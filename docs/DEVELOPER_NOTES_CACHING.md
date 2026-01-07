# Developer Notes: Caching Implementation

## Overview

This document details the caching implementation in MacroEconDataArchive, including the retry logic, exponential backoff, and Streamlit caching layer.

## Architecture

### Components

1. **fetch_fred()** - Core data fetching with retry logic (macro_utils.py)
2. **fetch_fred_cached()** - Streamlit caching wrapper (streamlit_app.py)
3. **Custom Exceptions** - FREDRateLimitError, FREDServerError (macro_utils.py)

### Data Flow

```
User Request
    ↓
fetch_fred_cached() [Streamlit @cache_data, 1hr TTL]
    ↓
fetch_fred() [Retry logic + exponential backoff]
    ↓
FRED CSV Endpoint (https://fred.stlouisfed.org/graph/fredgraph.csv)
    ↓
pandas DataFrame
```

## Core Implementation

### fetch_fred() Function

Located in `src/macro_econ_data_archive/macro_utils.py`

```python
def fetch_fred(
    series_ids: List[str],
    start: str = "1990-01-01",
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> pd.DataFrame:
```

**Features:**
- Fetches multiple series in a single call
- Exponential backoff retry logic
- 30-second HTTP timeout
- Custom exception handling

### Retry Logic

#### Error Handling Strategy

| Status Code | Action | Reasoning |
|-------------|--------|-----------|
| 200 OK | Return data | Success |
| 403 Forbidden | Raise FREDRateLimitError immediately | Rate limit exceeded, retrying won't help |
| 500-599 Server | Retry with backoff | Transient error, may resolve |
| Network errors | Retry with backoff | Temporary connection issue |

#### Exponential Backoff

Delays between retries: 2^(attempt-1) seconds

- Attempt 1: Immediate
- Attempt 2: Wait 1 second (2^0)
- Attempt 3: Wait 2 seconds (2^1)
- Attempt 4: Wait 4 seconds (2^2)

**Total wait time for 3 retries**: ~7 seconds

**Code:**
```python
for attempt in range(max_retries):
    try:
        response = requests.get(url, headers=headers, timeout=30)

        # Fail fast on rate limit
        if response.status_code == 403:
            raise FREDRateLimitError(...)

        # Retry on server errors
        if 500 <= response.status_code < 600:
            if attempt < max_retries - 1:
                delay = backoff_factor ** attempt
                time.sleep(delay)
                continue
            else:
                raise FREDServerError(...)

        # Success
        response.raise_for_status()
        return process_data(response)

    except requests.RequestException as e:
        # Network error - retry
        if attempt < max_retries - 1:
            time.sleep(backoff_factor ** attempt)
            continue
        raise
```

### Streamlit Caching Layer

Located in `src/macro_econ_data_archive/streamlit_app.py`

```python
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fred_cached(series_ids: List[str], start: str) -> pd.DataFrame:
    """Cached wrapper with 1-hour TTL."""
    return fetch_fred(series_ids, start=start)
```

**Configuration:**
- **TTL**: 3600 seconds (1 hour)
- **show_spinner**: False (handled at call site)
- **Cache key**: Automatic based on function arguments

**Benefits:**
- Reduces API calls
- Improves UI responsiveness
- Respects FRED usage limits

## Custom Exceptions

### FREDRateLimitError

**When raised**: HTTP 403 from FRED API

**Meaning**: Rate limit exceeded (too many requests)

**User action**: Wait a few minutes before retrying

**Implementation:**
```python
class FREDRateLimitError(Exception):
    """Raised when FRED API rate limit is exceeded (403 error)."""
    pass
```

### FREDServerError

**When raised**: HTTP 5xx from FRED after max retries

**Meaning**: FRED server issue persists

**User action**: Try again later or check FRED status

**Implementation:**
```python
class FREDServerError(Exception):
    """Raised when FRED API returns a server error (5xx)."""
    pass
```

## Performance Considerations

### Cache Hit Rate

Expected hit rate depends on usage pattern:
- Single user: ~80-90% (repeated views of same data)
- Multiple users: ~50-70% (shared cache across sessions)

### Memory Usage

Each cached DataFrame: ~10-100 KB (varies by series length)

Typical cache size: 1-10 MB for 10-100 cached series

### Network Impact

Without caching:
- Each chart fetch: ~500ms - 2s
- Report with 10 charts: 5-20 seconds total

With caching:
- Cached fetch: ~1-10ms
- Report with 10 charts: ~10-100ms total

## Cache Management

### Manual Cache Clear

**Streamlit UI:**
- Sidebar → Settings → "Clear Data Cache" button

**Programmatic:**
```python
from macro_econ_data_archive.streamlit_app import fetch_fred_cached
fetch_fred_cached.clear()
```

### Automatic Expiration

Cache entries expire after 1 hour (3600 seconds) automatically.

## Testing

### Unit Tests

Located in `test_caching_and_retry.py`

**Tests:**
1. Custom exceptions creation
2. fetch_fred signature validation
3. Retry logic with mocked requests
4. Exponential backoff timing
5. HTTP timeout enforcement
6. Streamlit cache decorator

**Run:**
```bash
python test_caching_and_retry.py
```

### Manual Testing

**Test rate limit handling:**
```python
# This will fail (invalid series)
try:
    fetch_fred(['INVALID_SERIES'])
except Exception as e:
    print(type(e), str(e))
```

**Test retry logic:**
```python
# Mock transient failure
with patch('requests.get') as mock:
    mock.side_effect = [
        Mock(status_code=500),  # Fail
        Mock(status_code=200, text="DATE,GDP\n2020-01-01,100\n")  # Success
    ]
    df = fetch_fred(['GDP'])
    print(f"Fetched {len(df)} rows after retry")
```

## Edge Cases

### Empty Series

**Scenario**: FRED returns empty data

**Handling**: Returns empty DataFrame, caller decides action

### Multiple Series, Partial Failure

**Scenario**: 2 of 3 series fail to fetch

**Handling**: Returns DataFrame with successful series only

### Network Timeout

**Scenario**: Request takes > 30 seconds

**Handling**: Raises TimeoutError, retries if attempts remain

## Configuration

### Adjusting Retry Parameters

**CLI/Direct call:**
```python
df = fetch_fred(
    ['GDPC1'],
    start='2020-01-01',
    max_retries=5,  # More retries
    backoff_factor=1.5  # Slower backoff
)
```

**Streamlit:**
Modify `fetch_fred_cached()` wrapper to pass custom parameters

### Adjusting Cache TTL

Edit `streamlit_app.py`:
```python
@st.cache_data(ttl=7200, show_spinner=False)  # 2 hours
def fetch_fred_cached(...):
    ...
```

## Debugging

### Enable Verbose Logging

Add debug prints in `fetch_fred()`:

```python
print(f"Fetching {series_id}, attempt {attempt + 1}/{max_retries}")
print(f"Response status: {response.status_code}")
```

### Check Cache Status

```python
# In Streamlit script
import streamlit as st
st.write(f"Cache info: {fetch_fred_cached.cache_info()}")
```

## Best Practices

1. **Use cached wrapper**: Always use `fetch_fred_cached()` in Streamlit
2. **Handle exceptions**: Catch FREDRateLimitError and FREDServerError explicitly
3. **Provide user feedback**: Show error messages for rate limits
4. **Clear cache when needed**: After data updates or corrections
5. **Monitor performance**: Track cache hit rates in production

## Future Enhancements

Potential improvements:
- Persistent cache (disk-based)
- Cache warming (pre-fetch popular series)
- Adaptive retry strategy based on error patterns
- Cache analytics dashboard
- Multi-tier caching (memory + disk)

## References

- Streamlit caching docs: https://docs.streamlit.io/library/advanced-features/caching
- FRED API documentation: https://fred.stlouisfed.org/docs/api/
- Exponential backoff pattern: https://en.wikipedia.org/wiki/Exponential_backoff

## Summary

The caching implementation provides:
- ✅ Robust retry logic with exponential backoff
- ✅ Custom exceptions for clear error handling
- ✅ Streamlit integration with 1-hour TTL
- ✅ 30-second HTTP timeout
- ✅ Comprehensive test coverage
- ✅ Manual cache management
- ✅ Fail-fast on rate limits, retry on transient errors

This architecture ensures reliable data fetching while respecting API limits and providing excellent user experience.
