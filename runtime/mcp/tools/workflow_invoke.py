"""Bounded workflow invocation tool for Runtime MCP V2.

This module is the only MCP tool allowed to route into AOR. It does not call
workflow handlers directly and does not spawn subprocesses.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from runtime.aor.engine import run_workflow
from runtime.context.boot import load_boot_context
from runtime.mcp.config import MCPConfig
from runtime.mcp.errors import (
    ERR_AOR_INVOCATION_FAILED,
    ERR_BAD_REQUEST,
    ERR_GATE_POLICY_DENIED,
    ERR_ROLE_CARD_NOT_FOUND,
    ERR_WORKFLOW_INPUTS_INVALID,
    ERR_WORKFLOW_MANIFEST_NOT_FOUND,
    ERR_WORKFLOW_NOT_ACTIVE,
    ERR_WORKFLOW_NOT_ALLOWED,
    ERR_WORKFLOW_OUTPUT_ALREADY_EXISTS,
    ERR_WORKFLOW_PERMISSION_CEILING_EXCEEDED,
    ERR_WORKFLOW_WRITEBACK_SCOPE_DENIED,
    domain_error,
    input_error,
    system_error,
)
from runtime.mcp.types import HandlerResult, PermissionEnvelope
from runtime.mcp.yaml_compat import safe_load
from runtime.chaseos_gate import check_runtime_operation


WORKFLOW_ALLOWLIST_VERSION = "2026-04-21-pass6b-v1"
ALLOWED_WORKFLOWS = {"operator_today", "operator_close_day"}
EXPECTED_TASK_TYPE = "operator-briefing"
EXPECTED_ROLE_CARD = "operator-briefing"
EXPECTED_PERMISSION_CEILING = "no_protected_file_writes"
EXPECTED_WRITEBACK_TARGET = "07_LOGS/Operator-Briefs/"
ALLOWED_ROLE_WRITE_SCOPES = {"07_LOGS/Operator-Briefs/", "07_LOGS/Agent-Activity/"}

ALLOWED_INPUT_KEYS = {
    "operator_today": {"date", "output_format"},
    "operator_close_day": {"date", "open_loops", "notes"},
}

ALLOWED_PARAM_KEYS = {"workflow_id", "inputs", "dry_run"}
DENIED_CONTROL_KEYS = {
    "approval",
    "approval_id",
    "approved",
    "apply",
    "browser",
    "command",
    "commit",
    "function",
    "git",
    "handler",
    "handler_name",
    "module",
    "module_name",
    "network",
    "path",
    "python_path",
    "schedule",
    "schedule_id",
    "shell",
    "subprocess",
    "target_path",
    "write_path",
}

RETRY_GUIDANCE = (
    "If completion status is ambiguous, do not retry blindly; reconcile the MCP audit, "
    "AOR audit, and output_artifacts first."
)


def _norm_path(value: Any) -> str:
    return str(value).strip().replace("\\", "/").rstrip("/") + "/"


def _vault_relative(path: Path, vault_root: Path) -> str:
    return str(path.relative_to(vault_root)).replace("\\", "/")


def _load_yaml_mapping(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    raw = safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return {}
    return raw


def _redacted_inputs_summary(inputs: dict[str, Any]) -> dict[str, str]:
    summary: dict[str, str] = {}
    for key, value in inputs.items():
        if isinstance(value, str):
            summary[key] = value[:80]
        elif isinstance(value, list):
            summary[key] = f"list[{len(value)}]"
        elif isinstance(value, dict):
            summary[key] = "mapping"
        else:
            summary[key] = type(value).__name__
    return summary


def _base_audit_metadata(
    workflow_id: str | None,
    inputs: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    return {
        "tool": "workflow.invoke_bounded",
        "workflow_id": workflow_id,
        "workflow_allowlist_version": WORKFLOW_ALLOWLIST_VERSION,
        "inputs_summary": _redacted_inputs_summary(inputs or {}),
        "dry_run": dry_run,
        "aor_invoked": False,
    }


def _deny(
    code: str,
    message: str,
    workflow_id: str | None,
    *,
    inputs: dict[str, Any] | None = None,
    dry_run: bool = False,
    **details: Any,
) -> HandlerResult:
    return HandlerResult(
        False,
        error=domain_error(code, message, **details),
        audit_metadata=_base_audit_metadata(workflow_id, inputs, dry_run),
    )


def _validate_request_shape(params: dict[str, Any]) -> tuple[str | None, dict[str, Any], bool, HandlerResult | None]:
    unknown_params = sorted(set(params) - ALLOWED_PARAM_KEYS)
    denied_params = sorted(set(params) & DENIED_CONTROL_KEYS)
    if unknown_params or denied_params:
        return (
            None,
            {},
            False,
            HandlerResult(
                False,
                error=input_error(
                    ERR_WORKFLOW_INPUTS_INVALID,
                    "workflow.invoke_bounded accepts only workflow_id, inputs, and dry_run.",
                    unknown_params=unknown_params,
                    denied_params=denied_params,
                ),
                audit_metadata=_base_audit_metadata(None),
            ),
        )

    workflow_id = params.get("workflow_id")
    if not isinstance(workflow_id, str) or not workflow_id.strip():
        return (
            None,
            {},
            False,
            HandlerResult(
                False,
                error=input_error(ERR_BAD_REQUEST, "workflow_id is required."),
                audit_metadata=_base_audit_metadata(None),
            ),
        )
    workflow_id = workflow_id.strip()

    inputs = params.get("inputs", {})
    if inputs is None:
        inputs = {}
    if not isinstance(inputs, dict):
        return (
            workflow_id,
            {},
            False,
            HandlerResult(
                False,
                error=input_error(ERR_WORKFLOW_INPUTS_INVALID, "inputs must be a mapping when provided."),
                audit_metadata=_base_audit_metadata(workflow_id),
            ),
        )

    dry_run = params.get("dry_run", False)
    if not isinstance(dry_run, bool):
        return (
            workflow_id,
            inputs,
            False,
            HandlerResult(
                False,
                error=input_error(ERR_WORKFLOW_INPUTS_INVALID, "dry_run must be a boolean when provided."),
                audit_metadata=_base_audit_metadata(workflow_id, inputs),
            ),
        )

    denied_input_keys = sorted(set(inputs) & DENIED_CONTROL_KEYS)
    if denied_input_keys:
        return (
            workflow_id,
            inputs,
            dry_run,
            HandlerResult(
                False,
                error=input_error(
                    ERR_WORKFLOW_INPUTS_INVALID,
                    "inputs contain denied control keys.",
                    denied_input_keys=denied_input_keys,
                ),
                audit_metadata=_base_audit_metadata(workflow_id, inputs, dry_run),
            ),
        )

    return workflow_id, inputs, dry_run, None


def _preflight_manifest(
    config: MCPConfig,
    workflow_id: str,
    inputs: dict[str, Any],
    dry_run: bool,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str], HandlerResult | None]:
    metadata = _base_audit_metadata(workflow_id, inputs, dry_run)
    files_read: list[str] = []

    if workflow_id not in ALLOWED_WORKFLOWS:
        return (
            None,
            None,
            files_read,
            _deny(
                ERR_WORKFLOW_NOT_ALLOWED,
                "workflow.invoke_bounded may only invoke the first-release allowlist.",
                workflow_id,
                inputs=inputs,
                dry_run=dry_run,
                allowed_workflow_ids=sorted(ALLOWED_WORKFLOWS),
            ),
        )

    allowed_input_keys = ALLOWED_INPUT_KEYS[workflow_id]
    unknown_inputs = sorted(set(inputs) - allowed_input_keys)
    if unknown_inputs:
        return (
            None,
            None,
            files_read,
            HandlerResult(
                False,
                error=input_error(
                    ERR_WORKFLOW_INPUTS_INVALID,
                    "inputs contain keys not allowed for this workflow.",
                    workflow_id=workflow_id,
                    allowed_input_keys=sorted(allowed_input_keys),
                    unknown_input_keys=unknown_inputs,
                ),
                audit_metadata=metadata,
            ),
        )

    manifest_path = config.vault_root / "runtime" / "workflows" / "registry" / f"{workflow_id}.yaml"
    manifest = _load_yaml_mapping(manifest_path)
    if manifest is None:
        return (
            None,
            None,
            files_read,
            _deny(
                ERR_WORKFLOW_MANIFEST_NOT_FOUND,
                "Requested workflow manifest could not be found.",
                workflow_id,
                inputs=inputs,
                dry_run=dry_run,
                manifest=str(manifest_path.relative_to(config.vault_root)).replace("\\", "/"),
            ),
        )
    files_read.append(_vault_relative(manifest_path, config.vault_root))

    metadata.update(
        {
            "manifest_status": manifest.get("status"),
            "task_type": manifest.get("task_type"),
            "role_card_id": manifest.get("role_card"),
            "permission_ceiling": manifest.get("permission_ceiling"),
        }
    )

    if manifest.get("status") != "active":
        return (
            manifest,
            None,
            files_read,
            HandlerResult(
                False,
                error=domain_error(
                    ERR_WORKFLOW_NOT_ACTIVE,
                    "Workflow manifest must be status: active.",
                    workflow_id=workflow_id,
                    manifest_status=manifest.get("status"),
                ),
                files_read=files_read,
                audit_metadata=metadata,
            ),
        )
    if manifest.get("task_type") != EXPECTED_TASK_TYPE:
        return (
            manifest,
            None,
            files_read,
            HandlerResult(
                False,
                error=domain_error(
                    ERR_WORKFLOW_NOT_ALLOWED,
                    "Workflow task_type is outside the first-release invocation class.",
                    workflow_id=workflow_id,
                    task_type=manifest.get("task_type"),
                ),
                files_read=files_read,
                audit_metadata=metadata,
            ),
        )
    if manifest.get("role_card") != EXPECTED_ROLE_CARD:
        return (
            manifest,
            None,
            files_read,
            HandlerResult(
                False,
                error=domain_error(
                    ERR_WORKFLOW_NOT_ALLOWED,
                    "Workflow role_card is outside the first-release invocation class.",
                    workflow_id=workflow_id,
                    role_card=manifest.get("role_card"),
                ),
                files_read=files_read,
                audit_metadata=metadata,
            ),
        )

    role_card_path = config.vault_root / "06_AGENTS" / "role-cards" / f"{EXPECTED_ROLE_CARD}.yaml"
    role_card = _load_yaml_mapping(role_card_path)
    if role_card is None:
        return (
            manifest,
            None,
            files_read,
            HandlerResult(
                False,
                error=domain_error(
                    ERR_ROLE_CARD_NOT_FOUND,
                    "Required role card could not be found.",
                    role_card=EXPECTED_ROLE_CARD,
                ),
                files_read=files_read,
                audit_metadata=metadata,
            ),
        )
    files_read.append(_vault_relative(role_card_path, config.vault_root))

    if manifest.get("permission_ceiling") != EXPECTED_PERMISSION_CEILING:
        return (
            manifest,
            role_card,
            files_read,
            HandlerResult(
                False,
                error=domain_error(
                    ERR_WORKFLOW_PERMISSION_CEILING_EXCEEDED,
                    "Workflow permission ceiling is outside MCP invocation bounds.",
                    workflow_id=workflow_id,
                    permission_ceiling=manifest.get("permission_ceiling"),
                    required_permission_ceiling=EXPECTED_PERMISSION_CEILING,
                ),
                files_read=files_read,
                audit_metadata=metadata,
            ),
        )

    writeback_targets = [_norm_path(target) for target in (manifest.get("writeback_targets") or [])]
    if writeback_targets != [EXPECTED_WRITEBACK_TARGET]:
        return (
            manifest,
            role_card,
            files_read,
            HandlerResult(
                False,
                error=domain_error(
                    ERR_WORKFLOW_WRITEBACK_SCOPE_DENIED,
                    "Workflow writeback target exceeds the draft/log-safe scope.",
                    workflow_id=workflow_id,
                    writeback_targets=writeback_targets,
                    required_writeback_targets=[EXPECTED_WRITEBACK_TARGET],
                ),
                files_read=files_read,
                audit_metadata=metadata,
            ),
        )

    role_write_scopes = {_norm_path(scope) for scope in (role_card.get("write_scope") or [])}
    if EXPECTED_WRITEBACK_TARGET not in role_write_scopes or not role_write_scopes.issubset(ALLOWED_ROLE_WRITE_SCOPES):
        return (
            manifest,
            role_card,
            files_read,
            HandlerResult(
                False,
                error=domain_error(
                    ERR_WORKFLOW_WRITEBACK_SCOPE_DENIED,
                    "Role card write scope exceeds the draft/log-safe scope.",
                    workflow_id=workflow_id,
                    role_write_scope=sorted(role_write_scopes),
                    allowed_role_write_scopes=sorted(ALLOWED_ROLE_WRITE_SCOPES),
                ),
                files_read=files_read,
                audit_metadata=metadata,
            ),
        )

    metadata["preflight"] = "passed"
    return manifest, role_card, files_read, None


def _extract_files_written(outputs: dict[str, Any]) -> list[str]:
    writeback = outputs.get("writeback")
    if not isinstance(writeback, dict):
        return []
    files = writeback.get("files_written") or []
    if not isinstance(files, list):
        return []
    return [str(path).replace("\\", "/") for path in files]


def _output_artifacts(files_written: list[str]) -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    for path in files_written:
        artifact_type = "operator_brief" if path.startswith(EXPECTED_WRITEBACK_TARGET) else "workflow_output"
        artifacts.append({"artifact_type": artifact_type, "path": path})
    return artifacts


def _gate_write_targets() -> list[str]:
    return [EXPECTED_WRITEBACK_TARGET, "07_LOGS/Agent-Activity/"]


def _resolve_invocation_date(inputs: dict[str, Any]) -> str | None:
    raw_value = inputs.get("date")
    if raw_value in (None, ""):
        return date.today().isoformat()
    if not isinstance(raw_value, str):
        return None
    try:
        return date.fromisoformat(raw_value.strip()).isoformat()
    except ValueError:
        return None


def _expected_output_paths(workflow_id: str, inputs: dict[str, Any]) -> list[str]:
    invocation_date = _resolve_invocation_date(inputs)
    if invocation_date is None:
        return []

    if workflow_id == "operator_today":
        output_format = str(inputs.get("output_format") or "markdown").strip().lower()
        if output_format not in {"markdown", "json"}:
            return []
        extension = "json" if output_format == "json" else "md"
        return [f"07_LOGS/Operator-Briefs/{invocation_date}-operator-today.{extension}"]

    if workflow_id == "operator_close_day":
        return [f"07_LOGS/Operator-Briefs/{invocation_date}-operator-close-day.md"]

    return []


def workflow_invoke_bounded(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    workflow_id, inputs, dry_run, request_error = _validate_request_shape(params)
    if request_error is not None:
        return request_error

    assert workflow_id is not None
    manifest, role_card, files_read, preflight_error = _preflight_manifest(
        config,
        workflow_id,
        inputs,
        dry_run,
    )
    if preflight_error is not None:
        if preflight_error.files_read:
            return preflight_error
        preflight_error.files_read = files_read
        return preflight_error

    if not dry_run:
        expected_output_paths = _expected_output_paths(workflow_id, inputs)
        existing_output_paths = [
            relative_path
            for relative_path in expected_output_paths
            if (config.vault_root / Path(relative_path)).exists()
        ]
        if existing_output_paths:
            audit_metadata = _base_audit_metadata(workflow_id, inputs, dry_run)
            audit_metadata.update(
                {
                    "manifest_status": manifest.get("status") if manifest else None,
                    "task_type": manifest.get("task_type") if manifest else None,
                    "role_card_id": role_card.get("id") if role_card else EXPECTED_ROLE_CARD,
                    "permission_ceiling": manifest.get("permission_ceiling") if manifest else None,
                    "preflight": "passed",
                    "duplicate_guard": "blocked_existing_output",
                    "expected_output_paths": expected_output_paths,
                    "existing_output_paths": existing_output_paths,
                    "retry_guidance": RETRY_GUIDANCE,
                }
            )
            return HandlerResult(
                False,
                error=domain_error(
                    ERR_WORKFLOW_OUTPUT_ALREADY_EXISTS,
                    "Predicted workflow output artifact already exists; live invocation was not started.",
                    workflow_id=workflow_id,
                    existing_artifacts=existing_output_paths,
                    retry_guidance=RETRY_GUIDANCE,
                ),
                audit_metadata=audit_metadata,
                files_read=files_read,
            )

    allowed, gate_reason = check_runtime_operation(
        "gateway.workflow.invoke_bounded",
        actor_adapter_id=envelope.runtime_id or "openclaw",
        task_type=str(manifest.get("task_type") if manifest else EXPECTED_TASK_TYPE),
        write_targets=_gate_write_targets(),
    )
    if not allowed:
        audit_metadata = _base_audit_metadata(workflow_id, inputs, dry_run)
        audit_metadata.update(
            {
                "manifest_status": manifest.get("status") if manifest else None,
                "task_type": manifest.get("task_type") if manifest else None,
                "role_card_id": role_card.get("id") if role_card else EXPECTED_ROLE_CARD,
                "permission_ceiling": manifest.get("permission_ceiling") if manifest else None,
                "preflight": "passed",
                "gate_operation": "gateway.workflow.invoke_bounded",
                "gate_policy": "denied",
                "gate_reason": gate_reason,
                "aor_invoked": False,
            }
        )
        return HandlerResult(
            False,
            error=domain_error(
                ERR_GATE_POLICY_DENIED,
                "Gate policy denied workflow.invoke_bounded before AOR invocation.",
                workflow_id=workflow_id,
                operation="gateway.workflow.invoke_bounded",
                reason=gate_reason,
            ),
            audit_metadata=audit_metadata,
            files_read=files_read,
        )

    audit_metadata = _base_audit_metadata(workflow_id, inputs, dry_run)
    audit_metadata.update(
        {
            "manifest_status": manifest.get("status") if manifest else None,
            "task_type": manifest.get("task_type") if manifest else None,
            "role_card_id": role_card.get("id") if role_card else EXPECTED_ROLE_CARD,
            "permission_ceiling": manifest.get("permission_ceiling") if manifest else None,
            "preflight": "passed",
            "aor_invoked": True,
        }
    )

    try:
        aor_result = run_workflow(
            workflow_id=workflow_id,
            inputs=inputs,
            vault_root=config.vault_root,
            dry_run=dry_run,
            runtime_id=envelope.runtime_id or "openclaw",
        )
    except Exception as exc:  # noqa: BLE001
        audit_metadata.update({"aor_status": "failed", "aor_error": str(exc)})
        return HandlerResult(
            False,
            error=system_error(ERR_AOR_INVOCATION_FAILED, str(exc), workflow_id=workflow_id),
            audit_metadata=audit_metadata,
            files_read=files_read,
        )

    aor_status = str(getattr(aor_result, "status", "unknown"))
    aor_audit_id = str(getattr(aor_result, "audit_id", ""))
    stage_reached = str(getattr(aor_result, "stage_reached", ""))
    outputs = getattr(aor_result, "outputs", {}) or {}
    if not isinstance(outputs, dict):
        outputs = {}

    files_written = _extract_files_written(outputs)
    audit_metadata.update(
        {
            "aor_status": aor_status,
            "aor_audit_id": aor_audit_id,
            "aor_stage_reached": stage_reached,
            "files_written": files_written,
        }
    )

    if aor_status not in {"success", "dry_run_ok"}:
        reason = getattr(aor_result, "escalation_reason", None) or getattr(aor_result, "error", None)
        return HandlerResult(
            False,
            error=system_error(
                ERR_AOR_INVOCATION_FAILED,
                str(reason or f"AOR returned status {aor_status!r}"),
                workflow_id=workflow_id,
                aor_status=aor_status,
                stage_reached=stage_reached,
                aor_audit_id=aor_audit_id,
            ),
            audit_metadata=audit_metadata,
            files_read=files_read,
            files_written=files_written,
        )

    # Load the boot frame and inject it into the response so the calling LLM
    # always sees the current ChaseOS context after a workflow invocation,
    # regardless of whether it called context.boot_frame explicitly.
    _boot_frame_text = ""
    try:
        _boot = load_boot_context(
            vault_root=config.vault_root,
            runtime_id=envelope.runtime_id or "openclaw",
        )
        _boot_frame_text = _boot.to_frame()
    except Exception:  # noqa: BLE001
        _boot_frame_text = "## ChaseOS Context Boot\n- Boot status: UNAVAILABLE"

    invocation_status = "dry_run_ok" if aor_status == "dry_run_ok" else "completed"
    payload = {
        "workflow_id": workflow_id,
        "invocation_status": invocation_status,
        "aor_status": aor_status,
        "aor_audit_id": aor_audit_id,
        "stage_reached": stage_reached,
        "dry_run": dry_run,
        "output_artifacts": _output_artifacts(files_written),
        "files_written": files_written,
        "canonical_write": False,
        "audit_reconciliation": {
            "aor_audit_id": aor_audit_id,
            "aor_audit_dir": "07_LOGS/Agent-Activity/",
            "mcp_audit_surface": "workflow.invoke_bounded",
            "mcp_audit_dir": "07_LOGS/Agent-Activity/",
        },
        "context_boot_frame": _boot_frame_text,
        "retry_guidance": RETRY_GUIDANCE,
    }

    audit_metadata["response_summary"] = json.dumps(payload, sort_keys=True)
    return HandlerResult(
        True,
        payload,
        audit_metadata=audit_metadata,
        files_read=files_read,
        files_written=files_written,
    )
