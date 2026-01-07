#!/usr/bin/env python3
"""
verify_installation.py

Quick installation verification script.
Checks that all dependencies are installed and basic functionality works.
"""

import sys
from pathlib import Path


def check_python_version():
    """Verify Python version is 3.8+."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor} (need 3.8+)")
        return False


def check_dependencies():
    """Check that all required packages are installed."""
    print("\nChecking dependencies...")

    required = {
        'pandas': 'pandas',
        'matplotlib': 'matplotlib',
        'reportlab': 'reportlab',
        'streamlit': 'streamlit',
        'plotly': 'plotly',
        'openai': 'openai',
        'kaleido': 'kaleido',
        'requests': 'requests'
    }

    results = {}
    for package, import_name in required.items():
        try:
            mod = __import__(import_name)
            version = getattr(mod, '__version__', 'unknown')
            print(f"  ✓ {package:<12} {version}")
            results[package] = True
        except ImportError:
            print(f"  ✗ {package:<12} NOT INSTALLED")
            results[package] = False

    return all(results.values())


def check_project_structure():
    """Verify project structure is intact."""
    print("\nChecking project structure...")

    required_paths = [
        "src/macro_econ_data_archive/__init__.py",
        "src/macro_econ_data_archive/macro_utils.py",
        "src/macro_econ_data_archive/report_generator.py",
        "src/macro_econ_data_archive/streamlit_app.py",
        "config/templates",
        "config/macro_chart_spec.json",
        "requirements.txt",
        "README.md",
        "generate_macro_report.py",
        "app.py"
    ]

    all_exist = True
    for path_str in required_paths:
        path = Path(path_str)
        if path.exists():
            print(f"  ✓ {path_str}")
        else:
            print(f"  ✗ {path_str} MISSING")
            all_exist = False

    return all_exist


def check_templates():
    """Check that templates exist."""
    print("\nChecking templates...")

    templates_dir = Path("config/templates")
    if not templates_dir.exists():
        print(f"  ✗ Templates directory not found")
        return False

    templates = list(templates_dir.glob("*.json"))
    if not templates:
        print(f"  ⚠ No templates found (not critical)")
        return True

    print(f"  ✓ Found {len(templates)} template(s):")
    for t in templates:
        print(f"    - {t.name}")

    return True


def run_cli_smoke_test():
    """Run a quick CLI smoke test."""
    print("\nRunning CLI smoke test...")

    try:
        # Test import (go up from tests/ to repo root)
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from macro_econ_data_archive.report_generator import discover_templates

        # Test template discovery
        templates = discover_templates()
        print(f"  ✓ CLI functions work")
        print(f"    Discovered {len(templates)} template(s)")

        return True
    except Exception as e:
        print(f"  ✗ CLI smoke test failed: {e}")
        return False


def run_streamlit_import_test():
    """Test that Streamlit app can be imported."""
    print("\nTesting Streamlit app import...")

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from macro_econ_data_archive import streamlit_app

        # Check key functions exist
        assert hasattr(streamlit_app, 'main')
        assert hasattr(streamlit_app, 'ChartConfig')
        assert hasattr(streamlit_app, 'SeriesInfo')
        assert hasattr(streamlit_app, 'fetch_fred_cached')

        print(f"  ✓ Streamlit app imports successfully")
        print(f"  ✓ Key components present")

        return True
    except Exception as e:
        print(f"  ✗ Streamlit import test failed: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("MacroEconDataArchive Installation Verification")
    print("=" * 70)

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Templates", check_templates),
        ("CLI Smoke Test", run_cli_smoke_test),
        ("Streamlit Import", run_streamlit_import_test)
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            results.append((name, False))

    # Print summary
    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{check_name:<25} {status}")

    print("-" * 70)
    print(f"Total: {passed}/{total} checks passed")

    if passed == total:
        print("\n✅ Installation verified successfully!")
        print("\nNext steps:")
        print("  1. Try CLI: python generate_macro_report.py --list-templates")
        print("  2. Try Streamlit: streamlit run app.py")
        print("  3. Run full tests: python test_cli_smoke.py")
    else:
        print("\n❌ Installation incomplete. Please fix the issues above.")

    print("=" * 70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
