"""Read-only Studio Runtime Support Loops contract builders.

Runtime Support Loops expose QA verification, proactive suggestions, usage
metrics, and repair candidates as advisory Studio evidence. They intentionally
perform no writes, no approval consumption, no Agent Bus task creation, no
runtime dispatch, and no provider/connector calls.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL_VERSION = "studio.runtime_support_loops.v1"

BLOCKED_AUTHORITY = [
    "approve_action",
    "consume_approval",
    "create_agent_bus_task",
    "write_runtime_memory",
    "apply_repair_memory",
    "dispatch_runtime",
    "execute_workflow",
    "call_provider",
    "call_connector",
    "modify_role_card_or_manifest",
    "mutate_trust_or_permission_posture",
    "canonical_writeback",
    "self_upgrade_runtime",
]

EVIDENCE_SOURCES = {
    "contract_doc": "06_AGENTS/Runtime-Support-Loops-Contract.md",
    "runtime_intelligence_panels": "runtime/studio/runtime_intelligence_panels.py",
    "scorecards": "runtime/memory/scorecards/*.json",
    "repair_memory": "runtime/memory/repair/*.json",
    "runtime_navigation": "runtime/memory/nav/*/nav-map.json",
    "aor_osril_events": "runtime/osril/run/*.events.jsonl",
    "agent_activity": "07_LOGS/Agent-Activity/",
    "pulse_readiness": "runtime/pulse/README.md",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _native_panel(panel_id: str) -> dict[str, Any]:
    return {
        "mounted": True,
        "panel_id": panel_id,
        "frontend_target": f"panel-{panel_id}",
        "route_hint": f"#{panel_id}",
        "read_only": True,
        "status": "mounted-read-only",
    }


def _authority() -> dict[str, Any]:
    return {
        "advisory_only": True,
        "read_only": True,
        "operator_approval_required_for_action": True,
        "writes_memory": False,
        "writes_agent_bus_tasks": False,
        "executes_workflows": False,
        "dispatches_runtimes": False,
        "consumes_approvals": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "canonical_mutation_allowed": False,
        "approves_actions": False,
        "applies_repair_candidates": False,
        "creates_second_datastore": False,
        "self_upgrade_allowed": False,
    }


def _stable_id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.relative_to(vault).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _scorecard_files(vault: Path, runtime_id: str | None = None) -> list[Path]:
    root = vault / "runtime/memory/scorecards"
    if runtime_id:
        candidate = root / f"{runtime_id}.json"
        return [candidate] if candidate.exists() else []
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.json") if path.is_file())


def _repair_files(vault: Path, runtime_id: str | None = None) -> list[Path]:
    root = vault / "runtime/memory/repair"
    if runtime_id:
        candidate = root / f"{runtime_id}.json"
        return [candidate] if candidate.exists() else []
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.json") if path.is_file())


def _scorecard_runs(scorecard: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("runs", "outcomes", "execution_history", "records"):
        value = scorecard.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _repair_patterns(repair_memory: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("repair_patterns", "incident_candidates", "failure_patterns", "candidates"):
        value = repair_memory.get(key)
        if isinstance(value, list):
            patterns = [item for item in value if isinstance(item, dict)]
            if patterns:
                return patterns
    return []


def build_support_loop_contract(vault_root: str | Path) -> dict[str, Any]:
    """Return the read-only Runtime Support Loops Studio contract."""
    vault = _vault_path(vault_root)
    return {
        "ok": True,
        "surface": "studio_runtime_support_loops_contract",
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "native_panel": _native_panel("runtime-support-loops"),
        "loop_families": {
            "qa_verification": {
                "packet": "qa_verification_packet",
                "allowed_actions": ["inspect", "report_to_operator"],
                "forbidden": ["fix_outputs", "rerun_workflow", "create_agent_bus_task", "approve_outputs"],
            },
            "proactive_suggestion": {
                "packet": "proactive_suggestion_packet",
                "approval_required": True,
                "allowed_actions": ["suggest_only", "route_to_operator_review"],
                "forbidden": ["auto_execute", "consume_approval", "write_memory", "dispatch_runtime"],
            },
            "usage_tracking": {
                "packet": "usage_metrics_packet",
                "allowed_actions": ["summarize_existing_evidence"],
                "forbidden": ["create_second_datastore", "mutate_scorecards", "change_runtime_selection"],
            },
            "execution_repair": {
                "packet": "repair_candidate_packet",
                "review_required": True,
                "apply_allowed": False,
                "allowed_actions": ["propose_for_review"],
                "forbidden": ["self_upgrade", "patch_skills", "edit_runtime_memory", "apply_repair_memory"],
            },
        },
        "authority": _authority(),
        "blocked_authority": list(BLOCKED_AUTHORITY),
        "allowed_actions": ["inspect-runtime-support-loops-panel"],
        "possible_writes": [],
        "evidence_sources": dict(EVIDENCE_SOURCES),
    }


def build_qa_verification_packet(
    vault_root: str | Path,
    *,
    source_ref: str | None = None,
    declared_success_criteria: list[str] | None = None,
    observed_evidence_refs: list[str] | None = None,
    missing_evidence: list[str] | None = None,
    discrepancies: list[str] | None = None,
    confidence: str = "needs_operator_review",
) -> dict[str, Any]:
    """Build an advisory QA verification packet without performing QA actions."""
    vault = _vault_path(vault_root)
    evidence_refs = list(observed_evidence_refs or [])
    return {
        "ok": True,
        "loop_id": _stable_id("qa", source_ref or "unspecified", evidence_refs),
        "loop_family": "qa_verification",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "source_run_ref": source_ref,
        "declared_success_criteria": list(declared_success_criteria or []),
        "observed_evidence_refs": evidence_refs,
        "missing_evidence": list(missing_evidence or []),
        "discrepancies": list(discrepancies or []),
        "confidence": confidence,
        "operator_review_required": True,
        "allowed_next_actions": ["operator_review"],
        "allowed_actions": ["inspect", "report_to_operator"],
        "possible_writes": [],
        "authority": _authority(),
        "blocked_authority": list(BLOCKED_AUTHORITY),
    }


def build_proactive_suggestion_packet(
    vault_root: str | Path,
    *,
    source_ref: str | None = None,
    recommendation_text: str | None = None,
    why_now: str | None = None,
    evidence_refs: list[str] | None = None,
    confidence: str = "candidate",
    suggested_route: str = "operator_review",
) -> dict[str, Any]:
    """Build an approval-required suggestion packet; it cannot enqueue or execute."""
    vault = _vault_path(vault_root)
    refs = list(evidence_refs or [])
    if source_ref and source_ref not in refs:
        refs.append(source_ref)
    text = recommendation_text or "Review runtime support-loop evidence for a possible next step."
    return {
        "ok": True,
        "suggestion_id": _stable_id("suggestion", source_ref or "unspecified", text),
        "loop_family": "proactive_suggestion",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "source_refs": [source_ref] if source_ref else [],
        "recommendation_text": text,
        "why_now": why_now or "Existing support-loop evidence indicates an operator-visible follow-up may be useful.",
        "evidence_refs": refs,
        "confidence": confidence,
        "approval_required": True,
        "suggested_route": suggested_route,
        "allowed_actions": ["suggest_only", "route_to_operator_review"],
        "possible_writes": [],
        "authority": _authority(),
        "blocked_authority": list(BLOCKED_AUTHORITY),
    }


def build_proactive_suggestions_packet(vault_root: str | Path, **kwargs: Any) -> dict[str, Any]:
    """Backward-compatible plural alias for the contract wording."""
    return build_proactive_suggestion_packet(vault_root, **kwargs)


def build_usage_metrics_packet(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    workflow_id: str | None = None,
    surface_id: str | None = None,
    window: str | None = None,
) -> dict[str, Any]:
    """Summarize existing scorecard evidence without creating an analytics store."""
    vault = _vault_path(vault_root)
    scorecards = [(_rel(vault, path), _read_json_file(path)) for path in _scorecard_files(vault, runtime_id)]
    runs: list[dict[str, Any]] = []
    for _, scorecard in scorecards:
        runs.extend(_scorecard_runs(scorecard))
    success_count = sum(1 for item in runs if str(item.get("status") or "").lower() in {"success", "passed", "complete", "completed"})
    blocked_count = sum(1 for item in runs if str(item.get("status") or "").lower() in {"blocked", "escalated", "halted"})
    approval_requested_count = sum(1 for item in runs if bool(item.get("approval_requested") or item.get("approval_required")))
    acceptance_count = sum(1 for item in runs if bool(item.get("operator_acceptance_signal") or item.get("accepted_by_operator")))
    resolved_runtime_id = runtime_id or next((str(card.get("runtime_id")) for _, card in scorecards if card.get("runtime_id")), None)
    resolved_workflow_id = workflow_id or next((str(card.get("workflow_id")) for _, card in scorecards if card.get("workflow_id")), None)
    return {
        "ok": True,
        "metrics_id": _stable_id("metrics", resolved_runtime_id or "all", resolved_workflow_id or surface_id or "all", window or "unspecified"),
        "loop_family": "usage_tracking",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "runtime_id": resolved_runtime_id,
        "workflow_id": resolved_workflow_id,
        "surface_id": surface_id,
        "time_window": window or "unspecified",
        "run_count": len(runs),
        "success_count": success_count,
        "blocked_count": blocked_count,
        "approval_requested_count": approval_requested_count,
        "operator_acceptance_signal_count": acceptance_count,
        "scorecard_refs": [ref for ref, _ in scorecards],
        "coverage_notes": [
            "Usage metrics summarize existing scorecard/audit-style evidence only.",
            "No second analytics datastore is created by this builder.",
        ],
        "allowed_actions": ["summarize_existing_evidence"],
        "possible_writes": [],
        "authority": _authority(),
        "blocked_authority": list(BLOCKED_AUTHORITY),
    }


def build_repair_candidate_packet(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
) -> dict[str, Any]:
    """Surface one execution-repair candidate for review; never applies it."""
    vault = _vault_path(vault_root)
    repair_refs = _repair_files(vault, runtime_id)
    selected_ref: str | None = None
    selected_runtime = runtime_id
    selected_pattern: dict[str, Any] = {}
    for path in repair_refs:
        payload = _read_json_file(path)
        patterns = _repair_patterns(payload)
        if patterns:
            selected_ref = _rel(vault, path)
            selected_runtime = selected_runtime or str(payload.get("runtime_id") or path.stem)
            selected_pattern = patterns[0]
            break
    failure_pattern = str(selected_pattern.get("failure_pattern") or selected_pattern.get("summary") or "No repeated failure pattern selected.")
    proposed_text = str(selected_pattern.get("proposed_repair_text") or selected_pattern.get("proposal") or "No repair proposal is applied; operator review is required.")
    evidence_refs = selected_pattern.get("evidence_refs") if isinstance(selected_pattern.get("evidence_refs"), list) else []
    if selected_ref and selected_ref not in evidence_refs:
        evidence_refs = [*evidence_refs, selected_ref]
    return {
        "ok": True,
        "repair_candidate_id": str(selected_pattern.get("id") or _stable_id("repair", selected_runtime or "unknown", failure_pattern)),
        "loop_family": "execution_repair",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "runtime_id": selected_runtime,
        "failure_pattern": failure_pattern,
        "evidence_refs": evidence_refs,
        "proposed_repair_text": proposed_text,
        "risk_level": str(selected_pattern.get("risk_level") or "unknown"),
        "review_required": True,
        "apply_allowed": False,
        "allowed_actions": ["propose_for_review"],
        "possible_writes": [],
        "authority": _authority(),
        "blocked_authority": list(BLOCKED_AUTHORITY),
    }


def build_runtime_support_loops_panel(vault_root: str | Path) -> dict[str, Any]:
    """Build the aggregate read-only Studio Runtime Support Loops panel."""
    vault = _vault_path(vault_root)
    contract = build_support_loop_contract(vault)
    qa = build_qa_verification_packet(vault)
    suggestion = build_proactive_suggestion_packet(vault)
    usage = build_usage_metrics_packet(vault)
    repair = build_repair_candidate_packet(vault)
    return {
        "ok": True,
        "surface": "studio_runtime_support_loops_panel",
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "native_panel": _native_panel("runtime-support-loops"),
        "summary": {
            "overall_status": "mounted-read-only",
            "loop_family_count": 4,
            "advisory_only": True,
            "operator_approval_required_for_suggestions": True,
            "repair_apply_allowed": False,
        },
        "contract": contract,
        "packets": {
            "qa_verification_packet": qa,
            "proactive_suggestion_packet": suggestion,
            "usage_metrics_packet": usage,
            "repair_candidate_packet": repair,
        },
        "authority": _authority(),
        "blocked_authority": list(BLOCKED_AUTHORITY),
        "allowed_actions": ["inspect-runtime-support-loops-panel"],
        "possible_writes": [],
        "readiness": {
            "runtime_support_loops_panel_mounted": True,
            "qa_verification_packet_available": True,
            "proactive_suggestion_packet_available": True,
            "usage_metrics_packet_available": True,
            "repair_candidate_packet_available": True,
            "no_memory_mutation": True,
            "no_agent_bus_task_write": True,
            "no_runtime_dispatch": True,
            "no_approval_consumption": True,
            "no_provider_or_connector_call": True,
            "no_canonical_writeback": True,
        },
    }
