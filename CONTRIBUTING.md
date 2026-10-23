# Contributing

**Submitting a report:** see [Submitting a report](README.md#submitting-a-report). Write it from [`AUDIT_REPORT_TEMPLATE.md`](AUDIT_REPORT_TEMPLATE.md) following [`FILLING_INSTRUCTIONS.md`](FILLING_INSTRUCTIONS.md), or convert your published report on the [submission page](https://ankeliu.github.io/audit-reports/).

**Changing the tooling, schema, or site:** open a pull request separate from any report. Before pushing:

```sh
pip install -e "tools/[dev]"
pytest
ruff check --config tools/pyproject.toml tools tests
```

If you change `schema/vocab.json`, regenerate the schema with `auditbank schema --write`.

Questions: your Audit Bank Slack channel.
