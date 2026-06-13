"""Controlled live proof for the ChaseOS-owned browser page Capture collector."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import html
import http.server
import json
from pathlib import Path
import socket
import threading
from typing import Any, Iterator

from runtime.studio.capture_collector_settings import (
    BrowserPageProvider,
    capture_chaseos_browser_page_for_markdown,
    capture_collector_settings_path,
    save_capture_collector_settings,
)
from runtime.studio.capture_to_markdown_panel import (
    preview_capture_to_markdown,
    save_capture_to_markdown,
)


DEFAULT_EVIDENCE_ROOT = Path("07_LOGS/Studio-Graph-Views")
DEFAULT_DESCRIPTOR = "capture-markdown-chaseos-browser-page-live-proof"
CONTROLLED_PAGE_TITLE = "ChaseOS Markdown Capture Controlled Page"
CONTROLLED_PAGE_SENTINEL = "CHASEOS_BROWSER_PAGE_CAPTURE_SENTINEL_2026_05_28"


def run_chaseos_browser_page_live_proof(
    *,
    vault_root: str | Path,
    evidence_root: str | Path = DEFAULT_EVIDENCE_ROOT,
    evidence_slug: str | None = None,
    run_id: str | None = None,
    save_markdown: bool = False,
    write_evidence: bool = True,
    browser_provider: BrowserPageProvider | None = None,
) -> dict[str, Any]:
    """Capture a controlled local page through the product collector and preview Markdown."""

    vault = Path(vault_root).resolve()
    slug = evidence_slug or f"{_date_slug()}-{DEFAULT_DESCRIPTOR}"
    capture_run_id = run_id or slug
    settings_path = capture_collector_settings_path(vault)
    original_settings_text = _read_text_if_exists(settings_path)
    original_settings_existed = original_settings_text is not None
    settings_restored = False
    capture: dict[str, Any] = {}
    preview: dict[str, Any] = {}
    saved: dict[str, Any] = {}
    server_url = ""

    try:
        with _serve_controlled_page() as server:
            server_url = server["url"]
            save_capture_collector_settings(
                vault,
                {"chaseos_browser_page_capture_enabled": True},
            )
            capture = capture_chaseos_browser_page_for_markdown(
                vault,
                {
                    "operator_confirmed": True,
                    "source_url": server_url,
                    "allowed_origin": server_url,
                    "title": CONTROLLED_PAGE_TITLE,
                    "run_id": capture_run_id,
                    "profile": "research_note",
                },
                browser_provider=browser_provider,
            )
            if capture.get("ok"):
                markdown_payload = {
                    "source_mode": capture.get("source_mode") or "controlled_html_artifact",
                    "profile": "research_note",
                    "title": capture.get("title") or CONTROLLED_PAGE_TITLE,
                    "file_path": capture.get("file_path") or "",
                    "source_url": capture.get("source_url") or server_url,
                }
                preview = preview_capture_to_markdown(vault, markdown_payload)
                if save_markdown:
                    saved = save_capture_to_markdown(vault, markdown_payload)
    finally:
        settings_restored = _restore_settings_file(
            settings_path,
            original_settings_text,
            original_settings_existed=original_settings_existed,
        )

    verification = _verify_live_proof(
        vault=vault,
        capture=capture,
        preview=preview,
        saved=saved,
        save_markdown=save_markdown,
        settings_restored=settings_restored,
    )
    proof = {
        "ok": verification["ok"],
        "status": (
            "chaseos_browser_page_live_capture_preview_verified"
            if verification["ok"]
            else "chaseos_browser_page_live_capture_preview_blocked"
        ),
        "schema_version": "studio.capture_markdown.chaseos_browser_page_live_proof.v1",
        "generated_at_utc": _now_utc(),
        "run_id": capture_run_id,
        "controlled_page": {
            "url": server_url,
            "title": CONTROLLED_PAGE_TITLE,
            "sentinel": CONTROLLED_PAGE_SENTINEL,
            "local_loopback_only": True,
        },
        "authority": {
            "settings_temporarily_enabled": True,
            "settings_restored_after_run": settings_restored,
            "operator_click_simulated_for_controlled_proof": True,
            "declared_http_address_required": True,
            "launches_chaseos_owned_isolated_browser": browser_provider is None,
            "test_injected_browser_provider": browser_provider is not None,
            "reads_personal_active_browser_tab": False,
            "reads_browser_profile": False,
            "reads_browser_history": False,
            "reads_browser_cookies": False,
            "reads_browser_sessions": False,
            "reads_browser_storage": False,
            "writes_controlled_browser_artifacts": bool(capture.get("write_performed")),
            "writes_raw_quarantine_markdown_on_collector_click": False,
            "save_markdown_requested": save_markdown,
            "external_send_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "capture": _summarize_capture(capture),
        "preview": _summarize_preview(preview),
        "save": _summarize_save(saved),
        "verification": verification,
        "evidence": {},
    }
    if write_evidence:
        proof["evidence"] = write_chaseos_browser_page_live_proof_evidence(
            vault,
            proof,
            evidence_root=evidence_root,
            evidence_slug=slug,
        )
    return proof


def write_chaseos_browser_page_live_proof_evidence(
    vault_root: str | Path,
    proof: dict[str, Any],
    *,
    evidence_root: str | Path = DEFAULT_EVIDENCE_ROOT,
    evidence_slug: str,
) -> dict[str, str]:
    vault = Path(vault_root).resolve()
    root = _resolve_under_vault(vault, evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / f"{evidence_slug}.json"
    markdown_path = root / f"{evidence_slug}.md"
    json_path.write_text(json.dumps(proof, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path.write_text(_proof_markdown(proof), encoding="utf-8")
    return {
        "json_path": _rel(json_path, vault),
        "markdown_path": _rel(markdown_path, vault),
    }


def _verify_live_proof(
    *,
    vault: Path,
    capture: dict[str, Any],
    preview: dict[str, Any],
    saved: dict[str, Any],
    save_markdown: bool,
    settings_restored: bool,
) -> dict[str, Any]:
    html_path = _resolve_optional_rel(vault, str(capture.get("file_path") or ""))
    screenshot_path = _resolve_optional_rel(vault, str(capture.get("screenshot_path") or ""))
    audit_path = _resolve_optional_rel(vault, str(capture.get("audit_path") or ""))
    html_text = _read_text_if_exists(html_path) if html_path else ""
    preview_markdown = str(preview.get("markdown") or "")

    checks = {
        "collector_capture_ok": bool(capture.get("ok")),
        "collector_ready_for_markdown": capture.get("status") == "chaseos_browser_page_ready_for_markdown",
        "collector_source_mode_controlled_html_artifact": capture.get("source_mode") == "controlled_html_artifact",
        "collector_writes_no_raw_quarantine_markdown": capture.get("writes_raw_quarantine_markdown") is False,
        "collector_next_action_preview_or_save": capture.get("next_action") == "preview_or_save_capture_to_markdown",
        "collector_reads_chaseos_owned_page": _authority(capture, "reads_chaseos_owned_browser_page") is True,
        "collector_reads_no_personal_browser_tab": _authority(capture, "reads_personal_active_browser_tab") is False,
        "collector_reads_no_browser_profile": _authority(capture, "reads_browser_profile") is False,
        "collector_reads_no_browser_history": _authority(capture, "reads_browser_history") is False,
        "collector_reads_no_browser_cookies": _authority(capture, "reads_browser_cookies") is False,
        "controlled_html_artifact_exists": bool(html_path and html_path.is_file()),
        "controlled_html_artifact_contains_sentinel": CONTROLLED_PAGE_SENTINEL in html_text,
        "screenshot_artifact_exists": bool(screenshot_path and screenshot_path.is_file()),
        "screenshot_artifact_nonempty": bool(screenshot_path and screenshot_path.is_file() and screenshot_path.stat().st_size > 0),
        "audit_artifact_exists": bool(audit_path and audit_path.is_file()),
        "preview_ok": bool(preview.get("ok")),
        "preview_write_free": preview.get("write_performed") is False,
        "preview_markdown_contains_sentinel": CONTROLLED_PAGE_SENTINEL in preview_markdown,
        "settings_restored_after_run": settings_restored,
    }
    if save_markdown:
        checks["save_markdown_ok"] = bool(saved.get("ok"))
        checks["save_markdown_written"] = saved.get("write_performed") is True
    else:
        checks["save_markdown_not_requested"] = not saved

    return {
        "ok": all(checks.values()),
        "checks": checks,
        "failed_checks": [key for key, value in checks.items() if not value],
        "artifact_paths": {
            "controlled_html_artifact": str(capture.get("file_path") or ""),
            "screenshot": str(capture.get("screenshot_path") or ""),
            "audit": str(capture.get("audit_path") or ""),
            "saved_markdown": str(saved.get("content_path") or ""),
            "saved_packet": str(saved.get("visual_capture_packet_path") or ""),
        },
    }


@contextmanager
def _serve_controlled_page() -> Iterator[dict[str, Any]]:
    port = _free_loopback_port()
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", port),
        _controlled_page_handler(),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield {"url": f"http://127.0.0.1:{port}/capture-markdown-controlled-page"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _controlled_page_handler() -> type[http.server.BaseHTTPRequestHandler]:
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path not in {"/", "/capture-markdown-controlled-page"}:
                self.send_response(404)
                self.end_headers()
                return
            body = _controlled_page_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def _controlled_page_html() -> str:
    title = html.escape(CONTROLLED_PAGE_TITLE)
    sentinel = html.escape(CONTROLLED_PAGE_SENTINEL)
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
</head>
<body>
<main>
<h1>{title}</h1>
<p>{sentinel}</p>
<p>This local page proves the ChaseOS-owned browser page collector can capture
controlled web content into a Markdown preview without reading personal browser
tabs, profiles, cookies, sessions, storage, or history.</p>
</main>
</body>
</html>
"""


def _proof_markdown(proof: dict[str, Any]) -> str:
    verification = proof.get("verification") if isinstance(proof.get("verification"), dict) else {}
    checks = verification.get("checks") if isinstance(verification.get("checks"), dict) else {}
    failed = verification.get("failed_checks") if isinstance(verification.get("failed_checks"), list) else []
    lines = [
        f"# {proof.get('run_id')}",
        "",
        f"- Status: `{proof.get('status')}`",
        f"- Overall result: `{proof.get('ok')}`",
        f"- Controlled page: `{proof.get('controlled_page', {}).get('url', '')}`",
        f"- Controlled sentinel: `{proof.get('controlled_page', {}).get('sentinel', '')}`",
        f"- Save Markdown requested: `{proof.get('authority', {}).get('save_markdown_requested')}`",
        f"- Reads personal active browser tab: `{proof.get('authority', {}).get('reads_personal_active_browser_tab')}`",
        f"- Reads browser cookies: `{proof.get('authority', {}).get('reads_browser_cookies')}`",
        f"- Writes raw quarantine Markdown on collector click: `{proof.get('authority', {}).get('writes_raw_quarantine_markdown_on_collector_click')}`",
        "",
        "## Checks",
        "",
    ]
    for key in sorted(checks):
        lines.append(f"- `{key}`: `{checks[key]}`")
    lines.extend(["", "## Failed Checks", ""])
    if failed:
        lines.extend(f"- `{item}`" for item in failed)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Controlled HTML artifact: `{proof.get('capture', {}).get('file_path', '')}`",
            f"- Screenshot: `{proof.get('capture', {}).get('screenshot_path', '')}`",
            f"- Audit: `{proof.get('capture', {}).get('audit_path', '')}`",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _summarize_capture(capture: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(capture.get("ok")),
        "status": capture.get("status"),
        "source_mode": capture.get("source_mode"),
        "title": capture.get("title"),
        "file_path": capture.get("file_path"),
        "source_url": capture.get("source_url"),
        "screenshot_path": capture.get("screenshot_path"),
        "audit_path": capture.get("audit_path"),
        "writes_raw_quarantine_markdown": capture.get("writes_raw_quarantine_markdown"),
        "blockers": list(capture.get("blockers") or []),
        "message": capture.get("message"),
    }


def _summarize_preview(preview: dict[str, Any]) -> dict[str, Any]:
    markdown = str(preview.get("markdown") or "")
    return {
        "ok": bool(preview.get("ok")),
        "status": preview.get("status"),
        "write_performed": preview.get("write_performed"),
        "save_allowed": preview.get("save_allowed"),
        "markdown_char_count": len(markdown),
        "contains_sentinel": CONTROLLED_PAGE_SENTINEL in markdown,
        "blockers": list(preview.get("blockers") or []),
    }


def _summarize_save(saved: dict[str, Any]) -> dict[str, Any]:
    if not saved:
        return {"requested": False}
    return {
        "requested": True,
        "ok": bool(saved.get("ok")),
        "status": saved.get("status"),
        "write_performed": saved.get("write_performed"),
        "content_path": saved.get("content_path"),
        "visual_capture_packet_path": saved.get("visual_capture_packet_path"),
        "blockers": list(saved.get("blockers") or []),
    }


def _authority(payload: dict[str, Any], key: str) -> Any:
    authority = payload.get("authority")
    if isinstance(authority, dict):
        return authority.get(key)
    return None


def _restore_settings_file(
    settings_path: Path,
    original_settings_text: str | None,
    *,
    original_settings_existed: bool,
) -> bool:
    try:
        if original_settings_existed:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(original_settings_text or "", encoding="utf-8")
        elif settings_path.exists():
            settings_path.unlink()
        return True
    except Exception:
        return False


def _read_text_if_exists(path: Path | None) -> str | None:
    if not path or not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _resolve_optional_rel(vault: Path, value: str) -> Path | None:
    if not value:
        return None
    path = Path(value)
    resolved = path if path.is_absolute() else vault / path
    resolved = resolved.resolve()
    try:
        resolved.relative_to(vault)
    except ValueError:
        return None
    return resolved


def _resolve_under_vault(vault: Path, path_value: str | Path) -> Path:
    path = Path(path_value)
    resolved = path if path.is_absolute() else vault / path
    resolved = resolved.resolve()
    try:
        resolved.relative_to(vault)
    except ValueError as exc:
        raise ValueError(f"path must stay inside vault root: {path_value}") from exc
    return resolved


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _date_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the controlled ChaseOS-owned browser page Capture to Markdown proof.",
    )
    parser.add_argument("--vault-root", default=".")
    parser.add_argument("--evidence-root", default=str(DEFAULT_EVIDENCE_ROOT))
    parser.add_argument("--evidence-slug", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--save-markdown", action="store_true")
    parser.add_argument("--no-write-evidence", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    proof = run_chaseos_browser_page_live_proof(
        vault_root=args.vault_root,
        evidence_root=args.evidence_root,
        evidence_slug=args.evidence_slug,
        run_id=args.run_id,
        save_markdown=args.save_markdown,
        write_evidence=not args.no_write_evidence,
    )
    if args.json:
        print(json.dumps(proof, indent=2, sort_keys=True))
    else:
        status = "OK" if proof.get("ok") else "BLOCKED"
        print(f"{status}: {proof.get('status')}")
        for failed_check in proof.get("verification", {}).get("failed_checks", []):
            print(f"- {failed_check}")
    return 0 if proof.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
