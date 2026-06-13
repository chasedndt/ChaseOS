"""Validated draft packet builder for Workspace Mode profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .loader import load_workspace_profile_from_mapping, parse_profile_text
from .profile_rollout_plan import (
    DEFAULT_ROLLOUT_CANDIDATES,
    RolloutCandidateSeed,
    build_workspace_profile_rollout_plan,
)


DEFAULT_DRAFT_PROFILE_PATHS: tuple[str, ...] = (
    "runtime/.workspace-mode.yaml",
    "06_AGENTS/.workspace-mode.yaml",
    "01_PROJECTS/ChaseOS/workspace-mode.yaml",
)

FULL_PRODUCT_PROFILE_SCOPE_ALIASES: tuple[str, ...] = (
    "full-product",
    "full_product",
    "full",
    "all-missing",
)


def _detect_vault_root() -> Path:
    here = Path(__file__).resolve()
    vault_root = here.parents[2]
    if not (vault_root / "CLAUDE.md").exists():
        raise RuntimeError(f"could not detect ChaseOS vault root from {here}")
    return vault_root


def _select_candidate_paths(
    candidates: list[dict[str, Any]],
    *,
    workspace_path: str | Path | None,
    profile_scope: str = "foundation",
) -> tuple[str, list[dict[str, Any]]]:
    if workspace_path is not None:
        return "targeted_workspace", candidates
    if profile_scope in FULL_PRODUCT_PROFILE_SCOPE_ALIASES:
        selected = [
            candidate
            for candidate in candidates
            if not bool(candidate.get("profile_present"))
        ]
        return "full_product_missing_profiles", selected
    selected = [
        candidate
        for candidate in candidates
        if str(candidate.get("profile_path")) in DEFAULT_DRAFT_PROFILE_PATHS
    ]
    return "recommended_runtime_foundation", selected


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    text = str(value)
    if not text:
        return '""'
    if any(char in text for char in [":", "#", "{", "}", "[", "]", "\n"]):
        return json.dumps(text)
    return text


def render_profile_yaml(profile: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in profile.items():
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
                continue
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {_yaml_scalar(item)}")
            continue
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for subkey, subvalue in value.items():
                lines.append(f"  {subkey}: {_yaml_scalar(subvalue)}")
            continue
        lines.append(f"{key}: {_yaml_scalar(value)}")
    return "\n".join(lines) + "\n"


def _validate_draft_yaml(profile: dict[str, Any], draft_yaml: str) -> dict[str, Any]:
    errors: list[str] = []
    mapping_validation_ok = False
    yaml_validation_ok = False
    try:
        load_workspace_profile_from_mapping(profile)
        mapping_validation_ok = True
    except Exception as exc:  # pragma: no cover - defensive path
        errors.append(f"mapping_validation_failed:{exc}")
    try:
        parsed = parse_profile_text(draft_yaml)
        load_workspace_profile_from_mapping(parsed)
        yaml_validation_ok = True
    except Exception as exc:
        errors.append(f"yaml_validation_failed:{exc}")
    return {
        "mapping_validation_ok": mapping_validation_ok,
        "yaml_roundtrip_validation_ok": yaml_validation_ok,
        "validation_errors": errors,
    }


def _draft_for_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    profile = dict(candidate["proposed_profile"])
    draft_yaml = render_profile_yaml(profile)
    validation = _validate_draft_yaml(profile, draft_yaml)
    profile_present = bool(candidate.get("profile_present"))
    write_blockers: list[str] = ["operator_approval_required_before_profile_write"]
    if profile_present:
        write_blockers.append("profile_path_already_exists_no_overwrite_without_explicit_approval")
    if not validation["mapping_validation_ok"] or not validation["yaml_roundtrip_validation_ok"]:
        write_blockers.append("draft_profile_validation_failed")

    return {
        "workspace_path": candidate.get("workspace_path"),
        "profile_path": candidate.get("profile_path"),
        "profile_present": profile_present,
        "recommended_mode": candidate.get("recommended_mode"),
        "priority": candidate.get("priority"),
        "draft_yaml_sha256": hashlib.sha256(draft_yaml.encode("utf-8")).hexdigest(),
        "draft_yaml": draft_yaml,
        "proposed_profile": profile,
        "validation": validation,
        "write_allowed_in_this_pass": False,
        "profile_file_written": False,
        "profile_write_requires_operator_approval": True,
        "write_blockers": write_blockers,
    }


def build_workspace_profile_draft_packet(
    *,
    vault_root: str | Path | None = None,
    workspace_path: str | Path | None = None,
    profile_scope: str = "foundation",
) -> dict[str, Any]:
    """Build validated draft YAML profile payloads without writing profile files."""

    root = Path(vault_root).resolve() if vault_root is not None else _detect_vault_root()
    rollout = build_workspace_profile_rollout_plan(
        vault_root=root,
        workspace_path=workspace_path,
    )
    scope, selected_candidates = _select_candidate_paths(
        list(rollout.get("candidates") or []),
        workspace_path=workspace_path,
        profile_scope=profile_scope,
    )
    drafts = [_draft_for_candidate(candidate) for candidate in selected_candidates]
    validation_ok = all(
        draft["validation"]["mapping_validation_ok"]
        and draft["validation"]["yaml_roundtrip_validation_ok"]
        for draft in drafts
    )
    existing_profile_blockers = [
        draft["profile_path"] for draft in drafts if draft["profile_present"]
    ]
    packet_blockers = ["operator_approval_required_before_profile_write"]
    if existing_profile_blockers:
        packet_blockers.append("one_or_more_profile_paths_already_exist")
    if not validation_ok:
        packet_blockers.append("one_or_more_draft_profiles_failed_validation")

    return {
        "ok": True,
        "surface": "workspace_mode_profile_draft_packet",
        "scope": scope,
        "profile_scope": profile_scope,
        "preview_only": True,
        "draft_packet_only": True,
        "profile_files_written": False,
        "profile_write_ready_for_operator_review": validation_ok,
        "profile_write_performed": False,
        "aor_dispatch_enabled": False,
        "workflow_execution_performed": False,
        "agent_bus_task_written": False,
        "approval_consumed": False,
        "canonical_write_performed": False,
        "external_action_performed": False,
        "vault_root": str(root),
        "source_rollout_surface": rollout.get("surface"),
        "draft_count": len(drafts),
        "drafts": drafts,
        "packet_blockers": packet_blockers,
        "acceptance_criteria_for_future_profile_write": [
            "operator explicitly approves selected profile paths",
            "writer revalidates draft YAML immediately before write",
            "writer refuses existing profile paths unless overwrite approval is explicit",
            "writer writes only approved profile paths",
            "route-preview is rerun after profile creation before dispatch gate work",
        ],
        "next_recommended_pass": (
            "workspace-mode-profile-write-approval-request"
            if validation_ok
            else "workspace-mode-profile-draft-repair"
        ),
    }


def format_workspace_profile_draft_packet(payload: dict[str, Any]) -> str:
    lines = [
        "Workspace Mode profile draft packet",
        f"  scope:             {payload.get('scope')}",
        f"  draft_count:       {payload.get('draft_count')}",
        f"  review_ready:      {payload.get('profile_write_ready_for_operator_review')}",
        f"  blockers:          {', '.join(payload.get('packet_blockers') or [])}",
        "  boundary: draft packet only; no profile file write, AOR dispatch, Agent Bus task write, approval consumption, external action, or canonical writeback.",
        "  drafts:",
    ]
    for draft in payload.get("drafts") or []:
        validation = draft.get("validation") or {}
        lines.append(
            "    - "
            f"{draft.get('profile_path')} "
            f"mode={draft.get('recommended_mode')} "
            f"present={draft.get('profile_present')} "
            f"yaml_valid={validation.get('yaml_roundtrip_validation_ok')}"
        )
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m runtime.workspace_modes.profile_draft_packet",
        description="Build validated WML profile draft packets without writing profile files.",
    )
    parser.add_argument("--workspace-path", default=None, metavar="PATH")
    parser.add_argument("--vault-root", default=None, metavar="PATH")
    parser.add_argument("--json", action="store_true", dest="output_json")
    args = parser.parse_args(argv)

    payload = build_workspace_profile_draft_packet(
        vault_root=args.vault_root,
        workspace_path=args.workspace_path,
    )
    if args.output_json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_workspace_profile_draft_packet(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
