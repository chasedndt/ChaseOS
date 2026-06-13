"""Guarded create-only writer for approved Workspace Mode profiles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .loader import load_workspace_profile, load_workspace_profile_from_mapping, parse_profile_text
from .profile_draft_packet import build_workspace_profile_draft_packet
from .profile_write_approval_request import _approval_packet_id


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


def _validated_drafts(drafts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    validated: list[dict[str, Any]] = []
    for draft in drafts:
        profile_path = str(draft.get("profile_path") or "")
        draft_yaml = str(draft.get("draft_yaml") or "")
        try:
            parsed = parse_profile_text(draft_yaml)
            profile = load_workspace_profile_from_mapping(parsed)
        except Exception as exc:
            blockers.append(f"draft_validation_failed:{profile_path}:{exc}")
            continue
        validated.append(
            {
                "profile_path": profile_path,
                "draft_yaml": draft_yaml,
                "draft_yaml_sha256": draft.get("draft_yaml_sha256"),
                "workspace_id": profile.workspace_id,
                "workspace_mode": profile.workspace_mode,
                "allowed_workflows": list(profile.allowed_workflows),
            }
        )
    return validated, blockers


def build_workspace_profile_guarded_write(
    *,
    vault_root: str | Path | None = None,
    workspace_path: str | Path | None = None,
    profile_scope: str = "foundation",
    approval_packet_id: str | None = None,
    confirm: bool = False,
    requested_by: str = "operator",
) -> dict[str, Any]:
    """Create approved WML profile files, or preview why the write is blocked."""

    root = Path(vault_root).resolve() if vault_root is not None else _detect_vault_root()
    draft_packet = build_workspace_profile_draft_packet(
        vault_root=root,
        workspace_path=workspace_path,
        profile_scope=profile_scope,
    )
    drafts = list(draft_packet.get("drafts") or [])
    expected_approval_packet_id = _approval_packet_id(drafts)
    validated_drafts, validation_blockers = _validated_drafts(drafts)

    profile_targets: list[dict[str, Any]] = []
    blockers: list[str] = []
    blockers.extend(validation_blockers)

    if not drafts:
        blockers.append("no_profile_drafts_available")
    if len(validated_drafts) != len(drafts):
        blockers.append("one_or_more_drafts_failed_revalidation")
    if not bool(draft_packet.get("profile_write_ready_for_operator_review")):
        blockers.append("draft_packet_not_ready_for_profile_write")
    if approval_packet_id != expected_approval_packet_id:
        blockers.append("approval_packet_id_required_or_mismatched")
    if not confirm:
        blockers.append("confirm_required")

    for draft in validated_drafts:
        profile_abs, inside_vault = _resolve_inside_vault(draft["profile_path"], root)
        profile_present = profile_abs.exists()
        parent_exists = profile_abs.parent.exists()
        if not inside_vault:
            blockers.append(f"profile_path_outside_vault:{draft['profile_path']}")
        if not parent_exists:
            blockers.append(f"profile_parent_missing:{draft['profile_path']}")
        if profile_present:
            blockers.append(f"profile_path_already_exists_no_overwrite:{draft['profile_path']}")
        profile_targets.append(
            {
                "profile_path": _safe_relative(profile_abs, root),
                "profile_path_in_vault": inside_vault,
                "profile_parent_exists": parent_exists,
                "profile_present_before_write": profile_present,
                "workspace_id": draft["workspace_id"],
                "workspace_mode": draft["workspace_mode"],
                "allowed_workflows": draft["allowed_workflows"],
                "draft_yaml_sha256": draft["draft_yaml_sha256"],
            }
        )

    ready_for_profile_write = not blockers
    profile_files_written = False
    written_profiles: list[dict[str, Any]] = []
    write_errors: list[str] = []

    if ready_for_profile_write:
        for draft in validated_drafts:
            profile_abs, _inside_vault = _resolve_inside_vault(draft["profile_path"], root)
            try:
                with profile_abs.open("x", encoding="utf-8", newline="\n") as handle:
                    handle.write(draft["draft_yaml"])
                loaded = load_workspace_profile(profile_abs)
            except FileExistsError:
                write_errors.append(f"profile_path_already_exists_no_overwrite:{draft['profile_path']}")
                break
            except Exception as exc:
                write_errors.append(f"profile_write_failed:{draft['profile_path']}:{exc}")
                break
            written_profiles.append(
                {
                    "profile_path": _safe_relative(profile_abs, root),
                    "workspace_id": loaded.workspace_id,
                    "workspace_mode": loaded.workspace_mode,
                    "allowed_workflows": list(loaded.allowed_workflows),
                    "draft_yaml_sha256": draft["draft_yaml_sha256"],
                }
            )
        profile_files_written = len(written_profiles) == len(validated_drafts) and not write_errors

    if write_errors:
        blockers.extend(write_errors)

    return {
        "ok": profile_files_written if confirm and approval_packet_id else True,
        "surface": "workspace_mode_profile_guarded_writer",
        "profile_scope": profile_scope,
        "profile_write_surface_only": True,
        "vault_root": str(root),
        "requested_by": requested_by,
        "approval_packet_id": approval_packet_id,
        "expected_approval_packet_id": expected_approval_packet_id,
        "approval_packet_matched": approval_packet_id == expected_approval_packet_id,
        "operator_confirmed": confirm,
        "ready_for_profile_write": ready_for_profile_write,
        "profile_files_written": profile_files_written,
        "profile_write_performed": profile_files_written,
        "profile_overwrite_performed": False,
        "written_profile_count": len(written_profiles),
        "target_profile_count": len(profile_targets),
        "target_profiles": profile_targets,
        "written_profiles": written_profiles,
        "draft_packet": draft_packet,
        "aor_dispatch_enabled": False,
        "workflow_execution_performed": False,
        "agent_bus_task_written": False,
        "approval_artifact_consumed": False,
        "approval_consumed": False,
        "profile_write_approval_used": profile_files_written,
        "provider_or_model_call_performed": False,
        "browser_or_external_action_performed": False,
        "external_action_performed": False,
        "canonical_write_performed": False,
        "blockers": blockers,
        "next_recommended_pass": (
            "workspace-mode-post-profile-route-preview"
            if profile_files_written
            else "workspace-mode-profile-write-approval-decision-or-guard-repair"
        ),
    }


def format_workspace_profile_guarded_write(payload: dict[str, Any]) -> str:
    lines = [
        "Workspace Mode guarded profile writer",
        f"  expected_approval_packet_id: {payload.get('expected_approval_packet_id')}",
        f"  approval_packet_matched:     {payload.get('approval_packet_matched')}",
        f"  operator_confirmed:          {payload.get('operator_confirmed')}",
        f"  ready_for_profile_write:     {payload.get('ready_for_profile_write')}",
        f"  profile_files_written:       {payload.get('profile_files_written')}",
        f"  written_profile_count:       {payload.get('written_profile_count')}",
        f"  blockers:                    {', '.join(payload.get('blockers') or []) or '(none)'}",
        "  boundary: create-only profile files; no overwrite, AOR dispatch, Agent Bus task write, provider/model call, external action, or canonical writeback.",
    ]
    for profile in payload.get("written_profiles") or []:
        lines.append(
            "    - "
            f"{profile.get('profile_path')} "
            f"mode={profile.get('workspace_mode')} "
            f"workflows={','.join(profile.get('allowed_workflows') or []) or '(none)'}"
        )
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m runtime.workspace_modes.profile_guarded_writer",
        description="Create approved WML profile files with create-only guards.",
    )
    parser.add_argument("--workspace-path", default=None, metavar="PATH")
    parser.add_argument("--vault-root", default=None, metavar="PATH")
    parser.add_argument("--approval-packet-id", required=True, metavar="ID")
    parser.add_argument("--requested-by", default="operator", metavar="ID")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--json", action="store_true", dest="output_json")
    args = parser.parse_args(argv)

    payload = build_workspace_profile_guarded_write(
        vault_root=args.vault_root,
        workspace_path=args.workspace_path,
        approval_packet_id=args.approval_packet_id,
        requested_by=args.requested_by,
        confirm=args.confirm,
    )
    if args.output_json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_workspace_profile_guarded_write(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
