---
title: ChaseOS Studio Product UI Test Target
type: runtime-spec
status: complete targeted / local target proof verified
created: 2026-05-02
updated: 2026-05-02
phase: Phase 9 Browser Runtime Adapter / Phase 10 Studio bridge
runtime: Codex
---

# ChaseOS Studio Product UI Test Target

This note defines the local product UI test target built for Browser Runtime production proofing.

It is not the final ChaseOS Studio product shell. It is a deterministic safe-mode UI target that is complex enough for browser runtime testing without granting real account, credential, workflow, Gate, provider, Agent Bus, trusted-write, or canonical-writeback authority.

## Surfaces

Model:

```text
runtime/studio/product_ui_test_model.py
```

Local app:

```text
runtime/studio/product_ui_test_app.py
```

CLI:

```powershell
python -m runtime.cli.main studio product-ui-test-app --vault-root . --host 127.0.0.1 --port 8770 --dry-run --json
```

Registered target URL:

```text
http://127.0.0.1:8770/
```

Health:

```text
http://127.0.0.1:8770/health.json
```

## Browser Proof Selectors

- root: `[data-testid='studio-product-ui-root']`
- safe mode banner: `[data-testid='safe-mode-banner']`
- overview tab: `[data-testid='tab-overview']`
- approvals tab: `[data-testid='tab-approvals']`
- workflow tab: `[data-testid='tab-workflow']`
- task table: `[data-testid='task-table']`
- approval table: `[data-testid='approval-table']`
- harmless action: `[data-testid='harmless-inspect-action']`
- status output: `[data-testid='action-status']`

## Safe Harmless Action

The only intended browser-proof action is:

```text
Mark panel inspected
```

Expected result:

```text
Panel inspected in safe mode.
```

The action is client-side only and does not call the server after page load.

## Authority Boundary

Allowed:

- local loopback serving,
- read-only deterministic model rendering,
- client-side tab switching,
- client-side harmless inspection state change,
- `/health.json` and `/product-ui.json` reads.

Forbidden:

- credentials, cookies, or session-token reads,
- real browser profiles,
- external accounts,
- provider calls,
- Agent Bus enqueue,
- Gate mutation,
- workflow execution,
- trusted Browser Skill or SiteOps writes,
- skill activation,
- canonical ChaseOS writeback.

## Current Verification

Current pass verification:

```text
launch readiness: vincisos_product_ui_launch_target_ready_no_start
target availability: vincisos_product_ui_target_available_no_browser
contract-backed planner: vincisos_contract_backed_proof_plan_ready_no_execution
browser proof: vincisos_product_ui_browser_proof_20260502_success
```

Browser proof evidence:

```text
07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_success.json
07_LOGS/Browser-Runs/vincisos_product_ui_browser_proof_20260502_screenshot.png
07_LOGS/Agent-Activity/2026-05-02-codex-vincisos-product-ui-browser-proof.md
06_AGENTS/Browser-Skills/_drafts/draft-vincisos-product-ui-browser-proof-20260502.md
03_INPUTS/Browser-Skill-Candidates/127-0-0-1/20260502__candidate-vincisos-product-ui-browser-proof-20260502.md
```

The target has now completed the isolated local product UI proof. This does not authorize real-account browsing, Browser Use CLI live authority, workflow replay execution, trusted skill promotion, or canonical writeback.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
