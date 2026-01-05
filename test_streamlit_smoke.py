#!/usr/bin/env python3
"""
Smoke test for Streamlit app (app.py).

This test validates that the Streamlit app can:
1. Import all required modules (streamlit, plotly, openai)
2. Initialize without errors
3. Load the main app components

Run with: python test_streamlit_smoke.py

Note: This does not launch the actual Streamlit server - that would require
      running: streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        import pandas
        import matplotlib
        import reportlab
        import requests
        import streamlit
        import plotly
        import openai
        
        print(f"  ✓ pandas {pandas.__version__}")
        print(f"  ✓ matplotlib {matplotlib.__version__}")
        print(f"  ✓ reportlab {reportlab.Version}")
        print(f"  ✓ requests {requests.__version__}")
        print(f"  ✓ streamlit {streamlit.__version__}")
        print(f"  ✓ plotly {plotly.__version__}")
        print(f"  ✓ openai {openai.__version__}")
        
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False


def test_kaleido():
    """Test that kaleido is available for PDF export."""
    print("\nTesting kaleido (for Plotly PDF export)...")
    try:
        import kaleido
        print(f"  ✓ kaleido available")
        return True
    except ImportError:
        print("  ⚠ kaleido not installed (PDF export may not work)")
        return False


def test_app_module():
    """Test that the app module can be imported."""
    print("\nTesting app module import...")
    try:
        # Ensure src is on path
        repo_root = Path(__file__).resolve().parent
        src_dir = repo_root / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        
        from macro_econ_data_archive import streamlit_app
        print("  ✓ streamlit_app module imported")
        return True
    except Exception as e:
        print(f"  ✗ Error importing app: {e}")
        return False


def test_utility_functions():
    """Test that utility functions work."""
    print("\nTesting utility functions...")
    try:
        repo_root = Path(__file__).resolve().parent
        src_dir = repo_root / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        
        from macro_econ_data_archive.macro_utils import (
            fetch_fred,
            yoy,
            qoq_saar,
            safe_to_numeric,
        )
        
        # Test FRED fetch (may fail due to network restrictions)
        try:
            df = fetch_fred("CPIAUCSL", start="2023-01-01")
            if df is not None and not df.empty:
                print(f"  ✓ fetch_fred works: {len(df)} data points")
            else:
                print("  ⚠ fetch_fred returned empty data (network issue)")
        except Exception as e:
            print(f"  ⚠ fetch_fred skipped (network unavailable)")
        
        # Test transformations (these should always work)
        import pandas as pd
        test_series = pd.Series([100, 102, 104, 106, 108])
        
        yoy_result = yoy(test_series, periods=4)
        print(f"  ✓ yoy transform works: {len(yoy_result)} values")
        
        qoq_result = qoq_saar(test_series)
        print(f"  ✓ qoq_saar transform works: {len(qoq_result)} values")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chart_config():
    """Test that ChartConfig dataclass works."""
    print("\nTesting ChartConfig...")
    try:
        repo_root = Path(__file__).resolve().parent
        src_dir = repo_root / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        
        from macro_econ_data_archive.streamlit_app import ChartConfig
        
        config = ChartConfig(
            title="Test Chart",
            series_id="CPIAUCSL",
            series_label="CPI-U",
            transform="yoy",
            frequency="monthly",
            units="Percent"
        )
        
        print(f"  ✓ ChartConfig created: {config.title}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_openai_client():
    """Test that OpenAI client can be instantiated."""
    print("\nTesting OpenAI client (without API key)...")
    try:
        from openai import OpenAI
        
        # Check if API key is set
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("  ⚠ OPENAI_API_KEY not set (AI features will not work)")
            print("    Set with: export OPENAI_API_KEY='your-key-here'")
            return False
        else:
            # Try to create client
            client = OpenAI(api_key=api_key)
            print("  ✓ OpenAI client initialized")
            return True
            
    except Exception as e:
        print(f"  ⚠ OpenAI client error: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("Streamlit App Smoke Test Suite")
    print("=" * 60)
    
    tests = [
        ("Core Imports", test_imports, True),
        ("Kaleido (optional)", test_kaleido, False),
        ("App Module", test_app_module, True),
        ("Utility Functions", test_utility_functions, True),
        ("ChartConfig", test_chart_config, True),
        ("OpenAI Client", test_openai_client, False),
    ]
    
    results = []
    for name, test_func, required in tests:
        try:
            result = test_func()
            results.append((name, result, required))
        except Exception as e:
            print(f"\n{name} crashed: {e}")
            results.append((name, False, required))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    passed = sum(1 for _, result, _ in results if result)
    required_passed = sum(1 for _, result, required in results if result and required)
    required_total = sum(1 for _, _, required in results if required)
    total = len(results)
    
    for name, result, required in results:
        if result:
            status = "✓ PASS"
        elif not required:
            status = "⚠ SKIP"
        else:
            status = "✗ FAIL"
        req_marker = " [required]" if required else " [optional]"
        print(f"{status}: {name}{req_marker}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Required: {required_passed}/{required_total} tests passed")
    print("=" * 60)
    
    if required_passed == required_total:
        print("\n✓ All required tests passed! Streamlit app should work.")
        print("  Run with: streamlit run app.py")
        return 0
    else:
        print("\n✗ Some required tests failed. Install missing dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
