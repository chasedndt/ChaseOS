"""Runtime memory mutation readiness for Personal Context Import.

Shows the current runtime memory state for each registered runtime and what
personal context route hints would be added to each runtime's nav map. Computes
a mutation readiness digest and supports queueing a digest-gated approval.

Does NOT mutate any runtime memory files.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.personal_context_import_runtime_memory_mutation_readiness.v1"
SURFACE_ID = "studio_personal_context_import_runtime_memory_mutation_readiness"
PASS_ID = "personal-context-import-runtime-memory-mutation-readiness"
APPROVAL_CLASS = "runtime_memory_mutation_readiness"
NEXT_RECOMMENDED_PASS = "personal-context-import-runtime-memory-approved-mutation-executor"
APPROVAL_ROOT = Path(
    "runtime/studio/approvals/personal-context-import/runtime-memory-mutation"
)

_RUNTIME_IDS = ("codex", "hermes", "archon")

_PERSONAL_CONTEXT_ROUTE_HINTS = (
    {
        "route_id": "personal_operator_index",
        "description": "Personal Operator Index hub for current operator identity and domain structure",
        "path": "00_HOME/Personal-Operator-Index.md",
        "trust": "operator_authored",
    },
    {
        "route_id": "personal_domains_index",
        "description": "Personal Domains Index covering fitness, language, networking, hardware, interests",
        "path": "00_HOME/Personal-Domains/Personal-Domains-Index.md",
        "trust": "operator_authored",
    },
    {
        "route_id": "personal_map_candidate_queue",
        "description": "Personal Map candidate JSONL queue with pending and approved candidates",
        "path": "07_LOGS/Pulse-Decks/memory-candidates/personal-map",
        "trust": "source_derived_review_required",
    },
    {
        "route_id": "personal_context_intake",
        "description": "Personal context raw intake and source digest artifacts",
        "path": "03_INPUTS/Personal-Context-Intake",
        "trust": "source_derived_review_required",
    },
    {
        "route_id": "applied_personal_map_graph",
        "description": "Applied Personal Map graph JSON with resolved nodes and edges",
        "path": "runtime/memory/personal-map/graph.json",
        "trust": "governed_apply_executed",
    },
)

_AUTHORITY = {
    "reads_runtime_memory_files": True,
    "reads_nav_maps": True,
    "runtime_memory_mutation_allowed": False,
    "nav_map_write_allowed": False,
    "canonical_writeback_allowed": False,
    "provider_calls_allowed": False,
    "agent_bus_dispatch_allowed": False,
    "secret_values_read": False,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _runtime_profile_path(runtime_id: str) -> Path:
    return Path("runtime/memory/adapters") / runtime_id / "profile.json"


def _runtime_nav_map_path(runtime_id: str) -> Path:
    return Path("runtime/memory/nav") / runtime_id / "nav-map.json"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _personal_context_already_in_nav(nav_data: dict[str, Any] | None) -> bool:
    if nav_data is None:
        return False
    routes = nav_data.get("successful_route_patterns") or []
    for route in routes:
        if isinstance(route, dict) and "personal_context" in str(route.get("pattern", "")):
            return True
        if isinstance(route, str) and "personal_context" in route:
            return True
    if "personal_context_routes" in str(nav_data):
        return True
    return False


def _runtime_state(vault: Path, runtime_id: str) -> dict[str, Any]:
    profile_path = vault / _runtime_profile_path(runtime_id)
    nav_path = vault / _runtime_nav_map_path(runtime_id)
    profile_data = _load_json(profile_path)
    nav_data = _load_json(nav_path)
    already_in_nav = _personal_context_already_in_nav(nav_data)
    return {
        "runtime_id": runtime_id,
        "profile_present": profile_path.exists(),
        "nav_map_present": nav_path.exists(),
        "profile_path": _runtime_profile_path(runtime_id).as_posix(),
        "nav_map_path": _runtime_nav_map_path(runtime_id).as_posix(),
        "profile_runtime": (profile_data or {}).get("runtime"),
        "personal_context_routes_already_present": already_in_nav,
        "mutation_needed": not already_in_nav,
    }


def _compute_mutation_digest(runtime_states: list[dict[str, Any]]) -> str:
    items = [
        {
            "runtime_id": s["runtime_id"],
            "profile_present": s["profile_present"],
            "nav_map_present": s["nav_map_present"],
            "personal_context_routes_already_present": s["personal_context_routes_already_present"],
        }
        for s in runtime_states
    ]
    route_hint_ids = sorted(h["route_id"] for h in _PERSONAL_CONTEXT_ROUTE_HINTS)
    return _sha256_text(
        _canonical_json(
            {
                "schema": MODEL_VERSION,
                "runtime_states": items,
                "route_hint_ids": route_hint_ids,
            }
        )
    )


def build_personal_context_import_runtime_memory_mutation_readiness(
    vault_root: str | Path,
) -> dict[str, Any]:
    """Return runtime memory mutation readiness for personal context route hints."""
    vault = Path(vault_root).resolve()
    runtime_states = [_runtime_state(vault, rid) for rid in _RUNTIME_IDS]
    mutation_digest = _compute_mutation_digest(runtime_states)

    runtimes_needing_mutation = [
        s["runtime_id"] for s in runtime_states if s["mutation_needed"]
    ]
    all_already_present = all(
        not s["mutation_needed"] for s in runtime_states
    )

    if all_already_present:
        status = "personal_context_routes_already_present_in_all_nav_maps"
    elif not runtimes_needing_mutation:
        status = "no_mutation_needed"
    else:
        status = f"mutation_needed_for_{len(runtimes_needing_mutation)}_runtimes"

    service = StudioService(vault)
    pending_approval_ids: list[str] = []
    try:
        for req in service.list_pending():
            meta = req.action_spec.metadata or {}
            if meta.get("runtime_memory_mutation_readiness_approval") is True:
                pending_approval_ids.append(req.approval_id)
    except Exception:
        pass

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "status": status,
        "mutation_digest": mutation_digest,
        "runtime_states": runtime_states,
        "runtimes_needing_mutation": runtimes_needing_mutation,
        "personal_context_route_hints": [dict(h) for h in _PERSONAL_CONTEXT_ROUTE_HINTS],
        "mutation_targets": [
            _runtime_nav_map_path(rid).as_posix()
            for rid in runtimes_needing_mutation
        ],
        "pending_approval_ids": pending_approval_ids,
        "approval_class": APPROVAL_CLASS,
        "can_request_approval": True,
        "mutation_gate_requirements": [
            "approval_id required",
            "exact runtime_memory_mutation_digest required",
            "operator_approval_statement required (must contain digest)",
            "execute=True required",
            "exact_once_marker reserved before any nav-map write",
        ],
        "authority": dict(_AUTHORITY),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def request_personal_context_import_runtime_memory_mutation_readiness_approval(
    vault_root: str | Path,
    *,
    expected_mutation_digest: str,
    operator_note: str = "",
    operator_id: str = "studio-operator",
) -> dict[str, Any]:
    """Queue a runtime memory mutation readiness approval (exact-digest-gated)."""
    vault = Path(vault_root).resolve()
    readiness = build_personal_context_import_runtime_memory_mutation_readiness(vault)
    actual_digest = str(readiness.get("mutation_digest") or "")
    expected = str(expected_mutation_digest or "").strip()

    blockers: list[str] = []
    if not expected:
        blockers.append("expected_mutation_digest_required")
    elif actual_digest != expected:
        blockers.append("mutation_digest_mismatch")

    if blockers:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "generated_at": _now_utc(),
            "vault_root": str(vault),
            "approval_queued": False,
            "blockers": blockers,
            "actual_mutation_digest": actual_digest,
            "expected_mutation_digest": expected,
        }

    service = StudioService(vault)
    for req in service.list_pending():
        meta = req.action_spec.metadata or {}
        if (
            meta.get("runtime_memory_mutation_readiness_approval") is True
            and meta.get("runtime_memory_mutation_digest") == actual_digest
        ):
            return {
                "ok": True,
                "surface": SURFACE_ID,
                "model_version": MODEL_VERSION,
                "generated_at": _now_utc(),
                "vault_root": str(vault),
                "approval_queued": False,
                "approval_already_exists": True,
                "approval_id": req.approval_id,
                "mutation_digest": actual_digest,
                "blockers": [],
            }

    content_payload = {
        "record_type": "personal_context_import_runtime_memory_mutation_readiness_approval",
        "schema_version": MODEL_VERSION,
        "mutation_digest": actual_digest,
        "runtime_states": readiness.get("runtime_states"),
        "personal_context_route_hints": readiness.get("personal_context_route_hints"),
        "mutation_targets": readiness.get("mutation_targets"),
        "source_text_included": False,
        "canonical_writeback_allowed": False,
        "future_executor_requires_matching_digest": True,
        "operator_note": operator_note,
    }
    target_path = (
        APPROVAL_ROOT / f"runtime-memory-mutation-{actual_digest[:16]}.json"
    ).as_posix()
    spec = ActionSpec(
        action_type="create_file",
        target_path=target_path,
        content=json.dumps(content_payload, indent=2, sort_keys=True) + "\n",
        metadata={
            "runtime_memory_mutation_readiness_approval": True,
            "runtime_memory_mutation_digest": actual_digest,
            "source_surface": SURFACE_ID,
            "required_approval_class": APPROVAL_CLASS,
            "runtime_memory_mutation_allowed": False,
            "source_text_included": False,
            "canonical_writeback_allowed": False,
        },
        submitted_by=operator_id,
        note=operator_note or "Runtime memory mutation readiness approval (digest-gated).",
    )
    req = service.queue_for_approval(spec)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "approval_queued": True,
        "approval_already_exists": False,
        "approval_id": req.approval_id,
        "mutation_digest": actual_digest,
        "blockers": [],
    }


def format_personal_context_import_runtime_memory_mutation_readiness(
    payload: dict[str, Any],
) -> str:
    lines = [
        "Personal Context Import Runtime Memory Mutation Readiness",
        f"Status: {payload.get('status')}",
        f"Mutation digest: {(payload.get('mutation_digest') or 'missing')[:24]}...",
        f"Runtimes needing mutation: {payload.get('runtimes_needing_mutation')}",
        f"Route hints: {len(payload.get('personal_context_route_hints') or [])}",
        f"Can request approval: {payload.get('can_request_approval')}",
        f"Next recommended pass: {payload.get('next_recommended_pass')}",
    ]
    return "\n".join(lines)
