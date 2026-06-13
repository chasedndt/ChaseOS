"""Envelope-owned audit logger for Runtime MCP V1.

Schema and naming convention frozen against ChaseOS-MCP-Audit-Policy.md v1.0.
MCPAuditLogger.log() raises MCPAuditError on write failure.
The server/envelope layer decides fail-open vs fail-closed policy per surface.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from runtime.mcp.types import AuditRecord


class MCPAuditError(OSError):
    """Raised by MCPAuditLogger.log() when the audit write fails."""


class MCPAuditLogger:
    """Write immutable JSON audit records to 07_LOGS/Agent-Activity/."""

    def __init__(self, audit_dir: Path) -> None:
        self.audit_dir = audit_dir

    def log(
        self,
        request_id: str,
        surface_id: str,
        surface_class: str,
        runtime_id: str,
        trust_tier: int,
        safety_mode: str,
        outcome: str,
        outcome_detail: str | None,
        files_read: list[str],
        files_written: list[str],
        error_code: str | None,
        error_message: str | None,
    ) -> None:
        """Write audit record to audit_dir.

        Raises MCPAuditError if write fails.
        The calling server/envelope applies fail-open vs fail-closed policy.
        """
        dt = datetime.now(timezone.utc).replace(microsecond=0)
        ts = dt.strftime("%Y%m%d-%H%M%S")
        recorded_at = dt.isoformat().replace("+00:00", "Z")

        # Filename convention: {YYYYMMDD-HHMMSS}__mcp__{surface_id}__{request_id[:8]}.json
        # Strip common prefix to get hex chars for the request_id suffix.
        _rid = request_id[4:] if request_id.startswith("req-") else request_id
        req_short = _rid.replace("-", "")[:8] or request_id[:8]

        stem = f"{ts}__mcp__{surface_id}__{req_short}"
        record = AuditRecord(
            schema_version="1.0",
            request_id=request_id,
            recorded_at=recorded_at,
            surface_id=surface_id,
            surface_class=surface_class,
            runtime_id=runtime_id,
            trust_tier=trust_tier,
            safety_mode=safety_mode,
            outcome=outcome,
            outcome_detail=outcome_detail,
            files_read=list(files_read),
            files_written=list(files_written),
            error_code=error_code,
            error_message=error_message,
        )
        try:
            self.audit_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = self.audit_dir / f".{stem}.tmp"
            final_path = self.audit_dir / f"{stem}.json"
            tmp_path.write_text(
                json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            tmp_path.replace(final_path)
        except Exception as exc:  # noqa: BLE001
            raise MCPAuditError(str(exc)) from exc
