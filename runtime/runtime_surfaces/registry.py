"""Read-only registry loader for Adaptive Runtime Surface Layer manifests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.runtime_surfaces.models import RuntimeSurfaceError, RuntimeSurfaceManifest

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


MANIFESTS_RELATIVE_PATH = Path("runtime/runtime_surfaces/manifests")
SCHEMA_RELATIVE_PATH = Path("runtime/runtime_surfaces/schemas/runtime_surface_manifest.schema.json")


@dataclass(frozen=True)
class RuntimeSurfaceRegistry:
    """In-memory read-only collection of validated runtime surface manifests."""

    manifests_by_id: dict[str, RuntimeSurfaceManifest]

    def list_surfaces(self) -> list[RuntimeSurfaceManifest]:
        return [self.manifests_by_id[surface_id] for surface_id in sorted(self.manifests_by_id)]

    def get_surface(self, surface_id: str) -> RuntimeSurfaceManifest:
        try:
            return self.manifests_by_id[surface_id]
        except KeyError as exc:
            raise RuntimeSurfaceError(f"Unknown runtime surface: {surface_id}") from exc

    def surfaces_for_capability(self, capability_id: str) -> list[RuntimeSurfaceManifest]:
        return [
            manifest
            for manifest in self.list_surfaces()
            if capability_id in manifest.capability_ids()
        ]

    def capabilities_by_risk(self, risk_class: str) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for manifest in self.list_surfaces():
            matches = [
                capability.capability_id
                for capability in manifest.capabilities
                if capability.risk_class == risk_class
            ]
            if matches:
                result[manifest.surface_id] = matches
        return result


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def manifest_root(vault_root: str | Path | None = None) -> Path:
    root = Path(vault_root) if vault_root is not None else _repo_root()
    return root / MANIFESTS_RELATIVE_PATH


def schema_path(vault_root: str | Path | None = None) -> Path:
    root = Path(vault_root) if vault_root is not None else _repo_root()
    return root / SCHEMA_RELATIVE_PATH


def load_surface_manifest(
    path: str | Path,
    *,
    vault_root: str | Path | None = None,
    require_files: bool = True,
) -> RuntimeSurfaceManifest:
    manifest_path = Path(path)
    if not manifest_path.is_absolute():
        root = Path(vault_root) if vault_root is not None else _repo_root()
        manifest_path = root / manifest_path
    data = _load_mapping(manifest_path)
    root = Path(vault_root) if vault_root is not None else _repo_root()
    return RuntimeSurfaceManifest.from_dict(
        data,
        source_path=manifest_path,
        vault_root=root,
        require_files=require_files,
    )


def load_runtime_surface_registry(
    vault_root: str | Path | None = None,
    *,
    manifests_dir: str | Path | None = None,
    require_files: bool = True,
) -> RuntimeSurfaceRegistry:
    root = Path(vault_root) if vault_root is not None else _repo_root()
    directory = Path(manifests_dir) if manifests_dir is not None else manifest_root(root)
    if not directory.is_absolute():
        directory = root / directory
    if not directory.is_dir():
        raise RuntimeSurfaceError(f"Runtime surface manifest directory missing: {directory}")

    manifests_by_id: dict[str, RuntimeSurfaceManifest] = {}
    for path in sorted(list(directory.glob("*.yaml")) + list(directory.glob("*.yml")) + list(directory.glob("*.json"))):
        manifest = load_surface_manifest(path, vault_root=root, require_files=require_files)
        if manifest.surface_id in manifests_by_id:
            raise RuntimeSurfaceError(f"duplicate runtime surface id: {manifest.surface_id}")
        manifests_by_id[manifest.surface_id] = manifest
    if not manifests_by_id:
        raise RuntimeSurfaceError(f"Runtime surface manifest directory is empty: {directory}")
    return RuntimeSurfaceRegistry(manifests_by_id=manifests_by_id)


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeSurfaceError(f"Runtime surface manifest missing: {path}") from exc

    try:
        payload = yaml.safe_load(text) if yaml is not None else json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeSurfaceError(f"Runtime surface manifest is invalid JSON/YAML: {path}: {exc}") from exc
    except Exception as exc:
        raise RuntimeSurfaceError(f"Runtime surface manifest is invalid YAML: {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeSurfaceError(f"Runtime surface manifest must be an object: {path}")
    return payload
