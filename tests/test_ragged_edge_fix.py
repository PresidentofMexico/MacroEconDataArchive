#!/usr/bin/env python3
"""
test_ragged_edge_fix.py

Tests for the ragged edge data problem fix.
Validates that prepare_data_summary correctly handles mixed-frequency data
where quarterly series have NaN values at the end of monthly data.
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports for ragged edge fix...")
    
    try:
        from src.macro_econ_data_archive.streamlit_app import (
            prepare_data_summary,
            generate_narrative,
            ChartConfig,
            SeriesInfo
        )
        print("  ✓ All functions imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import: {e}")
        return False


def test_ragged_edge_monthly_quarterly_mix():
    """Test ragged edge with monthly and quarterly series mixed."""
    print("\nTesting ragged edge: Monthly + Quarterly series...")
    
    try:
        from src.macro_econ_data_archive.streamlit_app import (
            prepare_data_summary,
            SeriesInfo
        )
        
        # Create test data: Monthly data from Jan-Jun 2024
        dates = pd.date_range('2024-01-31', periods=6, freq='M')
        df = pd.DataFrame({
            'UNRATE': [3.7, 3.8, 3.9, 3.8, 3.7, 3.6],  # Monthly unemployment
            'GDPC1': [100.0, None, None, 105.0, None, None]  # Quarterly GDP (Q1, Q2 only)
        }, index=dates)
        
        series_list = [
            SeriesInfo(series_id="UNRATE", series_label="Unemployment Rate"),
            SeriesInfo(series_id="GDPC1", series_label="Real GDP")
        ]
        
        result = prepare_data_summary(df, series_list, periods=6)
        
        # Verify return type is dict
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        print("  ✓ Returns dictionary")
        
        # Verify required keys
        assert "formatted_table" in result
        assert "latest_date" in result
        assert "latest_values" in result
        assert "growth_3m" in result
        print("  ✓ Contains all required keys")
        
        # Verify latest_values structure - should be dict with value and date
        assert "Unemployment Rate" in result["latest_values"], "Missing Unemployment Rate"
        assert "Real GDP" in result["latest_values"], "Missing Real GDP"
        
        # Check Unemployment Rate (monthly - should have latest value from June)
        unemp_info = result["latest_values"]["Unemployment Rate"]
        assert isinstance(unemp_info, dict), "latest_values should be dict with 'value' and 'date'"
        assert "value" in unemp_info, "Missing 'value' key"
        assert "date" in unemp_info, "Missing 'date' key"
        assert unemp_info["value"] == 3.6, f"Expected 3.6, got {unemp_info['value']}"
        assert "2024-06" in unemp_info["date"], f"Expected June 2024 date, got {unemp_info['date']}"
        print(f"  ✓ Unemployment Rate: {unemp_info['value']} as of {unemp_info['date']}")
        
        # Check Real GDP (quarterly - should have latest value from April, NOT NaN from June)
        gdp_info = result["latest_values"]["Real GDP"]
        assert isinstance(gdp_info, dict), "latest_values should be dict with 'value' and 'date'"
        assert "value" in gdp_info, "Missing 'value' key"
        assert "date" in gdp_info, "Missing 'date' key"
        assert gdp_info["value"] == 105.0, f"Expected 105.0 (not NaN), got {gdp_info['value']}"
        assert "2024-04" in gdp_info["date"], f"Expected April 2024 date (Q2), got {gdp_info['date']}"
        print(f"  ✓ Real GDP: {gdp_info['value']} as of {gdp_info['date']} (correctly anchored, not NaN)")
        
        # Verify growth_3m for Unemployment (should work with 6 monthly values)
        assert "Unemployment Rate" in result["growth_3m"]
        unemp_growth = result["growth_3m"]["Unemployment Rate"]
        # Growth from index[-3] (3.8 in April) to index[-1] (3.6 in June): (3.6-3.8)/3.8 * 100 = -5.26%
        # Values: [3.7, 3.8, 3.9, 3.8, 3.7, 3.6], so last 3 are [3.8, 3.7, 3.6]
        expected_growth = ((3.6 - 3.8) / 3.8) * 100
        assert abs(unemp_growth - expected_growth) < 0.1, f"Expected {expected_growth:.2f}%, got {unemp_growth:.2f}%"
        print(f"  ✓ Unemployment growth_3m: {unemp_growth:.2f}%")
        
        # Verify growth_3m for Real GDP (only 2 valid values, so should NOT be in growth_3m)
        # Actually, with indices [-1] and [-3], we need at least 3 values
        # We only have 2 GDP values (Jan and Apr), so growth_3m should be empty for GDP
        if "Real GDP" in result["growth_3m"]:
            print(f"  ⚠ Real GDP has growth_3m: {result['growth_3m']['Real GDP']:.2f}% (only 2 points)")
        else:
            print("  ✓ Real GDP has no growth_3m (insufficient data)")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_narrative_with_ragged_edge():
    """Test that generate_narrative correctly formats per-series dates."""
    print("\nTesting generate_narrative with ragged edge data...")
    
    try:
        from src.macro_econ_data_archive.streamlit_app import (
            generate_narrative
        )
        
        # Mock data_summary with new structure
        data_summary = {
            "formatted_table": "| Date | UNRATE | GDPC1 |\n|------|--------|-------|\n| 2024-06-30 | 3.6 | N/A |",
            "latest_date": "2024-06-30",
            "latest_values": {
                "Unemployment Rate": {"value": 3.6, "date": "2024-06-30"},
                "Real GDP": {"value": 105.0, "date": "2024-04-30"}
            },
            "growth_3m": {
                "Unemployment Rate": -7.69
            }
        }
        
        # Test with mock OpenAI API
        with patch('src.macro_econ_data_archive.streamlit_app.OpenAI') as MockOpenAI:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test narrative"
            mock_client.chat.completions.create.return_value = mock_response
            MockOpenAI.return_value = mock_client
            
            narrative = generate_narrative(
                data_summary,
                "Economic Indicators",
                "test_key"
            )
            
            # Verify the function was called
            assert MockOpenAI.called, "OpenAI should be called"
            assert mock_client.chat.completions.create.called, "chat.completions.create should be called"
            
            # Get the actual prompt sent
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            user_prompt = messages[1]['content']
            
            # Verify the prompt includes per-series dates
            assert "Unemployment Rate: 3.60 (as of 2024-06-30)" in user_prompt, "Should include per-series date for UNRATE"
            assert "Real GDP: 105.00 (as of 2024-04-30)" in user_prompt, "Should include per-series date for GDP"
            assert "LATEST DATA REPORT" in user_prompt, "Should have LATEST DATA REPORT section"
            
            print("  ✓ generate_narrative correctly formats per-series dates")
            print(f"  ✓ Prompt includes: 'Unemployment Rate: 3.60 (as of 2024-06-30)'")
            print(f"  ✓ Prompt includes: 'Real GDP: 105.00 (as of 2024-04-30)'")
            
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test backward compatibility with legacy format."""
    print("\nTesting backward compatibility with legacy format...")
    
    try:
        from src.macro_econ_data_archive.streamlit_app import (
            generate_narrative
        )
        
        # Mock data_summary with LEGACY structure (plain float values)
        data_summary = {
            "formatted_table": "| Date | Value |\n|------|-------|\n| 2024-06-30 | 3.6 |",
            "latest_date": "2024-06-30",
            "latest_values": {
                "Unemployment Rate": 3.6  # Legacy format - plain float
            },
            "growth_3m": {
                "Unemployment Rate": -7.69
            }
        }
        
        # Test with mock OpenAI API
        with patch('src.macro_econ_data_archive.streamlit_app.OpenAI') as MockOpenAI:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test narrative"
            mock_client.chat.completions.create.return_value = mock_response
            MockOpenAI.return_value = mock_client
            
            narrative = generate_narrative(
                data_summary,
                "Unemployment Rate",
                "test_key"
            )
            
            # Verify the function was called without error
            assert MockOpenAI.called, "OpenAI should be called"
            
            # Get the actual prompt sent
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            user_prompt = messages[1]['content']
            
            # Should handle legacy format gracefully (without date)
            assert "Unemployment Rate: 3.60" in user_prompt, "Should include value from legacy format"
            
            print("  ✓ generate_narrative handles legacy format gracefully")
            print("  ✓ No errors with plain float values")
            
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_empty_dataframe():
    """Test that empty dataframes are handled gracefully."""
    print("\nTesting empty dataframe handling...")
    
    try:
        from src.macro_econ_data_archive.streamlit_app import (
            prepare_data_summary,
            SeriesInfo
        )
        
        # Empty dataframe
        df = pd.DataFrame()
        series_list = [SeriesInfo(series_id="GDPC1", series_label="Real GDP")]
        
        result = prepare_data_summary(df, series_list, periods=24)
        
        assert isinstance(result, dict), "Should return dict"
        assert result["formatted_table"] == "No data available"
        assert result["latest_date"] is None
        assert result["latest_values"] == {}
        assert result["growth_3m"] == {}
        
        print("  ✓ Empty dataframe handled gracefully")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("RAGGED EDGE FIX TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_ragged_edge_monthly_quarterly_mix,
        test_generate_narrative_with_ragged_edge,
        test_backward_compatibility,
        test_empty_dataframe
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
