"""Check that the SPEC and named red tests cover the saved source links."""

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TRACE_PAIRS = {
    ("N.1", "SR.1"),
    ("N.1", "SR.3"),
    ("N.2", "SR.2"),
    ("N.3", "SR.4"),
    ("N.3", "SR.5"),
    ("N.3", "SR.7"),
    ("N.4", "SR.6"),
    ("N.5", "SR.8"),
    ("N.6", "SR.9"),
    ("N.7", "SR.10"),
    ("N.8", "SR.11"),
    ("N.9", "SR.12"),
    ("N.10", "SR.13"),
    ("N.10", "SR.14"),
    ("N.11", "SR.15"),
    ("N.11", "SR.16"),
    ("N.12", "SR.1"),
    ("N.12", "SR.7"),
    ("N.13", "SR.17"),
    ("N.13", "SR.18"),
}


def test_spec_manifest_and_red_tests_cover_all_source_links():
    """Check all 13 needs, 18 requirements, and 20 linked SPEC/test cases."""
    manifest = json.loads(
        (ROOT / "tests" / "acceptance_cases.json").read_text(encoding="utf-8")
    )
    cases = manifest["cases"]
    spec = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
    test_source = (ROOT / "tests" / "test_spec_acceptance.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(test_source)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }

    assert len(cases) == 20
    assert {case["need_id"] for case in cases} == {
        f"N.{number}" for number in range(1, 14)
    }
    assert {case["requirement_id"] for case in cases} == {
        f"SR.{number}" for number in range(1, 19)
    }
    assert {
        (case["need_id"], case["requirement_id"]) for case in cases
    } == EXPECTED_TRACE_PAIRS
    assert len({case["criterion_id"] for case in cases}) == 20
    assert len({case["test_name"] for case in cases}) == 20
    assert set(functions) == {case["test_name"] for case in cases}

    for case in cases:
        expected_id = (
            "AC-"
            + case["need_id"].replace(".", "")
            + "-"
            + case["requirement_id"].replace(".", "")
        )
        assert case["criterion_id"] == expected_id
        assert case["criterion_id"] in spec
        assert case["test_name"] in spec
        assert case["need_statement"] in spec
        assert case["moe"] in spec
        assert case["validation_criteria"] in spec
        function = functions[case["test_name"]]
        assert case["criterion_id"] in ast.get_docstring(function)

