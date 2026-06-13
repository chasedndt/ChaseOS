---
title: VincisOS Product UI Target Availability Preflight
type: runtime-spec
status: complete targeted / current target reachable
created: 2026-05-02
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter
runtime: Codex
---

# VincisOS Product UI Target Availability Preflight

This preflight is the production-enabling gate between the VincisOS full UI target contract and any later browser proof.

It answers one narrow question: does the declared local safe-mode product UI target answer a local HTTP request right now?

## Surface

```powershell
python -m runtime.browser_runtime.vincisos_product_ui_target_probe --contract-json runtime/browser_runtime/test_targets/vincisos_full_ui_target_contract.example.json --json
```

The probe validates the `vincisos.full_ui_target.v1` contract first. If the contract is not ready, the probe does not perform an HTTP request.

If the contract is ready, the probe performs a local HTTP GET against the declared target URL only. This is not browser automation and not a DOM inspection.

## Allowed

- Validate the VincisOS full UI target contract.
- Make one local HTTP availability request to an allowlisted loopback target.
- Report whether the local product UI target is reachable.
- Return machine-readable blockers.
- Keep all browser, CDP, profile, credential, cookie/session, provider, Gate, Agent Bus, trusted-write, and canonical-writeback flags false.

## Forbidden

- Browser launch.
- CDP connection.
- Browser Harness attachment.
- Browser Use CLI live execution.
- Real browser profile access.
- Credential, cookie, or session-token reads.
- DOM inspection.
- Screenshot capture.
- UI clicks or text entry.
- Trusted Browser Skill writes.
- Skill activation.
- Agent Bus enqueue.
- Provider/API calls.
- Gate mutation.
- Canonical ChaseOS writeback.

## Current Result

The example contract now targets the ChaseOS Studio Product UI Test Target:

```text
target_url: http://127.0.0.1:8770/
contract_status: vincisos_full_ui_target_contract_ready_no_execution
```

Current live result after the Studio Product UI Test Target pass:

```text
status: vincisos_product_ui_target_available_no_browser
http_status: 200
browser_launch_attempted: false
cdp_connection_attempted: false
credential/cookie/session read: false
files_modified by probe: false
canonical_writeback_attempted: false
```

## Relationship To Production Browser Runtime

This preflight is required before the next real product UI browser proof, but it does not complete that proof.

Production Browser Runtime remains blocked until a separate isolated browser proof records open, state read, screenshot, one harmless action, Browser Run evidence, Agent Activity evidence, and draft-only skill/candidate evidence.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
