import datetime as dt

import pytest
from auditbank.paths import REPORTS_DIR
from auditbank.validate import validate_file, validate_report, validate_text
from conftest import FIXTURES

TODAY = dt.date(2026, 10, 23)


def codes(problems, level=None):
    return {p["code"] for p in problems if level is None or p["level"] == level}


def test_minimal_valid_has_no_problems(valid_report):
    assert validate_report(valid_report, today=TODAY) == []


def test_invalid_counts_fixture():
    problems = validate_file(FIXTURES / "invalid-counts.md", today=TODAY)
    assert codes(problems, "error") == {"COUNTS"}


def test_parse_error():
    assert codes(validate_text("no frontmatter here")) == {"PARSE"}


def _set(report, dotted, value):
    target = report
    *parts, last = dotted.split(".")
    for part in parts:
        target = target[int(part)] if part.isdigit() else target[part]
    target[int(last) if last.isdigit() else last] = value


# (code, level, list of (dotted path, value) mutations)
CASES = [
    ("SCHEMA", "error", [("findings.0.category", "reentrancy")]),
    ("SCHEMA", "error", [("report.pdf_url", None)]),
    ("SCHEMA", "error", [("scope.repositories.0.commit_start", "abc123")]),
    ("SCHEMA", "error", [("findings.0.id", "EX-XYZ-001")]),
    ("COUNTS", "error", [("findings_summary.total", 4)]),
    (
        "ORDER",
        "error",
        [("findings.0.unified_severity", "Low"), ("findings_summary.high", 0), ("findings_summary.low", 1)],
    ),
    ("IDS_UNIQUE", "error", [("findings.1.id", "EX-RV-001")]),
    ("ID_FIRM_MATCH", "error", [("findings.2.id", "EX-HAL-003")]),
    ("RESOLVED_NEEDS_FIRM", "error", [("findings.0.remediation_verified_by", "not-reviewed")]),
    ("CLIENT_CLAIM", "error", [("findings.1.remediation_verified_by", "client-reported")]),
    ("POC_REQUIRED", "error", [("findings.0.proof", None)]),
    ("REDACTION_CONSISTENT", "error", [("findings.1.location", "withheld")]),
    ("REDACTION_CONSISTENT", "error", [("publication.disclosure_status", "redacted")]),
    (
        "EMBARGO_DATE",
        "warning",
        [
            ("publication.disclosure_status", "embargoed"),
            ("publication.embargo_until", "2026-01-01"),
            ("findings.1.location", "withheld"),
        ],
    ),
    (
        "COMMIT_FINAL_NEEDS_FIX_REVIEW",
        "warning",
        [
            ("audit.type", ["code-review"]),
            ("findings.0.status", "Fixed - Not Verified"),
            ("findings.0.remediation_verified_by", "client-reported"),
        ],
    ),
    ("DISCLAIMER_PRESENT", "error", [("sections.disclaimer", "")]),
    ("DISCLAIMER_PRESENT", "error", [("sections.disclaimer", "Our own terms."), ("publication.license", "")]),
    ("CONVERSION_NOTES_OPEN", "warning", [("findings.0.conversion_notes", ["category inferred"])]),
    ("SIGNOFF_PENDING", "warning", [("publication.conversion_method", None)]),
]


@pytest.mark.parametrize("code,level,mutations", CASES, ids=[f"{c[0]}-{i}" for i, c in enumerate(CASES)])
def test_each_rule_fires(valid_report, code, level, mutations):
    for dotted, value in mutations:
        _set(valid_report, dotted, value)
    problems = validate_report(valid_report, today=TODAY)
    assert code in codes(problems, level), problems


def test_withheld_proof_satisfies_poc_but_requires_redacted_status(valid_report):
    valid_report["findings"][0]["proof"] = "Withheld pending remediation"
    problems = validate_report(valid_report, today=TODAY)
    assert "POC_REQUIRED" not in codes(problems)
    assert "REDACTION_CONSISTENT" in codes(problems)
    valid_report["publication"]["disclosure_status"] = "redacted"
    assert validate_report(valid_report, today=TODAY) == []


def test_future_embargo_is_clean(valid_report):
    valid_report["publication"].update(disclosure_status="embargoed", embargo_until="2027-01-01")
    valid_report["findings"][1]["location"] = "withheld"
    assert validate_report(valid_report, today=TODAY) == []


def test_filename_rule(valid_report):
    good = REPORTS_DIR / "example-escrow" / "example-escrow--rv--2026-03-20.md"
    assert "FILENAME" not in codes(validate_report(valid_report, good, TODAY))
    bad = REPORTS_DIR / "example-escrow" / "example-escrow--hal--2026-03-20.md"
    assert "FILENAME" in codes(validate_report(valid_report, bad, TODAY), "error")
    nested = REPORTS_DIR / "a" / "b" / "example-escrow--rv--2026-03-20.md"
    assert "FILENAME" in codes(validate_report(valid_report, nested, TODAY), "error")
    outside = FIXTURES / "anything.md"
    assert "FILENAME" not in codes(validate_report(valid_report, outside, TODAY))
