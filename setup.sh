#!/bin/bash
# Setup script for first-time users

echo "🚀 Setting up Taobao HTML Data Extractor..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.11+ first."
    exit 1
fi

echo "✅ Python found"

# Create virtual environment if it doesn't exist
if [ ! -d "extract_html" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv extract_html
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source extract_html/bin/activate 2>/dev/null || extract_html/Scripts/activate

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
fi

# Create output directory if it doesn't exist  
if [ ! -d "output" ]; then
    echo "📁 Creating output directory..."
    mkdir -p output
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Place your Taobao HTML file in: data/input.html"
echo "2. Run: python extract_taobao.py"
echo "3. Check results in: output/"
echo ""
echo "For more information, see README.md"