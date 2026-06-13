---
title: Workflow Registry and Role Cards Standalone Application
type: implementation-bridge-plan
status: seeded — third concrete application of the markdown-to-standalone bridge
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Workflow Registry and Role Cards Standalone Application

> This document is the third concrete application pass for `06_AGENTS/Markdown-to-Standalone-Bridge.md`.
> It translates the bridge rules into a third standalone-ready slice: workflow registry + role-card permission envelopes.

**Approval Center routing:** workflow approval-center destinations should route to [[ChaseOS-Approval-Center]] for current cross-feature Approval Center semantics.

---

## 1. Purpose

The previous application passes established:
- how runtime navigation and browser governance map into standalone inspector surfaces,
- how runtime state, bootstrap, and detachable user attachment map into runtime posture surfaces,
- and how summaries should be treated as typed operating artifacts rather than generic text.

The next strongest slice is the one that tells ChaseOS:
- what executable workflow objects exist,
- what runtime permission envelope each workflow runs inside,
- how those two records stay distinct but linked,
- and how future operator surfaces should inspect them without turning the UI into a hidden authority system.

This document applies the bridge to:
- workflow manifests under `runtime/workflows/registry/`,
- role cards under `06_AGENTS/role-cards/`,
- and the future standalone surfaces that must show executable identity, bounded authority, and approval posture together.

This remains a planning/application artifact.
It does **not** replace markdown or YAML as current source of truth.

---

## 2. Scope of This Application Pass

Included in this pass:
- `runtime/workflows/registry/_schema.yaml`
- `runtime/workflows/registry/operator_today.yaml`
- `runtime/workflows/registry/operator_close_day.yaml`
- `runtime/workflows/registry/browser_research.yaml`
- `runtime/workflows/registry/graph_hygiene.yaml`
- `runtime/workflows/registry/graduate_ideas.yaml`
- `runtime/workflows/registry/source_pack_builder.yaml`
- `runtime/workflows/registry/hermes_operator_today_shadow.yaml`
- `runtime/workflows/registry/sbp_strikezone_digest.yaml`
- `runtime/workflows/registry/strikezone_acquisition.yaml`
- `runtime/workflows/registry/developer_repo_explain_shadow.yaml`
- `06_AGENTS/role-cards/_schema.yaml`
- `06_AGENTS/role-cards/operator-briefing.yaml`
- `06_AGENTS/role-cards/browser-research.yaml`
- `06_AGENTS/role-cards/vault-maintenance.yaml`
- `06_AGENTS/role-cards/idea-graduation.yaml`
- `06_AGENTS/role-cards/source-pack-builder.yaml`
- `06_AGENTS/role-cards/scheduled-briefing.yaml`
- `06_AGENTS/role-cards/hermes-operator-shadow.yaml`
- `06_AGENTS/role-cards/developer-copilot-shadow.yaml`

Not included yet:
- workflow editor UX
- role-card mutation UI
- approval-writing surfaces
- run-launch controls beyond existing bounded runtime/CLI paths
- generalized execution graph modeling beyond manifest + role-card pairing

---

## 3. Current Markdown-Era Roles

### A. Human-readable governance and interpretation layer
These files explain what the registry and role-card layer means inside ChaseOS:
- `06_AGENTS/Autonomous-Operator-Runtime.md`
- `06_AGENTS/HERMES.md` / `OPENCLAW.md` / adapter specs where relevant
- build logs and pass docs that explain why certain workflows or role cards exist

### B. Machine-readable execution identity layer
These files declare executable workflow objects:
- workflow manifest schema
- workflow manifests in `runtime/workflows/registry/`

### C. Machine-readable permission-envelope layer
These files declare bounded authority and escalation rules:
- role-card schema
- role cards in `06_AGENTS/role-cards/`

### D. Current operating pattern
Today ChaseOS works because these layers are distinct:
- docs explain the execution model,
- manifests define *what may run*,
- role cards define *what boundaries apply when it runs*,
- AOR and Gate enforce those declarations during execution,
- logs/audit records preserve what actually happened.

The standalone must preserve those distinctions instead of flattening workflows and permissions into one generic “automation card.”

---

## 4. Standalone Surface Families for This Slice

| Current artifact family | Standalone family | Primary standalone surface |
|---|---|---|
| Workflow manifest docs/records | Workflow Record | workflow registry browser |
| Role-card docs/records | Permission Envelope Record | role-card / permission inspector |
| Workflow manifest schema | Workflow Schema Record | workflow schema inspector |
| Role-card schema | Permission Schema Record | role-card schema inspector |
| Workflow + role-card linkage | Executable Contract View | workflow contract panel |
| Workflow-linked summary outputs | Summary Context View | runtime-aware summary/briefing panel |

---

## 5. Concrete Mapping Table

| Current path | Current role | Future standalone role | Key fields / behaviors that must survive |
|---|---|---|---|
| `runtime/workflows/registry/_schema.yaml` | manifest schema reference | workflow schema inspector | required fields, optional fields, identity rules, writeback/failure/audit declarations |
| `runtime/workflows/registry/operator_today.yaml` | active workflow manifest | workflow record | workflow identity, task type, role-card binding, writeback targets, approval rule, audit expectations |
| `runtime/workflows/registry/operator_close_day.yaml` | active workflow manifest | workflow record | same family as `operator_today`; comparable execution object |
| `runtime/workflows/registry/browser_research.yaml` | bounded browser workflow manifest | workflow record | browser-governed task identity, declared writeback, role-card coupling |
| `runtime/workflows/registry/graph_hygiene.yaml` | maintenance workflow manifest | workflow record | maintenance task identity, bounded write scope, review posture |
| `runtime/workflows/registry/graduate_ideas.yaml` | idea-promotion workflow manifest | workflow record | proposal/promotion posture, review-required path |
| `runtime/workflows/registry/source_pack_builder.yaml` | acquisition/build workflow manifest | workflow record | source-pack generation identity, declared outputs, bounded build scope |
| `runtime/workflows/registry/hermes_operator_today_shadow.yaml` | Hermes bounded shadow workflow manifest | workflow record | shadow mode, permission ceiling, restricted writebacks, non-canonical posture |
| `runtime/workflows/registry/sbp_strikezone_digest.yaml` | scheduled briefing workflow manifest | workflow record | schedule-linked execution identity, delivery-facing output class, guardrail linkage |
| `runtime/workflows/registry/strikezone_acquisition.yaml` | acquisition workflow manifest | workflow record | acquisition-stage posture, source-pack/briefing-input role |
| `runtime/workflows/registry/developer_repo_explain_shadow.yaml` | developer shadow workflow manifest | workflow record | draft-only/developer-copilot posture, bounded output targets |
| `06_AGENTS/role-cards/_schema.yaml` | role-card schema reference | permission schema inspector | required boundary fields, escalation rules, runtime expectations |
| `06_AGENTS/role-cards/operator-briefing.yaml` | permission envelope for operator brief workflows | permission envelope record | read-heavy/write-log-only posture, forbidden actions, write scope, escalation conditions |
| `06_AGENTS/role-cards/browser-research.yaml` | permission envelope for browser research workflows | permission envelope record | origin/task bounds, browser action restrictions, writeback boundary |
| `06_AGENTS/role-cards/vault-maintenance.yaml` | permission envelope for maintenance workflows | permission envelope record | hygiene-focused writes, forbidden protected mutations, escalation policy |
| `06_AGENTS/role-cards/idea-graduation.yaml` | permission envelope for idea graduation workflows | permission envelope record | proposal-only promotion posture, review requirements |
| `06_AGENTS/role-cards/source-pack-builder.yaml` | permission envelope for source-pack building | permission envelope record | acquisition/build scope, output constraints, no authority expansion |
| `06_AGENTS/role-cards/scheduled-briefing.yaml` | permission envelope for scheduled briefings | permission envelope record | schedule/governance coupling, delivery-safe boundary |
| `06_AGENTS/role-cards/hermes-operator-shadow.yaml` | Hermes-specific bounded role card | permission envelope record | shadow-only/log-only posture, forbidden shell/network/canonical writes |
| `06_AGENTS/role-cards/developer-copilot-shadow.yaml` | developer shadow role card | permission envelope record | draft-only developer assistance boundary |

---

## 6. Recommended Standalone Views

### A. Workflow Registry Workspace
This should answer:
1. **What workflows exist?**
2. **What kind of task does each workflow represent?**
3. **What role card governs it?**
4. **What outputs, writebacks, and approval posture follow from that pairing?**

Recommended panels:
1. **Workflow list / registry browser**
   - workflow ID
   - status
   - task type
   - trigger type
   - owner
2. **Workflow detail panel**
   - permission ceiling
   - writeback targets
   - failure behavior
   - approval rule
   - audit expectations
3. **Linked role-card summary**
   - role-card ID
   - write scope
   - forbidden actions
   - escalation rules
4. **Output/summaries panel**
   - operator briefs
   - build/session outputs
   - advisory summaries
   - approval/proposal outputs

### B. Permission Envelope Workspace
This should show that role cards are not personas but bounded execution envelopes.

Recommended panels:
1. **Role-card summary**
   - owner
   - allowed actions
   - forbidden actions
   - runtime expectations
2. **Write boundary panel**
   - write scope
   - forbidden write zones
3. **Escalation panel**
   - hard-stop triggers
   - missing-read or out-of-scope conditions
4. **Linked workflows panel**
   - which workflow manifests use this role card

### C. Workflow Contract Workspace
This should combine workflow record + role card without collapsing them.

Recommended panels:
1. **Executable identity**
   - workflow manifest metadata
2. **Permission envelope**
   - linked role-card boundary
3. **Governance chain**
   - AOR
   - Gate
   - audit trail
4. **Summary context panel**
   - what summary/output classes this workflow usually emits
   - where those summaries belong in the OS
   - whether they are advisory, evidentiary, or approval-facing

---

## 7. Relationship to the Summary Context Layer

This slice is where the Summary Context Layer becomes especially important.

A workflow record alone tells ChaseOS:
- what should run,
- under what manifest identity,
- with what writeback targets.

A role card alone tells ChaseOS:
- what the runtime may and may not do,
- where escalation must happen.

But when a workflow actually produces a summary or artifact, ChaseOS still needs to know:
- what class of summary that output is,
- whether it should appear in a runtime cockpit, approval center, chronology browser, or project cockpit,
- whether it is advisory, operational evidence, or proposal/review material.

That means future standalone surfaces should treat workflow outputs as:
- **workflow-linked summaries**, not anonymous text,
- typed by workflow class + role-card posture + routing destination.

This is how summary generation stays aligned with the OS rather than floating above it as generic prose.

### Summary-context application
For how workflow-linked summaries should preserve manifest identity, role-card authority envelope, and draft/proposal/shadow posture in future standalone surfaces, see:
- `06_AGENTS/Workflow-Registry-and-Role-Cards-Summary-Context-Application.md`

---

## 8. Service-Layer Boundary Rules

The standalone service layer for this slice should preserve the distinctions ChaseOS already relies on.

### Workflow records do not grant authority by themselves
A manifest is a declaration, not a permission bypass.
It remains subordinate to Gate, role cards, constitutional doctrine, and runtime state.

### Role cards remain boundary files, not UI labels
The standalone must not degrade role cards into friendly decorative descriptions.
Their job is to preserve hard execution boundaries.

### Workflow + role-card linkage must remain inspectable
The operator should always be able to see which role card governs which workflow.
Hidden coupling would make the system harder to audit.

### Summary outputs must preserve execution context
Summaries created by workflows should retain:
- workflow identity,
- role-card/authority posture,
- routing destination,
- promotion posture,
- provenance and audit linkage.

### No hidden launch authority
A workflow browser is not the same thing as permission to execute a workflow.
Any future run surface must still route through the normal AOR + approval + Gate chain.

---

## 9. Suggested Data Model Direction

This slice suggests ChaseOS likely needs at least these additional standalone object families:
- `workflow_record`
- `permission_envelope_record`
- `workflow_contract_view`
- `workflow_output_summary_record`

And likely these specialized presentation layers:
- `workflow_registry_view`
- `role_card_inspector`
- `workflow_contract_view`
- `approval_posture_view`

That matters because the standalone cannot treat execution as a single undifferentiated automation object.
ChaseOS execution is manifest-defined, role-card-bounded, and audit-linked.

---

## 10. What This Application Pass Proves

This pass proves the bridge can be extended from runtime posture and summary interpretation into executable workflow contracts.
It clarifies:
- which YAMLs are workflow records versus permission-envelope records,
- how those two records should stay linked but distinct,
- how future standalone surfaces can show execution identity without silently broadening authority,
- and how workflow-produced summaries fit into the wider ChaseOS operating model.

This means the bridge now has a third worked example, moving from navigation and posture into governed execution identity.

---

## 11. Alignment with the Overall ChaseOS Operating System

This pass aligns with ChaseOS as an operating system in four important ways.

### A. It reinforces constitutional layering
ChaseOS is not “just workflows.”
It is a constitutional OS where:
- doctrine defines the rules,
- manifests define executable identities,
- role cards define bounded authority,
- AOR executes,
- Gate enforces,
- audit logs preserve history.

This doc keeps those layers explicit.

### B. It preserves Phase 9 -> Phase 10 continuity
Phase 9 builds the execution substrate.
Phase 10 must surface that substrate without mutating its meaning.
This application pass defines how a future standalone can expose workflow execution objects faithfully.

### C. It improves operator legibility
A real OS needs the operator to understand:
- what can run,
- what permissions apply,
- what outputs belong where,
- what requires approval.

This slice makes those relationships inspectable instead of implicit.

### D. It keeps summaries aligned with governed execution
When a workflow produces a briefing, build artifact, browser summary, or proposal, that output should remain visibly tied to the execution contract that produced it.
That is exactly how summaries align with the overall ChaseOS model: not as detached text, but as governed OS artifacts.

---

## 12. Recommended Next Application Passes

After this slice, the strongest next bridge applications would be:
1. **agent bus + coordination substrate**
   - `runtime/agent_bus/`
   - `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
2. **core/personal split + export surfaces**
   - `CORE_MANIFEST.md`
   - `core_templates/`
   - `06_AGENTS/Core-Export-Sync-Procedure.md`
3. **runtime shell / approval center / operator browser use-case surfaces**
   - operator shell docs
   - approval-centered routing docs
   - runtime browser planning docs

That sequence would move from execution identity into coordination, portability, and operator-facing action surfaces.

---

## 13. Current Verdict

A future ChaseOS standalone should not present workflows as simple buttons or cards.
It should present them as **typed governed execution contracts** with:
- explicit manifest identity,
- explicit permission envelope,
- explicit summary/output posture,
- and explicit OS-level routing context.

That is how workflow execution aligns with the overall ChaseOS operating system.

---

*Graph links: [[Markdown-to-Standalone-Bridge]] · [[Standalone-Summary-Context-Layer]] · [[Runtime-State-and-Bootstrap-Standalone-Application]] · [[Autonomous-Operator-Runtime]] · [[ChaseOS-Studio-Architecture]]*

*Workflow-Registry-and-Role-Cards-Standalone-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
