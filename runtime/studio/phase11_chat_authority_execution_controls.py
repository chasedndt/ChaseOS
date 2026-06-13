"""Unified Phase 11 Chat authority execution controls.

This surface prepares and optionally executes the manual MVP test stack:
live provider response, credential posture, Hermes/main-runtime dispatch,
Discord-control handoff through OpenClaw, schedule/cron handoff through
OpenClaw, and Agent Bus readback. It does not make direct Discord API calls,
mutate external cron, or expose credential values.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.agent_bus.bus import list_tasks
from runtime.studio.phase11_chat_authority_tier_controls import build_phase11_chat_authority_tier_controls
from runtime.studio.phase11_chat_live_provider_approval_preview import (
    build_phase11_chat_live_provider_execution_approval_preview,
)
from runtime.studio.phase11_chat_live_provider_execution_executor import (
    execute_phase11_chat_live_provider_execution,
)
from runtime.studio.phase11_chat_runtime_dispatch_executor import execute_phase11_chat_runtime_dispatch
from runtime.studio.phase11_chat_runtime_dispatch_readiness import (
    build_phase11_chat_runtime_dispatch_readiness,
)
from runtime.studio.provider_readiness import build_studio_provider_readiness


MODEL_VERSION = "studio.phase11_chat_authority_execution_controls.v1"
SURFACE_ID = "phase11_chat_authority_execution_controls"
PASS_ID = "studio-chat-full-authority-manual-test-orchestrator"
STATUS_PREVIEW = "COMPLETE / READY FOR MANUAL TEST / APPROVAL DIGESTS PREPARED"
STATUS_EXECUTED = "COMPLETE / APPROVAL-GATED EXECUTION ATTEMPTED / READBACK AVAILABLE"
NEXT_RECOMMENDED_PASS = "manual-test-with-openclaw-hermes-and-provider-env-running"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _runtime_lane_message(kind: str, message: str) -> str:
    return f"[Studio Chat manual authority test][{kind}] {message}".strip()


def _digest(payload: dict[str, Any]) -> str:
    return str((payload.get("request_digest_proof") or {}).get("request_digest") or "")


def _preview_lanes(vault: Path, message: str, explicit_intent: str | None) -> dict[str, Any]:
    provider = build_phase11_chat_live_provider_execution_approval_preview(
        vault,
        message=message,
        explicit_intent=explicit_intent or "chat-answer",
    )
    main_runtime = build_phase11_chat_runtime_dispatch_readiness(
        vault,
        message=message,
        explicit_intent="runtime-task",
        requested_runtime_id="Hermes",
        requested_action="planning",
    )
    discord = build_phase11_chat_runtime_dispatch_readiness(
        vault,
        message=_runtime_lane_message("discord-control", message),
        explicit_intent="runtime-task",
        requested_runtime_id="OpenClaw",
        requested_action="operator-briefing",
    )
    cron = build_phase11_chat_runtime_dispatch_readiness(
        vault,
        message=_runtime_lane_message("schedule-cron-control", message),
        explicit_intent="runtime-task",
        requested_runtime_id="OpenClaw",
        requested_action="operator-briefing",
    )
    return {
        "provider": provider,
        "main_runtime": main_runtime,
        "discord_control": discord,
        "cron_control": cron,
    }


def _lane_card(
    *,
    lane_id: str,
    label: str,
    preview: dict[str, Any],
    digest_key: str,
    executor: str,
    direct_external_mutation: bool = False,
) -> dict[str, Any]:
    summary = preview.get("summary") or {}
    digest = _digest(preview)
    blockers = list(preview.get("blocked_reasons") or [])
    return {
        "lane_id": lane_id,
        "label": label,
        "executor": executor,
        "digest_key": digest_key,
        "digest": digest,
        "preview_ready": bool(
            summary.get("approval_preview_ready")
            or summary.get("dispatch_preview_ready")
            or summary.get("message_present")
        ),
        "execution_preconditions_met": bool(
            summary.get("execution_preconditions_met") or summary.get("dispatch_preconditions_met")
        ),
        "selected_runtime_id": summary.get("selected_runtime_id"),
        "selected_task_type": summary.get("selected_task_type"),
        "selected_provider_id": summary.get("selected_provider_id"),
        "selected_model": summary.get("selected_model"),
        "requires_operator_statement": True,
        "requires_exact_digest": True,
        "direct_external_mutation": direct_external_mutation,
        "blocked_reasons": blockers,
    }


def _agent_bus_readback(vault: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for runtime in ("Hermes", "OpenClaw"):
        try:
            tasks = list_tasks(vault, recipient=runtime)
        except Exception:
            tasks = []
        for task in tasks[:10]:
            rows.append(
                {
                    "task_id": task.get("task_id"),
                    "recipient": runtime,
                    "status": task.get("status"),
                    "task_type": task.get("task_type"),
                    "created_at": task.get("created_at"),
                    "result": task.get("result") or task.get("response") or "",
                }
            )
    return {
        "readback_available": True,
        "task_count": len(rows),
        "tasks": rows[:20],
    }


def _execute_runtime_lane(
    *,
    vault: Path,
    lane_message: str,
    runtime_id: str,
    task_type: str,
    expected_digest: str | None,
    operator_statement: str | None,
    operator_id: str,
) -> dict[str, Any]:
    if not expected_digest:
        return {
            "ok": False,
            "surface": "phase11_chat_runtime_dispatch_executor",
            "status": "BLOCKED / DIGEST REQUIRED",
            "blocked_reasons": ["expected_dispatch_digest_required"],
        }
    return execute_phase11_chat_runtime_dispatch(
        vault,
        message=lane_message,
        explicit_intent="runtime-task",
        requested_runtime_id=runtime_id,
        requested_action=task_type,
        expected_dispatch_digest=expected_digest,
        operator_id=operator_id,
        operator_approval_statement=operator_statement,
        priority="normal",
    )


def build_phase11_chat_authority_execution_controls(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
    execute: bool = False,
    execute_provider: bool = True,
    execute_main_runtime: bool = True,
    execute_discord_control: bool = True,
    execute_cron_control: bool = True,
    expected_provider_digest: str | None = None,
    expected_main_runtime_digest: str | None = None,
    expected_discord_control_digest: str | None = None,
    expected_cron_control_digest: str | None = None,
    operator_id: str = "studio-operator",
    operator_approval_statement: str | None = None,
) -> dict[str, Any]:
    """Build the unified manual-test control payload and optionally execute it."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    provider_readiness = build_studio_provider_readiness(vault)
    tier_controls = build_phase11_chat_authority_tier_controls(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
    )
    previews = _preview_lanes(vault, normalized_message, explicit_intent)
    lanes = [
        _lane_card(
            lane_id="provider_call",
            label="Provider Call",
            preview=previews["provider"],
            digest_key="expected_provider_digest",
            executor="execute_phase11_chat_live_provider_execution",
        ),
        _lane_card(
            lane_id="main_runtime",
            label="Hermes/Main Runtime",
            preview=previews["main_runtime"],
            digest_key="expected_main_runtime_digest",
            executor="execute_phase11_chat_runtime_dispatch",
        ),
        _lane_card(
            lane_id="discord_control",
            label="Discord Control Via Runtime",
            preview=previews["discord_control"],
            digest_key="expected_discord_control_digest",
            executor="execute_phase11_chat_runtime_dispatch",
        ),
        _lane_card(
            lane_id="cron_control",
            label="Cron/Schedule Control Via Runtime",
            preview=previews["cron_control"],
            digest_key="expected_cron_control_digest",
            executor="execute_phase11_chat_runtime_dispatch",
        ),
    ]

    execution_results: dict[str, Any] = {}
    if execute:
        if execute_provider:
            execution_results["provider_call"] = execute_phase11_chat_live_provider_execution(
                vault,
                message=normalized_message,
                explicit_intent=explicit_intent or "chat-answer",
                expected_provider_digest=expected_provider_digest,
                operator_id=operator_id,
                operator_approval_statement=operator_approval_statement,
            )
        if execute_main_runtime:
            execution_results["main_runtime"] = _execute_runtime_lane(
                vault=vault,
                lane_message=normalized_message,
                runtime_id="Hermes",
                task_type="planning",
                expected_digest=expected_main_runtime_digest,
                operator_statement=operator_approval_statement,
                operator_id=operator_id,
            )
        if execute_discord_control:
            execution_results["discord_control"] = _execute_runtime_lane(
                vault=vault,
                lane_message=_runtime_lane_message("discord-control", normalized_message),
                runtime_id="OpenClaw",
                task_type="operator-briefing",
                expected_digest=expected_discord_control_digest,
                operator_statement=operator_approval_statement,
                operator_id=operator_id,
            )
        if execute_cron_control:
            execution_results["cron_control"] = _execute_runtime_lane(
                vault=vault,
                lane_message=_runtime_lane_message("schedule-cron-control", normalized_message),
                runtime_id="OpenClaw",
                task_type="operator-briefing",
                expected_digest=expected_cron_control_digest,
                operator_statement=operator_approval_statement,
                operator_id=operator_id,
            )

    successes = [item for item in execution_results.values() if isinstance(item, dict) and item.get("ok")]
    failures = [item for item in execution_results.values() if isinstance(item, dict) and not item.get("ok")]
    readback = _agent_bus_readback(vault)
    credential = provider_readiness.get("credential_posture") or {}
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS_EXECUTED if execute else STATUS_PREVIEW,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": not execute,
        "approval_gated": True,
        "summary": {
            "message_present": bool(normalized_message),
            "manual_test_ready": bool(normalized_message),
            "execute_requested": bool(execute),
            "lane_count": len(lanes),
            "provider_lane_ready": bool(lanes[0]["digest"]),
            "main_runtime_lane_ready": bool(lanes[1]["digest"]),
            "discord_control_lane_ready": bool(lanes[2]["digest"]),
            "cron_control_lane_ready": bool(lanes[3]["digest"]),
            "credential_env_ref": credential.get("primary_provider_env_ref"),
            "credential_environment_present": bool(credential.get("primary_provider_env_present")),
            "credential_values_visible": False,
            "execution_attempt_count": len(execution_results),
            "execution_success_count": len(successes),
            "execution_failure_count": len(failures),
            "agent_bus_readback_task_count": readback.get("task_count"),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "operator_inputs": {
            "operator_id": operator_id,
            "operator_approval_statement_required": True,
            "expected_provider_digest": expected_provider_digest or None,
            "expected_main_runtime_digest": expected_main_runtime_digest or None,
            "expected_discord_control_digest": expected_discord_control_digest or None,
            "expected_cron_control_digest": expected_cron_control_digest or None,
        },
        "prepared_digests": {
            "expected_provider_digest": lanes[0]["digest"],
            "expected_main_runtime_digest": lanes[1]["digest"],
            "expected_discord_control_digest": lanes[2]["digest"],
            "expected_cron_control_digest": lanes[3]["digest"],
        },
        "lanes": lanes,
        "provider_readiness": provider_readiness,
        "authority_tier_controls": tier_controls,
        "previews": previews,
        "execution_results": execution_results,
        "agent_bus_readback": readback,
        "authority": {
            "approval_gated": True,
            "provider_calls_allowed_with_digest_and_statement": True,
            "credential_env_reference_allowed": True,
            "credential_values_visible": False,
            "main_runtime_dispatch_allowed_with_digest_and_statement": True,
            "agent_bus_task_write_allowed_with_digest_and_statement": True,
            "discord_api_calls_allowed_from_studio": False,
            "discord_control_handoff_to_runtime_allowed": True,
            "external_scheduler_mutation_allowed_from_studio": False,
            "cron_control_handoff_to_runtime_allowed": True,
            "runtime_task_claim_allowed_from_studio": False,
            "workflow_execution_allowed_from_studio": False,
            "canonical_mutation_allowed": False,
        },
        "blocked_reasons": [] if normalized_message else ["message_required_for_manual_authority_test"],
        "warnings": [
            "Discord control is dispatched to the runtime/control-plane owner; Studio does not call Discord directly.",
            "Cron/schedule control is dispatched to the runtime/AOR owner; Studio does not mutate external cron directly.",
            "Credential values are never rendered or returned; provider execution uses only the env reference.",
        ],
    }


def format_phase11_chat_authority_execution_controls(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digests = payload.get("prepared_digests") or {}
    return "\n".join(
        [
            "Phase 11 Chat Authority Execution Controls",
            f"  status: {payload.get('status')}",
            f"  manual_test_ready: {summary.get('manual_test_ready')}",
            f"  provider_digest: {digests.get('expected_provider_digest')}",
            f"  main_runtime_digest: {digests.get('expected_main_runtime_digest')}",
            f"  discord_digest: {digests.get('expected_discord_control_digest')}",
            f"  cron_digest: {digests.get('expected_cron_control_digest')}",
            f"  execution_attempts: {summary.get('execution_attempt_count')}",
            f"  successes: {summary.get('execution_success_count')}",
            "  Boundary: explicit approval digests only; no direct Discord API calls, external cron mutation, raw secret display, or canonical mutation.",
        ]
    )
