"""Approved extension points for Chaser Forge generated modules."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ForgeExtensionPoint:
    id: str
    label: str
    description: str
    install_surface: str
    lifecycle_gate: str
    allowed_fields: tuple[str, ...]
    forbidden_authority: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


APPROVED_EXTENSION_POINTS: dict[str, ForgeExtensionPoint] = {
    "sidebar.nav.item": ForgeExtensionPoint(
        id="sidebar.nav.item",
        label="Sidebar navigation item",
        description="Adds a navigation entry that routes to an extension-owned page.",
        install_surface="Studio navigation registry",
        lifecycle_gate="route namespace and permission validation",
        allowed_fields=("label", "icon", "route", "workspaceScope"),
        forbidden_authority=("core nav rewrite", "settings mutation", "hidden route"),
    ),
    "workspace.page": ForgeExtensionPoint(
        id="workspace.page",
        label="Workspace page",
        description="Adds a page mounted under the extension workspace namespace.",
        install_surface="Studio workspace page registry",
        lifecycle_gate="sandbox preview before live mount",
        allowed_fields=("title", "route", "component", "dataScopes"),
        forbidden_authority=("core page replacement", "arbitrary iframe", "script injection"),
    ),
    "dashboard.widget": ForgeExtensionPoint(
        id="dashboard.widget",
        label="Dashboard widget",
        description="Adds a bounded dashboard widget backed by extension-owned data.",
        install_surface="Dashboard widget registry",
        lifecycle_gate="read model and component validation",
        allowed_fields=("title", "widgetType", "dataSource", "refreshPolicy"),
        forbidden_authority=("dashboard layout rewrite", "live external calls without approval"),
    ),
    "agent.preset": ForgeExtensionPoint(
        id="agent.preset",
        label="Agent preset",
        description="Declares a bounded agent preset that can be routed through the Agent Bus.",
        install_surface="Agent preset registry",
        lifecycle_gate="tool, memory, and permission validation",
        allowed_fields=("name", "role", "tools", "memoryScopes", "taskTypes"),
        forbidden_authority=("runtime owner changes", "raw memory writes", "unbounded tools"),
    ),
    "workflow.template": ForgeExtensionPoint(
        id="workflow.template",
        label="Workflow template",
        description="Declares a reusable workflow template that remains approval-gated.",
        install_surface="Workflow template registry",
        lifecycle_gate="node and writeback target validation",
        allowed_fields=("name", "trigger", "steps", "approvalRule", "writebackTargets"),
        forbidden_authority=("schedule activation", "shell execution", "protected writes"),
    ),
    "form.schema": ForgeExtensionPoint(
        id="form.schema",
        label="Form schema",
        description="Adds an extension-owned input schema for forms and captures.",
        install_surface="Form schema registry",
        lifecycle_gate="field and data collection validation",
        allowed_fields=("fields", "validation", "collection"),
        forbidden_authority=("auth form replacement", "secrets capture"),
    ),
    "command.palette.action": ForgeExtensionPoint(
        id="command.palette.action",
        label="Command palette action",
        description="Adds a command that opens previews or queues governed actions.",
        install_surface="Command palette registry",
        lifecycle_gate="action handler and approval validation",
        allowed_fields=("label", "commandId", "targetRoute", "approvalRule"),
        forbidden_authority=("direct execution", "permission escalation"),
    ),
    "report.template": ForgeExtensionPoint(
        id="report.template",
        label="Report template",
        description="Adds a report renderer that reads extension-approved data.",
        install_surface="Report template registry",
        lifecycle_gate="source and output validation",
        allowed_fields=("title", "sections", "dataSources", "exportTypes"),
        forbidden_authority=("canonical overwrite", "external publish without approval"),
    ),
    "notification.template": ForgeExtensionPoint(
        id="notification.template",
        label="Notification template",
        description="Adds a notification draft template for approval-gated delivery.",
        install_surface="Notification template registry",
        lifecycle_gate="delivery and connector permission validation",
        allowed_fields=("title", "body", "channels", "approvalRule"),
        forbidden_authority=("direct send", "silent background delivery"),
    ),
    "connector.usage": ForgeExtensionPoint(
        id="connector.usage",
        label="Connector usage",
        description="Declares bounded read-only connector usage required by an extension.",
        install_surface="Connector permission registry",
        lifecycle_gate="connector scope and approval validation",
        allowed_fields=("connectorId", "scopes", "rateLimit", "approvalRule"),
        forbidden_authority=("credential read", "connector write without approval"),
    ),
    "marketplace.template": ForgeExtensionPoint(
        id="marketplace.template",
        label="Marketplace template",
        description="Packages an extension as a template for reviewable reuse.",
        install_surface="Marketplace template registry",
        lifecycle_gate="package integrity and provenance validation",
        allowed_fields=("category", "version", "license", "provenance"),
        forbidden_authority=("auto install", "core dependency mutation"),
    ),
}

APPROVED_EXTENSION_POINT_IDS: tuple[str, ...] = tuple(APPROVED_EXTENSION_POINTS)

ALLOWED_UI_COMPONENT_TYPES = frozenset(
    {
        "studio_panel",
        "dashboard_widget",
        "form",
        "table",
        "chart",
        "report_view",
        "command_action",
        "notification_draft",
    }
)

FORBIDDEN_UI_COMPONENT_TYPES = frozenset(
    {
        "raw_script",
        "inline_script",
        "iframe",
        "webview",
        "html_unsafe",
        "core_shell_patch",
    }
)

ALLOWED_WORKFLOW_NODE_TYPES = frozenset(
    {
        "approval.request",
        "agent.invoke",
        "extension.data.read",
        "extension.data.write",
        "form.submit",
        "notification.draft",
        "preview.render",
        "report.render",
        "workflow.template.run",
    }
)

FORBIDDEN_WORKFLOW_NODE_TYPES = frozenset(
    {
        "shell.execute",
        "python.exec",
        "powershell.exec",
        "node.exec",
        "raw_sql.execute",
        "core.file.write",
        "runtime.policy.write",
        "schedule.activate",
        "secrets.read",
        "credential.read",
    }
)

ALLOWED_AGENT_TOOLS = frozenset(
    {
        "content.generate",
        "content.review",
        "data.read.extension",
        "data.write.extension",
        "notification.draft",
        "report.generate",
        "workflow.run.approval_gated",
    }
)

FORBIDDEN_AGENT_TOOLS = frozenset(
    {
        "rawShell.execute",
        "powershell.execute",
        "python.execute",
        "secrets.read",
        "credentials.read",
        "runtime.policy.write",
        "core.memory.write",
        "personal_map.write",
    }
)

ALLOWED_MEMORY_SCOPES = frozenset(
    {
        "extension.local",
        "project.reference",
        "session.ephemeral",
        "workspace.readonly_summary",
    }
)

FORBIDDEN_MEMORY_SCOPES = frozenset(
    {
        "global",
        "pulse.memory",
        "personal_map",
        "runtime.profile",
        "identity.ledger",
        "permission.matrix",
    }
)

ALLOWED_PERMISSIONS = frozenset(
    {
        "workspace.read.basic",
        "extension.data.read",
        "extension.data.write",
        "ui.render.preview",
        "ui.render.workspace_page",
        "dashboard.widget.render",
        "form.submit",
        "report.render",
        "notification.draft",
        "agent.run.approval_gated",
        "workflow.run.approval_gated",
        "connector.read.metadata",
        "marketplace.package.preview",
    }
)

APPROVAL_REQUIRED_PERMISSIONS = frozenset(
    {
        "extension.data.write",
        "notification.draft",
        "agent.run.approval_gated",
        "workflow.run.approval_gated",
        "connector.read.metadata",
        "marketplace.package.preview",
    }
)

FORBIDDEN_PERMISSIONS = frozenset(
    {
        "auth.modify",
        "billing.modify",
        "permissions.modify",
        "trust_tiers.modify",
        "runtime.policy.write",
        "schedule.activate",
        "secrets.read",
        "credentials.read",
        "audit.modify",
        "core.file.write",
        "studio.shell.patch",
        "agent_bus.claim",
        "agent_bus.dispatch",
        "personal_map.write",
        "pulse.memory.write",
    }
)

CORE_SCHEMA_COLLECTIONS = frozenset(
    {
        "users",
        "sessions",
        "auth",
        "billing",
        "permissions",
        "trust_tiers",
        "audit_logs",
        "agent_bus_events",
        "runtime_profiles",
        "personal_map",
        "pulse_memory",
    }
)

LIFECYCLE_MODEL: tuple[dict[str, object], ...] = (
    {
        "id": "draft",
        "label": "Draft",
        "allowed_actions": ("edit manifest", "validate locally"),
        "writes_enabled": False,
        "required_gate": "schema validation",
    },
    {
        "id": "preview",
        "label": "Preview",
        "allowed_actions": ("render preview", "inspect permissions"),
        "writes_enabled": False,
        "required_gate": "protected-core and route validation",
    },
    {
        "id": "sandbox",
        "label": "Sandbox",
        "allowed_actions": ("write extension-owned sandbox data", "run fixture checks"),
        "writes_enabled": True,
        "required_gate": "operator sandbox approval",
    },
    {
        "id": "active",
        "label": "Live install",
        "allowed_actions": ("mount approved extension registry entry",),
        "writes_enabled": True,
        "required_gate": "operator live-install approval plus rollback snapshot",
    },
    {
        "id": "disabled",
        "label": "Disabled",
        "allowed_actions": ("read previous manifest", "rollback owned registry entry"),
        "writes_enabled": False,
        "required_gate": "rollback audit event",
    },
    {
        "id": "archived",
        "label": "Archived",
        "allowed_actions": ("retain audit trail",),
        "writes_enabled": False,
        "required_gate": "archive retention policy",
    },
)

LIFECYCLE_STAGE_IDS = frozenset(stage["id"] for stage in LIFECYCLE_MODEL)

AUDIT_EVENTS = (
    "forge.manifest.validated",
    "forge.preview.rendered",
    "forge.sandbox.approval_requested",
    "forge.sandbox.installed",
    "forge.live_install.approval_requested",
    "forge.live_install.completed",
    "forge.rollback.completed",
)


def list_approved_extension_points() -> list[dict[str, object]]:
    return [entry.to_dict() for entry in APPROVED_EXTENSION_POINTS.values()]


def is_approved_extension_point(extension_point: str) -> bool:
    return extension_point in APPROVED_EXTENSION_POINTS
