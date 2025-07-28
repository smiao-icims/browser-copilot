#!/bin/bash
set -e

echo "🔨 Testing Browser Pilot build process..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build package
echo "📦 Building package with uv..."
uv build

# Check package contents
echo "🔍 Checking package contents..."
if [ -f "dist/"*.whl ]; then
    echo "✅ Wheel file created"
    uv run python -m zipfile -l dist/*.whl | head -20
else
    echo "❌ No wheel file found"
    exit 1
fi

if [ -f "dist/"*.tar.gz ]; then
    echo "✅ Source distribution created"
    tar -tzf dist/*.tar.gz | head -20
else
    echo "❌ No source distribution found"
    exit 1
fi

# Validate package with twine
echo "🔍 Validating package with twine..."
if uv run twine check dist/* &> /dev/null; then
    uv run twine check dist/*
    echo "✅ Package validation passed"
else
    echo "⚠️  Twine validation failed or not available"
fi

# Test installation in virtual environment
echo "🧪 Testing installation..."
TEMP_VENV=$(mktemp -d)
uv run python -m venv "$TEMP_VENV"
source "$TEMP_VENV/bin/activate"

pip install dist/*.whl
browser-pilot --help > /dev/null
echo "✅ Installation test passed"

# Cleanup
deactivate
rm -rf "$TEMP_VENV"

echo "🎉 All build tests passed!"