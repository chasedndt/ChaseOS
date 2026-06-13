---
title: ChaseOS MCP Workflow Invocation - Active V2 Surface
type: architecture-doc
status: live - v1.2 2026-04-21; Pass 6C operator-smoke hardening added
created: 2026-04-21
version: 1.0
phase: Phase 9
knowledge_class: system-operational
---

# ChaseOS MCP Workflow Invocation

> Design and implementation contract for the first deferred Runtime MCP surface to graduate: `workflow.invoke_bounded`.
>
> This is an active V2 surface as of Pass 6B. Pass 6C adds real-use duplicate guardrails and operator smoke guidance. Runtime MCP V1 remains live and unchanged.

---

## Product Role

`workflow.invoke_bounded` lets a registered Runtime MCP client request one explicitly allowlisted AOR workflow run without gaining generic execution authority.

It is a tool surface because it can cause AOR-managed side effects. It is not a command bridge, shell bridge, scheduler, browser bridge, generic handler dispatcher, or canonical writeback path.

The MCP server's role is narrow:

1. Resolve the requesting runtime and safety mode.
2. Check that `workflow.invoke_bounded` is available only in `draft_execution`.
3. Preflight the requested workflow against the frozen MCP invocation allowlist.
4. Route the invocation through AOR.
5. Return a bounded status response and envelope-owned MCP audit record.

MCP does not execute the workflow itself.

---

## First-Release Allowed Invocation Set

The first release of `workflow.invoke_bounded` allows exactly two workflow IDs:

| workflow_id | Workflow class | Required role card | Required manifest status | Required permission ceiling | Allowed Stage 7 writeback |
|---|---|---|---|---|---|
| `operator_today` | `operator-briefing` | `operator-briefing` | `active` | `no_protected_file_writes` | `07_LOGS/Operator-Briefs/` |
| `operator_close_day` | `operator-briefing` | `operator-briefing` | `active` | `no_protected_file_writes` | `07_LOGS/Operator-Briefs/` |

This is an exact allowlist, not a dynamic family wildcard. A future workflow with `task_type: operator-briefing` is still denied until a later design pass adds it to the MCP invocation allowlist.

The first release is draft-safe/log-safe only. It may produce operator briefing artifacts and AOR/MCP audit records. It may not write canonical vault state.

---

## AOR Routing Rule

`workflow.invoke_bounded` must route through AOR only.

Allowed implementation shape:

- MCP performs permission-envelope and allowlist preflight.
- MCP calls a single bounded AOR invocation API for the approved `workflow_id`.
- AOR remains responsible for manifest lookup, task classification, role card resolution, permission ceiling checks, required reads, workflow handler dispatch, Stage 7 writeback, and AOR audit.
- MCP records its own envelope audit for the MCP request.

Denied implementation shapes:

- Calling individual workflow handler modules directly from MCP.
- Accepting arbitrary handler names, module names, Python paths, CLI commands, or function names.
- Calling `chaseos run` through a subprocess.
- Reimplementing the AOR pipeline inside MCP.
- Treating schedule intent as invocation authorization.

If AOR denies or escalates the run, MCP must not override it.

---

## Required Preconditions

Before AOR is called, the MCP server must verify all of the following:

1. The requesting runtime is registered or otherwise explicitly handled by config.
2. The resolved safety mode is `draft_execution`.
3. `workflow.invoke_bounded` is present in the resolved permission envelope for that runtime and mode.
4. `workflow_id` is exactly `operator_today` or `operator_close_day`.
5. The workflow manifest exists under `runtime/workflows/registry/`.
6. The manifest `status` is `active`.
7. The manifest `task_type` is `operator-briefing`.
8. The manifest `role_card` is `operator-briefing`.
9. The role card exists under `06_AGENTS/role-cards/`.
10. The manifest `permission_ceiling` is `no_protected_file_writes`.
11. The manifest Stage 7 `writeback_targets` are limited to `07_LOGS/Operator-Briefs/`.
12. The role card `write_scope` allows only the declared log/audit destinations needed for the workflow.
13. The request inputs contain only keys declared by the selected workflow manifest.
14. No client-controlled path, handler, module, schedule, shell, git, browser, network, apply, commit, or approval field is present.
15. For non-dry-run requests, the predicted Operator-Briefs output path does not already exist.

AOR still performs its own checks. MCP preflight is an admission gate, not a substitute for AOR enforcement.

The duplicate-output guard is intentionally narrow. It derives only the two first-release Operator-Briefs paths from `workflow_id`, `date`, and `output_format`; it does not accept client-controlled paths and does not create a general idempotency framework.

---

## Allowed Request Inputs

The request shape is intentionally narrow.

| Field | Required | Rule |
|---|---|---|
| `tool` | yes | Must be `workflow.invoke_bounded`. |
| `workflow_id` | yes | Must be `operator_today` or `operator_close_day`. |
| `inputs` | no | Object containing only manifest-declared input keys for that workflow. Defaults to `{}`. |
| `dry_run` | no | Boolean. Defaults to `false`. If `true`, MCP routes to AOR dry-run behavior and no workflow writeback occurs. |

Allowed `inputs` by workflow:

| workflow_id | Allowed input keys |
|---|---|
| `operator_today` | `date`, `output_format` |
| `operator_close_day` | `date`, `open_loops`, `notes` |

Unknown input keys are denied with `workflow_inputs_invalid`. Values are summarized for audit, not copied into the MCP audit record as raw content.

---

## Output Constraints

The first release may produce only:

- A bounded MCP response summarizing the AOR result.
- AOR-managed operator briefing artifacts under `07_LOGS/Operator-Briefs/`.
- AOR audit records under `07_LOGS/Agent-Activity/`.
- MCP envelope audit records under `07_LOGS/Agent-Activity/`.

The MCP response may include:

- `workflow_id`
- `invocation_status`
- `aor_status`
- `aor_audit_id`
- `stage_reached`
- `output_artifacts` as paths and artifact types only
- `files_written` as relative paths
- `dry_run`
- `audit_reconciliation` with the AOR audit id and shared audit directory references
- `retry_guidance` warning that ambiguous completion must be reconciled before retry

The MCP response must not include full generated operator brief text, raw vault file contents, protected file contents, untrusted raw inputs, or any apply/commit instruction.

---

## Audit Requirements

Audit ownership stays envelope-owned for MCP:

- MCP handlers return structured audit metadata only.
- MCP handlers do not call `MCPAuditLogger` directly.
- The server/envelope layer writes the MCP audit record.
- AOR continues to write its own AOR audit record inside the AOR pipeline.

The MCP invocation audit record must include or be able to reconstruct:

- `request_id`
- `surface_id: workflow.invoke_bounded`
- `surface_class: tool`
- `runtime_id`
- `trust_tier`
- `safety_mode: draft_execution`
- `workflow_id`
- `workflow_allowlist_version`
- `manifest_status`
- `task_type`
- `role_card_id`
- `permission_ceiling`
- redacted `inputs_summary`
- `dry_run`
- preflight check outcomes
- AOR result status
- AOR `audit_id`
- AOR `stage_reached`
- relative `output_artifacts`
- relative `files_written`
- duplicate-output guard outcome when a live retry is blocked before AOR
- denial or error code when applicable

No successful invocation response may be returned unless the MCP envelope audit is written. If AOR has already returned and the MCP completion audit fails, MCP returns `system_error(workflow_invocation_audit_failed)`, does not re-run the workflow, and does not attempt a canonical rollback.

---

## Denied Cases

`workflow.invoke_bounded` must deny:

- Any workflow ID not in the exact first-release allowlist.
- Any inactive, draft, disabled, missing, or malformed workflow manifest.
- Any workflow whose manifest `task_type`, `role_card`, `permission_ceiling`, or `writeback_targets` drift from the required values above.
- Any missing role card.
- Any request outside `draft_execution`.
- Any unregistered runtime not explicitly granted `draft_execution`.
- Any request that supplies handler names, Python modules, paths, schedule IDs, shell commands, git operations, browser actions, network actions, apply/commit instructions, approval flags, or canonical write intents.
- Any schedule-coupled request such as "run if due" or "invoke schedule target".
- Any non-dry-run request whose predicted first-release Operator-Briefs output already exists; this returns `workflow_output_already_exists` before AOR is called.
- Any request that would write outside `07_LOGS/Operator-Briefs/` plus required AOR/MCP audit records.
- Any request to promote, patch, rewrite, or commit canonical vault state.

---

## Why This Is Bounded, Not Generic Execution

This surface remains bounded because:

- The allowlist contains exact workflow IDs, not workflow classes or handler names.
- MCP is not an execution engine; AOR owns execution.
- MCP never accepts arbitrary code, commands, modules, paths, or schedule IDs.
- The only active mode that can include it is `draft_execution`.
- The first release writes only draft/log artifacts and audit records.
- Canonical writeback remains excluded.
- Shell, git, browser, and network bridges remain excluded.

---

## Pass 6B Implementation Points

Pass 6B implemented this contract by updating or verifying:

- `ChaseOS-MCP-Module-Design.md` for the exact module/file additions.
- `ChaseOS-MCP-Internal-Flow.md` for the invocation request flow.
- `ChaseOS-MCP-Audit-Policy.md` for fail-closed invocation audit behavior and the invocation audit fields.
- `runtime/mcp/config.yaml` and config validation for `draft_execution` grants.
- `runtime/mcp/safety.py` surface availability for the active V2 mode.
- `runtime/mcp/tools/workflow_invoke.py` for the bounded AOR-only tool implementation.
- Tests for allowlist enforcement, mode denial, AOR routing, audit ownership, audit failure, denied workflows, and no deferred/excluded surface bleed.

Future changes to this surface require updating this contract before implementation.

---

*Graph links: [[Vault-Map]] · [[ChaseOS-MCP-Server]] · [[ChaseOS-MCP-Surface-Map]] · [[ChaseOS-MCP-Safety-Modes]] · [[ChaseOS-MCP-Guardrails]] · [[ChaseOS-MCP-Data-Contracts]] · [[ChaseOS-MCP-Diagrams]] · [[Autonomous-Operator-Runtime]]*

*ChaseOS-MCP-Workflow-Invocation.md - v1.2 | Created: 2026-04-21 | Updated: 2026-04-21 Pass 6C (`workflow.invoke_bounded` operator-smoke hardening; duplicate-output guard; audit reconciliation response metadata)*
