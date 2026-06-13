---
title: ChaseOS MCP Data Contracts - V1 plus Active V2 Invocation Contract
type: architecture-doc
status: frozen - v1.3 2026-04-21; V1 contracts preserved; workflow.invoke_bounded Pass 6C operator hardening reflected
created: 2026-04-19
version: 1.0
phase: Phase 9
knowledge_class: system-operational
---

# ChaseOS MCP Data Contracts

> First-pass request/response contract shapes for V1 MCP surfaces.
>
> These contracts are frozen for V1 and implemented by the Pass 4 stdio scaffold where they apply to the V1 server.
> They represent the intended wire format for each surface and remain the contract reference for future hardening.
>
> Pass 6B implements the active V2 contract for `workflow.invoke_bounded`. Pass 6C adds duplicate-output denial and bounded audit reconciliation metadata. V1 contracts remain preserved.
>
> Field names use snake_case throughout. Types are descriptive, not formal schema. No transport-specific details are included.

---

## Contract Conventions

**Request shape:** Every request includes the resource or tool name as an identifier, plus any parameters. Optional fields are marked `?`.

**Response shape:** Every response includes a `status` field (`ok` or `error`), a `served_at` ISO 8601 timestamp, and the payload. Errors include the error taxonomy field and message.

**Null vs absent:** A field that is not applicable returns `null`, not absent. Absent fields indicate a schema violation, not a logical null.

**Schema stability:** These field names are intended to be stable. Implementers must not rename fields without updating this document first.

---

## Resource Contracts

### `runtime.identity`

**Purpose:** Server self-description. Lowest-trust, always available.

**Request:**
```json
{
  "resource": "runtime.identity"
}
```

**Response:**
```json
{
  "status": "ok",
  "served_at": "2026-04-19T07:00:00Z",
  "server_name": "chaseos-mcp",
  "server_version": "0.1.0",
  "chaseos_phase": "Phase 9",
  "vault_root_confirmed": true,
  "transport": "stdio",
  "active_safety_mode": "read_plus_proposal"
}
```

**Notes:** `vault_root_confirmed` is `true` only if the server can verify the vault root path exists and is readable. If it cannot, startup should fail, not return `false` silently.

---

### `chaseos.current_truth`

**Purpose:** Curated vault snapshot for runtime context loading.

**Request:**
```json
{
  "resource": "chaseos.current_truth",
  "fields": ["sprint_focus", "current_phase", "active_domains", "recent_decisions", "open_loops"]
}
```

`fields` is optional. If omitted, only the safe default subset is returned:
- `sprint_focus`
- `current_phase`
- `active_domains`

Additional fields require an explicit `fields: [...]` request. If provided, only the listed fields are returned.

**Response:**
```json
{
  "status": "ok",
  "served_at": "2026-04-19T07:00:00Z",
  "snapshot_freshness": "live",
  "sprint_focus": "Phase 9 — MCP server design freeze pass",
  "current_phase": "Phase 9 — Operator Runtime (AOR + SBP) — ACTIVE",
  "active_domains": [
    "ChaseOS / System Infrastructure",
    "Trading Systems / Market Ops",
    "StrikeZone Crypto",
    "University"
  ],
  "recent_decisions": [
    {
      "date": "2026-04-19",
      "decision_type": "architecture",
      "summary": "MCP V1 surface map and safety modes frozen"
    }
  ],
  "open_loops": {
    "ChaseOS": ["MCP server Pass 3 file/module design", "MCP server Pass 4 scaffold/build"]
  }
}
```

**Source mapping (implementation-enforced, not client-visible):**
- `sprint_focus` → `00_HOME/Now.md` current phase line only
- `current_phase` → `00_HOME/Now.md` phase header only
- `active_domains` → `00_HOME/Now.md` Active Now table only
- `recent_decisions` → `07_LOGS/Decision-Ledger/Index.md` last 5 entries only
- `open_loops` → `01_PROJECTS/[Project]/[Project]-OS.md` open loops sections (declared project list only)

No field in this contract reads a protected file. No field reads raw quarantine content.

---

### `workflows.registry`

**Purpose:** Runtime view of what AOR workflows are registered and their statuses.

**Request:**
```json
{
  "resource": "workflows.registry",
  "filter": "active"
}
```

`filter` is optional. Values: `"active"`, `"draft"`, `"all"`. Default: `"active"`.

**Response:**
```json
{
  "status": "ok",
  "served_at": "2026-04-19T07:00:00Z",
  "filter_applied": "active",
  "workflow_count": 5,
  "workflows": [
    {
      "id": "operator_today",
      "name": "Operator Today Brief",
      "status": "active",
      "task_type": "operator-briefing",
      "trigger_type": "manual",
      "writeback_targets": ["07_LOGS/Operator-Briefs/", "07_LOGS/Agent-Activity/"]
    },
    {
      "id": "operator_close_day",
      "name": "Operator Close Day Brief",
      "status": "active",
      "task_type": "operator-briefing",
      "trigger_type": "manual",
      "writeback_targets": ["07_LOGS/Operator-Briefs/", "07_LOGS/Agent-Activity/"]
    }
  ]
}
```

**Notes:** Response includes `id`, `name`, `status`, `task_type`, `trigger_type`, and `writeback_targets` only. Handler code, manifest full content, and role card content are not included.

---

## Tool Contracts

### `proposal.submit`

**Purpose:** Stage a vault write proposal as an artifact. Does not apply the proposal.

**Request:**
```json
{
  "tool": "proposal.submit",
  "target_file": "01_PROJECTS/ChaseOS/ChaseOS-OS.md",
  "change_type": "update",
  "proposed_content": "...[full proposed file content]...",
  "rationale": "Update phase status to reflect MCP Pass 2B completion",
  "requester_context": "operator_today session 2026-04-19"
}
```

**Fields:**
- `target_file`: vault-relative path to the file being proposed for change
- `change_type`: `"create"` | `"update"` | `"delete"`
- `proposed_content`: full proposed content (for create/update); omit for delete
- `rationale`: why the change is proposed
- `requester_context`: runtime or session context for audit trail

**Response (success):**
```json
{
  "status": "ok",
  "served_at": "2026-04-19T07:00:00Z",
  "proposal_id": "prop-2026-04-19-a1b2c3",
  "proposal_status": "staged",
  "staged_at": "2026-04-19T07:01:00Z",
  "target_file": "01_PROJECTS/ChaseOS/ChaseOS-OS.md",
  "change_type": "update",
  "preliminary_validation": {
    "is_protected_file": false,
    "governance_warnings": []
  }
}
```

**Protected-file staging behavior:**

`proposal.submit` does not hard-reject solely because `target_file` is protected. It may stage the proposal, sets `governance_flags.is_protected_file: true` in the staged `ProposalArtifact`, and returns `preliminary_validation.is_protected_file: true`. The governance violation is surfaced by `proposal.validate`.

**Response (success with protected-file flag):**
```json
{
  "status": "ok",
  "served_at": "2026-04-19T07:00:00Z",
  "proposal_id": "prop-2026-04-19-p7q8r9",
  "proposal_status": "staged",
  "staged_at": "2026-04-19T07:01:00Z",
  "target_file": "06_AGENTS/Permission-Matrix.md",
  "change_type": "update",
  "preliminary_validation": {
    "is_protected_file": true,
    "governance_warnings": [
      "Target file is protected; proposal.validate will return a governance violation."
    ]
  }
}
```

---

### `proposal.validate`

**Purpose:** Validate a staged proposal against governance rules.

**Request:**
```json
{
  "tool": "proposal.validate",
  "proposal_id": "prop-2026-04-19-a1b2c3"
}
```

**Response:**
```json
{
  "status": "ok",
  "served_at": "2026-04-19T07:02:00Z",
  "proposal_id": "prop-2026-04-19-a1b2c3",
  "is_valid": true,
  "protected_file_flag": false,
  "errors": [],
  "warnings": [
    "Target file has not been read in this session — diff may be computed against stale base"
  ],
  "governance_checks": {
    "permission_ceiling_ok": true,
    "target_path_in_allowed_writeback_scope": true,
    "proposed_content_schema_valid": null
  }
}
```

**Notes:** `governance_checks.proposed_content_schema_valid` is `null` for free-form Markdown files. It is relevant for YAML files with known schemas (e.g., workflow manifests, schedule intents).

**Protected-file validation response:**
```json
{
  "status": "ok",
  "served_at": "2026-04-19T07:02:00Z",
  "proposal_id": "prop-2026-04-19-p7q8r9",
  "is_valid": false,
  "protected_file_flag": true,
  "errors": [
    {
      "error_type": "domain_error",
      "error_code": "protected_file_governance_violation",
      "message": "Target file is protected. MCP may stage and surface this proposal for human review, but it has no apply path."
    }
  ],
  "warnings": [],
  "governance_checks": {
    "permission_ceiling_ok": false,
    "target_path_in_allowed_writeback_scope": false,
    "proposed_content_schema_valid": null
  }
}
```

---

### `proposal.diff_preview`

**Purpose:** Generate a unified diff preview of a staged proposal for human review.

**Request:**
```json
{
  "tool": "proposal.diff_preview",
  "proposal_id": "prop-2026-04-19-a1b2c3"
}
```

**Response:**
```json
{
  "status": "ok",
  "served_at": "2026-04-19T07:03:00Z",
  "proposal_id": "prop-2026-04-19-a1b2c3",
  "target_file": "01_PROJECTS/ChaseOS/ChaseOS-OS.md",
  "diff_format": "unified",
  "current_sha256": "abc123...",
  "proposed_sha256": "def456...",
  "diff_content": "--- a/01_PROJECTS/ChaseOS/ChaseOS-OS.md\n+++ b/01_PROJECTS/ChaseOS/ChaseOS-OS.md\n@@ -1,3 +1,3 @@\n ...",
  "lines_added": 2,
  "lines_removed": 1
}
```

**Notes:** `diff_content` is a standard unified diff. It is a human-readable preview artifact — not an apply instruction. The server computes the diff against the live vault file, not a cached version.

---

### `approval_request.create`

**Purpose:** Create a human approval request artifact for a staged proposal and deliver it to operator log targets.

**Request:**
```json
{
  "tool": "approval_request.create",
  "proposal_id": "prop-2026-04-19-a1b2c3",
  "urgency": "normal",
  "human_context": "Proposing status update to ChaseOS-OS.md following MCP Pass 2B completion"
}
```

**Fields:**
- `urgency`: `"normal"` | `"high"`
- `human_context`: optional free-form context for the human reviewer

**Delivery target:** V1 always writes the human approval request artifact to `07_LOGS/Operator-Briefs/`. The audit record is written separately by the server/envelope layer through `MCPAuditLogger`.

**Response:**
```json
{
  "status": "ok",
  "served_at": "2026-04-19T07:04:00Z",
  "approval_request_id": "aprq-2026-04-19-x9y8z7",
  "proposal_id": "prop-2026-04-19-a1b2c3",
  "approval_status": "pending_human_review",
  "created_at": "2026-04-19T07:04:00Z",
  "delivery_confirmed": true,
  "delivered_to": ["07_LOGS/Operator-Briefs/2026-04-19-approval-request.md"],
  "next_action": "Human operator must review and approve before proposal can be applied"
}
```

**Critical note:** `approval_status: "pending_human_review"` is the terminal state for the MCP server. The server has no mechanism to transition this to `"approved"` or `"applied"`. That transition happens outside the MCP surface — a human reads the approval request artifact and takes action.

---

## Active V2 Tool Contract

### `workflow.invoke_bounded`

**Purpose:** Request one exact allowlisted AOR workflow invocation through MCP. Does not execute directly, does not call workflow handlers directly, does not apply canonical writes, and does not infer authorization from schedule intent.

**Availability:** Active V2 only, under `draft_execution`.

**Allowed first-release workflow IDs:**
- `operator_today`
- `operator_close_day`

**Request:**
```json
{
  "tool": "workflow.invoke_bounded",
  "runtime_id": "openclaw",
  "mode": "draft_execution",
  "params": {
    "workflow_id": "operator_today",
    "inputs": {
      "date": "2026-04-21",
      "output_format": "markdown"
    },
    "dry_run": false
  }
}
```

**Fields:**
- `workflow_id`: required; must be exactly `operator_today` or `operator_close_day`
- `inputs`: optional object; defaults to `{}`
- `dry_run`: optional boolean; defaults to `false`; if `true`, AOR validation runs without workflow writeback

**Allowed input keys:**

| workflow_id | Allowed input keys |
|---|---|
| `operator_today` | `date`, `output_format` |
| `operator_close_day` | `date`, `open_loops`, `notes` |

Unknown input keys are rejected. Client-controlled paths, handler names, module names, schedule IDs, shell commands, git operations, browser actions, network actions, apply/commit instructions, and approval flags are never valid inputs.

**Required preconditions:**

| Check | Required value |
|---|---|
| safety mode | `draft_execution` |
| manifest path | `runtime/workflows/registry/{workflow_id}.yaml` |
| manifest status | `active` |
| task type | `operator-briefing` |
| role card | `operator-briefing` |
| permission ceiling | `no_protected_file_writes` |
| Stage 7 writeback target | `07_LOGS/Operator-Briefs/` only |
| routing | AOR only |

**Response (success):**
```json
{
  "request_id": "req-id",
  "ok": true,
  "result": {
    "workflow_id": "operator_today",
    "invocation_status": "completed",
    "aor_status": "success",
    "aor_audit_id": "aor-audit-id",
    "stage_reached": "audit_record",
    "dry_run": false,
    "output_artifacts": [
      {
        "artifact_type": "operator_brief",
        "path": "07_LOGS/Operator-Briefs/2026-04-21-operator-today.md"
      }
    ],
    "files_written": [
      "07_LOGS/Operator-Briefs/2026-04-21-operator-today.md"
    ],
    "canonical_write": false,
    "audit_reconciliation": {
      "aor_audit_id": "aor-audit-id",
      "aor_audit_dir": "07_LOGS/Agent-Activity/",
      "mcp_audit_surface": "workflow.invoke_bounded",
      "mcp_audit_dir": "07_LOGS/Agent-Activity/"
    },
    "retry_guidance": "If completion status is ambiguous, do not retry blindly; reconcile the MCP audit, AOR audit, and output_artifacts first."
  }
}
```

**Response (denied):**
```json
{
  "request_id": "req-id",
  "ok": false,
  "error": {
    "code": "workflow_not_allowed",
    "message": "workflow.invoke_bounded may only invoke the first-release allowlist.",
    "category": "domain_error",
    "details": {
      "workflow_id": "graph_hygiene",
      "allowed_workflow_ids": ["operator_today", "operator_close_day"]
    }
  }
}
```

**Response (duplicate live output denied before AOR):**
```json
{
  "request_id": "req-id",
  "ok": false,
  "error": {
    "code": "workflow_output_already_exists",
    "message": "Predicted workflow output artifact already exists; live invocation was not started.",
    "category": "domain_error",
    "details": {
      "workflow_id": "operator_today",
      "existing_artifacts": [
        "07_LOGS/Operator-Briefs/2026-04-21-operator-today.md"
      ],
      "retry_guidance": "If completion status is ambiguous, do not retry blindly; reconcile the MCP audit, AOR audit, and output_artifacts first."
    }
  }
}
```

**Output constraints:**

The response returns status, AOR audit reference, stage reached, artifact paths, relative files written, audit reconciliation metadata, and retry guidance. It must not return full generated operator brief text, raw vault file contents, protected file contents, untrusted raw inputs, or apply/commit instructions.

**Audit constraints:**

MCP handlers return audit metadata only. The server/envelope layer writes the MCP audit record. AOR writes its own AOR audit record. The MCP audit record must include workflow ID, allowlist version, runtime ID, `draft_execution` mode, redacted input summary, preflight check outcomes, AOR status, AOR audit ID, stage reached, files written, and denial/error code when applicable.

---

## Error Taxonomy

All errors follow a three-tier taxonomy. Every error response includes `status: "error"`, an `error_type`, an `error_code`, and a `message`.

### input_error

Caused by a malformed, incomplete, or invalid request.

| error_code | Meaning |
|---|---|
| `missing_required_field` | Request is missing a required field |
| `unknown_resource` | Requested resource name is not recognized |
| `unknown_tool` | Requested tool name is not recognized |
| `invalid_field_value` | A field value is not in the allowed set (e.g., invalid filter value) |
| `unknown_proposal_id` | `proposal_id` does not refer to a staged proposal |
| `malformed_json` | Request body is not valid JSON |

### domain_error

Caused by a valid request that conflicts with governance rules or ChaseOS domain constraints.

| error_code | Meaning |
|---|---|
| `protected_file_governance_violation` | Validation found that a staged proposal targets a protected file |
| `surface_unavailable` | Requested surface is not available in the current safety mode or runtime grant |
| `permission_ceiling_exceeded` | Request exceeds the trust tier of the requesting runtime |
| `proposal_exceeds_writeback_scope` | Proposed target is outside the allowed writeback scope for this mode |
| `deferred_surface_not_active` | Requested surface is deferred and not active |
| `excluded_surface_permanent` | Requested surface is permanently excluded |
| `workflow_not_allowed` | `workflow.invoke_bounded` requested a workflow outside the exact first-release allowlist |
| `workflow_not_active` | Workflow manifest exists but is not `status: active` |
| `workflow_manifest_not_found` | Requested workflow manifest could not be found |
| `role_card_not_found` | Required role card could not be found |
| `workflow_permission_ceiling_exceeded` | Requested workflow does not match the required MCP invocation permission ceiling |
| `workflow_writeback_scope_denied` | Requested workflow writeback target exceeds the draft/log-safe scope |
| `workflow_inputs_invalid` | Invocation input keys or values are outside the allowed manifest-declared shape |
| `workflow_output_already_exists` | Non-dry-run invocation was not started because the predicted Operator-Briefs output artifact already exists |
| `workflow_schedule_coupling_denied` | Design-level denied case; implementation surfaces this as `workflow_inputs_invalid` when schedule/control keys appear |

### system_error

Caused by internal server or vault state issues.

| error_code | Meaning |
|---|---|
| `vault_root_unavailable` | Vault root path cannot be reached or verified |
| `source_file_read_error` | A required vault file could not be read |
| `proposal_staging_write_error` | Proposal artifact could not be written to staging area |
| `audit_log_write_error` | Audit record could not be written; fail-open/fail-closed behavior follows `ChaseOS-MCP-Audit-Policy.md` |
| `aor_invocation_failed` | AOR returned failure or could not complete the invocation |
| `workflow_invocation_audit_failed` | AOR returned but the MCP envelope audit record could not be written; no success response is permitted |
| `snapshot_timeout` | Vault state snapshot timed out |

**On system_error:** The server returns a clean error response and does not partially serve data. Partial data is worse than a clean error — the runtime cannot know what it received was complete.

---

## Schema Notes

These contracts are frozen for V1 and the active V2 `workflow.invoke_bounded` surface.

During implementation and hardening:
- Field names in this document are the intended names. Do not rename without updating this document.
- The contracts will be implemented as dataclasses or TypedDicts in Python, not as JSON Schema files (to avoid external dependency).
- Transport encoding is JSON via stdio. No binary formats. No streaming responses.
- The `served_at` timestamp is always UTC ISO 8601. No timezone-local timestamps.
- `proposal_id` and `approval_request_id` formats are implementation choices. The formats shown here are illustrative. The IDs must be unique, deterministic, and human-readable enough for audit trail use.

---

*Graph links: [[Vault-Map]] · [[ChaseOS-MCP-Server]] · [[ChaseOS-MCP-Surface-Map]] · [[ChaseOS-MCP-Workflow-Invocation]] · [[ChaseOS-MCP-Safety-Modes]] · [[ChaseOS-MCP-Guardrails]] · [[ChaseOS-MCP-Diagrams]] · [[Autonomous-Operator-Runtime]] · [[Scheduling-Intent-Architecture]]*

*ChaseOS-MCP-Data-Contracts.md - v1.3 | Created: 2026-04-19 | Updated: 2026-04-21 Pass 6C (`workflow.invoke_bounded` duplicate-output denial and audit reconciliation metadata; V1 contracts preserved)*
