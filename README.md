# Macro Economic Data Archive

A powerful toolkit for creating chart-driven macroeconomic reports from public time series data. Available in two modes:
- **🚀 MacroBuilder (Streamlit App)**: Interactive web app with AI-powered insights, data caching, multi-series charts, templates, and configuration persistence
- **⚙️ CLI Tool**: Command-line PDF generator for automated workflows with template support
- **🐳 Docker**: Ready-to-deploy containerized application

## ✨ Latest Features (2026-01-07) ✅ NEW

**💾 Save & Load Configurations**:
- Save current report configuration as JSON ✅
- Download configurations for backup/sharing ✅
- Load saved configurations to continue work ✅
- Import configurations via drag-and-drop ✅
- Configurations compatible with template format ✅

**🐳 Docker Support**:
- Production-ready Dockerfile ✅
- Optimized with Kaleido/Plotly dependencies ✅
- Health checks and environment configuration ✅
- See [Docker Guide](docs/DOCKER_GUIDE.md) for deployment instructions ✅

## ✨ Previous Features (2026-01-05) ✅ COMPLETED

**🎯 Template System** - One-click report generation with 3 pre-built templates:
- Core Macro (4 indicators): GDP, inflation, unemployment, interest rates
- Inflation Deep Dive (8 measures): Headline, core, and component analysis
- Labor Markets (9 indicators): Employment, wages, and labor force metrics

**⚡ Data Caching & Reliability**:
- 1-hour data caching (10-200x speedup for repeated fetches) ✅
- Exponential backoff retry logic (auto-recovers from transient errors) ✅
- Smart error handling (rate limits, server errors, network issues) ✅
- Custom exceptions (FREDRateLimitError, FREDServerError) ✅
- Manual cache clear button in UI ✅

**📊 Multi-Series Charts**:
- Plot multiple indicators on one chart for comparison ✅
- Interactive legend and hover details ✅
- Support for both single and multi-series templates ✅

**🧪 Comprehensive Testing**:
- 5 test suites with 25+ tests (all passing) ✅
- Installation verification script ✅
- Smoke tests for CLI and Streamlit ✅
- Template validation tests ✅
- Caching and retry logic tests ✅

## Overview

This toolkit generates professional economic reports with data visualizations, similar in spirit to Federal Reserve publications. It pulls time series data from FRED (Federal Reserve Bank of St. Louis) and applies consistent transformations (level, year-over-year %, quarter-over-quarter SAAR %).

## 🆕 MacroBuilder - Interactive Streamlit App

Build custom economic reports interactively with AI-powered analysis.

### Features
- 📊 **Dynamic Chart Builder**: Add charts from 800,000+ FRED series with real-time preview
- 🎯 **Template System**: One-click report generation from pre-built templates
- ⚡ **Data Caching**: 1-hour TTL cache with 10-200x speedup for repeated queries
- 🔄 **Smart Retry Logic**: Exponential backoff handles transient API errors
- 📈 **Multi-Series Charts**: Compare multiple indicators on one chart
- 💾 **Save & Load**: Export and import report configurations as JSON
- 🤖 **AI-Powered Analysis**: Generate professional economic narratives using ChatGPT 4o-mini
- 🎨 **Interactive Visualizations**: Plotly charts with hover details and zoom
- 📝 **Report Assembly**: Reorder charts, edit narratives, preview final report
- 📥 **PDF Export**: Download publication-ready PDF reports
- 🐳 **Docker Ready**: Containerized deployment with one command

### Quick Start with MacroBuilder

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Verify installation:**
```bash
python verify_installation.py
```

3. **Set your OpenAI API key** (for AI features):
```bash
export OPENAI_API_KEY='your-api-key-here'
```

4. **Launch the app:**
```bash
streamlit run app.py
```

5. **Build your report:**
   - Load a template from the sidebar dropdown
   - Try quick-add examples or add custom charts
   - Generate AI analysis for each chart
   - Reorder sections as needed
   - Clear cache if you need fresh data
   - Save your configuration for later
   - Export to PDF

### Docker Deployment

Run MacroBuilder in a container:

```bash
# Build the image
docker build -t macrobuilder:latest .

# Run the container
docker run -p 8501:8501 -e OPENAI_API_KEY='your-key' macrobuilder:latest
```

See the complete [Docker Deployment Guide](docs/DOCKER_GUIDE.md) for advanced options.

### MacroBuilder Architecture

- **app.py**: Streamlit entrypoint (wrapper)
- **src/macro_econ_data_archive/streamlit_app.py**: Streamlit implementation with caching and templates
- **src/macro_econ_data_archive/macro_utils.py**: Shared data fetching + transforms (with retry logic)
- **generate_macro_report.py**: CLI entrypoint (wrapper)
- **config/templates/**: Pre-built report templates (JSON format)
- **src/macro_econ_data_archive/report_generator.py**: Chart rendering + PDF engine + template loading

## ⚙️ CLI Tool - Automated Report Generation

For programmatic report generation and CI/CD pipelines.

### Quick Start with CLI

1. **List available templates:**
```bash
python generate_macro_report.py --list-templates
```

2. **Generate report from template:**
```bash
python generate_macro_report.py \
  --template core_macro \
  --out report.pdf \
  --start 2020-01-01
```

3. **Or use custom JSON spec (legacy):**
```bash
python generate_macro_report.py \
  --spec config/macro_chart_spec.json \
  --out report.pdf \
  --start 2020-01-01
```

### Files

- **generate_macro_report.py**: Python script to generate a chart-driven PDF from public time series
- **config/macro_chart_spec.json**: Example chart specification (edit/extend to match your needs)
- **requirements.txt**: Python dependencies
- **AGENTS.md**: Documentation of the agentic architecture design philosophy
- **docs/**: Additional guides and implementation notes

## Quick Start

### CLI Mode

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install pandas matplotlib reportlab streamlit openai plotly
```

### 2. Generate a PDF Report

```bash
python generate_macro_report.py --spec config/macro_chart_spec.json --out Macro_Economic_Data_Archive.pdf
```

### 3. Customize Your Report

Edit `config/macro_chart_spec.json` to add or modify charts. For each chart, specify:

- **series**: List of FRED series IDs with labels
- **transform**: `level`, `yoy` (year-over-year %), or `qoq_saar` (quarter-over-quarter SAAR %)
- **frequency**: `daily`, `weekly`, `monthly`, or `quarterly`
- **units**: Label for the y-axis
- **notes**: Optional notes about the data source

Example chart specification:

```json
{
  "page_title": "Consumer Price Index",
  "series": [
    {
      "id": "CPIAUCSL",
      "label": "CPI-U (All Urban Consumers)"
    }
  ],
  "transform": "yoy",
  "frequency": "monthly",
  "units": "Percent",
  "notes": "Source: Bureau of Labor Statistics via FRED"
}
```

## Advanced Usage

### Custom Date Range

```bash
python generate_macro_report.py --spec config/macro_chart_spec.json --out report.pdf --start 2010-01-01
```

### Custom Temporary Directory

```bash
python generate_macro_report.py --spec config/macro_chart_spec.json --out report.pdf --tmpdir /tmp/charts
```

## Data Sources

The script uses the FRED API to access official data from:
- Bureau of Economic Analysis (BEA)
- Bureau of Labor Statistics (BLS)
- Census Bureau
- Federal Reserve
- Energy Information Administration (EIA)
- And many other agencies

## Extending the Template

This script is intentionally modular and can be extended to 100+ page reports by:

1. Adding more chart entries to `config/macro_chart_spec.json`
2. Using different FRED series IDs (search at https://fred.stlouisfed.org/)
3. Customizing the chart rendering and PDF layout functions
4. Adding additional data sources beyond FRED

## Requirements

- Python 3.7+
- Internet access (to fetch data from FRED API)
- OpenAI API key (for MacroBuilder AI features)
- The following Python packages:
  - pandas >= 2.3.3
  - matplotlib >= 3.10.8
  - reportlab >= 4.4.6
  - streamlit >= 1.40.0 (for MacroBuilder)
  - openai >= 1.57.0 (for MacroBuilder)
  - plotly >= 5.24.0 (for MacroBuilder)
  - kaleido >= 0.2.1 (for MacroBuilder PDF export)

## Notes

- The script requires internet access to fetch data from FRED
- Some economic series may have different update frequencies
- Missing or unavailable data will cause charts to be skipped with a warning
- Charts are saved temporarily to `_charts_tmp/` by default (configurable)

## License

This is a template for educational and research purposes. Please respect data source terms of use.
