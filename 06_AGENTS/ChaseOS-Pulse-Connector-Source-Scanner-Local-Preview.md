# ChaseOS Pulse Connector / Source Scanner Local Preview

Status: COMPLETE TARGETED / LOCAL METADATA PREVIEW BUILT
Date: 2026-05-03
Runtime: Codex

## Purpose

This pass adds the first local-only Pulse source candidate preview. It turns
already persisted ChaseOS source artifacts into reviewable candidate metadata
without executing connectors or reading source content.

## Runtime Surface

`runtime/pulse/connector_source_scanner_local_preview.py` builds a bounded
metadata preview over:

- Pulse deck and review artifacts
- Source Intelligence Core artifacts
- governed capture/quarantine inputs
- build logs
- agent activity logs
- local acquisition artifacts

The command surface is:

```text
chaseos pulse connector-source-scanner-local-preview --limit 12 --json
```

Optional explicit write mode:

```text
chaseos pulse connector-source-scanner-local-preview --write --json
```

Write mode can only write JSON under:

```text
07_LOGS/Pulse-Decks/source-scanner-preview/
```

## What It Emits

Each preview candidate includes:

- candidate id
- source surface id
- source path
- source class
- artifact kind
- file name
- extension
- size
- modified timestamp
- recommended card classes
- authority flags proving no source content read and no live connector requirement

## Boundary

This preview does not:

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
- activate schedules
- write Agent Bus tasks
- execute approvals
- approve memory
- promote sources
- write `02_KNOWLEDGE/`
- mutate canonical ChaseOS state
- update the R&D workbook

## Product Meaning

This is the first useful local scanner preview layer for Pulse. It lets Pulse
see what already exists locally and prepare source candidates for future cards
without taking external action.

## Next Pass

`chaseos-pulse-connector-source-scanner-candidate-cards`

That pass should convert selected local preview candidates into Pulse cards or
review candidates while still avoiding autonomous promotion and live connector
execution.

## Follow-Up Completed

The candidate-card follow-up is now complete targeted as of 2026-05-03.
`chaseos pulse connector-source-scanner-candidate-cards --limit 12 --write --json`
generated user, agent, and shared-coordination Pulse decks from local metadata
only. Live connector execution, source content reads, source promotion, approval
execution, schedule activation, and canonical writeback remain blocked.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
