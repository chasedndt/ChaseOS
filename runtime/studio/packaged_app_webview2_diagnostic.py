"""Bounded WebView2 diagnostics for the packaged ChaseOS Studio executable."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import importlib.util
import json
import os
import platform
from pathlib import Path
import subprocess
import tempfile
from typing import Any
import uuid

from runtime.studio.packaged_app_launch_smoke import (
    DEFAULT_EXE,
    _relative_to_vault,
    _resolve_executable,
)
from runtime.studio.packaged_app_visual_qa import build_packaged_app_visual_qa
from runtime.studio.packaging_proof import _sha256, build_studio_local_packaging_proof


MODEL_VERSION = "studio.packaged_app_webview2_diagnostic.v1"
SURFACE_ID = "studio_packaged_app_webview2_diagnostic"
DEFAULT_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "webview2-diagnostics"
DEFAULT_PROBE_ROOT = Path(".pytest_tmp_env") / "studio-webview2-diagnostic"
WEBVIEW2_USER_DATA_ENV = "WEBVIEW2_USER_DATA_FOLDER"
TEMP_ENV_KEYS = ("TEMP", "TMP", "TMPDIR")


def _hidden_subprocess_creationflags() -> int:
    if os.name != "nt":
        return 0
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _resolve_report_root(vault: Path, report_root: str | Path | None) -> Path:
    root_input = Path(report_root) if report_root else DEFAULT_REPORT_ROOT
    root = root_input if root_input.is_absolute() else vault / root_input
    root = root.resolve()
    try:
        root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("WebView2 diagnostic report root must stay inside the vault workspace") from exc
    return root


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _package_version(package_name: str) -> str | None:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _path_write_probe(path: Path) -> dict[str, Any]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        marker = path / ".chaseos-write-probe"
        marker.write_text("ok", encoding="utf-8")
        marker.unlink()
        return {"path": str(path), "writable": True, "error": None}
    except OSError as exc:
        return {"path": str(path), "writable": False, "error": str(exc)}


def _temp_write_probe() -> dict[str, Any]:
    root = Path(tempfile.gettempdir())
    path: Path | None = None
    try:
        for _ in range(100):
            candidate = root / f"chaseos-webview2-diagnostic-{uuid.uuid4().hex[:8]}"
            try:
                os.mkdir(candidate)
                path = candidate
                break
            except FileExistsError:
                continue
        if path is None:
            raise FileExistsError(f"Could not create a unique temp child under {root}")
        marker = path / "probe.txt"
        marker.write_text("ok", encoding="utf-8")
        marker.unlink()
        path.rmdir()
        return {"path": str(path), "writable": True, "cleanup_ok": True, "error": None}
    except OSError as exc:
        return {"path": None, "writable": False, "cleanup_ok": False, "error": str(exc)}


def _run_powershell_json(script: str, *, timeout_seconds: float = 10.0) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            creationflags=_hidden_subprocess_creationflags(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "returncode": None,
            "payload": {},
            "stdout_tail": "",
            "stderr_tail": str(exc)[-4000:],
        }
    payload: dict[str, Any] = {}
    try:
        payload = json.loads((proc.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        payload = {}
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "payload": payload,
        "stdout_tail": (proc.stdout or "")[-4000:],
        "stderr_tail": (proc.stderr or "")[-4000:],
    }


def _detect_windows_webview2_runtime() -> dict[str, Any]:
    if platform.system().lower() != "windows":
        return {
            "platform": platform.system(),
            "runtime_detected": False,
            "status": "not_windows",
            "registry_clients": [],
            "runtime_files": [],
            "probe": None,
        }

    script = r"""
$ErrorActionPreference = 'SilentlyContinue'
$registryRoots = @(
  'HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients',
  'HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients',
  'HKCU:\SOFTWARE\Microsoft\EdgeUpdate\Clients'
)
$clients = @()
foreach ($root in $registryRoots) {
  if (Test-Path $root) {
    Get-ChildItem -LiteralPath $root | ForEach-Object {
      $props = Get-ItemProperty -LiteralPath $_.PsPath
      $name = [string]$props.name
      $pv = [string]$props.pv
      if ($name -match 'WebView2' -or $_.PSChildName -match 'WebView2') {
        $clients += [pscustomobject]@{
          root = $root
          id = $_.PSChildName
          name = $name
          version = $pv
        }
      }
    }
  }
}
$runtimeFiles = @()
$patterns = @(
  "$env:ProgramFiles(x86)\Microsoft\EdgeWebView\Application\*\msedgewebview2.exe",
  "$env:ProgramFiles\Microsoft\EdgeWebView\Application\*\msedgewebview2.exe",
  "$env:LOCALAPPDATA\Microsoft\EdgeWebView\Application\*\msedgewebview2.exe"
)
foreach ($pattern in $patterns) {
  Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | ForEach-Object {
    $runtimeFiles += [pscustomobject]@{
      path = $_.FullName
      version = $_.Directory.Name
      length = $_.Length
    }
  }
}
@{
  runtime_detected = (($clients.Count -gt 0) -or ($runtimeFiles.Count -gt 0))
  registry_clients = @($clients)
  runtime_files = @($runtimeFiles)
} | ConvertTo-Json -Depth 5 -Compress
"""
    probe = _run_powershell_json(script)
    payload = probe.get("payload") or {}
    detected = bool(payload.get("runtime_detected"))
    return {
        "platform": platform.system(),
        "runtime_detected": detected,
        "status": "detected" if detected else "not_detected",
        "registry_clients": payload.get("registry_clients") or [],
        "runtime_files": payload.get("runtime_files") or [],
        "probe": probe,
    }


def build_packaged_app_webview2_diagnostic(
    vault_root: str | Path,
    *,
    executable_path: str | Path | None = None,
    probe_launch: bool = False,
    settle_seconds: float = 8.0,
    window_timeout_seconds: float = 15.0,
    terminate_timeout_seconds: float = 5.0,
    user_data_root: str | Path | None = None,
) -> dict[str, Any]:
    """Diagnose WebView2 runtime posture without mutating host policy."""

    vault = _vault_path(vault_root)
    exe = _resolve_executable(vault, executable_path or DEFAULT_EXE)
    packaging_proof = build_studio_local_packaging_proof(vault)
    pywebview_available = _module_available("webview")
    pywebview_version = _package_version("pywebview")
    webview2 = _detect_windows_webview2_runtime()
    probe_root = Path(user_data_root) if user_data_root else vault / DEFAULT_PROBE_ROOT / "user-data"
    if not probe_root.is_absolute():
        probe_root = (vault / probe_root).resolve()
    try:
        probe_root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("WebView2 diagnostic user-data root must stay inside the vault workspace") from exc

    workspace_user_data_probe = _path_write_probe(probe_root)
    workspace_temp_root = vault / DEFAULT_PROBE_ROOT / "temp"
    workspace_temp_probe = _path_write_probe(workspace_temp_root)
    temp_probe = _temp_write_probe()
    visual_probe: dict[str, Any] | None = None
    if probe_launch:
        probe_env = {WEBVIEW2_USER_DATA_ENV: str(probe_root)}
        probe_env.update({key: str(workspace_temp_root) for key in TEMP_ENV_KEYS})
        visual_probe = build_packaged_app_visual_qa(
            vault,
            executable_path=exe,
            screenshot_path=vault / DEFAULT_PROBE_ROOT / "workspace-user-data-probe.png",
            env_overrides=probe_env,
            settle_seconds=settle_seconds,
            window_timeout_seconds=window_timeout_seconds,
            terminate_timeout_seconds=terminate_timeout_seconds,
        )

    blockers: list[str] = []
    if not exe.is_file():
        blockers.append("Packaged Studio executable is missing.")
    if not (packaging_proof.get("outputs") or {}).get("executable_exists"):
        blockers.append("Local packaging proof does not currently see a generated executable.")
    if not pywebview_available:
        blockers.append("pywebview is not installed in the active Python environment.")
    if platform.system().lower() == "windows" and not webview2.get("runtime_detected"):
        blockers.append("WebView2 runtime was not detected by registry/file probe.")
    if not workspace_user_data_probe.get("writable"):
        blockers.append("Workspace-owned WebView2 user-data folder is not writable.")
    if not workspace_temp_probe.get("writable"):
        blockers.append("Workspace-owned temp folder is not writable.")
    if visual_probe:
        runtime_error = ((visual_probe.get("launch") or {}).get("runtime_error") or {})
        if runtime_error.get("blocked"):
            blockers.append("WebView2 initialization still fails with workspace-owned WebView2 user-data and temp folders.")

    visual_ok = bool(visual_probe and visual_probe.get("ok"))
    runtime_blocked = bool(
        visual_probe
        and (((visual_probe.get("launch") or {}).get("runtime_error") or {}).get("blocked"))
    )
    if visual_ok:
        status = "webview2_diagnostic_visual_qa_ready"
        next_recommended_pass = "pass10b-native-visual-qa-rerun"
    elif runtime_blocked:
        status = "blocked_webview2_initialization_with_workspace_runtime_dirs"
        next_recommended_pass = "pass10b-system-temp-permission-or-webview2-policy-check"
    elif not probe_launch and not blockers:
        status = "webview2_static_diagnostic_ready_for_launch_probe"
        next_recommended_pass = "pass10b-webview2-user-data-launch-probe"
    elif blockers:
        status = "blocked_webview2_diagnostic"
        next_recommended_pass = (
            "pass10b-install-or-repair-webview2-runtime"
            if any("WebView2 runtime was not detected" in item for item in blockers)
            else "pass10b-webview2-runtime-diagnostic"
        )
    else:
        status = "webview2_diagnostic_window_capture_followup"
        next_recommended_pass = "pass10b-webview2-window-capture-diagnostic"

    checks = [
        {"name": "packaged_executable_exists", "ok": exe.is_file(), "detail": _relative_to_vault(vault, exe)},
        {
            "name": "packaging_proof_executable_seen",
            "ok": bool((packaging_proof.get("outputs") or {}).get("executable_exists")),
            "detail": (packaging_proof.get("status") or "unknown"),
        },
        {"name": "pywebview_available", "ok": pywebview_available, "detail": pywebview_version},
        {"name": "webview2_runtime_detected", "ok": bool(webview2.get("runtime_detected")), "detail": webview2.get("status")},
        {"name": "workspace_user_data_writable", "ok": bool(workspace_user_data_probe.get("writable")), "detail": _relative_to_vault(vault, probe_root)},
        {"name": "workspace_temp_writable", "ok": bool(workspace_temp_probe.get("writable")), "detail": _relative_to_vault(vault, workspace_temp_root)},
        {"name": "system_temp_writable", "ok": bool(temp_probe.get("writable")), "detail": temp_probe.get("error") or temp_probe.get("path")},
        {"name": "workspace_user_data_probe_performed", "ok": bool(probe_launch), "detail": str(bool(probe_launch))},
        {
            "name": "workspace_user_data_probe_webview2_initialized",
            "ok": bool(visual_probe and not (((visual_probe.get("launch") or {}).get("runtime_error") or {}).get("blocked"))),
            "detail": (((visual_probe or {}).get("launch") or {}).get("runtime_error") or {}).get("status"),
        },
        {
            "name": "workspace_user_data_probe_visual_qa_complete",
            "ok": visual_ok,
            "detail": (visual_probe or {}).get("status"),
        },
    ]

    return {
        "ok": visual_ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "executable": {
            "path": _relative_to_vault(vault, exe),
            "exists": exe.is_file(),
            "sha256": _sha256(exe) if exe.is_file() else None,
        },
        "dependencies": {
            "pywebview_available": pywebview_available,
            "pywebview_version": pywebview_version,
        },
        "webview2_runtime": webview2,
        "workspace_user_data": workspace_user_data_probe,
        "workspace_temp": workspace_temp_probe,
        "system_temp": temp_probe,
        "probe_launch": {
            "requested": bool(probe_launch),
            "env": {
                WEBVIEW2_USER_DATA_ENV: _relative_to_vault(vault, probe_root),
                **{key: _relative_to_vault(vault, workspace_temp_root) for key in TEMP_ENV_KEYS},
            },
            "visual_qa_report": visual_probe,
        },
        "checks": checks,
        "blockers": blockers,
        "authority": {
            "detects_webview2_runtime": True,
            "creates_workspace_user_data_probe_dir": True,
            "launches_packaged_executable": bool(probe_launch),
            "captures_native_screenshot": bool(visual_probe and ((visual_probe.get("screenshot") or {}).get("exists"))),
            "mutates_host_policy": False,
            "installs_webview2": False,
            "signs_executable": False,
            "allowlists_executable": False,
            "writes_installer": False,
            "writes_host_startup": False,
            "grants_approvals": False,
            "executes_approval_decisions": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": False,
            "canonical_mutation_allowed": False,
        },
        "unverified": [
            "No WebView2 runtime install or repair was attempted.",
            "No host policy, signing, allowlisting, installer, startup, approval, provider, connector, Agent Bus, or canonical mutation was attempted.",
            "Native screenshot proof remains unverified unless the embedded visual-QA probe is complete.",
        ],
        "next_recommended_pass": next_recommended_pass,
    }


def write_packaged_app_webview2_diagnostic(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    report_slug: str | None = None,
    report_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _resolve_report_root(vault, report_root)
    slug = report_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-webview2-diagnostic"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("WebView2 diagnostic report output must stay inside the report root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    lines = [
        "# Studio Packaged App WebView2 Diagnostic",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next recommended pass: {report.get('next_recommended_pass')}",
        "",
        "## Executable",
        "",
        f"- Path: {(report.get('executable') or {}).get('path')}",
        f"- Exists: {(report.get('executable') or {}).get('exists')}",
        f"- SHA-256: {(report.get('executable') or {}).get('sha256')}",
        "",
        "## Checks",
        "",
        *[f"- {item.get('name')}: {item.get('ok')} - {item.get('detail')}" for item in report.get("checks") or []],
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in (report.get("blockers") or ["None"])],
        "",
        "## Authority",
        "",
        *[f"- {key}: {value}" for key, value in (report.get("authority") or {}).items()],
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
