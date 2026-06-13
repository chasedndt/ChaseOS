---
title: SiteOps Candidate Activation Approval Decision Consumer Write Guard
type: runtime-contract
status: BUILT / NO-MUTATION WRITE-GUARD CONTRACT
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
phase: Phase 9 runtime/operator infrastructure
---

# SiteOps Candidate Activation Approval Decision Consumer Write Guard

`siteops candidates activation-approval-decision-consumer-write-guard` is the
no-mutation write-guard contract for the future activation approval consumer.

It sits after `activation-approval-decision-consumer-design` and before any
consumer writer or activation executor. Its job is to declare the explicit
future write flag, create-new-only marker policy, audit roots, artifact
provenance requirements, and stop-before-activation rule without consuming the
activation approval or writing the marker.

## Command

```powershell
python -m runtime.cli.main siteops candidates activation-approval-decision-consumer-write-guard <candidate_id> --source-approval-id <source_approval_id> --activation-approval-id <activation_approval_id> --tenant <tenant_id> --workspace <workspace_id> --user <user_id> --actor <user_id> --json
```

## Guarded Future Flag

The future writer flag is:

```text
--consume-activation-approval
```

The flag is intentionally rejected by this command. A future writer must be a
separate operator-reviewed pass before any approval consumption, marker write,
or audit write is permitted.

## What It Requires

- approved activation approval decision preflight
- digest match between current preview and stored approval request metadata
- exact tenant/workspace/user scope match
- create-new-only activation consumer marker
- absent marker before any future write
- trusted Browser Skill and SiteOps Skill Card provenance check
- inactive-artifact posture before activation consumption
- prewrite and postwrite audit evidence
- rollback evidence for partial write failure
- no secrets, cookies, tokens, credentials, or browser session state
- stop before the activation executor

## Forbidden Effects

The command does not:

- write the activation consumer marker
- append activation consumer audit events
- consume the activation approval
- decide an approval request
- write trusted Browser Skill artifacts
- write SiteOps Skill Card artifacts
- mutate Gate policy
- activate skills
- launch or control browsers
- enqueue Agent Bus work
- call providers
- write canonical ChaseOS memory/state

## Current Status

The write-guard contract is built and verified. The activation consumer writer,
actual approval-consumption marker, audit writer, activation executor, browser
replay, Agent Bus/provider integration, and canonical writeback remain future
work.

Hermes remains bounded reviewer/shadow only. This contract does not make Hermes
the SiteOps runtime owner and does not grant Hermes activation authority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
