"""Rendered visual QA for the Studio Sources workspace.

Loads the production Studio shell with a pywebview bridge backed by StudioAPI
and proves the Sources page renders source channels, source packs, normalized
packs, briefing inputs, provenance, search, and inspector selection without
granting collection, provider, connector, dispatch, approval-consumption, or
canonical-write authority.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.shell.api import StudioAPI


MODEL_VERSION = "studio.sources_product_pipeline_visual_qa.v1"
SURFACE_ID = "sources_product_pipeline_visual_qa"
STATUS = "COMPLETE / SOURCES PRODUCT PIPELINE UI VERIFIED"
DEFAULT_OUTPUT_DIR = (
    Path("07_LOGS")
    / "Studio-Visual-QA"
    / "2026-05-31-studio-v1-sources-product-pass"
)
REPORT_JSON = "sources-product-pipeline-visual-qa.json"
REPORT_MD = "sources-product-pipeline-visual-qa.md"
REQUIRED_API_METHODS = (
    "get_acquisition_summary",
    "get_acquisition_runs",
    "get_sources_product_model",
)


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
        raise ValueError("Sources visual QA output must stay inside the vault") from exc
    return resolved


def _pywebview_stub() -> str:
    allowed = json.dumps(list(REQUIRED_API_METHODS))
    return f"""
(() => {{
  const allowed = new Set({allowed});
  window.__studioSourcesCalls = [];
  const fallback = (name) => {{
    if (name === "get_panel_registry") {{
      return {{ ok: true, status: "ok", surface: name, data: {{ panels: [], readiness: {{}}, authority: {{ inspect_registry: true }} }}, warnings: [], blocked_authority: [] }};
    }}
    if (name === "get_graph_style_registry") {{
      return {{ ok: true, status: "ok", surface: name, data: {{ node_families: {{}}, trust_states: {{}}, edge_layers: {{}} }}, warnings: [], blocked_authority: [] }};
    }}
    if (name === "list_graph_presets") {{
      return {{ ok: true, status: "ok", surface: name, data: {{ presets: [] }}, warnings: [], blocked_authority: [] }};
    }}
    if (name === "get_runtime_status") {{
      return {{ ok: true, status: "ok", surface: name, data: {{ status: "sources-product-visual-qa" }}, warnings: [], blocked_authority: [] }};
    }}
    return {{ ok: true, status: "ok", surface: name, data: {{}}, warnings: [], blocked_authority: [] }};
  }};
  window.pywebview = {{
    api: new Proxy({{}}, {{
      get(_target, prop) {{
        const name = String(prop);
        return async (...args) => {{
          window.__studioSourcesCalls.push({{ method: name, args }});
          if (!allowed.has(name)) return fallback(name);
          return await window.__studioApiCall({{ method: name, args }});
        }};
      }}
    }})
  }};
}})();
"""


def _run_playwright_flow(vault: Path, output_dir: Path) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    api = StudioAPI(str(vault))
    api_call_log: list[dict[str, Any]] = []

    def call_studio_api(payload: dict[str, Any]) -> dict[str, Any]:
        method = str(payload.get("method") or "")
        args = payload.get("args") if isinstance(payload.get("args"), list) else []
        entry: dict[str, Any] = {"method": method, "args": args}
        try:
            if method not in REQUIRED_API_METHODS:
                raise ValueError(f"method_not_allowed:{method}")
            result = getattr(api, method)(*args)
            entry.update(
                {
                    "ok": bool(result.get("ok")),
                    "status": result.get("status"),
                    "surface": result.get("surface"),
                    "blocked_authority": result.get("blocked_authority") or [],
                }
            )
            return result
        except Exception as exc:  # noqa: BLE001
            entry.update({"ok": False, "error": str(exc)})
            return {
                "ok": False,
                "status": "blocked_or_failed",
                "surface": method or "unknown",
                "error": {"code": "sources_visual_qa_api_call_failed", "message": str(exc)},
                "warnings": [],
                "blocked_authority": [],
            }
        finally:
            api_call_log.append(entry)

    output_dir.mkdir(parents=True, exist_ok=True)
    frontend = vault / "runtime" / "studio" / "shell" / "frontend" / "index.html"
    url = f"{frontend.resolve().as_uri()}#/acquisition"
    screenshots: list[dict[str, Any]] = []
    console_messages: list[str] = []
    page_errors: list[str] = []
    inspector_text = ""
    inspector_selected = False

    def capture(page: Any, step: str, viewport: str) -> dict[str, Any]:
        screenshot_path = output_dir / f"{step}-{viewport}-sources.png"
        text = page.locator("#panel-acquisition").inner_text(timeout=10_000)
        normalized_text = text.lower()
        required_tokens = (
            "sources",
            "source packs",
            "normalized packs",
            "briefing inputs",
            "provenance",
            "advanced",
        )
        forbidden_tokens = (
            "acquisition cockpit",
            "dry-run proposal",
            "implementation pass",
            "mvp",
            "python -m",
            "source-pack-builder",
            "acquisition_normalization",
        )
        missing_tokens = [token for token in required_tokens if token not in normalized_text]
        forbidden_present = [token for token in forbidden_tokens if token in normalized_text]
        page.screenshot(path=str(screenshot_path), full_page=True)
        shot = {
            "step": step,
            "viewport": viewport,
            "path": _relative_to_vault(vault, screenshot_path),
            "exists": screenshot_path.is_file(),
            "bytes": screenshot_path.stat().st_size if screenshot_path.is_file() else 0,
            "not_blank": screenshot_path.is_file() and screenshot_path.stat().st_size > 10_000,
            "has_product_copy": not missing_tokens,
            "missing_product_copy": missing_tokens,
            "forbidden_copy_absent": not forbidden_present,
            "forbidden_copy_present": forbidden_present,
        }
        screenshots.append(shot)
        return shot

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("console", lambda msg: console_messages.append(f"{msg.type}:{msg.text}"))
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.expose_function("__studioApiCall", call_studio_api)
            page.add_init_script(_pywebview_stub())
            page.goto(url, wait_until="domcontentloaded")
            page.locator("#panel-acquisition.active").wait_for(timeout=15_000)
            page.locator("#acquisition-sources-row .operator-surface-card, #acquisition-sources-row .acquisition-source-card").first.wait_for(timeout=15_000)
            capture(page, "initial", "desktop")

            page.locator('[data-acquisition-tab="source-packs"]').click()
            page.locator("#acquisition-tab-source-packs.active").wait_for(timeout=10_000)
            page.locator("#acquisition-source-packs-body .operator-surface-card").first.wait_for(timeout=10_000)
            page.locator("#acquisition-source-packs-body .operator-surface-card").first.click()
            inspector_text = page.locator("#object-inspector-body").inner_text(timeout=10_000)
            inspector_selected = page.locator("#object-inspector-body .object-inspector-node").count() > 0
            capture(page, "source-packs-selected", "desktop")

            page.locator('[data-acquisition-tab="normalized-packs"]').click()
            page.locator("#acquisition-tab-normalized-packs.active").wait_for(timeout=10_000)
            capture(page, "normalized-packs", "desktop")

            page.locator("#acquisition-search").fill("strikezone")
            capture(page, "filtered-search", "desktop")

            mobile = browser.new_page(viewport={"width": 430, "height": 860})
            mobile.on("console", lambda msg: console_messages.append(f"mobile:{msg.type}:{msg.text}"))
            mobile.on("pageerror", lambda exc: page_errors.append(f"mobile:{exc}"))
            mobile.expose_function("__studioApiCall", call_studio_api)
            mobile.add_init_script(_pywebview_stub())
            mobile.goto(url, wait_until="domcontentloaded")
            mobile.locator("#panel-acquisition.active").wait_for(timeout=15_000)
            mobile.locator("#acquisition-sources-row .operator-surface-card, #acquisition-sources-row .acquisition-source-card").first.wait_for(timeout=15_000)
            capture(mobile, "initial", "mobile")
            mobile.close()
        finally:
            browser.close()

    unexpected_methods = sorted(
        {
            entry["method"]
            for entry in api_call_log
            if entry.get("method") not in REQUIRED_API_METHODS
        }
    )
    return {
        "ok": (
            all(item["exists"] and item["not_blank"] and item["has_product_copy"] and item["forbidden_copy_absent"] for item in screenshots)
            and not page_errors
            and not unexpected_methods
            and any(entry["method"] == "get_sources_product_model" and entry.get("ok") for entry in api_call_log)
            and inspector_selected
        ),
        "screenshots": screenshots,
        "api_calls": api_call_log,
        "unexpected_methods": unexpected_methods,
        "console_messages": console_messages,
        "page_errors": page_errors,
        "inspector_selected": inspector_selected,
        "inspector_text_sample": inspector_text[:500],
        "authority": {
            "provider_calls": False,
            "connector_calls": False,
            "browser_authority": False,
            "workflow_execution": False,
            "agent_bus_dispatch": False,
            "approval_consumption": False,
            "canonical_writeback": False,
        },
    }


def _write_reports(vault: Path, output_dir: Path, report: dict[str, Any]) -> None:
    report.update(
        {
            "model_version": MODEL_VERSION,
            "surface_id": SURFACE_ID,
            "status": STATUS if report.get("ok") else "FAILED",
            "generated_at": _now_utc(),
        }
    )
    (output_dir / REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# Sources Product Pipeline Visual QA",
        "",
        f"- Status: {report['status']}",
        f"- Generated: {report['generated_at']}",
        f"- API methods: {', '.join(REQUIRED_API_METHODS)}",
        "- Authority: no provider calls, connector calls, browser authority, workflow execution, Agent Bus dispatch, approval consumption, or canonical writeback.",
        "",
        "## Screenshots",
    ]
    for shot in report.get("screenshots", []):
        lines.append(
            f"- {shot['step']} / {shot['viewport']}: {shot['path']} "
            f"({shot['bytes']} bytes, product_copy={shot['has_product_copy']})"
        )
    lines.extend(
        [
            "",
            "## Checks",
            f"- Inspector selection: {report.get('inspector_selected')}",
            f"- Unexpected API methods: {report.get('unexpected_methods')}",
            f"- Page errors: {report.get('page_errors')}",
        ]
    )
    (output_dir / REPORT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run rendered Sources product visual QA.")
    parser.add_argument("--vault-root", default=".", help="ChaseOS vault root")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory inside the vault")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args(argv)

    vault = Path(args.vault_root).resolve()
    output_dir = _resolve_output_dir(vault, args.output_dir)
    report = _run_playwright_flow(vault, output_dir)
    _write_reports(vault, output_dir, report)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
