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


def _write_capabilities(root: Path) -> None:
    runtime_dir = root / "runtime" / "hermes"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir.joinpath("capabilities.yaml").write_text(
        "\n".join(
            [
                "bus_name: Hermes",
                "display_name: Hermes Harness",
                "description: Test harness",
                "handles:",
                "  - task_type: repo.inspect",
                "    priority: primary",
                "max_concurrent_tasks: 1",
                "heartbeat_stale_seconds: 60",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_agent_bus_harness_readiness_cli_reports_blocked_read_only_contract(tmp_path: Path, capsys) -> None:
    _write_capabilities(tmp_path)

    exit_code = cli.main(
        [
            "agent-bus",
            "harness-readiness",
            "--runtime",
            "hermes",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 2
    assert result["surface"] == "agent_harness_readiness"
    assert result["read_only"] is True
    assert result["runtime_bus_name"] == "Hermes"
    assert result["harness_status"] == "blocked"
    assert "runtime_heartbeat_missing_or_stale" in result["blocked_reasons"]
    assert result["tool_calling"]["tools_callable_now"] is False
    assert result["authority"]["agent_bus_mutation_allowed"] is False
    assert result["authority"]["provider_calls_allowed"] is False
