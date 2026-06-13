"""Guarded local Canva-style browser autonomy proof."""

from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from runtime.browser_runtime.media_editor_autonomy_proof import (
    BLOCKED_EFFECTS,
    LiveCDPMediaEditorController,
    MediaEditorController,
    MediaEditorProofAction,
)
from runtime.browser_runtime.models import slugify


CANVA_STYLE_AUTONOMY_PROOF_VERSION = "browser.canva_style_autonomy_proof.v1"
CANVA_STYLE_AUTONOMY_PROOF_RECORD_TYPE = "siteops_canva_style_browser_autonomy_proof"
CANVA_STYLE_AUTONOMY_PROOF_COMPLETE = "canva_style_autonomy_proof_complete"
CANVA_STYLE_AUTONOMY_PROOF_BLOCKED = "blocked_canva_style_autonomy_proof"
CANVA_STYLE_AUTONOMY_PROOF_BLOCKED_NO_EXECUTION = "blocked_canva_style_autonomy_proof_no_execution_requested"
CANVA_STYLE_AUTONOMY_PROOF_BLOCKED_MARKER_EXISTS = "blocked_canva_style_autonomy_proof_marker_exists"
CANVA_STYLE_TARGET_FILE = Path(__file__).resolve().parent / "test_targets" / "siteops_canva_style_shadow.html"
LOCAL_ALLOWED_HOSTS = {"127.0.0.1", "localhost"}


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return None


@dataclass(frozen=True)
class CanvaStyleAutonomyProofRequest:
    tenant_id: str = "local"
    workspace_id: str = "default"
    user_id: str = "local-user"
    requested_by: str = "Codex"
    operator_id: str = "local-user"
    execute_browser: bool = False
    run_slug: str = ""
    host: str = "127.0.0.1"
    port: int = 0
    headed_browser: bool = False
    action_delay_ms: int = 0
    final_pause_seconds: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CanvaStyleAutonomyProofResult:
    record_type: str
    version: str
    generated_at: str
    status: str
    run_id: str
    scope: dict[str, str]
    target_url: str
    target_file: str
    request: CanvaStyleAutonomyProofRequest
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
    final_design_state: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    denied_effects: dict[str, bool] = field(default_factory=dict)
    next_step: str = "review_canva_style_browser_proof"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict()
        payload["actions"] = [action.as_dict() for action in self.actions]
        return payload

    def validate(self) -> None:
        if not self.scope.get("tenant_id") or not self.scope.get("user_id"):
            raise ValueError("tenant_id and user_id are required")
        for effect in BLOCKED_EFFECTS:
            if self.denied_effects.get(effect) is not False:
                raise ValueError(f"{effect} must remain false")
        if self.status == CANVA_STYLE_AUTONOMY_PROOF_COMPLETE:
            required = (
                "templateSelected",
                "canvasCleared",
                "fakeAssetsLoaded",
                "photoLayerAdded",
                "photoFrameAdded",
                "photoFrameResized",
                "circleFeatureAdded",
                "penDrawingEnabled",
                "manualDrawingAdded",
                "magicLayersCreated",
                "brandApplied",
                "resizeApplied",
                "exportBlocked",
                "publicShareBlocked",
                "accountSettingsBlocked",
                "agentControlVisible",
                "agentCursorMoved",
                "agentClickFeedbackShown",
                "agentDragFeedbackShown",
            )
            missing = [key for key in required if self.final_design_state.get(key) is not True]
            if missing:
                raise ValueError("complete proof missing final state flags: " + ", ".join(missing))
            if self.final_design_state.get("agentControlLane") != "browser":
                raise ValueError("complete proof requires browser agent-control lane")
            frame_size = self.final_design_state.get("photoFrameSize")
            if not isinstance(frame_size, dict):
                raise ValueError("complete proof missing photoFrameSize")
            if int(frame_size.get("width") or 0) < 180 or int(frame_size.get("height") or 0) < 150:
                raise ValueError("complete proof requires manually resized photo frame")
            if int(self.final_design_state.get("manualDrawingPointCount") or 0) < 3:
                raise ValueError("complete proof requires a manual browser drawing path")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_id(request: CanvaStyleAutonomyProofRequest, timestamp: str) -> str:
    if request.run_slug:
        return slugify(request.run_slug, "canva-style-autonomy-proof")
    return "siteops-canva-style-autonomy-proof-" + slugify(timestamp, "time")


def _scope(request: CanvaStyleAutonomyProofRequest) -> dict[str, str]:
    return {"tenant_id": request.tenant_id, "workspace_id": request.workspace_id, "user_id": request.user_id}


def _scoped_dir(vault: Path, request: CanvaStyleAutonomyProofRequest, *parts: str) -> Path:
    return vault.joinpath(*parts, request.tenant_id, request.workspace_id)


def _artifact_paths(vault: Path, request: CanvaStyleAutonomyProofRequest, run_id: str) -> dict[str, Path]:
    browser_root = _scoped_dir(vault, request, "07_LOGS", "Browser-Runs")
    return {
        "approval": _scoped_dir(vault, request, "07_LOGS", "SiteOps-Approvals") / f"approval_{run_id}.json",
        "marker": browser_root / "_canva-style-autonomy-markers" / f"{run_id}.json",
        "browser_run": browser_root / f"{run_id}.json",
        "screenshot": browser_root / f"{run_id}.png",
        "agent_activity": _scoped_dir(vault, request, "07_LOGS", "Agent-Activity") / f"2026-05-04-{run_id}.md",
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


def _write_activity(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "runtime: Codex",
        "activity_type: siteops-canva-style-autonomy-proof",
        f"status: {payload.get('status')}",
        f"run_id: {payload.get('run_id')}",
        "---",
        "",
        "# SiteOps Canva Style Browser Autonomy Proof",
        "",
        f"- Browser run: `{payload.get('browser_run_log_path')}`",
        f"- Screenshot: `{payload.get('screenshot_path')}`",
        f"- SiteOps run: `{payload.get('siteops_run_path')}`",
        f"- SiteOps audit: `{payload.get('siteops_audit_path')}`",
        "- No Canva account, real profile, credentials, export, public share, billing, or account mutation.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _serve_target(host: str, port: int) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    if not CANVA_STYLE_TARGET_FILE.exists():
        raise RuntimeError(f"Canva-style target missing: {CANVA_STYLE_TARGET_FILE}")
    handler = partial(QuietStaticHandler, directory=str(CANVA_STYLE_TARGET_FILE.parent))
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, name="siteops-canva-style-target", daemon=True)
    thread.start()
    return server, thread, f"http://{host}:{int(server.server_address[1])}/{CANVA_STYLE_TARGET_FILE.name}"


def _append_action(
    actions: list[MediaEditorProofAction],
    action: MediaEditorProofAction,
    *,
    delay_ms: int,
) -> None:
    actions.append(action)
    if delay_ms > 0:
        time.sleep(delay_ms / 1000)


def _execute_flow(
    controller: MediaEditorController,
    target_url: str,
    *,
    action_delay_ms: int = 0,
    final_pause_seconds: int = 0,
) -> tuple[list[MediaEditorProofAction], bytes, dict[str, Any]]:
    actions: list[MediaEditorProofAction] = [
        MediaEditorProofAction("open_canva_style_editor", target_url, "succeeded", controller.open(target_url)),
        MediaEditorProofAction("read_initial_state", "window.__siteopsMediaEditorState", "succeeded", controller.read_state()),
    ]
    for action_type, testid in (
        ("dirty_canvas_before_clear", "select-poster-template"),
        ("dirty_canvas_assets_before_clear", "load-fake-assets"),
        ("clear_canvas", "clear-canvas"),
    ):
        _append_action(
            actions,
            MediaEditorProofAction(action_type, testid, "succeeded", controller.click_testid(testid)),
            delay_ms=action_delay_ms,
        )
    _append_action(
        actions,
        MediaEditorProofAction("read_cleared_state", "window.__siteopsMediaEditorState", "succeeded", controller.read_state()),
        delay_ms=action_delay_ms,
    )
    for action_type, testid in (
        ("select_poster_template", "select-poster-template"),
        ("load_fake_assets", "load-fake-assets"),
        ("add_photo_layer", "add-photo-placeholder"),
        ("add_photo_frame", "add-photo-frame"),
        ("draw_feature_circle", "add-feature-circle"),
        ("enable_pen_drawing", "enable-pen-drawing"),
        ("run_magic_layers", "run-magic-layers"),
        ("apply_brand_kit", "apply-brand-kit"),
        ("resize_social", "resize-social"),
    ):
        _append_action(
            actions,
            MediaEditorProofAction(action_type, testid, "succeeded", controller.click_testid(testid)),
            delay_ms=action_delay_ms,
        )
    _append_action(
        actions,
        MediaEditorProofAction(
            "manual_resize_photo_frame",
            "photo-frame-resize-handle",
            "succeeded",
            controller.drag_testid("photo-frame-resize-handle", 88, 52),
        ),
        delay_ms=action_delay_ms,
    )
    _append_action(
        actions,
        MediaEditorProofAction(
            "manual_draw_poster_swoosh",
            "poster-drawing-surface",
            "succeeded",
            controller.drag_testid("poster-drawing-surface", 120, -48),
        ),
        delay_ms=action_delay_ms,
    )
    _append_action(
        actions,
        MediaEditorProofAction("attempt_export_blocked", "export-file", "blocked_expected", controller.click_testid("export-file")),
        delay_ms=action_delay_ms,
    )
    _append_action(
        actions,
        MediaEditorProofAction("attempt_public_share_blocked", "public-share", "blocked_expected", controller.click_testid("public-share")),
        delay_ms=action_delay_ms,
    )
    _append_action(
        actions,
        MediaEditorProofAction(
            "attempt_account_settings_blocked",
            "account-settings",
            "blocked_expected",
            controller.click_testid("account-settings"),
        ),
        delay_ms=action_delay_ms,
    )
    if final_pause_seconds > 0:
        time.sleep(final_pause_seconds)
    screenshot = controller.capture_screenshot()
    actions.append(MediaEditorProofAction("capture_screenshot", "visible viewport", "succeeded", {"screenshot_bytes": len(screenshot)}))
    state = controller.read_state().get("editor_state")
    return actions, screenshot, state if isinstance(state, dict) else {}


def run_canva_style_autonomy_proof(
    vault_root: str | Path,
    request: CanvaStyleAutonomyProofRequest,
    *,
    generated_at: str | None = None,
    controller: MediaEditorController | None = None,
) -> CanvaStyleAutonomyProofResult:
    timestamp = generated_at or _now_utc()
    vault = Path(vault_root).resolve()
    run_id = _run_id(request, timestamp)
    scope = _scope(request)
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
            CANVA_STYLE_AUTONOMY_PROOF_BLOCKED_NO_EXECUTION
            if blockers == ["execute_browser_false"]
            else CANVA_STYLE_AUTONOMY_PROOF_BLOCKED_MARKER_EXISTS
            if "idempotency_or_run_artifact_exists" in blockers
            else CANVA_STYLE_AUTONOMY_PROOF_BLOCKED
        )
        result = CanvaStyleAutonomyProofResult(
            record_type=CANVA_STYLE_AUTONOMY_PROOF_RECORD_TYPE,
            version=CANVA_STYLE_AUTONOMY_PROOF_VERSION,
            generated_at=timestamp,
            status=status,
            run_id=run_id,
            scope=scope,
            target_url="",
            target_file=CANVA_STYLE_TARGET_FILE.as_posix(),
            request=request,
            blockers=blockers,
            approval_record_path=paths["approval"].as_posix(),
            idempotency_marker_path=paths["marker"].as_posix(),
            denied_effects={effect: False for effect in BLOCKED_EFFECTS},
            next_step="repair_or_execute_canva_style_autonomy_proof",
        )
        result.validate()
        return result

    live_controller = controller or LiveCDPMediaEditorController(headless=not request.headed_browser)
    try:
        live_controller.ensure_available()
    except Exception as exc:
        result = CanvaStyleAutonomyProofResult(
            record_type=CANVA_STYLE_AUTONOMY_PROOF_RECORD_TYPE,
            version=CANVA_STYLE_AUTONOMY_PROOF_VERSION,
            generated_at=timestamp,
            status=CANVA_STYLE_AUTONOMY_PROOF_BLOCKED,
            run_id=run_id,
            scope=scope,
            target_url="",
            target_file=CANVA_STYLE_TARGET_FILE.as_posix(),
            request=request,
            blockers=["browser_controller_unavailable"],
            error=str(exc),
            denied_effects={effect: False for effect in BLOCKED_EFFECTS},
            next_step="configure_local_throwaway_browser",
        )
        result.validate()
        return result

    _safe_write_json_create_new(
        paths["approval"],
        {
            "record_type": "siteops_canva_style_autonomy_proof_approval",
            "schema_version": CANVA_STYLE_AUTONOMY_PROOF_VERSION,
            "status": "approved_for_single_local_throwaway_browser_trial",
            "approved_by": request.operator_id,
            "approved_at": timestamp,
            "scope": scope,
            "run_id": run_id,
            "allow_real_profile": False,
            "allow_credentials": False,
            "allow_export": False,
            "allow_public_share": False,
            "allow_account_mutation": False,
            "canonical_writeback_allowed": False,
        },
    )
    _safe_write_json_create_new(
        paths["marker"],
        {
            "record_type": "siteops_canva_style_autonomy_proof_idempotency_marker",
            "schema_version": CANVA_STYLE_AUTONOMY_PROOF_VERSION,
            "status": "reserved_before_browser_launch",
            "reserved_at": timestamp,
            "scope": scope,
            "run_id": run_id,
        },
    )
    server: ThreadingHTTPServer | None = None
    thread: threading.Thread | None = None
    target_url = ""
    actions: list[MediaEditorProofAction] = []
    screenshot = b""
    final_state: dict[str, Any] = {}
    error = ""
    server_started = False
    server_stopped = False
    try:
        server, thread, target_url = _serve_target(request.host, request.port)
        server_started = True
        actions, screenshot, final_state = _execute_flow(
            live_controller,
            target_url,
            action_delay_ms=request.action_delay_ms,
            final_pause_seconds=request.final_pause_seconds,
        )
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
    status = CANVA_STYLE_AUTONOMY_PROOF_COMPLETE if completed else CANVA_STYLE_AUTONOMY_PROOF_BLOCKED
    if completed:
        paths["screenshot"].write_bytes(screenshot)
    result = CanvaStyleAutonomyProofResult(
        record_type=CANVA_STYLE_AUTONOMY_PROOF_RECORD_TYPE,
        version=CANVA_STYLE_AUTONOMY_PROOF_VERSION,
        generated_at=timestamp,
        status=status,
        run_id=run_id,
        scope=scope,
        target_url=target_url,
        target_file=CANVA_STYLE_TARGET_FILE.as_posix(),
        request=request,
        actions=actions,
        blockers=[] if completed else ["canva_style_browser_flow_failed"],
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
        final_design_state=final_state,
        error=error,
        denied_effects={effect: False for effect in BLOCKED_EFFECTS},
        next_step="review_canva_style_browser_autonomy_proof" if completed else "inspect_failed_canva_style_proof",
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
            "mode": "local_canva_style_browser_autonomy_proof",
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
                "event_type": "canva_style_autonomy_proof_started",
                "timestamp": timestamp,
                "run_id": run_id,
                "scope": scope,
                "policy_decision": "allow_local_throwaway_browser_only",
            },
            {
                "event_type": "canva_style_autonomy_proof_completed" if completed else "canva_style_autonomy_proof_failed",
                "timestamp": _now_utc(),
                "run_id": run_id,
                "scope": scope,
                "policy_decision": "blocked_export_public_share_account_mutation",
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
    parser = argparse.ArgumentParser(description="Run a guarded local Canva-style browser autonomy proof.")
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
    parser.add_argument("--headed-browser", action="store_true")
    parser.add_argument("--action-delay-ms", type=int, default=0)
    parser.add_argument("--final-pause-seconds", type=int, default=0)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_canva_style_autonomy_proof(
        args.vault_root,
        CanvaStyleAutonomyProofRequest(
            tenant_id=args.tenant,
            workspace_id=args.workspace,
            user_id=args.user,
            requested_by=args.requested_by,
            operator_id=args.operator_id,
            execute_browser=args.execute_browser,
            run_slug=args.run_slug,
            host=args.host,
            port=args.port,
            headed_browser=args.headed_browser,
            action_delay_ms=args.action_delay_ms,
            final_pause_seconds=args.final_pause_seconds,
        ),
    )
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(f"status: {result.status}")
        print(f"run_id: {result.run_id}")
        print(f"browser_run_log_path: {result.browser_run_log_path}")
        print(f"screenshot_path: {result.screenshot_path}")
    return 0 if result.status == CANVA_STYLE_AUTONOMY_PROOF_COMPLETE else 2


if __name__ == "__main__":
    raise SystemExit(main())
