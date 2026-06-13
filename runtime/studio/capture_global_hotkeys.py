"""Operating-system-wide Capture to Markdown hotkey registration."""

from __future__ import annotations

import ctypes
import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from runtime.studio.capture_hotkey_settings import load_capture_hotkey_settings


WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

GLOBAL_CAPTURE_ACTIONS = {
    "run_screen_capture_collector": "captureCurrentScreenForMarkdown",
    "run_display_region_collector": "captureDisplayRegionForMarkdown",
    "run_active_window_collector": "captureActiveWindowForMarkdown",
    "run_clipboard_text_collector": "captureClipboardTextForMarkdown",
    "run_selected_text_collector": "captureSelectedTextForMarkdown",
    "run_accessibility_tree_collector": "captureAccessibilityTreeForMarkdown",
}

_MODIFIER_BITS = {
    "Ctrl": MOD_CONTROL,
    "Alt": MOD_ALT,
    "Shift": MOD_SHIFT,
    "Win": MOD_WIN,
}

_NAMED_KEYS = {
    "Space": 0x20,
    "Enter": 0x0D,
    "Escape": 0x1B,
    "Tab": 0x09,
    "Backspace": 0x08,
    "Delete": 0x2E,
    "Insert": 0x2D,
    "Home": 0x24,
    "End": 0x23,
    "PageUp": 0x21,
    "PageDown": 0x22,
    "ArrowUp": 0x26,
    "ArrowDown": 0x28,
    "ArrowLeft": 0x25,
    "ArrowRight": 0x27,
}


class CaptureGlobalHotkeyError(RuntimeError):
    """Raised when global hotkey registration cannot be started."""


@dataclass(frozen=True)
class CaptureGlobalHotkeyRegistration:
    action_id: str
    chord: str
    modifiers: int
    virtual_key: int
    handler_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "chord": self.chord,
            "modifiers": self.modifiers,
            "virtual_key": self.virtual_key,
            "handler_name": self.handler_name,
        }


def build_capture_global_hotkey_registration_plan(vault_root: str | Path) -> dict[str, Any]:
    settings = load_capture_hotkey_settings(vault_root)
    enabled = bool(settings.get("global_hotkeys_enabled"))
    bindings = settings.get("bindings") if isinstance(settings.get("bindings"), dict) else {}
    registrations: list[CaptureGlobalHotkeyRegistration] = []
    unsupported: list[dict[str, str]] = []
    for action_id, handler_name in GLOBAL_CAPTURE_ACTIONS.items():
        chord = str(bindings.get(action_id) or "").strip()
        if not chord:
            continue
        try:
            modifiers, virtual_key = parse_windows_hotkey_chord(chord)
        except CaptureGlobalHotkeyError as exc:
            unsupported.append({"action_id": action_id, "chord": chord, "reason": str(exc)})
            continue
        registrations.append(
            CaptureGlobalHotkeyRegistration(
                action_id=action_id,
                chord=chord,
                modifiers=modifiers,
                virtual_key=virtual_key,
                handler_name=handler_name,
            )
        )
    return {
        "surface": "studio_capture_global_hotkeys",
        "enabled": enabled,
        "available": os.name == "nt",
        "registrations": [item.to_dict() for item in registrations],
        "unsupported_bindings": unsupported,
        "registers_global_hotkeys": bool(enabled and os.name == "nt" and registrations),
        "message": (
            "Global Capture hotkeys are ready to register."
            if enabled and os.name == "nt" and registrations
            else "Global Capture hotkeys are off or have no supported bindings."
        ),
    }


def parse_windows_hotkey_chord(chord: str) -> tuple[int, int]:
    parts = [part.strip() for part in str(chord or "").split("+") if part.strip()]
    if len(parts) < 2:
        raise CaptureGlobalHotkeyError("global hotkey requires at least one modifier and one key")
    modifiers = MOD_NOREPEAT
    key_parts: list[str] = []
    for part in parts:
        if part in _MODIFIER_BITS:
            modifiers |= _MODIFIER_BITS[part]
        else:
            key_parts.append(part)
    if len(key_parts) != 1:
        raise CaptureGlobalHotkeyError("global hotkey requires exactly one non-modifier key")
    virtual_key = _virtual_key_for(key_parts[0])
    if not modifiers & (MOD_CONTROL | MOD_ALT | MOD_SHIFT | MOD_WIN):
        raise CaptureGlobalHotkeyError("global hotkey requires at least one modifier")
    return modifiers, virtual_key


def _virtual_key_for(key: str) -> int:
    normalized = key.strip()
    if len(normalized) == 1 and normalized.isalpha():
        return ord(normalized.upper())
    if len(normalized) == 1 and normalized.isdigit():
        return ord(normalized)
    if normalized.startswith("F") and normalized[1:].isdigit():
        number = int(normalized[1:])
        if 1 <= number <= 24:
            return 0x70 + number - 1
    if normalized in _NAMED_KEYS:
        return _NAMED_KEYS[normalized]
    raise CaptureGlobalHotkeyError(f"unsupported global hotkey key: {key}")


class WindowsGlobalHotkeyBackend:
    """Thin wrapper around user32 RegisterHotKey for the Studio process."""

    def __init__(self) -> None:
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._thread_id = 0
        self._registered_ids: list[int] = []
        self._action_by_id: dict[int, str] = {}

    def run(
        self,
        registrations: list[CaptureGlobalHotkeyRegistration],
        callback: Callable[[str], None],
        stop_event: threading.Event,
        ready_event: threading.Event,
    ) -> None:
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        self._registered_ids = []
        self._action_by_id = {}
        for index, registration in enumerate(registrations, start=1):
            hotkey_id = 9200 + index
            ok = self._user32.RegisterHotKey(
                None,
                hotkey_id,
                int(registration.modifiers),
                int(registration.virtual_key),
            )
            if not ok:
                self.unregister_all()
                raise CaptureGlobalHotkeyError(
                    f"could not register global hotkey {registration.chord}"
                )
            self._registered_ids.append(hotkey_id)
            self._action_by_id[hotkey_id] = registration.action_id
        ready_event.set()

        class Msg(ctypes.Structure):
            _fields_ = [
                ("hwnd", ctypes.c_void_p),
                ("message", ctypes.c_uint),
                ("wParam", ctypes.c_void_p),
                ("lParam", ctypes.c_void_p),
                ("time", ctypes.c_uint),
                ("pt_x", ctypes.c_long),
                ("pt_y", ctypes.c_long),
            ]

        msg = Msg()
        while not stop_event.is_set():
            result = self._user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if result in (0, -1):
                break
            if int(msg.message) == WM_HOTKEY:
                action_id = self._action_by_id.get(int(msg.wParam or 0))
                if action_id:
                    callback(action_id)
        self.unregister_all()

    def stop(self) -> None:
        if self._thread_id:
            self._user32.PostThreadMessageW(int(self._thread_id), 0x0012, 0, 0)

    def unregister_all(self) -> None:
        for hotkey_id in list(self._registered_ids):
            self._user32.UnregisterHotKey(None, hotkey_id)
        self._registered_ids = []
        self._action_by_id = {}


class CaptureGlobalHotkeyRuntime:
    def __init__(
        self,
        vault_root: str | Path,
        *,
        backend: WindowsGlobalHotkeyBackend | None = None,
    ) -> None:
        self.vault_root = Path(vault_root)
        self.backend = backend
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._window: Any = None
        self._active = False
        self._last_error = ""
        self._registrations: list[CaptureGlobalHotkeyRegistration] = []

    def start(self, window: Any) -> dict[str, Any]:
        self.stop()
        self._window = window
        plan = build_capture_global_hotkey_registration_plan(self.vault_root)
        self._registrations = [
            CaptureGlobalHotkeyRegistration(**item) for item in plan.get("registrations") or []
        ]
        if not plan.get("enabled") or not self._registrations:
            self._active = False
            self._last_error = ""
            return self.status() | {"plan": plan}
        if os.name != "nt":
            self._active = False
            self._last_error = "Global Capture hotkeys require Windows."
            return self.status() | {"plan": plan}

        self._stop_event.clear()
        ready_event = threading.Event()
        backend = self.backend or WindowsGlobalHotkeyBackend()
        self.backend = backend

        def _run() -> None:
            try:
                backend.run(self._registrations, self._on_hotkey, self._stop_event, ready_event)
            except Exception as exc:
                self._last_error = str(exc)
                ready_event.set()
            finally:
                self._active = False

        self._thread = threading.Thread(target=_run, name="capture-global-hotkeys", daemon=True)
        self._thread.start()
        ready_event.wait(timeout=2)
        self._active = bool(self._thread.is_alive() and not self._last_error)
        return self.status() | {"plan": plan}

    def stop(self) -> dict[str, Any]:
        self._stop_event.set()
        if self.backend is not None:
            try:
                self.backend.stop()
            except Exception:
                pass
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None
        self._active = False
        return self.status()

    def status(self) -> dict[str, Any]:
        return {
            "surface": "studio_capture_global_hotkeys",
            "active": bool(self._active),
            "registered_count": len(self._registrations) if self._active else 0,
            "last_error": self._last_error,
            "registrations": [item.to_dict() for item in self._registrations],
        }

    def _on_hotkey(self, action_id: str) -> None:
        handler_name = GLOBAL_CAPTURE_ACTIONS.get(action_id)
        window = self._window
        if not handler_name or window is None:
            return
        payload = json.dumps({"action_id": action_id, "handler": handler_name})
        js = (
            "(function(payload){"
            "try{"
            "window.location.hash='#/capture-markdown';"
            "setTimeout(function(){"
            "var fn=window[payload.handler];"
            "if(typeof fn==='function'){fn();}"
            "},80);"
            "}catch(err){console.warn('Capture global hotkey failed',err);}"
            f"}})({payload});"
        )
        try:
            window.evaluate_js(js)
        except Exception as exc:
            self._last_error = str(exc)
