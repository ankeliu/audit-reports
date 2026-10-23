"""Shared converter machinery: fetch -> extract -> normalize -> report dict.

Rules every converter follows (see CLAUDE_CODE_PLAN.md section 4.0):
- `Firm severity rating` is the firm's label verbatim; unified severity is only *proposed*.
- Every inferred value carries a CONVERSION-NOTE; nothing is silently asserted.
- `conversion_method` stays null: the merge step sets it after firm sign-off.
- Dates, commits, and counts are never guessed: missing -> null + note.
"""

import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests
from markdownify import markdownify

from ..paths import REPO_ROOT, vocab
from ..render import SEVERITY_ORDER, blank_finding, sort_findings
from ..template import default_disclaimer

CACHE_DIR = REPO_ROOT / "tests" / "fixtures" / "_downloads"
USER_AGENT = "Mozilla/5.0 (compatible; auditbank/0.2; +https://github.com/ankeliu/audit-reports)"
DEFAULT_LICENSE = "Apache-2.0"
MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024

UNIFIED_FROM_LABEL = {
    "critical": "Critical",
    "high": "High",
    "major": "High",
    "medium": "Moderate",
    "moderate": "Moderate",
    "low": "Low",
    "minor": "Low",
    "warning": "Low",
    "informational": "Informational",
    "informative": "Informational",
    "info": "Informational",
    "note": "Informational",
    "best practice": "Informational",
    "gas": "Informational",
    "qa": "Informational",
}


@dataclass
class RawDoc:
    source: str
    kind: str  # "html" | "pdf" | "md"
    path: Path
    url: str | None


def is_url(source: str) -> bool:
    return urlparse(source).scheme in ("http", "https")


def fetch(source: str) -> RawDoc:
    """Download a URL into the gitignored cache (or use a local file). Content is treated as untrusted data."""
    if not is_url(source):
        path = Path(source)
        return RawDoc(source, _kind(path.name, path.read_bytes()[:5]), path, None)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    name = Path(urlparse(source).path).name or "index"
    path = CACHE_DIR / f"{hashlib.sha256(source.encode()).hexdigest()[:12]}-{name}"
    if not path.exists():
        resp = requests.get(source, headers={"User-Agent": USER_AGENT}, timeout=60, stream=True)
        resp.raise_for_status()
        data = b""
        for chunk in resp.iter_content(1 << 16):
            data += chunk
            if len(data) > MAX_DOWNLOAD_BYTES:
                raise ValueError(f"{source}: download exceeds {MAX_DOWNLOAD_BYTES} bytes")
        path.write_bytes(data)
    return RawDoc(source, _kind(path.name, path.read_bytes()[:5]), path, source)


def _kind(name: str, head: bytes) -> str:
    if head.startswith(b"%PDF"):
        return "pdf"
    if name.lower().endswith((".md", ".markdown")):
        return "md"
    return "html"


def html_to_md(html: str | None) -> str | None:
    if not html:
        return None
    text = markdownify(
        html,
        heading_style="ATX",
        bullets="-",
        escape_underscores=False,
        escape_asterisks=False,
        code_language_callback=_code_language,
    )
    text = text.replace(" ", " ")
    text = demote_headings(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() or None


def demote_headings(text: str) -> str:
    """H1-H3 are the report's own structure (title, sections, findings); source headings become H4."""
    out, in_fence = [], False
    for line in text.split("\n"):
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
        if not in_fence:
            line = re.sub(r"^#{1,3}(?=\s)", "####", line)
        out.append(line)
    return "\n".join(out)


def _code_language(el) -> str:
    for cls in el.get("class") or []:
        if cls.startswith("language-"):
            return cls.removeprefix("language-")
    return el.get("language") or ""


def project_code(slug: str) -> str:
    """`splyce` -> `SPLYCE`; `trustless-work` -> `TW`."""
    parts = [p for p in slug.split("-") if p]
    code = "".join(p[0] for p in parts) if len(parts) > 1 else (parts[0] if parts else "X")
    return re.sub(r"[^A-Z0-9]", "", code.upper()) or "X"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def unified_from_label(label: str | None) -> str | None:
    return UNIFIED_FROM_LABEL.get((label or "").strip().lower())


def severity_note(label: str, unified: str) -> str:
    return f'unified severity "{unified}" proposed from firm rating "{label}"; firm to confirm'


# Ordered: earlier categories win ties. Title matches count triple.
CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("state-archival-ttl", ["ttl", "archiv", "extend_ttl", "rent", "expiration", "instance storage", "bump"]),
    ("upgrade-migration", ["upgrade", "migrat", "wasm hash", "update_current_contract_wasm"]),
    (
        "access-control-auth",
        [
            "require_auth",
            "authoriz",
            "unauthori",
            "access control",
            "permission",
            "whitelist",
            "allowlist",
            "privilege",
            "bypass",
            "only the admin",
            "restricted",
        ],
    ),
    (
        "governance-centralization",
        ["centraliz", "admin key", "single point", "timelock", "governance", "multisig", "threshold", "signer"],
    ),
    ("oracle-external-dependency", ["oracle", "price feed", "stale price", "staleness", "pending price"]),
    (
        "cross-contract-trust",
        ["cross-contract", "external contract", "untrusted contract", "callback", "reentran", "sibling"],
    ),
    (
        "economic-design",
        [
            "front-run",
            "frontrun",
            "mev",
            "sandwich",
            "manipulat",
            "incentive",
            "arbitrage",
            "fee avoidance",
            "risk-free",
            "profit",
        ],
    ),
    (
        "accounting-arithmetic",
        [
            "overflow",
            "underflow",
            "rounding",
            "precision",
            "division",
            "arithmetic",
            "accounting",
            "decimals",
            "cast",
            "total_shares",
            "fee shares",
            "accrual",
            "interest",
        ],
    ),
    (
        "liveness-dos",
        [
            "denial of service",
            " dos ",
            "unbounded",
            "budget",
            "stuck",
            "strand",
            "griefing",
            "permanently",
            "blocked",
            "locked",
        ],
    ),
    ("cryptography", ["ed25519", "signature", "nonce", "replay", "hash collision", "cryptograph"]),
    ("key-management-privacy", ["private key", "secret", "leak", "privacy"]),
    (
        "data-validation",
        [
            "validat",
            "sanitiz",
            "zero address",
            "bounds",
            "input",
            "missing check",
            "unchecked",
            "accepts",
            "no-op",
            "identical",
        ],
    ),
    ("observability", ["event", "emit", "logging", "log "]),
    ("operational", ["deploy", "configuration", "operational", "initializ", "init "]),
    (
        "code-quality",
        [
            "unused",
            "dead code",
            "typo",
            "naming",
            "redundant",
            "documentation",
            "natspec",
            "comment",
            "magic number",
            "clippy",
            "refactor",
            "inconsistent",
            "duplicate",
        ],
    ),
]


def infer_category(title: str, text: str, unified: str | None) -> str:
    title_l, text_l = title.lower(), (text or "").lower()
    best, best_score = None, 0
    for category, words in CATEGORY_KEYWORDS:
        score = sum(3 * title_l.count(w) + min(text_l.count(w), 3) for w in words)
        if score > best_score:
            best, best_score = category, score
    if best:
        return best
    return "code-quality" if unified == "Informational" else "data-validation"


def new_report(firm: str) -> dict:
    """A report dict with every frontmatter key present, in template order."""
    return {
        "schema_version": vocab()["schema_version"],
        "report": {
            "title": None,
            "audit_firm": firm,
            "firm_contact": None,
            "auditors": None,
            "client": None,
            "report_date": None,
            "engagement_start": None,
            "engagement_end": None,
            "report_version": "1.0",
            "pdf_url": None,
            "firm_report_url": None,
        },
        "publication": {
            "disclosure_status": "public",
            "embargo_until": None,
            "license": DEFAULT_LICENSE,
            "conversion_method": None,
        },
        "audit": {"type": ["code-review"], "methods": [], "tooling": None},
        "effort": {"engineer_weeks": None, "reviewers": None},
        "scope": {
            "chain": "stellar",
            "platform": "soroban",
            "languages": [],
            "repositories": [],
            "in_scope_paths": [],
            "out_of_scope": [],
            "loc": None,
        },
        "findings_summary": {},
        "severity_standard": f"audit-bank-v{vocab()['schema_version']}",
        "heading": None,
        "conversion_notes": [
            f'publication.license defaulted to "{DEFAULT_LICENSE}"; firm to confirm reuse terms',
        ],
        "findings": [],
        "sections": {
            "executive_summary": None,
            "project_context": None,
            "assumptions_limitations": None,
            "methodology": None,
            "disclaimer": None,
            "appendix": None,
        },
    }


def new_finding() -> dict:
    return blank_finding()


def finalize(report: dict) -> dict:
    """Sort findings into template order and recompute findings_summary from them."""
    report["findings"] = sort_findings(report["findings"])
    counts = {sev.lower(): 0 for sev in SEVERITY_ORDER}
    for f in report["findings"]:
        if f.get("unified_severity") in SEVERITY_ORDER:
            counts[f["unified_severity"].lower()] += 1
    report["findings_summary"] = {"total": len(report["findings"]), **counts}
    for f in report["findings"]:
        if not f.get("location"):
            f["conversion_notes"].append("location not found in the source; firm to supply path:line")
    return report


def platform_from_text(report: dict, text: str) -> None:
    """Chain/platform default to stellar/soroban; note it unless the source says so."""
    lowered = (text or "").lower()
    if "soroban" in lowered:
        return
    if "stellar" in lowered:
        report["conversion_notes"].append("scope.platform assumed 'soroban' (source names Stellar only); confirm")
    else:
        report["conversion_notes"].append("scope.chain/platform assumed stellar/soroban; firm to confirm")


def disclaimer_with_default(firm: str, firm_text: str | None) -> tuple[str, str | None]:
    """Firm text plus the template default when the firm's text misses the required elements."""
    default = default_disclaimer(firm)
    if not firm_text:
        return default, f"no disclaimer found in the source; template default used with firm name {firm}"
    lowered = firm_text.lower()
    covers = all(any(t in lowered for t in group) for group in [("point-in-time", "snapshot"), ("warranty",)])
    if covers:
        return firm_text, None
    return (
        f"{firm_text}\n\n{default}",
        "firm disclaimer lacks point-in-time / no-warranty / authoritative-PDF language; "
        "template default appended; firm to confirm or substitute its own",
    )


class Converter(ABC):
    firm_abbrev: str
    firm_name: str

    @classmethod
    @abstractmethod
    def matches(cls, source: str, raw: RawDoc | None = None) -> bool: ...

    def fetch(self, source: str) -> RawDoc:
        return fetch(source)

    @abstractmethod
    def extract(self, raw: RawDoc) -> dict:
        """Firm-native structure, nothing normalized yet. Must be JSON-serializable (tests commit subsets)."""

    @abstractmethod
    def normalize(self, firm_report: dict, project_slug: str | None) -> dict: ...

    def default_slug(self, firm_report: dict) -> str:
        return slugify(firm_report.get("client") or "project")

    def convert(self, source: str, project_slug: str | None = None) -> dict:
        firm_report = self.extract(self.fetch(source))
        return finalize(self.normalize(firm_report, project_slug or self.default_slug(firm_report)))
