"""No-secret Discord control-plane binding validation for ChaseOS.

The live Discord binding file is machine-local state under
`.chaseos/discord_instance_bindings.yaml`. This module validates structure and
presence without returning real server, account, channel, token, or webhook
values.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SURFACE_ID = "chaseos_discord_binding_validation"
BINDING_PATH = ".chaseos/discord_instance_bindings.yaml"
EXAMPLE_PATH = "runtime/bindings/discord_instance_bindings.example.yaml"
SETUP_SOP_PATH = "04_SOPS/Discord-Control-Plane-Setup-SOP.md"

PRIMARY_CHANNELS = [
    "control_plane_routing",
    "approvals",
    "audit_writeback",
    "runtime_chat_openclaw",
    "alerts_openclaw",
    "debug_openclaw",
    "docs_archive",
]

OPTIONAL_HERMES_CHANNELS = [
    "runtime_chat_hermes",
    "alerts_hermes",
    "debug_hermes",
]


def _load_yaml(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, "file_not_found"
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data, None
        return {}, "yaml_root_not_mapping"
    except Exception as exc:
        try:
            from runtime.lifecycle.health_cli import _parse_simple_yaml

            data = _parse_simple_yaml(text)
            if isinstance(data, dict):
                return data, None
        except Exception:
            pass
        return {}, f"yaml_parse_error:{type(exc).__name__}"


def _is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    upper = text.upper()
    return (
        text.startswith("<")
        and text.endswith(">")
        or "FILL_IN" in upper
        or "YOUR_" in upper
        or upper.startswith("SET_")
    )


def _present(value: Any) -> bool:
    return value is not None and str(value).strip() != "" and not _is_placeholder(value)


def _field_status(container: dict[str, Any], field: str) -> dict[str, Any]:
    value = container.get(field)
    return {
        "field": field,
        "present": _present(value),
        "placeholder": _is_placeholder(value),
        "value_visible": False,
    }


def _line_ignored_by_gitignore(gitignore_text: str, relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/").strip("/")
    parts = normalized.split("/")
    for raw in gitignore_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        line = line.replace("\\", "/")
        folder_rule = line.endswith("/")
        line = line.strip("/")
        if folder_rule:
            folder = line
            if parts and parts[0] == folder:
                return True
        if line.endswith("/*") and parts and parts[0] == line[:-2].strip("/"):
            return True
        if line == normalized or (len(parts) == 1 and line == parts[0]):
            return True
    return False


def _gitignore_status(root: Path) -> dict[str, Any]:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return {"checked": True, "ignored": False, "source": ".gitignore_missing"}
    text = gitignore.read_text(encoding="utf-8", errors="replace")
    return {
        "checked": True,
        "ignored": _line_ignored_by_gitignore(text, BINDING_PATH),
        "source": ".gitignore",
    }


def _secret_like_findings(value: Any, path: str = "$") -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            findings.extend(_secret_like_findings(child, f"{path}.{key}"))
        return findings
    if isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_secret_like_findings(child, f"{path}[{index}]"))
        return findings
    if not isinstance(value, str):
        return findings
    text = value.strip()
    lowered = text.lower()
    reason = None
    if "discord.com/api/webhooks/" in lowered:
        reason = "discord_webhook_url"
    elif "bot " in lowered or lowered.startswith("mfa."):
        reason = "token_like_value"
    elif len(text) > 48 and any(marker in lowered for marker in ("token", "secret", "webhook")):
        reason = "long_token_like_value"
    if reason:
        findings.append({"path": path, "reason": reason, "value_visible": False})
    return findings


def _runtime_status(name: str, data: dict[str, Any]) -> dict[str, Any]:
    required_fields = ["bot_user_id", "application_id", "public_key", "execution_lane_status"]
    fields = [_field_status(data, field) for field in required_fields]
    missing = [item["field"] for item in fields if not item["present"]]
    active = bool(data.get("execution_eligible")) or str(data.get("execution_lane_status") or "").lower() == "live"
    return {
        "runtime": name,
        "configured": not missing,
        "active": active,
        "execution_eligible": bool(data.get("execution_eligible")),
        "approval_authority": bool(data.get("approval_authority")),
        "allowed_adapters": list(data.get("allowed_adapters") or []),
        "field_statuses": fields,
        "missing_fields": missing,
        "values_visible": False,
    }


def _channel_status(name: str, data: dict[str, Any]) -> dict[str, Any]:
    fields = [_field_status(data, "id"), _field_status(data, "name"), _field_status(data, "channel_class")]
    return {
        "name": name,
        "bound": bool(data.get("bound")) and all(item["present"] for item in fields),
        "declared_bound": bool(data.get("bound")),
        "channel_class": data.get("channel_class"),
        "execution_authority": data.get("execution_authority"),
        "interactive_mode": data.get("interactive_mode"),
        "posting_eligible_runtimes": list(data.get("posting_eligible_runtimes") or []),
        "field_statuses": fields,
        "missing_fields": [item["field"] for item in fields if not item["present"]],
        "values_visible": False,
    }


def _studio_capability_map(validation: dict[str, Any]) -> list[dict[str, Any]]:
    summary = validation.get("summary") or {}
    active_runtimes = set(summary.get("active_runtime_ids") or [])
    bound_channels = set(summary.get("bound_channel_names") or [])
    has_schedule_docs = True
    return [
        {
            "id": "quick_open_runtime_chat",
            "label": "Quick open runtime chats",
            "status": "foundation_ready" if bound_channels else "blocked_missing_channel_bindings",
            "uses": [".chaseos/discord_instance_bindings.yaml", "runtime/studio/dashboard.py"],
            "next_implementation": "Add Studio actions that open the bound runtime chat lane without exposing channel IDs.",
            "authority": "navigation_only",
        },
        {
            "id": "create_runtime_threads",
            "label": "Create runtime threads",
            "status": "planned_requires_discord_gateway_or_operator_approval",
            "uses": ["Discord channel bindings", "future thread creation approval packet"],
            "next_implementation": "Gate thread creation behind explicit operator approval and route thread identity back into Agent Bus ingress context.",
            "authority": "approval_required_future_write",
        },
        {
            "id": "send_to_runtime_board",
            "label": "Send to Hermes/OpenClaw/future runtime board",
            "status": "foundation_ready" if active_runtimes else "blocked_no_active_runtime_bindings",
            "uses": ["runtime/agent_bus/", "Studio app launcher support ports", "runtime boards"],
            "next_implementation": "Create a board-routing proposal packet that can target Hermes, OpenClaw, Codex, or future runtime queues without direct mutation.",
            "authority": "proposal_first",
        },
        {
            "id": "manage_cron_tasks",
            "label": "Manage cron/schedule tasks",
            "status": "read_only_foundation_present" if has_schedule_docs else "planned",
            "uses": ["runtime/schedules/", "Studio schedule panel"],
            "next_implementation": "Add schedule intent proposal and approval flows; Studio should show changes immediately after approved writeback.",
            "authority": "approval_required_for_writes",
        },
        {
            "id": "chat_driven_runtime_setup",
            "label": "Chat-driven runtime setup visible in Studio",
            "status": "validator_available",
            "uses": ["setup discord validate", "Studio Discord control-plane panel"],
            "next_implementation": "Let Chat author setup proposal packets that Studio displays before any `.chaseos` or schedule mutation.",
            "authority": "proposal_and_validation_only",
        },
    ]


def build_discord_binding_validation(vault_root: str | Path) -> dict[str, Any]:
    root = Path(vault_root).resolve()
    binding_path = root / BINDING_PATH
    example_path = root / EXAMPLE_PATH
    setup_sop_path = root / SETUP_SOP_PATH
    data, load_error = _load_yaml(binding_path)

    blockers: list[str] = []
    warnings: list[str] = []
    if load_error:
        blockers.append(load_error)

    server = data.get("server") if isinstance(data.get("server"), dict) else {}
    operator = data.get("operator") if isinstance(data.get("operator"), dict) else {}
    runtimes = data.get("runtimes") if isinstance(data.get("runtimes"), dict) else {}
    primary_channels = data.get("primary_channels") if isinstance(data.get("primary_channels"), dict) else {}
    supplemental_channels = (
        data.get("supplemental_channels") if isinstance(data.get("supplemental_channels"), dict) else {}
    )

    server_fields = [_field_status(server, "id"), _field_status(server, "name")]
    operator_fields = [_field_status(operator, "user_id"), _field_status(operator, "display_name")]
    for field in server_fields:
        if not field["present"]:
            blockers.append(f"server.{field['field']}")
    for field in operator_fields:
        if not field["present"]:
            blockers.append(f"operator.{field['field']}")

    runtime_statuses = []
    for runtime_name in sorted(runtimes):
        runtime_data = runtimes.get(runtime_name) if isinstance(runtimes.get(runtime_name), dict) else {}
        status = _runtime_status(runtime_name, runtime_data)
        runtime_statuses.append(status)
        if status["active"] and status["missing_fields"]:
            for field in status["missing_fields"]:
                blockers.append(f"runtimes.{runtime_name}.{field}")

    channel_statuses = []
    for channel_name in sorted(primary_channels):
        channel_data = primary_channels.get(channel_name)
        if isinstance(channel_data, dict):
            channel_statuses.append(_channel_status(channel_name, channel_data))

    required_channels = list(PRIMARY_CHANNELS)
    hermes_status = next((item for item in runtime_statuses if item["runtime"] == "hermes"), None)
    if hermes_status and hermes_status.get("active"):
        required_channels.extend(OPTIONAL_HERMES_CHANNELS)
    for channel_name in required_channels:
        channel = next((item for item in channel_statuses if item["name"] == channel_name), None)
        if not channel:
            blockers.append(f"primary_channels.{channel_name}")
        elif not channel.get("bound"):
            blockers.append(f"primary_channels.{channel_name}.bound")

    secret_findings = _secret_like_findings(data)
    if secret_findings:
        blockers.append("secret_like_values_in_binding_file")

    default_policy = str(data.get("default_unmapped_policy") or "").strip().lower()
    if default_policy != "deny":
        blockers.append("default_unmapped_policy_not_deny")

    gitignore = _gitignore_status(root)
    if not gitignore.get("ignored"):
        blockers.append("binding_file_not_gitignored")

    if not example_path.exists():
        warnings.append("missing_tracked_example_template")
    if not setup_sop_path.exists():
        warnings.append("missing_setup_sop")

    active_runtime_ids = [item["runtime"] for item in runtime_statuses if item.get("active")]
    bound_channel_names = [item["name"] for item in channel_statuses if item.get("bound")]
    unbound_channel_names = [item["name"] for item in channel_statuses if not item.get("bound")]

    payload: dict[str, Any] = {
        "ok": True,
        "surface": SURFACE_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "vault_root": str(root),
        "status": "valid" if not blockers else "blocked",
        "valid": not blockers,
        "binding_file": {
            "path": BINDING_PATH,
            "exists": binding_path.exists(),
            "load_error": load_error,
            "values_visible": False,
            "ids_visible": False,
        },
        "example_template": {
            "path": EXAMPLE_PATH,
            "exists": example_path.exists(),
        },
        "setup_sop": {
            "path": SETUP_SOP_PATH,
            "exists": setup_sop_path.exists(),
        },
        "gitignore": gitignore,
        "server": {
            "field_statuses": server_fields,
            "values_visible": False,
        },
        "operator": {
            "field_statuses": operator_fields,
            "approval_authority": bool(operator.get("approval_authority")),
            "values_visible": False,
        },
        "runtimes": runtime_statuses,
        "primary_channels": channel_statuses,
        "supplemental_channel_count": len(supplemental_channels),
        "default_unmapped_policy": default_policy or None,
        "secret_like_findings": secret_findings,
        "secret_values_visible": False,
        "ids_visible": False,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "summary": {
            "active_runtime_count": len(active_runtime_ids),
            "active_runtime_ids": active_runtime_ids,
            "primary_channel_count": len(channel_statuses),
            "bound_channel_count": len(bound_channel_names),
            "bound_channel_names": bound_channel_names,
            "unbound_channel_names": unbound_channel_names,
            "secret_like_finding_count": len(secret_findings),
            "gitignored": bool(gitignore.get("ignored")),
        },
        "studio_runtime_control_plane": {},
        "authority": {
            "read_only": True,
            "writes_binding_file": False,
            "writes_env_file": False,
            "discord_api_calls_performed": False,
            "webhook_calls_performed": False,
            "agent_bus_task_write_allowed": False,
            "schedule_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "evidence_refs": [
            BINDING_PATH,
            EXAMPLE_PATH,
            SETUP_SOP_PATH,
            "06_AGENTS/ChaseOS-Discord-Control-Plane.md",
            "06_AGENTS/Discord-Identity-Map.md",
            "06_AGENTS/Discord-Channel-Registry.md",
            "runtime/agent_bus/bus.py",
        ],
    }
    payload["studio_runtime_control_plane"] = {
        "headline": "Discord is the current runtime control-plane transport; Studio now has a redacted readiness surface.",
        "capabilities": _studio_capability_map(payload),
        "future_runtime_rule": "New runtimes should declare Discord/chat/board/schedule lanes through the same binding and validation pattern before Studio exposes controls.",
    }
    return payload


def format_discord_binding_validation(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "ChaseOS Discord Binding Validation",
        f"  status: {payload.get('status')}",
        f"  valid: {payload.get('valid')}",
        f"  binding_file: {BINDING_PATH} exists={bool((payload.get('binding_file') or {}).get('exists'))}",
        f"  gitignored: {bool(summary.get('gitignored'))}",
        f"  active_runtimes: {', '.join(summary.get('active_runtime_ids') or []) or 'none'}",
        f"  bound_channels: {summary.get('bound_channel_count', 0)} / {summary.get('primary_channel_count', 0)}",
        f"  ids_visible: {payload.get('ids_visible')}",
        f"  secret_values_visible: {payload.get('secret_values_visible')}",
    ]
    if payload.get("blockers"):
        lines.append("  blockers:")
        for blocker in payload["blockers"]:
            lines.append(f"    - {blocker}")
    if payload.get("warnings"):
        lines.append("  warnings:")
        for warning in payload["warnings"]:
            lines.append(f"    - {warning}")
    lines.append("  next:")
    if payload.get("valid"):
        lines.append("    - Use this read-only status in Studio; future write actions still need approval packets.")
    else:
        lines.append(f"    - Copy {EXAMPLE_PATH} to {BINDING_PATH} and fill local IDs, or repair listed blockers.")
    return "\n".join(lines)
