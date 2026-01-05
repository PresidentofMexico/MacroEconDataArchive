# MacroBuilder User Guide

## Overview

**MacroBuilder** is an interactive Streamlit application that allows you to create custom economic reports with AI-powered insights. This guide will walk you through using the application.

## Prerequisites

1. **Python 3.7+** installed on your system
2. **Internet connection** to fetch data from FRED
3. **OpenAI API key** (for AI-powered narrative generation)

## Installation

```bash
# Clone the repository
git clone https://github.com/PresidentofMexico/MacroEconDataArchive.git
cd MacroEconDataArchive

# Install dependencies
pip install -r requirements.txt
```

## Getting Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (you won't be able to see it again)
5. Set it as an environment variable:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

## Starting the Application

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

## Using MacroBuilder

### 1. Initial Setup

When you first open the app:
- Enter your OpenAI API key in the sidebar (or it will be loaded from environment variable)
- Adjust the report title if desired
- Set the start date for historical data (default: 2010-01-01)

### 2. Adding Charts

#### Method A: Quick Add Examples
Use the quick-add buttons in the sidebar:
- **📈 Real GDP**: Adds quarterly real GDP data
- **📊 Unemployment Rate**: Adds monthly unemployment rate
- **💰 Inflation (YoY)**: Adds year-over-year inflation

#### Method B: Custom Charts
1. Click "Chart Configuration" in the sidebar to expand the form
2. Fill in the fields:
   - **Chart Title**: Descriptive title for your chart
   - **FRED Series ID**: The FRED identifier (e.g., `GDPC1`, `UNRATE`, `CPIAUCSL`)
     - Find series IDs at https://fred.stlouisfed.org/
   - **Series Label**: Label for the chart legend
   - **Frequency**: How often the data is reported (monthly, quarterly, etc.)
   - **Transform**: How to display the data:
     - `level`: Raw values
     - `yoy`: Year-over-year percent change
     - `qoq_saar`: Quarter-over-quarter seasonally adjusted annual rate
   - **Units**: Y-axis label (e.g., "Percent", "Billions of Dollars")
3. Click "➕ Add Chart to Report"

### 3. Working with Charts

Once charts are added, you can:

- **📊 View Charts**: See interactive Plotly visualizations with hover details
- **🔼 Move Up / 🔽 Move Down**: Reorder charts in your report
- **🗑️ Delete**: Remove a chart from the report
- **🤖 Generate Analysis**: Create AI-powered economic analysis

### 4. Generating AI Analysis

For each chart:
1. Click the **🤖 Generate Analysis** button
2. Wait a few seconds while the AI analyzes the data
3. The narrative appears below the chart
4. You can manually edit the narrative in the text box

The AI will:
- Analyze recent trends and momentum
- Identify peaks and troughs
- Provide professional, Fed-style commentary
- Reference specific data points

### 5. Viewing Your Report

Switch to the **📄 Report Preview** tab to see:
- Your complete report as it will appear
- All charts in order
- All narratives
- Professional formatting

### 6. Exporting to PDF

1. Go back to the **📊 Report Builder** tab
2. Click **📥 Export to PDF** at the top
3. Wait for PDF generation (may take 10-30 seconds)
4. Click **📥 Download PDF** when the button appears
5. Save your report

The PDF will include:
- Cover page with report title and date
- Each chart on its own page
- Professional header/footer design

## Tips and Best Practices

### Finding FRED Series IDs
1. Go to https://fred.stlouisfed.org/
2. Search for your economic indicator
3. The series ID is shown at the top of the data page
4. Common examples:
   - `GDPC1` - Real GDP
   - `UNRATE` - Unemployment Rate
   - `CPIAUCSL` - Consumer Price Index
   - `FEDFUNDS` - Federal Funds Rate
   - `DGS10` - 10-Year Treasury Rate
   - `PAYEMS` - Nonfarm Payrolls

### Transform Guidelines
- Use **level** for: Interest rates, unemployment rate, index levels
- Use **yoy** for: Inflation, wage growth, year-over-year comparisons
- Use **qoq_saar** for: GDP growth, quarterly economic indicators

### Frequency Settings
Match the frequency to your data:
- GDP data → `quarterly`
- CPI, employment → `monthly`
- Interest rates → `daily` or `monthly`

### AI Narrative Quality
For best results:
- Use descriptive chart titles
- Include clear series labels
- The AI analyzes the last 24 periods of data
- Edit the generated text to add your own insights

### Report Organization
- Start with big picture (GDP, employment)
- Then sector specifics
- End with forward-looking indicators (yield curve, etc.)

## Performance and Caching

### Data Caching
MacroBuilder automatically caches fetched FRED data to improve performance and reduce API load:

- **Cache Duration**: Data is cached for 1 hour (3600 seconds)
- **Cache Key**: Each series is cached by `(series_id, start_date)` combination
- **Automatic**: Caching happens transparently - no action needed
- **Benefits**:
  - Faster chart additions when reusing the same series
  - Reduced API calls to FRED
  - Better responsiveness when building reports with many charts

### Managing the Cache

**When to Clear Cache:**
- After updating the start date parameter
- When you need the most recent data (within the hour)
- If experiencing stale data issues

**How to Clear Cache:**
1. Look for the **⚡ Data Cache** section in the sidebar
2. Click the **🗑️** button
3. The cache will be cleared and fresh data will be fetched

### Reliability Features

**Automatic Retry Logic:**
MacroBuilder includes intelligent retry logic for FRED data fetching:
- **Network Errors**: Automatically retries up to 3 times with exponential backoff
- **Server Errors (5xx)**: Retries with increasing delays (2s, 4s, 8s)
- **Rate Limiting (403)**: Immediately shows friendly error message

**Error Messages:**
If you encounter errors, MacroBuilder provides clear guidance:
- **⚠️ FRED Rate Limit Reached**: Wait a few minutes before retrying
- **🔧 FRED Server Error**: FRED servers may be temporarily unavailable
- **❌ Other Errors**: Specific error details for troubleshooting

**Best Practices for Reliability:**
- Use the cache feature to minimize API calls
- Wait a few minutes between large batches of new series
- Clear cache only when necessary
- If rate limited, the cache will help you continue working with already-fetched data

## Troubleshooting

### "Series ID not found"
- Check that the FRED series ID is correct
- Verify the series exists at https://fred.stlouisfed.org/
- Some series may have been discontinued

### "No data available"
- Try a different start date (some series have limited history)
- Check that the frequency matches the data (e.g., quarterly data needs quarterly frequency)

### AI not generating narratives
- Verify your OpenAI API key is entered correctly
- Check that you have credits remaining in your OpenAI account
- Try again if there was a temporary API issue

### FRED Rate Limit Errors
If you see "⚠️ FRED Rate Limit Reached":
- **Wait**: FRED rate limits are temporary (usually 5-10 minutes)
- **Use Cache**: Previously fetched data remains available in cache
- **Batch Requests**: Add multiple charts at once rather than one-by-one rapidly
- **Note**: The cache helps prevent rate limiting by reusing data

### FRED Server Errors
If you see "🔧 FRED Server Error":
- The application automatically retried 3 times before showing this error
- FRED servers may be experiencing temporary issues
- Try again in a few minutes
- Check FRED status at https://fred.stlouisfed.org/

### PDF export fails
- Ensure all charts have valid data
- Check that kaleido is installed: `pip install kaleido`
- Try with fewer charts if memory is an issue

## Command Line Alternative

If you prefer automation, use the CLI tool:

```bash
python generate_macro_report.py --spec config/macro_chart_spec.json --out report.pdf
```

Edit `config/macro_chart_spec.json` to define your charts programmatically.

## Support and Contributions

- Report issues: https://github.com/PresidentofMexico/MacroEconDataArchive/issues
- View source: https://github.com/PresidentofMexico/MacroEconDataArchive

## License

This is a template for educational and research purposes. Please respect data source terms of use.
