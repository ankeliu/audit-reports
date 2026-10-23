"""`auditbank convert`: detect -> convert -> render -> write."""

import shutil
from pathlib import Path

from .converters import CONVERTERS
from .converters.base import finalize
from .detect import detect
from .paths import REPORTS_DIR, firm_abbrev
from .render import render


def default_out(report: dict, slug: str) -> Path:
    abbrev = (firm_abbrev(report["report"]["audit_firm"]) or "x").lower()
    return REPORTS_DIR / slug / f"{slug}--{abbrev}--{report['report']['report_date']}.md"


def convert(
    source: str,
    firm: str | None = None,
    project_slug: str | None = None,
    out=None,
    use_ai=False,
    ai_log: list | None = None,
) -> Path:
    key, raw = detect(source, firm)
    if key is None:  # already a standard file: copy it to the output path untouched
        if not out:
            raise SystemExit("standard .md detected: pass --out, or run `auditbank validate` on it directly")
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        if raw.path.resolve() != out.resolve():
            shutil.copyfile(raw.path, out)
        return out

    converter = CONVERTERS[key]()
    firm_report = converter.extract(raw)
    slug = project_slug or converter.default_slug(firm_report)
    report = converter.normalize(firm_report, slug)
    if use_ai:
        from .ai import fill_gaps

        report = fill_gaps(report, firm_report, log=ai_log)
    report = finalize(report)
    out = Path(out) if out else default_out(report, slug)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(report), encoding="utf-8")
    return out
