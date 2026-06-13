---
title: SiteOps Candidate Activation Executor Live Readiness
type: runtime-contract
status: COMPLETE TARGETED / READ-ONLY LIVE READINESS
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9
feature_family: SiteOps Browser Skill activation
---

# SiteOps Candidate Activation Executor Live Readiness

`siteops candidates activation-executor-live-readiness` is the read-only live
readiness surface for the guarded activation executor.

It validates or discovers the scoped source promotion approval and activation
approval IDs, then runs the activation executor only in dry-run mode. It
previews the exact future guarded activation command with
`--activate-trusted-artifact`, but never supplies that flag internally.

## Checks

The readiness packet reports:

- source promotion approval ID presence and approval posture
- activation approval ID presence and approval posture
- consumed activation marker evidence through the existing executor dry-run
- inactive trusted Browser Skill artifact posture
- inactive SiteOps Skill Card artifact posture
- scoped absent activation-record path when computable
- ChaseOS Gate posture for
  `siteops.browser_skill_candidate.activate_trusted_artifact`
- exact guarded activation command preview

## Boundary

This command does not:

- activate trusted artifacts
- write activation records
- append activation audit events
- mutate trusted Browser Skill artifacts
- mutate SiteOps Skill Card artifacts
- consume approvals or mutate ApprovalRequest status
- launch or control a browser/CDP session
- enqueue Agent Bus work
- call providers or external APIs
- mutate Gate policy
- write canonical ChaseOS memory/state

## Status

The command is implemented and tested. The live local candidate
`candidate_browser_runtime_20260430_022607_example-com` currently reports:

```text
blocked_activation_consumption_live_readiness: blocked_missing_source_promotion_approval_id
```

That means the guarded activation writer exists, but real-vault activation is
not ready. A real scoped approval pair, consumed marker, inactive trusted
artifacts, and Gate allowance are still required before any activation command
can be run.

Browser execution/replay remains a separate future feature and must begin in
shadow mode.

## Verification

Final validation for this pass:

- `python -m py_compile runtime\siteops\candidate_promotions.py runtime\cli\siteops_commands.py runtime\cli\main.py`
- `python -m pytest runtime\siteops\tests\test_candidate_promotions.py -q -k "activation_executor_live_readiness"` -> `4 passed, 186 deselected`
- `python -m pytest runtime\siteops\tests\test_candidate_promotions.py -q` -> `190 passed`
- `python -m pytest runtime\tests\test_cli_command_contract.py runtime\tests\test_cli_json_contract.py -q` -> `10 passed`
- `python -m runtime.cli.generate_docs --check` -> up to date
- fake-candidate CLI smoke -> fail-closed structured candidate-not-found JSON
- Gate file hashes unchanged after validation

A temp-vault smoke under `C:\tmp` could not be completed because the sandboxed
filesystem denied fixture directory creation. That does not change the feature
status: the successful readiness path is covered by temp-vault unit tests, and
real-vault activation remains intentionally blocked until real approval/Gate
evidence exists.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
