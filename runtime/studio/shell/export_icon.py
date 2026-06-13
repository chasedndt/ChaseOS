"""Export the ChaseOS Studio tray icon design to a .ico file.

Renders the same C-kernel programmatic icon used by tray.py and saves it as
a proper multi-size .ico file at runtime/studio/shell/chaseos_studio.ico.

Usage:
    .venv\Scripts\python.exe runtime\studio\shell\export_icon.py
"""
from __future__ import annotations

import math
import os
import struct
import sys
import io


def _render_at_size(size: int) -> bytes:
    """Render the icon at `size` x `size` and return raw RGBA bytes."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QPixmap, QColor, QPainter, QPen
    from PyQt6.QtCore import Qt, QPointF, QRectF, QBuffer, QIODevice

    cx, cy = size / 2.0, size / 2.0

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # ── Background circle ────────────────────────────────────────────────
    p.setBrush(QColor("#0a0d14"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(1, 1, size - 2, size - 2))

    # ── C-arc (Runtime Teal) ─────────────────────────────────────────────
    arc_r = size * 0.36
    arc_rect = QRectF(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)
    arc_pen = QPen(QColor("#39e6d2"))
    arc_pen.setWidth(max(3, int(size * 0.10)))
    arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(arc_pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(arc_rect, int(45 * 16), int(270 * 16))

    # ── Arc endpoints ────────────────────────────────────────────────────
    top_x = cx + arc_r * math.cos(math.radians(45))
    top_y = cy - arc_r * math.sin(math.radians(45))
    bot_x = cx + arc_r * math.cos(math.radians(-45))
    bot_y = cy - arc_r * math.sin(math.radians(-45))

    # ── Connector lines (violet, low opacity) ────────────────────────────
    conn_pen = QPen(QColor(124, 92, 255, 55))
    conn_pen.setWidth(max(1, int(size * 0.016)))
    p.setPen(conn_pen)
    p.drawLine(QPointF(cx, cy), QPointF(top_x, top_y))
    p.drawLine(QPointF(cx, cy), QPointF(bot_x, bot_y))

    # ── Agent nodes (Knowledge Violet) ───────────────────────────────────
    agent_r = size * 0.09
    p.setBrush(QColor("#7c5cff"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(top_x - agent_r, top_y - agent_r, agent_r * 2, agent_r * 2))
    p.drawEllipse(QRectF(bot_x - agent_r, bot_y - agent_r, agent_r * 2, agent_r * 2))

    # ── Central dot (Runtime Teal) ────────────────────────────────────────
    dot_r = size * 0.11
    p.setBrush(QColor("#39e6d2"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(cx - dot_r, cy - dot_r, dot_r * 2, dot_r * 2))

    p.end()

    # Export as PNG bytes via Qt buffer
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buf, "PNG")
    buf.close()
    return bytes(buf.data())


def _build_ico(png_blobs: list[tuple[int, bytes]]) -> bytes:
    """Assemble a .ico file from a list of (size, png_bytes) tuples.

    Uses PNG encoding inside ICO for Vista+ compatibility (supports alpha).
    """
    n = len(png_blobs)
    # Header: ICONDIR
    # Reserved(2) + Type(2) + Count(2)
    header = struct.pack("<HHH", 0, 1, n)

    # Each entry is 16 bytes in the directory
    entry_size = 16
    image_data_offset = 6 + n * entry_size

    entries = b""
    image_data = b""
    for size, png_bytes in png_blobs:
        entry_width  = size if size < 256 else 0   # 0 = 256 in ICO spec
        entry_height = size if size < 256 else 0
        entries += struct.pack(
            "<BBBBHHII",
            entry_width,          # width  (0 = 256)
            entry_height,         # height (0 = 256)
            0,                    # color count (0 = no palette)
            0,                    # reserved
            1,                    # planes
            32,                   # bit count
            len(png_bytes),       # size of image data
            image_data_offset,    # offset from start of file
        )
        image_data_offset += len(png_bytes)
        image_data += png_bytes

    return header + entries + image_data


def main() -> None:
    # QApplication must exist before any QPixmap operations
    app_instance = None
    try:
        from PyQt6.QtWidgets import QApplication
        app_instance = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        print("ERROR: PyQt6 is not installed. Run: pip install PyQt6", file=sys.stderr)
        sys.exit(1)

    sizes = [16, 32, 48, 64, 128, 256]
    blobs: list[tuple[int, bytes]] = []
    for s in sizes:
        png_data = _render_at_size(s)
        blobs.append((s, png_data))
        print(f"  rendered {s}x{s}  ({len(png_data)} bytes)")

    ico_bytes = _build_ico(blobs)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "chaseos_studio.ico")
    with open(out_path, "wb") as f:
        f.write(ico_bytes)

    print(f"\nOK  {out_path}  ({len(ico_bytes):,} bytes)")
    print("\nTo update the desktop shortcut, run:")
    print(f'  powershell -ExecutionPolicy Bypass -File "{out_dir}\\make_shortcut.ps1" -IconPath "{out_path}"')


if __name__ == "__main__":
    main()
