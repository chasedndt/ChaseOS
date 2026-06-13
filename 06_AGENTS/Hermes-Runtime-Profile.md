---
title: Hermes Runtime Profile
type: runtime-profile
status: active bounded Discord runtime lane and coordination-bus lane — seeded runtime navigation profile
version: 0.1
created: 2026-04-24
updated: 2026-05-15
runtime: hermes
owner: Optimus
---

# Hermes Runtime Profile

> Human-readable runtime navigation profile for Hermes inside ChaseOS.
> This profile connects the shared Vault Map, the runtime navigation overlay, and the current Obsidian markdown index structure so the same routes can later be preserved in the standalone ChaseOS surface.

---

## 1. Role in the System

Hermes is a **bounded Discord runtime lane and bounded coordination-bus lane** inside ChaseOS.

Its live Agent Bus daemon command is `chaseos runtime daemon --runtime hermes --daemon-interval N`, which keeps Hermes heartbeat/claim/dispatch state active without expanding Hermes beyond its declared coordination handlers.

It is not the constitutional control plane, not the canonical truth owner, and not the current broad execution lane. Hermes operates best as:
- a coordination/runtime-chat lane
- a bounded shadow/advisory workflow lane
- a documentation, planning, and navigation-aware runtime
- a future candidate for richer runtime memory and browser-assisted work under explicit governance

Primary governance anchors:
- `HERMES.md`
- `06_AGENTS/Hermes-Adapter-Spec.md`
- `06_AGENTS/ChaseOS-Discord-Control-Plane.md`
- `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
- `06_AGENTS/Runtime-Navigation-Map.md`
- `06_AGENTS/Runtime-Instance-Authority-Parity.md`

---

## 2. Preferred Read Routes

### A. Discord/runtime coordination work
1. `HERMES.md`
2. `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
3. `06_AGENTS/ChaseOS-Discord-Control-Plane.md`
4. `runtime/agent_bus/Agent-Bus-Folder-Guide.md`
5. `06_AGENTS/Vault-Map.md`
6. `00_HOME/Now.md`

Why: Hermes should orient first through bounded runtime truth, then through shared routing truth, then through current system state.

### B. Runtime navigation/profile maintenance
1. `06_AGENTS/Runtime-Navigation-Map.md`
2. `06_AGENTS/Hermes-Runtime-Profile.md`
3. `runtime/memory/nav/hermes/nav-map.json`
4. `runtime/Runtime-Layer-Guide.md`

Why: this keeps markdown doctrine and machine-readable runtime memory aligned.

### C. Documentation/index-sensitive work
1. `CLAUDE.md` when the current task is being routed through Claude Code / repository harness conventions
2. `06_AGENTS/Vault-Map.md`
3. folder index notes such as `07_LOGS/Build-Logs/Build-Logs-Index.md`, `07_LOGS/Agent-Activity/Agent-Activity-Index.md`, and `02_KNOWLEDGE/Knowledge-Index.md`
4. destination note/path

Why: Hermes should preserve the markdown-first Obsidian navigation model while preparing for a later standalone node/index model.

---

## 3. Trusted Zones

Hermes currently navigates most safely in:
- `06_AGENTS/` for governance-heavy reads
- `07_LOGS/Agent-Activity/` for audit-oriented outputs
- `07_LOGS/Operator-Briefs/` for advisory/shadow outputs
- `runtime/agent_bus/` for bounded dual-runtime coordination state
- `runtime/memory/nav/` for bounded runtime navigation state

These are trusted because they align with Hermes's bounded-role posture: read-heavy governance, explicit audit surfaces, and future runtime-local memory.

---

## 4. Safe Writeback Paths

Current and preferred bounded write targets:
- `07_LOGS/Agent-Activity/`
- `07_LOGS/Operator-Briefs/`
- `runtime/agent_bus/`
- `runtime/memory/nav/hermes/`

Important rule: safe writeback here means **governance-compatible**, not independent authority. Vault Map, role cards, Permission Matrix, and Gate still win.

---

## 5. Risk Zones and Escalation Boundaries

### Risk Zones
- `01_PROJECTS/`
- `02_KNOWLEDGE/`
- root governance docs
- protected files
- unrestricted browser/shell/connector expansion
- multi-repo work without explicit control-plane approval

### Escalate Immediately When
- a request asks Hermes to act beyond the approved workflow set
- canonical promotion is requested
- a protected-file edit is requested
- a browser/shell/connector capability is treated as automatically approved
- a second repository becomes part of active execution scope without explicit governance update

---

## 6. Relationship to Obsidian Markdown Structure

Hermes should treat the current markdown vault as the live navigational source of truth.

That means preserving:
- folder-level routing from `06_AGENTS/Vault-Map.md`
- index-note orientation such as `Build-Logs-Index.md`, `Knowledge-Index.md`, and `Documentation-History-Index.md`
- wikilink graph integrity
- stable markdown file paths that can later map to standalone nodes

Hermes should prefer adding explicit links and route metadata rather than relying on implicit memory alone.

---

## 6a. Agent-Activity Identity Binding

Hermes activity records should be discoverable as Hermes records in both filename slugs and graph links.

Required convention for future Hermes Agent-Activity records:
- filename slug begins with `YYYY-MM-DD-hermes-...`, or `YYYY-MM-DD-hermes-optimus-...` when the Optimus lane label is also useful
- frontmatter or visible metadata includes `runtime: hermes` and `runtime_node: [[Hermes-Runtime-Profile]]`
- graph links include `[[Hermes-Runtime-Profile]]`, `[[HERMES]]`, and `[[Agent-Activity-Index]]`
- `Optimus` may remain the human-facing lane/assistant label, but it must not be the only runtime identity in Agent-Activity naming or graph edges

This rule keeps Obsidian graph nodes aligned with the ChaseOS runtime-instance model and prevents Hermes activity from being stranded under persona-only labels.

## 6b. Live Coordination Daemon

When Hermes needs to participate in live Bus dispatches, the operator-controlled command is:

```powershell
chaseos runtime daemon --runtime hermes --daemon-interval N
```

The daemon runs Hermes's coordination-watch loop: publish heartbeat/state, inspect eligible Agent Bus tasks, claim safe Hermes-bound work, dispatch declared Hermes workflow handlers such as `hermes_watch`/review paths, and write result/audit state. It is not a permission grant for arbitrary shell, connector, protected-file, or canonical-promotion work.

---

## 7. Relationship to the Future Standalone

This runtime profile is written so it can survive the transition from:
- **Obsidian-first markdown navigation**, to
- **standalone ChaseOS graph/native navigation**

The stable bridge artifacts are:
- `06_AGENTS/Vault-Map.md`
- `06_AGENTS/Hermes-Runtime-Profile.md`
- `runtime/memory/nav/hermes/nav-map.json`

These should later map to:
- a shared system routing node
- a Hermes runtime identity/profile node
- a machine-readable runtime navigation record

---

## 8. Setup / Bootstrap Awareness

Hermes should now treat ChaseOS setup/bootstrap scaffolding as part of its runtime navigation awareness.

That means Hermes should know that a deployable ChaseOS instance is expected to include a broader mandatory core than only messaging/runtime coordination docs.

### Core scaffold awareness set
Hermes should expect setup/init to eventually scaffold or validate at least these categories:
- root architecture/foundation files such as `README.md`, `PROJECT_FOUNDATION.md`, `ROADMAP.md`, and `FORKING.md`
- identity and control files such as `SOUL.md`, `00_HOME/Now.md`, `00_HOME/Dashboard.md`, `00_HOME/Operating-System.md`, `00_HOME/Principles.md`, and `00_HOME/Assistant-Contract.md`
- governance/routing files such as `06_AGENTS/Vault-Map.md`, `06_AGENTS/Permission-Matrix.md`, `06_AGENTS/Agent-Registry.md`, `06_AGENTS/Tool-Map.md`, `06_AGENTS/Handoff-Protocol.md`, `06_AGENTS/Trust-Tiers.md`, and `06_AGENTS/Agent-Control-Plane.md`
- setup/runtime machine-readable files such as `runtime/setup_registry.json`, `runtime/setup_provider_profiles.json`, `runtime/setup_state.example.json`, `runtime/setup_state.schema.json`, `runtime/setup_state.json`, plus the `runtime/bindings/`, `runtime/lifecycle/`, `runtime/state/`, and `runtime/policy/` layers
- operator history/index surfaces such as `07_LOGS/Build-Logs/`, `07_LOGS/Agent-Activity/`, `07_LOGS/Operator-Briefs/`, `07_LOGS/Documentation-History/`, and their index notes
- runtime profile seeds for `openclaw`, `hermes`, and future runtime lanes

### Why this matters to Hermes
This matters because Hermes is a navigation-aware, documentation-capable runtime lane. If ChaseOS is deployed on a fresh machine, Hermes should be able to reason about whether the expected operator/governance scaffold exists before assuming richer runtime work is safe.

### Discord Binding and Studio Control Surface Awareness

Hermes currently participates through a bounded Discord runtime lane, so new installs must make the Discord lane explicit and inspectable instead of relying on undocumented channel IDs.

Current readiness surface:
- `.chaseos/discord_instance_bindings.yaml` is the local, Git-ignored binding file for server/runtime/channel IDs.
- `runtime/bindings/discord_instance_bindings.example.yaml` is the tracked setup template.
- `04_SOPS/Discord-Control-Plane-Setup-SOP.md` explains how to bind the local instance without putting webhook URLs or bot tokens in the YAML.
- `python -m runtime.cli.main setup discord validate --json` validates the binding file without exposing raw values.
- Studio Dashboard includes `discord_control_plane_panel`, a read-only visibility surface for Hermes/OpenClaw/future runtime control-plane readiness.

Hermes should use this panel as orientation and setup evidence only. Hermes free-response chat, thread creation, runtime-board routing, or schedule changes still require the normal ChaseOS proposal/approval/Agent Bus/AOR paths before any state changes.

## 9. Current Profile Verdict

Hermes is best used right now as a **navigation-aware, documentation-capable, bounded runtime lane**.

Its strongest current contribution is not broad execution authority; it is:
- clear routing
- bounded coordination
- documentation and structure work
- future-ready runtime memory scaffolding

### Summary-context application
For how Hermes preferred routes, trusted zones, risk zones, and escalation points should become typed human-facing summaries in future standalone surfaces, see:
- `06_AGENTS/Runtime-Navigation-Overlay-Summary-Context-Application.md`

---

*Graph links: [[CLAUDE]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[OPENCLAW]] · [[OpenClaw-Runtime-Profile]] · [[Archon-Runtime-Profile]] · [[Codex-Runtime-Profile]] · [[Hermes-Adapter-Spec]] · [[OpenClaw-Adapter-Spec]] · [[Runtime-Navigation-Map]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Runtime-Instance-Authority-Parity]] · [[ChaseOS-Discord-Control-Plane]] · [[Discord-Control-Plane-Setup-SOP]] · [[Vault-Map]] · [[Agent-Activity-Index]] · [[ChaseOS-Studio-Architecture]]*

*Hermes-Runtime-Profile.md — v0.2 | Created: 2026-04-24 | Updated: 2026-05-15 (Discord binding validator and Studio control-plane readiness added)*
