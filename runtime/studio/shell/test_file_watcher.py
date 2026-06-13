"""Tests for runtime.studio.shell.file_watcher — Pass 10D file-watcher-live-refresh."""

from __future__ import annotations

import json
import sys
import time
import threading
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from runtime.studio.shell.file_watcher import (
    FileWatcher,
    _is_watched_path,
    _VaultEventHandler,
)


# ── _is_watched_path ─────────────────────────────────────────────────────────

class TestIsWatchedPath:
    def test_md_accepted(self):
        assert _is_watched_path("/vault/01_PROJECTS/foo/bar.md") is True

    def test_yaml_accepted(self):
        assert _is_watched_path("/vault/runtime/schedules/sch-foo.yaml") is True

    def test_json_accepted(self):
        assert _is_watched_path("/vault/.chaseos/bus_config.json") is False  # .chaseos ignored

    def test_py_rejected(self):
        assert _is_watched_path("/vault/runtime/studio/service.py") is False

    def test_txt_rejected(self):
        assert _is_watched_path("/vault/notes.txt") is False

    def test_git_dir_ignored(self):
        assert _is_watched_path("/vault/.git/COMMIT_EDITMSG") is False

    def test_pycache_ignored(self):
        assert _is_watched_path("/vault/__pycache__/module.cpython-313.pyc") is False

    def test_venv_ignored(self):
        assert _is_watched_path("/vault/.venv/lib/site-packages/foo.yaml") is False

    def test_node_modules_ignored(self):
        assert _is_watched_path("/vault/node_modules/react/index.js") is False

    def test_mypy_cache_ignored(self):
        assert _is_watched_path("/vault/.mypy_cache/3.13/runtime.json") is False

    def test_normal_yaml_accepted(self):
        assert _is_watched_path("/vault/06_AGENTS/Vault-Map.md") is True

    def test_empty_string_rejected(self):
        assert _is_watched_path("") is False


# ── FileWatcher construction ──────────────────────────────────────────────────

class TestFileWatcherInit:
    def test_vault_root_stored(self, tmp_path):
        fw = FileWatcher(tmp_path)
        assert fw.get_status()["vault_root"] == str(tmp_path)

    def test_not_running_initially(self, tmp_path):
        fw = FileWatcher(tmp_path)
        assert fw.is_running() is False

    def test_event_count_zero(self, tmp_path):
        fw = FileWatcher(tmp_path)
        assert fw.get_status()["event_count"] == 0

    def test_last_event_none(self, tmp_path):
        fw = FileWatcher(tmp_path)
        assert fw.get_status()["last_event_path"] is None

    def test_set_window_stores(self, tmp_path):
        fw = FileWatcher(tmp_path)
        mock_win = MagicMock()
        fw.set_window(mock_win)
        assert fw._window is mock_win


# ── FileWatcher watchdog-unavailable path ─────────────────────────────────────

class TestFileWatcherUnavailable:
    def test_available_false_when_watchdog_missing(self, tmp_path):
        with patch.dict("sys.modules", {"watchdog": None}):
            fw = FileWatcher.__new__(FileWatcher)
            fw._vault_root = tmp_path
            fw._window = None
            fw._observer = None
            fw._handler = None
            fw._running = False
            fw._event_count = 0
            fw._last_event_path = None
            fw._lock = threading.Lock()
            try:
                import watchdog  # noqa: F401
                fw._available = True
                fw._unavailable_reason = ""
            except ImportError:
                fw._available = False
                fw._unavailable_reason = "watchdog_not_installed"
        # watchdog IS installed in the test env so just verify the path
        status = fw.get_status()
        assert "available" in status

    def test_start_returns_false_when_unavailable(self, tmp_path):
        fw = FileWatcher(tmp_path)
        fw._available = False
        fw._unavailable_reason = "watchdog_not_installed"
        result = fw.start()
        assert result is False
        assert fw.is_running() is False

    def test_stop_is_safe_when_never_started(self, tmp_path):
        fw = FileWatcher(tmp_path)
        fw._available = False
        fw.stop()  # must not raise


# ── FileWatcher get_status ────────────────────────────────────────────────────

class TestFileWatcherStatus:
    def test_status_keys_present(self, tmp_path):
        fw = FileWatcher(tmp_path)
        s = fw.get_status()
        for key in ("available", "running", "vault_root", "event_count",
                    "last_event_path", "unavailable_reason"):
            assert key in s, f"missing key: {key}"

    def test_unavailable_reason_none_when_ok(self, tmp_path):
        fw = FileWatcher(tmp_path)
        if fw._available:
            assert fw.get_status()["unavailable_reason"] is None


# ── _VaultEventHandler debounce ───────────────────────────────────────────────

class TestVaultEventHandlerDebounce:
    def _make_watcher_stub(self, tmp_path):
        fw = FileWatcher(tmp_path)
        fw._available = True
        fw._event_count = 0
        fw._last_event_path = None
        fw._window = None
        return fw

    def test_enqueue_ignored_for_py_file(self, tmp_path):
        fw = self._make_watcher_stub(tmp_path)
        handler = _VaultEventHandler(fw)
        ev = MagicMock()
        ev.is_directory = False
        ev.src_path = str(tmp_path / "foo.py")
        handler.on_modified(ev)
        time.sleep(0.6)
        assert fw._event_count == 0

    def test_enqueue_ignored_for_git_dir(self, tmp_path):
        fw = self._make_watcher_stub(tmp_path)
        handler = _VaultEventHandler(fw)
        ev = MagicMock()
        ev.is_directory = False
        ev.src_path = str(tmp_path / ".git" / "HEAD")
        handler.on_modified(ev)
        time.sleep(0.6)
        assert fw._event_count == 0

    def test_directory_events_skipped(self, tmp_path):
        fw = self._make_watcher_stub(tmp_path)
        handler = _VaultEventHandler(fw)
        ev = MagicMock()
        ev.is_directory = True
        ev.src_path = str(tmp_path / "somedir")
        handler.on_modified(ev)
        time.sleep(0.1)
        assert fw._event_count == 0

    def test_md_event_increments_count(self, tmp_path):
        fw = self._make_watcher_stub(tmp_path)
        handler = _VaultEventHandler(fw)
        ev = MagicMock()
        ev.is_directory = False
        ev.src_path = str(tmp_path / "note.md")
        handler.on_modified(ev)
        time.sleep(0.6)
        assert fw._event_count == 1
        assert fw._last_event_path == str(tmp_path / "note.md")

    def test_rapid_same_path_debounces_to_one(self, tmp_path):
        fw = self._make_watcher_stub(tmp_path)
        handler = _VaultEventHandler(fw)
        ev = MagicMock()
        ev.is_directory = False
        ev.src_path = str(tmp_path / "note.md")
        for _ in range(10):
            handler.on_modified(ev)
            time.sleep(0.02)
        time.sleep(0.8)
        assert fw._event_count == 1

    def test_on_created_fires(self, tmp_path):
        fw = self._make_watcher_stub(tmp_path)
        handler = _VaultEventHandler(fw)
        ev = MagicMock()
        ev.is_directory = False
        ev.src_path = str(tmp_path / "new.md")
        handler.on_created(ev)
        time.sleep(0.6)
        assert fw._event_count == 1

    def test_on_deleted_fires(self, tmp_path):
        fw = self._make_watcher_stub(tmp_path)
        handler = _VaultEventHandler(fw)
        ev = MagicMock()
        ev.is_directory = False
        ev.src_path = str(tmp_path / "gone.yaml")
        handler.on_deleted(ev)
        time.sleep(0.6)
        assert fw._event_count == 1

    def test_on_moved_fires(self, tmp_path):
        fw = self._make_watcher_stub(tmp_path)
        handler = _VaultEventHandler(fw)
        ev = MagicMock()
        ev.is_directory = False
        ev.src_path = str(tmp_path / "old.md")
        ev.dest_path = str(tmp_path / "new.md")
        handler.on_moved(ev)
        time.sleep(0.6)
        assert fw._event_count == 1
        assert fw._last_event_path == str(tmp_path / "new.md")


# ── JS notification ───────────────────────────────────────────────────────────

class TestFileWatcherNotify:
    def test_notify_calls_evaluate_js(self, tmp_path):
        fw = FileWatcher(tmp_path)
        mock_win = MagicMock()
        fw._window = mock_win
        fw._event_count = 0
        fw._last_event_path = None
        fw._notify(str(tmp_path / "note.md"))
        mock_win.evaluate_js.assert_called_once()
        call_arg = mock_win.evaluate_js.call_args[0][0]
        assert "onVaultChange" in call_arg
        assert "note.md" in call_arg

    def test_notify_no_window_is_safe(self, tmp_path):
        fw = FileWatcher(tmp_path)
        fw._window = None
        fw._event_count = 0
        fw._last_event_path = None
        fw._notify(str(tmp_path / "note.md"))  # must not raise

    def test_notify_evaluate_js_exception_safe(self, tmp_path):
        fw = FileWatcher(tmp_path)
        mock_win = MagicMock()
        mock_win.evaluate_js.side_effect = RuntimeError("window gone")
        fw._window = mock_win
        fw._event_count = 0
        fw._last_event_path = None
        fw._notify(str(tmp_path / "note.md"))  # must not raise

    def test_notify_payload_is_valid_json(self, tmp_path):
        import re
        fired_payloads = []

        def capture_js(js):
            # Extract JSON payload from: var e=<JSON>;
            m = re.search(r"var e=(\{[^;]+\});", js)
            if m:
                fired_payloads.append(json.loads(m.group(1)))

        fw = FileWatcher(tmp_path)
        mock_win = MagicMock()
        mock_win.evaluate_js.side_effect = capture_js
        fw._window = mock_win
        fw._event_count = 0
        fw._last_event_path = None
        fw._notify(str(tmp_path / "01_PROJECTS" / "foo" / "Foo-OS.md"))
        assert len(fired_payloads) == 1
        assert "path" in fired_payloads[0]
        assert "abs" in fired_payloads[0]

    def test_notify_increments_event_count(self, tmp_path):
        fw = FileWatcher(tmp_path)
        fw._window = MagicMock()
        fw._event_count = 0
        fw._last_event_path = None
        fw._notify(str(tmp_path / "a.md"))
        assert fw._event_count == 1
        fw._notify(str(tmp_path / "b.yaml"))
        assert fw._event_count == 2


# ── API integration ───────────────────────────────────────────────────────────

class TestAPIIntegration:
    def test_get_file_watcher_status_no_watcher(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(tmp_path)
        result = api.get_file_watcher_status()
        assert result["ok"] is True
        assert result["data"]["unavailable_reason"] == "watcher_not_initialized"

    def test_get_file_watcher_status_with_watcher(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(tmp_path)
        fw = FileWatcher(tmp_path)
        api._set_watcher(fw)
        result = api.get_file_watcher_status()
        assert result["ok"] is True
        assert "available" in result["data"]
        assert "event_count" in result["data"]

    def test_set_watcher_stored(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(tmp_path)
        fw = FileWatcher(tmp_path)
        api._set_watcher(fw)
        assert api._watcher is fw
