"""ChaseOS Studio — vault file watcher (Pass 10D file-watcher-live-refresh).

Watches vault root for .md / .yaml / .json changes and notifies the
WebView frontend via window.evaluate_js() so the graph and project
workspace panel refresh without a manual reload.

Fails gracefully when watchdog is not installed — the shell still runs,
live refresh is simply unavailable.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

_WATCH_EXTENSIONS = {".md", ".yaml", ".json"}

_IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".chaseos",
    "node_modules",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
}

_DEBOUNCE_SECONDS = 0.4


def _is_watched_path(path: str) -> bool:
    p = Path(path)
    if p.suffix.lower() not in _WATCH_EXTENSIONS:
        return False
    for part in p.parts:
        if part in _IGNORED_DIRS:
            return False
    return True


class _VaultEventHandler:
    """Watchdog-compatible event handler with per-path debounce."""

    def __init__(self, watcher: "FileWatcher") -> None:
        self._watcher = watcher
        self._lock = threading.Lock()
        self._pending: dict[str, float] = {}
        self._flush_thread: threading.Thread | None = None
        self._stop_flush = threading.Event()

    def _schedule_flush(self) -> None:
        if self._flush_thread is None or not self._flush_thread.is_alive():
            self._stop_flush.clear()
            self._flush_thread = threading.Thread(
                target=self._flush_loop, daemon=True, name="studio-fw-flush"
            )
            self._flush_thread.start()

    def _flush_loop(self) -> None:
        while not self._stop_flush.wait(timeout=0.1):
            now = time.monotonic()
            to_fire: list[str] = []
            with self._lock:
                for path, deadline in list(self._pending.items()):
                    if now >= deadline:
                        to_fire.append(path)
                for p in to_fire:
                    del self._pending[p]
            for path in to_fire:
                self._watcher._notify(path)
            with self._lock:
                if not self._pending:
                    break

    def _enqueue(self, path: str) -> None:
        if not _is_watched_path(path):
            return
        deadline = time.monotonic() + _DEBOUNCE_SECONDS
        with self._lock:
            self._pending[path] = deadline
        self._schedule_flush()

    def stop_flush(self) -> None:
        self._stop_flush.set()

    # watchdog event dispatch methods
    def on_created(self, event: Any) -> None:
        if not event.is_directory:
            self._enqueue(event.src_path)

    def on_modified(self, event: Any) -> None:
        if not event.is_directory:
            self._enqueue(event.src_path)

    def on_deleted(self, event: Any) -> None:
        if not event.is_directory:
            self._enqueue(event.src_path)

    def on_moved(self, event: Any) -> None:
        if not event.is_directory:
            self._enqueue(getattr(event, "dest_path", event.src_path))


class FileWatcher:
    """
    Watches the vault root directory for file changes and fires JS callbacks
    into the Studio WebView frontend.

    Lifecycle:
        watcher = FileWatcher(vault_root)
        watcher.set_window(pywebview_window)
        watcher.start()
        ...
        watcher.stop()
    """

    def __init__(self, vault_root: str | Path) -> None:
        self._vault_root = Path(vault_root)
        self._window: Any = None
        self._observer: Any = None
        self._handler: _VaultEventHandler | None = None
        self._running = False
        self._available = False
        self._unavailable_reason = ""
        self._event_count = 0
        self._last_event_path: str | None = None
        self._lock = threading.Lock()

        try:
            import watchdog  # noqa: F401
            self._available = True
        except ImportError:
            self._available = False
            self._unavailable_reason = "watchdog_not_installed"

    def set_window(self, window: Any) -> None:
        with self._lock:
            self._window = window

    def start(self) -> bool:
        if not self._available:
            return False
        if self._running:
            return True
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class _WatchdogBridge(FileSystemEventHandler):
                def __init__(self, handler: _VaultEventHandler) -> None:
                    super().__init__()
                    self._h = handler

                def on_created(self, event: Any) -> None:
                    self._h.on_created(event)

                def on_modified(self, event: Any) -> None:
                    self._h.on_modified(event)

                def on_deleted(self, event: Any) -> None:
                    self._h.on_deleted(event)

                def on_moved(self, event: Any) -> None:
                    self._h.on_moved(event)

            self._handler = _VaultEventHandler(self)
            bridge = _WatchdogBridge(self._handler)

            observer = Observer()
            observer.schedule(bridge, str(self._vault_root), recursive=True)
            observer.start()
            self._observer = observer
            self._running = True
            return True
        except Exception as exc:
            self._unavailable_reason = str(exc)
            return False

    def stop(self) -> None:
        if self._handler:
            self._handler.stop_flush()
        if self._observer is not None:
            try:
                self._observer.stop()
                self._observer.join(timeout=2.0)
            except Exception:
                pass
            self._observer = None
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def get_status(self) -> dict:
        return {
            "available": self._available,
            "running": self._running,
            "vault_root": str(self._vault_root),
            "event_count": self._event_count,
            "last_event_path": self._last_event_path,
            "unavailable_reason": self._unavailable_reason or None,
        }

    def _notify(self, path: str) -> None:
        with self._lock:
            self._event_count += 1
            self._last_event_path = path
            window = self._window

        if window is None:
            return

        rel = None
        try:
            rel = str(Path(path).relative_to(self._vault_root))
        except ValueError:
            rel = path

        payload = json.dumps({"path": rel, "abs": path})
        js = (
            f"(function(){{var e={payload};"
            f"if(typeof window.onVaultChange==='function'){{window.onVaultChange(e);}}"
            f"}})();"
        )
        try:
            window.evaluate_js(js)
        except Exception:
            pass
