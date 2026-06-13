---
title: SiteOps Candidate Activation Approval Decision Consumer Writer Implementation Approval
type: runtime-contract
status: BUILT / NO-MUTATION IMPLEMENTATION APPROVAL
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Activation Approval Decision Consumer Writer Implementation Approval

`siteops candidates activation-approval-decision-consumer-writer-implementation-approval`
is the no-mutation approve/reject packet for a future activation approval
consumer writer implementation.

It sits after
`activation-approval-decision-consumer-writer-implementation-request` and before
any implementation that can support `--consume-activation-approval`.

## Command

```powershell
python -m runtime.cli.main siteops candidates activation-approval-decision-consumer-writer-implementation-approval <candidate_id> --source-approval-id <source_approval_id> --activation-approval-id <activation_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --decision approve --json
```

`--decision` accepts only:

- `approve`
- `reject`

## Reserved Future Flag

The future writer flag remains:

```text
--consume-activation-approval
```

This approval command rejects that flag. The flag remains reserved for a later
writer implementation pass.

## Approval Packet Contents

The packet includes:

- operator decision intent
- candidate and proposed skill identifiers
- source approval and activation approval ids
- implementation request id
- future command name
- future explicit write flag
- future marker/audit write set
- rollback contract
- approval checks
- no-write and no-activation boundary flags

## Forbidden Effects

This command does not:

- write an implementation-approval artifact
- support `--consume-activation-approval`
- implement the activation consumer writer
- consume activation approvals
- write activation consumer markers
- append activation consumer audit events
- decide approvals durably
- write trusted Browser Skill artifacts
- write SiteOps Skill Card artifacts
- mutate Gate policy
- activate skills
- launch or control browsers
- enqueue Agent Bus work
- call providers
- write canonical ChaseOS memory/state

## Current Status

This is BUILT / NO-MUTATION IMPLEMENTATION APPROVAL. The actual activation
consumer writer, approval consumption, activation executor, browser replay,
Agent Bus/provider integration, and canonical writeback remain future work.

Hermes remains bounded reviewer/shadow only. This approval packet does not make
Hermes the SiteOps runtime owner and does not grant Hermes activation authority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
