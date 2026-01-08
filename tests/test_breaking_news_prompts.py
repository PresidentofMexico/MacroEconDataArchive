#!/usr/bin/env python3
"""
test_breaking_news_prompts.py

Tests for the Breaking News style prompt engineering updates.
Validates data summary metadata extraction, prompt formatting, and backward compatibility.
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports for breaking news prompts...")
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            prepare_data_summary,
            prepare_holistic_data_summary,
            generate_narrative,
            generate_executive_summary,
            ChartConfig,
            SeriesInfo
        )
        print("  ✓ All functions imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import: {e}")
        return False


def test_prepare_data_summary_returns_dict():
    """Test that prepare_data_summary returns a dictionary with metadata."""
    print("\nTesting prepare_data_summary() returns dict with metadata...")
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            prepare_data_summary,
            SeriesInfo
        )
        
        # Create test data with 6 months
        dates = pd.date_range('2024-01-01', periods=6, freq='M')
        df = pd.DataFrame({
            'GDPC1': [100, 102, 104, 103, 105, 107]
        }, index=dates)
        
        series_list = [SeriesInfo(series_id="GDPC1", series_label="Real GDP")]
        
        result = prepare_data_summary(df, series_list, periods=6)
        
        # Verify return type is dict
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        print("  ✓ Returns dictionary")
        
        # Verify required keys
        assert "formatted_table" in result, "Missing 'formatted_table' key"
        assert "latest_date" in result, "Missing 'latest_date' key"
        assert "latest_values" in result, "Missing 'latest_values' key"
        assert "growth_3m" in result, "Missing 'growth_3m' key"
        print("  ✓ Contains all required keys")
        
        # Verify formatted_table is a string
        assert isinstance(result["formatted_table"], str), "formatted_table should be string"
        assert "Date" in result["formatted_table"], "formatted_table should contain Date column"
        print("  ✓ formatted_table is valid markdown")
        
        # Verify latest_date
        assert result["latest_date"] is not None, "latest_date should not be None"
        print(f"  ✓ latest_date: {result['latest_date']}")
        
        # Verify latest_values (NEW FORMAT: dict with "value" and "date")
        assert "Real GDP" in result["latest_values"], "latest_values should contain 'Real GDP'"
        gdp_info = result["latest_values"]["Real GDP"]
        assert isinstance(gdp_info, dict), "latest_values should be dict with 'value' and 'date'"
        assert gdp_info["value"] == 107.0, f"latest_values value should be 107.0, got {gdp_info.get('value')}"
        assert "date" in gdp_info, "latest_values should have 'date' key"
        print(f"  ✓ latest_values: Real GDP = {gdp_info['value']} as of {gdp_info['date']}")
        
        # Verify growth_3m (should be (107-105)/105 * 100 = ~1.90%)
        # Data points: [100, 102, 104, 103, 105, 107]
        # Last 3 valid values at indices [-3, -2, -1] are: [105, 107]... wait, only 6 points total
        # Actually indices [-3] = 103, [-2] = 105, [-1] = 107
        # Growth = (107 - 103) / 103 * 100 = 3.88%
        assert "Real GDP" in result["growth_3m"], "growth_3m should contain 'Real GDP'"
        growth = result["growth_3m"]["Real GDP"]
        expected_growth = ((107 - 103) / 103) * 100
        assert abs(growth - expected_growth) < 0.1, f"growth_3m calculation incorrect: {growth} vs {expected_growth}"
        print(f"  ✓ growth_3m calculated correctly: {growth:.2f}%")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prepare_data_summary_multi_series():
    """Test prepare_data_summary with multiple series."""
    print("\nTesting prepare_data_summary() with multi-series...")
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            prepare_data_summary,
            SeriesInfo
        )
        
        # Create test data with 2 series
        dates = pd.date_range('2024-01-01', periods=5, freq='M')
        df = pd.DataFrame({
            'GDPC1': [100, 102, 104, 106, 108],
            'CPIAUCSL': [200, 202, 204, 203, 205]
        }, index=dates)
        
        series_list = [
            SeriesInfo(series_id="GDPC1", series_label="Real GDP"),
            SeriesInfo(series_id="CPIAUCSL", series_label="CPI")
        ]
        
        result = prepare_data_summary(df, series_list, periods=5)
        
        # Verify both series in latest_values (NEW FORMAT)
        assert "Real GDP" in result["latest_values"], "Missing Real GDP in latest_values"
        assert "CPI" in result["latest_values"], "Missing CPI in latest_values"
        gdp_info = result["latest_values"]["Real GDP"]
        cpi_info = result["latest_values"]["CPI"]
        assert isinstance(gdp_info, dict), "latest_values should be dict"
        assert isinstance(cpi_info, dict), "latest_values should be dict"
        assert gdp_info["value"] == 108.0, f"GDP value should be 108.0, got {gdp_info.get('value')}"
        assert cpi_info["value"] == 205.0, f"CPI value should be 205.0, got {cpi_info.get('value')}"
        print(f"  ✓ latest_values correct for multi-series: GDP={gdp_info['value']} as of {gdp_info['date']}, CPI={cpi_info['value']} as of {cpi_info['date']}")
        
        # Verify both series in growth_3m
        assert "Real GDP" in result["growth_3m"], "Missing Real GDP in growth_3m"
        assert "CPI" in result["growth_3m"], "Missing CPI in growth_3m"
        print(f"  ✓ growth_3m calculated for both series: {result['growth_3m']}")
        
        # Verify formatted table has both series
        assert "Real GDP" in result["formatted_table"], "Formatted table missing Real GDP column"
        assert "CPI" in result["formatted_table"], "Formatted table missing CPI column"
        print("  ✓ formatted_table contains both series")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prepare_data_summary_empty_data():
    """Test prepare_data_summary with empty data (backward compatibility)."""
    print("\nTesting prepare_data_summary() with empty data...")
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            prepare_data_summary,
            SeriesInfo
        )
        
        # Test with None
        result = prepare_data_summary(None, [], periods=6)
        assert result["formatted_table"] == "No data available"
        assert result["latest_date"] is None
        assert result["latest_values"] == {}
        assert result["growth_3m"] == {}
        print("  ✓ Handles None data gracefully")
        
        # Test with empty DataFrame
        df = pd.DataFrame()
        result = prepare_data_summary(df, [], periods=6)
        assert result["formatted_table"] == "No data available"
        print("  ✓ Handles empty DataFrame gracefully")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prepare_data_summary_insufficient_data_for_growth():
    """Test prepare_data_summary with less than 3 periods (no growth_3m)."""
    print("\nTesting prepare_data_summary() with insufficient data for 3m growth...")
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            prepare_data_summary,
            SeriesInfo
        )
        
        # Create test data with only 2 periods
        dates = pd.date_range('2024-01-01', periods=2, freq='M')
        df = pd.DataFrame({
            'GDPC1': [100, 102]
        }, index=dates)
        
        series_list = [SeriesInfo(series_id="GDPC1", series_label="Real GDP")]
        
        result = prepare_data_summary(df, series_list, periods=6)
        
        # Should have formatted_table and latest_values, but no growth_3m (NEW FORMAT)
        assert result["formatted_table"] != "No data available"
        gdp_info = result["latest_values"]["Real GDP"]
        assert isinstance(gdp_info, dict), "latest_values should be dict"
        assert gdp_info["value"] == 102.0, f"GDP value should be 102.0, got {gdp_info.get('value')}"
        assert result["growth_3m"] == {}, "growth_3m should be empty with insufficient data"
        print("  ✓ Handles insufficient data for growth calculation")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_narrative_accepts_dict():
    """Test that generate_narrative accepts dict parameter."""
    print("\nTesting generate_narrative() accepts dict parameter...")
    
    try:
        from macro_econ_data_archive.streamlit_app import generate_narrative
        
        # Mock OpenAI client
        with patch('macro_econ_data_archive.streamlit_app.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "As of 2024-06-30, Real GDP currently stands at 107.00..."
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Call with dict parameter
            data_summary = {
                "formatted_table": "| Date | Value |\n|------|-------|\n| 2024-06-30 | 107.00 |",
                "latest_date": "2024-06-30",
                "latest_values": {"Real GDP": 107.0},
                "growth_3m": {"Real GDP": 2.88}
            }
            
            result = generate_narrative(
                data_summary,
                "Real GDP",
                "fake-api-key"
            )
            
            assert isinstance(result, str), "Should return string"
            assert len(result) > 0, "Should return non-empty string"
            print("  ✓ generate_narrative accepts dict and returns narrative")
            
            # Verify the prompt includes latest data
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            user_prompt = messages[1]['content']
            
            assert "LATEST DATA" in user_prompt, "User prompt should include LATEST DATA section"
            assert "2024-06-30" in user_prompt, "User prompt should include latest date"
            assert "Real GDP: 107.00" in user_prompt, "User prompt should include latest value"
            assert "RECENT MOMENTUM" in user_prompt, "User prompt should include RECENT MOMENTUM section"
            print("  ✓ Prompt includes latest data and momentum sections")
            
            # Verify system prompt has Breaking News style
            system_prompt = messages[0]['content']
            assert "Breaking News" in system_prompt or "flash update" in system_prompt, \
                "System prompt should mention Breaking News or flash update"
            assert "80%" in system_prompt, "System prompt should mention 80% focus on recent data"
            assert "As of [Latest Date]" in system_prompt, "System prompt should instruct starting with latest date"
            print("  ✓ System prompt has Breaking News style")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prepare_holistic_data_summary_returns_dict():
    """Test that prepare_holistic_data_summary returns dict with metadata."""
    print("\nTesting prepare_holistic_data_summary() returns dict...")
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            prepare_holistic_data_summary,
            ChartConfig,
            SeriesInfo
        )
        
        # Create test charts
        dates = pd.date_range('2024-01-01', periods=6, freq='M')
        df1 = pd.DataFrame({'GDPC1': [100, 102, 104, 106, 108, 110]}, index=dates)
        df2 = pd.DataFrame({'CPIAUCSL': [200, 202, 204, 206, 208, 210]}, index=dates)
        
        charts = [
            ChartConfig(
                title="Real GDP",
                series=[SeriesInfo(series_id="GDPC1", series_label="Real GDP")],
                frequency="quarterly",
                transform="qoq_saar",
                units="Percent",
                data=df1,
                narrative=""
            ),
            ChartConfig(
                title="CPI",
                series=[SeriesInfo(series_id="CPIAUCSL", series_label="CPI")],
                frequency="monthly",
                transform="yoy",
                units="Percent",
                data=df2,
                narrative=""
            )
        ]
        
        result = prepare_holistic_data_summary(charts)
        
        # Verify return type is dict
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        print("  ✓ Returns dictionary")
        
        # Verify required keys
        assert "formatted_text" in result, "Missing 'formatted_text' key"
        assert "latest_overall_date" in result, "Missing 'latest_overall_date' key"
        assert "chart_summaries" in result, "Missing 'chart_summaries' key"
        print("  ✓ Contains all required keys")
        
        # Verify formatted_text
        assert isinstance(result["formatted_text"], str), "formatted_text should be string"
        assert "Chart 1: Real GDP" in result["formatted_text"]
        assert "Chart 2: CPI" in result["formatted_text"]
        print("  ✓ formatted_text contains both charts")
        
        # Verify latest_overall_date
        assert result["latest_overall_date"] is not None
        print(f"  ✓ latest_overall_date: {result['latest_overall_date']}")
        
        # Verify chart_summaries
        assert len(result["chart_summaries"]) == 2, "Should have 2 chart summaries"
        assert result["chart_summaries"][0]["title"] == "Real GDP"
        assert result["chart_summaries"][1]["title"] == "CPI"
        print("  ✓ chart_summaries contains metadata for both charts")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_executive_summary_accepts_dict():
    """Test that generate_executive_summary accepts dict parameter."""
    print("\nTesting generate_executive_summary() accepts dict parameter...")
    
    try:
        from macro_econ_data_archive.streamlit_app import generate_executive_summary
        
        # Mock OpenAI client
        with patch('macro_econ_data_archive.streamlit_app.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "As of 2024-06-30, the economy shows..."
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Call with dict parameter
            context_data = {
                "formatted_text": "### Chart 1: Real GDP\nData here...",
                "latest_overall_date": "2024-06-30",
                "chart_summaries": [
                    {
                        "title": "Real GDP",
                        "latest_date": "2024-06-30",
                        "latest_values": {"Real GDP": 110.0},
                        "growth_3m": {"Real GDP": 5.77}
                    }
                ]
            }
            
            result = generate_executive_summary(
                context_data,
                "fake-api-key"
            )
            
            assert isinstance(result, str), "Should return string"
            assert len(result) > 0, "Should return non-empty string"
            print("  ✓ generate_executive_summary accepts dict and returns summary")
            
            # Verify the prompt includes latest date
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            user_prompt = messages[1]['content']
            
            assert "2024-06-30" in user_prompt, "User prompt should include latest date"
            print("  ✓ Prompt includes latest overall date")
            
            # Verify system prompt has Breaking News style
            system_prompt = messages[0]['content']
            assert "As of [Latest Date]" in system_prompt, "System prompt should instruct starting with 'As of' date"
            assert "80%" in system_prompt or "recent momentum" in system_prompt, \
                "System prompt should emphasize recent data"
            print("  ✓ System prompt has Breaking News style with date instruction")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all test functions."""
    print("=" * 70)
    print("Running Breaking News Prompt Engineering Tests")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_prepare_data_summary_returns_dict,
        test_prepare_data_summary_multi_series,
        test_prepare_data_summary_empty_data,
        test_prepare_data_summary_insufficient_data_for_growth,
        test_generate_narrative_accepts_dict,
        test_prepare_holistic_data_summary_returns_dict,
        test_generate_executive_summary_accepts_dict
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n✗ {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))
    
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("-" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
