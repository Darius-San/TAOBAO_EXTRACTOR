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
        '商品编号': 'item_id',
        '单价': 'unit_price',
        '单项总价': 'item_total',
        '数量': 'quantity',
        '实付款': 'paid',
        '规格': 'specification',
        // '状态' and '快递单号' removed per user request
        '运费': 'lieferkosten'
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
    // allow header passed in Chinese or already-mapped English names
    const idIndex = header.indexOf('订单号') >= 0 ? header.indexOf('订单号') : header.indexOf('order_id');
        // Filter out rows that are clearly garbage/empty before exporting.
        // Strategy: keep rows that contain at least one meaningful field (order id, title, item id, unit_price, item_total, paid)
        const normalizedHeader = header.map(h => String(h).toLowerCase());
        const idxOrder = normalizedHeader.indexOf('订单号')>=0 ? normalizedHeader.indexOf('订单号') : normalizedHeader.indexOf('order_id');
    const idxTitle = normalizedHeader.indexOf('商品名称')>=0 ? normalizedHeader.indexOf('商品名称') : normalizedHeader.indexOf('title');
    const idxItemId = normalizedHeader.indexOf('商品编号')>=0 ? normalizedHeader.indexOf('商品编号') : normalizedHeader.indexOf('item_id');
    const idxUnit = normalizedHeader.indexOf('单价')>=0 ? normalizedHeader.indexOf('单价') : normalizedHeader.indexOf('unit_price');
    const idxSeller = normalizedHeader.indexOf('卖家')>=0 ? normalizedHeader.indexOf('卖家') : normalizedHeader.indexOf('seller');
    const idxItemTotal = normalizedHeader.indexOf('单项总价')>=0 ? normalizedHeader.indexOf('单项总价') : normalizedHeader.indexOf('item_total');
    const idxPaid = normalizedHeader.indexOf('实付款')>=0 ? normalizedHeader.indexOf('实付款') : normalizedHeader.indexOf('paid');

    const looksMeaningful = (row) => {
            if (!row || !Array.isArray(row)) return false;
            // normalize cell -> string
            const cell = (i) => { try { return String((row[i]===undefined||row[i]===null)?'':row[i]).trim(); } catch(e){ return ''; } };
            // drop rows that literally contain 'order number' artifacts
            for (const c of row) {
                if (!c) continue;
                if (/order\s*number/i.test(String(c))) return false;
            }
            // if any of the key columns has non-empty meaningful content, keep the row
            const hasOrder = (idxOrder >= 0 && cell(idxOrder));
            const hasTitle = (idxTitle >= 0 && cell(idxTitle));
            const hasItemId = (idxItemId >= 0 && cell(idxItemId));
            const hasUnit = (idxUnit >= 0 && cell(idxUnit) && /[0-9]/.test(cell(idxUnit)));
            const hasItemTotal = (idxItemTotal >= 0 && cell(idxItemTotal) && /[0-9]/.test(cell(idxItemTotal)));
            const hasPaid = (idxPaid >= 0 && cell(idxPaid) && /[0-9]/.test(cell(idxPaid)));
            const hasSeller = (idxSeller >= 0 && cell(idxSeller));

            // Keep row only if it contains at least one real data field besides a bare order id/date
            if (hasTitle || hasItemId || hasUnit || hasItemTotal || hasPaid || hasSeller) return true;
            // otherwise drop rows that only contain an order id or trivial content
            if (hasOrder) return false;
            // fallback: consider a cell meaningful only if it contains at least one alphanumeric or CJK character
            // this avoids keeping rows that are only punctuation/quotes/commas harvested from messy snippets
            const meaningfulCharRe = /[0-9A-Za-z\u4e00-\u9fff]/;
            for (const c of row) {
                try {
                    const s = String(c || '').trim();
                    if (s && meaningfulCharRe.test(s)) return true;
                } catch (e) { /* ignore conversion errors */ }
            }
            return false;
        };

    const filtered = (data || []).map(r => Array.from(r || [])).filter(looksMeaningful);

        // Helper: parse a single CSV line string into fields (handles quoted fields and doubled quotes)
        const parseCsvLine = (line) => {
            const out = [];
            let cur = '';
            let inQuote = false;
            for (let i = 0; i < line.length; ++i) {
                const ch = line[i];
                if (ch === '"') {
                    // doubled quote inside quoted field -> add one quote and skip next
                    if (inQuote && line[i+1] === '"') { cur += '"'; ++i; }
                    else { inQuote = !inQuote; }
                } else if (ch === ',' && !inQuote) {
                    out.push(cur);
                    cur = '';
                } else {
                    cur += ch;
                }
            }
            out.push(cur);
            return out.map(s => String(s == null ? '' : s).trim());
        };

        for (let order of filtered) {
            // Some recorder/parsed snippets accidentally produce a single-cell string that already
            // contains a full CSV row (commas + quoted fields). Detect that and split into columns
            // so the exported CSV is properly columnized instead of embedding a CSV string inside
            // the first cell (which later causes doubled/double-quotes when we re-quote everything).
            try {
                if ((!Array.isArray(order) || order.length === 1) && typeof order[0] === 'string' && order[0].indexOf(',') >= 0) {
                    const parsed = parseCsvLine(order[0]);
                    if (parsed && parsed.length > 1) order = parsed;
                }
            } catch (e) { /* ignore parse failures - fall back to raw row */ }
            // ensure row has same length as header: pad short rows and truncate long rows
            while (order.length < header.length) order.push('');
            if (order.length > header.length) order = order.slice(0, header.length);
            // sanitize each cell: trim, unwrap accidental surrounding quotes, remove stray tabs
            if (idIndex >= 0) {
                const rawId = (order[idIndex] === undefined || order[idIndex] === null) ? '' : String(order[idIndex]);
                const cleanId = rawId.replace(/^\s+/, '').replace(/\s+$/, '');
                order[idIndex] = '\t' + cleanId;
            }
            const sanitizeCell = (v) => {
                let s = (v === undefined || v === null) ? '' : String(v);
                s = s.trim();
                // if the value is wrapped in quotes ("..."), remove those outer quotes
                if (s.length >= 2 && s[0] === '"' && s[s.length-1] === '"') {
                    s = s.slice(1, -1);
                }
                // convert doubled-quote escapes "" -> " inside cell (undo previous CSV double-escaping)
                s = s.replace(/""/g, '"');
                // remove stray leading tabs that sometimes appear in recorder output
                s = s.replace(/^\t+/, '');
                return '"' + s.replace(/"/g, '""') + '"';
            };

            rows += order.map(v => sanitizeCell(v)).join(',') + '\n';
        }
        const blob = new Blob([rows], { type: 'text/csv;charset=utf-8;' });
        // create download name prompt only if filename omitted
        let outName = filename || '';
        if (!outName) outName = CONFIG.defaultFilename;
        if (!filename) {
            try {
                const user = prompt('Dateiname für Export (ohne Erweiterung):', outName);
                if (user && user.trim()) outName = user.trim();
            } catch (e) { /* ignore */ }
        }

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

    // Fetch the page HTML for a given URL and try to extract the embedded JSON payload.
    // Returns a parsed data object or null if no embedded JSON was found.
    function fetchEmbeddedDataFromUrl(url) {
        return new Promise((resolve, reject) => {
            const handleText = txt => {
                const m = String(txt).match(/var\s+data\s*=\s*JSON\.parse\('([\s\S]*?)'\);/);
                if (m && m[1]) {
                    try {
                        const dec = unescapeEmbeddedJson(m[1]);
                        const parsed = JSON.parse(dec);
                        resolve(parsed);
                    } catch (e) {
                        return resolve(null);
                    }
                } else {
                    resolve(null);
                }
            };

            // Prefer native fetch with credentials (ensures cookies/session) and no-cache to get the current server HTML
            // Fallback to GM_xmlhttpRequest when fetch is not available or fails
            try {
                fetch(url, { credentials: 'include', cache: 'no-cache', headers: { 'Cache-Control': 'no-cache' } })
                    .then(r => r.text())
                    .then(handleText)
                    .catch(err => {
                        // try GM_xmlhttpRequest as fallback
                        if (typeof GM_xmlhttpRequest === 'function') {
                            try {
                                GM_xmlhttpRequest({
                                    method: 'GET',
                                    url: url,
                                    responseType: 'text',
                                    onload(res) {
                                        if (res.status >= 200 && res.status < 300) handleText(res.responseText || res.response);
                                        else resolve(null);
                                    },
                                    onerror() { resolve(null); }
                                });
                            } catch (e) { resolve(null); }
                        } else {
                            resolve(null);
                        }
                    });
            } catch (e) {
                // If fetch throws synchronously, try GM_xmlhttpRequest
                if (typeof GM_xmlhttpRequest === 'function') {
                    try {
                        GM_xmlhttpRequest({
                            method: 'GET',
                            url: url,
                            responseType: 'text',
                            onload(res) {
                                if (res.status >= 200 && res.status < 300) handleText(res.responseText || res.response);
                                else resolve(null);
                            },
                            onerror() { resolve(null); }
                        });
                    } catch (e2) { resolve(null); }
                } else {
                    resolve(null);
                }
            }
        });
    }

    // Core extraction logic refactored to accept a parsed `data` object. Returns rows array.
    function extractOrdersFromData(data, showOrderNumberAlways) {
        const orders = (data && data.mainOrders) || [];
        const results = [];

        for (const order of orders) {
            try {
                const orderId = (order.orderInfo && order.orderInfo.id) || order.id || '';
                const status = (order.statusInfo && order.statusInfo.text) || '';
                const actualFee = (order.payInfo && order.payInfo.actualFee) || '';

                // extract order date
                let orderDate = '';
                try {
                    orderDate = (order.orderInfo && (order.orderInfo.createTime || order.orderInfo.createDate || order.orderInfo.gmtCreate)) || order.createTime || order.createDate || (order.payInfo && (order.payInfo.payTime || order.payInfo.createTime)) || '';
                    if (orderDate) {
                        if (/^\d{13}$/.test(String(orderDate))) orderDate = new Date(Number(orderDate)).toISOString().slice(0,10);
                        else if (/^\d{10}$/.test(String(orderDate))) orderDate = new Date(Number(orderDate) * 1000).toISOString().slice(0,10);
                        else if (String(orderDate).includes(' ')) orderDate = String(orderDate).split(' ')[0];
                        else if (String(orderDate).includes('T')) orderDate = String(orderDate).split('T')[0];
                    }
                } catch (e) { orderDate = ''; }

                // seller name
                let sellerName = '';
                try {
                    if (order.seller) sellerName = order.seller.shopName || order.seller.shopTitle || order.seller.storeName || order.seller.name || order.seller.nick || '';
                    if (!sellerName && Array.isArray(order.subOrders) && order.subOrders.length) {
                        const s0 = order.subOrders[0];
                        if (s0 && s0.seller) sellerName = s0.seller.shopName || s0.seller.name || s0.seller.nick || '';
                        sellerName = sellerName || s0.shopName || s0.shopTitle || '';
                    }
                    sellerName = sellerName || order.sellerName || order.shopName || '';
                    if (sellerName) sellerName = String(sellerName).replace(/,/g,'，');
                } catch (e) { sellerName = ''; }

                if (Array.isArray(order.subOrders) && order.subOrders.length) {
                    // first pass compute sum of item totals
                    let sumItemTotals = 0;
                    const itemTotalsTemp = [];
                    for (const so of order.subOrders) {
                        const itTemp = so.itemInfo || {};
                        const qtyTemp = Number(so.quantity || itTemp.quantity || so.count || 0) || 0;
                        const tryNumTemp = v => { if (v===undefined||v===null) return null; const s=String(v).replace(/[¥,\s]/g,''); const n=Number(s); return isFinite(n)?n:null };
                        const explicitTemp = tryNumTemp(so.totalFee) || tryNumTemp(so.totalPayment) || null;
                        let unitTemp = null;
                        const candidatesTemp = [ (so.priceInfo && so.priceInfo.realTotal) || (itTemp.priceInfo && itTemp.priceInfo.realTotal) || null, (so.priceInfo && so.priceInfo.original) || (itTemp.priceInfo && itTemp.priceInfo.original) || null, so.price, so.unitPrice, so.skuPrice, so.payPrice, itTemp.price, itTemp.promotionPrice, itTemp.skuPrice ];
                        for (const c of candidatesTemp) { const n = tryNumTemp(c); if (n!==null) { unitTemp = n; break; } }
                        let itemTotalTemp = '';
                        if (explicitTemp !== null && qtyTemp>0) itemTotalTemp = Number(explicitTemp).toFixed(2);
                        else if (unitTemp !== null && qtyTemp>0) itemTotalTemp = (Number(unitTemp) * qtyTemp).toFixed(2);
                        else itemTotalTemp = '';
                        itemTotalsTemp.push(itemTotalTemp);
                        const nt = (itemTotalTemp==='')?0:Number(itemTotalTemp)||0;
                        sumItemTotals += nt;
                    }

                    const tryNum = v => { if (v===undefined||v===null) return null; const s=String(v).replace(/[¥,\s]/g,''); const n=Number(s); return isFinite(n)?n:null };
                    const actualFeeNum = tryNum(actualFee);
                    const shipping = (actualFeeNum!==null) ? Math.abs(actualFeeNum - sumItemTotals).toFixed(2) : '';

                    let firstSubOrderEmitted = false;
                    for (const so of order.subOrders) {
                        try {
                            const it = so.itemInfo || {};
                            const title = it.title ? String(it.title).replace(/,/g,'，') : (so.title || '');
                            // spec not needed per user request
                            const itemUrl = (it.itemUrl || so.itemUrl || '').replace(/^\/\//,'https://');
                            const itemId = it.id || it.itemId || so.itemId || so.skuId || it.skuId || '';
                            let unitPrice = '';
                            const qty = Number(so.quantity || it.quantity || so.count || 0) || 0;
                            const candidates = [ (so.priceInfo && so.priceInfo.realTotal) || (it.priceInfo && it.priceInfo.realTotal) || null, (so.priceInfo && so.priceInfo.original) || (it.priceInfo && it.priceInfo.original) || null, so.price, so.unitPrice, so.skuPrice, so.payPrice, it.price, it.promotionPrice, it.skuPrice ];
                            let found = null;
                            for (const c of candidates) { const n = tryNum(c); if (n!==null) { found = n; break; } }
                            const explicitSubTotal = tryNum(so.totalFee) || tryNum(so.totalPayment) || null;
                            if ((explicitSubTotal !== null) && qty > 0) unitPrice = (explicitSubTotal/qty).toFixed(2);
                            else if (found !== null) { const fn = tryNum(found); unitPrice = (fn!==null) ? fn.toFixed(2) : String(found); }
                            const quantity = qty || '';
                            const upNum = tryNum(unitPrice);
                            const itemTotal = (explicitSubTotal !== null && qty>0) ? Number(explicitSubTotal).toFixed(2) : ((upNum !== null && qty>0) ? (upNum * qty).toFixed(2) : '');

                            const idStr = itemId ? String(itemId) : '';
                            const outItemId = idStr; // always show article/item number
                            const outItemTotal = itemTotal;

                            const outActualFee = firstSubOrderEmitted ? '' : actualFee;
                            const outShipping = firstSubOrderEmitted ? '' : shipping;
                            const outOrderId = showOrderNumberAlways ? orderId : (firstSubOrderEmitted ? '' : orderId);
                            firstSubOrderEmitted = true;

                            // no reliable spec in embedded JSON path for now; keep placeholder empty
                            results.push([ outOrderId, orderDate, sellerName, title, '', itemUrl, outItemId, unitPrice, quantity, outItemTotal, outActualFee, outShipping ]);
                        } catch (e) { console.debug('suborder parse error', e); }
                    }
                    continue;
                }

                // fallback when no subOrders
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

                // include spec placeholder (empty) after title
                results.push([ orderId, orderDate, sellerName, joinedTitles, '', firstItemUrl, '', '', '', '', actualFee, '' ]);
            } catch (e) { console.error('order parse error', e); }
        }
        return results;
    }

    async function extractOrdersFromEmbeddedJson(showOrderNumberAlways) {
        // Try to fetch the current page's HTML and extract the embedded JSON (option 1). If that fails,
        // fall back to reading the embedded JSON from the current DOM.
        try {
            const fetched = await fetchEmbeddedDataFromUrl(location.href);
            if (fetched) return extractOrdersFromData(fetched, showOrderNumberAlways);
        } catch (e) { /* ignore and fall back */ }

        // fallback: read embedded JSON from current DOM
        const raw = findEmbeddedJsonString();
        if (!raw) { console.error('No embedded JSON found.'); return []; }
        const dec = unescapeEmbeddedJson(raw);
        let data;
        try { data = JSON.parse(dec); } catch (e) { console.error('JSON parse failed', e); return []; }
        return extractOrdersFromData(data, showOrderNumberAlways);
    }

    async function exportOrdersFromJson() {
        // Single prompt for a filename; immediately download CSV with English headers.
    // header order adjusted: 单价 (unit), 数量 (quantity), 单项总价 (item total), 实付款 (order total)
    const zhHeader = ["订单号","下单日期","卖家","商品名称","规格","商品链接","商品编号","单价","数量","单项总价","实付款","运费"];
        // Ask user whether order number (订单号) should be shown on every subOrder row
        // or only on the first subOrder of a Sammelbestellung.
        let showOrderNumberAlways = true;
        try {
            showOrderNumberAlways = confirm('Show order numbers on every sub-order row? OK = yes, Cancel = show only on first sub-order of each order.');
        } catch(e) { /* ignore */ }

        const rows = await extractOrdersFromEmbeddedJson(showOrderNumberAlways);
        if (!rows.length) { alert('Keine Bestellungen gefunden oder JSON nicht lesbar.'); return; }
        // ask user for filename base once
        let baseName = CONFIG.defaultFilename;
        try { const n = prompt('Dateiname für Export (ohne Erweiterung):', baseName); if (n && n.trim()) baseName = n.trim(); } catch(e){}
        // produce English header version immediately using HEADER_MAP
        const enHeader = zhHeader.map(h => HEADER_MAP[h] || h);
        // toCsv will respect the provided filename and not re-prompt
        toCsv(enHeader, rows, baseName);
    }

    // Export using only the DOM (do not attempt fetch). Useful if fetch returns stale data
    async function exportUsingDomOnly() {
        let showOrderNumberAlways = true;
        try { showOrderNumberAlways = confirm('Show order numbers on every sub-order row? OK = yes, Cancel = show only on first sub-order of each order.'); } catch(e){}
        const raw = findEmbeddedJsonString();
        if (!raw) { alert('Keine eingebettete JSON im DOM gefunden.'); return; }
        const dec = unescapeEmbeddedJson(raw);
        let data;
        try { data = JSON.parse(dec); } catch (e) { alert('JSON parse failed from DOM'); return; }
        const rows = extractOrdersFromData(data, showOrderNumberAlways);
        if (!rows.length) { alert('Keine Bestellungen gefunden.'); return; }
        let baseName = CONFIG.defaultFilename;
        try { const n = prompt('Dateiname für Export (ohne Erweiterung):', baseName); if (n && n.trim()) baseName = n.trim(); } catch(e){}
    const zhHeader = ["订单号","下单日期","卖家","商品名称","规格","商品链接","商品编号","单价","数量","单项总价","实付款","运费"];
        const enHeader = zhHeader.map(h => HEADER_MAP[h] || h);
        toCsv(enHeader, rows, baseName);
    }

    // Export using only a fetched copy of the current page HTML (force server response parsing)
    async function exportUsingFetchOnly() {
        let showOrderNumberAlways = true;
        try { showOrderNumberAlways = confirm('Show order numbers on every sub-order row? OK = yes, Cancel = show only on first sub-order of each order.'); } catch(e){}
        const fetched = await fetchEmbeddedDataFromUrl(location.href);
        if (!fetched) { alert('Fetch of current page failed or no embedded JSON found in fetched HTML.'); return; }
        const rows = extractOrdersFromData(fetched, showOrderNumberAlways);
        if (!rows.length) { alert('Keine Bestellungen gefunden in fetched data.'); return; }
        let baseName = CONFIG.defaultFilename;
        try { const n = prompt('Dateiname für Export (ohne Erweiterung):', baseName); if (n && n.trim()) baseName = n.trim(); } catch(e){}
    const zhHeader = ["订单号","下单日期","卖家","商品名称","规格","商品链接","商品编号","单价","数量","单项总价","实付款","运费"];
        const enHeader = zhHeader.map(h => HEADER_MAP[h] || h);
        toCsv(enHeader, rows, baseName);
    }

    // Export using the rendered DOM parser (client-side rendered pages / SPA pagination)
    async function exportUsingRenderedDom() {
        let showOrderNumberAlways = true;
        try { showOrderNumberAlways = confirm('Show order numbers on every sub-order row? OK = yes, Cancel = show only on first sub-order of each order.'); } catch(e){}
        const rows = extractOrdersFromRenderedDom(showOrderNumberAlways);
        if (!rows || !rows.length) { alert('Keine Bestellungen gefunden im gerenderten DOM.'); return; }
        let baseName = CONFIG.defaultFilename;
        try { const n = prompt('Dateiname für Export (ohne Erweiterung):', baseName); if (n && n.trim()) baseName = n.trim(); } catch(e){}
    const zhHeader = ["订单号","下单日期","卖家","商品名称","规格","商品链接","商品编号","单价","数量","单项总价","实付款","运费"];
        const enHeader = zhHeader.map(h => HEADER_MAP[h] || h);
        toCsv(enHeader, rows, baseName);
    }

    // Heuristic extractor for pages that render orders directly into the DOM (client-side pagination)
    // Helper: parse a raw order-node text snippet (string) and return rows using same heuristics as DOM parser
    function parseOrderText(txt, showOrderNumberAlways, orderDateFallback) {
        const rows = [];
        if (!txt || !txt.trim()) return rows;
        const tryNum = v => { if (v===undefined||v===null) return null; const s=String(v).replace(/[¥,￥,\s]/g,''); const n=Number(s); return isFinite(n)?n:null };

        // overall shipping and order-level paid detection (kept for first emitted row)
        const shippingMatchAll = txt.match(/含运费[:：]?\s*[¥￥]?\s*([0-9.,]+)/);
        const shipping = (shippingMatchAll && shippingMatchAll[1]) ? (tryNum(shippingMatchAll[1])!==null?tryNum(shippingMatchAll[1]).toFixed(2):'') : '';
        // Prefer labelled totals like '实付款 297.00'. Otherwise pick the last price that occurs before a trailing marker
        let overallPaid = '';
        const labelled = txt.match(/(?:实付款|总价|总金额|gesamtkosten)[:：]?\s*[¥￥]?\s*([0-9]+(?:\.[0-9]+)?)/i);
        if (labelled && labelled[1]) {
            overallPaid = (tryNum(labelled[1])!==null? tryNum(labelled[1]).toFixed(2) : '');
        } else {
            const markerMatch = txt.match(/(交易成功|订单详情|交易完成|交易关闭)/);
            let upto = txt;
            if (markerMatch && typeof markerMatch.index === 'number' && markerMatch.index >= 0) upto = txt.slice(0, markerMatch.index + 1);
            // collect prices before marker
            const priceRegexAll = /[¥￥]\s*([0-9]+(?:\.[0-9]+)?)/g;
            let pm; const foundEntries = [];
            while ((pm = priceRegexAll.exec(upto)) !== null) {
                const n = tryNum(pm[1]); if (n!==null) foundEntries.push({n, idx: pm.index});
            }
            if (foundEntries.length) {
                // prefer a price that is followed by '(含运费' or contains '含运费' nearby
                const idxWithShip = upto.search(/\([\s\S]{0,40}?含运费|含运费[:：]?\s*[¥￥]?/);
                if (idxWithShip >= 0) {
                    // find the last price that appears before the '含运费' mention
                    let chosen = null;
                    for (let k = foundEntries.length-1; k>=0; --k) { if (foundEntries[k].idx < idxWithShip) { chosen = foundEntries[k].n; break; } }
                    if (chosen===null) chosen = foundEntries[foundEntries.length-1].n;
                    overallPaid = Number(chosen).toFixed(2);
                } else {
                    // otherwise prefer largest non-zero price (total usually larger than unit prices)
                    const nonZero = foundEntries.filter(e=> e.n && e.n>0).map(e=>e.n);
                    if (nonZero.length) overallPaid = Number(Math.max.apply(null, nonZero)).toFixed(2);
                    else overallPaid = Number(foundEntries[foundEntries.length-1].n).toFixed(2);
                }
            }
        }

        const orderDateMatch = txt.match(/(\d{4}-\d{2}-\d{2})/);
        const orderDate = orderDateMatch ? orderDateMatch[1] : (orderDateFallback || '');
        const orderIdMatch = txt.match(/订单号[:：]?\s*(\d{5,})/) || txt.match(/Order\s*No[:：]?\s*(\d{5,})/) || txt.match(/订单[:：]?\s*(\d{5,})/);
        const orderId = orderIdMatch ? orderIdMatch[1] : '';
        // try to extract seller: often the seller appears right after the order id separated by tab or spaces
        let sellerName = '';
        if (orderIdMatch) {
            // match '订单号: <id>\tSellerName' or similar
            const sellerRegex = new RegExp(orderId.replace(/([.*+?^=!:${}()|[\]\\])/g,'\\$1') + "\\s*[\t ]+([^\\t\\n\\r]+)");
            const sMatch = txt.match(sellerRegex);
            if (sMatch && sMatch[1]) sellerName = sMatch[1].trim();
        }

        const blocks = txt.split(/交易快照|交易成功|订单详情/).map(s=>s.trim()).filter(Boolean);

        // If there are multiple product blocks in a single node (Sammelbestellung), try to emit one row per product.
        let firstEmitted = false;
        if (blocks.length > 1) {
            for (const b of blocks) {
                try {
                    // skip obvious non-product blocks
                    if (!b) continue;
                    if (b.indexOf('保险服务')!==-1) continue;
                    // detect quantity: either explicit labels or a lone number on a line
                    const qlabel = b.match(/(?:数量|anzahl|qty)[:：]?\s*(\d+)/i);
                    let qmatch = qlabel;
                    if (!qmatch) {
                        // look for a standalone number on its own line (common in Taobao snippets)
                        const lone = b.match(/(?:\n|\r|^)\s*(\d{1,4})\s*(?:\n|\r|$)/);
                        if (lone) qmatch = lone;
                    }
                    const qty = qmatch ? String(qmatch[1]) : '';

                    // collect all price occurrences with positions
                    const priceRegex = /[¥￥]\s*([0-9]+(?:\.[0-9]+)?)/g;
                    let pm;
                    const prices = [];
                    while ((pm = priceRegex.exec(b)) !== null) {
                        const val = tryNum(pm[1]);
                        prices.push({v: val, idx: pm.index});
                    }

                    // choose unit price: prefer the price immediately before the quantity (if present), otherwise the last small-price in the block
                    let unit = null;
                    if (qty) {
                        const qidx = b.indexOf(qmatch[0]);
                        for (let i = prices.length - 1; i >= 0; --i) {
                            if (prices[i].idx < qidx) { unit = prices[i].v; break; }
                        }
                        if (unit===null && prices.length) unit = prices[prices.length-1].v;
                    } else {
                        if (prices.length) unit = prices[prices.length-1].v;
                    }

                    const unitPrice = (unit!==null) ? (Number(unit).toFixed(2)) : '';

                    // try explicit item total (rare inside product block) otherwise compute from unit * qty
                    let itemTotal = '';
                    const explicitTotal = b.match(/(?:单项总价|小计|商品小计|总价|实付款|gesamtkosten)[:：]?\s*[¥￥]?\s*([0-9]+(?:\.[0-9]+)?)/i);
                    if (explicitTotal && explicitTotal[1]) itemTotal = (tryNum(explicitTotal[1])!==null? tryNum(explicitTotal[1]).toFixed(2) : '');
                    if ((!itemTotal || itemTotal==='') && unit!==null && qty) itemTotal = (Number(unit) * Number(qty)).toFixed(2);

                    // skip blocks that don't look like product lines (no price and no qty)
                    if (!unit && !qty && !itemTotal) continue;

                    // extract sku and spec
                    const skuMatch = b.match(/(?:Artikelnummer|商品编号|商品ID)[:：]?\s*([0-9A-Za-z-]{6,})/) || b.match(/(\d{6,})/);
                    const outItemId = skuMatch ? skuMatch[1] : '';
                    let spec = '';
                    const specMatch = b.match(/(?:Style\s*:|color style:|规格[:：]|款式[:：])\s*([^,\n]+)/i);
                    if (specMatch) spec = specMatch[1].trim();

                    const title = (b.split(/¥|￥/)[0] || b).replace(/\n/g,' ').trim();
                    const itemDate = (b.match(/(\d{4}-\d{2}-\d{2})/) || [null, orderDate])[1] || orderDate;

                    const outPaid = firstEmitted ? '' : overallPaid;
                    const outShipping = firstEmitted ? '' : shipping;
                    const outOrderId = showOrderNumberAlways ? orderId : (firstEmitted ? '' : orderId);
                    firstEmitted = true;

                    // align with header: title, spec, item_url, item_id, unit, qty, item_total, paid, shipping
                    rows.push([ outOrderId, itemDate, sellerName || '', title, spec || '', '', outItemId, unitPrice, qty || '', itemTotal || '', outPaid || '', outShipping || '' ]);
                } catch (e) { /* ignore per-block errors */ }
            }
            return rows;
        }

        // single-block fallback (similar to original logic but prefer last price before qty)
        const b = blocks[0] || txt;
        const title = (b.split(/¥|￥/)[0] || b).replace(/\n/g,' ').trim();
        // quantity detection
        const qlabel = b.match(/(?:数量|anzahl|qty)[:：]?\s*(\d+)/i);
        let qmatch = qlabel;
        if (!qmatch) {
            const lone = b.match(/(?:\n|\r|^)\s*(\d{1,4})\s*(?:\n|\r|$)/);
            if (lone) qmatch = lone;
        }
        const qty = qmatch ? String(qmatch[1]) : '';
        // prices
        const priceRegex = /[¥￥]\s*([0-9]+(?:\.[0-9]+)?)/g;
        let pm2; const prices2 = [];
        while ((pm2 = priceRegex.exec(b)) !== null) prices2.push({v: tryNum(pm2[1]), idx: pm2.index});
        let unit2 = null;
        if (qty) {
            const qidx = b.indexOf(qmatch[0]);
            for (let i = prices2.length-1;i>=0;--i) if (prices2[i].idx < qidx) { unit2 = prices2[i].v; break; }
            if (unit2===null && prices2.length) unit2 = prices2[prices2.length-1].v;
        } else if (prices2.length) unit2 = prices2[prices2.length-1].v;
        const unitPrice = (unit2!==null) ? (Number(unit2).toFixed(2)) : '';
        let itemTotal = '';
        const explicitTotal2 = b.match(/(?:gesamtkosten|总价|实付款|总计|总金额|小计)[:：]?\s*[¥￥]?\s*([0-9]+(?:\.[0-9]+)?)/i);
        if (explicitTotal2 && explicitTotal2[1]) itemTotal = (tryNum(explicitTotal2[1])!==null? tryNum(explicitTotal2[1]).toFixed(2) : '');
        if ((!itemTotal || itemTotal==='') && unit2!==null && qty) itemTotal = (Number(unit2) * Number(qty)).toFixed(2);
        const skuMatch = b.match(/(?:Artikelnummer|商品编号|商品ID)[:：]?\s*([0-9A-Za-z-]{6,})/i) || b.match(/(\d{6,})/);
        const outItemId = skuMatch ? skuMatch[1] : '';
        let spec = '';
        const specMatch = b.match(/(?:Style\s*:|color style:|规格[:：]|款式[:：])\s*([^,\n]+)/i);
        if (specMatch) spec = specMatch[1].trim();

    // align with header: title, spec, item_url, item_id, unit, qty, item_total, paid, shipping
    rows.push([ showOrderNumberAlways ? orderId : orderId, orderDate, sellerName || '', title, spec || '', '', outItemId, unitPrice, qty || '', itemTotal || unitPrice || '', overallPaid || '', shipping || '' ]);
        return rows;
    }
    function extractOrdersFromRenderedDom(showOrderNumberAlways) {
        const rows = [];
        // select order containers observed by MutationObserver
        const nodes = Array.from(document.querySelectorAll('.js-order-container, [data-reactid*="$order-"]'));
        if (!nodes.length) return rows;

        const tryNum = v => { if (v===undefined||v===null) return null; const s=String(v).replace(/[¥,￥,\s]/g,''); const n=Number(s); return isFinite(n)?n:null };

        for (const node of nodes) {
            try {
                const txt = (node.innerText || '').replace(/\u00A0/g,' ');
                const parsed = parseOrderText(txt, showOrderNumberAlways, '');
                for (const r of parsed) rows.push(r);
            } catch (e) { console.debug('rendered-dom parse error', e); }
        }
        return rows;
    }

    // DOM recorder helpers: keep snippets of newly added order nodes for debugging/parsing
    function startTaobaoDomRecorder() {
        try {
            if (!window.__taobao_observed_snippets) window.__taobao_observed_snippets = [];
            if (window.__taobao_dom_observer) return; // already running
            const sel = '.js-order-container, [data-reactid*="$order-"]';
            const mo = new MutationObserver(muts => {
                for (const m of muts) {
                    for (const n of Array.from(m.addedNodes || [])) {
                        try {
                            if (!(n instanceof Element)) continue;
                            if (n.matches && n.matches(sel) || n.querySelector && n.querySelector(sel)) {
                                const el = n.matches && n.matches(sel) ? n : (n.querySelector ? n.querySelector(sel) : null);
                                if (!el) continue;
                                const txt = (el.innerText || '').replace(/\u00A0/g,' ');
                                const snippet = txt.slice(0,2000);
                                window.__taobao_observed_snippets.push({ time: Date.now(), snippet: snippet, node: el });
                                console.info('==[DOM-REC] possible orders node added');
                                console.log(el);
                                console.info('snippet:', snippet);
                            }
                        } catch (e) { /* ignore per-node errors */ }
                    }
                }
            });
            mo.observe(document.documentElement, { childList: true, subtree: true });
            window.__taobao_dom_observer = mo;
            window.getTaobaoObservedSnippets = function() { return window.__taobao_observed_snippets || []; };
            window.stopTaobaoDomRecorder = function() { try { if (window.__taobao_dom_observer) { window.__taobao_dom_observer.disconnect(); delete window.__taobao_dom_observer; } } catch(e){} };
            console.info('Taobao DOM recorder started — navigate pages to collect added order nodes. Use window.getTaobaoObservedSnippets() in Console to read results.');
        } catch (e) { console.error('startTaobaoDomRecorder failed', e); }
    }

    function addJsonExportButton(){
        try {
            const main = document.getElementById('J_bought_main') || document.querySelector('.col-main') || document.body;
            const wrap = document.createElement('div');
            wrap.style.display = 'flex';
            wrap.style.gap = '8px';

            // Keep only three controls to simplify UI: Export (JSON), Start Recorder, Stop Recorder
            const btnExport = document.createElement('input');
            btnExport.type = 'button';
            btnExport.value = 'Export (JSON)';
            Object.assign(btnExport.style, { padding:'8px 14px', background:'#28a745', color:'#fff', borderRadius:'6px', border:'none', cursor:'pointer' });
            btnExport.onclick = exportOrdersFromJson;

            const btnStartRec = document.createElement('input');
            btnStartRec.type = 'button';
            btnStartRec.value = 'Start Recorder';
            Object.assign(btnStartRec.style, { padding:'8px 10px', background:'#6c757d', color:'#fff', borderRadius:'6px', border:'none', cursor:'pointer' });
            btnStartRec.onclick = function(){ try{ startTaobaoDomRecorder(); alert('Recorder gestartet. Navigiere zu anderen Seiten, um Snippets zu sammeln.'); }catch(e){ console.error(e); alert('Start failed - see console'); } };

            const btnStopRec = document.createElement('input');
            btnStopRec.type = 'button';
            btnStopRec.value = 'Stop Recorder';
            Object.assign(btnStopRec.style, { padding:'8px 10px', background:'#adb5bd', color:'#000', borderRadius:'6px', border:'none', cursor:'pointer' });
            btnStopRec.onclick = function(){
                try{
                    if (window.stopTaobaoDomRecorder) {
                        try{ stopTaobaoDomRecorder(); } catch(e){}
                        // gather snippets collected by the recorder
                        const snippets = (window.getTaobaoObservedSnippets && typeof window.getTaobaoObservedSnippets === 'function') ? window.getTaobaoObservedSnippets() : (window.__taobao_observed_snippets || []);
                        if (!snippets || !snippets.length) {
                            alert('Recorder gestoppt. Keine gesammelten Snippets gefunden.');
                            return;
                        }
                        // parse each snippet into rows using existing parseOrderText
                        const allRows = [];
                        for (const s of snippets) {
                            try {
                                const text = (s && s.snippet) ? s.snippet : (s && s.node && s.node.innerText) ? s.node.innerText : '';
                                const parsed = parseOrderText(String(text || ''), true, '');
                                if (parsed && parsed.length) {
                                    for (const r of parsed) allRows.push(r);
                                }
                            } catch (e) { console.debug('snippet parse error', e); }
                        }
                        if (!allRows.length) {
                            alert('Recorder gestoppt. Es konnten keine Bestellungen aus den Snippets geparst werden.');
                            return;
                        }
                        const zhHeader = ["订单号","下单日期","卖家","商品名称","规格","商品链接","商品编号","单价","数量","单项总价","实付款","运费"];
                        const enHeader = zhHeader.map(h => HEADER_MAP[h] || h);
                        const baseName = CONFIG.defaultFilename + '_recorder_' + (new Date()).toISOString().slice(0,19).replace(/[T:]/g,'-');
                        toCsv(enHeader, allRows, baseName);
                        alert('Recorder gestoppt. CSV-Export wurde gestartet.');
                    } else {
                        alert('Recorder not running.');
                    }
                } catch (e) { console.error(e); alert('Stop failed - see console'); }
            };

            wrap.appendChild(btnExport);
            wrap.appendChild(btnStartRec);
            wrap.appendChild(btnStopRec);
            const container = document.createElement('div');
            container.style.margin = '6px';
            container.appendChild(wrap);
            main.insertBefore(container, main.firstChild);
        } catch(e){ console.debug(e); }
    }

    // insert button after short delay to ensure page loaded
    setTimeout(addJsonExportButton, 1200);

})();
