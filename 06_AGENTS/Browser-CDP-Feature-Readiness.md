---
title: Browser CDP Feature Readiness
type: readiness-tracker
status: IMPLEMENTED + OPERATIONALLY ACTIVATED - bounded approved read-only CDP proof executor passed local throwaway-profile smoke
created: 2026-05-01
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter / BOSL
runtime: Hermes
---

# Browser CDP Feature Readiness

This tracker separates Browser CDP implementation readiness from local machine
smoke availability. The bounded feature path is implemented behind explicit
approval, atomic idempotency, isolated launch, local CDP, and proof-artifact
writeback. On this WSL host, operational environment activation is now complete
through a user-local Chromium-compatible executable discovered as `chromium`.

## Current Verdict

| Feature Slice | Status | Evidence |
| --- | --- | --- |
| CDP design preflight | VERIFIED / NO-EXECUTION | `runtime.browser_runtime.adapters.cdp_design.evaluate_cdp_adapter_design(...)` |
| Gate schema declaration | VERIFIED / DENIED BY DEFAULT | `browser.cdp.read_only_proof`, `bosl.cdp_read_only_proof.v1` |
| Approval request artifact writer | VERIFIED / REQUEST ONLY | `chaseos runtime browser-cdp approval-request --write-approval-request` |
| Approval decision writer | VERIFIED / OPERATOR DECISION ARTIFACT | `chaseos runtime browser-cdp approval-decision --write-approval-decision --decision approved` |
| Approval artifact structural validation | VERIFIED | `validate_cdp_read_only_approval_artifact(...)` |
| Approval decision consumer | IMPLEMENTED / SINGLE-USE | `execute_cdp_read_only_proof(...)` consumes only approved, matching artifacts. |
| Atomic idempotency marker writer | IMPLEMENTED / CREATE-NEW-ONLY | `_write_cdp_idempotency_marker(...)`; duplicate markers block execution. |
| Isolated browser launcher | IMPLEMENTED / THROWAWAY PROFILE | `runtime.browser_runtime.cdp_live.IsolatedBrowserLauncher`; no real profile use. |
| Isolated launcher implementation preflight | VERIFIED / NO LAUNCH | `chaseos runtime browser-cdp isolated-launcher-implementation-preflight --gate-approval-id <id>` |
| Local CDP client/socket | IMPLEMENTED / LOCAL-ONLY | `runtime.browser_runtime.cdp_live.MinimalCDPClient`; bounded page navigate/read/screenshot path. |
| Proof artifact writer | IMPLEMENTED / DECLARED TARGETS ONLY | Browser run log, Agent Activity log, screenshot, DOM JSON, and untrusted skill candidate. |
| CLI live surface | IMPLEMENTED / APPROVAL-GATED | `chaseos runtime browser-cdp execute <target_url> --gate-approval-id <id>` |
| Closeout readiness report | VERIFIED / FEATURE IMPLEMENTED + ACTIVATED | `chaseos runtime browser-cdp closeout-readiness --gate-approval-id <id>` now reports activation when the Hermes activation build log evidence is present. |
| Real-environment Browser Run proof on this host | VERIFIED / OPERATIONALLY ACTIVATED | Approved throwaway smoke returned `implemented_cdp_read_only_proof_complete` and wrote declared screenshot, DOM, Browser Run, Agent Activity, marker, and untrusted candidate artifacts. |
| Excalidraw/VincisOS CDP proof | DEFERRED | Shadow and in-app browser proofs are separate from this CDP executor. |

## Done Definition

The Browser CDP feature can be marked implemented for the bounded ChaseOS
runtime path when these remain true:

- Gate operation and approval schema remain declared and denied by default.
- Approval request artifacts and explicit approval decision artifacts are written
  through bounded commands.
- The executor refuses missing, pending, denied, mismatched, or duplicate-marker
  approvals.
- The executor consumes one approved decision and writes one atomic idempotency
  marker before browser work.
- The default launcher creates a throwaway profile and never attaches to a real
  browser profile.
- The launcher implementation preflight confirms the live code path exists and
  checks opaque launcher metadata without launching.
- The default CDP client is local-only and exposes only the bounded read-only
  proof sequence.
- Proof artifacts write only to Browser Runs, Agent Activity, Operator
  Screenshots, and untrusted Browser Skill Candidates.
- Tests prove no credentials, cookies, sessions, real profile, trusted skill
  write, Agent Bus enqueue, provider call, or canonical writeback.

## Current Boundary

Implemented live execution is still intentionally narrow. It does not authorize:

- arbitrary raw CDP passthrough,
- `Runtime.evaluate` as a user-facing primitive,
- credential/cookie/session/storage reads,
- existing/real browser profile attachment,
- downloads, uploads, form entry, authenticated sessions, or DOM mutation,
- trusted skill activation,
- Agent Bus enqueue,
- provider calls,
- canonical ChaseOS writeback.

## Local Smoke Status

A safe throwaway CLI smoke with approved artifact reached the live executor and
returned:

- `status=implemented_cdp_read_only_proof_complete`
- `executor_status=implemented`
- `approval_consumed=True`
- `idempotency_marker_written=True`
- `browser_launch_attempted=True`
- `cdp_connection_attempted=True`
- `screenshot_attempted=True`
- `dom_snapshot_attempted=True`
- `title=ChaseOS Browser CDP Activation Smoke`
- `url=http://127.0.0.1:48449/index.html`
- proof artifacts existed for Browser Run log, Agent Activity log, screenshot, DOM JSON, idempotency marker, and untrusted Browser Skill Candidate.

The smoke used a throwaway vault root and local-only target. It consumed the one approved decision and wrote the exact-once marker as expected. Operational environment activation is now complete for this WSL host.

## Next Operational Step

No remaining operational activation item is open. Future Browser CDP runs should use the existing approval-request → approval-decision → execute sequence against an approved local/allowlisted target.

## Graph Links

[[Browser-CDP-Adapter-Design]] | [[Browser-Operator-Skill-Layer]] | [[Browser-Operator-Policy]] | [[Browser-Runtime-Test-Plan]] | [[ChaseOS-Gate]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
