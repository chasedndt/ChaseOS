---
title: SiteOps Candidate Source Approval Rebind Live Readiness
type: runtime-hardening
status: COMPLETE TARGETED / READ-ONLY LIVE READINESS
created: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Source Approval Rebind Live Readiness

`siteops candidates source-approval-rebind-live-readiness` reports whether a
Browser Skill candidate has a usable scoped source-promotion approval, or whether
a legacy/unbound approval must be replaced with a bound approval request.

This is a read-only readiness surface. It inventories source approval requests,
detects legacy-unbound approvals from historical approval text, composes the
existing approval rebind spec and bound approval writer dry-run, and previews the
exact replacement approval writer command.

## Live Result

The live local candidate
`candidate_browser_runtime_20260430_022607_example-com` now reports:

- `source_approval_rebind_live_readiness_status:
  source_approval_rebind_live_readiness_ready_no_write`
- selected approved legacy approval:
  `approval_siteops_candidate_20260430_062942_candidate-browser-runtime-20260430-022607-example-com_browser_skill_candidate_promote`
- pending legacy approval also present:
  `approval_siteops_candidate_20260430_063855_candidate-browser-runtime-20260430-022607-example-com_browser_skill_candidate_promote`
- no bound source approval exists yet
- replacement source approval dry-run is ready
- replacement source approval was not written

## Boundaries

This command does not:

- mutate legacy approval artifacts
- write replacement approval requests
- decide or consume approvals
- write trusted Browser Skill artifacts
- write SiteOps Skill Card artifacts
- activate skills
- launch or control a browser
- enqueue Agent Bus work
- call providers
- mutate Gate policy
- write canonical ChaseOS memory/state

## Next Step

The next pass may run the already-built guarded writer with explicit operator
intent:

```powershell
python -m runtime.cli.main siteops candidates bound-approval-writer-implementation candidate_browser_runtime_20260430_022607_example-com --approval-id approval_siteops_candidate_20260430_062942_candidate-browser-runtime-20260430-022607-example-com_browser_skill_candidate_promote --tenant local --workspace default --user local-user --actor local-user --write-replacement-approval --json
```

That next pass should write only the pending bound replacement source approval
request plus scoped run/audit/idempotency/recovery evidence. It must still not
write trusted artifacts, consume approvals, activate, mutate Gate, run browsers,
or write canonical state.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
