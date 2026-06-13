"""Runtime-consumption readiness for personal context import.

This surface builds a bounded reference packet from the Personal Operator
Context read model so runtimes can be handed explicit context references in a
future governed task. It does not include raw source text, call providers,
create Agent Bus tasks, mutate runtime memory, apply Personal Map candidates,
or write canonical vault state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.personal_operator_context_index import (
    ROOT_HUB_PATH,
    build_personal_operator_context_index,
)


MODEL_VERSION = "studio.personal_context_import_runtime_consumption_readiness.v1"
SURFACE_ID = "studio_personal_context_import_runtime_consumption_readiness"
PASS_ID = "personal-context-import-runtime-consumption-readiness"
STATUS = "COMPLETE / READ-ONLY / RUNTIME CONSUMPTION READINESS / LIVE DISPATCH BLOCKED"
DEGRADED_STATUS = "READY WITH WARNINGS / READ-ONLY / RUNTIME CONSUMPTION READINESS"
BLOCKED_STATUS = "BLOCKED / PERSONAL CONTEXT REFERENCES UNAVAILABLE / LIVE DISPATCH BLOCKED"
NEXT_RECOMMENDED_PASS = "personal-context-import-personal-map-apply-readiness"
DEFAULT_MAX_REFS = 96
MAX_REFS = 240

WORKSPACE_MODE_PATH = "00_HOME/.workspace-mode.yaml"
RAW_INTAKE_DIR = "03_INPUTS/Personal-Context-Intake"
PERSONAL_MAP_CANDIDATE_DIR = "07_LOGS/Pulse-Decks/memory-candidates/personal-map"
PREVIEW_ARTIFACT_DIR = "runtime/studio/context-import/previews"
EXECUTION_PROOF_DIR = "runtime/studio/context-import/execution-proofs"
FEATURE_CONTRACT_PATH = "06_AGENTS/Personal-Context-Import-Feature.md"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_max_refs(max_refs: int | None) -> int:
    try:
        parsed = int(max_refs or DEFAULT_MAX_REFS)
    except (TypeError, ValueError):
        parsed = DEFAULT_MAX_REFS
    return max(1, min(parsed, MAX_REFS))


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _path_snapshot(vault: Path, relative_dir: str, *, limit: int = 40) -> dict[str, Any]:
    root = vault / relative_dir
    if not root.exists():
        return {
            "path": relative_dir,
            "exists": False,
            "file_count": 0,
            "sample_paths": [],
            "content_included": False,
        }
    files = sorted(_rel(vault, path) for path in root.rglob("*") if path.is_file())
    return {
        "path": relative_dir,
        "exists": True,
        "file_count": len(files),
        "sample_paths": files[:limit],
        "content_included": False,
    }


def _artifact_snapshot(vault: Path) -> dict[str, Any]:
    return {
        "raw_intake": _path_snapshot(vault, RAW_INTAKE_DIR),
        "personal_map_candidates": _path_snapshot(vault, PERSONAL_MAP_CANDIDATE_DIR),
        "preview_artifacts": _path_snapshot(vault, PREVIEW_ARTIFACT_DIR),
        "execution_proofs": _path_snapshot(vault, EXECUTION_PROOF_DIR),
    }


def _workspace_mode(vault: Path) -> dict[str, Any]:
    path = vault / WORKSPACE_MODE_PATH
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    has_personal_os = "personal_os" in text
    return {
        "path": WORKSPACE_MODE_PATH,
        "exists": path.exists(),
        "declares_personal_os": has_personal_os,
        "content_included": False,
        "read_model": "workspace-mode-file-presence-only",
    }


def _operator_context(vault: Path) -> dict[str, Any]:
    try:
        return build_personal_operator_context_index(vault)
    except Exception as exc:
        return {
            "ok": False,
            "surface": "studio_personal_operator_context_index",
            "status": "unavailable",
            "summary": {},
            "groups": [],
            "link_blockers": [{"id": "personal_operator_context_unavailable", "error": str(exc)}],
            "link_warnings": [],
            "authority": {"read_only": True, "canonical_mutation_allowed": False},
        }


def _reference_groups(operator_context: dict[str, Any]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for group in operator_context.get("groups") or []:
        items = list(group.get("items") or [])
        existing = [item for item in items if item.get("exists")]
        groups.append(
            {
                "group_id": group.get("id"),
                "label": group.get("label"),
                "purpose": group.get("purpose"),
                "tracked_ref_count": len(items),
                "available_ref_count": len(existing),
                "missing_ref_count": len(items) - len(existing),
            }
        )
    return groups


def _requires_review(item: dict[str, Any]) -> bool:
    status = str(item.get("status") or "").upper()
    boundary = str(item.get("boundary") or "").lower()
    return (
        "REVIEW" in status
        or "CANDIDATE" in status
        or "RAW" in status
        or "PROTECTED" in status
        or "review" in boundary
        or "explicit" in boundary
    )


def _context_refs(operator_context: dict[str, Any], *, max_refs: int) -> tuple[list[dict[str, Any]], int]:
    refs: list[dict[str, Any]] = []
    total_available = 0
    for group in operator_context.get("groups") or []:
        group_id = str(group.get("id") or "")
        group_label = str(group.get("label") or group_id)
        for item in group.get("items") or []:
            if not item.get("exists"):
                continue
            total_available += 1
            if len(refs) >= max_refs:
                continue
            ref_material = {
                "group_id": group_id,
                "id": item.get("id"),
                "path": item.get("path"),
                "status": item.get("status"),
            }
            refs.append(
                {
                    "ref_id": f"personal-context-ref-{_sha256_text(_canonical_json(ref_material))[:12]}",
                    "group_id": group_id,
                    "group_label": group_label,
                    "item_id": item.get("id"),
                    "label": item.get("label"),
                    "path": item.get("path"),
                    "status": item.get("status"),
                    "boundary": item.get("boundary"),
                    "content_included": False,
                    "raw_source_text_included": False,
                    "allowed_for_runtime_reference": True,
                    "requires_human_review_for_canonical_use": _requires_review(item),
                    "runtime_may_mutate_source": False,
                }
            )
    return refs, total_available


def _authority() -> dict[str, bool]:
    return {
        "read_only": True,
        "reads_personal_operator_context": True,
        "reads_workspace_mode_profile": True,
        "reads_artifact_paths_only": True,
        "context_reference_packet_preview_allowed": True,
        "raw_context_body_included": False,
        "raw_full_memory_injection_allowed": False,
        "provider_context_delivery_allowed": False,
        "model_calls_allowed": False,
        "provider_calls_allowed": False,
        "approval_queue_write_allowed": False,
        "approval_consumption_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "runtime_memory_mutation_allowed": False,
        "personal_map_apply_allowed": False,
        "canonical_node_write_allowed": False,
        "canonical_index_write_allowed": False,
        "project_truth_mutation_allowed": False,
        "knowledge_promotion_allowed": False,
        "credential_values_visible": False,
        "secret_values_read": False,
        "secret_values_stored": False,
        "canonical_mutation_allowed": False,
    }


def _consumer_contracts() -> list[dict[str, Any]]:
    return [
        {
            "consumer": "Codex",
            "surface_class": "repo-aware development runtime",
            "allowed_use": "receive explicit context references in a future bounded task packet",
            "blocked_use": "no governed memory ownership, no ambient vault rewrite, no Agent Bus claim created here",
        },
        {
            "consumer": "Hermes",
            "surface_class": "workflow/operator runtime",
            "allowed_use": "future manifest-declared reads of approved reference paths only",
            "blocked_use": "no ambient personal vault access and no undeclared memory apply",
        },
        {
            "consumer": "OpenClaw",
            "surface_class": "governed runtime lane",
            "allowed_use": "future WML-scoped reference routing after operator approval",
            "blocked_use": "no direct canonical import writer and no schedule/runtime mutation",
        },
        {
            "consumer": "Phase 11 Chat / Studio",
            "surface_class": "operator UI",
            "allowed_use": "display reference packet posture and readiness",
            "blocked_use": "no provider delivery until secret reference and a separate live-use approval exist",
        },
    ]


def build_personal_context_import_runtime_consumption_readiness(
    vault_root: str | Path,
    *,
    max_refs: int = DEFAULT_MAX_REFS,
) -> dict[str, Any]:
    """Build a runtime-facing context-reference packet preview."""

    vault = Path(vault_root).resolve()
    safe_max_refs = _safe_max_refs(max_refs)
    before_artifacts = _artifact_snapshot(vault)
    operator_context = _operator_context(vault)
    workspace_mode = _workspace_mode(vault)
    refs, total_available_refs = _context_refs(operator_context, max_refs=safe_max_refs)
    reference_groups = _reference_groups(operator_context)
    after_artifacts = _artifact_snapshot(vault)

    summary = dict(operator_context.get("summary") or {})
    link_blocker_count = int(summary.get("link_blocker_count") or 0)
    link_warning_count = int(summary.get("link_warning_count") or 0)
    references_truncated = total_available_refs > len(refs)
    reference_packet_ready = (
        bool(refs)
        and bool(operator_context.get("ok"))
        and link_blocker_count == 0
        and bool(workspace_mode.get("declares_personal_os"))
    )
    blocked_reasons: list[str] = []
    if not refs:
        blocked_reasons.append("no_personal_context_references_available")
    if not operator_context.get("ok"):
        blocked_reasons.append("personal_operator_context_read_model_unavailable")
    if link_blocker_count:
        blocked_reasons.append("personal_operator_context_link_blockers_present")
    if not workspace_mode.get("declares_personal_os"):
        blocked_reasons.append("workspace_mode_personal_os_not_declared")
    if references_truncated:
        blocked_reasons.append("context_reference_packet_truncated_to_budget")

    status = STATUS
    if not reference_packet_ready:
        status = BLOCKED_STATUS
    elif link_warning_count or references_truncated:
        status = DEGRADED_STATUS

    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "workspace_mode": "personal_os",
        "operator_context_status": operator_context.get("status"),
        "workspace_mode_declares_personal_os": workspace_mode.get("declares_personal_os"),
        "context_ref_ids": [item.get("ref_id") for item in refs],
        "context_ref_paths": [item.get("path") for item in refs],
        "total_available_refs": total_available_refs,
        "artifact_paths_before": before_artifacts,
        "artifact_paths_after": after_artifacts,
    }
    packet_digest = _sha256_text(_canonical_json(digest_material))

    return {
        "ok": reference_packet_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "runtime_consumption_readiness_ready": reference_packet_ready,
            "runtime_reference_packet_ready": reference_packet_ready,
            "context_ref_count": len(refs),
            "total_available_context_ref_count": total_available_refs,
            "context_refs_truncated": references_truncated,
            "reference_group_count": len(reference_groups),
            "personal_operator_context_status": operator_context.get("status"),
            "personal_operator_context_link_blocker_count": link_blocker_count,
            "personal_operator_context_link_warning_count": link_warning_count,
            "workspace_mode_personal_os_declared": bool(workspace_mode.get("declares_personal_os")),
            "raw_context_body_included": False,
            "raw_full_memory_injection_allowed": False,
            "source_text_returned": False,
            "provider_call_performed": False,
            "model_call_performed": False,
            "agent_bus_task_written": False,
            "runtime_dispatch_performed": False,
            "runtime_memory_mutation_performed": False,
            "personal_map_apply_performed": False,
            "canonical_mutation_performed": False,
            "artifact_snapshot_unchanged": before_artifacts == after_artifacts,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "workspace_mode": workspace_mode,
        "runtime_reference_packet_preview": {
            "schema_version": "personal_context_runtime_reference_packet.v1",
            "packet_id": f"personal-context-runtime-{packet_digest[:16]}",
            "packet_digest": packet_digest,
            "context_scope": "personal_os",
            "root_hub_path": ROOT_HUB_PATH,
            "feature_contract_path": FEATURE_CONTRACT_PATH,
            "ready_for_runtime_reference_preview": reference_packet_ready,
            "ready_for_agent_bus_task_creation": False,
            "agent_bus_task_created": False,
            "provider_execution_allowed": False,
            "runtime_dispatch_allowed": False,
            "raw_context_body_included": False,
            "raw_full_memory_injection_allowed": False,
            "context_refs_only": True,
            "context_ref_count": len(refs),
            "context_refs": refs,
            "boundary_notice": (
                "This packet supplies file/path references and trust posture only. "
                "Future runtimes must read only explicitly provided refs under WML and permission policy."
            ),
        },
        "reference_groups": reference_groups,
        "artifact_reference_snapshot": after_artifacts,
        "consumer_contracts": _consumer_contracts(),
        "runtime_consumption_plan": [
            "Build a reference packet from Personal Operator Context and WML personal_os.",
            "Attach only scoped refs to a future approved runtime task packet.",
            "Require the runtime to cite refs it used in the result artifact.",
            "Keep raw source text, canonical writes, Personal Map apply, and runtime memory mutation behind separate approvals.",
        ],
        "operator_context_read_model": {
            "surface": operator_context.get("surface"),
            "status": operator_context.get("status"),
            "summary": summary,
            "content_included": False,
        },
        "readiness": {
            "personal_context_import_runtime_consumption_readiness_ready": reference_packet_ready,
            "personal_context_import_runtime_reference_packet_ready": reference_packet_ready,
            "personal_context_import_runtime_reference_packet_refs_only": True,
            "personal_context_import_runtime_reference_packet_source_text_returned": False,
            "personal_context_import_raw_full_memory_injection_blocked": True,
            "personal_context_import_personal_os_wml_declared": bool(workspace_mode.get("declares_personal_os")),
            "personal_context_import_provider_calls_blocked": True,
            "personal_context_import_agent_bus_dispatch_blocked": True,
            "personal_context_import_runtime_memory_mutation_blocked": True,
            "personal_context_import_personal_map_apply_blocked": True,
            "personal_context_import_canonical_writes_blocked": True,
            "runtime_consumption_live_verified": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "authority": _authority(),
        "digest_proof": {
            "runtime_reference_packet_digest": packet_digest,
            "digest_material": digest_material,
        },
        "denied_by_this_surface": [
            "raw_full_memory_injection",
            "raw_source_text_return",
            "provider_context_delivery",
            "provider_api_call",
            "model_response_generation",
            "approval_queue_write",
            "approval_consumption",
            "agent_bus_task_write",
            "runtime_dispatch",
            "runtime_memory_mutation",
            "personal_map_apply",
            "canonical_markdown_node_write",
            "dashboard_index_write",
            "personal_operator_index_write",
            "projects_hub_write",
            "knowledge_index_write",
            "credential_value_display",
            "canonical_writeback",
        ],
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "warnings": [],
    }


def format_personal_context_import_runtime_consumption_readiness(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    packet = payload.get("runtime_reference_packet_preview") or {}
    workspace = payload.get("workspace_mode") or {}
    lines = [
        "Personal Context Import Runtime Consumption Readiness",
        f"Status: {payload.get('status')}",
        f"Reference packet ready: {summary.get('runtime_reference_packet_ready')}",
        f"Context refs: {summary.get('context_ref_count')} / {summary.get('total_available_context_ref_count')}",
        f"Workspace mode personal_os declared: {workspace.get('declares_personal_os')}",
        f"Raw full-memory injection allowed: {packet.get('raw_full_memory_injection_allowed')}",
        f"Provider execution allowed: {packet.get('provider_execution_allowed')}",
        f"Runtime dispatch allowed: {packet.get('runtime_dispatch_allowed')}",
        f"Agent Bus task created: {packet.get('agent_bus_task_created')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers[:10])
    return "\n".join(lines)
