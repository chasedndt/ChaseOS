---
date: 2026-05-21
runtime: Codex
session_descriptor: feature-family-subfeature-inventory
type: canonical-feature-inventory
status: OPERATOR CONFIRMATION REQUIRED / REGISTER-SUPPLEMENT / NO RUNTIME AUTHORITY CHANGE
scope: feature families, subfeatures, mini-features, Studio product surfaces, recent implementation logs
authority: documentation normalization only
---

# ChaseOS Feature Family And Subfeature Inventory

## Purpose

This is the expanded feature inventory that sits below `[[Feature-Register]]` and beside `[[Feature-Fit-Register]]`.

The Feature Register names the major feature families. This file names the repo-observed features, subfeatures, mini-features, UI surfaces, approval lanes, runtime proof lanes, and planning seeds that currently belong under those families.

Use this file as the operator-confirmation source before updating `README.md`, `PROJECT_FOUNDATION.md`, guides, Studio navbar architecture, or dashboard/home copy.

## Audit Inputs

Repo-observed inputs used for this inventory:

- `06_AGENTS/Feature-Register.md`
- `06_AGENTS/Feature-Fit-Register.md`
- `06_AGENTS/Studio-Product-UI-Feature-Family-Normalization.md`
- `docs/features/*.md`
- `docs/features/-Upcoming-Features-Index.md`
- `subagents/README.md`
- `runtime/studio/shell/panel_registry.py`
- recent `07_LOGS/Build-Logs/` and `99_ARCHIVE/Documentation-History/` entries through 2026-05-21
- current Studio panel count from the prior normalization pass: 39 declared panels, 38 mounted panels, 1 readiness-only panel

## Status Rules

- `COMPLETE` means the scoped local feature has implementation and verification evidence.
- `PARTIAL` means some implementation exists but key product/runtime paths remain gated or unbuilt.
- `PLANNED` means an architecture/spec/seed exists without implementation evidence.
- `REFERENCE` means the repo keeps the feature as study material or extraction material, not active product scope.
- `DEFERRED` means deliberately not in current MVP execution scope.
- `UNKNOWN` means no repo evidence was found in this pass.

## Inventory Boundary

This file does not create new runtime authority, approval authority, graph write authority, memory write authority, provider authority, browser authority, release authority, external delivery authority, or canonical promotion authority.

It also does not collapse page labels into feature families. `Home`, `Missions`, `Extensions`, `Personal Memory`, `Logs / Audit`, and `QA / Proof` remain product or governance surfaces unless promoted through the register.

---

## 1. Source Intelligence Core

**Parent register row:** Source Intelligence Core (SIC)  
**Canonical nodes:** `[[Source-Intelligence-Core]]`, `[[SIC-Architecture]]`  
**Overall status:** COMPLETE for local SIC passes; future provider/provenance expansion remains.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Source Package Layer | COMPLETE | Normalized internal representation for promoted sources. |
| Workspace / Notebook Layer | COMPLETE | Grouped source sets around topic/project workspaces. |
| Retrieval / Evidence Layer | COMPLETE | Chunk/embed/query/citation workflow. |
| Output Generation Layer | COMPLETE | Structured summary/FAQ/synthesis/briefing style outputs. |
| Provider Adapter Layer | COMPLETE / PARTIAL | Local/stub and specific provider adapters exist; production provider breadth remains gated. |
| Source package builder | COMPLETE | Pass 2 implementation evidence. |
| Workspace manager | COMPLETE | Create/load/add/remove source packages. |
| Embedding backends | COMPLETE | Local stub/word and OpenAI opt-in backend paths recorded. |
| Index manager | COMPLETE | Workspace-local embedding indexes. |
| Retrieval + similarity | COMPLETE | `query_workspace()` cosine similarity with status codes. |
| Output store | COMPLETE | Workspace-local persisted generation. |
| Benchmark utility | COMPLETE | Embedding/backend evaluation utility. |
| SIC to Capture provenance link | FUTURE | Capture provenance link remains future. |
| Semantic hint validation | FUTURE | Sidecar hints currently advisory. |
| Cross-workspace retrieval | FUTURE | Multi-workspace permission boundary unresolved. |
| Additional real provider adapters | FUTURE | Requires credential-boundary audit per adapter. |
| Studio Research Collections panel | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | Product label for SIC collections; source-render QA verified desktop/mobile rendering and collection right-inspector selection 2026-05-24. No ingestion, extraction, graph promotion, or canonical writeback authority. |

---

## 2. Connector / Capture Automation And Visual Capture Markdown

**Parent register row:** Phase 8 Connector / Capture layer, Acquisition + Normalization Layer  
**Canonical nodes:** `[[Connector-Capture-Architecture]]`, `[[Acquisition-Normalization-Layer]]`, `[[Visual-Capture-Markdown-Ingestion-Feature]]`  
**Overall status:** Capture automation COMPLETE for early connectors; Visual Capture Markdown PARTIAL with Pass 14 local write executor verified and downstream dispatch blocked.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| `ContentPacket` | COMPLETE | Connector-agnostic content container. |
| Router + naming | COMPLETE | Type-first organization and deterministic naming. |
| Intake writer + `.meta.json` sidecar | COMPLETE | UUID4/SHA-256 sidecar discipline. |
| CLI capture from file/stdin | COMPLETE | `chaseos capture file/stdin`. |
| Operator CLI aliases | COMPLETE | `chaseos` / `chase` console surfaces. |
| Semantic breadcrumbs | COMPLETE | Domain/project/topic hints are advisory only. |
| RSS/Atom connector | COMPLETE | Public feed capture. |
| SHA-256 dedup registry | COMPLETE | First-capture-wins registry. |
| Browser/HTML connector | COMPLETE | Local HTML to Markdown path. |
| Perplexity connector | COMPLETE | API-key gated; no key written. |
| Watched-folder automation | COMPLETE | Polling path; no daemon. |
| Grok/xAI connector | COMPLETE | API-key gated. |
| Additional API connectors | FUTURE | Claude/OpenAI/Gemini/etc. |
| Recursive watched-folder scanning | FUTURE | Deeper-path blast-radius issue. |
| Watched-folder per-extension overrides | FUTURE | Planned lower-risk enhancement. |
| Live URL browser capture | FUTURE | Network/ToS/robots boundary. |
| Watched-folder daemon / OS service | FUTURE / Phase 9 | AOR scheduler/runtime concern. |
| Connector plugin system | FUTURE / Phase 9 | AOR extensibility concern. |
| Visual Capture Markdown Ingestion | PARTIAL | Product-facing feature: Capture to Markdown. |
| Explicit user-triggered visual capture | PARTIAL | Feature spec exists; fixture/static flows verified; live active-tab/screenshot capture remains deferred. |
| DOM/text/accessibility-first extraction | PARTIAL | Design rule recorded; full live captor breadth remains unverified. |
| Screenshot/OCR fallback | PLANNED / DEFERRED | OCR and real live screenshot capture remain unverified. |
| Raw Markdown capture artifact | PARTIAL / VERIFIED | Quarantine/raw capture path exists. |
| Capture metadata and provenance sidecars | PARTIAL / VERIFIED | `.meta.json` and visual capture packet lanes exist. |
| Review-state writer | PARTIAL / VERIFIED | Reviewed raw capture can be represented for downstream gates. |
| Attachment disposition policy | PARTIAL / VERIFIED | Pass 11 packaged Studio visual QA and policy evidence exists. |
| Acquisition bridge preview | PARTIAL / VERIFIED | Reviewed capture to source packet / normalized pack / briefing input previews. |
| Downstream gate readiness | PARTIAL / VERIFIED | Gate readiness exists; execution remains blocked. |
| Source-pack write approval preview | PARTIAL / VERIFIED | Pass 13 UI/API/read-only preview verified. |
| Approved source-pack write executor | PARTIAL / VERIFIED | Pass 14 writes create-only source-pack JSON with exact digest/operator statement and exact-once marker. |
| Source-pack AOR dispatch readiness preview | CODE-OBSERVED / LOG EVIDENCE REQUIRED | `panel_registry.py` reports readiness/UI/read-only flags and source contract includes `visual_capture_source_pack_aor_dispatch_readiness`; no dedicated Pass 15 build/history log was confirmed in this reconciliation. |
| Approval artifact queue/write executor | NOT BUILT | Explicitly deferred after Pass 14. |
| AOR dispatch executor from VCMI source pack | NOT BUILT | Registry explicitly keeps reviewed-capture AOR dispatch executor blocked. |
| SIC ingestion from VCMI source pack | NOT BUILT | Explicitly deferred after Pass 14. |
| Graph/canonical promotion from VCMI | NOT BUILT | Explicitly deferred after Pass 14. |
| Studio Capture panel | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | Product-facing Capture surface source-render verified across desktop/mobile 2026-05-24. Recent-capture empty state is valid; review, source-pack, AOR dispatch, SIC ingestion, graph, and canonical promotion lanes remain governed downstream. |

Pass-by-pass verified VCMI scope:

- Passes 1-4: core contract, quarantine writer, Studio panel, CLI/operator docs.
- Pass 5: Acquisition/AOR review bridge preview only.
- Pass 6: controlled browser/webview extraction within bounded local capture rules.
- Passes 7/7b/7c: screenshot/OCR fallback design, attachment quarantine-copy policy, retention/review policy; OCR and live pixel capture remain unverified.
- Passes 8-11: external surface deferral, review-state machine, packaged clickthrough/review UI, visual QA and attachment disposition policy.
- Passes 12-14: downstream gate readiness, source-pack approval preview UI, exact-digest approved source-pack write executor.

No VCMI row in this inventory authorizes AOR dispatch execution, Agent Bus enqueue, SIC ingestion, graph/canonical promotion, hotkey overlay, Discord/external capture, ambient clipboard, active-window/screen capture, active-tab capture, or accessibility-tree capture.

---

## 3. Acquisition + Normalization Layer

**Parent register row:** Acquisition + Normalization Layer  
**Canonical node:** `[[Acquisition-Normalization-Layer]]`  
**Overall status:** PASS 1A substrate live; broader artifact families future.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Acquisition plans | PARTIAL / VERIFIED | Declared source acquisition plans. |
| Source surface classification | PARTIAL / VERIFIED | Local/import/source method classification. |
| Local declared-source reads | PARTIAL / VERIFIED | No ambient source access. |
| `source_packet` output | PARTIAL / VERIFIED | Generated by Pass 1A substrate and VCMI bridge lanes. |
| `normalized_source_pack` output | PARTIAL / VERIFIED | Generated by Pass 1A substrate and preview lanes. |
| `briefing_ready_input_set` output | PARTIAL / VERIFIED | Generated by Pass 1A substrate. |
| Evidence bundle | FUTURE | Named in architecture; not broad built lane. |
| Action packet | FUTURE | Named in architecture; not broad built lane. |
| Memory candidate packet | FUTURE | Named in architecture; must remain gated. |
| Provenance/trust/freshness contracts | PARTIAL | Architecture and preview evidence; full product workflow not complete. |
| Studio Intake panel | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | Product-facing Intake surface source-render verified across desktop/mobile 2026-05-24 with quarantine item right-inspector selection. Promotion and canonical write remain approval-gated or unmounted. |
| Studio Sources panel | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | Product-facing Sources surface source-render verified across desktop/mobile 2026-05-24 with source/run right-inspector selection. External acquisition and workflow execution remain unmounted. |
| Studio Provenance panel | PARTIAL PRODUCT UI | Cross-links graph/provenance/source evidence. |

---

## 4. Autonomous Operator Runtime And Runtime Governance

**Parent register row:** Autonomous Operator Runtime (AOR)  
**Canonical node:** `[[Autonomous-Operator-Runtime]]`  
**Overall status:** PARTIAL LIVE; core 8-stage runtime path active with bounded workflow evidence.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| AOR 8-stage runtime engine | PARTIAL LIVE | `runtime/aor/engine.py` path recorded. |
| Workflow manifests | PARTIAL LIVE | Manifest-based bounded execution. |
| Workflow Registry | PARTIAL LIVE | Studio and CLI proof/debug surfaces exist. |
| Agent Role Cards | PARTIAL LIVE | Role-card inspection/gating surfaces exist. |
| Task-Type Router | PARTIAL LIVE | Routes tasks to declared handlers/workflows. |
| Decision Ledger | PARTIAL | Decision history/governance surface. |
| Feature Filter | PARTIAL | Studio feature audit/debug surface. |
| Pivot Log | PARTIAL | Governance decision/pivot tracking. |
| Runtime policy binding | PARTIAL LIVE | Unknown/draft workflows fail closed. |
| Concurrent load enforcement | PARTIAL LIVE | Recorded in AOR status. |
| Priority ceiling | PARTIAL LIVE | Recorded in AOR status. |
| Runtime-instance promotion readiness | PARTIAL / BLOCKED | OpenClaw/Hermes draft substrate; no canonical promotion authority. |
| Multi-repo / multi-directory policy | DEFERRED | Policy node exists; broad enforcement/use deferred. |
| Audit trail persistence | FUNCTIONAL | Current path under `07_LOGS/Agent-Activity`; formal `runtime/audit/` migration deferred. |
| Execution Repair Memory | SEEDED | `runtime/memory/repair/` inspector foothold. |
| Runtime Navigation Map | SEEDED | `runtime/memory/nav/` plus profile docs. |
| Agent Identity Ledger | SEEDED | Adapter identity files and inspector visibility. |
| Agent Bus / coordination bus | PARTIAL LIVE | Bus surfaces, task packets, worker integration, and diagnostics exist. |
| Codex bus adapter / daemon | PARTIAL LIVE | Codex worker integration and daemon readiness/logs exist; bounded worker, not core owner. |
| Hermes/OpenClaw coordination watch | PARTIAL LIVE | Runtime startup/watch/handoff evidence exists. |
| Runtime provider governance layer | PARTIAL | Config, probe, approval, and status lanes exist; live provider calls remain gated. |
| Runtime startup surfaces | PARTIAL | Startup/autostart approval surfaces exist. |
| Runtime Cockpit | PARTIAL PRODUCT UI | Startup/runtime status/action readiness, no broad execution authority. |
| AOR Executions / Task History | PARTIAL PRODUCT UI | Product label should be task history, not implementation acronym. |
| Runtime Support Loops | PARTIAL | OSRIL support/wait/resume visibility. |
| App Launcher | PARTIAL / ADVANCED | Utility surface; not a top-level MVP feature family. |

---

## 5. Scheduled Briefing Pipelines

**Parent register row:** Scheduled Briefing Pipelines (SBP)  
**Canonical node:** `[[Scheduled-Briefing-Pipelines]]`  
**Overall status:** Generic substrate live; specific instances partial.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Trigger schedules | PARTIAL LIVE | Schedule intent store and named schedules exist. |
| Input adapters | PARTIAL | SIC/vault/external/raw digest patterns recorded. |
| Execution adapters | PARTIAL | Runtime-bound execution under AOR. |
| Writeback targets | PARTIAL | Logs/project OS/writeback targets remain gated. |
| Delivery adapters | PARTIAL | Discord/Whop/email/Slack/internal model recorded; live breadth gated. |
| Guardrail profiles | PARTIAL | Permission ceiling/fail/HITL model recorded. |
| StrikeZone Market Digest Publisher | PARTIAL LIVE | Daily digest instance evidence exists. |
| Schedule intent writer | PARTIAL | Chat/schedule intent lanes exist. |
| Schedule activation readiness | PARTIAL | Readiness and manual UI test closeout evidence exists. |
| Native OS scheduler bridge | PARTIAL | OpenClaw bridge contract; ChaseOS-native cron runner not fully built. |
| Studio Schedules panel | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | Product schedule operating context, readiness, feature-family coverage, read-only intent cards/detail, and right-inspector selection verified 2026-05-24. No enable/disable, cron mutation, runtime dispatch, Agent Bus write, approval consumption, or external delivery authority. |
| Pulse scheduled proof panel | PARTIAL PRODUCT UI | Pulse-specific schedule proof surface. |

---

## 6. Model Context Protocol Integration

**Parent register row:** Model Context Protocol (MCP) Integration  
**Canonical nodes:** `[[ChaseOS-MCP-Server]]`, `[[ChaseOS-MCP-Module-Design]]`  
**Overall status:** V1 stdio scaffold live; broader deployment gated.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| MCP stdio server scaffold | PARTIAL LIVE | JSON-RPC 2.0 V1. |
| Scoped resources/tools/prompts | PARTIAL LIVE | Guarded MCP surfaces. |
| `workflow.invoke_bounded` | PARTIAL LIVE | V2 bounded invocation surface. |
| MCP compatibility wrapper | PARTIAL LIVE | Stdio compatibility evidence. |
| MCP hardening | PARTIAL | Pass 5A hardening recorded. |
| N8N/MCP proof artifacts | PARTIAL / GATED | Proof/readiness only; no broad deployment claim. |
| External MCP deployment | NOT BUILT | No live OpenAI/external MCP deployment claim. |

---

## 7. Interface / Experience Layer And ChaseOS Studio

**Parent register row:** Interface / Experience Layer  
**Canonical node:** `[[ChaseOS-Studio-Architecture]]`  
**Overall status:** PARTIAL; native shell active, final product UI cleanup not complete.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Native Studio shell | PARTIAL LIVE | Desktop shell/PyWebView packaging path exists. |
| Packaged `.exe` build | PARTIAL / VERIFIED ELSEWHERE | Working executable exists; UI cleanup still required. |
| Studio Dashboard / Home | PARTIAL / NEEDS REWRITE | Current dashboard shows implementation/release status, not real user home. |
| Sidebar/nav grouping | PARTIAL / OPERATOR CONFIRMATION REQUIRED | Headers retained: Main, Knowledge Graph, Content, Runtime, Personal Memory, Governance. |
| Studio product UI finalization handover | COMPLETE DOC | `[[Finalize-ChaseOS-Studio-Product-UI-Handover]]`. |
| Studio panel feature-family normalization | COMPLETE DOC | `[[Studio-Product-UI-Feature-Family-Normalization]]`. |
| Graph View | PARTIAL PRODUCT UI | Primary graph surface. |
| Node Inspector | PARTIAL PRODUCT UI | Needs product cleanup. |
| Graph Hygiene | PARTIAL PRODUCT UI | Review/maintenance surface. |
| Provenance Explorer | PARTIAL PRODUCT UI | Should be user-facing Provenance. |
| Workspace Entry / Workspace Setup | PARTIAL | Open-folder/vault detection/bootstrap readiness. |
| Open Folder compatibility readiness | PARTIAL / READ-ONLY | No folder mutation. |
| Obsidian vault detection | PARTIAL / READ-ONLY | No `.obsidian` writes. |
| General Markdown inference preview | PARTIAL / READ-ONLY | Read-only inference path. |
| Workspace bootstrap preview | PARTIAL | Upgrade/migration still gated. |
| Proof-temp workspace upgrade approval/execution | PARTIAL / GATED | Proof-temp only. |
| Settings | PARTIAL PRODUCT UI | Read-only/config-safe posture. |
| Approval Center | PARTIAL PRODUCT UI | Aggregator/readiness surfaces; approval execution remains lane-specific. |
| QA / Proof | PARTIAL / ADVANCED | Evidence/debug surface. |
| Logs / Audit | PARTIAL PRODUCT UI | Build log/audit visibility. |
| Feature Audit | PARTIAL / ADVANCED | Feature filter/register debug surface. |
| App Launcher | PARTIAL / ADVANCED | Hidden/advanced until productized. |
| Installer build approval lane | PARTIAL / GATED | Installer build approval artifacts/markers exist. |
| Code signing approval lane | PARTIAL / GATED | Signing approval artifacts/markers exist. |
| Startup/autostart approval lane | PARTIAL / GATED | Host mutation approval lane exists. |
| Release promotion approval lane | PARTIAL / GATED | Release promotion approval lane exists. |

---

## 8. Graph / Knowledge Graph / Graph Intelligence

**Parent rows:** Interface / Experience Layer, AOR, Acquisition  
**Canonical nodes:** `[[Graph-Substrate-Architecture]]`, `[[ChaseOS-Studio-Architecture]]`  
**Overall status:** PARTIAL; graph substrate exists, persisted graph storage deferred.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| GraphSnapshot | PARTIAL | Graph representation substrate. |
| GraphIndex | PARTIAL | Index structure substrate. |
| Deterministic extractors | PARTIAL | Parser/extractor lanes. |
| Topology reports | PARTIAL | Graph report/hygiene surfaces. |
| Typed graph overlays | PARTIAL | Studio graph implementation path. |
| Trust/provenance overlays | PARTIAL | Governance display path. |
| Graph provenance inspector | PARTIAL | Provenance Explorer/Node Inspector linkage. |
| Approval-gated node create/edit | PARTIAL / GATED | No ambient graph mutation. |
| Approval-gated visual link proposals | PARTIAL / GATED | Proposal path, not automatic mutation. |
| Graph hygiene review | PARTIAL | Loose/duplicate node review lanes. |
| Graph hygiene decision draft/executor | PARTIAL / GATED | Requires approval/decision discipline. |
| Persisted graph storage | DEFERRED | Explicitly still architecture-scope required. |
| Knowledge Boxes | PLANNED PRODUCT ABSTRACTION | Not built as a feature family yet. |

---

## 9. Phase 11 Chat / Conversational Command Center

**Parent rows:** Interface / Experience, OSRIL, Agent Memory, AOR  
**Canonical node:** `[[ChaseOS-Phase11-Architecture]]`  
**Overall status:** PARTIAL; many read-only previews and gated executors, no unrestricted chat authority.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Command Router | PLANNED / PARTIAL | Phase 11 row exists; specific UI/preview lanes implemented. |
| Autogenesis Engine | PLANNED | No broad implementation claim. |
| Workspace Context UX | PARTIAL | Workspace-mode and context proposals/deeplinks exist. |
| Multi-Model Provider Router | PARTIAL / GATED | Provider-agnostic routing architecture; live calls gated. |
| Runtime Control Surface | PARTIAL / GATED | Runtime/browser dispatch readiness and executors are gated. |
| Browser-Use Integration | PARTIAL / GATED | Readiness/proof lanes only. |
| Agent Companion System | PARTIAL | Runtime-linked companions; no authority expansion. |
| Slash Commands | PARTIAL | UI/catalog/audit lanes. |
| Operator Dashboard + Config | PARTIAL | Aggregate/audit/config surfaces. |
| Memory Save/Search | PARTIAL / GATED | Companion memory and personal/context lanes. |
| R&D Entry System | PLANNED / GATED | No direct truth-state mutation. |
| Chat panel read-only shell | PARTIAL | Product UI exists; needs copy cleanup. |
| Approval handoff queue | PARTIAL | Queue preview/write proof lanes exist. |
| Conversation persistence approval contract | PARTIAL / GATED | Preview/proof only; no broad ambient write. |
| Chat approval queue write proof | PARTIAL / VERIFIED | Pending approval artifacts can be written in specific lanes. |
| Live provider approval preview | PARTIAL / GATED | No provider call. |
| Runtime/browser dispatch readiness | PARTIAL / GATED | Readiness contracts only in early passes. |
| Approval consumption readiness | PARTIAL | Specific executor/readiness lanes. |
| No-HITL read-only card/card catalog | PARTIAL / VERIFIED | Read-only card QA and catalog audit. |
| Operator-action-required gate | PARTIAL | Gate model recorded. |
| Companion selection approval preview/executor | PARTIAL / GATED | Selection proof lanes; no authority expansion. |
| Runtime dispatch executor | PARTIAL / GATED | Evidence paths exist; no broad runtime authority. |
| Companion memory boundary | COMPLETE CONTRACT | Separate governed namespaces for Hermes/OpenClaw/Chaser Agent. |
| Companion memory approval preview | PARTIAL / VERIFIED | Digest-gated pending approval. |
| Companion memory proof execution | PARTIAL / VERIFIED | Proof-only exact-once path. |
| Companion memory ledger write | PARTIAL / VERIFIED | One real Hermes raw/non-canonical ledger entry after explicit approval. |
| Companion memory read model | PARTIAL / VERIFIED | Read-only readback/search/model. |
| Companion memory context readiness | PARTIAL / VERIFIED | Bounded context packet; no provider delivery. |
| Chat Adapter Selector + Daemon Control | PARTIAL | Product/runtime control surface exists; must stay gated. |
| Fake runtime harness | PARTIAL | Test/dry-run support. |
| Live E2E probe / round trip | PARTIAL / VERIFIED | 2026-05-18 live E2E evidence plus registry flags for bus write and runtime ack; still not broad chat autonomy. |
| Runtime dispatch verification | PARTIAL / VERIFIED | 2026-05-18 verification surface; approved dispatch lanes remain bounded. |
| Production operator dispatch readiness | PARTIAL / VERIFIED | 2026-05-19 readiness chain; no broad runtime claim/result canonical writeback. |
| Live daemon integration test | PARTIAL / VERIFIED | 2026-05-19 read-only integration readiness with operator-gated live probe path. |
| Studio EXE packaging/product hardening/live activation/vault health | PARTIAL / VERIFIED | 2026-05-19 Studio readiness chain; release-grade installer/signing/startup/release promotion remain separate gated lanes. |

---

## 10. Agent Memory / Personal Memory / Personal Context

**Parent register row:** Agent Memory Architecture  
**Canonical nodes:** `[[Agent-Memory-Architecture]]`, `[[Personal-Context-Import-Feature]]`  
**Overall status:** PARTIAL; Layer A/B active, product surfaces and governed memory lanes partial.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Layer A Shared System Doctrine | ACTIVE | Rules, Gate, taxonomy, permission docs. |
| Layer B User-Specific Operating Memory | ACTIVE / PARTIAL | Goals/preferences/cadences in docs/logs. |
| Layer C Runtime-Specific Memory | SEEDED / PARTIAL | Runtime profiles, identity ledgers, repair/nav memory. |
| Layer D Workspace/Task-Local Memory | PARTIAL | Run/workspace local state. |
| Layer E Execution-History/Audit Memory | ACTIVE | Logs/Agent Activity. |
| Agent Identity Ledger | SEEDED | Runtime identity baselines and inspector visibility. |
| Execution Repair Memory | SEEDED | Runtime repair pattern foothold. |
| Runtime Memory Inspector | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | Product-facing Memory Manager surface source-render verified across desktop/mobile 2026-05-24 with runtime memory right-inspector selection. Runtime brain/profile writes remain governed elsewhere. |
| Memory Ledger | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | Product-facing Memory Ledger surface source-render verified across desktop/mobile 2026-05-24 with runtime/task right-inspector selection. Memory mutation and canonical promotion remain governed elsewhere. |
| Studio Context Import panel | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | Product-facing Context Import surface source-render verified across desktop/mobile 2026-05-24. Runtime refs are references-only; Personal Map apply and canonical promotion remain governed. |
| Personal Context Import planner | PARTIAL | Planning/preview lanes exist. |
| Personal Context approved preview execution | PARTIAL / GATED | Approval-gated proof lanes. |
| Canonical promotion approved executor | PARTIAL / GATED | Must not imply ambient canonical memory mutation. |
| Multi-instance fixture harness | PARTIAL | Test support for context import. |
| Full CLI/API/panel/contract surface wiring | PARTIAL / VERIFIED | 2026-05-18 full-surface wiring across 14 commands and four surfaces. |
| Runtime consumption/reference readiness | PARTIAL / VERIFIED | Readiness/reference packet lanes exist; no runtime dispatch. |
| Agent Bus dispatch packet | CODE-OBSERVED / LOG EVIDENCE REQUIRED | Studio registry flag exists; matching dedicated build-history evidence was not fully confirmed in this pass. |
| Provider credential/execution proof | CODE-OBSERVED / LOG EVIDENCE REQUIRED | Registry flags exist; do not claim provider/model calls are available. |
| Runtime memory mutation readiness/executor | CODE-OBSERVED / LOG EVIDENCE REQUIRED | Registry flags exist; live writes remain blocked/gated. |
| Personal Map apply readiness/executor | CODE-OBSERVED / LOG EVIDENCE REQUIRED | Registry flags exist; graph writes remain gated. |
| Placeholder cleanup | PARTIAL | Recorded cleanup surfaces. |
| Personal life-domain nodes | PARTIAL | Exists as governed personal-map related layer. |
| Raw/route block boundaries | PARTIAL | Boundary docs/proofs exist. |
| Personal Map mutation | GATED / NOT AMBIENT | No direct mutation by this inventory. |
| Companion memory | PARTIAL / GATED | See Phase 11 companion memory rows. |

---

## 11. ChaseOS Pulse

**Parent register row:** ChaseOS Pulse  
**Canonical node:** `[[ChaseOS-Pulse-Architecture]]`  
**Overall status:** Current V1 local lane complete; broader product partial.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Pulse card schemas | COMPLETE LOCAL | Card/deck schemas exist. CLI contract shows 42 Pulse commands. |
| Local Pulse surface | COMPLETE LOCAL / PARTIAL PRODUCT | Studio/product surfaces exist; 2026-05-04 local v1 product-grade lane closed. |
| Feedback candidates | PARTIAL | Candidate persistence lanes. |
| Feedback review queue | PARTIAL | Review queue surface. |
| Agent Bus enqueue design/approval | PARTIAL / GATED | Enqueue remains approval-gated. |
| Schedule activation gate/request | PARTIAL / GATED | Schedule proof/activation lanes. |
| Run queue/audit proof | PARTIAL | Evidence lanes. |
| Supervised activation execution proof | PARTIAL / GATED | No broad autonomous authority. |
| Pulse schedule proof panel | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | Product-facing Proactive Briefings surface source-render verified across desktop/mobile 2026-05-24 with proof/control right-inspector selection. Schedule activation, queue writes, supervised execution, and trigger actions remain gated or unmounted. |
| Pulse enqueue panel | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | Product-facing Review Queue surface source-render verified across desktop/mobile 2026-05-24 with preflight/request/command right-inspector selection. Agent Bus task writes, claims, dispatch, and approval consumption remain unmounted. |
| Review-response ingest | PARTIAL | Feedback loop path. |
| Feedback-signal apply | PARTIAL / GATED | Application remains gated. |
| Post-apply truth audit | PARTIAL | Audit path. |
| R&D sync | PARTIAL / GATED | Must remain evidence-backed. |
| Pulse Deck app | PARTIAL | Product shell/app path. |
| Personal Memory Manager spec | PARTIAL | Related personal memory product layer. |
| Runtime brain visual UI | PARTIAL / PLANNED | Product surface seed. |
| Connector/source scanner proof chain | PARTIAL / GATED | Local preview, candidate cards, live approved proof, and live execution proof logs exist; live connector execution remains approval-scoped, not ambient. |
| Native schedule proof chain | PARTIAL / GATED | Activation gate, runner proof, run queue audit proof, runtime dispatch proof, supervised activation proof, and schedule proof shell logs exist; broad schedule activation remains governed. |

---

## 12. VentureOps / Missions / Workflow Packs / Founder Mode

**Parent register row:** ChaseOS VentureOps  
**Canonical nodes:** `[[VentureOps-Architecture]]`, `[[Workflow-Pack-Standard]]`, `[[Product-Workflow-Packs-Feature]]`  
**Overall status:** PARTIAL; local workflow-pack lanes verified, external/revenue/client execution remains blocked.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| VentureOps Architecture | PARTIAL | Business/application layer over AOR/SIC/MCP/Studio/Gate. |
| Mission Mode | PARTIAL | Governed long-goal layer above workflow packs. |
| Instance Intelligence | PARTIAL | Instance profiling/recommendation paths. |
| Workflow Recommendation Engine | PARTIAL | Deterministic helper/proof paths. |
| Revenue Workflow Registry | PARTIAL / GATED | No payment/CRM mutation. |
| Workflow Pack Standard | PARTIAL | Pack manifest/proof/scorecard standard. |
| Workflow Exchange Readiness | PARTIAL / GATED | Local preview only; no marketplace publication. |
| Proof artifacts / proof cards | PARTIAL | Local artifacts and proof cards verified in packs. |
| Scorecards | PARTIAL | Workflow/proof scorecard outputs. |
| Adapter Use Matrix | PARTIAL | Runtime/provider/tool use matrix. |
| Founder Mode / AI Builder Mode | PARTIAL DOC | Product mode and startup-validation mission spec. |
| Startup Validation & Launch | PARTIAL DOC | Mission spec; no live external execution. |
| AI Runtime Security Audit | PARTIAL / LOCAL PROOF | Bounded internal/local workflow; no real external send/payment/CRM. |
| Visual Product & Creative Studio pack | PARTIAL / VERIFIED LOCAL | Product-facing workflow pack. |
| Founder / Personal Automation Audit pack | PARTIAL / VERIFIED LOCAL | Product-facing workflow pack. |
| Research-to-Product Intelligence Engine pack | PARTIAL / VERIFIED LOCAL | Manual source intake, evidence/claim packet, scorecard, decision matrix, implementation/content briefs, R&D-style export, proof card, Studio API/UI. |
| Safe Agent Runtime Governance Kit pack | PARTIAL / VERIFIED LOCAL | `runtime/workflow_packs/agent_governance.py`, Studio registry readiness, and 2026-05-20 Agent Governance Kit MVP log exist. |
| Approval resume contract | PARTIAL / VERIFIED LOCAL | Product Workflow Packs approval/resume contract preview exists. |
| Approval review artifact writer | PARTIAL / VERIFIED LOCAL | Scoped review artifact writer exists. |
| Approval consumption dry-run | PARTIAL / VERIFIED LOCAL | Read-only approval-consumption validation exists. |
| Exact-once marker reservation | PARTIAL / VERIFIED | Product Workflow Packs approval marker reservation lane exists. |
| Approved local resume executor | PARTIAL / VERIFIED LOCAL | 2026-05-21 100-percent local approval resume evidence; one-gate/run local resume only. |
| Local resume / approval resume UI | PARTIAL / VERIFIED LOCAL | Product Workflow Packs local resume UI chain and packaged Studio clickthrough evidence. |
| External connectors/source fetching | NOT BUILT | No scraping/GitHub API/repo cloning in Research MVP. |
| Agent Bus/runtime execution from packs | NOT BUILT / GATED | Explicitly not built in Research MVP. |
| Graph/canonical/R&D workbook mutation | NOT BUILT / GATED | Explicitly not built in Research MVP. |
| Workflow Packs Studio panel / Missions UI | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | Product-facing Missions surface now exposes operating context, readiness, feature-family coverage, mission pack cards, local runs, review queue, proof cards, and right-inspector selection. Source-render visual QA verified 2026-05-24. No workflow execution, provider/model call, browser action, runtime dispatch, Agent Bus task write, approval consumption, graph/canonical mutation, or external delivery authority. |

---

## 13. SiteOps / Browser Runtime Skill Memory / Browser Proofs

**Parent register row:** ChaseOS SiteOps / Browser Runtime Skill Memory  
**Canonical nodes:** `[[ChaseOS-SiteOps]]`, `[[Browser-Runtime-Skill-Memory]]`  
**Overall status:** PARTIAL; bounded MVP and safe-local proofs, no broad browser authority.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| SiteOps Website Workflow Index | PARTIAL | Catalog/tenant/install/provider/credential-ref scaffold. |
| Browser Runtime Skill Memory | PARTIAL / VERIFIED LOCAL | Turns browser run evidence into candidate skill memory. |
| Browser run logging | PARTIAL | Browser Run and Agent Activity logging. |
| Safe shadow proof provider | PARTIAL | No-auth/no-real-profile proof. |
| Browser Use CLI wrapper | PARTIAL / FAIL-CLOSED | Guarded wrapper path. |
| Candidate writer | PARTIAL | Untrusted/draft-only candidate skills. |
| Site Skill review writer | PARTIAL / DRAFT | Review-only skill card path. |
| Site Memory Ledger | PARTIAL | Skill memory evidence layer. |
| VincisOS static local target proof | PARTIAL / VERIFIED LOCAL | Local proof lane. |
| Local in-app browser proof | PARTIAL / VERIFIED LOCAL | Browser proof evidence. |
| Safe-local workflow replay proof | PARTIAL / VERIFIED LOCAL | Bounded replay proof path. |
| Browser controller setup readiness | PARTIAL | Readiness path, no broad launch authority. |
| Live safe-local CDP read-only proof | PARTIAL / GATED | Approval-gated live CDP read-only proof evidence. |
| Excalidraw proof chain | PARTIAL / GATED | Prep/readiness/target/approval/proof-shell chain. |
| SiteOps candidate executor chain | PARTIAL / GATED | Checklist/preflight/design/collision/bound approval lanes. |
| SiteOps Pass 1B live browser executor | PARTIAL / GATED | 2026-05-18 spec/build logs exist; real profile/auth/session workflows remain blocked. |
| Trusted skill writes | NOT BUILT / GATED | No trusted writes without future approval/executor. |
| Real profile/auth/session workflows | NOT BUILT / GATED | Explicit approval and credential boundary required. |
| Browser Runtime Studio panel | PARTIAL PRODUCT UI | Advanced until product-ready. |
| Site Skills Studio panel | PARTIAL PRODUCT UI | Advanced unless operator promotes. |

---

## 14. Chaser Forge / Extensions / Self-Extension

**Parent register row:** Chaser Forge  
**Canonical node:** `[[Chaser-Forge-Feature-Family]]`  
**Overall status:** COMPLETE for governed local MVP; remote third-party marketplace deferred.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Approved extension points | COMPLETE | Tabs, pages, cards/widgets, forms, workflows, agent presets, templates, collections, commands, reports, tools, demos. |
| Forbidden extension points | COMPLETE POLICY | Auth, secrets, runtime internals, package/deploy/global CSS, CI/CD, `.env`, etc. blocked. |
| Feature brief | COMPLETE | Extension feature brief path. |
| Manifest | COMPLETE | Extension manifest model. |
| Preview/demo experience | COMPLETE | Local preview/proof deck paths. |
| Validation | COMPLETE | Local validation/governance checks. |
| Sandbox install | COMPLETE | Local sandbox install path. |
| Live install approval packet | COMPLETE / VERIFIED | Approval packet surface verified. |
| Governed marketplace install execution | COMPLETE / VERIFIED | Local MVP install proof. |
| Rollback | COMPLETE / PARTIAL | Local lifecycle includes rollback surfaces. |
| Marketplace import bridge | COMPLETE / VERIFIED LOCAL | Marketplace import to sandbox approval bridge. |
| Studio Chaser Forge panel / Extensions UI | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | Product-facing Extensions surface now exposes operating context, readiness, feature-family coverage, extension object cards, proof/static distribution lanes, and right-inspector selection. Source-render visual QA verified 2026-05-24. No ambient remote exchange, network fetch/upload, external registry mutation, provider call, Agent Bus dispatch, protected-core mutation, payment/license mutation, approval consumption expansion, graph/canonical mutation, or external delivery authority. |
| Proof deck/clickthrough visual QA | COMPLETE / VERIFIED | Proof deck and visual QA evidence. |
| Live StudioAPI control proof | COMPLETE / VERIFIED | StudioAPI proof recorded. |
| Completion audit | COMPLETE / VERIFIED | 2026-05-21 completion audit. |
| Agent preset registration extension point | PARTIAL / POLICY | V1 extension point; sub-agent live execution still gated. |
| Remote third-party marketplace exchange | DEFERRED | Explicitly blocked by design. |

---

## 15. Sub-Agent Presets / Task-Scoped Worker System

**Parent rows:** AOR, Agent Control Plane, Chaser Forge-adjacent, VentureOps/SiteOps worker model  
**Canonical nodes:** `[[Sub-Agent-Presets-Feature]]`, `[[docs/features/CHASE_OS_SUB_AGENT_PRESETS]]`  
**Overall status:** PARTIAL; schema/registry/router/approval contracts verified through inert Agent Bus task packet preview; live execution not built.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Sub-agent preset schema | PARTIAL / VERIFIED | `subagents/schemas/subagent-preset.schema.json`. |
| Team preset schema | PARTIAL / VERIFIED | `subagents/schemas/team-preset.schema.json`. |
| Preset files | PARTIAL / VERIFIED | 9 preset Markdown files observed. |
| Team files | PARTIAL / VERIFIED | 5 default team YAML files observed. |
| Preset registry/loader | PARTIAL / VERIFIED | Runtime registry surfaces exist. |
| Preset router | PARTIAL / VERIFIED | Task to preset/team routing preview. |
| Activation helpers | PARTIAL / VERIFIED | Activation planning, not live dispatch. |
| CLI list/show/validate | PARTIAL / VERIFIED | Read-only CLI. |
| Route preview | PARTIAL / VERIFIED | No execution. |
| Activation approval preview | PARTIAL / VERIFIED | Approval packet preview. |
| Pending approval request writer | PARTIAL / VERIFIED | Guarded pending approval request writing. |
| Approval consumption dry-run | PARTIAL / VERIFIED | Read-only readiness path. |
| Approval-review decision artifact | PARTIAL / VERIFIED | Immutable decision preview/write. |
| Decision-binding preflight | PARTIAL / VERIFIED | Request/decision binding validation. |
| Exact-once marker contract | PARTIAL / VERIFIED | Create-only marker reservation with exact fingerprint. |
| Inert Agent Bus task packet preview | PARTIAL / VERIFIED | Strict no-write/no-dispatch packet preview. |
| Agent Bus task enqueue writer | NOT BUILT | Next recommended pass in logs. |
| Full approval/decision consumer | NOT BUILT | Request/decision mutation not built. |
| Daemon start | NOT BUILT | No daemon start by sub-agent preset lane. |
| Runtime dispatch | NOT BUILT | No Hermes/OpenClaw/Codex/OpenHuman dispatch. |
| Studio Approval Center integration | NOT BUILT | Explicit remaining loop. |
| Live sub-agent execution | NOT BUILT | Explicit remaining loop. |

Preset nodes observed:

- `ceo-orchestrator`
- `memory-documentation-worker`
- `research-worker`
- `engineering-worker`
- `qa-testing-worker`
- `site-ops-worker`
- `marketing-content-worker`
- `product-analysis-worker`
- `venture-ops-worker`

Default teams observed:

- `default-mission-team`
- `default-server-team`
- `default-site-ops-team`
- `default-venture-ops-team`
- `default-workspace-team`

---

## 16. Workspace Mode Layer

**Parent rows:** Interface / Experience, AOR, VentureOps, Phase 11 Chat  
**Canonical node:** `[[Workspace-Mode-Layer-Feature-Family]]`  
**Overall status:** COMPLETE as scoped feature family; live execution remains approval-gated.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Workspace profiles | COMPLETE | `personal_os`, `study_research`, `founder_venture`, `business_ops`, `runtime_agent_ops`, `unknown`. |
| Profile standard | COMPLETE | Canonical profile standard. |
| Route preview | COMPLETE | Read-only routing preview. |
| Rollout planner | COMPLETE | Plan/draft lane. |
| Draft packets | COMPLETE | Draft packet output. |
| Write approval requests | COMPLETE / GATED | Guarded approval request writer. |
| Profile writer | COMPLETE / GATED | Approved profile write path. |
| Dispatch gate | COMPLETE / GATED | Dispatch gate/readiness. |
| Dry-run execution | COMPLETE | No live mutation. |
| Live execution approval | COMPLETE / GATED | Approval path exists. |
| Exact-scope live executor | COMPLETE / GATED | Exact-scope executor path. |
| Product status/ledger | COMPLETE | Status and ledger surfaces. |
| Studio selector | COMPLETE PRODUCT UI | Workspace mode selector. |
| Chat deeplinks | COMPLETE | Chat routing/deeplink surfaces. |

---

## 17. Developer Co-Development Mode

**Parent register row:** Developer Co-Development Mode  
**Canonical node:** `[[Developer-Co-Development-Mode]]`  
**Overall status:** COMPLETE / parked / shadow-oriented.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Repo Truth Explainer | COMPLETE | Explains repo truth from files. |
| Contradiction / Drift Scan | COMPLETE | Finds stale or conflicting docs. |
| Doc Refresh Proposal Generator | COMPLETE | Produces documentation update proposals. |
| Implementation Brief Generator | COMPLETE | Converts repo truth into implementation briefs. |
| Diagram Draft Generator | COMPLETE | Draft diagrams from architecture truth. |
| Shadow-only posture | COMPLETE POLICY | Does not autonomously mutate canonical truth. |

---

## 18. Full-System Operator Surface / OSRIL

**Parent rows:** FSOS, OSRIL, Interface / Experience, AOR  
**Canonical nodes:** `[[Full-System-Operator-Surface]]`, `[[Operator-Surface-Runtime-Interaction]]`  
**Overall status:** OSRIL runtime-side COMPLETE for Phase 9 feature scope; live product surfaces partial.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| OSRIL contract/session modules | COMPLETE PHASE 9 | Runtime-side session/event state. |
| Approval records | COMPLETE PHASE 9 | Runtime-side approval record surfaces. |
| Wait/resume visibility | COMPLETE PHASE 9 | Wait/resume status and response paths. |
| Resume-ready handoff | COMPLETE PHASE 9 | Bounded resume handoff. |
| Runtime support loops | PARTIAL PRODUCT UI | Studio support-loop surface. |
| Browser/runtime dispatch policy | PARTIAL / GATED | FSOS/browser policy hardening recorded. |
| Operator surface event model | PARTIAL | Surface/control event model. |
| External/live operator surface | PARTIAL / GATED | No broad external runtime authority. |

---

## 19. Core / Personal Split, Publication, And Runtime Templates

**Parent rows:** Governance, publication readiness, runtime operations  
**Canonical nodes:** `CORE_MANIFEST.md`, `core_export/`, `core_templates/`, runtime template docs  
**Overall status:** PARTIAL; audit/template assets exist, publication execution remains governed.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Core export audit | PARTIAL / VERIFIED | Public/private split audit evidence. |
| GitHub publication refresh audit | PARTIAL / VERIFIED | Public mirror readiness audit. |
| Core candidate inventory | PARTIAL | Candidate set observed in core export logs. |
| Runtime startup templates | PARTIAL / VERIFIED | Discord/Hermes/OpenClaw lifecycle/startup/handoff/reboot templates. |
| `.exe` release asset boundary | PARTIAL | Release asset/publication boundary tracked. |
| Secrets/private surface separation | PARTIAL / POLICY | Must remain protected. |
| Public mirror publication | GATED / UNKNOWN | No publication mutation claimed here. |

---

## 20. ChaseOS Creator Engine

**Parent rows:** VentureOps, Content, SiteOps, Creator workflows  
**Canonical nodes:** `[[ChaseOS-Creator-Engine-Feature]]`, `[[docs/features/chase-os-creator-engine-spec]]`  
**Overall status:** PARTIAL / PASSES 1-10 VERIFIED / APPROVAL REQUEST WRITER READY / PRODUCT EXECUTION BLOCKED. Creator Engine is not a primary Studio MVP nav item yet.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Runtime skeleton, models, schemas, job store, path policy | PARTIAL / VERIFIED | Pass 1 implemented `runtime/creator_engine/` foundation and schema files. |
| Provided transcript intake | PARTIAL / VERIFIED | Pass 2 runtime-local transcript intake; no transcription backend. |
| CLI ingest surface | PARTIAL / VERIFIED | Pass 3 `creator ingest`; CLI contract includes six Creator commands. |
| Manual source metadata + dry-run fixture smoke | PARTIAL / VERIFIED | Pass 4 adds write-free dry-run metadata and fixture smokes. |
| Manual media reference adapter | PARTIAL / VERIFIED | Pass 5 represents declared media as reference-only `SourceRecording`; no copy/probe/transcode. |
| Media/transcript job linking | PARTIAL / VERIFIED | Pass 6 attaches provided transcripts to reference-only media jobs. |
| RAG/context pack foundation | PARTIAL / VERIFIED | Pass 7 writes reviewable runtime-local `context_pack.json` and Markdown. |
| Cleaned transcript stub | PARTIAL / VERIFIED | Pass 8 deterministic draft artifact; not provider-generated final content. |
| AI narration/script scaffold | PARTIAL / VERIFIED | Pass 8 deterministic script/voiceover scaffolds; no provider/TTS. |
| Captions SRT/VTT | PARTIAL / VERIFIED | Pass 8 deterministic caption artifacts; ASS not verified. |
| Social pack + upload metadata | PARTIAL / VERIFIED | Pass 8 local draft artifacts; no upload/publish. |
| Edit plan + content memory card stub | PARTIAL / VERIFIED | Pass 8 local draft artifacts; no timeline execution or memory promotion. |
| Approval packet preview | PARTIAL / VERIFIED | Pass 9 read-only approval preview for memory-card, publish/upload, and timeline review scopes. |
| Approval request writer | PARTIAL / VERIFIED | Pass 10 create-only pending approval request writer with exact expected digest. |
| Approval consumption dry-run | CODE-OBSERVED / LOG EVIDENCE REQUIRED | CLI contract includes `creator approval-consumption-dry-run`; no dedicated Creator Pass 11 log confirmed. |
| Review-first workflow | PARTIAL POLICY | Approval preview/request lanes exist; grant/decision/consumption/execution remain blocked. |
| Hermes/OpenClaw callable tools | PLANNED / GATED | Future tools under runtime policy; no Studio/AOR/Agent Bus dispatch verified. |
| Recordly/OpenScreen bridge | FUTURE | Future integration. |
| Timeline state reading / region CRUD / frame capture | FUTURE | Future media editor integrations. |
| Auto-short generation | FUTURE | Future output automation. |
| Auto-upload after approval | FUTURE / GATED | Approval-gated only; no autonomous posting. |
| Feedback loop | FUTURE | Later optimization loop. |

Creator Engine remains blocked for: approval decision/grant writing, approval consumption, exact-once execution markers, final content generation through providers, TTS, FFmpeg/media probing, real transcription backend, Recordly/OpenScreen/OBS/editor automation, timeline execution, publish/upload, Studio panel integration, AOR workflow wiring, Agent Bus dispatch, SIC/RAG live query, and canonical memory promotion.

---

## 21. Adaptive Runtime Surface Layer And Reference Seeds

**Parent rows:** Planning/reference only unless promoted  
**Canonical nodes:** `[[adaptive-runtime-surface-layer-spec]]`, `[[adaptive-runtime-surface-layer-audit]]`  
**Overall status:** PLANNING / REFERENCE.

Repo-observed features and subfeatures:

| Feature / subfeature | Status | Notes |
|---|---:|---|
| Adaptive Runtime Surface Layer spec | PLANNED | Upcoming/reference index seed. |
| Adaptive Runtime Surface Layer audit | PLANNED | Audit seed. |
| OpenHuman reference extraction | REFERENCE | Active runtime integration retired/reference-only. |
| TinyHumans webapp reference extraction | REFERENCE | Product/UX lessons only. |
| Token Juice / provider-router / product UX lessons | REFERENCE | Seeded from reference products, not active feature families. |

---

## Studio Product Surface Names

These are product page/surface names, not necessarily feature families:

- Home
- Chat
- Project Workspace
- Missions / Workflow Packs
- Extensions / Chaser Forge
- Graph View
- Node Inspector
- Knowledge Boxes
- Graph Hygiene
- Provenance
- Intake
- Capture
- Sources
- Research Collections
- AI Agents
- Agent Bus
- Schedules
- Task History
- Browser Runtime
- Site Skills
- Context Import
- Memory Ledger
- Runtime Memory
- Proactive Briefings
- Review Queue
- Companion Surface
- Approvals
- Settings
- Logs / Audit
- Decisions
- QA / Proof
- Feature Audit
- Workflow Registry
- Role Cards
- Agent Identity
- Runtime Navigation
- Runtime Support Loops
- App Launcher
- Workspace Setup

## Operator Confirmation Checklist

- [ ] Confirm the 21 inventory sections are the correct canonical grouping for downstream docs.
- [ ] Confirm Visual Capture Markdown belongs under Capture + Acquisition and should appear in Studio as `Capture`.
- [ ] Confirm Sub-Agent Presets should stay under Runtime/Governance and Chaser Forge-adjacent extension points, not become a first-tier MVP nav item yet.
- [x] Confirm Product Workflow Packs should appear as `Missions / Workflow Packs`.
- [ ] Confirm Creator Engine remains outside first-tier MVP nav until product execution/Studio/AOR lanes are verified, despite its partial runtime implementation.
- [ ] Confirm Browser Runtime and Site Skills remain advanced until broader live browser authority is implemented.
- [ ] Confirm `Home` is a dashboard/product surface, not a feature family.

## Non-Claims

This inventory does not claim:

- every possible unlogged branch experiment has been found;
- VCMI source-pack AOR dispatch readiness is verified beyond code-observed registry/source-contract evidence;
- live sub-agent execution is built;
- Studio Dashboard/Home is product-ready;
- navbar implementation is done;
- graph persistence is built;
- VCMI writes promote to SIC/graph/canonical memory;
- Workflow Packs execute external work;
- Creator Engine is product-complete, Studio-mounted, AOR/Agent-Bus-dispatchable, approval-consumption complete, or publish/upload/timeline execution ready;
- provider/model calls are globally available;
- browser automation is broadly authorized;
- any secret, credential, `.env`, Pulse memory, Personal Map, R&D truth-state, or governed core runtime state was mutated.

## Graph Links

[[Feature-Register]] [[Feature-Fit-Register]] [[Studio-Product-UI-Feature-Family-Normalization]] [[Visual-Capture-Markdown-Ingestion-Feature]] [[Sub-Agent-Presets-Feature]] [[Product-Workflow-Packs-Feature]] [[ChaseOS-Creator-Engine-Feature]]
