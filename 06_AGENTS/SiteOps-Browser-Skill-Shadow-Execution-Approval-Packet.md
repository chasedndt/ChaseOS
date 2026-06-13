---
title: SiteOps Browser Skill Shadow Execution Approval Packet
type: architecture-note
status: COMPLETE TARGETED / APPROVAL REQUEST WRITTEN / NO BROWSER EXECUTION
created: 2026-05-04
updated: 2026-05-04
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Browser Skill Shadow Execution Approval Packet

This pass adds the bounded approval packet for a future guarded local Browser
Skill shadow execution proof. It is intentionally not the executor.

## Live Status

The command is available as:

```powershell
python -m runtime.cli.main siteops candidates browser-skill-shadow-execution-approval-packet <candidate_id> --source-approval-id <approval_id> --activation-approval-id <approval_id> --tenant local --workspace default --user local-user --actor local-user --target-url http://localhost:8765/shadow --shadow-mode --local-target-only
```

Default behavior is read-only and returns
`shadow_execution_approval_packet_ready_no_write` when the reviewed evidence
chain is valid.

With `--write-approval-request`, the command writes only scoped approval
metadata:

- `07_LOGS/SiteOps-Approvals/local/default/approval_siteops_shadow_exec_20260504_091240_candidate-browser-runtime-202604_browser_skill_candidate_browser_skill_shadow_execution_proof.json`
- `07_LOGS/SiteOps-Runs/local/default/siteops_shadow_exec_20260504_091240_candidate-browser-runtime-202604.json`
- `07_LOGS/SiteOps-Audits/local/default/siteops_shadow_exec_20260504_091240_candidate-browser-runtime-202604.jsonl`

The approval status is `pending`.

## Preconditions Checked

- Candidate exists and is scoped to `tenant_id=local`, `workspace_id=default`,
  and `user_id=local-user`.
- Source approval and activation approval IDs match the reviewed evidence chain.
- Browser Run evidence exists under the scoped Browser Runs lane.
- Evidence review closeout exists and remains
  `closed_untrusted_no_browser_evidence`.
- Browser Run SHA-256 is recomputed and matches the closeout reference.
- Evidence references match the expected Browser Run, Agent Activity, and
  candidate Markdown evidence paths.
- Target URL is local or explicitly allowlisted.
- `--shadow-mode` is required.
- Future execution Browser Run and Agent Activity paths are create-new targets.
- No forbidden browser/session/credential fields are present in the reviewed
  evidence.

## Explicitly Not Built

- Browser/CDP execution.
- Authenticated session handling.
- Cookie, token, localStorage, sessionStorage, or account-state reads.
- DOM mutation or form submission.
- Approval decision or approval consumption.
- Trusted Browser Skill promotion.
- Activation.
- Gate policy mutation.
- Agent Bus/provider calls.
- Hermes authority expansion.
- Canonical ChaseOS memory/state writeback.

## Next Pass

Next recommended pass:

`siteops-browser-skill-shadow-execution-approval-decision-preflight`

That pass should verify the pending ApprovalRequest, action, scope, evidence
digest, target URL policy, and future write set before any executor can consume
the approval. It should remain no-browser unless a later, separate operator
decision explicitly authorizes guarded local shadow execution proof.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
