#!/usr/bin/env python3
"""
Smoke test for CLI workflow (generate_macro_report.py).

This test validates that the CLI tool can:
1. Import all required modules
2. Parse command-line arguments
3. Fetch data from FRED
4. Generate charts
5. Assemble a PDF report

Run with: python test_cli_smoke.py
"""

from __future__ import annotations

import sys
import os
import tempfile
from pathlib import Path


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        import pandas
        import matplotlib
        import reportlab
        import requests
        print(f"  ✓ pandas {pandas.__version__}")
        print(f"  ✓ matplotlib {matplotlib.__version__}")
        print(f"  ✓ reportlab {reportlab.Version}")
        print(f"  ✓ requests {requests.__version__}")
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False


def test_cli_help():
    """Test that CLI can show help message."""
    print("\nTesting CLI help command...")
    try:
        # Ensure src is on path
        repo_root = Path(__file__).resolve().parent
        src_dir = repo_root / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        
        from macro_econ_data_archive.report_generator import main
        
        # Save original argv
        original_argv = sys.argv[:]
        
        # Test help
        sys.argv = ["test", "--help"]
        try:
            main()
        except SystemExit as e:
            if e.code == 0:
                print("  ✓ CLI help works")
                return True
            else:
                print(f"  ✗ CLI help exited with code {e.code}")
                return False
        finally:
            sys.argv = original_argv
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_fred_fetch():
    """Test that we can fetch data from FRED."""
    print("\nTesting FRED data fetch...")
    try:
        repo_root = Path(__file__).resolve().parent
        src_dir = repo_root / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        
        from macro_econ_data_archive.macro_utils import fetch_fred
        
        # Try to fetch a simple series
        df = fetch_fred(["CPIAUCSL"], start="2023-01-01")
        if df is not None and not df.empty:
            print(f"  ✓ Fetched CPIAUCSL: {len(df)} data points")
            return True
        else:
            print("  ✗ Fetch returned empty data")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_minimal_report_generation():
    """Test minimal report generation."""
    print("\nTesting minimal report generation...")
    try:
        repo_root = Path(__file__).resolve().parent
        src_dir = repo_root / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        
        from macro_econ_data_archive.report_generator import main
        import json
        
        # Create a minimal chart spec
        minimal_spec = {
            "charts": [
                {
                    "page_title": "Smoke Test Chart",
                    "series": [{"id": "CPIAUCSL", "label": "CPI-U"}],
                    "transform": "level",
                    "frequency": "monthly",
                    "units": "Index",
                    "notes": "Test chart"
                }
            ]
        }
        
        # Create temp files
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_file = Path(tmpdir) / "test_spec.json"
            out_file = Path(tmpdir) / "test_report.pdf"
            chart_dir = Path(tmpdir) / "charts"
            
            # Write spec
            with open(spec_file, 'w') as f:
                json.dump(minimal_spec, f)
            
            # Save original argv
            original_argv = sys.argv[:]
            
            # Run CLI
            sys.argv = [
                "test",
                "--spec", str(spec_file),
                "--out", str(out_file),
                "--tmpdir", str(chart_dir),
                "--start", "2023-01-01"
            ]
            
            try:
                exit_code = main()
                if exit_code == 0 and out_file.exists():
                    print(f"  ✓ Generated report: {out_file.stat().st_size} bytes")
                    return True
                else:
                    print(f"  ✗ Report generation failed (exit code: {exit_code})")
                    return False
            finally:
                sys.argv = original_argv
                
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("CLI Smoke Test Suite")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("CLI Help", test_cli_help),
        ("FRED Fetch", test_fred_fetch),
        ("Report Generation", test_minimal_report_generation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n{name} crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
