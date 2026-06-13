---
title: VincisOS Full UI Target Contract
type: runtime-contract
status: implemented validator / no product UI proof yet
created: 2026-05-01
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter
runtime: Codex
---

# VincisOS Full UI Target Contract

This note defines the contract required before ChaseOS may run a future browser proof against a full local VincisOS product UI. It does not authorize browser launch, CDP, Browser Harness, Browser Use live CLI execution, real browser profiles, credentials, trusted skill writes, Agent Bus enqueue, provider calls, Gate mutation, or canonical writeback.

## Validator

Runtime validator:

```powershell
python -m runtime.browser_runtime.vincisos_full_ui_target_contract --contract-json runtime/browser_runtime/test_targets/vincisos_full_ui_target_contract.example.json --json
```

Implementation:

```text
runtime/browser_runtime/vincisos_full_ui_target_contract.py
runtime/browser_runtime/test_targets/vincisos_full_ui_target_contract.example.json
```

The validator is non-executing. `ok=true` means only that a future proof has a valid local target declaration. It does not mean the product UI was opened or tested.

## Required Contract Shape

Required fields:

```json
{
  "contract_version": "vincisos.full_ui_target.v1",
  "target_name": "VincisOS local product UI safe-mode target",
  "target_url": "http://127.0.0.1:5173/",
  "target_kind": "product_ui",
  "mode": "shadow",
  "safe_mode_asserted": true,
  "safe_mode_evidence": ["operator-declared local safe-mode target"],
  "allowed_hosts": ["127.0.0.1", "localhost"],
  "allowed_actions": ["open", "read_state", "capture_screenshot", "harmless_click", "close"],
  "expected_artifacts": ["browser_run_log", "agent_activity_log", "screenshot", "draft_skill_candidate"],
  "draft_only": true,
  "forbidden_authority": {
    "allow_real_profile": false,
    "allow_credentials": false,
    "allow_cdp": false,
    "allow_browser_harness": false,
    "allow_browser_use_cli_live": false,
    "allow_trusted_skill_write": false,
    "allow_skill_activation": false,
    "allow_agent_bus_enqueue": false,
    "allow_provider_call": false,
    "allow_gate_mutation": false,
    "allow_canonical_writeback": false
  }
}
```

## Current Blocked Target

The current in-app browser URL is still the old static fixture:

```text
http://127.0.0.1:63479/vincisos_shadow.html
```

Blocked evidence:

```text
07_LOGS/Browser-Runs/vincisos_full_ui_target_contract_20260501_blocked_static_fixture.json
```

That URL is local, but it is not a full VincisOS product UI. The contract validator correctly blocks it with `static_fixture_is_not_product_ui`.

## Next Allowed Step

The next browser proof may proceed only after an actual local VincisOS product UI is running in safe/test mode and a contract using this schema points at that target. The contract must also pass the no-execution proof planner:

```powershell
python -m runtime.browser_runtime.vincisos_contract_backed_proof --contract-json <contract.json> --run-id <run_id> --json
```

The proof must remain local-only, isolated-profile, draft-only, fully logged, and non-canonical.

## Graph Links

[[Browser-Runtime-Test-Plan]] - [[VincisOS-Browser-Shadow-Proof]] - [[Browser-Runtime-Feature-Readiness-Tracker]] - [[Browser-Operator-Skill-Layer]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
