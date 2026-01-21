#!/bin/bash
# Deployment script for raglineage to PyPI

set -e

echo "🚀 Deploying raglineage to PyPI"
echo "================================"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the raglineage root directory."
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info 2>/dev/null || true

# Install build tools
echo "📦 Installing build tools..."
python3 -m pip install --upgrade build twine --quiet

# Build the package
echo "🔨 Building package..."
python3 -m build

# Check if build was successful
if [ ! -d "dist" ]; then
    echo "❌ Error: Build failed. dist/ directory not found."
    exit 1
fi

echo "✅ Build successful!"
echo ""
echo "📦 Built packages:"
ls -lh dist/

echo ""
echo "📤 Ready to upload to PyPI"
echo ""
echo "To upload to Test PyPI (recommended first):"
echo "  python3 -m twine upload --repository testpypi dist/*"
echo ""
echo "To upload to Production PyPI:"
echo "  python3 -m twine upload dist/*"
echo ""
echo "You'll need:"
echo "  - Username: __token__"
echo "  - Password: Your PyPI API token (get from https://pypi.org/manage/account/token/)"
echo ""

# Ask if user wants to upload now
read -p "Upload to PyPI now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Upload to Test PyPI (t) or Production (p)? " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Tt]$ ]]; then
        echo "Uploading to Test PyPI..."
        python3 -m twine upload --repository testpypi dist/*
    elif [[ $REPLY =~ ^[Pp]$ ]]; then
        echo "Uploading to Production PyPI..."
        python3 -m twine upload dist/*
    else
        echo "Skipping upload."
    fi
fi

echo ""
echo "✅ Deployment script complete!"
