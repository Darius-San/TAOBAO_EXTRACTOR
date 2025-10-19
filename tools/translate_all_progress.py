#!/usr/bin/env python3
"""
translate_all_progress.py

Translate any CSV cell that contains Chinese characters (Han) using googletrans,
show per-row progress and optionally write interim output so you can see live progress.

Usage:
  python tools/translate_all_progress.py -i in.csv -o out.csv --write-interval 10

"""
import argparse
import csv
import re
import sys
from time import time, sleep
from pathlib import Path

try:
    from googletrans import Translator
except Exception as e:
    Translator = None

CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')


def has_chinese(s):
    return bool(s and CHINESE_RE.search(s))


def translate_value(translator, text, src='zh-cn', dest='en', retries=2, backoff=0.5):
    if not text:
        return text
    attempt = 0
    while attempt <= retries:
        try:
            res = translator.translate(text, src=src, dest=dest)
            return res.text if hasattr(res, 'text') else str(res)
        except Exception as e:
            attempt += 1
            wait = backoff * attempt
            print(f'  translate failed attempt {attempt} for text len {len(text)}: {e}; retry {wait}s')
            sys.stdout.flush()
            sleep(wait)
    print('  translate ultimately failed, returning original')
    return text


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', '-i', required=True)
    p.add_argument('--output', '-o', required=True)
    p.add_argument('--write-interval', type=int, default=0, help='Write interim output every N rows')
    p.add_argument('--retries', type=int, default=2)
    p.add_argument('--backoff', type=float, default=0.5)
    p.add_argument('--src', default='zh-cn')
    p.add_argument('--dest', default='en')
    args = p.parse_args()

    inp = Path(args.input)
    outp = Path(args.output)
    if not inp.exists():
        print('Input missing:', inp)
        sys.exit(1)

    if Translator is None:
        print('googletrans not available in this interpreter')
        sys.exit(1)

    translator = Translator()

    with inp.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])

    total = len(rows)
    start = time()
    translated_count = 0

    for idx, row in enumerate(rows, start=1):
        changed = False
        for col in fields:
            val = row.get(col)
            if val and has_chinese(val):
                new = translate_value(translator, val, src=args.src, dest=args.dest, retries=args.retries, backoff=args.backoff)
                if new != val:
                    row[col] = new
                translated_count += 1
                changed = True
        # progress
        elapsed = time() - start
        rate = idx / elapsed if elapsed>0 else 0
        remaining = total - idx
        eta = remaining / rate if rate>0 else float('inf')
        print(f'Row {idx}/{total}  translated_items={translated_count}  rate={rate:.2f}/s  ETA={eta:.0f}s')
        sys.stdout.flush()

        # interim write
        if args.write_interval and idx % args.write_interval == 0:
            with outp.open('w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows[:idx])
            print(f'Wrote interim {idx} rows to {outp}')

    # final write
    with outp.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f'Done. Wrote {outp}. Translated cell updates: {translated_count}')


if __name__ == '__main__':
    main()
