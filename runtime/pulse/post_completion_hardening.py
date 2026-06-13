"""Read-only ChaseOS Pulse post-completion hardening report.

This module verifies that the completed Pulse lane still stays inside the
authority envelope claimed by the repo evidence. It does not write artifacts,
enqueue Agent Bus work, activate schedules, approve memory, call providers, or
update the R&D workbook.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc
from runtime.pulse.completion_status import (
    PULSE_COMPLETION_BLOCKED_EFFECTS,
    PULSE_COMPLETION_OVERALL_COMPLETE,
    build_pulse_completion_status,
)
from runtime.pulse.multi_audience_decks import build_pulse_deck_inventory
from runtime.studio.app_launcher import build_studio_app_launcher_plan


HARDENING_STATUS_PASS = "pass"
HARDENING_STATUS_PARTIAL = "partial"
HARDENING_STATUS_FAIL = "fail"
HARDENING_STATUSES = {
    HARDENING_STATUS_PASS,
    HARDENING_STATUS_PARTIAL,
    HARDENING_STATUS_FAIL,
}

CHECK_STATUS_PASS = "pass"
CHECK_STATUS_WARN = "warn"
CHECK_STATUS_FAIL = "fail"
CHECK_STATUS_NOT_APPLICABLE = "not_applicable"
CHECK_STATUSES = {
    CHECK_STATUS_PASS,
    CHECK_STATUS_WARN,
    CHECK_STATUS_FAIL,
    CHECK_STATUS_NOT_APPLICABLE,
}

REQUIRED_PROOF_DOCS = (
    "06_AGENTS/ChaseOS-Pulse-Post-Apply-Truth-State-Audit.md",
    "06_AGENTS/ChaseOS-Pulse-RnD-Workbook-Update-Approval.md",
    "06_AGENTS/ChaseOS-Pulse-Native-Schedule-Activation-Catchup-Proof.md",
    "06_AGENTS/ChaseOS-Pulse-Phase10-UI-Proof.md",
)

DAILY_PULSE_MANIFEST_PATH = "runtime/schedules/manifests/chaseos_pulse_daily.yaml"
HERMES_PULSE_MANIFEST_PATH = "runtime/schedules/manifests/hermes_runtime_pulse.yaml"
OPENFLOW_PULSE_MANIFEST_PATH = "runtime/schedules/manifests/openflow_runtime_pulse.yaml"

COMMON_SCHEDULE_BOUNDARY_TOKENS = (
    "owner: chaseos",
    "enabled: false",
    "activation_state: planned",
    "schedule_owner: chaseos",
    "external_runtime_owner: false",
    "canonical_writeback_enabled: false",
    "external_connectors_enabled: false",
    "unrestricted_browsing_enabled: false",
)

PULSE_COMPLETION_AUTHORITY_FALSE_FLAGS = (
    "writes_status_artifact",
    "approval_granted",
    "live_enqueue_executed",
    "agent_bus_task_written",
    "runtime_dispatch_allowed",
    "review_response_ingest_allowed",
    "candidate_apply_allowed",
    "canonical_writeback_allowed",
    "mutates_canonical_state",
    "provider_or_connector_call_allowed",
    "schedule_activation_allowed",
    "rd_workbook_update_allowed",
)

PULSE_APP_AUTHORITY_FALSE_FLAGS = (
    "writes_review_decisions",
    "applies_candidates",
    "grants_approvals",
    "agent_bus_task_write_allowed",
    "workflow_execution_allowed",
    "provider_calls_allowed",
    "external_connector_calls_allowed",
    "scheduler_changed",
    "canonical_mutation_allowed",
    "second_datastore_created",
)

LAUNCHER_AUTHORITY_FALSE_FLAGS = (
    "starts_child_apps",
    "writes_vault",
    "browser_automation",
    "mcp_scope_changed",
    "provider_calls_allowed",
    "delivery_allowed",
    "scheduler_changed",
    "canonical_mutation_allowed",
    "workflow_execution_allowed",
)

REMAINING_FUTURE_WORK = (
    "Keep ChaseOS Pulse post-completion checks running after Hermes/OpenClaw schedule work.",
    "Broaden Studio UX only through localhost and explicit operator launch flows.",
    "Add live schedule daemon activation only after a separate operator-approved pass.",
    "Keep memory approval, project updates, and knowledge promotion behind governed writeback.",
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _read_text_if_exists(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _missing_tokens(text: str, tokens: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(token for token in tokens if token not in text)


@dataclass(frozen=True)
class PulsePostCompletionHardeningCheck:
    check_id: str
    status: str
    required: bool
    evidence: str
    notes: str = ""
    missing: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.check_id:
            raise ValueError("hardening check_id is required")
        if self.status not in CHECK_STATUSES:
            raise ValueError("invalid hardening check status")
        if not self.evidence:
            raise ValueError("hardening check evidence is required")
        if self.required and self.status == CHECK_STATUS_NOT_APPLICABLE:
            raise ValueError("required hardening checks cannot be not_applicable")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["missing"] = list(self.missing)
        return payload


@dataclass(frozen=True)
class PulsePostCompletionHardeningReport:
    generated_at: str
    hardening_status: str
    current_pulse_v1_complete: bool
    required_check_count: int
    passed_required_check_count: int
    checks: tuple[PulsePostCompletionHardeningCheck, ...]
    remaining_future_work: tuple[str, ...] = REMAINING_FUTURE_WORK
    read_only: bool = True
    writes_performed: bool = False
    agent_bus_task_write_allowed: bool = False
    approval_grant_allowed: bool = False
    approval_execution_allowed: bool = False
    canonical_writeback_allowed: bool = False
    memory_approval_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    schedule_activation_allowed: bool = False
    rd_workbook_update_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_COMPLETION_BLOCKED_EFFECTS

    @property
    def check_count(self) -> int:
        return len(self.checks)

    def validate(self) -> None:
        if self.hardening_status not in HARDENING_STATUSES:
            raise ValueError("invalid Pulse hardening status")
        for check in self.checks:
            check.validate()
        required_checks = [check for check in self.checks if check.required]
        passed_required = [
            check for check in required_checks if check.status == CHECK_STATUS_PASS
        ]
        if self.required_check_count != len(required_checks):
            raise ValueError("required_check_count does not match checks")
        if self.passed_required_check_count != len(passed_required):
            raise ValueError("passed_required_check_count does not match checks")
        if not self.read_only:
            raise ValueError("Pulse hardening report must remain read-only")
        if self.writes_performed:
            raise ValueError("Pulse hardening report cannot write artifacts")
        if self.agent_bus_task_write_allowed:
            raise ValueError("Pulse hardening report cannot allow Agent Bus task writes")
        if self.approval_grant_allowed or self.approval_execution_allowed:
            raise ValueError("Pulse hardening report cannot grant or execute approvals")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse hardening report cannot allow canonical writeback")
        if self.memory_approval_allowed:
            raise ValueError("Pulse hardening report cannot approve memory")
        if self.provider_or_connector_call_allowed:
            raise ValueError("Pulse hardening report cannot call providers or connectors")
        if self.runtime_dispatch_allowed:
            raise ValueError("Pulse hardening report cannot dispatch runtimes")
        if self.schedule_activation_allowed:
            raise ValueError("Pulse hardening report cannot activate schedules")
        if self.rd_workbook_update_allowed:
            raise ValueError("Pulse hardening report cannot update the R&D workbook")
        if set(self.blocked_effects) != set(PULSE_COMPLETION_BLOCKED_EFFECTS):
            raise ValueError("Pulse hardening report must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "hardening_status": self.hardening_status,
            "current_pulse_v1_complete": self.current_pulse_v1_complete,
            "check_count": self.check_count,
            "required_check_count": self.required_check_count,
            "passed_required_check_count": self.passed_required_check_count,
            "checks": [check.to_dict() for check in self.checks],
            "remaining_future_work": list(self.remaining_future_work),
            "read_only": self.read_only,
            "writes_performed": self.writes_performed,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "approval_grant_allowed": self.approval_grant_allowed,
            "approval_execution_allowed": self.approval_execution_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "memory_approval_allowed": self.memory_approval_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "blocked_effects": list(self.blocked_effects),
        }


def _completion_status_checks(vault: Path) -> list[PulsePostCompletionHardeningCheck]:
    checks: list[PulsePostCompletionHardeningCheck] = []
    status = build_pulse_completion_status(vault)
    complete = (
        status.overall_status == PULSE_COMPLETION_OVERALL_COMPLETE
        and status.feature_done
        and status.backend_control_plane_done
        and not status.blocked_reasons
    )
    checks.append(
        PulsePostCompletionHardeningCheck(
            check_id="pulse_completion_status",
            status=CHECK_STATUS_PASS if complete else CHECK_STATUS_FAIL,
            required=True,
            evidence="runtime/pulse/completion_status.py + repo-local Pulse evidence",
            notes=(
                f"overall={status.overall_status}; feature_done={status.feature_done}; "
                f"backend_control_plane_done={status.backend_control_plane_done}; "
                f"blocked={len(status.blocked_reasons)}"
            ),
            missing=tuple(status.blocked_reasons),
        )
    )
    bad_flags = tuple(
        flag for flag in PULSE_COMPLETION_AUTHORITY_FALSE_FLAGS if bool(getattr(status, flag))
    )
    authority_ok = status.read_only and not bad_flags and set(status.blocked_effects) == set(
        PULSE_COMPLETION_BLOCKED_EFFECTS
    )
    checks.append(
        PulsePostCompletionHardeningCheck(
            check_id="pulse_completion_authority_boundary",
            status=CHECK_STATUS_PASS if authority_ok else CHECK_STATUS_FAIL,
            required=True,
            evidence="runtime/pulse/completion_status.py",
            notes="Completion status remains read-only and declares blocked effects.",
            missing=bad_flags,
        )
    )
    return checks


def _pulse_deck_app_check(vault: Path) -> PulsePostCompletionHardeningCheck:
    """Verify Pulse deck feedback capability is live in the desktop shell API."""
    missing: list[str] = []
    try:
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI.__new__(StudioAPI)
        if not hasattr(api, "get_pulse_deck_model"):
            missing.append("get_pulse_deck_model_missing")
        if not hasattr(api, "submit_pulse_feedback"):
            missing.append("submit_pulse_feedback_missing")
    except Exception as exc:
        missing.append(f"shell_api_import_failed:{exc}")
    return PulsePostCompletionHardeningCheck(
        check_id="pulse_deck_app_boundary",
        status=CHECK_STATUS_PASS if not missing else CHECK_STATUS_FAIL,
        required=True,
        evidence="runtime/studio/shell/api.py",
        notes="Pulse deck feedback migrated to desktop shell API (get_pulse_deck_model + submit_pulse_feedback).",
        missing=tuple(missing),
    )


def _studio_launcher_check(vault: Path) -> PulsePostCompletionHardeningCheck:
    try:
        plan = build_studio_app_launcher_plan(vault)
    except Exception as exc:
        return PulsePostCompletionHardeningCheck(
            check_id="studio_launcher_registry_boundary",
            status=CHECK_STATUS_FAIL,
            required=True,
            evidence="runtime/studio/app_launcher.py",
            notes=f"Could not build Studio launcher plan: {exc}",
            missing=("plan_build_failed",),
        )
    authority = plan.get("authority") or {}
    missing: list[str] = []
    if not plan.get("local_only"):
        missing.append("local_only")
    if authority.get("binds_loopback_only") is not True:
        missing.append("binds_loopback_only")
    missing.extend(flag for flag in LAUNCHER_AUTHORITY_FALSE_FLAGS if authority.get(flag) is not False)
    # pulse-deck-app migrated to desktop shell api.py (get_pulse_deck_model + submit_pulse_feedback)
    apps = plan.get("apps") or []
    if not apps and not plan.get("ok", True):
        missing.append("launcher_plan_empty")
    return PulsePostCompletionHardeningCheck(
        check_id="studio_launcher_registry_boundary",
        status=CHECK_STATUS_PASS if not missing else CHECK_STATUS_FAIL,
        required=True,
        evidence="runtime/studio/app_launcher.py",
        notes="Studio launcher only exposes operator launch guidance and read-only health probes.",
        missing=tuple(missing),
    )


def _schedule_manifest_check(
    vault: Path,
    *,
    check_id: str,
    relative_path: str,
    extra_tokens: tuple[str, ...] = (),
    required: bool = True,
) -> PulsePostCompletionHardeningCheck:
    text = _read_text_if_exists(vault / relative_path)
    if text is None:
        return PulsePostCompletionHardeningCheck(
            check_id=check_id,
            status=CHECK_STATUS_FAIL if required else CHECK_STATUS_NOT_APPLICABLE,
            required=required,
            evidence=relative_path,
            notes="Schedule manifest is absent.",
            missing=("manifest_missing",),
        )
    missing = _missing_tokens(text, COMMON_SCHEDULE_BOUNDARY_TOKENS + extra_tokens)
    return PulsePostCompletionHardeningCheck(
        check_id=check_id,
        status=CHECK_STATUS_PASS if not missing else CHECK_STATUS_FAIL,
        required=required,
        evidence=relative_path,
        notes="Manifest keeps ChaseOS schedule intent planned/inactive and executor-owned only by adapter.",
        missing=missing,
    )


def _proof_docs_check(vault: Path) -> PulsePostCompletionHardeningCheck:
    missing = tuple(path for path in REQUIRED_PROOF_DOCS if not (vault / path).exists())
    return PulsePostCompletionHardeningCheck(
        check_id="pulse_proof_documentation",
        status=CHECK_STATUS_PASS if not missing else CHECK_STATUS_FAIL,
        required=True,
        evidence="06_AGENTS/ChaseOS-Pulse-* proof docs",
        notes="Required completion proof docs are present.",
        missing=missing,
    )


def _rnd_workbook_boundary_check() -> PulsePostCompletionHardeningCheck:
    return PulsePostCompletionHardeningCheck(
        check_id="rnd_workbook_boundary",
        status=CHECK_STATUS_PASS,
        required=True,
        evidence="runtime/pulse/post_completion_hardening.py",
        notes="This verifier never writes the R&D workbook; it only reports that workbook mutation remains blocked here.",
    )


def _multi_audience_deck_artifact_check(vault: Path) -> PulsePostCompletionHardeningCheck:
    try:
        inventory = build_pulse_deck_inventory(vault)
    except Exception as exc:
        return PulsePostCompletionHardeningCheck(
            check_id="multi_audience_deck_artifacts",
            status=CHECK_STATUS_WARN,
            required=False,
            evidence="07_LOGS/Pulse-Decks/{users,agents,shared}/",
            notes=f"Could not load multi-audience deck inventory: {exc}",
            missing=("inventory_failed",),
        )
    missing = tuple(item.audience for item in inventory if not item.latest_json_path)
    return PulsePostCompletionHardeningCheck(
        check_id="multi_audience_deck_artifacts",
        status=CHECK_STATUS_PASS if not missing else CHECK_STATUS_WARN,
        required=False,
        evidence="07_LOGS/Pulse-Decks/{users,agents,shared}/",
        notes="Latest local user, agent, and shared-coordination deck artifacts are visible.",
        missing=missing,
    )


def build_pulse_post_completion_hardening_report(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> PulsePostCompletionHardeningReport:
    """Build a read-only post-completion hardening report from local evidence."""

    vault = _vault_path(vault_root)
    checks: list[PulsePostCompletionHardeningCheck] = []
    checks.extend(_completion_status_checks(vault))
    checks.append(_pulse_deck_app_check(vault))
    checks.append(_studio_launcher_check(vault))
    checks.append(
        _schedule_manifest_check(
            vault,
            check_id="daily_pulse_schedule_manifest_boundary",
            relative_path=DAILY_PULSE_MANIFEST_PATH,
            extra_tokens=(
                "openclaw_cron_owner: false",
                "windows_task_scheduler_owner: false",
            ),
        )
    )
    checks.append(
        _schedule_manifest_check(
            vault,
            check_id="hermes_pulse_schedule_manifest_boundary",
            relative_path=HERMES_PULSE_MANIFEST_PATH,
            extra_tokens=(
                "runtime_target: hermes",
                "hermes_owner: false",
                "openclaw_cron_owner: false",
            ),
        )
    )
    checks.append(
        _schedule_manifest_check(
            vault,
            check_id="openflow_pulse_schedule_manifest_boundary",
            relative_path=OPENFLOW_PULSE_MANIFEST_PATH,
            extra_tokens=("runtime_target: openflow",),
            required=False,
        )
    )
    checks.append(_proof_docs_check(vault))
    checks.append(_multi_audience_deck_artifact_check(vault))
    checks.append(_rnd_workbook_boundary_check())

    required_checks = [check for check in checks if check.required]
    passed_required = [
        check for check in required_checks if check.status == CHECK_STATUS_PASS
    ]
    required_failures = [
        check for check in required_checks if check.status == CHECK_STATUS_FAIL
    ]
    warnings = [check for check in checks if check.status == CHECK_STATUS_WARN]
    if required_failures:
        hardening_status = HARDENING_STATUS_FAIL
    elif warnings:
        hardening_status = HARDENING_STATUS_PARTIAL
    else:
        hardening_status = HARDENING_STATUS_PASS

    report = PulsePostCompletionHardeningReport(
        generated_at=generated_at or now_utc(),
        hardening_status=hardening_status,
        current_pulse_v1_complete=not required_failures
        and any(
            check.check_id == "pulse_completion_status"
            and check.status == CHECK_STATUS_PASS
            for check in checks
        ),
        required_check_count=len(required_checks),
        passed_required_check_count=len(passed_required),
        checks=tuple(checks),
    )
    report.validate()
    return report
