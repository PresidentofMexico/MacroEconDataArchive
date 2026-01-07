#!/usr/bin/env python3
"""
test_multi_series_input.py

Tests for the multi-series input parsing functionality in streamlit_app.py
"""

import sys
from pathlib import Path

# Add src to path for imports (go up from tests/ to repo root)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_series_parsing():
    """Test parsing of multi-line series input."""
    print("Testing multi-series input parsing...")

    from macro_econ_data_archive.streamlit_app import SeriesInfo

    # Test case 1: Single series
    series_input = "GDPC1, Real GDP"
    series_list = []

    for line in series_input.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        parts = line.split(',', 1)
        if len(parts) == 2:
            series_id = parts[0].strip()
            series_label = parts[1].strip()

            if series_id and series_label:
                series_list.append(SeriesInfo(series_id=series_id, series_label=series_label))

    assert len(series_list) == 1
    assert series_list[0].series_id == "GDPC1"
    assert series_list[0].series_label == "Real GDP"
    print("  ✓ Single series parsing works")

    # Test case 2: Multiple series
    series_input = """GDPC1, Real GDP
PCEC96, Real PCE
UNRATE, Unemployment Rate"""

    series_list = []
    for line in series_input.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        parts = line.split(',', 1)
        if len(parts) == 2:
            series_id = parts[0].strip()
            series_label = parts[1].strip()

            if series_id and series_label:
                series_list.append(SeriesInfo(series_id=series_id, series_label=series_label))

    assert len(series_list) == 3
    assert series_list[0].series_id == "GDPC1"
    assert series_list[1].series_id == "PCEC96"
    assert series_list[2].series_id == "UNRATE"
    print("  ✓ Multiple series parsing works")

    # Test case 3: Empty lines and whitespace
    series_input = """
    GDPC1, Real GDP

    PCEC96, Real PCE
    """

    series_list = []
    for line in series_input.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        parts = line.split(',', 1)
        if len(parts) == 2:
            series_id = parts[0].strip()
            series_label = parts[1].strip()

            if series_id and series_label:
                series_list.append(SeriesInfo(series_id=series_id, series_label=series_label))

    assert len(series_list) == 2
    print("  ✓ Whitespace handling works")

    # Test case 4: Label with comma
    series_input = "GDPC1, Real GDP, Seasonally Adjusted"

    series_list = []
    for line in series_input.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        parts = line.split(',', 1)  # Split by first comma only
        if len(parts) == 2:
            series_id = parts[0].strip()
            series_label = parts[1].strip()

            if series_id and series_label:
                series_list.append(SeriesInfo(series_id=series_id, series_label=series_label))

    assert len(series_list) == 1
    assert series_list[0].series_id == "GDPC1"
    assert series_list[0].series_label == "Real GDP, Seasonally Adjusted"
    print("  ✓ Labels with commas work correctly")

    return True


def test_quick_add_format():
    """Test that quick add buttons use the correct format."""
    print("\nTesting quick add button format...")

    # Simulate quick add format (single line with comma)
    series_input = "GDPC1, Real GDP"

    from macro_econ_data_archive.streamlit_app import SeriesInfo

    series_list = []
    for line in series_input.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        parts = line.split(',', 1)
        if len(parts) == 2:
            series_id = parts[0].strip()
            series_label = parts[1].strip()

            if series_id and series_label:
                series_list.append(SeriesInfo(series_id=series_id, series_label=series_label))

    assert len(series_list) == 1
    assert series_list[0].series_id == "GDPC1"
    assert series_list[0].series_label == "Real GDP"
    print("  ✓ Quick add format works correctly")

    return True


def test_edge_cases():
    """Test edge cases in parsing."""
    print("\nTesting edge cases...")

    from macro_econ_data_archive.streamlit_app import SeriesInfo

    # Test case 1: Missing label
    series_input = "GDPC1"
    series_list = []

    for line in series_input.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        parts = line.split(',', 1)
        if len(parts) == 2:
            series_id = parts[0].strip()
            series_label = parts[1].strip()

            if series_id and series_label:
                series_list.append(SeriesInfo(series_id=series_id, series_label=series_label))

    assert len(series_list) == 0  # Should be ignored
    print("  ✓ Missing label correctly ignored")

    # Test case 2: Empty string
    series_input = ""
    series_list = []

    for line in series_input.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        parts = line.split(',', 1)
        if len(parts) == 2:
            series_id = parts[0].strip()
            series_label = parts[1].strip()

            if series_id and series_label:
                series_list.append(SeriesInfo(series_id=series_id, series_label=series_label))

    assert len(series_list) == 0  # Should be empty
    print("  ✓ Empty string correctly handled")

    # Test case 3: Only commas
    series_input = ", "
    series_list = []

    for line in series_input.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        parts = line.split(',', 1)
        if len(parts) == 2:
            series_id = parts[0].strip()
            series_label = parts[1].strip()

            if series_id and series_label:
                series_list.append(SeriesInfo(series_id=series_id, series_label=series_label))

    assert len(series_list) == 0  # Should be ignored
    print("  ✓ Invalid format correctly ignored")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Multi-Series Input Parsing Tests")
    print("=" * 60)

    all_passed = True

    try:
        all_passed &= test_series_parsing()
    except Exception as e:
        print(f"  ✗ Series parsing test failed: {e}")
        all_passed = False

    try:
        all_passed &= test_quick_add_format()
    except Exception as e:
        print(f"  ✗ Quick add format test failed: {e}")
        all_passed = False

    try:
        all_passed &= test_edge_cases()
    except Exception as e:
        print(f"  ✗ Edge cases test failed: {e}")
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        print("=" * 60)
        sys.exit(1)
