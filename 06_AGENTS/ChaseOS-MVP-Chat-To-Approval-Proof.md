---
title: ChaseOS MVP Chat-To-Approval Proof
type: mvp-proof
status: COMPLETE / ONE CHAT REQUEST WROTE PENDING APPROVAL / EXECUTION BLOCKED
created: 2026-05-13
updated: 2026-05-13
runtime: Codex
session_descriptor: chat-to-approval-artifact-proof
---

# ChaseOS MVP Chat-To-Approval Proof

## Bottom Line

The MVP Chat-to-Approval requirement is now proven for one supported Chat proposal lane.

One bounded Chat request produced one pending Studio approval artifact:

- Approval id: `5849a53f-10e0-46af-a89a-7de06150f7f8`
- Approval artifact: `runtime/studio/approvals/5849a53f-10e0-46af-a89a-7de06150f7f8.json`
- Handoff audit: `runtime/studio/approvals/chat-handoffs/a3821be0353e03e9166c42a057cc0f83db9b03e6c13f2378f6fb070dbbe4d1a9.json`
- Action digest: `a3821be0353e03e9166c42a057cc0f83db9b03e6c13f2378f6fb070dbbe4d1a9`
- Source digest: `67eb534861895d16b25e4f30ecedcdb44b362b98b37eab4db7ceb309e832979a`
- Status: `pending`

The target proposal file was not written. Approval execution, provider calls, runtime dispatch, browser control, Agent Bus task write, Gate/Git/workflow/host mutation, and canonical writeback all remained blocked.

## Proof Request

```text
MVP Chat-to-Approval proof: draft a proposal for a small operator workflow status note. Queue it for approval only; do not write the target file.
```

Intent: `project-create`

The first attempted `runtime-task` version was correctly blocked because that intent is not supported by the generic Chat approval queue handoff contract. The successful proof used a supported queueable proposal intent.

## Commands

Preview:

```powershell
python -m chaseos studio phase11-chat-approval-queue-write-execution-proof --message "MVP Chat-to-Approval proof: draft a proposal for a small operator workflow status note. Queue it for approval only; do not write the target file." --intent project-create --operator-id codex-mvp-chat-proof --json
```

Write:

```powershell
python -m chaseos studio phase11-chat-approval-queue-write-execution-proof --message "MVP Chat-to-Approval proof: draft a proposal for a small operator workflow status note. Queue it for approval only; do not write the target file." --intent project-create --operator-id codex-mvp-chat-proof --expected-action-digest a3821be0353e03e9166c42a057cc0f83db9b03e6c13f2378f6fb070dbbe4d1a9 --write-approval --json
```

Duplicate replay:

```powershell
python -m chaseos studio phase11-chat-approval-queue-write-execution-proof --message "MVP Chat-to-Approval proof: draft a proposal for a small operator workflow status note. Queue it for approval only; do not write the target file." --intent project-create --operator-id codex-mvp-chat-proof --expected-action-digest a3821be0353e03e9166c42a057cc0f83db9b03e6c13f2378f6fb070dbbe4d1a9 --write-approval --json
```

## Verification

| Check | Result |
|---|---|
| Preview ready | `queue_write_preview_ready=true` |
| Digest matched on write | `expected_digest_matched=true` |
| Approval artifact created | `approval_request_created=true` |
| Approval id | `5849a53f-10e0-46af-a89a-7de06150f7f8` |
| Approval state | `pending` |
| Handoff audit written | `audit_record_written=true` |
| Duplicate replay | `duplicate_active_request_present=true`; existing approval returned |
| Approval Center visibility | latest Studio Service item shows approval `5849a53f-10e0-46af-a89a-7de06150f7f8` |
| Target file write | `false`; target path does not exist |
| Conversation log write | `false` |
| Provider call | `false` |
| Runtime dispatch | `false` |
| Agent Bus task write | `false` |
| Canonical mutation | `false` |

## Target Preview

The future target remains only a proposal preview:

`01_PROJECTS/_chat_proposals/mvp-chat-to-approval-proof-draft-a-proposal-for-a-small-operator-workflow-status-8a9571a16d09.md`

`Test-Path` returned `False`, confirming the target was not written by the queue write.

## MVP Meaning

This closes the explicit Chat-to-Approval outcome for a supported proposal lane:

`one Chat request -> one digest-bound pending approval artifact -> visible in Studio Approval Center -> no execution`

The next useful loop is not another approval preview. It is either:

1. consume an approved Chat-created artifact exactly once, or
2. continue using the already-proven runtime-dispatch approval-to-Agent-Bus path while the operator resolves provider credentials and VentureOps real-client inputs.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
