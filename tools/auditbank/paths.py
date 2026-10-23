"""Locations of the repo-level files the tooling reads (schema, vocab, template).

The package is installed editable from `tools/`, so the repo root is two levels up.
"""

import json
from functools import cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schema"
REPORTS_DIR = REPO_ROOT / "reports"
TEMPLATE_PATH = REPO_ROOT / "AUDIT_REPORT_TEMPLATE.md"


@cache
def vocab() -> dict:
    return json.loads((SCHEMA_DIR / "vocab.json").read_text())


@cache
def parse_rules() -> dict:
    return json.loads((SCHEMA_DIR / "parse-rules.json").read_text())


@cache
def report_schema() -> dict:
    return json.loads((SCHEMA_DIR / "report-schema.json").read_text())


def firm_abbrev(firm_name: str | None) -> str | None:
    for abbrev, name in vocab()["firms"].items():
        if name == firm_name:
            return abbrev
    return None
