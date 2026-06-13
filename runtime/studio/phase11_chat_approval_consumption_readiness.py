"""Phase 11 Chat approval-consumption readiness contract.

This surface inspects Chat-originated Studio approval requests and previews the
future exact-once consumption envelope. It does not approve, consume, execute,
reserve markers, write targets, or mutate approval records.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_router_contract import build_phase11_chat_router_contract
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.phase11_chat_approval_consumption_readiness.v1"
SURFACE_ID = "phase11_chat_approval_consumption_readiness_contract"
PASS_ID = "phase11-chat-approval-consumption-readiness-contract"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / EXECUTOR AVAILABLE"
NEXT_RECOMMENDED_PASS = "phase11-chat-approval-consumption-executor"
APPROVAL_CLASS = "studio_chat_approval_consumption_future"
MARKER_DIR = Path("runtime") / "studio" / "approvals" / "_chat_consumption_markers"

_CANONICAL_OR_HIGH_AUTHORITY_TARGET_ROOTS = (
    ("02_KNOWLEDGE/", "canonical_knowledge_root"),
    ("runtime/source_intelligence/", "source_pack_promotion_root"),
    ("runtime/acquisition/packs/", "source_pack_promotion_root"),
    ("runtime/graph/", "graph_promotion_root"),
)

POLICY_DOCS_CHECKED = [
    "06_AGENTS/ChaseOS-Deny-Default-Runtime-Policy.md",
    "06_AGENTS/Permission-Matrix.md",
    "06_AGENTS/Agent-Security-Model.md",
    "06_AGENTS/Browser-Operator-Policy.md",
    "06_AGENTS/Trust-Tiers.md",
    "runtime/policy/gateway_allowlists.json",
    "runtime/policy/protected_files.yaml",
]

_DENIED_ACTION_TO_DEPENDENCY_KEY = {
    "vault_write": "protected_file_write",
    "lifecycle_execution": "lifecycle_execution",
    "runtime_dispatch": "runtime_dispatch",
    "browser_or_shell_or_connector_authority": "browser_shell_connector_authority",
    "approval_consumption": "approval_consumption_execution",
    "protected_file_write": "protected_file_write",
    "hidden_memory_write": "canonical_knowledge_promotion",
    "credential_or_config_mutation": "credential_config_mutation",
    "source_pack_promotion": "source_pack_creation_promotion",
    "graph_mutation": "graph_canonical_mutation",
    "canonical_knowledge_promotion": "canonical_knowledge_promotion",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _approval_root(vault: Path) -> Path:
    return vault / StudioService.APPROVAL_DIR


def _safe_approval_payload(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, f"approval_artifact_read_failed:{exc}"
    except json.JSONDecodeError as exc:
        return None, f"approval_artifact_json_malformed:{exc}"
    if not isinstance(payload, dict):
        return None, "approval_artifact_json_not_object"
    return payload, None


def _approval_path(vault: Path, approval_id: str) -> Path:
    safe_id = "".join(c if c.isalnum() or c == "-" else "_" for c in str(approval_id or ""))
    return _approval_root(vault) / f"{safe_id}.json"


def _artifact_sha256(path: Path) -> str | None:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError:
        return None


def _metadata(payload: dict[str, Any] | None) -> dict[str, Any]:
    spec = (payload or {}).get("action_spec")
    if not isinstance(spec, dict):
        return {}
    metadata = spec.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _action_spec(payload: dict[str, Any] | None) -> dict[str, Any]:
    spec = (payload or {}).get("action_spec")
    return spec if isinstance(spec, dict) else {}


def _is_chat_originated(payload: dict[str, Any] | None) -> bool:
    metadata = _metadata(payload)
    spec = _action_spec(payload)
    return bool(
        metadata.get("phase11_chat_queue_write_proof") is True
        or metadata.get("chat_generated_proposal") is True
        or metadata.get("source_surface") == "phase11_chat_panel"
        or metadata.get("source_contract") == "phase11_chat_approval_queue_write_execution_proof"
        or spec.get("submitted_by") == "studio-chat"
    )


def _list_chat_approvals(vault: Path) -> list[dict[str, Any]]:
    root = _approval_root(vault)
    if not root.is_dir():
        return []
    results: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload, error = _safe_approval_payload(path)
        if error or not _is_chat_originated(payload):
            continue
        approval_id = str((payload or {}).get("approval_id") or path.stem)
        results.append(
            {
                "approval_id": approval_id,
                "path": path,
                "payload": payload,
                "status": str((payload or {}).get("status") or "unknown"),
            }
        )
    return results


def _select_approval(vault: Path, approval_id: str | None) -> dict[str, Any]:
    requested = _norm(approval_id)
    if requested:
        path = _approval_path(vault, requested)
        if not path.is_file():
            return {
                "requested_approval_id": requested,
                "selected": None,
                "error": "approval_artifact_not_found",
                "available_chat_approval_ids": [item["approval_id"] for item in _list_chat_approvals(vault)[:10]],
            }
        payload, error = _safe_approval_payload(path)
        return {
            "requested_approval_id": requested,
            "selected": {
                "approval_id": str((payload or {}).get("approval_id") or requested),
                "path": path,
                "payload": payload,
                "status": str((payload or {}).get("status") or "unknown"),
                "parse_error": error,
            },
            "error": error,
            "available_chat_approval_ids": [item["approval_id"] for item in _list_chat_approvals(vault)[:10]],
        }

    approvals = _list_chat_approvals(vault)
    return {
        "requested_approval_id": "",
        "selected": approvals[0] if approvals else None,
        "error": None if approvals else "no_chat_originated_approval_artifacts_found",
        "available_chat_approval_ids": [item["approval_id"] for item in approvals[:10]],
    }


def _target_path_state(vault: Path, spec: dict[str, Any]) -> dict[str, Any]:
    target_path = str(spec.get("target_path") or "")
    if not target_path:
        return {
            "target_path": "",
            "target_path_present": False,
            "target_path_under_vault": False,
            "target_file_exists": False,
            "target_file_written": False,
            "target_collision": False,
            "high_authority_target_policy": _high_authority_target_policy(target_path),
            "validation": None,
        }
    service = StudioService(vault)
    validation_payload: dict[str, Any] | None = None
    under_vault = False
    target_exists = False
    resolved_policy_path = target_path
    try:
        resolved = service._resolve_path(target_path)  # read-only validation; no mutation.
        under_vault = True
        target_exists = resolved.exists()
        resolved_policy_path = resolved.relative_to(vault).as_posix()
    except Exception:
        resolved = vault / target_path
    high_authority_policy = _high_authority_target_policy(resolved_policy_path)
    try:
        action = ActionSpec(
            action_type=str(spec.get("action_type") or "create_file"),
            target_path=target_path,
            content=str(spec.get("content") or ""),
            metadata=dict(spec.get("metadata") or {}),
            submitted_by=str(spec.get("submitted_by") or "studio-chat"),
            note=str(spec.get("note") or ""),
        )
        validation = service.validate_action(action)
        validation_payload = {
            "valid": validation.valid,
            "approval_required": validation.approval_required,
            "gate_blocked": validation.gate_blocked,
            "errors": list(validation.errors),
            "warnings": list(validation.warnings),
        }
    except Exception as exc:
        validation_payload = {
            "valid": False,
            "approval_required": True,
            "gate_blocked": True,
            "errors": [f"studio_service_validation_failed:{exc}"],
            "warnings": [],
        }
    return {
        "target_path": target_path,
        "target_path_present": True,
        "target_path_under_vault": under_vault,
        "target_file_exists": target_exists,
        "target_file_written": False,
        "target_collision": target_exists,
        "resolved_path_preview": _rel(vault, resolved),
        "high_authority_target_policy": high_authority_policy,
        "validation": validation_payload,
    }


def _high_authority_target_policy(target_path: str | None) -> dict[str, Any]:
    """Fail closed for Chat proposal targets that imply canonical/source-pack/graph promotion."""

    normalized = str(target_path or "").replace("\\", "/").lstrip("/")
    matched_root = ""
    target_class = ""
    for root, class_name in _CANONICAL_OR_HIGH_AUTHORITY_TARGET_ROOTS:
        if normalized == root.rstrip("/") or normalized.startswith(root):
            matched_root = root
            target_class = class_name
            break
    blocked = bool(matched_root)
    return {
        "checked": True,
        "blocked": blocked,
        "matched_root": matched_root or None,
        "target_authority_class": target_class or "ordinary_studio_service_target",
        "blocker": "canonical_or_high_authority_target_blocked" if blocked else None,
        "reason": (
            "Chat approval-consumption executor may not perform canonical knowledge, "
            "source-pack promotion, or graph promotion target writes; those route to "
            "Gate-backed lower-phase promotion contracts."
            if blocked
            else "target root is not classified as canonical/source-pack/graph promotion authority"
        ),
    }


def _approval_summary(vault: Path, path: Path | None, payload: dict[str, Any] | None) -> dict[str, Any]:
    spec = _action_spec(payload)
    metadata = _metadata(payload)
    content = str(spec.get("content") or "")
    return {
        "approval_id": str((payload or {}).get("approval_id") or (path.stem if path else "")),
        "status": str((payload or {}).get("status") or "unknown"),
        "path": _rel(vault, path) if path else "",
        "action_type": spec.get("action_type"),
        "target_path": spec.get("target_path"),
        "submitted_by": spec.get("submitted_by"),
        "reviewed_by": (payload or {}).get("reviewed_by"),
        "submitted_at": (payload or {}).get("submitted_at"),
        "updated_at": (payload or {}).get("updated_at"),
        "content_sha256": _sha256_text(content),
        "content_included": False,
        "metadata": {
            "pass": metadata.get("pass"),
            "phase11_intent": metadata.get("phase11_intent"),
            "source_surface": metadata.get("source_surface"),
            "source_contract": metadata.get("source_contract"),
            "phase11_chat_queue_write_proof": metadata.get("phase11_chat_queue_write_proof") is True,
            "phase11_chat_queue_write_execution_blocked": metadata.get(
                "phase11_chat_queue_write_execution_blocked"
            )
            is True,
            "phase11_chat_action_digest": metadata.get("phase11_chat_action_digest"),
            "source_message_sha256": metadata.get("source_message_sha256"),
        },
    }


def _policy_gate_report(router: dict[str, Any], *, surface: str) -> dict[str, Any]:
    input_posture = router.get("input_posture") or {}
    action_spec = router.get("action_spec") or {}
    ambiguity = action_spec.get("ambiguity") or {}
    denied_actions = list(input_posture.get("requested_denied_actions") or [])
    dependencies = list(router.get("backend_dependencies") or [])
    by_dependency_key = {str(item.get("dependency_key") or ""): item for item in dependencies}
    missing_by_action: dict[str, str] = {}
    blocked_action_reasons: list[dict[str, Any]] = []
    for action in denied_actions:
        dependency = by_dependency_key.get(_DENIED_ACTION_TO_DEPENDENCY_KEY.get(action, ""), {})
        reason = str(dependency.get("blocked_action_reason") or "missing_or_insufficient_lower_phase_authority")
        missing = str(dependency.get("missing_contract") or "missing backend contract")
        missing_by_action[action] = f"{missing}: {reason}"
        blocked_action_reasons.append(
            {
                "action_class": action,
                "denied": True,
                "missing_or_insufficient_authority": missing,
                "blocked_action_reason": reason,
            }
        )
    if ambiguity.get("requires_operator_clarification"):
        blocked_action_reasons.append(
            {
                "action_class": "ambiguous_command",
                "denied": True,
                "missing_or_insufficient_authority": "operator clarification required before approval consumption routing",
                "blocked_action_reason": "ambiguous Phase 11 Chat approval command cannot approve, reject, consume, execute, write, or dispatch",
            }
        )
    fail_closed = bool(denied_actions) or bool(ambiguity.get("requires_operator_clarification"))
    return {
        "surface": surface,
        "deny_default_runtime_policy_applied": True,
        "policy_docs_checked": POLICY_DOCS_CHECKED,
        "phase10_11_surface_only": True,
        "not_canonical_truth_engine": True,
        "fail_closed": fail_closed,
        "side_effects_performed": False,
        "execution_allowed": False,
        "denied_action_classes": denied_actions,
        "ambiguous_command": ambiguity,
        "backend_dependency_reports": dependencies,
        "missing_or_insufficient_authority_by_action": missing_by_action,
        "blocked_action_reasons": blocked_action_reasons,
    }


def build_phase11_chat_approval_consumption_readiness(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    message: str | None = None,
    explicit_intent: str | None = None,
) -> dict[str, Any]:
    """Build the read-only readiness contract for future Chat approval consumption."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    router = build_phase11_chat_router_contract(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent or "approval-action",
    )
    input_posture = router.get("input_posture") or {}
    action_spec = router.get("action_spec") or {}
    ambiguity = action_spec.get("ambiguity") or {}
    policy_gate = _policy_gate_report(router, surface=SURFACE_ID)
    selection = _select_approval(vault, approval_id)
    selected = selection.get("selected")
    payload = (selected or {}).get("payload") if isinstance(selected, dict) else None
    path = (selected or {}).get("path") if isinstance(selected, dict) else None
    path = path if isinstance(path, Path) else None
    spec = _action_spec(payload)
    metadata = _metadata(payload)
    approval_id_value = str((payload or {}).get("approval_id") or ((path.stem if path else "")))
    status = str((payload or {}).get("status") or "unknown")
    marker_path = vault / MARKER_DIR / f"{approval_id_value or 'unknown'}.json"
    target_state = _target_path_state(vault, spec) if payload else _target_path_state(vault, {})
    artifact_sha = _artifact_sha256(path) if path else None
    message_digest = _sha256_text(normalized_message)
    expected_message_digest = str(metadata.get("source_message_sha256") or "")
    message_digest_matches = bool(
        not normalized_message or (expected_message_digest and expected_message_digest == message_digest)
    )

    blockers: list[str] = []
    warnings: list[str] = []
    selection_error = selection.get("error")
    if selection_error:
        blockers.append(str(selection_error))
    if input_posture.get("prompt_injection_suspected"):
        blockers.append("prompt_injection_indicator_present")
    if policy_gate["denied_action_classes"]:
        blockers.append("denied_side_effect_prompt_present")
        blockers.append("policy_gate_denied_side_effect_request")
    if normalized_message and ambiguity.get("requires_operator_clarification"):
        blockers.append("ambiguous_command_requires_operator_clarification")
        blockers.append("policy_gate_ambiguous_command")
    if payload and not _is_chat_originated(payload):
        blockers.append("approval_not_chat_originated")
    if payload and status not in {"pending", "approved"}:
        blockers.append("approval_status_not_pending_or_approved")
    if payload and status != "approved":
        blockers.append("operator_decision_not_approved")
    if payload and not metadata.get("phase11_chat_action_digest"):
        blockers.append("phase11_chat_action_digest_missing")
    if payload and normalized_message and not message_digest_matches:
        blockers.append("source_message_digest_mismatch")
    if payload and target_state.get("target_collision"):
        blockers.append("future_target_path_collision")
    high_authority_policy = target_state.get("high_authority_target_policy") or {}
    if payload and high_authority_policy.get("blocked"):
        blockers.append("canonical_or_high_authority_target_blocked")
    validation = target_state.get("validation") or {}
    if payload and validation.get("gate_blocked"):
        blockers.append("studio_service_validation_gate_blocked")
    if marker_path.exists():
        blockers.append("future_exact_once_marker_already_present")

    consumption_material = {
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "approval_id": approval_id_value,
        "approval_status": status,
        "approval_artifact_sha256": artifact_sha,
        "phase11_chat_action_digest": metadata.get("phase11_chat_action_digest"),
        "target_path": spec.get("target_path"),
        "source_message_sha256": metadata.get("source_message_sha256"),
        "marker_path_preview": _rel(vault, marker_path),
        "router_model_version": router.get("model_version"),
    }
    consumption_digest = _sha256_text(_canonical_json(consumption_material))
    hard_blockers = {
        "approval_artifact_not_found",
        "approval_artifact_json_malformed",
        "approval_artifact_json_not_object",
        "no_chat_originated_approval_artifacts_found",
        "prompt_injection_indicator_present",
        "approval_not_chat_originated",
        "approval_status_not_pending_or_approved",
        "phase11_chat_action_digest_missing",
        "source_message_digest_mismatch",
        "future_target_path_collision",
        "canonical_or_high_authority_target_blocked",
        "studio_service_validation_gate_blocked",
        "future_exact_once_marker_already_present",
        "denied_side_effect_prompt_present",
        "policy_gate_denied_side_effect_request",
        "ambiguous_command_requires_operator_clarification",
        "policy_gate_ambiguous_command",
    }
    ok = not any(
        item in hard_blockers or item.startswith("approval_artifact_json_malformed")
        for item in blockers
    )

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": True,
        "summary": {
            "approval_id_requested": selection.get("requested_approval_id") or "",
            "selected_approval_id": approval_id_value or None,
            "approval_artifact_known": bool(payload),
            "chat_originated": bool(payload and _is_chat_originated(payload)),
            "approval_status": status if payload else "missing",
            "operator_approved": status == "approved",
            "consumption_preview_ready": bool(payload) and ok,
            "consumption_preconditions_met": False,
            "approval_status_mutated": False,
            "approval_execution_called": False,
            "exact_once_marker_written": False,
            "target_write_performed": False,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "browser_dispatch_performed": False,
            "agent_bus_task_written": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(list(dict.fromkeys(blockers))),
        },
        "source_selection": {
            "requested_approval_id": selection.get("requested_approval_id") or "",
            "selected_latest_chat_approval": bool(not selection.get("requested_approval_id") and payload),
            "available_chat_approval_count": len(selection.get("available_chat_approval_ids") or []),
            "available_chat_approval_ids": selection.get("available_chat_approval_ids") or [],
            "selection_error": selection_error,
        },
        "selected_approval": _approval_summary(vault, path, payload) if payload else None,
        "router_contract": router,
        "policy_gate_report": policy_gate,
        "preflight_checks": {
            "approval_artifact_exists": bool(path and path.exists()),
            "approval_artifact_json_valid": bool(payload),
            "approval_id_matches_request": bool(
                not selection.get("requested_approval_id")
                or str(selection.get("requested_approval_id")) == approval_id_value
            ),
            "chat_originated_metadata_present": bool(payload and _is_chat_originated(payload)),
            "operator_decision_approved": status == "approved",
            "approval_status_pending_or_approved": status in {"pending", "approved"},
            "phase11_chat_action_digest_present": bool(metadata.get("phase11_chat_action_digest")),
            "source_message_digest_present": bool(metadata.get("source_message_sha256")),
            "source_message_digest_matches_when_supplied": message_digest_matches,
            "target_path_under_vault": bool(target_state.get("target_path_under_vault")),
            "target_path_collision_absent": not bool(target_state.get("target_collision")),
            "studio_service_validation_gate_clear": not bool(validation.get("gate_blocked")),
            "future_exact_once_marker_absent": not marker_path.exists(),
            "approval_record_update_allowed_now": False,
            "studio_service_execute_approved_called": False,
            "target_write_allowed_now": False,
        },
        "target_write_preflight": target_state,
        "digest_proof": {
            "approval_artifact_sha256": artifact_sha,
            "phase11_chat_action_digest": metadata.get("phase11_chat_action_digest"),
            "source_message_sha256": metadata.get("source_message_sha256"),
            "supplied_message_sha256": message_digest if normalized_message else None,
            "supplied_message_digest_matched": message_digest_matches,
            "consumption_digest": consumption_digest,
            "digest_material": consumption_material,
            "digest_required_for_future_consumption": True,
        },
        "exact_once_marker_preview": {
            "marker_path_preview": _rel(vault, marker_path),
            "marker_exists_now": marker_path.exists(),
            "marker_reserved_now": False,
            "marker_written_now": False,
            "duplicate_consumption_blocks_before_writes": True,
        },
        "future_consumption_packet_preview": {
            "visible": True,
            "consumption_packet_id_preview": f"chat-approval-consumption-{consumption_digest[:20]}",
            "approval_class": APPROVAL_CLASS,
            "approval_id": approval_id_value or None,
            "approval_status_required": "approved",
            "approval_status_now": status if payload else "missing",
            "future_status_transition_preview": "approved -> executing -> executed",
            "approval_status_mutated": False,
            "approval_record_update_allowed_now": False,
            "approval_execution_called": False,
            "exact_once_marker_written": False,
            "target_path": spec.get("target_path"),
            "target_write_allowed_now": False,
            "target_file_written": False,
            "execution_audit_path_preview": f"07_LOGS/Agent-Activity/chat-approval-consumption-{consumption_digest[:20]}.md",
            "readiness_evidence_path_preview": f"07_LOGS/Studio-Graph-Views/chat-approval-consumption-{consumption_digest[:20]}.json",
        },
        "authority": {
            "read_only": True,
            "approval_gated": True,
            "approval_consumption_preview_allowed": True,
            "approval_status_mutation_allowed": False,
            "approval_grant_or_reject_allowed": False,
            "approval_execution_allowed": False,
            "target_vault_write_allowed": False,
            "exact_once_marker_write_allowed": False,
            "conversation_persistence_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "agent_bus_task_write_allowed": False,
            "gate_mutation_allowed": False,
            "git_mutation_allowed": False,
            "workflow_execution_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "approval_grant_or_reject",
            "approval_status_mutation",
            "studio_service_execute_approved",
            "exact_once_marker_write",
            "target_vault_file_write",
            "conversation_log_write",
            "provider_api_call",
            "runtime_dispatch",
            "browser_control",
            "agent_bus_task_write",
            "gate_mutation",
            "git_mutation",
            "workflow_execution",
            "host_mutation",
            "canonical_writeback",
        ],
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "warnings": warnings,
    }


def format_phase11_chat_approval_consumption_readiness(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    marker = payload.get("exact_once_marker_preview") or {}
    target = payload.get("target_write_preflight") or {}
    return "\n".join(
        [
            "Phase 11 Chat Approval Consumption Readiness Contract",
            f"  status: {payload.get('status')}",
            f"  approval_id: {summary.get('selected_approval_id') or 'none'}",
            f"  approval_status: {summary.get('approval_status')}",
            f"  consumption_preview_ready: {summary.get('consumption_preview_ready')}",
            f"  consumption_preconditions_met: {summary.get('consumption_preconditions_met')}",
            f"  consumption_digest: {digest.get('consumption_digest') or 'none'}",
            f"  marker_path_preview: {marker.get('marker_path_preview') or 'none'}",
            f"  target_path: {target.get('target_path') or 'none'}",
            f"  target_file_written: {summary.get('target_write_performed')}",
            f"  approval_execution_called: {summary.get('approval_execution_called')}",
            f"  next: {summary.get('next_recommended_pass')}",
            "  Boundary: read-only consumption readiness only; no approval status mutation, no execute_approved call, no marker reservation, no target vault write, no provider/runtime/browser dispatch, no Agent Bus write, and no canonical mutation.",
        ]
    )
