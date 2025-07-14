# MadSpark Test Suite

This directory contains the test files for the MadSpark Multi-Agent System.

## Test Structure

- `test_basic_imports.py` - Basic import and module availability tests
- `__init__.py` - Test package initialization

## Running Tests

From the project root:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_basic_imports.py

# Run with verbose output
pytest tests/ -v
```

## Test Philosophy

Tests are designed to run without external API calls by using:
- Mock mode for AI agent testing
- Import-only tests for dependency validation
- CI-safe tests that skip when dependencies unavailable

## Environment Setup

Tests automatically configure the Python path to import from `src/madspark`.
No additional environment setup is required for basic import tests.
