import datetime as dt
import json

import pytest
from auditbank.converters.base import finalize
from auditbank.converters.veridise import VeridiseConverter, parse_date_range
from auditbank.parse import parse
from auditbank.render import render
from auditbank.validate import validate_text
from conftest import FIXTURES

TODAY = dt.date(2026, 10, 23)
DRAFT_WARNINGS = {"SIGNOFF_PENDING", "CONVERSION_NOTES_OPEN"}
VERIDISE_URL = "https://veridise.com/wp-content/uploads/2025/10/VAR-Redstone-251006-Oracles-SDK-V2.pdf"


def _assert_clean_draft(report):
    text = render(report)
    assert render(parse(text)) == text, "converter output must round-trip"
    problems = validate_text(text, today=TODAY)
    assert {p["code"] for p in problems} == DRAFT_WARNINGS, problems
    assert all(p["level"] == "warning" for p in problems)


def test_date_range():
    assert parse_date_range("Oct. 6–Oct. 14, 2025") == ("2025-10-06", "2025-10-14")
    assert parse_date_range("Sep. 28–Oct. 3, 2025") == ("2025-09-28", "2025-10-03")


def test_veridise_normalize_fixture():
    firm_report = json.loads((FIXTURES / "veridise-redstone.extracted.json").read_text())
    report = finalize(VeridiseConverter().normalize(firm_report, "redstone"))
    _assert_clean_draft(report)

    meta = report["report"]
    assert meta["report_date"] == "2025-10-27" and meta["report_version"] == "V2"
    assert (meta["engagement_start"], meta["engagement_end"]) == ("2025-10-06", "2025-10-14")
    assert meta["auditors"] == ["Alberto Gonzalez", "Aayushman Thapa Magar"]
    assert meta["firm_contact"] == "contact@veridise.com"
    assert report["effort"] == {"engineer_weeks": 2, "reviewers": 2}
    commits = {r["commit_start"] for r in report["scope"]["repositories"]}
    assert commits == {"ff1de9da45e874ec09366ce4406e110131056a59", "726ac4bd7770ef16ab987d361b4683613bd983a0"}

    by_source = {f["firm_severity_rating"].rsplit("(source: ", 1)[1].rstrip(")"): f for f in report["findings"]}
    assert set(by_source) == {"V-RED-VUL-001", "V-RED-VUL-005", "V-RED-APP-VUL-001"}

    fixed = by_source["V-RED-VUL-001"]
    assert fixed["status"] == "Resolved" and fixed["remediation_verified_by"] == "firm"
    assert fixed["resolved_in"] == "https://github.com/redstone-finance/rust-sdk/pull/60 (e24a58a)"
    assert fixed["location"] == "rust-sdk/crates/redstone/src/types/signer_address.rs:L25"

    ack = by_source["V-RED-VUL-005"]
    assert ack["unified_severity"] == "Informational" and ack["status"] == "Acknowledged"
    assert ack["category"] == "code-quality"

    intended = by_source["V-RED-APP-VUL-001"]
    assert intended["status"] == "Risk Accepted" and intended["remediation_verified_by"] == "not-reviewed"
    assert any("intended behavior" in n for n in intended["conversion_notes"])
    assert intended["id"] == "REDSTONE-VER-003"  # appendix items continue the main numbering

    appendix = report["sections"]["appendix"]
    assert "Items the firm withdrew as invalid" in appendix and "V-RED-APP-VUL-005" in appendix
    assert any("All Rights Reserved" in n for n in report["conversion_notes"])


@pytest.mark.network
def test_veridise_redstone():
    report = VeridiseConverter().convert(VERIDISE_URL)
    assert len(report["findings"]) == 9  # 5 main + 4 intended behavior; 1 invalid item excluded
    assert report["findings_summary"] == {
        "total": 9,
        "critical": 0,
        "high": 0,
        "moderate": 0,
        "low": 8,
        "informational": 1,
    }
    assert report["report"]["pdf_url"] == VERIDISE_URL
    warnings = [f for f in report["findings"] if f["firm_severity_rating"].startswith("Warning")]
    assert len(warnings) == 5 and all(f["unified_severity"] == "Low" for f in warnings)
    assert "V-RED-APP-VUL-005" in report["sections"]["appendix"]
    _assert_clean_draft(report)
