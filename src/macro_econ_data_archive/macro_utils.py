#!/usr/bin/env python3
"""
macro_utils.py

Utility functions for fetching and transforming macroeconomic data.
Extracted from generate_macro_report.py to enable reuse in both CLI and Streamlit apps.
"""

from __future__ import annotations

from typing import List
from urllib.parse import quote_plus
import requests
import io
import time

import pandas as pd


# --------------------------
# Custom Exceptions
# --------------------------

class FREDRateLimitError(Exception):
    """Raised when FRED API rate limit is exceeded (403 error)."""
    pass


class FREDServerError(Exception):
    """Raised when FRED API returns a server error (5xx)."""
    pass


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

def fetch_fred(
    series_ids: List[str], 
    start: str = "1990-01-01",
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> pd.DataFrame:
    """
    Fetch series from FRED via the public `fredgraph.csv` endpoint (no API key).
    Includes retry logic with exponential backoff for transient errors.
    
    Args:
        series_ids: List of FRED series IDs to fetch
        start: Start date for data (YYYY-MM-DD format)
        max_retries: Maximum number of retry attempts for transient errors
        backoff_factor: Exponential backoff multiplier (delay = backoff_factor ** attempt)
    
    Returns:
        DataFrame with fetched series as columns
    
    Raises:
        FREDRateLimitError: If rate limit is exceeded (403 error)
        FREDServerError: If server error persists after retries (5xx)
        Exception: If data cannot be fetched from FRED for other reasons
    """
    start_ts = pd.to_datetime(start)
    df = pd.DataFrame()
    
    # Use requests with a proper User-Agent to avoid 403 Forbidden
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }
    
    for sid in series_ids:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={quote_plus(sid)}"
        
        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                
                # Handle rate limiting (403) - don't retry, raise immediately
                if response.status_code == 403:
                    raise FREDRateLimitError(
                        f"FRED rate limit exceeded for series '{sid}'. "
                        f"Please wait a few minutes before trying again."
                    )
                
                # Handle server errors (5xx) - retry with backoff
                if 500 <= response.status_code < 600:
                    if attempt < max_retries - 1:
                        delay = backoff_factor ** attempt
                        time.sleep(delay)
                        continue
                    else:
                        raise FREDServerError(
                            f"FRED server error ({response.status_code}) for series '{sid}' "
                            f"after {max_retries} attempts."
                        )
                
                # Raise for other HTTP errors
                response.raise_for_status()
                
                # Read CSV from response content
                raw = pd.read_csv(io.StringIO(response.text))
                
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
                
                # Success - break retry loop
                break
                
            except (FREDRateLimitError, FREDServerError):
                # Don't retry these, just re-raise
                raise
                
            except requests.exceptions.RequestException as e:
                # Network/connection errors - retry with backoff
                last_error = e
                if attempt < max_retries - 1:
                    delay = backoff_factor ** attempt
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(
                        f"Failed to fetch data for {sid} after {max_retries} attempts: {str(e)}"
                    )
                    
            except Exception as e:
                # Other errors (parsing, etc.) - don't retry
                raise Exception(f"Failed to fetch data for {sid}: {str(e)}")
            
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
