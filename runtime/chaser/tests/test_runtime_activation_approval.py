from __future__ import annotations

from pathlib import Path
import json

from runtime.chaser.runtime_activation_approval import (
    build_chaser_runtime_activation_approval_preview,
)
from runtime.chaser.runtime_activation_approval_request import (
    build_chaser_runtime_activation_approval_request,
)
from runtime.chaser.runtime_activation_approval_decision_preflight import (
    build_chaser_runtime_activation_approval_decision_preflight,
)
from runtime.chaser.runtime_activation_approval_consumption_design import (
    build_chaser_runtime_activation_approval_consumption_design,
)
from runtime.chaser.runtime_activation_approval_consumption_write_guard import (
    build_chaser_runtime_activation_approval_consumption_write_guard,
)
from runtime.chaser.runtime_activation_post_consumption_readiness import (
    build_chaser_runtime_activation_post_consumption_readiness,
)
from runtime.chaser.runtime_activation_executor_design import (
    build_chaser_runtime_activation_executor_design,
)
from runtime.chaser.runtime_activation_executor_write_guard import (
    build_chaser_runtime_activation_executor_write_guard,
)
from runtime.chaser.runtime_activation_state_readiness import (
    build_chaser_runtime_activation_state_readiness,
)
from runtime.chaser.runtime_profile_toolset_activation_design import (
    build_chaser_runtime_profile_toolset_activation_design,
)
from runtime.chaser.runtime_profile_toolset_activation_write_guard import (
    build_chaser_runtime_profile_toolset_activation_write_guard,
)
from runtime.chaser.runtime_profile_toolset_activation_readiness import (
    build_chaser_runtime_profile_toolset_activation_readiness,
)
from runtime.chaser.terminal_authority_audit import _snapshot
from runtime.studio.service import StudioService, StudioServiceError


def test_runtime_activation_approval_preview_is_read_only(tmp_path: Path) -> None:
    result = build_chaser_runtime_activation_approval_preview(tmp_path)

    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_activation_approval_preview"
    assert result["schema_version"] == "chaser_runtime_activation_approval_preview.v1"
    assert result["preview_status"] == "preview_ready_no_write"
    assert result["approval_request_written"] is False
    assert result["ready_to_write_activation_request_now"] is False
    assert result["activation_approval_consumption_available"] is False
    assert result["activation_approval_id"] is None
    assert result["activation_approval_preview_id"].startswith(
        "chaser-activation-preview-"
    )
    assert all(value is False for value in result["authority"].values())
    assert result["gate_design"]["ok"] is True
    preview = result["approval_request_preview"]
    assert preview["action_type"] == "chaser_runtime_activation"
    assert preview["request_status"] == "preview_only_not_written"
    assert preview["runtime_id"] == "chaser"
    assert preview["profile_id"] == "ops"
    assert preview["toolset_id"] == "terminal-preview"
    assert preview["agent_bus_mutation_requested"] is False
    assert preview["provider_dispatch_requested"] is False
    assert preview["authority_ceiling"]["terminal_output_trust_tier"] == "Tier 4"
    assert result["terminal_binding_contract"]["terminal_binding_allowed_now"] is False
    assert result["terminal_binding_contract"]["terminal_execution_allowed_now"] is False
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()
    assert not (tmp_path / "07_LOGS" / "Terminal-Runs").exists()


def test_runtime_activation_approval_preview_blocks_agent_bus_and_provider_requests(
    tmp_path: Path,
) -> None:
    result = build_chaser_runtime_activation_approval_preview(
        tmp_path,
        agent_bus_mutation_requested=True,
        provider_dispatch_requested=True,
    )

    assert result["ok"] is False
    assert result["preview_status"] == "preview_blocked"
    assert "agent_bus_mutation_requires_separate_gate" in result["blockers"]
    assert "provider_dispatch_requires_separate_gate" in result["blockers"]
    assert result["approval_request_written"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert result["authority"]["provider_call_now"] is False
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_preview_propagates_gate_blockers(
    tmp_path: Path,
) -> None:
    result = build_chaser_runtime_activation_approval_preview(
        tmp_path,
        profile_id="missing",
        toolset_id="terminal-preview",
    )

    assert result["ok"] is False
    assert result["preview_status"] == "preview_blocked"
    assert "activation_gate_design_not_ready" in result["blockers"]
    assert "unknown_profile:missing" in result["blockers"]
    assert result["gate_design"]["ok"] is False
    assert result["authority"]["runtime_activation_now"] is False
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()


def test_terminal_authority_snapshot_ignores_volatile_runtime_cache_files(
    tmp_path: Path,
) -> None:
    agent_bus = tmp_path / "runtime" / "agent_bus"
    cache_dir = agent_bus / "__pycache__"
    cache_dir.mkdir(parents=True)
    (cache_dir / "bus.cpython-313.pyc").write_bytes(b"cache")
    (agent_bus / "agent_bus.sqlite").write_text("state", encoding="utf-8")
    (agent_bus / "agent_bus.sqlite-wal").write_text("wal", encoding="utf-8")
    (agent_bus / "agent_bus.sqlite-shm").write_text("shm", encoding="utf-8")

    assert _snapshot(agent_bus) == ["agent_bus.sqlite"]


def test_runtime_activation_approval_request_defaults_to_preview_only(
    tmp_path: Path,
) -> None:
    result = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
    )

    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_activation_approval_request_write_gate"
    assert result["schema_version"] == "chaser_runtime_activation_approval_request_write_gate.v1"
    assert result["request_status"] == "ready_for_activation_approval_request"
    assert result["write_request_requested"] is False
    assert result["approval_request_written"] is False
    assert result["ready_to_write_activation_request_now"] is True
    assert result["activation_approval_consumption_available"] is False
    assert result["authority"]["approval_queue_write_now"] is False
    assert result["authority"]["runtime_activation_now"] is False
    assert result["authority"]["terminal_execution_now"] is False
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_request_write_queues_only(
    tmp_path: Path,
) -> None:
    result = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )

    assert result["ok"] is True
    assert result["request_status"] == "pending_activation_approval_request_written"
    assert result["approval_request_written"] is True
    assert result["approval_id"]
    assert result["approval_path"]
    assert result["authority"]["approval_queue_write_now"] is True
    assert result["authority"]["approval_consumption_now"] is False
    assert result["authority"]["runtime_activation_now"] is False
    assert result["authority"]["terminal_toolset_binding_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert result["authority"]["provider_call_now"] is False

    approval_path = tmp_path / result["approval_path"]
    assert approval_path.exists()
    approval = StudioService(tmp_path).get_approval(result["approval_id"])
    assert approval is not None
    assert approval.status == "pending"
    assert approval.action_spec.action_type == "execute_process"
    metadata = approval.action_spec.metadata
    assert metadata["chaser_runtime_activation_approval_request"] is True
    assert metadata["ambient_studio_approval_execution_blocked"] is True
    assert metadata["profile_id"] == "ops"
    assert metadata["toolset_id"] == "terminal-preview"
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_request_duplicate_pending_reuses_existing(
    tmp_path: Path,
) -> None:
    first = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    second = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )

    assert first["approval_request_written"] is True
    assert second["request_status"] == "existing_pending_activation_approval_request"
    assert second["approval_request_written"] is False
    assert second["approval_id"] == first["approval_id"]
    assert second["duplicate_of_existing_pending"] is True
    assert len(list((tmp_path / "runtime" / "studio" / "approvals").glob("*.json"))) == 1


def test_runtime_activation_approval_request_blocks_agent_bus_and_provider(
    tmp_path: Path,
) -> None:
    result = build_chaser_runtime_activation_approval_request(
        tmp_path,
        agent_bus_mutation_requested=True,
        provider_dispatch_requested=True,
        write_request=True,
    )

    assert result["ok"] is False
    assert result["request_status"] == "blocked"
    assert "agent_bus_mutation_requires_separate_gate" in result["blockers"]
    assert "provider_dispatch_requires_separate_gate" in result["blockers"]
    assert result["approval_request_written"] is False
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_request_blocks_ambient_studio_execution(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    service = StudioService(tmp_path)
    service.approve(request["approval_id"], reviewed_by="operator")

    try:
        service.execute_approved(request["approval_id"])
    except StudioServiceError as exc:
        assert "future governed activation approval consumption executor" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("ambient Studio execution unexpectedly consumed approval")


def test_runtime_activation_approval_decision_preflight_blocks_pending_without_mutation(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )

    result = build_chaser_runtime_activation_approval_decision_preflight(
        tmp_path,
        request["approval_id"],
    )

    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_activation_approval_decision_preflight"
    assert result["schema_version"] == (
        "chaser_runtime_activation_approval_decision_preflight.v1"
    )
    assert result["decision_preflight_status"] == "blocked_pending_activation_approval"
    assert result["approval_status"] == "pending"
    assert result["approval_decision_written"] is False
    assert result["approval_status_mutated"] is False
    assert result["approval_consumed"] is False
    assert result["ready_for_activation_consumer_next_pass"] is False
    assert all(value is False for value in result["authority"].values())
    assert StudioService(tmp_path).get_approval(request["approval_id"]).status == "pending"
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_decision_preflight_accepts_approved_for_future_consumer(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = build_chaser_runtime_activation_approval_decision_preflight(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is True
    assert result["decision_preflight_status"] == (
        "activation_approval_decision_preflight_ready_no_mutation"
    )
    assert result["approval_status"] == "approved"
    assert result["approved_for_future_activation_consumer_review"] is True
    assert result["ready_for_activation_consumer_next_pass"] is True
    assert result["activation_approval_consumption_available"] is False
    assert result["activation_allowed"] is False
    assert result["runtime_activation_now"] is False
    assert result["terminal_binding_now"] is False
    assert result["authority"]["approval_consumption_now"] is False
    assert result["authority"]["runtime_activation_now"] is False
    assert not result["blockers"]
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_decision_preflight_reports_rejected(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).reject(
        request["approval_id"],
        reason="not now",
        reviewed_by="operator",
    )

    result = build_chaser_runtime_activation_approval_decision_preflight(
        tmp_path,
        request["approval_id"],
    )

    assert result["ok"] is True
    assert result["decision_preflight_status"] == (
        "activation_approval_decision_preflight_rejected_blocks_activation"
    )
    assert result["approval_status"] == "rejected"
    assert result["approved_for_future_activation_consumer_review"] is False
    assert result["activation_allowed"] is False
    assert result["approval_consumed"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_decision_preflight_rejects_unsafe_or_missing_id(
    tmp_path: Path,
) -> None:
    unsafe = build_chaser_runtime_activation_approval_decision_preflight(
        tmp_path,
        "../escape",
    )
    missing = build_chaser_runtime_activation_approval_decision_preflight(
        tmp_path,
        "missing-approval",
    )

    assert unsafe["ok"] is False
    assert unsafe["decision_preflight_status"] == "blocked_unsafe_activation_approval_id"
    assert "unsafe_activation_approval_id" in unsafe["blockers"]
    assert missing["ok"] is False
    assert missing["decision_preflight_status"] == "blocked_missing_activation_approval"
    assert "activation_approval_not_found" in missing["blockers"]
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_consumption_design_blocks_pending_without_writes(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )

    result = build_chaser_runtime_activation_approval_consumption_design(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_activation_approval_consumption_design"
    assert result["schema_version"] == (
        "chaser_runtime_activation_approval_consumption_design.v1"
    )
    assert result["consumption_design_status"] == (
        "blocked_activation_approval_consumption_design_preflight_not_approved"
    )
    assert result["approval_status"] == "pending"
    assert result["ready_for_activation_consumption_write_guard_next_pass"] is False
    assert result["activation_approval_consumption_design_available"] is True
    assert result["activation_approval_consumption_available"] is False
    assert result["approval_consumed"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_performed"] is False
    assert all(value is False for value in result["authority"].values())
    marker_path = tmp_path / result["consumer_marker_preview"]["path"]
    assert not marker_path.exists()
    assert StudioService(tmp_path).get_approval(request["approval_id"]).status == "pending"
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_consumption_design_ready_for_approved_write_guard(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = build_chaser_runtime_activation_approval_consumption_design(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        actor="operator",
    )

    assert result["ok"] is True
    assert result["consumption_design_status"] == (
        "activation_approval_consumption_design_ready_no_mutation"
    )
    assert result["approval_status"] == "approved"
    assert result["ready_for_activation_consumption_write_guard_next_pass"] is True
    assert result["consumer_record_schema"]["approval_status_required"] == "approved"
    assert result["consumer_marker_preview"]["create_new_only"] is True
    assert result["consumer_marker_preview"]["exact_once"] is True
    assert result["audit_event_preview"]["append_only"] is True
    assert "stop_before_chaser_runtime_activation" in [
        step["step_id"] for step in result["future_consumer_sequence"]
    ]
    assert result["runtime_activation_now"] is False
    assert result["terminal_binding_now"] is False
    assert result["authority"]["approval_consumption_now"] is False
    assert result["authority"]["exact_once_marker_write_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert not (tmp_path / result["consumer_marker_preview"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_consumption_design_rejects_unsafe_or_missing_id(
    tmp_path: Path,
) -> None:
    unsafe = build_chaser_runtime_activation_approval_consumption_design(
        tmp_path,
        "../escape",
    )
    missing = build_chaser_runtime_activation_approval_consumption_design(
        tmp_path,
        "missing-approval",
    )

    assert unsafe["ok"] is False
    assert unsafe["consumption_design_status"] == (
        "blocked_activation_approval_consumption_design_preflight_unavailable"
    )
    assert unsafe["decision_preflight"]["decision_preflight_status"] == (
        "blocked_unsafe_activation_approval_id"
    )
    assert missing["ok"] is False
    assert missing["decision_preflight"]["decision_preflight_status"] == (
        "blocked_missing_activation_approval"
    )
    assert unsafe["authority"]["approval_consumption_now"] is False
    assert missing["authority"]["runtime_activation_now"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_consumption_write_guard_previews_ready_without_writes(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_activation_approval_consumption_write_guard"
    assert result["schema_version"] == (
        "chaser_runtime_activation_approval_consumption_write_guard.v1"
    )
    assert result["write_guard_status"] == (
        "activation_approval_consumption_write_guard_ready_no_write"
    )
    assert result["approval_status"] == "approved"
    assert result["write_consumption_marker_requested"] is False
    assert result["approval_consumed"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_audit_written"] is False
    assert result["authority"]["approval_consumption_now"] is False
    assert result["authority"]["exact_once_marker_write_now"] is False
    assert not (tmp_path / result["exact_once_marker"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_consumption_write_guard_blocks_pending_without_writes(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )

    result = build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )

    assert result["ok"] is False
    assert result["write_guard_status"] == (
        "blocked_activation_approval_consumption_write_guard"
    )
    assert "blocked_activation_approval_consumption_design_preflight_not_approved" in result["blockers"]
    assert result["approval_consumed"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_audit_written"] is False
    assert result["authority"]["approval_consumption_now"] is False
    assert not (tmp_path / result["exact_once_marker"]["path"]).exists()
    assert StudioService(tmp_path).get_approval(request["approval_id"]).status == "pending"
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_approval_consumption_write_guard_requires_confirmation(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
    )

    assert result["ok"] is False
    assert "explicit_activation_approval_consumption_confirmation_required" in result["blockers"]
    assert result["approval_consumed"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["activation_audit_written"] is False
    assert not (tmp_path / result["exact_once_marker"]["path"]).exists()
    assert StudioService(tmp_path).get_approval(request["approval_id"]).status == "approved"


def test_runtime_activation_approval_consumption_write_guard_writes_marker_and_audit_once(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        actor="operator",
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )

    assert result["ok"] is True
    assert result["write_guard_status"] == (
        "activation_approval_consumption_marker_and_audit_written_activation_blocked"
    )
    assert result["approval_consumed"] is True
    assert result["approval_status_after"] == "approved"
    assert result["approval_status_mutated"] is False
    assert result["activation_consumption_marker_written"] is True
    assert result["activation_audit_written"] is True
    assert result["activation_performed"] is False
    assert result["runtime_activation_now"] is False
    assert result["terminal_binding_now"] is False
    assert result["authority"]["approval_consumption_now"] is True
    assert result["authority"]["exact_once_marker_write_now"] is True
    assert result["authority"]["activation_audit_write_now"] is True
    assert result["authority"]["runtime_activation_now"] is False
    assert result["authority"]["terminal_execution_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False

    marker_path = tmp_path / result["exact_once_marker"]["path"]
    audit_path = tmp_path / result["activation_audit"]["path"]
    assert marker_path.exists()
    assert audit_path.exists()
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker["status"] == "consumed_marker_written_activation_still_blocked"
    assert marker["activation_approval_id"] == request["approval_id"]
    assert marker["runtime_activation_performed"] is False
    assert marker["terminal_binding_performed"] is False
    audit_lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) == 1
    event = json.loads(audit_lines[0])
    assert event["event_type"] == "chaser_runtime_activation_approval_consumption"
    assert event["activation_approval_id"] == request["approval_id"]
    assert event["runtime_activation_performed"] is False
    assert StudioService(tmp_path).get_approval(request["approval_id"]).status == "approved"
    assert not (tmp_path / "runtime" / "agent_bus").exists()

    duplicate = build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )
    assert duplicate["ok"] is False
    assert "exact_once_marker_already_present" in duplicate["blockers"]
    assert audit_path.read_text(encoding="utf-8").splitlines() == audit_lines


def test_runtime_activation_post_consumption_readiness_blocks_before_marker(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = build_chaser_runtime_activation_post_consumption_readiness(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is False
    assert result["surface"] == "chaser_runtime_activation_post_consumption_readiness"
    assert result["post_consumption_readiness_status"] == (
        "blocked_activation_post_consumption_readiness"
    )
    assert "activation_consumption_marker_missing" in result["blockers"]
    assert "activation_consumption_audit_missing" in result["blockers"]
    assert result["ready_for_activation_executor_next_pass"] is False
    assert result["activation_executor_available"] is False
    assert all(value is False for value in result["authority"].values())
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_post_consumption_readiness_blocks_marker_without_audit(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    consumed = build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )
    audit_path = tmp_path / consumed["activation_audit"]["path"]
    audit_path.unlink()

    result = build_chaser_runtime_activation_post_consumption_readiness(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is False
    assert "activation_consumption_audit_missing" in result["blockers"]
    assert result["exact_once_marker"]["loaded"] is True
    assert result["activation_audit"]["matching_event_found"] is False
    assert result["ready_for_activation_executor_next_pass"] is False
    assert result["activation_allowed"] is False
    assert result["writes_performed"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_post_consumption_readiness_reads_marker_and_audit(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    consumed = build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        actor="operator",
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )

    result = build_chaser_runtime_activation_post_consumption_readiness(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is True
    assert result["post_consumption_readiness_status"] == (
        "activation_post_consumption_readiness_ready_activation_still_blocked"
    )
    assert result["ready_for_activation_executor_next_pass"] is True
    assert result["activation_executor_available"] is False
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["runtime_activation_now"] is False
    assert result["terminal_binding_now"] is False
    assert result["writes_performed"] is False
    assert result["files_modified"] is False
    assert all(value is False for value in result["authority"].values())
    assert result["exact_once_marker"]["path"] == consumed["exact_once_marker"]["path"]
    assert result["exact_once_marker"]["loaded"] is True
    assert result["activation_audit"]["matching_event_found"] is True
    assert all(check["ok"] is True for check in result["marker_checks"])
    assert all(check["ok"] is True for check in result["audit_checks"])
    assert result["next_recommended_pass"] == (
        "terminal-n23-chaser-runtime-activation-executor-design"
    )
    assert StudioService(tmp_path).get_approval(request["approval_id"]).status == "approved"
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_executor_design_blocks_before_post_consumption_readiness(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = build_chaser_runtime_activation_executor_design(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is False
    assert result["surface"] == "chaser_runtime_activation_executor_design"
    assert result["activation_executor_design_status"] == (
        "blocked_activation_executor_design"
    )
    assert "post_consumption_readiness_not_ready" in result["blockers"]
    assert "activation_consumption_marker_missing" in result["blockers"]
    assert result["ready_for_activation_executor_write_guard_next_pass"] is False
    assert result["activation_executor_available"] is False
    assert result["activation_executor_write_guard_available"] is True
    assert result["activation_allowed"] is False
    assert result["writes_performed"] is False
    assert result["files_modified"] is False
    assert all(value is False for value in result["authority"].values())
    assert not (tmp_path / "runtime" / "chaser" / "activation-state").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_executor_design_reads_ready_consumed_pair_without_activation(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        actor="operator",
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )

    result = build_chaser_runtime_activation_executor_design(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is True
    assert result["activation_executor_design_status"] == (
        "activation_executor_design_ready_no_activation"
    )
    assert result["ready_for_activation_executor_write_guard_next_pass"] is True
    assert result["activation_executor_available"] is False
    assert result["activation_executor_write_guard_available"] is True
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["terminal_binding_allowed_in_activation_executor"] is False
    assert result["terminal_execution_allowed_in_activation_executor"] is False
    assert result["studio_execution_allowed_in_activation_executor"] is False
    assert result["future_activation_marker_preview"]["written_in_this_pass"] is False
    assert result["future_activation_state_preview"]["written_in_this_pass"] is False
    assert result["future_activation_audit_preview"]["written_in_this_pass"] is False
    assert result["post_consumption_readiness"]["ok"] is True
    assert all(check["passed"] is True for check in result["executor_design_checks"])
    assert all(value is False for value in result["authority"].values())
    assert result["next_recommended_pass"] == (
        "terminal-n24-chaser-runtime-activation-executor-write-guard"
    )
    assert not (tmp_path / result["future_activation_marker_preview"]["path"]).exists()
    assert not (tmp_path / result["future_activation_state_preview"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_executor_design_rejects_agent_bus_and_provider_scope(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )

    result = build_chaser_runtime_activation_executor_design(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        request_agent_bus_mutation=True,
        request_provider_dispatch=True,
    )

    assert result["ok"] is False
    assert "agent_bus_mutation_not_in_activation_executor_scope" in result["blockers"]
    assert "provider_dispatch_not_in_activation_executor_scope" in result["blockers"]
    assert result["activation_performed"] is False
    assert all(value is False for value in result["authority"].values())


def test_runtime_activation_executor_write_guard_previews_ready_without_writes(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )

    result = build_chaser_runtime_activation_executor_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_activation_executor_write_guard"
    assert result["schema_version"] == (
        "chaser_runtime_activation_executor_write_guard.v1"
    )
    assert result["write_guard_status"] == "activation_executor_write_guard_ready_no_write"
    assert result["ready_for_activation_executor_write_now"] is True
    assert result["write_activation_state_requested"] is False
    assert result["activation_marker_written"] is False
    assert result["activation_state_written"] is False
    assert result["activation_audit_written"] is False
    assert result["activation_performed"] is False
    assert result["live_runtime_activated"] is False
    assert result["terminal_binding_performed"] is False
    assert all(value is False for value in result["authority"].values())
    assert not (tmp_path / result["runtime_activation_marker"]["path"]).exists()
    assert not (tmp_path / result["runtime_activation_state"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_executor_write_guard_blocks_without_readiness(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = build_chaser_runtime_activation_executor_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_activation_state=True,
        confirm_runtime_activation_record=True,
    )

    assert result["ok"] is False
    assert result["write_guard_status"] == "blocked_activation_executor_write_guard"
    assert "post_consumption_readiness_not_ready" in result["blockers"]
    assert result["activation_marker_written"] is False
    assert result["activation_state_written"] is False
    assert result["activation_audit_written"] is False
    assert result["authority"]["activation_state_write_now"] is False
    assert not (tmp_path / result["runtime_activation_state"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_executor_write_guard_requires_confirmation(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )

    result = build_chaser_runtime_activation_executor_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_activation_state=True,
    )

    assert result["ok"] is False
    assert "explicit_runtime_activation_record_confirmation_required" in result["blockers"]
    assert result["activation_marker_written"] is False
    assert result["activation_state_written"] is False
    assert result["activation_audit_written"] is False
    assert result["authority"]["exact_once_marker_write_now"] is False
    assert not (tmp_path / result["runtime_activation_marker"]["path"]).exists()


def test_runtime_activation_executor_write_guard_writes_marker_state_and_audit_once(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )

    result = build_chaser_runtime_activation_executor_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        actor="operator",
        write_activation_state=True,
        confirm_runtime_activation_record=True,
    )

    assert result["ok"] is True
    assert result["write_guard_status"] == (
        "runtime_activation_marker_state_and_audit_written_live_runtime_blocked"
    )
    assert result["activation_marker_written"] is True
    assert result["activation_state_written"] is True
    assert result["activation_audit_written"] is True
    assert result["activation_performed"] is False
    assert result["live_runtime_activated"] is False
    assert result["terminal_binding_performed"] is False
    assert result["terminal_execution_performed"] is False
    assert result["approval_status_mutated"] is False
    assert result["authority"]["exact_once_marker_write_now"] is True
    assert result["authority"]["activation_state_write_now"] is True
    assert result["authority"]["activation_audit_write_now"] is True
    assert result["authority"]["runtime_activation_now"] is False
    assert result["authority"]["terminal_execution_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False

    marker_path = tmp_path / result["runtime_activation_marker"]["path"]
    state_path = tmp_path / result["runtime_activation_state"]["path"]
    audit_path = tmp_path / result["runtime_activation_audit"]["path"]
    assert marker_path.exists()
    assert state_path.exists()
    assert audit_path.exists()
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    audit_lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert marker["schema_version"] == "chaser_runtime_activation_marker.v1"
    assert marker["live_runtime_activated"] is False
    assert marker["terminal_binding_performed"] is False
    assert state["schema_version"] == "chaser_runtime_activation_state.v1"
    assert state["status"] == "activation_state_written_live_runtime_still_blocked"
    assert state["live_runtime_activated"] is False
    assert state["agent_bus_mutation_performed"] is False
    assert len(audit_lines) == 1
    event = json.loads(audit_lines[0])
    assert event["schema_version"] == "chaser_runtime_activation_executor_audit.v1"
    assert event["event_type"] == "chaser_runtime_activation_executor"
    assert event["live_runtime_activated"] is False
    assert StudioService(tmp_path).get_approval(request["approval_id"]).status == "approved"
    assert not (tmp_path / "runtime" / "agent_bus").exists()

    duplicate = build_chaser_runtime_activation_executor_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_activation_state=True,
        confirm_runtime_activation_record=True,
    )
    assert duplicate["ok"] is False
    assert "runtime_activation_marker_already_present" in duplicate["blockers"]
    assert audit_path.read_text(encoding="utf-8").splitlines() == audit_lines


def test_runtime_activation_executor_write_guard_rejects_agent_bus_and_provider_scope(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )

    result = build_chaser_runtime_activation_executor_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_activation_state=True,
        confirm_runtime_activation_record=True,
        request_agent_bus_mutation=True,
        request_provider_dispatch=True,
    )

    assert result["ok"] is False
    assert "agent_bus_mutation_not_in_activation_executor_scope" in result["blockers"]
    assert "provider_dispatch_not_in_activation_executor_scope" in result["blockers"]
    assert result["activation_marker_written"] is False
    assert result["activation_state_written"] is False
    assert result["authority"]["activation_state_write_now"] is False
    assert not (tmp_path / result["runtime_activation_state"]["path"]).exists()


def test_runtime_activation_state_readiness_blocks_before_executor_record(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )

    result = build_chaser_runtime_activation_state_readiness(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is False
    assert result["surface"] == "chaser_runtime_activation_state_readiness"
    assert result["activation_state_readiness_status"] == (
        "blocked_activation_state_readiness"
    )
    assert "runtime_activation_marker_missing" in result["blockers"]
    assert "runtime_activation_state_missing" in result["blockers"]
    assert "runtime_activation_executor_audit_missing" in result["blockers"]
    assert result["ready_for_profile_toolset_activation_design_next_pass"] is False
    assert result["profile_toolset_activation_design_available"] is True
    assert all(value is False for value in result["authority"].values())
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_state_readiness_reads_marker_state_and_audit(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )
    written = build_chaser_runtime_activation_executor_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_activation_state=True,
        confirm_runtime_activation_record=True,
    )

    result = build_chaser_runtime_activation_state_readiness(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is True
    assert result["activation_state_readiness_status"] == (
        "activation_state_readiness_ready_live_runtime_still_blocked"
    )
    assert result["ready_for_profile_toolset_activation_design_next_pass"] is True
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["live_runtime_activated"] is False
    assert result["runtime_activation_now"] is False
    assert result["terminal_binding_now"] is False
    assert result["writes_performed"] is False
    assert result["files_modified"] is False
    assert all(value is False for value in result["authority"].values())
    assert result["runtime_activation_marker"]["path"] == (
        written["runtime_activation_marker"]["path"]
    )
    assert result["runtime_activation_state"]["path"] == (
        written["runtime_activation_state"]["path"]
    )
    assert result["runtime_activation_marker"]["loaded"] is True
    assert result["runtime_activation_state"]["loaded"] is True
    assert result["runtime_activation_audit"]["matching_event_found"] is True
    assert all(check["ok"] is True for check in result["marker_checks"])
    assert all(check["ok"] is True for check in result["state_checks"])
    assert all(check["ok"] is True for check in result["audit_checks"])
    assert result["next_recommended_pass"] == (
        "terminal-n27-chaser-runtime-profile-toolset-activation-write-guard"
    )
    assert StudioService(tmp_path).get_approval(request["approval_id"]).status == "approved"
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_state_readiness_blocks_missing_state_file(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )
    written = build_chaser_runtime_activation_executor_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_activation_state=True,
        confirm_runtime_activation_record=True,
    )
    (tmp_path / written["runtime_activation_state"]["path"]).unlink()

    result = build_chaser_runtime_activation_state_readiness(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is False
    assert "runtime_activation_state_missing" in result["blockers"]
    assert result["runtime_activation_marker"]["loaded"] is True
    assert result["runtime_activation_state"]["loaded"] is False
    assert result["runtime_activation_audit"]["matching_event_found"] is True
    assert result["ready_for_profile_toolset_activation_design_next_pass"] is False
    assert result["activation_allowed"] is False
    assert result["writes_performed"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_activation_state_readiness_blocks_mutated_state_effects(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )
    written = build_chaser_runtime_activation_executor_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_activation_state=True,
        confirm_runtime_activation_record=True,
    )
    state_path = tmp_path / written["runtime_activation_state"]["path"]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["live_runtime_activated"] = True
    state_path.write_text(json.dumps(state), encoding="utf-8")

    result = build_chaser_runtime_activation_state_readiness(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
    )

    assert result["ok"] is False
    assert "state_check_failed:state_effects_false" in result["blockers"]
    assert result["runtime_activation_state"]["loaded"] is True
    assert result["activation_performed"] is False
    assert result["authority"]["runtime_activation_now"] is False


def test_runtime_activation_state_readiness_rejects_unsafe_or_missing_id(
    tmp_path: Path,
) -> None:
    unsafe = build_chaser_runtime_activation_state_readiness(tmp_path, "../escape")
    missing = build_chaser_runtime_activation_state_readiness(tmp_path, "missing")

    assert unsafe["ok"] is False
    assert "activation_executor_design_not_ready" in unsafe["blockers"]
    assert "blocked_unsafe_activation_approval_id" in unsafe["blockers"]
    assert missing["ok"] is False
    assert "activation_executor_design_not_ready" in missing["blockers"]
    assert "blocked_missing_activation_approval" in missing["blockers"]
    assert all(value is False for value in unsafe["authority"].values())


def test_runtime_profile_toolset_activation_design_blocks_before_state_readiness(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = build_chaser_runtime_profile_toolset_activation_design(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="ops",
        expected_toolset_id="terminal-preview",
    )

    assert result["ok"] is False
    assert result["surface"] == "chaser_runtime_profile_toolset_activation_design"
    assert result["profile_toolset_activation_design_status"] == (
        "blocked_profile_toolset_activation_design"
    )
    assert "activation_state_readiness_not_ready" in result["blockers"]
    assert result["ready_for_profile_toolset_activation_write_guard_next_pass"] is False
    assert result["profile_toolset_activation_design_available"] is True
    assert result["profile_toolset_activation_write_guard_available"] is True
    assert result["activation_allowed"] is False
    assert result["profile_activation_now"] is False
    assert result["toolset_activation_now"] is False
    assert all(value is False for value in result["authority"].values())
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_profile_toolset_activation_design_reads_n25_state(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )
    build_chaser_runtime_activation_executor_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_activation_state=True,
        confirm_runtime_activation_record=True,
    )

    result = build_chaser_runtime_profile_toolset_activation_design(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="ops",
        expected_toolset_id="terminal-preview",
    )

    assert result["ok"] is True
    assert result["profile_toolset_activation_design_status"] == (
        "profile_toolset_activation_design_ready_no_activation"
    )
    assert result["ready_for_profile_toolset_activation_write_guard_next_pass"] is True
    assert result["activation_state_readiness"]["ok"] is True
    assert result["profile_id"] == "ops"
    assert result["toolset_id"] == "terminal-preview"
    assert result["profile_validation"]["ok"] is True
    assert result["toolset_validation"]["ok"] is True
    assert result["future_write_guard_contract"]["contract_status"] == (
        "design_complete_write_guard_available"
    )
    artifacts = result["future_profile_toolset_activation_artifacts"]
    assert artifacts["profile_toolset_activation_marker"]["written_in_this_pass"] is False
    assert artifacts["profile_activation_state"]["written_in_this_pass"] is False
    assert artifacts["toolset_activation_state"]["written_in_this_pass"] is False
    assert artifacts["profile_toolset_activation_audit"]["written_in_this_pass"] is False
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["live_runtime_activated"] is False
    assert result["writes_performed"] is False
    assert result["files_modified"] is False
    assert result["terminal_binding_design"]["terminal_binding_allowed_now"] is False
    assert result["terminal_binding_design"]["terminal_execution_allowed_now"] is False
    assert all(value is False for value in result["authority"].values())
    assert result["next_recommended_pass"] == (
        "terminal-n28-chaser-runtime-profile-toolset-activation-readiness"
    )
    assert not (tmp_path / artifacts["profile_toolset_activation_marker"]["path"]).exists()
    assert not (tmp_path / artifacts["profile_activation_state"]["path"]).exists()
    assert not (tmp_path / artifacts["toolset_activation_state"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_profile_toolset_activation_design_blocks_expected_mismatch(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )
    build_chaser_runtime_activation_executor_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_activation_state=True,
        confirm_runtime_activation_record=True,
    )

    result = build_chaser_runtime_profile_toolset_activation_design(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="builder",
        expected_toolset_id="repo-preview",
    )

    assert result["ok"] is False
    assert "profile_id_mismatch:builder!=ops" in result["blockers"]
    assert "toolset_id_mismatch:repo-preview!=terminal-preview" in result["blockers"]
    assert result["activation_performed"] is False
    assert result["writes_performed"] is False


def _ready_profile_toolset_activation_request(tmp_path: Path) -> dict:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    build_chaser_runtime_activation_approval_consumption_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_consumption_marker=True,
        confirm_activation_approval_consumption=True,
    )
    build_chaser_runtime_activation_executor_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        write_activation_state=True,
        confirm_runtime_activation_record=True,
    )
    return request


def test_runtime_profile_toolset_activation_write_guard_previews_ready_without_writes(
    tmp_path: Path,
) -> None:
    request = _ready_profile_toolset_activation_request(tmp_path)

    result = build_chaser_runtime_profile_toolset_activation_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="ops",
        expected_toolset_id="terminal-preview",
    )

    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_profile_toolset_activation_write_guard"
    assert result["schema_version"] == (
        "chaser_runtime_profile_toolset_activation_write_guard.v1"
    )
    assert result["write_guard_status"] == (
        "profile_toolset_activation_write_guard_ready_no_write"
    )
    assert result["ready_for_profile_toolset_activation_write_now"] is True
    assert result["write_profile_toolset_activation_requested"] is False
    assert result["profile_toolset_activation_marker_written"] is False
    assert result["profile_activation_state_written"] is False
    assert result["toolset_activation_state_written"] is False
    assert result["profile_toolset_activation_audit_written"] is False
    assert result["activation_performed"] is False
    assert result["live_runtime_activated"] is False
    assert result["terminal_binding_performed"] is False
    assert all(value is False for value in result["authority"].values())
    assert not (tmp_path / result["profile_toolset_activation_marker"]["path"]).exists()
    assert not (tmp_path / result["profile_activation_state"]["path"]).exists()
    assert not (tmp_path / result["toolset_activation_state"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_profile_toolset_activation_write_guard_blocks_without_readiness(
    tmp_path: Path,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate chaser after operator approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = build_chaser_runtime_profile_toolset_activation_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="ops",
        expected_toolset_id="terminal-preview",
        write_profile_toolset_activation=True,
        confirm_profile_toolset_activation_record=True,
    )

    assert result["ok"] is False
    assert result["write_guard_status"] == "blocked_profile_toolset_activation_write_guard"
    assert "profile_toolset_activation_design_unavailable" in result["blockers"]
    assert "activation_state_readiness_not_ready" in result["blockers"]
    assert result["profile_toolset_activation_marker_written"] is False
    assert result["profile_activation_state_written"] is False
    assert result["toolset_activation_state_written"] is False
    assert result["authority"]["profile_activation_state_write_now"] is False
    assert not (tmp_path / result["profile_activation_state"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_profile_toolset_activation_write_guard_requires_confirmation(
    tmp_path: Path,
) -> None:
    request = _ready_profile_toolset_activation_request(tmp_path)

    result = build_chaser_runtime_profile_toolset_activation_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="ops",
        expected_toolset_id="terminal-preview",
        write_profile_toolset_activation=True,
    )

    assert result["ok"] is False
    assert "explicit_profile_toolset_activation_record_confirmation_required" in (
        result["blockers"]
    )
    assert result["profile_toolset_activation_marker_written"] is False
    assert result["profile_activation_state_written"] is False
    assert result["toolset_activation_state_written"] is False
    assert result["authority"]["exact_once_marker_write_now"] is False
    assert not (tmp_path / result["profile_toolset_activation_marker"]["path"]).exists()


def test_runtime_profile_toolset_activation_write_guard_writes_records_once(
    tmp_path: Path,
) -> None:
    request = _ready_profile_toolset_activation_request(tmp_path)

    result = build_chaser_runtime_profile_toolset_activation_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="ops",
        expected_toolset_id="terminal-preview",
        actor="operator",
        write_profile_toolset_activation=True,
        confirm_profile_toolset_activation_record=True,
    )

    assert result["ok"] is True
    assert result["write_guard_status"] == (
        "profile_toolset_activation_marker_state_and_audit_written_"
        "live_runtime_blocked"
    )
    assert result["profile_toolset_activation_marker_written"] is True
    assert result["profile_activation_state_written"] is True
    assert result["toolset_activation_state_written"] is True
    assert result["profile_toolset_activation_audit_written"] is True
    assert result["activation_performed"] is False
    assert result["live_runtime_activated"] is False
    assert result["terminal_binding_performed"] is False
    assert result["terminal_execution_performed"] is False
    assert result["approval_status_mutated"] is False
    assert result["authority"]["exact_once_marker_write_now"] is True
    assert result["authority"]["profile_activation_state_write_now"] is True
    assert result["authority"]["toolset_activation_state_write_now"] is True
    assert result["authority"]["profile_toolset_activation_audit_write_now"] is True
    assert result["authority"]["profile_activation_now"] is False
    assert result["authority"]["toolset_activation_now"] is False
    assert result["authority"]["terminal_execution_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False

    marker_path = tmp_path / result["profile_toolset_activation_marker"]["path"]
    profile_state_path = tmp_path / result["profile_activation_state"]["path"]
    toolset_state_path = tmp_path / result["toolset_activation_state"]["path"]
    audit_path = tmp_path / result["profile_toolset_activation_audit"]["path"]
    assert marker_path.exists()
    assert profile_state_path.exists()
    assert toolset_state_path.exists()
    assert audit_path.exists()
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    profile_state = json.loads(profile_state_path.read_text(encoding="utf-8"))
    toolset_state = json.loads(toolset_state_path.read_text(encoding="utf-8"))
    audit_lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert marker["schema_version"] == "chaser_profile_toolset_activation_marker.v1"
    assert marker["live_runtime_activated"] is False
    assert marker["terminal_binding_performed"] is False
    assert profile_state["schema_version"] == "chaser_profile_activation_state.v1"
    assert profile_state["profile_activation_performed"] is False
    assert toolset_state["schema_version"] == "chaser_toolset_activation_state.v1"
    assert toolset_state["toolset_activation_performed"] is False
    assert len(audit_lines) == 1
    event = json.loads(audit_lines[0])
    assert event["schema_version"] == "chaser_profile_toolset_activation_audit.v1"
    assert event["event_type"] == "chaser_profile_toolset_activation_write_guard"
    assert event["live_runtime_activated"] is False
    assert StudioService(tmp_path).get_approval(request["approval_id"]).status == "approved"
    assert not (tmp_path / "runtime" / "agent_bus").exists()

    duplicate = build_chaser_runtime_profile_toolset_activation_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="ops",
        expected_toolset_id="terminal-preview",
        write_profile_toolset_activation=True,
        confirm_profile_toolset_activation_record=True,
    )
    assert duplicate["ok"] is False
    assert "profile_toolset_activation_marker_already_present" in duplicate["blockers"]
    assert audit_path.read_text(encoding="utf-8").splitlines() == audit_lines


def _written_profile_toolset_activation_request(tmp_path: Path) -> dict:
    request = _ready_profile_toolset_activation_request(tmp_path)
    written = build_chaser_runtime_profile_toolset_activation_write_guard(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="ops",
        expected_toolset_id="terminal-preview",
        actor="operator",
        write_profile_toolset_activation=True,
        confirm_profile_toolset_activation_record=True,
    )
    assert written["ok"] is True
    request["written_profile_toolset_activation"] = written
    return request


def test_runtime_profile_toolset_activation_readiness_blocks_before_record(
    tmp_path: Path,
) -> None:
    request = _ready_profile_toolset_activation_request(tmp_path)

    result = build_chaser_runtime_profile_toolset_activation_readiness(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="ops",
        expected_toolset_id="terminal-preview",
    )

    assert result["ok"] is False
    assert result["surface"] == "chaser_runtime_profile_toolset_activation_readiness"
    assert result["schema_version"] == (
        "chaser_runtime_profile_toolset_activation_readiness.v1"
    )
    assert result["profile_toolset_activation_readiness_status"] == (
        "blocked_profile_toolset_activation_readiness"
    )
    assert "profile_toolset_activation_marker_missing" in result["blockers"]
    assert "profile_activation_state_missing" in result["blockers"]
    assert "toolset_activation_state_missing" in result["blockers"]
    assert result["ready_for_terminal_toolset_binding_design_next_pass"] is False
    assert result["terminal_toolset_binding_design_available"] is False
    assert result["writes_performed"] is False
    assert result["files_modified"] is False
    assert all(value is False for value in result["authority"].values())
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_profile_toolset_activation_readiness_reads_written_records(
    tmp_path: Path,
) -> None:
    request = _written_profile_toolset_activation_request(tmp_path)

    result = build_chaser_runtime_profile_toolset_activation_readiness(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="ops",
        expected_toolset_id="terminal-preview",
    )

    assert result["ok"] is True
    assert result["profile_toolset_activation_readiness_status"] == (
        "profile_toolset_activation_readiness_ready_terminal_binding_still_blocked"
    )
    assert result["ready_for_terminal_toolset_binding_design_next_pass"] is True
    assert result["profile_toolset_activation_marker"]["loaded"] is True
    assert result["profile_activation_state"]["loaded"] is True
    assert result["toolset_activation_state"]["loaded"] is True
    assert result["profile_toolset_activation_audit"]["matching_event_found"] is True
    assert all(check["ok"] is True for check in result["marker_checks"])
    assert all(check["ok"] is True for check in result["profile_state_checks"])
    assert all(check["ok"] is True for check in result["toolset_state_checks"])
    assert all(check["ok"] is True for check in result["audit_checks"])
    assert result["activation_performed"] is False
    assert result["live_runtime_activated"] is False
    assert result["terminal_binding_performed"] is False
    assert result["terminal_execution_performed"] is False
    assert result["writes_performed"] is False
    assert result["files_modified"] is False
    assert all(value is False for value in result["authority"].values())
    assert result["next_recommended_pass"] == (
        "terminal-n29-studio-full-terminal-product-contract"
    )
    assert StudioService(tmp_path).get_approval(request["approval_id"]).status == "approved"
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_runtime_profile_toolset_activation_readiness_blocks_missing_profile_state(
    tmp_path: Path,
) -> None:
    request = _written_profile_toolset_activation_request(tmp_path)
    written = request["written_profile_toolset_activation"]
    (tmp_path / written["profile_activation_state"]["path"]).unlink()

    result = build_chaser_runtime_profile_toolset_activation_readiness(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="ops",
        expected_toolset_id="terminal-preview",
    )

    assert result["ok"] is False
    assert "profile_activation_state_missing" in result["blockers"]
    assert result["ready_for_terminal_toolset_binding_design_next_pass"] is False
    assert result["writes_performed"] is False


def test_runtime_profile_toolset_activation_readiness_blocks_mutated_toolset_effects(
    tmp_path: Path,
) -> None:
    request = _written_profile_toolset_activation_request(tmp_path)
    written = request["written_profile_toolset_activation"]
    toolset_path = tmp_path / written["toolset_activation_state"]["path"]
    toolset_state = json.loads(toolset_path.read_text(encoding="utf-8"))
    toolset_state["toolset_activation_performed"] = True
    toolset_path.write_text(json.dumps(toolset_state), encoding="utf-8")

    result = build_chaser_runtime_profile_toolset_activation_readiness(
        tmp_path,
        request["approval_id"],
        expected_preview_id=request["activation_approval_preview_id"],
        expected_profile_id="ops",
        expected_toolset_id="terminal-preview",
    )

    assert result["ok"] is False
    assert "toolset_state_check_failed:toolset_state_effects_false" in result["blockers"]
    assert result["ready_for_terminal_toolset_binding_design_next_pass"] is False
    assert result["toolset_activation_state"]["loaded"] is True


def test_runtime_profile_toolset_activation_readiness_rejects_unsafe_or_missing_id(
    tmp_path: Path,
) -> None:
    unsafe = build_chaser_runtime_profile_toolset_activation_readiness(
        tmp_path,
        "../escape",
    )
    missing = build_chaser_runtime_profile_toolset_activation_readiness(
        tmp_path,
        "missing",
    )

    assert unsafe["ok"] is False
    assert "blocked_unsafe_activation_approval_id" in unsafe["blockers"]
    assert missing["ok"] is False
    assert "blocked_missing_activation_approval" in missing["blockers"]
    assert all(value is False for value in unsafe["authority"].values())
