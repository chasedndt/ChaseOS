"""Browser run and Agent Activity logging for the bounded runtime spike."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.browser_runtime.models import BrowserRunRequest, BrowserRunResult, now_iso, slugify


def vault_root(root: Path | str | None = None) -> Path:
    if root:
        return Path(root)
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    return Path.cwd()


def browser_runs_dir(root: Path | str | None = None) -> Path:
    return vault_root(root) / "07_LOGS" / "Browser-Runs"


def agent_activity_dir(root: Path | str | None = None) -> Path:
    return vault_root(root) / "07_LOGS" / "Agent-Activity"


def write_browser_run_log(
    result: BrowserRunResult,
    request: BrowserRunRequest,
    *,
    root: Path | str | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    directory = browser_runs_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{result.run_id}.json"
    payload = {
        "record_type": "browser_run_log",
        "created_at": now_iso(),
        "request": request.as_dict(),
        "result": result.as_dict(),
        "governance": {
            "aor_layer": "Phase 9 Browser Runtime Adapter spike",
            "canonical_writeback": False,
            "skill_activation": False,
            "real_profile_allowed": False,
            "credentials_allowed": False,
        },
        "extra": extra or {},
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return str(path)


def write_agent_activity_log(
    result: BrowserRunResult,
    request: BrowserRunRequest,
    *,
    root: Path | str | None = None,
) -> str:
    directory = agent_activity_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    descriptor = slugify(result.run_id, "browser-runtime")
    path = directory / f"{descriptor}.md"
    lines = [
        "---",
        "runtime: Codex",
        "task_type: browser-runtime-adapter-spike",
        f"status: {result.status}",
        f"created: {now_iso()}",
        "---",
        "",
        f"# Browser Runtime Agent Activity - {result.run_id}",
        "",
        "## Inputs Read",
        f"- URL: `{request.url}`",
        f"- Task: {request.task}",
        f"- Provider: `{request.provider.value}`",
        f"- Mode: `{request.mode}`",
        "",
        "## Actions Taken",
    ]
    for action in result.actions:
        lines.append(f"- `{action.action_type}` on `{action.target}`: {action.status}")
        if action.blocked_reason:
            lines.append(f"  - Blocked reason: {action.blocked_reason}")
    lines.extend(
        [
            "",
            "## Files Written",
            f"- Browser run log: `{result.browser_run_log_path or 'pending at activity write time'}`",
            f"- Skill candidate: `{result.skill_candidate_path or 'none'}`",
            f"- Skill draft: `{result.skill_draft_path or 'none'}`",
            f"- Site activity ledger: `{result.site_activity_log_path or 'none'}`",
            "",
            "## Boundaries Respected",
            "- No real Chrome profile was used.",
            "- No saved credentials were used.",
            "- No cookies were exported.",
            "- No canonical ChaseOS state was mutated.",
            "- No generated skill was activated.",
            "",
            "## Boundaries Not Tested",
            "- Live Browser Use/CDP execution.",
            "- Authenticated browser sessions.",
            "- VincisOS browser runtime test.",
            "- Excalidraw browser/MCP test.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def persist_run_evidence(
    result: BrowserRunResult,
    request: BrowserRunRequest,
    *,
    root: Path | str | None = None,
    extra: dict[str, Any] | None = None,
) -> BrowserRunResult:
    run_log_path = write_browser_run_log(result, request, root=root, extra=extra)
    interim = BrowserRunResult(
        **{
            **result.as_dict(),
            "provider": result.provider,
            "actions": result.actions,
            "artifacts": result.artifacts,
            "browser_run_log_path": run_log_path,
        }
    )
    activity_path = write_agent_activity_log(interim, request, root=root)
    return BrowserRunResult(
        **{
            **interim.as_dict(),
            "provider": interim.provider,
            "actions": interim.actions,
            "artifacts": interim.artifacts,
            "agent_activity_log_path": activity_path,
        }
    )
