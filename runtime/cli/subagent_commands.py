"""CLI handlers for read-only ChaseOS sub-agent preset surfaces."""

from __future__ import annotations

import argparse
import json
from typing import Any

from runtime.subagents.cli_surfaces import (
    build_subagent_agent_bus_task_packet_preview,
    build_subagent_approval_consumption_decision_binding,
    build_subagent_approval_consumption_dry_run,
    build_subagent_approval_consumption_exact_once_marker_contract,
    build_subagent_approval_packet_preview,
    build_subagent_approval_review_decision,
    build_subagent_approval_request,
    build_subagent_list,
    build_subagent_route_preview,
    build_subagent_show,
    build_subagent_validation,
    format_subagent_agent_bus_task_packet_preview,
    format_subagent_approval_consumption_decision_binding,
    format_subagent_approval_consumption_dry_run,
    format_subagent_approval_consumption_exact_once_marker_contract,
    format_subagent_approval_packet_preview,
    format_subagent_approval_review_decision,
    format_subagent_approval_request,
    format_subagent_list,
    format_subagent_route_preview,
    format_subagent_show,
    format_subagent_validation,
)


def _print(args: argparse.Namespace, payload: dict[str, Any], text: str) -> int:
    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(text)
    return 0 if payload.get("ok") else 1


def cmd_subagents_list(args: argparse.Namespace) -> int:
    payload = build_subagent_list(vault_root=getattr(args, "vault_root", None))
    return _print(args, payload, format_subagent_list(payload))


def cmd_subagents_show(args: argparse.Namespace) -> int:
    payload = build_subagent_show(
        getattr(args, "preset_id"),
        vault_root=getattr(args, "vault_root", None),
    )
    return _print(args, payload, format_subagent_show(payload))


def cmd_subagents_validate(args: argparse.Namespace) -> int:
    payload = build_subagent_validation(vault_root=getattr(args, "vault_root", None))
    return _print(args, payload, format_subagent_validation(payload))


def cmd_subagents_route_preview(args: argparse.Namespace) -> int:
    payload = build_subagent_route_preview(
        getattr(args, "preset_id"),
        mode=getattr(args, "mode", None),
        task_id=getattr(args, "task_id", None) or "subagent-route-preview",
        objective=getattr(args, "objective", None) or "Preview sub-agent routing without dispatch.",
        vault_root=getattr(args, "vault_root", None),
    )
    return _print(args, payload, format_subagent_route_preview(payload))


def cmd_subagents_approval_preview(args: argparse.Namespace) -> int:
    payload = build_subagent_approval_packet_preview(
        getattr(args, "preset_id"),
        mode=getattr(args, "mode", None),
        task_id=getattr(args, "task_id", None) or "subagent-approval-preview",
        objective=(
            getattr(args, "objective", None)
            or "Preview sub-agent activation approval packet without approval or dispatch."
        ),
        requested_by=getattr(args, "requested_by", None) or "operator",
        vault_root=getattr(args, "vault_root", None),
    )
    return _print(args, payload, format_subagent_approval_packet_preview(payload))


def cmd_subagents_write_approval_request(args: argparse.Namespace) -> int:
    payload = build_subagent_approval_request(
        getattr(args, "preset_id"),
        mode=getattr(args, "mode", None),
        task_id=getattr(args, "task_id", None) or "subagent-approval-request",
        objective=(
            getattr(args, "objective", None)
            or "Write a pending sub-agent activation approval request without consuming approval or dispatching."
        ),
        requested_by=getattr(args, "requested_by", None) or "operator",
        expected_work_fingerprint=getattr(args, "expected_work_fingerprint", None),
        write_approval_request=getattr(args, "write_approval_request", False),
        vault_root=getattr(args, "vault_root", None),
    )
    return _print(args, payload, format_subagent_approval_request(payload))


def cmd_subagents_approval_consumption_dry_run(args: argparse.Namespace) -> int:
    payload = build_subagent_approval_consumption_dry_run(
        getattr(args, "approval_artifact_path"),
        expected_work_fingerprint=getattr(args, "expected_work_fingerprint", None),
        vault_root=getattr(args, "vault_root", None),
    )
    return _print(args, payload, format_subagent_approval_consumption_dry_run(payload))


def cmd_subagents_approval_review_decision(args: argparse.Namespace) -> int:
    payload = build_subagent_approval_review_decision(
        getattr(args, "approval_artifact_path"),
        decision=getattr(args, "decision"),
        reviewer_id=getattr(args, "reviewer_id", None) or "operator",
        reason=getattr(args, "reason", None),
        expected_work_fingerprint=getattr(args, "expected_work_fingerprint", None),
        write_approval_decision=getattr(args, "write_approval_decision", False),
        vault_root=getattr(args, "vault_root", None),
    )
    return _print(args, payload, format_subagent_approval_review_decision(payload))


def cmd_subagents_approval_consumption_decision_binding(args: argparse.Namespace) -> int:
    payload = build_subagent_approval_consumption_decision_binding(
        getattr(args, "approval_artifact_path"),
        getattr(args, "decision_artifact_path"),
        expected_work_fingerprint=getattr(args, "expected_work_fingerprint", None),
        vault_root=getattr(args, "vault_root", None),
    )
    return _print(args, payload, format_subagent_approval_consumption_decision_binding(payload))


def cmd_subagents_approval_consumption_exact_once_marker_contract(args: argparse.Namespace) -> int:
    payload = build_subagent_approval_consumption_exact_once_marker_contract(
        getattr(args, "approval_artifact_path"),
        getattr(args, "decision_artifact_path"),
        expected_work_fingerprint=getattr(args, "expected_work_fingerprint", None),
        write_consumption_marker=getattr(args, "write_consumption_marker", False),
        consumed_by=getattr(args, "consumed_by", None) or "operator",
        vault_root=getattr(args, "vault_root", None),
    )
    return _print(
        args,
        payload,
        format_subagent_approval_consumption_exact_once_marker_contract(payload),
    )


def cmd_subagents_agent_bus_task_packet_preview(args: argparse.Namespace) -> int:
    payload = build_subagent_agent_bus_task_packet_preview(
        getattr(args, "approval_artifact_path"),
        getattr(args, "decision_artifact_path"),
        consumption_marker_path=getattr(args, "consumption_marker_path", None),
        expected_work_fingerprint=getattr(args, "expected_work_fingerprint", None),
        sender=getattr(args, "sender", None) or "Operator",
        priority=getattr(args, "priority", None) or "normal",
        vault_root=getattr(args, "vault_root", None),
    )
    return _print(args, payload, format_subagent_agent_bus_task_packet_preview(payload))
