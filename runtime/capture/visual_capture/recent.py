"""Recent visual capture listing helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def list_recent_visual_captures(vault_root: str | Path, *, limit: int = 10) -> list[dict[str, Any]]:
    """List recent VCMI saves by reading Phase 8 quarantine sidecars."""

    vault = Path(vault_root).resolve()
    quarantine_root = vault / "03_INPUTS" / "00_QUARANTINE"
    if not quarantine_root.exists():
        return []

    rows: list[dict[str, Any]] = []
    for sidecar_path in quarantine_root.rglob("*.meta.json"):
        try:
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        vc_meta = (sidecar.get("extra_metadata") or {}).get("visual_capture")
        if not isinstance(vc_meta, dict):
            continue
        disposition_policy = (
            vc_meta.get("attachment_disposition_policy")
            if isinstance(vc_meta.get("attachment_disposition_policy"), dict)
            else {}
        )
        attachments = vc_meta.get("attachments") if isinstance(vc_meta.get("attachments"), list) else []
        content_filename = sidecar.get("content_filename") or ""
        content_path = sidecar_path.parent / content_filename if content_filename else None
        rows.append(
            {
                "title": sidecar.get("title") or vc_meta.get("title") or content_filename,
                "capture_id": sidecar.get("capture_id"),
                "visual_capture_id": vc_meta.get("capture_id"),
                "captured_at": sidecar.get("captured_at") or "",
                "input_class": sidecar.get("input_class"),
                "profile": vc_meta.get("profile"),
                "source_platform": sidecar.get("source_platform"),
                "review_status": vc_meta.get("review_status"),
                "canonical_status": vc_meta.get("canonical_status"),
                "redaction_status": vc_meta.get("redaction_status"),
                "content_path": _vault_relative(content_path, vault) if content_path else "",
                "sidecar_path": _vault_relative(sidecar_path, vault),
                "visual_capture_packet_path": vc_meta.get("visual_capture_packet_path") or "",
                "attachment_count": len([item for item in attachments if isinstance(item, dict)]),
                "attachment_disposition": disposition_policy.get("default_disposition") or "not-applicable",
                "attachment_delete_request_status": disposition_policy.get("delete_request_status") or "",
                "attachment_cleanup_available": bool(disposition_policy.get("cleanup_executor_available")),
            }
        )

    rows.sort(key=lambda item: item.get("captured_at") or "", reverse=True)
    return rows[: max(0, int(limit))]


def _vault_relative(path: Path, vault_root: Path) -> str:
    try:
        return path.resolve().relative_to(vault_root).as_posix()
    except ValueError:
        return str(path)
