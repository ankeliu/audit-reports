# Stellar Audit Bank -- standardized audit reports (v0.2-draft for feedback)

A shared, machine-readable archive of every completed Audit Bank audit. Goal: give audit firms and ecosystem security tool builders reliable context on prior audits -- what was reviewed, what was found, on one comparable severity scale, and whether it was fixed -- in a format both humans and AI tooling can consume directly. The firm's original PDF always remains the authoritative report; these files are derived summaries.

This draft is circulating to all Audit Bank firms for feedback before we lock v0.2. Please comment on anything: field choices, severity definitions, category taxonomy, disclosure mechanics, workflow.

## Contents

| File | Purpose |
|---|---|
| `AUDIT_REPORT_TEMPLATE.md` | The report template: YAML frontmatter (metadata, scope, publication/disclosure controls, findings counts) + structured markdown body, findings-first. |
| `FILLING_INSTRUCTIONS.md` | Exact filling rules for human auditors and for AI agents converting existing PDF reports: severity mapping, redaction mechanics, status vocabulary, category taxonomy, self-validation checklist. |

## Design principles

- **Findings first; severity stays the firm's.** Every finding carries two ratings: a required unified severity (Critical / High / Moderate / Low / Informational, for cross-audit comparability) and the firm's own rating verbatim, free text, in its own system. The firm performs the mapping; on any dispute, the firm's original rating governs. Reports are pinned to the schema version they were submitted under -- no retroactive re-mapping.
- **Gold standard = RV depth + Halborn concision.** Deep on root cause, attack path, and fix; short on background. Length figures are guidance, not caps -- and assumptions/limitations (the actual result of formal work) have no cap.
- **Responsible disclosure built in.** Firms submit when they would normally publish publicly (post client approval, typically post-remediation). Embargo dates, per-finding redaction, and "Withheld pending remediation" PoCs are first-class -- confidentiality never reads as non-compliance.
- **Context, not a league table.** SDF collects this data to give the ecosystem audit context, not to rank firms, and will not publish cross-firm performance metrics from it. Optional effort fields (engineer-weeks, reviewers) exist so counts are never read without a denominator. Tooling/AI disclosure is encouraged and never penalized -- every finding is human-verified regardless.
- **Both a document and a dataset.** YAML frontmatter and fixed finding field blocks make every report queryable without per-firm parsers.
- **Reference reports that informed the format:** [RV -- Trustless Work](https://runtimeverification.com/public-report/trustless-work) ([PDF](https://d3qv7503rlaw88.cloudfront.net/uploads/Trustless_Work_a57b9f5ac6.pdf)) and [Halborn -- Templar Protocol](https://www.halborn.com/audits/templar-protocol/smart-contract-assessment-0669c5).

## Repo and publication model

One public repo. The standard file is an addendum to a report the firm has already published, so there is nothing to stage privately.

1. **Submit when you would publish.** A firm submits a report only when it would normally publish it publicly (client approval given, embargoes elapsed, redactions applied). Readiness-gated, no fixed cadence.
2. **One PR per report** (report `.md`, linking the firm's authoritative PDF/URL). Open it directly, or use the submission page (<https://ankeliu.github.io/audit-reports/>), which validates your file or converts your published report and files the PR for you.
3. **CI validates** YAML schema, findings-count consistency, required fields, severity/status/category vocabulary, disclaimer present, filename convention.
4. **Human in the loop.** The SDF audit coordinator confirms the PR corresponds to an Audit Bank engagement, the submitting account belongs to the firm, and client publication approval exists, then merges. If the file was AI-converted, a firm engineer must approve the PR before merge (`conversion_method: ai-converted-firm-reviewed`).
5. **Corrections** come as new PRs bumping `report_version`. Reports stay pinned to the schema version they were submitted under.

## Tooling

- [`tools/`](tools/) -- the `auditbank` Python package: `auditbank validate` checks a report against the schema and cross-field rules (the same checks CI runs); `auditbank convert` drafts a standard file from a firm's published report (Halborn, Runtime Verification, Veridise) for firm review; `auditbank index` rebuilds the archive index.
- [`schema/`](schema/) -- JSON Schema and controlled vocabularies (severity, status, category, firm abbreviations).
- Submission page (<https://ankeliu.github.io/audit-reports/>) -- paste a published report URL or a standard `.md` for an instant check, then file the submission.
- [`examples/`](examples/) -- unreviewed converter output for one Halborn, one Runtime Verification, and one Veridise report. Temporary: removed once each firm approves its converter.

## Feedback requested from firms

1. Can your pipeline emit this format -- or can an AI conversion pass over your PDF, reviewed by your engineer, produce it -- in under an hour per report?
2. Severity: does the two-field model (unified + your own rating verbatim, yours governing on dispute) resolve the "lost in translation" concern? Do the unified definitions map cleanly onto your scale?
3. Do the disclosure mechanics (embargo, per-finding redaction, withheld PoCs, submission timed to your own publication) fit your responsible-disclosure policy?
4. Is the category taxonomy sufficient -- particularly the Soroban-specific classes (state-archival-ttl, cross-contract-trust, access-control-auth) -- or are there finding classes it can't express?
5. Remediation provenance: does the `firm / client-reported / not-reviewed` distinction plus `Fixed - Not Verified` status correctly bound your post-engagement obligations?
6. Does the mandatory disclaimer/license section, with your own boilerplate substitutable, cover your legal requirements? What's missing?
7. Would you want SARIF as a companion output alongside this markdown? (The frontmatter + finding blocks are designed to be losslessly convertible.)

## Open questions

1. **Veridise mappings.** `Warning` -> `Low`, `Intended Behavior` -> `Risk Accepted`, and `Invalid` items excluded from findings (listed in the Appendix). To confirm with Veridise.
2. **Vocabulary for v0.3.** Should an `Intended Behavior`-style status be added instead of mapping it to `Risk Accepted`?
3. **Halborn `commit_final`.** The report page lists many remediation commits; the converter takes the last one listed. To confirm with Halborn.
4. **Firm reviewers.** `.github/firm-reviewers.yml` is empty. The AI-conversion sign-off check has no effect until each firm names its GitHub handles.
5. **Default license for converted drafts.** Drafts default to `Apache-2.0`, but firms keep copyright and some publish under "All Rights Reserved" (e.g. Veridise). Each firm confirms its terms during review.
6. **Report date for web reports.** Halborn's page has no publication date; the converter uses the latest finding remediation date and flags it.
7. **Firm disclaimers.** The Halborn, RV, and Veridise disclaimers don't cover every element Section 7 requires (point-in-time, no warranty, PDF authoritative). Converters append the template default; firms may substitute their own.
8. **RV "Difficulty".** RV's Difficulty runs opposite to likelihood (High = hard to exploit), so it is stored as `Difficulty: High` rather than a bare `High`.
9. **Moving to `stellar/audit-reports`.** Change `REPO` in `site/app.js`, the Pages URL in README / FILLING_INSTRUCTIONS / CONTRIBUTING / the issue form, and the `$id` in `tools/auditbank/schema_gen.py` (then `auditbank schema --write`).

Contact: Anke Liu / Michael Berryhill / Ashley Wright -- SDF Ecosystem Growth, or your Audit Bank Slack channel.
