"""Local-only Studio Acquisition Intake Cockpit model and static rendering.

This Phase 10A0 foothold wraps existing Phase 9 acquisition/import surfaces. It
intentionally does not launch a browser, create a server, call providers, deliver
externally, or mutate canonical notes. The only write helper here is explicit
operator file import into the already-declared StrikeZone local/import folders.
"""

from __future__ import annotations

import html
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.acquisition.builder import AcquisitionBuildError
from runtime.acquisition.research_imports import (
    STRIKEZONE_RESEARCH_DROP_ROOT,
    ResearchInboxImportError,
    ResearchImportPreviewError,
    ResearchPreviewPromotionError,
    ResearchRepositoryTemplateError,
    ResearchSBPConsumptionVerificationError,
    STRIKEZONE_OPTIONAL_RESEARCH_SOURCE_CLASSES,
    STRIKEZONE_RECOMMENDED_RESEARCH_SOURCE_CLASSES,
    STRIKEZONE_RESEARCH_DROP_FOLDERS,
    STRIKEZONE_RESEARCH_INBOX_FOLDERS,
    initialize_research_repository_template,
    import_research_inbox,
    import_staged_research_file,
    inspect_research_import_status,
    preview_research_imports,
    promote_research_preview_pack,
    verify_research_preview_sbp_consumption,
)
from runtime.acquisition.intake_normalization import (
    SUPPORTED_INTAKE_SUFFIXES,
    standardize_research_intake_file,
    supported_intake_suffixes,
)
from runtime.acquisition.validators import AcquisitionValidationError

_COCKPIT_ID = "studio_acquisition_intake_cockpit"
_ACTION_ALIASES = {
    "model": "model",
    "status": "model",
    "init-repository": "init_repository",
    "init_repository": "init_repository",
    "import-file": "import_file",
    "import_file": "import_file",
    "import-staged-file": "import_staged_file",
    "import_staged_file": "import_staged_file",
    "import-inbox": "import_inbox",
    "import_inbox": "import_inbox",
    "open-local-path": "open_local_path",
    "open_local_path": "open_local_path",
    "clear-active-intake": "clear_active_intake",
    "clear_active_intake": "clear_active_intake",
    "reset-active-intake": "clear_active_intake",
    "reset_active_intake": "clear_active_intake",
    "preview": "preview_read_only",
    "preview-read-only": "preview_read_only",
    "preview_read_only": "preview_read_only",
    "preview-write": "preview_write",
    "preview_write": "preview_write",
    "promote-reviewed-preview": "promote_reviewed_preview",
    "promote_reviewed_preview": "promote_reviewed_preview",
    "verify-research-sbp": "verify_research_sbp",
    "verify_research_sbp": "verify_research_sbp",
    "pulse-schedule-runner-status": "pulse_schedule_runner_status",
    "pulse-schedule-runner-proof": "pulse_schedule_runner_status",
    "pulse_schedule_runner_status": "pulse_schedule_runner_status",
    "pulse-schedule-live-runner-preview": "pulse_schedule_live_runner_preview",
    "pulse-native-schedule-live-runner-preview": "pulse_schedule_live_runner_preview",
    "pulse_schedule_live_runner_preview": "pulse_schedule_live_runner_preview",
    "pulse-schedule-live-runner-execute": "pulse_schedule_live_runner_execute",
    "pulse-native-schedule-live-runner-execute": "pulse_schedule_live_runner_execute",
    "pulse_schedule_live_runner_execute": "pulse_schedule_live_runner_execute",
    "pulse-schedule-runtime-dispatch-proof": "pulse_schedule_runtime_dispatch_proof",
    "pulse-native-schedule-runtime-dispatch-proof": "pulse_schedule_runtime_dispatch_proof",
    "pulse_schedule_runtime_dispatch_proof": "pulse_schedule_runtime_dispatch_proof",
    "pulse-schedule-runtime-dispatch-write-proof": "pulse_schedule_runtime_dispatch_write_proof",
    "pulse-native-schedule-runtime-dispatch-write-proof": "pulse_schedule_runtime_dispatch_write_proof",
    "pulse_schedule_runtime_dispatch_write_proof": "pulse_schedule_runtime_dispatch_write_proof",
    "pulse-schedule-activation-gate": "pulse_schedule_activation_gate",
    "pulse-native-schedule-activation-gate": "pulse_schedule_activation_gate",
    "pulse_schedule_activation_gate": "pulse_schedule_activation_gate",
    "pulse-schedule-activation-request": "pulse_schedule_activation_request",
    "pulse-native-schedule-activation-request": "pulse_schedule_activation_request",
    "pulse_schedule_activation_request": "pulse_schedule_activation_request",
    "pulse-schedule-run-queue-audit-proof": "pulse_schedule_run_queue_audit_proof",
    "pulse-native-schedule-run-queue-audit-proof": "pulse_schedule_run_queue_audit_proof",
    "pulse_schedule_run_queue_audit_proof": "pulse_schedule_run_queue_audit_proof",
    "pulse-schedule-run-queue-audit-write-proof": "pulse_schedule_run_queue_audit_write_proof",
    "pulse-native-schedule-run-queue-audit-write-proof": "pulse_schedule_run_queue_audit_write_proof",
    "pulse_schedule_run_queue_audit_write_proof": "pulse_schedule_run_queue_audit_write_proof",
    "pulse-schedule-supervised-activation-execution-proof": "pulse_schedule_supervised_activation_execution_proof",
    "pulse-native-schedule-supervised-activation-execution-proof": "pulse_schedule_supervised_activation_execution_proof",
    "pulse_schedule_supervised_activation_execution_proof": "pulse_schedule_supervised_activation_execution_proof",
    "pulse-schedule-activation-execution-proof": "pulse_schedule_supervised_activation_execution_proof",
    "pulse-schedule-supervised-activation-execution-write-proof": (
        "pulse_schedule_supervised_activation_execution_write_proof"
    ),
    "pulse-native-schedule-supervised-activation-execution-write-proof": (
        "pulse_schedule_supervised_activation_execution_write_proof"
    ),
    "pulse_schedule_supervised_activation_execution_write_proof": (
        "pulse_schedule_supervised_activation_execution_write_proof"
    ),
    "pulse-schedule-activation-execution-write-proof": "pulse_schedule_supervised_activation_execution_write_proof",
    "pulse-enqueue-preview": "pulse_enqueue_preview",
    "pulse-review-contract-preview": "pulse_enqueue_preview",
    "pulse_enqueue_preview": "pulse_enqueue_preview",
    "pulse-enqueue-approved": "pulse_enqueue_approved",
    "pulse-review-contract-enqueue": "pulse_enqueue_approved",
    "pulse_enqueue_approved": "pulse_enqueue_approved",
}
_WRITE_ACTIONS = {
    "init_repository",
    "import_file",
    "import_staged_file",
    "import_inbox",
    "clear_active_intake",
    "preview_write",
    "promote_reviewed_preview",
    "pulse_enqueue_approved",
    "pulse_schedule_activation_request",
    "pulse_schedule_live_runner_execute",
    "pulse_schedule_runtime_dispatch_write_proof",
    "pulse_schedule_run_queue_audit_write_proof",
    "pulse_schedule_supervised_activation_execution_write_proof",
}
_PULSE_REVIEW_REQUIRED_EVIDENCE = {
    "operator_approved": "--operator-approved",
    "gate_policy_defined": "--gate-policy-defined",
    "external_sender_allowance_present": "--external-sender-allowance-present",
    "duplicate_work_fingerprint_reviewed": "--duplicate-work-fingerprint-reviewed",
}
_PULSE_ENQUEUE_WRITE_ROOTS = [
    "07_LOGS/Pulse-Decks/agent-bus-approval-requests/",
    "07_LOGS/Pulse-Decks/agent-bus-enqueue-results/",
    "runtime/agent_bus/",
]
_PULSE_SCHEDULE_ACTIVATION_WRITE_ROOTS = [
    "07_LOGS/Pulse-Decks/native-schedule-activation-requests/",
]
_PULSE_SCHEDULE_RUN_QUEUE_WRITE_ROOTS = [
    "07_LOGS/Pulse-Decks/native-schedule-run-queue-audit-proof/",
]
_PULSE_SCHEDULE_LIVE_RUNNER_WRITE_ROOTS = [
    "07_LOGS/Pulse-Decks/native-schedule-run-queue/",
    "07_LOGS/Pulse-Decks/native-schedule-audit/",
    "07_LOGS/Pulse-Decks/native-schedule-runs/",
]
_PULSE_SCHEDULE_RUNTIME_DISPATCH_WRITE_ROOTS = [
    "07_LOGS/Pulse-Decks/native-schedule-runtime-dispatch-proof/",
]
_PULSE_SCHEDULE_SUPERVISED_ACTIVATION_WRITE_ROOTS = [
    "07_LOGS/Pulse-Decks/native-schedule-activation-executions/",
]
_PULSE_SCHEDULE_EVIDENCE_FLAGS = {
    "operator_approval_ref": "--operator-approval-ref",
    "permission_envelope_ref": "--permission-envelope-ref",
    "run_queue_scope_ref": "--run-queue-scope-ref",
    "audit_identity_ref": "--audit-identity-ref",
    "runtime_adapter_scope_ref": "--runtime-adapter-scope-ref",
    "rollback_plan_ref": "--rollback-plan-ref",
    "external_scheduler_denial_ref": "--external-scheduler-denial-ref",
    "canonical_writeback_denial_ref": "--canonical-writeback-denial-ref",
}
_REQUIRED_MANUAL_TEST_ACTIONS = {
    "init-repository",
    "import-inbox",
    "preview-read-only",
    "preview-write",
    "promote-reviewed-preview",
    "verify-research-sbp",
}
_EXPECTED_RESEARCH_SOURCE_CLASSES = [
    *STRIKEZONE_RECOMMENDED_RESEARCH_SOURCE_CLASSES,
    *STRIKEZONE_OPTIONAL_RESEARCH_SOURCE_CLASSES,
]
_ACTIVE_INTAKE_CLEAR_LEDGER_PATH = "runtime/acquisition/state/strikezone-active-intake-clears.jsonl"


class CockpitActionError(RuntimeError):
    """Raised when a governed Studio cockpit action cannot run."""


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _require_strikezone(profile: str) -> None:
    if profile != "strikezone":
        raise ValueError("only the strikezone profile is supported by the Phase 10A0 cockpit")


def _authority_boundary() -> dict[str, Any]:
    return {
        "browser_scope": [],
        "network_scope": [],
        "mcp_scope_changed": False,
        "canonical_mutation_allowed": False,
        "delivery_changed": False,
        "cron_or_scheduler_changed": False,
        "live_provider_calls_allowed": False,
    }


def _command_controls(profile: str, status: dict[str, Any]) -> list[dict[str, Any]]:
    latest = status.get("latest_pointer") or {}
    latest_preview_candidate = status.get("latest_preview_candidate") or {}
    readiness = status.get("readiness", {})
    if readiness.get("reviewed_preview_promoted"):
        briefing_input = latest.get("briefing_ready_input_set_path") or "<reviewed-preview-briefing-ready-input-set>"
    elif latest_preview_candidate.get("briefing_ready_input_set_path"):
        briefing_input = latest_preview_candidate["briefing_ready_input_set_path"]
    else:
        briefing_input = "<preview-briefing-ready-input-set>"
    has_sources = bool(status.get("source_count", 0))
    has_inbox_candidates = bool(status.get("inbox_candidate_count", 0))
    has_promoted_preview = bool(readiness.get("reviewed_preview_promoted"))
    has_preview_candidate = bool(latest_preview_candidate.get("valid_for_reviewed_promotion"))
    repository_template = status.get("repository_template") or {}
    repository_ready = bool(readiness.get("repository_template_ready") or repository_template.get("repository_ready"))
    return [
        {
            "id": "init_repository",
            "label": "Initialize research repository template",
            "command": f"chaseos acquisition init-research-repository --profile {profile} --confirm-action --json",
            "studio_action": "init-repository",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action init-repository --confirm-action --json"
            ),
            "write_action": True,
            "requires_confirmation": True,
            "enabled": not repository_ready,
            "confirmation_flag": "--confirm-action",
            "writes_only": [
                "runtime/acquisition/manual/strikezone/",
                "runtime/acquisition/manual/strikezone/_inbox/",
                "runtime/acquisition/manual/strikezone/templates/",
            ],
            "template_ready": repository_ready,
            "reason_if_disabled": "Research repository template already exists." if repository_ready else None,
        },
        {
            "id": "import_inbox",
            "label": "Import staged inbox files",
            "command": f"chaseos acquisition import-research-inbox --profile {profile} --confirm-action --json",
            "studio_action": "import-inbox",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action import-inbox --confirm-action --json"
            ),
            "write_action": True,
            "requires_confirmation": True,
            "enabled": has_inbox_candidates,
            "confirmation_flag": "--confirm-action",
            "writes_only": ["runtime/acquisition/manual/strikezone/<source_class>/"],
            "reason_if_disabled": "Stage files under _inbox/<source_class>/ first." if not has_inbox_candidates else None,
        },
        {
            "id": "clear_active_intake",
            "label": "Clear current intake (archive active files)",
            "command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action clear-active-intake --confirm-action --json"
            ),
            "studio_action": "clear-active-intake",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action clear-active-intake --confirm-action --json"
            ),
            "write_action": True,
            "requires_confirmation": True,
            "enabled": has_sources or has_inbox_candidates,
            "confirmation_flag": "--confirm-action",
            "writes_only": [
                "runtime/acquisition/manual/strikezone/_archive/<clear-id>/",
                _ACTIVE_INTAKE_CLEAR_LEDGER_PATH,
            ],
            "moves_only": True,
            "deletes_files": False,
            "reason_if_disabled": (
                "No active imported or staged intake files to archive."
                if not (has_sources or has_inbox_candidates)
                else None
            ),
        },
        {
            "id": "preview_read_only",
            "label": "Run read-only preview",
            "command": f"chaseos acquisition preview-research --profile {profile} --json",
            "studio_action": "preview-read-only",
            "studio_command": f"chaseos studio acquisition-cockpit --profile {profile} --action preview-read-only --json",
            "write_action": False,
            "requires_confirmation": False,
            "enabled": has_sources,
            "reason_if_disabled": "Add at least one declared research source file first." if not has_sources else None,
        },
        {
            "id": "preview_write",
            "label": "Write runtime-local preview pack",
            "command": f"chaseos acquisition preview-research --profile {profile} --write --json",
            "studio_action": "preview-write",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action preview-write --confirm-action --json"
            ),
            "write_action": True,
            "requires_confirmation": True,
            "enabled": has_sources,
            "confirmation_flag": "--confirm-action",
            "writes_only": ["runtime/acquisition/packs/<date>-strikezone-research-import-preview/"],
            "reason_if_disabled": "Add at least one declared research source file first." if not has_sources else None,
        },
        {
            "id": "promote_reviewed_preview",
            "label": "Promote reviewed preview pointer",
            "command": (
                f"chaseos acquisition promote-research-preview --profile {profile} "
                f"--briefing-input {briefing_input} --reviewed --json"
            ),
            "studio_action": "promote-reviewed-preview",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} --action promote-reviewed-preview "
                f"--briefing-input {briefing_input} --reviewed --confirm-action --json"
            ),
            "briefing_input": briefing_input if has_preview_candidate or readiness.get("reviewed_preview_promoted") else "",
            "latest_preview_candidate": latest_preview_candidate or None,
            "write_action": True,
            "requires_confirmation": True,
            "enabled": has_preview_candidate or bool(readiness.get("reviewed_preview_promoted")),
            "confirmation_flag": "--confirm-action",
            "writes_only": ["runtime/acquisition/packs/strikezone-latest.json"],
            "reason_if_disabled": (
                "Write and review a preview pack before promotion." if not has_preview_candidate else None
            ),
        },
        {
            "id": "verify_research_sbp",
            "label": "Verify SBP consumption",
            "command": f"chaseos acquisition verify-research-sbp --profile {profile} --json",
            "studio_action": "verify-research-sbp",
            "studio_command": f"chaseos studio acquisition-cockpit --profile {profile} --action verify-research-sbp --json",
            "write_action": False,
            "requires_confirmation": False,
            "enabled": has_promoted_preview,
            "reason_if_disabled": "Promote a reviewed preview before running the default SBP verifier." if not has_promoted_preview else None,
        },
    ]


def _pulse_schedule_runner_status(vault: Path) -> dict[str, Any]:
    """Return Studio-safe status for Pulse runner proof plus governed live runner."""

    try:
        from runtime.pulse.native_schedule_runner_proof import build_pulse_native_schedule_runner_proof

        proof = build_pulse_native_schedule_runner_proof(
            vault,
            simulate_missed_run=True,
            write=False,
        ).to_dict()
    except Exception as exc:  # noqa: BLE001 - status surfaces must degrade cleanly.
        return {
            "surface": "studio_pulse_schedule_runner_status",
            "available": False,
            "status": "unavailable",
            "error": str(exc),
            "live_runner_built": False,
            "live_runner_status": "BLOCKED",
            "schedule_activation_allowed": False,
            "schedule_daemon_started": False,
            "runner_proof": None,
            "blockers": ["Pulse native schedule manifests are unavailable to this vault snapshot."],
        }

    try:
        from runtime.pulse.native_schedule_live_runner import build_pulse_native_schedule_live_runner

        live = build_pulse_native_schedule_live_runner(
            vault,
            force_due=True,
        ).to_dict()
    except Exception as exc:  # noqa: BLE001 - proof surface stays available if live runner degrades.
        live = {
            "runner_status": "unavailable",
            "error": str(exc),
            "active_schedule_count": 0,
            "due_schedule_count": 0,
            "queue_entry_count": 0,
            "audit_event_count": 0,
            "write_executed": False,
            "run_queue_write_executed": False,
            "audit_event_write_executed": False,
            "schedule_daemon_started": False,
            "runtime_dispatch_allowed": False,
            "workflow_execution_allowed": False,
            "canonical_writeback_allowed": False,
            "targets": [],
        }

    blockers: list[str] = []
    for schedule in proof.get("schedules", []):
        blockers.extend(str(item) for item in schedule.get("blockers", []) if item)
    for target in live.get("targets", []):
        blockers.extend(str(item) for item in target.get("blockers", []) if item)
    return {
        "surface": "studio_pulse_schedule_runner_status",
        "available": True,
        "status": proof.get("runner_status"),
        "live_runner_built": live.get("runner_status") != "unavailable",
        "live_runner_status": live.get("runner_status"),
        "live_active_schedule_count": int(live.get("active_schedule_count", 0) or 0),
        "live_due_schedule_count": int(live.get("due_schedule_count", 0) or 0),
        "live_queue_entry_count": int(live.get("queue_entry_count", 0) or 0),
        "live_audit_event_count": int(live.get("audit_event_count", 0) or 0),
        "live_run_queue_write_executed": bool(live.get("run_queue_write_executed")),
        "live_audit_event_write_executed": bool(live.get("audit_event_write_executed")),
        "live_runner": live,
        "schedule_count": proof.get("schedule_count", 0),
        "ready_schedule_count": proof.get("ready_schedule_count", 0),
        "enabled_schedule_count": proof.get("enabled_schedule_count", 0),
        "schedule_activation_allowed": bool(proof.get("schedule_activation_allowed")),
        "schedule_daemon_started": bool(proof.get("schedule_daemon_started")),
        "runner_proof": proof,
        "blockers": sorted(set(blockers)),
        "next_recommended_pass": proof.get("next_recommended_pass"),
    }


def _pulse_schedule_activation_gate_status(vault: Path) -> dict[str, Any]:
    """Return Studio-safe status for the existing Pulse supervised activation gate."""

    try:
        from runtime.pulse.native_schedule_activation_gate import build_pulse_native_schedule_activation_gate

        gate = build_pulse_native_schedule_activation_gate(vault).to_dict()
    except Exception as exc:  # noqa: BLE001 - status surfaces must degrade cleanly.
        return {
            "surface": "studio_pulse_schedule_activation_gate",
            "available": False,
            "status": "unavailable",
            "gate_status": "unavailable",
            "error": str(exc),
            "missing_evidence_slots": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS),
            "missing_evidence_count": len(_PULSE_SCHEDULE_EVIDENCE_FLAGS),
            "required_evidence_flags": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS.values()),
            "write_root": _PULSE_SCHEDULE_ACTIVATION_WRITE_ROOTS[0],
            "request_action_id": "pulse-schedule-activation-request",
            "schedule_activation_allowed": False,
            "schedule_manifest_write_allowed": False,
            "schedule_daemon_started": False,
            "activation_request_write_available": False,
            "result": None,
        }

    missing = list(gate.get("missing_evidence_slots") or [])
    return {
        "surface": "studio_pulse_schedule_activation_gate",
        "available": True,
        "status": gate.get("gate_status"),
        "gate_status": gate.get("gate_status"),
        "schedule_ids": list(gate.get("schedule_ids") or []),
        "schedule_count": int(gate.get("schedule_count", 0) or 0),
        "ready_schedule_count": int(gate.get("ready_schedule_count", 0) or 0),
        "enabled_schedule_count": int(gate.get("enabled_schedule_count", 0) or 0),
        "missing_evidence_slots": missing,
        "missing_evidence_count": len(missing),
        "required_evidence_flags": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS.values()),
        "write_root": str(gate.get("allowed_write_root") or _PULSE_SCHEDULE_ACTIVATION_WRITE_ROOTS[0]),
        "request_action_id": "pulse-schedule-activation-request",
        "schedule_activation_allowed": bool(gate.get("schedule_activation_allowed")),
        "schedule_manifest_write_allowed": bool(gate.get("schedule_manifest_write_allowed")),
        "schedule_daemon_started": bool(gate.get("schedule_daemon_started")),
        "activation_request_write_available": True,
        "next_recommended_pass": gate.get("next_recommended_pass"),
        "result": gate,
    }


def _pulse_schedule_runtime_dispatch_proof_status(vault: Path) -> dict[str, Any]:
    """Return Studio-safe status for the proof-only runtime dispatch packet."""

    try:
        from runtime.pulse.native_schedule_runtime_dispatch_proof import (
            build_pulse_native_schedule_runtime_dispatch_proof,
        )

        proof = build_pulse_native_schedule_runtime_dispatch_proof(vault).to_dict()
    except Exception as exc:  # noqa: BLE001 - status surfaces must degrade cleanly.
        return {
            "surface": "studio_pulse_schedule_runtime_dispatch_proof",
            "available": False,
            "status": "unavailable",
            "dispatch_status": "unavailable",
            "error": str(exc),
            "queue_file_exists": False,
            "queue_entry_count": 0,
            "pending_entry_count": 0,
            "dispatch_target_count": 0,
            "ready_dispatch_target_count": 0,
            "blocked_dispatch_target_count": 0,
            "missing_workflow_count": 0,
            "write_root": _PULSE_SCHEDULE_RUNTIME_DISPATCH_WRITE_ROOTS[0],
            "write_action_id": "pulse-schedule-runtime-dispatch-write-proof",
            "execute_dispatch_action_exposed": False,
            "run_queue_status_write_executed": False,
            "runtime_dispatch_allowed": False,
            "runtime_dispatch_started": False,
            "workflow_execution_allowed": False,
            "workflow_execution_started": False,
            "provider_or_connector_call_allowed": False,
            "canonical_writeback_allowed": False,
            "result": None,
        }

    blockers: list[str] = []
    for target in proof.get("dispatch_targets", []):
        blockers.extend(str(item) for item in target.get("blockers", []) if item)
    return {
        "surface": "studio_pulse_schedule_runtime_dispatch_proof",
        "available": True,
        "status": proof.get("dispatch_status"),
        "dispatch_status": proof.get("dispatch_status"),
        "queue_file_exists": bool(proof.get("queue_file_exists")),
        "queue_entry_count": int(proof.get("queue_entry_count", 0) or 0),
        "pending_entry_count": int(proof.get("pending_entry_count", 0) or 0),
        "invalid_queue_line_count": int(proof.get("invalid_queue_line_count", 0) or 0),
        "dispatch_target_count": int(proof.get("dispatch_target_count", 0) or 0),
        "ready_dispatch_target_count": int(proof.get("ready_dispatch_target_count", 0) or 0),
        "blocked_dispatch_target_count": int(proof.get("blocked_dispatch_target_count", 0) or 0),
        "missing_workflow_count": int(proof.get("missing_workflow_count", 0) or 0),
        "write_root": str(proof.get("allowed_write_root") or _PULSE_SCHEDULE_RUNTIME_DISPATCH_WRITE_ROOTS[0]),
        "write_action_id": "pulse-schedule-runtime-dispatch-write-proof",
        "execute_dispatch_action_exposed": bool(proof.get("execute_dispatch_action_exposed")),
        "run_queue_status_write_executed": bool(proof.get("run_queue_status_write_executed")),
        "runtime_dispatch_allowed": bool(proof.get("runtime_dispatch_allowed")),
        "runtime_dispatch_started": bool(proof.get("runtime_dispatch_started")),
        "workflow_execution_allowed": bool(proof.get("workflow_execution_allowed")),
        "workflow_execution_started": bool(proof.get("workflow_execution_started")),
        "provider_or_connector_call_allowed": bool(proof.get("provider_or_connector_call_allowed")),
        "canonical_writeback_allowed": bool(proof.get("canonical_writeback_allowed")),
        "next_recommended_pass": proof.get("next_recommended_pass"),
        "blockers": sorted(set(blockers)),
        "result": proof,
    }


def _pulse_schedule_run_queue_audit_proof_status(vault: Path) -> dict[str, Any]:
    """Return Studio-safe status for the existing proof-only run-queue/audit packet."""

    try:
        from runtime.pulse.native_schedule_run_queue_audit_proof import (
            build_pulse_native_schedule_run_queue_audit_proof,
        )

        proof = build_pulse_native_schedule_run_queue_audit_proof(vault).to_dict()
    except Exception as exc:  # noqa: BLE001 - status surfaces must degrade cleanly.
        return {
            "surface": "studio_pulse_schedule_run_queue_audit_proof",
            "available": False,
            "status": "unavailable",
            "proof_status": "unavailable",
            "gate_status": "unavailable",
            "error": str(exc),
            "missing_evidence_slots": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS),
            "missing_evidence_count": len(_PULSE_SCHEDULE_EVIDENCE_FLAGS),
            "required_evidence_ref_flags": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS.values()),
            "write_root": _PULSE_SCHEDULE_RUN_QUEUE_WRITE_ROOTS[0],
            "write_action_id": "pulse-schedule-run-queue-audit-write-proof",
            "proof_queue_entry_count": 0,
            "proof_audit_event_count": 0,
            "real_run_queue_written": False,
            "real_audit_event_written": False,
            "schedule_activation_allowed": False,
            "schedule_manifest_write_allowed": False,
            "schedule_daemon_started": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_execution_allowed": False,
            "canonical_writeback_allowed": False,
            "result": None,
        }

    missing = list(proof.get("missing_evidence_slots") or [])
    return {
        "surface": "studio_pulse_schedule_run_queue_audit_proof",
        "available": True,
        "status": proof.get("proof_status"),
        "proof_status": proof.get("proof_status"),
        "gate_status": proof.get("gate_status"),
        "schedule_ids": list(proof.get("schedule_ids") or []),
        "schedule_count": int(proof.get("schedule_count", 0) or 0),
        "missing_evidence_slots": missing,
        "missing_evidence_count": len(missing),
        "required_evidence_ref_flags": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS.values()),
        "write_root": str(proof.get("allowed_write_root") or _PULSE_SCHEDULE_RUN_QUEUE_WRITE_ROOTS[0]),
        "write_action_id": "pulse-schedule-run-queue-audit-write-proof",
        "proof_queue_entry_count": int(proof.get("proof_queue_entry_count", 0) or 0),
        "proof_audit_event_count": int(proof.get("proof_audit_event_count", 0) or 0),
        "real_run_queue_written": bool(proof.get("real_run_queue_written")),
        "real_audit_event_written": bool(proof.get("real_audit_event_written")),
        "schedule_activation_allowed": bool(proof.get("schedule_activation_allowed")),
        "schedule_manifest_write_allowed": bool(proof.get("schedule_manifest_write_allowed")),
        "schedule_daemon_started": bool(proof.get("schedule_daemon_started")),
        "agent_bus_task_write_allowed": bool(proof.get("agent_bus_task_write_allowed")),
        "runtime_dispatch_allowed": bool(proof.get("runtime_dispatch_allowed")),
        "workflow_execution_allowed": bool(proof.get("workflow_execution_allowed")),
        "canonical_writeback_allowed": bool(proof.get("canonical_writeback_allowed")),
        "next_recommended_pass": proof.get("next_recommended_pass"),
        "result": proof,
    }


def _pulse_schedule_supervised_activation_execution_status(vault: Path) -> dict[str, Any]:
    """Return Studio-safe status for the guarded supervised activation execution proof."""

    try:
        from runtime.pulse.native_schedule_supervised_activation_execution import (
            build_pulse_native_schedule_supervised_activation_execution,
        )

        proof = build_pulse_native_schedule_supervised_activation_execution(vault).to_dict()
    except Exception as exc:  # noqa: BLE001 - status surfaces must degrade cleanly.
        return {
            "surface": "studio_pulse_schedule_supervised_activation_execution",
            "available": False,
            "status": "unavailable",
            "execution_status": "unavailable",
            "gate_status": "unavailable",
            "run_queue_proof_status": "unavailable",
            "error": str(exc),
            "missing_evidence_slots": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS),
            "missing_evidence_count": len(_PULSE_SCHEDULE_EVIDENCE_FLAGS),
            "required_evidence_ref_flags": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS.values()),
            "write_root": _PULSE_SCHEDULE_SUPERVISED_ACTIVATION_WRITE_ROOTS[0],
            "write_action_id": "pulse-schedule-supervised-activation-execution-write-proof",
            "execute_activation_action_exposed": False,
            "execute_requested": False,
            "manifest_patch_count": 0,
            "schedule_manifest_write_executed": False,
            "schedule_activation_executed": False,
            "schedule_daemon_started": False,
            "real_run_queue_written": False,
            "real_audit_event_written": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_execution_allowed": False,
            "provider_or_connector_call_allowed": False,
            "canonical_writeback_allowed": False,
            "result": None,
        }

    missing = list(proof.get("missing_evidence_slots") or [])
    return {
        "surface": "studio_pulse_schedule_supervised_activation_execution",
        "available": True,
        "status": proof.get("execution_status"),
        "execution_status": proof.get("execution_status"),
        "gate_status": proof.get("gate_status"),
        "run_queue_proof_status": proof.get("run_queue_proof_status"),
        "schedule_ids": list(proof.get("schedule_ids") or []),
        "schedule_count": int(proof.get("schedule_count", 0) or 0),
        "missing_evidence_slots": missing,
        "missing_evidence_count": len(missing),
        "required_evidence_ref_flags": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS.values()),
        "write_root": str(proof.get("allowed_write_root") or _PULSE_SCHEDULE_SUPERVISED_ACTIVATION_WRITE_ROOTS[0]),
        "write_action_id": "pulse-schedule-supervised-activation-execution-write-proof",
        "execute_activation_action_exposed": False,
        "execute_requested": bool(proof.get("execute_requested")),
        "manifest_patch_count": int(proof.get("manifest_patch_count", 0) or 0),
        "schedule_manifest_write_executed": bool(proof.get("schedule_manifest_write_executed")),
        "schedule_activation_executed": bool(proof.get("schedule_activation_executed")),
        "schedule_daemon_started": bool(proof.get("schedule_daemon_started")),
        "real_run_queue_written": bool(proof.get("real_run_queue_written")),
        "real_audit_event_written": bool(proof.get("real_audit_event_written")),
        "agent_bus_task_write_allowed": bool(proof.get("agent_bus_task_write_allowed")),
        "runtime_dispatch_allowed": bool(proof.get("runtime_dispatch_allowed")),
        "workflow_execution_allowed": bool(proof.get("workflow_execution_allowed")),
        "provider_or_connector_call_allowed": bool(proof.get("provider_or_connector_call_allowed")),
        "canonical_writeback_allowed": bool(proof.get("canonical_writeback_allowed")),
        "next_recommended_pass": proof.get("next_recommended_pass"),
        "result": proof,
    }


def _pulse_enqueue_preview(
    vault: Path,
    *,
    recipient: str = "Hermes",
    candidate_kinds: set[str] | None = None,
    candidate_id: str | None = None,
    limit: int | None = 5,
) -> dict[str, Any]:
    """Return a no-write Pulse enqueue pipeline preview for Studio controls."""

    try:
        from runtime.pulse.pipeline_runner import run_pulse_enqueue_pipeline

        result = run_pulse_enqueue_pipeline(
            vault,
            dry_run=True,
            default_recipient=recipient,
            candidate_kinds=candidate_kinds,
            candidate_id=candidate_id,
            limit=limit,
        ).to_dict()
    except Exception as exc:  # noqa: BLE001 - unavailable Pulse state should not break acquisition intake.
        return {
            "surface": "studio_pulse_review_contract_enqueue_preview",
            "available": False,
            "status": "unavailable",
            "error": str(exc),
            "dry_run": True,
            "plan_preflight_count": 0,
            "preview_count": 0,
            "dry_run_previews": [],
            "write_executed": False,
        }

    return {
        "surface": "studio_pulse_review_contract_enqueue_preview",
        "available": True,
        "status": result.get("pipeline_status"),
        "dry_run": True,
        "plan_preflight_count": int(result.get("plan_preflight_count", 0) or 0),
        "preview_count": len(result.get("dry_run_previews", [])),
        "dry_run_previews": list(result.get("dry_run_previews", [])),
        "write_executed": False,
        "result": result,
    }


def _pulse_roadmap_controls(vault: Path, profile: str) -> dict[str, Any]:
    schedule = _pulse_schedule_runner_status(vault)
    runtime_dispatch = _pulse_schedule_runtime_dispatch_proof_status(vault)
    activation = _pulse_schedule_activation_gate_status(vault)
    run_queue = _pulse_schedule_run_queue_audit_proof_status(vault)
    supervised_execution = _pulse_schedule_supervised_activation_execution_status(vault)
    enqueue_preview = _pulse_enqueue_preview(vault)
    preflight_count = int(enqueue_preview.get("plan_preflight_count", 0) or 0)
    enqueue_available = bool(enqueue_preview.get("available"))
    enqueue_enabled = enqueue_available and preflight_count > 0
    controls = [
        {
            "id": "pulse_schedule_runner_status",
            "label": "Pulse schedule runner status",
            "command": "chaseos pulse native-schedule-live-runner --force-due --json",
            "studio_action": "pulse-schedule-runner-status",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action pulse-schedule-runner-status --json"
            ),
            "write_action": False,
            "requires_confirmation": False,
            "enabled": bool(schedule.get("available")),
            "live_runner_built": bool(schedule.get("live_runner_built")),
            "reason_if_disabled": None if schedule.get("available") else schedule.get("error"),
        },
        {
            "id": "pulse_schedule_live_runner_preview",
            "label": "Pulse live schedule runner preview",
            "command": "chaseos pulse native-schedule-live-runner --force-due --json",
            "studio_action": "pulse-schedule-live-runner-preview",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action pulse-schedule-live-runner-preview --force-due --json"
            ),
            "write_action": False,
            "requires_confirmation": False,
            "enabled": bool(schedule.get("live_runner_built")),
            "force_due_available": True,
            "reason_if_disabled": None if schedule.get("live_runner_built") else schedule.get("error"),
        },
        {
            "id": "pulse_schedule_live_runner_execute",
            "label": "Write Pulse live schedule queue/audit records",
            "command": "chaseos pulse native-schedule-live-runner --force-due --execute --json",
            "studio_action": "pulse-schedule-live-runner-execute",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action pulse-schedule-live-runner-execute --force-due --confirm-action --json"
            ),
            "write_action": True,
            "requires_confirmation": True,
            "enabled": bool(schedule.get("live_runner_built")),
            "confirmation_flag": "--confirm-action",
            "force_due_available": True,
            "writes_only": list(_PULSE_SCHEDULE_LIVE_RUNNER_WRITE_ROOTS),
            "reason_if_disabled": None if schedule.get("live_runner_built") else schedule.get("error"),
        },
        {
            "id": "pulse_schedule_runtime_dispatch_proof",
            "label": "Pulse schedule runtime dispatch proof",
            "command": "chaseos pulse native-schedule-runtime-dispatch-proof --json",
            "studio_action": "pulse-schedule-runtime-dispatch-proof",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action pulse-schedule-runtime-dispatch-proof --json"
            ),
            "write_action": False,
            "requires_confirmation": False,
            "enabled": bool(runtime_dispatch.get("available")),
            "execute_dispatch_exposed": False,
            "reason_if_disabled": None if runtime_dispatch.get("available") else runtime_dispatch.get("error"),
        },
        {
            "id": "pulse_schedule_runtime_dispatch_write_proof",
            "label": "Write Pulse schedule runtime dispatch proof artifact",
            "command": "chaseos pulse native-schedule-runtime-dispatch-proof --write-proof --json",
            "studio_action": "pulse-schedule-runtime-dispatch-write-proof",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action pulse-schedule-runtime-dispatch-write-proof --confirm-action --json"
            ),
            "write_action": True,
            "requires_confirmation": True,
            "enabled": bool(runtime_dispatch.get("available")),
            "confirmation_flag": "--confirm-action",
            "writes_only": list(_PULSE_SCHEDULE_RUNTIME_DISPATCH_WRITE_ROOTS),
            "execute_dispatch_exposed": False,
            "reason_if_disabled": None if runtime_dispatch.get("available") else runtime_dispatch.get("error"),
        },
        {
            "id": "pulse_schedule_activation_gate",
            "label": "Pulse schedule activation gate",
            "command": "chaseos pulse native-schedule-activation-gate --json",
            "studio_action": "pulse-schedule-activation-gate",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action pulse-schedule-activation-gate --json"
            ),
            "write_action": False,
            "requires_confirmation": False,
            "enabled": bool(activation.get("available")),
            "required_evidence_ref_flags": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS.values()),
            "reason_if_disabled": None if activation.get("available") else activation.get("error"),
        },
        {
            "id": "pulse_schedule_activation_request",
            "label": "Write pending Pulse schedule activation request",
            "command": (
                "chaseos pulse native-schedule-activation-gate --write-request "
                "--operator-approval-ref <ref> --permission-envelope-ref <ref> "
                "--run-queue-scope-ref <ref> --audit-identity-ref <ref> "
                "--runtime-adapter-scope-ref <ref> --rollback-plan-ref <ref> "
                "--external-scheduler-denial-ref <ref> --canonical-writeback-denial-ref <ref> --json"
            ),
            "studio_action": "pulse-schedule-activation-request",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action pulse-schedule-activation-request --confirm-action --json"
            ),
            "write_action": True,
            "requires_confirmation": True,
            "enabled": bool(activation.get("available")),
            "confirmation_flag": "--confirm-action",
            "required_evidence_ref_flags": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS.values()),
            "writes_only": list(_PULSE_SCHEDULE_ACTIVATION_WRITE_ROOTS),
            "reason_if_disabled": None if activation.get("available") else activation.get("error"),
        },
        {
            "id": "pulse_schedule_run_queue_audit_proof",
            "label": "Pulse schedule run-queue/audit proof",
            "command": "chaseos pulse native-schedule-run-queue-audit-proof --json",
            "studio_action": "pulse-schedule-run-queue-audit-proof",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action pulse-schedule-run-queue-audit-proof --json"
            ),
            "write_action": False,
            "requires_confirmation": False,
            "enabled": bool(run_queue.get("available")),
            "required_evidence_ref_flags": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS.values()),
            "reason_if_disabled": None if run_queue.get("available") else run_queue.get("error"),
        },
        {
            "id": "pulse_schedule_run_queue_audit_write_proof",
            "label": "Write Pulse schedule run-queue/audit proof artifact",
            "command": (
                "chaseos pulse native-schedule-run-queue-audit-proof --write-proof "
                "--operator-approval-ref <ref> --permission-envelope-ref <ref> "
                "--run-queue-scope-ref <ref> --audit-identity-ref <ref> "
                "--runtime-adapter-scope-ref <ref> --rollback-plan-ref <ref> "
                "--external-scheduler-denial-ref <ref> --canonical-writeback-denial-ref <ref> --json"
            ),
            "studio_action": "pulse-schedule-run-queue-audit-write-proof",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action pulse-schedule-run-queue-audit-write-proof --confirm-action --json"
            ),
            "write_action": True,
            "requires_confirmation": True,
            "enabled": bool(run_queue.get("available")),
            "confirmation_flag": "--confirm-action",
            "required_evidence_ref_flags": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS.values()),
            "writes_only": list(_PULSE_SCHEDULE_RUN_QUEUE_WRITE_ROOTS),
            "reason_if_disabled": None if run_queue.get("available") else run_queue.get("error"),
        },
        {
            "id": "pulse_schedule_supervised_activation_execution_proof",
            "label": "Pulse schedule supervised activation execution proof",
            "command": "chaseos pulse native-schedule-supervised-activation-execution-proof --json",
            "studio_action": "pulse-schedule-supervised-activation-execution-proof",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action pulse-schedule-supervised-activation-execution-proof --json"
            ),
            "write_action": False,
            "requires_confirmation": False,
            "enabled": bool(supervised_execution.get("available")),
            "required_evidence_ref_flags": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS.values()),
            "execute_activation_exposed": False,
            "reason_if_disabled": (
                None if supervised_execution.get("available") else supervised_execution.get("error")
            ),
        },
        {
            "id": "pulse_schedule_supervised_activation_execution_write_proof",
            "label": "Write Pulse schedule supervised activation execution proof artifact",
            "command": (
                "chaseos pulse native-schedule-supervised-activation-execution-proof --write-proof "
                "--operator-approval-ref <ref> --permission-envelope-ref <ref> "
                "--run-queue-scope-ref <ref> --audit-identity-ref <ref> "
                "--runtime-adapter-scope-ref <ref> --rollback-plan-ref <ref> "
                "--external-scheduler-denial-ref <ref> --canonical-writeback-denial-ref <ref> --json"
            ),
            "studio_action": "pulse-schedule-supervised-activation-execution-write-proof",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action pulse-schedule-supervised-activation-execution-write-proof --confirm-action --json"
            ),
            "write_action": True,
            "requires_confirmation": True,
            "enabled": bool(supervised_execution.get("available")),
            "confirmation_flag": "--confirm-action",
            "required_evidence_ref_flags": list(_PULSE_SCHEDULE_EVIDENCE_FLAGS.values()),
            "writes_only": list(_PULSE_SCHEDULE_SUPERVISED_ACTIVATION_WRITE_ROOTS),
            "execute_activation_exposed": False,
            "reason_if_disabled": (
                None if supervised_execution.get("available") else supervised_execution.get("error")
            ),
        },
        {
            "id": "pulse_enqueue_preview",
            "label": "Preview Pulse review contract enqueue",
            "command": "chaseos pulse run-pipeline --limit 5 --json",
            "studio_action": "pulse-enqueue-preview",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} "
                "--action pulse-enqueue-preview --limit 5 --json"
            ),
            "write_action": False,
            "requires_confirmation": False,
            "enabled": enqueue_available,
            "reason_if_disabled": None if enqueue_available else enqueue_preview.get("error"),
        },
        {
            "id": "pulse_enqueue_approved",
            "label": "Operator-approved Pulse review enqueue",
            "command": (
                "chaseos pulse run-pipeline --live --operator-approved "
                "--gate-policy-defined --external-sender-allowance-present "
                "--duplicate-work-fingerprint-reviewed --limit 5 --json"
            ),
            "studio_action": "pulse-enqueue-approved",
            "studio_command": (
                f"chaseos studio acquisition-cockpit --profile {profile} --action pulse-enqueue-approved "
                "--operator-approved --gate-policy-defined --external-sender-allowance-present "
                "--duplicate-work-fingerprint-reviewed --confirm-action --limit 5 --json"
            ),
            "write_action": True,
            "requires_confirmation": True,
            "enabled": enqueue_enabled,
            "confirmation_flag": "--confirm-action",
            "required_evidence_flags": list(_PULSE_REVIEW_REQUIRED_EVIDENCE.values()),
            "writes_only": list(_PULSE_ENQUEUE_WRITE_ROOTS),
            "reason_if_disabled": (
                "No Pulse review-contract preflights are available."
                if enqueue_available and not enqueue_enabled
                else enqueue_preview.get("error")
                if not enqueue_available
                else None
            ),
        },
    ]
    return {
        "surface": "studio_pulse_roadmap_controls",
        "roadmap_item": "10A0 - Studio Acquisition Intake Cockpit",
        "profile": profile,
        "live_schedule_runner": schedule,
        "schedule_runtime_dispatch_proof": runtime_dispatch,
        "schedule_activation_gate": activation,
        "schedule_run_queue_audit_proof": run_queue,
        "schedule_supervised_activation_execution": supervised_execution,
        "agent_bus_enqueue": {
            "surface": "operator_approved_agent_bus_enqueue_surface",
            "available": enqueue_available,
            "preflight_count": preflight_count,
            "preview_count": int(enqueue_preview.get("preview_count", 0) or 0),
            "dry_run_preview": enqueue_preview,
            "live_enqueue_requires": list(_PULSE_REVIEW_REQUIRED_EVIDENCE.values()) + ["--confirm-action"],
            "allowed_recipients": ["Hermes", "OpenClaw"],
            "approved_action_id": "pulse-enqueue-approved",
            "write_roots": list(_PULSE_ENQUEUE_WRITE_ROOTS),
        },
        "controls": controls,
        "authority": {
            "local_only": True,
            "operator_approval_required_for_live_enqueue": True,
            "agent_bus_task_write_allowed_only_for_approved_action": True,
            "schedule_activation_allowed": False,
            "schedule_manifest_write_allowed": False,
            "schedule_daemon_start_allowed": False,
            "activation_request_write_allowed_only_for_confirmed_action": True,
            "live_schedule_runner_built": bool(schedule.get("live_runner_built")),
            "run_queue_write_allowed": bool(schedule.get("live_queue_entry_count")),
            "run_queue_write_allowed_only_for_confirmed_live_runner": True,
            "real_audit_event_write_allowed": bool(schedule.get("live_audit_event_count")),
            "real_audit_event_write_allowed_only_for_confirmed_live_runner": True,
            "runtime_dispatch_proof_built": bool(runtime_dispatch.get("available")),
            "runtime_dispatch_proof_ready_count": int(runtime_dispatch.get("ready_dispatch_target_count", 0) or 0),
            "runtime_dispatch_proof_write_allowed_only_for_confirmed_action": True,
            "run_queue_audit_proof_write_allowed_only_for_confirmed_action": True,
            "schedule_activation_execution_allowed": False,
            "supervised_activation_execute_action_exposed": False,
            "activation_execution_proof_write_allowed_only_for_confirmed_action": True,
            "candidate_apply_allowed": False,
            "review_response_ingest_allowed": False,
            "canonical_writeback_allowed": False,
            "provider_or_connector_call_allowed": False,
        },
        "status": (
            "ready"
            if enqueue_available or schedule.get("available") or activation.get("available") or run_queue.get("available")
            or supervised_execution.get("available") or runtime_dispatch.get("available")
            else "unavailable"
        ),
    }


def _rehearsal_ladder(profile: str, status: dict[str, Any], controls: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a read-only stage model for the local research-file rehearsal."""

    controls_by_action = {
        str(control.get("studio_action")): control
        for control in controls
        if control.get("studio_action")
    }
    readiness = status.get("readiness", {})
    source_count = int(status.get("source_count", 0) or 0)
    inbox_count = int(status.get("inbox_candidate_count", 0) or 0)
    preview_count = int(status.get("preview_candidate_count", 0) or 0)
    latest_preview = status.get("latest_preview_candidate") or {}
    has_valid_preview = bool(latest_preview.get("valid_for_reviewed_promotion"))
    reviewed_preview = bool(readiness.get("reviewed_preview_promoted"))
    default_verify_ready = bool(readiness.get("default_verify_ready"))
    missing_recommended = list(status.get("missing_recommended_source_classes", []))
    repository_ready = bool(readiness.get("repository_template_ready"))

    if not repository_ready:
        current_step_id = "init_repository"
    elif default_verify_ready:
        current_step_id = None
    elif source_count == 0 and inbox_count == 0:
        current_step_id = "stage_research_files"
    elif inbox_count > 0:
        current_step_id = "import_inbox"
    elif source_count > 0 and preview_count == 0 and not reviewed_preview:
        current_step_id = "preview_write"
    elif has_valid_preview and not reviewed_preview:
        current_step_id = "reviewed_promotion"
    elif reviewed_preview:
        current_step_id = "verify_sbp_consumption"
    else:
        current_step_id = "reviewed_promotion"

    def control(action: str) -> dict[str, Any]:
        return controls_by_action.get(action, {})

    def step(
        step_id: str,
        label: str,
        *,
        complete: bool,
        blocked: bool = False,
        action_id: str | None = None,
        command: str | None = None,
        detail: str,
        blockers: list[str] | None = None,
        write_action: bool = False,
        requires_confirmation: bool = False,
    ) -> dict[str, Any]:
        if complete:
            state = "complete"
        elif step_id == current_step_id and not blocked:
            state = "current"
        elif blocked:
            state = "blocked"
        else:
            state = "pending"
        return {
            "id": step_id,
            "label": label,
            "state": state,
            "action_id": action_id,
            "command": command,
            "detail": detail,
            "blockers": blockers or [],
            "write_action": write_action,
            "requires_confirmation": requires_confirmation,
        }

    init_control = control("init-repository")
    import_control = control("import-inbox")
    preview_control = control("preview-write")
    promotion_control = control("promote-reviewed-preview")
    verify_control = control("verify-research-sbp")

    steps = [
        step(
            "init_repository",
            "Initialize repository template",
            complete=repository_ready,
            action_id="init-repository",
            command=init_control.get("studio_command"),
            detail="Create the local StrikeZone research folder, inbox, and template layout for this machine.",
            blockers=[] if repository_ready else ["Research repository template is missing folders or template files."],
            write_action=True,
            requires_confirmation=True,
        ),
        step(
            "stage_research_files",
            "Stage research files",
            complete=source_count > 0 or inbox_count > 0,
            blocked=not repository_ready,
            action_id="stage-upload",
            detail="Upload or place operator-reviewed files into the matching source-class inbox.",
            blockers=[],
            write_action=True,
            requires_confirmation=True,
        ),
        step(
            "import_inbox",
            "Import staged inbox files",
            complete=source_count > 0 and inbox_count == 0,
            blocked=not repository_ready or (inbox_count == 0 and source_count == 0),
            action_id="import-inbox",
            command=import_control.get("studio_command"),
            detail="Copy staged inbox files into declared local source-class folders.",
            blockers=["No staged inbox files are available."] if inbox_count == 0 and source_count == 0 else [],
            write_action=True,
            requires_confirmation=True,
        ),
        step(
            "preview_write",
            "Write preview pack",
            complete=preview_count > 0 or reviewed_preview,
            blocked=not repository_ready or source_count == 0,
            action_id="preview-write",
            command=preview_control.get("studio_command"),
            detail="Build runtime-local preview artifacts from declared research files.",
            blockers=["No declared research source files are available."] if source_count == 0 else [],
            write_action=True,
            requires_confirmation=True,
        ),
        step(
            "reviewed_promotion",
            "Review and promote preview",
            complete=reviewed_preview,
            blocked=not repository_ready or (not has_valid_preview and not reviewed_preview),
            action_id="promote-reviewed-preview",
            command=promotion_control.get("studio_command"),
            detail="Review the preview pack, then confirm the latest-pointer promotion.",
            blockers=["No valid preview BRIS is available for reviewed promotion."]
            if not has_valid_preview and not reviewed_preview
            else [],
            write_action=True,
            requires_confirmation=True,
        ),
        step(
            "verify_sbp_consumption",
            "Verify SBP consumption",
            complete=default_verify_ready,
            blocked=not repository_ready or not reviewed_preview,
            action_id="verify-research-sbp",
            command=verify_control.get("studio_command"),
            detail="Verify the StrikeZone SBP acquisition-pack adapter can consume the promoted preview.",
            blockers=["No reviewed preview pointer has been promoted."] if not reviewed_preview else [],
            write_action=False,
            requires_confirmation=False,
        ),
    ]

    return {
        "surface": "strikezone_research_rehearsal_ladder",
        "profile": profile,
        "current_step_id": current_step_id,
        "complete": repository_ready and default_verify_ready,
        "steps": steps,
        "authority": _authority_boundary(),
    }


def _control_by_id_or_action(controls: list[dict[str, Any]], *keys: str) -> dict[str, Any]:
    wanted = {key for key in keys if key}
    for control in controls:
        if control.get("id") in wanted or control.get("studio_action") in wanted:
            return control
    return {}


def _source_pack_review_handoff(profile: str, status: dict[str, Any], controls: list[dict[str, Any]]) -> dict[str, Any]:
    """Return Studio-only preview/review/evidence/handoff state for source packs.

    This is a Phase 10 surface over the existing Phase 9 acquisition/SBP
    contracts. It explains what exists and which governed handoff command is
    available; it does not create packs, promote pointers, verify SBP inputs, or
    mutate canonical graph truth.
    """

    readiness = status.get("readiness", {})
    latest_preview = status.get("latest_preview_candidate") or {}
    latest_pointer = status.get("latest_pointer") or {}
    promotion_control = _control_by_id_or_action(controls, "promote_reviewed_preview", "promote-reviewed-preview")
    verify_control = _control_by_id_or_action(controls, "verify_research_sbp", "verify-research-sbp")

    reviewed_preview_promoted = bool(readiness.get("reviewed_preview_promoted"))
    default_verify_ready = bool(readiness.get("default_verify_ready"))
    current_pointer_consumable = bool(readiness.get("current_pointer_consumable_by_sbp"))
    default_verify_error = status.get("default_verify_error")
    latest_pointer_path = str(status.get("latest_pointer_path") or "runtime/acquisition/packs/strikezone-latest.json")
    source_packet_paths = [str(path) for path in latest_preview.get("source_packet_paths", [])]
    briefing_input = str(
        latest_preview.get("briefing_ready_input_set_path")
        or latest_pointer.get("briefing_ready_input_set_path")
        or ""
    )
    normalized_pack = str(latest_preview.get("normalized_source_pack_path") or "")

    blocked_backend_dependencies: list[dict[str, str]] = []
    if not latest_preview.get("valid_for_reviewed_promotion") and not reviewed_preview_promoted:
        blocked_backend_dependencies.append(
            {
                "missing_contract": "valid runtime-local preview source pack is unavailable",
                "affected_phase10_surface": "Acquisition Cockpit source-pack preview and reviewed-promotion controls",
                "lower_phase_owner_surface": "Phase 9 acquisition builder/validator: runtime/acquisition/research_imports.preview_research_imports",
                "minimum_proof_needed": "Run the governed preview-write action after operator-reviewed research files are imported and observe a valid latest_preview_candidate.",
                "blocked_action_reason": "No valid preview BRIS/normalized source pack is available for reviewed promotion.",
            }
        )
    if reviewed_preview_promoted and not default_verify_ready:
        blocked_backend_dependencies.append(
            {
                "missing_contract": "default reviewed-preview SBP verification is not complete",
                "affected_phase10_surface": "Acquisition Cockpit reviewed-promotion visibility and SBP handoff readiness",
                "lower_phase_owner_surface": "Phase 9 acquisition/SBP adapter: runtime/acquisition/research_imports.verify_research_preview_sbp_consumption",
                "minimum_proof_needed": "Run the governed verify-research-sbp action against the promoted reviewed preview pointer and observe default_verify_ready=true.",
                "blocked_action_reason": str(default_verify_error or "Reviewed preview pointer exists but default SBP verification is not ready."),
            }
        )
    if not current_pointer_consumable and reviewed_preview_promoted:
        blocked_backend_dependencies.append(
            {
                "missing_contract": "current reviewed pointer is not consumable by the SBP acquisition-pack adapter",
                "affected_phase10_surface": "Acquisition Cockpit operator handoff path to SBP input readiness",
                "lower_phase_owner_surface": "Phase 9 SBP acquisition-pack input adapter: runtime/sbp/input_adapters.py",
                "minimum_proof_needed": "Resolve the pointer/BRIS adapter error and rerun verify-research-sbp until current_pointer_consumable_by_sbp=true.",
                "blocked_action_reason": str(status.get("current_pointer_verification_error") or "Current pointer cannot be consumed by SBP."),
            }
        )

    return {
        "surface": "studio_acquisition_source_pack_review_handoff",
        "profile": profile,
        "source_pack_preview": {
            "candidate_count": int(status.get("preview_candidate_count", 0) or 0),
            "latest_pack_root": str(latest_preview.get("pack_root") or ""),
            "valid_for_reviewed_promotion": bool(latest_preview.get("valid_for_reviewed_promotion")),
            "source_classes": dict(latest_preview.get("source_classes") or {}),
            "source_packet_count": int(latest_preview.get("source_packet_count", len(source_packet_paths)) or 0),
            "warnings": list(latest_preview.get("warnings") or status.get("preview_warnings", []) or []),
        },
        "evidence": {
            "briefing_ready_input_set_path": briefing_input,
            "normalized_source_pack_path": normalized_pack,
            "source_packet_paths": source_packet_paths,
        },
        "review_state": {
            "reviewed_preview_promoted": reviewed_preview_promoted,
            "reviewed_by": latest_pointer.get("reviewed_by"),
            "promoted_at": latest_pointer.get("promoted_at"),
            "current_pointer_consumable_by_sbp": current_pointer_consumable,
            "default_verify_ready": default_verify_ready,
            "default_verify_error": default_verify_error,
        },
        "operator_handoff_paths": {
            "preview_bris": briefing_input,
            "preview_normalized_source_pack": normalized_pack,
            "promoted_latest_pointer": latest_pointer_path,
        },
        "operator_handoff_actions": {
            "promote_reviewed_preview": {
                "studio_command": promotion_control.get("studio_command"),
                "enabled": bool(promotion_control.get("enabled")),
                "write_action": bool(promotion_control.get("write_action")),
                "requires_confirmation": bool(promotion_control.get("requires_confirmation")),
                "writes_only": list(promotion_control.get("writes_only", [])),
            },
            "verify_research_sbp": {
                "studio_command": verify_control.get("studio_command"),
                "enabled": bool(verify_control.get("enabled")),
                "write_action": bool(verify_control.get("write_action")),
                "requires_confirmation": bool(verify_control.get("requires_confirmation")),
            },
        },
        "blocked_backend_dependencies": blocked_backend_dependencies,
        "authority": _authority_boundary(),
    }


def _manual_test_sequence(profile: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "init_repository",
            "label": "Initialize research repository",
            "operator_action": "Create the local StrikeZone research repository template on this machine.",
            "command": f"chaseos studio acquisition-cockpit --profile {profile} --action init-repository --confirm-action --json",
            "write_action": True,
            "requires_confirmation": True,
            "expected_output": "Source-class folders, inbox folders, and reusable templates exist under runtime/acquisition/manual/strikezone/.",
        },
        {
            "id": "stage_research_files",
            "label": "Stage real research files",
            "operator_action": "Use the localhost cockpit upload controls or place files in the source-class inboxes.",
            "command": f"chaseos studio acquisition-cockpit-app --profile {profile}",
            "write_action": True,
            "requires_confirmation": True,
            "expected_output": "Files staged under runtime/acquisition/manual/strikezone/_inbox/<source_class>/.",
        },
        {
            "id": "import_inbox",
            "label": "Import staged inbox",
            "operator_action": "Run the governed inbox import after staged files look correct.",
            "command": f"chaseos studio acquisition-cockpit --profile {profile} --action import-inbox --confirm-action --json",
            "write_action": True,
            "requires_confirmation": True,
            "expected_output": "Files copied into declared source-class folders and local import ledger updated.",
        },
        {
            "id": "preview_write",
            "label": "Write preview pack",
            "operator_action": "Build runtime-local preview artifacts from the declared local files.",
            "command": f"chaseos studio acquisition-cockpit --profile {profile} --action preview-write --confirm-action --json",
            "write_action": True,
            "requires_confirmation": True,
            "expected_output": "Preview source packets, normalized source pack, and BRIS under runtime/acquisition/packs/.",
        },
        {
            "id": "reviewed_promotion",
            "label": "Review and promote preview",
            "operator_action": "Inspect the preview pack, then promote the prefilled BRIS path only after review.",
            "command": (
                f"chaseos studio acquisition-cockpit --profile {profile} --action promote-reviewed-preview "
                "--briefing-input <prefilled-preview-bris> --reviewed --confirm-action --json"
            ),
            "write_action": True,
            "requires_confirmation": True,
            "expected_output": "runtime/acquisition/packs/strikezone-latest.json points at a reviewed preview pack.",
        },
        {
            "id": "verify_sbp_consumption",
            "label": "Verify SBP consumption",
            "operator_action": "Run the read-only verifier against the promoted reviewed preview pointer.",
            "command": f"chaseos studio acquisition-cockpit --profile {profile} --action verify-research-sbp --json",
            "write_action": False,
            "requires_confirmation": False,
            "expected_output": "StrikeZone SBP acquisition-pack adapter consumes the richer preview pack.",
        },
    ]


def _manual_test_readiness(
    profile: str,
    status: dict[str, Any],
    controls: list[dict[str, Any]],
    rehearsal: dict[str, Any],
    source_class_cards: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return a closeout contract for later manual real-file rehearsal."""

    control_actions = {
        str(control.get("studio_action") or control.get("id") or "")
        for control in controls
        if control.get("studio_action") or control.get("id")
    }
    source_classes = {
        str(card.get("source_class"))
        for card in source_class_cards
        if card.get("source_class")
    }
    missing_contract_actions = sorted(_REQUIRED_MANUAL_TEST_ACTIONS - control_actions)
    missing_source_class_cards = sorted(set(_EXPECTED_RESEARCH_SOURCE_CLASSES) - source_classes)
    required_status_fields = {
        "source_count",
        "inbox_candidate_count",
        "preview_candidates",
        "preview_candidate_count",
        "latest_preview_candidate",
        "repository_template",
        "readiness",
    }
    missing_status_fields = sorted(required_status_fields - set(status))

    development_blockers: list[str] = []
    if missing_source_class_cards:
        development_blockers.append("Missing source-class cards: " + ", ".join(missing_source_class_cards))
    if missing_contract_actions:
        development_blockers.append("Missing governed controls: " + ", ".join(missing_contract_actions))
    if missing_status_fields:
        development_blockers.append("Missing status fields: " + ", ".join(missing_status_fields))
    if rehearsal.get("surface") != "strikezone_research_rehearsal_ladder":
        development_blockers.append("Workflow rehearsal ladder is unavailable.")

    readiness = status.get("readiness", {})
    source_count = int(status.get("source_count", 0) or 0)
    inbox_count = int(status.get("inbox_candidate_count", 0) or 0)
    preview_count = int(status.get("preview_candidate_count", 0) or 0)
    missing_recommended = list(status.get("missing_recommended_source_classes", []))
    repository_ready = bool(readiness.get("repository_template_ready"))
    reviewed_preview_promoted = bool(readiness.get("reviewed_preview_promoted"))
    default_verify_ready = bool(readiness.get("default_verify_ready"))

    manual_blockers: list[str] = []
    if not repository_ready:
        manual_blockers.append("Research repository template has not been initialized for this vault.")
    if source_count == 0 and inbox_count == 0:
        manual_blockers.append("No operator-selected research files are staged or imported yet.")
    if source_count > 0 and preview_count == 0 and not reviewed_preview_promoted:
        manual_blockers.append("No preview pack has been written from the imported research files yet.")
    if preview_count > 0 and not reviewed_preview_promoted:
        manual_blockers.append("A preview pack exists but still needs operator review and reviewed pointer promotion.")
    if reviewed_preview_promoted and not default_verify_ready:
        manual_blockers.append("Reviewed preview pointer exists but SBP consumption verification is not complete.")

    development_ready = not development_blockers
    manual_input_ready = development_ready and not manual_blockers
    return {
        "surface": "studio_acquisition_manual_test_readiness",
        "profile": profile,
        "development_ready_for_manual_real_file_test": development_ready,
        "manual_input_ready": manual_input_ready,
        "manual_rehearsal_complete": default_verify_ready,
        "current_rehearsal_step_id": rehearsal.get("current_step_id"),
        "remaining_development_passes": [],
        "remaining_manual_test_passes": [
            "phase10a0-real-local-file-rehearsal",
            "phase10a0-reviewed-research-pack-sbp-proof",
        ],
        "minimum_viable_source_count": 1,
        "source_coverage_model": "flexible",
        "coverage_warnings": [
            "Missing recommended source classes: " + ", ".join(missing_recommended)
        ]
        if missing_recommended
        else [],
        "development_blockers": development_blockers,
        "manual_blockers": manual_blockers,
        "required_source_classes": [],
        "recommended_source_classes": list(STRIKEZONE_RECOMMENDED_RESEARCH_SOURCE_CLASSES),
        "optional_source_classes": list(STRIKEZONE_OPTIONAL_RESEARCH_SOURCE_CLASSES),
        "supported_source_classes": list(_EXPECTED_RESEARCH_SOURCE_CLASSES),
        "required_actions": sorted(_REQUIRED_MANUAL_TEST_ACTIONS),
        "manual_test_sequence": _manual_test_sequence(profile),
        "authority": _authority_boundary(),
    }


def build_acquisition_cockpit_model(vault_root: str | Path, profile: str = "strikezone") -> dict[str, Any]:
    """Return a UI-ready model for the local/import research cockpit.

    The model is read-only. It surfaces declared folders, missing source-class
    coverage, command controls, and explicit authority boundaries for a future
    local UI renderer.
    """
    _require_strikezone(profile)
    vault = _vault_path(vault_root)
    status = inspect_research_import_status(vault, profile=profile).to_summary()
    imported_artifacts = _imported_artifacts_from_status(status)
    counts = status.get("source_classes", {})
    inbox_summary = status.get("inbox_readiness_summary", {})
    inbox_by_class = inbox_summary.get("source_classes", {})
    inbox_candidates_by_class: dict[str, list[dict[str, Any]]] = {}
    for candidate in status.get("inbox_candidates", []):
        source_class = str(candidate.get("source_class") or "")
        if source_class:
            inbox_candidates_by_class.setdefault(source_class, []).append(candidate)
    missing = set(status.get("missing_recommended_source_classes", []))
    source_class_cards: list[dict[str, Any]] = []
    for source_class, folder in status.get("source_class_folders", {}).items():
        recommended = source_class in STRIKEZONE_RECOMMENDED_RESEARCH_SOURCE_CLASSES
        optional = source_class in STRIKEZONE_OPTIONAL_RESEARCH_SOURCE_CLASSES
        file_count = int(counts.get(source_class, 0))
        source_inbox_summary = inbox_by_class.get(source_class, {})
        inbox_candidates = inbox_candidates_by_class.get(source_class, [])
        inbox_candidate_count = int(source_inbox_summary.get("candidate_count", 0) or 0)
        inbox_warning_count = int(source_inbox_summary.get("warning_count", 0) or 0)
        inbox_metadata_ready_count = int(source_inbox_summary.get("metadata_ready_count", 0) or 0)
        source_class_cards.append(
            {
                "source_class": source_class,
                "folder": folder,
                "inbox_folder": status.get("source_class_inboxes", {}).get(
                    source_class,
                    STRIKEZONE_RESEARCH_INBOX_FOLDERS.get(source_class),
                ),
                "file_count": file_count,
                "inbox_candidate_count": inbox_candidate_count,
                "inbox_metadata_ready_count": inbox_metadata_ready_count,
                "inbox_warning_count": inbox_warning_count,
                "inbox_readiness_label": (
                    "empty"
                    if inbox_candidate_count == 0
                    else "metadata_ready"
                    if inbox_metadata_ready_count == inbox_candidate_count
                    else "needs_review"
                ),
                "inbox_candidates": [
                    {
                        "filename": candidate.get("filename"),
                        "source_class": source_class,
                        "source_path": candidate.get("source_path"),
                        "fingerprint": candidate.get("fingerprint"),
                        "display_name": candidate.get("display_name"),
                        "readiness_label": (candidate.get("readiness") or {}).get("readiness_label"),
                        "warnings": list((candidate.get("readiness") or {}).get("warnings") or [])[:4],
                        "intake_suffix": candidate.get("intake_suffix"),
                        "normalization_method": candidate.get("normalization_method"),
                        "transform_method": (candidate.get("planned_artifact") or {}).get("transform_method"),
                        "source_claims_unverified": (candidate.get("planned_artifact") or {}).get(
                            "source_claims_unverified"
                        ),
                        "planned_artifact": candidate.get("planned_artifact") or {},
                        "import_action": {
                            "id": "import_staged_file",
                            "studio_action": "import-staged-file",
                            "source_class": source_class,
                            "source_path": candidate.get("source_path"),
                            "write_action": True,
                            "requires_confirmation": True,
                            "confirmation_flag": "--confirm-action",
                        },
                    }
                    for candidate in inbox_candidates[:5]
                ],
                "recommended_for_pilot": recommended,
                "required_for_live_proof": False,
                "optional": optional,
                "coverage_present": file_count > 0 or inbox_candidate_count > 0,
                "coverage_warning": source_class in missing,
                "missing": False,
                "accepted_suffixes": supported_intake_suffixes(),
                "import_action": {
                    "id": "import_research_file",
                    "source_class": source_class,
                    "studio_action": "import-file",
                    "studio_command": (
                        f"chaseos studio acquisition-cockpit --profile {profile} --action import-file "
                        f"--source-class {source_class} --source-file <operator-selected-file> "
                        "--confirm-action --json"
                    ),
                    "write_action": True,
                    "requires_confirmation": True,
                    "confirmation_flag": "--confirm-action",
                    "destination_folder": folder,
                },
            }
        )

    pulse_roadmap_controls = _pulse_roadmap_controls(vault, profile)
    controls = _command_controls(profile, status) + list(pulse_roadmap_controls.get("controls", []))
    source_pack_review_handoff = _source_pack_review_handoff(profile, status, controls)
    rehearsal = _rehearsal_ladder(profile, status, controls)
    return {
        "surface": _COCKPIT_ID,
        "title": "Research Intake Cockpit",
        "phase": "Phase 10A0",
        "profile": profile,
        "local_only": True,
        "status": status,
        "source_class_cards": source_class_cards,
        "imported_artifacts": imported_artifacts,
        "controls": controls,
        "source_pack_review_handoff": source_pack_review_handoff,
        "pulse_roadmap_controls": pulse_roadmap_controls,
        "rehearsal": rehearsal,
        "manual_test_readiness": _manual_test_readiness(
            profile,
            status,
            controls,
            rehearsal,
            source_class_cards,
        ),
        "writes": [],
        "authority": _authority_boundary(),
        "boundaries": [
            "No browser authority",
            "No MCP authority",
            "No external delivery authority",
            "No live provider calls",
            "No canonical note mutation",
            "Pulse Agent Bus enqueue is available only through explicit operator approval, evidence flags, and confirmation",
            "Pulse schedule activation request writes are pending-review artifacts only; no manifests are enabled",
            "Pulse live schedule runner can write local queue/audit records only for confirmed supervised active manifests",
            "Pulse runtime dispatch proof writes are proof artifacts only; no runtime dispatch or workflow execution is started",
            "Pulse run-queue/audit proof writes are proof artifacts only; no real queue or audit event is written",
            "Pulse supervised activation execution proof writes are proof artifacts only in 10A0; --execute-activation is not exposed",
            "Pulse schedule daemon start, runtime dispatch, and workflow execution remain blocked",
            "All writes require explicit operator action and map to existing Phase 9 acquisition surfaces",
        ],
    }


def _imported_artifacts_from_status(status: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for record in status.get("files", []):
        path = str(record.get("path") or "")
        if not path:
            continue
        display_name = str(record.get("display_name") or Path(path).stem)
        artifacts.append(
            {
                "source_class": record.get("source_class"),
                "path": path,
                "trading_brief_path": path,
                "display_name": display_name,
                "size_bytes": record.get("size_bytes"),
                "source_event_at": record.get("source_event_at"),
                "open_targets": [
                    {
                        "id": "open_antigravity",
                        "label": "Open in Antigravity",
                        "studio_action": "open-local-path",
                        "target": "antigravity",
                        "path": path,
                    },
                    {
                        "id": "open_folder",
                        "label": "Open folder",
                        "studio_action": "open-local-path",
                        "target": "folder",
                        "path": path,
                    },
                ],
            }
        )
    return artifacts


def _normalize_action(action: str) -> str:
    action_id = _ACTION_ALIASES.get(str(action or "model").strip())
    if not action_id:
        choices = ", ".join(sorted(_ACTION_ALIASES))
        raise CockpitActionError(f"unsupported cockpit action: {action!r}; expected one of: {choices}")
    return action_id


def _require_confirmation(action_id: str, confirm_action: bool) -> None:
    if action_id in _WRITE_ACTIONS and not confirm_action:
        raise CockpitActionError(f"{action_id} requires --confirm-action")


def _preview_writes(summary: dict[str, Any]) -> list[str]:
    writes: list[str] = []
    for key in ("normalized_source_pack_path", "briefing_ready_input_set_path"):
        value = summary.get(key)
        if value:
            writes.append(str(value))
    writes.extend(str(path) for path in summary.get("source_packet_paths", []))
    return writes


def _with_action_result(
    vault: Path,
    profile: str,
    *,
    action_id: str,
    result: dict[str, Any],
    write_action: bool,
    requires_confirmation: bool,
    writes: list[str],
) -> dict[str, Any]:
    model = build_acquisition_cockpit_model(vault, profile=profile)
    model["action"] = {
        "id": action_id,
        "status": "complete",
        "write_action": write_action,
        "requires_confirmation": requires_confirmation,
        "writes": writes,
        "result": result,
    }
    model["writes"] = writes
    return model


_LOCAL_OPEN_PREFIXES = (
    "runtime/acquisition/manual/strikezone/",
)


def _open_local_path(vault: Path, *, open_path: str | Path | None, target: str | None) -> dict[str, Any]:
    if not open_path:
        raise CockpitActionError("open-local-path requires open_path")
    target_id = str(target or "").strip().lower()
    if target_id not in {"antigravity", "folder"}:
        raise CockpitActionError("open-local-path target must be antigravity or folder")
    relative_path, absolute_path = _safe_local_open_path(vault, open_path)
    if target_id == "antigravity":
        executable = (
            shutil.which("antigravity")
            or shutil.which("antigravity.cmd")
            or shutil.which("Antigravity")
            or shutil.which("Antigravity.exe")
        )
        if not executable:
            raise CockpitActionError("Antigravity executable was not found on PATH")
        argv = [executable, str(absolute_path)]
    else:
        folder = absolute_path if absolute_path.is_dir() else absolute_path.parent
        explorer = shutil.which("explorer.exe") or "explorer.exe"
        argv = [explorer, str(folder)]
    popen_kwargs: dict[str, Any] = {"cwd": str(vault)}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    subprocess.Popen(argv, **popen_kwargs)
    return {
        "ok": True,
        "surface": "studio_acquisition_guarded_local_open",
        "target": target_id,
        "path": relative_path,
        "allowed": True,
        "authority": {
            "allowed_roots": list(_LOCAL_OPEN_PREFIXES),
            "shell_interpolation": False,
            "vault_relative_only": True,
            "canonical_mutation_allowed": False,
        },
    }


def _safe_local_open_path(vault: Path, open_path: str | Path) -> tuple[str, Path]:
    raw = str(open_path).strip().replace("\\", "/")
    if not raw:
        raise CockpitActionError("open path is empty")
    if Path(raw).is_absolute():
        raise CockpitActionError("open path must be vault-relative")
    if raw.startswith("../") or "/../" in raw or raw == "..":
        raise CockpitActionError("open path may not traverse outside the vault")
    if not any(raw.startswith(prefix) for prefix in _LOCAL_OPEN_PREFIXES):
        raise CockpitActionError("open path is outside the allowed generated research artifact roots")
    absolute = (vault / raw).resolve()
    if not _path_is_relative_to(absolute, vault):
        raise CockpitActionError("open path escapes vault root")
    if not absolute.exists():
        raise CockpitActionError(f"open path does not exist: {raw}")
    return raw, absolute


def _path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _coerce_candidate_kinds(value: str | list[str] | tuple[str, ...] | set[str] | None) -> set[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(",", " ").split()]
    else:
        parts = [str(part).strip() for part in value]
    cleaned = {part for part in parts if part}
    return cleaned or None


def _coerce_limit(value: int | str | None) -> int | None:
    if value in (None, ""):
        return None
    limit = int(value)
    if limit < 1:
        raise CockpitActionError("--limit must be at least 1")
    return limit


def _coerce_schedule_ids(value: str | list[str] | tuple[str, ...] | set[str] | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(",", " ").split()]
    else:
        parts = [str(part).strip() for part in value]
    cleaned = tuple(part for part in parts if part)
    return cleaned or None


def _pulse_schedule_evidence_refs(
    *,
    operator_approval_ref: str | None,
    permission_envelope_ref: str | None,
    run_queue_scope_ref: str | None,
    audit_identity_ref: str | None,
    runtime_adapter_scope_ref: str | None,
    rollback_plan_ref: str | None,
    external_scheduler_denial_ref: str | None,
    canonical_writeback_denial_ref: str | None,
) -> dict[str, str | None]:
    return {
        "operator_approval_ref": operator_approval_ref,
        "permission_envelope_ref": permission_envelope_ref,
        "run_queue_scope_ref": run_queue_scope_ref,
        "audit_identity_ref": audit_identity_ref,
        "runtime_adapter_scope_ref": runtime_adapter_scope_ref,
        "rollback_plan_ref": rollback_plan_ref,
        "external_scheduler_denial_ref": external_scheduler_denial_ref,
        "canonical_writeback_denial_ref": canonical_writeback_denial_ref,
    }


def _require_pulse_enqueue_evidence(
    *,
    operator_approved: bool,
    gate_policy_defined: bool,
    external_sender_allowance_present: bool,
    duplicate_work_fingerprint_reviewed: bool,
) -> None:
    values = {
        "operator_approved": operator_approved,
        "gate_policy_defined": gate_policy_defined,
        "external_sender_allowance_present": external_sender_allowance_present,
        "duplicate_work_fingerprint_reviewed": duplicate_work_fingerprint_reviewed,
    }
    missing = [flag for key, flag in _PULSE_REVIEW_REQUIRED_EVIDENCE.items() if not values[key]]
    if missing:
        raise CockpitActionError(
            "pulse_enqueue_approved requires evidence flags: " + ", ".join(missing)
        )


def _run_pulse_schedule_activation_gate(
    vault: Path,
    *,
    write_request: bool,
    schedule_ids: str | list[str] | tuple[str, ...] | set[str] | None,
    evidence_refs: dict[str, str | None],
) -> dict[str, Any]:
    try:
        from runtime.pulse.native_schedule_activation_gate import (
            build_pulse_native_schedule_activation_gate,
            write_pulse_native_schedule_activation_request,
        )

        normalized_schedule_ids = _coerce_schedule_ids(schedule_ids)
        if write_request:
            return write_pulse_native_schedule_activation_request(
                vault,
                schedule_ids=normalized_schedule_ids,
                evidence_refs=evidence_refs,
            ).to_dict()
        return build_pulse_native_schedule_activation_gate(
            vault,
            schedule_ids=normalized_schedule_ids,
            evidence_refs=evidence_refs,
        ).to_dict()
    except Exception as exc:  # noqa: BLE001
        raise CockpitActionError(str(exc)) from exc


def _run_pulse_schedule_run_queue_audit_proof(
    vault: Path,
    *,
    write_proof: bool,
    schedule_ids: str | list[str] | tuple[str, ...] | set[str] | None,
    evidence_refs: dict[str, str | None],
) -> dict[str, Any]:
    try:
        from runtime.pulse.native_schedule_run_queue_audit_proof import (
            build_pulse_native_schedule_run_queue_audit_proof,
            write_pulse_native_schedule_run_queue_audit_proof,
        )

        normalized_schedule_ids = _coerce_schedule_ids(schedule_ids)
        if write_proof:
            return write_pulse_native_schedule_run_queue_audit_proof(
                vault,
                schedule_ids=normalized_schedule_ids,
                evidence_refs=evidence_refs,
            ).to_dict()
        return build_pulse_native_schedule_run_queue_audit_proof(
            vault,
            schedule_ids=normalized_schedule_ids,
            evidence_refs=evidence_refs,
        ).to_dict()
    except Exception as exc:  # noqa: BLE001
        raise CockpitActionError(str(exc)) from exc


def _run_pulse_schedule_supervised_activation_execution_proof(
    vault: Path,
    *,
    write_proof: bool,
    schedule_ids: str | list[str] | tuple[str, ...] | set[str] | None,
    evidence_refs: dict[str, str | None],
) -> dict[str, Any]:
    try:
        from runtime.pulse.native_schedule_supervised_activation_execution import (
            build_pulse_native_schedule_supervised_activation_execution,
            write_pulse_native_schedule_supervised_activation_execution_proof,
        )

        normalized_schedule_ids = _coerce_schedule_ids(schedule_ids)
        if write_proof:
            return write_pulse_native_schedule_supervised_activation_execution_proof(
                vault,
                schedule_ids=normalized_schedule_ids,
                evidence_refs=evidence_refs,
                execute_activation=False,
            ).to_dict()
        return build_pulse_native_schedule_supervised_activation_execution(
            vault,
            schedule_ids=normalized_schedule_ids,
            evidence_refs=evidence_refs,
        ).to_dict()
    except Exception as exc:  # noqa: BLE001
        raise CockpitActionError(str(exc)) from exc


def _run_pulse_schedule_live_runner(
    vault: Path,
    *,
    execute: bool,
    force_due: bool,
    schedule_ids: str | list[str] | tuple[str, ...] | set[str] | None,
) -> dict[str, Any]:
    try:
        from runtime.pulse.native_schedule_live_runner import (
            build_pulse_native_schedule_live_runner,
            write_pulse_native_schedule_live_runner_records,
        )

        normalized_schedule_ids = _coerce_schedule_ids(schedule_ids)
        if execute:
            return write_pulse_native_schedule_live_runner_records(
                vault,
                schedule_ids=normalized_schedule_ids,
                force_due=force_due,
                execute=True,
            ).to_dict()
        return build_pulse_native_schedule_live_runner(
            vault,
            schedule_ids=normalized_schedule_ids,
            force_due=force_due,
        ).to_dict()
    except Exception as exc:  # noqa: BLE001
        raise CockpitActionError(str(exc)) from exc


def _run_pulse_schedule_runtime_dispatch_proof(
    vault: Path,
    *,
    write_proof: bool,
    schedule_ids: str | list[str] | tuple[str, ...] | set[str] | None,
) -> dict[str, Any]:
    try:
        from runtime.pulse.native_schedule_runtime_dispatch_proof import (
            build_pulse_native_schedule_runtime_dispatch_proof,
            write_pulse_native_schedule_runtime_dispatch_proof,
        )

        normalized_schedule_ids = _coerce_schedule_ids(schedule_ids)
        if write_proof:
            return write_pulse_native_schedule_runtime_dispatch_proof(
                vault,
                schedule_ids=normalized_schedule_ids,
            ).to_dict()
        return build_pulse_native_schedule_runtime_dispatch_proof(
            vault,
            schedule_ids=normalized_schedule_ids,
        ).to_dict()
    except Exception as exc:  # noqa: BLE001
        raise CockpitActionError(str(exc)) from exc


def _run_pulse_enqueue_pipeline(
    vault: Path,
    *,
    dry_run: bool,
    recipient: str,
    candidate_kinds: set[str] | None,
    candidate_id: str | None,
    limit: int | None,
    skip_duplicate_check: bool,
    operator_approved: bool = False,
    gate_policy_defined: bool = False,
    external_sender_allowance_present: bool = False,
    duplicate_work_fingerprint_reviewed: bool = False,
) -> dict[str, Any]:
    try:
        from runtime.pulse.pipeline_runner import run_pulse_enqueue_pipeline

        return run_pulse_enqueue_pipeline(
            vault,
            operator_approved=operator_approved,
            gate_policy_defined=gate_policy_defined,
            external_sender_allowance_present=external_sender_allowance_present,
            duplicate_work_fingerprint_reviewed=duplicate_work_fingerprint_reviewed,
            dry_run=dry_run,
            candidate_kinds=candidate_kinds,
            candidate_id=candidate_id,
            default_recipient=recipient,
            limit=limit,
            skip_duplicate_check=skip_duplicate_check,
        ).to_dict()
    except Exception as exc:  # noqa: BLE001
        raise CockpitActionError(str(exc)) from exc


def run_acquisition_cockpit_action(
    vault_root: str | Path,
    *,
    action: str = "model",
    profile: str = "strikezone",
    source_class: str | None = None,
    source_path: str | Path | None = None,
    open_target: str | None = None,
    open_path: str | Path | None = None,
    briefing_input: str | None = None,
    reviewed: bool = False,
    reviewed_by: str = "operator",
    allow_non_preview: bool = False,
    confirm_action: bool = False,
    pulse_recipient: str = "Hermes",
    pulse_candidate_kinds: str | list[str] | tuple[str, ...] | set[str] | None = None,
    pulse_candidate_id: str | None = None,
    pulse_limit: int | str | None = None,
    pulse_skip_duplicate_check: bool = False,
    pulse_schedule_ids: str | list[str] | tuple[str, ...] | set[str] | None = None,
    pulse_force_due: bool = False,
    operator_approved: bool = False,
    gate_policy_defined: bool = False,
    external_sender_allowance_present: bool = False,
    duplicate_work_fingerprint_reviewed: bool = False,
    operator_approval_ref: str | None = None,
    permission_envelope_ref: str | None = None,
    run_queue_scope_ref: str | None = None,
    audit_identity_ref: str | None = None,
    runtime_adapter_scope_ref: str | None = None,
    rollback_plan_ref: str | None = None,
    external_scheduler_denial_ref: str | None = None,
    canonical_writeback_denial_ref: str | None = None,
) -> dict[str, Any]:
    """Run a governed Studio cockpit action and return a refreshed UI model."""
    _require_strikezone(profile)
    vault = _vault_path(vault_root)
    action_id = _normalize_action(action)
    _require_confirmation(action_id, confirm_action)

    if action_id == "model":
        return build_acquisition_cockpit_model(vault, profile=profile)

    if action_id == "pulse_schedule_runner_status":
        result = _pulse_schedule_runner_status(vault)
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=False,
            requires_confirmation=False,
            writes=[],
        )

    if action_id in {"pulse_schedule_live_runner_preview", "pulse_schedule_live_runner_execute"}:
        execute = action_id == "pulse_schedule_live_runner_execute"
        result = _run_pulse_schedule_live_runner(
            vault,
            execute=execute,
            force_due=pulse_force_due,
            schedule_ids=pulse_schedule_ids,
        )
        writes = list(result.get("writes") or []) if execute else []
        if execute and result.get("write_executed") and not writes:
            writes = list(_PULSE_SCHEDULE_LIVE_RUNNER_WRITE_ROOTS)
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=execute,
            requires_confirmation=execute,
            writes=writes,
        )

    if action_id in {"pulse_schedule_runtime_dispatch_proof", "pulse_schedule_runtime_dispatch_write_proof"}:
        write_proof = action_id == "pulse_schedule_runtime_dispatch_write_proof"
        result = _run_pulse_schedule_runtime_dispatch_proof(
            vault,
            write_proof=write_proof,
            schedule_ids=pulse_schedule_ids,
        )
        writes = list(result.get("writes") or []) if write_proof else []
        if write_proof and result.get("write_executed") and not writes:
            writes = list(_PULSE_SCHEDULE_RUNTIME_DISPATCH_WRITE_ROOTS)
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=write_proof,
            requires_confirmation=write_proof,
            writes=writes,
        )

    if action_id in {"pulse_schedule_activation_gate", "pulse_schedule_activation_request"}:
        evidence_refs = _pulse_schedule_evidence_refs(
            operator_approval_ref=operator_approval_ref,
            permission_envelope_ref=permission_envelope_ref,
            run_queue_scope_ref=run_queue_scope_ref,
            audit_identity_ref=audit_identity_ref,
            runtime_adapter_scope_ref=runtime_adapter_scope_ref,
            rollback_plan_ref=rollback_plan_ref,
            external_scheduler_denial_ref=external_scheduler_denial_ref,
            canonical_writeback_denial_ref=canonical_writeback_denial_ref,
        )
        write_request = action_id == "pulse_schedule_activation_request"
        result = _run_pulse_schedule_activation_gate(
            vault,
            write_request=write_request,
            schedule_ids=pulse_schedule_ids,
            evidence_refs=evidence_refs,
        )
        writes = list(result.get("writes") or []) if write_request else []
        if write_request and not writes:
            writes = list(_PULSE_SCHEDULE_ACTIVATION_WRITE_ROOTS)
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=write_request,
            requires_confirmation=write_request,
            writes=writes,
        )

    if action_id in {"pulse_schedule_run_queue_audit_proof", "pulse_schedule_run_queue_audit_write_proof"}:
        evidence_refs = _pulse_schedule_evidence_refs(
            operator_approval_ref=operator_approval_ref,
            permission_envelope_ref=permission_envelope_ref,
            run_queue_scope_ref=run_queue_scope_ref,
            audit_identity_ref=audit_identity_ref,
            runtime_adapter_scope_ref=runtime_adapter_scope_ref,
            rollback_plan_ref=rollback_plan_ref,
            external_scheduler_denial_ref=external_scheduler_denial_ref,
            canonical_writeback_denial_ref=canonical_writeback_denial_ref,
        )
        write_proof = action_id == "pulse_schedule_run_queue_audit_write_proof"
        result = _run_pulse_schedule_run_queue_audit_proof(
            vault,
            write_proof=write_proof,
            schedule_ids=pulse_schedule_ids,
            evidence_refs=evidence_refs,
        )
        writes = list(result.get("writes") or []) if write_proof else []
        if write_proof and not writes:
            writes = list(_PULSE_SCHEDULE_RUN_QUEUE_WRITE_ROOTS)
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=write_proof,
            requires_confirmation=write_proof,
            writes=writes,
        )

    if action_id in {
        "pulse_schedule_supervised_activation_execution_proof",
        "pulse_schedule_supervised_activation_execution_write_proof",
    }:
        evidence_refs = _pulse_schedule_evidence_refs(
            operator_approval_ref=operator_approval_ref,
            permission_envelope_ref=permission_envelope_ref,
            run_queue_scope_ref=run_queue_scope_ref,
            audit_identity_ref=audit_identity_ref,
            runtime_adapter_scope_ref=runtime_adapter_scope_ref,
            rollback_plan_ref=rollback_plan_ref,
            external_scheduler_denial_ref=external_scheduler_denial_ref,
            canonical_writeback_denial_ref=canonical_writeback_denial_ref,
        )
        write_proof = action_id == "pulse_schedule_supervised_activation_execution_write_proof"
        result = _run_pulse_schedule_supervised_activation_execution_proof(
            vault,
            write_proof=write_proof,
            schedule_ids=pulse_schedule_ids,
            evidence_refs=evidence_refs,
        )
        writes = list(result.get("writes") or []) if write_proof else []
        if write_proof and not writes:
            writes = list(_PULSE_SCHEDULE_SUPERVISED_ACTIVATION_WRITE_ROOTS)
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=write_proof,
            requires_confirmation=write_proof,
            writes=writes,
        )

    if action_id == "pulse_enqueue_preview":
        result = _run_pulse_enqueue_pipeline(
            vault,
            dry_run=True,
            recipient=pulse_recipient,
            candidate_kinds=_coerce_candidate_kinds(pulse_candidate_kinds),
            candidate_id=pulse_candidate_id,
            limit=_coerce_limit(pulse_limit),
            skip_duplicate_check=pulse_skip_duplicate_check,
        )
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=False,
            requires_confirmation=False,
            writes=[],
        )

    if action_id == "pulse_enqueue_approved":
        _require_pulse_enqueue_evidence(
            operator_approved=operator_approved,
            gate_policy_defined=gate_policy_defined,
            external_sender_allowance_present=external_sender_allowance_present,
            duplicate_work_fingerprint_reviewed=duplicate_work_fingerprint_reviewed,
        )
        result = _run_pulse_enqueue_pipeline(
            vault,
            dry_run=False,
            recipient=pulse_recipient,
            candidate_kinds=_coerce_candidate_kinds(pulse_candidate_kinds),
            candidate_id=pulse_candidate_id,
            limit=_coerce_limit(pulse_limit),
            skip_duplicate_check=pulse_skip_duplicate_check,
            operator_approved=operator_approved,
            gate_policy_defined=gate_policy_defined,
            external_sender_allowance_present=external_sender_allowance_present,
            duplicate_work_fingerprint_reviewed=duplicate_work_fingerprint_reviewed,
        )
        writes = list(_PULSE_ENQUEUE_WRITE_ROOTS) if int(result.get("plan_preflight_count", 0) or 0) else []
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=True,
            requires_confirmation=True,
            writes=writes,
        )

    if action_id == "init_repository":
        try:
            result = initialize_research_repository_template(
                vault,
                profile=profile,
                confirm_action=True,
            )
        except ResearchRepositoryTemplateError as exc:
            raise CockpitActionError(str(exc)) from exc
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=True,
            requires_confirmation=True,
            writes=list(result.get("writes", [])),
        )

    if action_id == "import_file":
        if not source_class:
            raise CockpitActionError("--source-class is required for import-file")
        if source_path is None:
            raise CockpitActionError("--source-file is required for import-file")
        result = import_research_file(
            vault,
            source_class=source_class,
            source_path=source_path,
            profile=profile,
        )
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=True,
            requires_confirmation=True,
            writes=list(result.get("writes", [])),
        )

    if action_id == "import_staged_file":
        if not source_class:
            raise CockpitActionError("--source-class is required for import-staged-file")
        if source_path is None:
            raise CockpitActionError("--source-file is required for import-staged-file")
        try:
            result = import_staged_research_file(
                vault,
                source_class=source_class,
                source_path=source_path,
                profile=profile,
                confirm_action=True,
            )
        except (ResearchInboxImportError, AcquisitionValidationError, ValueError) as exc:
            raise CockpitActionError(str(exc)) from exc
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=True,
            requires_confirmation=True,
            writes=list(result.get("writes", [])),
        )

    if action_id == "import_inbox":
        try:
            result = import_research_inbox(
                vault,
                profile=profile,
                confirm_action=True,
            )
        except (ResearchInboxImportError, AcquisitionValidationError, ValueError) as exc:
            raise CockpitActionError(str(exc)) from exc
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=True,
            requires_confirmation=True,
            writes=list(result.get("writes", [])),
        )

    if action_id == "open_local_path":
        result = _open_local_path(vault, open_path=open_path, target=open_target)
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=False,
            requires_confirmation=False,
            writes=[],
        )

    if action_id == "clear_active_intake":
        result = clear_active_research_intake(vault, profile=profile)
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=result,
            write_action=True,
            requires_confirmation=True,
            writes=list(result.get("writes", [])),
        )

    if action_id in {"preview_read_only", "preview_write"}:
        try:
            preview = preview_research_imports(vault, profile=profile, write=action_id == "preview_write")
        except (ResearchImportPreviewError, AcquisitionValidationError, AcquisitionBuildError) as exc:
            raise CockpitActionError(str(exc)) from exc
        summary = preview.to_summary()
        writes = _preview_writes(summary) if summary.get("write") else []
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=summary,
            write_action=bool(summary.get("write")),
            requires_confirmation=action_id == "preview_write",
            writes=writes,
        )

    if action_id == "promote_reviewed_preview":
        if not reviewed:
            raise CockpitActionError("--reviewed is required for promote-reviewed-preview")
        if not briefing_input:
            raise CockpitActionError("--briefing-input is required for promote-reviewed-preview")
        try:
            promotion = promote_research_preview_pack(
                vault,
                profile=profile,
                briefing_ready_input_set_path=briefing_input,
                reviewed_by=reviewed_by,
            )
        except ResearchPreviewPromotionError as exc:
            raise CockpitActionError(str(exc)) from exc
        summary = promotion.to_summary()
        writes = [str(summary["latest_pointer_path"])]
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=summary,
            write_action=True,
            requires_confirmation=True,
            writes=writes,
        )

    if action_id == "verify_research_sbp":
        try:
            verification = verify_research_preview_sbp_consumption(
                vault,
                profile=profile,
                require_promoted_preview=not allow_non_preview,
            )
        except ResearchSBPConsumptionVerificationError as exc:
            raise CockpitActionError(str(exc)) from exc
        summary = verification.to_summary()
        return _with_action_result(
            vault,
            profile,
            action_id=action_id,
            result=summary,
            write_action=False,
            requires_confirmation=False,
            writes=[],
        )

    raise CockpitActionError(f"unhandled cockpit action: {action_id}")


def _safe_destination(vault: Path, source_class: str, source_path: Path) -> Path:
    if source_class not in STRIKEZONE_RESEARCH_DROP_FOLDERS:
        raise ValueError(f"unknown source_class: {source_class}")
    if not source_path.exists() or not source_path.is_file():
        raise ValueError(f"research source file does not exist: {source_path}")
    suffix = source_path.suffix.lower()
    if suffix not in SUPPORTED_INTAKE_SUFFIXES:
        raise ValueError(f"unsupported research file suffix: {suffix}")

    dest_dir = (vault / STRIKEZONE_RESEARCH_DROP_FOLDERS[source_class]).resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    if vault not in dest_dir.parents and dest_dir != vault:
        raise ValueError("destination folder escapes vault root")

    safe_name = Path(source_path.name).name
    destination = dest_dir / safe_name
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    for index in range(2, 1000):
        candidate = dest_dir / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise ValueError("could not choose a non-overwriting destination filename")


def _clear_archive_root(vault: Path) -> tuple[str, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_base = (vault / STRIKEZONE_RESEARCH_DROP_ROOT / "_archive").resolve()
    if vault != archive_base and vault not in archive_base.parents:
        raise ValueError("active intake archive root escapes vault root")
    for index in range(1, 1000):
        clear_id = timestamp if index == 1 else f"{timestamp}-{index}"
        candidate = archive_base / clear_id
        if not candidate.exists():
            return clear_id, candidate
    raise ValueError("could not choose a non-overwriting active intake archive folder")


def _clearable_intake_files(vault: Path) -> list[tuple[str, str, Path, Path]]:
    ignored = {"readme.md", "manifest.example.json", "research-imports.example.json", ".gitkeep"}
    files: list[tuple[str, str, Path, Path]] = []
    for area, folders in (
        ("imported-sources", STRIKEZONE_RESEARCH_DROP_FOLDERS),
        ("staged-inbox", STRIKEZONE_RESEARCH_INBOX_FOLDERS),
    ):
        for source_class, folder_rel in folders.items():
            folder = (vault / folder_rel).resolve()
            if not folder.exists() or not folder.is_dir():
                continue
            if vault != folder and vault not in folder.parents:
                raise ValueError(f"active intake folder escapes vault root: {folder_rel}")
            for path in sorted(folder.rglob("*")):
                if not path.is_file():
                    continue
                name = path.name.lower()
                if name.startswith(".") or name in ignored:
                    continue
                files.append((area, source_class, path, folder))
    return files


def _safe_clear_archive_destination(
    vault: Path,
    archive_root: Path,
    *,
    area: str,
    source_class: str,
    source_path: Path,
    source_base: Path,
) -> Path:
    rel_inside = source_path.relative_to(source_base)
    destination = (archive_root / area / source_class / rel_inside).resolve()
    if vault != destination and vault not in destination.parents:
        raise ValueError("active intake archive destination escapes vault root")
    if not destination.exists():
        return destination
    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    for index in range(2, 1000):
        candidate = parent / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise ValueError("could not choose a non-overwriting archive filename")


def clear_active_research_intake(
    vault_root: str | Path,
    *,
    profile: str = "strikezone",
) -> dict[str, Any]:
    """Archive current staged/imported local intake files without deleting them."""

    _require_strikezone(profile)
    vault = _vault_path(vault_root)
    files = _clearable_intake_files(vault)
    clear_id, archive_root = _clear_archive_root(vault)
    archived: list[dict[str, Any]] = []
    writes: list[str] = []

    for area, source_class, source_path, source_base in files:
        destination = _safe_clear_archive_destination(
            vault,
            archive_root,
            area=area,
            source_class=source_class,
            source_path=source_path,
            source_base=source_base,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(destination))
        source_rel = source_path.relative_to(vault).as_posix()
        destination_rel = destination.relative_to(vault).as_posix()
        archived.append(
            {
                "area": area,
                "source_class": source_class,
                "source_path": source_rel,
                "archive_path": destination_rel,
            }
        )
        writes.append(destination_rel)

    ledger_path = (vault / _ACTIVE_INTAKE_CLEAR_LEDGER_PATH).resolve()
    if vault != ledger_path and vault not in ledger_path.parents:
        raise ValueError("active intake clear ledger path escapes vault root")
    record = {
        "cleared_at": datetime.now(timezone.utc).isoformat(),
        "clear_id": clear_id,
        "profile": profile,
        "archive_root": archive_root.relative_to(vault).as_posix(),
        "archived_count": len(archived),
        "archived": archived,
        "deletes_files": False,
        "clears_preview_packs": False,
        "clears_latest_pointer": False,
    }
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    ledger_rel = ledger_path.relative_to(vault).as_posix()
    writes.append(ledger_rel)

    return {
        "ok": True,
        "surface": _COCKPIT_ID,
        "profile": profile,
        "action": "clear-active-intake",
        "clear_id": clear_id,
        "archive_root": record["archive_root"],
        "archived_count": len(archived),
        "archived_source_count": sum(1 for item in archived if item["area"] == "imported-sources"),
        "archived_staged_count": sum(1 for item in archived if item["area"] == "staged-inbox"),
        "archived": archived,
        "writes": writes,
        "deletes_files": False,
        "clears_preview_packs": False,
        "clears_latest_pointer": False,
        "authority": _authority_boundary(),
    }


def import_research_file(
    vault_root: str | Path,
    *,
    source_class: str,
    source_path: str | Path,
    profile: str = "strikezone",
) -> dict[str, Any]:
    """Explicitly import and standardize an operator-selected file."""
    _require_strikezone(profile)
    vault = _vault_path(vault_root)
    source = Path(source_path).resolve()
    if source_class not in STRIKEZONE_RESEARCH_DROP_FOLDERS:
        raise ValueError(f"unknown source_class: {source_class}")
    if source.suffix.lower() not in SUPPORTED_INTAKE_SUFFIXES:
        raise ValueError(f"unsupported research file suffix: {source.suffix.lower()}")
    standardized = standardize_research_intake_file(
        vault,
        source_path=source,
        source_class=source_class,
        profile=profile,
        write_daily_index=True,
    )
    return {
        "ok": True,
        "surface": _COCKPIT_ID,
        "profile": profile,
        "source_class": source_class,
        "source_path": str(source),
        "destination_path": standardized["destination_path"],
        "raw_destination_path": standardized["raw_destination_path"],
        "raw_source_path": standardized["raw_source_path"],
        "standardized_artifact_path": standardized["standardized_artifact_path"],
        "trading_brief_path": standardized["trading_brief_path"],
        "dashboard_ledger_path": standardized["dashboard_ledger_path"],
        "daily_note_path": standardized["daily_note_path"],
        "daily_index_path": standardized["daily_index_path"],
        "dashboard_ready": standardized["dashboard_ready"],
        "normalization_method": standardized["extraction_method"],
        "transform_method": standardized["transform_method"],
        "source_claims_unverified": standardized["source_claims_unverified"],
        "open_targets": standardized["open_targets"],
        "writes": list(standardized.get("writes", [])),
        "authority": _authority_boundary(),
    }


def _html_text(value: Any) -> str:
    return html.escape(str(value))


def _html_code(value: Any) -> str:
    return html.escape(str(value), quote=False)


def _render_tags(values: list[Any]) -> str:
    if not values:
        return "<span class='muted'>none</span>"
    return "".join(f"<span class='tag'>{_html_text(value)}</span>" for value in values)


def _render_list(items: list[Any], *, empty: str) -> str:
    if not items:
        return f"<p class='muted'>{_html_text(empty)}</p>"
    return "<ul>" + "".join(f"<li>{_html_text(item)}</li>" for item in items) + "</ul>"


def _yes_no(value: Any) -> str:
    return "yes" if bool(value) else "no"


def _status_class(enabled: bool) -> str:
    return "ready" if enabled else "blocked"


def _metric_card(label: str, value: Any, detail: str, state: str = "neutral") -> str:
    return (
        f"<section class='metric {state}'>"
        f"<span>{_html_text(label)}</span>"
        f"<strong>{_html_text(value)}</strong>"
        f"<p>{_html_text(detail)}</p>"
        "</section>"
    )


def _render_inbox_candidates(candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return "<p class='muted'>No staged inbox files.</p>"
    items: list[str] = []
    for candidate in candidates:
        label = _html_text(candidate.get("display_name") or candidate.get("filename") or "staged file")
        readiness_label = _html_text(candidate.get("readiness_label") or "unknown")
        warnings = list(candidate.get("warnings") or [])
        warning_text = f" - {_html_text('; '.join(warnings))}" if warnings else ""
        items.append(f"<li><strong>{label}</strong> <span class='muted'>({readiness_label}){warning_text}</span></li>")
    return "<ul class='candidate-list'>" + "".join(items) + "</ul>"


def _render_rehearsal_ladder(rehearsal: dict[str, Any]) -> str:
    steps = list(rehearsal.get("steps") or [])
    if not steps:
        return "<p class='muted'>No rehearsal steps available.</p>"
    items: list[str] = []
    for item in steps:
        state = _html_text(item.get("state", "pending"))
        label = _html_text(item.get("label", "step"))
        detail = _html_text(item.get("detail", ""))
        action = _html_text(item.get("action_id") or "none")
        command = _html_code(item.get("command") or "")
        blockers = [str(blocker) for blocker in item.get("blockers", [])]
        blockers_html = _render_list(blockers, empty="No blockers.")
        command_html = f"<pre>{command}</pre>" if command else "<p class='muted'>Use the source-class upload controls.</p>"
        items.append(
            f"<section class='step-card {state}'>"
            "<div class='card-head'>"
            f"<h3>{label}</h3>"
            f"<span class='pill {state}'>{state}</span>"
            "</div>"
            f"<p>{detail}</p>"
            f"<p class='muted'>Action: <strong>{action}</strong> / "
            f"{'write' if item.get('write_action') else 'read-only'} / "
            f"{'confirmation required' if item.get('requires_confirmation') else 'no confirmation'}</p>"
            f"{command_html}"
            f"{blockers_html}"
            "</section>"
        )
    return "<div class='rehearsal-grid'>" + "".join(items) + "</div>"


def _render_manual_test_readiness(readiness: dict[str, Any]) -> str:
    if not readiness:
        return "<p class='muted'>Manual test readiness is unavailable.</p>"
    development_ready = bool(readiness.get("development_ready_for_manual_real_file_test"))
    manual_input_ready = bool(readiness.get("manual_input_ready"))
    remaining_dev = list(readiness.get("remaining_development_passes") or [])
    manual_blockers = list(readiness.get("manual_blockers") or [])
    development_blockers = list(readiness.get("development_blockers") or [])
    coverage_warnings = list(readiness.get("coverage_warnings") or [])
    sequence = list(readiness.get("manual_test_sequence") or [])
    remaining_dev_text = ", ".join(str(item) for item in remaining_dev) if remaining_dev else "none"
    summary = [
        ("Development surface", "available" if development_ready else "blocked"),
        ("Manual proof", "ready for preview" if manual_input_ready else "in progress"),
        ("Current stage", str(readiness.get("current_rehearsal_step_id") or "complete")),
        ("Development cleanup", "none blocking" if not remaining_dev else remaining_dev_text),
    ]
    summary_html = "".join(
        f"<div><span>{_html_text(label)}</span><strong>{_html_text(value)}</strong></div>"
        for label, value in summary
    )
    sequence_items = [
        f"{item.get('label', item.get('id', 'step'))}: {item.get('operator_action', '')}"
        for item in sequence
    ]
    return (
        "<div class='boundary-grid'>"
        f"{summary_html}"
        "</div>"
        "<div class='section split-list'>"
        "<section>"
        "<h3>Development blockers</h3>"
        f"{_render_list([str(item) for item in development_blockers], empty='No development blockers remain.')}"
        "</section>"
        "<section>"
        "<h3>Manual blockers</h3>"
        f"{_render_list([str(item) for item in manual_blockers], empty='No manual blockers reported.')}"
        "</section>"
        "<section>"
        "<h3>Coverage warnings</h3>"
        f"{_render_list([str(item) for item in coverage_warnings], empty='No coverage warnings reported.')}"
        "</section>"
        "</div>"
        "<div class='section'>"
        "<h3>Later manual test sequence</h3>"
        f"{_render_list(sequence_items, empty='No manual sequence reported.')}"
        "</div>"
    )


def _render_source_pack_review_handoff(handoff: dict[str, Any]) -> str:
    if not handoff:
        return "<p class='muted'>Source-pack review handoff is unavailable.</p>"

    preview = handoff.get("source_pack_preview", {})
    evidence = handoff.get("evidence", {})
    review = handoff.get("review_state", {})
    paths = handoff.get("operator_handoff_paths", {})
    actions = handoff.get("operator_handoff_actions", {})
    blockers = handoff.get("blocked_backend_dependencies", [])
    promotion_action = actions.get("promote_reviewed_preview", {})
    verify_action = actions.get("verify_research_sbp", {})

    blocker_items = [
        " | ".join(
            [
                f"missing contract: {blocker.get('missing_contract', '')}",
                f"affected Phase 10 surface: {blocker.get('affected_phase10_surface', '')}",
                f"lower-phase owner/surface: {blocker.get('lower_phase_owner_surface', '')}",
                f"minimum proof needed: {blocker.get('minimum_proof_needed', '')}",
                f"blocked action reason: {blocker.get('blocked_action_reason', '')}",
            ]
        )
        for blocker in blockers
    ]

    return (
        "<dl>"
        f"<dt>Preview pack</dt><dd><code>{_html_code(preview.get('latest_pack_root') or 'none')}</code></dd>"
        f"<dt>Preview candidates</dt><dd>{int(preview.get('candidate_count', 0) or 0)}</dd>"
        f"<dt>Preview BRIS</dt><dd><code>{_html_code(evidence.get('briefing_ready_input_set_path') or 'none')}</code></dd>"
        f"<dt>Normalized pack</dt><dd><code>{_html_code(evidence.get('normalized_source_pack_path') or 'none')}</code></dd>"
        f"<dt>Latest pointer</dt><dd><code>{_html_code(paths.get('promoted_latest_pointer') or 'none')}</code></dd>"
        f"<dt>Reviewed by</dt><dd>{_html_text(review.get('reviewed_by') or 'not promoted')}</dd>"
        f"<dt>SBP ready</dt><dd>{_html_text('yes' if review.get('default_verify_ready') else 'no')}</dd>"
        "</dl>"
        "<div class='split-list'>"
        "<div><h3>Source packets</h3>"
        f"{_render_list(list(evidence.get('source_packet_paths', [])), empty='No source packets reported.')}"
        "</div>"
        "<div><h3>Operator handoff commands</h3>"
        f"<pre>{_html_code(promotion_action.get('studio_command') or '')}</pre>"
        f"<pre>{_html_code(verify_action.get('studio_command') or '')}</pre>"
        "</div>"
        "</div>"
        "<h3>Blocked backend dependencies</h3>"
        f"{_render_list(blocker_items, empty='No blocked backend dependencies reported.')}"
    )


def render_acquisition_cockpit_html(model: dict[str, Any]) -> str:
    """Render the cockpit model as a static local operator surface."""
    title = _html_text(model.get("title", "Studio Acquisition Intake Cockpit"))
    profile = _html_text(model.get("profile", "strikezone"))
    phase = _html_text(model.get("phase", "Phase 10A0"))
    status = model.get("status", {})
    readiness = status.get("readiness", {})
    source_count = int(status.get("source_count", 0) or 0)
    missing_classes = list(status.get("missing_recommended_source_classes", []))
    recommended_classes = list(status.get("recommended_source_classes", []))
    optional_classes = list(status.get("optional_source_classes", []))
    latest_pointer_path = status.get("latest_pointer_path", "")
    latest_pointer = status.get("latest_pointer") or {}
    latest_preview_candidate = status.get("latest_preview_candidate") or {}
    latest_preview_bris_path = latest_preview_candidate.get("briefing_ready_input_set_path", "none")
    preview_candidate_count = int(status.get("preview_candidate_count", 0) or 0)
    inbox_summary = status.get("inbox_readiness_summary", {})
    inbox_candidate_count = int(inbox_summary.get("candidate_count", 0) or 0)
    inbox_warning_count = int(inbox_summary.get("warning_count", 0) or 0)
    briefing_input_path = latest_pointer.get("briefing_ready_input_set_path", "none")
    current_pointer_consumable = bool(readiness.get("current_pointer_consumable_by_sbp"))
    reviewed_preview_promoted = bool(readiness.get("reviewed_preview_promoted"))
    default_verify_ready = bool(readiness.get("default_verify_ready"))
    default_verify_error = status.get("default_verify_error")
    rehearsal_html = _render_rehearsal_ladder(model.get("rehearsal", {}))
    manual_test_readiness_html = _render_manual_test_readiness(model.get("manual_test_readiness", {}))
    source_pack_review_html = _render_source_pack_review_handoff(model.get("source_pack_review_handoff", {}))

    cards_html = []
    for card in model.get("source_class_cards", []):
        source_class = _html_text(card.get("source_class", "unknown"))
        folder = _html_code(card.get("folder", ""))
        state = "missing" if card.get("missing") else "ready"
        role = "optional" if card.get("optional") else "recommended"
        file_count = int(card.get("file_count", 0) or 0)
        inbox_candidate_count_for_card = int(card.get("inbox_candidate_count", 0) or 0)
        inbox_metadata_ready_count = int(card.get("inbox_metadata_ready_count", 0) or 0)
        inbox_warning_count_for_card = int(card.get("inbox_warning_count", 0) or 0)
        inbox_label = _html_text(card.get("inbox_readiness_label", "empty"))
        inbox_candidates = _render_inbox_candidates(list(card.get("inbox_candidates", [])))
        import_action = card.get("import_action", {})
        import_command = _html_code(import_action.get("studio_command", ""))
        destination = _html_code(import_action.get("destination_folder", card.get("folder", "")))
        suffix_tags = _render_tags(list(card.get("accepted_suffixes", [])))
        cards_html.append(
            f"<section class='source-card {state}'>"
            "<div class='card-head'>"
            f"<h3>{source_class}</h3>"
            f"<span class='pill {state}'>{state}</span>"
            "</div>"
            f"<p class='source-role'>{_html_text(role)}</p>"
            "<dl>"
            f"<dt>Folder</dt><dd><code>{folder}</code></dd>"
            f"<dt>Files</dt><dd>{file_count}</dd>"
            f"<dt>Inbox</dt><dd>{inbox_candidate_count_for_card} staged / {inbox_metadata_ready_count} metadata ready / {inbox_warning_count_for_card} warnings</dd>"
            f"<dt>Readiness</dt><dd>{inbox_label}</dd>"
            f"<dt>Destination</dt><dd><code>{destination}</code></dd>"
            "</dl>"
            f"{inbox_candidates}"
            f"<div class='tags'>{suffix_tags}</div>"
            "<div class='command-block'>"
            "<span>Import command</span>"
            f"<pre>{import_command}</pre>"
            "</div>"
            "</section>"
        )

    controls_html = []
    for control in model.get("controls", []):
        enabled = bool(control.get("enabled"))
        state = _status_class(enabled)
        label = _html_text(control.get("label", "control"))
        command = _html_code(control.get("studio_command") or control.get("command", ""))
        write = "write action" if control.get("write_action") else "read-only"
        confirm = "confirmation required" if control.get("requires_confirmation") else "no confirmation"
        reason = control.get("reason_if_disabled") if not enabled else None
        reason_html = f"<p class='reason'>{_html_text(reason)}</p>" if reason else ""
        writes_only = [str(path) for path in control.get("writes_only", [])]
        writes_html = _render_tags(writes_only)
        controls_html.append(
            f"<section class='control-card {state}'>"
            "<div class='card-head'>"
            f"<h3>{label}</h3>"
            f"<span class='pill {state}'>{'enabled' if enabled else 'disabled'}</span>"
            "</div>"
            f"<p>{_html_text(write)} / {_html_text(confirm)}</p>"
            f"{reason_html}"
            f"<div class='write-targets'><span>Write targets</span><div>{writes_html}</div></div>"
            "<div class='command-block'>"
            "<span>Studio command</span>"
            f"<pre>{command}</pre>"
            "</div>"
            "</section>"
        )

    action_html = ""
    if model.get("action"):
        action = model["action"]
        writes = action.get("writes", []) or []
        action_result = html.escape(json.dumps(action.get("result", {}), indent=2, default=str))
        action_html = (
            "<section class='panel action-panel'>"
            "<div class='panel-title'><h2>Last action</h2></div>"
            "<div class='action-summary'>"
            f"<span class='pill ready'>{_html_text(action.get('status', 'unknown'))}</span>"
            f"<strong>{_html_text(action.get('id', 'unknown'))}</strong>"
            f"<span>{'write action' if action.get('write_action') else 'read-only'}</span>"
            "</div>"
            "<h3>Writes</h3>"
            f"{_render_list(list(writes), empty='No writes recorded for this action.')}"
            "<details><summary>Action result JSON</summary>"
            f"<pre>{action_result}</pre>"
            "</details>"
            "</section>"
        )

    boundary = model.get("authority", {})
    browser = "none" if not boundary.get("browser_scope") else str(boundary.get("browser_scope"))
    network = "none" if not boundary.get("network_scope") else str(boundary.get("network_scope"))
    boundary_items = [
        ("Browser authority", browser),
        ("Network/provider calls", network),
        ("MCP changed", _yes_no(boundary.get("mcp_scope_changed"))),
        ("Delivery changed", _yes_no(boundary.get("delivery_changed"))),
        ("Scheduler changed", _yes_no(boundary.get("cron_or_scheduler_changed"))),
        ("Canonical mutation", "allowed" if boundary.get("canonical_mutation_allowed") else "blocked"),
    ]
    boundary_html = "".join(
        f"<div><span>{_html_text(label)}</span><strong>{_html_text(value)}</strong></div>"
        for label, value in boundary_items
    )
    boundary_bullets = _render_list(list(model.get("boundaries", [])), empty="No authority boundaries reported.")
    next_actions = _render_list(list(status.get("next_actions", [])), empty="No next actions reported.")
    warnings = _render_list(list(status.get("warnings", [])), empty="No warnings reported.")

    metrics = "".join(
        [
            _metric_card("Source files", source_count, "Declared local/import research files", "ready" if source_count else "blocked"),
            _metric_card("Staged inbox", inbox_candidate_count, f"{inbox_warning_count} readiness warnings", "ready" if inbox_candidate_count and inbox_warning_count == 0 else "blocked" if inbox_candidate_count else "neutral"),
            _metric_card("Missing recommended", len(missing_classes), ", ".join(missing_classes) or "none", "blocked" if missing_classes else "ready"),
            _metric_card("Current pointer SBP", "ready" if current_pointer_consumable else "blocked", str(briefing_input_path), "ready" if current_pointer_consumable else "blocked"),
            _metric_card("Reviewed preview", "ready" if reviewed_preview_promoted else "not ready", str(default_verify_error or "default verifier ready"), "ready" if default_verify_ready else "blocked"),
        ]
    )

    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f6f7;
      --panel: #ffffff;
      --text: #202124;
      --muted: #5f6368;
      --line: #d7dce2;
      --command: #101418;
      --ready: #1f7a5c;
      --ready-bg: #e7f5ee;
      --blocked: #b45309;
      --blocked-bg: #fff4df;
      --danger: #b42318;
      --accent: #2457a6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 24px; }}
    h1, h2, h3, p {{ margin-top: 0; }}
    h1 {{ font-size: 32px; line-height: 1.15; margin-bottom: 8px; }}
    h2 {{ font-size: 18px; line-height: 1.25; }}
    h3 {{ font-size: 15px; line-height: 1.25; margin-bottom: 0; }}
    code, pre {{
      background: var(--command);
      color: #edf2f7;
      border-radius: 6px;
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
    }}
    code {{ padding: 2px 6px; overflow-wrap: anywhere; }}
    pre {{ margin: 8px 0 0; padding: 10px; white-space: pre-wrap; overflow-wrap: anywhere; overflow-x: auto; }}
    ul {{ margin: 0; padding-left: 20px; }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
      margin-bottom: 20px;
    }}
    .eyebrow {{ margin-bottom: 6px; color: var(--accent); font-size: 13px; font-weight: 700; text-transform: uppercase; }}
    .subtitle {{ color: var(--muted); margin-bottom: 0; }}
    .pill-row {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }}
    .pill, .tag {{
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      border-radius: 999px;
      border: 1px solid var(--line);
      padding: 3px 9px;
      font-size: 12px;
      font-weight: 700;
      background: #fff;
      white-space: nowrap;
    }}
    .pill.ready, .pill.complete, .tag.ready {{ color: var(--ready); background: var(--ready-bg); border-color: #9dd8c0; }}
    .pill.current {{ color: var(--accent); background: #eef4ff; border-color: #a8c4ef; }}
    .pill.missing, .pill.blocked {{ color: var(--blocked); background: var(--blocked-bg); border-color: #f2c46b; }}
    .metric-grid, .source-grid, .control-grid, .boundary-grid, .rehearsal-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }}
    .split-list {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }}
    .metric, .panel, .source-card, .control-card, .step-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 1px 2px rgba(16, 20, 24, 0.04);
    }}
    .metric {{ min-height: 118px; }}
    .metric span, .command-block span, .write-targets span, .boundary-grid span {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .metric strong {{ display: block; margin: 10px 0 6px; font-size: 28px; line-height: 1; }}
    .metric p, .source-card p, .control-card p, .step-card p, .panel p {{ color: var(--muted); margin-bottom: 0; }}
    .metric.ready, .source-card.ready, .control-card.ready, .step-card.complete {{ border-left: 5px solid var(--ready); }}
    .step-card.current {{ border-left: 5px solid var(--accent); }}
    .metric.blocked, .source-card.missing, .control-card.blocked, .step-card.blocked {{ border-left: 5px solid var(--blocked); }}
    .section {{ margin-top: 18px; }}
    .panel-title, .card-head {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }}
    .source-role {{ font-size: 13px; text-transform: uppercase; font-weight: 700; }}
    dl {{ display: grid; grid-template-columns: 88px minmax(0, 1fr); gap: 8px 10px; margin: 0 0 12px; }}
    dt {{ color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; }}
    dd {{ margin: 0; min-width: 0; }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }}
    .command-block {{ margin-top: 12px; }}
    .reason {{ color: var(--danger) !important; font-weight: 700; }}
    .write-targets {{ display: grid; gap: 6px; margin-top: 10px; }}
    .boundary-grid div {{
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      min-height: 72px;
    }}
    .boundary-grid strong {{ display: block; margin-top: 8px; }}
    .action-summary {{ display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }}
    details {{ margin-top: 12px; }}
    summary {{ cursor: pointer; color: var(--accent); font-weight: 700; }}
    .muted {{ color: var(--muted); }}
    @media (max-width: 720px) {{
      main {{ padding: 16px; }}
      .topbar, .panel-title, .card-head {{ align-items: flex-start; flex-direction: column; }}
      .pill-row {{ justify-content: flex-start; }}
      dl {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <header class="topbar">
      <div>
        <p class="eyebrow">{phase}</p>
        <h1>{title}</h1>
        <p class="subtitle">Profile: <strong>{profile}</strong></p>
      </div>
      <div class="pill-row">
        <span class="pill ready">local-only</span>
        <span class="pill {source_state}">{source_label}</span>
        <span class="pill {review_state}">{review_label}</span>
      </div>
    </header>

    <section class="metric-grid">{metrics}</section>

    <section class="section panel">
      <div class="panel-title"><h2>Authority boundary</h2></div>
      <div class="boundary-grid">{boundary_html}</div>
      <div class="section">{boundary_bullets}</div>
    </section>

    <section class="section panel">
      <div class="panel-title"><h2>Workflow rehearsal</h2></div>
      {rehearsal}
    </section>

    <section class="section panel">
      <div class="panel-title"><h2>Manual test readiness</h2></div>
      {manual_test_readiness}
    </section>

    <section class="section panel">
      <div class="panel-title"><h2>Source-pack review handoff</h2></div>
      {source_pack_review_handoff}
    </section>

    <section class="section panel">
      <div class="panel-title">
        <h2>Source classes</h2>
        <div class="pill-row">
          <span class="pill">recommended: {recommended_count}</span>
          <span class="pill">optional: {optional_count}</span>
        </div>
      </div>
      <div class="source-grid">{cards}</div>
    </section>

    <section class="section panel">
      <div class="panel-title"><h2>Governed controls</h2></div>
      <div class="control-grid">{controls}</div>
    </section>

    <section class="section panel">
      <div class="panel-title"><h2>Current pointer</h2></div>
      <dl>
        <dt>Pointer</dt><dd><code>{latest_pointer_path}</code></dd>
        <dt>Briefing input</dt><dd><code>{briefing_input_path}</code></dd>
        <dt>Latest preview BRIS</dt><dd><code>{latest_preview_bris_path}</code></dd>
        <dt>Preview candidates</dt><dd>{preview_candidate_count}</dd>
        <dt>Default verify</dt><dd>{default_verify}</dd>
      </dl>
    </section>

    {action_html}

    <section class="section panel">
      <div class="panel-title"><h2>Next actions</h2></div>
      {next_actions}
    </section>

    <section class="section panel">
      <div class="panel-title"><h2>Warnings</h2></div>
      {warnings}
    </section>
  </main>
</body>
</html>
""".format(
        title=title,
        profile=profile,
        phase=phase,
        source_state="ready" if source_count else "blocked",
        source_label=f"{source_count} source files",
        review_state="ready" if reviewed_preview_promoted else "blocked",
        review_label="reviewed preview ready" if reviewed_preview_promoted else "reviewed preview pending",
        metrics=metrics,
        boundary_html=boundary_html,
        boundary_bullets=boundary_bullets,
        rehearsal=rehearsal_html,
        manual_test_readiness=manual_test_readiness_html,
        source_pack_review_handoff=source_pack_review_html,
        recommended_count=len(recommended_classes),
        optional_count=len(optional_classes),
        cards="\n".join(cards_html),
        controls="\n".join(controls_html),
        latest_pointer_path=_html_code(latest_pointer_path),
        briefing_input_path=_html_code(briefing_input_path),
        latest_preview_bris_path=_html_code(latest_preview_bris_path),
        preview_candidate_count=preview_candidate_count,
        default_verify=_html_text("ready" if default_verify_ready else str(default_verify_error or "not ready")),
        action_html=action_html,
        next_actions=next_actions,
        warnings=warnings,
    )
