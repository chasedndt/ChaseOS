from __future__ import annotations

import json
from pathlib import Path

from runtime.chaser.chat_session_adapter import (
    build_session_record_from_studio_chat,
    export_studio_chat_session,
)
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
                "session_id": "chat-safe-001",
                "created_at_utc": "2026-06-06T10:00:00Z",
                "updated_at_utc": "2026-06-06T10:05:00Z",
                "provider_call_performed": False,
                "canonical_memory_written": False,
                "messages": [
                    {
                        "role": "user",
                        "content": "inspect terminal state",
                        "created_at_utc": "2026-06-06T10:00:01Z",
                    },
                    {
                        "role": "runtime",
                        "content": "terminal state is available as audit evidence",
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


def test_build_session_record_from_studio_chat_attaches_terminal_run(tmp_path: Path) -> None:
    _write_chat(tmp_path)
    run_id = _record_terminal_run(tmp_path)

    record = build_session_record_from_studio_chat(
        tmp_path,
        "runtime-ops-hermes-chat",
        terminal_run_ids=[run_id],
    )

    assert record.session_id == "chat-safe-001"
    assert record.runtime == "hermes"
    assert record.profile == "studio-chat"
    assert len(record.messages) == 2
    assert record.messages[0].content == "inspect terminal state"
    assert len(record.terminal_runs) == 1
    assert record.terminal_runs[0].run_id == run_id
    assert record.terminal_runs[0].trust_tier == "Tier 4"


def test_export_studio_chat_session_writes_export_without_execution(tmp_path: Path) -> None:
    _write_chat(tmp_path)
    run_id = _record_terminal_run(tmp_path)

    result = export_studio_chat_session(
        tmp_path,
        "runtime-ops-hermes-chat",
        fmt="json",
        actor="codex",
        terminal_run_ids=[run_id],
    )

    assert result["ok"] is True
    assert result["external_upload_performed"] is False
    assert result["authority"]["terminal_execution"] is False
    assert result["authority"]["provider_calls"] is False
    payload = json.loads(Path(result["export_path"]).read_text(encoding="utf-8"))
    assert payload["session"]["session_id"] == "chat-safe-001"
    assert payload["terminal_run_manifest"][0]["run_id"] == run_id


def test_export_studio_chat_session_redacts_secret_text(tmp_path: Path) -> None:
    _write_chat(tmp_path)
    path = tmp_path / "runtime" / "studio" / "chat" / "native-state" / "conversations" / "runtime-ops-hermes-chat.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["messages"][1]["content"] = "API_KEY=test-key-test1234567890abcdef"
    path.write_text(json.dumps(data), encoding="utf-8")

    result = export_studio_chat_session(tmp_path, "runtime-ops-hermes-chat", fmt="markdown")

    assert result["ok"] is True
    body = Path(result["export_path"]).read_text(encoding="utf-8")
    assert "test-key-test1234567890abcdef" not in body
    assert "[REDACTED]" in body


def test_export_studio_chat_session_rejects_unsafe_thread_without_writes(tmp_path: Path) -> None:
    result = export_studio_chat_session(tmp_path, "../escape", fmt="json")

    assert result["ok"] is False
    assert result["authority"]["terminal_execution"] is False
    assert not (tmp_path / "07_LOGS" / "Chaser-Sessions" / "exports").exists()


def test_export_studio_chat_session_rejects_missing_terminal_run(tmp_path: Path) -> None:
    _write_chat(tmp_path)

    result = export_studio_chat_session(
        tmp_path,
        "runtime-ops-hermes-chat",
        fmt="json",
        terminal_run_ids=["term_missing"],
    )

    assert result["ok"] is False
    assert "terminal run" in result["error"]["message"]
    assert not (tmp_path / "07_LOGS" / "Chaser-Sessions" / "exports").exists()
