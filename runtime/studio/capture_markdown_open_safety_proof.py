"""Open-safety proof for the Capture to Markdown Studio surfaces."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Iterator

from runtime.studio.capture_ocr_settings import capture_local_image_text_settings_path


DEFAULT_EVIDENCE_ROOT = Path("07_LOGS/Studio-Graph-Views")
DEFAULT_DESCRIPTOR = "capture-markdown-open-safety-proof"


def run_capture_markdown_open_safety_proof(
    *,
    vault_root: str | Path,
    evidence_root: str | Path = DEFAULT_EVIDENCE_ROOT,
    evidence_slug: str | None = None,
    write_evidence: bool = True,
) -> dict[str, Any]:
    """Verify Capture and Settings load without launching image text commands."""

    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.settings_runtime_controls_panel import (
        build_settings_runtime_controls_panel,
    )

    vault = Path(vault_root).resolve()
    slug = evidence_slug or f"{_date_slug()}-{DEFAULT_DESCRIPTOR}"
    settings_path = capture_local_image_text_settings_path(vault)
    original_settings_text = _read_text_if_exists(settings_path)
    original_settings_existed = original_settings_text is not None
    scratch = _resolve_under_vault(vault, Path(evidence_root) / f"{slug}-scratch")
    marker = scratch / "command-ran.txt"
    before_executables = _studio_executable_paths(vault)

    shell_rejection: dict[str, Any] = {}
    marker_save: dict[str, Any] = {}
    image_text_settings: dict[str, Any] = {}
    capture_panel: dict[str, Any] = {}
    runtime_settings: dict[str, Any] = {}
    subprocess_calls: list[dict[str, Any]] = []
    load_error = ""
    settings_restored = False
    scratch_removed = False
    after_executables: list[str] = list(before_executables)

    try:
        api = StudioAPI(str(vault))
        shell_rejection = api.save_capture_local_image_text_settings(
            {
                "local_ocr_command": "powershell.exe -NoProfile -Command Write-Output blocked",
                "local_ocr_timeout_seconds": 30,
            }
        )
        marker_command = _write_marker_local_image_text_engine(
            scratch,
            marker=marker,
            output_text="Open safety proof command output.",
        )
        marker_save = api.save_capture_local_image_text_settings(
            {
                "local_ocr_command": marker_command,
                "local_ocr_timeout_seconds": 30,
            }
        )
        try:
            with _block_subprocess_calls(subprocess_calls):
                image_text_settings = api.get_capture_local_image_text_settings()
                capture_panel = api.get_capture_to_markdown_panel(10)
                runtime_settings = build_settings_runtime_controls_panel(vault)
        except Exception as exc:
            load_error = str(exc)
        after_executables = _studio_executable_paths(vault)
    finally:
        settings_restored = _restore_file(
            settings_path,
            original_settings_text,
            original_existed=original_settings_existed,
        )
        scratch_removed = _remove_tree(scratch)

    verification = _verify_open_safety(
        before_executables=before_executables,
        after_executables=after_executables,
        capture_panel=capture_panel,
        image_text_settings=image_text_settings,
        runtime_settings=runtime_settings,
        shell_rejection=shell_rejection,
        marker_save=marker_save,
        marker=marker,
        subprocess_calls=subprocess_calls,
        load_error=load_error,
        settings_restored=settings_restored,
        scratch_removed=scratch_removed,
    )
    proof = {
        "ok": verification["ok"],
        "status": (
            "capture_markdown_open_safety_verified"
            if verification["ok"]
            else "capture_markdown_open_safety_failed"
        ),
        "schema_version": "studio.capture_markdown.open_safety_proof.v1",
        "generated_at_utc": _now_utc(),
        "run_id": slug,
        "authority": {
            "proof_blocks_subprocess_calls_during_surface_load": True,
            "capture_page_load_allowed_to_run_local_image_text_command": False,
            "settings_page_load_allowed_to_run_local_image_text_command": False,
            "shell_launchers_allowed_for_local_image_text_command": False,
            "registers_global_hotkeys": False,
            "reads_personal_active_browser_tab": False,
            "reads_browser_profile": False,
            "reads_browser_history": False,
            "reads_browser_cookies": False,
            "calls_discord_api": False,
            "provider_calls_allowed": False,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "surfaces": {
            "local_image_text_settings": _surface_summary(image_text_settings),
            "capture_panel": _surface_summary(capture_panel),
            "settings_runtime_controls": _surface_summary(runtime_settings),
        },
        "shell_launcher_rejection": {
            "ok": bool(shell_rejection.get("ok")),
            "error": shell_rejection.get("error"),
            "message": shell_rejection.get("message"),
            "payload": _compact_payload(shell_rejection),
        },
        "marker_command": {
            "save_ok": bool(marker_save.get("ok")),
            "marker_path": _rel(marker, vault),
            "marker_exists_after_surface_load": marker.exists(),
        },
        "subprocess_calls": subprocess_calls,
        "studio_executables": {
            "before": before_executables,
            "after": after_executables,
        },
        "cleanup": {
            "settings_restored": settings_restored,
            "scratch_removed": scratch_removed,
        },
        "verification": verification,
        "evidence": {},
    }
    if write_evidence:
        proof["evidence"] = write_capture_markdown_open_safety_evidence(
            vault,
            proof,
            evidence_root=evidence_root,
            evidence_slug=slug,
        )
    return proof


def write_capture_markdown_open_safety_evidence(
    vault_root: str | Path,
    proof: dict[str, Any],
    *,
    evidence_root: str | Path = DEFAULT_EVIDENCE_ROOT,
    evidence_slug: str,
) -> dict[str, str]:
    vault = Path(vault_root).resolve()
    root = _resolve_under_vault(vault, evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / f"{evidence_slug}.json"
    markdown_path = root / f"{evidence_slug}.md"
    json_path.write_text(json.dumps(proof, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path.write_text(_proof_markdown(proof), encoding="utf-8")
    return {
        "json_path": _rel(json_path, vault),
        "markdown_path": _rel(markdown_path, vault),
    }


def _verify_open_safety(
    *,
    before_executables: list[str],
    after_executables: list[str],
    capture_panel: dict[str, Any],
    image_text_settings: dict[str, Any],
    runtime_settings: dict[str, Any],
    shell_rejection: dict[str, Any],
    marker_save: dict[str, Any],
    marker: Path,
    subprocess_calls: list[dict[str, Any]],
    load_error: str,
    settings_restored: bool,
    scratch_removed: bool,
) -> dict[str, Any]:
    rejection_text = json.dumps(shell_rejection, sort_keys=True, default=str)
    capture_data = capture_panel.get("data") if isinstance(capture_panel.get("data"), dict) else {}
    settings_data = (
        image_text_settings.get("data")
        if isinstance(image_text_settings.get("data"), dict)
        else {}
    )
    checks = {
        "shell_launcher_rejected_before_persistence": (
            shell_rejection.get("ok") is False
            and "Shell launchers are blocked" in rejection_text
        ),
        "marker_command_saved_for_readback": marker_save.get("ok") is True,
        "local_image_text_settings_load_ok": image_text_settings.get("ok") is True,
        "capture_panel_load_ok": capture_panel.get("ok") is True,
        "settings_runtime_controls_load_ok": bool(runtime_settings.get("surface")),
        "settings_surface_reports_no_command_run_on_load": (
            settings_data.get("authority", {}).get("captures_screen_pixels") is False
            and settings_data.get("readiness", {}).get("settings_page_visible") is True
        ),
        "capture_surface_reports_no_collector_start_on_load": (
            capture_data.get("release_readiness", {})
            .get("authority", {})
            .get("starts_collectors")
            is False
        ),
        "marker_command_not_executed_on_load": not marker.exists(),
        "subprocess_run_or_popen_not_called": not subprocess_calls,
        "surface_load_error_absent": not load_error,
        "studio_executables_unchanged": before_executables == after_executables,
        "settings_restored_after_run": settings_restored,
        "scratch_removed_after_run": scratch_removed,
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "failed_checks": [key for key, value in checks.items() if not value],
        "load_error": load_error,
        "subprocess_call_count": len(subprocess_calls),
        "studio_executable_count_before": len(before_executables),
        "studio_executable_count_after": len(after_executables),
    }


@contextmanager
def _block_subprocess_calls(calls: list[dict[str, Any]]) -> Iterator[None]:
    original_run = subprocess.run
    original_popen = subprocess.Popen

    def blocked_run(*args: Any, **kwargs: Any) -> Any:
        calls.append({"kind": "run", "args": _safe_args(args), "kwargs": sorted(kwargs)})
        raise RuntimeError("Capture to Markdown open safety proof blocked subprocess.run")

    def blocked_popen(*args: Any, **kwargs: Any) -> Any:
        calls.append({"kind": "Popen", "args": _safe_args(args), "kwargs": sorted(kwargs)})
        raise RuntimeError("Capture to Markdown open safety proof blocked subprocess.Popen")

    subprocess.run = blocked_run  # type: ignore[assignment]
    subprocess.Popen = blocked_popen  # type: ignore[assignment]
    try:
        yield
    finally:
        subprocess.run = original_run  # type: ignore[assignment]
        subprocess.Popen = original_popen  # type: ignore[assignment]


def _write_marker_local_image_text_engine(scratch: Path, *, marker: Path, output_text: str) -> str:
    scratch.mkdir(parents=True, exist_ok=True)
    script = scratch / "fake-local-image-text-engine.py"
    script.write_text(
        "from __future__ import annotations\n"
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('ran', encoding='utf-8')\n"
        f"print({output_text!r})\n",
        encoding="utf-8",
    )
    return json.dumps([sys.executable, str(script)])


def _studio_executable_paths(vault: Path) -> list[str]:
    return sorted(
        _rel(path, vault)
        for path in vault.rglob("ChaseOS-Studio.exe")
        if ".venv" not in path.parts
    )


def _surface_summary(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return {
        "ok": payload.get("ok", True) if isinstance(payload, dict) else False,
        "surface": data.get("surface") if isinstance(data, dict) else None,
        "status": data.get("status") if isinstance(data, dict) else None,
        "error": payload.get("error") if isinstance(payload, dict) else None,
    }


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: payload.get(key)
        for key in ("ok", "surface", "error", "message", "warnings")
        if key in payload
    }


def _proof_markdown(proof: dict[str, Any]) -> str:
    verification = proof.get("verification") if isinstance(proof.get("verification"), dict) else {}
    checks = verification.get("checks") if isinstance(verification.get("checks"), dict) else {}
    failed = verification.get("failed_checks") if isinstance(verification.get("failed_checks"), list) else []
    lines = [
        f"# {proof.get('run_id')}",
        "",
        f"- Status: `{proof.get('status')}`",
        f"- Overall result: `{proof.get('ok')}`",
        f"- Subprocess calls during surface load: `{verification.get('subprocess_call_count')}`",
        f"- Studio executable count before: `{verification.get('studio_executable_count_before')}`",
        f"- Studio executable count after: `{verification.get('studio_executable_count_after')}`",
        f"- Marker command executed on load: `{proof.get('marker_command', {}).get('marker_exists_after_surface_load')}`",
        f"- Settings restored: `{proof.get('cleanup', {}).get('settings_restored')}`",
        f"- Scratch removed: `{proof.get('cleanup', {}).get('scratch_removed')}`",
        "",
        "## Checks",
        "",
    ]
    for key in sorted(checks):
        lines.append(f"- `{key}`: `{checks[key]}`")
    lines.extend(["", "## Failed Checks", ""])
    if failed:
        lines.extend(f"- `{item}`" for item in failed)
    else:
        lines.append("- None")
    return "\n".join(lines).strip() + "\n"


def _restore_file(path: Path, original_text: str | None, *, original_existed: bool) -> bool:
    try:
        if original_existed:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(original_text or "", encoding="utf-8")
        elif path.exists():
            path.unlink()
        return True
    except Exception:
        return False


def _remove_tree(path: Path) -> bool:
    try:
        if path.exists():
            shutil.rmtree(path, ignore_errors=False)
        return not path.exists()
    except Exception:
        return False


def _read_text_if_exists(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _resolve_under_vault(vault: Path, path_value: str | Path) -> Path:
    raw = Path(path_value)
    resolved = raw if raw.is_absolute() else vault / raw
    resolved = resolved.resolve()
    try:
        resolved.relative_to(vault)
    except ValueError as exc:
        raise ValueError(f"path must stay inside vault root: {path_value}") from exc
    return resolved


def _rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _safe_args(args: tuple[Any, ...]) -> list[str]:
    return [str(item)[:500] for item in args]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _date_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify Capture to Markdown opens without subprocess or command execution.",
    )
    parser.add_argument("--vault-root", default=".")
    parser.add_argument("--evidence-root", default=str(DEFAULT_EVIDENCE_ROOT))
    parser.add_argument("--evidence-slug", default=None)
    parser.add_argument("--no-write-evidence", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    proof = run_capture_markdown_open_safety_proof(
        vault_root=args.vault_root,
        evidence_root=args.evidence_root,
        evidence_slug=args.evidence_slug,
        write_evidence=not args.no_write_evidence,
    )
    if args.json:
        print(json.dumps(proof, indent=2, sort_keys=True))
    else:
        status = "OK" if proof.get("ok") else "BLOCKED"
        print(f"{status}: {proof.get('status')}")
        for failed_check in proof.get("verification", {}).get("failed_checks", []):
            print(f"- {failed_check}")
    return 0 if proof.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
