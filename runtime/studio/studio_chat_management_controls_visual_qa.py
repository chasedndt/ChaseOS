"""Visual QA for Studio Chat folder and thread management controls.

This proof renders the production Chat shell with the real local folder/thread
model and captures the opened folder dropdown plus the opened Manage menu. It
uses a pywebview mock bridge for frontend-only verification; it does not send
runtime messages, start processes, read credentials, consume approvals, or write
canonical memory.
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

from runtime.studio.phase11_chat_runtime_dispatch_verification import (
    build_chat_runtime_availability,
)
from runtime.studio.phase11_chat_workspaces_foundation import (
    build_phase11_chat_workspaces_foundation,
)


SURFACE_ID = "studio_chat_management_controls_visual_qa"
PASS_ID = "studio-chat-management-controls-visual-proof"
MODEL_VERSION = "studio.chat_management_controls_visual_qa.v1"


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
    return json.dumps(value, ensure_ascii=True).replace("</", "<\\/")


def _daemon_status_for(availability: dict[str, Any], adapter_id: str) -> dict[str, Any]:
    runtime = ((availability.get("runtime_by_adapter") or {}).get(adapter_id) or {}).copy()
    if runtime.get("heartbeat_online") or runtime.get("gateway_port_online") or runtime.get("pid_alive"):
        runtime.setdefault("status", "running")
    else:
        runtime.setdefault("status", "stopped")
    return runtime


def _bridge_script(
    *,
    vault: Path,
    foundation: dict[str, Any],
    availability: dict[str, Any],
) -> str:
    return f"""
window.__CHASEOS_VAULT_ROOT__ = {_js(str(vault))};
window.confirm = () => true;
window.prompt = (_message, value) => value || 'Renamed folder';
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
    send_chat_message: async () => ({{ ok: true, data: {{ task_id: 'visual-chat-task' }} }}),
    poll_chat_result: async () => ({{ ok: true, data: {{ is_complete: true, status: 'complete', result_text: 'Visual proof response.' }} }}),
    get_daemon_status: async (adapter_id) => {{
      const statuses = {{
        hermes: {_js(_daemon_status_for(availability, "hermes"))},
        openclaw: {_js(_daemon_status_for(availability, "openclaw"))}
      }};
      return {{ ok: true, data: statuses[adapter_id] || {{ status: 'stopped' }} }};
    }},
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
    frontend_base_url: str,
    foundation: dict[str, Any],
    availability: dict[str, Any],
) -> Path:
    source = (vault / "runtime" / "studio" / "shell" / "frontend" / "index.html").read_text(encoding="utf-8")
    bridge = _bridge_script(vault=vault, foundation=foundation, availability=availability)
    html = source.replace("<head>", f'<head>\n<base href="{frontend_base_url}">', 1)
    html = html.replace('href="styles.css"', 'href="styles.css?v=studio-chat-management-proof"', 1)
    html = html.replace(
        '<script src="app.js"></script>',
        f"<script>\n{bridge}\n</script>\n<script src=\"app.js\"></script>",
        1,
    )
    proof_path = output_dir / "studio-chat-management-controls-proof.html"
    proof_path.write_text(html, encoding="utf-8")
    return proof_path


def _page_state(page: Any) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const rect = (selector) => {
            const el = document.querySelector(selector);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, width: r.width, height: r.height };
          };
          const visibleText = (selector) => Array.from(document.querySelectorAll(selector))
            .filter((el) => el.offsetParent !== null)
            .map((el) => (el.textContent || '').trim())
            .filter(Boolean);
          const composerRect = rect('.phase11-chat-composer');
          const transcript = document.querySelector('#phase11-chat-conversation-stream') || document.querySelector('.phase11-chat-transcript');
          const folderDelete = document.querySelector('[data-chat-folder-menu-delete][data-chat-folder-id="runtime-control"]');
          const providerReadiness = document.querySelector('#chat-provider-readiness');
          const bodyText = document.body ? document.body.innerText || '' : '';
          return {
            title: document.querySelector('.phase11-chat-thread-header h3')?.textContent?.trim() || '',
            selectedRuntime: document.querySelector('.phase11-chat-thread-runtime strong')?.textContent?.trim() || '',
            runtimeStatus: document.querySelector('.phase11-chat-thread-runtime em')?.textContent?.trim() || '',
            folderToggleText: document.querySelector('#chat-folder-dropdown-button')?.textContent?.trim() || '',
            threadRows: visibleText('.chat-thread-nav-row strong'),
            folderRows: visibleText('.chat-folder-row span'),
            folderMenuVisible: !!document.querySelector('#chat-folder-dropdown-menu:not([hidden])'),
            folderMenuLabels: visibleText('.chat-folder-menu-select strong'),
            folderRenameVisible: visibleText('[data-chat-folder-menu-rename]').length > 0,
            folderDeleteVisible: visibleText('[data-chat-folder-menu-delete]').length > 0,
            runtimeFolderDeleteDisabled: !!(folderDelete && folderDelete.disabled),
            manageMenuOpen: !!document.querySelector('.phase11-chat-manage-menu[open]'),
            manageMoveButtons: visibleText('[data-chat-move-thread-folder]'),
            manageRenameVisible: visibleText('[data-chat-rename-current-folder]').length > 0,
            manageDeleteFolderVisible: visibleText('[data-chat-delete-current-folder]').length > 0,
            manageDeleteThreadVisible: visibleText('[data-chat-delete-current-thread]').length > 0,
            contextDrawerVisible: visibleText('.phase11-chat-context-drawer span').length > 0,
            composerVisible: !!composerRect,
            composerFitsViewport: !!composerRect && composerRect.bottom <= window.innerHeight + 2,
            pageVerticalOverflowPx: Math.max(
              document.documentElement.scrollHeight,
              document.body ? document.body.scrollHeight : 0
            ) - window.innerHeight,
            transcriptScrollable: !!transcript && transcript.scrollHeight > transcript.clientHeight + 2,
            providerReadinessVisible: !!providerReadiness && providerReadiness.offsetParent !== null,
            objectInspectorVisible: !!document.querySelector('#object-inspector')
              && getComputedStyle(document.querySelector('#object-inspector')).display !== 'none',
            sendButtonText: document.querySelector('#chat-send-button')?.textContent?.trim() || '',
            daemonButtons: visibleText('#chat-daemon-control button'),
            daemonStatus: document.querySelector('#chat-daemon-status-label')?.textContent?.trim() || '',
            leftRuntimeSelectorVisible: visibleText('#chat-adapter-selector .adapter-card').length > 0,
            leftDaemonControlVisible: visibleText('#chat-daemon-control').length > 0,
            leftRuntimeBannerVisible: visibleText('#chat-runtime-offline-banner').length > 0,
            inlineRuntimeButtons: visibleText('[data-chat-inline-runtime] span'),
            inlineRuntimeSelected: document.querySelector('[data-chat-inline-runtime].is-selected span')?.textContent?.trim() || '',
            runtimeManageButtons: visibleText('[data-chat-start-runtime-control], [data-chat-stop-runtime-control]'),
            runtimeCaption: document.querySelector('[data-chat-runtime-caption]')?.textContent?.trim() || '',
            hasProductNoiseText: /runtime governed|saved threads|file staged locally|preview first/i.test(bodyText),
            hasTemplateOnlyFolders: visibleText('.chat-folder-row span').some((label) =>
              ['Boards', 'Client Evidence', 'Missions', 'Research Threads', 'Today'].includes(label)
            )
          };
        }"""
    )


def _capture_state(
    *,
    page: Any,
    vault: Path,
    output_dir: Path,
    name: str,
    action: str,
) -> dict[str, Any]:
    if action == "folder-dropdown":
        page.click("#chat-folder-dropdown-button")
        page.wait_for_selector("#chat-folder-dropdown-menu:not([hidden])", state="visible", timeout=10_000)
    elif action == "manage-menu":
        page.click(".phase11-chat-manage-menu summary")
        page.wait_for_selector(".phase11-chat-manage-menu[open] .phase11-chat-manage-popover", state="visible", timeout=10_000)

    page.wait_for_timeout(250)
    screenshot_path = output_dir / f"{name}.png"
    page.screenshot(path=str(screenshot_path), full_page=False)
    state = _page_state(page)
    return {
        "name": name,
        "action": action,
        "path": _rel(vault, screenshot_path),
        "bytes": screenshot_path.stat().st_size if screenshot_path.is_file() else 0,
        "not_blank": screenshot_path.is_file() and screenshot_path.stat().st_size > 10_000,
        "state": state,
    }


def _capture_screenshots(
    *,
    vault: Path,
    output_dir: Path,
    foundation: dict[str, Any],
    availability: dict[str, Any],
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
            bridge = _bridge_script(vault=vault, foundation=foundation, availability=availability)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    for viewport_name, viewport in {
                        "desktop": {"width": 1440, "height": 940},
                        "mobile": {"width": 390, "height": 844},
                    }.items():
                        for action in ("default", "folder-dropdown", "manage-menu"):
                            page = browser.new_page(viewport=viewport)
                            console_errors: list[str] = []
                            page.on(
                                "console",
                                lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
                            )
                            page.add_init_script(bridge)
                            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                            page.wait_for_selector(".phase11-chat-live-thread", state="visible", timeout=45_000)
                            page.wait_for_selector(".phase11-chat-composer", state="visible", timeout=45_000)
                            capture = _capture_state(
                                page=page,
                                vault=vault,
                                output_dir=output_dir,
                                name=f"{viewport_name}-{action}",
                                action=action,
                            )
                            capture["viewport"] = viewport_name
                            capture["console_errors"] = console_errors[:10]
                            screenshots.append(capture)
                            page.close()
                finally:
                    browser.close()
    except Exception as exc:  # pragma: no cover - environment dependent
        errors.append(f"playwright_capture_failed:{exc}")

    return screenshots, errors


def _write_markdown_report(report: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Studio Chat Management Controls Visual QA",
        "",
        f"- Date: {report['created_at_utc']}",
        f"- Surface: `{SURFACE_ID}`",
        f"- Status: `{report['status']}`",
        f"- Browser path: `{report['browser_path']}`",
        f"- Fallback reason: {report['browser_fallback_reason']}",
        "",
        "## Checks",
    ]
    for check in report.get("checks", []):
        lines.append(f"- [{'x' if check.get('ok') else ' '}] {check.get('name')}: {check.get('detail')}")
    lines.extend(["", "## Screenshots"])
    for item in report.get("screenshots", []):
        state = item.get("state") or {}
        lines.append(
            f"- `{item.get('name')}`: `{item.get('path')}` "
            f"(composer fits: `{state.get('composerFitsViewport')}`, "
            f"folders: `{len(state.get('folderRows') or [])}`, "
            f"threads: `{len(state.get('threadRows') or [])}`)"
        )
    if report.get("blockers"):
        lines.extend(["", "## Blockers"])
        lines.extend(f"- {blocker}" for blocker in report["blockers"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_visual_qa(vault_root: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    out = Path(output_dir) if output_dir else vault / "07_LOGS" / "Visual-QA" / "2026-05-27-studio-chat-management-controls"
    if not out.is_absolute():
        out = (vault / out).resolve()
    out.relative_to(vault)
    out.mkdir(parents=True, exist_ok=True)

    foundation = build_phase11_chat_workspaces_foundation(vault)
    availability = build_chat_runtime_availability(vault)
    screenshots, screenshot_errors = _capture_screenshots(
        vault=vault,
        output_dir=out,
        foundation=foundation,
        availability=availability,
    )

    expected_custom_folder = any(
        str(folder.get("label") or folder.get("folder_id") or "").lower() == "coding"
        for folder in foundation.get("folders") or []
    )

    def all_states(predicate) -> bool:
        return bool(screenshots) and all(predicate(item.get("state") or {}) for item in screenshots)

    folder_open_states = [item.get("state") or {} for item in screenshots if item.get("action") == "folder-dropdown"]
    manage_open_states = [item.get("state") or {} for item in screenshots if item.get("action") == "manage-menu"]
    desktop_states = [item.get("state") or {} for item in screenshots if item.get("viewport") == "desktop"]

    checks = [
        {
            "name": "screenshots_captured",
            "ok": len(screenshots) == 6,
            "detail": f"{len(screenshots)} screenshots captured",
        },
        {
            "name": "screenshots_not_blank",
            "ok": bool(screenshots) and all(item.get("not_blank") for item in screenshots),
            "detail": "all screenshots exceed nonblank size threshold",
        },
        {
            "name": "saved_threads_visible",
            "ok": all_states(lambda state: bool(state.get("threadRows"))),
            "detail": "saved chat rows visible in default and opened states",
        },
        {
            "name": "folders_visible",
            "ok": all_states(lambda state: bool(state.get("folderRows"))),
            "detail": "folder list visible in Chat rail",
        },
        {
            "name": "custom_folder_visible_when_present",
            "ok": (not expected_custom_folder)
            or any(
                "coding" in [str(label).lower() for label in state.get("folderRows") or state.get("folderMenuLabels") or []]
                for state in [item.get("state") or {} for item in screenshots]
            ),
            "detail": "coding folder visible" if expected_custom_folder else "no coding folder exists in current state",
        },
        {
            "name": "folder_dropdown_actions_visible",
            "ok": bool(folder_open_states)
            and all(
                state.get("folderMenuVisible")
                and state.get("folderRenameVisible")
                and state.get("folderDeleteVisible")
                and state.get("runtimeFolderDeleteDisabled")
                for state in folder_open_states
            ),
            "detail": "folder dropdown exposes rename/delete and protects Runtime Chats deletion",
        },
        {
            "name": "folder_dropdown_shows_selected_folder",
            "ok": all_states(lambda state: state.get("folderToggleText") not in {"", "Folders", "All folders"}),
            "detail": "folder dropdown button names the active folder instead of a generic label",
        },
        {
            "name": "template_only_folders_hidden",
            "ok": all_states(lambda state: not state.get("hasTemplateOnlyFolders")),
            "detail": "template-only board/mission/research lanes stay out of the default Chat rail",
        },
        {
            "name": "manage_menu_actions_visible",
            "ok": bool(manage_open_states)
            and all(
                state.get("manageMenuOpen")
                and state.get("manageMoveButtons")
                and state.get("manageRenameVisible")
                and state.get("manageDeleteFolderVisible")
                and state.get("manageDeleteThreadVisible")
                and not state.get("contextDrawerVisible")
                for state in manage_open_states
            ),
            "detail": "Manage menu exposes move, rename, delete folder, and delete chat without context-chip clutter",
        },
        {
            "name": "runtime_controls_moved_from_thread_rail",
            "ok": all_states(
                lambda state: not state.get("leftRuntimeSelectorVisible")
                and not state.get("leftDaemonControlVisible")
                and not state.get("leftRuntimeBannerVisible")
            )
            and bool(manage_open_states)
            and all(
                state.get("inlineRuntimeButtons")
                and state.get("inlineRuntimeSelected")
                and state.get("runtimeManageButtons")
                and state.get("runtimeCaption")
                for state in manage_open_states
            ),
            "detail": "runtime switch/connect controls live in Manage instead of the folders/thread rail",
        },
        {
            "name": "product_noise_removed",
            "ok": all_states(lambda state: not state.get("hasProductNoiseText")),
            "detail": "default Chat viewport does not show noisy implementation chips",
        },
        {
            "name": "runtime_readiness_not_cluttering_view",
            "ok": all_states(lambda state: not state.get("providerReadinessVisible")),
            "detail": "runtime sync details are not rendered as a large default panel above the chat",
        },
        {
            "name": "runtime_status_not_generic_syncing",
            "ok": all_states(
                lambda state: str(state.get("runtimeStatus") or "").strip().lower()
                not in {"checking", "syncing"}
            ),
            "detail": "Chat thread status hides transient runtime states and shows only concrete runtime state chips",
        },
        {
            "name": "composer_fits_viewport",
            "ok": bool(desktop_states) and all(bool(state.get("composerFitsViewport")) for state in desktop_states),
            "detail": "desktop composer remains in the first viewport",
        },
        {
            "name": "desktop_global_scroll_avoided",
            "ok": bool(desktop_states)
            and all(int(state.get("pageVerticalOverflowPx") or 0) <= 8 for state in desktop_states),
            "detail": "desktop Chat uses internal transcript/rail scrolling rather than page overflow",
        },
        {
            "name": "object_inspector_hidden",
            "ok": all_states(lambda state: not state.get("objectInspectorVisible")),
            "detail": "Chat page does not show the right object inspector",
        },
        {
            "name": "console_clean",
            "ok": bool(screenshots) and all(not item.get("console_errors") for item in screenshots),
            "detail": "no browser console errors captured",
        },
    ]

    blockers = [check["name"] for check in checks if not check["ok"]]
    blockers.extend(screenshot_errors)
    status = "verified" if not blockers else "blocked"

    report = {
        "surface": SURFACE_ID,
        "pass_id": PASS_ID,
        "model_version": MODEL_VERSION,
        "created_at_utc": _now_utc(),
        "status": status,
        "ok": not blockers,
        "browser_path": "regular_playwright",
        "browser_fallback_reason": "Browser plugin not available in this Codex continuation; regular Playwright used.",
        "vault_root": str(vault),
        "output_dir": _rel(vault, out),
        "expected_custom_folder_coding": expected_custom_folder,
        "checks": checks,
        "screenshots": screenshots,
        "screenshot_errors": screenshot_errors,
        "blockers": blockers,
        "authority": {
            "provider_calls_performed": False,
            "runtime_messages_sent": False,
            "runtime_processes_started": False,
            "approval_consumed": False,
            "canonical_memory_written": False,
        },
    }
    json_path = out / "studio-chat-management-controls-visual-qa.json"
    md_path = out / "studio-chat-management-controls-visual-qa.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    _write_markdown_report(report, md_path)
    report["report_json_path"] = _rel(vault, json_path)
    report["report_markdown_path"] = _rel(vault, md_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-root", default=".")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run_visual_qa(args.vault_root, args.output_dir)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        print(f"{SURFACE_ID}: {report['status']}")


if __name__ == "__main__":
    main()
