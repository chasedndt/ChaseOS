---
title: OpenClaw Agent — ChaseOS Integration Position
type: architecture
status: LIVE — active bounded runtime adapter lane on this machine; OpenClaw installed and operational; Discord transport/control surface operational; operator_today, operator_close_day, and graph_hygiene executed through OpenClaw → chaseos run → AOR path; scheduled execution proven through OpenClaw cron/control plane; Discord delivery operational
created: 2026-04-09
version: 1.2
---

# OPENCLAW.md — OpenClaw Agent ChaseOS Integration

> This document defines what OpenClaw Agent is inside ChaseOS, what layer it belongs to, and what it is and is not authorized to do.
> It is a positioning document, not a runtime contract. The runtime contract is in `06_AGENTS/OpenClaw-Adapter-Spec.md`.
> OpenClaw is the **active bounded runtime adapter lane** for this machine. Live execution is proven. Governance is enforced.
>
> **Scheduling distinction:** OpenClaw's own cron/control plane manages scheduled execution on this machine. ChaseOS native schedule intent (`runtime/schedules/`) is now built and validated; OpenClaw remains the external execution lane that reads ChaseOS intent and invokes `chaseos run`.
>
> **Discord control-plane distinction:** OpenClaw's Discord transport is operational, but Discord does not grant authority by itself. `openclaw-chat` is OpenClaw free-response chat lane, `chaseos-ops` is shared but mention-required, and `change-log` is output-only. Canonical shared Discord routing, approval, audit, and Hermes boundary rules are defined in `06_AGENTS/ChaseOS-Discord-Control-Plane.md`.
>
> **Coordination distinction:** runtime-to-runtime machine coordination is now bootstrapped through the ChaseOS-owned structured bus at `runtime/agent_bus/`. Discord remains visibility and operator interaction, not the machine-state source of truth.

---

## What OpenClaw Is

OpenClaw is a persistent long-running operator runtime being adopted as the **active experimental Phase 9 bounded operator adapter** for this machine.

Key capabilities relevant to ChaseOS integration:
- Persistent runtime process (not session-based)
- Native Windows support (WSL2 optional but not required on this machine)
- Node 24 runtime
- Runs tools directly on the host — full local filesystem access by default
- Workspace injects runtime control files including `AGENTS.md`, `SOUL.md`, and `TOOLS.md`
- Supports bounded operator workflows with declared toolsets

These capabilities make OpenClaw a strong candidate for:
- Running `chaseos run operator_today` and `chaseos run operator_close_day` as scheduled/triggered ops
- Operating as the execution surface for AOR-governed workflows
- Providing persistent operator memory across sessions
- Running its ChaseOS coordination daemon with `chaseos runtime daemon --runtime openclaw --daemon-interval N` so OpenClaw can keep a fresh Agent Bus heartbeat, claim eligible OpenClaw-bound tasks, and dispatch only declared OpenClaw workflow handlers

---

## What OpenClaw Is Not (in ChaseOS context)

OpenClaw is **not**:
- A replacement for ChaseOS governance
- A canonical truth engine or memory authority
- Above or outside the ChaseOS control plane
- A bypass of the ChaseOS Gate or protected-file rules
- Broadly authorized to modify vault content without declared scope
- The only execution surface for ChaseOS workflows

ChaseOS remains:
- The constitutional OS and control plane
- The source of canonical truth
- The governance and promotion authority
- The writeback authority
- The audit and provenance layer

OpenClaw operates **inside** ChaseOS governance, not above it.

**2026-04-28 governance hardening:** OpenClaw's host-level shell/filesystem capability is treated as a risk boundary, not a permission grant. ChaseOS-governed work remains limited to declared AOR/Gate surfaces, and the current OpenClaw/Hermes authority envelope is now machine-checked by `runtime/adapters/runtime_governance.py`.

---

## How OpenClaw Fits — Architectural Framing

```
ChaseOS Control Plane (constitutional authority)
  └── AOR (Autonomous Operator Runtime) — Phase 9 execution infrastructure
        └── OpenClaw Adapter — one bounded execution surface among others
              ├── reads:    ChaseOS control files + declared workflow context
              ├── executes: chaseos CLI commands (run, capture, intake)
              └── writes:   07_LOGS/Operator-Briefs/, 07_LOGS/Agent-Activity/ (first phase)
```

OpenClaw is one adapter binding in the AOR. The AOR supplies governance, context, and policy. OpenClaw supplies execution capability and persistence.

---

## The Injected File Problem

OpenClaw injects `AGENTS.md`, `SOUL.md`, and `TOOLS.md` into its workspace. ChaseOS already has `SOUL.md` as a protected canonical identity file.

**How ChaseOS resolves this:**

| OpenClaw file | ChaseOS mapping | Rule |
|---------------|-----------------|------|
| `SOUL.md` (injected) | Ignored or mapped to a runtime-local scratch file | ChaseOS's `SOUL.md` is protected and must NOT be overwritten by OpenClaw's injected version. If OpenClaw needs a soul/persona file, it should be scoped to `runtime/openclaw/` or a session-local path. |
| `AGENTS.md` (injected) | Maps to ChaseOS role cards (`06_AGENTS/role-cards/`) | The role card governs what OpenClaw's agent role may do in ChaseOS. `AGENTS.md` should reference or confirm the active role card, not redefine permissions. |
| `TOOLS.md` (injected) | Maps to ChaseOS's permitted tool set | OpenClaw's tool declarations must stay within what the AOR role card permits for the active workflow. |

**Governing rule:** OpenClaw's injected files are runtime configuration for OpenClaw's internal operation. They do not override ChaseOS canonical files. Any injected file that would conflict with a protected ChaseOS file is scoped to the OpenClaw runtime environment only.

---

## What OpenClaw Is Allowed First

In the **first bounded activation** (this machine, Phase 9):

**Allowed reads:**
- `CLAUDE.md` — routing anchor
- `00_HOME/Now.md` — sprint focus
- `06_AGENTS/OpenClaw-Adapter-Spec.md` — adapter contract
- Active Project-OS files for current domains
- `07_LOGS/Build-Logs/` and `07_LOGS/Operator-Briefs/` — context only

**Allowed executions:**
- `chaseos run operator_today` — via AOR path
- `chaseos run operator_close_day` — via AOR path
- `chaseos intake ls` and `chaseos intake dedup-stats` — read-only audit
- `chaseos runtime daemon --runtime openclaw --daemon-interval N` — operator-controlled coordination-watch loop for live Agent Bus dispatches; this does not grant broader shell, connector, protected-file, or canonical-promotion authority
- Studio Settings -> Runtime Controls can start/stop the OpenClaw coordination daemon and the local OpenClaw gateway launcher separately, and can set `Manual`, `Start with ChaseOS`, or gateway `Start with Windows` mode. This is operator-control only; it does not grant OpenClaw broader shell, connector, protected-file, or canonical-promotion authority.

**Allowed writes (via AOR writeback, not direct):**
- `07_LOGS/Operator-Briefs/` — operator briefs from governed AOR runs
- `07_LOGS/Agent-Activity/` — audit records from governed AOR runs

---

## What OpenClaw May Not Do (First Phase)

Even with host-level access, OpenClaw is constrained to the adapter boundary in the first phase:

- **No direct writes to `00_HOME/Now.md`** — Now.md is operator-updated, not autonomously written
- **No direct writes to `01_PROJECTS/`, `02_KNOWLEDGE/`, or `06_AGENTS/`** — project and knowledge files are operator-governed
- **No modification of protected files** (SOUL.md, CLAUDE.md, Principles.md, Operating-System.md, etc.)
- **No multi-repo access** — single-repo scope first
- **No connector invocations** (Discord, Telegram, Slack, external APIs) without explicit AOR workflow declaration
- **No autonomous knowledge promotion** — Gate rules apply
- **No override of AOR governance** — all writes route through Stage 7 writeback enforcement

Broader OpenClaw authority is unlocked only by explicit user grant and AOR manifest declaration.

---

## Relationship to Hermes

Hermes is not a secondary runtime in ChaseOS doctrine.
Per `06_AGENTS/Runtime-Instance-Authority-Parity.md`, Hermes and OpenClaw are peer runtime instances with equal authority ceilings under AOR/Gate governance.

Hermes and OpenClaw also share a ChaseOS-owned structured coordination substrate under `runtime/agent_bus/`. This is a bounded task-routing layer, not an authority expansion for either runtime. The substrate is now being upgraded as a **default ChaseOS coordination rule** so machine work can deconflict across channel/thread-aware ingress contexts and future runtimes, rather than assuming one runtime always equals one ingress lane.

Key differences for this machine should be described as implementation/state differences, not authority ranking:
- OpenClaw supports native Windows without WSL2 requirement
- OpenClaw's host-level execution model currently maps more directly to the local development workflow
- Hermes currently has a narrower enabled workflow set on this machine

See `HERMES.md`, `06_AGENTS/Hermes-Adapter-Spec.md`, and `06_AGENTS/Runtime-Instance-Authority-Parity.md` for Hermes-side governance and parity documentation.

### Phase 10 Studio Handoff Boundary

OpenClaw is not the Phase 10 Studio implementer by default. Hermes/Optimus owns bounded Studio surface continuation: UI/readiness panels, local-only Studio wrappers, proof summaries, and approved audit/handoff documentation.

OpenClaw's Studio-adjacent role is backend dependency tracking and lower-phase handoff support when its Windows-side/runtime execution context exposes blockers that Hermes/Optimus cannot resolve inside Phase 10 authority. OpenClaw should record those blockers as dependencies, not silently convert them into OpenClaw-owned Studio implementation. A valid backend dependency handoff includes: missing contract, affected Phase 10/11 surface, lower-phase owner/surface, minimum proof needed, and blocked action reason.

This keeps Studio and Chat aligned with the ChaseOS OS model: they are operator surfaces over AOR/Gate/Agent Bus/runtime contracts, not canonical truth engines and not authority escalators for either runtime.

---

## Relationship to Other ChaseOS Components

| Component | Relationship |
|-----------|-------------|
| **AOR** | OpenClaw is one AOR execution surface. AOR governs what OpenClaw may do. |
| **ChaseOS Gate** | Gate rules apply to all OpenClaw writeback — no bypass. |
| **operator_today / operator_close_day** | These are the first workflows OpenClaw should be able to invoke. |
| **Discord Control Plane** | Discord is a shared operator/control transport surface. OpenClaw may use `openclaw-chat` as its free-response lane, `chaseos-ops` as shared mention-required lane, and shared/output channels only within declared AOR scope and approval rules. |
| **Role Cards** | `operator-briefing` role card is the initial permission envelope. |
| **Permission Matrix** | OpenClaw's per-surface permission scope is governed by the Permission Matrix. |
| **Trust Tiers** | OpenClaw starts at Tier 4 default → Tier 2 ceiling maximum with explicit grant. |

---

## Current Live State

As of 2026-04-15, OpenClaw is fully live on this machine:

- OpenClaw installed and operational (Windows native, Node 24)
- Discord transport/control surface working
- `openclaw-chat` remains OpenClaw free-response lane; `chaseos-ops` is shared mention-required lane; shared output lanes include `audit-writeback`, `artifact-paths`, `operator-runs`, `change-log`, `server-notes`, `docs-snippets`, `alerts-workflows`, `alerts-security`, `debug-adapters`, and `runtime-debug`
- `operator_today` executed through the bounded OpenClaw → `chaseos run` → AOR path ✅
- `operator_close_day` executed through the bounded OpenClaw → `chaseos run` → AOR path ✅
- `graph_hygiene` executed through the bounded OpenClaw → `chaseos run` → AOR path ✅
- Scheduled jobs created in OpenClaw cron/control plane ✅
- Scheduled workflow execution proven operationally ✅
- Discord delivery for scheduled/operator summaries operational (after channel config fix) ✅
- AOR writeback and audit trail verified through the OpenClaw lane ✅
- Structured coordination bus bootstrap created under `runtime/agent_bus/` for Hermes ↔ OpenClaw task routing ✅

## Next Steps — Phase 9 Remaining

1. ~~**ChaseOS MCP Server**~~ — **COMPLETE** (`runtime/mcp/` V1 live; `workflow.invoke_bounded` active V2 live 2026-04-21)
2. ~~**OpenClaw schedule-source sync**~~ — **COMPLETE** (`runtime/openclaw/schedule_bridge.md` bridge contract + `chaseos schedule export --adapter openclaw`; ChaseOS owns intent, OpenClaw executes from ChaseOS-native intent 2026-04-21)
3. **Event-triggered AOR workflows** — add only after manifest, role card, and audit behavior are explicit
4. **Additional scheduled workflow families** — expand after the current operator briefing schedule path remains stable
5. **Expand OpenClaw permission scope** — as each bounded run is clean, unlock additional workflows per the trust tier progression in `06_AGENTS/OpenClaw-Adapter-Spec.md`

See `06_AGENTS/OpenClaw-Activation-Runbook.md` for detailed activation steps.

---

*Graph links: [[CLAUDE]] · [[OPENCLAW]] · [[OpenClaw-Runtime-Profile]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Chaser-Agent-Runtime-Profile]] · [[Codex-Runtime-Profile]] · [[OpenClaw-Adapter-Spec]] · [[Hermes-Adapter-Spec]] · [[Runtime-Navigation-Map]] · [[06_AGENTS/Runtime-InterAgent-Coordination-Bus|Runtime-InterAgent-Coordination-Bus]] · [[Runtime-Instance-Authority-Parity]] · [[ChaseOS-Discord-Control-Plane]] · [[06_AGENTS/Autonomous-Operator-Runtime|Autonomous-Operator-Runtime]] · [[06_AGENTS/Permission-Matrix|Permission-Matrix]] · [[06_AGENTS/Trust-Tiers|Trust-Tiers]] · [[06_AGENTS/ChaseOS-Gate|ChaseOS-Gate]] · [[Phase9-Adopted-Feature-Specification]]*

*OPENCLAW.md — v1.6 | Created: 2026-04-09 | Patched: 2026-04-14 (activation state clarified — governance-configured, not live; scheduling intent reference added; next steps updated) | Patched: 2026-04-15 (status corrected to LIVE — OpenClaw installed and operational; Discord transport working; bounded execution proven; scheduled execution proven) | Patched: 2026-04-20 (native ChaseOS schedule intent corrected to built; operator_today v2 no longer listed as next) | Patched: 2026-04-20 (Discord control-plane spec linked; Discord transport does not expand OpenClaw authority) | Patched: 2026-04-21 (Next Steps updated — MCP complete + schedule-source sync complete; schedule_bridge.md bridge contract live) | Patched: 2026-04-25 (relationship to Hermes rewritten around runtime-instance authority parity rather than alternate/deferred-lane framing) | Patched: 2026-04-28 (OpenClaw/Hermes governance verifier linked; host privilege clarified as risk boundary, not permission)*
