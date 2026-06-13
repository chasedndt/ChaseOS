"""Tests verifying the provider-agnostic rule for Studio Chat runtime dispatch.

Architecture rule: Studio Chat routes through Agent Bus. Runtimes (Hermes, OpenClaw, Archon)
dispatch chat via execute_synthesis() — never by calling any model provider directly.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_synthesis_result(text: str = "synthesized reply") -> SimpleNamespace:
    return SimpleNamespace(text=text, model_id="test-model", runtime="hermes", usage={}, fallback_used=False)


# ---------------------------------------------------------------------------
# Hermes
# ---------------------------------------------------------------------------

class TestHermesChatDispatch:
    def test_routes_through_execute_synthesis(self, tmp_path):
        from runtime.workflows.hermes_watch import _hermes_runtime_chat

        with patch("runtime.workflows.hermes_watch.call_hermes_chat_bridge", return_value={"ok": False, "error": "test_bridge_unavailable"}), \
             patch("runtime.execution_adapters.execute.execute_synthesis", return_value=_mock_synthesis_result()) as mock_synth:
            result = _hermes_runtime_chat("hello hermes", vault_root=tmp_path)

        assert result == "synthesized reply"
        mock_synth.assert_called_once()
        assert mock_synth.call_args[1]["execution_adapter"] == "hermes"
        assert mock_synth.call_args[1]["prompt_user"] == "hello hermes"

    def test_uses_hermes_adapter(self, tmp_path):
        from runtime.workflows.hermes_watch import _hermes_runtime_chat

        with patch("runtime.workflows.hermes_watch.call_hermes_chat_bridge", return_value={"ok": False, "error": "test_bridge_unavailable"}), \
             patch("runtime.execution_adapters.execute.execute_synthesis", return_value=_mock_synthesis_result()) as mock_synth:
            _hermes_runtime_chat("test", vault_root=tmp_path)

        assert mock_synth.call_args[1]["execution_adapter"] == "hermes"

    def test_fail_open_on_exception(self, tmp_path):
        from runtime.workflows.hermes_watch import _hermes_runtime_chat

        with patch("runtime.workflows.hermes_watch.call_hermes_chat_bridge", return_value={"ok": False, "error": "test_bridge_unavailable"}), \
             patch("runtime.execution_adapters.execute.execute_synthesis", side_effect=RuntimeError("no key")):
            result = _hermes_runtime_chat("test", vault_root=tmp_path)

        assert result is None

    def test_empty_synthesis_result_returns_none(self, tmp_path):
        from runtime.workflows.hermes_watch import _hermes_runtime_chat

        with patch("runtime.workflows.hermes_watch.call_hermes_chat_bridge", return_value={"ok": False, "error": "test_bridge_unavailable"}), \
             patch("runtime.execution_adapters.execute.execute_synthesis", return_value=_mock_synthesis_result(text="   ")):
            result = _hermes_runtime_chat("test", vault_root=tmp_path)

        assert result is None

    def test_no_direct_provider_url_in_hermes_watch(self):
        src = (Path(__file__).resolve().parents[2] / "runtime" / "workflows" / "hermes_watch.py").read_text(encoding="utf-8")
        assert "api.anthropic.com" not in src
        assert "api.openai.com" not in src
        assert "api.x.ai" not in src


# ---------------------------------------------------------------------------
# OpenClaw
# ---------------------------------------------------------------------------

class TestOpenClawChatDispatch:
    def test_bus_dispatch_only_returns_none(self, tmp_path):
        """OpenClaw is bus-dispatch-only. Chat synthesis routes via Agent Bus to Hermes.
        Until bus-based chat coordination is built, the stub returns None."""
        from runtime.workflows.openclaw_watch import _openclaw_runtime_chat

        with patch("runtime.execution_adapters.execute.execute_synthesis") as mock_synth:
            result = _openclaw_runtime_chat("hello openclaw", vault_root=tmp_path)

        assert result is None
        mock_synth.assert_not_called()

    def test_no_direct_provider_url_in_openclaw_watch(self):
        src = (Path(__file__).resolve().parents[2] / "runtime" / "workflows" / "openclaw_watch.py").read_text(encoding="utf-8")
        assert "api.anthropic.com" not in src
        assert "api.openai.com" not in src
        assert "api.x.ai" not in src

    def test_does_not_import_execute_synthesis(self):
        src = (Path(__file__).resolve().parents[2] / "runtime" / "workflows" / "openclaw_watch.py").read_text(encoding="utf-8")
        assert "execute_synthesis" not in src


# ---------------------------------------------------------------------------
# Archon
# ---------------------------------------------------------------------------

class TestArchonChatDispatch:
    def test_routes_through_execute_synthesis(self, tmp_path):
        from runtime.workflows.archon_watch import _archon_runtime_chat

        with patch("runtime.execution_adapters.execute.execute_synthesis", return_value=_mock_synthesis_result("archon reply")) as mock_synth:
            result = _archon_runtime_chat("hello archon", vault_root=tmp_path)

        assert result == "archon reply"
        mock_synth.assert_called_once()
        assert mock_synth.call_args[1]["execution_adapter"] == "archon"
        assert mock_synth.call_args[1]["prompt_user"] == "hello archon"

    def test_uses_archon_adapter(self, tmp_path):
        from runtime.workflows.archon_watch import _archon_runtime_chat

        with patch("runtime.execution_adapters.execute.execute_synthesis", return_value=_mock_synthesis_result()) as mock_synth:
            _archon_runtime_chat("test", vault_root=tmp_path)

        assert mock_synth.call_args[1]["execution_adapter"] == "archon"

    def test_fail_open_on_exception(self, tmp_path):
        from runtime.workflows.archon_watch import _archon_runtime_chat

        with patch("runtime.execution_adapters.execute.execute_synthesis", side_effect=RuntimeError("no key")):
            result = _archon_runtime_chat("test", vault_root=tmp_path)

        assert result is None

    def test_no_direct_provider_url_in_archon_watch(self):
        src = (Path(__file__).resolve().parents[2] / "runtime" / "workflows" / "archon_watch.py").read_text(encoding="utf-8")
        assert "api.anthropic.com" not in src
        assert "api.openai.com" not in src
        assert "api.x.ai" not in src


# ---------------------------------------------------------------------------
# execute_synthesis adapter mapping
# ---------------------------------------------------------------------------

class TestAdapterToRuntimeMapping:
    def test_archon_maps_to_hermes_runtime(self):
        from runtime.execution_adapters.execute import ADAPTER_TO_RUNTIME
        assert ADAPTER_TO_RUNTIME["archon"] == "hermes"

    def test_hermes_maps_to_hermes_runtime(self):
        from runtime.execution_adapters.execute import ADAPTER_TO_RUNTIME
        assert ADAPTER_TO_RUNTIME["hermes"] == "hermes"

    def test_openclaw_maps_to_openclaw_runtime(self):
        from runtime.execution_adapters.execute import ADAPTER_TO_RUNTIME
        assert ADAPTER_TO_RUNTIME["openclaw"] == "openclaw"

    def test_unknown_adapter_raises(self):
        from runtime.execution_adapters.execute import _resolve_runtime, ExecutionAdapterError
        try:
            _resolve_runtime("unknown-xyz")
            assert False, "should have raised"
        except ExecutionAdapterError:
            pass
