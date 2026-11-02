import datetime as dt
import json

import pytest
from auditbank.converters.base import finalize, project_code
from auditbank.converters.halborn import HalbornConverter
from auditbank.parse import parse
from auditbank.render import render
from auditbank.validate import validate_report, validate_text
from conftest import FIXTURES

TODAY = dt.date(2026, 10, 23)
DRAFT_WARNINGS = {"SIGNOFF_PENDING", "CONVERSION_NOTES_OPEN"}
HALBORN_URL = "https://www.halborn.com/audits/splyce/smart-contract-assessment-de69cd"


def _codes(problems):
    return {p["code"] for p in problems}


def _assert_clean_draft(report):
    text = render(report)
    assert render(parse(text)) == text, "converter output must round-trip"
    problems = validate_text(text, today=TODAY)
    assert _codes(problems) == DRAFT_WARNINGS, problems
    assert all(p["level"] == "warning" for p in problems)


def test_project_code():
    assert project_code("splyce") == "SPLYCE"
    assert project_code("trustless-work") == "TW"


def test_halborn_normalize_fixture():
    firm_report = json.loads((FIXTURES / "halborn-splyce.findings.json").read_text())
    report = finalize(HalbornConverter().normalize(firm_report, "splyce"))
    _assert_clean_draft(report)

    by_id = {f["id"]: f for f in report["findings"]}
    hal1 = by_id["SPLYCE-HAL-001"]
    assert hal1["unified_severity"] == "Critical"
    assert "BVSS 2.0 10.00" in hal1["firm_severity_rating"] and "(source: HAL-01)" in hal1["firm_severity_rating"]
    assert hal1["status"] == "Resolved" and hal1["remediation_verified_by"] == "firm"
    assert hal1["proof"] and "RUST\n\nCopy" not in hal1["proof"]
    assert hal1["location"].startswith("contracts/proxy_asset_manager/src/storage.rs:L34")
    # Rule-based severity mappings carry no note; repeated guesses roll up into one report-level note.
    assert not any("unified severity" in n for n in hal1["conversion_notes"])
    assert not any("category inferred" in n for n in hal1["conversion_notes"])
    assert any(n.startswith("category inferred from the finding text") for n in report["conversion_notes"])

    risk = by_id["SPLYCE-HAL-003"]
    assert risk["status"] == "Risk Accepted" and risk["remediation_verified_by"] == "not-reviewed"
    assert risk["resolved_in"] is None
    ack = by_id["SPLYCE-HAL-050"]
    assert ack["status"] == "Acknowledged" and ack["resolved_in"]

    assert report["publication"]["conversion_method"] is None
    assert report["publication"]["license"] == "Apache-2.0"
    assert report["scope"]["repositories"][0]["commit_start"] == "e1abc2fe64ff2c26b349da7596933baa686f6b30"
    assert "fix-review" in report["audit"]["type"]


@pytest.mark.network
def test_halborn_splyce():
    report = HalbornConverter().convert(HALBORN_URL, "splyce")
    assert len(report["findings"]) == 67
    hal1 = report["findings"][0]
    assert hal1["id"] == "SPLYCE-HAL-001" and hal1["unified_severity"] == "Critical"
    assert "BVSS 2.0 10.00" in hal1["firm_severity_rating"]
    summary = report["findings_summary"]
    assert summary == {"total": 67, "critical": 1, "high": 0, "moderate": 10, "low": 35, "informational": 21}
    assert _codes(validate_report(report, today=TODAY)) == DRAFT_WARNINGS
    _assert_clean_draft(report)


def test_examples_are_clean_drafts():
    examples = sorted((FIXTURES.parent.parent / "examples").glob("*.md"))
    examples = [p for p in examples if p.name != "README.md"]
    assert len(examples) == 3
    for path in examples:
        text = path.read_text()
        assert render(parse(text)) == text, path.name
        assert _codes(validate_text(text, today=TODAY)) == DRAFT_WARNINGS, path.name


def test_tidy_notes_drops_rule_based_and_rolls_up_repeats(valid_report):
    from auditbank.converters.base import tidy_notes

    r = valid_report
    r["conversion_notes"] = ["Section 1 is the firm's summary verbatim", "license defaulted"]
    r["findings"][0]["conversion_notes"] = [
        'unified severity "High" proposed from firm rating "High"; firm to confirm',
        "category inferred: accounting-arithmetic",
        "only on this finding",
    ]
    r["findings"][1]["conversion_notes"] = [
        'unified severity "Low" proposed from firm rating "Warning"; firm to confirm',
        "category inferred: data-validation",
    ]
    r["findings"][2]["conversion_notes"] = ["category inferred: observability"]
    tidy_notes(r)
    assert r["findings"][0]["conversion_notes"] == ["only on this finding"]
    assert r["findings"][1]["conversion_notes"] == [
        'unified severity "Low" proposed from firm rating "Warning"; firm to confirm'
    ]
    assert r["conversion_notes"] == [
        "license defaulted",
        "category inferred from the finding text; check it (all 3 findings)",
    ]


def test_halborn_page_reviewed_from_an_archive():
    """Some Halborn pages (e.g. Templar) list an uploaded zip instead of a repository and file list."""
    firm_report = json.loads((FIXTURES / "halborn-splyce.findings.json").read_text())
    firm_report["sources"] = [
        {
            "repositoryUrl": None,
            "commitHash": None,
            "scopeFiles": [],
            "outOfScopeFiles": [],
            "outOfScopeExtra": [],
            "files": ["soroban.zip"],
        }
    ]
    firm_report["introduction_html"] = firm_report["assessment_summary_html"] = firm_report["methodology_html"] = None
    firm_report["sections_html"] = {
        "Executive Summary": "<p>Halborn reviewed the vault.</p>",
        "Scope and Methodology": (
            '<p>Paths are relative to <a href="https://github.com/Example/contracts">github.com/Example/contracts</a>.</p>'
            "<ul><li><code>contracts/proxy_asset_manager/**</code></li><li><code>contracts/stoken/**</code></li></ul>"
        ),
    }
    report = finalize(HalbornConverter().normalize(firm_report, "splyce"))
    _assert_clean_draft(report)
    repo = report["scope"]["repositories"][0]
    assert repo["url"] == "https://github.com/Example/contracts" and repo["commit_start"] is None
    assert report["scope"]["in_scope_paths"] == ["contracts/proxy_asset_manager/**", "contracts/stoken/**"]
    assert report["sections"]["executive_summary"] == "Halborn reviewed the vault."
    assert report["findings"][0]["location"].startswith("contracts/")
    assert any("soroban.zip" in n for n in report["conversion_notes"])
