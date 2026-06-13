"""Phase 10F4 ChaseOS bootstrap wizard preview.

This surface productizes the older Workspace Entry bootstrap plan as a
read-only setup preview. It models what a ChaseOS-native workspace bootstrap
would create, but it never creates folders/files or approval artifacts.
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.chaseos_bootstrap_wizard_preview.v1"
SURFACE_ID = "studio_chaseos_bootstrap_wizard_preview"
PASS_ID = "phase10f4-chaseos-bootstrap-wizard-preview"
NEXT_RECOMMENDED_PASS = "phase10f5-upgrade-plan-approval-packet"

REQUIRED_DIRS = [
    "00_HOME",
    "01_PROJECTS",
    "02_AREAS",
    "03_RESOURCES",
    "04_ARCHIVE",
    "05_RND",
    "06_AGENTS",
    "07_LOGS",
    "08_TEMPLATES",
    "99_ARCHIVE",
]

REQUIRED_FILES = [
    "README.md",
    "PROJECT_FOUNDATION.md",
    "ROADMAP.md",
    "CLAUDE.md",
    "00_HOME/Now.md",
    "00_HOME/Assistant-Contract.md",
    "06_AGENTS/Agent-Registry.md",
    "06_AGENTS/Vault-Map.md",
    "06_AGENTS/Permission-Matrix.md",
    "06_AGENTS/Trust-Tiers.md",
]

BOOTSTRAP_STEPS = [
    {
        "id": "select-target",
        "step": 1,
        "title": "Select target folder",
        "description": "Confirm the folder that would become the ChaseOS-native workspace root.",
        "creates": [],
    },
    {
        "id": "create-core-folders",
        "step": 2,
        "title": "Create core folders",
        "description": "Prepare the canonical ChaseOS folder skeleton.",
        "creates": REQUIRED_DIRS,
    },
    {
        "id": "write-anchor-docs",
        "step": 3,
        "title": "Write anchor docs",
        "description": "Create the minimum framework, roadmap, home, and agent-control anchors.",
        "creates": REQUIRED_FILES,
    },
    {
        "id": "scaffold-brain-draft",
        "step": 4,
        "title": "Generate scaffold brain draft",
        "description": "Produce a draft-only scaffold request for operator review.",
        "creates": ["runtime/scaffold/generated/brain-<workspace>/scaffold_request.json"],
    },
    {
        "id": "approval-packet",
        "step": 5,
        "title": "Prepare upgrade approval packet",
        "description": "Future pass only: package the planned writes for approval.",
        "creates": ["07_LOGS/Agent-Activity/_workspace_upgrade_approvals/<packet>.json"],
    },
    {
        "id": "execution-proof",
        "step": 6,
        "title": "Execute after approval",
        "description": "Future pass only: consume approval exactly once and write proof evidence.",
        "creates": ["07_LOGS/Studio-Graph-Views/<upgrade-proof>.json"],
    },
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_target(vault_root: str | Path, target_path: str | Path | None) -> tuple[Path, Path]:
    vault = Path(vault_root).resolve()
    target = Path(target_path).expanduser() if target_path is not None and str(target_path).strip() else vault
    if not target.is_absolute():
        target = vault / target
    return vault, target.resolve()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "my-chaseos-vault"


def _path_status(target: Path, rel_path: str) -> dict[str, Any]:
    path = target / rel_path
    return {
        "path": rel_path,
        "exists": path.exists(),
        "is_directory": path.is_dir() if path.exists() else False,
        "is_file": path.is_file() if path.exists() else False,
        "would_create": not path.exists(),
    }


def _target_state(target: Path) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    if target.exists() and not target.is_dir():
        blockers.append("target-path-is-not-a-directory")
        return "blocked_file_collision", blockers, warnings
    if not target.exists():
        if not target.parent.exists():
            blockers.append("target-parent-does-not-exist")
            return "blocked_missing_parent", blockers, warnings
        return "missing_ready_to_create", blockers, warnings

    entries = [item for item in target.iterdir() if item.name not in {".", ".."}]
    present_dirs = [rel for rel in REQUIRED_DIRS if (target / rel).is_dir()]
    present_files = [rel for rel in REQUIRED_FILES if (target / rel).is_file()]
    if len(present_dirs) == len(REQUIRED_DIRS) and len(present_files) >= 4:
        warnings.append("target-already-looks-chaseos-native")
        return "existing_chaseos_native", blockers, warnings
    if present_dirs or present_files:
        warnings.append("partial-chaseos-shape-present")
        return "existing_partial_chaseos", blockers, warnings
    if not entries:
        return "empty_directory", blockers, warnings
    warnings.append("non-empty-folder-preview-only")
    return "non_empty_unclassified", blockers, warnings


def _step_status(step: dict[str, Any], target: Path, target_state: str) -> dict[str, Any]:
    creates = [item.replace("<workspace>", _slugify(target.name)) for item in step.get("creates") or []]
    existing = [item for item in creates if (target / item).exists()]
    if target_state.startswith("blocked_"):
        status = "blocked"
    elif step["id"] in {"approval-packet", "execution-proof"}:
        status = "future_approval_required"
    elif creates and len(existing) == len(creates):
        status = "already_present"
    else:
        status = "would_create"
    return {
        **step,
        "creates": creates,
        "existing_paths": existing,
        "missing_paths": [item for item in creates if item not in existing],
        "status": status,
        "preview_only": True,
    }


def build_chaseos_bootstrap_wizard_preview(
    vault_root: str | Path,
    target_path: str | Path | None = None,
    workspace_name: str = "my-chaseos-vault",
) -> dict[str, Any]:
    """Return a read-only bootstrap preview for a ChaseOS workspace target."""

    vault, target = _resolve_target(vault_root, target_path)
    slug = _slugify(workspace_name or target.name)
    target_state, blockers, warnings = _target_state(target)
    folders = [_path_status(target, item) for item in REQUIRED_DIRS]
    files = [_path_status(target, item) for item in REQUIRED_FILES]
    steps = [_step_status(step, target, target_state) for step in BOOTSTRAP_STEPS]
    preview_ready = not blockers

    return {
        "ok": preview_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "COMPLETE / READ-ONLY / VERIFIED",
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Bootstrap Wizard Preview",
        "vault_root": str(vault),
        "target": {
            "requested_path": str(target_path) if target_path is not None else None,
            "resolved_path": str(target),
            "parent_path": str(target.parent),
            "exists": target.exists(),
            "parent_exists": target.parent.exists(),
            "is_directory": target.is_dir() if target.exists() else False,
            "state": target_state,
        },
        "workspace": {
            "name": workspace_name,
            "slug": slug,
            "launch_command_after_bootstrap": f"chaseos studio shell --vault-root \"{target}\"",
        },
        "scaffold_command_contract": {
            "previewed_command": f"chaseos scaffold brain \"{workspace_name}\" --json",
            "write_command_requires_future_approval": f"chaseos scaffold brain \"{workspace_name}\" --write --json",
            "command_family": "chaseos scaffold brain",
            "draft_only": True,
            "invoked_by_preview": False,
            "workspace_folder_execution_built": False,
        },
        "target_folders": {
            "required_count": len(REQUIRED_DIRS),
            "present_count": sum(1 for item in folders if item["exists"]),
            "missing_count": sum(1 for item in folders if not item["exists"]),
            "items": folders,
        },
        "target_files": {
            "required_count": len(REQUIRED_FILES),
            "present_count": sum(1 for item in files if item["exists"]),
            "missing_count": sum(1 for item in files if not item["exists"]),
            "items": files,
        },
        "steps": steps,
        "summary": {
            "preview_ready": preview_ready,
            "target_state": target_state,
            "total_steps": len(steps),
            "would_create_folder_count": sum(1 for item in folders if item["would_create"]),
            "would_create_file_count": sum(1 for item in files if item["would_create"]),
            "future_approval_step_count": sum(1 for item in steps if item["status"] == "future_approval_required"),
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
        },
        "readiness": {
            "ok": preview_ready,
            "chaseos_bootstrap_wizard_preview_ready": preview_ready,
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "approval_packet_required_for_execution": True,
            "bootstrap_execution_available": False,
            "upgrade_execution_available": False,
        },
        "authority_boundary": {
            "read_only": True,
            "preview_only": True,
            "writes_selected_folder": False,
            "writes_target_folders": False,
            "writes_target_files": False,
            "writes_vault": False,
            "writes_approval_artifacts": False,
            "writes_scaffold_artifacts": False,
            "invokes_scaffold_generator": False,
            "migration_writer_built": False,
            "upgrade_executor_built": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "workflow_execution_allowed": False,
            "agent_bus_task_writes_allowed": False,
            "gate_mutation_allowed": False,
            "git_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "allowed_actions": ["inspect-chaseos-bootstrap-wizard-preview"],
        "possible_writes": [],
        "future_passes": [
            "10F5-upgrade-plan-approval-packet",
            "10F6-approved-upgrade-execution-proof",
        ],
    }
