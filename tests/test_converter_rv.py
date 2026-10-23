import datetime as dt
import json

import pytest
from auditbank.converters.base import fetch, finalize
from auditbank.converters.runtime_verification import RuntimeVerificationConverter, text_to_md
from auditbank.parse import parse
from auditbank.render import render
from auditbank.validate import validate_text
from conftest import FIXTURES

TODAY = dt.date(2026, 10, 23)
DRAFT_WARNINGS = {"SIGNOFF_PENDING", "CONVERSION_NOTES_OPEN"}
RV_URL = "https://strapi.runtimeverification.com/uploads/Moonlight_report_64808bfd8e.pdf"


def _assert_clean_draft(report):
    text = render(report)
    assert render(parse(text)) == text, "converter output must round-trip"
    problems = validate_text(text, today=TODAY)
    assert {p["code"] for p in problems} == DRAFT_WARNINGS, problems
    assert all(p["level"] == "warning" for p in problems)


def test_rv_matches_url():
    assert RuntimeVerificationConverter.matches(RV_URL)
    assert not RuntimeVerificationConverter.matches("https://www.halborn.com/audits/x/y")


def test_code_excerpt_becomes_fenced_block_with_reference():
    text = (
        "Intro sentence:\n\n"
        "     Org/repo/contracts/a/src/lib.rs\n"
        " Line 10 to 12 in abc1234\n\n"
        "  10 pub fn f() {\n"
        "  11     g();\n\n\n"
        "  12 }\n\n"
        "After the code, Vec<T> stays literal."
    )
    md, refs = text_to_md(text)
    assert refs == [{"repo": "Org/repo", "path": "contracts/a/src/lib.rs", "start": 10, "end": 12, "commit": "abc1234"}]
    assert "```rust\npub fn f() {\n    g();\n}\n```" in md
    assert "Vec\\<T>" in md


def test_rv_normalize_fixture():
    firm_report = json.loads((FIXTURES / "rv-moonlight.extracted.json").read_text())
    report = finalize(RuntimeVerificationConverter().normalize(firm_report, "moonlight"))
    _assert_clean_draft(report)

    meta = report["report"]
    assert meta["client"] == "Moonlight"
    assert meta["report_date"] == "2026-07-24"
    assert meta["engagement_start"] == "2026-06-29" and meta["engagement_end"] is None
    assert meta["pdf_url"] == RV_URL
    repo = report["scope"]["repositories"][0]
    assert repo == {
        "url": "https://github.com/Moonlight-Protocol/soroban-core",
        "commit_start": "d65780bbf0a6f8b2b601e4a536b38000775c8a15",
        "commit_final": "867c23da1769a2f56e42449ce5d5315ffb5f4cdc",
    }
    assert report["scope"]["in_scope_paths"] == ["contracts/channel-auth", "contracts/privacy-channel"]
    assert report["audit"]["type"] == ["design-review", "code-review", "fix-review"]
    assert "Almanax" in report["audit"]["tooling"]
    assert report["effort"]["engineer_weeks"] is None

    by_id = {f["id"]: f for f in report["findings"]}
    a1 = by_id["MOONLIGHT-RV-001"]
    assert a1["unified_severity"] == "Moderate"
    assert a1["firm_severity_rating"] == "Medium (Difficulty: High; Recommended Action: Fix Code) (source: A1)"
    assert a1["difficulty_likelihood"] == "Difficulty: High"
    assert a1["status"] == "Resolved" and a1["remediation_verified_by"] == "firm"
    assert a1["resolved_in"] == "https://github.com/Moonlight-Protocol/soroban-core/commit/97922db"
    assert a1["location"].startswith("modules/primitives/src/lib.rs:L120-L163")
    assert a1["remediation_notes"].startswith("Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/38")

    b1 = by_id["MOONLIGHT-RV-002"]
    assert b1["unified_severity"] == "Informational" and b1["difficulty_likelihood"] is None
    assert b1["firm_severity_rating"] == "Informative (Recommended Action: Fix Code) (source: B1)"
    assert any("f9cdd3b" in n for n in b1["conversion_notes"])

    b12 = by_id["MOONLIGHT-RV-003"]
    assert b12["status"] == "Acknowledged" and b12["remediation_verified_by"] == "not-reviewed"
    assert "(source: B12)" in b12["firm_severity_rating"]
    assert "Acknowledged by client" not in b12["firm_severity_rating"]

    assert "Invariants" not in report["sections"]["assumptions_limitations"]
    assert "#### T. Trust assumptions" in report["sections"]["assumptions_limitations"]
    assert report["sections"]["disclaimer"]


@pytest.mark.network
def test_rv_moonlight():
    report = RuntimeVerificationConverter().convert(RV_URL)
    assert fetch(RV_URL).kind == "pdf"
    assert len(report["findings"]) == 15
    assert report["findings_summary"] == {
        "total": 15,
        "critical": 0,
        "high": 0,
        "moderate": 3,
        "low": 0,
        "informational": 12,
    }
    assert [f["id"] for f in report["findings"]][:3] == ["MOONLIGHT-RV-001", "MOONLIGHT-RV-002", "MOONLIGHT-RV-003"]
    assert all(f["location"] for f in report["findings"])
    _assert_clean_draft(report)
