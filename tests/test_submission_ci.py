import re
import shutil

import pytest
import yaml
from auditbank import ci
from auditbank.parse import parse_file
from auditbank.paths import REPO_ROOT, vocab
from auditbank.render import render
from auditbank.submission import SubmissionError, check_form, comment, parse_issue_form
from conftest import FIXTURES

ISSUE_BODY = """### Audit firm

Halborn (HAL)

### Published report URL

https://www.halborn.com/audits/splyce/smart-contract-assessment-de69cd

### Attachment

_No response_

### Project slug

splyce

### Client approval

- [X] The client has approved public publication of this report

### Notes

_No response_
"""


def test_issue_form_dropdown_matches_vocab():
    form = yaml.safe_load((REPO_ROOT / ".github/ISSUE_TEMPLATE/submit-report.yml").read_text())
    firm = next(b for b in form["body"] if b.get("id") == "firm")
    options = [re.fullmatch(r"(.+) \((\w+)\)", o).groups() for o in firm["attributes"]["options"]]
    assert {abbrev: name for name, abbrev in options} == vocab()["firms"]


def test_parse_and_check_form():
    info = check_form(parse_issue_form(ISSUE_BODY))
    assert info["abbrev"] == "HAL" and info["firm"] == "Halborn"
    assert info["slug"] == "splyce"
    assert info["source"].startswith("https://www.halborn.com/") and info["attachment"] is None


def test_project_slug_is_optional():
    info = check_form(parse_issue_form(ISSUE_BODY.replace("splyce\n\n### Client", "_No response_\n\n### Client")))
    assert info["slug"] is None


def test_attachment_link_is_found():
    body = ISSUE_BODY.replace(
        "### Attachment\n\n_No response_",
        "### Attachment\n\n[report.pdf](https://github.com/user-attachments/files/123/report.pdf)",
    ).replace("https://www.halborn.com/audits/splyce/smart-contract-assessment-de69cd", "_No response_")
    info = check_form(parse_issue_form(body))
    assert info["attachment"] == "https://github.com/user-attachments/files/123/report.pdf"
    assert info["attachment_name"] == "report.pdf"


@pytest.mark.parametrize(
    "old,new,message",
    [
        ("- [X]", "- [ ]", "client-approval"),
        ("splyce\n\n### Client", "Splyce Finance\n\n### Client", "lowercase words"),
        ("Halborn (HAL)", "Someone Else (SE)", "unknown audit firm"),
        ("https://www.halborn.com/audits/splyce/smart-contract-assessment-de69cd", "_No response_", "attach"),
    ],
)
def test_form_errors(old, new, message):
    with pytest.raises(SubmissionError, match=message):
        check_form(parse_issue_form(ISSUE_BODY.replace(old, new)))


def test_unattached_pdf_gets_a_clear_message():
    body = ISSUE_BODY.replace(
        "https://www.halborn.com/audits/splyce/smart-contract-assessment-de69cd", "_No response_"
    ).replace("### Attachment\n\n_No response_", "### Attachment\n\nDrag Moonlight_report.pdf into this box.")
    with pytest.raises(SubmissionError, match="Moonlight_report.pdf wasn't attached"):
        check_form(parse_issue_form(body))


def test_comment_for_error():
    text = comment({"error": "the client-approval checkbox must be ticked", "problems": []})
    assert "could not be processed" in text and "client-approval" in text
    assert "Edit this issue" in text


@pytest.fixture
def draft(tmp_path, monkeypatch):
    report = parse_file(FIXTURES / "minimal-valid.md")
    report["publication"]["conversion_method"] = None
    report["findings"][0]["conversion_notes"] = ["category inferred: accounting-arithmetic"]
    path = tmp_path / "example.md"
    path.write_text(render(report))
    reviewers = tmp_path / "firm-reviewers.yml"
    reviewers.write_text("RV: ['@rv-engineer']\nHAL: []\n")
    monkeypatch.setattr(ci, "REVIEWERS_PATH", reviewers)
    return path


def test_gate_blocks_notes_without_label(draft):
    assert ci.gate([draft], set())
    assert ci.gate([draft], {"firm-reviewed"}, labeler="rv-engineer") == []


def test_gate_ignores_label_from_unlisted_account(draft):
    assert ci.gate([draft], {"firm-reviewed"}, labeler="someone-else")
    assert ci.gate([draft], {"firm-reviewed"}, labeler=None)


def test_stamp_requires_listed_reviewer(draft):
    assert ci.stamp([draft], "someone-else")
    assert parse_file(draft)["publication"]["conversion_method"] is None


def test_stamp_sets_method_and_clears_notes(draft):
    assert ci.stamp([draft], "RV-Engineer") == []
    report = parse_file(draft)
    assert report["publication"]["conversion_method"] == "ai-converted-firm-reviewed"
    assert report["findings"][0]["conversion_notes"] == []
    assert render(report) == draft.read_text()


def test_signoff_needs_approval_from_listed_handle(draft):
    ci.stamp([draft], "rv-engineer")
    reviews = [{"user": {"login": "random"}, "state": "APPROVED", "submitted_at": "2026-10-01T00:00:00Z"}]
    assert ci.signoff([draft], reviews)
    reviews.append({"user": {"login": "rv-engineer"}, "state": "APPROVED", "submitted_at": "2026-10-02T00:00:00Z"})
    assert ci.signoff([draft], reviews) == []
    reviews.append(
        {"user": {"login": "rv-engineer"}, "state": "CHANGES_REQUESTED", "submitted_at": "2026-10-03T00:00:00Z"}
    )
    assert ci.signoff([draft], reviews)


def test_firm_native_needs_no_signoff(tmp_path):
    path = tmp_path / "x.md"
    shutil.copyfile(FIXTURES / "minimal-valid.md", path)
    assert ci.signoff([path], []) == []
