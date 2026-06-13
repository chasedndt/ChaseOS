---
title: SiteOps Browser Skill Shadow Execution Approval Decision Request
type: architecture-note
status: COMPLETE TARGETED / GUARDED DECISION PATH BUILT / LIVE DECISION NOT WRITTEN
created: 2026-05-04
updated: 2026-05-04
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Browser Skill Shadow Execution Approval Decision Request

This pass adds the guarded decision path for the pending Browser Skill shadow
execution ApprovalRequest. The command can preview an approve/reject decision
without mutation, and can write only the approval decision when the explicit
`--write-approval-decision` flag is present.

## Command

```powershell
python -m runtime.cli.main siteops candidates browser-skill-shadow-execution-approval-decision-request <candidate_id> --shadow-execution-approval-id <approval_id> --source-approval-id <approval_id> --activation-approval-id <approval_id> --decision approve --tenant local --workspace default --user local-user --actor local-user --target-url http://localhost:8765/shadow --shadow-mode --local-target-only --json
```

Decision writes require:

```powershell
--write-approval-decision
```

## Live Result

The live local smoke intentionally omitted `--write-approval-decision` and
returned:

```text
shadow_execution_approval_decision_ready_no_write
```

The live approval remains `pending`. No live approval decision was written.

## Write Boundary

When the explicit write flag is used, the backend may write only the scoped
ApprovalRequest status and approval-decision audit metadata through the existing
SiteOps approval path. It still does not consume the approval or proceed to
execution proof.

## Checks

- Composes the no-mutation approval decision preflight.
- Requires the pending ApprovalRequest to match tenant/workspace/user, action,
  candidate, proposed skill, target URL, source approval ID, activation
  approval ID, Browser Run digest, evidence-review digest, and future write
  set.
- Accepts only `approve` or `reject`.
- Preview mode returns `shadow_execution_approval_decision_ready_no_write`.
- Explicit write mode in temp-vault tests returns
  `shadow_execution_approval_decision_written`.
- Approved decisions only make the future proof pass eligible; they do not run
  proof.

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

`siteops-browser-skill-shadow-execution-approval-live-decision`

That pass should write an actual approve/reject decision only if the operator
explicitly authorizes it. The later proof pass must consume the approved request
explicitly and remain guarded.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
