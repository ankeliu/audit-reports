"""`auditbank validate|convert|index|render|schema`."""

import argparse
import json
import sys
from pathlib import Path

from . import index as index_mod
from . import schema_gen
from .render import render
from .validate import ERROR, has_errors, validate_file


def _print_problems(path: str, problems: list[dict]) -> None:
    if not problems:
        print(f"{path}: OK")
        return
    errors = sum(p["level"] == ERROR for p in problems)
    print(f"{path}: {errors} error(s), {len(problems) - errors} warning(s)")
    for p in problems:
        print(f"  {p['level']:<7} {p['code']:<30} {p['path']:<36} {p['message']}")


def cmd_validate(args) -> int:
    results = {}
    failed = False
    for file in args.files:
        problems = validate_file(file)
        results[file] = problems
        failed |= has_errors(problems) or (args.strict and bool(problems))
        if not args.json:
            _print_problems(file, problems)
    if args.json:
        print(json.dumps(results if len(args.files) > 1 else results[args.files[0]], indent=2))
    return 1 if failed else 0


def cmd_convert(args) -> int:
    from .ai import log_markdown
    from .convert import convert

    ai_log: list = []
    out = convert(
        args.source, firm=args.firm, project_slug=args.project_slug, out=args.out, use_ai=args.ai, ai_log=ai_log
    )
    if ai_log:
        print(log_markdown(ai_log))
    problems = validate_file(out)
    _print_problems(str(out), problems)
    return 1 if has_errors(problems) else 0


def cmd_index(args) -> int:
    if args.check:
        if index_mod.is_current():
            print("reports/index.json and reports/README.md are up to date")
            return 0
        print("reports/index.json or reports/README.md is stale: run `auditbank index`", file=sys.stderr)
        return 1
    index = index_mod.write()
    print(f"indexed {len(index['reports'])} report(s)")
    return 0


def cmd_render(args) -> int:
    report = json.loads(Path(args.report).read_text())
    sys.stdout.write(render(report))
    return 0


def cmd_schema(args) -> int:
    if args.check:
        if schema_gen.is_current():
            print("schema/report-schema.json is up to date")
            return 0
        print("schema/report-schema.json is stale: run `auditbank schema --write`", file=sys.stderr)
        return 1
    schema_gen.write()
    print("wrote schema/report-schema.json")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="auditbank", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="validate standard report(s); exit 1 on errors")
    p.add_argument("files", nargs="+")
    p.add_argument("--json", action="store_true", help="print problems as JSON")
    p.add_argument("--strict", action="store_true", help="warnings also fail")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("convert", help="draft a standard report from a firm's published report")
    p.add_argument("source", help="report URL or local PDF/HTML/.md path")
    p.add_argument("--firm", choices=["hal", "rv", "ver"], help="skip auto-detection")
    p.add_argument("--project-slug", help="lowercase-kebab project slug (default: derived from the source)")
    p.add_argument("--out", help="output path (default: reports/<slug>/<slug>--<firm>--<date>.md)")
    p.add_argument("--ai", action="store_true", help="fill structural gaps with Claude (needs ANTHROPIC_API_KEY)")
    p.set_defaults(func=cmd_convert)

    p = sub.add_parser("index", help="rebuild reports/index.json and reports/README.md")
    p.add_argument("--check", action="store_true", help="fail if the index is stale instead of writing")
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("render", help="render a parsed report JSON to standard markdown")
    p.add_argument("report")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("schema", help="regenerate schema/report-schema.json from schema/vocab.json")
    p.add_argument("--check", action="store_true")
    p.add_argument("--write", action="store_true", help="(default) write the schema")
    p.set_defaults(func=cmd_schema)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
