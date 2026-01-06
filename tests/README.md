# Test Suite

This directory contains all test files for the MacroEconDataArchive project.

## Test Files

- `test_cli_smoke.py` - CLI smoke tests for report generation
- `test_streamlit_smoke.py` - Streamlit app functionality tests
- `test_templates.py` - Template system tests
- `test_caching_and_retry.py` - Caching and retry logic tests
- `test_breaking_changes.py` - Edge case and breaking change tests
- `verify_installation.py` - Installation verification script

## Running Tests

Since the tests were moved from the root directory, you need to ensure Python can find the source modules. Run tests from the repository root using:

```bash
# Run all tests from repository root
cd /path/to/MacroEconDataArchive
python -m pytest tests/

# Run a specific test file
python tests/test_cli_smoke.py

# Or set PYTHONPATH if running from tests directory
cd tests
PYTHONPATH=.. python test_cli_smoke.py
```

## Test Requirements

All test dependencies are included in `requirements.txt`. Ensure you have installed:

```bash
pip install -r requirements.txt
```

## Test Coverage

The test suite covers:

1. **CLI Functionality** - Verifies command-line report generation works correctly
2. **Streamlit App** - Tests the web interface and interactive features
3. **Template System** - Validates template loading and usage
4. **Caching & Retry** - Ensures data fetching resilience
5. **Breaking Changes** - Guards against regressions from integration changes
6. **Installation** - Verifies all dependencies are properly installed

## Notes

- Tests expect to be run from the repository root directory
- Some tests may require internet access to fetch data from FRED
- Mock data is used where appropriate to avoid external dependencies
- Tests are designed to be fast and focused on specific functionality
