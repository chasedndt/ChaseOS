---
title: Phase 9 Implementation Closure Plan
type: implementation-plan
status: seeded — active execution ordering plan
version: 0.2
created: 2026-04-25
updated: 2026-04-29
owner: Optimus
phase: Phase 9
---

# Phase 9 Implementation Closure Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Clear the remaining high-impact Phase 9 implementation backlog in the right dependency order so ChaseOS finishes its runtime/operator substrate before shifting attention to later feature-R&D surfaces.

**Architecture:** Prioritize the machine-readable runtime-governance spine first, then the operator command surface, then the event/session visibility layer, then the higher-risk operator-surface execution substrates. Do not jump ahead to Phase 10 product-shell work or abstract feature-R&D expansions until their Phase 9 prerequisites are actually built.

**Tech Stack:** Python stdlib, existing `runtime/` package structure, AOR engine + registry + role cards + task router, repo-local CLI under `runtime/cli/main.py`, markdown architecture docs under `06_AGENTS/`, pytest for focused and broader verification.

---

## Current Repo Truth Snapshot (2026-04-28)

**Implementation progress inside this plan:**

2026-04-27 update:
- Discord-origin multi-lane arbitration is now materially closed at the public bus API and SQLite backend mutation boundary.
- Tasks now persist `owner_instance` for Hermes/OpenClaw thread ownership.
- Shared runtime/control channel work such as Discord `chaseos-ops` now derives channel-scoped ownership as `discord-channel-{source_channel_id}`, while OpenClaw/Hermes thread work remains `discord-thread-{source_thread_id}`.
- Coordination-watch activation proof now has a read-only `activation-report` operator surface that aggregates install status, scheduler query, supervisor state, heartbeat freshness, success records, and reboot-verification evidence. Live host registration/reboot proof is still not complete on this machine.
- OSRIL contract substrate, vault-local event dispatch footholds, operator-facing `chaseos osril sessions|show|events` inspection, and immutable `chaseos osril approvals|respond` approval-response records now exist. Approval responses now also write immutable application markers and `approval_response` session events; AOR now enforces bounded `approval_gate` resume for `operator-explicit` manifests with one-time resume markers. Long-lived executor/surface resume remains future.
- Gate policy expansion now covers bounded browser operator open/inspect/screenshot as explicit `browser.navigation` external-API operations, `agent register` / lifecycle-transition runtime registry writes, coordination-watch lifecycle/bootstrap side-effect surfaces bound to `runtime_lifecycle_state`, `host.process`, and `host.scheduler`, and existing event/MCP AOR dispatch seams through `gateway.workflow.dispatch` and `gateway.workflow.invoke_bounded`. Future concrete Gateway/Studio UI surfaces and browser actions beyond bounded read/screenshot remain Gate expansion targets.
- Agent Identity Ledger formal-file foothold is complete for the Phase 9 DoD: `runtime/memory/adapters/claude/identity-ledger.json`, `_identity_ledger_schema.json`, and `06_AGENTS/Claude-Identity-Ledger.md` exist; Hermes/OpenClaw seeded ledger files are also present as peer runtime-instance lanes; memory inspector surfaces all three as advisory Layer C memory.
- Runtime-memory consolidation update: `chaseos memory summary` now consolidates Layer C/D validation, runtime-family coverage, active task-context counts, governance flags, attention items, and next actions across profiles, identity ledgers, nav maps, scorecards, repair memory, and task-local memory without mutating or granting authority.

2026-04-28 update:
- Coordination-watch activation-report now distinguishes live liveness readiness from full activation proof. `activation_state: proven` now requires scheduler registration, running supervisor, fresh heartbeat, success-state evidence, and reboot-verification evidence together; current live Hermes/OpenClaw reports remain `partial` because host startup registration and reboot-verification proof are still absent.
- SBP delivery external side effects are now explicitly bound to Gate operations. Discord webhook delivery checks `sbp.delivery.discord.webhook_send` / `delivery.discord_webhook` and Whop post delivery checks `sbp.delivery.whop.post` / `delivery.whop_api` before network writes.
- Priority 1 / Task 1 complete — Runtime Registry substrate now exists under `runtime/aor/runtime_registry/` with loader, focused tests, and seeded Hermes/OpenClaw entries
- Priority 1 / Task 2 complete — `chaseos agent list/register/status/lifecycle` now exists as the first operator-facing onboarding command family on top of the runtime registry substrate
- Priority 1 / Task 3 complete — runtime policy-binding records now exist for Hermes/OpenClaw, registry entries track `policy_binding_record`, and `execution-capable` lifecycle now fails closed without completed binding
- Provider/model registry + health polish update: `chaseos runtime provider-status` now includes a read-only `readiness_summary` with ready/degraded/blocked posture, provider/runtime counts, queue health counts, and degradation reasons for Phase 10 Settings/Studio wrapping.
- Priority 2 / Task 5 complete — bounded config store now exists through `runtime/config/store.py` plus `chaseos config list/set`, with `.chaseos/config.yaml` seeded on demand and config keys kept subordinate to Gate/governance constraints
- Priority 2 / Task 6 complete — scaffold generator foothold now exists through `runtime/scaffold/generator.py` plus promoted `chaseos scaffold project/workspace`, generating draft-only artifacts under `runtime/scaffold/generated/`
- Coordination closure override resolved — Discord-origin multi-lane runtime coordination is now materially hardened enough that the highest-impact immediate gap has shifted to selected Phase 9 feature/hardening work outside OSRIL, with long-lived OSRIL live-surface UX deferred to Phase 10+.
- Priority 3 / Task 7 complete — OSRIL contract/session substrate now exists with read-only CLI inspection via `chaseos osril sessions|show|events`
- Gateway/Studio policy preflight complete — existing event-triggered AOR dispatch and Runtime MCP `workflow.invoke_bounded` now check named Gate operations before invoking AOR, and SBP Discord/Whop delivery adapters now check named external delivery operations before HTTP writes. Studio remains Phase 10 docs-only; this pass did not build a UI or HTTP gateway.
- OSRIL wait/resume surface complete — `runtime/osril/wait_resume.py` and `chaseos osril wait-resume` now expose a read-only approval wait/resume queue with pending, approved-ready, denied, resumed, unapplied, and missing states plus bounded polling for a specific approval id.
- OSRIL one-shot resume hardening complete — `runtime/osril/resume_ready.py` and `chaseos osril resume-ready` now scan approved-ready OSRIL items and hand them back through AOR's existing `operator_approval_ref` path after the `osril.approval_resume` Gate operation allows the resume write surfaces.
- OSRIL Phase 9 feature closeout complete — `06_AGENTS/OSRIL-Phase9-Closeout.md` now records Phase 9 OSRIL as COMPLETE / VERIFIED for runtime-side scope. Long-lived continuation UX beyond the one-shot runner, reconnect transport, live operator shell, voice/visual/companion surfaces, and richer per-tool streaming are moved to Phase 10+ unless explicitly reopened as Phase 9.x hardening.
- Coordination-watch activation hardening update — `activation-checklist` now exists as a read-only operator runbook above `activation-report`, exposing current step, ready commands, host/elevation-required actions, missing evidence, and proof paths for Hermes/OpenClaw without mutating scheduler, supervisor, or lifecycle state. Live host startup registration and reboot-verification proof remain unverified on this machine.
- Runtime config/settings polish update — `chaseos config summary` now exists as a read-only Settings/Studio-ready summary over bounded config validation, provider setup readiness, runtime defaults, attention items, next actions, and explicit governance boundaries. It does not seed missing config files, switch providers, mutate lifecycle state, or expand Gate authority.
- Multi-repo/multi-directory enforcement update — AOR now has a shared path policy module, manifest/role-card validation for vault-relative executable paths, Stage 5 required-read containment, Stage 7 handler writeback traversal blocking, and fail-closed `repo_scope` semantics. Current implementation is vault-root-only; cross-repo declarations require `policy_ref` / `policy_path` and extra directories remain non-executable until a future evaluator is built.
- Hermes/OpenClaw workflow breadth update — Hermes watch now dispatches bounded `planning`, `shadow-audit`, and `developer-co-development` coordination-bus packets in addition to review. Hermes governance now validates the exact approved workflow set: `hermes_operator_today_shadow`, `hermes_review_execute`, and `hermes_watch`. Discord-triggered Hermes execution remains shadow-only; shell, connector, credential, browser, delivery, canonical, and protected-write authority remain blocked. OpenClaw `source-pack-builder` watch dispatch now exists through a declared JSON input envelope (`source_pack_inputs_path` or `source_pack_inputs_json`) that feeds the existing bounded `source_pack_builder` workflow; it does not add live connector, browser, delivery, canonical, or credential authority.

2026-04-29 update:
- Coordination-watch activation proof verifier hardening — generated reboot-verification scripts now require a zero `schtasks` query exit code plus expected task-name evidence before marking scheduler registration observed; activation-report success and reboot evidence now validates runtime/task identity and scheduler proof before allowing `proof_complete`. Live Hermes/OpenClaw reports remain `partial` because host scheduler registration and reboot-result evidence are still absent.


2026-04-29 continuation update:
- Coordination-watch activation proof handoff is PARTIAL / VERIFIED TARGETED. Repo-local bootstrap launchers, registration artifacts, elevated Task Scheduler handoff bundles, and reboot-verification bundles now exist for both OpenClaw and Hermes. Current-session supervisors are running and fresh bus heartbeats were verified. Full activation proof is still blocked by host elevation and future reboot/logon evidence: scheduler registration returned `Access is denied` from the current non-admin shell, no success record can be confirmed until scheduler registration exists, and no post-reboot verification result exists yet.
- Supervisor status hardening is complete for this gap: `runtime/lifecycle/coordination_watch_supervisor.py` now falls back from restricted `tasklist` output to Windows process API / PowerShell PID checks so activation reports do not under-report live supervised loops when `tasklist` is denied.
- Phase 10A0 live-proof handover is now explicit: `06_AGENTS/Phase10A0-Live-Proof-Test-Handover.md` records that coordination-watch activation proof does not require real source files but does require real host-state proof, while reviewed research-pack SBP verification does require real local source files. The recommended next UI foothold is `phase10a0-studio-acquisition-intake-cockpit`, a local-only wrapper around existing Phase 9 acquisition commands.

2026-04-29 host-registration update:
- Coordination-watch host startup registration is now LIVE-AWAITING-REBOOT-PROOF / VERIFIED TARGETED for both OpenClaw and Hermes. The generated UAC handoff scripts created `ChaseOS-OpenClaw-Coordination-Watch` and `ChaseOS-Hermes-Coordination-Watch` in Windows Task Scheduler; elevated/outside-sandbox `verify`, `capture-success`, `activation-report`, and `activation-checklist` runs now confirm scheduler registration, supervisor state/log evidence, fresh heartbeats, and success records for both runtimes.
- Full coordination-watch activation proof is still not complete. The only remaining evidence gap is `reboot_verification_observed`: after a real reboot/logon cycle, run the generated `*-coordination-watch-reboot-verify.ps1` scripts and then reconcile the results before marking `proof_complete`.


2026-04-29 final interface-planning update:
- Phase 10 can begin planning/building because the relevant Phase 9 runtime-side footholds exist: OSRIL wait/resume and resume-ready, provider-status/config validation/summary, Agent Bus inspection, memory/identity read surfaces, provenance/trace substrate, graph substrate, acquisition/SBP live-file CLI workflow, and coordination-watch host registration awaiting reboot proof.
- If the Studio desktop/product shell is not available yet, remaining useful work should stay backend/UI-ready: read-only smokes, bounded Agent Bus inspection, provider/config posture checks, coordination-watch proof reconciliation, and reviewed research-pack SBP verification with real files. Do not widen runtime authority just to compensate for missing UI.
- Phase 10 interface lanes that must be considered by the UI runtime: Settings/provider/config UI, [[ChaseOS-Approval-Center|Approval Center]] over OSRIL wait-resume/resume-ready, Runtime Cockpit over Agent Bus/provider/lifecycle health, Provenance Explorer, Memory/Agent Identity Ledger UI, graph/node UI, voice/visual/companion ingress surfaces, and reconnect/history/operator-shell continuation UX.

2026-04-28 R&D workbook closeout sync update:
- The stale 2026-04-15 workbook posture has been reconciled in `99_ARCHIVE/Reporting/ChaseOS_RnD_Update_Report_2026-04-28.md`.
- Phase 9 is not globally closed. Runtime Shell, OSRIL, SBP, Acquisition/Normalization, Agent Bus, Agent Memory/Identity, Runtime MCP, n8n proof, and Gateway/Studio policy preflight all have live repo footholds, while selected Phase 9 feature implementation and hardening can still continue.
- OSRIL is no longer a Phase 9 blocker by current closeout boundary. Its Phase 9 runtime-side substrate is complete; one-shot approved resume is now available, while long-lived executor/surface continuation semantics beyond that runner are Phase 10+ continuation work unless intentionally reopened as Phase 9.x hardening.
- Hardening/activation still open: coordination-watch post-reboot/logon proof and reviewed research-pack SBP verification with real local files. Final config/settings polish is materially closed at the Phase 9 CLI substrate layer: `chaseos config validate` is live/read-only/secret-aware and `chaseos config summary` now composes config/provider/runtime posture for Settings/Studio without mutation or authority expansion, so remaining Settings/Studio work is primarily Phase 10 presentation/wiring rather than missing Phase 9 config visibility substrate.
- Explicit deferred non-blockers: live n8n deployment/token/workflow, multi-repo enforcement, `runtime/audit/` migration, Core/Personal export completion.

Already materially built inside Phase 9:
- AOR 8-stage pipeline
- first-wave bounded workflows (`operator_today`, `operator_close_day`, `graph_hygiene`, `graduate_ideas`)
- runtime-instance promotion draft/readiness substrate for Hermes + OpenClaw
- Provenance Schema foothold
- Context Governance Layer
- Agent Scorecards
- `trace_idea`
- `drift_scan`
- dual-runtime agent bus substrate
- runtime state / lifecycle health / top-level `chaseos.py` footholds

**Strongest remaining implementation gaps inside Phase 9:**
1. Selected Phase 9 feature/hardening work outside OSRIL: continue implementing concrete remaining slices instead of treating Phase 9 as globally frozen.
2. Coordination-watch activation proof: host startup registration and live liveness/success evidence are now verified for OpenClaw and Hermes through the generated UAC handoff and success-capture path. Full proof still requires post-reboot/logon verification and reconcile before `proof_complete` can be claimed. This proof needs real host state, not real research/source files.
3. Reviewed research-pack SBP verification: local/import readiness, preview, reviewed promotion, and read-only SBP adapter verification exist, but final live proof still needs real operator-supplied local files for the recommended source classes. Phase 10A0 should make this workflow testable without manual folder scavenging.
4. Provider/model registry + expanded health/config polish for Phase 10 Settings/Studio wrapping is materially closed at the Phase 9 CLI substrate layer: provider readiness summary is live, `chaseos config validate` verifies bounded non-secret config posture without mutation, and `chaseos config summary` exposes a Settings-ready config/provider/runtime posture payload. Remaining work is Phase 10 Settings presentation/wiring and live operator UX, not missing Phase 9 provider/config visibility.
5. Final global Phase 9 closeout freeze: defer until active feature/hardening slices are intentionally finished.
6. Optional/deferred scope: live n8n deployment, multi-repo enforcement, `runtime/audit/` migration, Core export completion, broader Hermes/OpenClaw gateway workflow breadth, and OSRIL Phase 10+ live-surface continuation after shared runtime substrate is stronger.

Important repo-truth note:
- the old “Phase 9 second-wave features are mostly unbuilt” story is stale
- by live repo truth, the next serious work is **selected Phase 9 implementation/hardening**, not a global closeout freeze by default

---

## Execution Rule for This Thread

From this point onward:
- finish the highest-impact remaining **Phase 9 implementation** in dependency order
- only then shift into additional feature-R&D implementation/design that depends on those substrates
- when a feature-R&D item is blocked by a missing prerequisite, build the prerequisite first instead of forcing the feature prematurely

This plan is therefore ordered by **OS leverage**, not by oldest document date.

---

## Priority Order

### Priority 1 — Runtime Registry + Agent Onboarding Surface

**Why this is first:** ChaseOS is already a real multi-runtime system, but it still lacks the canonical machine-readable runtime-governance registry and operator-facing onboarding flow that should sit above Hermes/OpenClaw parity, lifecycle, and policy binding.

**Deliverables:**
- `runtime/aor/runtime_registry/` substrate
- registry entry schema and example records for Hermes/OpenClaw
- `chaseos agent register`
- `chaseos agent status`
- `chaseos agent lifecycle`
- runtime policy binding record shape
- focused tests for registration, lifecycle transitions, and fail-closed policy binding

**Prerequisites already satisfied:**
- runtime bindings concepts exist
- runtime state exists
- adapter manifests exist
- parity doctrine exists
- agent bus exists

**Why it matters to ChaseOS:**
This is the missing OS-native bridge between “multiple runtimes exist” and “the operating system governs runtime identity, lifecycle, and policy binding explicitly.”

---

### Priority 2 — Runtime Shell Completion

**Why this is second:** After runtime onboarding exists, ChaseOS needs the command surface that operators actually use to inspect and manage the runtime layer coherently.

**Deliverables:**
- provider/model registry substrate
- `chaseos models list`
- `chaseos providers status`
- config store at `.chaseos/config.yaml`
- `chaseos config set/list`
- workflow/shell router completion where still missing
- scaffold generator contract (`chaseos scaffold ...`) at least as a bounded Phase 9 CLI foothold

**Why it matters to ChaseOS:**
The Runtime Shell is the operator-facing entrance to Phase 9. Without it, too much Phase 9 power remains buried in internal modules and partial command seams.

---

### Priority 3 — OSRIL Runtime Interaction Contract + Event Surface *(runtime foothold completed 2026-04-26)*

**Why this is third:** Once command-in surfaces are stronger, ChaseOS needs event-out visibility so runtime activity becomes legible in a future-native operator shell. The first runtime-local contract/event foothold, approval-response record/application layer, and bounded AOR approval-gate resume path are now live, even though richer transport and long-lived surface/executor resume plumbing still remain.

**Deliverables:**
- runtime interaction contract schema
- standard event types
- AOR event emission normalization
- approval-required / task-started / task-complete event routing
- bounded AOR `approval_gate` resume from approved OSRIL response records
- runtime session model footing
- operator-facing session/event inspection through `chaseos osril sessions|show|events`
- operator-facing approval queue/response records and session-state application through `chaseos osril approvals|respond`
- one-time immutable approval resume markers for approved responses consumed by AOR
- tests proving fail-closed session/event behavior

**Why it matters to ChaseOS:**
This is the event-visibility half of the OS. Runtime Shell routes commands in; OSRIL routes execution state out.

---

### Priority 4 — FSOS Execution Surface: Browser Non-Stub, Then Dispatch

**Why this is fourth:** High-value, but should sit behind stronger runtime governance and event visibility.

**Deliverables:**
- non-stub browser adapter
- real Playwright-backed execution footing
- `chaseos operate ...` CLI family foothold
- AOR dispatch wiring into `runtime/operator_surface/`
- approval and audit integration for operator-surface actions

**Why it matters to ChaseOS:**
This is the transition from bounded workflow runtime into bounded full-system operator capability.

---

### Priority 5 — Runtime Memory Consolidation

**Why this is fifth:** The memory pieces exist, but they need stronger machine-readable structure once onboarding and lifecycle are real.

**Deliverables:**
- Agent Identity Ledger runtime substrate
- governed runtime memory growth contract implementation foothold
- clearer consolidation of nav maps, scorecards, repair memory, and identity records
- command/read surface for inspecting runtime-memory families

**Why it matters to ChaseOS:**
This is how persistent runtimes become inspectable operating actors instead of disconnected tool surfaces.

---

### Priority 6 — Multi-Repo / Multi-Directory Enforcement Completion

**Why this is sixth:** Important constitutional boundary, but less foundational than onboarding + shell + event visibility.

**Deliverables:**
- manifest-level repo scope enforcement completion
- explicit extra-dir enforcement
- cross-repo edit gating
- tests for denied cross-root writes and undeclared read scope

**Why it matters to ChaseOS:**
As soon as ChaseOS operates across more than one repo or vault, this becomes a hard constitutional safety boundary.

---

### Priority 7 — Hermes Workflow Breadth / Gateway Expansion

**Why this is seventh:** Worth doing, but after the shared Phase 9 substrate is stronger.

**Deliverables:**
- broader Hermes workflow enablement beyond the current shadow lane
- bounded gateway-surface expansion where allowed
- runtime-specific operational paths that use the same shared AOR/Gate substrate without lowering parity

**Why it matters to ChaseOS:**
This closes implementation-breadth gaps while preserving the already-established equal-authority doctrine.

---

## Ordered Task Program

## Task 1: Build Runtime Registry substrate

**Objective:** Create the canonical machine-readable registry for runtime instances.

**Files:**
- Create: `runtime/aor/runtime_registry/Runtime-Registry-Folder-Guide.md`
- Create: `runtime/aor/runtime_registry/_schema.yaml`
- Create: `runtime/aor/runtime_registry/openclaw/registry_entry.yaml`
- Create: `runtime/aor/runtime_registry/hermes/registry_entry.yaml`
- Create: `runtime/aor/runtime_registry.py`
- Test: `runtime/aor/test_runtime_registry.py`

**Verification:**
- focused pytest for load/validate/list behavior
- registry entries fail closed on missing required fields

---

## Task 2: Build `chaseos agent register/status/lifecycle`

**Objective:** Expose runtime onboarding through the operator CLI.

**Files:**
- Modify: `runtime/cli/main.py`
- Modify: `runtime/COMMANDS.md`
- Modify: `README.md` (only if command surface needs truth-sync)
- Test: `runtime/tests/test_agent_cli.py`

**Verification:**
- `chaseos.py agent status`
- `chaseos.py agent register hermes --surface discord` (or equivalent bounded shape)
- `chaseos.py agent lifecycle hermes`

---

## Task 3: Build runtime policy binding record foothold

**Objective:** Make registration subordinate to an explicit policy-binding layer rather than ambient runtime assumptions.

**Files:**
- Create: `runtime/aor/policy_binding.py`
- Create: `runtime/aor/runtime_registry/<runtime_id>/policy_binding.yaml` examples or generated outputs
- Test: `runtime/aor/test_policy_binding.py`

**Verification:**
- registration does not imply execution capability
- missing binding keeps runtime fail-closed

---

## Task 4: Build provider/model registry

**Objective:** Finish the first Runtime Shell operator inventory layer.

**Files:**
- Create: `.chaseos/providers.json` or canonical equivalent if repo-local fixture is preferred for tests
- Create: `runtime/providers/registry.py` or equivalent under existing structure
- Modify: `runtime/cli/main.py`
- Test: `runtime/tests/test_provider_model_registry.py`

**Verification:**
- list providers
- inspect model bindings
- fail clearly on malformed provider records

---

## Task 5: Build config store commands

**Objective:** Give Phase 9 a bounded operator config surface.

**Files:**
- Create: `runtime/config/store.py`
- Modify: `runtime/cli/main.py`
- Modify: `runtime/COMMANDS.md`
- Test: `runtime/tests/test_config_store.py`

**Verification:**
- set/list config values
- preserve Gate supremacy over config

---

## Task 6: Build scaffold generator foothold

**Objective:** Seed the first bounded scaffold surface promised by the Runtime Shell docs.

**Files:**
- Create: `runtime/scaffold/` package
- Modify: `runtime/cli/main.py`
- Test: `runtime/tests/test_scaffold_generator.py`

**Verification:**
- scaffold writes only bounded draft/operator-safe artifacts
- generated workflows remain `status: draft`

---

## Task 7: Build OSRIL runtime interaction contract *(completed 2026-04-26)*

**Objective:** Define the first machine-readable event/session contract above AOR. This is now live through `runtime/osril/contract.py`, `runtime/osril/session.py`, and `runtime/osril/inspector.py` with runtime-local session snapshots, JSONL event streams, and read-only CLI inspection under `chaseos osril`.

**Files:**
- Create: `runtime/osril/contract.py` or equivalent aligned path
- Create: `runtime/osril/session.py`
- Create: `runtime/osril/inspector.py`
- Modify: `runtime/cli/main.py`
- Test: `runtime/tests/test_osril_contract.py`
- Test: `runtime/tests/test_osril_cli.py`
- Truth-sync: `06_AGENTS/Operator-Surface-Runtime-Interaction.md` if needed after implementation

**Verification:**
- standard event payloads validate
- approval-required event shape exists
- session continuity is explicit and bounded

---

## Task 8: Wire AOR event emission into OSRIL *(completed 2026-04-26)*

**Objective:** Make the contract real by routing bounded execution events out of the engine. This is now live for normalized run-level outcomes (`status`, `task_started`, `task_complete`, `task_failed`) from `runtime/aor/engine.py` without widening any write authority.

**Files:**
- Modify: `runtime/aor/engine.py`
- Test: `runtime/tests/test_aor_osril_events.py`

**Verification:**
- workflow start/complete/escalation emit normalized events
- failures do not suppress audit

---

## Task 9: Implement browser adapter non-stub foothold

**Objective:** Turn FSOS browser execution from architecture-plus-stubs into a bounded real surface.

**Files:**
- Modify: `runtime/operator_surface/adapters/browser_adapter.py`
- Modify: `runtime/operator_surface/browser/actions.py`
- Modify: `runtime/operator_surface/browser/perception.py`
- Test: `runtime/operator_surface/tests/test_browser_non_stub.py`

**Verification:**
- isolated browser context opens
- one safe bounded action executes under declared scope
- audit/event surfaces receive results

---

## Task 10: Build `chaseos operate` command family foothold

**Objective:** Expose FSOS through the CLI once the browser adapter is real enough.

**Files:**
- Modify: `runtime/cli/main.py`
- Modify: `runtime/COMMANDS.md`
- Test: `runtime/tests/test_operate_cli.py`

**Verification:**
- inspect/open/action path works in bounded mode
- commands remain approval-aware and fail closed

---

## Task 10A: Harden FSOS browser policy boundary — COMPLETE (2026-04-28)

**Objective:** Make the browser authority boundary inspectable and ensure adapter-specific always-approval actions participate in executor approval checks.

**Implemented files:**
- `runtime/operator_surface/browser/policy.py`
- `runtime/operator_surface/scopes.py` via `approval_required_actions_for(...)`
- `runtime/operator_surface/executor.py` via shared-plus-adapter approval union
- `runtime/cli/main.py` via `chaseos operate browser policy`
- `runtime/cli/json_contract.py`
- `runtime/cli/command_contract.json`
- `runtime/operator_surface/tests/test_browser_policy.py`
- generated CLI reference and FSOS/browser docs

**Verification:**
- `chaseos operate browser policy --json` returns a read-only authority report without launching a browser
- executor pauses before adapter-specific always-approval actions such as `cookie_consent_accept`
- the report separates promoted CLI authority from adapter-supported but unpromoted primitives (`click`, `type`, keyboard, tab management, generic extraction)
- no click/form/download/authenticated-session authority was widened

---

## Task 11: Build Agent Identity Ledger substrate — COMPLETE (2026-04-27)

**Objective:** Create the machine-readable identity layer that complements scorecards and nav memory.

**Implemented files:**
- `runtime/memory/adapters/_identity_ledger_schema.json`
- `runtime/memory/adapters/claude/identity-ledger.json`
- `runtime/memory/adapters/hermes/identity-ledger.json`
- `runtime/memory/adapters/openclaw/identity-ledger.json`
- `06_AGENTS/Claude-Identity-Ledger.md`
- read-only inspector support in `runtime/memory/inspector.py` and `chaseos memory show <runtime> --json`
- focused coverage in `runtime/memory/test_memory_inspector.py`

**Verification:**
- runtime identity records load cleanly through the read-only memory inspector
- behavior history is inspectable, not permission-granting
- `uvx pytest runtime/memory/test_memory_inspector.py -q` passes
- `uvx --with pyyaml pytest runtime/memory/test_memory_inspector.py runtime/memory/scorecards/test_scorecard_updater.py -q` passes

---

## Task 12: Build governed runtime-memory consolidation surface — COMPLETE (2026-04-28)

**Objective:** Consolidate scorecards, nav maps, identity, and repair-memory routing under one inspectable family.

**Implemented files:**
- `runtime/memory/inspector.py` via `build_memory_summary(...)`
- `runtime/cli/main.py` via `chaseos memory summary`
- `runtime/cli/command_contract.json`
- `runtime/memory/test_memory_inspector.py`
- generated CLI reference and runtime memory docs

**Verification:**
- all runtime-memory families enumerate cleanly through `memory summary`
- validation includes adapters, repair memory, nav maps, scorecards, and active task contexts
- missing runtime-memory families are surfaced as attention items instead of invented
- governance flags make memory advisory and deny automatic Gate/source-truth override, task-memory promotion, identity authority, and repair-memory auto-application

---

## Task 13: Complete multi-repo enforcement — COMPLETE / VERIFIED TARGETED (2026-04-28)

**Objective:** Turn the policy doctrine into stronger runtime enforcement.

**Files:**
- Created: `runtime/aor/path_policy.py`
- Modified: `runtime/aor/engine.py`
- Modified: `runtime/aor/registry.py`
- Modified: `runtime/aor/role_cards.py`
- Modified: `runtime/tests/test_gate_deny_default_runtime_policy.py` (stale FSOS action-contract assertions corrected)
- Tested: `runtime/tests/test_multi_repo_enforcement.py`

**Verification:**
- undeclared extra directories blocked by manifest validation
- cross-repo access requires explicit `policy_ref` / `policy_path`
- absolute, drive-qualified, and parent-traversal manifest/role paths are blocked
- AOR Stage 5 resolves required reads under `vault_root`
- AOR Stage 7 resolves handler writebacks before directory creation or file writes
- attempted path traversal from a handler escalates at `writeback_handling` and does not create the escaped file
- existing current manifests and role cards still load under the stricter validation

**Remaining limitation:**
- true cross-repo / extra-directory execution remains intentionally non-executable. This pass closes the vault-root escape and declaration validation gap; a future evaluator is still required before any extra repo can be read or written.

---

## Task 14: Expand Hermes/OpenClaw workflow breadth on the stronger substrate - COMPLETE / VERIFIED TARGETED (2026-04-29)

**Objective:** Increase Hermes/OpenClaw implementation breadth only after the shared runtime substrate is stronger.

**2026-04-29 status:** Hermes breadth is expanded for coordination-bus review and bounded bus-analysis packets only. This closes the capability/dispatch mismatch for Hermes `planning`, `shadow-audit`, and `developer-co-development` task types without adding external, shell, browser, credential, canonical, or protected-write authority. The OpenClaw `source-pack-builder` receiver gap is also closed through a declared JSON input envelope (`source_pack_inputs_path` or `source_pack_inputs_json`) that feeds the existing bounded `source_pack_builder` workflow.

**Files:**
- likely under `runtime/workflows/registry/`
- likely under `06_AGENTS/role-cards/`
- runtime-specific config/policy surfaces as needed

**Verification:**
- broader Hermes bounded workflows execute through the same AOR/Gate policy chain
- no parity regressions in doctrine or machine-readable posture
- targeted verification passed for governance exact-workflow checks and manual Hermes watch dispatch; full Hermes watch pytest remains blocked locally by Windows temp ACL behavior
- targeted OpenClaw source-pack receiver tests pass for workflow inference, dispatch-table registration, declared JSON input-packet loading, missing-envelope fail-closed behavior, and the full OpenClaw watch regression file

**Remaining:** Task 14 has no known capability/dispatch mismatch remaining inside current bounded scope. Live host scheduler proof and broader live connector/source coverage remain separate Phase 9 hardening/acquisition lanes, not this workflow-breadth receiver gap.

---

## What Comes After Phase 9 Closure

Only after the above Phase 9 closure work is materially complete should the thread shift into broader feature-R&D implementation/design that depends on those prerequisites.

The most likely follow-on surfaces after Phase 9 closure:
- richer Runtime Shell / Settings product-surface mapping
- richer OSRIL operator-shell surfaces
- broader FSOS adapter family completion
- more advanced runtime-memory/identity quality surfaces
- Phase 10 ChaseOS Studio implementation/design moves backed by real Phase 9 substrate rather than paper prerequisites

---

## Recommended Immediate Start

Start with one of three non-OSRIL choices:

1. **Phase 10A0 Studio Acquisition Intake Cockpit** if the operator wants the reviewed research-pack/SBP live-file workflow to become easy to test and operate.
2. **Remaining Phase 9 activation hardening** if the operator wants host startup/reboot proof closed next.
3. **Another concrete Phase 9 feature slice** if the operator selects a specific unfinished runtime/operator feature.

Do not restart OSRIL Phase 9. The Phase 9 runtime-side OSRIL feature scope is closed in `06_AGENTS/OSRIL-Phase9-Closeout.md`; OSRIL live-surface continuation now belongs to Phase 10+ unless deliberately reopened as Phase 9.x hardening.

The older Runtime Registry / agent command / policy-binding start sequence is complete by live repo truth. Do not restart that lane unless validating or extending it.

---

## Reporting Rule for the User Loop

For each future pass in this thread, report back with:
- what priority lane is being executed now
- what concrete files were created/modified
- what tests passed
- what Phase 9 prerequisite was just cleared
- what becomes newly ready because of that cleared prerequisite

That keeps implementation sequencing visible and prevents feature-R&D from drifting ahead of substrate truth.

---

*Graph links: [[Phase9-Adopted-Feature-Specification]] · [[Feature-Register]] · [[Feature-Fit-Register]] · [[Runtime-Onboarding-Standard]] · [[ChaseOS-Runtime-Shell]] · [[Operator-Surface-Runtime-Interaction]] · [[Agent-Scorecards-and-Runtime-Quality-Surfaces-Standalone-Application]] · [[Agent-Identity-Ledger-Surfaces-Standalone-Application]] · [[Memory-Inspector-and-Runtime-Memory-Surfaces-Standalone-Application]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
