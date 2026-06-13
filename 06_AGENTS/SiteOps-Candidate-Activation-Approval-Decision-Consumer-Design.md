---
title: SiteOps Candidate Activation Approval Decision Consumer Design
type: runtime-contract
status: BUILT / NO-MUTATION CONSUMER DESIGN
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Activation Approval Decision Consumer Design

`siteops candidates activation-approval-decision-consumer-design` is the
no-mutation design packet for the future activation approval consumer.

It sits after `activation-approval-decision-preflight` and before any consumer
writer or activation executor. Its job is to define the future exact-once
consumer record, audit event, stop conditions, and handoff requirements without
consuming approval or activating anything.

## Command

```powershell
python -m runtime.cli.main siteops candidates activation-approval-decision-consumer-design <candidate_id> --source-approval-id <source_approval_id> --activation-approval-id <activation_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

## What It Designs

- future exact-once activation consumer marker path
- future activation consumer record schema
- future scoped activation consumer audit event
- required preflight rerun before any write
- stop-before-activation-executor rule
- no-secret/no-session-state metadata expectations

## Forbidden Effects

The command does not:

- write the activation consumer marker
- consume the activation approval
- decide an approval request
- write trusted Browser Skill artifacts
- write SiteOps Skill Card artifacts
- activate skills
- launch or control browsers
- enqueue Agent Bus work
- call providers
- write canonical ChaseOS memory/state

## Current Status

The design packet is built and verified. The write guard, actual consumer
writer, activation executor, browser replay, Agent Bus/provider integration,
and canonical writeback remain future work.

Hermes remains bounded reviewer/shadow only. This contract does not make Hermes
the SiteOps runtime owner and does not grant Hermes activation authority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
