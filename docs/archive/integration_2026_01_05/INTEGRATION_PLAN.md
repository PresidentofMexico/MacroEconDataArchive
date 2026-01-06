# Integration Plan for PRs #10-#13

## Executive Summary

This document outlines the comprehensive plan to integrate four parallel pull requests (#10, #11, #12, #13) from the `[template-pushbutton-upgrade-2026]` epic into a single coherent codebase.

## PRs to Integrate

| PR # | Title | Lines Changed | Key Features |
|------|-------|---------------|--------------|
| #10 | Fix requirements.txt / installability + smoke tests + docs | +1041, -20 | Complete requirements.txt, smoke tests, error handling |
| #11 | Template-driven report generation | +1346, -8 | Template system, one-click reports |
| #12 | Streamlit caching + FRED reliability | +1880, -33 | Data caching, retry logic, exponential backoff |
| #13 | Multi-series charts | +290, -55 | Multiple series per chart |

**Total**: ~4,550 lines of additions across 4 PRs

## Integration Status

### ✅ Phase 1: COMPLETED
- requirements.txt updated with all 8 dependencies
- test_cli_smoke.py created
- Integration roadmap documented

###  Phase 2: IN PROGRESS
Core file integration needed:

#### Critical Files with Conflicts

1. **AGENTS.md**
   - Conflict: All 4 PRs add different "Session 6" entries
   - Solution: Create single consolidated Session 6 referencing all 4 issues
   - Status: ⏳ Pending

2. **src/macro_econ_data_archive/streamlit_app.py**
   - Modified by ALL 4 PRs
   - PR #10: +37 lines (kale ido error handling)
   - PR #11: +180 lines (template loading)
   - PR #12: +51 lines (caching decorator, error handling)
   - PR #13: +137 lines (multi-series support, SeriesInfo dataclass)
   - Solution: Merge all changes sequentially, ensuring compatibility
   - Status: ⏳ Pending - MOST COMPLEX FILE

3. **src/macro_econ_data_archive/macro_utils.py**
   - PR #12: +97 lines, -29 lines (retry logic, custom exceptions)
   - Compatible with other PRs
   - Solution: Apply PR #12 changes directly
   - Status: ⏳ Pending

4. **src/macro_econ_data_archive/report_generator.py**
   - PR #11: +90 lines (template support)
   - Solution: Apply PR #11 changes directly
   - Status: ⏳ Pending

5. **README.md**
   - All PRs modify this file
   - Solution: Merge documentation sections
   - Status: ⏳ Pending

6. **CHANGELOG.md**
   - PR #12 adds extensive changelog
   - Solution: Create comprehensive entry for all 4 PRs
   - Status: ⏳ Pending

#### New Files to Create

**From PR #10:**
- `test_streamlit_smoke.py` (231 lines)
- `verify_installation.py` (129 lines)
- `docs/TESTING.md` (255 lines)

**From PR #11:**
- `config/templates/core_macro.json` (79 lines)
- `config/templates/inflation_deep_dive.json` (118 lines)
- `config/templates/labor_markets.json` (131 lines)
- `docs/TEMPLATE_GUIDE.md` (330 lines)
- `test_templates.py` (260 lines)

**From PR #12:**
- `docs/DEVELOPER_NOTES_CACHING.md` (283 lines)
- `docs/QUICK_REFERENCE_CACHING.md` (209 lines)
- `docs/VISUAL_DOCUMENTATION_CACHING.md` (365 lines)
- `ISSUE_6_SUMMARY.md` (417 lines)
- `test_caching_and_retry.py` (169 lines)

**From PR #13:**
- `test_multi_series.py` (if exists)

## Detailed Integration Steps

### Step 1: Apply PR #10 Changes (Foundation)
```bash
# Already done:
✓ requirements.txt 
✓ test_cli_smoke.py

# TODO:
- Create test_streamlit_smoke.py
- Create verify_installation.py
- Create docs/TESTING.md
- Update .gitignore
- Apply kaleido error handling to streamlit_app.py
```

### Step 2: Apply PR #12 Changes (Infrastructure)
```bash
# Highest priority - enables reliability
- Update macro_utils.py with retry logic
- Add FREDRateLimitError and FREDServerError exceptions
- Add caching wrapper to streamlit_app.py
- Create caching documentation files
- Create test_caching_and_retry.py
```

### Step 3: Apply PR #13 Changes (Data Model)
```bash
# Must come before templates (templates need multi-series support)
- Add SeriesInfo dataclass to streamlit_app.py
- Update ChartConfig to use List[SeriesInfo]
- Update create_plotly_chart() for multi-series
- Update prepare_data_summary() for multi-series
- Add multi-series UI components
- Update examples in macro_chart_spec.json
```

### Step 4: Apply PR #11 Changes (User Features)
```bash
# Templates leverage the updated data model
- Update report_generator.py with template functions
- Add template discovery and loading to streamlit_app.py
- Create template JSON files
- Create docs/TEMPLATE_GUIDE.md
- Create test_templates.py
```

### Step 5: Consolidate AGENTS.md
Create single Session 6 entry:

```markdown
### Session 6: Integrate PRs #10-#13 (template-pushbutton-upgrade-2026 Epic)
**Date:** 2026-01-05
**Branch:** copilot/integrate-pr10-13
**Status:** ✅ COMPLETED
**Agent:** copilot-swe-agent

**Summary:**
Integrated four parallel PRs implementing the complete template-pushbutton-upgrade-2026 epic:
- PR #10 (Issue #5): Requirements.txt + smoke tests + installability
- PR #12 (Issue #6): Caching + retry logic with exponential backoff
- PR #13 (Issue #8): Multi-series chart support
- PR #11 (Issue #7): Template-driven report generation

**Tasks Completed:**
- ✅ Updated requirements.txt with all 8 dependencies
- ✅ Created comprehensive smoke test suite (CLI + Streamlit)
- ✅ Added retry logic with exponential backoff (3 retries, 2x factor)
- ✅ Implemented data caching (1-hour TTL)
- ✅ Added multi-series chart support (Streamlit + CLI)
- ✅ Created template system with 3 built-in templates
- ✅ Integrated all features cohesively
- ✅ Comprehensive documentation (6 new docs)
- ✅ Full test coverage

**Features Integrated:**
1. **Push-Button Installability**: All dependencies in requirements.txt
2. **Data Caching**: 50-200x faster for repeated series
3. **Retry Logic**: Auto-recovery from transient errors
4. **Multi-Series Charts**: Compare multiple indicators on one chart
5. **Template System**: One-click report generation
6. **Error Handling**: User-friendly messages for all error types

**Files Modified:** (20+ files)
- Core: requirements.txt, macro_utils.py, report_generator.py, streamlit_app.py
- Tests: test_cli_smoke.py, test_streamlit_smoke.py, test_templates.py, test_caching_and_retry.py
- Config: config/templates/*.json, macro_chart_spec.json
- Docs: AGENTS.md, README.md, CHANGELOG.md, + 6 new docs

**Notes for Next Agent:**
- All 4 PRs successfully integrated
- All features work together cohesively
- Next step: Issue #9 (Part 5/5) - Additional data sources
- Consider: Cache metrics dashboard, persistent cache, prefetching

**Supersedes:**
- PR #10, PR #11, PR #12, PR #13
```

### Step 6: Update README.md
Merge all feature descriptions:
- Prerequisites and installation (PR #10)
- Multi-series examples (PR #13)
- Template usage (PR #11)
- Performance notes (PR #12)

### Step 7: Create Consolidated CHANGELOG.md Entry
Document all changes under "2026-01-05 - Integration of PRs #10-#13"

## Compatibility Matrix

| Feature | PR #10 | PR #11 | PR #12 | PR #13 | Compatible? |
|---------|--------|--------|--------|--------|-------------|
| requirements.txt | ✓ | - | - | - | ✅ Yes |
| Smoke tests | ✓ | - | - | - | ✅ Yes |
| Retry logic | - | - | ✓ | - | ✅ Yes |
| Caching | - | - | ✓ | - | ✅ Yes |
| Multi-series | - | - | - | ✓ | ✅ Yes |
| Templates | - | ✓ | - | - | ⚠️ Needs multi-series |
| Template + Multi-series | - | ✓ | - | ✓ | ✅ Yes (with integration) |
| Caching + Multi-series | - | - | ✓ | ✓ | ✅ Yes |
| All together | ✓ | ✓ | ✓ | ✓ | ✅ Yes (with careful integration) |

## Testing Strategy

### Test Order
1. Test requirements installation
2. Run smoke tests (PR #10)
3. Test macro_utils retry logic (PR #12)
4. Test streamlit caching (PR #12)
5. Test multi-series charts (PR #13)
6. Test templates (PR #11)
7. Test templates with multi-series
8. Full integration test

### Test Commands
```bash
# Install
pip install -r requirements.txt

# Smoke tests
python test_cli_smoke.py
python test_streamlit_smoke.py

# Feature tests
python test_caching_and_retry.py
python test_templates.py

# Integration tests
python generate_macro_report.py --list-templates
python generate_macro_report.py --template core_macro --out test.pdf
streamlit run app.py
```

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Merge conflicts in streamlit_app.py | HIGH | HIGH | Manual careful merge, test each addition |
| Feature incompatibility | MEDIUM | HIGH | Test after each integration step |
| Breaking existing functionality | LOW | HIGH | Run smoke tests after each change |
| Documentation gaps | MEDIUM | MEDIUM | Cross-reference all 4 PRs |
| Test failures | MEDIUM | MEDIUM | Fix incrementally, isolate issues |

## Success Criteria

- [ ] All files from all 4 PRs integrated
- [ ] No merge conflicts remaining
- [ ] All smoke tests pass
- [ ] CLI works: `--spec`, `--template`, `--list-templates`
- [ ] Streamlit works: templates, multi-series, caching, PDF export
- [ ] AGENTS.md has single consolidated Session 6 entry
- [ ] Documentation is complete and consistent
- [ ] All features work together
- [ ] No regressions in existing functionality

## Estimated Effort

- **File Creation**: 15 new files (~2,800 lines total)
- **Code Integration**: 4 major files with conflicts (~400 lines to merge)
- **Documentation**: Consolidate and update (~500 lines)
- **Testing**: Validate all features work together
- **Total**: ~3,700 lines to integrate carefully

## Current Progress

✅ **Phase 1 Complete** (20%)
- Requirements.txt updated
- First smoke test created
- Integration plan documented

⏳ **Phase 2 In Progress** (80% remaining)
- Create remaining files from PRs
- Integrate code changes
- Test and validate

## Next Immediate Actions

1. Create test_streamlit_smoke.py from PR #10
2. Update macro_utils.py with retry logic from PR #12
3. Begin streamlit_app.py integration (most complex)
4. Create template files from PR #11
5. Test incrementally after each change

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-05  
**Status**: Integration in progress  
**Estimated Completion**: Requires focused 2-3 hour session
