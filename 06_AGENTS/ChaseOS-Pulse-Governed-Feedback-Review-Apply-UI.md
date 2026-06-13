# ChaseOS Pulse Governed Feedback Review/Apply UI

**Status:** SPEC / READY FOR BOUNDED IMPLEMENTATION  
**Created:** 2026-05-12  
**Runtime:** Hermes/Optimus  
**Phase:** Phase 10 Studio governed feedback surface  
**Scope:** Operator-facing review/apply UX over existing Pulse candidate, decision, and non-canonical apply contracts.

## Purpose

This document defines the next governed Phase 10 UI layer for Pulse feedback review and candidate application.

The goal is to move beyond persisted review-decision records and read-only queues into an operator surface that can show exactly what a reviewed Pulse candidate would do, which backend lane owns the effect, and whether the action is preview-only, approval-gated, or blocked.

This is not a new memory authority, not a Personal Map promotion shortcut, not a canonical writeback route, and not an ambient Studio mutation surface. It is a governed review/apply UX contract over existing Phase 9-and-below runtime surfaces.

## Current Repo Truth

Existing substrate:

| Surface | Current role | Authority posture |
|---|---|---|
| `runtime/pulse/feedback_review_queue.py` | Builds pending feedback review queue and in-memory feedback apply contracts. | Read-only / contract-only; no persisted decision and no effects. |
| `runtime/pulse/review_decision_log.py` | Persists operator review intent under `07_LOGS/Pulse-Decks/review-decisions/`. | Record-only; blocks feedback application, memory approval, Personal Map mutation, runtime-memory mutation, task creation, schedule activation, providers/connectors, and canonical writeback. |
| `runtime/pulse/candidate_inspector.py` | Aggregates feedback, Personal Map, execution repair, and review-decision lanes. | Read-only inspector; no effects and no second datastore. |
| `runtime/pulse/bus_review_contract.py` | Builds Agent Bus REVIEW task previews from inspector rows. | Non-mutating contract preview; no bus task write without later approval. |
| `runtime/pulse/candidate_apply.py` | Existing apply backend for approved review decisions. | The only current Pulse `candidate_apply_allowed=True` module; writes only to non-canonical runtime memory and an apply registry. Dry-run by default. |
| `runtime/studio/approval_center_app.py` | Localhost Approval Center readiness mount. | Read-only; no approval execution, review-decision writes, candidate apply, Agent Bus writes, memory approval, schedule activation, or canonical mutation. |
| `runtime/studio/approval_queue_panel.py` | Studio panel mount for existing static approval queue artifact. | Read-only; candidate apply UI not built. |
| `runtime/studio/desktop_shell_app.py` | Studio desktop shell composition. | Reports `candidate_apply_ui_built: false` and `applies_candidates: false`. |

Existing live apply backend effect boundaries:

| Candidate kind | Apply decision type | Backend write target | Canonical? | UI posture |
|---|---|---|---|---|
| `feedback` | `accept_for_future_ranking` | `runtime/memory/feedback-rules/accepted-signals.jsonl` | No | Can be previewed and, only with explicit approval, invoked through the existing apply command. |
| `personal_map` | `approve_for_future_apply` | `runtime/memory/personal-map/graph.json` | No | Can be previewed and, only with explicit approval, invoked through the existing apply command. Must never edit `00_HOME/Personal-Map.md` directly. |
| `execution_repair` | `approve_for_future_apply` | `runtime/memory/repair/<runtime_id>.json` through `runtime.memory.growth.record_repair_pattern(...)` | No | Can be previewed and, only with explicit approval, invoked through the existing apply command. |
| Any kind | Reject/defer/context/duplicate/revision decisions | No apply effect; follow-up signal only. | No | Display as recorded/reviewed, not executable. |

The apply registry is:

```text
07_LOGS/Pulse-Decks/apply-registry/applied-decisions.json
```

It prevents double-apply across runs. The UI must display registry status before offering any apply affordance.

## UX Contract

### Operator flow

1. **Inspect candidate**
   - Read from the unified inspector snapshot.
   - Show candidate kind, source log path, source deck/card refs, runtime refs, target ref, review decisions, and blocked effects.
   - No writes.

2. **Review decision state**
   - Show whether a persisted review decision exists.
   - Show decision type, reviewer, note, follow-up signals, and blocked effects from `review_decision_log.py`.
   - If no decision exists, the surface may show a disabled “record decision” placeholder only. It must not write a decision unless a separate review-decision write lane is approved.

3. **Apply preview**
   - For apply-family decisions only, run/represent the equivalent of:

     ```text
     chaseos pulse apply-decisions --kind <feedback|personal_map|execution_repair> --json
     ```

     without `--live`.
   - Display candidate ID, decision ID, target write path, skipped state, errors, and governance flags.
   - Preview must declare `canonical_writeback_allowed: false`, `mutates_canonical_state: false`, `creates_vault_notes: false`, `calls_provider_or_connector: false`, and `schedule_activation_allowed: false`.

4. **Approval gate**
   - The UI may show a disabled or gated “Apply approved decision” action only when all of these are true:
     - a persisted apply-family review decision exists;
     - the candidate exists and matches the decision kind;
     - dry-run preview resolves a non-canonical runtime-memory write target;
     - the decision ID is not already in the apply registry;
     - an explicit operator approval/evidence reference is present;
     - the action is scoped to one candidate kind or one candidate ID;
     - the UI can prove the action invokes the existing backend, not a new mutation path.

5. **Apply execution handoff**
   - Phase 10 UI must not auto-run live apply on page load, route change, or background refresh.
   - If implementation chooses to support live apply from Studio, it must be an explicit operator action that calls the existing CLI/backend equivalent with `--live` and records the output as evidence.
   - If the UI cannot consume a valid approval artifact, it must remain preview-only and route a backend blocker.

6. **Post-apply evidence**
   - After live apply, the UI must refresh by reading:
     - the apply registry;
     - the runtime-memory target written by the backend;
     - the original review decision;
     - the source candidate log.
   - The UI must label the result as non-canonical runtime memory, not Personal Map canonical truth, not project memory promotion, and not knowledge promotion.

## Allowed Effects

Allowed without additional backend authority:

- read candidate/review/apply preview state;
- render a local/localhost Studio surface;
- render static HTML or JSON under an approved Pulse/Studio artifact lane if the implementing task explicitly declares that write;
- display the existing dry-run apply preview;
- display the existing explicit live command as a gated handoff;
- read the apply registry;
- display non-canonical runtime-memory target paths.

Allowed only through the existing approved apply backend and explicit operator approval:

- append accepted feedback ranking signals to `runtime/memory/feedback-rules/accepted-signals.jsonl`;
- upsert approved Personal Map candidates into `runtime/memory/personal-map/graph.json`;
- record approved execution repair patterns under `runtime/memory/repair/<runtime_id>.json`;
- update `07_LOGS/Pulse-Decks/apply-registry/applied-decisions.json`.

## Blocked Effects

The UI must not:

- mutate source decks;
- write review decisions unless a separate review-decision write lane is approved;
- approve memory by itself;
- mutate `00_HOME/Personal-Map.md` or any canonical Personal Map note;
- write `02_KNOWLEDGE/`;
- promote canonical knowledge;
- create tasks, SOPs, or Agent Bus rows from the apply button;
- dispatch runtimes;
- activate schedules;
- call providers/connectors;
- update Runtime Navigation Maps;
- update Agent Identity Ledgers;
- expand permissions;
- create a second datastore;
- treat non-canonical runtime memory as ChaseOS canonical truth.

## Proposed Studio Surface Shape

Preferred bounded implementation path:

```text
runtime/studio/pulse_governed_feedback_review_apply_panel.py
runtime/studio/test_pulse_governed_feedback_review_apply_panel.py
```

The panel should build a JSON model with these top-level keys:

```text
surface
ok
panel
summary
candidate
review_decision
apply_preview
apply_registry
allowed_actions
authority
blocked_effects
possible_writes
routes
docs
```

Minimum panel truth:

```json
{
  "surface": "studio_pulse_governed_feedback_review_apply_panel",
  "panel": {
    "surface_route": "#pulse-feedback-review-apply",
    "panel_mode": "governed-review-apply-preview",
    "source_contracts": [
      "runtime.pulse.candidate_inspector.build_candidate_inspector_snapshot",
      "runtime.pulse.review_decision_log.load_review_decisions",
      "runtime.pulse.candidate_apply.apply_reviewed_candidates"
    ]
  },
  "authority": {
    "read_only_by_default": true,
    "dry_run_preview_only_by_default": true,
    "writes_review_decisions": false,
    "applies_candidates_without_operator_approval": false,
    "applies_candidates_via_new_backend": false,
    "canonical_writeback_allowed": false,
    "memory_approval_allowed": false,
    "agent_bus_task_write_allowed": false,
    "schedule_activation_allowed": false,
    "provider_or_connector_call_allowed": false
  }
}
```

### Action states

| UI action | Enabled when | Effect now | Backend owner |
|---|---|---|---|
| Inspect candidate | Candidate exists in inspector snapshot. | Read-only display. | `candidate_inspector.py` |
| Preview apply | Apply-family persisted review decision exists. | Dry-run preview only. | `candidate_apply.py` with `dry_run=True` |
| Apply approved decision | Valid operator approval evidence plus apply-family decision plus dry-run target plus not-yet-applied registry state. | Optional live backend invocation if explicitly implemented and approved. | `candidate_apply.py` with `dry_run=False` / `chaseos pulse apply-decisions --live` |
| Record decision | Not part of this surface unless separately approved. | Disabled/blocked placeholder. | Future review-decision write lane |
| Enqueue bus review | Not part of apply UI. | Route to Agent Bus approval/enqueue surface, not this button. | `bus_review_contract.py` plus approved enqueue lane |

## Acceptance Criteria For Implementation

A coding implementation of this spec should prove:

1. The panel reads candidate/review/apply state without creating or mutating source artifacts.
2. Dry-run apply preview is visible and never updates the apply registry.
3. Live apply is unavailable unless explicit operator approval evidence is supplied.
4. Any live apply path delegates to `runtime.pulse.candidate_apply.apply_reviewed_candidates(...)` rather than reimplementing write logic.
5. UI/model output keeps canonical safeguards visible:
   - `canonical_writeback_allowed: false`
   - `mutates_canonical_state: false`
   - `memory_approval_allowed: false`
   - `agent_bus_task_write_allowed: false`
   - `schedule_activation_allowed: false`
6. Personal Map apply is labeled as runtime-memory graph mutation only, not canonical Personal Map promotion.
7. Already-applied decisions are disabled through the apply registry.
8. Non-apply decisions show follow-up signals but no apply affordance.
9. Desktop shell readiness can expose `candidate_apply_ui_built: true` only after the bounded panel exists and focused tests pass.
10. The Approval Center/Queue surfaces continue to report no approval execution unless a separate approval-execution lane is implemented.

## Test Plan

Existing backend proof to preserve:

```text
PYTHONPATH=. uvx pytest runtime/pulse/test_candidate_apply.py -q
```

Recommended focused implementation tests:

```text
PYTHONPATH=. uvx pytest runtime/studio/test_pulse_governed_feedback_review_apply_panel.py -q
PYTHONPATH=. uvx pytest runtime/pulse/test_candidate_apply.py runtime/pulse/test_personal_map_review_apply.py -q
PYTHONPATH=. uvx pytest runtime/studio/test_approval_queue_panel.py runtime/studio/test_desktop_shell_app.py -q
```

Recommended broader regression after implementation:

```text
PYTHONPATH=. uvx pytest runtime/pulse runtime/studio -q
```

## Backend Blockers To Route If Live Apply UI Is Desired

If the implementing lane wants an actual Studio button that runs live apply, route these backend decisions before enabling it:

1. **Approval artifact contract:** exact field names for operator approval evidence consumed by Studio.
2. **Single-candidate apply scope:** backend support for applying one decision/candidate instead of broad kind-level live apply, or an explicit decision that kind-level apply is acceptable.
3. **Apply evidence write lane:** approved location for the UI to record live apply result evidence beyond the existing registry.
4. **Review-decision write lane:** whether recording a decision from the UI is authorized or must stay in a separate backend workflow.
5. **Runtime-memory promotion boundary:** explicit statement that runtime-memory writes remain non-canonical until a separate Gate promotion path exists.

Until those are settled, the safe Phase 10 deliverable is preview/readiness UI plus an operator command handoff, not an in-browser mutation button.

## OS Alignment

In the ChaseOS operating-system model, this surface is an operator cockpit over governed runtime substrates:

```text
Pulse candidate/review logs
  -> Studio review/apply panel
  -> dry-run apply preview
  -> explicit approval gate
  -> existing non-canonical runtime-memory apply backend
  -> later Gate/promotion lanes only if separately authorized
```

ChaseOS remains the authority layer. Studio displays and routes. Pulse supplies candidate/review signals. The apply backend writes only bounded runtime memory. Canonical truth promotion remains outside this Phase 10 UI unless a lower-phase Gate workflow explicitly grants it.

## Graph Links

[[ChaseOS-Pulse-Architecture]] · [[Pulse-Feedback-Policy]] · [[ChaseOS-Pulse-Review-Decision-Log-Policy]] · [[ChaseOS-Pulse-Unified-Candidate-Inspector-Policy]] · [[ChaseOS-Pulse-Personal-Map-Review-Apply-Surface]] · [[ChaseOS-Pulse-Studio-Approval-Center-Local-Mount]] · [[ChaseOS-Approval-Center]] · [[ChaseOS-Studio-Architecture]] · [[Agent-Activity-Index]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
