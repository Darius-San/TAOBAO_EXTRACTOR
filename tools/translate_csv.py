#!/usr/bin/env python3
"""
translate_csv.py

Small utility to translate a CSV column from Chinese to English.
Usage examples:
  # Using googletrans (unofficial) for live translation:
  python tools/translate_csv.py --input output/taobao_products_english.csv --column "商品名称" --output output/taobao_products_english_translated.csv --service googletrans

  # Using a local mapping JSON file (fast, offline):
  python tools/translate_csv.py --input output/taobao_products_english.csv --column "商品名称" --output output/taobao_products_english_translated.csv --service map --map-file tools/translation_map.json

Notes:
- googletrans is unofficial and may fail if Google blocks it. Use it for small batches.
- For production use, consider Google Cloud Translate or DeepL API (requires API key).
"""

import argparse
import csv
import json
import sys
from pathlib import Path


def translate_with_map(text, mapping):
    return mapping.get(text, text)


def translate_with_googletrans(texts):
    try:
        from googletrans import Translator
    except Exception as e:
        raise RuntimeError("googletrans not installed. Install with: pip install googletrans==4.0.0-rc1")
    translator = Translator()
    # googletrans can accept list of texts
    translated = []
    # chunk to avoid very large calls
    chunk = []
    CHUNK_SIZE = 50
    for t in texts:
        chunk.append(t)
        if len(chunk) >= CHUNK_SIZE:
            res = translator.translate(chunk, src='zh-cn', dest='en')
            translated.extend([r.text for r in res])
            chunk = []
    if chunk:
        res = translator.translate(chunk, src='zh-cn', dest='en')
        translated.extend([r.text for r in res])
    return translated


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', '-i', required=True, help='Input CSV file path')
    p.add_argument('--output', '-o', required=True, help='Output CSV file path')
    p.add_argument('--column', '-c', required=True, help='Column name to translate (header)')
    p.add_argument('--service', '-s', choices=['map', 'googletrans'], default='map', help='Translation service: map (local) or googletrans (live)')
    p.add_argument('--map-file', help='Path to JSON map file (required when service==map)')
    args = p.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    # Read CSV
    with input_path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if args.column not in fieldnames:
        print(f"Column '{args.column}' not found in CSV headers: {fieldnames}")
        sys.exit(1)

    texts = [row[args.column] for row in rows]

    if args.service == 'map':
        if not args.map_file:
            print('map-file is required for service=map')
            sys.exit(1)
        map_path = Path(args.map_file)
        if not map_path.exists():
            print(f'Map file not found: {map_path}')
            sys.exit(1)
        with map_path.open('r', encoding='utf-8') as mf:
            mapping = json.load(mf)
        translated = [translate_with_map(t, mapping) for t in texts]
    else:
        translated = translate_with_googletrans(texts)

    # Write output CSV: add new column with suffix _en
    out_field = args.column + '_en'
    if out_field in fieldnames:
        print(f'Output column {out_field} already exists, will overwrite')
    if out_field not in fieldnames:
        fieldnames.append(out_field)

    for i, row in enumerate(rows):
        row[out_field] = translated[i]

    with output_path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f'Wrote translated CSV to {output_path}')

if __name__ == '__main__':
    main()
