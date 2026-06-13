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


def test_studio_terminal_product_contract_cli_is_read_only(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli.main(
        [
            "studio",
            "terminal-product-contract",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["surface"] == "studio_full_terminal_product_contract"
    assert result["contract_status"] == "contract_ready_no_execution"
    assert result["authority"]["studio_terminal_execution_now"] is False
    assert result["authority"]["chaser_agent_terminal_binding_now"] is False
    assert result["authority"]["agent_bus_mutation_now"] is False
    assert result["authority"]["provider_dispatch_now"] is False
    assert result["next_recommended_pass"] == "terminal-n30-terminal-session-backend-pty"
    assert not (tmp_path / "07_LOGS" / "Terminal-Sessions").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()
