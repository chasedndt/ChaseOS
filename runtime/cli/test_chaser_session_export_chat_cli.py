from __future__ import annotations

import json
from pathlib import Path

from runtime.cli import main as cli
from runtime.operator_surface import terminal_runs


def _write_chat(vault: Path, thread_id: str = "runtime-ops-hermes-chat") -> None:
    path = vault / "runtime" / "studio" / "chat" / "native-state" / "conversations" / f"{thread_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "surface": "phase11_chat_thread_conversations",
                "thread_id": thread_id,
                "title": "Runtime Ops Hermes Chat",
                "runtime_id": "hermes",
                "session_id": "chat-safe-cli-001",
                "created_at_utc": "2026-06-06T10:00:00Z",
                "updated_at_utc": "2026-06-06T10:05:00Z",
                "provider_call_performed": False,
                "canonical_memory_written": False,
                "messages": [
                    {
                        "role": "user",
                        "content": "preview terminal evidence",
                        "created_at_utc": "2026-06-06T10:00:01Z",
                    },
                    {
                        "role": "runtime",
                        "content": "attached recorded audit run only",
                        "created_at_utc": "2026-06-06T10:00:05Z",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def _record_terminal_run(vault: Path) -> str:
    record = terminal_runs.build_run_record(
        command="pwd",
        cwd=str(vault),
        classification={"action_class": "read_only_command", "allowed": True},
        policy_decision="executed",
        exit_code=0,
        stdout_excerpt="C:/repo",
    )
    terminal_runs.record_terminal_run(vault, record)
    return record["run_id"]


def _decode_cli_envelope(output: str) -> dict:
    envelope = json.loads(output)
    result = envelope["result"]
    if isinstance(result, dict) and "raw_stdout" not in result:
        return result
    return json.loads(result["raw_stdout"])


def test_chaser_session_export_chat_cli_exports_studio_chat_without_execution(
    tmp_path: Path,
    capsys,
) -> None:
    _write_chat(tmp_path)
    run_id = _record_terminal_run(tmp_path)

    exit_code = cli.main(
        [
            "chaser",
            "session",
            "export-chat",
            "runtime-ops-hermes-chat",
            "--format",
            "json",
            "--terminal-run",
            run_id,
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    captured = capsys.readouterr()
    result = _decode_cli_envelope(captured.out)

    assert exit_code == 0
    assert result["ok"] is True
    assert result["authority"]["terminal_execution"] is False
    assert result["authority"]["provider_calls"] is False
    assert result["authority"]["agent_bus_writes"] is False
    assert result["terminal_run_count"] == 1
    export_payload = json.loads(Path(result["export_path"]).read_text(encoding="utf-8"))
    assert export_payload["session"]["session_id"] == "chat-safe-cli-001"
    assert export_payload["terminal_run_manifest"][0]["run_id"] == run_id


def test_chaser_session_export_chat_cli_rejects_unsafe_thread_without_writes(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = cli.main(
        [
            "chaser",
            "session",
            "export-chat",
            "../escape",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    captured = capsys.readouterr()
    result = _decode_cli_envelope(captured.out)

    assert exit_code == 2
    assert result["ok"] is False
    assert result["authority"]["terminal_execution"] is False
    assert result["authority"]["approval_consumption"] is False
    assert not (tmp_path / "07_LOGS" / "Chaser-Sessions" / "exports").exists()
