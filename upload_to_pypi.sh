#!/bin/bash
# Upload raglineage to PyPI
# Usage: ./upload_to_pypi.sh [testpypi|pypi]

set -e

REPO="${1:-pypi}"

if [ "$REPO" != "testpypi" ] && [ "$REPO" != "pypi" ]; then
    echo "Usage: $0 [testpypi|pypi]"
    echo "  testpypi - Upload to Test PyPI"
    echo "  pypi     - Upload to Production PyPI (default)"
    exit 1
fi

if [ ! -d "dist" ]; then
    echo "❌ Error: dist/ directory not found. Run build first."
    exit 1
fi

echo "📤 Uploading to $REPO..."
echo ""

if [ "$REPO" == "testpypi" ]; then
    python3 -m twine upload --repository testpypi dist/*
else
    python3 -m twine upload dist/*
fi

echo ""
echo "✅ Upload complete!"
echo ""
if [ "$REPO" == "testpypi" ]; then
    echo "Test installation with:"
    echo "  pip install --index-url https://test.pypi.org/simple/ raglineage"
else
    echo "Install with:"
    echo "  pip install raglineage"
fi
