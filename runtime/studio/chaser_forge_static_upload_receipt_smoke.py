"""Direct smoke test for Chaser Forge static-host upload receipt proof.

This drives the StudioAPI receipt preview/write path against a temporary
fixture vault. It verifies local receipt artifacts and Studio wiring without
network fetch, network upload, external registry mutation, payment/license
mutation, package install, or real-vault Forge artifact writes.
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


SMOKE_STATUS = "COMPLETE / GOVERNED STATIC HOST UPLOAD RECEIPT VERIFIED"
DEFAULT_OUTPUT_DIR = (
    Path("07_LOGS")
    / "Studio-Visual-QA"
    / "2026-05-23-chaser-forge-static-upload-receipt-smoke"
)
RESULT_NAME = "chaser-forge-static-upload-receipt-smoke-result.json"
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
        raise ValueError("Static upload receipt smoke output must stay inside the vault") from exc
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


def _drive_upload_receipt(fixture: Path) -> dict[str, Any]:
    api = StudioAPI(fixture)
    preview = _result_data(
        api.get_chaser_forge_marketplace_static_host_upload_receipt(RECEIPT_BASE_URL),
        "static upload receipt preview",
    )
    wrong_receipt = api.write_chaser_forge_marketplace_static_host_upload_receipt(
        preview["remote_index_digest_sha256"],
        preview["hosted_bundle_digest_sha256"],
        preview["static_publication_digest_sha256"],
        preview["upload_handoff_digest_sha256"],
        "wrong",
        preview["operator_uploaded_base_url"],
        preview["required_operator_receipt_statement"],
    )
    wrong_statement = api.write_chaser_forge_marketplace_static_host_upload_receipt(
        preview["remote_index_digest_sha256"],
        preview["hosted_bundle_digest_sha256"],
        preview["static_publication_digest_sha256"],
        preview["upload_handoff_digest_sha256"],
        preview["upload_receipt_digest_sha256"],
        preview["operator_uploaded_base_url"],
        "wrong",
    )
    wrong_handoff = api.write_chaser_forge_marketplace_static_host_upload_receipt(
        preview["remote_index_digest_sha256"],
        preview["hosted_bundle_digest_sha256"],
        preview["static_publication_digest_sha256"],
        "wrong",
        preview["upload_receipt_digest_sha256"],
        preview["operator_uploaded_base_url"],
        preview["required_operator_receipt_statement"],
    )
    written = _result_data(
        api.write_chaser_forge_marketplace_static_host_upload_receipt(
            preview["remote_index_digest_sha256"],
            preview["hosted_bundle_digest_sha256"],
            preview["static_publication_digest_sha256"],
            preview["upload_handoff_digest_sha256"],
            preview["upload_receipt_digest_sha256"],
            preview["operator_uploaded_base_url"],
            preview["required_operator_receipt_statement"],
        ),
        "static upload receipt write",
    )
    receipt_json = fixture / str(written.get("upload_receipt_json_path") or "")
    receipt_markdown = fixture / str(written.get("upload_receipt_markdown_path") or "")
    panel = _result_data(api.get_chaser_forge_panel(), "Chaser Forge panel")
    registry = build_native_shell_panel_registry(fixture)
    chaser_panel = next(
        (panel_item for panel_item in registry.get("panels") or [] if panel_item.get("id") == "chaser-forge"),
        {},
    )
    return {
        "preview": preview,
        "wrong_receipt": wrong_receipt,
        "wrong_statement": wrong_statement,
        "wrong_handoff": wrong_handoff,
        "written": written,
        "receipt_json_exists": receipt_json.is_file(),
        "receipt_markdown_exists": receipt_markdown.is_file(),
        "receipt_payload": json.loads(receipt_json.read_text(encoding="utf-8")) if receipt_json.is_file() else {},
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
    fixture = (vault / "_cfstaticuploadreceiptsmoke").resolve()
    result_path = output_root / RESULT_NAME
    real_paths = {
        "registry": vault / "runtime" / "forge" / "registry" / "extensions.json",
        "catalog": vault / "runtime" / "forge" / "registry" / "marketplace-catalog.json",
        "remote_index_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Remote-Indexes",
        "hosted_bundle_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Hosted-Bundles",
        "static_publication_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Static-Host-Publications",
        "static_upload_handoff_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Static-Host-Upload-Handoffs",
        "static_upload_receipt_dir": vault / "07_LOGS" / "Workflow-Proofs" / "Forge-Marketplace-Static-Host-Upload-Receipts",
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
        flow = _drive_upload_receipt(fixture)
        steps.append(
            {"step": "studioapi_static_upload_receipt_flow_completed", "elapsed_seconds": round(time.perf_counter() - started, 3)}
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
    receipt_payload = flow.get("receipt_payload") if isinstance(flow.get("receipt_payload"), dict) else {}
    panel_summary = flow.get("panel_summary") if isinstance(flow.get("panel_summary"), dict) else {}
    registry_api_methods = flow.get("panel_registry_api_methods") if isinstance(flow.get("panel_registry_api_methods"), list) else []
    registry_readiness = flow.get("panel_registry_readiness") if isinstance(flow.get("panel_registry_readiness"), dict) else {}
    wrong_receipt_blockers = _blockers(flow.get("wrong_receipt") or {})
    wrong_statement_blockers = _blockers(flow.get("wrong_statement") or {})
    wrong_handoff_blockers = _blockers(flow.get("wrong_handoff") or {})
    real_fingerprints_after = {name: _fingerprint(path) for name, path in real_paths.items()}

    checks = {
        "flow_completed_without_error": not runner_error,
        "upload_receipt_preview_ready": preview.get("ok") is True,
        "wrong_upload_receipt_digest_blocked": "expected_upload_receipt_digest_required_or_mismatched"
        in wrong_receipt_blockers,
        "wrong_operator_receipt_statement_blocked": "operator_receipt_statement_required_or_mismatched"
        in wrong_statement_blockers,
        "wrong_upload_handoff_digest_blocked": "expected_upload_handoff_digest_mismatch" in wrong_handoff_blockers,
        "upload_receipt_written": written.get("upload_receipt_written") is True,
        "upload_receipt_files_written": flow.get("receipt_json_exists") is True
        and flow.get("receipt_markdown_exists") is True,
        "operator_receipt_statement_recorded": receipt_payload.get("operator_receipt_statement")
        == preview.get("required_operator_receipt_statement"),
        "operator_manual_upload_claim_recorded": written.get("operator_manual_upload_claim_recorded") is True,
        "network_fetch_blocked": written.get("network_fetch_performed") is False
        and written.get("network_fetch_allowed") is False,
        "network_upload_blocked": written.get("network_upload_performed") is False
        and written.get("network_upload_allowed") is False,
        "external_registry_mutation_blocked": written.get("external_registry_mutation_allowed") is False,
        "payment_mutation_blocked": written.get("payment_mutation_allowed") is False,
        "license_checkout_blocked": written.get("license_checkout_allowed") is False,
        "package_install_blocked": written.get("package_install_allowed") is False,
        "panel_summary_upload_receipt_ready": panel_summary.get("marketplace_static_upload_receipt_ready") is True,
        "panel_registry_upload_receipt_methods_wired": all(
            method in registry_api_methods
            for method in (
                "get_chaser_forge_marketplace_static_host_upload_receipt",
                "write_chaser_forge_marketplace_static_host_upload_receipt",
            )
        ),
        "panel_registry_upload_receipt_readiness_wired": registry_readiness.get(
            "chaser_forge_marketplace_static_upload_receipt_ready"
        )
        is True
        and registry_readiness.get("chaser_forge_marketplace_static_upload_receipt_digest_gated") is True,
        "frontend_upload_receipt_section_wired": "Upload receipt" in app_js and "Write Upload Receipt" in app_js,
        "frontend_upload_receipt_api_tokens_wired": "get_chaser_forge_marketplace_static_host_upload_receipt" in app_js
        and "write_chaser_forge_marketplace_static_host_upload_receipt" in app_js,
        "real_vault_registry_catalog_remote_index_hosted_bundle_static_publication_upload_handoff_upload_receipt_unchanged": (
            real_fingerprints_before == real_fingerprints_after
        ),
        "fixture_cleanup_completed": fixture_cleanup_completed,
    }
    failures = _require(checks)
    if runner_error:
        failures.append(f"runner_error:{runner_error}")
    result = {
        "ok": not failures,
        "status": SMOKE_STATUS if not failures else "BLOCKED / GOVERNED STATIC HOST UPLOAD RECEIPT FAILED",
        "date": "2026-05-23",
        "runtime": "Codex",
        "session_descriptor": "chaser-forge-static-host-upload-receipt-proof",
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "checks": checks,
        "failures": failures,
        "flow_summary": {
            "remote_index_digest_sha256": written.get("remote_index_digest_sha256") or "",
            "hosted_bundle_digest_sha256": written.get("hosted_bundle_digest_sha256") or "",
            "static_publication_digest_sha256": written.get("static_publication_digest_sha256") or "",
            "upload_handoff_digest_sha256": written.get("upload_handoff_digest_sha256") or "",
            "upload_receipt_digest_sha256": written.get("upload_receipt_digest_sha256") or "",
            "upload_receipt_json_path": written.get("upload_receipt_json_path") or "",
            "upload_receipt_markdown_path": written.get("upload_receipt_markdown_path") or "",
            "operator_uploaded_base_url": written.get("operator_uploaded_base_url") or "",
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
            "real_vault_static_upload_receipt_write_allowed": False,
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
    parser = argparse.ArgumentParser(description="Run direct Chaser Forge static-host upload receipt smoke test.")
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
