---
title: StrikeZone Acquisition + Normalization Pilot
type: pilot-contract
status: canonical - pilot architecture active; Pass 1A-1D, Pass 2/2B, SBP consumption, latest pointer, local/import preview path, local/import metadata enrichment, operator setup guide/templates, reviewed pointer promotion, read-only SBP verification, and research readiness status repo-observed; Phase 10A0 cockpit planned for live-file testing
version: 1.8
created: 2026-04-23
updated: 2026-04-29
phase: Phase 9 - Acquisition + Normalization
knowledge_class: canonical-state
---

# StrikeZone Acquisition + Normalization Pilot
## ChaseOS - Crypto Daily Digest Source Pack Contract

> StrikeZone is the first serious pilot for the Acquisition + Normalization Layer. It is not the whole identity of the feature family. The pilot defines how crypto/trading sources become a governed daily source pack before a digest or delivery pipeline consumes them.

---

## 1. Repo-Observed Starting Point

Direct repo inspection on 2026-04-23 and 2026-04-27 shows:

| Surface | Observed state |
|---|---|
| SBP substrate | `runtime/sbp/` exists with manifest, guardrail, input adapter, delivery adapter, base handler, runner |
| StrikeZone SBP manifest | `runtime/workflows/registry/sbp_strikezone_digest.yaml` exists and is `status: active` |
| StrikeZone SBP handler | `runtime/workflows/sbp_strikezone_digest.py` exists |
| StrikeZone schedule | `runtime/schedules/sch-sbp-strikezone-digest-0600.yaml` exists and targets OpenClaw |
| Discord delivery | `DiscordDeliveryAdapter` exists and uses `DISCORD_WEBHOOK_URL` env var |
| Pass 1A acquisition fixture | `runtime/acquisition/fixtures/strikezone_pass1a/acquisition_plan.json` with safe local fixture sources |
| Pass 1A normalized pack output | `runtime/acquisition/packs/strikezone_pass1a_fixture/2026-04-23/` with `source_packet_*.json`, `normalized_source_pack.json`, and `briefing_ready_input_set.json` |
| SBP acquisition-pack consumption | `AcquisitionPackInputAdapter` and StrikeZone digest handler consumption are repo-observed complete after SBP Pass 1B |
| Latest pointer / acquisition workflow | `strikezone_acquisition` workflow, latest-pointer resolution, and `sch-strikezone-acquisition-0550` are repo-observed after Acquisition Pass 1C |
| Live-source adapters | Acquisition Pass 2 + 2B added SQLite artifact store plus RSS/web/email/Google adapter surfaces before the file-read builder boundary |
| Local/import research preview | `runtime/acquisition/research_imports.py`, `chaseos acquisition preview-research`, and `runtime/acquisition/manual/strikezone/` drop folders are repo-observed |
| Local/import metadata enrichment | Operator-supplied frontmatter/JSON metadata for title, declared URL, source event time, captured time, and author/platform notes is repo-observed for local/import research files |
| Operator research import guide/templates | `runtime/acquisition/manual/strikezone/StrikeZone-Research-Import-Operator-Guide.md` plus safe templates under `runtime/acquisition/manual/strikezone/templates/` are repo-observed for manual source export setup |
| Reviewed preview SBP verification | `chaseos acquisition verify-research-sbp --profile strikezone` proves a reviewed research-preview latest pointer can be read by the existing StrikeZone SBP `acquisition-pack` adapter without running synthesis or delivery |
| Research readiness status | `chaseos acquisition research-status --profile strikezone` reports present source-class files, recommended/optional source-class coverage, latest-pointer provenance, SBP consumability, default verification readiness, and next actions without writing artifacts |
| Remaining missing pieces | Real source availability/credentials, browser metadata capture for some sources, Whop/n8n live delivery expansions, and any canonical promotion remain separate downstream passes |

This pilot does not rebuild the digest publisher. The source-pack layer, SBP consumption, latest pointer, local/import preview path, reviewed promotion, read-only SBP verification, and research readiness status are present; live usefulness still depends on declared sources, configured credentials where applicable, and downstream delivery/runtime choices.

---

## 2. Pilot Objective

Build a daily StrikeZone crypto market source pack that can be generated before the digest pipeline runs.

Target result:

```text
declared trading source classes
  -> bounded acquisition methods
  -> normalized source packets
  -> trust/freshness/actionability evaluation
  -> briefing-ready StrikeZone source pack
  -> SBP digest generation and delivery
```

The pack supports briefings and operator review. It does not issue trades, place orders, change risk settings, or create canonical market doctrine.

---

## 3. Source Classes

| Source class | Examples | First-wave status | Default trust | First method |
|---|---|---|---|---|
| user morning thesis notes | operator notes, prior thesis, active focus | already exists | Tier 1/2 depending location | direct file read |
| existing StrikeZone project state | `01_PROJECTS/StrikeZone/StrikeZone-Crypto-OS.md` | already exists | Tier 1 | direct file read |
| ChatGPT-created research/digests | pasted/exported chat output | should be added through import | Tier 3 research, Tier 4 until reviewed | user-confirmed import/watch folder |
| Perplexity outputs/tasks | API output, citations, scheduled task exports | recognized source class: `perplexity_digest` | Tier 3 research | staged capture, user-confirmed import, Perplexity connector |
| Grok/X market digests | xAI output, saved market narratives | recognized source class: `grok_digest` | Tier 3 research | staged capture, user-confirmed import, Grok connector |
| YouTube summaries/transcripts | channel/video summaries, captions | recognized source class: `youtube_summary` | Tier 3/4 depending summary provenance | manual transcript/summary import; browser metadata later |
| TradingView ideas | idea pages, author posts | should be added | Tier 4 until triage | browser operator declared URLs |
| market news websites | articles, news feeds | should be added | Tier 4 until triage | RSS/API first, browser extraction second |
| X/Twitter/social posts | specific posts, lists, feed excerpts | defer for broad feeds; allow explicit post import | Tier 4 | user-confirmed import or declared URL only |
| runtime observations | previous digest gaps, OpenClaw/AOR run notes | partially exists | Tier 2 as execution history | AOR audit/log read |
| saved outputs from trading toolchain | exports, screenshots, markdown notes, NotebookLM-style synthesis, altFINS/Market Masters views, TradingView ideas | recognized source class: `research_export` | depends source; default Tier 3/4 until reviewed | watched folder/user-confirmed import |
| chart screenshots/pages | TradingView chart snapshots | should be added later | Tier 4 evidence, low actionability | screenshot with metadata; OCR/vision later |
| live market data APIs | price/funding/vol/open interest snapshots | should be added later | provider-dependent; Tier 3/4 | credential-scoped API poll |

---

## 4. Acquisition Methods For Pilot

| Method | Pilot use | Automation status | Approval requirement |
|---|---|---|---|
| direct file read | Now.md, StrikeZone OS, prior SBP run, operator notes | live | manifest/role-card scope |
| connector capture | Perplexity, Grok, RSS feeds | live on demand | credential use requires approval/env discipline |
| watched-folder intake | ChatGPT exports, trading toolchain files, saved markdown/HTML | live | user-configured folder |
| local/import research preview | saved Perplexity digests, YouTube summaries, Grok digests, trading research exports | live via `chaseos acquisition preview-research` | declared drop folders only; no latest-pointer, delivery, or canonical promotion by default |
| reviewed research preview verification | promoted local/import research preview pack | live via `chaseos acquisition verify-research-sbp` | read-only adapter proof; no digest synthesis, delivery, canonical promotion, MCP, browser, or schedule change |
| research readiness status | local/import research lane | live via `chaseos acquisition research-status` | read-only readiness and next-action report; no pack write, pointer write, delivery, MCP, browser, or schedule change |
| browser operator extraction | TradingView ideas, articles, YouTube metadata, declared dashboard URLs | partially live | URL/origin declared; no auth/form/download |
| user-confirmed import | social posts, screenshots, PDFs, unusual files | live/manual | user chooses item |
| schedule-triggered acquisition | daily pre-digest run | partially live | `sch-strikezone-acquisition-0550` exists; live output depends on available/configured sources |
| API poll | market data providers | future | credential/rate/cost approval required |
| screenshot/OCR fallback | chart images when text/API unavailable | future | explicit operator approval |

First implementation avoids broad social-feed crawling, authenticated dashboard scraping, exchange data, and any trading action. The preview path uses only declared local/import drop folders.

---

## 5. Normalization Targets

| Target artifact | Purpose | Suggested future path | Required fields |
|---|---|---|---|
| `strikezone_source_packet` | One source item with normalized text and provenance | `runtime/acquisition/packs/strikezone/<date>/items/` | source_origin, method, captured_at, source_event_at, trust_tier, freshness, raw_ref |
| `strikezone_daily_source_pack` | Full daily bundle of all source packets | `runtime/acquisition/packs/strikezone/<date>/source_pack.json` | date, objective, source_packets, trust_summary, freshness_gaps, excluded_sources |
| `strikezone_briefing_input_set` | Digest-ready structured packet | `runtime/acquisition/packs/strikezone/<date>/briefing_input.json` | market_context, thesis_context, source_sections, risk_flags, citations |
| `strikezone_pack_summary` | Human-inspectable markdown summary | `07_LOGS/Acquisition-Packs/YYYY-MM-DD-strikezone-source-pack.md` | source table, gaps, warnings, next-step notes |
| `strikezone_memory_candidate` | Possible recurring lesson or source quality note | future `runtime/memory/candidates/` | proposed lesson, evidence refs, outcome feedback placeholder |

Do not write pilot normalization outputs to `02_KNOWLEDGE/`, project OS files, or protected files.

Pass 1A concrete output path: `runtime/acquisition/packs/strikezone_pass1a_fixture/2026-04-23/`. The fixture creates only the generic artifact names (`source_packet_001.json`, `source_packet_002.json`, `source_packet_003.json`, `normalized_source_pack.json`, `briefing_ready_input_set.json`) rather than StrikeZone-specific schemas.

2026-04-27 source-class expansion: `runtime/acquisition/source_classes.py` now makes `perplexity_digest`, `youtube_summary`, `research_export`, and `grok_digest` first-class acquisition source classes. The generic artifact names remain unchanged; the source identity lives in each `source_packet.source_class` and BRIS `sections` key.

2026-04-27 local/import preview path: `runtime/acquisition/research_imports.py` scans `runtime/acquisition/manual/strikezone/perplexity_digest/`, `youtube_summary/`, `research_export/`, and `grok_digest/`. `chaseos acquisition preview-research --profile strikezone` is read-only by default; `--write` writes runtime-local preview pack artifacts without updating `strikezone-latest.json`, delivering externally, or promoting source material.

The daily StrikeZone acquisition plan declares those source-class folders in read scope through `runtime/acquisition/plans/strikezone-daily.json`; concrete research files are discovered by the preview command when the operator has dropped saved exports into those folders.

2026-04-27 reviewed latest-pointer promotion path: after reviewing a written preview pack, the operator can run `chaseos acquisition promote-research-preview --briefing-input <path> --reviewed --profile strikezone`. The command validates that the BRIS came from a StrikeZone research-import preview pack and then updates only `runtime/acquisition/packs/strikezone-latest.json`, allowing the current SBP digest adapter to consume the richer pack through the existing latest-pointer path.

2026-04-28 read-only SBP verification path: `chaseos acquisition verify-research-sbp --profile strikezone` verifies that the current `strikezone-latest.json` pointer resolves through `sbp_strikezone_digest`'s existing `acquisition-pack` input adapter. Default mode requires reviewed research-preview provenance; `--allow-non-preview` verifies the generic adapter path against the current latest pointer.

2026-04-28 readiness status path: `chaseos acquisition research-status --profile strikezone` reports whether research files are present in the declared source-class folders, whether the latest pointer is a reviewed preview, whether the current pointer is SBP-consumable, and what the operator should do next. Live status on 2026-04-28 reports zero local/import research files and a current `strikezone-daily` latest pointer.

2026-04-28 local/import metadata enrichment: dropped research files may declare optional source identity metadata in frontmatter or JSON. The preview/status path maps title/display name, declared URL, source event time, captured time, and author/platform notes into existing acquisition source fields, then into source packets and pack freshness/provenance through the generic builder. Metadata does not raise trust tier, mark content reviewed, request network access, expand browser authority, update the latest pointer, mutate canonical notes, or grant delivery authority.

2026-04-28 operator setup kit: `runtime/acquisition/manual/strikezone/StrikeZone-Research-Import-Operator-Guide.md` tells the operator which source exports must be saved manually, where they belong, and what each folder should contain. Templates under `runtime/acquisition/manual/strikezone/templates/` provide safe metadata formats outside the scanned drop folders. `research-status` reports recommended source classes (`perplexity_digest`, `youtube_summary`, `research_export`), optional source classes (`grok_digest`), and missing recommended coverage without writing artifacts.

2026-04-29 Phase 10A0 testing handover: the remaining practical blocker is live operator workflow, not pilot architecture. The next UI pass should build a local-only Studio Acquisition Intake Cockpit that surfaces `research-status`, imports/drops real local source files into the declared source-class folders, runs preview, writes preview only on explicit action, promotes reviewed preview only on explicit confirmation, and runs read-only SBP verification. Final proof of this lane requires real local research files; synthetic files are acceptable only for first UI plumbing tests.

---

## 6. Digest-Ready Source Contract

The SBP digest should consume a briefing-ready input set with this minimum shape:

```yaml
pipeline_id: "strikezone_daily_source_pack"
date: "YYYY-MM-DD"
generated_at: "ISO-8601"
acquirer: "workflow_or_runtime_id"
objective: "Prepare StrikeZone morning crypto digest inputs"
sections:
  user_thesis:
    content_ref: "path_or_null"
    freshness: "same_day|stale|missing"
  market_news:
    items: []
  research_digests:
    items: []
  tradingview_ideas:
    items: []
  youtube_or_longform:
    items: []
  runtime_observations:
    items: []
trust_summary:
  tier1_count: 0
  tier2_count: 0
  tier3_count: 0
  tier4_count: 0
  conflicts: []
freshness_summary:
  stale_items: []
  missing_required_sources: []
actionability:
  allowed_use: "briefing_only"
  blocked_actions:
    - "trade_execution"
    - "canonical_knowledge_promotion"
source_refs: []
```

The digest may summarize this packet. It may not infer unsourced market facts or convert Tier 4 material into trade instructions.

---

## 7. Trust / Provenance Treatment

| Source | Base provenance | Freshness rule | Actionability |
|---|---|---|---|
| Now.md / StrikeZone OS | canonical vault path + file timestamp | warn if stale | briefing context only |
| prior SBP run | run path + AOR/SBP audit if available | same-day or prior-day only | continuity context |
| Perplexity/Grok | sidecar + query/model/citations/usage where available | same-day preferred; stale after 24h for trading | briefing only; verify before action |
| RSS/news | sidecar + source URL + published date | source event date required when available | briefing only |
| TradingView/social | URL + author + capture timestamp + screenshot/HTML if available | same-day preferred; stale quickly | review required |
| YouTube summaries | URL/video id + transcript/source metadata | event date and upload date noted | context only unless verified |
| chart screenshots | screenshot path + source page URL + timestamp | stale immediately for action | visual evidence only |
| runtime observations | AOR audit/log refs | same week unless workflow-specific | workflow improvement context |

Outcome scoring can later record whether a source class was useful after market behavior unfolds. It must not rewrite base provenance.

---

## 8. Delivery Targets

| Delivery target | Status | Rule |
|---|---|---|
| vault-local pack summary | runtime-local pack artifacts live | Writes only to runtime/log-local pack paths unless a separate promotion gate is invoked |
| SBP digest input | live via acquisition-pack input adapter/latest pointer | Consumed by `sbp_strikezone_digest`; live quality depends on source availability and current pack freshness |
| Discord digest delivery | repo-observed in SBP instance | Delivery happens after SBP generation, not from acquisition pack |
| Whop/dashboard update | future | Must be declared delivery adapter |
| operator review | always allowed | Review packet can surface gaps and approvals |

---

## 9. Runtime Responsibilities

| Runtime/surface | Pilot responsibility |
|---|---|
| Claude Code / Codex | Build and maintain implementation passes, docs, logs, and tests |
| OpenClaw | Execute declared schedules and watch-loop exports from `runtime/schedules/` |
| Browser Operator Surface | Acquire declared URL/page content into quarantine/source packets |
| Capture connectors | Pull Perplexity/Grok/RSS and watched folder imports |
| SBP | Consume briefing-ready input set and generate/deliver digest through declared delivery adapters |
| Hermes | No first-wave acquisition role beyond possible Discord approval relay later |
| MCP | No scope change; not used for StrikeZone source acquisition in this pass |

---

## 10. Manual vs Automated

### Manual / approval-based first

- choosing monitored sources and watchlists
- importing ChatGPT/social/screenshot/PDF sources
- approving authenticated dashboard reads
- handling contradictions or injection flags
- promoting any source-derived knowledge
- changing delivery targets
- acting on trading decisions

### Automate first

- direct read of declared vault context
- rehydrating prior pack/run history
- Perplexity/Grok/RSS capture with env-var credentials and audit
- watched-folder import for user-designated exports
- local/import research preview from `runtime/acquisition/manual/strikezone/`
- declared URL browser extraction
- pack assembly, trust summary, freshness/gap report
- vault-local source-pack summary

---

## 11. Template Value For Future Users

The StrikeZone pilot pattern should be reusable:

```text
domain source classes
  -> existing capture/browser/local methods
  -> normalized daily/project/research source pack
  -> briefing-ready input set
  -> SBP/operator workflow
  -> delivery/review/memory candidate
```

Replace crypto sources with household docs, project dashboards, university readings, work meetings, or content metrics. The source-pack contract stays the same.

### Summary-context application
For how source-pack artifacts and briefing-ready input sets should remain distinct from downstream briefs and other human-facing outputs in future standalone surfaces, see:
- `06_AGENTS/Acquisition-and-Source-Pack-Summary-Context-Application.md`

---

## 12. Not In Scope

- trade execution
- exchange account acquisition
- automated financial advice
- unsupervised social feed scraping
- authenticated dashboard scraping without approval
- canonical promotion
- new MCP surfaces
- native ChaseOS cron
- broad Discord automation

*StrikeZone-Acquisition-Normalization-Pilot.md - v1.8 | Created: 2026-04-23 | Updated: 2026-04-29 | Pass 1A-1D, Pass 2/2B, SBP consumption, latest pointer, local/import preview path, local/import metadata enrichment, operator setup guide/templates, reviewed pointer promotion, read-only SBP verification, research readiness status, and Phase 10A0 live-file testing handover repo-observed*


*Graph links: [[Vault-Map]]*
