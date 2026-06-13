# runtime/siteops/

Runtime-local substrate for **ChaseOS SiteOps**.

- Feature family: ChaseOS SiteOps
- Technical registry: Website Workflow Index
- User-facing tab: Site Skills
- CLI namespace: `chaseos siteops ...`

## Current status

This package is now a registry + production-scaffold + validation + dry-run runtime with a narrow SiteOps candidate replacement-approval writer.

It does **not** launch browsers, call provider APIs, mutate websites, write canonical knowledge, publish content, purchase anything, place trades, connect brokers, change billing, or change account settings.

## Layout

```text
runtime/siteops/
  registry.py
  models.py
  tenancy.py
  validator.py
  policy.py
  approvals.py
  audit.py
  budgets.py
  credentials.py
  browser_profiles.py
  runner.py
  catalog/*.yaml
  tenants/local.yaml
  schemas/*.schema.yaml
  registry/
    sites/*.json
    providers/*.json
    workflows/*.json
    skill_cards/*.json
```

## Commands

```bash
chaseos siteops list --json
chaseos siteops show canva.poster.magic_layers --json
chaseos siteops validate --json
chaseos siteops dry-run canva.poster.magic_layers \
  --input source_image_path=sample.png \
  --input edit_prompt="make it ChaseOS branded" \
  --json

chaseos siteops catalog list --json
chaseos siteops tenants list --json
chaseos siteops skills list --tenant local --json
chaseos siteops workflows dry-run perplexity.research.capture \
  --tenant local \
  --user local-user \
  --input query="ETH 4H setup" \
  --json
chaseos siteops runs list --tenant local --json
chaseos siteops approvals list --tenant local --json
chaseos siteops credentials check local-gemini-api-credential --tenant local --user local-user --json
chaseos siteops browser-profiles check local-user-canva-browser --tenant local --user local-user --json
chaseos siteops budgets check --provider gemini_image --tenant local --estimated-cost 0.0300 --json
chaseos siteops candidates request-promotion candidate_browser_runtime_20260430_022607_example-com \
  --tenant local \
  --workspace default \
  --user local-user \
  --write-approval-request \
  --json
chaseos siteops candidates apply-contract candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates gate-apply-design candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates gate-executor-spec candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates gate-allowlist-review candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates trusted-executor-design candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates executor-review-checklist candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates preimplementation-verifier candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates executor-implementation-design-review candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates executor-prewrite-audit-spec candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates inactive-artifact-validator candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates collision-policy-spec candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates approval-rebind-spec candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates bound-approval-request-spec candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates bound-approval-writer-design candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates bound-approval-writer-preflight candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates bound-approval-writer-implementation-request candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates bound-approval-writer-implementation-approval candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --decision approve \
  --json
chaseos siteops candidates bound-approval-writer-implementation candidate_browser_runtime_20260430_022607_example-com \
  --approval-id APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --write-replacement-approval \
  --json
chaseos siteops candidates replacement-approval-decision-consumption candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --decision approve \
  --write-approval-decision \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-preflight candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-implementation-request candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-implementation-approval candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --decision approve \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-implementation candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-live-gate-readiness candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-gate-allowlist-approval-request candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --requested-by local-user \
  --write-approval-request \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-gate-allowlist-decision-preflight candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --gate-approval-id GATE_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-plan candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --gate-approval-id GATE_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-application-design candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --gate-approval-id GATE_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-application-preflight candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --gate-approval-id GATE_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-application-write-guard candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --gate-approval-id GATE_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-writer-design candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --gate-approval-id GATE_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation-request candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --gate-approval-id GATE_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --json
chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation-approval candidate_browser_runtime_20260430_022607_example-com \
  --replacement-approval-id REPLACEMENT_APPROVAL_ID \
  --gate-approval-id GATE_APPROVAL_ID \
  --tenant local \
  --workspace default \
  --user local-user \
  --actor local-user \
  --decision approve \
  --json
```

## Seeded workflows

- `canva.poster.magic_layers`
- `tradingview.idea.capture`
- `tradingview.indicator.review`
- `gemini.image.edit`
- `perplexity.research.capture`

## Governance notes

Registry objects store operational knowledge and references only. They do not store secrets, session data, credential values, billing details, or account settings.

Dry-run plans expose:
- required inputs,
- planned steps,
- approval gates,
- blocked actions,
- output targets,
- writeback boundary.

Future execution must route through AOR/Gate and preserve quarantine-first capture and explicit approval before irreversible side effects.

## Production Scaffold

The local single-user path is represented as:

```yaml
tenant_id: local
workspace_id: default
user_id: local-user
```

This is compatibility mode of the production object model, not a separate architecture.

The scaffold includes scoped run/audit/approval lanes:

```text
07_LOGS/SiteOps-Runs/<tenant_id>/<workspace_id>/<run_id>.json
07_LOGS/SiteOps-Audits/<tenant_id>/<workspace_id>/<run_id>.jsonl
07_LOGS/SiteOps-Approvals/<tenant_id>/<workspace_id>/<approval_id>.json
```

Secrets, cookies, raw tokens, and browser session contents remain forbidden in YAML and audit logs.

Candidate promotion scope alignment:
- `request-promotion --write-approval-request` writes only scoped run/audit/approval metadata.
- `apply-contract` is non-mutating and cannot write trusted skills or SiteOps skill cards.
- `gate-apply-design` is non-mutating and keeps the future trusted-artifact apply operation denied-by-default until a separate Gate executor is approved.
- `gate-executor-spec` is non-mutating and describes the future executor preconditions/write plan while keeping the executor NOT BUILT and disabled.
- `gate-allowlist-review` is non-mutating and reviews the future Gate allowlist question while keeping `runtime/policy/gateway_allowlists.json` unchanged.
- `trusted-executor-design` is non-mutating and defines the future executor components, audit sequence, rollback plan, failure modes, and acceptance tests while keeping the executor NOT BUILT and disabled.
- Executor guard tests cover pending approval and legacy/unbound approval blockers before trusted-executor design can proceed to any write consideration.
- `executor-review-checklist` is non-mutating and exposes the no-write implementation review gate for any future trusted artifact executor pass.
- `06_AGENTS/SiteOps-Candidate-Executor-Implementation-Checklist.md` documents the same no-write implementation review gate.
- `preimplementation-verifier` is read-only and verifies checklist readiness, Gate denial, executor-entrypoint absence, trusted target absence, guard-test presence, and CLI contract presence before any future executor patch proposal.
- `preimplementation-verifier` negative tests cover pre-existing target artifacts, unexpected executor entrypoints, and missing CLI contract markers.
- `executor-implementation-design-review` is review-only and composes the verifier into a future patch-plan packet; every patch-plan item remains `allowed_in_this_pass=false`.
- `executor-prewrite-audit-spec` is no-write and defines the future executor audit event sequence, inactive-artifact contract, validation checks, and forbidden metadata fields without writing audit events or trusted artifacts.
- `inactive-artifact-validator` is no-write and validates proposed inactive Browser Skill and SiteOps Skill Card payloads in memory only.
- `collision-policy-spec` is no-write and defines fail-closed collision, overwrite, idempotency, and rollback policy for future inactive trusted artifact writes.
- `approval-rebind-spec` is no-write and defines how legacy-unbound approval artifacts must be superseded by future bound approval evidence without mutating legacy approval records.
- `bound-approval-request-spec` is no-write and defines the future bound replacement approval request artifact shape without writing approval records.
- `bound-approval-writer-design` is no-write and defines the future replacement approval writer sequence, target path preview, audit event contract, idempotency policy, and rollback policy without building/running the writer or writing approval records.
- `bound-approval-writer-preflight` is no-write and checks a future writer invocation for design readiness, scoped target absence, idempotency/recovery marker absence, secret-like field exclusion, audit contract posture, and Gate posture without writing approval records or markers.
- `bound-approval-writer-implementation-request` is no-write and returns an operator review packet for a future writer implementation pass without writing that packet, implementing the writer, or authorizing approval persistence.
- `bound-approval-writer-implementation-approval` is no-write and returns an approve/reject decision packet for a future writer implementation pass without writing the decision packet, implementing the writer, or persisting replacement approvals.
- `bound-approval-writer-implementation` defaults to dry-run and, only with `--write-replacement-approval`, writes a new pending replacement approval request plus scoped run/audit/idempotency/recovery evidence after implementation approval and preflight are ready. It does not consume approvals, mutate legacy approvals, write trusted artifacts, execute browsers, or write canonical state.
- `replacement-approval-decision-consumption` defaults to dry-run and, only with `--write-approval-decision`, writes approve/reject status plus scoped audit evidence for a pending bound replacement approval. Approved replacements report consumption-ready for a future trusted executor, but this command writes no consumption marker, trusted artifacts, browser state, activation, or canonical state.
- `trusted-inactive-artifact-writer-preflight` is no-write and checks approved bound replacement approval readiness, inactive payload validation, target path confinement/collision posture, and Gate posture before any future trusted inactive writer exists.
- `trusted-inactive-artifact-writer-implementation-request` is no-write and returns an operator review packet for a future trusted inactive writer implementation pass without writing that packet, consuming approval, writing trusted artifacts, mutating Gate policy, activating skills, executing browsers, enqueueing Agent Bus work, calling providers, or writing canonical state.
- `trusted-inactive-artifact-writer-implementation-approval` is no-write and returns an approve/reject packet for a future trusted inactive writer implementation pass. It can set `implementation_patch_allowed_next_pass=true` only when the request is ready and the operator decision is `approve`; it writes no approval record, consumes no approval, writes no trusted artifacts, and mutates no Gate/browser/Agent Bus/provider/activation/canonical state.
- `trusted-inactive-artifact-writer-implementation` is the bounded writer. It defaults to dry-run/blocked status and writes inactive-review Browser Skill + SiteOps Skill Card artifacts only with `--write-inactive-artifacts`, ready implementation approval/preflight posture, clear target paths, and Gate allowance. It does not consume replacement approvals, mutate Gate policy, activate skills, execute browsers, enqueue Agent Bus work, call providers, or write canonical state.
- `trusted-inactive-artifact-writer-live-gate-readiness` is no-write and reports whether the bounded writer is ready for a separate operator-reviewed Gate policy patch. It previews the Gate policy shape and fail-closed smoke command, but writes no artifacts, edits no Gate policy, consumes no approvals, activates no skills, executes no browsers, enqueues no Agent Bus work, calls no providers, and writes no canonical state.
- `trusted-inactive-artifact-writer-gate-allowlist-approval-request` previews by default and can write only a pending SiteOps approval request plus scoped audit event with `--write-approval-request`. It does not edit Gate policy, change gateway allowlists, write trusted artifacts, consume approvals, activate skills, execute browsers, enqueue Agent Bus work, call providers, or write canonical state.
- `trusted-inactive-artifact-writer-gate-allowlist-decision-preflight` is no-write and validates the Gate approval request status, request digest, scope, target paths/categories, current readiness, Gate denial, fail-closed smoke requirement, and no-mutation metadata before any future policy patch plan. It performs no policy edit, approval consumption, artifact write, browser execution, Agent Bus work, provider call, activation, or canonical writeback.
- `trusted-inactive-artifact-writer-gate-policy-patch-plan` is no-write and previews the exact runtime operation policy entry and gateway write-target category additions for the future Gate patch after approved decision-preflight evidence. It performs no policy edit, approval consumption, artifact write, browser execution, Agent Bus work, provider call, activation, or canonical writeback.
- `trusted-inactive-artifact-writer-gate-policy-patch-application-design` is no-write and designs the future explicit two-file Gate policy application transaction, including atomicity, rollback, and post-apply verification order. It performs no policy edit, approval consumption, artifact write, browser execution, Agent Bus work, provider call, activation, or canonical writeback.
- `trusted-inactive-artifact-writer-gate-policy-patch-application-preflight` is no-write and reads/parses current Gate files, records pre-patch digests, verifies the future operation/categories are absent, and previews rollback/audit shape before any future write pass. It performs no policy edit, approval consumption, rollback/audit artifact write, artifact write, browser execution, Agent Bus work, provider call, activation, or canonical writeback.
- `trusted-inactive-artifact-writer-gate-policy-patch-application-write-guard` is no-write and declares the future explicit `--apply-gate-policy-patch` flag, exact target files, digest requirements, rollback/audit requirements, and post-apply verification contract while keeping that write flag unsupported. It performs no policy edit, approval consumption, rollback/audit artifact write, artifact write, browser execution, Agent Bus work, provider call, activation, or canonical writeback.
- `trusted-inactive-artifact-writer-gate-policy-patch-writer-design` is no-write and designs the future explicit Gate policy patch writer, including required evidence, exact two-file scope, backup/rollback policy, atomic write sequence, and post-apply verification. It performs no policy edit, approval consumption, backup/rollback artifact write, trusted artifact write, browser execution, Agent Bus work, provider call, activation, or canonical writeback.
- `trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation-request` is no-write and packages the writer-design evidence into an operator implementation-request packet for a future Gate policy patch writer. The actual write flag remains unsupported and it performs no policy edit, approval consumption, implementation-request artifact write, backup/rollback artifact write, trusted artifact write, browser execution, Agent Bus work, provider call, activation, or canonical writeback.
- `trusted-inactive-artifact-writer-gate-policy-patch-writer-implementation-approval` is no-write and records approve/reject intent for the future Gate policy patch writer implementation. It keeps `--apply-gate-policy-patch` unsupported and performs no policy edit, approval consumption, implementation-approval artifact write, backup/rollback artifact write, trusted artifact write, browser execution, Agent Bus work, provider call, activation, or canonical writeback.
- Future replacement approval preview IDs are stable for the same tenant/workspace/user/candidate/source-approval tuple so repeated preflight/idempotency/recovery checks inspect the same target path.
- `approvals --include-activation-boundary` is read-only and projects activation-boundary readiness into the approval queue without activating skills, writing trusted artifacts, or mutating approvals.
- `approvals --include-bound-approval-request-spec` is read-only and projects the no-write bound replacement approval-request spec for each listed approval; it may identify legacy-unbound approvals that are ready for a separate future writer, but it does not write replacement approval records or mutate legacy approvals.
- `approvals --include-readiness-summary` is read-only and adds aggregate approval/provenance/apply-contract counts, plus executor-preflight, activation-boundary, and bound-approval-request-spec counts when those projections are requested.
- Live browser execution, skill activation, Agent Bus enqueue, provider calls, and canonical writeback remain not built.
