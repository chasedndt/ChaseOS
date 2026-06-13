---
title: SiteOps Candidate Activation Approval Decision Consumer Writer Implementation Request
type: runtime-contract
status: BUILT / NO-MUTATION IMPLEMENTATION REQUEST
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Activation Approval Decision Consumer Writer Implementation Request

`siteops candidates activation-approval-decision-consumer-writer-implementation-request`
is the no-mutation review packet for a future activation approval consumer
writer implementation.

It sits after `activation-approval-decision-consumer-writer-design` and before
any implementation approval or explicit writer. Its job is to package the
reviewed writer-design evidence into an operator-readable request without
writing the request artifact, consuming an approval, writing the marker, or
activating a skill.

## Command

```powershell
python -m runtime.cli.main siteops candidates activation-approval-decision-consumer-writer-implementation-request <candidate_id> --source-approval-id <source_approval_id> --activation-approval-id <activation_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

## Reserved Future Flag

The future writer flag remains:

```text
--consume-activation-approval
```

This command rejects that flag. The flag cannot be accepted until a separate
operator-reviewed implementation and approval pass exists.

## Request Packet Contents

The packet includes:

- request id and request type
- tenant/workspace/user scope
- candidate and proposed skill identifiers
- source approval and activation approval ids
- writer design status and write-guard status
- future explicit write flag
- future marker/audit write set
- rollback contract
- record schema
- future writer sequence
- no-write and no-activation boundary flags

## Forbidden Effects

This command does not:

- write an implementation-request artifact
- support `--consume-activation-approval`
- consume activation approvals
- write activation consumer markers
- append activation consumer audit events
- decide approvals
- write trusted Browser Skill artifacts
- write SiteOps Skill Card artifacts
- mutate Gate policy
- activate skills
- launch or control browsers
- enqueue Agent Bus work
- call providers
- write canonical ChaseOS memory/state

## Current Status

This is BUILT / NO-MUTATION IMPLEMENTATION REQUEST. The implementation
approval, actual activation consumer writer, approval consumption, activation
executor, browser replay, Agent Bus/provider integration, and canonical
writeback remain future work.

Hermes remains bounded reviewer/shadow only. This request does not make Hermes
the SiteOps runtime owner and does not grant Hermes activation authority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
