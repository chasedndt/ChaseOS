"""Approval-request packet builder for Workspace Mode profile writes."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .profile_draft_packet import build_workspace_profile_draft_packet


APPROVAL_ROOT = Path("07_LOGS/Agent-Activity/_workspace_mode_profile_write_approvals")


def _detect_vault_root() -> Path:
    here = Path(__file__).resolve()
    vault_root = here.parents[2]
    if not (vault_root / "CLAUDE.md").exists():
        raise RuntimeError(f"could not detect ChaseOS vault root from {here}")
    return vault_root


def _safe_relative(path: Path, vault_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(vault_root.resolve())).replace("\\", "/")
    except (OSError, ValueError):
        return str(path).replace("\\", "/")


def _resolve_inside_vault(path: str | Path, vault_root: Path) -> tuple[Path, bool]:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = vault_root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(vault_root.resolve())
        return resolved, True
    except ValueError:
        return resolved, False


def _approval_digest_material(drafts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "profile_write_request_version": 1,
        "requested_action": "create_missing_workspace_mode_profiles",
        "profiles": [
            {
                "profile_path": draft.get("profile_path"),
                "draft_yaml_sha256": draft.get("draft_yaml_sha256"),
                "recommended_mode": draft.get("recommended_mode"),
            }
            for draft in drafts
        ],
    }


def _approval_packet_id(drafts: list[dict[str, Any]]) -> str:
    material = _approval_digest_material(drafts)
    digest = hashlib.sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()
    return f"wml-profile-write-appr-{digest[:16]}"


def _approval_text(profile_paths: list[str]) -> str:
    lines = [
        "APPROVE WML PROFILE FILE CREATION ONLY:",
        *[f"- {path}" for path in profile_paths],
        "",
        "No AOR dispatch.",
        "No profile overwrite.",
        "No approval consumption beyond the profile-write approval.",
        "No Studio UI or runtime execution.",
    ]
    return "\n".join(lines)


def _approval_artifact_payload(
    *,
    approval_packet_id: str,
    requested_by: str,
    vault_root: Path,
    draft_packet: dict[str, Any],
    profile_paths: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "workspace_mode_profile_write_approval_request.v1",
        "approval_packet_id": approval_packet_id,
        "status": "pending_operator_decision",
        "created_at": datetime.now(UTC).isoformat(),
        "requested_by": requested_by,
        "vault_root": str(vault_root),
        "requested_action": "create_missing_workspace_mode_profiles",
        "approval_scope": {
            "selected_profile_paths": profile_paths,
            "profile_file_creation_only": True,
            "profile_overwrite_allowed": False,
            "aor_dispatch_allowed": False,
            "agent_bus_task_allowed": False,
            "approval_consumption_allowed": False,
            "provider_or_model_call_allowed": False,
            "browser_or_external_action_allowed": False,
            "canonical_write_allowed": False,
        },
        "operator_confirmation_text": _approval_text(profile_paths),
        "draft_packet_scope": draft_packet.get("scope"),
        "draft_count": draft_packet.get("draft_count"),
        "drafts": [
            {
                "profile_path": draft.get("profile_path"),
                "recommended_mode": draft.get("recommended_mode"),
                "draft_yaml_sha256": draft.get("draft_yaml_sha256"),
                "draft_yaml": draft.get("draft_yaml"),
                "validation": draft.get("validation"),
            }
            for draft in draft_packet.get("drafts") or []
        ],
        "future_writer_requirements": [
            "approval packet id must match this request",
            "operator decision must explicitly approve the selected profile paths",
            "writer must revalidate every draft YAML immediately before write",
            "writer must refuse existing profile paths unless a separate overwrite approval exists",
            "writer must write only the approved profile paths",
            "route-preview must be rerun after profile creation before any dispatch work",
        ],
        "authority_flags": {
            "profile_files_written": False,
            "profile_write_performed": False,
            "aor_dispatch_enabled": False,
            "workflow_execution_performed": False,
            "agent_bus_task_written": False,
            "approval_consumed": False,
            "provider_or_model_call_performed": False,
            "browser_or_external_action_performed": False,
            "canonical_write_performed": False,
        },
    }


def build_workspace_profile_write_approval_request(
    *,
    vault_root: str | Path | None = None,
    workspace_path: str | Path | None = None,
    profile_scope: str = "foundation",
    requested_by: str = "operator",
    approval_packet_id: str | None = None,
    write_approval_request: bool = False,
) -> dict[str, Any]:
    """Build or optionally write a pending approval request for WML profile files.

    This never writes workspace-mode profile files and never consumes an approval.
    """

    root = Path(vault_root).resolve() if vault_root is not None else _detect_vault_root()
    draft_packet = build_workspace_profile_draft_packet(
        vault_root=root,
        workspace_path=workspace_path,
        profile_scope=profile_scope,
    )
    drafts = list(draft_packet.get("drafts") or [])
    profile_paths = [str(draft.get("profile_path")) for draft in drafts]
    existing_profile_paths = [
        str(draft.get("profile_path")) for draft in drafts if draft.get("profile_present")
    ]
    validation_ok = bool(draft_packet.get("profile_write_ready_for_operator_review"))
    request_id = approval_packet_id or _approval_packet_id(drafts)
    approval_rel_path = APPROVAL_ROOT / f"{request_id}.json"
    approval_abs_path, approval_path_inside = _resolve_inside_vault(approval_rel_path, root)

    blockers: list[str] = []
    if not drafts:
        blockers.append("no_profile_drafts_available")
    if not validation_ok:
        blockers.append("draft_packet_not_ready_for_operator_review")
    if existing_profile_paths:
        blockers.append("one_or_more_profile_paths_already_exist")
    if not approval_path_inside:
        blockers.append("approval_artifact_path_outside_vault")

    ready_for_operator_decision = not blockers
    artifact_payload = _approval_artifact_payload(
        approval_packet_id=request_id,
        requested_by=requested_by,
        vault_root=root,
        draft_packet=draft_packet,
        profile_paths=profile_paths,
    )

    approval_artifact_written = False
    if write_approval_request:
        if not ready_for_operator_decision:
            blockers.append("approval_request_not_written_until_blockers_clear")
        elif approval_abs_path.exists():
            blockers.append("approval_artifact_already_exists_no_overwrite")
        else:
            approval_abs_path.parent.mkdir(parents=True, exist_ok=True)
            approval_abs_path.write_text(
                json.dumps(artifact_payload, indent=2) + "\n",
                encoding="utf-8",
            )
            approval_artifact_written = True

    return {
        "ok": True,
        "surface": "workspace_mode_profile_write_approval_request",
        "profile_scope": profile_scope,
        "preview_only": not approval_artifact_written,
        "approval_request_surface_only": True,
        "write_approval_request_requested": write_approval_request,
        "approval_request_written": approval_artifact_written,
        "approval_packet_id": request_id,
        "approval_artifact_path": _safe_relative(approval_abs_path, root),
        "approval_artifact_path_in_vault": approval_path_inside,
        "requested_by": requested_by,
        "profile_write_ready_for_operator_review": validation_ok,
        "ready_for_operator_decision": ready_for_operator_decision,
        "selected_profile_paths": profile_paths,
        "existing_profile_paths": existing_profile_paths,
        "operator_confirmation_text": _approval_text(profile_paths),
        "draft_packet": draft_packet,
        "approval_artifact_preview": artifact_payload,
        "profile_files_written": False,
        "profile_write_performed": False,
        "profile_overwrite_performed": False,
        "aor_dispatch_enabled": False,
        "workflow_execution_performed": False,
        "agent_bus_task_written": False,
        "approval_consumed": False,
        "provider_or_model_call_performed": False,
        "browser_or_external_action_performed": False,
        "external_action_performed": False,
        "canonical_write_performed": False,
        "blockers": blockers,
        "next_recommended_pass": (
            "workspace-mode-profile-write-approval-decision-or-guarded-profile-writer"
            if ready_for_operator_decision
            else "workspace-mode-profile-write-approval-request-repair"
        ),
    }


def format_workspace_profile_write_approval_request(payload: dict[str, Any]) -> str:
    lines = [
        "Workspace Mode profile write approval request",
        f"  approval_packet_id: {payload.get('approval_packet_id')}",
        f"  ready_for_decision: {payload.get('ready_for_operator_decision')}",
        f"  request_written:    {payload.get('approval_request_written')}",
        f"  artifact_path:      {payload.get('approval_artifact_path')}",
        f"  blockers:           {', '.join(payload.get('blockers') or []) or '(none)'}",
        "  boundary: approval request only; no profile file write, AOR dispatch, Agent Bus task write, approval consumption, provider/model call, external action, or canonical writeback.",
        "  operator approval text:",
        payload.get("operator_confirmation_text") or "",
    ]
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m runtime.workspace_modes.profile_write_approval_request",
        description="Build or write a pending WML profile-write approval request without profile writes.",
    )
    parser.add_argument("--workspace-path", default=None, metavar="PATH")
    parser.add_argument("--vault-root", default=None, metavar="PATH")
    parser.add_argument("--requested-by", default="operator", metavar="ID")
    parser.add_argument("--approval-packet-id", default=None, metavar="ID")
    parser.add_argument("--write-approval-request", action="store_true")
    parser.add_argument("--json", action="store_true", dest="output_json")
    args = parser.parse_args(argv)

    payload = build_workspace_profile_write_approval_request(
        vault_root=args.vault_root,
        workspace_path=args.workspace_path,
        requested_by=args.requested_by,
        approval_packet_id=args.approval_packet_id,
        write_approval_request=args.write_approval_request,
    )
    if args.output_json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_workspace_profile_write_approval_request(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
