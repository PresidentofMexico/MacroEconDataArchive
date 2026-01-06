# UI Changes - Visual Guide

This document illustrates the user-facing changes made to resolve breaking changes.

## Change 1: Template Loading - Replace vs Append

### Before (Issue)
```
When existing charts are present:
┌─────────────────────────────┐
│ Load Template Button        │  ← Always appends, causing duplicates
└─────────────────────────────┘
```
**Problem:** Repeatedly clicking "Load Template" would create duplicate charts

### After (Fixed)
```
When NO existing charts:
┌─────────────────────────────┐
│ 📥 Load Template            │  ← Single button
└─────────────────────────────┘

When existing charts present:
┌─────────────┬───────────────┐
│ 📥 Replace  │  ➕ Append    │  ← Two clear options
└─────────────┴───────────────┘
```
**Solution:** Users explicitly choose Replace (clear all and load) or Append (add to existing)

---

## Change 2: Missing Series Warnings

### Before (Silent Failure)
```
Chart Title: GDP and CPI Comparison
[Chart shows only GDP line]
```
**Problem:** Missing series silently omitted, chart looks incomplete

### After (Explicit Warning)
```
⚠️ Chart 'GDP and CPI Comparison': Missing data columns for series: CPI. 
   These series will not appear in the chart.

Chart Title: GDP and CPI Comparison
[Chart shows only GDP line]
```
**Solution:** User immediately knows why a series is missing

---

## Change 3: Cache Behavior Visualization

### Before (Order-Dependent Caching)
```
Request A: ["GDPC1", "PCEC96"]  → Cache Entry 1
Request B: ["PCEC96", "GDPC1"]  → Cache Entry 2 (duplicate!)
                                  ↳ Wastes cache space
```

### After (Order-Independent Caching)
```
Request A: ["GDPC1", "PCEC96"]  → sorted → ["GDPC1", "PCEC96"] → Cache Entry 1
Request B: ["PCEC96", "GDPC1"]  → sorted → ["GDPC1", "PCEC96"] → Cache Entry 1 ✓
                                             ↳ Cache hit!
```
**Impact:** Better cache efficiency, fewer redundant FRED API calls

---

## Change 4: Enhanced Error Messages

### FRED Data Fetch Errors

**Before:**
```
ValueError: Unexpected FRED response for series 'CPIAUCSL': missing 'CPIAUCSL' column
```

**After:**
```
Option 1 (Fallback succeeds):
⚠️ Warning: FRED response for 'CPIAUCSL' missing expected column, 
   using 'value' instead. This may indicate a FRED API change.
   
Option 2 (No fallback available):
ValueError: Unexpected FRED response for series 'CPIAUCSL': missing 'CPIAUCSL' column 
and no numeric fallback columns found. Available columns: ['DATE', 'notes']
```

### PDF Export Errors

**Before:**
```
Exception: write_image error
```

**After:**
```
Option 1 (Kaleido-related):
ImportError: Kaleido is required for PDF export but not properly installed. 
Please reinstall with: pip install -U kaleido
Original error: kaleido not found

Option 2 (Other errors):
RuntimeError: Failed to save chart as PNG for PDF export. 
This may be due to missing system dependencies (e.g., chromium). 
Error: Permission denied
```

---

## Technical Implementation Details

### Missing Series Warning (streamlit_app.py)
```python
# Added tracking of missing series
missing_series = []
for series_info in chart_config.series:
    if series_info.series_id in chart_config.data.columns:
        fig.add_trace(...)
    else:
        missing_series.append(series_info.series_id)  # Track missing

# Display warning if any series missing
if missing_series:
    st.warning(f"⚠️ Chart '{chart_config.title}': Missing data columns...")
```

### Cache Canonicalization (streamlit_app.py)
```python
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fred_cached(series_ids: List[str], start: str) -> pd.DataFrame:
    # KEY CHANGE: Sort series IDs for consistent cache keys
    canonical_series_ids = sorted(series_ids)
    return fetch_fred(canonical_series_ids, start=start)
```

### Template Load Control (streamlit_app.py)
```python
# Function signature change
def load_template_into_report(template_path: Path, replace_existing: bool = False):
    if replace_existing or not st.session_state.charts:
        st.session_state.charts = charts  # Replace
    else:
        st.session_state.charts.extend(charts)  # Append

# UI implementation
if st.session_state.charts:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📥 Replace", ...):
            load_template_into_report(path, replace_existing=True)
    with col2:
        if st.button("➕ Append", ...):
            load_template_into_report(path, replace_existing=False)
```

### FRED Fallback Logic (macro_utils.py)
```python
if sid not in raw.columns:
    # NEW: Fallback to first numeric column
    numeric_cols = [col for col in raw.columns if col != date_col and 
                   pd.api.types.is_numeric_dtype(raw[col])]
    if numeric_cols:
        actual_col = numeric_cols[0]
        warnings.warn(f"FRED response for '{sid}' missing expected column...")
        raw[sid] = raw[actual_col]  # Rename for consistency
    else:
        # Enhanced error message with available columns
        raise ValueError(f"... Available columns: {list(raw.columns)}")
```

---

## User Experience Impact Summary

| Change | Before | After | User Benefit |
|--------|--------|-------|--------------|
| Template Loading | Always appends, creates duplicates | Explicit Replace/Append choice | No accidental duplicates |
| Missing Series | Silent omission | Warning message | Clear feedback on incomplete charts |
| Cache Behavior | Order-dependent, fragmented | Order-independent, efficient | Faster load times |
| FRED Errors | Generic error | Specific fallback or detailed error | Better troubleshooting |
| PDF Export Errors | Vague message | Actionable guidance | Clear next steps |

---

## Backward Compatibility

✅ All changes are backward compatible:
- Existing single-series charts still work
- Legacy template format (with `series_id`/`series_label`) still supported
- No breaking changes to API or data structures
- Enhanced error handling gracefully degrades

---

## Testing

All changes validated with comprehensive test suite:
```
✓ PASS: Empty Series List Safety
✓ PASS: Series Order Cache Consistency
✓ PASS: Template Schema Validation
✓ PASS: Missing Column Handling
✓ PASS: FRED Column Name Strictness
✓ PASS: Kaleido Error Detection
✓ PASS: Analysis Generation Safety
```

Total: 7/7 tests passed
