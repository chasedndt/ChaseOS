---
title: SiteOps Gate Policy Live Application Runbook
type: template
status: TEMPLATE
created: 2026-05-03
updated: 2026-05-03
---

# SiteOps Gate Policy Live Application Runbook

Use this template for the future live application pass that applies the reviewed
Gate policy patch for SiteOps trusted inactive artifact writing.

Do not record secrets, cookies, tokens, credentials, browser profile data, or
personal account state in this runbook.

## Run Metadata

- Date:
- Runtime:
- Operator:
- Session descriptor:
- Candidate ID:
- Tenant:
- Workspace:
- User:
- Actor:
- Replacement approval ID:
- Gate approval ID:

## Scope Confirmation

| Boundary | Confirmed |
| --- | --- |
| Apply Gate policy only | |
| Do not consume approvals | |
| Do not write trusted artifacts | |
| Do not activate skills | |
| Do not launch browser/CDP | |
| Do not enqueue Agent Bus work | |
| Do not call providers | |
| Do not write canonical memory/state | |

## Before State

| File | Pre-apply digest | Operation/category posture |
| --- | --- | --- |
| `runtime/chaseos_gate.py` | | |
| `runtime/policy/gateway_allowlists.json` | | |

Readiness command:

```powershell

```

Expected readiness status:

```text
gate_policy_live_application_ready_no_write
```

Observed readiness status:

```text

```

Future apply command preview copied from readiness:

```powershell

```

## Apply Step

Command executed:

```powershell

```

Expected status:

```text
gate_policy_patch_writer_implementation_applied
```

Observed status:

```text

```

Writer artifact directory:

```text

```

Backup files:

```text

```

Rollback audit:

```text

```

## After State

| File | Post-apply digest | Verification result |
| --- | --- | --- |
| `runtime/chaseos_gate.py` | | |
| `runtime/policy/gateway_allowlists.json` | | |

Required verification commands:

```powershell
python -m py_compile runtime/chaseos_gate.py
python -m json.tool runtime/policy/gateway_allowlists.json
```

Verification output summary:

```text

```

## Exact Patch Confirmation

| Check | Result |
| --- | --- |
| Operation present exactly once | |
| No unrelated Gate operation changed | |
| `browser_skills_inactive_review` category exact | |
| `siteops_skill_cards_inactive_review` category exact | |
| No unrelated gateway category changed | |
| Backup artifacts exist | |
| Rollback audit exists | |
| No secret/session-state material in artifacts | |

## Post-Apply Smokes

Re-run live readiness:

```powershell

```

Observed status:

```text

```

Run trusted executor no-write posture smoke:

```powershell
python -m runtime.cli.main siteops candidates apply-trusted-candidate-artifacts <candidate_id> --replacement-approval-id <replacement_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

Observed status:

```text

```

## Rollback Evidence

Complete only if rollback was required.

- Rollback required:
- Reason:
- Operator confirmation:
- Backup file used for `runtime/chaseos_gate.py`:
- Backup file used for `runtime/policy/gateway_allowlists.json`:
- Post-rollback Gate digest:
- Post-rollback gateway digest:
- Post-rollback `py_compile` result:
- Post-rollback `json.tool` result:
- Post-rollback readiness result:

## Final Status

- Final status:
- What changed:
- What did not change:
- Remaining unverified:
- Next recommended pass:

## Required Links

- Build log:
- Documentation-history note:
- Daily note:
- Agent Activity log:
- SiteOps tracker:
