"""Studio-facing runtime startup controls.

This module builds a UI-ready control model over the lifecycle startup-surface
commands. It deliberately routes state changes through the existing runtime
startup-surface executor contract instead of writing host startup files itself.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
import json

from runtime.lifecycle.startup_surfaces import (
    ROOT,
    STARTUP_SURFACE_APPROVAL_DIR,
    build_startup_surface_approval_consumption,
    build_startup_surface_executor_readiness_report,
    build_startup_surface_mutation_contract,
    build_startup_surface_settings_report,
    execute_startup_surface_toggle,
    _json_digest,
    _plan_digest_payload,
)


class RuntimeStartupControlError(ValueError):
    """Raised when a Studio startup control action is invalid or unconfirmed."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _intent_commands(runtime_id: str, surface_id: str, intent: str) -> dict[str, str]:
    base = f"chaseos studio runtime-startup-controls --runtime {runtime_id} --surface {surface_id} --intent {intent}"
    runtime_base = f"chaseos runtime startup-surface-toggle --runtime {runtime_id} --surface {surface_id} --intent {intent}"
    return {
        "studio_preview": f"{base} --action dry-run --json",
        "studio_toggle": f"{base} --action toggle --confirm-action",
        "runtime_preview": f"{runtime_base} --dry-run --json",
        "runtime_toggle": f"{runtime_base} --confirm",
    }


def _approval_artifact_matches(payload: dict[str, Any], *, runtime_id: str, surface_id: str, intent: str, digest: str) -> bool:
    status = str(payload.get("approval_status") or payload.get("status") or payload.get("decision") or "").strip().lower()
    return bool(
        status in {"approved", "granted"}
        and payload.get("runtime_id") == runtime_id
        and payload.get("surface_id") == surface_id
        and payload.get("intent") == intent
        and str(payload.get("plan_digest_sha256") or "").lower() == digest
    )


def _matching_approval_artifacts(runtime_id: str, surface_id: str, intent: str, digest: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    if not STARTUP_SURFACE_APPROVAL_DIR.exists():
        return matches
    for path in sorted(STARTUP_SURFACE_APPROVAL_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        if _approval_artifact_matches(payload, runtime_id=runtime_id, surface_id=surface_id, intent=intent, digest=digest):
            matches.append(
                {
                    "gate_approval_id": payload.get("gate_approval_id") or path.stem,
                    "path": str(path),
                    "status": str(payload.get("approval_status") or payload.get("status") or payload.get("decision") or "approved").lower(),
                    "plan_digest_sha256": digest,
                }
            )
    return matches


@lru_cache(maxsize=64)
def _approval_readiness_material(runtime_id: str, surface_id: str, intent: str) -> dict[str, Any]:
    contract = build_startup_surface_mutation_contract(runtime_id, surface_id, intent)
    digest = _json_digest(_plan_digest_payload(contract))
    marker_path = (
        ROOT
        / "runtime"
        / "lifecycle"
        / "run"
        / "startup-surface-mutations"
        / f"{runtime_id}-{surface_id}-{intent}-{digest[:12]}.json"
    )
    return {"contract": contract, "digest": digest, "marker_path": marker_path}


def _executor_readiness_preview(runtime_id: str, surface_id: str, intent: str) -> dict[str, Any]:
    return {
        "read_only": True,
        "executor_enabled_now": False,
        "eligible_for_future_enablement": False,
        "startup_folder_mutation_enabled": False,
        "task_scheduler_mutation_enabled": False,
        "host_mutation_attempted": False,
        "approval_consumed": False,
        "idempotency_marker_written": False,
        "readiness_command": (
            "chaseos runtime startup-surface-executor-readiness "
            f"--runtime {runtime_id} --surface {surface_id} --intent {intent} "
            "--gate-approval-id <approval-id> --plan-digest <sha256-from-current-mutation-contract> --json"
        ),
        "blocked_reasons": [
            "host-mutation-backend-not-enabled",
            "operator-confirmation-policy-not-finalized",
            "rollback-recovery-policy-not-finalized",
            "post-mutation-verification-policy-not-finalized",
            "wsl-windows-host-boundary-policy-not-finalized",
            "production-approval-to-mutation-envelope-not-enabled",
        ],
        "boundary": "Executor readiness visibility only. Studio does not enable host startup mutation.",
    }


def _host_boundary_policy_preview(runtime_id: str, surface_id: str, intent: str) -> dict[str, Any]:
    return {
        "read_only": True,
        "policy_status": "blocked",
        "host_mutation_attempted": False,
        "approval_consumed": False,
        "idempotency_marker_written": False,
        "policy_command": (
            "chaseos runtime startup-surface-host-boundary-policy "
            f"--runtime {runtime_id} --surface {surface_id} --intent {intent} "
            "--gate-approval-id <approval-id> --plan-digest <sha256-from-current-mutation-contract> --json"
        ),
        "blocked_reasons": [
            "wsl-windows-host-boundary-policy-not-approved",
            "operator-confirmation-wording-not-approved",
            "rollback-policy-not-approved",
            "post-mutation-verification-evidence-not-approved",
            "host-executor-still-disabled",
        ],
        "boundary": "Host-boundary policy visibility only. Studio does not enable host startup mutation.",
    }


def _host_mutation_audit_template_preview(runtime_id: str, surface_id: str, intent: str) -> dict[str, Any]:
    return {
        "read_only": True,
        "audit_template_status": "blocked",
        "host_mutation_attempted": False,
        "approval_consumed": False,
        "idempotency_marker_written": False,
        "audit_template_command": (
            "chaseos runtime startup-surface-host-mutation-audit-template "
            f"--runtime {runtime_id} --surface {surface_id} --intent {intent} "
            "--gate-approval-id <approval-id> --plan-digest <sha256-from-current-mutation-contract> --json"
        ),
        "blocked_reasons": [
            "audit-template-not-approved",
            "success-marker-acceptance-policy-not-approved",
            "host-executor-still-disabled",
        ],
        "boundary": "Host-mutation audit template visibility only. Studio does not enable host startup mutation.",
    }


def _success_marker_evidence_verifier_preview(runtime_id: str, surface_id: str, intent: str) -> dict[str, Any]:
    return {
        "read_only": True,
        "verifier_status": "blocked",
        "candidate_evidence_present": False,
        "success_marker_allowed_now": False,
        "host_mutation_attempted": False,
        "approval_consumed": False,
        "idempotency_marker_written": False,
        "verifier_command": (
            "chaseos runtime startup-surface-success-marker-evidence-verifier "
            f"--runtime {runtime_id} --surface {surface_id} --intent {intent} "
            "--gate-approval-id <approval-id> --plan-digest <sha256-from-current-mutation-contract> --json"
        ),
        "blocked_reasons": [
            "candidate-evidence-missing",
            "audit-template-not-approved",
            "success-marker-acceptance-policy-not-approved",
            "host-executor-still-disabled",
        ],
        "boundary": "Success-marker evidence verifier visibility only. Studio does not accept success markers or mutate host startup state.",
    }


def _success_marker_acceptance_policy_preview(runtime_id: str, surface_id: str, intent: str) -> dict[str, Any]:
    return {
        "read_only": True,
        "acceptance_policy_status": "blocked",
        "success_marker_allowed_now": False,
        "success_marker_write_allowed": False,
        "host_mutation_attempted": False,
        "approval_consumed": False,
        "idempotency_marker_written": False,
        "success_marker_written": False,
        "policy_command": (
            "chaseos runtime startup-surface-success-marker-acceptance-policy "
            f"--runtime {runtime_id} --surface {surface_id} --intent {intent} "
            "--gate-approval-id <approval-id> --plan-digest <sha256-from-current-mutation-contract> --json"
        ),
        "blocked_reasons": [
            "verified-evidence-missing",
            "success-marker-acceptance-policy-not-approved",
            "success-marker-write-gate-not-approved",
            "host-executor-still-disabled",
            "approval-consumption-not-enabled-for-success-marker",
            "idempotency-marker-write-not-enabled-for-success-marker",
            "operator-final-confirmation-missing",
        ],
        "boundary": "Success-marker acceptance policy visibility only. Studio does not accept or write success markers and does not mutate host startup state.",
    }


def _approval_readiness(runtime_id: str, surface_id: str, intent: str) -> dict[str, Any]:
    material = _approval_readiness_material(runtime_id, surface_id, intent)
    contract = material["contract"]
    digest = material["digest"]
    marker_path = material["marker_path"]
    matches = _matching_approval_artifacts(runtime_id, surface_id, intent, digest)
    approval_status = "approved-found" if matches else "missing"
    first_approval_id = matches[0]["gate_approval_id"] if matches else "<approval-id>"
    return {
        "runtime_id": runtime_id,
        "surface_id": surface_id,
        "intent": intent,
        "approval_required": True,
        "approval_artifact": {
            "status": approval_status,
            "present": bool(matches),
            "matching_count": len(matches),
            "matching_approval_ids": [item["gate_approval_id"] for item in matches],
            "approval_dir": str(STARTUP_SURFACE_APPROVAL_DIR),
            "consumption_enabled": False,
            "consumption_built": False,
            "consumed": False,
        },
        "required_gate_operation": contract.get("required_gate_operation"),
        "plan_digest_sha256": digest,
        "preflight_command": (
            "chaseos runtime startup-surface-executor-preflight "
            f"--runtime {runtime_id} --surface {surface_id} --intent {intent} "
            f"--gate-approval-id {first_approval_id} --plan-digest {digest} --json"
        ),
        "idempotency": {
            "marker_path": str(marker_path),
            "marker_present": marker_path.exists(),
            "marker_written": False,
            "marker_write_enabled": False,
            "duplicate_replay_blocked_if_present": True,
        },
        "executor_readiness": _executor_readiness_preview(runtime_id, surface_id, intent),
        "host_boundary_policy": _host_boundary_policy_preview(runtime_id, surface_id, intent),
        "host_mutation_audit_template": _host_mutation_audit_template_preview(runtime_id, surface_id, intent),
        "success_marker_evidence_verifier": _success_marker_evidence_verifier_preview(runtime_id, surface_id, intent),
        "success_marker_acceptance_policy": _success_marker_acceptance_policy_preview(runtime_id, surface_id, intent),
        "live_toggle_blocked_until_approval_consumption": True,
        "read_only": True,
        "boundary": "Readiness only. Studio does not consume approval artifacts, write idempotency markers, or mutate host startup state in this model.",
    }


def _approval_readiness_preview(runtime_id: str, surface_id: str, intent: str, setting: dict[str, Any]) -> dict[str, Any]:
    digest_payload = {
        "runtime_id": runtime_id,
        "surface_id": surface_id,
        "intent": intent,
        "current_state": setting.get("current_state"),
        "target_state": "registered" if intent == "enable" and surface_id == "gateway" else ("running" if intent == "enable" else "off"),
        "contract_command": ((setting.get("commands") or {}).get(f"contract_{intent}")),
    }
    digest = _json_digest(digest_payload)
    marker_path = (
        ROOT
        / "runtime"
        / "lifecycle"
        / "run"
        / "startup-surface-mutations"
        / f"{runtime_id}-{surface_id}-{intent}-{digest[:12]}.json"
    )
    return {
        "runtime_id": runtime_id,
        "surface_id": surface_id,
        "intent": intent,
        "approval_required": True,
        "approval_artifact": {
            "status": "missing",
            "present": False,
            "matching_count": 0,
            "matching_approval_ids": [],
            "approval_dir": str(STARTUP_SURFACE_APPROVAL_DIR),
            "consumption_enabled": False,
            "consumption_built": False,
            "consumed": False,
        },
        "required_gate_operation": f"lifecycle.startup_surface.{surface_id}.{intent}",
        "model_plan_digest_sha256": digest,
        "plan_digest_sha256": None,
        "preflight_command": (
            "chaseos runtime startup-surface-executor-preflight "
            f"--runtime {runtime_id} --surface {surface_id} --intent {intent} "
            "--gate-approval-id <approval-id> --plan-digest <sha256-from-current-mutation-contract> --json"
        ),
        "contract_command": (setting.get("commands") or {}).get(f"contract_{intent}"),
        "idempotency": {
            "marker_path": str(marker_path),
            "marker_present": marker_path.exists(),
            "marker_written": False,
            "marker_write_enabled": False,
            "duplicate_replay_blocked_if_present": True,
        },
        "executor_readiness": _executor_readiness_preview(runtime_id, surface_id, intent),
        "host_boundary_policy": _host_boundary_policy_preview(runtime_id, surface_id, intent),
        "host_mutation_audit_template": _host_mutation_audit_template_preview(runtime_id, surface_id, intent),
        "success_marker_evidence_verifier": _success_marker_evidence_verifier_preview(runtime_id, surface_id, intent),
        "success_marker_acceptance_policy": _success_marker_acceptance_policy_preview(runtime_id, surface_id, intent),
        "live_toggle_blocked_until_approval_consumption": True,
        "read_only": True,
        "boundary": "Preview readiness only. Use the contract/preflight commands for exact digest validation. Studio does not consume approval artifacts, write idempotency markers, or mutate host startup state in this model.",
    }


def _approval_readiness_unavailable(runtime_id: str, surface_id: str, intent: str) -> dict[str, Any]:
    return {
        "runtime_id": runtime_id,
        "surface_id": surface_id,
        "intent": intent,
        "approval_required": False,
        "approval_artifact": {
            "status": "not-applicable",
            "present": False,
            "matching_count": 0,
            "matching_approval_ids": [],
            "approval_dir": str(STARTUP_SURFACE_APPROVAL_DIR),
            "consumption_enabled": False,
            "consumption_built": False,
            "consumed": False,
        },
        "required_gate_operation": None,
        "plan_digest_sha256": None,
        "preflight_command": None,
        "idempotency": {
            "marker_path": None,
            "marker_present": False,
            "marker_written": False,
            "marker_write_enabled": False,
            "duplicate_replay_blocked_if_present": True,
        },
        "executor_readiness": _executor_readiness_preview(runtime_id, surface_id, intent),
        "host_boundary_policy": _host_boundary_policy_preview(runtime_id, surface_id, intent),
        "host_mutation_audit_template": _host_mutation_audit_template_preview(runtime_id, surface_id, intent),
        "success_marker_evidence_verifier": _success_marker_evidence_verifier_preview(runtime_id, surface_id, intent),
        "success_marker_acceptance_policy": _success_marker_acceptance_policy_preview(runtime_id, surface_id, intent),
        "live_toggle_blocked_until_approval_consumption": True,
        "read_only": True,
        "boundary": "Surface is not currently Studio-toggleable; no approval artifact is consumed and no idempotency marker is written.",
    }


def _surface_card(runtime: dict[str, Any], setting: dict[str, Any]) -> dict[str, Any]:
    runtime_id = str(runtime.get("runtime_id") or "")
    surface_id = str(setting.get("surface_id") or "")
    can_toggle = bool(
        setting.get("user_manageable")
        and (setting.get("studio_cli_control_enabled") or setting.get("cli_mutation_enabled"))
    )
    readiness = {
        "enable": _approval_readiness_preview(runtime_id, surface_id, "enable", setting) if can_toggle else _approval_readiness_unavailable(runtime_id, surface_id, "enable"),
        "disable": _approval_readiness_preview(runtime_id, surface_id, "disable", setting) if can_toggle else _approval_readiness_unavailable(runtime_id, surface_id, "disable"),
    }
    return {
        "runtime_id": runtime_id,
        "runtime_name": runtime.get("runtime_name"),
        "surface_id": surface_id,
        "ui_label": setting.get("ui_label") or surface_id,
        "current_state": setting.get("current_state"),
        "target_states": {
            "enable": "registered" if surface_id == "gateway" else "running",
            "disable": "off",
        },
        "user_manageable": bool(setting.get("user_manageable")),
        "cli_mutation_enabled": bool(setting.get("cli_mutation_enabled")),
        "studio_cli_control_enabled": bool(setting.get("studio_cli_control_enabled") or can_toggle),
        "studio_control_enabled": can_toggle,
        "studio_visual_toggle_built": True,
        "requires_confirm_action": True,
        "approval_readiness": readiness,
        "startup_registration_kind": setting.get("startup_registration_kind"),
        "launch_profile": setting.get("launch_profile"),
        "managed_target_launcher": setting.get("managed_target_launcher"),
        "commands": {
            "enable": _intent_commands(runtime_id, surface_id, "enable"),
            "disable": _intent_commands(runtime_id, surface_id, "disable"),
        },
        "boundary": "Studio CLI wraps the lifecycle startup-surface command; it does not write host startup state directly.",
    }


def build_runtime_startup_controls_model(
    vault_root: str | Path,
    runtime_id: str | None = None,
    *,
    probe_processes: bool = True,
) -> dict[str, Any]:
    """Return a Studio-ready startup-controls model for runtimes and surfaces."""
    vault = Path(vault_root).resolve()
    settings_report = build_startup_surface_settings_report(
        runtime_id or "all",
        probe_processes=probe_processes,
    )
    surface_cards: list[dict[str, Any]] = []
    for runtime in settings_report.get("runtimes", []):
        for setting in runtime.get("settings", []):
            surface_cards.append(_surface_card(runtime, setting))

    return {
        "ok": not bool(settings_report.get("errors")),
        "surface": "studio_runtime_startup_controls",
        "title": "Runtime Startup Controls",
        "generated_at_utc": _utc_now_iso(),
        "vault_root": str(vault),
        "runtime_filter": runtime_id or "all",
        "read_only": True,
        "process_probe_enabled": bool(probe_processes),
        "settings_write_enabled": bool(settings_report.get("settings_write_enabled")),
        "mutation_actions_enabled": any(card.get("studio_control_enabled") for card in surface_cards),
        "studio_visual_toggle_built": True,
        "approval_boundary": {
            "approval_required_before_confirmed_mutation": True,
            "approval_artifact_preflight_built": True,
            "approval_artifact_consumption_built": False,
            "approval_artifact_consumption_enabled": False,
            "idempotency_marker_preflight_built": True,
            "idempotency_marker_write_built": False,
            "idempotency_marker_write_enabled": False,
            "confirmed_host_mutation_blocked_until_boundary_settled": True,
            "executor_readiness_packet_built": True,
            "executor_enabled_now": False,
            "startup_folder_mutation_enabled": False,
            "task_scheduler_mutation_enabled": False,
            "boundary": "Model exposes approval/idempotency/executor-readiness posture only; it does not consume artifacts, write markers, or mutate host startup state.",
        },
        "runtime_count": settings_report.get("runtime_count"),
        "surface_count": len(surface_cards),
        "surface_cards": surface_cards,
        "source_settings_report": settings_report,
        "boundary": {
            "writes_vault": False,
            "writes_host_startup": False,
            "live_toggle_requires_confirm_action": True,
            "uses_runtime_lifecycle_executor": True,
            "canonical_mutation_allowed": False,
            "visual_studio_ui_built": True,
        },
        "errors": settings_report.get("errors") or [],
    }


def run_runtime_startup_control_action(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    surface_id: str | None = None,
    intent: str | None = None,
    action: str = "model",
    confirm_action: bool = False,
    requested_by: str = "studio",
    gate_approval_id: str | None = None,
    plan_digest: str | None = None,
) -> dict[str, Any]:
    """Run a Studio startup control action.

    Supported actions:
    - model: read-only UI model
    - dry-run: lifecycle executor dry-run for one concrete surface/intent
    - toggle: live lifecycle executor; requires confirm_action
    """
    normalized_action = (action or "model").strip().lower()
    if normalized_action == "model":
        return build_runtime_startup_controls_model(vault_root, runtime_id)

    normalized_runtime = (runtime_id or "").strip().lower()
    normalized_surface = (surface_id or "").strip()
    normalized_intent = (intent or "").strip().lower()
    if not normalized_runtime or normalized_runtime in {"all", "*"}:
        raise RuntimeStartupControlError("--runtime must name one runtime for dry-run or toggle actions")
    if not normalized_surface:
        raise RuntimeStartupControlError("--surface is required for dry-run or toggle actions")
    if normalized_intent not in {"enable", "disable"}:
        raise RuntimeStartupControlError("--intent must be enable or disable")

    dry_run = normalized_action == "dry-run"
    approval_gate: dict[str, Any] | None = None
    lifecycle_toggle_invoked = False
    host_mutation_attempted = False
    if normalized_action == "toggle":
        if not confirm_action:
            raise RuntimeStartupControlError("--confirm-action is required for live startup toggles")
        normalized_gate_approval_id = (gate_approval_id or "").strip()
        normalized_plan_digest = (plan_digest or "").strip().lower()
        if not normalized_gate_approval_id or not normalized_plan_digest:
            raise RuntimeStartupControlError(
                "confirmed Studio startup toggles require gate approval material: --gate-approval-id and --plan-digest"
            )
        approval_gate = build_startup_surface_approval_consumption(
            normalized_runtime,
            normalized_surface,
            normalized_intent,
            gate_approval_id=normalized_gate_approval_id,
            plan_digest=normalized_plan_digest,
            consumed_by=requested_by or "studio",
            write=False,
        )
        approval_gate = {
            **approval_gate,
            "write_enabled": False,
            "approval_consumed": False,
            "idempotency_marker_written": False,
        }
        if not approval_gate.get("ready"):
            blockers = approval_gate.get("blocked_reasons") or []
            raise RuntimeStartupControlError(
                "confirmed Studio startup toggle approval gate is not ready: " + ", ".join(str(item) for item in blockers)
            )
        result = {
            "before_state": None,
            "after_state": None,
            "requested_state": normalized_intent,
            "dry_run": False,
            "approval_gate_checked": True,
            "approval_gate_consumed": False,
            "idempotency_marker_written": False,
            "host_mutation_attempted": False,
            "startup_surface_mutation_executed": False,
            "message": "approval/idempotency gate checked read-only; Studio does not consume approvals, write idempotency markers, or mutate host startup state",
        }
        dry_run = False
    elif not dry_run:
        raise RuntimeStartupControlError("--action must be model, dry-run, or toggle")
    else:
        result = execute_startup_surface_toggle(
            normalized_runtime,
            normalized_surface,
            normalized_intent,
            confirm=bool(confirm_action),
            dry_run=dry_run,
            requested_by=requested_by or "studio",
        )
        lifecycle_toggle_invoked = True
        host_mutation_attempted = not dry_run

    approval_readiness = _approval_readiness(normalized_runtime, normalized_surface, normalized_intent)
    status = "dry_run_complete" if dry_run else "approval_gate_ready_host_mutation_blocked"
    return {
        "ok": True,
        "surface": "studio_runtime_startup_controls",
        "title": "Runtime Startup Controls",
        "generated_at_utc": _utc_now_iso(),
        "runtime_id": normalized_runtime,
        "surface_id": normalized_surface,
        "intent": normalized_intent,
        "action": {
            "id": normalized_action,
            "status": status,
            "confirm_action": bool(confirm_action),
            "writes_host_startup": False if normalized_action == "toggle" else not dry_run,
            "host_mutation_attempted": host_mutation_attempted,
            "lifecycle_toggle_invoked": lifecycle_toggle_invoked,
            "approval_readiness": approval_readiness,
            "approval_gate": approval_gate,
            "result": result,
        },
        "approval_boundary": {
            "approval_required_before_confirmed_mutation": True,
            "approval_artifact_preflight_built": True,
            "approval_artifact_consumption_built": False,
            "approval_artifact_consumption_enabled": False,
            "idempotency_marker_preflight_built": True,
            "idempotency_marker_write_built": False,
            "idempotency_marker_write_enabled": False,
            "confirmed_host_mutation_blocked_until_boundary_settled": True,
        },
        "boundary": {
            "uses_runtime_lifecycle_executor": True,
            "direct_studio_host_write": False,
            "canonical_mutation_allowed": False,
            "visual_studio_ui_built": True,
        },
    }
