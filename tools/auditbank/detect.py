"""URL or file -> which converter (or None for a standard .md that only needs validating)."""

import re
from pathlib import Path
from urllib.parse import urlparse

from .converters import CONVERTERS
from .converters.base import RawDoc, fetch, is_url

NO_CONVERTER = "no converter for this source; submit a standard .md or ask SDF to add your firm"
PDF_MARKERS = {"rv": "Runtime Verification", "ver": "Veridise"}


class DetectionError(ValueError):
    pass


def is_standard_md(text: str) -> bool:
    return bool(re.match(r"^﻿?---\s*\n[\s\S]*?^schema_version:", text, re.M))


def _pdf_identity(path: Path) -> str:
    """Metadata plus the first pages (RV puts its name after the cover and table of contents)."""
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        meta = " ".join(str(v) for v in (pdf.metadata or {}).values())
        return meta + "\n" + "\n".join((page.extract_text() or "") for page in pdf.pages[:8])


def detect(source: str, firm: str | None = None) -> tuple[str | None, RawDoc]:
    """Return (converter key or None for standard markdown, fetched document)."""
    if firm:
        if firm not in CONVERTERS:
            raise DetectionError(f"no converter for firm {firm!r} yet")
        return firm, fetch(source)
    for key, cls in CONVERTERS.items():
        if is_url(source) and cls.matches(source):
            return key, fetch(source)
    host = urlparse(source).netloc if is_url(source) else ""
    if "runtimeverification.com" in host and "rv" in CONVERTERS:
        return "rv", fetch(source)
    if "veridise.com" in host and "ver" in CONVERTERS:
        return "ver", fetch(source)
    raw = fetch(source)
    if raw.kind == "md" or raw.path.suffix.lower() in (".md", ".markdown"):
        if is_standard_md(raw.path.read_text(encoding="utf-8", errors="replace")):
            return None, raw
        raise DetectionError("markdown file has no `schema_version:` frontmatter; " + NO_CONVERTER)
    if raw.kind == "pdf":
        text = _pdf_identity(raw.path)
        for key, marker in PDF_MARKERS.items():
            if marker.lower() in text.lower() and key in CONVERTERS:
                return key, raw
    raise DetectionError(NO_CONVERTER)
