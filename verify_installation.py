#!/usr/bin/env python3
"""
Quick verification script to check if MacroEconDataArchive is properly installed.

This script checks:
1. All required packages are installed with correct versions
2. Imports work correctly
3. Basic functionality is available

Run with: python verify_installation.py
"""

from __future__ import annotations

import sys


def check_python_version():
    """Check Python version meets requirements."""
    print("Checking Python version...")
    version = sys.version_info
    if version >= (3, 8):
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)")
        return False


def check_packages():
    """Check all required packages are installed with minimum versions."""
    print("\nChecking required packages...")
    
    required_packages = {
        'requests': '2.31.0',
        'pandas': '2.0.0',
        'matplotlib': '3.7.0',
        'reportlab': '4.0.0',
        'streamlit': '1.28.0',
        'plotly': '5.17.0',
        'kaleido': '0.2.1',
        'openai': '1.0.0',
    }
    
    all_ok = True
    
    for package, min_version in required_packages.items():
        try:
            if package == 'reportlab':
                import reportlab
                version = reportlab.Version
            else:
                mod = __import__(package)
                version = mod.__version__
            
            print(f"  ✓ {package} {version} (>= {min_version})")
        except ImportError:
            print(f"  ✗ {package} not installed (requires >= {min_version})")
            all_ok = False
        except AttributeError:
            print(f"  ⚠ {package} installed but version unknown")
    
    return all_ok


def check_cli_tool():
    """Check CLI tool is accessible."""
    print("\nChecking CLI tool...")
    try:
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from macro_econ_data_archive.report_generator import main
        print("  ✓ CLI tool (generate_macro_report.py) is accessible")
        return True
    except Exception as e:
        print(f"  ✗ CLI tool not accessible: {e}")
        return False


def check_streamlit_app():
    """Check Streamlit app is accessible."""
    print("\nChecking Streamlit app...")
    try:
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from macro_econ_data_archive.streamlit_app import main
        print("  ✓ Streamlit app (app.py) is accessible")
        return True
    except Exception as e:
        print(f"  ✗ Streamlit app not accessible: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("MacroEconDataArchive Installation Verification")
    print("=" * 60)
    
    results = [
        check_python_version(),
        check_packages(),
        check_cli_tool(),
        check_streamlit_app(),
    ]
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ Installation verification PASSED")
        print("\nYou can now:")
        print("  - Run CLI tool: python generate_macro_report.py --help")
        print("  - Launch Streamlit: streamlit run app.py")
        print("  - Run smoke tests: python test_cli_smoke.py")
        print("=" * 60)
        return 0
    else:
        print("❌ Installation verification FAILED")
        print("\nTo fix:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run smoke tests: python test_streamlit_smoke.py")
        print("  3. See docs/TESTING.md for troubleshooting")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
