# Stellar Audit Bank audit reports

A public archive of completed Stellar Audit Bank audits in one standard format. Each report lists what was reviewed, what was found, how severe it is on a shared scale, and whether it was fixed. People can read it, and security tools can parse it.

Each file summarizes a report the audit firm has already published. The firm's PDF or report page remains the authoritative version.

## Submitting a report

Submit only once your firm would publish the report anyway: the client has approved publication and any embargo is over.

- **Have a published PDF or report page?** Use the [submission page](https://ankeliu.github.io/audit-reports/). It converts the report, posts the result on a GitHub issue, and opens a pull request for an engineer at your firm to review. Converters exist for Halborn, Runtime Verification, and Veridise.
- **Already have a file in the standard format?** Check it on the same page, or open a pull request adding `reports/{project}/{project}--{firm}--{YYYY-MM-DD}.md`.

Every pull request is checked automatically. The SDF audit coordinator then confirms the report belongs to an Audit Bank engagement and that the client approved publication, and merges it. Converted reports also need approval from an engineer at the firm. Corrections are new pull requests that increase `report_version`.

## What's here

| Path | What it is |
|---|---|
| [`AUDIT_REPORT_TEMPLATE.md`](AUDIT_REPORT_TEMPLATE.md) | The report template |
| [`FILLING_INSTRUCTIONS.md`](FILLING_INSTRUCTIONS.md) | How to fill it in, including severity mapping, redaction, and a checklist |
| [`reports/`](reports/) | Accepted reports and their index |
| [`schema/`](schema/) | JSON Schema and the allowed values for severity, status, category, and firms |
| [`tools/`](tools/) | The `auditbank` command-line tool |
| [`site/`](site/) | The submission page |
| [`examples/`](examples/) | Sample conversions, removed once firms approve their converters |

## Using the command-line tool

```sh
pip install -e tools/
auditbank validate path/to/report.md       # the same checks the pull request runs
auditbank convert <report URL or PDF>      # draft a standard file from a published report
```

## Converters

Each firm reviews how its reports are converted before the converter is used for real submissions. Questions for each firm are in the [converter review issues](https://github.com/ankeliu/audit-reports/issues?q=label%3Aconverter-review); firms can answer there.

## Principles

- **Severity belongs to the firm.** Every finding keeps the firm's own rating next to the shared one, and the firm's rating wins if they disagree.
- **Published reports are not re-rated.** A report keeps the format version it was submitted under.
- **No rankings.** SDF uses this data for audit context and does not publish comparisons between firms.

Contact: Anke Liu, Michael Berryhill, or Ashley Wright (SDF Ecosystem Growth), or your Audit Bank Slack channel.
