from __future__ import annotations

import json
from pathlib import Path

from runtime.cli import main as cli


def _decode_cli_result(output: str) -> dict:
    envelope = json.loads(output)
    result = envelope["result"]
    if isinstance(result, dict) and "raw_stdout" not in result:
        return result
    return json.loads(result["raw_stdout"])


def test_chaser_terminal_authority_audit_cli_is_read_only(tmp_path: Path, capsys) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "terminal",
            "authority-audit",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["surface"] == "chaser_terminal_authority_audit"
    assert result["summary"]["checks_failed"] == 0
    assert result["authority"]["studio_execution_now"] is False
    assert result["authority"]["terminal_execution_now"] is False
    assert result["authority"]["approval_queue_write_now"] is False
    assert result["authority"]["approval_consumption_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert result["authority"]["provider_call_now"] is False
    assert result["authority"]["canonical_writeback_now"] is False
    assert result["side_effects"]["probe_target_not_created"] is True
    assert not (tmp_path / result["probe"]["target_path"]).exists()
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()
