"""Schema + cross-field validation. Every problem is {level, code, path, message}.

The site re-implements the cross-field rules in JS with the same codes, so CI and the
browser print identical tables.
"""

import datetime as dt
import re
from pathlib import Path

from jsonschema import Draft202012Validator

from .parse import ParseError, parse
from .paths import REPORTS_DIR, firm_abbrev, report_schema, vocab
from .render import SEVERITY_ORDER

ERROR, WARNING = "error", "warning"
WITHHELD_PROOF = "withheld pending remediation"
DISCLAIMER_TERMS = [("point-in-time", "snapshot"), ("warranty",), ("authoritative",)]


def _problem(level, code, path, message):
    return {"level": level, "code": code, "path": path, "message": message}


def _path(parts) -> str:
    out = "$"
    for part in parts:
        out += f"[{part}]" if isinstance(part, int) else f".{part}"
    return out


def schema_errors(report: dict) -> list[dict]:
    validator = Draft202012Validator(report_schema())
    problems = []
    for err in sorted(validator.iter_errors(report), key=lambda e: list(map(str, e.absolute_path))):
        message = err.message
        if err.validator == "anyOf" and list(err.absolute_path) == ["report"]:
            message = "at least one of report.pdf_url / report.firm_report_url must be a URL"
        problems.append(_problem(ERROR, "SCHEMA", _path(err.absolute_path), message))
    return problems


def _findings(report):
    findings = report.get("findings")
    return [f for f in findings if isinstance(f, dict)] if isinstance(findings, list) else []


def _id_number(finding_id: str) -> int:
    match = re.search(r"-(\d+)$", finding_id or "")
    return int(match.group(1)) if match else 0


def check_counts(report):
    summary = report.get("findings_summary") or {}
    findings = _findings(report)
    problems = []
    for sev in SEVERITY_ORDER:
        key = sev.lower()
        actual = sum(1 for f in findings if f.get("unified_severity") == sev)
        if summary.get(key) != actual:
            problems.append(
                _problem(
                    ERROR,
                    "COUNTS",
                    f"$.findings_summary.{key}",
                    f"findings_summary.{key} is {summary.get(key)!r} but there are {actual} {sev} findings",
                )
            )
    parts = [summary.get(s.lower()) for s in SEVERITY_ORDER]
    if all(isinstance(p, int) for p in parts) and summary.get("total") != sum(parts):
        problems.append(
            _problem(
                ERROR,
                "COUNTS",
                "$.findings_summary.total",
                f"findings_summary.total is {summary.get('total')!r} but the severity counts sum to {sum(parts)}",
            )
        )
    if summary.get("total") != len(findings):
        problems.append(
            _problem(
                ERROR,
                "COUNTS",
                "$.findings_summary.total",
                f"findings_summary.total is {summary.get('total')!r} but the report has {len(findings)} findings",
            )
        )
    return problems


def check_order(report):
    findings = _findings(report)

    def key(f):
        sev = f.get("unified_severity")
        rank = SEVERITY_ORDER.index(sev) if sev in SEVERITY_ORDER else len(SEVERITY_ORDER)
        return (rank, _id_number(f.get("id")))

    for i in range(1, len(findings)):
        if key(findings[i]) < key(findings[i - 1]):
            return [
                _problem(
                    ERROR,
                    "ORDER",
                    f"$.findings[{i}]",
                    f"{findings[i].get('id')} is out of order: findings must run Critical -> Informational, "
                    "then by ID within a severity",
                )
            ]
    return []


def check_ids(report):
    problems, seen = [], set()
    expected = firm_abbrev((report.get("report") or {}).get("audit_firm"))
    for i, f in enumerate(_findings(report)):
        fid = f.get("id")
        if fid in seen:
            problems.append(_problem(ERROR, "IDS_UNIQUE", f"$.findings[{i}].id", f"duplicate finding ID {fid}"))
        seen.add(fid)
        parts = (fid or "").split("-")
        if expected and len(parts) == 3 and parts[1] != expected:
            problems.append(
                _problem(
                    ERROR,
                    "ID_FIRM_MATCH",
                    f"$.findings[{i}].id",
                    f"{fid} uses firm abbreviation {parts[1]} but report.audit_firm maps to {expected}",
                )
            )
    return problems


def check_remediation(report):
    problems = []
    for i, f in enumerate(_findings(report)):
        status, verified = f.get("status"), f.get("remediation_verified_by")
        if status == "Resolved" and verified != "firm":
            problems.append(
                _problem(
                    ERROR,
                    "RESOLVED_NEEDS_FIRM",
                    f"$.findings[{i}].status",
                    f"{f.get('id')}: 'Resolved' requires remediation_verified_by 'firm' "
                    "(use 'Fixed - Not Verified' for unverified client claims)",
                )
            )
        if verified == "client-reported" and status not in ("Fixed - Not Verified", "Partially Resolved"):
            problems.append(
                _problem(
                    ERROR,
                    "CLIENT_CLAIM",
                    f"$.findings[{i}].status",
                    f"{f.get('id')}: client-reported remediation must use status 'Fixed - Not Verified' "
                    "or 'Partially Resolved'",
                )
            )
    return problems


def check_poc(report):
    return [
        _problem(
            ERROR,
            "POC_REQUIRED",
            f"$.findings[{i}].proof",
            f"{f.get('id')}: {f.get('unified_severity')} findings need a Proof / attack path "
            "(or 'Withheld pending remediation')",
        )
        for i, f in enumerate(_findings(report))
        if f.get("unified_severity") in ("Critical", "High") and not f.get("proof")
    ]


def _withheld_items(report) -> list[str]:
    w = vocab()["withheld"]
    items = []
    scope = report.get("scope") or {}
    for i, repo in enumerate(scope.get("repositories") or []):
        for key in ("url", "commit_start"):
            if isinstance(repo, dict) and repo.get(key) == w:
                items.append(f"$.scope.repositories[{i}].{key}")
    if scope.get("in_scope_paths") == w:
        items.append("$.scope.in_scope_paths")
    for i, f in enumerate(_findings(report)):
        if f.get("location") == w:
            items.append(f"$.findings[{i}].location")
        if (f.get("redacted") or {}).get("value") is True:
            items.append(f"$.findings[{i}].redacted")
        if (f.get("proof") or "").strip().rstrip(".").lower() == WITHHELD_PROOF:
            items.append(f"$.findings[{i}].proof")
    return items


def check_redaction(report):
    status = (report.get("publication") or {}).get("disclosure_status")
    items = _withheld_items(report)
    if items and status not in ("redacted", "embargoed"):
        return [
            _problem(
                ERROR,
                "REDACTION_CONSISTENT",
                "$.publication.disclosure_status",
                f"disclosure_status is {status!r} but content is withheld/redacted at {', '.join(items)}; "
                "use 'redacted' or 'embargoed'",
            )
        ]
    if status == "redacted" and not items:
        return [
            _problem(
                ERROR,
                "REDACTION_CONSISTENT",
                "$.publication.disclosure_status",
                "disclosure_status is 'redacted' but nothing is withheld or redacted",
            )
        ]
    return []


def check_embargo(report, today: dt.date):
    pub = report.get("publication") or {}
    if pub.get("disclosure_status") != "embargoed":
        return []
    until = pub.get("embargo_until")
    if not until:
        return [_problem(ERROR, "EMBARGO_DATE", "$.publication.embargo_until", "embargoed reports need embargo_until")]
    try:
        elapsed = dt.date.fromisoformat(str(until)) <= today
    except ValueError:
        return []  # schema already flags the format
    if elapsed:
        return [
            _problem(
                WARNING,
                "EMBARGO_DATE",
                "$.publication.embargo_until",
                f"embargo_until {until} has passed; set disclosure_status to 'public' (or 'redacted')",
            )
        ]
    return []


def check_commit_final(report):
    audit_types = (report.get("audit") or {}).get("type") or []
    firm_verified = any(f.get("remediation_verified_by") == "firm" for f in _findings(report))
    problems = []
    for i, repo in enumerate((report.get("scope") or {}).get("repositories") or []):
        if (
            isinstance(repo, dict)
            and repo.get("commit_final")
            and "fix-review" not in audit_types
            and not firm_verified
        ):
            problems.append(
                _problem(
                    WARNING,
                    "COMMIT_FINAL_NEEDS_FIX_REVIEW",
                    f"$.scope.repositories[{i}].commit_final",
                    "commit_final is set but no fix review is recorded (add 'fix-review' to audit.type, "
                    "or set commit_final to null)",
                )
            )
    return problems


def check_disclaimer(report):
    text = ((report.get("sections") or {}).get("disclaimer") or "").lower()
    license_ = (report.get("publication") or {}).get("license")
    if not text.strip():
        return [
            _problem(
                ERROR, "DISCLAIMER_PRESENT", "$.sections.disclaimer", "Section 7 (Disclaimer and license) is mandatory"
            )
        ]
    has_default_terms = all(any(t in text for t in group) for group in DISCLAIMER_TERMS)
    if not has_default_terms and not license_:
        return [
            _problem(
                ERROR,
                "DISCLAIMER_PRESENT",
                "$.sections.disclaimer",
                "a substituted firm disclaimer requires publication.license to be stated",
            )
        ]
    return []


def check_filename(report, path: Path | None):
    if path is None or not path.is_relative_to(REPORTS_DIR):
        return []
    meta = report.get("report") or {}
    abbrev = (firm_abbrev(meta.get("audit_firm")) or "?").lower()
    slug = path.parent.name
    expected = f"{slug}--{abbrev}--{meta.get('report_date')}.md"
    problems = []
    if path.parent.parent != REPORTS_DIR:
        problems.append(_problem(ERROR, "FILENAME", "$", f"reports live at reports/{{slug}}/{expected}"))
    if path.name != expected:
        problems.append(
            _problem(
                ERROR,
                "FILENAME",
                "$",
                f"filename {path.name!r} should be {expected!r} (directory slug, firm abbreviation, report_date)",
            )
        )
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        problems.append(_problem(ERROR, "FILENAME", "$", f"project slug {slug!r} must be lowercase kebab-case"))
    return problems


def check_conversion(report):
    problems = []
    notes = list(report.get("conversion_notes") or [])
    notes += [n for f in _findings(report) for n in (f.get("conversion_notes") or [])]
    if notes:
        problems.append(
            _problem(
                WARNING,
                "CONVERSION_NOTES_OPEN",
                "$",
                f"{len(notes)} CONVERSION-NOTE comment(s) remain for the firm reviewer to resolve",
            )
        )
    if (report.get("publication") or {}).get("conversion_method") is None:
        problems.append(
            _problem(
                WARNING,
                "SIGNOFF_PENDING",
                "$.publication.conversion_method",
                "conversion_method is unset: set by the merge step once a firm engineer approves the PR",
            )
        )
    return problems


def validate_report(report: dict, path: Path | None = None, today: dt.date | None = None) -> list[dict]:
    today = today or dt.date.today()
    problems = schema_errors(report)
    problems += check_counts(report)
    problems += check_order(report)
    problems += check_ids(report)
    problems += check_remediation(report)
    problems += check_poc(report)
    problems += check_redaction(report)
    problems += check_embargo(report, today)
    problems += check_commit_final(report)
    problems += check_disclaimer(report)
    problems += check_filename(report, path)
    problems += check_conversion(report)
    return problems


def validate_text(text: str, path: Path | None = None, today: dt.date | None = None) -> list[dict]:
    try:
        report = parse(text)
    except ParseError as exc:
        return [_problem(ERROR, "PARSE", "$", str(exc))]
    return validate_report(report, path, today)


def validate_file(path, today: dt.date | None = None) -> list[dict]:
    path = Path(path)
    return validate_text(path.read_text(encoding="utf-8"), path.resolve(), today)


def has_errors(problems: list[dict]) -> bool:
    return any(p["level"] == ERROR for p in problems)
