"""ChaseOS Excalidraw live browser proof — using in-built browser operator.

Navigates to the known public URL https://excalidraw.com using the ChaseOS
in-built Playwright browser operator. No environment variable configuration
is required for known public targets.

Architecture:
  - Target URL is a hardcoded known constant (excalidraw.com is a well-known
    public app; operators should not need to configure env vars to use it)
  - Uses runtime.operator_surface.adapters.browser_adapter.BrowserAdapter
    (the same Playwright path used by `chaseos operate browser`)
  - Proof: page loads, title matches, canvas element detected, screenshot captured
  - Evidence written to 07_LOGS/Browser-Runs/

Authority:
  - Navigates to https://excalidraw.com only (read-only web navigation)
  - No login, profile, cookies, credentials, CDP raw manipulation
  - No Browser Use CLI invoked
  - No Agent Bus, Gate, canonical mutation
  - Screenshot evidence written to 07_LOGS/Browser-Runs/ only
"""

from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.browser_targets import get_known_browser_target

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    sync_playwright = None  # type: ignore[assignment]
    _PLAYWRIGHT_AVAILABLE = False

EXCALIDRAW_TARGET = get_known_browser_target("excalidraw")
EXCALIDRAW_TARGET_URL = EXCALIDRAW_TARGET.url
EXCALIDRAW_EXPECTED_TITLE_FRAGMENT = "Excalidraw"
EXCALIDRAW_CANVAS_SELECTOR = "canvas"
PROOF_VERSION = "browser.excalidraw_live_browser_proof.v1"
EVIDENCE_DIR = Path("07_LOGS/Browser-Runs")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _playwright_available() -> bool:
    return _PLAYWRIGHT_AVAILABLE


def run_excalidraw_live_browser_proof(
    vault_root: str | Path,
    *,
    headless: bool = True,
    settle_ms: int = 3000,
    write_evidence: bool = True,
    run_slug: str | None = None,
) -> dict[str, Any]:
    """
    Navigate to excalidraw.com using in-built Playwright browser, capture
    screenshot, verify canvas loaded, and write evidence.

    Returns a structured proof result dict.
    Authority: read-only navigation to excalidraw.com; screenshot to 07_LOGS/Browser-Runs/
    """
    vault = Path(vault_root).resolve()
    slug = run_slug or _slug()
    started_at = _now_utc()

    checks: list[dict] = []
    blockers: list[str] = []
    screenshot_path: str | None = None
    page_title: str | None = None
    canvas_found: bool = False
    nav_ok = False

    if not _playwright_available():
        return {
            "ok": False,
            "version": PROOF_VERSION,
            "target_url": EXCALIDRAW_TARGET_URL,
            "started_at": started_at,
            "status": "blocked_playwright_not_available",
            "checks": [],
            "blockers": ["playwright_not_installed"],
            "screenshot_path": None,
            "page_title": None,
            "canvas_found": False,
            "authority": _authority(),
            "note": "Install playwright: pip install playwright && python -m playwright install chromium",
        }

    try:
        evidence_dir = vault / EVIDENCE_DIR
        screenshot_file = evidence_dir / f"excalidraw_live_proof_{slug}.png"

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=headless)
            try:
                ctx = browser.new_context(
                    no_viewport=False,
                    viewport={"width": 1280, "height": 800},
                )
                page = ctx.new_page()

                # Navigate
                nav_error: str | None = None
                try:
                    page.goto(EXCALIDRAW_TARGET_URL, timeout=30000, wait_until="domcontentloaded")
                    nav_ok = True
                except Exception as exc:
                    nav_error = str(exc)

                checks.append({
                    "name": "navigation_succeeded",
                    "ok": nav_ok,
                    "detail": f"goto {EXCALIDRAW_TARGET_URL}" if nav_ok else f"navigation failed: {nav_error}",
                })

                if nav_ok:
                    # Settle
                    try:
                        page.wait_for_timeout(settle_ms)
                    except Exception:
                        pass

                    # Title check
                    try:
                        page_title = page.title()
                        title_ok = EXCALIDRAW_EXPECTED_TITLE_FRAGMENT.lower() in page_title.lower()
                        checks.append({
                            "name": "title_matches_excalidraw",
                            "ok": title_ok,
                            "detail": f"title: {page_title!r}",
                        })
                        if not title_ok:
                            blockers.append(f"unexpected_title: {page_title!r}")
                    except Exception as exc:
                        checks.append({"name": "title_matches_excalidraw", "ok": False, "detail": str(exc)})

                    # Canvas check
                    try:
                        canvas_el = page.query_selector(EXCALIDRAW_CANVAS_SELECTOR)
                        canvas_found = canvas_el is not None
                        checks.append({
                            "name": "canvas_element_present",
                            "ok": canvas_found,
                            "detail": "canvas element detected" if canvas_found else "no canvas found — page may not have fully loaded",
                        })
                    except Exception as exc:
                        checks.append({"name": "canvas_element_present", "ok": False, "detail": str(exc)})

                    # Screenshot
                    if write_evidence:
                        try:
                            evidence_dir.mkdir(parents=True, exist_ok=True)
                            page.screenshot(path=str(screenshot_file), full_page=False)
                            screenshot_path = str(screenshot_file.relative_to(vault))
                            checks.append({
                                "name": "screenshot_captured",
                                "ok": True,
                                "detail": screenshot_path,
                            })
                        except Exception as exc:
                            checks.append({"name": "screenshot_captured", "ok": False, "detail": str(exc)})
            finally:
                browser.close()

    except Exception as exc:
        checks.append({"name": "playwright_session", "ok": False, "detail": traceback.format_exc(limit=5)})
        blockers.append(f"playwright_error: {exc}")

    all_ok = nav_ok and not blockers and all(c["ok"] for c in checks)
    status = (
        "excalidraw_live_browser_proof_complete" if all_ok
        else "excalidraw_live_browser_proof_partial" if nav_ok
        else "excalidraw_live_browser_proof_failed"
    )

    result: dict[str, Any] = {
        "ok": all_ok,
        "version": PROOF_VERSION,
        "target_url": EXCALIDRAW_TARGET_URL,
        "started_at": started_at,
        "completed_at": _now_utc(),
        "status": status,
        "checks": checks,
        "blockers": blockers,
        "screenshot_path": screenshot_path,
        "page_title": page_title,
        "canvas_found": canvas_found,
        "run_slug": slug,
        "authority": _authority(),
    }

    if write_evidence:
        try:
            evidence_dir = vault / EVIDENCE_DIR
            evidence_dir.mkdir(parents=True, exist_ok=True)
            json_path = evidence_dir / f"excalidraw_live_proof_{slug}.json"
            json_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
            result["evidence_json"] = str(json_path.relative_to(vault))
        except Exception:
            pass

    return result


def _authority() -> dict:
    return {
        "navigates_to_excalidraw_com": True,
        "target_hardcoded": False,
        "target_registered_in_chaseos": True,
        "target_registry_id": EXCALIDRAW_TARGET.target_id,
        "env_var_required": False,
        "headless_browser_only": True,
        "no_login_profile_cookies": True,
        "no_cdp_raw_manipulation": True,
        "no_browser_use_cli": True,
        "screenshot_written_to_logs": True,
        "no_vault_markdown_writes": True,
        "no_agent_bus_writes": True,
        "no_gate_mutation": True,
        "no_canonical_mutation": True,
        "no_provider_calls": True,
    }
