---
title: OpenClaw Coordination Bridge
type: openclaw-runtime-control
scope: runtime-local — binds OpenClaw to the ChaseOS coordination bus without expanding authority
created: 2026-04-24
updated: 2026-04-24
---

# OpenClaw Coordination Bridge

> This file tells OpenClaw how to participate in the ChaseOS dual-runtime coordination bus.
> It does not grant new permissions. OpenClaw remains bounded by `OPENCLAW.md`, `06_AGENTS/OpenClaw-Adapter-Spec.md`, AOR manifests, and role cards.

---

## Read Order

1. `OPENCLAW.md`
2. `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
3. `runtime/agent_bus/Agent-Bus-Folder-Guide.md`
4. `runtime/openclaw/agents.md`
5. `runtime/openclaw/tools.md`

---

## Runtime Name

Use this exact machine identifier in coordination packets:
- `OpenClaw`

---

## Coordination Rule

OpenClaw should not use Discord free-chat as its primary machine-to-machine protocol with Hermes.
It should read and write structured coordination state under:
- `runtime/agent_bus/`

Discord remains visibility and operator interaction, not machine-state authority.

---

## Allowed Coordination Actions

OpenClaw may, within its already-declared bounds and in this pass primarily through operator-directed/manual coordination use:
- claim a task packet addressed to `OpenClaw`
- update task state while it is the owner
- post result packets
- post blocker packets
- emit heartbeats

OpenClaw may not treat the coordination bus as permission to:
- edit protected files
- expand workflow scope
- bypass AOR writeback
- self-authorize new connectors or schedules

---

## Expected Behavior

For each assigned task:
1. Validate task against current OpenClaw authority.
2. If valid, claim it and move to `in_progress`.
3. Produce artifacts through normal governed paths.
4. Return `RESULT` or `BLOCKER` packet.
5. Mirror only concise summaries to Discord when needed.

Current CLI bridge helpers:
- `chaseos agent-bus task list --recipient OpenClaw`
- `chaseos agent-bus task claim TASK_ID --runtime OpenClaw`
- `chaseos agent-bus task update TASK_ID --runtime OpenClaw --status ... --message ...`
- `chaseos agent-bus heartbeat --runtime OpenClaw --status busy --health ok --runtime-instance-id <lane-id> --heartbeat-scope instance --control-surface discord --control-surface-key <conversation-key>`
- `chaseos agent-bus watch --runtime OpenClaw --once|--interval N [--claim-next] [--runtime-instance-id <lane-id>] [--control-surface discord] [--control-surface-key <conversation-key>]`

Current watch/liveness direction inside ChaseOS:
- watch surfaces may emit either runtime-scoped or instance-scoped heartbeats
- when claimed work is tied to a Discord/control-surface lane, ChaseOS should preserve that lane identity in heartbeat state rather than collapsing it to only `OpenClaw`
- this is required so one runtime can participate safely across shared ops lanes, dedicated runtime chats, Discord threads, CLI sessions, and future control surfaces
- the same model should generalize to future runtimes, not just Hermes/OpenClaw

Automatic runtime-native watcher/service ownership is not assumed by this bootstrap doc yet, but the ChaseOS-owned loop surface now exists through:
- `chaseos agent-bus watch --runtime OpenClaw --once --runtime-instance-id <lane-id> --control-surface discord --control-surface-key <conversation-key>`
- `chaseos agent-bus watch --runtime OpenClaw --interval N [--claim-next] --runtime-instance-id <lane-id> --control-surface discord --control-surface-key <conversation-key>`

The next live lifecycle-owned layer now also exists through:
- `chaseos runtime coordination-watch-supervisor --runtime openclaw --action plan --json`
- `chaseos runtime coordination-watch-supervisor --runtime openclaw --action status --json`
- `chaseos runtime coordination-watch-supervisor --runtime openclaw --action start`
- `chaseos runtime coordination-watch-supervisor --runtime openclaw --action stop`

The next bootstrap-registration layer now also exists through:
- `chaseos runtime coordination-watch-bootstrap --runtime openclaw --action plan --json`
- `chaseos runtime coordination-watch-bootstrap --runtime openclaw --action status --json`
- `chaseos runtime coordination-watch-bootstrap --runtime openclaw --action install`
- `chaseos runtime coordination-watch-bootstrap --runtime openclaw --action apply --json`
- `chaseos runtime coordination-watch-bootstrap --runtime openclaw --action verify --json`
- `chaseos runtime coordination-watch-bootstrap --runtime openclaw --action handoff --json`
- `chaseos runtime coordination-watch-bootstrap --runtime openclaw --action reboot-verify --json`
- `chaseos runtime coordination-watch-bootstrap --runtime openclaw --action capture-success --json`
- `chaseos runtime coordination-watch-bootstrap --runtime openclaw --action reconcile-reboot-result --json`
- `chaseos runtime coordination-watch-bootstrap --runtime openclaw --action unregister`
- `chaseos runtime coordination-watch-bootstrap --runtime openclaw --action remove`

This is a ChaseOS-owned background-loop plus registration-artifact/apply foothold, it includes a privilege-aware elevated handoff bundle for the Windows scheduler boundary when the current shell returns `Access is denied.`, status exposes the bootstrap event-log path plus latest event so audit-significant registration actions remain visible after cleanup, `reboot-verify` defines the post-registration evidence bundle plus a host-side result JSON path for later restart/logon checks, and both `capture-success` and the explicit `reconcile-reboot-result` action reconcile that reboot-result evidence into the durable success-state record while only emitting Agent Activity writeback if a real success posture is actually observed.

---

*Authority doc: `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`*


*Graph links: [[OpenClaw-Runtime-Profile]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
