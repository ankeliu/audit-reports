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

Each file has zero errors and two warnings that clear when the firm signs off:
`SIGNOFF_PENDING` (no firm approval yet) and `CONVERSION_NOTES_OPEN` (the few points the firm needs to confirm,
such as inferred categories, the report date, and the license, each marked with a `<!-- CONVERSION-NOTE -->`).
These are the same questions as in each firm's [converter review issue](https://github.com/ankeliu/audit-reports/issues?q=label%3Aconverter-review);
once a firm answers, the converter is updated and those notes stop appearing. Content copyright remains with each firm.

Regenerate with:

```sh
auditbank convert <source-url> --project-slug <slug> --out examples/<slug>--<firm>--<date>.md
```
