from __future__ import annotations

import json
from pathlib import Path

from runtime.cli import main as cli
from runtime.chaser.runtime_activation_approval_request import (
    build_chaser_runtime_activation_approval_request,
)
from runtime.studio.service import StudioService


def _decode_cli_result(output: str) -> dict:
    envelope = json.loads(output)
    result = envelope["result"]
    if isinstance(result, dict) and "raw_stdout" not in result:
        return result
    return json.loads(result["raw_stdout"])


def test_chaser_runtime_activation_approval_preview_cli_is_read_only(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-preview",
            "--profile",
            "ops",
            "--toolset",
            "terminal-preview",
            "--operator-intent",
            "activate local preview after approval",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_activation_approval_preview"
    assert result["preview_status"] == "preview_ready_no_write"
    assert result["approval_request_written"] is False
    assert result["ready_to_write_activation_request_now"] is False
    assert result["authority"]["runtime_activation_now"] is False
    assert result["authority"]["approval_queue_write_now"] is False
    assert result["authority"]["approval_consumption_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert result["authority"]["provider_call_now"] is False
    assert result["approval_request_preview"]["operator_intent"] == (
        "activate local preview after approval"
    )
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_approval_preview_cli_blocks_provider_dispatch(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-preview",
            "--request-provider-dispatch",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert result["ok"] is False
    assert result["preview_status"] == "preview_blocked"
    assert "provider_dispatch_requires_separate_gate" in result["blockers"]
    assert result["approval_request_written"] is False
    assert result["authority"]["provider_call_now"] is False
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()


def test_chaser_runtime_activation_approval_preview_cli_blocks_unknown_toolset(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-preview",
            "--toolset",
            "missing",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert result["ok"] is False
    assert "activation_gate_design_not_ready" in result["blockers"]
    assert "unknown_toolset:missing" in result["blockers"]
    assert result["authority"]["runtime_activation_now"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_approval_request_cli_defaults_to_preview(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-request",
            "--operator-intent",
            "activate after approval",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_activation_approval_request_write_gate"
    assert result["request_status"] == "ready_for_activation_approval_request"
    assert result["approval_request_written"] is False
    assert result["authority"]["approval_queue_write_now"] is False
    assert result["authority"]["runtime_activation_now"] is False
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_approval_request_cli_write_queues_only(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-request",
            "--operator-intent",
            "activate after approval",
            "--write-approval-request",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["request_status"] == "pending_activation_approval_request_written"
    assert result["approval_request_written"] is True
    assert result["approval_id"]
    assert (tmp_path / result["approval_path"]).exists()
    assert result["authority"]["approval_queue_write_now"] is True
    assert result["authority"]["approval_consumption_now"] is False
    assert result["authority"]["terminal_execution_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert result["authority"]["provider_call_now"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_approval_request_cli_blocks_provider_dispatch(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-request",
            "--request-provider-dispatch",
            "--write-approval-request",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert result["ok"] is False
    assert result["request_status"] == "blocked"
    assert "provider_dispatch_requires_separate_gate" in result["blockers"]
    assert result["approval_request_written"] is False
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()


def test_chaser_runtime_activation_approval_decision_preflight_cli_reports_pending(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-decision-preflight",
            request["approval_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["surface"] == "chaser_runtime_activation_approval_decision_preflight"
    assert result["decision_preflight_status"] == "blocked_pending_activation_approval"
    assert result["approval_status"] == "pending"
    assert result["approval_status_mutated"] is False
    assert result["approval_consumed"] is False
    assert result["authority"]["approval_consumption_now"] is False
    assert result["authority"]["runtime_activation_now"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_approval_decision_preflight_cli_accepts_approved(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-decision-preflight",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["decision_preflight_status"] == (
        "activation_approval_decision_preflight_ready_no_mutation"
    )
    assert result["approval_status"] == "approved"
    assert result["ready_for_activation_consumer_next_pass"] is True
    assert result["activation_approval_consumption_available"] is False
    assert result["runtime_activation_now"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_approval_decision_preflight_cli_rejects_unsafe_id(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-decision-preflight",
            "../escape",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert result["ok"] is False
    assert result["decision_preflight_status"] == "blocked_unsafe_activation_approval_id"
    assert result["authority"]["approval_consumption_now"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_approval_consumption_design_cli_reports_pending(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-design",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["surface"] == "chaser_runtime_activation_approval_consumption_design"
    assert result["consumption_design_status"] == (
        "blocked_activation_approval_consumption_design_preflight_not_approved"
    )
    assert result["approval_status"] == "pending"
    assert result["ready_for_activation_consumption_write_guard_next_pass"] is False
    assert result["approval_consumed"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["authority"]["approval_consumption_now"] is False
    assert result["authority"]["runtime_activation_now"] is False
    assert not (tmp_path / result["consumer_marker_preview"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_approval_consumption_design_cli_accepts_approved(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-design",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--actor",
            "operator",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["consumption_design_status"] == (
        "activation_approval_consumption_design_ready_no_mutation"
    )
    assert result["approval_status"] == "approved"
    assert result["ready_for_activation_consumption_write_guard_next_pass"] is True
    assert result["activation_approval_consumption_available"] is False
    assert result["activation_performed"] is False
    assert result["authority"]["exact_once_marker_write_now"] is False
    assert not (tmp_path / result["consumer_marker_preview"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_approval_consumption_design_cli_rejects_unsafe_id(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-design",
            "../escape",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert result["ok"] is False
    assert result["decision_preflight"]["decision_preflight_status"] == (
        "blocked_unsafe_activation_approval_id"
    )
    assert result["authority"]["approval_consumption_now"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_approval_consumption_write_guard_cli_previews_approved(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["surface"] == "chaser_runtime_activation_approval_consumption_write_guard"
    assert result["write_guard_status"] == (
        "activation_approval_consumption_write_guard_ready_no_write"
    )
    assert result["write_consumption_marker_requested"] is False
    assert result["approval_consumed"] is False
    assert result["activation_consumption_marker_written"] is False
    assert result["authority"]["approval_consumption_now"] is False
    assert not (tmp_path / result["exact_once_marker"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_approval_consumption_write_guard_cli_requires_confirmation(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-consumption-marker",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert "explicit_activation_approval_consumption_confirmation_required" in result["blockers"]
    assert result["approval_consumed"] is False
    assert result["activation_consumption_marker_written"] is False
    assert not (tmp_path / result["exact_once_marker"]["path"]).exists()


def test_chaser_runtime_activation_approval_consumption_write_guard_cli_writes_marker_and_audit_once(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-consumption-marker",
            "--confirm-activation-approval-consumption",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["write_guard_status"] == (
        "activation_approval_consumption_marker_and_audit_written_activation_blocked"
    )
    assert result["approval_consumed"] is True
    assert result["approval_status_after"] == "approved"
    assert result["approval_status_mutated"] is False
    assert result["activation_consumption_marker_written"] is True
    assert result["activation_audit_written"] is True
    assert result["activation_performed"] is False
    assert result["authority"]["approval_consumption_now"] is True
    assert result["authority"]["exact_once_marker_write_now"] is True
    assert result["authority"]["activation_audit_write_now"] is True
    assert result["authority"]["runtime_activation_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    marker_path = tmp_path / result["exact_once_marker"]["path"]
    audit_path = tmp_path / result["activation_audit"]["path"]
    assert marker_path.exists()
    assert audit_path.exists()
    assert StudioService(tmp_path).get_approval(request["approval_id"]).status == "approved"
    assert not (tmp_path / "runtime" / "agent_bus").exists()

    duplicate_exit = cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-consumption-marker",
            "--confirm-activation-approval-consumption",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    duplicate = _decode_cli_result(capsys.readouterr().out)
    assert duplicate_exit == 2
    assert "exact_once_marker_already_present" in duplicate["blockers"]


def test_chaser_runtime_activation_post_consumption_readiness_cli_reads_consumed_pair(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-consumption-marker",
            "--confirm-activation-approval-consumption",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-post-consumption-readiness",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["surface"] == "chaser_runtime_activation_post_consumption_readiness"
    assert result["ready_for_activation_executor_next_pass"] is True
    assert result["activation_executor_available"] is False
    assert result["activation_allowed"] is False
    assert result["authority"]["runtime_activation_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert result["activation_audit"]["matching_event_found"] is True
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_post_consumption_readiness_cli_blocks_without_marker(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-post-consumption-readiness",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert "activation_consumption_marker_missing" in result["blockers"]
    assert result["ready_for_activation_executor_next_pass"] is False
    assert all(value is False for value in result["authority"].values())


def test_chaser_runtime_activation_executor_design_cli_reads_consumed_pair(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-consumption-marker",
            "--confirm-activation-approval-consumption",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-executor-design",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["surface"] == "chaser_runtime_activation_executor_design"
    assert result["ready_for_activation_executor_write_guard_next_pass"] is True
    assert result["activation_executor_available"] is False
    assert result["activation_executor_write_guard_available"] is True
    assert result["activation_allowed"] is False
    assert result["terminal_binding_allowed_in_activation_executor"] is False
    assert result["authority"]["runtime_activation_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert not (tmp_path / result["future_activation_state_preview"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_executor_design_cli_blocks_without_readiness(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-executor-design",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert "post_consumption_readiness_not_ready" in result["blockers"]
    assert result["ready_for_activation_executor_write_guard_next_pass"] is False
    assert all(value is False for value in result["authority"].values())


def test_chaser_runtime_activation_executor_write_guard_cli_writes_record_once(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-consumption-marker",
            "--confirm-activation-approval-consumption",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-executor-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-activation-state",
            "--confirm-runtime-activation-record",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["surface"] == "chaser_runtime_activation_executor_write_guard"
    assert result["activation_marker_written"] is True
    assert result["activation_state_written"] is True
    assert result["activation_audit_written"] is True
    assert result["activation_performed"] is False
    assert result["live_runtime_activated"] is False
    assert result["terminal_binding_performed"] is False
    assert result["authority"]["activation_state_write_now"] is True
    assert result["authority"]["runtime_activation_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert (tmp_path / result["runtime_activation_marker"]["path"]).exists()
    assert (tmp_path / result["runtime_activation_state"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()

    duplicate_exit = cli.main(
        [
            "chaser",
            "runtime",
            "activation-executor-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-activation-state",
            "--confirm-runtime-activation-record",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    duplicate = _decode_cli_result(capsys.readouterr().out)
    assert duplicate_exit == 2
    assert "runtime_activation_marker_already_present" in duplicate["blockers"]


def test_chaser_runtime_activation_executor_write_guard_cli_blocks_without_readiness(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-executor-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-activation-state",
            "--confirm-runtime-activation-record",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert "post_consumption_readiness_not_ready" in result["blockers"]
    assert result["activation_marker_written"] is False
    assert result["activation_state_written"] is False
    assert result["activation_audit_written"] is False
    assert result["authority"]["activation_state_write_now"] is False


def test_chaser_runtime_activation_state_readiness_cli_reads_written_record(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-consumption-marker",
            "--confirm-activation-approval-consumption",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-executor-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-activation-state",
            "--confirm-runtime-activation-record",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-state-readiness",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["surface"] == "chaser_runtime_activation_state_readiness"
    assert result["ready_for_profile_toolset_activation_design_next_pass"] is True
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["live_runtime_activated"] is False
    assert result["runtime_activation_now"] is False
    assert result["terminal_binding_now"] is False
    assert result["runtime_activation_audit"]["matching_event_found"] is True
    assert all(value is False for value in result["authority"].values())
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_state_readiness_cli_blocks_without_record(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-consumption-marker",
            "--confirm-activation-approval-consumption",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-state-readiness",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert "runtime_activation_marker_missing" in result["blockers"]
    assert "runtime_activation_state_missing" in result["blockers"]
    assert result["ready_for_profile_toolset_activation_design_next_pass"] is False
    assert result["activation_allowed"] is False
    assert all(value is False for value in result["authority"].values())


def test_chaser_runtime_profile_toolset_activation_design_cli_reads_n25_state(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-consumption-marker",
            "--confirm-activation-approval-consumption",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-executor-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-activation-state",
            "--confirm-runtime-activation-record",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "profile-toolset-activation-design",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--expected-profile",
            "ops",
            "--expected-toolset",
            "terminal-preview",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["surface"] == "chaser_runtime_profile_toolset_activation_design"
    assert result["ready_for_profile_toolset_activation_write_guard_next_pass"] is True
    assert result["profile_toolset_activation_write_guard_available"] is True
    assert result["activation_allowed"] is False
    assert result["activation_performed"] is False
    assert result["profile_activation_now"] is False
    assert result["toolset_activation_now"] is False
    assert result["terminal_binding_now"] is False
    assert result["writes_performed"] is False
    assert all(value is False for value in result["authority"].values())
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_profile_toolset_activation_design_cli_blocks_without_n25(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "profile-toolset-activation-design",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert "activation_state_readiness_not_ready" in result["blockers"]
    assert result["ready_for_profile_toolset_activation_write_guard_next_pass"] is False
    assert result["activation_allowed"] is False
    assert all(value is False for value in result["authority"].values())


def test_chaser_runtime_profile_toolset_activation_write_guard_cli_writes_once(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-consumption-marker",
            "--confirm-activation-approval-consumption",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-executor-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-activation-state",
            "--confirm-runtime-activation-record",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "profile-toolset-activation-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--expected-profile",
            "ops",
            "--expected-toolset",
            "terminal-preview",
            "--write-profile-toolset-activation",
            "--confirm-profile-toolset-activation-record",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["surface"] == "chaser_runtime_profile_toolset_activation_write_guard"
    assert result["write_guard_status"] == (
        "profile_toolset_activation_marker_state_and_audit_written_"
        "live_runtime_blocked"
    )
    assert result["profile_toolset_activation_marker_written"] is True
    assert result["profile_activation_state_written"] is True
    assert result["toolset_activation_state_written"] is True
    assert result["profile_toolset_activation_audit_written"] is True
    assert result["live_runtime_activated"] is False
    assert result["terminal_binding_performed"] is False
    assert result["authority"]["profile_activation_state_write_now"] is True
    assert result["authority"]["profile_activation_now"] is False
    assert result["authority"]["terminal_execution_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert (tmp_path / result["profile_toolset_activation_marker"]["path"]).exists()
    assert (tmp_path / result["profile_activation_state"]["path"]).exists()
    assert (tmp_path / result["toolset_activation_state"]["path"]).exists()
    assert (tmp_path / result["profile_toolset_activation_audit"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()

    duplicate_code = cli.main(
        [
            "chaser",
            "runtime",
            "profile-toolset-activation-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--expected-profile",
            "ops",
            "--expected-toolset",
            "terminal-preview",
            "--write-profile-toolset-activation",
            "--confirm-profile-toolset-activation-record",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    duplicate = _decode_cli_result(capsys.readouterr().out)
    assert duplicate_code == 2
    assert "profile_toolset_activation_marker_already_present" in duplicate["blockers"]


def test_chaser_runtime_profile_toolset_activation_write_guard_cli_blocks_without_n25(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "profile-toolset-activation-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--expected-profile",
            "ops",
            "--expected-toolset",
            "terminal-preview",
            "--write-profile-toolset-activation",
            "--confirm-profile-toolset-activation-record",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert result["write_guard_status"] == "blocked_profile_toolset_activation_write_guard"
    assert "activation_state_readiness_not_ready" in result["blockers"]
    assert result["profile_toolset_activation_marker_written"] is False
    assert result["profile_activation_state_written"] is False
    assert result["toolset_activation_state_written"] is False
    assert result["authority"]["profile_activation_state_write_now"] is False
    assert not (tmp_path / result["profile_activation_state"]["path"]).exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_profile_toolset_activation_readiness_cli_reads_written_record(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-consumption-marker",
            "--confirm-activation-approval-consumption",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-executor-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-activation-state",
            "--confirm-runtime-activation-record",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()
    cli.main(
        [
            "chaser",
            "runtime",
            "profile-toolset-activation-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--expected-profile",
            "ops",
            "--expected-toolset",
            "terminal-preview",
            "--write-profile-toolset-activation",
            "--confirm-profile-toolset-activation-record",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "profile-toolset-activation-readiness",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--expected-profile",
            "ops",
            "--expected-toolset",
            "terminal-preview",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["surface"] == "chaser_runtime_profile_toolset_activation_readiness"
    assert result["profile_toolset_activation_readiness_status"] == (
        "profile_toolset_activation_readiness_ready_terminal_binding_still_blocked"
    )
    assert result["ready_for_terminal_toolset_binding_design_next_pass"] is True
    assert result["profile_toolset_activation_audit"]["matching_event_found"] is True
    assert result["activation_performed"] is False
    assert result["terminal_binding_performed"] is False
    assert all(value is False for value in result["authority"].values())
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_profile_toolset_activation_readiness_cli_blocks_without_n27(
    tmp_path: Path,
    capsys,
) -> None:
    request = build_chaser_runtime_activation_approval_request(
        tmp_path,
        operator_intent="activate after approval",
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-approval-consumption-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-consumption-marker",
            "--confirm-activation-approval-consumption",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()
    cli.main(
        [
            "chaser",
            "runtime",
            "activation-executor-write-guard",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--write-activation-state",
            "--confirm-runtime-activation-record",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "profile-toolset-activation-readiness",
            request["approval_id"],
            "--expected-preview-id",
            request["activation_approval_preview_id"],
            "--expected-profile",
            "ops",
            "--expected-toolset",
            "terminal-preview",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert result["profile_toolset_activation_readiness_status"] == (
        "blocked_profile_toolset_activation_readiness"
    )
    assert "profile_toolset_activation_marker_missing" in result["blockers"]
    assert "profile_activation_state_missing" in result["blockers"]
    assert result["ready_for_terminal_toolset_binding_design_next_pass"] is False
    assert result["writes_performed"] is False
    assert all(value is False for value in result["authority"].values())

