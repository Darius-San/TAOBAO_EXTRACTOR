import re
import json
from pathlib import Path

def unescape_embedded_json(s: str) -> str:
    # mirror the JS unescapeEmbeddedJson
    s = s.replace('\\\\', '\\')
    s = s.replace('\\"', '"')
    # convert \xYY to \u00YY so Python unicode decoding can handle it
    s = re.sub(r'\\x([0-9A-Fa-f]{2})', lambda m: '\\u00' + m.group(1), s)
    try:
        # decode escaped sequences
        return bytes(s, 'utf-8').decode('unicode_escape')
    except Exception:
        return s

def extract_embedded_json_from_file(path: Path):
    txt = path.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r"var\s+data\s*=\s*JSON\.parse\('([\s\S]*?)'\);", txt)
    if not m:
        print('No embedded JSON match found in', path)
        return None
    raw = m.group(1)
    dec = unescape_embedded_json(raw)
    try:
        data = json.loads(dec)
        return data
    except Exception as e:
        print('JSON parse failed:', e)
        # try a best-effort fallback: replace single backslashes
        try:
            fix = dec.replace('\\', '\\\\')
            data = json.loads(fix)
            return data
        except Exception as e2:
            print('Fallback parse failed:', e2)
            return None

def summarize(data):
    if not isinstance(data, dict):
        print('Parsed data is not an object')
        return
    main = data.get('mainOrders') or []
    print('mainOrders count =', len(main))
    if not main:
        return
    o = main[0]
    print('First order keys:', list(o.keys())[:10])
    subs = o.get('subOrders') or []
    print('First order subOrders count =', len(subs))
    if subs:
        s0 = subs[0]
        print('First subOrder example keys:', list(s0.keys())[:10])
        # try to show some price-related fields
        pi = s0.get('priceInfo') or {}
        print('subOrder.priceInfo keys:', list(pi.keys()))
        print('subOrder.totalFee / totalPayment:', s0.get('totalFee'), s0.get('totalPayment'))

if __name__ == '__main__':
    p = Path('data/input.html')
    if not p.exists():
        print('data/input.html not found in workspace')
    else:
        data = extract_embedded_json_from_file(p)
        if data is None:
            print('No data extracted')
        else:
            summarize(data)
