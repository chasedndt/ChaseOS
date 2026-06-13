---
title: SiteOps Candidate Activation Approval Decision Consumer Writer Design
type: runtime-contract
status: BUILT / NO-MUTATION WRITER DESIGN
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Activation Approval Decision Consumer Writer Design

`siteops candidates activation-approval-decision-consumer-writer-design` is the
no-mutation design packet for a future activation approval consumer writer.

It sits after:

- `activation-approval-decision-preflight`
- `activation-approval-decision-consumer-design`
- `activation-approval-decision-consumer-write-guard`

Its job is to define the future writer transaction, not to consume approvals or
activate a skill.

## Command

```powershell
python -m runtime.cli.main siteops candidates activation-approval-decision-consumer-writer-design <candidate_id> --source-approval-id <source_approval_id> --activation-approval-id <activation_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

## Design Scope

The packet declares:

- the future explicit `--consume-activation-approval` writer flag
- the future create-new-only activation consumer marker
- the future append-only audit path
- required digest and scope rechecks
- trusted-artifact provenance and inactive-state checks
- stop-before-activation behavior
- forbidden secret/session fields

## Forbidden Effects

This command does not:

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

This is BUILT / NO-MUTATION WRITER DESIGN. The actual activation consumer
writer remains NOT BUILT. The next pass should package an implementation-request
surface for the reviewed writer before any explicit write command is added.

Hermes remains bounded reviewer/shadow only. This design does not make Hermes
the SiteOps runtime owner and does not grant Hermes activation authority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
