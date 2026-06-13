"""Static rendered proof for Chaser Forge Approval Center lifecycle visibility.

This harness renders the production Approval Center frontend against a temporary
Forge approval fixture. It writes visual QA evidence only; it does not approve,
consume, execute, install, roll back, or mutate real Forge approval roots.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import shutil
from typing import Any, Callable

from runtime.forge.registry import (
    LIVE_INSTALL_APPROVAL_RECORD_TYPE,
    LIVE_INSTALL_APPROVAL_RELATIVE_DIR,
    LIVE_INSTALL_APPROVAL_SCOPE,
    ROLLBACK_APPROVAL_RECORD_TYPE,
    ROLLBACK_APPROVAL_RELATIVE_DIR,
    ROLLBACK_APPROVAL_SCOPE,
    SANDBOX_APPROVAL_RECORD_TYPE,
    SANDBOX_APPROVAL_RELATIVE_DIR,
    SANDBOX_APPROVAL_SCOPE,
)
from runtime.studio.approval_center_panel import build_approval_center_panel


MODEL_VERSION = "studio.chaser_forge_approval_center_lifecycle_visual_qa.v1"
SURFACE_ID = "chaser_forge_approval_center_lifecycle_visual_qa"
PASS_ID = "chaser-forge-manual-ui-lifecycle-proof"
STATUS = "PARTIAL / STATIC UI LIFECYCLE + DECISION HANDOFF PROOF / VERIFIED"
DEFAULT_OUTPUT_DIR = Path("07_LOGS") / "Studio-Visual-QA" / "2026-05-20-chaser-forge-approval-center-lifecycle-proof"
NEXT_RECOMMENDED_PASS = "chaser-forge-decision-bound-executor-consumption-proof"

LIFECYCLE_TOKENS = (
    "Chaser Forge Approval Requests",
    "pending_operator_review",
    "approved_pending_execution",
    "consumed",
    "rejected",
    "invalid_packet",
    "Source-specific handoff",
    "review_chaser_forge_approval_decision",
    "available=true",
    "extensions/ugc-campaign-studio/manifest.json",
    "Canonical mutation",
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
        raise ValueError("Chaser Forge lifecycle visual QA output must stay inside the vault workspace") from exc
    return resolved


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "visual_evidence_allowed": True,
        "source_specific_decision_handoff_visible": True,
        "approval_decision_allowed": False,
        "approval_artifact_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "forge_sandbox_install_allowed": False,
        "forge_live_install_allowed": False,
        "forge_rollback_allowed": False,
        "forge_registry_mutation_allowed": False,
        "extension_file_write_allowed": False,
        "extension_file_delete_allowed": False,
        "protected_core_mutation_allowed": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
        "schedule_activation_allowed": False,
        "agent_bus_task_write_allowed": False,
        "secret_values_visible": False,
        "canonical_mutation_allowed": False,
    }


def _forge_packet(
    *,
    record_type: str,
    scope: str,
    packet_id: str,
    status: str,
    decision: str,
    request_digest: str,
    marker_field: str,
    consumed: bool = False,
) -> dict[str, Any]:
    return {
        "record_type": record_type,
        "schema_version": "forge.lifecycle-visual-qa.v1",
        "generated_at": "2026-05-20T00:00:00Z",
        "status": status,
        "approval_packet_id": packet_id,
        "request_digest_sha256": request_digest,
        "operator_decision": decision,
        "approval_scope": scope,
        "requested_by": "Codex",
        "extension_id": "ugc-campaign-studio",
        "extension_name": "UGC Campaign Studio",
        "approval_artifact_path": f"07_LOGS/Agent-Activity/_fixture/{packet_id}.json",
        "future_registry_path": "runtime/forge/registry/extensions.json",
        marker_field: f"07_LOGS/Agent-Activity/_forge_lifecycle_visual_qa_markers/{packet_id}.json",
        "future_extension_target_paths": [
            "extensions/ugc-campaign-studio/manifest.json",
            "extensions/ugc-campaign-studio/ui/sidebar.json",
        ],
        "operator_confirmation_text": "APPROVE FORGE LIFECYCLE VISUAL QA ONLY",
        "approved_material": {
            "requested_action": f"request_{packet_id.replace('-', '_')}",
            "extension_id": "ugc-campaign-studio",
            "target_paths": [
                "extensions/ugc-campaign-studio/manifest.json",
                "extensions/ugc-campaign-studio/ui/sidebar.json",
            ],
            "approval_effect": "visual QA fixture only; source-specific Forge executor would still need to revalidate exact approval material before any write.",
        },
        "approval_consumed": consumed,
    }


def _seed_forge_lifecycle_fixture(vault: Path) -> list[dict[str, str]]:
    sandbox_root = vault / SANDBOX_APPROVAL_RELATIVE_DIR
    live_root = vault / LIVE_INSTALL_APPROVAL_RELATIVE_DIR
    rollback_root = vault / ROLLBACK_APPROVAL_RELATIVE_DIR
    sandbox_root.mkdir(parents=True, exist_ok=True)
    live_root.mkdir(parents=True, exist_ok=True)
    rollback_root.mkdir(parents=True, exist_ok=True)

    packets = [
        (
            sandbox_root / "sandbox-pending.json",
            _forge_packet(
                record_type=SANDBOX_APPROVAL_RECORD_TYPE,
                scope=SANDBOX_APPROVAL_SCOPE,
                packet_id="forge-sandbox-pending-visual",
                status="pending_operator_decision",
                decision="pending",
                request_digest="visual-sandbox-pending-digest",
                marker_field="future_exact_once_marker_path",
            ),
        ),
        (
            live_root / "live-approved.json",
            _forge_packet(
                record_type=LIVE_INSTALL_APPROVAL_RECORD_TYPE,
                scope=LIVE_INSTALL_APPROVAL_SCOPE,
                packet_id="forge-live-approved-visual",
                status="approved",
                decision="approved",
                request_digest="visual-live-approved-digest",
                marker_field="future_live_exact_once_marker_path",
            ),
        ),
        (
            rollback_root / "rollback-consumed.json",
            _forge_packet(
                record_type=ROLLBACK_APPROVAL_RECORD_TYPE,
                scope=ROLLBACK_APPROVAL_SCOPE,
                packet_id="forge-rollback-consumed-visual",
                status="consumed",
                decision="approved",
                request_digest="visual-rollback-consumed-digest",
                marker_field="future_rollback_exact_once_marker_path",
                consumed=True,
            ),
        ),
        (
            rollback_root / "rollback-rejected.json",
            _forge_packet(
                record_type=ROLLBACK_APPROVAL_RECORD_TYPE,
                scope=ROLLBACK_APPROVAL_SCOPE,
                packet_id="forge-rollback-rejected-visual",
                status="rejected",
                decision="rejected",
                request_digest="visual-rollback-rejected-digest",
                marker_field="future_rollback_exact_once_marker_path",
            ),
        ),
    ]
    written: list[dict[str, str]] = []
    for path, packet in packets:
        path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
        written.append({"path": _relative_to_vault(vault, path) or str(path), "packet_id": str(packet["approval_packet_id"])})

    invalid_path = rollback_root / "rollback-invalid.json"
    invalid_path.write_text("{not-json", encoding="utf-8")
    written.append({"path": _relative_to_vault(vault, invalid_path) or str(invalid_path), "packet_id": "invalid-json"})
    return written


def _html_shell(styles: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Chaser Forge Approval Center Lifecycle Proof</title>
  <style>
    body {{
      margin: 0;
      padding: 24px;
      background: var(--bg, #0f172a);
      color: var(--text-primary, #f8fafc);
      font-family: Inter, "Segoe UI", Arial, sans-serif;
    }}
    .forge-lifecycle-proof-shell {{
      max-width: 1220px;
      margin: 0 auto;
    }}
    .forge-lifecycle-proof-title {{
      margin: 0 0 14px;
      font-size: 20px;
      font-weight: 800;
      letter-spacing: 0;
    }}
    {styles}
  </style>
</head>
<body>
  <main class="forge-lifecycle-proof-shell" data-proof-surface="chaser-forge-approval-center-lifecycle">
    <h1 class="forge-lifecycle-proof-title">Chaser Forge Approval Center Lifecycle Proof</h1>
    <section id="panel-approval-center" class="panel active" data-panel-id="approval-center" data-panel-status="mounted" data-read-only="true">
      <div class="approval-center-panel">
        <div class="panel-header">
          <div>
            <div class="panel-kicker">Governance</div>
            <h2>Approval Center</h2>
          </div>
          <span id="approval-center-status" class="panel-status-pill">Loading</span>
        </div>
        <div id="approval-center-body"></div>
      </div>
    </section>
  </main>
</body>
</html>
"""


def _write_markdown_report(path: Path, report: dict[str, Any]) -> None:
    evidence = report.get("evidence") or {}
    summary = report.get("summary") or {}
    authority = report.get("authority") or {}
    screenshots = evidence.get("screenshots") or []
    screenshot_lines = [
        f"- {item.get('viewport')}: `{item.get('path')}`"
        for item in screenshots
    ] or ["- not captured"]
    path.write_text(
        "\n".join(
            [
                "# Chaser Forge Approval Center Lifecycle Visual QA",
                "",
                f"- Status: {report.get('status')}",
                f"- Pass: {report.get('pass')}",
                f"- Browser path: {summary.get('browser_path')}",
                f"- Browser fallback reason: {summary.get('browser_fallback_reason')}",
                f"- Source group visible: {summary.get('source_group_visible')}",
                f"- Source-specific decision handoff visible: {summary.get('source_specific_decision_handoff_visible')}",
                f"- Lifecycle tokens visible: {summary.get('lifecycle_tokens_visible')}",
                f"- Screenshot captured: {summary.get('screenshot_captured')}",
                f"- Approval execution allowed: {authority.get('approval_execution_allowed')}",
                f"- Forge execution allowed: {authority.get('forge_live_install_allowed')}",
                f"- Canonical mutation allowed: {authority.get('canonical_mutation_allowed')}",
                f"- HTML artifact: `{evidence.get('html_path')}`",
                f"- JSON report: `{evidence.get('report_path')}`",
                "",
                "## Screenshots",
                "",
                *screenshot_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )


def _capture_with_playwright(
    *,
    html_path: Path,
    app_js: str,
    model: dict[str, Any],
    output_dir: Path,
) -> list[dict[str, Any]]:
    from playwright.sync_api import sync_playwright

    screenshots: list[dict[str, Any]] = []
    viewport_specs = [
        ("desktop", {"width": 1440, "height": 1000}),
        ("mobile", {"width": 390, "height": 900}),
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for name, viewport in viewport_specs:
                console_messages: list[dict[str, str]] = []
                page = browser.new_page(viewport=viewport)
                page.on(
                    "console",
                    lambda msg: console_messages.append({"type": msg.type, "text": msg.text}),
                )
                page.set_content(html_path.read_text(encoding="utf-8"), wait_until="domcontentloaded")
                page.add_script_tag(content=app_js)
                page.evaluate("(payload) => renderApprovalCenterPanel(payload)", model)
                details_summary = page.locator("details.approval-center-tech summary")
                if details_summary.count():
                    details_summary.click()
                body_text = page.locator("#approval-center-body").inner_text(timeout=5_000)
                status_text = page.locator("#approval-center-status").inner_text(timeout=5_000)
                missing_tokens = [token for token in LIFECYCLE_TOKENS if token not in body_text]
                screenshot_path = output_dir / f"{name}-approval-center-forge-lifecycle.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                relevant_console = [
                    item
                    for item in console_messages
                    if item.get("type") in {"error", "warning"}
                ]
                screenshots.append(
                    {
                        "viewport": name,
                        "path": str(screenshot_path),
                        "bytes": screenshot_path.stat().st_size,
                        "status_text": status_text,
                        "body_text_length": len(body_text),
                        "source_group_visible": "Chaser Forge Approval Requests" in body_text,
                        "missing_lifecycle_tokens": missing_tokens,
                        "not_blank": len(body_text) > 200 and screenshot_path.stat().st_size > 10_000,
                        "framework_overlay_detected": any(
                            token in body_text
                            for token in ("ReferenceError", "Traceback", "webpack", "Vite Error", "Next.js")
                        ),
                        "console_messages": relevant_console,
                    }
                )
                page.close()
        finally:
            browser.close()
    return screenshots


def build_chaser_forge_approval_center_lifecycle_visual_qa(
    vault_root: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    capture_screenshots: bool = True,
    screenshot_runner: Callable[..., list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Render and optionally screenshot the Forge lifecycle Approval Center proof."""

    vault = Path(vault_root).resolve() if vault_root is not None else _repo_root()
    output = _resolve_output_dir(vault, output_dir)
    output.mkdir(parents=True, exist_ok=True)
    fixture_vault = output / "_fixture_vault"
    if fixture_vault.exists():
        shutil.rmtree(fixture_vault)
    fixture_vault.mkdir(parents=True)

    generated_at = _now_utc()
    fixture_artifacts = _seed_forge_lifecycle_fixture(fixture_vault)
    model = build_approval_center_panel(fixture_vault)
    forge_group = next((group for group in model.get("source_groups") or [] if group.get("id") == "chaser-forge"), {})

    frontend = _repo_root() / "runtime" / "studio" / "shell" / "frontend"
    styles = (frontend / "styles.css").read_text(encoding="utf-8")
    app_js = (frontend / "app.js").read_text(encoding="utf-8")
    html_path = output / "chaser-forge-approval-center-lifecycle.html"
    html_path.write_text(_html_shell(styles), encoding="utf-8")

    screenshots: list[dict[str, Any]] = []
    screenshot_errors: list[str] = []
    if capture_screenshots:
        try:
            runner = screenshot_runner or _capture_with_playwright
            screenshots = runner(html_path=html_path, app_js=app_js, model=model, output_dir=output)
        except Exception as exc:  # noqa: BLE001
            screenshot_errors.append(str(exc))

    shutil.rmtree(fixture_vault, ignore_errors=True)

    lifecycle_statuses = set((forge_group.get("status_counts") or {}).keys())
    required_statuses = {"pending_operator_review", "approved_pending_execution", "consumed", "rejected", "invalid_packet"}
    screenshot_ok = (
        not capture_screenshots
        or (
            bool(screenshots)
            and all(
                item.get("not_blank")
                and item.get("source_group_visible")
                and not item.get("missing_lifecycle_tokens")
                and not item.get("framework_overlay_detected")
                and not item.get("console_messages")
                for item in screenshots
            )
        )
    )
    blockers: list[str] = []
    if forge_group.get("id") != "chaser-forge":
        blockers.append("chaser_forge_group_missing")
    if not required_statuses.issubset(lifecycle_statuses):
        blockers.append("required_lifecycle_statuses_missing")
    if not forge_group.get("source_specific_decision_handoff_available"):
        blockers.append("source_specific_decision_handoff_missing")
    if not screenshot_ok:
        blockers.append("rendered_screenshot_checks_failed")
    blockers.extend(f"screenshot_error:{item}" for item in screenshot_errors)

    report_path = output / "chaser-forge-approval-center-lifecycle-report.json"
    markdown_path = output / "chaser-forge-approval-center-lifecycle-report.md"
    evidence = {
        "html_path": _relative_to_vault(vault, html_path),
        "report_path": _relative_to_vault(vault, report_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
        "screenshots": [
            {
                **item,
                "path": _relative_to_vault(vault, item.get("path")) or str(item.get("path")),
            }
            for item in screenshots
        ],
        "fixture_vault_persisted": False,
    }
    report: dict[str, Any] = {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if not blockers else "BLOCKED / STATIC UI LIFECYCLE PROOF FAILED",
        "generated_at_utc": generated_at,
        "vault_root": str(vault),
        "flow_under_test": "static Studio Approval Center -> render temporary Forge lifecycle approval fixture -> source group and lifecycle states visible",
        "browser_availability": {
            "browser_plugin_available": True,
            "browser_path_attempted": True,
            "browser_path_blocked": True,
            "browser_path_blocker": "Required Node REPL JavaScript control tool was not exposed after tool discovery.",
            "fallback_used": "playwright_sync_local_static_render",
        },
        "summary": {
            "browser_path": "blocked_browser_plugin_node_repl_unavailable",
            "browser_fallback_reason": "Browser plugin present, but required Node REPL JS tool unavailable; local Playwright static render used.",
            "source_group_visible": forge_group.get("id") == "chaser-forge",
            "source_specific_decision_handoff_visible": bool(forge_group.get("source_specific_decision_handoff_available")),
            "decision_handoff_api_method": forge_group.get("decision_handoff_api_method"),
            "lifecycle_statuses": sorted(lifecycle_statuses),
            "lifecycle_tokens_visible": screenshot_ok if capture_screenshots else required_statuses.issubset(lifecycle_statuses),
            "artifact_count": forge_group.get("artifact_count"),
            "pending_count": forge_group.get("pending_count"),
            "ready_count": forge_group.get("ready_count"),
            "blocked_count": forge_group.get("blocked_count"),
            "screenshot_captured": bool(screenshots),
            "desktop_and_mobile_checked": {item.get("viewport") for item in screenshots} == {"desktop", "mobile"},
            "framework_overlay_detected": any(item.get("framework_overlay_detected") for item in screenshots),
            "console_errors_or_warnings": [
                message
                for item in screenshots
                for message in (item.get("console_messages") or [])
            ],
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "forge_source_group": forge_group,
        "fixture_artifacts": fixture_artifacts,
        "authority": _authority(),
        "evidence": evidence,
        "blocked_reasons": blockers,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    _write_markdown_report(markdown_path, report)
    return report


def format_chaser_forge_approval_center_lifecycle_visual_qa(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    evidence = payload.get("evidence") or {}
    return "\n".join(
        [
            "Chaser Forge Approval Center Lifecycle Visual QA",
            f"  status: {payload.get('status')}",
            f"  ok: {payload.get('ok')}",
            f"  source_group_visible: {summary.get('source_group_visible')}",
            f"  source_specific_decision_handoff_visible: {summary.get('source_specific_decision_handoff_visible')}",
            f"  lifecycle_statuses: {summary.get('lifecycle_statuses')}",
            f"  screenshot_captured: {summary.get('screenshot_captured')}",
            f"  desktop_and_mobile_checked: {summary.get('desktop_and_mobile_checked')}",
            f"  html_path: {evidence.get('html_path')}",
            f"  report_path: {evidence.get('report_path')}",
            f"  next: {summary.get('next_recommended_pass')}",
            "  Boundary: visual proof only; no approval decision, approval consumption, Forge execution, registry mutation, extension-file write/delete, provider/model call, Agent Bus write, or canonical mutation.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Chaser Forge Approval Center lifecycle visual QA proof.")
    parser.add_argument("--vault-root", default=".", help="Vault/repo root.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Proof output directory.")
    parser.add_argument("--no-screenshots", action="store_true", help="Skip Playwright screenshot capture.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()
    report = build_chaser_forge_approval_center_lifecycle_visual_qa(
        args.vault_root,
        output_dir=args.output_dir,
        capture_screenshots=not args.no_screenshots,
    )
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(format_chaser_forge_approval_center_lifecycle_visual_qa(report))


if __name__ == "__main__":
    main()
