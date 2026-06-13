"""N8 terminal authority audit.

This module builds a read-only proof packet across the Studio Terminal
Workbench, Chaser board, N7 gateway ingress, and N6 terminal write executor
gates. It does not execute commands, write approval requests, consume approvals,
write Agent Bus tasks, call providers, or mutate canonical state.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.board import (
    build_action_proposal,
    build_board_state,
    build_terminal_write_approval_request,
)
from runtime.chaser.gateway import build_gateway_ingress_contract, handle_gateway_ingress
from runtime.chaser.terminal_write_executor import execute_terminal_write_approval
from runtime.chaser.terminal_write_executor_readiness import (
    build_terminal_write_executor_readiness,
)
from runtime.operator_surface.adapters.terminal_adapter import TerminalAdapter
from runtime.studio.terminal_workbench import build_terminal_workbench_contract


SURFACE = "chaser_terminal_authority_audit"
SCHEMA_VERSION = "chaser_terminal_authority_audit.v1"

_NO_AUTHORITY_KEYS = (
    "studio_execution_now",
    "terminal_execution_now",
    "approval_consumption_now",
    "approval_queue_write_now",
    "agent_bus_write_now",
    "provider_call_now",
    "canonical_writeback_now",
    "host_mutation_now",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _probe_name(root: Path) -> str:
    digest = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:12]
    return f"n8-authority-audit-target-{digest}"


def _snapshot(path: Path) -> list[str]:
    if not path.exists():
        return []
    entries: list[str] = []
    for item in path.rglob("*"):
        relative = item.relative_to(path)
        parts = set(relative.parts)
        if "__pycache__" in parts or item.suffix in {".pyc", ".pyo"}:
            continue
        if item.name.endswith(("-wal", "-shm")):
            continue
        entries.append(str(relative.as_posix()))
    return sorted(entries)


def _check(
    checks: list[dict[str, Any]],
    name: str,
    passed: bool,
    detail: str,
    *,
    evidence: dict[str, Any] | None = None,
) -> None:
    checks.append(
        {
            "name": name,
            "status": "pass" if passed else "fail",
            "passed": bool(passed),
            "detail": detail,
            "evidence": evidence or {},
        }
    )


def _all_false(mapping: dict[str, Any], keys: tuple[str, ...]) -> tuple[bool, dict[str, Any]]:
    evidence = {key: mapping.get(key) for key in keys}
    return all(value is False or value in (None, 0, "") for value in evidence.values()), evidence


def _supported_intents(contract: dict[str, Any]) -> set[str]:
    return {
        str(item.get("intent") or "")
        for item in contract.get("supported_intents", [])
        if isinstance(item, dict)
    }


def build_terminal_authority_audit(vault_root: str | Path) -> dict[str, Any]:
    """Return a read-only terminal authority audit packet.

    The audit intentionally uses denied/preview paths only. It verifies the
    current terminal wiring without creating terminal run records, approval
    requests, exact-once markers, Agent Bus state, or the probe target path.
    """

    root = Path(vault_root).resolve()
    probe_target = _probe_name(root)
    probe_command = f"mkdir {probe_target}"
    approval_dir = root / "runtime" / "studio" / "approvals"
    marker_dir = root / "07_LOGS" / "Terminal-Runs" / "_execution_markers"
    terminal_run_dir = root / "07_LOGS" / "Terminal-Runs"
    terminal_session_dir = root / "07_LOGS" / "Terminal-Sessions"
    agent_bus_dir = root / "runtime" / "agent_bus"

    before = {
        "approval_files": _snapshot(approval_dir),
        "marker_files": _snapshot(marker_dir),
        "terminal_run_files": _snapshot(terminal_run_dir),
        "terminal_session_files": _snapshot(terminal_session_dir),
        "agent_bus_files": _snapshot(agent_bus_dir),
        "probe_target_exists": (root / probe_target).exists(),
    }

    checks: list[dict[str, Any]] = []
    warnings = [
        "audit_is_read_only",
        "terminal_output_and_terminal_intent_are_tier4_untrusted",
        "no_studio_execution_no_agent_bus_write_no_provider_call_no_canonical_writeback",
    ]

    workbench = build_terminal_workbench_contract(root, command=probe_command, limit=3)
    workbench_authority = workbench.get("authority") if isinstance(workbench.get("authority"), dict) else {}
    _check(
        checks,
        "studio_terminal_workbench_read_only",
        workbench_authority.get("shell_execution_from_studio") is False
        and workbench_authority.get("command_run_from_studio") is False
        and workbench_authority.get("approval_consumption") is False
        and workbench_authority.get("agent_bus_mutation") is False
        and workbench_authority.get("provider_calls") is False,
        "Studio Terminal Workbench exposes preview/history/detail only.",
        evidence={"authority": workbench_authority},
    )
    preview = workbench.get("preview") if isinstance(workbench.get("preview"), dict) else {}
    preview_classification = (
        preview.get("classification") if isinstance(preview.get("classification"), dict) else {}
    )
    _check(
        checks,
        "studio_preview_does_not_execute_write_command",
        preview.get("would_execute") is False
        and preview_classification.get("action_class") == "write_command",
        "Workbench classification preview refuses write execution.",
        evidence={"preview": preview},
    )

    board = build_board_state(root, limit=2, include_gateway=False)
    board_authority = board.get("authority_summary") if isinstance(board.get("authority_summary"), dict) else {}
    _check(
        checks,
        "chaser_board_authority_is_read_only",
        board_authority.get("terminal_execution") is False
        and board_authority.get("studio_execution") is False
        and board_authority.get("provider_calls") is False
        and board_authority.get("agent_bus_writes") is False
        and board_authority.get("approval_consumption") is False,
        "Chaser board remains a proposal/evidence surface.",
        evidence={"authority_summary": board_authority},
    )

    proposal = build_action_proposal(
        root,
        action_type="terminal_command",
        command=probe_command,
        cwd=str(root),
        actor="n8-authority-audit",
    )
    _check(
        checks,
        "terminal_write_proposal_is_not_execution",
        proposal.get("status") == "approval_required_future_n6"
        and proposal.get("executes_now") is False
        and proposal.get("writes_now") is False
        and proposal.get("approval_queue_write_now") is False
        and proposal.get("agent_bus_write_now") is False
        and not (root / probe_target).exists(),
        "Write commands are proposal packets until the N6 approval lane is explicitly used.",
        evidence={
            "proposal_id": proposal.get("proposal_id"),
            "status": proposal.get("status"),
            "policy_decision": proposal.get("policy_decision"),
        },
    )

    approval_preview = build_terminal_write_approval_request(
        root,
        command=probe_command,
        cwd=str(root),
        actor="n8-authority-audit",
        write_request=False,
    )
    _check(
        checks,
        "approval_request_preview_does_not_queue_or_execute",
        approval_preview.get("status") == "ready_for_approval_request"
        and approval_preview.get("approval_request_written") is False
        and approval_preview.get("executes_now") is False
        and approval_preview.get("approval_consumption_now") is False
        and not (root / probe_target).exists(),
        "Approval request preview is eligible but performs no write.",
        evidence={
            "proposal_id": approval_preview.get("proposal_id"),
            "approval_request_written": approval_preview.get("approval_request_written"),
        },
    )

    readiness = build_terminal_write_executor_readiness(root, approval_id="../bad")
    _check(
        checks,
        "terminal_executor_readiness_rejects_unsafe_ids",
        readiness.get("ok") is False and "unsafe_approval_id" in (readiness.get("blockers") or []),
        "N6 readiness rejects path-like approval ids before any consumption or execution.",
        evidence={
            "blockers": readiness.get("blockers"),
            "authority": readiness.get("authority"),
        },
    )

    blocked_executor = execute_terminal_write_approval(
        root,
        approval_id="n8-authority-audit-missing",
        expected_proposal_id="",
        actor="n8-authority-audit",
        confirm_approved_terminal_write=False,
    )
    blocked_auth = (
        blocked_executor.get("authority")
        if isinstance(blocked_executor.get("authority"), dict)
        else {}
    )
    blocked_auth_ok, blocked_auth_evidence = _all_false(blocked_auth, _NO_AUTHORITY_KEYS)
    _check(
        checks,
        "terminal_write_executor_requires_explicit_confirmation",
        blocked_executor.get("ok") is False
        and "explicit_approved_terminal_write_confirmation_required"
        in (blocked_executor.get("blockers") or [])
        and blocked_auth_ok
        and not (root / probe_target).exists(),
        "N6 executor blocks before readiness unless the explicit terminal write confirmation is present.",
        evidence={
            "blockers": blocked_executor.get("blockers"),
            "authority": blocked_auth_evidence,
        },
    )

    gateway_contract = build_gateway_ingress_contract(root)
    gateway_auth = (
        gateway_contract.get("authority") if isinstance(gateway_contract.get("authority"), dict) else {}
    )
    gateway_auth_ok, gateway_auth_evidence = _all_false(gateway_auth, _NO_AUTHORITY_KEYS)
    required_intents = {
        "terminal.propose",
        "terminal.approval_request_preview",
        "terminal.approval_request_write",
        "terminal.executor_readiness",
        "terminal.execute_approval",
    }
    _check(
        checks,
        "gateway_contract_preserves_terminal_gates",
        gateway_auth_ok and required_intents.issubset(_supported_intents(gateway_contract)),
        "N7 ingress advertises terminal routes while preserving no ambient authority.",
        evidence={
            "authority": gateway_auth_evidence,
            "supported_intents": sorted(_supported_intents(gateway_contract)),
        },
    )

    gateway_missing_auth = handle_gateway_ingress(
        root,
        {
            "request_id": "n8auditmissauth",
            "intent": "terminal.propose",
            "payload": {"command": probe_command, "cwd": str(root)},
            "auth": {},
        },
    )
    _check(
        checks,
        "gateway_ingress_requires_local_operator_auth",
        gateway_missing_auth.get("ok") is False
        and "local_operator_confirmation_required" in (gateway_missing_auth.get("blockers") or []),
        "Gateway ingress fails closed without local-operator confirmation.",
        evidence={"blockers": gateway_missing_auth.get("blockers")},
    )

    gateway_preview = handle_gateway_ingress(
        root,
        {
            "request_id": "n8auditpreview",
            "intent": "terminal.propose",
            "payload": {"command": probe_command, "cwd": str(root)},
            "auth": {"mode": "local_operator", "operator_confirmed": True},
        },
    )
    gateway_preview_auth = (
        gateway_preview.get("authority") if isinstance(gateway_preview.get("authority"), dict) else {}
    )
    gateway_preview_auth_ok, gateway_preview_evidence = _all_false(gateway_preview_auth, _NO_AUTHORITY_KEYS)
    gateway_preview_result = (
        gateway_preview.get("result") if isinstance(gateway_preview.get("result"), dict) else {}
    )
    _check(
        checks,
        "gateway_terminal_proposal_is_preview_only",
        gateway_preview.get("ok") is True
        and gateway_preview_result.get("status") == "approval_required_future_n6"
        and gateway_preview_auth_ok
        and not (root / probe_target).exists(),
        "Authorized gateway proposal still does not execute or write approvals.",
        evidence={
            "status": gateway_preview_result.get("status"),
            "authority": gateway_preview_evidence,
        },
    )

    gateway_execute_missing_confirmation = handle_gateway_ingress(
        root,
        {
            "request_id": "n8auditexecblock",
            "intent": "terminal.execute_approval",
            "payload": {
                "approval_id": "n8-authority-audit-missing",
                "expected_proposal_id": "",
            },
            "auth": {"mode": "local_operator", "operator_confirmed": True},
        },
    )
    _check(
        checks,
        "gateway_execute_requires_terminal_write_confirmation",
        gateway_execute_missing_confirmation.get("ok") is False
        and "operator_approved_terminal_write_confirmation_required"
        in (gateway_execute_missing_confirmation.get("blockers") or []),
        "Gateway execution route is gated before it can delegate to N6.",
        evidence={"blockers": gateway_execute_missing_confirmation.get("blockers")},
    )

    blocked_commands = {
        "shell_control": "pwd && whoami",
        "elevated": "sudo ls",
        "destructive": "rm -rf example",
        "network": "curl https://example.com",
    }
    classifications = {
        name: TerminalAdapter.classify_command(command)
        for name, command in blocked_commands.items()
    }
    expected_classes = {
        "shell_control": "blocked_shell_control_command",
        "elevated": "elevated_command",
        "destructive": "destructive_command",
        "network": "network_command",
    }
    _check(
        checks,
        "terminal_adapter_blocks_unsafe_command_classes",
        all(
            classifications[name].get("allowed") is False
            and classifications[name].get("approval_required") is True
            and classifications[name].get("action_class") == expected
            for name, expected in expected_classes.items()
        ),
        "Adapter classification blocks shell control, elevated, destructive, and network commands.",
        evidence={"classifications": classifications},
    )

    forbidden_methods = [
        "run_terminal",
        "execute_terminal",
        "run_chaser_gateway_ingress",
        "execute_chaser_gateway_ingress",
        "run_chaser_terminal",
        "execute_chaser_terminal",
        "run_terminal_from_studio",
        "execute_terminal_from_studio",
    ]
    read_only_methods = (
        "get_terminal_workbench",
        "get_terminal_run_detail",
        "get_chaser_gateway_ingress_contract",
        "get_chaser_terminal_write_executor_readiness",
        "get_chaser_runtime_readiness",
    )
    human_terminal_methods = (
        "create_terminal_session",
        "list_terminal_sessions",
        "get_terminal_session",
        "read_terminal_output",
        "write_terminal_input",
        "resize_terminal_session",
        "interrupt_terminal_session",
        "terminate_terminal_session",
        "close_terminal_session",
    )
    try:
        from runtime.studio.shell.api import StudioAPI

        present_forbidden = [name for name in forbidden_methods if hasattr(StudioAPI, name)]
        studio_api_check_ok = not present_forbidden
        studio_api_evidence: dict[str, Any] = {
            "forbidden_methods_present": present_forbidden,
            "read_only_methods_present": [
                name for name in read_only_methods if hasattr(StudioAPI, name)
            ],
            "human_terminal_methods_present": [
                name for name in human_terminal_methods if hasattr(StudioAPI, name)
            ],
            "inspection_mode": "runtime_import",
        }
    except Exception as exc:  # pragma: no cover - defensive import guard
        api_source = Path(__file__).resolve().parents[1] / "studio" / "shell" / "api.py"
        try:
            text = api_source.read_text(encoding="utf-8", errors="replace")
            present_forbidden = [
                name
                for name in forbidden_methods
                if f"StudioAPI.{name}" in text or f"def {name}(" in text or f"def _{name}(" in text
            ]
            read_only_present = [name for name in read_only_methods if f"StudioAPI.{name}" in text]
            human_terminal_present = [name for name in human_terminal_methods if f"StudioAPI.{name}" in text]
            studio_api_check_ok = not present_forbidden and len(read_only_present) >= 3
            studio_api_evidence = {
                "forbidden_methods_present": present_forbidden,
                "read_only_methods_present": read_only_present,
                "human_terminal_methods_present": human_terminal_present,
                "inspection_mode": "source_text_fallback",
                "import_error": str(exc),
                "source": api_source.as_posix(),
            }
        except Exception as fallback_exc:  # pragma: no cover - defensive import guard
            studio_api_check_ok = False
            studio_api_evidence = {
                "error": str(exc),
                "fallback_error": str(fallback_exc),
                "inspection_mode": "unavailable",
            }
    _check(
        checks,
        "studio_api_has_only_human_terminal_and_readback_methods",
        studio_api_check_ok,
        "Studio exposes human operator terminal sessions plus readback methods, with no forbidden Chaser/autonomous terminal execution names.",
        evidence=studio_api_evidence,
    )

    # N33: live runtime naming must be ChaserAgent / Hermes / OpenClaw, and the
    # retired "OpenCore" lane must not appear in live terminal registries.
    try:
        from runtime.studio.terminal_agent_launchers import list_terminal_agent_launchers
        from runtime.studio.terminal_slash_commands import list_terminal_slash_commands

        slash = list_terminal_slash_commands(root)
        launchers = list_terminal_agent_launchers(root)
        slash_blob = " ".join(str(item.get("command", "")) for item in slash.get("commands", [])).lower()
        launcher_ids = {str(item.get("id", "")).lower() for item in launchers.get("launchers", [])}
        no_opencore = "opencore" not in slash_blob and "opencore" not in launcher_ids
        established = {"hermes", "openclaw", "chaseragent"}
        naming_ok = no_opencore and established.issubset(launcher_ids)
        naming_evidence = {
            "launcher_ids": sorted(launcher_ids),
            "opencore_absent": no_opencore,
            "established_lanes_present": sorted(established & launcher_ids),
        }
    except Exception as exc:  # pragma: no cover - defensive
        naming_ok = False
        naming_evidence = {"error": str(exc)}
    _check(
        checks,
        "live_runtime_naming_chaseragent_hermes_openclaw_no_opencore",
        naming_ok,
        "Live terminal registries use ChaserAgent/Hermes/OpenClaw and contain no OpenCore lane.",
        evidence=naming_evidence,
    )

    after = {
        "approval_files": _snapshot(approval_dir),
        "marker_files": _snapshot(marker_dir),
        "terminal_run_files": _snapshot(terminal_run_dir),
        "terminal_session_files": _snapshot(terminal_session_dir),
        "agent_bus_files": _snapshot(agent_bus_dir),
        "probe_target_exists": (root / probe_target).exists(),
    }
    side_effects = {
        "approval_files_unchanged": before["approval_files"] == after["approval_files"],
        "marker_files_unchanged": before["marker_files"] == after["marker_files"],
        "terminal_run_files_unchanged": before["terminal_run_files"] == after["terminal_run_files"],
        "terminal_session_files_unchanged": before["terminal_session_files"] == after["terminal_session_files"],
        "agent_bus_files_unchanged": before["agent_bus_files"] == after["agent_bus_files"],
        "probe_target_not_created": before["probe_target_exists"] is False
        and after["probe_target_exists"] is False,
    }
    side_effect_diffs = {
        "agent_bus_files_added": sorted(
            set(after["agent_bus_files"]) - set(before["agent_bus_files"])
        )[:20],
        "agent_bus_files_removed": sorted(
            set(before["agent_bus_files"]) - set(after["agent_bus_files"])
        )[:20],
    }
    _check(
        checks,
        "audit_created_no_runtime_side_effects",
        all(side_effects.values()),
        "Authority audit did not create approvals, markers, terminal run/session records, Agent Bus files, or probe target.",
        evidence={
            "before": before,
            "after": after,
            "side_effects": side_effects,
            "side_effect_diffs": side_effect_diffs,
        },
    )

    failed = [check for check in checks if not check["passed"]]
    passed_count = len(checks) - len(failed)
    return {
        "ok": not failed,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "mode": "read_only_authority_audit",
        "vault_root": str(root),
        "generated_at": _now_iso(),
        "summary": {
            "status": "pass" if not failed else "fail",
            "checks_total": len(checks),
            "checks_passed": passed_count,
            "checks_failed": len(failed),
            "failed_checks": [str(check["name"]) for check in failed],
        },
        "authority": {
            "studio_execution_now": False,
            "terminal_execution_now": False,
            "approval_queue_write_now": False,
            "approval_consumption_now": False,
            "exact_once_marker_write_now": False,
            "terminal_audit_write_now": False,
            "agent_bus_write_now": False,
            "provider_call_now": False,
            "canonical_writeback_now": False,
            "external_upload_now": False,
            "host_mutation_now": False,
        },
        "probe": {
            "command": probe_command,
            "cwd": str(root),
            "target_path": probe_target,
            "target_exists_after": (root / probe_target).exists(),
        },
        "checks": checks,
        "side_effects": side_effects,
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": warnings,
    }
