---
title: "ChaseOS Runtime MCP — Smoke Test Guide"
version: "1.1"
date: 2026-04-21
status: live
knowledge_class: system-operational
---

# ChaseOS Runtime MCP - Smoke Test Guide

Local-first, stdio-first verification guide for the V1 server plus active V2 `workflow.invoke_bounded`.

---

## Automated Test Suite

Run the full MCP test suite (67 tests covering V1, hardening paths, Pass 6B `workflow.invoke_bounded`, and Pass 6C duplicate/audit hardening):

```bash
cd <vault_root>
.venv/Scripts/python.exe -m pytest runtime/mcp/tests/test_runtime_mcp_v1.py -v
```

Expected: **67 passed, 0 failed**

---

## Manual Stdio Smoke Test

Pipe newline-delimited JSON directly into the server:

```bash
cd <vault_root>

echo '{"resource": "runtime.identity", "runtime_id": "openclaw", "mode": "read_only"}' | \
  .venv/Scripts/python.exe -m runtime.mcp.server
```

Expected response (formatted for readability):
```json
{
  "ok": true,
  "request_id": "req-...",
  "result": {
    "server_name": "chaseos-runtime-mcp",
    "server_version": "0.1.0",
    "chaseos_phase": "Phase 9",
    "vault_root_confirmed": true,
    "transport": "stdio",
    "active_safety_mode": "read_only",
    "runtime_id": "openclaw"
  }
}
```

---

## Multi-Request Smoke (stdin file)

Create a test input file and pipe it in:

```bash
cat > /tmp/mcp_smoke.jsonl << 'EOF'
{"resource": "runtime.identity", "runtime_id": "openclaw", "mode": "read_only"}
{"resource": "chaseos.current_truth", "runtime_id": "openclaw", "mode": "read_only"}
{"resource": "workflows.registry", "runtime_id": "openclaw", "mode": "read_only", "params": {"filter": "active"}}
{"resource": "runtime.audit.recent", "runtime_id": "openclaw", "mode": "read_only", "params": {"limit": 5}}
EOF

cat /tmp/mcp_smoke.jsonl | .venv/Scripts/python.exe -m runtime.mcp.server
```

Expected: 4 lines of JSON, all `"ok": true`.

---

## Bounded Workflow Invocation Smoke (dry_run)

Use dry-run mode to verify `workflow.invoke_bounded` routes through AOR without writing an Operator-Briefs artifact:

```bash
echo '{"tool": "workflow.invoke_bounded", "runtime_id": "openclaw", "mode": "draft_execution", "params": {"workflow_id": "operator_today", "dry_run": true}}' | \
  .venv/Scripts/python.exe -m runtime.mcp.server
```

Expected: `"ok": true`, `"aor_status": "dry_run_ok"`, `"canonical_write": false`, and `"files_written": []`.

The response also includes `audit_reconciliation` and `retry_guidance`. It must not include generated brief text.

---

## Bounded Workflow Invocation Smoke (one intentional live path)

Use live mode only when the intended Operator-Briefs artifact is known not to exist. The Pass 6C verified path used JSON output to avoid overwriting the existing markdown morning brief:

```bash
echo '{"request_id":"smoke-pass6c-live-json","tool":"workflow.invoke_bounded","runtime_id":"openclaw","mode":"draft_execution","params":{"workflow_id":"operator_today","inputs":{"date":"2026-04-21","output_format":"json"},"dry_run":false}}' | \
  .venv/Scripts/python.exe -m runtime.mcp.server
```

Expected: `"ok": true`, `"aor_status": "success"`, `"invocation_status": "completed"`, `"canonical_write": false`, and `output_artifacts[0].path` set to `07_LOGS/Operator-Briefs/2026-04-21-operator-today.json`.

Inspect:
- Output artifact: `07_LOGS/Operator-Briefs/2026-04-21-operator-today.json`
- AOR audit: `07_LOGS/Agent-Activity/{timestamp}__operator_today__{aor_audit_id[:8]}.json`
- MCP audit: `07_LOGS/Agent-Activity/{timestamp}__mcp__workflow.invoke_bounded__smokepas.json`

The MCP response must not include the full generated brief text.

---

## Duplicate Live Invocation Guard

Rerunning the same live invocation after the output exists must deny before AOR:

```bash
echo '{"request_id":"smoke-pass6c-dup-json","tool":"workflow.invoke_bounded","runtime_id":"openclaw","mode":"draft_execution","params":{"workflow_id":"operator_today","inputs":{"date":"2026-04-21","output_format":"json"},"dry_run":false}}' | \
  .venv/Scripts/python.exe -m runtime.mcp.server
```

Expected: `"ok": false`, `"code": "workflow_output_already_exists"`, `existing_artifacts` listing the predicted output path, and no new AOR audit record for the duplicate request.

This is the "do not retry blindly" signal. Reconcile the MCP audit, AOR audit, and output artifact before choosing a new date/output format or taking manual action.

Denied-mode check:

```bash
echo '{"tool": "workflow.invoke_bounded", "runtime_id": "openclaw", "mode": "read_plus_proposal", "params": {"workflow_id": "operator_today", "dry_run": true}}' | \
  .venv/Scripts/python.exe -m runtime.mcp.server
```

Expected: `"ok": false`, `"code": "surface_unavailable"`.

---

## Error Path Verification

### Bad JSON

```bash
echo '{not valid json}' | .venv/Scripts/python.exe -m runtime.mcp.server
```

Expected: `{"error": {"code": "bad_json", ...}, "ok": false, "request_id": "unknown"}`

---

### Mode denied (n8n trying read_plus_proposal)

```bash
echo '{"resource": "runtime.identity", "runtime_id": "n8n", "mode": "read_plus_proposal"}' | \
  .venv/Scripts/python.exe -m runtime.mcp.server
```

Expected: `"ok": false`, `"code": "mode_denied"`

---

### Read_only blocking tools

```bash
echo '{"tool": "proposal.submit", "runtime_id": "openclaw", "mode": "read_only", "params": {"target_file": "x.md", "proposed_content": "y"}}' | \
  .venv/Scripts/python.exe -m runtime.mcp.server
```

Expected: `"ok": false`, `"code": "surface_unavailable"`

---

### Proposal submit flow (requires read_plus_proposal)

```bash
echo '{"tool": "proposal.submit", "runtime_id": "openclaw", "mode": "read_plus_proposal", "params": {"target_file": "05_TEMPLATES/example.md", "change_type": "update", "proposed_content": "# Updated\n", "description": "smoke test proposal"}}' | \
  .venv/Scripts/python.exe -m runtime.mcp.server
```

Expected: `"ok": true`, `"result": {"proposal_status": "staged", ...}`

Verify the artifact was written:
```bash
ls .chaseos/mcp-proposals/
```

---

## Python Integration Smoke (no process spawn)

Run the built-in integration test directly from Python:

```python
import json
from io import StringIO
from runtime.mcp.server import run_server

lines = "\n".join([
    json.dumps({"resource": "runtime.identity", "runtime_id": "openclaw", "mode": "read_only"}),
    json.dumps({"resource": "chaseos.current_truth", "runtime_id": "openclaw", "mode": "read_only"}),
    "{bad json}",
])

output = StringIO()
exit_code = run_server(stdin=StringIO(lines + "\n"), stdout=output)
responses = [json.loads(line) for line in output.getvalue().strip().splitlines()]

assert responses[0]["ok"] is True
assert responses[0]["result"]["server_name"] == "chaseos-runtime-mcp"
assert responses[1]["ok"] is True
assert responses[2]["ok"] is False
assert responses[2]["error"]["code"] == "bad_json"
print("All assertions passed.")
```

Or run the existing `test_stdio_multi_request_smoke` test:

```bash
.venv/Scripts/python.exe -m pytest runtime/mcp/tests/test_runtime_mcp_v1.py::RuntimeMCPV1Tests::test_stdio_multi_request_smoke -v
```

---

## Regression Commands After Any MCP Change

```bash
# MCP tests only (fast)
.venv/Scripts/python.exe -m pytest runtime/mcp/tests/test_runtime_mcp_v1.py -v

# Full vault suite (comprehensive)
.venv/Scripts/python.exe -m pytest --tb=short -q
```

Both should complete with 0 failures before any MCP PR is considered clean.

---

## Interpreting Audit Records

After any successful request, an audit record lands in `07_LOGS/Agent-Activity/`.

Filename format: `{YYYYMMDD-HHMMSS}__mcp__{surface_id}__{request_id[:8]}.json`

Example: `20260420-143052__mcp__runtime.identity__abc12345.json`

Frozen schema fields: `schema_version`, `request_id`, `recorded_at`, `surface_id`, `surface_class`, `runtime_id`, `trust_tier` (int), `safety_mode`, `outcome`, `outcome_detail`, `files_read`, `files_written`, `error_code`, `error_message`

---

*ChaseOS Runtime MCP Smoke Test Guide - Phase 9 Pass 6C - 2026-04-21*


*Graph links: [[Vault-Map]]*
