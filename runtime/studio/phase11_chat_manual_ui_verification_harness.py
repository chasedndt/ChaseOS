"""Phase 11 Chat manual UI verification harness.

Loopback-only HTTP harness for manually testing the Chat Prepare All →
Run Approved Test flow at http://127.0.0.1:8772/ or the port passed on
the command line.

The harness calls the same StudioAPI and authority execution controls that
the native Studio Chat panel uses, then shows the prepare/execute results
in the browser.  It does NOT expose credential values, call Discord directly,
mutate external cron, or bypass any governed approval gate.

Accepted use: run this harness while OPENAI_API_KEY, Hermes, and OpenClaw
are present in the process environment to perform the P0 manual verification.
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
from urllib.parse import parse_qs, urlparse

from runtime.studio.phase11_chat_authority_execution_controls import (
    build_phase11_chat_authority_execution_controls,
)
from runtime.studio.phase11_chat_conversation_log_writer import write_conversation_log
from runtime.studio.phase11_chat_runtime_result_display import build_chat_runtime_result_display
from runtime.studio.shell.api import StudioAPI


SURFACE_ID = "phase11_chat_manual_ui_verification_harness"
MODEL_VERSION = "studio.phase11_chat_manual_ui_verification_harness.v1"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8772
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

_SECRET_INDICATORS = (
    "sk-", "xoxb-", "-----BEGIN", "OPENAI_API_KEY=",
    "ANTHROPIC_API_KEY=", "DISCORD_TOKEN=", "BOT_TOKEN=",
)


class HarnessError(RuntimeError):
    """Raised when the harness cannot proceed safely."""


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path | None = None) -> Path:
    return Path(vault_root or Path.cwd()).expanduser().resolve()


def _require_loopback(host: str) -> None:
    if host not in LOOPBACK_HOSTS:
        raise HarnessError(f"Harness may only bind to loopback; got: {host}")


def _has_secret_indicator(text: str) -> bool:
    return any(ind.lower() in text.lower() for ind in _SECRET_INDICATORS)


def _esc(text: str) -> str:
    return html.escape(str(text or ""))


def _json_response(data: dict[str, Any]) -> bytes:
    return json.dumps(data, indent=2, default=str).encode("utf-8")


def _status_badge(status: str | None) -> str:
    s = str(status or "").lower()
    color = {
        "true": "#22c55e",
        "false": "#ef4444",
        "ok": "#22c55e",
        "blocked": "#f59e0b",
        "failed": "#ef4444",
    }.get(s, "#64748b")
    return f'<span style="background:{color};color:#fff;padding:2px 6px;border-radius:4px;font-size:12px">{_esc(status or "—")}</span>'


_INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ChaseOS Studio Chat – P0 Verification Harness</title>
<style>
body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:16px}
h1{color:#38bdf8;font-size:20px;margin:0 0 4px}
h2{color:#7dd3fc;font-size:15px;margin:16px 0 8px}
.card{background:#1e293b;border-radius:8px;padding:12px;margin-bottom:12px}
.row{display:flex;gap:12px;align-items:flex-start;flex-wrap:wrap}
label{font-size:13px;color:#94a3b8;display:block;margin-bottom:4px}
input,textarea{width:100%;box-sizing:border-box;background:#0f172a;color:#e2e8f0;
  border:1px solid #334155;border-radius:6px;padding:8px;font-size:13px}
textarea{min-height:80px;resize:vertical}
button{background:#0ea5e9;color:#fff;border:none;border-radius:6px;
  padding:8px 16px;font-size:13px;cursor:pointer}
button:hover{background:#0284c7}
button.danger{background:#dc2626}
.warn{color:#f59e0b;font-size:12px;margin-top:8px}
#log{background:#020617;border-radius:6px;padding:10px;
  font-size:12px;font-family:monospace;max-height:480px;overflow-y:auto;
  white-space:pre-wrap;word-break:break-all}
.tag{font-size:11px;padding:1px 6px;border-radius:3px;font-weight:600}
.green{background:#166534;color:#bbf7d0}
.red{background:#7f1d1d;color:#fecaca}
.amber{background:#78350f;color:#fde68a}
.blue{background:#1e3a5f;color:#bae6fd}
</style>
</head>
<body>
<h1>ChaseOS Studio Chat — P0 Manual Verification Harness</h1>
<p style="font-size:13px;color:#64748b">
  Target: <code>http://127.0.0.1:{PORT}/</code> &nbsp;|&nbsp;
  Vault: <code id="vault-display">…</code> &nbsp;|&nbsp;
  <span class="tag blue">loopback-only</span>
</p>

<div class="card">
  <h2>1 · Prepare All Digests</h2>
  <div class="row">
    <div style="flex:2;min-width:220px">
      <label>Message</label>
      <textarea id="msg-prepare" placeholder="e.g. What is today's market summary?"></textarea>
    </div>
    <div style="flex:1;min-width:120px;display:flex;align-items:flex-end">
      <button onclick="prepare()">Prepare All</button>
    </div>
  </div>
  <div id="prepare-result" style="margin-top:10px"></div>
</div>

<div class="card">
  <h2>2 · Run Approved Test Stack</h2>
  <p style="font-size:12px;color:#64748b">
    Paste the digests from step 1, provide an operator statement, then click Run.
    Leave a digest blank to skip that lane.
  </p>
  <div class="row">
    <div style="flex:2;min-width:220px">
      <label>Message</label>
      <input id="msg-run" type="text" placeholder="Same message as above">
    </div>
    <div style="flex:2;min-width:220px">
      <label>Operator approval statement</label>
      <input id="op-statement" type="text" placeholder="I approve this Chat manual authority test">
    </div>
  </div>
  <div class="row" style="margin-top:8px">
    <div style="flex:1;min-width:160px">
      <label>Provider digest</label>
      <input id="dig-provider" type="text">
    </div>
    <div style="flex:1;min-width:160px">
      <label>Hermes digest</label>
      <input id="dig-hermes" type="text">
    </div>
    <div style="flex:1;min-width:160px">
      <label>Discord digest</label>
      <input id="dig-discord" type="text">
    </div>
    <div style="flex:1;min-width:160px">
      <label>Cron digest</label>
      <input id="dig-cron" type="text">
    </div>
  </div>
  <div style="margin-top:8px;display:flex;gap:8px">
    <button onclick="runTest(false)">Run (provider + Hermes)</button>
    <button onclick="runTest(true)">Run All Lanes</button>
  </div>
  <div id="run-result" style="margin-top:10px"></div>
</div>

<div class="card">
  <h2>3 · Agent Bus Readback</h2>
  <button onclick="readback()">Refresh Readback</button>
  <div id="readback-result" style="margin-top:10px"></div>
</div>

<div class="card">
  <h2>4 · Save Conversation Log</h2>
  <p style="font-size:12px;color:#64748b">
    After a successful run, save the conversation log to
    <code>07_LOGS/Conversations/</code>.
  </p>
  <div class="row">
    <div style="flex:2;min-width:220px">
      <label>Operator save statement</label>
      <input id="save-statement" type="text" placeholder="Saving P0 verification conversation log">
    </div>
  </div>
  <div style="margin-top:8px;display:flex;gap:8px">
    <button onclick="saveLog(true)">Dry Run Preview</button>
    <button onclick="saveLog(false)">Save Live</button>
  </div>
  <div id="save-result" style="margin-top:10px"></div>
</div>

<div class="card">
  <h2>Event Log</h2>
  <pre id="log">Harness ready. Run the steps above.\n</pre>
</div>

<script>
const port = {PORT};
let _lastPrepare = null;
let _lastRun = null;

function log(msg) {
  const el = document.getElementById('log');
  el.textContent += '[' + new Date().toISOString() + '] ' + msg + '\n';
  el.scrollTop = el.scrollHeight;
}

function renderJson(id, data) {
  const el = document.getElementById(id);
  const ok = data && data.ok !== false;
  const color = ok ? '#16a34a' : '#dc2626';
  el.innerHTML = '<pre style="margin:0;font-size:11px;color:' + color + ';' +
    'background:#020617;border-radius:4px;padding:8px;max-height:300px;overflow-y:auto">' +
    JSON.stringify(data, null, 2).replace(/&/g,'&amp;').replace(/</g,'&lt;') + '</pre>';
}

async function prepare() {
  const msg = document.getElementById('msg-prepare').value.trim();
  if (!msg) { log('ERROR: message required for prepare'); return; }
  log('Preparing digests for: ' + msg.substring(0, 60) + '…');
  try {
    const r = await fetch('/api/prepare', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({message: msg})
    });
    const data = await r.json();
    _lastPrepare = data;
    renderJson('prepare-result', data);
    const d = (data.prepared_digests || {});
    document.getElementById('msg-run').value = msg;
    document.getElementById('dig-provider').value = d.expected_provider_digest || '';
    document.getElementById('dig-hermes').value = d.expected_main_runtime_digest || '';
    document.getElementById('dig-discord').value = d.expected_discord_control_digest || '';
    document.getElementById('dig-cron').value = d.expected_cron_control_digest || '';
    log('Prepare complete. Digests copied to run form.');
  } catch(e) { log('Prepare error: ' + e); }
}

async function runTest(allLanes) {
  const msg = document.getElementById('msg-run').value.trim();
  const stmt = document.getElementById('op-statement').value.trim();
  if (!msg) { log('ERROR: message required'); return; }
  if (!stmt) { log('ERROR: operator approval statement required'); return; }
  log('Running approved test stack (allLanes=' + allLanes + ')…');
  try {
    const body = {
      message: msg,
      operator_approval_statement: stmt,
      expected_provider_digest: document.getElementById('dig-provider').value.trim() || null,
      expected_main_runtime_digest: document.getElementById('dig-hermes').value.trim() || null,
      expected_discord_control_digest: allLanes ? (document.getElementById('dig-discord').value.trim() || null) : null,
      expected_cron_control_digest: allLanes ? (document.getElementById('dig-cron').value.trim() || null) : null,
    };
    const r = await fetch('/api/run-test', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(body)
    });
    const data = await r.json();
    _lastRun = data;
    renderJson('run-result', data);
    const s = data.summary || {};
    log('Run complete. successes=' + s.execution_success_count +
      ' failures=' + s.execution_failure_count +
      ' bus_tasks=' + s.agent_bus_readback_task_count);
  } catch(e) { log('Run error: ' + e); }
}

async function readback() {
  log('Refreshing Agent Bus readback…');
  try {
    const r = await fetch('/api/readback');
    const data = await r.json();
    renderJson('readback-result', data);
    log('Readback: ' + (data.summary || {}).total_tasks + ' tasks across ' +
      ((data.lanes || []).length) + ' runtimes');
  } catch(e) { log('Readback error: ' + e); }
}

async function saveLog(dryRun) {
  const stmt = document.getElementById('save-statement').value.trim();
  if (!stmt) { log('ERROR: save statement required'); return; }
  const runData = _lastRun || {};
  const msg = document.getElementById('msg-run').value.trim();
  log('Saving conversation log (dry_run=' + dryRun + ')…');
  try {
    const r = await fetch('/api/save-log', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        dry_run: dryRun,
        operator_approval_statement: stmt,
        user_prompt: msg,
        run_payload: runData,
      })
    });
    const data = await r.json();
    renderJson('save-result', data);
    log('Save log: file_written=' + data.file_written + ' session_id=' + data.session_id);
  } catch(e) { log('Save error: ' + e); }
}

// Load vault path on init
fetch('/api/info').then(r=>r.json()).then(d=>{
  document.getElementById('vault-display').textContent = d.vault_root || '…';
  log('Harness loaded. vault=' + (d.vault_root || '?'));
}).catch(()=>{});
</script>
</body>
</html>
"""


class HarnessHandler(BaseHTTPRequestHandler):
    vault: Path
    _api: StudioAPI | None
    _lock: Lock

    def log_message(self, fmt: str, *args: object) -> None:  # suppress default logging
        pass

    def _api_instance(self) -> StudioAPI:
        return StudioAPI(str(self.vault))

    def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        body = _json_response(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, body_html: str) -> None:
        body = body_html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/":
            self._send_html(_INDEX_HTML.replace("{PORT}", str(DEFAULT_PORT)))
        elif path == "/api/info":
            self._send_json({
                "ok": True,
                "surface": SURFACE_ID,
                "vault_root": str(self.vault),
                "harness": "phase11_chat_manual_ui_verification_harness",
                "generated_at_utc": _now_utc(),
            })
        elif path == "/api/readback":
            data = build_chat_runtime_result_display(self.vault)
            self._send_json(data)
        else:
            self._send_json({"ok": False, "error": "not_found"}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._read_body()

        if path == "/api/prepare":
            message = str(body.get("message") or "").strip()
            if _has_secret_indicator(message):
                self._send_json({"ok": False, "blocked_reasons": ["secret_indicator_in_message"]})
                return
            data = build_phase11_chat_authority_execution_controls(
                self.vault,
                message=message,
                execute=False,
            )
            self._send_json(data)

        elif path == "/api/run-test":
            message = str(body.get("message") or "").strip()
            stmt = str(body.get("operator_approval_statement") or "").strip()
            if _has_secret_indicator(message) or _has_secret_indicator(stmt):
                self._send_json({"ok": False, "blocked_reasons": ["secret_indicator_in_input"]})
                return
            if not message:
                self._send_json({"ok": False, "blocked_reasons": ["message_required"]})
                return
            if not stmt:
                self._send_json({"ok": False, "blocked_reasons": ["operator_approval_statement_required"]})
                return
            data = build_phase11_chat_authority_execution_controls(
                self.vault,
                message=message,
                execute=True,
                execute_provider=bool(body.get("expected_provider_digest")),
                execute_main_runtime=bool(body.get("expected_main_runtime_digest")),
                execute_discord_control=bool(body.get("expected_discord_control_digest")),
                execute_cron_control=bool(body.get("expected_cron_control_digest")),
                expected_provider_digest=body.get("expected_provider_digest") or None,
                expected_main_runtime_digest=body.get("expected_main_runtime_digest") or None,
                expected_discord_control_digest=body.get("expected_discord_control_digest") or None,
                expected_cron_control_digest=body.get("expected_cron_control_digest") or None,
                operator_approval_statement=stmt,
            )
            self._send_json(data)

        elif path == "/api/save-log":
            stmt = str(body.get("operator_approval_statement") or "").strip()
            user_prompt = str(body.get("user_prompt") or "").strip()
            dry_run = bool(body.get("dry_run", True))
            run_payload = body.get("run_payload") or {}
            if _has_secret_indicator(stmt) or _has_secret_indicator(user_prompt):
                self._send_json({"ok": False, "blocked_reasons": ["secret_indicator_in_input"]})
                return

            exec_results = run_payload.get("execution_results") or {}
            provider_result = exec_results.get("provider_call") or {}
            provider_call = provider_result.get("provider_call") or {}
            hermes_result = exec_results.get("main_runtime") or {}
            discord_result = exec_results.get("discord_control") or {}
            cron_result = exec_results.get("cron_control") or {}

            data = write_conversation_log(
                self.vault,
                operator_id="studio-operator",
                operator_approval_statement=stmt,
                user_prompt=user_prompt,
                provider_output=str(provider_call.get("output_text_preview") or "")[:2000] or None,
                provider_id=str(provider_call.get("provider_id") or "") or None,
                provider_model=str(provider_call.get("model") or "") or None,
                provider_approval_id=str((provider_result.get("summary") or {}).get("approval_id") or "") or None,
                provider_digest=str(provider_call.get("credential_env_ref") or "") or None,
                provider_evidence_path=str(provider_call.get("output_path") or "") or None,
                hermes_task_id=str((hermes_result.get("summary") or {}).get("task_id") or "") or None,
                hermes_status=str(hermes_result.get("status") or "") or None,
                hermes_result_summary=str(hermes_result.get("status") or "") or None,
                openclaw_discord_task_id=str((discord_result.get("summary") or {}).get("task_id") or "") or None,
                openclaw_discord_status=str(discord_result.get("status") or "") or None,
                openclaw_cron_task_id=str((cron_result.get("summary") or {}).get("task_id") or "") or None,
                openclaw_cron_status=str(cron_result.get("status") or "") or None,
                dry_run=dry_run,
            )
            self._send_json(data)

        else:
            self._send_json({"ok": False, "error": "not_found"}, 404)


def _make_handler(vault: Path) -> type[HarnessHandler]:
    class _Handler(HarnessHandler):
        pass
    _Handler.vault = vault
    _Handler._lock = Lock()
    return _Handler


def run_manual_verification_harness(
    vault_root: str | Path | None = None,
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    open_browser: bool = True,
) -> None:
    """Start the loopback manual verification harness."""
    _require_loopback(host)
    vault = _vault_path(vault_root)
    handler = _make_handler(vault)
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    print(f"[phase11-harness] listening at {url}")
    print(f"[phase11-harness] vault: {vault}")
    print("[phase11-harness] Ctrl+C to stop")
    if open_browser:
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


def check_harness_readiness(vault_root: str | Path | None = None) -> dict[str, Any]:
    """Return readiness report without starting a server."""
    import os
    vault = _vault_path(vault_root)
    openai_present = bool(os.environ.get("OPENAI_API_KEY"))
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "vault_root": str(vault),
        "generated_at_utc": _now_utc(),
        "readiness": {
            "vault_exists": vault.is_dir(),
            "openai_api_key_present": openai_present,
            "openai_api_key_env_ref": "OPENAI_API_KEY",
            "credential_value_displayed": False,
            "harness_port": DEFAULT_PORT,
            "loopback_only": True,
        },
        "lanes_to_verify": [
            "provider_call (OPENAI_API_KEY required)",
            "hermes_main_runtime (Hermes daemon required)",
            "openclaw_discord_control (OpenClaw daemon required)",
            "openclaw_cron_control (OpenClaw daemon required)",
        ],
        "verification_steps": [
            "1. Start harness: python -m runtime.studio.phase11_chat_manual_ui_verification_harness",
            "2. Open http://127.0.0.1:8772/ in browser",
            "3. Enter a test message and click 'Prepare All'",
            "4. Copy digests to Run form, add operator statement, click 'Run'",
            "5. Check each lane result card for ok/blocked/failed status",
            "6. Click 'Refresh Readback' to see Agent Bus task states",
            "7. Click 'Save Live' to persist the conversation log",
            "8. Record results in build log",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 11 Chat P0 manual verification harness")
    parser.add_argument("--vault-root", default=None)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--readiness", action="store_true", help="Print readiness report and exit")
    args = parser.parse_args()

    if args.readiness:
        report = check_harness_readiness(args.vault_root)
        print(json.dumps(report, indent=2, default=str))
        return

    run_manual_verification_harness(
        vault_root=args.vault_root,
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
    )


if __name__ == "__main__":
    main()
