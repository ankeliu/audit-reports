---
# ============================================================
# STELLAR AUDIT BANK: STANDARD AUDIT REPORT (machine-readable)
# Schema version: 0.2 | Maintained by SDF Ecosystem Growth
# Reports are pinned to the schema version they were submitted
# under; published reports are never retroactively re-mapped.
# Fill every field; where confidentiality prevents disclosure,
# use "withheld" (see FILLING_INSTRUCTIONS.md), else null only
# where a field truly does not apply.
# ============================================================
schema_version: "0.2"
report:
  title: ""                    # e.g. "Trustless Work: Smart Escrow Audit"
  audit_firm: ""               # canonical firm name, e.g. "Runtime Verification"
  firm_contact: ""             # email or URL for report verification inquiries
  auditors: null               # optional list of named auditors; null if firm prefers no attribution
  client: ""                   # project / company name
  report_date: ""              # YYYY-MM-DD (final report publication)
  engagement_start: ""         # YYYY-MM-DD
  engagement_end: ""           # YYYY-MM-DD
  report_version: "1.0"        # bump on any post-publication revision
  pdf_url: null                # URL of the firm's original PDF; the PDF is the authoritative report and this file summarizes it
  firm_report_url: null        # firm-hosted report page, if public
publication:
  disclosure_status: "public"  # public | embargoed | redacted (see instructions)
  embargo_until: null          # YYYY-MM-DD if embargoed, else null
  license: ""                  # e.g. "CC BY-ND 4.0" or firm's own terms; content copyright remains with the firm
  conversion_method: ""        # firm-native | ai-converted-firm-reviewed
audit:
  type: []                     # one or more of: code-review | formal-verification | fuzzing | design-review | threat-modeling | economic-review | cryptographic-review | penetration-test | opsec-review | fix-review | audit-contest
  methods: []                  # free-form list, e.g. ["manual line-by-line review", "invariant testing"]
  tooling: null                # optional: notable tools used (static analyzers, fuzzers, AI assistants, solvers). Listing them is encouraged and never counts against the firm; every finding is confirmed by a person regardless
effort:                        # optional: engagement size, so finding counts can be read in context
  engineer_weeks: null
  reviewers: null
scope:
  chain: "stellar"             # stellar | ethereum | ... (lowercase)
  platform: "soroban"          # soroban | stellar-classic | offchain | multi
  languages: []                # e.g. ["rust"]
  repositories:                # one entry per repo; multi-repo engagements are common
    - url: ""                  # repo URL, or "withheld" for private pre-launch repos
      commit_start: ""         # full 40-char commit hash audited
      commit_final: null       # commit after fix review; MUST be null unless a fix review engagement actually occurred
  in_scope_paths: []           # e.g. ["contracts/escrow/src/**"]
  out_of_scope: []             # short bullets, e.g. ["off-chain backend", "frontend"]
  loc: null                    # integer, lines of code in scope (approx OK)
findings_summary:
  total: 0
  critical: 0
  high: 0
  moderate: 0
  low: 0
  informational: 0
severity_standard: "audit-bank-v0.2"   # confirms use of the unified scale in Section 4; the firm's own rating is preserved per finding and governs in case of dispute
---

# {Project Name}: {Audit Type} by {Audit Firm}

## 1. Executive summary

<!-- Guidance: ~250 words. Three paragraphs:
(1) who engaged whom, when, and what was audited;
(2) what was found, leading with the most severe issues and their real-world impact;
(3) overall assessment and the single most important next step for the project.
No methodology detail here. No marketing language. -->

## 2. Project context

<!-- Guidance: ~300 words. What the project does, who its users are, and the
2-4 architectural facts a future reader (human or AI) needs to understand the
findings: key contracts, roles/privileges, external dependencies, where value
is held. Link to project docs for the rest. -->

**Key contracts and roles**

| Component | Path | Role / trust assumption |
|---|---|---|
| | | |

## 3. Findings

<!-- HIGHEST-PRIORITY SECTION. One subsection per finding, ordered by unified
severity (Critical first), then by finding ID. Every finding uses the exact
field block below; tools parse it. See FILLING_INSTRUCTIONS.md. -->

### [{FINDING-ID}] {One-line title stating the actual issue}

| Field | Value |
|---|---|
| **Unified severity** | Critical / High / Moderate / Low / Informational |
| **Firm severity rating** | the firm's own label, score, and scale, as written in its report (e.g. "BVSS 2.0: 7.5 (High)"). If it disagrees with the unified severity, this rating wins |
| **Difficulty / likelihood** *(optional)* | Low / Medium / High, or the firm's own rating as written: how hard the issue is to exploit (e.g. any user, governance takeover, admin or deploy keys). Null if the firm doesn't rate this |
| **Status** | Resolved / Fixed - Not Verified / Acknowledged / Risk Accepted / Mitigated (off-chain) / Partially Resolved / Unresolved / Disputed |
| **Remediation verified by** | firm / client-reported / not-reviewed |
| **Category** | see taxonomy in FILLING_INSTRUCTIONS.md |
| **Location** | `path/to/file.rs:L120-L145` (or "withheld") |
| **Resolved in** | commit hash / PR URL / null |
| **Redacted** | false / true: reason (e.g. "true: PoC withheld pending remediation"). Must match the published PDF: if the finding is fully public there, there is nothing to redact |

**Description.**
<!-- 2-6 sentences. First sentence states the flaw plainly. Then the root
cause and the code behavior that makes it exploitable. Reference exact
functions/lines. -->

**Impact.**
<!-- 1-4 sentences. Concrete worst case: who loses what (or which guarantee
breaks), under which preconditions. Quantify where possible. -->

**Proof / attack path.** *(required for Critical and High; "Withheld pending remediation" is always acceptable)*
<!-- Numbered attacker steps, a link to a PoC test, or "Withheld pending
remediation". Minimal-reproducible. -->

**Recommendation.**
<!-- 1-4 sentences. The specific fix, not generalities. -->

**Remediation notes.** *(fill after a fix review engagement, else null)*
<!-- What the project changed, whether the fix fully addresses root cause,
residual risk, and who verified it (must match "Remediation verified by"). -->

---

<!-- repeat the finding block above for every finding -->

## 4. Unified severity definitions

<!-- The unified scale exists for cross-audit comparability only. The firm
performs the mapping; the firm's own rating is recorded per finding and
governs in case of dispute. -->

| Level | Definition |
|---|---|
| **Critical** | Directly exploitable now with no privileged preconditions: loss or freezing of user funds, full compromise of protocol control, or violation of a core safety property the protocol's security depends on. |
| **High** | Loss/freezing of funds, compromise of protocol control, or breach of a core guarantee requiring specific but realistic preconditions (a privileged role acting maliciously, a dependent contract compromised, timing conditions). Includes severe centralization of upgrade/admin keys where a single compromise endangers user funds. |
| **Moderate** | Violates intended behavior or degrades security guarantees: limited direct loss, loss requiring unlikely precondition chains, liveness failures with recovery paths, economic/oracle manipulation with bounded impact, or governance weaknesses with mitigating controls. |
| **Low** | Minor deviation from best practice with a plausible but low-impact security consequence. |
| **Informational** | No direct security impact: code quality, gas/efficiency, documentation, observability, test-coverage gaps. Use the Category field to distinguish these classes. |

## 5. Assumptions and limitations

<!-- No length limit: for formal verification, the assumptions are the result.
State: trust assumptions the analysis relies on, properties verified vs. not
verified, and known scope gaps the firm chooses to disclose (e.g. in-scope
components reviewed with limited depth due to time constraints). Disclosure of
coverage gaps is at the firm's discretion. -->

## 6. Methodology *(optional)*

<!-- Optional: the firm may leave this section out and point to its own
PDF (linked in frontmatter). If included: keep high-level (~200 words
guidance). Phases, tooling and how tool/AI output was human-verified, tests
added. -->

## 7. Disclaimer and license *(required; the firm may use its own standard text)*

<!-- Default text; replace with the firm's own disclaimer if preferred. -->

This report reflects a point-in-time review of the specified scope at the specified commit(s). It is not a warranty that the code is free of vulnerabilities, not an endorsement of the project, and not investment advice. Security reviews are time-boxed and cannot guarantee the absence of defects. The firm's original PDF report is the authoritative document; this markdown file is a derived summary prepared for the Stellar Audit Bank report archive. Copyright in the report content remains with {Audit Firm}; reuse is governed by the license stated in the frontmatter.

## 8. Appendix *(optional)*

<!-- Invariants verified, formal specs, links to test files added during the
engagement. Links + one-line descriptions. -->
