"""Read-only final ChaseOS Pulse product-readiness audit.

This audit reconciles the current bounded Pulse v1 local lane with broader
product-grade gaps. It reports truth; it does not close gaps by mutating memory,
activating schedules, dispatching runtimes, or writing canonical state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from runtime.pulse.approval_center import build_pulse_approval_center_readiness
from runtime.pulse.card_schema import now_utc
from runtime.pulse.connector_source_scanner_readiness import (
    build_pulse_connector_source_scanner_readiness,
)
from runtime.pulse.connector_source_scanner_local_preview import (
    build_pulse_connector_source_scanner_local_preview,
)
from runtime.pulse.connector_source_scanner_candidate_cards import (
    build_pulse_connector_source_scanner_candidate_cards,
)
from runtime.pulse.connector_source_scanner_live_proof import (
    build_pulse_connector_source_scanner_live_proof,
)
from runtime.pulse.connector_source_scanner_live_execution_proof import (
    build_pulse_connector_source_scanner_live_execution_proof,
)
from runtime.pulse.completion_status import build_pulse_completion_status
from runtime.pulse.memory_runtime_readiness import build_pulse_memory_runtime_readiness
from runtime.pulse.native_schedule_activation_gate import build_pulse_native_schedule_activation_gate
from runtime.pulse.native_schedule_run_queue_audit_proof import (
    build_pulse_native_schedule_run_queue_audit_proof,
)
from runtime.pulse.native_schedule_runner_proof import build_pulse_native_schedule_runner_proof
from runtime.pulse.native_schedule_supervised_activation_execution import (
    build_pulse_native_schedule_supervised_activation_execution,
)
from runtime.pulse.personal_map_apply_transaction_proof import (
    build_personal_map_apply_transaction_proof,
)
from runtime.pulse.post_completion_hardening import build_pulse_post_completion_hardening_report
from runtime.pulse.product_shell_browser_qa import (
    latest_pulse_product_shell_browser_qa_note,
    latest_pulse_product_shell_browser_qa_screenshot,
    pulse_product_shell_browser_qa_evidence_built,
    pulse_product_shell_panel_contract_built,
    pulse_product_shell_studio_mount_built,
)
from runtime.studio.runtime_brain_dashboard import build_runtime_brain_dashboard_contract


AUDIT_STATUS_CURRENT_V1_COMPLETE_FULL_PRODUCT_PARTIAL = (
    "current_v1_local_lane_complete_full_product_partial"
)
AUDIT_STATUS_PARTIAL = "partial"
AUDIT_STATUS_FAIL = "fail"
AUDIT_STATUSES = {
    AUDIT_STATUS_CURRENT_V1_COMPLETE_FULL_PRODUCT_PARTIAL,
    AUDIT_STATUS_PARTIAL,
    AUDIT_STATUS_FAIL,
}

CHECK_STATUS_PASS = "pass"
CHECK_STATUS_PARTIAL = "partial"
CHECK_STATUS_MISSING = "missing"
CHECK_STATUS_BLOCKED = "blocked"
CHECK_STATUSES = {
    CHECK_STATUS_PASS,
    CHECK_STATUS_PARTIAL,
    CHECK_STATUS_MISSING,
    CHECK_STATUS_BLOCKED,
}

EXPECTED_PRIOR_PASS_DESCRIPTORS = (
    "chaseos-pulse-signal-driven-deck-enrichment",
    "chaseos-pulse-approval-center-readiness-surface",
    "chaseos-pulse-studio-approval-center-local-mount",
    "chaseos-pulse-memory-runtime-readiness-surface",
    "chaseos-pulse-runtime-brain-dashboard-contract",
)

CURRENT_PASS_DESCRIPTOR = "chaseos-pulse-final-product-readiness-audit"

FULL_PRODUCT_REMAINING_LANES = (
    "interactive_pulse_governed_controls",
    "personal_map_live_apply_proof_and_interactive_ui",
    "visual_runtime_brain_dashboard",
    "approval_queue_ui",
    "native_schedule_runner_activation_and_missed_run_proof",
    "optional_connector_and_source_scanner_expansion",
)

BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_grant",
    "approval_execution",
    "candidate_apply",
    "canonical_writeback",
    "memory_approval",
    "personal_map_mutation",
    "provider_or_connector_call",
    "rd_workbook_update",
    "runtime_brain_update",
    "runtime_dispatch",
    "schedule_activation",
    "second_datastore_write",
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _build_log_exists(vault: Path, descriptor: str) -> bool:
    build_log_dir = vault / "07_LOGS" / "Build-Logs"
    return any(build_log_dir.glob(f"*-ChaseOS-{descriptor}.md"))


def _doc_exists(vault: Path, relative_path: str) -> bool:
    return (vault / relative_path).exists()


def _visual_shell_exists(vault: Path) -> bool:
    return (
        _doc_exists(vault, "runtime/pulse/visual_card_deck_shell.py")
        and _doc_exists(vault, "06_AGENTS/ChaseOS-Pulse-Visual-Card-Deck-Shell.md")
        and bool(list((vault / "07_LOGS" / "Pulse-Decks" / "users").glob("*.visual-shell.html")))
    )


def _product_shell_exists(vault: Path) -> bool:
    return (
        _doc_exists(vault, "runtime/pulse/product_shell.py")
        and _doc_exists(vault, "06_AGENTS/ChaseOS-Pulse-Product-Shell-Integration.md")
        and bool(list((vault / "07_LOGS" / "Pulse-Decks" / "product-shell").glob("*.html")))
    )


def _personal_map_visualization_exists(vault: Path) -> bool:
    return (
        _doc_exists(vault, "runtime/pulse/personal_map_visualization.py")
        and _doc_exists(vault, "06_AGENTS/ChaseOS-Pulse-Personal-Map-Visualization-Contract.md")
        and bool(list((vault / "07_LOGS" / "Pulse-Decks" / "personal-map").glob("*.html")))
    )


def _personal_map_review_apply_exists(vault: Path) -> bool:
    return (
        _doc_exists(vault, "runtime/pulse/personal_map_review_apply.py")
        and _doc_exists(vault, "06_AGENTS/ChaseOS-Pulse-Personal-Map-Review-Apply-Surface.md")
        and bool(
            list(
                (vault / "07_LOGS" / "Pulse-Decks" / "personal-map-review").glob("*.html")
            )
        )
    )


def _personal_map_live_apply_proof_exists(vault: Path) -> bool:
    return (
        _doc_exists(vault, "runtime/pulse/personal_map_live_apply_proof.py")
        and _doc_exists(vault, "06_AGENTS/ChaseOS-Pulse-Personal-Map-Live-Apply-Proof.md")
        and bool(
            list(
                (vault / "07_LOGS" / "Pulse-Decks" / "personal-map-live-apply-proof").glob("*.html")
            )
        )
    )


def _personal_map_apply_transaction_proof_exists(vault: Path) -> bool:
    return (
        _doc_exists(vault, "runtime/pulse/personal_map_apply_transaction_proof.py")
        and _doc_exists(vault, "06_AGENTS/ChaseOS-Pulse-Personal-Map-Apply-Transaction-Proof.md")
        and bool(
            list(
                (vault / "07_LOGS" / "Pulse-Decks" / "personal-map-apply-transactions").glob("*.json")
            )
        )
    )


def _product_grade_local_closeout_exists(vault: Path) -> bool:
    return (
        _doc_exists(vault, "runtime/pulse/product_grade_local_closeout.py")
        and _doc_exists(vault, "06_AGENTS/ChaseOS-Pulse-Product-Grade-Local-V1-Closeout.md")
        and bool(
            list((vault / "07_LOGS" / "Pulse-Decks" / "product-closeout").glob("*.json"))
        )
    )


def _rd_workbook_final_sync_exists(vault: Path) -> bool:
    return (
        _doc_exists(vault, "99_ARCHIVE/Reporting/ChaseOS_RnD_Canonical_Full_2026-04-28.xlsx")
        and _doc_exists(vault, "06_AGENTS/ChaseOS-Pulse-RnD-Workbook-Final-Sync.md")
        and _doc_exists(
            vault,
            "99_ARCHIVE/Reporting/ChaseOS_RnD_Pulse_Product_Closeout_Final_Sync_2026-05-04.md",
        )
    )


def _runtime_brain_visualization_exists(vault: Path) -> bool:
    return (
        _doc_exists(vault, "runtime/pulse/runtime_brain_visualization.py")
        and _doc_exists(vault, "06_AGENTS/ChaseOS-Pulse-Runtime-Brain-Visual-UI.md")
        and bool(list((vault / "07_LOGS" / "Pulse-Decks" / "runtime-brains").glob("*.html")))
    )


def _approval_queue_ui_exists(vault: Path) -> bool:
    return (
        _doc_exists(vault, "runtime/pulse/approval_queue_ui.py")
        and _doc_exists(vault, "06_AGENTS/ChaseOS-Pulse-Approval-Queue-UI.md")
        and bool(list((vault / "07_LOGS" / "Pulse-Decks" / "approval-queue").glob("*.html")))
    )


def _approval_queue_panel_mount_exists(vault: Path) -> bool:
    if not (
        _doc_exists(vault, "runtime/studio/approval_queue_panel.py")
        and _doc_exists(vault, "06_AGENTS/ChaseOS-Pulse-Approval-Queue-Studio-Panel-Mount.md")
        and _doc_exists(vault, "runtime/studio/desktop_shell_app.py")
    ):
        return False
    try:
        from runtime.studio.approval_queue_panel import build_studio_approval_queue_panel_contract
    except Exception:
        return False
    return bool(build_studio_approval_queue_panel_contract(vault).get("ok"))


def _interactive_governed_controls_exists(vault: Path) -> bool:
    if not _doc_exists(vault, "06_AGENTS/ChaseOS-Pulse-Interactive-Governed-Controls.md"):
        return False
    try:
        from runtime.pulse.card_schema import FEEDBACK_TYPES
        from runtime.pulse.local_surface import DEFAULT_FEEDBACK_CANDIDATES
    except Exception:
        return False
    return set(DEFAULT_FEEDBACK_CANDIDATES) == set(FEEDBACK_TYPES)


@dataclass(frozen=True)
class PulseFinalReadinessCheck:
    check_id: str
    status: str
    required_for_current_v1: bool
    required_for_full_product: bool
    evidence: str
    notes: str = ""

    def validate(self) -> None:
        if not self.check_id:
            raise ValueError("final readiness check_id is required")
        if self.status not in CHECK_STATUSES:
            raise ValueError("invalid final readiness check status")
        if not self.evidence:
            raise ValueError("final readiness check evidence is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseFinalProductReadinessAudit:
    generated_at: str
    audit_status: str
    current_v1_local_lane_complete: bool
    full_product_grade_complete: bool
    prior_pass_count: int
    expected_prior_pass_count: int
    checks: tuple[PulseFinalReadinessCheck, ...]
    live_surface_summary: dict[str, Any]
    remaining_full_product_lanes: tuple[str, ...] = FULL_PRODUCT_REMAINING_LANES
    next_recommended_pass: str = "pulse-product-grade-closeout-or-approved-external-evidence"
    no_more_generic_pulse_catchup_passes_required: bool = True
    read_only: bool = True
    local_only: bool = True
    writes_audit_artifact: bool = False
    applies_candidates: bool = False
    mutates_memory: bool = False
    mutates_personal_map: bool = False
    updates_runtime_brains: bool = False
    grants_permissions: bool = False
    agent_bus_task_write_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    approval_execution_allowed: bool = False
    canonical_writeback_allowed: bool = False
    second_datastore_created: bool = False
    rd_workbook_update_allowed: bool = False
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS

    @property
    def check_count(self) -> int:
        return len(self.checks)

    def validate(self) -> None:
        if self.audit_status not in AUDIT_STATUSES:
            raise ValueError("invalid final Pulse audit status")
        for check in self.checks:
            check.validate()
        if self.full_product_grade_complete and self.remaining_full_product_lanes:
            raise ValueError("full product complete cannot have remaining lanes")
        if self.current_v1_local_lane_complete and self.audit_status == AUDIT_STATUS_FAIL:
            raise ValueError("current v1 complete cannot have failed audit status")
        if not self.read_only or not self.local_only:
            raise ValueError("final Pulse audit must remain read-only and local-only")
        if self.writes_audit_artifact:
            raise ValueError("final Pulse audit cannot write audit artifacts")
        if self.applies_candidates:
            raise ValueError("final Pulse audit cannot apply candidates")
        if self.mutates_memory or self.mutates_personal_map:
            raise ValueError("final Pulse audit cannot mutate memory or Personal Map")
        if self.updates_runtime_brains:
            raise ValueError("final Pulse audit cannot update runtime brains")
        if self.grants_permissions:
            raise ValueError("final Pulse audit cannot grant permissions")
        if self.agent_bus_task_write_allowed:
            raise ValueError("final Pulse audit cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed:
            raise ValueError("final Pulse audit cannot dispatch runtimes")
        if self.provider_or_connector_call_allowed:
            raise ValueError("final Pulse audit cannot call providers/connectors")
        if self.schedule_activation_allowed:
            raise ValueError("final Pulse audit cannot activate schedules")
        if self.approval_execution_allowed:
            raise ValueError("final Pulse audit cannot execute approvals")
        if self.canonical_writeback_allowed:
            raise ValueError("final Pulse audit cannot allow canonical writeback")
        if self.second_datastore_created:
            raise ValueError("final Pulse audit cannot create a second datastore")
        if self.rd_workbook_update_allowed:
            raise ValueError("final Pulse audit cannot update the R&D workbook")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("final Pulse audit must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "audit_status": self.audit_status,
            "current_v1_local_lane_complete": self.current_v1_local_lane_complete,
            "full_product_grade_complete": self.full_product_grade_complete,
            "prior_pass_count": self.prior_pass_count,
            "expected_prior_pass_count": self.expected_prior_pass_count,
            "check_count": self.check_count,
            "checks": [check.to_dict() for check in self.checks],
            "live_surface_summary": self.live_surface_summary,
            "remaining_full_product_lanes": list(self.remaining_full_product_lanes),
            "next_recommended_pass": self.next_recommended_pass,
            "no_more_generic_pulse_catchup_passes_required": self.no_more_generic_pulse_catchup_passes_required,
            "read_only": self.read_only,
            "local_only": self.local_only,
            "writes_audit_artifact": self.writes_audit_artifact,
            "applies_candidates": self.applies_candidates,
            "mutates_memory": self.mutates_memory,
            "mutates_personal_map": self.mutates_personal_map,
            "updates_runtime_brains": self.updates_runtime_brains,
            "grants_permissions": self.grants_permissions,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "approval_execution_allowed": self.approval_execution_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "second_datastore_created": self.second_datastore_created,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "blocked_effects": list(self.blocked_effects),
        }


def build_pulse_final_product_readiness_audit(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> PulseFinalProductReadinessAudit:
    """Return a read-only final readiness audit over current Pulse evidence."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()

    completion = build_pulse_completion_status(vault)
    hardening = build_pulse_post_completion_hardening_report(vault)
    approval_center = build_pulse_approval_center_readiness(vault)
    memory_runtime = build_pulse_memory_runtime_readiness(vault)
    connector_source_scanner = build_pulse_connector_source_scanner_readiness(vault)
    connector_source_preview = build_pulse_connector_source_scanner_local_preview(vault)
    connector_source_cards = build_pulse_connector_source_scanner_candidate_cards(vault)
    connector_source_live_proof = build_pulse_connector_source_scanner_live_proof(vault)
    connector_source_live_execution = build_pulse_connector_source_scanner_live_execution_proof(
        vault,
        connector_id="acquisition_rss_live",
    )
    try:
        native_schedule_runner_proof = build_pulse_native_schedule_runner_proof(
            vault,
            simulate_missed_run=True,
        )
        native_schedule_runner_error = ""
    except ValueError as exc:
        native_schedule_runner_proof = None
        native_schedule_runner_error = str(exc)
    try:
        native_schedule_activation_gate = build_pulse_native_schedule_activation_gate(vault)
        native_schedule_activation_gate_error = ""
    except ValueError as exc:
        native_schedule_activation_gate = None
        native_schedule_activation_gate_error = str(exc)
    try:
        native_schedule_run_queue_audit_proof = build_pulse_native_schedule_run_queue_audit_proof(vault)
        native_schedule_run_queue_audit_proof_error = ""
    except ValueError as exc:
        native_schedule_run_queue_audit_proof = None
        native_schedule_run_queue_audit_proof_error = str(exc)
    try:
        native_schedule_supervised_activation_execution = (
            build_pulse_native_schedule_supervised_activation_execution(vault)
        )
        native_schedule_supervised_activation_execution_error = ""
    except ValueError as exc:
        native_schedule_supervised_activation_execution = None
        native_schedule_supervised_activation_execution_error = str(exc)
    runtime_dashboard = build_runtime_brain_dashboard_contract(vault)
    visual_shell_present = _visual_shell_exists(vault)
    product_shell_present = _product_shell_exists(vault)
    product_shell_browser_qa_present = pulse_product_shell_browser_qa_evidence_built(vault)
    product_shell_panel_contract_present = pulse_product_shell_panel_contract_built(vault)
    product_shell_studio_mount_present = pulse_product_shell_studio_mount_built(vault)
    personal_map_visualization_present = _personal_map_visualization_exists(vault)
    personal_map_review_apply_present = _personal_map_review_apply_exists(vault)
    personal_map_live_apply_proof_present = _personal_map_live_apply_proof_exists(vault)
    personal_map_apply_transaction_proof_present = _personal_map_apply_transaction_proof_exists(vault)
    product_grade_local_closeout_present = _product_grade_local_closeout_exists(vault)
    rd_workbook_final_sync_present = _rd_workbook_final_sync_exists(vault)
    personal_map_apply_transaction_proof = build_personal_map_apply_transaction_proof(vault)
    runtime_brain_visualization_present = _runtime_brain_visualization_exists(vault)
    approval_queue_ui_present = _approval_queue_ui_exists(vault)
    approval_queue_panel_mount_present = _approval_queue_panel_mount_exists(vault)
    interactive_governed_controls_present = _interactive_governed_controls_exists(vault)
    remaining_lanes = tuple(
        lane
        for lane in FULL_PRODUCT_REMAINING_LANES
        if not (
            lane == "interactive_pulse_governed_controls"
            and interactive_governed_controls_present
        )
        and not (
            lane == "approval_queue_ui"
            and approval_queue_ui_present
            and approval_queue_panel_mount_present
        )
    )

    prior_pass_count = sum(
        1 for descriptor in EXPECTED_PRIOR_PASS_DESCRIPTORS if _build_log_exists(vault, descriptor)
    )
    prior_passes_complete = prior_pass_count == len(EXPECTED_PRIOR_PASS_DESCRIPTORS)
    current_v1_complete = (
        completion.feature_done
        and completion.backend_control_plane_done
        and hardening.hardening_status == "pass"
        and prior_passes_complete
    )

    checks = (
        PulseFinalReadinessCheck(
            check_id="six_pass_prior_build_logs",
            status=CHECK_STATUS_PASS if prior_passes_complete else CHECK_STATUS_PARTIAL,
            required_for_current_v1=True,
            required_for_full_product=True,
            evidence="07_LOGS/Build-Logs/*-ChaseOS-chaseos-pulse-*.md",
            notes=f"Observed {prior_pass_count}/{len(EXPECTED_PRIOR_PASS_DESCRIPTORS)} prior catch-up pass build logs.",
        ),
        PulseFinalReadinessCheck(
            check_id="completion_status",
            status=CHECK_STATUS_PASS if completion.feature_done else CHECK_STATUS_BLOCKED,
            required_for_current_v1=True,
            required_for_full_product=True,
            evidence="runtime/pulse/completion_status.py",
            notes=f"overall={completion.overall_status}; backend_control_plane_done={completion.backend_control_plane_done}",
        ),
        PulseFinalReadinessCheck(
            check_id="post_completion_hardening",
            status=CHECK_STATUS_PASS if hardening.hardening_status == "pass" else CHECK_STATUS_BLOCKED,
            required_for_current_v1=True,
            required_for_full_product=True,
            evidence="runtime/pulse/post_completion_hardening.py",
            notes=f"required_checks={hardening.passed_required_check_count}/{hardening.required_check_count}",
        ),
        PulseFinalReadinessCheck(
            check_id="approval_center_readiness",
            status=CHECK_STATUS_PASS
            if approval_center.approval_center_status in {"ready_for_operator_review", "no_review_items"}
            else CHECK_STATUS_PARTIAL,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/pulse/approval_center.py",
            notes=f"status={approval_center.approval_center_status}; lanes={approval_center.lane_count}",
        ),
        PulseFinalReadinessCheck(
            check_id="memory_runtime_readiness",
            status=CHECK_STATUS_PASS
            if memory_runtime.readiness_status in {"ready", "partial"}
            else CHECK_STATUS_BLOCKED,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/pulse/memory_runtime_readiness.py",
            notes=f"status={memory_runtime.readiness_status}; runtimes={memory_runtime.runtime_count}",
        ),
        PulseFinalReadinessCheck(
            check_id="runtime_brain_dashboard_contract",
            status=CHECK_STATUS_PASS
            if runtime_dashboard.get("status") in {
                "runtime_brain_dashboard_contract_ready",
                "runtime_brain_dashboard_contract_partial",
            }
            else CHECK_STATUS_BLOCKED,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/studio/runtime_brain_dashboard.py",
            notes=f"status={runtime_dashboard.get('status')}; cards={runtime_dashboard.get('metrics', {}).get('runtime_card_count')}",
        ),
        PulseFinalReadinessCheck(
            check_id="full_visual_product_ui",
            status=CHECK_STATUS_PARTIAL,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="06_AGENTS/ChaseOS-Pulse-Completion-Tracker.md",
            notes=(
                "Integrated static Pulse product shell has browser QA, a Studio panel contract, a read-only Studio shell mount, and first interactive governed controls; candidate review/apply and other full-product lanes remain incomplete."
                if product_shell_present
                and product_shell_browser_qa_present
                and product_shell_panel_contract_present
                and product_shell_studio_mount_present
                and interactive_governed_controls_present
                else "Integrated static Pulse product shell has browser QA, a Studio panel contract, and a read-only Studio shell mount; interactive governed controls remain incomplete."
                if product_shell_present
                and product_shell_browser_qa_present
                and product_shell_panel_contract_present
                and product_shell_studio_mount_present
                else "Integrated static Pulse product shell has browser QA and a Studio panel contract; actual Studio shell mount is not built."
                if product_shell_present
                and product_shell_browser_qa_present
                and product_shell_panel_contract_present
                else "Integrated static Pulse product shell exists; browser QA or Studio panel contract remains incomplete."
                if product_shell_present
                else "First static visual Pulse shell exists; full visual Pulse/Studio product UI is not built."
                if visual_shell_present
                else "Local Pulse app and read-only Studio contracts exist; full visual Pulse/Studio product UI is not built."
            ),
        ),
        PulseFinalReadinessCheck(
            check_id="native_schedule_activation",
            status=CHECK_STATUS_PARTIAL,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/schedules/manifests/chaseos_pulse_daily.yaml",
            notes="Schedule intent, catch-up proof, non-executing runner proof, supervised activation gate, and run-queue/audit proof exist; live schedule runner activation remains separate approval work.",
        ),
        PulseFinalReadinessCheck(
            check_id="native_schedule_runner_proof",
            status=CHECK_STATUS_PARTIAL
            if native_schedule_runner_proof is not None
            and native_schedule_runner_proof.runner_status == "runner_ready_activation_blocked"
            else CHECK_STATUS_MISSING,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/pulse/native_schedule_runner_proof.py",
            notes=(
                f"status={native_schedule_runner_proof.runner_status}; "
                f"schedules={native_schedule_runner_proof.ready_schedule_count}/{native_schedule_runner_proof.schedule_count}; "
                "no daemon start, manifest enablement, run queue write, Agent Bus task write, runtime dispatch, or workflow execution."
                if native_schedule_runner_proof is not None
                else f"runner proof blocked: {native_schedule_runner_error}"
            ),
        ),
        PulseFinalReadinessCheck(
            check_id="native_schedule_activation_gate",
            status=CHECK_STATUS_PARTIAL
            if native_schedule_activation_gate is not None
            and native_schedule_activation_gate.gate_status
            in {"blocked_missing_activation_evidence", "ready_for_operator_supervised_activation"}
            else CHECK_STATUS_MISSING,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/pulse/native_schedule_activation_gate.py",
            notes=(
                f"status={native_schedule_activation_gate.gate_status}; "
                f"missing_evidence={len(native_schedule_activation_gate.missing_evidence_slots)}; "
                "no approval grant, manifest write, daemon start, run queue write, runtime dispatch, workflow execution, or external scheduler ownership."
                if native_schedule_activation_gate is not None
                else f"activation gate blocked: {native_schedule_activation_gate_error}"
            ),
        ),
        PulseFinalReadinessCheck(
            check_id="native_schedule_run_queue_audit_proof",
            status=CHECK_STATUS_PARTIAL
            if native_schedule_run_queue_audit_proof is not None
            and native_schedule_run_queue_audit_proof.proof_status
            in {"blocked_activation_gate_not_ready", "run_queue_audit_proof_ready"}
            else CHECK_STATUS_MISSING,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/pulse/native_schedule_run_queue_audit_proof.py",
            notes=(
                f"status={native_schedule_run_queue_audit_proof.proof_status}; "
                f"proof_queue_entries={native_schedule_run_queue_audit_proof.proof_queue_entry_count}; "
                f"proof_audit_events={native_schedule_run_queue_audit_proof.proof_audit_event_count}; "
                "real run queue writes, real audit writes, dispatch, workflow execution, and schedule activation remain blocked."
                if native_schedule_run_queue_audit_proof is not None
                else f"run queue/audit proof blocked: {native_schedule_run_queue_audit_proof_error}"
            ),
        ),
        PulseFinalReadinessCheck(
            check_id="native_schedule_supervised_activation_execution_proof",
            status=CHECK_STATUS_PARTIAL
            if native_schedule_supervised_activation_execution is not None
            and native_schedule_supervised_activation_execution.execution_status
            in {
                "blocked_activation_gate_not_ready",
                "ready_for_supervised_activation_execution",
            }
            else CHECK_STATUS_MISSING,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/pulse/native_schedule_supervised_activation_execution.py",
            notes=(
                f"status={native_schedule_supervised_activation_execution.execution_status}; "
                f"manifest_patch_count={native_schedule_supervised_activation_execution.manifest_patch_count}; "
                "current repo dry-run has no execution flag and no real approval evidence, so schedule activation remains blocked."
                if native_schedule_supervised_activation_execution is not None
                else f"supervised activation execution proof blocked: {native_schedule_supervised_activation_execution_error}"
            ),
        ),
        PulseFinalReadinessCheck(
            check_id="connector_source_scanner_readiness",
            status=CHECK_STATUS_PARTIAL
            if connector_source_scanner.readiness_status == "contract_ready_live_execution_blocked"
            else CHECK_STATUS_MISSING,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/pulse/connector_source_scanner_readiness.py",
            notes=(
                "Governed connector/source-scanner readiness contract exists, but live connector execution and external source scanning remain blocked."
            ),
        ),
        PulseFinalReadinessCheck(
            check_id="connector_source_scanner_local_preview",
            status=CHECK_STATUS_PASS
            if connector_source_preview.candidate_count > 0
            else CHECK_STATUS_PARTIAL,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/pulse/connector_source_scanner_local_preview.py",
            notes=(
                f"Local metadata-only preview reports {connector_source_preview.candidate_count} candidate(s); "
                "live connector execution and source promotion remain blocked."
            ),
        ),
        PulseFinalReadinessCheck(
            check_id="connector_source_scanner_candidate_cards",
            status=CHECK_STATUS_PASS
            if connector_source_cards.card_count > 0
            else CHECK_STATUS_PARTIAL,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/pulse/connector_source_scanner_candidate_cards.py",
            notes=(
                f"Local metadata-only preview candidates can generate {connector_source_cards.card_count} "
                "governed Pulse card(s); source content reads, live connector execution, approval execution, "
                "and source promotion remain blocked."
            ),
        ),
        PulseFinalReadinessCheck(
            check_id="connector_source_scanner_live_approved_proof",
            status=CHECK_STATUS_PARTIAL
            if connector_source_live_proof.status == "blocked_missing_operator_permission_envelope"
            else CHECK_STATUS_MISSING,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/pulse/connector_source_scanner_live_proof.py",
            notes=(
                "Approval-gated live proof/request contract exists and remains fail-closed; "
                "actual connector execution requires a real operator approval reference and permission envelope."
            ),
        ),
        PulseFinalReadinessCheck(
            check_id="connector_source_scanner_live_execution_proof",
            status=CHECK_STATUS_PARTIAL
            if connector_source_live_execution.execution_status
            in {
                "blocked_missing_operator_permission_envelope",
                "ready_for_live_connector_execution",
                "blocked_missing_live_connector_runner",
            }
            else CHECK_STATUS_MISSING,
            required_for_current_v1=False,
            required_for_full_product=True,
            evidence="runtime/pulse/connector_source_scanner_live_execution_proof.py",
            notes=(
                f"status={connector_source_live_execution.execution_status}; "
                f"connector={connector_source_live_execution.connector_id}; "
                "CLI binds no live connector runner, so current repo execution remains blocked without approval/permission evidence."
            ),
        ),
        PulseFinalReadinessCheck(
            check_id="rd_workbook_state",
            status=CHECK_STATUS_PASS
            if _doc_exists(vault, "99_ARCHIVE/Reporting/ChaseOS_RnD_Canonical_Full_2026-04-28.xlsx")
            else CHECK_STATUS_MISSING,
            required_for_current_v1=True,
            required_for_full_product=True,
            evidence="99_ARCHIVE/Reporting/ChaseOS_RnD_Canonical_Full_2026-04-28.xlsx",
            notes=(
                "Final workbook sync evidence is present; audit remains read-only and does not write workbook rows."
                if rd_workbook_final_sync_present
                else "Audit reads workbook presence only; it does not write or sync workbook rows."
            ),
        ),
    )

    if not current_v1_complete:
        audit_status = AUDIT_STATUS_PARTIAL
        next_pass = "complete-missing-current-v1-pulse-evidence"
    else:
        audit_status = AUDIT_STATUS_CURRENT_V1_COMPLETE_FULL_PRODUCT_PARTIAL
        if product_grade_local_closeout_present and rd_workbook_final_sync_present:
            next_pass = "pulse-explicit-next-feature-lane-selection"
        elif product_grade_local_closeout_present:
            next_pass = "pulse-rd-workbook-final-sync-if-operator-approved"
        else:
            next_pass = "pulse-product-grade-closeout-or-approved-external-evidence"

    return PulseFinalProductReadinessAudit(
        generated_at=generated,
        audit_status=audit_status,
        current_v1_local_lane_complete=current_v1_complete,
        full_product_grade_complete=False,
        prior_pass_count=prior_pass_count,
        expected_prior_pass_count=len(EXPECTED_PRIOR_PASS_DESCRIPTORS),
        checks=checks,
        remaining_full_product_lanes=remaining_lanes,
        live_surface_summary={
            "completion_status": {
                "overall_status": completion.overall_status,
                "feature_done": completion.feature_done,
                "backend_control_plane_done": completion.backend_control_plane_done,
                "next_recommended_pass": completion.next_recommended_pass,
            },
            "post_completion_hardening": {
                "hardening_status": hardening.hardening_status,
                "required_checks": hardening.required_check_count,
                "passed_required_checks": hardening.passed_required_check_count,
            },
            "approval_center": {
                "status": approval_center.approval_center_status,
                "lane_count": approval_center.lane_count,
                "action_count": approval_center.action_count,
            },
            "memory_runtime_readiness": {
                "status": memory_runtime.readiness_status,
                "memory_posture": memory_runtime.memory_posture,
                "runtime_count": memory_runtime.runtime_count,
                "runtime_card_count": memory_runtime.runtime_card_count,
            },
            "runtime_brain_dashboard": {
                "status": runtime_dashboard.get("status"),
                "metrics": runtime_dashboard.get("metrics", {}),
            },
            "native_schedule_runner_proof": {
                "status": native_schedule_runner_proof.runner_status
                if native_schedule_runner_proof is not None
                else "missing",
                "schedule_count": native_schedule_runner_proof.schedule_count
                if native_schedule_runner_proof is not None
                else 0,
                "ready_schedule_count": native_schedule_runner_proof.ready_schedule_count
                if native_schedule_runner_proof is not None
                else 0,
                "enabled_schedule_count": native_schedule_runner_proof.enabled_schedule_count
                if native_schedule_runner_proof is not None
                else 0,
                "simulated_missed_run": native_schedule_runner_proof.simulated_missed_run
                if native_schedule_runner_proof is not None
                else False,
                "schedule_daemon_started": native_schedule_runner_proof.schedule_daemon_started
                if native_schedule_runner_proof is not None
                else False,
                "schedule_manifest_written": native_schedule_runner_proof.schedule_manifest_written
                if native_schedule_runner_proof is not None
                else False,
                "schedule_activation_allowed": native_schedule_runner_proof.schedule_activation_allowed
                if native_schedule_runner_proof is not None
                else False,
                "run_queue_written": native_schedule_runner_proof.run_queue_written
                if native_schedule_runner_proof is not None
                else False,
                "agent_bus_task_write_allowed": native_schedule_runner_proof.agent_bus_task_write_allowed
                if native_schedule_runner_proof is not None
                else False,
                "runtime_dispatch_allowed": native_schedule_runner_proof.runtime_dispatch_allowed
                if native_schedule_runner_proof is not None
                else False,
                "workflow_execution_allowed": native_schedule_runner_proof.workflow_execution_allowed
                if native_schedule_runner_proof is not None
                else False,
                "provider_or_connector_call_allowed": native_schedule_runner_proof.provider_or_connector_call_allowed
                if native_schedule_runner_proof is not None
                else False,
                "canonical_writeback_allowed": native_schedule_runner_proof.canonical_writeback_allowed
                if native_schedule_runner_proof is not None
                else False,
                "error": native_schedule_runner_error or None,
            },
            "native_schedule_activation_gate": {
                "status": native_schedule_activation_gate.gate_status
                if native_schedule_activation_gate is not None
                else "missing",
                "schedule_count": native_schedule_activation_gate.schedule_count
                if native_schedule_activation_gate is not None
                else 0,
                "ready_schedule_count": native_schedule_activation_gate.ready_schedule_count
                if native_schedule_activation_gate is not None
                else 0,
                "enabled_schedule_count": native_schedule_activation_gate.enabled_schedule_count
                if native_schedule_activation_gate is not None
                else 0,
                "missing_evidence_slots": list(native_schedule_activation_gate.missing_evidence_slots)
                if native_schedule_activation_gate is not None
                else [],
                "approval_granted": native_schedule_activation_gate.approval_granted
                if native_schedule_activation_gate is not None
                else False,
                "approval_execution_allowed": native_schedule_activation_gate.approval_execution_allowed
                if native_schedule_activation_gate is not None
                else False,
                "schedule_activation_allowed": native_schedule_activation_gate.schedule_activation_allowed
                if native_schedule_activation_gate is not None
                else False,
                "schedule_manifest_write_allowed": native_schedule_activation_gate.schedule_manifest_write_allowed
                if native_schedule_activation_gate is not None
                else False,
                "schedule_daemon_started": native_schedule_activation_gate.schedule_daemon_started
                if native_schedule_activation_gate is not None
                else False,
                "run_queue_written": native_schedule_activation_gate.run_queue_written
                if native_schedule_activation_gate is not None
                else False,
                "agent_bus_task_write_allowed": native_schedule_activation_gate.agent_bus_task_write_allowed
                if native_schedule_activation_gate is not None
                else False,
                "runtime_dispatch_allowed": native_schedule_activation_gate.runtime_dispatch_allowed
                if native_schedule_activation_gate is not None
                else False,
                "workflow_execution_allowed": native_schedule_activation_gate.workflow_execution_allowed
                if native_schedule_activation_gate is not None
                else False,
                "provider_or_connector_call_allowed": native_schedule_activation_gate.provider_or_connector_call_allowed
                if native_schedule_activation_gate is not None
                else False,
                "external_scheduler_install_allowed": native_schedule_activation_gate.external_scheduler_install_allowed
                if native_schedule_activation_gate is not None
                else False,
                "canonical_writeback_allowed": native_schedule_activation_gate.canonical_writeback_allowed
                if native_schedule_activation_gate is not None
                else False,
                "error": native_schedule_activation_gate_error or None,
            },
            "native_schedule_run_queue_audit_proof": {
                "status": native_schedule_run_queue_audit_proof.proof_status
                if native_schedule_run_queue_audit_proof is not None
                else "missing",
                "schedule_count": native_schedule_run_queue_audit_proof.schedule_count
                if native_schedule_run_queue_audit_proof is not None
                else 0,
                "proof_queue_entry_count": native_schedule_run_queue_audit_proof.proof_queue_entry_count
                if native_schedule_run_queue_audit_proof is not None
                else 0,
                "proof_audit_event_count": native_schedule_run_queue_audit_proof.proof_audit_event_count
                if native_schedule_run_queue_audit_proof is not None
                else 0,
                "missing_evidence_slots": list(native_schedule_run_queue_audit_proof.missing_evidence_slots)
                if native_schedule_run_queue_audit_proof is not None
                else [],
                "real_run_queue_written": native_schedule_run_queue_audit_proof.real_run_queue_written
                if native_schedule_run_queue_audit_proof is not None
                else False,
                "real_audit_event_written": native_schedule_run_queue_audit_proof.real_audit_event_written
                if native_schedule_run_queue_audit_proof is not None
                else False,
                "schedule_activation_allowed": native_schedule_run_queue_audit_proof.schedule_activation_allowed
                if native_schedule_run_queue_audit_proof is not None
                else False,
                "schedule_manifest_write_allowed": native_schedule_run_queue_audit_proof.schedule_manifest_write_allowed
                if native_schedule_run_queue_audit_proof is not None
                else False,
                "schedule_daemon_started": native_schedule_run_queue_audit_proof.schedule_daemon_started
                if native_schedule_run_queue_audit_proof is not None
                else False,
                "agent_bus_task_write_allowed": native_schedule_run_queue_audit_proof.agent_bus_task_write_allowed
                if native_schedule_run_queue_audit_proof is not None
                else False,
                "runtime_dispatch_allowed": native_schedule_run_queue_audit_proof.runtime_dispatch_allowed
                if native_schedule_run_queue_audit_proof is not None
                else False,
                "workflow_execution_allowed": native_schedule_run_queue_audit_proof.workflow_execution_allowed
                if native_schedule_run_queue_audit_proof is not None
                else False,
                "approval_execution_allowed": native_schedule_run_queue_audit_proof.approval_execution_allowed
                if native_schedule_run_queue_audit_proof is not None
                else False,
                "provider_or_connector_call_allowed": native_schedule_run_queue_audit_proof.provider_or_connector_call_allowed
                if native_schedule_run_queue_audit_proof is not None
                else False,
                "external_scheduler_install_allowed": native_schedule_run_queue_audit_proof.external_scheduler_install_allowed
                if native_schedule_run_queue_audit_proof is not None
                else False,
                "canonical_writeback_allowed": native_schedule_run_queue_audit_proof.canonical_writeback_allowed
                if native_schedule_run_queue_audit_proof is not None
                else False,
                "error": native_schedule_run_queue_audit_proof_error or None,
            },
            "native_schedule_supervised_activation_execution": {
                "status": native_schedule_supervised_activation_execution.execution_status
                if native_schedule_supervised_activation_execution is not None
                else "missing",
                "schedule_count": native_schedule_supervised_activation_execution.schedule_count
                if native_schedule_supervised_activation_execution is not None
                else 0,
                "missing_evidence_slots": list(
                    native_schedule_supervised_activation_execution.missing_evidence_slots
                )
                if native_schedule_supervised_activation_execution is not None
                else [],
                "execute_requested": native_schedule_supervised_activation_execution.execute_requested
                if native_schedule_supervised_activation_execution is not None
                else False,
                "write_executed": native_schedule_supervised_activation_execution.write_executed
                if native_schedule_supervised_activation_execution is not None
                else False,
                "manifest_patch_count": native_schedule_supervised_activation_execution.manifest_patch_count
                if native_schedule_supervised_activation_execution is not None
                else 0,
                "schedule_manifest_write_executed": native_schedule_supervised_activation_execution.schedule_manifest_write_executed
                if native_schedule_supervised_activation_execution is not None
                else False,
                "schedule_activation_executed": native_schedule_supervised_activation_execution.schedule_activation_executed
                if native_schedule_supervised_activation_execution is not None
                else False,
                "schedule_daemon_started": native_schedule_supervised_activation_execution.schedule_daemon_started
                if native_schedule_supervised_activation_execution is not None
                else False,
                "real_run_queue_written": native_schedule_supervised_activation_execution.real_run_queue_written
                if native_schedule_supervised_activation_execution is not None
                else False,
                "real_audit_event_written": native_schedule_supervised_activation_execution.real_audit_event_written
                if native_schedule_supervised_activation_execution is not None
                else False,
                "agent_bus_task_write_allowed": native_schedule_supervised_activation_execution.agent_bus_task_write_allowed
                if native_schedule_supervised_activation_execution is not None
                else False,
                "runtime_dispatch_allowed": native_schedule_supervised_activation_execution.runtime_dispatch_allowed
                if native_schedule_supervised_activation_execution is not None
                else False,
                "workflow_execution_allowed": native_schedule_supervised_activation_execution.workflow_execution_allowed
                if native_schedule_supervised_activation_execution is not None
                else False,
                "provider_or_connector_call_allowed": native_schedule_supervised_activation_execution.provider_or_connector_call_allowed
                if native_schedule_supervised_activation_execution is not None
                else False,
                "external_scheduler_install_allowed": native_schedule_supervised_activation_execution.external_scheduler_install_allowed
                if native_schedule_supervised_activation_execution is not None
                else False,
                "canonical_writeback_allowed": native_schedule_supervised_activation_execution.canonical_writeback_allowed
                if native_schedule_supervised_activation_execution is not None
                else False,
                "error": native_schedule_supervised_activation_execution_error or None,
            },
            "connector_source_scanner_readiness": {
                "status": connector_source_scanner.readiness_status,
                "source_surface_count": connector_source_scanner.source_surface_count,
                "ready_source_surface_count": connector_source_scanner.ready_source_surface_count,
                "connector_count": connector_source_scanner.connector_count,
                "external_connector_count": connector_source_scanner.external_connector_count,
                "live_enabled_connector_count": connector_source_scanner.live_enabled_connector_count,
                "provider_or_connector_call_allowed": connector_source_scanner.provider_or_connector_call_allowed,
                "unrestricted_web_scan_allowed": connector_source_scanner.unrestricted_web_scan_allowed,
                "browser_history_ingest_allowed": connector_source_scanner.browser_history_ingest_allowed,
            },
            "connector_source_scanner_local_preview": {
                "status": connector_source_preview.preview_status,
                "candidate_count": connector_source_preview.candidate_count,
                "scanned_surface_count": connector_source_preview.scanned_surface_count,
                "source_surface_count": connector_source_preview.source_surface_count,
                "source_content_read": connector_source_preview.source_content_read,
                "provider_or_connector_call_allowed": connector_source_preview.provider_or_connector_call_allowed,
                "unrestricted_web_scan_allowed": connector_source_preview.unrestricted_web_scan_allowed,
                "canonical_writeback_allowed": connector_source_preview.canonical_writeback_allowed,
            },
            "connector_source_scanner_candidate_cards": {
                "status": connector_source_cards.status,
                "preview_candidate_count": connector_source_cards.preview_candidate_count,
                "card_count": connector_source_cards.card_count,
                "deck_count": connector_source_cards.deck_count,
                "source_content_read": connector_source_cards.source_content_read,
                "provider_or_connector_call_allowed": connector_source_cards.provider_or_connector_call_allowed,
                "unrestricted_web_scan_allowed": connector_source_cards.unrestricted_web_scan_allowed,
                "source_promotion_allowed": connector_source_cards.source_promotion_allowed,
                "canonical_writeback_allowed": connector_source_cards.canonical_writeback_allowed,
            },
            "connector_source_scanner_live_approved_proof": {
                "status": connector_source_live_proof.status,
                "connector_id": connector_source_live_proof.connector_id,
                "target_count": connector_source_live_proof.target_count,
                "external_connector_count": connector_source_live_proof.external_connector_count,
                "live_enabled_connector_count": connector_source_live_proof.live_enabled_connector_count,
                "write_executed": connector_source_live_proof.write_executed,
                "approval_granted": connector_source_live_proof.approval_granted,
                "approval_execution_allowed": connector_source_live_proof.approval_execution_allowed,
                "source_content_read": connector_source_live_proof.source_content_read,
                "provider_or_connector_call_allowed": connector_source_live_proof.provider_or_connector_call_allowed,
                "source_promotion_allowed": connector_source_live_proof.source_promotion_allowed,
                "canonical_writeback_allowed": connector_source_live_proof.canonical_writeback_allowed,
            },
            "connector_source_scanner_live_execution_proof": {
                "status": connector_source_live_execution.execution_status,
                "connector_id": connector_source_live_execution.connector_id,
                "target_count": connector_source_live_execution.target_count,
                "missing_evidence_slots": list(connector_source_live_execution.missing_evidence_slots),
                "execute_requested": connector_source_live_execution.execute_requested,
                "write_executed": connector_source_live_execution.write_executed,
                "connector_runner_bound": connector_source_live_execution.connector_runner_bound,
                "live_connector_execution_executed": connector_source_live_execution.live_connector_execution_executed,
                "provider_or_connector_call_executed": connector_source_live_execution.provider_or_connector_call_executed,
                "source_content_read": connector_source_live_execution.source_content_read,
                "unrestricted_web_scan_allowed": connector_source_live_execution.unrestricted_web_scan_allowed,
                "browser_history_ingest_allowed": connector_source_live_execution.browser_history_ingest_allowed,
                "credential_or_secret_read_allowed": connector_source_live_execution.credential_or_secret_read_allowed,
                "schedule_activation_allowed": connector_source_live_execution.schedule_activation_allowed,
                "agent_bus_task_write_allowed": connector_source_live_execution.agent_bus_task_write_allowed,
                "approval_granted": connector_source_live_execution.approval_granted,
                "approval_execution_allowed": connector_source_live_execution.approval_execution_allowed,
                "source_promotion_allowed": connector_source_live_execution.source_promotion_allowed,
                "canonical_writeback_allowed": connector_source_live_execution.canonical_writeback_allowed,
            },
            "visual_card_deck_shell": {
                "status": "first_static_shell_present" if visual_shell_present else "not_present",
                "artifact_present": visual_shell_present,
                "writes_html_only_when_explicit": True,
                "full_visual_product_ui_complete": False,
            },
            "pulse_product_shell": {
                "status": (
                    "studio_read_only_mount_present"
                    if product_shell_present
                    and product_shell_browser_qa_present
                    and product_shell_panel_contract_present
                    and product_shell_studio_mount_present
                    else "browser_qa_and_panel_contract_present"
                    if product_shell_present and product_shell_browser_qa_present and product_shell_panel_contract_present
                    else "first_integrated_static_shell_present"
                    if product_shell_present
                    else "not_present"
                ),
                "artifact_present": product_shell_present,
                "browser_qa_present": product_shell_browser_qa_present,
                "browser_qa_note": (
                    str(latest_pulse_product_shell_browser_qa_note(vault).relative_to(vault).as_posix())
                    if latest_pulse_product_shell_browser_qa_note(vault)
                    else None
                ),
                "browser_qa_screenshot": (
                    str(latest_pulse_product_shell_browser_qa_screenshot(vault).relative_to(vault).as_posix())
                    if latest_pulse_product_shell_browser_qa_screenshot(vault)
                    else None
                ),
                "studio_panel_contract_present": product_shell_panel_contract_present,
                "studio_read_only_mount_present": product_shell_studio_mount_present,
                "interactive_governed_controls_present": interactive_governed_controls_present,
                "writes_html_only_when_explicit": True,
                "starts_server": False,
                "opens_browser": False,
                "executes_actions": False,
                "full_studio_shell_mount_complete": product_shell_studio_mount_present,
                "interactive_governed_controls_complete": interactive_governed_controls_present,
            },
            "personal_map_visualization": {
                "status": "first_contract_present" if personal_map_visualization_present else "not_present",
                "artifact_present": personal_map_visualization_present,
                "writes_html_only_when_explicit": True,
                "applies_personal_map_candidates": False,
                "full_personal_map_visualization_complete": False,
            },
            "personal_map_review_apply": {
                "status": "first_static_surface_present" if personal_map_review_apply_present else "not_present",
                "artifact_present": personal_map_review_apply_present,
                "writes_html_only_when_explicit": True,
                "surface_runs_live_apply": False,
                "applies_personal_map_candidates": False,
                "writes_runtime_memory_graph": False,
                "full_personal_map_product_ui_complete": False,
            },
            "personal_map_live_apply_proof": {
                "status": "first_static_proof_present" if personal_map_live_apply_proof_present else "not_present",
                "artifact_present": personal_map_live_apply_proof_present,
                "writes_html_only_when_explicit": True,
                "surface_runs_live_apply": False,
                "applies_personal_map_candidates": False,
                "writes_runtime_memory_graph": False,
                "full_personal_map_product_ui_complete": False,
            },
            "personal_map_apply_transaction_proof": {
                "status": (
                    "proof_artifact_present"
                    if personal_map_apply_transaction_proof_present
                    else personal_map_apply_transaction_proof.transaction_status
                ),
                "artifact_present": personal_map_apply_transaction_proof_present,
                "ready_candidate_count": personal_map_apply_transaction_proof.ready_candidate_count,
                "transaction_entry_count": personal_map_apply_transaction_proof.transaction_entry_count,
                "graph_present_before": personal_map_apply_transaction_proof.graph_present_before,
                "live_apply_allowed": personal_map_apply_transaction_proof.live_apply_allowed,
                "applies_personal_map_candidates": personal_map_apply_transaction_proof.applies_personal_map_candidates,
                "writes_runtime_memory_graph": personal_map_apply_transaction_proof.writes_runtime_memory_graph,
                "canonical_writeback_allowed": personal_map_apply_transaction_proof.canonical_writeback_allowed,
                "full_personal_map_product_ui_complete": False,
            },
            "product_grade_local_closeout": {
                "status": (
                    "local_v1_product_grade_ready_external_lanes_deferred"
                    if product_grade_local_closeout_present
                    else "not_present"
                ),
                "artifact_present": product_grade_local_closeout_present,
                "local_v1_product_grade_ready": product_grade_local_closeout_present,
                "full_product_grade_complete": False,
                "deferred_external_lanes": [
                    "live_connector_source_scanner_execution",
                    "live_native_schedule_activation",
                    "approval_execution_apply_flow",
                    "live_personal_map_apply_with_real_candidates",
                    "runtime_brain_mutation_or_self_upgrade",
                ],
                "rd_workbook_final_sync_complete": rd_workbook_final_sync_present,
                "provider_or_connector_call_allowed": False,
                "schedule_activation_allowed": False,
                "approval_execution_allowed": False,
                "canonical_writeback_allowed": False,
                "rd_workbook_update_allowed": False,
            },
            "runtime_brain_visualization": {
                "status": "first_static_ui_present" if runtime_brain_visualization_present else "not_present",
                "artifact_present": runtime_brain_visualization_present,
                "writes_html_only_when_explicit": True,
                "updates_runtime_brains": False,
                "applies_execution_repair_memory": False,
                "grants_permissions": False,
                "full_runtime_brain_visual_ui_complete": False,
            },
            "approval_queue_ui": {
                "status": (
                    "studio_read_only_mount_present"
                    if approval_queue_ui_present and approval_queue_panel_mount_present
                    else "first_static_ui_present"
                    if approval_queue_ui_present
                    else "not_present"
                ),
                "artifact_present": approval_queue_ui_present,
                "studio_panel_mount_present": approval_queue_panel_mount_present,
                "writes_html_only_when_explicit": True,
                "grants_approvals": False,
                "executes_approval": False,
                "applies_candidates": False,
                "agent_bus_task_write_allowed": False,
                "full_approval_queue_ui_complete": approval_queue_ui_present and approval_queue_panel_mount_present,
            },
            "parallel_runtime_evidence": {
                "hermes_pulse_logs_present": bool(
                    list((vault / "07_LOGS" / "Build-Logs").glob("*hermes*Pulse*.md"))
                    or list((vault / "07_LOGS" / "Build-Logs").glob("*hermes*pulse*.md"))
                ),
                "openclaw_runtime_memory_present": _doc_exists(
                    vault,
                    "runtime/memory/adapters/openclaw/profile.json",
                ),
            },
        },
        next_recommended_pass=next_pass,
    )
