---
title: VincisOS Contract-Backed Proof Plan
type: runtime-plan
status: implemented planner / no browser execution
created: 2026-05-02
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter
runtime: Codex
---

# VincisOS Contract-Backed Proof Plan

This note records the no-execution planner for a future full VincisOS product UI browser proof. It composes the `vincisos.full_ui_target.v1` target contract into a proof action plan and artifact plan, but it does not open a browser or write proof artifacts.

## Planner

Runtime planner:

```powershell
python -m runtime.browser_runtime.vincisos_contract_backed_proof --contract-json runtime/browser_runtime/test_targets/vincisos_full_ui_target_contract.example.json --run-id vincisos_full_ui_contract_backed_proof_20260502 --json
```

Implementation:

```text
runtime/browser_runtime/vincisos_contract_backed_proof.py
```

The planner returns `vincisos_contract_backed_proof_plan_ready_no_execution` only when the target contract is valid. That status means the future proof has a plan; it does not mean the product UI was opened or tested.

## Planned Future Proof Shape

Planned actions:

1. Validate `vincisos.full_ui_target.v1`.
2. Open the local target in a future isolated browser context.
3. Read UI state.
4. Capture screenshot.
5. Perform one operator-approved harmless local UI action.
6. Write Browser Run, Agent Activity, screenshot, draft skill, and untrusted skill-candidate evidence.

Planned artifact classes:

```text
07_LOGS/Browser-Runs/<run_id>.json
07_LOGS/Agent-Activity/<run_id>.md
07_LOGS/Browser-Runs/<run_id>_screenshot.png
06_AGENTS/Browser-Skills/_drafts/<run_id>.md
03_INPUTS/Browser-Skill-Candidates/vincisos-local/<run_id>.md
```

## Current Blocked Target

The current in-app browser URL is still the old static fixture:

```text
http://127.0.0.1:63479/vincisos_shadow.html
```

Blocked planner evidence:

```text
07_LOGS/Browser-Runs/vincisos_contract_backed_proof_plan_20260502_blocked_static_fixture.json
```

The block reasons are `target_contract_not_ready` and `static_fixture_is_not_product_ui`.

## Denied Authority

The planner keeps these false:

- browser launch attempted
- screenshot attempted
- CDP connection attempted
- Browser Harness used
- Browser Use CLI live used
- real profile used
- credentials or cookies read
- trusted Browser Skill or SiteOps Skill Card write
- skill activation
- Agent Bus enqueue
- provider call
- Gate mutation
- canonical writeback

## Next Allowed Step

The next real proof may run only after an actual local VincisOS product UI exists in safe/test mode, the target contract points at it, and the operator accepts an isolated-profile browser proof that writes draft/log artifacts only.

## Graph Links

[[VincisOS-Full-UI-Target-Contract]] - [[Browser-Runtime-Test-Plan]] - [[VincisOS-Browser-Shadow-Proof]] - [[Browser-Runtime-Feature-Readiness-Tracker]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
