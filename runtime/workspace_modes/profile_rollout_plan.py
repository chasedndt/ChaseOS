"""Review-only rollout planner for Workspace Mode profiles."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .aor_routing_preview import INFERRED_MODE_POLICIES
from .inference import infer_workspace_mode, normalize_workspace_path


@dataclass(frozen=True)
class RolloutCandidateSeed:
    workspace_path: str
    profile_path: str
    priority: int
    reason: str
    recommended_mode: str | None = None
    allowed_workflows: tuple[str, ...] = ()


DEFAULT_ROLLOUT_CANDIDATES: tuple[RolloutCandidateSeed, ...] = (
    RolloutCandidateSeed(
        workspace_path="runtime/",
        profile_path="runtime/.workspace-mode.yaml",
        priority=10,
        reason="Runtime code is the first WML/AOR dispatch-risk surface.",
        recommended_mode="runtime_agent_ops",
        allowed_workflows=("operator_today", "operator_close_day"),
    ),
    RolloutCandidateSeed(
        workspace_path="06_AGENTS/",
        profile_path="06_AGENTS/.workspace-mode.yaml",
        priority=20,
        reason="Agent governance docs define runtime and adapter authority boundaries.",
        recommended_mode="runtime_agent_ops",
        allowed_workflows=("operator_today",),
    ),
    RolloutCandidateSeed(
        workspace_path="01_PROJECTS/ChaseOS/",
        profile_path="01_PROJECTS/ChaseOS/workspace-mode.yaml",
        priority=30,
        reason="ChaseOS project truth is the main framework/runtime workspace.",
        recommended_mode="runtime_agent_ops",
        allowed_workflows=("operator_today", "operator_close_day", "graph_hygiene"),
    ),
    RolloutCandidateSeed(
        workspace_path="04_SOPS/",
        profile_path="04_SOPS/.workspace-mode.yaml",
        priority=40,
        reason="SOP work needs business/process posture and protected operational boundaries.",
        recommended_mode="business_ops",
    ),
    RolloutCandidateSeed(
        workspace_path="01_PROJECTS/University/",
        profile_path="01_PROJECTS/University/workspace-mode.yaml",
        priority=50,
        reason="University work should remain source/provenance-first and runtime blocked.",
        recommended_mode="study_research",
    ),
    RolloutCandidateSeed(
        workspace_path="00_HOME/",
        profile_path="00_HOME/.workspace-mode.yaml",
        priority=60,
        reason="Personal operating context is high-sensitivity and should stay approval-gated.",
        recommended_mode="personal_os",
    ),
)


MODE_DEFAULTS: dict[str, dict[str, Any]] = {
    "runtime_agent_ops": {
        "primary_domains": ["AI Engineering", "Runtime Governance", "Agent Operations"],
        "canonical_state_files": ["00_HOME/Now.md", "ROADMAP.md", "PROJECT_FOUNDATION.md"],
        "required_read_order": [
            "README.md",
            "PROJECT_FOUNDATION.md",
            "ROADMAP.md",
            "00_HOME/Now.md",
            "06_AGENTS/Agent-Control-Plane.md",
            "06_AGENTS/Permission-Matrix.md",
            "06_AGENTS/Trust-Tiers.md",
        ],
        "default_output_classes": ["build-log", "agent-activity-log", "operator-brief", "proposal"],
        "default_write_targets": [
            "07_LOGS/Build-Logs/",
            "07_LOGS/Agent-Activity/",
            "99_ARCHIVE/Documentation-History/",
        ],
    },
    "business_ops": {
        "primary_domains": ["Business Operations", "Process Governance"],
        "canonical_state_files": ["04_SOPS/"],
        "required_read_order": ["04_SOPS/Build-Log-SOP.md", "06_AGENTS/Permission-Matrix.md"],
        "default_output_classes": ["operator-brief", "proposal", "audit-packet"],
        "default_write_targets": ["07_LOGS/Operator-Briefs/", "07_LOGS/Workflow-Proofs/"],
    },
    "study_research": {
        "primary_domains": ["University", "Research"],
        "canonical_state_files": ["01_PROJECTS/University/Degree-OS.md"],
        "required_read_order": [
            "01_PROJECTS/University/Degree-OS.md",
            "04_SOPS/Research-Ingest-SOP.md",
        ],
        "default_output_classes": ["source-note", "synthesis-note", "proposal"],
        "default_write_targets": ["03_INPUTS/", "02_KNOWLEDGE/"],
    },
    "personal_os": {
        "primary_domains": ["Personal Operating System"],
        "canonical_state_files": ["00_HOME/Now.md", "00_HOME/Operating-System.md"],
        "required_read_order": ["00_HOME/Now.md", "00_HOME/Assistant-Contract.md"],
        "default_output_classes": ["daily-note", "proposal", "reflection"],
        "default_write_targets": ["07_LOGS/Daily/"],
    },
    "founder_venture": {
        "primary_domains": ["Founder", "Venture", "Product R&D"],
        "canonical_state_files": ["01_PROJECTS/Businesses/Businesses-OS.md"],
        "required_read_order": ["PROJECT_FOUNDATION.md", "ROADMAP.md"],
        "default_output_classes": ["build-log", "operator-brief", "proposal"],
        "default_write_targets": ["07_LOGS/Build-Logs/", "07_LOGS/Operator-Briefs/"],
    },
    "unknown": {
        "primary_domains": [],
        "canonical_state_files": [],
        "required_read_order": [],
        "default_output_classes": ["proposal"],
        "default_write_targets": [],
    },
}

COMMON_ALLOWED_KNOWLEDGE_CLASSES: tuple[str, ...] = (
    "user-origin",
    "source-derived",
    "synthesized",
    "generated-ideas",
    "system-operational",
    "canonical-state",
)

COMMON_APPROVAL_RULES: dict[str, str] = {
    "canonical_state_write": "explicit_user_approval_required",
    "generated_idea_creation": "allowed_with_label",
    "generated_idea_endorsement": "human_only",
    "source_promotion": "gate_required",
    "protected_file_write": "explicit_per_file_approval_required",
    "shell_execution": "blocked_by_default",
    "external_connector_action": "blocked_by_default",
}

COMMON_GRAPH_RULES: dict[str, bool] = {
    "update_domain_index_on_promotion": True,
    "backlinks_required_for_durable_notes": True,
    "orphan_notes_flagged": True,
}

COMMON_PROTECTED_PATHS: tuple[str, ...] = (
    ".env",
    "secrets/",
    "credentials/",
    "00_HOME/Now.md",
    "ROADMAP.md",
    "PROJECT_FOUNDATION.md",
)

COMMON_ESCALATION_RULES: dict[str, str] = {
    "unknown_mode": "stop_and_request_mode",
    "protected_write": "require_explicit_approval",
    "external_action": "require_explicit_approval",
    "runtime_authority_unclear": "fail_closed",
}


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


def _profile_exists(profile_path: Path) -> bool:
    return profile_path.exists()


def _slug_from_path(path: str) -> str:
    cleaned = path.strip("/").replace("\\", "/")
    if not cleaned:
        return "vault-root"
    return cleaned.lower().replace("/", "-").replace("_", "-").replace(".", "-").strip("-")


def _name_from_path(path: str) -> str:
    cleaned = path.strip("/").replace("\\", "/")
    if not cleaned:
        return "Vault Root"
    name = cleaned.rsplit("/", 1)[-1]
    if name.lower() == "chaseos":
        return "ChaseOS"
    return name.replace("-", " ").replace("_", " ").title()


def _profile_path_for_target(workspace_path: str) -> str:
    normalized = normalize_workspace_path(workspace_path)
    last_part = normalized.rstrip("/").rsplit("/", 1)[-1]
    is_file_path = "." in last_part
    if is_file_path:
        parent = normalized.rsplit("/", 1)[0] if "/" in normalized else ""
        normalized = f"{parent}/" if parent else ""
    if normalized.startswith("01_PROJECTS/"):
        parts = normalized.strip("/").split("/")
        if len(parts) >= 2:
            return f"01_PROJECTS/{parts[1]}/workspace-mode.yaml"
    base = normalized.rstrip("/")
    return f"{base}/.workspace-mode.yaml" if base else ".workspace-mode.yaml"


def _seed_for_workspace_path(workspace_path: str) -> RolloutCandidateSeed:
    normalized = normalize_workspace_path(workspace_path)
    mode = infer_workspace_mode(normalized)
    return RolloutCandidateSeed(
        workspace_path=normalized,
        profile_path=_profile_path_for_target(normalized),
        priority=100,
        reason="Operator-requested targeted workspace profile review.",
        recommended_mode=mode,
    )


def _proposed_profile(seed: RolloutCandidateSeed, mode: str) -> dict[str, Any]:
    defaults = MODE_DEFAULTS.get(mode, MODE_DEFAULTS["unknown"])
    policy = INFERRED_MODE_POLICIES.get(mode, INFERRED_MODE_POLICIES["unknown"])
    workspace_path = _workspace_identity_path_from_profile_path(seed.profile_path)
    return {
        "workspace_id": _slug_from_path(workspace_path),
        "workspace_name": _name_from_path(workspace_path),
        "workspace_mode": mode,
        "description": f"Workspace Mode profile for {workspace_path or 'vault root'}.",
        "primary_domains": list(defaults["primary_domains"]),
        "canonical_state_files": list(defaults["canonical_state_files"]),
        "required_read_order": list(defaults["required_read_order"]),
        "allowed_knowledge_classes": list(COMMON_ALLOWED_KNOWLEDGE_CLASSES),
        "default_output_classes": list(defaults["default_output_classes"]),
        "allowed_workflows": list(seed.allowed_workflows),
        "runtime_adapter_ceiling": dict(policy.adapter_ceiling),
        "approval_rules": dict(COMMON_APPROVAL_RULES),
        "graph_rules": dict(COMMON_GRAPH_RULES),
        "protected_paths": list(COMMON_PROTECTED_PATHS),
        "default_write_targets": list(defaults["default_write_targets"]),
        "escalation_rules": dict(COMMON_ESCALATION_RULES),
    }


def _workspace_identity_path_from_profile_path(profile_path: str) -> str:
    normalized = profile_path.replace("\\", "/").strip("/")
    if normalized.endswith("/workspace-mode.yaml"):
        return normalize_workspace_path(normalized[: -len("/workspace-mode.yaml")])
    if normalized.endswith("/.workspace-mode.yaml"):
        return normalize_workspace_path(normalized[: -len("/.workspace-mode.yaml")])
    return normalize_workspace_path(normalized)


def _candidate_from_seed(seed: RolloutCandidateSeed, vault_root: Path) -> dict[str, Any]:
    workspace_path = normalize_workspace_path(seed.workspace_path)
    workspace_abs, workspace_inside = _resolve_inside_vault(workspace_path, vault_root)
    profile_abs, profile_inside = _resolve_inside_vault(seed.profile_path, vault_root)
    inferred_mode = infer_workspace_mode(workspace_path, vault_root=vault_root)
    recommended_mode = seed.recommended_mode or inferred_mode
    profile_exists = _profile_exists(profile_abs)
    blockers: list[str] = []
    if not workspace_inside or not profile_inside:
        blockers.append("candidate_path_outside_vault")
    if recommended_mode == "unknown":
        blockers.append("workspace_mode_unknown_operator_confirmation_required")
    if profile_exists:
        blockers.append("profile_already_exists_review_before_overwrite")

    return {
        "workspace_path": workspace_path,
        "workspace_exists": workspace_abs.exists(),
        "workspace_path_in_vault": workspace_inside,
        "profile_path": _safe_relative(profile_abs, vault_root),
        "profile_path_in_vault": profile_inside,
        "profile_present": profile_exists,
        "inferred_mode": inferred_mode,
        "recommended_mode": recommended_mode,
        "priority": seed.priority,
        "reason": seed.reason,
        "review_required": True,
        "write_allowed_in_this_pass": False,
        "manual_action_required": not profile_exists,
        "dispatch_ready_after_this_plan": False,
        "blockers": blockers,
        "proposed_profile": _proposed_profile(seed, recommended_mode),
    }


def build_workspace_profile_rollout_plan(
    *,
    vault_root: str | Path | None = None,
    workspace_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a review-only plan for the first explicit WML profiles."""

    root = Path(vault_root).resolve() if vault_root is not None else _detect_vault_root()
    if workspace_path is None:
        seeds = DEFAULT_ROLLOUT_CANDIDATES
        scope = "default_first_profiles"
    else:
        seeds = (_seed_for_workspace_path(str(workspace_path)),)
        scope = "targeted_workspace"

    candidates = [_candidate_from_seed(seed, root) for seed in seeds]
    candidates.sort(key=lambda item: int(item["priority"]))
    profiles_missing = [item for item in candidates if not item["profile_present"]]

    return {
        "ok": True,
        "surface": "workspace_mode_profile_rollout_plan",
        "scope": scope,
        "preview_only": True,
        "profile_files_written": False,
        "aor_dispatch_enabled": False,
        "workflow_execution_performed": False,
        "agent_bus_task_written": False,
        "approval_consumed": False,
        "canonical_write_performed": False,
        "external_action_performed": False,
        "vault_root": str(root),
        "candidate_count": len(candidates),
        "profiles_missing_count": len(profiles_missing),
        "profiles_present_count": len(candidates) - len(profiles_missing),
        "candidates": candidates,
        "recommended_sequence": [
            item["profile_path"] for item in candidates if not item["profile_present"]
        ],
        "dispatch_gate_blockers": [
            "explicit_workspace_profiles_not_written_by_this_plan",
            "operator_review_required_before_profile_file_creation",
            "aor_dispatch_gate_not_implemented",
            "approval_consumption_not_connected_to_workspace_mode_dispatch",
        ],
        "acceptance_criteria_for_future_write_pass": [
            "operator selects candidate profile paths",
            "operator reviews proposed profile modes and workflow allowlists",
            "future writer blocks overwrites unless explicitly approved",
            "future writer validates each YAML profile before dispatch gate work",
            "route-preview remains blocked until explicit profiles exist",
        ],
        "next_recommended_pass": "workspace-mode-profile-draft-packet",
    }


def format_workspace_profile_rollout_plan(payload: dict[str, Any]) -> str:
    lines = [
        "Workspace Mode profile rollout plan",
        f"  scope:                {payload.get('scope')}",
        f"  candidate_count:      {payload.get('candidate_count')}",
        f"  profiles_missing:     {payload.get('profiles_missing_count')}",
        "  boundary: review only; no profile file write, AOR dispatch, Agent Bus task write, approval consumption, external action, or canonical writeback.",
        "  candidates:",
    ]
    for item in payload.get("candidates") or []:
        blockers = ", ".join(item.get("blockers") or []) or "(none)"
        lines.append(
            "    - "
            f"{item.get('profile_path')} "
            f"mode={item.get('recommended_mode')} "
            f"present={item.get('profile_present')} "
            f"priority={item.get('priority')} "
            f"blockers={blockers}"
        )
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m runtime.workspace_modes.profile_rollout_plan",
        description="Plan WML profile rollout without writing profile files.",
    )
    parser.add_argument("--workspace-path", default=None, metavar="PATH")
    parser.add_argument("--vault-root", default=None, metavar="PATH")
    parser.add_argument("--json", action="store_true", dest="output_json")
    args = parser.parse_args(argv)

    payload = build_workspace_profile_rollout_plan(
        vault_root=args.vault_root,
        workspace_path=args.workspace_path,
    )
    if args.output_json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_workspace_profile_rollout_plan(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
