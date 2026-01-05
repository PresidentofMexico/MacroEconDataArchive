# Testing and Smoke Tests

This document describes the testing infrastructure for the MacroEconDataArchive toolkit.

## Overview

The repository includes automated smoke tests to verify that both the CLI tool and Streamlit app can be installed and run successfully. These tests are designed to be run on a fresh installation to ensure "push-button" installability.

## Smoke Tests

### CLI Smoke Test (`test_cli_smoke.py`)

Tests the command-line interface tool (`generate_macro_report.py`).

**What it tests:**
- All required packages can be imported (pandas, matplotlib, reportlab, requests)
- CLI help command works
- FRED data fetching works (if network available)
- Report generation pipeline works (if network available)

**How to run:**
```bash
python test_cli_smoke.py
```

**Expected output:**
```
============================================================
CLI Smoke Test Suite
============================================================
Testing imports...
  ✓ pandas 2.3.3
  ✓ matplotlib 3.10.8
  ✓ reportlab 4.4.7
  ✓ requests 2.31.0

Testing CLI help command...
  ✓ CLI help works

Testing FRED data fetch...
  ✓ Fetched CPIAUCSL: 500+ data points

Testing minimal report generation...
  ✓ Generated report: 125432 bytes

============================================================
Test Results:
============================================================
✓ PASS: Import Test
✓ PASS: CLI Help
✓ PASS: FRED Fetch
✓ PASS: Report Generation

Total: 4/4 tests passed
============================================================
```

### Streamlit App Smoke Test (`test_streamlit_smoke.py`)

Tests the Streamlit web application (`app.py`).

**What it tests:**
- All required packages can be imported (streamlit, plotly, openai, plus CLI deps)
- Optional kaleido package is available (for PDF export)
- App module imports successfully
- Utility functions work correctly
- ChartConfig dataclass works
- OpenAI client can be initialized (if API key set)

**How to run:**
```bash
python test_streamlit_smoke.py
```

**Expected output:**
```
============================================================
Streamlit App Smoke Test Suite
============================================================
Testing imports...
  ✓ pandas 2.3.3
  ✓ matplotlib 3.10.8
  ✓ reportlab 4.4.7
  ✓ requests 2.31.0
  ✓ streamlit 1.52.2
  ✓ plotly 6.5.0
  ✓ openai 2.14.0

Testing kaleido (for Plotly PDF export)...
  ✓ kaleido available

Testing app module import...
  ✓ streamlit_app module imported

Testing utility functions...
  ✓ fetch_fred works: 500+ data points
  ✓ yoy transform works: 5 values
  ✓ qoq_saar transform works: 5 values

Testing ChartConfig...
  ✓ ChartConfig created: Test Chart

Testing OpenAI client (without API key)...
  ⚠ OPENAI_API_KEY not set (AI features will not work)
    Set with: export OPENAI_API_KEY='your-key-here'

============================================================
Test Results:
============================================================
✓ PASS: Core Imports [required]
✓ PASS: Kaleido (optional) [optional]
✓ PASS: App Module [required]
✓ PASS: Utility Functions [required]
✓ PASS: ChartConfig [required]
⚠ SKIP: OpenAI Client [optional]

Total: 5/6 tests passed
Required: 4/4 tests passed
============================================================

✓ All required tests passed! Streamlit app should work.
  Run with: streamlit run app.py
```

## Fresh Installation Testing

To test the complete installation process from scratch:

### 1. Create a fresh virtual environment

```bash
python3 -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run smoke tests

```bash
python test_cli_smoke.py
python test_streamlit_smoke.py
```

### 4. Test CLI tool manually

```bash
python generate_macro_report.py --spec config/macro_chart_spec.json --out test_report.pdf --start 2020-01-01
```

### 5. Test Streamlit app manually

```bash
# Set OpenAI API key (optional, for AI features)
export OPENAI_API_KEY='your-api-key-here'

# Launch app
streamlit run app.py
```

Then:
- Add a chart using the sidebar
- Generate AI analysis (if API key is set)
- Export to PDF

## Network Connectivity

Note that the smoke tests and the applications require internet access to:
- Fetch economic data from FRED (fred.stlouisfed.org)
- Generate AI narratives via OpenAI API (api.openai.com)

If running in a restricted environment:
- FRED fetch tests may fail or be skipped
- OpenAI tests will be skipped if no API key is set
- Other tests (imports, transforms, etc.) will still pass

## Troubleshooting

### Import Errors

If you see import errors, ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Kaleido Issues

If PDF export fails with a kaleido error:
```bash
pip install --upgrade kaleido
```

On some systems, you may need:
```bash
pip install kaleido==0.2.1
```

### Network Issues

If FRED data fetching fails:
1. Check internet connectivity
2. Verify fred.stlouisfed.org is accessible
3. Check if there are firewall/proxy restrictions

### OpenAI API Issues

If AI narrative generation fails:
1. Ensure OPENAI_API_KEY is set: `echo $OPENAI_API_KEY`
2. Verify the API key is valid
3. Check API quota/billing status

## CI/CD Integration

These smoke tests can be integrated into CI/CD pipelines:

**GitHub Actions example:**
```yaml
- name: Install dependencies
  run: pip install -r requirements.txt

- name: Run CLI smoke tests
  run: python test_cli_smoke.py

- name: Run Streamlit smoke tests  
  run: python test_streamlit_smoke.py
```

Note: Network-dependent tests may need to be mocked or skipped in CI environments.

## Test Coverage

Current test coverage:
- ✅ Package installation
- ✅ Module imports
- ✅ CLI argument parsing
- ✅ Data transformation functions
- ✅ Data structures (ChartConfig)
- ✅ Streamlit app initialization
- ⚠️ FRED data fetching (network-dependent)
- ⚠️ OpenAI integration (API key required)
- ⚠️ Full end-to-end report generation (network-dependent)

## Future Enhancements

Potential test improvements:
- Unit tests for individual functions
- Integration tests with mocked data sources
- Performance/benchmark tests
- Security/vulnerability scanning
- Automated screenshot testing for UI
- Cross-platform testing (Linux, macOS, Windows)
