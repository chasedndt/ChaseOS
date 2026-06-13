# Chaser Gateway Architecture

Date: 2026-06-03 (N1 diagnostic built 2026-06-03; N7 internal ingress facade, N8 authority audit, N9 approved file-create, and N10 approved file-copy built 2026-06-06)
Runtime: Chaser Agent (claude-code); Codex for N7 internal facade
Status: PARTIAL - architecture + read-only diagnostic + internal structured ingress facade + terminal authority audit built; always-on/network gateway process and external ingress transports not built
Source books: `247 Agent Harness engineering V0.md`, `deep-research-report.md` (Hermes/OpenClaw reverse-engineering)
Related: [[ChaserAgent-Architecture]] · [[Terminal-Workbench-Architecture]] · [[ChaserAgent-Moat]] · [[board-py-Integration-Deep-Dive]] · [[Autonomous-Operator-Runtime]] · [[Runtime-InterAgent-Coordination-Bus]] · [[ChaseOS-Gate]] · [[Provider-Agnostic-Routing-Architecture]]

## 0. Purpose

You provided two reverse-engineering reports on **Hermes Agent** and **OpenClaw** — always-on agent runtimes. They describe a 14-layer anatomy (threat model → gateway → provider resolution → auth → prompt assembly → tools → sessions → scheduling → routing → sandboxing → secrets → plugins → observability → build-your-own). You also provided two architecture diagrams of a **Chaser Gateway** + **Chaser Runtime**.

This document does three things:

1. Explains what a "**Hermes Gateway diagnostic**" actually is (you said you were unsure).
2. Maps the diagram + the 14-layer anatomy onto **what ChaseOS already has** vs. what is missing.
3. Defines the **Chaser Gateway** and a **Chaser Gateway Diagnostic** as ChaseOS-native concepts — without copying Hermes' authority model and without bypassing the ChaseOS Gate.

This is the layer-by-layer deep-dive substrate. Each layer below becomes its own future build pass.

## 1. What the "Hermes Gateway diagnostic" is

In Hermes/OpenClaw, the **gateway** is a single always-on background process that:

- connects to external surfaces (Discord/Telegram/email/webhooks),
- authenticates the caller and resolves a session,
- runs cron/heartbeat work,
- routes requests into the model+tools runtime,
- delivers outputs back.

A **gateway diagnostic** is the operator health-check ladder for that process. In the books it is things like `hermes gateway status`, `openclaw doctor`, `openclaw gateway status --json`, `openclaw security audit`, `models status --probe`. Concretely it answers:

- Is the host/OS layer up (on Windows: is WSL2 running, is the Ubuntu distro started, does the Linux user exist)?
- Does the runtime binary resolve and report a version?
- Is the gateway loopback URL reachable?
- What is the last failure reason, and what is the next safe operator action?

So "Hermes Gateway diagnostic" = **a deterministic readiness probe + repair-plan generator for the always-on agent process**, run *before* trusting it to do unattended work. It does not auto-start or auto-repair by default; it reports state and emits a *plan*.

ChaseOS already has fragments of this idea: `runtime/studio/runtime_cockpit.py` (`_runtime_health`, `_bus_heartbeat_state`), `chaseos runtime daemon`, the Agent Bus heartbeat table, and `chaseos agent-bus mode/heartbeats`. The Chaser Gateway Diagnostic (Section 6) consolidates those into one ChaseOS-native readiness surface.

## 2. The two diagrams, mapped to ChaseOS

### Diagram 1 — Chaser Gateway (ingress/control plane)

```
Internet/External → Chaser Gateway[ AuthN → AuthZ → Session Router → Rate Limits ]
```

| Diagram node | ChaseOS owner (existing or planned) | Status |
|---|---|---|
| AuthN ("who are you?") | `runtime/chaser/gateway.py` local-operator request auth for internal ingress; Agent Bus ingress + runtime identity ledger; Discord control-plane binding (`chaseos setup discord`) | partial |
| AuthZ ("what can you do?") | [[ChaseOS-Gate]] + [[Permission-Matrix]] + [[Trust-Tiers]] + role cards | existing |
| Session Router | `runtime/chaser/gateway.py` intent router + `runtime/chaser/sessions.py` (read store today) + Agent Bus task routing (`route_task_type`) | partial |
| Rate Limits | `runtime/chaser/gateway.py` bounded request payload size; `max_concurrent_tasks` / `priority_ceiling` in the bus router | partial |

### Diagram 2 — Chaser Runtime (model + tools + boundaries)

```
Prompt Builder → LLM → Policy Engine → Capabilities[ Terminal, Filesystem, Browser, Database, SaaS, Trading ]
   → Hard Boundaries[ Sandbox/Container, Secret Vault, Approval Service ] → Trace Recorder → Audit Store
```

| Diagram node | ChaseOS owner | Status |
|---|---|---|
| Prompt Builder | AOR `engine.py` required-reads + boot frame (`runtime/context/boot.py`) + Agent-Memory layering | partial |
| LLM | **Runtime-owned** (Hermes/OpenClaw/Chaser Agent resolve their own provider per [[Provider-Agnostic-Routing-Architecture]]) — Chaser core never calls providers directly | existing rule |
| Policy Engine | ChaseOS Gate hooks + AOR permission ceiling stage | existing |
| Capabilities → Terminal | **`TerminalAdapter` + `chaseos operate terminal` (built 2026-06-03)** | partial |
| Capabilities → Filesystem | `filesystem_adapter.py` (operator surface) | partial |
| Capabilities → Browser | `browser/` operator surface (parked but live) | partial |
| Capabilities → Database/SaaS/Trading | not built | planned |
| Hard Boundary → Sandbox/Container | terminal policy `host_mutation: blocked`; Docker backend not built | planned |
| Hard Boundary → Secret Vault | provider model_config + env-var-only secrets; SecretRef-style migration not built | planned |
| Hard Boundary → Approval Service | `runtime/studio/service.py` approval queue + AOR OSRIL approvals | existing |
| Trace Recorder | `terminal_runs.py`, Agent-Activity audit, OperatorRunAudit | partial |
| Audit Store | `07_LOGS/` (Agent-Activity, Terminal-Runs, Decision-Ledger) | existing |

**Conclusion:** ChaseOS already owns the *hard* half of both diagrams (AuthZ, Policy Engine, Approval Service, Audit Store) because that is the governance moat. The internal ingress facade now exists for governed local routes, but the always-on gateway process, external transports, and broader capability breadth (database/SaaS/trading, sandbox container) remain thin/planned.

## 3. The 14-layer anatomy mapped to ChaseOS

Per the books (chapters A–N). For each: ChaseOS owner + status. This table is the deep-dive backlog — each row is a future pass.

| # | Book layer | ChaseOS owner | Status |
|---|---|---|---|
| A | Threat model / runtime invariants | Trust-Tiers, Permission-Matrix, Agent-Security-Model | existing |
| B | Gateway boot / supervision / lifetime | `runtime/lifecycle/`, `chaseos runtime daemon`, coordination-watch supervisor | partial |
| C | Provider runtime resolution / model routing | per-runtime `model_config.yaml`; Provider-Agnostic-Routing-Architecture | existing (rule) |
| D | OAuth / auth profiles / credentials | env-var + model_config; OAuth profiles + refresh not built | planned |
| E | Prompt assembly / identity layering | AOR required-reads + boot frame + Agent-Memory-Architecture + SOUL/Principles | partial |
| F | Tool registry / dispatch / policy | operator_surface adapters + adapter_registry + Gate; no unified toolset manager | partial |
| G | Sessions / persistence / memory | `runtime/chaser/sessions.py` (read) + runtime memory adapters + dedup registry | partial |
| H | Scheduling / heartbeat / automation | `runtime/schedules/`, SBP, AOR, OpenClaw cron | existing |
| I | Messaging adapters / control-plane routing | Agent Bus + Discord ingress + bus router | partial |
| J | Sandboxing / exec approvals / isolation | terminal policy classes + approval service; container sandbox not built | partial |
| K | Secrets / SecretRefs / crypto boundaries | env-var-only + security audits; SecretRef migration not built | planned |
| L | Plugins / MCP / extension supply chain | `runtime/mcp/` stdio scaffold + Hermes skill review | partial |
| M | Observability / audits / operator runbooks | runtime cockpit, Studio dashboard, audit logs, `chaseos health` | existing |
| N | Build-your-own runtime | **this is ChaserAgent core (`runtime/chaser/`)** | foothold |

## 4. The Chaser Gateway — ChaseOS-native definition

The Chaser Gateway is **the ingress + control-plane façade over ChaserAgent core and the Agent Bus**. It is the "one core, many surfaces" pattern from the books, expressed under ChaseOS governance.

Key rules (the moat — see [[ChaserAgent-Moat]]):

1. The Chaser Gateway is **not** a second brain and **not** a second source of truth. It is a router/authorizer in front of the ChaseOS Gate, never around it.
2. Every inbound request becomes a **typed, authorized, audited** session before it can touch a capability.
3. The gateway **never** calls model providers directly. It dispatches to a runtime (Hermes/OpenClaw/Chaser Agent) over the Agent Bus, and that runtime owns its provider/credentials ([[Provider-Agnostic-Routing-Architecture]]).
4. Session identifiers are **routing selectors, not auth tokens** (the OpenClaw lesson — the single most common mistake the books call out).
5. Capabilities are reached only through governed adapters (TerminalAdapter, browser surface, filesystem adapter), never raw shell/FS.

Current home (mirrors `runtime/chaser/` from ChaserAgent-Architecture):

```text
runtime/chaser/
  gateway.py     # internal ingress facade: authN -> authZ -> intent route -> bounded payload  (BUILT PARTIAL)
  board.py       # orchestration board over bus/AOR/terminal/approvals          (BUILT PARTIAL - see deep-dive)
  sessions.py    # session store (BUILT — read-only)
  exports.py     # session export (BUILT — md/json)
  models.py      # session/tool/terminal/artifact models (BUILT)
```

The Chaser Gateway does not replace the Agent Bus; it is the **authorizing front door** that decides *whether* and *as whom* a request enters the bus. The bus remains the inter-runtime transport.

2026-06-06 implementation note: N7 built the internal structured facade, not an always-on network gateway. `handle_gateway_ingress()` currently routes `board.state`, `terminal.propose`, `terminal.approval_request_preview`, `terminal.approval_request_write`, `terminal.executor_readiness`, and `terminal.execute_approval`. It requires local-operator confirmation for every route; approval queue writes require an additional confirmation; terminal execution requires approved-terminal-write confirmation and delegates to the existing N6 executor. It writes no Agent Bus tasks, calls no providers, mutates no canonical truth, and exposes no Studio execution route.

2026-06-06 authority audit note: N8 added `runtime/chaser/terminal_authority_audit.py`, CLI `chaseos chaser terminal authority-audit --json`, and Studio API `get_chaser_terminal_authority_audit()`. This audit checks the terminal/gateway authority posture through preview and blocked paths only, snapshots side-effect-sensitive storage before/after, and performs no execution, approval write/consumption, marker/audit write, Agent Bus write, provider call, canonical writeback, external upload, or host mutation.

2026-06-06 approved file-operation note: N9 and N10 expanded the N6 executor that N7 delegates to from `mkdir <target>` only to `mkdir <target>`, `touch <target>`, `copy <source> <target>`, and `cp <source> <target>`. The gateway contract did not gain new ambient authority: `terminal.execute_approval` still requires local-operator and approved-terminal-write confirmation and delegates to exact N6 approval/proposal/scope/marker checks. Copy requires an existing in-vault source file, existing target parent, and absent in-vault target; it does not create parents, overwrite files, read source content into output, invoke shell operators, write Agent Bus tasks, call providers, or mutate canonical truth.

## 5. Why ChaseOS does not just clone Hermes Gateway

The books are explicit: Hermes is the cleaner model for **runtime composition**; OpenClaw is the cleaner model for **operator-grade hardening**. ChaseOS already has the hardening (Gate, Trust-Tiers, Permission-Matrix, approval service, audit store) — that is its existing advantage. So the Chaser Gateway copies the **shape** (one core, many surfaces; shared sessions; provider resolver per runtime; prompt layering; tool loop; SQLite-style state) but inherits authority from ChaseOS, not from a gateway role/scope handshake. Hermes/OpenClaw are *reference patterns under ChaseOS Gate*, never authority peers.

## 6. The Chaser Gateway Diagnostic (ChaseOS analog of `hermes gateway status` / `openclaw doctor`)

This is the ChaseOS-native answer to "we will need a chaser agent gateway diagnostic." It is a **read-only readiness probe + repair-plan generator**, never an auto-starter.

> **Status: BUILT (2026-06-03).** `runtime/chaser/gateway_diagnostic.py` (`run_gateway_diagnostic`), CLI `chaseos chaser gateway diagnose [--runtime ID] [--json]`, and `StudioAPI.get_chaser_gateway_diagnostic`. Read-only, fail-open per check, does **not** materialize the bus DB (reports "not initialized" instead of creating it), and emits a `next_actions` repair plan for operator review. States: `running` / `degraded` / `failed`. 6 tests. The diagnostic writes nothing to the vault.

States (from the books' diagnostic ladder): `not_configured`, `configured`, `starting`, `running`, `degraded`, `failed`, `proven_after_reboot`.

Checks (each maps to an existing ChaseOS signal — no new host authority):

| Check | Existing ChaseOS source |
|---|---|
| Vault root + boot context loads | `runtime/context/boot.py` `load_boot_context()` |
| Runtime adapters registered | `chaseos agent list`, runtime memory adapters |
| Agent Bus mode + backend healthy | `get_bus_mode()`, backend_loader |
| Per-runtime heartbeat freshness | `list_heartbeats()`, `_bus_heartbeat_state()` (fresh/recent/stale) |
| Daemon/lifecycle state | `runtime/lifecycle/`, coordination-watch supervisor |
| Schedule intents valid | `runtime/schedules/loader.py` `validate_all_schedules()` |
| Pending approvals backlog | `runtime/studio/service.py` approval queue |
| Terminal surface policy intact | `TerminalAdapter` policy + `terminal_runs` audit dir |
| Last failure + next safe action | derived; emits a **plan artifact**, does not execute |

**Governance:** the diagnostic must never silently add startup items / cron jobs / services / scheduled tasks. Any host startup change goes through the existing runtime-gateway-controls approval path. On a degraded result it emits a *start-plan / repair-checklist artifact* for operator review — exactly the books' "generate plans before executing starts/restarts" rule.

## 7. Build order (each is a future pass)

1. ~~**Chaser Gateway Diagnostic** (read-only)~~ — ✅ **BUILT 2026-06-03** (`runtime/chaser/gateway_diagnostic.py`).
2. **Session write lifecycle** (pin/rename/archive) over `runtime/chaser/sessions.py`.
3. **`runtime/chaser/board.py`** orchestration board (see [[board-py-Integration-Deep-Dive]]).
4. ~~**`runtime/chaser/gateway.py`** ingress facade (authN->authZ->session route->rate limit)~~ - BUILT PARTIAL 2026-06-06 as an internal structured facade over existing governed routes. Network serving, external transports, Agent Bus task mutation, provider/runtime dispatch, and ChaserAgent live activation remain future gated work.
5. **Capability breadth**: database/SaaS/trading adapters, container sandbox — each under Gate + approval.
6. **Auth/SecretRef hardening** (layers D + K) — OAuth profiles, SecretRef migration, `secrets audit --check` analog.

Do not skip ahead to a live gateway process before the diagnostic, board contracts, N6 approval/executor path, and N7 internal facade are reviewed and test-covered. That is the books' core warning and the ChaseOS governance rule.
