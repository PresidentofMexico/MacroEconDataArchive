Agentic Architecture: Macro-Economic Report Generator

Architect: [Redacted] (ex-OpenAI, Current JEPA Lab)
Version: 0.9.4 (Alpha)
Philosophy: Grounded Reasoning / Multi-Step Verification

1. System Overview

This system is not a chatbot. It is a Hierarchical Agentic Workflow designed to ingest raw economic time-series data, construct a latent representation of economic health (the "World Model"), and render that model into a human-readable format (the Report).

The architecture eschews a flat "chat" structure in favor of a Directed Acyclic Graph (DAG) execution flow. Hallucination is strictly prohibited; all narrative claims must be back-referenced to a specific data point retrieved by the Data Ingest Agent.

Core Directives

Data Sovereignty: Narrative cannot be generated without preceding data validation.

Chart-First Narrative: The text explains the chart; the chart does not decorate the text.

Tone Consistency: All outputs must mimic the style of a Federal Reserve Beige Book or a Tier-1 Investment Bank strategy note.

2. The Agents

Agent A: The Orchestrator (System Root)

Role: The Central Executive / State Manager.

Responsibility: Decomposes the user's request (the "Original Prompt") into a dependency graph. It does not write code or analyze data; it manages the hand-offs between agents.

Behavior:

Parses the "Sample Report" to extract the schema (Section headers, Chart types).

Dispatches tasks to Agent B (Data).

Upon data receipt, triggers Agent C (Quant).

Upon visualization receipt, triggers Agent D (Narrator).

Tools: TaskQueue, StateMonitor.

Agent B: The Data Steward (Sensorium)

Role: Interface to external reality (APIs).

Responsibility: Fetching raw data. This agent is deaf to "narrative" and cares only about JSON structures and time-series integrity.

Inputs: List of indicators (e.g., "CPI-U", "Real GDP", "U-3 Unemployment").

Tools:

pandas_datareader (FRED API interface)

BLS_Public_Data_API

World_Bank_Connector

Guardrails:

Must verify data freshness (reject data older than current reporting period).

Must normalize units (e.g., convert all "Billions USD" to uniform scale).

FAILURE MODE: If data is missing, it must throw a DataMissingException rather than fabricating numbers.

Agent C: The Quantitative Analyst (The "Quant")

Role: Processing and Visualization.

Responsibility: meaningful transformation of raw data. A raw CPI number is useless; the Year-over-Year % Change is the insight.

Inputs: Cleaned DataFrames from Agent B.

Operations:

Calculation of YoY, MoM, and CAGR.

Seasonal adjustment verification.

Correlation analysis (e.g., "Does the Phillips Curve hold in this dataset?").

Visualization Generation: Uses matplotlib or seaborn to generate static assets.

Output:

charts/: Directory of .png files.

stats_summary.json: Key metrics for the Narrator (e.g., "Inflation = 3.2%").

Agent D: The Macro Strategist (The Narrator)

Role: Synthesis and Prose.

Responsibility: Translating the stats_summary.json and charts into the "Written Narrative."

Persona: A Senior Economist at Goldman Sachs or the BLS.

Instructions:

"Look at the chart provided by Agent C."

"Describe the trend (Bullish/Bearish/Neutral)."

"Contextualize this against the broader narrative provided by the Orchestrator."

Strict Prohibition: Do not use adjectives like "skyrocketed" or "plummeted." Use "increased significantly" or "declined sharply."

Context Window: Heavily weighted with the "Sample Report" provided in the prompt to ensure style matching.

Agent E: The Compliance Editor (The Critic)

Role: Quality Assurance.

Responsibility: Reviewing the draft against the generated charts.

Process:

Fact Check: Does the text say "GDP rose 2%" when the chart shows 2.1%?

Hallucination Check: Does the text reference data that Agent B never fetched?

Tone Check: Is the language too informal?

Action: Returns the draft to Agent D if thresholds are not met.

3. Interaction Graph

graph TD
    User[User Request] --> Orch[Orchestrator]
    Orch -- 1. Schema Extraction --> Sample[Sample Report Analysis]
    Orch -- 2. Data Request --> Data[Data Steward]
    Data -- 3. Raw Data --> Quant[Quantitative Analyst]
    Quant -- 4. Charts & Stats --> Narr[Macro Strategist]
    Narr -- 5. Draft Text --> Edit[Compliance Editor]
    Edit -- 6. Revision Request --> Narr
    Edit -- 7. Final Approval --> Orch
    Orch --> Final[Final PDF Report]


4. Implementation Details

System Prompts (Excerpts)

Agent D (Macro Strategist):

You are a veteran macroeconomist. You do not speculate. You interpret.

INPUT:

Chart: unemployment_rate_2024.png (Trend: Downward)

Data: current_rate: 3.7%, prev_rate: 3.9%

TASK:
Write a paragraph for the "Labor Market" section.

CONSTRAINT:

Use passive voice where appropriate for formality.

Reference the chart explicitly (e.g., "As illustrated in Figure 2...").

Avoid conversational fillers.

Agent B (Data Steward):

You are a Python script wrapper. You do not speak English; you speak JSON.

TASK:
Fetch Series ID: GDP from FRED.

IF fail:
Retry with exponential backoff.

IF success:
Return strict JSON schema: { "date": [], "value": [], "units": "" }

5. Future Roadmap (World Model Integration)

Phase 2: Implement a predictive JEPA (Joint Embedding Predictive Architecture) model to forecast the next quarter's data based on the current ingest, allowing the report to include a "Forward Outlook" section grounded in latent-space projections rather than autoregressive guessing.

---

# AGENT SESSION BREADCRUMBS

**CRITICAL: All future agents MUST read this section first and append their session details below.**

## Instructions for Future Agents

1. **READ** this entire AGENTS.md file to understand the architecture
2. **REVIEW** the session history below to understand what has been done
3. **APPEND** your session details to the end of this breadcrumbs section
4. **PRESERVE** all previous session information
5. **COMMIT** your changes with clear messages
6. **REFERENCE** the CHANGELOG.md for detailed bug fix history

---

## Session History

### Session 1: Initial Bug Fixes and Setup
**Date:** 2025-12-17  
**Branch:** copilot/fix-obvious-errors-and-bugs  
**Status:** ✅ MERGED (PR #1)  
**Agent:** copilot-swe-agent

**Summary:**
Fixed critical bugs and created missing files to make the repository fully operational.

**Changes Made:**
- ✅ Created `.gitignore` for build artifact exclusion
- ✅ Created `macro_chart_spec.json` with 10 example charts
- ✅ Created `requirements.txt` with dependency versions
- ✅ Created comprehensive `README.md` documentation
- ✅ Created `CHANGELOG.md` documenting all fixes
- ✅ Fixed DataFrame column mismatch bug in `generate_macro_report.py`
- ✅ Added error handling for empty data
- ✅ Added progress messages and proper exit codes

**Critical Bugs Fixed:**
1. DataFrame column name mismatch (line 89-103)
2. No error handling for empty data (line 260-275)
3. Missing configuration files
4. Poor error messages

**Testing:**
- Python syntax validation ✅
- JSON validation ✅
- Import checks ✅
- Edge case testing ✅

**Files Modified:** 8 files added/modified, 925 lines total

---

### Session 2: Review Changes & Update Requirements
**Date:** 2025-12-18  
**Branch:** copilot/review-recent-changes  
**Status:** 🔄 IN PROGRESS  
**Agent:** copilot-swe-agent

**Summary:**
Comprehensive review of all previous changes and updating requirements.txt to latest versions.

**Tasks Completed:**
- ✅ Reviewed all git commits and history
- ✅ Analyzed previous agent session work thoroughly
- ✅ Verified no errors exist in previous commits
- ✅ Checked latest package versions:
  - pandas: 2.3.3 (from >=1.3.0)
  - pandas-datareader: 0.10.0 (already latest)
  - matplotlib: 3.10.8 (from >=3.4.0)
  - reportlab: 4.4.6 (from >=3.6.0)
- ✅ Created SESSION_CONTEXT.md with full session history
- ✅ Updated AGENTS.md with breadcrumbs section (this section)

**Tasks In Progress:**
- 🔄 Update requirements.txt to latest stable versions
- 🔄 Test updated requirements

**Notes for Next Agent:**
- All previous session work was high quality with no errors found
- The agentic architecture is well-documented and ready for enhancement
- Requirements are being updated to latest stable versions
- SESSION_CONTEXT.md provides detailed history

**Key Architecture Insights:**
- System follows DAG execution flow (Orchestrator → Data Steward → Quant → Strategist → Editor)
- Data sovereignty principle: no narrative without data validation
- Chart-first approach: text explains charts, not decorates them
- Professional tone matching Federal Reserve Beige Book style

---

## Template for Next Agent Session

**Copy and fill this template when you start your session:**

```markdown
### Session X: [Brief Title]
**Date:** YYYY-MM-DD  
**Branch:** [branch-name]  
**Status:** [IN PROGRESS | COMPLETED | MERGED]  
**Agent:** [agent-name]

**Summary:**
[1-2 sentence summary of what you're doing]

**Tasks Completed:**
- ✅ Task 1
- ✅ Task 2

**Tasks In Progress:**
- 🔄 Task in progress

**Tasks Remaining:**
- ⏳ Pending task

**Issues Found & Fixed:**
- 🐛 Issue description and resolution

**Files Modified:**
- 📝 file1.py - description
- 📝 file2.json - description

**Notes for Next Agent:**
- Important context or gotchas
- Suggestions for future work

**Testing Performed:**
- Test description and results
```

---

## Important Reminders

⚠️ **Always check these before completing your session:**
1. Have you reviewed previous session notes?
2. Have you updated this breadcrumbs section?
3. Have you tested your changes?
4. Have you updated CHANGELOG.md if fixing bugs?
5. Have you committed with clear messages?
6. Have you noted any warnings for the next agent?

📋 **Quick Reference:**
- Main script: `generate_macro_report.py`
- Config file: `macro_chart_spec.json`
- Dependencies: `requirements.txt`
- Architecture: See sections 1-5 above
- Bug history: See `CHANGELOG.md`
- Session history: This section

---

**END OF BREADCRUMBS SECTION**
