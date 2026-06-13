"""Read-only AOR routing preview for Workspace Mode Layer context."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.aor.registry import load_manifest

from .inference import infer_workspace_mode, normalize_workspace_path
from .loader import WorkspaceModeLoadError, load_workspace_profile
from .models import WorkspaceModeProfile, build_unknown_profile


@dataclass(frozen=True)
class InferredModePolicy:
    adapter_ceiling: dict[str, str]
    approval_mode: str
    default_write_targets: tuple[str, ...]


INFERRED_MODE_POLICIES: dict[str, InferredModePolicy] = {
    "personal_os": InferredModePolicy(
        adapter_ceiling={
            "claude": "tier-3",
            "codex": "tier-3",
            "openclaw": "blocked",
            "hermes": "blocked",
        },
        approval_mode="personal_canonical_writes_require_explicit_approval",
        default_write_targets=("07_LOGS/Daily/",),
    ),
    "study_research": InferredModePolicy(
        adapter_ceiling={
            "claude": "tier-3",
            "codex": "tier-3",
            "openclaw": "blocked",
            "hermes": "blocked",
        },
        approval_mode="source_provenance_first; promotion_requires_gate",
        default_write_targets=("03_INPUTS/", "02_KNOWLEDGE/"),
    ),
    "founder_venture": InferredModePolicy(
        adapter_ceiling={
            "claude": "tier-2-bounded",
            "codex": "tier-2-bounded",
            "openclaw": "blocked",
            "hermes": "blocked",
        },
        approval_mode="roadmap_or_project_truth_changes_require_explicit_approval",
        default_write_targets=("07_LOGS/Build-Logs/", "07_LOGS/Operator-Briefs/"),
    ),
    "business_ops": InferredModePolicy(
        adapter_ceiling={
            "claude": "tier-2-bounded",
            "codex": "tier-2-bounded",
            "openclaw": "blocked",
            "hermes": "blocked",
        },
        approval_mode="external_business_action_blocked_without_explicit_approval",
        default_write_targets=("07_LOGS/Operator-Briefs/", "07_LOGS/Workflow-Proofs/"),
    ),
    "runtime_agent_ops": InferredModePolicy(
        adapter_ceiling={
            "claude": "tier-2",
            "codex": "tier-2",
            "openclaw": "tier-2-bounded",
            "hermes": "tier-2-bounded",
        },
        approval_mode="protected_canonical_shell_and_external_actions_fail_closed",
        default_write_targets=(
            "07_LOGS/Build-Logs/",
            "07_LOGS/Agent-Activity/",
            "99_ARCHIVE/Documentation-History/",
        ),
    ),
    "unknown": InferredModePolicy(
        adapter_ceiling={
            "claude": "blocked",
            "codex": "blocked",
            "openclaw": "blocked",
            "hermes": "blocked",
        },
        approval_mode="unknown_mode_stop_and_request_mode",
        default_write_targets=(),
    ),
}


def _detect_vault_root() -> Path:
    here = Path(__file__).resolve()
    vault_root = here.parents[2]
    if not (vault_root / "CLAUDE.md").exists():
        raise RuntimeError(f"could not detect ChaseOS vault root from {here}")
    return vault_root


def _resolve_target_path(path: str | Path, vault_root: Path) -> Path:
    target = Path(path)
    if not target.is_absolute():
        target = vault_root / target
    return target.resolve()


def _safe_relative(path: Path, vault_root: Path) -> str:
    try:
        rel = path.resolve().relative_to(vault_root.resolve())
        return str(rel).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _profile_payload(profile: WorkspaceModeProfile) -> dict[str, Any]:
    return {
        "workspace_id": profile.workspace_id,
        "workspace_name": profile.workspace_name,
        "workspace_mode": profile.workspace_mode,
        "required_read_order": list(profile.required_read_order),
        "allowed_workflows": list(profile.allowed_workflows),
        "default_write_targets": list(profile.default_write_targets),
        "runtime_adapter_ceiling": dict(profile.runtime_adapter_ceiling),
        "approval_rules": dict(profile.approval_rules),
        "graph_rules": dict(profile.graph_rules),
        "protected_paths": list(profile.protected_paths),
    }


def _find_workspace_profile(
    workspace_path: str | Path,
    vault_root: Path,
    *,
    profile_path: str | Path | None = None,
) -> tuple[WorkspaceModeProfile | None, str, str | None]:
    if profile_path is not None:
        explicit = _resolve_target_path(profile_path, vault_root)
        return load_workspace_profile(explicit), "explicit_profile", _safe_relative(explicit, vault_root)

    target = _resolve_target_path(workspace_path, vault_root)
    if target.suffix.lower() in {".md", ".markdown"} and target.exists():
        try:
            return load_workspace_profile(target), "markdown_frontmatter", _safe_relative(target, vault_root)
        except (OSError, ValueError):
            pass

    cursor = target if target.is_dir() else target.parent
    try:
        cursor = cursor.resolve()
        root = vault_root.resolve()
        cursor.relative_to(root)
    except ValueError:
        return None, "outside_vault_no_profile", None

    while True:
        for name in ("workspace-mode.yaml", ".workspace-mode.yaml"):
            candidate = cursor / name
            if candidate.exists():
                return load_workspace_profile(candidate), "discovered_profile", _safe_relative(candidate, vault_root)
        if cursor == root:
            break
        cursor = cursor.parent
    return None, "path_inference", None


def _manifest_preview(vault_root: Path, workflow_id: str | None) -> tuple[dict[str, Any] | None, list[str]]:
    if not workflow_id:
        return None, []
    manifest = load_manifest(workflow_id, vault_root)
    if manifest is None:
        return None, [f"workflow_manifest_not_found:{workflow_id}"]
    return {
        "id": manifest.get("id"),
        "status": manifest.get("status"),
        "task_type": manifest.get("task_type"),
        "role_card": manifest.get("role_card"),
        "permission_ceiling": manifest.get("permission_ceiling"),
        "approval_rule": manifest.get("approval_rule", "none"),
        "writeback_targets": list(manifest.get("writeback_targets") or []),
    }, []


def build_aor_workspace_route_preview(
    *,
    workspace_path: str | Path,
    workflow_id: str | None = None,
    adapter: str = "codex",
    vault_root: str | Path | None = None,
    profile_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a no-dispatch WML/AOR routing preview."""

    root = Path(vault_root).resolve() if vault_root is not None else _detect_vault_root()
    normalized_path = normalize_workspace_path(workspace_path, vault_root=root)
    profile_error: str | None = None
    profile: WorkspaceModeProfile | None
    profile_source: str
    profile_source_path: str | None

    try:
        profile, profile_source, profile_source_path = _find_workspace_profile(
            workspace_path,
            root,
            profile_path=profile_path,
        )
    except (OSError, WorkspaceModeLoadError, ValueError) as exc:
        profile = build_unknown_profile(str(workspace_path))
        profile_source = "profile_error_fail_closed"
        profile_source_path = str(profile_path) if profile_path is not None else None
        profile_error = str(exc)

    inferred_mode = infer_workspace_mode(workspace_path, vault_root=root)
    if profile is None:
        mode = inferred_mode
        policy = INFERRED_MODE_POLICIES.get(mode, INFERRED_MODE_POLICIES["unknown"])
        adapter_ceiling = policy.adapter_ceiling.get(adapter, "blocked")
        approval_mode = policy.approval_mode
        default_write_targets = list(policy.default_write_targets)
        allowed_workflows: list[str] = []
        profile_loaded = False
    else:
        mode = profile.workspace_mode
        adapter_ceiling = profile.adapter_ceiling_for(adapter)
        approval_mode = str(profile.approval_rules.get("canonical_state_write", "unspecified"))
        default_write_targets = list(profile.default_write_targets)
        allowed_workflows = list(profile.allowed_workflows)
        profile_loaded = profile_source != "profile_error_fail_closed"

    manifest, manifest_blockers = _manifest_preview(root, workflow_id)
    workflow_allowed = bool(workflow_id and workflow_id in allowed_workflows)
    blockers: list[str] = []
    blockers.extend(manifest_blockers)

    if mode == "unknown":
        blockers.append("workspace_mode_unknown")
    if adapter_ceiling == "blocked":
        blockers.append(f"adapter_blocked:{adapter}")
    if workflow_id and manifest is not None and manifest.get("status") != "active":
        blockers.append(f"workflow_not_active:{manifest.get('status')}")
    if workflow_id and not workflow_allowed and profile_loaded:
        blockers.append("workflow_not_allowed_by_explicit_profile")
    if workflow_id and not workflow_allowed and not profile_loaded:
        blockers.append("workflow_not_authorized_without_explicit_profile")
    if not profile_loaded:
        blockers.append("explicit_workspace_profile_required_for_aor_dispatch")
    if profile_error:
        blockers.append("profile_validation_failed")

    ready_for_aor_dispatch = bool(
        workflow_id
        and manifest is not None
        and manifest.get("status") == "active"
        and profile_loaded
        and workflow_allowed
        and adapter_ceiling != "blocked"
        and mode != "unknown"
        and not profile_error
    )

    return {
        "ok": True,
        "preview_only": True,
        "workflow_execution_performed": False,
        "agent_bus_task_written": False,
        "approval_consumed": False,
        "canonical_write_performed": False,
        "external_action_performed": False,
        "vault_root": str(root),
        "workspace_path": normalized_path,
        "requested_workflow_id": workflow_id,
        "requested_adapter": adapter,
        "workspace_mode": mode,
        "inferred_mode": inferred_mode,
        "profile_loaded": profile_loaded,
        "profile_source": profile_source,
        "profile_source_path": profile_source_path,
        "profile_error": profile_error,
        "adapter_ceiling": adapter_ceiling,
        "approval_mode": approval_mode,
        "default_write_targets": default_write_targets,
        "allowed_workflows": allowed_workflows,
        "workflow_allowed_by_profile": workflow_allowed,
        "workflow_manifest": manifest,
        "ready_for_aor_dispatch": ready_for_aor_dispatch,
        "dispatch_blockers": blockers,
        "next_recommended_pass": (
            "workspace-mode-aor-dispatch-gate"
            if ready_for_aor_dispatch
            else "add-explicit-workspace-mode-profile-or-adjust-workflow-scope"
        ),
        "profile": _profile_payload(profile) if profile is not None else None,
    }


def format_aor_workspace_route_preview(payload: dict[str, Any]) -> str:
    blockers = payload.get("dispatch_blockers") or []
    lines = [
        "Workspace Mode AOR route preview",
        f"  workspace_path:       {payload.get('workspace_path')}",
        f"  workspace_mode:       {payload.get('workspace_mode')}",
        f"  profile_source:       {payload.get('profile_source')}",
        f"  requested_workflow:   {payload.get('requested_workflow_id') or '(none)'}",
        f"  requested_adapter:    {payload.get('requested_adapter')}",
        f"  adapter_ceiling:      {payload.get('adapter_ceiling')}",
        f"  approval_mode:        {payload.get('approval_mode')}",
        f"  write_targets:        {', '.join(payload.get('default_write_targets') or []) or '(none)'}",
        f"  ready_for_dispatch:   {payload.get('ready_for_aor_dispatch')}",
        f"  blockers:             {', '.join(blockers) if blockers else '(none)'}",
        "  boundary: preview only; no AOR workflow dispatch, Agent Bus task write, approval consumption, external action, or canonical writeback.",
    ]
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m runtime.workspace_modes.aor_routing_preview",
        description="Preview WML/AOR routing without dispatching a workflow.",
    )
    parser.add_argument("--workspace-path", required=True, metavar="PATH")
    parser.add_argument("--workflow-id", default=None, metavar="WORKFLOW_ID")
    parser.add_argument("--adapter", default="codex", metavar="ADAPTER")
    parser.add_argument("--profile", dest="profile_path", default=None, metavar="PATH")
    parser.add_argument("--vault-root", default=None, metavar="PATH")
    parser.add_argument("--json", action="store_true", dest="output_json")
    args = parser.parse_args(argv)

    payload = build_aor_workspace_route_preview(
        workspace_path=args.workspace_path,
        workflow_id=args.workflow_id,
        adapter=args.adapter,
        vault_root=args.vault_root,
        profile_path=args.profile_path,
    )
    if args.output_json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_aor_workspace_route_preview(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
