---
title: ChaseOS Pulse Approval Queue Studio Panel Mount
type: implementation-note
status: complete-targeted
created: 2026-05-03
updated: 2026-05-03
runtime: Codex
feature: ChaseOS Pulse
phase: Phase 10 local Studio surface
---

# ChaseOS Pulse Approval Queue Studio Panel Mount

Canonical cross-feature Approval Center reference:
[[ChaseOS-Approval-Center]]. This document describes the Pulse approval queue
Studio panel mount; the standalone Approval Center document owns cross-feature
source rules and authority vocabulary.

## Status

`runtime/studio/approval_queue_panel.py` and:

```text
chaseos studio approval-queue-panel --json
```

now expose the static Pulse Approval Queue artifact as a read-only Studio panel
contract.

`runtime/studio/desktop_shell_app.py` now mounts that contract under
`#approval-queue` and exposes:

```text
/approval-queue.json
```

This is a Studio mount over the existing static approval queue surface. It is
not an approval executor.

## What It Reads

The panel contract reads:

- `runtime/pulse/approval_queue_ui.py`
- `runtime/pulse/approval_center.py`
- `runtime/pulse/candidate_inspector.py`
- the latest static approval queue artifact under
  `07_LOGS/Pulse-Decks/approval-queue/`

## What It Adds

This pass adds:

- `studio.pulse.approval_queue.panel`
- `#approval-queue` Studio shell route
- `/approval-queue.json` desktop-shell route
- latest static approval queue artifact detection
- read-only iframe/webview mount metadata
- readiness fields for panel contract, static artifact, and desktop shell mount
- focused tests for the panel contract and desktop-shell mount

## Authority Boundary

This surface is read-only and local-only.

It does not:

- grant approvals
- execute approvals
- write review decisions
- write feedback candidates
- apply candidates
- approve memory
- write Agent Bus tasks
- dispatch runtimes
- activate schedules
- call providers or connectors
- write canonical state
- create a second datastore
- update the R&D workbook

## Product Boundary

This completes the read-only Studio mount for the Approval Queue lane. The next
Pulse product work is not another static approval queue duplicate; it should
move into either governed live Personal Map apply proof, deeper candidate
review/apply interaction, or separately approved native schedule activation
proof.

## Graph Links

[[ChaseOS-Approval-Center]] - [[ChaseOS-Pulse-Approval-Queue-UI]] - [[ChaseOS-Pulse-Completion-Tracker]] - [[ChaseOS-Studio-Architecture]] - [[Pulse-Feedback-Policy]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]] . [[ChaseOS-Approval-Center]]*
