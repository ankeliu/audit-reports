"""Constants pulled from AUDIT_REPORT_TEMPLATE.md, so the renderer never hand-copies template text."""

import re
from functools import cache

from .paths import TEMPLATE_PATH

_COMMENT = re.compile(r"<!--[\s\S]*?-->")


def _section(number: int) -> str:
    text = TEMPLATE_PATH.read_text()
    match = re.search(rf"^## {number}\. .*?$\n([\s\S]*?)(?=^## \d+\. |\Z)", text, re.M)
    if not match:
        raise RuntimeError(f"section {number} not found in {TEMPLATE_PATH}")
    return _COMMENT.sub("", match.group(1)).strip()


@cache
def severity_definitions() -> str:
    """Section 4 table, verbatim."""
    return _section(4)


@cache
def default_disclaimer_template() -> str:
    """Section 7 default text, with the `{Audit Firm}` placeholder intact."""
    return _section(7)


def default_disclaimer(firm: str) -> str:
    return default_disclaimer_template().replace("{Audit Firm}", firm)
