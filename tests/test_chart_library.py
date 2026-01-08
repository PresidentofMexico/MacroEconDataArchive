#!/usr/bin/env python3
"""
test_chart_library.py

Tests for the Chart Library functionality in the MacroBuilder Streamlit app.
Validates that the POPULAR_CHARTS constant is properly structured and contains
all required economic indicators.
"""

import sys
from pathlib import Path

# Add src to path for imports (go up from tests/ to repo root)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        from macro_econ_data_archive.streamlit_app import POPULAR_CHARTS
        print("  ✓ POPULAR_CHARTS imported")
    except ImportError as e:
        print(f"  ✗ Failed to import POPULAR_CHARTS: {e}")
        return False

    return True


def test_popular_charts_structure():
    """Test that POPULAR_CHARTS is properly structured."""
    print("\nTesting POPULAR_CHARTS structure...")

    from macro_econ_data_archive.streamlit_app import POPULAR_CHARTS

    # Check that it's a list
    assert isinstance(POPULAR_CHARTS, list), "POPULAR_CHARTS should be a list"
    print(f"  ✓ POPULAR_CHARTS is a list with {len(POPULAR_CHARTS)} items")

    # Check minimum number of charts (should have 20+)
    assert len(POPULAR_CHARTS) >= 20, f"POPULAR_CHARTS should have at least 20 items, got {len(POPULAR_CHARTS)}"
    print(f"  ✓ Has {len(POPULAR_CHARTS)} charts (requirement: 20+)")

    return True


def test_chart_entry_fields():
    """Test that each chart entry has all required fields."""
    print("\nTesting chart entry fields...")

    from macro_econ_data_archive.streamlit_app import POPULAR_CHARTS

    required_fields = ['label', 'category', 'series_input', 'frequency', 'transform', 'units', 'title']

    for idx, chart in enumerate(POPULAR_CHARTS):
        # Check that it's a dictionary
        assert isinstance(chart, dict), f"Chart {idx} should be a dictionary"

        # Check all required fields exist
        for field in required_fields:
            assert field in chart, f"Chart {idx} missing required field: {field}"
            assert chart[field], f"Chart {idx} has empty value for field: {field}"

    print(f"  ✓ All {len(POPULAR_CHARTS)} charts have required fields: {', '.join(required_fields)}")
    return True


def test_categories_present():
    """Test that all required categories are present."""
    print("\nTesting required categories...")

    from macro_econ_data_archive.streamlit_app import POPULAR_CHARTS

    required_categories = ['Growth', 'Inflation', 'Labor', 'Rates', 'Housing', 'Markets']

    # Collect all unique categories
    categories_found = set(chart['category'] for chart in POPULAR_CHARTS)

    print(f"  Categories found: {sorted(categories_found)}")

    # Check that all required categories are present
    for category in required_categories:
        assert category in categories_found, f"Missing required category: {category}"

    print(f"  ✓ All required categories present: {', '.join(required_categories)}")
    return True


def test_specific_indicators():
    """Test that specific required indicators are present."""
    print("\nTesting specific required indicators...")

    from macro_econ_data_archive.streamlit_app import POPULAR_CHARTS

    # Required series IDs from the problem statement
    required_series = {
        'GDPC1': 'Real GDP',
        'RSXFS': 'Retail Sales',
        'INDPRO': 'Industrial Production',
        'CPIAUCSL': 'CPI',
        'PCEPI': 'PCE',
        'PPIACO': 'PPI',
        'T5YIE': '5Y Breakevens',
        'UNRATE': 'Unemployment Rate',
        'PAYEMS': 'Nonfarm Payrolls',
        'AHETPI': 'Wage Growth',
        'FEDFUNDS': 'Fed Funds',
        'DGS10': '10Y Treasury',
        'DGS2': '2Y Treasury',
        'MORTGAGE30US': 'Mortgage Rates',
        'HOUST': 'Housing Starts',
        'CSUSHPISA': 'Case-Shiller',
        'GOLDAMGBD228NLBM': 'Gold',
        'DCOILWTICO': 'Oil',
        'SP500': 'S&P 500',
        'VIXCLS': 'VIX',
    }

    # Extract all series IDs from the charts
    found_series = set()
    for chart in POPULAR_CHARTS:
        # Extract series ID from series_input (format: "CODE, Label")
        series_input = chart['series_input']
        series_id = series_input.split(',')[0].strip()
        found_series.add(series_id)

    print(f"  Found {len(found_series)} unique series IDs")

    # Check each required series
    missing = []
    for series_id, description in required_series.items():
        if series_id not in found_series:
            missing.append(f"{series_id} ({description})")

    if missing:
        print(f"  ✗ Missing required series: {', '.join(missing)}")
        return False

    print(f"  ✓ All {len(required_series)} required series present")
    return True


def test_valid_frequencies():
    """Test that all charts use valid frequency values."""
    print("\nTesting frequency values...")

    from macro_econ_data_archive.streamlit_app import POPULAR_CHARTS

    valid_frequencies = ['monthly', 'quarterly', 'weekly', 'daily']

    for idx, chart in enumerate(POPULAR_CHARTS):
        frequency = chart['frequency']
        assert frequency in valid_frequencies, \
            f"Chart {idx} ({chart['label']}) has invalid frequency: {frequency}"

    print(f"  ✓ All charts use valid frequencies: {', '.join(valid_frequencies)}")
    return True


def test_valid_transforms():
    """Test that all charts use valid transform values."""
    print("\nTesting transform values...")

    from macro_econ_data_archive.streamlit_app import POPULAR_CHARTS

    valid_transforms = ['level', 'yoy', 'qoq_saar']

    for idx, chart in enumerate(POPULAR_CHARTS):
        transform = chart['transform']
        assert transform in valid_transforms, \
            f"Chart {idx} ({chart['label']}) has invalid transform: {transform}"

    print(f"  ✓ All charts use valid transforms: {', '.join(valid_transforms)}")
    return True


def test_series_input_format():
    """Test that series_input follows the expected format."""
    print("\nTesting series_input format...")

    from macro_econ_data_archive.streamlit_app import POPULAR_CHARTS

    for idx, chart in enumerate(POPULAR_CHARTS):
        series_input = chart['series_input']

        # Check format: "CODE, Label"
        assert ',' in series_input, \
            f"Chart {idx} ({chart['label']}) series_input missing comma: {series_input}"

        parts = series_input.split(',', 1)
        assert len(parts) == 2, \
            f"Chart {idx} ({chart['label']}) series_input should have format 'CODE, Label': {series_input}"

        series_id = parts[0].strip()
        series_label = parts[1].strip()

        assert series_id, f"Chart {idx} ({chart['label']}) has empty series ID"
        assert series_label, f"Chart {idx} ({chart['label']}) has empty series label"

    print(f"  ✓ All {len(POPULAR_CHARTS)} charts have properly formatted series_input")
    return True


def test_category_distribution():
    """Test that indicators are distributed across categories."""
    print("\nTesting category distribution...")

    from macro_econ_data_archive.streamlit_app import POPULAR_CHARTS

    category_counts = {}
    for chart in POPULAR_CHARTS:
        category = chart['category']
        category_counts[category] = category_counts.get(category, 0) + 1

    print("  Category distribution:")
    for category, count in sorted(category_counts.items()):
        print(f"    {category}: {count} charts")

    # Each category should have at least 1 chart
    for category, count in category_counts.items():
        assert count > 0, f"Category {category} should have at least one chart"

    print("  ✓ All categories have at least one chart")
    return True


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_imports,
        test_popular_charts_structure,
        test_chart_entry_fields,
        test_categories_present,
        test_specific_indicators,
        test_valid_frequencies,
        test_valid_transforms,
        test_series_input_format,
        test_category_distribution,
    ]

    print("=" * 60)
    print("Running Chart Library Tests")
    print("=" * 60)

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            results.append(False)
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
