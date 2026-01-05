# Macro Economic Data Archive

A powerful toolkit for creating chart-driven macroeconomic reports from public time series data. Available in two modes:
- **🚀 MacroBuilder (Streamlit App)**: Interactive web app with AI-powered insights
- **⚙️ CLI Tool**: Command-line PDF generator for automated workflows

## Overview

This toolkit generates professional economic reports with data visualizations, similar in spirit to Federal Reserve publications. It pulls time series data from FRED (Federal Reserve Bank of St. Louis) and applies consistent transformations (level, year-over-year %, quarter-over-quarter SAAR %).

## 🆕 MacroBuilder - Interactive Streamlit App

**NEW!** Build custom economic reports interactively with AI-powered analysis.

### Features
- 📊 **Dynamic Chart Builder**: Add charts from 800,000+ FRED series with real-time preview
- 🤖 **AI-Powered Analysis**: Generate professional economic narratives using ChatGPT 4o-mini
- 🎨 **Interactive Visualizations**: Plotly charts with hover details and zoom
- 📝 **Report Assembly**: Reorder charts, edit narratives, preview final report
- 📥 **PDF Export**: Download publication-ready PDF reports

### Quick Start with MacroBuilder

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set your OpenAI API key** (for AI features):
```bash
export OPENAI_API_KEY='your-api-key-here'
```

3. **Launch the app:**
```bash
streamlit run app.py
```

4. **Build your report:**
   - Add charts using the sidebar (or try quick-add examples)
   - Generate AI analysis for each chart
   - Reorder sections as needed
   - Export to PDF

### MacroBuilder Architecture

- **app.py**: Streamlit entrypoint (wrapper)
- **src/macro_econ_data_archive/streamlit_app.py**: Streamlit implementation
- **src/macro_econ_data_archive/macro_utils.py**: Shared data fetching + transforms
- **generate_macro_report.py**: CLI entrypoint (wrapper)
- **src/macro_econ_data_archive/report_generator.py**: Chart rendering + PDF engine (also used by MacroBuilder)

## ⚙️ CLI Tool - Automated Report Generation

For programmatic report generation and CI/CD pipelines.

### Files

- **generate_macro_report.py**: Python script to generate a chart-driven PDF from public time series
- **config/macro_chart_spec.json**: Example chart specification (edit/extend to match your needs)
- **requirements.txt**: Python dependencies
- **AGENTS.md**: Documentation of the agentic architecture design philosophy
- **docs/**: Additional guides and implementation notes

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Internet access (for fetching data from FRED API)
- OpenAI API key (optional, for AI-powered narrative generation in MacroBuilder)

### Installation

**Install all dependencies:**

```bash
pip install -r requirements.txt
```

This will install:
- `pandas` - Data manipulation
- `matplotlib` - Chart generation (CLI)
- `reportlab` - PDF assembly
- `streamlit` - Interactive web app
- `plotly` - Interactive visualizations
- `openai` - AI narrative generation
- `kaleido` - Plotly to PNG conversion (for PDF export)
- `requests` - HTTP requests for data fetching

**Verify installation:**

```bash
# Test CLI tool
python test_cli_smoke.py

# Test Streamlit app
python test_streamlit_smoke.py
```

### CLI Mode

### 1. Generate a PDF Report

```bash
python generate_macro_report.py --spec config/macro_chart_spec.json --out Macro_Economic_Data_Archive.pdf
```

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

- Python 3.8 or higher
- Internet access (to fetch data from FRED API)
- OpenAI API key (optional, for MacroBuilder AI features)

All required Python packages are listed in `requirements.txt`:
- `pandas>=2.0.0` - Data manipulation and analysis
- `matplotlib>=3.7.0` - Chart generation for CLI tool
- `reportlab>=4.0.0` - PDF document assembly
- `streamlit>=1.28.0` - Interactive web application framework
- `plotly>=5.17.0` - Interactive data visualizations
- `openai>=1.0.0` - AI-powered narrative generation
- `kaleido>=0.2.1` - Plotly to static image export (for PDF)
- `requests>=2.31.0` - HTTP library for API calls

Install with: `pip install -r requirements.txt`

## Notes

- The script requires internet access to fetch data from FRED
- Some economic series may have different update frequencies
- Missing or unavailable data will cause charts to be skipped with a warning
- Charts are saved temporarily to `_charts_tmp/` by default (configurable)

## License

This is a template for educational and research purposes. Please respect data source terms of use.
