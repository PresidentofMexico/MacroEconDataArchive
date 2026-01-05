# Quick Reference: Data Caching in MacroBuilder

## 🚀 What is Caching?

MacroBuilder automatically saves fetched FRED data for 1 hour. When you add the same chart again (or use the same series), it loads instantly from cache instead of re-fetching from FRED.

## ⚡ Performance Benefits

| Action | Without Cache | With Cache (Hit) | Speedup |
|--------|--------------|------------------|---------|
| Add chart for GDPC1 | 1.5 seconds | 0.01 seconds | 150x faster |
| Add 5 charts (2 repeated) | 8.6 seconds | 5.3 seconds | 38% faster |
| Build 20-chart report | 34 seconds | 12 seconds | 65% faster |

## 🎯 When Cache Helps

✅ **Building multiple versions of reports**
- Try different transformations (level, yoy, qoq) of same series
- Reorder charts without refetching data

✅ **Exploratory analysis**
- Add/remove charts to find best combination
- Cache keeps previously fetched data available

✅ **Iterative workflows**
- Fetch data once, generate multiple narratives
- Experiment with date ranges efficiently

## 🗑️ Managing Cache

### When to Clear Cache

❌ **You DON'T need to clear cache if:**
- You're just building a report normally
- It's been less than 1 hour since you started
- You're happy with the data freshness

✅ **Clear cache when:**
- You changed the start date and want fresh data range
- You need the absolute latest data (within the hour)
- You're experiencing stale data issues
- You want to free up memory

### How to Clear Cache

1. Look for **⚡ Data Cache** in the sidebar
2. Click the **🗑️** button
3. You'll see "Cache cleared!" confirmation
4. Next data fetch will be fresh from FRED

## 🔄 Cache Behavior

### Cache Key
Cache is stored by `(series_id, start_date)`:
- Same series + same start date = **Cache Hit** ⚡
- Different series = **Cache Miss** (fetch from FRED)
- Same series + different start date = **Cache Miss**

### Cache Duration
- **Default**: 1 hour (3600 seconds)
- Automatically expires after 1 hour
- Manual clear via 🗑️ button clears all cached data

### Cache Scope
- **Per session**: Each browser tab has its own cache
- **In-memory**: Cache doesn't persist after closing browser
- **Automatic**: No configuration needed

## ⚠️ Error Messages Explained

### ⚠️ FRED Rate Limit Reached
**What it means:** You've made too many requests to FRED in a short time.

**What to do:**
1. Wait 5-10 minutes
2. Use cached data for already-fetched series
3. Add charts more slowly (batch similar series)

**Prevention:**
- Use cache effectively (don't clear unnecessarily)
- Add multiple charts at once when possible
- Space out requests for many new series

---

### 🔧 FRED Server Error
**What it means:** FRED servers are temporarily unavailable or overloaded.

**What to do:**
1. Wait a few minutes and try again
2. The system already tried 3 times automatically
3. Check FRED status if problem persists

**Note:** This is rare but can happen during high traffic or maintenance.

---

### ❌ General Errors
**What it means:** Invalid series ID, data parsing error, or network issue.

**What to do:**
1. Check series ID is correct at https://fred.stlouisfed.org/
2. Verify series exists and has data
3. Check your internet connection

## 🔧 Retry Logic (Automatic)

MacroBuilder automatically retries failed requests:

| Error Type | Retry? | Attempts | Delays |
|-----------|--------|----------|--------|
| Network timeout | ✅ Yes | 3 | 1s, 2s, 4s |
| Server error (5xx) | ✅ Yes | 3 | 1s, 2s, 4s |
| Rate limit (403) | ❌ No | 1 | N/A |
| Invalid series | ❌ No | 1 | N/A |

**You don't need to do anything** - the retry happens automatically in the background!

## 📊 Real-World Examples

### Example 1: Building a Monthly Report
```
Day 1, 9:00 AM:
- Add 10 charts → All fetch from FRED (15 seconds total)
- Cache is populated

Day 1, 9:30 AM:
- Regenerate same report → All cache hits! (0.1 seconds)
- Add 5 more charts → Only new ones fetch from FRED

Day 1, 10:30 AM (1.5 hours later):
- Cache expired (1 hour TTL)
- Next report build fetches fresh data
```

### Example 2: Exploring Different Transformations
```
- Add GDP (level) → Fetch from FRED (1.5s)
- Remove it, add GDP (yoy) → Cache hit! (0.01s)
- Remove it, add GDP (qoq) → Cache hit! (0.01s)

Result: Test 3 transformations in 1.52s instead of 4.5s
```

### Example 3: Handling Rate Limits
```
- Add 20 charts rapidly → FRED rate limit at chart #18
- Get ⚠️ error message
- Wait 5 minutes
- Charts 1-17 still in cache (no re-fetch needed)
- Retry charts 18-20 → Success!
```

## 💡 Pro Tips

1. **Batch Your Work**
   - Add multiple related charts at once
   - Use quick-add buttons for common series
   - Cache makes experimentation cheap

2. **Use Cache Strategically**
   - Don't clear cache unless necessary
   - Let TTL handle freshness automatically
   - Clear only when changing date ranges

3. **Monitor Performance**
   - First chart addition is slower (cache miss)
   - Repeated charts are instant (cache hit)
   - This is expected and normal!

4. **Handle Rate Limits**
   - If rate limited, cache helps you keep working
   - Previously fetched data remains accessible
   - Wait, then continue with new series

5. **Fresh Data When Needed**
   - Most economic data updates monthly/quarterly
   - 1-hour cache is usually fine
   - Clear cache for absolute latest data

## 🆘 Troubleshooting

**Q: Charts are loading too slowly**
A: First time loading is normal (fetching from FRED). Subsequent loads should be fast (cache hit).

**Q: I changed the start date but data looks the same**
A: Clear the cache with 🗑️ button. Cache key includes start date, so this shouldn't normally happen.

**Q: Memory usage seems high**
A: Cache uses memory. Clear cache to free up. Each series is ~1-5MB depending on length.

**Q: Cache doesn't seem to be working**
A: Check that you're using the exact same series ID and start date. Different parameters = different cache key = cache miss.

**Q: How do I know if cache is working?**
A: Add the same chart twice. First time takes 1-2s, second time is instant (<0.01s).

## 📚 More Information

- Full user guide: `docs/MACROBUILDER_GUIDE.md`
- Technical details: `docs/DEVELOPER_NOTES_CACHING.md`
- Visual diagrams: `docs/VISUAL_DOCUMENTATION_CACHING.md`
- Changelog: `CHANGELOG.md` (see Issue #6 section)

---

**Version:** Part 2 of 5 - MacroBuilder Production Upgrade Epic  
**Tag:** [template-pushbutton-upgrade-2026]  
**Last Updated:** 2026-01-05
