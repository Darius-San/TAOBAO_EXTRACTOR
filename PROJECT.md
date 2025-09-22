---
name: Taobao HTML Data Extractor
description: Professional Python tool for extracting and translating Taobao purchase data from HTML to English CSV/Markdown
author: Data Extraction Team
version: 1.0.0
license: MIT
topics:
  - data-extraction
  - taobao
  - html-parsing
  - translation
  - csv-export
  - python
languages:
  - Python
homepage: https://github.com/yourusername/taobao-data-extractor
issues: https://github.com/yourusername/taobao-data-extractor/issues
---

# Project Overview

This repository contains a complete, production-ready tool for extracting Taobao purchase data from HTML files and converting everything to English.

## 🎯 Purpose
Extract 75+ products from Taobao purchase history HTML files with complete English translations, proper seller mapping, and purchase date assignment.

## 🏗️ Architecture
- **JSON-based parsing**: Robust data extraction from HTML
- **Translation system**: 47+ product translations, 59+ color mappings
- **Seller mapping**: Intelligent English seller name assignment  
- **Date handling**: Complete purchase date reconstruction
- **Output formats**: UTF-8-BOM CSV (Excel-compatible) and Markdown

## 📊 Statistics
- **Products extracted**: 75
- **Translation coverage**: 100% (no Chinese characters remain)
- **Seller mappings**: 25+ intelligent mappings
- **Output formats**: 2 (CSV + Markdown)
- **Dependencies**: 4 (BeautifulSoup4, pandas, lxml, html5lib)

## 🚀 Quick Start
1. Run `setup.bat` (Windows) or `setup.sh` (Unix)
2. Place HTML file in `data/input.html`
3. Execute `python extract_taobao.py`
4. Find results in `output/` directory

## 📁 Repository Structure
```
├── 📄 Core Files
│   ├── extract_taobao.py      # Main extraction script
│   ├── requirements.txt       # Python dependencies
│   └── data/input.html       # Your HTML file goes here
│
├── 📊 Output
│   ├── example_output.csv    # Sample CSV output
│   ├── example_output.md     # Sample Markdown output
│   └── output/               # Generated results
│
├── 📚 Documentation
│   ├── README.md            # Complete user guide
│   ├── QUICKSTART.md        # Quick setup instructions  
│   ├── CONTRIBUTING.md      # Development guidelines
│   ├── CHANGELOG.md         # Version history
│   └── GIT_SETUP.md         # Git installation guide
│
├── 🔧 Setup & Configuration
│   ├── setup.bat           # Windows setup script
│   ├── setup.sh            # Unix setup script
│   ├── .gitignore          # Git ignore rules
│   ├── .gitattributes      # Git line ending config
│   └── LICENSE             # MIT License
│
└── 🤖 Automation
    └── .github/workflows/
        └── ci.yml          # GitHub Actions CI/CD
```

This is a professional, Git-ready project structure suitable for open-source distribution and collaborative development.