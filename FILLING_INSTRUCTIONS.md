# Filling instructions: Stellar Audit Bank standard report (v0.2)

Follow these instructions whether you write the report by hand or convert an existing one. Tools parse these files automatically, so the structure matters.

## Purpose

Every completed Audit Bank audit is published in this format so audit firms and security tool builders can see, for any prior audit, what was reviewed, what was found, how severe it was on one shared scale, and whether it was fixed. The firm's original PDF or report page remains the authoritative report. This file is a summary of it.

## Ground rules

1. **Findings matter most.** Put your effort there and keep everything else short.
2. **Lead with the issue.** The first sentence of every finding states the actual flaw. Someone reading only titles and first sentences should understand every issue.
3. **Deep on findings, brief on background.** Explain root cause, attack path, and fix in full. Keep project context to about 300 words and link to the project's docs. Word counts are guidance, not limits, and Assumptions and limitations has no limit.
4. **A person confirms every finding.** Tools and AI may help find issues, and listing them in `audit.tooling` is encouraged and never counts against you. But an engineer must confirm each finding is real, reachable, and correctly rated.
5. **Withhold openly, never silently.** Don't publish anything the client hasn't approved or that would put unfixed code at risk. Mark it `"withheld"` instead of leaving it blank or leaving it out.
6. **Don't invent or drop anything.** Use `null` for unknowns. Keep every Informational finding, and don't merge separate issues into one.

## Severity: two fields, both set by the firm

Every finding has two severity fields:

- **Unified severity** (required): `Critical`, `High`, `Moderate`, `Low`, or `Informational`, using the definitions in Section 4 of the template. It exists so findings can be compared across audits.
- **Firm severity rating** (required): your own label, score, and scale, exactly as in your report, for example "BVSS 2.0: 7.5 (High)" or "Spec deviation, no exploitability claim".

Rules:

- **The firm chooses the unified severity**, not SDF. If the two fields ever disagree, the firm's own rating wins.
- Mapping guide: Critical to Critical; High or Major to High; Medium or Moderate to Moderate; Low or Minor to Low; Informational, Note, Best Practice, Gas, or QA to Informational. CVSS: 9.0 to 10 is Critical, 7.0 to 8.9 High, 4.0 to 6.9 Moderate, 0.1 to 3.9 Low. If a score and the Section 4 definitions disagree, the definitions win.
- Findings that aren't exploits (spec gaps, violated properties, centralization risks, economic manipulation) are rated by consequence using Section 4, which covers broken guarantees and loss of control as well as loss of funds. If unsure, use Moderate and explain why in the Description.
- A report keeps the schema version it was submitted under. Published reports are never re-rated against later scales.

## Disclosure and redaction

- Submit a report **only when you would publish it anyway**: after the client approves publication and usually after fixes, not when the engagement ends.
- `publication.disclosure_status` is `public`, `embargoed` (with the release date in `embargo_until`), or `redacted` (public, with specific fields withheld).
- **Proof / attack path** is required for Critical and High findings, but `Withheld pending remediation` is always acceptable: for unfixed issues, for patterns that exist in other deployed code, or because of your disclosure policy. Set `Redacted` to `true` with the reason on that finding.
- **Match the PDF.** Withhold something here only if it is also withheld in the published PDF. If the finding is fully public in the PDF, there is nothing to redact here.
- `repositories[].url`, `in_scope_paths`, and `Location` may be `"withheld"` for private, pre-launch code. Whether to disclose them is the client's decision.

## Step by step

### Step 1: YAML frontmatter

- Fill every field. Use `"withheld"` for confidential values and `null` for unknown or not applicable ones. Dates are `YYYY-MM-DD`; commit hashes are the full 40 characters.
- `repositories` has one entry per repository. Leave `commit_final` as `null` unless a fix review actually took place.
- `publication.license`: the terms for reusing this summary, for example "CC BY-ND 4.0" or "All rights reserved; summary published with permission". Copyright stays with the firm.
- `publication.conversion_method`: `firm-native` if you wrote the report in this format, or `ai-converted-firm-reviewed` if it was converted from your PDF and then checked and approved by an engineer at your firm. AI conversions without that review are not accepted.
- `auditors` is optional: name the auditors or leave it `null`.
- `effort` (engineer weeks, reviewers) is optional context, so finding counts can be read against the size of the engagement.
- `findings_summary` must match the number of findings at each unified severity. Recount after every edit.

### Step 2: Executive summary (about 250 words)

Three paragraphs: the engagement; the most severe findings and their real-world impact; the overall assessment and the most important next step. Write for a reader who isn't an engineer.

### Step 3: Project context (about 300 words, plus the table)

Only what a reader needs to understand the findings. List the in-scope contracts, their paths, and their trust assumptions in the table.

### Step 4: Findings

- **ID:** `{PROJECT}-{FIRM}-{NNN}`, uppercase, three digits, for example `TW-RV-003`. Firm abbreviations: `RV`, `HAL`, `OS`, `VER`, `CER`, `ZEL`, `SPB`, `OAK`, `QS`, `HSH`, `CS`. IDs never change after publication.
- **Order:** Critical, High, Moderate, Low, Informational; by ID within each severity.
- **Difficulty / likelihood (optional):** how hard the issue is to exploit, separate from its impact. For example, any user can exploit it (High likelihood), it needs a governance takeover (Medium), or it needs admin or deploy keys (Low). Use `Low`, `Medium`, or `High`, or your own rating as written (RV's "difficulty" and Certora's "likelihood" both go here). Use `null` if you don't rate this.
- **Status (exact values):**
  - `Resolved`: the fix was reviewed and confirmed
  - `Fixed - Not Verified`: the client says it is fixed; no fix review was done
  - `Acknowledged`: the client agrees but hasn't fixed it yet
  - `Risk Accepted`: the client chose not to fix it
  - `Mitigated (off-chain)`: handled by operations or monitoring; code unchanged
  - `Partially Resolved`
  - `Unresolved`
  - `Disputed`: the firm and client disagree on validity or severity (summarize both views in Remediation notes)
- **Remediation verified by (exact values):** `firm` (a fix review confirmed the root cause is addressed), `client-reported` (the client's claim, not checked by the firm), or `not-reviewed`. `Resolved` requires `firm`; a client's claim uses `Fixed - Not Verified` with `client-reported`. These fields describe the state at `report_date` or the fix review; firms aren't expected to track fixes after that.
- **Category (pick the one that fits best):**
  - `access-control-auth`: including `require_auth` misuse and custom account contracts
  - `accounting-arithmetic`
  - `liveness-dos`
  - `upgrade-migration`
  - `state-archival-ttl`: Soroban state expiration, rent, TTL extension
  - `cross-contract-trust`: trust between contracts, adapters, and dependencies
  - `oracle-external-dependency`
  - `economic-design`: incentives, MEV, manipulation
  - `governance-centralization`: admin keys, timelocks, upgrade authority
  - `cryptography`
  - `data-validation`
  - `key-management-privacy`
  - `observability`
  - `code-quality`
  - `operational`
- **Location:** path from the repository root, with a line range, at the audited commit. Separate multiple locations with commas, most important first. May be `"withheld"`.
- **Description:** 2 to 6 sentences. The first states the flaw; the rest give the root cause and the exact code behavior. Put function and variable names in backticks.
- **Impact:** the realistic worst case: who loses what, or which guarantee breaks, and under what conditions.
- **Proof / attack path:** numbered attacker steps, a link to a proof-of-concept test, or `Withheld pending remediation`.
- **Recommendation:** the specific fix. "Add validation" is not enough; say what to validate and where.
- **Remediation notes:** only after a fix review, and consistent with `Remediation verified by`. Otherwise `null`.

### Step 5: Assumptions and limitations

No length limit. List the trust assumptions the review relies on. For formal verification, state which properties were and weren't verified; these are the result. You may also note parts of the scope that got less depth.

### Step 6: Methodology (optional)

You may leave this out and point to your PDF. If included, keep it to about 200 words: phases, tools, and how tool or AI output was checked by people.

### Step 7: Disclaimer and license (required)

Keep the template's text or use your firm's standard disclaimer. It must say the review is a point-in-time review, that it is no guarantee the code is free of vulnerabilities, that it is not an endorsement or investment advice, that the PDF is authoritative, and under what license this summary may be reused.

### Step 8: Checklist before submitting

- [ ] Every frontmatter field is filled, `"withheld"`, or `null`, and `disclosure_status` matches any withheld or redacted content
- [ ] `findings_summary` matches the findings exactly
- [ ] Every finding has all table fields (Difficulty / likelihood may be `null`) plus Description, Impact, and Recommendation
- [ ] Every Critical and High finding has a Proof / attack path or `Withheld pending remediation`
- [ ] Every finding has both a unified severity and your firm's own rating
- [ ] `Resolved` appears only with `Remediation verified by: firm`
- [ ] The disclaimer is present and the license is stated in the frontmatter
- [ ] `conversion_method` is correct, and an engineer at your firm has approved any AI conversion
- [ ] Nothing confidential beyond what the client approved for publication
- [ ] `auditbank validate` passes

## Converting an existing report (by hand or with tools)

1. Carry over every finding in the source. If the source groups several issues under one heading, split them and add `(split from source finding N)` to Remediation notes.
2. Copy the firm's severity exactly into `Firm severity rating` and propose a unified severity from Section 4 for the firm to confirm.
3. If the source lacks a required field, use `null`; don't guess. The one exception is **Category**, which most reports don't have: infer it and flag it for the firm to confirm. If the source deliberately withholds something, use `"withheld"` and fill in the redaction fields.
4. Flag anything uncertain with an HTML comment, `<!-- CONVERSION-NOTE: ... -->`, for the firm's reviewer. Pull requests can't be merged while these remain unless the firm signs off.
5. Set `conversion_method: ai-converted-firm-reviewed` only after an engineer at the firm has reviewed the result.

## Submission

One pull request per report, saved as `reports/{project-slug}/{project-slug}--{firm-abbrev}--{YYYY-MM-DD}.md` (lowercase, with the date from `report.report_date`). Open the PR yourself, or use the [submission page](https://ankeliu.github.io/audit-reports/) to send a report link or PDF and have the PR opened for you. The SDF audit coordinator reviews and merges. For AI conversions, an engineer at your firm must approve the PR first.
