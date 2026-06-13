---
title: ChaseOS Cross-Runtime Handoff
created: 2026-05-01
status: ACTIVE / HANDOFF SNAPSHOT
scope: Future agents resuming ChaseOS Phase 9/10 runtime, Pulse, Studio, SiteOps, Browser Skill, and Agent Bus work
---

# ChaseOS Cross-Runtime Handoff

This is a concise, non-secret handoff for future agents. It summarizes current repo truth from recent build logs, documentation-history notes, runtime adapter handoffs, and Agent Activity records. Treat linked build logs as the detailed source of truth.

## Current State

- Workspace: `%CHASEOS_VAULT_ROOT%`.
- Git: this workspace is **not a Git repository**; `git -C ... status --short --branch` returns `fatal: not a git repository`.
- Current phase: Phase 9 remains active for selected hardening/proof; Phase 10/Studio surfaces are being introduced narrowly, not as a finished desktop/product shell.
- Hermes startup: Windows Startup now delegates to `%USERPROFILE%\.hermes\gateway.cmd`; the live target launcher was updated to enter WSL `Ubuntu` as user `chaseos`, run from `<WSL_CHASEOS_VAULT_ROOT>`, retry, and log to `%USERPROFILE%\.hermes\gateway-startup.log`. Post-logon proof remains unverified.
- Pulse: backend/local static surfaces exist and now include read-only review queue, Agent Bus handoff preview, and supervised live handoff readiness panels. Live enqueue, approval grants, runtime dispatch, candidate apply, schedule activation, provider calls, and canonical writeback remain blocked.
- SiteOps / Browser Skill candidate lane: registry, dry-run plans, candidate approvals, readiness summaries, bound approval request projections, and executor/preflight/spec surfaces are read-only or dry-run. Trusted Browser Skill writes, SiteOps Skill Card writes, browser/CDP execution, activation, Agent Bus mutation, provider calls, and canonical writeback remain unbuilt/blocked unless a specific future governed pass proves otherwise.
- Studio: Hermes/Optimus is the primary Phase 10 Studio surface implementer. Phase 10A0 Acquisition Intake Cockpit has local-only model/CLI/static/localhost footholds, action wrappers, preview-pack visibility, and rehearsal ladder; later Studio and Phase 11 Chat surfaces are operator interfaces over existing ChaseOS contracts, not canonical truth engines. Full desktop/product authority and backend execution remain gated by lower-phase contracts; backend gaps are dependency handoffs, not permission for Studio work to cross into Phase 9-and-below authority.
- Codex adapter: `runtime/adapters/codex/` contains handoffs for the Codex bus worker and live CLI tests. Codex is expected to join Agent Bus as runtime `Codex` with retained instance `Axiom-Codex`.
- Archon: established as named Agent Bus runtime peer for the Claude Code engineering lane, with memory surfaces and `archon_watch`; current handlers are bounded analysis/engineering handlers, not unrestricted LLM synthesis.

## Recent Passes Inspected

- [[2026-05-01-ChaseOS-hermes-wsl-startup-settings-model]] / [[2026-05-01_hermes-wsl-startup-settings-model]] / [[2026-05-01-codex-hermes-wsl-startup-settings-model]]
  - Added managed Hermes WSL launcher profile and `chaseos runtime startup-surface-settings`.
  - Validation included `30 passed`, CLI docs check, live settings/startup smokes, and WSL probe recording `Wsl/Service/E_ACCESSDENIED`.
- [[2026-05-01-openclaw-phase10-agent-bus-handoff-preview]]
  - Pulse local surface now previews bounded Agent Bus `REVIEW` task handoffs without writing bus tasks or approvals.
  - Validation: focused Pulse tests `19 passed, 16 subtests`; full Pulse `239 passed, 186 subtests`.
- [[2026-05-01-openclaw-phase10-supervised-handoff-readiness]]
  - Pulse local surface now composes persisted enqueue approval requests with `bus_handoff_preflight.py` into a read-only supervised readiness panel.
  - Validation: focused tests `15 passed, 20 subtests`; full Pulse `240 passed, 186 subtests`; broad `runtime` suite had unrelated drift (`3214 passed, 11 skipped, 21 failed`).
- [[2026-05-01-ChaseOS-optimus-siteops-approval-readiness-summary]]
  - Added queue-level SiteOps candidate approval readiness summaries; no mutation authority.
  - Validation included candidate promotion `61 passed`, SiteOps `103 passed`, AOR `580 passed`, and live non-writing smoke.
- [[2026-05-01-ChaseOS-optimus-siteops-approval-bound-request-projection]] and [[2026-05-01-ChaseOS-optimus-siteops-bound-approval-summary-parity]]
  - Added/restored bound approval request projection and summary parity for SiteOps approvals.
  - Validation included candidate promotion `64 passed`, SiteOps `106 passed`, AOR `580 passed`, command-contract/docs checks, and live non-writing smoke with `writes_performed=false`.
- [[2026-04-30-ChaseOS-browser-operator-skill-layer]]
  - Added bounded Browser Operator Skill Layer scaffolding, schema, validator, templates, candidate/run folders, and draft Excalidraw shadow skill.
  - Validation: focused validator `10 passed`; browser policy subset `4 passed, 1 deselected`; `py_compile` passed. Full combined browser policy test was blocked by Windows temp ACL behavior, not BOSL code.
- [[2026-04-30-ChaseOS-optimus-siteops-registry-dry-run-foothold]]
  - Added SiteOps Website Workflow Index, Site Skills registry, validation, dry-run planning, CLI, and audit target.
  - Validation: focused nearby `19 passed`, AOR `580 passed`, syntax and live dry-run/validate smokes.
- [[2026-04-30_archon-runtime-identity]]
  - Established Archon runtime identity, memory surfaces, role card, task types, and `archon_watch` with 55 tests.
- [[2026-04-30_phase10a0-studio-preview-promotion-prefill]] and [[2026-04-30_phase10a0-studio-rehearsal-ladder]]
  - Studio acquisition cockpit gained preview-pack BRIS prefill and a read-only workflow rehearsal ladder while preserving local-only/non-authoritative boundaries.
- [[2026-04-29-ChaseOS-optimus-pulse-ui-runtime-handoff-alignment]] / [[ChaseOS-Pulse-UI-and-Runtime-Handoff]]
  - User pivot to ChaseOS Pulse captured; Pulse handoff made the active implementation context for Codex/Hermes/OpenClaw coordination.

## Validation Commands to Prefer

Run from `%CHASEOS_VAULT_ROOT%`.

```powershell
# Basic repo/non-repo reality
Test-Path .git
git -C . status --short --branch

# Hermes startup settings/read-only surfaces
python -m py_compile runtime/lifecycle/startup_surfaces.py runtime/cli/main.py runtime/chaseos_gate.py
python -m pytest runtime/lifecycle/test_startup_surfaces.py runtime/test_runtime_startup_surfaces_cli.py runtime/test_chaseos_startup_surfaces_cli.py runtime/tests/test_cli_command_contract.py -q -p no:cacheprovider
python chaseos.py runtime startup-surface-settings --runtime hermes --json
python chaseos.py runtime startup-surfaces --runtime hermes --json

# Pulse local/operator handoff surfaces
python -m pytest runtime\pulse\test_local_surface.py runtime\pulse\test_bus_handoff_preflight.py runtime\pulse\test_bus_review_queue.py runtime\pulse\test_candidate_inspector.py -q
python -m pytest runtime\pulse -q

# SiteOps read-only/dry-run lane
python -m pytest runtime/siteops/tests/test_candidate_promotions.py runtime/tests/test_cli_command_contract.py -q
python -m pytest runtime/siteops -q
python chaseos.py siteops validate --json
python chaseos.py siteops candidates approvals --tenant TENANT_ID --workspace WORKSPACE_ID --include-readiness-summary --include-bound-approval-request-spec --json

# Codex adapter readiness/smoke
python -m chaseos agent-bus codex-daemon --readiness --json
python -m chaseos agent-bus codex-daemon --once --executor mock --json
python -m pytest runtime\adapters\codex -q

# Generated docs / command contract
python -m runtime.cli.generate_docs --check
python -m json.tool runtime/cli/command_contract.json
```

Use `.venv\Scripts\python.exe` where a pass specifically depended on the local venv. In WSL/bare `uvx`, add `--with pyyaml` when YAML imports are needed.

## Known Constraints and Boundaries

- Not a git repo: do not promise branch names, diffs, or commits unless a future agent initializes or works in an actual git checkout.
- Dry-run/read-only expectation is the default for SiteOps, BOSL, provider governance, startup settings, and Pulse handoff previews unless a specific governed writer/executor has been implemented and validated.
- Do not treat approval request generation, bound request specs, executor preflights, or readiness summaries as approval decisions or execution authority.
- Do not mutate `02_KNOWLEDGE/`, R&D workbook truth, Pulse memory, Personal Map, provider config, Gate allowlists, browser profiles, credentials, external sites, or canonical ChaseOS truth from these surfaces unless a future task explicitly grants a validated governed write path.
- Hermes WSL startup still needs post-logon evidence from `%USERPROFILE%\.hermes\gateway-startup.log`; current WSL probe from shell recorded `Wsl/Service/E_ACCESSDENIED`.
- Browser live automation remains unproven for BOSL; Excalidraw shadow proof, CDP adapter, isolated-profile run logging, and promotion pipeline are future work.
- Broad runtime suite drift exists outside the latest Pulse handoff changes; do not treat broad failures as caused by Pulse without reproducing and isolating them.

## Safe Next Tasks

1. Read-only post-logon verifier for Hermes startup: inspect/import `gateway-startup.log` and Agent Bus/Hermes status without starting/stopping processes or mutating scheduler/startup entries.
2. No-mutation startup-surface approval-request writer for future preference/executor toggles; keep idempotency and approval consumption separate.
3. Pulse next safe increment: read-only/pending-review UI improvements over existing deck/candidate/handoff artifacts; no live enqueue until approval/evidence/final-enqueue gates are explicit and tested.
4. SiteOps next safe increment: bound approval request writer design or validation-only writer rehearsal; preserve no decision/apply/activation/browser execution.
5. BOSL next safe increment: isolated-profile Excalidraw shadow proof with no login, no credentials, relative coordinates, and run log under `07_LOGS/Browser-Runs/`.
6. Studio next safe increment: operator-guided real-file rehearsal once local research files are staged; keep action confirmations explicit and local-only.
7. Codex adapter next safe increment: readiness/mock daemon plus task-level constraint smokes before any live Codex daemon polling.
8. Archon next safe increment: add Archon seeding to `brain_bootstrap.py` and/or scorecard tracking only if backed by tests; keep review routing to Hermes unless docs change.

## Runtime-Specific Ownership / Evidence

| Runtime / Surface | Evidenced role | Current owner boundary |
|---|---|---|
| OpenClaw | Registered peer/runtime lane; implemented Pulse Agent Bus handoff preview and supervised handoff readiness passes. | Backend dependency tracking, Windows-side proof, scheduled/AOR execution, and lower-phase handoff evidence; not the default Phase 10 Studio implementer and no live enqueue or authority expansion from latest passes. |
| Hermes / Optimus | Runtime lane for review/operator coordination, startup lifecycle, and bounded Phase 10 Studio surface continuation; WSL gateway target launcher managed through Windows Startup delegation. | Primary Phase 10 Studio implementer for surface/readiness/local wrapper work and approved audit/handoff artifacts; may document dependencies but not resolve Phase 9 backend authority gaps; post-logon Hermes gateway proof still unknown. |
| Codex | Repo-aware coding/runtime adapter; Agent Bus worker handoffs under `runtime/adapters/codex/`; retained instance `Axiom-Codex`. | Code/repo/test tasks through bounded packets; no direct Pulse memory, Personal Map, R&D truth, or governed runtime mutation unless explicitly authorized. |
| Optimus | Evidenced in SiteOps approval/readiness/projection build logs as bounded Hermes-lane implementation/review work. | SiteOps read-only readiness/projection/control-plane improvements; no approvals, trusted writes, browser execution, Agent Bus mutation, provider calls, or canonical writeback. |
| Browser / BOSL | Feature surface, not evidenced here as an autonomous runtime owner. BOSL scaffold and Browser Operator Surface are governed under AOR/Gate. | Skill/candidate validation and future isolated shadow runs only; live browser/CDP/account authority remains unbuilt/blocked. |
| Pulse | Native ChaseOS proactive intelligence feature family, not a generic digest. | Local deck/candidate/review/handoff surfaces are partial and read-only/pending-review; no schedule activation, memory approval, live dispatch, or canonical writeback. |
| Studio | Phase 10 interface/product-shell surface; Hermes/Optimus-owned implementation lane for bounded surface/readiness work; Phase 10A0 acquisition cockpit is the narrow live foothold. | Local-only UI/service wrappers with explicit confirmations; backend blockers must be reported with missing contract, affected Phase 10/11 surface, lower-phase owner/surface, minimum proof needed, and blocked action reason; full Studio desktop and startup toggles UI/executor remain unbuilt. |
| Archon | Named Agent Bus runtime peer / Claude Code engineering lane with memory surfaces and `archon_watch`. | Bounded engineering/analysis handlers; review remains Hermes-routed; LLM synthesis and full scorecard wiring are future gaps. |

## Source Links

- [[Build-Logs-Index]]
- [[Documentation-History-Index]]
- [[Agent-Activity-Index]]
- [[ChaseOS-Pulse-UI-and-Runtime-Handoff]]
- [[CODEX_BUS_HANDOFF]]
- [[CODEX_CLI_LIVE_TEST_HANDOFF]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
