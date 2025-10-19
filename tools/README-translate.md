translate_csv.py

Small helper to translate the Chinese product title column in a CSV file.

Usage examples:

1) Using a local mapping (recommended if you already have translations):

python tools/translate_csv.py \
  --input output/taobao_products_english.csv \
  --output output/taobao_products_translated.csv \
  --column "商品名称" \
  --service map \
  --map-file tools/translation_map.json

2) Using googletrans (unofficial) for small batches:

pip install -r requirements.txt
python tools/translate_csv.py \
  --input output/taobao_products_english.csv \
  --output output/taobao_products_translated.csv \
  --column "商品名称" \
  --service googletrans

Notes:
- googletrans is unofficial and may fail under heavy use.
- For production, consider using Google Cloud Translate or DeepL API and adapt the script accordingly.
