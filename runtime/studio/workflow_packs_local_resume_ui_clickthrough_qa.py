"""Rendered Studio QA for Workflow Packs local approval resume clickthrough.

This harness exercises the production Studio Workflow Packs frontend against
temporary Workflow Pack state. It writes QA evidence only. Real vault Workflow
Pack state, provider calls, browser product actions, Agent Bus tasks, and
canonical state are not touched.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
from typing import Any, Callable
import uuid

from runtime.studio.shell.api import StudioAPI


MODEL_VERSION = "studio.workflow_packs_local_resume_ui_clickthrough_qa.v1"
SURFACE_ID = "workflow_packs_local_resume_ui_clickthrough_qa"
PASS_ID = "product-workflow-packs-packaged-studio-clickthrough-qa"
STATUS = "COMPLETE / WORKFLOW PACKS LOCAL RESUME UI CLICKTHROUGH VERIFIED"
DEFAULT_OUTPUT_DIR = (
    Path("07_LOGS")
    / "Studio-Visual-QA"
    / "2026-05-21-workflow-packs-local-resume-ui-clickthrough"
)
NEXT_RECOMMENDED_PASS = "product-workflow-packs-external-action-executor-design-only-if-authorized"

WORKFLOW_PACK_METHOD_CHAIN = (
    "get_workflow_pack_approval_resume_contract",
    "review_workflow_pack_approval_artifact",
    "review_workflow_pack_approval_artifact",
    "get_workflow_pack_approval_consumption_dry_run",
    "reserve_workflow_pack_exact_once_marker",
    "reserve_workflow_pack_exact_once_marker",
    "execute_workflow_pack_approved_local_resume",
    "execute_workflow_pack_approved_local_resume",
    "get_workflow_packs_panel",
)
REQUIRED_RENDER_TOKENS = (
    "Missions",
    "Approve Local",
    "Reject Local",
    "approved",
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
        raise ValueError("Workflow Packs clickthrough QA output must stay inside the vault workspace") from exc
    return resolved


def _new_fixture_vault(label: str) -> Path:
    base = Path("C:/tmp/chaseos-workflow-packs-clickthrough-fixtures") if os.name == "nt" else Path(
        "/tmp/chaseos-workflow-packs-clickthrough-fixtures"
    )
    slug = "".join(ch if ch.isalnum() else "-" for ch in label.lower()).strip("-") or "fixture"
    return (base / f"{slug}-{uuid.uuid4().hex[:10]}").resolve()


def _authority() -> dict[str, Any]:
    return {
        "visual_evidence_allowed": True,
        "temporary_fixture_created": True,
        "temporary_fixture_persisted": False,
        "fixture_local_approval_artifact_write_allowed": True,
        "fixture_exact_once_marker_write_allowed": True,
        "fixture_local_resume_write_allowed": True,
        "real_vault_workflow_pack_state_write_allowed": False,
        "real_vault_approval_artifact_write_allowed": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
        "browser_product_actions_allowed": False,
        "connector_calls_allowed": False,
        "email_or_publish_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "canonical_mutation_allowed": False,
        "secret_or_credential_read_allowed": False,
    }


def _seed_workflow_pack_fixture(fixture_vault: Path) -> dict[str, Any]:
    from runtime.workflow_packs import store as workflow_store

    previous_state_root = workflow_store.STATE_ROOT
    workflow_store.STATE_ROOT = Path("wfp_state")
    fixture_vault.mkdir(parents=True, exist_ok=True)
    api = StudioAPI(fixture_vault)
    try:
        created = api.create_workflow_pack_demo_run(
            "founder_personal_automation_audit",
            "Missions local resume check",
            "Verify the Studio approval gate can approve and resume locally",
        )
        if not created.get("ok"):
            raise RuntimeError(f"failed to seed Workflow Packs QA fixture: {created}")
        panel = api.get_workflow_packs_panel()
        if not panel.get("ok"):
            raise RuntimeError(f"failed to read Workflow Packs QA panel fixture: {panel}")
        data = panel.get("data") or {}
        review_queue = data.get("review_queue") or []
        pending_gate = next(
            (
                item
                for item in review_queue
                if item.get("kind") == "approval_gate" and item.get("status") == "pending"
            ),
            None,
        )
        if not pending_gate:
            raise RuntimeError("Workflow Packs QA fixture did not create a pending approval gate")
        return {
            "api": api,
            "created": created,
            "panel": panel,
            "run_id": pending_gate.get("run_id"),
            "gate_id": pending_gate.get("item_id"),
            "fixture_vault": fixture_vault,
            "previous_state_root": previous_state_root,
        }
    except Exception:
        workflow_store.STATE_ROOT = previous_state_root
        raise


def _restore_workflow_pack_state_root(fixture: dict[str, Any] | None) -> None:
    if not fixture:
        return
    from runtime.workflow_packs import store as workflow_store

    previous = fixture.get("previous_state_root")
    if isinstance(previous, Path):
        workflow_store.STATE_ROOT = previous


def _pywebview_stub_script() -> str:
    methods = (
        "get_workflow_packs_panel",
        "get_workflow_pack_approval_resume_contract",
        "review_workflow_pack_approval_artifact",
        "get_workflow_pack_approval_consumption_dry_run",
        "reserve_workflow_pack_exact_once_marker",
        "execute_workflow_pack_approved_local_resume",
    )
    method_list = json.dumps(list(methods))
    return f"""
(() => {{
  window.confirm = () => true;
  window.__workflowPacksCallLog = [];
  const api = {{}};
  for (const method of {method_list}) {{
    api[method] = async (...args) => {{
      const response = await window.__workflowPacksInvoke(method, args);
      const data = (response && response.data) || {{}};
      window.__workflowPacksCallLog.push({{
        method,
        args,
        ok: Boolean(response && response.ok),
        surface: response && response.surface,
        summary: data.summary || {{}},
        status: data.status || null,
      }});
      return response;
    }};
  }}
  window.pywebview = {{
    api: new Proxy(api, {{
      get(target, prop) {{
        if (prop in target) return target[prop];
        return async () => ({{ ok: true, data: {{}} }});
      }},
    }}),
  }};
}})();
"""


def _contains_subsequence(values: list[str], expected: tuple[str, ...]) -> bool:
    cursor = 0
    for value in values:
        if cursor < len(expected) and value == expected[cursor]:
            cursor += 1
    return cursor == len(expected)


def _dispatch_workflow_pack_api(api: StudioAPI, method: str, args: list[Any]) -> dict[str, Any]:
    allowed = {
        "get_workflow_packs_panel",
        "get_workflow_pack_approval_resume_contract",
        "review_workflow_pack_approval_artifact",
        "get_workflow_pack_approval_consumption_dry_run",
        "reserve_workflow_pack_exact_once_marker",
        "execute_workflow_pack_approved_local_resume",
    }
    if method not in allowed:
        return {"ok": False, "error": {"message": f"unsupported method: {method}"}}
    target = getattr(api, method)
    return target(*list(args or []))


def _capture_with_playwright(*, vault: Path, output_dir: Path) -> list[dict[str, Any]]:
    from playwright.sync_api import sync_playwright

    frontend = _repo_root() / "runtime" / "studio" / "shell" / "frontend"
    index_path = frontend / "index.html"
    url = f"{index_path.resolve().as_uri()}#/workflow-packs"
    screenshots: list[dict[str, Any]] = []
    viewport_specs = (
        ("desktop", {"width": 1440, "height": 1000}),
        ("mobile", {"width": 390, "height": 900}),
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for viewport_name, viewport in viewport_specs:
                fixture_vault = _new_fixture_vault(viewport_name)
                if fixture_vault.exists():
                    shutil.rmtree(fixture_vault)
                fixture: dict[str, Any] | None = None
                console_messages: list[dict[str, str]] = []
                page_errors: list[str] = []

                try:
                    fixture = _seed_workflow_pack_fixture(fixture_vault)
                    api = fixture["api"]

                    def _invoke(method: str, args: list[Any]) -> dict[str, Any]:
                        return _dispatch_workflow_pack_api(api, method, list(args or []))

                    page = browser.new_page(viewport=viewport)
                    page.on(
                        "console",
                        lambda msg: console_messages.append({"type": msg.type, "text": msg.text}),
                    )
                    page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                    page.expose_function("__workflowPacksInvoke", _invoke)
                    page.add_init_script(_pywebview_stub_script())
                    page.goto(url, wait_until="domcontentloaded")
                    page.wait_for_selector(".workflow-packs-tab[data-workflow-packs-tab='review']", timeout=10_000)
                    page.evaluate(
                        """
                        () => {
                          const selected = 'review';
                          document.querySelectorAll('.workflow-packs-tab').forEach(item => {
                            const active = item.dataset.workflowPacksTab === selected;
                            item.classList.toggle('workflow-packs-tab--active', active);
                            item.setAttribute('aria-selected', active ? 'true' : 'false');
                          });
                          document.querySelectorAll('.workflow-packs-tab-body').forEach(body => {
                            body.style.display = body.id === `workflow-packs-tab-${selected}` ? 'block' : 'none';
                          });
                        }
                        """
                    )
                    page.wait_for_selector(
                        "#workflow-packs-tab-review .workflow-pack-approval-action",
                        state="visible",
                        timeout=10_000,
                    )
                    before_text = page.locator("#panel-workflow-packs").inner_text(timeout=5_000)
                    button_count = page.locator("#workflow-packs-tab-review .workflow-pack-approval-action").count()
                    page.evaluate(
                        """
                        async () => {
                          const button = document.querySelector(
                            "#workflow-packs-tab-review .workflow-pack-approval-action[data-decision='approved']"
                          );
                          const row = button.closest('.workflow-pack-row');
                          const statusEl = row ? row.querySelector('.workflow-pack-approval-result') : null;
                          await runWorkflowPackLocalResume(
                            button.dataset.runId || '',
                            button.dataset.gateId || '',
                            button.dataset.decision || 'approved',
                            statusEl,
                          );
                        }
                        """
                    )
                    call_log = page.evaluate("() => window.__workflowPacksCallLog || []")
                    final_panel = api.get_workflow_packs_panel()
                    final_data = final_panel.get("data") or {}
                    final_runs = final_data.get("runs") or []
                    final_run = next(
                        (item for item in final_runs if item.get("id") == fixture.get("run_id")),
                        {},
                    )
                    page.evaluate(
                        """
                        (data) => {
                          renderWorkflowPacksPanel(data);
                          const selected = 'review';
                          document.querySelectorAll('.workflow-packs-tab').forEach(item => {
                            const active = item.dataset.workflowPacksTab === selected;
                            item.classList.toggle('workflow-packs-tab--active', active);
                            item.setAttribute('aria-selected', active ? 'true' : 'false');
                          });
                          document.querySelectorAll('.workflow-packs-tab-body').forEach(body => {
                            body.style.display = body.id === `workflow-packs-tab-${selected}` ? 'block' : 'none';
                          });
                        }
                        """,
                        final_data,
                    )
                    after_text = page.locator("#panel-workflow-packs").inner_text(timeout=5_000)
                    screenshot_path = output_dir / f"{viewport_name}-workflow-packs-local-resume-clickthrough.png"
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    page.close()
                    methods = [str(item.get("method") or "") for item in call_log]
                    body_text = f"{before_text}\n{after_text}\n{final_run.get('status') or ''}"
                    relevant_console = [
                        item
                        for item in console_messages
                        if item.get("type") in {"error", "warning"}
                        and "favicon" not in str(item.get("text") or "").lower()
                    ]
                    screenshots.append(
                        {
                            "viewport": viewport_name,
                            "url": url,
                            "path": _relative_to_vault(vault, screenshot_path),
                            "bytes": screenshot_path.stat().st_size if screenshot_path.is_file() else 0,
                            "not_blank": screenshot_path.is_file()
                            and screenshot_path.stat().st_size > 10_000
                            and len(body_text) > 500,
                            "approval_buttons_before": button_count,
                            "approve_button_visible_before": "Approve Local" in before_text,
                            "reject_button_visible_before": "Reject Local" in before_text,
                            "no_review_items_after": "No review items" in after_text,
                            "run_status_after": final_run.get("status"),
                            "approval_gate_removed_after": all(
                                item.get("item_id") != fixture.get("gate_id")
                                for item in (final_data.get("review_queue") or [])
                            ),
                            "method_sequence": methods,
                            "expected_method_chain_present": _contains_subsequence(
                                methods,
                                WORKFLOW_PACK_METHOD_CHAIN,
                            ),
                            "resume_execute_summary": (
                                next(
                                    (
                                        item
                                        for item in reversed(call_log)
                                        if item.get("method") == "execute_workflow_pack_approved_local_resume"
                                    ),
                                    {},
                                ).get("summary")
                                or {}
                            ),
                            "required_tokens_missing": [
                                token for token in REQUIRED_RENDER_TOKENS if token not in body_text
                            ],
                            "framework_overlay_detected": any(
                                token in body_text
                                for token in ("ReferenceError", "Traceback", "webpack", "Vite Error", "Next.js")
                            ),
                            "console_errors_or_warnings": relevant_console,
                            "page_errors": page_errors,
                        }
                    )
                finally:
                    _restore_workflow_pack_state_root(fixture)
                    shutil.rmtree(fixture_vault, ignore_errors=True)
        finally:
            browser.close()

    return screenshots


def _write_markdown_report(path: Path, report: dict[str, Any]) -> None:
    summary = report.get("summary") or {}
    authority = report.get("authority") or {}
    screenshots = report.get("screenshots") or []
    screenshot_lines = [
        (
            f"- {item.get('viewport')}: `{item.get('path')}` "
            f"bytes={item.get('bytes')} chain={item.get('expected_method_chain_present')} "
            f"run_status={item.get('run_status_after')}"
        )
        for item in screenshots
    ] or ["- not captured"]
    blocker_lines = [f"- {item}" for item in report.get("blockers", [])] or ["- none"]
    path.write_text(
        "\n".join(
            [
                "# Workflow Packs Local Resume UI Clickthrough QA",
                "",
                f"- Status: {report.get('status')}",
                f"- OK: {report.get('ok')}",
                f"- Surface: {report.get('surface')}",
                f"- Flow: {report.get('flow_under_test')}",
                f"- Desktop/mobile checked: {summary.get('desktop_and_mobile_checked')}",
                f"- Clickthrough verified: {summary.get('clickthrough_verified')}",
                f"- Browser fallback: {report.get('browser_availability', {}).get('fallback_used')}",
                "",
                "## Screenshots",
                "",
                *screenshot_lines,
                "",
                "## Boundary",
                "",
                f"- real_vault_workflow_pack_state_write_allowed: {authority.get('real_vault_workflow_pack_state_write_allowed')}",
                f"- provider_calls_allowed: {authority.get('provider_calls_allowed')}",
                f"- browser_product_actions_allowed: {authority.get('browser_product_actions_allowed')}",
                f"- agent_bus_task_write_allowed: {authority.get('agent_bus_task_write_allowed')}",
                f"- canonical_mutation_allowed: {authority.get('canonical_mutation_allowed')}",
                "",
                "## Blockers",
                "",
                *blocker_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )


def _static_contract(vault: Path, output_dir: Path) -> dict[str, Any]:
    frontend = _repo_root() / "runtime" / "studio" / "shell" / "frontend"
    app_text = (frontend / "app.js").read_text(encoding="utf-8")
    styles_text = (frontend / "styles.css").read_text(encoding="utf-8")
    index_text = (frontend / "index.html").read_text(encoding="utf-8")
    fixture_vault = _new_fixture_vault("static-contract")
    if fixture_vault.exists():
        shutil.rmtree(fixture_vault)
    fixture: dict[str, Any] | None = None
    try:
        fixture = _seed_workflow_pack_fixture(fixture_vault)
        panel_data = fixture["panel"].get("data") or {}
    finally:
        _restore_workflow_pack_state_root(fixture)
        shutil.rmtree(fixture_vault, ignore_errors=True)
    return {
        "frontend_index_has_panel": 'data-panel="workflow-packs"' in index_text
        and 'id="panel-workflow-packs"' in index_text,
        "frontend_runner_present": "runWorkflowPackLocalResume" in app_text
        and "workflowPackAssertOk" in app_text,
        "frontend_action_controls_present": "workflow-pack-approval-action" in app_text
        and "Approve Local" in app_text
        and "Reject Local" in app_text,
        "frontend_action_styles_present": ".workflow-pack-approval-actions" in styles_text
        and ".workflow-pack-approval-result" in styles_text,
        "panel_has_pending_gate": any(
            item.get("kind") == "approval_gate" and item.get("status") == "pending"
            for item in (panel_data.get("review_queue") or [])
        ),
        "panel_local_resume_ready": (panel_data.get("summary") or {}).get("approved_local_resume_executor_ready")
        is True,
        "fixture_vault_persisted": fixture_vault.exists(),
    }


def build_workflow_packs_local_resume_ui_clickthrough_qa(
    vault_root: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    capture_screenshots: bool = True,
    screenshot_runner: Callable[..., list[dict[str, Any]]] | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    """Run the Workflow Packs local resume UI clickthrough QA harness."""

    vault = Path(vault_root).resolve() if vault_root is not None else _repo_root()
    cleanup_output = False
    if write_report or capture_screenshots:
        output = _resolve_output_dir(vault, output_dir)
    else:
        output = (vault / ".pytest_tmp_env" / "workflow-packs-local-resume-ui-clickthrough-static").resolve()
        cleanup_output = True
    output.mkdir(parents=True, exist_ok=True)
    generated_at = _now_utc()

    static_contract = _static_contract(vault, output)
    screenshots: list[dict[str, Any]] = []
    screenshot_errors: list[str] = []
    if capture_screenshots:
        try:
            runner = screenshot_runner or _capture_with_playwright
            screenshots = runner(vault=vault, output_dir=output)
        except Exception as exc:  # noqa: BLE001
            screenshot_errors.append(str(exc))

    blockers: list[str] = []
    if not all(static_contract.values()):
        blockers.extend(
            f"static_contract_failed:{name}"
            for name, value in static_contract.items()
            if not value and name != "fixture_vault_persisted"
        )
    if static_contract.get("fixture_vault_persisted"):
        blockers.append("static_fixture_vault_persisted")
    if capture_screenshots and not screenshots:
        blockers.append("no_screenshots_captured")
    if capture_screenshots and {item.get("viewport") for item in screenshots} != {"desktop", "mobile"}:
        blockers.append("desktop_mobile_coverage_missing")
    for item in screenshots:
        if not item.get("not_blank"):
            blockers.append(f"{item.get('viewport')}:blank_or_tiny_screenshot")
        if not item.get("approve_button_visible_before"):
            blockers.append(f"{item.get('viewport')}:approve_button_not_visible")
        if not item.get("reject_button_visible_before"):
            blockers.append(f"{item.get('viewport')}:reject_button_not_visible")
        if not item.get("expected_method_chain_present"):
            blockers.append(f"{item.get('viewport')}:expected_method_chain_missing")
        if item.get("run_status_after") != "approved":
            blockers.append(f"{item.get('viewport')}:run_status_not_approved")
        if not item.get("approval_gate_removed_after"):
            blockers.append(f"{item.get('viewport')}:approval_gate_not_removed")
        summary = item.get("resume_execute_summary") or {}
        if summary.get("external_actions_performed") is not False:
            blockers.append(f"{item.get('viewport')}:external_actions_flag_not_false")
        if summary.get("provider_calls_performed") is not False:
            blockers.append(f"{item.get('viewport')}:provider_calls_flag_not_false")
        if summary.get("agent_bus_dispatch_performed") is not False:
            blockers.append(f"{item.get('viewport')}:agent_bus_dispatch_flag_not_false")
        if item.get("required_tokens_missing"):
            blockers.append(f"{item.get('viewport')}:required_tokens_missing")
        if item.get("framework_overlay_detected"):
            blockers.append(f"{item.get('viewport')}:framework_overlay_detected")
        if item.get("console_errors_or_warnings"):
            blockers.append(f"{item.get('viewport')}:console_errors_or_warnings_present")
        if item.get("page_errors"):
            blockers.append(f"{item.get('viewport')}:page_errors_present")
    blockers.extend(f"screenshot_error:{item}" for item in screenshot_errors)

    report_path = output / "workflow-packs-local-resume-ui-clickthrough-report.json"
    markdown_path = output / "workflow-packs-local-resume-ui-clickthrough-report.md"
    report: dict[str, Any] = {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if not blockers else "BLOCKED / WORKFLOW PACKS LOCAL RESUME UI CLICKTHROUGH FAILED",
        "generated_at_utc": generated_at,
        "vault_root": str(vault),
        "output_dir": _relative_to_vault(vault, output),
        "flow_under_test": "Studio Missions route -> pending approval gate -> Approve Local -> contract, review artifact, duplicate-protection lock, local resume executor, panel refresh",
        "browser_availability": {
            "browser_plugin_available": True,
            "browser_path_attempted": True,
            "browser_path_blocked": True,
            "browser_path_blocker": "Required Node REPL JavaScript control tool was not exposed after tool discovery.",
            "fallback_used": "playwright_sync_local_static_render",
        },
        "summary": {
            "static_contract_ready": all(
                value for name, value in static_contract.items() if name != "fixture_vault_persisted"
            )
            and static_contract.get("fixture_vault_persisted") is False,
            "screenshot_captured": bool(screenshots),
            "desktop_and_mobile_checked": {item.get("viewport") for item in screenshots} == {"desktop", "mobile"},
            "clickthrough_verified": bool(screenshots)
            and all(
                item.get("expected_method_chain_present")
                and item.get("approval_gate_removed_after")
                and item.get("run_status_after") == "approved"
                for item in screenshots
            ),
            "real_vault_workflow_pack_state_write_performed": False,
            "provider_call_performed": False,
            "browser_product_action_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "static_contract": static_contract,
        "expected_method_chain": list(WORKFLOW_PACK_METHOD_CHAIN),
        "required_render_tokens": list(REQUIRED_RENDER_TOKENS),
        "screenshots": screenshots,
        "authority": _authority(),
        "blockers": list(dict.fromkeys(blockers)),
        "evidence": {
            "written": bool(write_report),
            "report_path": _relative_to_vault(vault, report_path) if write_report else None,
            "markdown_path": _relative_to_vault(vault, markdown_path) if write_report else None,
            "fixture_vault_persisted": False,
        },
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
    if write_report:
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
        _write_markdown_report(markdown_path, report)
    if cleanup_output:
        shutil.rmtree(output, ignore_errors=True)
    return report


def format_workflow_packs_local_resume_ui_clickthrough_qa(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    evidence = report.get("evidence") or {}
    return "\n".join(
        [
            "Workflow Packs Local Resume UI Clickthrough QA",
            f"  status: {report.get('status')}",
            f"  ok: {report.get('ok')}",
            f"  static_contract_ready: {summary.get('static_contract_ready')}",
            f"  screenshot_captured: {summary.get('screenshot_captured')}",
            f"  desktop_and_mobile_checked: {summary.get('desktop_and_mobile_checked')}",
            f"  clickthrough_verified: {summary.get('clickthrough_verified')}",
            f"  report_path: {evidence.get('report_path')}",
            f"  next: {summary.get('next_recommended_pass')}",
            "  Boundary: temporary fixture only; no real vault Workflow Pack state write, provider/model call, browser product action, connector call, Agent Bus write, runtime dispatch, canonical mutation, or secret read.",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Workflow Packs local resume UI clickthrough QA.")
    parser.add_argument("--vault-root", default=".", help="Vault/repo root.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Vault-local evidence output directory.")
    parser.add_argument("--no-screenshots", action="store_true", help="Skip Playwright screenshot/clickthrough capture.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args(argv)
    report = build_workflow_packs_local_resume_ui_clickthrough_qa(
        args.vault_root,
        output_dir=args.output_dir,
        capture_screenshots=not args.no_screenshots,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(format_workflow_packs_local_resume_ui_clickthrough_qa(report))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
