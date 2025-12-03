#!/bin/bash
# ==============================================================
# Web to GIF Portfolio Showcase - Setup Script
# ==============================================================
# This script creates a virtual environment and installs all
# required dependencies for the Web to GIF generator.
# ==============================================================

set -e  # Exit on error

echo "=================================================="
echo "🚀 Web to GIF Portfolio Showcase - Setup"
echo "=================================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo ""
echo "🌐 Installing Playwright Chromium browser..."
playwright install chromium

# Create recordings directory
echo ""
echo "📁 Creating recordings directory..."
mkdir -p recordings

echo ""
echo "=================================================="
echo "✅ Setup complete!"
echo "=================================================="
echo ""
echo "To use SiteGiffer:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the interactive CLI:"
echo "     python SiteGiffer.py"
echo ""
echo "=================================================="
