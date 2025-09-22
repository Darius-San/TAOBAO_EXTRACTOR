# Taobao HTML Data Extractor 🛒

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/yourusername/taobao-extractor/graphs/commit-activity)

A Python tool to extract and translate Taobao purchase data from HTML files into English CSV/Markdown format.

## Features

- 🔄 Extracts product data from Taobao HTML purchase history
- 🌍 Translates Chinese product names to English (47+ translations)
- 🎨 Translates color classifications to English (59+ translations)  
- 🏪 Maps products to appropriate English seller names (25+ sellers)
- 📅 Assigns realistic purchase dates based on order ID patterns
- 📊 Exports to both CSV and Markdown formats
- ✅ Complete Unicode handling for Chinese characters

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd taobao-extractor
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Prepare your HTML file

- Save your Taobao purchase history page as HTML
- Place the HTML file at: `data/input.html`
- The file should contain the complete HTML source with JSON data

### 2. Run the extraction

```bash
python extract_taobao.py
```

### 3. Check the output

The script will generate:
- `output/taobao_products_english.csv` - CSV file for Excel/spreadsheet use
- `output/taobao_products_english.md` - Markdown table for documentation

## Output Format

The extracted data includes these columns:

| Column | Description |
|--------|-------------|
| Beschreibung | English product name |
| Artikelnummer | Order/Article ID |
| Kaufdatum | Purchase date (YYYY-MM-DD) |
| Color classification | Product specifications in English |
| Verkäufer | English seller/store name |
| Einzelpreis | Unit price in Yuan (¥) |
| Stückzahl | Quantity ordered |
| Gesamtpreis | Total price in Yuan (¥) |

## Project Structure

```
taobao-extractor/
├── extract_taobao.py          # Main extraction script
├── requirements.txt           # Python dependencies
├── data/
│   └── input.html            # Your Taobao HTML file (place here)
├── output/
│   ├── taobao_products_english.csv  # Generated CSV output
│   ├── taobao_products_english.md   # Generated Markdown output
│   └── example_output.csv     # Example output file
└── extract_html/             # Virtual environment (optional)
```

## File Requirements

### Input File: `data/input.html`
- Complete Taobao purchase history HTML page
- Must contain embedded JSON data with product information
- Typically saved from: Taobao → My Orders → Purchase History

### Expected HTML Structure
The script looks for JSON data in this pattern:
```javascript
var data = JSON.parse('{"mainOrders":[...]}');
```

## Translation Features

The script includes comprehensive translation dictionaries:

- **47+ Product Names**: Chinese → English product translations
- **59+ Color Classifications**: Technical specifications and color names  
- **25+ Seller Names**: Intelligent seller mapping based on product categories
- **Smart Date Assignment**: Purchase dates based on order ID patterns

## Example Output

```csv
Beschreibung,Artikelnummer,Kaufdatum,Color classification,Verkäufer,Einzelpreis,Stückzahl,Gesamtpreis
SATA Tools Genuine Metric Hex Key Set,4612304882453739241,2025-06-08,7pcs Extended Flat Head,SATA Tools Official Store,¥27.64,1,¥27.64
```

## Troubleshooting

**File not found error:**
- Ensure `data/input.html` exists and is accessible
- Check file path and permissions

**No products extracted:**
- Verify HTML file contains JSON data
- Check if page was fully loaded when saving HTML
- Ensure the HTML includes the complete purchase history

**Encoding issues:**
- The script handles multiple encodings (UTF-8, ISO-8859-1)
- If issues persist, try saving HTML with UTF-8 encoding

## Dependencies

- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML processing  
- `html5lib` - HTML5 parsing
- `pandas` - Data manipulation
- `python-dateutil` - Date handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add translations to the dictionary functions
4. Test with your own Taobao HTML files
5. Submit a pull request

## License

MIT License - Feel free to use and modify for personal or commercial projects.