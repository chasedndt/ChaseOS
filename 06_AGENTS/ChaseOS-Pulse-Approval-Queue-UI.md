---
title: ChaseOS Pulse Approval Queue UI
type: implementation-note
status: complete-targeted
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
feature: ChaseOS Pulse
phase: Phase 10 local visual surface
---

# ChaseOS Pulse Approval Queue UI

Canonical cross-feature Approval Center reference:
[[ChaseOS-Approval-Center]]. This document describes a Pulse static approval
queue UI artifact; cross-feature approval-source rules and lifecycle vocabulary
belong to the standalone Approval Center document.

## Status

`runtime/pulse/approval_queue_ui.py` and:

```text
chaseos pulse approval-queue-ui --json
chaseos pulse approval-queue-ui --write --json
```

provide the first local-only static Pulse Approval Queue UI artifact.

This is not an approval executor. It is a static visual surface over the
existing Pulse approval-center readiness contract and candidate inspector
snapshot.

## What It Reads

The UI composes:

- `runtime/pulse/approval_center.py`
- `runtime/pulse/candidate_inspector.py`
- local Pulse deck inventory
- feedback candidate lanes
- Personal Map candidate lanes
- execution repair candidate lanes
- review-decision logs
- Agent Bus approval-request evidence
- final evidence gate status

## What It Renders

The static artifact shows:

- approval-center status
- lane counts
- action preview counts
- candidate queue rows
- approval request counts
- missing approval-key counts
- display-only action previews
- blocked authority

The artifact path is:

```text
07_LOGS/Pulse-Decks/approval-queue/YYYY-MM-DD-approval-queue.html
```

Artifacts are written only when `--write` is passed.

## Authority Boundary

This surface is read-only and local-only.

It does not:

- grant approvals
- execute approvals
- write review decisions
- write feedback candidates
- apply candidates
- write Agent Bus tasks
- dispatch runtimes
- activate schedules
- call providers or connectors
- approve memory
- write canonical state
- create a second datastore
- update the R&D workbook

## Product Boundary

This pass completes a first static approval queue UI foothold for Pulse. It
does not implement a full interactive approval workflow, approval execution,
candidate apply, schedule activation, or canonical writeback.

## Graph Links

[[ChaseOS-Approval-Center]] - [[ChaseOS-Pulse-Approval-Center-Readiness]] - [[ChaseOS-Pulse-Studio-Approval-Center-Local-Mount]] - [[ChaseOS-Pulse-Completion-Tracker]] - [[Pulse-Feedback-Policy]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]] . [[ChaseOS-Approval-Center]]*
