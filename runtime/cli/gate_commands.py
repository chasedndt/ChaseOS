"""Gate command handlers for the canonical ChaseOS CLI.

Parser registration remains in ``runtime.cli.main``. This module owns the Gate
command implementations so the canonical entrypoint can stay authoritative
without concentrating every command family's logic in one file.
"""

from __future__ import annotations

import argparse
import json
import sys

from runtime.chaseos_gate import (
    check_control_plane_transport,
    check_coordination_path,
    check_credential_reference,
    check_external_api,
    check_runtime_operation,
    check_task_type,
    check_write_permission,
    get_runtime_operation_approval_schema,
    load_gateway_allowlists,
    load_adapter_manifest,
    load_all_manifests,
    validate_all_manifests,
)


def cmd_gate_validate(args: argparse.Namespace) -> int:
    errors = validate_all_manifests()
    if getattr(args, "output_json", False):
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
        return 0 if not errors else 1
    if not errors:
        print("All adapter manifests are valid.")
        return 0
    for adapter_id, adapter_errors in errors.items():
        print(f"\n{adapter_id}:")
        for error in adapter_errors:
            print(f"  - {error}")
    return 1


def cmd_gate_list_adapters(args: argparse.Namespace) -> int:
    manifests = load_all_manifests()
    if getattr(args, "output_json", False):
        payload = [
            {
                "adapter_id": adapter_id,
                "adapter_name": manifest.get("adapter_name", adapter_id),
                "status": manifest.get("status", "unknown"),
                "surface": manifest.get("surface"),
            }
            for adapter_id, manifest in sorted(manifests.items())
        ]
        print(json.dumps(payload, indent=2))
        return 0
    if not manifests:
        print("No adapter manifests found in runtime/policy/adapters/")
        return 1
    for adapter_id, manifest in sorted(manifests.items()):
        status = manifest.get("status", "unknown")
        name = manifest.get("adapter_name", adapter_id)
        print(f"{adapter_id:20s} [{status:8s}] {name}")
    return 0


def cmd_gate_show_adapter(args: argparse.Namespace) -> int:
    manifest = load_adapter_manifest(args.adapter_id)
    if not manifest:
        print(f"ERROR: adapter '{args.adapter_id}' not found", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2))
    return 0


def cmd_gate_show_allowlists(args: argparse.Namespace) -> int:
    payload = load_gateway_allowlists()
    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2))
        return 0 if payload else 1

    if not payload:
        print("Gateway allowlists are missing or invalid.", file=sys.stderr)
        return 1
    print("ChaseOS Gateway Allowlists")
    print(f"  version: {payload.get('version')}")
    for key in [
        "write_targets",
        "task_types",
        "external_apis",
        "control_plane_transports",
        "credential_references",
    ]:
        value = payload.get(key)
        if isinstance(value, dict):
            print(f"  {key}: {len(value)}")
        elif isinstance(value, list):
            print(f"  {key}: {len(value)}")
    return 0


def cmd_gate_check_write(args: argparse.Namespace) -> int:
    allowed, reason = check_write_permission(args.adapter_id, args.path)
    if getattr(args, "output_json", False):
        print(json.dumps({"allowed": allowed, "reason": reason}, indent=2))
    else:
        print(f"Write permission: {'ALLOWED' if allowed else 'BLOCKED'}")
        print(f"Reason: {reason}")
    return 0 if allowed else 1


def cmd_gate_check_task(args: argparse.Namespace) -> int:
    allowed, reason = check_task_type(args.adapter_id, args.task_type)
    if getattr(args, "output_json", False):
        print(json.dumps({"allowed": allowed, "reason": reason}, indent=2))
    else:
        print(f"Task allowed: {'YES' if allowed else 'NO'}")
        print(f"Reason: {reason}")
    return 0 if allowed else 1


def cmd_gate_check_coordination(args: argparse.Namespace) -> int:
    via_bus = args.via == "runtime/agent_bus/"
    allowed, reason = check_coordination_path(
        args.adapter_id,
        coordination_sensitive=args.coordination_sensitive,
        via_bus=via_bus,
        target_runtime=args.target_runtime,
    )
    if getattr(args, "output_json", False):
        print(
            json.dumps(
                {
                    "allowed": allowed,
                    "reason": reason,
                    "via": args.via,
                    "target_runtime": args.target_runtime,
                },
                indent=2,
            )
        )
    else:
        print(f"Coordination path: {'ALLOWED' if allowed else 'BLOCKED'}")
        print(f"Reason: {reason}")
    return 0 if allowed else 1


def cmd_gate_check_external_api(args: argparse.Namespace) -> int:
    allowed, reason = check_external_api(args.api_id)
    if getattr(args, "output_json", False):
        print(json.dumps({"allowed": allowed, "api_id": args.api_id, "reason": reason}, indent=2))
    else:
        print(f"External API: {'ALLOWED' if allowed else 'BLOCKED'}")
        print(f"Reason: {reason}")
    return 0 if allowed else 1


def cmd_gate_check_transport(args: argparse.Namespace) -> int:
    allowed, reason = check_control_plane_transport(args.transport)
    if getattr(args, "output_json", False):
        print(json.dumps({"allowed": allowed, "transport": args.transport, "reason": reason}, indent=2))
    else:
        print(f"Control-plane transport: {'ALLOWED' if allowed else 'BLOCKED'}")
        print(f"Reason: {reason}")
    return 0 if allowed else 1


def cmd_gate_check_credential_reference(args: argparse.Namespace) -> int:
    allowed, reason = check_credential_reference(args.kind, args.target)
    if getattr(args, "output_json", False):
        print(
            json.dumps(
                {"allowed": allowed, "kind": args.kind, "target": args.target, "reason": reason},
                indent=2,
            )
        )
    else:
        print(f"Credential reference: {'ALLOWED' if allowed else 'BLOCKED'}")
        print(f"Reason: {reason}")
    return 0 if allowed else 1


def cmd_gate_check_operation(args: argparse.Namespace) -> int:
    via_bus = args.via == "runtime/agent_bus/" if getattr(args, "via", None) else None
    approval_schema = get_runtime_operation_approval_schema(
        args.operation,
        external_api=getattr(args, "external_api", None),
        source_command="chaseos gate check-operation",
    )
    allowed, reason = check_runtime_operation(
        args.operation,
        actor_adapter_id=getattr(args, "actor_adapter", None),
        target_runtime=getattr(args, "target_runtime", None),
        task_type=getattr(args, "task_type", None),
        write_targets=getattr(args, "write_target", None),
        coordination_sensitive=getattr(args, "coordination_sensitive", None),
        via_bus=via_bus,
        external_api=getattr(args, "external_api", None),
        external_side_effect=getattr(args, "external_side_effect", False),
        control_plane_transport=getattr(args, "control_plane_transport", None),
    )
    if getattr(args, "output_json", False):
        print(
            json.dumps(
                {
                    "allowed": allowed,
                    "operation": args.operation,
                    "reason": reason,
                    "actor_adapter": getattr(args, "actor_adapter", None),
                    "target_runtime": getattr(args, "target_runtime", None),
                    "external_api": getattr(args, "external_api", None),
                    "control_plane_transport": getattr(args, "control_plane_transport", None),
                    "approval_schema": approval_schema,
                },
                indent=2,
            )
        )
    else:
        print(f"Runtime operation: {'ALLOWED' if allowed else 'BLOCKED'}")
        print(f"Reason: {reason}")
        if approval_schema:
            print(f"Approval schema: {approval_schema.get('approval_schema_id')}")
    return 0 if allowed else 1
