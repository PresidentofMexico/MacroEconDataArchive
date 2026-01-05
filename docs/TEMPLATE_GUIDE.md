# Template Guide for MacroBuilder

## Overview

Templates are pre-configured sets of charts that allow you to create comprehensive economic reports with a single click. Instead of adding charts one by one, you can load a complete template that includes multiple related charts.

**Tag**: `[template-pushbutton-upgrade-2026]`

## Using Templates

### Streamlit App

1. Open MacroBuilder: `streamlit run app.py`
2. In the sidebar, find the **"📋 Build from Template"** section
3. Select a template from the dropdown (e.g., "Core Macro Dashboard")
4. Review the template description and tags
5. Click **"📥 Load Template"**
6. All charts from the template will be loaded into your report
7. You can then:
   - Generate AI analysis for each chart
   - Reorder or remove charts
   - Add additional custom charts
   - Export to PDF

### Command Line Interface (CLI)

List available templates:
```bash
python generate_macro_report.py --list-templates
```

Generate a report from a template:
```bash
python generate_macro_report.py --template core_macro --out report.pdf
```

Generate with a custom date range:
```bash
python generate_macro_report.py --template inflation_deep_dive --out report.pdf --start 2020-01-01
```

## Built-in Templates

### 1. Core Macro Dashboard (`core_macro.json`)

**Description**: Essential macroeconomic indicators for a comprehensive overview

**Charts included:**
- Real GDP Growth Rate (QoQ SAAR)
- Consumer Price Index - Year-over-Year Change
- Unemployment Rate
- Federal Funds Effective Rate
- 10-Year Treasury Constant Maturity Rate

**Best for**: Quick economic snapshots, board presentations, general analysis

---

### 2. Inflation Deep Dive (`inflation_deep_dive.json`)

**Description**: Comprehensive inflation analysis including CPI, PCE, PPI, and wage growth

**Charts included:**
- Consumer Price Index (Level)
- CPI Year-over-Year Inflation Rate
- Core CPI (Excluding Food and Energy) - YoY
- Personal Consumption Expenditures Price Index - YoY
- Core PCE - YoY
- Producer Price Index - Final Demand - YoY
- Average Hourly Earnings - YoY
- 5-Year Breakeven Inflation Rate

**Best for**: Federal Reserve watchers, inflation analysis, monetary policy research

---

### 3. Labor Markets (`labor_markets.json`)

**Description**: Comprehensive employment and labor market indicators

**Charts included:**
- Unemployment Rate (U-3)
- U-6 Unemployment Rate (Broad Measure)
- Total Nonfarm Payrolls (Level)
- Nonfarm Payrolls - Year-over-Year Growth
- Labor Force Participation Rate
- Initial Jobless Claims (4-Week Moving Average)
- Average Hourly Earnings (Level)
- Average Hourly Earnings - Year-over-Year Growth
- Job Openings (JOLTS)

**Best for**: Labor market analysis, employment reports, wage research

## Creating Custom Templates

### Template File Structure

Templates are JSON files stored in `config/templates/`. Here's the schema:

```json
{
  "template_metadata": {
    "name": "Your Template Name",
    "description": "Brief description of what this template covers",
    "version": "1.0",
    "tags": ["tag1", "tag2", "tag3"],
    "author": "Your Name",
    "created": "YYYY-MM-DD"
  },
  "report_title": "Title for the Generated Report",
  "as_of": "Current Period",
  "charts": [
    {
      "page_title": "Chart Title",
      "series": [
        {
          "id": "FRED_SERIES_ID",
          "label": "Display Label"
        }
      ],
      "transform": "level",
      "frequency": "monthly",
      "units": "Percent",
      "notes": "Optional notes about data source"
    }
  ]
}
```

### Field Descriptions

#### template_metadata (optional but recommended)

- **name**: Display name shown in the UI
- **description**: Brief explanation of the template's purpose
- **version**: Template version (useful for tracking updates)
- **tags**: Array of keywords for categorization
- **author**: Creator's name
- **created**: Creation date (YYYY-MM-DD)

#### Report Settings

- **report_title**: Title that appears at the top of the PDF
- **as_of**: Date/period descriptor (can be overridden)

#### Chart Configuration

Each chart in the `charts` array should have:

- **page_title**: Title for the chart page
- **series**: Array of FRED series to plot
  - **id**: FRED series ID (e.g., "GDPC1", "UNRATE")
  - **label**: Human-readable label for the legend
- **transform**: Data transformation
  - `"level"` - Raw data values
  - `"yoy"` - Year-over-year percent change
  - `"qoq_saar"` - Quarter-over-quarter seasonally adjusted annual rate
- **frequency**: Data frequency
  - `"daily"`, `"weekly"`, `"monthly"`, `"quarterly"`
- **units**: Y-axis label (e.g., "Percent", "Billions of Dollars")
- **notes**: Optional source attribution or methodological notes

### Step-by-Step: Creating a Custom Template

1. **Plan your report**: Decide which economic indicators you want to include

2. **Find FRED series IDs**: Search at https://fred.stlouisfed.org/
   - Example: Search "consumer price index" → find "CPIAUCSL"

3. **Create the JSON file**: 
   ```bash
   touch config/templates/my_template.json
   ```

4. **Add metadata and charts**: Follow the structure above

5. **Validate the JSON**: Ensure proper syntax
   ```bash
   python -m json.tool config/templates/my_template.json
   ```

6. **Test the template**:
   - CLI: `python generate_macro_report.py --template my_template --out test.pdf`
   - Streamlit: Load it from the dropdown

### Example: Creating a "Housing Market" Template

```json
{
  "template_metadata": {
    "name": "Housing Market Dashboard",
    "description": "Comprehensive housing market indicators",
    "version": "1.0",
    "tags": ["housing", "real-estate", "construction"],
    "author": "Your Name",
    "created": "2026-01-05"
  },
  "report_title": "Housing Market Analysis",
  "as_of": "Current Period",
  "charts": [
    {
      "page_title": "New Home Sales",
      "series": [
        {
          "id": "HSN1F",
          "label": "New Single-Family Home Sales"
        }
      ],
      "transform": "level",
      "frequency": "monthly",
      "units": "Thousands",
      "notes": "Seasonally adjusted annual rate. Source: Census Bureau via FRED"
    },
    {
      "page_title": "Housing Starts",
      "series": [
        {
          "id": "HOUST",
          "label": "Total Housing Starts"
        }
      ],
      "transform": "level",
      "frequency": "monthly",
      "units": "Thousands of Units",
      "notes": "Seasonally adjusted annual rate. Source: Census Bureau via FRED"
    },
    {
      "page_title": "30-Year Fixed Mortgage Rate",
      "series": [
        {
          "id": "MORTGAGE30US",
          "label": "30-Year Fixed Rate Mortgage Average"
        }
      ],
      "transform": "level",
      "frequency": "weekly",
      "units": "Percent",
      "notes": "Source: Freddie Mac via FRED"
    },
    {
      "page_title": "Case-Shiller Home Price Index - YoY Change",
      "series": [
        {
          "id": "CSUSHPISA",
          "label": "Case-Shiller U.S. National Home Price Index"
        }
      ],
      "transform": "yoy",
      "frequency": "monthly",
      "units": "Percent",
      "notes": "Seasonally adjusted. Source: S&P Dow Jones Indices via FRED"
    }
  ]
}
```

Save this as `config/templates/housing_market.json` and it will appear in the template selector!

## Best Practices

### Template Design

1. **Focused themes**: Group related indicators (e.g., all inflation metrics)
2. **Logical ordering**: Start with high-level indicators, then drill down
3. **5-10 charts**: Balance comprehensiveness with readability
4. **Consistent transforms**: Use YoY for growth rates, level for rates/prices
5. **Clear labels**: Make series labels self-explanatory

### Metadata

1. **Descriptive names**: Use clear, professional names
2. **Helpful descriptions**: Explain the template's purpose in 1-2 sentences
3. **Relevant tags**: Add 3-5 keywords for discoverability
4. **Version control**: Update version when making significant changes

### Data Quality

1. **Verify series IDs**: Test that FRED series exist and are active
2. **Check frequencies**: Ensure frequency matches the actual data
3. **Appropriate transforms**: Use `qoq_saar` for GDP, `yoy` for most growth rates
4. **Clear units**: Match units to the transform (e.g., "Percent" for YoY changes)

## Troubleshooting

### Template doesn't appear in dropdown

- Check that the file is in `config/templates/`
- Verify the JSON syntax is valid
- Ensure the file has a `.json` extension
- Restart the Streamlit app

### Charts fail to load

- Verify FRED series IDs are correct (search on FRED website)
- Check that the series is still active (some series are discontinued)
- Ensure your date range includes available data
- Review the error message for specific issues

### Template loads but charts are empty

- Check the `start_date` - it may be after the series start
- Verify the frequency matches the series (e.g., don't use "quarterly" for monthly data)
- Some series have gaps or delays in reporting

## Advanced Features

### Multi-Series Charts (Future - Issue #8)

Note: Currently, each chart supports one series. Multi-series support is planned for Issue #8 of the upgrade epic.

### Multiple Data Sources (Future - Issue #9)

Note: Currently, only FRED data is supported. Additional sources (BLS, BEA, etc.) are planned for Issue #9.

## Resources

- **FRED Search**: https://fred.stlouisfed.org/
- **JSON Validator**: https://jsonlint.com/
- **MacroBuilder Docs**: See other files in `docs/` folder
- **Issue Tracker**: GitHub issues for feature requests

## Support

If you create a useful template, consider contributing it back to the project via a pull request!

For questions or issues:
1. Check the template JSON syntax
2. Review error messages carefully
3. Test with a smaller template first
4. Open an issue on GitHub with the template file attached
