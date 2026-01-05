# Visual Documentation: Caching Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        MacroEconDataArchive                     │
│                        Caching Architecture                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   User       │
│  Browser     │
└──────┬───────┘
       │
       │ HTTP Request
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Streamlit Application                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ streamlit_app.py                                           │ │
│  │                                                             │ │
│  │  ┌─────────────────────────────────────────────┐          │ │
│  │  │ fetch_fred_cached()                         │          │ │
│  │  │ @st.cache_data(ttl=3600)                   │          │ │
│  │  │                                             │          │ │
│  │  │ Cache Key: (series_ids, start_date)        │          │ │
│  │  └─────────────┬───────────────────────────────┘          │ │
│  │                │                                           │ │
│  │                │ Cache Miss?                               │ │
│  │                ▼                                           │ │
│  │  ┌─────────────────────────────────────────────┐          │ │
│  │  │ fetch_fred()  [macro_utils.py]             │          │ │
│  │  │                                             │          │ │
│  │  │ • Retry Logic (3 attempts)                 │          │ │
│  │  │ • Exponential Backoff (1s, 2s, 4s)        │          │ │
│  │  │ • HTTP Timeout (30s)                       │          │ │
│  │  │ • Custom Exceptions                        │          │ │
│  │  └─────────────┬───────────────────────────────┘          │ │
│  └────────────────┼────────────────────────────────────────────┘ │
└───────────────────┼──────────────────────────────────────────────┘
                    │
                    │ HTTPS GET
                    ▼
     ┌──────────────────────────────────┐
     │   FRED API                       │
     │   fred.stlouisfed.org/           │
     │   graph/fredgraph.csv            │
     └──────────────────────────────────┘
```

## Request Flow Diagram

### Scenario 1: Cache Hit (Fast Path)

```
User clicks "Add Chart"
       │
       ▼
fetch_fred_cached(["GDPC1"], "2020-01-01")
       │
       ▼
  Check Cache
       │
       ├─── Cache HIT ✓
       │         │
       │         ▼
       │   Return DataFrame
       │   (< 10 ms)
       │         │
       │         ▼
       │   Build Chart
       │         │
       │         ▼
       └─── Display to User
```

### Scenario 2: Cache Miss (Slow Path)

```
User clicks "Add Chart"
       │
       ▼
fetch_fred_cached(["UNRATE"], "2020-01-01")
       │
       ▼
  Check Cache
       │
       ├─── Cache MISS ✗
       │         │
       │         ▼
       │   fetch_fred(["UNRATE"], "2020-01-01")
       │         │
       │         ├──► Attempt 1 ──► FRED API ──► Response
       │         │                     (1-2 sec)
       │         ▼
       │   Store in Cache
       │         │
       │         ▼
       │   Return DataFrame
       │         │
       │         ▼
       │   Build Chart
       │         │
       │         ▼
       └─── Display to User
```

## Retry Logic Flow

```
fetch_fred() called
       │
       ▼
┌─────────────────┐
│ Attempt 1       │
│ (immediate)     │
└────┬─────┬──────┘
     │     │
     │     └── Success (200) ──► Return Data ✓
     │
     ├── 403 Forbidden ──► Raise FREDRateLimitError ✗
     │
     └── 500 Server Error
            │
            ▼
     ┌─────────────────┐
     │ Wait 1 second   │
     │ (2^0)           │
     └────┬────────────┘
          │
          ▼
     ┌─────────────────┐
     │ Attempt 2       │
     └────┬─────┬──────┘
          │     │
          │     └── Success (200) ──► Return Data ✓
          │
          └── Still 500
                 │
                 ▼
          ┌─────────────────┐
          │ Wait 2 seconds  │
          │ (2^1)           │
          └────┬────────────┘
               │
               ▼
          ┌─────────────────┐
          │ Attempt 3       │
          └────┬─────┬──────┘
               │     │
               │     └── Success (200) ──► Return Data ✓
               │
               └── Still 500 ──► Raise FREDServerError ✗
```

## Cache Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    Cache Entry Lifecycle                     │
└─────────────────────────────────────────────────────────────┘

Time: 10:00 AM
Event: User loads chart with series ["GDPC1"]
       │
       ▼
   ┌────────────────┐
   │ Cache EMPTY    │  ← Initial state
   └───────┬────────┘
           │
           ├─► Fetch from FRED (2 seconds)
           │
           ▼
   ┌────────────────┐
   │ Cache FILLED   │  ← Data cached at 10:00 AM
   │ TTL: 1 hour    │
   │ Expires: 11:00 │
   └───────┬────────┘
           │
           ├─► 10:05 AM: User reloads → Cache HIT (fast)
           ├─► 10:30 AM: Another user  → Cache HIT (fast)
           ├─► 10:45 AM: Load template → Cache HIT (fast)
           │
           ▼
Time: 11:00 AM (1 hour later)
   ┌────────────────┐
   │ Cache EXPIRED  │  ← TTL reached
   └───────┬────────┘
           │
           └─► Next request → Fetch fresh data from FRED
```

## Performance Comparison

```
Without Caching:
┌─────────────────────────────────────────────────────────────┐
│ Load 10-chart report                                        │
├─────────────────────────────────────────────────────────────┤
│ Chart 1: Fetch GDP      [████████████████] 1.5s            │
│ Chart 2: Fetch CPI      [████████████████] 1.8s            │
│ Chart 3: Fetch UNRATE   [████████████████] 1.2s            │
│ Chart 4: Fetch PAYEMS   [████████████████] 2.1s            │
│ Chart 5: Fetch DGS10    [████████████████] 1.4s            │
│ Chart 6: Fetch UMCSENT  [████████████████] 1.9s            │
│ Chart 7: Fetch CPIAUCSL [████████████████] 1.6s            │
│ Chart 8: Fetch GDPC1    [████████████████] 1.7s            │
│ Chart 9: Fetch UNRATE   [████████████████] 1.3s            │
│ Chart 10: Fetch M2SL    [████████████████] 1.5s            │
├─────────────────────────────────────────────────────────────┤
│ TOTAL TIME: ~16 seconds                                     │
└─────────────────────────────────────────────────────────────┘

With Caching (second load):
┌─────────────────────────────────────────────────────────────┐
│ Load 10-chart report                                        │
├─────────────────────────────────────────────────────────────┤
│ Chart 1-10: All cached  [█] 0.05s                          │
├─────────────────────────────────────────────────────────────┤
│ TOTAL TIME: ~0.05 seconds (320x faster!)                    │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling State Machine

```
                        ┌──────────────┐
                        │ Request Data │
                        └──────┬───────┘
                               │
                               ▼
                      ┌────────────────┐
                      │  HTTP Request  │
                      └──┬──────┬──────┘
                         │      │
        ┌────────────────┘      └────────────────┐
        │                                        │
        ▼                                        ▼
┌──────────────┐                        ┌──────────────┐
│  200 OK      │                        │ Error Code   │
└──────┬───────┘                        └──────┬───────┘
       │                                       │
       │                           ┌───────────┼───────────┐
       │                           │           │           │
       │                           ▼           ▼           ▼
       │                    ┌───────────┐ ┌────────┐ ┌──────────┐
       │                    │ 403 Rate  │ │ 5xx    │ │ Network  │
       │                    │ Limit     │ │ Server │ │ Error    │
       │                    └─────┬─────┘ └───┬────┘ └────┬─────┘
       │                          │           │           │
       │                          │           ├───────────┤
       │                          │           │ Retries   │
       │                          │           │ < Max?    │
       │                          │           └───┬───┬───┘
       │                          │               │   │
       │                          │               │   └─► Retry
       │                          │               │      (with
       │                          │               │       backoff)
       │                          │               ▼
       │                          │         ┌──────────┐
       │                          └────────►│  Raise   │
       │                                    │Exception │
       │                                    └──────────┘
       ▼
┌────────────┐
│ Return     │
│ DataFrame  │
└────────────┘
```

## Multi-User Caching Benefit

```
Office with 5 users, all loading same template:

User 1 (10:00 AM):
[████████████████] Load template (15 seconds - FRED fetch)
✓ Data cached

User 2 (10:02 AM):
[█] Load template (0.1 seconds - cache hit!)

User 3 (10:05 AM):
[█] Load template (0.1 seconds - cache hit!)

User 4 (10:10 AM):
[█] Load template (0.1 seconds - cache hit!)

User 5 (10:15 AM):
[█] Load template (0.1 seconds - cache hit!)

Total time saved: 60 seconds (4 users × 15s)
Cache efficiency: 80% (4/5 requests from cache)
```

## Summary Metrics

| Metric | Without Cache | With Cache | Improvement |
|--------|--------------|------------|-------------|
| First load | 1-2 sec/series | 1-2 sec/series | 0% (cache miss) |
| Subsequent loads | 1-2 sec/series | 10-100 ms | **10-200x faster** |
| API calls (10 charts) | 10 calls | 1 call (first) + 0 (cached) | **90% reduction** |
| Memory usage | Minimal | ~10 MB (100 series) | Acceptable |
| User experience | Slow | Fast | **Significantly better** |

## Key Takeaways

1. **Caching is automatic** - no user action required
2. **1-hour TTL** balances freshness and performance
3. **Retry logic** handles transient errors gracefully
4. **Exponential backoff** prevents overwhelming FRED servers
5. **Custom exceptions** provide clear error messages
6. **Shared cache** benefits all users in multi-user scenarios
7. **One-click clear** for manual refresh when needed

For more details, see [DEVELOPER_NOTES_CACHING.md](DEVELOPER_NOTES_CACHING.md) and [QUICK_REFERENCE_CACHING.md](QUICK_REFERENCE_CACHING.md).
