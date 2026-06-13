---
title: ChaseOS MCP Module Design — Pass 3 Freeze
type: architecture-doc
status: frozen — v1.0 2026-04-20; module layout frozen; Pass 4 stdio scaffold implemented 2026-04-20
created: 2026-04-20
version: 1.0
phase: Phase 9
knowledge_class: system-operational
---

# ChaseOS MCP Module Design

> Defines the file and module layout for `runtime/mcp/`.
>
> This document translates the frozen V1 design (Pass 2B) into an implementation-ready module map.
> Pass 4 (scaffold/build) follows this layout for V1 surfaces. No new V1 surfaces were added.
>
> **`runtime/mcp/` exists as of Pass 4.** This document remains the module responsibility map.
> Pass 6B adds the active V2 `workflow.invoke_bounded` tool module without changing the V1 surface set.

---

## Design Principles Applied

All module decisions follow the conventions established in `runtime/aor/` and `runtime/schedules/`:

- stdlib-first: no external MCP SDK dependency in V1
- dataclasses for all structured types
- YAML for configuration
- fail-closed on validation errors
- audit records are immutable JSON, one file per event
- no circular imports between layers
- transport concerns isolated to one module

---

## Proposed Directory Tree

```
runtime/mcp/
├── __init__.py                  # public API re-exports
├── server.py                    # stdio MCP server entrypoint and dispatch loop
├── config.py                    # config loader — reads runtime/mcp/config.yaml
├── config.yaml                  # machine-readable server + runtime trust config
├── types.py                     # all shared dataclasses and enums
├── errors.py                    # error taxonomy and factory functions
├── safety.py                    # safety mode enforcement + permission envelope resolution
├── yaml_compat.py               # stdlib-first YAML fallback for config/manifests when PyYAML is absent
│
├── resources/
│   ├── __init__.py              # resource registry dict + resolve_resource()
│   ├── runtime_identity.py      # runtime.identity handler
│   ├── runtime_capabilities.py  # runtime.capabilities handler
│   ├── current_truth.py         # chaseos.current_truth handler + field resolver
│   ├── workflows.py             # workflows.registry + workflows.role_boundaries handlers
│   ├── permission_envelope.py   # runtime.permission_envelope handler
│   ├── handoff.py               # runtime.handoff.current handler
│   ├── audit_stream.py          # runtime.audit.recent handler
│   └── briefing.py              # operator.briefing.latest handler
│
├── tools/
│   ├── __init__.py              # tool registry dict + resolve_tool()
│   ├── proposal.py              # proposal.submit + proposal.validate + proposal.diff_preview
│   ├── approval.py              # approval_request.create
│   └── workflow_invoke.py       # workflow.invoke_bounded; AOR-only bounded invocation
│
├── prompts/
│   ├── __init__.py              # prompt registry + HANDOFF_FRAME_TEMPLATE constant
│   └── handoff_frame.py         # handoff.runtime_draft_frame content and metadata
│
├── staging/
│   ├── __init__.py              # staging store public API
│   └── store.py                 # ProposalStore: CRUD against .chaseos/mcp-proposals/
│
├── audit/
│   ├── __init__.py              # audit logger public API
│   └── logger.py                # MCPAuditLogger: immutable JSON records to 07_LOGS/Agent-Activity/
│
└── tests/
    ├── __init__.py
    └── test_runtime_mcp_v1.py   # consolidated V1 acceptance tests
```

**Implementation note:** Pass 4 keeps the frozen V1 surface modules and adds `yaml_compat.py` only to preserve stdlib-first config/manifest parsing on machines without PyYAML.

---

## Module Responsibilities

### Foundation Layer (no upward imports)

**`types.py`**
- All shared dataclasses: `MCPRequest`, `MCPResponse`, `MCPError`, `ProposalArtifact`, `AuditRecord`, `PermissionEnvelope`, `SafetyMode`
- All enums: `SurfaceClass` (resource/tool/prompt), `ErrorType` (input/domain/system), `ChangeType` (create/update/delete)
- No imports from other `runtime/mcp/` modules
- Stdlib only

**`errors.py`**
- Error factory functions: `input_error(code, message)`, `domain_error(code, message)`, `system_error(code, message)`
- Error code vocabulary as constants (mirrors `ChaseOS-MCP-Data-Contracts.md`)
- Imports: `types.py` only

**`config.py`**
- `load_config(vault_root=None) -> MCPConfig` — reads and validates `runtime/mcp/config.yaml`
- `MCPConfig` dataclass: server name/version, vault root override, default safety mode, runtime trust registry, staging path, audit path
- Fail-closed: config parse error → `MCPSystemError` raised at startup, server does not start
- Stdlib only (YAML parsing uses stdlib-compatible approach or explicit yaml import)

**`config.yaml`** (not a Python module — documented here for completeness)
- Canonical source of truth for: server identity, runtime trust tier assignments, safety mode grants, staging path, audit target path
- Content specification: see *Config Schema* section below

---

### Policy Layer

**`safety.py`**
- `SafetyModeEnforcer` class with three public methods:
  - `resolve_session_mode(runtime_id: str, requested_mode: str | None) -> SafetyMode` — determines the active mode for a session based on runtime registration and request
  - `resolve_permission_envelope(runtime_id: str, mode: SafetyMode) -> PermissionEnvelope` — builds the permission envelope from config + mode
  - `check_surface_available(surface_name: str, mode: SafetyMode) -> bool | MCPError` — returns True or a domain_error
- Imports: `config.py`, `types.py`, `errors.py`
- Does NOT read vault files directly
- Does NOT import from `resources/`, `tools/`, `staging/`, or `audit/`

---

### Transport Layer

**`server.py`**
- stdio MCP server: reads JSON from stdin, writes JSON to stdout, one message per line
- `run_server(vault_root=None) -> None` — the entry point called by `chaseos mcp start`
- Request dispatch: parse request → call `safety.py` for mode/envelope → route to resource/tool/prompt handler → receive response + audit metadata → write audit record via `MCPAuditLogger` → return response
- Error boundary: all unhandled exceptions produce a `system_error` response; server never crashes silently
- Owns all audit writes. Handlers return structured audit metadata only and do not call `MCPAuditLogger`.
- Imports: `config.py`, `safety.py`, `resources/__init__.py`, `tools/__init__.py`, `prompts/__init__.py`, `audit/logger.py`, `types.py`, `errors.py`
- Does NOT import from `staging/` for normal handler work; audit-failure rollback for `proposal.submit` is coordinated from the envelope using handler-returned rollback metadata
- Does NOT import from AOR engine, ChaseOS Gate, schedule loader, or SIC

---

### Domain Layer — Resources

**`resources/__init__.py`**
- `RESOURCE_REGISTRY: dict[str, Callable]` — maps resource URI strings to handler functions
- `resolve_resource(name: str) -> Callable | None`
- `list_available_resources(mode: SafetyMode) -> list[str]` — returns the resource names available in the given mode (all 9 for V1 modes)

**`resources/runtime_identity.py`**
- `handle_runtime_identity(vault_root, config, mode) -> MCPResponse`
- Returns: server_name, server_version, chaseos_phase, vault_root_confirmed, transport, active_safety_mode
- No vault file reads (uses config only)

**`resources/runtime_capabilities.py`**
- `handle_runtime_capabilities(vault_root, config, mode) -> MCPResponse`
- Returns: available resources, tools, prompts in current mode
- No vault file reads — reads from RESOURCE_REGISTRY, TOOL_REGISTRY, PROMPT_REGISTRY filtered by mode

**`resources/current_truth.py`**
- `FIELD_SOURCE_MAP: dict[str, str]` — hard-coded mapping from field name to vault-relative file path
- `SAFE_DEFAULT_FIELDS: list[str]` — `["sprint_focus", "current_phase", "active_domains"]`
- `read_field(field_name: str, vault_root: Path) -> Any` — reads only the required vault file for that field
- `handle_current_truth(request, vault_root) -> MCPResponse` — if no `fields` param, returns SAFE_DEFAULT_FIELDS only; explicit `fields` returns requested subset
- See *Field-to-Source Mapping* section for the frozen mapping

**`resources/workflows.py`**
- `handle_workflows_registry(request, vault_root) -> MCPResponse` — reads workflow manifests from `runtime/workflows/registry/*.yaml`, returns summary list (id, name, status, task_type, trigger_type, writeback_targets only)
- `handle_workflows_role_boundaries(request, vault_root) -> MCPResponse` — reads role cards from `06_AGENTS/role-cards/*.yaml`, returns name + write_scope + forbidden_write_zones summary only
- Does NOT return handler code or full manifest content

**`resources/permission_envelope.py`**
- `handle_permission_envelope(request, vault_root, config, mode, runtime_id) -> MCPResponse`
- Reads from config (runtime trust registry) + mode definition
- Returns: trust_tier, permitted_modes, active_mode, permitted_surfaces, forbidden_surfaces
- No vault file reads

**`resources/handoff.py`**
- `handle_handoff_current(request, vault_root) -> MCPResponse`
- Reads: `00_HOME/Now.md` (open loops section only) + `07_LOGS/Operator-Briefs/` most recent close note (carry-forward section only)
- Returns structured handoff fields: open_loops, carry_forward_status, sprint_alignment

**`resources/audit_stream.py`**
- `handle_audit_recent(request, vault_root) -> MCPResponse`
- Reads: `07_LOGS/Agent-Activity/*.json` — last N records by timestamp (N default 10, max 50)
- Returns: summary list with workflow_id/status/timestamp/files_written only — no full record content

**`resources/briefing.py`**
- `handle_briefing_latest(request, vault_root) -> MCPResponse`
- Reads: `07_LOGS/Operator-Briefs/` most recent file
- Returns: structured sections only (current phase, active domains, carry-forward flags, recent decisions count) — not full brief content

---

### Domain Layer — Tools

**`tools/__init__.py`**
- `TOOL_REGISTRY: dict[str, Callable]` — maps tool names to handlers
- `resolve_tool(name: str) -> Callable | None`
- `list_available_tools(mode: SafetyMode) -> list[str]` — returns tools for the given mode (empty for read_only; 4 tools for read_plus_proposal; V1 tools plus `workflow.invoke_bounded` for draft_execution)

**`tools/proposal.py`**
- `handle_proposal_submit(request, vault_root, staging_store, config) -> MCPResponse`
  - Validates request fields
  - Checks target_file against protected file list and sets `governance_flags.is_protected_file`; does not hard-reject solely because the target is protected
  - Checks permission ceiling
  - Calls `staging_store.stage(proposal_artifact)` — writes to `.chaseos/mcp-proposals/`
  - Returns: proposal_id, status="staged", staged_at, preliminary_validation, audit_metadata, rollback_metadata
- `handle_proposal_validate(request, vault_root, staging_store) -> MCPResponse`
  - Loads proposal from staging store
  - Runs governance checks: protected file flag, permission ceiling, writeback scope, YAML schema if applicable
  - Returns: is_valid, errors, warnings, governance_checks, audit_metadata
- `handle_proposal_diff_preview(request, vault_root, staging_store) -> MCPResponse`
  - Loads proposal from staging store
  - Reads current vault file (if exists)
  - Computes unified diff
  - Returns: diff_content, lines_added, lines_removed, sha256s, audit_metadata

**`tools/approval.py`**
- `handle_approval_request_create(request, vault_root, staging_store, config) -> MCPResponse`
  - Loads proposal from staging store
  - Generates human-readable approval request markdown
  - Writes approval request artifact to `07_LOGS/Operator-Briefs/YYYYMMDD-approval-request-{id}.md`

**`tools/workflow_invoke.py`**
- `workflow_invoke_bounded(params, config, envelope) -> HandlerResult`
  - Validates `workflow_id`, `inputs`, and `dry_run`
  - Enforces exact allowlist: `operator_today`, `operator_close_day`
  - Preflights manifest, status, task type, role card, permission ceiling, allowed inputs, and writeback target
  - Calls AOR via the bounded `runtime.aor.engine.run_workflow()` path only
  - Returns bounded status, AOR audit ID, stage reached, artifact paths, files written, and `canonical_write: false`
  - Returns structured audit metadata; does not call `MCPAuditLogger`
  - Does not call workflow handlers directly, spawn subprocesses, read schedules, or expose shell/git/browser/network behavior
  - Returns: approval_request_id, status="pending_human_review", created_at, delivered_to, audit_metadata

Tool handlers do not write audit records. The server/envelope calls `MCPAuditLogger` after handler completion and applies fail-open/fail-closed policy.

---

### Domain Layer — Prompts

**`prompts/__init__.py` + `prompts/handoff_frame.py`**
- `PROMPT_REGISTRY: dict[str, str]` — maps prompt name to template string
- `handle_prompt(name: str, mode: SafetyMode) -> MCPResponse` — returns template string
- `HANDOFF_FRAME_TEMPLATE` constant: the actual prompt text, defined in `handoff_frame.py`
- No vault reads. No staging. No audit writes (fail-open for prompts).

---

### Proposal Staging Layer

**`staging/store.py`**
- `ProposalStore(staging_dir: Path)` class
- `stage(artifact: ProposalArtifact) -> str` — writes artifact JSON to `.chaseos/mcp-proposals/`, returns proposal_id
- `read(proposal_id: str) -> ProposalArtifact | None`
- `rollback(proposal_id: str) -> None` — deletes a just-staged proposal only after `proposal.submit` audit failure
- `list_staged() -> list[str]` — returns proposal IDs (no content)
- Naming convention: `{YYYYMMDD-HHMMSS}__{proposal_id[:8]}.json` — see `ChaseOS-MCP-Proposal-Staging.md`
- Imports: `types.py`, `errors.py` only
- Does NOT import from `resources/`, `tools/`, `safety.py`, or `audit/`

---

### Audit Layer

**`audit/logger.py`**
- `MCPAuditLogger(audit_dir: Path)` class
- `log(surface_name, surface_class, request_id, runtime_id, mode, status, detail) -> None`
- Record format: JSON, one file per event, naming matches AOR pattern: `{timestamp}__mcp__{surface}__{request_id[:8]}.json`
- Called only by `server.py` / the shared request envelope; never by resource, tool, staging, or prompt handlers
- Imports: `types.py` only
- Does NOT import from any other `runtime/mcp/` module
- Does NOT import from AOR engine

---

## Config Schema (config.yaml)

```yaml
server:
  identity: chaseos-runtime-mcp
  version: "0.1.0"
  transport: stdio

safety:
  default_mode: read_only
  allowed_modes:
    - read_only
    - read_plus_proposal
    - draft_execution
  fail_closed_surfaces:
    - proposal.submit
    - workflow.invoke_bounded
  fail_open_surface_classes:
    - resource
    - prompt
  fail_open_surfaces:
    - proposal.validate
    - proposal.diff_preview
    - approval_request.create

paths:
  staging_dir: ".chaseos/mcp-proposals"
  audit_dir: "07_LOGS/Agent-Activity"
  operator_briefs_dir: "07_LOGS/Operator-Briefs"

runtimes:
  openclaw:
    trust_tier: "internal_runtime"
    allowed_modes:
      - read_only
      - read_plus_proposal
      - draft_execution
  claude_code:
    trust_tier: "operator_runtime"
    allowed_modes:
      - read_only
      - read_plus_proposal
  n8n:
    trust_tier: "external_orchestrator"
    allowed_modes:
      - read_only
  _unregistered:
    trust_tier: "unknown"
    allowed_modes:
      - read_only
```

**This config is the `runtime.permission_envelope` source.** The `permission_envelope.py` handler reads this config to determine trust tier and permitted modes for a given runtime. It does not read Trust-Tiers.md at runtime.

---

## Frozen Field-to-Source Mapping (chaseos.current_truth)

This mapping is a hard constant in `resources/current_truth.py`. It is not dynamic.

| Field | Source File | What Is Read |
|---|---|---|
| `sprint_focus` | `00_HOME/Now.md` | Current phase line (first `### Phase` heading and its paragraph) |
| `current_phase` | `00_HOME/Now.md` | Same section — phase status line |
| `active_domains` | `00_HOME/Now.md` | Rows from the "Active Now" table only |
| `recent_decisions` | `07_LOGS/Decision-Ledger/Index.md` | Last 5 table rows (date, decision_type, summary) only |
| `open_loops` | `01_PROJECTS/ChaseOS/ChaseOS-OS.md` (and equivalent per registered project list) | Open loops sections only |

**Safe default fields (returned when `fields` param is absent):** `sprint_focus`, `current_phase`, `active_domains`

**Requesting additional fields:** client must supply `fields: [...]` explicitly.

**No protected files appear in this mapping.** No credentials. No `.claude/` files.

---

## Dependency Direction Rules

These rules must be enforced during implementation. Circular imports are a hard stop.

```
Allowed import directions (→ = may import from):

server.py → safety.py, resources/, tools/, prompts/, audit/, config.py, types.py, errors.py
safety.py → config.py, types.py, errors.py
resources/* → types.py, errors.py  [may read vault files; no staging or audit imports]
tools/proposal.py → staging/, types.py, errors.py
tools/approval.py → staging/, types.py, errors.py
tools/workflow_invoke.py → runtime.aor.engine, config.py, types.py, errors.py, yaml_compat.py
prompts/* → types.py  [no vault reads; no staging; no audit]
staging/* → types.py, errors.py  [no resources; no tools; no safety; no audit]
audit/* → types.py  [no other runtime/mcp imports]
config.py → stdlib + yaml_compat.py only
types.py → stdlib only
errors.py → types.py only

Forbidden import directions:
- resources/* must NOT import from tools/, staging/, or safety.py
- resources/*, tools/*, staging/*, and prompts/* must NOT import from audit/
- staging/* must NOT import from resources/, tools/, or safety.py
- audit/* must NOT import from anything in runtime/mcp/ except types.py
- ANY module in runtime/mcp/ must NOT import from runtime.aor.engine except `tools/workflow_invoke.py`
- ANY module in runtime/mcp/ must NOT import from runtime.capture or runtime.source_intelligence
```

---

## What Is NOT In Pass 4

These are explicitly out of scope for the initial scaffold pass:

- `workflow.invoke_bounded` handler (deferred during Pass 4; implemented later in Pass 6B as active V2)
- `schedule.intent.read` handler (deferred surface — no handler file created)
- HTTP/SSE transport (stdio only in V1 — no transport switching infrastructure)
- Session state persistence (stateless by default — no session store module)
- Multi-runtime concurrency (stdio is single-session; concurrency is a future concern)
- `approved_write` mode enforcement (excluded from V1 — no mode file or handler)
- Authentication / connection tokens (stdio local-only; no auth module in V1)

**No placeholder stubs for deferred surfaces.** The module tree above is complete for V1. Deferred surfaces get modules when their pass arrives, not before.

---

## Permission Matrix Update (Completed in Pass 4)

`06_AGENTS/Permission-Matrix.md` now includes the concrete MCP server V1 row:

| Surface | Read (vault) | Create (files) | Edit (files) | Delete | Execute | Network |
|---|---|---|---|---|---|---|
| ChaseOS MCP Server | ✅ curated endpoints only | ✅ `.chaseos/mcp-proposals/`, `07_LOGS/Agent-Activity/`, `07_LOGS/Operator-Briefs/` (approval artifacts only) | ❌ | ❌ | ❌ | ❌ |

This row records the Pass 4 implementation identity. It does not grant edit/delete/execute/network authority.

---

*Graph links: [[Vault-Map]] · [[ChaseOS-MCP-Server]] · [[ChaseOS-MCP-Surface-Map]] · [[ChaseOS-MCP-Safety-Modes]] · [[ChaseOS-MCP-Internal-Flow]] · [[ChaseOS-MCP-Proposal-Staging]] · [[ChaseOS-MCP-Audit-Policy]] · [[ChaseOS-MCP-Data-Contracts]] · [[Autonomous-Operator-Runtime]] · [[Permission-Matrix]] · [[Trust-Tiers]]*

*ChaseOS-MCP-Module-Design.md — v1.0 | Created: 2026-04-20 | Phase 9 Pass 3 (MCP Module Design Freeze) | Pass 4 stdio scaffold implemented 2026-04-20*
