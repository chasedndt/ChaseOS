# ChaseOS Pulse Approval Center Readiness

Canonical cross-feature Approval Center reference:
[[ChaseOS-Approval-Center]]. This document describes the Pulse readiness source
that feeds the broader Approval Center; it is not the whole Approval Center.

**Status:** PARTIAL / VERIFIED TARGETED  
**Created:** 2026-05-02  
**Runtime:** Codex  
**Phase:** ChaseOS Pulse product-grade expansion pass 2/6  

## Purpose

The Pulse approval center readiness surface is a local, read-only aggregation
packet for the future ChaseOS Studio approval center.

It answers:

- which Pulse deck artifacts exist
- which feedback, Personal Map, and execution repair candidates are pending
- which review decisions have been recorded
- which Agent Bus approval requests exist
- whether a selected request is blocked or ready for operator review
- whether the final evidence gate is blocked or ready
- whether the post-completion hardening surface is available

This is not the visual approval center UI and not an approval executor.

## Runtime Surface

Code:

```text
runtime/pulse/approval_center.py
```

CLI:

```text
chaseos pulse approval-center-readiness --json
chaseos pulse approval-center-readiness --request-id REQUEST_ID --evidence-id EVIDENCE_ID --json
```

The command composes existing Pulse surfaces:

- `candidate_inspector.py`
- `feedback_review_queue.py`
- `bus_enqueue_approval_request.py`
- `approval_readiness_summary.py`
- `final_evidence_gate.py`
- `multi_audience_decks.py`

The post-completion hardening lane is represented by a non-writing availability
signal. The full hardening report remains a separate command:

```text
chaseos pulse post-completion-hardening --json
```

This avoids materializing runtime scaffolding when approval-center readiness is
run against sparse test vaults.

## Lanes

The readiness packet always exposes these lanes:

- `pulse_decks`
- `feedback_candidates`
- `memory_candidates`
- `execution_repair_candidates`
- `review_decisions`
- `agent_bus_approval_requests`
- `final_evidence_gate`
- `post_completion_hardening`

Each lane reports item, pending, ready, blocked, status, and source reference
signals. These are review signals only.

## Boundary

The approval center readiness surface explicitly blocks:

- status artifact writes
- review decision writes
- feedback candidate writes
- candidate apply
- approval grant
- approval execution
- Agent Bus task writes
- runtime dispatch
- provider or connector calls
- schedule activation
- memory approval
- canonical writeback
- canonical mutation
- second datastore creation
- R&D workbook updates

Action previews are display-only. Even when the final evidence gate is ready,
the surface can only show a supervised command preview. It cannot run the
command.

## Current Status

This pass gives Pulse a machine-readable approval-center readiness packet for
the future Studio approval queue. It does not build the visual UI and does not
advance any approval state.

## Verification

Targeted tests:

```text
python -m pytest runtime/pulse/test_approval_center.py runtime/tests/test_cli_command_contract.py -q
```

Live read-only smoke:

```text
python -m chaseos pulse approval-center-readiness --json
```

## Next

The next product-grade Pulse pass should build the actual local Studio approval
center mount over this contract, still without adding approval execution or
canonical writeback authority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]] . [[ChaseOS-Approval-Center]]*
