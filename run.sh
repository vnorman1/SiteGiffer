#!/bin/bash
# ============================================================
# SiteGiffer - Quick Run Script
# ============================================================

cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found!"
    echo "Please run: ./setup.sh first"
    exit 1
fi

# Activate venv and run
source venv/bin/activate
python SiteGiffer.py
