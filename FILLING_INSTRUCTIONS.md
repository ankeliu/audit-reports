# Filling instructions -- Stellar Audit Bank standard report (v0.2-draft)

These instructions are written to be followed by a human auditor or by an AI agent converting an existing report. Follow them exactly; downstream tooling (ecosystem security dashboards, AI audit assistants, cross-audit context retrieval) parses these files programmatically.

## Purpose

Every completed Audit Bank audit is published in this format so audit firms and ecosystem security tool builders have structured, high-quality context on prior audits: what was reviewed, what was found, on one comparable scale, and whether it was fixed. Your report is both a human document and a dataset row. The firm's original PDF remains the authoritative report; this file is a derived summary.

## Golden rules

1. **Findings are the product.** Spend your effort there. Everything else is context and should be short.
2. **First sentence of every finding states the actual issue.** A reader scanning only titles and first sentences must understand every issue in the report.
3. **Depth without verbosity.** Go deep on root cause, attack path, and fix. Do not go deep on "how the system works" -- keep project context near ~300 words and link out. Length figures are guidance, not hard caps; the Assumptions and limitations section has no cap at all.
4. **Every finding is human-verified.** Tool- and AI-assisted discovery is welcome and disclosure in `audit.tooling` is encouraged -- it is context, never a quality penalty. No finding enters this report without an engineer confirming it is real, reachable, and correctly rated.
5. **Confidentiality beats completeness, honestly declared.** Never publish what the client hasn't approved or what would endanger unfixed code. Use the redaction mechanics below instead of leaving fields blank -- "withheld" is a valid, first-class value; silently omitting is not.
6. **Never invent.** Unknown = `null`. Do not drop Informational findings to make counts look better; do not merge distinct issues into one finding.

## Severity: two fields, firm-owned

Every finding carries two severity fields:

- **Unified severity** (required enum): `Critical | High | Moderate | Low | Informational`, assigned by the firm using the definitions in the template's Section 4. This exists solely for cross-audit comparability.
- **Firm severity rating** (required free text): the firm's own label, score, and system, verbatim -- e.g. "BVSS 2.0: 7.5 (High)", "Spec deviation, no exploitability claim". Nothing is lost in translation because nothing is translated away.

Rules:
- The **firm performs the mapping**, not SDF. In case of dispute between the two fields, the firm's original rating governs.
- Mapping guide: Critical → Critical; High / Major → High; Medium / Moderate → Moderate; Low / Minor → Low; Informational / Note / Best Practice / Gas / QA → Informational. CVSS: 9.0-10 → Critical, 7.0-8.9 → High, 4.0-6.9 → Moderate, 0.1-3.9 → Low. Definitions win over numeric scores -- sanity-check the band against Section 4.
- Findings that aren't exploitability claims (formal spec gaps, violated properties, centralization risks, economic manipulation): rate by consequence using the Section 4 definitions, which cover broken guarantees and control compromise, not only fund loss. When in doubt, rate Moderate and explain in the Description.
- Reports are pinned to the schema version they were submitted under. Published reports are never retroactively re-mapped to later scales.

## Disclosure and redaction

- `publication.disclosure_status`: `public` (cleared for the public archive), `embargoed` (submit now, publish after `embargo_until`), `redacted` (public with specific fields withheld).
- Submit your report **when you would normally publish it to the world** -- i.e. after client publication approval and, typically, after remediation -- not at engagement close.
- **Proof / attack path** is required for Critical and High, but `Withheld pending remediation` is always an acceptable value -- for unremediated findings, for patterns that exist in adjacent deployed code, or per your disclosure policy. Set `Redacted: true` with the reason on that finding.
- **Redaction tracks the authoritative PDF.** Redact in this summary only what is also withheld from (or redacted in) the published PDF. If the full finding is already public in the PDF, redacting it here serves no purpose -- disclosure decisions are made once, at the report level, and both artifacts reflect them identically.
- `repositories[].url`, `in_scope_paths`, and `Location` may be `"withheld"` for private pre-launch codebases -- disclosure of these is the client's decision, not the firm's obligation.

## Step-by-step

### Step 1 -- YAML frontmatter
- Fill every field; `"withheld"` where confidentiality applies, `null` where genuinely unknown or inapplicable. Dates `YYYY-MM-DD`, commit hashes full 40 characters.
- `repositories` is a list -- one entry per repo for multi-repo engagements. `commit_final` stays `null` unless a fix review engagement actually occurred.
- `publication.license`: state reuse terms (e.g. "CC BY-ND 4.0" or "All rights reserved -- summary published with permission"). Copyright stays with the firm.
- `publication.conversion_method`: `firm-native` (written in this format) or `ai-converted-firm-reviewed` (AI-converted from your PDF, then reviewed and signed off by a firm engineer). AI-converted reports without firm review are not accepted.
- `auditors` is optional -- named credit or no attribution, firm's choice.
- `effort` fields are optional context (engineer-weeks, reviewer count) so findings counts are never read without a denominator.
- `findings_summary` counts MUST equal the number of finding blocks per unified severity. Recompute after any edit.

### Step 2 -- Executive summary (~250 words guidance)
Three paragraphs: engagement facts; most severe findings and their real-world impact; overall assessment plus the single most important next step. Written for a non-engineer reviewer.

### Step 3 -- Project context (~300 words guidance + table)
Only what a future reader needs to understand the findings. Fill the components table with in-scope contracts, paths, and trust assumptions.

### Step 4 -- Findings
- **ID format:** `{PROJECT}-{FIRM}-{NNN}`, uppercase, zero-padded (e.g. `TW-RV-003`). Firm abbreviations: `RV`, `HAL`, `OS`, `VER`, `CER`, `ZEL`, `SPB`, `OAK`, `QS`, `HSH`, `CS`. IDs are permanent -- never renumber after publication.
- **Order:** Critical → High → Moderate → Low → Informational; within a severity, by ID.
- **Difficulty / likelihood (optional):** a second axis for how hard the exploit is to realize, independent of impact -- e.g. exploitable by any user (High likelihood) vs. requiring a governance takeover (Medium) vs. requiring admin/deploy keys (Low). Use `Low | Medium | High` or your own rating verbatim (RV's "difficulty" and Certora's "likelihood" both map here); `null` if your methodology doesn't rate this axis. The unified severity remains the single required axis.
- **Status vocabulary (exact strings):** `Resolved` (fix reviewed and confirmed), `Fixed - Not Verified` (client reports a fix; no fix review performed), `Acknowledged` (client agrees, no fix yet), `Risk Accepted` (client explicitly chose not to fix), `Mitigated (off-chain)` (operational/monitoring mitigation, code unchanged), `Partially Resolved`, `Unresolved`, `Disputed` (firm and client disagree on validity or severity -- summarize both positions in Remediation notes).
- **Remediation verified by (exact strings):** `firm` (a paid fix review confirmed root cause addressed), `client-reported` (client's claim, unverified by the firm), `not-reviewed`. A client-supplied "fixed" is never recorded as a firm attestation: `Resolved` requires `firm`; client claims use `Fixed - Not Verified` + `client-reported`. Post-engagement tracking is not an ongoing obligation -- fields reflect state as of `report_date` / the fix review, nothing more.
- **Category (pick exactly one, the dominant):** `access-control-auth` (incl. require_auth misuse, auth-vs-authentication confusion, custom account contracts), `accounting-arithmetic`, `liveness-dos`, `upgrade-migration`, `state-archival-ttl` (Soroban state expiration, rent, TTL extension), `cross-contract-trust` (invocation trust, adapter/dependency boundaries), `oracle-external-dependency`, `economic-design` (incentive/game-theoretic, MEV, manipulation), `governance-centralization` (admin keys, timelocks, upgrade authority), `cryptography`, `data-validation`, `key-management-privacy`, `observability`, `code-quality`, `operational`.
- **Location:** repo-relative path with line range at the audited commit; multiple locations comma-separated, most important first; `"withheld"` permitted per disclosure rules.
- **Description:** 2-6 sentences. Sentence 1 = the flaw. Then root cause and exact code behavior. Functions and variables in backticks.
- **Impact:** concrete worst case -- who loses what, or which guarantee breaks, under which preconditions.
- **Proof / attack path:** numbered attacker steps, a PoC link, or `Withheld pending remediation`.
- **Recommendation:** the specific fix. "Add validation" is insufficient.
- **Remediation notes:** only after a fix review; must be consistent with `Remediation verified by`. Otherwise `null`.

### Step 5 -- Assumptions and limitations
No length cap. Trust assumptions the analysis relies on; for formal verification, the properties verified and not verified -- these are the result, state them fully. Known scope gaps ("in scope but reviewed with limited depth") may be disclosed here at the firm's discretion.

### Step 6 -- Methodology (optional)
The firm may omit this section entirely and defer to its PDF. If included, keep it high-level (~200 words guidance): phases, tooling, how tool/AI output was human-verified.

### Step 7 -- Disclaimer and license (mandatory)
Keep the template's default text or substitute the firm's own standard disclaimer. It must cover: point-in-time review, no warranty of absence of vulnerabilities, not an endorsement or investment advice, PDF authoritative, copyright/license. This section may not be null.

### Step 8 -- Self-validation checklist
- [ ] All frontmatter fields filled, `"withheld"`, or `null` -- and `disclosure_status` consistent with any withheld/redacted content
- [ ] `findings_summary` counts match the finding blocks exactly
- [ ] Every finding has all eight required table fields (Difficulty / likelihood may be null) plus Description, Impact, Recommendation
- [ ] Every Critical/High finding has a Proof / attack path or an explicit `Withheld pending remediation`
- [ ] Every finding has both a unified severity and the firm's own rating verbatim
- [ ] `Resolved` status appears only where `Remediation verified by: firm`
- [ ] Disclaimer and license section present; license stated in frontmatter
- [ ] `conversion_method` accurate; if AI-converted, a firm engineer has reviewed and signed off
- [ ] No confidential client information beyond what the client approved for publication
- [ ] Valid markdown, valid YAML frontmatter (lint before submitting)

## Instructions for AI agents converting existing PDF reports

1. Extract, never summarize away: every finding in the source must appear as a finding block. If the source merges several issues under one heading, split them and note `(split from source finding N)` in Remediation notes.
2. Copy the firm's original severity verbatim into `Firm severity rating`; propose the unified severity from the Section 4 definitions, flagged for firm confirmation -- the firm owns the final mapping.
3. Where the source lacks a required field, set `null` -- do not guess. Exception: **Category** may be inferred from the finding content when the source report has no category field (most don't) -- infer it, and flag it with a `<!-- CONVERSION-NOTE: category inferred -->` for firm confirmation. Where the source deliberately withholds something, use `"withheld"` and set redaction fields.
4. Flag every uncertainty in an HTML comment `<!-- CONVERSION-NOTE: ... -->` for the firm reviewer.
5. Set `conversion_method: ai-converted-firm-reviewed` only after a firm engineer has actually reviewed the output. Output must pass the Step 8 checklist.

## Submission

One PR per report, filename `reports/{project-slug}/{project-slug}--{firm-abbrev}--{YYYY-MM-DD}.md` (lowercase slug, firm abbreviation lowercase, date = `report.report_date`). Either open the PR yourself or use the submission page (<https://ankeliu.github.io/audit-reports/>): paste your published report URL or upload your `.md`/PDF, get an instant validation result, and it files the PR. The SDF audit coordinator reviews and merges. If the file was AI-converted, an engineer from your firm must approve the PR.
