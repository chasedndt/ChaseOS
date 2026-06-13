"""Localhost-only manual test app for Studio Chat schedule controls.

This app is a browser compatibility harness for the native Studio Chat
schedule-control chain. It calls the same StudioAPI methods as the native Chat
panel and keeps the same boundary: local proposal/approval/schedule/export
artifacts only, no external scheduler, Discord, provider, or runtime dispatch.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Lock, Thread
from time import monotonic
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from runtime.studio.phase11_chat_schedule_ui_action_controls_and_readback import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_chat_schedule_ui_action_controls_and_readback,
)
from runtime.studio.shell.api import StudioAPI


SURFACE_ID = "phase11_chat_schedule_manual_test_app"
MODEL_VERSION = "studio.phase11_chat_schedule_manual_test_app.v1"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8791
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
SECRET_INDICATORS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DISCORD_TOKEN",
    "BOT_TOKEN",
    "WEBHOOK_URL",
    "sk-",
    "xoxb-",
    "-----BEGIN",
)


class ScheduleManualTestAppError(RuntimeError):
    """Raised when the schedule manual test app cannot proceed safely."""


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path | None = None) -> Path:
    return Path(vault_root or Path.cwd()).expanduser().resolve()


def _require_loopback(host: str) -> None:
    if host not in LOOPBACK_HOSTS:
        raise ScheduleManualTestAppError("schedule manual test app only binds to loopback hosts")


def _contains_secret_indicator(value: Any) -> bool:
    if isinstance(value, str):
        upper = value.upper()
        return any(marker.upper() in upper for marker in SECRET_INDICATORS)
    if isinstance(value, dict):
        return any(_contains_secret_indicator(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_secret_indicator(item) for item in value)
    return False


def _json_response(ok: bool, surface: str, data: dict[str, Any] | None = None, *, code: str | None = None, message: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": ok,
        "surface": surface,
        "generated_at_utc": _now_utc(),
    }
    if data is not None:
        payload["data"] = data
    if not ok:
        payload["error"] = {"code": code or "schedule_manual_test_app_error", "message": message or "request failed"}
    return payload


def build_schedule_manual_test_app_plan(
    vault_root: str | Path,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> dict[str, Any]:
    """Return a no-mutation manual-test app plan."""

    _require_loopback(host)
    vault = _vault_path(vault_root)
    readback = build_phase11_chat_schedule_ui_action_controls_and_readback(vault)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": "READY / LOCALHOST MANUAL TEST APP",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "host": host,
        "port": int(port),
        "url": f"http://{host}:{int(port)}/",
        "health_url": f"http://{host}:{int(port)}/health.json",
        "readback_url": f"http://{host}:{int(port)}/api/readback",
        "action_url": f"http://{host}:{int(port)}/api/action",
        "manual_ui_test_ready": True,
        "readback_ready": True,
        "local_only": True,
        "authority": {
            "binds_loopback_only": True,
            "uses_existing_studio_api_methods": True,
            "secret_fields_rendered": False,
            "secret_indicator_guard_enabled": True,
            "schedule_proposal_approval_queue_write_allowed_with_digest": True,
            "approved_schedule_proposal_consumption_allowed": True,
            "approved_schedule_intent_write_allowed": True,
            "approved_schedule_activation_allowed": True,
            "approved_adapter_export_packet_write_allowed": True,
            "external_scheduler_mutation_allowed": False,
            "openclaw_cron_mutation_allowed": False,
            "hermes_cron_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_dispatch_allowed": False,
            "discord_api_calls_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
            "canonical_mutation_allowed": False,
        },
        "readback": readback,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def execute_schedule_manual_test_action(
    vault_root: str | Path,
    action: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Execute one manual UI action through the existing StudioAPI."""

    if _contains_secret_indicator(payload):
        return _json_response(
            False,
            SURFACE_ID,
            code="secret_indicator_blocked",
            message="manual schedule test inputs must not include secret-like values",
        )
    api = StudioAPI(str(_vault_path(vault_root)))
    workflow_id = str(payload.get("workflowId") or "operator_today")
    cron_expression = str(payload.get("cronExpression") or "17 9 * * 1-5")
    timezone_name = str(payload.get("timezoneName") or "Europe/London")
    runtime_adapter_target = str(payload.get("runtimeAdapterTarget") or "openclaw")
    schedule_summary = str(payload.get("scheduleSummary") or "Manual Studio Chat schedule UI test.")
    schedule_id = str(payload.get("scheduleId") or "")
    approval_id = str(payload.get("approvalId") or "")
    schedule_digest = str(payload.get("scheduleDigest") or "")
    staged_proposal_path = str(payload.get("stagedProposalPath") or "")
    activation_digest = str(payload.get("activationDigest") or "")
    export_digest = str(payload.get("exportDigest") or "")
    approval_statement = str(payload.get("operatorApprovalStatement") or "")
    schedule_write_statement = str(payload.get("operatorScheduleWriteStatement") or "")
    activation_statement = str(payload.get("operatorActivationStatement") or "")
    export_write_statement = str(payload.get("operatorExportWriteStatement") or "")

    if action == "preview-proposal":
        return api.get_phase11_chat_schedule_proposal_packet(
            "",
            workflow_id,
            "",
            "",
            cron_expression,
            timezone_name,
            runtime_adapter_target,
            "",
            schedule_summary,
        )
    if action == "queue-proposal":
        return api.request_phase11_chat_schedule_proposal_packet(
            schedule_digest,
            "",
            workflow_id,
            "",
            "",
            cron_expression,
            timezone_name,
            runtime_adapter_target,
            "",
            schedule_summary,
        )
    if action == "consume-proposal":
        return api.execute_phase11_chat_schedule_proposal_consumption(
            approval_id,
            schedule_digest,
            "studio-operator",
            approval_statement,
        )
    if action == "write-intent":
        return api.execute_phase11_chat_approved_schedule_intent_writer(
            staged_proposal_path,
            schedule_id,
            schedule_digest,
            "studio-operator",
            schedule_write_statement,
        )
    if action == "preview-activation":
        return api.get_phase11_chat_schedule_intent_activation_readiness(schedule_id)
    if action == "queue-activation":
        return api.request_phase11_chat_schedule_intent_activation(
            activation_digest,
            schedule_id,
            "studio-operator",
        )
    if action == "activate":
        return api.execute_phase11_chat_approved_schedule_activation(
            approval_id,
            activation_digest,
            "studio-operator",
            activation_statement,
        )
    if action == "preview-export":
        return api.get_phase11_chat_schedule_adapter_export_readiness(runtime_adapter_target, schedule_id)
    if action == "queue-export":
        return api.request_phase11_chat_schedule_adapter_export(
            export_digest,
            runtime_adapter_target,
            schedule_id,
            "studio-operator",
        )
    if action == "write-export-packet":
        return api.execute_phase11_chat_approved_schedule_adapter_export_packet_writer(
            approval_id,
            export_digest,
            "studio-operator",
            export_write_statement,
        )
    return _json_response(False, SURFACE_ID, code="unknown_action", message=f"unknown action: {action}")


def render_schedule_manual_test_app_html(plan: dict[str, Any]) -> str:
    """Render the browser manual-test UI."""

    readback = plan.get("readback") or {}
    latest = readback.get("latest_readback") or {}
    default_adapter = ((readback.get("summary") or {}).get("default_runtime_adapter_target") or "openclaw")
    title = "Studio Chat Schedule Manual Test"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #101418;
      --panel: #171d22;
      --panel-2: #1d252b;
      --border: #31404a;
      --text: #eef4f8;
      --muted: #a8b6bf;
      --accent: #6eb6ff;
      --ok: #79d79d;
      --warn: #ffd37a;
      --err: #ff8f8f;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Segoe UI, Arial, sans-serif; background: var(--bg); color: var(--text); }}
    header {{ padding: 18px 22px; border-bottom: 1px solid var(--border); background: #121920; position: sticky; top: 0; z-index: 2; }}
    header h1 {{ margin: 0; font-size: 22px; font-weight: 650; }}
    header p {{ margin: 6px 0 0; color: var(--muted); max-width: 980px; line-height: 1.45; }}
    main {{ display: grid; grid-template-columns: minmax(360px, 520px) 1fr; gap: 16px; padding: 16px; }}
    section {{ border: 1px solid var(--border); background: var(--panel); border-radius: 8px; padding: 14px; }}
    h2 {{ margin: 0 0 12px; font-size: 16px; }}
    label {{ display: grid; gap: 5px; color: var(--muted); font-size: 12px; margin-bottom: 9px; }}
    input, textarea {{ width: 100%; border: 1px solid var(--border); background: #0f151a; color: var(--text); border-radius: 6px; padding: 8px 9px; font: inherit; }}
    textarea {{ min-height: 54px; resize: vertical; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
    .actions {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }}
    button {{ border: 1px solid var(--border); background: var(--panel-2); color: var(--text); border-radius: 6px; padding: 9px 10px; cursor: pointer; font-weight: 600; }}
    button:hover {{ border-color: var(--accent); }}
    .status {{ margin-top: 12px; padding: 10px; border: 1px solid var(--border); border-radius: 6px; color: var(--muted); min-height: 42px; }}
    .status.ok {{ border-color: #2a7f48; color: var(--ok); }}
    .status.err {{ border-color: #954040; color: var(--err); }}
    .cards {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 12px; }}
    .card {{ background: var(--panel-2); border: 1px solid var(--border); border-radius: 8px; padding: 10px; }}
    .card span {{ display: block; color: var(--muted); font-size: 12px; }}
    .card strong {{ display: block; margin-top: 5px; font-size: 18px; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #0b1115; border: 1px solid var(--border); border-radius: 8px; padding: 12px; min-height: 220px; max-height: 68vh; overflow: auto; }}
    .boundary {{ color: var(--warn); }}
    @media (max-width: 980px) {{ main {{ grid-template-columns: 1fr; }} .cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(title)}</h1>
    <p>Loopback-only ChaseOS Studio harness for manually testing the local schedule chain. It uses existing governed StudioAPI methods. External scheduler changes, OpenClaw/Hermes cron mutation, Discord, providers, runtime dispatch, Agent Bus writes, and credential reads remain blocked.</p>
  </header>
  <main>
    <section>
      <h2>Manual Controls</h2>
      <div class="grid">
        <label>Workflow<input id="workflowId" value="operator_today"></label>
        <label>Runtime Adapter<input id="runtimeAdapterTarget" value="{html.escape(str(default_adapter))}"></label>
      </div>
      <div class="grid">
        <label>Cron<input id="cronExpression" value="17 9 * * 1-5"></label>
        <label>Timezone<input id="timezoneName" value="Europe/London"></label>
      </div>
      <label>Summary<textarea id="scheduleSummary">Manual Studio Chat schedule UI test.</textarea></label>
      <div class="grid">
        <label>Schedule ID<input id="scheduleId"></label>
        <label>Approval ID<input id="approvalId"></label>
      </div>
      <label>Schedule Digest<input id="scheduleDigest"></label>
      <label>Staged Proposal Path<input id="stagedProposalPath"></label>
      <label>Activation Digest<input id="activationDigest"></label>
      <label>Export Digest<input id="exportDigest"></label>
      <label>Proposal Approval Statement<textarea id="operatorApprovalStatement">I approve this Studio Chat schedule proposal for local manual testing.</textarea></label>
      <label>Schedule Write Statement<textarea id="operatorScheduleWriteStatement">I approve writing this disabled ChaseOS schedule intent for local manual testing.</textarea></label>
      <label>Activation Statement<textarea id="operatorActivationStatement">I approve enabling this ChaseOS schedule intent for local manual testing.</textarea></label>
      <label>Export Packet Statement<textarea id="operatorExportWriteStatement">I approve writing this local adapter export packet for manual testing.</textarea></label>
      <div class="actions">
        <button data-action="preview-proposal">Preview Proposal</button>
        <button data-action="queue-proposal">Queue Proposal</button>
        <button data-action="consume-proposal">Consume Proposal</button>
        <button data-action="write-intent">Write Intent</button>
        <button data-action="preview-activation">Preview Activation</button>
        <button data-action="queue-activation">Queue Activation</button>
        <button data-action="activate">Activate</button>
        <button data-action="preview-export">Preview Export</button>
        <button data-action="queue-export">Queue Export</button>
        <button data-action="write-export-packet">Write Export Packet</button>
      </div>
      <div id="status" class="status">Ready for manual UI test.</div>
    </section>
    <section>
      <h2>Readback</h2>
      <div class="cards">
        <div class="card"><span>Schedules</span><strong id="scheduleCount">{int(latest.get("schedule_count") or 0)}</strong></div>
        <div class="card"><span>Enabled</span><strong id="enabledCount">{int(latest.get("enabled_schedule_count") or 0)}</strong></div>
        <div class="card"><span>Approvals</span><strong id="approvalCount">{int(((latest.get("schedule_approval_counts") or {}).get("total")) or 0)}</strong></div>
        <div class="card"><span>Export Packets</span><strong id="exportPacketCount">{len(latest.get("latest_local_adapter_export_packets") or [])}</strong></div>
      </div>
      <p class="boundary">All readback is local ChaseOS state. No credential values are rendered.</p>
      <pre id="responseJson">{html.escape(json.dumps(readback, indent=2, default=str))}</pre>
    </section>
  </main>
  <script>
    const fieldIds = ['workflowId','runtimeAdapterTarget','cronExpression','timezoneName','scheduleSummary','scheduleId','approvalId','scheduleDigest','stagedProposalPath','activationDigest','exportDigest','operatorApprovalStatement','operatorScheduleWriteStatement','operatorActivationStatement','operatorExportWriteStatement'];
    function payload() {{ return Object.fromEntries(fieldIds.map(id => [id, document.getElementById(id).value])); }}
    function status(text, ok) {{
      const el = document.getElementById('status');
      el.textContent = text;
      el.className = 'status ' + (ok ? 'ok' : 'err');
    }}
    function findKey(obj, names) {{
      if (!obj || typeof obj !== 'object') return '';
      for (const name of names) if (Object.prototype.hasOwnProperty.call(obj, name) && obj[name]) return String(obj[name]);
      for (const value of Object.values(obj)) {{
        const found = findKey(value, names);
        if (found) return found;
      }}
      return '';
    }}
    function storeResponse(resp) {{
      const root = resp.data || resp;
      const scheduleId = findKey(root, ['schedule_id']);
      const approvalId = findKey(root, ['approval_id', 'id']);
      const scheduleDigest = findKey(root, ['schedule_digest']);
      const stagedProposalPath = findKey(root, ['staged_proposal_path', 'proposal_path', 'target_path']);
      const activationDigest = findKey(root, ['activation_digest']);
      const exportDigest = findKey(root, ['export_digest']);
      const exportPacketPath = findKey(root, ['export_packet_path', 'packet_path']);
      if (scheduleId) document.getElementById('scheduleId').value = scheduleId;
      if (approvalId) document.getElementById('approvalId').value = approvalId;
      if (scheduleDigest) document.getElementById('scheduleDigest').value = scheduleDigest;
      if (stagedProposalPath && stagedProposalPath.includes('schedule-proposals')) document.getElementById('stagedProposalPath').value = stagedProposalPath;
      if (activationDigest) document.getElementById('activationDigest').value = activationDigest;
      if (exportDigest) document.getElementById('exportDigest').value = exportDigest;
      if (exportPacketPath) console.log('export packet path', exportPacketPath);
    }}
    async function refreshReadback(extra) {{
      const resp = await fetch('/api/readback');
      const json = await resp.json();
      const latest = (((json.data || {{}}).latest_readback) || {{}});
      document.getElementById('scheduleCount').textContent = latest.schedule_count || 0;
      document.getElementById('enabledCount').textContent = latest.enabled_schedule_count || 0;
      document.getElementById('approvalCount').textContent = ((latest.schedule_approval_counts || {{}}).total) || 0;
      document.getElementById('exportPacketCount').textContent = (latest.latest_local_adapter_export_packets || []).length;
      document.getElementById('responseJson').textContent = JSON.stringify(extra ? {{ last_response: extra, readback: json }} : json, null, 2);
    }}
    async function runAction(action) {{
      status('Running ' + action + '...', true);
      const resp = await fetch('/api/action', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{ action, payload: payload() }}) }});
      const json = await resp.json();
      storeResponse(json);
      await refreshReadback(json);
      status((json.ok ? 'OK: ' : 'Blocked: ') + action, !!json.ok);
    }}
    document.querySelectorAll('button[data-action]').forEach(btn => btn.addEventListener('click', () => runAction(btn.dataset.action)));
    refreshReadback();
  </script>
</body>
</html>"""


class _ScheduleManualTestHandler(BaseHTTPRequestHandler):
    vault_root: Path
    host: str
    port: int
    plan: dict[str, Any] | None
    plan_lock: Lock

    def _get_plan(self) -> dict[str, Any]:
        cls = self.__class__
        if cls.plan is None:
            with cls.plan_lock:
                if cls.plan is None:
                    cls.plan = build_schedule_manual_test_app_plan(cls.vault_root, host=cls.host, port=cls.port)
        return cls.plan

    def _write(self, status: int, body: str | bytes, *, content_type: str) -> None:
        payload = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._write(200, render_schedule_manual_test_app_html(self._get_plan()), content_type="text/html; charset=utf-8")
            return
        if parsed.path == "/health.json":
            plan = self._get_plan()
            self._write(200, json.dumps(plan, indent=2, default=str), content_type="application/json")
            return
        if parsed.path == "/api/readback":
            data = build_phase11_chat_schedule_ui_action_controls_and_readback(self.__class__.vault_root)
            self._write(200, json.dumps(_json_response(True, "phase11_chat_schedule_ui_action_controls_and_readback", data), indent=2, default=str), content_type="application/json")
            return
        self._write(404, "not found", content_type="text/plain; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/action":
            self._write(404, "not found", content_type="text/plain; charset=utf-8")
            return
        try:
            body = self._read_json_body()
            action = str(body.get("action") or "")
            payload = body.get("payload") if isinstance(body.get("payload"), dict) else {}
            result = execute_schedule_manual_test_action(self.__class__.vault_root, action, payload)
            self._write(200, json.dumps(result, indent=2, default=str), content_type="application/json")
        except (json.JSONDecodeError, ValueError) as exc:
            self._write(
                400,
                json.dumps(_json_response(False, SURFACE_ID, code="invalid_json", message=str(exc)), indent=2),
                content_type="application/json",
            )

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def make_schedule_manual_test_handler(
    vault_root: str | Path,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    plan: dict[str, Any] | None = None,
) -> type[BaseHTTPRequestHandler]:
    _require_loopback(host)
    vault = _vault_path(vault_root)

    class Handler(_ScheduleManualTestHandler):
        pass

    Handler.vault_root = vault
    Handler.host = host
    Handler.port = int(port)
    Handler.plan = plan
    Handler.plan_lock = Lock()
    return Handler


def serve_schedule_manual_test_app(
    vault_root: str | Path,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    serve_seconds: float | None = None,
) -> None:
    _require_loopback(host)
    server = ThreadingHTTPServer(
        (host, int(port)),
        make_schedule_manual_test_handler(vault_root, host=host, port=port),
    )
    try:
        if serve_seconds is None:
            server.serve_forever()
            return
        server.timeout = 0.2
        deadline = monotonic() + max(0.0, float(serve_seconds))
        while monotonic() < deadline:
            server.handle_request()
    finally:
        server.server_close()


def smoke_test_schedule_manual_test_app(
    vault_root: str | Path,
    *,
    host: str = DEFAULT_HOST,
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    """Run a bounded loopback smoke test and stop the server."""

    _require_loopback(host)
    vault = _vault_path(vault_root)
    server = ThreadingHTTPServer((host, 0), make_schedule_manual_test_handler(vault, host=host, port=0))
    port = int(server.server_address[1])
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{host}:{port}"
    checks: list[dict[str, Any]] = []
    ok = True
    for route in ("/health.json", "/api/readback", "/"):
        started = monotonic()
        try:
            request = Request(f"{base_url}{route}", headers={"User-Agent": "chaseos-schedule-manual-test-smoke"})
            with urlopen(request, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace")
                checks.append(
                    {
                        "route": route,
                        "ok": response.status == 200,
                        "status": response.status,
                        "elapsed_seconds": round(monotonic() - started, 4),
                        "manual_controls_present": "Manual Controls" in body,
                        "readback_present": "Readback" in body or "latest_readback" in body,
                        "secret_field_present": any(
                            marker in body
                            for marker in (
                                'id="openaiApiKey"',
                                'name="OPENAI_API_KEY"',
                                'id="discordToken"',
                                'name="DISCORD_TOKEN"',
                                'type="password"',
                                "test-key-test",
                            )
                        ),
                    }
                )
        except (OSError, URLError) as exc:
            ok = False
            checks.append({"route": route, "ok": False, "error": str(exc)})
    server.shutdown()
    thread.join(timeout=2.0)
    return {
        "ok": bool(ok and all(item.get("ok") for item in checks)),
        "surface": SURFACE_ID,
        "mode": "bounded_loopback_smoke",
        "base_url": base_url,
        "server_stopped": not thread.is_alive(),
        "manual_ui_test_ready": True,
        "visual_browser_qa_complete": False,
        "external_scheduler_mutation_allowed": False,
        "runtime_dispatch_allowed": False,
        "discord_api_calls_allowed": False,
        "provider_calls_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
        "checks": checks,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve or inspect the Studio Chat schedule manual test app")
    parser.add_argument("--vault-root", default=None, metavar="PATH")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--serve-seconds", type=float, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--json", action="store_true", dest="output_json")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    vault = _vault_path(args.vault_root)
    if args.smoke:
        payload = smoke_test_schedule_manual_test_app(vault, host=args.host)
        print(json.dumps(payload, indent=2, default=str) if args.output_json else payload)
        return 0 if payload.get("ok") else 1
    plan = build_schedule_manual_test_app_plan(vault, host=args.host, port=args.port)
    if args.dry_run:
        print(json.dumps(plan, indent=2, default=str) if args.output_json else plan)
        return 0
    print(f"Serving Studio Chat schedule manual test app at {plan['url']}")
    serve_schedule_manual_test_app(vault, host=args.host, port=args.port, serve_seconds=args.serve_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
