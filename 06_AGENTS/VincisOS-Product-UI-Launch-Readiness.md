---
title: VincisOS Product UI Launch Readiness
type: runtime-spec
status: complete targeted / launch target registered
created: 2026-05-02
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter
runtime: Codex
---

# VincisOS Product UI Launch Readiness

This read-only gate checks whether ChaseOS has a registered local product UI launch surface that can satisfy the future VincisOS browser proof.

It exists because the target contract can be valid while the actual local product UI is still absent or not registered.

## Surface

```powershell
python -m runtime.browser_runtime.vincisos_product_ui_launch_readiness --vault-root . --json
```

The command reads the existing Studio App Launcher registry and health metadata. It does not start child apps.

## Current Result

Current live result after the Studio Product UI Test Target pass:

```text
status: vincisos_product_ui_launch_target_ready_no_start
discovered_app_count: 7
candidate_app_count: 1
```

The registered browser-proof target is:

- `vincisos-product-ui-test-target`

It points to `http://127.0.0.1:8770/`, runs through `runtime.studio.product_ui_test_app`, and remains local-only/read-only/safe-mode.

## Allowed

- Read the Studio App Launcher registry.
- Perform the launcher registry's short read-only localhost health probes.
- Report discovered local apps and candidate count.
- Return machine-readable blockers.

## Forbidden

- Starting servers or child apps.
- Shell command execution.
- Browser launch.
- CDP connection.
- Browser Harness attachment.
- Browser Use CLI live execution.
- Real profile access.
- Credential, cookie, or session-token reads.
- Trusted skill writes or activation.
- Agent Bus enqueue.
- Provider calls.
- Gate mutation.
- Canonical ChaseOS writeback.

## Production Meaning

This gate does not complete Browser Runtime production. It only clears the launch-registration prerequisite. The product UI target must still be reachable, and then a separate isolated browser proof must record browser run, screenshot, harmless action, Agent Activity, and draft-only candidate evidence.

The required order is:

1. Keep the registered local product UI test target available.
2. Pass `vincisos_product_ui_target_probe`.
3. Run the isolated browser proof.
4. Keep all proof artifacts draft/log-only until reviewed.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
