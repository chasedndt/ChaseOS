---
title: Runtime Shell, Approval Center, and Runtime Browser Standalone Application
type: implementation-bridge-plan
status: seeded — fifth concrete application of the markdown-to-standalone bridge
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Runtime Shell, Approval Center, and Runtime Browser Standalone Application

> This document is the fifth concrete application pass for `06_AGENTS/Markdown-to-Standalone-Bridge.md`.
> It translates the bridge rules into a standalone-ready operator action slice: the Runtime Shell command surface, OSRIL approval/session visibility, and the future Approval Center / Agent-Runtime Browser family.

Canonical cross-feature Approval Center reference:
[[ChaseOS-Approval-Center]]. This document remains a bridge/application plan;
the standalone Approval Center document owns current source-family and authority
boundary truth.

---

## 1. Purpose

The earlier worked bridge passes covered:
- runtime navigation + browser governance,
- runtime state + bootstrap/user attachment,
- workflow registry + role-card execution contracts,
- the Summary Context Layer for typed operating artifacts,
- and the coordination substrate for dual-runtime task routing.

The next strong slice is the one that turns those substrates into an operator-facing control surface.

This pass applies the bridge to:
- `06_AGENTS/ChaseOS-Runtime-Shell.md`
- `06_AGENTS/Operator-Surface-Runtime-Interaction.md`
- `06_AGENTS/Full-System-Operator-Surface.md`
- `06_AGENTS/Browser-Operator-Surface-Operational-State.md`
- the Phase 10 surface targets already described in `Feature-Fit-Register.md`

This remains a planning/application artifact.
It does **not** create a UI, replace the markdown docs, or change current authority paths.

---

## 2. Scope of This Application Pass

Included in this pass:
- `06_AGENTS/ChaseOS-Runtime-Shell.md`
- `06_AGENTS/Operator-Surface-Runtime-Interaction.md`
- `06_AGENTS/Full-System-Operator-Surface.md`
- `06_AGENTS/Browser-Operator-Surface-Operational-State.md`
- `06_AGENTS/Feature-Fit-Register.md`
- `06_AGENTS/Standalone-Summary-Context-Layer.md`
- `06_AGENTS/Workflow-Registry-and-Role-Cards-Standalone-Application.md`
- `06_AGENTS/Runtime-Agent-Bus-and-Coordination-Standalone-Application.md`

Not included yet:
- final desktop/graph UI implementation
- mutation-capable approval actions in a live standalone app
- full OSRIL event-bus implementation
- runtime shell backend completion beyond the current CLI/runtime footholds
- scorecard-driven runtime ranking surfaces
- voice shell / companion surface implementation

---

## 3. Current Markdown-Era Roles

### A. Operator command-ingress layer
These docs define how an operator should issue commands into ChaseOS:
- `ChaseOS-Runtime-Shell.md`
- future shell router / workflow launcher / provider registry files when built

### B. Runtime-event and session-visibility layer
These docs define how running work becomes visible back to the operator:
- `Operator-Surface-Runtime-Interaction.md`
- `Full-System-Operator-Surface.md`
- browser operator surface operational-state docs for the first live child execution slice

### C. Execution/governance substrate below the shell
These already-established bridge slices supply the underlying machine meaning:
- workflow manifests + role cards
- runtime state + bootstrap posture
- coordination bus state
- summary-context routing

### D. Future product-facing operator surfaces
These are already named in architecture/register docs even though they are not built yet:
- Runtime/Operator View
- Approval Center
- Agent / Runtime Browser
- Live Operator Shell
- runtime cockpit and chronology-linked review surfaces

### E. Current operating pattern
Today ChaseOS keeps these distinctions intact:
- command ingress is not the same as execution authority,
- approval visibility is not the same as approval mutation,
- runtime state display is not the same as machine-state truth,
- operator-facing summaries are derivative surfaces, not sovereign doctrine.

The standalone must preserve those distinctions instead of collapsing everything into one generic dashboard.

---

## 4. Standalone Surface Families for This Slice

| Current artifact family | Standalone family | Primary standalone surface |
|---|---|---|
| Runtime shell doctrine | Operator Command Surface Node | runtime shell / command palette / workflow launcher view |
| OSRIL event/session architecture | Runtime Interaction Contract View | live operator shell / runtime session panel |
| FSOS parent execution architecture | Operator Execution Surface Node | operator activity / surface inspector |
| Browser operator operational-state record | Runtime Surface Status Record | browser surface status panel |
| Approval-center feature rows in register/docs | Approval Queue View | approval center |
| Agent/runtime browser feature rows in register/docs | Runtime Identity Browser View | runtime browser / runtime registry panel |
| workflow/coordination/runtime-state summary links | Operator Summary Context View | cockpit cards / approval items / chronology-linked detail panes |

---

## 5. Concrete Mapping Table

| Current path | Current role | Future standalone role | Key fields / behaviors that must survive |
|---|---|---|---|
| `06_AGENTS/ChaseOS-Runtime-Shell.md` | canonical command-surface doctrine | runtime shell / command-surface node | command family distinctions, shell-vs-AOR separation, provider registry concept, workflow launcher rules, config-store boundaries |
| `06_AGENTS/Operator-Surface-Runtime-Interaction.md` | OSRIL architecture and session/approval/event model | runtime interaction contract view | event classes, approval-linked execution flow, session continuity, runtime-local session state, operator visibility rules |
| `06_AGENTS/Full-System-Operator-Surface.md` | execution-surface family architecture | operator execution surface node | ingress-vs-execution distinction, shared contracts, surface hierarchy, approval/audit/recovery posture |
| `06_AGENTS/Browser-Operator-Surface-Operational-State.md` | first live operator-surface runtime status record | runtime surface status record | what is live now, what is deferred, reopen conditions, smoke tests, operational posture |
| `06_AGENTS/Feature-Fit-Register.md` Phase 10 rows | canonical product-surface declarations | approval-center / runtime-browser / cockpit capability references | status truth, dependency gates, governance notes, cross-phase placement |
| `06_AGENTS/Workflow-Registry-and-Role-Cards-Standalone-Application.md` | execution-contract bridge slice | workflow-launch context panel | workflow identity, role-card linkage, no hidden launch authority |
| `06_AGENTS/Runtime-Agent-Bus-and-Coordination-Standalone-Application.md` | coordination bridge slice | coordination-linked operator panel | blocker/review posture, liveness view, machine-state provenance |
| `06_AGENTS/Standalone-Summary-Context-Layer.md` | typed summary/use-case layer | operator summary-context view | routing surface, authority posture, promotion posture, runtime identity |

---

## 6. Recommended Standalone Views

### A. Runtime Shell / Command Surface
This should answer:
1. what commands or workflow launches are available,
2. what each command family actually routes to,
3. what governance layers apply before execution starts,
4. and what runtime/provider/config posture is currently active.

Recommended panels:
1. **Command palette / shell launcher**
   - command family
   - workflow shortcuts
   - task class
   - required context
2. **Execution route panel**
   - shell command -> workflow manifest -> role card -> AOR -> Gate path
3. **Provider/config panel**
   - current provider/model registry posture
   - config-store visibility
   - shell-level preferences
4. **Run eligibility panel**
   - what is runnable now
   - what is blocked by missing handlers, approval, or status

### B. Approval Center
This should present approvals as typed governed work, not as raw notifications.

Recommended panels:
1. **Unified approval queue**
   - approval class
   - source workflow/runtime
   - current posture
   - age / urgency
2. **Approval detail panel**
   - originating workflow or operator run
   - requested action
   - affected write targets or action class
   - provenance links
3. **Decision context panel**
   - role-card boundary
   - runtime state
   - related coordination/blocker context
4. **Chronology / audit panel**
   - immutable approval records
   - response history
   - downstream effect trace

### C. Agent / Runtime Browser
This should show runtime identity as a bounded operating concept, not a personality gallery.

Recommended panels:
1. **Runtime registry list**
   - runtime ID
   - adapter lane
   - lifecycle state
   - trust ceiling
2. **Runtime detail panel**
   - active role/profile docs
   - current posture
   - allowed workflow families
   - output surfaces
3. **Permission / boundary panel**
   - role-card links
   - manifest-linked limits
   - forbidden zones/actions
4. **Recent activity + summary panel**
   - last run status
   - recent summaries
   - coordination posture
   - review/blocker state where relevant

### D. Live Operator Shell / Runtime Session Panel
This is the place where OSRIL and FSOS visibility become legible.

Recommended panels:
1. **Current session state**
   - active workflow
   - current step
   - pending approvals
   - runtime ownership
2. **Event feed**
   - typed events
   - start/progress/pause/recovery/complete
3. **Surface-state subpanel**
   - browser/terminal/desktop/filesystem status when relevant
4. **Resume / reconnect context**
   - what can be resumed
   - what is only historical
   - what requires a fresh run

---

## 7. Relationship to the Summary Context Layer

This slice depends on the Summary Context Layer because operator-facing shells and approval surfaces are where summary ambiguity becomes dangerous.

Without typed summary context:
- an approval request can look like a completion,
- a runtime-status card can look like authority,
- a coordination blocker can look like a low-priority notification,
- a session summary can look like canonical truth,
- a browser run status can look like an unconstrained agent capability.

The Summary Context Layer already established that summaries should carry:
- runtime identity,
- output class,
- authority posture,
- source posture,
- routing destination,
- promotion/review posture.

This operator-facing slice applies that directly.
Future standalone/operator surfaces should treat shell, approval, and runtime-browser summaries as:
- **typed operating artifacts**, not dashboard filler,
- visibly linked back to workflow/runtime/coordination provenance,
- subordinate to manifests, role cards, runtime state, and audit records.

The dedicated follow-on document `Runtime-Shell-and-Command-Surface-Summary-Context-Application.md` now makes the shell-specific family explicit by separating:
- runtime shell summaries,
- command-contract summaries,
- command-availability summaries,
- runtime-status summaries,
- and doctor/health summaries.

That is how these surfaces align with ChaseOS as an operating system instead of drifting into generic productivity UI.

---

## 8. Service-Layer Boundary Rules

The standalone service layer for this slice should preserve the distinctions ChaseOS already relies on.

### Command surfaces do not grant new authority
A visible launcher or shell command list is not a permission bypass.
Execution still routes through manifests, role cards, AOR, approval rules, and Gate.

### Approval center is a governed decision surface
It may present pending approvals clearly, but it must not rewrite the approval chain or soften immutable audit requirements.

### Runtime browser is an inspection surface first
Showing runtime ceilings, role-card links, or summaries does not create ambient control over those runtimes.

### Session state remains runtime-local
Resume/reconnect context is useful operator state, but it is not canonical memory and not a replacement for logs or knowledge notes.

### FSOS surface state remains subordinate to governance
A live browser/terminal/desktop/filesystem status panel must still reflect scope ceilings, approval gates, and failure posture rather than presenting execution as uncontrolled autonomy.

### Summary mirrors remain visibly derivative
Operator-facing cards and queues should always be traceable to the runtime, workflow, event, approval, and audit sources underneath them.

---

## 9. Suggested Data Model Direction

This slice suggests ChaseOS likely needs at least these additional standalone object families:
- `operator_command_surface`
- `runtime_interaction_contract_view`
- `approval_queue_item`
- `runtime_browser_record`
- `runtime_session_record`
- `operator_surface_status_record`

And likely these specialized presentation layers:
- `runtime_shell_view`
- `approval_center_view`
- `runtime_browser_view`
- `live_operator_shell_view`
- `execution_route_inspector`

That matters because operator control in ChaseOS is not one generic dashboard.
It is the intersection of command ingress, governed execution, approval visibility, runtime identity, and typed summary routing.

---

## 10. What This Application Pass Proves

This pass proves the bridge can be extended from substrate docs into true operator-facing surfaces.
It clarifies:
- which docs become command/approval/runtime-browser nodes,
- how runtime shell, OSRIL, and FSOS should remain distinct but linked,
- how Approval Center and Agent/Runtime Browser emerge from already-existing Phase 9 substrate truth,
- and how operator-facing summaries should remain typed, governed OS artifacts instead of generic dashboard text.

This gives the bridge a fifth worked example and extends it from runtime/governance substrate mapping into human-operable control surfaces.

---

## 11. Alignment with the Overall ChaseOS Operating System

This pass aligns with ChaseOS as an operating system in four important ways.

### A. It preserves constitutional layering
ChaseOS remains layered:
- shell ingress proposes commands,
- workflow/role-card contracts define what may run,
- AOR executes,
- Gate governs writes and approvals,
- OSRIL exposes events/session visibility,
- logs preserve durable history.

This doc keeps those layers explicit instead of flattening them into one app-screen idea.

### B. It turns substrate work into operator legibility
The prior bridge slices established runtime posture, workflow identity, coordination state, and typed summary behavior.
This pass shows how those become a usable operator surface without losing their meanings.
That is a direct ChaseOS operating-system move: preserving system structure while making it navigable.

### C. It protects bounded autonomy
A future operator should be able to see what is runnable, what is blocked, what needs approval, what each runtime is doing, and what happened recently — without that visibility silently broadening runtime power.
That is core ChaseOS behavior: legible autonomy, not hidden autonomy.

### D. It keeps summaries aligned with action surfaces
Approval cards, runtime panels, shell session feeds, and runtime-browser summaries should all remain visibly tied to the governed system state beneath them.
That is how this work aligns with the wider ChaseOS model: not as a UI add-on, but as a faithful operator-facing expression of the OS.

---

## 12. Recommended Next Application Passes

After this slice, the strongest next bridge applications would be:
1. **provenance explorer / chronology browser surface mapping**
   - `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`
2. **summary taxonomy + object-model consolidation**
   - unify summary classes across runtime-state, workflow, coordination, and operator-shell surfaces
   - move toward a shared machine-readable summary-context schema
3. **core/personal split + export surfaces**
   - keep this as a long-horizon structural portability pass, not the immediate primary build lane

---

## 13. Current Verdict

A future ChaseOS standalone should not present runtime shell, approvals, and runtime browsers as generic app widgets.
It should present them as **typed operator control surfaces** with:
- explicit command-ingress meaning,
- explicit approval posture,
- explicit runtime identity and ceilings,
- explicit session/event visibility,
- and explicit linkage back to the governed machine state underneath.

That is how operator-facing control surfaces align with the overall ChaseOS operating system.

---

*Graph links: [[Markdown-to-Standalone-Bridge]] · [[ChaseOS-Runtime-Shell]] · [[Operator-Surface-Runtime-Interaction]] · [[Full-System-Operator-Surface]] · [[Browser-Operator-Surface-Operational-State]] · [[Standalone-Summary-Context-Layer]] · [[Runtime-Shell-and-Command-Surface-Summary-Context-Application]] · [[Summary-Context-Taxonomy-and-Object-Model]] · [[Workflow-Registry-and-Role-Cards-Standalone-Application]] · [[Runtime-Agent-Bus-and-Coordination-Standalone-Application]] · [[Provenance-Explorer-and-Chronology-Browser-Standalone-Application]] · [[Feature-Fit-Register]] · [[ChaseOS-Studio-Architecture]]*

*Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]] . [[ChaseOS-Approval-Center]]*
