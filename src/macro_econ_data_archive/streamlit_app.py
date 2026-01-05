#!/usr/bin/env python3
"""
streamlit_app.py - MacroBuilder Streamlit Application

A dynamic, interactive application for creating custom economic reports with AI-powered insights.
"""

import os
import io
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI

# Import utilities from our refactored module
from .macro_utils import (
    fetch_fred,
    build_series_for_chart,
    yoy,
    qoq_saar,
    infer_yoy_periods
)

# Import PDF generation from original script
from .report_generator import assemble_pdf


# --------------------------
# Configuration
# --------------------------

st.set_page_config(
    page_title="MacroBuilder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------
# Data Classes
# --------------------------

@dataclass
class SeriesInfo:
    """Information for a single series in a chart."""
    id: str
    label: str

@dataclass
class ChartConfig:
    """Configuration for a single chart in the report (supports multiple series)."""
    title: str
    series: List[SeriesInfo]  # List of series to plot on this chart
    frequency: str  # "monthly", "quarterly", "weekly", "daily"
    transform: str  # "level", "yoy", "qoq_saar"
    units: str
    data: Optional[pd.DataFrame] = None
    narrative: str = ""


# --------------------------
# Session State Initialization
# --------------------------

def init_session_state():
    """Initialize session state variables."""
    if 'charts' not in st.session_state:
        st.session_state.charts = []
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = os.getenv('OPENAI_API_KEY', '')
    if 'report_title' not in st.session_state:
        st.session_state.report_title = "Macro Economic Data Archive"
    if 'start_date' not in st.session_state:
        st.session_state.start_date = "2010-01-01"


# --------------------------
# AI Integration
# --------------------------

def generate_narrative(data_summary: str, series_name: str, api_key: str, model: str = "gpt-4o-mini") -> str:
    """
    Generate professional economic analysis using ChatGPT 4o-mini.
    
    Args:
        data_summary: Recent data in CSV or markdown table format
        series_name: Name of the economic series being analyzed
        api_key: OpenAI API key
        model: Model to use (default: gpt-4o-mini)
    
    Returns:
        Generated narrative text
    """
    try:
        client = OpenAI(api_key=api_key)
        
        system_prompt = """You are a Chief Macro Economist with expertise in economic data analysis. 
Your writing style matches that of Federal Reserve publications and top-tier investment bank strategy notes.

When analyzing data:
- Identify key trends, peaks, troughs, and recent momentum
- Use precise, professional language (avoid hyperbole like "skyrocketed" or "plummeted")
- Prefer passive voice where appropriate for formality
- Be concise and data-driven
- Reference specific values and time periods
- Avoid conversational fillers

Keep analysis to 2-3 paragraphs maximum."""

        user_prompt = f"""Analyze the following economic data for {series_name}.

Recent Data:
{data_summary}

Provide a professional analysis highlighting:
1. Current level and recent trend
2. Notable peaks, troughs, or inflection points in the recent period
3. The momentum and directional bias

Keep it professional and concise."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Error generating narrative: {str(e)}"


# --------------------------
# Chart Visualization
# --------------------------

def create_plotly_chart(chart_config: ChartConfig) -> go.Figure:
    """
    Create an interactive Plotly chart from chart configuration.
    Supports multiple series on the same chart.
    
    Args:
        chart_config: Chart configuration with data
    
    Returns:
        Plotly figure object
    """
    if chart_config.data is None or chart_config.data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    fig = go.Figure()
    
    # Add trace for each series
    for series_info in chart_config.series:
        if series_info.id in chart_config.data.columns:
            fig.add_trace(go.Scatter(
                x=chart_config.data.index,
                y=chart_config.data[series_info.id],
                mode='lines',
                name=series_info.label,
                line=dict(width=2)
            ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=chart_config.title,
            font=dict(size=18, family="Arial, sans-serif")
        ),
        xaxis_title="",
        yaxis_title=chart_config.units,
        hovermode='x unified',
        template='plotly_white',
        height=500,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    # Add grid
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')
    
    return fig


def save_plotly_as_png(fig: go.Figure, output_path: Path) -> None:
    """
    Save Plotly figure as PNG for PDF export.
    
    Args:
        fig: Plotly figure
        output_path: Path to save PNG file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(output_path), width=1050, height=650, scale=2)


# --------------------------
# Data Preparation
# --------------------------

def prepare_data_summary(df: pd.DataFrame, series_list: List[SeriesInfo], periods: int = 24) -> str:
    """
    Prepare recent data summary for LLM context (supports multiple series).
    
    Args:
        df: DataFrame with time series data
        series_list: List of series info objects
        periods: Number of recent periods to include (default: 24)
    
    Returns:
        Formatted data summary as markdown table
    """
    if df is None or df.empty or not series_list:
        return "No data available"
    
    # Build table with all series
    table_lines = ["| Date |"]
    
    # Add series labels as headers
    for series_info in series_list:
        if series_info.id in df.columns:
            table_lines[0] += f" {series_info.label} |"
    
    # Add separator row
    separator = "|------|"
    for series_info in series_list:
        if series_info.id in df.columns:
            separator += "-------|"
    table_lines.append(separator)
    
    # Get last N periods
    recent_data = df.tail(periods)
    
    if recent_data.empty:
        return "No data available"
    
    # Format each row
    for date, row in recent_data.iterrows():
        date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
        row_str = f"| {date_str} |"
        
        for series_info in series_list:
            if series_info.id in df.columns:
                value = row[series_info.id]
                if pd.notna(value):
                    row_str += f" {value:.2f} |"
                else:
                    row_str += " N/A |"
        
        table_lines.append(row_str)
    
    return "\n".join(table_lines)


# --------------------------
# UI Components
# --------------------------

def render_sidebar():
    """Render sidebar with chart builder and configuration."""
    st.sidebar.title("📊 MacroBuilder")
    st.sidebar.markdown("---")
    
    # Report configuration
    st.sidebar.subheader("Report Settings")
    st.session_state.report_title = st.sidebar.text_input(
        "Report Title",
        value=st.session_state.report_title
    )
    
    st.session_state.start_date = st.sidebar.text_input(
        "Start Date (YYYY-MM-DD)",
        value=st.session_state.start_date
    )
    
    st.sidebar.markdown("---")
    
    # OpenAI API Key
    st.sidebar.subheader("AI Settings")
    api_key = st.sidebar.text_input(
        "OpenAI API Key",
        value=st.session_state.openai_api_key,
        type="password",
        help="Required for AI-powered narrative generation"
    )
    st.session_state.openai_api_key = api_key
    
    st.sidebar.markdown("---")
    
    # Chart builder
    st.sidebar.subheader("Add New Chart")
    
    with st.sidebar.expander("Chart Configuration", expanded=False):
        chart_title = st.text_input("Chart Title", key="new_chart_title")
        
        # Initialize series list in session state if not present
        if 'chart_builder_series' not in st.session_state:
            st.session_state.chart_builder_series = []
        
        st.markdown("**Series to Include:**")
        
        # Show current series list
        if st.session_state.chart_builder_series:
            for idx, (sid, slabel) in enumerate(st.session_state.chart_builder_series):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(f"{slabel} ({sid})")
                with col2:
                    if st.button("🗑️", key=f"remove_series_{idx}"):
                        st.session_state.chart_builder_series.pop(idx)
                        st.rerun()
        else:
            st.info("No series added yet. Add at least one series below.")
        
        # Add series inputs
        st.markdown("**Add Series:**")
        series_id = st.text_input(
            "FRED Series ID",
            key="new_series_id",
            help="e.g., GDPC1, UNRATE, CPIAUCSL"
        )
        series_label = st.text_input("Series Label", key="new_series_label")
        
        if st.button("➕ Add Series to List", use_container_width=True):
            if series_id and series_label:
                st.session_state.chart_builder_series.append((series_id, series_label))
                st.rerun()
            else:
                st.error("Please enter both Series ID and Label")
        
        st.markdown("---")
        
        # Chart settings
        col1, col2 = st.columns(2)
        with col1:
            frequency = st.selectbox(
                "Frequency",
                ["monthly", "quarterly", "weekly", "daily"],
                key="new_frequency"
            )
        
        with col2:
            transform = st.selectbox(
                "Transform",
                ["level", "yoy", "qoq_saar"],
                key="new_transform"
            )
        
        units = st.text_input("Units", key="new_units")
        
        if st.button("📊 Create Chart", use_container_width=True):
            if chart_title and st.session_state.chart_builder_series:
                add_chart_to_report(
                    chart_title,
                    st.session_state.chart_builder_series,
                    frequency, transform, units
                )
                # Clear the series list after adding chart
                st.session_state.chart_builder_series = []
            elif not chart_title:
                st.error("Please enter a chart title")
            else:
                st.error("Please add at least one series")
    
    st.sidebar.markdown("---")
    
    # Quick examples (single-series for simplicity, but can easily be extended)
    st.sidebar.subheader("Quick Add Examples")
    if st.sidebar.button("📈 Real GDP Growth", use_container_width=True):
        add_chart_to_report(
            "Real GDP Growth (Quarter over Quarter, Annualized)",
            [("GDPC1", "Real GDP")],
            "quarterly",
            "qoq_saar",
            "Percent"
        )
    
    if st.sidebar.button("📊 Real Consumer Spending", use_container_width=True):
        add_chart_to_report(
            "Real Consumer Spending (Year-over-Year)",
            [("PCEC96", "Real Personal Consumption Expenditures")],
            "monthly",
            "yoy",
            "Percent"
        )
    
    if st.sidebar.button("💰 Federal Debt to GDP", use_container_width=True):
        add_chart_to_report(
            "Federal Debt as Percent of GDP",
            [("GFDEGDQ188S", "Federal Debt to GDP")],
            "quarterly",
            "level",
            "Percent of GDP"
        )
    
    # Multi-series example
    if st.sidebar.button("📉 Fed Funds vs 10Y Treasury", use_container_width=True):
        add_chart_to_report(
            "Federal Funds Rate vs 10-Year Treasury Yield",
            [("FEDFUNDS", "Federal Funds Rate"), ("GS10", "10-Year Treasury")],
            "monthly",
            "level",
            "Percent"
        )


def add_chart_to_report(title: str, series_list: List[tuple], frequency: str, transform: str, units: str):
    """
    Add a new chart to the report.
    
    Args:
        title: Chart title
        series_list: List of (series_id, series_label) tuples
        frequency: Data frequency
        transform: Transformation to apply
        units: Y-axis units
    """
    try:
        # Extract series IDs
        series_ids = [s[0] for s in series_list]
        
        # Fetch data for all series
        with st.spinner(f"Fetching data for {len(series_ids)} series..."):
            raw_data = fetch_fred(series_ids, start=st.session_state.start_date)
            transformed_data = build_series_for_chart(
                raw_data, transform, frequency
            ).dropna(how="all")
        
        if transformed_data.empty:
            st.error(f"No data available for any of the series")
            return
        
        # Create SeriesInfo objects
        series_info_list = [SeriesInfo(id=s[0], label=s[1]) for s in series_list]
        
        # Create chart config
        chart = ChartConfig(
            title=title,
            series=series_info_list,
            frequency=frequency,
            transform=transform,
            units=units,
            data=transformed_data,
            narrative=""
        )
        
        st.session_state.charts.append(chart)
        st.success(f"✅ Added: {title}")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error adding chart: {str(e)}")


def render_main_area():
    """Render main content area with tabs."""
    if not st.session_state.charts:
        st.info("👈 Use the sidebar to add charts to your report")
        st.markdown("""
        ### Welcome to MacroBuilder!
        
        **MacroBuilder** is an interactive tool for creating custom economic reports with:
        - 📊 **Dynamic Charts**: Pull data from FRED and visualize with interactive Plotly charts
        - 🤖 **AI Analysis**: Generate professional economic narratives using ChatGPT 4o-mini
        - 📄 **PDF Export**: Download your complete report as a high-quality PDF
        
        #### Getting Started:
        1. Add your OpenAI API key in the sidebar (for AI features)
        2. Use the sidebar to add charts from FRED data
        3. Generate AI analysis for each chart
        4. Export your report as PDF
        
        #### Quick Examples:
        Try the quick-add buttons in the sidebar to get started with common economic indicators!
        """)
        return
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["📊 Report Builder", "📄 Report Preview"])
    
    with tab1:
        render_builder_view()
    
    with tab2:
        render_preview_view()


def render_builder_view():
    """Render the interactive builder view."""
    st.subheader("Report Builder")
    st.markdown(f"**{len(st.session_state.charts)}** chart(s) in report")
    
    # Export button at top
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("📥 Export to PDF", use_container_width=True):
            export_to_pdf()
    with col2:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.charts = []
            st.rerun()
    
    st.markdown("---")
    
    # Render each chart
    for idx, chart in enumerate(st.session_state.charts):
        render_chart_card(idx, chart)


def render_chart_card(idx: int, chart: ChartConfig):
    """Render a single chart card with controls."""
    with st.container():
        st.markdown(f"### {idx + 1}. {chart.title}")
        
        # Control buttons
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 3])
        
        with col1:
            if st.button("🔼", key=f"up_{idx}", disabled=(idx == 0)):
                move_chart(idx, -1)
        
        with col2:
            if st.button("🔽", key=f"down_{idx}", 
                        disabled=(idx == len(st.session_state.charts) - 1)):
                move_chart(idx, 1)
        
        with col3:
            if st.button("🗑️", key=f"delete_{idx}"):
                delete_chart(idx)
        
        with col4:
            if st.button("🤖 Generate Analysis", key=f"generate_{idx}"):
                generate_analysis_for_chart(idx)
        
        # Chart visualization
        fig = create_plotly_chart(chart)
        st.plotly_chart(fig, use_container_width=True)
        
        # Show metadata
        with st.expander("Chart Details"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Series:**")
                for series_info in chart.series:
                    st.text(f"• {series_info.label} ({series_info.id})")
            with col2:
                st.metric("Frequency", chart.frequency)
            with col3:
                st.metric("Transform", chart.transform)
        
        # Narrative section
        st.markdown("**Economic Analysis:**")
        narrative = st.text_area(
            "Edit or generate narrative",
            value=chart.narrative,
            height=150,
            key=f"narrative_{idx}",
            placeholder="Click 'Generate Analysis' to create AI-powered narrative, or write your own..."
        )
        
        # Update narrative if changed
        if narrative != chart.narrative:
            st.session_state.charts[idx].narrative = narrative
        
        st.markdown("---")


def render_preview_view():
    """Render the report preview."""
    st.subheader("Report Preview")
    st.markdown(f"## {st.session_state.report_title}")
    st.markdown(f"*As of {datetime.today().strftime('%B %d, %Y')}*")
    st.markdown("---")
    
    for idx, chart in enumerate(st.session_state.charts):
        st.markdown(f"### {chart.title}")
        
        fig = create_plotly_chart(chart)
        st.plotly_chart(fig, use_container_width=True)
        
        if chart.narrative:
            st.markdown(chart.narrative)
        else:
            st.info("No analysis generated yet")
        
        st.markdown("---")


# --------------------------
# Chart Management
# --------------------------

def move_chart(idx: int, direction: int):
    """Move chart up (-1) or down (+1) in the list."""
    new_idx = idx + direction
    if 0 <= new_idx < len(st.session_state.charts):
        st.session_state.charts[idx], st.session_state.charts[new_idx] = \
            st.session_state.charts[new_idx], st.session_state.charts[idx]
        st.rerun()


def delete_chart(idx: int):
    """Delete chart at given index."""
    st.session_state.charts.pop(idx)
    st.rerun()


def generate_analysis_for_chart(idx: int):
    """Generate AI narrative for a specific chart."""
    if not st.session_state.openai_api_key:
        st.error("Please provide an OpenAI API key in the sidebar")
        return
    
    chart = st.session_state.charts[idx]
    
    with st.spinner("Generating analysis..."):
        # Prepare data summary
        data_summary = prepare_data_summary(
            chart.data,
            chart.series,
            periods=24
        )
        
        # Build series names for narrative prompt
        series_names = ", ".join([s.label for s in chart.series])
        
        # Generate narrative
        narrative = generate_narrative(
            data_summary,
            series_names,
            st.session_state.openai_api_key
        )
        
        # Update chart
        st.session_state.charts[idx].narrative = narrative
        st.rerun()


# --------------------------
# PDF Export
# --------------------------

def export_to_pdf():
    """Export current report to PDF."""
    if not st.session_state.charts:
        st.error("No charts to export")
        return
    
    try:
        with st.spinner("Generating PDF..."):
            # Create temporary directory for images
            tmpdir = Path("_charts_tmp")
            tmpdir.mkdir(exist_ok=True)
            
            # Save charts as static images
            png_paths = []
            for idx, chart in enumerate(st.session_state.charts):
                fig = create_plotly_chart(chart)
                png_path = tmpdir / f"chart_{idx:03d}.png"
                save_plotly_as_png(fig, png_path)
                png_paths.append(png_path)
            
            # Generate PDF
            output_path = tmpdir / "report.pdf"
            as_of = datetime.today().strftime("%B %d, %Y")
            assemble_pdf(
                st.session_state.report_title,
                as_of,
                png_paths,
                output_path
            )
            
            # Provide download
            with open(output_path, "rb") as f:
                pdf_bytes = f.read()
            
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=f"macro_report_{datetime.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
            
            st.success("✅ PDF generated successfully!")
    
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")


# --------------------------
# Main Application
# --------------------------

def main():
    """Main application entry point."""
    init_session_state()
    render_sidebar()
    render_main_area()


if __name__ == "__main__":
    main()
