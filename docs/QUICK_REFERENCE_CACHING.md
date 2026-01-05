# Quick Reference: Caching

## What is Caching?

Caching stores fetched data temporarily so repeated requests return instantly without re-downloading from FRED. This makes the app faster and reduces API usage.

## Benefits

- ⚡ **Faster loading**: Cached data loads in milliseconds vs seconds
- 🔄 **Reduced API calls**: Fewer requests to FRED servers
- 📊 **Better UX**: Smoother navigation between charts
- 🛡️ **Rate limit protection**: Less likely to hit FRED usage limits

## How It Works

### Cache Duration
- Data is cached for **1 hour (3600 seconds)**
- After 1 hour, data is automatically refreshed from FRED
- Manual refresh available anytime via "Clear Data Cache" button

### What Gets Cached
- FRED series data (raw time series)
- Applies to all chart types
- Shared across all Streamlit sessions

### What Doesn't Get Cached
- Chart transformations (yoy, qoq_saar) - computed on-the-fly
- AI-generated narratives
- Chart configurations
- User settings

## Using the Cache

### Automatic Caching

Caching happens automatically when you:
1. Load a template
2. Add a chart manually
3. Refresh the page

**No action needed** - it just works! 🎉

### Manual Cache Clear

Clear the cache when you need fresh data:

1. Open Streamlit app
2. Go to sidebar
3. Click **Settings** section
4. Click **"🔄 Clear Data Cache"** button
5. Data will be refreshed on next fetch

### When to Clear Cache

Clear the cache when:
- ✅ FRED releases new data (usually monthly/quarterly)
- ✅ You need the absolute latest data
- ✅ You encounter stale data
- ✅ Testing data updates

**No need to clear** for:
- ❌ Changing chart types
- ❌ Generating AI narratives
- ❌ Reordering charts
- ❌ Switching templates

## Troubleshooting

### "Stale Data" Issue

**Symptom**: Chart shows old data

**Solution**:
1. Click "Clear Data Cache"
2. Reload the chart

### "Rate Limit Exceeded" Error

**Error message**: `FRED rate limit exceeded. Please wait...`

**What it means**: Too many requests in short time

**Solution**:
1. Wait 5-10 minutes
2. The app will cache data to prevent future rate limits
3. Use templates instead of adding charts one-by-one

### Slow Loading After Cache Clear

**Symptom**: First load after clearing cache is slow

**Expected behavior**: This is normal!
- First fetch: 1-2 seconds per series (from FRED)
- Subsequent fetches: < 100ms (from cache)

## Performance Tips

### Maximize Cache Benefits

1. **Load templates**: Templates fetch all data at once
2. **Avoid excessive refreshing**: Data updates infrequently (monthly/quarterly)
3. **Reuse charts**: Edit rather than delete/recreate
4. **Share reports**: Multiple users benefit from shared cache

### Multi-User Scenarios

**Office/Team Use:**
- First user loads template → data cached
- Other users get instant loading
- Cache shared across all users
- Huge time savings for teams!

## Technical Details

### Cache Key

Cache key includes:
- Series IDs (e.g., ["GDPC1", "UNRATE"])
- Start date (e.g., "2020-01-01")

**Same series + same start date = Cache hit ✅**

### Cache Storage

- Stored in memory (RAM)
- Not persistent (cleared on app restart)
- Typical size: 1-10 MB for 10-100 series

### Cache Expiration

```
Fetch time: 10:00 AM
Cache expires: 11:00 AM (1 hour later)
Next fetch after 11:00 AM: Fresh data from FRED
```

## Command Reference

### CLI (No Caching)

CLI doesn't use caching - each run fetches fresh data:

```bash
python generate_macro_report.py --template core_macro --out report.pdf
```

**Why no CLI caching?**
- CLI typically run once (not interactive)
- Reports usually need latest data
- No performance impact (run in background)

### Streamlit (With Caching)

Streamlit automatically caches:

```bash
streamlit run app.py
```

All fetches are cached automatically!

## FAQ

**Q: How do I know if cache is working?**

A: Second load of same data is instant (< 100ms)

**Q: Can I disable caching?**

A: Not recommended, but you can clear cache before each fetch

**Q: Does caching work offline?**

A: No, initial fetch requires internet. Cached data persists for 1 hour.

**Q: Is cached data shared between users?**

A: Yes, when using same Streamlit instance

**Q: What happens if FRED is down?**

A: Cached data still accessible. New fetches fail after 3 retries with exponential backoff.

**Q: How much faster is caching?**

A: 10-100x faster (1-2s → 10-100ms)

**Q: Can I change cache duration?**

A: Yes, edit `streamlit_app.py` and modify `@st.cache_data(ttl=3600)` to desired seconds

**Q: Does cache persist after closing browser?**

A: Yes, as long as Streamlit server keeps running

**Q: What if I need real-time data?**

A: Use 5-minute TTL or clear cache frequently

## Summary

- **Automatic**: Caching works without any user action
- **Smart**: 1-hour TTL balances freshness and performance
- **Fast**: 10-100x speed improvement
- **Simple**: One-click cache clear when needed
- **Reliable**: Retry logic handles transient errors

**Bottom line**: Just use the app normally and enjoy the speed! 🚀

For technical details, see [DEVELOPER_NOTES_CACHING.md](DEVELOPER_NOTES_CACHING.md).
