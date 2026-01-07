# Save & Load Configuration Guide

This guide explains how to use the save and load configuration features in MacroBuilder to persist your work and share report configurations.

## Overview

The Save & Load feature allows you to:
- **Save** your current report configuration as a JSON file
- **Load** previously saved configurations to continue working
- **Share** configurations with colleagues
- **Version control** your report templates
- **Backup** your work before making changes

## Saving a Configuration

### Steps to Save

1. Build your report by adding charts in MacroBuilder
2. Locate the **💾 Save & Load** section in the sidebar
3. Click the **💾 Save Configuration** button
4. The file `macro_report_config.json` will be downloaded to your default downloads folder

### What Gets Saved

The configuration file includes:
- Report title
- All chart definitions:
  - Chart title (page_title)
  - Series IDs and labels
  - Frequency (monthly, quarterly, etc.)
  - Transform type (level, yoy, qoq_saar)
  - Units
  - Narrative text (notes)

### What Doesn't Get Saved

The following are **not** saved (intentionally):
- Raw data (DataFrame objects)
- Chart images
- API keys
- Cached data

This design ensures:
- Small, portable configuration files
- Fresh data when loading (always up-to-date)
- No sensitive data in saved files
- Easy version control compatibility

## Loading a Configuration

### Steps to Load

1. Locate the **💾 Save & Load** section in the sidebar
2. Click the **📂 Upload Configuration** file picker
3. Either:
   - **Drag and drop** your JSON file into the upload area
   - **Click "Browse files"** to select a file from your computer
4. Wait for the configuration to load and data to be fetched
5. Your report will be restored with fresh data from FRED

### Loading Behavior

- **Replaces current report**: Loading a configuration replaces all existing charts
- **Re-fetches data**: All data is fetched fresh from FRED using your current start date
- **Preserves narratives**: Any text you wrote is restored from the saved notes
- **Updates title**: The report title is restored from the configuration

### Load Time

Loading time depends on:
- Number of charts (typically 1-5 seconds per chart)
- Network speed
- FRED API response time
- Cache status (faster if series were recently fetched)

## Configuration File Format

### Schema

The JSON file follows this structure:

```json
{
  "report_title": "Your Report Title",
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
      "notes": "Your narrative text here"
    }
  ]
}
```

### Field Descriptions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `report_title` | string | Title of the report | "Q4 2025 Economic Analysis" |
| `charts` | array | List of chart configurations | `[{...}, {...}]` |
| `page_title` | string | Title displayed on the chart | "Real GDP Growth" |
| `series` | array | List of series in the chart | `[{"id": "GDPC1", "label": "Real GDP"}]` |
| `frequency` | string | Data frequency | "monthly", "quarterly", "weekly", "daily" |
| `transform` | string | Data transformation | "level", "yoy", "qoq_saar" |
| `units` | string | Y-axis label | "Percent", "Billions of Dollars", etc. |
| `notes` | string | Narrative/analysis text | "GDP growth accelerated..." |

### Multi-Series Charts

For charts with multiple series:

```json
{
  "page_title": "Inflation Comparison",
  "series": [
    {"id": "CPIAUCSL", "label": "Headline CPI"},
    {"id": "CPILFESL", "label": "Core CPI"},
    {"id": "PCEPI", "label": "PCE Price Index"}
  ],
  "frequency": "monthly",
  "transform": "yoy",
  "units": "Percent",
  "notes": "Headline inflation remains elevated..."
}
```

## Use Cases

### 1. Regular Report Updates

**Scenario**: You create a monthly economic update report.

**Workflow**:
1. Build your report structure once with all desired charts
2. Save the configuration as `monthly_report_template.json`
3. Each month:
   - Load the configuration
   - Data is automatically updated with latest FRED data
   - Generate new AI analysis
   - Export to PDF

**Benefit**: Consistent report structure with fresh data

### 2. Sharing with Team

**Scenario**: Share a report template with colleagues.

**Workflow**:
1. Create a comprehensive report with multiple charts
2. Add narrative text and analysis
3. Save configuration
4. Share the JSON file via email/Slack/Git
5. Colleagues load it in their MacroBuilder instance

**Benefit**: Consistent analysis across team

### 3. Version Control

**Scenario**: Track changes to your report structure over time.

**Workflow**:
1. Save configuration to a Git repository
2. Use descriptive names: `report_v1.0.json`, `report_v1.1.json`
3. Use Git to track changes, branches, and history
4. Revert to previous versions if needed

**Benefit**: Professional version control

### 4. A/B Testing Report Structures

**Scenario**: Test different chart combinations.

**Workflow**:
1. Create first version with certain charts
2. Save as `approach_A.json`
3. Modify the report structure
4. Save as `approach_B.json`
5. Load each to compare effectiveness

**Benefit**: Experiment without losing work

### 5. Backup Before Experiments

**Scenario**: Try new charts without losing current work.

**Workflow**:
1. Save current configuration as `backup.json`
2. Experiment with new charts and settings
3. If unhappy with changes, load `backup.json`
4. If happy, save a new version

**Benefit**: Safe experimentation

## Compatibility

### Template System

Saved configurations use the **same format** as template files in `config/templates/`. This means:

- You can save a custom report and use it as a template
- You can hand-edit saved configurations like templates
- Template files can be loaded via the upload feature
- Saved configurations can be placed in `config/templates/` for template dropdown

### Backward Compatibility

The format is compatible with:
- Single-series charts (legacy format)
- Multi-series charts (new format)
- All transform types (level, yoy, qoq_saar)
- All frequency types (monthly, quarterly, weekly, daily)

## Troubleshooting

### "Add charts to enable save"

**Problem**: The save button is disabled.

**Solution**: Add at least one chart to your report before saving.

---

### "Invalid JSON file"

**Problem**: File upload shows JSON error.

**Solution**: 
- Ensure the file is valid JSON (use [JSONLint](https://jsonlint.com/) to validate)
- Check for missing commas, quotes, or brackets
- Don't edit the file manually unless you're confident with JSON syntax

---

### "Error loading configuration"

**Problem**: File uploads but fails to load charts.

**Solution**:
- Check that series IDs are valid FRED series
- Verify your internet connection
- Check the browser console for detailed error messages
- Ensure transform and frequency values are valid

---

### "No data available"

**Problem**: Charts load but show "No data available".

**Solution**:
- Check the start date in sidebar (may be too recent for historical series)
- Verify the series ID exists in FRED
- Check if the series has been discontinued
- Try a different date range

---

### Load takes a long time

**Problem**: Configuration loads slowly.

**Solution**:
- Normal for reports with many charts (each fetches separately)
- Wait for all spinners to complete
- Check network connection
- Clear cache and try again if it seems stuck
- FRED API may be slow - try again later

## Best Practices

### Naming Conventions

Use descriptive, dated filenames:
- ✅ `monthly_report_2025_01.json`
- ✅ `inflation_analysis_v2.json`
- ✅ `gdp_employment_backup.json`
- ❌ `config.json`
- ❌ `report.json`
- ❌ `test.json`

### File Organization

Organize saved configurations:
```
reports/
├── templates/
│   ├── monthly_template.json
│   ├── quarterly_template.json
│   └── annual_template.json
├── 2025/
│   ├── january_report.json
│   ├── february_report.json
│   └── march_report.json
└── backups/
    └── pre_major_changes.json
```

### Documentation

Add a README.md alongside your configurations:
```markdown
# Report Configurations

- `monthly_template.json` - Standard monthly economic update
- `deep_dive.json` - Extended analysis with 15+ indicators
- `executive_summary.json` - High-level overview for executives
```

### Version Control

Commit configurations to Git with meaningful messages:
```bash
git add reports/monthly_report_2025_01.json
git commit -m "Add January 2025 monthly report configuration"
```

## Advanced Tips

### Combining Templates

Manually combine multiple saved configurations:
1. Save Configuration A
2. Save Configuration B
3. Open both JSON files in a text editor
4. Copy charts array from B into A's charts array
5. Save as `combined.json`
6. Load the combined configuration

### Customizing in Text Editor

You can manually edit saved configurations:
- Change chart titles
- Update series IDs
- Modify transforms or frequencies
- Add/remove series
- Update narrative text

**Warning**: Ensure JSON remains valid after editing.

### Creating Custom Templates

1. Build a report with your preferred charts
2. Save the configuration
3. Copy to `config/templates/` directory
4. It will appear in the template dropdown on next restart

## Security Considerations

### What's Safe to Share

✅ Saved configurations are safe to share because they contain:
- Public FRED series IDs
- Chart configurations
- Narrative text

### What to Keep Private

🔒 Never put in saved configurations:
- API keys (not saved automatically)
- Proprietary data sources
- Confidential analysis
- Sensitive company information

### Git Repositories

✅ Safe to commit to public repos:
- Configuration structure
- FRED series IDs
- General economic analysis

❌ Don't commit to public repos:
- Configurations with proprietary indicators
- Internal company analysis text
- Custom data sources

## Support

For issues with Save & Load:
- Check this guide first
- Review [AGENTS.md](../AGENTS.md) for architecture details
- Check [CHANGELOG.md](../CHANGELOG.md) for recent changes
- Open an issue on GitHub with your configuration file attached

## Examples

See `config/templates/` directory for example configurations:
- `core_macro.json` - 4 essential indicators
- `inflation_deep_dive.json` - 8 inflation measures
- `labor_markets.json` - 9 labor market indicators
