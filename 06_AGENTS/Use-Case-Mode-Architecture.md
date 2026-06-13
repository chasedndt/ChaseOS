---
type: architecture
title: Workspace Mode Layer Architecture
status: active contract
created: 2026-05-13
runtime_package: runtime/workspace_modes/
---

# Workspace Mode Layer Architecture

The Workspace Mode Layer (WML) is the ChaseOS context contract that tells agents what kind of workspace they are operating inside before reading, reasoning, writing, routing, escalating, or invoking workflows.

Canonical feature-family node: [[Workspace-Mode-Layer-Feature-Family]].

WML is not enterprise packaging, a team-account model, a Studio UI pass, or an RBAC layer. It is a local-first mode-awareness layer for a single ChaseOS operator who may move between personal, academic, venture, business operations, and runtime governance contexts.

## Why Mode Awareness Exists

ChaseOS already has governed memory, source intelligence, AOR workflows, permission matrices, trust tiers, adapter profiles, build logs, agent activity logs, and promotion gates. The missing question was:

> What kind of workspace is this task inside?

The same runtime should behave differently in a personal journal, a university module, a founder R&D workspace, a business SOP folder, or a runtime governance folder. WML makes that distinction explicit and machine-readable.

## Workspace Mode, Not User Type

Mode belongs to the workspace or task context, not to the human.

A single operator can simultaneously run:

| Workspace | Mode |
|---|---|
| Personal planning and doctrine | `personal_os` |
| University/coursework | `study_research` |
| TradeSync, VentureOps, product R&D | `founder_venture` |
| SOPs, fulfillment, client-safe process drafts | `business_ops` |
| ChaseOS runtime, AOR, adapters, permissions | `runtime_agent_ops` |

The user is not "enterprise" or "student" or "founder" globally. The current workspace has an operating mode.

## Modes

| Mode | Purpose | Default posture |
|---|---|---|
| `personal_os` | Personal life, goals, doctrine, routines, journaling, planning, private knowledge | Conservative; generated ideas allowed with labels; canonical/personal doctrine writes require approval |
| `study_research` | University, research, lectures, PDFs, labs, revision, evidence-grounded synthesis | Source/provenance first; generated explanations are hypotheses unless verified |
| `founder_venture` | Startups, products, R&D, market research, roadmap proposals, experiments | Strict around roadmap/project truth; generated venture ideas remain candidates until accepted |
| `business_ops` | SOPs, customer/process operations, fulfillment, support drafts, audit packets | Strict; no external sends or customer-impacting action without explicit approval |
| `runtime_agent_ops` | ChaseOS runtime governance, AOR, OpenClaw, Hermes, Codex, policies, workflows, logs | Very strict; protected writes, shell, external actions, and canonical mutation fail closed by default |
| `unknown` | Safe fallback when mode cannot be inferred | Inspect, summarize, propose mode, ask user; no runtime execution or durable/canonical writeback |

## What Modes Affect

WML influences:

- Read order: which docs/files should be loaded first.
- Output classes: build log, operator brief, source note, generated idea, proposal, audit packet.
- Knowledge classes: which of the six ChaseOS knowledge classes may be created or referenced.
- Workflows: which AOR or registry workflows are allowed in the workspace.
- Runtime adapter authority: the ceiling for Claude, Codex, OpenClaw, Hermes, and future adapters.
- Approval posture: when canonical state, protected paths, generated ideas, shell, or external connectors must escalate.
- Graph rules: index updates, backlinks, orphan-note flags, and promotion graph hygiene.
- Write targets: where outputs may land by default.

## Relationship to Knowledge Taxonomy

WML preserves the existing ChaseOS knowledge classes:

- `user-origin`
- `source-derived`
- `synthesized`
- `generated-ideas`
- `system-operational`
- `canonical-state`

WML does not rename or replace these classes. Profiles declare which classes are allowed for a workspace and which output classes are expected by default.

## Relationship to the AI-Generated Output Bridge

WML preserves the existing four-layer generated-output bridge:

| Layer | Meaning |
|---|---|
| Layer A | Raw quarantine capture under `03_INPUTS/00_QUARANTINE/[class]/` |
| Layer B | SIC workspace-local outputs under `runtime/source_intelligence/workspaces/{workspace_id}/outputs/` |
| Layer C | Durable generated artifacts under `02_KNOWLEDGE/[Domain]/Generated-Ideas/` |
| Layer D | Canonical promoted knowledge/state in `02_KNOWLEDGE/`, `01_PROJECTS/`, `00_HOME/Now.md`, `ROADMAP.md`, and `PROJECT_FOUNDATION.md` |

Generated ideas remain non-canonical until reviewed. Endorsement is human-only. Canonical promotion remains Gate-governed.

## Relationship to Agent Control Plane

WML sits below the request and above runtime action. Agents should resolve mode before acting, then apply:

1. `Agent-Control-Plane.md`
2. `Permission-Matrix.md`
3. `Trust-Tiers.md`
4. relevant runtime adapter profile
5. WML profile or safe inference result

WML does not grant authority. It narrows or clarifies the authority that existing control-plane rules already govern.

## Relationship to AOR

AOR runs workflows. WML supplies context for future workflow routing.

Future integration shape:

```text
workflow request
  -> resolve workspace mode
  -> load profile
  -> validate workflow allowed in profile
  -> validate runtime adapter ceiling
  -> validate write targets and approval rules
  -> run AOR workflow
  -> write audit/log output
```

The current implementation defines the contract and runtime helper package, exposes canonical CLI previews and packet helpers, has created the approved runtime/operator profile set, provides a no-execution AOR dispatch gate, can call AOR with `dry_run=True` through a WML-gated executor, can consume an exact approved packet for one live AOR workflow execution, and exposes read-only product status plus approval-ledger surfaces. Live execution remains exact-scope and approval-gated, not broad runtime autonomy.

Current read-only preview surface:

```powershell
python -m runtime.cli.main runtime workspace-mode route-preview --workspace-path runtime/aor/engine.py --workflow-id operator_today --adapter codex --json
```

Current review-only rollout surface:

```powershell
python -m runtime.cli.main runtime workspace-mode rollout-plan --json
```

Current validated draft-packet surface:

```powershell
python -m runtime.cli.main runtime workspace-mode draft-packet --json
```

Current profile-write approval request surface:

```powershell
python -m runtime.cli.main runtime workspace-mode write-approval-request --json
```

Current guarded profile writer surface:

```powershell
python -m runtime.cli.main runtime workspace-mode write-profiles --gate-approval-id wml-profile-write-appr-98b513c58e0412ac --confirm --json
```

Current no-execution dispatch gate surface:

```powershell
python -m runtime.cli.main runtime workspace-mode dispatch-gate --workspace-path runtime/aor/engine.py --workflow-id operator_today --adapter codex --confirm --json
```

Current WML-gated AOR dry-run executor surface:

```powershell
python -m runtime.cli.main runtime workspace-mode dispatch-dry-run --workspace-path runtime/aor/engine.py --workflow-id operator_today --adapter codex --confirm --json
```

Current live-execution approval request surface:

```powershell
python -m runtime.cli.main runtime workspace-mode live-execution-approval-gate --workspace-path runtime/aor/engine.py --workflow-id operator_today --adapter codex --confirm --json
```

Current exact-scope live executor surface:

```powershell
python -m runtime.cli.main runtime workspace-mode live-executor --workspace-path runtime/aor/engine.py --workflow-id operator_today --adapter codex --gate-approval-id wml-aor-live-exec-appr-58147fa104e8514d --decision approved --write-approval-decision --write-approval-consumption --write-consumption-marker --confirm --json
```

Current product status and approval ledger:

```powershell
python -m runtime.cli.main runtime workspace-mode product-status --json
python -m runtime.cli.main runtime workspace-mode approval-ledger --json
```

The canonical `chaseos` route-preview command resolves mode/profile source, inspects the requested workflow manifest, reports adapter ceiling, approval mode, write targets, and dispatch blockers, then stops. The rollout-plan command proposes explicit workspace profile targets and draft payloads for operator review. The draft-packet command renders validated YAML drafts and hashes them for review. The write-approval-request command renders a pending approval scope and exact operator confirmation text for profile creation, but by default does not write an approval artifact. The guarded writer created the three approved runtime foundation profiles and blocks duplicate overwrite attempts. The full-product profile pass then created the remaining missing business, study, and personal profiles after approval packet `wml-profile-write-appr-980b50fd2868cd1f`, leaving profile coverage at 6/6 valid. The dispatch gate confirms whether a request is ready for a guarded executor without calling `run_workflow`. The dry-run executor re-runs the gate, then calls `run_workflow(..., dry_run=True)` only after the gate clears. The live-execution approval gate re-runs the dispatch gate and can write a pending exact-scope approval request without live execution. The live executor consumes an exact approved packet once, records decision/marker/consumption artifacts, re-runs the dispatch gate, binds fresh dry-run evidence, and calls live AOR for that exact workflow only. Current proof consumed `wml-aor-live-exec-appr-58147fa104e8514d` and wrote `07_LOGS/Operator-Briefs/2026-05-14-operator-today.md`; a duplicate invocation blocked before `run_workflow`. `product-status` reports the WML runtime/operator product feature `COMPLETE` from repo evidence when core modules, profile coverage, architecture docs, and generated CLI/operator docs are present. `approval-ledger` reads profile-write and AOR live-execution artifacts without mutation. WML live execution does not grant Agent Bus tasks, provider/model calls, browser/external actions, protected-file writes, canonical promotion, or broad runtime autonomy.

## Relationship to Runtime Adapters

WML makes adapter ceilings mode-aware:

- `runtime_agent_ops`: strict, declared workflows only, protected/canonical writes gated.
- `business_ops`: draft/proposal/audit-first; no external business action by default.
- `founder_venture`: repo-bound development and proposal work allowed when scoped; roadmap adoption requires approval.
- `study_research`: research/synthesis surfaces allowed; dangerous shell/runtime actions blocked.
- `personal_os`: bounded tasks only; no full-control runtime behavior by default.
- `unknown`: runtime execution blocked.

OpenClaw and Hermes remain bounded by declared workflows only. Host capability is treated as risk, not permission.

## Relationship to Studio and Chat

The WML runtime/operator product feature is complete and now has read-only Studio and Chat visibility. Product status, approval ledger, profile coverage, route previews, guarded executor surfaces, the Studio Workspace Mode panel, and the Chat-side `Workspace Mode Studio` deeplink selector are all machine-readable or UI-visible over the same WML contract.

The Studio panel exposes URL-persistent `wml_mode` selection, project/domain context, route previews, and visual proof. The Chat selector exposes the same mode family as navigation-only cards that deep-link into the Studio panel. These surfaces do not execute WML workflows, write profiles, dispatch Agent Bus tasks, consume approvals, call providers, or mutate canonical state.

## Fail-Closed Rule

If no profile exists and path inference cannot prove a mode, WML returns `unknown`.

`unknown` permits inspection and proposal only. It does not authorize durable outputs, canonical state writes, runtime execution, external sends, generated idea promotion, or protected-path mutation.

---

*Graph links: [[Workspace-Mode-Layer-Feature-Family]] [[Workspace-Mode-Profile-Standard]] [[Knowledge-Taxonomy]] [[AI-Generated-Output-Bridge]] [[Agent-Control-Plane]] [[Autonomous-Operator-Runtime]] [[ChaseOS-Studio-Architecture]] [[ChaseOS-Phase11-Architecture]] [[Vault-Map]] [[Permission-Matrix]] [[Trust-Tiers]]*
