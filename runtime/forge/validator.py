"""Manifest validator for Chaser Forge generated extensions."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from runtime.forge.extension_points import (
    ALLOWED_AGENT_TOOLS,
    ALLOWED_MEMORY_SCOPES,
    ALLOWED_PERMISSIONS,
    ALLOWED_UI_COMPONENT_TYPES,
    ALLOWED_WORKFLOW_NODE_TYPES,
    APPROVAL_REQUIRED_PERMISSIONS,
    APPROVED_EXTENSION_POINTS,
    CORE_SCHEMA_COLLECTIONS,
    FORBIDDEN_AGENT_TOOLS,
    FORBIDDEN_MEMORY_SCOPES,
    FORBIDDEN_PERMISSIONS,
    FORBIDDEN_UI_COMPONENT_TYPES,
    FORBIDDEN_WORKFLOW_NODE_TYPES,
    LIFECYCLE_MODEL,
    LIFECYCLE_STAGE_IDS,
)
from runtime.forge.protected_core import validate_generated_extension_paths


MANIFEST_SCHEMA_VERSION = "forge.extension.v1"
_EXTENSION_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,62}$")
_SAFE_LOCAL_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{2,96}$")

REQUIRED_TOP_LEVEL_FIELDS = (
    "schemaVersion",
    "id",
    "name",
    "description",
    "version",
    "status",
    "createdBy",
    "compatibility",
    "risk",
    "permissions",
    "extensionPoints",
    "rollback",
)


def _issue(severity: str, code: str, message: str, *, field: str = "", item: str = "") -> dict[str, str]:
    issue = {"severity": severity, "code": code, "message": message}
    if field:
        issue["field"] = field
    if item:
        issue["item"] = item
    return issue


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _string_list(value: Any) -> list[str]:
    return [item for item in _as_list(value) if isinstance(item, str)]


def _permission_values(manifest: dict[str, Any]) -> list[str]:
    permissions = list(_string_list(manifest.get("permissions")))
    for point in _as_list(manifest.get("extensionPoints")):
        if isinstance(point, dict):
            permissions.extend(_string_list(point.get("permissions")))
    return permissions


def _validate_permissions(manifest: dict[str, Any], issues: list[dict[str, str]], approvals: set[str]) -> None:
    for permission in sorted(set(_permission_values(manifest))):
        if permission in FORBIDDEN_PERMISSIONS:
            issues.append(
                _issue(
                    "blocked",
                    "forbidden_permission",
                    "Permission is reserved for ChaseOS protected core authority",
                    field="permissions",
                    item=permission,
                )
            )
        elif permission not in ALLOWED_PERMISSIONS:
            issues.append(
                _issue(
                    "blocked",
                    "unknown_permission",
                    "Permission is not in the approved Forge permission set",
                    field="permissions",
                    item=permission,
                )
            )
        elif permission in APPROVAL_REQUIRED_PERMISSIONS:
            approvals.add(f"permission:{permission}")


def _validate_extension_points(manifest: dict[str, Any], issues: list[dict[str, str]], approvals: set[str]) -> None:
    extension_id = manifest.get("id", "")
    points = _as_list(manifest.get("extensionPoints"))
    if not points:
        issues.append(_issue("blocked", "missing_extension_points", "Manifest must declare at least one extension point", field="extensionPoints"))
        return

    seen: set[str] = set()
    for index, point in enumerate(points):
        field = f"extensionPoints[{index}]"
        if not isinstance(point, dict):
            issues.append(_issue("blocked", "invalid_extension_point", "Extension point entries must be objects", field=field))
            continue
        point_type = str(point.get("type", ""))
        local_id = str(point.get("id", ""))
        if point_type not in APPROVED_EXTENSION_POINTS:
            issues.append(
                _issue(
                    "blocked",
                    "unapproved_extension_point",
                    "Extension point is not approved for Chaser Forge",
                    field=f"{field}.type",
                    item=point_type,
                )
            )
        if local_id:
            if not _SAFE_LOCAL_ID_RE.match(local_id):
                issues.append(_issue("blocked", "unsafe_extension_point_id", "Extension point id is not a safe local id", field=f"{field}.id", item=local_id))
            if local_id in seen:
                issues.append(_issue("blocked", "duplicate_extension_point_id", "Extension point id is duplicated", field=f"{field}.id", item=local_id))
            seen.add(local_id)
        if point_type in {"agent.preset", "workflow.template", "connector.usage"}:
            approvals.add(f"extension_point:{point_type}")

        route = point.get("route")
        if point_type in {"workspace.page", "sidebar.nav.item", "command.palette.action"} and route:
            expected_prefix = f"/workspace/{{workspaceId}}/extensions/{extension_id}"
            if not isinstance(route, str) or not route.startswith(expected_prefix):
                issues.append(
                    _issue(
                        "blocked",
                        "unsafe_route_namespace",
                        "Extension routes must stay under /workspace/{workspaceId}/extensions/{extensionId}",
                        field=f"{field}.route",
                        item=str(route),
                    )
                )

        component = point.get("component")
        if component:
            _validate_ui_component(component, issues, f"{field}.component")


def _validate_ui_component(component: Any, issues: list[dict[str, str]], field: str) -> None:
    component_type = component.get("type") if isinstance(component, dict) else component
    component_type = str(component_type or "")
    if component_type in FORBIDDEN_UI_COMPONENT_TYPES:
        issues.append(_issue("blocked", "forbidden_ui_component", "UI component type can inject or replace protected shell behavior", field=field, item=component_type))
    elif component_type and component_type not in ALLOWED_UI_COMPONENT_TYPES:
        issues.append(_issue("blocked", "unknown_ui_component", "UI component type is not approved for Forge", field=field, item=component_type))


def _validate_ui(manifest: dict[str, Any], issues: list[dict[str, str]]) -> None:
    ui = manifest.get("ui") or {}
    if not isinstance(ui, dict):
        issues.append(_issue("blocked", "invalid_ui_block", "ui must be an object", field="ui"))
        return
    for index, component in enumerate(_as_list(ui.get("components"))):
        _validate_ui_component(component, issues, f"ui.components[{index}]")
    for index, route in enumerate(_string_list(ui.get("routes"))):
        expected_prefix = f"/workspace/{{workspaceId}}/extensions/{manifest.get('id', '')}"
        if not route.startswith(expected_prefix):
            issues.append(_issue("blocked", "unsafe_route_namespace", "UI routes must stay under the extension namespace", field=f"ui.routes[{index}]", item=route))


def _validate_workflows(manifest: dict[str, Any], issues: list[dict[str, str]], approvals: set[str]) -> None:
    for workflow_index, workflow in enumerate(_as_list(manifest.get("workflows"))):
        if not isinstance(workflow, dict):
            issues.append(_issue("blocked", "invalid_workflow", "Workflow declarations must be objects", field=f"workflows[{workflow_index}]"))
            continue
        for step_index, step in enumerate(_as_list(workflow.get("steps"))):
            step_type = step.get("type") if isinstance(step, dict) else step
            step_type = str(step_type or "")
            field = f"workflows[{workflow_index}].steps[{step_index}].type"
            if step_type in FORBIDDEN_WORKFLOW_NODE_TYPES:
                issues.append(_issue("blocked", "forbidden_workflow_node", "Workflow node type can mutate protected core or execute code", field=field, item=step_type))
            elif step_type and step_type not in ALLOWED_WORKFLOW_NODE_TYPES:
                issues.append(_issue("blocked", "unknown_workflow_node", "Workflow node type is not approved for Forge", field=field, item=step_type))
            elif step_type in {"agent.invoke", "extension.data.write", "notification.draft", "workflow.template.run"}:
                approvals.add(f"workflow_node:{step_type}")


def _validate_agents(manifest: dict[str, Any], issues: list[dict[str, str]], approvals: set[str]) -> None:
    for agent_index, agent in enumerate(_as_list(manifest.get("agents"))):
        if not isinstance(agent, dict):
            issues.append(_issue("blocked", "invalid_agent", "Agent declarations must be objects", field=f"agents[{agent_index}]"))
            continue
        for tool in _string_list(agent.get("tools")):
            field = f"agents[{agent_index}].tools"
            if tool in FORBIDDEN_AGENT_TOOLS:
                issues.append(_issue("blocked", "forbidden_agent_tool", "Agent tool crosses protected runtime authority", field=field, item=tool))
            elif tool not in ALLOWED_AGENT_TOOLS:
                issues.append(_issue("blocked", "unknown_agent_tool", "Agent tool is not approved for Forge", field=field, item=tool))
            elif tool in {"data.write.extension", "notification.draft", "workflow.run.approval_gated"}:
                approvals.add(f"agent_tool:{tool}")
        for scope in _string_list(agent.get("memoryScopes")):
            field = f"agents[{agent_index}].memoryScopes"
            if scope in FORBIDDEN_MEMORY_SCOPES:
                issues.append(_issue("blocked", "forbidden_memory_scope", "Agent memory scope crosses governed core memory boundaries", field=field, item=scope))
            elif scope not in ALLOWED_MEMORY_SCOPES:
                issues.append(_issue("blocked", "unknown_memory_scope", "Agent memory scope is not approved for Forge", field=field, item=scope))


def _validate_data_schemas(manifest: dict[str, Any], issues: list[dict[str, str]]) -> None:
    extension_id = str(manifest.get("id", "")).replace("-", "_")
    required_prefix = f"ext_{extension_id}_"
    for index, schema in enumerate(_as_list(manifest.get("dataSchemas"))):
        if not isinstance(schema, dict):
            issues.append(_issue("blocked", "invalid_data_schema", "Data schema entries must be objects", field=f"dataSchemas[{index}]"))
            continue
        collection = str(schema.get("collection", ""))
        if collection in CORE_SCHEMA_COLLECTIONS:
            issues.append(_issue("blocked", "core_collection_name", "Extension data cannot use a protected core collection name", field=f"dataSchemas[{index}].collection", item=collection))
        elif collection and not collection.startswith(required_prefix):
            issues.append(
                _issue(
                    "blocked",
                    "unsafe_collection_namespace",
                    "Extension collection names must use ext_{extension_id}_ namespace",
                    field=f"dataSchemas[{index}].collection",
                    item=collection,
                )
            )


def _validate_preview(manifest: dict[str, Any], issues: list[dict[str, str]]) -> None:
    preview = manifest.get("preview") or {}
    if not isinstance(preview, dict):
        issues.append(_issue("blocked", "invalid_preview_block", "preview must be an object", field="preview"))
        return
    for key in ("productionWrites", "externalCalls", "scheduleActivation", "secretsAccess"):
        if preview.get(key) is True:
            issues.append(_issue("blocked", "unsafe_preview_capability", "Preview mode cannot enable production writes, external calls, schedules, or secrets access", field=f"preview.{key}", item=key))


def _validate_rollback(manifest: dict[str, Any], issues: list[dict[str, str]]) -> None:
    rollback = manifest.get("rollback")
    if not isinstance(rollback, dict):
        issues.append(_issue("blocked", "invalid_rollback", "rollback must be an object", field="rollback"))
        return
    for key in ("strategy", "snapshotPolicy"):
        if not rollback.get(key):
            issues.append(_issue("blocked", "rollback_missing_field", "Rollback must declare strategy and snapshotPolicy", field=f"rollback.{key}"))


def _declared_risk_level(manifest: dict[str, Any]) -> str:
    risk = manifest.get("risk") or {}
    if isinstance(risk, dict):
        level = str(risk.get("level", "low")).lower()
    else:
        level = str(risk).lower()
    return level if level in {"low", "medium", "high"} else "unknown"


def validate_manifest(manifest: dict[str, Any], target_paths: list[str] | tuple[str, ...] | None = None) -> dict[str, Any]:
    """Validate a Forge extension manifest without writing or installing anything."""

    issues: list[dict[str, str]] = []
    approvals: set[str] = set()
    if not isinstance(manifest, dict):
        issues.append(_issue("blocked", "invalid_manifest", "Manifest must be a JSON object", field="$"))
        manifest = {}

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in manifest:
            issues.append(_issue("blocked", "missing_required_field", "Manifest is missing a required top-level field", field=field))

    extension_id = str(manifest.get("id", ""))
    if not _EXTENSION_ID_RE.match(extension_id):
        issues.append(_issue("blocked", "invalid_extension_id", "Extension id must be a lowercase slug", field="id", item=extension_id))

    schema_version = str(manifest.get("schemaVersion", ""))
    if schema_version != MANIFEST_SCHEMA_VERSION:
        issues.append(_issue("blocked", "unsupported_schema_version", "Manifest schemaVersion is not supported", field="schemaVersion", item=schema_version))

    status = str(manifest.get("status", ""))
    if status not in LIFECYCLE_STAGE_IDS:
        issues.append(_issue("blocked", "invalid_lifecycle_status", "Manifest status must match the Forge lifecycle model", field="status", item=status))
    elif status == "active":
        approvals.add("lifecycle:live_install")

    _validate_permissions(manifest, issues, approvals)
    _validate_extension_points(manifest, issues, approvals)
    _validate_ui(manifest, issues)
    _validate_workflows(manifest, issues, approvals)
    _validate_agents(manifest, issues, approvals)
    _validate_data_schemas(manifest, issues)
    _validate_preview(manifest, issues)
    _validate_rollback(manifest, issues)

    install = manifest.get("install") if isinstance(manifest.get("install"), dict) else {}
    manifest_target_paths = target_paths if target_paths is not None else install.get("targetPaths", [])
    path_guard = validate_generated_extension_paths(extension_id or "invalid-extension", _string_list(manifest_target_paths))
    for path_issue in path_guard["issues"]:
        issues.append(
            _issue(
                path_issue.get("severity", "blocked"),
                path_issue.get("code", "path_guard_failed"),
                path_issue.get("message", "Target path failed Forge protected-core validation"),
                field="install.targetPaths",
                item=path_issue.get("path", ""),
            )
        )

    if not issues:
        approvals.add("forge.live_install.operator_approval")
    approvals.add("forge.rollback.snapshot_required")

    errors = [issue for issue in issues if issue["severity"] in {"blocked", "error"}]
    warnings = [issue for issue in issues if issue["severity"] == "warning"]
    valid = not errors
    declared_risk = _declared_risk_level(manifest)
    risk_level = "blocked" if errors else declared_risk

    return {
        "valid": valid,
        "status": "valid" if valid else "blocked",
        "schemaVersion": schema_version,
        "extensionId": extension_id,
        "declaredRiskLevel": declared_risk,
        "riskLevel": risk_level,
        "extensionPoints": [
            deepcopy(point)
            for point in _as_list(manifest.get("extensionPoints"))
            if isinstance(point, dict)
        ],
        "approvedExtensionPointTypes": sorted(APPROVED_EXTENSION_POINTS),
        "installLifecycle": list(LIFECYCLE_MODEL),
        "requiredApprovals": sorted(approvals),
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
        "protectedCore": {
            "coreMutationAllowed": False,
            "targetPathValidation": path_guard,
        },
    }
