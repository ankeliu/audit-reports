"""Issue-form submission -> converted/validated report + issue comment + PR body.

Run by .github/workflows/submission.yml:

    python -m auditbank.submission --issue-number N --workdir DIR --github-output $GITHUB_OUTPUT

The issue body is read from the ISSUE_BODY environment variable (never interpolated into shell).
Everything in it, and anything it links to, is untrusted data: it is downloaded and parsed, never executed.
"""

import argparse
import os
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

import requests

from .ai import log_markdown
from .convert import convert
from .converters import CONVERTERS
from .converters.base import USER_AGENT
from .detect import DetectionError, is_standard_md
from .parse import ParseError, parse_file
from .paths import REPO_ROOT, REPORTS_DIR, firm_abbrev, vocab
from .validate import ERROR, has_errors, validate_file

FIELDS = {
    "Audit firm": "firm",
    "Published report URL": "source_url",
    "Attachment": "attachment",
    "Project slug": "project_slug",
    "Client approval": "client_approval",
    "Notes": "notes",
}
NO_RESPONSE = "_No response_"
ATTACHMENT_URL = re.compile(
    r"https://github\.com/(?:user-attachments/(?:assets|files)/|[\w.-]+/[\w.-]+/files/)[^\s)\]]+"
)
MAX_BYTES = 50 * 1024 * 1024


class SubmissionError(ValueError):
    pass


def firm_reviewers(abbrev: str) -> list[str]:
    """GitHub handles listed for the firm in .github/firm-reviewers.yml (the base branch's copy in CI)."""
    from .ci import reviewers

    return reviewers().get(abbrev, [])


def parse_issue_form(body: str) -> dict:
    """GitHub renders issue forms as `### <label>` blocks."""
    out = {}
    for match in re.finditer(r"^### (.+?)\s*\n([\s\S]*?)(?=^### |\Z)", body or "", re.M):
        key = FIELDS.get(match.group(1).strip())
        if key:
            value = match.group(2).strip()
            out[key] = None if value == NO_RESPONSE else value
    return out


def check_form(form: dict) -> dict:
    firms = vocab()["firms"]
    m = re.search(r"\(([A-Z]+)\)\s*$", form.get("firm") or "")
    if not m or m.group(1) not in firms:
        raise SubmissionError(f"unknown audit firm {form.get('firm')!r}")
    # Optional: when blank, the converter derives it from the report (Halborn URL, or the client name).
    slug = (form.get("project_slug") or "").strip().strip("`") or None
    if slug and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        raise SubmissionError(f"project slug {slug!r} must be lowercase words joined by hyphens, e.g. `trustless-work`")
    if not re.search(r"- \[[xX]\]", form.get("client_approval") or ""):
        raise SubmissionError("the client-approval checkbox must be ticked")
    source = (form.get("source_url") or "").strip() or None
    attachment = ATTACHMENT_URL.search(form.get("attachment") or "")
    if source and urlparse(source).scheme != "https":
        raise SubmissionError("the report URL must be an https:// link")
    if not source and not attachment:
        named = re.search(r"[\w.()\[\]-]+\.(?:pdf|md)\b", form.get("attachment") or "", re.I)
        if named:
            raise SubmissionError(
                f"{named.group(0)} wasn't attached: the Attachment box only has text. "
                "Drag the file into that box and wait for its link to appear before saving."
            )
        raise SubmissionError("Add the published report's link, or attach its PDF or standard .md file.")
    return {
        "abbrev": m.group(1),
        "firm": firms[m.group(1)],
        "slug": slug,
        "source": source,
        "attachment": attachment.group(0) if attachment else None,
        "attachment_name": _attachment_name(form.get("attachment") or "", attachment.group(0) if attachment else ""),
    }


def _attachment_name(text: str, url: str) -> str:
    m = re.search(r"\[([^\]]+)\]\(" + re.escape(url), text) if url else None
    return m.group(1) if m else Path(urlparse(url).path).name


def download(url: str, dest_dir: Path, name_hint: str = "") -> Path:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60, stream=True, allow_redirects=True)
    resp.raise_for_status()
    data = b""
    for chunk in resp.iter_content(1 << 16):
        data += chunk
        if len(data) > MAX_BYTES:
            raise SubmissionError(f"attachment exceeds {MAX_BYTES // (1024 * 1024)} MB")
    if data.startswith(b"%PDF"):
        suffix = ".pdf"
    elif is_standard_md(data[:4096].decode("utf-8", errors="replace")):
        suffix = ".md"
    else:
        suffix = Path(name_hint).suffix.lower() if Path(name_hint).suffix.lower() in (".pdf", ".md") else ".html"
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"submission{suffix}"
    path.write_bytes(data)
    return path


def place_standard_md(path: Path, info: dict) -> Path:
    try:
        report = parse_file(path)
    except ParseError as exc:
        raise SubmissionError(f"could not parse the .md: {exc}") from exc
    date = (report.get("report") or {}).get("report_date") or "unknown-date"
    slug = info["slug"] or re.sub(
        r"[^a-z0-9]+", "-", str((report.get("report") or {}).get("client") or "").lower()
    ).strip("-")
    if not slug:
        raise SubmissionError("could not derive a project slug: fill in report.client or the Project slug field")
    out = REPORTS_DIR / slug / f"{slug}--{info['abbrev'].lower()}--{date}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, out)
    return out


def run(body: str, workdir: Path, use_ai: bool = False) -> dict:
    """Returns {ok, report_path, problems, info, error, conversion_method}."""
    result: dict = {"ok": False, "report_path": None, "problems": [], "info": None, "error": None, "ai_log": []}
    try:
        info = check_form(parse_issue_form(body))
        result["info"] = info
        if info["attachment"]:
            source = str(download(info["attachment"], workdir, info["attachment_name"]))
        else:
            source = info["source"]
            if source.lower().split("?")[0].endswith(".md"):
                source = str(download(source, workdir, "report.md"))
        if source.endswith(".md"):
            out = place_standard_md(Path(source), info)
        else:
            key = info["abbrev"].lower()
            if key not in CONVERTERS:
                raise SubmissionError(
                    f"no converter for {info['firm']} yet: submit a standard .md (see AUDIT_REPORT_TEMPLATE.md)"
                )
            out = convert(source, firm=key, project_slug=info["slug"], use_ai=use_ai, ai_log=result["ai_log"])
    except (SubmissionError, DetectionError, requests.RequestException, ValueError) as exc:
        result["error"] = str(exc)
        return result

    report = parse_file(out)
    if (report.get("report") or {}).get("audit_firm") != info["firm"]:
        result["error"] = (
            f"report.audit_firm is {report['report'].get('audit_firm')!r} but the form says {info['firm']}"
        )
    result["report_path"] = out
    result["conversion_method"] = (report.get("publication") or {}).get("conversion_method")
    result["problems"] = validate_file(out)
    result["ok"] = not result["error"] and not has_errors(result["problems"])
    result["notes"] = list(report.get("conversion_notes") or []) + [
        f"{f.get('id')}: {n}" for f in report.get("findings") or [] for n in f.get("conversion_notes") or []
    ]
    return result


def comment(result: dict, run_url: str | None = None) -> str:
    lines = []
    if result["error"]:
        lines += [
            "### Submission could not be processed",
            "",
            f"**{result['error']}**",
            "",
            "Edit this issue to fix it. The check runs again automatically when you save.",
            "",
        ]
    else:
        errors = sum(p["level"] == ERROR for p in result["problems"])
        warnings = len(result["problems"]) - errors
        verdict = "passed" if result["ok"] else "failed"
        rel = result["report_path"].relative_to(REPO_ROOT).as_posix()
        lines += [f"### Validation {verdict}: {errors} error(s), {warnings} warning(s)", "", f"File: `{rel}`", ""]
        if result["problems"]:
            lines += ["| Level | Code | Path | Message |", "|---|---|---|---|"]
            for p in result["problems"]:
                msg = p["message"].replace("|", "\\|")
                lines.append(f"| {p['level']} | `{p['code']}` | `{p['path']}` | {msg} |")
            lines.append("")
        notes = result.get("notes") or []
        if notes:
            lines += [
                f"<details><summary>{len(notes)} CONVERSION-NOTE(s) for the firm reviewer</summary>",
                "",
                *[f"- {n}" for n in notes[:100]],
                *([f"- ... and {len(notes) - 100} more (see the file)"] if len(notes) > 100 else []),
                "",
                "</details>",
                "",
            ]
        if result["ok"]:
            lines.append("A PR with this file is being opened. A firm engineer reviews it and resolves the notes.")
        else:
            lines.append("Fix the errors (edit the issue or upload a corrected file), then comment `/rerun`.")
    if run_url:
        lines += ["", f"[Workflow run]({run_url})"]
    return "\n".join(lines) + "\n"


def pr_body(result: dict, issue_number: int) -> str:
    info = result["info"]
    template = (REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text()
    rel = result["report_path"].relative_to(REPO_ROOT).as_posix()
    report = parse_file(result["report_path"])
    source = (report.get("report") or {}).get("pdf_url") or (report.get("report") or {}).get("firm_report_url")
    ai = result.get("conversion_method") is None
    template = template.replace("`reports/<slug>/<slug>--<firm>--<YYYY-MM-DD>.md`", f"`{rel}`")
    template = template.replace("**Authoritative report (PDF / firm page):**", f"**Authoritative report:** {source}")
    template = template.replace(
        "**Conversion method:** firm-native / AI-converted (needs firm sign-off)",
        "**Conversion method:** "
        + ("converted by the repo tooling; needs firm sign-off" if ai else result["conversion_method"]),
    )
    listed = firm_reviewers(info["abbrev"])
    reviewers = ", ".join(f"@{h}" for h in listed) if listed else "none listed yet in `.github/firm-reviewers.yml`"
    head = f"Closes #{issue_number}\n\nSubmitted via the issue form. {info['firm']} reviewers: {reviewers}.\n\n"
    return head + template + ("\n" + log_markdown(result["ai_log"]) if result.get("ai_log") else "")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue-number", type=int, required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--github-output")
    ap.add_argument("--run-url")
    ap.add_argument("--ai", action="store_true")
    args = ap.parse_args(argv)

    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    result = run(os.environ.get("ISSUE_BODY", ""), workdir / "download", use_ai=args.ai)
    (workdir / "comment.md").write_text(comment(result, args.run_url))

    outputs = {"ok": str(result["ok"]).lower()}
    if result["report_path"]:
        info = result["info"]
        report = parse_file(result["report_path"])
        date = (report.get("report") or {}).get("report_date")
        outputs.update(
            report_path=result["report_path"].relative_to(REPO_ROOT).as_posix(),
            branch=f"submit/{result['report_path'].parent.name}-{info['abbrev'].lower()}-{date}",
            title=f"Add {report['report'].get('client')} report by {info['firm']} ({date})",
            reviewer=",".join(firm_reviewers(info["abbrev"])),
            needs_firm_review=str(result.get("conversion_method") is None).lower(),
            firm=firm_abbrev(info["firm"]) or "",
        )
        if result["ok"]:
            (workdir / "pr-body.md").write_text(pr_body(result, args.issue_number))
    if args.github_output:
        with open(args.github_output, "a") as fh:
            for k, v in outputs.items():
                fh.write(f"{k}={v}\n")
    print((workdir / "comment.md").read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
