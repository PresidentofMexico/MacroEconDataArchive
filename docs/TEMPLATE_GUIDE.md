# Template Guide

## Overview

The template system enables one-click report generation with predefined sets of economic indicators. Templates are JSON files that specify charts, series, and formatting options.

## Quick Start

### Using Templates (CLI)

List available templates:
```bash
python generate_macro_report.py --list-templates
```

Generate a report from a template:
```bash
python generate_macro_report.py \
  --template core_macro \
  --out report.pdf \
  --start 2020-01-01
```

### Using Templates (Streamlit)

1. Launch the app: `streamlit run app.py`
2. Select a template from the sidebar dropdown
3. Click "Load Template"
4. Generate AI analysis for each chart
5. Export to PDF

## Template Structure

### Basic Template

```json
{
  "report_title": "Economic Report Title",
  "description": "Optional description",
  "charts": [
    {
      "page_title": "Chart Title",
      "series": [
        {
          "id": "GDPC1",
          "label": "Real GDP"
        }
      ],
      "frequency": "quarterly",
      "transform": "qoq_saar",
      "units": "Percent",
      "notes": "Optional notes or commentary"
    }
  ]
}
```

### Required Fields

**Root Level:**
- `report_title` (string): Title for the report
- `charts` (array): List of chart configurations

**Chart Level:**
- `page_title` (string): Chart title
- `series` (array): List of series to plot (see below)

**Series Level:**
- `id` (string): FRED series ID (e.g., "GDPC1")
- `label` (string): Display name for the series

### Optional Fields

**Root Level:**
- `description` (string): Template description

**Chart Level:**
- `frequency` (string): "monthly", "quarterly", "weekly", "daily" (default: "monthly")
- `transform` (string): "level", "yoy", "qoq_saar" (default: "level")
- `units` (string): Y-axis label (e.g., "Percent", "Billions USD")
- `notes` (string): Chart commentary or context

## Transform Types

### Level
No transformation. Shows raw data.

```json
{
  "transform": "level",
  "units": "Billions of Dollars"
}
```

### Year-over-Year (yoy)
Percent change from same period last year.

```json
{
  "transform": "yoy",
  "units": "Percent"
}
```

### Quarter-over-Quarter SAAR (qoq_saar)
Annualized growth rate from previous quarter.

```json
{
  "transform": "qoq_saar",
  "units": "Percent"
}
```

## Multi-Series Charts

Plot multiple series on one chart:

```json
{
  "page_title": "Consumer vs Business Sentiment",
  "series": [
    {
      "id": "UMCSENT",
      "label": "Consumer Sentiment"
    },
    {
      "id": "BSCICP03USM665S",
      "label": "Business Confidence"
    }
  ],
  "frequency": "monthly",
  "transform": "level",
  "units": "Index"
}
```

## Built-in Templates

### core_macro.json
**4 essential macroeconomic indicators**

- Real GDP (quarterly, qoq_saar)
- Unemployment Rate (monthly, level)
- CPI Inflation (monthly, yoy)
- 10-Year Treasury Rate (daily, level)

Usage:
```bash
python generate_macro_report.py --template core_macro --out core.pdf
```

### inflation_deep_dive.json
**8 comprehensive inflation measures**

- Headline CPI
- Core CPI
- PPI
- PCE Price Index
- Core PCE
- Import Prices
- Export Prices
- Commodity Prices

Usage:
```bash
python generate_macro_report.py --template inflation_deep_dive --out inflation.pdf
```

### labor_markets.json
**9 employment and wage indicators**

- Unemployment Rate
- Labor Force Participation
- Nonfarm Payrolls
- Initial Jobless Claims
- Job Openings (JOLTS)
- Quits Rate
- Average Hourly Earnings
- Employment Cost Index
- Productivity

Usage:
```bash
python generate_macro_report.py --template labor_markets --out labor.pdf
```

## Creating Custom Templates

### Step 1: Find Series IDs

Search FRED: https://fred.stlouisfed.org/

Example popular series:
- **GDPC1**: Real GDP
- **UNRATE**: Unemployment Rate
- **CPIAUCSL**: Consumer Price Index
- **DGS10**: 10-Year Treasury Rate
- **PAYEMS**: Nonfarm Payrolls
- **UMCSENT**: Consumer Sentiment

### Step 2: Create Template File

Save as `config/templates/my_template.json`:

```json
{
  "report_title": "My Custom Report",
  "description": "Custom economic indicators",
  "charts": [
    {
      "page_title": "Real GDP Growth",
      "series": [
        {
          "id": "GDPC1",
          "label": "Real GDP"
        }
      ],
      "frequency": "quarterly",
      "transform": "qoq_saar",
      "units": "Percent"
    },
    {
      "page_title": "Labor Market Indicators",
      "series": [
        {
          "id": "UNRATE",
          "label": "Unemployment Rate"
        },
        {
          "id": "CIVPART",
          "label": "Labor Force Participation"
        }
      ],
      "frequency": "monthly",
      "transform": "level",
      "units": "Percent"
    }
  ]
}
```

### Step 3: Test Template

List templates to verify it's found:
```bash
python generate_macro_report.py --list-templates
```

Generate report:
```bash
python generate_macro_report.py --template my_template --out test.pdf --start 2020-01-01
```

## Advanced Features

### Combining Frequencies

Mix monthly and quarterly data:

```json
{
  "charts": [
    {
      "page_title": "Monthly Inflation",
      "series": [{"id": "CPIAUCSL", "label": "CPI"}],
      "frequency": "monthly",
      "transform": "yoy"
    },
    {
      "page_title": "Quarterly GDP",
      "series": [{"id": "GDPC1", "label": "GDP"}],
      "frequency": "quarterly",
      "transform": "qoq_saar"
    }
  ]
}
```

### Comparative Charts

Compare related indicators:

```json
{
  "page_title": "Headline vs Core Inflation",
  "series": [
    {
      "id": "CPIAUCSL",
      "label": "Headline CPI"
    },
    {
      "id": "CPILFESL",
      "label": "Core CPI"
    }
  ],
  "frequency": "monthly",
  "transform": "yoy",
  "units": "Year-over-Year %"
}
```

## Best Practices

### Template Design

1. **Logical grouping**: Organize charts by theme (inflation, labor, GDP, etc.)
2. **Consistent transforms**: Use appropriate transforms for each series type
3. **Clear labels**: Use descriptive names, not just FRED IDs
4. **Reasonable chart count**: 4-10 charts per template for readability
5. **Add context**: Include notes field with important details

### Naming Conventions

- Use lowercase with underscores: `my_template.json`
- Be descriptive: `inflation_analysis.json` not `template1.json`
- Avoid spaces in filenames

### Testing

Always test new templates:
```bash
# Test data fetching
python generate_macro_report.py --template my_template --out test.pdf --start 2023-01-01

# Verify in Streamlit
streamlit run app.py
# Load template and check charts render correctly
```

## Troubleshooting

### Template Not Found

**Issue**: `Template 'my_template' not found`

**Solutions**:
- Check filename: Must be in `config/templates/`
- Check extension: Must end with `.json`
- Verify permissions: File must be readable

### Invalid JSON

**Issue**: `JSON decode error`

**Solutions**:
- Validate JSON syntax: https://jsonlint.com/
- Check for missing commas, brackets
- Ensure proper quotes (double quotes only)

### Series Not Found

**Issue**: `No data available for series XXXXX`

**Solutions**:
- Verify series ID on FRED: https://fred.stlouisfed.org/
- Check spelling (case-sensitive)
- Ensure series has data for your date range
- Try different start date: `--start 1990-01-01`

### Empty Charts

**Issue**: Charts render but show no data

**Solutions**:
- Check transform compatibility (e.g., qoq_saar only for quarterly)
- Verify frequency matches series
- Extend date range

## Template Validation

Use the test suite:

```bash
python test_templates.py
```

This validates:
- JSON structure
- Required fields present
- Series IDs format
- Schema compliance

## Example: Building a Financial Markets Template

```json
{
  "report_title": "Financial Markets Dashboard",
  "description": "Key financial market indicators",
  "charts": [
    {
      "page_title": "Equity Markets",
      "series": [
        {
          "id": "SP500",
          "label": "S&P 500"
        }
      ],
      "frequency": "daily",
      "transform": "level",
      "units": "Index Level"
    },
    {
      "page_title": "Treasury Yields",
      "series": [
        {
          "id": "DGS2",
          "label": "2-Year"
        },
        {
          "id": "DGS10",
          "label": "10-Year"
        },
        {
          "id": "DGS30",
          "label": "30-Year"
        }
      ],
      "frequency": "daily",
      "transform": "level",
      "units": "Percent"
    },
    {
      "page_title": "Dollar Index",
      "series": [
        {
          "id": "DTWEXBGS",
          "label": "Broad USD Index"
        }
      ],
      "frequency": "daily",
      "transform": "level",
      "units": "Index"
    },
    {
      "page_title": "Credit Spreads",
      "series": [
        {
          "id": "BAMLH0A0HYM2",
          "label": "High Yield OAS"
        }
      ],
      "frequency": "daily",
      "transform": "level",
      "units": "Basis Points"
    }
  ]
}
```

## Resources

- **FRED Database**: https://fred.stlouisfed.org/
- **FRED API Docs**: https://fred.stlouisfed.org/docs/api/
- **Popular Series**: https://fred.stlouisfed.org/tags/series
- **JSON Validator**: https://jsonlint.com/

## Summary

- Templates enable one-click report generation
- Simple JSON structure for easy customization
- Support single and multi-series charts
- Three built-in templates provided
- Create custom templates for specific analysis needs
- Fully integrated with CLI and Streamlit UI

For more information, see README.md or run `python generate_macro_report.py --help`.
