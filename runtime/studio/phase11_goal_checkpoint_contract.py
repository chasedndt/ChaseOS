"""Read-only Phase 11 long-running /goal checkpoint contract.

This module provides a deterministic checkpoint fixture/template for
Hermes/Optimus continuation agents. It is intentionally read-only: callers get
an inspectable checkpoint shape, artifact-path expectations, no-write proof
fields, and dependency-routing examples without provider calls, browser launch,
Agent Bus writes, approval consumption, runtime dispatch, credential/config
mutation, protected-file writes, or canonical writeback.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.phase11_goal_checkpoint_contract.v1"
SURFACE_ID = "phase11_goal_checkpoint_contract"
CHECKPOINT_STATUS = "READ-ONLY / HANDOFF TEMPLATE / NO-WRITE PROOF"

NO_WRITE_PROOF_FIELDS = [
    "provider_call",
    "browser_launch",
    "agent_bus_task_written",
    "approval_consumed",
    "runtime_dispatched",
    "credential_config_mutated",
    "protected_file_written",
    "canonical_writeback",
]

DEPENDENCY_REPORT_FIELDS = [
    "missing_contract",
    "affected_phase10_or_phase11_surface",
    "lower_phase_owner_or_surface",
    "minimum_proof_needed",
    "blocked_action_reason",
]

DEFAULT_ARTIFACT_PATHS = [
    "06_AGENTS/Hermes-Phase11-Implementation-Handover.md",
    "07_LOGS/Agent-Activity/YYYY-MM-DD-hermes-optimus-<topic>.md",
    "07_LOGS/Agent-Activity/Agent-Activity-Index.md",
    "runtime/studio/phase11_goal_checkpoint_contract.py",
    "runtime/studio/test_phase11_goal_checkpoint_contract.py",
]


DEPENDENCY_ROUTING_EXAMPLES = [
    {
        "dependency_key": "agent_bus_runtime_dispatch",
        "missing_contract": "agent_bus runtime dispatch packet creation and claim/execute contract",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat runtime task preview / handoff surface",
        "lower_phase_owner_or_surface": "runtime/agent_bus router plus Phase 9 AOR workflow foundation",
        "minimum_proof_needed": "schema-valid packet preview, eligible runtime route, approval envelope where required, non-Chat execution consumer, and audit proof",
        "blocked_action_reason": "Chat may preview the handoff but must not create Agent Bus tasks, claim work, or dispatch executable runtimes",
    },
    {
        "dependency_key": "provider_execution",
        "missing_contract": "approval-gated provider execution consumer contract",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat answer/proposal preview surface",
        "lower_phase_owner_or_surface": "RPGL/provider governance and approved provider execution lane",
        "minimum_proof_needed": "approved provider route, redacted credential reference, exact consumer proof, no-secret audit record, and rollback/replay policy",
        "blocked_action_reason": "Checkpointing may record provider readiness but must not call live providers or consume provider approvals",
    },
    {
        "dependency_key": "protected_or_canonical_writeback",
        "missing_contract": "Gate-governed protected-file/canonical writeback contract",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat handoff and Agent-Activity continuation record surface",
        "lower_phase_owner_or_surface": "ChaseOS Gate, Permission Matrix, and canonical promotion workflow",
        "minimum_proof_needed": "operator-approved candidate artifact, provenance proof, protected-file allowlist, Gate decision, and audit writeback",
        "blocked_action_reason": "Hermes/Optimus checkpoint templates may write approved audit/handoff artifacts only; they must not mutate protected files or canonical knowledge",
    },
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_posix_list(values: list[str | Path] | None, fallback: list[str]) -> list[str]:
    if not values:
        return list(fallback)
    return [Path(value).as_posix() if isinstance(value, Path) else str(value) for value in values]


def _normalize_dependency_report(report: dict[str, Any]) -> dict[str, Any]:
    normalized = {field: str(report.get(field, "")).strip() for field in DEPENDENCY_REPORT_FIELDS}
    if "dependency_key" in report:
        normalized["dependency_key"] = str(report["dependency_key"])
    normalized["complete"] = all(bool(normalized[field]) for field in DEPENDENCY_REPORT_FIELDS)
    return normalized


def build_phase11_goal_checkpoint_contract(
    vault_root: str | Path,
    *,
    surface: str = "Phase 11 Chat / Hermes-Optimus long-running /goal handoff",
    artifacts: list[str | Path] | None = None,
    tests_or_smokes: list[str] | None = None,
    dependency_reports: list[dict[str, Any]] | None = None,
    next_safe_action: str = "Continue bounded Chat/Studio surface work or route missing backend proof to Phase 9-and-below.",
) -> dict[str, Any]:
    """Build a read-only checkpoint template for long-running Phase 11 work."""

    vault = Path(vault_root).resolve()
    reports = dependency_reports if dependency_reports is not None else DEPENDENCY_ROUTING_EXAMPLES
    normalized_reports = [_normalize_dependency_report(report) for report in reports]
    no_write_proof = {field: False for field in NO_WRITE_PROOF_FIELDS}

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": CHECKPOINT_STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "checkpoint": {
            "heading": "## Checkpoint — <UTC timestamp>",
            "surface": surface,
            "artifacts": _as_posix_list(artifacts, DEFAULT_ARTIFACT_PATHS),
            "status": "read-only / approval-gated / blocked-or-verified",
            "tests_or_smokes": tests_or_smokes
            or ["PYTHONPATH=. uvx --with pyyaml pytest runtime/studio/test_phase11_goal_checkpoint_contract.py -q"],
            "authority_posture": "Phase 11 Chat/Studio operator surface only; no backend execution authority granted.",
            "no_write_proof": no_write_proof,
            "dependency_reports": normalized_reports,
            "next_safe_action": next_safe_action,
        },
        "template_markdown": _render_checkpoint_markdown(
            surface=surface,
            artifacts=_as_posix_list(artifacts, DEFAULT_ARTIFACT_PATHS),
            tests_or_smokes=tests_or_smokes
            or ["PYTHONPATH=. uvx --with pyyaml pytest runtime/studio/test_phase11_goal_checkpoint_contract.py -q"],
            no_write_proof=no_write_proof,
            dependency_reports=normalized_reports,
            next_safe_action=next_safe_action,
        ),
        "dependency_report_required_fields": list(DEPENDENCY_REPORT_FIELDS),
        "denied_by_this_surface": [
            "provider_call",
            "browser_launch",
            "agent_bus_task_write",
            "approval_consumption",
            "runtime_dispatch",
            "credential_config_mutation",
            "protected_file_write",
            "canonical_writeback",
        ],
        "authority": {
            "checkpoint_template_only": True,
            "provider_calls_allowed": False,
            "browser_launch_allowed": False,
            "agent_bus_task_write_allowed": False,
            "approval_consumption_allowed": False,
            "runtime_dispatch_allowed": False,
            "credential_config_mutation_allowed": False,
            "protected_file_write_allowed": False,
            "canonical_writeback_allowed": False,
        },
    }


def _render_checkpoint_markdown(
    *,
    surface: str,
    artifacts: list[str],
    tests_or_smokes: list[str],
    no_write_proof: dict[str, bool],
    dependency_reports: list[dict[str, Any]],
    next_safe_action: str,
) -> str:
    proof = "; ".join(f"{field}={str(value).lower()}" for field, value in no_write_proof.items())
    artifact_lines = "\n".join(f"- {path}" for path in artifacts)
    test_lines = "\n".join(f"- {test}" for test in tests_or_smokes)
    dependency_lines = "\n".join(
        f"- {report.get('dependency_key', 'dependency')}: {report['missing_contract']} -> {report['lower_phase_owner_or_surface']}"
        for report in dependency_reports
    )
    return "\n".join(
        [
            "## Checkpoint — <UTC timestamp>",
            f"- Surface: {surface}",
            "- Artifact(s):",
            artifact_lines,
            "- Status: read-only / approval-gated / blocked-or-verified",
            "- Tests or smokes:",
            test_lines,
            f"- No-write proof: {proof}",
            "- Dependency reports:",
            dependency_lines,
            f"- Next safe action: {next_safe_action}",
        ]
    )
