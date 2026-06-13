"""runtime.scaffold.generator — bounded Phase 9 scaffold-generator foothold.

Generates draft-only scaffold artifacts under runtime/scaffold/generated/
without mutating canonical vault/project truth directly.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from runtime.config.store import load_config_store


def _detect_vault_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / "CLAUDE.md").exists():
            return candidate
    raise FileNotFoundError("Could not locate ChaseOS vault root (CLAUDE.md not found)")



def _resolve_vault_root(vault_root: Optional[Path] = None) -> Path:
    return Path(vault_root) if vault_root else _detect_vault_root()



def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "unnamed"



def _scaffold_root(vault_root: Path, scaffold_type: str, slug: str) -> Path:
    return vault_root / "runtime" / "scaffold" / "generated" / f"{scaffold_type}-{slug}"



def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")



def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")



def _project_target_path(vault_root: Path, slug: str) -> Path:
    config = load_config_store(vault_root=vault_root)
    project_root = config.get("scaffold_defaults", {}).get("project_root") or "01_PROJECTS"
    return vault_root / str(project_root) / slug



def _workspace_target_path(vault_root: Path, slug: str) -> Path:
    config = load_config_store(vault_root=vault_root)
    workspace_root = config.get("scaffold_defaults", {}).get("workspace_root") or "runtime/source_intelligence/workspaces"
    return vault_root / str(workspace_root) / slug


def _brain_target_path(vault_root: Path, slug: str) -> Path:
    config = load_config_store(vault_root=vault_root)
    brain_root = config.get("scaffold_defaults", {}).get("brain_root") or "runtime/scaffold/brain_targets"
    return vault_root / str(brain_root) / slug



def generate_scaffold(scaffold_type: str, name: str, *, vault_root: Optional[Path] = None, write: bool = True) -> dict[str, Any]:
    resolved_root = _resolve_vault_root(vault_root)
    slug = _slugify(name)
    if scaffold_type not in {"project", "workspace", "brain"}:
        raise ValueError(f"Unsupported scaffold_type: {scaffold_type}")

    root = _scaffold_root(resolved_root, scaffold_type, slug)
    artifacts_root = root / "artifacts"
    request_path = root / "scaffold_request.json"
    artifact_paths: list[str] = []

    if scaffold_type == "project":
        target_path = _project_target_path(resolved_root, slug)
        project_note = artifacts_root / target_path.relative_to(resolved_root) / f"{name.replace(' ', '-')}-OS.draft.md"
        workflow_manifest = artifacts_root / "runtime" / "workflows" / "registry" / f"{slug}_scaffold_draft.yaml"
        if write:
            payload = {
                "scaffold_type": scaffold_type,
                "name": name,
                "slug": slug,
                "draft_only": True,
                "target_path": str(target_path),
            }
            _write_json(request_path, payload)
            _write_text(
                project_note,
                f"---\ntitle: {name} OS Draft\nstatus: draft\nsource: scaffold-generator\n---\n\n# {name} OS Draft\n\n- Draft-only scaffold artifact.\n",
            )
            _write_text(
                workflow_manifest,
                f"id: {slug}_scaffold_draft\nstatus: draft\nruntime_adapter: openclaw\ntask_type: scaffold-draft\nwriteback_targets:\n  - runtime/scaffold/generated/\n",
            )
        artifact_paths = [str(project_note), str(workflow_manifest)]
    elif scaffold_type == "workspace":
        target_path = _workspace_target_path(resolved_root, slug)
        workspace_payload_path = artifacts_root / target_path.relative_to(resolved_root) / "workspace.draft.json"
        if write:
            payload = {
                "scaffold_type": scaffold_type,
                "name": name,
                "slug": slug,
                "draft_only": True,
                "target_path": str(target_path),
            }
            _write_json(request_path, payload)
            _write_json(
                workspace_payload_path,
                {
                    "workspace_id": slug,
                    "display_name": name,
                    "status": "draft",
                    "source": "scaffold-generator",
                    "notes": "Draft-only workspace scaffold artifact.",
                },
            )
        artifact_paths = [str(workspace_payload_path)]
    else:
        target_path = _brain_target_path(resolved_root, slug)
        brain_payload_path = artifacts_root / target_path.relative_to(resolved_root) / "brain.draft.json"
        if write:
            payload = {
                "scaffold_type": scaffold_type,
                "name": name,
                "slug": slug,
                "draft_only": True,
                "target_path": str(target_path),
            }
            _write_json(request_path, payload)
            _write_json(
                brain_payload_path,
                {
                    "workspace_id": slug,
                    "display_name": name,
                    "status": "draft",
                    "source": "scaffold-generator",
                    "notes": "Draft-only ChaseOS brain bootstrap artifact. Does not create a workspace root.",
                    "required_dirs": [
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
                    ],
                    "requires_future_approval_packet": True,
                },
            )
        artifact_paths = [str(brain_payload_path)]

    if not write:
        root.mkdir(parents=True, exist_ok=True)
        _write_json(
            request_path,
            {
                "scaffold_type": scaffold_type,
                "name": name,
                "slug": slug,
                "draft_only": True,
                "target_path": str(target_path),
                "write": False,
            },
        )

    return {
        "scaffold_type": scaffold_type,
        "kind": scaffold_type,
        "name": name,
        "slug": slug,
        "write": bool(write),
        "draft_only": True,
        "target_path": str(target_path),
        "scaffold_root": str(root),
        "artifact_paths": artifact_paths,
    }



def scaffold_project(name: str, *, vault_root: Optional[Path] = None, write: bool = False) -> dict[str, Any]:
    return generate_scaffold("project", name, vault_root=vault_root, write=write)



def scaffold_workspace(name: str, *, vault_root: Optional[Path] = None, write: bool = False) -> dict[str, Any]:
    return generate_scaffold("workspace", name, vault_root=vault_root, write=write)


def scaffold_brain(name: str, *, vault_root: Optional[Path] = None, write: bool = False) -> dict[str, Any]:
    return generate_scaffold("brain", name, vault_root=vault_root, write=write)
