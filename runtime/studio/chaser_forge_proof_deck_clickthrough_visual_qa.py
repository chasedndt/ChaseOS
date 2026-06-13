"""Static Studio clickthrough proof for the Chaser Forge proof-deck section.

The harness loads the production Studio shell frontend with a pywebview API
stub, routes to Chaser Forge, and verifies that the read-only proof-deck
section renders. It writes visual QA evidence only.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
from typing import Any, Callable

from runtime.forge.panel import build_chaser_forge_panel


MODEL_VERSION = "studio.chaser_forge_proof_deck_clickthrough_visual_qa.v2"
SURFACE_ID = "chaser_forge_proof_deck_clickthrough_visual_qa"
PASS_ID = "chaser-forge-marketplace-proof-deck-studio-clickthrough"
DEFAULT_OUTPUT_DIR = Path("07_LOGS") / "Studio-Visual-QA" / "2026-05-21-chaser-forge-marketplace-proof-deck-clickthrough"

REQUIRED_TOKENS = (
    "Chaser Forge",
    "Proof Deck",
    "COMPLETE / PROOF DECK READY",
    "07_LOGS/Workflow-Proofs/2026-05-21_chaser-forge-marketplace-proof-deck.md",
    "Marketplace Publish And Install",
    "remote-distribution-only-if-authorized-or-select-next-chaseos-feature-family",
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
        raise ValueError("Chaser Forge proof-deck clickthrough output must stay inside the vault workspace") from exc
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
        "proof_deck_log_artifact_write_allowed": False,
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
        "secret_or_credential_read_allowed": False,
        "pulse_memory_mutation_allowed": False,
        "personal_map_mutation_allowed": False,
        "rnd_truth_state_mutation_allowed": False,
        "canonical_mutation_allowed": False,
    }


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


def _run_playwright_clickthrough(vault: Path, output_dir: Path, panel_data: dict[str, Any]) -> dict[str, Any]:
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
                page.wait_for_selector('[data-proof-deck-surface="chaser-forge-proof-deck"]', timeout=7000)
                text = page.locator("#panel-chaser-forge").inner_text(timeout=3000)
                normalized_text = text.lower()
                screenshot_path = output_dir / f"{viewport_name}-chaser-forge-proof-deck-clickthrough.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                missing = [token for token in REQUIRED_TOKENS if token.lower() not in normalized_text]
                screenshots.append(
                    {
                        "viewport": viewport_name,
                        "path": _relative_to_vault(vault, screenshot_path),
                        "exists": screenshot_path.is_file(),
                        "bytes": screenshot_path.stat().st_size if screenshot_path.is_file() else 0,
                        "not_blank": screenshot_path.is_file() and screenshot_path.stat().st_size > 1024,
                        "proof_deck_section_visible": "proof deck" in normalized_text,
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
    screenshot_lines = "\n".join(
        f"- {shot['viewport']}: `{shot['path']}` bytes={shot['bytes']} proof_deck_section_visible={shot['proof_deck_section_visible']}"
        for shot in report.get("screenshots", [])
    )
    blocker_lines = "\n".join(f"- {escape(str(blocker))}" for blocker in report.get("blockers", [])) or "- none"
    return "\n".join(
        [
            "# Chaser Forge Proof Deck Studio Clickthrough Visual QA",
            "",
            f"- Status: {report.get('status')}",
            f"- OK: {report.get('ok')}",
            f"- Surface: {report.get('surface')}",
            f"- Proof deck status: {report.get('proof_deck_status')}",
            f"- Markdown path: `{report.get('proof_deck_markdown_path')}`",
            f"- JSON path: `{report.get('proof_deck_json_path')}`",
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


def build_chaser_forge_proof_deck_clickthrough_visual_qa(
    vault_root: str | Path,
    *,
    output_dir: str | Path | None = None,
    screenshot_runner: Callable[[Path, Path, dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    resolved_output_dir = _resolve_output_dir(vault, output_dir)
    panel = build_chaser_forge_panel(vault)
    proof_deck = panel.get("proof_deck") if isinstance(panel.get("proof_deck"), dict) else {}
    runner = screenshot_runner or _run_playwright_clickthrough
    visual = runner(vault, resolved_output_dir, panel)
    screenshots = visual.get("screenshots") if isinstance(visual.get("screenshots"), list) else []
    missing_tokens = sorted(
        {
            token
            for screenshot in screenshots
            for token in (screenshot.get("missing_required_tokens") or [])
        }
    )
    blockers: list[str] = []
    if not proof_deck.get("ok"):
        blockers.append("proof_deck_not_ready")
    if missing_tokens:
        blockers.extend(f"missing_required_token:{token}" for token in missing_tokens)
    if not screenshots:
        blockers.append("no_screenshots_captured")
    if any(not shot.get("proof_deck_section_visible") for shot in screenshots):
        blockers.append("proof_deck_section_not_visible")
    if any(not shot.get("not_blank") for shot in screenshots):
        blockers.append("blank_or_tiny_screenshot")
    if visual.get("console_errors_or_warnings"):
        blockers.append("console_errors_or_warnings_present")
    if visual.get("page_errors"):
        blockers.append("page_errors_present")

    report = {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "schema_version": MODEL_VERSION,
        "pass_id": PASS_ID,
        "status": "COMPLETE / MARKETPLACE PROOF DECK STUDIO CLICKTHROUGH VERIFIED" if not blockers else "BLOCKED",
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "output_dir": _relative_to_vault(vault, resolved_output_dir),
        "proof_deck_status": proof_deck.get("status"),
        "proof_deck_markdown_path": proof_deck.get("markdown_path"),
        "proof_deck_json_path": proof_deck.get("json_path"),
        "proof_deck_read_only": proof_deck.get("read_only"),
        "screenshots": screenshots,
        "console_errors_or_warnings": visual.get("console_errors_or_warnings") or [],
        "page_errors": visual.get("page_errors") or [],
        "required_tokens": list(REQUIRED_TOKENS),
        "missing_required_tokens": missing_tokens,
        "authority": _authority(),
        "blockers": blockers,
        "next_recommended_pass": "remote-distribution-only-if-authorized-or-select-next-chaseos-feature-family",
    }

    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    json_path = resolved_output_dir / "chaser-forge-proof-deck-clickthrough-report.json"
    md_path = resolved_output_dir / "chaser-forge-proof-deck-clickthrough-report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    md_path.write_text(_format_markdown(report), encoding="utf-8")
    report["report_path"] = _relative_to_vault(vault, json_path)
    report["markdown_report_path"] = _relative_to_vault(vault, md_path)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Chaser Forge proof-deck Studio clickthrough visual QA.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--output-dir", default=None, help="Optional output directory inside the vault.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args(argv)
    report = build_chaser_forge_proof_deck_clickthrough_visual_qa(
        args.vault_root,
        output_dir=args.output_dir,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(_format_markdown(report))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
