#!/usr/bin/env python3
"""
finalize_translated_csv.py

Small utility to post-process translated CSVs created by the translation pipeline.
It maps Chinese column names to canonical English names (when possible) and removes
rows that are empty or where both the product title and any price field are missing.

Usage:
  python tools/finalize_translated_csv.py -i input_no_chinese.csv -o output_final.csv

If -o is omitted the script writes to the input path with '_final' appended before
the extension.

This script is intentionally small and dependency-free (uses only the stdlib).
"""
from __future__ import annotations

import argparse
import csv
import os
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import sys
from typing import List, Dict, Tuple


HEADER_MAP = {
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
    '运费': 'lieferkosten'
}

# Canonical header ordering we prefer in the final CSV
CANONICAL_HEADERS = [
    'order_id', 'order_date', 'seller', 'title', 'specification',
    'item_url', 'item_id', 'unit_price', 'quantity', 'item_total', 'paid', 'lieferkosten'
]

# Characters considered meaningful (alphanumeric or CJK)
MEANINGFUL_RE = re.compile(r'[0-9A-Za-z\u4e00-\u9fff]')


def read_csv_rows(path: str) -> List[List[str]]:
    with open(path, 'r', encoding='utf-8-sig', newline='') as fh:
        reader = csv.reader(fh)
        return [row for row in reader]


def write_csv_rows(path: str, header: List[str], rows: List[List[str]]) -> None:
    with open(path, 'w', encoding='utf-8-sig', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for r in rows:
            writer.writerow(r)


def map_headers(input_header: List[str]) -> List[str]:
    # Map Chinese headers to english using HEADER_MAP, otherwise keep as-is
    mapped = []
    for h in input_header:
        key = h.strip()
        mapped.append(HEADER_MAP.get(key, key))
    return mapped


def row_is_meaningful(row: List[str]) -> bool:
    # Any cell that contains at least one meaningful char qualifies the row
    for c in row:
        if c and MEANINGFUL_RE.search(c):
            return True
    return False


def clean_rows(input_header: List[str], input_rows: List[List[str]], collapse_groups: bool = True, zero_shipping_if_equal: bool = True) -> Tuple[List[str], List[List[str]]]:
    # Map header names
    mapped_header = map_headers(input_header)

    # Determine indices for title and price columns (by mapped header name)
    h_lower = [h.lower() for h in mapped_header]
    title_idx = None
    for candidate in ('title', '商品名称'):
        if candidate in h_lower:
            title_idx = h_lower.index(candidate)
            break

    # price-ish columns
    price_candidates = ['unit_price', 'item_total', 'paid', '单价', '单项总价', '实付款']
    price_idxs = [i for i, hn in enumerate(h_lower) if hn in price_candidates]

    out_rows: List[List[str]] = []

    for row in input_rows:
        # normalize row length to header
        if len(row) < len(mapped_header):
            row = row + [''] * (len(mapped_header) - len(row))
        elif len(row) > len(mapped_header):
            row = row[:len(mapped_header)]

        # quick drop: completely empty or not meaningful at all
        if not row_is_meaningful(row):
            continue

        # drop rows that lack both title and any price information
        title_val = ''
        if title_idx is not None and title_idx < len(row):
            title_val = (row[title_idx] or '').strip()

        price_present = False
        for pi in price_idxs:
            if pi < len(row):
                v = (row[pi] or '').strip()
                if v and re.search(r'[0-9]', v):
                    price_present = True
                    break

        # If there's no title AND no price, drop the row
        if not title_val and not price_present:
            continue

        out_rows.append(row)

    # If group collapse disabled, simply return mapped header and rows
    if not collapse_groups:
        final_header = []
        header_to_index: Dict[str, int] = {mapped_header[i].lower(): i for i in range(len(mapped_header))}
        for ch in CANONICAL_HEADERS:
            final_header.append(ch)
        final_rows: List[List[str]] = []
        for r in out_rows:
            newr: List[str] = []
            for fh in final_header:
                idx = header_to_index.get(fh)
                if idx is not None and idx < len(r):
                    newr.append(r[idx])
                else:
                    newr.append('')
            final_rows.append(newr)
        return final_header, final_rows

    # Build list of dict rows keyed by mapped_header
    mapped_lower = [h.lower() for h in mapped_header]
    rows_dicts: List[Dict[str, str]] = []
    for r in out_rows:
        d: Dict[str, str] = {}
        for i, h in enumerate(mapped_header):
            d[h.lower()] = r[i] if i < len(r) else ''
        rows_dicts.append(d)

    # Group by order_id (empty order_id -> unique group per-row)
    groups: Dict[str, List[int]] = {}
    for idx, d in enumerate(rows_dicts):
        oid = (d.get('order_id') or '').strip()
        if oid:
            groups.setdefault(oid, []).append(idx)
        else:
            # make unique key for empty-order rows
            groups.setdefault(f'__row_{idx}', []).append(idx)

    def parse_decimal(s: str) -> Decimal | None:
        if not s:
            return None
        try:
            # remove currency symbols and commas
            s2 = re.sub(r'[¥￥,\s]', '', s)
            return Decimal(s2)
        except (InvalidOperation, TypeError):
            return None

    final_rows_dicts: List[Dict[str, str]] = []

    # Process each group
    for gid, idxs in groups.items():
        # compute per-row item total where possible
        per_row_item_totals: List[Decimal] = []
        paid_val: Decimal | None = None
        # collect numeric sums
        for i in idxs:
            d = rows_dicts[i]
            unit = parse_decimal(d.get('unit_price') or d.get('单价') or '')
            qty_raw = (d.get('quantity') or d.get('数量') or '').strip()
            qty = None
            try:
                qty = Decimal(qty_raw) if qty_raw else None
            except (InvalidOperation, TypeError):
                qty = None

            item_total = parse_decimal(d.get('item_total') or d.get('单项总价') or '')

            computed = None
            if unit is not None and qty is not None:
                computed = (unit * qty).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            elif item_total is not None:
                computed = item_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            if computed is not None:
                per_row_item_totals.append(computed)

            if paid_val is None:
                p = parse_decimal(d.get('paid') or d.get('实付款') or '')
                if p is not None:
                    paid_val = p.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        sum_items = sum(per_row_item_totals) if per_row_item_totals else Decimal('0.00')

        # determine shipping for the order if paid present
        shipping_calc: Decimal | None = None
        if paid_val is not None:
            if zero_shipping_if_equal and (sum_items == paid_val):
                shipping_calc = Decimal('0.00')
            else:
                # shipping = paid - sum_items (may be negative if data inconsistent)
                shipping_calc = (paid_val - sum_items).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Emit rows: first item keeps order_id/paid/shipping, others have those cleared
        first = True
        for i in idxs:
            d = dict(rows_dicts[i])  # copy
            if first:
                # ensure paid and lieferkosten set according to shipping_calc when available
                if shipping_calc is not None:
                    d['lieferkosten'] = str(shipping_calc)
                # ensure paid field normalized
                if paid_val is not None:
                    d['paid'] = str(paid_val)
                first = False
                final_rows_dicts.append(d)
            else:
                # clear order-level fields
                d['order_id'] = ''
                d['paid'] = ''
                d['lieferkosten'] = ''
                final_rows_dicts.append(d)

    # Build final header in canonical order and rows
    header_to_index: Dict[str, int] = {mapped_header[i].lower(): i for i in range(len(mapped_header))}
    final_header = [h for h in CANONICAL_HEADERS]
    final_rows: List[List[str]] = []
    for d in final_rows_dicts:
        newr: List[str] = []
        for fh in final_header:
            newr.append(d.get(fh, ''))
        final_rows.append(newr)

    return final_header, final_rows

    # Reorder the header to canonical order where possible; for missing canonical columns,
    # leave other columns in their mapped form appended after canonical ones.
    final_header = []
    header_to_index: Dict[str, int] = {mapped_header[i].lower(): i for i in range(len(mapped_header))}

    for ch in CANONICAL_HEADERS:
        if ch in header_to_index:
            final_header.append(ch)
        else:
            # if canonical header absent, still include it to keep consistent column count
            final_header.append(ch)

    # Build final rows aligned to final_header (pull values from mapped_header positions when available)
    final_rows: List[List[str]] = []
    for r in out_rows:
        newr: List[str] = []
        for fh in final_header:
            idx = header_to_index.get(fh)
            if idx is not None and idx < len(r):
                newr.append(r[idx])
            else:
                newr.append('')
        final_rows.append(newr)

    return final_header, final_rows


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Finalize translated Taobao CSV: map headers and drop junk rows')
    p.add_argument('-i', '--input', required=True, help='Input CSV path (translated, possibly _no_chinese.csv)')
    p.add_argument('-o', '--output', required=False, help='Output CSV path (defaults to input + _final.csv)')
    p.add_argument('--no-collapse', dest='collapse', action='store_false', help='Do not collapse Sammelbestellungen (keep order_id/paid/shipping on every row)')
    p.add_argument('--no-zero-shipping', dest='zero_shipping', action='store_false', help='Do not force shipping to 0 when sum(items)==paid')
    p.add_argument('--preview', type=int, default=0, help='Print a preview of first N cleaned rows to stdout')
    return p.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    inp = args.input
    out = args.output
    if not out:
        base, ext = os.path.splitext(inp)
        out = base + '_final' + (ext or '.csv')

    if not os.path.exists(inp):
        print(f'Input file not found: {inp}', file=sys.stderr)
        return 2

    rows = read_csv_rows(inp)
    if not rows:
        print('No rows read from input', file=sys.stderr)
        return 3

    input_header = rows[0]
    input_data = rows[1:]

    final_header, final_rows = clean_rows(input_header, input_data, collapse_groups=args.collapse, zero_shipping_if_equal=args.zero_shipping)

    write_csv_rows(out, final_header, final_rows)

    print(f'Wrote {len(final_rows)} rows to {out} (from {len(input_data)} input rows)')
    if args.preview and args.preview > 0:
        print('\nPreview:')
        # print header then first N rows
        print(','.join(final_header))
        for r in final_rows[:args.preview]:
            print(','.join(r))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
