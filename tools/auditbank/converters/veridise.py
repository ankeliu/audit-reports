"""Veridise audit report PDFs ("Auditing Report ... Veridise Inc.").

Layout (verified against VAR-Redstone-251006-Oracles-SDK-V2.pdf): cover (Prepared For/By, Contact Us,
Version History), 1 Executive Summary (full commit hashes in footnote URLs), 2 Project Dashboard
(Tables 2.1-2.4), 3 Goals/Methodology/3.3 Scope/3.4 Classification, 4 Trust Model, 5 Vulnerability
Report with one box per finding (Severity/Commit/Type/Status/Location(s)/Confirmed Fix At) followed by
Description/Impact/Recommendation/Developers Response, and Appendix A.1 Intended Behavior / A.2 Invalid
Issues using the same box.
"""

import datetime as dt
import re
from urllib.parse import urlparse

from .base import (
    Converter,
    RawDoc,
    demote_headings,
    disclaimer_with_default,
    infer_category,
    new_finding,
    new_report,
    pdf_text,
    platform_from_text,
    project_code,
    severity_note,
    slugify,
    unified_from_label,
)

STATUS = {"Fixed": "Resolved", "Acknowledged": "Acknowledged", "Intended Behavior": "Risk Accepted"}
CATEGORY_FROM_TYPE = {
    "Data Validation": "data-validation",
    "Maintainability": "code-quality",
    "Usability Issue": "operational",
}
MONTHS = {
    m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)
}
DATE = r"([A-Z][a-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})"
FURNITURE = [
    re.compile(r"^\s*©\s*\d{4}\s+Veridise Inc\.?.*$"),
    re.compile(r"^\s*Veridise Audit Report:.*$"),
    re.compile(r"^\s*[ivx\d]+\s+Contents\s*$"),
]
TOP_SECTION = re.compile(
    r"^\s*(\d+|[A-Z])\s{2,}(Executive Summary|Project Dashboard|Security Assessment Goals and Scope|"
    r"Trust Model|Vulnerability Report|Appendix)\s*$"
)
SUB_SECTION = re.compile(r"^\s*(\d+\.\d+|[A-Z]\.\d+)\s+([A-Z][A-Za-z ,()/-]+)$")
FINDING_HEADING = re.compile(r"^\s*(?:\d+\.\d+\.\d+|[A-Z]\.\d+\.\d+)\s+(V-[A-Z0-9]+-(?:APP-)?VUL-\d+):\s*(.*)$")
BODY_LABEL = re.compile(
    r"^\s*(Description|Impact|Recommendation|Developers? Response|Proof of Concept|Why Invalid)\b[ \t]*(.*)$"
)
BODY_KEYS = {
    "Description": "description",
    "Impact": "impact",
    "Recommendation": "recommendation",
    "Developers Response": "developers_response",
    "Developer Response": "developers_response",
    "Proof of Concept": "proof",
    "Why Invalid": "why_invalid",
}
FILE_REF = re.compile(
    r"([\w.\-/\[\]]+\.(?:rs|toml|ts|js|sol|json|go|move))(?::\s*((?:\d+(?:-\d+)?)(?:,\s*\d+(?:-\d+)?)*))?"
)


# ------------------------------------------------------------------------------------------- PDF text


def strip_furniture(lines: list[str]) -> list[str]:
    return [line.replace("\f", "") for line in lines if not any(rx.match(line.replace("\f", "")) for rx in FURNITURE)]


def _code_spans(lines: list[str]) -> list[tuple[int, int]]:
    """Find numbered code listings (`1  fn x() {`, `2  ...`) and return [start, end) line spans."""
    numbered = re.compile(r"^\s*(\d+)(?:\s+(.*))?$")
    spans, i = [], 0
    while i < len(lines):
        m = numbered.match(lines[i])
        if not (m and m.group(1) == "1"):
            i += 1
            continue
        start, expected, j, last = i, 2, i + 1, i
        while j < len(lines):
            m2 = numbered.match(lines[j])
            if m2 and int(m2.group(1)) == expected:
                expected += 1
                last = j
                j += 1
                continue
            # continuation (wrapped code) or blank: keep only if the next numbered line follows soon
            nonblank = [k for k in range(j, len(lines)) if lines[k].strip()][:4]
            ahead = [k for k in nonblank if numbered.match(lines[k])]
            if ahead and int(numbered.match(lines[ahead[0]]).group(1)) == expected:
                j += 1
                continue
            break
        if expected > 2:
            spans.append((start, last + 1))
            i = last + 1
        else:
            i += 1
    return spans


def _code_block(lines: list[str]) -> str:
    """Strip listing numbers; wrapped continuation lines keep their parent's indentation."""
    numbered = re.compile(r"^\s*\d+(?:\s(.*))?$")
    body: list[str] = []
    for line in lines:
        m = numbered.match(line)
        if m:
            body.append(m.group(1) or "")
        elif line.strip():
            parent = next((b for b in reversed(body) if b.strip()), "")
            body.append(" " * (len(parent) - len(parent.lstrip())) + line.strip())
        elif body and body[-1].strip():
            body.append("")
    while body and not body[-1].strip():
        body.pop()
    indent = min((len(b) - len(b.lstrip()) for b in body if b.strip()), default=0)
    return "```\n" + "\n".join(b[indent:].rstrip() for b in body) + "\n```"


def reflow(lines: list[str]) -> str:
    """Hard-wrapped PDF prose -> markdown paragraphs, bullets, and fenced code listings."""
    lines = strip_furniture(lines)
    spans = _code_spans(lines)
    blocks: list[str] = []
    para: list[str] = []

    def flush():
        if para:
            blocks.append(" ".join(para))
            para.clear()

    i = 0
    while i < len(lines):
        span = next((s for s in spans if s[0] == i), None)
        if span:
            flush()
            blocks.append(_code_block(lines[span[0] : span[1]]))
            i = span[1]
            continue
        text = lines[i].strip()
        i += 1
        if not text:
            flush()
            continue
        bullet = re.match(r"^(▶|•|-)\s*(.*)$", text)
        numbered = re.match(r"^(\d+)\.\s+(.*)$", text)
        if bullet or numbered:
            flush()
            indent = "  " if bullet and bullet.group(1) == "•" else ""
            para.append(f"{indent}- {bullet.group(2)}" if bullet else f"{numbered.group(1)}. {numbered.group(2)}")
            continue
        if para and para[-1].endswith("-") and not para[-1].endswith(" -"):
            para[-1] += text
        else:
            para.append(text)
    flush()
    # bullets/numbered items were flushed as their own paragraphs; tighten them into lists
    out = "\n\n".join(b for b in blocks if b.strip())
    out = re.sub(r"\n\n(?=(?:  )?- |\d+\. )", "\n", out)
    return demote_headings(out).strip()


def parse_date(text: str | None) -> str | None:
    m = re.search(DATE, text or "")
    if not m or m.group(1)[:3].lower() not in MONTHS:
        return None
    return dt.date(int(m.group(3)), MONTHS[m.group(1)[:3].lower()], int(m.group(2))).isoformat()


def parse_date_range(text: str) -> tuple[str | None, str | None]:
    """`Oct. 6–Oct. 14, 2025` or `Oct. 6–14, 2025` or `Sep. 28, 2025–Oct. 3, 2025`."""
    m = re.search(
        r"([A-Z][a-z]+)\.?\s+(\d{1,2})(?:,\s*(\d{4}))?\s*[\u2013\u2014-]\s*(?:([A-Z][a-z]+)\.?\s+)?(\d{1,2}),\s*(\d{4})",
        text or "",
    )
    if not m:
        return None, None
    m1, d1, y1, m2, d2, y2 = m.groups()
    m2 = m2 or m1
    y1 = y1 or y2
    try:
        start = dt.date(int(y1), MONTHS[m1[:3].lower()], int(d1)).isoformat()
        end = dt.date(int(y2), MONTHS[m2[:3].lower()], int(d2)).isoformat()
    except (KeyError, ValueError):
        return None, None
    return start, end


# ---------------------------------------------------------------------------------------- converter


class VeridiseConverter(Converter):
    firm_abbrev = "VER"
    firm_name = "Veridise"

    @classmethod
    def matches(cls, source: str, raw: RawDoc | None = None) -> bool:
        return urlparse(source).netloc.endswith("veridise.com")

    # ---------------------------------------------------------------- extract

    def extract(self, raw: RawDoc) -> dict:
        text = pdf_text(raw.path)
        lines = text.replace("\r", "").split("\n")
        sections = _split_sections(lines)
        cover = sections.get("cover", [])

        exec_lines = sections.get("1", [])
        footnotes = {}
        for line in exec_lines:
            m = re.match(r"^\s*(\S)\s+(https?://\S+/tree/([0-9a-f]{40}))\s*$", line)
            if m:
                footnotes[m.group(3)] = m.group(2)
        exec_body = [line for line in exec_lines if not re.match(r"^\s*\S\s+https?://\S+/tree/[0-9a-f]{40}\s*$", line)]
        exec_paras = _labelled_paragraphs(exec_body)

        dashboard = "\n".join(sections.get("2", []))
        trust = sections.get("4", [])
        return {
            "url": raw.url,
            "source_file": raw.path.name,
            "project": _after_marker(cover, "FOR") or None,
            "cover_date": parse_date("\n".join(cover)),
            "client": _cover_field(cover, "Prepared For:")[:1],
            "auditors": _cover_field(cover, "Prepared By:"),
            "contact": next(iter(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", "\n".join(cover))), None),
            "versions": [
                {"date": parse_date(line), "label": m.group(1)}
                for line in cover
                if (m := re.search(r"\b(V\d+(?:\.\d+)?)\s*$", line.strip())) and parse_date(line)
            ],
            "copyright": next((line.strip() for line in cover if "©" in line), None),
            "commit_urls": footnotes,
            "executive_summary": exec_paras,
            "application_summary": _table_rows(dashboard, "Table 2.1", "Table 2.2"),
            "engagement_summary": _table_rows(dashboard, "Table 2.2", "Table 2.3"),
            "vulnerability_summary": _table_rows(dashboard, "Table 2.3", "Table 2.4"),
            "methodology": "\n\n".join(
                x for x in (reflow(sections.get("3.2", [])), _methodology_note(sections.get("3.3", []))) if x
            ),
            "scope": _scope(sections.get("3.3", [])),
            "trust_model": reflow(trust),
            "findings": _findings(sections),
        }

    # -------------------------------------------------------------- normalize

    def default_slug(self, firm_report: dict) -> str:
        return slugify((firm_report.get("client") or [""])[0] or firm_report.get("project") or "project")

    def normalize(self, fr: dict, project_slug: str | None) -> dict:
        slug = project_slug or self.default_slug(fr)
        report = new_report(self.firm_name)
        notes = report["conversion_notes"]
        meta = report["report"]
        code = project_code(slug)

        client = (fr.get("client") or [None])[0]
        project = fr.get("project") or client
        meta["client"] = client or project
        meta["title"] = f"{project}: Security Assessment"
        meta["auditors"] = fr.get("auditors") or None
        meta["firm_contact"] = fr.get("contact")
        meta["pdf_url"] = fr.get("url")
        if not meta["pdf_url"]:
            notes.append("report.pdf_url unknown (converted from a local file); add the public PDF URL")
        report["heading"] = f"{project}: Security Assessment by Veridise"

        versions = sorted((v for v in fr.get("versions") or [] if v.get("date")), key=lambda v: v["date"])
        if versions:
            meta["report_date"] = versions[-1]["date"]
            meta["report_version"] = versions[-1]["label"]
            # Archive rule: report_date is the latest Version History entry, not the cover date.
        else:
            meta["report_date"] = fr.get("cover_date")
            notes.append("no Version History found: report.report_date taken from the cover date; confirm")

        engagement = _row(fr.get("engagement_summary"), 0)
        start, end = parse_date_range(engagement.get("Dates", "")) if engagement else (None, None)
        meta["engagement_start"], meta["engagement_end"] = start, end
        if not start:
            notes.append("engagement dates not found in Table 2.2")
        if engagement.get("Method"):
            report["audit"]["methods"] = [engagement["Method"]]
        weeks = re.search(r"([\d.]+)\s*person-weeks?", engagement.get("Level of Effort", ""))
        report["effort"]["engineer_weeks"] = _number(weeks.group(1)) if weeks else None
        consultants = engagement.get("Consultants Engaged", "")
        report["effort"]["reviewers"] = int(consultants) if consultants.isdigit() else None

        # scope: one repository per commit footnote, ordered as Table 2.1 lists the commits
        scope = report["scope"]
        commit_urls = fr.get("commit_urls") or {}
        apps = fr.get("application_summary") or []
        short_order = [a.get("Version", "") for a in apps]
        repos = []
        for full, url in commit_urls.items():
            repo_url = url.split("/tree/")[0]
            short = next((s for s in short_order if s and full.startswith(s)), full[:6])
            repos.append((short_order.index(short) if short in short_order else 99, short, repo_url, full))
        repos.sort()
        scope["repositories"] = [{"url": r[2], "commit_start": r[3], "commit_final": None} for r in repos]
        if not repos:
            notes.append("no full commit hashes found in the Executive Summary footnotes; firm to supply")
        short_to_repo = {r[1]: r[2].rstrip("/").split("/")[-1] for r in repos}
        missing_short = [s for s in short_order if s and s not in short_to_repo]
        if missing_short:
            notes.append(f"Table 2.1 commits {missing_short} have no full hash in the source; firm to supply")
        platforms = " ".join(a.get("Platform", "") + " " + a.get("Name", "") for a in apps)
        types = {a.get("Type", "") for a in apps}
        scope["languages"] = sorted({t.lower() for t in types if t and t.lower() in {"rust", "solidity", "move", "go"}})
        platform_from_text(report, platforms + " " + " ".join(fr.get("executive_summary", {}).get("_intro", [])))
        in_scope, out_scope = [], []
        for group in fr.get("scope") or []:
            in_scope += group["include"]
            out_scope += group["exclude"]
        scope["in_scope_paths"] = in_scope
        scope["out_of_scope"] = out_scope

        # findings: main series first, then intended-behavior items; invalid items go to the appendix
        findings, invalid = [], []
        main = [f for f in fr["findings"] if f["group"] == "main"]
        appendix = [f for f in fr["findings"] if f["group"] != "main"]
        number = 0
        for f in main + appendix:
            if f.get("status") == "Invalid" or f["group"] == "invalid":
                invalid.append(f)
                continue
            number += 1
            findings.append(self._finding(f, f"{code}-VER-{number:03d}", short_to_repo))
        report["findings"] = findings
        if any(f["remediation_verified_by"] == "firm" for f in findings):
            report["audit"]["type"] = ["code-review", "fix-review"]

        summary = {r.get("Name", ""): r for r in fr.get("vulnerability_summary") or []}
        total = summary.get("TOTAL", {}).get("Number")
        if total and total.isdigit() and int(total) != len(main):
            notes.append(f"Table 2.3 reports {total} issues but {len(main)} were found in Section 5; check")

        sections = report["sections"]
        ex = fr.get("executive_summary") or {}
        summary_parts = [p for p in ex.get("_intro", [])]
        for label in ("Summary of Issues Detected", "Recommendations"):
            if ex.get(label):
                summary_parts.append(f"**{label}.** {ex[label]}")
        sections["executive_summary"] = "\n\n".join(summary_parts) or None
        notes.append("Section 1 assembled from Veridise's Executive Summary paragraphs; trim toward ~250 words")
        context = [f"**{label}.** {ex[label]}" for label in ("Project Summary", "Code Assessment") if ex.get(label)]
        sections["project_context"] = "\n\n".join(context) or None
        notes.append("Section 2 is Veridise's Project Summary; the key contracts table is not in the source")
        sections["assumptions_limitations"] = fr.get("trust_model") or None
        if not sections["assumptions_limitations"]:
            notes.append("no Trust Model section found; firm to supply assumptions")
        extra = [
            f"**{label}.** {ex[label]}" for label in ("Incident Response", "Volatility Scenarios") if ex.get(label)
        ]
        if extra and sections["assumptions_limitations"]:
            sections["assumptions_limitations"] += (
                "\n\n#### Operational considerations (from the Executive Summary)\n\n"
            )
            sections["assumptions_limitations"] += "\n\n".join(extra)
        sections["methodology"] = fr.get("methodology") or None

        firm_disclaimer = ex.get("Disclaimer")
        if firm_disclaimer and fr.get("copyright"):
            firm_disclaimer = f"{firm_disclaimer}\n\n{fr['copyright']}"
        sections["disclaimer"], note = disclaimer_with_default(self.firm_name, firm_disclaimer)
        if note:
            notes.append(note)
        if fr.get("copyright") and "all rights reserved" in fr["copyright"].lower():
            # One license note, not two: replace the generic default note with the specific conflict.
            notes[:] = [n for n in notes if not n.startswith("publication.license")]
            notes.append(
                f'publication.license defaulted to "Apache-2.0" but the PDF says "{fr["copyright"]}"; '
                "Veridise to confirm reuse terms"
            )

        if invalid:
            items = []
            for f in invalid:
                why = f.get("why_invalid") or "No reason stated."
                where = ", ".join(f.get("locations") or []) or "n/a"
                items.append(
                    f"- **{f['id']}: {f['title']}** (Veridise severity: {f.get('severity')}; type: {f.get('type')}; "
                    f"location: {where}). Why invalid: {why}"
                )
            sections["appendix"] = "#### Items the firm withdrew as invalid\n\n" + "\n".join(items)
        return report

    def _finding(self, f: dict, finding_id: str, short_to_repo: dict) -> dict:
        out = new_finding()
        notes = out["conversion_notes"]
        out["id"] = finding_id
        out["title"] = f["title"]

        severity = f.get("severity") or ""
        out["unified_severity"] = unified_from_label(severity)
        rating = f"{severity} (Veridise impact x likelihood matrix); Type: {f.get('type')}"
        out["firm_severity_rating"] = f"{rating} (source: {f['id']})"
        if severity.lower() == "warning":
            notes.append(
                'Veridise "Warning" mapped to unified "Low" (Warning sits between Info and Low in the Veridise '
                "matrix); Veridise to confirm"
            )
        elif out["unified_severity"]:
            notes.append(severity_note(severity, out["unified_severity"]))
        else:
            notes.append(f"Veridise severity {severity!r} has no unified mapping; firm to assign")

        status = f.get("status") or ""
        has_fix = bool(f.get("fix_urls") or f.get("fix_commits"))
        out["status"] = STATUS.get(status, "Unresolved")
        if status not in STATUS:
            notes.append(f"Veridise status {status!r} mapped to Unresolved; confirm")
        if status == "Intended Behavior":
            notes.append("client states intended behavior (Veridise Appendix A.1); recorded as Risk Accepted")
        if status == "Fixed" and has_fix:
            out["remediation_verified_by"] = "firm"
        elif status == "Fixed":
            out["status"], out["remediation_verified_by"] = "Fixed - Not Verified", "client-reported"
            notes.append("Fixed without a Confirmed Fix At entry: recorded as Fixed - Not Verified; confirm")
        else:
            out["remediation_verified_by"] = "not-reviewed"
        urls, commits = f.get("fix_urls") or [], f.get("fix_commits") or []
        if urls or commits:
            out["resolved_in"] = ", ".join(urls) + (
                f" ({', '.join(commits)})" if urls and commits else ", ".join(commits) if not urls else ""
            )

        vtype = f.get("type") or ""
        body = f.get("description") or ""
        if vtype in CATEGORY_FROM_TYPE:
            out["category"] = CATEGORY_FROM_TYPE[vtype]
            notes.append(f"category mapped from Veridise type '{vtype}': {out['category']}; confirm")
        else:
            out["category"] = infer_category(out["title"], body, out["unified_severity"])
            notes.append(f"category inferred from Veridise type '{vtype}' and content: {out['category']}")

        out["location"] = ", ".join(_format_location(loc) for loc in f.get("locations") or []) or None
        if out["location"] and "[...]" in out["location"]:
            notes.append("Veridise abbreviates paths with [...]; firm to supply full repo-relative paths")
        repo = short_to_repo.get(f.get("commit") or "")
        if f.get("commit") and not repo:
            notes.append(f"finding commit {f['commit']} does not match a scoped repository")

        out["description"] = body or None
        if f.get("impact"):
            out["impact"] = f["impact"]
        else:
            first = re.split(r"(?<=[.!?])\s", body.strip(), maxsplit=1)[0]
            out["impact"] = first or None
            notes.append("no Impact block in the source: Impact repeats the first sentence; firm to rewrite")
        out["proof"] = f.get("proof") or None
        out["recommendation"] = f.get("recommendation") or None
        out["remediation_notes"] = f.get("developers_response") or None
        if f["title"].lower().startswith("informational:") or "issues" in f["title"].lower():
            notes.append("the source groups several issues under one finding; firm may split them")
        return out


# ------------------------------------------------------------------------------------------ helpers


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    """Split the document into cover, top-level sections (`1`..`5`, `A`) and subsections (`3.3`, `A.2`)."""
    sections: dict[str, list[str]] = {"cover": []}
    current = ["cover"]
    seen_toc_end = False
    for line in lines:
        clean = line.replace("\f", "")
        if not seen_toc_end:
            # the table of contents repeats every heading; the body starts at the first heading after it
            if TOP_SECTION.match(clean) and "Executive Summary" in clean and not re.search(r"\s\d+\s*$", clean):
                seen_toc_end = True
            else:
                sections["cover"].append(clean)
                continue
        top = TOP_SECTION.match(clean)
        sub = SUB_SECTION.match(clean)
        if top:
            current = [top.group(1)]
            sections.setdefault(top.group(1), [])
            continue
        if sub and not FINDING_HEADING.match(clean):
            current = [current[0], sub.group(1)]
            sections.setdefault(sub.group(1), [])
            continue
        for key in current:
            sections[key].append(clean)
    return sections


def _after_marker(lines: list[str], marker: str) -> str:
    for i, line in enumerate(lines):
        if line.strip() == marker:
            return next((x.strip() for x in lines[i + 1 :] if x.strip()), "")
    return ""


def _cover_field(lines: list[str], label: str) -> list[str]:
    for i, line in enumerate(lines):
        if label in line:
            values = []
            for x in lines[i + 1 :]:
                if x.strip().startswith("▶") or "©" in x:
                    break
                if x.strip() and not x.strip().startswith("http"):
                    values.append(x.strip())
            return values
    return []


LABEL = re.compile(r"^([A-Z][A-Za-z]+(?: [A-Za-z]+){0,3})\.\s+([A-Z].*)$", re.S)


def _labelled_paragraphs(lines: list[str]) -> dict:
    """Executive Summary: untitled intro paragraphs plus `Label. Text` paragraphs."""
    spaced: list[str] = []
    for line in lines:
        prev = next((x for x in reversed(spaced) if x.strip()), "")
        if LABEL.match(line.strip()) and prev.rstrip().endswith("."):
            spaced.append("")
        spaced.append(line)
    out: dict = {"_intro": []}
    last = None
    for para in reflow(spaced).split("\n\n"):
        m = LABEL.match(para)
        if m and len(m.group(1)) <= 40:
            last = m.group(1)
            out[last] = m.group(2).strip()
        elif last:
            out[last] += "\n\n" + para
        else:
            out["_intro"].append(para)
    return out


def _table_rows(text: str, start: str, end: str) -> list[dict]:
    """Rows of a whitespace-aligned table between two caption markers."""
    a, b = text.find(start), text.find(end)
    if a < 0:
        return []
    block = [line for line in text[a : b if b > a else None].split("\n")[1:] if line.strip()]
    if not block:
        return []
    header = re.split(r"\s{2,}", block[0].strip())
    rows = []
    for line in block[1:]:
        cells = re.split(r"\s{2,}", line.strip())
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells, strict=True)))
    return rows


def _row(rows, index) -> dict:
    return rows[index] if rows and len(rows) > index else {}


def _number(text: str):
    value = float(text)
    return int(value) if value.is_integer() else value


def _scope(lines: list[str]) -> list[dict]:
    """3.3 Scope: `<label> on commit <short>:` then bullet paths, optional `Excluding:` bullets."""
    groups: list[dict] = []
    mode = "include"
    for raw in strip_furniture(lines):
        line = raw.strip()
        head = re.match(r"^(.*?)\s+on commit\s+([0-9a-f]{6,40}):?\s*$", line)
        if head:
            groups.append(
                {"label": f"{head.group(1)} @ {head.group(2)}", "commit": head.group(2), "include": [], "exclude": []}
            )
            mode = "include"
        elif line.startswith("Excluding"):
            mode = "exclude"
        elif groups and line.startswith("▶"):
            groups[-1][mode].append(line.lstrip("▶ ").strip())
        elif groups and line and not line.startswith("▶") and groups[-1]["include"]:
            # prose after the lists (e.g. "Methodology. ...") ends the scope listing
            if re.match(r"^[A-Z][a-z]+\.", line):
                break
    return groups


def _methodology_note(lines: list[str]) -> str:
    """The `Methodology.` paragraph Veridise places after the scope lists in 3.3."""
    lines = strip_furniture(lines)
    start = next((i for i, line in enumerate(lines) if line.strip().startswith("Methodology.")), None)
    return reflow(lines[start:]) if start is not None else ""


def _findings(sections: dict[str, list[str]]) -> list[dict]:
    blocks = [("main", sections.get("5", []) or sections.get("5.1", []))]
    blocks.append(("intended", sections.get("A.1", [])))
    blocks.append(("invalid", sections.get("A.2", [])))
    findings = []
    for group, lines in blocks:
        lines = strip_furniture(lines)
        starts = [i for i, line in enumerate(lines) if FINDING_HEADING.match(line)]
        for n, start in enumerate(starts):
            end = starts[n + 1] if n + 1 < len(starts) else len(lines)
            findings.append(_finding_block(lines[start:end], group))
    return findings


def _finding_block(lines: list[str], group: str) -> dict:
    head = FINDING_HEADING.match(lines[0])
    title_parts = [head.group(2).strip()]
    i = 1
    while i < len(lines) and lines[i].strip() and not re.search(r"\bSeverity\b", lines[i]):
        title_parts.append(lines[i].strip())
        i += 1
    box_start = next((k for k in range(i, len(lines)) if re.search(r"\bSeverity\b", lines[k])), len(lines))
    body_start = next((k for k in range(box_start, len(lines)) if BODY_LABEL.match(lines[k])), len(lines))
    box = lines[box_start:body_start]
    f = {"id": head.group(1), "group": group, "title": " ".join(title_parts)}
    f.update(_parse_box(box))

    current, buf = None, []
    fields: dict[str, list[str]] = {}
    for line in lines[body_start:]:
        m = BODY_LABEL.match(line)
        key = BODY_KEYS.get(m.group(1)) if m else None
        if key and key not in fields:
            if current:
                fields[current] = buf
            current, buf = key, [" " * (len(line) - len(line.lstrip())) + m.group(2)]
            continue
        buf.append(line)
    if current:
        fields[current] = buf
    for key, value in fields.items():
        f[key] = reflow(value) or None
    return f


def _parse_box(box: list[str]) -> dict:
    text = "\n".join(box)
    out: dict = {}
    m = re.search(r"Severity\s+(\S+)\s+Commit\s+([0-9a-f]+)", text)
    if m:
        out["severity"], out["commit"] = m.group(1), m.group(2)
    m = re.search(r"Type\s+(.+?)\s{2,}Status\s+(.+?)\s*$", text, re.M)
    if m:
        out["type"], out["status"] = m.group(1).strip(), m.group(2).strip()
    rest = "\n".join(line for line in box if not re.search(r"\b(Severity|Type)\b.*\b(Commit|Status)\b", line))
    rest = rest.replace("Location(s)", " ").replace("Confirmed Fix At", " ")
    # URLs wrap after "https:" or after a "/" at the end of a line
    joined = re.sub(r"(https?:|/)\s*\n\s*", r"\1", rest)
    urls = [u.rstrip(",.") for u in re.findall(r"https?://\S+", joined)]
    without_urls = re.sub(r"https?://\S+", " ", joined)
    commits = re.findall(r"(?<![\w/.])([0-9a-f]{7,40})(?![\w/.])", without_urls)
    flat = re.sub(r",\s*\n\s*(?=\d)", ", ", without_urls)
    flat = flat.replace("▶", " ")
    locations = []
    for path, lines_ in FILE_REF.findall(flat):
        locations.append(f"{path}:{lines_}" if lines_ else path)
    out["locations"] = locations
    out["fix_urls"] = urls
    out["fix_commits"] = [c for c in commits if not any(c in u for u in urls)]
    return out


def _format_location(loc: str) -> str:
    """`path:25` -> `path:L25`; `path:47-51` -> `path:L47-L51`; `path:38, 38-39` -> two entries."""
    if ":" not in loc:
        return loc
    path, spec = loc.split(":", 1)
    parts = []
    for rng in re.split(r",\s*", spec):
        a, _, b = rng.partition("-")
        parts.append(f"{path}:L{a}" + (f"-L{b}" if b and b != a else ""))
    return ", ".join(parts)
