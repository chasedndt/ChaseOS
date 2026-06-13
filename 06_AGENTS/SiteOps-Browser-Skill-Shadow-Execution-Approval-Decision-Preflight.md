---
title: SiteOps Browser Skill Shadow Execution Approval Decision Preflight
type: architecture-note
status: COMPLETE TARGETED / NO-MUTATION PREFLIGHT / APPROVAL STILL PENDING
created: 2026-05-04
updated: 2026-05-04
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Browser Skill Shadow Execution Approval Decision Preflight

This pass adds a no-mutation preflight over the pending Browser Skill shadow
execution ApprovalRequest. It verifies whether the approval object is still
bound to the reviewed evidence chain before any future executor can consume it.

## Command

```powershell
python -m runtime.cli.main siteops candidates browser-skill-shadow-execution-approval-decision-preflight <candidate_id> --shadow-execution-approval-id <approval_id> --source-approval-id <approval_id> --activation-approval-id <approval_id> --tenant local --workspace default --user local-user --actor local-user --target-url http://localhost:8765/shadow --shadow-mode --local-target-only --json
```

## Live Result

The live local candidate returned:

```text
blocked_pending_shadow_execution_approval
```

All required metadata/provenance checks passed. The block is only that the
ApprovalRequest remains `pending`.

## Checks

- Approval scope matches tenant/workspace/user.
- Approval action is
  `browser_skill_candidate.browser_skill_shadow_execution_proof`.
- Candidate, proposed skill, target URL, source approval ID, and activation
  approval ID match the approval metadata.
- Browser Run SHA-256 matches the reviewed replay evidence.
- Evidence-review closeout SHA-256 matches the approval metadata.
- Evidence refs match the scoped reviewed evidence paths.
- Future Browser Run and Agent Activity proof paths match the approval request
  and remain create-new targets.
- Required approver role is `approver`.
- Target URL policy still allows only local or explicitly allowlisted targets.
- Approval metadata contains no forbidden secret/session fields.

## Explicitly Not Done

- No approval decision was written.
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

`siteops-browser-skill-shadow-execution-approval-decision-request`

That pass should create an explicit operator decision packet for approving or
rejecting the pending request. It should still stop before consuming the
approval or running shadow execution proof.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
