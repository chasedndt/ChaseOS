"""Live StudioAPI control proof for governed Chaser Forge marketplace/install.

This proof drives the real StudioAPI methods against temporary fixture vaults.
It writes only the requested proof report under the caller's output directory;
all Forge approval, registry, package, and extension writes happen inside
temporary fixtures that are deleted by default.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable

from runtime.studio.shell.api import StudioAPI


MODEL_VERSION = "studio.chaser_forge_live_control_proof.v2"
SURFACE_ID = "chaser_forge_live_studio_control_proof"
PASS_ID = "chaser-forge-marketplace-live-studio-control-proof"
STATUS = "COMPLETE / MARKETPLACE LIVE STUDIO CONTROL PROOF VERIFIED"
OUTPUT_DIR = Path("07_LOGS") / "Studio-Visual-QA" / "2026-05-21-chaser-forge-marketplace-live-studio-control-proof"
REPORT_NAME = "chaser-forge-live-studio-control-proof-report.json"
MARKDOWN_NAME = "chaser-forge-live-studio-control-proof-report.md"
NEXT_RECOMMENDED_PASS = "chaser-forge-marketplace-completion-audit"

FORBIDDEN_AUTHORITY_FLAGS = (
    "real_vault_forge_approval_write_allowed",
    "real_vault_registry_write_allowed",
    "real_vault_extension_file_write_allowed",
    "real_vault_exact_once_marker_write_allowed",
    "provider_or_model_call_allowed",
    "agent_bus_dispatch_allowed",
    "protected_core_mutation_allowed",
    "pulse_memory_mutation_allowed",
    "personal_map_mutation_allowed",
    "rnd_truth_state_mutation_allowed",
    "canonical_mutation_allowed",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _assert_inside(child: Path, parent: Path) -> None:
    child_resolved = child.resolve()
    parent_resolved = parent.resolve()
    try:
        child_resolved.relative_to(parent_resolved)
    except ValueError as exc:
        raise ValueError("Chaser Forge live control proof output must stay inside the vault") from exc


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _approval_statement(fixture: Path, approval_artifact_path: str) -> str:
    payload = _read_json(fixture / approval_artifact_path)
    return str(payload.get("operator_confirmation_text") or "")


def _record_approved_decision(api: StudioAPI, fixture: Path, approval_artifact_path: str, request_digest: str) -> dict:
    return api.review_chaser_forge_approval_decision(
        approval_artifact_path,
        "approved",
        request_digest,
        _approval_statement(fixture, approval_artifact_path),
        write_decision=True,
        reviewer_id="Codex live control proof",
    )


def _new_fixture(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix)).resolve()


def _cleanup_fixture(path: Path, persist_fixture: bool) -> bool:
    if persist_fixture:
        return False
    shutil.rmtree(path, ignore_errors=True)
    return not path.exists()


def _run_lifecycle_controls(fixture: Path) -> dict[str, Any]:
    api = StudioAPI(fixture)
    panel = api.get_chaser_forge_panel()
    sandbox_preview = panel["data"]["sandbox_approval"]
    sandbox_wrong = api.request_chaser_forge_sandbox_approval("wrong")
    sandbox_request = api.request_chaser_forge_sandbox_approval(sandbox_preview["request_digest_sha256"])
    sandbox_decision = _record_approved_decision(
        api,
        fixture,
        sandbox_request["data"]["approval_artifact_path"],
        sandbox_request["data"]["request_digest_sha256"],
    )
    sandbox_ready = api.execute_chaser_forge_sandbox_registry_write(
        sandbox_preview["request_digest_sha256"],
        execute=False,
    )
    sandbox_executed = api.execute_chaser_forge_sandbox_registry_write(
        sandbox_preview["request_digest_sha256"],
        execute=True,
    )

    live_panel = api.get_chaser_forge_panel()
    live_preview = live_panel["data"]["live_install_approval"]
    live_wrong = api.request_chaser_forge_live_install_approval("wrong")
    live_request = api.request_chaser_forge_live_install_approval(live_preview["request_digest_sha256"])
    live_decision = _record_approved_decision(
        api,
        fixture,
        live_request["data"]["approval_artifact_path"],
        live_request["data"]["request_digest_sha256"],
    )
    live_ready = api.execute_chaser_forge_live_install(live_preview["request_digest_sha256"], execute=False)
    live_executed = api.execute_chaser_forge_live_install(live_preview["request_digest_sha256"], execute=True)

    rollback_panel = api.get_chaser_forge_panel()
    rollback_preview = rollback_panel["data"]["rollback_approval"]
    rollback_wrong = api.request_chaser_forge_rollback_approval("wrong")
    rollback_request = api.request_chaser_forge_rollback_approval(rollback_preview["request_digest_sha256"])
    rollback_decision = _record_approved_decision(
        api,
        fixture,
        rollback_request["data"]["approval_artifact_path"],
        rollback_request["data"]["request_digest_sha256"],
    )
    rollback_ready = api.execute_chaser_forge_rollback(rollback_preview["request_digest_sha256"], execute=False)
    rollback_executed = api.execute_chaser_forge_rollback(rollback_preview["request_digest_sha256"], execute=True)

    registry_path = fixture / "runtime" / "forge" / "registry" / "extensions.json"
    registry = _read_json(registry_path) if registry_path.is_file() else {}
    registry_entry = (registry.get("entries") or [{}])[0] if isinstance(registry.get("entries"), list) else {}
    extension_dir = fixture / "extensions" / "ugc-campaign-studio"

    checks = {
        "sandbox_wrong_digest_blocked": sandbox_wrong["data"]["approval_request_written"] is False
        and "request_digest_required_or_mismatched" in sandbox_wrong["data"]["blockers"],
        "sandbox_decision_recorded": sandbox_decision["data"]["decision_artifact_written"] is True
        and sandbox_decision["data"]["approval_artifact_mutated"] is True,
        "sandbox_ready_without_write": sandbox_ready["data"]["registry_written"] is False,
        "sandbox_registry_written": sandbox_executed["data"]["registry_written"] is True,
        "sandbox_approval_consumed": sandbox_executed["data"]["approval_consumed"] is True,
        "live_wrong_digest_blocked": live_wrong["data"]["approval_request_written"] is False
        and "request_digest_required_or_mismatched" in live_wrong["data"]["blockers"],
        "live_decision_recorded": live_decision["data"]["decision_artifact_written"] is True
        and live_decision["data"]["approval_artifact_mutated"] is True,
        "live_ready_without_write": live_ready["data"]["registry_updated"] is False,
        "live_install_executed": live_executed["data"]["live_install_executed"] is True,
        "live_approval_consumed": live_executed["data"]["approval_consumed"] is True,
        "rollback_wrong_digest_blocked": rollback_wrong["data"]["approval_request_written"] is False
        and "request_digest_required_or_mismatched" in rollback_wrong["data"]["blockers"],
        "rollback_decision_recorded": rollback_decision["data"]["decision_artifact_written"] is True
        and rollback_decision["data"]["approval_artifact_mutated"] is True,
        "rollback_ready_without_write": rollback_ready["data"]["registry_updated"] is False,
        "rollback_executed": rollback_executed["data"]["rollback_executed"] is True,
        "rollback_approval_consumed": rollback_executed["data"]["approval_consumed"] is True,
        "registry_returned_to_sandbox": registry_entry.get("registry_status") == "sandbox_installed"
        and registry_entry.get("install_environment") == "sandbox",
        "extension_files_retained_after_rollback": extension_dir.is_dir(),
        "protected_core_mutation_blocked": all(
            result["data"].get("authority", {}).get("mutates_protected_core") is not True
            for result in (sandbox_executed, live_executed, rollback_executed)
        ),
    }
    return {
        "fixture_vault": str(fixture),
        "panel_status": panel["data"]["status"],
        "sandbox": {
            "request_digest_sha256": sandbox_preview["request_digest_sha256"],
            "approval_artifact_path": sandbox_request["data"]["approval_artifact_path"],
            "decision_artifact_path": sandbox_decision["data"]["decision_artifact_path"],
            "registry_written": sandbox_executed["data"]["registry_written"],
            "approval_consumed": sandbox_executed["data"]["approval_consumed"],
            "extension_files_written": sandbox_executed["data"]["extension_files_written"],
        },
        "live_install": {
            "request_digest_sha256": live_preview["request_digest_sha256"],
            "approval_artifact_path": live_request["data"]["approval_artifact_path"],
            "decision_artifact_path": live_decision["data"]["decision_artifact_path"],
            "live_install_executed": live_executed["data"]["live_install_executed"],
            "approval_consumed": live_executed["data"]["approval_consumed"],
            "extension_files_written": live_executed["data"]["extension_files_written"],
        },
        "rollback": {
            "request_digest_sha256": rollback_preview["request_digest_sha256"],
            "approval_artifact_path": rollback_request["data"]["approval_artifact_path"],
            "decision_artifact_path": rollback_decision["data"]["decision_artifact_path"],
            "rollback_executed": rollback_executed["data"]["rollback_executed"],
            "approval_consumed": rollback_executed["data"]["approval_consumed"],
            "extension_files_deleted": rollback_executed["data"]["extension_files_deleted"],
        },
        "registry": {
            "path": str(registry_path),
            "exists": registry_path.is_file(),
            "entry_status": registry_entry.get("registry_status"),
            "install_environment": registry_entry.get("install_environment"),
        },
        "checks": checks,
    }


def _run_marketplace_controls(fixture: Path) -> dict[str, Any]:
    api = StudioAPI(fixture)
    export_preview = api.get_chaser_forge_marketplace_export_package()
    package_wrong = api.write_chaser_forge_marketplace_export_package("wrong")
    package_write = api.write_chaser_forge_marketplace_export_package(export_preview["data"]["package_digest_sha256"])
    import_preview = api.get_chaser_forge_marketplace_import_preview(
        package_write["data"]["package_artifact_path"],
        package_write["data"]["package_digest_sha256"],
    )
    catalog_before = api.get_chaser_forge_marketplace_catalog()
    publish_preview = api.get_chaser_forge_marketplace_publish_preview()
    publish_wrong = api.publish_chaser_forge_marketplace_package("wrong")
    publish = api.publish_chaser_forge_marketplace_package(publish_preview["data"]["listing_digest_sha256"])
    catalog_after = api.get_chaser_forge_marketplace_catalog()
    panel = api.get_chaser_forge_panel()
    import_approval_preview = panel["data"]["marketplace"]["import_approval_request"]
    import_approval_wrong = api.request_chaser_forge_marketplace_import_sandbox_approval("wrong")
    import_approval = api.request_chaser_forge_marketplace_import_sandbox_approval(
        import_approval_preview["request_digest_sha256"],
    )
    import_decision = _record_approved_decision(
        api,
        fixture,
        import_approval["data"]["approval_artifact_path"],
        import_approval["data"]["request_digest_sha256"],
    )
    bridge_preview = api.get_chaser_forge_marketplace_import_sandbox_request(
        import_approval["data"]["approval_artifact_path"],
        import_approval["data"]["request_digest_sha256"],
    )
    bridge_wrong = api.request_chaser_forge_marketplace_import_sandbox_request(
        import_approval["data"]["approval_artifact_path"],
        import_approval["data"]["request_digest_sha256"],
        "wrong",
    )
    bridge_written = api.request_chaser_forge_marketplace_import_sandbox_request(
        import_approval["data"]["approval_artifact_path"],
        import_approval["data"]["request_digest_sha256"],
        bridge_preview["data"]["request_digest_sha256"],
    )
    sandbox_decision = _record_approved_decision(
        api,
        fixture,
        bridge_written["data"]["sandbox_approval_artifact_path"],
        bridge_written["data"]["sandbox_request_digest_sha256"],
    )
    install_ready = api.execute_chaser_forge_marketplace_install(
        import_approval["data"]["approval_artifact_path"],
        import_approval["data"]["request_digest_sha256"],
        bridge_written["data"]["sandbox_approval_artifact_path"],
        bridge_written["data"]["sandbox_request_digest_sha256"],
        publish["data"]["listing_digest_sha256"],
        publish["data"]["listing_id"],
        bridge_written["data"]["request_digest_sha256"],
        execute=False,
    )
    install_executed = api.execute_chaser_forge_marketplace_install(
        import_approval["data"]["approval_artifact_path"],
        import_approval["data"]["request_digest_sha256"],
        bridge_written["data"]["sandbox_approval_artifact_path"],
        bridge_written["data"]["sandbox_request_digest_sha256"],
        publish["data"]["listing_digest_sha256"],
        publish["data"]["listing_id"],
        bridge_written["data"]["request_digest_sha256"],
        execute=True,
    )
    duplicate_install = api.execute_chaser_forge_marketplace_install(
        import_approval["data"]["approval_artifact_path"],
        import_approval["data"]["request_digest_sha256"],
        bridge_written["data"]["sandbox_approval_artifact_path"],
        bridge_written["data"]["sandbox_request_digest_sha256"],
        publish["data"]["listing_digest_sha256"],
        publish["data"]["listing_id"],
        bridge_written["data"]["request_digest_sha256"],
        execute=True,
    )

    import_payload = _read_json(fixture / import_approval["data"]["approval_artifact_path"])
    sandbox_payload = _read_json(fixture / bridge_written["data"]["sandbox_approval_artifact_path"])
    registry_path = fixture / "runtime" / "forge" / "registry" / "extensions.json"
    extension_dir = fixture / "extensions" / "ugc-campaign-studio"
    checks = {
        "package_wrong_digest_blocked": package_wrong["data"]["package_artifact_written"] is False
        and "expected_package_digest_mismatch" in package_wrong["data"]["blockers"],
        "package_artifact_written": package_write["data"]["package_artifact_written"] is True,
        "import_preview_ok": import_preview["data"]["ok"] is True,
        "import_preview_no_install": import_preview["data"]["import_install_allowed"] is False,
        "catalog_initially_readable": catalog_before["data"]["ok"] is True,
        "publish_preview_ok": publish_preview["data"]["ok"] is True,
        "publish_wrong_digest_blocked": publish_wrong["data"]["catalog_listing_written"] is False
        and "expected_listing_digest_required_or_mismatched" in publish_wrong["data"]["blockers"],
        "catalog_listing_written": publish["data"]["catalog_listing_written"] is True,
        "catalog_entry_readable": catalog_after["data"]["entry_count"] == 1,
        "import_approval_wrong_digest_blocked": import_approval_wrong["data"]["approval_request_written"] is False
        and "request_digest_required_or_mismatched" in import_approval_wrong["data"]["blockers"],
        "import_approval_written": import_approval["data"]["approval_request_written"] is True,
        "import_decision_recorded": import_decision["data"]["decision_artifact_written"] is True
        and import_decision["data"]["approval_artifact_mutated"] is True,
        "bridge_preview_ok": bridge_preview["data"]["ok"] is True,
        "bridge_wrong_digest_blocked": bridge_wrong["data"]["sandbox_approval_request_written"] is False
        and "request_digest_required_or_mismatched" in bridge_wrong["data"]["blockers"],
        "sandbox_request_written": bridge_written["data"]["sandbox_approval_request_written"] is True,
        "sandbox_decision_recorded": sandbox_decision["data"]["decision_artifact_written"] is True
        and sandbox_decision["data"]["approval_artifact_mutated"] is True,
        "marketplace_install_ready_without_write": install_ready["data"]["ok"] is True
        and install_ready["data"]["registry_written"] is False,
        "marketplace_install_executed": install_executed["data"]["marketplace_install_executed"] is True,
        "marketplace_import_approval_consumed_by_install": import_payload.get("approval_consumed") is True,
        "sandbox_approval_consumed_by_install": sandbox_payload.get("approval_consumed") is True,
        "registry_written_by_marketplace_install": registry_path.is_file() and install_executed["data"]["registry_written"] is True,
        "extension_files_written_by_marketplace_install": extension_dir.is_dir()
        and bool(install_executed["data"]["extension_files_written"]),
        "exact_once_marker_reserved_by_marketplace_install": install_executed["data"]["exact_once_marker_reserved"] is True,
        "duplicate_marketplace_install_blocked": duplicate_install["data"]["ok"] is False
        and "marketplace_import_approval_already_consumed" in duplicate_install["data"]["blockers"],
    }
    return {
        "fixture_vault": str(fixture),
        "export_package": {
            "package_digest_sha256": export_preview["data"]["package_digest_sha256"],
            "package_artifact_path": package_write["data"]["package_artifact_path"],
            "package_artifact_written": package_write["data"]["package_artifact_written"],
        },
        "import_preview": {
            "ok": import_preview["data"]["ok"],
            "package_digest_sha256": import_preview["data"]["package_digest_sha256"],
            "registry_written": import_preview["data"]["registry_written"],
            "extension_files_written": import_preview["data"]["extension_files_written"],
            "import_install_allowed": import_preview["data"]["import_install_allowed"],
        },
        "marketplace_publish": {
            "catalog_initial_entry_count": catalog_before["data"]["entry_count"],
            "listing_digest_sha256": publish["data"]["listing_digest_sha256"],
            "listing_id": publish["data"]["listing_id"],
            "catalog_listing_written": publish["data"]["catalog_listing_written"],
            "catalog_entry_count": catalog_after["data"]["entry_count"],
        },
        "import_approval": {
            "approval_artifact_path": import_approval["data"]["approval_artifact_path"],
            "approval_request_written": import_approval["data"]["approval_request_written"],
            "approval_consumed": import_payload.get("approval_consumed"),
            "decision_artifact_path": import_decision["data"]["decision_artifact_path"],
        },
        "sandbox_request_bridge": {
            "sandbox_approval_artifact_path": bridge_written["data"]["sandbox_approval_artifact_path"],
            "sandbox_approval_request_written": bridge_written["data"]["sandbox_approval_request_written"],
            "sandbox_approval_consumed": sandbox_payload.get("approval_consumed"),
            "marketplace_import_approval_consumed": bridge_written["data"]["marketplace_import_approval_consumed"],
            "registry_written": bridge_written["data"]["registry_written"],
            "extension_files_written": bridge_written["data"]["extension_files_written"],
            "exact_once_marker_reserved": bridge_written["data"]["exact_once_marker_reserved"],
        },
        "marketplace_install": {
            "ready_ok": install_ready["data"]["ok"],
            "ready_registry_written": install_ready["data"]["registry_written"],
            "marketplace_install_executed": install_executed["data"]["marketplace_install_executed"],
            "marketplace_import_approval_consumed": install_executed["data"]["marketplace_import_approval_consumed"],
            "sandbox_approval_consumed": install_executed["data"]["sandbox_approval_consumed"],
            "registry_written": install_executed["data"]["registry_written"],
            "registry_path": install_executed["data"]["registry_path"],
            "extension_files_written": install_executed["data"]["extension_files_written"],
            "exact_once_marker_reserved": install_executed["data"]["exact_once_marker_reserved"],
            "duplicate_blockers": duplicate_install["data"]["blockers"],
        },
        "checks": checks,
    }


def _authority(write_report: bool, report_written: bool) -> dict[str, Any]:
    authority = {flag: False for flag in FORBIDDEN_AUTHORITY_FLAGS}
    authority.update(
        {
            "proof_report_write_requested": bool(write_report),
            "proof_report_written": bool(report_written),
            "fixture_vault_writes_allowed": True,
            "fixture_vault_removed_by_default": True,
            "log_only": True,
        }
    )
    return authority


def _collect_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    lifecycle_checks = (report.get("lifecycle_controls") or {}).get("checks") or {}
    marketplace_checks = (report.get("marketplace_controls") or {}).get("checks") or {}
    blockers.extend(f"lifecycle_check_failed:{key}" for key, value in lifecycle_checks.items() if value is not True)
    blockers.extend(f"marketplace_check_failed:{key}" for key, value in marketplace_checks.items() if value is not True)
    authority = report.get("authority") or {}
    blockers.extend(f"forbidden_authority_flag_true:{flag}" for flag in FORBIDDEN_AUTHORITY_FLAGS if authority.get(flag) is not False)
    return list(dict.fromkeys(blockers))


def render_chaser_forge_live_studio_control_proof(report: dict[str, Any]) -> str:
    lifecycle = report.get("lifecycle_controls") or {}
    marketplace = report.get("marketplace_controls") or {}
    return "\n".join(
        [
            "# Chaser Forge Live Studio Control Proof",
            "",
            f"- Date: {report.get('date')}",
            f"- Runtime: {report.get('runtime')}",
            f"- Session descriptor: `{report.get('session_descriptor')}`",
            f"- Status: {report.get('status')}",
            f"- OK: {str(bool(report.get('ok'))).lower()}",
            "",
            "## Lifecycle Controls",
            "",
            f"- Sandbox registry written: {str((lifecycle.get('sandbox') or {}).get('registry_written')).lower()}",
            f"- Live install executed: {str((lifecycle.get('live_install') or {}).get('live_install_executed')).lower()}",
            f"- Rollback executed: {str((lifecycle.get('rollback') or {}).get('rollback_executed')).lower()}",
            f"- Registry final state: {(lifecycle.get('registry') or {}).get('entry_status')} / {(lifecycle.get('registry') or {}).get('install_environment')}",
            "",
            "## Marketplace Controls",
            "",
            f"- Package artifact written in fixture: {str((marketplace.get('export_package') or {}).get('package_artifact_written')).lower()}",
            f"- Catalog listing written in fixture: {str((marketplace.get('marketplace_publish') or {}).get('catalog_listing_written')).lower()}",
            f"- Import approval written in fixture: {str((marketplace.get('import_approval') or {}).get('approval_request_written')).lower()}",
            f"- Sandbox request written in fixture: {str((marketplace.get('sandbox_request_bridge') or {}).get('sandbox_approval_request_written')).lower()}",
            f"- Marketplace install executed: {str((marketplace.get('marketplace_install') or {}).get('marketplace_install_executed')).lower()}",
            f"- Marketplace import approval consumed: {str((marketplace.get('marketplace_install') or {}).get('marketplace_import_approval_consumed')).lower()}",
            f"- Registry written by marketplace install: {str((marketplace.get('marketplace_install') or {}).get('registry_written')).lower()}",
            f"- Exact-once marker reserved by marketplace install: {str((marketplace.get('marketplace_install') or {}).get('exact_once_marker_reserved')).lower()}",
            "",
            "## Blockers",
            "",
            "\n".join(f"- {blocker}" for blocker in report.get("blockers") or []) or "- None",
            "",
            "## Boundary",
            "",
            "StudioAPI controls were exercised against temporary fixture vaults only. The report adds no real-vault Forge approval, registry, extension-file, exact-once marker, provider/model, Agent Bus, protected-core, memory, R&D, or canonical authority.",
            "",
        ]
    )


def build_chaser_forge_live_studio_control_proof(
    vault_root: str | Path,
    *,
    output_dir: str | Path = OUTPUT_DIR,
    generated_at: str | None = None,
    write: bool = True,
    persist_fixture: bool = False,
    fixture_factory: Callable[[str], Path] = _new_fixture,
) -> dict[str, Any]:
    """Run live StudioAPI Forge controls in temp fixtures and optionally write a report."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    resolved_output_dir = (vault / output_dir).resolve() if not Path(output_dir).is_absolute() else Path(output_dir).resolve()
    _assert_inside(resolved_output_dir, vault)

    if fixture_factory is _new_fixture:
        scratch_root = Path("C:/tmp")
        fixture_root = scratch_root / "chaser-forge-live-studio-control-proof-fixtures" if scratch_root.is_dir() else resolved_output_dir / "_fixtures"
        fixture_root.mkdir(parents=True, exist_ok=True)
        lifecycle_fixture = Path(tempfile.mkdtemp(prefix="chaser-forge-lifecycle-", dir=str(fixture_root))).resolve()
        marketplace_fixture = Path(tempfile.mkdtemp(prefix="chaser-forge-marketplace-", dir=str(fixture_root))).resolve()
    else:
        lifecycle_fixture = fixture_factory("chaser-forge-lifecycle-")
        marketplace_fixture = fixture_factory("chaser-forge-marketplace-")
    lifecycle_cleanup_completed = False
    marketplace_cleanup_completed = False
    try:
        lifecycle_controls = _run_lifecycle_controls(lifecycle_fixture)
        marketplace_controls = _run_marketplace_controls(marketplace_fixture)
    finally:
        lifecycle_cleanup_completed = _cleanup_fixture(lifecycle_fixture, persist_fixture)
        marketplace_cleanup_completed = _cleanup_fixture(marketplace_fixture, persist_fixture)

    report_path = resolved_output_dir / REPORT_NAME
    markdown_path = resolved_output_dir / MARKDOWN_NAME
    report: dict[str, Any] = {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass_id": PASS_ID,
        "status": STATUS,
        "date": timestamp[:10],
        "generated_at": timestamp,
        "runtime": "Codex",
        "session_descriptor": "chaser-forge-no-deferrals-studio-marketplace",
        "vault_root": str(vault),
        "report_path": _relative_to_vault(vault, report_path),
        "markdown_report_path": _relative_to_vault(vault, markdown_path),
        "write_requested": bool(write),
        "write_executed": False,
        "fixture_policy": {
            "persist_fixture": persist_fixture,
            "lifecycle_fixture": str(lifecycle_fixture),
            "marketplace_fixture": str(marketplace_fixture),
            "lifecycle_cleanup_completed": lifecycle_cleanup_completed,
            "marketplace_cleanup_completed": marketplace_cleanup_completed,
        },
        "lifecycle_controls": lifecycle_controls,
        "marketplace_controls": marketplace_controls,
        "authority": _authority(write_report=write, report_written=False),
        "blockers": [],
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
    report["blockers"] = _collect_blockers(report)
    report["ok"] = not report["blockers"]
    report["status"] = STATUS if report["ok"] else "PARTIAL / LIVE STUDIO CONTROL PROOF BLOCKED"

    if write:
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
        report["write_executed"] = True
        report["authority"] = _authority(write_report=True, report_written=True)
        report["blockers"] = _collect_blockers(report)
        report["ok"] = not report["blockers"]
        report["status"] = STATUS if report["ok"] else "PARTIAL / LIVE STUDIO CONTROL PROOF BLOCKED"
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        markdown_path.write_text(render_chaser_forge_live_studio_control_proof(report), encoding="utf-8")

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Chaser Forge live StudioAPI control proof.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Report output directory inside the vault.")
    parser.add_argument("--generated-at", default=None, help="Override generated_at timestamp.")
    parser.add_argument("--no-write", action="store_true", help="Do not write report artifacts.")
    parser.add_argument("--persist-fixture", action="store_true", help="Keep temporary fixture vaults for inspection.")
    parser.add_argument("--json", action="store_true", help="Print the report JSON envelope.")
    args = parser.parse_args(argv)

    report = build_chaser_forge_live_studio_control_proof(
        args.vault_root,
        output_dir=args.output_dir,
        generated_at=args.generated_at,
        write=not args.no_write,
        persist_fixture=args.persist_fixture,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(render_chaser_forge_live_studio_control_proof(report))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
