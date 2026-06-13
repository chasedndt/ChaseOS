"""Minimal packaged PyWebView/WebView2 repro for Pass 10B."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from runtime.operator_surface.browser.image_verifier import analyze_png_nonblank
from runtime.studio.packaged_app_launch_smoke import _relative_to_vault, _terminate_owned_process
from runtime.studio.packaged_app_visual_qa import (
    _capture_window_screenshot,
    _classify_runtime_error,
    build_packaged_app_visual_qa,
    build_runtime_env_overrides,
)
from runtime.studio.packaging_proof import _module_available, _run_command, _sha256


MODEL_VERSION = "studio.pywebview_webview2_minimal_repro.v1"
SURFACE_ID = "studio_pywebview_webview2_minimal_repro"
DEFAULT_OUTPUT_ROOT = Path(".pytest_tmp_env") / "studio-pywebview-webview2-minimal-repro"
DEFAULT_REPORT_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "pywebview-webview2-minimal-repro"
APP_NAME = "ChaseOS-WebView2-Minimal-Repro"


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


def _output_root(vault: Path, output_root: str | Path | None) -> Path:
    return _resolve_inside_vault(vault, output_root or DEFAULT_OUTPUT_ROOT, label="minimal repro output root")


def _report_root(vault: Path, report_root: str | Path | None) -> Path:
    return _resolve_inside_vault(vault, report_root or DEFAULT_REPORT_ROOT, label="minimal repro report root")


def _source_path(output_root: Path) -> Path:
    return output_root / "src" / "minimal_pywebview_webview2_repro.py"


def _spec_path(output_root: Path) -> Path:
    return output_root / "minimal-pywebview-webview2-repro.spec"


def _expected_executable(output_root: Path) -> Path:
    executable_name = f"{APP_NAME}.exe" if sys.platform.startswith("win") else APP_NAME
    return output_root / "dist" / APP_NAME / executable_name


def _minimal_app_source() -> str:
    return r'''"""Minimal PyWebView/WebView2 packaged repro entry point."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile
import traceback
import uuid


WEBVIEW2_USER_DATA_ENV = "WEBVIEW2_USER_DATA_FOLDER"


def _log(message: str) -> None:
    path = os.environ.get("CHASEOS_STUDIO_STARTUP_LOG")
    if not path:
        return
    selected = Path(path)
    selected.parent.mkdir(parents=True, exist_ok=True)
    with selected.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def _install_windows_safe_mkdtemp_workaround() -> None:
    if sys.platform != "win32" or getattr(tempfile, "_chaseos_safe_mkdtemp_installed", False):
        return
    original_mkdtemp = tempfile.mkdtemp

    def _safe_mkdtemp(suffix=None, prefix=None, dir=None):
        if any(isinstance(value, bytes) for value in (suffix, prefix, dir)):
            return original_mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
        selected_suffix = "" if suffix is None else suffix
        selected_prefix = "tmp" if prefix is None else prefix
        root = Path(dir if dir is not None else tempfile.gettempdir())
        root.mkdir(parents=True, exist_ok=True)
        for _ in range(100):
            candidate = root / f"{selected_prefix}{uuid.uuid4().hex[:8]}{selected_suffix}"
            try:
                os.mkdir(candidate)
                return str(candidate)
            except FileExistsError:
                continue
        return original_mkdtemp(suffix=selected_suffix, prefix=selected_prefix, dir=str(root))

    tempfile.mkdtemp = _safe_mkdtemp
    tempfile._chaseos_safe_mkdtemp_installed = True


def _resolve_storage_path(vault_root: Path) -> str | None:
    raw = os.environ.get(WEBVIEW2_USER_DATA_ENV)
    if not raw:
        return None
    selected = Path(raw)
    if not selected.is_absolute():
        selected = vault_root / selected
    selected = selected.resolve()
    selected.mkdir(parents=True, exist_ok=True)
    return str(selected)


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal ChaseOS PyWebView WebView2 repro")
    parser.add_argument("--vault-root", default=".")
    parser.add_argument("args", nargs="*")
    parsed = parser.parse_args()
    vault_root = Path(parsed.vault_root).resolve()
    _install_windows_safe_mkdtemp_workaround()
    _log(f"minimal_repro_start vault_root={vault_root}")
    try:
        import webview

        storage_path = _resolve_storage_path(vault_root)
        _log(f"storage_path={storage_path}")
        webview.create_window(
            "ChaseOS WebView2 Minimal Repro",
            html=(
                "<!doctype html><html><head><meta charset='utf-8'>"
                "<title>ChaseOS WebView2 Minimal Repro</title>"
                "<style>body{margin:0;font-family:Segoe UI,Arial,sans-serif;"
                "background:#16202a;color:#f5f7fa;display:flex;align-items:center;"
                "justify-content:center;height:100vh}main{border:1px solid #6fd3ff;"
                "padding:28px;background:#1f2f3b}h1{font-size:28px;margin:0 0 12px}"
                "p{font-size:16px;margin:0}</style></head><body><main>"
                "<h1>ChaseOS WebView2 Minimal Repro</h1>"
                "<p>Vanilla PyWebView packaged window initialized.</p>"
                "</main></body></html>"
            ),
            width=900,
            height=620,
        )
        webview.start(debug=False, storage_path=storage_path)
    except Exception:
        _log(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
'''


def _minimal_spec(source_path: Path) -> str:
    source_literal = str(source_path).replace("\\", "\\\\")
    return f'''# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

HIDDEN = collect_submodules("webview")

a = Analysis(
    [r"{source_literal}"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=HIDDEN,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="{APP_NAME}",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="{APP_NAME}",
)
'''


def _write_minimal_build_inputs(output_root: Path) -> dict[str, Path]:
    source = _source_path(output_root)
    spec = _spec_path(output_root)
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(_minimal_app_source(), encoding="utf-8")
    spec.write_text(_minimal_spec(source), encoding="utf-8")
    return {"source": source, "spec": spec}


def _build_source_probe(
    vault: Path,
    out_root: Path,
    source: Path,
    *,
    webview2_user_data_root: str | Path | None = None,
    temp_root: str | Path | None = None,
    settle_seconds: float = 8.0,
    window_timeout_seconds: float = 15.0,
    terminate_timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    screenshot = out_root / "minimal-source-repro-screenshot.png"
    startup_log = out_root / "minimal-source-repro-screenshot.startup.log"
    env = os.environ.copy()
    runtime_overrides, runtime_dirs = build_runtime_env_overrides(
        vault,
        webview2_user_data_root=webview2_user_data_root,
        temp_root=temp_root,
    )
    env.update(runtime_overrides)
    env.setdefault("CHASEOS_STUDIO_STARTUP_LOG", str(startup_log))
    proc: subprocess.Popen[Any] | None = None
    launch_error: str | None = None
    capture: dict[str, Any] = {}
    termination = {"attempted": False, "terminated": False, "returncode": None}
    process_alive_before_capture = False
    try:
        proc = subprocess.Popen(
            [sys.executable, str(source), "--vault-root", str(vault)],
            cwd=str(vault),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        )
        time.sleep(max(0.1, float(settle_seconds)))
        process_alive_before_capture = proc.poll() is None
        if process_alive_before_capture:
            capture = _capture_window_screenshot(
                process_id=proc.pid,
                screenshot_path=screenshot,
                timeout_seconds=window_timeout_seconds,
            )
    except OSError as exc:
        launch_error = str(exc)
    finally:
        if proc is not None:
            termination = _terminate_owned_process(proc, terminate_timeout_seconds)

    stdout_tail = ""
    stderr_tail = ""
    if proc is not None and proc.poll() is not None:
        try:
            stdout, stderr = proc.communicate(timeout=1)
            stdout_tail = (stdout or "")[-4000:]
            stderr_tail = (stderr or "")[-4000:]
        except (subprocess.TimeoutExpired, ValueError):
            pass
    startup_log_tail = ""
    startup_log_exists = startup_log.is_file()
    if startup_log_exists:
        startup_log_tail = startup_log.read_text(encoding="utf-8", errors="replace")[-4000:]
    runtime_error = _classify_runtime_error((stderr_tail or "") + "\n" + (startup_log_tail or ""))
    screenshot_exists = screenshot.is_file()
    screenshot_size = screenshot.stat().st_size if screenshot_exists else 0
    visual_verification = analyze_png_nonblank(screenshot)
    ok = (
        launch_error is None
        and process_alive_before_capture
        and bool(capture.get("ok"))
        and screenshot_exists
        and screenshot_size > 1000
        and bool(visual_verification.get("ok"))
        and bool(termination.get("terminated"))
        and not bool(runtime_error.get("blocked"))
    )
    return {
        "ok": ok,
        "status": "minimal_pywebview_source_probe_complete" if ok else "blocked_minimal_pywebview_source_probe",
        "source_path": _relative_to_vault(vault, source),
        "launch": {
            "started": proc is not None,
            "process_id": proc.pid if proc is not None else None,
            "process_alive_before_capture": process_alive_before_capture,
            "launch_error": launch_error,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "startup_log_path": _relative_to_vault(vault, startup_log),
            "startup_log_exists": startup_log_exists,
            "startup_log_tail": startup_log_tail,
            "runtime_env_override_keys": sorted(runtime_overrides.keys()),
            "runtime_dirs": runtime_dirs,
            "runtime_error": runtime_error,
        },
        "screenshot": {
            "path": _relative_to_vault(vault, screenshot),
            "exists": screenshot_exists,
            "size_bytes": screenshot_size,
            "capture": capture,
            "visual_verification": visual_verification,
        },
        "termination": termination,
        "checks": [
            {"name": "source_process_started", "ok": proc is not None, "detail": launch_error},
            {"name": "source_process_alive_before_capture", "ok": process_alive_before_capture, "detail": str(process_alive_before_capture)},
            {"name": "source_webview2_initialized", "ok": not bool(runtime_error.get("blocked")), "detail": runtime_error.get("status")},
            {"name": "source_window_capture_ok", "ok": bool(capture.get("ok")), "detail": capture.get("error")},
            {"name": "source_screenshot_nonblank", "ok": bool(visual_verification.get("ok")), "detail": visual_verification.get("reason")},
            {"name": "source_owned_process_terminated", "ok": bool(termination.get("terminated")), "detail": str(termination.get("returncode"))},
        ],
    }


def build_pywebview_webview2_minimal_repro(
    vault_root: str | Path,
    *,
    execute_build: bool = False,
    output_root: str | Path | None = None,
    build_timeout_seconds: float = 900.0,
    probe_source: bool = False,
    probe_launch: bool = False,
    webview2_user_data_root: str | Path | None = None,
    temp_root: str | Path | None = None,
    settle_seconds: float = 8.0,
    window_timeout_seconds: float = 15.0,
    terminate_timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    out_root = _output_root(vault, output_root)
    source = _source_path(out_root)
    spec = _spec_path(out_root)
    exe = _expected_executable(out_root)
    pyinstaller_available = _module_available("PyInstaller")
    pywebview_available = _module_available("webview")
    blockers: list[str] = []
    if not pyinstaller_available:
        blockers.append("PyInstaller is not installed in the active Python environment.")
    if not pywebview_available:
        blockers.append("pywebview is not installed in the active Python environment.")

    build_inputs_written = False
    build_result: dict[str, Any] | None = None
    build_started = False
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(out_root / "dist"),
        "--workpath",
        str(out_root / "build"),
        str(spec),
    ]
    if execute_build and not blockers:
        paths = _write_minimal_build_inputs(out_root)
        source = paths["source"]
        spec = paths["spec"]
        build_inputs_written = True
        command[-1] = str(spec)
        build_started = True
        build_result = _run_command(command, cwd=vault, timeout_seconds=build_timeout_seconds)
        if not build_result.get("ok"):
            blockers.append("Minimal PyInstaller build failed.")

    source_probe: dict[str, Any] | None = None
    if probe_source and not blockers:
        if not source.is_file():
            paths = _write_minimal_build_inputs(out_root)
            source = paths["source"]
            spec = paths["spec"]
            command[-1] = str(spec)
            build_inputs_written = True
        source_probe = _build_source_probe(
            vault,
            out_root,
            source,
            webview2_user_data_root=webview2_user_data_root,
            temp_root=temp_root,
            settle_seconds=settle_seconds,
            window_timeout_seconds=window_timeout_seconds,
            terminate_timeout_seconds=terminate_timeout_seconds,
        )

    executable_exists = exe.is_file()
    if execute_build and not executable_exists:
        blockers.append("Minimal PyInstaller build did not produce the expected executable.")

    visual_probe: dict[str, Any] | None = None
    if probe_launch and executable_exists:
        visual_probe = build_packaged_app_visual_qa(
            vault,
            executable_path=exe,
            screenshot_path=out_root / "minimal-repro-screenshot.png",
            webview2_user_data_root=webview2_user_data_root,
            temp_root=temp_root,
            settle_seconds=settle_seconds,
            window_timeout_seconds=window_timeout_seconds,
            terminate_timeout_seconds=terminate_timeout_seconds,
        )
    elif probe_launch and not executable_exists:
        blockers.append("Minimal packaged executable is missing for launch probe.")

    visual_ok = bool(visual_probe and visual_probe.get("ok"))
    runtime_blocked = bool(
        visual_probe
        and (((visual_probe.get("launch") or {}).get("runtime_error") or {}).get("blocked"))
    )
    host_policy_blocked = bool(
        visual_probe
        and (
            ((visual_probe.get("launch") or {}).get("host_policy") or visual_probe.get("host_policy") or {}).get(
                "blocked_by_windows_application_control"
            )
        )
    )
    source_runtime_blocked = bool(
        source_probe
        and (((source_probe.get("launch") or {}).get("runtime_error") or {}).get("blocked"))
    )
    source_ok = bool(source_probe and source_probe.get("ok"))
    if visual_ok:
        status = "minimal_pywebview_webview2_repro_visual_qa_complete"
        next_pass = "pass10b-studio-shell-webview-startup-differential"
        ok = True
    elif runtime_blocked:
        status = "blocked_minimal_pywebview_webview2_runtime"
        next_pass = "pass10b-webview2-runtime-host-remediation"
        ok = False
    elif host_policy_blocked:
        status = "blocked_minimal_pywebview_packaged_host_policy"
        next_pass = "pass10b-minimal-packaged-host-policy-unblock"
        ok = False
    elif probe_launch and visual_probe:
        status = "blocked_minimal_pywebview_webview2_window_capture"
        next_pass = "pass10b-minimal-repro-window-capture-diagnostic"
        ok = False
    elif source_runtime_blocked:
        status = "blocked_minimal_pywebview_source_webview2_runtime"
        next_pass = "pass10b-webview2-runtime-host-remediation"
        ok = False
    elif probe_source and source_ok:
        status = "minimal_pywebview_source_repro_complete_packaged_probe_pending"
        next_pass = "pass10b-pywebview-webview2-minimal-repro-packaged-probe"
        ok = True
    elif probe_source and source_probe:
        status = "blocked_minimal_pywebview_source_probe"
        next_pass = "pass10b-minimal-source-probe-diagnostic"
        ok = False
    elif blockers:
        status = "blocked_minimal_pywebview_webview2_repro"
        next_pass = "pass10b-pywebview-webview2-minimal-repro"
        ok = False
    elif executable_exists:
        status = "minimal_pywebview_webview2_repro_ready_for_probe"
        next_pass = "pass10b-pywebview-webview2-minimal-repro-probe"
        ok = True
    else:
        status = "minimal_pywebview_webview2_repro_ready_to_build"
        next_pass = "pass10b-pywebview-webview2-minimal-repro"
        ok = True
    reported_blockers = list(blockers)
    if source_runtime_blocked:
        reported_blockers.append("Minimal source PyWebView/WebView2 probe fails with WebView2 initialization error.")
    if runtime_blocked:
        reported_blockers.append("Minimal packaged PyWebView/WebView2 probe fails with WebView2 initialization error.")
    if host_policy_blocked:
        reported_blockers.append("Minimal packaged PyWebView executable is blocked by host application control.")

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "execute_build_requested": bool(execute_build),
        "probe_source_requested": bool(probe_source),
        "probe_launch_requested": bool(probe_launch),
        "dependencies": {
            "pyinstaller_available": pyinstaller_available,
            "pywebview_available": pywebview_available,
        },
        "build_inputs": {
            "written": build_inputs_written,
            "source_path": _relative_to_vault(vault, source),
            "spec_path": _relative_to_vault(vault, spec),
        },
        "command": {
            "argv": command,
            "cwd": str(vault),
            "timeout_seconds": float(build_timeout_seconds),
            "started": build_started,
        },
        "outputs": {
            "output_root": _relative_to_vault(vault, out_root),
            "expected_executable": _relative_to_vault(vault, exe),
            "executable_exists": executable_exists,
            "executable_sha256": _sha256(exe),
        },
        "build": build_result,
        "source_probe": source_probe,
        "visual_probe": visual_probe,
        "checks": [
            {"name": "pyinstaller_available", "ok": pyinstaller_available, "detail": str(pyinstaller_available)},
            {"name": "pywebview_available", "ok": pywebview_available, "detail": str(pywebview_available)},
            {"name": "minimal_build_inputs_written", "ok": build_inputs_written or not execute_build, "detail": _relative_to_vault(vault, source)},
            {"name": "minimal_executable_exists", "ok": executable_exists, "detail": _relative_to_vault(vault, exe)},
            {"name": "minimal_source_probe_requested", "ok": bool(probe_source), "detail": str(bool(probe_source))},
            {"name": "minimal_source_probe_complete", "ok": source_ok, "detail": (source_probe or {}).get("status")},
            {"name": "minimal_visual_probe_requested", "ok": bool(probe_launch), "detail": str(bool(probe_launch))},
            {
                "name": "minimal_webview2_initialized",
                "ok": bool(visual_probe and not runtime_blocked),
                "detail": (((visual_probe or {}).get("launch") or {}).get("runtime_error") or {}).get("status"),
            },
            {"name": "minimal_visual_qa_complete", "ok": visual_ok, "detail": (visual_probe or {}).get("status")},
        ],
        "blockers": reported_blockers,
        "authority": {
            "writes_minimal_repro_build_inputs": bool(build_inputs_written),
            "builds_minimal_packaged_executable": bool(execute_build and build_inputs_written),
            "launches_minimal_packaged_executable": bool(probe_launch and executable_exists),
            "launches_minimal_source_probe": bool(source_probe and ((source_probe.get("launch") or {}).get("started"))),
            "captures_native_screenshot": bool(visual_probe and ((visual_probe.get("screenshot") or {}).get("exists"))),
            "terminates_owned_process": bool(visual_probe and ((visual_probe.get("termination") or {}).get("attempted"))),
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
            "This repro uses a vanilla PyWebView HTML window and does not load the ChaseOS Studio shell.",
            "No WebView2 runtime install or repair was attempted.",
            "No host policy, signing, allowlisting, installer, startup, approval, provider, connector, Agent Bus, or canonical mutation was attempted.",
            "Native packaged Studio visual QA remains unverified unless the Studio executable itself captures a nonblank screenshot.",
        ],
        "next_recommended_pass": next_pass,
    }


def write_pywebview_webview2_minimal_repro(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    report_slug: str | None = None,
    report_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _report_root(vault, report_root)
    slug = report_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-pywebview-webview2-minimal-repro"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("minimal repro report output must stay inside the report root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    outputs = report.get("outputs") or {}
    source_probe = report.get("source_probe") or {}
    visual = report.get("visual_probe") or {}
    screenshot = visual.get("screenshot") or {}
    lines = [
        "# PyWebView WebView2 Minimal Repro",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next recommended pass: {report.get('next_recommended_pass')}",
        "",
        "## Outputs",
        "",
        f"- Output root: {outputs.get('output_root')}",
        f"- Expected executable: {outputs.get('expected_executable')}",
        f"- Executable exists: {outputs.get('executable_exists')}",
        f"- Executable sha256: {outputs.get('executable_sha256')}",
        "",
        "## Visual Probe",
        "",
        f"- Source probe requested: {report.get('probe_source_requested')}",
        f"- Source probe status: {source_probe.get('status')}",
        f"- Source probe OK: {source_probe.get('ok')}",
        "",
        f"- Requested: {report.get('probe_launch_requested')}",
        f"- Status: {visual.get('status')}",
        f"- OK: {visual.get('ok')}",
        f"- Screenshot: {screenshot.get('path')}",
        f"- Screenshot exists: {screenshot.get('exists')}",
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
