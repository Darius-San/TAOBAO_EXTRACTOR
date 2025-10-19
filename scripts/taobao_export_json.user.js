// ==UserScript==
// @name         Taobao orders export (JSON) 淘宝订单导出 (JSON)
// @namespace    http://tampermonkey.net/
// @version      0.2.0
// @description  Use embedded JSON in Taobao orders page to export CSV (more reliable than DOM selectors). Attempts to fetch logistics data when available.
// @author       adapted
// @match        https://buyertrade.taobao.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_download
// @connect      buyertrade.taobao.com
// @connect      wuliu.taobao.com
// @connect      market.m.taobao.com
// @license      MIT
// ==/UserScript==

(function() {
    'use strict';

    let orderList = [];
    // Header translation map: Chinese -> English
    const HEADER_MAP = {
        '订单号': 'order_id',
        '下单日期': 'order_date',
        '卖家': 'seller',
        '商品名称': 'title',
        '商品链接': 'item_url',
        '单价': 'unit_price',
        '数量': 'quantity',
        '实付款': 'paid',
        '状态': 'status',
        '快递单号': 'tracking_number',
        '规格': 'spec'
    };

    // Config: default filename base (no extension) and whether to attempt GM_download
    const CONFIG = {
        defaultFilename: 'taobao_orders_export',
        useGMDownload: true
    };

    function toCsv(header, data, filename) {
        // header: array of Chinese column names
        // filename: base filename (without .csv)
        let rows = '\uFEFF' + header.join(',') + '\n';
        const idIndex = header.indexOf('订单号');
        const trackingIndex = header.indexOf('快递单号');
        for (let order of data) {
            // ensure row has same length as header
            while (order.length < header.length) order.push('');
            if (idIndex >= 0) order[idIndex] = '\t' + (order[idIndex] || '');
            if (trackingIndex >= 0 && order[trackingIndex]) order[trackingIndex] = '\t' + order[trackingIndex];
            rows += order.map(v => (v===undefined||v===null)?'':('"'+String(v).replace(/"/g,'""')+'"')).join(',') + '\n';
        }
        const blob = new Blob([rows], { type: 'text/csv;charset=utf-8;' });
        // create download name prompt
        let outName = filename || CONFIG.defaultFilename;
        try {
            const user = prompt('Dateiname für Export (ohne Erweiterung):', outName);
            if (user && user.trim()) outName = user.trim();
        } catch (e) { /* ignore */ }

        const fullName = outName + '.csv';
        // Prefer GM_download if available and configured
        if (typeof GM_download === 'function' && CONFIG.useGMDownload) {
            try {
                const reader = new FileReader();
                reader.onload = function() {
                    const dataUrl = reader.result;
                    GM_download({url: dataUrl, name: fullName, saveAs: true});
                };
                reader.readAsDataURL(blob);
                return;
            } catch (e) { console.debug('GM_download failed', e); }
        }

        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = fullName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    function findEmbeddedJsonString() {
        const scripts = Array.from(document.querySelectorAll('script'));
        for (const s of scripts) {
            const txt = s.textContent || '';
            if (txt.includes('var data = JSON.parse(')) {
                const m = txt.match(/var\s+data\s*=\s*JSON\.parse\('([\s\S]*?)'\);/);
                if (m && m[1]) return m[1];
            }
        }
        return null;
    }

    function unescapeEmbeddedJson(str) {
        let s = str.replace(/\\\\/g, '\\');
        s = s.replace(/\\"/g, '"');
        s = s.replace(/\\x/g, '\\u00');
        return s;
    }

    function gmFetchJson(url) {
        return new Promise((resolve, reject) => {
            if (typeof GM_xmlhttpRequest === 'function') {
                GM_xmlhttpRequest({
                    method: 'GET',
                    url: url,
                    responseType: 'json',
                    onload: function(res) {
                        if (res.status >= 200 && res.status < 300) {
                            resolve(res.response);
                        } else reject(new Error('Status ' + res.status));
                    },
                    onerror: function(err) { reject(err); }
                });
            } else {
                fetch(url, { credentials: 'same-origin' }).then(r=>r.json()).then(resolve).catch(reject);
            }
        });
    }

    async function extractOrdersFromEmbeddedJson() {
        const raw = findEmbeddedJsonString();
        if (!raw) { console.error('No embedded JSON found.'); return []; }
        const dec = unescapeEmbeddedJson(raw);
        let data;
        try { data = JSON.parse(dec); } catch (e) { console.error('JSON parse failed', e); return []; }

        const orders = data.mainOrders || [];
        const results = [];

        for (const order of orders) {
            try {
                const orderId = (order.orderInfo && order.orderInfo.id) || order.id || '';
                const status = (order.statusInfo && order.statusInfo.text) || '';
                const actualFee = (order.payInfo && order.payInfo.actualFee) || '';
                const sellerUrl = (order.seller && order.seller.shopUrl) || '';

                // extract order date from multiple possible fields
                let orderDate = '';
                try {
                    orderDate = (order.orderInfo && (order.orderInfo.createTime || order.orderInfo.createDate || order.orderInfo.gmtCreate)) || order.createTime || order.createDate || (order.payInfo && (order.payInfo.payTime || order.payInfo.createTime)) || '';
                    if (orderDate) {
                        // numeric timestamps
                        if (/^\d{13}$/.test(String(orderDate))) {
                            orderDate = new Date(Number(orderDate)).toISOString().slice(0,10);
                        } else if (/^\d{10}$/.test(String(orderDate))) {
                            orderDate = new Date(Number(orderDate) * 1000).toISOString().slice(0,10);
                        } else if (String(orderDate).includes(' ')) {
                            orderDate = String(orderDate).split(' ')[0];
                        } else if (String(orderDate).includes('T')) {
                            orderDate = String(orderDate).split('T')[0];
                        }
                    }
                } catch (e) { console.debug('orderDate parse error', e); orderDate = '' }

                // extract seller/store name from several possible fields
                let sellerName = '';
                try {
                    if (order.seller) {
                        sellerName = order.seller.shopName || order.seller.shopTitle || order.seller.storeName || order.seller.name || order.seller.nick || '';
                    }
                    // fallback: check first subOrder for seller info
                    if (!sellerName && Array.isArray(order.subOrders) && order.subOrders.length) {
                        const s0 = order.subOrders[0];
                        if (s0 && s0.seller) {
                            sellerName = s0.seller.shopName || s0.seller.name || s0.seller.nick || '';
                        }
                        // some payloads include shopName on subOrder
                        sellerName = sellerName || s0.shopName || s0.shopTitle || '';
                    }
                    // final fallback: attempt to read from order.sellerName or order.shopName
                    sellerName = sellerName || order.sellerName || order.shopName || '';
                    // sanitize commas
                    if (sellerName) sellerName = String(sellerName).replace(/,/g,'，');
                } catch (e) { console.debug('sellerName parse error', e); sellerName = '' }

                // Try to fetch tracking via viewLogistic dataUrl if present (do this early so subOrders can include it)
                let tracking = '';
                try {
                    const ops = order.statusInfo && order.statusInfo.operations;
                    if (Array.isArray(ops)) {
                        const op = ops.find(o => o.id === 'viewLogistic' && (o.dataUrl || o.url));
                        if (op && op.dataUrl) {
                            const url = op.dataUrl.startsWith('http') ? op.dataUrl : (location.origin + op.dataUrl);
                            const json = await gmFetchJson(url).catch(()=>null);
                            if (json) {
                                const txt = JSON.stringify(json);
                                const m = txt.match(/\d{11,}/);
                                if (m) tracking = m[0];
                            }
                        }
                    }
                } catch (err) { console.debug('tracking fetch failed', err); }

                // If subOrders exist, list each subOrder as its own CSV row
                if (Array.isArray(order.subOrders) && order.subOrders.length) {
                    // if order has multiple items, insert an empty row before to visually separate groups
                    if (order.subOrders.length > 1) results.push([]);
                    for (const so of order.subOrders) {
                        try {
                            const it = so.itemInfo || {};
                            const title = it.title ? String(it.title).replace(/,/g,'，') : (so.title || '');
                            // spec may be in skuTitle, skuPropertiesName, or a specific field
                            const spec = it.skuTitle || it.skuPropertiesName || it.spec || so.skuTitle || '';
                            const itemUrl = (it.itemUrl || so.itemUrl || '').replace(/^\/\//,'https://');
                            // unit price: try several candidate fields, fall back to total/quantity when possible
                            let unitPrice = '';
                            const qty = Number(so.quantity || it.quantity || so.count || 0) || 0;
                            const tryNum = v => { if (v===undefined||v===null) return null; const s=String(v).replace(/[¥,\s]/g,''); const n=Number(s); return isFinite(n)?n:null };
                            const candidates = [so.price, so.unitPrice, so.skuPrice, so.payPrice, so.totalFee, so.totalPayment, it.price, it.promotionPrice, it.skuPrice];
                            let found = null;
                            for (const c of candidates) {
                                const n = tryNum(c);
                                if (n!==null) { found = n; break; }
                            }
                            if (found !== null) {
                                // if candidate looks like a total (and qty>1) and it's from total-like fields, try to divide
                                // Heuristic: if field name contains 'total' and qty>0
                                const totalLike = (String(so.totalFee||so.totalPayment||'') !== '');
                                if (totalLike && qty>0 && (tryNum(so.totalFee) || tryNum(so.totalPayment))) {
                                    const total = tryNum(so.totalFee) || tryNum(so.totalPayment) || found;
                                    unitPrice = (total && qty>0) ? (total/qty).toFixed(2) : String(found);
                                } else {
                                    unitPrice = String(found);
                                }
                            } else {
                                // as last resort, if there is a numeric total on so and qty, compute
                                const totalN = tryNum(so.totalFee) || tryNum(so.totalPayment) || null;
                                if (totalN !== null && qty>0) unitPrice = (totalN/qty).toFixed(2);
                                else unitPrice = '';
                            }
                            const quantity = qty || '';

                            results.push([
                                orderId,
                                orderDate,
                                sellerName,
                                title,
                                itemUrl,
                                unitPrice,
                                quantity,
                                actualFee,
                                status,
                                tracking,
                                spec
                            ]);
                        } catch (e) {
                            console.debug('suborder parse error', e);
                        }
                    }
                    // after group, add an empty row to separate groups visually
                    if (order.subOrders.length > 1) results.push([]);
                    // continue to next order (we already pushed suborders)
                    continue;
                }

                // fallback when no subOrders: create a single row from order-level info
                const titles = [];
                const itemUrls = [];
                if (Array.isArray(order.items)) {
                    for (const it of order.items) {
                        if (it && it.title) titles.push(it.title.replace(/,/g,'，'));
                        if (it && it.itemUrl) itemUrls.push(it.itemUrl.replace(/^\/\//,'https://'));
                    }
                }
                const joinedTitles = titles.join('||');
                const firstItemUrl = itemUrls.length ? itemUrls[0] : '';

                // (tracking was retrieved earlier)

                results.push([
                    orderId,
                    orderDate,
                    sellerName,
                    joinedTitles,
                    firstItemUrl,
                    '', // unit price (not present in this JSON example)
                    '', // quantity (not present)
                    actualFee,
                    status,
                    tracking,
                    '' // spec empty
                ]);
            } catch (e) {
                console.error('order parse error', e);
            }
        }
        return results;
    }

    async function exportOrdersFromJson() {
        const header = ["订单号","下单日期","卖家","商品名称","商品链接","单价","数量","实付款","状态","快递单号","规格"];
        const rows = await extractOrdersFromEmbeddedJson();
        if (!rows.length) { alert('Keine Bestellungen gefunden oder JSON nicht lesbar.'); return; }
        // ask user for filename base
        let baseName = CONFIG.defaultFilename;
        try { const n = prompt('Dateiname für Export (ohne Erweiterung):', baseName); if (n && n.trim()) baseName = n.trim(); } catch(e){}
        toCsv(header, rows, baseName);

        // offer an English-header version
        try {
            const makeEn = confirm('Auch eine Version mit englischen Spaltennamen erzeugen? (OK = Ja)');
            if (makeEn) {
                const enHeader = header.map(h => HEADER_MAP[h] || h);
                // build CSV rows with same data but enHeader as header
                toCsv(enHeader, rows, baseName + '_en_headers');
            }
        } catch(e) { /* ignore */ }
    }

    function addJsonExportButton(){
        try {
            const main = document.getElementById('J_bought_main') || document.querySelector('.col-main') || document.body;
            const btn = document.createElement('input');
            btn.type = 'button';
            btn.value = '导出 (JSON)';
            Object.assign(btn.style, { padding:'8px 14px', margin:'6px', background:'#28a745', color:'#fff', borderRadius:'6px', border:'none', cursor:'pointer' });
            btn.onclick = exportOrdersFromJson;
            main.insertBefore(btn, main.firstChild);
        } catch(e){ console.debug(e); }
    }

    // insert button after short delay to ensure page loaded
    setTimeout(addJsonExportButton, 1200);

})();
