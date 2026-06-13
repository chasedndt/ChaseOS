---
title: Runtime Acquisition Responsibility Matrix
type: architecture
status: canonical - Phase 9 responsibility split
version: 1.2
created: 2026-04-23
updated: 2026-04-27
phase: Phase 9 - Acquisition + Normalization
knowledge_class: canonical-state
---

# Runtime Acquisition Responsibility Matrix
## ChaseOS - Who Gathers What, Under Which Boundaries

> Runtimes can help gather source material only inside declared acquisition plans, workflow manifests, role cards, and adapter contracts. This matrix defines responsibility split; it is not a permission grant.

---

## Current Assumptions - Confirmed Or Revised

| Assumption | Decision | Repo-truth basis |
|---|---|---|
| OpenClaw is the first live executor/acquisition lane for schedule/Discord-connected workflows | Confirmed with caveat | OpenClaw is live and schedule-source sync is complete; ChaseOS still owns schedule truth |
| Hermes parity is constitutional; current acquisition breadth is narrower by implementation state, not lower authority | Revised | Hermes is an active bounded Discord lane with narrower currently enabled acquisition/workflow breadth |
| MCP is a bounded internal interface, not ambient power source | Confirmed | `workflow.invoke_bounded` remains exact allowlist: `operator_today`, `operator_close_day` only |
| Browser control is a first-class acquisition primitive | Confirmed | Browser operator surface is parked but live for declared browser research/extraction |
| Schedule execution remains OpenClaw-owned for now | Confirmed | Native ChaseOS cron is not built; OpenClaw consumes derived schedule intent |
| Native ChaseOS cron remains out of scope | Confirmed | Schedule intent exists; cron runner does not |

---

## Runtime Responsibility Matrix

| Runtime/surface | Acquisition classes | May do | Must not do | Current status | First use in this layer |
|---|---|---|---|---|---|
| Claude Code / Codex / Anthropic-compatible harnesses | Architecture passes, direct repo/vault reads, declared source-pack builds, manual/on-demand normalization | Read/write docs and log artifacts per user direction; build acquisition contracts; run local tests; create source-pack docs | Act as scheduled daemon; self-authorize external APIs; bypass protected-file approval | Active development lanes | Maintain source-pack builder, docs, tests, and local/import preview conventions |
| OpenClaw | Scheduled AOR workflows, schedule-triggered acquisition plans, Discord-connected workflow execution, operator brief/digest runs | Invoke declared `chaseos run <workflow>` or command schedules derived from `runtime/schedules/`; execute bounded workflows; produce AOR logs | Own schedule truth; maintain duplicate cron truth; broaden workflow set without manifest/role card; write canonical files directly | Live bounded runtime adapter | Scheduled executor for declared acquisition, digest, event-watch, and watch-loop paths |
| Hermes | Bounded Discord command/envelope lane, one shadow operator workflow, future approval-gated source requests | Observe/handle declared Discord approval envelopes; write draft/audit outputs for approved shadow workflow | Shell, connectors, canonical promotion, protected-file writes, self-approval, broad browser acquisition | Active bounded Discord runtime lane, narrow current implementation breadth | Runtime-specific acquisition/approval relay with authority parity to OpenClaw but narrower current enablement |
| Browser Operator Surface | Declared URL/page/dashboard/article/chart acquisition | Navigate scoped URLs/origins; extract visible/DOM text; capture screenshot; route extracted content through quarantine | Read personal browser history; use saved credentials; submit forms; download files; crawl broadly; treat page text as instruction | Parked but live for Tier A browser extraction and `browser_research` | First browser acquisition method for declared source lists |
| Runtime MCP | Curated runtime resources and exact bounded workflow invocation | Serve V1 resources; invoke only allowlisted operator workflows in `draft_execution` for OpenClaw | Add acquisition surfaces; become generic file/network/browser bridge; invoke SBP/StrikeZone unless explicitly designed later | Live V1 + bounded V2 | No new role in this pass |
| SIC | Promoted source packages, workspace evidence, retrieval outputs | Query workspaces, produce evidence, generate outputs, persist workspace-local artifacts | Ingest raw quarantine automatically; promote to knowledge; own acquisition scope | Complete Phase 7 subsystem | Consume normalized packs after promotion/ingestion |
| Capture CLI/connectors | External content intake and quarantine | Capture files/stdin/RSS/browser-saved/Perplexity/Grok/watch folders with sidecar/dedup | Promote knowledge; decide workflow source strategy; run scheduled daemon as connector-only concern | Complete Phase 8 subsystem | Main first-wave intake methods |
| SBP substrate and instance handlers | Briefing-ready input consumption, generation, vault/local/external delivery | Consume declared input adapters; generate briefing; write to `07_LOGS/SBP-Runs/`; deliver via declared adapters | Implement bespoke scraping inside every instance; promote to canonical; hide source provenance | Substrate live; StrikeZone instance observed in repo | Downstream consumer of acquisition packs |
| Future OpenAI Agent Harness | Scoped acquisition/normalization execution | Same as Claude harness once adapter contract and permissions exist | Use provider identity as permission; bypass Gate; ambient MCP reads | Planned | Alternative executor after adapter stabilization |
| Future n8n | Pure orchestration, webhook/poll scheduling, connector handoff | Trigger declared capture/acquisition workflows; pass structured payloads; maintain auth/rate limits | Own ChaseOS truth; write canonical vault state; bypass AOR/Gate | Not deployed | Later push/webhook acquisition orchestration |
| Future local/OSS harness | Local acquisition and normalization for privacy-sensitive packs | Run declared local reads/normalization within path scope | Ambient filesystem roaming; unsupervised desktop/app state | Future | Local-first normalization option |

---

## Responsibility By Acquisition Class

| Acquisition class | Primary owner | Secondary owner | Notes |
|---|---|---|---|
| local vault/log acquisition | Claude Code for implementation; AOR for workflows | OpenClaw when executing scheduled AOR workflows | Use direct file reads with declared scope |
| quarantine/capture acquisition | Phase 8 capture subsystem | AOR/OpenClaw can invoke later when declared | Capture remains quarantine-first |
| browser URL acquisition | Browser Operator Surface | OpenClaw can trigger the workflow; Claude can implement | Isolated context only |
| external digest acquisition | Capture connectors and acquisition adapters | AOR/OpenClaw for declared scheduled runs | Perplexity/Grok/RSS live on demand; Acquisition Pass 2/2B adds RSS/web/email/Google staging before builder reads |
| runtime history acquisition | AOR audit/log layer | Runtime-specific adapters | No ambient runtime memory reads |
| user objective acquisition | AOR/task manifests and operator prompts | Runtime Shell/OSRIL later | Objectives guide gathering; they are not evidence |
| delivery packet preparation | SBP/delivery adapters | Acquisition + Normalization provides source refs | Delivery is downstream |
| memory candidate preparation | Agent Memory layer | AOR/normalizer | Review required before durable memory |

---

## Runtime Boundary Rules

1. A runtime may gather only sources declared by the acquisition plan, workflow manifest, role card, or explicit operator instruction.
2. A runtime may normalize only into declared artifact destinations.
3. A runtime may not self-expand source scope during a run. It may emit a gap/request for operator approval.
4. Browser runtimes use isolated contexts and scoped URL/origin lists.
5. Schedule-triggered acquisition uses ChaseOS-owned schedule intent and OpenClaw execution until native cron exists.
6. MCP remains a narrow runtime interface and does not become an acquisition bus in this pass.
7. Every runtime-produced pack must include acquirer identity and audit reference.

---

## First Implementation Status

Pass 1A implemented the first generic source-pack substrate with Claude Code as the development lane:

1. `runtime/acquisition/` now validates acquisition plans and first-wave normalized artifacts.
2. `LocalDeclaredSourceAdapter` reads only declared vault/log/manual-drop-in local sources.
3. `SourcePackBuilder` produces `source_packet`, `normalized_source_pack`, and `briefing_ready_input_set`.
4. The StrikeZone fixture proves the path without live browser, connector/API, MCP, cron, delivery, or trading-action authority.
5. All outputs stay under declared runtime-local packet paths.

2026-04-27 repo-observed updates:

1. SBP Pass 1B and Acquisition Pass 1C wired `briefing_ready_input_set` consumption, latest-pointer resolution, `strikezone_acquisition`, and `sch-strikezone-acquisition-0550`.
2. Acquisition Pass 2/2B added SQLite artifact storage plus RSS/web/email/Google live-source adapters before the file-read builder boundary.
3. `runtime/acquisition/research_imports.py` and `chaseos acquisition preview-research --profile strikezone` provide a local/import-only preview path for declared StrikeZone research drop folders.
4. These updates do not grant MCP scope, browser credential authority, delivery authority, exchange/account access, or canonical promotion authority.

*Runtime-Acquisition-Responsibility-Matrix.md - v1.2 | Created: 2026-04-23 | Updated: 2026-04-27 | Phase 9 Acquisition + Normalization responsibility split + Pass 1C/2/2B + local/import preview status*


*Graph links: [[Vault-Map]]*
