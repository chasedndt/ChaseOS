# Autonomous-Operator-Runtime.md
## ChaseOS — Autonomous Operator Runtime Feature Architecture

> The Autonomous Operator Runtime (AOR) is the OS-level execution infrastructure layer for ChaseOS. It is the system that binds chosen runtimes, models, and tools to ChaseOS memory, repositories, execution rules, writeback targets, and audit requirements — enabling bounded autonomous operation under explicit policy.

**Version:** 1.8
**Created:** 2026-03-23
**Updated:** 2026-05-10
**Status:** PARTIAL — Phase 9 Passes 1–6 complete:
- Pass 4 (2026-04-09): all four first-wave workflows live (`operator_today`, `operator_close_day`, `graph_hygiene`, `graduate_ideas`); `graph_hygiene` and `graduate_ideas` are proposal-only; Hermes shadow activation proven; OpenClaw designated as active experimental lane (governance configured)
- Graph Substrate Passes 1+2 (2026-04-10): `runtime/graph/` subsystem built — deterministic structure extraction, persistent snapshot artifacts, topology-aware clustering, graph-first routing, AOR advisory narrowing seam; 87 tests passing; feeds into future AOR Stage 5 enrichment
- Architecture Pass (2026-04-14): Operator-Briefing-Architecture.md, Scheduling-Intent-Architecture.md, ChaseOS-MCP-Server.md created; Phase 9 truth-synced
- **OpenClaw LIVE (2026-04-15):** OpenClaw installed and operational on this machine; Discord transport operational; `operator_today`, `operator_close_day`, and `graph_hygiene` executed through the bounded OpenClaw → `chaseos run` → AOR path; scheduled execution proven through OpenClaw cron/control plane; Discord delivery operational after channel config fix
- Native ChaseOS schedule intent (`runtime/schedules/`) is built and validated; Operator Briefing V2 handlers for `operator_today` and `operator_close_day` are live; MCP server implementation and event-triggered workflows remain next
- Multi-repo/multi-directory enforcement hardening (2026-04-28): `runtime/aor/path_policy.py` now enforces vault-relative manifest paths, role-card write scopes, required-read containment, handler writeback traversal blocking, `repo_scope` fail-closed semantics, and tests for denied cross-root writes / undeclared read escape.

---

## What the Autonomous Operator Runtime Is

The Autonomous Operator Runtime is not a workflow. It is not a specific feature. It is the infrastructure that makes autonomous workflows possible inside ChaseOS's governed system.

It is the layer that answers: *how does a runtime operate autonomously inside ChaseOS without abandoning governance?*

The AOR provides:
- Execution scheduling and trigger management
- Runtime and model selection per workflow
- Bounded autonomy with explicit permission ceilings
- Repo-aware operation (runtime reads current vault state before acting)
- Prompt-injection hardening for all automated inputs
- Mandatory audit trails for every autonomous action
- Multi-repo targeting under declared policy
- Long-running runtime support (not just session-based execution)
- Runtime memory layering (Layer C and D from `Agent-Memory-Architecture.md`)
- Graceful failure handling that leaves the vault in a known-good state

**What the AOR is not:**
- Not a specific workflow (that is Scheduled Briefing Pipelines or other operator workflows)
- Not a replacement for session-based Claude Code execution
- Not a general-purpose automation engine
- Not a bypass of the ChaseOS Gate or governance rules

---

## Why the AOR Exists

Phase 9's purpose is to move ChaseOS from session-based execution to persistent, scheduled, and event-driven operator workflows. The challenge is: how do autonomous systems operate inside a tightly governed vault without undermining the governance?

The AOR solves this by:
1. Making autonomy explicit and policy-bounded, not ambient
2. Requiring every workflow to declare its full scope before execution
3. Enforcing the same Gate, taxonomy, and writeback rules that apply to human-assisted sessions
4. Logging all autonomous actions with the same discipline as manual sessions
5. Supporting long-running runtimes without sacrificing inspectability

The result: autonomous operation that is safe, auditable, and improvable — not a black box that modifies the vault without accountability.

---

## Core AOR Principles

### 1. Bounded Autonomy

No workflow runs without a declared permission boundary. The AOR does not grant general vault access to any runtime. Every autonomous workflow declares:
- What it is allowed to read
- What it is allowed to write
- What external systems it may contact
- What it may NOT do
- Its maximum execution scope

If a workflow tries to exceed its declared boundaries, it halts and logs.

### 2. Repo-Aware Operation

Before any autonomous workflow executes, the AOR loads current vault state: sprint focus (`Now.md`), relevant project OS files, and active sprint priorities. The runtime reasons from current, verified state — not cached assumptions.

This is the autonomous equivalent of the session-start context check that Claude Code performs when a user starts a session.

### 3. Prompt-Injection Hardening

All inputs to autonomous workflows are classified by trust tier before they enter reasoning:
- External data feeds → Tier 4 (untrusted, quarantined)
- SIC workspace outputs → Tier 3 (research, not canonical)
- Vault canonical state → Tier 1–2 (trusted, current)

No automated input at Tier 4 may be treated as an instruction. The AOR enforces this at the input-adapter boundary.

### 4. Mandatory Audit Trails

Every autonomous action is logged:
- What workflow ran
- What runtime executed it
- What inputs were used (with trust tier)
- What outputs were produced
- What was written to the vault
- Whether the run succeeded or failed and why

Audit logs go to `07_LOGS/Agent-Activity/` and future `runtime/audit/` structures. No silent execution.

### 5. Gate Rules Apply

Autonomous workflows are not exempt from ChaseOS Gate rules. All writeback from autonomous runs goes through Gate. Automated workflows may write to log folders. They may not auto-promote to `02_KNOWLEDGE/` without a Gate-approved promotion step. They may not modify protected files.

### 6. Graceful Failure

If an autonomous workflow encounters an error, it:
1. Halts immediately
2. Writes a failure log to `07_LOGS/Agent-Activity/`
3. Notifies the user (if a delivery adapter is configured)
4. Leaves the vault in the same state it was in before the run started

No partial writes. No silent corruption. The vault is always in a known-good state.

---

## AOR Components

### Workflow Registry

A central registry of all declared autonomous workflows, their manifests, and their current status. Located in future `runtime/workflows/` directory and referenced in `06_AGENTS/Agent-Registry.md`.

Each registered workflow has:
- Unique workflow ID
- Trigger schedule
- Runtime binding (which execution adapter)
- Input adapter declarations
- Output and writeback targets
- Guardrail profile
- Enabled/disabled flag
- Last run status

### Runtime Binding

The AOR binds a workflow to a specific ChaseOS execution adapter. The adapter supplies the model and tools; the AOR supplies the governance, context, and policy.

Supported adapter bindings:
- Claude / Anthropic lane (current — Tier 2; reference implementation)
- **OpenClaw** (LIVE — active bounded operator runtime adapter on this machine; operator_today, operator_close_day, graph_hygiene proven through OpenClaw → AOR path; Discord transport operational; scheduled execution proven through OpenClaw cron/control plane; Tier 4 default → Tier 2 ceiling; see `OPENCLAW.md` and `06_AGENTS/OpenClaw-Adapter-Spec.md`)
- OpenAI Agent Harness (planned — Tier 2 ceiling)
- Local/Open-Source Harness (future — Tier 2 ceiling)
- n8n Workflow Runtime (planned — conditional Tier 2)
- Hermes Agent (bounded shadow + coordination-bus workflows only; approved set: `hermes_operator_today_shadow`, `hermes_review_execute`, `hermes_watch`; not an active broad adapter lane; see `HERMES.md`)

### Runtime Coordination Bus

For multi-runtime work, the AOR now recognizes a ChaseOS-owned coordination substrate under `runtime/agent_bus/`.

This bus:
- coordinates ownership and handoff state between runtimes
- does not grant new execution permissions
- should now be treated as ingress-aware by default when a runtime is controlled through multiple channels, threads, topics, or future operator surfaces
- must remain generic for future runtime lanes rather than encoding Hermes/OpenClaw-only assumptions into the substrate
- does not replace workflow manifests, role cards, Gate, or audit requirements
- exists so dual-runtime work can be durable and inspectable without turning Discord into the machine-state protocol
- is now the required structured coordination path for coordination-sensitive cross-runtime work originating from harness/runtime ingress surfaces

### Execution Policy Engine

The component that evaluates whether a workflow action is within its declared scope before allowing it. Every tool call, file write, external API call, delivery action, and coordination-sensitive cross-runtime handoff is checked against the workflow's manifest and the relevant ChaseOS-owned structured-state rule before execution.

If an action is not in the manifest, the AOR:
1. Blocks the action
2. Logs the attempted scope violation
3. Halts the workflow
4. Notifies the user

### Operator Memory Layer

The AOR maintains a memory layer for each workflow and runtime:
- **Workflow execution history** — every run's inputs, outputs, and outcomes
- **Runtime behavioral profile** — feeds into the Agent Identity Ledger (see `Agent-Memory-Architecture.md`)
- **Corrective context** — lessons learned from failed runs, applied to future runs
- **Runtime Navigation Map** — the evolving per-runtime overlay of preferred vault routes, trusted zones, known failure points, safe writeback paths, and escalation boundaries (see `06_AGENTS/Runtime-Navigation-Map.md`)

Before each autonomous workflow run, the AOR consults the active runtime's Navigation Map to inform route selection, context pre-loading strategy, risk avoidance, and escalation decision points. The RNM does not grant expanded permissions — it makes the runtime more efficient within its already-defined permission scope.

This memory is stored in `runtime/memory/` (future) and referenced by the AOR before each run.

---

## Multi-Repo / Multi-Directory Policy

**Status:** PARTIAL / VERIFIED TARGETED. This is a formal ChaseOS feature, not an implicit assumption. Current executable enforcement is vault-root-only and fail-closed for cross-repo execution.

The AOR explicitly governs whether and how autonomous workflows access multiple repositories or directories. By default, access is single-repo and vault-root bounded. Runtime reads and writebacks must be vault-relative, must not contain parent traversal, and must resolve inside the active vault root before execution continues.

Current implementation truth:
- workflow manifests validate `writeback_targets`, top-level `required_reads`, and `repo_scope`
- role cards validate `write_scope`, `forbidden_write_zones`, and concrete read-scope lists
- AOR Stage 5 resolves required reads under `vault_root` before checking existence
- AOR Stage 7 resolves handler writeback paths under `vault_root` before creating directories or writing files
- path traversal such as `07_LOGS/Operator-Briefs/../../outside.md`, absolute paths, and drive-qualified paths are blocked
- `repo_scope.primary_repo` must be `.`
- `repo_scope.cross_repo_access: true` requires an explicit `policy_ref` or `policy_path`
- `repo_scope.extra_dirs` remains non-executable until a future cross-repo policy evaluator is implemented

### Run Manifest: Repository and Directory Scope

Current executable workflow manifests use vault-relative scope:

```yaml
repo_scope:
  primary_repo: "."
  extra_dirs: []
  cross_repo_access: false
  writeback_targets:
    - "07_LOGS/Operator-Briefs/"
required_reads:
  - "00_HOME/Now.md"
```

### Scope Rules

| Scope type | Default | To enable |
|-----------|---------|-----------|
| Primary repo read | Enabled only through declared required reads / role-card reads | Declare vault-relative paths |
| Primary repo write | Scoped to declared targets only | Declare `writeback_targets` |
| Extra directory read | Disabled | Future explicit policy evaluator required |
| Extra directory write | Disabled | Future explicit policy evaluator required |
| Cross-repo edits | Disabled | `cross_repo_access: true` plus `policy_ref` / `policy_path`; still non-executable in current AOR |
| External network access | Disabled | Explicit input adapter or delivery adapter declaration |

### Why This Matters

Without explicit multi-repo policy, autonomous runtimes have no clear boundary on what they can access. The AOR treats every directory beyond the primary repo as excluded unless explicitly declared. This prevents workflows from accidentally reading or modifying unrelated repositories, personal files, or system directories.

---

## OpenClaw-Style and Custom Operator Support

The AOR is explicitly designed to support future OpenClaw-style and custom operator runtimes. These are high-autonomy, long-running operator processes that may have more complex execution patterns than standard session-based agents.

**How custom operators fit into the AOR:**
- They are registered in the workflow registry as any other workflow
- They must declare a manifest with full scope, permission ceiling, and audit requirements
- They are assigned a trust tier (Tier 4 by default for new custom operators, escalating with explicit user grants)
- They do not get ambient vault access — every access is manifested and logged
- They interact with ChaseOS through the same input/output/writeback interface as any other AOR workflow

**Custom operators enable:**
- Full local operator power without abandoning governance
- Multi-backend runtime support (operator may span Anthropic + local model)
- Repo-aware operations across multiple declared directories
- Multi-repo targeting under policy
- Long-running autonomous task execution with checkpoint logging
- Future: operator-level autonomy bounded by explicit permission ceilings

**What they cannot do:**
- Modify protected files without user approval
- Auto-promote to `02_KNOWLEDGE/` without Gate
- Access directories not declared in their manifest
- Execute without producing an audit trail

---

## Relationship to Other ChaseOS Components

| Component | Relationship |
|-----------|-------------|
| **Scheduled Briefing Pipelines** | SBP is one workflow type that the AOR executes. AOR is the infrastructure; SBP is the use case. |
| **Source Intelligence Core** | SIC can be a runtime resource for AOR workflows. AOR workflows may query SIC workspaces as an input adapter. |
| **ChaseOS Gate** | AOR enforces Gate rules during autonomous execution. No autonomous workflow bypasses the Gate. |
| **Agent Memory Architecture** | AOR populates Layer D (workspace-local) and Layer E (execution history). It also feeds the Agent Identity Ledger and Runtime Navigation Map (both Layer C). |
| **Multi-Repo Policy** | AOR is the enforcement layer for multi-repo policy. Every run's manifest declares its repo scope. |
| **n8n Workflow Runtime** | n8n is a potential orchestration backend for AOR. It would be registered as an execution adapter. |
| **ChaseOS VentureOps** | VentureOps is the business/application layer above AOR. It packages AOR-executed workflows into monetizable workflow packs, proof artifacts, scorecards, and offer paths. VentureOps does not grant new execution authority; every workflow still runs through AOR manifests, Gate checks, approvals, and audit logs. |

---

## AOR Development Phases

The AOR is a Phase 9 feature. Its development will proceed in passes:

**Phase 9 — Pass 1–4 complete (2026-04-09):**
- [x] Operator workflow format defined — 8-stage engine + manifest schema live
- [x] Workflow registry and manifest-based execution — `runtime/aor/registry.py` live
- [x] Role card system — `runtime/aor/role_cards.py` + `06_AGENTS/role-cards/` live
- [x] Task-type router — `runtime/aor/task_router.py` + `task_type_table.yaml` live
- [x] First-wave handlers: `operator_today`, `operator_close_day`, `graph_hygiene`, `graduate_ideas` — all live
- [x] Graceful failure behavior verified — escalation path active; vault left in known-good state
- [x] Audit records writing to `07_LOGS/Agent-Activity/`

**Phase 9 — Graph Substrate Passes 1+2 complete (2026-04-10):**
- [x] `runtime/graph/` subsystem built — extractor, index, topology, reporter, query, builder
- [x] AOR advisory narrowing seam (`runtime/graph/advisory.py`) — graph-informed candidate reads for Stage 5; advisory-only, fail-open
- [x] Snapshot diffing (`runtime/graph/diff.py`) — structural change detection
- [x] Cross-file resolution (`runtime/graph/resolver.py`) — import nodes resolved to file nodes; INFERRED edges
- [x] 87 tests passing; 1667 nodes / 2303 edges on real vault

**Phase 9 — Architecture Pass (2026-04-14):**
- [x] Operator-Briefing-Architecture.md — v2 briefing design with four-layer model
- [x] Scheduling-Intent-Architecture.md — native ChaseOS scheduling intent design
- [x] ChaseOS-MCP-Server.md — MCP server placement and architecture

**Phase 9 — Implementation updates (2026-04-15 to 2026-04-20):**
- [x] Native schedule intent implementation — `runtime/schedules/`, schedule intent files, CLI list/show/enable/disable/validate
- [x] Operator Briefing V2 handlers — `operator_today` and `operator_close_day` four-layer model, carry-forward, runtime records, bounded Operator-Briefs writeback
- [x] Hermes shadow proof — `hermes_operator_today_shadow` writes draft/audit artifacts only under fail-closed config
- [x] Hermes bounded bus workflow breadth — `hermes_review_execute` and `hermes_watch` handle review plus planning/shadow-audit/developer co-development bus packets with bus-result and Agent-Activity writebacks only

**Phase 9 — Still to build:**
- [ ] n8n deployed and registered with scoped permission grant
- [ ] Additional scheduled workflow families beyond the current operator briefing schedule path
- [ ] At least one event-triggered workflow
- [ ] MCP server for ChaseOS vault access deployed (`runtime/mcp/`)
- [ ] `runtime/audit/` formal directory (currently writes to `07_LOGS/Agent-Activity/`)
- [ ] Multi-repo policy enforcement in AOR (schema defined; enforcement to be built)

**Phase 9+ (iterative):**
- Runtime memory layering (per-workflow and per-runtime memory stores)
- Agent Identity Ledger first implementation
- Runtime Navigation Map first population for Claude/Anthropic lane; curation protocol established
- Multi-backend orchestration (workflows spanning Claude + OpenAI or local model)

---

## What Is Not In Scope for the AOR

These are explicitly deferred:
- Fully autonomous knowledge promotion (humans remain in the promotion loop)
- Unmonitored long-running runtimes (audit logging is non-negotiable)
- Ambient vault access for any runtime (every access is manifested)
- Bypassing Gate for convenience (even in automation)
- External network access without declaration

*2026-05-10 update: VentureOps relationship added as the business/application layer above AOR. This adds no new authority, no executable workflow, and no bypass around manifests, Gate checks, approvals, or audit logs.*

---

*Graph links: [[OpenClaw-Runtime-Profile]] · [[Vault-Map]] · [[Scheduled-Briefing-Pipelines]] · [[SIC-Architecture]] · [[Agent-Memory-Architecture]] · [[Runtime-Navigation-Map]] · [[ChaseOS-Gate]] · [[Feature-Register]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Operator-Briefing-Architecture]] · [[Scheduling-Intent-Architecture]] · [[ChaseOS-MCP-Server]] · [[Graph-Substrate-Architecture]]*

*Autonomous-Operator-Runtime.md — v1.6 | Created: 2026-03-23 | Updated: 2026-04-15 (OpenClaw status corrected to LIVE: installed, Discord transport operational, operator_today/operator_close_day/graph_hygiene proven through OpenClaw → AOR path, scheduled execution proven, v1.5 had stale "pending Node 24" language) | Previous: v1.5 2026-04-14 (architecture pass: Operator-Briefing-Architecture, Scheduling-Intent-Architecture, ChaseOS-MCP-Server referenced) | v1.4 2026-04-09 (Pass 4 complete: graph_hygiene + graduate_ideas live; Hermes shadow proven)*
