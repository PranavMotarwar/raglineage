# Contributing to raglineage

Thank you for your interest in contributing to raglineage! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/raglineage.git
   cd raglineage
   ```
3. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```
4. Run tests to ensure everything works:
   ```bash
   pytest
   ```

## Code Style

- Use **type hints** everywhere (Python ≥ 3.10)
- Follow **PEP 8** style guidelines
- Use **ruff** for linting (configuration in `pyproject.toml`)
- Use **pydantic** models for all data schemas
- Write **docstrings** for all public functions and classes

## Testing

- Write tests for all new features
- Aim for high test coverage
- Tests should be in `tests/` directory

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass: `pytest`
5. Run linting: `ruff check .`
6. Update documentation if needed
7. Submit a pull request with a clear description

## Commit Messages

- Use clear, descriptive commit messages
- Reference issue numbers if applicable
- Follow conventional commit format when possible

## Questions?

Open an issue on GitHub for questions or discussions.

Thank you for contributing!
