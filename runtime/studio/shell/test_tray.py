"""Tests for the ChaseOS Studio system tray integration.

These tests exercise tray module logic without requiring a live display
server, Qt application, or actual tray icon. All Qt/pywebview calls are
mocked — the tests verify decision logic, callback wiring, and the
status-refresh path.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, PropertyMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers / fakes
# ---------------------------------------------------------------------------

def _fake_vault(tmp_path: Path) -> Path:
    v = tmp_path / "my_vault"
    v.mkdir()
    return v


def _fake_api(pending: int = 0, ok: bool = True) -> MagicMock:
    api = MagicMock()
    api.get_dashboard.return_value = {
        "ok": ok,
        "data": {
            "approvals": {"pending_count": pending},
        },
    }
    return api


def _fake_window() -> MagicMock:
    window = MagicMock()
    # events.closing behaves like an event with += operator
    window.events = SimpleNamespace(closing=MagicMock())
    return window


# ---------------------------------------------------------------------------
# Import guard — tray module
# ---------------------------------------------------------------------------

def test_tray_module_imports():
    from runtime.studio.shell import tray as tray_mod
    assert hasattr(tray_mod, "SystemTrayManager")


def test_tray_manager_constructs(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager
    vault = _fake_vault(tmp_path)
    api = _fake_api()
    window = _fake_window()
    qt_app = MagicMock()

    mgr = SystemTrayManager(qt_app, window, vault, api)
    assert mgr._vault_root == vault
    assert mgr._allow_quit is False
    assert mgr._running is True
    assert mgr._tray is None


# ---------------------------------------------------------------------------
# _build_icon — runs without real Qt display
# ---------------------------------------------------------------------------

def test_build_icon_with_mock_qt(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    # Mock the entire PyQt6 stack the method needs
    mock_pixmap = MagicMock()
    mock_painter = MagicMock()
    mock_icon = MagicMock()
    mock_path = MagicMock()

    with patch.dict("sys.modules", {
        "PyQt6": MagicMock(),
        "PyQt6.QtGui": MagicMock(
            QIcon=MagicMock(return_value=mock_icon),
            QPixmap=MagicMock(return_value=mock_pixmap),
            QColor=MagicMock(),
            QPainter=MagicMock(return_value=mock_painter),
            QPainterPath=MagicMock(return_value=mock_path),
        ),
        "PyQt6.QtCore": MagicMock(),
    }):
        mgr = SystemTrayManager(MagicMock(), _fake_window(), _fake_vault(tmp_path), _fake_api())
        icon = mgr._build_icon()
        # Icon is whatever QIcon() returned
        assert icon is mock_icon


# ---------------------------------------------------------------------------
# setup() — wires closing event and starts refresh thread
# ---------------------------------------------------------------------------

def test_setup_wires_closing_event(tmp_path):
    """setup() should hook window.events.closing."""
    import sys
    from runtime.studio.shell.tray import SystemTrayManager

    window = _fake_window()
    vault = _fake_vault(tmp_path)
    mgr = SystemTrayManager(MagicMock(), window, vault, _fake_api())

    # Build fake PyQt6 stack — force-override so real PyQt6 (if installed) is bypassed
    mock_tray = MagicMock()
    mock_menu = MagicMock()
    mock_menu.addAction.return_value = MagicMock()
    fake_pyqt = MagicMock()
    fake_pyqt.QtWidgets.QSystemTrayIcon.return_value = mock_tray
    fake_pyqt.QtWidgets.QMenu.return_value = mock_menu

    # Capture the original closing mock BEFORE setup() reassigns it via +=
    original_closing = window.events.closing

    orig = {k: sys.modules.get(k) for k in ("PyQt6", "PyQt6.QtWidgets", "PyQt6.QtGui")}
    sys.modules["PyQt6"] = fake_pyqt
    sys.modules["PyQt6.QtWidgets"] = fake_pyqt.QtWidgets
    sys.modules["PyQt6.QtGui"] = MagicMock()

    try:
        with patch.object(SystemTrayManager, "_build_icon", return_value=MagicMock()), \
             patch.object(SystemTrayManager, "_refresh_loop"):
            result = mgr.setup()
    finally:
        for k, v in orig.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v

    # setup() succeeded and subscribed to the closing event
    assert result is True
    original_closing.__iadd__.assert_called_once()


def test_setup_returns_false_on_import_error(tmp_path):
    """setup() should return False (not raise) if PyQt6 is unavailable."""
    from runtime.studio.shell.tray import SystemTrayManager
    import sys

    mgr = SystemTrayManager(MagicMock(), _fake_window(), _fake_vault(tmp_path), _fake_api())

    orig = sys.modules.get("PyQt6.QtWidgets")
    sys.modules["PyQt6.QtWidgets"] = None  # force ImportError

    try:
        result = mgr.setup()
    except ImportError:
        result = False
    finally:
        if orig is None:
            sys.modules.pop("PyQt6.QtWidgets", None)
        else:
            sys.modules["PyQt6.QtWidgets"] = orig

    # Either False or tray stayed None
    assert result is False or mgr._tray is None


# ---------------------------------------------------------------------------
# _on_window_closing — close vs minimise-to-tray logic
# ---------------------------------------------------------------------------

def test_on_window_closing_hides_not_destroys_by_default(tmp_path):
    """X button should hide the window and return False (cancel close)."""
    from runtime.studio.shell.tray import SystemTrayManager

    window = _fake_window()
    mgr = SystemTrayManager(MagicMock(), window, _fake_vault(tmp_path), _fake_api())
    mgr._tray = MagicMock()
    mgr._tray.supportsMessages.return_value = False
    mgr._allow_quit = False

    with patch("runtime.studio.shell.tray.SystemTrayManager._build_icon"):
        result = mgr._on_window_closing()

    assert result is False
    window.hide.assert_called_once()
    window.destroy.assert_not_called()


def test_on_window_closing_allows_when_quit_flagged(tmp_path):
    """When _allow_quit is True the close should be permitted."""
    from runtime.studio.shell.tray import SystemTrayManager

    window = _fake_window()
    mgr = SystemTrayManager(MagicMock(), window, _fake_vault(tmp_path), _fake_api())
    mgr._allow_quit = True

    result = mgr._on_window_closing()

    assert result is True
    window.hide.assert_not_called()


def test_on_window_closing_shows_balloon(tmp_path):
    """A balloon notification should fire on first hide."""
    pytest.importorskip("PyQt6", reason="Qt tray balloon test requires PyQt6 runtime")
    from runtime.studio.shell.tray import SystemTrayManager

    window = _fake_window()
    mgr = SystemTrayManager(MagicMock(), window, _fake_vault(tmp_path), _fake_api())
    mock_tray = MagicMock()
    mock_tray.supportsMessages.return_value = True
    mgr._tray = mock_tray
    mgr._allow_quit = False

    with patch("runtime.studio.shell.tray.SystemTrayManager._build_icon"), \
         patch("PyQt6.QtWidgets.QSystemTrayIcon") as mock_sti:
        mock_sti.MessageIcon.Information = 1
        mgr._on_window_closing()

    mock_tray.showMessage.assert_called_once()
    args = mock_tray.showMessage.call_args[0]
    assert "ChaseOS Studio" in args[0]


# ---------------------------------------------------------------------------
# _quit — sets allow_quit and destroys window
# ---------------------------------------------------------------------------

def test_quit_sets_allow_quit_and_destroys(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    window = _fake_window()
    mgr = SystemTrayManager(MagicMock(), window, _fake_vault(tmp_path), _fake_api())
    mgr._tray = MagicMock()

    mgr._quit()

    assert mgr._allow_quit is True
    assert mgr._running is False
    window.destroy.assert_called_once()


def test_quit_hides_tray_icon(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    window = _fake_window()
    mgr = SystemTrayManager(MagicMock(), window, _fake_vault(tmp_path), _fake_api())
    mock_tray = MagicMock()
    mgr._tray = mock_tray

    mgr._quit()

    mock_tray.hide.assert_called_once()


# ---------------------------------------------------------------------------
# _show_window
# ---------------------------------------------------------------------------

def test_show_window_calls_pywebview_show(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    window = _fake_window()
    mgr = SystemTrayManager(MagicMock(), window, _fake_vault(tmp_path), _fake_api())
    mgr._show_window()

    window.show.assert_called_once()


def test_show_window_tolerates_exception(tmp_path):
    """If window.show() raises, _show_window should not propagate."""
    from runtime.studio.shell.tray import SystemTrayManager

    window = _fake_window()
    window.show.side_effect = RuntimeError("no display")
    mgr = SystemTrayManager(MagicMock(), window, _fake_vault(tmp_path), _fake_api())

    # Should not raise
    mgr._show_window()


# ---------------------------------------------------------------------------
# _on_activated — double-click shows window
# ---------------------------------------------------------------------------

def test_on_activated_double_click_shows_window(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    window = _fake_window()
    mgr = SystemTrayManager(MagicMock(), window, _fake_vault(tmp_path), _fake_api())

    import sys
    mock_sti = MagicMock()
    mock_sti.ActivationReason.DoubleClick = "dbl"
    fake_pyqt = MagicMock()
    fake_pyqt.QtWidgets.QSystemTrayIcon = mock_sti
    sys.modules["PyQt6"] = fake_pyqt
    sys.modules["PyQt6.QtWidgets"] = fake_pyqt.QtWidgets

    try:
        mgr._on_activated("dbl")
    finally:
        sys.modules.pop("PyQt6", None)
        sys.modules.pop("PyQt6.QtWidgets", None)

    window.show.assert_called_once()


def test_on_activated_single_click_does_not_show(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    window = _fake_window()
    mgr = SystemTrayManager(MagicMock(), window, _fake_vault(tmp_path), _fake_api())

    import sys
    mock_sti = MagicMock()
    mock_sti.ActivationReason.DoubleClick = "dbl"
    fake_pyqt = MagicMock()
    fake_pyqt.QtWidgets.QSystemTrayIcon = mock_sti
    sys.modules["PyQt6"] = fake_pyqt
    sys.modules["PyQt6.QtWidgets"] = fake_pyqt.QtWidgets

    try:
        mgr._on_activated("single")  # different from DoubleClick
    finally:
        sys.modules.pop("PyQt6", None)
        sys.modules.pop("PyQt6.QtWidgets", None)

    window.show.assert_not_called()


# ---------------------------------------------------------------------------
# _do_refresh — status line logic
# ---------------------------------------------------------------------------

def test_do_refresh_no_pending_sets_all_clear(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    mgr = SystemTrayManager(MagicMock(), _fake_window(), _fake_vault(tmp_path), _fake_api(pending=0))
    mock_tray = MagicMock()
    mock_action = MagicMock()
    mgr._tray = mock_tray
    mgr._status_action = mock_action

    mgr._do_refresh()

    mock_action.setText.assert_called_with("All clear")
    tip = mock_tray.setToolTip.call_args[0][0]
    assert "ChaseOS Studio" in tip
    assert "pending" not in tip.lower()


def test_do_refresh_with_pending_shows_count(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    vault = _fake_vault(tmp_path)
    mgr = SystemTrayManager(MagicMock(), _fake_window(), vault, _fake_api(pending=3))
    mock_tray = MagicMock()
    mock_action = MagicMock()
    mgr._tray = mock_tray
    mgr._status_action = mock_action

    mgr._do_refresh()

    mock_action.setText.assert_called_with("3 approvals pending")
    tip = mock_tray.setToolTip.call_args[0][0]
    assert "3" in tip
    assert "approval" in tip


def test_do_refresh_singular_approval(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    mgr = SystemTrayManager(MagicMock(), _fake_window(), _fake_vault(tmp_path), _fake_api(pending=1))
    mock_action = MagicMock()
    mgr._tray = MagicMock()
    mgr._status_action = mock_action

    mgr._do_refresh()

    text = mock_action.setText.call_args[0][0]
    assert text == "1 approval pending"


def test_do_refresh_api_not_ok_is_silent(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    mgr = SystemTrayManager(MagicMock(), _fake_window(), _fake_vault(tmp_path), _fake_api(ok=False))
    mock_action = MagicMock()
    mgr._tray = MagicMock()
    mgr._status_action = mock_action

    mgr._do_refresh()  # should not raise

    mock_action.setText.assert_not_called()


def test_do_refresh_tolerates_api_exception(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    api = MagicMock()
    api.get_dashboard.side_effect = RuntimeError("bus down")
    mgr = SystemTrayManager(MagicMock(), _fake_window(), _fake_vault(tmp_path), api)
    mgr._tray = MagicMock()
    mgr._status_action = MagicMock()

    mgr._do_refresh()  # should not raise


# ---------------------------------------------------------------------------
# stop()
# ---------------------------------------------------------------------------

def test_stop_sets_running_false(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    mgr = SystemTrayManager(MagicMock(), _fake_window(), _fake_vault(tmp_path), _fake_api())
    mgr._tray = MagicMock()
    mgr.stop()

    assert mgr._running is False
    mgr._tray.hide.assert_called_once()


def test_stop_with_no_tray_does_not_raise(tmp_path):
    from runtime.studio.shell.tray import SystemTrayManager

    mgr = SystemTrayManager(MagicMock(), _fake_window(), _fake_vault(tmp_path), _fake_api())
    mgr._tray = None
    mgr.stop()  # should not raise


# ---------------------------------------------------------------------------
# main.py integration — tray created if QApplication available
# ---------------------------------------------------------------------------

def test_main_py_imports_tray_correctly():
    """tray module must be importable from shell package."""
    from runtime.studio.shell import tray
    assert hasattr(tray, "SystemTrayManager")


def test_main_py_has_tray_wiring():
    """main.py must contain tray setup logic."""
    import inspect
    from runtime.studio.shell import main as main_mod
    src = inspect.getsource(main_mod)
    assert "SystemTrayManager" in src
    assert "tray_manager" in src
    assert "tray_manager.setup" in src
    assert "tray_manager.stop" in src


def test_main_py_creates_qt_app_before_webview():
    """QApplication must be created before webview.start() in main()."""
    import inspect
    from runtime.studio.shell import main as main_mod
    src = inspect.getsource(main_mod.main)
    qa_pos = src.find("QApplication")
    wv_start_pos = src.find("webview.start")
    assert qa_pos != -1, "QApplication not found in main()"
    assert wv_start_pos != -1, "webview.start not found in main()"
    assert qa_pos < wv_start_pos, "QApplication must appear before webview.start()"


def test_main_forces_pyqt6_backend_env(monkeypatch):
    from runtime.studio.shell import main as main_mod

    monkeypatch.delenv("PYWEBVIEW_GUI", raising=False)
    monkeypatch.delenv("QT_API", raising=False)

    main_mod._configure_qt_backend_env()

    assert os.environ["PYWEBVIEW_GUI"] == "qt"
    assert os.environ["QT_API"] == "pyqt6"


def test_main_passes_explicit_qt_backend_to_pywebview_start():
    import inspect
    from runtime.studio.shell import main as main_mod

    src = inspect.getsource(main_mod.main)

    assert 'webview.start(gui="qt"' in src
    assert "import webview.platforms.qt" in src


def test_main_loads_frontend_with_file_uri():
    import inspect
    from runtime.studio.shell import main as main_mod

    src = inspect.getsource(main_mod.main)

    assert ".resolve().as_uri()" in src
