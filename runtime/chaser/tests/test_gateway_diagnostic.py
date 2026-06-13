from __future__ import annotations

from pathlib import Path

from runtime.chaser.gateway_diagnostic import (
    STATE_DEGRADED,
    STATE_FAILED,
    STATE_RUNNING,
    run_gateway_diagnostic,
)


def _make_vault(tmp_path: Path, *, with_now: bool = True) -> Path:
    (tmp_path / "00_HOME").mkdir(parents=True, exist_ok=True)
    if with_now:
        (tmp_path / "00_HOME" / "Now.md").write_text(
            "# Now\n## Current Sprint\nPhase X ACTIVE\n", encoding="utf-8"
        )
    (tmp_path / "runtime" / "operator_surface" / "policies").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runtime" / "operator_surface" / "policies" / "terminal.yaml").write_text(
        "version: 1\n", encoding="utf-8"
    )
    return tmp_path


def test_result_shape_and_authority(tmp_path: Path) -> None:
    _make_vault(tmp_path)
    result = run_gateway_diagnostic(tmp_path)
    assert result["surface"] == "chaser_gateway_diagnostic"
    assert result["overall_state"] in (STATE_RUNNING, STATE_DEGRADED, STATE_FAILED)
    assert result["authority"]["host_mutation"] is False
    assert result["authority"]["process_start"] is False
    assert result["authority"]["read_only"] is True
    assert isinstance(result["checks"], list) and result["checks"]
    assert {"name", "status", "detail"} <= set(result["checks"][0])


def test_checks_present(tmp_path: Path) -> None:
    _make_vault(tmp_path)
    names = {c["name"] for c in run_gateway_diagnostic(tmp_path)["checks"]}
    assert {
        "boot_context", "runtime_adapters", "agent_bus_mode",
        "bus_heartbeats", "schedule_intents", "approval_backlog", "terminal_surface",
    } <= names


def test_missing_now_md_degrades_or_fails(tmp_path: Path) -> None:
    _make_vault(tmp_path, with_now=False)
    result = run_gateway_diagnostic(tmp_path)
    # boot fails (no Now.md) → overall degraded or failed, never running
    assert result["overall_state"] in (STATE_DEGRADED, STATE_FAILED)
    assert result["ready"] is False


def test_degraded_emits_repair_plan(tmp_path: Path) -> None:
    _make_vault(tmp_path)
    result = run_gateway_diagnostic(tmp_path)
    if result["overall_state"] != STATE_RUNNING:
        assert result["next_actions"]
        for action in result["next_actions"]:
            assert "action" in action and action["check"]


def test_terminal_surface_missing_policy_degrades(tmp_path: Path) -> None:
    _make_vault(tmp_path)
    (tmp_path / "runtime" / "operator_surface" / "policies" / "terminal.yaml").unlink()
    result = run_gateway_diagnostic(tmp_path)
    term = next(c for c in result["checks"] if c["name"] == "terminal_surface")
    assert term["status"] == "degraded"


def test_no_writes_to_vault(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    before = {p for p in vault.rglob("*") if p.is_file()}
    run_gateway_diagnostic(vault)
    after = {p for p in vault.rglob("*") if p.is_file()}
    assert before == after  # read-only — no artifacts written
