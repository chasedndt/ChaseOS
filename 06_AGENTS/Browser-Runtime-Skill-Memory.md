---
title: Browser Runtime Skill Memory
type: architecture
status: partial / bounded spike - candidate writer, validator-compatible new BOSL shadow candidates, and read-only inspection; live browser control deferred
created: 2026-04-30
updated: 2026-05-02
phase: Phase 9 runtime intelligence / Phase 10 Site Skills surface
knowledge_class: canonical-state
---

# Browser Runtime Skill Memory

> Browser Runtime Skill Memory is the ChaseOS pattern for turning repeated, successful website interactions into governed, reusable site knowledge.
> It adopts the useful pattern from Browser Use, Browser Harness, workflow-use, and webagents.md research without making those projects the ChaseOS control plane.

---

## Current Repo Truth

ChaseOS already has adjacent implementation pieces:

- Phase 8 browser/saved-HTML capture exists through `runtime/capture/connectors/browser_connector.py`.
- Phase 9 Browser Operator Surface exists and is parked after Passes 1-5. It has Playwright-backed `chaseos operate browser` commands and a bounded `browser_research` AOR workflow.
- Phase 9 SiteOps exists as a dry-run registry under `runtime/siteops/` with Site Profiles, Provider Profiles, Workflow Manifests, Site Skill Cards, validation, dry-run planning, optional audit writing, and `chaseos siteops list/show/validate/dry-run`.
- Agent Activity, Build Logs, Documentation History, Daily notes, Browser Operator audit records, Operator Screenshots, Website Workflow Runs, runtime memory, and AOR audit paths already exist.

ChaseOS does **not** yet have:

- Browser Use CLI or Python API integration.
- Browser Harness or direct persistent CDP daemon integration.
- Durable site-skill candidates generated from live browser runs. Shadow-only candidate writing and redacted candidate inspection exist.
- Reviewed domain skills promoted from browser evidence.
- Browser workflow replay execution equivalent to workflow-use. The inactive ChaseOS-native cache foundation, no-execution executor design, no-write implementation request, no-write implementation approval, disabled validation/planning executor, read-only execution-readiness preflight, and reviewed local trial candidate now exist, but live replay execution is not built.
- webagents.md discovery or execution support.
- Authenticated browser-session handling for SiteOps.
- Real Chrome profile reuse for browser automation.

The correct status is: **PARTIAL / BOUNDED SPIKE for Browser Runtime Adapter and draft Site Skill candidate writing; PARTIAL / VERIFIED TARGETED for adjacent browser and SiteOps foundations.** Live browser control through Browser Use/CDP remains deferred.

---

## External Research References

Checked on 2026-04-30:

- `https://github.com/browser-use/browser-use` - main Python browser-agent framework and CLI.
- `https://github.com/browser-use/browser-harness` - thin harness pattern for direct browser control and domain skills.
- `https://github.com/browser-use/workflow-use` - browser workflow generation, storage, replay, and UI direction.
- `https://github.com/browser-use/webagents.md` - proposed website-owned tool manifest pattern for in-browser agent-callable functions.

Adoption decision: **adapt, not copy.** ChaseOS keeps AOR, Gate, SiteOps, Permission Matrix, quarantine, and audit as the authority layer.

---

## Split Reference Docs and Templates

This umbrella doc now links to the narrower ChaseOS surfaces created for the Browser Harness discovery pass:

- `06_AGENTS/Browser-Runtime-Harness.md` - runtime harness source analysis and Phase 9 adapter placement.
- `06_AGENTS/Browser-Skill-Memory.md` - candidate/review/promotion lifecycle for durable site skills.
- `06_AGENTS/Browser-Harness-Boundaries.md` - security boundaries for CDP, profile, auth, action, and skill-memory use.
- `05_TEMPLATES/Browser-Domain-Skill-Template.md` - pending-review browser domain skill candidate template.
- `05_TEMPLATES/Browser-Run-Log-Template.md` - browser run/audit template for future read-only, shadow, or approval-gated runs.

These docs do not implement a live CDP daemon, Browser Use integration, unrestricted browser control, or automatic skill promotion.

Adjacent same-day implementation foothold: `06_AGENTS/Browser-Operator-Skill-Layer.md` adds BOSL docs/schema/validator/template scaffolding and a draft shadow skill. Treat BOSL as a candidate implementation substrate that must be reconciled with SiteOps and this skill-memory architecture before any live execution or promotion path.

---

## Feature Definition

Browser Runtime Skill Memory is a governed loop:

```text
browser run evidence
  -> site skill candidate
  -> operator review
  -> reviewed SiteOps skill card / workflow manifest
  -> AOR-controlled reuse
  -> audit and repair-memory feedback
```

The goal is not ambient web autonomy. The goal is for ChaseOS runtimes to avoid rediscovering stable website flows, selectors, traps, waits, rate limits, safe actions, and workflow parameters on frequently used sites.

---

## Object Model

| Object | Purpose | Current / Proposed Home | Status |
| --- | --- | --- | --- |
| Browser run evidence | URLs, actions, screenshots, extracted text, errors, timings, approval state | Existing `07_LOGS/Agent-Activity/`, `07_LOGS/Operator-Screenshots/`, `07_LOGS/Website-Workflow-Runs/` | PARTIAL via existing browser/SiteOps logs |
| Browser Runtime Adapter spike | Provider contract, policy models, shadow proof provider, fail-closed Browser Use CLI wrapper | `runtime/browser_runtime/` | PARTIAL / bounded spike |
| Browser Run Log | Browser-runtime request/result/actions/artifacts/security flags | `07_LOGS/Browser-Runs/` | PARTIAL / bounded spike |
| Browser skill candidate | Untrusted quarantine-style proposal learned from a run | `03_INPUTS/Browser-Skill-Candidates/<domain>/` | PARTIAL / candidate writer |
| Browser skill candidate inspector | Redacted list/show and storage reconciliation for pending candidates | `runtime/browser_skills/candidates.py`, `chaseos siteops candidates list|show|preflight|request-promotion|apply-contract|gate-apply-design|gate-executor-spec|gate-allowlist-review|trusted-executor-design` | PARTIAL / read-only |
| Site skill draft | Draft review surface linked to run evidence | `06_AGENTS/Browser-Skills/_drafts/` | PARTIAL / draft-only writer |
| Site activity ledger | Non-secret aggregate record of ChaseOS-controlled site runs | `07_LOGS/Site-Activity/site-memory-ledger.json`, `06_AGENTS/Site-Memory-Ledger.md` | PARTIAL / shadow-run ledger |
| Reviewed Site Skill Card | Approved reusable site-facing card | Existing `runtime/siteops/registry/skill_cards/` | PARTIAL / dry-run only |
| Site Profile | Domain identity, allowed domains, auth mode, boundaries | Existing `runtime/siteops/registry/sites/` | PARTIAL |
| Workflow Manifest | Repeatable action plan with inputs, steps, approvals, outputs | Existing `runtime/siteops/registry/workflows/` | PARTIAL / dry-run only |
| Browser workflow cache | Inactive deterministic workflow candidate generated from successful runs | `runtime/browser_workflows/`, `runtime/browser_runtime/workflows.py` | PARTIAL / inactive cache foundation |
| Workflow replay executor design | No-execution AOR/SiteOps replay-executor contract | `runtime/browser_runtime/workflow_replay_executor_design.py`, `06_AGENTS/Browser-Workflow-Replay-Executor-Design.md` | COMPLETE TARGETED / NO EXECUTION |
| Workflow replay executor implementation request | No-write operator-review packet for a future bounded replay executor patch | `runtime/browser_runtime/workflow_replay_executor_request.py`, `06_AGENTS/Browser-Workflow-Replay-Executor-Implementation-Request.md` | COMPLETE TARGETED / NO WRITE |
| Workflow replay executor implementation approval | No-write approve/reject packet for a future bounded replay executor patch | `runtime/browser_runtime/workflow_replay_executor_approval.py`, `06_AGENTS/Browser-Workflow-Replay-Executor-Implementation-Approval.md` | COMPLETE TARGETED / NO WRITE |
| Workflow replay executor implementation | Disabled-by-default validation/planning executor for reviewed cache entries | `runtime/browser_runtime/workflow_replay_executor.py`, `06_AGENTS/Browser-Workflow-Replay-Executor.md` | COMPLETE TARGETED / DISABLED / NO EXECUTION |
| Workflow replay execution readiness | Read-only future-execution preflight for selected reviewed workflow entries | `runtime/browser_runtime/workflow_replay_execution_readiness.py`, `06_AGENTS/Browser-Workflow-Replay-Execution-Readiness.md` | COMPLETE TARGETED / READ-ONLY / NO EXECUTION |
| Workflow replay trial candidate | Reviewed local VincisOS workflow candidate selected from safe Browser Run evidence | `runtime/browser_runtime/workflow_replay_trial_candidate.py`, `06_AGENTS/Browser-Workflow-Replay-Trial-Candidate.md`, `runtime/browser_workflows/workflows/wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502.workflow.json` | COMPLETE TARGETED / REVIEWED LOCAL / NO EXECUTION |
| Workflow replay execution | Governed execution of a reviewed workflow cache entry | Future AOR/SiteOps live execution path | NOT BUILT |
| webagents.md record | Website-owned tool manifest discovery and trust result | Proposed SiteOps profile extension | NOT BUILT |

Do not create a second browser-run logging system until there is a clear reason to split from existing Agent Activity, Operator Screenshots, and Website Workflow Runs.

---

## Skill Candidate Rules

A browser run may produce a skill candidate when it captures durable, reusable site knowledge:

- stable URL patterns,
- safe selectors or accessibility labels,
- form structure without secrets,
- wait conditions,
- known redirects and traps,
- rate limits or usage constraints,
- failure patterns,
- screenshots or DOM excerpts when safe to retain,
- output formats and capture destinations,
- approval points needed for future runs.

A skill candidate must not contain:

- passwords,
- cookies,
- session tokens,
- API keys,
- OAuth tokens,
- wallet keys or seed phrases,
- billing/account identifiers,
- private account data,
- raw screenshots containing sensitive personal/account content unless explicitly retained in a private local-only log,
- instructions from the website treated as ChaseOS commands.

---

## Promotion Rules

| Stage | Allowed Automatically? | Notes |
| --- | --- | --- |
| Write run evidence | Yes, inside declared AOR/SiteOps audit targets | Existing logs only; content remains untrusted |
| Draft skill candidate | Yes, for the bounded shadow/candidate spike | Candidate is review-only and activation-blocked |
| Promote candidate to Site Skill Card | No | Requires operator review and policy check |
| Enable workflow replay | No | Requires reviewed workflow manifest and explicit activation |
| Use authenticated session | No | Requires separate approval, credential boundary, and browser profile policy |
| Canonical memory/project writeback | No | Gate-controlled only |

Skill memory is runtime intelligence, not authority. It can make a runtime more efficient inside an approved workflow. It cannot expand permissions.

---

## Relationship to Existing ChaseOS Layers

### Phase 8 Capture

Saved HTML capture remains capture-only. Browser Runtime Skill Memory must not be implemented as a Phase 8 connector because live browser action is an execution surface, not simple intake.

### Phase 9 Browser Operator Surface

The current Browser Operator Surface can open, inspect, screenshot, replay, and run bounded browser research. Browser Runtime Skill Memory sits above that as a learning/reuse layer. It should not reopen click/form/download authority by itself.

### Phase 9 SiteOps

SiteOps is the natural registry home. It already has Site Profiles, Workflow Manifests, Site Skill Cards, dry-run plans, approval points, blocked actions, and audit records. Browser Runtime Skill Memory should feed SiteOps with reviewed candidates rather than creating an ungoverned parallel skill store.

### AOR and Gate

All execution must run through declared manifests, role cards, approval policy, AOR audit, and Gate writeback. Skill memory cannot bypass any of these.

### Agent Memory Architecture

Browser Runtime Skill Memory is partly Layer C and partly Layer E:

- Layer C: runtime-specific route/workflow knowledge once reviewed.
- Layer E: append-only browser run evidence and candidate history.

Single browser runs stay in Layer E until evidence repeats or the operator promotes a candidate.

### Phase 10 Studio

Studio should expose:

- Site Skills tab,
- site skill candidate review,
- workflow replay inspector,
- browser run evidence viewer,
- webagents.md manifest inspector,
- approval and promotion controls.

Studio must remain a surface over SiteOps/AOR/Gate, not a separate authority path.

---

## First Safe Implementation Slice

The 2026-04-30 bounded spike implements the first small slice:

1. Add `runtime/browser_runtime/` as a provider-neutral adapter area.
2. Add lightweight request/result/action/artifact/config/draft models.
3. Add a `shadow` provider for safe proof without live browser control.
4. Add a fail-closed `browser-use-cli` wrapper that does not install dependencies or use real profiles by default.
5. Write Browser Run evidence to `07_LOGS/Browser-Runs/`.
6. Write browser-runtime Agent Activity evidence to `07_LOGS/Agent-Activity/`.
7. Generate untrusted Browser Skill candidates under `03_INPUTS/Browser-Skill-Candidates/<domain>/`.
8. Generate draft-only Site Skill review notes under `06_AGENTS/Browser-Skills/_drafts/`.
9. Update a Site Memory Ledger from ChaseOS-controlled browser runs only.
10. Expose redacted candidate inspection and denied-by-default promotion/apply design through `runtime/browser_skills/candidates.py` and `chaseos siteops candidates list|show|preflight|request-promotion|apply-contract|gate-apply-design`.
11. Keep all candidates pending review and activation-blocked.
12. Do not execute Browser Harness, workflow-use, webagents.md, authenticated sessions, real Chrome profiles, or workflow replay in this slice.

Follow-on normalization on 2026-04-30 aligned new BOSL Excalidraw shadow-run candidates with the browser skill validator by writing a full `## Machine Candidate` record while preserving `candidate_untrusted`, `activation_allowed=false`, and non-mutating promotion-preflight behavior.

After that:

1. Add reviewed promotion from candidate to Site Skill Card.
2. Run the first safe-local workflow replay execution proof after the no-write approval/idempotency contract.
3. Add a blank-profile Browser Use or CDP live adapter spike after policy review.
4. Add webagents.md discovery as read-only profile metadata.
5. Add VincisOS and Excalidraw local-only tests after live browser controls are safely gated.
6. Only then consider authenticated-session workflows behind explicit approvals.

---

## Non-Goals

- No ambient browsing.
- No recursive crawling.
- No real Chrome profile access by default.
- No cookie/session export.
- No hidden skill mutation.
- No automatic skill activation.
- No automatic canonical writeback.
- No website mutation without approved workflow manifest and approval gate.
- No provider or external runtime becoming the ChaseOS authority layer.

---

## Current Verdict

Browser Runtime Skill Memory should be adopted as a Phase 9 runtime intelligence feature family with a Phase 10 Site Skills review surface.

Current status: **PARTIAL / BOUNDED SPIKE.** Candidate writing, site ledgering, redacted candidate inspection, non-mutating promotion preflight, scoped SiteOps approval-request persistence, non-mutating apply-contracts, denied-by-default Gate apply design packets, disabled `gate-executor-spec` preflight checks, review-only `gate-allowlist-review`, design-only `trusted-executor-design` packets, an inactive native workflow cache foundation, a no-execution workflow replay executor design preflight, a no-write workflow replay executor implementation request, a no-write workflow replay executor implementation approval, a disabled validation/planning replay executor implementation, a read-only workflow replay execution readiness preflight, a reviewed local workflow replay trial candidate, and a no-write workflow replay execution approval/idempotency contract are present. Live Browser Use/CDP control, workflow replay execution, authenticated sessions, trusted skill promotion, Site Skill Card creation, Gate allowlist mutation, and a real Gate apply executor remain **NOT BUILT**.

Adjacent implementation status:

- Browser Operator Surface: **PARTIAL / VERIFIED TARGETED / PARKED**.
- SiteOps registry: **PARTIAL / VERIFIED TARGETED / DRY-RUN READY**.
- Browser Use-style persistent CDP/domain-skill/workflow-replay execution layer: **NOT BUILT**; inactive ChaseOS-native workflow cache foundation, replay-executor design, no-write implementation request, no-write implementation approval, disabled replay executor implementation, read-only execution-readiness preflight, reviewed local trial candidate selection, and no-write replay approval/idempotency contract are **COMPLETE TARGETED** sub-gates only.

---

*Graph links: [[ChaseOS-SiteOps]] - [[Browser-Operator-Surface]] - [[Browser-Operator-Surface-Operational-State]] - [[Browser-Autonomy-Policy]] - [[Autonomous-Operator-Runtime]] - [[Agent-Memory-Architecture]] - [[Feature-Fit-Register]] - [[Feature-Register]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
