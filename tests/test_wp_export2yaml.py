import pytest
from wp_converter.wp_export2yaml import parse_wxr2yaml


def test_parse_wxr2yaml_runs(tmp_path):
    # This is a placeholder test. Adjust with real test data and assertions.
    xml_file = "wp_export.xml"  # Use a sample or fixture file
    yaml_file = tmp_path / "output.yaml"
    try:
        parse_wxr2yaml(xml_file, str(yaml_file))
    except Exception as e:
        pytest.fail(f"parse_wxr2yaml raised an exception: {e}")
