---
title: Hermes Agent — ChaseOS Integration Position
type: architecture
status: active bounded Discord runtime lane and bounded bus workflow lane; approved workflows are `hermes_operator_today_shadow`, `hermes_review_execute`, and `hermes_watch`; Discord gateway lane remains shadow-only; advisory, bus-result, and draft/audit outputs only; OpenClaw remains active scheduled execution lane (see OPENCLAW.md)
created: 2026-04-08
version: 1.5
---

# HERMES.md — Hermes Agent ChaseOS Integration

> This document defines what Hermes Agent is inside ChaseOS, what layer it belongs to, and what it is and is not authorized to do.
> It is a positioning document, not a runtime contract. The runtime contract is in `06_AGENTS/Hermes-Adapter-Spec.md`.
> Hermes is a Phase 9 bounded operator runtime adapter — not a replacement for ChaseOS, not a second OS, not a canonical truth engine.
> Constitutional authority truth: `06_AGENTS/Runtime-Instance-Authority-Parity.md` — Hermes and OpenClaw are peer runtime instances with equal authority ceilings under AOR/Gate governance; implementation breadth may differ without implying secondary status.
> Current local truth: Hermes is an active bounded Discord runtime lane and a bounded coordination-bus runtime lane. Approved Hermes workflows are `hermes_operator_today_shadow`, `hermes_review_execute`, and `hermes_watch`. Discord-triggered execution remains limited to `hermes_operator_today_shadow`; bus review/planning/shadow-audit/developer co-development packets route through `runtime/agent_bus/` and may only produce bus results plus Agent-Activity audit writebacks. Shell, connectors, credentials, canonical promotion, protected-file writes, and ambient vault access remain blocked.
> Discord control-plane truth: `06_AGENTS/ChaseOS-Discord-Control-Plane.md` — Hermes is a live bounded Discord runtime lane under ChaseOS control-plane governance. `hermes-chat` is Hermes free-response chat lane, `chaseos-ops` is shared but mention-required, `change-log` is output-only, and Hermes may post to shared/output channels except OpenClaw-only runtime lanes.

---

## What Hermes Is

Hermes Agent is a long-running persistent operator runtime being evaluated for integration into ChaseOS as a **Phase 9 bounded operator runtime adapter**.

Hermes has capabilities that make it a strong candidate as a persistent execution surface:
- Persistent runtime memory
- Auto-generated and composable skills
- Scheduling and automation primitives
- Isolated subagent execution
- Browser and tool control
- Multiple execution backends
- Multi-platform gateway surfaces (Telegram, Discord, Slack, etc.)

These capabilities make Hermes more like a persistent operator runtime than a session-based chat surface. That is precisely why Hermes maps onto ChaseOS Phase 9 — where the architecture already expects autonomous operator runtimes, scheduled pipelines, and bounded long-running operator behavior.

---

## What Hermes Is Not

Hermes is **not**:
- A replacement for ChaseOS
- A second uncontrolled operating system
- A canonical truth engine or memory owner
- The default execution surface for all tasks
- Above or outside the ChaseOS control plane
- A direct route to canonical knowledge promotion
- A bypass of the ChaseOS Gate

ChaseOS remains:
- The constitutional OS and control plane
- The source of canonical truth
- The governance and promotion authority
- The writeback authority
- The audit and provenance layer

---

## How Hermes Fits — Architectural Framing

```
ChaseOS Control Plane (constitutional authority)
  └── AOR (Autonomous Operator Runtime) — Phase 9 execution infrastructure
        └── Hermes Adapter — one bounded execution surface among others
              ├── reads:    declared workflow inputs, approved vault zones
              ├── writes:   logs, drafts, quarantine captures, workflow outputs
              └── escalates: to ChaseOS Gate for any canonical promotion
```

**Plain English:** ChaseOS decides the rules. Hermes does the work. Hermes does not own canonical truth. Hermes writes only into approved surfaces. Promotion into durable knowledge goes through ChaseOS governance.

### Phase 10 Studio Ownership Boundary — Hermes/Optimus

Hermes/Optimus is the primary Phase 10 Studio implementation lane for bounded Studio surface work. In this context, "Studio implementation" means interface/product-shell work over existing ChaseOS contracts: read-only panels, preview/readiness surfaces, local static or localhost Studio UI slices, operator-confirmed wrappers, and approved audit/handoff artifact updates that keep `07_LOGS/Agent-Activity/` and related handoff records synchronized.

This Phase 10 ownership does **not** expand Hermes into Phase 9-and-below backend authority. Hermes/Optimus may surface, test, document, and route backend dependencies, but it must not solve missing AOR, Gate, Agent Bus, provider, credential, browser, lifecycle, approval-consumption, canonical writeback, or runtime dispatch contracts unless a separate lower-phase workflow explicitly grants that authority. Phase 10 Studio and Phase 11 Chat are operator surfaces over ChaseOS; they are not new canonical truth engines and do not bypass ChaseOS Gate or vault governance.

When Studio work is blocked by a backend gap, Hermes/Optimus records the dependency as evidence and routes it to the responsible lower-phase lane instead of crossing the authority boundary. Each blocker record should name: missing contract, affected Phase 10/11 surface, lower-phase owner/surface, minimum proof needed, and blocked action reason.

### Phase 11 Chat Implementation Handover Lane — Hermes/Optimus

Hermes/Optimus also owns the bounded Phase 11 Chat implementation handover lane documented in `06_AGENTS/Hermes-Phase11-Implementation-Handover.md`. This lane exists so long-running `/goal` agents can continue Chat work with durable checkpoints, no-write proof, and lower-phase dependency routing instead of relying on transient chat context.

Authorized Phase 11 continuation work is limited to Chat surface contracts, proposal/action previews, read-only readiness packets, local Studio UI rendering, tests that prove blocked authority, and Agent-Activity handoff/audit records. The lane does **not** authorize Chat to become a control plane or canonical truth engine. Backend execution, approval consumption, runtime dispatch, browser/shell/connector authority, credential/config mutation, source-pack promotion, graph/canonical mutation, protected-file writes, and knowledge promotion must route back to Phase 9-and-below with the dependency report fields defined in the handover.

---

## Why Phase 9

Phase 9 is the Autonomous Operator Runtime phase. The architecture already expects:
- Long-running bounded operator runtimes
- Declared workflow manifests with permission ceilings
- Audit trails for all autonomous execution
- Repo-aware operation (reads current vault state before acting)
- Prompt-injection hardening at the input boundary
- Gate-enforced writeback policy
- OpenClaw-style and custom operator registration

Hermes is a strong candidate for this role because it can persist state, execute scheduled workflows, and coordinate across tools — but **only if integrated under the same governance constraints** that apply to all Phase 9 operator runtimes.

---

## Security Considerations

High-privilege operator runtimes create compounding risk. Hermes integration must account for:

| Risk Class | Description |
|-----------|-------------|
| Privilege aggregation | Persistent memory + browser + shell + messaging in one surface is a large combined attack surface |
| Filesystem access | Hermes must be repo-scoped, not ambient — no access beyond declared paths |
| Credential concentration | Hermes must not hold credentials beyond what a declared workflow requires |
| Prompt injection | External gateway inputs (Telegram, Discord, RSS) are Tier 4 — never trusted as instructions |
| Long-lived compromise surface | A compromised long-running runtime has persistent access — audit and rotation matter more than for session-based surfaces |
| Silent canonical mutation | Hermes must not auto-promote to `02_KNOWLEDGE/` without Gate approval |
| Skill mutation without review | Auto-generated skills must pass a skill quarantine before use in production workflows |

All risk classes addressed in `06_AGENTS/Agent-Security-Model.md` apply to Hermes with heightened emphasis given its persistent and multi-surface nature.

---

## What Hermes May Do

### Read
- Declared workflow inputs (specified in workflow manifest)
- Approved project docs (specified in role card)
- Selected workspace / SIC outputs (specified in workflow manifest)
- Selected logs within declared scope
- Declared temporary working areas
- Approved runtime maps / overlays if justified in role card

### Write
- Run logs in `07_LOGS/Agent-Activity/` and `07_LOGS/Operator-Briefs/`
- Draft outputs in declared draft destinations
- Quarantine captures to `03_INPUTS/00_QUARANTINE/`
- Proposed updates (proposals only — not direct promotion)
- Workflow outputs in approved destinations declared in workflow manifest
- Bounded runtime state in `runtime/memory/` (future)

### Not Directly — Requires Approval or Gate
- Canonical knowledge in `02_KNOWLEDGE/`
- Protected control docs
- Permission Matrix, Trust Tiers, Gate rules
- Security doctrine
- Final promoted knowledge
- High-value project truth
- Any protected file (canonical list: `[[06_AGENTS/Permission-Matrix|Permission-Matrix]]` Section 2)

---

## What Hermes Must Not Get on Day One

Do NOT grant Hermes:
- Full-vault write access
- Broad credential access
- Direct final promotion into `02_KNOWLEDGE/`
- Unmanaged email/chat ingestion with action rights
- Broad browser + shell + repo + messaging in one unrestricted role
- Ambient multi-repo roaming
- Unsupervised canonical doc editing
- Uncontrolled doctrine editing
- Hidden skill mutation with no review path

---

## Integration Pass Sequencing

### Pass 1 — Planning / Binding Pass (COMPLETE — 2026-04-08)
Architecture and governance documentation only. Creates:
- `HERMES.md` (this file)
- `06_AGENTS/Hermes-Adapter-Spec.md`
- `06_AGENTS/Hermes-Workflow-Boundaries.md`
- `06_AGENTS/Hermes-Memory-Boundary.md`
Updates registry, backends, feature register, roadmap.
Status: **Docs Only**

### Pass 2 — Runtime Boundary Pass (BOUNDED SHADOW ACTIVE)
Built for the single approved shadow workflow:
- Scoped runtime config (`.chaseos/hermes_config.yaml`)
- Repo allowlists (explicit path declarations)
- Draft/audit writeback target declaration
- Log/audit output path wiring through AOR Stage 7
- Fail-closed config checks for deny-by-default approval, disabled connectors, and forbidden canonical promotion

### Pass 3 — Workflow Enablement (BOUNDED BUS ACTIVE)
Hermes workflow breadth is now expanded only for coordination-bus review and bounded bus-analysis packets:
- `hermes_review_execute` handles review tasks through the coordination bus and returns structural results plus Agent-Activity audit writebacks
- `hermes_watch` handles review dispatch plus bounded `planning`, `shadow-audit`, and `developer-co-development` task packets
- `chaseos runtime daemon --runtime hermes --daemon-interval N` is the direct operator-controlled way to keep the Hermes coordination-watch loop live: it refreshes bus heartbeat/state, claims eligible Hermes-bound tasks, dispatches only the declared Hermes handlers, and writes bus results/audit writebacks
- Studio Settings -> Runtime Controls can now start/stop the Hermes coordination daemon and the local Hermes gateway launcher separately, and can set `Manual`, `Start with ChaseOS`, or gateway `Start with Windows` mode. This is operator-control only; it does not grant Hermes provider, shell, memory, or canonical-promotion authority.
- Scheduled briefings (`operator_today`, `operator_close_day`) remain live AOR/OpenClaw workflows, not general Hermes workflows
- Research synthesis drafts, repo maintenance jobs, capture helpers, delivery, shell, browser, and connector workflows remain deferred for Hermes

### Pass 4 — Gateway Surfaces

Current status: **DISCORD LANE ACTIVE — BOUNDED.** Hermes is an active bounded Discord runtime lane on this machine.

Local launcher status (2026-05-25): Hermes gateway process launch is live-proven on this host through the ChaseOS-managed Windows/WSL launcher and Studio Settings control surface. Messaging-channel authority remains bounded by the Discord control-plane rules below.

Reboot proof update (2026-05-25): the managed Windows/WSL gateway launcher is now idempotent (`2026.05.25-wslservice-idempotent-autostart`) and live host evidence shows Ubuntu WSL2 running, the Hermes WSL gateway process present, `127.0.0.1:18791` listening, a visible `ChaseOS Hermes Gateway` window, matching installed Startup-folder launcher content, and `ChaseOS-Hermes-Coordination-Watch` registered in Task Scheduler. This is still not full reboot/logon completion: the activation report remains `live-awaiting-reboot-proof` until a real post-reboot verification artifact exists.

Gateway configuration update (2026-05-25): the visible Hermes Gateway warning was confirmed as Hermes private gateway configuration readiness, not ChaseOS Gate policy and not a WSL launch failure. Hermes Optimus applied the backup-first private config bootstrap. ChaseOS now resolves the active Hermes home at `<WSL_HOME>/runtimes/hermes-home/.env`, and `runtime hermes-gateway-config --action status --json` reports `gateway_ready: true`, `allowlist_status: configured`, `messaging_platform_status: configured`, and `redaction_guard_passed: true` without exposing IDs or tokens. Studio Settings -> Runtime Controls now shows a Hermes Gateway Allowlist row with `Check`, `Add ChaseOS Operator`, and `Set IDs`; live writes require operator confirmation and record a redacted approval event. A fresh gateway restart observation is still required before claiming the old warning disappeared from a newly started gateway process. Durable runtime-ops doc: `02_KNOWLEDGE/Runtime-Ops/Hermes-Gateway-Autostart-and-Configuration.md`. Closeout: `07_LOGS/Build-Logs/2026-05-25-ChaseOS-hermes-gateway-allowlist-button.md`.

Portable startup approval update (2026-05-25): the Hermes gateway startup surface no longer hard-codes the Windows user path or WSL user in the lifecycle record. `runtime/lifecycle/hermes.lifecycle.yaml` now declares dynamic placeholders for the Windows profile, Startup folder, vault path, WSL vault path, and optional WSL user. The generated launcher uses the default WSL user unless `CHASEOS_HERMES_WSL_USER` is explicitly set, and uses `${HOME}/.local/bin/hermes gateway run` instead of `<WSL_HOME>`. Studio `system_start` mode now delegates to the lifecycle startup-surface toggle so approval markers/events are recorded instead of writing Startup-folder files directly. The current host launcher was re-applied through `startup-surface-toggle --confirm`, producing approval-recorded mutation `startup-surface-hermes-gateway-enable-20260525T115946Z-bb09366e8f`. Cross-system installer UI prompting remains a next pass, but the lifecycle default is now portable and approval-logged.

Active Discord capabilities:
- Discord gateway connection (bot account registered in `.chaseos/discord_instance_bindings.yaml`)
- Free-response interaction in `hermes-chat`
- Mention-required interaction in `chaseos-ops`
- Observe bounded approval records in `approvals` for declared Hermes actions
- Post to Hermes-only output lanes (`alerts-hermes`, `debug-hermes`)
- Post to shared output lanes (`alerts-workflows`, `alerts-security`, `debug-adapters`, `runtime-debug`, `audit-writeback`, `artifact-paths`, `operator-runs`, `change-log`, `server-notes`, `docs-snippets`)
- Keep raw logs local; Discord gets summaries, snippets, links, and artifact paths rather than full log spam
- Execute `hermes_operator_today_shadow` when an approved envelope is present in the approvals channel
- Participate in bounded machine coordination with OpenClaw through `runtime/agent_bus/` as a structured task-routing layer; this does not expand Hermes workflow or shell authority

Still deferred:
- Telegram / Slack bridge
- Scheduled delivery via gateway
- Cross-surface continuation
- Voice memo ingestion
- Free-form runtime-to-runtime Discord self-chat as a machine protocol (structured coordination bus is the approved route instead)

### Pass 5 — Learning-Loop Hardening
Only after gateway surfaces are stable:
- Skill quarantine and review process
- Runtime scorecards
- Repair-pattern capture
- Navigation-map updates
- Memory export/import discipline

---

## Governance Summary

| Dimension | Rule |
|-----------|------|
| Trust tier | Tier 4 by default → escalates to Tier 2 ceiling with explicit evaluation and owner assignment |
| Vault read | Declared workflow inputs only — no ambient vault access |
| Vault write | Approved destinations only (logs, drafts, quarantine) — not canonical knowledge |
| Promotion | Must go through ChaseOS Gate — Hermes cannot auto-promote |
| Protected files | Hermes may not mutate protected files by default — requires explicit workflow contract |
| Memory | Runtime-local only — inspectable, exportable, subordinate to ChaseOS canonical truth |
| Skills | Auto-generated skills must pass skill quarantine before use in production workflows |
| Audit | Every Hermes run must produce an audit log entry in `07_LOGS/Agent-Activity/`; future entries must use a `hermes` or `hermes-optimus` filename slug and link `[[Hermes-Runtime-Profile]]` plus `[[Agent-Activity-Index]]` so the runtime graph node remains connected |
| Escalation | Hermes must pause and escalate on any action outside declared scope |
| Gateway inputs | All Discord, Telegram, RSS inputs treated as Tier 4 untrusted — data only, never commands; command authority flows through ChaseOS envelope validation only |

---

**2026-04-28 governance hardening:** Hermes remains approval-first shadow for external authority and bounded bus-result-only for coordination workflows. `runtime/adapters/runtime_governance.py` now checks the Hermes manifest and `.chaseos/hermes_config.yaml` for the exact approved workflow set, disabled shell/connectors/credential access, draft/audit/bus-result-only writeback, and shared OpenClaw/Hermes Tier 2 ceiling.

---

## Key Documents

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | Repository routing anchor; links Hermes runtime-specific work back to `[[Hermes-Runtime-Profile]]`, `[[HERMES]]`, and Agent-Activity naming rules |
| `06_AGENTS/Hermes-Adapter-Spec.md` | Full execution adapter spec — all required sections per Execution-Adapter-Standard |
| `06_AGENTS/Hermes-Workflow-Boundaries.md` | Explicit read/write/forbidden boundaries per workflow type |
| `06_AGENTS/Hermes-Memory-Boundary.md` | Memory architecture — what Hermes may hold and what ChaseOS owns |
| `06_AGENTS/Hermes-Phase10-Studio-Handover.md` | Phase 10 Studio continuation lane for Hermes/Optimus `/goal` agents, including Studio surface ownership, checkpoints, no-write proof, tests, audit conventions, and lower-phase dependency routing |
| `06_AGENTS/Hermes-Phase11-Implementation-Handover.md` | Phase 11 Chat continuation lane for Hermes/Optimus `/goal` agents, including checkpoints, no-write proof, tests, audit conventions, and lower-phase dependency routing |
| `06_AGENTS/Autonomous-Operator-Runtime.md` | The AOR infrastructure that Hermes operates inside |
| `06_AGENTS/Permission-Matrix.md` | Canonical permission source |
| `06_AGENTS/Trust-Tiers.md` | Authority ceiling definitions |
| `06_AGENTS/Agent-Security-Model.md` | Threat model and fail-closed principles |
| `06_AGENTS/Execution-Adapter-Standard.md` | Conformance standard all adapters must follow |

---

*Graph links: [[CLAUDE]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[OPENCLAW]] · [[OpenClaw-Runtime-Profile]] · [[Chaser-Agent-Runtime-Profile]] · [[Codex-Runtime-Profile]] · [[Hermes-Adapter-Spec]] · [[OpenClaw-Adapter-Spec]] · [[Runtime-Navigation-Map]] · [[06_AGENTS/Runtime-InterAgent-Coordination-Bus|Runtime-InterAgent-Coordination-Bus]] · [[Runtime-Instance-Authority-Parity]] · [[Hermes-Workflow-Boundaries]] · [[Hermes-Memory-Boundary]] · [[Hermes-Phase10-Studio-Handover]] · [[Hermes-Phase11-Implementation-Handover]] · [[ChaseOS-Discord-Control-Plane]] · [[06_AGENTS/Autonomous-Operator-Runtime|Autonomous-Operator-Runtime]] · [[06_AGENTS/Permission-Matrix|Permission-Matrix]] · [[06_AGENTS/Trust-Tiers|Trust-Tiers]] · [[06_AGENTS/Agent-Security-Model|Agent-Security-Model]] · [[06_AGENTS/Execution-Adapter-Standard|Execution-Adapter-Standard]] · [[Agent-Activity-Index]]*

*HERMES.md — ChaseOS Hermes Agent Integration Position*
*Updated: 2026-04-28 (bounded Hermes bus workflow breadth added for review/watch planning, shadow-audit, and developer co-development packets; no shell/connector/canonical authority added)*
*Version: 1.4 | Created: 2026-04-08 | Updated: 2026-04-20 (bounded shadow active; broader Hermes workflow/gateway/shell authority remains blocked) | Updated: 2026-04-20 (Discord control-plane spec linked; Hermes remains not Discord-enabled) | Updated: 2026-04-21 (Hermes Discord Activation Alignment Pass — Hermes promoted to active bounded Discord runtime lane; Pass 4 gateway status updated; governance summary updated; header/callout rewritten) | Updated: 2026-04-25 (runtime-instance authority parity ruling linked; local implementation breadth distinguished from constitutional authority) | Updated: 2026-04-28 (OpenClaw/Hermes governance verifier linked; shadow-only execution envelope machine-checked) | Updated: 2026-05-25 (Studio Settings runtime gateway controls and local Hermes gateway launch proof recorded)*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
