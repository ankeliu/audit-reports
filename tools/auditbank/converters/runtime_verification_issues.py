"""Runtime Verification issue-tracker input (stub, not implemented yet).

RV said it would rather sync the standard file from its internal issue tracker than from the PDF.
Their findings live as GitHub issues in an engagement repository; each issue carries the finding
ID (`A1`, `B3`, ...), title, severity / difficulty / recommended-action labels, the Description and
Recommendation as markdown, and the remediation status with links to the fixing PR and commit.
Converting from that source would skip PDF text extraction entirely and give exact locations and
full commit hashes.

To be implemented when RV shares a sample export (issue JSON from the GitHub API, or their own
export format). The intended shape mirrors `RuntimeVerificationConverter`: `extract()` returns the
same firm-native finding dicts (`source_id`, `title`, `severity`, `difficulty`, `recommended_action`,
`description`, `recommendation`, `status`), so `normalize()` can be reused unchanged.
"""


def extract_issues(source: str) -> dict:
    raise NotImplementedError("RV issue-tracker input: waiting for a sample export from Runtime Verification")
