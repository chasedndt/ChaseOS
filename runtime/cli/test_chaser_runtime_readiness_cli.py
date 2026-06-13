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


def test_chaser_runtime_readiness_cli_is_read_only(tmp_path: Path, capsys) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "runtime",
            "readiness",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    result = _decode_cli_result(capsys.readouterr().out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["surface"] == "chaser_runtime_readiness_review"
    assert result["live_runtime_ready"] is False
    assert result["ready_for_runtime_activation"] is False
    assert result["profile_toolset_activation_readiness_available"] is True
    assert result["profile_toolset_activation_readiness_surface"] == (
        "chaser_runtime_profile_toolset_activation_readiness"
    )
    assert result["terminal_toolset_binding_design_available"] is False
    assert result["terminal_toolset_binding_design_surface"] == ""
    assert result["terminal_toolset_binding_write_guard_available"] is False
    assert result["next_recommended_pass"] == (
        "terminal-n29-studio-full-terminal-product-contract"
    )
    assert result["contract_summary"]["checks_failed"] == 0
    assert all(value is False for value in result["authority"].values())
    assert result["activation_posture"]["studio_execution_allowed"] is False
    assert result["activation_posture"]["terminal_execution_allowed"] is False
    assert result["activation_posture"]["profile_toolset_activation_readiness_allowed"] is True
    assert result["activation_posture"]["terminal_toolset_binding_design_allowed"] is False
    assert result["activation_posture"]["terminal_toolset_binding_write_guard_allowed"] is False
    assert result["activation_posture"]["agent_bus_mutation_allowed"] is False
    assert result["activation_posture"]["provider_call_allowed"] is False
    assert "provider_runtime_dispatch_not_authorized" in result["blockers_for_live_wiring"]
    assert "external_gateway_ingress_not_implemented" in result["blockers_for_live_wiring"]
    assert "profile_toolset_activation_readiness_not_implemented" not in result["blockers_for_live_wiring"]
    assert not (tmp_path / "runtime" / "agent_bus").exists()
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
