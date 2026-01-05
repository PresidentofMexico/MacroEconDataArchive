#!/usr/bin/env python3
"""
Test script for template functionality

Tests all template features without requiring network access to FRED.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_cli_template_discovery():
    """Test CLI template discovery"""
    print("=" * 60)
    print("TEST 1: CLI Template Discovery")
    print("=" * 60)
    
    from macro_econ_data_archive.report_generator import list_templates, get_templates_dir
    
    templates_dir = get_templates_dir()
    print(f"Templates directory: {templates_dir}")
    print(f"Exists: {templates_dir.exists()}")
    
    templates = list_templates()
    print(f"\nFound {len(templates)} templates:")
    for template in templates:
        print(f"  - {template}")
    
    assert len(templates) == 3, f"Expected 3 templates, found {len(templates)}"
    assert "core_macro" in templates
    assert "inflation_deep_dive" in templates
    assert "labor_markets" in templates
    
    print("\n✅ CLI template discovery works!\n")
    return True


def test_cli_template_loading():
    """Test CLI template loading"""
    print("=" * 60)
    print("TEST 2: CLI Template Loading")
    print("=" * 60)
    
    from macro_econ_data_archive.report_generator import load_template, parse_charts
    
    # Test each template
    for template_name in ["core_macro", "inflation_deep_dive", "labor_markets"]:
        print(f"\nLoading template: {template_name}")
        template = load_template(template_name)
        
        # Check metadata
        meta = template.get("template_metadata", {})
        print(f"  Name: {meta.get('name')}")
        print(f"  Description: {meta.get('description')}")
        print(f"  Tags: {meta.get('tags')}")
        
        # Parse charts
        charts = parse_charts(template)
        print(f"  Charts: {len(charts)}")
        
        assert len(charts) > 0, f"Template {template_name} has no charts"
        
        # Check first chart structure
        first_chart = charts[0]
        print(f"    First chart: {first_chart.page_title}")
        print(f"    Series: {[s.id for s in first_chart.series]}")
        print(f"    Transform: {first_chart.transform}")
        print(f"    Frequency: {first_chart.frequency}")
        
        assert first_chart.page_title, "Chart missing page_title"
        assert len(first_chart.series) > 0, "Chart missing series"
        assert first_chart.transform in ["level", "yoy", "qoq_saar"], f"Invalid transform: {first_chart.transform}"
    
    print("\n✅ CLI template loading works!\n")
    return True


def test_streamlit_template_discovery():
    """Test Streamlit template discovery"""
    print("=" * 60)
    print("TEST 3: Streamlit Template Discovery")
    print("=" * 60)
    
    from macro_econ_data_archive.streamlit_app import discover_templates, get_templates_dir
    
    templates_dir = get_templates_dir()
    print(f"Templates directory: {templates_dir}")
    
    templates = discover_templates()
    print(f"\nFound {len(templates)} templates:")
    
    for name, path, metadata in templates:
        print(f"\n  Template: {name}")
        print(f"    Path: {path.name}")
        print(f"    Description: {metadata.get('description', 'N/A')}")
        print(f"    Tags: {', '.join(metadata.get('tags', []))}")
        print(f"    Version: {metadata.get('version', 'N/A')}")
    
    assert len(templates) == 3, f"Expected 3 templates, found {len(templates)}"
    
    # Check that each template returns proper structure
    for name, path, metadata in templates:
        assert name, "Template name is empty"
        assert path.exists(), f"Template file {path} doesn't exist"
        assert isinstance(metadata, dict), "Metadata is not a dict"
    
    print("\n✅ Streamlit template discovery works!\n")
    return True


def test_template_json_structure():
    """Test that all templates have valid structure"""
    print("=" * 60)
    print("TEST 4: Template JSON Structure Validation")
    print("=" * 60)
    
    import json
    
    templates_dir = Path("config/templates")
    
    for template_file in templates_dir.glob("*.json"):
        print(f"\nValidating {template_file.name}...")
        
        with open(template_file) as f:
            data = json.load(f)
        
        # Check required top-level fields
        assert "charts" in data, f"{template_file.name}: missing 'charts' field"
        assert isinstance(data["charts"], list), f"{template_file.name}: 'charts' must be a list"
        assert len(data["charts"]) > 0, f"{template_file.name}: 'charts' list is empty"
        
        # Check optional metadata
        if "template_metadata" in data:
            meta = data["template_metadata"]
            print(f"  ✓ Has metadata")
            print(f"    Name: {meta.get('name')}")
            print(f"    Description: {meta.get('description')[:50]}...")
            print(f"    Tags: {meta.get('tags')}")
        
        # Check report fields
        if "report_title" in data:
            print(f"  ✓ Report title: {data['report_title']}")
        
        # Check each chart
        print(f"  ✓ {len(data['charts'])} charts")
        
        for i, chart in enumerate(data["charts"], 1):
            # Required fields
            assert "page_title" in chart, f"Chart {i}: missing 'page_title'"
            assert "series" in chart, f"Chart {i}: missing 'series'"
            assert isinstance(chart["series"], list), f"Chart {i}: 'series' must be a list"
            assert len(chart["series"]) > 0, f"Chart {i}: 'series' list is empty"
            
            # Check series structure
            for series in chart["series"]:
                assert "id" in series, f"Chart {i}: series missing 'id'"
                assert "label" in series, f"Chart {i}: series missing 'label'"
            
            # Optional but recommended fields
            if "transform" in chart:
                assert chart["transform"] in ["level", "yoy", "qoq_saar"], \
                    f"Chart {i}: invalid transform '{chart['transform']}'"
            
            if "frequency" in chart:
                assert chart["frequency"] in ["daily", "weekly", "monthly", "quarterly"], \
                    f"Chart {i}: invalid frequency '{chart['frequency']}'"
        
        print(f"  ✅ {template_file.name} is valid")
    
    print("\n✅ All templates have valid structure!\n")
    return True


def test_documentation_exists():
    """Test that documentation exists"""
    print("=" * 60)
    print("TEST 5: Documentation Exists")
    print("=" * 60)
    
    docs_dir = Path("docs")
    template_guide = docs_dir / "TEMPLATE_GUIDE.md"
    
    print(f"Checking for {template_guide}...")
    assert template_guide.exists(), f"{template_guide} not found"
    
    # Read and check basic structure
    with open(template_guide) as f:
        content = f.read()
    
    # Check for key sections
    required_sections = [
        "# Template Guide",
        "## Using Templates",
        "## Built-in Templates",
        "## Creating Custom Templates",
        "### Template File Structure",
    ]
    
    for section in required_sections:
        assert section in content, f"Documentation missing section: {section}"
        print(f"  ✓ Found section: {section}")
    
    # Check that it mentions all three templates
    assert "core_macro" in content.lower(), "Documentation doesn't mention core_macro template"
    assert "inflation" in content.lower(), "Documentation doesn't mention inflation template"
    assert "labor" in content.lower(), "Documentation doesn't mention labor template"
    
    print("\n✅ Documentation exists and is complete!\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("TEMPLATE FUNCTIONALITY TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_cli_template_discovery,
        test_cli_template_loading,
        test_streamlit_template_discovery,
        test_template_json_structure,
        test_documentation_exists,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"PASSED: {passed}/{total} tests")
    print("=" * 60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
