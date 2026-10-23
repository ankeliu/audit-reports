---
schema_version: '0.2'
report:
  title: Example Escrow -- Smart Contract Audit
  audit_firm: Runtime Verification
  firm_contact: contact@example.com
  auditors: null
  client: Example Escrow
  report_date: '2026-03-20'
  engagement_start: '2026-02-02'
  engagement_end: '2026-02-27'
  report_version: '1.0'
  pdf_url: https://example.com/reports/example-escrow.pdf
  firm_report_url: null
publication:
  disclosure_status: public
  embargo_until: null
  license: Apache-2.0
  conversion_method: firm-native
audit:
  type:
    - code-review
    - fix-review
  methods:
    - manual line-by-line review
    - property-based testing
  tooling: null
effort:
  engineer_weeks: 4
  reviewers: 2
scope:
  chain: stellar
  platform: soroban
  languages:
    - rust
  repositories:
    - url: https://github.com/example/escrow
      commit_start: 3f2a9c4e1b7d8a6f5e4c3b2a1908f7e6d5c4b3a2
      commit_final: 9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d
  in_scope_paths:
    - contracts/escrow/src/**
  out_of_scope:
    - frontend
    - off-chain indexer
  loc: 1840
findings_summary:
  total: 3
  critical: 0
  high: 1
  moderate: 2
  low: 0
  informational: 1
severity_standard: audit-bank-v0.2
---

# Example Escrow -- Code Review by Runtime Verification

## 1. Executive summary

Example Escrow engaged Runtime Verification to review its Soroban escrow contracts in February 2026.

The review found one High issue: `release` could be called twice for the same escrow, draining funds held for other users. It was fixed and verified.

The contracts are in good shape after remediation; the project should add a regression test for double release.

## 2. Project context

Example Escrow holds tokens on behalf of a payer until an approver releases them to a payee.

**Key contracts and roles**

| Component | Path | Role / trust assumption |
|---|---|---|
| Escrow | `contracts/escrow` | Holds all escrowed funds; approver is trusted to release correctly |

## 3. Findings

### [EX-RV-001] Release can be called twice, draining the escrow

| Field | Value |
|---|---|
| **Unified severity** | High |
| **Firm severity rating** | High (Difficulty: Medium; Recommended Action: Fix Code) |
| **Difficulty / likelihood** | Medium |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | accounting-arithmetic |
| **Location** | `contracts/escrow/src/lib.rs:L88-L102` |
| **Resolved in** | https://github.com/example/escrow/commit/9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d |
| **Redacted** | false |

**Description.**

`release` does not mark the escrow as settled before transferring funds. The `settled` flag is written after the token transfer, and nothing prevents a second call with the same escrow ID.

**Impact.**

The approver can release the same escrow twice and drain funds belonging to other escrows held by the contract.

**Proof / attack path.**

1. Create escrow A for 100 tokens.
2. Call `release(A)`.
3. Call `release(A)` again; another 100 tokens leave the contract.

**Recommendation.**

Set `settled = true` and persist it before the transfer, and reject `release` when `settled` is already true.

**Remediation notes.**

Fixed by checking and writing `settled` before the transfer; verified in the fix review.

---

### [EX-RV-002] Dispute resolver can be set to the zero address

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium (Difficulty: High; Recommended Action: Fix Code) |
| **Difficulty / likelihood** | High |
| **Status** | Acknowledged |
| **Remediation verified by** | not-reviewed |
| **Category** | data-validation |
| **Location** | `contracts/escrow/src/admin.rs:L14-L22` |
| **Resolved in** | null |
| **Redacted** | false |

**Description.**

`set_resolver` accepts any address, including one that cannot sign. Once set, disputes cannot be resolved.

**Impact.**

Funds in disputed escrows stay locked until the admin replaces the resolver.

**Proof / attack path.**

null

**Recommendation.**

Reject addresses that are not valid accounts or contracts in `set_resolver`.

**Remediation notes.**

null

---

### [EX-RV-003] Events omit the escrow ID

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative |
| **Difficulty / likelihood** | null |
| **Status** | Acknowledged |
| **Remediation verified by** | not-reviewed |
| **Category** | observability |
| **Location** | `contracts/escrow/src/events.rs:L5-L12` |
| **Resolved in** | null |
| **Redacted** | false |

**Description.**

The `released` and `refunded` events do not include the escrow ID.

**Impact.**

Indexers cannot attribute events to escrows without replaying state.

**Proof / attack path.**

null

**Recommendation.**

Add the escrow ID as an event topic.

**Remediation notes.**

null

---

## 4. Unified severity definitions

| Level | Definition |
|---|---|
| **Critical** | Directly exploitable now with no privileged preconditions: loss or freezing of user funds, full compromise of protocol control, or violation of a core safety property the protocol's security depends on. |
| **High** | Loss/freezing of funds, compromise of protocol control, or breach of a core guarantee requiring specific but realistic preconditions (a privileged role acting maliciously, a dependent contract compromised, timing conditions). Includes severe centralization of upgrade/admin keys where a single compromise endangers user funds. |
| **Moderate** | Violates intended behavior or degrades security guarantees: limited direct loss, loss requiring unlikely precondition chains, liveness failures with recovery paths, economic/oracle manipulation with bounded impact, or governance weaknesses with mitigating controls. |
| **Low** | Minor deviation from best practice with a plausible but low-impact security consequence. |
| **Informational** | No direct security impact: code quality, gas/efficiency, documentation, observability, test-coverage gaps. Use the Category field to distinguish these classes. |

## 5. Assumptions and limitations

- The token contract behaves as a standard SAC.
- The admin key is held by a multisig.

## 7. Disclaimer and license

This report reflects a point-in-time review of the specified scope at the specified commit(s). It is not a warranty that the code is free of vulnerabilities, not an endorsement of the project, and not investment advice. Security reviews are time-boxed and cannot guarantee the absence of defects. The firm's original PDF report is the authoritative document; this markdown file is a derived summary prepared for the Stellar Audit Bank report archive. Copyright in the report content remains with Runtime Verification; reuse is governed by the license stated in the frontmatter.
