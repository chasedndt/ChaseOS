"""Studio Standalone .exe Packaging Readiness.

Read-only verification surface that checks whether the ChaseOS Studio
standalone .exe packaging chain is ready for an operator build run.

Checks:
  1. PyInstaller spec file present (ChaseOS-Studio.spec)
  2. Build script present (build_exe.ps1)
  3. Frontend assets present (frontend/index.html, frontend/app.js)
  4. config.py MEIPASS path wired (studio_frontend lookup)
  5. PyWebView importable
  6. PyInstaller importable (soft — not a hard production blocker)

Read-only: no builds triggered, no files written, no vault mutations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.standalone_exe_packaging_readiness.v1"
SURFACE_ID = "studio_standalone_exe_packaging_readiness"
PASS_ID = "studio-standalone-exe-packaging-readiness"
NEXT_RECOMMENDED_PASS = "studio-product-hardening-complete"

# Paths relative to the shell directory
_SHELL_DIR = Path(__file__).parent / "shell"
_SPEC_FILE = _SHELL_DIR / "ChaseOS-Studio.spec"
_BUILD_SCRIPT = _SHELL_DIR / "build_exe.ps1"
_FRONTEND_DIR = _SHELL_DIR / "frontend"
_FRONTEND_INDEX = _FRONTEND_DIR / "index.html"
_FRONTEND_APP_JS = _FRONTEND_DIR / "app.js"
_FRONTEND_STYLES_CSS = _FRONTEND_DIR / "styles.css"
_CONFIG_PY = _SHELL_DIR / "config.py"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _check_spec_file() -> dict[str, Any]:
    exists = _SPEC_FILE.exists()
    size = _SPEC_FILE.stat().st_size if exists else None
    # Quick content probe — look for PyInstaller markers
    has_analysis = False
    has_meipass_path = False
    if exists:
        try:
            content = _SPEC_FILE.read_text(encoding="utf-8", errors="replace")
            has_analysis = "Analysis(" in content
            has_meipass_path = "studio_frontend" in content
        except OSError:
            pass
    return {
        "ok": exists and has_analysis and has_meipass_path,
        "path": str(_SPEC_FILE),
        "exists": exists,
        "size_bytes": size,
        "has_analysis_block": has_analysis,
        "has_meipass_path_wired": has_meipass_path,
    }


def _check_build_script() -> dict[str, Any]:
    exists = _BUILD_SCRIPT.exists()
    size = _BUILD_SCRIPT.stat().st_size if exists else None
    has_pyinstaller_call = False
    if exists:
        try:
            content = _BUILD_SCRIPT.read_text(encoding="utf-8", errors="replace")
            has_pyinstaller_call = "pyinstaller" in content.lower()
        except OSError:
            pass
    return {
        "ok": exists and has_pyinstaller_call,
        "path": str(_BUILD_SCRIPT),
        "exists": exists,
        "size_bytes": size,
        "has_pyinstaller_call": has_pyinstaller_call,
    }


def _check_frontend_assets() -> dict[str, Any]:
    index_ok = _FRONTEND_INDEX.exists()
    app_js_ok = _FRONTEND_APP_JS.exists()
    styles_ok = _FRONTEND_STYLES_CSS.exists()
    all_ok = index_ok and app_js_ok and styles_ok
    # Count bundleable assets
    asset_count = sum(1 for _ in _FRONTEND_DIR.rglob("*") if _.is_file()) if _FRONTEND_DIR.exists() else 0
    return {
        "ok": all_ok,
        "frontend_dir": str(_FRONTEND_DIR),
        "index_html_present": index_ok,
        "app_js_present": app_js_ok,
        "styles_css_present": styles_ok,
        "total_asset_count": asset_count,
    }


def _check_config_meipass_wired() -> dict[str, Any]:
    exists = _CONFIG_PY.exists()
    meipass_wired = False
    studio_frontend_path = False
    if exists:
        try:
            content = _CONFIG_PY.read_text(encoding="utf-8", errors="replace")
            meipass_wired = "_MEIPASS" in content
            studio_frontend_path = "studio_frontend" in content
        except OSError:
            pass
    return {
        "ok": exists and meipass_wired and studio_frontend_path,
        "config_py_exists": exists,
        "meipass_lookup_present": meipass_wired,
        "studio_frontend_path_wired": studio_frontend_path,
    }


def _check_pywebview_importable() -> dict[str, Any]:
    try:
        import webview  # noqa: F401
        version = getattr(webview, "__version__", "unknown")
        return {"ok": True, "version": version}
    except ImportError as exc:
        return {"ok": False, "error": str(exc)[:120]}


def _check_pyinstaller_importable() -> dict[str, Any]:
    """Soft check — PyInstaller is a build-time dep, not always installed in the dev venv."""
    try:
        import PyInstaller  # noqa: F401
        version = getattr(PyInstaller, "__version__", "unknown")
        return {"ok": True, "version": version, "note": "build-time dep present"}
    except ImportError:
        # Not a hard blocker — operators install it at build time via build_exe.ps1
        return {
            "ok": False,
            "error": "PyInstaller not installed in current env",
            "note": "build_exe.ps1 installs it automatically before building",
            "is_hard_blocker": False,
        }


def build_studio_standalone_exe_packaging_readiness() -> dict[str, Any]:
    """Verify ChaseOS Studio standalone .exe packaging chain readiness.

    Read-only: no builds triggered, no files written, no vault mutations.
    """
    spec = _check_spec_file()
    build_script = _check_build_script()
    frontend = _check_frontend_assets()
    config_meipass = _check_config_meipass_wired()
    pywebview = _check_pywebview_importable()
    pyinstaller = _check_pyinstaller_importable()

    # Hard blockers — static file checks; must pass for a successful build
    hard_checks: dict[str, bool] = {
        "spec_file_present_and_valid": spec["ok"],
        "build_script_present": build_script["ok"],
        "frontend_assets_present": frontend["ok"],
        "config_meipass_wired": config_meipass["ok"],
    }

    # Soft checks — build-time / runtime deps; advisory only
    # (pywebview is a desktop GUI dep — not always in the headless dev venv)
    soft_checks: dict[str, bool] = {
        "pywebview_importable": pywebview["ok"],
        "pyinstaller_importable": pyinstaller["ok"],
    }

    blocked_reasons: list[str] = []
    if not spec["ok"]:
        blocked_reasons.append("spec_file_missing_or_invalid")
    if not build_script["ok"]:
        blocked_reasons.append("build_script_missing_or_invalid")
    if not frontend["ok"]:
        blocked_reasons.append("frontend_assets_incomplete")
    if not config_meipass["ok"]:
        blocked_reasons.append("config_meipass_not_wired")

    operator_actions: list[str] = []
    if not pyinstaller["ok"]:
        operator_actions.append(
            "PyInstaller not installed — run build_exe.ps1 which installs it automatically, "
            "or: .venv/Scripts/pip install pyinstaller PyQt6 PyQt6-WebEngine qtpy"
        )
    if not pywebview["ok"]:
        operator_actions.append(
            "PyWebView not in dev venv — this is normal; build_exe.ps1 bundles it via PyInstaller. "
            "To install for local shell launch: .venv/Scripts/pip install pywebview==6.2.1"
        )

    hard_ok = all(hard_checks.values())

    if hard_ok and pyinstaller["ok"] and pywebview["ok"]:
        status = "BUILD READY — run build_exe.ps1 to produce ChaseOS-Studio.exe"
    elif hard_ok:
        status = "SPEC READY — run build_exe.ps1 (installs PyInstaller + bundles PyWebView automatically)"
    else:
        status = f"NOT READY — {len(blocked_reasons)} hard blocker(s): {', '.join(blocked_reasons[:3])}"

    return {
        "ok": True,  # the probe itself always succeeds
        "packaging_ready": hard_ok,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "status": status,
        "hard_checks": hard_checks,
        "soft_checks": soft_checks,
        "blocked_reasons": blocked_reasons,
        "operator_actions": operator_actions,
        "details": {
            "spec_file": spec,
            "build_script": build_script,
            "frontend_assets": frontend,
            "config_meipass": config_meipass,
            "pywebview": pywebview,
            "pyinstaller": pyinstaller,
        },
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "authority": {
            "read_only": True,
            "build_triggered": False,
            "files_written": False,
            "vault_mutations": False,
        },
    }
