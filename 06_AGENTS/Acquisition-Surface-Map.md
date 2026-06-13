---
title: Acquisition Surface Map
type: architecture
status: canonical - Phase 9 acquisition classification; local/import metadata/setup enrichment repo-observed
version: 1.5
created: 2026-04-23
updated: 2026-04-28
phase: Phase 9 - Acquisition + Normalization
knowledge_class: canonical-state
---

# Acquisition Surface Map
## ChaseOS - Source Surfaces And Acquisition Methods

> This document classifies the source surfaces and methods that may feed the Acquisition + Normalization Layer. It is a map, not an implementation grant. A surface listed here is not live unless its status says live, and no runtime receives ambient access from this map.

---

## Status Vocabulary

| Status | Meaning |
|---|---|
| already exists | Repo has a working surface or method that can be reused now |
| partially exists | Repo has a related implementation, but not full acquisition/normalization coverage |
| should be added | Belongs to this feature family and should be implemented in a future pass |
| defer | Architecturally valid, but not first-wave or currently too broad |
| exclude for now | Too risky, too undefined, or not aligned with current authority model |

---

## A. Local / Vault / Repo Surfaces

| Surface | Classification | Viable methods | Notes |
|---|---|---|---|
| vault notes | already exists | direct file read, SIC workspace read, AOR required reads | Must be explicitly declared for runtime workflows |
| project OS files | already exists | direct file read, AOR required reads | Canonical state; read allowed by scoped workflows, writes separate |
| build logs | already exists | direct file read, log index read | Layer E execution history |
| archive notes | already exists | direct file read, archive index read | Durable history, useful for repo-truth restatement |
| operator briefs | already exists | direct file read, AOR output read | Daily/close context source |
| SBP runs | partially exists | direct file read, SBP run output read | `07_LOGS/SBP-Runs/` is the intended output home; created on first run if absent |
| agent activity logs | already exists | direct file read, audit record read | Primary execution evidence until `runtime/audit/` exists |
| decision ledgers | already exists | direct file read, index read | High-value rationale source |
| runtime memory artifacts | defer | memory replay, runtime-native read | Layer C/D structures are not yet formalized |
| source packages | already exists | SIC source package read | SIC owns source package schema; acquisition should not duplicate it |
| workspace outputs | already exists | SIC workspace output read | Workspace-local, not canonical unless promoted |
| quarantined inputs | already exists | capture sidecar read, direct file read, user-confirmed import | Tier 4 until triage/promotion |
| watched folders | already exists | watch-folder intake, CLI-triggered capture | Phase 8 watch folders are poll-only, not daemon |
| downloaded files | should be added | user-confirmed import, watch-folder intake | Downloads should not be ambient-scanned |
| screenshots | partially exists | browser screenshot, operator screenshot read | Existing operator screenshots live under logs; OCR is future fallback |
| PDFs | partially exists | user-confirmed import, future extraction/OCR | PDF handling exists as source type concept, but robust extraction is not first-wave |
| markdown docs | already exists | direct file read, capture file, SIC ingest after promotion | Core local surface |
| code files | already exists | direct file read, developer-mode declared reads | Code may feed developer workflows, not general acquisition by default |
| local config files | partially exists | direct file read with manifest scope | Sensitive configs require credential-boundary review |
| local browser exports/captures | already exists | saved-HTML browser connector, browser operator extraction | Existing saved HTML connector and live browser operator support this |

---

## B. User-Intent / Objective Surfaces

| Surface | Classification | Viable methods | Notes |
|---|---|---|---|
| user prompts | partially exists | task-local acquisition bundle, session log/handoff capture | Current chat prompts are not systematically normalized |
| cron objectives | partially exists | schedule intent read | `runtime/schedules/` exists; native cron does not |
| automation/task prompts | partially exists | workflow manifest read, automation prompt import | Must be separated from source evidence |
| operator requests | partially exists | AOR inputs, CLI inputs, Discord envelope when valid | Request text is an objective, not evidence |
| recurring objectives | partially exists | schedule intent read, Now.md read | Needs normalization into objective records |
| active focus / daily goals | already exists | Now.md read, operator_today read | Canonical daily focus source |
| approval requests | partially exists | Discord approval envelope, future OSRIL approval event | Approval request text is governance data |
| handoff packets | partially exists | handoff doc read, archive/build log read | Needs structured replay contract before automation |
| runbooks / playbooks | already exists | direct file read | Useful as instructions only when canonical and declared |

---

## C. Runtime / Harness Surfaces

| Surface | Classification | Viable methods | Notes |
|---|---|---|---|
| OpenClaw run history | partially exists | AOR audit read, OpenClaw activity logs, schedule bridge read | OpenClaw remains executor, not truth owner |
| Hermes run history | partially exists | AOR audit read, Hermes draft/log read | Hermes is bounded Discord lane; no broad acquisition authority |
| runtime-specific brains / memory | defer | runtime-native read, memory replay | Must wait for runtime memory store and export discipline |
| prior conversations / summaries / handoff packets | partially exists | archive read, handoff replay, build log read | No ambient conversation mining |
| runtime error logs | partially exists | direct log read, audit read | Useful for repair memory later |
| runtime audit records | already exists | Agent-Activity JSON/MD read | `runtime/audit/` remains future |
| workflow execution traces | partially exists | AOR/FSOS audit read, browser replay | FSOS browser has replay/audit surfaces |
| control-plane messages | partially exists | Discord envelope/channel logs when captured | Discord is transport, not authority |
| runtime-generated drafts / proposals | already exists | draft/output directory read | Proposal-only surfaces remain non-canonical |

---

## D. Connector / Digest / Research Surfaces

| Surface | Classification | Viable methods | Notes |
|---|---|---|---|
| Grok digests | already exists | Grok connector capture, manual drop-in, staged import | Recognized source class: `grok_digest`; Tier 3 research output, briefing-only |
| Perplexity outputs/tasks | already exists | Perplexity connector capture, manual import, staged import | Recognized source class: `perplexity_digest`; citations captured when API returns them |
| RSS captures | already exists | RSS connector capture | Public feed items, Tier 4 until triage |
| external API responses | partially exists | API connector, future API poll | Perplexity/Grok exist; generic API polling future |
| saved research exports | already exists | CLI capture, watched folder, user-confirmed import | Recognized source class: `research_export`; covers NotebookLM-style synthesis, trading tool exports, and manually saved research bundles |
| browser clip captures | already exists | saved HTML connector, browser operator extraction | Browser content remains data |
| manual drop-ins from external tools | already exists | CLI capture, file drop, watched folder, `chaseos acquisition preview-research` | Must preserve origin and method; StrikeZone drop folders live under `runtime/acquisition/manual/strikezone/` and may be typed as `perplexity_digest`, `youtube_summary`, `research_export`, or `grok_digest` when declared |
| connector-produced packets | already exists | ContentPacket and sidecar read | Phase 8 packet remains intake contract |

---

## E. Browser / Computer-Control Surfaces

| Surface | Classification | Viable methods | Notes |
|---|---|---|---|
| visited pages | should be added | browser operator extraction, declared URL list | No ambient history scraping |
| declared URLs | already exists | `browser_research`, browser operator, saved HTML connector | Best first browser acquisition source |
| user-defined monitoring sites | should be added | schedule-triggered browser acquisition, API poll where available | Monitoring needs cadence, rate, and ToS review |
| dashboards | should be added | browser operator read-only extraction, screenshot fallback | Authenticated dashboards require approval/credential boundary |
| watchlists | should be added | browser operator, API poll, local file import | For trading, prefer API/export over scraping when possible |
| article pages | already exists | browser operator extraction, saved HTML connector, RSS | Good first-wave browser source |
| social posts / feeds | defer | browser operator read-only capture, API where allowed | High injection/ToS/volatility risk |
| TradingView ideas | should be added | browser operator extraction, user-confirmed import | Good StrikeZone pilot source, but scope URLs explicitly |
| chart pages | should be added | screenshot plus metadata; OCR/vision only if necessary | Screenshots are evidence, not trade authority |
| market news sites | should be added | RSS/API first, browser extraction second | Respect source freshness and attribution |
| YouTube channel/video pages | partially exists | transcript/summary import, browser metadata capture later | Recognized local/import source class: `youtube_summary`; full video understanding and browser metadata capture deferred |
| comments / post bodies / metadata | defer | explicit URL capture only | High noise and injection risk |
| browser-extracted screenshots / HTML / markdown | partially exists | browser operator screenshot/extract, capture pipeline | Tier A DOM live; OCR/vision deferred |
| tab state / browsing session context where allowed | defer | browser session state read | Do not read personal browser sessions; isolated context only |

---

## F. Future Personal / Productivity Surfaces

| Surface | Classification | Viable methods | Notes |
|---|---|---|---|
| email | should be added later | connector read, MCP-mediated read, approval-gated acquisition | Read-only by default; sensitive surface |
| calendar | should be added later | connector read, MCP-mediated read | Good daily ops input once scoped |
| task managers | should be added later | connector read/API poll | Needs identity and dedup rules |
| chat platforms | should be added later | connector/gateway envelope read | Chat inputs are Tier 4 unless validated |
| cloud docs | defer | connector/API read, user-confirmed import | Needs provider-specific permission model |
| local folders outside the vault | defer | watch-folder or explicit path import | No ambient outside-vault roaming |
| clipboard | should be added | user-confirmed import, capture clipboard | Must avoid accidental credential capture |
| desktop/application state | defer | FSOS desktop adapter | High-risk, not first-wave |
| system events / filesystem events | defer | event-triggered acquisition | Event-trigger implementation not built yet |
| voice transcripts | should be added later | voice transcript capture, user-confirmed import, `Voice-IO-Architecture.md` retention rules | Voice I/O is OSRIL/Phase 10 surface; transcripts route through capture only after explicit review and do not become canonical truth by default |

---

## Additional Surfaces

| Surface | Classification | Reason |
|---|---|---|
| market data provider snapshots | should be added | Strong StrikeZone input if API/export-based and credential scoped |
| exchange account/position data | exclude for now | Financial action surface; do not acquire until read-only keys, audit, and risk policy are formalized |
| credential stores / `.env` values | exclude for now | Credentials are not source material; agents may confirm presence only with approval |
| external issue trackers / PR systems | should be added later | Useful project digest source through GitHub/Linear/Jira connectors |
| local model outputs | should be added | Treat as runtime-generated drafts with provenance |

---

## Acquisition Method Classification

| Method | Current status | Risk/authority notes | Best use |
|---|---|---|---|
| direct file read | already live | Must be manifest/role-card scoped for runtimes | Vault notes, logs, project OS files, docs |
| connector capture | already live | Quarantine-first; credentials by env var only | Grok, Perplexity, RSS, saved research |
| watch-folder intake | already live | Poll-only; no recursive scan in current implementation | User drop folders and exports |
| browser capture helper | already live | Saved/local HTML path; content treated as untrusted | Manual web exports |
| browser operator control | partially live | Isolated context, scoped origins, no credentials/forms by default | Declared URLs, articles, dashboards |
| full-system operator surface / Playwright path | partially live | Browser Tier A live; terminal/desktop/filesystem stubs | Browser research acquisition only for first wave |
| MCP-mediated read | partially live | Curated endpoints only; no new surfaces in this pass | Runtime state queries, bounded resources |
| runtime-native read | partially live | Requires adapter contract; no ambient runtime memory reads | OpenClaw/Hermes declared run history |
| CLI-triggered capture | already live | User/session invoked; sidecar + dedup | First implementation path |
| schedule-triggered acquisition | partially live | Schedules exist; acquisition workflow not built | Future recurring source packs |
| event-triggered acquisition | architecture-only | Event-trigger workflows not built | Future alerts, file events, price alerts |
| on-demand manual run | already live | Safest first invocation model | First implementation of source packs |
| webhook / push ingest | defer | Requires auth, payload validation, replay protection | Future Discord/n8n/GitHub events |
| API poll | partially live | Per-connector credentials/rate/cost controls | Market/news/research APIs |
| HTML scrape / conversion | partially live | Prefer structured extraction; respect scope | Browser pages and saved HTML |
| screenshot / OCR fallback | future-facing | Use only when DOM/API/text unavailable; lower confidence | Chart pages, visual dashboards |
| user-confirmed import | already live | Human chooses source; still needs provenance | Local files, exports, PDFs |
| approval-gated acquisition | should be added | Required for sensitive dashboards, auth pages, email, clipboard | High-sensitivity sources |
| memory replay / handoff replay | partially exists | Must not treat runtime memory as canonical | Runtime continuity and repair review |
| digest rehydration from prior artifacts | should be added | Rebuild packs from known sidecars/logs without refetching | Reproducible briefings and traceability |

---

## First Implementation Status

Pass 1A implements the safest first method set:

1. direct file read of declared vault/log/manual-drop-in sources
2. acquisition plan validation before any read
3. bounded runtime-local source-pack output only

Future first-wave expansions may add:

1. connector capture via existing Phase 8 connectors
2. watched-folder/user-confirmed imports
3. browser operator extraction for declared URL lists only
4. digest rehydration from prior sidecars and logs

### Trading Research Source-Class Expansion - 2026-04-27

The acquisition layer now recognizes the first safe trading research source classes without granting new acquisition authority:

| Source class | Intended input | Current allowed model |
|---|---|---|
| `perplexity_digest` | Perplexity scheduled task output, saved/API capture, or staged digest | local file, staged capture, quarantine/import rehydration |
| `youtube_summary` | User-confirmed trader video/channel summary or transcript-derived summary | local file, watched/drop-in import, quarantine/import rehydration |
| `research_export` | NotebookLM-style synthesis, altFINS/Market Masters view export, TradingView idea export, or other saved research bundle | local file, watched/drop-in import, quarantine/import rehydration |
| `grok_digest` | Optional Grok/X market digest or saved xAI capture | local file, staged capture, quarantine/import rehydration |

This source-class identity is separate from downstream analysis. It does not add browser authority, authenticated scraping, API polling, social crawling, delivery authority, MCP scope, native cron, or canonical mutation.

Operator preview path: `runtime/acquisition/research_imports.py` scans declared local/import drop folders under `runtime/acquisition/manual/strikezone/` through `chaseos acquisition preview-research --profile strikezone`. `runtime/acquisition/plans/strikezone-daily.json` declares those folders as local read scope, while concrete source entries are discovered from dropped files at preview time. Preview is read-only by default; `--write` writes runtime-local pack artifacts only and does not update a latest pointer, deliver externally, or promote content.

Reviewed preview promotion path: `chaseos acquisition promote-research-preview --briefing-input <path> --reviewed --profile strikezone` validates a written preview BRIS and normalized pack before updating `runtime/acquisition/packs/strikezone-latest.json`. This is a runtime pointer update only; it does not mutate canonical vault notes, delivery adapters, MCP, browser authority, or schedules.

SBP consumption proof path: `chaseos acquisition verify-research-sbp --profile strikezone` checks the current StrikeZone latest pointer against the existing `sbp_strikezone_digest` `acquisition-pack` input adapter without running digest synthesis or delivery. Default mode requires a reviewed research-preview pointer; `--allow-non-preview` verifies generic adapter consumption of the current latest pointer.

Readiness status path: `chaseos acquisition research-status --profile strikezone` is a read-only operator surface for the same local/import lane. It counts present files under the declared source-class folders, reports current latest-pointer provenance, and returns the next action needed before reviewed-preview promotion or default SBP verification.

Local/import metadata enrichment path: operator-supplied frontmatter or JSON metadata in declared StrikeZone research files can populate title/display name, declared URL, source event time, captured time, and author/platform notes in existing acquisition source records. This remains local file import only and does not create browser authority, network access, MCP scope, delivery authority, native cron, canonical mutation, approval state, or trust-tier elevation.

Operator guide path: `runtime/acquisition/manual/strikezone/StrikeZone-Research-Import-Operator-Guide.md` and `templates/` provide manual export guidance, folder-content expectations, and safe metadata formats outside scanned drop folders. `research-status` reports recommended and optional source-class coverage without writing artifacts.

Methods to treat as dangerous or over-authoritative until later:

- ambient browser history
- authenticated dashboard scraping
- email and clipboard ingestion
- exchange account data
- social feed crawling
- desktop/application state
- event-triggered actions without approval gates

*Acquisition-Surface-Map.md - v1.5 | Created: 2026-04-23 | Updated: 2026-04-28 | Phase 9 Acquisition + Normalization surface status + trading research preview, metadata enrichment, operator setup, and reviewed latest-pointer promotion path*


*Graph links: [[Vault-Map]] · [[Source-Intelligence-OS]] · [[StrikeZone-Acquisition-Normalization-Pilot]]*
