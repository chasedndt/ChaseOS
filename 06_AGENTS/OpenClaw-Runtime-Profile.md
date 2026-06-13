---
title: OpenClaw Runtime Profile
type: runtime-profile
status: active bounded execution lane — seeded runtime navigation profile
version: 0.1
created: 2026-04-24
updated: 2026-05-15
runtime: openclaw
owner: Sygnal
---

# OpenClaw Runtime Profile

> Human-readable runtime navigation profile for OpenClaw inside ChaseOS.
> This profile connects the shared Vault Map, the runtime navigation overlay, and the current Obsidian markdown/index structure so active runtime execution routes remain usable when ChaseOS is later represented in a standalone surface.

---

## 1. Role in the System

OpenClaw is the **active bounded runtime adapter lane** on this machine.

It is execution-oriented, schedule-aware, and tied closely to the live AOR path. It is not allowed to override ChaseOS governance, but it is the primary active runtime for bounded operator execution. Its live Agent Bus daemon command is `chaseos runtime daemon --runtime openclaw --daemon-interval N`, which keeps OpenClaw heartbeat/claim/dispatch state active without expanding its authority envelope.

Primary governance anchors:
- `OPENCLAW.md`
- `06_AGENTS/OpenClaw-Adapter-Spec.md`
- `06_AGENTS/ChaseOS-Discord-Control-Plane.md`
- `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
- `06_AGENTS/Runtime-Navigation-Map.md`
- `06_AGENTS/Runtime-Instance-Authority-Parity.md`

---

## 2. Preferred Read Routes

### A. Active operator execution work
1. `OPENCLAW.md`
2. `06_AGENTS/OpenClaw-Adapter-Spec.md`
3. `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
4. `runtime/agent_bus/Agent-Bus-Folder-Guide.md`
5. `06_AGENTS/Vault-Map.md`
6. `runtime/aor/`
7. `runtime/workflows/registry/`
8. `runtime/schedules/`

Why: OpenClaw's highest-value route is from adapter contract to shared routing to live runtime substrate.

### B. Runtime navigation/profile maintenance
1. `06_AGENTS/Runtime-Navigation-Map.md`
2. `06_AGENTS/OpenClaw-Runtime-Profile.md`
3. `runtime/memory/nav/openclaw/nav-map.json`
4. `runtime/Runtime-Layer-Guide.md`

Why: this keeps runtime execution truth and navigation overlay aligned.

### C. Output/index-sensitive work
1. `06_AGENTS/Vault-Map.md`
2. `07_LOGS/Build-Logs/Build-Logs-Index.md`
3. `07_LOGS/Agent-Activity/Agent-Activity-Index.md`
4. `07_LOGS/Decision-Ledger/Index.md`
5. target runtime output path

Why: OpenClaw should preserve the markdown-first output/index structure that will later need a clean standalone mapping.

---

## 3. Trusted Zones

OpenClaw currently navigates most safely in:
- `runtime/aor/`
- `runtime/workflows/registry/`
- `runtime/schedules/`
- `runtime/agent_bus/`
- `07_LOGS/Operator-Briefs/`
- `07_LOGS/Agent-Activity/`
- `runtime/memory/nav/`

These are execution-aligned, bounded, and already part of the declared runtime substrate.

---

## 4. Safe Writeback Paths

Current and preferred bounded write targets:
- `07_LOGS/Operator-Briefs/`
- `07_LOGS/Agent-Activity/`
- `runtime/memory/nav/openclaw/`
- `runtime/agent_bus/`

Important rule: OpenClaw can be the active execution lane without becoming an unbounded author. AOR, role cards, Gate, and protected-file boundaries still govern.

---

## 5. Risk Zones and Escalation Boundaries

### Risk Zones
- `01_PROJECTS/`
- `02_KNOWLEDGE/`
- `03_INPUTS/` outside declared workflow scope
- root governance docs
- undeclared connector/network expansion
- multi-repo expansion without explicit approval

### Escalate Immediately When
- a request falls outside active AOR workflow + role-card boundaries
- protected-file or canonical mutation is requested
- a new connector, browser, MCP, or multi-repo authority is implied rather than declared
- execution paths diverge from declared writeback/audit surfaces

---

## 6. Relationship to Obsidian Markdown Structure

OpenClaw should preserve the current markdown-first routing model, especially where execution leaves durable traces.

That means respecting:
- `06_AGENTS/Vault-Map.md` as the shared routing anchor
- log index notes as stable navigation surfaces
- immutable-style ledger/index destinations
- predictable file paths that can later be represented as standalone nodes and audit streams

OpenClaw should treat markdown path stability as part of runtime reliability, not as a cosmetic documentation detail.

## 6a. Live Coordination Daemon

When OpenClaw needs to participate in live Bus dispatches, the operator-controlled command is:

```powershell
chaseos runtime daemon --runtime openclaw --daemon-interval N
```

The daemon runs OpenClaw's coordination-watch loop: publish heartbeat/state, inspect eligible Agent Bus tasks, claim safe OpenClaw-bound work, dispatch declared OpenClaw workflow handlers, and write result/audit state. It is not a permission grant for arbitrary shell, connector, protected-file, or canonical-promotion work.

---

## 7. Relationship to the Future Standalone

This runtime profile is designed to bridge:
- **today's Obsidian vault + indexes + wikilinks**, and
- **tomorrow's standalone ChaseOS runtime cockpit / graph-native surface**

The stable bridge artifacts are:
- `06_AGENTS/Vault-Map.md`
- `06_AGENTS/OpenClaw-Runtime-Profile.md`
- `runtime/memory/nav/openclaw/nav-map.json`
- `runtime/schedules/`

These should later map to:
- a shared routing node
- an OpenClaw runtime profile node
- a machine-readable runtime navigation record
- an execution/scheduling node family

---

## 8. Setup / Bootstrap Awareness

OpenClaw should now treat ChaseOS setup/bootstrap scaffolding as part of runtime orientation, not just as static documentation.

That means OpenClaw should know that a deployable ChaseOS instance is expected to include a broader mandatory core than provider/integration setup alone.

### Core scaffold awareness set
OpenClaw should expect setup/init to eventually scaffold or validate at least these categories:
- root product/foundation files such as `README.md`, `PROJECT_FOUNDATION.md`, `ROADMAP.md`, `FORKING.md`
- identity and control files such as `SOUL.md`, `00_HOME/Now.md`, `00_HOME/Dashboard.md`, `00_HOME/Operating-System.md`, `00_HOME/Principles.md`, `00_HOME/Assistant-Contract.md`
- governance/routing files such as `06_AGENTS/Vault-Map.md`, `06_AGENTS/Permission-Matrix.md`, `06_AGENTS/Agent-Registry.md`, `06_AGENTS/Tool-Map.md`, `06_AGENTS/Handoff-Protocol.md`, `06_AGENTS/Trust-Tiers.md`, `06_AGENTS/Agent-Control-Plane.md`
- setup/runtime machine-readable files such as `runtime/setup_registry.json`, `runtime/setup_provider_profiles.json`, `runtime/setup_state.example.json`, `runtime/setup_state.schema.json`, `runtime/setup_state.json`, `runtime/bindings/`, `runtime/lifecycle/`, `runtime/state/`, and `runtime/policy/`
- operator index and log surfaces such as `07_LOGS/Build-Logs/`, `07_LOGS/Agent-Activity/`, `07_LOGS/Operator-Briefs/`, `07_LOGS/Documentation-History/`, and their related index notes
- runtime profile seeds for `openclaw`, `hermes`, and future runtime lanes

### Why this matters to OpenClaw
This matters because OpenClaw is the active bounded execution lane. If ChaseOS is deployed on a fresh machine, OpenClaw must be able to reason about whether the substrate it expects actually exists.

That means future setup/doctor/validate output should be legible to OpenClaw as part of runtime readiness, attachment awareness, and operator support.

### Discord Binding and Studio Control Surface Awareness

OpenClaw's current operator-facing transport is Discord, but the canonical authority remains ChaseOS. OpenClaw should treat `.chaseos/discord_instance_bindings.yaml` as the local, Git-ignored binding layer for Discord server/runtime/channel IDs and should treat `runtime/bindings/discord_instance_bindings.example.yaml` plus `04_SOPS/Discord-Control-Plane-Setup-SOP.md` as the Git-safe onboarding surfaces.

Current readiness surface:
- `python -m runtime.cli.main setup discord validate --json` validates required OpenClaw/Hermes control-plane channels without exposing raw IDs or secrets.
- Studio Dashboard includes `discord_control_plane_panel`, a read-only panel that reports binding validity, active runtime labels, bound channel counts, and planned runtime-control capabilities.
- Studio quick-open chats, thread creation, send-to-runtime-board, and cron/schedule management remain future or approval-gated actions. The current implementation is visibility and validation only.

OpenClaw must not treat Discord channel presence, Studio panel visibility, or local binding validity as execution permission. Execution still requires AOR, role-card, schedule, approval, and Gate compliance.

## 9. Self-Orientation Layer

OpenClaw now has a first machine-readable self-orientation layer under `runtime/memory/nav/openclaw/`.

Current self-state artifacts:
- `runtime/memory/nav/openclaw/state.json`
- `runtime/memory/nav/openclaw/capabilities.json`
- `runtime/memory/nav/openclaw/next-actions.json`
- `runtime/memory/nav/openclaw/self-report.json`
- `runtime/memory/nav/openclaw/nav-map.json`

These files are intended to let the runtime answer, in structured form:
- who it is
- what it is currently allowed to do
- what is blocked or deferred
- what its next valid actions are
- how it should orient through ChaseOS without claiming canonical authority

This is the first step from documentation-only runtime identity toward a self-describing runtime surface.

The `self-report.json` artifact is the first operator-facing condensation of that state: a single place where the runtime can summarize who it is, what it can do now, what is blocked, and what its next bounded moves are.

## 10. Current Profile Verdict

OpenClaw is best understood as the **active bounded execution runtime** whose routes must remain legible in both markdown and future standalone form.

Its strongest current value is:
- governed execution
- schedule-aware operation
- AOR-compatible writeback/audit traces
- runtime substrate continuity
- emerging machine-readable self-orientation

### Summary-context application
For how OpenClaw preferred routes, trusted zones, risk zones, safe writeback paths, and escalation points should become typed human-facing summaries in future standalone surfaces, see:
- `06_AGENTS/Runtime-Navigation-Overlay-Summary-Context-Application.md`

---

*Graph links: [[CLAUDE]] · [[OPENCLAW]] · [[OpenClaw-Runtime-Profile]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Chaser-Agent-Runtime-Profile]] · [[Codex-Runtime-Profile]] · [[OpenClaw-Adapter-Spec]] · [[Hermes-Adapter-Spec]] · [[Operator-Surface-Adapter-Spec]] · [[Runtime-Navigation-Map]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Runtime-Instance-Authority-Parity]] · [[ChaseOS-Discord-Control-Plane]] · [[Discord-Control-Plane-Setup-SOP]] · [[Vault-Map]] · [[Agent-Activity-Index]] · [[ChaseOS-Studio-Architecture]]*

*OpenClaw-Runtime-Profile.md — v0.3 | Created: 2026-04-24 | Updated: 2026-05-15 (Discord binding validator and Studio control-plane readiness added)*


*Graph links auto-wired by vault_hygiene (2026-04-24): [[CRON-SETUP-GUIDE]] . [[agents]] . [[coordination_bridge]] . [[schedule_bridge]] . [[soul]] . [[tools]]*
