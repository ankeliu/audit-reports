from auditbank import index, schema_gen
from auditbank.paths import report_schema, vocab


def test_schema_file_is_generated_from_vocab():
    assert schema_gen.is_current(), "run `auditbank schema --write`"


def test_schema_enums_match_vocab():
    finding = report_schema()["properties"]["findings"]["items"]["properties"]
    assert finding["status"]["enum"] == vocab()["status"]
    assert finding["category"]["enum"] == vocab()["category"]
    assert finding["unified_severity"]["enum"] == vocab()["unified_severity"]


def test_index_has_no_comparison_fields():
    allowed = {
        "path",
        "project_slug",
        "client",
        "audit_firm",
        "firm_abbrev",
        "report_date",
        "platform",
        "disclosure_status",
        "conversion_method",
        "findings_summary",
        "pdf_url",
        "firm_report_url",
    }
    for entry in index.build()["reports"]:
        assert set(entry) <= allowed


def test_index_matches_index_schema():
    import json

    from auditbank.paths import SCHEMA_DIR
    from jsonschema import Draft202012Validator

    schema = json.loads((SCHEMA_DIR / "index-schema.json").read_text())
    Draft202012Validator(schema).validate(index.build())
