# Example conversions (temporary)

> **These are examples, not archive entries.** They are unreviewed output of the converters in
> [`tools/auditbank/converters/`](../tools/auditbank/converters/), kept here so firms can see what a
> conversion of their published report looks like. **Remove this directory once each firm has reviewed
> and approved its converter.** Accepted reports live in [`reports/`](../reports/), and only those are indexed.

| Example | Source (authoritative) | Converter |
|---|---|---|
| [`splyce--hal--2026-07-30.md`](splyce--hal--2026-07-30.md) | [Halborn report page](https://www.halborn.com/audits/splyce/smart-contract-assessment-de69cd) | `halborn.py` |
| [`moonlight--rv--2026-07-24.md`](moonlight--rv--2026-07-24.md) | [Runtime Verification PDF](https://strapi.runtimeverification.com/uploads/Moonlight_report_64808bfd8e.pdf) | `runtime_verification.py` |
| [`redstone--ver--2025-10-27.md`](redstone--ver--2025-10-27.md) | [Veridise PDF](https://veridise.com/wp-content/uploads/2025/10/VAR-Redstone-251006-Oracles-SDK-V2.pdf) | `veridise.py` |

Each file validates with zero errors and two expected draft warnings: `SIGNOFF_PENDING` (no firm sign-off yet)
and `CONVERSION_NOTES_OPEN` (every proposed severity, inferred category or location, and assumed date or
license is flagged with a `<!-- CONVERSION-NOTE -->` for the firm to confirm). Content copyright remains with
each firm; the `Apache-2.0` license in these drafts is a placeholder default the firm must confirm.

Regenerate with:

```sh
auditbank convert <source-url> --project-slug <slug> --out examples/<slug>--<firm>--<date>.md
```
