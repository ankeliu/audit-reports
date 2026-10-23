# Contributing a report

This repo accepts Stellar Audit Bank reports in the standard format, one PR per report, submitted when the firm would publish the report publicly anyway.

1. **Write or convert the report** using [`AUDIT_REPORT_TEMPLATE.md`](AUDIT_REPORT_TEMPLATE.md), following [`FILLING_INSTRUCTIONS.md`](FILLING_INSTRUCTIONS.md) exactly. The firm's PDF or report page stays authoritative; link it in `report.pdf_url` or `report.firm_report_url`.
2. **Validate locally:**
   ```sh
   pip install -e tools/
   auditbank validate path/to/report.md
   ```
3. **Submit.** Either open a PR adding `reports/{project-slug}/{project-slug}--{firm-abbrev}--{YYYY-MM-DD}.md`, or use the submission page (`<PAGES_URL>`), which checks your file or converts your published report and files the PR for you.
4. **Review.** CI runs the same checks as `auditbank validate`. The SDF audit coordinator confirms the engagement, the submitting account, and client publication approval, then merges. AI-converted files also need an approving review from an engineer at your firm.

Corrections are new PRs that bump `report.report_version`. Questions: your Audit Bank Slack channel.
