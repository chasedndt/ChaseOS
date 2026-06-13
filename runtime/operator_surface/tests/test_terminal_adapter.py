from __future__ import annotations

from pathlib import Path
import sys

import pytest

from runtime.operator_surface.adapters.terminal_adapter import TerminalAdapter
from runtime.operator_surface.capabilities import SurfaceType
from runtime.operator_surface.contracts import OperatorScope, OperatorSession


def _adapter(tmp_path: Path) -> TerminalAdapter:
    scope = OperatorScope(
        run_id="terminal-test-run",
        surface=SurfaceType.TERMINAL,
        target_uris=[f"file://{tmp_path}"],
        allowed_paths=[str(tmp_path)],
    )
    session = OperatorSession(run_id="terminal-test-run", workflow_id="terminal-test", surface="terminal")
    adapter = TerminalAdapter()
    adapter.initialize(scope, session)
    return adapter


def test_classifies_safe_read_only_command() -> None:
    classification = TerminalAdapter.classify_command("pwd")

    assert classification["action_class"] == "read_only_command"
    assert classification["allowed"] is True
    assert classification["approval_required"] is False
    assert classification["untrusted_output"] is True


def test_blocks_shell_control_operator() -> None:
    classification = TerminalAdapter.classify_command("pwd && whoami")

    assert classification["allowed"] is False
    assert classification["action_class"] == "blocked_shell_control_command"
    assert "shell control" in classification["reason"]


def test_blocks_destructive_command() -> None:
    classification = TerminalAdapter.classify_command("rm -rf /tmp/chaseos-example")

    assert classification["allowed"] is False
    assert classification["action_class"] == "destructive_command"
    assert "destructive" in classification["reason"]


def test_blocks_sudo_or_elevated_command() -> None:
    classification = TerminalAdapter.classify_command("sudo apt update")

    assert classification["allowed"] is False
    assert classification["action_class"] == "elevated_command"
    assert "elevated" in classification["reason"]


def test_blocks_package_manager_commands() -> None:
    for command in ("pip install requests", "npm install"):
        classification = TerminalAdapter.classify_command(command)

        assert classification["allowed"] is False
        assert classification["action_class"] == "write_command"


def test_execute_blocks_path_arguments_outside_allowed_roots(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    events = []

    result = adapter.execute_step(
        {"step_index": 0, "action_type": "run_command", "command": "ls /", "cwd": str(tmp_path)},
        events.append,
    )

    assert result.success is False
    assert result.action_type == "path_outside_scope"
    assert isinstance(result.output, dict)
    assert result.output["blocked"] is True
    assert result.error is not None
    assert "outside allowed terminal scope" in result.error
    assert events[-1].event_type.value == "step_failed"


def test_blocks_cwd_outside_allowed_roots(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    outside = tmp_path.parent / "outside-terminal-scope"
    outside.mkdir(exist_ok=True)

    with pytest.raises(ValueError, match="outside allowed terminal scope"):
        adapter.validate_cwd(outside)


def test_execute_captures_redacts_truncates_and_marks_output_untrusted(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    events = []
    command = (
        f'"{sys.executable}" -c "'
        "print('API_KEY=test-key-test-1234567890abcdefghijklmnop')\n"
        "print('x' * 3000)"
        '"'
    )
    result = adapter.execute_step(
        {
            "step_index": 0,
            "action_type": "run_command",
            "command": command,
            "cwd": str(tmp_path),
            "max_output_chars": 120,
        },
        events.append,
    )

    assert result.success is True
    assert result.action_type == "read_only_command"
    assert result.output["stdout_truncated"] is True
    assert "[REDACTED]" in result.output["stdout"]
    assert "test-key-test" not in result.output["stdout"]
    assert result.output["untrusted_tier"] == "Tier 4"
    assert result.output["terminal_output_trusted"] is False
    assert events[-1].event_type.value == "step_complete"
    assert events[-1].payload["untrusted_tier"] == "Tier 4"


def test_blocked_command_emits_audit_shape(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    events = []

    result = adapter.execute_step(
        {"step_index": 1, "action_type": "run_command", "command": "sudo whoami", "cwd": str(tmp_path)},
        events.append,
    )
    audit = adapter.build_audit_payload()

    assert result.success is False
    assert result.output["blocked"] is True
    assert result.output["classification"]["action_class"] == "elevated_command"
    assert audit["adapter_status"] == "partial"
    assert audit["steps_failed"] == 1
    assert audit["terminal_output_trust_tier"] == "Tier 4"
    assert events[-1].event_type.value == "step_failed"
