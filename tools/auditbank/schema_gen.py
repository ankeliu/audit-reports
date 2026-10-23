"""Build schema/report-schema.json from schema/vocab.json (the single source of truth for enums)."""

import json

from .paths import SCHEMA_DIR, vocab

DATE = {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"}
DATE_OR_NULL = {"anyOf": [DATE, {"type": "null"}]}
URL = {"type": "string", "pattern": r"^https?://\S+$"}
URL_OR_NULL = {"anyOf": [URL, {"type": "null"}]}
SHA = {"type": "string", "pattern": "^[0-9a-f]{40}$"}
NONEMPTY = {"type": "string", "minLength": 1}
STR_OR_NULL = {"type": ["string", "null"]}
STR_LIST = {"type": "array", "items": NONEMPTY}
COUNT = {"type": "integer", "minimum": 0}


def _enum(values):
    return {"type": "string", "enum": list(values)}


def _obj(properties: dict, required=None) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties) if required is None else required,
        "properties": properties,
    }


def build() -> dict:
    v = vocab()
    withheld = {"const": v["withheld"]}
    firm_alt = "|".join(v["firms"])
    finding = _obj(
        {
            "id": {"type": "string", "pattern": rf"^[A-Z0-9]+-({firm_alt})-\d{{3}}$"},
            "title": NONEMPTY,
            "unified_severity": _enum(v["unified_severity"]),
            "firm_severity_rating": NONEMPTY,
            "difficulty_likelihood": STR_OR_NULL,
            "status": _enum(v["status"]),
            "remediation_verified_by": _enum(v["remediation_verified_by"]),
            "category": _enum(v["category"]),
            "location": NONEMPTY,
            "resolved_in": STR_OR_NULL,
            "redacted": _obj({"value": {"type": "boolean"}, "reason": STR_OR_NULL}),
            "description": NONEMPTY,
            "impact": NONEMPTY,
            "proof": STR_OR_NULL,
            "recommendation": NONEMPTY,
            "remediation_notes": STR_OR_NULL,
            "conversion_notes": STR_LIST,
        },
        required=[
            "id",
            "title",
            "unified_severity",
            "firm_severity_rating",
            "difficulty_likelihood",
            "status",
            "remediation_verified_by",
            "category",
            "location",
            "resolved_in",
            "redacted",
            "description",
            "impact",
            "proof",
            "recommendation",
            "remediation_notes",
        ],
    )
    report = _obj(
        {
            "title": NONEMPTY,
            "audit_firm": _enum(v["firms"].values()),
            "firm_contact": STR_OR_NULL,
            "auditors": {"anyOf": [STR_LIST, {"type": "null"}]},
            "client": NONEMPTY,
            "report_date": DATE,
            "engagement_start": DATE_OR_NULL,
            "engagement_end": DATE_OR_NULL,
            "report_version": NONEMPTY,
            "pdf_url": URL_OR_NULL,
            "firm_report_url": URL_OR_NULL,
        }
    )
    # The PDF or firm page is the authoritative document: at least one link must be present.
    report["anyOf"] = [
        {"properties": {"pdf_url": URL}},
        {"properties": {"firm_report_url": URL}},
    ]
    publication = _obj(
        {
            "disclosure_status": _enum(v["disclosure_status"]),
            "embargo_until": DATE_OR_NULL,
            "license": NONEMPTY,
            "conversion_method": {"anyOf": [_enum(v["conversion_method"]), {"type": "null"}]},
        }
    )
    publication["if"] = {"properties": {"disclosure_status": {"const": "embargoed"}}}
    publication["then"] = {"properties": {"embargo_until": DATE}}
    publication["else"] = {"properties": {"embargo_until": {"type": "null"}}}
    repository = _obj(
        {
            "url": {"anyOf": [URL, withheld]},
            "commit_start": {"anyOf": [SHA, withheld]},
            "commit_final": {"anyOf": [SHA, {"type": "null"}]},
        }
    )
    section_text = NONEMPTY
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/ankeliu/audit-reports/schema/report-schema.json",
        "title": "Stellar Audit Bank standard audit report (parsed form)",
        "description": (
            "Generated from schema/vocab.json by `auditbank schema --write`; do not edit by hand. "
            "Describes the parsed report: YAML frontmatter plus `heading`, `conversion_notes`, "
            "`findings` and `sections` extracted from the markdown body."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "report",
            "publication",
            "audit",
            "scope",
            "findings_summary",
            "severity_standard",
            "heading",
            "findings",
            "sections",
        ],
        "properties": {
            "schema_version": {"const": v["schema_version"]},
            "report": report,
            "publication": publication,
            "audit": _obj(
                {
                    "type": {"type": "array", "minItems": 1, "items": _enum(v["audit_type"])},
                    "methods": STR_LIST,
                    "tooling": {"anyOf": [STR_LIST, {"type": "null"}]},
                },
                required=["type"],
            ),
            "effort": _obj(
                {
                    "engineer_weeks": {"type": ["number", "null"], "minimum": 0},
                    "reviewers": {"type": ["integer", "null"], "minimum": 0},
                }
            ),
            "scope": _obj(
                {
                    "chain": NONEMPTY,
                    "platform": _enum(v["platform"]),
                    "languages": STR_LIST,
                    "repositories": {"type": "array", "minItems": 1, "items": repository},
                    "in_scope_paths": {"anyOf": [STR_LIST, withheld]},
                    "out_of_scope": STR_LIST,
                    "loc": {"type": ["integer", "null"], "minimum": 0},
                },
                required=["chain", "platform", "repositories", "in_scope_paths"],
            ),
            "findings_summary": _obj(
                {k: COUNT for k in ("total", "critical", "high", "moderate", "low", "informational")}
            ),
            "severity_standard": {"const": f"audit-bank-v{v['schema_version']}"},
            "heading": NONEMPTY,
            "conversion_notes": STR_LIST,
            "findings": {"type": "array", "items": finding},
            "sections": _obj(
                {
                    "executive_summary": section_text,
                    "project_context": section_text,
                    "assumptions_limitations": section_text,
                    "methodology": STR_OR_NULL,
                    "disclaimer": section_text,
                    "appendix": STR_OR_NULL,
                },
                required=["executive_summary", "project_context", "assumptions_limitations", "disclaimer"],
            ),
        },
    }


def render_json() -> str:
    return json.dumps(build(), indent=2) + "\n"


def write() -> None:
    (SCHEMA_DIR / "report-schema.json").write_text(render_json())


def is_current() -> bool:
    path = SCHEMA_DIR / "report-schema.json"
    return path.exists() and path.read_text() == render_json()
