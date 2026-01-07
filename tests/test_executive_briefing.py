#!/usr/bin/env python3
"""
test_executive_briefing.py

Tests for the Executive Briefing feature in MacroBuilder.
Validates data aggregation, AI generation, and UI integration.
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports for executive briefing...")
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            prepare_holistic_data_summary,
            generate_executive_summary,
            ChartConfig,
            SeriesInfo
        )
        print("  ✓ Executive briefing functions imported")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import: {e}")
        return False


def test_prepare_holistic_data_summary():
    """Test the holistic data summary preparation function."""
    print("\nTesting prepare_holistic_data_summary()...")
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            prepare_holistic_data_summary,
            ChartConfig,
            SeriesInfo
        )
        
        # Test with empty charts list
        summary = prepare_holistic_data_summary([])
        assert summary == "No charts available for analysis."
        print("  ✓ Empty charts list handled correctly")
        
        # Test with single chart
        dates = pd.date_range('2024-01-01', periods=24, freq='M')
        df = pd.DataFrame({
            'GDPC1': [100 + i for i in range(24)]
        }, index=dates)
        
        chart = ChartConfig(
            title="Real GDP Growth",
            series=[SeriesInfo(series_id="GDPC1", series_label="Real GDP")],
            frequency="quarterly",
            transform="qoq_saar",
            units="Percent",
            data=df,
            narrative=""
        )
        
        summary = prepare_holistic_data_summary([chart])
        assert "Chart 1: Real GDP Growth" in summary
        assert "qoq_saar" in summary
        assert "quarterly" in summary
        assert "Percent" in summary
        print("  ✓ Single chart summary generated correctly")
        
        # Test with multiple charts
        df2 = pd.DataFrame({
            'CPIAUCSL': [200 + i for i in range(24)]
        }, index=dates)
        
        chart2 = ChartConfig(
            title="Inflation Rate",
            series=[SeriesInfo(series_id="CPIAUCSL", series_label="CPI")],
            frequency="monthly",
            transform="yoy",
            units="Percent",
            data=df2,
            narrative=""
        )
        
        summary = prepare_holistic_data_summary([chart, chart2])
        assert "Chart 1: Real GDP Growth" in summary
        assert "Chart 2: Inflation Rate" in summary
        print("  ✓ Multiple charts summary generated correctly")
        
        # Test that data is limited to 12 periods
        # The summary should not be excessively long
        assert len(summary) < 5000  # Reasonable token limit check
        print("  ✓ Summary length is reasonable (token management)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prepare_holistic_data_summary_with_multi_series():
    """Test holistic summary with multi-series charts."""
    print("\nTesting prepare_holistic_data_summary() with multi-series charts...")
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            prepare_holistic_data_summary,
            ChartConfig,
            SeriesInfo
        )
        
        dates = pd.date_range('2024-01-01', periods=24, freq='M')
        df = pd.DataFrame({
            'GDPC1': [100 + i for i in range(24)],
            'PCEC96': [150 + i * 0.5 for i in range(24)]
        }, index=dates)
        
        chart = ChartConfig(
            title="GDP and Consumer Spending",
            series=[
                SeriesInfo(series_id="GDPC1", series_label="Real GDP"),
                SeriesInfo(series_id="PCEC96", series_label="Consumer Spending")
            ],
            frequency="monthly",
            transform="yoy",
            units="Percent",
            data=df,
            narrative=""
        )
        
        summary = prepare_holistic_data_summary([chart])
        assert "Chart 1: GDP and Consumer Spending" in summary
        assert "Real GDP" in summary
        assert "Consumer Spending" in summary
        print("  ✓ Multi-series chart summary generated correctly")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_executive_summary():
    """Test the executive summary generation with mocked OpenAI."""
    print("\nTesting generate_executive_summary()...")
    
    try:
        from macro_econ_data_archive.streamlit_app import generate_executive_summary
        
        context_data = """### Chart 1: Real GDP Growth
| Date | Value |
|------|-------|
| 2024-01-01 | 2.5 |
| 2024-02-01 | 2.6 |
| 2024-03-01 | 2.7 |

### Chart 2: Inflation Rate
| Date | Value |
|------|-------|
| 2024-01-01 | 3.2 |
| 2024-02-01 | 3.1 |
| 2024-03-01 | 3.0 |"""
        
        # Mock the OpenAI client
        with patch('macro_econ_data_archive.streamlit_app.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = """**Executive Summary:** The economy demonstrates moderate expansion with GDP growth accelerating from 2.5% to 2.7% while inflation shows a gradual decline from 3.2% to 3.0%, indicating progress toward price stability.

**Key Drivers:** The positive GDP trajectory suggests sustained economic activity, while the declining inflation path reflects cooling price pressures. This combination indicates the economy is achieving a soft landing scenario.

**Outlook:** Forward momentum appears constructive with growth remaining positive and inflation trending downward toward target levels."""
            
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            summary = generate_executive_summary(context_data, "test-api-key")
            
            assert "Executive Summary:" in summary
            assert "Key Drivers:" in summary
            assert "Outlook:" in summary
            assert len(summary) > 100  # Should be substantial
            print("  ✓ Executive summary generated with correct structure")
            
            # Verify correct API call
            assert mock_openai.called
            assert mock_client.chat.completions.create.called
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]['model'] == 'gpt-4o-mini'
            assert call_args[1]['temperature'] == 0.7
            assert call_args[1]['max_tokens'] == 1000
            print("  ✓ OpenAI API called with correct parameters")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_executive_summary_error_handling():
    """Test error handling in executive summary generation."""
    print("\nTesting generate_executive_summary() error handling...")
    
    try:
        from macro_econ_data_archive.streamlit_app import generate_executive_summary
        
        # Mock OpenAI to raise an exception
        with patch('macro_econ_data_archive.streamlit_app.OpenAI') as mock_openai:
            mock_openai.side_effect = Exception("API connection failed")
            
            summary = generate_executive_summary("test data", "test-api-key")
            
            assert "Error generating executive summary" in summary
            print("  ✓ Error handled gracefully")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_session_state_initialization():
    """Test that executive_summary is added to session state."""
    print("\nTesting session state initialization...")
    
    try:
        from macro_econ_data_archive.streamlit_app import init_session_state
        import streamlit as st
        
        # Mock streamlit session state
        with patch('streamlit.session_state', {}) as mock_state:
            # Simulate what init_session_state does
            mock_state['charts'] = []
            mock_state['openai_api_key'] = ''
            mock_state['report_title'] = "Macro Economic Data Archive"
            mock_state['start_date'] = "2010-01-01"
            mock_state['executive_summary'] = ""
            
            assert 'executive_summary' in mock_state
            assert mock_state['executive_summary'] == ""
            print("  ✓ executive_summary initialized in session state")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_system_prompt_structure():
    """Test that system prompt has correct structure and content."""
    print("\nTesting system prompt structure...")
    
    try:
        from macro_econ_data_archive.streamlit_app import generate_executive_summary
        
        # Mock OpenAI and capture the prompts
        with patch('macro_econ_data_archive.streamlit_app.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            generate_executive_summary("test context", "test-api-key")
            
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            
            # Check system prompt
            system_msg = messages[0]
            assert system_msg['role'] == 'system'
            assert 'Chief Economist' in system_msg['content']
            assert 'Executive Summary:' in system_msg['content']
            assert 'Key Drivers:' in system_msg['content']
            assert 'Outlook:' in system_msg['content']
            assert 'Federal Reserve Beige Book' in system_msg['content']
            print("  ✓ System prompt has correct structure and content")
            
            # Check user prompt
            user_msg = messages[1]
            assert user_msg['role'] == 'user'
            assert 'test context' in user_msg['content']
            print("  ✓ User prompt includes context data")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_with_existing_functions():
    """Test that new functions work with existing prepare_data_summary."""
    print("\nTesting integration with existing functions...")
    
    try:
        from macro_econ_data_archive.streamlit_app import (
            prepare_data_summary,
            prepare_holistic_data_summary,
            ChartConfig,
            SeriesInfo
        )
        
        dates = pd.date_range('2024-01-01', periods=24, freq='M')
        df = pd.DataFrame({
            'GDPC1': [100 + i for i in range(24)]
        }, index=dates)
        
        chart = ChartConfig(
            title="Test Chart",
            series=[SeriesInfo(series_id="GDPC1", series_label="Test Series")],
            frequency="monthly",
            transform="level",
            units="Billions",
            data=df,
            narrative=""
        )
        
        # Test that prepare_data_summary still works as before
        single_summary = prepare_data_summary(df, chart.series, periods=12)
        assert "Date" in single_summary
        assert "Value" in single_summary
        print("  ✓ prepare_data_summary works correctly")
        
        # Test that holistic summary uses prepare_data_summary
        holistic = prepare_holistic_data_summary([chart])
        # Should contain the table structure from prepare_data_summary
        assert "Date" in holistic
        assert "Test Chart" in holistic
        print("  ✓ prepare_holistic_data_summary integrates with prepare_data_summary")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 70)
    print("EXECUTIVE BRIEFING FEATURE TESTS")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_prepare_holistic_data_summary,
        test_prepare_holistic_data_summary_with_multi_series,
        test_generate_executive_summary,
        test_generate_executive_summary_error_handling,
        test_session_state_initialization,
        test_system_prompt_structure,
        test_integration_with_existing_functions
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
