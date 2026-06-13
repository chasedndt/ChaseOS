---
title: "ChaseOS Runtime MCP — Usage Guide"
version: "1.1"
date: 2026-04-21
status: live
knowledge_class: system-operational
---

# ChaseOS Runtime MCP - Usage Guide

Internal stdio JSON server providing bounded vault read access, governed proposal staging, and one active V2 bounded workflow invocation surface to operator runtimes (OpenClaw, claude_code, n8n).

Pass 6C verifies normal operator use for `workflow.invoke_bounded`: dry-run, one intentional live invocation, MCP/AOR audit reconciliation, and duplicate-output denial before AOR.

---

## How to Start the Server

```bash
# From the vault root, using the repo-local venv
.venv/Scripts/python.exe -m runtime.mcp.server
```

The server reads newline-delimited JSON from stdin, writes newline-delimited JSON to stdout, and runs until stdin closes.

---

## Request Envelope Format

Every request is one JSON line:

```json
{
  "resource": "<surface_name>",
  "runtime_id": "openclaw",
  "mode": "read_only",
  "params": {}
}
```

Use `"resource"`, `"tool"`, or `"prompt"` as the surface-class key. `mode` is optional (defaults to `read_only`). `request_id` is optional (generated if absent).

---

## Live V1 Surfaces

### Resources (read_only or read_plus_proposal)

#### `runtime.identity`

```json
{"resource": "runtime.identity", "runtime_id": "openclaw", "mode": "read_only"}
```

Response fields: `server_name`, `server_version`, `chaseos_phase`, `vault_root_confirmed`, `transport`, `active_safety_mode`, `runtime_id`

---

#### `runtime.capabilities`

```json
{"resource": "runtime.capabilities", "runtime_id": "openclaw", "mode": "read_only"}
```

Returns `resources`, `tools`, `prompts`, `v2_tools`, `deferred`, `excluded`, and `modes`.

---

#### `chaseos.current_truth`

```json
{"resource": "chaseos.current_truth", "runtime_id": "openclaw", "mode": "read_only",
 "params": {"fields": ["sprint_focus", "current_phase", "active_domains"]}}
```

Allowed fields: `sprint_focus`, `current_phase`, `active_domains`, `open_loops`, `recent_decisions`

Default fields (no params): `sprint_focus`, `current_phase`, `active_domains`

Source: `00_HOME/Now.md` (required). Missing Now.md returns `system_error(source_file_read_error)`.

---

#### `workflows.registry`

```json
{"resource": "workflows.registry", "runtime_id": "openclaw", "mode": "read_only",
 "params": {"filter": "active"}}
```

`filter` param: `"active"` | `"draft"` | `"all"` (default: `"all"`)

Returns `workflows` list (id, name, status, task_type, role_card, permission_ceiling, writeback_targets) and `filter` echo.

---

#### `workflows.role_boundaries`

```json
{"resource": "workflows.role_boundaries", "runtime_id": "openclaw", "mode": "read_only"}
```

Returns `role_cards` list (id, name, allowed_actions, forbidden_actions, write_scope, forbidden_write_zones).

---

#### `runtime.permission_envelope`

```json
{"resource": "runtime.permission_envelope", "runtime_id": "openclaw", "mode": "read_only"}
```

Returns the resolved permission envelope for the runtime/mode combination.

---

#### `runtime.handoff.current`

```json
{"resource": "runtime.handoff.current", "runtime_id": "openclaw", "mode": "read_only"}
```

Returns `current_truth` (default fields), `open_loops`, `latest_operator_brief`.

Fails cleanly if Now.md is missing (same error as current_truth).

---

#### `runtime.audit.recent`

```json
{"resource": "runtime.audit.recent", "runtime_id": "openclaw", "mode": "read_only",
 "params": {"limit": 10}}
```

`limit` param: 1–50 (default: 10, clamped). Returns `records` list using frozen 14-field audit schema.

---

#### `operator.briefing.latest`

```json
{"resource": "operator.briefing.latest", "runtime_id": "openclaw", "mode": "read_only"}
```

Returns `latest` (path, title, preview — first 12 lines) or `null` if no briefs exist.

---

### V1 Tools (read_plus_proposal or draft_execution)

#### `proposal.submit`

```json
{"tool": "proposal.submit", "runtime_id": "openclaw", "mode": "read_plus_proposal",
 "params": {
   "target_file": "05_TEMPLATES/example.md",
   "change_type": "update",
   "proposed_content": "# Updated\nNew content here.\n",
   "description": "Update example template"
 }}
```

`change_type`: `"create"` | `"update"` | `"delete"`

Response: `proposal_id`, `proposal_status`, `staged_at`, `target_file`, `change_type`, `preliminary_validation`

Staged artifact lands at: `.chaseos/mcp-proposals/{YYYYMMDD-HHMMSS}__{proposal_id[:8]}.json`

Audit write is **fail-closed**: if audit fails, proposal is rolled back.

---

#### `proposal.validate`

```json
{"tool": "proposal.validate", "runtime_id": "openclaw", "mode": "read_plus_proposal",
 "params": {"proposal_id": "proposal-<uuid>"}}
```

Response: `is_valid`, `protected_file_flag`, `errors` (list of `{error_type, error_code, message}`), `warnings`, `governance_checks`

Protected files (exact list per frozen Proposal Staging doc):
- `06_AGENTS/Permission-Matrix.md`
- `06_AGENTS/Trust-Tiers.md`
- `CLAUDE.md`
- `04_SOPS/Credential-Boundaries-SOP.md`
- `04_SOPS/Untrusted-Input-Handling-SOP.md`
- `runtime/aor/engine.py`
- Pattern: `runtime/policy/adapters/*.yaml`

---

#### `proposal.diff_preview`

```json
{"tool": "proposal.diff_preview", "runtime_id": "openclaw", "mode": "read_plus_proposal",
 "params": {"proposal_id": "proposal-<uuid>"}}
```

Response: `diff_content` (unified diff), `diff_format`, `current_sha256`, `proposed_sha256`, `lines_added`, `lines_removed`

---

#### `approval_request.create`

```json
{"tool": "approval_request.create", "runtime_id": "openclaw", "mode": "read_plus_proposal",
 "params": {"proposal_id": "proposal-<uuid>"}}
```

Response: `approval_request_id`, `proposal_id`, `approval_status`, `created_at`, `delivery_confirmed`, `delivered_to` (list of paths), `next_action`

Approval artifact lands at: `07_LOGS/Operator-Briefs/`

---

### Prompts (read_plus_proposal or draft_execution)

#### `handoff.runtime_draft_frame`

```json
{"prompt": "handoff.runtime_draft_frame", "runtime_id": "openclaw", "mode": "read_plus_proposal"}
```

Returns static template text and `context_loaded: false` (no ambient vault reads at prompt serve time).

---

### Active V2 Tool (draft_execution only)

#### `workflow.invoke_bounded`

Available only to runtimes explicitly granted `draft_execution` in `runtime/mcp/config.yaml`.

```json
{"tool": "workflow.invoke_bounded", "runtime_id": "openclaw", "mode": "draft_execution",
 "params": {"workflow_id": "operator_today", "dry_run": true}}
```

Allowed workflow IDs: `operator_today`, `operator_close_day`.

Response: `workflow_id`, `invocation_status`, `aor_status`, `aor_audit_id`, `stage_reached`, `dry_run`, `output_artifacts`, `files_written`, `canonical_write: false`, `audit_reconciliation`, `retry_guidance`.

The response does not include generated brief text, raw vault content, apply/commit instructions, or schedule authorization.

Dry-run is the default operator smoke path:

```json
{"tool": "workflow.invoke_bounded", "runtime_id": "openclaw", "mode": "draft_execution",
 "params": {"workflow_id": "operator_today", "dry_run": true}}
```

One intentional live verification path may be used when the target artifact is known not to exist:

```json
{"tool": "workflow.invoke_bounded", "runtime_id": "openclaw", "mode": "draft_execution",
 "params": {"workflow_id": "operator_today",
            "inputs": {"date": "2026-04-21", "output_format": "json"},
            "dry_run": false}}
```

Success writes only the AOR-managed Operator-Briefs artifact listed in `output_artifacts` plus AOR/MCP audit records. If the predicted live output already exists, MCP returns `workflow_output_already_exists` before AOR is called. Treat that as a do-not-retry-blindly signal: inspect the listed artifact and the MCP/AOR audit records first.

---

## Registered Runtimes

| runtime_id | trust_tier | allowed_modes |
|---|---|---|
| `openclaw` | internal_runtime (1) | read_only, read_plus_proposal, draft_execution |
| `claude_code` | operator_runtime (2) | read_only, read_plus_proposal |
| `n8n` | external_orchestrator (3) | read_only only |
| `_unregistered` | unknown (3) | read_only only |

Unregistered runtime_ids fall back to `_unregistered` policy.

---

## Where Artifacts Land

| Artifact type | Location |
|---|---|
| Staged proposals | `.chaseos/mcp-proposals/` |
| Audit records | `07_LOGS/Agent-Activity/` |
| Approval artifacts | `07_LOGS/Operator-Briefs/` |
| AOR workflow artifacts from `workflow.invoke_bounded` | `07_LOGS/Operator-Briefs/` through AOR only |

For `workflow.invoke_bounded`, reconcile:
- AOR audit: `07_LOGS/Agent-Activity/{timestamp}__operator_today__{aor_audit_id[:8]}.json`
- MCP audit: `07_LOGS/Agent-Activity/{timestamp}__mcp__workflow.invoke_bounded__{request_id[:8]}.json`
- Output artifact: the relative path listed in `output_artifacts`

---

## Error Response Format

```json
{
  "request_id": "req-abc123",
  "ok": false,
  "error": {
    "code": "bad_json",
    "message": "...",
    "category": "input_error",
    "details": {}
  }
}
```

Error categories: `input_error`, `domain_error`, `system_error`

Common codes: `bad_json`, `bad_request`, `config_invalid`, `mode_denied`, `surface_unavailable`, `unknown_surface`, `proposal_not_found`, `protected_file_violation`, `audit_write_failed`, `artifact_write_failed`, `workflow_output_already_exists`, `workflow_invocation_audit_failed`

---

## V1 Limits and Non-Goals

- **No writes applied** — proposals are staged only; no write commits happen via MCP
- **No generic workflow invocation** — only `workflow.invoke_bounded` is live, only in `draft_execution`, and only for `operator_today` / `operator_close_day`
- **No blind duplicate live invocation** - first-release live invocations deny before AOR if the predicted Operator-Briefs output already exists
- **No schedule surfaces** — `schedule.intent.read` is deferred (V2)
- **No shell/git/browser bridges** — permanently excluded
- **No session persistence** — every request is stateless; no memory of prior requests
- **No ambient reads** — handlers read only from defined source files; no glob walks

---

*ChaseOS Runtime MCP - Phase 9 Pass 6C - 2026-04-21*


*Graph links: [[Vault-Map]]*
