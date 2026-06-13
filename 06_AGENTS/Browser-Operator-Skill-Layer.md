---
title: Browser Operator Skill Layer
type: architecture
status: PARTIAL - BOSL scaffold plus SiteOps Gate-checked inactive writer, CDP governance, injected proof executor, and no-launch isolated launcher design
phase: Phase 9 - AOR / Browser Operator Surface skill layer
created: 2026-04-30
updated: 2026-05-02
runtime: Codex
knowledge_class: system-operational
---

# Browser Operator Skill Layer

> The Browser Operator Skill Layer (BOSL) is the governed recipe and learning layer for bounded browser work inside ChaseOS. It stores reusable browser interaction knowledge as reviewable skills, not as autonomous authority. BOSL sits above the existing Browser Operator Surface and below AOR policy, role cards, Gate rules, and operator approval.

## Status

This pass creates a foothold only:

- Architecture and policy documents.
- Machine-readable browser skill schema scaffolding.
- Runtime package for skill registry and validation.
- Shadow-plan runner for validating a BOSL skill without launching a browser.
- New BOSL shadow-run candidates now include validator-compatible machine candidate records while remaining untrusted and activation-blocked.
- Templates for browser run logs, skill candidates, and approved skill files.
- Untrusted candidate and browser-run log folders.
- One draft non-executable Excalidraw shadow skill.
- Read-only candidate storage reconciliation and SiteOps inspection via `runtime/browser_skills/candidates.py` and `chaseos siteops candidates list|show|preflight|request-promotion`.
- Scoped SiteOps candidate promotion request persistence via `runtime/siteops/candidate_promotions.py` and `chaseos siteops candidates request-promotion --tenant ... --user ... --write-approval`, which writes only `SiteOpsRun`, `SiteOpsAuditEvent`, and `ApprovalRequest` artifacts.
- Non-mutating scoped apply contracts via `chaseos siteops candidates apply-contract`.
- Denied-by-default Gate apply design previews via `chaseos siteops candidates gate-apply-design`.
- Fail-closed future executor specs via `chaseos siteops candidates gate-executor-spec`; this describes the future executor contract, exposes machine-readable executor preflight checks, and keeps the executor not built and disabled.
- Review-only Gate allowlist packets via `chaseos siteops candidates gate-allowlist-review`; this evaluates allowlist eligibility and risks without editing `runtime/policy/gateway_allowlists.json`.
- Design-only trusted executor packets via `chaseos siteops candidates trusted-executor-design`; this defines future executor components, audit sequencing, rollback behavior, failure modes, and acceptance tests without implementing the executor.
- Executor guard tests that keep the future trusted executor absent, Gate-denied, write-disabled, and non-mutating until a separate implementation and allowlist pass is intentionally approved.
- No-write executor implementation checklist CLI via `chaseos siteops candidates executor-review-checklist`; this defines required future preconditions, execution order, tests, audit events, rollback behavior, and denied effects before any trusted artifact executor can be built.
- Read-only preimplementation verifier via `chaseos siteops candidates preimplementation-verifier`; this aggregates checklist readiness, Gate denial, executor-entrypoint absence, target artifact absence, guard-test presence, and CLI contract presence before any executor patch is proposed.
- Review-only executor implementation design review via `chaseos siteops candidates executor-implementation-design-review`; this composes the verifier into a future patch plan while keeping implementation, Gate, trusted write, browser, provider, Agent Bus, activation, and canonical writeback authority false.
- No-write executor prewrite audit spec via `chaseos siteops candidates executor-prewrite-audit-spec`; this defines the future executor audit event sequence, inactive-artifact contract, validation checks, and forbidden metadata fields without writing audit events or trusted artifacts.
- No-write inactive artifact validator via `chaseos siteops candidates inactive-artifact-validator`; this validates proposed inactive Browser Skill and SiteOps Skill Card payloads in memory only.
- No-write collision policy spec via `chaseos siteops candidates collision-policy-spec`; this defines fail-closed collision, overwrite, idempotency, and rollback policy for future inactive trusted artifact writes without writing artifacts.
- No-write approval rebind spec via `chaseos siteops candidates approval-rebind-spec`; this defines future replacement approval requirements for legacy-unbound approvals without mutating the legacy approval or writing a replacement approval.
- No-write bound approval request spec via `chaseos siteops candidates bound-approval-request-spec`; this builds and validates the future replacement approval request artifact in memory only.
- No-write bound approval writer design via `chaseos siteops candidates bound-approval-writer-design`; this computes the future writer sequence, scoped target path preview, audit event contract, idempotency policy, and rollback policy without building or running the writer.
- No-write bound approval writer preflight via `chaseos siteops candidates bound-approval-writer-preflight`; this checks design readiness, target path posture, idempotency/recovery marker absence, secret-like field exclusion, and Gate posture without writing approval artifacts or markers.
- No-write bound approval writer implementation request via `chaseos siteops candidates bound-approval-writer-implementation-request`; this composes the writer preflight into an operator review packet for a future implementation pass without writing the packet or authorizing the writer.
- No-write bound approval writer implementation approval via `chaseos siteops candidates bound-approval-writer-implementation-approval`; this composes the implementation request into an approve/reject decision packet for a future writer implementation pass without writing the packet, implementing the writer, or persisting replacement approvals.
- Bounded bound approval writer implementation via `chaseos siteops candidates bound-approval-writer-implementation`; this defaults to dry-run and writes only a new pending replacement approval request plus scoped run/audit/idempotency/recovery evidence when `--write-replacement-approval` is supplied and preflight is ready.
- Decision-write-only replacement approval decision/consumption via `chaseos siteops candidates replacement-approval-decision-consumption`; this can approve/reject a bound replacement approval and report approved replacements as consumption-ready for a future executor, but it writes no consumption marker, trusted Browser Skill, SiteOps Skill Card, Gate policy, browser state, activation, or canonical writeback.
- No-write trusted inactive artifact writer preflight via `chaseos siteops candidates trusted-inactive-artifact-writer-preflight`; this checks the approved bound replacement approval, inactive artifact payloads, target path posture, and Gate posture without writing artifacts or consuming approvals.
- No-write trusted inactive artifact writer implementation request via `chaseos siteops candidates trusted-inactive-artifact-writer-implementation-request`; this packages preflight evidence for operator review without implementing the writer or writing any request/artifact/Gate/browser/Agent Bus/provider/canonical state.
- No-write trusted inactive artifact writer implementation approval via `chaseos siteops candidates trusted-inactive-artifact-writer-implementation-approval`; this composes the request into an approve/reject packet for a future writer implementation pass without writing the decision packet, consuming approvals, implementing the writer, or writing trusted artifacts.
- Gate-checked trusted inactive artifact writer implementation via `chaseos siteops candidates trusted-inactive-artifact-writer-implementation`; this writes inactive-review Browser Skill and SiteOps Skill Card artifacts only with explicit `--write-inactive-artifacts`, ready preflight, clear target paths, and Gate allowance, while preserving no approval consumption, Gate mutation, activation, browser execution, Agent Bus/provider call, or canonical writeback.
- No-write live Gate readiness packet via `chaseos siteops candidates trusted-inactive-artifact-writer-live-gate-readiness`; this reports readiness for a separate operator-reviewed Gate policy patch and fail-closed smoke while preserving no Gate mutation, artifact write, approval consumption, activation, browser execution, Agent Bus/provider call, or canonical writeback.
- Pending Gate allowlist approval request path via `chaseos siteops candidates trusted-inactive-artifact-writer-gate-allowlist-approval-request`; this previews by default and can write only a pending SiteOps approval request plus scoped audit event with `--write-approval-request`, while preserving no Gate mutation, trusted artifact write, approval consumption, activation, browser execution, Agent Bus/provider call, or canonical writeback.
- No-write Gate allowlist decision preflight via `chaseos siteops candidates trusted-inactive-artifact-writer-gate-allowlist-decision-preflight`; this validates Gate approval request status, request digest, scope, target paths/categories, current readiness, Gate denial, fail-closed smoke requirement, and no-mutation metadata before any policy patch plan while preserving no Gate mutation, trusted artifact write, approval consumption, activation, browser execution, Agent Bus/provider call, or canonical writeback.
- No-write Gate policy patch plan via `chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-plan`; this previews the exact `runtime/chaseos_gate.py` operation policy entry and `runtime/policy/gateway_allowlists.json` write-target category additions after approved decision-preflight evidence while preserving no Gate mutation, trusted artifact write, approval consumption, activation, browser execution, Agent Bus/provider call, or canonical writeback.
- No-write Gate policy patch application design via `chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-application-design`; this describes the future explicit Gate file write transaction, atomicity, rollback, and post-apply verification requirements while preserving no Gate mutation, trusted artifact write, approval consumption, activation, browser execution, Agent Bus/provider call, or canonical writeback.
- No-write Gate policy patch application preflight via `chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-application-preflight`; this reads/parses current Gate files, computes pre-patch digests, checks operation/category absence and exact desired entries, and previews rollback/audit shape while preserving no Gate mutation, trusted artifact write, approval consumption, activation, browser execution, Agent Bus/provider call, or canonical writeback.
- No-write Gate policy patch application write guard via `chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-application-write-guard`; this declares the future explicit `--apply-gate-policy-patch` guard, exact target files, digest/rollback requirements, and post-apply verification while keeping the write flag unsupported and preserving no Gate mutation, trusted artifact write, approval consumption, activation, browser execution, Agent Bus/provider call, or canonical writeback.
- No-write Gate policy patch writer design via `chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-writer-design`; this designs the future explicit Gate policy patch writer, backup/rollback policy, atomic two-file write sequence, and post-apply verification while preserving no Gate mutation, trusted artifact write, approval consumption, activation, browser execution, Agent Bus/provider call, or canonical writeback.
- No-write Gate policy patch writer implementation request via `chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation-request`; this packages the writer-design evidence into an operator request packet for a future Gate patch writer implementation while preserving no Gate mutation, trusted artifact write, approval consumption, implementation-request artifact write, activation, browser execution, Agent Bus/provider call, or canonical writeback.
- No-write Gate policy patch writer implementation approval via `chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation-approval`; this records approve/reject intent for a future Gate patch writer implementation while preserving no Gate mutation, trusted artifact write, approval consumption, implementation-approval artifact write, backup/rollback artifact write, activation, browser execution, Agent Bus/provider call, or canonical writeback.
- Stable bound replacement approval preview IDs now keep repeated writer preflight/idempotency/recovery checks on the same scoped target path for the same tenant/workspace/user/candidate/source-approval tuple.
- No-execution CDP design preflight via `runtime.browser_runtime.adapters.cdp_design`; this reviews proposed local-only/no-profile/no-raw-CDP boundaries and always leaves execution disabled.
- Declared-but-blocked CDP read-only proof Gate schema via `chaseos gate check-operation browser.cdp.read_only_proof --external-api browser.navigation --json`; this exposes `bosl.cdp_read_only_proof.v1` while returning denied and attempting no browser launch or CDP connection.
- No-execution CDP executor-spec via `chaseos runtime browser-cdp executor-spec`; this reports the injected CDP read-only proof executor contract while attempting no browser launch, CDP connection, approval lookup, trusted write, or canonical writeback.
- Request-only CDP approval artifacts via `chaseos runtime browser-cdp approval-request --write-approval-request`; this writes pending review records under `07_LOGS/Agent-Activity/_bosl_cdp_approvals/` and can structurally validate them without approval consumption or execution.
- No-execution CDP decision preflight via `chaseos runtime browser-cdp decision-preflight --gate-approval-id <id>`; this checks approval status, future idempotency-marker posture, and a bounded future write plan without consuming approval, writing a marker, launching a browser, connecting to CDP, or writing run evidence.
- No-execution CDP idempotency reservation spec via `chaseos runtime browser-cdp idempotency-reservation-spec --gate-approval-id <id>`; this returns the future marker path, marker record template, atomic create-new reservation rules, and blocked status without consuming approval, writing the marker, launching a browser, connecting to CDP, or writing run evidence.
- No-execution CDP executor dry-run via `chaseos runtime browser-cdp executor-dry-run --gate-approval-id <id>`; this returns the future executor sequence, stop conditions, artifact plan, and feature completion tracker without consuming approval, writing markers, launching a browser, connecting to CDP, or writing run evidence.
- No-execution CDP approval-decision policy via `chaseos runtime browser-cdp approval-decision-policy --gate-approval-id <id>`; this returns the future approval decision record template and consumption rules without writing a decision, consuming approval, writing markers, launching a browser, connecting to CDP, or writing run evidence.
- No-execution CDP approval decision consumer design via `chaseos runtime browser-cdp approval-decision-consumer-design --gate-approval-id <id>`; this returns the future single-use approval consumer algorithm, request/decision binding checks, marker-absence guard, sanitized consumption record template, and forbidden field policy without writing or consuming decisions, writing markers, launching a browser, connecting to CDP, or writing run evidence.
- No-write CDP atomic marker writer design via `chaseos runtime browser-cdp atomic-marker-writer-design --gate-approval-id <id>`; this returns the future exclusive-create marker write algorithm, path constraints, sanitized marker payload template, and failure/retry policy without consuming approval, creating marker directories, writing markers, launching a browser, connecting to CDP, or writing run evidence.
- No-launch CDP isolated browser launcher design via `chaseos runtime browser-cdp isolated-browser-launcher-design --gate-approval-id <id>`; this returns the throwaway-profile launch contract without creating a profile, spawning a browser, opening a CDP port, connecting to CDP, or writing proof evidence.
- No-launch CDP isolated launcher implementation preflight via `chaseos runtime browser-cdp isolated-launcher-implementation-preflight --gate-approval-id <id>`; this checks live launcher/client code presence and opaque implementation metadata without launching.
- Injected CDP proof executor tests prove bounded artifact writing with fake launcher/CDP-client collaborators, and the default live path has passed a Hermes local throwaway-profile activation smoke while remaining approval-gated.
- No-execution VincisOS readiness preflight via `runtime.browser_runtime.vincisos_preflight`; this blocks missing or remote targets, accepts only local port-scoped shadow targets, and attempts no browser launch, CDP connection, screenshot, profile/credential access, skill activation, trusted write, or canonical writeback.
- No-browser VincisOS static target proof via `runtime.browser_runtime.vincisos_static_target`; this serves `runtime/browser_runtime/test_targets/vincisos_shadow.html` through a temporary local server, verifies local socket reachability, shuts down the server, and writes no Browser Run or skill artifacts.
- Follow-on bounded browser runtime integration can now generate untrusted candidates from shadow run evidence under `03_INPUTS/Browser-Skill-Candidates/<domain>/` and update the Site Memory Ledger from ChaseOS-controlled runs only.

This pass does not create a new live browser-control runtime, does not expand the existing Browser Operator Surface authority, and does not authorize authenticated browsing, credential use, unrestricted CDP, shell execution, canonical writeback, or browser history import.

## Repo-Truth Placement

BOSL belongs primarily to Phase 9 AOR as a governed runtime support layer:

| Layer | BOSL relationship |
| --- | --- |
| Phase 8 Capture | Browser-derived content still routes through quarantine-first capture when content is captured. Skill candidates are untrusted intake material. |
| Phase 9 AOR | AOR remains the execution/control layer. BOSL supplies reusable skills only after validation and approval. |
| Browser Operator Surface | The existing bounded browser adapter/CLI/workflow remains the execution surface. BOSL does not replace it. |
| OSRIL / Runtime Shell | Future approval UI may display skill use, candidate promotion, and browser-run state. |
| Runtime Shell / Studio | Future operator views may inspect skills, candidates, site ledgers, run logs, and approval state. |
| Separate BOSL family | BOSL is useful enough to document as its own feature family, but it stays subordinate to AOR/Gate governance. |

Adjacent same-day architecture docs also exist:

- `06_AGENTS/Browser-Runtime-Skill-Memory.md` - umbrella docs-only pattern for browser run evidence becoming reviewed site knowledge.
- `06_AGENTS/Browser-Skill-Memory.md` - docs-only candidate/review/promotion memory lifecycle.

BOSL is the requested implementation foothold for schema, validator, templates, candidate folders, and draft skills. Storage reconciliation now keeps `03_INPUTS/Browser-Skill-Candidates/` as the canonical pending-review candidate home, with SiteOps exposing read-only inspection instead of a duplicate store.

## Core Definitions

### Browser Operator Adapter

A browser operator adapter is the bounded execution adapter that can navigate, inspect, screenshot, or interact with a browser under declared scope. In current repo truth, this maps to the parked Browser Operator Surface implementation under `runtime/operator_surface/browser/` and `runtime/operator_surface/adapters/browser_adapter.py`.

A future CDP adapter may exist, but it must still be a ChaseOS-controlled adapter with isolated profile rules, domain allowlists, action allowlists, audit, and approval gates.

### Browser Run

A browser run is one bounded browser session with:

- declared goal,
- declared mode (`shadow`, `read_only`, `approved_action`, or future equivalent),
- allowed domains,
- action plan,
- adapter/runtime identity,
- screenshot/data retention policy,
- audit output,
- explicit result status.

Browser runs write evidence to `07_LOGS/Browser-Runs/` only when a workflow explicitly declares that write target. Existing operator-surface audit artifacts may continue to use `07_LOGS/Agent-Activity/` and screenshots may continue to use `07_LOGS/Operator-Screenshots/`.

### Interaction Skill

An interaction skill is a reusable recipe for a repeatable UI interaction pattern, such as selecting a shape tool, opening a command palette, or dragging on a canvas using relative coordinates.

Interaction skills are not site-owner memory, account memory, or browser session memory. They must not store cookies, credentials, raw tokens, personal browser state, or user-specific screen coordinates.

### Domain Skill

A domain skill is a reusable recipe scoped to a website/domain or class of pages, such as `excalidraw.draw_basic_shape` or a future public-docs selector extraction recipe.

Domain skills require:

- domain and allowed domain declarations,
- preconditions,
- selectors or semantic targets,
- steps,
- wait conditions,
- verification criteria,
- secret policy,
- source runs,
- approval status,
- risk level,
- last verification timestamp if approved.

### Skill Candidate

A skill candidate is untrusted material generated from a run log, operator note, or manual observation. Candidates live under `03_INPUTS/Browser-Skill-Candidates/` and must be treated like quarantine material.

Candidates are data, not instructions. They may suggest a skill, but they cannot directly mutate trusted skill files.

### Skill Promotion

Skill promotion is the explicit operator/Gate-reviewed movement from candidate to trusted skill storage under `runtime/browser_skills/skills/`.

Promotion requirements:

- candidate reviewed by a human/operator-authorized pass,
- no secrets, cookies, session tokens, profile paths, or user-specific state,
- no raw absolute-only pixel coordinate recipes,
- domain and action scope declared,
- validator passes,
- approval status recorded,
- source run evidence linked,
- risk level declared.

### Site Memory Ledger

The site memory ledger is a future governed ledger of safe, non-secret website interaction facts, such as stable public selectors, page load expectations, or known UI labels.

Allowed ledger material:

- public selectors,
- semantic labels,
- known wait conditions,
- public route patterns,
- non-sensitive failure/recovery notes,
- relative-coordinate strategy notes for canvas-style tools.

Forbidden ledger material:

- cookies,
- session tokens,
- local storage dumps,
- browser profile paths,
- account identifiers unless explicitly redacted and required,
- private workspace names from third-party accounts,
- payment/account/security settings,
- raw absolute screen coordinates as the only locator.

### Frequently Visited Website Educator

The frequently visited website educator is a future learning pipeline that proposes skill candidates from operator-approved browser-run logs. It must not scrape full browser history or personal profiles.

Safe first form:

- operator manually selects run logs or sites for analysis,
- candidate output goes to `03_INPUTS/Browser-Skill-Candidates/`,
- trusted skill files are not mutated directly,
- validator and human review are required before promotion.

Current first form:

- `runtime/browser_runtime/candidates.py` builds validator-compatible untrusted candidate material from a Browser Run Result.
- `runtime/browser_runtime/site_memory.py` updates `07_LOGS/Site-Activity/site-memory-ledger.json` and `06_AGENTS/Site-Memory-Ledger.md`.
- `runtime/browser_runtime.smoke` proves the path with `example.com` in shadow mode.
- `runtime/browser_skills/candidates.py` scans candidate files as redacted records and exposes storage reconciliation for SiteOps.
- `chaseos siteops candidates list|show|preflight|request-promotion|apply-contract|gate-apply-design|gate-executor-spec|gate-allowlist-review|trusted-executor-design|executor-review-checklist|preimplementation-verifier|executor-implementation-design-review|executor-prewrite-audit-spec|inactive-artifact-validator|collision-policy-spec|approval-rebind-spec|bound-approval-request-spec|bound-approval-writer-design|bound-approval-writer-preflight|bound-approval-writer-implementation-request|bound-approval-writer-implementation-approval|bound-approval-writer-implementation|replacement-approval-decision-consumption|trusted-inactive-artifact-writer-preflight|trusted-inactive-artifact-writer-implementation-request|trusted-inactive-artifact-writer-implementation-approval|trusted-inactive-artifact-writer-implementation|trusted-inactive-artifact-writer-live-gate-readiness|trusted-inactive-artifact-writer-gate-allowlist-approval-request|trusted-inactive-artifact-writer-gate-allowlist-decision-preflight|trusted-inactive-artifact-writer-gate-policy-patch-plan|trusted-inactive-artifact-writer-gate-policy-patch-application-design|trusted-inactive-artifact-writer-gate-policy-patch-application-preflight|trusted-inactive-artifact-writer-gate-policy-patch-application-write-guard|trusted-inactive-artifact-writer-gate-policy-patch-writer-design|trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation-request|trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation-approval` inspects candidates, writes scoped approval request artifacts only when explicitly requested, previews future Gate apply requirements, describes the future executor contract with read-only secret/session exclusion recheck status, reviews the future Gate allowlist question, defines the future executor design, exposes no-write implementation review gates, verifies preimplementation guard state, returns a no-authority implementation patch plan, defines no-write prewrite audit/inactive-artifact contracts, validates proposed inactive artifacts in memory only, defines fail-closed collision/overwrite/idempotency/rollback policy, defines legacy-approval supersession policy, validates the future bound replacement approval request in memory, designs and preflights the replacement approval writer, returns no-write operator implementation request/approval packets, can write only the pending replacement approval evidence bundle behind an explicit flag, can decide the bound replacement approval only when explicitly requested, verifies the future trusted inactive writer preflight, packages no-write trusted inactive writer implementation request/approval packets, implements a Gate-checked inactive writer behind explicit flags, previews live Gate readiness without mutating policy, can write a pending Gate allowlist approval request only behind an explicit flag, validates Gate approval decision readiness without consuming it, previews an exact Gate policy patch plan without applying it, designs the future Gate patch application transaction without applying it, preflights current Gate files and rollback/audit shape before that future transaction, declares the future Gate patch write guard while keeping its write flag unsupported, designs the future explicit Gate patch writer without implementing it, packages its implementation request, records no-write implementation approval intent, and still blocks promotion, activation, browser execution, trusted skill writes unless Gate-approved, SiteOps skill-card writes unless Gate-approved, Gate allowlist edits, Agent Bus enqueue, provider calls, and raw-content exposure.
- `runtime/siteops/tests/test_candidate_promotions.py` now includes guard tests for the future trusted executor entrypoint, pending/unbound approval blockers, Gate-denied operation, unimplemented write plan, and absent target artifacts.
- `06_AGENTS/SiteOps-Candidate-Executor-Implementation-Checklist.md` records the no-write review checklist and `chaseos siteops candidates executor-review-checklist` exposes it as machine-readable runtime output.
- `06_AGENTS/SiteOps-Candidate-Executor-Preimplementation-Verifier.md` records the read-only go/no-go verifier before any future executor patch proposal.
- `06_AGENTS/SiteOps-Candidate-Executor-Implementation-Design-Review.md` records the review-only implementation-shape packet for a future executor patch.
- `06_AGENTS/SiteOps-Candidate-Executor-Prewrite-Audit-Spec.md` records the no-write future audit event and inactive-artifact contract.
- `06_AGENTS/SiteOps-Candidate-Inactive-Artifact-Validator.md` records the no-write inactive Browser Skill and SiteOps Skill Card payload validator.
- `06_AGENTS/SiteOps-Candidate-Executor-Collision-Policy-Spec.md` records the no-write collision, overwrite, idempotency, and rollback policy.
- `06_AGENTS/SiteOps-Candidate-Executor-Approval-Rebind-Spec.md` records the no-write legacy approval rebind/supersession policy.
- `06_AGENTS/SiteOps-Candidate-Executor-Bound-Approval-Request-Spec.md` records the no-write future replacement approval request artifact contract.
- `06_AGENTS/SiteOps-Candidate-Executor-Bound-Approval-Writer-Design.md` records the no-write future replacement approval writer design.
- `06_AGENTS/SiteOps-Candidate-Bound-Approval-Writer-Preflight.md` records the no-write future writer invocation preflight.
- `06_AGENTS/SiteOps-Candidate-Bound-Approval-Writer-Implementation-Request.md` records the no-write operator implementation request packet for a future writer implementation pass.
- `06_AGENTS/SiteOps-Candidate-Bound-Approval-Writer-Implementation.md` records the bounded replacement approval writer implementation.
- `06_AGENTS/SiteOps-Candidate-Replacement-Approval-Decision-Consumption.md` records the decision-write-only replacement approval decision/consumption path.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Preflight.md` records the no-write trusted inactive artifact writer preflight.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Implementation-Request.md` records the no-write trusted inactive writer implementation request packet.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Implementation-Approval.md` records the no-write trusted inactive writer implementation approval packet.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Implementation.md` records the Gate-checked bounded inactive artifact writer implementation.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Live-Gate-Readiness.md` records the no-write live Gate readiness packet.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Gate-Allowlist-Approval-Request.md` records the bounded pending approval-request path for the future Gate allowlist patch.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Gate-Allowlist-Decision-Preflight.md` records the no-write decision preflight for that Gate approval request.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Gate-Policy-Patch-Plan.md` records the no-write exact Gate policy patch plan for the future inactive trusted writer allowlist.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Gate-Policy-Patch-Application-Design.md` records the no-write future Gate policy patch application design.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Gate-Policy-Patch-Application-Preflight.md` records the no-write current-file/digest preflight for the future Gate policy patch application.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Gate-Policy-Patch-Application-Write-Guard.md` records the no-write write-guard contract for the future Gate policy patch application.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Gate-Policy-Patch-Writer-Design.md` records the no-write writer design for the future explicit Gate policy patch writer.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Gate-Policy-Patch-Writer-Implementation-Request.md` records the no-write implementation request packet for the future explicit Gate policy patch writer.
- `06_AGENTS/SiteOps-Candidate-Trusted-Inactive-Artifact-Writer-Gate-Policy-Patch-Writer-Implementation-Approval.md` records the no-write implementation approval packet for the future explicit Gate policy patch writer.
- `06_AGENTS/SiteOps-Candidate-Executor-Feature-Completion-Tracker.md` tracks when this feature is actually done.
- `06_AGENTS/Browser-CDP-Adapter-Design.md` records the no-execution CDP adapter boundary, and `runtime.browser_runtime.adapters.cdp_design` exposes a review-only preflight packet without connecting to CDP.
- `runtime/chaseos_gate.py` declares `browser.cdp.read_only_proof` as approval-required and exposes `bosl.cdp_read_only_proof.v1` for schema inspection only.
- `runtime/browser_runtime/cdp_executor_spec.py` exposes a no-execution executor-spec packet for future CDP read-only proof work.
- `runtime/browser_runtime/cdp_executor_spec.py` also writes and validates pending CDP approval request records without executing or consuming approval.
- `runtime/browser_runtime/cdp_executor_spec.py` exposes a no-execution CDP idempotency reservation spec that computes the future marker contract without writing it.
- `runtime/browser_runtime/cdp_executor_spec.py` exposes a no-execution CDP executor dry-run plan that computes future sequence, stop conditions, and artifact targets without executing.
- `runtime/browser_runtime/cdp_executor_spec.py` exposes a no-execution CDP approval-decision policy that defines future decision record and consumption rules without writing or consuming decisions.
- `runtime/browser_runtime/cdp_executor_spec.py` exposes a no-execution CDP approval decision consumer design that defines future single-use consumption, marker-absence, and forbidden output-field rules without consuming decisions.
- `runtime/browser_runtime/cdp_executor_spec.py` exposes a no-write CDP atomic marker writer design that defines future marker writer preconditions without writing markers.
- `runtime/browser_runtime/cdp_executor_spec.py` exposes a no-launch CDP isolated browser launcher design that defines future local-only throwaway-profile launch preconditions without spawning a browser.
- `runtime/browser_runtime/cdp_executor_spec.py` exposes a no-launch isolated launcher implementation preflight for the current `runtime.browser_runtime.cdp_live` launcher/client path.
- `runtime/browser_runtime/cdp_executor_spec.py` exposes an injected CDP read-only proof executor used by tests and a default live path that blocks before execution when no Chromium-compatible executable is available; the current host has activation evidence from the Hermes 2026-05-02 smoke.
- The trusted registry under `runtime/browser_skills/skills/` remains unchanged.

Validated continuation:

- Candidate listing, storage reconciliation, promotion preflight, scoped promotion request, scoped approval persistence, apply-contract, gate-apply-design, gate-executor-spec, gate-allowlist-review, trusted-executor-design, executor-review-checklist, and preimplementation-verifier paths have focused runtime/CLI coverage.
- Executor guard tests now protect the disabled trusted-artifact boundary, including pending/unbound approval blockers, before any future implementation pass can proceed.
- Preimplementation-verifier hardening tests now cover pre-existing target artifacts, unexpected executor entrypoints, and missing CLI contract markers.
- Executor implementation design-review tests cover ready/no-authority, pending-approval blocked, and CLI non-mutating states.
- Executor prewrite audit-spec tests cover ready/no-authority, pending-approval blocked, and CLI non-mutating states.
- Inactive artifact validator tests cover ready/no-authority, pending-approval blocked, and CLI non-mutating states.
- Collision policy spec tests cover ready/no-authority, pre-existing target collision, pending-approval blocked, and CLI non-mutating states.
- Approval rebind spec tests cover legacy-unbound replacement-required, bound-match not-required, and CLI non-mutating states.
- Bound approval request spec tests cover future replacement request artifact validation and CLI non-mutating states.
- Bound approval writer design tests cover ready/no-write, pending-approval blocked, and CLI non-mutating states.
- CDP design preflight, Gate, request-artifact, executor-spec, decision-preflight, idempotency-reservation, executor dry-run, approval-decision policy, approval decision consumer design, atomic marker writer design, isolated launcher design, isolated launcher implementation preflight, live environment blocker, and injected executor tests now protect the browser-control boundary from remote endpoints, real profiles, credentials, cookies, raw CDP, forbidden CDP actions, trusted writes, canonical writeback, unapproved browser launch, and unapproved CDP proof execution.
- Scoped approval persistence is intentionally limited to `07_LOGS/SiteOps-Runs/`, `07_LOGS/SiteOps-Audits/`, and `07_LOGS/SiteOps-Approvals/`; it does not write trusted skills or SiteOps skill cards.
- The next implementation pass must remain a separately approved executor/allowlist decision before any trusted Browser Skill or SiteOps Skill Card write is implemented; the checklist note is review-only and does not grant implementation or Gate authority.

## Allowed Browser Data

Allowed in skills, candidates, and ledgers:

- public domain or origin,
- public URL pattern when needed,
- CSS selector candidates,
- ARIA role/name hints,
- visible labels,
- high-level page state descriptions,
- relative coordinate strategies (`x_pct`, `y_pct`, bounding-box-relative),
- wait conditions,
- non-sensitive error patterns,
- screenshot references after retention/redaction review,
- run IDs and audit artifact paths.

## Forbidden Browser Data

Forbidden in skills, candidates, ledgers, and shared logs:

- credentials,
- passwords,
- API keys,
- cookies,
- session tokens,
- bearer tokens,
- authorization headers,
- local storage or indexedDB dumps,
- browser profile/user-data paths,
- raw Chrome profile state,
- full browser history imports without explicit approval,
- account-specific private workspace state,
- payment, banking, email, Discord, GitHub, Outlook, or other authenticated account data,
- raw absolute-only pixel coordinates as the sole interaction locator.

## Relationship to Phase 8 Capture

Phase 8 remains the content capture layer. Browser page content captured during a run must route to quarantine-first intake through the capture pipeline, not directly to canonical knowledge.

BOSL adds a different artifact class:

- browser content capture -> `03_INPUTS/00_QUARANTINE/`
- browser skill candidate -> `03_INPUTS/Browser-Skill-Candidates/`
- browser run log -> `07_LOGS/Browser-Runs/`
- trusted browser skill -> `runtime/browser_skills/skills/`

Skill candidates are not source notes and are not trusted instructions.

## Relationship to Phase 9 AOR

AOR remains the authority boundary. BOSL does not run workflows by itself.

Future browser-skill execution should follow this order:

1. AOR resolves workflow manifest.
2. AOR resolves task type and role card.
3. Browser policy and allowed domains are checked.
4. BOSL registry resolves approved skill.
5. BOSL validator confirms the skill file is safe.
6. Browser adapter executes only allowed steps.
7. Browser run log and audit artifacts are written.
8. Any skill candidate output remains untrusted until promoted.

## Why BOSL Is Not Unrestricted OpenClaw-Style Control

BOSL is not a general browser agent and not an unrestricted runtime owner.

It cannot:

- choose arbitrary websites,
- import browser history,
- connect to logged-in personal Chrome,
- read cookies or session state,
- use credentials,
- expose CDP broadly,
- run shell commands,
- auto-promote knowledge,
- mutate canonical vault state,
- write trusted skill files from a browser run.

BOSL provides skill files and validation rules. AOR, role cards, policy docs, and Gate rules decide whether anything may execute.

## Initial File Map

```text
06_AGENTS/
  Browser-Operator-Skill-Layer.md
  Browser-Operator-Policy.md

runtime/browser_skills/
  schemas/browser_skill.schema.yaml
  skills/README.md
  skills/excalidraw/draw_basic_shape.yaml
  registry.py
  shadow_runner.py
  validator.py

03_INPUTS/
  Browser-Skill-Candidates/README.md

07_LOGS/
  Browser-Runs/README.md

05_TEMPLATES/
  Browser-Run-Log-Template.md
  Browser-Skill-Candidate-Template.md
  Browser-Skill-Template.md
```

## Excalidraw Shadow Test Plan

Purpose: prove the BOSL skill shape can describe a canvas interaction without credentials, login, raw absolute pixels, or canonical writeback.

Initial target:

- Domain: `excalidraw.com`
- Account: none
- Mode: shadow
- Browser profile: isolated disposable profile only
- Output: browser run log plus optional proof evidence
- Writeback: no canonical writeback

Shadow-plan sequence:

1. Validate the `excalidraw.draw_basic_shape` skill file.
2. Confirm no account/login is required.
3. Confirm no credentials, cookies, session tokens, real profile, canonical writeback, or raw absolute-only pixels are declared.
4. Plan navigation to `https://excalidraw.com/` without launching a browser.
5. Plan selector click, relative-canvas drag, and verification steps without executing them.
6. Write a non-sensitive text proof artifact.
7. Write run log to `07_LOGS/Browser-Runs/`.
8. Write an untrusted candidate to `03_INPUTS/Browser-Skill-Candidates/`.

Verified shadow-plan proof:

- Runner: `python -m runtime.browser_skills.shadow_runner excalidraw.draw_basic_shape`
- Latest validator-compatible run log: `07_LOGS/Browser-Runs/bosl_shadow_2026-04-30T061019.532006z0000_excalidraw-draw-basic-shape.json`
- Latest validator-compatible untrusted candidate: `03_INPUTS/Browser-Skill-Candidates/bosl-shadow-2026-04-30t061019-532006z0000-excalidraw-draw-basic-shape-candidate.md`
- Latest Agent Activity: `07_LOGS/Agent-Activity/bosl-shadow-2026-04-30t061019-532006z0000-excalidraw-draw-basic-shape.md`

New shadow candidates generated after the 2026-04-30 normalization pass preflight as validator-compatible untrusted candidates. Older Excalidraw shadow candidates remain historical proof artifacts and may fail candidate preflight because their machine block was metadata-only.

This is not a live Excalidraw automation proof. No browser was launched, no network request was made, and no canvas was mutated.

## Current Status

PARTIAL / VERIFIED SHADOW-PLAN + BOUNDED CDP READ-ONLY PROOF PATH. BOSL is documented and scaffolded, the Excalidraw skill can be validated into a non-executing shadow proof, and the browser CDP read-only proof operation now has declared Gate schema, request-only approval artifacts, executor spec, decision preflight, idempotency reservation spec, executor dry-run plan, approval-decision policy, approval decision consumer design, atomic marker writer design, isolated launcher design, isolated launcher implementation preflight, injected proof-executor tests, and a default live code path with Hermes activation evidence for the local throwaway-profile smoke. It is not production-ready unrestricted browser automation, not a live Excalidraw proof, not a promoted skill-learning loop, and not an account automation system.

## Graph Links

[[Browser-Runtime-Skill-Memory]] | [[Browser-Skill-Memory]] | [[Browser-CDP-Adapter-Design]] | [[Browser-CDP-Feature-Readiness]] | [[Browser-Operator-Surface]] | [[Browser-Autonomy-Policy]] | [[Browser-Operator-Surface-Operational-State]] | [[Autonomous-Operator-Runtime]] | [[Connector-Capture-Architecture]] | [[Ingestion-Architecture]] | [[Agent-Security-Model]] | [[Permission-Matrix]] | [[Trust-Tiers]]

*Graph links: [[OpenClaw-Runtime-Profile]]*
