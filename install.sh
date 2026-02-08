#!/bin/bash
# install.sh

echo "Installing MTSer - MTS Link Webinar Downloader"

# Check Python version
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ $python_version < 3.7 ]]; then
    echo "Error: Python 3.7 or higher is required (found $python_version)"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install httpx tqdm moviepy numpy

# Make script executable
chmod +x mtser.py

echo ""
echo "✅ Installation complete!"
echo ""
echo "To use mtser:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run: python mtser.py --interactive"
echo ""
echo "Or add alias to your shell:"
echo "  echo 'alias mtser=\"$(pwd)/venv/bin/python $(pwd)/mtser.py\"' >> ~/.bashrc"
echo "  source ~/.bashrc"
