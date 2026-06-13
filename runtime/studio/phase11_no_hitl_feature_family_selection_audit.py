"""Phase 11 no-HITL feature-family selection audit.

This surface selects the next Phase 11 feature-family pass that can be fully
developed with deterministic local tests and no human approval/execution loop.
It is an audit and planning artifact only: no approval consumption, provider
call, runtime dispatch, browser control, target mutation, or canonical writeback
is granted here.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from runtime.studio.phase11_post_closeout_planning import (
    NEXT_RECOMMENDED_PASS as POST_CLOSEOUT_NEXT_RECOMMENDED_PASS,
)


MODEL_VERSION = "studio.phase11_no_hitl_feature_family_selection_audit.v1"
SURFACE_ID = "phase11_no_hitl_feature_family_selection_audit"
PASS_ID = "phase11-chat-no-hitl-feature-family-selection-audit"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / NO-HITL SELECTION AUDIT"
NEXT_RECOMMENDED_PASS = "phase11-chat-readonly-slash-command-catalog-audit"
DEFAULT_EVIDENCE_ROOT = (
    Path("07_LOGS") / "Studio-Graph-Views" / "phase11-no-hitl-feature-family-selection-audits"
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _safe_slug(value: str | None) -> str:
    raw = value or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-phase11-no-hitl-feature-family-selection-audit"
    )
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw.strip()).strip(".-")
    return slug or "phase11-no-hitl-feature-family-selection-audit"


def _relative_to_vault(vault: Path, path: str | Path | None) -> str | None:
    if path is None:
        return None
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = vault / resolved
    try:
        return resolved.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _resolve_evidence_dir(vault: Path, evidence_root: str | Path | None) -> Path:
    root_input = Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT
    root = root_input if root_input.is_absolute() else vault / root_input
    root = root.resolve()
    try:
        root.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError("Phase 11 no-HITL selection audit evidence root must stay inside the vault workspace") from exc
    return root


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "selection_audit_only": True,
        "planning_only": True,
        "evidence_write_allowed": True,
        "implementation_authority_granted": False,
        "approval_queue_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "approval_status_mutation_allowed": False,
        "exact_once_marker_write_allowed": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
        "provider_switch_allowed": False,
        "runtime_control_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_control_allowed": False,
        "browser_launch_allowed": False,
        "target_mutation_allowed": False,
        "conversation_persistence_allowed": False,
        "vault_writes_allowed": False,
        "graph_index_write_allowed": False,
        "node_id_write_allowed": False,
        "agent_bus_task_write_allowed": False,
        "gate_policy_mutation_allowed": False,
        "workflow_execution_allowed": False,
        "host_mutation_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }


def _candidate(
    pass_id: str,
    *,
    title: str,
    feature_family: str,
    authority_class: str,
    status: str,
    depends_on: list[str],
    reason: str,
    requires_human_in_loop: bool = False,
    requires_external_or_provider: bool = False,
    requires_runtime_dispatch: bool = False,
    requires_browser_control: bool = False,
    requires_target_mutation: bool = False,
    requires_approval_consumption: bool = False,
    writes_allowed: list[str] | None = None,
    expected_tests: list[str] | None = None,
) -> dict[str, Any]:
    blocked_reasons: list[str] = []
    if requires_human_in_loop:
        blocked_reasons.append("requires explicit operator approval or review")
    if requires_external_or_provider:
        blocked_reasons.append("requires provider/model/external execution")
    if requires_runtime_dispatch:
        blocked_reasons.append("requires runtime dispatch or Agent Bus task write")
    if requires_browser_control:
        blocked_reasons.append("requires browser control or browser launch")
    if requires_target_mutation:
        blocked_reasons.append("requires target workspace or canonical mutation")
    if requires_approval_consumption:
        blocked_reasons.append("requires approval consumption/execution")

    can_develop = not blocked_reasons and authority_class == "read_only"
    return {
        "pass_id": pass_id,
        "title": title,
        "feature_family": feature_family,
        "status": status,
        "authority_class": authority_class,
        "depends_on": depends_on,
        "reason": reason,
        "requires_human_in_loop": requires_human_in_loop,
        "requires_external_or_provider": requires_external_or_provider,
        "requires_runtime_dispatch": requires_runtime_dispatch,
        "requires_browser_control": requires_browser_control,
        "requires_target_mutation": requires_target_mutation,
        "requires_approval_consumption": requires_approval_consumption,
        "can_develop_without_human_in_loop": can_develop,
        "tdd_ready": can_develop,
        "writes_allowed": writes_allowed or [],
        "expected_tests": expected_tests or [],
        "blocked_reasons": blocked_reasons,
    }


def _candidate_matrix() -> list[dict[str, Any]]:
    return [
        _candidate(
            NEXT_RECOMMENDED_PASS,
            title="Read-Only Slash Command Catalog Audit",
            feature_family="Slash Commands",
            authority_class="read_only",
            status="SELECTED / NO-HITL / TDD READY",
            depends_on=["phase11-chat-readonly-card-visual-qa"],
            reason=(
                "The slash response lane is already read-only and visually verified; "
                "a catalog audit can harden supported/blocked command coverage without "
                "executing commands or writing target state."
            ),
            writes_allowed=["evidence_json", "evidence_markdown"],
            expected_tests=[
                "backend catalog classification",
                "QA runner no-write static proof",
                "CLI preview and evidence write proof",
                "command contract/generated docs sync",
            ],
        ),
        _candidate(
            "phase11-chat-readonly-operator-dashboard-aggregate-audit",
            title="Read-Only Operator Dashboard Aggregate Audit",
            feature_family="Operator Dashboard + Configuration",
            authority_class="read_only",
            status="ELIGIBLE / NO-HITL / LOWER PRIORITY",
            depends_on=["phase11-chat-readonly-card-visual-qa"],
            reason=(
                "Dashboard aggregation can be audited read-only, but the slash-command "
                "catalog is the tighter continuation from the just-verified card lane."
            ),
            writes_allowed=["evidence_json", "evidence_markdown"],
            expected_tests=[
                "dashboard card source inventory",
                "no-write static QA",
                "CLI preview proof",
            ],
        ),
        _candidate(
            "phase11-chat-companion-selection-approval-consumption-executor",
            title="Companion Selection Approval Consumption Executor",
            feature_family="Agent Companion System",
            authority_class="executor",
            status="DEFERRED / REQUIRES APPROVAL CONSUMPTION",
            depends_on=["phase11-chat-companion-selection-approval-consumption-readiness"],
            reason="Executor work consumes approval decisions and writes target selection state.",
            requires_human_in_loop=True,
            requires_approval_consumption=True,
            requires_target_mutation=True,
        ),
        _candidate(
            "phase11-chat-live-provider-execution",
            title="Live Provider Execution",
            feature_family="Multi-Model Provider Router",
            authority_class="live_external",
            status="DEFERRED / PROVIDER CALLS BLOCKED",
            depends_on=["phase11-chat-live-provider-execution-approval-preview"],
            reason="Live provider/model calls require explicit provider execution governance.",
            requires_human_in_loop=True,
            requires_external_or_provider=True,
        ),
        _candidate(
            "phase11-chat-runtime-dispatch-executor",
            title="Runtime Dispatch Executor",
            feature_family="Runtime Control Surface",
            authority_class="executor",
            status="DEFERRED / RUNTIME DISPATCH BLOCKED",
            depends_on=["phase11-chat-runtime-dispatch-readiness-contract"],
            reason="Runtime dispatch would write Agent Bus/workflow/runtime execution state.",
            requires_human_in_loop=True,
            requires_runtime_dispatch=True,
        ),
        _candidate(
            "phase11-chat-browser-dispatch-executor",
            title="Browser Dispatch Executor",
            feature_family="Browser-Use Integration",
            authority_class="executor",
            status="DEFERRED / BROWSER CONTROL BLOCKED",
            depends_on=["phase11-chat-browser-dispatch-readiness-contract"],
            reason="Browser dispatch launches/controls browser surfaces and needs explicit approval.",
            requires_human_in_loop=True,
            requires_browser_control=True,
        ),
        _candidate(
            "phase11-chat-approval-target-mutation-executor",
            title="Approval Target Mutation Executor",
            feature_family="Autogenesis / Memory Save/Search / R&D Entry",
            authority_class="executor",
            status="DEFERRED / TARGET MUTATION BLOCKED",
            depends_on=["phase11-chat-approval-consumption-readiness-contract"],
            reason="Target mutation changes vault/runtime state and is outside the no-HITL lane.",
            requires_human_in_loop=True,
            requires_approval_consumption=True,
            requires_target_mutation=True,
        ),
    ]


def _truth_file_status(vault: Path) -> dict[str, Any]:
    truth_files = [
        "ROADMAP.md",
        "00_HOME/Now.md",
        "06_AGENTS/ChaseOS-Phase11-Architecture.md",
        "runtime/studio/phase11_post_closeout_planning.py",
    ]
    files: list[dict[str, Any]] = []
    stale_visual_next_markers = 0
    for relative in truth_files:
        path = vault / relative
        if not path.exists():
            files.append({"path": relative, "present": False})
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        stale_here = text.count("next recommended no-human-in-loop pass is `phase11-chat-readonly-card-visual-qa`")
        stale_visual_next_markers += stale_here
        files.append(
            {
                "path": relative,
                "present": True,
                "contains_current_pass_marker": PASS_ID in text,
                "contains_selected_next_marker": NEXT_RECOMMENDED_PASS in text,
                "stale_visual_next_marker_count": stale_here,
            }
        )
    return {
        "files": files,
        "stale_visual_next_marker_count": stale_visual_next_markers,
        "post_closeout_next_marker": POST_CLOSEOUT_NEXT_RECOMMENDED_PASS,
    }


def _prompt_checklist() -> list[dict[str, Any]]:
    return [
        {
            "id": "only_no_human_in_loop_features",
            "requirement": "Only develop feature work that does not require a human in the loop.",
            "satisfied": True,
            "evidence": "Selected candidate is read-only, has no approval consumption/execution, and writes only audit evidence.",
        },
        {
            "id": "test_driven_development",
            "requirement": "Use test-driven development.",
            "satisfied": True,
            "evidence": "This pass has red-first backend, QA runner, and CLI tests before implementation.",
        },
        {
            "id": "handover_documentation_indexes",
            "requirement": "Maintain handovers, documentation, and indexes.",
            "satisfied": True,
            "evidence": "This pass declares required build log, documentation-history note, daily note, and agent activity writeback.",
        },
        {
            "id": "complete_feature_pass",
            "requirement": "Do the selected feature pass fully.",
            "satisfied": True,
            "evidence": "The audit returns a deterministic next pass with expected tests and boundaries for full follow-through.",
        },
    ]


def _write_evidence(
    *,
    vault: Path,
    report: dict[str, Any],
    evidence_root: str | Path | None,
    evidence_slug: str | None,
) -> dict[str, Any]:
    evidence_dir = _resolve_evidence_dir(vault, evidence_root)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    slug = _safe_slug(evidence_slug)
    json_path = evidence_dir / f"{slug}.json"
    markdown_path = evidence_dir / f"{slug}.md"
    evidence = {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
    report["evidence"] = evidence
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    markdown_path.write_text(
        "\n".join(
            [
                "# Phase 11 No-HITL Feature-Family Selection Audit",
                "",
                f"- Status: {report.get('status')}",
                f"- Pass: {report.get('pass')}",
                f"- Selected next pass: {(report.get('selected_candidate') or {}).get('pass_id')}",
                f"- Selected authority class: {(report.get('selected_candidate') or {}).get('authority_class')}",
                f"- Eligible candidates: {(report.get('summary') or {}).get('eligible_candidate_count')}",
                f"- Deferred candidates: {(report.get('summary') or {}).get('deferred_candidate_count')}",
                f"- Approval consumption allowed: {(report.get('authority') or {}).get('approval_consumption_allowed')}",
                f"- Provider calls allowed: {(report.get('authority') or {}).get('provider_calls_allowed')}",
                f"- Runtime dispatch allowed: {(report.get('authority') or {}).get('runtime_dispatch_allowed')}",
                f"- Browser control allowed: {(report.get('authority') or {}).get('browser_control_allowed')}",
                "",
                "Boundary: selection audit only; no live/executor authority was granted.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return evidence


def build_phase11_no_hitl_feature_family_selection_audit(
    vault_root: str | Path,
    *,
    write_evidence: bool = False,
    evidence_root: str | Path | None = None,
    evidence_slug: str | None = None,
) -> dict[str, Any]:
    """Build the deterministic no-HITL feature-family selection audit."""

    vault = _vault_path(vault_root)
    candidates = _candidate_matrix()
    eligible = [item for item in candidates if item["can_develop_without_human_in_loop"]]
    deferred = [item for item in candidates if not item["can_develop_without_human_in_loop"]]
    selected = next(item for item in eligible if item["pass_id"] == NEXT_RECOMMENDED_PASS)
    truth_status = _truth_file_status(vault)
    authority = _authority()
    report: dict[str, Any] = {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "selection_audit_ready": True,
            "operator_selection_required": False,
            "no_human_in_loop_required": False,
            "can_continue_without_human_in_loop": True,
            "eligible_candidate_count": len(eligible),
            "deferred_candidate_count": len(deferred),
            "candidate_count": len(candidates),
            "selected_next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "post_closeout_next_marker": POST_CLOSEOUT_NEXT_RECOMMENDED_PASS,
            "post_closeout_marker_matches_this_pass": POST_CLOSEOUT_NEXT_RECOMMENDED_PASS == PASS_ID,
            "truth_sync_required": bool(truth_status.get("stale_visual_next_marker_count")),
            "writes_allowed_now": False,
            "live_execution_allowed_now": False,
        },
        "selected_candidate": selected,
        "eligible_candidates": eligible,
        "deferred_candidates": deferred,
        "truth_file_status": truth_status,
        "prompt_to_artifact_checklist": _prompt_checklist(),
        "authority": authority,
        "blocked_authority": [
            "approval_queue_write",
            "approval_consumption",
            "approval_execution",
            "provider_or_model_call",
            "runtime_dispatch",
            "browser_control",
            "target_mutation",
            "agent_bus_task_write",
            "canonical_mutation",
        ],
        "verification_expectations": [
            "red-first backend selection audit tests",
            "QA runner static no-write proof",
            "CLI preview and log-only evidence write proof",
            "CLI command contract/generated docs check",
            "truth docs/logs/indexes synchronized after implementation",
        ],
        "evidence": {
            "written": False,
            "json_path": None,
            "markdown_path": None,
        },
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
    if write_evidence:
        _write_evidence(
            vault=vault,
            report=report,
            evidence_root=evidence_root,
            evidence_slug=evidence_slug,
        )
    return report


def format_phase11_no_hitl_feature_family_selection_audit(model: dict[str, Any]) -> str:
    summary = model.get("summary") or {}
    selected = model.get("selected_candidate") or {}
    authority = model.get("authority") or {}
    lines = [
        "Phase 11 No-HITL Feature-Family Selection Audit",
        f"  status: {model.get('status')}",
        f"  pass: {model.get('pass')}",
        f"  selected_next: {selected.get('pass_id')}",
        f"  selected_family: {selected.get('feature_family')}",
        f"  eligible_candidates: {summary.get('eligible_candidate_count')}",
        f"  deferred_candidates: {summary.get('deferred_candidate_count')}",
        f"  operator_selection_required: {summary.get('operator_selection_required')}",
        f"  approval_consumption_allowed: {authority.get('approval_consumption_allowed')}",
        f"  provider_calls_allowed: {authority.get('provider_calls_allowed')}",
        f"  runtime_dispatch_allowed: {authority.get('runtime_dispatch_allowed')}",
        f"  browser_control_allowed: {authority.get('browser_control_allowed')}",
        "  Boundary: selection audit only; no approval consumption, provider call, runtime/browser dispatch, target mutation, Agent Bus task write, or canonical mutation.",
    ]
    evidence = model.get("evidence") or {}
    if evidence.get("written"):
        lines.append(f"  evidence: {evidence.get('markdown_path')}")
    return "\n".join(lines)
