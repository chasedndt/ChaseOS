# runtime/osril/ - Operator Surface Runtime Interaction Layer

OSRIL is the runtime-side interaction substrate that records AOR session snapshots and event streams for future operator surfaces.

## Live Substrate

- `contract.py` defines the normalized OSRIL event contract.
- `session.py` writes session snapshots and JSONL event logs under `runtime/osril/run/`.
- `inspector.py` provides read-only operator inspection helpers.
- `approvals.py` records immutable operator responses to existing `approval_required` events, writes separate immutable application markers, appends `approval_response` events to the linked OSRIL session, and records immutable AOR resume markers when an approved response is consumed by an approval-gated workflow.
- `wait_resume.py` builds a read-only approval wait/resume queue across pending approvals, recorded responses, denial state, and one-time AOR resume markers.
- `resume_ready.py` runs a bounded one-shot scan for `ready_to_resume` approvals and resumes each approved item through the same AOR `operator_approval_ref` path as a manual rerun.

## Operator CLI

```powershell
python -m runtime.cli.main osril sessions --limit 10 --json
python -m runtime.cli.main osril show SESSION_ID --json
python -m runtime.cli.main osril events --runtime hermes --limit 20 --json
python -m runtime.cli.main osril approvals --runtime openclaw --json
python -m runtime.cli.main osril wait-resume --status ready_to_resume --json
python -m runtime.cli.main osril resume-ready --dry-run --json
python -m runtime.cli.main osril respond APPROVAL_ID --decision approve --operator chase --json
```

`sessions`, `show`, `events`, `approvals`, and `wait-resume` are read-only. `wait-resume` reports `waiting_response`, `ready_to_resume`, `denied`, `resumed`, `response_unapplied`, and `not_found` states with response/resume command hints; when called with an approval id and `--timeout`, it performs only bounded polling against OSRIL state. `respond` writes one immutable response record after Gate allows the `osril.approval_response` runtime operation, writes a separate application marker, and records an `approval_response` event against the linked session. The application is OSRIL session-state only; `resume_executed` remains `false` until AOR consumes the approval through an approval-gated workflow resume. `resume-ready` is the bounded one-shot execution surface: `--dry-run` plans only, and non-dry runs require the `osril.approval_resume` Gate operation before approved-ready items are handed back to AOR.

For AOR workflows that declare `approval_rule: operator-explicit`, `chaseos run WORKFLOW_ID` now stops before handler execution, emits `approval_required`, and returns `status=waiting_approval`. After the operator records an approval response, the workflow can be resumed through the existing input channel:

```powershell
python -m runtime.cli.main osril respond APPROVAL_ID --decision approve --operator chase --json
python -m runtime.cli.main run WORKFLOW_ID --input operator_approval_ref=APPROVAL_ID --json
python -m runtime.cli.main osril resume-ready APPROVAL_ID --json
```

An approved response is consumed once by writing `runtime/osril/approvals/APPROVAL_ID.resume.json`. Denials and replay attempts halt at `approval_gate` before handler execution.

## Current Boundary

This closes the Phase 9 runtime-side OSRIL feature scope only; it does not close Phase 9 globally. The live substrate includes session/event inspection, run-level AOR event emission, immutable approval-response records, session-state application markers, bounded AOR approval-gate resume for `operator-explicit` manifests, a read-only wait/resume queue surface, and a Gate-bound one-shot `resume-ready` runner for approved items.

Phase 10+ owns the remaining cross-phase OSRIL work: a live operator shell, reconnect/history transport, companion/voice/visual surfaces, richer per-tool dispatch visibility, and any long-lived continuation UX beyond the current one-shot runner while still preserving AOR, Gate, and one-time resume-marker enforcement.

Canonical closeout: `06_AGENTS/OSRIL-Phase9-Closeout.md`.
