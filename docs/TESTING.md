# Testing Guide

## Overview

This guide covers the testing infrastructure for the MacroEconDataArchive project. The test suite ensures reliability, backward compatibility, and correct integration of all features.

## Test Structure

The project uses Python's standard testing approach with dedicated test scripts for different components:

### Test Files

1. **verify_installation.py** - Quick installation verification
2. **test_cli_smoke.py** - CLI functionality tests
3. **test_streamlit_smoke.py** - Streamlit app tests
4. **test_templates.py** - Template system tests
5. **test_caching_and_retry.py** - Data fetching and caching tests

## Running Tests

### Quick Verification

For a rapid installation check:

```bash
python verify_installation.py
```

This validates:
- Python version (3.8+)
- All dependencies installed
- Project structure intact
- Basic functionality working

### Individual Test Suites

Run specific test suites:

```bash
# CLI smoke tests
python test_cli_smoke.py

# Streamlit smoke tests
python test_streamlit_smoke.py

# Template system tests
python test_templates.py

# Caching and retry tests
python test_caching_and_retry.py
```

### Run All Tests

To run all tests sequentially:

```bash
python verify_installation.py
python test_cli_smoke.py
python test_streamlit_smoke.py
python test_templates.py
python test_caching_and_retry.py
```

Expected output: All tests should PASS with status indicators.

## Test Coverage

### 1. Installation Verification (verify_installation.py)

**Purpose**: Ensure the project is correctly installed and ready to use.

**Tests**:
- Python version check (3.8+)
- All 8 dependencies present (pandas, matplotlib, reportlab, streamlit, plotly, openai, kaleido, requests)
- Project structure validation
- Template existence check
- Basic import tests

**Usage**:
```bash
python verify_installation.py
```

**Exit Codes**:
- 0: All checks passed
- 1: One or more checks failed

---

### 2. CLI Smoke Tests (test_cli_smoke.py)

**Purpose**: Validate command-line report generation functionality.

**Tests**:
- Argument parsing
- Template listing
- JSON spec loading
- Data fetching (basic)
- Chart rendering (with mock data)
- PDF generation

**Usage**:
```bash
python test_cli_smoke.py
```

**Coverage**:
- `--list-templates` command
- `--template` argument
- `--spec` argument (legacy)
- Error handling
- Edge cases

---

### 3. Streamlit Smoke Tests (test_streamlit_smoke.py)

**Purpose**: Ensure the Streamlit web application works correctly.

**Tests**:
- Import validation (all dependencies)
- Data class structure (ChartConfig, SeriesInfo)
- Template discovery and loading
- Caching decorator configuration
- Custom exception handling
- Plotly chart creation (single and multi-series)

**Usage**:
```bash
python test_streamlit_smoke.py
```

**Coverage**:
- Session state initialization
- Chart configuration
- Multi-series support
- Template integration
- Caching layer
- Error handling

---

### 4. Template Tests (test_templates.py)

**Purpose**: Validate the template system functionality.

**Tests**:
- Template discovery (CLI and Streamlit)
- Template schema validation
- Template loading by filename and stem
- Content validity (series IDs, structure)
- Specific template verification

**Usage**:
```bash
python test_templates.py
```

**Template Schema Validation**:
- Root keys: `report_title`, `charts`
- Chart keys: `page_title`, `series` (or `series_id` for legacy)
- Series keys: `id`, `label`
- Optional keys: `description`, `frequency`, `transform`, `units`, `notes`

---

### 5. Caching and Retry Tests (test_caching_and_retry.py)

**Purpose**: Validate data fetching, caching, and retry logic.

**Tests**:
- Custom exception creation (FREDRateLimitError, FREDServerError)
- `fetch_fred` function signature
- Retry logic with mocked requests
- Exponential backoff timing
- HTTP timeout configuration
- Streamlit caching decorator

**Usage**:
```bash
python test_caching_and_retry.py
```

**Mock Testing**:
- 403 errors raise FREDRateLimitError immediately (no retries)
- 500 errors retry 3 times with exponential backoff
- Successful fetches after transient errors
- Timeout enforcement (30 seconds)

---

## Continuous Integration (CI)

### GitHub Actions

To set up CI testing:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run verification
      run: python verify_installation.py
    
    - name: Run CLI tests
      run: python test_cli_smoke.py
    
    - name: Run Streamlit tests
      run: python test_streamlit_smoke.py
    
    - name: Run template tests
      run: python test_templates.py
    
    - name: Run caching tests
      run: python test_caching_and_retry.py
```

## Writing New Tests

### Adding a New Test File

Follow this pattern:

```python
#!/usr/bin/env python3
"""
test_new_feature.py

Description of what this test suite covers.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_feature_one():
    """Test feature one."""
    print("Testing feature one...")
    
    try:
        # Test logic here
        assert condition, "Error message"
        print("  ✓ Test passed")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("New Feature Tests")
    print("=" * 70)
    
    tests = [
        ("Feature One", test_feature_one),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<30} {status}")
    
    print("-" * 70)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
```

## Debugging Failed Tests

### Common Issues

1. **Import Errors**
   - Ensure `src/` is in Python path
   - Check dependencies are installed: `pip install -r requirements.txt`

2. **Template Not Found**
   - Verify templates exist in `config/templates/`
   - Check template JSON structure

3. **Network/FRED Errors**
   - Caching tests use mocks (no network required)
   - Actual data fetching requires internet connection

4. **Streamlit Warnings**
   - "missing ScriptRunContext" warnings are expected in test mode
   - These can be safely ignored

### Verbose Output

For detailed debugging, add print statements in test functions or use Python's debugger:

```bash
python -m pdb test_streamlit_smoke.py
```

## Test Maintenance

### When to Update Tests

Update tests when:
- Adding new features
- Modifying existing functionality
- Changing data structures
- Updating dependencies
- Fixing bugs (add regression test)

### Best Practices

1. **Keep tests simple**: Test one thing at a time
2. **Use descriptive names**: Function names should explain what's being tested
3. **Provide clear output**: Use ✓/✗ indicators and descriptive messages
4. **Test edge cases**: Empty data, missing files, network errors
5. **Mock external dependencies**: Use mocks for FRED API calls
6. **Maintain backward compatibility**: Ensure old features still work

## Performance Testing

While not included in the current test suite, consider adding performance tests for:
- Large data downloads
- Multi-chart PDF generation
- Template loading with many charts
- Cache hit/miss ratios

## Security Testing

Verify:
- API keys not hardcoded
- No secrets in templates
- Safe file operations
- Input validation

## Summary

- **5 test suites** covering all major components
- **25+ individual tests** with comprehensive coverage
- **Quick verification** with `verify_installation.py`
- **CI-ready** for automated testing
- **Developer-friendly** output format

For issues or questions, see the main README.md or open an issue on GitHub.
