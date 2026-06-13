from __future__ import annotations

import sys
from pathlib import Path

from runtime.operator_surface.terminal import operator as terminal_op
from runtime.operator_surface import terminal_runs


def test_policy_runs_clean(capsys) -> None:
    rc = terminal_op.run_policy(output_json=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert "read_only_command" in out
    assert "Tier 4" in out


def test_preview_allows_read_only(capsys) -> None:
    rc = terminal_op.run_preview("pwd", output_json=True)
    assert rc == 0


def test_preview_blocks_destructive(capsys) -> None:
    rc = terminal_op.run_preview("rm -rf /tmp/x", output_json=True)
    assert rc == 3  # blocked exit code


def test_run_blocks_and_audits_destructive(tmp_path: Path, capsys) -> None:
    rc = terminal_op.run_command("sudo whoami", cwd=str(tmp_path),
                                 output_json=True, vault_root=tmp_path)
    assert rc == 3
    runs = terminal_runs.list_terminal_runs(tmp_path)
    assert len(runs) == 1
    assert runs[0]["policy_decision"] == "blocked"


def test_run_executes_read_only_and_audits(tmp_path: Path, capsys) -> None:
    # Use the current python to print a deterministic string (python is allowlisted).
    rc = terminal_op.run_command(
        f'"{sys.executable}" -c "print(\'hello-terminal\')"',
        cwd=str(tmp_path), output_json=True, vault_root=tmp_path,
    )
    assert rc == 0
    runs = terminal_runs.list_terminal_runs(tmp_path)
    assert len(runs) == 1
    assert runs[0]["policy_decision"] == "executed"
    loaded = terminal_runs.load_terminal_run(tmp_path, runs[0]["run_id"])
    assert "hello-terminal" in loaded["stdout_excerpt"]
    assert loaded["terminal_output_trusted"] is False


def test_history_lists_runs(tmp_path: Path, capsys) -> None:
    terminal_op.run_command(
        f'"{sys.executable}" --version', cwd=str(tmp_path),
        output_json=True, vault_root=tmp_path,
    )
    rc = terminal_op.run_history(output_json=True, vault_root=tmp_path)
    assert rc == 0
    out = capsys.readouterr().out
    assert "--version" in out


def test_show_lists_one_run_without_execution(tmp_path: Path, capsys) -> None:
    record = terminal_runs.build_run_record(
        command="pwd",
        cwd=str(tmp_path),
        classification={"action_class": "read_only_command", "allowed": True},
        policy_decision="executed",
        exit_code=0,
        stdout_excerpt="readback",
    )
    terminal_runs.record_terminal_run(tmp_path, record)

    rc = terminal_op.run_show(record["run_id"], output_json=True, vault_root=tmp_path)

    assert rc == 0
    out = capsys.readouterr().out
    assert record["run_id"] in out
    assert "readback" in out
    assert len(terminal_runs.list_terminal_runs(tmp_path)) == 1


def test_show_rejects_unsafe_run_id(tmp_path: Path, capsys) -> None:
    rc = terminal_op.run_show("../escape", output_json=True, vault_root=tmp_path)

    assert rc == 2
    assert "unsafe_run_id" in capsys.readouterr().out


def test_run_handles_missing_executable(tmp_path: Path, capsys) -> None:
    # 'where' is allowlisted but querying a nonexistent target returns nonzero,
    # while a totally absent executable path is caught as an execution_error.
    rc = terminal_op.run_command(
        "git status", cwd=str(tmp_path), output_json=True, vault_root=tmp_path,
    )
    # git may or may not be installed; either a clean run or a recorded error,
    # but never an uncaught exception.
    assert rc in (0, 1)
    assert len(terminal_runs.list_terminal_runs(tmp_path)) == 1


def test_adapter_registered() -> None:
    from runtime.operator_surface.adapter_registry import get_default_registry
    from runtime.operator_surface.capabilities import SurfaceType

    assert get_default_registry().is_registered(SurfaceType.TERMINAL)
