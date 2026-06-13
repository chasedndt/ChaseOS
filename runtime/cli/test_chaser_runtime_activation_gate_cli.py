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


def test_chaser_runtime_activation_gate_design_cli_is_read_only(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-gate-design",
            "--profile",
            "ops",
            "--toolset",
            "terminal-preview",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_activation_gate_design"
    assert result["design_status"] == "design_ready_no_activation"
    assert result["ready_for_activation_now"] is False
    assert result["activation_request_write_available"] is True
    assert result["activation_approval_decision_preflight_available"] is True
    assert result["activation_approval_consumption_design_available"] is True
    assert result["activation_approval_consumption_write_guard_available"] is True
    assert result["activation_post_consumption_readiness_available"] is True
    assert result["activation_executor_design_available"] is True
    assert result["activation_executor_write_guard_available"] is True
    assert result["activation_state_readiness_available"] is True
    assert result["profile_toolset_activation_design_available"] is True
    assert result["profile_toolset_activation_write_guard_available"] is True
    assert result["profile_toolset_activation_readiness_available"] is True
    assert result["terminal_toolset_binding_design_available"] is False
    assert result["terminal_toolset_binding_write_guard_available"] is False
    assert result["activation_approval_consumption_available"] is True
    assert result["authority"]["runtime_activation_now"] is False
    assert result["authority"]["approval_queue_write_now"] is False
    assert result["authority"]["approval_consumption_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert result["authority"]["provider_call_now"] is False
    assert "activation_approval_decision_preflight_not_implemented" not in result["future_gate_blockers"]
    assert "activation_approval_consumption_write_guard_not_implemented" not in result["future_gate_blockers"]
    assert "activation_post_consumption_readiness_not_implemented" not in result["future_gate_blockers"]
    assert "activation_approval_consumption_activation_executor_not_implemented" not in result["future_gate_blockers"]
    assert "activation_executor_write_guard_not_implemented" not in result["future_gate_blockers"]
    assert "activation_state_readiness_not_implemented" not in result["future_gate_blockers"]
    assert "profile_toolset_activation_design_not_implemented" not in result["future_gate_blockers"]
    assert "profile_toolset_activation_write_guard_not_implemented" not in result["future_gate_blockers"]
    assert "profile_toolset_activation_readiness_not_implemented" not in result["future_gate_blockers"]
    assert "terminal_toolset_binding_design_not_implemented" in result["future_gate_blockers"]
    assert "terminal_toolset_binding_write_guard_not_implemented" not in result["future_gate_blockers"]
    assert result["next_recommended_pass"] == (
        "terminal-n29-studio-full-terminal-product-contract"
    )
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_chaser_runtime_activation_gate_design_cli_blocks_unknown_toolset(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "activation-gate-design",
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
    assert "unknown_toolset:missing" in result["blockers"]
    assert result["authority"]["runtime_activation_now"] is False
    assert not (tmp_path / "runtime" / "agent_bus").exists()
