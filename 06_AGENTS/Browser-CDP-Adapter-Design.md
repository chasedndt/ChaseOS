---
title: Browser CDP Adapter Design
type: architecture
status: partial / bounded CDP executor implemented and operationally activated; broader browser runtime still partial
created: 2026-04-30
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter / BOSL
runtime: Codex
---

# Browser CDP Adapter Design

This note defines the ChaseOS boundary for the bounded Chrome DevTools Protocol
adapter path. The read-only proof executor and live primitives now exist, and
Hermes completed the local throwaway-profile operational smoke on 2026-05-02.
The feature remains narrow and approval-gated, not unrestricted browser control.

## Current Surface

Runtime scaffold:

```python
runtime.browser_runtime.adapters.cdp_design.CDPAdapterDesignRequest
runtime.browser_runtime.adapters.cdp_design.evaluate_cdp_adapter_design(...)
runtime.browser_runtime.cdp_executor_spec.build_cdp_read_only_executor_spec(...)
runtime.browser_runtime.cdp_executor_spec.write_cdp_read_only_approval_request(...)
runtime.browser_runtime.cdp_executor_spec.validate_cdp_read_only_approval_artifact(...)
runtime.browser_runtime.cdp_executor_spec.build_cdp_read_only_decision_preflight(...)
runtime.browser_runtime.cdp_executor_spec.build_cdp_read_only_idempotency_reservation_spec(...)
runtime.browser_runtime.cdp_executor_spec.build_cdp_read_only_executor_dry_run_plan(...)
runtime.browser_runtime.cdp_executor_spec.build_cdp_read_only_approval_decision_policy(...)
runtime.browser_runtime.cdp_executor_spec.build_cdp_read_only_approval_decision_consumer_design(...)
runtime.browser_runtime.cdp_executor_spec.build_cdp_read_only_atomic_marker_writer_design(...)
runtime.browser_runtime.cdp_executor_spec.build_cdp_read_only_isolated_browser_launcher_design(...)
runtime.browser_runtime.cdp_executor_spec.build_cdp_read_only_isolated_launcher_implementation_preflight(...)
runtime.browser_runtime.cdp_executor_spec.execute_cdp_read_only_proof(...)
runtime.browser_runtime.cdp_live.IsolatedBrowserLauncher
runtime.browser_runtime.cdp_live.MinimalCDPClient
```

The scaffold evaluates a proposed CDP adapter configuration and returns a
machine-readable design preflight packet. It never opens a socket, launches a
browser, attaches to Chrome, reads a profile, logs cookies, writes trusted
skills, or mutates canonical ChaseOS state.

Gate schema surface:

```powershell
chaseos gate check-operation browser.cdp.read_only_proof --external-api browser.navigation --json
```

Read-only executor-spec surface:

```powershell
chaseos runtime browser-cdp executor-spec http://127.0.0.1:<port> --runtime Codex --json
```

Request-only approval artifact surface:

```powershell
chaseos runtime browser-cdp approval-request http://127.0.0.1:<port> --runtime Codex --requested-by operator --write-approval-request --json
chaseos runtime browser-cdp approval-request --gate-approval-id <id> --json
```

No-execution decision preflight surface:

```powershell
chaseos runtime browser-cdp decision-preflight http://127.0.0.1:<port> --runtime Codex --gate-approval-id <id> --json
```

No-execution idempotency reservation spec surface:

```powershell
chaseos runtime browser-cdp idempotency-reservation-spec http://127.0.0.1:<port> --runtime Codex --gate-approval-id <id> --json
```

No-execution executor dry-run surface:

```powershell
chaseos runtime browser-cdp executor-dry-run http://127.0.0.1:<port> --runtime Codex --gate-approval-id <id> --json
```

No-execution approval-decision policy surface:

```powershell
chaseos runtime browser-cdp approval-decision-policy http://127.0.0.1:<port> --runtime Codex --gate-approval-id <id> --json
```

No-execution approval decision consumer design surface:

```powershell
chaseos runtime browser-cdp approval-decision-consumer-design http://127.0.0.1:<port> --runtime Codex --gate-approval-id <id> --json
```

No-write atomic marker writer design surface:

```powershell
chaseos runtime browser-cdp atomic-marker-writer-design http://127.0.0.1:<port> --runtime Codex --gate-approval-id <id> --json
```

No-launch isolated browser launcher design surface:

```powershell
chaseos runtime browser-cdp isolated-browser-launcher-design http://127.0.0.1:<port> --runtime Codex --gate-approval-id <id> --json
```

No-launch launcher implementation preflight:

```powershell
chaseos runtime browser-cdp isolated-launcher-implementation-preflight http://127.0.0.1:<port> --runtime Codex --gate-approval-id <id> --json
```

Gate operation:

```text
browser.cdp.read_only_proof
```

Approval schema:

```text
bosl.cdp_read_only_proof.v1
```

## Current Verdict

CDP remains partial but no longer only scaffolded. The implemented surfaces
include no-exec preflight/specification helpers, request and decision artifact
writers, approval consumption, atomic marker creation, a default isolated
launcher/client code path, proof artifact writers, and injected executor tests.
The current host still has no configured/discoverable Chromium-compatible
executable, so real-environment smoke remains blocked:

```text
adapter_implemented: true_for_bounded_read_only_proof
execution_allowed: approval_gated
browser_launch_allowed: approval_gated_and_environment_dependent
cdp_connection_attempted: false
raw_cdp_exposed: false
executor_status: implemented
real_isolated_browser_launcher: implemented_code_path_environment_unverified
default_live_cdp_client_binding: implemented_code_path_environment_unverified
```

`check_runtime_operation("browser.cdp.read_only_proof")` returns denied by
default because the operation requires explicit Gate approval. Approved
execution can use the bounded default launcher/client path, but local smoke is
blocked until browser executable discovery is satisfied.

`build_cdp_read_only_executor_spec(...)` reports the bounded injected executor
contract, Gate state, and approval-artifact gaps. The spec surface itself does
not write approval artifacts, consume approvals, launch a browser, connect to
CDP, capture screenshots, inspect DOM state, or write run evidence.

`write_cdp_read_only_approval_request(...)` can persist a pending request under
`07_LOGS/Agent-Activity/_bosl_cdp_approvals/`. The artifact is a review record
only. It does not approve, consume approval, execute CDP, or authorize a browser
action.

`build_cdp_read_only_decision_preflight(...)` reads a supplied approval artifact,
checks approval status, confirms a future idempotency marker is absent, and
builds a bounded future write-plan preview. It does not consume approval, mutate
the approval artifact, create an idempotency marker, launch a browser, connect
to CDP, capture screenshots, inspect DOM state, or write run evidence.

`build_cdp_read_only_idempotency_reservation_spec(...)` composes the decision
preflight into the future marker-reservation contract. It returns the marker
path, marker record template, atomic create-new rules, retry/failure policy, and
blocked status, but does not write the marker, consume approval, mutate the
approval artifact, launch a browser, connect to CDP, capture screenshots,
inspect DOM state, or write run evidence.

`build_cdp_read_only_executor_dry_run_plan(...)` composes the reservation spec
into a future executor sequence and stop-condition packet. It reports future
approval consumption, marker creation, isolated launch, local CDP connection,
bounded observation, artifact writes, and cleanup steps, but performs none of
them.

`build_cdp_read_only_approval_decision_policy(...)` defines the future approval
decision artifact and consumption rules. It makes explicit that an edited
`status: approved` field is not enough authority by itself. It does not write a
decision artifact, consume approval, write a marker, launch a browser, or
connect to CDP.

`build_cdp_read_only_approval_decision_consumer_design(...)` defines the future
single-use approval consumer before that consumer exists. It checks the pending
approval artifact, decision status posture, request digest binding,
idempotency-marker absence, forbidden output fields, and future consumption
record template. It does not write or consume a decision, mutate an approval
artifact, write a marker, launch a browser, connect to CDP, or write proof
evidence.

`build_cdp_read_only_atomic_marker_writer_design(...)` defines the future
exclusive-create idempotency marker writer before that writer exists. It returns
the marker path constraints, sanitized marker payload template, create-new
algorithm, failure/retry policy, and fail-closed preconditions. It does not
consume approval, create the marker directory, write a marker, launch a browser,
connect to CDP, or write proof evidence.

`build_cdp_read_only_isolated_browser_launcher_design(...)` defines the future
real browser launcher boundary. It requires a
ChaseOS-created throwaway profile, local-only CDP port, no existing profile
attachment, no public debugging endpoint, no credentials/cookies/sessions, and
cleanup evidence. It does not create a profile, spawn a browser, open a port,
connect to CDP, or write proof evidence.

`build_cdp_read_only_isolated_launcher_implementation_preflight(...)` checks
the implementation acceptance gate for `runtime.browser_runtime.cdp_live`
without launching. It verifies live launcher/client code presence, opaque
managed executable/profile refs, loopback-only port allocation,
`bounded_spawn_no_shell`, cleanup policy, and bounded CDP client binding.

`execute_cdp_read_only_proof(...)` supports injected test collaborators and the
default `runtime.browser_runtime.cdp_live` launcher/client. The default path
first checks browser executable availability; when unavailable it returns
`blocked_browser_executable_unavailable` before approval consumption or marker
creation.

## Required Future Boundary

A future CDP adapter must be ChaseOS-owned and AOR/Gate-controlled:

1. AOR resolves the workflow and role card.
2. Browser policy verifies the mode, domain, action, and artifact targets.
3. Gate authorizes the specific browser operation.
4. The adapter launches or connects only to an isolated local browser context.
5. Run evidence is written only to declared log/candidate surfaces.
6. Any learned skill remains an untrusted candidate until separately promoted.

## Gate Approval Schema

The declared approval schema is a request shape only. It does not write an
approval artifact and does not execute a browser action.

Required fields:

- `operator_request_id`
- `gate_approval_id`
- `runtime`
- `target_url`
- `allowed_domains`
- `cdp_endpoint`
- `launch_strategy`
- `browser_profile_policy`
- `allowed_actions`
- `artifact_targets`
- `screenshot_retention`
- `secret_policy`

Default template constraints:

- `cdp_endpoint` must be local-only,
- `launch_strategy` must be `chaseos_launch_isolated`,
- `browser_profile_policy` must be `throwaway_only`,
- credentials, cookies, session tokens, real profiles, raw CDP, and
  `Runtime.evaluate` remain false,
- artifact targets remain limited to browser run logs, agent activity, and
  untrusted Browser Skill candidates.

## Executor Spec

The executor-spec surface is intentionally read-only. It records that the
bounded executor contract exists for injected collaborators while the live
browser path still requires:

- isolated browser launcher,
- default CDP client/socket connection,
- real-environment proof and failure evidence policy validation.

The spec may accept a `gate_approval_id` and structurally validate a pending
artifact. Validation does not consume approval and does not make execution
allowed.

## Decision Preflight

The decision preflight is also read-only. It exists to define the future
approval-consumption boundary before any executor is written.

It checks:

- approval artifact structural validity,
- approval status,
- target/runtime match against the executor spec,
- absence of a future idempotency marker,
- future write-plan confinement to Browser Run logs, Agent Activity,
  Operator Screenshots, and untrusted Browser Skill candidates.

It reports bounded approval and artifact state while still keeping side effects
disabled:

```text
execution_enabled: false
approval_consumed: false
browser_launch_attempted: false
cdp_connection_attempted: false
files_modified: false
```

The future idempotency marker path is declared under:

```text
07_LOGS/Agent-Activity/_bosl_cdp_approvals/_execution_markers/
```

The current helper never writes that marker.

## Idempotency Reservation Spec

The idempotency reservation spec is a no-write contract for the marker that a
future executor must create before any browser/CDP action.

It returns:

- `reservation_status`,
- marker path under
  `07_LOGS/Agent-Activity/_bosl_cdp_approvals/_execution_markers/`,
- `marker_record_template`,
- `reservation_rules`,
- approval validation state,
- decision preflight payload,
- false side-effect flags.

Current outcomes include:

- `blocked_approval_artifact_invalid`,
- `blocked_prior_cdp_proof_marker_exists`,
- `blocked_approval_not_approved`,
- `ready_for_future_marker_reservation_but_writer_not_built`.

The future writer must be atomic and create-new only. If a later proof fails,
failure evidence must be written and the marker must not be deleted. Retries
require operator review and a new approval/reservation decision.

## Executor Dry-Run Plan

The executor dry-run plan is the last pre-execution planning packet before any
future implementation of a marker writer, browser launcher, or CDP client.

It returns:

- `dry_run_status`,
- future execution sequence,
- stop conditions,
- future artifact targets,
- feature completion tracker,
- false side-effect flags.

The future execution sequence is:

1. reload and validate approval artifact,
2. consume approval decision,
3. reserve idempotency marker,
4. launch isolated browser,
5. connect local CDP,
6. navigate and observe,
7. capture bounded evidence,
8. write declared artifacts,
9. close context and record result.

Current dry-run output remains blocked when approval is pending, invalid, or an
idempotency marker already exists. It is still a dry run and does not launch a
real browser.

## Approval Decision Policy

The approval-decision policy defines the future immutable decision record and
consumption rules before any consumer exists.

It requires future consumers to:

- re-read and structurally validate the approval artifact,
- bind decision identity to operation, approval ID, request digest, target URL,
  and runtime,
- reject approved status without decision identity/timestamp metadata,
- reject expired, revoked, denied, mismatched, or already-consumed decisions,
- consume at most once before marker creation,
- write no credentials, cookies, sessions, browser storage, or profile paths.

This surface always reports:

```text
approval_decision_accepted: false
approval_consumed: false
approval_decision_written: false
browser_launch_attempted: false
cdp_connection_attempted: false
files_modified: false
```

## Approval Decision Consumer Design

The approval decision consumer design defines the future single-use consumer
without granting that consumer authority.

It requires future consumers to:

- re-read the approval artifact and immutable decision immediately before use,
- verify operation, approval ID, request digest, target URL, runtime, and expiry,
- reject pending, denied, revoked, expired, mismatched, already-consumed, or
  marker-present approvals,
- create a sanitized consumption record only after all authority checks pass,
- keep credentials, cookies, session tokens, browser storage, profile paths, raw
  pixels, DOM snapshots, and canonical write targets out of consumption data.

This surface always reports:

```text
consumer_status: not_built
approval_consumed: false
approval_decision_written: false
idempotency_marker_written: false
browser_launch_attempted: false
cdp_connection_attempted: false
files_modified: false
```

## Atomic Marker Writer Design

The atomic marker writer design is a no-write contract for the future
idempotency marker writer implementation.

It defines:

- approval-decision and request-digest checks required before marker creation,
- marker path confinement under
  `07_LOGS/Agent-Activity/_bosl_cdp_approvals/_execution_markers/`,
- exclusive create-new semantics,
- overwrite/delete/retry denial,
- sanitized marker payload fields,
- failure handling that keeps the marker if later execution fails.

This surface always reports:

```text
writer_status: not_built
approval_consumed: false
approval_decision_written: false
idempotency_marker_written: false
browser_launch_attempted: false
cdp_connection_attempted: false
files_modified: false
```

## Isolated Browser Launcher Design

The isolated browser launcher design is a no-launch contract for the future
real browser process boundary.

It defines:

- `chaseos_launch_isolated` as the only launch strategy,
- throwaway-only profile policy,
- required local debugging endpoint constraints,
- forbidden existing-profile, credential, cookie, session, history, extension,
  sync, public endpoint, raw-profile-path, and canonical-writeback surfaces,
- cleanup and failure-evidence expectations.

This surface always reports:

```text
launcher_status: not_built
execution_enabled: false
browser_launch_attempted: false
browser_process_spawned: false
throwaway_profile_created: false
cdp_port_opened: false
cdp_connection_attempted: false
files_modified: false
```

## Isolated Launcher Implementation Preflight

The implementation preflight is a no-launch acceptance gate over the current
`runtime.browser_runtime.cdp_live` implementation.

It checks:

- `IsolatedBrowserLauncher` code is present,
- `MinimalCDPClient` code is present,
- managed browser executable reference is opaque,
- throwaway profile parent reference is opaque,
- port allocation strategy is `allocate_unused_loopback_port`,
- process runner policy is `bounded_spawn_no_shell`,
- cleanup strategy is `close_then_delete_throwaway_profile`,
- CDP client binding is a bounded `runtime.browser_runtime.*` binding.

CLI mode supplies no launcher metadata and therefore fails closed. Direct
runtime callers can supply opaque refs for patch-readiness checks without
launching or creating a profile.

It always reports:

```text
execution_enabled: false
browser_launch_attempted: false
browser_process_spawned: false
throwaway_profile_created: false
cdp_port_opened: false
cdp_connection_attempted: false
files_modified: false
```

## Local-Only Endpoint Rule

Default CDP endpoints must be local:

- `127.0.0.1`
- `localhost`
- `::1`

Public CDP endpoints, tunnels, shared remote debugging ports, and attachment to
unknown existing Chrome instances are forbidden by default.

## Profile Rule

The future adapter may not attach to the operator's real browser profile by
default. It must use a throwaway or ChaseOS-created isolated context.

Forbidden by default:

- existing personal Chrome profile,
- saved passwords,
- cookies and session state,
- extension state,
- synced profile data,
- raw profile/user-data-dir logging.

## CDP Action Boundary

Safe design-level actions are limited to observation and bounded navigation:

- `page.navigate`
- `page.capture_screenshot`
- `dom.snapshot`
- `page.read_title`
- `page.read_url`
- `page.read_visible_text`
- `wait_for`

Forbidden or future-approval-required actions include:

- raw CDP passthrough,
- `Runtime.evaluate`,
- cookie/session/storage reads,
- permission grants,
- download behavior changes,
- file chooser/upload,
- arbitrary key/text injection,
- DOM mutation.

## Relationship to BOSL and SiteOps

CDP is a possible future execution adapter, not a skill registry and not a
promotion authority.

- BOSL stores reviewed skills and untrusted candidates.
- SiteOps controls candidate review and future promotion contracts.
- AOR/Gate controls execution.
- CDP may only execute approved, policy-checked actions after a separate future
  implementation and Gate decision.

## Not Unrestricted Browser Control

This design intentionally rejects unrestricted CDP:

- no raw protocol surface for browser agents,
- no real-account browsing,
- no credential/session extraction,
- no full browser history import,
- no shell execution,
- no public debugging endpoint,
- no canonical writeback,
- no trusted skill mutation.

## Current Tests

Focused tests live in:

```text
runtime/browser_runtime/test_browser_runtime.py
```

They verify:

- a local-only proposal can be reviewable but still non-executable,
- remote endpoints, existing profiles, credentials, cookie access, raw CDP,
  `Runtime.evaluate`, forbidden actions, trusted writes, and canonical
  writeback are blocked.
- Gate exposes `bosl.cdp_read_only_proof.v1` while returning denied and
  attempting no CDP connection or browser launch.
- `chaseos runtime browser-cdp executor-spec ...` returns a non-executing
  precondition packet with `executor_status: implemented` for the injected
  executor contract.
- pending approval request artifacts can be written and structurally validated,
  but approval decision consumption and browser execution are still absent.
- decision preflight reports approval status, idempotency-marker posture, and a
  bounded future write plan without consuming approval or writing artifacts.
- idempotency reservation spec returns a future marker template and reservation
  rules without writing a marker or enabling execution.
- executor dry-run plan returns future sequence, stop conditions, and feature
  completion status without consuming approval, writing markers, or executing.
- approval-decision policy returns the future decision record template and
  consumption rules without writing or consuming a decision.
- approval decision consumer design returns the future single-use consumption
  algorithm, marker-absence guard, forbidden output fields, and consumption
  record template without consuming approval, writing decisions, or writing
  markers.
- atomic marker writer design, isolated browser launcher design, and isolated
  launcher implementation preflight remain no-write/no-launch inspection
  surfaces.
- injected proof executor tests write bounded Browser Run, Agent Activity,
  screenshot, DOM, and untrusted candidate artifacts using fake collaborators;
  they do not prove a real browser launcher.

## Graph Links

[[Browser-CDP-Feature-Readiness]] - [[Browser-Operator-Skill-Layer]] - [[Browser-Operator-Policy]] - [[Browser-Runtime-Test-Plan]] - [[ChaseOS-SiteOps]] - [[Agent-Security-Model]] - [[Permission-Matrix]] - [[Trust-Tiers]]
