import re, json, os
p = os.path.abspath(r"d:/Daten/3-PROJECTS/4-EXTRACT_PAPA/data/input.html")
print('reading', p)
with open(p, 'r', encoding='utf-8') as f:
    txt = f.read()
# find var data = JSON.parse('...'); pattern
m = re.search(r"var\s+data\s*=\s*JSON\.parse\('([\s\S]*?)'\);", txt)
if not m:
    print('embedded JSON not found')
    raise SystemExit(1)
raw = m.group(1)
# unescape similar to userscript
s = raw.replace('\\\\','\\').replace('\\"','\"').replace('\\x','\\u00')
try:
    data = json.loads(s)
except Exception as e:
    print('json parse failed', e)
    s2 = s.encode('utf-8').decode('unicode_escape')
    try:
        data = json.loads(s2)
    except Exception as e2:
        print('second parse failed', e2)
        raise
orders = data.get('mainOrders', [])
print('found', len(orders), 'orders')
if not orders:
    raise SystemExit(0)
for idx,o in enumerate(orders[:3], start=1):
    print('\n=== Order', idx, 'id', o.get('orderInfo',{}).get('id') or o.get('id'))
    subs = o.get('subOrders', [])
    print(' subOrders:', len(subs))
    for i,so in enumerate(subs[:10],1):
        pi = so.get('priceInfo') or so.get('payInfo') or {}
        qty = so.get('quantity') or so.get('count') or so.get('num') or ''
        print('  sub', i, 'id', so.get('id'), 'quantity', qty, 'priceInfo keys', list(pi.keys()))
        if 'realTotal' in pi or 'original' in pi:
            print('    realTotal', pi.get('realTotal'), 'original', pi.get('original'))
        ii = so.get('itemInfo', {})
        if 'priceInfo' in ii:
            print('    itemInfo.priceInfo', ii.get('priceInfo'))
        if so.get('itemInfo') and so.get('itemInfo').get('title'):
            print('    title', so['itemInfo']['title'][:80])
print('\ninspection done')
