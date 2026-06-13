"""Bounded local packaging proof for the native Studio shell."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from runtime.studio.packaging_readiness import build_studio_packaging_readiness


MODEL_VERSION = "studio.local_packaging_proof.v1"
SURFACE_ID = "studio_local_packaging_proof"
DEFAULT_OUTPUT_ROOT = Path(".pytest_tmp_env") / "studio-packaging-proof"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views"
SPEC_PATH = Path("runtime") / "studio" / "packaging" / "chaseos-studio.spec"
APP_NAME = "ChaseOS-Studio"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _resolve_evidence_root(vault: Path, evidence_root: str | Path | None) -> Path:
    root_input = Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT
    root = root_input if root_input.is_absolute() else vault / root_input
    root = root.resolve()
    try:
        root.relative_to(vault)
    except ValueError as exc:
        raise ValueError("Studio local packaging proof evidence root must stay inside the vault workspace") from exc
    return root


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_command(args: list[str], *, cwd: Path, timeout_seconds: float) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-4000:],
            "stderr_tail": (proc.stderr or "")[-4000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def _output_root(vault: Path, output_root: str | Path | None) -> Path:
    if output_root:
        path = Path(output_root)
        if not path.is_absolute():
            path = vault / path
        return path.resolve()
    return (vault / DEFAULT_OUTPUT_ROOT).resolve()


def _expected_executable(output_root: Path) -> Path:
    return output_root / "dist" / APP_NAME / f"{APP_NAME}.exe"


def build_studio_local_packaging_proof(
    vault_root: str | Path,
    *,
    execute_build: bool = False,
    output_root: str | Path | None = None,
    timeout_seconds: float = 900.0,
) -> dict[str, Any]:
    """Run or preflight a bounded local PyInstaller proof for Studio."""

    vault = _vault_path(vault_root)
    readiness = build_studio_packaging_readiness(vault)
    proof_output = _output_root(vault, output_root)
    expected_exe = _expected_executable(proof_output)
    spec = vault / SPEC_PATH
    pyinstaller_available = _module_available("PyInstaller")
    pywebview_available = _module_available("webview")
    blockers: list[str] = []
    if not readiness.get("ok"):
        blockers.append("Packaging readiness contract is not green.")
    if not pyinstaller_available:
        blockers.append("PyInstaller is not installed in the active Python environment.")
    if not pywebview_available:
        blockers.append("pywebview is not installed in the active Python environment.")
    if not spec.is_file():
        blockers.append("PyInstaller spec template is missing.")

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(proof_output / "dist"),
        "--workpath",
        str(proof_output / "build"),
        str(spec),
    ]
    build_result: dict[str, Any] | None = None
    build_started = False
    if execute_build and not blockers:
        proof_output.mkdir(parents=True, exist_ok=True)
        build_started = True
        build_result = _run_command(command, cwd=vault, timeout_seconds=timeout_seconds)

    executable_exists = expected_exe.is_file()
    executable_sha256 = _sha256(expected_exe)
    if execute_build and not blockers and not executable_exists:
        blockers.append("PyInstaller finished without the expected Studio executable.")

    if blockers:
        status = "blocked_local_packaging_proof"
        ok = False
    elif execute_build:
        status = "local_packaging_proof_complete" if executable_exists else "local_packaging_proof_failed"
        ok = bool(executable_exists and (build_result or {}).get("ok"))
    else:
        status = "ready_to_execute_local_packaging_proof"
        ok = True

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "execute_build_requested": bool(execute_build),
        "readiness_status": readiness.get("status"),
        "dependencies": {
            "pyinstaller_available": pyinstaller_available,
            "pywebview_available": pywebview_available,
        },
        "command": {
            "argv": command,
            "cwd": str(vault),
            "timeout_seconds": float(timeout_seconds),
            "started": build_started,
        },
        "outputs": {
            "output_root": _relative_to_vault(vault, proof_output),
            "dist_dir": _relative_to_vault(vault, proof_output / "dist"),
            "build_dir": _relative_to_vault(vault, proof_output / "build"),
            "expected_executable": _relative_to_vault(vault, expected_exe),
            "executable_exists": executable_exists,
            "executable_sha256": executable_sha256,
        },
        "build": build_result,
        "authority": {
            "builds_executable": bool(execute_build and not blockers),
            "writes_packaging_output_root": bool(execute_build and not blockers),
            "writes_installer": False,
            "launches_executable": False,
            "launches_pywebview": False,
            "writes_vault_source_files": False,
            "writes_host_startup": False,
            "mutates_gate": False,
            "grants_approvals": False,
            "executes_approval_decisions": False,
            "executes_workflows": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": blockers,
        "unverified": [
            "Generated executable was not launched.",
            "Native PyWebView visual QA was not run against packaged output.",
            "Installer creation/signing was not attempted.",
            "Startup/autostart integration was not attempted.",
        ],
        "next_recommended_pass": "studio-packaged-app-launch-smoke"
        if executable_exists and not blockers
        else "studio-local-packaging-proof",
    }


def write_packaging_proof_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _resolve_evidence_root(vault, evidence_root)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-local-packaging-proof"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Studio local packaging proof evidence output must stay inside the evidence root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    lines = [
        "# Studio Local Packaging Proof Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Execute build requested: {report.get('execute_build_requested')}",
        "",
        "## Dependencies",
        "",
        f"- PyInstaller available: {(report.get('dependencies') or {}).get('pyinstaller_available')}",
        f"- pywebview available: {(report.get('dependencies') or {}).get('pywebview_available')}",
        "",
        "## Outputs",
        "",
        f"- Output root: {(report.get('outputs') or {}).get('output_root')}",
        f"- Expected executable: {(report.get('outputs') or {}).get('expected_executable')}",
        f"- Executable exists: {(report.get('outputs') or {}).get('executable_exists')}",
        f"- Executable sha256: {(report.get('outputs') or {}).get('executable_sha256')}",
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
