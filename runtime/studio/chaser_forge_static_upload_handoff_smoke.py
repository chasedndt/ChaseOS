"""Direct smoke test for Chaser Forge manual static-host upload handoff.

This avoids browser and pytest wrappers. It drives the StudioAPI handoff
preview/write path against a temporary fixture vault, then verifies registry,
panel, and frontend wiring from the production repo.
"""

from __future__ import annotations

import argparse
import faulthandler
import json
from pathlib import Path
import shutil
import time
from typing import Any

from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


SMOKE_STATUS = "COMPLETE / GOVERNED STATIC HOST UPLOAD HANDOFF VERIFIED"
DEFAULT_OUTPUT_DIR = (
    Path("07_LOGS")
    / "Studio-Visual-QA"
    / "2026-05-23-chaser-forge-static-upload-handoff-smoke"
)
RESULT_NAME = "chaser-forge-static-upload-handoff-smoke-result.json"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _resolve_inside_vault(vault: Path, output_dir: str | Path) -> Path:
    raw = Path(output_dir)
    resolved = raw if raw.is_absolute() else vault / raw
    resolved = resolved.resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError("Static upload handoff smoke output must stay inside the vault") from exc
    return resolved


def _result_data(resp: dict[str, Any], label: str) -> dict[str, Any]:
    if not resp or resp.get("ok") is not True:
        error = (resp.get("error") or {}).get("message") if isinstance(resp, dict) else ""
        raise RuntimeError(f"{label} failed: {error or 'unknown error'}")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    if data.get("ok") is False:
        blockers = "; ".join(str(item) for item in data.get("blockers") or [])
        raise RuntimeError(f"{label} blocked: {blockers or 'unknown blocker'}")
    return data


def _fingerprint(path: Path) -> dict[str, Any]:
    if path.is_dir():
        files = sorted(item.relative_to(path).as_posix() for item in path.rglob("*") if item.is_file())
        return {"exists": True, "file_count": len(files), "files": files}
    if path.is_file():
        return {"exists": True, "mtime_ns": path.stat().st_mtime_ns, "size": path.stat().st_size}
    return {"exists": False}


def _blockers(resp: dict[str, Any]) -> list[str]:
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    blockers = data.get("blockers") if isinstance(data.get("blockers"), list) else []
    return [str(item) for item in blockers]


def _drive_upload_handoff(fixture: Path) -> dict[str, Any]:
    api = StudioAPI(fixture)
    preview = _result_data(
        api.get_chaser_forge_marketplace_static_host_upload_handoff(),
        "static upload handoff preview",
    )
    wrong_handoff = api.write_chaser_forge_marketplace_static_host_upload_handoff(
        preview["remote_index_digest_sha256"],
        preview["hosted_bundle_digest_sha256"],
        preview["static_publication_digest_sha256"],
        "wrong",
    )
    wrong_static = api.write_chaser_forge_marketplace_static_host_upload_handoff(
        preview["remote_index_digest_sha256"],
        preview["hosted_bundle_digest_sha256"],
        "wrong",
        preview["upload_handoff_digest_sha256"],
    )
    written = _result_data(
        api.write_chaser_forge_marketplace_static_host_upload_handoff(
            preview["remote_index_digest_sha256"],
            preview["hosted_bundle_digest_sha256"],
            preview["static_publication_digest_sha256"],
            preview["upload_handoff_digest_sha256"],
        ),
        "static upload handoff write",
    )
    handoff_json = fixture / str(written.get("upload_handoff_json_path") or "")
    handoff_markdown = fixture / str(written.get("upload_handoff_markdown_path") or "")
    panel = _result_data(api.get_chaser_forge_panel(), "Chaser Forge panel")
    registry = build_native_shell_panel_registry(fixture)
    chaser_panel = next(
        (panel_item for panel_item in registry.get("panels") or [] if panel_item.get("id") == "chaser-forge"),
        {},
    )
    return {
        "preview": preview,
        "wrong_handoff": wrong_handoff,
        "wrong_static": wrong_static,
        "written": written,
        "handoff_json_exists": handoff_json.is_file(),
        "handoff_markdown_exists": handoff_markdown.is_file(),
        "panel_summary": panel.get("summary") or {},
        "panel_registry_api_methods": list(chaser_panel.get("api_methods") or []),
        "panel_registry_readiness": registry.get("readiness") or {},
    }


def _require(checks: dict[str, bool]) -> list[str]:
    return [name for name, ok in checks.items() if ok is not True]


def run_smoke(vault_root: str | Path, *, output_dir: str | Path, timeout_seconds: int) -> dict[str, Any]:
    faulthandler.dump_traceback_later(timeout_seconds, exit=True)
    started = time.perf_counter()
    vault = Path(vault_root).resolve()
    output_root = _resolve_inside_vault(vault, output_dir)
    fixture = (vault / "_cfstaticuploadhandoffsmoke").resolve()
    result_path = output_root / RESULT_NAME
    real_paths = {
        "registry": vault / "runtime" / "forge" / "registry" / "extensions.json",
        "catalog": vault / "runtime" / "forge" / "registry" / "marketplace-catalog.json",
        "remote_index_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Remote-Indexes",
        "hosted_bundle_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Hosted-Bundles",
        "static_publication_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Static-Host-Publications",
        "static_upload_handoff_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Static-Host-Upload-Handoffs",
    }
    real_fingerprints_before = {name: _fingerprint(path) for name, path in real_paths.items()}
    steps: list[dict[str, Any]] = []
    flow: dict[str, Any] = {}
    runner_error = ""
    if fixture.exists():
        shutil.rmtree(fixture, ignore_errors=True)
    fixture.mkdir(parents=True)
    try:
        steps.append({"step": "fixture_created", "elapsed_seconds": round(time.perf_counter() - started, 3)})
        flow = _drive_upload_handoff(fixture)
        steps.append(
            {"step": "studioapi_static_upload_handoff_flow_completed", "elapsed_seconds": round(time.perf_counter() - started, 3)}
        )
    except Exception as exc:  # noqa: BLE001
        runner_error = str(exc)
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
        fixture_cleanup_completed = not fixture.exists()
        faulthandler.cancel_dump_traceback_later()

    app_js_path = vault / "runtime" / "studio" / "shell" / "frontend" / "app.js"
    app_js = app_js_path.read_text(encoding="utf-8") if app_js_path.is_file() else ""
    preview = flow.get("preview") if isinstance(flow.get("preview"), dict) else {}
    written = flow.get("written") if isinstance(flow.get("written"), dict) else {}
    panel_summary = flow.get("panel_summary") if isinstance(flow.get("panel_summary"), dict) else {}
    registry_api_methods = flow.get("panel_registry_api_methods") if isinstance(flow.get("panel_registry_api_methods"), list) else []
    registry_readiness = flow.get("panel_registry_readiness") if isinstance(flow.get("panel_registry_readiness"), dict) else {}
    wrong_handoff_blockers = _blockers(flow.get("wrong_handoff") or {})
    wrong_static_blockers = _blockers(flow.get("wrong_static") or {})
    real_fingerprints_after = {name: _fingerprint(path) for name, path in real_paths.items()}

    checks = {
        "flow_completed_without_error": not runner_error,
        "upload_handoff_preview_ready": preview.get("ok") is True,
        "wrong_upload_handoff_digest_blocked": "expected_upload_handoff_digest_required_or_mismatched"
        in wrong_handoff_blockers,
        "wrong_static_publication_digest_blocked": bool(
            {
                "expected_static_publication_digest_required_or_mismatched",
                "expected_static_publication_digest_mismatch",
            }.intersection(wrong_static_blockers)
        ),
        "upload_handoff_written": written.get("upload_handoff_written") is True,
        "upload_handoff_files_written": flow.get("handoff_json_exists") is True
        and flow.get("handoff_markdown_exists") is True,
        "static_publication_files_present": written.get("static_publication_files_present") is True,
        "manual_upload_handoff_ready": written.get("manual_upload_handoff_ready") is True,
        "network_upload_blocked": written.get("network_upload_performed") is False
        and written.get("network_upload_allowed") is False,
        "external_registry_mutation_blocked": written.get("external_registry_mutation_allowed") is False,
        "payment_mutation_blocked": written.get("payment_mutation_allowed") is False,
        "license_checkout_blocked": written.get("license_checkout_allowed") is False,
        "package_install_blocked": written.get("package_install_allowed") is False,
        "panel_summary_upload_handoff_ready": panel_summary.get("marketplace_static_upload_handoff_ready") is True,
        "panel_registry_upload_handoff_methods_wired": all(
            method in registry_api_methods
            for method in (
                "get_chaser_forge_marketplace_static_host_upload_handoff",
                "write_chaser_forge_marketplace_static_host_upload_handoff",
            )
        ),
        "panel_registry_upload_handoff_readiness_wired": registry_readiness.get(
            "chaser_forge_marketplace_static_upload_handoff_ready"
        )
        is True
        and registry_readiness.get("chaser_forge_marketplace_static_upload_handoff_digest_gated") is True,
        "frontend_upload_handoff_section_wired": "Upload handoff" in app_js and "Write Upload Handoff" in app_js,
        "frontend_upload_handoff_api_tokens_wired": "get_chaser_forge_marketplace_static_host_upload_handoff" in app_js
        and "write_chaser_forge_marketplace_static_host_upload_handoff" in app_js,
        "real_vault_registry_catalog_remote_index_hosted_bundle_static_publication_upload_handoff_unchanged": (
            real_fingerprints_before == real_fingerprints_after
        ),
        "fixture_cleanup_completed": fixture_cleanup_completed,
    }
    failures = _require(checks)
    if runner_error:
        failures.append(f"runner_error:{runner_error}")
    result = {
        "ok": not failures,
        "status": SMOKE_STATUS if not failures else "BLOCKED / GOVERNED STATIC HOST UPLOAD HANDOFF FAILED",
        "date": "2026-05-23",
        "runtime": "Codex",
        "session_descriptor": "chaser-forge-manual-static-host-upload-handoff",
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "checks": checks,
        "failures": failures,
        "flow_summary": {
            "remote_index_digest_sha256": written.get("remote_index_digest_sha256") or "",
            "hosted_bundle_digest_sha256": written.get("hosted_bundle_digest_sha256") or "",
            "static_publication_digest_sha256": written.get("static_publication_digest_sha256") or "",
            "upload_handoff_digest_sha256": written.get("upload_handoff_digest_sha256") or "",
            "upload_handoff_json_path": written.get("upload_handoff_json_path") or "",
            "upload_handoff_markdown_path": written.get("upload_handoff_markdown_path") or "",
            "file_count": written.get("file_count"),
        },
        "authority": {
            "fixture_vault_writes_allowed": True,
            "real_vault_registry_write_allowed": False,
            "real_vault_catalog_write_allowed": False,
            "real_vault_remote_index_write_allowed": False,
            "real_vault_hosted_bundle_write_allowed": False,
            "real_vault_static_publication_write_allowed": False,
            "real_vault_static_upload_handoff_write_allowed": False,
            "remote_network_publish_allowed": False,
            "remote_network_fetch_allowed": False,
            "network_upload_allowed": False,
            "external_registry_mutation_allowed": False,
            "payment_mutation_allowed": False,
            "license_checkout_allowed": False,
            "package_install_allowed": False,
            "provider_or_model_call_allowed": False,
            "agent_bus_dispatch_allowed": False,
            "protected_core_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "result_path": str(result_path.relative_to(vault).as_posix()),
        "steps": steps,
    }
    _write(result_path, json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run direct Chaser Forge static-host upload handoff smoke test.")
    parser.add_argument("--vault-root", default=".", help="Path to ChaseOS vault root.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory inside the vault.")
    parser.add_argument("--timeout-seconds", type=int, default=30, help="Self-timeout before traceback dump and exit.")
    parser.add_argument("--json", action="store_true", help="Print JSON result.")
    args = parser.parse_args(argv)
    result = run_smoke(args.vault_root, output_dir=args.output_dir, timeout_seconds=args.timeout_seconds)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
