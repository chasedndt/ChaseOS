"""runtime.audit.recent resource handler."""

from __future__ import annotations

import json
from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.types import HandlerResult, PermissionEnvelope


def runtime_audit_recent(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    limit = int(params.get("limit", 10))
    limit = max(1, min(limit, 50))
    records: list[dict[str, Any]] = []
    if config.audit_dir.exists():
        files = sorted(
            [path for path in config.audit_dir.iterdir() if path.suffix == ".json"],
            key=lambda p: p.name,
            reverse=True,
        )
        for path in files[:limit]:
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            # Return frozen V1 schema fields only.
            records.append(
                {
                    "schema_version": raw.get("schema_version", "1.0"),
                    "request_id": raw.get("request_id"),
                    "recorded_at": raw.get("recorded_at"),
                    "surface_id": raw.get("surface_id"),
                    "surface_class": raw.get("surface_class"),
                    "runtime_id": raw.get("runtime_id"),
                    "trust_tier": raw.get("trust_tier"),
                    "safety_mode": raw.get("safety_mode"),
                    "outcome": raw.get("outcome"),
                    "outcome_detail": raw.get("outcome_detail"),
                    "files_read": raw.get("files_read", []),
                    "files_written": raw.get("files_written", []),
                    "error_code": raw.get("error_code"),
                    "error_message": raw.get("error_message"),
                }
            )
    return HandlerResult(
        True,
        {"records": records},
        audit_metadata={"resource": "runtime.audit.recent", "count": len(records)},
    )
