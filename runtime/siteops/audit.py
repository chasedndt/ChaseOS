"""Scoped SiteOps run and audit event storage."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.siteops.models import SiteOpsAuditEvent, SiteOpsRun
from runtime.siteops.errors import SiteOpsNotFoundError
from runtime.siteops.tenancy import vault_root
from runtime.siteops.validator import SECRET_KEY_PATTERNS


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def runs_dir(root: Path | str | None, tenant_id: str, workspace_id: str) -> Path:
    return vault_root(root) / "07_LOGS" / "SiteOps-Runs" / tenant_id / workspace_id


def audits_dir(root: Path | str | None, tenant_id: str, workspace_id: str) -> Path:
    return vault_root(root) / "07_LOGS" / "SiteOps-Audits" / tenant_id / workspace_id


def run_path(root: Path | str | None, tenant_id: str, workspace_id: str, run_id: str) -> Path:
    return runs_dir(root, tenant_id, workspace_id) / f"{run_id}.json"


def audit_path(root: Path | str | None, tenant_id: str, workspace_id: str, run_id: str) -> Path:
    return audits_dir(root, tenant_id, workspace_id) / f"{run_id}.jsonl"


def _redact(value: Any, *, path: str = "$", redacted: list[str] | None = None) -> tuple[Any, list[str]]:
    redacted = redacted if redacted is not None else []
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            lower = str(key).lower()
            if any(pattern in lower for pattern in SECRET_KEY_PATTERNS):
                clean[key] = "[REDACTED]"
                redacted.append(f"{path}.{key}")
            else:
                clean[key], redacted = _redact(item, path=f"{path}.{key}", redacted=redacted)
        return clean, redacted
    if isinstance(value, list):
        items: list[Any] = []
        for index, item in enumerate(value):
            clean_item, redacted = _redact(item, path=f"{path}[{index}]", redacted=redacted)
            items.append(clean_item)
        return items, redacted
    return value, redacted


def write_run_record(root: Path | str | None, run: SiteOpsRun) -> str:
    path = run_path(root, run.tenant_id, run.workspace_id, run.run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run.as_dict(), indent=2) + "\n", encoding="utf-8")
    return str(path)


def append_audit_event(root: Path | str | None, event: SiteOpsAuditEvent) -> str:
    path = audit_path(root, event.tenant_id, event.workspace_id, event.run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = event.as_dict()
    payload["metadata"], redacted = _redact(payload.get("metadata", {}))
    payload["redacted_fields"] = sorted(set(payload.get("redacted_fields", []) + redacted))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return str(path)


def list_run_records(root: Path | str | None = None, tenant_id: str = "local", workspace_id: str | None = None) -> list[dict[str, Any]]:
    base = vault_root(root) / "07_LOGS" / "SiteOps-Runs" / tenant_id
    folders = [base / workspace_id] if workspace_id else ([path for path in base.glob("*") if path.is_dir()] if base.exists() else [])
    records: list[dict[str, Any]] = []
    for folder in folders:
        for path in sorted(folder.glob("*.json")):
            item = json.loads(path.read_text(encoding="utf-8"))
            item["run_ref"] = str(path)
            records.append(item)
    return records


def show_run_record(root: Path | str | None, run_id: str, tenant_id: str | None = None) -> dict[str, Any]:
    base = vault_root(root) / "07_LOGS" / "SiteOps-Runs"
    tenant_folders = [base / tenant_id] if tenant_id else ([path for path in base.glob("*") if path.is_dir()] if base.exists() else [])
    for tenant_folder in tenant_folders:
        for path in tenant_folder.glob("*/*.json"):
            item = json.loads(path.read_text(encoding="utf-8"))
            if item.get("run_id") == run_id:
                item["run_ref"] = str(path)
                return item
    raise SiteOpsNotFoundError(f"SiteOpsRun not found: {run_id}")
