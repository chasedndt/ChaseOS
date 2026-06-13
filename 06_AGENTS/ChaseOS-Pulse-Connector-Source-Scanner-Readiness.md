# ChaseOS Pulse Connector / Source Scanner Readiness

Status: PARTIAL / CONTRACT READY / LIVE EXECUTION BLOCKED
Date: 2026-05-03
Runtime: Codex

## Purpose

This pass defines the governed connector/source-scanner lane for ChaseOS Pulse.
Pulse can use local source intelligence and connector-derived signals, but it
must not become an unrestricted browser, API, or history scanner.

## Runtime Surface

`runtime/pulse/connector_source_scanner_readiness.py` exposes a read-only
readiness contract over:

- local Pulse deck artifacts
- Source Intelligence Core folders
- governed capture/quarantine folders
- build logs
- agent activity logs
- acquisition/normalization runtime code
- Phase 8 capture connectors
- Phase 9 acquisition adapters

The command surface is:

```text
chaseos pulse connector-source-scanner-readiness --json
```

## Governance Boundary

This readiness contract does not:

- call providers
- call connectors
- fetch RSS feeds
- scrape web pages
- read email
- read Google Docs or Drive
- read browser history
- inspect cookies
- read credentials or secrets
- activate schedules
- write Agent Bus tasks
- execute approvals
- approve memory
- promote sources
- write `02_KNOWLEDGE/`
- mutate canonical ChaseOS state

## Source Policy

Allowed by this contract:

- local source packages and Source Intelligence Core outputs
- explicitly captured local files
- operator-supplied browser/HTML files
- build logs and agent activity logs
- connector outputs only after a future explicit connector execution pass

Denied by default:

- hidden browser history ingestion
- cookies
- credential stores
- password managers
- private email without connector approval
- private calendar without connector approval
- unbounded filesystem scanning

## Next Pass

`chaseos-pulse-connector-source-scanner-local-preview` was completed as the
next targeted pass. It added:

- `runtime/pulse/connector_source_scanner_local_preview.py`
- `chaseos pulse connector-source-scanner-local-preview --json`
- optional write mode under `07_LOGS/Pulse-Decks/source-scanner-preview/`
- metadata-only local source candidates

The candidate-card pass is also complete targeted. It added:

- `runtime/pulse/connector_source_scanner_candidate_cards.py`
- `chaseos pulse connector-source-scanner-candidate-cards --json`
- user, agent, and shared-coordination cards from metadata-only candidates
- optional deck writes under `07_LOGS/Pulse-Decks/`

The live-approved proof pass is now complete targeted as a fail-closed request
layer. It added:

- `runtime/pulse/connector_source_scanner_live_proof.py`
- `chaseos pulse connector-source-scanner-live-approved-proof --json`
- optional pending approval request writes under
  `07_LOGS/Pulse-Decks/source-scanner-live-approval-requests/`

Actual live connector execution remains separate, explicitly approved, and
blocked by default.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
