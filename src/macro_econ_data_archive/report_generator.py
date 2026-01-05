#!/usr/bin/env python3
"""
report_generator.py

CLI report generator core (chart rendering + PDF assembly).

This module lives under the src/ package so it can be reused by:
- The CLI wrapper at repo root: generate_macro_report.py
- The Streamlit app: macro_econ_data_archive.streamlit_app
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from . import macro_utils


# --------------------------
# Constants
# --------------------------

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


# --------------------------
# Chart specification
# --------------------------

@dataclass
class SeriesSpec:
    id: str
    label: str

@dataclass
class ChartSpec:
    page_title: str
    series: List[SeriesSpec]
    transform: str = "level"  # "level", "yoy", "qoq_saar"
    frequency: str = "monthly"
    units: str = ""
    notes: str = ""


# --------------------------
# Plotting
# --------------------------

def build_series_for_chart(df: pd.DataFrame, spec: ChartSpec) -> pd.DataFrame:
    return macro_utils.build_series_for_chart(df, transform=spec.transform, frequency=spec.frequency)

def render_chart(spec: ChartSpec, data: pd.DataFrame, out_png: Path) -> None:
    """
    Render a single-page time-series chart as a PNG (to embed in the PDF).
    """
    plt.figure(figsize=(10.5, 6.5))
    for sid in data.columns:
        label = next((s.label for s in spec.series if s.id == sid), sid)
        plt.plot(data.index, data[sid], label=label)
    plt.title(spec.page_title)
    plt.xlabel("")
    if spec.units:
        plt.ylabel(spec.units)
    plt.grid(True, linewidth=0.3, alpha=0.6)
    if len(data.columns) > 1:
        plt.legend(loc="best", fontsize=8)
    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=160)
    plt.close()


# --------------------------
# PDF assembly
# --------------------------

def pdf_header_footer(c: canvas.Canvas, title: str, as_of: str, page_num: int) -> None:
    w, h = landscape(letter)
    bar_h = 0.5 * inch
    c.saveState()
    c.setFillColor(HexColor("#0B2E5E"))
    c.rect(0, h - bar_h, w, bar_h, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(0.6 * inch, h - bar_h + 0.18 * inch, title.upper())
    c.setFont("Helvetica", 10)
    c.drawRightString(w - 0.6 * inch, h - bar_h + 0.18 * inch, f"As of {as_of}")
    c.setFillColor(colors.grey)
    c.setFont("Helvetica", 9)
    c.drawRightString(w - 0.6 * inch, 0.35 * inch, f"Page {page_num}")
    c.restoreState()

def assemble_pdf(title: str, as_of: str, png_paths: List[Path], out_pdf: Path) -> None:
    w, h = landscape(letter)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=landscape(letter))
    page_num = 1

    # Cover
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(w / 2, h * 0.65, title.upper())
    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, h * 0.58, f"As of {as_of}")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.grey)
    c.drawCentredString(w / 2, h * 0.53, "Generated from public data series (see specification file).")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.grey)
    c.drawRightString(w - 0.6 * inch, 0.35 * inch, f"Page {page_num}")
    c.setFillColor(colors.black)
    c.showPage()
    page_num += 1

    # Chart pages
    for p in png_paths:
        pdf_header_footer(c, title, as_of, page_num)
        # draw chart image area
        img = ImageReader(str(p))
        # Fit within margins under header
        left = 0.6 * inch
        right = 0.6 * inch
        top = 0.8 * inch  # below header
        bottom = 0.75 * inch
        usable_w = w - left - right
        usable_h = h - (0.5 * inch) - top - bottom
        c.drawImage(img, left, bottom, width=usable_w, height=usable_h, preserveAspectRatio=True, anchor="c")
        c.showPage()
        page_num += 1

    c.save()


# --------------------------
# Main
# --------------------------

def get_templates_dir() -> Path:
    """Get the templates directory path."""
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
            
            templates.append({
                'filename': template_file.name,
                'path': template_file,
                'title': template_data.get('report_title', template_file.stem),
                'description': template_data.get('description', 'No description'),
                'chart_count': len(template_data.get('charts', []))
            })
        except Exception:
            continue
    
    return templates


def load_template(template_name: str) -> Path:
    """
    Load a template by name.
    
    Args:
        template_name: Template filename (e.g., 'core_macro.json') or stem (e.g., 'core_macro')
    
    Returns:
        Path to template file
    
    Raises:
        FileNotFoundError: If template not found
    """
    templates_dir = get_templates_dir()
    
    # Try as-is first
    template_path = templates_dir / template_name
    if template_path.exists():
        return template_path
    
    # Try adding .json extension
    template_path = templates_dir / f"{template_name}.json"
    if template_path.exists():
        return template_path
    
    raise FileNotFoundError(f"Template '{template_name}' not found in {templates_dir}")


def load_spec(path: Path) -> Dict:
    with open(path, "r") as f:
        return json.load(f)

def parse_charts(spec_dict: Dict) -> List[ChartSpec]:
    charts = []
    for c in spec_dict["charts"]:
        series = [SeriesSpec(**s) for s in c["series"]]
        charts.append(ChartSpec(
            page_title=c["page_title"],
            series=series,
            transform=c.get("transform", "level"),
            frequency=c.get("frequency", "monthly"),
            units=c.get("units", ""),
            notes=c.get("notes", ""),
        ))
    return charts

def main():
    ap = argparse.ArgumentParser(
        description="Generate macro economic reports from FRED data"
    )
    
    # Input options (mutually exclusive)
    input_group = ap.add_mutually_exclusive_group(required=False)
    input_group.add_argument(
        "--spec",
        help="Path to chart specification JSON file (legacy mode)"
    )
    input_group.add_argument(
        "--template",
        help="Template name (e.g., 'core_macro' or 'core_macro.json')"
    )
    input_group.add_argument(
        "--list-templates",
        action="store_true",
        help="List available templates and exit"
    )
    
    # Output options
    ap.add_argument("--out", help="Output PDF file (required unless --list-templates)")
    ap.add_argument("--start", default="1990-01-01", help="Start date for data pulls.")
    ap.add_argument("--tmpdir", default="_charts_tmp", help="Temporary folder for chart PNGs.")
    
    args = ap.parse_args()
    
    # Handle --list-templates
    if args.list_templates:
        templates = discover_templates()
        if not templates:
            print("No templates found in config/templates/")
            return EXIT_SUCCESS
        
        print("Available templates:")
        print("-" * 70)
        for t in templates:
            print(f"  {t['filename']:<25} {t['title']}")
            print(f"    Description: {t['description']}")
            print(f"    Charts: {t['chart_count']}")
            print()
        return EXIT_SUCCESS
    
    # Validate required arguments
    if not args.out:
        print("Error: --out is required")
        return EXIT_FAILURE
    
    if not args.spec and not args.template:
        print("Error: Either --spec or --template is required")
        return EXIT_FAILURE
    
    # Determine spec path
    if args.template:
        try:
            spec_path = load_template(args.template)
            print(f"Using template: {spec_path}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return EXIT_FAILURE
    else:
        spec_path = Path(args.spec)
        if not spec_path.exists():
            print(f"Error: Spec file not found: {spec_path}")
            return EXIT_FAILURE

    spec_dict = load_spec(spec_path)
    title = spec_dict.get("report_title", "Macro Economic Data Archive")
    as_of = spec_dict.get("as_of", datetime.today().strftime("%B %d, %Y"))
    charts = parse_charts(spec_dict)

    tmpdir = Path(args.tmpdir)
    pngs: List[Path] = []

    for i, ch in enumerate(charts, start=1):
        series_ids = [s.id for s in ch.series]
        print(f"Processing chart {i}/{len(charts)}: {ch.page_title}")
        try:
            raw = macro_utils.fetch_fred(series_ids, start=args.start)
            transformed = build_series_for_chart(raw, ch).dropna(how="all")
            if transformed.empty:
                print(f"  Warning: No data available for chart '{ch.page_title}'. Skipping.")
                continue
            out_png = tmpdir / f"chart_{i:03d}.png"
            render_chart(ch, transformed, out_png)
            pngs.append(out_png)
        except Exception as e:
            print(f"  Error processing chart '{ch.page_title}': {e}")
            print(f"  Skipping this chart and continuing...")
            continue

    if not pngs:
        print("Error: No charts were successfully generated. Cannot create PDF.")
        return EXIT_FAILURE
    
    assemble_pdf(title, as_of, pngs, Path(args.out))
    print(f"Wrote: {args.out}")
    return EXIT_SUCCESS

if __name__ == "__main__":
    import sys
    sys.exit(main())
