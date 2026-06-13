# ChaseOS Pulse Connector / Source Scanner Candidate Cards

Status: COMPLETE TARGETED / LOCAL METADATA CARDS BUILT
Date: 2026-05-03
Runtime: Codex

## Purpose

This pass converts local source scanner preview candidates into governed Pulse
cards. It uses metadata from already persisted ChaseOS artifacts only.

It does not read source file content and does not execute live connector,
provider, browser, schedule, approval, memory, promotion, or canonical
writeback actions.

## Runtime Surface

`runtime/pulse/connector_source_scanner_candidate_cards.py` builds
multi-audience Pulse decks from
`runtime/pulse/connector_source_scanner_local_preview.py`.

The command surface is:

```text
chaseos pulse connector-source-scanner-candidate-cards --limit 12 --json
```

Optional explicit write mode:

```text
chaseos pulse connector-source-scanner-candidate-cards --limit 12 --write --json
```

Write mode creates normal Pulse deck artifacts only under:

```text
07_LOGS/Pulse-Decks/users/
07_LOGS/Pulse-Decks/agents/
07_LOGS/Pulse-Decks/shared/
```

## Output Artifacts

The 2026-05-03 write smoke produced:

- `07_LOGS/Pulse-Decks/users/2026-05-03-source-scanner-user-cards.md`
- `07_LOGS/Pulse-Decks/users/2026-05-03-source-scanner-user-cards.json`
- `07_LOGS/Pulse-Decks/agents/2026-05-03-source-scanner-agent-cards.md`
- `07_LOGS/Pulse-Decks/agents/2026-05-03-source-scanner-agent-cards.json`
- `07_LOGS/Pulse-Decks/shared/2026-05-03-source-scanner-shared-cards.md`
- `07_LOGS/Pulse-Decks/shared/2026-05-03-source-scanner-shared-cards.json`

## Audience Mapping

Candidate cards are generated for the appropriate Pulse audience:

- user cards for Source Intelligence, acquisition, capture, and build-log candidates
- agent cards for agent-activity candidates
- shared-coordination cards for Pulse deck/review-artifact candidates

Each card includes evidence metadata, source links, related nodes, thumbnail
metadata, recommended actions, confidence, promotion status, writeback status,
and canonical writeback disabled.

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
- activate schedules
- write Agent Bus tasks
- execute approvals
- approve memory
- promote sources
- write `02_KNOWLEDGE/`
- mutate canonical ChaseOS state
- update the R&D workbook during runtime execution

## Verification

Focused tests verify dry-run metadata-only behavior, schema completeness,
bounded deck writes, and current repo no-live-authority posture.

Live smoke with `--limit 12 --json` reported:

- `status=ready`
- `preview_candidate_count=12`
- `card_count=12`
- `deck_count=3`
- `source_content_read=false`
- `provider_or_connector_call_allowed=false`
- `unrestricted_web_scan_allowed=false`
- `source_promotion_allowed=false`
- `canonical_writeback_allowed=false`

## Product Meaning

Pulse can now turn local source scanner preview metadata into actual user,
agent, and shared-coordination cards without crossing the governed connector
boundary. The next step is not unrestricted scanning; it is explicit
operator-approved live connector proof or a separate review/apply lane.

## Follow-On Pass

`chaseos-pulse-connector-source-scanner-live-approved-proof`

That pass is now complete targeted as a fail-closed proof/request layer. It
adds `runtime/pulse/connector_source_scanner_live_proof.py` and
`chaseos pulse connector-source-scanner-live-approved-proof`, reports seven
external connector proof targets in the current repo, and can write a pending
operator-review request artifact. It still does not grant approval, execute
connectors, read source content, promote sources, or write canonical truth.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
