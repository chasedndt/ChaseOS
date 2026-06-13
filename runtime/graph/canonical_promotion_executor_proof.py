"""Proof packet for governed graph/source-pack/canonical promotion execution.

This module intentionally models the lower-phase executor contract without
performing canonical graph mutation, source-pack promotion, or knowledge
promotion. The only optional write is an Agent-Activity proof artifact under
``07_LOGS/Agent-Activity``.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaseos_gate import check_write_permission

SURFACE_ID = "graph_source_pack_canonical_promotion_executor_proof"
MODEL_VERSION = "2026-05-11.v1"
DEFAULT_CANDIDATE_ID = "candidate.graph-source-pack-canonical-proof.v1"
DEFAULT_APPROVAL_ID = "gate-approval.synthetic-approved-candidate-proof"
PROTECTED_DENIAL_TARGET = "06_AGENTS/Permission-Matrix.md"
CANONICAL_TARGET_PREVIEW = "02_KNOWLEDGE/Graph-Source-Pack-Promotion-Proof.md"
AUDIT_ROOT = Path("07_LOGS/Agent-Activity")


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256_payload(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _source_pack_state(vault_root: Path) -> dict[str, Any]:
    latest = vault_root / "runtime" / "acquisition" / "packs" / "strikezone-latest.json"
    state: dict[str, Any] = {
        "source_pack_visibility_checked": True,
        "latest_pointer_path": _rel(latest, vault_root),
        "latest_pointer_exists": latest.exists(),
        "promotion_state_mutation_requested": True,
        "promotion_state_mutation_allowed_now": False,
        "promotion_state_written": False,
        "connector_collection_allowed": False,
    }
    payload = _load_json(latest) if latest.exists() else None
    if payload:
        pack_path = payload.get("normalized_source_pack") or payload.get("normalized_pack_path") or payload.get("pack_path")
        state.update(
            {
                "latest_pointer_parse_ok": True,
                "latest_pointer_profile": payload.get("profile") or payload.get("pilot") or "unknown",
                "latest_pointer_pack_ref": pack_path,
                "reviewed_pointer_observed": bool(payload.get("reviewed") or payload.get("reviewed_preview") or payload.get("review_status") == "reviewed"),
            }
        )
    else:
        state.update(
            {
                "latest_pointer_parse_ok": False,
                "latest_pointer_profile": None,
                "latest_pointer_pack_ref": None,
                "reviewed_pointer_observed": False,
            }
        )
    return state


def build_canonical_promotion_executor_proof(
    vault_root: str | Path,
    *,
    candidate_id: str = DEFAULT_CANDIDATE_ID,
    gate_approval_id: str | None = DEFAULT_APPROVAL_ID,
    decision: str = "approved",
    write_audit: bool = False,
    audit_slug: str | None = None,
) -> dict[str, Any]:
    """Build a governed promotion executor proof packet.

    ``decision='approved'`` plus a ``gate_approval_id`` models the approved
    candidate packet required by the future executor. Even in that approved
    shape this proof remains non-mutating: canonical graph, source-pack
    promotion state, and knowledge targets are previewed only.
    """

    root = Path(vault_root).resolve()
    approved = bool(gate_approval_id) and decision == "approved"
    protected_allowed, protected_reason = check_write_permission("hermes", PROTECTED_DENIAL_TARGET)

    candidate_packet = {
        "candidate_id": candidate_id,
        "packet_type": "graph-source-pack-canonical-promotion-candidate",
        "approval_state": decision,
        "gate_approval_id": gate_approval_id,
        "approved_candidate_packet": approved,
        "requested_mutations": [
            "canonical_graph_mutation",
            "source_pack_promotion_state_update",
            "knowledge_promotion",
        ],
        "target_previews": {
            "canonical_knowledge_path": CANONICAL_TARGET_PREVIEW,
            "protected_denial_probe_path": PROTECTED_DENIAL_TARGET,
            "source_pack_latest_pointer": "runtime/acquisition/packs/strikezone-latest.json",
        },
        "operator_confirmation_required_for_future_apply": True,
    }
    candidate_packet["candidate_digest_sha256"] = _sha256_payload(candidate_packet)

    derived_vs_canonical = {
        "derived_graph_read_model_available": True,
        "derived_graph_sources": [
            "runtime/graph/builder.py",
            "runtime/graph/index.py",
            "runtime/studio/graph_view_contract.py",
            "runtime/studio/node_inspector_contract.py",
        ],
        "derived_graph_may_be_displayed_by_studio_chat": True,
        "canonical_graph_mutation_requested": True,
        "canonical_graph_mutation_allowed_now": False,
        "canonical_graph_mutation_performed": False,
        "canonical_node_id_writer_enabled": False,
        "knowledge_promotion_allowed_now": False,
        "knowledge_promotion_performed": False,
    }

    source_pack_state = _source_pack_state(root)
    protected_file_denial = {
        "target_path": PROTECTED_DENIAL_TARGET,
        "gate_checked_adapter": "hermes",
        "write_allowed": protected_allowed,
        "denial_proven": protected_allowed is False,
        "reason": protected_reason,
        "protected_file_written": False,
    }

    execution_gate = {
        "candidate_packet_approved": approved,
        "gate_approval_required": True,
        "gate_approval_id": gate_approval_id,
        "future_executor_backend_owner": "Phase 9 graph/acquisition/Gate owner",
        "executor_enabled_now": False,
        "mutation_execution_allowed_now": False,
        "would_execute_if_future_executor_enabled": approved and protected_allowed is False,
        "blocked_reasons": [] if approved else ["approved-candidate-packet-missing"],
    }

    rollback_rejection_behavior = {
        "rejection_path_modeled": True,
        "rollback_path_modeled": True,
        "rejected_candidate_effect": "no canonical graph/source-pack/knowledge writes; emit rejection audit only",
        "rollback_strategy": "future executor must write canonical targets atomically, verify post-state, and retain pre-image/manifest for rollback before success audit",
        "rollback_executed_now": False,
        "rejection_executed_now": decision == "rejected",
        "canonical_state_restored_or_unchanged": True,
    }

    authority = {
        "read_only_contract": not write_audit,
        "agent_activity_audit_writeback_allowed": True,
        "agent_activity_audit_written": False,
        "canonical_graph_write_allowed": False,
        "source_pack_promotion_write_allowed": False,
        "knowledge_promotion_write_allowed": False,
        "protected_file_write_allowed": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "agent_bus_write_allowed": False,
        "studio_chat_direct_apply_allowed": False,
    }

    model: dict[str, Any] = {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "title": "Graph / Source-Pack / Canonical Promotion Backend Executor Proof",
        "status": "approved-candidate-proof-non-mutating" if approved else "blocked-missing-approved-candidate",
        "vault_root": str(root),
        "candidate_packet": candidate_packet,
        "derived_vs_canonical_graph": derived_vs_canonical,
        "source_pack_promotion_state": source_pack_state,
        "protected_file_denial_proof": protected_file_denial,
        "execution_gate": execution_gate,
        "provenance_audit": {
            "provenance_chain": [
                "derived graph read model",
                "normalized source-pack pointer inspection",
                "candidate packet digest",
                "Gate protected-file denial check",
                "Agent-Activity audit writeback preview",
            ],
            "audit_write_requested": write_audit,
            "audit_written": False,
            "audit_markdown_path": None,
            "audit_json_path": None,
        },
        "rollback_rejection_behavior": rollback_rejection_behavior,
        "authority": authority,
        "affected_surfaces": [
            "graph view",
            "node inspector",
            "candidate apply surfaces",
            "acquisition cockpit",
            "source-pack visibility",
            "Chat proposal cards",
        ],
        "next_route": "future Phase 9 graph/acquisition/Gate executor implementation may consume this contract; Studio/Chat remain preview/readiness surfaces only",
    }

    if write_audit:
        audit_paths = write_agent_activity_audit(root, model, audit_slug=audit_slug)
        model["provenance_audit"].update(
            {
                "audit_written": True,
                "audit_markdown_path": audit_paths["markdown_path"],
                "audit_json_path": audit_paths["json_path"],
            }
        )
        model["authority"]["agent_activity_audit_written"] = True
        model["authority"]["read_only_contract"] = False

    return model


def write_agent_activity_audit(vault_root: Path, model: dict[str, Any], *, audit_slug: str | None = None) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    slug = audit_slug or f"{now:%Y-%m-%d}-hermes-optimus-graph-source-pack-canonical-promotion-executor-proof"
    safe_slug = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in slug).strip("-")
    audit_dir = vault_root / AUDIT_ROOT
    audit_dir.mkdir(parents=True, exist_ok=True)
    json_path = audit_dir / f"{safe_slug}.json"
    md_path = audit_dir / f"{safe_slug}.md"

    audit_model = dict(model)
    audit_model["provenance_audit"] = dict(model.get("provenance_audit") or {})
    audit_model["provenance_audit"].update(
        {
            "audit_written": True,
            "audit_markdown_path": _rel(md_path, vault_root),
            "audit_json_path": _rel(json_path, vault_root),
            "written_at_utc": now.isoformat(),
        }
    )
    audit_model["authority"] = dict(model.get("authority") or {})
    audit_model["authority"].update({"agent_activity_audit_written": True, "read_only_contract": False})

    json_path.write_text(json.dumps(audit_model, indent=2, default=str) + "\n", encoding="utf-8")
    md_path.write_text(_render_audit_markdown(audit_model), encoding="utf-8")
    return {"json_path": _rel(json_path, vault_root), "markdown_path": _rel(md_path, vault_root)}


def _render_audit_markdown(model: dict[str, Any]) -> str:
    candidate = model.get("candidate_packet") or {}
    protected = model.get("protected_file_denial_proof") or {}
    source_pack = model.get("source_pack_promotion_state") or {}
    audit = model.get("provenance_audit") or {}
    authority = model.get("authority") or {}
    return "\n".join(
        [
            "---",
            "title: Graph / Source-Pack / Canonical Promotion Backend Executor Proof",
            "runtime: hermes-optimus",
            "lane: Optimus",
            "status: backend-executor-proof / non-canonical / audit-writeback-only",
            "related:",
            "  - \"[[Hermes-Runtime-Profile]]\"",
            "  - \"[[HERMES]]\"",
            "  - \"[[Agent-Activity-Index]]\"",
            "---",
            "",
            "# Graph / Source-Pack / Canonical Promotion Backend Executor Proof",
            "",
            "Runtime lane: Hermes/Optimus.",
            "",
            "This proof models the lower-phase backend executor contract for canonical graph mutation, source-pack promotion, and knowledge promotion through Gate. It does not perform canonical mutation; the only write in this run is this Agent-Activity audit artifact and its JSON sidecar.",
            "",
            "## Proof summary",
            "",
            f"- Candidate packet approved: `{candidate.get('approved_candidate_packet')}`",
            f"- Candidate digest: `{candidate.get('candidate_digest_sha256')}`",
            f"- Derived graph display allowed: `{model.get('derived_vs_canonical_graph', {}).get('derived_graph_may_be_displayed_by_studio_chat')}`",
            f"- Canonical graph mutation performed: `{model.get('derived_vs_canonical_graph', {}).get('canonical_graph_mutation_performed')}`",
            f"- Source-pack latest pointer exists: `{source_pack.get('latest_pointer_exists')}`",
            f"- Source-pack promotion state written: `{source_pack.get('promotion_state_written')}`",
            f"- Protected-file denial proven: `{protected.get('denial_proven')}` — {protected.get('reason')}",
            f"- Knowledge promotion performed: `{model.get('derived_vs_canonical_graph', {}).get('knowledge_promotion_performed')}`",
            f"- Rollback/rejection modeled: `{model.get('rollback_rejection_behavior', {}).get('rollback_path_modeled')}` / `{model.get('rollback_rejection_behavior', {}).get('rejection_path_modeled')}`",
            "",
            "## Authority boundary",
            "",
            f"- Agent-Activity audit written: `{authority.get('agent_activity_audit_written')}`",
            f"- Canonical graph write allowed: `{authority.get('canonical_graph_write_allowed')}`",
            f"- Source-pack promotion write allowed: `{authority.get('source_pack_promotion_write_allowed')}`",
            f"- Knowledge promotion write allowed: `{authority.get('knowledge_promotion_write_allowed')}`",
            f"- Protected-file write allowed: `{authority.get('protected_file_write_allowed')}`",
            f"- Studio/Chat direct apply allowed: `{authority.get('studio_chat_direct_apply_allowed')}`",
            "",
            "## ChaseOS OS alignment",
            "",
            "Studio and Chat may consume this proof as readiness/provenance evidence for graph view, node inspector, acquisition cockpit, source-pack visibility, and Chat proposal cards. They still may not mutate canonical graph/source-pack/knowledge state; future mutation must route through a Gate-backed Phase 9 backend executor with exact candidate, approval, protected-file, rollback, and audit checks.",
            "",
            "## JSON sidecar",
            "",
            f"- `{audit.get('audit_json_path')}`",
            "",
        ]
    )
