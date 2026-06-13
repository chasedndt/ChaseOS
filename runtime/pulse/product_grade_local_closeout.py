"""Read-only/log-only ChaseOS Pulse local product-grade closeout.

The closeout reconciles the local Pulse v1 lane after the final readiness audit.
It can write a closeout artifact under Pulse logs when explicitly requested, but
it does not grant approvals, execute connectors, activate schedules, apply
candidates, mutate memory, or update the R&D workbook.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc
from runtime.pulse.completion_status import build_pulse_completion_status
from runtime.pulse.final_product_readiness_audit import (
    BLOCKED_EFFECTS,
    build_pulse_final_product_readiness_audit,
)
from runtime.pulse.post_completion_hardening import (
    build_pulse_post_completion_hardening_report,
)


STATUS_LOCAL_V1_READY = "local_v1_product_grade_ready_external_lanes_deferred"
STATUS_BLOCKED = "blocked_current_v1_not_complete"
STATUSES = {STATUS_LOCAL_V1_READY, STATUS_BLOCKED}

CLOSEOUT_ARTIFACT_ROOT = Path("07_LOGS/Pulse-Decks/product-closeout")

EXTERNAL_LANES = (
    "live_connector_source_scanner_execution",
    "live_native_schedule_activation",
    "approval_execution_apply_flow",
    "live_personal_map_apply_with_real_candidates",
    "runtime_brain_mutation_or_self_upgrade",
)

LOCAL_PRODUCT_SURFACES = (
    "multi_audience_decks",
    "signal_driven_decks",
    "feedback_candidate_review_apply_proof",
    "hermes_review_handoff_proof",
    "post_apply_truth_state_audit",
    "static_visual_card_deck_shell",
    "integrated_product_shell",
    "product_shell_browser_qa",
    "studio_pulse_panel_mount",
    "approval_queue_static_ui_and_panel",
    "personal_map_visualization_and_apply_proof_surfaces",
    "runtime_brain_static_visual_ui",
    "native_schedule_proof_surfaces",
    "connector_source_scanner_proof_surfaces",
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(path: Path, vault: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return path.as_posix()


def _default_closeout_path(vault: Path) -> Path:
    return vault / CLOSEOUT_ARTIFACT_ROOT / "2026-05-04-pulse-product-grade-local-v1-closeout.json"


def _rd_workbook_final_sync_exists(vault: Path) -> bool:
    return (
        (vault / "99_ARCHIVE" / "Reporting" / "ChaseOS_RnD_Canonical_Full_2026-04-28.xlsx").exists()
        and (vault / "06_AGENTS" / "ChaseOS-Pulse-RnD-Workbook-Final-Sync.md").exists()
        and (
            vault
            / "99_ARCHIVE"
            / "Reporting"
            / "ChaseOS_RnD_Pulse_Product_Closeout_Final_Sync_2026-05-04.md"
        ).exists()
    )


def _resolve_output_path(vault: Path, output_path: str | Path | None) -> Path:
    target = Path(output_path) if output_path else _default_closeout_path(vault)
    if not target.is_absolute():
        target = vault / target
    target = target.resolve()
    allowed_root = (vault / CLOSEOUT_ARTIFACT_ROOT).resolve()
    if target != allowed_root and allowed_root not in target.parents:
        raise ValueError(
            "Pulse product closeout artifacts may only be written under "
            f"{CLOSEOUT_ARTIFACT_ROOT.as_posix()}"
        )
    return target


@dataclass(frozen=True)
class PulseProductGradeDeferredLane:
    lane_id: str
    status: str
    evidence: str
    required_to_unblock: tuple[str, ...]
    notes: str = ""

    def validate(self) -> None:
        if not self.lane_id:
            raise ValueError("deferred lane_id is required")
        if self.status != "deferred_requires_explicit_approval_or_evidence":
            raise ValueError("deferred lane status must be explicit")
        if not self.evidence:
            raise ValueError("deferred lane evidence is required")
        if not self.required_to_unblock:
            raise ValueError("deferred lane requires unblock criteria")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseProductGradeLocalCloseout:
    generated_at: str
    closeout_status: str
    local_v1_product_grade_ready: bool
    current_v1_local_lane_complete: bool
    full_product_grade_complete: bool
    closeout_artifact_written: bool
    closeout_artifact_path: str | None
    local_product_surfaces: tuple[str, ...]
    deferred_external_lanes: tuple[PulseProductGradeDeferredLane, ...]
    evidence: dict[str, Any]
    next_recommended_pass: str
    read_only: bool = True
    local_only: bool = True
    writes_audit_artifact: bool = False
    applies_candidates: bool = False
    mutates_memory: bool = False
    mutates_personal_map: bool = False
    updates_runtime_brains: bool = False
    grants_permissions: bool = False
    approval_execution_allowed: bool = False
    agent_bus_task_write_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    schedule_activation_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    source_content_read: bool = False
    unrestricted_web_scan_allowed: bool = False
    browser_history_ingest_allowed: bool = False
    canonical_writeback_allowed: bool = False
    second_datastore_created: bool = False
    rd_workbook_update_allowed: bool = False
    mutates_canonical_state: bool = False
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS

    @property
    def deferred_lane_count(self) -> int:
        return len(self.deferred_external_lanes)

    def validate(self) -> None:
        if self.closeout_status not in STATUSES:
            raise ValueError("invalid Pulse local closeout status")
        if self.local_v1_product_grade_ready and self.closeout_status != STATUS_LOCAL_V1_READY:
            raise ValueError("ready local closeout requires ready status")
        if self.local_v1_product_grade_ready and not self.current_v1_local_lane_complete:
            raise ValueError("ready local closeout requires current v1 completion")
        if self.full_product_grade_complete:
            raise ValueError("this closeout cannot claim full product-grade completion")
        if not self.next_recommended_pass:
            raise ValueError("next_recommended_pass is required")
        if not self.local_product_surfaces:
            raise ValueError("local_product_surfaces are required")
        for lane in self.deferred_external_lanes:
            lane.validate()
        if not self.read_only:
            raise ValueError("closeout must remain read-only")
        if not self.local_only:
            raise ValueError("closeout must remain local-only")
        if self.applies_candidates:
            raise ValueError("closeout cannot apply candidates")
        if self.mutates_memory:
            raise ValueError("closeout cannot mutate memory")
        if self.mutates_personal_map:
            raise ValueError("closeout cannot mutate Personal Map")
        if self.updates_runtime_brains:
            raise ValueError("closeout cannot update runtime brains")
        if self.grants_permissions or self.approval_execution_allowed:
            raise ValueError("closeout cannot grant or execute approvals")
        if self.agent_bus_task_write_allowed:
            raise ValueError("closeout cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed:
            raise ValueError("closeout cannot dispatch runtimes")
        if self.schedule_activation_allowed:
            raise ValueError("closeout cannot activate schedules")
        if self.provider_or_connector_call_allowed:
            raise ValueError("closeout cannot call providers or connectors")
        if self.source_content_read:
            raise ValueError("closeout cannot read source content")
        if self.unrestricted_web_scan_allowed or self.browser_history_ingest_allowed:
            raise ValueError("closeout cannot scan unrestricted web or browser history")
        if self.canonical_writeback_allowed or self.mutates_canonical_state:
            raise ValueError("closeout cannot write canonical state")
        if self.second_datastore_created:
            raise ValueError("closeout cannot create a second datastore")
        if self.rd_workbook_update_allowed:
            raise ValueError("closeout cannot update the R&D workbook")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("closeout must preserve final audit blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "closeout_status": self.closeout_status,
            "local_v1_product_grade_ready": self.local_v1_product_grade_ready,
            "current_v1_local_lane_complete": self.current_v1_local_lane_complete,
            "full_product_grade_complete": self.full_product_grade_complete,
            "closeout_artifact_written": self.closeout_artifact_written,
            "closeout_artifact_path": self.closeout_artifact_path,
            "local_product_surfaces": list(self.local_product_surfaces),
            "deferred_lane_count": self.deferred_lane_count,
            "deferred_external_lanes": [
                lane.to_dict() for lane in self.deferred_external_lanes
            ],
            "evidence": self.evidence,
            "next_recommended_pass": self.next_recommended_pass,
            "read_only": self.read_only,
            "local_only": self.local_only,
            "writes_audit_artifact": self.writes_audit_artifact,
            "applies_candidates": self.applies_candidates,
            "mutates_memory": self.mutates_memory,
            "mutates_personal_map": self.mutates_personal_map,
            "updates_runtime_brains": self.updates_runtime_brains,
            "grants_permissions": self.grants_permissions,
            "approval_execution_allowed": self.approval_execution_allowed,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "source_content_read": self.source_content_read,
            "unrestricted_web_scan_allowed": self.unrestricted_web_scan_allowed,
            "browser_history_ingest_allowed": self.browser_history_ingest_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "second_datastore_created": self.second_datastore_created,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "blocked_effects": list(self.blocked_effects),
        }


def _build_deferred_lanes(
    *,
    rd_workbook_final_sync_complete: bool = False,
) -> tuple[PulseProductGradeDeferredLane, ...]:
    lanes = [
        PulseProductGradeDeferredLane(
            lane_id="live_connector_source_scanner_execution",
            status="deferred_requires_explicit_approval_or_evidence",
            evidence="runtime/pulse/connector_source_scanner_live_execution_proof.py",
            required_to_unblock=(
                "operator_approval_ref",
                "permission_envelope_ref",
                "connector_scope_ref",
                "source_class_scope_ref",
                "denylist_ack_ref",
                "output_write_scope_ref",
                "bounded_connector_runner",
            ),
            notes="Current CLI binds no live connector runner and current repo has no execution approval.",
        ),
        PulseProductGradeDeferredLane(
            lane_id="live_native_schedule_activation",
            status="deferred_requires_explicit_approval_or_evidence",
            evidence="runtime/pulse/native_schedule_supervised_activation_execution.py",
            required_to_unblock=(
                "operator_approval_ref",
                "permission_envelope_ref",
                "run_queue_scope_ref",
                "audit_identity_ref",
                "runtime_adapter_scope_ref",
                "rollback_plan_ref",
                "external_scheduler_denial_ref",
                "canonical_writeback_denial_ref",
            ),
            notes="Current Pulse schedule manifests remain inactive.",
        ),
        PulseProductGradeDeferredLane(
            lane_id="approval_execution_apply_flow",
            status="deferred_requires_explicit_approval_or_evidence",
            evidence="06_AGENTS/ChaseOS-Pulse-Final-Product-Readiness-Audit.md",
            required_to_unblock=(
                "operator_approved_apply_scope",
                "idempotency_policy",
                "review_decision_evidence",
                "rollback_or_reversal_policy",
            ),
        ),
        PulseProductGradeDeferredLane(
            lane_id="live_personal_map_apply_with_real_candidates",
            status="deferred_requires_explicit_approval_or_evidence",
            evidence="runtime/pulse/personal_map_apply_transaction_proof.py",
            required_to_unblock=(
                "ready_personal_map_candidates",
                "operator_review_decisions",
                "runtime_memory_write_scope",
                "idempotency_key",
            ),
            notes="Current repo proof has zero ready Personal Map candidates.",
        ),
        PulseProductGradeDeferredLane(
            lane_id="runtime_brain_mutation_or_self_upgrade",
            status="deferred_requires_explicit_approval_or_evidence",
            evidence="runtime/studio/runtime_brain_dashboard.py",
            required_to_unblock=(
                "runtime_brain_write_policy",
                "operator_approval_ref",
                "drift_review_policy",
                "rollback_policy",
            ),
        ),
    ]
    if not rd_workbook_final_sync_complete:
        lanes.append(
            PulseProductGradeDeferredLane(
            lane_id="rd_workbook_final_update",
            status="deferred_requires_explicit_approval_or_evidence",
            evidence="99_ARCHIVE/Reporting/ChaseOS_RnD_Canonical_Full_2026-04-28.xlsx",
            required_to_unblock=(
                "operator_workbook_update_instruction",
                "final_row_mapping",
                "post_write_workbook_validation",
            ),
            notes="This pass can stage closeout truth but does not write the workbook.",
            )
        )
    return tuple(lanes)


def build_pulse_product_grade_local_closeout(
    vault_root: str | Path = ".",
    *,
    generated_at: str | None = None,
    write_closeout: bool = False,
    output_path: str | Path | None = None,
) -> PulseProductGradeLocalCloseout:
    vault = _vault_path(vault_root)
    completion = build_pulse_completion_status(vault)
    hardening = build_pulse_post_completion_hardening_report(vault)
    audit = build_pulse_final_product_readiness_audit(vault)
    rd_workbook_final_sync_complete = _rd_workbook_final_sync_exists(vault)

    current_ready = (
        completion.feature_done
        and completion.backend_control_plane_done
        and hardening.hardening_status == "pass"
        and audit.current_v1_local_lane_complete
    )
    status = STATUS_LOCAL_V1_READY if current_ready else STATUS_BLOCKED
    artifact_path: Path | None = None
    if write_closeout:
        artifact_path = _resolve_output_path(vault, output_path)

    closeout = PulseProductGradeLocalCloseout(
        generated_at=generated_at or now_utc(),
        closeout_status=status,
        local_v1_product_grade_ready=current_ready,
        current_v1_local_lane_complete=audit.current_v1_local_lane_complete,
        full_product_grade_complete=False,
        closeout_artifact_written=False,
        closeout_artifact_path=_relative_to_vault(artifact_path, vault) if artifact_path else None,
        local_product_surfaces=LOCAL_PRODUCT_SURFACES,
        deferred_external_lanes=_build_deferred_lanes(
            rd_workbook_final_sync_complete=rd_workbook_final_sync_complete,
        ),
        evidence={
            "completion_status": completion.overall_status,
            "backend_control_plane_done": completion.backend_control_plane_done,
            "post_completion_hardening": hardening.hardening_status,
            "final_audit_status": audit.audit_status,
            "final_audit_current_v1_local_lane_complete": audit.current_v1_local_lane_complete,
            "final_audit_full_product_grade_complete": audit.full_product_grade_complete,
            "final_audit_next_recommended_pass": audit.next_recommended_pass,
            "rd_workbook_final_sync_complete": rd_workbook_final_sync_complete,
            "rd_workbook_final_sync_doc": (
                "06_AGENTS/ChaseOS-Pulse-RnD-Workbook-Final-Sync.md"
                if rd_workbook_final_sync_complete
                else None
            ),
        },
        next_recommended_pass=(
            "pulse-explicit-next-feature-lane-selection"
            if current_ready and rd_workbook_final_sync_complete
            else "pulse-rd-workbook-final-sync-if-operator-approved"
            if current_ready
            else "pulse-product-grade-gap-repair"
        ),
        writes_audit_artifact=write_closeout,
    )
    closeout.validate()

    if write_closeout and artifact_path:
        payload = closeout.to_dict()
        payload["closeout_artifact_written"] = True
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
        closeout = PulseProductGradeLocalCloseout(
            **{
                **closeout.__dict__,
                "closeout_artifact_written": True,
            }
        )
        closeout.validate()
    return closeout
