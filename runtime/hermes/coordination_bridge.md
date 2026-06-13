---
title: Hermes Coordination Bridge
type: hermes-runtime-control
scope: runtime-local — binds Hermes to the ChaseOS coordination bus without broadening Hermes authority
created: 2026-04-24
updated: 2026-04-24
---

# Hermes Coordination Bridge

> This file tells Hermes how to participate in the ChaseOS dual-runtime coordination bus.
> It does not supersede `HERMES.md`, adapter manifests, role cards, or the Discord control-plane rules.

---

## Read Order

1. `HERMES.md`
2. `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
3. `06_AGENTS/ChaseOS-Discord-Control-Plane.md`
4. `runtime/agent_bus/Agent-Bus-Folder-Guide.md`
5. `runtime/hermes/agents.md`

---

## Runtime Name

Use this exact machine identifier in coordination packets:
- `Hermes`

---

## Coordination Rule

Hermes should use:
- `runtime/agent_bus/` for machine-readable task routing and runtime state
- Discord for operator-facing summaries, approvals, and bounded visibility

Hermes should not try to conduct free-form machine coordination with OpenClaw purely through Discord chat.

---

## Expected Hermes Behavior

Hermes should:
1. classify operator intent
2. convert executable work into structured task packets
3. assign tasks to `OpenClaw` when appropriate
4. review returned results
5. emit concise Discord summaries for the operator

Current CLI bridge helpers:
- `chaseos agent-bus status`
- `chaseos agent-bus task list --recipient Hermes`
- `chaseos agent-bus task update TASK_ID --runtime Hermes --status ... --message ...`
- `chaseos agent-bus heartbeat --runtime Hermes --status idle|busy|blocked|offline`
- `chaseos agent-bus heartbeat --runtime Hermes --status busy --health ok --runtime-instance-id <lane-id> --heartbeat-scope instance --control-surface discord --control-surface-key <conversation-key>`
- `chaseos agent-bus watch --runtime Hermes --once|--interval N [--claim-next] [--runtime-instance-id <lane-id>] [--control-surface discord] [--control-surface-key <conversation-key>]`

Current watch/liveness direction inside ChaseOS:
- Hermes coordination-watch should be understood as a ChaseOS-owned watch posture for all current and future runtimes, not a Hermes-only special case
- watch surfaces may emit either runtime-scoped or instance-scoped heartbeats depending on whether active work is bound to a specific Discord/control-surface lane
- when Hermes is coordinating work from shared ops lanes, dedicated runtime chats, Discord threads, CLI sessions, or future control surfaces, the bus should preserve that lane identity instead of reducing everything to one undifferentiated `Hermes` heartbeat

In this bootstrap pass, manual/operator-directed packet creation and review are valid until full runtime-native watcher/service ownership is added.
The ChaseOS-owned loop surface already exists through:
- `chaseos agent-bus watch --runtime Hermes --once --runtime-instance-id <lane-id> --control-surface discord --control-surface-key <conversation-key>`
- `chaseos agent-bus watch --runtime Hermes --interval N [--claim-next] --runtime-instance-id <lane-id> --control-surface discord --control-surface-key <conversation-key>`

The next live lifecycle-owned layer now also exists through:
- `chaseos runtime coordination-watch-supervisor --runtime hermes --action plan --json`
- `chaseos runtime coordination-watch-supervisor --runtime hermes --action status --json`
- `chaseos runtime coordination-watch-supervisor --runtime hermes --action start`
- `chaseos runtime coordination-watch-supervisor --runtime hermes --action stop`

The next bootstrap-registration layer now also exists through:
- `chaseos runtime coordination-watch-bootstrap --runtime hermes --action plan --json`
- `chaseos runtime coordination-watch-bootstrap --runtime hermes --action status --json`
- `chaseos runtime coordination-watch-bootstrap --runtime hermes --action install`
- `chaseos runtime coordination-watch-bootstrap --runtime hermes --action apply --json`
- `chaseos runtime coordination-watch-bootstrap --runtime hermes --action verify --json`
- `chaseos runtime coordination-watch-bootstrap --runtime hermes --action handoff --json`
- `chaseos runtime coordination-watch-bootstrap --runtime hermes --action reboot-verify --json`
- `chaseos runtime coordination-watch-bootstrap --runtime hermes --action capture-success --json`
- `chaseos runtime coordination-watch-bootstrap --runtime hermes --action reconcile-reboot-result --json`
- `chaseos runtime coordination-watch-bootstrap --runtime hermes --action unregister`
- `chaseos runtime coordination-watch-bootstrap --runtime hermes --action remove`

This is a ChaseOS-owned background-loop plus registration-artifact/apply foothold, it includes a privilege-aware elevated handoff bundle for the Windows scheduler boundary when the current shell returns `Access is denied.`, status exposes the bootstrap event-log path plus latest event so audit-significant registration actions remain visible after cleanup, `reboot-verify` defines the post-registration evidence bundle plus a host-side result JSON path for later restart/logon checks, and both `capture-success` and the explicit `reconcile-reboot-result` action reconcile that reboot-result evidence into the durable success-state record while only emitting Agent Activity writeback if a real success posture is actually observed.

---

## Hard Boundary

The coordination bridge does not authorize Hermes to:
- gain shell access
- edit protected files
- expand beyond declared workflow scope
- treat Discord replies as machine-state truth without bus translation

---

*Authority doc: `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`*


*Graph links: [[OpenClaw-Runtime-Profile]] · [[Hermes-Runtime-Profile]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
