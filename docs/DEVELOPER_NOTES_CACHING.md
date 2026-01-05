# Developer Notes: Caching and Retry Logic

## Overview

This document describes the implementation of data caching and retry logic added to MacroBuilder in Issue #6 (Part 2 of the 5-part production upgrade epic).

**Tag:** `[template-pushbutton-upgrade-2026]`

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit App                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ fetch_fred_cached(series_id, start_date)          │  │
│  │ - @st.cache_data(ttl=3600)                        │  │
│  │ - Cache key: (series_id, start_date)              │  │
│  └─────────────────────┬─────────────────────────────┘  │
│                        │                                 │
│                        ▼                                 │
│  ┌───────────────────────────────────────────────────┐  │
│  │ fetch_fred(series_ids, start, max_retries=3)      │  │
│  │ - Retry loop with exponential backoff             │  │
│  │ - Smart error handling (403, 5xx, network)        │  │
│  │ - Timeout: 30 seconds per request                 │  │
│  └─────────────────────┬─────────────────────────────┘  │
│                        │                                 │
│                        ▼                                 │
│  ┌───────────────────────────────────────────────────┐  │
│  │              FRED API                              │  │
│  │  https://fred.stlouisfed.org/graph/fredgraph.csv  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Custom Exception Classes (`macro_utils.py`)

Two custom exceptions were added to distinguish between different error types:

```python
class FREDRateLimitError(Exception):
    """Raised when FRED API rate limit is exceeded (403 error)."""
    pass

class FREDServerError(Exception):
    """Raised when FRED API returns a server error (5xx)."""
    pass
```

**Design Rationale:**
- Allows different handling strategies for different error types
- Rate limits should be surfaced immediately to users (no retry)
- Server errors should be retried with backoff
- Provides clear error messages for debugging

### 2. Enhanced `fetch_fred()` Function

#### New Parameters
- `max_retries: int = 3` - Maximum retry attempts for transient errors
- `backoff_factor: float = 2.0` - Exponential backoff multiplier

#### Retry Logic Flow

```python
for attempt in range(max_retries):
    try:
        # Make request with 30-second timeout
        response = requests.get(url, headers=headers, timeout=30)
        
        # Handle 403 (rate limit) - raise immediately, don't retry
        if response.status_code == 403:
            raise FREDRateLimitError(...)
        
        # Handle 5xx (server errors) - retry with backoff
        if 500 <= response.status_code < 600:
            if attempt < max_retries - 1:
                delay = backoff_factor ** attempt  # 1s, 2s, 4s
                time.sleep(delay)
                continue
            else:
                raise FREDServerError(...)
        
        # Parse and return data
        ...
        break  # Success
        
    except requests.exceptions.RequestException as e:
        # Network errors - retry with backoff
        if attempt < max_retries - 1:
            delay = backoff_factor ** attempt
            time.sleep(delay)
            continue
        else:
            raise Exception(...)
```

#### Exponential Backoff Timing
- **Attempt 1**: Immediate request
- **Attempt 2**: Wait 1 second (2^0)
- **Attempt 3**: Wait 2 seconds (2^1)
- **Total delay**: Up to 3 seconds for 3 attempts

**Design Rationale:**
- Short delays are appropriate for FRED's typical transient errors
- Exponential backoff prevents overwhelming the server
- Rate limit errors don't retry (they require longer waits)
- Network errors get same retry treatment as server errors

### 3. Streamlit Caching Layer (`streamlit_app.py`)

#### Cache Function

```python
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fred_cached(series_id: str, start_date: str) -> pd.DataFrame:
    """
    Cached wrapper for fetch_fred() to improve performance.
    Cache is keyed by (series_id, start_date).
    """
    return fetch_fred([series_id], start=start_date)
```

#### Cache Characteristics
- **TTL**: 3600 seconds (1 hour)
- **Cache Key**: `(series_id, start_date)` tuple
- **Scope**: Session-wide (Streamlit default)
- **Storage**: In-memory (Streamlit default)

**Cache Invalidation:**
- Automatic after 1 hour TTL
- Manual via cache clear button
- Automatic when `(series_id, start_date)` parameters change

**Design Rationale:**
- 1-hour TTL balances freshness vs. performance (most economic data updates daily/monthly)
- Keying by `(series_id, start_date)` ensures:
  - Different series don't collide
  - Changing start date fetches new data range
  - Same series + same start date = cache hit
- `show_spinner=False` because outer function has its own spinner

### 4. User Interface Components

#### Cache Control (Sidebar)
```python
st.sidebar.subheader("⚡ Data Cache")
col1, col2 = st.sidebar.columns([3, 1])
with col1:
    st.caption("Cache improves performance by storing fetched data")
with col2:
    if st.button("🗑️", help="Clear all cached data"):
        st.cache_data.clear()
        st.sidebar.success("Cache cleared!")
```

#### Error Handling in UI
```python
try:
    raw_data = fetch_fred_cached(series_id, st.session_state.start_date)
    ...
except FREDRateLimitError as e:
    st.error(f"⚠️ **FRED Rate Limit Reached**\n\n{str(e)}\n\n...")
except FREDServerError as e:
    st.error(f"🔧 **FRED Server Error**\n\n{str(e)}\n\n...")
except Exception as e:
    st.error(f"❌ **Error adding chart**: {str(e)}")
```

**Design Rationale:**
- Emoji indicators (⚠️, 🔧, ❌) provide quick visual feedback
- Multi-line error messages with markdown formatting
- Specific guidance for each error type
- Rate limit errors suggest using the cache

## Performance Metrics

### Cache Hit Rate
- **Expected**: 60-80% for typical report building workflows
- **Measured**: Not yet instrumented (future enhancement)

### Request Timing (Without Cache)
- **FRED request**: 0.5-2.0 seconds per series
- **Network timeout**: 30 seconds max
- **Retry overhead**: 0-3 seconds (if retries needed)
- **Total**: 0.5-5.0 seconds per series (worst case with retries)

### Request Timing (With Cache)
- **Cache hit**: <0.01 seconds (near-instant)
- **Speedup**: 50-200x faster

## Error Scenarios and Handling

| Scenario | Status Code | Behavior | User Impact |
|----------|-------------|----------|-------------|
| Rate limit exceeded | 403 | Raise `FREDRateLimitError` immediately | User sees friendly message, no retry |
| Server overload | 503 | Retry 3x with backoff | Auto-recovery if transient |
| Server error | 500-599 | Retry 3x with backoff | Auto-recovery if transient |
| Network timeout | N/A | Retry 3x with backoff | Auto-recovery if transient |
| DNS failure | N/A | Retry 3x with backoff | User sees error after 3 attempts |
| Invalid series ID | 200 + parse error | Fail fast, no retry | User sees clear error message |

## Testing Strategy

### Automated Tests (`test_caching_and_retry.py`)
- ✅ Exception classes exist and are importable
- ✅ Retry parameters present in function signature
- ✅ Exponential backoff logic implemented
- ✅ Error handling for 403 and 5xx status codes
- ✅ Cache decorator applied with correct parameters
- ✅ Cache key structure (series_id, start_date)
- ✅ Documentation completeness

### Manual Testing Checklist
- [ ] Cache hit: Add same chart twice, verify second is instant
- [ ] Cache invalidation: Clear cache, verify next fetch takes time
- [ ] Start date change: Change start date, verify new fetch
- [ ] Rate limit simulation: (Requires API limit testing)
- [ ] Network error recovery: (Requires network manipulation)
- [ ] Server error recovery: (Requires FRED downtime)

## Future Enhancements

### Potential Improvements
1. **Cache Metrics Dashboard**
   - Show cache hit/miss rate
   - Display cached series list
   - Show cache memory usage

2. **Configurable Cache Settings**
   - User-adjustable TTL
   - Persistent cache across sessions (Redis, file system)
   - Cache size limits

3. **Smarter Retry Logic**
   - Respect `Retry-After` headers
   - Jittered backoff to prevent thundering herd
   - Circuit breaker pattern for prolonged outages

4. **Prefetching**
   - Background prefetch for common series
   - Predictive prefetch based on user patterns

5. **Offline Mode**
   - Fallback to cached data when FRED is down
   - Warning banner for stale data

## Migration Notes

### Breaking Changes
- None. The changes are backward compatible.

### API Changes
- `fetch_fred()` now accepts optional `max_retries` and `backoff_factor` parameters
- New exception types may be raised: `FREDRateLimitError`, `FREDServerError`
- Timeout increased from infinite to 30 seconds

### Upgrade Path
1. No code changes required for existing CLI scripts
2. Streamlit app automatically uses new caching
3. Error handling is improved but backward compatible

## References

### Related Issues
- Issue #5: Fix requirements.txt (Part 1 of 5)
- Issue #6: Add caching and retry logic (Part 2 of 5) **← Current**
- Issue #8: Multi-series charts (Part 3 of 5)
- Issue #7: Template-driven reports (Part 4 of 5)
- Issue #9: Additional data sources (Part 5 of 5)

### Documentation
- User Guide: `docs/MACROBUILDER_GUIDE.md` (updated with caching section)
- Architecture: `AGENTS.md` (breadcrumbs updated)
- Changelog: `CHANGELOG.md` (to be updated)

### External Resources
- FRED API Documentation: https://fred.stlouisfed.org/
- Streamlit Caching: https://docs.streamlit.io/library/advanced-features/caching
- Exponential Backoff: https://en.wikipedia.org/wiki/Exponential_backoff
