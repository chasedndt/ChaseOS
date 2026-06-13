"""Shared source metadata helpers for Creator Engine intake."""

from __future__ import annotations

from typing import Any


MANUAL_SOURCE_METADATA_KEYS = {
    "source_title",
    "source_origin",
    "source_kind",
    "recorded_at",
    "source_notes",
}


def normalize_manual_source_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Return only the bounded operator-supplied metadata fields Creator Engine accepts."""

    if not metadata:
        return {}
    normalized: dict[str, Any] = {}
    for key, raw_value in metadata.items():
        if key not in MANUAL_SOURCE_METADATA_KEYS or raw_value is None:
            continue
        if isinstance(raw_value, list):
            notes = [_clean_metadata_text(item) for item in raw_value]
            cleaned_notes = [item for item in notes if item]
            if cleaned_notes:
                normalized[key] = cleaned_notes
            continue
        cleaned = _clean_metadata_text(raw_value)
        if cleaned:
            normalized[key] = cleaned
    return normalized


def _clean_metadata_text(value: Any) -> str:
    return str(value).replace("\r\n", "\n").replace("\r", "\n").strip()[:1000]
