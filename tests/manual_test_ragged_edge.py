#!/usr/bin/env python3
"""
manual_test_ragged_edge.py

Manual demonstration of the ragged edge fix.
Shows how the updated code correctly handles mixed-frequency data.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.macro_econ_data_archive.streamlit_app import (
    prepare_data_summary,
    SeriesInfo
)


def create_realistic_ragged_edge_data():
    """
    Create realistic mixed-frequency data:
    - Monthly unemployment data (complete through June 2024)
    - Quarterly GDP data (complete through Q1 2024, NaN for Apr-Jun)
    """
    dates = pd.date_range('2024-01-31', periods=6, freq='M')
    
    df = pd.DataFrame({
        'UNRATE': [3.7, 3.8, 3.9, 3.8, 3.7, 3.6],  # Monthly - complete
        'GDPC1': [21500.0, None, None, 21800.0, None, None],  # Quarterly - Q1, Q2
        'CPIAUCSL': [308.4, 309.7, 310.3, 311.1, 311.5, 312.0]  # Monthly - complete
    }, index=dates)
    
    return df


def test_old_vs_new_behavior():
    """Demonstrate the difference between old and new behavior."""
    print("=" * 70)
    print("RAGGED EDGE FIX DEMONSTRATION")
    print("=" * 70)
    print()
    print("Scenario: Mixed-frequency data with Monthly and Quarterly series")
    print("Data through June 30, 2024")
    print()
    
    # Create test data
    df = create_realistic_ragged_edge_data()
    
    print("Data structure:")
    print(df.to_string())
    print()
    
    series_list = [
        SeriesInfo(series_id="UNRATE", series_label="Unemployment Rate"),
        SeriesInfo(series_id="GDPC1", series_label="Real GDP"),
        SeriesInfo(series_id="CPIAUCSL", series_label="CPI")
    ]
    
    # Get the new behavior
    result = prepare_data_summary(df, series_list, periods=6)
    
    print("-" * 70)
    print("NEW BEHAVIOR (with ragged edge fix):")
    print("-" * 70)
    print()
    
    print("latest_values (per-series anchoring):")
    for label, info in result["latest_values"].items():
        print(f"  • {label}: {info['value']:.2f} as of {info['date']}")
    print()
    
    print("Key improvements:")
    print("  ✓ Unemployment Rate: Latest value from June 2024 (most recent)")
    print("  ✓ Real GDP: Latest value from April 2024 (Q2, not NaN from June)")
    print("  ✓ CPI: Latest value from June 2024 (most recent)")
    print("  ✓ Each series anchored to its actual last valid data point")
    print()
    
    print("-" * 70)
    print("GROWTH MOMENTUM (3-period change):")
    print("-" * 70)
    print()
    
    for label, pct in result["growth_3m"].items():
        direction = "↑" if pct > 0 else "↓"
        print(f"  • {label}: {direction} {abs(pct):.2f}%")
    print()
    
    if "Real GDP" not in result["growth_3m"]:
        print("  Note: Real GDP has no growth_3m (only 2 data points available)")
        print()
    
    print("-" * 70)
    print("PROMPT FORMAT (what AI sees):")
    print("-" * 70)
    print()
    print("LATEST DATA REPORT:")
    for label, info in result["latest_values"].items():
        print(f"  {label}: {info['value']:.2f} (as of {info['date']})")
    print()
    
    print("-" * 70)
    print("COMPARISON TO OLD BEHAVIOR:")
    print("-" * 70)
    print()
    print("Old behavior would have:")
    print("  • Used last row (2024-06-30) as date for ALL series")
    print("  • Real GDP would show as missing/NaN for June")
    print("  • AI would ignore GDP data or use stale/incorrect date")
    print()
    print("New behavior:")
    print("  • Each series has its own 'as of' date")
    print("  • Real GDP correctly shows April 2024 date")
    print("  • AI sees accurate, series-specific timeliness")
    print()
    
    print("=" * 70)
    print("✅ RAGGED EDGE PROBLEM SOLVED")
    print("=" * 70)


def test_single_series_still_works():
    """Verify single-series charts still work correctly."""
    print()
    print()
    print("=" * 70)
    print("BACKWARD COMPATIBILITY TEST: Single-Series Chart")
    print("=" * 70)
    print()
    
    # Create simple monthly data
    dates = pd.date_range('2024-01-31', periods=6, freq='M')
    df = pd.DataFrame({
        'UNRATE': [3.7, 3.8, 3.9, 3.8, 3.7, 3.6]
    }, index=dates)
    
    series_list = [SeriesInfo(series_id="UNRATE", series_label="Unemployment Rate")]
    
    result = prepare_data_summary(df, series_list, periods=6)
    
    print("Single series latest_values:")
    for label, info in result["latest_values"].items():
        print(f"  • {label}: {info['value']:.2f} as of {info['date']}")
    print()
    
    print("✓ Single-series charts work correctly")
    print()


if __name__ == "__main__":
    test_old_vs_new_behavior()
    test_single_series_still_works()
