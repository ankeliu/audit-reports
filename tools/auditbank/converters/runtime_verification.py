"""Runtime Verification PDF reports (e.g. strapi.runtimeverification.com/uploads/...pdf).

Text comes from `pdftotext -layout` (pdfplumber fallback). Structure, verified on the Moonlight report:
`Delivered: <Month D, YYYY>`, then body headings at column 0 (Disclaimer, Executive Summary, Scope,
Methodology, ..., Invariants, Findings, Informative Findings, Appendix). Each finding opens with
`[A1] <title, may wrap>` then `Severity: X  Difficulty: Y  Recommended Action: Z  [Addressed by client]`
and has `Description` / `Recommendation` / `Status` blocks. Code excerpts are introduced by
`<org>/<repo>/<path>` and `Line N to M in <short commit>`, followed by numbered source lines.
"""

import datetime as dt
import re
import textwrap
from pathlib import Path
from urllib.parse import urlparse

from .base import (
    Converter,
    RawDoc,
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

HEADINGS = [
    "Disclaimer",
    "Executive Summary",
    "Scope",
    "Methodology",
    "Roles Description and Analysis",
    "Business Logic and Expected Flow of Operations",
    "Invariants",
    "Findings",
    "Informative Findings",
    "Appendix",
]
KNOWN_TOOLS = [
    "Almanax",
    "cargo audit",
    "cargo outdated",
    "cargo clippy",
    "cargo fuzz",
    "Kani",
    "Komet",
    "K Framework",
    "Slither",
    "Echidna",
    "proptest",
    "Scout",
]
MAX_CODE_LINES = 15

FOOTER = re.compile(r"^\s*\d+/\d+\s*$")
FINDING_HEADER = re.compile(r"^\[([A-Z]\d+)\]\s*(.*)$")
SEVERITY_LINE = re.compile(
    r"^\s*Severity:\s*(?P<severity>\w+)"
    r"(?:\s+Difficulty:\s*(?P<difficulty>\w+))?"
    r"(?:\s+Recommended Action:\s*(?P<action>.+?))?"
    r"(?:\s{2,}(?P<client_response>\w+ by client))?\s*$"
)
CODE_PATH = re.compile(r"^[\w.-]+/[\w.-]+/[\w./-]+$")
CODE_LINES = re.compile(r"^Line (\d+)(?: to (\d+))? in ([0-9a-f]{7,40})$")
NUMBERED = re.compile(r"^\s*(\d+)(?:\s(.*))?$")
URL_WRAP = re.compile(r"(https?://\S*-)\n\s*(\S)")
IMPACT_WORDS = re.compile(r"\b(can|could|allows?|locked|loss|lose|steal|drain|redirect)\b", re.I)
STEP = re.compile(r"^\d+\.\s+\S")

STATUS_RULES = [
    (re.compile(r"^fixed in\b", re.I), "Resolved"),
    (re.compile(r"\bpartially\b", re.I), "Partially Resolved"),
    (re.compile(r"\b(won't fix|will not fix|risk accepted|accepted the risk)\b", re.I), "Risk Accepted"),
    (re.compile(r"\backnowledged?\b", re.I), "Acknowledged"),
]


# ------------------------------------------------------------------ text extraction


def _clean_lines(text: str) -> list[str]:
    """Drop form feeds and `N/M` page footers; keep layout indentation."""
    return [line.rstrip() for line in text.replace("\f", "\n").split("\n") if not FOOTER.match(line)]


def _repo_hyperlink(path: Path) -> str | None:
    """The Scope page links the repository name; pdftotext loses the URL, the link annotation keeps it."""
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:20]:
            if "fixed commit hash" not in (page.extract_text() or ""):
                continue
            for link in page.hyperlinks:
                uri = link.get("uri") or ""
                parsed = urlparse(uri)
                if parsed.netloc == "github.com" and len([p for p in parsed.path.split("/") if p]) == 2:
                    return uri.rstrip("/")
    return None


def _split_sections(lines: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    """Body headings sit alone at column 0; the table of contents before `Disclaimer` is skipped."""
    found: list[tuple[str, int]] = []
    pos = 0
    for heading in HEADINGS:
        for i in range(pos, len(lines)):
            if lines[i] == heading and (found or heading == "Disclaimer"):
                found.append((heading, i))
                pos = i + 1
                break
    front = lines[: found[0][1]] if found else lines
    sections = {}
    for n, (heading, start) in enumerate(found):
        end = found[n + 1][1] if n + 1 < len(found) else len(lines)
        sections[heading] = lines[start + 1 : end]
    if "Appendix" in sections:
        body = sections["Appendix"]
        stop = next((i for i, line in enumerate(body) if line == "Protocol Summary"), len(body))
        sections["Appendix"] = body[:stop]
    return front, sections


def _split_findings(lines: list[str]) -> list[dict]:
    findings: list[dict] = []
    current = None
    for line in lines:
        header = FINDING_HEADER.match(line)
        if header:
            current = {"source_id": header.group(1), "title_lines": [header.group(2)], "lines": [], "meta": None}
            findings.append(current)
        elif current is not None:
            if current["meta"] is None:
                sev = SEVERITY_LINE.match(line)
                if sev:
                    current["meta"] = sev.groupdict()
                elif line.strip():
                    current["title_lines"].append(line.strip())
            else:
                current["lines"].append(line)

    out = []
    for f in findings:
        blocks: dict[str, list[str]] = {}
        key = None
        for line in f["lines"]:
            if line.strip() in ("Description", "Recommendation", "Status") and not line.startswith(" " * 8):
                key = line.strip().lower()
                blocks[key] = []
            elif key:
                blocks[key].append(line)
        meta = f["meta"] or {}
        out.append(
            {
                "source_id": f["source_id"],
                "title": " ".join(t for t in f["title_lines"] if t).strip(),
                "severity": meta.get("severity"),
                "difficulty": meta.get("difficulty"),
                "recommended_action": (meta.get("action") or "").strip() or None,
                "client_response": meta.get("client_response"),
                "description": "\n".join(blocks.get("description", [])).strip("\n"),
                "recommendation": "\n".join(blocks.get("recommendation", [])).strip("\n"),
                "status": "\n".join(blocks.get("status", [])).strip("\n"),
            }
        )
    return out


# ------------------------------------------------------------------ text -> markdown


def text_to_md(text: str) -> tuple[str, list[dict]]:
    """Layout text -> markdown. Code excerpts become fenced blocks (trimmed); returns their references."""
    lines = text.split("\n")
    out: list[str] = []
    refs: list[dict] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        header = CODE_LINES.match(nxt) if CODE_PATH.match(stripped) else None
        if header:
            start, end = int(header.group(1)), int(header.group(2) or header.group(1))
            code, i = _collect_code(lines, i + 2, start, end)
            path = "/".join(stripped.split("/")[2:])
            repo = "/".join(stripped.split("/")[:2])
            refs.append({"repo": repo, "path": path, "start": start, "end": end, "commit": header.group(3)})
            span = f"line {start}" if start == end else f"lines {start}-{end}"
            lang = "rust" if path.endswith(".rs") else ""
            if len(code) > MAX_CODE_LINES:
                code = code[:MAX_CODE_LINES] + ["// ... trimmed; see the authoritative PDF"]
            out += ["", f"`{path}` {span} (at `{header.group(3)}`):", "", f"```{lang}", *code, "```", ""]
            continue
        out.append(_escape(stripped))
        i += 1
    md = URL_WRAP.sub(r"\1\2", "\n".join(out))
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return md, refs


def _collect_code(lines: list[str], i: int, start: int, end: int) -> tuple[list[str], int]:
    """Numbered source lines in [start, end], across page breaks; unnumbered lines right after one are wraps."""
    code: list[str] = []
    last_was_code = False
    while i < len(lines):
        line = lines[i]
        m = NUMBERED.match(line)
        if m and start <= int(m.group(1)) <= end and (not code or int(m.group(1)) >= _last_no(code)):
            code.append(f"{m.group(1)}\x00{m.group(2) or ''}")
            last_was_code = True
        elif not line.strip():
            last_was_code = False
            ahead = next((x for x in lines[i + 1 :] if x.strip()), "")
            am = NUMBERED.match(ahead)
            in_range = bool(am) and start <= int(am.group(1)) <= end
            if not (in_range and (not code or int(am.group(1)) > _last_no(code))):
                break
        elif last_was_code and code:
            code[-1] += " " + line.strip()
        else:
            break
        i += 1
    body = textwrap.dedent("\n".join(c.split("\x00", 1)[1] for c in code)).split("\n") if code else []
    return [b.rstrip() for b in body], i


def _last_no(code: list[str]) -> int:
    return int(code[-1].split("\x00", 1)[0])


def _escape(line: str) -> str:
    """Keep prose from turning into markdown structure (headings, tables, raw HTML like `Vec<Condition>`)."""
    line = line.replace("<", "\\<")
    if line.startswith(("#", "|")):
        line = "\\" + line
    return line


def _paragraphs(md: str) -> list[str]:
    """Prose paragraphs only (code fences and their captions dropped)."""
    without_code = re.sub(r"`[^`\n]+` lines? [\d-]+ \(at `[0-9a-f]+`\):\n\n```[\s\S]*?```", "", md)
    return [p.strip() for p in re.split(r"\n\s*\n", without_code) if p.strip()]


def _date(text: str) -> str | None:
    text = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", text).replace(",", "")
    try:
        return dt.datetime.strptime(" ".join(text.split()), "%B %d %Y").date().isoformat()
    except ValueError:
        return None


# ------------------------------------------------------------------ converter


class RuntimeVerificationConverter(Converter):
    firm_abbrev = "RV"
    firm_name = "Runtime Verification"

    @classmethod
    def matches(cls, source: str, raw: RawDoc | None = None) -> bool:
        return urlparse(source).netloc.endswith("runtimeverification.com")

    def extract(self, raw: RawDoc) -> dict:
        if raw.kind != "pdf":
            raise ValueError("Runtime Verification converter expects the report PDF")
        lines = _clean_lines(pdf_text(raw.path))
        front, sections = _split_sections(lines)
        if "Findings" not in sections:
            raise ValueError("no Findings section found; the RV report layout may have changed")
        delivered = next((m.group(1) for line in front if (m := re.search(r"Delivered:\s*(.+)$", line))), None)
        title_lines = []
        for line in front:
            if line.strip().startswith("Delivered:"):
                break
            if line.strip():
                title_lines.append(line.strip())
        return {
            "url": raw.url,
            "title_lines": title_lines,
            "delivered": delivered,
            "repo_url": _repo_hyperlink(raw.path),
            "sections": {
                name: "\n".join(body).strip("\n")
                for name, body in sections.items()
                if name not in ("Findings", "Informative Findings")
            },
            "findings": _split_findings(sections.get("Findings", []) + sections.get("Informative Findings", [])),
        }

    def default_slug(self, firm_report: dict) -> str:
        return slugify(_client(firm_report) or "project")

    def normalize(self, fr: dict, project_slug: str | None) -> dict:
        slug = project_slug or self.default_slug(fr)
        report = new_report(self.firm_name)
        notes = report["conversion_notes"]
        meta = report["report"]
        sections = fr.get("sections") or {}
        exec_text = sections.get("Executive Summary", "")
        scope_text = sections.get("Scope", "")
        method_text = sections.get("Methodology", "")

        project = " ".join(t for t in fr.get("title_lines", []) if t.lower() != "security audit report").strip()
        client = _client(fr)
        if not client:
            client = project or slug.replace("-", " ").title()
            notes.append(f"client name '{client}' taken from the report title; confirm")
        meta["client"] = client
        meta["title"] = f"{project or client} -- Security Audit Report"
        report["heading"] = f"{project or client} -- Security Audit by Runtime Verification"
        meta["report_date"] = _date(fr.get("delivered") or "")
        if not meta["report_date"]:
            notes.append("report.report_date not found (no `Delivered:` date); firm to supply")
        began = re.search(r"audit began on\s+([A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})", exec_text)
        meta["engagement_start"] = _date(began.group(1)) if began else None
        weeks = re.search(r"(\d+)-week review", exec_text)
        remediation_weeks = re.search(r"(\d+) weeks? of remediation", exec_text)
        duration = ""
        if weeks:
            duration = f"a {weeks.group(1)}-week review"
            if remediation_weeks:
                duration += f" plus {remediation_weeks.group(1)} week(s) of remediation support"
        notes.append(
            "report.engagement_end not stated in the report"
            + (f" (RV states {duration} starting {meta['engagement_start']})" if duration else "")
            + "; firm to supply"
        )
        if not meta["engagement_start"]:
            notes.append("report.engagement_start not found in the Executive Summary; firm to supply")
        if duration:
            notes.append(f"effort.engineer_weeks left null: the report states {duration} (calendar time), not effort")

        if fr.get("url"):
            meta["pdf_url"] = fr["url"]
        else:
            notes.append("converted from a local PDF: set report.pdf_url to the public PDF link")

        scope = report["scope"]
        platform_from_text(report, f"{exec_text}\n{scope_text}")
        commit_start = re.search(r"fixed commit hash\s+([0-9a-f]{40})", scope_text)
        commit_final = re.search(r"latest reviewed PRs are contained in commit ID\s+([0-9a-f]{40})", scope_text)
        repo_url = fr.get("repo_url")
        code_refs = [r for f in fr["findings"] for r in _code_repo_refs(f.get("description", ""))]
        if not repo_url and code_refs:
            repo_url = f"https://github.com/{code_refs[0]}"
            notes.append(f"repository URL derived from code excerpt paths ({repo_url}); confirm")
        if not commit_start:
            notes.append("audited commit (`fixed commit hash`) not found in Scope; firm to supply")
        scope["repositories"] = [
            {
                "url": repo_url,
                "commit_start": commit_start.group(1) if commit_start else None,
                "commit_final": commit_final.group(1) if commit_final else None,
            }
        ]
        scope["in_scope_paths"] = re.findall(r"^\s*\./(\S+?)\s*:", scope_text, re.M)
        if re.search(r"\brust\b", f"{scope_text}\n{method_text}\n{exec_text}", re.I):
            scope["languages"] = ["rust"]

        lowered = f"{exec_text}\n{method_text}".lower()
        audit_type = []
        if "design review" in lowered:
            audit_type.append("design-review")
        audit_type.append("code-review")
        if "formal verification" in lowered:
            audit_type.append("formal-verification")
        if "remediation" in exec_text.lower() and commit_final:
            audit_type.append("fix-review")
        report["audit"]["type"] = audit_type
        tools = [t for t in KNOWN_TOOLS if re.search(rf"\b{re.escape(t)}\b", method_text)]
        report["audit"]["tooling"] = tools or None

        audited = commit_start.group(1) if commit_start else ""
        audited_repo = "/".join(urlparse(repo_url or "").path.strip("/").split("/")[:2])
        report["findings"] = [
            self._finding(f, n, slug, audited, audited_repo) for n, f in enumerate(fr["findings"], start=1)
        ]

        report["sections"] = self._sections(sections, notes)
        return report

    def _sections(self, sections: dict, notes: list[str]) -> dict:
        out = {
            k: None
            for k in (
                "executive_summary",
                "project_context",
                "assumptions_limitations",
                "methodology",
                "disclaimer",
                "appendix",
            )
        }
        out["executive_summary"] = text_to_md(sections.get("Executive Summary", ""))[0] or None
        notes.append("Section 1 is RV's Executive Summary verbatim; trim toward ~250 words if desired")

        components = []
        for item in re.split(r"\n(?=\s*\./)", sections.get("Scope", "")):
            m = re.match(r"\s*\./(\S+?)\s*:\s*([\s\S]*)", item)
            if m:
                body = " ".join(m.group(2).split()).split(" As findings are identified")[0]
                components.append(f"- `{m.group(1)}`: {body}")
        out["project_context"] = "\n".join(components) or None
        notes.append(
            "Section 2 built from RV's Scope component descriptions; roles and business logic are in the PDF; "
            "the key contracts table is not filled"
        )
        out["assumptions_limitations"] = _invariants_md(sections.get("Invariants", "")) or None
        notes.append("Section 5 is RV's Invariants section, including T. Trust assumptions")
        out["methodology"] = text_to_md(sections.get("Methodology", ""))[0] or None
        disclaimer = text_to_md(sections.get("Disclaimer", ""))[0] or None
        out["disclaimer"], note = disclaimer_with_default(self.firm_name, disclaimer)
        if note:
            notes.append(note)
        appendix = text_to_md(sections.get("Appendix", ""))[0]
        if appendix:
            out["appendix"] = (
                appendix + "\n\nThe Protocol Summary itself is not reproduced here; see the authoritative PDF."
            )
            notes.append("Section 8 keeps RV's Appendix introduction only; the Protocol Summary stays in the PDF")
        return out

    def _finding(self, f: dict, n: int, slug: str, audited_commit: str, audited_repo: str) -> dict:
        out = new_finding()
        notes = out["conversion_notes"]
        out["id"] = f"{project_code(slug)}-RV-{n:03d}"
        out["title"] = f["title"]

        severity = f.get("severity") or ""
        out["unified_severity"] = unified_from_label(severity)
        if out["unified_severity"]:
            notes.append(severity_note(severity, out["unified_severity"]))
        else:
            notes.append(f"RV severity {severity!r} has no unified mapping; firm to assign")
        parts = []
        if f.get("difficulty"):
            parts.append(f"Difficulty: {f['difficulty']}")
        if f.get("recommended_action"):
            parts.append(f"Recommended Action: {f['recommended_action']}")
        rating = f"{severity} ({'; '.join(parts)})" if parts else severity
        out["firm_severity_rating"] = f"{rating} (source: {f['source_id']})"
        out["difficulty_likelihood"] = f"Difficulty: {f['difficulty']}" if f.get("difficulty") else None

        description, refs = text_to_md(f.get("description", ""))
        out["description"] = description or None
        paragraphs = _paragraphs(description)
        impact = [p for p in paragraphs if IMPACT_WORDS.search(p)]
        if impact:
            out["impact"] = impact[-1]
            notes.append("Impact is the Description paragraph that states consequences; firm to confirm or rewrite")
        else:
            out["impact"] = paragraphs[0] if paragraphs else None
            notes.append("no impact statement found: Impact repeats the first Description paragraph; firm to rewrite")
        steps = [p for p in paragraphs if sum(bool(STEP.match(line)) for line in p.split("\n")) >= 2]
        out["proof"] = "\n\n".join(steps) or None

        recommendation, rec_refs = text_to_md(f.get("recommendation", ""))
        out["recommendation"] = recommendation or None
        status_md, status_refs = text_to_md(f.get("status", ""))
        out["remediation_notes"] = status_md or None

        out["status"] = "Unresolved"
        for pattern, status in STATUS_RULES:
            if pattern.search(status_md or ""):
                out["status"] = status
                break
        else:
            notes.append(f"RV status text not recognized ({(status_md or '')[:60]!r}); mapped to Unresolved")
        fixed_in = bool(re.match(r"fixed in\b", status_md or "", re.I))
        out["remediation_verified_by"] = "firm" if fixed_in else "not-reviewed"
        head = re.search(r"head at (https?://\S+?)\)", status_md or "")
        pull = re.search(r"https?://\S+?/pull/\d+", status_md or "")
        out["resolved_in"] = head.group(1) if head else (pull.group(0) if pull else None)
        if out["resolved_in"] and not fixed_in:
            notes.append(f"remediation PR/commit present on a {out['status']} finding; confirm status")

        out["category"] = infer_category(out["title"], description, out["unified_severity"])
        notes.append(f"category inferred: {out['category']}")

        located = refs or rec_refs or status_refs
        if located and not refs:
            notes.append("location taken from code excerpts outside the Description; confirm")
        external = sorted({r["repo"] for r in located if audited_repo and r["repo"] != audited_repo})
        if external and any(r["repo"] == audited_repo for r in located):
            located = [r for r in located if r["repo"] == audited_repo]
            notes.append(f"code excerpts from {', '.join(external)} (outside the audited repo) left out of Location")
        elif external:
            notes.append(f"location points outside the audited repository ({', '.join(external)}); confirm")
        locations = []
        for r in located:
            loc = r["path"] + (f":L{r['start']}" if r["start"] == r["end"] else f":L{r['start']}-L{r['end']}")
            if loc not in locations:
                locations.append(loc)
        out["location"] = ", ".join(locations[:5]) or None
        other_commits = sorted({r["commit"] for r in located if not audited_commit.startswith(r["commit"])})
        if other_commits:
            notes.append(f"line numbers refer to commit(s) {', '.join(other_commits)}, not the audited commit; confirm")
        return out


def _client(fr: dict) -> str | None:
    exec_text = (fr.get("sections") or {}).get("Executive Summary", "")
    m = re.search(r"^\s*(\S.*?)\s+engaged Runtime Verification", exec_text, re.M)
    return m.group(1).strip() if m else None


def _code_repo_refs(text: str) -> list[str]:
    """`org/repo` of every code excerpt path in the text."""
    lines = [line.strip() for line in text.split("\n")]
    return [
        "/".join(line.split("/")[:2])
        for line, nxt in zip(lines, lines[1:] + [""], strict=True)
        if CODE_PATH.match(line) and CODE_LINES.match(nxt)
    ]


def _invariants_md(text: str) -> str:
    """Group headings (`A. Value conservation`) -> H4; each `I1 —` / `T1 —` item -> a bullet."""
    out: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if re.match(r"^[A-Z]\. \S", stripped) and len(stripped) < 90 and not stripped.endswith("."):
            out += ["", f"#### {_escape(stripped)}", ""]
        elif re.match(r"^[IT]\d+\s+—", stripped):
            out.append(f"- {_escape(stripped)}")
        elif stripped and out and out[-1].startswith(("- ", "  ")):
            out.append(f"  {_escape(stripped)}")
        else:
            out.append(_escape(stripped))
    md = URL_WRAP.sub(r"\1\2", "\n".join(out))
    return re.sub(r"\n{3,}", "\n\n", md).strip()
