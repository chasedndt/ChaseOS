"""Read-only deterministic instance profiling for VentureOps."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import DomainSignal, EvidenceRef, InstanceProfile


MODEL_VERSION = "ventureops.instance_profile.v1"
MAX_MARKDOWN_FILES = 500
MAX_FILE_BYTES = 120_000
MAX_EVIDENCE_PER_DOMAIN = 8

CHASEOS_MARKERS = (
    "README.md",
    "PROJECT_FOUNDATION.md",
    "ROADMAP.md",
    "00_HOME/Now.md",
    "00_HOME/Dashboard.md",
    "Projects-Hub.md",
    "06_AGENTS/Feature-Register.md",
    "06_AGENTS/Feature-Fit-Register.md",
    "06_AGENTS/Autonomous-Operator-Runtime.md",
    "runtime/workflows/registry/use_case_registry.yaml",
)

PROTECTED_OR_SECRET_PARTS = {
    ".env",
    "secrets",
    "credentials",
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
}

DOMAIN_TERMS: dict[str, tuple[str, ...]] = {
    "visual_product_creative": ("visual", "creative", "poster", "mockup", "landing", "design", "growth studio"),
    "creator_content": ("creator", "content", "newsletter", "audience", "cta", "funnel", "chaseintech"),
    "client_services": ("client", "freelance", "quote", "invoice", "scope", "fulfilment", "fulfillment"),
    "jobs_career": ("job", "internship", "cv", "resume", "cover letter", "recruiter", "career"),
    "university": ("university", "student", "module", "lecture", "lab", "revision", "coursework"),
    "research_to_product": ("research", "paper", "repo", "tool", "r&d", "roadmap", "intelligence"),
    "runtime_governance": ("runtime", "agent", "permission", "gate", "security", "audit", "mcp", "aor"),
    "crypto_trading": ("tradesync", "strikezone", "trading", "crypto", "signal provider", "chaser.sol", "solana"),
    "ecommerce_reselling": ("ecommerce", "reselling", "inventory", "listing", "hardware", "price research"),
    "game_prototype": ("game", "prototype", "playable", "mechanic", "interactive"),
    "founder_automation": ("automation", "operating system", "repeated task", "founder", "workflow audit"),
    "delegation": ("delegation", "outsourcing", "human specialist", "qa checklist", "acceptance criteria"),
    "ai_engineering": ("ai engineering", "model", "adapter", "role card", "mcp tool", "workflow lab"),
    "fullstack_build": ("full-stack", "fullstack", "prototype", "tests", "deployment", "build sprint"),
}

MONETIZATION_TERMS = (
    "client",
    "customer",
    "offer",
    "revenue",
    "monetizable",
    "cash-flow",
    "invoice",
    "price",
    "sell",
    "marketplace",
    "service",
    "productized",
)

ACTIVE_TERMS = ("active", "current", "now", "p0", "p1", "next", "in progress", "priority")
DORMANT_TERMS = ("paused", "dormant", "deferred", "later", "not active", "archive")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _is_safe_markdown(path: Path, root: Path) -> bool:
    rel_parts = {part.lower() for part in path.relative_to(root).parts}
    if rel_parts & PROTECTED_OR_SECRET_PARTS:
        return False
    if any(part.startswith(".codex") or part.startswith(".pytest") for part in rel_parts):
        return False
    return path.is_file() and path.suffix.lower() == ".md"


def _read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return path.read_text(encoding="utf-8", errors="ignore")[:MAX_FILE_BYTES]
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _iter_markdown(root: Path) -> tuple[list[Path], bool, list[str]]:
    paths: list[Path] = []
    errors: list[str] = []
    truncated = False
    try:
        iterator = root.rglob("*.md")
        for path in iterator:
            try:
                if not _is_safe_markdown(path, root):
                    continue
            except (OSError, ValueError) as exc:
                errors.append(str(exc))
                continue
            if len(paths) >= MAX_MARKDOWN_FILES:
                truncated = True
                break
            paths.append(path)
    except OSError as exc:
        errors.append(str(exc))
    return paths, truncated, errors


def _workspace_mode(root: Path, markdown_count: int) -> tuple[str, float, list[str], list[str]]:
    present = [marker for marker in CHASEOS_MARKERS if (root / marker).exists()]
    missing = [marker for marker in CHASEOS_MARKERS if marker not in present]
    has_dashboard_like_file = any(
        (root / candidate).exists()
        for candidate in ("Dashboard.md", "00_HOME/Dashboard.md", "Projects-Hub.md")
    )
    if len(present) >= 7:
        return "chaseos_native", 0.9, present, missing
    if len(present) >= 2:
        return "partial_chaseos", 0.65, present, missing
    if (root / ".obsidian").is_dir() or markdown_count >= 2 or has_dashboard_like_file:
        return "general_markdown", 0.45, present, missing
    return "unknown_sparse", 0.15, present, missing


def _extract_frontmatter_tags(text: str) -> list[str]:
    tags: list[str] = []
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if line.strip().lower().startswith("tags:"):
                    tags.extend(re.findall(r"[A-Za-z0-9_\-/]+", line.split(":", 1)[1]))
    tags.extend(match.group(1) for match in re.finditer(r"(?<!\w)#([A-Za-z0-9_\-/]+)", text))
    return sorted({tag.lower() for tag in tags if tag})


def _matches(text: str, terms: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    return [term for term in terms if term in lowered]


def _domain_signals(root: Path, markdown_paths: list[Path]) -> tuple[list[DomainSignal], list[str], list[dict[str, Any]]]:
    evidence_by_domain: dict[str, list[EvidenceRef]] = defaultdict(list)
    evidence_files: set[str] = set()
    monetization_signals: list[dict[str, Any]] = []

    for path in markdown_paths:
        text = _read_text(path)
        if not text:
            continue
        rel = _safe_rel(path, root)
        tags = _extract_frontmatter_tags(text)
        searchable = f"{rel}\n{text}\n{' '.join(tags)}"
        money_matches = _matches(searchable, MONETIZATION_TERMS)
        if money_matches:
            monetization_signals.append(
                {
                    "path": rel,
                    "matched_terms": money_matches[:8],
                    "confidence": min(0.9, 0.25 + 0.08 * len(money_matches)),
                }
            )
            evidence_files.add(rel)
        for domain, terms in DOMAIN_TERMS.items():
            matched = _matches(searchable, terms)
            if not matched:
                continue
            if len(evidence_by_domain[domain]) < MAX_EVIDENCE_PER_DOMAIN:
                evidence_by_domain[domain].append(
                    EvidenceRef(path=rel, matched_terms=matched[:8], reason="local workspace term match")
                )
            evidence_files.add(rel)

    signals: list[DomainSignal] = []
    for domain, evidence in evidence_by_domain.items():
        score = min(0.95, 0.22 + 0.13 * len(evidence))
        unique_terms = {term for item in evidence for term in item.matched_terms}
        score = min(0.98, score + min(0.24, 0.03 * len(unique_terms)))
        signals.append(DomainSignal(domain=domain, confidence=score, evidence=evidence))

    signals.sort(key=lambda item: (-item.confidence, item.domain))
    return signals, sorted(evidence_files), monetization_signals[:30]


def _project_records(root: Path, markdown_paths: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    active: list[dict[str, Any]] = []
    dormant: list[dict[str, Any]] = []
    for path in markdown_paths:
        rel = _safe_rel(path, root)
        lower_rel = rel.lower()
        if not any(part in lower_rel for part in ("project", "dashboard", "now", "roadmap")):
            continue
        text = _read_text(path).lower()
        active_hits = [term for term in ACTIVE_TERMS if term in text]
        dormant_hits = [term for term in DORMANT_TERMS if term in text]
        record = {
            "path": rel,
            "name": path.stem,
            "evidence_terms": (active_hits or dormant_hits)[:8],
        }
        if active_hits and len(active) < 20:
            active.append({**record, "confidence": min(0.9, 0.35 + 0.1 * len(active_hits))})
        elif dormant_hits and len(dormant) < 20:
            dormant.append({**record, "confidence": min(0.8, 0.25 + 0.1 * len(dormant_hits))})
    return active, dormant


def _workflow_opportunities(signals: list[DomainSignal]) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    for signal in signals:
        evidence_files = [item.path for item in signal.evidence]
        opportunities.append(
            {
                "domain": signal.domain,
                "confidence": round(signal.confidence, 3),
                "evidence_files": evidence_files,
                "suggestion_mode": "evidence_backed_draft",
            }
        )
    return opportunities


def _missing_information(mode: str, signals: list[DomainSignal]) -> list[str]:
    missing = [
        "approved customer or internal user for each workflow pack",
        "explicit approval policy for external sends and mutations",
        "first proof-card run target",
    ]
    if mode == "unknown_sparse":
        return [
            "workspace purpose",
            "active domains",
            "current projects",
            "repeatable tasks",
            "safe runtime boundaries",
        ]
    if not signals:
        missing.append("domain evidence")
    if not any(signal.domain in {"client_services", "creator_content", "visual_product_creative"} for signal in signals):
        missing.append("customer or monetization evidence")
    return missing


def _questions(mode: str, signals: list[DomainSignal]) -> list[str]:
    if mode == "unknown_sparse":
        return [
            "What are the three domains or projects this workspace should support first?",
            "Which repeated task would be valuable if it became a governed workflow pack?",
            "Which actions must remain human-approved or draft-only?",
        ]
    if not signals:
        return [
            "Which folders represent active work?",
            "Which outputs should become proof artifacts?",
            "Which customer or internal user should the first workflow serve?",
        ]
    return [
        "Which detected domain should become the first draft manifest?",
        "What input sources are approved for that workflow?",
        "What proof artifact would make the workflow trustworthy?",
    ]


def build_instance_profile(vault_root: str | Path) -> dict[str, Any]:
    """Build a read-only evidence-backed VentureOps instance profile."""
    root = Path(vault_root).resolve()
    markdown_paths, truncated, errors = _iter_markdown(root) if root.exists() and root.is_dir() else ([], False, [])
    mode, mode_confidence, present_markers, missing_markers = _workspace_mode(root, len(markdown_paths))
    signals, evidence_files, monetization = _domain_signals(root, markdown_paths)
    active, dormant = _project_records(root, markdown_paths)
    readiness = "insufficient_evidence"
    if mode == "unknown_sparse":
        readiness = "insufficient_evidence"
    elif signals and monetization:
        readiness = "ready_to_draft_manifest"
    elif signals:
        readiness = "needs_customer_offer"

    profile = InstanceProfile(
        workspace_mode=mode,
        confidence=mode_confidence if signals else min(mode_confidence, 0.35),
        detected_domains=signals,
        active_projects=active,
        dormant_projects=dormant,
        monetization_signals=monetization,
        workflow_opportunities=_workflow_opportunities(signals),
        evidence_files=evidence_files[:60],
        missing_information=_missing_information(mode, signals),
        discovery_questions=_questions(mode, signals),
        readiness_level=readiness,
        authority_boundary={
            "read_only": True,
            "writes_workspace": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "external_sends_allowed": False,
            "live_trading_allowed": False,
            "credential_or_secret_reads_allowed": False,
            "canonical_promotion_allowed": False,
        },
        scan_summary={
            "model_version": MODEL_VERSION,
            "generated_at": _now_utc(),
            "root": str(root),
            "exists": root.exists(),
            "is_directory": root.is_dir() if root.exists() else False,
            "markdown_files_scanned": len(markdown_paths),
            "scan_limit": MAX_MARKDOWN_FILES,
            "truncated": truncated,
            "errors": errors[:20],
            "present_chaseos_markers": present_markers,
            "missing_chaseos_markers": missing_markers,
        },
    )
    return profile.to_dict()
