from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.chaser.exports import ExportError, export_session
from runtime.chaser.models import SessionRecord
from runtime.chaser.sessions import (
    SessionNotFoundError,
    SessionStoreError,
    archive_session,
    list_sessions,
    load_session,
    rename_session,
    set_session_pinned,
    session_path,
)


def _write_session(vault_root: Path, data: dict) -> None:
    path = session_path(vault_root, data["session_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _sample_session(session_id: str = "sess-001") -> dict:
    return {
        "session_id": session_id,
        "title": "Terminal diagnosis chat",
        "runtime": "archon",
        "profile": "ops",
        "model": "claude-opus-4-8",
        "provider": "anthropic",
        "created_at": "2026-06-03T10:00:00+00:00",
        "updated_at": "2026-06-03T10:30:00+00:00",
        "pinned": True,
        "messages": [
            {"role": "user", "content": "check status", "timestamp": "2026-06-03T10:00:01+00:00"},
            {
                "role": "assistant",
                "content": "Here is the key: API_KEY=test-key-test1234567890abcdef and a bearer Bearer abcdef123456",
                "timestamp": "2026-06-03T10:00:05+00:00",
            },
        ],
        "tool_runs": [
            {
                "tool": "run_command",
                "args": {"command": "git status", "token": "password=hunter2supersecret"},
                "result_summary": "clean tree",
                "trust_tier": "Tier 4",
                "audit_id": "aud-1",
            }
        ],
        "terminal_runs": [
            {
                "run_id": "term-1",
                "command": "git status",
                "cwd": "/repo",
                "classification": "read_only_command",
                "blocked": False,
                "returncode": 0,
                "stdout_excerpt": "nothing to commit",
                "stderr_excerpt": "",
                "audit_id": "aud-2",
            }
        ],
        "artifacts": [
            {
                "artifact_id": "art-1",
                "artifact_type": "file",
                "title": "summary.md",
                "path_or_uri": "07_LOGS/x/summary.md",
                "source": "term-1",
                "generated": True,
            }
        ],
    }


def test_missing_session_fails_cleanly(tmp_path: Path) -> None:
    with pytest.raises(SessionNotFoundError):
        load_session(tmp_path, "does-not-exist")


def test_unsafe_session_id_rejected(tmp_path: Path) -> None:
    with pytest.raises(SessionStoreError):
        load_session(tmp_path, "../escape")


def test_payload_session_id_mismatch_rejected(tmp_path: Path) -> None:
    data = _sample_session("sess-path")
    data["session_id"] = "sess-payload"
    path = session_path(tmp_path, "sess-path")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(SessionStoreError):
        load_session(tmp_path, "sess-path")


def test_markdown_export_shape(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session())
    result = export_session(tmp_path, "sess-001", fmt="markdown")

    assert result["ok"] is True
    assert result["format"] == "markdown"
    assert result["external_upload_performed"] is False
    export_path = Path(result["export_path"])
    assert export_path.exists()
    body = export_path.read_text(encoding="utf-8")
    assert "# Session Export — Terminal diagnosis chat" in body
    assert "## Transcript" in body
    assert "## Terminal Runs" in body
    assert "Tier 4 untrusted" in body


def test_json_export_shape(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session())
    result = export_session(tmp_path, "sess-001", fmt="json")

    assert result["format"] == "json"
    payload = json.loads(Path(result["export_path"]).read_text(encoding="utf-8"))
    assert payload["session"]["session_id"] == "sess-001"
    assert payload["untrusted_tier"] == "Tier 4"
    assert "tool_run_manifest" in payload
    assert "terminal_run_manifest" in payload
    assert "artifact_manifest" in payload


def test_artifact_manifest_included(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session())
    result = export_session(tmp_path, "sess-001", fmt="json")

    manifest = json.loads(Path(result["artifact_manifest_path"]).read_text(encoding="utf-8"))
    assert len(manifest) == 1
    assert manifest[0]["artifact_id"] == "art-1"
    assert manifest[0]["artifact_type"] == "file"


def test_tool_and_terminal_manifest_included(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session())
    result = export_session(tmp_path, "sess-001", fmt="json")
    payload = json.loads(Path(result["export_path"]).read_text(encoding="utf-8"))

    assert len(payload["tool_run_manifest"]) == 1
    assert payload["tool_run_manifest"][0]["tool"] == "run_command"
    assert len(payload["terminal_run_manifest"]) == 1
    assert payload["terminal_run_manifest"][0]["run_id"] == "term-1"


def test_secret_like_values_redacted_markdown(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session())
    result = export_session(tmp_path, "sess-001", fmt="markdown")
    body = Path(result["export_path"]).read_text(encoding="utf-8")

    assert "test-key-test1234567890abcdef" not in body
    assert "[REDACTED]" in body
    assert result["redaction_applied"] is True


def test_secret_like_values_redacted_json(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session())
    result = export_session(tmp_path, "sess-001", fmt="json")
    raw = Path(result["export_path"]).read_text(encoding="utf-8")

    assert "test-key-test1234567890abcdef" not in raw
    assert "hunter2supersecret" not in raw
    assert "[REDACTED]" in raw


def test_export_audit_emitted(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session())
    captured: list[dict] = []
    result = export_session(tmp_path, "sess-001", fmt="markdown", actor="archon", emit_audit=captured.append)

    audit_path = Path(result["audit_path"])
    assert audit_path.exists()
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["event"] == "session_export"
    assert audit["actor"] == "archon"
    assert audit["external_upload_performed"] is False
    assert audit["redaction"]["applied"] is True
    assert captured and captured[0]["session_id"] == "sess-001"


def test_unsupported_format_rejected(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session())
    with pytest.raises(ExportError):
        export_session(tmp_path, "sess-001", fmt="pdf")


def test_no_redaction_when_clean(tmp_path: Path) -> None:
    data = _sample_session("sess-clean")
    data["messages"] = [{"role": "user", "content": "hello world", "timestamp": ""}]
    data["tool_runs"] = []
    data["terminal_runs"] = []
    _write_session(tmp_path, data)
    result = export_session(tmp_path, "sess-clean", fmt="json")

    assert result["redaction_applied"] is False
    assert result["redaction_report"]["total_redactions"] == 0


def test_export_accepts_preloaded_record(tmp_path: Path) -> None:
    record = SessionRecord.from_dict(_sample_session("sess-pre"))
    result = export_session(tmp_path, "sess-pre", fmt="markdown", session=record)
    assert result["ok"] is True
    assert Path(result["export_path"]).exists()


def test_list_sessions_returns_metadata(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session("sess-a"))
    _write_session(tmp_path, _sample_session("sess-b"))
    sessions = list_sessions(tmp_path)
    ids = {s["session_id"] for s in sessions}
    assert ids == {"sess-a", "sess-b"}
    assert all("message_count" in s for s in sessions)


def test_list_sessions_empty_when_no_store(tmp_path: Path) -> None:
    assert list_sessions(tmp_path) == []


def test_set_session_pinned_updates_metadata_and_audit(tmp_path: Path) -> None:
    data = _sample_session("sess-pin")
    data["pinned"] = False
    _write_session(tmp_path, data)

    result = set_session_pinned(tmp_path, "sess-pin", True, actor="codex")

    assert result["ok"] is True
    assert result["action"] == "pin"
    assert result["pinned"] is True
    assert result["hard_delete_performed"] is False
    record = load_session(tmp_path, "sess-pin")
    assert record.pinned is True
    assert record.updated_at
    audit = json.loads(Path(result["audit_path"]).read_text(encoding="utf-8"))
    assert audit["event"] == "session_lifecycle"
    assert audit["action"] == "pin"
    assert audit["actor"] == "codex"
    assert audit["before"]["pinned"] is False
    assert audit["after"]["pinned"] is True
    assert audit["authority"]["terminal_execution"] is False
    assert audit["canonical_writeback_performed"] is False


def test_set_session_pinned_can_unpin(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session("sess-unpin"))

    result = set_session_pinned(tmp_path, "sess-unpin", False)

    assert result["action"] == "unpin"
    assert load_session(tmp_path, "sess-unpin").pinned is False


def test_rename_session_updates_title_and_preserves_messages(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session("sess-rename"))

    result = rename_session(tmp_path, "sess-rename", " Gateway review ")

    assert result["ok"] is True
    assert result["title"] == "Gateway review"
    record = load_session(tmp_path, "sess-rename")
    assert record.title == "Gateway review"
    assert len(record.messages) == 2
    audit = json.loads(Path(result["audit_path"]).read_text(encoding="utf-8"))
    assert audit["action"] == "rename"
    assert audit["before"]["title"] == "Terminal diagnosis chat"
    assert audit["after"]["title"] == "Gateway review"


def test_rename_session_rejects_empty_or_control_title(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session("sess-title-guard"))

    with pytest.raises(SessionStoreError):
        rename_session(tmp_path, "sess-title-guard", "   ")
    with pytest.raises(SessionStoreError):
        rename_session(tmp_path, "sess-title-guard", "bad\ntitle")


def test_rename_session_rejects_unsafe_session_id(tmp_path: Path) -> None:
    with pytest.raises(SessionStoreError):
        rename_session(tmp_path, "../escape", "safe title")


def test_archive_session_moves_active_record_and_writes_audit(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session("sess-archive"))
    active_path = session_path(tmp_path, "sess-archive")

    result = archive_session(tmp_path, "sess-archive", actor="codex", reason="operator cleanup")

    assert result["ok"] is True
    assert result["action"] == "archive"
    assert result["hard_delete_performed"] is False
    assert not active_path.exists()
    archive_path = Path(result["archive_path"])
    assert archive_path.exists()
    archived = json.loads(archive_path.read_text(encoding="utf-8"))
    assert archived["session_id"] == "sess-archive"
    assert archived["archive_reason"] == "operator cleanup"
    assert archived["archived_at"]
    audit = json.loads(Path(result["audit_path"]).read_text(encoding="utf-8"))
    assert audit["action"] == "archive"
    assert audit["archive_path"] == str(archive_path)
    assert audit["after"] is None
    assert audit["hard_delete_performed"] is False


def test_archived_sessions_are_not_listed_as_active(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session("sess-active"))
    _write_session(tmp_path, _sample_session("sess-archived"))
    archive_session(tmp_path, "sess-archived")

    sessions = list_sessions(tmp_path)

    assert {item["session_id"] for item in sessions} == {"sess-active"}


def test_archive_session_then_load_fails_cleanly(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session("sess-gone"))
    archive_session(tmp_path, "sess-gone")

    with pytest.raises(SessionNotFoundError):
        load_session(tmp_path, "sess-gone")


def test_session_export_after_metadata_lifecycle(tmp_path: Path) -> None:
    _write_session(tmp_path, _sample_session("sess-export-after-lifecycle"))
    set_session_pinned(tmp_path, "sess-export-after-lifecycle", False)
    rename_session(tmp_path, "sess-export-after-lifecycle", "Renamed export")

    result = export_session(tmp_path, "sess-export-after-lifecycle", fmt="json")

    payload = json.loads(Path(result["export_path"]).read_text(encoding="utf-8"))
    assert payload["session"]["title"] == "Renamed export"
    assert payload["session"]["pinned"] is False
