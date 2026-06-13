# ChaseOS Pulse Studio Approval Center Local Mount

Canonical cross-feature Approval Center reference:
[[ChaseOS-Approval-Center]]. This document describes the older Pulse-specific
localhost mount; the canonical multi-source Approval Center boundary now lives
in the standalone Approval Center document.

**Status:** COMPLETE TARGETED / LOCAL READ-ONLY MOUNT VERIFIED  
**Created:** 2026-05-02  
**Runtime:** Codex  
**Phase:** ChaseOS Pulse product-grade expansion pass 3/6  

## Purpose

This pass mounts the ChaseOS Pulse approval-center readiness contract as a
localhost-only Studio app.

The mount gives the operator a local visual review surface for:

- Pulse deck lanes
- feedback candidates
- Personal Map memory candidates
- execution repair candidates
- review decisions
- Agent Bus approval requests
- final evidence gate posture
- post-completion hardening availability

It is a Studio foothold over existing Pulse backend truth. It is not an
approval executor and not a new write authority.

## Runtime Surface

Code:

```text
runtime/studio/approval_center_app.py
```

CLI:

```text
chaseos studio approval-center-app --dry-run --json
chaseos studio approval-center-app --host 127.0.0.1 --port 8773
```

Local routes:

```text
/
/health.json
/approval-center.json
/app-plan.json
```

Default URL:

```text
http://127.0.0.1:8773/
```

## Composition

The app wraps:

```text
runtime.pulse.approval_center.build_pulse_approval_center_readiness
```

The app is also registered in:

```text
runtime/studio/app_launcher.py
```

and surfaced by the desktop shell mock as a mounted read-only view in:

```text
runtime/studio/desktop_shell_app.py
```

## Authority Boundary

The app explicitly blocks:

- approval grant
- approval execution
- review-decision writes
- feedback-candidate writes
- candidate apply
- Agent Bus task writes
- runtime dispatch
- provider or connector calls
- schedule activation
- memory approval
- canonical writeback
- canonical mutation
- second datastore creation
- R&D workbook update

Display actions are previews only. Even if the final evidence gate reports a
ready command preview, this app does not run it.

## Current Live Proof

Live local smoke on 2026-05-02:

```text
http://127.0.0.1:8773/health.json -> 200
http://127.0.0.1:8773/approval-center.json -> ready_for_operator_review
```

Observed live state:

- lanes: 8
- latest decks: 3
- Agent Bus write allowed: false
- canonical writeback allowed: false
- HTML root present: true
- script tags present: false

## Not Implemented

- no full standalone Studio desktop shell
- no approval execution UI
- no candidate apply UI in this older Pulse-specific mount; the current bounded
  review/apply UI contract is [[ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI]]
- no canonical writeback UI
- no schedule activation UI
- no provider/connector invocation
- no R&D workbook mutation

## Next

The next Pulse product-grade pass should implement the bounded governed
feedback review/apply panel from [[ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI]]
as preview/readiness UI first. Any live apply affordance must remain approval
gated and must delegate to the existing non-canonical `candidate_apply.py`
backend rather than expanding this Approval Center mount into a mutation surface.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]] . [[ChaseOS-Approval-Center]]*
