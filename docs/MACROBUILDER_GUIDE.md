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

#### Method A: Quick Add Examples (Single & Multi-Series)
Use the quick-add buttons in the sidebar:
- **📈 Real GDP Growth**: Adds quarterly real GDP growth data
- **📊 Real Consumer Spending**: Adds monthly consumer spending growth
- **💰 Federal Debt to GDP**: Adds federal debt ratio
- **📉 Fed Funds vs 10Y Treasury**: **NEW!** Multi-series chart comparing short-term and long-term rates

#### Method B: Custom Charts (Multi-Series Support!)
1. Click "Chart Configuration" in the sidebar to expand the form
2. **Add series to your chart:**
   - Enter **FRED Series ID** (e.g., `GDPC1`, `UNRATE`, `CPIAUCSL`)
     - Find series IDs at https://fred.stlouisfed.org/
   - Enter **Series Label** for the legend
   - Click **➕ Add Series to List**
   - Repeat for additional series (you can add multiple series to one chart!)
   - Use the 🗑️ button to remove a series from the list
3. **Configure chart settings:**
   - **Chart Title**: Descriptive title for your chart
   - **Frequency**: How often the data is reported (monthly, quarterly, etc.)
   - **Transform**: How to display the data:
     - `level`: Raw values
     - `yoy`: Year-over-year percent change
     - `qoq_saar`: Quarter-over-quarter seasonally adjusted annual rate
   - **Units**: Y-axis label (e.g., "Percent", "Billions of Dollars")
4. Click **📊 Create Chart** to add to your report

**Multi-Series Example Use Cases:**
- Compare Federal Funds Rate vs 10-Year Treasury Yield
- Overlay CPI inflation with Core CPI
- Compare GDP growth across multiple countries
- Plot unemployment rate vs labor force participation rate
- Compare different stock market indices

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
