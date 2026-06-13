---
title: Runtime Support Loops Contract
status: implemented/proven — read-only Phase 10 support-loop contract and Studio panel mounted; no-write proof passed
version: 0.2
created: 2026-05-12
owner: Optimus
phase: Phase 10 surface over Phase 9/AOR/runtime-memory substrate
---

# Runtime Support Loops Contract

> Runtime Support Loops are advisory operator-support surfaces for QA verification, proactive suggestions, usage tracking, and execution-repair learning. They make runtime behavior easier to inspect and improve, but they do not approve actions, dispatch runtimes, mutate memory, upgrade agents, or write canonical knowledge.

---

## 1. Purpose

This contract records the implemented/proven Phase 10 Runtime Support Loops surface from OSRIL.

The goal is to connect existing ChaseOS substrates:
- `runtime/studio/runtime_intelligence_panels.py`
- `runtime/memory/scorecards/`
- `runtime/memory/repair/`
- `runtime/memory/nav/*/nav-map.json`
- ChaseOS Pulse readiness/product-shell surfaces
- AOR audit records, Agent Activity, and runtime quality docs

into a bounded read-only support-loop panel that is now implemented under `runtime/studio/runtime_support_loops.py`, exposed through `StudioAPI.get_runtime_support_loops_panel`, and mounted in the native panel registry as `runtime-support-loops`.

Runtime Support Loops answer four operator questions:
1. Did the runtime output satisfy the declared success criteria?
2. What next step is worth considering, and what evidence supports it?
3. Which workflows/runtimes are being used, accepted, blocked, or repeatedly corrected?
4. What repair pattern should be proposed for review after repeated failures?

---

## 2. Current Repo Truth Inventory

### Already present and usable as inputs

| Surface | Current role in support loops |
|---|---|
| `runtime/studio/runtime_intelligence_panels.py` | Read-only Studio panels for provenance, memory ledger, identity ledger, and runtime navigation. Already declares no memory writeback, no Agent Bus task writes, no runtime dispatch, no provider/connector calls, and no canonical mutation. |
| `runtime/memory/README.md` | Defines Layer C runtime memory (`scorecards`, `repair`, `nav`, identity ledgers) as advisory; defines Layer D task memory as task-scoped and non-durable unless governed promotion occurs. |
| `runtime/memory/scorecards/*.json` | Existing runtime scorecard records for runtime-quality/usage-derived posture. |
| `runtime/memory/repair/*.json` | Existing execution-repair memory records for failure-pattern visibility. |
| `runtime/memory/nav/*/nav-map.json` | Runtime navigation overlays: advisory route intelligence, not permission grants. |
| `runtime/pulse/README.md` | Pulse already frames deck generation, runtime-brain dashboards, review queues, approval queues, memory/runtime readiness, and product-shell surfaces as candidate/preview/read-only outputs with no autonomous mutation. |
| `06_AGENTS/Agent-Scorecards-and-Runtime-Quality-Surfaces-Standalone-Application.md` | Defines scorecards as factual runtime-performance memory, not autonomous governance levers. |
| `06_AGENTS/Operator-Surface-Runtime-Interaction.md` | Names Runtime Support Loops as a Phase 10 OSRIL subfeature and defines QA, suggestions, usage tracking, and learning/repair as governed outputs. |

### Implemented/proven repo truth

| Surface | Proven role in support loops |
|---|---|
| `runtime/studio/runtime_support_loops.py` | Read-only builder module for the aggregate contract, QA verification packet, proactive suggestion packet, usage metrics packet, repair candidate packet, and Studio panel payload. |
| `StudioAPI.get_runtime_support_loops_panel` | JSON-safe Studio API method that returns the support-loop panel as an inspectable envelope. |
| `runtime/studio/shell/panel_registry.py` | Native shell registry mounts `runtime-support-loops` as a read-only main panel with frontend target `panel-runtime-support-loops`. |
| `runtime/studio/test_runtime_support_loops.py` | Focused tests prove packet shape, advisory authority, blocked authority, and no mutation of source evidence while packet builders run. |
| `runtime/studio/shell/test_pass10a_shell.py` | Focused registry/API tests prove the panel is mounted and returned through the Studio shell. |
| Parent proof task `t_c6791bf1` | Reviewer smoke invoked `build_support_loop_contract`, all packet builders, `build_runtime_support_loops_panel`, and `StudioAPI.get_runtime_support_loops_panel` against watched paths and observed `changed_file_count: 0`. |

---

## 3. Loop Families

### A. QA Verification Loop

**Trigger:** A workflow/run/panel proof exists and declares success criteria or readiness expectations.

**Reads:** declared criteria, AOR/Agent Activity audit records, produced artifacts, Studio/Pulse readiness packets, test result references.

**Produces:** `qa_verification_packet`.

**Packet minimum fields:**
- `loop_id`
- `loop_family: qa_verification`
- `source_run_ref`
- `declared_success_criteria`
- `observed_evidence_refs`
- `missing_evidence`
- `discrepancies`
- `confidence`
- `operator_review_required`
- `allowed_next_actions`
- `blocked_authority`

**Allowed action:** inspect/report only.

**Forbidden:** fixing outputs, rerunning workflows, creating bus tasks, approving outputs, or writing canonical state.

### B. Proactive Suggestion Loop

**Trigger:** A support packet, Pulse card, runtime-quality signal, repeated blocker, or operator-facing readiness packet indicates a possible next step.

**Reads:** support packets, Pulse cards, scorecards, repair memory, nav overlays, build logs, readiness packets.

**Produces:** `proactive_suggestion_packet`.

**Packet minimum fields:**
- `suggestion_id`
- `source_refs`
- `recommendation_text`
- `why_now`
- `evidence_refs`
- `confidence`
- `approval_required: true`
- `suggested_route` (for example `operator_review`, `agent_bus_task_request`, or `defer`)
- `blocked_authority`

**Allowed action:** suggest only.

**Forbidden:** auto-executing the suggestion, creating tasks without a governed enqueue path, consuming approvals, writing memory, or dispatching runtimes.

### C. Usage Tracking Loop

**Trigger:** A workflow/run/support packet exists or a Studio/Pulse surface is inspected.

**Reads:** AOR audit records, Agent Activity records, scorecard records, approval/review decision records, Pulse deck/review metadata.

**Produces:** `usage_metrics_packet`.

**Packet minimum fields:**
- `metrics_id`
- `runtime_id`
- `workflow_id` or `surface_id`
- `time_window`
- `run_count`
- `success_count`
- `blocked_count`
- `approval_requested_count`
- `operator_acceptance_signal_count`
- `scorecard_refs`
- `coverage_notes`

**Allowed action:** summarize usage and point to evidence.

**Forbidden:** creating a second analytics datastore, mutating scorecards directly from Studio, altering runtime selection, or changing trust/permission posture.

### D. Learning / Execution Repair Loop

**Trigger:** Repeated failure, repeated correction, operator feedback, or QA discrepancy pattern.

**Reads:** `runtime/memory/repair/*.json`, Agent Activity, failure reports, correction history, scorecards.

**Produces:** `repair_candidate_packet`.

**Packet minimum fields:**
- `repair_candidate_id`
- `runtime_id`
- `failure_pattern`
- `evidence_refs`
- `proposed_repair_text`
- `risk_level`
- `review_required: true`
- `apply_allowed: false`
- `blocked_authority`

**Allowed action:** propose repair for review.

**Forbidden:** self-upgrading, patching skills, editing runtime memory, changing prompts/role cards/manifests, or applying repair memory without governed review.

---

## 4. Authority Boundary

Runtime Support Loops inherit the strictest boundary from the current Studio/Pulse runtime-intelligence surfaces:

| Capability | Support-loop v0.1 posture |
|---|---|
| Read existing artifacts | Allowed within declared source paths |
| Write preview/report artifacts | Future implementation task may add a bounded proof/report lane only |
| Approve actions | Not allowed |
| Consume approvals | Not allowed |
| Create Agent Bus tasks | Not allowed in v0.1; future only through governed enqueue/review path |
| Mutate runtime memory | Not allowed |
| Apply repair memory | Not allowed |
| Dispatch runtimes/workflows | Not allowed |
| Call providers/connectors | Not allowed |
| Modify role cards/manifests/trust tiers | Not allowed |
| Canonical writeback | Not allowed |
| Self-upgrade / autonomous learning | Not allowed |

Short rule: **support loops produce inspectable evidence and recommendations; they do not take action.**

---

## 5. Implemented Shape

### Runtime module

The read-only module now exists:

```text
runtime/studio/runtime_support_loops.py
```

Implemented builders:
- `build_support_loop_contract(vault_root)`
- `build_qa_verification_packet(vault_root, *, source_ref=None)`
- `build_proactive_suggestions_packet(vault_root, *, source_ref=None)`
- `build_usage_metrics_packet(vault_root, *, runtime_id=None, window=None)`
- `build_repair_candidate_packet(vault_root, *, runtime_id=None)`
- `build_runtime_support_loops_panel(vault_root)`

### Studio panel contract

The read-only panel is now mounted adjacent to runtime intelligence panels:

```text
surface: studio_runtime_support_loops_panel
native_panel.panel_id: runtime-support-loops
authority.read_only: true
possible_writes: []
allowed_actions:
  - inspect-runtime-support-loops-panel
```

### Optional proof/report output lane

No separate Runtime Support Loops report lane was needed for the first implementation. Proof is currently carried by focused tests, parent proof-task metadata, and the build-log record. If a future implementation needs durable proof artifacts, use a report-only lane such as:

```text
07_LOGS/Runtime-Support-Loops/
```

This lane would be for QA/support-loop proof reports only. It would not be memory, not Agent Bus, not approval execution, and not canonical knowledge.

---

## 6. Audit and Evidence Records

Support-loop packets should reference existing evidence instead of duplicating it.

Primary evidence refs:
- AOR audit record path
- Agent Activity record path
- Studio/Pulse readiness packet path
- scorecard record path
- repair-memory record path
- runtime navigation map path
- build log path
- QA screenshot/proof path when present

Every support-loop packet should include:

```yaml
authority:
  advisory_only: true
  operator_approval_required_for_action: true
  writes_memory: false
  writes_agent_bus_tasks: false
  executes_workflows: false
  dispatches_runtimes: false
  canonical_mutation_allowed: false
```

---

## 7. First Implementation / Proof Result

The first implementation/proof pass satisfied these criteria:

1. A read-only runtime support loops builder exists under `runtime/studio/` as `runtime/studio/runtime_support_loops.py`.
2. The builder inventories QA verification, proactive suggestion, usage tracking, and repair candidate loop families.
3. The returned contract includes explicit `authority` and `blocked_authority` fields.
4. Proactive suggestions are marked advisory-only and `approval_required: true`.
5. Usage metrics read existing scorecard/audit-style evidence and do not create a new datastore.
6. Repair candidates are surfaced as review-needed proposals and cannot be applied.
7. The panel contract exposes `possible_writes: []` and no runtime dispatch/provider/connector authority.
8. Focused tests prove the no-write/no-dispatch/no-memory-mutation posture.
9. A QA/proof worker validated the output shape and no-write boundary from live repo truth.
10. Any broader writes or activation remain routed to lower Phase 9-and-below contracts.

Proof commands recorded by parent task `t_c6791bf1`:
- `python3 -m py_compile runtime/studio/runtime_support_loops.py runtime/studio/shell/api.py runtime/studio/shell/panel_registry.py` — pass.
- `PYTHONPATH=. uvx --with pytest --with pyyaml pytest -q runtime/studio/test_runtime_support_loops.py` — `2 passed`.
- `PYTHONPATH=. uvx --with pytest --with pyyaml pytest -q runtime/studio/shell/test_pass10a_shell.py::TestAPIEnvelopes::test_get_runtime_intelligence_panels_return_read_only_envelopes runtime/studio/shell/test_pass10a_shell.py::TestNativePanelRegistry::test_registry_shape_and_mounts runtime/studio/shell/test_pass10a_shell.py::TestNativePanelRegistry::test_registry_is_read_only_and_blocks_authority` — `3 passed`.
- `PYTHONPATH=. uvx --with pytest --with pyyaml pytest -q runtime/studio/test_qa_runner.py::test_runtime_intelligence_static_runner_validates_panels_without_server_or_writeback runtime/studio/shell/test_pass10w_runtime_memory_inspector.py::TestPanelRegistry::test_possible_writes_empty runtime/studio/shell/test_pass10w_runtime_memory_inspector.py::TestRuntimeMemoryAPI::test_runtime_list_returns_registered_runtimes` — `3 passed`.
- `PYTHONPATH=. uvx --with pytest --with pyyaml pytest --collect-only -q runtime/studio/test_qa_runner.py runtime/studio/shell/test_pass10w_runtime_memory_inspector.py` — `82 tests collected`.
- Live no-write snapshot smoke invoked the support-loop contract, all packet builders, the panel builder, and Studio API against watched paths `runtime/memory`, `runtime/agent_bus`, and `06_AGENTS/Runtime-Support-Loops-Contract.md`; result: `changed_file_count: 0`.

---

## 8. Implementation / Proof Task Status

The original task split is now closed through proof:

1. **Implementation task:** complete — read-only contract/panel builder and focused tests exist.
2. **Proof/review task:** complete — packet shape, no-write posture, mounted panel truth, and static boundary review passed from live repo truth.
3. **Documentation sync task:** complete for current proof — this contract and adjacent OSRIL/Studio/register/routing surfaces now reflect the implemented/proven read-only support-loop panel.

Remaining future work is not activation. Any move from advisory packets to write-capable report generation, queueing, approval consumption, dispatch, memory mutation, repair application, or canonical writeback would require a separate lower-phase contract, Gate path, tests, and review.

---

## 9. ChaseOS OS Alignment

Runtime Support Loops strengthen ChaseOS as an operating system because they make the OS self-observing without making it self-authorizing.

They connect runtime history, scorecards, repairs, Pulse cards, Studio panels, and QA evidence into operator-visible loops. That gives Hermes/OpenClaw/other runtime-instance summaries practical payoff: the operator can see what worked, what failed, what is worth considering next, and where repeated repair patterns exist.

But the support loops stay subordinate to ChaseOS governance:
- suggestions are not approvals,
- QA reports are not automatic fixes,
- usage metrics are not permission changes,
- repair candidates are not self-upgrades,
- and all writeback/dispatch/approval consumption remains behind governed Phase 9-and-below paths.

---

## 10. Current Verdict

Runtime Support Loops are now an implemented/proven read-only Phase 10 Studio surface over existing Phase 9/runtime-memory/Pulse/Studio truth.

They are testable now as contract/panel outputs through `runtime/studio/runtime_support_loops.py`, `StudioAPI.get_runtime_support_loops_panel`, and the mounted `runtime-support-loops` native panel. They are still not autonomous runtime behavior: suggestions do not execute, QA packets do not fix outputs, usage metrics do not create a second datastore or alter runtime selection, repair candidates do not self-apply, and no support-loop path approves actions, consumes approvals, creates Agent Bus tasks, dispatches runtimes, mutates memory, calls providers/connectors, self-upgrades, or writes canonical state.

---

*Graph links: [[Operator-Surface-Runtime-Interaction]] · [[Agent-Scorecards-and-Runtime-Quality-Surfaces-Standalone-Application]] · [[Execution-Repair-and-Failure-Recovery-Surfaces-Standalone-Application]] · [[Memory-Inspector-and-Runtime-Memory-Surfaces-Standalone-Application]] · [[ChaseOS-Pulse-Architecture]] · [[ChaseOS-Studio-Architecture]] · [[Runtime-Navigation-Map]] · [[Agent-Activity-Index]]*

*Runtime-Support-Loops-Contract.md — v0.2 | Created: 2026-05-12 | Updated: 2026-05-13 (implementation/proof truth-sync: read-only support-loop module, Studio API/panel registry mount, focused tests, and live no-write snapshot proof recorded) | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
