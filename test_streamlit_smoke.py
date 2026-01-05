#!/usr/bin/env python3
"""
test_streamlit_smoke.py

Smoke tests for the Streamlit MacroBuilder application.
Validates that the app can start, key components exist, and basic functionality works.
"""

import sys
import os
from pathlib import Path
import importlib
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import streamlit as st
        print("  ✓ streamlit imported")
    except ImportError as e:
        print(f"  ✗ Failed to import streamlit: {e}")
        return False
    
    try:
        import plotly.graph_objects as go
        print("  ✓ plotly imported")
    except ImportError as e:
        print(f"  ✗ Failed to import plotly: {e}")
        return False
    
    try:
        from openai import OpenAI
        print("  ✓ openai imported")
    except ImportError as e:
        print(f"  ✗ Failed to import openai: {e}")
        return False
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            ChartConfig, SeriesInfo, init_session_state,
            fetch_fred_cached, create_plotly_chart
        )
        print("  ✓ streamlit_app components imported")
    except ImportError as e:
        print(f"  ✗ Failed to import streamlit_app: {e}")
        return False
    
    return True


def test_dataclasses():
    """Test that data classes are properly structured."""
    print("\nTesting data classes...")
    
    try:
        from macro_econ_data_archive.streamlit_app import ChartConfig, SeriesInfo
        
        # Test SeriesInfo
        series = SeriesInfo(series_id="GDPC1", series_label="Real GDP")
        assert series.series_id == "GDPC1"
        assert series.series_label == "Real GDP"
        print("  ✓ SeriesInfo works")
        
        # Test ChartConfig with single series
        chart = ChartConfig(
            title="Test Chart",
            series=[series],
            frequency="quarterly",
            transform="qoq_saar",
            units="Percent",
            data=None,
            narrative=""
        )
        assert chart.title == "Test Chart"
        assert len(chart.series) == 1
        assert chart.series_id == "GDPC1"  # Legacy compatibility
        assert chart.series_label == "Real GDP"  # Legacy compatibility
        print("  ✓ ChartConfig works")
        
        # Test ChartConfig with multiple series
        series2 = SeriesInfo(series_id="PCEC96", series_label="Consumer Spending")
        chart_multi = ChartConfig(
            title="Multi Series Chart",
            series=[series, series2],
            frequency="monthly",
            transform="yoy",
            units="Percent"
        )
        assert len(chart_multi.series) == 2
        print("  ✓ Multi-series ChartConfig works")
        
        return True
    except Exception as e:
        print(f"  ✗ Data class test failed: {e}")
        return False


def test_template_discovery():
    """Test template discovery functionality."""
    print("\nTesting template discovery...")
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            get_templates_dir, discover_templates
        )
        
        # Check templates directory exists
        templates_dir = get_templates_dir()
        if not templates_dir.exists():
            print(f"  ✗ Templates directory not found: {templates_dir}")
            return False
        
        print(f"  ✓ Templates directory exists: {templates_dir}")
        
        # Discover templates
        templates = discover_templates()
        if not templates:
            print("  ⚠ No templates found (this is acceptable)")
            return True
        
        print(f"  ✓ Found {len(templates)} template(s):")
        for t in templates:
            print(f"    - {t['filename']}: {t['title']} ({t['chart_count']} charts)")
        
        # Validate template structure
        for t in templates:
            assert 'filename' in t
            assert 'path' in t
            assert 'title' in t
            assert 'description' in t
            assert 'chart_count' in t
        
        print("  ✓ Template structure validated")
        return True
        
    except Exception as e:
        print(f"  ✗ Template discovery test failed: {e}")
        return False


def test_template_loading():
    """Test that templates can be loaded."""
    print("\nTesting template loading...")
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            discover_templates, load_template
        )
        
        templates = discover_templates()
        if not templates:
            print("  ⚠ No templates to test (skipping)")
            return True
        
        # Load first template
        template_path = templates[0]['path']
        template_data = load_template(template_path)
        
        # Validate structure
        assert isinstance(template_data, dict)
        assert 'charts' in template_data
        assert isinstance(template_data['charts'], list)
        
        print(f"  ✓ Loaded template: {templates[0]['filename']}")
        print(f"    Charts: {len(template_data['charts'])}")
        
        # Validate first chart structure
        if template_data['charts']:
            chart = template_data['charts'][0]
            assert 'page_title' in chart
            # Should have either 'series' (multi) or 'series_id' (legacy)
            assert 'series' in chart or 'series_id' in chart
            print(f"  ✓ Chart structure validated")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Template loading test failed: {e}")
        return False


def test_caching_decorator():
    """Test that caching decorator is properly configured."""
    print("\nTesting caching decorator...")
    
    try:
        from macro_econ_data_archive.streamlit_app import fetch_fred_cached
        
        # Check that it's a cached function
        assert hasattr(fetch_fred_cached, 'clear')
        print("  ✓ fetch_fred_cached has cache clear method")
        
        # Check function signature
        import inspect
        sig = inspect.signature(fetch_fred_cached)
        params = list(sig.parameters.keys())
        assert 'series_ids' in params
        assert 'start' in params
        print("  ✓ fetch_fred_cached has correct signature")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Caching test failed: {e}")
        return False


def test_error_handling():
    """Test that custom exceptions are imported."""
    print("\nTesting error handling...")
    
    try:
        from macro_econ_data_archive.macro_utils import (
            FREDRateLimitError, FREDServerError
        )
        
        # Test exception creation
        error1 = FREDRateLimitError("Test rate limit")
        assert str(error1) == "Test rate limit"
        print("  ✓ FREDRateLimitError works")
        
        error2 = FREDServerError("Test server error")
        assert str(error2) == "Test server error"
        print("  ✓ FREDServerError works")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error handling test failed: {e}")
        return False


def test_plotly_chart_creation():
    """Test that Plotly charts can be created."""
    print("\nTesting Plotly chart creation...")
    
    try:
        import pandas as pd
        import plotly.graph_objects as go
        from macro_econ_data_archive.streamlit_app import (
            ChartConfig, SeriesInfo, create_plotly_chart
        )
        
        # Create dummy data
        dates = pd.date_range('2020-01-01', periods=10, freq='M')
        data = pd.DataFrame({
            'GDPC1': range(100, 110),
            'PCEC96': range(80, 90)
        }, index=dates)
        
        # Single series chart
        series1 = SeriesInfo(series_id="GDPC1", series_label="Real GDP")
        chart1 = ChartConfig(
            title="Single Series Test",
            series=[series1],
            frequency="monthly",
            transform="level",
            units="Billions",
            data=data
        )
        
        fig1 = create_plotly_chart(chart1)
        assert isinstance(fig1, go.Figure)
        assert len(fig1.data) == 1  # One trace
        print("  ✓ Single series chart created")
        
        # Multi series chart
        series2 = SeriesInfo(series_id="PCEC96", series_label="Consumer Spending")
        chart2 = ChartConfig(
            title="Multi Series Test",
            series=[series1, series2],
            frequency="monthly",
            transform="level",
            units="Billions",
            data=data
        )
        
        fig2 = create_plotly_chart(chart2)
        assert isinstance(fig2, go.Figure)
        assert len(fig2.data) == 2  # Two traces
        print("  ✓ Multi series chart created")
        
        # Empty data chart
        chart3 = ChartConfig(
            title="Empty Data Test",
            series=[series1],
            frequency="monthly",
            transform="level",
            units="Billions",
            data=None
        )
        
        fig3 = create_plotly_chart(chart3)
        assert isinstance(fig3, go.Figure)
        print("  ✓ Empty data chart handled gracefully")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Chart creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all smoke tests."""
    print("=" * 70)
    print("MacroBuilder Streamlit Smoke Tests")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Import Test", test_imports()))
    results.append(("Data Classes", test_dataclasses()))
    results.append(("Template Discovery", test_template_discovery()))
    results.append(("Template Loading", test_template_loading()))
    results.append(("Caching Decorator", test_caching_decorator()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("Plotly Chart Creation", test_plotly_chart_creation()))
    
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
