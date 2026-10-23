import json

from auditbank.parse import parse, parse_file
from auditbank.paths import TEMPLATE_PATH
from auditbank.render import render
from conftest import FIXTURES


def test_fixture_roundtrips_byte_for_byte():
    text = (FIXTURES / "minimal-valid.md").read_text()
    assert render(parse(text)) == text


def test_parse_render_parse_is_stable(valid_report):
    assert parse(render(valid_report)) == valid_report


def test_parsed_report_is_json_serializable(valid_report):
    json.dumps(valid_report)


def test_template_parses_with_guidance_stripped():
    report = parse_file(TEMPLATE_PATH)
    assert report["schema_version"] == "0.2"
    [finding] = report["findings"]
    assert finding["id"] == "{FINDING-ID}"
    assert finding["unified_severity"].startswith("Critical / High")
    assert finding["difficulty_likelihood"].startswith("Low / Medium / High")
    assert finding["redacted"]["value"] is not True
    assert finding["description"] is None or "<!--" not in finding["description"]
    assert "point-in-time" in report["sections"]["disclaimer"]


def test_conversion_notes_are_kept_and_guidance_dropped(valid_report):
    valid_report["findings"][0]["conversion_notes"] = ["category inferred"]
    valid_report["conversion_notes"] = ["client name taken from URL"]
    text = render(valid_report).replace("**Impact.**", "<!-- Guidance: remove me -->\n**Impact.**", 1)
    report = parse(text)
    assert report["findings"][0]["conversion_notes"] == ["category inferred"]
    assert report["conversion_notes"] == ["client name taken from URL"]
    assert "Guidance" not in report["findings"][0]["description"]


def test_code_fences_do_not_split_findings(valid_report):
    valid_report["findings"][0]["proof"] = "```rust\n### [NOT-A-HEADING] x\n**Impact.** not a lead\n```"
    report = parse(render(valid_report))
    assert len(report["findings"]) == 3
    assert report["findings"][0]["proof"].startswith("```rust")


def test_redacted_and_pipes_roundtrip(valid_report):
    f = valid_report["findings"][1]
    f["redacted"] = {"value": True, "reason": "PoC withheld pending remediation"}
    f["firm_severity_rating"] = "Medium | impact x likelihood"
    report = parse(render(valid_report))
    assert report["findings"][1]["redacted"] == f["redacted"]
    assert report["findings"][1]["firm_severity_rating"] == "Medium | impact x likelihood"
