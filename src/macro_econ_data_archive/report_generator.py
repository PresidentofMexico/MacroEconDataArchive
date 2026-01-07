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
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle

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
# Modern Platypus-based PDF Generation
# --------------------------

def markdown_to_reportlab_text(markdown_text: str) -> str:
    """
    Convert basic Markdown syntax to ReportLab paragraph markup.
    
    Supports:
    - **bold** → <b>bold</b>
    - *italic* → <i>italic</i>
    
    Args:
        markdown_text: Text with basic Markdown formatting
    
    Returns:
        Text with ReportLab XML-like tags
    """
    import re
    
    # Convert **bold** to <b>bold</b> (must come before single asterisk)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', markdown_text)
    
    # Convert *italic* to <i>italic</i> (but not if already converted to bold)
    # Use negative lookbehind/lookahead to avoid matching asterisks that are part of **
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    
    return text



def parse_markdown_sections(markdown_text: str) -> List[Dict[str, str]]:
    """
    Parse Markdown text into sections based on headers.
    
    Returns list of dicts with 'type' (header/paragraph) and 'content'.
    
    Args:
        markdown_text: Markdown formatted text
    
    Returns:
        List of sections with type and content
    """
    import re
    
    sections = []
    lines = markdown_text.split('\n')
    current_para = []
    
    for line in lines:
        # Check for headers (### Header)
        if line.startswith('###'):
            # Flush current paragraph
            if current_para:
                sections.append({
                    'type': 'paragraph',
                    'content': '\n'.join(current_para).strip()
                })
                current_para = []
            
            # Add header
            header_text = line.replace('###', '').strip()
            sections.append({
                'type': 'header',
                'content': header_text
            })
        # Check for **Bold:** patterns (subheaders) - format is **text:** not **text**:
        elif re.match(r'^\*\*[^*:]+:\*\*', line):
            # Flush current paragraph
            if current_para:
                sections.append({
                    'type': 'paragraph',
                    'content': '\n'.join(current_para).strip()
                })
                current_para = []
            
            # Add as subheader (keep the line as-is, will be converted later)
            sections.append({
                'type': 'subheader',
                'content': line
            })
        else:
            # Add to current paragraph
            if line.strip():
                current_para.append(line)
            elif current_para:
                # Empty line - flush paragraph
                sections.append({
                    'type': 'paragraph',
                    'content': '\n'.join(current_para).strip()
                })
                current_para = []
    
    # Flush remaining paragraph
    if current_para:
        sections.append({
            'type': 'paragraph',
            'content': '\n'.join(current_para).strip()
        })
    
    return sections



def generate_pdf_report(
    filename: Path,
    title: str,
    executive_summary: str,
    calendar_data: pd.DataFrame,
    charts: List[Dict]
) -> None:
    """
    Generate a professional multi-page PDF report using ReportLab Platypus.
    
    Args:
        filename: Output PDF file path
        title: Report title
        executive_summary: Executive briefing text (Markdown format)
        calendar_data: DataFrame with release calendar (columns: Series ID, Series, Release Name, Next Release, Days Remaining)
        charts: List of dicts with keys: 'title', 'image_path', 'narrative'
    
    The PDF structure:
    - Page 1: Cover with title, date, and executive briefing
    - Page 2: Release calendar table
    - Page 3+: Charts with titles, images, and narratives
    """
    # Create output directory
    filename.parent.mkdir(parents=True, exist_ok=True)
    
    # Create document with 1-inch margins
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=letter,
        leftMargin=1*inch,
        rightMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Get default styles and create custom styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=HexColor('#0B2E5E'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.grey,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#0B2E5E'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    subsection_header_style = ParagraphStyle(
        'SubsectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#0B2E5E'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    chart_title_style = ParagraphStyle(
        'ChartTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#0B2E5E'),
        spaceAfter=10,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    )
    
    # Build story (list of flowables)
    story = []
    
    # PAGE 1: COVER PAGE
    # Title
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph(title.upper(), title_style))
    
    # Date
    from datetime import datetime
    date_str = datetime.today().strftime("%B %d, %Y")
    story.append(Paragraph(f"As of {date_str}", subtitle_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Executive Briefing Section
    if executive_summary and executive_summary.strip():
        story.append(Paragraph("Executive Briefing", section_header_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Parse markdown sections
        sections = parse_markdown_sections(executive_summary)
        
        for section in sections:
            if section['type'] == 'header':
                # Skip top-level headers (already used as section titles)
                continue
            elif section['type'] == 'subheader':
                converted_text = markdown_to_reportlab_text(section['content'])
                story.append(Paragraph(converted_text, subsection_header_style))
            elif section['type'] == 'paragraph':
                converted_text = markdown_to_reportlab_text(section['content'])
                story.append(Paragraph(converted_text, body_style))
                story.append(Spacer(1, 0.1*inch))
    
    # Page break after cover
    story.append(PageBreak())
    
    # PAGE 2: RELEASE CALENDAR
    if calendar_data is not None and not calendar_data.empty:
        story.append(Paragraph("Release Calendar", section_header_style))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            "Next scheduled release dates for economic indicators in this report:",
            body_style
        ))
        story.append(Spacer(1, 0.2*inch))
        
        # Prepare table data
        table_data = [calendar_data.columns.tolist()]  # Header row
        for _, row in calendar_data.iterrows():
            table_data.append([str(val) for val in row.tolist()])
        
        # Create table
        col_widths = [1.2*inch, 2*inch, 1.8*inch, 1.2*inch, 1*inch]  # Adjust as needed
        
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#0B2E5E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            
            # Body styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#F0F0F0')]),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(table)
        story.append(PageBreak())
    
    # PAGE 3+: CHARTS
    for idx, chart in enumerate(charts):
        # Chart title
        story.append(Paragraph(chart['title'], chart_title_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Chart image
        if chart.get('image_path') and Path(chart['image_path']).exists():
            # Size image to fit page width (with margins)
            img = Image(str(chart['image_path']), width=6.5*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 0.15*inch))
        
        # Narrative
        if chart.get('narrative') and chart['narrative'].strip():
            # Parse narrative sections
            sections = parse_markdown_sections(chart['narrative'])
            
            for section in sections:
                if section['type'] == 'header':
                    # Skip headers in chart narratives (chart title is enough)
                    continue
                elif section['type'] == 'subheader':
                    converted_text = markdown_to_reportlab_text(section['content'])
                    story.append(Paragraph(converted_text, subsection_header_style))
                elif section['type'] == 'paragraph':
                    converted_text = markdown_to_reportlab_text(section['content'])
                    story.append(Paragraph(converted_text, body_style))
                    story.append(Spacer(1, 0.1*inch))
        
        # Add page break after every 1-2 charts (depending on content length)
        # For simplicity, add page break after each chart
        if idx < len(charts) - 1:  # Don't add after last chart
            story.append(PageBreak())
    
    # Add page numbers
    def add_page_number(canvas, doc):
        """Add page number to each page."""
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.grey)
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.drawRightString(
            letter[0] - 1*inch,
            0.5*inch,
            text
        )
        canvas.restoreState()
    
    # Build PDF
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)


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
