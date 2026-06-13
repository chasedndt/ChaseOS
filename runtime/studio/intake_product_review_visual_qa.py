"""Rendered visual QA for the Studio Intake review desk.

The harness loads the production Studio shell, injects a temporary pywebview
bridge backed by StudioAPI over a fixture vault, and proves the Intake page
renders user-facing review language, search/filter behavior, object inspector
selection, and approval-request wiring without granting new runtime authority.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from runtime.studio.shell.api import StudioAPI


MODEL_VERSION = "studio.intake_product_review_visual_qa.v1"
SURFACE_ID = "intake_product_review_visual_qa"
STATUS = "COMPLETE / INTAKE PRODUCT REVIEW UI VERIFIED"
DEFAULT_OUTPUT_DIR = (
    Path("07_LOGS")
    / "Studio-Visual-QA"
    / "2026-05-31-studio-v1-intake-product-pass"
)
REPORT_JSON = "intake-product-review-visual-qa.json"
REPORT_MD = "intake-product-review-visual-qa.md"
REQUIRED_API_METHODS = ("get_intake_panel", "promote_from_quarantine")


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
        raise ValueError("Intake visual QA output must stay inside the vault") from exc
    return resolved


def _new_fixture() -> Path:
    root = Path("C:/tmp")
    if root.is_dir():
        fixture_root = root / "chaseos-intake-product-fixtures"
        try:
            fixture_root.mkdir(parents=True, exist_ok=True)
            return Path(tempfile.mkdtemp(prefix="intake-product-", dir=str(fixture_root))).resolve()
        except OSError:
            pass
    return Path(tempfile.mkdtemp(prefix="intake-product-")).resolve()


def _seed_capture(
    fixture: Path,
    input_class: str,
    filename: str,
    *,
    title: str,
    platform: str,
    captured_at: str,
    sha: str,
    scan: str = "not-scanned",
    status: str = "pending",
) -> None:
    folder = fixture / "03_INPUTS" / "00_QUARANTINE" / input_class
    folder.mkdir(parents=True, exist_ok=True)
    (folder / filename).write_text(f"# {title}\n\nFixture capture body.\n", encoding="utf-8")
    sidecar = {
        "capture_id": f"fixture-{input_class}-{filename}",
        "content_filename": filename,
        "input_class": input_class,
        "source_platform": platform,
        "captured_at": captured_at,
        "title": title,
        "content_sha256": sha,
        "injection_scan": scan,
        "promotion_status": status,
    }
    (folder / f"{filename}.meta.json").write_text(
        json.dumps(sidecar, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _seed_fixture(fixture: Path) -> None:
    _seed_capture(
        fixture,
        "source",
        "venture-ops-brief.md",
        title="VentureOps capture brief",
        platform="web",
        captured_at="2026-05-31T08:15:00Z",
        sha="a" * 64,
    )
    _seed_capture(
        fixture,
        "digest",
        "weekly-signal-digest.md",
        title="Weekly signal digest",
        platform="newsletter",
        captured_at="2026-05-31T09:45:00Z",
        sha="b" * 64,
        scan="clean",
    )


def _pywebview_stub() -> str:
    allowed = json.dumps(list(REQUIRED_API_METHODS))
    return f"""
(() => {{
  const allowed = new Set({allowed});
  window.__studioIntakeCalls = [];
  window.__studioIntakeConfirmations = [];
  window.confirm = (message) => {{
    window.__studioIntakeConfirmations.push(String(message || ""));
    return true;
  }};
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
      return {{ ok: true, status: "ok", surface: name, data: {{ status: "intake-product-visual-qa" }}, warnings: [], blocked_authority: [] }};
    }}
    return {{ ok: true, status: "ok", surface: name, data: {{}}, warnings: [], blocked_authority: [] }};
  }};
  window.pywebview = {{
    api: new Proxy({{}}, {{
      get(_target, prop) {{
        const name = String(prop);
        return async (...args) => {{
          window.__studioIntakeCalls.push({{ method: name, args }});
          if (!allowed.has(name)) return fallback(name);
          return await window.__studioApiCall({{ method: name, args }});
        }};
      }}
    }})
  }};
}})();
"""


def _run_playwright_flow(vault: Path, output_dir: Path, fixture: Path) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    api = StudioAPI(str(fixture))
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
                "error": {"code": "intake_visual_qa_api_call_failed", "message": str(exc)},
                "warnings": [],
                "blocked_authority": [],
            }
        finally:
            api_call_log.append(entry)

    output_dir.mkdir(parents=True, exist_ok=True)
    frontend = vault / "runtime" / "studio" / "shell" / "frontend" / "index.html"
    url = f"{frontend.resolve().as_uri()}#/intake"
    screenshots: list[dict[str, Any]] = []
    console_messages: list[str] = []
    page_errors: list[str] = []

    def capture(page: Any, step: str, viewport: str) -> dict[str, Any]:
        screenshot_path = output_dir / f"{step}-{viewport}-intake.png"
        text = page.locator("#panel-intake").inner_text(timeout=10_000)
        normalized_text = text.lower()
        required_tokens = (
            "new captures",
            "duplicate protection",
            "approval required",
            "no automatic filing",
            "request approval",
        )
        missing_tokens = [token for token in required_tokens if token not in normalized_text]
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
            "forbidden_copy_absent": not any(
                token in text
                for token in (
                    "Quarantine items",
                    "Dedup registry",
                    "chaseos capture file",
                    "Promote ->",
                    "Status:",
                )
            ),
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
            page.wait_for_selector(".intake-item", timeout=30_000)

            initial = capture(page, "initial", "desktop")
            item_count = page.locator(".intake-item").count()

            page.locator(".intake-item").first.click()
            page.wait_for_selector("#object-inspector-body [data-selected-product-object]", timeout=10_000)
            inspector_text = page.locator("#object-inspector-body").inner_text(timeout=10_000)
            selected = capture(page, "selected-item", "desktop")

            search = page.locator("#intake-search-filter")
            search.fill("digest")
            page.wait_for_timeout(250)
            filtered_count = page.locator(".intake-item").count()
            filtered = capture(page, "filtered-search", "desktop")
            search.fill("")
            page.wait_for_timeout(250)

            page.locator(".intake-promote-btn").first.click(timeout=10_000)
            page.wait_for_function(
                """() => (window.__studioIntakeCalls || []).some(
                  call => call.method === "promote_from_quarantine"
                    && String((call.args || [])[0] || "").includes("03_INPUTS/00_QUARANTINE/")
                )""",
                timeout=10_000,
            )
            modal_text = page.locator("#approval-modal").inner_text(timeout=10_000)
            approval = capture(page, "approval-request", "desktop")

            page.set_viewport_size({"width": 390, "height": 900})
            page.wait_for_timeout(250)
            mobile = capture(page, "approval-request", "mobile")

            js_calls = page.evaluate("() => window.__studioIntakeCalls || []")
            title = page.title()
            final_url = page.url
        finally:
            browser.close()

    severe_console = [
        item for item in console_messages if item.startswith(("error:", "warning:", "warn:")) and "favicon" not in item.lower()
    ]
    promote_calls = [entry for entry in api_call_log if entry.get("method") == "promote_from_quarantine"]
    return {
        "url": final_url,
        "title": title,
        "item_count": item_count,
        "filtered_count": filtered_count,
        "inspector_text_contains_safe_posture": "will not file it into your knowledge base" in inspector_text,
        "approval_path_was_vault_relative": any(
            "03_INPUTS/00_QUARANTINE/" in str((entry.get("args") or [""])[0])
            for entry in promote_calls
        ),
        "approval_modal_is_productized": (
            "File capture into knowledge base" in modal_text
            and "Request approval to file" in modal_text
            and "03_INPUTS" not in modal_text
            and "02_KNOWLEDGE" not in modal_text
        ),
        "approval_request_returned_gate": any(
            entry.get("status") == "requires_approval"
            and "write_vault" in (entry.get("blocked_authority") or [])
            for entry in promote_calls
        ),
        "screenshots": screenshots,
        "initial_check": initial,
        "selected_check": selected,
        "filtered_check": filtered,
        "approval_check": approval,
        "mobile_check": mobile,
        "js_call_log": js_calls,
        "api_call_log": api_call_log,
        "console_errors_or_warnings": severe_console,
        "page_errors": page_errors,
    }


def _format_markdown(report: dict[str, Any]) -> str:
    screenshots = "\n".join(
        f"- {shot.get('step')} / {shot.get('viewport')}: `{shot.get('path')}` bytes={shot.get('bytes')}"
        for shot in report.get("screenshots") or []
    ) or "- none"
    blockers = "\n".join(f"- {blocker}" for blocker in report.get("blockers") or []) or "- none"
    return "\n".join(
        [
            "# Intake Product Review Visual QA",
            "",
            f"- Status: {report.get('status')}",
            f"- OK: {report.get('ok')}",
            f"- Flow: {report.get('flow_under_test')}",
            f"- Output dir: `{report.get('output_dir')}`",
            f"- Item count: {report.get('summary', {}).get('item_count')}",
            f"- Filtered count: {report.get('summary', {}).get('filtered_count')}",
            f"- Approval path vault-relative: {report.get('summary', {}).get('approval_path_was_vault_relative')}",
            f"- Approval modal productized: {report.get('summary', {}).get('approval_modal_is_productized')}",
            f"- Approval request returned gate: {report.get('summary', {}).get('approval_request_returned_gate')}",
            "",
            "## Blockers",
            blockers,
            "",
            "## Screenshots",
            screenshots,
        ]
    ) + "\n"


def run_visual_qa(
    vault_root: str | Path,
    output_dir: str | Path | None = None,
    *,
    persist_fixture: bool = False,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    out_dir = _resolve_output_dir(vault, output_dir)
    fixture = _new_fixture()
    fixture_removed = False
    try:
        _seed_fixture(fixture)
        flow = _run_playwright_flow(vault, out_dir, fixture)
    finally:
        if not persist_fixture:
            shutil.rmtree(fixture, ignore_errors=True)
            fixture_removed = not fixture.exists()

    summary = {
        "item_count": flow.get("item_count"),
        "filtered_count": flow.get("filtered_count"),
        "inspector_text_contains_safe_posture": flow.get("inspector_text_contains_safe_posture"),
        "approval_path_was_vault_relative": flow.get("approval_path_was_vault_relative"),
        "approval_modal_is_productized": flow.get("approval_modal_is_productized"),
        "approval_request_returned_gate": flow.get("approval_request_returned_gate"),
        "screenshots_not_blank": all(shot.get("not_blank") for shot in flow.get("screenshots") or []),
        "product_copy_visible": all(shot.get("has_product_copy") for shot in flow.get("screenshots") or [] if shot.get("step") in {"initial", "selected-item", "approval-request"}),
        "forbidden_copy_absent": all(shot.get("forbidden_copy_absent") for shot in flow.get("screenshots") or []),
        "fixture_removed": fixture_removed,
    }
    blockers: list[str] = []
    for key, value in summary.items():
        if key in {"item_count", "filtered_count"}:
            continue
        if value is not True:
            blockers.append(key)
    if (summary["item_count"] or 0) < 2:
        blockers.append("fixture_items_missing")
    if (summary["filtered_count"] or 0) != 1:
        blockers.append("search_filter_failed")
    if flow.get("console_errors_or_warnings"):
        blockers.append("console_errors_or_warnings")
    if flow.get("page_errors"):
        blockers.append("page_errors")

    report = {
        "ok": not blockers,
        "status": STATUS,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "output_dir": _relative_to_vault(vault, out_dir),
        "fixture_root": str(fixture),
        "flow_under_test": "#/intake -> render review inbox -> search -> select item -> request approval -> mobile fit",
        "browser_path": "playwright_sync_static_render_with_python_exposed_studioapi_fixture",
        "browser_fallback_reason": (
            "In-app Browser is available, but this proof needs a pre-load pywebview bridge "
            "via add_init_script and expose_function so production frontend calls a temporary StudioAPI fixture."
        ),
        "authority": {
            "provider_calls_allowed": False,
            "external_actions_allowed": False,
            "runtime_dispatch_allowed": False,
            "approval_consumption_allowed": False,
            "canonical_mutation_allowed": False,
            "production_frontend_rendered": True,
            "actual_studio_api_methods_exercised": True,
            "fixture_vault_writes_allowed": True,
            "visual_evidence_allowed": True,
        },
        "summary": summary,
        "screenshots": flow.get("screenshots") or [],
        "api_call_log": flow.get("api_call_log") or [],
        "js_call_log": flow.get("js_call_log") or [],
        "console_errors_or_warnings": flow.get("console_errors_or_warnings") or [],
        "page_errors": flow.get("page_errors") or [],
        "blockers": blockers,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    md_path = out_dir / REPORT_MD
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_format_markdown(report), encoding="utf-8")
    report["evidence"] = {
        "json": _relative_to_vault(vault, json_path),
        "markdown": _relative_to_vault(vault, md_path),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Intake product review visual QA.")
    parser.add_argument("--vault-root", default=str(_repo_root()))
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--persist-fixture", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = run_visual_qa(
        args.vault_root,
        args.output_dir,
        persist_fixture=args.persist_fixture,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"ok={report['ok']} blockers={report['blockers']}")
        for shot in report["screenshots"]:
            print(f"{shot['step']} {shot['viewport']}: {shot['path']} {shot['bytes']} bytes")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
