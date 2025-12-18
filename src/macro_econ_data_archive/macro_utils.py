#!/usr/bin/env python3
"""
macro_utils.py

Utility functions for fetching and transforming macroeconomic data.
Extracted from generate_macro_report.py to enable reuse in both CLI and Streamlit apps.
"""

from __future__ import annotations

from typing import List
from urllib.parse import quote_plus

import pandas as pd


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
    Fetch series from FRED via the public `fredgraph.csv` endpoint (no API key).
    
    Args:
        series_ids: List of FRED series IDs to fetch
        start: Start date for data (YYYY-MM-DD format)
    
    Returns:
        DataFrame with fetched series as columns
    
    Raises:
        Exception: If data cannot be fetched from FRED
    """
    start_ts = pd.to_datetime(start)
    df = pd.DataFrame()
    for sid in series_ids:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={quote_plus(sid)}"
        raw = pd.read_csv(url)
        if "DATE" in raw.columns:
            date_col = "DATE"
        elif "observation_date" in raw.columns:
            date_col = "observation_date"
        else:
            raise ValueError(f"Unexpected FRED response for series '{sid}': missing date column")

        raw[date_col] = pd.to_datetime(raw[date_col], errors="coerce")
        raw = raw.dropna(subset=[date_col]).set_index(date_col).sort_index()

        if sid not in raw.columns:
            raise ValueError(f"Unexpected FRED response for series '{sid}': missing '{sid}' column")

        s = safe_to_numeric(raw[sid])
        s = s[s.index >= start_ts]
        df[sid] = s
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
