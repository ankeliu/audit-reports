"""`--ai`: model-assisted gap filling for converter drafts (CLAUDE_CODE_PLAN.md section 7).

Exactly four jobs, each leaving a CONVERSION-NOTE for the firm reviewer:
1. split a single Description blob into Description / Impact / Proof when the source doesn't separate them;
2. propose `category` from the taxonomy, with a one-line justification;
3. propose `unified_severity` when the firm's label is ambiguous (e.g. Veridise "Warning");
4. draft the ~250-word executive summary from the firm's own summary.

Hard rules: the model never sets dates, commits, counts, locations, or statuses. Every answer is checked
mechanically before use (splits must be verbatim source text, drafted prose may not introduce numbers absent
from the source, enums are schema-constrained); anything that fails a check is discarded and the deterministic
value stays. Each call's prompt/response SHA-256 goes into `log` for the PR body.
"""

import hashlib
import json
import re
import sys

from .paths import vocab

MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"

SYSTEM = (
    "You help convert published smart-contract audit reports into a standard format. You work only from the "
    "text you are given: never add facts, numbers, dates, commits, file paths, or claims that are not in it. "
    "The audit firm reviews everything you produce before publication."
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _norm(text: str) -> str:
    return " ".join((text or "").split())


class Assistant:
    """Thin wrapper: one structured-output call per job, with logging and refusal handling."""

    def __init__(self, client=None, log: list | None = None):
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self.client = client
        self.log = log if log is not None else []

    def ask(self, job: str, prompt: str, schema: dict, effort: str = "low", max_tokens: int = 8000) -> dict | None:
        try:
            response = self.client.beta.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=SYSTEM,
                betas=[FALLBACK_BETA],
                fallbacks="default",
                output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:  # any API failure leaves the deterministic draft in place
            print(f"auditbank --ai: {job} skipped ({type(exc).__name__}: {exc})", file=sys.stderr)
            return None
        text = next((b.text for b in response.content if getattr(b, "type", None) == "text"), "")
        self.log.append(
            {
                "job": job,
                "model": getattr(response, "model", MODEL),
                "prompt_sha256": _sha(prompt),
                "response_sha256": _sha(text),
                "stop_reason": response.stop_reason,
            }
        )
        if response.stop_reason != "end_turn" or not text:
            print(f"auditbank --ai: {job} returned stop_reason={response.stop_reason}; skipped", file=sys.stderr)
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None


# ------------------------------------------------------------------ job 1: split

SPLIT_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "impact": {"type": "string"},
        "proof": {"type": ["string", "null"]},
    },
    "required": ["description", "impact", "proof"],
    "additionalProperties": False,
}


SPLIT_TRIGGER = re.compile(r"impact.*(heading|paragraph|statement)|(heading|paragraph|statement).*impact", re.I)


def _verbatim(part: str | None, source: str) -> bool:
    """Every sentence of `part` must appear in the source (whitespace-insensitive)."""
    if not part:
        return True
    src = _norm(source)
    sentences = [s for s in re.split(r"(?<=[.!?])\s+|\n+", part) if len(_norm(s)) > 3]
    return all(_norm(s) in src for s in sentences)


def split_description(ai: Assistant, finding: dict) -> bool:
    source = "\n\n".join(x for x in (finding.get("description"), finding.get("proof")) if x)
    prompt = (
        "Split this audit finding's text into three parts, copying sentences VERBATIM (no rewording, no new text):\n"
        "- description: the flaw and its root cause;\n"
        "- impact: the sentences describing consequences (who loses what, which guarantee breaks);\n"
        "- proof: numbered attack steps or a PoC reference if present, else null.\n"
        "Every sentence must come from the text below; code blocks stay with the part they illustrate.\n\n"
        f"Finding title: {finding.get('title')}\n\n<text>\n{source}\n</text>"
    )
    out = ai.ask("split", prompt, SPLIT_SCHEMA, effort="low")
    if not out or not out["description"].strip() or not out["impact"].strip():
        return False
    if not all(_verbatim(out[k], source) for k in ("description", "impact", "proof")):
        ai.log[-1]["rejected"] = "split was not verbatim source text"
        return False
    finding["description"], finding["impact"] = out["description"].strip(), out["impact"].strip()
    if out["proof"] and out["proof"].strip():
        finding["proof"] = out["proof"].strip()
    finding["conversion_notes"] = [n for n in finding["conversion_notes"] if "impact" not in n.lower()]
    finding["conversion_notes"].append("Description / Impact / Proof split by AI from the source text; confirm")
    return True


# --------------------------------------------------------------- job 2: category


def propose_categories(ai: Assistant, findings: list[dict]) -> int:
    targets = [f for f in findings if any("category inferred" in n for n in f["conversion_notes"])]
    if not targets:
        return 0
    categories = vocab()["category"]
    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "enum": [f["id"] for f in targets]},
                        "category": {"type": "string", "enum": categories},
                        "justification": {"type": "string"},
                    },
                    "required": ["id", "category", "justification"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["items"],
        "additionalProperties": False,
    }
    taxonomy = (
        "access-control-auth (require_auth misuse, auth confusion, custom accounts); accounting-arithmetic; "
        "liveness-dos; upgrade-migration; state-archival-ttl (Soroban state expiration, rent, TTL); "
        "cross-contract-trust (invocation trust, adapter/dependency boundaries); oracle-external-dependency; "
        "economic-design (incentives, MEV, manipulation); governance-centralization (admin keys, timelocks, upgrade "
        "authority); cryptography; data-validation; key-management-privacy; observability; code-quality; operational"
    )
    blocks = "\n\n".join(
        f'<finding id="{f["id"]}">\n{f["title"]}\n{(f.get("description") or "")[:1500]}\n</finding>' for f in targets
    )
    prompt = (
        f"Pick exactly one category per finding, the dominant one, from this taxonomy:\n{taxonomy}\n\n"
        "Give a one-line justification grounded in the finding text.\n\n" + blocks
    )
    out = ai.ask("category", prompt, schema, effort="low", max_tokens=16000)
    if not out:
        return 0
    by_id = {f["id"]: f for f in targets}
    changed = 0
    for item in out["items"]:
        f = by_id.get(item["id"])
        if not f:
            continue
        f["category"] = item["category"]
        f["conversion_notes"] = [n for n in f["conversion_notes"] if "category inferred" not in n]
        reason = _norm(item["justification"]).replace("-->", "->")
        f["conversion_notes"].append(f"category proposed by AI: {item['category']} ({reason}); firm to confirm")
        changed += 1
    return changed


# --------------------------------------------------------------- job 3: severity

AMBIGUOUS = re.compile(r'"warning"|no unified mapping', re.I)
SEVERITY_SCHEMA = {
    "type": "object",
    "properties": {
        "unified_severity": {"type": "string", "enum": ["Critical", "High", "Moderate", "Low", "Informational"]},
        "justification": {"type": "string"},
    },
    "required": ["unified_severity", "justification"],
    "additionalProperties": False,
}


def propose_severity(ai: Assistant, finding: dict, definitions: str) -> bool:
    if not any(AMBIGUOUS.search(n) for n in finding["conversion_notes"]):
        return False
    prompt = (
        "The audit firm rated this finding with a label that has no direct equivalent on the unified scale. "
        "Propose the unified severity using ONLY these definitions; the firm's own rating is kept verbatim and "
        f"governs on dispute.\n\n{definitions}\n\nFirm rating: {finding.get('firm_severity_rating')}\n"
        f"Title: {finding.get('title')}\n\nDescription:\n{finding.get('description')}\n\n"
        f"Impact:\n{finding.get('impact')}"
    )
    out = ai.ask("severity", prompt, SEVERITY_SCHEMA, effort="medium")
    if not out:
        return False
    finding["unified_severity"] = out["unified_severity"]
    finding["conversion_notes"] = [n for n in finding["conversion_notes"] if not AMBIGUOUS.search(n)]
    reason = _norm(out["justification"]).replace("-->", "->")
    finding["conversion_notes"].append(
        f"unified severity {out['unified_severity']} proposed by AI from the Section 4 definitions ({reason}); "
        "firm to confirm"
    )
    return True


# ------------------------------------------------------ job 4: executive summary

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}},
    "required": ["summary"],
    "additionalProperties": False,
}


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)*", text or ""))


def draft_summary(ai: Assistant, report: dict) -> bool:
    source = (report.get("sections") or {}).get("executive_summary") or ""
    if len(source.split()) <= 300:
        return False
    counts = report.get("findings_summary") or {}
    facts = (
        f"Client: {report['report'].get('client')}. Firm: {report['report'].get('audit_firm')}. "
        f"Findings by unified severity: {json.dumps(counts)}."
    )
    prompt = (
        "Rewrite the firm's executive summary below into about 250 words, three paragraphs, for a non-engineer "
        "reviewer: (1) who engaged whom and what was audited; (2) the most severe findings and their real-world "
        "impact; (3) overall assessment and the single most important next step. Use only facts from the text "
        "and the facts line; do not introduce any number that is not in them. No marketing language.\n\n"
        f"Facts: {facts}\n\n<firm_summary>\n{source}\n</firm_summary>"
    )
    out = ai.ask("summary", prompt, SUMMARY_SCHEMA, effort="medium")
    if not out or not out["summary"].strip():
        return False
    invented = _numbers(out["summary"]) - _numbers(source) - _numbers(facts)
    if invented:
        ai.log[-1]["rejected"] = f"summary introduced numbers {sorted(invented)}"
        return False
    report["sections"]["executive_summary"] = out["summary"].strip()
    report["conversion_notes"] = [n for n in report["conversion_notes"] if not n.startswith("Section 1 ")]
    report["conversion_notes"].append(
        "Section 1 drafted by AI from the firm's executive summary (no new facts or numbers); firm to review"
    )
    return True


# ------------------------------------------------------------------------ entry


def fill_gaps(report: dict, firm_report: dict | None = None, client=None, log: list | None = None) -> dict:
    """Run the four jobs on a converter draft. Never raises on API problems; the draft stays as it was."""
    from .template import severity_definitions

    ai = Assistant(client, log)
    for f in report["findings"]:
        if any(SPLIT_TRIGGER.search(n) for n in f["conversion_notes"]):
            split_description(ai, f)
    propose_categories(ai, report["findings"])
    definitions = severity_definitions()
    for f in report["findings"]:
        propose_severity(ai, f, definitions)
    draft_summary(ai, report)
    return report


def log_markdown(log: list[dict]) -> str:
    if not log:
        return ""
    rows = [
        f"| {e['job']} | `{e['model']}` | `{e['prompt_sha256']}` | `{e['response_sha256']}` | "
        f"{e.get('rejected') or e['stop_reason']} |"
        for e in log
    ]
    return "\n".join(
        [
            "### AI-assisted steps",
            "",
            "| Job | Model | Prompt SHA-256 | Response SHA-256 | Outcome |",
            "|---|---|---|---|---|",
            *rows,
            "",
        ]
    )
