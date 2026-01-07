#!/usr/bin/env python3
"""
test_save_load_config.py - Tests for save/load configuration functionality
"""

import json
import sys
from pathlib import Path
from dataclasses import asdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock streamlit before importing
class MockStreamlit:
    """Mock Streamlit for testing."""
    class session_state:
        report_title = "Test Report"
        start_date = "2020-01-01"
        charts = []

    @staticmethod
    def cache_data(**kwargs):
        def decorator(func):
            return func
        return decorator

    @staticmethod
    def set_page_config(**kwargs):
        pass

sys.modules['streamlit'] = MockStreamlit()

from src.macro_econ_data_archive.streamlit_app import (
    ChartConfig, SeriesInfo, save_current_configuration
)

def test_save_empty_configuration():
    """Test saving an empty configuration."""
    print("Test 1: Save Empty Configuration")

    # Setup
    MockStreamlit.session_state.charts = []
    MockStreamlit.session_state.report_title = "Empty Report"

    # Execute
    config_json = save_current_configuration()
    config = json.loads(config_json)

    # Verify
    assert config['report_title'] == "Empty Report"
    assert config['charts'] == []
    assert isinstance(config_json, str)

    print("  ✓ Empty configuration saved correctly")
    print(f"  ✓ JSON structure valid")
    print()


def test_save_single_chart_configuration():
    """Test saving a configuration with a single chart."""
    print("Test 2: Save Single Chart Configuration")

    # Setup
    series = [SeriesInfo(series_id="GDPC1", series_label="Real GDP")]
    chart = ChartConfig(
        title="Real GDP Growth",
        series=series,
        frequency="quarterly",
        transform="qoq_saar",
        units="Percent",
        data=None,
        narrative="Test narrative about GDP growth."
    )

    MockStreamlit.session_state.charts = [chart]
    MockStreamlit.session_state.report_title = "GDP Report"

    # Execute
    config_json = save_current_configuration()
    config = json.loads(config_json)

    # Verify
    assert config['report_title'] == "GDP Report"
    assert len(config['charts']) == 1

    chart_data = config['charts'][0]
    assert chart_data['page_title'] == "Real GDP Growth"
    assert len(chart_data['series']) == 1
    assert chart_data['series'][0]['id'] == "GDPC1"
    assert chart_data['series'][0]['label'] == "Real GDP"
    assert chart_data['frequency'] == "quarterly"
    assert chart_data['transform'] == "qoq_saar"
    assert chart_data['units'] == "Percent"
    assert chart_data['notes'] == "Test narrative about GDP growth."

    print("  ✓ Single chart saved correctly")
    print(f"  ✓ Chart title: {chart_data['page_title']}")
    print(f"  ✓ Series: {chart_data['series']}")
    print(f"  ✓ Narrative saved as notes")
    print()


def test_save_multi_series_chart():
    """Test saving a chart with multiple series."""
    print("Test 3: Save Multi-Series Chart Configuration")

    # Setup
    series = [
        SeriesInfo(series_id="GDPC1", series_label="Real GDP"),
        SeriesInfo(series_id="PCEC96", series_label="Real PCE"),
        SeriesInfo(series_id="UNRATE", series_label="Unemployment Rate")
    ]
    chart = ChartConfig(
        title="Multiple Economic Indicators",
        series=series,
        frequency="monthly",
        transform="yoy",
        units="Percent",
        data=None,
        narrative="Multi-series analysis."
    )

    MockStreamlit.session_state.charts = [chart]
    MockStreamlit.session_state.report_title = "Multi-Series Report"

    # Execute
    config_json = save_current_configuration()
    config = json.loads(config_json)

    # Verify
    chart_data = config['charts'][0]
    assert len(chart_data['series']) == 3
    assert chart_data['series'][0]['id'] == "GDPC1"
    assert chart_data['series'][1]['id'] == "PCEC96"
    assert chart_data['series'][2]['id'] == "UNRATE"

    print("  ✓ Multi-series chart saved correctly")
    print(f"  ✓ Number of series: {len(chart_data['series'])}")
    for s in chart_data['series']:
        print(f"    - {s['label']} ({s['id']})")
    print()


def test_save_multiple_charts():
    """Test saving a configuration with multiple charts."""
    print("Test 4: Save Multiple Charts Configuration")

    # Setup
    charts = [
        ChartConfig(
            title="Chart 1",
            series=[SeriesInfo(series_id="GDPC1", series_label="Real GDP")],
            frequency="quarterly",
            transform="qoq_saar",
            units="Percent",
            data=None,
            narrative="First chart narrative."
        ),
        ChartConfig(
            title="Chart 2",
            series=[SeriesInfo(series_id="CPIAUCSL", series_label="CPI")],
            frequency="monthly",
            transform="yoy",
            units="Percent",
            data=None,
            narrative="Second chart narrative."
        ),
        ChartConfig(
            title="Chart 3",
            series=[SeriesInfo(series_id="UNRATE", series_label="Unemployment")],
            frequency="monthly",
            transform="level",
            units="Percent",
            data=None,
            narrative=""
        )
    ]

    MockStreamlit.session_state.charts = charts
    MockStreamlit.session_state.report_title = "Comprehensive Report"

    # Execute
    config_json = save_current_configuration()
    config = json.loads(config_json)

    # Verify
    assert len(config['charts']) == 3
    assert config['charts'][0]['page_title'] == "Chart 1"
    assert config['charts'][1]['page_title'] == "Chart 2"
    assert config['charts'][2]['page_title'] == "Chart 3"
    assert config['charts'][0]['notes'] == "First chart narrative."
    assert config['charts'][1]['notes'] == "Second chart narrative."
    assert config['charts'][2]['notes'] == ""

    print("  ✓ Multiple charts saved correctly")
    print(f"  ✓ Total charts: {len(config['charts'])}")
    print()


def test_json_schema_compatibility():
    """Test that saved JSON matches template schema."""
    print("Test 5: JSON Schema Compatibility with Templates")

    # Setup - create a chart similar to template structure
    series = [SeriesInfo(series_id="GDPC1", series_label="Real GDP")]
    chart = ChartConfig(
        title="Real GDP Growth (Quarter over Quarter, Annualized)",
        series=series,
        frequency="quarterly",
        transform="qoq_saar",
        units="Percent",
        data=None,
        narrative="Real Gross Domestic Product, seasonally adjusted annual rate"
    )

    MockStreamlit.session_state.charts = [chart]
    MockStreamlit.session_state.report_title = "Core Macroeconomic Indicators Report"

    # Execute
    config_json = save_current_configuration()
    config = json.loads(config_json)

    # Verify schema matches template format
    assert 'report_title' in config
    assert 'charts' in config
    assert isinstance(config['charts'], list)

    chart_data = config['charts'][0]
    required_fields = ['page_title', 'series', 'frequency', 'transform', 'units', 'notes']
    for field in required_fields:
        assert field in chart_data, f"Missing required field: {field}"

    # Verify series structure
    assert isinstance(chart_data['series'], list)
    assert len(chart_data['series']) > 0
    series_data = chart_data['series'][0]
    assert 'id' in series_data
    assert 'label' in series_data

    print("  ✓ JSON schema matches template format")
    print(f"  ✓ All required fields present: {', '.join(required_fields)}")
    print(f"  ✓ Series structure correct: id, label")
    print()


def test_json_pretty_formatting():
    """Test that JSON is properly formatted for readability."""
    print("Test 6: JSON Pretty Formatting")

    # Setup
    series = [SeriesInfo(series_id="GDPC1", series_label="Real GDP")]
    chart = ChartConfig(
        title="Test Chart",
        series=series,
        frequency="quarterly",
        transform="level",
        units="Billions",
        data=None,
        narrative="Test"
    )

    MockStreamlit.session_state.charts = [chart]
    MockStreamlit.session_state.report_title = "Test Report"

    # Execute
    config_json = save_current_configuration()

    # Verify formatting
    assert config_json.count('\n') > 10  # Should have line breaks
    assert '  ' in config_json  # Should have indentation

    # Verify it's valid JSON
    json.loads(config_json)

    print("  ✓ JSON is pretty-formatted with indentation")
    print(f"  ✓ Total lines: {config_json.count(chr(10)) + 1}")
    print()


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("TESTING: Save/Load Configuration Functionality")
    print("=" * 70)
    print()

    tests = [
        test_save_empty_configuration,
        test_save_single_chart_configuration,
        test_save_multi_series_chart,
        test_save_multiple_charts,
        test_json_schema_compatibility,
        test_json_pretty_formatting
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"  ✗ FAILED: {e}")
            print()
        except Exception as e:
            failed += 1
            print(f"  ✗ ERROR: {e}")
            print()

    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
