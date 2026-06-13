"""Direct smoke test for Chaser Forge published static index registration.

This drives the StudioAPI registration preview/write path against a temporary
fixture vault. It verifies local registration artifacts and Studio wiring
without live URL fetch, network upload, external registry mutation,
payment/license mutation, package install, or real-vault Forge artifact writes.
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


SMOKE_STATUS = "COMPLETE / GOVERNED PUBLISHED STATIC INDEX REGISTRATION VERIFIED"
DEFAULT_OUTPUT_DIR = (
    Path("07_LOGS")
    / "Studio-Visual-QA"
    / "2026-05-24-chaser-forge-published-static-index-registration-smoke"
)
RESULT_NAME = "chaser-forge-published-static-index-registration-smoke-result.json"
PUBLISHED_INDEX_URL = "https://example.invalid/chaser-forge/index.json"
RECEIPT_BASE_URL = "https://example.invalid/chaser-forge"


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
        raise ValueError("Published static index registration smoke output must stay inside the vault") from exc
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


def _drive_registration(fixture: Path) -> dict[str, Any]:
    api = StudioAPI(fixture)
    api_preview = _result_data(
        api.get_chaser_forge_marketplace_published_static_index_registration(PUBLISHED_INDEX_URL),
        "published static index registration StudioAPI preview",
    )
    from runtime.forge.marketplace import (
        build_forge_marketplace_export_package,
        build_forge_marketplace_hosted_export_bundle,
        build_forge_marketplace_published_static_index_registration,
        build_forge_marketplace_remote_distribution,
        build_forge_marketplace_static_host_publication,
        build_forge_marketplace_static_host_upload_handoff,
        build_forge_marketplace_static_host_upload_receipt,
    )
    from runtime.forge.panel import build_chaser_forge_panel, load_demo_manifest

    package_preview = build_forge_marketplace_export_package(fixture, manifest=load_demo_manifest())
    distribution_preview = build_forge_marketplace_remote_distribution(
        fixture,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
    )
    written_index = build_forge_marketplace_remote_distribution(
        fixture,
        package_payload=package_preview["package_payload"],
        publisher_id="local-operator",
        publisher_public_key_fingerprint="local-test-fingerprint",
        write_index=True,
        expected_remote_index_digest=distribution_preview["remote_index_digest_sha256"],
    )
    hosted_preview = build_forge_marketplace_hosted_export_bundle(
        fixture,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        publisher_id="local-operator",
    )
    hosted_written = build_forge_marketplace_hosted_export_bundle(
        fixture,
        remote_index_artifact_path=written_index["remote_index_artifact_path"],
        expected_remote_index_digest=written_index["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_preview["hosted_bundle_digest_sha256"],
        publisher_id="local-operator",
        write_bundle=True,
    )
    publication_preview = build_forge_marketplace_static_host_publication(
        fixture,
        hosted_bundle_artifact_path=hosted_written["hosted_bundle_artifact_path"],
        expected_remote_index_digest=hosted_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_written["hosted_bundle_digest_sha256"],
    )
    publication_written = build_forge_marketplace_static_host_publication(
        fixture,
        hosted_bundle_artifact_path=hosted_written["hosted_bundle_artifact_path"],
        expected_remote_index_digest=hosted_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=hosted_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_preview["static_publication_digest_sha256"],
        write_publication=True,
    )
    handoff_preview = build_forge_marketplace_static_host_upload_handoff(
        fixture,
        static_publication_preview=publication_written,
        expected_remote_index_digest=publication_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=publication_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_written["static_publication_digest_sha256"],
        declared_static_base_url=RECEIPT_BASE_URL,
    )
    handoff_written = build_forge_marketplace_static_host_upload_handoff(
        fixture,
        static_publication_preview=publication_written,
        expected_remote_index_digest=publication_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=publication_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=publication_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=handoff_preview["upload_handoff_digest_sha256"],
        declared_static_base_url=RECEIPT_BASE_URL,
        write_handoff=True,
    )
    receipt_preview = build_forge_marketplace_static_host_upload_receipt(
        fixture,
        upload_handoff_artifact_path=handoff_written["upload_handoff_json_path"],
        expected_remote_index_digest=handoff_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=handoff_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=handoff_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=handoff_written["upload_handoff_digest_sha256"],
        operator_uploaded_base_url=RECEIPT_BASE_URL,
    )
    receipt_written = build_forge_marketplace_static_host_upload_receipt(
        fixture,
        upload_handoff_artifact_path=handoff_written["upload_handoff_json_path"],
        expected_remote_index_digest=handoff_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=handoff_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=handoff_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=handoff_written["upload_handoff_digest_sha256"],
        expected_upload_receipt_digest=receipt_preview["upload_receipt_digest_sha256"],
        operator_uploaded_base_url=RECEIPT_BASE_URL,
        operator_receipt_statement=receipt_preview["required_operator_receipt_statement"],
        write_receipt=True,
    )
    preview = build_forge_marketplace_published_static_index_registration(
        fixture,
        upload_receipt_artifact_path=receipt_written["upload_receipt_json_path"],
        expected_remote_index_digest=receipt_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=receipt_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=receipt_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=receipt_written["upload_handoff_digest_sha256"],
        expected_upload_receipt_digest=receipt_written["upload_receipt_digest_sha256"],
        operator_published_static_index_url=PUBLISHED_INDEX_URL,
    )
    wrong_registration = {
        "data": build_forge_marketplace_published_static_index_registration(
            fixture,
            upload_receipt_artifact_path=receipt_written["upload_receipt_json_path"],
            expected_published_static_index_registration_digest="wrong",
            operator_published_static_index_url=PUBLISHED_INDEX_URL,
            operator_registration_statement=preview["required_operator_registration_statement"],
            write_registration=True,
        )
    }
    wrong_statement = {
        "data": build_forge_marketplace_published_static_index_registration(
            fixture,
            upload_receipt_artifact_path=receipt_written["upload_receipt_json_path"],
            expected_published_static_index_registration_digest=preview[
                "published_static_index_registration_digest_sha256"
            ],
            operator_published_static_index_url=PUBLISHED_INDEX_URL,
            operator_registration_statement="wrong",
            write_registration=True,
        )
    }
    wrong_receipt = {
        "data": build_forge_marketplace_published_static_index_registration(
            fixture,
            upload_receipt_artifact_path=receipt_written["upload_receipt_json_path"],
            expected_upload_receipt_digest="wrong",
            expected_published_static_index_registration_digest=preview[
                "published_static_index_registration_digest_sha256"
            ],
            operator_published_static_index_url=PUBLISHED_INDEX_URL,
            operator_registration_statement=preview["required_operator_registration_statement"],
            write_registration=True,
        )
    }
    written = build_forge_marketplace_published_static_index_registration(
        fixture,
        upload_receipt_artifact_path=receipt_written["upload_receipt_json_path"],
        expected_remote_index_digest=receipt_written["remote_index_digest_sha256"],
        expected_hosted_bundle_digest=receipt_written["hosted_bundle_digest_sha256"],
        expected_static_publication_digest=receipt_written["static_publication_digest_sha256"],
        expected_upload_handoff_digest=receipt_written["upload_handoff_digest_sha256"],
        expected_upload_receipt_digest=receipt_written["upload_receipt_digest_sha256"],
        expected_published_static_index_registration_digest=preview[
            "published_static_index_registration_digest_sha256"
        ],
        operator_published_static_index_url=PUBLISHED_INDEX_URL,
        operator_registration_statement=preview["required_operator_registration_statement"],
        write_registration=True,
    )
    if written.get("ok") is not True:
        blockers = "; ".join(str(item) for item in written.get("blockers") or [])
        raise RuntimeError(f"builder registration write blocked: {blockers or 'unknown blocker'}")
    registration_json = fixture / str(written.get("published_static_index_registration_json_path") or "")
    registration_markdown = fixture / str(written.get("published_static_index_registration_markdown_path") or "")
    panel = build_chaser_forge_panel(fixture)
    registry = build_native_shell_panel_registry(fixture)
    chaser_panel = next(
        (panel_item for panel_item in registry.get("panels") or [] if panel_item.get("id") == "chaser-forge"),
        {},
    )
    return {
        "preview": preview,
        "api_preview": api_preview,
        "receipt_preview": receipt_preview,
        "wrong_registration": wrong_registration,
        "wrong_statement": wrong_statement,
        "wrong_receipt": wrong_receipt,
        "written": written,
        "registration_json_exists": registration_json.is_file(),
        "registration_markdown_exists": registration_markdown.is_file(),
        "registration_payload": json.loads(registration_json.read_text(encoding="utf-8"))
        if registration_json.is_file()
        else {},
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
    fixture = (vault / "_cfpublishedindexregistrationsmoke").resolve()
    result_path = output_root / RESULT_NAME
    real_paths = {
        "registry": vault / "runtime" / "forge" / "registry" / "extensions.json",
        "catalog": vault / "runtime" / "forge" / "registry" / "marketplace-catalog.json",
        "remote_index_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Remote-Indexes",
        "hosted_bundle_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Hosted-Bundles",
        "static_publication_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Static-Host-Publications",
        "static_upload_handoff_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Static-Host-Upload-Handoffs",
        "static_upload_receipt_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Static-Host-Upload-Receipts",
        "published_static_index_registration_dir": vault
        / "07_LOGS"
        / "Workflow-Proofs"
        / "Forge-Marketplace-Published-Static-Index-Registrations",
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
        flow = _drive_registration(fixture)
        steps.append(
            {
                "step": "studioapi_published_static_index_registration_flow_completed",
                "elapsed_seconds": round(time.perf_counter() - started, 3),
            }
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
    registration_payload = flow.get("registration_payload") if isinstance(flow.get("registration_payload"), dict) else {}
    panel_summary = flow.get("panel_summary") if isinstance(flow.get("panel_summary"), dict) else {}
    registry_api_methods = flow.get("panel_registry_api_methods") if isinstance(flow.get("panel_registry_api_methods"), list) else []
    registry_readiness = flow.get("panel_registry_readiness") if isinstance(flow.get("panel_registry_readiness"), dict) else {}
    wrong_registration_blockers = _blockers(flow.get("wrong_registration") or {})
    wrong_statement_blockers = _blockers(flow.get("wrong_statement") or {})
    wrong_receipt_blockers = _blockers(flow.get("wrong_receipt") or {})
    real_fingerprints_after = {name: _fingerprint(path) for name, path in real_paths.items()}

    checks = {
        "flow_completed_without_error": not runner_error,
        "published_static_index_registration_preview_ready": preview.get("ok") is True,
        "wrong_published_static_index_registration_digest_blocked": (
            "expected_published_static_index_registration_digest_required_or_mismatched"
            in wrong_registration_blockers
        ),
        "wrong_operator_registration_statement_blocked": (
            "operator_registration_statement_required_or_mismatched" in wrong_statement_blockers
        ),
        "wrong_upload_receipt_digest_blocked": "expected_upload_receipt_digest_mismatch" in wrong_receipt_blockers,
        "published_static_index_registration_written": (
            written.get("published_static_index_registration_written") is True
        ),
        "published_static_index_registration_files_written": flow.get("registration_json_exists") is True
        and flow.get("registration_markdown_exists") is True,
        "operator_registration_statement_recorded": registration_payload.get("operator_registration_statement")
        == preview.get("required_operator_registration_statement"),
        "operator_declared_published_index_registered": (
            written.get("operator_declared_published_index_registered") is True
        ),
        "live_url_fetch_unverified_and_blocked": written.get("live_url_verified") is False
        and written.get("network_fetch_performed") is False
        and written.get("network_fetch_allowed") is False,
        "network_upload_blocked": written.get("network_upload_performed") is False
        and written.get("network_upload_allowed") is False,
        "external_registry_mutation_blocked": written.get("external_registry_mutation_allowed") is False,
        "payment_mutation_blocked": written.get("payment_mutation_allowed") is False,
        "license_checkout_blocked": written.get("license_checkout_allowed") is False,
        "package_install_blocked": written.get("package_install_allowed") is False,
        "panel_summary_published_static_index_registration_ready": panel_summary.get(
            "marketplace_published_static_index_registration_ready"
        )
        is True,
        "panel_registry_published_static_index_registration_methods_wired": all(
            method in registry_api_methods
            for method in (
                "get_chaser_forge_marketplace_published_static_index_registration",
                "write_chaser_forge_marketplace_published_static_index_registration",
            )
        ),
        "panel_registry_published_static_index_registration_readiness_wired": registry_readiness.get(
            "chaser_forge_marketplace_published_static_index_registration_ready"
        )
        is True
        and registry_readiness.get(
            "chaser_forge_marketplace_published_static_index_registration_digest_gated"
        )
        is True,
        "frontend_published_static_index_registration_section_wired": "Published index registration" in app_js
        and "Register Published Index" in app_js,
        "frontend_published_static_index_registration_api_tokens_wired": (
            "get_chaser_forge_marketplace_published_static_index_registration" in app_js
            and "write_chaser_forge_marketplace_published_static_index_registration" in app_js
        ),
        "real_vault_registry_catalog_distribution_registration_paths_unchanged": (
            real_fingerprints_before == real_fingerprints_after
        ),
        "fixture_cleanup_completed": fixture_cleanup_completed,
    }
    failures = _require(checks)
    if runner_error:
        failures.append(f"runner_error:{runner_error}")
    result = {
        "ok": not failures,
        "status": SMOKE_STATUS if not failures else "BLOCKED / GOVERNED PUBLISHED STATIC INDEX REGISTRATION FAILED",
        "date": "2026-05-24",
        "runtime": "Codex",
        "session_descriptor": "chaser-forge-published-static-index-registration",
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "checks": checks,
        "failures": failures,
        "flow_summary": {
            "remote_index_digest_sha256": written.get("remote_index_digest_sha256") or "",
            "hosted_bundle_digest_sha256": written.get("hosted_bundle_digest_sha256") or "",
            "static_publication_digest_sha256": written.get("static_publication_digest_sha256") or "",
            "upload_handoff_digest_sha256": written.get("upload_handoff_digest_sha256") or "",
            "upload_receipt_digest_sha256": written.get("upload_receipt_digest_sha256") or "",
            "published_static_index_registration_digest_sha256": written.get(
                "published_static_index_registration_digest_sha256"
            )
            or "",
            "published_static_index_registration_json_path": written.get(
                "published_static_index_registration_json_path"
            )
            or "",
            "published_static_index_registration_markdown_path": written.get(
                "published_static_index_registration_markdown_path"
            )
            or "",
            "operator_published_static_index_url": written.get("operator_published_static_index_url") or "",
            "file_count": len(registration_payload.get("source_receipt_hosted_file_receipts") or []),
        },
        "authority": {
            "fixture_vault_writes_allowed": True,
            "real_vault_registry_write_allowed": False,
            "real_vault_catalog_write_allowed": False,
            "real_vault_distribution_registration_write_allowed": False,
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
    parser = argparse.ArgumentParser(description="Run direct Chaser Forge published static index registration smoke test.")
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
