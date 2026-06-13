"""Site activity ledger for ChaseOS-controlled browser runtime runs."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.browser_runtime.models import BrowserRunResult, domain_from_url, now_iso, slugify


def _default_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    return Path.cwd()


def site_activity_dir(root: Path | str | None = None) -> Path:
    base = Path(root) if root else _default_root()
    return base / "07_LOGS" / "Site-Activity"


def site_activity_ledger_path(root: Path | str | None = None) -> Path:
    return site_activity_dir(root) / "site-memory-ledger.json"


def vault_site_memory_note_path(root: Path | str | None = None) -> Path:
    base = Path(root) if root else _default_root()
    return base / "06_AGENTS" / "Site-Memory-Ledger.md"


def load_site_activity_ledger(root: Path | str | None = None) -> dict:
    path = site_activity_ledger_path(root)
    if not path.exists():
        return {"record_type": "site_memory_ledger", "created_at": now_iso(), "sites": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def update_site_activity_ledger(
    result: BrowserRunResult,
    *,
    root: Path | str | None = None,
    candidate_path: str | None = None,
    draft_path: str | None = None,
) -> str:
    """Record non-secret aggregate memory for ChaseOS-controlled browser runs."""
    path = site_activity_ledger_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    ledger = load_site_activity_ledger(root)
    domain = domain_from_url(result.url) or "local-file"
    site = ledger.setdefault("sites", {}).setdefault(
        domain,
        {
            "domain": domain,
            "visit_count_chaseos_runs": 0,
            "common_tasks": [],
            "known_traps": [],
            "candidate_skills": [],
            "last_run_log": None,
            "promotion_status": "candidate",
            "updated_at": None,
        },
    )
    site["visit_count_chaseos_runs"] = int(site.get("visit_count_chaseos_runs", 0)) + 1
    if result.task and result.task not in site["common_tasks"]:
        site["common_tasks"].append(result.task)
    for item in [
        "No secrets, cookies, profile state, or credentials observed/retained in this ledger.",
        "Only ChaseOS-controlled browser runtime runs are counted.",
    ]:
        if item not in site["known_traps"]:
            site["known_traps"].append(item)
    for item in [candidate_path, draft_path]:
        if item and item not in site["candidate_skills"]:
            site["candidate_skills"].append(item)
    site["last_run_log"] = result.browser_run_log_path
    site["updated_at"] = now_iso()
    ledger["updated_at"] = now_iso()
    path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    write_site_memory_note(ledger, root=root)
    return str(path)


def write_site_memory_note(ledger: dict, *, root: Path | str | None = None) -> str:
    """Write a vault-facing read-only summary of the site memory ledger."""
    path = vault_site_memory_note_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "title: Site Memory Ledger",
        "type: runtime-ledger",
        "status: partial / browser-runtime-controlled runs only",
        f"updated: {now_iso()}",
        "---",
        "",
        "# Site Memory Ledger",
        "",
        "This ledger summarizes reusable, non-secret website interaction facts from ChaseOS-controlled browser runtime runs only.",
        "",
        "It must not import real browser history, cookies, session tokens, credentials, profile paths, or private account state.",
        "",
        "## Sites",
        "",
    ]
    for domain, site in sorted((ledger.get("sites") or {}).items()):
        lines.extend(
            [
                f"### {domain}",
                "",
                f"- ChaseOS run count: {site.get('visit_count_chaseos_runs', 0)}",
                f"- Last run log: `{site.get('last_run_log')}`",
                f"- Promotion status: {site.get('promotion_status')}",
                "- Candidate skills:",
            ]
        )
        candidates = site.get("candidate_skills") or []
        if candidates:
            lines.extend(f"  - `{item}`" for item in candidates)
        else:
            lines.append("  - none")
        lines.extend(["- Common tasks:"])
        tasks = site.get("common_tasks") or []
        if tasks:
            lines.extend(f"  - {item}" for item in tasks)
        else:
            lines.append("  - none")
        lines.extend(["", ""])
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return str(path)


def site_summary_for_domain(root: Path | str | None, domain: str) -> dict:
    ledger = load_site_activity_ledger(root)
    sites = ledger.get("sites") or {}
    return dict(sites.get(domain) or sites.get(slugify(domain), {}))
