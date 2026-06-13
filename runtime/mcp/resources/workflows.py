"""Workflow registry and role-boundary resource handlers."""

from __future__ import annotations

from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.types import HandlerResult, PermissionEnvelope
from runtime.mcp.yaml_compat import safe_load


_VALID_FILTERS = {"active", "draft", "all"}


def workflows_registry(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    from runtime.mcp.errors import input_error  # local import to avoid circular risk

    filter_status = params.get("filter", "all")
    if filter_status not in _VALID_FILTERS:
        return HandlerResult(
            False,
            error=input_error(
                "invalid_filter_value",
                f"filter must be one of: {', '.join(sorted(_VALID_FILTERS))}",
                provided=filter_status,
            ),
        )

    registry_dir = config.vault_root / "runtime" / "workflows" / "registry"
    workflows: list[dict[str, Any]] = []
    if registry_dir.exists():
        for path in sorted(registry_dir.iterdir()):
            if path.suffix not in {".yaml", ".yml"} or path.name.startswith("_"):
                continue
            raw = safe_load(path.read_text(encoding="utf-8")) or {}
            status = raw.get("status")
            if filter_status != "all" and status != filter_status:
                continue
            workflows.append(
                {
                    "id": raw.get("id", path.stem),
                    "name": raw.get("name"),
                    "status": status,
                    "task_type": raw.get("task_type"),
                    "role_card": raw.get("role_card"),
                    "permission_ceiling": raw.get("permission_ceiling"),
                    "writeback_targets": list(raw.get("writeback_targets") or []),
                }
            )
    return HandlerResult(
        True,
        {"workflows": workflows, "filter": filter_status},
        audit_metadata={"resource": "workflows.registry", "count": len(workflows), "filter": filter_status},
    )


def workflows_role_boundaries(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    cards_dir = config.vault_root / "06_AGENTS" / "role-cards"
    cards: list[dict[str, Any]] = []
    if cards_dir.exists():
        for path in sorted(cards_dir.iterdir()):
            if path.suffix not in {".yaml", ".yml"} or path.name.startswith("_"):
                continue
            raw = safe_load(path.read_text(encoding="utf-8")) or {}
            cards.append(
                {
                    "id": raw.get("id", path.stem),
                    "name": raw.get("name"),
                    "allowed_actions": list(raw.get("allowed_actions") or []),
                    "forbidden_actions": list(raw.get("forbidden_actions") or []),
                    "write_scope": list(raw.get("write_scope") or []),
                    "forbidden_write_zones": list(raw.get("forbidden_write_zones") or []),
                }
            )
    return HandlerResult(
        True,
        {"role_cards": cards},
        audit_metadata={"resource": "workflows.role_boundaries", "count": len(cards)},
    )
