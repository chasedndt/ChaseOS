"""Guarded local media-editor browser autonomy proof.

This module runs a real isolated browser against a ChaseOS-owned localhost
media-editor target. It is intentionally narrower than Canva/Excalidraw live
automation: no account, no external domain, no real profile, no credentials,
and no export/share/account mutation.
"""

from __future__ import annotations

import argparse
import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Protocol

from runtime.browser_runtime.cdp_live import IsolatedBrowserLauncher, MinimalCDPClient
from runtime.browser_runtime.models import slugify


MEDIA_EDITOR_AUTONOMY_PROOF_VERSION = "browser.media_editor_autonomy_proof.v1"
MEDIA_EDITOR_AUTONOMY_PROOF_RECORD_TYPE = "siteops_media_editor_browser_autonomy_proof"
MEDIA_EDITOR_AUTONOMY_PROOF_COMPLETE = "media_editor_autonomy_proof_complete"
MEDIA_EDITOR_AUTONOMY_PROOF_BLOCKED = "blocked_media_editor_autonomy_proof"
MEDIA_EDITOR_AUTONOMY_PROOF_BLOCKED_NO_EXECUTION = "blocked_media_editor_autonomy_proof_no_execution_requested"
MEDIA_EDITOR_AUTONOMY_PROOF_BLOCKED_MARKER_EXISTS = "blocked_media_editor_autonomy_proof_marker_exists"
MEDIA_EDITOR_TARGET_FILE = Path(__file__).resolve().parent / "test_targets" / "siteops_media_editor_shadow.html"
LOCAL_ALLOWED_HOSTS = {"127.0.0.1", "localhost"}
SAFE_ACTIONS = (
    "open_local_media_editor",
    "read_initial_state",
    "add_media_layer",
    "add_text_layer",
    "add_shape_layer",
    "apply_filter",
    "attempt_export_blocked",
    "attempt_account_settings_blocked",
    "capture_screenshot",
)
BLOCKED_EFFECTS = (
    "real_profile_access_attempted",
    "credential_or_cookie_read_attempted",
    "cookie_export_attempted",
    "browser_history_import_attempted",
    "public_tunnel_attempted",
    "external_navigation_attempted",
    "external_upload_attempted",
    "external_share_attempted",
    "public_publish_attempted",
    "billing_or_purchase_attempted",
    "account_mutation_attempted",
    "trusted_skill_write_attempted",
    "skill_activation_attempted",
    "canonical_writeback_attempted",
    "agent_bus_enqueue_attempted",
    "provider_call_attempted",
    "gate_mutation_attempted",
)


class QuietStaticHandler(SimpleHTTPRequestHandler):
    """HTTP handler with request logging suppressed."""

    def log_message(self, format: str, *args: Any) -> None:
        return None


class MediaEditorController(Protocol):
    """Controller surface needed by the local media-editor proof."""

    def ensure_available(self) -> dict[str, Any]:
        """Return controller readiness."""

    def open(self, url: str) -> dict[str, Any]:
        """Open the target URL."""

    def read_state(self) -> dict[str, Any]:
        """Read visible target state."""

    def click_testid(self, testid: str) -> dict[str, Any]:
        """Click one allowlisted test id."""

    def drag_testid(self, testid: str, delta_x: int, delta_y: int) -> dict[str, Any]:
        """Drag one allowlisted test id by a bounded delta."""

    def capture_screenshot(self) -> bytes:
        """Capture screenshot bytes."""

    def close(self) -> None:
        """Close the browser/session."""


class LiveCDPMediaEditorController:
    """Minimal live controller over the existing throwaway-profile CDP path."""

    def __init__(self, *, headless: bool = True) -> None:
        self.launcher = IsolatedBrowserLauncher(headless=headless)
        self.client = MinimalCDPClient()
        self.connected = False

    def ensure_available(self) -> dict[str, Any]:
        return dict(self.launcher.ensure_available())

    def open(self, url: str) -> dict[str, Any]:
        launch = dict(self.launcher.launch() or {})
        endpoint = str(launch.get("cdp_endpoint") or "")
        self.client.connect(endpoint)
        self.connected = True
        self.client.navigate(url)
        return {"opened_url": url, "profile_policy": "throwaway_only", "launch": launch}

    def read_state(self) -> dict[str, Any]:
        base = dict(self.client.read_state() or {})
        editor_state = self.client._eval(  # noqa: SLF001 - bounded local proof wrapper.
            "window.__siteopsMediaEditorState ? JSON.parse(JSON.stringify(window.__siteopsMediaEditorState)) : {}"
        )
        status_text = self.client._eval(
            "document.querySelector('[data-testid=\"status-line\"]')?.textContent || ''"
        )
        base["editor_state"] = editor_state if isinstance(editor_state, dict) else {}
        base["status_line"] = status_text
        return base

    def click_testid(self, testid: str) -> dict[str, Any]:
        expression = (
            "(() => {"
            f"const el = document.querySelector('[data-testid={json.dumps(testid)}]');"
            "if (!el) return {ok:false, reason:'selector_not_found'};"
            "el.scrollIntoView({block:'center', inline:'center'});"
            "const rect = el.getBoundingClientRect();"
            "return {ok:true, testid:"
            f"{json.dumps(testid)}"
            ", text:(el.textContent || '').trim(), x: rect.left + (rect.width / 2), y: rect.top + (rect.height / 2)};"
            "})()"
        )
        target = self.client._eval(expression)  # noqa: SLF001 - bounded local proof wrapper.
        if not isinstance(target, dict) or not target.get("ok"):
            raise RuntimeError(f"media editor click target failed for {testid}: {target}")
        self.client.click(float(target["x"]), float(target["y"]))
        result = self.client._eval(  # noqa: SLF001 - bounded local proof wrapper.
            "(() => ({ok:true, testid:"
            f"{json.dumps(testid)}"
            ", text:(document.querySelector('[data-testid="
            f"{json.dumps(testid)}"
            "]')?.textContent || '').trim(), state: JSON.parse(JSON.stringify(window.__siteopsMediaEditorState || {}))}))()"
        )
        if not isinstance(result, dict) or not result.get("ok"):
            raise RuntimeError(f"media editor click failed for {testid}: {result}")
        return result

    def drag_testid(self, testid: str, delta_x: int, delta_y: int) -> dict[str, Any]:
        expression = (
            "(() => {"
            f"const el = document.querySelector('[data-testid={json.dumps(testid)}]');"
            "if (!el) return {ok:false, reason:'selector_not_found'};"
            "el.scrollIntoView({block:'center', inline:'center'});"
            "const rect = el.getBoundingClientRect();"
            "return {ok:true, testid:"
            f"{json.dumps(testid)}"
            ", startX: rect.left + (rect.width / 2), startY: rect.top + (rect.height / 2)};"
            "})()"
        )
        target = self.client._eval(expression)  # noqa: SLF001 - bounded local proof wrapper.
        if not isinstance(target, dict) or not target.get("ok"):
            raise RuntimeError(f"media editor drag target failed for {testid}: {target}")
        start_x = float(target["startX"])
        start_y = float(target["startY"])
        self.client.drag(start_x, start_y, start_x + delta_x, start_y + delta_y)
        result = self.client._eval(  # noqa: SLF001 - bounded local proof wrapper.
            "(() => ({ok:true, testid:"
            f"{json.dumps(testid)}"
            ", deltaX:"
            f"{int(delta_x)}"
            ", deltaY:"
            f"{int(delta_y)}"
            ", state: JSON.parse(JSON.stringify(window.__siteopsMediaEditorState || {}))}))()"
        )
        if not isinstance(result, dict) or not result.get("ok"):
            raise RuntimeError(f"media editor drag failed for {testid}: {result}")
        return result

    def capture_screenshot(self) -> bytes:
        return bytes(self.client.capture_screenshot() or b"")

    def close(self) -> None:
        try:
            self.client.close()
        finally:
            self.launcher.close()


@dataclass(frozen=True)
class MediaEditorAutonomyProofRequest:
    """Request for one guarded local media-editor browser proof."""

    tenant_id: str = "local"
    workspace_id: str = "default"
    user_id: str = "local-user"
    requested_by: str = "Codex"
    operator_id: str = "local-user"
    execute_browser: bool = False
    run_slug: str = ""
    host: str = "127.0.0.1"
    port: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MediaEditorProofAction:
    """One browser action in the media-editor proof."""

    action_type: str
    target: str
    status: str
    evidence: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MediaEditorAutonomyProofResult:
    """Result for the guarded local media-editor browser proof."""

    record_type: str
    version: str
    generated_at: str
    status: str
    run_id: str
    scope: dict[str, str]
    target_url: str
    target_file: str
    request: MediaEditorAutonomyProofRequest
    actions: list[MediaEditorProofAction] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    approval_record_written: bool = False
    idempotency_marker_written: bool = False
    local_server_started: bool = False
    local_server_stopped: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    browser_actions_attempted: bool = False
    screenshot_attempted: bool = False
    browser_run_log_written: bool = False
    agent_activity_log_written: bool = False
    siteops_run_written: bool = False
    siteops_audit_written: bool = False
    screenshot_artifact_written: bool = False
    approval_record_path: str = ""
    idempotency_marker_path: str = ""
    browser_run_log_path: str = ""
    agent_activity_log_path: str = ""
    siteops_run_path: str = ""
    siteops_audit_path: str = ""
    screenshot_path: str = ""
    final_editor_state: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    denied_effects: dict[str, bool] = field(default_factory=dict)
    next_step: str = "review_media_editor_browser_proof"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict()
        payload["actions"] = [action.as_dict() for action in self.actions]
        return payload

    def validate(self) -> None:
        if self.scope.get("tenant_id") == "" or self.scope.get("user_id") == "":
            raise ValueError("tenant_id and user_id are required")
        for effect in BLOCKED_EFFECTS:
            if self.denied_effects.get(effect) is not False:
                raise ValueError(f"{effect} must remain false")
        if self.status == MEDIA_EDITOR_AUTONOMY_PROOF_COMPLETE:
            if not self.approval_record_written or not self.idempotency_marker_written:
                raise ValueError("complete proof requires approval and marker records")
            if not self.browser_run_log_written or not self.agent_activity_log_written:
                raise ValueError("complete proof requires browser run and activity logs")
            if self.final_editor_state.get("exportBlocked") is not True:
                raise ValueError("complete proof must show export was blocked")
            if self.final_editor_state.get("accountSettingsBlocked") is not True:
                raise ValueError("complete proof must show account settings were blocked")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _scope(request: MediaEditorAutonomyProofRequest) -> dict[str, str]:
    return {
        "tenant_id": request.tenant_id,
        "workspace_id": request.workspace_id,
        "user_id": request.user_id,
    }


def _run_id(request: MediaEditorAutonomyProofRequest, timestamp: str) -> str:
    if request.run_slug:
        return slugify(request.run_slug, "media-editor-autonomy-proof")
    stamp = timestamp.replace(":", "").replace("+00:00", "Z")
    return "siteops-media-editor-autonomy-proof-" + slugify(stamp, "time")


def _scoped_dir(vault: Path, request: MediaEditorAutonomyProofRequest, *parts: str) -> Path:
    return vault.joinpath(*parts, request.tenant_id, request.workspace_id)


def _artifact_paths(vault: Path, request: MediaEditorAutonomyProofRequest, run_id: str) -> dict[str, Path]:
    browser_root = _scoped_dir(vault, request, "07_LOGS", "Browser-Runs")
    return {
        "approval": _scoped_dir(vault, request, "07_LOGS", "SiteOps-Approvals")
        / f"approval_{run_id}.json",
        "marker": browser_root / "_media-editor-autonomy-markers" / f"{run_id}.json",
        "browser_run": browser_root / f"{run_id}.json",
        "screenshot": browser_root / f"{run_id}.png",
        "agent_activity": _scoped_dir(vault, request, "07_LOGS", "Agent-Activity")
        / f"2026-05-04-{run_id}.md",
        "siteops_run": _scoped_dir(vault, request, "07_LOGS", "SiteOps-Runs") / f"{run_id}.json",
        "siteops_audit": _scoped_dir(vault, request, "07_LOGS", "SiteOps-Audits") / f"{run_id}.jsonl",
    }


def _safe_write_json_create_new(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")


def _write_activity(path: Path, result_payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "runtime: Codex",
        "activity_type: siteops-media-editor-autonomy-proof",
        f"status: {result_payload.get('status')}",
        f"run_id: {result_payload.get('run_id')}",
        "---",
        "",
        "# SiteOps Media Editor Browser Autonomy Proof",
        "",
        "## Evidence",
        f"- Browser run: `{result_payload.get('browser_run_log_path')}`",
        f"- Screenshot: `{result_payload.get('screenshot_path')}`",
        f"- SiteOps run: `{result_payload.get('siteops_run_path')}`",
        f"- SiteOps audit: `{result_payload.get('siteops_audit_path')}`",
        "",
        "## Boundary",
        "- Local localhost media-editor target only.",
        "- Throwaway browser profile only.",
        "- No real account, credentials, cookies, uploads, export, share, billing, or account mutation.",
        "- No trusted skill activation, Gate mutation, Agent Bus enqueue, provider call, or canonical writeback.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _serve_target(host: str, port: int) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    if not MEDIA_EDITOR_TARGET_FILE.exists():
        raise RuntimeError(f"media editor target file missing: {MEDIA_EDITOR_TARGET_FILE}")
    handler = partial(QuietStaticHandler, directory=str(MEDIA_EDITOR_TARGET_FILE.parent))
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, name="siteops-media-editor-target", daemon=True)
    thread.start()
    actual_port = int(server.server_address[1])
    return server, thread, f"http://{host}:{actual_port}/{MEDIA_EDITOR_TARGET_FILE.name}"


def _execute_media_editor_flow(controller: MediaEditorController, target_url: str) -> tuple[list[MediaEditorProofAction], bytes, dict[str, Any]]:
    actions: list[MediaEditorProofAction] = []
    actions.append(MediaEditorProofAction("open_local_media_editor", target_url, "succeeded", controller.open(target_url)))
    initial_state = controller.read_state()
    actions.append(MediaEditorProofAction("read_initial_state", "window.__siteopsMediaEditorState", "succeeded", initial_state))
    for action_type, testid in (
        ("add_media_layer", "add-media-layer"),
        ("add_text_layer", "add-text-layer"),
        ("add_shape_layer", "add-shape-layer"),
        ("apply_filter", "apply-filter"),
    ):
        actions.append(MediaEditorProofAction(action_type, testid, "succeeded", controller.click_testid(testid)))
    export_evidence = controller.click_testid("export-file")
    actions.append(MediaEditorProofAction("attempt_export_blocked", "export-file", "blocked_expected", export_evidence))
    account_evidence = controller.click_testid("account-settings")
    actions.append(MediaEditorProofAction("attempt_account_settings_blocked", "account-settings", "blocked_expected", account_evidence))
    screenshot = controller.capture_screenshot()
    actions.append(
        MediaEditorProofAction(
            "capture_screenshot",
            "visible viewport",
            "succeeded",
            {"screenshot_bytes": len(screenshot)},
        )
    )
    final_state = controller.read_state()
    editor_state = final_state.get("editor_state")
    return actions, screenshot, editor_state if isinstance(editor_state, dict) else {}


def run_media_editor_autonomy_proof(
    vault_root: str | Path,
    request: MediaEditorAutonomyProofRequest,
    *,
    generated_at: str | None = None,
    controller: MediaEditorController | None = None,
) -> MediaEditorAutonomyProofResult:
    """Run one guarded local media-editor browser proof."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    run_id = _run_id(request, timestamp)
    scope = _scope(request)
    target_url = ""
    paths = _artifact_paths(vault, request, run_id)
    blockers: list[str] = []
    if not request.tenant_id:
        blockers.append("tenant_id_missing")
    if not request.user_id:
        blockers.append("user_id_missing")
    if request.host not in LOCAL_ALLOWED_HOSTS:
        blockers.append("target_host_not_local")
    if not request.execute_browser:
        blockers.append("execute_browser_false")
    if paths["marker"].exists() or paths["approval"].exists() or paths["browser_run"].exists():
        blockers.append("idempotency_or_run_artifact_exists")
    if blockers:
        status = (
            MEDIA_EDITOR_AUTONOMY_PROOF_BLOCKED_NO_EXECUTION
            if blockers == ["execute_browser_false"]
            else (
                MEDIA_EDITOR_AUTONOMY_PROOF_BLOCKED_MARKER_EXISTS
                if "idempotency_or_run_artifact_exists" in blockers
                else MEDIA_EDITOR_AUTONOMY_PROOF_BLOCKED
            )
        )
        result = MediaEditorAutonomyProofResult(
            record_type=MEDIA_EDITOR_AUTONOMY_PROOF_RECORD_TYPE,
            version=MEDIA_EDITOR_AUTONOMY_PROOF_VERSION,
            generated_at=timestamp,
            status=status,
            run_id=run_id,
            scope=scope,
            target_url=target_url,
            target_file=MEDIA_EDITOR_TARGET_FILE.as_posix(),
            request=request,
            blockers=blockers,
            approval_record_path=paths["approval"].as_posix(),
            idempotency_marker_path=paths["marker"].as_posix(),
            denied_effects={effect: False for effect in BLOCKED_EFFECTS},
            next_step="repair_or_explicitly_execute_media_editor_autonomy_proof",
        )
        result.validate()
        return result

    live_controller = controller or LiveCDPMediaEditorController()
    try:
        live_controller.ensure_available()
    except Exception as exc:
        result = MediaEditorAutonomyProofResult(
            record_type=MEDIA_EDITOR_AUTONOMY_PROOF_RECORD_TYPE,
            version=MEDIA_EDITOR_AUTONOMY_PROOF_VERSION,
            generated_at=timestamp,
            status=MEDIA_EDITOR_AUTONOMY_PROOF_BLOCKED,
            run_id=run_id,
            scope=scope,
            target_url=target_url,
            target_file=MEDIA_EDITOR_TARGET_FILE.as_posix(),
            request=request,
            blockers=["browser_controller_unavailable"],
            error=str(exc),
            denied_effects={effect: False for effect in BLOCKED_EFFECTS},
            next_step="configure_local_throwaway_browser",
        )
        result.validate()
        return result

    server: ThreadingHTTPServer | None = None
    thread: threading.Thread | None = None
    server_started = False
    server_stopped = False
    actions: list[MediaEditorProofAction] = []
    screenshot = b""
    final_state: dict[str, Any] = {}
    error = ""
    _safe_write_json_create_new(
        paths["approval"],
        {
            "record_type": "siteops_media_editor_autonomy_proof_approval",
            "schema_version": MEDIA_EDITOR_AUTONOMY_PROOF_VERSION,
            "status": "approved_for_single_local_throwaway_browser_trial",
            "approved_by": request.operator_id,
            "approved_at": timestamp,
            "scope": scope,
            "run_id": run_id,
            "target": "local media editor sandbox",
            "allow_real_profile": False,
            "allow_credentials": False,
            "allow_export": False,
            "allow_external_share": False,
            "allow_account_mutation": False,
            "canonical_writeback_allowed": False,
        },
    )
    _safe_write_json_create_new(
        paths["marker"],
        {
            "record_type": "siteops_media_editor_autonomy_proof_idempotency_marker",
            "schema_version": MEDIA_EDITOR_AUTONOMY_PROOF_VERSION,
            "status": "reserved_before_browser_launch",
            "reserved_at": timestamp,
            "scope": scope,
            "run_id": run_id,
        },
    )
    try:
        server, thread, target_url = _serve_target(request.host, request.port)
        server_started = True
        actions, screenshot, final_state = _execute_media_editor_flow(live_controller, target_url)
    except Exception as exc:
        error = str(exc)
    finally:
        try:
            live_controller.close()
        except Exception:
            pass
        if server is not None:
            server.shutdown()
            server.server_close()
            server_stopped = True
        if thread is not None:
            thread.join(timeout=2)

    completed = not error
    status = MEDIA_EDITOR_AUTONOMY_PROOF_COMPLETE if completed else MEDIA_EDITOR_AUTONOMY_PROOF_BLOCKED
    if completed:
        paths["screenshot"].write_bytes(screenshot)

    result = MediaEditorAutonomyProofResult(
        record_type=MEDIA_EDITOR_AUTONOMY_PROOF_RECORD_TYPE,
        version=MEDIA_EDITOR_AUTONOMY_PROOF_VERSION,
        generated_at=timestamp,
        status=status,
        run_id=run_id,
        scope=scope,
        target_url=target_url,
        target_file=MEDIA_EDITOR_TARGET_FILE.as_posix(),
        request=request,
        actions=actions,
        blockers=[] if completed else ["media_editor_browser_flow_failed"],
        approval_record_written=True,
        idempotency_marker_written=True,
        local_server_started=server_started,
        local_server_stopped=server_stopped,
        browser_launch_attempted=True,
        cdp_connection_attempted=True,
        browser_actions_attempted=True,
        screenshot_attempted=completed,
        browser_run_log_written=True,
        agent_activity_log_written=completed,
        siteops_run_written=True,
        siteops_audit_written=True,
        screenshot_artifact_written=completed,
        approval_record_path=paths["approval"].as_posix(),
        idempotency_marker_path=paths["marker"].as_posix(),
        browser_run_log_path=paths["browser_run"].as_posix(),
        agent_activity_log_path=paths["agent_activity"].as_posix() if completed else "",
        siteops_run_path=paths["siteops_run"].as_posix(),
        siteops_audit_path=paths["siteops_audit"].as_posix(),
        screenshot_path=paths["screenshot"].as_posix() if completed else "",
        final_editor_state=final_state,
        error=error,
        denied_effects={effect: False for effect in BLOCKED_EFFECTS},
        next_step="review_media_editor_browser_autonomy_proof" if completed else "inspect_failed_media_editor_proof",
    )
    result.validate()

    payload = result.as_dict()
    _write_json(paths["browser_run"], payload)
    _write_json(
        paths["siteops_run"],
        {
            "record_type": "siteops_run",
            "run_id": run_id,
            "tenant_id": request.tenant_id,
            "workspace_id": request.workspace_id,
            "user_id": request.user_id,
            "mode": "local_browser_autonomy_proof",
            "status": "succeeded" if completed else "failed",
            "browser_run_ref": paths["browser_run"].as_posix(),
            "screenshot_ref": paths["screenshot"].as_posix() if completed else "",
            "canonical_writeback_allowed": False,
        },
    )
    _write_jsonl(
        paths["siteops_audit"],
        [
            {
                "event_type": "media_editor_autonomy_proof_started",
                "timestamp": timestamp,
                "run_id": run_id,
                "scope": scope,
                "policy_decision": "allow_local_throwaway_browser_only",
            },
            {
                "event_type": "media_editor_autonomy_proof_completed" if completed else "media_editor_autonomy_proof_failed",
                "timestamp": _now_utc(),
                "run_id": run_id,
                "scope": scope,
                "policy_decision": "blocked_external_export_share_account_mutation",
                "denied_effects": {effect: False for effect in BLOCKED_EFFECTS},
            },
        ],
    )
    if completed:
        _write_activity(paths["agent_activity"], payload)
    marker = json.loads(paths["marker"].read_text(encoding="utf-8"))
    marker.update(
        {
            "status": "completed" if completed else "failed",
            "target_url": target_url,
            "browser_run_log_path": paths["browser_run"].as_posix(),
            "completed_at": _now_utc() if completed else None,
            "failed_at": _now_utc() if not completed else None,
        }
    )
    paths["marker"].write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a guarded local media-editor browser autonomy proof.")
    parser.add_argument("--vault-root", default=".")
    parser.add_argument("--tenant", default="local")
    parser.add_argument("--workspace", default="default")
    parser.add_argument("--user", default="local-user")
    parser.add_argument("--requested-by", default="Codex")
    parser.add_argument("--operator-id", default="local-user")
    parser.add_argument("--execute-browser", action="store_true")
    parser.add_argument("--run-slug", default="")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = run_media_editor_autonomy_proof(
        args.vault_root,
        MediaEditorAutonomyProofRequest(
            tenant_id=args.tenant,
            workspace_id=args.workspace,
            user_id=args.user,
            requested_by=args.requested_by,
            operator_id=args.operator_id,
            execute_browser=args.execute_browser,
            run_slug=args.run_slug,
            host=args.host,
            port=args.port,
        ),
    )
    payload = result.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {result.status}")
        print(f"run_id: {result.run_id}")
        print(f"browser_run_log_path: {result.browser_run_log_path}")
        print(f"screenshot_path: {result.screenshot_path}")
    return 0 if result.status == MEDIA_EDITOR_AUTONOMY_PROOF_COMPLETE else 2


if __name__ == "__main__":
    raise SystemExit(main())
