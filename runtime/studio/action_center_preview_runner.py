"""Bounded preview runner for Studio release-grade action-center lanes.

The runner may invoke a small allowlist of read-only preview/readiness commands
and summarize their JSON envelopes for Studio. It never consumes approvals,
passes execution flags, writes artifacts, dispatches runtimes/browsers, reads
credentials, or mutates host/release/canonical state.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from runtime.studio.dashboard import get_dashboard

_DEFAULT_TIMEOUT_SECONDS = 45

_RUNNER_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "branded_installer_logo_icon": ("studio", "installer-plan", "--json"),
    "signing_chain": ("studio", "signing-approval-preview", "--json"),
    "startup_autostart_host_mutation": ("studio", "startup-autostart-approval-preview", "--json"),
    "release_promotion": ("studio", "release-promotion-approval-preview", "--json"),
    "provider_model_live_calls": ("studio", "phase11-chat-live-provider-execution-approval-preview", "--json"),
    "runtime_browser_dispatch": ("studio", "phase11-chat-runtime-dispatch-readiness-contract", "--json"),
}

_NOT_RUNNABLE_REASONS = {
    "real_target_workspace_migration": "requires_operator_target_path_and_approval_packet_id",
    "persisted_graph_storage_scope": "architecture_doc_review_only_no_cli_preview_runner",
}


def _extract_summary(envelope: dict[str, Any]) -> dict[str, Any]:
    result = envelope.get("result") if isinstance(envelope.get("result"), dict) else envelope
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    authority = result.get("authority") if isinstance(result.get("authority"), dict) else {}
    return {
        "ok": envelope.get("ok", result.get("ok")),
        "action": envelope.get("action"),
        "surface": result.get("surface"),
        "status": result.get("status"),
        "blocker_count": summary.get("blocker_count"),
        "next_recommended_pass": summary.get("next_recommended_pass") or result.get("next_recommended_pass"),
        "authority": {
            "read_only": authority.get("read_only"),
            "approval_execution_allowed": authority.get("approval_execution_allowed"),
            "provider_calls_allowed": authority.get("provider_calls_allowed"),
            "runtime_dispatch_allowed": authority.get("runtime_dispatch_allowed"),
            "browser_control_allowed": authority.get("browser_control_allowed"),
            "host_mutation_allowed": authority.get("host_mutation_allowed"),
            "canonical_mutation_allowed": authority.get("canonical_mutation_allowed"),
        },
    }


def _run_preview(args: tuple[str, ...], vault: Path, timeout_seconds: int) -> dict[str, Any]:
    command = (sys.executable, "-m", "runtime.cli.main", *args, "--vault-root", str(vault))
    creationflags = 0
    if os.name == "nt":
        creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0) or 0)
    completed = subprocess.run(
        command,
        cwd=vault,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
        creationflags=creationflags,
    )
    stdout = completed.stdout.strip()
    parsed: dict[str, Any] | None = None
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = None
    summary = _extract_summary(parsed or {}) if parsed else {}
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "json_parse_ok": parsed is not None,
        "preview_ok": bool(parsed and parsed.get("ok")),
        "blocked_preview_ok": bool(parsed and parsed.get("result")),
        "stdout_bytes": len(completed.stdout.encode("utf-8", errors="replace")),
        "stderr_excerpt": completed.stderr.strip()[:400],
        "summary": summary,
    }


def build_studio_action_center_preview_runner(
    vault_root: str | Path,
    *,
    execute_previews: bool = False,
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Build or run the no-execution Studio action-center preview summary."""

    vault = Path(vault_root).resolve()
    dashboard = get_dashboard(vault, probe_child_apps=False)
    product = dashboard.get("studio_product_home_panel") or {}
    lanes = product.get("open_release_lanes") or []
    preview_results: list[dict[str, Any]] = []

    for lane in lanes:
        lane_id = lane.get("id")
        allowed_args = _RUNNER_ALLOWLIST.get(str(lane_id))
        runnable = allowed_args is not None
        result: dict[str, Any] = {
            "lane_id": lane_id,
            "label": lane.get("label"),
            "human_loop": lane.get("human_loop"),
            "operator_input": lane.get("operator_input"),
            "runner_allowed": runnable,
            "execute_requested": execute_previews,
            "execution_authority_granted": False,
            "release_action_executed": False,
            "not_runnable_reason": None if runnable else _NOT_RUNNABLE_REASONS.get(str(lane_id), "not_in_preview_runner_allowlist"),
        }
        if runnable:
            result["allowlisted_command"] = " ".join((sys.executable, "-m", "runtime.cli.main", *allowed_args, "--vault-root", str(vault)))
        if runnable and execute_previews:
            try:
                result["preview_result"] = _run_preview(allowed_args, vault, timeout_seconds)
            except subprocess.TimeoutExpired:
                result["preview_result"] = {"timed_out": True, "timeout_seconds": timeout_seconds}
        preview_results.append(result)

    executed = [item for item in preview_results if item.get("preview_result")]
    return {
        "ok": True,
        "surface": "studio_action_center_preview_runner",
        "status": "PREVIEW_RUNNER_READY" if not execute_previews else "PREVIEW_RUNNER_EXECUTED_SAFE_PREVIEWS",
        "execute_previews": execute_previews,
        "lane_count": len(preview_results),
        "runner_allowed_count": sum(1 for item in preview_results if item.get("runner_allowed")),
        "not_runnable_count": sum(1 for item in preview_results if not item.get("runner_allowed")),
        "preview_executed_count": len(executed),
        "preview_json_parse_count": sum(1 for item in executed if (item.get("preview_result") or {}).get("json_parse_ok")),
        "preview_success_count": sum(1 for item in executed if (item.get("preview_result") or {}).get("preview_ok")),
        "blocked_preview_count": sum(
            1
            for item in executed
            if not (item.get("preview_result") or {}).get("preview_ok")
            and (item.get("preview_result") or {}).get("blocked_preview_ok")
        ),
        "lanes": preview_results,
        "authority": {
            "read_only": True,
            "allowlist_only": True,
            "executes_safe_preview_commands": bool(execute_previews),
            "executes_release_actions": False,
            "approval_execution_allowed": False,
            "signing_allowed": False,
            "host_mutation_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "target_mutation_allowed": False,
            "graph_store_write_allowed": False,
            "release_promotion_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }
