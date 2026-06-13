"""Read-only temp and policy checks for packaged Studio WebView2 failures."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any

from runtime.studio.packaged_app_launch_smoke import _relative_to_vault


MODEL_VERSION = "studio.packaged_app_webview2_policy_check.v1"
SURFACE_ID = "studio_packaged_app_webview2_policy_check"
DEFAULT_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "webview2-policy-checks"
WEBVIEW2_DIAGNOSTIC_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "webview2-diagnostics"
DEFAULT_WORKSPACE_TEMP_ROOT = Path(".pytest_tmp_env") / "studio-webview2-policy-check" / "temp"
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
        raise ValueError("WebView2 policy-check report root must stay inside the vault workspace") from exc
    return root


def _latest_json(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _load_latest_webview2_diagnostic(vault: Path, report_path: str | Path | None = None) -> dict[str, Any]:
    selected = Path(report_path) if report_path else _latest_json(vault / WEBVIEW2_DIAGNOSTIC_REPORT_ROOT)
    if selected is None:
        return {
            "ok": False,
            "path": None,
            "artifact_present": False,
            "payload": None,
            "reason": "No WebView2 diagnostic report was found.",
        }
    selected = selected if selected.is_absolute() else vault / selected
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError:
        return {
            "ok": False,
            "path": str(selected),
            "artifact_present": True,
            "payload": None,
            "reason": "WebView2 diagnostic report must stay inside the vault workspace.",
        }
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "path": _relative_to_vault(vault, selected),
            "artifact_present": True,
            "payload": None,
            "reason": f"WebView2 diagnostic report could not be read: {exc}",
        }
    return {
        "ok": payload.get("surface") == "studio_packaged_app_webview2_diagnostic",
        "path": _relative_to_vault(vault, selected),
        "artifact_present": True,
        "payload": payload,
        "reason": "Latest WebView2 diagnostic report loaded.",
    }


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
        return {"ok": False, "returncode": None, "payload": {}, "stdout_tail": "", "stderr_tail": str(exc)[-4000:]}
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


def _detect_webview2_policies() -> dict[str, Any]:
    if platform.system().lower() != "windows":
        return {"platform": platform.system(), "policy_detected": False, "policies": [], "probe": None}
    script = r"""
$ErrorActionPreference = 'SilentlyContinue'
$roots = @(
  'HKLM:\SOFTWARE\Policies\Microsoft\Edge\WebView2',
  'HKLM:\SOFTWARE\WOW6432Node\Policies\Microsoft\Edge\WebView2',
  'HKCU:\SOFTWARE\Policies\Microsoft\Edge\WebView2'
)
$items = @()
foreach ($root in $roots) {
  if (Test-Path $root) {
    $props = Get-ItemProperty -LiteralPath $root
    $names = $props.PSObject.Properties | Where-Object {
      $_.Name -notmatch '^PS(ParentPath|ChildName|Drive|Provider|Path)$'
    }
    foreach ($item in $names) {
      $items += [pscustomobject]@{
        root = $root
        name = $item.Name
        value = [string]$item.Value
      }
    }
  }
}
@{
  policy_detected = ($items.Count -gt 0)
  policies = @($items)
} | ConvertTo-Json -Depth 5 -Compress
"""
    probe = _run_powershell_json(script)
    payload = probe.get("payload") or {}
    return {
        "platform": platform.system(),
        "policy_detected": bool(payload.get("policy_detected")),
        "policies": payload.get("policies") or [],
        "probe": probe,
    }


def _python_temp_probe(temp_root: Path) -> dict[str, Any]:
    temp_root.mkdir(parents=True, exist_ok=True)
    script = r"""
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

result = {"ok": False, "cleanup_ok": False}
created = None
try:
    tempdir = tempfile.gettempdir()
    root = Path(tempdir)
    for _ in range(100):
        candidate = root / f"chaseos-policy-check-{uuid.uuid4().hex[:8]}"
        try:
            os.mkdir(candidate)
            created = candidate
            break
        except FileExistsError:
            continue
    if created is None:
        raise FileExistsError(f"Could not create a unique temp child under {root}")
    marker = created / "probe.txt"
    marker.write_text("ok", encoding="utf-8")
    marker.unlink()
    shutil.rmtree(created)
    result.update({"ok": True, "cleanup_ok": True, "tempdir": tempdir, "created": str(created), "error": None})
except Exception as exc:
    result.update({"error": repr(exc), "tempdir": tempfile.gettempdir()})
print(json.dumps(result, sort_keys=True))
"""
    env = {**{key: str(temp_root) for key in TEMP_ENV_KEYS}}
    launch_env = {**os.environ.copy(), **env}
    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=10,
            env=launch_env,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "env": env, "payload": {}, "returncode": None, "stderr_tail": str(exc)[-4000:]}
    try:
        payload = json.loads((proc.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        payload = {}
    return {
        "ok": bool(payload.get("ok")) and proc.returncode == 0,
        "env": env,
        "payload": payload,
        "returncode": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-4000:],
        "stderr_tail": (proc.stderr or "")[-4000:],
    }


def _workspace_cleanup_error(stderr_tail: str, vault: Path) -> dict[str, Any]:
    text = stderr_tail or ""
    match = re.search(r"PermissionError:[^\n]*Access is denied: '([^']+)'", text)
    path = Path(match.group(1)) if match else None
    under_vault = False
    if path is not None:
        try:
            path.resolve().relative_to(vault)
            under_vault = True
        except OSError:
            under_vault = False
        except ValueError:
            under_vault = False
    return {
        "detected": "PermissionError" in text and "Access is denied" in text,
        "path": str(path) if path else None,
        "path_inside_vault": under_vault,
        "stderr_excerpt": text[-2000:],
    }


def build_packaged_app_webview2_policy_check(
    vault_root: str | Path,
    *,
    diagnostic_report_path: str | Path | None = None,
    workspace_temp_root: str | Path | None = None,
) -> dict[str, Any]:
    """Classify temp/profile/policy evidence without mutating host state."""

    vault = _vault_path(vault_root)
    latest = _load_latest_webview2_diagnostic(vault, diagnostic_report_path)
    payload = latest.get("payload") or {}
    workspace_temp = Path(workspace_temp_root) if workspace_temp_root else vault / DEFAULT_WORKSPACE_TEMP_ROOT
    if not workspace_temp.is_absolute():
        workspace_temp = (vault / workspace_temp).resolve()
    try:
        workspace_temp.relative_to(vault)
    except ValueError as exc:
        raise ValueError("WebView2 policy-check workspace temp root must stay inside the vault workspace") from exc

    system_temp = payload.get("system_temp") or {}
    probe_launch = payload.get("probe_launch") or {}
    visual_report = probe_launch.get("visual_qa_report") or {}
    launch = visual_report.get("launch") or {}
    stderr_tail = launch.get("stderr_tail") or ""
    runtime_error = launch.get("runtime_error") or {}
    cleanup_error = _workspace_cleanup_error(stderr_tail, vault)
    policy = _detect_webview2_policies()
    python_temp = _python_temp_probe(workspace_temp)

    blockers: list[str] = []
    if not latest.get("ok"):
        blockers.append(str(latest.get("reason") or "Latest WebView2 diagnostic report is invalid."))
    if not system_temp.get("writable"):
        blockers.append("System temp write probe is denied or unavailable.")
    if not python_temp.get("ok"):
        blockers.append("Workspace Python temp override probe cannot create and clean up a temp directory.")
    if cleanup_error.get("detected"):
        blockers.append("Packaged PyWebView launch stderr contains a temp cleanup PermissionError.")
    if policy.get("policy_detected"):
        blockers.append("WebView2 policy registry values are present and require operator review.")
    if runtime_error.get("blocked") and not blockers:
        blockers.append("Packaged WebView2 initialization still fails after temp and policy checks.")

    if not latest.get("ok"):
        status = "blocked_missing_webview2_diagnostic"
        next_pass = "pass10b-webview2-runtime-diagnostic"
    elif policy.get("policy_detected"):
        status = "blocked_webview2_policy_review_required"
        next_pass = "pass10b-webview2-policy-remediation-handoff"
    elif (not system_temp.get("writable")) and (not python_temp.get("ok")) and cleanup_error.get("detected"):
        status = "blocked_system_and_workspace_temp_permission"
        next_pass = "pass10b-workspace-temp-acl-cleanup-diagnostic"
    elif (not system_temp.get("writable")) and cleanup_error.get("detected"):
        status = "blocked_temp_permission_and_cleanup_error"
        next_pass = "pass10b-pywebview-temp-cleanup-diagnostic"
    elif not system_temp.get("writable"):
        status = "blocked_system_temp_permission"
        next_pass = "pass10b-system-temp-permission-handoff"
    elif cleanup_error.get("detected"):
        status = "blocked_workspace_temp_cleanup_permission"
        next_pass = "pass10b-pywebview-temp-cleanup-diagnostic"
    elif runtime_error.get("blocked"):
        status = "blocked_webview2_runtime_unexplained_after_temp_policy_check"
        next_pass = "pass10b-pywebview-webview2-minimal-repro"
    else:
        status = "webview2_temp_policy_check_clear"
        next_pass = "pass10b-native-visual-qa-rerun"

    checks = [
        {"name": "latest_webview2_diagnostic_loaded", "ok": bool(latest.get("ok")), "detail": latest.get("path")},
        {"name": "system_temp_writable", "ok": bool(system_temp.get("writable")), "detail": system_temp.get("error") or system_temp.get("path")},
        {"name": "workspace_python_temp_override_ok", "ok": bool(python_temp.get("ok")), "detail": (python_temp.get("payload") or {}).get("tempdir")},
        {"name": "workspace_temp_cleanup_permission_error_absent", "ok": not bool(cleanup_error.get("detected")), "detail": cleanup_error.get("path")},
        {"name": "webview2_policy_absent", "ok": not bool(policy.get("policy_detected")), "detail": len(policy.get("policies") or [])},
        {"name": "webview2_runtime_error_absent", "ok": not bool(runtime_error.get("blocked")), "detail": runtime_error.get("status")},
    ]

    return {
        "ok": status == "webview2_temp_policy_check_clear",
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "latest_webview2_diagnostic": {
            "path": latest.get("path"),
            "artifact_present": latest.get("artifact_present"),
            "status": payload.get("status"),
            "next_recommended_pass": payload.get("next_recommended_pass"),
        },
        "system_temp": system_temp,
        "workspace_temp_probe": {
            "root": _relative_to_vault(vault, workspace_temp),
            "python_temp_probe": python_temp,
        },
        "workspace_cleanup_error": cleanup_error,
        "webview2_policy": policy,
        "packaged_runtime_error": runtime_error,
        "checks": checks,
        "blockers": blockers,
        "authority": {
            "reads_webview2_diagnostic_report": True,
            "reads_webview2_policy_registry": platform.system().lower() == "windows",
            "creates_workspace_temp_probe_dir": True,
            "launches_packaged_executable": False,
            "captures_native_screenshot": False,
            "mutates_temp_acl": False,
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
        "next_recommended_pass": next_pass,
    }


def write_packaged_app_webview2_policy_check(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    report_slug: str | None = None,
    report_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _resolve_report_root(vault, report_root)
    slug = report_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-webview2-policy-check"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("WebView2 policy-check report output must stay inside the report root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    lines = [
        "# Studio Packaged App WebView2 Temp/Policy Check",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next recommended pass: {report.get('next_recommended_pass')}",
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
