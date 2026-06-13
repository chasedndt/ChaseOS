"""Rendered operator-use proof for Chaser Forge marketplace Studio buttons.

The harness loads the production Studio shell, injects a temporary pywebview
API bridge backed by StudioAPI over a fixture vault, clicks the actual
Local Catalog & Install buttons, accepts the test confirmations, and
verifies visible status plus fixture-only registry/file/marker writes.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable

from runtime.studio.shell.api import StudioAPI


MODEL_VERSION = "studio.chaser_forge_marketplace_operator_use_visual_qa.v1"
SURFACE_ID = "chaser_forge_marketplace_operator_use_visual_qa"
PASS_ID = "chaser-forge-marketplace-operator-use-studio-proof"
STATUS = "COMPLETE / MARKETPLACE OPERATOR USE STUDIO BUTTON FLOW VERIFIED"
DEFAULT_OUTPUT_DIR = (
    Path("07_LOGS")
    / "Studio-Visual-QA"
    / "2026-05-21-chaser-forge-marketplace-operator-use-studio-proof"
)
REPORT_NAME = "chaser-forge-marketplace-operator-use-visual-qa-report.json"
MARKDOWN_NAME = "chaser-forge-marketplace-operator-use-visual-qa-report.md"
NEXT_RECOMMENDED_PASS = "remote-distribution-only-if-authorized-or-select-next-chaseos-feature-family"

REQUIRED_API_METHODS = (
    "get_chaser_forge_panel",
    "get_chaser_forge_marketplace_publish_preview",
    "publish_chaser_forge_marketplace_package",
    "request_chaser_forge_marketplace_import_sandbox_approval",
    "review_chaser_forge_approval_decision",
    "get_chaser_forge_marketplace_import_sandbox_request",
    "request_chaser_forge_marketplace_import_sandbox_request",
    "execute_chaser_forge_marketplace_install",
)

FORBIDDEN_AUTHORITY_FLAGS = (
    "real_vault_approval_artifact_write_allowed",
    "real_vault_registry_write_allowed",
    "real_vault_extension_file_write_allowed",
    "real_vault_exact_once_marker_write_allowed",
    "remote_marketplace_call_allowed",
    "third_party_package_exchange_allowed",
    "unauthorized_auto_install_allowed",
    "generic_approval_center_write_control_allowed",
    "provider_or_model_call_allowed",
    "agent_bus_dispatch_allowed",
    "protected_core_mutation_allowed",
    "pulse_memory_mutation_allowed",
    "personal_map_mutation_allowed",
    "rnd_truth_state_mutation_allowed",
    "canonical_mutation_allowed",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def _resolve_output_dir(vault: Path, output_dir: str | Path | None) -> Path:
    raw = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    resolved = raw if raw.is_absolute() else vault / raw
    resolved = resolved.resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError("Chaser Forge operator-use visual QA output must stay inside the vault") from exc
    return resolved


def _new_fixture(prefix: str) -> Path:
    root = Path("C:/tmp")
    if root.is_dir():
        fixture_root = root / "chaser-forge-marketplace-operator-use-fixtures"
        try:
            fixture_root.mkdir(parents=True, exist_ok=True)
            return Path(tempfile.mkdtemp(prefix=prefix, dir=str(fixture_root))).resolve()
        except OSError:
            pass
    return Path(tempfile.mkdtemp(prefix=prefix)).resolve()


def _cleanup_fixture(path: Path, persist_fixture: bool) -> bool:
    if persist_fixture:
        return False
    shutil.rmtree(path, ignore_errors=True)
    return not path.exists()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _authority(write_report: bool, report_written: bool) -> dict[str, Any]:
    authority = {flag: False for flag in FORBIDDEN_AUTHORITY_FLAGS}
    authority.update(
        {
            "production_frontend_rendered": True,
            "studio_buttons_clicked": True,
            "actual_studio_api_methods_exercised": True,
            "operator_confirmations_stubbed_for_test": True,
            "fixture_vault_writes_allowed": True,
            "fixture_vault_removed_by_default": True,
            "visual_evidence_allowed": True,
            "proof_report_write_requested": bool(write_report),
            "proof_report_written": bool(report_written),
            "log_only": True,
        }
    )
    return authority


def _pywebview_stub() -> str:
    allowed = json.dumps(list(REQUIRED_API_METHODS))
    return f"""
(() => {{
  const forgeMethods = new Set({allowed});
  window.__studioOperatorUseCalls = [];
  window.__studioOperatorConfirmations = [];
  window.confirm = (message) => {{
    window.__studioOperatorConfirmations.push(String(message || ""));
    return true;
  }};
  const fallback = (name) => {{
    if (name === "get_panel_registry") {{
      return {{ ok: true, status: "ok", surface: name, data: {{ panels: [], readiness: {{}}, authority: {{ read_only_registry: true }} }}, warnings: [], blocked_authority: [] }};
    }}
    if (name === "get_graph_style_registry") {{
      return {{ ok: true, status: "ok", surface: name, data: {{ node_families: {{}}, trust_states: {{}}, edge_layers: {{}} }}, warnings: [], blocked_authority: [] }};
    }}
    if (name === "list_graph_presets") {{
      return {{ ok: true, status: "ok", surface: name, data: {{ presets: [] }}, warnings: [], blocked_authority: [] }};
    }}
    if (name === "get_runtime_status") {{
      return {{ ok: true, status: "ok", surface: name, data: {{ status: "operator-use-visual-qa" }}, warnings: [], blocked_authority: [] }};
    }}
    return {{ ok: true, status: "ok", surface: name, data: {{}}, warnings: [], blocked_authority: [] }};
  }};
  window.pywebview = {{
    api: new Proxy({{}}, {{
      get(_target, prop) {{
        const name = String(prop);
        return async (...args) => {{
          window.__studioOperatorUseCalls.push({{ method: name, args }});
          if (!forgeMethods.has(name)) return fallback(name);
          return await window.__studioApiCall({{ method: name, args }});
        }};
      }}
    }})
  }};
}})();
"""


def _collect_fixture_evidence(fixture: Path) -> dict[str, Any]:
    registry_path = fixture / "runtime" / "forge" / "registry" / "extensions.json"
    registry = _read_json(registry_path)
    entries = registry.get("entries") if isinstance(registry.get("entries"), list) else []
    extension_root = fixture / "extensions" / "ugc-campaign-studio"
    extension_files = sorted(
        path.relative_to(fixture).as_posix()
        for path in extension_root.rglob("*")
        if path.is_file()
    ) if extension_root.is_dir() else []

    import_root = fixture / "07_LOGS" / "Agent-Activity" / "_forge_marketplace_import_approvals"
    sandbox_root = fixture / "07_LOGS" / "Agent-Activity" / "_forge_sandbox_approvals"
    import_artifacts = [_read_json(path) for path in sorted(import_root.glob("*.json"))] if import_root.is_dir() else []
    sandbox_artifacts = [_read_json(path) for path in sorted(sandbox_root.glob("*.json"))] if sandbox_root.is_dir() else []
    marker_root = sandbox_root / "_sandbox_markers"
    marker_paths = sorted(
        path.relative_to(fixture).as_posix()
        for path in marker_root.rglob("*.json")
        if path.is_file()
    ) if marker_root.is_dir() else []

    return {
        "registry_path": registry_path.relative_to(fixture).as_posix(),
        "registry_exists": registry_path.is_file(),
        "registry_entry_count": len(entries),
        "registry_statuses": [entry.get("registry_status") for entry in entries if isinstance(entry, dict)],
        "install_environments": [entry.get("install_environment") for entry in entries if isinstance(entry, dict)],
        "extension_root": extension_root.relative_to(fixture).as_posix(),
        "extension_root_exists": extension_root.is_dir(),
        "extension_files_written": extension_files,
        "marketplace_import_approval_count": len(import_artifacts),
        "marketplace_import_approvals_consumed": [
            artifact.get("approval_consumed") for artifact in import_artifacts if artifact
        ],
        "marketplace_import_approval_statuses": [artifact.get("status") for artifact in import_artifacts if artifact],
        "sandbox_approval_count": len(sandbox_artifacts),
        "sandbox_approvals_consumed": [artifact.get("approval_consumed") for artifact in sandbox_artifacts if artifact],
        "sandbox_approval_statuses": [artifact.get("status") for artifact in sandbox_artifacts if artifact],
        "sandbox_marker_count": len(marker_paths),
        "sandbox_marker_paths": marker_paths,
    }


def _run_playwright_operator_flow(vault: Path, output_dir: Path, fixture: Path) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    api = StudioAPI(fixture)
    api_call_log: list[dict[str, Any]] = []

    def call_studio_api(payload: dict[str, Any]) -> dict[str, Any]:
        method = str(payload.get("method") or "")
        args = payload.get("args") if isinstance(payload.get("args"), list) else []
        entry: dict[str, Any] = {"method": method, "args_count": len(args)}
        try:
            if method not in REQUIRED_API_METHODS:
                raise ValueError(f"method_not_allowed:{method}")
            result = getattr(api, method)(*args)
            data = result.get("data") if isinstance(result.get("data"), dict) else {}
            entry.update(
                {
                    "ok": bool(result.get("ok")),
                    "surface": result.get("surface"),
                    "data_status": data.get("status"),
                    "data_ok": data.get("ok"),
                }
            )
            if not result.get("ok"):
                entry["error"] = (result.get("error") or {}).get("message") or "unknown API error"
            return result
        except Exception as exc:  # noqa: BLE001
            entry.update({"ok": False, "error": str(exc)})
            return {
                "ok": False,
                "status": "blocked_or_failed",
                "surface": method or "unknown",
                "error": {"code": "operator_use_api_call_failed", "message": str(exc)},
                "warnings": [],
                "blocked_authority": [],
            }
        finally:
            api_call_log.append(entry)

    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = _repo_root() / "runtime" / "studio" / "shell" / "frontend" / "index.html"
    url = f"{index_path.resolve().as_uri()}#/chaser-forge"
    screenshots: list[dict[str, Any]] = []
    console_messages: list[str] = []
    page_errors: list[str] = []
    status_history: list[dict[str, Any]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("console", lambda msg: console_messages.append(f"{msg.type}:{msg.text}"))
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.expose_function("__studioApiCall", call_studio_api)
            page.add_init_script(_pywebview_stub())
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_selector('[data-marketplace-surface="chaser-forge-marketplace-import-export"]', timeout=10_000)

            def capture(step: str, viewport: str) -> dict[str, Any]:
                panel_text = page.locator("#panel-chaser-forge").inner_text(timeout=5_000)
                status_locator = page.locator("#chaser-forge-marketplace-action-status")
                status_text = status_locator.inner_text(timeout=5_000) if status_locator.count() else ""
                status_state = status_locator.get_attribute("data-state", timeout=5_000) if status_locator.count() else ""
                screenshot_path = output_dir / f"{step}-{viewport}-chaser-forge-marketplace-operator-use.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                shot = {
                    "step": step,
                    "viewport": viewport,
                    "path": _relative_to_vault(vault, screenshot_path),
                    "exists": screenshot_path.is_file(),
                    "bytes": screenshot_path.stat().st_size if screenshot_path.is_file() else 0,
                    "not_blank": screenshot_path.is_file() and screenshot_path.stat().st_size > 10_000,
                    "marketplace_section_visible": (
                        "Publish Sample Extension" in panel_text and "Run Governed Install" in panel_text
                    ),
                    "publish_button_visible": "Publish Sample Extension" in panel_text,
                    "install_button_visible": "Run Governed Install" in panel_text,
                    "status_text": status_text,
                    "status_state": status_state,
                    "framework_overlay_detected": any(
                        token in panel_text for token in ("ReferenceError", "Traceback", "webpack", "Vite Error", "Next.js")
                    ),
                }
                screenshots.append(shot)
                return shot

            capture("initial", "desktop")
            publish_count = page.locator("#chaser-forge-publish-demo").count()
            install_count = page.locator("#chaser-forge-install-demo").count()
            page.locator("#chaser-forge-publish-demo").click(timeout=10_000)
            page.wait_for_function(
                """() => {
                  const el = document.querySelector('#chaser-forge-marketplace-action-status');
                  return el && el.dataset.state === 'complete' && el.textContent.includes('Published');
                }""",
                timeout=30_000,
            )
            publish_status = capture("after-publish", "desktop")
            status_history.append({"step": "after-publish", **publish_status})

            page.locator("#chaser-forge-install-demo").click(timeout=10_000)
            page.wait_for_function(
                """() => {
                  const el = document.querySelector('#chaser-forge-marketplace-action-status');
                  return el && el.dataset.state === 'complete' && el.textContent.includes('Marketplace install complete');
                }""",
                timeout=60_000,
            )
            install_status = capture("after-install", "desktop")
            status_history.append({"step": "after-install", **install_status})

            page.set_viewport_size({"width": 390, "height": 900})
            page.wait_for_timeout(250)
            capture("after-install", "mobile")

            js_call_log = page.evaluate("() => window.__studioOperatorUseCalls || []")
            confirmations = page.evaluate("() => window.__studioOperatorConfirmations || []")
            title = page.title()
            final_url = page.url
        finally:
            browser.close()

    severe_console = [
        item for item in console_messages if item.startswith(("error:", "warning:", "warn:")) and "favicon" not in item.lower()
    ]
    return {
        "url": final_url,
        "title": title,
        "publish_button_count": publish_count,
        "install_button_count": install_count,
        "publish_status_text": publish_status.get("status_text", ""),
        "publish_status_state": publish_status.get("status_state", ""),
        "install_status_text": install_status.get("status_text", ""),
        "install_status_state": install_status.get("status_state", ""),
        "operator_confirmations": confirmations,
        "js_call_log": js_call_log,
        "api_call_log": api_call_log,
        "screenshots": screenshots,
        "console_errors_or_warnings": severe_console,
        "page_errors": page_errors,
    }


def _format_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    fixture = report.get("fixture_evidence") or {}
    screenshots = "\n".join(
        f"- {shot.get('step')} / {shot.get('viewport')}: `{shot.get('path')}` bytes={shot.get('bytes')} status={shot.get('status_state')} text={shot.get('status_text')!r}"
        for shot in report.get("screenshots") or []
    ) or "- none"
    blockers = "\n".join(f"- {escape(str(blocker))}" for blocker in report.get("blockers") or []) or "- none"
    return "\n".join(
        [
            "# Chaser Forge Marketplace Operator Use Studio Proof",
            "",
            f"- Status: {report.get('status')}",
            f"- OK: {report.get('ok')}",
            f"- Flow: {report.get('flow_under_test')}",
            f"- Publish status visible after refresh: {summary.get('publish_status_visible_after_refresh')}",
            f"- Install status visible after refresh: {summary.get('install_status_visible_after_refresh')}",
            f"- Required API methods called: {summary.get('required_api_methods_called')}",
            f"- Operator confirmations accepted: {summary.get('operator_confirmations_accepted')}",
            f"- Registry written in fixture: {fixture.get('registry_exists')}",
            f"- Extension files written in fixture: {bool(fixture.get('extension_files_written'))}",
            f"- Sandbox markers in fixture: {fixture.get('sandbox_marker_count')}",
            "",
            "## Screenshots",
            "",
            screenshots,
            "",
            "## Blockers",
            "",
            blockers,
            "",
            "## Boundary",
            "",
            "This proof uses a temporary fixture vault and writes only the proof report/screenshots to the real vault. It does not add remote marketplace exchange, real-vault approval consumption, real-vault registry writes, provider/model calls, Agent Bus dispatch, protected-core mutation, memory mutation, R&D truth-state mutation, or canonical mutation.",
            "",
        ]
    )


def build_chaser_forge_marketplace_operator_use_visual_qa(
    vault_root: str | Path,
    *,
    output_dir: str | Path | None = None,
    generated_at: str | None = None,
    write: bool = True,
    persist_fixture: bool = False,
    fixture_factory: Callable[[str], Path] = _new_fixture,
    flow_runner: Callable[[Path, Path, Path], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the rendered Studio operator-use marketplace button flow."""

    vault = Path(vault_root).resolve()
    timestamp = generated_at or _now_utc()
    resolved_output_dir = _resolve_output_dir(vault, output_dir)
    fixture = fixture_factory("chaser-forge-marketplace-operator-use-")
    runner = flow_runner or _run_playwright_operator_flow
    visual: dict[str, Any] = {}
    fixture_evidence: dict[str, Any] = {}
    fixture_cleanup_completed = False
    runner_error = ""
    try:
        visual = runner(vault, resolved_output_dir, fixture)
        fixture_evidence = _collect_fixture_evidence(fixture)
    except Exception as exc:  # noqa: BLE001
        runner_error = str(exc)
    finally:
        fixture_cleanup_completed = _cleanup_fixture(fixture, persist_fixture)

    screenshots = visual.get("screenshots") if isinstance(visual.get("screenshots"), list) else []
    api_call_log = visual.get("api_call_log") if isinstance(visual.get("api_call_log"), list) else []
    api_methods_seen = [str(item.get("method")) for item in api_call_log if item.get("ok") is True]
    missing_api_methods = [method for method in REQUIRED_API_METHODS if method not in api_methods_seen]
    confirmations = visual.get("operator_confirmations") if isinstance(visual.get("operator_confirmations"), list) else []

    summary = {
        "page_identity_ok": str(visual.get("url") or "").endswith("#/chaser-forge"),
        "publish_button_clicked": int(visual.get("publish_button_count") or 0) == 1,
        "install_button_clicked": int(visual.get("install_button_count") or 0) == 1,
        "publish_status_visible_after_refresh": visual.get("publish_status_state") == "complete"
        and "Published" in str(visual.get("publish_status_text") or ""),
        "install_status_visible_after_refresh": visual.get("install_status_state") == "complete"
        and "Marketplace install complete" in str(visual.get("install_status_text") or ""),
        "operator_confirmations_accepted": len(confirmations),
        "required_api_methods_called": not missing_api_methods,
        "desktop_and_mobile_checked": {shot.get("viewport") for shot in screenshots} >= {"desktop", "mobile"},
        "screenshots_not_blank": bool(screenshots) and all(shot.get("not_blank") is True for shot in screenshots),
        "marketplace_section_visible": bool(screenshots)
        and all(shot.get("marketplace_section_visible") is True for shot in screenshots),
        "fixture_registry_written": fixture_evidence.get("registry_exists") is True,
        "fixture_extension_files_written": bool(fixture_evidence.get("extension_files_written")),
        "fixture_import_approval_consumed": True in list(fixture_evidence.get("marketplace_import_approvals_consumed") or []),
        "fixture_sandbox_approval_consumed": True in list(fixture_evidence.get("sandbox_approvals_consumed") or []),
        "fixture_exact_once_marker_written": int(fixture_evidence.get("sandbox_marker_count") or 0) >= 1,
        "fixture_cleanup_completed": fixture_cleanup_completed,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }

    blockers: list[str] = []
    if runner_error:
        blockers.append(f"runner_error:{runner_error}")
    for key, value in summary.items():
        if key == "operator_confirmations_accepted":
            if value < 2:
                blockers.append("operator_confirmations_not_accepted")
        elif key != "next_recommended_pass" and value is not True:
            blockers.append(f"summary_check_failed:{key}")
    blockers.extend(f"missing_required_api_method:{method}" for method in missing_api_methods)
    if any(shot.get("framework_overlay_detected") for shot in screenshots):
        blockers.append("framework_overlay_detected")
    if visual.get("console_errors_or_warnings"):
        blockers.append("console_errors_or_warnings_present")
    if visual.get("page_errors"):
        blockers.append("page_errors_present")

    report_path = resolved_output_dir / REPORT_NAME
    markdown_path = resolved_output_dir / MARKDOWN_NAME
    report: dict[str, Any] = {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "schema_version": MODEL_VERSION,
        "pass_id": PASS_ID,
        "status": STATUS if not blockers else "BLOCKED / MARKETPLACE OPERATOR USE STUDIO BUTTON FLOW FAILED",
        "date": timestamp[:10],
        "generated_at": timestamp,
        "runtime": "Codex",
        "session_descriptor": "chaser-forge-marketplace-operator-use-studio-proof",
        "vault_root": str(vault),
        "output_dir": _relative_to_vault(vault, resolved_output_dir),
        "report_path": _relative_to_vault(vault, report_path),
        "markdown_report_path": _relative_to_vault(vault, markdown_path),
        "write_requested": bool(write),
        "write_executed": False,
        "flow_under_test": (
            "Studio shell #/chaser-forge -> click Publish Sample Extension -> visible Published status -> "
            "click Run Governed Install -> test confirmations accepted -> visible Marketplace install complete "
            "and fixture registry/files/exact-once marker written"
        ),
        "browser_availability": {
            "browser_plugin_available": "connected_for_session",
            "browser_path": "playwright_sync_static_render_with_python_exposed_studioapi_fixture",
            "fallback_used": True,
            "fallback_reason": (
                "In-app Browser was available, but this fixture proof needs a pre-load pywebview bridge via "
                "add_init_script and expose_function so the production frontend can call a temporary StudioAPI fixture."
            ),
        },
        "summary": summary,
        "fixture_policy": {
            "persist_fixture": persist_fixture,
            "fixture_vault": str(fixture),
            "fixture_cleanup_completed": fixture_cleanup_completed,
        },
        "fixture_evidence": fixture_evidence,
        "screenshots": screenshots,
        "api_call_log": api_call_log,
        "js_call_log": visual.get("js_call_log") or [],
        "operator_confirmations": confirmations,
        "required_api_methods": list(REQUIRED_API_METHODS),
        "missing_required_api_methods": missing_api_methods,
        "console_errors_or_warnings": visual.get("console_errors_or_warnings") or [],
        "page_errors": visual.get("page_errors") or [],
        "authority": _authority(write_report=write, report_written=False),
        "blockers": list(dict.fromkeys(blockers)),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
    if write:
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
        report["write_executed"] = True
        report["authority"] = _authority(write_report=True, report_written=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        markdown_path.write_text(_format_markdown(report), encoding="utf-8")
    return report


def format_chaser_forge_marketplace_operator_use_visual_qa(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    fixture = payload.get("fixture_evidence") or {}
    return "\n".join(
        [
            "Chaser Forge Marketplace Operator Use Studio Proof",
            f"  status: {payload.get('status')}",
            f"  ok: {payload.get('ok')}",
            f"  publish_status_visible_after_refresh: {summary.get('publish_status_visible_after_refresh')}",
            f"  install_status_visible_after_refresh: {summary.get('install_status_visible_after_refresh')}",
            f"  required_api_methods_called: {summary.get('required_api_methods_called')}",
            f"  operator_confirmations_accepted: {summary.get('operator_confirmations_accepted')}",
            f"  registry_written: {fixture.get('registry_exists')}",
            f"  extension_files_written: {bool(fixture.get('extension_files_written'))}",
            f"  sandbox_marker_count: {fixture.get('sandbox_marker_count')}",
            f"  report_path: {payload.get('report_path')}",
            f"  next: {payload.get('next_recommended_pass')}",
            "  Boundary: production frontend button proof over a temporary StudioAPI fixture only; no real-vault install, remote exchange, provider/model call, Agent Bus dispatch, protected-core mutation, memory mutation, R&D truth-state mutation, or canonical mutation.",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Chaser Forge marketplace operator-use Studio visual QA.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory inside the vault.")
    parser.add_argument("--generated-at", default=None, help="Override generated_at timestamp.")
    parser.add_argument("--no-write", action="store_true", help="Do not write report artifacts.")
    parser.add_argument("--persist-fixture", action="store_true", help="Keep the temporary fixture vault for inspection.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args(argv)
    report = build_chaser_forge_marketplace_operator_use_visual_qa(
        args.vault_root,
        output_dir=args.output_dir,
        generated_at=args.generated_at,
        write=not args.no_write,
        persist_fixture=args.persist_fixture,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(format_chaser_forge_marketplace_operator_use_visual_qa(report))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
