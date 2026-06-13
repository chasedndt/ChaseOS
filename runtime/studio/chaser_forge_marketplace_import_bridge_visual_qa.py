"""Static Studio visual proof for the Chaser Forge marketplace import bridge.

The harness renders the production Studio Chaser Forge panel against a temporary
approved marketplace-import fixture. It writes visual QA evidence only; it does
not approve, consume, install, mutate the real Forge registry, write real
extension files, or persist fixture approval artifacts in the real vault.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import shutil
from typing import Any, Callable

from runtime.forge.approval_decision import build_forge_approval_decision_handoff
from runtime.forge.marketplace import (
    build_forge_marketplace_export_package,
    build_forge_marketplace_import_sandbox_approval,
    build_forge_marketplace_import_sandbox_request,
)
from runtime.forge.panel import build_chaser_forge_panel, load_demo_manifest


MODEL_VERSION = "studio.chaser_forge_marketplace_import_bridge_visual_qa.v2"
SURFACE_ID = "chaser_forge_marketplace_import_bridge_visual_qa"
PASS_ID = "chaser-forge-marketplace-publish-install-visual-qa"
STATUS = "COMPLETE / MARKETPLACE PUBLISH AND INSTALL STUDIO UI VISUAL QA VERIFIED"
DEFAULT_OUTPUT_DIR = (
    Path("07_LOGS")
    / "Studio-Visual-QA"
    / "2026-05-21-chaser-forge-marketplace-publish-install-visual-qa"
)
# Intentionally terse: nested pytest roots can hit Windows MAX_PATH when the
# Forge approval artifact directories and packet ids are appended.
FIXTURE_RELATIVE_DIR = Path("_cfvqa")
NEXT_RECOMMENDED_PASS = "remote-distribution-only-if-authorized-or-select-next-chaseos-feature-family"

REQUIRED_TOKENS = (
    "Marketplace Publish And Install",
    "Import sandbox request bridge",
    "Sandbox request preview API",
    "get_chaser_forge_marketplace_import_sandbox_request",
    "Sandbox request API",
    "request_chaser_forge_marketplace_import_sandbox_request",
    "Sandbox request bridge",
    "forge_marketplace_import_sandbox_request_written",
    "Sandbox request written",
    "Yes",
    "Publish allowed",
    "Auto install",
    "Yes",
    "Publish Demo Package",
    "Run Demo Marketplace Install",
    "execute_chaser_forge_marketplace_install",
    "07_LOGS/Agent-Activity/_forge_sandbox_approvals/",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_output_dir(vault: Path, output_dir: str | Path | None) -> Path:
    raw = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    resolved = raw if raw.is_absolute() else vault / raw
    resolved = resolved.resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError("Chaser Forge marketplace bridge visual QA output must stay inside the vault") from exc
    return resolved


def _relative_to_vault(vault: Path, path: str | Path | None) -> str | None:
    if path is None:
        return None
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = vault / resolved
    try:
        return resolved.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "visual_evidence_allowed": True,
        "temporary_fixture_approval_artifacts_created": True,
        "fixture_vault_persisted": False,
        "real_vault_approval_artifact_write_allowed": False,
        "real_vault_approval_decision_allowed": False,
        "real_vault_sandbox_approval_request_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "forge_sandbox_install_allowed": False,
        "forge_registry_mutation_allowed": False,
        "extension_file_write_allowed": False,
        "extension_file_delete_allowed": False,
        "protected_core_mutation_allowed": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
        "schedule_activation_allowed": False,
        "agent_bus_task_write_allowed": False,
        "secret_or_credential_read_allowed": False,
        "pulse_memory_mutation_allowed": False,
        "personal_map_mutation_allowed": False,
        "rnd_truth_state_mutation_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _build_bridge_fixture_panel(fixture_vault: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = load_demo_manifest()
    generated_at = "2026-05-21T00:00:00Z"
    package_preview = build_forge_marketplace_export_package(
        fixture_vault,
        manifest=manifest,
        generated_at=generated_at,
    )
    approval_preview = build_forge_marketplace_import_sandbox_approval(
        fixture_vault,
        package_payload=package_preview["package_payload"],
        generated_at=generated_at,
    )
    approval_written = build_forge_marketplace_import_sandbox_approval(
        fixture_vault,
        package_payload=package_preview["package_payload"],
        write_approval_request=True,
        request_digest=approval_preview["request_digest_sha256"],
        generated_at=generated_at,
    )
    if not approval_written.get("ok"):
        raise RuntimeError(f"marketplace import approval fixture blocked: {approval_written.get('blockers')}")
    approval_path = fixture_vault / str(approval_written["approval_artifact_path"])
    source_payload = _read_json(approval_path)
    decision = build_forge_approval_decision_handoff(
        fixture_vault,
        approval_artifact_path=approval_written["approval_artifact_path"],
        decision="approved",
        expected_request_digest=str(approval_written["request_digest_sha256"]),
        operator_statement=str(source_payload["operator_confirmation_text"]),
        write_decision=True,
        reviewer_id="visual-qa",
        generated_at=generated_at,
    )
    if not decision.get("ok"):
        raise RuntimeError(f"marketplace import decision fixture blocked: {decision.get('blockers')}")
    bridge_preview = build_forge_marketplace_import_sandbox_request(
        fixture_vault,
        import_approval_artifact_path=approval_written["approval_artifact_path"],
        expected_import_request_digest=str(approval_written["request_digest_sha256"]),
        generated_at=generated_at,
    )
    if not bridge_preview.get("ok"):
        raise RuntimeError(f"marketplace bridge preview fixture blocked: {bridge_preview.get('blockers')}")
    bridge_written = build_forge_marketplace_import_sandbox_request(
        fixture_vault,
        import_approval_artifact_path=approval_written["approval_artifact_path"],
        expected_import_request_digest=str(approval_written["request_digest_sha256"]),
        write_sandbox_request=True,
        request_digest=str(bridge_preview["request_digest_sha256"]),
        generated_at=generated_at,
    )
    if not bridge_written.get("ok"):
        raise RuntimeError(f"marketplace bridge write fixture blocked: {bridge_written.get('blockers')}")
    approved_source_payload = _read_json(approval_path)
    sandbox_path = fixture_vault / str(bridge_written["sandbox_approval_artifact_path"])
    sandbox_payload = _read_json(sandbox_path)

    panel = build_chaser_forge_panel(fixture_vault)
    panel["summary"]["marketplace_import_approval_preview_ready"] = True
    panel["summary"]["marketplace_import_approval_request_written"] = True
    panel["summary"]["marketplace_import_sandbox_request_preview_ready"] = bool(bridge_written.get("ok"))
    panel["summary"]["marketplace_import_sandbox_request_written"] = bool(
        bridge_written.get("sandbox_approval_request_written")
    )
    panel["summary"]["marketplace_import_approval_consumed_by_bridge"] = bool(
        bridge_written.get("marketplace_import_approval_consumed")
    )
    panel["marketplace"]["import_approval_request"] = {
        **approval_written,
        "status": approved_source_payload.get("status"),
        "operator_decision": approved_source_payload.get("operator_decision"),
        "approval_consumed": approved_source_payload.get("approval_consumed"),
        "decision_artifact_path": approved_source_payload.get("decision_artifact_path"),
        "approval_decision_recorded": approved_source_payload.get("approval_decision_recorded"),
    }
    panel["marketplace"]["import_sandbox_request"] = bridge_written

    evidence = {
        "package_preview_ok": package_preview.get("ok"),
        "marketplace_import_approval_written": approval_written.get("approval_request_written"),
        "marketplace_import_approval_path": approval_written.get("approval_artifact_path"),
        "marketplace_import_approval_status": approved_source_payload.get("status"),
        "marketplace_import_approval_consumed": approved_source_payload.get("approval_consumed"),
        "decision_recorded": decision.get("ok"),
        "decision_artifact_path": approved_source_payload.get("decision_artifact_path"),
        "bridge_preview_ok": bridge_preview.get("ok"),
        "bridge_written_ok": bridge_written.get("ok"),
        "bridge_request_digest_sha256": bridge_written.get("request_digest_sha256"),
        "sandbox_approval_request_written": bridge_written.get("sandbox_approval_request_written"),
        "sandbox_approval_artifact_path": bridge_written.get("sandbox_approval_artifact_path"),
        "sandbox_approval_status": sandbox_payload.get("status"),
        "sandbox_approval_consumed": sandbox_payload.get("approval_consumed"),
        "registry_written": bridge_written.get("registry_written"),
        "extension_files_written": bridge_written.get("extension_files_written"),
        "exact_once_marker_reserved": bridge_written.get("exact_once_marker_reserved"),
    }
    return panel, evidence


def _pywebview_stub(panel_data: dict[str, Any]) -> str:
    payload = json.dumps(panel_data, sort_keys=True, default=str)
    return f"""
(() => {{
  const chaserForgePanel = {payload};
  const api = {{
    get_chaser_forge_panel: async () => ({{ ok: true, data: chaserForgePanel }}),
    get_panel_registry: async () => ({{ ok: true, data: {{ panels: [], readiness: {{}}, authority: {{ read_only_registry: true }} }} }}),
    get_graph_style_registry: async () => ({{ ok: true, data: {{ styles: [] }} }}),
    get_graph_settings: async () => ({{ ok: true, data: {{}} }}),
    list_graph_presets: async () => ({{ ok: true, data: {{ presets: [] }} }}),
    get_runtime_status: async () => ({{ ok: true, data: {{ status: "visual-qa-stub" }} }}),
    get_dashboard: async () => ({{ ok: true, data: {{ cards: [], summary: {{}} }} }}),
  }};
  window.pywebview = {{
    api: new Proxy(api, {{
      get(target, prop) {{
        return target[prop] || (async () => ({{ ok: true, data: {{}}, warnings: [] }}));
      }}
    }})
  }};
}})();
"""


def _run_playwright_visual_qa(vault: Path, output_dir: Path, panel_data: dict[str, Any]) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = _repo_root() / "runtime" / "studio" / "shell" / "frontend" / "index.html"
    url = f"{index_path.resolve().as_uri()}#/chaser-forge"
    screenshots: list[dict[str, Any]] = []
    console_messages: list[str] = []
    page_errors: list[str] = []
    stub = _pywebview_stub(panel_data)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            for viewport_name, viewport in (
                ("desktop", {"width": 1440, "height": 1000}),
                ("mobile", {"width": 390, "height": 900}),
            ):
                page = browser.new_page(viewport=viewport)
                page.on("console", lambda msg: console_messages.append(f"{msg.type}:{msg.text}"))
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                page.add_init_script(stub)
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_selector('[data-marketplace-surface="chaser-forge-marketplace-import-export"]', timeout=7000)
                text = page.locator("#panel-chaser-forge").inner_text(timeout=5000)
                normalized_text = text.lower()
                screenshot_path = output_dir / f"{viewport_name}-chaser-forge-marketplace-bridge.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                missing = [token for token in REQUIRED_TOKENS if token.lower() not in normalized_text]
                screenshots.append(
                    {
                        "viewport": viewport_name,
                        "path": _relative_to_vault(vault, screenshot_path),
                        "exists": screenshot_path.is_file(),
                        "bytes": screenshot_path.stat().st_size if screenshot_path.is_file() else 0,
                        "not_blank": screenshot_path.is_file() and screenshot_path.stat().st_size > 10_000,
                        "marketplace_section_visible": "marketplace publish and install" in normalized_text,
                        "bridge_api_tokens_visible": (
                            "get_chaser_forge_marketplace_import_sandbox_request" in normalized_text
                            and "request_chaser_forge_marketplace_import_sandbox_request" in normalized_text
                        ),
                        "bridge_written_state_visible": (
                            "forge_marketplace_import_sandbox_request_written" in normalized_text
                            and "sandbox request written" in normalized_text
                        ),
                        "framework_overlay_detected": any(
                            token.lower() in normalized_text
                            for token in ("ReferenceError", "Traceback", "webpack", "Vite Error", "Next.js")
                        ),
                        "missing_required_tokens": missing,
                    }
                )
                page.close()
        finally:
            browser.close()

    severe_console = [
        item for item in console_messages if item.startswith(("error:", "warning:")) and "favicon" not in item.lower()
    ]
    return {
        "url": url,
        "screenshots": screenshots,
        "console_errors_or_warnings": severe_console,
        "page_errors": page_errors,
    }


def _format_markdown(report: dict[str, Any]) -> str:
    evidence = report.get("fixture_evidence") or {}
    screenshot_lines = "\n".join(
        f"- {shot['viewport']}: `{shot['path']}` bytes={shot['bytes']} marketplace_section_visible={shot['marketplace_section_visible']} bridge_written_state_visible={shot['bridge_written_state_visible']}"
        for shot in report.get("screenshots", [])
    )
    blocker_lines = "\n".join(f"- {escape(str(blocker))}" for blocker in report.get("blockers", [])) or "- none"
    return "\n".join(
        [
            "# Chaser Forge Marketplace Import Sandbox Request Bridge Visual QA",
            "",
            f"- Status: {report.get('status')}",
            f"- OK: {report.get('ok')}",
            f"- Surface: {report.get('surface')}",
            f"- Browser path: {report.get('browser_availability', {}).get('browser_path')}",
            f"- Browser fallback reason: {report.get('browser_availability', {}).get('fallback_reason')}",
            f"- Bridge written: {evidence.get('sandbox_approval_request_written')}",
            f"- Marketplace approval consumed: {evidence.get('marketplace_import_approval_consumed')}",
            f"- Sandbox approval consumed: {evidence.get('sandbox_approval_consumed')}",
            f"- Registry written: {evidence.get('registry_written')}",
            f"- Exact-once marker reserved: {evidence.get('exact_once_marker_reserved')}",
            f"- Sandbox approval artifact: `{evidence.get('sandbox_approval_artifact_path')}`",
            "",
            "## Screenshots",
            "",
            screenshot_lines,
            "",
            "## Blockers",
            "",
            blocker_lines,
            "",
        ]
    )


def build_chaser_forge_marketplace_import_bridge_visual_qa(
    vault_root: str | Path,
    *,
    output_dir: str | Path | None = None,
    screenshot_runner: Callable[[Path, Path, dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    resolved_output_dir = _resolve_output_dir(vault, output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    # Keep the temporary approval fixture near the vault root so Windows MAX_PATH
    # limits do not interfere with the intentionally long Forge artifact names.
    fixture_vault = (vault / FIXTURE_RELATIVE_DIR).resolve()
    try:
        fixture_vault.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError("Chaser Forge marketplace bridge fixture must stay inside the vault") from exc
    if fixture_vault.exists():
        shutil.rmtree(fixture_vault)
    fixture_vault.mkdir(parents=True)

    panel: dict[str, Any] = {}
    fixture_evidence: dict[str, Any] = {}
    fixture_errors: list[str] = []
    try:
        panel, fixture_evidence = _build_bridge_fixture_panel(fixture_vault)
    except Exception as exc:  # noqa: BLE001
        fixture_errors.append(str(exc))
    finally:
        shutil.rmtree(fixture_vault, ignore_errors=True)

    runner = screenshot_runner or _run_playwright_visual_qa
    visual = runner(vault, resolved_output_dir, panel) if panel else {"screenshots": []}
    screenshots = visual.get("screenshots") if isinstance(visual.get("screenshots"), list) else []
    missing_tokens = sorted(
        {
            token
            for screenshot in screenshots
            for token in (screenshot.get("missing_required_tokens") or [])
        }
    )

    blockers: list[str] = []
    if fixture_errors:
        blockers.extend(f"fixture_error:{item}" for item in fixture_errors)
    if not fixture_evidence.get("bridge_written_ok"):
        blockers.append("bridge_write_not_ready")
    if fixture_evidence.get("marketplace_import_approval_consumed") is not False:
        blockers.append("marketplace_import_approval_consumed_unexpected")
    if fixture_evidence.get("sandbox_approval_consumed") is not False:
        blockers.append("sandbox_approval_consumed_unexpected")
    if fixture_evidence.get("registry_written") is not False:
        blockers.append("registry_written_unexpected")
    if fixture_evidence.get("extension_files_written") != []:
        blockers.append("extension_files_written_unexpected")
    if fixture_evidence.get("exact_once_marker_reserved") is not False:
        blockers.append("exact_once_marker_reserved_unexpected")
    if missing_tokens:
        blockers.extend(f"missing_required_token:{token}" for token in missing_tokens)
    if not screenshots:
        blockers.append("no_screenshots_captured")
    if any(not shot.get("marketplace_section_visible") for shot in screenshots):
        blockers.append("marketplace_section_not_visible")
    if any(not shot.get("bridge_api_tokens_visible") for shot in screenshots):
        blockers.append("bridge_api_tokens_not_visible")
    if any(not shot.get("bridge_written_state_visible") for shot in screenshots):
        blockers.append("bridge_written_state_not_visible")
    if any(not shot.get("not_blank") for shot in screenshots):
        blockers.append("blank_or_tiny_screenshot")
    if any(shot.get("framework_overlay_detected") for shot in screenshots):
        blockers.append("framework_overlay_detected")
    if visual.get("console_errors_or_warnings"):
        blockers.append("console_errors_or_warnings_present")
    if visual.get("page_errors"):
        blockers.append("page_errors_present")

    report = {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "schema_version": MODEL_VERSION,
        "pass_id": PASS_ID,
        "status": STATUS if not blockers else "BLOCKED / MARKETPLACE IMPORT SANDBOX REQUEST BRIDGE VISUAL QA FAILED",
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "output_dir": _relative_to_vault(vault, resolved_output_dir),
        "flow_under_test": (
            "Studio Chaser Forge panel -> Marketplace Publish And Install section -> approved marketplace-import "
            "review bridge renders pending sandbox approval request handoff"
        ),
        "browser_availability": {
            "browser_plugin_available": "not_checked_by_standalone_cli",
            "browser_path": "playwright_sync_local_static_render",
            "fallback_used": False,
            "fallback_reason": (
                "Standalone visual QA uses a vault-local Playwright static render path; MCP browser tools "
                "are chat-session tools, not runtime dependencies for this CLI harness."
            ),
        },
        "summary": {
            "marketplace_section_visible": bool(screenshots)
            and all(shot.get("marketplace_section_visible") for shot in screenshots),
            "bridge_api_tokens_visible": bool(screenshots)
            and all(shot.get("bridge_api_tokens_visible") for shot in screenshots),
            "bridge_written_state_visible": bool(screenshots)
            and all(shot.get("bridge_written_state_visible") for shot in screenshots),
            "desktop_and_mobile_checked": {shot.get("viewport") for shot in screenshots} == {"desktop", "mobile"},
            "screenshot_captured": bool(screenshots),
            "fixture_vault_persisted": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "fixture_evidence": fixture_evidence,
        "screenshots": screenshots,
        "console_errors_or_warnings": visual.get("console_errors_or_warnings") or [],
        "page_errors": visual.get("page_errors") or [],
        "required_tokens": list(REQUIRED_TOKENS),
        "missing_required_tokens": missing_tokens,
        "authority": _authority(),
        "blockers": list(dict.fromkeys(blockers)),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }

    json_path = resolved_output_dir / "chaser-forge-marketplace-import-bridge-visual-qa-report.json"
    md_path = resolved_output_dir / "chaser-forge-marketplace-import-bridge-visual-qa-report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    md_path.write_text(_format_markdown(report), encoding="utf-8")
    report["report_path"] = _relative_to_vault(vault, json_path)
    report["markdown_report_path"] = _relative_to_vault(vault, md_path)
    return report


def format_chaser_forge_marketplace_import_bridge_visual_qa(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    evidence = payload.get("fixture_evidence") or {}
    return "\n".join(
        [
            "Chaser Forge Marketplace Import Sandbox Request Bridge Visual QA",
            f"  status: {payload.get('status')}",
            f"  ok: {payload.get('ok')}",
            f"  marketplace_section_visible: {summary.get('marketplace_section_visible')}",
            f"  bridge_api_tokens_visible: {summary.get('bridge_api_tokens_visible')}",
            f"  bridge_written_state_visible: {summary.get('bridge_written_state_visible')}",
            f"  desktop_and_mobile_checked: {summary.get('desktop_and_mobile_checked')}",
            f"  sandbox_approval_request_written: {evidence.get('sandbox_approval_request_written')}",
            f"  marketplace_import_approval_consumed: {evidence.get('marketplace_import_approval_consumed')}",
            f"  sandbox_approval_consumed: {evidence.get('sandbox_approval_consumed')}",
            f"  registry_written: {evidence.get('registry_written')}",
            f"  exact_once_marker_reserved: {evidence.get('exact_once_marker_reserved')}",
            f"  report_path: {payload.get('report_path')}",
            f"  next: {summary.get('next_recommended_pass')}",
            "  Boundary: visual proof only; fixture approvals are temporary and no real-vault install, approval consumption, registry mutation, extension-file write, provider/model call, Agent Bus write, or canonical mutation is performed.",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Chaser Forge marketplace bridge Studio visual QA.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory inside the vault.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args(argv)
    report = build_chaser_forge_marketplace_import_bridge_visual_qa(
        args.vault_root,
        output_dir=args.output_dir,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(format_chaser_forge_marketplace_import_bridge_visual_qa(report))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
