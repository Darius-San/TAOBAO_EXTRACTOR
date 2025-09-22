# Contributing to Taobao HTML Data Extractor

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/taobao-extractor.git
   cd taobao-extractor
   ```

2. **Create virtual environment**
   ```bash
   python -m venv extract_html
   # Windows
   extract_html\Scripts\activate
   # Unix/macOS  
   source extract_html/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow Python PEP 8 style guidelines
   - Add comments for complex logic
   - Update translations if needed

3. **Test your changes**
   ```bash
   python extract_taobao.py
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Add: your feature description"
   git push origin feature/your-feature-name
   ```

## Translation Contributions

To add new product translations:

1. Edit the `get_english_translations()` function in `extract_taobao.py`
2. Add exact Chinese text as key and English translation as value
3. Test with your HTML file
4. Submit pull request

## Bug Reports

Please include:
- Python version
- Operating system
- Error message
- Sample HTML (anonymized)

## Questions?

Open an issue or contact the maintainers.