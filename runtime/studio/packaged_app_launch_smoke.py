"""Bounded launch smoke for the packaged native Studio executable."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any

from runtime.studio.packaging_proof import build_studio_local_packaging_proof, _expected_executable, _sha256


MODEL_VERSION = "studio.packaged_app_launch_smoke.v1"
SURFACE_ID = "studio_packaged_app_launch_smoke"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views"
DEFAULT_EXE = _expected_executable(Path(".pytest_tmp_env") / "studio-packaging-proof")


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
        raise ValueError("packaged app launch smoke evidence root must stay inside the vault workspace") from exc
    return root


def _resolve_executable(vault: Path, executable_path: str | Path | None) -> Path:
    path = Path(executable_path) if executable_path else DEFAULT_EXE
    if not path.is_absolute():
        path = vault / path
    resolved = path.resolve()
    try:
        resolved.relative_to(vault)
    except ValueError as exc:
        raise ValueError("packaged app launch smoke only launches executables inside the vault workspace") from exc
    return resolved


def _vault_arg_for_packaged_exe(vault: Path) -> str:
    """Return a vault-root argument usable by a Windows packaged exe launched from WSL."""

    vault_text = str(vault)
    vault_probe = vault_text.replace("\\", "/")
    if vault_probe.startswith("/mnt/"):
        try:
            converted = subprocess.run(
                ["wslpath", "-w", vault_probe],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            ).stdout.strip()
            if converted:
                return converted
        except (OSError, subprocess.SubprocessError, TypeError):
            pass
    return vault_text


def _markdown_snapshot(vault: Path) -> dict[str, str]:
    """Capture a bounded markdown content sentinel without walking generated trees.

    The launch smoke only needs to prove the packaged app did not mutate ChaseOS
    markdown/knowledge surfaces during startup. A whole-vault walk is both noisy
    and too slow on WSL when generated runtime/build trees are present, so this
    sentinel is intentionally scoped to markdown-bearing vault surfaces and uses
    file content hashes rather than mtimes. Active editors and indexers can touch
    mtimes without changing content; approval artifacts remain mtime-guarded.
    """

    snapshot: dict[str, str] = {}
    candidate_roots = [
        vault,
        vault / "00_HOME",
        vault / "01_PROJECTS",
        vault / "02_KNOWLEDGE",
        vault / "03_INPUTS",
        vault / "04_SOPS",
        vault / "05_TEMPLATES",
        vault / "06_AGENTS",
        vault / "docs",
        vault / "security",
    ]
    excluded_dirs = {"07_LOGS", "99_ARCHIVE", "core_export", "runtime", "kernel", "core_templates"}
    for candidate in candidate_roots:
        if not candidate.exists():
            continue
        if candidate == vault:
            paths = [path for path in candidate.glob("*.md") if path.is_file()]
        else:
            paths = []
            for root, dirs, files in os.walk(candidate):
                dirs[:] = [
                    item
                    for item in dirs
                    if not item.startswith(".")
                    and item != "__pycache__"
                    and item not in excluded_dirs
                ]
                base = Path(root)
                paths.extend(base / filename for filename in files if filename.endswith(".md"))
        for path in paths:
            try:
                snapshot[_relative_to_vault(vault, path)] = _sha256(path)
            except OSError:
                continue
    return snapshot


def _approval_artifact_snapshot(vault: Path) -> dict[str, float]:
    roots = [
        vault / "runtime" / "studio" / "approvals",
        vault / "07_LOGS" / "SiteOps-Approvals",
        vault / "07_LOGS" / "Promotion-Records",
        vault / "07_LOGS" / "Agent-Activity" / "_vcmi_aor_dispatch_approvals",
        vault / "07_LOGS" / "Agent-Activity" / "_vcmi_sic_ingestion_approvals",
        vault / "07_LOGS" / "Agent-Activity" / "_vcmi_canonical_promotion_approvals",
        vault / "07_LOGS" / "Agent-Activity" / "_vcmi_canonical_promotion",
    ]
    snapshot: dict[str, float] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file():
                try:
                    snapshot[_relative_to_vault(vault, path)] = path.stat().st_mtime
                except OSError:
                    continue
    return snapshot


def _snapshot_delta(before: dict[str, float], after: dict[str, float]) -> dict[str, list[str]]:
    before_keys = set(before)
    after_keys = set(after)
    return {
        "added": sorted(after_keys - before_keys),
        "removed": sorted(before_keys - after_keys),
        "modified": sorted(path for path in before_keys & after_keys if before[path] != after[path]),
    }


def _snapshot_delta_changed(delta: dict[str, list[str]]) -> bool:
    return any(delta.get(key) for key in ("added", "removed", "modified"))


def _snapshot_delta_detail(delta: dict[str, list[str]]) -> str:
    if not _snapshot_delta_changed(delta):
        return "snapshot unchanged"
    parts: list[str] = []
    for key in ("added", "removed", "modified"):
        values = delta.get(key) or []
        if values:
            sample = ", ".join(values[:5])
            suffix = "" if len(values) <= 5 else f", +{len(values) - 5} more"
            parts.append(f"{key}: {sample}{suffix}")
    return "; ".join(parts)


def _terminate_owned_process(proc: subprocess.Popen[Any], timeout_seconds: float) -> dict[str, Any]:
    if proc.poll() is not None:
        return {"attempted": False, "terminated": True, "returncode": proc.returncode}
    proc.terminate()
    try:
        proc.wait(timeout=timeout_seconds)
        return {"attempted": True, "terminated": True, "returncode": proc.returncode}
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            return {"attempted": True, "terminated": False, "returncode": None}
        return {"attempted": True, "terminated": True, "returncode": proc.returncode, "killed": True}


def build_packaged_app_launch_smoke(
    vault_root: str | Path,
    *,
    executable_path: str | Path | None = None,
    settle_seconds: float = 8.0,
    terminate: bool = True,
    terminate_timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    """Launch the packaged Studio exe briefly and terminate only that process."""

    vault = _vault_path(vault_root)
    exe = _resolve_executable(vault, executable_path)
    blockers: list[str] = []
    packaging_proof: dict[str, Any] = {
        "status": "not_checked_missing_executable",
        "outputs": {"executable_exists": False, "executable_sha256": None},
    }
    before_markdown: dict[str, float] = {}
    before_approvals: dict[str, float] = {}
    after_markdown: dict[str, float] = {}
    after_approvals: dict[str, float] = {}
    explicit_executable_supplied = executable_path is not None
    if not exe.is_file():
        blockers.append("Packaged Studio executable is missing.")
    else:
        packaging_proof = build_studio_local_packaging_proof(vault)
        proof_executable_exists = bool((packaging_proof.get("outputs") or {}).get("executable_exists"))
        if not proof_executable_exists and not explicit_executable_supplied:
            blockers.append("Local packaging proof does not currently see a generated executable.")

    proc: subprocess.Popen[Any] | None = None
    launch_error: str | None = None
    process_alive_after_settle = False
    termination = {"attempted": False, "terminated": False, "returncode": None}
    if not blockers:
        before_markdown = _markdown_snapshot(vault)
        before_approvals = _approval_artifact_snapshot(vault)
        try:
            launch_vault_arg = _vault_arg_for_packaged_exe(vault)
            proc = subprocess.Popen(
                [str(exe), "--vault-root", launch_vault_arg],
                cwd=str(vault),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )
            time.sleep(max(0.1, float(settle_seconds)))
            process_alive_after_settle = proc.poll() is None
            if terminate:
                termination = _terminate_owned_process(proc, terminate_timeout_seconds)
        except OSError as exc:
            launch_error = str(exc)
            blockers.append(f"Packaged Studio executable launch failed: {exc}")
        after_markdown = _markdown_snapshot(vault)
        after_approvals = _approval_artifact_snapshot(vault)
    markdown_delta = _snapshot_delta(before_markdown, after_markdown)
    approval_delta = _snapshot_delta(before_approvals, after_approvals)
    if _snapshot_delta_changed(markdown_delta):
        blockers.append("Markdown write sentinel changed during packaged launch smoke.")
    if _snapshot_delta_changed(approval_delta):
        blockers.append("Approval artifact write sentinel changed during packaged launch smoke.")
    ok = not blockers and process_alive_after_settle and (not terminate or bool(termination.get("terminated")))
    status = "packaged_app_launch_smoke_complete" if ok else "blocked_packaged_app_launch_smoke"
    stdout_tail = ""
    stderr_tail = ""
    if proc is not None and proc.poll() is not None:
        try:
            stdout, stderr = proc.communicate(timeout=1)
            stdout_tail = (stdout or "")[-4000:]
            stderr_tail = (stderr or "")[-4000:]
        except (subprocess.TimeoutExpired, ValueError):
            pass

    proof_outputs = packaging_proof.get("outputs") or {}
    executable_sha256 = _sha256(exe) if explicit_executable_supplied else proof_outputs.get("executable_sha256") or _sha256(exe)

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "executable": {
            "path": _relative_to_vault(vault, exe),
            "exists": exe.is_file(),
            "sha256": executable_sha256,
        },
        "launch": {
            "started": proc is not None,
            "process_id": proc.pid if proc is not None else None,
            "settle_seconds": float(settle_seconds),
            "process_alive_after_settle": process_alive_after_settle,
            "returncode_after_termination": termination.get("returncode"),
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "launch_error": launch_error,
        },
        "termination": termination,
        "write_sentinel": {
            "markdown": markdown_delta,
            "approval_artifacts": approval_delta,
        },
        "authority": {
            "launches_packaged_executable": proc is not None,
            "terminates_owned_process": bool(termination.get("attempted")),
            "writes_installer": False,
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
        "checks": [
            {"name": "packaged_executable_exists", "ok": exe.is_file(), "detail": _relative_to_vault(vault, exe)},
            {
                "name": "packaging_proof_executable_seen",
                "ok": bool((packaging_proof.get("outputs") or {}).get("executable_exists")) or explicit_executable_supplied,
                "detail": (
                    "explicit executable path supplied; default packaging proof output is not required"
                    if explicit_executable_supplied and not bool((packaging_proof.get("outputs") or {}).get("executable_exists"))
                    else packaging_proof.get("status", "")
                ),
            },
            {"name": "process_alive_after_settle", "ok": process_alive_after_settle, "detail": "PyWebView process stayed alive long enough for launch smoke"},
            {"name": "owned_process_terminated", "ok": not terminate or bool(termination.get("terminated")), "detail": "terminated only the process started by this smoke"},
            {"name": "no_markdown_writes", "ok": not _snapshot_delta_changed(markdown_delta), "detail": _snapshot_delta_detail(markdown_delta)},
            {"name": "no_approval_artifact_writes", "ok": not _snapshot_delta_changed(approval_delta), "detail": _snapshot_delta_detail(approval_delta)},
        ],
        "blockers": blockers,
        "unverified": [
            "Native screenshot capture was not performed by this command.",
            "Installer creation/signing was not attempted.",
            "Startup/autostart integration was not attempted.",
        ],
        "next_recommended_pass": "studio-packaged-app-visual-qa" if ok else "studio-packaged-app-launch-smoke",
    }


def write_launch_smoke_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = _resolve_evidence_root(vault, evidence_root)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-packaged-app-launch-smoke"
    json_path = (root / f"{slug}.json").resolve()
    markdown_path = (root / f"{slug}.md").resolve()
    for path in (json_path, markdown_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError("packaged app launch smoke evidence output must stay inside the evidence root") from exc
    root.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    lines = [
        "# Studio Packaged App Launch Smoke Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        "",
        "## Executable",
        "",
        f"- Path: {(report.get('executable') or {}).get('path')}",
        f"- Exists: {(report.get('executable') or {}).get('exists')}",
        f"- SHA-256: {(report.get('executable') or {}).get('sha256')}",
        "",
        "## Launch",
        "",
        f"- Started: {(report.get('launch') or {}).get('started')}",
        f"- Process ID: {(report.get('launch') or {}).get('process_id')}",
        f"- Alive after settle: {(report.get('launch') or {}).get('process_alive_after_settle')}",
        f"- Terminated: {(report.get('termination') or {}).get('terminated')}",
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in report.get("blockers") or ["None"]],
        "",
        "## Checks",
        "",
        *[f"- {item.get('name')}: {item.get('ok')} - {item.get('detail')}" for item in report.get("checks") or []],
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
