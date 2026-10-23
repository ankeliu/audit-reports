"""The site's JS parser/validator (site/auditbank.js) must agree with the Python tooling."""

import copy
import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from auditbank.parse import parse
from auditbank.paths import TEMPLATE_PATH
from auditbank.validate import validate_report, validate_text
from conftest import FIXTURES
from test_validate import CASES, TODAY, _set

HARNESS = Path(__file__).parent / "site_harness.js"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def run_js(jobs):
    out = subprocess.run(
        ["node", str(HARNESS)], input=json.dumps(jobs), capture_output=True, text=True, check=True
    ).stdout
    return json.loads(out)


def _texts():
    texts = [FIXTURES / "minimal-valid.md", FIXTURES / "invalid-counts.md", TEMPLATE_PATH]
    texts += sorted(Path(__file__).parent.glob("../examples/*.md"))
    return [p.read_text() for p in texts]


def test_parse_matches_python():
    texts = _texts()
    results = run_js([{"kind": "parse", "text": t} for t in texts])
    for text, js in zip(texts, results, strict=True):
        assert js.get("report") == json.loads(json.dumps(parse(text)))


def _key(problems):
    return sorted({(p["level"], p["code"], p["path"]) for p in problems})


def test_validate_text_matches_python():
    texts = _texts() + ["no frontmatter"]
    results = run_js([{"kind": "validate_text", "text": t, "today": TODAY.isoformat()} for t in texts])
    for text, js in zip(texts, results, strict=True):
        assert _key(js["problems"]) == _key(validate_text(text, today=TODAY))


def test_every_rule_case_matches_python(valid_report):
    jobs, expected = [], []
    for _code, _level, mutations in CASES:
        report = copy.deepcopy(valid_report)
        for dotted, value in mutations:
            _set(report, dotted, value)
        jobs.append({"kind": "validate_report", "report": report, "today": TODAY.isoformat()})
        expected.append(validate_report(report, today=TODAY))
    for js, py in zip(run_js(jobs), expected, strict=True):
        js_codes = {(p["level"], p["code"]) for p in js["problems"]}
        py_codes = {(p["level"], p["code"]) for p in py}
        assert js_codes == py_codes
        assert {p["path"] for p in js["problems"] if p["code"] != "SCHEMA"} == {
            p["path"] for p in py if p["code"] != "SCHEMA"
        }


def test_today_is_injectable():
    assert dt.date.fromisoformat(TODAY.isoformat()) == TODAY
