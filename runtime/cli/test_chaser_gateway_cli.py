from __future__ import annotations

import json
from pathlib import Path

from runtime.cli import main as cli
from runtime.studio.service import StudioService


def _decode_cli_result(output: str) -> dict:
    envelope = json.loads(output)
    result = envelope["result"]
    if isinstance(result, dict) and "raw_stdout" not in result:
        return result
    return json.loads(result["raw_stdout"])


def test_chaser_gateway_ingress_cli_rejects_missing_operator_confirmation(tmp_path: Path, capsys) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "gateway",
            "ingress",
            "terminal.propose",
            "--payload-json",
            json.dumps({"command": "pwd", "cwd": str(tmp_path)}),
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert result["ok"] is False
    assert "local_operator_confirmation_required" in result["blockers"]
    assert result["authority"]["agent_bus_write_now"] is False
    assert result["authority"]["provider_call_now"] is False


def test_chaser_gateway_ingress_cli_terminal_propose_is_preview_only(tmp_path: Path, capsys) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "gateway",
            "ingress",
            "terminal.propose",
            "--payload-json",
            json.dumps({"command": "mkdir example", "cwd": str(tmp_path)}),
            "--confirm-local-operator",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["result"]["status"] == "approval_required_future_n6"
    assert result["authority"]["terminal_execution_now"] is False
    assert result["authority"]["approval_queue_write_now"] is False
    assert not (tmp_path / "example").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_gateway_ingress_cli_executes_only_confirmed_approved_terminal_write(
    tmp_path: Path,
    capsys,
) -> None:
    write_exit = cli.main(
        [
            "chaser",
            "gateway",
            "ingress",
            "terminal.approval_request_write",
            "--payload-json",
            json.dumps({"command": "mkdir example", "cwd": str(tmp_path)}),
            "--confirm-local-operator",
            "--confirm-approval-queue-write",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    write_result = _decode_cli_result(capsys.readouterr().out)
    assert write_exit == 0
    assert write_result["result"]["approval_request_written"] is True

    approval = write_result["result"]
    StudioService(tmp_path).approve(approval["approval_id"], reviewed_by="operator")

    blocked_exit = cli.main(
        [
            "chaser",
            "gateway",
            "ingress",
            "terminal.execute_approval",
            "--payload-json",
            json.dumps({
                "approval_id": approval["approval_id"],
                "expected_proposal_id": approval["proposal_id"],
            }),
            "--confirm-local-operator",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    blocked = _decode_cli_result(capsys.readouterr().out)
    assert blocked_exit == 2
    assert "operator_approved_terminal_write_confirmation_required" in blocked["blockers"]
    assert not (tmp_path / "example").exists()

    exec_exit = cli.main(
        [
            "chaser",
            "gateway",
            "ingress",
            "terminal.execute_approval",
            "--payload-json",
            json.dumps({
                "approval_id": approval["approval_id"],
                "expected_proposal_id": approval["proposal_id"],
            }),
            "--confirm-local-operator",
            "--confirm-approved-terminal-write",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    executed = _decode_cli_result(capsys.readouterr().out)

    assert exec_exit == 0
    assert executed["ok"] is True
    assert executed["authority"]["terminal_execution_now"] is True
    assert executed["authority"]["approval_consumption_now"] is True
    assert executed["authority"]["agent_bus_write_now"] is False
    assert executed["authority"]["provider_call_now"] is False
    assert executed["authority"]["canonical_writeback_now"] is False
    assert (tmp_path / "example").is_dir()
