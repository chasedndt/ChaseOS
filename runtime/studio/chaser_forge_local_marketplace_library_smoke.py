"""Direct smoke test for Chaser Forge local Marketplace Library Studio use.

This smoke path avoids pytest and Playwright. It drives the existing StudioAPI
marketplace publish/install chain against a temporary fixture vault, then
verifies that the production Chaser Forge panel exposes the read-only Local
Marketplace Library model and frontend tokens.
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


SMOKE_STATUS = "COMPLETE / LOCAL MARKETPLACE LIBRARY STUDIO USE VERIFIED"
DEFAULT_OUTPUT_DIR = (
    Path("07_LOGS")
    / "Studio-Visual-QA"
    / "2026-05-22-chaser-forge-local-marketplace-library-studio-use-smoke"
)
RESULT_NAME = "chaser-forge-local-marketplace-library-studio-use-smoke-result.json"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_inside_vault(vault: Path, output_dir: str | Path) -> Path:
    raw = Path(output_dir)
    resolved = raw if raw.is_absolute() else vault / raw
    resolved = resolved.resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError("Marketplace library smoke output must stay inside the vault") from exc
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


def _approve(api: StudioAPI, fixture: Path, artifact_path: str, request_digest: str) -> dict[str, Any]:
    payload = _read_json(fixture / artifact_path)
    statement = str(payload.get("operator_confirmation_text") or "")
    if not statement:
        raise RuntimeError(f"operator confirmation statement missing for {artifact_path}")
    return _result_data(
        api.review_chaser_forge_approval_decision(
            artifact_path,
            "approved",
            request_digest,
            statement,
            write_decision=True,
            reviewer_id="studio-library-smoke",
        ),
        "Forge decision handoff",
    )


def _drive_marketplace_install(fixture: Path) -> dict[str, Any]:
    api = StudioAPI(fixture)
    publish_preview = _result_data(api.get_chaser_forge_marketplace_publish_preview(), "publish preview")
    published = _result_data(
        api.publish_chaser_forge_marketplace_package(publish_preview["listing_digest_sha256"]),
        "publish local catalog listing",
    )
    catalog = _result_data(api.get_chaser_forge_marketplace_catalog(), "catalog read")
    library_before = _result_data(api.get_chaser_forge_marketplace_local_library(), "library before install")
    panel_before = _result_data(api.get_chaser_forge_panel(), "panel before install")
    import_preview = ((panel_before.get("marketplace") or {}).get("import_approval_request") or {})
    import_request = _result_data(
        api.request_chaser_forge_marketplace_import_sandbox_approval(
            str(import_preview.get("request_digest_sha256") or "")
        ),
        "marketplace import approval request",
    )
    _approve(
        api,
        fixture,
        str(import_request["approval_artifact_path"]),
        str(import_request["request_digest_sha256"]),
    )
    bridge_preview = _result_data(
        api.get_chaser_forge_marketplace_import_sandbox_request(
            import_request["approval_artifact_path"],
            import_request["request_digest_sha256"],
        ),
        "marketplace sandbox request preview",
    )
    bridge_write = _result_data(
        api.request_chaser_forge_marketplace_import_sandbox_request(
            import_request["approval_artifact_path"],
            import_request["request_digest_sha256"],
            bridge_preview["request_digest_sha256"],
        ),
        "marketplace sandbox request write",
    )
    _approve(
        api,
        fixture,
        str(bridge_write["sandbox_approval_artifact_path"]),
        str(bridge_write["sandbox_request_digest_sha256"]),
    )
    executed = _result_data(
        api.execute_chaser_forge_marketplace_install(
            import_request["approval_artifact_path"],
            import_request["request_digest_sha256"],
            bridge_write["sandbox_approval_artifact_path"],
            bridge_write["sandbox_request_digest_sha256"],
            published["listing_digest_sha256"],
            published["listing_id"],
            bridge_write["request_digest_sha256"],
            True,
        ),
        "marketplace install execution",
    )
    library_after = _result_data(api.get_chaser_forge_marketplace_local_library(), "library after install")
    panel_after = _result_data(api.get_chaser_forge_panel(), "panel after install")
    registry = build_native_shell_panel_registry(fixture)
    chaser_panel = next(
        (panel for panel in registry.get("panels") or [] if panel.get("id") == "chaser-forge"),
        {},
    )
    return {
        "publish_preview": publish_preview,
        "published": published,
        "catalog": catalog,
        "library_before": library_before,
        "panel_before_summary": panel_before.get("summary") or {},
        "import_request": import_request,
        "bridge_write": bridge_write,
        "executed": executed,
        "library_after": library_after,
        "panel_after_summary": panel_after.get("summary") or {},
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
    fixture = (vault / "_cflibrarysmoke").resolve()
    result_path = output_root / RESULT_NAME
    real_registry_path = vault / "runtime" / "forge" / "registry" / "extensions.json"
    real_catalog_path = vault / "runtime" / "forge" / "registry" / "marketplace-catalog.json"
    real_path_fingerprints = {
        "registry_exists": real_registry_path.exists(),
        "registry_mtime_ns": real_registry_path.stat().st_mtime_ns if real_registry_path.exists() else None,
        "catalog_exists": real_catalog_path.exists(),
        "catalog_mtime_ns": real_catalog_path.stat().st_mtime_ns if real_catalog_path.exists() else None,
    }
    steps: list[dict[str, Any]] = []
    flow: dict[str, Any] = {}
    runner_error = ""
    if fixture.exists():
        shutil.rmtree(fixture, ignore_errors=True)
    fixture.mkdir(parents=True)
    try:
        steps.append({"step": "fixture_created", "elapsed_seconds": round(time.perf_counter() - started, 3)})
        flow = _drive_marketplace_install(fixture)
        steps.append({"step": "studioapi_marketplace_flow_completed", "elapsed_seconds": round(time.perf_counter() - started, 3)})
    except Exception as exc:  # noqa: BLE001
        runner_error = str(exc)
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
        fixture_cleanup_completed = not fixture.exists()
        faulthandler.cancel_dump_traceback_later()

    app_js_path = vault / "runtime" / "studio" / "shell" / "frontend" / "app.js"
    app_js = app_js_path.read_text(encoding="utf-8") if app_js_path.is_file() else ""
    library_before = flow.get("library_before") if isinstance(flow.get("library_before"), dict) else {}
    library_after = flow.get("library_after") if isinstance(flow.get("library_after"), dict) else {}
    panel_after_summary = flow.get("panel_after_summary") if isinstance(flow.get("panel_after_summary"), dict) else {}
    library_items = library_after.get("items") if isinstance(library_after.get("items"), list) else []
    item = library_items[0] if library_items and isinstance(library_items[0], dict) else {}
    registry_api_methods = flow.get("panel_registry_api_methods") if isinstance(flow.get("panel_registry_api_methods"), list) else []
    registry_readiness = flow.get("panel_registry_readiness") if isinstance(flow.get("panel_registry_readiness"), dict) else {}
    real_path_fingerprints_after = {
        "registry_exists": real_registry_path.exists(),
        "registry_mtime_ns": real_registry_path.stat().st_mtime_ns if real_registry_path.exists() else None,
        "catalog_exists": real_catalog_path.exists(),
        "catalog_mtime_ns": real_catalog_path.stat().st_mtime_ns if real_catalog_path.exists() else None,
    }

    checks = {
        "flow_completed_without_error": not runner_error,
        "library_before_listed_not_installed": library_before.get("listed_not_installed_count") == 1,
        "library_after_ok": library_after.get("ok") is True,
        "library_after_has_one_item": library_after.get("library_item_count") == 1,
        "library_after_listed_installed": library_after.get("listed_installed_count") == 1,
        "library_item_installed": item.get("installed") is True,
        "library_item_registry_status_visible": item.get("registry_status") == "sandbox_installed",
        "library_item_target_paths_verified": item.get("target_paths_existing_count") == item.get("target_path_count"),
        "panel_summary_library_ready": panel_after_summary.get("marketplace_local_library_ready") is True,
        "panel_summary_library_read_only": panel_after_summary.get("marketplace_local_library_read_only") is True,
        "panel_registry_api_wired": "get_chaser_forge_marketplace_local_library" in registry_api_methods,
        "panel_registry_readiness_wired": registry_readiness.get("chaser_forge_marketplace_local_library_ui_wired") is True,
        "frontend_library_section_wired": "Local Marketplace Library" in app_js
        and "data-marketplace-library-surface" in app_js,
        "frontend_library_api_token_wired": "get_chaser_forge_marketplace_local_library" in app_js,
        "remote_exchange_blocked": library_after.get("remote_marketplace_call_allowed") is False,
        "unauthorized_auto_install_blocked": library_after.get("unauthorized_auto_install_allowed") is False,
        "real_vault_registry_and_catalog_unchanged": real_path_fingerprints == real_path_fingerprints_after,
        "fixture_cleanup_completed": fixture_cleanup_completed,
    }
    failures = _require(checks)
    if runner_error:
        failures.append(f"runner_error:{runner_error}")
    result = {
        "ok": not failures,
        "status": SMOKE_STATUS if not failures else "BLOCKED / LOCAL MARKETPLACE LIBRARY STUDIO USE FAILED",
        "date": "2026-05-22",
        "runtime": "Codex",
        "session_descriptor": "chaser-forge-local-marketplace-studio-use",
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "checks": checks,
        "failures": failures,
        "flow_summary": {
            "published_listing_id": (flow.get("published") or {}).get("listing_id") if isinstance(flow.get("published"), dict) else "",
            "library_before_status": library_before.get("status") or "",
            "library_after_status": library_after.get("status") or "",
            "library_item_count": library_after.get("library_item_count"),
            "listed_installed_count": library_after.get("listed_installed_count"),
            "installed_unlisted_count": library_after.get("installed_unlisted_count"),
            "marketplace_install_executed": (flow.get("executed") or {}).get("marketplace_install_executed") if isinstance(flow.get("executed"), dict) else None,
            "registry_written_in_fixture": (flow.get("executed") or {}).get("registry_written") if isinstance(flow.get("executed"), dict) else None,
        },
        "authority": {
            "real_vault_registry_write_allowed": False,
            "real_vault_catalog_write_allowed": False,
            "fixture_vault_writes_allowed": True,
            "remote_marketplace_call_allowed": False,
            "third_party_package_exchange_allowed": False,
            "unauthorized_auto_install_allowed": False,
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
    parser = argparse.ArgumentParser(description="Run direct Chaser Forge local marketplace library Studio smoke test.")
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
