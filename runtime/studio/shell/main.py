"""ChaseOS Studio — desktop shell entry point (Pass 10A).

Usage:
    python -m runtime.studio.shell.main [--vault-root PATH] [--dev] [--initial-hash #/dashboard]
    chaseos studio shell [--vault-root PATH] [--dev] [--initial-hash #/dashboard]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import traceback
from pathlib import Path
import tempfile
import uuid

WEBVIEW2_USER_DATA_ENV = "WEBVIEW2_USER_DATA_FOLDER"
PYWEBVIEW_GUI_ENV = "PYWEBVIEW_GUI"
QT_API_ENV = "QT_API"
INITIAL_HASH_ENV = "CHASEOS_STUDIO_INITIAL_HASH"
QA_SCREENSHOT_PATH_ENV = "CHASEOS_STUDIO_QA_SCREENSHOT_PATH"
QA_SCREENSHOT_META_PATH_ENV = "CHASEOS_STUDIO_QA_SCREENSHOT_META_PATH"
QA_SCREENSHOT_DELAY_MS_ENV = "CHASEOS_STUDIO_QA_SCREENSHOT_DELAY_MS"
QA_EXIT_AFTER_SCREENSHOT_ENV = "CHASEOS_STUDIO_QA_EXIT_AFTER_SCREENSHOT"
QA_BATCH_PLAN_PATH_ENV = "CHASEOS_STUDIO_QA_BATCH_PLAN_PATH"
QA_BATCH_RESULT_PATH_ENV = "CHASEOS_STUDIO_QA_BATCH_RESULT_PATH"
QA_WINDOW_WIDTH_ENV = "CHASEOS_STUDIO_QA_WINDOW_WIDTH"
QA_WINDOW_HEIGHT_ENV = "CHASEOS_STUDIO_QA_WINDOW_HEIGHT"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ChaseOS Studio desktop shell")
    parser.add_argument("--vault-root", dest="vault_root", default=None)
    parser.add_argument(
        "--initial-hash",
        dest="initial_hash",
        default=None,
        help="Optional Studio route fragment for native visual QA, e.g. #/chat",
    )
    parser.add_argument("--dev", action="store_true", default=False)
    # Absorb any extra args passed through chaseos CLI routing
    parser.add_argument("args", nargs="*")
    return parser.parse_args()


def _install_windows_safe_mkdtemp_workaround() -> None:
    if sys.platform != "win32" or getattr(tempfile, "_chaseos_safe_mkdtemp_installed", False):
        return
    original_mkdtemp = tempfile.mkdtemp

    def _safe_mkdtemp(suffix: str | None = None, prefix: str | None = None, dir: str | None = None) -> str:
        if any(isinstance(value, bytes) for value in (suffix, prefix, dir)):
            return original_mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
        selected_suffix = "" if suffix is None else suffix
        selected_prefix = "tmp" if prefix is None else prefix
        root = Path(dir if dir is not None else tempfile.gettempdir())
        root.mkdir(parents=True, exist_ok=True)
        for _ in range(100):
            candidate = root / f"{selected_prefix}{uuid.uuid4().hex[:8]}{selected_suffix}"
            try:
                os.mkdir(candidate)
                return str(candidate)
            except FileExistsError:
                continue
        return original_mkdtemp(suffix=selected_suffix, prefix=selected_prefix, dir=str(root))

    tempfile.mkdtemp = _safe_mkdtemp
    tempfile._chaseos_safe_mkdtemp_installed = True


def _resolve_webview_storage_path(vault_root: Path) -> str | None:
    raw = os.environ.get(WEBVIEW2_USER_DATA_ENV)
    if not raw:
        return None
    selected = Path(raw)
    if not selected.is_absolute():
        selected = vault_root / selected
    selected = selected.resolve()
    selected.mkdir(parents=True, exist_ok=True)
    return str(selected)


def _configure_qt_backend_env() -> None:
    """Force pywebview onto the PyQt6 backend before Qt/pywebview imports.

    Also inject Chromium flags that enable WebGL and bypass the GPU blocklist.
    Chromium (used by QtWebEngine) can suppress hardware-accelerated WebGL on
    certain driver configurations, causing Three.js to silently render a blank
    canvas.  The flags below force GPU rasterisation and disable the blocklist
    so 3d-force-graph always gets a real WebGL context.

    QTWEBENGINE_CHROMIUM_FLAGS must be set before QApplication is created.
    """

    os.environ[PYWEBVIEW_GUI_ENV] = "qt"
    os.environ[QT_API_ENV] = "pyqt6"

    # Merge with any existing flags the user may have set already
    existing = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "").strip()
    webgl_flags = (
        "--enable-webgl "
        "--ignore-gpu-blocklist "
        "--enable-gpu-rasterization "
        "--enable-accelerated-2d-canvas "
        "--disable-software-rasterizer"
    )
    merged = (existing + " " + webgl_flags).strip() if existing else webgl_flags
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = merged


def _normalize_initial_hash(value: str | None) -> str:
    raw = value or os.environ.get(INITIAL_HASH_ENV) or ""
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith("#/"):
        candidate = raw
    elif raw.startswith("#"):
        candidate = "#/" + raw.lstrip("#/")
    else:
        candidate = "#/" + raw.lstrip("/")
    fragment = candidate[2:]
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_/")
    if not fragment or any(char not in allowed for char in fragment):
        raise ValueError("initial hash must be a Studio route fragment such as #/chat")
    return candidate


def _route_label_from_hash(route_hash: str) -> str:
    fragment = route_hash.lstrip("#/").strip()
    if not fragment:
        return "Home"
    try:
        from runtime.studio.final_productization_visual_qa import PANELS

        for panel in PANELS:
            if str(panel.get("id") or "") == fragment:
                return str(panel.get("name") or fragment)
    except Exception:
        pass
    return fragment.replace("-", " ").replace("_", " ").title()


def _append_startup_message(message: str) -> None:
    log_path = os.environ.get("CHASEOS_STUDIO_STARTUP_LOG")
    if not log_path:
        return
    try:
        path = Path(log_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        path.write_text(existing + message + "\n", encoding="utf-8")
    except Exception:
        pass


def _qa_env_path(env_key: str) -> Path | None:
    raw = os.environ.get(env_key)
    if not raw:
        return None
    try:
        return Path(raw).expanduser().resolve()
    except Exception:
        return None


def _qa_window_dimension(env_key: str, *, default: int, minimum: int, maximum: int) -> int:
    raw = os.environ.get(env_key)
    if not raw:
        return default
    try:
        requested = int(str(raw).strip())
    except ValueError:
        return default
    return max(minimum, min(maximum, requested))


def _schedule_qa_screenshot(qt_app, window, *, title: str, vault_name: str = "") -> None:
    screenshot_path = _qa_env_path(QA_SCREENSHOT_PATH_ENV)
    batch_plan_path = _qa_env_path(QA_BATCH_PLAN_PATH_ENV)
    batch_result_path = _qa_env_path(QA_BATCH_RESULT_PATH_ENV)
    if screenshot_path is None and batch_plan_path is None:
        return
    if qt_app is None:
        return
    if getattr(_schedule_qa_screenshot, "_scheduled", False):
        return
    setattr(_schedule_qa_screenshot, "_scheduled", True)
    meta_path = _qa_env_path(QA_SCREENSHOT_META_PATH_ENV) or (
        screenshot_path.with_suffix(".qa-meta.json") if screenshot_path else None
    )
    try:
        delay_ms = int(os.environ.get(QA_SCREENSHOT_DELAY_MS_ENV) or "3000")
    except ValueError:
        delay_ms = 3000
    delay_ms = max(250, min(delay_ms, 30000))
    exit_after = os.environ.get(QA_EXIT_AFTER_SCREENSHOT_ENV, "").strip().lower() in {"1", "true", "yes"}
    state = {"attempts": 0, "ok": False}

    def _write_meta_to(target_meta_path: Path, payload: dict) -> None:
        try:
            target_meta_path.parent.mkdir(parents=True, exist_ok=True)
            target_meta_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        except Exception as exc:
            _append_startup_message(f"QA screenshot metadata write failed: {exc}")

    def _capture_to(target_screenshot_path: Path, target_meta_path: Path, extra: dict | None = None) -> dict:
        state["attempts"] += 1
        route_title = str((extra or {}).get("window_title") or title)
        payload: dict = {
            "ok": False,
            "method": "qt_widget_grab",
            "window_title": route_title,
            "screenshot_path": str(target_screenshot_path),
            "meta_path": str(target_meta_path),
            "attempt": state["attempts"],
        }
        if extra:
            payload.update(extra)
        try:
            from PyQt6.QtWidgets import QApplication

            _append_startup_message(f"QA screenshot capture attempt {state['attempts']} started")
            qt_app.processEvents()
            widgets = [widget for widget in QApplication.topLevelWidgets() if widget is not None]
            visible_widgets = [widget for widget in widgets if widget.isVisible()]
            candidates = visible_widgets or widgets
            payload["widget_count"] = len(widgets)
            payload["visible_widget_count"] = len(visible_widgets)
            if not candidates:
                raise RuntimeError("no Qt top-level widgets available for QA screenshot")
            target = max(candidates, key=lambda widget: max(0, widget.width()) * max(0, widget.height()))
            target.showNormal()
            target.raise_()
            target.activateWindow()
            for _ in range(4):
                qt_app.processEvents()
                time.sleep(0.05)
            # Prefer widget.grab() for route proof. On some Windows/WebEngine
            # hosts QScreen.grabWindow(winId) can return the foreground desktop
            # surface instead of the Studio window, producing false route proof.
            prefer_screen_grab = os.environ.get("CHASEOS_STUDIO_QA_SCREEN_GRAB") == "1"
            pixmap = None
            if prefer_screen_grab:
                try:
                    screen = QApplication.primaryScreen()
                    if screen is not None:
                        pixmap = screen.grabWindow(int(target.winId()))
                        if pixmap is not None and not pixmap.isNull():
                            payload["method"] = "qscreen_grabwindow"
                            _append_startup_message(
                                f"QA screenshot: QScreen.grabWindow (preferred) "
                                f"({pixmap.width()}x{pixmap.height()})"
                            )
                        else:
                            pixmap = None
                except Exception as _pref_grab_exc:
                    _append_startup_message(
                        f"QA screenshot: preferred QScreen.grabWindow raised {_pref_grab_exc!r}"
                    )
                    pixmap = None
            if not prefer_screen_grab:
                pixmap = target.grab()
                payload["method"] = "qt_widget_grab"
                _append_startup_message("QA screenshot: using widget.grab()")
            if pixmap is None or pixmap.isNull():
                try:
                    screen = QApplication.primaryScreen()
                    if screen is not None:
                        pixmap = screen.grabWindow(int(target.winId()))
                        if pixmap is not None and not pixmap.isNull():
                            payload["method"] = "qscreen_grabwindow"
                            _append_startup_message(
                                f"QA screenshot: QScreen.grabWindow succeeded "
                                f"({pixmap.width()}x{pixmap.height()})"
                            )
                        else:
                            pixmap = None
                            _append_startup_message(
                                "QA screenshot: QScreen.grabWindow returned null, falling back"
                            )
                except Exception as _grab_exc:
                    _append_startup_message(
                        f"QA screenshot: QScreen.grabWindow raised {_grab_exc!r}, falling back"
                    )
                    pixmap = None
            if pixmap is None or pixmap.isNull():
                pixmap = target.grab()
                payload["method"] = "qt_widget_grab_fallback"
                _append_startup_message("QA screenshot: using widget.grab() fallback")
            if pixmap is None or pixmap.isNull():
                raise RuntimeError("Qt widget grab returned a null pixmap")
            target_screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            saved = bool(pixmap.save(str(target_screenshot_path), "PNG"))
            payload.update(
                {
                    "ok": saved and target_screenshot_path.is_file(),
                    "width": int(pixmap.width()),
                    "height": int(pixmap.height()),
                    "size_bytes": target_screenshot_path.stat().st_size if target_screenshot_path.is_file() else 0,
                    "ui_automation_text": "",
                }
            )
        except Exception as exc:
            payload.update({"ok": False, "error": str(exc)})
            _append_startup_message(
                "QA screenshot capture failed:\n"
                + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            )
        finally:
            _write_meta_to(target_meta_path, payload)
            _append_startup_message(
                f"QA screenshot capture completed: ok={payload.get('ok')} path={target_screenshot_path}"
            )
        return payload

    def _capture() -> None:
        if state["ok"] or screenshot_path is None or meta_path is None:
            return
        payload = _capture_to(screenshot_path, meta_path)
        try:
            if payload.get("ok"):
                state["ok"] = True
            if exit_after and payload.get("ok"):
                try:
                    qt_app.quit()
                except Exception:
                    pass
        except Exception:
            pass

    try:
        from PyQt6.QtCore import QEventLoop, QObject, QMetaObject, QTimer, Qt, pyqtSlot

        class _QAScreenshotBridge(QObject):
            @pyqtSlot()
            def capture(self) -> None:
                _capture()

            @pyqtSlot()
            def captureBatchNext(self) -> None:
                callback = getattr(qt_app, "_chaseos_qa_batch_capture_next", None)
                if callable(callback):
                    callback()

            @pyqtSlot()
            def captureBatchCurrent(self) -> None:
                callback = getattr(qt_app, "_chaseos_qa_batch_capture_current", None)
                if callable(callback):
                    callback()

        bridge = _QAScreenshotBridge()
        try:
            bridge.moveToThread(qt_app.thread())
        except Exception as exc:
            _append_startup_message(f"QA screenshot bridge thread binding failed: {exc}")
        setattr(qt_app, "_chaseos_qa_screenshot_bridge", bridge)

        batch_routes: list[dict] = []
        if batch_plan_path is not None:
            try:
                plan = json.loads(batch_plan_path.read_text(encoding="utf-8"))
                batch_routes = [item for item in plan.get("routes", []) if isinstance(item, dict)]
            except Exception as exc:
                if batch_result_path is not None:
                    _write_meta_to(
                        batch_result_path,
                        {"ok": False, "error": f"batch plan unreadable: {exc}", "routes": []},
                    )
                batch_routes = []

        if batch_routes:
            batch_state = {"index": 0, "results": [], "running": False, "done": False}

            def _write_batch_result(done: bool) -> None:
                if batch_result_path is None:
                    return
                results = list(batch_state["results"])
                _write_meta_to(
                    batch_result_path,
                    {
                        "ok": done and all(bool(item.get("ok")) for item in results) and len(results) == len(batch_routes),
                        "done": done,
                        "captured_count": len(results),
                        "expected_count": len(batch_routes),
                        "results": results,
                    },
                )

            def _coerce_batch_delay_ms(value: object, *, default: int, minimum: int = 0, maximum: int = 60000) -> int:
                try:
                    parsed = int(value)
                except (TypeError, ValueError):
                    parsed = default
                return max(minimum, min(maximum, parsed))

            def _capture_markdown_batch_action_script(payload: dict) -> str:
                payload_json = json.dumps(payload)
                return f"""
(() => {{
  const payload = {payload_json};
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  const setResult = (value) => {{ window.__CHASEOS_PACKAGED_CAPTURE_ACTION_RESULT__ = value; }};
  const byId = (id) => document.getElementById(id);
  const requireId = (id) => {{
    const element = byId(id);
    if (!element) throw new Error(`Missing element: ${{id}}`);
    return element;
  }};
  const setValue = (id, value) => {{
    const element = requireId(id);
    element.value = value;
    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
  }};
  const waitForElement = async (id, attempts = 80) => {{
    for (let index = 0; index < attempts; index += 1) {{
      const element = byId(id);
      if (element) return element;
      await sleep(100);
    }}
    throw new Error(`Timed out waiting for element: ${{id}}`);
  }};
  const waitForText = async (id, expected, attempts = 100) => {{
    for (let index = 0; index < attempts; index += 1) {{
      const element = byId(id);
      const text = element ? (element.innerText || element.textContent || '') : '';
      if (text.includes(expected)) return element;
      await sleep(100);
    }}
    const element = byId(id);
    const text = element ? (element.innerText || element.textContent || '') : '';
    throw new Error(`Timed out waiting for text ${{expected}} in ${{id}}. Current text: ${{text.slice(0, 240)}}`);
  }};

  setResult({{ ok: false, status: 'started', title: payload.title, token: payload.token }});

  (async () => {{
    try {{
      if (window.location.hash !== '#/capture-markdown') {{
        window.location.hash = '#/capture-markdown';
        window.dispatchEvent(new Event('hashchange'));
      }}
      await waitForElement('capture-markdown-title-input');
      await waitForElement('capture-markdown-preview-btn');
      await waitForElement('capture-markdown-save-btn');
      setValue('capture-markdown-title-input', payload.title || '');
      setValue('capture-markdown-raw-text', payload.raw_text || '');
      setValue('capture-markdown-source-url-input', payload.source_url || '');
      setValue('capture-markdown-intent-input', payload.user_intent || '');
      setValue('capture-markdown-summary-input', payload.generated_summary || '');
      setValue('capture-markdown-notes-text', payload.structured_notes || '');
      setValue('capture-markdown-interpretation-text', payload.generated_interpretation || '');

      requireId('capture-markdown-preview-btn').click();
      await waitForText('capture-markdown-preview-body', payload.preview_marker || payload.title || 'Capture to Markdown');
      requireId('capture-markdown-save-btn').click();
      await waitForText('capture-markdown-action-msg', payload.saved_message || 'Saved to quarantine');
      await waitForText('capture-markdown-recent-body', payload.title || '');
      const output = byId('capture-markdown-preview-body');
      if (output && output.scrollIntoView) output.scrollIntoView({{ block: 'center' }});
      await sleep(350);
      const message = byId('capture-markdown-action-msg');
      const recent = byId('capture-markdown-recent-body');
      setResult({{
        ok: true,
        status: 'saved',
        title: payload.title,
        token: payload.token,
        action_message: message ? (message.innerText || message.textContent || '') : '',
        preview_text: output ? (output.innerText || output.textContent || '').slice(0, 4000) : '',
        recent_text: recent ? (recent.innerText || recent.textContent || '').slice(0, 4000) : '',
        body_text: (document.body.innerText || document.body.textContent || '').slice(0, 8000)
      }});
    }} catch (error) {{
      setResult({{
        ok: false,
        status: 'error',
        title: payload.title,
        token: payload.token,
        error: String(error && (error.message || error)),
        body_text: (document.body.innerText || document.body.textContent || '').slice(0, 8000)
      }});
    }}
  }})();

  return {{ ok: true, started: true, title: payload.title, token: payload.token }};
}})()
""".strip()

            def _run_batch_route_script(
                script: str,
                route_id: str,
                *,
                timeout_ms: int = 5000,
                wait_for_result: bool = True,
            ) -> dict:
                try:
                    from PyQt6.QtWebEngineWidgets import QWebEngineView
                    from PyQt6.QtWidgets import QApplication

                    qt_app.processEvents()
                    views = []
                    for widget in QApplication.topLevelWidgets():
                        try:
                            views.extend(widget.findChildren(QWebEngineView))
                        except Exception:
                            continue
                    candidates = [view for view in views if view is not None and view.page() is not None]
                    if not candidates:
                        return {"ok": False, "method": "qt_webengine_runJavaScript", "error": "no_qwebengineview"}
                    target = max(candidates, key=lambda view: max(0, view.width()) * max(0, view.height()))
                    if not wait_for_result:
                        target.page().runJavaScript(script)
                        return {
                            "ok": True,
                            "method": "qt_webengine_runJavaScript",
                            "route_id": route_id,
                            "webengine_view_count": len(candidates),
                            "timed_out": False,
                            "waited_for_result": False,
                            "result": None,
                        }
                    script_state = {"done": False, "timed_out": False, "result": None}
                    loop = QEventLoop()

                    def _script_done(result: object) -> None:
                        script_state["done"] = True
                        script_state["result"] = result
                        try:
                            loop.quit()
                        except Exception:
                            pass

                    try:
                        target.page().runJavaScript(script, _script_done)
                        QTimer.singleShot(
                            _coerce_batch_delay_ms(timeout_ms, default=5000, minimum=250, maximum=60000),
                            loop.quit,
                        )
                        loop.exec()
                    except TypeError:
                        target.page().runJavaScript(script)
                        script_state["done"] = True
                    if not script_state["done"]:
                        script_state["timed_out"] = True
                    return {
                        "ok": not bool(script_state["timed_out"]),
                        "method": "qt_webengine_runJavaScript",
                        "route_id": route_id,
                        "webengine_view_count": len(candidates),
                        "timed_out": bool(script_state["timed_out"]),
                        "waited_for_result": True,
                        "result": script_state["result"],
                    }
                except Exception as exc:
                    _append_startup_message(
                        "QA batch route script failed:\n"
                        + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                    )
                    return {"ok": False, "method": "qt_webengine_runJavaScript", "error": str(exc)}

            def _capture_batch_next() -> None:
                _append_startup_message(
                    f"QA batch capture next requested: index={batch_state.get('index')} "
                    f"running={batch_state.get('running')} done={batch_state.get('done')}"
                )
                if batch_state.get("done") or batch_state.get("running"):
                    return
                batch_state["running"] = True
                index = int(batch_state["index"])
                if index >= len(batch_routes):
                    batch_state["done"] = True
                    batch_state["running"] = False
                    _write_batch_result(True)
                    if exit_after:
                        try:
                            qt_app.quit()
                        except Exception:
                            pass
                    return
                route = batch_routes[index]
                route_hash = str(route.get("hash") or "")
                route_id = str(route.get("id") or f"route-{index + 1}")
                route_title = f"ChaseOS Studio Shell - {vault_name or 'workspace'} - {_route_label_from_hash(route_hash)}"
                target_screenshot = Path(str(route.get("screenshot_path") or ""))
                target_meta = Path(str(route.get("meta_path") or target_screenshot.with_suffix(".qa-meta.json")))
                route_script_result: dict[str, object] = {}
                try:
                    if route_hash:
                        _append_startup_message(
                            f"QA batch navigating route {index + 1}/{len(batch_routes)}: {route_id} {route_hash}"
                        )
                        route_navigation_script = f"""
(function () {{
  const routeHash = {json.dumps(route_hash)};
  const panelId = String(routeHash || '').replace(/^#\\/?/, '').trim();
  let shown = false;
  let activation = null;
  if (panelId && window.__CHASEOS_STUDIO_QA_MODE__ && typeof window.__chaseosActivatePanelForQa === 'function') {{
    activation = window.__chaseosActivatePanelForQa(panelId, routeHash);
    shown = !!(activation && activation.ok);
  }} else if (panelId && typeof window.showPanel === 'function') {{
    shown = !!window.showPanel(panelId, {{ updateHash: false, deferLoad: true }});
  }}
  if (routeHash && window.location && window.location.hash !== routeHash) {{
    try {{
      window.history.replaceState(null, '', routeHash);
    }} catch (_) {{
      window.location.hash = routeHash;
    }}
  }}
  const activePanel = document.querySelector('.panel.active');
  const activePanelId = activePanel ? String(activePanel.id || '') : '';
  return {{
    ok: !!shown && activePanelId === ('panel-' + panelId),
    shown,
    activation,
    panel_id: panelId,
    active_panel_id: activePanelId,
    hash: window.location ? window.location.hash : '',
  }};
}})()
""".strip()
                        route_result = _run_batch_route_script(
                            # Activate the panel directly for deterministic
                            # packaged screenshots. Hash-only navigation can
                            # be delayed by bridge-backed route hydration, which
                            # lets subsequent captures see the previous panel.
                            route_navigation_script,
                            route_id,
                        )
                        route_script_result["navigation"] = route_result
                        route_navigation_ok = bool(route_result.get("ok")) and (
                            isinstance(route_result.get("result"), dict)
                            and route_result["result"].get("ok")
                        )
                        if route_navigation_ok:
                            _append_startup_message(f"QA batch route navigation completed: {route_id}")
                        else:
                            route_script_result["navigation_warning"] = str(
                                route_result.get("error")
                                or route_result.get("result")
                                or "route navigation callback did not confirm active panel"
                            )
                            route_script_result["navigation_fallback"] = _run_batch_route_script(
                                route_navigation_script,
                                route_id,
                                wait_for_result=False,
                            )
                            _append_startup_message(
                                f"QA batch route navigation fallback dispatched: {route_id}"
                            )
                    capture_markdown_action = (
                        route.get("capture_markdown_action")
                        if isinstance(route.get("capture_markdown_action"), dict)
                        else None
                    )
                    route_script = route.get("script") or route.get("action_script")
                    if not route_script and capture_markdown_action:
                        route_script = _capture_markdown_batch_action_script(capture_markdown_action)
                    if route_script:
                        _append_startup_message(f"QA batch running route script: {route_id}")
                        script_wait_for_result = route.get("script_wait_for_result")
                        if script_wait_for_result is None:
                            script_wait_for_result = not bool(route.get("script_fire_and_forget"))
                        start_result = _run_batch_route_script(
                            str(route_script),
                            route_id,
                            timeout_ms=_coerce_batch_delay_ms(
                                route.get("script_timeout_ms"),
                                default=5000,
                                minimum=250,
                                maximum=60000,
                            ),
                            wait_for_result=bool(script_wait_for_result),
                        )
                        route_script_result["start"] = start_result
                        if not start_result.get("ok") and bool(route.get("script_required", True)):
                            raise RuntimeError(str(start_result.get("error") or "route script failed"))
                except Exception as exc:
                    payload = {
                        "ok": False,
                        "method": "qt_widget_grab",
                        "error": f"route navigation failed: {exc}",
                        "route_id": route_id,
                        "route_hash": route_hash,
                        "screenshot_path": str(target_screenshot),
                        "meta_path": str(target_meta),
                    }
                    _write_meta_to(target_meta, payload)
                    batch_state["results"].append(payload)
                    batch_state["index"] = index + 1
                    batch_state["running"] = False
                    _write_batch_result(False)
                    QTimer.singleShot(250, _capture_batch_next)
                    return

                _route_captured = [False]

                def _capture_current_route() -> None:
                    # Guard: QTimer + thread fallback may both fire; only run once.
                    if _route_captured[0]:
                        _append_startup_message(
                            f"QA batch route already captured, skipping duplicate: {route_id}"
                        )
                        return
                    _route_captured[0] = True
                    _append_startup_message(
                        f"QA batch capturing route {index + 1}/{len(batch_routes)}: {route_id}"
                    )
                    result_script = route.get("result_script") or route.get("script_result_script")
                    if not result_script and isinstance(route.get("capture_markdown_action"), dict):
                        result_script = (
                            "JSON.parse(JSON.stringify("
                            "window.__CHASEOS_PACKAGED_CAPTURE_ACTION_RESULT__ || null"
                            "));"
                        )
                    if result_script:
                        route_script_result["final"] = _run_batch_route_script(
                            str(result_script),
                            route_id,
                            timeout_ms=_coerce_batch_delay_ms(
                                route.get("result_script_timeout_ms"),
                                default=3000,
                                minimum=250,
                                maximum=60000,
                            ),
                        )
                    payload = _capture_to(
                        target_screenshot,
                        target_meta,
                        {
                            "route_id": route_id,
                            "route_hash": route_hash,
                            "route_name": route.get("name"),
                            "window_title": route_title,
                            "route_script": route_script_result,
                        },
                    )
                    batch_state["results"].append(payload)
                    batch_state["index"] = index + 1
                    batch_state["running"] = False
                    _write_batch_result(False)
                    _append_startup_message(
                        f"QA batch route captured: {route_id} ok={payload.get('ok')}"
                    )
                    QTimer.singleShot(250, _capture_batch_next)

                setattr(qt_app, "_chaseos_qa_batch_capture_current", _capture_current_route)
                _route_delay_ms = _coerce_batch_delay_ms(
                    route.get("capture_delay_ms"), default=1000, minimum=250, maximum=300000
                )
                # Primary: QTimer in the main event loop.
                QTimer.singleShot(_route_delay_ms, _capture_current_route)
                # Fallback: background thread that fires 2 s after the QTimer should
                # have fired.  In headless/minimised Qt windows the main-loop timer can
                # be starved; the thread + QMetaObject.invokeMethod path is immune.
                if _route_delay_ms > 5000:
                    def _per_route_delay_thread(_delay_ms: int = _route_delay_ms) -> None:
                        time.sleep((_delay_ms + 2000) / 1000.0)
                        try:
                            QMetaObject.invokeMethod(
                                bridge,
                                "captureBatchCurrent",
                                Qt.ConnectionType.QueuedConnection,
                            )
                        except Exception as _prt_exc:
                            _append_startup_message(
                                f"QA per-route fallback thread failed: {_prt_exc}"
                            )
                    _prt = threading.Thread(
                        target=_per_route_delay_thread,
                        daemon=True,
                        name=f"chaseos-qa-route-delay-{route_id}",
                    )
                    _prt.start()
                    _append_startup_message(
                        f"QA batch route delay: {_route_delay_ms}ms QTimer + "
                        f"thread fallback at {_route_delay_ms + 2000}ms"
                    )

            setattr(qt_app, "_chaseos_qa_batch_capture_next", _capture_batch_next)
            QTimer.singleShot(delay_ms, _capture_batch_next)
            QTimer.singleShot(delay_ms + 2000, _capture_batch_next)

            def _trigger_batch_capture() -> None:
                time.sleep((delay_ms + 3000) / 1000)
                try:
                    QMetaObject.invokeMethod(bridge, "captureBatchNext", Qt.ConnectionType.QueuedConnection)
                except Exception as exc:
                    if batch_result_path is not None:
                        _write_meta_to(
                            batch_result_path,
                            {"ok": False, "done": False, "error": f"batch trigger failed: {exc}", "routes": []},
                        )

            batch_thread = threading.Thread(
                target=_trigger_batch_capture,
                name="chaseos-qa-batch-screenshot",
                daemon=True,
            )
            batch_thread.start()
            setattr(qt_app, "_chaseos_qa_batch_screenshot_thread", batch_thread)
            _append_startup_message(
                f"QA batch screenshot capture scheduled: routes={len(batch_routes)} delay_ms={delay_ms} plan={batch_plan_path}"
            )
            return

        QTimer.singleShot(delay_ms, _capture)
        QTimer.singleShot(delay_ms + 2000, _capture)

        def _trigger_capture() -> None:
            time.sleep((delay_ms + 3000) / 1000)
            try:
                QMetaObject.invokeMethod(bridge, "capture", Qt.ConnectionType.QueuedConnection)
            except Exception as exc:
                if meta_path is not None:
                    _write_meta_to(meta_path, {"ok": False, "method": "qt_widget_grab", "error": str(exc)})

        thread = threading.Thread(target=_trigger_capture, name="chaseos-qa-screenshot", daemon=True)
        thread.start()
        setattr(qt_app, "_chaseos_qa_screenshot_thread", thread)
        _append_startup_message(
            f"QA screenshot capture scheduled: delay_ms={delay_ms} path={screenshot_path} methods=qt_timer,queued_thread"
        )
    except Exception as exc:
        if meta_path is not None:
            _write_meta_to(meta_path, {"ok": False, "method": "qt_widget_grab", "error": str(exc)})


def main(vault_root_override: str | None = None, dev: bool = False, initial_hash: str | None = None) -> None:
    from runtime.studio.shell.config import resolve_vault_root, is_dev_mode, frontend_dir
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.file_watcher import FileWatcher

    _install_windows_safe_mkdtemp_workaround()
    _configure_qt_backend_env()

    vault_root = resolve_vault_root(vault_root_override)
    dev_mode = dev or is_dev_mode()
    webview_storage_path = _resolve_webview_storage_path(vault_root)

    api = StudioAPI(vault_root)
    route_hash = _normalize_initial_hash(initial_hash)
    html_path = (frontend_dir() / "index.html").resolve().as_uri() + route_hash

    route_label = _route_label_from_hash(route_hash)
    title = f"ChaseOS Studio Shell - {vault_root.name} - {route_label}"

    # Force Qt backend; pythonnet/WinForms is unavailable on Python 3.14.x.
    # PyQt6 + PyQt6-WebEngine provide equivalent rendering quality.
    # Create QApplication before webview does so we can attach the tray.
    # pywebview Qt backend reuses an existing QApplication.instance().
    # QtWebEngine requires AA_ShareOpenGLContexts before the application exists;
    # without it, source launches can fail and fall through to unavailable WinForms.
    _qt_app = None
    try:
        from PyQt6.QtCore import Qt, QCoreApplication
        from PyQt6.QtWidgets import QApplication

        if QApplication.instance() is None:
            QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
        _qt_app = QApplication.instance() or QApplication(sys.argv)
    except Exception as exc:
        _append_startup_message(
            "Qt backend preflight failed before pywebview start:\n"
            + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        )
        raise

    import webview
    try:
        import webview.platforms.qt  # noqa: F401
    except Exception as exc:
        _append_startup_message(
            "pywebview Qt backend import failed before start:\n"
            + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        )
        raise

    qa_mode = bool(os.environ.get(QA_SCREENSHOT_PATH_ENV) or os.environ.get(QA_BATCH_PLAN_PATH_ENV))
    window_width = _qa_window_dimension(
        QA_WINDOW_WIDTH_ENV,
        default=1400,
        minimum=900,
        maximum=2400,
    ) if qa_mode else 1400
    window_height = _qa_window_dimension(
        QA_WINDOW_HEIGHT_ENV,
        default=900,
        minimum=600,
        maximum=1600,
    ) if qa_mode else 900

    window = webview.create_window(
        title=title,
        url=html_path,
        js_api=api,
        width=window_width,
        height=window_height,
        min_size=(900, 600),
        background_color="#0f172a",
    )

    api._set_window(window)
    try:
        api.start_capture_global_hotkeys()
    except Exception as exc:
        _append_startup_message(f"Capture global hotkey startup skipped: {exc}")

    watcher = FileWatcher(vault_root)
    watcher.set_window(window)
    api._set_watcher(watcher)

    # Attach system tray; non-fatal if Qt tray APIs unavailable.
    tray_manager = None
    if _qt_app is not None:
        try:
            from runtime.studio.shell.tray import SystemTrayManager
            tray_manager = SystemTrayManager(_qt_app, window, vault_root, api)
            tray_manager.setup()
        except Exception:
            tray_manager = None  # tray is optional

    def _on_loaded() -> None:
        watcher.start()
        _append_startup_message("Studio shell loaded event fired")
        window.evaluate_js(
            f"window.__CHASEOS_VAULT_ROOT__ = {json.dumps(str(vault_root))};"
            f"window.__CHASEOS_DEV_MODE__ = {'true' if dev_mode else 'false'};"
            f"window.__CHASEOS_STUDIO_QA_MODE__ = {'true' if qa_mode else 'false'};"
            "if (typeof window.__onShellReady === 'function') { window.__onShellReady(); }"
        )
        _schedule_qa_screenshot(_qt_app, window, title=title, vault_name=vault_root.name)

    window.events.loaded += _on_loaded

    try:
        start_kwargs: dict = {"debug": dev_mode}
        if storage_path := webview_storage_path:
            start_kwargs["storage_path"] = storage_path
        webview.start(gui="qt", **start_kwargs)
    finally:
        watcher.stop()
        if tray_manager is not None:
            tray_manager.stop()


def _write_startup_exception(exc: BaseException) -> None:
    log_path = os.environ.get("CHASEOS_STUDIO_STARTUP_LOG")
    if not log_path:
        return
    try:
        path = Path(log_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            encoding="utf-8",
        )
    except Exception:
        pass


if __name__ == "__main__":
    # PyInstaller onefile EXE: QtWebEngineWidgets spawns renderer/GPU/utility
    # subprocesses using the same binary with --type=... flags. Guard against
    # starting Studio in those subprocess contexts.
    _qt_subprocess = any(
        a.startswith(("--type=", "--utility-sub-type=", "--crashpad-handler", "--no-sandbox"))
        for a in sys.argv[1:]
    )
    if not _qt_subprocess:
        args = _parse_args()
        try:
            main(vault_root_override=args.vault_root, dev=args.dev, initial_hash=args.initial_hash)
        except Exception as exc:
            _write_startup_exception(exc)
            raise
