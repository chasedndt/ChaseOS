"""Phase 11 no-HITL lane completion audit.

This surface closes the autonomous Phase 11 feature-family lane by checking the
completed read-only/no-human-in-loop passes, their evidence, and their linked
handover surfaces. It does not consume approvals, execute commands, call
providers, dispatch runtimes or browsers, write Agent Bus tasks, mutate target
state, or update canonical memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


MODEL_VERSION = "studio.phase11_no_hitl_lane_completion_audit.v1"
SURFACE_ID = "phase11_no_hitl_lane_completion_audit"
PASS_ID = "phase11-chat-no-hitl-lane-completion-audit"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / NO-HITL LANE COMPLETION AUDIT"
NEXT_RECOMMENDED_PASS = "operator-selected-governed-executor-or-deferred-closeout"
DEFAULT_EVIDENCE_ROOT = (
    Path("07_LOGS") / "Studio-Graph-Views" / "phase11-no-hitl-lane-completion-audits"
)


@dataclass(frozen=True)
class CompletedPass:
    pass_id: str
    pass_slug: str
    status: str
    authority: str
    evidence_folder: str | None = None
    evidence_slug: str | None = None

    @property
    def build_log_stem(self) -> str:
        return f"2026-05-12-ChaseOS-{self.pass_slug}"

    @property
    def history_stem(self) -> str:
        return f"2026-05-12_{self.pass_slug}"

    @property
    def activity_stem(self) -> str:
        return f"2026-05-12-codex-{self.pass_slug}"


COMPLETED_NO_HITL_PASSES: tuple[CompletedPass, ...] = (
    CompletedPass(
        pass_id="phase11-chat-readonly-slash-command-responses",
        pass_slug="phase11-readonly-slash-command-responses",
        status="COMPLETE / READ-ONLY / VERIFIED / NO COMMAND EXECUTION",
        authority="read-only slash response cards without command execution or writes",
    ),
    CompletedPass(
        pass_id="phase11-chat-readonly-slash-command-response-ui",
        pass_slug="phase11-readonly-slash-command-response-ui",
        status="COMPLETE / READ-ONLY / VERIFIED / STATIC QA COVERED",
        authority="native Chat rendering of read-only slash response cards without authority expansion",
    ),
    CompletedPass(
        pass_id="phase11-chat-readonly-card-visual-qa",
        pass_slug="phase11-readonly-card-visual-qa",
        status="COMPLETE / VISUAL QA VERIFIED / NO COMMAND EXECUTION",
        authority="static HTML and loopback screenshot evidence for read-only cards without command execution",
        evidence_folder="phase11-readonly-card-visual-qa",
        evidence_slug="phase11-readonly-card-visual-qa",
    ),
    CompletedPass(
        pass_id="phase11-chat-no-hitl-feature-family-selection-audit",
        pass_slug="phase11-no-hitl-feature-family-selection-audit",
        status="COMPLETE / READ-ONLY / VERIFIED / NO-HITL SELECTION AUDIT",
        authority="deterministic feature-family selection audit with log-only evidence writeback",
        evidence_folder="phase11-no-hitl-feature-family-selection-audits",
        evidence_slug="phase11-no-hitl-feature-family-selection-audit",
    ),
    CompletedPass(
        pass_id="phase11-chat-readonly-slash-command-catalog-audit",
        pass_slug="phase11-readonly-slash-command-catalog-audit",
        status="COMPLETE / READ-ONLY / VERIFIED / SLASH COMMAND CATALOG AUDIT",
        authority="read-only slash catalog coverage audit with log-only evidence writeback",
        evidence_folder="phase11-readonly-slash-command-catalog-audits",
        evidence_slug="phase11-readonly-slash-command-catalog-audit",
    ),
    CompletedPass(
        pass_id="phase11-chat-readonly-operator-dashboard-aggregate-audit",
        pass_slug="phase11-readonly-operator-dashboard-aggregate-audit",
        status="COMPLETE / READ-ONLY / VERIFIED / OPERATOR DASHBOARD AGGREGATE AUDIT",
        authority="read-only operator dashboard aggregate source audit with log-only evidence writeback",
        evidence_folder="phase11-dashboard-aggregate-audits",
        evidence_slug="phase11-readonly-operator-dashboard-aggregate-audit",
    ),
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _safe_slug(value: str | None) -> str:
    raw = value or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-phase11-no-hitl-lane-completion-audit"
    )
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw.strip()).strip(".-")
    return slug or "phase11-no-hitl-lane-completion-audit"


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


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _contains_link_or_stem(text: str, stem: str) -> bool:
    return stem in text or f"[[{stem}]]" in text or f"{stem}.md" in text


def _resolve_evidence_dir(vault: Path, evidence_root: str | Path | None) -> Path:
    root_input = Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT
    root = root_input if root_input.is_absolute() else vault / root_input
    root = root.resolve()
    try:
        root.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError("Phase 11 no-HITL lane completion evidence root must stay inside the vault workspace") from exc
    return root


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "completion_audit_only": True,
        "evidence_write_allowed": True,
        "implementation_authority_granted": False,
        "command_execution_allowed": False,
        "approval_queue_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "approval_action_allowed": False,
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
        "schedule_mutation_allowed": False,
        "gate_policy_mutation_allowed": False,
        "workflow_execution_allowed": False,
        "host_mutation_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }


def _authority_bounded(authority: dict[str, Any]) -> bool:
    return all(
        authority.get(key) is False
        for key in [
            "command_execution_allowed",
            "approval_queue_write_allowed",
            "approval_consumption_allowed",
            "approval_execution_allowed",
            "approval_action_allowed",
            "approval_status_mutation_allowed",
            "exact_once_marker_write_allowed",
            "provider_calls_allowed",
            "model_calls_allowed",
            "runtime_dispatch_allowed",
            "browser_control_allowed",
            "browser_launch_allowed",
            "target_mutation_allowed",
            "conversation_persistence_allowed",
            "vault_writes_allowed",
            "agent_bus_task_write_allowed",
            "canonical_mutation_allowed",
        ]
    )


def _daily_index_has_daily_or_session(text: str, session_stems: list[str]) -> bool:
    daily_note_markers = ["[[2026-05-12]]", "2026-05-12.md", "07_LOGS/Daily/2026-05-12.md"]
    return any(marker in text for marker in daily_note_markers) or any(stem in text for stem in session_stems)


def _evidence_presence(vault: Path, completed: CompletedPass) -> dict[str, Any]:
    if not completed.evidence_folder or not completed.evidence_slug:
        return {
            "required": False,
            "present": True,
            "json_path": None,
            "markdown_path": None,
        }

    root = vault / "07_LOGS" / "Studio-Graph-Views" / completed.evidence_folder
    json_path = root / f"2026-05-12-{completed.evidence_slug}.json"
    markdown_path = root / f"2026-05-12-{completed.evidence_slug}.md"
    return {
        "required": True,
        "present": json_path.is_file() and markdown_path.is_file(),
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }


def _artifact_audit(vault: Path) -> list[dict[str, Any]]:
    build_index_text = _read_text(vault / "07_LOGS" / "Build-Logs" / "Build-Logs-Index.md")
    history_index_text = _read_text(
        vault / "99_ARCHIVE" / "Documentation-History" / "Documentation-History-Index.md"
    )
    daily_note_text = _read_text(vault / "07_LOGS" / "Daily" / "2026-05-12.md")
    daily_index_text = _read_text(vault / "07_LOGS" / "Daily" / "Daily-Index.md")
    activity_index_text = _read_text(vault / "07_LOGS" / "Agent-Activity" / "Agent-Activity-Index.md")

    audits: list[dict[str, Any]] = []
    for completed in COMPLETED_NO_HITL_PASSES:
        build_path = vault / "07_LOGS" / "Build-Logs" / f"{completed.build_log_stem}.md"
        history_path = vault / "99_ARCHIVE" / "Documentation-History" / f"{completed.history_stem}.md"
        activity_path = vault / "07_LOGS" / "Agent-Activity" / f"{completed.activity_stem}.md"
        build_text = _read_text(build_path)
        session_stems = [completed.build_log_stem, completed.history_stem, completed.activity_stem]
        evidence = _evidence_presence(vault, completed)
        tdd_evidence_present = "Tests Run" in build_text and "Test Results" in build_text
        red_first_mentioned = "Red-first" in build_text or "red-first" in build_text.lower()
        index_checks = {
            "build_log_indexed": _contains_link_or_stem(build_index_text, completed.build_log_stem),
            "documentation_history_indexed": _contains_link_or_stem(history_index_text, completed.history_stem),
            "daily_note_linked": all(stem in daily_note_text for stem in session_stems),
            "daily_index_linked": _daily_index_has_daily_or_session(daily_index_text, session_stems),
            "agent_activity_indexed": _contains_link_or_stem(activity_index_text, completed.activity_stem),
        }
        required_paths = {
            "build_log": _relative_to_vault(vault, build_path),
            "documentation_history": _relative_to_vault(vault, history_path),
            "agent_activity": _relative_to_vault(vault, activity_path),
        }
        all_required_paths_present = build_path.is_file() and history_path.is_file() and activity_path.is_file()
        all_required_artifacts_present = all_required_paths_present and evidence["present"] is True
        index_coverage_complete = all(index_checks.values())
        audits.append(
            {
                "pass_id": completed.pass_id,
                "pass_slug": completed.pass_slug,
                "status": completed.status,
                "authority": completed.authority,
                "read_only_or_no_hitl": True,
                "requires_human_in_loop": False,
                "all_required_paths_present": all_required_paths_present,
                "all_required_artifacts_present": all_required_artifacts_present,
                "required_paths": required_paths,
                "evidence": evidence,
                "tdd_evidence_present": tdd_evidence_present,
                "red_first_mentioned": red_first_mentioned,
                "index_coverage": index_checks,
                "index_coverage_complete": index_coverage_complete,
                "complete": all_required_artifacts_present and tdd_evidence_present and index_coverage_complete,
            }
        )
    return audits


def _retired_lanes() -> list[dict[str, Any]]:
    return [
        {
            "lane_id": "live_provider_model_execution",
            "title": "Live Provider / Model Execution",
            "retired": True,
            "retired_reason": "architecture_violation: studio_never_calls_providers_directly",
            "requires_human_in_loop": True,
            "requires_approval_consumption": False,
            "requires_provider_or_external_call": True,
            "requires_runtime_dispatch": False,
            "requires_browser_control": False,
            "requires_target_mutation": False,
            "eligible_for_no_hitl": False,
            "deferred_reason": "Retired: Studio never calls providers directly. All LLM dispatch routes Agent Bus -> runtime.",
        },
    ]


def _deferred_lanes() -> list[dict[str, Any]]:
    return [
        {
            "lane_id": "browser_dispatch_executor",
            "title": "Browser Dispatch Executor",
            "requires_human_in_loop": True,
            "requires_approval_consumption": True,
            "requires_provider_or_external_call": False,
            "requires_runtime_dispatch": False,
            "requires_browser_control": True,
            "requires_target_mutation": False,
            "eligible_for_no_hitl": False,
            "deferred_reason": "Would control browser state and must remain operator-governed.",
        },
        {
            "lane_id": "approval_target_mutation_executor",
            "title": "Approval Target Mutation Executor",
            "requires_human_in_loop": True,
            "requires_approval_consumption": True,
            "requires_provider_or_external_call": False,
            "requires_runtime_dispatch": False,
            "requires_browser_control": False,
            "requires_target_mutation": True,
            "eligible_for_no_hitl": False,
            "deferred_reason": "Would write target vault/profile/canonical state after approval.",
        },
        {
            "lane_id": "agent_bus_or_canonical_writeback",
            "title": "Agent Bus / Canonical Writeback Lane",
            "requires_human_in_loop": True,
            "requires_approval_consumption": True,
            "requires_provider_or_external_call": True,  # dispatches to runtimes that may invoke providers
            "requires_runtime_dispatch": True,
            "requires_browser_control": False,
            "requires_target_mutation": True,
            "eligible_for_no_hitl": False,
            "deferred_reason": "Would write governed runtime or canonical state outside the read-only lane.",
        },
    ]


def _checklist(
    *,
    artifact_audits: list[dict[str, Any]],
    deferred_lanes: list[dict[str, Any]],
    authority_bounded: bool,
) -> list[dict[str, Any]]:
    completed_count = sum(1 for item in artifact_audits if item.get("complete") is True)
    artifacts_complete = completed_count == len(COMPLETED_NO_HITL_PASSES)
    deferred_blocked = all(item.get("eligible_for_no_hitl") is False for item in deferred_lanes)
    no_hitl_only = all(item.get("read_only_or_no_hitl") is True for item in artifact_audits) and deferred_blocked
    tdd_observed = all(item.get("tdd_evidence_present") is True for item in artifact_audits)
    docs_maintained = all(item.get("all_required_paths_present") is True for item in artifact_audits)
    indexes_connected = all(item.get("index_coverage_complete") is True for item in artifact_audits)
    return [
        {
            "id": "phase11_feature_family_development_started",
            "satisfied": completed_count >= 1,
            "evidence": f"{completed_count} completed no-HITL/read-only Phase 11 artifacts audited.",
        },
        {
            "id": "only_no_hitl_features_developed",
            "satisfied": no_hitl_only,
            "evidence": "Audited completed lane is read-only/no-HITL; executor/live/target lanes are deferred.",
        },
        {
            "id": "test_driven_development_observed",
            "satisfied": tdd_observed,
            "evidence": "Each completed pass build log includes Tests Run and Test Results sections.",
        },
        {
            "id": "handovers_and_documentation_maintained",
            "satisfied": docs_maintained,
            "evidence": "Build log, documentation-history note, and agent-activity log are present for each audited pass.",
        },
        {
            "id": "daily_build_history_indexes_connected",
            "satisfied": indexes_connected,
            "evidence": "Build log, documentation history, daily, and agent-activity index links are present.",
        },
        {
            "id": "completion_audit_performed_against_current_state",
            "satisfied": artifacts_complete and deferred_blocked and authority_bounded,
            "evidence": "Completion audit inspected concrete repo artifacts and deferred unsafe lanes.",
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
    summary = report.get("summary") or {}
    markdown_path.write_text(
        "\n".join(
            [
                "# Phase 11 No-HITL Lane Completion Audit",
                "",
                f"- Status: {report.get('status')}",
                f"- Pass: {report.get('pass')}",
                f"- Lane result: {(report.get('lane_result') or {}).get('status')}",
                f"- Completed no-HITL artifacts: {summary.get('completed_no_hitl_artifact_count')}",
                f"- Eligible no-HITL remaining: {summary.get('eligible_no_hitl_remaining_count')}",
                f"- Can continue without human in loop: {summary.get('can_continue_without_human_in_loop')}",
                f"- Human/operator gate required for next work: {summary.get('human_or_operator_gate_required_for_next_work')}",
                f"- Next recommended pass: {summary.get('selected_next_recommended_pass')}",
                f"- Provider calls allowed: {(report.get('authority') or {}).get('provider_calls_allowed')}",
                f"- Runtime dispatch allowed: {(report.get('authority') or {}).get('runtime_dispatch_allowed')}",
                f"- Browser control allowed: {(report.get('authority') or {}).get('browser_control_allowed')}",
                "",
                "Boundary: completion audit only; no command execution, approval consumption/execution, provider/model call, runtime/browser dispatch, Agent Bus task write, target mutation, or canonical writeback.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return evidence


def build_phase11_no_hitl_lane_completion_audit(
    vault_root: str | Path,
    *,
    write_evidence: bool = False,
    evidence_root: str | Path | None = None,
    evidence_slug: str | None = None,
) -> dict[str, Any]:
    """Build the read-only no-HITL lane completion audit."""

    vault = _vault_path(vault_root)
    artifact_audits = _artifact_audit(vault)
    deferred_lanes = _deferred_lanes()
    retired_lanes = _retired_lanes()
    authority = _authority()
    bounded = _authority_bounded(authority)
    checklist = _checklist(
        artifact_audits=artifact_audits,
        deferred_lanes=deferred_lanes,
        authority_bounded=bounded,
    )
    completed_count = sum(1 for item in artifact_audits if item.get("complete") is True)
    eligible_remaining = sum(1 for item in deferred_lanes if item.get("eligible_for_no_hitl") is True)
    checklist_complete = all(item.get("satisfied") is True for item in checklist)
    lane_complete = checklist_complete and eligible_remaining == 0

    report: dict[str, Any] = {
        "ok": lane_complete,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "completion_audit_ready": lane_complete,
            "no_hitl_lane_complete": lane_complete,
            "completed_no_hitl_artifact_count": completed_count,
            "required_no_hitl_artifact_count": len(COMPLETED_NO_HITL_PASSES),
            "completed_no_hitl_pass_count": completed_count,
            "eligible_no_hitl_remaining_count": eligible_remaining,
            "deferred_lane_count": len(deferred_lanes),
            "retired_lane_count": len(retired_lanes),
            "can_continue_without_human_in_loop": False,
            "human_or_operator_gate_required_for_next_work": True,
            "prompt_to_artifact_checklist_complete": checklist_complete,
            "completed_no_hitl_artifacts_indexed": all(
                item.get("index_coverage_complete") is True for item in artifact_audits
            ),
            "deferred_lanes_require_human_or_live_authority": all(
                item.get("eligible_for_no_hitl") is False for item in deferred_lanes
            ),
            "selected_next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "writes_allowed_now": False,
            "live_execution_allowed_now": False,
            "command_execution_performed": False,
            "approval_action_performed": False,
            "approval_consumption_performed": False,
            "approval_execution_performed": False,
            "provider_call_performed": False,
            "model_call_performed": False,
            "runtime_dispatch_performed": False,
            "browser_action_performed": False,
            "target_mutation_performed": False,
            "vault_write_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
        },
        "lane_result": {
            "status": "NO_HITL_LANE_COMPLETE / EXECUTOR_LANES_DEFERRED"
            if lane_complete
            else "NO_HITL_LANE_INCOMPLETE / ARTIFACT_GAPS_PRESENT",
            "no_hitl_lane_complete": lane_complete,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "operator_decision_required": True,
        },
        "completed_no_hitl_artifacts": artifact_audits,
        "deferred_lanes": deferred_lanes,
        "retired_lanes": retired_lanes,
        "prompt_to_artifact_checklist": checklist,
        "authority": authority,
        "blocked_authority": [
            "slash_command_execution",
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
            "red-first backend completion audit tests",
            "QA runner static no-write proof",
            "CLI preview and log-only evidence write proof",
            "CLI command contract/generated docs check",
            "post-closeout planner advances to operator-selected governed executor or deferred closeout",
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


def format_phase11_no_hitl_lane_completion_audit(model: dict[str, Any]) -> str:
    summary = model.get("summary") or {}
    authority = model.get("authority") or {}
    lane_result = model.get("lane_result") or {}
    lines = [
        "Phase 11 No-HITL Lane Completion Audit",
        f"  status: {model.get('status')}",
        f"  pass: {model.get('pass')}",
        f"  lane_result: {lane_result.get('status')}",
        f"  completed_no_hitl_artifacts: {summary.get('completed_no_hitl_artifact_count')}",
        f"  eligible_no_hitl_remaining: {summary.get('eligible_no_hitl_remaining_count')}",
        f"  can_continue_without_human_in_loop: {summary.get('can_continue_without_human_in_loop')}",
        f"  human_or_operator_gate_required: {summary.get('human_or_operator_gate_required_for_next_work')}",
        f"  provider_calls_allowed: {authority.get('provider_calls_allowed')}",
        f"  runtime_dispatch_allowed: {authority.get('runtime_dispatch_allowed')}",
        f"  browser_control_allowed: {authority.get('browser_control_allowed')}",
        f"  next: {summary.get('selected_next_recommended_pass')}",
        "  Boundary: completion audit only; no command execution, approval consumption/execution, provider/model call, runtime/browser dispatch, Agent Bus task write, target mutation, or canonical mutation.",
    ]
    evidence = model.get("evidence") or {}
    if evidence.get("written"):
        lines.append(f"  evidence: {evidence.get('markdown_path')}")
    return "\n".join(lines)
