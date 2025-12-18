#!/usr/bin/env python3
"""
generate_macro_report.py

A reproducible template to generate a chart-driven macroeconomic report similar in spirit to the provided sample.

Data source approach
- Pull time series from FRED (Federal Reserve Bank of St. Louis) whenever possible.
  FRED republishes official series from BEA, BLS, Census, Federal Reserve, EIA, etc.
- Apply consistent transformations: level, YoY %, QoQ SAAR %, spreads.

Usage (example)
  pip install pandas pandas_datareader matplotlib reportlab
  python generate_macro_report.py --spec macro_chart_spec.json --out Macro_Economic_Data_Archive.pdf

Notes
- This script is intentionally modular so you can expand to 100+ pages by adding chart specs.
- If you prefer to hit BEA/BLS APIs directly (instead of FRED), replace the fetch layer.
"""

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
import matplotlib.pyplot as plt

from pandas_datareader import data as pdr

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


# --------------------------
# Transform utilities
# --------------------------

def yoy(series: pd.Series, periods: int) -> pd.Series:
    """Year-over-year percent change for the given periodicity."""
    return 100.0 * (series / series.shift(periods) - 1.0)

def qoq_saar(series: pd.Series) -> pd.Series:
    """Quarter-over-quarter change at a seasonally adjusted annual rate."""
    return 100.0 * ((series / series.shift(1)) ** 4 - 1.0)

def safe_to_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


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
# Data fetch
# --------------------------

def fetch_fred(series_ids: List[str], start: str = "1990-01-01") -> pd.DataFrame:
    """
    Fetch series from FRED via pandas_datareader. Requires internet access.
    """
    df = pd.DataFrame()
    for sid in series_ids:
        s = pdr.DataReader(sid, "fred", start=start)
        if isinstance(s, pd.DataFrame):
            # Handle case where column name might not match series ID exactly
            if sid in s.columns:
                s = s[sid]
            else:
                # Take the first column if exact match not found
                s = s.iloc[:, 0]
        df[sid] = safe_to_numeric(s)
    return df


# --------------------------
# Plotting
# --------------------------

def infer_yoy_periods(freq: str) -> int:
    f = freq.lower()
    if f.startswith("m"):
        return 12
    if f.startswith("q"):
        return 4
    if f.startswith("w"):
        return 52
    if f.startswith("d"):
        return 365
    # default to 12
    return 12

def build_series_for_chart(df: pd.DataFrame, spec: ChartSpec) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    if spec.transform == "level":
        out = df.copy()
    elif spec.transform == "yoy":
        periods = infer_yoy_periods(spec.frequency)
        for c in df.columns:
            out[c] = yoy(df[c], periods=periods)
    elif spec.transform == "qoq_saar":
        for c in df.columns:
            out[c] = qoq_saar(df[c])
    else:
        raise ValueError(f"Unknown transform: {spec.transform}")
    return out

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
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="Path to chart specification JSON.")
    ap.add_argument("--out", required=True, help="Output PDF file.")
    ap.add_argument("--start", default="1990-01-01", help="Start date for data pulls.")
    ap.add_argument("--tmpdir", default="_charts_tmp", help="Temporary folder for chart PNGs.")
    args = ap.parse_args()

    spec_path = Path(args.spec)
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
            raw = fetch_fred(series_ids, start=args.start)
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
        return 1
    
    assemble_pdf(title, as_of, pngs, Path(args.out))
    print(f"Wrote: {args.out}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
