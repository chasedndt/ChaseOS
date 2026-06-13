"""ChaseOS Studio — system tray integration.

Uses QSystemTrayIcon from the existing PyQt6 QApplication that pywebview
runs on. Must be set up BEFORE webview.start() is called so the tray icon
is registered in the Qt event loop from the start.

Behaviour:
- Tray icon appears immediately when the shell launches.
- Clicking the X button on the main window hides it (minimise to tray)
  instead of quitting — the QApplication (and tray) stay alive.
- Double-clicking the tray icon or clicking "Show" restores the window.
- "Quit" in the tray menu destroys the window and exits cleanly.
- Tray tooltip and status line refresh every 30 s with pending-approval
  count from the dashboard API.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

_log = logging.getLogger("chaseos.studio.tray")

if TYPE_CHECKING:
    from runtime.studio.shell.api import StudioAPI


class SystemTrayManager:
    """Manages the system tray icon for ChaseOS Studio."""

    _REFRESH_INTERVAL = 30  # seconds between dashboard polls

    def __init__(self, qt_app, webview_window, vault_root: Path, api: "StudioAPI") -> None:
        self._app = qt_app
        self._window = webview_window       # pywebview window object
        self._vault_root = vault_root
        self._api = api
        self._tray = None
        self._status_action = None
        self._allow_quit = False            # set True when Quit is chosen from menu
        self._running = True
        self._refresh_in_flight = False     # guard: skip cycle if previous still running

    # ── Public ────────────────────────────────────────────────────────────────

    def setup(self) -> bool:
        """Create and show the tray icon. Returns True on success."""
        try:
            from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
            from PyQt6.QtGui import QIcon
        except ImportError:
            return False

        icon = self._build_icon()

        # Set app-wide window icon (Windows taskbar + Alt-Tab switcher)
        try:
            self._app.setWindowIcon(icon)
        except Exception:
            pass

        tray = QSystemTrayIcon(icon, self._app)
        tray.setToolTip(f"ChaseOS Studio — {self._vault_root.name}")

        # ── Context menu ──────────────────────────────────────────────────
        menu = QMenu()
        show_action = menu.addAction("Show ChaseOS Studio")
        menu.addSeparator()
        self._status_action = menu.addAction("…")
        self._status_action.setEnabled(False)
        menu.addSeparator()
        quit_action = menu.addAction("Quit ChaseOS Studio")

        show_action.triggered.connect(self._show_window)
        quit_action.triggered.connect(self._quit)

        tray.activated.connect(self._on_activated)
        tray.setContextMenu(menu)
        tray.show()
        self._tray = tray

        # ── Intercept window close (X button → hide to tray) ──────────────
        self._window.events.closing += self._on_window_closing

        # ── Background status refresh ─────────────────────────────────────
        t = threading.Thread(target=self._refresh_loop, daemon=True, name="tray-status")
        t.start()

        return True

    def stop(self) -> None:
        """Stop the refresh loop and hide the tray icon."""
        self._running = False
        if self._tray:
            try:
                self._tray.hide()
            except Exception:
                pass

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_icon(self):
        """Build the C-kernel programmatic icon (tray + taskbar).

        Design: Sovereign Obsidian palette.
          • Deep background circle  — #0a0d14
          • C-arc (Runtime Teal)    — #39e6d2, ~270° arc opening right
          • Agent nodes (Violet)    — #7c5cff at arc endpoints
          • Connector lines         — violet, low opacity
          • Central dot (Teal)      — #39e6d2
        """
        from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QPen
        from PyQt6.QtCore import Qt, QPointF, QRectF

        size = 64
        cx, cy = size / 2, size / 2

        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ── Background circle ─────────────────────────────────────────────
        p.setBrush(QColor("#0a0d14"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(1, 1, size - 2, size - 2))

        # ── C-arc (Runtime Teal) ─────────────────────────────────────────
        # Qt drawArc: startAngle CCW from 3-o'clock, in 1/16° units.
        # Start at 45° (northeast), sweep 270° CCW → arc covers left/top/bottom,
        # leaving a gap on the right — creating a "C" opening to the right.
        arc_r = size * 0.36
        arc_rect = QRectF(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)
        arc_pen = QPen(QColor("#39e6d2"))
        arc_pen.setWidth(max(4, int(size * 0.10)))
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(arc_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(arc_rect, int(45 * 16), int(270 * 16))

        # ── Arc endpoints (for agent node placement) ─────────────────────
        # Qt 45° = northeast: x+, y-  |  Qt 315° (-45°) = southeast: x+, y+
        top_x = cx + arc_r * math.cos(math.radians(45))
        top_y = cy - arc_r * math.sin(math.radians(45))
        bot_x = cx + arc_r * math.cos(math.radians(-45))
        bot_y = cy - arc_r * math.sin(math.radians(-45))

        # ── Connector lines (violet, low opacity) ────────────────────────
        conn_pen = QPen(QColor(124, 92, 255, 55))
        conn_pen.setWidth(1)
        p.setPen(conn_pen)
        p.drawLine(QPointF(cx, cy), QPointF(top_x, top_y))
        p.drawLine(QPointF(cx, cy), QPointF(bot_x, bot_y))

        # ── Agent nodes (Knowledge Violet) ───────────────────────────────
        agent_r = size * 0.09
        p.setBrush(QColor("#7c5cff"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(top_x - agent_r, top_y - agent_r, agent_r * 2, agent_r * 2))
        p.drawEllipse(QRectF(bot_x - agent_r, bot_y - agent_r, agent_r * 2, agent_r * 2))

        # ── Central dot (Runtime Teal) ────────────────────────────────────
        dot_r = size * 0.11
        p.setBrush(QColor("#39e6d2"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx - dot_r, cy - dot_r, dot_r * 2, dot_r * 2))

        p.end()
        return QIcon(pixmap)

    # ── Slot / event handlers ─────────────────────────────────────────────────

    def _show_window(self) -> None:
        try:
            self._window.show()
        except Exception:
            pass

    def _quit(self) -> None:
        self._allow_quit = True
        self._running = False
        if self._tray:
            try:
                self._tray.hide()
            except Exception:
                pass
        try:
            self._window.destroy()
        except Exception:
            pass

    def _on_activated(self, reason) -> None:
        try:
            from PyQt6.QtWidgets import QSystemTrayIcon
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                self._show_window()
        except Exception:
            pass

    def _on_window_closing(self) -> bool:
        """Return False to cancel close (hide to tray instead)."""
        if self._allow_quit:
            return True                     # real quit — allow it

        # Hide window; keep tray + event loop alive
        try:
            self._window.hide()
        except Exception:
            pass

        # Show balloon notification (only once per hide)
        try:
            from PyQt6.QtWidgets import QSystemTrayIcon
            if self._tray and self._tray.supportsMessages():
                self._tray.showMessage(
                    "ChaseOS Studio",
                    "Still running in the background. Double-click to restore.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2500,
                )
        except Exception:
            pass

        return False                        # cancel the close event

    # ── Status refresh ────────────────────────────────────────────────────────

    def _refresh_loop(self) -> None:
        # First refresh shortly after startup so the status isn't stale
        time.sleep(3)
        while self._running:
            self._do_refresh()
            for _ in range(self._REFRESH_INTERVAL * 10):
                if not self._running:
                    return
                time.sleep(0.1)

    def _do_refresh(self) -> None:
        # Rate-limit guard: skip if a dashboard call from a previous cycle is
        # still in progress (can happen on slow vaults or large graphs).
        if self._refresh_in_flight:
            _log.debug("tray refresh SKIPPED — previous cycle still in flight")
            return
        self._refresh_in_flight = True
        t0 = time.monotonic()
        _log.debug("tray refresh START")
        try:
            result = self._api.get_dashboard()
            elapsed = time.monotonic() - t0
            if not result or not result.get("ok"):
                _log.debug("tray refresh DONE (no data) elapsed=%.3fs", elapsed)
                return

            d = result.get("data", {}) or {}
            approvals = d.get("approvals", {}) or {}
            pending = int(approvals.get("pending_count", 0) or 0)

            vault_name = self._vault_root.name
            if pending:
                tip = f"ChaseOS Studio — {vault_name}\n{pending} approval{'s' if pending != 1 else ''} waiting"
                status_text = f"{pending} approval{'s' if pending != 1 else ''} pending"
            else:
                tip = f"ChaseOS Studio — {vault_name}"
                status_text = "All clear"

            if self._tray:
                self._tray.setToolTip(tip)
            if self._status_action:
                self._status_action.setText(status_text)

            _log.debug("tray refresh OK pending=%d elapsed=%.3fs", pending, elapsed)

        except Exception as exc:
            _log.warning("tray refresh ERROR: %s (elapsed=%.3fs)", exc, time.monotonic() - t0)
        finally:
            self._refresh_in_flight = False
