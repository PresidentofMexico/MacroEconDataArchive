#!/usr/bin/env python3
"""
macro_utils.py

Utility functions for fetching and transforming macroeconomic data.
Extracted from generate_macro_report.py to enable reuse in both CLI and Streamlit apps.
"""

from typing import List
import pandas as pd
from pandas_datareader import data as pdr


# --------------------------
# Transform utilities
# --------------------------

def yoy(series: pd.Series, periods: int) -> pd.Series:
    """
    Year-over-year percent change for the given periodicity.
    
    Args:
        series: Time series data
        periods: Number of periods for comparison (e.g., 12 for monthly, 4 for quarterly)
    
    Returns:
        Series with YoY percent change
    """
    return 100.0 * (series / series.shift(periods) - 1.0)


def qoq_saar(series: pd.Series) -> pd.Series:
    """
    Quarter-over-quarter change at a seasonally adjusted annual rate.
    
    Args:
        series: Time series data
    
    Returns:
        Series with QoQ SAAR percent change
    """
    return 100.0 * ((series / series.shift(1)) ** 4 - 1.0)


def safe_to_numeric(s: pd.Series) -> pd.Series:
    """
    Safely convert series to numeric, coercing errors to NaN.
    
    Args:
        s: Series to convert
    
    Returns:
        Numeric series
    """
    return pd.to_numeric(s, errors="coerce")


def infer_yoy_periods(freq: str) -> int:
    """
    Infer the number of periods for year-over-year calculation based on frequency.
    
    Args:
        freq: Frequency string (e.g., "monthly", "quarterly", "weekly", "daily")
    
    Returns:
        Number of periods in a year
    """
    f = freq.lower()
    if f.startswith("m"):
        return 12
    if f.startswith("q"):
        return 4
    if f.startswith("w"):
        return 52
    if f.startswith("d"):
        return 365
    # default to 12
    return 12


# --------------------------
# Data fetch
# --------------------------

def fetch_fred(series_ids: List[str], start: str = "1990-01-01") -> pd.DataFrame:
    """
    Fetch series from FRED via pandas_datareader. Requires internet access.
    
    Args:
        series_ids: List of FRED series IDs to fetch
        start: Start date for data (YYYY-MM-DD format)
    
    Returns:
        DataFrame with fetched series as columns
    
    Raises:
        Exception: If data cannot be fetched from FRED
    """
    df = pd.DataFrame()
    for sid in series_ids:
        s = pdr.DataReader(sid, "fred", start=start)
        if isinstance(s, pd.DataFrame):
            # Handle case where column name might not match series ID exactly
            if sid in s.columns:
                s = s[sid]
            else:
                # Take the first column if exact match not found
                s = s.iloc[:, 0]
        df[sid] = safe_to_numeric(s)
    return df


def build_series_for_chart(df: pd.DataFrame, transform: str, frequency: str = "monthly") -> pd.DataFrame:
    """
    Apply transformation to dataframe based on specified transform type.
    
    Args:
        df: Raw data DataFrame
        transform: Type of transformation ("level", "yoy", or "qoq_saar")
        frequency: Data frequency for YoY calculation
    
    Returns:
        Transformed DataFrame
    
    Raises:
        ValueError: If unknown transform type is specified
    """
    out = pd.DataFrame(index=df.index)
    if transform == "level":
        out = df.copy()
    elif transform == "yoy":
        periods = infer_yoy_periods(frequency)
        for c in df.columns:
            out[c] = yoy(df[c], periods=periods)
    elif transform == "qoq_saar":
        for c in df.columns:
            out[c] = qoq_saar(df[c])
    else:
        raise ValueError(f"Unknown transform: {transform}")
    return out
