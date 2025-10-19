// ==UserScript==
// @name         Taobao orders export (JSON) 淘宝订单导出 (JSON)
// @namespace    http://tampermonkey.net/
// @version      0.2.0
// @description  Use embedded JSON in Taobao orders page to export CSV (more reliable than DOM selectors). Attempts to fetch logistics data when available.
// @author       adapted
// @match        https://buyertrade.taobao.com/*
// @grant        GM_xmlhttpRequest
// @connect      buyertrade.taobao.com
// @connect      wuliu.taobao.com
// @connect      market.m.taobao.com
// @license      MIT
// ==/UserScript==

(function() {
    'use strict';

    let orderList = [];

    function toCsv(header, data, filename) {
        let rows = '\uFEFF' + header.join(',') + '\n';
        for (let order of data) {
            order[0] = '\t' + (order[0] || '');
            order[7] = order[7] ? '\t' + order[7] : '';
            rows += order.map(v => (v===undefined||v===null)?'':('"'+String(v).replace(/"/g,'""')+'"')).join(',') + '\n';
        }
        const blob = new Blob([rows], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename + '.csv';
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

                const titles = [];
                const itemUrls = [];
                if (Array.isArray(order.subOrders)) {
                    for (const so of order.subOrders) {
                        const it = so.itemInfo || {};
                        if (it.title) titles.push(it.title.replace(/,/g,'，'));
                        if (it.itemUrl) itemUrls.push(it.itemUrl.replace(/^\/\//,'https://'));
                    }
                }
                const joinedTitles = titles.join('||');
                const firstItemUrl = itemUrls.length ? itemUrls[0] : '';

                // Try to fetch tracking via viewLogistic dataUrl if present
                let tracking = '0';
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

                results.push([
                    orderId,
                    joinedTitles,
                    firstItemUrl,
                    '', // unit price (not present in this JSON example)
                    '', // quantity (not present)
                    actualFee,
                    status,
                    tracking
                ]);
            } catch (e) {
                console.error('order parse error', e);
            }
        }
        return results;
    }

    async function exportOrdersFromJson() {
        const header = ["订单号","商品名称","商品链接","单价","数量","实付款","状态","快递单号"];
        const rows = await extractOrdersFromEmbeddedJson();
        if (!rows.length) { alert('Keine Bestellungen gefunden oder JSON nicht lesbar.'); return; }
        toCsv(header, rows, '淘宝订单导出_JSON');
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
