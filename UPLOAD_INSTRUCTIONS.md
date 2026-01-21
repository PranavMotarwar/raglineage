# Uploading raglineage to PyPI

The package has been successfully built! The distribution files are in the `dist/` directory:

- `raglineage-0.1.0-py3-none-any.whl` (wheel)
- `raglineage-0.1.0.tar.gz` (source distribution)

## Prerequisites

1. **PyPI Account**: Sign up at https://pypi.org/account/register/ if you don't have one
2. **API Token**: Create an API token at https://pypi.org/manage/account/token/
   - For production: Create a token with "Upload packages" scope
   - For test: Create a token at https://test.pypi.org/manage/account/token/

## Upload Methods

### Method 1: Using the upload script (Recommended)

```bash
# Make script executable (if not already)
chmod +x upload_to_pypi.sh

# Upload to Test PyPI first (recommended)
./upload_to_pypi.sh testpypi

# After testing, upload to Production PyPI
./upload_to_pypi.sh pypi
```

When prompted:
- **Username**: `__token__`
- **Password**: Your PyPI API token (starts with `pypi-`)

### Method 2: Manual upload with twine

```bash
# Upload to Test PyPI
python3 -m twine upload --repository testpypi dist/*

# Upload to Production PyPI
python3 -m twine upload dist/*
```

### Method 3: Using environment variables (non-interactive)

```bash
# Set credentials as environment variables
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-api-token-here

# Upload
python3 -m twine upload dist/*
```

### Method 4: Using .pypirc config file

Create `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
username = __token__
password = pypi-your-test-token-here
```

Then upload:
```bash
python3 -m twine upload dist/*
```

## Testing Before Production

**Always test on Test PyPI first:**

```bash
# Upload to Test PyPI
./upload_to_pypi.sh testpypi

# Test installation
pip install --index-url https://test.pypi.org/simple/ raglineage

# Verify it works
python3 -c "from raglineage import RagLineage; print('✅ raglineage installed successfully!')"
```

## After Upload

Once uploaded to PyPI, your package will be available at:
- **Production**: https://pypi.org/project/raglineage/
- **Test**: https://test.pypi.org/project/raglineage/

Users can install with:
```bash
pip install raglineage
```

## Troubleshooting

1. **"Package already exists"**: The version 0.1.0 is already on PyPI. Update version in `pyproject.toml` and rebuild.

2. **"Invalid credentials"**: Double-check your API token and ensure username is `__token__`.

3. **"Network error"**: Check your internet connection and PyPI status.

4. **"Package name conflict"**: The name `raglineage` might be taken. Consider a different name or check https://pypi.org/project/raglineage/

## Next Steps

After successful upload:
1. Verify the package page on PyPI
2. Test installation in a fresh environment
3. Update GitHub repository with PyPI badge
4. Announce the release!
