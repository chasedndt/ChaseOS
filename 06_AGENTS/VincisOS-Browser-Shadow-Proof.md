---
title: VincisOS Browser Shadow Proof
type: test-plan
status: bounded static-fixture MVP complete / full VincisOS UI test deferred
created: 2026-04-30
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter / BOSL
runtime: Codex
---

# VincisOS Browser Shadow Proof

This note records the first ChaseOS-owned readiness gate for a future VincisOS browser proof. It does not authorize a browser launch or live UI control.

## Current Result

The first pass found no actual local VincisOS UI target. The next pass added a harmless repo-local static target at:

```text
runtime/browser_runtime/test_targets/vincisos_shadow.html
```

The target proof is:

```powershell
python -m runtime.browser_runtime.vincisos_static_target --json
```

That command starts a temporary `127.0.0.1` HTTP server, runs the no-execution readiness preflight with local socket reachability, then stops the server before returning.

The current static-target result is:

- `status: static_target_preflight_ready_no_browser`
- nested preflight: `ready_for_future_vincisos_shadow_browser_test_no_execution`
- local socket reachable: true
- server started: true
- server stopped: true
- browser launch attempted: false
- CDP connection attempted: false
- screenshot attempted: false
- profile access attempted: false
- credential read attempted: false
- skill activation attempted: false
- canonical writeback attempted: false

## Accepted Future Target Shape

A later pass may proceed only when the target is explicit and local, for example:

```text
http://127.0.0.1:<port>
http://localhost:<port>
```

The readiness preflight accepts local, port-scoped shadow targets but still does not execute a browser run. The first local browser proof now exists through the Codex in-app browser against the repo-local static target. A later full VincisOS product UI test still requires an explicitly available local UI target.

## Live Browser Proof Attempt

The first local browser attempt used the required Codex Browser plugin path. Browser setup returned `No active Codex browser pane available`, and a direct tab creation probe timed out/reset the Node kernel before any local server or browser page was opened.

Blocked run evidence:

```text
07_LOGS/Browser-Runs/vincisos_local_browser_20260430_blocked_iab_unavailable.json
```

No browser, CDP connection, screenshot, profile, credential, cookie, skill draft, active skill, or canonical writeback was used.

## In-App Browser Proof

The next attempt succeeded after the Codex in-app browser pane was available. Codex used the Browser plugin `iab` backend, started a temporary `127.0.0.1` server for the static fixture, opened the local page, inspected visible state, clicked the harmless `Inspect State` control, verified `Shadow state: inspected`, saved screenshot evidence, wrote a Browser Run Log, and generated draft-only local site skill memory.

Run evidence:

```text
07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_success.json
07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_screenshot.png
06_AGENTS/Browser-Skills/_drafts/draft-vincisos-inapp-browser-20260430.md
```

This proof did not use a real Chrome profile, saved credentials, cookies, browser history, CDP, Browser Harness, Browser Use CLI, Agent Bus enqueue, provider calls, Gate mutation, trusted Browser Skill writes, SiteOps Skill Card writes, active skill promotion, or canonical ChaseOS writeback.

## Draft Skill Replay Proof

On 2026-05-01, Codex replayed the draft-only local VincisOS site skill memory against the repo-local static target. The replay loaded:

```text
06_AGENTS/Browser-Skills/_drafts/draft-vincisos-inapp-browser-20260430.md
```

Replay evidence:

```text
07_LOGS/Browser-Runs/vincisos_draft_skill_replay_20260501_success.json
07_LOGS/Browser-Runs/vincisos_draft_skill_replay_20260501_screenshot.png
06_AGENTS/Browser-Skills/_drafts/replay-vincisos-draft-skill-20260501.md
```

The replay confirmed the stored toggle selector resolves to one element, `#runtime-state` remains the verification selector, and `#event-log` remains absent. The in-app browser selector click failed at the click-translation layer, and a visible local fallback was needed to finish the harmless action. This evidence updates the draft-review picture only; it does not activate or promote the skill.

## Fresh-Tab Click Hardening

On 2026-05-01, Codex reran the draft skill replay from a fresh in-app browser tab. The stored selector clicked successfully without fallback:

```text
07_LOGS/Browser-Runs/vincisos_replay_click_hardening_20260501_success.json
```

The pass confirms the draft selector itself is valid for the static fixture. The prior click failure appears tied to stale tab or browser-state behavior. Screenshot capture for this hardening pass failed with a `Page.captureScreenshot` timeout and is tracked at:

```text
07_LOGS/Browser-Runs/vincisos_replay_click_hardening_20260501_screenshot_blocked.md
06_AGENTS/Browser-Runtime-Feature-Readiness-Tracker.md
```

## Screenshot Artifact Hardening

On 2026-05-01, Codex reran the local static fixture path and used the Codex Browser plugin CUA visible-screenshot base64 path instead of the timed-out `Page.captureScreenshot` path. The run kept the same local-only harmless action boundary and saved a fresh screenshot artifact:

```text
07_LOGS/Browser-Runs/vincisos_screenshot_artifact_hardening_20260501_success.json
07_LOGS/Browser-Runs/vincisos_screenshot_artifact_hardening_20260501_screenshot.png
runtime/browser_runtime/artifacts.py
```

The screenshot is 23,988 bytes and shows `Shadow state: inspected`. The temporary loopback server stopped after evidence capture. This closes the bounded static-fixture MVP blocker, but it does not test the full VincisOS product UI.

## Full UI Safe-Mode Preflight

On 2026-05-01, Codex added a stricter non-executing preflight for a future full VincisOS product UI proof:

```text
runtime/browser_runtime/vincisos_full_ui_preflight.py
```

The current in-app browser URL was still the old static fixture:

```text
http://127.0.0.1:63479/vincisos_shadow.html
```

That target is correctly blocked for the production UI gate because `vincisos_shadow.html` is the repo-local static fixture and the temporary port is no longer reachable. Evidence:

```text
07_LOGS/Browser-Runs/vincisos_full_ui_safe_mode_preflight_20260501_blocked_current_static_fixture.json
```

The preflight attempted no browser launch, screenshot, CDP connection, Browser Harness use, Browser Use CLI live execution, profile access, credential read, trusted write, skill activation, Agent Bus enqueue, provider call, Gate mutation, or canonical writeback.

## Full UI Target Contract

On 2026-05-01, Codex added a stricter contract validator for a future contract-backed full VincisOS product UI proof:

```text
runtime/browser_runtime/vincisos_full_ui_target_contract.py
runtime/browser_runtime/test_targets/vincisos_full_ui_target_contract.example.json
06_AGENTS/VincisOS-Full-UI-Target-Contract.md
```

The contract validator requires `contract_version=vincisos.full_ui_target.v1`, `target_kind=product_ui`, shadow mode, safe-mode evidence, local-only allowed hosts, minimum harmless action set, expected proof artifacts, `draft_only=true`, and explicit false authority flags for real profiles, credentials, CDP, Browser Harness, Browser Use CLI live execution, trusted writes, activation, Agent Bus enqueue, provider calls, Gate mutation, and canonical writeback.

The current in-app browser URL remains blocked:

```text
07_LOGS/Browser-Runs/vincisos_full_ui_target_contract_20260501_blocked_static_fixture.json
```

The block reason is `static_fixture_is_not_product_ui`. No browser launch, screenshot, CDP, Browser Harness, Browser Use CLI live execution, profile access, credential read, trusted write, skill activation, Agent Bus enqueue, provider call, Gate mutation, or canonical writeback occurred.

## Contract-Backed Proof Planner

On 2026-05-02, Codex added a no-execution proof planner for the future contract-backed full VincisOS product UI proof:

```text
runtime/browser_runtime/vincisos_contract_backed_proof.py
06_AGENTS/VincisOS-Contract-Backed-Proof-Plan.md
```

The planner composes the target contract into a future proof action plan and artifact plan. For a valid contract, it reports planned Browser Run, Agent Activity, screenshot, draft Site Skill, and untrusted skill-candidate outputs. It writes none of those artifacts during planning.

The current in-app browser URL remains blocked:

```text
07_LOGS/Browser-Runs/vincisos_contract_backed_proof_plan_20260502_blocked_static_fixture.json
```

The block reasons are `target_contract_not_ready` and `static_fixture_is_not_product_ui`. No browser launch, screenshot, CDP, Browser Harness, Browser Use CLI live execution, profile access, credential read, trusted write, skill activation, Agent Bus enqueue, provider call, Gate mutation, or canonical writeback occurred.

## Denied Surfaces

- real Chrome profile use
- saved credentials
- cookie or session export
- CDP execution
- raw CDP exposure
- browser profile sync
- public tunnel use
- canonical ChaseOS writeback
- trusted Browser Skill or SiteOps Skill Card writes
- automatic skill activation

## Future Success Criteria

1. VincisOS target is local-only and explicitly declared.
2. Browser context is isolated or throwaway.
3. Browser action is harmless and local.
4. Browser Run Log writes under `07_LOGS/Browser-Runs/`.
5. Agent Activity writes under `07_LOGS/Agent-Activity/`.
6. Draft skill candidate writes under review-only storage.
7. No active skill or canonical memory is mutated.

## Graph Links

[[Browser-Runtime-Test-Plan]] - [[Browser-Operator-Skill-Layer]] - [[Browser-CDP-Adapter-Design]] - [[ChaseOS-SiteOps]] - [[Permission-Matrix]] - [[Trust-Tiers]]
