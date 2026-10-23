"""Standard report markdown -> plain dict matching schema/report-schema.json.

The regexes live in schema/parse-rules.json so the site's JS parser uses the same ones.
Parsing is tolerant (missing fields are simply absent); the validator reports what is wrong.
"""

import datetime as dt
import re
from functools import cache

import yaml

from .paths import parse_rules

FINDING_KEYS = [
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
    "conversion_notes",
]
NULLABLE_FIELDS = {"difficulty_likelihood", "location", "resolved_in"}
NULLABLE_LEADS = {"proof", "remediation_notes"}


class ParseError(ValueError):
    pass


@cache
def _rx() -> dict[str, re.Pattern]:
    rules = parse_rules()
    multiline = {"conversion_note"}
    return {
        key: re.compile(value, 0 if key in multiline else re.M)
        for key, value in rules.items()
        if isinstance(value, str) and not key.startswith("$")
    }


def _normalize_scalars(value):
    """YAML turns unquoted dates into date objects; the schema expects YYYY-MM-DD strings."""
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _normalize_scalars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_scalars(v) for v in value]
    return value


def _is_null(text: str | None) -> bool:
    return text is None or text.strip().lower() in {"", "null", "none", "n/a", "—", "-"}


def _extract_notes(text: str) -> tuple[str, list[str]]:
    """Drop guidance comments, pull CONVERSION-NOTE comments out into a list."""
    rx = _rx()
    notes: list[str] = []

    def replace(match: re.Match) -> str:
        note = rx["conversion_note"].match(match.group(1))
        if note:
            notes.append(" ".join(note.group(1).split()))
        return ""

    return rx["comment"].sub(replace, text), notes


def _clean(text: str) -> str:
    """Strip outer whitespace and collapse the blank-line runs left behind by removed comments."""
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _split(lines: list[str], pattern: re.Pattern) -> list[tuple[re.Match | None, list[str]]]:
    """Split lines on heading-like matches, ignoring anything inside code fences."""
    chunks: list[tuple[re.Match | None, list[str]]] = [(None, [])]
    in_fence = False
    fence = _rx()["fence"]
    for line in lines:
        if fence.match(line):
            in_fence = not in_fence
        match = None if in_fence else pattern.match(line)
        if match:
            chunks.append((match, []))
        else:
            chunks[-1][1].append(line)
    return chunks


def _section_key(heading: str) -> str | None:
    name = _rx()["optional_marker"].sub("", heading).strip().lower()
    for prefix, key in parse_rules()["sections"]:
        if name.startswith(prefix):
            return key
    return None


def _parse_redacted(text: str) -> dict:
    text = text.strip()
    if text.lower() == "false":
        return {"value": False, "reason": None}
    match = _rx()["redacted_true"].match(text)
    if match:
        return {"value": True, "reason": match.group(1).strip()}
    if text.lower() == "true":
        return {"value": True, "reason": None}
    return {"value": text, "reason": None}  # left invalid on purpose; the schema flags it


def _parse_finding(match: re.Match, lines: list[str]) -> dict:
    rx = _rx()
    rules = parse_rules()
    block, notes = _extract_notes("\n".join(lines))
    block_lines = block.split("\n")
    while block_lines and (not block_lines[-1].strip() or rx["hr"].match(block_lines[-1])):
        block_lines.pop()

    finding: dict = {"id": match.group(1).strip(), "title": match.group(2).strip()}
    parts = _split(block_lines, rx["lead"])

    for line in parts[0][1]:
        row = rx["table_row"].match(line)
        if not row:
            continue
        key = rules["fields"].get(row.group(1).strip())
        if not key:
            continue
        value = row.group(2).replace("\\|", "|").strip()
        if key == "redacted":
            finding[key] = _parse_redacted(value)
        elif key == "location":
            finding[key] = None if _is_null(value) else value.replace("`", "")
        elif key == "resolved_in":
            finding[key] = None if _is_null(value) else value.strip("`")
        elif key in NULLABLE_FIELDS and _is_null(value):
            finding[key] = None
        else:
            finding[key] = value

    for lead, body in parts[1:]:
        key = rules["leads"][lead.group(1)]
        text = _clean("\n".join([lead.group(2), *body]))
        if key in NULLABLE_LEADS and _is_null(text):
            finding[key] = None
        else:
            finding[key] = text

    finding["conversion_notes"] = notes
    return {k: finding[k] for k in FINDING_KEYS if k in finding}


def parse(text: str) -> dict:
    rx = _rx()
    text = text.replace("\r\n", "\n").lstrip("﻿")
    fm = rx["frontmatter"].match(text)
    if not fm:
        raise ParseError("no YAML frontmatter: the file must start with a '---' fenced block")
    try:
        frontmatter = yaml.safe_load(fm.group(1))
    except yaml.YAMLError as exc:
        raise ParseError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(frontmatter, dict):
        raise ParseError("YAML frontmatter must be a mapping")

    report = _normalize_scalars(frontmatter)
    body_lines = text[fm.end() :].split("\n")

    heading = None
    body: list[str] = []
    for match, chunk in _split(body_lines, rx["h1"]):
        if match and heading is None:
            heading = match.group(1).strip()
        elif match:
            body.append(match.group(0))
        body += chunk

    report_notes: list[str] = []
    sections: dict = {}
    findings: list[dict] = []
    for match, lines in _split(body, rx["h2"]):
        key = _section_key(match.group(1)) if match else None
        if key == "findings":
            finding_chunks = _split(lines, rx["finding_heading"])
            _, preamble_notes = _extract_notes("\n".join(finding_chunks[0][1]))
            report_notes += preamble_notes
            findings = [_parse_finding(m, chunk) for m, chunk in finding_chunks[1:]]
            continue
        text_, notes = _extract_notes("\n".join(lines))
        report_notes += notes
        if key and key != "severity_definitions":
            sections[key] = _clean(text_) or None

    for optional in ("methodology", "appendix"):
        sections.setdefault(optional, None)

    report["heading"] = heading
    report["conversion_notes"] = report_notes
    report["findings"] = findings
    report["sections"] = sections
    return report


def parse_file(path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return parse(fh.read())
