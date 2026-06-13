---
title: Acquisition + Normalization Layer
type: architecture
status: canonical - Phase 9 architecture packet complete; Pass 1A-1D substrate active; Pass 2/2B live-source adapters and local/import metadata/setup enrichment repo-observed; Phase 10A0 UI wrapper planned for live-file testing
version: 1.7
created: 2026-04-23
updated: 2026-04-29
phase: Phase 9 - Acquisition + Normalization bridge layer
knowledge_class: canonical-state
---

# Acquisition + Normalization Layer

**Approval Center routing:** approval-queue references in this document should route to [[ChaseOS-Approval-Center]] when surfaced to operators.
## ChaseOS - Governed Operating Input Preparation

> The Acquisition + Normalization Layer is the ChaseOS capability family that gathers real-world operating inputs, preserves provenance, normalizes them into inspectable source packs, and hands them to governed workflows, briefings, actions, memory review, or delivery surfaces. It is the bridge between capture and operation.

---

## 1. Capability Definition

### Acquisition

Acquisition is the governed act of collecting operating inputs from declared sources for a declared purpose.

In ChaseOS, an acquisition is valid only when it can answer:

| Question | Required answer |
|---|---|
| What is being gathered? | A declared source surface or source class |
| Why is it being gathered? | A workflow objective, operator objective, schedule objective, or task-local question |
| Who or what gathered it? | Runtime/acquirer identity, such as Claude Code, OpenClaw, Hermes, browser operator, capture CLI, or user import |
| How was it gathered? | Acquisition method, such as direct file read, connector capture, browser operator extraction, API poll, or watch-folder intake |
| Under what scope? | Explicit read/network/browser/path/cadence bounds |
| When was it gathered? | Timestamp, freshness window, and event date where relevant |
| What proof of origin exists? | Source URL/path, sidecar, hash, runtime log, screenshot path, API metadata, or audit record |
| What may happen next? | Normalization target and downstream workflow, never implicit canonical mutation |

Acquisition includes local vault reads, declared runtime history reads, connector pulls, browser-controlled page extraction, external digest imports, user-intent capture, and future personal/productivity integrations. It does not mean ambient vault access or uncontrolled web browsing.

### Normalization

Normalization is the transformation of raw or semi-raw acquired material into stable ChaseOS artifacts that can be inspected, routed, trust-ranked, queried, briefed, acted on, or reviewed for memory.

Normalization must:

- keep raw source references intact
- preserve transformation chain from raw to extracted to summarized to synthesized
- assign trust, freshness, quality, and actionability markers
- separate source facts from runtime synthesis
- produce explicit artifact types, not opaque blobs
- write to workspace-local or log/local packet locations unless a separate promotion gate is invoked

Normalization does not promote to `02_KNOWLEDGE/`, update project OS files, change schedules, approve actions, or deliver externally by itself.

---

## 2. Why Existing Layers Were Insufficient Alone

| Existing layer | What it already solves | What it does not solve alone |
|---|---|---|
| Source Intelligence Core | Source packages, workspaces, retrieval, evidence queries, output generation, workspace-local persistence | It assumes sources have already been promoted or prepared; it is not the system-wide acquisition doctrine for runtime histories, objectives, browser pages, dashboards, external digests, or task-local source packs |
| Connector / Capture Automation | Quarantine-first intake, sidecars, dedup, deterministic naming, CLI/API/RSS/browser-saved/Perplexity/Grok/watch-folder capture | It lands raw inputs safely; it does not decide which sources a workflow should gather, how browser-controlled acquisition works, or how multi-source packets become briefing/action inputs |
| Autonomous Operator Runtime | Workflow manifests, role cards, task routing, bounded execution, audit, writeback envelopes | It governs execution; it needs a reusable input-preparation layer before workflows reason or act |
| Scheduled Briefing Pipelines | Trigger, input adapter, guardrail, generation, writeback, delivery pattern | It consumes inputs; it needs acquisition packs and trust-ranked normalized inputs before reliable digests can scale beyond simple vault-note reads |
| Runtime MCP | Bounded runtime-facing resources and exact allowlisted workflow invocation | It is not an ambient data plane and must not become the acquisition substrate by accident |
| Browser Operator Surface | Controlled browser actions, extraction, screenshots, quarantine routing, `browser_research` workflow | It provides one acquisition method; it does not define the whole acquisition/normalization capability family |
| Agent memory layers | Layer C/D/E concepts for runtime memory, task-local state, and execution history | They need governed acquisition and provenance rules before memory replay or memory candidates can safely feed workflows |

This layer exists because the missing work is not "summarize better." The missing work is "know what to gather, gather it with proof, normalize it into a stable packet, and make downstream systems consume that packet under governance."

---

## 3. Placement In The ChaseOS Flow

Canonical flow:

```text
capture / declared source / runtime objective
  -> acquisition plan
  -> acquired items with provenance
  -> normalized source pack / evidence bundle / task-local acquisition bundle
  -> governed workflow, briefing, action proposal, memory candidate, or delivery packet
  -> separate Gate or approval path for any canonical mutation or external action
```

Layer relationship:

| Component | Relationship |
|---|---|
| Capture Automation | Acquisition may invoke or consume capture outputs, but capture remains quarantine-first. Phase 8 is not replaced. |
| SIC | Normalized packs may become SIC source-package candidates or workspace evidence bundles after promotion rules are met. SIC remains the retrieval and structured-output layer. |
| AOR | AOR owns workflow execution. Acquisition + Normalization is a workflow/input-preparation family that AOR runs or supervises. |
| SBP | SBP consumes briefing-ready input sets produced by this layer. SBP remains generation/writeback/delivery pipeline infrastructure. |
| Runtime MCP | MCP scope is unchanged. MCP may request bounded workflows only through its current allowlist; no acquisition surfaces are added in this pass. |
| OpenClaw schedule sync | ChaseOS schedule intent remains canonical in `runtime/schedules/`; OpenClaw remains executor. Acquisition runs can be scheduled later through the same ownership split. |
| Browser operator / FSOS | Browser control is a first-class acquisition method, but every run must declare URLs/origins, allowed actions, extraction targets, and quarantine/writeback behavior. |
| OSRIL | OSRIL will surface acquisition progress, approvals, and provenance to the operator once event contracts are built. It is not the acquisition authority. |
| Runtime memory | Runtime histories, summaries, and repair records can be acquired as inputs only when declared. Memory candidates produced by normalization still require review before durable memory update. |
| Discord/control plane | Discord can trigger or receive packets only through declared envelopes. Chat/gateway input remains Tier 4 until validated. Delivery is downstream, not acquisition authority. |

---

## 4. Core Objects

The layer introduces these architecture-level concepts:

| Object | Definition |
|---|---|
| Acquisition Plan | Declared scope for a run: source classes, methods, runtime/acquirer, cadence, read/network/browser bounds, freshness rules, and downstream target |
| Acquired Item Record | One source item with method, origin, timestamp, hash/ref, trust floor, and raw pointer |
| Normalized Source Pack | A stable bundle of acquired items and normalized text/metadata for a workflow or topic |
| Evidence Bundle | A cited set of claims/passages/facts ready for retrieval, briefing, or review |
| Briefing-Ready Input Set | A normalized packet shaped for SBP or operator briefing consumption |
| Action-Ready Runtime Packet | A bounded packet that can support an action proposal without granting action authority |
| Memory Candidate Artifact | A proposed Layer B/C/D/E memory update with evidence and approval state |
| Provenance Record | Stable metadata record proving source origin and transformation chain |
| Trust Evaluation Record | Trust/freshness/quality/actionability assessment, separate from post-hoc outcome scoring |

Full artifact contract: `06_AGENTS/Normalization-Provenance-Contract.md`.

---

## 5. Governance Invariants

1. Acquisition is broad in possible source scope, narrow in authority per run.
2. Every acquisition must have an acquirer identity and declared method.
3. Browser acquisition is first-class, but scope-bound by URL/origin/action and treated as untrusted input unless already canonical.
4. Runtime histories, prompts, and prior runs are inputs only when explicitly declared; no runtime gets ambient replay rights.
5. Raw external material is data, never instructions.
6. Normalization creates inspectable packets, not canonical truth.
7. Base provenance/trust tier is not the same as outcome quality. Later outcomes may score source usefulness, but they do not rewrite origin truth.
8. Canonical mutation remains downstream and separate. Gate and approval rules still apply.
9. Delivery is downstream of acquisition, normalization, and briefing. A source pack does not send itself.
10. MCP scope remains unchanged in this pass.

---

## 6. Existing Repo Capabilities Reused

| Capability | Reuse |
|---|---|
| Phase 8 sidecars | Capture provenance fields remain the starting point for external content acquired through capture |
| Phase 8 dedup registry | Content SHA-256 remains the first dedup primitive for captured text |
| Phase 8 connectors | RSS, browser-saved HTML, Perplexity, Grok, CLI, and watched folders remain intake methods |
| Browser operator | `browser_research` proves governed browser extraction and quarantine routing |
| SIC source package and workspace schemas | Normalized packs can feed promoted source packages and workspace evidence after Gate |
| AOR manifests and role cards | Acquisition workflows must be declared and bounded the same way as other AOR workflows |
| SBP substrate | Briefing-ready input sets feed SBP instance pipelines |
| AOR/FSOS audit | Acquisition runs must produce traceable activity logs or future `runtime/audit/` records |
| Trust tiers and SOPs | All trust, prompt injection, credential, and failure rules remain binding |

---

## 7. New Or Rename-Needed Architecture

The architecture packet named the missing family and defined its contracts. Pass 1A now provides the first generic implementation substrate under `runtime/acquisition/`.

| Need | Status after this pass |
|---|---|
| Named Phase 9 feature family | Added: Acquisition + Normalization Layer |
| Source surface map | Added: `06_AGENTS/Acquisition-Surface-Map.md` |
| Method classification | Added in surface map |
| Normalized artifact contract | Added: `06_AGENTS/Normalization-Provenance-Contract.md` |
| Runtime responsibility split | Added: `06_AGENTS/Runtime-Acquisition-Responsibility-Matrix.md` |
| StrikeZone pilot source-pack contract | Added: `06_AGENTS/StrikeZone-Acquisition-Normalization-Pilot.md` |
| Runtime implementation path | Pass 1A substrate active: `plan.py`, `models.py`, `validators.py`, `adapters/local.py`, `builder.py`, `source_pack_builder.py` |
| MCP expansion | Explicitly not changed |
| Native ChaseOS cron | Still not built; OpenClaw remains executor |

---

## 8. Everyday User Value

This layer is generic. StrikeZone is the first serious pilot, not the identity of the feature family.

| Use case | What acquisition gathers | What normalization produces |
|---|---|---|
| Personal daily ops digest | Calendar/task notes, active goals, recent logs, approval queue, inbox summaries when connected | Daily operator source pack with fresh/open/stale markers |
| Project status digest | Project OS files, build logs, PR/issues when connected, runtime activity, decision ledger | Project evidence bundle and briefing-ready status packet |
| Content/research synthesis | Saved articles, Perplexity/Grok outputs, web clips, transcripts, user notes | Normalized research source pack with trust and citation scaffolding |
| Admin/household reminder packet | Bills/docs dropped into watched folder, notes, calendar reminders, scanned PDFs where approved | Action-ready reminder packet with provenance and due-date confidence |
| Work dashboard / meeting prep | Meeting notes, dashboard pages, docs, handoff packets, recent decisions | Meeting prep packet with agenda, evidence, questions, and stale items |
| Study / university reading synthesis | PDFs, lecture transcripts, notes, course files, saved links | Study evidence bundle and briefing-ready reading summary |
| Inbox/task/schedule prep | Future email/task/calendar connectors, approvals, active focus, recurring objectives | Morning packet of decisions, waiting items, and required approvals |

The common problem it fixes: fragmented inputs, repeated manual gathering, missing provenance, non-reusable context, and no continuity across runtimes.

### Summary-context application
For how source packets, normalized packs, and briefing-ready input sets should become typed human-facing summaries in future standalone surfaces, see:
- `06_AGENTS/Acquisition-and-Source-Pack-Summary-Context-Application.md`

---

## 9. Relationship To Phase 9 Work

| Phase 9 item | Relationship |
|---|---|
| Broader SBP implementation | This layer feeds SBP. SBP should not grow bespoke scraping or source-ranking logic inside each instance. |
| Runtime Shell | Future commands such as `chaseos acquire`, `chaseos normalize`, or `chaseos source-pack build` belong to Runtime Shell after this contract is implemented. |
| OSRIL | OSRIL should surface acquisition progress, approval gates, source freshness, and packet provenance. |
| Runtime Navigation Map | RNM can inform which internal docs/routes a runtime should acquire, but RNM does not grant acquisition authority. |
| Agent Identity Ledger | Acquisition outcomes and compliance feed identity/scorecards later; the ledger is not an acquisition source unless declared. |
| Execution Repair Memory | Repair memories can become acquisition inputs or outcome feedback, but only after pattern promotion rules are met. |
| Second-wave Feature 11, Provenance Schema | This layer makes the provenance need explicit and gives it an artifact contract. It does not implement the full second-wave schema. |
| Second-wave Feature 12, Context Governance Layer | CGL should eventually decide which acquired materials are eligible as context. This layer defines the packet it will inspect. |
| Features 13-16 | Scorecards, meeting linker, trace_idea, and drift_scan all depend on normalized, provenance-rich acquisition records. |
| Event-triggered workflows | Event triggers should invoke acquisition plans, not raw actions. Event-trigger implementation remains future. |
| Delivery adapters | Delivery receives delivery-ready summary packets or SBP outputs. It does not gather sources itself. |
| Future control-plane integrations | Discord, companion surfaces, n8n, and Paperclip must call into declared acquisition/workflow contracts, not get direct vault/source authority. |

---

## 10. Current Repo-Truth Notes

The baseline truth remains: Phase 7 SIC complete, Phase 8 capture complete, Runtime MCP V1 live, `workflow.invoke_bounded` bounded to `operator_today` and `operator_close_day`, OpenClaw schedule-source sync complete, native ChaseOS cron not built, and MCP scope unchanged.

Pass 1A generic implementation substrate now active:

- `runtime/acquisition/plan.py` defines and validates acquisition plans with objective, requester, downstream target, surfaces, methods, acquirer identity, read/browser/network scope, cadence/trigger, freshness policy, trust policy, output targets, promotion defaults, audit requirements, and declared sources.
- `runtime/acquisition/models.py` defines the first-wave artifact dataclasses: `SourcePacket`, `NormalizedSourcePack`, and `BriefingReadyInputSet`.
- `runtime/acquisition/validators.py` enforces provenance, trust, freshness, transformation-chain, audit, bounded-write, and `canonical_mutation_allowed: false` requirements.
- `runtime/acquisition/adapters/local.py` implements the first conservative adapter, limited to declared vault/log/manual-drop-in local files.
- `runtime/acquisition/builder.py` builds source packets, a normalized source pack, and a briefing-ready input set from a validated plan, and writes only to declared non-canonical pack paths.
- `runtime/acquisition/source_pack_builder.py` remains the AOR-compatible wrapper for the existing workflow surface.
- `runtime/acquisition/fixtures/strikezone_pass1a/` proves the generic path with safe synthetic StrikeZone inputs.
- `runtime/workflows/registry/source_pack_builder.yaml` registers the workflow.
- `06_AGENTS/role-cards/source-pack-builder.yaml` defines its permission envelope.
- Outputs are runtime/log-local only and do not mutate canonical state.

Direct repo inspection additionally shows:

- `runtime/sbp/` generic substrate exists.
- `runtime/workflows/registry/sbp_strikezone_digest.yaml` exists and is `status: active`.
- `runtime/workflows/sbp_strikezone_digest.py` exists as a StrikeZone instance handler.
- `runtime/schedules/sch-sbp-strikezone-digest-0600.yaml` exists and targets OpenClaw.
- `runtime/sbp/delivery_adapters.py` contains a concrete Discord webhook adapter using `DISCORD_WEBHOOK_URL`.
- No build log for SBP Pass 1B was found in `07_LOGS/Build-Logs/` during this pass.

Therefore this architecture treats the current StrikeZone digest publisher as repo-observed implementation surface. The generic Pass 1A substrate is now the first upstream source-pack path; StrikeZone-specific live SBP consumer wiring remains a later pilot pass.

2026-04-27 source-class update: the acquisition substrate now includes a generic source-class registry at `runtime/acquisition/source_classes.py`. The first trading research source classes are `perplexity_digest`, `youtube_summary`, `research_export`, and `grok_digest`. These classes preserve identity in `source_packet.source_class` and BRIS sections while keeping the builder generic and file-read based. This update does not add MCP scope, browser authority, delivery authority, native cron, social crawling, authenticated scraping, exchange/account access, or canonical mutation.

2026-04-27 live-source update: Acquisition Pass 2 + 2B is repo-observed complete in `07_LOGS/Build-Logs/2026-04-27-ChaseOS-Acquisition-Pass2.md`: SQLite artifact store, RSS/web/email/Google adapters, and `run_all_live_acquisitions()` are implemented before the file-read builder boundary. Live runs remain source/credential dependent and are separate from canonical promotion.

2026-04-27 local/import preview update: `runtime/acquisition/research_imports.py` and `chaseos acquisition preview-research --profile strikezone` provide an operator preview path for saved Perplexity digests, YouTube summaries, research exports, and optional Grok digests under `runtime/acquisition/manual/strikezone/`. `runtime/acquisition/plans/strikezone-daily.json` declares those folders as local read scope, while concrete source entries are generated only from actual dropped files. The command is read-only by default; `--write` writes runtime-local preview pack artifacts only and does not update the latest pointer, deliver externally, or promote content.

2026-04-28 local/import metadata enrichment update: the StrikeZone local/import preview path now parses optional operator-supplied frontmatter or JSON metadata for title/display name, declared URL, source event time, captured time, and author/platform notes. These values map into existing generic acquisition source fields and downstream source packet provenance/freshness. The parser stays file-only and does not add browser authority, network access, MCP scope, delivery authority, native cron, canonical mutation, approval state, or trust-tier elevation.

2026-04-27 reviewed-preview promotion update: `chaseos acquisition promote-research-preview --briefing-input <path> --reviewed --profile strikezone` validates a written research preview BRIS and normalized pack before updating `runtime/acquisition/packs/strikezone-latest.json`. The update is limited to the runtime latest pointer and remains outside canonical vault mutation, browser authority, MCP scope, delivery scope, and schedule authority.

2026-04-28 SBP consumption proof update: `chaseos acquisition verify-research-sbp --profile strikezone` verifies that a reviewed research-preview latest pointer is consumable by the existing `sbp_strikezone_digest` `acquisition-pack` input adapter. The command is read-only and stops before synthesis, workflow invoke, delivery, canonical promotion, MCP changes, browser authority changes, or schedule changes. `--allow-non-preview` can verify adapter consumption of the current latest pointer without requiring reviewed-preview provenance.

2026-04-28 research readiness status update: `chaseos acquisition research-status --profile strikezone` gives a read-only operator status surface for the local/import research lane. It counts declared source-class files, reports latest-pointer provenance, verifies current-pointer SBP consumability, reports whether default reviewed-preview verification is ready, and returns next actions without writing artifacts or expanding authority.

2026-04-28 operator setup update: the StrikeZone manual import lane now has an operator setup guide and safe source templates under `runtime/acquisition/manual/strikezone/`. `research-status` also reports recommended source-class coverage so the operator can see whether `perplexity_digest`, `youtube_summary`, and `research_export` are present before previewing or promoting a pack. This remains a local/import setup surface only.

2026-04-29 Phase 10A0 testing handover: the local/import acquisition lane is mature enough that the next blocker is operator UX and live-file proof, not more architecture. `06_AGENTS/Phase10A0-Live-Proof-Test-Handover.md` defines the Studio Acquisition Intake Cockpit as the next narrow UI foothold. The UI should wrap existing readiness/preview/promotion/SBP-verification commands and must not add browser, MCP, delivery, cron, provider-call, or canonical writeback authority. Final reviewed proof still requires real local research files.

---

## 11. Implementation Boundary For This Pass

This layer remains bounded. The current Pass 1A implementation does not:

- implement new MCP surfaces
- broaden `draft_execution`
- build a giant browser agent
- add native ChaseOS cron
- add event-trigger execution
- deploy n8n
- mutate canonical state through acquisition
- auto-promote any content
- make StrikeZone the whole feature family

---

## Related Documents

| Document | Purpose |
|---|---|
| `06_AGENTS/Acquisition-Surface-Map.md` | Source and method classification |
| `06_AGENTS/Normalization-Provenance-Contract.md` | Artifact model and provenance/trust contract |
| `06_AGENTS/Runtime-Acquisition-Responsibility-Matrix.md` | Runtime responsibility split |
| `06_AGENTS/StrikeZone-Acquisition-Normalization-Pilot.md` | First pilot contract |
| `06_AGENTS/SIC-Architecture.md` | Retrieval/source intelligence layer |
| `06_AGENTS/Connector-Capture-Architecture.md` | Quarantine intake layer |
| `06_AGENTS/Autonomous-Operator-Runtime.md` | Runtime execution governance |
| `06_AGENTS/Scheduled-Briefing-Pipelines.md` | Briefing pipeline consumer |
| `06_AGENTS/Browser-Operator-Surface.md` | Browser acquisition method |
| `04_SOPS/Untrusted-Input-Handling-SOP.md` | Raw input handling |
| `04_SOPS/Credential-Boundaries-SOP.md` | Credential safety |

*Graph links: [[Vault-Map]] · [[SIC-Architecture]] [[Connector-Capture-Architecture]] [[Autonomous-Operator-Runtime]] [[Scheduled-Briefing-Pipelines]] [[Browser-Operator-Surface]] [[Runtime-Navigation-Map]] [[Agent-Memory-Architecture]] [[Trust-Tiers]] [[Permission-Matrix]] [[Feature-Register]]*

*Acquisition-Normalization-Layer.md - v1.7 | Created: 2026-04-23 | Updated: 2026-04-29 | Phase 9 Acquisition + Normalization Architecture + Pass 1A-1D substrate + Pass 2/2B live-source adapters + local/import preview, metadata enrichment, operator setup, reviewed latest-pointer promotion path, and Phase 10A0 live-file testing handover*
