"""Approval-consuming public Excalidraw drawing proof runner.

This module runs one bounded, no-login browser-only drawing proof against the
known public Excalidraw target. It requires a written approval packet from
``excalidraw_public_drawing_approval``, reserves the exact-once marker before
browser launch, draws one rectangle and one approved text label through
Playwright mouse/keyboard actions, and writes evidence.

It does not use Browser Use CLI, real browser profiles, credentials, cookies,
MCP, providers, Agent Bus, Gate mutation, trusted skill writes, skill
activation, or canonical ChaseOS writeback.
"""

from __future__ import annotations

import argparse
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.browser_targets import get_known_browser_target
from runtime.browser_runtime.excalidraw_public_drawing_approval import (
    APPROVAL_RELATIVE_DIR,
    EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_RECORD_TYPE,
    EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_VERSION,
    EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_WRITTEN,
    IDEMPOTENCY_MARKER_RELATIVE_DIR,
)

try:
    from playwright.sync_api import sync_playwright

    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    sync_playwright = None  # type: ignore[assignment]
    _PLAYWRIGHT_AVAILABLE = False


EXCALIDRAW_PUBLIC_DRAWING_PROOF_RECORD_TYPE = "excalidraw_public_browser_drawing_proof_run"
EXCALIDRAW_PUBLIC_DRAWING_PROOF_VERSION = "browser.excalidraw_public_drawing_proof.v1"
EXCALIDRAW_PUBLIC_DRAWING_PROOF_COMPLETE = "excalidraw_public_browser_drawing_proof_complete"
EXCALIDRAW_PUBLIC_DRAWING_PROOF_FAILED = "excalidraw_public_browser_drawing_proof_failed"
EXCALIDRAW_PUBLIC_DRAWING_PROOF_BLOCKED = "blocked_excalidraw_public_browser_drawing_proof"

EVIDENCE_DIR = Path("07_LOGS/Browser-Runs")
AGENT_ACTIVITY_EVIDENCE_DIR = Path("07_LOGS/Agent-Activity/_excalidraw_public_drawing_runs")
EXCALIDRAW_CANVAS_SELECTOR = "canvas"
EXCALIDRAW_EXPECTED_TITLE_FRAGMENT = "Excalidraw"

FORBIDDEN_FALSE_FLAGS = (
    "mcp_invocation_attempted",
    "mcp_tool_call_attempted",
    "draft_skill_written",
    "untrusted_candidate_written",
    "trusted_skill_write_attempted",
    "skill_activation_attempted",
    "real_profile_access_attempted",
    "credential_or_cookie_read_attempted",
    "cookie_export_attempted",
    "browser_profile_sync_attempted",
    "browser_history_import_attempted",
    "public_tunnel_attempted",
    "browser_harness_used",
    "browser_use_cli_live_used",
    "workflow_use_code_copied",
    "shell_execution_from_browser_runtime_attempted",
    "agent_bus_enqueue_attempted",
    "provider_call_attempted",
    "gate_mutation_attempted",
    "canonical_writeback_attempted",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _relative_or_posix(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_relative_path(vault: Path, relative_path: str, base_relative: Path) -> Path:
    base = (vault / base_relative).resolve()
    path = (vault / relative_path).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Path escapes expected base directory: {path}") from exc
    return path


def _approval_payload_ok(vault: Path, payload: dict[str, Any]) -> bool:
    target = get_known_browser_target("excalidraw")
    return (
        payload.get("record_type") == EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_RECORD_TYPE
        and payload.get("schema_version") == EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_VERSION
        and payload.get("status") == EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_WRITTEN
        and payload.get("target_registry_id") == target.target_id
        and payload.get("target_url") == target.url
        and payload.get("approval_artifact_written") is True
        and payload.get("future_single_run_approved") is True
        and payload.get("execution_allowed_in_this_pass") is False
        and bool(payload.get("approval_id"))
        and bool(payload.get("request_digest_sha256"))
        and bool(payload.get("source_reachability_evidence_path"))
        and (vault / str(payload.get("source_reachability_evidence_path"))).exists()
        and bool(payload.get("idempotency_marker_path"))
        and not payload.get("blockers")
    )


def _load_approval(vault: Path, approval_id: str = "") -> tuple[str, dict[str, Any] | None]:
    if approval_id:
        path = (vault / APPROVAL_RELATIVE_DIR / f"{approval_id}.json").resolve()
        payload = _read_json(path)
        if payload is not None and _approval_payload_ok(vault, payload):
            return _relative_or_posix(vault, path), payload
        return _relative_or_posix(vault, path), None

    candidates = sorted(
        (vault / APPROVAL_RELATIVE_DIR).glob("*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        payload = _read_json(path)
        if payload is not None and _approval_payload_ok(vault, payload):
            return _relative_or_posix(vault, path), payload
    return "", None


def _approval_label(payload: dict[str, Any]) -> str:
    request = payload.get("request")
    label = request.get("drawing_label") if isinstance(request, dict) else ""
    return str(label or "ChaseOS proof")


def _marker_payload(
    *,
    approval: dict[str, Any],
    run_slug: str,
    status: str,
    evidence_json_path: str = "",
    screenshot_path: str = "",
    reserved_at: str | None = None,
    completed_at: str | None = None,
) -> dict[str, Any]:
    return {
        "record_type": "excalidraw_public_browser_drawing_proof_marker",
        "schema_version": EXCALIDRAW_PUBLIC_DRAWING_PROOF_VERSION,
        "approval_id": approval.get("approval_id"),
        "request_digest_sha256": approval.get("request_digest_sha256"),
        "run_slug": run_slug,
        "status": status,
        "reserved_at": reserved_at or _now_utc(),
        "completed_at": completed_at,
        "evidence_json_path": evidence_json_path,
        "screenshot_path": screenshot_path,
    }


def _reserve_marker(vault: Path, approval: dict[str, Any], run_slug: str) -> tuple[str, Path]:
    marker_relative = str(approval.get("idempotency_marker_path") or "")
    marker_path = _safe_relative_path(vault, marker_relative, IDEMPOTENCY_MARKER_RELATIVE_DIR)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    payload = _marker_payload(approval=approval, run_slug=run_slug, status="reserved")
    with marker_path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return _relative_or_posix(vault, marker_path), marker_path


def _update_marker(
    marker_path: Path,
    *,
    approval: dict[str, Any],
    run_slug: str,
    status: str,
    evidence_json_path: str,
    screenshot_path: str,
) -> None:
    existing = _read_json(marker_path) or {}
    payload = _marker_payload(
        approval=approval,
        run_slug=run_slug,
        status=status,
        evidence_json_path=evidence_json_path,
        screenshot_path=screenshot_path,
        reserved_at=str(existing.get("reserved_at") or _now_utc()),
        completed_at=_now_utc(),
    )
    marker_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _largest_canvas_box(page: Any) -> dict[str, float] | None:
    canvases = page.query_selector_all(EXCALIDRAW_CANVAS_SELECTOR)
    best_box: dict[str, float] | None = None
    best_area = 0.0
    for canvas in canvases:
        box = canvas.bounding_box()
        if not box:
            continue
        area = float(box.get("width", 0)) * float(box.get("height", 0))
        if area > best_area:
            best_area = area
            best_box = {
                "x": float(box.get("x", 0)),
                "y": float(box.get("y", 0)),
                "width": float(box.get("width", 0)),
                "height": float(box.get("height", 0)),
            }
    return best_box


def _draw_rectangle_and_label(page: Any, box: dict[str, float], label: str) -> None:
    left = box["x"] + box["width"] * 0.42
    top = box["y"] + box["height"] * 0.42
    right = box["x"] + box["width"] * 0.58
    bottom = box["y"] + box["height"] * 0.56
    center_x = box["x"] + box["width"] * 0.5
    center_y = box["y"] + box["height"] * 0.5

    page.mouse.click(center_x, center_y)
    page.keyboard.press("2")
    page.wait_for_timeout(250)
    page.mouse.move(left, top)
    page.mouse.down()
    page.mouse.move(right, bottom, steps=10)
    page.mouse.up()
    page.wait_for_timeout(450)

    page.keyboard.press("8")
    page.wait_for_timeout(250)
    page.mouse.click(left, bottom + 36)
    page.keyboard.type(label, delay=20)
    page.wait_for_timeout(700)
    page.keyboard.press("Escape")


def _storage_observation(page: Any, label: str) -> dict[str, Any]:
    try:
        return page.evaluate(
            """(label) => {
                const keys = Object.keys(window.localStorage || {});
                const values = keys.map((key) => String(window.localStorage.getItem(key) || ""));
                return {
                    local_storage_key_count: keys.length,
                    local_storage_keys: keys.slice(0, 20),
                    contains_label: values.some((value) => value.includes(label)),
                    contains_rectangle: values.some((value) => value.includes("rectangle")),
                };
            }""",
            label,
        )
    except Exception as exc:
        return {
            "local_storage_key_count": 0,
            "local_storage_keys": [],
            "contains_label": False,
            "contains_rectangle": False,
            "error": str(exc),
        }


def _authority() -> dict[str, bool | str]:
    target = get_known_browser_target("excalidraw")
    return {
        "target_registered_in_chaseos": True,
        "target_registry_id": target.target_id,
        "target_url": target.url,
        "allowed_domain": "excalidraw.com",
        "throwaway_browser_context_only": True,
        "no_login_profile_cookies": True,
        "no_real_profile": True,
        "no_credentials": True,
        "no_cookie_export": True,
        "no_browser_use_cli": True,
        "no_mcp_invocation": True,
        "no_provider_calls": True,
        "no_agent_bus_writes": True,
        "no_gate_mutation": True,
        "no_trusted_skill_write": True,
        "no_skill_activation": True,
        "no_canonical_mutation": True,
    }


def _base_result(
    *,
    generated_at: str,
    run_slug: str,
    approval_path: str,
    approval: dict[str, Any] | None,
    status: str,
    blockers: list[str],
    checks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    target = get_known_browser_target("excalidraw")
    return {
        "ok": False,
        "record_type": EXCALIDRAW_PUBLIC_DRAWING_PROOF_RECORD_TYPE,
        "schema_version": EXCALIDRAW_PUBLIC_DRAWING_PROOF_VERSION,
        "generated_at": generated_at,
        "completed_at": None,
        "status": status,
        "run_slug": run_slug,
        "approval_artifact_path": approval_path,
        "approval_id": approval.get("approval_id") if approval else "",
        "request_digest_sha256": approval.get("request_digest_sha256") if approval else "",
        "source_reachability_evidence_path": (
            approval.get("source_reachability_evidence_path") if approval else ""
        ),
        "idempotency_marker_path": approval.get("idempotency_marker_path") if approval else "",
        "target_registry_id": target.target_id,
        "target_url": target.url,
        "drawing_label": _approval_label(approval) if approval else "",
        "checks": checks or [],
        "blockers": blockers,
        "screenshot_path": "",
        "evidence_json_path": "",
        "agent_activity_evidence_path": "",
        "page_title": None,
        "canvas_found": False,
        "canvas_box": None,
        "visual_change_after_actions": False,
        "local_storage_observation": {},
        "authority": _authority(),
        "browser_launch_attempted": False,
        "target_navigation_attempted": False,
        "drawing_action_attempted": False,
        "rectangle_action_attempted": False,
        "text_action_attempted": False,
        "screenshot_attempted": False,
        "browser_run_log_written": False,
        "agent_activity_log_written": False,
        "mcp_invocation_attempted": False,
        "mcp_tool_call_attempted": False,
        "draft_skill_written": False,
        "untrusted_candidate_written": False,
        "trusted_skill_write_attempted": False,
        "skill_activation_attempted": False,
        "real_profile_access_attempted": False,
        "credential_or_cookie_read_attempted": False,
        "cookie_export_attempted": False,
        "browser_profile_sync_attempted": False,
        "browser_history_import_attempted": False,
        "public_tunnel_attempted": False,
        "browser_harness_used": False,
        "browser_use_cli_live_used": False,
        "workflow_use_code_copied": False,
        "shell_execution_from_browser_runtime_attempted": False,
        "agent_bus_enqueue_attempted": False,
        "provider_call_attempted": False,
        "gate_mutation_attempted": False,
        "canonical_writeback_attempted": False,
    }


def _write_evidence(vault: Path, result: dict[str, Any]) -> None:
    evidence_dir = vault / EVIDENCE_DIR
    evidence_dir.mkdir(parents=True, exist_ok=True)
    json_path = evidence_dir / f"excalidraw_public_drawing_proof_{result['run_slug']}.json"
    result["evidence_json_path"] = _relative_or_posix(vault, json_path)
    result["browser_run_log_written"] = True
    json_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")


def _write_agent_activity_evidence(vault: Path, result: dict[str, Any]) -> None:
    activity_dir = vault / AGENT_ACTIVITY_EVIDENCE_DIR
    activity_dir.mkdir(parents=True, exist_ok=True)
    path = activity_dir / f"excalidraw_public_drawing_proof_{result['run_slug']}.json"
    payload = {
        "record_type": "excalidraw_public_browser_drawing_proof_agent_activity_evidence",
        "schema_version": EXCALIDRAW_PUBLIC_DRAWING_PROOF_VERSION,
        "run_slug": result["run_slug"],
        "approval_id": result["approval_id"],
        "request_digest_sha256": result["request_digest_sha256"],
        "status": result["status"],
        "ok": result["ok"],
        "browser_run_log": result.get("evidence_json_path", ""),
        "screenshot_path": result.get("screenshot_path", ""),
        "forbidden_effects_false": {
            name: result.get(name) is False for name in FORBIDDEN_FALSE_FLAGS
        },
        "written_at": _now_utc(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result["agent_activity_evidence_path"] = _relative_or_posix(vault, path)
    result["agent_activity_log_written"] = True


def run_excalidraw_public_drawing_proof(
    vault_root: str | Path,
    *,
    approval_id: str = "",
    headless: bool = True,
    settle_ms: int = 6000,
    run_slug: str | None = None,
    write_evidence: bool = True,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    slug = run_slug or _slug()
    generated_at = _now_utc()
    approval_path, approval = _load_approval(vault, approval_id)
    result = _base_result(
        generated_at=generated_at,
        run_slug=slug,
        approval_path=approval_path,
        approval=approval,
        status=EXCALIDRAW_PUBLIC_DRAWING_PROOF_BLOCKED,
        blockers=[],
    )

    if approval is None:
        result["blockers"].append("valid_public_drawing_approval_not_found")
        result["checks"].append({"name": "approval_loaded", "ok": False, "detail": approval_path})
        return result

    result["checks"].append({"name": "approval_loaded", "ok": True, "detail": approval_path})
    marker_path = _safe_relative_path(
        vault,
        str(approval.get("idempotency_marker_path") or ""),
        IDEMPOTENCY_MARKER_RELATIVE_DIR,
    )
    if marker_path.exists():
        result["blockers"].append("idempotency_marker_already_exists")
        result["checks"].append(
            {
                "name": "idempotency_marker_absent",
                "ok": False,
                "detail": _relative_or_posix(vault, marker_path),
            }
        )
        return result

    if not _PLAYWRIGHT_AVAILABLE:
        result["blockers"].append("playwright_not_installed")
        result["checks"].append({"name": "playwright_available", "ok": False})
        return result
    result["checks"].append({"name": "playwright_available", "ok": True})

    reserved_marker_path = ""
    try:
        reserved_marker_path, marker_path = _reserve_marker(vault, approval, slug)
        result["checks"].append(
            {"name": "idempotency_marker_reserved", "ok": True, "detail": reserved_marker_path}
        )
    except FileExistsError:
        result["blockers"].append("idempotency_marker_already_exists")
        result["checks"].append({"name": "idempotency_marker_reserved", "ok": False})
        return result
    except Exception as exc:
        result["blockers"].append(f"idempotency_marker_reservation_failed: {exc}")
        result["checks"].append({"name": "idempotency_marker_reserved", "ok": False, "detail": str(exc)})
        return result

    label = _approval_label(approval)
    final_screenshot_path = vault / EVIDENCE_DIR / f"excalidraw_public_drawing_proof_{slug}.png"
    before_screenshot = b""
    after_screenshot = b""

    try:
        with sync_playwright() as pw:
            result["browser_launch_attempted"] = True
            browser = pw.chromium.launch(headless=headless)
            try:
                context = browser.new_context(
                    no_viewport=False,
                    viewport={"width": 1280, "height": 800},
                    storage_state=None,
                )
                page = context.new_page()
                result["target_navigation_attempted"] = True
                page.goto(result["target_url"], timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(settle_ms)
                result["checks"].append(
                    {"name": "navigation_succeeded", "ok": True, "detail": result["target_url"]}
                )

                title = page.title()
                result["page_title"] = title
                title_ok = EXCALIDRAW_EXPECTED_TITLE_FRAGMENT.lower() in title.lower()
                result["checks"].append(
                    {"name": "title_matches_excalidraw", "ok": title_ok, "detail": title}
                )

                canvas_box = _largest_canvas_box(page)
                result["canvas_found"] = canvas_box is not None
                result["canvas_box"] = canvas_box
                result["checks"].append(
                    {
                        "name": "canvas_element_present",
                        "ok": canvas_box is not None,
                        "detail": "largest canvas selected" if canvas_box else "no canvas found",
                    }
                )
                if canvas_box is None:
                    raise RuntimeError("no Excalidraw canvas found")

                before_screenshot = page.screenshot(full_page=False)
                result["drawing_action_attempted"] = True
                result["rectangle_action_attempted"] = True
                result["text_action_attempted"] = True
                _draw_rectangle_and_label(page, canvas_box, label)
                result["checks"].append({"name": "rectangle_action_attempted", "ok": True})
                result["checks"].append({"name": "text_action_attempted", "ok": True, "detail": label})

                result["local_storage_observation"] = _storage_observation(page, label)
                final_screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                result["screenshot_attempted"] = True
                after_screenshot = page.screenshot(path=str(final_screenshot_path), full_page=False)
                result["screenshot_path"] = _relative_or_posix(vault, final_screenshot_path)
                result["checks"].append(
                    {"name": "screenshot_captured", "ok": final_screenshot_path.exists(), "detail": result["screenshot_path"]}
                )
            finally:
                browser.close()

        visual_changed = bool(before_screenshot and after_screenshot and before_screenshot != after_screenshot)
        result["visual_change_after_actions"] = visual_changed
        storage = result.get("local_storage_observation") or {}
        semantic_observed = bool(storage.get("contains_label") or storage.get("contains_rectangle"))
        result["checks"].append(
            {
                "name": "visual_change_after_actions",
                "ok": visual_changed,
                "detail": "pre/post screenshots differ" if visual_changed else "pre/post screenshots identical",
            }
        )
        result["checks"].append(
            {
                "name": "throwaway_local_storage_scene_observed",
                "ok": semantic_observed,
                "detail": "label or rectangle observed" if semantic_observed else "not observed",
            }
        )

        required_checks_ok = all(
            bool(check.get("ok"))
            for check in result["checks"]
            if check.get("name")
            in {
                "approval_loaded",
                "playwright_available",
                "idempotency_marker_reserved",
                "navigation_succeeded",
                "title_matches_excalidraw",
                "canvas_element_present",
                "rectangle_action_attempted",
                "text_action_attempted",
                "screenshot_captured",
                "visual_change_after_actions",
            }
        )
        if not required_checks_ok:
            result["blockers"].append("required_drawing_proof_check_failed")
    except Exception as exc:
        result["blockers"].append(f"playwright_drawing_error: {exc}")
        result["checks"].append(
            {"name": "playwright_drawing_session", "ok": False, "detail": traceback.format_exc(limit=5)}
        )

    result["completed_at"] = _now_utc()
    result["ok"] = not result["blockers"]
    result["status"] = (
        EXCALIDRAW_PUBLIC_DRAWING_PROOF_COMPLETE
        if result["ok"]
        else EXCALIDRAW_PUBLIC_DRAWING_PROOF_FAILED
    )
    if write_evidence:
        _write_evidence(vault, result)
        _write_agent_activity_evidence(vault, result)
        _write_evidence(vault, result)
    if reserved_marker_path:
        _update_marker(
            marker_path,
            approval=approval,
            run_slug=slug,
            status="completed" if result["ok"] else "failed",
            evidence_json_path=result.get("evidence_json_path", ""),
            screenshot_path=result.get("screenshot_path", ""),
        )
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run approved public Excalidraw drawing proof.")
    parser.add_argument("--vault-root", default=".", help="Path to ChaseOS vault root.")
    parser.add_argument("--approval-id", default="", help="Approval id to consume; defaults to latest valid approval.")
    parser.add_argument("--headed", action="store_true", help="Run headed instead of headless.")
    parser.add_argument("--settle-ms", default=6000, type=int, help="Milliseconds to wait after navigation.")
    parser.add_argument("--run-slug", default="", help="Optional deterministic run slug.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = run_excalidraw_public_drawing_proof(
        args.vault_root,
        approval_id=args.approval_id,
        headless=not args.headed,
        settle_ms=args.settle_ms,
        run_slug=args.run_slug or None,
    )
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"ok: {result['ok']}")
        print(f"status: {result['status']}")
        print(f"approval_id: {result.get('approval_id')}")
        print(f"screenshot_path: {result.get('screenshot_path')}")
        print(f"evidence_json_path: {result.get('evidence_json_path')}")
        for blocker in result.get("blockers", []):
            print(f"blocker: {blocker}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
