"""Halborn report pages (halborn.com/audits/...): a Next.js app with the findings in the RSC payload.

The page streams `self.__next_f.push([1, "..."])` chunks. Concatenated, they form RSC rows
`<hex id>:<json>\\n` or `<hex id>:T<hex byte length>,<text>`; string fields like `"$57"` point at row 57.
"""

import json
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .base import (
    Converter,
    RawDoc,
    disclaimer_with_default,
    html_to_md,
    infer_category,
    new_finding,
    new_report,
    platform_from_text,
    project_code,
    severity_note,
    slugify,
    unified_from_label,
)

STATUS = {
    "Solved": "Resolved",
    "Risk Accepted": "Risk Accepted",
    "Acknowledged": "Acknowledged",
    "Partially Solved": "Partially Resolved",
}
FINDING_FIELDS = [
    "halIndex",
    "title",
    "description",
    "poc",
    "remediation",
    "remediationComment",
    "remediationHash",
    "remediationState",
    "remediationDate",
    "bvss_score",
    "bvss_vector",
    "bvss_grade",
    "cvss_score",
    "cvss_grade",
]
SHA = re.compile(r"\b[0-9a-f]{40}\b")
RS_MENTION = re.compile(r"\b([\w./-]+\.rs)(?::(\d+)(?:\s*[–-]\s*(\d+))?)?")
CAMEL = re.compile(r"\b([A-Z][A-Za-z0-9]+)\b")
IMPACT_HEADING = re.compile(r"(?im)^(?:#{1,6}\s*impact\s*:?\s*|\*\*impact\*\*\s*:?\s*)$")


def _rsc_rows(stream: str) -> dict[str, str]:
    data = stream.encode()
    rows: dict[str, str] = {}
    row = re.compile(rb"([0-9a-f]+):")
    i = 0
    while i < len(data):
        m = row.match(data, i)
        if not m:
            nl = data.find(b"\n", i)
            i = len(data) if nl < 0 else nl + 1
            continue
        rid, j = m.group(1).decode(), m.end()
        if data[j : j + 1] == b"T":
            comma = data.index(b",", j)
            n = int(data[j + 1 : comma], 16)
            rows[rid] = data[comma + 1 : comma + 1 + n].decode(errors="replace")
            i = comma + 1 + n
        else:
            nl = data.find(b"\n", j)
            nl = len(data) if nl < 0 else nl
            rows[rid] = data[j:nl].decode(errors="replace")
            i = nl + 1
    return rows


def _key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


class HalbornConverter(Converter):
    firm_abbrev = "HAL"
    firm_name = "Halborn"

    @classmethod
    def matches(cls, source: str, raw: RawDoc | None = None) -> bool:
        parsed = urlparse(source)
        return parsed.netloc.endswith("halborn.com") and parsed.path.startswith("/audits/")

    # ---------------------------------------------------------------- extract

    def extract(self, raw: RawDoc) -> dict:
        html = raw.path.read_text(encoding="utf-8", errors="replace")
        chunks = re.findall(r"self\.__next_f\.push\((\[.*?\])\)</script>", html, re.S)
        stream = "".join(arr[1] for arr in map(json.loads, chunks) if len(arr) > 1 and isinstance(arr[1], str))
        start = stream.find('"realAudit":')
        if start < 0:
            raise ValueError("Halborn page has no realAudit payload; the page format may have changed")
        audit, _ = json.JSONDecoder().raw_decode(stream, start + len('"realAudit":'))
        rows = _rsc_rows(stream)

        def resolve(value):
            if isinstance(value, str) and re.fullmatch(r"\$[0-9a-f]+", value):
                return rows.get(value[1:])
            return None if value == "$undefined" else value

        sections = {
            s.get("name"): resolve((s.get("customFields") or [{}])[0].get("text")) for s in audit.get("sections") or []
        }
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        disclaimer = soup.find(id="disclaimer")
        disclaimer_text = None
        if disclaimer:
            disclaimer_text = re.sub(r"^\s*Disclaimer\s*#?\s*", "", disclaimer.get_text(" ", strip=True)).strip()
        text = soup.get_text("\n", strip=True)
        commits: list[str] = []
        marker = text.find("Remediation Commit ID")
        if marker >= 0:
            for line in text[marker:].split("\n")[1:]:
                if not SHA.fullmatch(line.strip()):
                    break
                commits.append(line.strip())

        return {
            "url": raw.url or raw.source,
            "client": (audit.get("company") or {}).get("name"),
            "name": audit.get("name"),
            "date_start": audit.get("date_start"),
            "date_end": audit.get("date_end"),
            "updated_at": audit.get("updatedAt"),
            "is_pdf_ready": '"isPdfReady":true' in stream,
            "introduction_html": sections.get("Introduction"),
            "assessment_summary_html": sections.get("Assessment Summary"),
            "methodology_html": sections.get("Test Approach and Methodology"),
            "disclaimer_text": disclaimer_text,
            "sources": [
                {
                    "repositoryUrl": s.get("repositoryUrl") or s.get("repo"),
                    "commitHash": s.get("commitHash") or s.get("hash"),
                    "scopeFiles": s.get("scopeFiles") or [],
                    "outOfScopeFiles": s.get("outOfScopeFiles") or [],
                    "outOfScopeExtra": s.get("outOfScopeExtra") or [],
                }
                for s in audit.get("sources") or []
            ],
            "remediation_commits": commits,
            "findings": [{k: resolve(f.get(k)) for k in FINDING_FIELDS} for f in audit.get("findings") or []],
        }

    # -------------------------------------------------------------- normalize

    def default_slug(self, firm_report: dict) -> str:
        path = urlparse(firm_report.get("url") or "").path.split("/")
        return path[2] if len(path) > 2 and path[1] == "audits" else slugify(firm_report.get("client") or "")

    def normalize(self, fr: dict, project_slug: str | None) -> dict:
        slug = project_slug or self.default_slug(fr)
        report = new_report(self.firm_name)
        notes = report["conversion_notes"]
        meta = report["report"]

        client = fr.get("client")
        if not client:
            client = slug.replace("-", " ").title()
            notes.append(f"client name '{client}' derived from the URL; confirm")
        meta["client"] = client
        meta["title"] = f"{client}: {fr.get('name') or 'Security Assessment'}"
        meta["firm_report_url"] = fr.get("url")
        meta["engagement_start"] = (fr.get("date_start") or "")[:10] or None
        meta["engagement_end"] = (fr.get("date_end") or "")[:10] or None
        if not meta["engagement_start"]:
            notes.append("engagement dates not found on the page")
        dates = sorted(f["remediationDate"][:10] for f in fr["findings"] if f.get("remediationDate"))
        if dates:
            meta["report_date"] = dates[-1]
            notes.append(
                f"report.report_date taken from the latest finding remediationDate ({dates[-1]}); "
                f"page last updated {(fr.get('updated_at') or '?')[:10]}; firm to confirm the publication date"
            )
        elif fr.get("updated_at"):
            meta["report_date"] = fr["updated_at"][:10]
            notes.append("report.report_date taken from the page's last-updated date; firm to confirm")
        else:
            notes.append("report.report_date not found; firm to supply")
        if fr.get("is_pdf_ready"):
            notes.append("the page offers a PDF download; add its URL as report.pdf_url if it is public")
        report["heading"] = f"{client}: {fr.get('name') or 'Security Assessment'} by Halborn"

        scope = report["scope"]
        intro_md = html_to_md(fr.get("introduction_html")) or ""
        platform_from_text(report, intro_md)
        commits = fr.get("remediation_commits") or []
        for i, src in enumerate(fr["sources"]):
            commit_final = commits[-1] if commits and i == len(fr["sources"]) - 1 else None
            scope["repositories"].append(
                {"url": src["repositoryUrl"], "commit_start": src["commitHash"], "commit_final": commit_final}
            )
        if commits:
            notes.append(
                f"scope.repositories[].commit_final is the last of {len(commits)} listed remediation commits; "
                "Halborn to confirm it is the final reviewed commit"
            )
        scope_files = [p for s in fr["sources"] for p in s["scopeFiles"]]
        scope["in_scope_paths"] = scope_files
        scope["out_of_scope"] = [p for s in fr["sources"] for p in s["outOfScopeFiles"] + s["outOfScopeExtra"]]
        scope["languages"] = ["rust"] if any(p.endswith(".rs") for p in scope_files) else []

        findings = [self._finding(f, slug, scope_files) for f in fr["findings"]]
        report["findings"] = findings
        if any(f["remediation_verified_by"] == "firm" for f in findings):
            report["audit"]["type"] = ["code-review", "fix-review"]

        sections = report["sections"]
        sections["executive_summary"] = html_to_md(fr.get("assessment_summary_html"))
        notes.append("Section 1 is Halborn's Assessment Summary verbatim; trim toward ~250 words if desired")
        sections["project_context"] = intro_md or None
        notes.append("Section 2 is Halborn's Introduction; the key contracts table is not in the source")
        extra = [x for s in fr["sources"] for x in s["outOfScopeExtra"]]
        sections["assumptions_limitations"] = (
            "\n".join(f"- Out of scope: {x}" for x in extra) if extra else "No assumptions stated in the source."
        )
        notes.append("Section 5 built from Halborn's out-of-scope notes; Halborn has no assumptions section")
        sections["methodology"] = html_to_md(fr.get("methodology_html"))
        sections["disclaimer"], note = disclaimer_with_default(self.firm_name, fr.get("disclaimer_text"))
        if note:
            notes.append(note)
        return report

    def _finding(self, f: dict, slug: str, scope_files: list[str]) -> dict:
        out = new_finding()
        notes = out["conversion_notes"]
        source_id = f"HAL-{f['halIndex']:02d}"
        out["id"] = f"{project_code(slug)}-HAL-{f['halIndex']:03d}"
        out["title"] = (f.get("title") or "").strip()

        grade = (f.get("bvss_grade") or [None])[0]
        out["unified_severity"] = unified_from_label(grade)
        rating = f"{grade}, BVSS 2.0 {f.get('bvss_score')} ({f.get('bvss_vector')})"
        out["firm_severity_rating"] = f"{rating} (source: {source_id})"
        if out["unified_severity"]:
            notes.append(severity_note(grade, out["unified_severity"]))
        else:
            notes.append(f"BVSS grade {grade!r} has no unified mapping; firm to assign")

        state = f.get("remediationState")
        out["status"] = STATUS.get(state, "Unresolved")
        if state not in STATUS:
            notes.append(f"Halborn remediation state {state!r} mapped to Unresolved; confirm")
        if state == "Solved" and out_hash(f):
            out["remediation_verified_by"] = "firm"
        elif state == "Solved":
            out["status"], out["remediation_verified_by"] = "Fixed - Not Verified", "client-reported"
            notes.append("Solved without a remediation commit: recorded as Fixed - Not Verified; confirm")
        else:
            out["remediation_verified_by"] = "not-reviewed"
        out["resolved_in"] = f.get("remediationHash") or None
        if out["resolved_in"] and state != "Solved":
            notes.append(f"remediation commit present on a {state} finding; consider Partially Resolved")

        description_html, excerpts = _strip_code_headers(f.get("description") or "")
        description = html_to_md(description_html) or ""
        parts = IMPACT_HEADING.split(description, maxsplit=1)
        if len(parts) == 2:
            out["description"], out["impact"] = parts[0].strip(), parts[1].strip()
        else:
            out["description"] = description
            first = re.split(r"(?<=[.!?])\s", description.strip(), maxsplit=1)[0]
            out["impact"] = first or None
            notes.append("no Impact heading in the source: Impact repeats the first sentence; firm to rewrite")

        out["proof"] = html_to_md(_strip_code_headers(f.get("poc") or "")[0])
        out["recommendation"] = html_to_md(_strip_code_headers(f.get("remediation") or "")[0])
        comment = html_to_md(f.get("remediationComment"))
        if comment and f.get("remediationDate"):
            comment += f"\n\nHalborn remediation date: {f['remediationDate'][:10]}."
        out["remediation_notes"] = comment

        out["category"] = infer_category(out["title"], description, out["unified_severity"])
        notes.append(f"category inferred: {out['category']}")

        location, inferred = _locations(out["title"], description, excerpts, scope_files)
        out["location"] = location
        if location and inferred:
            notes.append("location inferred from contract names and code excerpt line ranges; confirm")
        return out


def out_hash(f: dict) -> str | None:
    return f.get("remediationHash") or None


def _strip_code_headers(html: str) -> tuple[str, list[tuple[str, str]]]:
    """Remove Halborn's code-block header chrome ("RUST 2906-2907 Copy") and keep (caption, line range)."""
    soup = BeautifulSoup(html, "html.parser")
    excerpts = []
    for wrapper in soup.select("div.code-block-wrapper"):
        rng = wrapper.select_one(".code-block-line-range")
        caption_el = wrapper.find_previous_sibling(["p", "h3", "h4"])
        if rng:
            excerpts.append((caption_el.get_text(" ", strip=True) if caption_el else "", rng.get_text(strip=True)))
        header = wrapper.select_one(".code-block-header")
        if header:
            header.decompose()
    return str(soup), excerpts


def _locations(title: str, text: str, excerpts, scope_files: list[str]) -> tuple[str | None, bool]:
    """Resolve `path:Lx-Ly` locations from explicit .rs mentions, then code excerpts, then contract names."""
    main_file = {}
    for path in scope_files:
        parts = path.split("/")
        if len(parts) >= 2 and _key(parts[-1].removesuffix(".rs")) == _key(parts[1]):
            main_file[_key(parts[1])] = path

    def contracts_in(s: str) -> list[str]:
        return [main_file[_key(n)] for n in CAMEL.findall(s or "") if _key(n) in main_file]

    hints = contracts_in(title) + contracts_in(text)
    found: list[str] = []
    inferred = False

    def add(loc: str):
        path = loc.split(":")[0]
        if loc in found or (":" not in loc and any(f.split(":")[0] == path for f in found)):
            return
        if ":" in loc and path in found:
            found.remove(path)
        found.append(loc)

    for name, start, end in RS_MENTION.findall(text):
        candidates = [p for p in scope_files if p.endswith("/" + name) or p == name]
        if len(candidates) > 1:
            dirs = {"/".join(h.split("/")[:2]) for h in hints}
            narrowed = [c for c in candidates if "/".join(c.split("/")[:2]) in dirs]
            candidates = narrowed[:1] if narrowed else []
            inferred = True
        if len(candidates) != 1:
            continue
        lines = f":L{start}" + (f"-L{end}" if end else "") if start else ""
        add(candidates[0] + lines)

    for caption, rng in excerpts:
        files = contracts_in(caption) or hints[:1]
        m = re.fullmatch(r"(\d+)(?:\s*[–-]\s*(\d+))?", rng.strip())
        if files and m:
            inferred = True
            add(f"{files[0]}:L{m.group(1)}" + (f"-L{m.group(2)}" if m.group(2) and m.group(2) != m.group(1) else ""))

    if not found and hints:
        inferred = True
        add(hints[0])
    return (", ".join(found[:5]) or None), inferred
