"""Local visual QA for the Chat WML deeplink selector.

This harness renders the production Chat panel frontend with a mocked pywebview
contract payload. It performs no provider calls, no browser dispatch from
ChaseOS, no approval consumption, and no vault mutation beyond the proof files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_panel_contract import build_phase11_chat_panel_contract


DEFAULT_OUTPUT_DIR = Path("07_LOGS/Studio-Visual-QA/2026-05-14-workspace-mode-chat-deeplink-selector")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _html(styles: str) -> str:
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{
      --bg: #0f172a;
      --bg-deep: #0b1120;
      --bg-surface: #111827;
      --bg-raised: #172033;
      --border: #334155;
      --border-subtle: #263244;
      --text: #f8fafc;
      --text-primary: #f8fafc;
      --text-secondary: #cbd5e1;
      --text-muted: #94a3b8;
      --accent: #2dd4bf;
      --accent-hover: #5eead4;
      --ts-disputed: #f87171;
    }}
    body {{
      margin: 0;
      padding: 24px;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .visual-qa-shell {{
      max-width: 1180px;
      margin: 0 auto;
    }}
    .visual-qa-title {{
      margin: 0 0 12px;
      font-size: 18px;
      font-weight: 800;
    }}
    {styles}
  </style>
</head>
<body>
  <main class="visual-qa-shell">
    <h1 class="visual-qa-title">ChaseOS Chat - Workspace Mode Studio</h1>
    <div id="chat-status"></div>
    <div id="chat-provider-readiness"></div>
    <div id="chat-preview-body"></div>
  </main>
</body>
</html>"""


def build_workspace_mode_chat_deeplink_visual_qa(
    vault_root: str | Path | None = None,
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    """Render desktop/mobile screenshots of the Chat WML selector."""

    root = Path(vault_root).resolve() if vault_root else _repo_root()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    contract = build_phase11_chat_panel_contract(root, message="/dashboard")
    frontend = root / "runtime/studio/shell/frontend"
    styles = (frontend / "styles.css").read_text(encoding="utf-8")
    app_js = (frontend / "app.js").read_text(encoding="utf-8")

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
                page = browser.new_page(viewport=viewport)
                page.set_content(_html(styles), wait_until="domcontentloaded")
                page.add_script_tag(content=app_js)
                page.evaluate("(payload) => renderPhase11ChatPanel(payload)", contract)
                page.wait_for_selector(".phase11-chat-workspace-mode-selector", state="visible", timeout=10_000)
                selector_count = page.locator(".phase11-chat-workspace-mode-selector").count()
                card_count = page.locator(".phase11-chat-workspace-mode-card").count()
                founder_count = page.locator('.phase11-chat-workspace-mode-card[data-mode="founder_venture"]').count()
                link_count = page.locator(".phase11-chat-workspace-mode-link").count()
                screenshot_path = output / f"{name}-chat-wml-selector.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                screenshots.append(
                    {
                        "viewport": name,
                        "path": str(screenshot_path),
                        "bytes": screenshot_path.stat().st_size,
                        "selector_visible": selector_count == 1,
                        "card_count": card_count,
                        "founder_venture_card_visible": founder_count == 1,
                        "link_count": link_count,
                    }
                )
                page.close()
        finally:
            browser.close()

    report = {
        "ok": all(
            item["selector_visible"]
            and item["card_count"] >= 6
            and item["founder_venture_card_visible"]
            and item["link_count"] >= 6
            and item["bytes"] > 10_000
            for item in screenshots
        ),
        "surface": "workspace_mode_chat_deeplink_visual_qa",
        "read_only": True,
        "contract_card_count": (contract.get("workspace_mode_deeplink_selector") or {}).get("card_count"),
        "screenshots": screenshots,
        "authority": {
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_dispatch_from_chat_allowed": False,
            "workspace_mode_execution_allowed": False,
            "workspace_mode_profile_write_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }
    report_path = output / "visual-qa-report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["report_path"] = str(report_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Chat WML deeplink selector visual QA screenshots.")
    parser.add_argument("--vault-root", default=".", help="Vault/repo root.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Proof output directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()
    report = build_workspace_mode_chat_deeplink_visual_qa(args.vault_root, output_dir=args.output_dir)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"ok={report['ok']} report={report['report_path']}")


if __name__ == "__main__":
    main()
