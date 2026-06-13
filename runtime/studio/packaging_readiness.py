"""Read-only Studio desktop packaging readiness contract."""

from __future__ import annotations

from pathlib import Path
import sys
import tomllib
from typing import Any


MODEL_VERSION = "studio.packaging_readiness.v1"
SURFACE_ID = "studio_packaging_readiness"
SPEC_PATH = Path("runtime") / "studio" / "packaging" / "chaseos-studio.spec"
FRONTEND_PACKAGE_DATA = "runtime.studio.shell"
REQUIRED_FRONTEND_FILES = (
    "index.html",
    "app.js",
    "styles.css",
    "inspectorTabs.js",
    "assets/cytoscape.min.js",
)
BLOCKED_AUTHORITY = {
    "builds_executable": False,
    "writes_installer": False,
    "writes_vault": False,
    "writes_host_startup": False,
    "mutates_gate": False,
    "grants_approvals": False,
    "executes_approval_decisions": False,
    "executes_workflows": False,
    "provider_calls_allowed": False,
    "connector_calls_allowed": False,
    "writes_agent_bus_tasks": False,
    "canonical_mutation_allowed": False,
}


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _load_pyproject(vault: Path) -> dict[str, Any]:
    pyproject = vault / "pyproject.toml"
    if not pyproject.is_file():
        return {}
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))


def _dependency_declared(pyproject: dict[str, Any], dependency_name: str) -> bool:
    project = pyproject.get("project") or {}
    candidates: list[str] = list(project.get("dependencies") or [])
    optional = project.get("optional-dependencies") or {}
    for values in optional.values():
        candidates.extend(values or [])
    needle = dependency_name.lower()
    return any(str(item).lower().startswith(needle) for item in candidates)


def _package_data_declared(pyproject: dict[str, Any]) -> bool:
    package_data = ((pyproject.get("tool") or {}).get("setuptools") or {}).get("package-data") or {}
    patterns = package_data.get(FRONTEND_PACKAGE_DATA) or []
    required_patterns = {
        "frontend/*.css",
        "frontend/*.html",
        "frontend/*.js",
        "frontend/assets/*.js",
    }
    return required_patterns.issubset(set(patterns))


def _frontend_dir_is_meipass_aware(vault: Path) -> bool:
    config_path = vault / "runtime" / "studio" / "shell" / "config.py"
    if not config_path.is_file():
        return False
    text = config_path.read_text(encoding="utf-8")
    return "_MEIPASS" in text and "studio_frontend" in text


def build_studio_packaging_readiness(vault_root: str | Path) -> dict[str, Any]:
    """Build a no-build packaging readiness contract for the native Studio shell."""

    vault = _vault_path(vault_root)
    pyproject = _load_pyproject(vault)
    frontend = vault / "runtime" / "studio" / "shell" / "frontend"
    spec = vault / SPEC_PATH
    frontend_files = [
        {
            "path": _relative_to_vault(vault, frontend / item),
            "exists": (frontend / item).is_file(),
        }
        for item in REQUIRED_FRONTEND_FILES
    ]
    pywebview_declared = _dependency_declared(pyproject, "pywebview")
    pyinstaller_declared = _dependency_declared(pyproject, "pyinstaller")
    package_data_declared = _package_data_declared(pyproject)
    meipass_aware = _frontend_dir_is_meipass_aware(vault)
    local_shell_entry = (vault / "runtime" / "studio" / "shell" / "main.py").is_file()
    api_entry = (vault / "runtime" / "studio" / "shell" / "api.py").is_file()
    spec_available = spec.is_file()

    readiness = {
        "native_shell_primary": True,
        "legacy_localhost_harness_secondary": True,
        "local_shell_entry_exists": local_shell_entry,
        "studio_api_entry_exists": api_entry,
        "frontend_assets_local": all(item["exists"] for item in frontend_files),
        "frontend_package_data_declared": package_data_declared,
        "pywebview_dependency_declared": pywebview_declared,
        "pyinstaller_dependency_declared": pyinstaller_declared,
        "pyinstaller_spec_available": spec_available,
        "pyinstaller_frontend_resolution_supported": meipass_aware,
        "local_packaging_proof_run": False,
        "installer_built": False,
    }
    static_ready = all(
        readiness[key]
        for key in [
            "native_shell_primary",
            "legacy_localhost_harness_secondary",
            "local_shell_entry_exists",
            "studio_api_entry_exists",
            "frontend_assets_local",
            "frontend_package_data_declared",
            "pywebview_dependency_declared",
            "pyinstaller_dependency_declared",
            "pyinstaller_spec_available",
            "pyinstaller_frontend_resolution_supported",
        ]
    )
    blockers: list[str] = []
    if not pywebview_declared:
        blockers.append("pywebview dependency is not declared for Studio shell runtime.")
    if not pyinstaller_declared:
        blockers.append("PyInstaller dependency is not declared for local packaging proof.")
    if not package_data_declared:
        blockers.append("Studio frontend package data is not declared for installed package layouts.")
    if not meipass_aware:
        blockers.append("Studio frontend path resolution is not PyInstaller _MEIPASS aware.")
    if not spec_available:
        blockers.append("PyInstaller spec is missing.")
    if not readiness["frontend_assets_local"]:
        blockers.append("One or more local Studio frontend assets is missing.")

    return {
        "ok": static_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": "ready_for_local_packaging_proof" if static_ready else "blocked_static_packaging_readiness",
        "vault_root": str(vault),
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
        },
        "product_lane": {
            "primary": "native_pywebview_shell",
            "primary_command": "chaseos studio shell",
            "secondary_qa_harness": "chaseos studio desktop-shell-app",
            "localhost_mock_is_product_target": False,
        },
        "packaging_target": {
            "app_name": "ChaseOS Studio",
            "entry_script": "runtime/studio/shell/main.py",
            "spec_path": _relative_to_vault(vault, spec),
            "dist_exe": "dist/ChaseOS-Studio/ChaseOS-Studio.exe",
            "onefile": False,
        },
        "frontend": {
            "directory": _relative_to_vault(vault, frontend),
            "required_files": frontend_files,
            "package_data_declared": package_data_declared,
            "pyinstaller_meipass_resolution": meipass_aware,
        },
        "dependencies": {
            "pywebview_declared": pywebview_declared,
            "pyinstaller_declared": pyinstaller_declared,
            "declared_as_optional_packaging_extra": bool(
                ((pyproject.get("project") or {}).get("optional-dependencies") or {}).get("studio-packaging")
            ),
        },
        "readiness": readiness,
        "authority": BLOCKED_AUTHORITY,
        "blocked_authority": [key for key, value in BLOCKED_AUTHORITY.items() if value is False],
        "blockers": blockers,
        "unverified": [
            "PyInstaller build was not executed in this read-only readiness pass.",
            "Generated executable launch was not tested.",
            "Installer creation/signing was not attempted.",
            "Native PyWebView GUI was not launched by this contract.",
        ],
        "next_recommended_pass": "studio-local-packaging-proof",
    }
