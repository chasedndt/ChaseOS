from __future__ import annotations

from pathlib import Path

from runtime.agent_bus.bus import create_task, list_tasks
from runtime.chaser.board import (
    build_action_proposal,
    build_board_state,
    build_terminal_write_approval_request,
)
from runtime.chaser.terminal_write_executor_readiness import (
    build_terminal_write_executor_readiness,
)
from runtime.chaser.terminal_write_executor import execute_terminal_write_approval
from runtime.operator_surface import terminal_runs
from runtime.studio.service import ActionSpec, StudioService, StudioServiceError


def _card_types(board: dict) -> set[str]:
    return {str(card.get("type")) for card in board.get("cards", [])}


def test_board_state_empty_does_not_initialize_agent_bus(tmp_path: Path) -> None:
    board = build_board_state(tmp_path, include_gateway=False)

    assert board["ok"] is True
    assert board["surface"] == "chaser_orchestration_board"
    assert board["authority_summary"]["agent_bus_writes"] is False
    assert board["authority_summary"]["terminal_execution"] is False
    assert board["authority_summary"]["approval_consumption"] is False
    agent_bus = next(source for source in board["sources"] if source["source_id"] == "agent_bus")
    assert agent_bus["status"] == "not_initialized"
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_board_state_aggregates_terminal_run_and_pending_approval(tmp_path: Path) -> None:
    record = terminal_runs.build_run_record(
        command="pwd",
        cwd=str(tmp_path),
        classification={"action_class": "read_only_command", "allowed": True},
        policy_decision="executed",
        exit_code=0,
        stdout_excerpt="C:/repo",
    )
    terminal_runs.record_terminal_run(tmp_path, record)
    approval = StudioService(tmp_path).queue_for_approval(
        ActionSpec(
            action_type="write_file",
            target_path="07_LOGS/Operator-Briefs/example.md",
            content="example",
            metadata={"source_surface": "test"},
        )
    )

    board = build_board_state(tmp_path, include_gateway=False)

    assert {"terminal_run", "approval"} <= _card_types(board)
    terminal_card = next(card for card in board["cards"] if card["type"] == "terminal_run")
    assert terminal_card["data"]["run_id"] == record["run_id"]
    assert terminal_card["data"]["terminal_output_trusted"] is False
    assert terminal_card["actions"][0]["proposal_only"] is True
    assert terminal_card["actions"][0]["executes_now"] is False
    approval_card = next(card for card in board["cards"] if card["type"] == "approval")
    assert approval_card["title"] == approval.approval_id
    assert approval_card["status"] == "pending"
    assert approval_card["writes_now"] is False


def test_board_state_reads_existing_agent_bus_tasks_without_creating_tasks(tmp_path: Path) -> None:
    created = create_task(
        tmp_path,
        sender="Operator",
        recipient="Codex",
        intent="TASK",
        priority="normal",
        request="Inspect board",
        expected_output="read-only card",
        allow_external_sender=True,
    )
    assert created["created"] is True
    before = list_tasks(tmp_path)

    board = build_board_state(tmp_path, include_gateway=False)

    after = list_tasks(tmp_path)
    assert after == before
    task_card = next(card for card in board["cards"] if card["type"] == "agent_task")
    assert task_card["data"]["task_id"] == created["task_id"]
    assert board["authority_summary"]["agent_bus_writes"] is False


def test_board_state_gateway_card_is_read_only(tmp_path: Path) -> None:
    board = build_board_state(tmp_path, include_gateway=True)

    assert "gateway_diag" in _card_types(board)
    gateway = next(card for card in board["cards"] if card["type"] == "gateway_diag")
    assert gateway["data"]["authority"]["provider_calls"] is False
    assert gateway["data"]["authority"]["canonical_writeback"] is False
    assert gateway["executes_now"] is False


def test_board_action_proposal_terminal_read_only_preview_only(tmp_path: Path) -> None:
    proposal = build_action_proposal(
        tmp_path,
        action_type="terminal_command",
        command="pwd",
        cwd=tmp_path,
    )

    assert proposal["ok"] is True
    assert proposal["status"] == "preview_allowed"
    assert proposal["classification"]["action_class"] == "read_only_command"
    assert proposal["policy_decision"]["preview_allowed"] is True
    assert proposal["policy_decision"]["terminal_execution_allowed_now"] is False
    assert proposal["executes_now"] is False
    assert proposal["approval_queue_write_now"] is False
    assert proposal["agent_bus_write_now"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_board_action_proposal_write_command_is_future_n6_only(tmp_path: Path) -> None:
    proposal = build_action_proposal(
        tmp_path,
        action_type="terminal_command",
        command="mkdir example",
        cwd=tmp_path,
    )

    assert proposal["ok"] is True
    assert proposal["status"] == "approval_required_future_n6"
    assert proposal["classification"]["action_class"] == "write_command"
    assert proposal["policy_decision"]["approval_required"] is True
    assert proposal["policy_decision"]["n6_write_lane_required"] is True
    assert proposal["executes_now"] is False
    assert proposal["writes_now"] is False
    assert proposal["approval_queue_write_now"] is False
    assert not (tmp_path / "example").exists()


def test_board_action_proposal_blocks_shell_control(tmp_path: Path) -> None:
    proposal = build_action_proposal(
        tmp_path,
        action_type="terminal_command",
        command="pwd && whoami",
        cwd=tmp_path,
    )

    assert proposal["ok"] is False
    assert proposal["status"] == "blocked"
    assert proposal["classification"]["action_class"] == "blocked_shell_control_command"
    assert proposal["executes_now"] is False
    assert proposal["approval_queue_write_now"] is False


def test_terminal_write_approval_request_preview_does_not_write(tmp_path: Path) -> None:
    result = build_terminal_write_approval_request(
        tmp_path,
        command="mkdir example",
        cwd=tmp_path,
        write_request=False,
    )

    assert result["ok"] is True
    assert result["status"] == "ready_for_approval_request"
    assert result["approval_request_written"] is False
    assert result["executes_now"] is False
    assert result["approval_consumption_now"] is False
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "example").exists()


def test_terminal_write_approval_request_writes_pending_request_only(tmp_path: Path) -> None:
    result = build_terminal_write_approval_request(
        tmp_path,
        command="mkdir example",
        cwd=tmp_path,
        write_request=True,
    )

    assert result["ok"] is True
    assert result["status"] == "pending_approval_request_written"
    assert result["approval_request_written"] is True
    assert result["executes_now"] is False
    assert result["agent_bus_write_now"] is False
    approval_path = tmp_path / result["approval_path"]
    assert approval_path.exists()
    request = StudioService(tmp_path).get_approval(result["approval_id"])
    assert request is not None
    assert request.status == "pending"
    assert request.action_spec.metadata["terminal_write_lane_approval_request"] is True
    assert request.action_spec.metadata["terminal_write_executor_implemented"] is True
    assert request.action_spec.metadata["command"] == "mkdir example"
    assert not (tmp_path / "example").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_terminal_write_approval_request_duplicate_returns_existing_pending(tmp_path: Path) -> None:
    first = build_terminal_write_approval_request(
        tmp_path,
        command="mkdir example",
        cwd=tmp_path,
        write_request=True,
    )
    second = build_terminal_write_approval_request(
        tmp_path,
        command="mkdir example",
        cwd=tmp_path,
        write_request=True,
    )

    assert second["status"] == "existing_pending_approval_request"
    assert second["approval_id"] == first["approval_id"]
    assert second["approval_request_written"] is False
    assert len(StudioService(tmp_path).list_pending()) == 1


def test_terminal_write_approval_request_blocks_ineligible_commands(tmp_path: Path) -> None:
    read_only = build_terminal_write_approval_request(
        tmp_path,
        command="pwd",
        cwd=tmp_path,
        write_request=True,
    )
    shell_control = build_terminal_write_approval_request(
        tmp_path,
        command="pwd && whoami",
        cwd=tmp_path,
        write_request=True,
    )

    assert read_only["ok"] is False
    assert read_only["status"] == "blocked"
    assert "proposal_not_eligible:preview_allowed" in read_only["blocked_reasons"]
    assert shell_control["ok"] is False
    assert "proposal_not_eligible:blocked" in shell_control["blocked_reasons"]
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()


def test_terminal_write_approval_request_blocks_ambient_studio_execution(tmp_path: Path) -> None:
    result = build_terminal_write_approval_request(
        tmp_path,
        command="mkdir example",
        cwd=tmp_path,
        write_request=True,
    )
    service = StudioService(tmp_path)
    service.approve(result["approval_id"], reviewed_by="operator")

    try:
        service.execute_approved(result["approval_id"])
    except StudioServiceError as exc:
        assert "future governed N6 terminal write executor" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("ambient Studio execution should be blocked")

    assert not (tmp_path / "example").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_terminal_write_executor_readiness_rejects_unsafe_or_missing_approval_id(tmp_path: Path) -> None:
    unsafe = build_terminal_write_executor_readiness(
        tmp_path,
        approval_id="../approval",
    )
    missing = build_terminal_write_executor_readiness(
        tmp_path,
        approval_id="missing-approval",
    )

    assert unsafe["ok"] is False
    assert "unsafe_approval_id" in unsafe["blockers"]
    assert missing["ok"] is False
    assert "approval_request_missing" in missing["blockers"]
    assert unsafe["terminal_execution_now"] is False
    assert missing["approval_consumption_now"] is False


def test_terminal_write_executor_readiness_pending_approval_blocks_without_execution(tmp_path: Path) -> None:
    request = build_terminal_write_approval_request(
        tmp_path,
        command="mkdir example",
        cwd=tmp_path,
        write_request=True,
    )

    readiness = build_terminal_write_executor_readiness(
        tmp_path,
        approval_id=request["approval_id"],
    )

    assert readiness["ok"] is False
    assert readiness["readiness_status"] == "blocked"
    assert "approval_status_not_approved:pending" in readiness["blockers"]
    assert readiness["terminal_execution_now"] is False
    assert readiness["exact_once_marker_write_now"] is False
    assert readiness["approval_consumption_now"] is False
    assert not (tmp_path / "example").exists()


def test_terminal_write_executor_readiness_validates_approved_request_for_executor(tmp_path: Path) -> None:
    request = build_terminal_write_approval_request(
        tmp_path,
        command="mkdir example",
        cwd=tmp_path,
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    readiness = build_terminal_write_executor_readiness(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
    )

    assert readiness["ok"] is True
    assert readiness["scope_validation_ok"] is True
    assert readiness["readiness_status"] == "ready_for_executor"
    assert readiness["ready_for_future_executor_after_review"] is True
    assert readiness["terminal_write_executor_implemented"] is True
    assert readiness["ready_for_execution_now"] is True
    assert readiness["remaining_gates"] == []
    assert readiness["fresh_proposal"]["proposal_id"] == request["proposal_id"]
    assert readiness["classification"]["action_class"] == "write_command"
    assert readiness["authority"]["terminal_execution_now"] is False
    assert readiness["authority"]["approval_consumption_now"] is False
    assert readiness["authority"]["agent_bus_write_now"] is False
    assert not (tmp_path / "example").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_terminal_write_executor_readiness_blocks_existing_exact_once_marker(tmp_path: Path) -> None:
    request = build_terminal_write_approval_request(
        tmp_path,
        command="mkdir example",
        cwd=tmp_path,
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")
    preview = build_terminal_write_executor_readiness(
        tmp_path,
        approval_id=request["approval_id"],
    )
    marker_path = tmp_path / preview["exact_once_marker_path"]
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text('{"reserved": true}', encoding="utf-8")

    readiness = build_terminal_write_executor_readiness(
        tmp_path,
        approval_id=request["approval_id"],
    )

    assert readiness["ok"] is False
    assert "exact_once_marker_already_present" in readiness["blockers"]
    assert readiness["terminal_execution_now"] is False
    assert not (tmp_path / "example").exists()


def test_terminal_write_executor_requires_explicit_confirmation(tmp_path: Path) -> None:
    request = build_terminal_write_approval_request(
        tmp_path,
        command="mkdir example",
        cwd=tmp_path,
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = execute_terminal_write_approval(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
    )

    assert result["ok"] is False
    assert "explicit_approved_terminal_write_confirmation_required" in result["blockers"]
    assert result["authority"]["terminal_execution_now"] is False
    assert not (tmp_path / "example").exists()
    assert not (tmp_path / "07_LOGS" / "Terminal-Runs" / "_execution_markers").exists()


def test_terminal_write_executor_consumes_approved_mkdir_once(tmp_path: Path) -> None:
    request = build_terminal_write_approval_request(
        tmp_path,
        command="mkdir example",
        cwd=tmp_path,
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = execute_terminal_write_approval(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
        confirm_approved_terminal_write=True,
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert result["authority"]["terminal_execution_now"] is True
    assert result["authority"]["approval_consumption_now"] is True
    assert result["authority"]["exact_once_marker_write_now"] is True
    assert result["authority"]["terminal_audit_write_now"] is True
    assert result["authority"]["agent_bus_write_now"] is False
    assert result["authority"]["provider_call_now"] is False
    assert result["authority"]["canonical_writeback_now"] is False
    assert (tmp_path / "example").is_dir()
    assert (tmp_path / result["exact_once_marker_path"]).exists()
    assert Path(result["audit_paths"]["json"]).exists()

    approval = StudioService(tmp_path).get_approval(request["approval_id"])
    assert approval is not None
    assert approval.status == "executed"
    assert approval.result_action_id == result["run_id"]

    duplicate = execute_terminal_write_approval(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
        confirm_approved_terminal_write=True,
    )
    assert duplicate["ok"] is False
    assert "approval_status_not_approved:executed" in duplicate["blockers"]
    assert duplicate["authority"]["terminal_execution_now"] is False


def test_terminal_write_executor_blocks_pending_without_marker_or_execution(tmp_path: Path) -> None:
    request = build_terminal_write_approval_request(
        tmp_path,
        command="mkdir example",
        cwd=tmp_path,
        write_request=True,
    )

    result = execute_terminal_write_approval(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
        confirm_approved_terminal_write=True,
    )

    assert result["ok"] is False
    assert "approval_status_not_approved:pending" in result["blockers"]
    assert not (tmp_path / "example").exists()
    assert not (tmp_path / "07_LOGS" / "Terminal-Runs" / "_execution_markers").exists()


def test_terminal_write_executor_blocks_out_of_vault_target_before_consumption(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-terminal-executor-test"
    request = build_terminal_write_approval_request(
        tmp_path,
        command=f'mkdir "{outside}"',
        cwd=tmp_path,
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = execute_terminal_write_approval(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
        confirm_approved_terminal_write=True,
    )

    assert result["ok"] is False
    assert any("target path escapes vault root" in reason for reason in result["blockers"])
    assert not outside.exists()
    assert not (tmp_path / "07_LOGS" / "Terminal-Runs" / "_execution_markers").exists()
    approval = StudioService(tmp_path).get_approval(request["approval_id"])
    assert approval is not None
    assert approval.status == "approved"


def test_terminal_write_executor_consumes_approved_touch_once(tmp_path: Path) -> None:
    request = build_terminal_write_approval_request(
        tmp_path,
        command="touch example.txt",
        cwd=tmp_path,
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = execute_terminal_write_approval(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
        confirm_approved_terminal_write=True,
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert result["supported_write_executable"] == "touch"
    assert result["authority"]["terminal_execution_now"] is True
    assert result["authority"]["approval_consumption_now"] is True
    assert result["authority"]["exact_once_marker_write_now"] is True
    assert result["authority"]["terminal_audit_write_now"] is True
    assert result["authority"]["agent_bus_write_now"] is False
    assert result["authority"]["provider_call_now"] is False
    assert result["authority"]["canonical_writeback_now"] is False
    assert (tmp_path / "example.txt").is_file()
    assert (tmp_path / "example.txt").read_text(encoding="utf-8") == ""
    assert (tmp_path / result["exact_once_marker_path"]).exists()
    assert Path(result["audit_paths"]["json"]).exists()

    approval = StudioService(tmp_path).get_approval(request["approval_id"])
    assert approval is not None
    assert approval.status == "executed"
    assert approval.result_action_id == result["run_id"]

    duplicate = execute_terminal_write_approval(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
        confirm_approved_terminal_write=True,
    )
    assert duplicate["ok"] is False
    assert "approval_status_not_approved:executed" in duplicate["blockers"]
    assert duplicate["authority"]["terminal_execution_now"] is False


def test_terminal_write_executor_touch_missing_parent_fails_after_marker(tmp_path: Path) -> None:
    request = build_terminal_write_approval_request(
        tmp_path,
        command="touch missing-parent/example.txt",
        cwd=tmp_path,
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = execute_terminal_write_approval(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
        confirm_approved_terminal_write=True,
    )

    assert result["ok"] is False
    assert result["status"] == "execution_failed"
    assert result["supported_write_executable"] == "touch"
    assert "target parent does not exist" in result["stderr"]
    assert result["authority"]["terminal_execution_now"] is True
    assert result["authority"]["approval_consumption_now"] is True
    assert result["authority"]["exact_once_marker_write_now"] is True
    assert result["authority"]["terminal_audit_write_now"] is True
    assert result["authority"]["host_mutation_now"] is False
    assert not (tmp_path / "missing-parent" / "example.txt").exists()
    assert (tmp_path / result["exact_once_marker_path"]).exists()
    approval = StudioService(tmp_path).get_approval(request["approval_id"])
    assert approval is not None
    assert approval.status == "execution_failed"


def test_terminal_write_executor_consumes_approved_copy_once(tmp_path: Path) -> None:
    (tmp_path / "source.txt").write_text("copy me\n", encoding="utf-8")
    request = build_terminal_write_approval_request(
        tmp_path,
        command="copy source.txt dest.txt",
        cwd=tmp_path,
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = execute_terminal_write_approval(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
        confirm_approved_terminal_write=True,
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert result["supported_write_executable"] == "copy"
    assert result["source_path"] == "source.txt"
    assert result["target_path"] == "dest.txt"
    assert result["authority"]["terminal_execution_now"] is True
    assert result["authority"]["approval_consumption_now"] is True
    assert result["authority"]["exact_once_marker_write_now"] is True
    assert result["authority"]["terminal_audit_write_now"] is True
    assert result["authority"]["agent_bus_write_now"] is False
    assert result["authority"]["provider_call_now"] is False
    assert result["authority"]["canonical_writeback_now"] is False
    assert (tmp_path / "source.txt").read_text(encoding="utf-8") == "copy me\n"
    assert (tmp_path / "dest.txt").read_text(encoding="utf-8") == "copy me\n"
    assert (tmp_path / result["exact_once_marker_path"]).exists()
    assert Path(result["audit_paths"]["json"]).exists()

    approval = StudioService(tmp_path).get_approval(request["approval_id"])
    assert approval is not None
    assert approval.status == "executed"
    assert approval.result_action_id == result["run_id"]

    duplicate = execute_terminal_write_approval(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
        confirm_approved_terminal_write=True,
    )
    assert duplicate["ok"] is False
    assert "approval_status_not_approved:executed" in duplicate["blockers"]
    assert duplicate["authority"]["terminal_execution_now"] is False


def test_terminal_write_executor_copy_missing_source_blocks_before_consumption(tmp_path: Path) -> None:
    request = build_terminal_write_approval_request(
        tmp_path,
        command="copy missing.txt dest.txt",
        cwd=tmp_path,
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = execute_terminal_write_approval(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
        confirm_approved_terminal_write=True,
    )

    assert result["ok"] is False
    assert any("source file does not exist" in reason for reason in result["blockers"])
    assert not (tmp_path / "dest.txt").exists()
    assert not (tmp_path / "07_LOGS" / "Terminal-Runs" / "_execution_markers").exists()
    approval = StudioService(tmp_path).get_approval(request["approval_id"])
    assert approval is not None
    assert approval.status == "approved"


def test_terminal_write_executor_blocks_unsupported_write_command_before_consumption(tmp_path: Path) -> None:
    request = build_terminal_write_approval_request(
        tmp_path,
        command="mv source.txt dest.txt",
        cwd=tmp_path,
        write_request=True,
    )
    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    result = execute_terminal_write_approval(
        tmp_path,
        approval_id=request["approval_id"],
        expected_proposal_id=request["proposal_id"],
        confirm_approved_terminal_write=True,
    )

    assert result["ok"] is False
    assert "unsupported_n6_write_executable:mv" in result["blockers"]
    assert not (tmp_path / "dest.txt").exists()
    assert not (tmp_path / "07_LOGS" / "Terminal-Runs" / "_execution_markers").exists()
    approval = StudioService(tmp_path).get_approval(request["approval_id"])
    assert approval is not None
    assert approval.status == "approved"
