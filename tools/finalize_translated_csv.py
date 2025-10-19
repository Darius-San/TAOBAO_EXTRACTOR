#!/usr/bin/env python3
"""
finalize_translated_csv.py

Overwrite original Chinese fields with their *_en translations (if present),
translate common Chinese headers to English, drop the helper *_en columns and
write a final English CSV.

Usage:
  python tools/finalize_translated_csv.py -i input.csv -o output.csv

"""
import argparse
import csv
from pathlib import Path

HEADER_MAP = {
    '订单号': 'order_id',
    '商品名称': 'title',
    '商品链接': 'item_url',
    '单价': 'unit_price',
    '数量': 'quantity',
    '实付款': 'paid',
    '状态': 'status',
    '快递单号': 'tracking_number',
}


def finalize(input_path: Path, output_path: Path):
    with input_path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    # find *_en columns
    en_cols = [c for c in fieldnames if c.endswith('_en')]

    # For each en column, compute base and overwrite base values
    for en in en_cols:
        base = en[:-3]
        for r in rows:
            en_val = r.get(en)
            if en_val is not None and en_val != '':
                # overwrite base cell (even if empty)
                r[base] = en_val

    # Remove en columns from fieldnames
    for en in en_cols:
        if en in fieldnames:
            fieldnames.remove(en)

    # Translate headers using HEADER_MAP; unknown headers are kept but normalized to ascii-like safe names
    out_fieldnames = []
    for h in fieldnames:
        out_fieldnames.append(HEADER_MAP.get(h, h))

    # Build rows with translated headers
    out_rows = []
    for r in rows:
        out_r = {}
        for i, h in enumerate(fieldnames):
            out_key = out_fieldnames[i]
            out_r[out_key] = r.get(h, '')
        out_rows.append(out_r)

    # Write final CSV
    with output_path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f'Wrote finalized CSV to {output_path} with headers: {out_fieldnames}')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', '-i', required=True)
    p.add_argument('--output', '-o', required=True)
    args = p.parse_args()
    inp = Path(args.input)
    out = Path(args.output)
    if not inp.exists():
        print('Input not found:', inp)
        return
    finalize(inp, out)


if __name__ == '__main__':
    main()
