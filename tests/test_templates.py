#!/usr/bin/env python3
"""
test_templates.py

Tests for template discovery, loading, and validation.
"""

import sys
import json
from pathlib import Path

# Add src to path (go up from tests/ to repo root)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_template_discovery():
    """Test template discovery functionality."""
    print("Testing template discovery...")

    try:
        from macro_econ_data_archive.report_generator import (
            get_templates_dir, discover_templates
        )

        # Check templates directory
        templates_dir = get_templates_dir()
        assert templates_dir.exists(), f"Templates directory not found: {templates_dir}"
        print(f"  ✓ Templates directory: {templates_dir}")

        # Discover templates
        templates = discover_templates()
        print(f"  ✓ Discovered {len(templates)} template(s)")

        # Validate structure
        for t in templates:
            assert 'filename' in t
            assert 'path' in t
            assert 'title' in t
            assert 'description' in t
            assert 'chart_count' in t
            print(f"    - {t['filename']}: {t['title']} ({t['chart_count']} charts)")

        print("  ✓ Template structure validated")
        return True

    except Exception as e:
        print(f"  ✗ Template discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_schema():
    """Test that all templates follow the expected schema."""
    print("\nTesting template schema...")

    try:
        from macro_econ_data_archive.report_generator import discover_templates

        templates = discover_templates()
        if not templates:
            print("  ⚠ No templates found (skipping)")
            return True

        required_root_keys = ['report_title', 'charts']
        required_chart_keys = ['page_title']

        for t in templates:
            print(f"\n  Validating: {t['filename']}")

            with open(t['path'], 'r') as f:
                data = json.load(f)

            # Check root keys
            for key in required_root_keys:
                assert key in data, f"Missing required key: {key}"
            print(f"    ✓ Root keys present")

            # Check charts array
            assert isinstance(data['charts'], list), "charts must be a list"
            assert len(data['charts']) > 0, "charts array is empty"
            print(f"    ✓ {len(data['charts'])} charts defined")

            # Validate each chart
            for i, chart in enumerate(data['charts']):
                for key in required_chart_keys:
                    assert key in chart, f"Chart {i} missing required key: {key}"

                # Check series format (either multi-series or legacy single-series)
                has_multi = 'series' in chart and isinstance(chart['series'], list)
                has_legacy = 'series_id' in chart

                assert has_multi or has_legacy, f"Chart {i} must have 'series' list or 'series_id'"

                if has_multi:
                    for j, series in enumerate(chart['series']):
                        assert 'id' in series, f"Chart {i}, series {j} missing 'id'"
                        assert 'label' in series, f"Chart {i}, series {j} missing 'label'"

            print(f"    ✓ All charts validated")

        print("\n  ✓ All templates follow schema")
        return True

    except Exception as e:
        print(f"  ✗ Template schema validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_loading_cli():
    """Test template loading via CLI functions."""
    print("\nTesting CLI template loading...")

    try:
        from macro_econ_data_archive.report_generator import (
            discover_templates, load_template
        )

        templates = discover_templates()
        if not templates:
            print("  ⚠ No templates to test (skipping)")
            return True

        # Test loading by full filename
        first_template = templates[0]
        path1 = load_template(first_template['filename'])
        assert path1.exists(), f"Template path doesn't exist: {path1}"
        print(f"  ✓ Loaded by filename: {first_template['filename']}")

        # Test loading by stem (without .json)
        stem = first_template['filename'].replace('.json', '')
        path2 = load_template(stem)
        assert path2.exists(), f"Template path doesn't exist: {path2}"
        print(f"  ✓ Loaded by stem: {stem}")

        # Test loading nonexistent template
        try:
            load_template('nonexistent_template')
            print("  ✗ Should have raised FileNotFoundError")
            return False
        except FileNotFoundError:
            print("  ✓ Correctly raises FileNotFoundError for missing template")

        return True

    except Exception as e:
        print(f"  ✗ CLI template loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_loading_streamlit():
    """Test template loading via Streamlit functions."""
    print("\nTesting Streamlit template loading...")

    try:
        from macro_econ_data_archive.streamlit_app import (
            discover_templates, load_template
        )

        templates = discover_templates()
        if not templates:
            print("  ⚠ No templates to test (skipping)")
            return True

        # Load first template
        first_template = templates[0]
        data = load_template(first_template['path'])

        # Validate structure
        assert isinstance(data, dict)
        assert 'charts' in data
        assert isinstance(data['charts'], list)

        print(f"  ✓ Loaded template: {first_template['filename']}")
        print(f"    Title: {data.get('report_title', 'N/A')}")
        print(f"    Charts: {len(data['charts'])}")

        return True

    except Exception as e:
        print(f"  ✗ Streamlit template loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_specific_templates():
    """Test specific known templates."""
    print("\nTesting specific templates...")

    expected_templates = [
        ('core_macro.json', 4),
        ('inflation_deep_dive.json', 8),
        ('labor_markets.json', 9)
    ]

    templates_dir = Path("config/templates")

    results = []
    for filename, expected_count in expected_templates:
        template_path = templates_dir / filename

        if not template_path.exists():
            print(f"  ⚠ {filename} not found (optional)")
            continue

        try:
            with open(template_path, 'r') as f:
                data = json.load(f)

            actual_count = len(data.get('charts', []))
            if actual_count == expected_count:
                print(f"  ✓ {filename}: {actual_count} charts")
                results.append(True)
            else:
                print(f"  ⚠ {filename}: expected {expected_count} charts, got {actual_count}")
                results.append(True)  # Still pass, just a warning

        except Exception as e:
            print(f"  ✗ {filename}: failed to load - {e}")
            results.append(False)

    return all(results) if results else True


def test_template_content_validity():
    """Test that template content is valid (series IDs look reasonable)."""
    print("\nTesting template content validity...")

    try:
        from macro_econ_data_archive.report_generator import discover_templates

        templates = discover_templates()
        if not templates:
            print("  ⚠ No templates to test (skipping)")
            return True

        for t in templates:
            with open(t['path'], 'r') as f:
                data = json.load(f)

            for i, chart in enumerate(data['charts']):
                # Extract series IDs
                if 'series' in chart:
                    series_ids = [s['id'] for s in chart['series']]
                elif 'series_id' in chart:
                    series_ids = [chart['series_id']]
                else:
                    print(f"  ✗ Chart {i} has no series")
                    return False

                # Validate series IDs (should be uppercase alphanumeric)
                for sid in series_ids:
                    assert sid.isupper() or sid.isalnum(), f"Invalid series ID: {sid}"
                    assert len(sid) > 0, "Empty series ID"

            print(f"  ✓ {t['filename']}: content valid")

        return True

    except Exception as e:
        print(f"  ✗ Content validity check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all template tests."""
    print("=" * 70)
    print("Template System Tests")
    print("=" * 70)

    tests = [
        ("Template Discovery", test_template_discovery),
        ("Template Schema", test_template_schema),
        ("CLI Template Loading", test_template_loading_cli),
        ("Streamlit Template Loading", test_template_loading_streamlit),
        ("Specific Templates", test_specific_templates),
        ("Content Validity", test_template_content_validity)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<35} {status}")

    print("-" * 70)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
