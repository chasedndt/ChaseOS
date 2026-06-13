---
title: SiteOps Browser Skill Shadow Execution Approval Live Decision Readiness
type: architecture-note
status: COMPLETE TARGETED / LIVE DECISION READINESS BUILT / EXPLICIT DECISION STILL REQUIRED
created: 2026-05-04
updated: 2026-05-04
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Browser Skill Shadow Execution Approval Live Decision Readiness

This pass adds a fail-closed readiness surface for the live Browser Skill shadow
execution approval decision. It verifies that an approve/reject write can be
prepared, but it does not mutate the live ApprovalRequest.

## Command

```powershell
python -m runtime.cli.main siteops candidates browser-skill-shadow-execution-approval-live-decision-readiness <candidate_id> --shadow-execution-approval-id <approval_id> --source-approval-id <approval_id> --activation-approval-id <approval_id> --intended-decision approve --tenant local --workspace default --user local-user --actor local-user --target-url http://localhost:8765/shadow --shadow-mode --local-target-only --json
```

`--intended-decision approve|reject` is optional. If it is omitted, the command
returns `blocked_missing_explicit_operator_decision`.

## Live Result

The live local smoke returned:

```text
live_decision_ready_waiting_explicit_write_authorization
approval_status: pending
explicit_operator_authorization_present: false
live_decision_written: false
approval_decision_written: false
approval_consumed: false
browser_execution_allowed: false
writes_performed: false
```

The live ApprovalRequest remains pending:

```text
approval_siteops_shadow_exec_20260504_091240_candidate-browser-runtime-202604_browser_skill_candidate_browser_skill_shadow_execution_proof
```

## Purpose

This readiness layer prevents a generic instruction such as "continue" from
becoming an implicit high-risk approval. The next mutating pass needs explicit
operator language saying whether to approve or reject the pending request.

## Explicitly Not Done

- No live approval decision was written.
- No approval was consumed.
- No browser/CDP was launched.
- No authenticated browser session was used.
- No cookies, tokens, secrets, localStorage, sessionStorage, or account state
  were read.
- No DOM mutation, form submit, publish, purchase, trade, or account mutation
  occurred.
- No execution proof was written.
- No trusted Browser Skill or SiteOps Skill Card artifact was promoted.
- No activation, Agent Bus/provider call, Gate mutation, Hermes authority
  expansion, or canonical ChaseOS memory/state writeback occurred.

## Next Pass

Next recommended pass:

`siteops-browser-skill-shadow-execution-approval-live-decision-write`

That pass should run only after the operator explicitly says either:

- approve the pending shadow execution ApprovalRequest
- reject the pending shadow execution ApprovalRequest


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
