"""Parsed report dict -> standard markdown, in the exact template layout.

Every converter ends by calling `render`, and `parse(render(x)) == x` for any valid report dict.
"""

import yaml

from . import template
from .parse import FINDING_KEYS

BODY_KEYS = {"heading", "conversion_notes", "findings", "sections"}
SEVERITY_ORDER = ["Critical", "High", "Moderate", "Low", "Informational"]

FIELD_ROWS = [
    ("Unified severity", "unified_severity"),
    ("Firm severity rating", "firm_severity_rating"),
    ("Difficulty / likelihood", "difficulty_likelihood"),
    ("Status", "status"),
    ("Remediation verified by", "remediation_verified_by"),
    ("Category", "category"),
    ("Location", "location"),
    ("Resolved in", "resolved_in"),
    ("Redacted", "redacted"),
]
LEADS = [
    ("Description", "description"),
    ("Impact", "impact"),
    ("Proof / attack path", "proof"),
    ("Recommendation", "recommendation"),
    ("Remediation notes", "remediation_notes"),
]
SECTIONS = [
    ("1. Executive summary", "executive_summary"),
    ("2. Project context", "project_context"),
    ("3. Findings", None),
    ("4. Unified severity definitions", None),
    ("5. Assumptions and limitations", "assumptions_limitations"),
    ("6. Methodology", "methodology"),
    ("7. Disclaimer and license", "disclaimer"),
    ("8. Appendix", "appendix"),
]
OPTIONAL_SECTIONS = {"methodology", "appendix"}


class _Dumper(yaml.SafeDumper):
    """Indent block sequences under their key, as the template does."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def _str(dumper, value):
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Dumper.add_representer(str, _str)


def render_frontmatter(report: dict) -> str:
    frontmatter = {k: v for k, v in report.items() if k not in BODY_KEYS}
    return yaml.dump(
        frontmatter,
        Dumper=_Dumper,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=1_000_000,
    )


def sort_findings(findings: list[dict]) -> list[dict]:
    """Template order: unified severity Critical -> Informational, then finding ID."""

    def key(f):
        sev = f.get("unified_severity")
        return (SEVERITY_ORDER.index(sev) if sev in SEVERITY_ORDER else len(SEVERITY_ORDER), f.get("id", ""))

    return sorted(findings, key=key)


def _cell(key: str, value) -> str:
    if key == "redacted":
        value = value or {"value": False, "reason": None}
        if value.get("value") is True:
            return f"true: {value['reason']}" if value.get("reason") else "true"
        return "false"
    if value is None:
        return "null"
    if key == "location" and value != "withheld":
        value = ", ".join(f"`{part.strip()}`" for part in str(value).split(","))
    return str(value).replace("|", "\\|").replace("\n", " ")


def _note(text: str) -> str:
    return f"<!-- CONVERSION-NOTE: {text} -->"


def render_finding(finding: dict) -> str:
    out = [f"### [{finding.get('id', '')}] {finding.get('title', '')}", "", "| Field | Value |", "|---|---|"]
    out += [f"| **{label}** | {_cell(key, finding.get(key))} |" for label, key in FIELD_ROWS]
    out.append("")
    for note in finding.get("conversion_notes") or []:
        out += [_note(note), ""]
    for label, key in LEADS:
        value = finding.get(key)
        out += [f"**{label}.**", "", "null" if value is None else value, ""]
    out += ["---", ""]
    return "\n".join(out)


def render(report: dict) -> str:
    sections = report.get("sections") or {}
    out = ["---", render_frontmatter(report).rstrip("\n"), "---", "", f"# {report.get('heading', '')}", ""]
    for note in report.get("conversion_notes") or []:
        out += [_note(note), ""]
    for title, key in SECTIONS:
        if key in OPTIONAL_SECTIONS and not sections.get(key):
            continue
        out += [f"## {title}", ""]
        if title.startswith("3."):
            out += [render_finding(f) for f in sort_findings(report.get("findings") or [])]
        elif title.startswith("4."):
            out += [template.severity_definitions(), ""]
        else:
            out += [sections.get(key) or "", ""]
    return "\n".join(out).rstrip("\n") + "\n"


def blank_finding() -> dict:
    return {k: None for k in FINDING_KEYS} | {"redacted": {"value": False, "reason": None}, "conversion_notes": []}
