"""
runtime.operator_surface.browser.policy

Read-only Browser Operator Surface policy report.

This module exposes the current Phase 9 browser authority boundary without
launching a browser, mutating vault state, or widening adapter permissions.
"""

from __future__ import annotations

from runtime.operator_surface.adapters.browser_adapter import BrowserAdapter
from runtime.operator_surface.capabilities import SurfaceType
from runtime.operator_surface.scopes import (
    SURFACE_DEFAULT_APPROVALS,
    approval_required_actions_for,
)


PROMOTED_CLI_ACTIONS = frozenset({
    "navigate",
    "read_url",
    "read_title",
    "read_visible_text",
    "screenshot",
    "replay",
    "list_runs",
})

PROMOTED_WORKFLOWS = [
    {
        "workflow_id": "browser_research",
        "status": "active",
        "permission_ceiling": "quarantine_and_logs_only",
        "writes": [
            "03_INPUTS/00_QUARANTINE/source/",
            "07_LOGS/Operator-Briefs/",
            "07_LOGS/Agent-Activity/",
        ],
        "non_goals": [
            "recursive_crawling",
            "form_filling",
            "login_flows",
            "authenticated_sessions",
            "canonical_knowledge_promotion",
        ],
    }
]

BLOCKED_OR_UNPROMOTED_AUTHORITIES = [
    {
        "authority": "form_submit",
        "status": "always_approval_required",
        "reason": "Irreversible server-side state change.",
    },
    {
        "authority": "credential_field_fill",
        "status": "always_approval_required",
        "reason": "Credential exposure risk; credential_access=True is invalid in current scope validation.",
    },
    {
        "authority": "file_download",
        "status": "always_approval_required",
        "reason": "Unscoped filesystem write outside the current browser CLI contract.",
    },
    {
        "authority": "cookie_consent_accept",
        "status": "always_approval_required",
        "reason": "Privacy-relevant consent must not be granted silently.",
    },
    {
        "authority": "click_type_keypress_tab_management",
        "status": "adapter_supported_not_promoted_cli",
        "reason": "Internal adapter primitives exist, but promoted CLI/AOR workflows remain read/screenshot/replay/research bounded.",
    },
    {
        "authority": "authenticated_browser_session",
        "status": "not_built",
        "reason": "Adapter launches isolated headless contexts without personal profile, cookies, or saved credentials.",
    },
    {
        "authority": "canonical_vault_write",
        "status": "blocked",
        "reason": "Browser outputs route to quarantine, operator briefs, screenshots, or audit logs only.",
    },
    {
        "authority": "recursive_web_crawling",
        "status": "not_built",
        "reason": "Current workflow visits declared URLs only.",
    },
]

KNOWN_LIMITATIONS = [
    "Tier B accessibility grounding is declared but not promoted as an execution path.",
    "Tier C vision grounding is declared but not promoted as an execution path.",
    "Credential-field semantic detection for generic type/click flows is not verified; current promoted workflows avoid those flows.",
    "Post-click redirect drift is not promoted because click flows are not exposed through the CLI or browser_research workflow.",
]


def build_browser_policy_report() -> dict:
    """Return the current browser policy boundary as a JSON-serializable dict."""
    adapter_supported = set(BrowserAdapter.SUPPORTED_ACTION_TYPES)
    promoted_internal = set(PROMOTED_CLI_ACTIONS)
    defaults = set(SURFACE_DEFAULT_APPROVALS.get(SurfaceType.BROWSER, frozenset()))
    adapter_required = set(BrowserAdapter.APPROVAL_REQUIRED_ACTIONS)
    effective_required = set(approval_required_actions_for(SurfaceType.BROWSER, BrowserAdapter))

    return {
        "surface": SurfaceType.BROWSER.value,
        "policy_version": "2026-04-28",
        "status": "configured_bounded",
        "read_only": True,
        "mutates_browser": False,
        "mutates_vault": False,
        "policy_command_external_network": False,
        "browser_navigation_external_network": "scoped_by_target_uris_or_allowed_origins",
        "promoted_cli_commands": [
            "operate browser policy",
            "operate browser open",
            "operate browser inspect",
            "operate browser screenshot",
            "operate browser replay",
            "operate browser list-runs",
        ],
        "promoted_cli_action_classes": sorted(PROMOTED_CLI_ACTIONS),
        "adapter_supported_action_types": sorted(adapter_supported),
        "adapter_supported_not_promoted_cli": sorted(
            action for action in adapter_supported - promoted_internal
        ),
        "surface_default_approval_required": sorted(defaults),
        "adapter_approval_required": sorted(adapter_required),
        "effective_approval_required": sorted(effective_required),
        "blocked_or_unpromoted_authorities": BLOCKED_OR_UNPROMOTED_AUTHORITIES,
        "promoted_workflows": PROMOTED_WORKFLOWS,
        "governance": {
            "isolated_browser_context": True,
            "uses_personal_browser_profile": False,
            "credential_access_allowed": False,
            "page_content_trust": "untrusted_data_only",
            "scope_boundary": "target_uris_or_allowed_origins",
            "canonical_knowledge_write": False,
            "gate_override": False,
            "operator_audit_artifact": "07_LOGS/Agent-Activity/",
        },
        "write_surfaces": [
            "07_LOGS/Agent-Activity/",
            "07_LOGS/Operator-Screenshots/",
            "07_LOGS/Operator-Briefs/",
            "03_INPUTS/00_QUARANTINE/source/",
        ],
        "known_limitations": KNOWN_LIMITATIONS,
        "next_actions": [
            "Keep browser_research read/quarantine bounded unless a new approval-resume flow is explicitly implemented.",
            "Before promoting click/type/tab workflows, add semantic risk detection and approval-resume coverage.",
            "Wire Tier B accessibility and Tier C vision only after their grounding checks are test-backed.",
        ],
    }


def format_browser_policy_report(report: dict) -> str:
    """Return a concise human-readable report."""
    lines = [
        "ChaseOS Browser Operator Policy",
        f"  surface: {report['surface']}",
        f"  status: {report['status']}",
        f"  read_only: {report['read_only']}",
        "",
        "Promoted CLI commands:",
    ]
    for command in report["promoted_cli_commands"]:
        lines.append(f"  - chaseos {command}")

    lines.append("")
    lines.append("Effective approval-required actions:")
    for action in report["effective_approval_required"]:
        lines.append(f"  - {action}")

    lines.append("")
    lines.append("Adapter-supported but not promoted through CLI:")
    for action in report["adapter_supported_not_promoted_cli"]:
        lines.append(f"  - {action}")

    lines.append("")
    lines.append("Known limitations:")
    for item in report["known_limitations"]:
        lines.append(f"  - {item}")

    return "\n".join(lines)
