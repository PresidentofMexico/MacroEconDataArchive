# Visual Documentation: Caching and Retry Features

## Cache Control UI in Sidebar

```
┌─────────────────────────────────────────┐
│ 📊 MacroBuilder                         │
├─────────────────────────────────────────┤
│ Report Settings                         │
│ ┌─────────────────────────────────────┐ │
│ │ Report Title                        │ │
│ │ [Macro Economic Data Archive      ] │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Start Date (YYYY-MM-DD)             │ │
│ │ [2010-01-01                       ] │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ AI Settings                             │
│ ┌─────────────────────────────────────┐ │
│ │ OpenAI API Key                      │ │
│ │ [••••••••••••••••••••••••••••••••] │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│ ⚡ Data Cache            🗑️            │  ← NEW!
│ Cache improves performance by           │
│ storing fetched data                    │
├─────────────────────────────────────────┤
│ Add New Chart                           │
│ ...                                     │
└─────────────────────────────────────────┘
```

**New Feature Highlights:**
- ⚡ Data Cache section added between AI Settings and Chart Builder
- 🗑️ Clear button for manual cache invalidation
- Informative caption explaining cache purpose
- Clicking 🗑️ clears all cached data and shows success message

---

## Error Message Examples

### 1. Rate Limit Error (403)

```
┌─────────────────────────────────────────────────────────┐
│ ⚠️ FRED Rate Limit Reached                              │
│                                                          │
│ FRED rate limit exceeded for series 'GDPC1'. Please    │
│ wait a few minutes before trying again.                 │
│                                                          │
│ Tip: Try again in a few minutes, or use the cache       │
│ clear button if you've recently fetched this data.      │
└─────────────────────────────────────────────────────────┘
```

**Behavior:**
- Shows immediately without retry attempts
- Suggests specific wait time
- Mentions cache as workaround
- Red/orange warning styling in Streamlit

---

### 2. Server Error (5xx)

```
┌─────────────────────────────────────────────────────────┐
│ 🔧 FRED Server Error                                     │
│                                                          │
│ FRED server error (503) for series 'UNRATE' after 3    │
│ attempts.                                                │
│                                                          │
│ The FRED server may be temporarily unavailable. Please  │
│ try again later.                                         │
└─────────────────────────────────────────────────────────┘
```

**Behavior:**
- Only shows after 3 retry attempts fail
- Indicates the system tried multiple times
- Suggests temporary server issue
- Blue/info styling in Streamlit

---

### 3. General Error

```
┌─────────────────────────────────────────────────────────┐
│ ❌ Error adding chart: Failed to fetch data for        │
│ INVALID_ID: Unexpected FRED response for series        │
│ 'INVALID_ID': missing 'INVALID_ID' column              │
└─────────────────────────────────────────────────────────┘
```

**Behavior:**
- Shows for parsing errors, invalid series IDs, etc.
- Provides specific error details for debugging
- Red error styling in Streamlit

---

## Retry Logic Visualization

### Successful Request (No Retry Needed)

```
┌────────┐           ┌────────┐
│ Client │           │  FRED  │
└───┬────┘           └───┬────┘
    │                    │
    │  GET /GDPC1        │
    ├───────────────────>│
    │                    │
    │  200 OK + Data     │
    │<───────────────────┤
    │                    │
    ▼                    ▼
 Success!            
 (0.5-2.0s)
```

---

### Server Error with Retry

```
┌────────┐           ┌────────┐
│ Client │           │  FRED  │
└───┬────┘           └───┬────┘
    │                    │
    │  GET /UNRATE       │
    ├───────────────────>│
    │                    │
    │  503 Server Error  │
    │<───────────────────┤
    │                    │
    │  [wait 1s]         │
    │                    │
    │  GET /UNRATE       │
    ├───────────────────>│
    │                    │
    │  503 Server Error  │
    │<───────────────────┤
    │                    │
    │  [wait 2s]         │
    │                    │
    │  GET /UNRATE       │
    ├───────────────────>│
    │                    │
    │  200 OK + Data     │
    │<───────────────────┤
    │                    │
    ▼                    ▼
 Success!
 (3.5-5.0s with retries)
```

**Exponential Backoff:**
- Attempt 1: Immediate
- Attempt 2: Wait 1 second (2^0)
- Attempt 3: Wait 2 seconds (2^1)
- Total: 3 attempts over ~3 seconds

---

### Rate Limit (No Retry)

```
┌────────┐           ┌────────┐
│ Client │           │  FRED  │
└───┬────┘           └───┬────┘
    │                    │
    │  GET /CPIAUCSL     │
    ├───────────────────>│
    │                    │
    │  403 Forbidden     │
    │<───────────────────┤
    │                    │
    ▼                    ▼
 Immediate Error!
 Show friendly message
 (No retry - respect rate limit)
```

---

## Caching Behavior Diagram

### Cache Miss (First Request)

```
User Action: Add chart for "GDPC1"
      │
      ▼
┌──────────────────────────────────┐
│ fetch_fred_cached("GDPC1", "2010")│ ← Cache key: (GDPC1, 2010-01-01)
└───────────┬──────────────────────┘
            │
            ▼
    [Cache Lookup]
            │
            ├─> Cache Miss! ❌
            │
            ▼
┌──────────────────────────────┐
│ fetch_fred(["GDPC1"], "2010")│ ← Actual FRED API call
└───────────┬──────────────────┘
            │
            ▼
      [FRED API]
      0.5-2.0 seconds
            │
            ▼
    [Store in Cache] ✅
            │
            ▼
    Return data to user
```

---

### Cache Hit (Subsequent Request)

```
User Action: Add chart for "GDPC1" again
      │
      ▼
┌──────────────────────────────────┐
│ fetch_fred_cached("GDPC1", "2010")│ ← Same cache key
└───────────┬──────────────────────┘
            │
            ▼
    [Cache Lookup]
            │
            ├─> Cache Hit! ✅
            │
            ▼
    Return cached data
    <0.01 seconds
    
🚀 50-200x faster!
```

---

### Cache Invalidation Scenarios

#### 1. TTL Expiration
```
Time: 0:00    - User adds "GDPC1" chart → Cache stored
Time: 0:59    - User adds "GDPC1" again → Cache hit! ✅
Time: 1:01    - User adds "GDPC1" again → Cache expired, fetch fresh ❌
```

#### 2. Parameter Change
```
Request 1: fetch_fred_cached("GDPC1", "2010-01-01") → Cache key: (GDPC1, 2010-01-01)
Request 2: fetch_fred_cached("GDPC1", "2010-01-01") → Same key, cache hit! ✅
Request 3: fetch_fred_cached("GDPC1", "2000-01-01") → Different key, cache miss! ❌
```

#### 3. Manual Clear
```
User clicks 🗑️ button → st.cache_data.clear() → All cached data removed
Next request → Cache miss, fresh fetch ❌
```

---

## Performance Comparison

### Without Caching (Legacy Behavior)

```
Add Chart 1 (GDPC1)   : 1.5s  ████████████████
Add Chart 2 (UNRATE)  : 1.8s  ██████████████████
Add Chart 3 (GDPC1)   : 1.6s  ████████████████   ← Same series, still slow
Add Chart 4 (CPIAUCSL): 2.0s  ████████████████████
Add Chart 5 (GDPC1)   : 1.7s  █████████████████  ← Same series, still slow

Total Time: 8.6 seconds
```

---

### With Caching (New Behavior)

```
Add Chart 1 (GDPC1)   : 1.5s  ████████████████   ← Cache miss
Add Chart 2 (UNRATE)  : 1.8s  ██████████████████ ← Cache miss
Add Chart 3 (GDPC1)   : 0.01s █                  ← Cache hit! ⚡
Add Chart 4 (CPIAUCSL): 2.0s  ████████████████████ ← Cache miss
Add Chart 5 (GDPC1)   : 0.01s █                  ← Cache hit! ⚡

Total Time: 5.32 seconds (38% faster!)
```

With more repeated series, savings increase dramatically!

---

## Error Flow Decision Tree

```
                    [Make FRED Request]
                            │
                            ▼
                    ┌───────────────┐
                    │ Response Code │
                    └───────┬───────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
        ┌───────┐      ┌───────┐      ┌────────┐
        │  403  │      │  5xx  │      │  2xx   │
        │ Rate  │      │Server │      │Success │
        │ Limit │      │ Error │      │        │
        └───┬───┘      └───┬───┘      └───┬────┘
            │              │              │
            ▼              │              ▼
    [Don't Retry]          │        [Parse Data]
            │              │              │
            ▼              │              ▼
   Show ⚠️ Error          │         [Return]
    (Friendly)            │
                          │
                          ▼
                 [Attempt < Max?]
                          │
                    ┌─────┴─────┐
                    │           │
                Yes ▼           │ No
            [Wait Backoff]      │
                    │           │
                    ▼           ▼
               [Retry]    Show 🔧 Error
                              (Friendly)
```

---

## Summary

### What Changed
1. ✅ Automatic caching (1-hour TTL)
2. ✅ Smart retry logic (3 attempts, exponential backoff)
3. ✅ Request timeout (30 seconds)
4. ✅ Friendly error messages (⚠️, 🔧, ❌)
5. ✅ Cache control UI (🗑️ button)

### User Benefits
- 🚀 50-200x faster for repeated series
- 🔧 Auto-recovery from transient errors
- 💬 Clear, actionable error messages
- 🎯 Better reliability for large reports

### Developer Benefits
- 📊 Comprehensive test coverage
- 📚 Detailed technical documentation
- 🔍 Clear error types for debugging
- 🏗️ Production-ready architecture
