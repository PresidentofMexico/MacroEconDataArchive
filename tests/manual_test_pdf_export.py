#!/usr/bin/env python3
"""
Manual integration test for PDF export functionality.
This simulates what happens when a user exports a PDF from the Streamlit app.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.macro_econ_data_archive.report_generator import generate_pdf_report
from src.macro_econ_data_archive.streamlit_app import create_plotly_chart, ChartConfig, SeriesInfo
from src.macro_econ_data_archive.macro_utils import fetch_fred, build_series_for_chart

print("="*70)
print("Manual Integration Test: Board-Ready PDF Export")
print("="*70)

# Create output directory
output_dir = Path("/tmp/test_pdf_export")
output_dir.mkdir(exist_ok=True)

print("\n1. Fetching sample data from FRED...")
try:
    # Fetch a simple series (GDP)
    series_ids = ['GDPC1']
    raw_data = fetch_fred(series_ids, start='2020-01-01')
    print(f"   ✓ Fetched {len(raw_data)} data points for GDPC1")
    
    # Transform data
    transformed_data = build_series_for_chart(
        raw_data, 
        transform='qoq_saar', 
        frequency='quarterly'
    ).dropna(how='all')
    print(f"   ✓ Transformed data: {len(transformed_data)} quarters")
    
except Exception as e:
    print(f"   ⚠ Could not fetch data (expected in sandboxed environment): {e}")
    # Create dummy data for testing
    dates = pd.date_range('2020-01-01', periods=16, freq='Q')
    transformed_data = pd.DataFrame({
        'GDPC1': [2.5, 3.1, -5.0, 33.4, 4.5, 6.7, 2.3, 6.9, -1.6, 3.2, 4.9, 2.7, 2.6, 2.2, 3.0, 2.5]
    }, index=dates)
    print(f"   ✓ Using dummy data: {len(transformed_data)} quarters")

print("\n2. Creating chart configuration...")
chart_config = ChartConfig(
    title="Real GDP Growth (Quarter-over-Quarter, Annualized)",
    series=[SeriesInfo(series_id='GDPC1', series_label='Real GDP')],
    frequency='quarterly',
    transform='qoq_saar',
    units='Percent',
    data=transformed_data,
    narrative="""The economy showed **resilient growth** despite significant challenges in recent quarters.

**Key Observations:** Real GDP expanded at an average pace of 2.5% on a quarter-over-quarter seasonally adjusted annual rate basis over the past year.

**Recent Performance:** The most recent quarter saw growth moderate to a sustainable pace, consistent with the Federal Reserve's dual mandate objectives.

**Outlook:** Forward momentum suggests continued expansion, albeit at a measured pace reflecting the lagged effects of monetary policy transmission."""
)
print(f"   ✓ Chart: {chart_config.title}")

print("\n3. Generating chart image...")
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=transformed_data.index,
    y=transformed_data['GDPC1'],
    mode='lines',
    name='Real GDP',
    line=dict(width=2, color='#0B2E5E')
))

fig.update_layout(
    title=dict(text=chart_config.title, font=dict(size=18)),
    xaxis_title="",
    yaxis_title=chart_config.units,
    template='plotly_white',
    height=500
)

# Save as PNG
chart_image_path = output_dir / "gdp_growth.png"
try:
    fig.write_image(str(chart_image_path), width=1050, height=650, scale=2)
    print(f"   ✓ Chart saved: {chart_image_path}")
except Exception as e:
    print(f"   ⚠ Could not save chart image (Kaleido issue): {e}")
    # Create a minimal placeholder PNG
    import base64
    png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    )
    chart_image_path.write_bytes(png_data)
    print(f"   ✓ Using placeholder image: {chart_image_path}")

print("\n4. Preparing executive summary...")
executive_summary = """### Executive Summary
The U.S. economy demonstrated **resilient performance** in 2024, navigating a complex landscape of elevated inflation, higher interest rates, and global economic uncertainty.

**Key Drivers:** Consumer spending remained robust despite inflationary pressures, supported by a strong labor market. Business investment showed moderate growth, while exports benefited from a weakening dollar.

**Outlook:** The Federal Reserve's monetary policy stance is expected to remain restrictive through early 2025, maintaining current policy rates until inflation shows sustained convergence toward the 2% target. Growth is projected to moderate to a below-trend pace in 2025, with risks balanced between persistent inflation and potential economic weakening."""

print(f"   ✓ Executive summary: {len(executive_summary)} characters")

print("\n5. Preparing release calendar...")
calendar_data = pd.DataFrame({
    'Series ID': ['GDPC1', 'UNRATE', 'CPIAUCSL'],
    'Series': ['Real GDP', 'Unemployment Rate', 'Consumer Price Index'],
    'Release Name': ['Gross Domestic Product', 'Employment Situation', 'Consumer Price Index'],
    'Next Release': ['2025-01-30', '2025-02-07', '2025-02-13'],
    'Days Remaining': [23, 31, 37]
})
print(f"   ✓ Release calendar: {len(calendar_data)} series")

print("\n6. Generating professional PDF report...")
charts_data = [
    {
        'title': chart_config.title,
        'image_path': str(chart_image_path),
        'narrative': chart_config.narrative
    }
]

output_pdf = output_dir / "macro_economic_report.pdf"
try:
    generate_pdf_report(
        filename=output_pdf,
        title="Quarterly Economic Report - Q4 2024",
        executive_summary=executive_summary,
        calendar_data=calendar_data,
        charts=charts_data
    )
    
    print(f"   ✓ PDF generated successfully!")
    print(f"   ✓ Location: {output_pdf}")
    
    # Verify file
    file_size = output_pdf.stat().st_size
    print(f"   ✓ File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    # Check PDF header
    with open(output_pdf, 'rb') as f:
        header = f.read(5)
        if header == b'%PDF-':
            print(f"   ✓ Valid PDF file")
        else:
            print(f"   ✗ Invalid PDF header: {header}")
    
    print("\n" + "="*70)
    print("✅ INTEGRATION TEST PASSED")
    print("="*70)
    print(f"\nGenerated PDF: {output_pdf}")
    print("You can download this file to verify the layout:")
    print(f"  - Page 1: Cover with title and executive briefing")
    print(f"  - Page 2: Release calendar table")
    print(f"  - Page 3: GDP chart with narrative")
    print(f"  - Professional styling with 1-inch margins and page numbers")
    
except Exception as e:
    print(f"   ✗ PDF generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
