---
title: ChaseOS Discord Control Plane
type: architecture
status: ACTIVE — dual-runtime Discord control-plane; OpenClaw live, Hermes bounded active Discord lane
version: 1.4
created: 2026-04-20
updated: 2026-05-16
scope: Dual-runtime Discord control-plane — OpenClaw live, Hermes bounded active Discord lane
---

# ChaseOS Discord Control Plane

> Discord is a shared operator/control transport surface for ChaseOS runtimes.
> It is not a runtime, not a source of canonical truth, not a permission authority, and not a shortcut around AOR, Gate, role cards, workflow manifests, or human approval.

---

## Current Local Truth

- ChaseOS remains the constitutional control plane and canonical truth source.
- OpenClaw is the active bounded runtime adapter lane on this machine.
- OpenClaw Discord transport/control surface is already operational.
- `operator_today` and `operator_close_day` are live bounded AOR workflows through the real AOR path.
- Hermes is an active bounded Discord runtime lane: one Discord-eligible workflow, `hermes_operator_today_shadow`, advisory and shadow read-only outputs only. Hermes also has bounded bus workflows outside Discord (`hermes_review_execute`, `hermes_watch`).
- Interactive routing and output posting are separate rights. `hermes-chat` is Hermes free-response chat lane, `openclaw-chat` is OpenClaw free-response chat lane, `chaseos-ops` is shared but mention-required, and `change-log` is output-only.
- Hermes ↔ OpenClaw machine coordination is now bootstrapped through `runtime/agent_bus/`; Discord remains the human-facing visibility/control surface rather than the machine-state source of truth.
- Hermes has no shell authority, no connector authority, no canonical promotion authority, and no broader workflow authority beyond its declared bounded scope.
- MCP is a separate lane and is not part of this Discord control-plane spec.
- Home Assistant is not part of this spec.
- Machine-local Discord server/runtime/channel bindings live in `.chaseos/discord_instance_bindings.yaml`, which must stay Git-ignored. The tracked template lives at `runtime/bindings/discord_instance_bindings.example.yaml`; setup instructions live at `04_SOPS/Discord-Control-Plane-Setup-SOP.md`.
- `python -m runtime.cli.main setup discord validate --json` now validates the binding file without exposing IDs, webhook URLs, bot tokens, public keys, or secret values.
- ChaseOS Studio Dashboard now exposes a read-only `discord_control_plane_panel` that shows valid/blocked status, active runtime labels, bound channel counts, Git-ignore status, and the next Studio runtime-control capability map. It performs no Discord API calls, webhook calls, Agent Bus writes, schedule mutation, or canonical mutation.

---

## Local Binding and Studio Status Surface

The local Discord binding file is the machine/user attachment layer for the current ChaseOS install. It binds this installation's Discord server, operator identity, runtime bot/application identities, and channel classes to the canonical control-plane model above.

Rules:
- `.chaseos/discord_instance_bindings.yaml` is local runtime configuration, not public repository content.
- Runtime/provider secrets such as bot tokens or webhook URLs belong in the Git-ignored `.env`, never in the Discord binding YAML.
- The binding YAML may contain IDs and public key material needed for local routing validation; validators and Studio must return only presence/status fields, never raw values.
- Future runtimes that use Discord, chat, boards, or schedule lanes should follow the same pattern: tracked example template, ignored local binding, no-secret validation command, Studio visibility, and approval-gated write paths.

Current implementation status:

| Surface | Status | Authority |
|---|---|---|
| `runtime/discord_bindings.py` | IMPLEMENTED | Read-only validation; no secret or ID disclosure |
| `setup discord validate` | IMPLEMENTED | CLI wrapper for no-secret validation |
| Studio `discord_control_plane_panel` | IMPLEMENTED | Read-only dashboard/status surface |
| Studio native Chat workspace/thread foundation | IMPLEMENTED / PARTIAL | Read-only ChaseOS Chat product model that consumes redacted Discord posture without calling Discord |
| Studio workspace/folder/thread proposal writer | IMPLEMENTED / PARTIAL | Digest-bound approval artifact writer for native Chat workspace/folder/thread requests; proposal-record execution is handled by the consumer, while real Chat/Discord target state remains future |
| Studio workspace/folder/thread proposal consumer | IMPLEMENTED / PARTIAL | Exact-once consumer for approved proposal artifacts; writes native proposal JSON only, no Chat/Discord/runtime side effects |
| Studio workspace/folder/thread target-state executor | IMPLEMENTED / PARTIAL | Exact-once executor for approved proposal records; writes native Studio Chat state only, no Discord/API/runtime side effects |
| Studio route-state and draft surface | IMPLEMENTED / PARTIAL | Persists local Studio Chat route selection plus unsent message draft/intent JSON only; no message send, Discord/API/runtime side effects |
| Studio quick-open chat actions | IMPLEMENTED / LOCAL ROUTE STATE ONLY | Workspace/thread route previews, digest-bound proposal packets, and local route-state persistence are rendered; live opening/transport execution remains future |
| Studio thread creation | PARTIAL / NATIVE STATE ONLY | Pending approval artifacts can now be queued, consumed into proposal JSON, and applied to native Studio Chat state; Discord thread creation remains future |
| Studio send-to-runtime-board | IMPLEMENTED / PARTIAL | Digest-bound approval request packet for a future runtime board item; generic approval execution blocks, and actual board/Agent Bus/runtime effects remain future |
| Studio cron/schedule task management | IMPLEMENTED / PARTIAL | Digest-bound approval request packet, exact-once staged proposal consumer, exact-once approved schedule-intent writer for disabled `runtime/schedules/*.yaml` plus regenerated index, digest-bound activation-readiness approval packet, exact-once approved activation executor for schedule enablement plus index regeneration, digest-bound adapter export-readiness approval packet, and exact-once approved local adapter export packet writer; generic approval execution blocks, while external scheduler, OpenClaw/Hermes cron, Discord, Agent Bus, and runtime dispatch effects remain future |
| Studio schedule manual test controls | IMPLEMENTED / LOCAL UI CONTROLS + READBACK | Native Chat buttons, fields, status, and readback for the full local schedule chain; calls existing governed Studio APIs only, with no Discord API, external scheduler, cron, Agent Bus, runtime dispatch, provider, credential, or broad canonical effects |
| Studio authority-tier Chat controls | IMPLEMENTED / NAVIGATION + READINESS ONLY | Groups provider calls, credential readiness, runtime dispatch, Agent Bus tasks, Discord actions, and external cron apply into one Chat block; buttons navigate to existing governed surfaces only, with direct execution, Discord calls, Agent Bus writes, runtime dispatch, provider calls, credential reads, cron mutation, and canonical mutation blocked |

This is the first concrete Studio-side bridge toward replacing Discord as the only practical operator surface. Discord remains the current transport; Studio now has redacted readiness state, a native Chat workspace/thread foundation, a digest-bound proposal writer, a governed exact-once proposal consumer, a governed native target-state executor, a local route-state/message-draft surface, a digest-bound runtime-board handoff approval request surface, a digest-bound schedule proposal packet surface, a governed schedule proposal consumer, a governed approved schedule-intent writer, a schedule activation-readiness packet surface, a governed approved schedule-activation executor, a schedule adapter export-readiness approval surface, a governed approved local adapter export packet writer, manual Chat UI controls/readback, and a unified authority-tier control block where provider, credential, runtime dispatch, Agent Bus, Discord, and external cron lanes can be inspected safely. The proposal writer queues pending Studio approval artifacts only after exact digest match; the proposal consumer can write the approved proposal JSON record only; the target-state executor can write local native Studio Chat workspace/folder/thread state only after exact digest plus operator target-state statement; the route/draft surface writes only local UI route selection and unsent draft intent state; the runtime-board handoff surface queues only a pending approval artifact for a future board item; the schedule proposal surface queues only a pending approval artifact for future schedule intent YAML; the schedule proposal consumer writes only a staged approved schedule proposal under `runtime/studio/chat/schedule-proposals/`; the approved schedule-intent writer writes only the declared disabled `runtime/schedules/*.yaml` file and regenerates `runtime/schedules/index.yaml`; activation readiness queues only a pending activation approval packet and ambient execution is blocked; the approved activation executor enables one approved ChaseOS schedule and regenerates the schedule index only; adapter export readiness queues only a pending approval packet; the approved adapter export packet writer writes only one local JSON packet under `runtime/studio/chat/schedule-adapter-exports/`; the manual UI controls call those existing governed methods and read back local state; the authority-tier controls only navigate to existing governed surfaces. They still perform no Discord API call, Discord thread creation, webhook post, message send, transcript/conversation log write, Agent Bus task write, runtime board mutation, external scheduler mutation, OpenClaw/Hermes cron mutation, runtime/workflow dispatch, provider call, credential display, or broader canonical mutation.

## Purpose

The Discord control plane defines how Discord may be used as an operator-facing transport surface for routing, status, approvals, alerts, and audit visibility across ChaseOS runtime adapters.

It exists to prevent three forms of drift:

1. Treating a Discord message as a trusted instruction.
2. Letting an adapter's Discord integration expand that adapter's authority.
3. Mixing runtime chat, approvals, audit, debug output, and external publication in the same channel.

Discord may carry requests and outputs. ChaseOS decides what those requests mean, which adapter may handle them, whether approval is required, and where any resulting output is written.

When dual-runtime coordination is needed, Discord-origin requests should be translated into structured coordination tasks under `runtime/agent_bus/` before Hermes and OpenClaw continue machine-to-machine work.

Default ChaseOS rule going forward:
- coordination-sensitive machine work must be represented as structured bus state using the real ingress/work-item context
- that context includes runtime plus channel/lane/thread/topic or equivalent future ingress identity
- runtime-only arbitration is insufficient when one runtime participates through multiple operator-facing lanes
- future runtimes should inherit this same rule by default rather than requiring a Hermes-specific exception

More general rule:
- Discord is one ingress transport only
- future control panels or communication infrastructures should follow the same translation rule
- actionable control-surface input must route into structured ChaseOS state before continuing as runtime work

---

## Non-Goals

This spec does not:

- implement a Discord bot,
- create new AOR workflows,
- create new Hermes workflows,
- enable Hermes shell access,
- enable Hermes connectors,
- implement MCP,
- add Home Assistant integration,
- add external network or connector behavior,
- alter the AOR execution engine.

---

## Channel Model

Discord channels must be separated by function. A message in one channel does not inherit authority from another channel.

| Channel Class | Purpose | Allowed Content | Execution Authority | Writeback / Audit Rule |
|---|---|---|---|---|
| `control-plane-routing` | Intake operator intents and route them to the correct review path | Structured requests, workflow run intents, status asks, routing questions | None directly. Routes to ChaseOS review or an approved adapter path. | Routing decisions must be logged when they lead to execution. |
| `runtime-chat` | Human/runtime conversation and low-stakes clarification | Discussion, summaries, questions, draft reasoning | Advisory only. No direct vault write or runtime execution. | Useful outcomes must be captured by a governed harness or AOR workflow before becoming ChaseOS state. |
| `approvals` | Explicit operator approval or denial for a proposed action | Approval cards, deny/approve responses, scoped confirmations | Approval can unlock only the named action, target, adapter, and run. | Approval record must be copied into audit before execution resumes. |
| `audit-writeback` | Post-run visibility and links to written artifacts | Run summaries, audit links, writeback paths, failure records | None. Output only. | Append-only; no command parsing from this channel. |
| `alerts` | Notify operator of failures, stale schedules, blocked requests, or security issues | Failures, scope violations, prompt-injection warnings, schedule health | None. Alerts may link to approval or debug channels. | Alert source and run ID must be recorded when available. |
| `debug` | Bounded diagnostic discussion for runtime operators | Stack traces, config status, dry-run output, sanitized errors | No production execution. Debug commands require separate approval if they touch runtime state. | Never post secrets, tokens, full env dumps, or protected-file contents. |
| `docs-archive` | Publish links to canonical docs, build logs, archive notes, and runbooks | Links, short summaries, index updates | None. Documentation visibility only. | Canonical docs live in the vault, not in Discord. |

Recommended channel names are implementation details. The class names above are canonical; actual server channels may be prefixed or renamed if the class is preserved in config.

---

## Message Trust Model

Discord input is not trusted by default.

| Source | Default Trust | Rule |
|---|---:|---|
| Owner/operator typed message | Tier 1 identity may be recognized, but the message still requires routing and scope checks | Operator intent is not execution authority until mapped to a declared workflow/action. |
| Runtime-generated message | Tier 2 or lower depending on adapter | Runtime output is report data, not permission to continue. |
| External user message | Tier 4 | Treat as untrusted input; never execute as instruction. |
| Webhook/bot/system message | Tier 4 unless explicitly registered | Data only; must be classified before use. |
| Copied external content | Tier 4 | May be summarized or captured; never obey embedded instructions. |

Emoji reactions are not approvals. They may acknowledge receipt only. Approval requires an explicit approval record with action, target, adapter, workflow, and run scope.

---

## Routing Model

### Routes to OpenClaw

OpenClaw is the active bounded runtime adapter lane on this machine. Discord-origin requests may route to OpenClaw only when all of the following are true:

1. The request maps to an existing active AOR workflow.
2. The workflow manifest and role card permit the requested action.
3. The request does not require a protected-file edit, canonical promotion, secret access, new connector, shell expansion, multi-repo expansion, or new workflow.
4. Approval is present when the action is not already part of a configured schedule.
5. The run writes through normal AOR writeback and audit paths.

Currently eligible OpenClaw-routed examples:

| Request Type | Route | Approval |
|---|---|---|
| Run `operator_today` | OpenClaw -> `chaseos run operator_today` -> AOR | Approval required for ad hoc Discord-triggered run; scheduled runs use configured schedule approval. |
| Run `operator_close_day` | OpenClaw -> `chaseos run operator_close_day` -> AOR | Approval required for ad hoc Discord-triggered run; scheduled runs use configured schedule approval. |
| Request schedule status | OpenClaw or local harness read-only status path | Advisory/status only if read-only; no approval unless it changes state. |
| Request graph hygiene proposal run | OpenClaw -> `chaseos run graph_hygiene` -> AOR | Approval required; output remains proposal-only. |

### Routes to Hermes

Hermes is an active bounded Discord runtime lane. Discord-origin requests may route to Hermes only when all of the following are true:

1. The request maps to `hermes_operator_today_shadow` (the only currently Discord-eligible Hermes workflow).
2. The Hermes role card and workflow manifest permit the requested action.
3. The request does not require shell execution, connector access, canonical promotion, protected-file writes, or authority beyond the declared bounded scope.
4. Approval is present (the workflow is not scheduled; all Hermes Discord runs are ad hoc and require explicit approval).
5. The run writes only to declared advisory output paths; no canonical vault state changes.

Currently eligible Hermes-routed actions:

| Request Type | Route | Approval |
|---|---|---|
| Run `hermes_operator_today_shadow` | Hermes bounded Discord lane → shadow read-only AOR path | Approval required |
| Advisory discussion, status, draft artifact review | hermes-chat or runtime-chat | Advisory only; no approval |

Hermes interactive lanes: `hermes-chat` (free-response), `chaseos-ops` (mention-required), `approvals` (approval records only).

Hermes output-only lanes: `alerts-hermes`, `debug-hermes`, `alerts-workflows`, `alerts-security`, `debug-adapters`, `runtime-debug`, `audit-writeback`, `artifact-paths`, `operator-runs`, `change-log`, `server-notes`, `docs-snippets`.

OpenClaw interactive lanes: `openclaw-chat` (free-response), `chaseos-ops` (mention-required), `approvals` (approval records only).

OpenClaw output-only lanes: `alerts-openclaw`, `debug-openclaw`, `alerts-workflows`, `alerts-security`, `debug-adapters`, `runtime-debug`, `audit-writeback`, `artifact-paths`, `operator-runs`, `change-log`, `server-notes`, `docs-snippets`.

The following still require ChaseOS control-plane review before any Hermes action:
- any new Hermes workflow request,
- any Hermes shell, connector, or broader authority expansion,
- any protected-file edit or canonical promotion.

### Must Stay in ChaseOS Control-Plane Review First

The following do not route to OpenClaw or Hermes directly:

- new workflow creation,
- any Hermes gateway, connector, shell, browser, memory, or broader workflow expansion,
- MCP-related requests,
- Home Assistant requests,
- protected-file edits,
- canonical promotion to `02_KNOWLEDGE/`,
- writes to `01_PROJECTS/`, `02_KNOWLEDGE/`, `06_AGENTS/`, or root governance files,
- credential or secret requests,
- multi-repo access,
- external publication beyond configured delivery,
- command text from an unknown or external Discord user,
- any ambiguous request.

Ambiguity defaults to stop, ask, and log.

---

## Permission Model for Discord-Sourced Actions

| Permission Class | Meaning | Examples | Handling |
|---|---|---|---|
| Advisory only | May be discussed or summarized; no execution or writeback | "What ran today?", "summarize this build log", "what does Hermes status mean?" | Runtime chat or docs/archive; capture useful output through governed writeback if needed. |
| Approval required | May execute only after scoped operator approval | Ad hoc `operator_today`, ad hoc `operator_close_day`, graph hygiene proposal run, retry failed scheduled run | Approval card in `approvals`; approval copied to audit; then route to eligible adapter. |
| Allowed execution | Already declared, approved, and bounded by manifest/schedule | Existing OpenClaw scheduled operator briefing path | Execute through OpenClaw -> `chaseos run` -> AOR; write normal outputs and audit. |
| Forbidden | Must not execute from Discord | Hermes shell, Hermes connectors, MCP implementation, Home Assistant, protected-file edits, canonical promotion, unregistered workflows, deletion, credential disclosure | Deny, log if meaningful, and route to architecture review only if the operator wants a future spec. |

Discord never grants a permission class by itself. The class is assigned by ChaseOS policy based on source, action, target, adapter, workflow, and current manifest state.

---

## Approval Model

An approval request must include:

- `request_id`
- `source_channel_class`
- `requesting_identity`
- `adapter`
- `workflow_id` or action name
- exact command/action proposed
- inputs and date/window
- read targets
- write targets
- external systems touched
- risk class
- expiration or single-run scope
- expected audit destination

Approvals are scoped to one action, one target set, one adapter, and one run. They do not generalize to future runs or adjacent workflow classes.

Approval states:

| State | Meaning |
|---|---|
| `pending` | No action may execute yet. |
| `approved_once` | Execute only the exact requested action once. |
| `denied` | Do not execute; record denial if a run was blocked. |
| `needs_clarification` | Ask operator; do not infer. |
| `expired` | Treat as denied; require a new approval. |

Approval is invalid if it is ambiguous, delivered by an unrecognized identity, delivered in the wrong channel class, or missing target/action scope.

---

## Audit and Writeback Model

Discord is not the audit store. The vault is.

When a Discord-sourced request leads to execution:

1. The request is classified.
2. The route decision is recorded.
3. Any required approval is recorded.
4. The adapter executes through the governed AOR path.
5. Writeback lands only in declared output targets.
6. The resulting audit record is written to `07_LOGS/Agent-Activity/`.
7. Discord receives a summary and links/paths to the canonical artifacts.

If Hermes and OpenClaw coordinate on the same work item, the machine-state handoff belongs in `runtime/agent_bus/`; Discord should receive only summaries, blockers, approvals, and artifact paths.

No run is considered complete because Discord says it completed. The canonical completion record is the AOR audit/writeback artifact.

---

## Hermes Bounded Discord Lane

Hermes is activated as a bounded Discord runtime lane. This activation is narrow and does not expand Hermes authority beyond what is explicitly listed here.

**What Hermes may now do via Discord:**

- Participate in `hermes-chat` as the Hermes free-response chat lane.
- Participate in `chaseos-ops` only when explicitly mentioned.
- Observe bounded approval records in `approvals` when a declared Hermes action requires approval.
- Post to Hermes-only output lanes (`alerts-hermes`, `debug-hermes`) and shared output lanes (`alerts-workflows`, `alerts-security`, `debug-adapters`, `runtime-debug`, `audit-writeback`, `artifact-paths`, `operator-runs`, `change-log`, `server-notes`, `docs-snippets`).
- Keep raw full logs local; Discord gets summaries, snippets, links, and paths rather than full log spam.
- Execute `hermes_operator_today_shadow` when an approved envelope is present.

**What Hermes still may not do:**

- Invoke shell commands.
- Use connectors.
- Call external networks beyond what `hermes_operator_today_shadow` manifest explicitly permits.
- Run `operator_today` or `operator_close_day` (those are OpenClaw workflows).
- Write canonical docs (`02_KNOWLEDGE/`, `01_PROJECTS/`, `06_AGENTS/`).
- Write Project-OS files.
- Promote content.
- Create or modify workflow manifests.
- Use persistent memory.
- Use generated skills.
- Access credentials.
- Perform multi-repo actions.
- Approve its own requests.
- Use Discord as a self-approval surface.

Any future expansion of Hermes Discord authority requires a separate pass that updates the Hermes adapter spec, workflow boundaries, role card, workflow manifest, runtime policy, permission matrix, audit path, and activation tests.

---

## OpenClaw Boundary Preserved

OpenClaw may use Discord as the active operational transport only inside its existing bounded adapter lane.

OpenClaw Discord control does not permit:

- direct vault writes outside AOR writeback,
- bypassing `chaseos run`,
- bypassing workflow manifests or role cards,
- shell expansion beyond its approved adapter scope,
- protected-file edits,
- canonical promotion,
- new connectors without explicit workflow declaration,
- multi-repo access without a manifest and operator approval.

OpenClaw remains an execution surface inside ChaseOS governance.

---

## Activation Requirements Before Multi-Harness Discord Execution

This document is a spec, not an implementation. Before Discord can become a multi-harness execution surface, ChaseOS needs:

1. ✅ **SCHEMA COMPLETE** — A Discord identity map for operator and runtime bot accounts. → `06_AGENTS/Discord-Identity-Map.md` (operator and bot IDs pending operator fill-in)
2. ✅ **SCHEMA COMPLETE** — A channel registry mapping real Discord channels to the canonical channel classes above. → `06_AGENTS/Discord-Channel-Registry.md` (real channel IDs pending operator fill-in)
3. ✅ **SCHEMA COMPLETE** — A signed or otherwise authenticated command envelope. → `06_AGENTS/Discord-Command-Envelope-Schema.md` (validation wiring deferred to future pass)
4. A request classifier that treats all Discord-origin input as untrusted until scoped.
5. An approval ledger that writes to `07_LOGS/Agent-Activity/` or a future formal audit path.
6. Adapter allowlists for which workflows may be triggered from Discord.
7. A deny-by-default policy for unknown commands, unknown users, unknown channels, and ambiguous actions.
8. Red-team tests for prompt injection, impersonation, replay, malformed approvals, and channel confusion.
9. Dry-run mode for every Discord-triggered execution route.
10. Documentation of rollback/failure behavior for each route.

Until all ten exist, Discord remains operational for the existing OpenClaw lane only and architectural/spec-level for broader ChaseOS use.

---

## Canonical Rule

Discord transports intent and visibility.
ChaseOS assigns meaning and authority.
AOR executes only declared workflows.
Gate governs writeback and promotion.
The vault remains canonical truth.

---

*Graph links: [[Vault-Map]] · [[OPENCLAW]] · [[OpenClaw-Runtime-Profile]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Runtime-Navigation-Map]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Runtime-Instance-Authority-Parity]] · [[Autonomous-Operator-Runtime]] · [[Permission-Matrix]] · [[Backends-Supported]] · [[Agent-Registry]] · [[Discord-Identity-Map]] · [[Discord-Channel-Registry]] · [[Discord-Command-Envelope-Schema]]*

*ChaseOS-Discord-Control-Plane.md - Version 1.2 | Created: 2026-04-20 (spec-only Discord control-plane architecture; OpenClaw route preserved; Hermes remains shadow-only and not Discord-enabled) | Patched: 2026-04-20 (Discord control-plane hardening Pass 1 — blockers 1–3 schema-complete; identity map, channel registry, and command envelope schema created; blocker status updated in activation requirements section) | Patched: 2026-04-20 (Hermes Discord Activation Alignment Pass — Hermes promoted to active bounded Discord runtime lane; Current Local Truth updated; Non-Goals updated; Routes to Hermes section replaced with bounded routing rules; Permission Model Forbidden row updated; Hermes Restrictions Preserved section renamed and split into active vs still-forbidden)*
