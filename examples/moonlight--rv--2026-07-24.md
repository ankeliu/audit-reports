---
schema_version: '0.2'
report:
  title: 'Moonlight Stellar: Security Audit Report'
  audit_firm: Runtime Verification
  firm_contact: null
  auditors: null
  client: Moonlight
  report_date: '2026-07-24'
  engagement_start: '2026-06-29'
  engagement_end: null
  report_version: '1.0'
  pdf_url: https://strapi.runtimeverification.com/uploads/Moonlight_report_64808bfd8e.pdf
  firm_report_url: null
publication:
  disclosure_status: public
  embargo_until: null
  license: Apache-2.0
  conversion_method: null
audit:
  type:
    - design-review
    - code-review
    - fix-review
  methods: []
  tooling:
    - Almanax
    - cargo audit
    - cargo outdated
    - cargo clippy
effort:
  engineer_weeks: null
  reviewers: null
scope:
  chain: stellar
  platform: soroban
  languages:
    - rust
  repositories:
    - url: https://github.com/Moonlight-Protocol/soroban-core
      commit_start: d65780bbf0a6f8b2b601e4a536b38000775c8a15
      commit_final: 867c23da1769a2f56e42449ce5d5315ffb5f4cdc
  in_scope_paths:
    - contracts/channel-auth
    - contracts/privacy-channel
  out_of_scope: []
  loc: null
findings_summary:
  total: 15
  critical: 0
  high: 0
  moderate: 3
  low: 0
  informational: 12
severity_standard: audit-bank-v0.2
---

# Moonlight Stellar: Security Audit by Runtime Verification

<!-- CONVERSION-NOTE: publication.license defaulted to "Apache-2.0"; firm to confirm reuse terms -->

<!-- CONVERSION-NOTE: report.engagement_end not stated in the report (RV states a 2-week review plus 1 week(s) of remediation support starting 2026-06-29); firm to supply -->

<!-- CONVERSION-NOTE: effort.engineer_weeks left null: the report states a 2-week review plus 1 week(s) of remediation support (calendar time), not effort -->

<!-- CONVERSION-NOTE: firm disclaimer lacks point-in-time / no-warranty / authoritative-PDF language; template default appended; firm to confirm or substitute its own -->

<!-- CONVERSION-NOTE: Impact taken from the Description text; check it (all 15 findings) -->

<!-- CONVERSION-NOTE: category inferred from the finding text; check it (all 15 findings) -->

## 1. Executive summary

Moonlight engaged Runtime Verification Inc. to conduct a 2-week review of the Moonlight core contracts,
followed by 1 week of remediation support. The audit began on June 29th, 2026, with the objective of
evaluating the correctness and security of the protocol, reviewing existing quality assurance measures,
identifying potential vulnerabilities, and providing recommendations for improvements in terms of code,
testing, and documentation.
The audit's primary focus is the UTXO-based privacy-channel contract, which implements a shielded
deposit / private-transfer / withdrawal lifecycle secured by P256 UTXO-owner signatures and Ed25519
provider co-signatures, with a secondary focus on the channel-auth (Quorum Auth) contract that gates this
activity via a 1-of-N provider signature threshold and owner-governed provider registry. Each actor
(Admin/Owner, Pending Admin, Privacy Provider, UTXO owner, Depositor, Withdrawal recipient, Transaction
submitter) has a specific, bounded set of capabilities, and verifying these bounds, including that a provider
cannot redirect, reduce, or drop a signer's intended outputs, is central to the protocol's security. The review
will also cover TTL maintenance across both in-scope contracts.

Runtime Verification's audit process began with a design review, where we familiarized ourselves with the
protocol's role structure and contract architecture by reviewing documentation and the existing codebase,
with the objective of identifying gaps in the role and permission model and providing recommendations on
how to address them. Using the understanding developed during the design review, we conducted a manual
code review of the contract implementation, comparing the implemented role capabilities and bounds
against the intended design and security best practices. This was followed by a one-week period of
remediation support, during which Runtime Verification worked with the Moonlight team to address identified
issues and verify proposed fixes.

## 2. Project context

- `contracts/channel-auth`: Contains the implementation of the Quorum Auth contract, including its authority model (Admin/Owner and Pending Admin roles via stellar_access::ownable), the provider registry and its 1-of-N Privacy Provider signature threshold enforced through require_provider, the asset-channel enable/disable lifecycle, and contract upgrade logic.
- `contracts/privacy-channel`: Contains the implementation of the Privacy Channel contract, including the UTXO-based deposit, private-transfer, and withdrawal flows; the P256 (secp256r1) UTXO- owner and Ed25519 depositor authorization and execution-binding of signed Create/ExtWithdraw conditions; conservation accounting across spend/create/withdraw operations; and persistent/instance TTL maintenance.

## 3. Findings

### [MOONLIGHT-RV-001] hash_payload encoding is not injective

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium (Difficulty: High; Recommended Action: Fix Code) (source: A1) |
| **Difficulty / likelihood** | Difficulty: High |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | access-control-auth |
| **Location** | `modules/primitives/src/lib.rs:L120-L163`, `modules/primitives/src/lib.rs:L11`, `modules/auth/src/core.rs:L126` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/97922db |
| **Redacted** | false |

**Description.**

hash_payload hashes the requesting contract, the four condition buckets concatenated back to back, and
the live_until_ledger , with no length prefixes, variant tags, or bucket separators:

`modules/primitives/src/lib.rs` lines 120-163 (at `d65780b`):

```rust
pub fn hash_payload(e: &Env, auth_payload: &AuthPayload, contract: &Bytes) -> Hash<32> {
    let mut b = Bytes::new(&e);
    b.append(&contract);

    let mut b_create = Bytes::new(&e);
    let mut b_deposit = Bytes::new(&e);
    let mut b_withdraw = Bytes::new(&e);
    let mut b_integrate = Bytes::new(&e);

    for cond in auth_payload.conditions.iter() {
        match cond {
            Condition::Create(utxo, amount) => {
                b_create.append(&Bytes::from_slice(&e, utxo.to_array().as_ref()));
                b_create.append(&Bytes::from_slice(&e, &amount.to_le_bytes()));
            }
// ... trimmed; see the authoritative PDF
```

The number of conditions in a bucket is unmarked, the ExtIntegration UTXO vector has no length
marker, and empty buckets contribute no bytes, so distinct condition lists can encode to the same byte
stream. Record sizes are fixed ( i128 amount 16 bytes, UTXO id 65 bytes, address strkey 56 bytes), so a
collision must preserve total length — easily arranged, since UTXO ids and amounts are free bytes. Three
examples:

Redistribute UTXOs within the integration bucket (same count, same total UTXOs):
Int(A, [u1, u2], m1), Int(B, [], m2) and Int(A, [u1], m1'), Int(B, [u2], m2') are both
274 bytes and can be made byte-identical by choosing the free UTXO/amount bytes so the boundaries
line up.
Cross-bucket through Create : a Create record is 81 bytes ( 65 + 16 ) and an ExtDeposit record
is 72 bytes ( 56 + 16 ); 81·a = 72·b first solves at a = 8, b = 9 , so an all- Create bucket of 8
conditions (648 bytes) can read as an all- ExtDeposit bucket of 9, provided the 56-byte address slots
decode as valid strkeys.
Same-size cross-bucket, no crafting: ExtDeposit and ExtWithdraw records encode identically —
both 56 + 16 bytes, address strkey then little-endian i128 , with no tag to separate them. Since the
buckets are adjacent and empty ones contribute nothing, [Dep(X, a)] and [Wd(X, a)] both encode
to enc(X, a) and are byte-identical, and the boundary slides freely ( Dep(X, a), Dep(Y, b) vs
Dep(X, a), Wd(Y, b) ). ExtIntegration(A, [], m) is likewise 72 bytes and collides with
Dep(A, m) / Wd(A, m) . Unlike the cases above, this needs no free-byte arrangement and no strkey
carving — the address slots hold the signer's own valid strkeys — so the colliding pair exists with
probability 1.

The variable-length variant:

`modules/primitives/src/lib.rs` line 11 (at `d65780b`):

```rust
ExtIntegration(Address, Vec<BytesN<65>>, i128), // contract id of the adapter, the keys to authorize the withdrawal, the amount to deposit
```

A signed hash therefore does not identify one condition list. A signer who reviews decoded conditions and
signs may have authorized a second list with the same encoding, which handle_utxo_auth will accept:

`modules/auth/src/core.rs` line 126 (at `d65780b`):

```rust
verify_signature(&e, &signer, &sig_variant, &msg)?;
```

Severity splits in two. The crafted cases ( Create -bucket reparse, integration redistribution) can't reuse an
existing honest signature (that would be a SHA-256 second preimage), so they need the payload composed
before signing. The deposit↔withdraw / empty-integration case has no such gate: a genuine signature over
[Dep(X, a)] is byte-identical to one over [Wd(X, a)] , so an untrusted submitter can reinterpret an
already-signed deposit as a withdraw at tx-build time. Either way it is an audit hazard: two bundles
indistinguishable to a signer break any "this signature authorized exactly this bundle" reasoning.

**Impact.**

Severity splits in two. The crafted cases ( Create -bucket reparse, integration redistribution) can't reuse an
existing honest signature (that would be a SHA-256 second preimage), so they need the payload composed
before signing. The deposit↔withdraw / empty-integration case has no such gate: a genuine signature over
[Dep(X, a)] is byte-identical to one over [Wd(X, a)] , so an untrusted submitter can reinterpret an
already-signed deposit as a withdraw at tx-build time. Either way it is an audit hazard: two bundles
indistinguishable to a signer break any "this signature authorized exactly this bundle" reasoning.

**Proof / attack path.**

null

**Recommendation.**

Make the signed encoding self-delimiting. Minimally, length-prefix every variable-length field (the
ExtIntegration UTXO vector especially, plus a count of conditions per bucket) and mark bucket
boundaries. Better, hash the canonical XDR of the Vec\<Condition> via ToXdr , injective by construction
and already a dependency, since equal_condition_sequence already compares conditions on XDR bytes:

`modules/primitives/src/lib.rs` lines 200-214 (at `d65780b`):

```rust
pub fn equal_condition_sequence(e: &Env, a: &Vec<Condition>, b: &Vec<Condition>) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut it_b = b.iter();
    for ca in a.iter() {
        match it_b.next() {
            Some(cb) => {
                // Compare on-wire representation to avoid needing Eq on Condition.
                if ca.to_xdr(&e) != cb.to_xdr(&e) {
                    return false;
                }
            }
            None => return false,
        }
```

The fix is small, and afterward a P256 signature covers exactly one condition list. Note that a whole- Vec
XDR digest is order-sensitive, so it also binds the ordering the signer reviewed; if order-insensitivity is
wanted, canonicalize (e.g. sort) the conditions before hashing.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/38 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/97922db) by hashing the canonical XDR of the whole Vec\<Condition> .

Since the only production caller passes contract as a fixed-length 56-byte strkey, the payload is injective
in practice.
The hash_payload function itself is still not injective, though: the payload is
contract ‖ xdr(conditions) ‖ le32(live_until)

and the contract field is appended as unframed Bytes, so injectivity of the full payload rests on the caller's
convention rather than the encoding. To avoid a future regression, consider length-prefixing the contract
field too, or XDR-encoding the whole (contract, conditions, live_until) tuple as one structure.

---

### [MOONLIGHT-RV-002] UTXO keys are never validated, value under a malformed key is locked permanently

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium (Difficulty: High; Recommended Action: Fix Code) (source: A2) |
| **Difficulty / likelihood** | Difficulty: High |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | liveness-dos |
| **Location** | `modules/storage/src/lib.rs:L80-L93`, `modules/utxo-core/src/core.rs:L116-L124` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/49b0fdb |
| **Redacted** | false |

**Description.**

No UTXO write path validates that a created key is a well-formed P-256 point. Store::create accepts any
65-byte value:

`modules/storage/src/lib.rs` lines 80-93 (at `d65780b`):

```rust
pub fn create(&mut self, utxo65: &BytesN<65>, amount: i128) {
    if amount <= 0 {
        panic_with_error!(&self.env, Error::InvalidCreateAmount);
    }

    let k = self.utxo_key(utxo65);

    if self.env.storage().persistent().get::<_, i128>(&k).is_some() {
        panic_with_error!(&self.env, Error::UtxoAlreadyExists);
    }

    self.env.storage().persistent().set(&k, &amount);
    self.bump_ttl(&k);
}
```

and process_bundle records it as-is, guarding only amount and prior existence:

`modules/utxo-core/src/core.rs` lines 116-124 (at `d65780b`):

```rust
for (create_utxo, amount) in bundle.create.iter() {
    if store.balance(&create_utxo) != -1 {
        panic_with_error!(e, MoonlightError::UtxoAlreadyExists);
    }

    assert_with_error!(&e, amount > 0, MoonlightError::InvalidCreateAmount);

    store.create(&create_utxo, amount);
    total_available_balance -= amount;
```

Under the deployed wiring the recorded bytes are also the sole spending credential: __check_auth
releases a UTXO only on a P-256 signature verifying under its key, and secp256r1_verify traps on a
malformed key, so any spend attempt on such a UTXO aborts the transaction. Value created under a
malformed key, for example a mistyped key in a signed Create condition, is therefore locked permanently
once the bundle settles.

The precondition is confined: the key is chosen by the party who signs the Create (or fixed as composer-
controlled residual), so this is honest-mistake loss, not an attack path. No trust boundary is crossed. But the
check is cheap, near-complete against the stated failure mode, and the failure is unrecoverable, which is
why it is worth stating.
The check cannot, of course, prove spendability: a valid on-curve key whose private key nobody holds is
equally locked, and no on-chain check can detect that. That residual risk is inherently a wallet-side concern,
which is why the recommendation below carries a documentation component either way.

**Impact.**

The precondition is confined: the key is chosen by the party who signs the Create (or fixed as composer-
controlled residual), so this is honest-mistake loss, not an attack path. No trust boundary is crossed. But the
check is cheap, near-complete against the stated failure mode, and the failure is unrecoverable, which is
why it is worth stating.
The check cannot, of course, prove spendability: a valid on-curve key whose private key nobody holds is
equally locked, and no on-chain check can detect that. That residual risk is inherently a wallet-side concern,
which is why the recommendation below carries a documentation component either way.

**Proof / attack path.**

null

**Recommendation.**

Reject a create whose key is not a valid P-256 point at the Store::create guard (a one-time cost paid
only at creation, never on spend), with the 0x04 prefix check as a minimum if full on-curve validation is
deemed too costly on-chain. In the latter case, document the burden explicitly so wallets validate keys
before funding them; wallets should validate regardless, since key-possession errors are undetectable on-
chain.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/44 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/49b0fdb) by checking the 0x04 marker in Store::create , and
documenting the additional validation burden.
Note that the comment identifier PC-16 collides with PC-16 from [A3]. When merging the PRs, this needs to
be resolved.

---

### [MOONLIGHT-RV-003] Byte-identical signed effects merge into one execution

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium (Difficulty: High; Recommended Action: Fix Code) (source: A3) |
| **Difficulty / likelihood** | Difficulty: High |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | data-validation |
| **Location** | `contracts/privacy-channel/src/transact.rs:L113-L130` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/90bf08c |
| **Redacted** | false |

**Description.**

The signed-effects binding compares conditions as a set keyed by canonical XDR bytes, so byte-identical
conditions collapse to one entry, discharged by a single executed occurrence:

`contracts/privacy-channel/src/transact.rs` lines 113-130 (at `d65780b`):

```rust
fn assert_signed_effects_are_executed(e: &Env, op: &ChannelOperation) {
    let mut authorized: Map<Bytes, ()> = Map::new(e);
    collect_authorized_effects(e, &mut authorized, &op.spend);
    collect_authorized_effects_from_external(e, &mut authorized, &op.deposit);

    let mut executed: Map<Bytes, ()> = Map::new(e);
    for (utxo, amount) in op.create.iter() {
        executed.set(Condition::Create(utxo, amount).to_xdr(e), ());
    }
    for (addr, amount, _conds) in op.withdraw.iter() {
        executed.set(Condition::ExtWithdraw(addr, amount).to_xdr(e), ());
    }

    // Subset: every signed effect must be executed exactly. Extra executed effects are allowed.
    for key in authorized.keys().iter() {
// ... trimmed; see the authoritative PDF
```

The balance still counts every spent and deposited amount in full. When two independently signed spends
each demand the identical ExtWithdraw(to, amount) , a composer holding both can deliberately batch
them: the bundle pays to once, and the difference becomes unsigned residual the composer allocates to
any recipient. Nor can such a bundle settle the effect once per signer: duplicate withdraw addresses are
rejected, and a combined (to, 2·amount) tuple has different bytes and fails the subset check — merged
execution is the only way the pair settles in one bundle.

The precondition is two independently signed identical conditions, each backed by its signer's value; a
composer cannot manufacture the second from the first, since duplicating a condition inside a signed list
breaks the signature, re-spending the same UTXO is rejected, and a condition on the composer's own

spend is backed by the composer's own funds. Byte identity requires equal address and equal amount (for
Create , the same key and amount). That arises when several parties withdraw a common amount to a
shared address, and — more plainly — when one party authorizes the same effect repeatedly: recurring
payments of a fixed amount to a fixed recipient produce byte-identical conditions on distinct spends, and a
composer batching two such spends pays the recipient once while the other payment becomes residual.

**Impact.**

The balance still counts every spent and deposited amount in full. When two independently signed spends
each demand the identical ExtWithdraw(to, amount) , a composer holding both can deliberately batch
them: the bundle pays to once, and the difference becomes unsigned residual the composer allocates to
any recipient. Nor can such a bundle settle the effect once per signer: duplicate withdraw addresses are
rejected, and a combined (to, 2·amount) tuple has different bytes and fails the subset check — merged
execution is the only way the pair settles in one bundle.

**Proof / attack path.**

null

**Recommendation.**

Distinguishing merged effects would require matching executed effects to signed conditions with multiplicity
rather than as a set — a substantial change to the binding and its balance reasoning.
Given the precondition, treat this as a batching constraint and document it: byte-identical execution-bound
conditions must never share a bundle, screening co-batched conditions is the submitter's responsibility, and
repeated identical effects (e.g. recurring payments) settle safely only in separate bundles.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/45 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/90bf08c) by documenting the batching constraint.
Note that the comment identifier PC-16 collides with PC-16 from [A2]. When merging the PRs, this needs to
be resolved.

This section includes observations that are not directly exploitable but highlight areas for improvement in
code clarity, maintainability, or best practices. While not critical, addressing these can strengthen the
system's overall robustness.

---

### [MOONLIGHT-RV-004] set_admin grants the maximum acceptance window, a pending transfer never auto-expires

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative (Recommended Action: Fix Code) (source: B1) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | state-archival-ttl |
| **Location** | `contracts/channel-auth/src/contract.rs:L86-L88`, `contracts/privacy-channel/src/contract.rs:L70-L72` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/e769ee7 |
| **Redacted** | false |

<!-- CONVERSION-NOTE: line numbers refer to commit(s) f9cdd3b, not the audited commit; confirm -->

**Description.**

Both contracts wrap ownable::transfer_ownership in set_admin , hardcoding live_until_ledger to
e.ledger().max_live_until_ledger() without exposing it:

`contracts/channel-auth/src/contract.rs` lines 86-88 (at `f9cdd3b`):

```rust
pub fn set_admin(e: &Env, new_admin: Address) {
    ownable::transfer_ownership(e, &new_admin, e.ledger().max_live_until_ledger());
}
```

`contracts/privacy-channel/src/contract.rs` lines 70-72 (at `f9cdd3b`):

```rust
pub fn set_admin(e: &Env, new_admin: Address) {
    ownable::transfer_ownership(e, &new_admin, e.ledger().max_live_until_ledger());
}
```

Per its documentation, transfer_ownership treats live_until_ledger as the ledger "until which the new
owner can accept." By always passing the maximum ledger, set_admin gives every pending transfer the
longest possible window: a PendingOwner set today stays acceptable for the full maximum temporary TTL
rather than lapsing on its own.
A pending transfer only matters while it lingers unaccepted, since a healthy one closes by acceptance.
While it lingers, whoever holds PendingOwner can accept_admin at any time until expiry, so if that key is
later compromised, the exposure runs for the full maximum TTL (months). A finite deadline caps this
automatically, without anyone monitoring. The owner can always overwrite PendingOwner via
set_admin(SAFE) , but that requires noticing and reacting, whereas expiry does not.

Additionally, because the deadline is fixed at the maximum, the documented 0 -cancels behavior is also
unreachable — there is no way to clear a pending transfer other than redirecting it (e.g. set_admin(self)
then accept_admin ).

**Impact.**

Per its documentation, transfer_ownership treats live_until_ledger as the ledger "until which the new
owner can accept." By always passing the maximum ledger, set_admin gives every pending transfer the
longest possible window: a PendingOwner set today stays acceptable for the full maximum temporary TTL
rather than lapsing on its own.
A pending transfer only matters while it lingers unaccepted, since a healthy one closes by acceptance.
While it lingers, whoever holds PendingOwner can accept_admin at any time until expiry, so if that key is
later compromised, the exposure runs for the full maximum TTL (months). A finite deadline caps this
automatically, without anyone monitoring. The owner can always overwrite PendingOwner via
set_admin(SAFE) , but that requires noticing and reacting, whereas expiry does not.

**Proof / attack path.**

null

**Recommendation.**

Thread the deadline through as set_admin(e, new_admin, live_until_ledger) and forward it to
transfer_ownership . Callers can then bound the acceptance window to a sensible finite value (and, as a
bonus, pass 0 to cancel), without changing behavior for callers who continue to pass the maximum.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/40 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/e769ee7) by threading live_until_ledger through set_admin in both
contracts, and additionally enforcing an in-contract 7-day ceiling ( AcceptanceWindowTooLong ) with
live_until_ledger == 0 exempted to preserve the library's cancel path.

---

### [MOONLIGHT-RV-005] Bundle balance accumulator uses raw arithmetics rather than checked_add/checked_sub

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative (Recommended Action: Fix Code) (source: B2) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | accounting-arithmetic |
| **Location** | `modules/utxo-core/src/core.rs:L95-L141`, `contracts/privacy-channel/src/transact.rs:L41-L58` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/12a5280 |
| **Redacted** | false |

**Description.**

process_bundle maintains its running conservation total, total_available_balance , with unchecked
+= / -= operators, rather than the checked_add / checked_sub pattern used elsewhere in the same flow.
The invariant that guards value conservation ( total_available_balance == expected_outgoing ) is
therefore only sound due to its reliance on the overflow checks on the environment.
The accumulator initializes at the incoming amount, then adds each spent UTXO's amount and subtracts
each created amount with raw operators, before the equality check:

`modules/utxo-core/src/core.rs` lines 95-141 (at `d65780b`):

```rust
Store::apply(e, |store| {
    for spend_utxo in bundle.spend.iter() {
        let amount = match store.balance(&spend_utxo) {
            a if a > 0 => a,
            0 => panic_with_error!(e, MoonlightError::UtxoAlreadySpent),
            _ => panic_with_error!(e, MoonlightError::UtxoDoesNotExist),
        };

          store.spend(&spend_utxo);
          total_available_balance += amount;

          #[cfg(not(feature = "no-utxo-events"))]
          UtxoEvent {
              name: symbol_short!("utxo"),
              utxo: spend_utxo.clone(),
// ... trimmed; see the authoritative PDF
```

Contrast this with pre_process_channel_operation in the privacy channel, which already sums external
amounts defensively with checked_add and a dedicated AmountOverflow error:

`contracts/privacy-channel/src/transact.rs` lines 41-58 (at `d65780b`):

```rust
let mut total_deposit: i128 = 0;
for (_addr, amt, _conds) in op.deposit.iter() {
    // MOON-05: reject non-positive amounts in-contract rather than relying on the asset SAC.
    assert_with_error!(&e, amt > 0, Error::InvalidExternalAmount);
    total_deposit = match total_deposit.checked_add(amt) {
        Some(v) => v,
        None => panic_with_error!(&e, Error::AmountOverflow),
    };
}

let mut total_withdraw: i128 = 0;
for (_addr, amt, _conds) in op.withdraw.iter() {
    assert_with_error!(&e, amt > 0, Error::InvalidExternalAmount);
    total_withdraw = match total_withdraw.checked_add(amt) {
        Some(v) => v,
// ... trimmed; see the authoritative PDF
```

With the environment specification of overflow checks, an overflow/underflow panics and reverts the
transaction, so conservation holds, and this is not exploitable as shipped. The concern is one of robustness
and locality of reasoning, and it is sharper because utxo-core is a reusable library. process_bundle is
exposed for arbitrary integrating contracts, and a consumer that compiles it under a profile under different
circumstances would silently reintroduce wrap-around arithmetic on the protocol's central invariant. A core
safety property of a shared module should not depend on the build configuration of the linker. Reaching the
overflow boundary also requires amounts near i128::MAX , which is not approachable with a legitimately
funded channel, unless we consider tokens with custom, abnormally large decimals.

**Impact.**

process_bundle maintains its running conservation total, total_available_balance , with unchecked
+= / -= operators, rather than the checked_add / checked_sub pattern used elsewhere in the same flow.
The invariant that guards value conservation ( total_available_balance == expected_outgoing ) is
therefore only sound due to its reliance on the overflow checks on the environment.
The accumulator initializes at the incoming amount, then adds each spent UTXO's amount and subtracts
each created amount with raw operators, before the equality check:

**Proof / attack path.**

null

**Recommendation.**

Replace the raw += / -= on total_available_balance with checked_add / checked_sub , mapping
failure to the existing AmountOverflow / AmountUnderflow errors, mirroring the deposit/withdraw

summation in pre_process_channel_operation . This makes conservation correct-by-construction
regardless of the compiling profile and removes the implicit dependency on overflow-checks for a
security-critical invariant. It also standardizes the approaches to mathematical operations in the contract.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/39 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/12a5280) by replacing the accumulator's raw += / -= with
checked_add/checked_sub, mapping failure to the existing AmountOverflow / AmountUnderflow errors as
recommended.

---

### [MOONLIGHT-RV-006] hash_payload Doc Specifies the Wrong Integer Width (8 vs 16 bytes)

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative (Recommended Action: Document Prominently) (source: B3) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | state-archival-ttl |
| **Location** | `modules/primitives/src/lib.rs:L115`, `modules/primitives/src/lib.rs:L129-L151` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/97922db |
| **Redacted** | false |

**Description.**

The hash_payload docstring states that "all integer amounts are encoded as little-endian 8-byte
sequences," but amounts are i128 , and the implementation appends amount.to_le_bytes() , which is 16
bytes.
Docstring:

`modules/primitives/src/lib.rs` line 115 (at `d65780b`):

```rust
/// For consistency, all integer amounts are encoded as little-endian 8-byte sequences.
```

Encoding that contradicts it using i128::to_le_bytes:

`modules/primitives/src/lib.rs` lines 129-151 (at `d65780b`):

```rust
for cond in auth_payload.conditions.iter() {
    match cond {
        Condition::Create(utxo, amount) => {
            b_create.append(&Bytes::from_slice(&e, utxo.to_array().as_ref()));
            b_create.append(&Bytes::from_slice(&e, &amount.to_le_bytes()));
        }
        Condition::ExtDeposit(addr, amount) => {
            b_deposit.append(&addr.to_string().to_bytes());
            b_deposit.append(&Bytes::from_slice(&e, &amount.to_le_bytes()));
        }
        Condition::ExtWithdraw(addr, amount) => {
            b_withdraw.append(&addr.to_string().to_bytes());
            b_withdraw.append(&Bytes::from_slice(&e, &amount.to_le_bytes()));
        }
        Condition::ExtIntegration(adapter, utxos, amount) => {
// ... trimmed; see the authoritative PDF
```

This is a documentation-only defect with no on-chain security impact, as the contract hashes 16-byte
amounts and verifies against 16-byte amounts, so it is internally consistent. The failure mode is a fail-safe.
An off-chain signer built to the documented 8-byte format computes a non-matching hash, and its signatures
are simply rejected by the verifier (no unauthorized action, no stuck state). The real cost is
developer/integration confusion for anyone treating the prose as the canonical serialization spec.
Two sibling errors live in the same docstring and should be corrected together:
1. The contract address is described as "(32 bytes)" when it is the ~56-byte strkey string, and;
2. The note suggesting conditions be kept "in the same ordering as the original bundle" is misleading,
since the implementation buckets conditions by type.

**Impact.**

The hash_payload docstring states that "all integer amounts are encoded as little-endian 8-byte
sequences," but amounts are i128 , and the implementation appends amount.to_le_bytes() , which is 16
bytes.
Docstring:

**Proof / attack path.**

This is a documentation-only defect with no on-chain security impact, as the contract hashes 16-byte
amounts and verifies against 16-byte amounts, so it is internally consistent. The failure mode is a fail-safe.
An off-chain signer built to the documented 8-byte format computes a non-matching hash, and its signatures
are simply rejected by the verifier (no unauthorized action, no stuck state). The real cost is
developer/integration confusion for anyone treating the prose as the canonical serialization spec.
Two sibling errors live in the same docstring and should be corrected together:
1. The contract address is described as "(32 bytes)" when it is the ~56-byte strkey string, and;
2. The note suggesting conditions be kept "in the same ordering as the original bundle" is misleading,
since the implementation buckets conditions by type.

**Recommendation.**

Correct the amount width (8 to 16 bytes), and fix the sibling contract-address and ordering statements in the
same pass. Preferably, replace hand-counted byte widths with a precise field-by-field serialization

description and commit signed test vectors as the authoritative reference, so off-chain signers verify against
fixtures rather than prose.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/38 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/97922db), where all three docstring errors were corrected. The rewritten
docstring accurately describes the new XDR-based encoding.

---

### [MOONLIGHT-RV-007] Redundant Reentrancy Guard

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative (Recommended Action: Fix Code) (source: B4) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | cross-contract-trust |
| **Location** | `contracts/privacy-channel/src/contract.rs:L39-L54`, `contracts/privacy-channel/src/contract.rs:L107-L119` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/7d24257 |
| **Redacted** | false |

**Description.**

transact wraps its body in a temporary-storage reentrancy guard, where enter_reentrancy_guard sets
a flag on entry and panics with ReentrantCall if it is already set, and exit_reentrancy_guard clears it on
exit.

`contracts/privacy-channel/src/contract.rs` lines 39-54 (at `d65780b`):

```rust
// MOON-06: reentrancy guard. `transact` makes external SAC calls (deposit pull / withdraw push);
// a non-standard or malicious asset could call back into `transact`. The guard is a transient flag
// that is set on entry and cleared on exit; a re-entrant call observes it and reverts. (On revert
// the transient write is rolled back, so the flag never persists across transactions.)
const REENTRANCY_GUARD: Symbol = symbol_short!("RGUARD");

fn enter_reentrancy_guard(e: &Env) {
    if e.storage().temporary().has(&REENTRANCY_GUARD) {
        panic_with_error!(e, Error::ReentrantCall);
    }
    e.storage().temporary().set(&REENTRANCY_GUARD, &true);
}

fn exit_reentrancy_guard(e: &Env) {
    e.storage().temporary().remove(&REENTRANCY_GUARD);
// ... trimmed; see the authoritative PDF
```

`contracts/privacy-channel/src/contract.rs` lines 107-119 (at `d65780b`):

```rust
pub fn transact(e: Env, op: ChannelOperation) {
    bump_instance_ttl(&e);
    enter_reentrancy_guard(&e);

    let (utxo_op, total_deposit, total_withdraw) =
        pre_process_channel_operation(&e, op.clone());

    Self::process_bundle(&e, utxo_op.clone(), total_deposit, total_withdraw);

    execute_external_operations(&e, op.deposit, op.withdraw);

    exit_reentrancy_guard(&e);
}
```

Soroban prohibits reentrancy at the host level, meaning that a contract currently in the call stack cannot be
re-entered. The exact scenario the guard targets (a non-standard or malicious asset calling back into
transact during the external deposit / withdraw transfers) is therefore already rejected by the runtime.
The guard is redundant with that platform guarantee, as the host rule already covers every entrypoint (not
just transact ). Additionally, the flag takes no effect for cross-contract cases (a call into a different channel
is not reentrancy of this one and would not observe this contract's guard). This is not a vulnerability, and the
cost is minor: two temporary-storage writes per transact , plus the extra code path and ReentrantCall
error.

**Impact.**

transact wraps its body in a temporary-storage reentrancy guard, where enter_reentrancy_guard sets
a flag on entry and panics with ReentrantCall if it is already set, and exit_reentrancy_guard clears it on
exit.

**Proof / attack path.**

null

**Recommendation.**

Optionally, remove the guard and the ReentrantCall error, replacing it with a comment noting that
reentrancy is prevented by Soroban's host-level non-reentrancy. If the team prefers to keep it as explicit
defense-in-depth, document that the primary protection is the platform guarantee and the guard is
secondary, and do not treat it as a load-bearing control. Either way, since the redundancy depends on the
host guarantee, re-validate that non-reentrancy semantics hold for the target protocol version on any
SDK/protocol upgrade.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/41 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/7d24257) by removing the redundant reentrancy guard and its
ReentrantCall error, as recommended.

---

### [MOONLIGHT-RV-008] Fragmented and Partially Duplicated Validation Across the Transact Flow

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative (Recommended Action: Fix Code) (source: B5) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | code-quality |
| **Location** | `modules/utxo-core/src/core.rs:L95-L141`, `modules/storage/src/lib.rs:L74-L116` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/7374602 |
| **Redacted** | false |

**Description.**

Validation of a transact bundle is distributed across four crates with no single structural-validation layer:
primitives - reusable predicates: condition checks ( conflicts_with , equal_condition_sequence )
and operation-identifier deduplication ( no_duplicate_keys over UTXO keys,
no_duplicate_addresses over addresses).
privacy-channel ( transact.rs ) - bundle orchestration and higher-level checks:
op_has_no_conflicting_conditions , verify_external_operations , the amount-positivity loops,
and assert_signed_effects_are_executed .
utxo-core ( process_bundle ) - per-UTXO deduplication and state pre-checks.
storage ( Store ) - per-UTXO existence, spent-state, and positivity enforcement.

Beyond being spread out, per-UTXO validation is duplicated between the last two layers, with redundant
storage reads. For spend , process_bundle calls store.balance() to verify the UTXO is unspent and
obtain its amount, then store.spend() re-reads and re-checks the same state, and its returned amount
(the same value) is discarded. For create , process_bundle checks balance() != -1 and amount > 0 ,
then store.create() re-checks existence and positivity.

`modules/utxo-core/src/core.rs` lines 95-141 (at `d65780b`):

```rust
        Store::apply(e, |store| {
            for spend_utxo in bundle.spend.iter() {
                let amount = match store.balance(&spend_utxo) {
                    a if a > 0 => a,
                    0 => panic_with_error!(e, MoonlightError::UtxoAlreadySpent),
                    _ => panic_with_error!(e, MoonlightError::UtxoDoesNotExist),
                };

                  store.spend(&spend_utxo);
                  total_available_balance += amount;

                  #[cfg(not(feature = "no-utxo-events"))]
                  UtxoEvent {
                      name: symbol_short!("utxo"),
                      utxo: spend_utxo.clone(),
// ... trimmed; see the authoritative PDF
```

`modules/storage/src/lib.rs` lines 74-116 (at `d65780b`):

```rust
 /// Creates a new unspent UTXO with the provided amount.
 ///
 /// # Panics
 ///
 /// Panics if the amount is not positive or if a record already exists for
 /// the UTXO key (including a spent record, which can never be recreated).
 pub fn create(&mut self, utxo65: &BytesN<65>, amount: i128) {
     if amount <= 0 {
         panic_with_error!(&self.env, Error::InvalidCreateAmount);
     }

     let k = self.utxo_key(utxo65);

     if self.env.storage().persistent().get::<_, i128>(&k).is_some() {
         panic_with_error!(&self.env, Error::UtxoAlreadyExists);
// ... trimmed; see the authoritative PDF
```

Amount positivity alone is enforced in three separate places (create in process_bundle , create in
Store::create , and deposit/withdraw in pre_process_channel_operation ). There is no security impact
(behavior is correct), but the same invariants must be tracked across multiple layers, which raises the
maintenance and implementation cost, and the repeated reads add minor per-UTXO gas.

**Impact.**

Validation of a transact bundle is distributed across four crates with no single structural-validation layer:
primitives - reusable predicates: condition checks ( conflicts_with , equal_condition_sequence )
and operation-identifier deduplication ( no_duplicate_keys over UTXO keys,
no_duplicate_addresses over addresses).
privacy-channel ( transact.rs ) - bundle orchestration and higher-level checks:
op_has_no_conflicting_conditions , verify_external_operations , the amount-positivity loops,
and assert_signed_effects_are_executed .
utxo-core ( process_bundle ) - per-UTXO deduplication and state pre-checks.
storage ( Store ) - per-UTXO existence, spent-state, and positivity enforcement.

**Proof / attack path.**

null

**Recommendation.**

Establish a single source of truth for per-UTXO validation, and either let Store::create/spend be the sole
enforcers and drop the pre-checks in process_bundle (which already delegates to the store), or make the
store methods unchecked and validate only in process_bundle . Either choice removes the double read
and double check. Additionally, group the bundle's structural checks (conflict, deduplication, sequence-
equality, positivity) behind one clearly-named validation step so the invariants are enforced and discoverable
in one place.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/43 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/7374602) by consolidating the bundle-level validation into a single validator.

---

### [MOONLIGHT-RV-009] Provider signature deadline is not provider- signed and enforced only against cooperative submitters

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative (Recommended Action: Document Prominently) (source: B6) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | cryptography |
| **Location** | `modules/auth/src/core.rs:L215-L222` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/cc765e7 |
| **Redacted** | false |

<!-- CONVERSION-NOTE: code excerpts from stellar/rs-soroban-env (outside the audited repo) left out of Location -->

**Description.**

The provider check rejects a Provider entry whose valid_until_ledger is below the current ledger, but
that field is not covered by any provider signature:

`modules/auth/src/core.rs` lines 215-222 (at `d65780b`):

```rust
let (sig_variant, valid_until_ledger) =
    sig_map.get(signer.clone()).ok_or(Error::MissingSignature)?;

if valid_until_ledger < e.ledger().sequence() {
    return Err(Error::SignatureExpired);
}

verify_signature(&e, &signer, &sig_variant, &payload)?;
```

The provider signs only payload (the host authorization payload). The valid_until_ledger paired with it
in the Signatures map is attached by the transaction submitter, who can set any value. So this check
constrains only a submitter acting against its own interest: it cannot enforce a deadline the provider chose.
(A P256 entry differs, as there the deadline is bound into the signed message.)
Neither direction has security impact. Expiry and replay protection for provider signatures are enforced
separately, at the host layer: the entry's signature_expiration_ledger is part of the signed authorization
preimage,

`soroban-env-host/src/auth.rs` lines 2030-2048 (at `cf58d53`):

```rust
fn get_signature_payload(&self, host: &Host) -> Result<[u8; 32], HostError> {
    let (nonce, live_until_ledger) = self.nonce.ok_or_else(|| {
        host.err(
            ScErrorType::Auth,
            ScErrorCode::InternalError,
            "unexpected missing nonce",
            &[],
        )
    })?;
    let payload_preimage =
        HashIdPreimage::SorobanAuthorization(HashIdPreimageSorobanAuthorization {
            network_id: Hash(host.with_ledger_info(|li| li.network_id.metered_clone(host))?),
            nonce,
            signature_expiration_ledger: live_until_ledger,
            invocation: self.root_invocation_to_xdr(host)?,
// ... trimmed; see the authoritative PDF
```

and the host checks it and consumes the entry's nonce before the contract runs:

`soroban-env-host/src/auth.rs` lines 1985-2015 (at `cf58d53`):

```rust
fn verify_and_consume_nonce(&mut self, host: &Host) -> Result<(), HostError> {
    if self.is_transaction_source_account {
        return Ok(());
    }
    if let Some((nonce, live_until_ledger)) = &self.nonce {
        let ledger_seq = host.with_ledger_info(|li| Ok(li.sequence_number))?;
        if ledger_seq > *live_until_ledger {
            return Err(host.err(
                ScErrorType::Auth,
                ScErrorCode::InvalidInput,
                "signature has expired",
                &[
                    self.address.into(),
                    ledger_seq.try_into_val(host)?,
                    live_until_ledger.try_into_val(host)?,
// ... trimmed; see the authoritative PDF
```

So a submitter-inflated valid_until_ledger cannot extend a provider signature's life past the host-
enforced, provider-signed expiry, and a deflated one only dooms the submitter's own transaction.
The contract-level field is therefore a second deadline that no provider signature covers, distinct from the
host-enforced one. The residual concern is misreading: an integrator could take the in-contract check for the
operative expiry control and reason about provider-signature lifetime from the wrong field.

**Impact.**

So a submitter-inflated valid_until_ledger cannot extend a provider signature's life past the host-
enforced, provider-signed expiry, and a deflated one only dooms the submitter's own transaction.
The contract-level field is therefore a second deadline that no provider signature covers, distinct from the
host-enforced one. The residual concern is misreading: an integrator could take the in-contract check for the
operative expiry control and reason about provider-signature lifetime from the wrong field.

**Proof / attack path.**

null

**Recommendation.**

Document at the check that this field is submitter-supplied and that the enforced provider deadline lives at
the host layer over the signed authorization preimage, so no reader mistakes it for a binding control. If a
provider-chosen contract-level deadline is in fact wanted, bind valid_until_ledger into the provider's
signed message (as the P256 path already does for its own deadline); the check then enforces a deadline
the provider actually chose rather than one the submitter supplies.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/47 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/cc765e7) by documenting that valid_until_ledger is submitter-supplied
and non-binding.

---

### [MOONLIGHT-RV-010] Provider registration accepts addresses the provider check can never match

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative (Recommended Action: Fix Code) (source: B7) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | cryptography |
| **Location** | `contracts/channel-auth/src/contract.rs:L112-L117`, `modules/auth/src/core.rs:L206-L214`, `modules/helpers/src/parser.rs:L4-L9` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/cc765e7 |
| **Redacted** | false |

**Description.**

ChannelAuthContract.add_provider stores any Address in the provider registry without validating its
kind:

`contracts/channel-auth/src/contract.rs` lines 112-117 (at `d65780b`):

```rust
pub fn add_provider(e: &Env, provider: Address) {
    ownable::enforce_owner_auth(e);
    let addr = provider.clone();
    Self::register_provider(e, provider);
    ProviderAdded { provider: addr }.publish(e);
}
```

The provider check of __check_auth , however, never looks up the registered address as submitted. For
each Provider -keyed signature it derives a Stellar account address from the signer key's Ed25519 public
key and matches the derived address against the registry:

`modules/auth/src/core.rs` lines 206-214 (at `d65780b`):

```rust
for signer in sig_map.keys().iter() {
    if let SignerKey::Provider(pk32) = signer.clone() {
        let provider_addr: Address = address_from_ed25519_pk_bytes(&e, &pk32);

        assert_with_error!(
            e,
            Self::is_provider(&e, provider_addr.clone()),
            Error::ProviderNotRegistered
        );
```

`modules/helpers/src/parser.rs` lines 4-9 (at `d65780b`):

```rust
pub fn address_from_ed25519_pk_bytes(e: &Env, provider_pk32: &BytesN<32>) -> Address {
    Address::from_payload(
        e,
        AddressPayload::AccountIdPublicKeyEd25519(provider_pk32.clone()),
    )
}
```

Since SignerKey::Provider carries a raw Ed25519 public key, only Ed25519 account addresses can ever
match. Any other address — a contract address, for instance — is accepted by add_provider and reported
as registered by is_provider , but the entry grants nothing, and both calls succeed without indication.
Provider-gated calls then fail with ProviderNotRegistered until the correct account address is registered.

**Impact.**

Since SignerKey::Provider carries a raw Ed25519 public key, only Ed25519 account addresses can ever
match. Any other address — a contract address, for instance — is accepted by add_provider and reported
as registered by is_provider , but the entry grants nothing, and both calls succeed without indication.
Provider-gated calls then fail with ProviderNotRegistered until the correct account address is registered.

**Proof / attack path.**

null

**Recommendation.**

Validate the address kind at registration, so add_provider rejects any address the provider check cannot
match. The address_to_ed25519_pk_bytes helper already performs exactly this discrimination, panicking
with NotEd25519AccountAddress on a contract address:

`modules/helpers/src/parser.rs` lines 11-19 (at `d65780b`):

```rust
pub fn address_to_ed25519_pk_bytes(e: &Env, addr: &Address) -> BytesN<32> {
    match addr.to_payload() {
        Some(AddressPayload::AccountIdPublicKeyEd25519(provider_pk32)) => provider_pk32,
        Some(AddressPayload::ContractIdHash(_)) => {
            panic_with_error!(e, MoonlightError::NotEd25519AccountAddress)
        }
        None => panic_with_error!(e, MoonlightError::UnsupportedAddressPayload),
    }
}
```

Alternatively, since registration is owner-only and recoverable through remove_provider , this can be
documented as an operational constraint: add_provider accepts only the Ed25519 account address of a
provider signing key, and an entry reported by is_provider does not imply it can authorize.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/47 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/cc765e7) by validating the address kind in add_provider .

---

### [MOONLIGHT-RV-011] Argument-less authorization contexts are gated by the provider check alone

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative (Recommended Action: Document Prominently) (source: B8) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | access-control-auth |
| **Location** | `modules/auth/src/core.rs:L80-L90`, `modules/utxo-core/src/core.rs:L87-L93` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/cc765e7 |
| **Redacted** | false |

**Description.**

The UTXO check of ChannelAuthContract.__check_auth skips every authorization context that carries no
arguments, inspecting neither the invoked contract nor the invoked function:

`modules/auth/src/core.rs` lines 80-90 (at `d65780b`):

```rust
for c in contexts.iter() {
    if let Context::Contract(cc) = c {
        let sig_map = signatures.0.clone();

        if cc.args.len() < 1 {
            // MOON-03: a context with no auth-requirements arg carries no UTXO
            // requirements, but it must only skip THIS context — never short-circuit the
            // whole check. A `return Ok(())` here would let an empty-args context that
            // precedes a spend-bearing context bypass the latter's P256 verification.
            continue;
        }
```

A skipped context reaches no operation-binding check, so the provider check — one registered provider
signature — is its only gate.
The skip is deliberate. As the MOON-03 comment records, it must continue rather than return Ok(()) ,
or an argument-less context preceding a spend-bearing one would bypass the latter's P256 verification. And
the shape legitimately occurs: on spend-free bundles the channel requests authorization from this account
with an empty argument vector:

`modules/utxo-core/src/core.rs` lines 87-93 (at `d65780b`):

```rust
let auth_args = if bundle.req.0.is_empty() {
    vec![&e]
} else {
    vec![&e, bundle.req.clone().into_val(e)]
};

Self::auth(&e).require_auth_for_args(auth_args);
```

For that intended case the single-provider gate is the intended authorization: such a bundle carries no P256
spend requirements, and the balance check, depositor authorizations, and signed-effects binding constrain
the rest.
It becomes an issue only if this account authorizes anything else: a zero-argument entrypoint of another
contract gated on it is approved by one provider signature, with the owner and every P256 holder
uninvolved. Each approval still requires a fresh provider signature over the host payload, which commits to
the specific invocation, a nonce, and an expiration — so the exposure is a lowered signing threshold, not an
open gate.

**Impact.**

The UTXO check of ChannelAuthContract.__check_auth skips every authorization context that carries no
arguments, inspecting neither the invoked contract nor the invoked function:

**Proof / attack path.**

null

**Recommendation.**

Document the constraint: this account should be named as authorizer only where a single-provider gate on
an argument-less invocation is acceptable, the channel's spend-free path being the intended case.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/47 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/cc765e7) by documenting the constraint.

---

### [MOONLIGHT-RV-012] P256 signatures verified by the UTXO check carry no replay protection

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative (Recommended Action: Document Prominently) (source: B9) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | cryptography |
| **Location** | `modules/auth/src/core.rs:L107-L127`, `modules/storage/src/lib.rs:L104-L116` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/cc765e7 |
| **Redacted** | false |

**Description.**

The UTXO check of ChannelAuthContract.__check_auth verifies a P256 signature against a message
binding the condition list, the entry's valid_until_ledger , and the requesting contract, and consumes
nothing:

`modules/auth/src/core.rs` lines 107-127 (at `d65780b`):

```rust
match signer.clone() {
    SignerKey::P256(_signer_pk) => {
        // Lookup signature by key.

       let (sig_variant, valid_until_ledger) =
           sig_map.get(signer.clone()).ok_or(Error::MissingSignature)?;

       if valid_until_ledger < e.ledger().sequence() {
           return Err(Error::SignatureExpired);
       }

       let auth_payload = AuthPayload {
           conditions: conds,
           live_until_ledger: valid_until_ledger,
       };
// ... trimmed; see the authoritative PDF
```

An unexpired P256 entry of signatures therefore re-verifies identically in every authorization until its
deadline passes. The host nonce does not close this: it is consumed per authorization entry, and a submitter
can wrap the same P256 signature in a fresh entry with a fresh nonce and provider countersignature. Reuse
is confined to the requesting contract and condition list the signed message binds, and to the signer-chosen
deadline window.

Under the documented wiring this is not exploitable, because the channel supplies single-use itself. The
signer key is the UTXO key; a settled spend tombstones its entry in place (amount zeroed, TTL refreshed),
and a later bundle spending that key fails:

`modules/storage/src/lib.rs` lines 104-116 (at `d65780b`):

```rust
pub fn spend(&mut self, utxo65: &BytesN<65>) -> i128 {
    let k = self.utxo_key(utxo65);
    match self.env.storage().persistent().get::<_, i128>(&k) {
        Some(amount) if amount > 0 => {
            self.env.storage().persistent().set(&k, &0i128);
            // Keep the spent record alive so the UTXO cannot be recreated after archival.
            self.bump_ttl(&k);
            amount
        }
        Some(_) => panic_with_error!(&self.env, Error::UtxoAlreadySpent),
        None => panic_with_error!(&self.env, Error::UtxoDoesNotExist),
    }
}
```

So a P256 signature that has settled once can never authorize a second spend of the same UTXO, and the
reusability of the check never surfaces.
The single-use guarantee, however, lives entirely in the requesting contract, not in __check_auth . For any
other contract naming this account as authorizer, an unexpired P256 signature authorizes unboundedly
many invocations within its deadline window — each still requiring a provider countersignature — unless
that contract enforces its own single-use.

**Impact.**

So a P256 signature that has settled once can never authorize a second spend of the same UTXO, and the
reusability of the check never surfaces.
The single-use guarantee, however, lives entirely in the requesting contract, not in __check_auth . For any
other contract naming this account as authorizer, an unexpired P256 signature authorizes unboundedly
many invocations within its deadline window — each still requiring a provider countersignature — unless
that contract enforces its own single-use.

**Proof / attack path.**

null

**Recommendation.**

No change is required for the paired channel: the tombstone is a complete single-use mechanism, and it is
the property the system's safety rests on here. Document that __check_auth provides no replay protection
of its own for P256 entries, so any contract naming this account as authorizer must supply its own single-
use (as the channel does through the UTXO tombstone) or bound the reuse another way.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/47 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/cc765e7) by documenting the constraint.

---

### [MOONLIGHT-RV-013] Deposit amounts are not authorized at the channel, only by the asset transfer

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative (Recommended Action: Document Prominently) (source: B10) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | access-control-auth |
| **Location** | `contracts/privacy-channel/src/transact.rs:L203-L207` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/0d59e24 |
| **Redacted** | false |

**Description.**

A deposit entry (from, amount, conditions) splits the depositor's consent across two authorizations. The
channel requires from to authorize only [conditions] ; the amount appears solely in the immediately
following transfer(from, contract, amount) and is covered only by the asset's transfer authorization:

`contracts/privacy-channel/src/transact.rs` lines 203-207 (at `d65780b`):

```rust
for (from, amount, deposit_conditions) in deposit.iter() {
    from.require_auth_for_args(vec![&e, deposit_conditions.into_val(e)]);
    asset_client.transfer(&from, &e.current_contract_address(), &amount);
    increase_supply(&e, amount);
}
```

Under the documented wiring this is sound. The trust model pins the asset to a Stellar Asset Contract and
trusts it to enforce its transfer semantics, and an SAC's transfer requires from to authorize the amount:
Failed to load
It becomes an issue only under an asset that moves value without requiring the authorization of from .
Nothing at the channel then binds the amount to anything the depositor signed: a composer holding a
signed conditions context can pair it with any amount, the channel check passes, the signed conditions
execute, and the value above them becomes unsigned residual the composer allocates. (An ExtDeposit
condition can carry an amount, but nothing compares it to the tuple's amount .)

**Impact.**

Under the documented wiring this is sound. The trust model pins the asset to a Stellar Asset Contract and
trusts it to enforce its transfer semantics, and an SAC's transfer requires from to authorize the amount:
Failed to load
It becomes an issue only under an asset that moves value without requiring the authorization of from .
Nothing at the channel then binds the amount to anything the depositor signed: a composer holding a
signed conditions context can pair it with any amount, the channel check passes, the signed conditions
execute, and the value above them becomes unsigned residual the composer allocates. (An ExtDeposit
condition can carry an amount, but nothing compares it to the tuple's amount .)

**Proof / attack path.**

null

**Recommendation.**

Bind the amount into the depositor's channel authorization. It is in scope at the require_auth_for_args
call site; pass it alongside conditions (or as a struct carrying both). This is a small, local change that
makes the depositor's amount consent rest on the channel's own guarantee regardless of the asset's
authorization behavior. It is defense-in-depth, not a correctness fix: under a compliant asset the amount is
simply authorized twice, and value conservation still rests on the asset trust assumption, so asset vetting
remains necessary for other reasons.
Alternatively, leave the amount consent with the asset and document the constraint: an asset that transfers
without requiring from 's authorization must not be used as a channel asset.

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/46 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/0d59e24) by documenting the constraint.

---

### [MOONLIGHT-RV-014] Withdrawals to the channel's own address burn claims without moving tokens

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative (Recommended Action: Fix Code) (source: B11) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | state-archival-ttl |
| **Location** | `contracts/privacy-channel/src/transact.rs:L209-L230` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/0d59e24 |
| **Redacted** | false |

**Description.**

No path of transact compares a withdrawal recipient against the channel's own address. The withdraw
loop transfers to to and decrements Supply , whatever to is:

`contracts/privacy-channel/src/transact.rs` lines 209-230 (at `d65780b`):

```rust
for (to, amount, _) in withdraw.iter() {
    let args_val: Vec<Val> = vec![
        e,
        (&e.current_contract_address()).into_val(e),
        (&to).into_val(e),
        (&amount).into_val(e),
    ];

     e.authorize_as_current_contract(vec![
         &e,
         InvokerContractAuthEntry::Contract(SubContractInvocation {
             context: ContractContext {
                 contract: asset.clone(),
                 fn_name: Symbol::new(e, "transfer"),
                 args: args_val.clone(),
// ... trimmed; see the authoritative PDF
```

A withdraw naming the channel itself thus executes as transfer(contract, contract, amount) — net-
zero under a compliant asset — while Supply still decreases by amount , which the bundle balance still
requires be funded by spends or deposits. Claims burn without tokens moving; afterwards the channel's
token balance exceeds Supply by amount .
The surplus is unreachable in the contract as deployed: the withdraw loop is the only outbound-transfer site,
no allowance is ever granted, and every payout is coupled to an equal reduction of claims. Tokens sent to

the channel directly through the asset, outside transact , produce the same unreachable surplus. In either
case the surplus is recoverable only by an admin-driven contract upgrade, which inherits the balance and
could sweep or re-account it.

**Impact.**

the channel directly through the asset, outside transact , produce the same unreachable surplus. In either
case the surplus is recoverable only by an admin-driven contract upgrade, which inherits the balance and
could sweep or re-account it.

**Proof / attack path.**

null

**Recommendation.**

Reject a withdrawal naming the channel's own address — check to != e.current_contract_address() in
the withdraw loop or in verify_external_operations — failing the bundle. This closes the in-band path at
one site.
The direct-transfer variant cannot be prevented by the contract. The surplus it creates is inert — never
payable out in deployed code — so it is at most a donation the admin can eventually recover, needing no
handling beyond awareness that the token balance may exceed Supply .

**Remediation notes.**

Fixed in https://github.com/Moonlight-Protocol/soroban-core/pull/46 (head at https://github.com/Moonlight-Protocol/soroban-core/commit/0d59e24) by rejecting any withdrawal naming the channel's own address in
verify_external_operations ( WithdrawToChannelAddress ).

---

### [MOONLIGHT-RV-015] enable_channel / disable_channel are event-only

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informative (Recommended Action: Fix Code) (source: B12) |
| **Difficulty / likelihood** | null |
| **Status** | Acknowledged |
| **Remediation verified by** | not-reviewed |
| **Category** | observability |
| **Location** | `contracts/channel-auth/src/contract.rs:L135-L155`, `contracts/privacy-channel/src/contract.rs:L107-L119` |
| **Resolved in** | https://github.com/Moonlight-Protocol/soroban-core/commit/32d929e |
| **Redacted** | false |

<!-- CONVERSION-NOTE: remediation PR or commit present on a finding marked Acknowledged; confirm status -->

**Description.**

disable_channel (and enable_channel ) only emit ChannelStateChanged ; they write no state:

`contracts/channel-auth/src/contract.rs` lines 135-155 (at `d65780b`):

```rust
pub fn enable_channel(e: &Env, channel: Address, asset: Address) {
    ownable::enforce_owner_auth(e);
    ChannelStateChanged {
        channel,
        asset,
        enabled: true,
    }
    .publish(e);
}

/// Disable an asset `channel`. The channel becomes withdraw-only (new deposits/sends rejected);
/// that enforcement lives provider-side. Emits `ChannelStateChanged { enabled: false }`.
pub fn disable_channel(e: &Env, channel: Address, asset: Address) {
    ownable::enforce_owner_auth(e);
    ChannelStateChanged {
// ... trimmed; see the authoritative PDF
```

transact never reads any enabled/disabled flag, so a "disabled" channel keeps accepting deposits,
transfers, and withdrawals on-chain:

`contracts/privacy-channel/src/contract.rs` lines 107-119 (at `d65780b`):

```rust
pub fn transact(e: Env, op: ChannelOperation) {
    bump_instance_ttl(&e);
    enter_reentrancy_guard(&e);

    let (utxo_op, total_deposit, total_withdraw) =
        pre_process_channel_operation(&e, op.clone());

    Self::process_bundle(&e, utxo_op.clone(), total_deposit, total_withdraw);

    execute_external_operations(&e, op.deposit, op.withdraw);

    exit_reentrancy_guard(&e);
}
```

The disable is advisory, enforced off-chain by providers. Consequently, there is no on-chain way to halt a
channel in an incident (compromised asset, discovered bug, misbehaving provider). The only on-chain lever
is a full upgrade , which is itself the heaviest trust operation.

**Impact.**

disable_channel (and enable_channel ) only emit ChannelStateChanged ; they write no state:

**Proof / attack path.**

null

**Recommendation.**

If an on-chain halt is desired, add an owner-settable enabled flag in the channel and check it in transact
(at minimum gating deposits and transfers, leaving withdrawals open for exit). Otherwise, document
explicitly that channel disabling is advisory/off-chain only and that upgrade is the sole on-chain stop.

**Remediation notes.**

The client has acknowledged this finding. Still, in https://github.com/Moonlight-Protocol/soroban-core/pull/48
(head at https://github.com/Moonlight-Protocol/soroban-core/commit/32d929e), the project now documents
its design decision to keep disable_channel and enable_channel event-only operations.

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

The following invariants capture the properties that must hold for the Moonlight contracts (Privacy Channel
and Channel Auth) to behave correctly and safely. Each is a condition the protocol is expected to preserve
at all times, regardless of the order or combination of operations, and together they define the boundary
between intended behavior and a potential vulnerability. They are organized by domain and serve as the
reference against which the code is reviewed. Any execution path that can violate one of these properties is
a finding.

#### A. Value conservation & supply

- I1 — Bundle conservation. For every transact :
  Σspent + Σdeposited == Σcreated + Σwithdrawn . Violation = minting or destroying channel value.
- I2 — Supply/UTXO consistency (global, inductive). At all times
  supply == Σ amounts of all unspent UTXOs .
- I3 — Asset backing. The channel's actual token balance ≥ supply . Holds only if the asset transfers
  exactly amount (see T1). Violation = withdrawals become insolvent.
- I4 — Strict positivity. Every UTXO amount > 0. Violation = negative-amount inversion of supply
  accounting.
- I5 — Supply non-negativity (derived). At all times supply >= 0 .
- I6 — Overflow safety. Mathematical operations should never overflow.

#### B. UTXO state machine

- I7 — One-way lifecycle. absent -> unspent(>0) -> spent(0) , no backward transitions.
- I8 — No double-spend. A UTXO's amount is credited to a bundle at most once.
- I9 — No intra-bundle duplicates. A key appears at most once in the spend set and once in the create
  set.
- I10 — Identifier permanence. A spent key can never be re-created (tombstone kept forever, TTL-
  bumped on spend).
- I11 — Identity injectivity. UTXO identity = SHA-256(pubkey65) .

#### C. Authorization

- I12 — Universal provider gate. Every __check_auth requires ≥ 1 registered, unexpired provider
  Ed25519 signature over the tx payload.
- I13 — Owner-bound spends. Every spent UTXO requires a valid P256 signature under that UTXO's
  key, over its exact condition list + live_until_ledger , domain-separated by the calling contract's
  address. Violation = theft of user funds.

- I14 — Effect binding (MOON-01). Every signed Create / ExtWithdraw condition is executed exactly
  (same key/address, same amount): authorized \<contains> executed by canonical XDR. Violation =
  provider redirects user value.
- I15 — Depositor consent. Every deposit executes from.require_auth_for_args(conditions)
  before pulling tokens. No one can be deposited-from involuntarily.
- I16 — Signature expiry. Any signature with valid_until_ledger \< current is rejected (both P256
  and provider paths). Sets a bounded replay window.
- I17 — No effective replay. A signed payload cannot be re-executed with effect: spends are blocked by
  the tombstone (I7/I8), re-creates by I7, and deposits by Soroban's own auth-nonce on the depositor's
  entry.
- I18 — Non-empty conditions. Every signer in the auth requirements carries ≥ 1 condition.
- I19 — Single egress path. Tokens leave the channel only through the withdraw branch of a conserved,
  authorized bundle.

#### D. Governance

- I20 — Owner-only privileged surface. upgrade , add_provider / remove_provider ,
  enable_channel / disable_channel , set_admin are all gated by ownable::enforce_owner_auth .
  Violation = full protocol takeover.
- I21 — Owner always exists. Set once in each constructor, renounce_ownership not exposed, and
  two-step transfer can never null it, so the privileged surface can't be orphaned or bricked.
- I22 — Two-step handover. A pending admin has zero authority until accept_admin under its own key;
  the incumbent retains control until acceptance; proposals expire.
- I23 — Immutable bindings. The channel's auth contract and asset are written only in the
  constructor — no runtime entrypoint can repoint them. Violation (e.g., re-exposing set_auth ) = total
  authorization bypass; this regressed once before (pre-MOON fix), so it deserves a regression test.

#### E. Execution discipline

- I24 — Non-reentrancy. transact cannot be re-entered, and neither is used in a two-part reentrancy
  design.
- I25 — State-before-interaction. All UTXO state transitions and the conservation check are complete
  before any external token call.
- I26 — Liveness maintenance. Every touch of a UTXO entry and every mutating entrypoint/auth check
  bumps the relevant TTL. Expiry can only ever produce archival (recoverable DoS), never silent data
  loss or state corruption, since nothing protocol-critical lives in temporary storage.

#### T. Trust assumptions (boundary conditions, not enforced)

- T1 — Standard asset. The SEP-41 asset transfers exactly amount , no fee-on-transfer/rebasing.
  Tokens with a custom design can be used with the consent of the privacy channel administrator.
- T2 — Provider honesty for privacy & liveness only. A malicious provider can censor or deanonymize
  (off-chain), but I12–I14 must prevent it from stealing or redirecting funds.
- T3 — Council multisig. The owner is a single Address on-chain. "Quorum" governance is a
  deployment assumption (T-of-N multisig), not contract-enforced.
- T4 — Key hygiene. P256 UTXO keys are generated fresh and never reused across channels.
- T5 — SDK panic semantics. secp256r1_verify / ed25519_verify trap on invalid signatures.

## 6. Methodology

Runtime Verification followed a structured methodology to evaluate the correctness and security of the
Moonlight core smart contracts within the agreed 2-week engagement, followed by 1-week remediation
period. Although manual review cannot guarantee the discovery of all vulnerabilities, our approach was
designed to maximize coverage and identify the most impactful risks within the available timeline.

Design Review and Role/Actor Mapping
The engagement began with documentation and scope intake, followed by a high-level design review of the
Moonlight protocol, focusing on the lifecycle of the channel-auth (Quorum Auth) contract and the privacy-
channel contract, and on how the two components interact during deposit, private-transfer, and withdrawal
operations.
The Moonlight contracts use a minimal authority model layered on explicit, signature-based authorization to
correctly execute their functionality and implement their business logic. Each actor is enabled with specific
capabilities in each contract, and the correct management of bounds for actions of each actor within the
protocol is crucial to its proper functioning. Aiming to validate this, we first built an understanding of the
actors available in each contract, including the Admin/Owner, Pending Admin, Privacy Provider, UTXO
owner, Depositor, Withdrawal recipient, and Transaction submitter.

Threat Analysis from the Design Review
Building on the role and invariant mapping, we conducted a dedicated threat analysis of the protocol. This
included generating invariants for each privileged operation and each signed condition (Create,
ExtWithdraw, deposit), running Almanax scans of the codebase using the context developed during the
design review, and evaluating financial and business-logic risk, with particular attention to the protocol's
conservation guarantees, the implications of compromised or misused provider and owner keys, and
dependencies on external inputs such as the provider registry and asset-channel lifecycle state.

Manual Code Review
After establishing the protocol model, we performed a line-by-line review of the Soroban Rust codebase,
covering both in-scope contracts. This included examining:

Correctness of the channel-auth contract's privileged operations, including provider registry
management, the asset-channel enable/disable lifecycle, and the two-step admin rotation mechanism;
Correctness of the channel-auth contract's 1-of-N provider signature threshold enforced via
require_provider, and its distinction from the owner-level governance quorum;
Correctness of the privacy-channel contract's UTXO lifecycle, including deposit, private-transfer, and
withdrawal flows, and the execution-binding of signed Create/ExtWithdraw conditions;
Soroban-specific concerns across both contracts, including storage layout, persistent and instance TTL
maintenance and refresh behavior, event emission, and the existing test suites;

Conservation accounting across spend/create/withdraw operations, and the reentrancy guard protecting
transact;
Authorization and permission boundaries across both contracts, verified against the role and trust
model identified during the design review;
Edge cases, boundary conditions, and potential state inconsistencies, including archived (TTL-lapsed)
UTXOs and the currently-unexecuted ExtIntegration condition variant.

Execution paths and state transitions were evaluated against the invariants identified earlier, including a final
invariant check based on the findings of the low-level code review, to ensure alignment between the
intended design and the implemented behavior.
Tool-Assisted Analysis

To supplement manual review, we incorporated targeted automated analysis using Almanax for AI-assisted
bug pattern detection and anomaly surfacing across the codebase, with findings analyzed and triaged
alongside the manual review results. Standard Rust tooling (including cargo audit, cargo outdated, and
cargo clippy) was additionally run over the codebase to surface dependency and code-quality issues.
Finally, we conducted rounds of internal discussions with security experts over the code and platform design
to verify possible exploitation vectors and identify improvements for the analyzed contracts.

Findings Consolidation and Reporting
In the final stage of the review, we consolidated all findings from the manual review, the threat analysis, and
the Almanax scans, revisited any pending notes raised during earlier phases, and proofread the resulting
report prior to delivery.

## 7. Disclaimer and license

This report does not constitute legal or investment advice. You understand and agree that this report relates
to new and emerging technologies and that there are significant risks inherent in using such technologies
that cannot be completely protected against. While this report has been prepared based on data and
information that has been provided by you or is otherwise publicly available, there are likely additional
unknown risks that otherwise exist. This report is also not comprehensive in scope, excluding a number of
components critical to the correct operation of this system. This report is for informational purposes only and
is provided on an "as-is" basis, and you acknowledge and agree that you are making use of this report and
the information contained herein at your own risk. The preparers of this report make no representations or
warranties of any kind, either express or implied, regarding the information in or the use of this report and
shall not be liable to you or any third parties for any acts or omissions undertaken by you or any third parties
based on the information contained herein.
Smart contracts are still a nascent software arena, and their deployment and public offering carry substantial
risk.

Finally, the possibility of human error in the manual review process is very real, and we recommend seeking
multiple independent opinions on any claims that impact a large quantity of funds.

This report reflects a point-in-time review of the specified scope at the specified commit(s). It is not a warranty that the code is free of vulnerabilities, not an endorsement of the project, and not investment advice. Security reviews are time-boxed and cannot guarantee the absence of defects. The firm's original PDF report is the authoritative document; this markdown file is a derived summary prepared for the Stellar Audit Bank report archive. Copyright in the report content remains with Runtime Verification; reuse is governed by the license stated in the frontmatter.

## 8. Appendix

This appendix gathers supplementary reference material that supported the review but does not form part of
the findings. It is included for context only and introduces no new issues, severities, or recommendations.
The Protocol Summary that follows provides a consolidated overview of the Moonlight core contracts (their
roles, on-chain state, and the deposit, private-transfer, and withdrawal lifecycle) as understood during the
engagement, and may serve as a reference material for readers new to the protocol before returning to the
findings above.

The Protocol Summary itself is not reproduced here; see the authoritative PDF.
