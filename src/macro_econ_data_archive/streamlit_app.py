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
    infer_yoy_periods,
    get_series_release_info,
    FREDRateLimitError,
    FREDServerError
)

# Import PDF generation from report generator
from .report_generator import assemble_pdf, generate_pdf_report


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
    """Information about a single series in a chart."""
    series_id: str
    series_label: str


@dataclass
class ChartConfig:
    """Configuration for a single chart in the report."""
    title: str
    series: List[SeriesInfo]  # Now supports multiple series
    frequency: str  # "monthly", "quarterly", "weekly", "daily"
    transform: str  # "level", "yoy", "qoq_saar"
    units: str
    data: Optional[pd.DataFrame] = None
    narrative: str = ""

    # Legacy compatibility properties
    @property
    def series_id(self) -> str:
        """Get first series ID for backward compatibility."""
        return self.series[0].series_id if self.series else ""

    @property
    def series_label(self) -> str:
        """Get first series label for backward compatibility."""
        return self.series[0].series_label if self.series else ""


# --------------------------
# Session State Initialization
# --------------------------

def init_session_state():
    """Initialize session state variables."""
    if 'charts' not in st.session_state:
        st.session_state.charts = []
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = os.getenv('OPENAI_API_KEY', '')
    if 'fred_api_key' not in st.session_state:
        st.session_state.fred_api_key = os.getenv('FRED_API_KEY', '')
    if 'report_title' not in st.session_state:
        st.session_state.report_title = "Macro Economic Data Archive"
    if 'start_date' not in st.session_state:
        st.session_state.start_date = "2010-01-01"
    if 'executive_summary' not in st.session_state:
        st.session_state.executive_summary = ""


# --------------------------
# Data Fetching with Caching
# --------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fred_cached(series_ids: List[str], start: str) -> pd.DataFrame:
    """
    Cached wrapper for fetch_fred with 1-hour TTL.
    Canonicalizes series order to ensure consistent caching.

    Args:
        series_ids: List of FRED series IDs
        start: Start date in YYYY-MM-DD format

    Returns:
        DataFrame with fetched data (columns in sorted order by series ID)

    Raises:
        FREDRateLimitError: If rate limit exceeded
        FREDServerError: If server error persists

    Note:
        Series IDs are sorted alphabetically to ensure cache hits regardless
        of the order in which series are requested. This prevents cache
        fragmentation for semantically identical requests.
    """
    # Sort series IDs for cache consistency
    # ["PCEC96", "GDPC1"] and ["GDPC1", "PCEC96"] will use the same cache entry
    canonical_series_ids = sorted(series_ids)
    return fetch_fred(canonical_series_ids, start=start)


@st.cache_data(ttl=86400, show_spinner=False)
def get_series_release_info_cached(series_id: str, api_key: str) -> dict:
    """
    Cached wrapper for get_series_release_info with 24-hour TTL.
    
    Release schedules don't change frequently, so we cache for longer.
    
    Args:
        series_id: FRED series ID
        api_key: FRED API key
    
    Returns:
        Dictionary with release information
    """
    return get_series_release_info(series_id, api_key)


# --------------------------
# Template Loading
# --------------------------

def get_templates_dir() -> Path:
    """Get the templates directory path."""
    # Templates are in config/templates relative to repo root
    repo_root = Path(__file__).parent.parent.parent
    return repo_root / "config" / "templates"


def discover_templates() -> List[Dict]:
    """
    Discover available template files.

    Returns:
        List of template metadata dictionaries
    """
    templates_dir = get_templates_dir()
    if not templates_dir.exists():
        return []

    templates = []
    for template_file in sorted(templates_dir.glob("*.json")):
        try:
            with open(template_file, 'r') as f:
                template_data = json.load(f)

            # Extract metadata
            templates.append({
                'filename': template_file.name,
                'path': template_file,
                'title': template_data.get('report_title', template_file.stem),
                'description': template_data.get('description', 'No description'),
                'chart_count': len(template_data.get('charts', []))
            })
        except Exception as e:
            st.warning(f"Could not load template {template_file.name}: {e}")
            continue

    return templates


def load_template(template_path: Path) -> Dict:
    """
    Load a template JSON file.

    Args:
        template_path: Path to template JSON file

    Returns:
        Template data dictionary
    """
    with open(template_path, 'r') as f:
        return json.load(f)


def load_template_charts(template_data: Dict, start_date: str) -> List[ChartConfig]:
    """
    Load charts from template data into ChartConfig objects.

    Args:
        template_data: Template dictionary with 'charts' key
        start_date: Start date for data fetching

    Returns:
        List of ChartConfig objects with data loaded
    """
    charts = []

    for chart_spec in template_data.get('charts', []):
        try:
            # Extract series information
            series_list = []
            if 'series' in chart_spec:
                # Multi-series format
                for s in chart_spec['series']:
                    series_list.append(SeriesInfo(
                        series_id=s['id'],
                        series_label=s['label']
                    ))
            elif 'series_id' in chart_spec:
                # Legacy single-series format
                series_list.append(SeriesInfo(
                    series_id=chart_spec['series_id'],
                    series_label=chart_spec.get('series_label', chart_spec['series_id'])
                ))

            if not series_list:
                st.warning(f"Skipping chart with no series: {chart_spec.get('page_title', 'Unknown')}")
                continue

            # Fetch data for all series
            series_ids = [s.series_id for s in series_list]

            with st.spinner(f"Loading {chart_spec.get('page_title', 'chart')}..."):
                raw_data = fetch_fred_cached(series_ids, start=start_date)
                transformed_data = build_series_for_chart(
                    raw_data,
                    transform=chart_spec.get('transform', 'level'),
                    frequency=chart_spec.get('frequency', 'monthly')
                ).dropna(how='all')

            if transformed_data.empty:
                st.warning(f"No data for: {chart_spec.get('page_title', 'Unknown chart')}")
                continue

            # Create ChartConfig
            chart = ChartConfig(
                title=chart_spec.get('page_title', 'Untitled Chart'),
                series=series_list,
                frequency=chart_spec.get('frequency', 'monthly'),
                transform=chart_spec.get('transform', 'level'),
                units=chart_spec.get('units', ''),
                data=transformed_data,
                narrative=chart_spec.get('notes', '')
            )

            charts.append(chart)

        except FREDRateLimitError as e:
            st.error(f"FRED rate limit exceeded: {e}")
            break
        except FREDServerError as e:
            st.error(f"FRED server error: {e}")
            continue
        except Exception as e:
            st.error(f"Error loading chart '{chart_spec.get('page_title', 'Unknown')}': {e}")
            continue

    return charts


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


def generate_executive_summary(context_data: str, api_key: str, model: str = "gpt-4o-mini") -> str:
    """
    Generate holistic executive briefing using ChatGPT 4o-mini.
    
    Args:
        context_data: Aggregate data from all charts
        api_key: OpenAI API key
        model: Model to use (default: gpt-4o-mini)
    
    Returns:
        Generated executive briefing text
    """
    try:
        client = OpenAI(api_key=api_key)
        
        system_prompt = """You are the Chief Economist for a major central bank. You have been provided with a dashboard of key economic indicators. Write a 1-page 'Executive Briefing' summarizing the overall state of the economy. Structure your response as follows:

**Executive Summary:** A 2-3 sentence high-level thesis (e.g., 'The economy is cooling but remains resilient...').

**Key Drivers:** Synthesize the trends from the provided charts (e.g., connect Inflation falling to Interest Rate pauses).

**Outlook:** A cautious forward-looking statement based on the momentum.

Style: Professional, objective, dense (Federal Reserve Beige Book style). No flowery language."""
        
        user_prompt = f"""Here is the data for the current economic dashboard:

{context_data}"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Error generating executive summary: {str(e)}"


# --------------------------
# Chart Visualization
# --------------------------

def create_plotly_chart(chart_config: ChartConfig) -> go.Figure:
    """
    Create an interactive Plotly chart from chart configuration.
    Supports both single and multi-series charts.

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
    missing_series = []
    for series_info in chart_config.series:
        if series_info.series_id in chart_config.data.columns:
            fig.add_trace(go.Scatter(
                x=chart_config.data.index,
                y=chart_config.data[series_info.series_id],
                mode='lines',
                name=series_info.series_label,
                line=dict(width=2)
            ))
        else:
            missing_series.append(series_info.series_id)

    # Warn about missing series (important for debugging)
    if missing_series:
        st.warning(
            f"⚠️ Chart '{chart_config.title}': Missing data columns for series: {', '.join(missing_series)}. "
            f"These series will not appear in the chart."
        )

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
    Handles Kaleido installation issues gracefully.

    Args:
        fig: Plotly figure
        output_path: Path to save PNG file

    Raises:
        ImportError: If Kaleido is not properly installed
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.write_image(str(output_path), width=1050, height=650, scale=2)
    except Exception as e:
        error_str = str(e).lower()
        # Check for various Kaleido-related errors
        kaleido_keywords = ['kaleido', 'orca', 'image export', 'write_image']
        if any(keyword in error_str for keyword in kaleido_keywords):
            raise ImportError(
                "Kaleido is required for PDF export but not properly installed. "
                "Please reinstall with: pip install -U kaleido\n"
                f"Original error: {e}"
            ) from e
        # For other errors, provide more context
        raise RuntimeError(
            f"Failed to save chart as PNG for PDF export. "
            f"This may be due to missing system dependencies (e.g., chromium). "
            f"Error: {e}"
        ) from e


# --------------------------
# Data Preparation
# --------------------------

def prepare_data_summary(df: pd.DataFrame, series_list: List[SeriesInfo], periods: int = 24) -> str:
    """
    Prepare recent data summary for LLM context.
    Supports both single and multi-series data.

    Args:
        df: DataFrame with time series data
        series_list: List of SeriesInfo objects
        periods: Number of recent periods to include (default: 24)

    Returns:
        Formatted data summary as markdown table
    """
    if df is None or df.empty:
        return "No data available"

    # Get series IDs that exist in the dataframe
    available_series = [s for s in series_list if s.series_id in df.columns]

    if not available_series:
        return "No data available"

    # Get last N periods
    recent_data = df[[s.series_id for s in available_series]].dropna(how='all').tail(periods)

    if recent_data.empty:
        return "No data available"

    # Format as markdown table
    if len(available_series) == 1:
        # Single series - simple two-column table
        table_lines = ["| Date | Value |", "|------|-------|"]
        for date, row in recent_data.iterrows():
            date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
            value = row[available_series[0].series_id]
            if pd.notna(value):
                table_lines.append(f"| {date_str} | {value:.2f} |")
    else:
        # Multi-series - table with column for each series
        header = "| Date | " + " | ".join([s.series_label for s in available_series]) + " |"
        separator = "|------|" + "|".join(["-------" for _ in available_series]) + "|"
        table_lines = [header, separator]

        for date, row in recent_data.iterrows():
            date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
            values = []
            for s in available_series:
                value = row[s.series_id]
                values.append(f"{value:.2f}" if pd.notna(value) else "N/A")
            table_lines.append(f"| {date_str} | " + " | ".join(values) + " |")

    return "\n".join(table_lines)


def prepare_holistic_data_summary(charts: List[ChartConfig]) -> str:
    """
    Prepare holistic data summary from all charts for executive briefing.
    
    Args:
        charts: List of ChartConfig objects
    
    Returns:
        Formatted markdown string with all chart data summaries
    """
    if not charts:
        return "No charts available for analysis."
    
    summary_sections = []
    
    for idx, chart in enumerate(charts, 1):
        # Add section header
        summary_sections.append(f"### Chart {idx}: {chart.title}")
        
        # Add chart metadata
        summary_sections.append(f"**Transform:** {chart.transform} | **Frequency:** {chart.frequency} | **Units:** {chart.units}")
        summary_sections.append("")
        
        # Add data table (limited to 12 periods to save tokens)
        data_table = prepare_data_summary(chart.data, chart.series, periods=12)
        summary_sections.append(data_table)
        summary_sections.append("")
    
    return "\n".join(summary_sections)


# --------------------------
# Save/Load Configuration
# --------------------------

def save_current_configuration() -> str:
    """
    Save the current report configuration to JSON format.

    Returns:
        JSON string representing the current report configuration

    Note:
        Only saves chart definitions (not raw data), which can be
        re-fetched when loading the configuration.
    """
    config = {
        "report_title": st.session_state.report_title,
        "charts": []
    }

    # Convert each ChartConfig to JSON format matching template schema
    for chart in st.session_state.charts:
        chart_dict = {
            "page_title": chart.title,
            "series": [
                {"id": s.series_id, "label": s.series_label}
                for s in chart.series
            ],
            "frequency": chart.frequency,
            "transform": chart.transform,
            "units": chart.units,
            "notes": chart.narrative  # Save narrative as notes
        }
        config["charts"].append(chart_dict)

    return json.dumps(config, indent=2)


def load_configuration_from_json(json_data: dict):
    """
    Load a configuration from parsed JSON data.

    Args:
        json_data: Parsed JSON configuration data

    Note:
        This function reuses the existing load_template_charts function
        to fetch data and create ChartConfig objects.
    """
    try:
        # Update report title if specified
        if 'report_title' in json_data:
            st.session_state.report_title = json_data['report_title']

        # Load all charts from configuration
        with st.spinner("Loading configuration and fetching data..."):
            charts = load_template_charts(json_data, st.session_state.start_date)

        if charts:
            st.session_state.charts = charts
            st.success(f"✅ Loaded {len(charts)} chart(s) from configuration")
            st.rerun()
        else:
            st.warning("No charts could be loaded from configuration")

    except Exception as e:
        st.error(f"Error loading configuration: {str(e)}")


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

    # API Keys
    st.sidebar.subheader("🔑 API Keys")
    
    # OpenAI API Key
    openai_key = st.sidebar.text_input(
        "OpenAI API Key",
        value=st.session_state.openai_api_key,
        type="password",
        help="Required for AI-powered narrative generation"
    )
    st.session_state.openai_api_key = openai_key
    
    # FRED API Key
    fred_key = st.sidebar.text_input(
        "FRED API Key",
        value=st.session_state.fred_api_key,
        type="password",
        help="Required for Release Calendar feature. Get free key at https://fred.stlouisfed.org/docs/api/api_key.html"
    )
    st.session_state.fred_api_key = fred_key

    st.sidebar.markdown("---")

    # Template loading
    st.sidebar.subheader("📋 Load Template")
    templates = discover_templates()

    if templates:
        template_options = {t['title']: t for t in templates}
        selected_template = st.sidebar.selectbox(
            "Choose a template",
            options=["-- Select Template --"] + list(template_options.keys()),
            key="template_selector"
        )

        if selected_template != "-- Select Template --":
            template_info = template_options[selected_template]
            st.sidebar.markdown(f"**Description:** {template_info['description']}")
            st.sidebar.markdown(f"**Charts:** {template_info['chart_count']}")

            # If there are existing charts, let user choose replace vs append
            if st.session_state.charts:
                col1, col2 = st.sidebar.columns(2)
                with col1:
                    if st.button("📥 Replace", use_container_width=True, help="Replace all existing charts"):
                        load_template_into_report(template_info['path'], replace_existing=True)
                with col2:
                    if st.button("➕ Append", use_container_width=True, help="Add to existing charts"):
                        load_template_into_report(template_info['path'], replace_existing=False)
            else:
                if st.sidebar.button("📥 Load Template", use_container_width=True):
                    load_template_into_report(template_info['path'], replace_existing=False)
    else:
        st.sidebar.info("No templates found in config/templates/")

    st.sidebar.markdown("---")

    # Save & Load Configuration
    st.sidebar.subheader("💾 Save & Load")

    # Save configuration
    if st.session_state.charts:
        config_json = save_current_configuration()
        st.sidebar.download_button(
            label="💾 Save Configuration",
            data=config_json,
            file_name="macro_report_config.json",
            mime="application/json",
            use_container_width=True,
            help="Download current report configuration as JSON"
        )
    else:
        st.sidebar.info("Add charts to enable save")

    # Load configuration
    uploaded_file = st.sidebar.file_uploader(
        "📂 Upload Configuration",
        type=['json'],
        help="Load a previously saved report configuration",
        key="config_uploader"
    )

    if uploaded_file is not None:
        try:
            # Parse JSON from uploaded file
            json_data = json.load(uploaded_file)
            load_configuration_from_json(json_data)
        except json.JSONDecodeError as e:
            st.sidebar.error(f"Invalid JSON file: {e}")
        except Exception as e:
            st.sidebar.error(f"Error loading file: {e}")

    st.sidebar.markdown("---")

    # Cache management
    st.sidebar.subheader("⚙️ Settings")
    if st.sidebar.button("🔄 Clear Data Cache", use_container_width=True):
        fetch_fred_cached.clear()
        get_series_release_info_cached.clear()
        st.sidebar.success("Cache cleared!")

    st.sidebar.markdown("---")

    # Chart builder
    st.sidebar.subheader("Add New Chart")

    with st.sidebar.expander("Chart Configuration", expanded=False):
        chart_title = st.text_input("Chart Title", key="new_chart_title")
        series_input = st.text_area(
            "Series List (One per line)",
            key="new_series_input",
            help="Format: SeriesID, Label\nExample:\nGDPC1, Real GDP\nPCEC96, Real PCE\nUNRATE, Unemployment Rate",
            placeholder="GDPC1, Real GDP\nPCEC96, Real PCE",
            height=100
        )

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

        if st.button("➕ Add Chart to Report", use_container_width=True):
            if chart_title and series_input:
                add_chart_to_report(
                    chart_title, series_input,
                    frequency, transform, units
                )
            else:
                st.error("Please fill in Chart Title and at least one series")

    st.sidebar.markdown("---")

    # Quick examples
    st.sidebar.subheader("Quick Add Examples")
    if st.sidebar.button("📈 Real GDP Growth", use_container_width=True):
        add_chart_to_report(
            "Real GDP Growth (Quarter over Quarter, Annualized)",
            "GDPC1, Real GDP",
            "quarterly",
            "qoq_saar",
            "Percent"
        )

    if st.sidebar.button("📊 Real Consumer Spending", use_container_width=True):
        add_chart_to_report(
            "Real Consumer Spending (Year-over-Year)",
            "PCEC96, Real Personal Consumption Expenditures",
            "monthly",
            "yoy",
            "Percent"
        )

    if st.sidebar.button("💰 Federal Debt to GDP", use_container_width=True):
        add_chart_to_report(
            "Federal Debt as Percent of GDP",
            "GFDEGDQ188S, Federal Debt to GDP",
            "quarterly",
            "level",
            "Percent of GDP"
        )


def add_chart_to_report(title: str, series_input: str,
                       frequency: str, transform: str, units: str):
    """
    Add a new chart to the report with one or more series.

    Args:
        title: Chart title
        series_input: Multi-line string with format "SeriesID, Label" per line
        frequency: Data frequency (monthly, quarterly, etc.)
        transform: Transform type (level, yoy, qoq_saar)
        units: Units label for the chart
    """
    try:
        # Parse series input
        series_list = []
        series_ids = []

        for line in series_input.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            # Split by first comma
            parts = line.split(',', 1)
            if len(parts) == 2:
                series_id = parts[0].strip()
                series_label = parts[1].strip()

                if series_id and series_label:
                    series_list.append(SeriesInfo(series_id=series_id, series_label=series_label))
                    series_ids.append(series_id)

        # Validate that we have at least one series
        if not series_list:
            st.error("Please provide at least one valid series in the format: SeriesID, Label")
            return

        # Fetch data using cached wrapper
        with st.spinner(f"Fetching data for {len(series_ids)} series..."):
            raw_data = fetch_fred_cached(series_ids, start=st.session_state.start_date)
            transformed_data = build_series_for_chart(
                raw_data, transform, frequency
            ).dropna(how="all")

        if transformed_data.empty:
            st.error(f"No data available for the requested series")
            return

        # Create chart config with multi-series format
        chart = ChartConfig(
            title=title,
            series=series_list,
            frequency=frequency,
            transform=transform,
            units=units,
            data=transformed_data,
            narrative=""
        )

        st.session_state.charts.append(chart)
        st.success(f"✅ Added: {title} ({len(series_list)} series)")
        st.rerun()

    except FREDRateLimitError as e:
        st.error(f"FRED rate limit exceeded: {e}")
    except FREDServerError as e:
        st.error(f"FRED server error: {e}")
    except Exception as e:
        st.error(f"Error adding chart: {str(e)}")


def load_template_into_report(template_path: Path, replace_existing: bool = False):
    """
    Load charts from a template file into the current report.

    Args:
        template_path: Path to the template JSON file
        replace_existing: If True, replace existing charts. If False, append.
    """
    try:
        with st.spinner("Loading template..."):
            # Load template data
            template_data = load_template(template_path)

            # Update report title if specified in template
            if 'report_title' in template_data:
                st.session_state.report_title = template_data['report_title']

            # Load all charts from template
            charts = load_template_charts(template_data, st.session_state.start_date)

            if charts:
                # Replace or append based on parameter
                if replace_existing or not st.session_state.charts:
                    st.session_state.charts = charts
                    action = "Loaded"
                else:
                    st.session_state.charts.extend(charts)
                    action = "Appended"

                st.success(f"✅ {action} {len(charts)} chart(s) from template")
                st.rerun()
            else:
                st.warning("No charts could be loaded from template")

    except Exception as e:
        st.error(f"Error loading template: {str(e)}")


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
    tab1, tab2, tab3 = st.tabs(["📊 Report Builder", "📄 Report Preview", "📅 Release Calendar"])

    with tab1:
        render_builder_view()

    with tab2:
        render_preview_view()
    
    with tab3:
        render_calendar_view()


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
        st.plotly_chart(fig, use_container_width=True, key=f"chart_builder_{idx}")

        # Show metadata
        with st.expander("Chart Details"):
            col1, col2, col3 = st.columns(3)
            with col1:
                # Show all series IDs
                series_ids = ", ".join([s.series_id for s in chart.series])
                st.metric("Series ID(s)", series_ids if len(series_ids) < 40 else f"{len(chart.series)} series")
            with col2:
                st.metric("Frequency", chart.frequency)
            with col3:
                st.metric("Transform", chart.transform)

            # If multiple series, show them in a list
            if len(chart.series) > 1:
                st.markdown("**Series in this chart:**")
                for s in chart.series:
                    st.markdown(f"- {s.series_label} ({s.series_id})")

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
    
    # Executive Briefing Controls at the top
    if st.session_state.charts:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("📝 Generate Executive Briefing", use_container_width=True, type="primary"):
                generate_executive_briefing()
        
        with col2:
            if st.session_state.executive_summary:
                if st.button("🗑️ Clear Briefing", use_container_width=True):
                    st.session_state.executive_summary = ""
                    st.rerun()
        
        # Display Executive Summary if available
        if st.session_state.executive_summary:
            st.markdown("### 🎯 Executive Briefing: State of the Economy")
            # Use a styled container for the summary
            st.info(st.session_state.executive_summary)
            st.markdown("---")
    
    st.markdown(f"## {st.session_state.report_title}")
    st.markdown(f"*As of {datetime.today().strftime('%B %d, %Y')}*")
    st.markdown("---")

    for idx, chart in enumerate(st.session_state.charts):
        st.markdown(f"### {chart.title}")

        fig = create_plotly_chart(chart)
        st.plotly_chart(fig, use_container_width=True, key=f"chart_preview_{idx}")

        if chart.narrative:
            st.markdown(chart.narrative)
        else:
            st.info("No analysis generated yet")

        st.markdown("---")


def render_calendar_view():
    """Render the release calendar showing next update dates for all series."""
    st.subheader("📅 Release Calendar")
    
    # Check if FRED API key is available
    if not st.session_state.fred_api_key:
        st.warning("⚠️ Please provide a FRED API key in the sidebar to view release schedules")
        st.info("""
        **How to get a FRED API key:**
        1. Visit https://fred.stlouisfed.org/docs/api/api_key.html
        2. Register for a free account
        3. Generate your API key
        4. Enter it in the sidebar under "API Keys"
        
        The Release Calendar feature shows you when the economic data in your report will be updated next.
        """)
        return
    
    # Check if there are any charts
    if not st.session_state.charts:
        st.info("👈 Add charts to your report to see their release schedules")
        return
    
    st.markdown("""
    This calendar shows the next scheduled release dates for all economic indicators in your report.
    Data is fetched from the FRED API and shows when each series will be updated.
    """)
    
    # Extract unique series IDs from all charts
    unique_series = set()
    series_info_map = {}  # Map series_id to its label
    
    for chart in st.session_state.charts:
        for series in chart.series:
            unique_series.add(series.series_id)
            series_info_map[series.series_id] = series.series_label
    
    series_list = sorted(unique_series)
    
    # Fetch release info for each series
    st.markdown(f"**Fetching release schedules for {len(series_list)} unique series...**")
    
    # Use progress bar for better UX
    progress_bar = st.progress(0)
    release_data = []
    
    for idx, series_id in enumerate(series_list):
        # Update progress
        progress = (idx + 1) / len(series_list)
        progress_bar.progress(progress)
        
        # Fetch release info (cached)
        try:
            info = get_series_release_info_cached(series_id, st.session_state.fred_api_key)
            
            # Calculate days remaining if we have a valid date
            next_date = info.get('next_release_date', 'TBD')
            if next_date != 'TBD':
                try:
                    release_date = pd.to_datetime(next_date)
                    today = pd.Timestamp.now().normalize()
                    days_remaining = (release_date - today).days
                except:
                    days_remaining = None
            else:
                days_remaining = None
            
            release_data.append({
                'Series ID': series_id,
                'Series': series_info_map.get(series_id, series_id),
                'Release Name': info.get('release_name', 'Unknown'),
                'Next Release': next_date,
                'Days Remaining': days_remaining if days_remaining is not None else 'N/A'
            })
        except Exception as e:
            # Handle errors gracefully
            release_data.append({
                'Series ID': series_id,
                'Series': series_info_map.get(series_id, series_id),
                'Release Name': 'Error',
                'Next Release': 'TBD',
                'Days Remaining': 'N/A'
            })
    
    # Clear progress bar
    progress_bar.empty()
    
    # Create DataFrame
    if release_data:
        df = pd.DataFrame(release_data)
        
        # Sort by next release date (put TBD at the end)
        def sort_key(row):
            if row['Next Release'] == 'TBD':
                return (1, '')  # TBD comes last
            else:
                return (0, row['Next Release'])
        
        df['_sort_key'] = df.apply(sort_key, axis=1)
        df = df.sort_values('_sort_key').drop('_sort_key', axis=1)
        
        st.markdown("---")
        
        # Display summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            scheduled_count = len([r for r in release_data if r['Next Release'] != 'TBD'])
            st.metric("Scheduled Releases", scheduled_count)
        with col2:
            upcoming_7d = len([r for r in release_data 
                             if isinstance(r['Days Remaining'], int) and r['Days Remaining'] <= 7])
            st.metric("Within 7 Days", upcoming_7d)
        with col3:
            tbd_count = len([r for r in release_data if r['Next Release'] == 'TBD'])
            st.metric("TBD/Irregular", tbd_count)
        
        st.markdown("---")
        
        # Highlight rows with releases in next 7 days
        def highlight_upcoming(row):
            if isinstance(row['Days Remaining'], int) and row['Days Remaining'] <= 7 and row['Days Remaining'] >= 0:
                return ['background-color: #ffcccc'] * len(row)
            return [''] * len(row)
        
        # Display the table with styling
        styled_df = df.style.apply(highlight_upcoming, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Add legend
        st.markdown("""
        **Legend:**
        - 🔴 **Highlighted rows**: Releases scheduled within the next 7 days
        - **TBD**: No regular release schedule or future date not available
        - **Days Remaining**: Number of days until next release (from today)
        """)
    else:
        st.warning("Could not fetch release information")


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
        # Prepare data summary with multi-series support
        data_summary = prepare_data_summary(
            chart.data,
            chart.series,
            periods=24
        )

        # Generate narrative (use first series label for context)
        series_name = chart.series[0].series_label if chart.series else "Economic Indicator"
        narrative = generate_narrative(
            data_summary,
            series_name,
            st.session_state.openai_api_key
        )

        # Update chart
        st.session_state.charts[idx].narrative = narrative
        # Force the text area widget to update its display value
        if f"narrative_{idx}" in st.session_state:
            st.session_state[f"narrative_{idx}"] = narrative
        st.rerun()


def generate_executive_briefing():
    """Generate holistic executive briefing from all charts."""
    if not st.session_state.openai_api_key:
        st.error("Please provide an OpenAI API key in the sidebar")
        return
    
    if not st.session_state.charts:
        st.error("No charts available for analysis")
        return
    
    with st.spinner("Generating Executive Briefing... This may take a moment."):
        # Prepare holistic data summary from all charts
        context_data = prepare_holistic_data_summary(st.session_state.charts)
        
        # Generate executive summary
        executive_summary = generate_executive_summary(
            context_data,
            st.session_state.openai_api_key
        )
        
        # Update session state
        st.session_state.executive_summary = executive_summary
        st.rerun()


# --------------------------
# PDF Export
# --------------------------

def export_to_pdf():
    """Export current report to PDF with executive summary and release calendar."""
    if not st.session_state.charts:
        st.error("No charts to export")
        return

    try:
        with st.spinner("Generating professional PDF report..."):
            # Create temporary directory for images
            tmpdir = Path("_charts_tmp")
            tmpdir.mkdir(exist_ok=True)

            # Step 1: Prepare chart data (images + narratives)
            charts_data = []
            for idx, chart in enumerate(st.session_state.charts):
                # Save chart as PNG
                fig = create_plotly_chart(chart)
                png_path = tmpdir / f"chart_{idx:03d}.png"
                save_plotly_as_png(fig, png_path)
                
                # Collect chart info
                charts_data.append({
                    'title': chart.title,
                    'image_path': str(png_path),
                    'narrative': chart.narrative or ""
                })

            # Step 2: Get executive summary from session state
            executive_summary = st.session_state.executive_summary or ""

            # Step 3: Prepare release calendar data
            calendar_df = None
            if st.session_state.fred_api_key:
                try:
                    # Extract unique series IDs from all charts
                    unique_series = set()
                    series_info_map = {}
                    
                    for chart in st.session_state.charts:
                        for series in chart.series:
                            unique_series.add(series.series_id)
                            series_info_map[series.series_id] = series.series_label
                    
                    series_list = sorted(unique_series)
                    
                    # Fetch release info for each series
                    release_data = []
                    for series_id in series_list:
                        try:
                            info = get_series_release_info_cached(
                                series_id, 
                                st.session_state.fred_api_key
                            )
                            
                            # Calculate days remaining
                            next_date = info.get('next_release_date', 'TBD')
                            if next_date != 'TBD':
                                try:
                                    release_date = pd.to_datetime(next_date)
                                    today = pd.Timestamp.now().normalize()
                                    days_remaining = (release_date - today).days
                                except:
                                    days_remaining = 'N/A'
                            else:
                                days_remaining = 'N/A'
                            
                            release_data.append({
                                'Series ID': series_id,
                                'Series': series_info_map.get(series_id, series_id),
                                'Release Name': info.get('release_name', 'Unknown'),
                                'Next Release': next_date,
                                'Days Remaining': days_remaining
                            })
                        except Exception:
                            # Skip series with errors
                            continue
                    
                    # Create DataFrame if we have data
                    if release_data:
                        calendar_df = pd.DataFrame(release_data)
                        
                        # Sort by next release date
                        def sort_key(row):
                            if row['Next Release'] == 'TBD':
                                return (1, '')
                            else:
                                return (0, row['Next Release'])
                        
                        calendar_df['_sort_key'] = calendar_df.apply(sort_key, axis=1)
                        calendar_df = calendar_df.sort_values('_sort_key').drop('_sort_key', axis=1)
                
                except Exception as e:
                    # If calendar fetch fails, continue without it
                    st.warning(f"Could not fetch release calendar data: {e}")
                    calendar_df = None

            # Step 4: Generate PDF using new function
            output_path = tmpdir / "report.pdf"
            generate_pdf_report(
                filename=output_path,
                title=st.session_state.report_title,
                executive_summary=executive_summary,
                calendar_data=calendar_df,
                charts=charts_data
            )

            # Step 5: Provide download button
            with open(output_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=f"macro_report_{datetime.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                key="pdf_download"
            )

            st.success("✅ Professional PDF report generated successfully!")

    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")



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
