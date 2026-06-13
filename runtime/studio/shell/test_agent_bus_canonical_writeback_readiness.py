"""Tests for agent_bus_canonical_writeback_readiness.py.

Verifies the two-lane readiness surface (Agent Bus + canonical writeback)
without performing real network calls, real bus task writes, or vault mutations.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "00_HOME").mkdir()
    (vault / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    bus_dir = vault / "runtime" / "agent_bus"
    bus_dir.mkdir(parents=True)
    return vault


def _init_bus(vault: Path) -> None:
    from runtime.agent_bus.bus import init_db
    init_db(vault)


def _seed_bus_db(vault: Path) -> None:
    """Init the bus database so bus_storage check passes."""
    _init_bus(vault)


def _build(vault: Path, **kwargs) -> dict[str, Any]:
    from runtime.studio.agent_bus_canonical_writeback_readiness import (
        build_agent_bus_canonical_writeback_readiness,
    )
    return build_agent_bus_canonical_writeback_readiness(vault, **kwargs)


# ── TestTopLevelShape ─────────────────────────────────────────────────────────

class TestTopLevelShape:
    def test_returns_dict(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        assert isinstance(result, dict)

    def test_required_keys_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        for key in ("ok", "pass", "surface", "model_version", "status",
                    "generated_at_utc", "vault_root", "checks",
                    "blocked_reasons", "bus_lane", "writeback_lane",
                    "summary", "authority"):
            assert key in result, f"missing key: {key}"

    def test_pass_id(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        assert result["pass"] == "agent-bus-or-canonical-writeback-readiness"

    def test_surface_id(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        assert result["surface"] == "agent_bus_canonical_writeback_readiness"

    def test_model_version(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        assert result["model_version"] == "studio.agent_bus_canonical_writeback_readiness.v1"

    def test_vault_root_in_result(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        assert str(vault.resolve()) in result["vault_root"]

    def test_generated_at_utc_format(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        assert result["generated_at_utc"].endswith("Z")

    def test_authority_read_only(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        auth = result["authority"]
        assert auth["read_only"] is True
        assert auth["agent_bus_task_write_performed"] is False
        assert auth["approval_consumed"] is False
        assert auth["canonical_mutation_performed"] is False


# ── TestBusStorageCheck ───────────────────────────────────────────────────────

class TestBusStorageCheck:
    def test_bus_storage_not_present_without_db(self, tmp_path):
        vault = _make_vault(tmp_path)
        # No bus DB initialised — should report not present
        result = _build(vault)
        assert result["checks"]["bus_storage_accessible"] is False
        assert "agent_bus_storage_not_present" in result["blocked_reasons"]

    def test_bus_storage_present_after_init(self, tmp_path):
        vault = _make_vault(tmp_path)
        _seed_bus_db(vault)
        result = _build(vault)
        assert result["checks"]["bus_storage_accessible"] is True
        assert "agent_bus_storage_not_present" not in result["blocked_reasons"]

    def test_bus_lane_storage_detail(self, tmp_path):
        vault = _make_vault(tmp_path)
        _seed_bus_db(vault)
        result = _build(vault)
        storage = result["bus_lane"]["storage"]
        assert storage["ok"] is True
        assert "agent_bus.sqlite" in storage["path"]
        assert storage["size_bytes"] is not None


# ── TestRuntimeOnlineCheck ────────────────────────────────────────────────────

class TestRuntimeOnlineCheck:
    def test_no_runtime_online_without_heartbeat(self, tmp_path, monkeypatch):
        vault = _make_vault(tmp_path)
        _seed_bus_db(vault)
        # Stub out the dispatch verification import so it always reports offline
        import runtime.studio.agent_bus_canonical_writeback_readiness as _mod
        monkeypatch.setattr(
            _mod,
            "_check_runtime_online",
            lambda _vault: {"ok": False, "any_online": False, "online_runtimes": [], "total_checked": 0},
        )
        result = _build(vault)
        assert result["checks"]["any_runtime_online"] is False
        assert "no_runtime_online" in result["blocked_reasons"]

    def test_runtime_online_with_fresh_heartbeat(self, tmp_path, monkeypatch):
        vault = _make_vault(tmp_path)
        _seed_bus_db(vault)
        import runtime.studio.agent_bus_canonical_writeback_readiness as _mod
        monkeypatch.setattr(
            _mod,
            "_check_runtime_online",
            lambda _vault: {"ok": True, "any_online": True, "online_runtimes": ["hermes"], "total_checked": 2},
        )
        result = _build(vault)
        assert result["checks"]["any_runtime_online"] is True
        assert "no_runtime_online" not in result["blocked_reasons"]
        assert result["summary"]["any_runtime_online"] is True
        assert "hermes" in result["summary"]["online_runtimes"]


# ── TestSendPollImportable ────────────────────────────────────────────────────

class TestSendPollImportable:
    def test_send_poll_importable(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        # These modules exist in the repo — should always be importable
        assert result["checks"]["send_chat_message_importable"] is True
        assert result["checks"]["poll_chat_result_importable"] is True

    def test_send_poll_not_importable_stub(self, tmp_path, monkeypatch):
        vault = _make_vault(tmp_path)
        import runtime.studio.agent_bus_canonical_writeback_readiness as _mod
        monkeypatch.setattr(
            _mod,
            "_check_send_poll_importable",
            lambda: {"ok": False, "send_callable": False, "poll_callable": False,
                     "error": "No module named 'runtime.studio.phase11_chat_send_message'"},
        )
        result = _build(vault)
        assert result["checks"]["send_chat_message_importable"] is False
        assert "send_poll_not_importable" in result["blocked_reasons"]


# ── TestChatTaskTypeRegistered ────────────────────────────────────────────────

class TestChatTaskTypeRegistered:
    def test_chat_task_type_registered(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        assert result["checks"]["chat_task_type_registered"] is True

    def test_chat_task_type_not_registered_stub(self, tmp_path, monkeypatch):
        vault = _make_vault(tmp_path)
        import runtime.studio.agent_bus_canonical_writeback_readiness as _mod
        monkeypatch.setattr(
            _mod,
            "_check_chat_task_type_registered",
            lambda: {"ok": False, "task_type": "chat", "error": "classify failed"},
        )
        result = _build(vault)
        assert result["checks"]["chat_task_type_registered"] is False
        assert "chat_task_type_not_registered" in result["blocked_reasons"]


# ── TestBusResponseCheckModule ────────────────────────────────────────────────

class TestBusResponseCheckModule:
    def test_bus_response_check_informational_only(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        # Module should be importable; note: even if absent it's not a blocker
        bus_check = result["bus_lane"]["bus_check_module"]
        assert "ok" in bus_check

    def test_bus_response_check_not_a_blocker_when_absent(self, tmp_path, monkeypatch):
        vault = _make_vault(tmp_path)
        import runtime.studio.agent_bus_canonical_writeback_readiness as _mod
        monkeypatch.setattr(
            _mod,
            "_check_bus_response_check_available",
            lambda: {"ok": False, "error": "No module named 'runtime.studio.runtime_bus_response_check'"},
        )
        result = _build(vault)
        # Missing bus_response_check module must NOT add a blocked reason
        assert "bus_response_check_not_available" not in result["blocked_reasons"]


# ── TestWritebackDirs ─────────────────────────────────────────────────────────

class TestWritebackDirs:
    def test_writeback_dirs_ok_even_when_absent(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        # Missing dirs are lazy-create — never a blocker
        assert result["checks"]["writeback_dirs_ok"] is True

    def test_writeback_dirs_present_count(self, tmp_path):
        vault = _make_vault(tmp_path)
        # Create some of the dirs
        (vault / "07_LOGS" / "Conversations").mkdir(parents=True)
        result = _build(vault)
        dirs_detail = result["writeback_lane"]["dirs"]
        assert dirs_detail["total"] == 4
        assert dirs_detail["present_count"] >= 1

    def test_all_writeback_dirs_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        for rel in ("07_LOGS/Conversations", "07_LOGS/Agent-Activity",
                    "07_LOGS/Operator-Briefs", "runtime/studio/approvals"):
            (vault / rel).mkdir(parents=True)
        result = _build(vault)
        assert result["writeback_lane"]["dirs"]["present_count"] == 4


# ── TestConversationLogWriter ─────────────────────────────────────────────────

class TestConversationLogWriter:
    def test_conversation_log_writer_importable(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        assert result["checks"]["conversation_log_writer_importable"] is True

    def test_conversation_log_writer_not_importable_stub(self, tmp_path, monkeypatch):
        vault = _make_vault(tmp_path)
        import runtime.studio.agent_bus_canonical_writeback_readiness as _mod
        monkeypatch.setattr(
            _mod,
            "_check_conversation_log_writer",
            lambda: {"ok": False, "error": "No module named 'phase11_chat_conversation_log_writer'"},
        )
        result = _build(vault)
        assert result["checks"]["conversation_log_writer_importable"] is False
        assert "conversation_log_writer_not_importable" in result["blocked_reasons"]


# ── TestApprovalGate ──────────────────────────────────────────────────────────

class TestApprovalGate:
    def test_approval_gate_wired(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        assert result["checks"]["approval_gate_wired"] is True

    def test_approval_gate_not_importable_stub(self, tmp_path, monkeypatch):
        vault = _make_vault(tmp_path)
        import runtime.studio.agent_bus_canonical_writeback_readiness as _mod
        monkeypatch.setattr(
            _mod,
            "_check_approval_gate_wired",
            lambda: {"ok": False, "error": "No module named 'runtime.studio.service'"},
        )
        result = _build(vault)
        assert result["checks"]["approval_gate_wired"] is False
        assert "approval_gate_not_importable" in result["blocked_reasons"]

    def test_writeback_lane_auto_promote_always_blocked(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _build(vault)
        wl = result["writeback_lane"]
        assert wl["auto_promote_blocked"] is True
        assert wl["explicit_approval_required"] is True


# ── TestLaneOkLogic ───────────────────────────────────────────────────────────

class TestLaneOkLogic:
    def _all_checks_ok(self, tmp_path, monkeypatch) -> dict:
        """Return result with all checks passing via stubs."""
        vault = _make_vault(tmp_path)
        _seed_bus_db(vault)
        import runtime.studio.agent_bus_canonical_writeback_readiness as _mod
        monkeypatch.setattr(_mod, "_check_runtime_online",
            lambda _v: {"ok": True, "any_online": True, "online_runtimes": ["hermes"], "total_checked": 2})
        monkeypatch.setattr(_mod, "_check_send_poll_importable",
            lambda: {"ok": True, "send_callable": True, "poll_callable": True})
        monkeypatch.setattr(_mod, "_check_chat_task_type_registered",
            lambda: {"ok": True, "task_type": "chat", "classify_result": {"classified": True}})
        monkeypatch.setattr(_mod, "_check_conversation_log_writer",
            lambda: {"ok": True, "module": "phase11_chat_conversation_log_writer"})
        monkeypatch.setattr(_mod, "_check_approval_gate_wired",
            lambda: {"ok": True, "gate": "StudioService approval gate active",
                     "auto_promote_blocked": True, "explicit_approval_required": True})
        return _build(vault)

    def test_all_ok_produces_ready_status(self, tmp_path, monkeypatch):
        result = self._all_checks_ok(tmp_path, monkeypatch)
        assert result["ok"] is True
        assert "READY" in result["status"]

    def test_bus_lane_ok(self, tmp_path, monkeypatch):
        result = self._all_checks_ok(tmp_path, monkeypatch)
        assert result["bus_lane"]["ok"] is True

    def test_writeback_lane_ok(self, tmp_path, monkeypatch):
        result = self._all_checks_ok(tmp_path, monkeypatch)
        assert result["writeback_lane"]["ok"] is True

    def test_summary_next_recommended_pass(self, tmp_path, monkeypatch):
        result = self._all_checks_ok(tmp_path, monkeypatch)
        assert result["summary"]["next_recommended_pass"] == "phase11-production-operator-dispatch-readiness"

    def test_partial_status_bus_only(self, tmp_path, monkeypatch):
        """Bus lane OK but writeback lane failing → PARTIAL status."""
        vault = _make_vault(tmp_path)
        _seed_bus_db(vault)
        import runtime.studio.agent_bus_canonical_writeback_readiness as _mod
        monkeypatch.setattr(_mod, "_check_runtime_online",
            lambda _v: {"ok": True, "any_online": True, "online_runtimes": ["hermes"], "total_checked": 2})
        monkeypatch.setattr(_mod, "_check_send_poll_importable",
            lambda: {"ok": True, "send_callable": True, "poll_callable": True})
        monkeypatch.setattr(_mod, "_check_chat_task_type_registered",
            lambda: {"ok": True, "task_type": "chat", "classify_result": {"classified": True}})
        monkeypatch.setattr(_mod, "_check_conversation_log_writer",
            lambda: {"ok": False, "error": "missing"})
        monkeypatch.setattr(_mod, "_check_approval_gate_wired",
            lambda: {"ok": False, "error": "missing"})
        result = _build(vault)
        assert "PARTIAL" in result["status"]
        assert result["bus_lane"]["ok"] is True
        assert result["writeback_lane"]["ok"] is False

    def test_partial_status_writeback_only(self, tmp_path, monkeypatch):
        """Writeback lane OK but bus lane failing → PARTIAL status."""
        vault = _make_vault(tmp_path)
        # No bus DB → bus_storage fails
        import runtime.studio.agent_bus_canonical_writeback_readiness as _mod
        monkeypatch.setattr(_mod, "_check_runtime_online",
            lambda _v: {"ok": True, "any_online": True, "online_runtimes": ["hermes"], "total_checked": 2})
        monkeypatch.setattr(_mod, "_check_conversation_log_writer",
            lambda: {"ok": True, "module": "phase11_chat_conversation_log_writer"})
        monkeypatch.setattr(_mod, "_check_approval_gate_wired",
            lambda: {"ok": True, "gate": "StudioService approval gate active",
                     "auto_promote_blocked": True, "explicit_approval_required": True})
        result = _build(vault)
        assert "PARTIAL" in result["status"]
        assert result["writeback_lane"]["ok"] is True

    def test_not_ready_status_with_multiple_blockers(self, tmp_path, monkeypatch):
        vault = _make_vault(tmp_path)
        import runtime.studio.agent_bus_canonical_writeback_readiness as _mod
        monkeypatch.setattr(_mod, "_check_runtime_online",
            lambda _v: {"ok": False, "any_online": False, "online_runtimes": [], "total_checked": 0})
        monkeypatch.setattr(_mod, "_check_send_poll_importable",
            lambda: {"ok": False, "send_callable": False, "poll_callable": False, "error": "missing"})
        monkeypatch.setattr(_mod, "_check_conversation_log_writer",
            lambda: {"ok": False, "error": "missing"})
        monkeypatch.setattr(_mod, "_check_approval_gate_wired",
            lambda: {"ok": False, "error": "missing"})
        result = _build(vault)
        assert result["ok"] is False
        assert "NOT READY" in result["status"]
        assert len(result["blocked_reasons"]) >= 3

    def test_blocked_reason_count_in_summary(self, tmp_path, monkeypatch):
        vault = _make_vault(tmp_path)
        import runtime.studio.agent_bus_canonical_writeback_readiness as _mod
        monkeypatch.setattr(_mod, "_check_runtime_online",
            lambda _v: {"ok": False, "any_online": False, "online_runtimes": [], "total_checked": 0})
        result = _build(vault)
        assert result["summary"]["blocked_reason_count"] == len(result["blocked_reasons"])


# ── TestPanelRegistry ─────────────────────────────────────────────────────────

class TestPanelRegistry:
    def _registry(self, tmp_path) -> dict:
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry as build_panel_registry
        vault = _make_vault(tmp_path)
        return build_panel_registry(vault)

    def test_agent_bus_canonical_writeback_readiness_mounted(self, tmp_path):
        r = self._registry(tmp_path)
        flags = r["readiness"]
        assert flags.get("agent_bus_canonical_writeback_readiness_mounted") is True

    def test_runtime_bus_response_check_mounted(self, tmp_path):
        r = self._registry(tmp_path)
        flags = r["readiness"]
        assert flags.get("runtime_bus_response_check_mounted") is True

    def test_next_recommended_pass_advanced(self, tmp_path):
        r = self._registry(tmp_path)
        flags = r["readiness"]
        nxt = flags.get("next_recommended_pass", "")
        assert nxt != "agent-bus-or-canonical-writeback-readiness", (
            "next_recommended_pass must advance past agent-bus-or-canonical-writeback-readiness"
        )
        assert nxt == "ventureops-operator-readiness-gate"


# ── TestApiMethod ─────────────────────────────────────────────────────────────

class TestApiMethod:
    def _api(self, tmp_path) -> Any:
        from runtime.studio.shell.api import StudioAPI
        vault = _make_vault(tmp_path)
        _seed_bus_db(vault)
        return StudioAPI(str(vault))

    def test_api_method_exists(self, tmp_path):
        api = self._api(tmp_path)
        assert hasattr(api, "get_agent_bus_canonical_writeback_readiness")
        assert callable(api.get_agent_bus_canonical_writeback_readiness)

    def test_api_method_returns_dict(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_agent_bus_canonical_writeback_readiness()
        assert isinstance(result, dict)

    def test_api_method_ok_key_present(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_agent_bus_canonical_writeback_readiness()
        assert "ok" in result

    def test_api_envelope_surface(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_agent_bus_canonical_writeback_readiness()
        assert result.get("surface") == "get_agent_bus_canonical_writeback_readiness"

    def test_api_data_has_pass_id(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_agent_bus_canonical_writeback_readiness()
        data = result.get("data") or {}
        assert data.get("pass") == "agent-bus-or-canonical-writeback-readiness"
