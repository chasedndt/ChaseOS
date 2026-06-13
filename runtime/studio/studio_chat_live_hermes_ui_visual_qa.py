"""Live Hermes response proof for the Studio Chat UI.

This bounded QA pass sends a real Chat message through the ChaseOS Agent Bus to
Hermes, waits for the runtime response, then renders the production Chat shell
with the persisted conversation state and captures desktop/mobile screenshots.

The Playwright bridge returns real backend data captured after the live probe.
It does not call providers, read credentials, consume approvals, mutate
canonical memory, or perform external browser actions.
"""

from __future__ import annotations

import argparse
import contextlib
import http.server
import json
import socket
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_live_e2e import run_chat_probe
from runtime.studio.phase11_chat_route_state_and_message_drafts import (
    build_phase11_chat_route_state_and_message_drafts,
)
from runtime.studio.phase11_chat_runtime_dispatch_verification import (
    build_chat_runtime_availability,
)
from runtime.studio.phase11_chat_thread_conversations import load_chat_thread_conversations
from runtime.studio.phase11_chat_workspaces_foundation import (
    build_phase11_chat_workspaces_foundation,
)


SURFACE_ID = "studio_chat_live_hermes_ui_visual_qa"
PASS_ID = "studio-chat-live-hermes-ui-proof"
MODEL_VERSION = "studio.chat_live_hermes_ui_visual_qa.v1"
DEFAULT_MESSAGE = (
    "Studio UI proof request: reply with a short ChaseOS Hermes runtime "
    "acknowledgement for the saved Chat page."
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextlib.contextmanager
def _serve_frontend(frontend: Path):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(frontend), **kwargs)

        def log_message(self, _format: str, *args: Any) -> None:
            return

    port = _free_port()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}/index.html#chat"
    finally:
        server.shutdown()
        server.server_close()


def _js(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def _bridge_script(
    *,
    vault: Path,
    foundation: dict[str, Any],
    availability: dict[str, Any],
    probe: dict[str, Any],
) -> str:
    return f"""
window.__CHASEOS_VAULT_ROOT__ = {_js(str(vault))};
window.pywebview = {{
  api: {{
    get_chat_runtime_availability: async () => ({{ ok: true, data: {_js(availability)} }}),
    get_phase11_chat_workspaces_foundation: async () => ({{ ok: true, data: {_js(foundation)} }}),
    save_phase11_chat_route_state: async () => ({{ ok: true, data: {{ summary: {{ route_state_written: true }} }} }}),
    create_chat_folder: async (workspace_id, label) => ({{
      ok: true,
      data: {{ folder: {{ workspace_id, folder_id: String(label || 'new-folder').toLowerCase().replace(/[^a-z0-9]+/g, '-'), label }} }}
    }}),
    create_chat_thread: async (title, workspace_id, folder_id, folder_label, runtime_id) => ({{
      ok: true,
      data: {{ conversation: {{ thread_id: 'visual-created-thread', title, workspace_id, folder_id, folder_label, runtime_id, runtime_label: 'Hermes' }} }}
    }}),
    rename_chat_folder: async (workspace_id, folder_id, label) => ({{
      ok: true,
      data: {{ folder: {{ workspace_id, folder_id, label }}, updated_thread_count: 1 }}
    }}),
    delete_chat_folder: async (workspace_id, folder_id) => ({{
      ok: true,
      data: {{ workspace_id, folder_id, folder_deleted: true, moved_thread_count: 1 }}
    }}),
    move_chat_thread: async (thread_id, workspace_id, folder_id, folder_label) => ({{
      ok: true,
      data: {{ conversation: {{ thread_id, workspace_id, folder_id, folder_label, runtime_id: 'hermes', runtime_label: 'Hermes' }} }}
    }}),
    delete_chat_thread: async (thread_id) => ({{
      ok: true,
      data: {{ thread_id, active_record_deleted: true }}
    }}),
    send_chat_message: async () => ({{
      ok: true,
      data: {{
        ok: true,
        task_id: {_js(probe.get('task_id') or '')},
        thread_id: {_js(probe.get('thread_id') or 'runtime-ops-hermes-chat')},
        conversation_persisted: true,
        status: {_js(probe.get('status') or '')}
      }}
    }}),
    poll_chat_result: async () => ({{ ok: true, data: {_js(probe)} }}),
    get_daemon_status: async () => ({{ ok: true, data: {{ status: 'running' }} }}),
    start_runtime_daemon: async () => ({{ ok: true, data: {{ status: 'running' }} }}),
    stop_runtime_daemon: async () => ({{ ok: true, data: {{ status: 'stopped' }} }}),
    get_panel_registry: async () => ({{ ok: true, data: {{ panels: [], readiness: {{}} }} }}),
    get_graph_style_registry: async () => ({{ ok: true, data: {{}} }}),
    get_graph_settings: async () => ({{ ok: true, data: {{}} }}),
    list_graph_presets: async () => ({{ ok: true, data: {{ presets: [] }} }}),
    get_runtime_gateway_controls: async () => ({{ ok: true, data: {{}} }}),
    apply_runtime_chaseos_start_preferences: async () => ({{ ok: true, data: {{}} }}),
    get_dashboard: async () => ({{ ok: true, data: {{}} }})
  }}
}};
"""


def _write_browser_proof_html(
    *,
    vault: Path,
    output_dir: Path,
    foundation: dict[str, Any],
    availability: dict[str, Any],
    probe: dict[str, Any],
) -> Path:
    source = (vault / "runtime" / "studio" / "shell" / "frontend" / "index.html").read_text(encoding="utf-8")
    bridge = _bridge_script(
        vault=vault,
        foundation=foundation,
        availability=availability,
        probe=probe,
    )
    html = source.replace(
        "<head>",
        '<head>\n<base href="http://127.0.0.1:8895/">',
        1,
    )
    html = html.replace('href="styles.css"', 'href="styles.css?v=studio-chat-live-hermes-proof"', 1)
    html = html.replace(
        '<script src="app.js"></script>',
        f"<script>\n{bridge}\n</script>\n<script src=\"app.js\"></script>",
        1,
    )
    path = output_dir / "live-hermes-ui-proof.html"
    path.write_text(html, encoding="utf-8")
    return path


def _capture_screenshots(
    *,
    vault: Path,
    output_dir: Path,
    foundation: dict[str, Any],
    availability: dict[str, Any],
    probe: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    screenshots: list[dict[str, Any]] = []
    errors: list[str] = []
    frontend = vault / "runtime" / "studio" / "shell" / "frontend"

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - environment dependent
        return screenshots, [f"playwright_import_failed:{exc}"]

    try:
        with _serve_frontend(frontend) as url:
            bridge = _bridge_script(
                vault=vault,
                foundation=foundation,
                availability=availability,
                probe=probe,
            )
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    for name, viewport in {
                        "desktop": {"width": 1440, "height": 980},
                        "mobile": {"width": 390, "height": 844},
                    }.items():
                        page = browser.new_page(viewport=viewport)
                        console_errors: list[str] = []
                        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
                        page.add_init_script(bridge)
                        page.goto(url, wait_until="domcontentloaded")
                        page.wait_for_selector(".phase11-chat-live-thread", state="visible", timeout=15_000)
                        page.wait_for_selector(".phase11-chat-message.is-runtime", state="visible", timeout=15_000)
                        page.wait_for_timeout(600)

                        screenshot_path = output_dir / f"{name}-studio-chat-live-hermes-ui-proof.png"
                        page.screenshot(path=str(screenshot_path), full_page=True)
                        visible = page.evaluate(
                            """() => ({
                              title: document.querySelector('.phase11-chat-thread-header h3')?.textContent || '',
                              threadRows: Array.from(document.querySelectorAll('.chat-thread-nav-row strong')).map(el => el.textContent),
                              folderRows: Array.from(document.querySelectorAll('.chat-folder-row span')).map(el => el.textContent),
                              runtimeMessages: Array.from(document.querySelectorAll('.phase11-chat-message.is-runtime p')).map(el => el.textContent),
                              userMessages: Array.from(document.querySelectorAll('.phase11-chat-message.is-user p')).map(el => el.textContent),
                              sendButton: document.querySelector('#chat-send-button')?.textContent || '',
                              composer: !!document.querySelector('.phase11-chat-composer-box'),
                              inspector: !!document.querySelector('.phase11-chat-inspector'),
                              objectInspectorVisible: getComputedStyle(document.querySelector('#object-inspector')).display !== 'none',
                              leftRail: !!document.querySelector('.phase11-chat-left-rail')
                            })"""
                        )
                        screenshots.append(
                            {
                                "viewport": name,
                                "path": _rel(vault, screenshot_path),
                                "bytes": screenshot_path.stat().st_size if screenshot_path.is_file() else 0,
                                "not_blank": screenshot_path.is_file() and screenshot_path.stat().st_size > 10_000,
                                "visible": visible,
                                "hermes_response_visible": bool(probe.get("result_text"))
                                and any(str(probe.get("result_text") or "").splitlines()[0] in item for item in visible.get("runtimeMessages", [])),
                                "hermes_blocker_visible": any(
                                    "could not return a live reply yet" in item
                                    or "native Chat backend" in item
                                    or "Blocker:" in item
                                    for item in visible.get("runtimeMessages", [])
                                ),
                                "saved_threads_visible": bool(visible.get("threadRows")),
                                "folders_visible": bool(visible.get("folderRows")),
                                "composer_visible": bool(visible.get("composer")),
                                "object_inspector_hidden": not bool(visible.get("objectInspectorVisible")),
                                "console_errors": console_errors[:10],
                            }
                        )
                        page.close()
                finally:
                    browser.close()
    except Exception as exc:  # pragma: no cover - environment dependent
        errors.append(f"playwright_capture_failed:{exc}")

    return screenshots, errors


def build_studio_chat_live_hermes_ui_visual_qa(
    vault_root: str | Path,
    *,
    output_dir: str | Path | None = None,
    probe_timeout_s: float = 60.0,
    probe_message: str = DEFAULT_MESSAGE,
    capture_screenshots: bool = True,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    output = Path(output_dir).resolve() if output_dir else (
        vault / "07_LOGS" / "Visual-QA" / "2026-05-27-studio-chat-live-hermes-proof"
    )
    output.mkdir(parents=True, exist_ok=True)

    probe = run_chat_probe(
        vault,
        probe_message,
        runtime_id="hermes",
        max_wait_s=probe_timeout_s,
        poll_interval_s=1.0,
        synthesize_on_trigger=True,
    )
    result_text = str(probe.get("result_text") or "")
    bounded_ack_only = (
        "[Hermes bounded ack]" in result_text
        or "runtime execution is not currently active or returned no response" in result_text
        or "native Chat backend is not currently configured or authorized" in result_text
    )
    thread_id = str(probe.get("thread_id") or "runtime-ops-hermes-chat")
    conversations = load_chat_thread_conversations(vault)
    conversation = (conversations.get("conversations_by_thread_id") or {}).get(thread_id) or {}
    build_phase11_chat_route_state_and_message_drafts(
        vault,
        selected_workspace_id=conversation.get("workspace_id") or "runtime-ops",
        selected_folder_id=conversation.get("folder_id") or "runtime-control",
        selected_thread_id=thread_id,
        write_route_state=True,
    )
    foundation = build_phase11_chat_workspaces_foundation(vault)
    availability = build_chat_runtime_availability(vault)
    proof_html_path = _write_browser_proof_html(
        vault=vault,
        output_dir=output,
        foundation=foundation,
        availability=availability,
        probe=probe,
    )

    screenshots: list[dict[str, Any]] = []
    screenshot_errors: list[str] = []
    if capture_screenshots:
        screenshots, screenshot_errors = _capture_screenshots(
            vault=vault,
            output_dir=output,
            foundation=foundation,
            availability=availability,
            probe=probe,
        )

    blockers: list[str] = []
    if not probe.get("ok"):
        blockers.append(f"hermes_probe_{probe.get('probe_outcome') or 'failed'}")
    if capture_screenshots and not screenshots:
        blockers.append("no_screenshots_captured")
    if any(not item.get("not_blank") for item in screenshots):
        blockers.append("blank_or_tiny_screenshot")
    if any(
        not (item.get("hermes_response_visible") or item.get("hermes_blocker_visible"))
        for item in screenshots
    ):
        blockers.append("hermes_response_not_visible_in_ui")
    if any(not item.get("saved_threads_visible") for item in screenshots):
        blockers.append("saved_threads_not_visible")
    if any(not item.get("folders_visible") for item in screenshots):
        blockers.append("folders_not_visible")
    if any(not item.get("object_inspector_hidden") for item in screenshots):
        blockers.append("object_inspector_still_visible")
    if bounded_ack_only:
        blockers.append("hermes_synthesis_not_returned")
    if any(item.get("console_errors") for item in screenshots):
        blockers.append("console_errors_present")
    blockers.extend(screenshot_errors)

    report = {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "pass": PASS_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "status": "VERIFIED" if not blockers else "BLOCKED",
        "probe": probe,
        "thread_id": thread_id,
        "conversation_path": conversation.get("state_record_path"),
        "browser_proof_html_path": _rel(vault, proof_html_path),
        "runtime_availability_summary": availability.get("summary") or {},
        "screenshots": screenshots,
        "screenshot_errors": screenshot_errors,
        "blockers": blockers,
        "summary": {
            "hermes_probe_ok": bool(probe.get("ok")),
            "hermes_task_id": probe.get("task_id"),
            "hermes_result_visible_in_ui": bool(screenshots)
            and all(item.get("hermes_response_visible") or item.get("hermes_blocker_visible") for item in screenshots),
            "hermes_blocker_visible_in_ui": bool(screenshots)
            and all(item.get("hermes_blocker_visible") for item in screenshots),
            "desktop_and_mobile_checked": {item.get("viewport") for item in screenshots} == {"desktop", "mobile"},
            "saved_threads_visible": bool(screenshots)
            and all(item.get("saved_threads_visible") for item in screenshots),
            "folders_visible": bool(screenshots)
            and all(item.get("folders_visible") for item in screenshots),
            "bounded_ack_only": bounded_ack_only,
            "synthesize_trigger_requested": True,
            "provider_call_performed_by_studio": False,
            "approval_consumed": False,
            "canonical_mutation_performed": False,
        },
    }
    report_path = output / "studio-chat-live-hermes-ui-proof.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["report_path"] = _rel(vault, report_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture live Hermes response proof in the Studio Chat UI.")
    parser.add_argument("--vault-root", default=".")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--probe-timeout-s", type=float, default=60.0)
    parser.add_argument("--probe-message", default=DEFAULT_MESSAGE)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-screenshots", action="store_true")
    args = parser.parse_args()
    report = build_studio_chat_live_hermes_ui_visual_qa(
        args.vault_root,
        output_dir=args.output_dir,
        probe_timeout_s=args.probe_timeout_s,
        probe_message=args.probe_message,
        capture_screenshots=not args.no_screenshots,
    )
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"{report['status']}: {report.get('report_path', '')}")


if __name__ == "__main__":
    main()
