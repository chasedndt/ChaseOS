"""Render Capture to Markdown output files and save screenshot proof."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


DEFAULT_OUTPUT_DIR = (
    "07_LOGS/Studio-Visual-QA/"
    "2026-05-27-markdown-capture-real-chain-output-proof"
)


def render_markdown_output_proof(
    *,
    vault_root: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    inputs: list[tuple[str, str, str]],
    viewport_width: int = 1280,
    viewport_height: int = 900,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    target_dir = _resolve_under_vault(vault, output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    rendered: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(
            viewport={"width": viewport_width, "height": viewport_height}
        )
        for label, rel_path, slug in inputs:
            source_path = _resolve_under_vault(vault, rel_path)
            markdown = source_path.read_text(encoding="utf-8", errors="replace")
            html_path = target_dir / f"{slug}.html"
            screenshot_path = target_dir / f"{slug}.png"
            html_path.write_text(
                _page_html(label=label, rel_path=rel_path, markdown=markdown),
                encoding="utf-8",
            )
            page.goto(html_path.as_uri(), wait_until="load")
            page.screenshot(path=str(screenshot_path), full_page=True)
            rendered.append(
                {
                    "label": label,
                    "source_markdown_path": rel_path,
                    "rendered_html_path": _rel(html_path, vault),
                    "screenshot_path": _rel(screenshot_path, vault),
                    "screenshot_size_bytes": screenshot_path.stat().st_size,
                }
            )
        browser.close()

    return {
        "ok": all(item["screenshot_size_bytes"] > 0 for item in rendered),
        "status": "markdown_output_visual_proof_created",
        "output_dir": _rel(target_dir, vault),
        "viewport": {"width": viewport_width, "height": viewport_height},
        "rendered": rendered,
    }


def _page_html(*, label: str, rel_path: str, markdown: str) -> str:
    escaped_label = html.escape(label)
    escaped_path = html.escape(rel_path)
    escaped_markdown = html.escape(markdown)
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{escaped_label}</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: #f4f1ec;
    color: #1f2933;
    font: 15px/1.5 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }}
  main {{
    max-width: 1080px;
    margin: 0 auto;
    padding: 32px 28px 48px;
  }}
  header {{
    border-bottom: 1px solid #c8d1d8;
    margin-bottom: 20px;
    padding-bottom: 16px;
  }}
  h1 {{
    font-size: 30px;
    line-height: 1.15;
    margin: 0 0 8px;
    letter-spacing: 0;
  }}
  .path {{
    color: #46545f;
    font: 13px/1.45 ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
    overflow-wrap: anywhere;
  }}
  pre {{
    margin: 0;
    padding: 22px;
    background: #ffffff;
    border: 1px solid #c8d1d8;
    border-radius: 6px;
    box-shadow: 0 1px 2px rgba(31, 41, 51, 0.08);
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    font: 13px/1.55 ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
  }}
</style>
</head>
<body>
<main>
<header>
<h1>{escaped_label}</h1>
<div class="path">{escaped_path}</div>
</header>
<pre>{escaped_markdown}</pre>
</main>
</body>
</html>
"""


def _parse_input(value: str) -> tuple[str, str, str]:
    parts = value.split("|")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            "--input must use the format 'Label|relative/path.md|slug'"
        )
    label, rel_path, slug = (part.strip() for part in parts)
    if not label or not rel_path or not slug:
        raise argparse.ArgumentTypeError(
            "--input label, relative path, and slug must all be non-empty"
        )
    return label, rel_path, slug


def _resolve_under_vault(vault: Path, path_value: str | Path) -> Path:
    raw = Path(path_value)
    path = raw if raw.is_absolute() else vault / raw
    resolved = path.resolve()
    try:
        resolved.relative_to(vault)
    except ValueError as exc:
        raise ValueError(f"path must stay inside vault root: {path_value}") from exc
    return resolved


def _rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render generated Markdown outputs and save screenshot proof."
    )
    parser.add_argument("--vault-root", default=".")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--input",
        action="append",
        type=_parse_input,
        required=True,
        help="Format: 'Label|relative/path.md|slug'",
    )
    parser.add_argument("--viewport-width", type=int, default=1280)
    parser.add_argument("--viewport-height", type=int, default=900)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = render_markdown_output_proof(
        vault_root=args.vault_root,
        output_dir=args.output_dir,
        inputs=args.input,
        viewport_width=args.viewport_width,
        viewport_height=args.viewport_height,
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"{result['status']}: {result['output_dir']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
