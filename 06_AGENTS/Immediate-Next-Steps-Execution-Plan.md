---
title: Immediate Next Steps Execution Plan
type: implementation-plan
status: active
version: 0.1
created: 2026-04-26
updated: 2026-04-26
owner: Optimus
phase: Phase 9
---

# Immediate Next Steps Execution Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Finish the highest-leverage remaining Phase 9 platform-closure work now that coordination policy, UTC/time cleanup, runtime registry substrate, and coordination-watch surfaces are already real.

**Architecture:** Prioritize the operating-system control spine first: runtime identity/onboarding, policy binding, operator shell inventory/config, then event/session visibility. Defer wider gateway breadth and further feature-R&D until those core OS surfaces are explicit and machine-readable.

**Tech Stack:** Python stdlib, `runtime/aor/`, `runtime/cli/main.py`, top-level `chaseos.py`, markdown truth docs under `06_AGENTS/`, pytest, repo-local `.venv/Scripts/python.exe`.

---

## Current Repo Truth Snapshot (2026-04-26)

Already real on disk:
- AOR pipeline and first-wave bounded workflows
- runtime-instance promotion draft/readiness substrate
- agent bus + router + claimed-task lifecycle
- promoted `chaseos gate check-coordination ...`
- `chaseos run ...` preflight for declared coordination-sensitive workflows
- runtime registry substrate under `runtime/aor/runtime_registry/`
- `chaseos agent list/register/status/lifecycle`
- runtime-local policy-binding records for Hermes/OpenClaw plus fail-closed `execution-capable` gating
- runtime coordination-watch lifecycle + CLI footholds
- provenance validator + `trace_idea`
- UTC cleanup + explicit local-time semantics for operator-local chronology utilities

Strongest remaining gaps after this cleanup sequence:
1. Discord-origin multi-lane runtime coordination closure
   - channel-aware bus arbitration
   - lane/thread-aware claim scope
   - work fingerprinting / dedupe
   - real Hermes coordination-watch activation visible from operator-owned terminals
2. later Phase 9 closure surfaces (FSOS, runtime-memory consolidation, multi-repo enforcement) once the coordination/event spine is stronger

---

## Priority Order

### Priority 1 — Agent Onboarding Surface *(completed 2026-04-26)*
Build the missing operator-facing layer above the runtime registry. This layer is now live through `chaseos agent list/register/status/lifecycle`.

**Why now:** The registry substrate exists, but ChaseOS still lacks the canonical commands for registering, inspecting, and reviewing runtime lifecycle/policy state as an OS-owned surface.

**Deliverables:**
- `chaseos agent register`
- `chaseos agent status`
- `chaseos agent lifecycle`
- focused CLI + registry tests

### Priority 2 — Runtime Policy Binding *(completed 2026-04-26)*
Make registration subordinate to explicit policy binding, not ambient assumptions. This substrate is now live through runtime-local binding records plus fail-closed `execution-capable` lifecycle gating.

**Why now:** Runtime identity without policy binding is descriptive, not enforceable. This is the missing bridge between runtime existence and constitutional authority.

**Deliverables:**
- `runtime/aor/policy_binding.py`
- policy binding records per runtime
- fail-closed tests for missing/invalid bindings

### Priority 3 — Runtime Shell Inventory + Config *(provider/model + config complete 2026-04-26)*
Finish the operator-facing shell footing that should sit above Phase 9 runtime infrastructure. The provider/model inventory layer and the first bounded config layer are now both live.

**Why now:** Too much usable runtime capability was buried in internal modules and partial CLI seams; this priority is now materially cleared enough to hand off to scaffold generation.

**Deliverables:**
- provider/model registry
- `chaseos models list`
- `chaseos providers status`
- bounded config store
- `chaseos config set/list`

### Priority 4 — Channel-Aware Coordination Closure *(new highest-impact live priority — 2026-04-26)*
Close the gap between Discord lane-aware ingress and runtime-only bus arbitration.

**Why now:** ChaseOS now uses multiple Discord ingress contexts for the same runtime (`hermes-chat`, threads under `hermes-chat`, and `chaseos-ops`), but the current bus still models ownership primarily at the runtime name level. That is too coarse to prevent duplicate Hermes work. Before further shell/product work, the coordination substrate must become lane/thread-aware and visibly live from operator-owned terminals.

**Deliverables:**
- ingress-aware bus task identity
- lane/thread-aware claim scope
- work fingerprinting / dedupe
- Discord-origin coordination-sensitive requests translated into structured bus state before machine work continues
- real Hermes coordination-watch activation/state visible from operator terminals

### Priority 5 — OSRIL Event / Session Contract *(completed runtime foothold 2026-04-26)*
Build the event-out visibility layer above AOR. The first bounded implementation is now live through `runtime/osril/` plus normalized AOR outcome emission into runtime-local event/session records.

**Why now:** Once the coordination substrate is fixed, ChaseOS still needs the machine-readable event/session layer that routes execution state out.

**Deliverables:**
- OSRIL contract schema / session footing
- normalized event types
- AOR event emission tests

---

## Ordered Task Program

## Task 1: Expose runtime registry through `chaseos agent ...`

**Objective:** Turn the existing runtime registry substrate into a real operator-facing command family.

**Files:**
- Modify: `runtime/cli/main.py`
- Modify: `runtime/cli.py`
- Modify: `chaseos.py`
- Test: `runtime/tests/test_agent_cli.py`
- Read first: `runtime/aor/runtime_registry.py`

**Verification:**
- `.venv/Scripts/python.exe chaseos.py agent status`
- `.venv/Scripts/python.exe chaseos.py agent lifecycle hermes`
- focused pytest for parser/dispatch/registry read behavior

---

## Task 2: Add registration write path with fail-closed validation

**Objective:** Support bounded registration writes without implying execution authority.

**Files:**
- Modify: `runtime/aor/runtime_registry.py`
- Modify: `runtime/cli/main.py`
- Test: `runtime/aor/test_runtime_registry.py`
- Test: `runtime/tests/test_agent_cli.py`

**Verification:**
- invalid registration payloads fail closed
- registration records write only into declared registry surfaces
- registration does not itself grant runnable workflow breadth

---

## Task 3: Build policy-binding layer

**Objective:** Make runtime registration subordinate to explicit policy-binding truth.

**Files:**
- Create: `runtime/aor/policy_binding.py`
- Create: `runtime/aor/runtime_registry/hermes/policy_binding.yaml`
- Create: `runtime/aor/runtime_registry/openclaw/policy_binding.yaml`
- Test: `runtime/aor/test_policy_binding.py`

**Verification:**
- missing binding => fail closed
- malformed binding => fail closed
- registration + binding remain separate concepts

---

## Task 4: Add provider/model registry *(completed 2026-04-26)*

**Objective:** Finish the first real Runtime Shell inventory surface. The underlying registry module already existed, and the missing shell-wiring/verification layer is now live through `chaseos providers list|status` and `chaseos models list`.

**Files:**
- Create: `runtime/providers/registry.py`
- Modify: `runtime/cli/main.py`
- Test: `runtime/tests/test_provider_model_registry.py`
- Truth-sync later: `06_AGENTS/ChaseOS-CLI-Surface-Architecture.md`

**Verification:**
- `.venv/Scripts/python.exe -m pytest runtime/tests/test_provider_model_registry.py -q`
- provider listing works
- malformed provider entries fail clearly

---

## Task 5: Add bounded config store surface *(completed 2026-04-26)*

**Objective:** Give Phase 9 a governed operator config layer. The first implementation is now live through `runtime/config/store.py` plus `chaseos config list|set`, with `.chaseos/config.yaml` seeded on demand and unknown keys rejected fail-closed.

**Files:**
- Create: `runtime/config/store.py`
- Modify: `runtime/cli/main.py`
- Test: `runtime/tests/test_config_store.py`

**Verification:**
- set/list config values
- config stays subordinate to Gate and manifest policy
- no config write path mutates protected/canonical surfaces silently

---

## Task 6: Add scaffold generator foothold *(completed 2026-04-26)*

**Objective:** Seed bounded scaffolding for future runtime/workflow surfaces. The first implementation is now live through `runtime/scaffold/generator.py` plus promoted `chaseos scaffold project|workspace`, generating draft-only artifacts under `runtime/scaffold/generated/` rather than mutating canonical surfaces directly.

**Files:**
- Create: `runtime/scaffold/__init__.py`
- Create: `runtime/scaffold/generator.py`
- Modify: `runtime/cli/main.py`
- Test: `runtime/tests/test_scaffold_generator.py`

**Verification:**
- generated artifacts remain draft-only
- scaffold output stays in allowed operator-safe surfaces
- no canonical/promotion authority implied

---

## Task 7: Build OSRIL contract substrate *(completed 2026-04-26)*

**Objective:** Define the first machine-readable runtime interaction/event contract. This is now live through `runtime/osril/contract.py` + `runtime/osril/session.py`, with explicit event validation and runtime-local session snapshots.

**Files:**
- Create: `runtime/osril/contract.py`
- Create: `runtime/osril/session.py`
- Test: `runtime/tests/test_osril_contract.py`

**Verification:**
- event payloads validate
- session shape is explicit
- approval-required / task-started / task-complete event families exist

---

## Task 8: Emit normalized AOR events into OSRIL *(completed 2026-04-26)*

**Objective:** Make the contract real by routing bounded execution events out of AOR. The first normalized emission layer is now live for run-level `status`, `task_started`, `task_complete`, and `task_failed` events.

**Files:**
- Modify: `runtime/aor/engine.py`
- Test: `runtime/tests/test_aor_osril_events.py`

**Verification:**
- success / escalation / failure emit normalized events
- audit trail still survives all paths
- event emission does not widen permissions

---

## Execution Rules

1. **Use strict TDD** for each new command/substrate.
2. **Keep each pass narrow** — one substrate seam at a time.
3. **Run focused tests first**, then broader `runtime/aor` / adjacent suites.
4. **Truth-sync docs and indexes after each pass**.
5. **Do not confuse registration with authority** — all onboarding surfaces remain subordinate to manifests, role cards, Gate, and policy binding.

---

## Verification Ladder

For each future pass in this plan:
1. focused test slice for the new seam
2. parser/CLI smoke if command surface changed
3. `py_compile` on changed Python files
4. adjacent subsystem suite
5. broader `runtime/aor -q` when the pass touches shared runtime substrate

---

## Why This Matters to ChaseOS
This plan finishes the missing control spine that turns ChaseOS from “a repo with many runtime parts” into a more complete operating system:
- runtime identity becomes operator-visible
- policy binding becomes machine-readable
- shell inventory/config become real
- events/sessions become explicit
- future expansion sits on top of governed substrate instead of ad hoc seams

---

## Next-Step Commitments
Unless repo truth changes materially, the next things I should do in order are:
1. build OSRIL contract + AOR event emission
2. continue broader runtime-shell completion only after that shell/event spine is in place
3. then move into later Phase 9 closure surfaces by OS leverage

*Optimus note: this is the post-cleanup execution order that gives ChaseOS the most OS leverage next, rather than drifting into lower-priority feature work before the control spine is finished.*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
