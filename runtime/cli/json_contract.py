"""Shared JSON output contract for the canonical ChaseOS CLI."""

from __future__ import annotations

import argparse
import json
from typing import Any


JSON_CONTRACT_KEYS = ("ok", "action", "result", "errors", "warnings", "audit_id")

_ACTION_ATTRS = (
    "command",
    "runtime_command",
    "runtime_subcommand",
    "runtime_target",
    "setup_mode",
    "setup_command",
    "capture_mode",
    "markdown_mode",
    "intake_mode",
    "browser_mode",
    "watch_mode",
    "schedule_mode",
    "events_mode",
    "osril_mode",
    "providers_mode",
    "models_mode",
    "config_mode",
    "scaffold_mode",
    "scaffold_type",
    "agent_mode",
    "agent_bus_mode",
    "agent_bus_task_mode",
    "agent_bus_ingress_mode",
    "operate_mode",
    "operate_surface",
    "operate_browser_cmd",
    "browser_command",
    "context_mode",
    "develop_mode",
    "gate_mode",
    "core_export_mode",
    "doctor_target",
    "maintain_mode",
    "memory_mode",
    "n8n_cmd",
    "mvp_mode",
    "audit_mode",
    "scorecard_mode",
    "sbp_mode",
    "studio_mode",
    "ventureops_mode",
    "pulse_target",
    "creator_mode",
    "subagents_mode",
    "siteops_mode",
    "siteops_candidates_mode",
    "siteops_catalog_mode",
    "siteops_tenants_mode",
    "siteops_skills_mode",
    "siteops_workflows_mode",
    "siteops_runs_mode",
    "siteops_approvals_mode",
    "siteops_credentials_mode",
    "siteops_browser_profiles_mode",
    "siteops_budgets_mode",
    "acquisition_mode",
    "aiso_mode",
    "test_target",
)


def build_action(args: argparse.Namespace) -> str:
    """Build a stable dotted action name from argparse command fields."""
    parts: list[str] = []
    for attr in _ACTION_ATTRS:
        if (
            attr == "runtime_subcommand"
            and getattr(args, "command", None) == "runtime"
            and getattr(args, "runtime_command", None) == "workspace-mode"
        ):
            continue
        value = getattr(args, attr, None)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            parts.append(text)
    return ".".join(parts) if parts else "unknown"


def _coerce_messages(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return [value] if value else []
    if isinstance(value, str):
        return [value] if value else []
    return [value]


def _extract_errors(payload: Any, *, ok: bool) -> list[Any]:
    if isinstance(payload, dict):
        errors = _coerce_messages(payload.get("errors"))
        if errors:
            return errors
        if not ok:
            for key in ("error", "reason", "message"):
                value = payload.get(key)
                if value:
                    return _coerce_messages(value)
    return [] if ok else ["Command failed."]


def _extract_warnings(payload: Any) -> list[Any]:
    if isinstance(payload, dict):
        return _coerce_messages(payload.get("warnings"))
    return []


def _extract_audit_id(payload: Any) -> str | None:
    if isinstance(payload, dict):
        value = payload.get("audit_id")
        if value:
            return str(value)
        result = payload.get("result")
        if isinstance(result, dict) and result.get("audit_id"):
            return str(result["audit_id"])
    return None


def is_json_contract_payload(payload: Any) -> bool:
    return isinstance(payload, dict) and all(key in payload for key in JSON_CONTRACT_KEYS)


def envelope_json_payload(
    payload: Any,
    *,
    action: str,
    exit_code: int,
    warnings: list[Any] | None = None,
) -> dict[str, Any]:
    """Wrap a native command payload in the ChaseOS CLI JSON envelope."""
    if is_json_contract_payload(payload):
        return payload

    ok = exit_code == 0
    extracted_warnings = _extract_warnings(payload)
    if warnings:
        extracted_warnings.extend(warnings)

    return {
        "ok": ok,
        "action": action,
        "result": payload,
        "errors": _extract_errors(payload, ok=ok),
        "warnings": extracted_warnings,
        "audit_id": _extract_audit_id(payload),
    }


def envelope_raw_stdout(raw_stdout: str, *, action: str, exit_code: int) -> dict[str, Any]:
    """Parse command stdout if possible, then return a contract envelope."""
    text = raw_stdout.strip()
    if not text:
        return envelope_json_payload(None, action=action, exit_code=exit_code)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return envelope_json_payload(
            {"stdout": raw_stdout},
            action=action,
            exit_code=exit_code,
            warnings=["Command emitted non-JSON stdout while --json was requested."],
        )
    return envelope_json_payload(payload, action=action, exit_code=exit_code)
