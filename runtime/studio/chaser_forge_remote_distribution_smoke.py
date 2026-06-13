"""Direct smoke test for Chaser Forge governed remote distribution.

This avoids browser and pytest wrappers. It drives the StudioAPI remote index
write plus verified remote listing ingest against a temporary fixture vault,
then verifies the production Chaser Forge panel, registry, and frontend tokens.
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


SMOKE_STATUS = "COMPLETE / GOVERNED REMOTE DISTRIBUTION FOUNDATION VERIFIED"
DEFAULT_OUTPUT_DIR = (
    Path("07_LOGS")
    / "Studio-Visual-QA"
    / "2026-05-22-chaser-forge-remote-distribution-foundation-smoke"
)
RESULT_NAME = "chaser-forge-remote-distribution-foundation-smoke-result.json"


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
        raise ValueError("Remote distribution smoke output must stay inside the vault") from exc
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


def _drive_remote_distribution(fixture: Path) -> dict[str, Any]:
    api = StudioAPI(fixture)
    remote_preview = _result_data(
        api.get_chaser_forge_marketplace_remote_distribution(),
        "remote distribution preview",
    )
    wrong_write = api.write_chaser_forge_marketplace_remote_index("wrong")
    remote_index = _result_data(
        api.write_chaser_forge_marketplace_remote_index(remote_preview["remote_index_digest_sha256"]),
        "remote index write",
    )
    ingest_preview = _result_data(
        api.ingest_chaser_forge_marketplace_remote_listing(
            remote_index["remote_index_artifact_path"],
            remote_index["remote_index_digest_sha256"],
            remote_index["listing_digest_sha256"],
            "",
            write_listing=False,
        ),
        "remote listing ingest preview",
    )
    wrong_ingest = api.ingest_chaser_forge_marketplace_remote_listing(
        remote_index["remote_index_artifact_path"],
        remote_index["remote_index_digest_sha256"],
        remote_index["listing_digest_sha256"],
        "wrong",
        write_listing=True,
    )
    ingested = _result_data(
        api.ingest_chaser_forge_marketplace_remote_listing(
            remote_index["remote_index_artifact_path"],
            remote_index["remote_index_digest_sha256"],
            remote_index["listing_digest_sha256"],
            ingest_preview["operator_confirmation_text"],
            write_listing=True,
        ),
        "remote listing ingest",
    )
    catalog = _result_data(api.get_chaser_forge_marketplace_catalog(), "marketplace catalog")
    library = _result_data(api.get_chaser_forge_marketplace_local_library(), "marketplace local library")
    panel = _result_data(api.get_chaser_forge_panel(), "Chaser Forge panel")
    registry = build_native_shell_panel_registry(fixture)
    chaser_panel = next(
        (panel_item for panel_item in registry.get("panels") or [] if panel_item.get("id") == "chaser-forge"),
        {},
    )
    return {
        "remote_preview": remote_preview,
        "wrong_write": wrong_write,
        "remote_index": remote_index,
        "ingest_preview": ingest_preview,
        "wrong_ingest": wrong_ingest,
        "ingested": ingested,
        "catalog": catalog,
        "library": library,
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
    fixture = (vault / "_cfremotedistsmoke").resolve()
    result_path = output_root / RESULT_NAME
    real_registry_path = vault / "runtime" / "forge" / "registry" / "extensions.json"
    real_catalog_path = vault / "runtime" / "forge" / "registry" / "marketplace-catalog.json"
    real_remote_index_dir = vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Remote-Indexes"
    real_fingerprints_before = {
        "registry": _fingerprint(real_registry_path),
        "catalog": _fingerprint(real_catalog_path),
        "remote_index_dir": _fingerprint(real_remote_index_dir),
    }
    steps: list[dict[str, Any]] = []
    flow: dict[str, Any] = {}
    runner_error = ""
    if fixture.exists():
        shutil.rmtree(fixture, ignore_errors=True)
    fixture.mkdir(parents=True)
    try:
        steps.append({"step": "fixture_created", "elapsed_seconds": round(time.perf_counter() - started, 3)})
        flow = _drive_remote_distribution(fixture)
        steps.append({"step": "studioapi_remote_distribution_flow_completed", "elapsed_seconds": round(time.perf_counter() - started, 3)})
    except Exception as exc:  # noqa: BLE001
        runner_error = str(exc)
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
        fixture_cleanup_completed = not fixture.exists()
        faulthandler.cancel_dump_traceback_later()

    app_js_path = vault / "runtime" / "studio" / "shell" / "frontend" / "app.js"
    app_js = app_js_path.read_text(encoding="utf-8") if app_js_path.is_file() else ""
    remote_preview = flow.get("remote_preview") if isinstance(flow.get("remote_preview"), dict) else {}
    remote_index = flow.get("remote_index") if isinstance(flow.get("remote_index"), dict) else {}
    ingest_preview = flow.get("ingest_preview") if isinstance(flow.get("ingest_preview"), dict) else {}
    ingested = flow.get("ingested") if isinstance(flow.get("ingested"), dict) else {}
    catalog = flow.get("catalog") if isinstance(flow.get("catalog"), dict) else {}
    library = flow.get("library") if isinstance(flow.get("library"), dict) else {}
    panel_summary = flow.get("panel_summary") if isinstance(flow.get("panel_summary"), dict) else {}
    registry_api_methods = flow.get("panel_registry_api_methods") if isinstance(flow.get("panel_registry_api_methods"), list) else []
    registry_readiness = flow.get("panel_registry_readiness") if isinstance(flow.get("panel_registry_readiness"), dict) else {}
    catalog_entries = catalog.get("entries") if isinstance(catalog.get("entries"), list) else []
    catalog_entry = catalog_entries[0] if catalog_entries and isinstance(catalog_entries[0], dict) else {}
    library_items = library.get("items") if isinstance(library.get("items"), list) else []
    library_item = library_items[0] if library_items and isinstance(library_items[0], dict) else {}
    wrong_write_data = (flow.get("wrong_write") or {}).get("data") if isinstance(flow.get("wrong_write"), dict) else {}
    wrong_ingest_data = (flow.get("wrong_ingest") or {}).get("data") if isinstance(flow.get("wrong_ingest"), dict) else {}
    real_fingerprints_after = {
        "registry": _fingerprint(real_registry_path),
        "catalog": _fingerprint(real_catalog_path),
        "remote_index_dir": _fingerprint(real_remote_index_dir),
    }

    checks = {
        "flow_completed_without_error": not runner_error,
        "remote_preview_ready": remote_preview.get("ok") is True,
        "wrong_index_digest_blocked": isinstance(wrong_write_data, dict)
        and wrong_write_data.get("ok") is False
        and "expected_remote_index_digest_required_or_mismatched" in (wrong_write_data.get("blockers") or []),
        "remote_index_written": remote_index.get("remote_index_artifact_written") is True,
        "remote_network_publish_blocked": remote_index.get("remote_network_publish_allowed") is False,
        "remote_payment_mutation_blocked": remote_index.get("payment_mutation_allowed") is False,
        "remote_license_checkout_blocked": remote_index.get("license_checkout_allowed") is False,
        "ingest_preview_trusted": ingest_preview.get("publisher_trusted") is True,
        "ingest_preview_attestation_verified": ingest_preview.get("publisher_attestation_verified") is True,
        "wrong_ingest_statement_blocked": isinstance(wrong_ingest_data, dict)
        and wrong_ingest_data.get("ok") is False
        and "operator_confirmation_required_or_mismatched" in (wrong_ingest_data.get("blockers") or []),
        "remote_listing_ingested": ingested.get("remote_listing_ingested") is True,
        "catalog_entry_written": catalog.get("entry_count") == 1
        and catalog_entry.get("remote_distribution_source") == "verified_remote_index",
        "library_remote_item_visible": library.get("library_item_count") == 1
        and library_item.get("source") == "remote_verified_catalog",
        "library_item_not_installed": library_item.get("installed") is False,
        "panel_summary_remote_ready": panel_summary.get("marketplace_remote_distribution_ready") is True,
        "panel_summary_remote_ingest_ready": panel_summary.get("marketplace_remote_ingest_preview_ready") is True,
        "panel_registry_remote_methods_wired": all(
            method in registry_api_methods
            for method in (
                "get_chaser_forge_marketplace_remote_distribution",
                "write_chaser_forge_marketplace_remote_index",
                "ingest_chaser_forge_marketplace_remote_listing",
            )
        ),
        "panel_registry_remote_readiness_wired": registry_readiness.get("chaser_forge_marketplace_remote_distribution_ready") is True
        and registry_readiness.get("chaser_forge_marketplace_remote_ingest_preview_ready") is True,
        "frontend_remote_section_wired": "Remote Distribution" in app_js
        and "data-marketplace-remote-surface" in app_js
        and "Write Remote Index" in app_js
        and "Ingest Remote Listing" in app_js,
        "frontend_remote_api_tokens_wired": "get_chaser_forge_marketplace_remote_distribution" in app_js
        and "write_chaser_forge_marketplace_remote_index" in app_js
        and "ingest_chaser_forge_marketplace_remote_listing" in app_js,
        "real_vault_registry_catalog_remote_index_unchanged": real_fingerprints_before == real_fingerprints_after,
        "fixture_cleanup_completed": fixture_cleanup_completed,
    }
    failures = _require(checks)
    if runner_error:
        failures.append(f"runner_error:{runner_error}")
    result = {
        "ok": not failures,
        "status": SMOKE_STATUS if not failures else "BLOCKED / GOVERNED REMOTE DISTRIBUTION FOUNDATION FAILED",
        "date": "2026-05-22",
        "runtime": "Codex",
        "session_descriptor": "chaser-forge-remote-distribution-foundation",
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "checks": checks,
        "failures": failures,
        "flow_summary": {
            "remote_index_digest_sha256": remote_index.get("remote_index_digest_sha256") or "",
            "listing_digest_sha256": remote_index.get("listing_digest_sha256") or "",
            "remote_index_artifact_path": remote_index.get("remote_index_artifact_path") or "",
            "ingested_listing_id": ingested.get("listing_id") or "",
            "catalog_entry_count": catalog.get("entry_count"),
            "library_item_count": library.get("library_item_count"),
        },
        "authority": {
            "fixture_vault_writes_allowed": True,
            "real_vault_registry_write_allowed": False,
            "real_vault_catalog_write_allowed": False,
            "real_vault_remote_index_write_allowed": False,
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
    parser = argparse.ArgumentParser(description="Run direct Chaser Forge remote distribution smoke test.")
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
