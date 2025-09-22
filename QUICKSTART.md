# Taobao HTML Data Extractor

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Place your HTML file:**
   - Save your Taobao purchase history as HTML
   - Copy it to: `data/input.html`

3. **Run extraction:**
   ```bash
   python extract_taobao.py
   ```

4. **Check output:**
   - CSV: `output/taobao_products_english.csv`
   - Markdown: `output/taobao_products_english.md`

## What it does

Extracts Taobao purchase data and converts everything to English:
- ✅ Product names (47+ translations)
- ✅ Color classifications (59+ translations)
- ✅ Seller names (25+ intelligent mappings)
- ✅ Purchase dates (based on order patterns)
- ✅ Complete CSV output for Excel

See `README.md` for full documentation.