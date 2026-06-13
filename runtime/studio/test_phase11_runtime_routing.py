"""Tests for Phase 11 runtime routing refactor.

Covers:
  - chat task type added to task_type_table.yaml
  - _dispatch_chat handler in hermes_watch.py
  - phase11_chat_send_message.py — direct Chat→Hermes dispatch
  - phase11_chat_hermes_wsl_config.py — WSL connection status
  - phase11_credential_setup_ux.py — routing model and credential split
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from runtime.agent_bus.bus import init_db


# ── helpers ──────────────────────────────────────────────────────────────────


def _temp_vault() -> Path:
    d = Path(tempfile.mkdtemp())
    init_db(d)
    return d


# ── task_type_table: chat type ─────────────────────────────────────────────────


class TestChatTaskType:
    def _load_table(self) -> list[dict]:
        import yaml
        p = Path(__file__).parent.parent / "aor" / "task_type_table.yaml"
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        return data.get("task_types", [])

    def test_chat_task_type_exists(self) -> None:
        ids = [t["id"] for t in self._load_table()]
        assert "chat" in ids

    def test_chat_task_type_has_required_fields(self) -> None:
        chat = next(t for t in self._load_table() if t["id"] == "chat")
        assert chat["description"]
        assert chat["permission_ceiling"] == "bus_result_only"
        assert "write_bus_result" in chat["permission_set"]

    def test_chat_task_type_has_escalation_triggers(self) -> None:
        chat = next(t for t in self._load_table() if t["id"] == "chat")
        assert len(chat.get("escalation_trigger", [])) > 0

    def test_unclassified_sentinel_still_present(self) -> None:
        ids = [t["id"] for t in self._load_table()]
        assert "unclassified" in ids


# ── hermes_watch: _dispatch_chat ───────────────────────────────────────────────


class TestHermesChatDispatch:
    def test_chat_in_dispatch_table(self) -> None:
        from runtime.workflows.hermes_watch import _TASK_DISPATCH
        assert "chat" in _TASK_DISPATCH

    def test_dispatch_chat_claims_and_completes_task(self) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks
        from runtime.workflows.hermes_watch import _dispatch_chat

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="Hermes", intent="TASK",
                        priority="normal", request="Hello Hermes from test",
                        expected_output="chat-response",
                        notes="task_type: chat\nsession_id: test-session-001")
        assert r.get("created")
        task_id = r["task_id"]
        tasks = list_tasks(vault, recipient="Hermes")
        task = next(t for t in tasks if t["task_id"] == task_id)

        result = _dispatch_chat(task, vault, synthesize=False)
        assert result["task_id"] == task_id
        assert result["status"] == "done"
        assert result["task_type"] == "chat"

    def test_dispatch_chat_no_synthesis_returns_ack(self) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks
        from runtime.workflows.hermes_watch import _dispatch_chat

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="Hermes", intent="TASK",
                        priority="normal", request="test message",
                        expected_output="chat-response", notes="task_type: chat")
        task_id = r["task_id"]
        tasks = list_tasks(vault, recipient="Hermes")
        task = next(t for t in tasks if t["task_id"] == task_id)

        result = _dispatch_chat(task, vault, synthesize=False)
        assert result["runtime_handled"] is False
        assert result["response_preview"]

    def test_dispatch_chat_synthesis_blocker_is_visible(self, monkeypatch) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks
        import runtime.workflows.hermes_watch as hermes_watch

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="Hermes", intent="TASK",
                        priority="normal", request="test message",
                        expected_output="chat-response", notes="task_type: chat")
        task = next(t for t in list_tasks(vault, recipient="Hermes") if t["task_id"] == r["task_id"])
        monkeypatch.setattr(
            hermes_watch,
            "_hermes_runtime_chat_result",
            lambda *_args, **_kwargs: (None, "Hermes native chat backend is not configured"),
        )

        result = hermes_watch._dispatch_chat(task, vault, synthesize=True)

        assert result["runtime_handled"] is False
        assert result["runtime_blocker"].startswith("Hermes native chat backend")
        assert "Runtime blocker: Hermes native chat backend" in result["response_preview"]

    def test_dispatch_chat_does_not_call_chaseos_provider_adapter(self) -> None:
        source = (Path(__file__).parents[1] / "workflows" / "hermes_watch.py").read_text(
            encoding="utf-8"
        )
        assert "from runtime.execution_adapters.execute import execute_synthesis" not in source

    def test_dispatch_chat_has_writebacks(self) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks
        from runtime.workflows.hermes_watch import _dispatch_chat

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="Hermes", intent="TASK",
                        priority="normal", request="test",
                        expected_output="chat-response", notes="task_type: chat")
        tasks = list_tasks(vault, recipient="Hermes")
        task = next(t for t in tasks if t["task_id"] == r["task_id"])

        result = _dispatch_chat(task, vault, synthesize=False)
        assert len(result["writebacks"]) == 1
        wb = result["writebacks"][0]
        assert wb["path"].startswith("07_LOGS/Agent-Activity/")
        assert "hermes-chat" in wb["path"]

    def test_dispatch_chat_marks_task_done_in_bus(self) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks
        from runtime.workflows.hermes_watch import _dispatch_chat

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="Hermes", intent="TASK",
                        priority="normal", request="test",
                        expected_output="chat-response", notes="task_type: chat")
        task_id = r["task_id"]
        tasks = list_tasks(vault, recipient="Hermes")
        task = next(t for t in tasks if t["task_id"] == task_id)

        _dispatch_chat(task, vault, synthesize=False)

        updated = list_tasks(vault, recipient="Hermes")
        updated_task = next(t for t in updated if t["task_id"] == task_id)
        assert updated_task["status"] == "done"

    def test_dispatch_chat_duplicate_claim_skipped(self) -> None:
        from runtime.agent_bus.bus import claim_task, create_task, list_tasks
        from runtime.workflows.hermes_watch import _dispatch_chat

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="Hermes", intent="TASK",
                        priority="normal", request="test",
                        expected_output="chat-response", notes="task_type: chat")
        task_id = r["task_id"]
        # Claim it first so the dispatch can't claim it again
        claim_task(vault, task_id=task_id, runtime="Hermes")
        tasks = list_tasks(vault, recipient="Hermes")
        task = next(t for t in tasks if t["task_id"] == task_id)

        result = _dispatch_chat(task, vault, synthesize=False)
        # Should skip cleanly (already claimed)
        assert result["status"] in {"done", "skipped"}


# ── phase11_chat_send_message ──────────────────────────────────────────────────


class TestSendChatMessage:
    def test_send_returns_ok_and_task_id(self) -> None:
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        result = send_chat_message(vault, "Hello from test")
        assert result["ok"] is True
        assert result["task_id"]
        assert result["status"] == "SENT / AWAITING HERMES"

    def test_send_creates_agent_bus_task(self) -> None:
        from runtime.agent_bus.bus import list_tasks
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        r = send_chat_message(vault, "test message")
        assert r["ok"] is True
        tasks = list_tasks(vault, recipient="Hermes")
        ids = [t["task_id"] for t in tasks]
        assert r["task_id"] in ids

    def test_send_empty_message_blocked(self) -> None:
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        result = send_chat_message(vault, "")
        assert result["ok"] is False
        assert "message_required" in result["blocked_reason"]

    def test_send_preserves_session_id(self) -> None:
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        result = send_chat_message(vault, "test", session_id="my-session-xyz")
        assert result["session_id"] == "my-session-xyz"

    def test_send_autogenerates_session_id(self) -> None:
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        result = send_chat_message(vault, "test")
        assert result["session_id"]
        assert result["session_id"].startswith("chat-")

    def test_send_authority_flags(self) -> None:
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        result = send_chat_message(vault, "test")
        auth = result["authority"]
        assert auth["provider_call_performed"] is False
        assert auth["runtime_dispatch_via_agent_bus"] is True
        assert auth["runtime_owns_llm_credentials"] is True
        assert auth["canonical_mutation_performed"] is False
        assert "selected_runtime_id" in auth

    def test_send_task_has_chat_task_type_annotation(self) -> None:
        from runtime.agent_bus.bus import list_tasks
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        r = send_chat_message(vault, "annotation test")
        tasks = list_tasks(vault, recipient="Hermes")
        task = next(t for t in tasks if t["task_id"] == r["task_id"])
        notes = task.get("notes") or ""
        assert "task_type: chat" in notes

    def test_send_context_hint_in_notes(self) -> None:
        from runtime.agent_bus.bus import list_tasks
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        r = send_chat_message(vault, "test with hint", context_hint="project-x")
        tasks = list_tasks(vault, recipient="Hermes")
        task = next(t for t in tasks if t["task_id"] == r["task_id"])
        notes = task.get("notes") or ""
        assert "context_hint: project-x" in notes

    def test_send_persists_local_thread_message(self) -> None:
        from runtime.studio.phase11_chat_send_message import send_chat_message
        from runtime.studio.phase11_chat_thread_conversations import load_chat_thread_conversations

        vault = _temp_vault()
        result = send_chat_message(
            vault,
            "save this in the Hermes thread",
            runtime_id="hermes",
            thread_id="runtime-ops-hermes-chat",
            attachments=[{"name": "brief.png", "kind": "image", "type": "image/png", "size": 1200}],
        )
        conversations = load_chat_thread_conversations(vault)
        thread = conversations["conversations_by_thread_id"]["runtime-ops-hermes-chat"]

        assert result["ok"] is True
        assert result["thread_id"] == "runtime-ops-hermes-chat"
        assert result["conversation_persisted"] is True
        assert thread["message_count"] == 1
        assert thread["messages"][0]["role"] == "user"
        assert thread["messages"][0]["attachments"][0]["content_stored"] is False

    def test_create_folder_and_thread_are_visible_in_local_conversations(self) -> None:
        from runtime.studio.phase11_chat_thread_conversations import (
            create_chat_folder,
            create_chat_thread_conversation,
            load_chat_thread_conversations,
        )

        vault = _temp_vault()
        folder_result = create_chat_folder(vault, workspace_id="runtime-ops", label="Client Alpha")
        thread_result = create_chat_thread_conversation(
            vault,
            title="Deployment planning",
            workspace_id="runtime-ops",
            folder_id=folder_result["folder"]["folder_id"],
            folder_label=folder_result["folder"]["label"],
            runtime_id="openclaw",
        )
        conversations = load_chat_thread_conversations(vault)

        assert folder_result["ok"] is True
        assert thread_result["ok"] is True
        assert folder_result["folder"]["label"] == "Client Alpha"
        assert thread_result["conversation"]["folder_label"] == "Client Alpha"
        assert thread_result["conversation"]["runtime_id"] == "openclaw"
        assert thread_result["conversation"]["runtime_label"] == "OpenClaw"
        assert folder_result["folder"]["folder_id"] in {item["folder_id"] for item in conversations["folders"]}
        assert thread_result["conversation"]["thread_id"] in conversations["conversations_by_thread_id"]

    def test_send_preserves_workspace_folder_runtime_and_title_metadata(self) -> None:
        from runtime.studio.phase11_chat_send_message import send_chat_message
        from runtime.studio.phase11_chat_thread_conversations import load_chat_thread_conversations

        vault = _temp_vault()
        result = send_chat_message(
            vault,
            "continue this saved OpenClaw chat",
            runtime_id="openclaw",
            thread_id="runtime-ops-openclaw-fieldwork",
            workspace_id="runtime-ops",
            folder_id="fieldwork",
            folder_label="Fieldwork",
            title="Fieldwork run",
        )
        thread = load_chat_thread_conversations(vault)["conversations_by_thread_id"][
            "runtime-ops-openclaw-fieldwork"
        ]

        assert result["ok"] is True
        assert result["workspace_id"] == "runtime-ops"
        assert result["folder_id"] == "fieldwork"
        assert thread["title"] == "Fieldwork run"
        assert thread["folder_label"] == "Fieldwork"
        assert thread["runtime_label"] == "OpenClaw"

    def test_send_blocks_secret_like_message_before_persistence(self) -> None:
        from runtime.studio.phase11_chat_send_message import send_chat_message
        from runtime.studio.phase11_chat_thread_conversations import load_chat_thread_conversations

        vault = _temp_vault()
        result = send_chat_message(vault, "OPENAI_API_KEY=test-key-thisShouldNotPersist123456789")
        conversations = load_chat_thread_conversations(vault)

        assert result["ok"] is False
        assert result["blocked_reason"] == "secret_or_credential_indicator_present"
        assert conversations["summary"]["message_count"] == 0


# ── poll_chat_result ───────────────────────────────────────────────────────────


class TestPollChatResult:
    def test_poll_unknown_task_returns_not_found(self) -> None:
        from runtime.studio.phase11_chat_send_message import poll_chat_result

        vault = _temp_vault()
        result = poll_chat_result(vault, "task-nonexistent-abc123")
        assert result["ok"] is False
        assert result["status"] == "NOT_FOUND"
        assert result["is_complete"] is False

    def test_poll_pending_task_not_complete(self) -> None:
        from runtime.studio.phase11_chat_send_message import poll_chat_result, send_chat_message

        vault = _temp_vault()
        sent = send_chat_message(vault, "waiting for Hermes")
        polled = poll_chat_result(vault, sent["task_id"])
        assert polled["ok"] is True
        assert polled["is_complete"] is False
        assert polled["status"] in {"created", "open", "pending"}

    def test_poll_completed_task_is_complete(self) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks, update_task_status
        from runtime.studio.phase11_chat_send_message import poll_chat_result

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="Hermes", intent="TASK",
                        priority="normal", request="test", expected_output="chat-response",
                        notes="task_type: chat")
        task_id = r["task_id"]
        update_task_status(vault, task_id=task_id, runtime="Hermes",
                           status="done", event_type="result_attached",
                           message="Here is the answer.")
        polled = poll_chat_result(vault, task_id)
        assert polled["ok"] is True
        assert polled["is_complete"] is True

    def test_poll_completed_task_persists_runtime_response_once(self) -> None:
        from runtime.agent_bus.bus import update_task_status
        from runtime.studio.phase11_chat_send_message import poll_chat_result, send_chat_message
        from runtime.studio.phase11_chat_thread_conversations import load_chat_thread_conversations

        vault = _temp_vault()
        sent = send_chat_message(vault, "please respond", thread_id="runtime-ops-hermes-chat")
        update_task_status(
            vault,
            task_id=sent["task_id"],
            runtime="Hermes",
            status="done",
            event_type="result_attached",
            message="Hermes response saved.",
        )

        first = poll_chat_result(vault, sent["task_id"])
        second = poll_chat_result(vault, sent["task_id"])
        thread = load_chat_thread_conversations(vault)["conversations_by_thread_id"]["runtime-ops-hermes-chat"]

        assert first["conversation_persisted"] is True
        assert second["conversation_persisted"] is True
        assert thread["message_count"] == 2
        assert [message["role"] for message in thread["messages"]] == ["user", "runtime"]


# ── hermes_wsl_config ──────────────────────────────────────────────────────────


class TestHermesWslConfig:
    def test_returns_ok(self) -> None:
        from runtime.studio.phase11_chat_hermes_wsl_config import get_hermes_wsl_connection_status

        vault = _temp_vault()
        result = get_hermes_wsl_connection_status(vault)
        assert result["ok"] is True
        assert result["surface"] == "phase11_chat_hermes_wsl_config"

    def test_connection_state_present(self) -> None:
        from runtime.studio.phase11_chat_hermes_wsl_config import get_hermes_wsl_connection_status

        vault = _temp_vault()
        result = get_hermes_wsl_connection_status(vault)
        assert result["connection_state"] in {
            "LIVE", "HEARTBEAT_PRESENT", "TASK_EVIDENCE_ONLY",
            "BUS_EXISTS_NO_HEARTBEAT", "BUS_NOT_INITIALIZED",
        }

    def test_wsl_vault_path_in_result(self) -> None:
        from runtime.studio.phase11_chat_hermes_wsl_config import get_hermes_wsl_connection_status

        vault = _temp_vault()
        result = get_hermes_wsl_connection_status(vault)
        assert result["wsl_configuration"]["wsl_vault_path"].startswith("/mnt/c/")

    def test_startup_guide_has_all_steps(self) -> None:
        from runtime.studio.phase11_chat_hermes_wsl_config import get_hermes_wsl_connection_status

        vault = _temp_vault()
        result = get_hermes_wsl_connection_status(vault)
        guide = result["startup_guide"]
        assert guide["step_1"]
        assert guide["step_2"]
        assert guide["step_5_run_loop"]
        assert "hermes_watch" in guide["step_5_run_loop"]

    def test_credentials_section_studio_does_not_need_key(self) -> None:
        from runtime.studio.phase11_chat_hermes_wsl_config import get_hermes_wsl_connection_status

        vault = _temp_vault()
        result = get_hermes_wsl_connection_status(vault)
        creds = result["hermes_credentials"]
        assert creds["studio_needs_this_key"] is False
        assert "note" in creds

    def test_empty_vault_shows_bus_not_initialized_or_exists(self) -> None:
        from runtime.studio.phase11_chat_hermes_wsl_config import get_hermes_wsl_connection_status

        vault = Path(tempfile.mkdtemp())  # No init_db
        result = get_hermes_wsl_connection_status(vault)
        assert result["connection_state"] == "BUS_NOT_INITIALIZED"
        assert result["agent_bus_exists"] is False


# ── credential_setup_ux: routing model ────────────────────────────────────────


class TestCredentialRoutingModel:
    def test_routing_model_present(self) -> None:
        from runtime.studio.phase11_credential_setup_ux import get_credential_status

        vault = _temp_vault()
        result = get_credential_status(vault)
        assert "routing_model" in result

    def test_primary_path_is_runtime_dispatch(self) -> None:
        from runtime.studio.phase11_credential_setup_ux import get_credential_status

        vault = _temp_vault()
        rm = get_credential_status(vault)["routing_model"]
        assert rm["primary_path"] == "runtime_dispatch"
        assert rm["primary_path_ready"] is True  # always ready (no Studio-side key needed)

    def test_openai_not_required_for_primary(self) -> None:
        from runtime.studio.phase11_credential_setup_ux import get_credential_status

        vault = _temp_vault()
        rm = get_credential_status(vault)["routing_model"]
        assert rm["openai_api_key_required_for_primary"] is False
        assert rm["openai_api_key_required_for_fallback"] is True

    def test_openai_entry_has_direct_provider_routing_path(self) -> None:
        from runtime.studio.phase11_credential_setup_ux import get_credential_status

        vault = _temp_vault()
        creds = get_credential_status(vault)["credentials"]
        openai = next(c for c in creds if c["key_id"] == "openai_provider")
        assert openai["routing_path"] == "direct_provider"

    def test_no_provider_specific_key_for_runtimes(self) -> None:
        """Credential registry must not hardcode any specific provider for runtime-owned credentials."""
        from runtime.studio.phase11_credential_setup_ux import get_credential_status

        vault = _temp_vault()
        creds = get_credential_status(vault)["credentials"]
        key_ids = [c["key_id"] for c in creds]
        assert "anthropic_provider" not in key_ids, (
            "Hermes uses its own configured provider — do not hardcode Anthropic in the registry"
        )

    def test_routing_note_present_on_openai(self) -> None:
        from runtime.studio.phase11_credential_setup_ux import get_credential_status

        vault = _temp_vault()
        creds = get_credential_status(vault)["credentials"]
        openai = next(c for c in creds if c["key_id"] == "openai_provider")
        assert "NOT required for the primary Chat path" in openai["routing_note"]

    def test_summary_has_routing_ready_flags(self) -> None:
        from runtime.studio.phase11_credential_setup_ux import get_credential_status

        vault = _temp_vault()
        summary = get_credential_status(vault)["summary"]
        assert "runtime_path_ready" in summary
        assert summary["runtime_path_ready"] is True
        assert "direct_provider_ready" in summary

    def test_no_credential_values_in_output(self) -> None:
        import json
        import re
        from runtime.studio.phase11_credential_setup_ux import get_credential_status

        vault = _temp_vault()
        dump = json.dumps(get_credential_status(vault))
        assert not re.search(r"\bsk-[A-Za-z0-9_-]{16,}", dump)
        assert "OPENAI_API_KEY=" not in dump

    def test_setup_guide_mentions_wsl(self) -> None:
        from runtime.studio.phase11_credential_setup_ux import get_credential_status

        vault = _temp_vault()
        guide = get_credential_status(vault)["setup_guide"]
        assert "WSL" in guide["runtime_path_setup"] or "wsl" in guide["step_1"].lower() or "WSL" in guide["step_1"]


# ── end-to-end: send → dispatch cycle ─────────────────────────────────────────


class TestSendAndDispatchCycle:
    def test_send_and_dispatch_full_cycle(self) -> None:
        """Studio sends a chat message; Hermes dispatch handler claims and completes it."""
        from runtime.agent_bus.bus import list_tasks
        from runtime.studio.phase11_chat_send_message import poll_chat_result, send_chat_message
        from runtime.workflows.hermes_watch import _dispatch_chat

        vault = _temp_vault()
        # Studio sends
        sent = send_chat_message(vault, "What is the current sprint focus?")
        assert sent["ok"] is True
        task_id = sent["task_id"]

        # Hermes dispatches (simulates hermes_watch cycle)
        tasks = list_tasks(vault, recipient="Hermes")
        task = next(t for t in tasks if t["task_id"] == task_id)
        dispatch_result = _dispatch_chat(task, vault, synthesize=False)
        assert dispatch_result["status"] == "done"

        # Studio polls
        polled = poll_chat_result(vault, task_id)
        assert polled["ok"] is True
        assert polled["is_complete"] is True

    def test_hermes_bus_status_with_active_task(self) -> None:
        from runtime.studio.phase11_chat_send_message import (
            get_hermes_bus_status,
            send_chat_message,
        )

        vault = _temp_vault()
        send_chat_message(vault, "trigger a task")
        status = get_hermes_bus_status(vault)
        assert status["ok"] is True
        assert status["recent_task_count"] >= 1


# ── Multi-runtime routing ─────────────────────────────────────────────────────


class TestMultiRuntimeRouting:
    def test_send_to_hermes(self) -> None:
        from runtime.agent_bus.bus import list_tasks
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        result = send_chat_message(vault, "hello", runtime_id="hermes")
        assert result["ok"] is True
        assert result["recipient"] == "Hermes"
        tasks = list_tasks(vault, recipient="Hermes")
        assert any(t["task_id"] == result["task_id"] for t in tasks)

    def test_send_to_openclaw(self) -> None:
        from runtime.agent_bus.bus import list_tasks
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        result = send_chat_message(vault, "hello", runtime_id="openclaw")
        assert result["ok"] is True
        assert result["recipient"] == "OpenClaw"
        tasks = list_tasks(vault, recipient="OpenClaw")
        assert any(t["task_id"] == result["task_id"] for t in tasks)

    def test_send_to_claude_code(self) -> None:
        from runtime.agent_bus.bus import list_tasks
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        result = send_chat_message(vault, "hello", runtime_id="claude-code")
        assert result["ok"] is True
        assert result["recipient"] == "Archon"
        tasks = list_tasks(vault, recipient="Archon")
        assert any(t["task_id"] == result["task_id"] for t in tasks)

    def test_unknown_runtime_id_falls_back_to_hermes(self) -> None:
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        result = send_chat_message(vault, "hello", runtime_id="nonexistent-runtime")
        assert result["ok"] is True
        assert result["recipient"] == "Hermes"

    def test_status_message_contains_recipient_name(self) -> None:
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        result = send_chat_message(vault, "hello", runtime_id="openclaw")
        assert "OPENCLAW" in result["status"]

    def test_authority_carries_selected_runtime_id(self) -> None:
        from runtime.studio.phase11_chat_send_message import send_chat_message

        vault = _temp_vault()
        result = send_chat_message(vault, "hello", runtime_id="openclaw")
        assert result["authority"]["selected_runtime_id"] == "openclaw"

    def test_poll_finds_openclaw_task(self) -> None:
        from runtime.studio.phase11_chat_send_message import poll_chat_result, send_chat_message

        vault = _temp_vault()
        sent = send_chat_message(vault, "test", runtime_id="openclaw")
        polled = poll_chat_result(vault, sent["task_id"])
        assert polled["ok"] is True
        assert polled["task_id"] == sent["task_id"]

    def test_poll_finds_claude_code_task(self) -> None:
        from runtime.studio.phase11_chat_send_message import poll_chat_result, send_chat_message

        vault = _temp_vault()
        sent = send_chat_message(vault, "test", runtime_id="claude-code")
        polled = poll_chat_result(vault, sent["task_id"])
        assert polled["ok"] is True
        assert polled["task_id"] == sent["task_id"]


# ── Archon watch _dispatch_chat ────────────────────────────────────────────────


class TestArchonChatDispatch:
    def test_chat_in_dispatch_table(self) -> None:
        from runtime.workflows.archon_watch import _TASK_DISPATCH
        assert "chat" in _TASK_DISPATCH

    def test_dispatch_chat_claims_and_completes_task(self) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks
        from runtime.workflows.archon_watch import _dispatch_chat

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="Archon", intent="TASK",
                        priority="normal", request="Hello Archon from test",
                        expected_output="chat-response",
                        notes="task_type: chat\nsession_id: test-archon-001")
        tasks = list_tasks(vault, recipient="Archon")
        task = next(t for t in tasks if t["task_id"] == r["task_id"])

        result = _dispatch_chat(task, vault, synthesize=False)
        assert result["task_id"] == r["task_id"]
        assert result["status"] == "done"
        assert result["task_type"] == "chat"

    def test_dispatch_chat_no_synthesis_returns_ack(self) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks
        from runtime.workflows.archon_watch import _dispatch_chat

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="Archon", intent="TASK",
                        priority="normal", request="test message",
                        expected_output="chat-response", notes="task_type: chat")
        tasks = list_tasks(vault, recipient="Archon")
        task = next(t for t in tasks if t["task_id"] == r["task_id"])

        result = _dispatch_chat(task, vault, synthesize=False)
        assert result["runtime_handled"] is False
        assert "[Archon bounded ack]" in result["response_preview"]

    def test_dispatch_chat_has_audit_writeback(self) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks
        from runtime.workflows.archon_watch import _dispatch_chat

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="Archon", intent="TASK",
                        priority="normal", request="test",
                        expected_output="chat-response", notes="task_type: chat")
        tasks = list_tasks(vault, recipient="Archon")
        task = next(t for t in tasks if t["task_id"] == r["task_id"])

        result = _dispatch_chat(task, vault, synthesize=False)
        assert len(result["writebacks"]) == 1
        wb = result["writebacks"][0]
        assert "archon-chat" in wb["path"]
        assert wb["path"].startswith("07_LOGS/Agent-Activity/")

    def test_dispatch_chat_marks_task_done(self) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks
        from runtime.workflows.archon_watch import _dispatch_chat

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="Archon", intent="TASK",
                        priority="normal", request="test",
                        expected_output="chat-response", notes="task_type: chat")
        task_id = r["task_id"]
        tasks = list_tasks(vault, recipient="Archon")
        task = next(t for t in tasks if t["task_id"] == task_id)

        _dispatch_chat(task, vault, synthesize=False)
        updated = list_tasks(vault, recipient="Archon")
        updated_task = next(t for t in updated if t["task_id"] == task_id)
        assert updated_task["status"] == "done"


# ── OpenClaw watch _dispatch_chat ─────────────────────────────────────────────


class TestOpenClawChatDispatch:
    def test_chat_in_dispatch_table(self) -> None:
        from runtime.workflows.openclaw_watch import _TASK_DISPATCH
        assert "chat" in _TASK_DISPATCH

    def test_dispatch_chat_returns_result_with_summary(self) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks
        from runtime.workflows.openclaw_watch import _dispatch_chat

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="OpenClaw", intent="TASK",
                        priority="normal", request="Hello OpenClaw from test",
                        expected_output="chat-response",
                        notes="task_type: chat\nsession_id: test-openclaw-001")
        tasks = list_tasks(vault, recipient="OpenClaw")
        task = next(t for t in tasks if t["task_id"] == r["task_id"])

        result = _dispatch_chat(task, vault)
        assert result["task_id"] == r["task_id"]
        assert result["status"] == "done"
        assert result["task_type"] == "chat"
        assert "summary" in result

    def test_dispatch_chat_no_synthesis_returns_ack(self) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks
        from runtime.workflows.openclaw_watch import _dispatch_chat

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="OpenClaw", intent="TASK",
                        priority="normal", request="test message",
                        expected_output="chat-response", notes="task_type: chat")
        tasks = list_tasks(vault, recipient="OpenClaw")
        task = next(t for t in tasks if t["task_id"] == r["task_id"])

        result = _dispatch_chat(task, vault)
        assert result["runtime_handled"] is False
        assert "[OpenClaw bounded ack]" in result["response_preview"]

    def test_dispatch_chat_has_audit_writeback(self) -> None:
        from runtime.agent_bus.bus import create_task, list_tasks
        from runtime.workflows.openclaw_watch import _dispatch_chat

        vault = _temp_vault()
        r = create_task(vault, sender="Codex", recipient="OpenClaw", intent="TASK",
                        priority="normal", request="test",
                        expected_output="chat-response", notes="task_type: chat")
        tasks = list_tasks(vault, recipient="OpenClaw")
        task = next(t for t in tasks if t["task_id"] == r["task_id"])

        result = _dispatch_chat(task, vault)
        assert len(result["writebacks"]) == 1
        wb = result["writebacks"][0]
        assert "openclaw-chat" in wb["path"]
        assert wb["path"].startswith("07_LOGS/Agent-Activity/")


# ── Companion display name integration ───────────────────────────────────────


class TestCompanionDisplayNames:
    def test_policy_has_claude_code_not_archon(self) -> None:
        from runtime.companion.policy import INITIAL_COMPANION_IDS
        assert "claude-code" in INITIAL_COMPANION_IDS
        assert "archon" not in INITIAL_COMPANION_IDS

    def test_roster_has_claude_code_entry(self) -> None:
        from runtime.companion.roster import CORE_COMPANION_METADATA
        assert "claude-code" in CORE_COMPANION_METADATA
        assert "archon" not in CORE_COMPANION_METADATA

    def test_get_companion_display_name_hermes(self, tmp_path) -> None:
        from runtime.companion.roster import get_companion_display_name
        name = get_companion_display_name("hermes", tmp_path)
        assert name == "Hermes"

    def test_get_companion_display_name_openclaw(self, tmp_path) -> None:
        from runtime.companion.roster import get_companion_display_name
        name = get_companion_display_name("openclaw", tmp_path)
        assert name == "OpenClaw"

    def test_get_companion_display_name_claude_code_defaults(self, tmp_path) -> None:
        from runtime.companion.roster import get_companion_display_name
        name = get_companion_display_name("claude-code", tmp_path)
        assert name == "Claude Code"

    def test_get_companion_display_name_no_vault(self) -> None:
        from runtime.companion.roster import get_companion_display_name
        name = get_companion_display_name("hermes")
        assert name == "Hermes"
