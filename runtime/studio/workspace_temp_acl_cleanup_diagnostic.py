"""Read-only workspace temp ACL and cleanup diagnostics for Pass 10B."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
from typing import Any
import uuid

from runtime.studio.packaged_app_launch_smoke import _relative_to_vault


MODEL_VERSION = "studio.workspace_temp_acl_cleanup_diagnostic.v1"
SURFACE_ID = "studio_workspace_temp_acl_cleanup_diagnostic"
DEFAULT_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "workspace-temp-acl-cleanup-diagnostics"
WEBVIEW2_POLICY_CHECK_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "webview2-policy-checks"
DEFAULT_PROBE_ROOT = Path(".pytest_tmp_env") / "studio-workspace-temp-acl-cleanup-diagnostic" / "probes"
DEFAULT_TEMP_ROOTS = (
    Path(".pytest_tmp_env") / "studio-webview2-policy-check" / "temp",
    Path(".pytest_tmp_env") / "studio-webview2-diagnostic" / "temp",
)


def _hidden_subprocess_creationflags() -> int:
    if os.name != "nt":
        return 0
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _resolve_inside_vault(vault: Path, path: str | Path, *, label: str) -> Path:
    selected = Path(path)
    if not selected.is_absolute():
        selected = vault / selected
    selected = selected.resolve()
    try:
        selected.relative_to(vault)
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside the vault workspace") from exc
    return selected


def _resolve_report_root(vault: Path, report_root: str | Path | None) -> Path:
    root_input = Path(report_root) if report_root else DEFAULT_REPORT_ROOT
    root = root_input if root_input.is_absolute() else vault / root_input
    root = root.resolve()
    try:
        root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("Workspace temp diagnostic report root must stay inside the vault workspace") from exc
    return root


def _latest_json(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _load_latest_policy_check(vault: Path, report_path: str | Path | None = None) -> dict[str, Any]:
    selected = Path(report_path) if report_path else _latest_json(vault / WEBVIEW2_POLICY_CHECK_REPORT_ROOT)
    if selected is None:
        return {
            "ok": False,
            "path": None,
            "artifact_present": False,
            "payload": None,
            "reason": "No WebView2 temp/policy check report was found.",
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
            "reason": "WebView2 temp/policy check report must stay inside the vault workspace.",
        }
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "path": _relative_to_vault(vault, selected),
            "artifact_present": True,
            "payload": None,
            "reason": f"WebView2 temp/policy check report could not be read: {exc}",
        }
    return {
        "ok": payload.get("surface") == "studio_packaged_app_webview2_policy_check",
        "path": _relative_to_vault(vault, selected),
        "artifact_present": True,
        "payload": payload,
        "reason": "Latest WebView2 temp/policy check report loaded.",
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


def _path_snapshot(vault: Path, path: Path, *, max_children: int = 25) -> dict[str, Any]:
    info: dict[str, Any] = {
        "path": _relative_to_vault(vault, path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
        "readable": os.access(path, os.R_OK) if path.exists() else False,
        "writable": os.access(path, os.W_OK) if path.exists() else False,
        "executable": os.access(path, os.X_OK) if path.exists() else False,
        "stat_ok": False,
        "mode": None,
        "readonly": None,
        "child_count": None,
        "children_sample": [],
        "error": None,
    }
    try:
        st = path.stat()
        info["stat_ok"] = True
        info["mode"] = oct(stat.S_IMODE(st.st_mode))
        info["readonly"] = not bool(st.st_mode & stat.S_IWRITE)
        info["mtime"] = datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
    except OSError as exc:
        info["error"] = repr(exc)
        return info
    if path.is_dir():
        try:
            children = list(path.iterdir())
            info["child_count"] = len(children)
            info["children_sample"] = [
                {
                    "name": child.name,
                    "is_dir": child.is_dir(),
                    "is_file": child.is_file(),
                }
                for child in children[:max_children]
            ]
        except OSError as exc:
            info["error"] = repr(exc)
    return info


def _powershell_acl_snapshot(path: Path) -> dict[str, Any]:
    if platform.system().lower() != "windows":
        return {"platform": platform.system(), "ok": False, "skipped": True, "reason": "ACL snapshot is Windows-only."}
    path_text = str(path).replace("'", "''")
    script = f"""
$ErrorActionPreference = 'Stop'
$target = '{path_text}'
$result = [ordered]@{{ ok = $false; exists = (Test-Path -LiteralPath $target); path = $target; owner = $null; access = @(); error = $null }}
try {{
  if ($result.exists) {{
    $acl = Get-Acl -LiteralPath $target
    $result.ok = $true
    $result.owner = [string]$acl.Owner
    $result.access = @($acl.Access | Select-Object -First 12 | ForEach-Object {{
      [ordered]@{{
        identity = [string]$_.IdentityReference
        rights = [string]$_.FileSystemRights
        type = [string]$_.AccessControlType
        inherited = [bool]$_.IsInherited
      }}
    }})
  }}
}} catch {{
  $result.error = $_.Exception.Message
}}
$result | ConvertTo-Json -Depth 6 -Compress
"""
    return _run_powershell_json(script).get("payload") or {"ok": False, "path": str(path), "error": "ACL probe failed."}


def _mkdir_unique_child(parent: Path, *, prefix: str, attempts: int = 100) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    for _ in range(attempts):
        candidate = parent / f"{prefix}{uuid.uuid4().hex[:8]}"
        try:
            os.mkdir(candidate)
            return candidate
        except FileExistsError:
            continue
    raise FileExistsError(f"Could not create a unique child directory under {parent}")


def _owned_cleanup_probe(vault: Path, probe_root: Path) -> dict[str, Any]:
    probe_root.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "root": _relative_to_vault(vault, probe_root),
        "created": None,
        "file_write_ok": False,
        "owned_cleanup_ok": False,
        "leftover_exists": False,
        "error": None,
    }
    created: Path | None = None
    try:
        created = _mkdir_unique_child(probe_root, prefix="chaseos-owned-cleanup-")
        result["created"] = _relative_to_vault(vault, created)
        marker = created / "probe.txt"
        marker.write_text("ok", encoding="utf-8")
        result["file_write_ok"] = True
        marker.unlink()
        shutil.rmtree(created)
        result["owned_cleanup_ok"] = True
    except Exception as exc:  # pragma: no cover - live filesystem failures are platform-specific.
        result["error"] = repr(exc)
    finally:
        if created is not None:
            result["leftover_exists"] = created.exists()
    return result


def _policy_temp_roots(vault: Path, payload: dict[str, Any]) -> list[Path]:
    roots: list[Path] = []
    workspace_probe = payload.get("workspace_temp_probe") or {}
    root = workspace_probe.get("root")
    if root:
        roots.append(_resolve_inside_vault(vault, root, label="policy workspace temp root"))
    cleanup = payload.get("workspace_cleanup_error") or {}
    cleanup_path = cleanup.get("path")
    if cleanup_path:
        path = _resolve_inside_vault(vault, cleanup_path, label="cleanup error path")
        roots.append(path)
        roots.append(path.parent)
    for default in DEFAULT_TEMP_ROOTS:
        roots.append(_resolve_inside_vault(vault, default, label="default workspace temp root"))
    deduped: list[Path] = []
    seen: set[str] = set()
    for item in roots:
        key = str(item)
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def build_workspace_temp_acl_cleanup_diagnostic(
    vault_root: str | Path,
    *,
    policy_check_report_path: str | Path | None = None,
    probe_root: str | Path | None = None,
) -> dict[str, Any]:
    """Inspect workspace temp ACL/cleanup posture without repairing or deleting stale artifacts."""

    vault = _vault_path(vault_root)
    latest = _load_latest_policy_check(vault, policy_check_report_path)
    payload = latest.get("payload") or {}
    selected_probe_root = _resolve_inside_vault(
        vault,
        probe_root or DEFAULT_PROBE_ROOT,
        label="workspace temp diagnostic probe root",
    )

    roots = _policy_temp_roots(vault, payload) if latest.get("ok") else [
        _resolve_inside_vault(vault, default, label="default workspace temp root") for default in DEFAULT_TEMP_ROOTS
    ]
    snapshots = [_path_snapshot(vault, root) for root in roots]
    acl_snapshots = [_powershell_acl_snapshot(root) for root in roots]
    owned_probe = _owned_cleanup_probe(vault, selected_probe_root)

    policy_next = payload.get("next_recommended_pass")
    cleanup_error = payload.get("workspace_cleanup_error") or {}
    workspace_temp_probe = payload.get("workspace_temp_probe") or {}
    policy_python_probe = workspace_temp_probe.get("python_temp_probe") or {}
    policy_temp_checks_clear = (
        bool(policy_python_probe.get("ok"))
        and not bool(cleanup_error.get("detected"))
        and policy_next == "pass10b-pywebview-webview2-minimal-repro"
    )
    policy_route_acceptable = policy_next == "pass10b-workspace-temp-acl-cleanup-diagnostic" or policy_temp_checks_clear
    stale_cleanup_path_exists = any(
        item.get("path") == _relative_to_vault(vault, _resolve_inside_vault(vault, cleanup_error.get("path"), label="cleanup error path"))
        and item.get("exists")
        for item in snapshots
    ) if cleanup_error.get("path") else False
    acl_errors = [item for item in acl_snapshots if item.get("exists") and not item.get("ok")]

    blockers: list[str] = []
    if not latest.get("ok"):
        blockers.append(str(latest.get("reason") or "Latest WebView2 temp/policy check report is invalid."))
    if not policy_route_acceptable:
        blockers.append("Latest policy check does not point at workspace temp ACL/cleanup diagnostics.")
    if not owned_probe.get("file_write_ok"):
        blockers.append("Owned workspace temp diagnostic probe cannot write its marker file.")
    if not owned_probe.get("owned_cleanup_ok"):
        blockers.append("Owned workspace temp diagnostic probe cannot clean up its own child directory.")
    if bool(policy_python_probe.get("ok")) is False:
        blockers.append("Prior workspace Python temp override probe failed.")
    if cleanup_error.get("detected") and stale_cleanup_path_exists:
        blockers.append("Packaged cleanup error path still exists inside the workspace temp tree.")
    if acl_errors:
        blockers.append("One or more workspace temp paths could not be ACL-inspected.")

    runtime_error = payload.get("packaged_runtime_error") or {}
    if not latest.get("ok"):
        status = "blocked_missing_webview2_policy_check"
        next_pass = "pass10b-system-temp-permission-or-webview2-policy-check"
    elif not owned_probe.get("file_write_ok"):
        status = "blocked_workspace_temp_probe_write"
        next_pass = "pass10b-workspace-temp-acl-operator-handoff"
    elif not owned_probe.get("owned_cleanup_ok"):
        status = "blocked_workspace_temp_owned_cleanup"
        next_pass = "pass10b-workspace-temp-acl-operator-handoff"
    elif cleanup_error.get("detected") and stale_cleanup_path_exists:
        status = "blocked_workspace_temp_stale_cleanup_artifact"
        next_pass = "pass10b-workspace-temp-stale-artifact-operator-handoff"
    elif bool(policy_python_probe.get("ok")) is False:
        status = "blocked_prior_workspace_python_temp_override_failure"
        next_pass = "pass10b-pyinstaller-pywebview-temp-minimal-repro"
    elif runtime_error.get("blocked"):
        status = "blocked_webview2_runtime_after_workspace_temp_acl_check"
        next_pass = "pass10b-pywebview-webview2-minimal-repro"
    else:
        status = "workspace_temp_acl_cleanup_diagnostic_clear"
        next_pass = "pass10b-native-visual-qa-rerun"

    checks = [
        {"name": "latest_webview2_policy_check_loaded", "ok": bool(latest.get("ok")), "detail": latest.get("path")},
        {"name": "policy_next_pass_matches_workspace_temp_diagnostic", "ok": bool(policy_route_acceptable), "detail": policy_next},
        {"name": "owned_probe_file_write_ok", "ok": bool(owned_probe.get("file_write_ok")), "detail": owned_probe.get("created")},
        {"name": "owned_probe_cleanup_ok", "ok": bool(owned_probe.get("owned_cleanup_ok")), "detail": owned_probe.get("error")},
        {"name": "stale_cleanup_error_path_absent", "ok": not stale_cleanup_path_exists, "detail": cleanup_error.get("path")},
        {"name": "acl_snapshots_available", "ok": not bool(acl_errors), "detail": len(acl_snapshots)},
        {"name": "prior_workspace_python_temp_override_ok", "ok": bool(policy_python_probe.get("ok")), "detail": (policy_python_probe.get("payload") or {}).get("error")},
    ]

    return {
        "ok": status == "workspace_temp_acl_cleanup_diagnostic_clear",
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "latest_webview2_policy_check": {
            "path": latest.get("path"),
            "artifact_present": latest.get("artifact_present"),
            "status": payload.get("status"),
            "next_recommended_pass": payload.get("next_recommended_pass"),
        },
        "workspace_temp_paths": snapshots,
        "acl_snapshots": acl_snapshots,
        "owned_cleanup_probe": owned_probe,
        "prior_workspace_python_temp_probe": policy_python_probe,
        "prior_workspace_cleanup_error": cleanup_error,
        "packaged_runtime_error": runtime_error,
        "checks": checks,
        "blockers": blockers,
        "authority": {
            "reads_webview2_policy_check_report": True,
            "reads_workspace_temp_metadata": True,
            "reads_workspace_temp_acl": platform.system().lower() == "windows",
            "creates_owned_workspace_temp_probe_child": True,
            "deletes_owned_workspace_temp_probe_child_only": True,
            "deletes_existing_temp_artifacts": False,
            "mutates_temp_acl": False,
            "mutates_host_policy": False,
            "installs_webview2": False,
            "launches_packaged_executable": False,
            "captures_native_screenshot": False,
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


def write_workspace_temp_acl_cleanup_diagnostic(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    report_slug: str | None = None,
    report_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _resolve_report_root(vault, report_root)
    slug = report_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-workspace-temp-acl-cleanup-diagnostic"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Workspace temp diagnostic report output must stay inside the report root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    lines = [
        "# Workspace Temp ACL Cleanup Diagnostic",
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
        "## Workspace Temp Paths",
        "",
        *[
            f"- {item.get('path')}: exists={item.get('exists')} writable={item.get('writable')} child_count={item.get('child_count')}"
            for item in report.get("workspace_temp_paths") or []
        ],
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
