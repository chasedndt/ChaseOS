---
title: Browser Runtime Test Plan
type: test-plan
status: partial / bounded static-fixture MVP complete; CDP live code path activated for read-only proof; broader runtime still partial
created: 2026-04-30
updated: 2026-05-04
phase: Phase 9 Browser Runtime Adapter
knowledge_class: canonical-state
---

# Browser Runtime Test Plan

This plan defines the safe path from the bounded `runtime/browser_runtime/` spike toward future live browser tests. It does not authorize real-account browsing, real Chrome profile reuse, saved credential access, Browser Harness attachment, or automatic skill promotion.

## Current Safe Proof

The first executable proof is the `shadow` provider:

```powershell
python -m runtime.browser_runtime.smoke
```

It uses `https://example.com`, writes Browser Run evidence, writes Agent Activity evidence, and generates a draft-only Site Skill candidate. It does not launch a real browser.

## Future VincisOS Target

VincisOS is the preferred first live UI target because it can be local, controlled, and free of real account data.

Current readiness proof:

```powershell
python -m runtime.browser_runtime.vincisos_preflight --json
python -m runtime.browser_runtime.vincisos_static_target --json
```

The preflight is non-executing. It blocks if no explicit local target URL is declared, accepts only local port-scoped targets such as `http://127.0.0.1:<port>`, and records that browser launch, CDP connection, screenshot capture, profile access, credential reads, canonical writeback, and skill activation were not attempted.

The static target helper serves `runtime/browser_runtime/test_targets/vincisos_shadow.html` through a temporary `127.0.0.1` HTTP server, verifies local socket reachability, and shuts the server down before returning. This proves a safe local target exists without running a browser.

Current local in-app browser proof:

```text
07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_success.json
07_LOGS/Browser-Runs/vincisos_inapp_browser_20260430_screenshot.png
06_AGENTS/Browser-Skills/_drafts/draft-vincisos-inapp-browser-20260430.md
```

That proof used the Codex Browser plugin `iab` backend against the repo-local static target only. It opened the local URL, read page state, clicked one harmless control, captured a screenshot, stopped the loopback server, and generated draft-only skill memory. It did not use real profile state, credentials, cookies, CDP, Browser Harness, Browser Use CLI, public tunnels, trusted skill writes, active skill promotion, or canonical writeback.

Current local product UI browser proof:

```text
07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_success.json
07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_screenshot.png
07_LOGS/Agent-Activity/2026-05-02-codex-vincisos-product-ui-browser-proof.md
06_AGENTS/Browser-Skills/_drafts/draft-vincisos-product-ui-browser-proof-20260502.md
03_INPUTS/Browser-Skill-Candidates/127-0-0-1/20260502__candidate-vincisos-product-ui-browser-proof-20260502.md
```

That proof used the Codex Browser plugin `iab` backend against the registered local Studio Product UI Test Target at `http://127.0.0.1:8770/`. It verified stable selectors, task and approval row counts, approval/workflow panels, the harmless safe-mode inspection action, screenshot evidence, draft-only skill memory, and untrusted candidate evidence. It did not use real profile state, credentials, cookies, CDP, Browser Harness, Browser Use CLI, public tunnels, trusted skill writes, active skill promotion, Agent Bus enqueue, provider calls, Gate mutation, or canonical writeback.

Draft skill replay proof:

```text
07_LOGS/Browser-Runs/vincisos_draft_skill_replay_20260501_success.json
07_LOGS/Browser-Runs/vincisos_draft_skill_replay_20260501_screenshot.png
06_AGENTS/Browser-Skills/_drafts/replay-vincisos-draft-skill-20260501.md
```

That replay loaded the existing draft skill memory and reused its stored selectors for orientation and verification. The primary selector resolved to one element, the verification selector worked, and the negative selector remained absent. The in-app browser selector click failed at the click-translation layer, so the run used a visible local fallback to complete the harmless action. This is replay evidence only; the skill is still not active or promoted.

Fresh-tab click hardening proof:

```text
07_LOGS/Browser-Runs/vincisos_replay_click_hardening_20260501_success.json
07_LOGS/Browser-Runs/vincisos_replay_click_hardening_20260501_screenshot_blocked.md
06_AGENTS/Browser-Runtime-Feature-Readiness-Tracker.md
```

That proof opened a fresh in-app browser tab before replaying the stored selector. The selector click succeeded without fallback, confirming the previous replay failure was stale-tab or browser-state related rather than a selector-invalidity problem. Screenshot capture for this hardening pass timed out, so current hardening artifact capture remains blocked.

Screenshot artifact hardening proof:

```text
07_LOGS/Browser-Runs/vincisos_screenshot_artifact_hardening_20260501_success.json
07_LOGS/Browser-Runs/vincisos_screenshot_artifact_hardening_20260501_screenshot.png
runtime/browser_runtime/artifacts.py
```

That proof used a fresh local static fixture run and captured screenshot evidence through `tab.cua.get_visible_screenshot().toBase64()` instead of the timed-out `Page.captureScreenshot` path. The screenshot artifact is 23,988 bytes, visually confirms `Shadow state: inspected`, and the run log records the server stopped. The bounded local static-fixture MVP is complete; the production feature remains incomplete until a full safe-mode VincisOS UI target and later production gates are verified.

Future full VincisOS UI test path:

1. Start a local VincisOS UI in a clearly isolated test mode.
2. Use a throwaway browser profile or isolated Playwright/Chromium context.
3. Open the local URL only, such as `http://127.0.0.1:<port>`.
4. Read page state.
5. Capture a screenshot.
6. Perform one harmless navigation or local UI interaction.
7. Write Browser Run Log under `07_LOGS/Browser-Runs/`.
8. Write Agent Activity under `07_LOGS/Agent-Activity/`.
9. Generate one draft Site Skill candidate under `06_AGENTS/Browser-Skills/_drafts/`.
10. Do not mutate canonical ChaseOS notes or active SiteOps skills.

Current full UI preflight:

```powershell
python -m runtime.browser_runtime.vincisos_full_ui_preflight --target-url http://127.0.0.1:<port>/ --safe-mode-asserted --json
```

The full UI preflight is non-executing and stricter than the static-fixture preflight. It requires an explicit local product UI URL, safe/test mode assertion, `target_kind=product_ui`, and no real-profile, credential, CDP, Browser Harness, Browser Use CLI live, trusted write, activation, Agent Bus, provider, Gate mutation, or canonical writeback authority. It blocks `vincisos_shadow.html` even when local because the fixture cannot satisfy the product UI gate.

Blocked current-target evidence:

```text
07_LOGS/Browser-Runs/vincisos_full_ui_safe_mode_preflight_20260501_blocked_current_static_fixture.json
```

The current in-app browser URL points to the old static fixture at `http://127.0.0.1:63479/vincisos_shadow.html`; the old temporary port is closed and the path is the static fixture, so it is not a valid full product UI target.

Current full UI target contract:

```powershell
python -m runtime.browser_runtime.vincisos_full_ui_target_contract --contract-json runtime/browser_runtime/test_targets/vincisos_full_ui_target_contract.example.json --json
```

The target contract validator requires `contract_version=vincisos.full_ui_target.v1`, `target_kind=product_ui`, `mode=shadow`, safe-mode evidence, local-only allowed hosts, minimum allowed actions, required expected artifacts, `draft_only=true`, and explicit false authority flags for real profiles, credentials, CDP, Browser Harness, Browser Use live CLI, trusted writes, skill activation, Agent Bus enqueue, provider calls, Gate mutation, and canonical writeback.

Blocked current-target contract evidence:

```text
07_LOGS/Browser-Runs/vincisos_full_ui_target_contract_20260501_blocked_static_fixture.json
```

This is still no-execution. It validates only the target declaration for a future product UI proof. It does not open a browser, check DOM state, capture screenshots, write skills, or prove the product UI.

Current contract-backed proof planner:

```powershell
python -m runtime.browser_runtime.vincisos_contract_backed_proof --contract-json runtime/browser_runtime/test_targets/vincisos_full_ui_target_contract.example.json --run-id vincisos_full_ui_contract_backed_proof_20260502 --json
```

The proof planner composes the target contract into a future action/artifact plan. It can report `vincisos_contract_backed_proof_plan_ready_no_execution` for a valid contract, but it still performs no browser launch, screenshot capture, UI inspection, skill writing, or canonical mutation.

Fresh dual-track evidence from 2026-05-02:

```text
run_id: vincisos-full-ui-contract-backed-proof-20260502-both-tracks
status: vincisos_contract_backed_proof_plan_ready_no_execution
target_url: http://127.0.0.1:8770/
browser_launch_attempted: false
cdp_connection_attempted: false
files_modified: false
```

Blocked current-target proof-plan evidence:

```text
07_LOGS/Browser-Runs/vincisos_contract_backed_proof_plan_20260502_blocked_static_fixture.json
```

The current old fixture URL remains blocked with `target_contract_not_ready` and `static_fixture_is_not_product_ui`.

Current product UI target availability preflight:

```powershell
python -m runtime.browser_runtime.vincisos_product_ui_target_probe --contract-json runtime/browser_runtime/test_targets/vincisos_full_ui_target_contract.example.json --timeout-seconds 0.5 --json
```

The availability preflight validates the target contract and then performs one local HTTP reachability request only. It does not launch a browser, connect CDP, inspect DOM state, capture screenshots, click UI, read credentials/cookies/session state, write artifacts, promote skills, enqueue Agent Bus tasks, call providers, mutate Gate policy, or write canonical state.

Current live result from this pass:

```text
status: vincisos_product_ui_target_available_no_browser
target_url: http://127.0.0.1:8770/
http_status: 200
browser_launch_attempted: false
cdp_connection_attempted: false
credential/cookie/session read: false
files_modified: false
```

This means the declared target contract is valid and the registered safe-mode local product UI test target is reachable. The next browser proof is still a separate isolated browser run.

Current product UI launch-readiness gate:

```powershell
python -m runtime.browser_runtime.vincisos_product_ui_launch_readiness --vault-root . --json
```

The launch-readiness gate reads the Studio App Launcher registry and reports whether a local app is registered as a VincisOS/product UI browser-proof target. It does not start servers, execute shell commands, launch a browser, connect CDP, inspect DOM state, capture screenshots, click UI, read credentials/cookies/session state, write artifacts, promote skills, enqueue Agent Bus tasks, call providers, mutate Gate policy, or write canonical state.

Current live result from this pass:

```text
status: vincisos_product_ui_launch_target_ready_no_start
registered_target: vincisos-product-ui-test-target
target_url: http://127.0.0.1:8770/
candidate_app_count: 1
```

The Studio Product UI Test Target is registered as the safe local product UI target. The next production proof still requires isolated browser open/state/screenshot/harmless-action evidence.

Current completion-status check:

```powershell
python -m runtime.browser_runtime.completion_status --vault-root . --json
```

Expected current posture:

```text
overall_status: mvp_done_production_blocked
bounded_mvp_done: true
production_feature_done: false
```

This check is read-only. It reports feature status from repo-local evidence and forbidden-authority flags; it does not launch a browser, connect CDP, write status artifacts, promote skills, enqueue Agent Bus tasks, call providers, mutate Gate policy, or write canonical ChaseOS state.

Current Studio/operator UI readiness check:

```powershell
python -m runtime.studio.browser_runtime_operator_ui_readiness --vault-root . --json
```

Expected current posture:

```text
status: PARTIAL / READ-ONLY OPERATOR UI READINESS CONTRACT BUILT / FULL UI NOT BUILT
studio_operator_ui_built: false
remaining_major_passes: 2-4
```

This check is read-only. It defines the future Studio Browser Runtime panels for completion, remaining passes, external blockers, Excalidraw chain state, provider validation, draft skill memory, approvals, and run evidence. It does not launch a UI, grant approvals, execute browser actions, promote skills, mutate Gate policy, or write canonical ChaseOS state.

As of 2026-05-02, the status check also recognizes the bounded live CDP executor activation evidence from the Hermes Browser CDP implementation and operational activation logs. That removes the `default_live_cdp_launcher_and_client_not_built` blocker, but it does not change the next VincisOS gate: the current in-app URL is still the old static fixture, and no full VincisOS product UI browser proof exists.

Current Browser Use CLI validation preflight:

```powershell
python -m runtime.browser_runtime.browser_use_cli_validation --vault-root . --json
```

This is a read-only wrapper/config/executable check. It does not install `browser-use`, invoke `browser-use`, launch a browser, read profiles, inspect credentials/cookies, write Browser Run artifacts, promote skills, enqueue Agent Bus tasks, mutate Gate policy, call providers, or write canonical state.

Current live result:

```text
status: blocked_browser_use_cli_unavailable
```

This closes the validation-preflight surface and records the current live-validation blocker:

```text
07_LOGS/Browser-Runs/browser_use_cli_live_validation_20260502_blocked_unavailable.json
```

Browser Use CLI live validation is blocked-unavailable because `browser-use` is not on PATH. ChaseOS did not install Browser Use, invoke the CLI, launch a browser, read profiles/credentials/cookies/session data, write trusted skills, activate skills, enqueue Agent Bus work, mutate Gate, call providers, or write canonical state. A future live validation requires operator-side installation plus explicit approval for a separate safe no-account run.

Current Browser Harness adoption decision:

```powershell
python -m runtime.browser_runtime.browser_harness_adoption --json
```

Current result:

```text
status: reference_only_raw_harness_not_adopted
adoption_mode: adapt_patterns_do_not_copy_or_run
```

This closes the adoption-decision question only. ChaseOS adapts Browser Harness domain/interaction skill-memory patterns, but does not install Browser Harness, run its CLI, attach to a real Chrome profile, provision remote browsers, sync profiles/cookies, execute free-form CDP snippets, write trusted skills, activate skills, enqueue Agent Bus tasks, mutate Gate policy, or write canonical state.

Current Browser Workflow Cache foundation:

```powershell
python -m runtime.browser_runtime.workflows --vault-root . --json
```

Current result:

```text
status: cache_foundation_ready
workflow_count: 1
activation_allowed: false
replay_allowed: false
```

This is an inactive ChaseOS-native cache foundation only. It can validate and store review-only workflow entries in `runtime/browser_workflows/`, but it does not execute or replay workflows, launch browsers, connect CDP, use Browser Harness, run Browser Use live, enqueue Agent Bus tasks, call providers, mutate Gate, or write canonical state. `browser-use/workflow-use` remains AGPL-3.0 reference-only.

Current Workflow Replay Executor design preflight:

```powershell
python -m runtime.browser_runtime.workflow_replay_executor_design --vault-root . --json
```

Current result:

```text
status: ready_for_operator_review_no_execution
implementation_strategy: chaseos_native_aor_siteops_executor_no_external_code_copy
```

This is a no-execution contract packet only. It defines the future AOR/SiteOps replay executor preconditions, sequence, stop conditions, and artifacts without running cached workflows or copying external code.

Current Workflow Replay Executor implementation request:

```powershell
python -m runtime.browser_runtime.workflow_replay_executor_request --vault-root . --json
```

Current result:

```text
status: workflow_replay_executor_implementation_request_ready_no_write
request_ready_no_write: true
implementation_allowed_in_this_pass: false
```

This is a no-write operator-review packet only. It names the future
implementation patch scope and required guardrails while still executing no
cached workflows, launching no browser, connecting no CDP session, copying no
external code, and writing no trusted or canonical artifacts.

Current Workflow Replay Executor implementation approval:

```powershell
python -m runtime.browser_runtime.workflow_replay_executor_approval --vault-root . --decision approve --json
```

Current result:

```text
status: workflow_replay_executor_implementation_approval_ready_no_write
implementation_approved_for_future_patch: true
implementation_allowed_in_this_pass: false
approval_artifact_written: false
replay_execution_allowed: false
```

This is a no-write approval packet only. It can approve a later bounded
implementation patch under the recorded guardrails, but it does not implement
the executor, write an approval artifact, replay workflows, launch browsers,
connect CDP, copy external code, activate skills, or write trusted/canonical
artifacts.

Current Workflow Replay Executor implementation:

```powershell
python -m runtime.browser_runtime.workflow_replay_executor --vault-root . --json
```

Current result:

```text
status: workflow_replay_executor_disabled_no_workflow_selected
execution_allowed: false
workflow_replay_attempted: false
replay_artifacts_written: false
```

This is a disabled validation/planning executor only. It can inspect a selected
cache entry and return a plan, but it does not run cached workflows, launch
browsers, connect CDP, use Browser Harness, run Browser Use live, copy external
code, activate skills, write trusted/canonical artifacts, or mutate Gate.

Current Workflow Replay Execution readiness preflight:

```powershell
python -m runtime.browser_runtime.workflow_replay_execution_readiness --vault-root . --json
```

Current live result:

```text
status: workflow_replay_execution_readiness_ready_no_execution
workflow_count: 1
workflow_id: wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502
execution_allowed: false
workflow_replay_attempted: false
browser_launch_attempted: false
```

This read-only preflight composes the inactive workflow cache and disabled
executor to show that a reviewed local workflow candidate is selected for
no-execution readiness. It writes no Browser Run log, writes no Agent Activity
log, launches no browser, connects no CDP session, uses no Browser Harness or
Browser Use live runtime, and mutates no Gate/trusted/canonical state.

Current Workflow Replay trial candidate:

```powershell
python -m runtime.browser_runtime.workflow_replay_trial_candidate --vault-root . --write-trial-candidate --json
```

Current selected entry:

```text
runtime/browser_workflows/workflows/wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502.workflow.json
```

The selected candidate is derived only from the local VincisOS product UI proof
run. It is `reviewed_for_trial`, inactive, and replay-enabled only for
readiness validation. It is not active runtime memory and not a live replay
approval.

## Optional Excalidraw Candidate

Excalidraw now has a BOSL non-executing shadow-plan proof through:

```powershell
python -m runtime.browser_skills.shadow_runner excalidraw.draw_basic_shape
```

That proof validates the skill file, plans the canvas actions, writes Browser Run evidence, writes an untrusted candidate, and does not launch a browser or make a network request.

Fresh dual-track evidence from 2026-05-02:

```text
07_LOGS/Browser-Runs/bosl_shadow_2026-05-02T020341.380669z0000_excalidraw-draw-basic-shape.json
07_LOGS/Browser-Runs/bosl_shadow_2026-05-02T020341.380669z0000_excalidraw-draw-basic-shape-shadow-proof.txt
03_INPUTS/Browser-Skill-Candidates/bosl-shadow-2026-05-02t020341-380669z0000-excalidraw-draw-basic-shape-candidate.md
07_LOGS/Agent-Activity/bosl-shadow-2026-05-02t020341-380669z0000-excalidraw-draw-basic-shape.md
```

A live Excalidraw browser/canvas test remains a later candidate. The safe version should prefer a local canvas/MCP setup such as `mcp_excalidraw` only after:

- the canvas server binds to `127.0.0.1`,
- no public tunnel is enabled,
- no saved browser profile is used,
- the action is local test drawing only,
- all output writes to logs or draft artifacts,
- no external account or collaboration session is used.

Current Excalidraw browser/MCP proof prep:

```powershell
python -m runtime.browser_runtime.excalidraw_mcp_proof_prep --vault-root . --run-date 20260503 --write-prep --json
```

Evidence:

```text
07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_proof_prep_20260503_ready.json
06_AGENTS/Excalidraw-Browser-MCP-Proof-Prep.md
```

That prep packet is no-execution. It declares local-first target posture,
public Excalidraw fallback approval requirements, expected future artifacts,
and draft-only skill memory rules. It does not launch a browser, invoke MCP,
navigate to Excalidraw, use a real browser profile, read credentials/cookies,
write trusted skills, activate skills, enqueue Agent Bus work, call providers,
mutate Gate, or write canonical state.

Current Excalidraw browser/MCP live readiness:

```powershell
python -m runtime.browser_runtime.excalidraw_mcp_live_readiness --vault-root . --write-readiness --json
```

Evidence:

```text
07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_blocked_missing_local_target.json
06_AGENTS/Excalidraw-Browser-MCP-Live-Readiness.md
```

Current result:

```text
status: blocked_excalidraw_live_readiness_missing_local_target
blocker: local_excalidraw_target_url_not_provided
next_recommended_pass: excalidraw-local-target-setup-instructions
```

This readiness gate is also no-execution. It validates prep evidence and
browser-controller readiness, then stops because no local loopback
Excalidraw/MCP target URL was provided. It performs no browser launch, CDP
connection, MCP invocation, target navigation/probe, dependency install,
real-profile or credential/cookie access, trusted write, activation, Agent
Bus/provider call, Gate mutation, or canonical writeback.

Current Excalidraw local target setup instructions:

```powershell
python -m runtime.browser_runtime.excalidraw_target_setup_instructions --vault-root . --write-instructions --json
```

Evidence:

```text
07_LOGS/Browser-Runs/excalidraw_local_target_setup_instructions_20260503_ready.json
06_AGENTS/Excalidraw-Local-Target-Setup-Instructions.md
```

Current result:

```text
status: excalidraw_local_target_setup_instructions_ready_no_execution
next_recommended_pass: external-runtime-provide-excalidraw-target-url
```

This pass gives an external runtime/operator the exact local target requirement: provide a loopback URL such as `http://127.0.0.1:<port>/` or `http://localhost:<port>/`, then rerun the no-execution live-readiness gate with `--local-target-url`. ChaseOS still does not install dependencies, start servers, launch browsers, connect CDP, invoke MCP, navigate, probe the target, use real profiles, read credentials/cookies, write trusted skills, activate skills, enqueue Agent Bus work, call providers, mutate Gate, or write canonical state.

Current Excalidraw local target contract request:

```powershell
python -m runtime.browser_runtime.excalidraw_target_contract --vault-root . --write-contract --json
```

Evidence:

```text
07_LOGS/Browser-Runs/excalidraw_local_target_contract_request_20260503_ready.json
06_AGENTS/Excalidraw-Local-Target-Contract.md
```

Current result:

```text
status: excalidraw_local_target_contract_request_ready_no_execution
next_recommended_pass: external-runtime-provide-excalidraw-target-url
```

This contract/request packet makes the handoff machine-readable for the external runtime. It can validate a provided local URL shape without probing it, and it performs no install, server start, network probe, browser launch, CDP connection, MCP invocation, navigation, trusted write, activation, Agent Bus/provider call, Gate mutation, or canonical writeback.

Current Excalidraw local target response intake:

```powershell
python -m runtime.browser_runtime.excalidraw_target_response --vault-root . --write-response --json
```

Evidence:

```text
03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_pending.json
06_AGENTS/Excalidraw-Local-Target-Response-Intake.md
```

Current result:

```text
status: excalidraw_local_target_response_pending_external_runtime
next_recommended_pass: external-runtime-provide-excalidraw-target-url
```

This pending response packet gives the external runtime/operator a reviewable input slot. It validates only loopback URL shape and performs no install, server start, network probe, browser launch, CDP connection, MCP invocation, navigation, trusted write, activation, Agent Bus/provider call, Gate mutation, or canonical writeback.

Current Excalidraw target response latest resolver:

```powershell
python -m runtime.browser_runtime.excalidraw_target_response_resolver --vault-root . --json
```

Evidence:

```text
runtime/browser_runtime/excalidraw_target_response_resolver.py
runtime/browser_runtime/test_excalidraw_target_response_resolver.py
06_AGENTS/Excalidraw-Target-Response-Latest-Resolver.md
```

Current result:

```text
status: excalidraw_target_response_resolution_pending_external_runtime
target_url: ""
```

This resolver scans only the untrusted pending response folder and lets a future accepted loopback response artifact be discovered without a code edit. It does not install dependencies, start or probe a target, launch a browser, connect CDP, invoke MCP, navigate, read real profiles/credentials/cookies, write trusted skills, activate skills, enqueue Agent Bus work, call providers, mutate Gate, or write canonical state.

Current Excalidraw readiness from target response:

```powershell
python -m runtime.browser_runtime.excalidraw_readiness_from_response --vault-root . --write-bridge --json
```

Evidence:

```text
07_LOGS/Browser-Runs/excalidraw_readiness_from_target_response_20260503_blocked_pending.json
06_AGENTS/Excalidraw-Readiness-From-Target-Response.md
```

Current result:

```text
status: blocked_excalidraw_readiness_from_response_pending_external_runtime
next_recommended_pass: external-runtime-provide-excalidraw-target-url
```

This bridge composes an accepted loopback target response into the existing no-execution live-readiness gate. It currently blocks because the response is pending and contains no `target_url`. It performs no install, server start, network probe, browser launch, CDP connection, MCP invocation, navigation, trusted write, activation, Agent Bus/provider call, Gate mutation, or canonical writeback.

Current Excalidraw browser/MCP execution approval:

```powershell
python -m runtime.browser_runtime.excalidraw_mcp_execution_approval --vault-root . --json
```

Evidence:

```text
runtime/browser_runtime/excalidraw_mcp_execution_approval.py
runtime/browser_runtime/test_excalidraw_mcp_execution_approval.py
06_AGENTS/Excalidraw-Browser-MCP-Execution-Approval.md
```

Current result:

```text
status: blocked_excalidraw_mcp_execution_approval
next_step: external-runtime-provide-excalidraw-target-url
```

This no-write contract computes the future approval preview and exact-once marker path for a local Excalidraw canvas proof. It currently blocks because the response-to-readiness bridge is still pending. It performs no approval write, approval consumption, marker reservation, browser launch, CDP connection, MCP invocation, navigation, trusted write, activation, Agent Bus/provider call, Gate mutation, or canonical writeback.

Current Excalidraw browser/MCP proof execution shell:

```powershell
python -m runtime.browser_runtime.excalidraw_mcp_proof_execution --vault-root . --json
```

Evidence:

```text
runtime/browser_runtime/excalidraw_mcp_proof_execution.py
runtime/browser_runtime/test_excalidraw_mcp_proof_execution.py
06_AGENTS/Excalidraw-Browser-MCP-Proof-Execution-Shell.md
```

Current result:

```text
status: blocked_excalidraw_mcp_proof_execution_approval_not_ready
next_step: external-runtime-provide-excalidraw-target-url
```

This fail-closed shell validates approval/readiness/idempotency posture and
computes the future proof artifact plan. It does not write approvals, consume
decisions, reserve markers, launch browsers, connect CDP, invoke MCP, navigate,
capture screenshots, write draft skills, activate skills, enqueue Agent Bus
work, call providers, mutate Gate, or write canonical state.

Current Excalidraw live-chain readiness reporter:

```powershell
python -m runtime.browser_runtime.excalidraw_live_chain_readiness --vault-root . --json
```

Evidence:

```text
runtime/browser_runtime/excalidraw_live_chain_readiness.py
runtime/browser_runtime/test_excalidraw_live_chain_readiness.py
06_AGENTS/Excalidraw-Live-Chain-Readiness.md
```

Current result:

```text
status: blocked_excalidraw_live_chain_readiness_target_response_not_accepted
next_recommended_pass: external-runtime-provide-excalidraw-target-url
```

This read-only reporter composes target response resolution, readiness,
approval, and proof-shell status into one chain status. It performs no
dependency install, server start, target probe, browser launch, CDP connection,
MCP invocation, navigation, screenshot capture, run-log write, activity-log
write, skill write, skill activation, Agent Bus/provider call, Gate mutation, or
canonical writeback.

Current Browser Runtime completion estimate:

```powershell
python -m runtime.browser_runtime.completion_estimate --vault-root . --json
```

Current result:

```text
status: browser_runtime_completion_estimate_production_blocked
remaining_major_passes: 2-4
```

This read-only reporter converts the current completion blockers into pass
groups. It writes no estimate artifact, Browser Run log, Agent Activity log,
skill memory, Gate policy, Agent Bus task, provider output, or canonical state.

## Browser Use / Browser Harness Comparison

| Reference | Useful Pattern | ChaseOS Decision |
| --- | --- | --- |
| `browser-use/browser-use` | Browser agent, CLI, state, screenshots, persistent sessions | Wrap only behind AOR/Gate. `browser-use-cli` wrapper is fail-closed and dependency-free. |
| `browser-use/browser-harness` | Thin CDP harness and domain/interaction skills | Reference-only decision recorded; adopt skill-memory patterns, do not adopt raw harness authority. Real-profile attachment remains forbidden by default. |
| `browser-use/browser-harness-js` | Typed CDP method surface over a persistent session | Reference only. Too much raw authority for direct adoption. |
| `browser-use/workflow-use` | Run once, generate workflow, store/reuse | Reference only. ChaseOS now has a native inactive cache foundation, disabled validation/planning executor, read-only execution-readiness preflight, reviewed local trial candidate, and no-write replay approval/idempotency contract; no workflow-use code copied and no live replay execution built. |
| `browser-use/web-ui` | Browser agent UI, own-browser support, persistent sessions | UI/reference only; own-browser session support is explicitly forbidden by default. |
| `yctimlin/mcp_excalidraw` | Local canvas server plus MCP tools and screenshots | Future local-only canvas test candidate. |

## Expected Artifacts

- Browser Run Log: `07_LOGS/Browser-Runs/<run_id>.json`
- Screenshot or proof artifact: `07_LOGS/Browser-Runs/<run_id>-*.png` or placeholder in shadow mode
- Agent Activity Log: `07_LOGS/Agent-Activity/<run_id>.md`
- Draft Site Skill: `06_AGENTS/Browser-Skills/_drafts/<draft_id>.md`
- Build Log and Documentation History notes for any implementation pass

## Success Criteria

- Browser runtime provider is selected through an explicit config.
- The run uses throwaway or isolated browser state.
- URL/domain scope is allowlisted.
- The run records all actions.
- Screenshots/artifacts are retained only under approved log paths.
- Generated site skill remains draft-only.
- No cookies, credentials, tokens, saved sessions, or real profile paths are retained.
- No canonical ChaseOS note, SiteOps registry object, or runtime profile is promoted automatically.

## Failure Modes

- Browser provider unavailable.
- Browser launch blocked by local dependency or sandbox.
- Domain not allowlisted.
- Page redirects outside allowed domain.
- Auth wall encountered.
- Screenshot capture fails.
- Selector/state extraction is incomplete.
- Website content attempts prompt injection.
- Draft candidate would include sensitive content and must be suppressed or redacted.

## Security Constraints

- No real Chrome profile by default.
- No saved credentials by default.
- No shell execution from browser runtime.
- No network connectors beyond explicit browser navigation.
- No cookies export.
- No browser profile sync.
- No public tunnel.
- No automatic skill activation.
- No canonical writeback.
- Every browser run must be logged.
- Every generated skill candidate must link back to run evidence.

## Current Deferred Items

- VincisOS readiness preflight: verified no-execution.
- VincisOS static local target preflight: verified with temporary `127.0.0.1` server and no browser launch.
- VincisOS first local browser attempt: blocked because no active Codex in-app browser pane was available; no page was opened.
- VincisOS local in-app browser proof: verified against the repo-local static target with Browser Run evidence, screenshot artifact, and draft-only skill memory.
- VincisOS draft skill replay proof: verified against the same repo-local static target with Browser Run evidence, screenshot artifact, and draft replay evidence; primary selector resolved but in-app browser click required a local visible fallback.
- VincisOS fresh-tab click hardening proof: verified stored selector click succeeds from a fresh in-app browser tab; the earlier screenshot capture blocker is retained as historical evidence.
- VincisOS screenshot artifact hardening proof: verified `tab.cua.get_visible_screenshot().toBase64()` saves a fresh 23,988-byte screenshot artifact under `07_LOGS/Browser-Runs/`; bounded static-fixture MVP is complete.
- Browser Runtime feature readiness tracker: current; bounded static-fixture MVP is complete and production feature remains not done.
- Browser Runtime completion-status reporter: verified; bounded MVP reports done, production feature reports not done, and current blockers are machine-readable.
- Browser Use CLI live validation: blocked-unavailable; read-only preflight found no `browser-use` executable and wrote `07_LOGS/Browser-Runs/browser_use_cli_live_validation_20260502_blocked_unavailable.json`; no dependency install, CLI invocation, browser launch, profile/credential/cookie/session access, trusted write, activation, Agent Bus/provider call, Gate mutation, or canonical writeback occurred.
- VincisOS full product UI safe-mode preflight: verified; current old fixture URL is blocked as static fixture / not reachable.
- VincisOS full product UI target contract validator: verified; example local product UI contract validates without execution, and the current old fixture URL is blocked as static fixture / not product UI.
- VincisOS contract-backed proof planner: verified; example local product UI contract produces a no-execution proof plan, the 2026-05-02 dual-track run returned `vincisos_contract_backed_proof_plan_ready_no_execution`, and the current old fixture URL remains blocked.
- VincisOS full product UI browser proof: verified against the registered local Studio Product UI Test Target with Browser Run, screenshot, Agent Activity, draft skill, and untrusted candidate evidence; this closes the VincisOS product UI proof gate only, not the full Browser Runtime production feature.
- Excalidraw BOSL shadow-plan proof: verified; fresh 2026-05-02 shadow proof wrote Browser Run, Agent Activity, proof text, and untrusted candidate artifacts without live browser control.
- Excalidraw browser/MCP proof prep: verified no-execution; prep evidence writes only `07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_proof_prep_20260503_ready.json` and keeps browser launch, MCP invocation, navigation, real-profile, credentials/cookies, trusted writes, activation, Agent Bus/provider, Gate, and canonical effects false.
- Excalidraw browser/MCP live readiness: verified no-execution and safely blocked on missing local loopback target; current evidence is `07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_blocked_missing_local_target.json`.
- Excalidraw local target setup instructions: verified no-execution; current evidence is `07_LOGS/Browser-Runs/excalidraw_local_target_setup_instructions_20260503_ready.json`, and the next gate is `external-runtime-provide-excalidraw-target-url` until an accepted loopback target response exists.
- Excalidraw local target contract request: verified no-execution; current evidence is `07_LOGS/Browser-Runs/excalidraw_local_target_contract_request_20260503_ready.json`, and the external runtime still needs to provide the loopback URL.
- Excalidraw local target response intake: verified no-execution; current evidence is `03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_pending.json`, and the external runtime still needs to provide the loopback URL.
- Excalidraw target response latest resolver: verified no-execution; `runtime.browser_runtime.excalidraw_target_response_resolver` scans only `03_INPUTS/Browser-Target-Responses/_pending/` and selects the latest accepted or pending response without target probing, browser launch, CDP, MCP, trusted writes, activation, Gate mutation, or canonical writeback.
- Excalidraw readiness from target response: verified no-execution and CLI-wired through `chaseos operate browser excalidraw-readiness-from-response`; current evidence is `07_LOGS/Browser-Runs/excalidraw_readiness_from_target_response_20260503_blocked_pending.json`, and the bridge blocks until an accepted loopback target response exists.
- Excalidraw public live browser proof: verified complete targeted after the operator supplied `https://excalidraw.com/`; current evidence is `07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.json`, `07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.png`, `07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.md`, and `06_AGENTS/Excalidraw-Public-Live-Browser-Proof.md`. The run proves navigation, title, canvas presence, and screenshot capture only. It does not prove drawing, MCP invocation, approval execution, skill memory, Gate mutation, Agent Bus writes, provider calls, or canonical writeback.
- Excalidraw browser/MCP execution approval: verified no-write; `runtime.browser_runtime.excalidraw_mcp_execution_approval` computes the future approval request preview and exact-once marker path while writing no approval, consuming no decision, reserving no marker, and attempting no browser/CDP/MCP action.
- Excalidraw browser/MCP proof execution shell: verified fail-closed/no-execution; `runtime.browser_runtime.excalidraw_mcp_proof_execution` validates approval/readiness/idempotency posture and computes the future artifact plan while writing no approval, consuming no decision, reserving no marker, launching no browser, invoking no MCP, and writing no skill memory.
- Excalidraw live-chain readiness reporter: verified read-only/no-execution; `runtime.browser_runtime.excalidraw_live_chain_readiness` composes target response resolution, readiness, approval, and proof-shell status while writing no artifacts and attempting no browser/CDP/MCP action.
- Browser Runtime completion estimate: verified read-only/no-execution; `runtime.browser_runtime.completion_estimate` now reports `0-0` remaining major passes after the public drawing-proof run, without writing artifacts or attempting browser/CDP/MCP action.
- Excalidraw live browser/MCP test: public no-login drawing proof is complete targeted with approval, exact-once marker, screenshot, JSON, and Agent Activity evidence. The stricter local path remains optional and still requires a local loopback target URL plus no-execution readiness rerun before any local MCP proof.
- CDP design preflight scaffold: verified no-execution.
- CDP read-only proof Gate schema: verified declared-but-blocked; `browser.cdp.read_only_proof` exposes `bosl.cdp_read_only_proof.v1` and returns denied without browser launch or CDP connection.
- CDP read-only proof approval artifacts: verified request-only; `chaseos runtime browser-cdp approval-request --write-approval-request` writes pending review records and structural validation keeps execution disallowed.
- CDP read-only proof executor-spec: verified no-execution; `chaseos runtime browser-cdp executor-spec` reports the injected executor contract while leaving browser launch, CDP connection, trusted writes, and canonical writeback false.
- CDP read-only proof decision preflight: verified no-execution; `chaseos runtime browser-cdp decision-preflight --gate-approval-id <id>` reports approval status, future idempotency-marker posture, and bounded future write-plan targets while leaving approval consumption, marker writes, browser launch, CDP connection, screenshot/DOM capture, trusted writes, and canonical writeback false.
- CDP read-only proof idempotency reservation spec: verified no-execution; `chaseos runtime browser-cdp idempotency-reservation-spec --gate-approval-id <id>` returns marker path, marker record template, atomic create-new rules, and blocked status while leaving approval consumption, marker writes, browser launch, CDP connection, screenshot/DOM capture, trusted writes, and canonical writeback false.
- CDP read-only proof executor dry-run: verified no-execution; `chaseos runtime browser-cdp executor-dry-run --gate-approval-id <id>` returns executor sequence, stop conditions, artifact plan, and feature completion tracker while leaving approval consumption, marker writes, browser launch, CDP connection, screenshot/DOM capture, trusted writes, and canonical writeback false.
- CDP read-only proof approval-decision policy: verified no-execution; `chaseos runtime browser-cdp approval-decision-policy --gate-approval-id <id>` returns decision record template and consumption rules while leaving decision writes, approval consumption, marker writes, browser launch, CDP connection, screenshot/DOM capture, trusted writes, and canonical writeback false.
- CDP read-only proof approval decision consumer design: verified no-execution; `chaseos runtime browser-cdp approval-decision-consumer-design --gate-approval-id <id>` returns the single-use consumer algorithm, request/decision binding checks, marker-absence guard, consumption record template, and forbidden field policy while leaving decision writes, approval consumption, marker writes, browser launch, CDP connection, screenshot/DOM capture, trusted writes, and canonical writeback false.
- CDP read-only proof atomic marker writer design: verified no-write; `chaseos runtime browser-cdp atomic-marker-writer-design --gate-approval-id <id>` returns the exclusive-create marker write algorithm, path constraints, marker template, and failure/retry policy while leaving approval consumption, marker-directory creation, marker writes, browser launch, CDP connection, screenshot/DOM capture, trusted writes, and canonical writeback false.
- CDP read-only proof isolated browser launcher design: verified no-launch; `chaseos runtime browser-cdp isolated-browser-launcher-design --gate-approval-id <id>` returns the throwaway-profile launch contract while leaving browser process spawn, throwaway profile creation, CDP port opening, CDP connection, marker writes, proof artifacts, trusted writes, and canonical writeback false.
- CDP read-only proof isolated launcher implementation preflight: verified no-launch; `chaseos runtime browser-cdp isolated-launcher-implementation-preflight --gate-approval-id <id>` reports live launcher/client code presence plus opaque implementation metadata checks while leaving browser process spawn, throwaway profile creation, CDP port opening, CDP connection, marker writes, proof artifacts, trusted writes, and canonical writeback false.
- CDP bounded live read-only executor: verified complete-targeted by Hermes/Optimus activation evidence; approval request -> approval decision -> execute succeeded against a throwaway localhost target with isolated profile, local CDP, screenshot/DOM proof, idempotency marker, Browser Run, Agent Activity, and untrusted candidate artifacts. This does not authorize unrestricted CDP, real profiles, credentials/cookies/session reads, trusted skill writes, Agent Bus/provider calls, Gate mutation, canonical writeback, or VincisOS product UI completion.
- CDP injected proof executor: verified with fake launcher/CDP-client collaborators; writes bounded Browser Run, Agent Activity, screenshot, DOM, and untrusted candidate artifacts only in the injected test harness.
- CDP default live proof code path: implemented and Hermes-activated for the current local throwaway-profile read-only smoke; approval consumption and marker writing remain false when executable discovery fails in environments without Chromium.
- Browser Harness direct CDP adapter: deferred.
- Browser Use Python API adapter: deferred.
- Workflow replay executor implementation: verified disabled-by-default; validates/plans only, returns `workflow_replay_executor_disabled_no_workflow_selected` when no workflow is selected, and keeps replay execution deferred.
- Workflow replay execution readiness preflight: verified read-only; reports `workflow_replay_execution_readiness_ready_no_execution` when the reviewed local trial candidate is selected, and keeps all browser/runtime/writeback side effects false.
- Workflow replay trial candidate selection: verified targeted; selected `wf-127-0-0-1-vincisos-product-ui-safe-panel-inspection-trial-20260502` from the local VincisOS product UI proof while keeping activation, trusted writes, live replay, browser launch, CDP, Browser Harness, Browser Use CLI live, Agent Bus, providers, Gate mutation, and canonical writeback false.
- Workflow replay execution approval/idempotency: verified no-write; `runtime.browser_runtime.workflow_replay_execution_approval` binds the selected local workflow, approval preview, and exact-once marker path while writing no approval request, consuming no decision, reserving no marker, replaying no browser actions, and keeping launch/CDP/profile/credential/trusted-write/canonical flags false.
- Workflow replay execution: deferred; inactive cache foundation, no-execution executor design preflight, no-write implementation request, no-write implementation approval, disabled validation/planning executor, and read-only readiness preflight exist.
- webagents.md discovery: deferred.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
