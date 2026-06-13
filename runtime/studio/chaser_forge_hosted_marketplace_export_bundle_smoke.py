"""Direct smoke test for Chaser Forge hosted marketplace export bundles.

This avoids browser and pytest wrappers. It drives the StudioAPI hosted bundle
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


SMOKE_STATUS = "COMPLETE / GOVERNED HOSTED MARKETPLACE EXPORT BUNDLE VERIFIED"
DEFAULT_OUTPUT_DIR = (
    Path("07_LOGS")
    / "Studio-Visual-QA"
    / "2026-05-22-chaser-forge-hosted-marketplace-export-bundle-smoke"
)
RESULT_NAME = "chaser-forge-hosted-marketplace-export-bundle-smoke-result.json"


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
        raise ValueError("Hosted bundle smoke output must stay inside the vault") from exc
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


def _drive_hosted_bundle(fixture: Path) -> dict[str, Any]:
    api = StudioAPI(fixture)
    hosted_preview = _result_data(
        api.get_chaser_forge_marketplace_hosted_export_bundle(),
        "hosted bundle preview",
    )
    wrong_bundle = api.write_chaser_forge_marketplace_hosted_export_bundle(
        hosted_preview["remote_index_digest_sha256"],
        "wrong",
    )
    wrong_remote = api.write_chaser_forge_marketplace_hosted_export_bundle(
        "wrong",
        hosted_preview["hosted_bundle_digest_sha256"],
    )
    hosted_bundle = _result_data(
        api.write_chaser_forge_marketplace_hosted_export_bundle(
            hosted_preview["remote_index_digest_sha256"],
            hosted_preview["hosted_bundle_digest_sha256"],
        ),
        "hosted bundle write",
    )
    panel = _result_data(api.get_chaser_forge_panel(), "Chaser Forge panel")
    registry = build_native_shell_panel_registry(fixture)
    chaser_panel = next(
        (panel_item for panel_item in registry.get("panels") or [] if panel_item.get("id") == "chaser-forge"),
        {},
    )
    return {
        "hosted_preview": hosted_preview,
        "wrong_bundle": wrong_bundle,
        "wrong_remote": wrong_remote,
        "hosted_bundle": hosted_bundle,
        "panel_summary": panel.get("summary") or {},
        "panel_marketplace": panel.get("marketplace") or {},
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
    fixture = (vault / "_cfhostedbundlesmoke").resolve()
    result_path = output_root / RESULT_NAME
    real_registry_path = vault / "runtime" / "forge" / "registry" / "extensions.json"
    real_catalog_path = vault / "runtime" / "forge" / "registry" / "marketplace-catalog.json"
    real_remote_index_dir = vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Remote-Indexes"
    real_hosted_bundle_dir = vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Hosted-Bundles"
    real_fingerprints_before = {
        "registry": _fingerprint(real_registry_path),
        "catalog": _fingerprint(real_catalog_path),
        "remote_index_dir": _fingerprint(real_remote_index_dir),
        "hosted_bundle_dir": _fingerprint(real_hosted_bundle_dir),
    }
    steps: list[dict[str, Any]] = []
    flow: dict[str, Any] = {}
    runner_error = ""
    if fixture.exists():
        shutil.rmtree(fixture, ignore_errors=True)
    fixture.mkdir(parents=True)
    try:
        steps.append({"step": "fixture_created", "elapsed_seconds": round(time.perf_counter() - started, 3)})
        flow = _drive_hosted_bundle(fixture)
        steps.append({"step": "studioapi_hosted_bundle_flow_completed", "elapsed_seconds": round(time.perf_counter() - started, 3)})
    except Exception as exc:  # noqa: BLE001
        runner_error = str(exc)
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
        fixture_cleanup_completed = not fixture.exists()
        faulthandler.cancel_dump_traceback_later()

    app_js_path = vault / "runtime" / "studio" / "shell" / "frontend" / "app.js"
    app_js = app_js_path.read_text(encoding="utf-8") if app_js_path.is_file() else ""
    hosted_preview = flow.get("hosted_preview") if isinstance(flow.get("hosted_preview"), dict) else {}
    hosted_bundle = flow.get("hosted_bundle") if isinstance(flow.get("hosted_bundle"), dict) else {}
    panel_summary = flow.get("panel_summary") if isinstance(flow.get("panel_summary"), dict) else {}
    registry_api_methods = flow.get("panel_registry_api_methods") if isinstance(flow.get("panel_registry_api_methods"), list) else []
    registry_readiness = flow.get("panel_registry_readiness") if isinstance(flow.get("panel_registry_readiness"), dict) else {}
    wrong_bundle_data = (flow.get("wrong_bundle") or {}).get("data") if isinstance(flow.get("wrong_bundle"), dict) else {}
    wrong_remote_data = (flow.get("wrong_remote") or {}).get("data") if isinstance(flow.get("wrong_remote"), dict) else {}
    real_fingerprints_after = {
        "registry": _fingerprint(real_registry_path),
        "catalog": _fingerprint(real_catalog_path),
        "remote_index_dir": _fingerprint(real_remote_index_dir),
        "hosted_bundle_dir": _fingerprint(real_hosted_bundle_dir),
    }

    checks = {
        "flow_completed_without_error": not runner_error,
        "hosted_preview_ready": hosted_preview.get("ok") is True,
        "wrong_bundle_digest_blocked": isinstance(wrong_bundle_data, dict)
        and wrong_bundle_data.get("ok") is False
        and "expected_hosted_bundle_digest_required_or_mismatched" in (wrong_bundle_data.get("blockers") or []),
        "wrong_remote_index_digest_blocked": isinstance(wrong_remote_data, dict)
        and wrong_remote_data.get("ok") is False
        and "expected_remote_index_digest_required_or_mismatched" in (wrong_remote_data.get("blockers") or []),
        "hosted_bundle_written": hosted_bundle.get("hosted_bundle_artifact_written") is True,
        "manual_static_host_ready": hosted_bundle.get("manual_static_host_ready") is True,
        "hosted_bundle_publication_manifest_ready": (hosted_bundle.get("publication_manifest") or {}).get("publication_mode")
        == "manual_static_host",
        "hosted_bundle_no_credentials": (hosted_bundle.get("publication_manifest") or {}).get("credentials_included") is False,
        "hosted_bundle_network_publish_blocked": hosted_bundle.get("remote_network_publish_allowed") is False,
        "hosted_bundle_payment_mutation_blocked": hosted_bundle.get("payment_mutation_allowed") is False,
        "hosted_bundle_license_checkout_blocked": hosted_bundle.get("license_checkout_allowed") is False,
        "hosted_bundle_package_install_blocked": hosted_bundle.get("package_install_allowed") is False,
        "panel_summary_hosted_ready": panel_summary.get("marketplace_hosted_export_bundle_ready") is True,
        "panel_summary_hosted_manual_static_ready": panel_summary.get("marketplace_hosted_export_manual_static_ready") is True,
        "panel_registry_hosted_methods_wired": all(
            method in registry_api_methods
            for method in (
                "get_chaser_forge_marketplace_hosted_export_bundle",
                "write_chaser_forge_marketplace_hosted_export_bundle",
            )
        ),
        "panel_registry_hosted_readiness_wired": registry_readiness.get("chaser_forge_marketplace_hosted_export_bundle_ready")
        is True
        and registry_readiness.get("chaser_forge_marketplace_hosted_export_bundle_digest_gated") is True,
        "frontend_hosted_section_wired": "Hosted bundle ready" in app_js
        and "Write Hosted Bundle" in app_js,
        "frontend_hosted_api_tokens_wired": "get_chaser_forge_marketplace_hosted_export_bundle" in app_js
        and "write_chaser_forge_marketplace_hosted_export_bundle" in app_js,
        "real_vault_registry_catalog_remote_index_hosted_bundle_unchanged": real_fingerprints_before
        == real_fingerprints_after,
        "fixture_cleanup_completed": fixture_cleanup_completed,
    }
    failures = _require(checks)
    if runner_error:
        failures.append(f"runner_error:{runner_error}")
    result = {
        "ok": not failures,
        "status": SMOKE_STATUS if not failures else "BLOCKED / GOVERNED HOSTED MARKETPLACE EXPORT BUNDLE FAILED",
        "date": "2026-05-22",
        "runtime": "Codex",
        "session_descriptor": "chaser-forge-hosted-marketplace-export-bundle",
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "checks": checks,
        "failures": failures,
        "flow_summary": {
            "remote_index_digest_sha256": hosted_bundle.get("remote_index_digest_sha256") or "",
            "hosted_bundle_digest_sha256": hosted_bundle.get("hosted_bundle_digest_sha256") or "",
            "hosted_bundle_artifact_path": hosted_bundle.get("hosted_bundle_artifact_path") or "",
            "entry_count": hosted_bundle.get("entry_count"),
            "publication_mode": (hosted_bundle.get("publication_manifest") or {}).get("publication_mode") or "",
        },
        "authority": {
            "fixture_vault_writes_allowed": True,
            "real_vault_registry_write_allowed": False,
            "real_vault_catalog_write_allowed": False,
            "real_vault_remote_index_write_allowed": False,
            "real_vault_hosted_bundle_write_allowed": False,
            "remote_network_publish_allowed": False,
            "remote_network_fetch_allowed": False,
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
    parser = argparse.ArgumentParser(description="Run direct Chaser Forge hosted marketplace export bundle smoke test.")
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
