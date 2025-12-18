# Macro Economic Data Archive

A reproducible template to generate chart-driven macroeconomic reports from public time series data.

## Overview

This tool generates professional PDF reports with economic charts and data visualizations, similar in spirit to Federal Reserve publications. It pulls time series data from FRED (Federal Reserve Bank of St. Louis) and applies consistent transformations (level, year-over-year %, quarter-over-quarter SAAR %).

## Files

- **generate_macro_report.py**: Python script to generate a chart-driven PDF from public time series
- **macro_chart_spec.json**: Example chart specification (edit/extend to match your needs)
- **requirements.txt**: Python dependencies
- **AGENTS.md**: Documentation of the agentic architecture design philosophy

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install pandas pandas-datareader matplotlib reportlab
```

### 2. Generate a PDF Report

```bash
python generate_macro_report.py --spec macro_chart_spec.json --out Macro_Economic_Data_Archive.pdf
```

### 3. Customize Your Report

Edit `macro_chart_spec.json` to add or modify charts. For each chart, specify:

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
python generate_macro_report.py --spec macro_chart_spec.json --out report.pdf --start 2010-01-01
```

### Custom Temporary Directory

```bash
python generate_macro_report.py --spec macro_chart_spec.json --out report.pdf --tmpdir /tmp/charts
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

1. Adding more chart entries to `macro_chart_spec.json`
2. Using different FRED series IDs (search at https://fred.stlouisfed.org/)
3. Customizing the chart rendering and PDF layout functions
4. Adding additional data sources beyond FRED

## Requirements

- Python 3.7+
- Internet access (to fetch data from FRED API)
- The following Python packages:
  - pandas >= 1.3.0
  - pandas-datareader >= 0.10.0
  - matplotlib >= 3.4.0
  - reportlab >= 3.6.0

## Notes

- The script requires internet access to fetch data from FRED
- Some economic series may have different update frequencies
- Missing or unavailable data will cause charts to be skipped with a warning
- Charts are saved temporarily to `_charts_tmp/` by default (configurable)

## License

This is a template for educational and research purposes. Please respect data source terms of use.
