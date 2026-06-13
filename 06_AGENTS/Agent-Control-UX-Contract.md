---
title: Agent Control UX Contract
type: product-runtime-contract
status: CONTRACT SEEDED / BROWSER LANE PROVEN LOCALLY / FILES SYSTEM RUNTIME LANES NOT BUILT
created: 2026-05-04
updated: 2026-05-04
phase: Phase 9 to Phase 10 bridge
runtime: Codex
---

# Agent Control UX Contract

This contract defines how ChaseOS should visibly represent an agent or runtime
controlling an external surface.

It is a product and safety contract, not a permission grant. A visible control
indicator does not authorize an action. Authority still comes from the ChaseOS
control plane: scoped workflow manifests, SiteOps policy, AOR routing, Gate
checks, approvals, tenancy/session boundaries, and audit/provenance.

## Current Status

The browser lane has one complete targeted local proof:

```text
06_AGENTS/SiteOps-Agent-Control-Visual-Affordance-Proof.md
07_LOGS/Browser-Runs/local/default/siteops-agent-control-visual-affordance-proof-20260504-final.png
```

That proof shows:

- `Agent control active` HUD,
- cursor icon,
- movement trail,
- click feedback,
- drag feedback,
- browser-lane marker,
- scoped Browser Run / SiteOpsRun / SiteOpsAudit evidence.

The following lanes are contract-only and are not built:

- file explorer control,
- OS/system control,
- runtime/lifecycle control,
- authenticated browser/session control,
- external-site production autonomy.

## Control Lanes

| Lane | Purpose | Current Status | Required Before Implementation |
| --- | --- | --- | --- |
| Browser | Operate local or external browser surfaces under SiteOps policy | Proven locally on a ChaseOS-owned sandbox | Site profile, workflow manifest, user/session scope, approval rules, audit path |
| Files | Open, inspect, move, rename, or edit files through an operator surface | Not built | Workspace scope, protected-file rules, explicit file targets, dry-run preview, undo/rollback policy |
| System | Operate OS-level UI, settings, apps, windows, or shell-adjacent surfaces | Not built | High-risk approval model, allowlisted actions, no-destructive default, operator takeover, event recording |
| Runtime | Start, stop, inspect, or coordinate runtimes, daemons, schedules, or adapters | Not built | Runtime manifest, lifecycle policy, Agent Bus/AOR routing, Gate allowance, audit ledger |

## Required Visual Components

Every controlled surface must show these elements while an agent is operating:

1. Active-control HUD  
   A fixed indicator naming the controlling runtime, active lane, current state,
   and risk level.

2. Cursor or focus marker  
   Browser and desktop lanes should show a pointer. File/runtime lanes may show
   a focus outline or selected target marker instead of a cursor.

3. Action feedback  
   Clicks, drags, typed input, file operations, runtime actions, and approval
   pauses must produce visible feedback.

4. Control lane rail  
   The UI must clearly distinguish `browser`, `files`, `system`, and `runtime`
   lanes so an operator can see what kind of authority is active.

5. Approval state  
   If execution reaches an approval gate, the surface must stop and show
   `approval_needed`. It must not continue while approval is pending.

6. Blocked state  
   If policy denies an action, the surface must show `blocked` and record the
   policy decision.

7. Manual takeover state  
   Future interactive sessions must expose a clear `manual_takeover` state so
   the operator can pause the agent and take control.

8. Provenance link  
   The UI must link to the scoped run/audit/artifact record or show its run ID.

## Control States

| State | Meaning | Runner Behavior |
| --- | --- | --- |
| `idle` | No agent control active | No action surface visible except history |
| `armed` | A workflow is ready but not acting | Show plan, scope, and approvals |
| `observing` | Agent is reading or inspecting | Read-only indicators only |
| `controlling` | Agent is actively operating a surface | Show HUD, cursor/focus, action feedback |
| `approval_needed` | A gate paused execution | Stop execution and create/await approval object |
| `blocked` | Policy denied the action | Stop execution and log policy decision |
| `manual_takeover` | Human operator is controlling the surface | Agent pauses and records takeover boundary |
| `completed` | Run finished | Show result and evidence links |
| `failed` | Run failed | Show error, artifact links, and recovery options |

## Minimum Event Schema

Future implementations should emit an event shape compatible with this contract:

```yaml
event_type: agent_control_event
run_id: required
tenant_id: required
workspace_id: required
user_id: required
runtime_id: required
lane: browser | files | system | runtime
state: idle | armed | observing | controlling | approval_needed | blocked | manual_takeover | completed | failed
action: optional
target_ref: optional
risk_level: low | medium | high | critical
policy_decision_ref: optional
approval_id: optional
artifact_ref: optional
timestamp: required
redacted_fields: []
```

Events must not include secrets, cookies, raw session data, private keys,
passwords, tokens, seed phrases, or raw credential values.

## Browser Lane Requirements

The browser lane must keep the current local proof guarantees:

- throwaway profile for local proofs,
- user-scoped profile refs for future production,
- no raw cookies or session contents in logs,
- domain allowlist checks,
- blocked export/share/account mutation unless approved,
- visible cursor and action feedback,
- screenshot/run/audit evidence under scoped artifact roots.

## Files Lane Requirements

The files lane must not become "agent can freely use File Explorer."

Before any implementation:

- exact root and target path scope must be known,
- protected-file rules must be loaded,
- destructive actions must be denied by default,
- move/rename/delete must require explicit approval,
- file contents shown to the agent must follow existing read rules,
- every operation must produce a preview and audit event,
- hidden canonical writeback remains forbidden.

## System Lane Requirements

The system lane is highest risk and must start as read-only/observe-only.

Before mutation:

- system action categories must be allowlisted,
- app/window target must be explicit,
- settings changes, installs, permissions, account changes, purchases, and
  destructive operations require explicit approval,
- operator takeover must be available,
- no secrets may be read from password managers, browser storage, terminal
  history, environment files, or credential stores.

## Runtime Lane Requirements

The runtime lane must route through ChaseOS-owned runtime state, not ambient UI
state.

Required boundaries:

- registered runtime manifest,
- role/permission check,
- AOR or Agent Bus routing where coordination-sensitive,
- Gate allowance for mutation,
- lifecycle audit event,
- no start/stop/restart of production runtimes without explicit approval,
- no Hermes/OpenClaw/Codex authority expansion by UI implication.

## Product Surface Pattern

The future Studio surface should expose:

```text
Control HUD
├── Runtime: Codex / OpenClaw / Hermes / Site Operator
├── Lane: Browser / Files / System / Runtime
├── State: Observing / Controlling / Approval needed / Blocked
├── Scope: tenant / workspace / user
├── Current action
├── Risk level
├── Approval gate if present
└── Run/audit link
```

The operator should always be able to answer:

- Who is controlling?
- What lane are they controlling?
- What are they doing now?
- What can they not do?
- What approval is needed?
- Where is the audit trail?
- How do I pause or take over?

## Phase 11 Chat Intent Translation Surface

The Phase 11 chat surface is an operator ingress and preview layer, not an execution backend. Natural-language commands such as `do X`, `/run ...`, or `ask Hermes ...` must first be translated into inspectable structured intent/action state before any lower-phase surface can consider work.

Minimum Phase 11 intent preview fields:

- `intent_class` and deterministic classifier metadata,
- affected surfaces such as Phase 11 Chat, Studio proposal cards, `runtime/agent_bus`, AOR/Gate, provider routing, SiteOps/browser-shell-connector authority, or canonical writeback,
- authority class: read-only preview, model-route preview, proposal-only, approval-gated lower-phase dependency, or denied lower-phase dependency,
- required approvals and blocked reasons,
- ambiguity status and denial status,
- duplicate fingerprint handling,
- backend dependency mapping naming missing contract, affected Phase 10/11 surface, lower-phase owner/surface, minimum proof needed, and blocked action reason,
- schema-compatible Agent Bus task/event previews when runtime coordination is implicated.

The chat surface may render these previews and blocked states. It must not dispatch runtime work, consume approvals, control browser/shell/connectors, mutate credentials/config, write protected files, promote source packs, mutate graph/canonical knowledge, or imply Hermes/OpenClaw authority expansion by language alone. Those actions remain Phase 9-and-below foundation work routed through ChaseOS structured state.

## Non-Goals For This Contract

This contract does not:

- grant browser authority,
- implement file explorer control,
- implement OS/system control,
- implement runtime lifecycle control,
- authorize external websites,
- authorize authenticated sessions,
- bypass Gate/AOR/SiteOps policy,
- expand Hermes/OpenClaw/Codex authority,
- create a marketplace or public Site Skills UI.

## Next Implementation Order

1. Keep browser lane as the only proven local control lane.
2. Use `06_AGENTS/Live-Operator-Shell-Browser-Surface.md` as the Phase 10 browser shell scope: render visible-control/readiness/dependency states first, with no shell-side browser execution.
3. Add the first read-only `runtime/operator_surface/browser/` panel model that composes existing Browser Runtime readiness and Chat/Studio dispatch-lane proofs.
4. Add a shared event schema module only after another lane needs it.
5. Add files lane as preview-only/read-only before any mutation.
6. Add runtime lane as inspect-only before lifecycle controls.
7. Treat system lane as last and highest-risk.

## Related Docs

- `06_AGENTS/Live-Operator-Shell-Browser-Surface.md`
- `runtime/operator_surface/browser/Browser-Operator-Surface-Folder-Guide.md`
- `06_AGENTS/SiteOps-Agent-Control-Visual-Affordance-Proof.md`
- `06_AGENTS/Agent-Control-Plane.md`
- `06_AGENTS/Permission-Matrix.md`
- `06_AGENTS/SiteOps-Candidate-Executor-Feature-Completion-Tracker.md`
- `runtime/browser_runtime/README.md`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
