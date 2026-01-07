#!/usr/bin/env python3
"""
Test suite for Phase 6: Board-Ready PDF Export feature.

This test validates:
1. Markdown to ReportLab conversion
2. PDF generation with executive summary
3. Release calendar rendering
4. Multi-page chart layout
"""

import sys
from pathlib import Path
import tempfile
import pandas as pd

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from src.macro_econ_data_archive.report_generator import (
    markdown_to_reportlab_text,
    parse_markdown_sections,
    generate_pdf_report
)


def test_markdown_to_reportlab_conversion():
    """Test basic Markdown to ReportLab conversion."""
    print("\n=== Test 1: Markdown to ReportLab Conversion ===")
    
    # Test bold conversion
    input_text = "This is **bold text** in a sentence."
    expected = "This is <b>bold text</b> in a sentence."
    result = markdown_to_reportlab_text(input_text)
    assert result == expected, f"Expected: {expected}, Got: {result}"
    print("✓ Bold conversion works")
    
    # Test italic conversion
    input_text = "This is *italic text* in a sentence."
    expected = "This is <i>italic text</i> in a sentence."
    result = markdown_to_reportlab_text(input_text)
    assert result == expected, f"Expected: {expected}, Got: {result}"
    print("✓ Italic conversion works")
    
    # Test multiple bold words
    input_text = "**Executive Summary:** The economy is **strong** but inflation remains **elevated**."
    result = markdown_to_reportlab_text(input_text)
    assert "<b>Executive Summary:</b>" in result
    assert "<b>strong</b>" in result
    assert "<b>elevated</b>" in result
    print("✓ Multiple bold conversions work")
    
    print("✅ All markdown conversion tests passed")


def test_parse_markdown_sections():
    """Test parsing of markdown into sections."""
    print("\n=== Test 2: Parse Markdown Sections ===")
    
    markdown_text = """### Executive Summary
This is a high-level overview of the economy.

**Key Drivers:** The main factors affecting the economy.

Growth is strong but inflation is elevated.

### Outlook
The future looks uncertain but stable."""
    
    sections = parse_markdown_sections(markdown_text)
    
    # Check we got sections
    assert len(sections) > 0, "Should have parsed sections"
    
    # Check for headers
    headers = [s for s in sections if s['type'] == 'header']
    assert len(headers) >= 1, f"Should have at least 1 header, got {len(headers)}"
    print(f"✓ Found {len(headers)} headers")
    
    # Check for subheaders
    subheaders = [s for s in sections if s['type'] == 'subheader']
    assert len(subheaders) >= 1, f"Should have at least 1 subheader, got {len(subheaders)}"
    print(f"✓ Found {len(subheaders)} subheaders")
    
    # Check for paragraphs
    paragraphs = [s for s in sections if s['type'] == 'paragraph']
    assert len(paragraphs) >= 1, f"Should have at least 1 paragraph, got {len(paragraphs)}"
    print(f"✓ Found {len(paragraphs)} paragraphs")
    
    print("✅ All section parsing tests passed")


def test_generate_pdf_with_all_features():
    """Test PDF generation with all features."""
    print("\n=== Test 3: Generate Complete PDF ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create sample chart image (just a placeholder file)
        chart_image = tmpdir_path / "chart_001.png"
        # Create a minimal 1x1 pixel PNG for testing
        import base64
        png_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        )
        chart_image.write_bytes(png_data)
        
        # Prepare test data
        title = "Q4 2024 Economic Report"
        
        executive_summary = """### Executive Summary
The economy showed **resilient growth** in Q4 2024, with GDP expanding at a solid pace.

**Key Drivers:** Consumer spending remained strong despite elevated inflation pressures.

**Outlook:** The Federal Reserve is expected to maintain current policy stance through early 2025."""
        
        calendar_data = pd.DataFrame({
            'Series ID': ['GDPC1', 'UNRATE', 'CPIAUCSL'],
            'Series': ['Real GDP', 'Unemployment Rate', 'CPI All Items'],
            'Release Name': ['GDP', 'Employment Situation', 'CPI'],
            'Next Release': ['2024-01-25', '2024-02-02', '2024-02-13'],
            'Days Remaining': [18, 26, 37]
        })
        
        charts = [
            {
                'title': 'Real GDP Growth (QoQ SAAR)',
                'image_path': str(chart_image),
                'narrative': """The economy expanded at a **moderate pace** in Q4 2024.

**Key Observations:** Real GDP grew 2.5% on a quarter-over-quarter seasonally adjusted annual rate basis.

Consumer spending remained the primary driver of growth."""
            },
            {
                'title': 'Unemployment Rate',
                'image_path': str(chart_image),
                'narrative': "The unemployment rate remained stable at 3.7%, indicating a tight labor market."
            }
        ]
        
        # Generate PDF
        output_path = tmpdir_path / "test_report.pdf"
        
        try:
            generate_pdf_report(
                filename=output_path,
                title=title,
                executive_summary=executive_summary,
                calendar_data=calendar_data,
                charts=charts
            )
            
            # Check PDF was created
            assert output_path.exists(), "PDF file should be created"
            print("✓ PDF file created successfully")
            
            # Check file size is reasonable (> 5KB for a real PDF)
            file_size = output_path.stat().st_size
            assert file_size > 5000, f"PDF should be > 5KB, got {file_size} bytes"
            print(f"✓ PDF file size is reasonable: {file_size} bytes")
            
            # Read PDF header to validate it's a real PDF
            with open(output_path, 'rb') as f:
                header = f.read(5)
                assert header == b'%PDF-', "Should be a valid PDF file"
            print("✓ PDF has valid header")
            
            print("✅ PDF generation successful")
            print(f"   Generated PDF: {output_path}")
            
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            import traceback
            traceback.print_exc()
            raise


def test_generate_pdf_without_calendar():
    """Test PDF generation without release calendar (optional feature)."""
    print("\n=== Test 4: Generate PDF Without Calendar ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create sample chart image
        chart_image = tmpdir_path / "chart_001.png"
        import base64
        png_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        )
        chart_image.write_bytes(png_data)
        
        # Test without calendar
        charts = [
            {
                'title': 'Test Chart',
                'image_path': str(chart_image),
                'narrative': 'Test narrative.'
            }
        ]
        
        output_path = tmpdir_path / "test_no_calendar.pdf"
        
        try:
            generate_pdf_report(
                filename=output_path,
                title="Test Report",
                executive_summary="Test summary.",
                calendar_data=None,  # No calendar data
                charts=charts
            )
            
            assert output_path.exists(), "PDF should be created without calendar"
            print("✓ PDF created successfully without calendar")
            
            print("✅ PDF generation without calendar works")
            
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            raise


def test_generate_pdf_with_empty_executive_summary():
    """Test PDF generation with empty executive summary."""
    print("\n=== Test 5: Generate PDF With Empty Executive Summary ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create sample chart image
        chart_image = tmpdir_path / "chart_001.png"
        import base64
        png_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        )
        chart_image.write_bytes(png_data)
        
        charts = [
            {
                'title': 'Test Chart',
                'image_path': str(chart_image),
                'narrative': 'Test narrative.'
            }
        ]
        
        output_path = tmpdir_path / "test_no_summary.pdf"
        
        try:
            generate_pdf_report(
                filename=output_path,
                title="Test Report",
                executive_summary="",  # Empty summary
                calendar_data=None,
                charts=charts
            )
            
            assert output_path.exists(), "PDF should be created without executive summary"
            print("✓ PDF created successfully without executive summary")
            
            print("✅ PDF generation with empty executive summary works")
            
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            raise


def run_all_tests():
    """Run all test suites."""
    print("="*70)
    print("Board-Ready PDF Export Test Suite")
    print("="*70)
    
    tests = [
        test_markdown_to_reportlab_conversion,
        test_parse_markdown_sections,
        test_generate_pdf_with_all_features,
        test_generate_pdf_without_calendar,
        test_generate_pdf_with_empty_executive_summary,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ Test failed: {test.__name__}")
            print(f"   Error: {e}")
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
