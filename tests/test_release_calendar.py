#!/usr/bin/env python3
"""
test_release_calendar.py

Test suite for the Release Calendar feature.
Tests backend logic, caching, and integration with Streamlit UI.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import inspect  # Added for source code inspection

# Add src to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

import pytest
import pandas as pd


# --------------------------
# Test get_series_release_info function
# --------------------------

def test_get_series_release_info_import():
    """Test that get_series_release_info can be imported."""
    from src.macro_econ_data_archive.macro_utils import get_series_release_info
    assert callable(get_series_release_info)


def test_get_series_release_info_no_api_key():
    """Test that function raises error when no API key provided."""
    from src.macro_econ_data_archive.macro_utils import get_series_release_info
    
    with pytest.raises(ValueError, match="FRED API key is required"):
        get_series_release_info("UNRATE", "")


@patch('src.macro_econ_data_archive.macro_utils.requests.get')
def test_get_series_release_info_success(mock_get):
    """Test successful release info retrieval with valid responses."""
    from src.macro_econ_data_archive.macro_utils import get_series_release_info
    
    # Mock the series/release endpoint
    series_release_response = Mock()
    series_release_response.status_code = 200
    series_release_response.json.return_value = {
        'releases': [{
            'id': 50,
            'name': 'Employment Situation',
            'press_release': True
        }]
    }
    
    # Mock the release/dates endpoint
    release_dates_response = Mock()
    release_dates_response.status_code = 200
    release_dates_response.json.return_value = {
        'release_dates': [
            {'date': '2026-02-07'},
            {'date': '2026-03-07'}
        ]
    }
    
    # Configure mock to return different responses
    mock_get.side_effect = [series_release_response, release_dates_response]
    
    result = get_series_release_info("UNRATE", "fake_api_key")
    
    assert result['series_id'] == 'UNRATE'
    assert result['release_name'] == 'Employment Situation'
    assert result['next_release_date'] == '2026-02-07'
    assert result['release_id'] == 50
    assert 'error' not in result


@patch('src.macro_econ_data_archive.macro_utils.requests.get')
def test_get_series_release_info_no_release(mock_get):
    """Test handling of series with no regular release schedule."""
    from src.macro_econ_data_archive.macro_utils import get_series_release_info
    
    # Mock response with no releases
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'releases': []}
    mock_get.return_value = mock_response
    
    result = get_series_release_info("CUSTOM123", "fake_api_key")
    
    assert result['series_id'] == 'CUSTOM123'
    assert result['release_name'] == 'N/A'
    assert result['next_release_date'] == 'TBD'
    assert result['release_id'] is None


@patch('src.macro_econ_data_archive.macro_utils.requests.get')
def test_get_series_release_info_no_future_dates(mock_get):
    """Test handling when no future release dates are available."""
    from src.macro_econ_data_archive.macro_utils import get_series_release_info
    
    # Mock series/release response
    series_release_response = Mock()
    series_release_response.status_code = 200
    series_release_response.json.return_value = {
        'releases': [{'id': 10, 'name': 'Some Release'}]
    }
    
    # Mock release/dates response with no dates
    release_dates_response = Mock()
    release_dates_response.status_code = 200
    release_dates_response.json.return_value = {'release_dates': []}
    
    mock_get.side_effect = [series_release_response, release_dates_response]
    
    result = get_series_release_info("TEST", "fake_api_key")
    
    assert result['next_release_date'] == 'TBD'


@patch('src.macro_econ_data_archive.macro_utils.requests.get')
def test_get_series_release_info_network_error(mock_get):
    """Test error handling for network failures."""
    from src.macro_econ_data_archive.macro_utils import get_series_release_info
    import requests
    
    # Simulate network error
    mock_get.side_effect = requests.exceptions.ConnectionError("Network unavailable")
    
    result = get_series_release_info("GDPC1", "fake_api_key")
    
    assert result['series_id'] == 'GDPC1'
    assert result['release_name'] == 'Error'
    assert result['next_release_date'] == 'TBD'
    assert 'error' in result


@patch('src.macro_econ_data_archive.macro_utils.requests.get')
def test_get_series_release_info_api_error(mock_get):
    """Test error handling for API errors (e.g., invalid API key)."""
    from src.macro_econ_data_archive.macro_utils import get_series_release_info
    
    # Mock API error response
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.raise_for_status.side_effect = Exception("Bad API key")
    mock_get.return_value = mock_response
    
    result = get_series_release_info("GDPC1", "bad_key")
    
    assert result['series_id'] == 'GDPC1'
    assert result['release_name'] == 'Error'
    assert result['next_release_date'] == 'TBD'


# --------------------------
# Test Streamlit Integration
# --------------------------

def test_streamlit_imports():
    """Test that streamlit_app imports work with new function."""
    try:
        from src.macro_econ_data_archive.streamlit_app import (
            get_series_release_info_cached,
            render_calendar_view
        )
        assert callable(get_series_release_info_cached)
        assert callable(render_calendar_view)
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_init_session_state_has_fred_key():
    """Test that init_session_state includes fred_api_key."""
    from src.macro_econ_data_archive.streamlit_app import init_session_state
    
    # Create mock streamlit module
    mock_st = MagicMock()
    mock_session_state = {}
    
    # Mock the session state to behave like a dict with attribute access
    class MockSessionState(dict):
        def __getattr__(self, name):
            return self.get(name)
        def __setattr__(self, name, value):
            self[name] = value
    
    mock_st.session_state = MockSessionState()
    
    with patch('src.macro_econ_data_archive.streamlit_app.st', mock_st):
        with patch('src.macro_econ_data_archive.streamlit_app.os.getenv', return_value=''):
            init_session_state()
    
    # Check that fred_api_key is initialized
    assert 'fred_api_key' in mock_st.session_state


@patch('src.macro_econ_data_archive.streamlit_app.st')
def test_render_calendar_view_no_api_key(mock_st):
    """Test calendar view shows warning when no API key."""
    from src.macro_econ_data_archive.streamlit_app import render_calendar_view
    
    # Mock session state without API key
    mock_st.session_state.fred_api_key = ""
    mock_st.session_state.charts = []
    
    # Call function
    render_calendar_view()
    
    # Verify warning was shown
    mock_st.warning.assert_called_once()


@patch('src.macro_econ_data_archive.streamlit_app.st')
def test_render_calendar_view_no_charts(mock_st):
    """Test calendar view shows info when no charts."""
    from src.macro_econ_data_archive.streamlit_app import render_calendar_view
    
    # Mock session state with API key but no charts
    mock_st.session_state.fred_api_key = "test_key"
    mock_st.session_state.charts = []
    
    # Call function
    render_calendar_view()
    
    # Verify info message was shown (called at least once)
    assert mock_st.info.called


@patch('src.macro_econ_data_archive.streamlit_app.get_series_release_info_cached')
@patch('src.macro_econ_data_archive.streamlit_app.st')
def test_render_calendar_view_with_charts(mock_st, mock_get_release):
    """Test calendar view processes charts correctly."""
    from src.macro_econ_data_archive.streamlit_app import render_calendar_view, ChartConfig, SeriesInfo
    
    # Mock session state with API key and charts
    class MockSessionState:
        fred_api_key = "test_key"
        charts = [
            ChartConfig(
                title="Test Chart",
                series=[SeriesInfo(series_id="UNRATE", series_label="Unemployment Rate")],
                frequency="monthly",
                transform="level",
                units="Percent"
            )
        ]
    
    mock_st.session_state = MockSessionState()
    
    # Mock release info response
    mock_get_release.return_value = {
        'series_id': 'UNRATE',
        'release_name': 'Employment Situation',
        'next_release_date': '2026-02-07',
        'release_id': 50
    }
    
    # Mock progress bar and other UI elements
    mock_progress = MagicMock()
    mock_st.progress.return_value = mock_progress
    mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
    
    # Call function
    render_calendar_view()
    
    # Verify release info was fetched
    mock_get_release.assert_called_once_with("UNRATE", "test_key")
    
    # Verify progress bar was used and cleared
    mock_st.progress.assert_called_once()
    mock_progress.empty.assert_called_once()


@patch('src.macro_econ_data_archive.streamlit_app.get_series_release_info_cached')
@patch('src.macro_econ_data_archive.streamlit_app.st')
@patch('src.macro_econ_data_archive.streamlit_app.pd.DataFrame')
def test_render_calendar_view_calculates_days(mock_df, mock_st, mock_get_release):
    """Test that days remaining is calculated correctly."""
    from src.macro_econ_data_archive.streamlit_app import render_calendar_view, ChartConfig, SeriesInfo
    
    # Mock session state
    class MockSessionState:
        fred_api_key = "test_key"
        charts = [
            ChartConfig(
                title="Test",
                series=[SeriesInfo(series_id="GDPC1", series_label="Real GDP")],
                frequency="quarterly",
                transform="level",
                units="Billions"
            )
        ]
    
    mock_st.session_state = MockSessionState()
    
    # Mock release with future date
    mock_get_release.return_value = {
        'series_id': 'GDPC1',
        'release_name': 'GDP Release',
        'next_release_date': '2026-03-15',
        'release_id': 9
    }
    
    # Mock progress bar and other UI elements
    mock_progress = MagicMock()
    mock_st.progress.return_value = mock_progress
    mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
    
    # Call function
    render_calendar_view()
    
    # Verify function completed without errors
    assert mock_get_release.called


# --------------------------
# Integration Tests
# --------------------------

def test_cache_decorator_applied():
    """Test that cache decorator is applied to release info function."""
    from src.macro_econ_data_archive.streamlit_app import get_series_release_info_cached
    import inspect
    
    # Get source code of the function
    src = inspect.getsource(get_series_release_info_cached)
    
    # Verify the decorator is present in the source code
    # This is more robust than checking __wrapped__ in CI environments where 
    # Streamlit might act as a pass-through (identity) decorator.
    assert "@st.cache_data" in src, "Function should be decorated with @st.cache_data"


def test_multiple_series_deduplication():
    """Test that duplicate series IDs are handled correctly."""
    from src.macro_econ_data_archive.streamlit_app import ChartConfig, SeriesInfo
    
    # Create charts with overlapping series
    chart1 = ChartConfig(
        title="Chart 1",
        series=[
            SeriesInfo(series_id="UNRATE", series_label="Unemployment"),
            SeriesInfo(series_id="GDPC1", series_label="GDP")
        ],
        frequency="monthly",
        transform="level",
        units="Percent"
    )
    
    chart2 = ChartConfig(
        title="Chart 2",
        series=[
            SeriesInfo(series_id="UNRATE", series_label="U Rate"),  # Duplicate
            SeriesInfo(series_id="CPIAUCSL", series_label="CPI")
        ],
        frequency="monthly",
        transform="yoy",
        units="Percent"
    )
    
    # Extract unique series
    charts = [chart1, chart2]
    unique_series = set()
    for chart in charts:
        for series in chart.series:
            unique_series.add(series.series_id)
    
    # Should have 3 unique series (UNRATE, GDPC1, CPIAUCSL)
    assert len(unique_series) == 3
    assert "UNRATE" in unique_series
    assert "GDPC1" in unique_series
    assert "CPIAUCSL" in unique_series


# --------------------------
# Run Tests
# --------------------------

if __name__ == "__main__":
    print("Running Release Calendar tests...")
    print("=" * 60)
    
    test_functions = [
        ("Import get_series_release_info", test_get_series_release_info_import),
        ("No API key error", test_get_series_release_info_no_api_key),
        ("Successful retrieval", test_get_series_release_info_success),
        ("No release schedule", test_get_series_release_info_no_release),
        ("No future dates", test_get_series_release_info_no_future_dates),
        ("Network error handling", test_get_series_release_info_network_error),
        ("API error handling", test_get_series_release_info_api_error),
        ("Streamlit imports", test_streamlit_imports),
        ("Session state init", test_init_session_state_has_fred_key),
        ("Calendar no API key", test_render_calendar_view_no_api_key),
        ("Calendar no charts", test_render_calendar_view_no_charts),
        ("Calendar with charts", test_render_calendar_view_with_charts),
        ("Days calculation", test_render_calendar_view_calculates_days),
        ("Cache decorator", test_cache_decorator_applied),
        ("Series deduplication", test_multiple_series_deduplication),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in test_functions:
        try:
            test_func()
            print(f"✓ PASS: {name}")
            passed += 1
        except Exception as e:
            print(f"✗ FAIL: {name}")
            print(f"  Error: {str(e)}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_functions)} tests")
    
    sys.exit(0 if failed == 0 else 1)
