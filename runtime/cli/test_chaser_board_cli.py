from __future__ import annotations

import json
from pathlib import Path

from runtime.cli import main as cli
from runtime.operator_surface import terminal_runs


def _decode_cli_result(output: str) -> dict:
    envelope = json.loads(output)
    result = envelope["result"]
    if isinstance(result, dict) and "raw_stdout" not in result:
        return result
    return json.loads(result["raw_stdout"])


def test_chaser_board_state_cli_is_read_only(tmp_path: Path, capsys) -> None:
    record = terminal_runs.build_run_record(
        command="pwd",
        cwd=str(tmp_path),
        classification={"action_class": "read_only_command", "allowed": True},
        policy_decision="executed",
        exit_code=0,
    )
    terminal_runs.record_terminal_run(tmp_path, record)

    exit_code = cli.main(
        [
            "chaser",
            "board",
            "state",
            "--vault-root",
            str(tmp_path),
            "--skip-gateway",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    result = _decode_cli_result(captured.out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["authority_summary"]["terminal_execution"] is False
    assert result["authority_summary"]["provider_calls"] is False
    assert result["authority_summary"]["agent_bus_writes"] is False
    assert any(card["type"] == "terminal_run" for card in result["cards"])
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_board_propose_terminal_command_cli_is_preview_only(tmp_path: Path, capsys) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "board",
            "propose",
            "terminal-command",
            "mkdir example",
            "--cwd",
            str(tmp_path),
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    captured = capsys.readouterr()
    result = _decode_cli_result(captured.out)

    assert exit_code == 0
    assert result["status"] == "approval_required_future_n6"
    assert result["classification"]["action_class"] == "write_command"
    assert result["executes_now"] is False
    assert result["writes_now"] is False
    assert result["approval_queue_write_now"] is False
    assert result["agent_bus_write_now"] is False
    assert not (tmp_path / "example").exists()
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()


def test_chaser_board_request_terminal_approval_cli_preview_is_no_write(tmp_path: Path, capsys) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "board",
            "request-terminal-approval",
            "mkdir example",
            "--cwd",
            str(tmp_path),
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    captured = capsys.readouterr()
    result = _decode_cli_result(captured.out)

    assert exit_code == 0
    assert result["status"] == "ready_for_approval_request"
    assert result["approval_request_written"] is False
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "example").exists()


def test_chaser_board_request_terminal_approval_cli_write_flag_queues_only(tmp_path: Path, capsys) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "board",
            "request-terminal-approval",
            "mkdir example",
            "--cwd",
            str(tmp_path),
            "--vault-root",
            str(tmp_path),
            "--write-approval-request",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    result = _decode_cli_result(captured.out)

    assert exit_code == 0
    assert result["status"] == "pending_approval_request_written"
    assert result["approval_request_written"] is True
    assert (tmp_path / result["approval_path"]).exists()
    assert result["executes_now"] is False
    assert result["approval_consumption_now"] is False
    assert result["agent_bus_write_now"] is False
    assert not (tmp_path / "example").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_board_terminal_executor_readiness_cli_is_no_execution(tmp_path: Path, capsys) -> None:
    write_exit = cli.main(
        [
            "chaser",
            "board",
            "request-terminal-approval",
            "mkdir example",
            "--cwd",
            str(tmp_path),
            "--vault-root",
            str(tmp_path),
            "--write-approval-request",
            "--json",
        ]
    )
    write_result = _decode_cli_result(capsys.readouterr().out)
    assert write_exit == 0

    from runtime.studio.service import StudioService

    StudioService(tmp_path).approve(write_result["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "board",
            "terminal-executor-readiness",
            write_result["approval_id"],
            "--expected-proposal-id",
            write_result["proposal_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    captured = capsys.readouterr()
    result = _decode_cli_result(captured.out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["readiness_status"] == "ready_for_executor"
    assert result["ready_for_execution_now"] is True
    assert result["terminal_execution_now"] is False
    assert result["approval_consumption_now"] is False
    assert result["exact_once_marker_write_now"] is False
    assert not (tmp_path / "example").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_board_terminal_executor_readiness_cli_blocks_pending(tmp_path: Path, capsys) -> None:
    cli.main(
        [
            "chaser",
            "board",
            "request-terminal-approval",
            "mkdir example",
            "--cwd",
            str(tmp_path),
            "--vault-root",
            str(tmp_path),
            "--write-approval-request",
            "--json",
        ]
    )
    write_result = _decode_cli_result(capsys.readouterr().out)

    exit_code = cli.main(
        [
            "chaser",
            "board",
            "terminal-executor-readiness",
            write_result["approval_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert "approval_status_not_approved:pending" in result["blockers"]
    assert result["terminal_execution_now"] is False
    assert not (tmp_path / "example").exists()


def test_chaser_board_execute_terminal_approval_cli_requires_confirmation(tmp_path: Path, capsys) -> None:
    cli.main(
        [
            "chaser",
            "board",
            "request-terminal-approval",
            "mkdir example",
            "--cwd",
            str(tmp_path),
            "--vault-root",
            str(tmp_path),
            "--write-approval-request",
            "--json",
        ]
    )
    request = _decode_cli_result(capsys.readouterr().out)

    from runtime.studio.service import StudioService

    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "board",
            "execute-terminal-approval",
            request["approval_id"],
            "--expected-proposal-id",
            request["proposal_id"],
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert "explicit_approved_terminal_write_confirmation_required" in result["blockers"]
    assert not (tmp_path / "example").exists()


def test_chaser_board_execute_terminal_approval_cli_consumes_once(tmp_path: Path, capsys) -> None:
    cli.main(
        [
            "chaser",
            "board",
            "request-terminal-approval",
            "mkdir example",
            "--cwd",
            str(tmp_path),
            "--vault-root",
            str(tmp_path),
            "--write-approval-request",
            "--json",
        ]
    )
    request = _decode_cli_result(capsys.readouterr().out)

    from runtime.studio.service import StudioService

    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "board",
            "execute-terminal-approval",
            request["approval_id"],
            "--expected-proposal-id",
            request["proposal_id"],
            "--vault-root",
            str(tmp_path),
            "--confirm-approved-terminal-write",
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["status"] == "executed"
    assert result["authority"]["approval_consumption_now"] is True
    assert result["authority"]["terminal_audit_write_now"] is True
    assert result["authority"]["agent_bus_write_now"] is False
    assert (tmp_path / "example").is_dir()
    assert (tmp_path / result["exact_once_marker_path"]).exists()

    duplicate_exit = cli.main(
        [
            "chaser",
            "board",
            "execute-terminal-approval",
            request["approval_id"],
            "--expected-proposal-id",
            request["proposal_id"],
            "--vault-root",
            str(tmp_path),
            "--confirm-approved-terminal-write",
            "--json",
        ]
    )
    duplicate = _decode_cli_result(capsys.readouterr().out)

    assert duplicate_exit == 2
    assert "approval_status_not_approved:executed" in duplicate["blockers"]


def test_chaser_board_execute_terminal_approval_cli_consumes_touch_once(tmp_path: Path, capsys) -> None:
    cli.main(
        [
            "chaser",
            "board",
            "request-terminal-approval",
            "touch example.txt",
            "--cwd",
            str(tmp_path),
            "--vault-root",
            str(tmp_path),
            "--write-approval-request",
            "--json",
        ]
    )
    request = _decode_cli_result(capsys.readouterr().out)

    from runtime.studio.service import StudioService

    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "board",
            "execute-terminal-approval",
            request["approval_id"],
            "--expected-proposal-id",
            request["proposal_id"],
            "--vault-root",
            str(tmp_path),
            "--confirm-approved-terminal-write",
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["status"] == "executed"
    assert result["supported_write_executable"] == "touch"
    assert result["authority"]["approval_consumption_now"] is True
    assert result["authority"]["terminal_audit_write_now"] is True
    assert result["authority"]["agent_bus_write_now"] is False
    assert (tmp_path / "example.txt").is_file()
    assert (tmp_path / result["exact_once_marker_path"]).exists()

    duplicate_exit = cli.main(
        [
            "chaser",
            "board",
            "execute-terminal-approval",
            request["approval_id"],
            "--expected-proposal-id",
            request["proposal_id"],
            "--vault-root",
            str(tmp_path),
            "--confirm-approved-terminal-write",
            "--json",
        ]
    )
    duplicate = _decode_cli_result(capsys.readouterr().out)

    assert duplicate_exit == 2
    assert "approval_status_not_approved:executed" in duplicate["blockers"]


def test_chaser_board_execute_terminal_approval_cli_consumes_copy_once(tmp_path: Path, capsys) -> None:
    (tmp_path / "source.txt").write_text("copied through cli\n", encoding="utf-8")
    cli.main(
        [
            "chaser",
            "board",
            "request-terminal-approval",
            "copy source.txt copied.txt",
            "--cwd",
            str(tmp_path),
            "--vault-root",
            str(tmp_path),
            "--write-approval-request",
            "--json",
        ]
    )
    request = _decode_cli_result(capsys.readouterr().out)

    from runtime.studio.service import StudioService

    StudioService(tmp_path).approve(request["approval_id"], reviewed_by="operator")

    exit_code = cli.main(
        [
            "chaser",
            "board",
            "execute-terminal-approval",
            request["approval_id"],
            "--expected-proposal-id",
            request["proposal_id"],
            "--vault-root",
            str(tmp_path),
            "--confirm-approved-terminal-write",
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["status"] == "executed"
    assert result["supported_write_executable"] == "copy"
    assert result["source_path"] == "source.txt"
    assert result["target_path"] == "copied.txt"
    assert result["authority"]["approval_consumption_now"] is True
    assert result["authority"]["terminal_audit_write_now"] is True
    assert result["authority"]["agent_bus_write_now"] is False
    assert (tmp_path / "copied.txt").read_text(encoding="utf-8") == "copied through cli\n"
    assert (tmp_path / result["exact_once_marker_path"]).exists()

    duplicate_exit = cli.main(
        [
            "chaser",
            "board",
            "execute-terminal-approval",
            request["approval_id"],
            "--expected-proposal-id",
            request["proposal_id"],
            "--vault-root",
            str(tmp_path),
            "--confirm-approved-terminal-write",
            "--json",
        ]
    )
    duplicate = _decode_cli_result(capsys.readouterr().out)

    assert duplicate_exit == 2
    assert "approval_status_not_approved:executed" in duplicate["blockers"]
