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

                # Try to find the series column - prefer exact match, fallback to first numeric column
                if sid not in raw.columns:
                    # Fallback: use first non-date numeric column if available
                    numeric_cols = [col for col in raw.columns if col != date_col and
                                   pd.api.types.is_numeric_dtype(raw[col])]
                    if numeric_cols:
                        actual_col = numeric_cols[0]
                        # Warn but continue - this handles cases where FRED returns differently named columns
                        import warnings
                        warnings.warn(
                            f"FRED response for '{sid}' missing expected column, "
                            f"using '{actual_col}' instead. This may indicate a FRED API change.",
                            UserWarning
                        )
                        # Rename to expected column name for consistency downstream
                        raw[sid] = raw[actual_col]
                    else:
                        raise ValueError(
                            f"Unexpected FRED response for series '{sid}': missing '{sid}' column "
                            f"and no numeric fallback columns found. Available columns: {list(raw.columns)}"
                        )

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


# --------------------------
# FRED Release Calendar
# --------------------------

def get_series_release_info(series_id: str, api_key: str) -> dict:
    """
    Get release schedule information for a FRED series.
    
    This function queries the FRED API to find which release a series belongs to,
    then determines the next scheduled release date for that release.
    
    Args:
        series_id: FRED series ID (e.g., "GDPC1", "UNRATE")
        api_key: FRED API key (obtain from https://fred.stlouisfed.org/docs/api/api_key.html)
    
    Returns:
        Dictionary with keys:
            - series_id: The series ID
            - release_name: Name of the release (e.g., "Employment Situation")
            - next_release_date: Next scheduled release date as string (YYYY-MM-DD) or "TBD"
            - release_id: FRED release ID (for reference)
    
    Raises:
        Exception: If API request fails or data cannot be retrieved
    
    Example:
        >>> info = get_series_release_info("UNRATE", "your_api_key")
        >>> print(info)
        {'series_id': 'UNRATE', 'release_name': 'Employment Situation', 
         'next_release_date': '2026-02-07', 'release_id': 50}
    """
    if not api_key:
        raise ValueError("FRED API key is required")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        # Step 1: Find which release this series belongs to
        series_release_url = (
            f"https://api.stlouisfed.org/fred/series/release"
            f"?series_id={series_id}&api_key={api_key}&file_type=json"
        )
        
        response = requests.get(series_release_url, headers=headers, timeout=30)
        response.raise_for_status()
        release_data = response.json()
        
        # Extract release information
        releases = release_data.get('releases', [])
        if not releases:
            # Series might not be part of a regular release schedule
            return {
                'series_id': series_id,
                'release_name': 'N/A',
                'next_release_date': 'TBD',
                'release_id': None
            }
        
        # Use the first (primary) release
        release = releases[0]
        release_id = release.get('id')
        release_name = release.get('name', 'Unknown Release')
        
        # Step 2: Get next release date for this release
        today = pd.Timestamp.now().strftime('%Y-%m-%d')
        release_dates_url = (
            f"https://api.stlouisfed.org/fred/release/dates"
            f"?release_id={release_id}&api_key={api_key}"
            f"&include_release_dates_with_no_data=true"
            f"&realtime_start={today}&file_type=json"
        )
        
        response = requests.get(release_dates_url, headers=headers, timeout=30)
        response.raise_for_status()
        dates_data = response.json()
        
        # Extract future release dates
        release_dates = dates_data.get('release_dates', [])
        if release_dates:
            # Get the first (soonest) future release date
            next_date = release_dates[0].get('date', 'TBD')
        else:
            next_date = 'TBD'
        
        return {
            'series_id': series_id,
            'release_name': release_name,
            'next_release_date': next_date,
            'release_id': release_id
        }
    
    except requests.exceptions.RequestException as e:
        # Network or API error
        return {
            'series_id': series_id,
            'release_name': 'Error',
            'next_release_date': 'TBD',
            'release_id': None,
            'error': str(e)
        }
    except Exception as e:
        # Other errors (parsing, etc.)
        return {
            'series_id': series_id,
            'release_name': 'Error',
            'next_release_date': 'TBD',
            'release_id': None,
            'error': str(e)
        }
