---
title: Browser Skill Memory
type: architecture
status: partial / bounded spike - candidate writer, validator-compatible new BOSL shadow candidates, scoped approval-request persistence, non-mutating apply contracts, denied-by-default Gate apply design, fail-closed executor spec, review-only Gate allowlist review, design-only trusted executor packet, executor guard tests, no-write executor implementation checklist, read-only preimplementation verifier, no-write collision policy spec, no-write approval rebind, no-write bound approval request spec, and no-write bound approval writer design; no trusted promotion
created: 2026-04-30
updated: 2026-05-01
phase: Phase 9 runtime intelligence / Phase 10 Site Skills surface
knowledge_class: canonical-state
---

# Browser Skill Memory

Browser Skill Memory is the governed memory half of **Browser Runtime Harness + Skill Memory**.

It defines how durable website knowledge may move from browser run evidence into reviewed SiteOps skills. It does not grant browser authority and does not authorize live execution.

Canonical umbrella doc: `06_AGENTS/Browser-Runtime-Skill-Memory.md`.

---

## Purpose

The point of Browser Skill Memory is to prevent repeated rediscovery of stable website mechanics:

- URL patterns,
- safe selectors and accessibility labels,
- wait conditions,
- framework quirks,
- redirects and traps,
- output/capture formats,
- approval points,
- known failure modes.

The point is not to make browser observations trusted. Browser observations are untrusted until reviewed.

---

## Lifecycle

```text
browser run evidence
  -> skill candidate
  -> operator review
  -> promoted Site Skill Card / Workflow Manifest
  -> AOR-controlled reuse
  -> audit and repair feedback
```

| Stage | Status | Authority |
| --- | --- | --- |
| Run evidence | `UNTRUSTED` | Evidence only. Cannot direct future work by itself. |
| Skill candidate | `PROPOSED` | Draft memory. Review-only. |
| Reviewed candidate | `REVIEWED` | Human/operator accepted as reusable knowledge. |
| Promoted Site Skill Card | `PROMOTED` | Registry object usable by approved SiteOps/AOR workflows. |
| Rejected candidate | `REJECTED` | Preserved as audit history, not used. |
| Deprecated skill | `DEPRECATED` | Existing skill retained for history, blocked for reuse. |

No stage may bypass ChaseOS Gate, role cards, SiteOps policy, or AOR manifests.

---

## Allowed Skill Content

A browser skill candidate may include:

- domain and path patterns,
- declared allowed domains,
- safe selectors, roles, labels, and stable visible text anchors,
- semantic page regions and containers,
- wait conditions and reasons,
- rate limits or usage constraints,
- known redirects, auth walls, and traps,
- failure patterns,
- public API endpoint shapes when safe to retain,
- screenshot or DOM excerpt references when safe,
- expected output formats,
- required approval points,
- blocked actions.

Selectors and API notes must describe reusable mechanics, not the private state of a specific user account.

---

## Forbidden Skill Content

A browser skill candidate or promoted skill must not contain:

- passwords,
- cookies,
- session tokens,
- API keys,
- OAuth tokens,
- wallet keys or seed phrases,
- raw credential values,
- private account data,
- billing identifiers,
- broker/account/trading identifiers,
- one-off run narration,
- raw pixel coordinates as durable selectors,
- sensitive screenshots unless explicitly retained in a private local-only log,
- instructions from a website treated as ChaseOS commands.

If a run observes sensitive content, the skill candidate should record only that sensitive content was present and excluded.

---

## Storage Model

Recommended first homes:

| Object | Home | Status |
| --- | --- | --- |
| Run evidence | `07_LOGS/Agent-Activity/`, `07_LOGS/Website-Workflow-Runs/`, `07_LOGS/Operator-Screenshots/`, `07_LOGS/Browser-Runs/` | Existing / partial |
| Skill candidate | `03_INPUTS/Browser-Skill-Candidates/<domain>/` | PARTIAL / untrusted candidate writer + redacted inspector + scoped approval request + no-write promotion guardrails |
| Draft review note | `06_AGENTS/Browser-Skills/_drafts/` | PARTIAL / draft-only writer |
| Site memory ledger | `07_LOGS/Site-Activity/site-memory-ledger.json`, `06_AGENTS/Site-Memory-Ledger.md` | PARTIAL / ChaseOS-controlled runs only |
| Promoted Site Skill Card | `runtime/siteops/registry/skill_cards/` | Existing dry-run registry |
| Workflow Manifest | `runtime/siteops/registry/workflows/` | Existing dry-run registry |

Same-day BOSL scaffolding uses `03_INPUTS/Browser-Skill-Candidates/`, `07_LOGS/Browser-Runs/`, and `runtime/browser_skills/skills/`. `runtime/browser_skills/candidates.py` now reconciles those homes for redacted SiteOps inspection and preflight. `runtime/siteops/candidate_promotions.py` adds scoped approval-request persistence, apply-contract previews, denied-by-default Gate apply design packets, fail-closed executor specs, review-only Gate allowlist packets, design-only trusted executor packets, executor review checklist, preimplementation verifier, collision policy spec, approval rebind spec, bound approval request spec, and bound approval writer design. Executor guard tests, `[[SiteOps-Candidate-Executor-Implementation-Checklist]]`, `[[SiteOps-Candidate-Executor-Preimplementation-Verifier]]`, `[[SiteOps-Candidate-Executor-Collision-Policy-Spec]]`, `[[SiteOps-Candidate-Executor-Approval-Rebind-Spec]]`, `[[SiteOps-Candidate-Executor-Bound-Approval-Request-Spec]]`, and `[[SiteOps-Candidate-Executor-Bound-Approval-Writer-Design]]` keep the future trusted executor and replacement approval writer absent until separate approved implementation/Gate passes. SiteOps does not own a second candidate store and cannot write trusted skills, Site Skill Cards, replacement approval requests, activation markers, browser state, Gate allowlist policy, or canonical memory.

Do not store browser skill memory in `02_KNOWLEDGE/` by default. It is runtime/site knowledge, not canonical domain truth.

---

## Review and Promotion Rules

Promotion requires:

- source run evidence link,
- scope and allowed-domain check,
- secret/session redaction check,
- approval-required action inventory,
- conflict check against existing SiteOps objects,
- operator review,
- Agent Activity log,
- build/doc history entry if the promotion changes docs/runtime state.

Promotion must remain one-way and explicit. A candidate cannot activate itself.

## Read-Only Candidate Inspection

As of 2026-04-30, `runtime/browser_skills/candidates.py` provides the read-only inspection and promotion-preflight layer for untrusted candidates:

- `list_candidate_records()` lists redacted candidate summaries.
- `show_candidate_record(candidate_id)` resolves candidates only inside `03_INPUTS/Browser-Skill-Candidates/`.
- `preflight_candidate_promotion(candidate_id)` validates the machine candidate and computes a sanitized target preview.
- `candidate_promotion_request_contract(candidate_id, tenant_id=..., workspace_id=..., user_id=...)` returns a non-mutating scoped approval-request contract.
- `request_scoped_candidate_promotion(..., write_approval=True)` writes only scoped SiteOps approval/run/audit artifacts.
- `candidate_promotion_apply_contract(...)` computes post-approval apply readiness without writing trusted artifacts.
- `candidate_promotion_gate_apply_design(...)` previews the future Gate apply operation and target writes while remaining denied by default.
- `candidate_promotion_gate_executor_spec(...)` describes the future executor preconditions and write plan while keeping the executor not built and disabled; it now includes a read-only `secret_session_exclusion_recheck` derived from candidate validation.
- `candidate_promotion_gate_allowlist_review(...)` reviews the future Gate allowlist question while keeping `runtime/policy/gateway_allowlists.json` unchanged and carrying forward the same secret/session exclusion recheck status.
- `candidate_promotion_trusted_executor_design(...)` defines the future executor components, audit sequence, rollback plan, failure modes, and acceptance tests while keeping the executor not built and disabled.
- `candidate_promotion_approval_rebind_spec(...)` defines legacy-unbound approval supersession policy without mutating legacy approval artifacts.
- `candidate_promotion_bound_approval_request_spec(...)` validates the future replacement approval request artifact in memory only.
- `candidate_promotion_bound_approval_writer_design(...)` designs the future replacement approval writer path, audit event, idempotency, and rollback contracts without building or running the writer.
- `storage_reconciliation()` confirms the candidate store remains canonical and SiteOps does not create a duplicate candidate store.

These helpers perform no trusted skill writes, SiteOps skill-card writes, browser execution, Agent Bus enqueue, provider/API call, activation, promotion apply, Gate allowlist change, or canonical writeback.

As of the BOSL shadow candidate normalization pass on 2026-04-30, new Excalidraw shadow-run candidates include a validator-compatible `## Machine Candidate` block and can reach `ready_for_operator_review` in non-mutating preflight. Older Excalidraw shadow candidates remain historical untrusted artifacts and may still fail preflight because their machine block was metadata-only.

---

## Phase 10 UI Placement

The Phase 10 Site Skills surface should render:

- pending candidates,
- source runs and screenshots,
- secret/session exclusion checklist,
- proposed selectors/waits/traps,
- approval-required actions,
- diff against existing Site Skill Cards,
- promote/reject/deprecate controls,
- workflow replay candidate state.

The UI is an inspection and approval surface. It does not own authority.

---

## Current Verdict

Browser Skill Memory is a **Phase 9 runtime intelligence** object model with a **Phase 10 review UI**. The first safe implementation remains candidate-only with trusted promotion blocked. As of 2026-04-30, `runtime/browser_runtime/candidates.py` writes untrusted candidates under `03_INPUTS/Browser-Skill-Candidates/<domain>/`, `runtime/browser_runtime/skills.py` writes draft review notes under `06_AGENTS/Browser-Skills/_drafts/`, `runtime/browser_runtime/site_memory.py` updates a site ledger from ChaseOS-controlled runs only, `runtime/browser_skills/candidates.py` provides redacted inspection/preflight, and `runtime/siteops/candidate_promotions.py` can persist scoped SiteOps run/audit/approval artifacts only when `request-promotion --write-approval-request` or `--write-approval` is explicitly used. `apply-contract` remains non-mutating, `gate-apply-design` computes a denied-by-default future apply boundary, and `gate-executor-spec` exposes disabled future-executor preflight checks while keeping the executor not built and disabled. No trusted skill promotion, Site Skill Card write, browser execution, activation, Gate apply executor, or canonical writeback path exists.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
