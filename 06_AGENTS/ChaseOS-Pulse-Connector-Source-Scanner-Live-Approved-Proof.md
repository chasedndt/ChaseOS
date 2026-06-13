# ChaseOS Pulse Connector / Source Scanner Live Approved Proof

Status: COMPLETE TARGETED / APPROVAL REQUEST PROOF / LIVE EXECUTION BLOCKED
Date: 2026-05-03
Runtime: Codex

## Purpose

This pass adds the fail-closed handoff layer for a future live
connector/source-scanner proof. It proves which connector contracts could be
requested for live proof and which approval evidence is still required.

It does not execute live connectors.

## Runtime Surface

`runtime/pulse/connector_source_scanner_live_proof.py` composes the existing
connector/source-scanner readiness contract and reports live-proof targets for
external connector contracts only.

The command surface is:

```text
chaseos pulse connector-source-scanner-live-approved-proof --json
```

Optional explicit request-write mode:

```text
chaseos pulse connector-source-scanner-live-approved-proof --connector-id acquisition_rss_live --write-request --json
```

Request-write mode creates a pending operator-review artifact only under:

```text
07_LOGS/Pulse-Decks/source-scanner-live-approval-requests/
```

The request artifact is not an approval grant and not an execution record.

## Required Evidence Slots

A future live proof must provide real refs for:

- `operator_approval_ref`
- `permission_envelope_ref`
- `connector_scope_ref`
- `source_class_scope_ref`
- `denylist_ack_ref`
- `output_write_scope_ref`

Placeholder refs are not sufficient for live connector execution.

## Current Repo Result

Live smoke reported:

- `status=blocked_missing_operator_permission_envelope`
- `target_count=7`
- `external_connector_count=7`
- `live_enabled_connector_count=0`
- `approval_granted=false`
- `approval_execution_allowed=false`
- `provider_or_connector_call_allowed=false`
- `source_promotion_allowed=false`
- `canonical_writeback_allowed=false`

An explicit request-write smoke wrote:

```text
07_LOGS/Pulse-Decks/source-scanner-live-approval-requests/2026-05-03-live-proof-request-acquisition_rss_live.json
```

That artifact is pending-review evidence only.

## Boundary

This pass does not:

- read source content
- call providers
- call connectors
- fetch RSS feeds
- scrape web pages
- read email
- read Google Docs or Drive
- read browser history
- inspect cookies
- read credentials or secrets
- grant approvals
- execute approvals
- activate schedules
- write Agent Bus tasks
- approve memory
- promote sources
- write `02_KNOWLEDGE/`
- mutate canonical ChaseOS state
- update the R&D workbook during runtime execution

## Product Meaning

Pulse now has a concrete, test-backed live connector proof gate. The system can
surface a reviewable request for a narrow connector, but the actual live source
scanner remains blocked until an operator-approved permission envelope and
scope evidence exist.

## Next Pass

Choose one:

- approve a narrow live connector proof for one connector and source scope
- defer live connectors and continue the remaining Pulse product-grade lanes

No unrestricted browsing or autonomous source promotion should be added.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
