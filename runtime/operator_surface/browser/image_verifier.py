"""Local PNG visual evidence checks for browser operator screenshots."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import struct
import zlib
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _samples_for_color_type(color_type: int) -> int | None:
    return {
        0: 1,  # grayscale
        2: 3,  # rgb
        3: 1,  # indexed
        4: 2,  # grayscale + alpha
        6: 4,  # rgba
    }.get(color_type)


def _decode_png_pixels(path: Path) -> tuple[int, int, int, int, list[bytes]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG file")

    offset = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = None
    idat_parts: list[bytes] = []

    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data_start = offset + 8
        chunk_data_end = chunk_data_start + length
        if chunk_data_end + 4 > len(data):
            raise ValueError("truncated PNG chunk")
        chunk_data = data[chunk_data_start:chunk_data_end]
        offset = chunk_data_end + 4

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            if compression != 0 or filter_method != 0 or interlace != 0:
                raise ValueError("unsupported PNG compression/filter/interlace mode")
        elif chunk_type == b"IDAT":
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    if width is None or height is None or bit_depth is None or color_type is None:
        raise ValueError("missing PNG IHDR")
    samples = _samples_for_color_type(color_type)
    if bit_depth != 8 or samples is None:
        raise ValueError(f"unsupported PNG color format bit_depth={bit_depth} color_type={color_type}")

    bpp = samples
    row_bytes = int(width) * bpp
    raw = zlib.decompress(b"".join(idat_parts))
    expected = (row_bytes + 1) * int(height)
    if len(raw) < expected:
        raise ValueError("truncated PNG image data")

    rows: list[bytes] = []
    previous = bytearray(row_bytes)
    cursor = 0
    for _ in range(int(height)):
        filter_type = raw[cursor]
        cursor += 1
        scanline = bytearray(raw[cursor : cursor + row_bytes])
        cursor += row_bytes

        for index in range(row_bytes):
            left = scanline[index - bpp] if index >= bpp else 0
            up = previous[index]
            upper_left = previous[index - bpp] if index >= bpp else 0
            if filter_type == 1:
                scanline[index] = (scanline[index] + left) & 0xFF
            elif filter_type == 2:
                scanline[index] = (scanline[index] + up) & 0xFF
            elif filter_type == 3:
                scanline[index] = (scanline[index] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                scanline[index] = (scanline[index] + _paeth(left, up, upper_left)) & 0xFF
            elif filter_type != 0:
                raise ValueError(f"unsupported PNG filter type {filter_type}")

        rows.append(bytes(scanline))
        previous = scanline

    return int(width), int(height), int(bit_depth), int(color_type), rows


def analyze_png_nonblank(
    path: str | Path,
    *,
    min_unique_colors: int = 2,
    max_dominant_ratio: float = 0.995,
    max_sample_pixels: int = 500_000,
) -> dict[str, Any]:
    """Return visual nonblank evidence for a local PNG screenshot."""

    screenshot = Path(path)
    result: dict[str, Any] = {
        "path": str(screenshot),
        "exists": screenshot.is_file(),
        "png": False,
        "ok": False,
        "reason": "file-missing",
    }
    if not screenshot.is_file():
        return result

    result["size_bytes"] = screenshot.stat().st_size
    try:
        width, height, bit_depth, color_type, rows = _decode_png_pixels(screenshot)
    except Exception as exc:
        result.update({"reason": "png-decode-failed", "error": str(exc)})
        return result

    pixel_count = width * height
    stride = max(1, pixel_count // max(1, max_sample_pixels))
    samples = _samples_for_color_type(color_type) or 1
    colors: Counter[bytes] = Counter()
    seen = 0
    cursor = 0
    for row in rows:
        for start in range(0, len(row), samples):
            if cursor % stride == 0:
                colors[row[start : start + samples]] += 1
                seen += 1
            cursor += 1

    dominant_count = max(colors.values()) if colors else 0
    dominant_ratio = dominant_count / seen if seen else 1.0
    unique_color_count = len(colors)
    ok = unique_color_count >= int(min_unique_colors) and dominant_ratio <= float(max_dominant_ratio)
    reason = "nonblank" if ok else "blank-or-near-uniform"
    result.update(
        {
            "png": True,
            "ok": ok,
            "reason": reason,
            "width": width,
            "height": height,
            "bit_depth": bit_depth,
            "color_type": color_type,
            "pixel_count": pixel_count,
            "sampled_pixels": seen,
            "unique_color_count": unique_color_count,
            "dominant_color_ratio": round(dominant_ratio, 6),
            "min_unique_colors": int(min_unique_colors),
            "max_dominant_ratio": float(max_dominant_ratio),
        }
    )
    return result
