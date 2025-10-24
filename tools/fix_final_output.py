import csv
from pathlib import Path

IN = Path('final_output/taobao_orders_no_chinese.csv')
OUT = Path('final_output/taobao_orders_no_chinese_fixed.csv')

def try_num(s):
    if s is None: return None
    s = str(s).strip()
    if s == '': return None
    # remove non-numeric except dot and minus
    import re
    cleaned = re.sub(r"[^0-9.\-]", '', s)
    try:
        return float(cleaned)
    except:
        return None

if not IN.exists():
    print('Input file not found:', IN)
    raise SystemExit(1)

with IN.open('r', encoding='utf-8-sig', newline='') as f:
    reader = csv.reader(f)
    rows = list(reader)

if not rows:
    print('No rows found')
    raise SystemExit(1)

hdr = rows[0]
# detect columns (lowercase header names)
col_idx = {c: i for i, c in enumerate(hdr)}

# expected existing columns may contain status and tracking_number
# Build new header: order_id,order_date,seller,title,item_url,unit_price,quantity,item_total,paid,spec
new_hdr = ['order_id','order_date','seller','title','item_url','unit_price','quantity','item_total','paid','spec']

out_rows = [new_hdr]
for r in rows[1:]:
    # ensure row length
    if len(r) < len(hdr):
        r = r + [''] * (len(hdr)-len(r))
    # helper fetch
    def g(name):
        return r[col_idx[name]] if name in col_idx and col_idx[name] < len(r) else ''

    order_id = g('order_id') if 'order_id' in col_idx else g('订单号') if '订单号' in col_idx else ''
    order_date = g('order_date') if 'order_date' in col_idx else g('下单日期') if '下单日期' in col_idx else ''
    seller = g('seller') if 'seller' in col_idx else g('卖家') if '卖家' in col_idx else ''
    title = g('title') if 'title' in col_idx else g('商品名称') if '商品名称' in col_idx else ''
    item_url = g('item_url') if 'item_url' in col_idx else g('商品链接') if '商品链接' in col_idx else ''
    unit_price = g('unit_price') if 'unit_price' in col_idx else g('单价') if '单价' in col_idx else ''
    quantity = g('quantity') if 'quantity' in col_idx else g('数量') if '数量' in col_idx else ''
    paid = g('paid') if 'paid' in col_idx else g('实付款') if '实付款' in col_idx else ''
    spec = g('spec') if 'spec' in col_idx else g('规格') if '规格' in col_idx else ''

    up = try_num(unit_price)
    qn = try_num(quantity)
    if up is not None and qn is not None:
        item_total = f"{(up*qn):.2f}"
    else:
        # try to take existing item_total if present
        if 'item_total' in col_idx:
            item_total = r[col_idx['item_total']]
        elif '单项总价' in col_idx:
            item_total = r[col_idx['单项总价']]
        else:
            item_total = ''

    out_rows.append([order_id,order_date,seller,title,item_url,unit_price,quantity,item_total,paid,spec])

with OUT.open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(out_rows)

print('Wrote', OUT)
