import json
from types import SimpleNamespace

from auditbank import ai
from auditbank.converters.base import finalize
from auditbank.render import render
from auditbank.validate import validate_text
from test_converters import DRAFT_WARNINGS, TODAY, _codes

LONG_SUMMARY = " ".join(["The review covered the escrow contracts and found 3 issues."] * 40)


class FakeClient:
    """Answers each job from `answers[job]`; records request kwargs."""

    def __init__(self, answers, stop_reason="end_turn", fail=False):
        self.answers, self.stop_reason, self.fail, self.calls = answers, stop_reason, fail, []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail:
            raise RuntimeError("network down")
        props = set(kwargs["output_config"]["format"]["schema"]["properties"])
        job = {"description": "split", "items": "category", "unified_severity": "severity", "summary": "summary"}[
            next(p for p in ("description", "items", "unified_severity", "summary") if p in props)
        ]
        answer = self.answers[job]
        text = json.dumps(answer(kwargs) if callable(answer) else answer)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=text)], stop_reason=self.stop_reason, model=ai.MODEL
        )


def _draft(valid_report):
    r = valid_report
    r["publication"]["conversion_method"] = None
    f0 = r["findings"][0]
    f0["description"] = (
        "`release` does not mark the escrow as settled before transferring funds. "
        "The approver can release the same escrow twice and drain funds belonging to other escrows."
    )
    f0["impact"] = "`release` does not mark the escrow as settled before transferring funds."
    f0["conversion_notes"] = ["no Impact heading in the source: Impact repeats the first sentence; firm to rewrite"]
    r["findings"][1]["conversion_notes"] = ["category inferred: data-validation"]
    r["findings"][2]["conversion_notes"] = [
        'Veridise "Warning" mapped to unified "Low" (Warning sits between Info and Low); Veridise to confirm'
    ]
    r["sections"]["executive_summary"] = LONG_SUMMARY
    r["conversion_notes"] = ["Section 1 is the firm's Executive Summary verbatim"]
    return r


ANSWERS = {
    "split": {
        "description": "`release` does not mark the escrow as settled before transferring funds.",
        "impact": "The approver can release the same escrow twice and drain funds belonging to other escrows.",
        "proof": None,
    },
    "category": {"items": [{"id": "EX-RV-002", "category": "governance-centralization", "justification": "admin"}]},
    "severity": {"unified_severity": "Informational", "justification": "no security impact"},
    "summary": {"summary": "Example Escrow engaged the firm, which found 3 issues."},
}


def test_fill_gaps_applies_all_four_jobs(valid_report):
    report = _draft(valid_report)
    client, log = FakeClient(ANSWERS), []
    report = finalize(ai.fill_gaps(report, client=client, log=log))

    f = {x["id"]: x for x in report["findings"]}
    assert f["EX-RV-001"]["impact"].startswith("The approver can release")
    assert any("split by AI" in n for n in f["EX-RV-001"]["conversion_notes"])
    assert f["EX-RV-002"]["category"] == "governance-centralization"
    assert f["EX-RV-003"]["unified_severity"] == "Informational"
    assert report["sections"]["executive_summary"].startswith("Example Escrow engaged")
    assert [e["job"] for e in log] == ["split", "category", "severity", "summary"]
    assert all(len(e["prompt_sha256"]) == 16 for e in log)

    call = client.calls[0]
    assert call["model"] == "claude-opus-5-5" and call["fallbacks"] == "default"
    assert call["betas"] == [ai.FALLBACK_BETA]
    assert "thinking" not in call and "temperature" not in call

    text = render(report)
    assert _codes(validate_text(text, today=TODAY)) == DRAFT_WARNINGS
    assert "| **Category** | governance-centralization |" in text


def test_guards_reject_invented_text_and_numbers(valid_report):
    report = _draft(valid_report)
    answers = dict(ANSWERS)
    answers["split"] = {**ANSWERS["split"], "impact": "Attackers can steal 1,000,000 tokens."}
    answers["summary"] = {"summary": "The firm found 7 critical issues worth $5 million."}
    log = []
    before_impact = report["findings"][0]["impact"]
    report = ai.fill_gaps(report, client=FakeClient(answers), log=log)
    assert report["findings"][0]["impact"] == before_impact
    assert report["sections"]["executive_summary"] == LONG_SUMMARY
    assert {e["job"]: e.get("rejected") for e in log}["summary"].startswith("summary introduced numbers")
    assert {e["job"]: e.get("rejected") for e in log}["split"] == "split was not verbatim source text"


def test_api_failure_and_refusal_leave_draft_unchanged(valid_report):
    for client in (FakeClient(ANSWERS, fail=True), FakeClient(ANSWERS, stop_reason="refusal")):
        report = _draft(json.loads(json.dumps(valid_report)))
        snapshot = json.dumps(report, sort_keys=True)
        ai.fill_gaps(report, client=client)
        assert json.dumps(report, sort_keys=True) == snapshot


def test_log_markdown():
    md = ai.log_markdown(
        [{"job": "split", "model": "m", "prompt_sha256": "a", "response_sha256": "b", "stop_reason": "end_turn"}]
    )
    assert "| split | `m` | `a` | `b` | end_turn |" in md
