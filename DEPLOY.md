# Deploying to PyPI

This guide explains how to deploy raglineage to PyPI.

## Prerequisites

1. Install build tools:
   ```bash
   pip install build twine
   ```

2. Create PyPI account:
   - Sign up at https://pypi.org/account/register/
   - Create API token at https://pypi.org/manage/account/token/

## Building the Package

1. Clean previous builds:
   ```bash
   rm -rf dist/ build/ *.egg-info
   ```

2. Build the package:
   ```bash
   python -m build
   ```

   This creates:
   - `dist/raglineage-0.1.0.tar.gz` (source distribution)
   - `dist/raglineage-0.1.0-py3-none-any.whl` (wheel)

## Testing the Build

Test the build locally before uploading:

```bash
pip install dist/raglineage-0.1.0-py3-none-any.whl
```

## Uploading to PyPI

### Test PyPI (recommended first step)

1. Upload to Test PyPI:
   ```bash
   twine upload --repository testpypi dist/*
   ```

2. Test installation from Test PyPI:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ raglineage
   ```

### Production PyPI

Once tested, upload to production PyPI:

```bash
twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token

## Version Updates

To release a new version:

1. Update version in `pyproject.toml`:
   ```toml
   version = "0.1.1"
   ```

2. Update version in `raglineage/__init__.py`:
   ```python
   __version__ = "0.1.1"
   ```

3. Build and upload as above.

## Notes

- Always test on Test PyPI first
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Update CHANGELOG.md (if maintained) with each release
