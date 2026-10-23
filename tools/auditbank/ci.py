"""CI-only checks used by .github/workflows/validate.yml.

python -m auditbank.ci gate    --labels "a,b" FILES...          # CONVERSION-NOTEs block merge without `firm-reviewed`
python -m auditbank.ci signoff --reviews reviews.json FILES...  # AI_CONVERSION_SIGNOFF
python -m auditbank.ci stamp   --sender LOGIN FILES...          # set conversion_method after a listed reviewer labels
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from .parse import parse_file
from .paths import REPO_ROOT, firm_abbrev

REVIEWERS_PATH = REPO_ROOT / ".github" / "firm-reviewers.yml"
FIRM_REVIEWED = "firm-reviewed"
NOTE = re.compile(r"[ \t]*<!--\s*CONVERSION-NOTE:[\s\S]*?-->[ \t]*\n?(?:[ \t]*\n)?")
CONVERSION_METHOD = re.compile(r"^(\s*conversion_method:).*$", re.M)


def reviewers() -> dict[str, list[str]]:
    data = yaml.safe_load(REVIEWERS_PATH.read_text()) or {}
    return {k: [h.lstrip("@").lower() for h in (v or [])] for k, v in data.items()}


def _firm(path: Path) -> str | None:
    return firm_abbrev((parse_file(path).get("report") or {}).get("audit_firm"))


def _notes(path: Path) -> int:
    report = parse_file(path)
    return len(report.get("conversion_notes") or []) + sum(
        len(f.get("conversion_notes") or []) for f in report.get("findings") or []
    )


def gate(files: list[Path], labels: set[str], labeler: str | None = None) -> list[str]:
    """CONVERSION-NOTEs block merge unless `firm-reviewed` was applied by a reviewer listed for each file's firm."""
    allowed = reviewers()
    if FIRM_REVIEWED in labels and labeler and all(labeler.lower() in allowed.get(_firm(p), []) for p in files):
        return []
    return [
        f"{p}: {n} CONVERSION-NOTE(s) remain; resolve them or have a listed firm reviewer add the "
        f"`{FIRM_REVIEWED}` label"
        for p in files
        if (n := _notes(p))
    ]


def signoff(files: list[Path], reviews: list[dict]) -> list[str]:
    """AI-converted reports need an APPROVED review from a handle listed for that firm."""
    allowed = reviewers()
    latest: dict[str, str] = {}
    for r in sorted(reviews, key=lambda r: r.get("submitted_at") or ""):
        login = ((r.get("user") or {}).get("login") or "").lower()
        if r.get("state") in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            latest[login] = r["state"]
    problems = []
    for p in files:
        report = parse_file(p)
        if (report.get("publication") or {}).get("conversion_method") != "ai-converted-firm-reviewed":
            continue
        firm = _firm(p)
        approvers = [u for u, state in latest.items() if state == "APPROVED" and u in allowed.get(firm, [])]
        if not approvers:
            listed = ", ".join(allowed.get(firm, [])) or "none yet: add handles to .github/firm-reviewers.yml"
            problems.append(f"{p}: AI_CONVERSION_SIGNOFF needs an approving review from a {firm} reviewer ({listed})")
    return problems


def stamp(files: list[Path], sender: str, method: str = "ai-converted-firm-reviewed") -> list[str]:
    """Set conversion_method and drop resolved CONVERSION-NOTEs, if `sender` may sign off for each file's firm."""
    allowed = reviewers()
    problems = []
    for p in files:
        firm = _firm(p)
        if sender.lower() not in allowed.get(firm, []):
            problems.append(f"{p}: @{sender} is not listed for {firm} in .github/firm-reviewers.yml")
            continue
        text = p.read_text(encoding="utf-8")
        current = (parse_file(p).get("publication") or {}).get("conversion_method")
        text = CONVERSION_METHOD.sub(rf"\g<1> {current or method}", text, count=1)
        text = NOTE.sub("", text)
        p.write_text(text, encoding="utf-8")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m auditbank.ci")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gate")
    g.add_argument("--labels", default="")
    g.add_argument("--labeler", help="login that most recently applied the firm-reviewed label")
    g.add_argument("files", nargs="*")
    s = sub.add_parser("signoff")
    s.add_argument("--reviews", required=True, help="JSON from GET /repos/{o}/{r}/pulls/{n}/reviews")
    s.add_argument("files", nargs="*")
    t = sub.add_parser("stamp")
    t.add_argument("--sender", required=True)
    t.add_argument("files", nargs="*")
    args = ap.parse_args(argv)

    files = [Path(f) for f in args.files]
    if args.cmd == "gate":
        problems = gate(files, {x.strip() for x in args.labels.split(",") if x.strip()}, args.labeler)
    elif args.cmd == "signoff":
        problems = signoff(files, json.loads(Path(args.reviews).read_text()))
    else:
        problems = stamp(files, args.sender)
    for p in problems:
        print(f"::error::{p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
