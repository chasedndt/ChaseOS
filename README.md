# ChaseOS

**Human intent. Agentic execution. Private control.**

ChaseOS is the local-first AI operating system for builders running real projects with agents. It turns scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.

The core brand idea is simple: human intent and permissioned agent runtimes operating inside a private, evolving control plane.

## Website

ChaseOS public launch domain:

https://chaseos.ai

The public site will host ChaseOS Studio Early Access, Chaser Forge marketplace preview, standards and pack manifests, documentation, open-core/commercial philosophy, waitlist, privacy/security notes, support, and creator submission paths.

Status: ChaseOS Studio Early Access / Developer Preview. `chaseos.systems` is superseded as the primary launch domain and may remain a future secondary redirect, standards alias, ecosystem alias, or defensive domain if purchased later.

---

## What is ChaseOS?

ChaseOS is a local-first, privacy-first command layer for human-agent work. It connects source intelligence, structured memory, knowledge graph relationships, SOPs, workflow automation, runtime profiles, permission matrices, approvals, and bounded execution into one governed system.

The current implementation uses an Obsidian-first markdown vault plus Python runtime packages. That is the substrate, not the identity. The product identity is ChaseOS: a private operating layer where human intent, agent runtimes, memory, workflows, and execution history stay under user control.

## Why ChaseOS exists

Modern AI work is fragmented. People think in one AI chat, store context in another notes system, run code in terminals, manage automations elsewhere, keep files in scattered folders, and hand off tasks to agents that do not share a durable operating memory.

That creates repeated re-briefing, lost project context, unclear agent authority, disconnected workflows, and automation that cannot be trusted without visible provenance and permission boundaries.

ChaseOS exists to make that operating context durable, inspectable, and executable without giving up private control.

## The problem: agentic chaos

ChaseOS is built against agentic chaos: disconnected tools, forgetful chats, shallow AI wrappers, ungoverned automation, and agent systems that execute without enough user doctrine, memory, or permission structure.

The problem is not that AI tools cannot answer questions. The problem is that most AI tools do not operate inside one trusted system of record.

## The solution: a private command layer

ChaseOS gives the operator one private command layer where:

- files, notes, sources, projects, workflows, SOPs, and outputs have durable homes;
- knowledge graph memory links sources, decisions, work products, approvals, and runtime activity;
- AI agents act as bounded runtimes, not uncontrolled authorities;
- automations and workflows run through visible gates, logs, and permission boundaries;
- generated ideas stay separate from verified facts and canonical project state.

The human stays in control. Agents gain useful context. The system compounds over time.

## Core capabilities

- Secure memory and writeback: local-first markdown, runtime artifacts, logs, provenance, and canonical state separation.
- Knowledge graph memory: relationships across sources, projects, workflows, decisions, approvals, and outputs.
- Source intelligence: governed ingestion, source packages, workspaces, retrieval, and structured outputs.
- Permissioned agent runtimes: explicit trust tiers, permission matrices, runtime profiles, Agent Bus boundaries, and approval-gated execution.
- Automation, SOP, and workflow execution: bounded AOR workflows, schedule intent, workflow packs, mission modes, and audit trails where implemented.
- Human-agent collaboration: agents assist, propose, route, execute within approved scopes, and write back evidence without replacing operator authority.
- Privacy-first positioning: user data, source archives, project memory, and generated outputs stay in the user's system unless a specific connector/runtime path is approved.

## Who ChaseOS is for

The first audience is AI-native operators: technical founders, AI engineers, developers, high-agency creators, entrepreneurs, researchers, and builders who already feel the cost of scattered chats, repos, notes, files, workflows, and agents.

Longer term, ChaseOS can support students, creators, knowledge workers, operators, small businesses, and everyday users who want a private AI operating system for goals, study, work, planning, and execution.

## How ChaseOS is different

ChaseOS is not a generic AI chat, a second-brain template, a productivity app, or an automation wrapper.

It is different because it combines:

- private local-first memory;
- knowledge graph relationships;
- explicit permission and trust boundaries;
- governed source ingestion;
- runtime and agent profiles;
- approval-gated execution;
- SOP/workflow automation;
- durable logs, proof artifacts, and documentation history.

Most AI tools answer in the moment. ChaseOS remembers the system.

## Brand and design foundation

The current brand foundation lives in [docs/brand/](docs/brand/).

- Canonical name: `ChaseOS`
- Primary tagline direction: `Human intent. Agentic execution. Private control.`
- Visual essence: `Human core. Agent network. Private boundary. Controlled execution.`
- Design status: `DOCS-ONLY / BRAND FOUNDATION ADOPTED / LOGO AND UI REDESIGN NOT COMPLETE`

Use [docs/brand/Brand_Copy_Bank.md](docs/brand/Brand_Copy_Bank.md) for reusable definitions, taglines, and copy. Use [docs/brand/Design_Tokens_Preliminary.md](docs/brand/Design_Tokens_Preliminary.md) for preliminary visual tokens before any future UI redesign.

## Project status / roadmap

**Public launch status (2026-05-31 domain override):**
- Primary domain selected: `https://chaseos.ai`.
- Current public posture: `ChaseOS Studio Early Access / Developer Preview`; do not claim public-user beta readiness until release-smoke and public-doc gates clear.
- Public-facing product identity: ChaseOS = local-first AI operating system; ChaseOS Studio = desktop command surface; Chaser Forge = workflow-pack/marketplace preview; Managed Agents / Chaser Agent = future runtime infrastructure.
- Public Forge index target: `https://chaseos.ai/forge/index.json`.
- Current public blockers: public README/package hygiene, Studio route smoke, landing/legal/privacy wiring, package/license/export decision, truthful runtime/status labels, and one recorded green release-smoke packet.
- Non-blocking/upcoming if labeled honestly: AISO, voice, full browser automation, billing, managed agents, live marketplace payments, external delivery, CRM/payment mutation, and full provider abstraction.

**What ChaseOS does (current capability):**
- Ingests sources (transcripts, research digests, documents, NotebookLM outputs) through a five-stage governed pipeline — not a flat pile of raw files
- Turns processed inputs into classified knowledge notes with explicit trust labels, origin provenance, and domain indexing
- Keeps AI-generated ideas visibly separate from verified facts and active project state
- Adds a Workspace Mode Layer (WML) so agents can distinguish `personal_os`, `study_research`, `founder_venture`, `business_ops`, `runtime_agent_ops`, and `unknown` contexts before choosing read order, outputs, workflows, approvals, and adapter ceilings; canonical feature-family node: `06_AGENTS/Workspace-Mode-Layer-Feature-Family.md`
- 2026-05-14 WML product-feature status: `COMPLETE` for the runtime/operator product surface. Core WML modules, six validated workspace profiles, route preview, profile approval/write gates, dispatch gate, dry-run executor, exact-scope live AOR executor, product-status command, approval-ledger command, read-only Studio WML selector panel, and Chat-to-Studio WML deeplink selector are implemented and dry-tested. The Studio panel exposes URL-persistent mode selection, project/domain context, and read-only route previews; the Chat panel exposes read-only WML mode cards that link into the Studio panel. These surfaces do not execute WML workflows, write profiles, dispatch Agent Bus tasks, consume approvals, call providers, or mutate canonical state.
- Governs every active project with an operating file: mission, status, goals, and open loops in one place
- Routes AI tools with explicit permission contracts and hook-level enforcement — bounded, not unconstrained
- Works across any domain: trading, engineering, courses, business, fitness, creative work, personal life
- Runs coherently on low-energy days — SOPs and templates do the thinking; you do the deciding

**Phase 8 — Connector / Capture Automation — COMPLETE (2026-03-31, all 10 passes):**
- ContentPacket, router, intake_writer, dedup registry, watched-folder automation, RSS/Atom connector, browser/HTML connector, Perplexity API connector, Grok/xAI API connector — all live
- `chaseos` operator command surface — `chaseos capture file`, `chaseos capture stdin`, `chaseos capture rss URL [--limit N]`, `chaseos capture browser file PATH`, `chaseos capture perplexity --query "..."`, `chaseos capture grok --query "..."`, `chaseos watch add PATH --class CLASS`, `chaseos watch run --once`, `chaseos intake ls`, `chaseos intake inspect`, `chaseos intake dedup-stats`, `chaseos doctor`, `chaseos test capture`
- Phase 7 (Source Intelligence Core) is complete — all 7 passes done; local-first source packages, workspaces, retrieval, output generation, embedding backends
- `06_AGENTS/Feature-Fit-Register.md` created — canonical feature/layer triage register for Phase 8 through Phase 10

**Setup/bootstrap note (2026-04-26):**
- `chaseos setup` is being developed not only as provider/integration configuration, but as the deployable bootstrap surface for a fresh ChaseOS instance
- early `setup init` work scaffolds framework/setup/runtime/orientation surfaces only
- it intentionally does **not** fabricate personal project truth, knowledge notes, fake logs, or secrets
- CLI consolidation is now active: installed `chaseos` / `chase` entrypoints point to `runtime.cli.main:main`; `chaseos.py` and `runtime/cli.py` are compatibility shims only

**What ChaseOS is building next (Phase 9 — Operator Runtime):**
- Autonomous Operator Runtime — PARTIAL LIVE: all four first-wave workflows (`operator_today`, `operator_close_day`, `graph_hygiene`, `graduate_ideas`) execute through the real 8-stage AOR pipeline; bounded writeback and audit active; Graph Substrate subsystem built (`runtime/graph/`, 87 tests, advisory narrowing seam); operator briefing v2 and native schedule intent are live; OpenClaw/Hermes draft runtime-instance promotion/readiness substrate is now machine-checkable through manifests, role cards, readiness helpers, promotion records, and pair-level validation while canonical promotion authority remains blocked
- Agent Memory / Identity — SEEDED OPERATIONAL (2026-04-27): Layer C/D memory inspector, runtime profiles, repair memory, nav overlays, task-local context homes, and first Agent Identity Ledger formal files are present; Claude has the primary Phase 9 identity-ledger foothold and Hermes/OpenClaw have seeded peer runtime-instance ledgers
- Native Scheduling Intent Architecture — BUILT (2026-04-15); ChaseOS owns schedule intent as canonical state in `runtime/schedules/`; OpenClaw remains the external execution lane that reads ChaseOS intent and invokes `chaseos run`
- Operator Briefing V2 — BUILT (2026-04-17); `operator_today` and `operator_close_day` implement the four-layer model (canonical state / carry-forward / sourced runtime context / synthesis) with bounded Operator-Briefs writeback
- ChaseOS MCP Server — V1 stdio scaffold built (2026-04-20); partial JSON-RPC stdio compatibility and local process-boundary client smoke proof added (2026-04-27); scoped resources/tools/prompt live in `runtime/mcp/`; proposal staging, envelope-owned audit, static prompt, and safe current_truth defaults implemented
- Runtime Bootstrap + User Attachment Contracts — SEEDED (2026-04-24); machine-readable startup/attachment layer now lives in `runtime/bindings/`
- Runtime State Resolver + CLI Foothold — SEEDED (2026-04-24); canonical runtime-state artifact, manifest-aware resolution, operator docs, and first local runtime inspection commands now live in `runtime/state/`
- Runtime Lifecycle Layer — SEEDED (2026-04-24); machine-readable lifecycle records for OpenClaw and Hermes now live in `runtime/lifecycle/` as the future substrate for `start` / `stop` / `restart` / `health`
- SiteOps Browser Control Proof — COMPLETE TARGETED LOCAL PROOF (2026-05-04); ChaseOS can launch a throwaway-profile local browser against a ChaseOS-owned Canva-style editor sandbox, operate the UI through bounded CDP pointer actions, show an `Agent control active` HUD with cursor/trail/click/drag feedback, write scoped Browser Run/SiteOpsRun/SiteOpsAudit evidence, and block export/public share/account settings. This is not canva.com automation, not authenticated-session control, and not full computer/file-system control.
- Agent Control UX Contract — SEEDED (2026-05-04); `06_AGENTS/Agent-Control-UX-Contract.md` defines the shared visible-control pattern for future browser, files, system, and runtime lanes: active-control HUD, cursor/focus marker, action feedback, lane rail, approval/blocked/manual-takeover states, and provenance links. Only the browser lane has a local proof; all other lanes remain future governed work.
- Scheduled Briefing Pipelines — architecture defined; first implementation (StrikeZone Market Digest Publisher) pending scheduling intent + MCP server foundation
- Runtime Navigation Map — architecture defined; implementation is Phase 9

**ChaseOS Studio - Phase 10 product layer:**
ChaseOS Studio is the standalone desktop, graph-first, mouse-first visual operating surface for ChaseOS. It is the product shell where the full ChaseOS system becomes operable without navigating raw markdown files. Current repo truth: the native PyWebView Studio shell and read-only panel lane are implemented through Pass 10W, Pass 10X adds read-only parser-backed graph input, Pass 10Y adds read-only typed graph/trust overlays, Pass 10Z adds read-only graph-node provenance chain inspection, Pass 10AA adds approval-gated node create/edit, Pass 10AB adds approval-gated visual link proposals with lightweight pending-edge overlays, Pass 10AC adds approval-gated Runtime Cockpit action-readiness requests, Pass 10F1 adds read-only Open Folder compatibility readiness, Pass 10F2 adds bounded read-only Obsidian vault detection, Pass 10F3 adds read-only general Markdown inference preview, Pass 10F4 adds a read-only ChaseOS bootstrap wizard preview, and Pass 10F5/10F6 add a governed workspace upgrade approval packet plus proof-temp exact-once execution chain. As of 2026-05-12, the Pass 10B expansion-pack installer-build execution proof for packet `studio-installer-build-appr-ac14811da651baec` is **COMPLETE / VERIFIED**: the exact-once marker, portable ZIP, manifest, output audits, dry-run evidence, execution evidence, and post-execution completion audit are present, and forbidden signing/startup/release/host/provider/Agent Bus/Gate/Git/workflow/canonical mutations remain absent. This proof is a scoped `zip-portable` artifact and does not include a branded installer logo/icon, shortcut, signed installer, or install wizard. Studio internal portable MVP is now **COMPLETE / INTERNAL PORTABLE MVP CLOSED WITH DEFERRALS** after explicit operator acceptance and accepted closure evidence. Release-grade Studio is still open: branded assets, signing, startup/autostart, release promotion, real target migration, provider/model calls, runtime/browser dispatch, and persisted graph storage remain deferred/operator-governed. Canonical architecture: `06_AGENTS/ChaseOS-Studio-Architecture.md`; canonical closure tracker: `06_AGENTS/ChaseOS-Studio-Phase10-Implementation-Tracker.md`.

2026-05-12 manual acceptance update: `chaseos studio mvp-manual-install-launch-acceptance` validates the existing packaged launch/visual QA evidence and writes bounded readiness/acceptance records. The earlier readiness record was blocked on a missing operator acceptance statement; the later accepted record closes only the internal portable MVP profile with explicit release-grade deferrals.

2026-05-12 internal portable MVP closeout update: after the operator supplied the acceptance statement `i accept begin the nest pass`, the accepted manual evidence, accepted operator decision packet, and closure gate now report `COMPLETE / INTERNAL PORTABLE MVP CLOSED WITH DEFERRALS` with zero blockers. This is not release-grade completion: signing, branded installer assets, startup/autostart, release promotion, provider/model calls, runtime/browser dispatch, real target migration, and broader approval/canonical writeback remain deferred/operator-governed.

2026-05-12 Studio product-home update: the Studio Dashboard model, native shell Dashboard view, and localhost Dashboard app now surface a first-screen product status panel that explicitly distinguishes `internal_portable_mvp_closed=true` from `release_grade_complete=false`, lists the eight open release-grade lanes, links the closure/decision/manual-acceptance evidence, and keeps signing, host mutation, provider calls, runtime/browser dispatch, target mutation, release promotion, and canonical mutation blocked.

2026-05-12 Studio release-grade action-center update: the product-home panel now includes an action center for the eight open release-grade lanes. Each lane shows the required operator input, human-in-the-loop category, safe preview/review command when one exists, and disabled UI action control. The stale companion-selection executor lane was removed because the governed companion-selection consumption executor is already complete; persisted graph storage now appears as the still-open architecture lane. Execution remains blocked for all action-center lanes.

2026-05-13 Studio action-center preview-runner update: the release-grade action center now has a bounded allowlist runner. The native shell exposes a `Run Safe Previews` control through `get_action_center_preview_runner`, and the localhost Dashboard app surfaces runner readiness. The runner can invoke six no-execution preview/readiness commands and summarize their JSON results, while two lanes remain explicitly operator-gated: real target workspace migration requires an operator target path plus approval packet ID, and persisted graph storage remains architecture-review-only. Verification ran the six allowlisted previews: one returned ready, five returned blocked preview/readiness envelopes, and no approval consumption, signing, host mutation, provider call, runtime/browser dispatch, target migration, release promotion, graph-store write, or canonical mutation was authorized.

2026-05-12 companion-selection executor update: the governed Phase 11 companion-selection approval-consumption executor is now complete for one approved selection. It consumed approval `1276be3b-cccc-4c74-89e4-9a73f3eeb541`, wrote `runtime/studio/chat/companion-selection.json`, reserved the exact-once marker, and blocked duplicate execution before target rewrite. Live provider/model calls, runtime/browser dispatch, broader approval target mutation, Agent Bus/canonical writeback, signing, branded installer assets, startup/autostart, release promotion, and real target migration remain operator-governed.

**ChaseOS Pulse — local v1 product-grade lane (2026-05-04):**
ChaseOS Pulse now has a product-grade local v1 closeout surface. The local lane includes multi-audience decks, governed feedback candidates, static product-shell and Studio panel footholds, Personal Map/Runtime Brain/Approval Queue proof surfaces, native schedule proof surfaces, and connector/source-scanner proof surfaces. Current cross-feature Approval Center truth and authority boundaries live in [[ChaseOS-Approval-Center]]. Live connector execution, schedule activation, approval execution/apply flow, and runtime brain mutation remain deferred until explicitly approved. After operator approval, the R&D workbook final sync is now complete and verified with existing Pulse rows updated plus `CH-1008`; no runtime authority was expanded.

**ChaseOS VentureOps - business/application product layer (2026-05-10):**
ChaseOS VentureOps is now formally adopted as the governed runtime/product layer that converts ChaseOS capabilities into repeatable, auditable, monetizable workflows for Chase-owned ventures and client-facing services. Current status is **IMPLEMENTATION COMPLETE / LOCAL PROOF VERIFIED / REAL-WORLD DELIVERY AND REVENUE EVIDENCE BLOCKED**: architecture docs, portable instance-intelligence contract, recommendation-engine contract, revenue workflow registry, workflow-pack standard, proof-artifact standard, scorecard standard, adapter-use matrix, exchange readiness standard, templates, YAML registry/schema scaffolds, two workflow-pack examples, `runtime/ventureops/` deterministic profiling/recommendation/validation helpers, canonical CLI validation/readiness/proof-gate commands under `chaseos ventureops`, the canonical passover/handover plus exact requested alias `06_AGENTS/VentureOps-externaal-Readiness-Handover.md`, readiness report writeback artifacts, evidence packet template artifacts, template-only rejection guard, operator evidence intake CLI, evidence discovery preflight CLI, real-client input manifest report write guard, scope approval packet builder CLI, scope evidence packet builder CLI, delivery proof packet builder CLI, revenue evidence packet builder CLI, external packet path guard, real evidence closeout readiness CLI, whole feature-family completion audit CLI, autonomous implementation completion CLI, final external execution runbook CLI, final evidence bundle packet builder CLI, final evidence bundle packet path guard, final evidence bundle validator CLI, final evidence bundle validation report write guard, final evidence bundle validation report dated default, final evidence bundle validation report default collision guard, final bundle validation completion gate, scope source path verifier, live-client proof artifact verifier, live-delivery proof artifact verifier, actual final proof artifact discovery with root-aware revenue reference revalidation, live-client source digest validation, live-client completion reference revalidation, live-client scope packet reference revalidation, live-client reference consistency validation, revenue reference consistency validation, receipt artifact validation, and positive-path completion test coverage, guarded live client scope proof CLI, guarded live client workflow proof CLI, and guarded proof-only live revenue CLI mapped into the completion audit, durable external audit/runbook report writeback, and the first bounded AOR-backed VentureOps workflow (`agent_runtime_governance_audit`) exist. The latest synthetic client-style internal run ingested declared fixture runtime/governance files and wrote an internal proof, client-safe draft report, standalone scorecard, offer packet, client-scope record, blocked delivery-approval contract, no-send delivery packet preview, pending approval request artifact, approval consumption proof, exact-once delivery gate proof, delivery gate marker, external-send dry-run proof, approved external-send local proof-sink artifact, CRM draft, payment/invoice draft, Workflow Exchange publication preview, and live client scope contract under `07_LOGS/Workflow-Proofs/2026-05-11_agent_runtime_governance_audit_live-client-scope-contract*`. The CLI can audit the full feature-family objective, audit external readiness, audit autonomous implementation completion, write durable audit reports, write a final external command runbook, author guarded operator evidence packets that block escaped paths from writing outside the vault root, author a guarded final evidence bundle packet that blocks escaped paths from writing outside the vault root, validate an operator-supplied final evidence bundle before completion audit rerun, block final bundle validation report overwrites or escaped report paths, default final bundle validation reports to a dated create-only path when `--write-report` omits `--report-path`, advance that implicit default to the next suffixed path when the dated report already exists, guard real-client input manifest report writeback against overwrite/escaped paths while advancing omitted report paths to the next dated default, require a ready final bundle validation report before final completion, write placeholder evidence packet templates, author guarded scope approval artifacts, scope packets, delivery proof, and revenue evidence packets from operator-supplied approval/source/delivery/receipt/proof fields, validate scope/revenue evidence packets, run `evidence-intake` to compose supplied packets and recommend the next guarded proof command, run `evidence-discovery-preflight` to scan bounded repo-local evidence roots and reject template-only scaffolds, run `real-evidence-closeout-readiness` to review the typo handover/passover/audit/intake surfaces and state the final blockers, verify approved scope source paths exist as files before proof-gate readiness/execution, validate typed scope approval artifacts before scope evidence authoring, readiness, intake, discovery, AOR loading, and proof execution, validate live-client proof artifact shape and source digests before proof-only revenue, validate operator-attested live-delivery proof artifact shape before revenue proof, discover actual final live-client and revenue proof artifacts before completion, revalidate revenue proof references from disk before accepting final revenue completion, revalidate live-client workflow proof references from disk before accepting final live-client completion, revalidate the live-client workflow proof's referenced scope packet, typed approval artifact, and approved source files before accepting final live-client completion, verify live-client referenced scope gate and scorecard consistency before accepting final live-client completion, verify revenue referenced delivery and live-client proof consistency before accepting final revenue completion, validate redacted JSON receipt artifacts before accepting final revenue completion, prove the audit completion path in a temp-root fixture containing valid final artifacts plus a ready final bundle validation report, check whether a scope packet is ready for the proof gate, execute the guarded local live-client scope proof gate with `--execute-proof` and a valid scope packet, write a scoped local live-client workflow proof with `live-client-workflow-proof`, write proof-only local revenue artifacts with `live-revenue-proof` only after a valid live-client workflow proof artifact and valid delivery proof artifact exist, check future revenue-proof readiness against revenue packet, delivery proof, and live-client workflow proof artifact path, and write blocked-state readiness reports for operator passover. The implementation lane is now complete without operator-supplied payment evidence, but real-world delivery/revenue completion remains blocked: no factual operator delivery attestation, redacted receipt/payment evidence, payment mutation, CRM mutation, provider call, browser action, live external client delivery, accounting claim, or completed live revenue workflow has been performed.

**VentureOps MVP current-status correction (2026-05-14):**
The May 10/11 blocked-input language is superseded for the first MVP pass-7 criterion. `mvp readiness-gate --json` now discovers valid internal ChaseOS scope evidence and a valid scoped local `ventureops-live-client-workflow-proof` artifact, so VentureOps is complete for one scoped local workflow proof. It is still not complete for live revenue, external delivery, CRM/payment mutation, provider/browser execution, marketplace publication, or canonical promotion. The current MVP P0 blocker is the unresolved OpenAI secret reference only; tracked Chat approval `5849a53f-10e0-46af-a89a-7de06150f7f8` was explicitly approved, consumed exactly once, wrote target proposal `01_PROJECTS/_chat_proposals/mvp-chat-to-approval-proof-draft-a-proposal-for-a-small-operator-workflow-status-8a9571a16d09.md`, and is replay-blocked by marker `runtime/studio/approvals/_chat_consumption_markers/5849a53f-10e0-46af-a89a-7de06150f7f8.json`.

**VentureOps Mission Mode final hardening (2026-05-14):**
The local Mission Mode workspace for `mission-chase-ai-runtime-governance-kit` is active locally and final-hardened: exact-once claim/result and activation gates are consumed, the local Codex Agent Bus task is closed to `done`, closed-task drift and activation workspace mismatch now fail validation, credential/secret-read boundary flags are explicit, and `runtime/ventureops` regression coverage is green. This does not authorize external/client delivery, provider calls, browser action, CRM/payment mutation, live trading, workflow evolution apply, protected-file edit, credential read, or canonical promotion.

**VentureOps Mission Mode external/client evidence gate readiness (2026-05-14):**
`chaseos ventureops mission-external-client-evidence-gate --mission-workspace PATH --json` now evaluates the post-local-activation evidence boundary. With no supplied operator evidence it fails closed as `blocked_missing_external_client_evidence`, requiring an external action type, explicit operator approval statement, and typed scope/delivery/revenue proof paths that resolve inside the vault root. The gate composes the existing VentureOps evidence validators and can report readiness only for the next guarded proof/review command; it does not execute live workflows, send externally, call providers/browsers, mutate CRM/payment systems, read credentials, apply workflow evolution, trade, edit protected files, or promote canonical state.

**VentureOps governed completion attempt (2026-05-15):**
Codex ran the delivery proof, revenue evidence/proof, and final evidence bundle chain in one governed pass using existing repo-local evidence. The chain failed closed at the factual evidence boundary: no operator delivery attestation, redacted receipt/payment artifact, received/settled payment status, amount greater than zero, delivery proof, revenue packet, proof-only live revenue artifact, or final bundle packet was created. Blocked reports live under `07_LOGS/Workflow-Proofs/2026-05-15_ventureops-governed-completion-*`; VentureOps remains not complete for delivery, revenue, or final bundle completion.

**VentureOps real-operator evidence ingestion prep (2026-05-15):**
Codex prepared the next safe intake lane as template/readiness artifacts only. `07_LOGS/Workflow-Proofs/2026-05-15_ventureops-real-operator-evidence-ingestion-packet.json` lists the exact delivery attestation, redacted receipt/payment, payment status/amount/currency, CRM reference, and approval fields required before delivery/revenue/final proof artifacts can be written. No delivery proof, revenue packet, proof-only live revenue artifact, final bundle, external send, provider/browser action, CRM/payment mutation, invoice, credential read, or revenue claim was performed.

**VentureOps autonomous implementation completion (2026-05-15):**
`chaseos ventureops autonomous-implementation-completion --json` now separates implementation completion from real-world delivery/revenue completion. Live report `07_LOGS/Workflow-Proofs/2026-05-15_ventureops-autonomous-implementation-completion-report.json` returns `feature_implementation_complete=true`, `operator_evidence_required_for_tests=false`, and `safe_to_mark_real_world_delivery_revenue_complete=false`. This completes the local implementation lane and preserves the factual evidence gate; no delivery proof, revenue packet, payment/CRM mutation, external send, provider/browser action, invoice, credential read, accounting claim, or revenue claim was performed.

**VentureOps final hardening Studio guide (2026-05-15):**
Studio Dashboard now surfaces a VentureOps real-world usecase hardening panel in both the localhost dashboard app and native Studio shell. The panel reads the autonomous implementation audit, keeps `feature_implementation_complete=true` separate from `real_world_delivery_revenue_complete=false`, links the operator guide at `07_LOGS/Operator-Briefs/2026-05-15-ventureops-studio-real-world-usecase-test-guide.md`, and exposes safe dry-run commands for rehearsing the AI Runtime Governance Audit workflow. This is Studio visibility and operator-test hardening only; no external send, provider/browser action, CRM/payment mutation, invoice, credential read, accounting claim, revenue claim, or canonical promotion was performed.

**VentureOps completion hardening addendum (2026-05-12):**
Final proof-only revenue completion now also revalidates the original referenced revenue packet from disk before discovery or final bundle validation can accept a revenue proof. Final completion discovery also revalidates each ready final bundle validation report's referenced `bundle_path` before accepting the report. This remains proof-chain hardening only; no real client scope packet, real revenue packet, live external delivery, CRM/payment mutation, accounting claim, or completed live revenue workflow has been performed.

**VentureOps AI runtime security audit alias closeout (2026-05-13):**
The exact P0 workflow id `ventureops_ai_runtime_security_audit` now exists as a bounded AOR alias for `agent_runtime_governance_audit`, with manifest `runtime/workflows/registry/ventureops_ai_runtime_security_audit.yaml`, handler `runtime/workflows/ventureops_ai_runtime_security_audit.py`, role card `06_AGENTS/role-cards/security_reviewer.yaml`, and runtime audit report `07_LOGS/Runtime-Audits/2026-05-13-ventureops-ai-runtime-security-audit.md`. Live local proof `07_LOGS/Workflow-Proofs/2026-05-13_ventureops_ai_runtime_security_audit_session-closeout-v2.md` verified internal proof/report/scorecard writeback for declared local governance/runtime files only. This does not supply real client evidence, run an external client workflow, send externally, call a provider, control a browser, mutate CRM/payment systems, perform live remediation, or complete live revenue.

**VentureOps live-client scope proof blocked-input pass (2026-05-13):**
The requested next pass, `ventureops-live-client-scope-proof`, was attempted as a readiness/input-manifest pass and is correctly blocked because no typed real-client scope approval, approved source paths, approval artifact, or real-client scope evidence packet exists in the repo. Evidence was written to `07_LOGS/Workflow-Proofs/2026-05-13_ventureops-real-client-input-manifest.json` and `07_LOGS/Workflow-Proofs/2026-05-13_ventureops-live-client-proof-readiness-report.json`; runtime summary lives at `07_LOGS/Runtime-Audits/2026-05-13-ventureops-live-client-scope-proof-blocked.md`. No live-client workflow proof, client data ingestion, external send, provider/browser action, CRM/payment mutation, live remediation, revenue claim, or canonical promotion was performed.

**VentureOps real-client input packet handoff (2026-05-13):**
The follow-on input-packet pass wrote a template-only operator handoff at `07_LOGS/Workflow-Proofs/2026-05-13_ventureops-real-client-input-packet.md` plus JSON/readiness evidence. This packet lists the concrete fields needed before `scope-approval-packet` or `scope-evidence-packet` can be authored. It is not a real approval artifact, not scope evidence, and cannot satisfy the live-client proof gate.

**VentureOps internal scope packet/readiness pass (2026-05-13):**
After the operator granted broad repo access, Codex converted that into a bounded internal scope rather than approving secrets, broad folders, or external side effects. The pass wrote typed scope approval and scope evidence artifacts for `ChaseOS Internal Runtime Security Audit` under `07_LOGS/Workflow-Proofs/2026-05-13_chaseos-internal-runtime-security-audit_scope-approval.json` and `07_LOGS/Workflow-Proofs/2026-05-13_chaseos-internal-runtime-security-audit_scope-evidence.json`, covering 15 exact governance/runtime files. `live-client-proof-readiness` reports `ready_for_live_client_workflow_proof=true` for that internal scope packet.

**VentureOps live-client workflow proof execution (2026-05-13):**
Codex ran the guarded local `live-client-workflow-proof --execute-proof` over the verified internal scope packet. It wrote the proof batch rooted at `07_LOGS/Workflow-Proofs/2026-05-13_agent_runtime_governance_audit_2026-05-13_chaseos-internal-runtime-security-audit_live-client-workflow-proof*`, including `..._live-client-workflow-proof.json`, with `live_client_workflow_proof_performed=true`, `scoped_client_data_ingested=true`, and `broad_client_data_ingested=false`. No external send, provider/browser action, CRM/payment mutation, invoice send, revenue claim, marketplace publication, or canonical promotion occurred. The next real-use blocker is live revenue proof: `live-revenue-proof-readiness` is blocked because no live revenue evidence packet or delivery proof artifact has been supplied.

**VentureOps live revenue evidence handoff (2026-05-13):**
Codex wrote the operator handoff for the remaining live revenue evidence lane at `07_LOGS/Operator-Briefs/2026-05-13-ventureops-live-revenue-evidence-packet-handoff.md`, plus handoff JSON, template-only revenue scaffold, discovery report, and blocked readiness report under `07_LOGS/Workflow-Proofs/2026-05-13_chaseos-internal-runtime-security-audit_*`. The handoff pre-fills the safe proof-chain fields and leaves only real operator facts for payment reference, received/settled amount, redacted receipt, CRM/reference id, and delivery attestation. This is ACTION_REQUIRED only: no payment/CRM mutation, invoice send, external delivery, provider/browser action, accounting claim, revenue claim, or final completion occurred.

**VentureOps internal workflow proof closeout (2026-05-13):**
After operator review, the current VentureOps instance is closed as an internal scoped workflow proof, not a revenue proof. No payment evidence is required for this closeout. The proof verified that VentureOps can package, scope, run, and evidence the local AI Runtime Security Audit workflow over approved ChaseOS files with no provider call, browser action, external send, CRM/payment mutation, invoice, revenue claim, or canonical promotion. Live revenue and real external delivery are deferred until a future real-world use case intentionally supplies real scope, delivery, and payment evidence.

**VentureOps Mission Mode foundation (2026-05-13):**
VentureOps now has a governed Mission Mode foundation for long-running objectives. The pass added architecture docs, templates, machine-readable schemas, deterministic draft helpers, validators, tests, and example mission manifests for mission manifests, sub-agent responsibility splits, mission state ledgers, mission reviews, workflow evolution proposals, domain goal profiles, site-profile/browser-learning proposals, and evidence-backed mission recommendations. Status is PARTIAL / GOVERNED FOUNDATION IMPLEMENTED / NO LIVE AUTONOMY: no live mission execution, Studio Mission Mode UI, provider/model call, browser skill activation, external send, purchase, listing, payment, live trading, protected-file edit, workflow self-mutation, or canonical promotion was added. A later bounded pass added local AOR dry-review and inert Agent Bus packet preview surfaces only.

**VentureOps Mission Mode local dry-run workspace (2026-05-13):**
The first local Mission Mode dry run now exists for `mission-chase-ai-runtime-governance-kit` under `07_LOGS/VentureOps-Missions/2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run/`. It includes validated manifest, domain profile, sub-agent plan, state ledger, review, proposal-only workflow evolution artifact, site-profile candidate, proof card, scorecard, and boundary flags, plus `runtime.ventureops.mission_dry_runs.validate_mission_dry_run_workspace` and focused tests. Status is LOCAL DRY-RUN VERIFIED / NO LIVE AUTONOMY: the pass did not activate the mission, dispatch AOR, write Agent Bus tasks, apply workflow evolution, call providers, control browsers, send externally, mutate CRM/payment systems, edit protected files, or promote canonical state.

**VentureOps Mission Mode activation/AOR readiness (2026-05-13):**
`chaseos ventureops mission-activation-readiness --mission-workspace PATH --json` checks the dry-run bundle, activation approval state, manifest-promotion/workflow-evolution review state, AOR mission handler presence, and Agent Bus mission dispatch contract presence without executing anything. At the time of the 2026-05-13 readiness pass, live output was READY_FOR_ACTIVATION with valid artifacts, consumed activation approval, consumed manifest-promotion/workflow-evolution review, implemented local AOR dry-review handler, and implemented inert Agent Bus mission packet preview contract. That historical status is superseded by the 2026-05-14 runtime claim/result and activation gates below, which now report `mission_active_local`. Optional `--write-report` output remains create-only and vault-root bounded.

**VentureOps Mission Mode activation approval consumption (2026-05-13):**
`chaseos ventureops mission-activation-approval-consume --mission-workspace PATH --write-approval --consume --json` writes a typed activation approval artifact and exact-once consumption marker for the local Mission Mode gate. Live proof wrote `activation-approval-approved.json` and `activation-approval-consumption.json`, and duplicate consumption blocks on `exact_once_marker_already_present`. This gate clears only `mission_activation_approval_missing`; it did not activate the mission, dispatch AOR, write live Agent Bus tasks, apply workflow evolution, call providers/browsers, send externally, mutate CRM/payment systems, trade, edit protected files, read credentials, or promote canonical state.

**VentureOps Mission Mode manifest-promotion/workflow-evolution review gate (2026-05-13):**
`chaseos ventureops mission-manifest-promotion-review-gate --mission-workspace PATH --write-review --consume --json` now writes a typed review artifact and exact-once marker for the manifest-promotion/workflow-evolution review gate. Live proof wrote `mission-manifest-promotion-workflow-evolution-review-approved.json` and `mission-manifest-promotion-workflow-evolution-review-consumption.json`; duplicate consumption blocks on `exact_once_marker_already_present`. This clears the `mission_manifest_is_draft` and `workflow_evolution_proposal_pending_review` readiness blockers through gate evidence only. It does not mutate `mission-manifest.json`, apply `workflow-evolution-proposal.json`, activate the mission, dispatch AOR, write Agent Bus tasks, call providers/browsers, send externally, mutate CRM/payment systems, trade, edit protected files, read credentials, or promote canonical state. Next gated lane is a separately approved AOR dry-run/dispatch or Agent Bus mission enqueue gate.

**VentureOps Mission Mode runtime claim/result ingestion and local activation gates (2026-05-14):**
`chaseos ventureops mission-runtime-claim-result-gate --mission-workspace PATH --write-approval --consume --claim-task --dispatch-aor --ingest-result --close-task --json` now claims the previously enqueued local Codex `mission.run_dry_review` task exactly once, dispatches only the existing local AOR dry-review handler, ingests the result into the mission workspace, and closes the Agent Bus task to `done`. `chaseos ventureops mission-activation-gate --mission-workspace PATH --write-approval --consume --activate --json` then moves the workspace into local active mission state exactly once. Live proof wrote runtime claim/result and activation artifacts, proved duplicate blocks before redispatch/reactivation, and `mission-activation-readiness --json` now reports `mission_active_local` with no readiness blockers. This is local Mission Mode activation only: no workflow evolution was applied, no provider/model call, browser action, external send, CRM/payment mutation, live trading, credential read, protected-file edit outside declared surfaces, or canonical promotion occurred.

The final external execution runbook now routes the final bundle validation step through `final-evidence-bundle --bundle PATH --write-report --report-path PATH --json`, matching the completion audit's requirement for a discoverable ready validation report. This remains no-execution runbook hardening only.

After a ready final evidence bundle validation, the validator and runbook now route to `feature-family-completion-audit --write-report --report-path PATH --json` so final completion review writes a durable audit report. This does not supply real client or revenue proof.

The final feature-family completion audit report writer is now create-only and vault-root bounded. When `--write-report` is supplied without `--report-path`, it uses a dated `YYYY-MM-DD_ventureops-feature-family-completion-audit-report.json` default and advances to the next suffixed path when that default already exists. This is report-write hardening only and does not supply real client or revenue proof.

The external-readiness audit report writer now follows the same create-only and vault-root-bounded posture. `external-readiness-audit --write-report` blocks existing or escaped report paths, uses a dated `YYYY-MM-DD_ventureops-external-readiness-audit-report.json` default, and advances omitted defaults to the next suffixed path when needed.

The final external execution runbook report writer now follows that same create-only and vault-root-bounded posture. `final-external-execution-runbook --write-report` blocks existing or escaped report paths, uses a dated `YYYY-MM-DD_ventureops-final-external-execution-runbook-report.json` default, and advances omitted defaults to the next suffixed path when needed.

The real evidence closeout readiness report writer now follows that same create-only and vault-root-bounded posture. `real-evidence-closeout-readiness --write-report` blocks existing or escaped report paths, uses a dated `YYYY-MM-DD_ventureops-real-evidence-closeout-readiness-report.json` default, and advances omitted defaults to the next suffixed path when needed.

The operator evidence intake report writer now follows that same create-only and vault-root-bounded posture. `evidence-intake --write-report` blocks existing or escaped report paths, uses a dated `YYYY-MM-DD_ventureops-evidence-intake-report.json` default, and advances omitted defaults to the next suffixed path when needed.

The real-client input manifest report dated default and default collision guard are now exposed as first-class external-readiness and feature-family audit flags. This is audit-surface hardening only; real client scope evidence and live revenue proof are still missing.

The `real-client-input-manifest` command contract now discloses dated default report writes and collision-safe suffixed defaults as separate side effects, and the generated CLI reference/handbook have been refreshed. This is contract/docs hardening only.

The live client and live revenue readiness report writers now follow the same create-only, vault-root-bounded posture. `live-client-proof-readiness --write-report` and `live-revenue-proof-readiness --write-report` block existing or escaped report paths, use dated `YYYY-MM-DD_ventureops-live-*-proof-readiness-report.json` defaults when no report path is supplied, and advance omitted defaults to the next suffixed path when needed. This is blocked-state passover hardening only; real client scope evidence, live client workflow proof, and live revenue proof are still missing.

Client-safe delivery artifact validation is now enforced in the final external proof chain. Delivery proof packet authoring, final completion discovery, and final evidence bundle validation require the referenced client-safe delivery artifact to be a typed redacted JSON object with no side-effect flags, provider/browser actions, revenue claim, unsafe proof path, or secret-shaped keys. This closes an arbitrary-file proof gap only; no real external delivery or revenue proof was supplied.

**What ChaseOS is not yet:**
- A finished standalone Studio product - the native Studio shell exists, parser-backed graph input, typed graph/trust overlays, graph-node provenance inspection, approval-gated node create/edit, approval-gated visual link proposals, approval-gated Runtime Cockpit action-readiness requests, read-only Open Folder compatibility readiness, read-only Obsidian vault detection, read-only general Markdown inference preview, read-only ChaseOS bootstrap wizard preview, proof-temp upgrade approval/execution, native packaged visual QA, product hardening, installer planning, release-readiness governance, installer-build approval artifact write, approval-consumption dry run, approved installer-build execution proof, and governed companion-selection approval consumption are verified, but approval execution/target mutation is not broadly proven, real provider/runtime/browser execution remains deferred, real target-folder/file upgrade execution is still planned or needs explicit deferral, branded installer/logo/icon packaging is not done, and installer/signing/startup/release/host mutation follow-through remains governed future work
- A fully self-governing operating system — scheduled execution and runtime buses exist, but Phase 9 still needs hardening before Phase 10 Studio becomes the product shell
- A general computer-control runtime yet — the SiteOps local browser proof has visible agent-control affordances for the browser lane, but file explorer, OS/system, authenticated browser sessions, and broader compute-control surfaces remain future governed work
- Finished — this is an active framework in development (Phase 8 complete; Phase 9 runtime hardening active)

See [ROADMAP.md](ROADMAP.md) for the full development phase plan.

---

## Technical architecture detail

ChaseOS is a privacy-first agentic operating system and local-first control plane. It is the environment in which a person and permissioned agent runtimes work together: ingesting sources, reasoning over structured workspaces, executing bounded tasks, writing back to canonical state, and generating ideas that stay visibly separate from verified truth.

It is not a note-taking setup. It is not a productivity method. It is not a second brain.

It is an operating system: a set of conventions, routing rules, memory structures, operating files, agent contracts, and enforcement hooks that let a person — and the AI tools they work with — operate coherently across a large, complex, multi-domain life.

**ChaseOS ages with the user.** Most AI tools are useful in the moment. ChaseOS is designed to get more useful over time — because the value lives in the system, not in any single session. As the user keeps learning, building, operating, and writing back into ChaseOS, the system compounds:

- The source archive gets deeper — more material for retrieval-backed reasoning
- The doctrine gets sharper — better decisions with less re-briefing
- The project state stays continuous — agents re-orient in seconds, not minutes
- The operator memory improves — runtimes learn from their own behavioral history
- Cross-domain associations become possible — the graph connects ideas across domains
- Recurring workflow patterns become reusable — what you did manually becomes something the system can support or automate
- Failure-handling patterns accumulate — the system learns from its own mistakes

This is accumulated operating context, not chat memory. The architecture is designed so that useful context is never lost between sessions, never conflated across content types, and never allowed to override governance rules.

The Source Intelligence Core is now complete. ChaseOS already owns local source packages, workspaces, retrieval, and structured outputs rather than delegating that architecture to external platforms. The current major layer is Phase 9/10 hardening and productization: runtime buses, schedules, MCP, scorecards, acquisition/normalization, Studio shell/panel surfaces, parser-backed graph input, and the security posture required before broader governed Studio write/action flows.

**Local-first principle:** User sources and knowledge remain in the user's system. Source packages, indexes, workspace objects, and generated outputs are stored locally. The model provider (Claude, OpenAI, local runtime) is pluggable — it supplies generation and embeddings. It does not own the workspace architecture or the knowledge model. ChaseOS does.

ChaseOS separates four distinct categories that most systems conflate:

- **Raw inputs** — unverified external content held in quarantine until processed
- **Processed knowledge** — source-derived notes and multi-source syntheses with explicit trust labeling
- **Generated ideas** — AI-generated or human+AI hypotheses, theses, and proposals kept visibly separate from verified facts
- **Canonical state** — active project truth, sprint priorities, and operating status

ChaseOS provides:

- **Structured memory** — canonical knowledge, project state, and operating principles stored in a navigable, machine-readable format
- **Knowledge taxonomy** — explicit classification of every knowledge note by origin, trust tier, and verification status
- **Project governance** — each active project has an operating file defining its mission, status, goals, and open loops
- **Context routing** — agents are directed to read specific files rather than loading everything; narrow context, not full context
- **Governed ingestion** — a five-stage pipeline (Quarantine → Triage → Sanitize → Route → Promote) for processing external content
- **Operating discipline** — SOPs, build logs, decision logs, and review cadences that create writeback accountability
- **Agent behavior contracts** — explicit rules governing what AI tools can and cannot do inside the system
- **Mechanical enforcement** — hook scripts, adapter manifests, and runtime policy files enforce the agent contracts at the tool-call level (not just as instructions)
- **Domain operating layers** — 18 named domains, each with its own knowledge base and project structure

---

## What ChaseOS Is Not

- Not an Obsidian plugin or Obsidian-specific product
- Not a generic PKM template
- Not a journaling framework
- Not a productivity methodology
- Not a finished product — it is a living, evolving framework
- Not a replacement for domain expertise — it routes and structures it

---

## Why Obsidian Right Now

Obsidian is currently the default memory backend and visualization layer for ChaseOS.

It was chosen because:
- Files are plain markdown — portable, not locked in
- Vault structure maps cleanly to ChaseOS folder conventions
- Graph view and backlinks support navigation between related context
- Local-first architecture fits the sovereignty requirements of the system
- The plugin ecosystem allows rapid customization without building custom tooling yet

**Obsidian is not the product identity.** ChaseOS is the framework. Obsidian is one implementation of it.

The product identity is **ChaseOS Studio** - a standalone desktop, graph-first operating surface for ChaseOS (Phase 10). The native shell, read-only panel lane, parser-backed graph input, typed graph/trust overlay model, graph-node provenance inspection, approval-gated node create/edit, approval-gated visual link proposal flow, and approval-gated Runtime Cockpit action-readiness request surface are built; general markdown / Obsidian-compatible onboarding previews are built through bootstrap preview; proof-temp workspace upgrade approval/execution is built; persisted graph storage, real target-folder/file upgrade execution, and runtime action execution remain future work. The framework conventions are designed to survive the transition away from Obsidian as the primary interface.

---

## System Layers

```
┌─────────────────────────────────────────────────────────┐
│  ChaseOS Framework                                       │
│  ─────────────────────────────────────────────────────  │
│  Memory Layer      → structured notes, project OS files  │
│  Governance Layer  → SOPs, templates, decision logs      │
│  Context Layer     → Vault Map, routing rules, registry  │
│  Agent Layer       → contracts, permissions, trust levels│
│  Gate Layer        → adapter manifests, hook enforcement │
│  Identity Layer    → SOUL, principles, operating doctrine│
│  Log Layer         → build logs, daily, weekly reviews   │
│  Archive Layer     → history, snapshots, handovers       │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  Feature Families (subsystems + capability layers)       │
│  ─────────────────────────────────────────────────────  │
│  Source Intelligence Core    (Phase 7 — COMPLETE)         │
│    Source Package Layer  → normalized source objects     │
│    Workspace Layer       → grouped source sets           │
│    Retrieval Layer       → evidence-grounded reasoning   │
│    Output Layer          → summary, FAQ, synthesis draft │
│    Provider Adapter      → pluggable model backend       │
│                                                          │
│  Autonomous Operator Runtime (Phase 9 — partial)         │
│    Workflow Registry → manifest-based execution          │
│    Bounded Autonomy  → explicit permission ceilings      │
│    Multi-Repo Policy → declared directory scope          │
│    Audit Trails      → every action logged               │
│    Runtime Navigation Map → evolving per-runtime         │
│      navigational overlay (routes, zones, escalations)   │
│                                                          │
│  Scheduled Briefing Pipelines (Phase 9 — planned)        │
│    Trigger Schedule  → cron or event-based               │
│    Input Adapters    → SIC workspaces, vault, APIs       │
│    Delivery Adapters → Discord, email, dashboard         │
│    Guardrail Profile → fail-closed, audit-required       │
│                                                          │
│  Operator Surface + Runtime Interaction (Phase 9/10)     │
│    Phase 9: Runtime Interaction Contract → event bus     │
│             Action Dispatch Visibility → live view       │
│             Runtime Session Model → resumable sessions   │
│             Approval-Linked Execution → gated confirms   │
│    Phase 10: Operator Shell → browser shell + approvals  │
│              Voice I/O → STT/TTS provider-neutral        │
│              Companion Surface → mobile/tablet access    │
│                                                          │
│  ChaseOS Studio (Phase 10 - active)                      │
│    Native shell + read-only panels through 10W           │
│    Parser-backed graph input complete in 10X             │
│    Typed graph/trust overlays complete in 10Y            │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  Current Implementation: Obsidian Vault                  │
│  (default memory backend + visualization interface)      │
└─────────────────────────────────────────────────────────┘
```

---

## Major Domains

ChaseOS currently operates across 18 named domains (A–R):

| ID | Domain | Description |
|----|--------|-------------|
| A | ChaseOS / System Infrastructure | The operating system itself |
| B | Market Operations | Trading, market research, and risk-review workflows |
| C | Community / Signal Products | Audience, membership, and distribution workflows |
| D | Indicator R&D / Technical Tooling | Custom indicators, strategy research, and tool prototypes |
| E | Autonomous Trading Systems | Agent-assisted trading research and governed execution design |
| F | Macro Intelligence | Cross-market macro intelligence and dashboard workflows |
| G | AI / Agent Engineering | Agent architecture, tooling, systems |
| H | Full-Stack / Software Engineering | Web2, Web3, and product engineering workflows |
| I | Security Research | Offensive security, blockchain security, and vulnerability workflows |
| J | Learning / Credential Ops | Structured study, credential, and education workflows |
| K | Career / Client Ops | Internship, freelance, and client-service positioning |
| L | Content Engine | Research-to-content and distribution workflows |
| M | Businesses / Ventures | Active, paused, and legacy venture operations |
| N | Hardware / Robotics / Future Systems | GPU, embedded, robotics, and future system tracks |
| O | Doctrine / Philosophy / Identity | Operating principles and identity templates |
| P | Physical Discipline | Training, health, and performance standards |
| Q | Network / Relationship Ops | Relationship and professional-network workflows |
| R | Language / Mobility Ops | Language learning and international optionality workflows |

---

## Core vs Personal

ChaseOS now treats Core/Personal as an active structural separation lane, not only a concept.

### ChaseOS Core
The public, forkable, reusable framework.

Contains: folder conventions, note type definitions, routing rules, operating principles, agent behavior contracts, templates, boilerplate structure, and forking guidance.

This layer is meant to be standardized, version-controlled, and usable by anyone willing to populate it with their own context. The current Core extraction lane is controlled by `CORE_MANIFEST.md`, `core_export/export_manifest.yaml`, `core_export/core_candidate_inventory.yaml`, scanner/sanitizer policy, curated templates under `core_export/templates/`, and rendered review artifacts under `core_export/reports/latest/`.

### ChaseOS Personal
The private, populated instance.

Contains: real projects, real priorities, personal doctrine, private operating history, personal logs, individualized knowledge, and private workflows.

This layer is specific to each operator or organization and is not intended to be shared publicly as-is. It follows the Core conventions while being populated with private operational context.

The active development workspace is the source workspace for validating ChaseOS Core/Personal separation. Guarded Core export targets are inspection/export-candidate outputs only; they are not public, not authoritative, and not Git repositories unless a later explicit Git-init gate approves that step. The latest Core export tracker records 57 manifest candidates/previews, 0 scanner blockers, a guarded local export update, a recorded verify-export pass, and Git/commit/remote/push/publication still unapproved; the latest revalidation found the export target and manual review artifact missing, so current verify-export is blocked until restored through the guarded export lane.

See [FORKING.md](FORKING.md) for how to create your own instance.

---

## Where This Project Is

ChaseOS is currently in **Phase 9 — Operator Runtime (AOR + SBP) — active implementation**. Phases 1–8 are complete. Phase 7 (Source Intelligence Core) and Phase 8 (Connector / Capture Automation) are fully operational.

Phase 6 built the governed ingestion architecture, ChaseOS Gate (ACTIVE VERIFIED), knowledge taxonomy (six classes), and operational SOPs. Phase 7 delivered the full SIC stack. Phase 8 delivered the capture and connector automation layer. A Phase 9 planning pass was completed 2026-03-31, producing `06_AGENTS/Phase9-Adopted-Feature-Specification.md` — full specification for 17 adopted Phase 9 features across governance infrastructure, AOR workflows, and data governance layers.

**Phase 7 engineering progress (SIC — COMPLETE 2026-03-26):**
- Pass 1: Architecture kickoff — SIC-Architecture.md, schemas, runtime/source_intelligence/ structure ✅
- Pass 2: Source Package Builder MVP ✅
- Pass 3: Workspace Management ✅
- Pass 4: Index Contract + Embedding State ✅
- Pass 5: Local Retrieval Contract + Evidence Query Layer ✅
- Pass 6: Output Generation Layer (StubGenerationAdapter + AnthropicGenerationAdapter, 7 output types) ✅
- Pass 6B: Output Persistence + Contract Alignment (output_store.py, generate_and_persist) ✅
- Pass 7: Embedding Backend Abstraction + Benchmark (LocalWordEmbedder, OpenAIEmbedder, backend_registry) ✅

**What is already built and operational:**
- Full 18-domain folder hierarchy and naming conventions
- `CLAUDE.md` routing anchor for Claude Code (v2.0)
- `SOUL.md` identity layer
- `00_HOME/` control files (Now.md, Operating-System.md, Dashboard.md, Principles.md, Assistant-Contract.md)
- Project OS files for all major active domains
- Knowledge index files across all active domains
- SOPs: Build-Log-SOP, Research-Ingest-SOP v2.1, Promotion-Session-SOP v1.0, Ingestion-Cadence v1.0
- Templates: Project-OS, Decision-Log, Experiment, Source-Note, Synthesis-Note, Generated-Idea, Daily-Note, Trade-Journal-Entry
- Agent control plane in `06_AGENTS/`: registry, vault map, tool map, permission matrix, trust tiers, handoff protocol, backends matrix
- Knowledge taxonomy — six knowledge classes, mandatory frontmatter schema, generated-ideas layer
- Active five-stage ingestion pipeline (`03_INPUTS/` → triage → sanitize → route → `02_KNOWLEDGE/`)
- ChaseOS Gate — Anthropic lane ACTIVE VERIFIED: hook scripts enforcing protected-file writes and ingestion promotion guard
- Claude persistent memory seeded: project state, writeback discipline, user profile
- Active build log discipline in `07_LOGS/Build-Logs/`

**Phase 8 engineering (COMPLETE 2026-03-31):**
- Passes 1–10: capture pipeline, operator CLI, quarantine boundary, sidecar v8.3, semantic breadcrumbs, RSS/Atom connector, SHA-256 dedup registry, browser/HTML connector, Perplexity API connector, watched-folder automation, Grok/xAI API connector ✅
- 485 tests, 0 failures; `06_AGENTS/Feature-Fit-Register.md` created ✅

**What is not yet built (honest boundaries):**
- Autonomous Operator Runtime — first-wave bounded workflows are live (Passes 1–4, 2026-04-09); Graph Substrate subsystem built (Passes 1+2, 2026-04-10); native schedule intent is built in `runtime/schedules/` (2026-04-15); Operator Briefing V2 handlers are live (2026-04-17); Runtime MCP V1 scaffold is built in `runtime/mcp/` (2026-04-20), with `workflow.invoke_bounded` active V2 for `operator_today`/`operator_close_day` as of 2026-04-21; event-triggered workflow infrastructure now has bounded queue/rule/schedule readiness surfaces, but broad event-triggered execution remains gated.
- Scheduled Briefing Pipelines — `operator_today` and `operator_close_day` are live; broader SBP consumer wiring and briefing-family expansion remain partial/gated and are tracked as NB-002/NB-021 in `docs/features/chaseos_not_built_backlog.md`.
- What's-missing Release Matrix — Studio now has a read-only `Release Matrix` panel/API/catalog entry for NB-001 through NB-043 posture, with UI/UX proof at `07_LOGS/Visual-QA/2026-06-12-nb001-043-release-matrix-closeout/`. Current parsed matrix: 43 rows total, 17 implemented-or-preview, 26 blocked-or-gated, 0 needs-review, and 43 Studio-wired-or-mapped; public beta remains **NO-GO** until Ship/Ship-Minimum gates are verified.
- Phase 9 first-wave governance infrastructure — BUILT/PARTIAL by lane: Workflow Registry has a read-only completion inspector; Agent Role Cards have registry/readiness surfaces but still need coverage refresh; Task-Type Router, Decision Ledger, Feature Filter, and Project Pivot Log are implemented.
- Phase 9 first-wave workflow handlers — BUILT in bounded form: `operator_today` and `operator_close_day` write operator briefs; `graph_hygiene` writes hygiene reports only; `graduate_ideas` writes graduation proposals only.
- Phase 9 second-wave features (Provenance Schema, Context Governance Layer, Agent Scorecards, Meeting Ingest Linker, trace_idea, drift_scan) — no longer blanket-deferred: several readiness/proof/status surfaces exist, but integrated execution and score application remain gated.
- Agent Memory Architecture — Layers C and D are formalized; read-only memory/identity inspection exists, and `chaseos memory structure` now proves the Layer C/D file-structure homes are present with missing_paths `[]`. Memory mutation, runtime dispatch, approval consumption, and canonical promotion remain gated.
- Agent Identity Ledger — seeded operationally under `runtime/memory/adapters/` with read-only inspection; automated drift scoring and mutation workflows remain deferred.
- Runtime Navigation Map — architecture defined (2026-03-25); implementation foothold seeded 2026-04-24 via `runtime/memory/nav/` + runtime profile docs; Studio now surfaces accumulated route-pattern evidence read-only, while curation/writeback remains Phase 9 governed work.
- Multi-Repo / Multi-Directory Policy enforcement — schema defined; enforcement is Phase 9
- Layer C durable generated artifacts (`02_KNOWLEDGE/[Domain]/Generated-Ideas/`) — architecture defined; directories created lazily on first promotion
- ChaseOS Studio (Phase 10) - native shell and read-only panels are implemented through Pass 10W, parser-backed graph input is complete in Pass 10X, typed graph/trust overlays are complete in Pass 10Y, read-only graph provenance inspection is complete in Pass 10Z, approval-gated node create/edit is complete in Pass 10AA, approval-gated visual link proposals are complete in Pass 10AB, Runtime Cockpit action readiness is complete in Pass 10AC, ChaseOS bootstrap wizard preview is complete in Pass 10F4, and proof-temp workspace upgrade approval/execution is complete in Pass 10F5/10F6; persisted graph storage, real target-folder/file upgrade execution, runtime action execution, and runtime/adapter activation remain future work
- Core/Personal structural separation — ACTIVE / PARTIAL: implementation plan, `CORE_MANIFEST.md`, `core_export/` allowlist machinery, candidate inventory, scanner-clean dry-run previews/reports, templates, and evidence for a guarded local Core export candidate exist; the current tracked packet is 57 manifest candidates/previews with 0 scanner blockers and a last recorded verify-export pass. The latest revalidation found the guarded export target and manual review artifact missing, so current verification is blocked until restored through the guarded export lane. Git initialization, public repository setup, license choice, public `.gitignore`, remote creation, push/publication, and canonical promotion remain separate approval gates.
- Gate enforcement beyond the Anthropic lane - runtime operation policy foothold is active for agent-bus mutation paths plus bounded setup/config/schedule/scaffold draft/browser read-screenshot paths; broader gateway/Studio/lifecycle/browser-action side-effect coverage remains Phase 9 hardening

See [ROADMAP.md](ROADMAP.md) for the full development phases.

---

## Knowledge Classification

ChaseOS classifies every piece of knowledge in the vault by its origin and trust level. This prevents raw research, verified facts, AI-generated ideas, and active project state from being conflated.

| Class | What it is | Default trust |
|-------|-----------|---------------|
| `user-origin` | Directly authored or explicitly endorsed by the user | High |
| `source-derived` | Processed from a single outside source | Tier 3 — verify before citing |
| `synthesized` | Combined from multiple sources or platform synthesis | Tier 3 — flag unverified claims |
| `generated-ideas` | AI-generated or human+AI hypotheses, theses, proposals | Tier 3 — not canonical without endorsement |
| `system-operational` | Framework SOPs, policies, templates, runtime logic | Tier 2 — framework authority |
| `canonical-state` | Active project state, roadmap, sprint priorities | High — current authoritative truth |

Every promoted knowledge note in `02_KNOWLEDGE/` carries `knowledge_class` in frontmatter.
The full taxonomy, frontmatter schema, and generated-ideas rules: `06_AGENTS/Knowledge-Taxonomy.md`

---

## How to Read ChaseOS — Key Terms

A short vocabulary for working with the system. These terms have precise meanings here — conflating them is the main source of confusion about trust levels and content types.

| Term | What it means |
|------|---------------|
| **Raw input** | Unprocessed external content in `03_INPUTS/` — untrusted by default until triaged |
| **Source note** | A processed note from a single external source — article, video, lecture, or transcript |
| **Synthesis note** | A note combining multiple sources or a platform synthesis output (NotebookLM, Perplexity digest) |
| **Idea Generation** | An AI-generated or human+AI hypothesis, thesis, or proposal — not a verified fact; kept visibly separate from processed knowledge |
| **Canonical state** | Active, verified project truth — project OS files, `Now.md`, `ROADMAP.md` — what the system currently believes is true |
| **Knowledge class** | A tag on every knowledge note classifying its origin and trust level: how it was made, how much to trust it |
| **Promotion** | Moving content from `03_INPUTS/` quarantine into `02_KNOWLEDGE/` after passing a four-condition gate; always human-approved |
| **Trust tier** | An authority ceiling — Tier 4 = untrusted external input, Tier 3 = research starting point, Tier 2 = operational framework |
| **The Gate** | The enforcement control layer: hook scripts and adapter manifests that block policy violations at the tool-call level |
| **Domain** | One of ChaseOS's 18 named knowledge areas — each has a knowledge index file and a project OS file |

**One example pass:** You find a useful YouTube lecture. Drop the transcript in `03_INPUTS/Transcript-Raw/`. In an ingestion session: triage it (source identified, no injection detected), sanitize it (unverified claims labeled), promote it to `02_KNOWLEDGE/Trading-Systems/` as a source note with `knowledge_class: source-derived`. The domain index gets updated. Action items surface to you for routing. The raw file keeps a PROCESSED banner as an audit trail.

---

## Why ChaseOS Is More Than AI Memory

Most AI memory tools store what you've told them and surface it later. ChaseOS is a different category.

**Local-first sovereignty.** User sources, knowledge, indexes, and workspace objects stay on the user's machine. Model providers (Claude, OpenAI, local runtimes) supply generation and embeddings — they do not own the data, define the workspace, or set governance rules. The knowledge is not delegated to a platform.

**Governed writeback.** Information that exists only in a chat window does not exist in ChaseOS. Every output from every session must be written to the vault. The Gate enforces this mechanically — hook scripts block unintended writes and require promotion approval for knowledge promotion. Discipline is structural, not volitional.

**Explicit content separation.** ChaseOS separates raw inputs, processed knowledge, AI-generated ideas, and canonical project state. These categories are never conflated. An AI-generated hypothesis is not treated as a verified fact until the user explicitly endorses it. Raw research is not the same as promoted knowledge. This separation makes the system trustworthy.

**Inspectable provenance.** Every output should eventually trace back to its inputs — the source packages, doctrine notes, memory clusters, workspace context, and prior outputs that produced it. ChaseOS is building toward a system where nothing is a black box. You can ask what the system used to derive something.

**Multi-runtime control plane.** ChaseOS is not built for one model or one provider. The same governance layer, Gate enforcement, taxonomy, and writeback discipline applies regardless of whether Claude, OpenAI, or a local model is the active runtime. The control plane is provider-agnostic.

**Ingress surfaces vs coordination substrate.** Discord is the current shared control/visibility transport, but it is not intended to remain the permanent control-field identity. ChaseOS is moving toward a model where many ingress surfaces may exist (Discord, CLI/runtime shell, future Studio/operator panels, future companion surfaces), while actionable coordination-sensitive work is translated into ChaseOS-owned structured state such as `runtime/agent_bus/` rather than being tracked in chat threads or transport-local state.

**Default coordination rule.** When one runtime participates through multiple ingress lanes (for example `hermes-chat`, a thread under `hermes-chat`, and shared `chaseos-ops`), runtime-only arbitration is not enough. By default, ChaseOS coordination-sensitive work should be represented with ingress/work-item context — channel, thread/topic, conversation identity, and work fingerprint — so present and future runtimes can deconflict work on the real unit of coordination.

**Personalization that compounds.** The system gets more useful as source archives deepen, doctrine sharpens, operator memory accumulates, and recurring workflows become patterns. This is not about better prompts. It is about accumulated operating context that the system can use across all future sessions.

**Runtime behavior that is inspectable and improvable.** Through the Agent Identity Ledger (planned), every runtime accumulates a behavioral record — what it does well, where it fails, what corrections have been applied. A system you can inspect is a system you can improve.

---

## Getting started

Start by reading the brand foundation, current repo truth, and the current operating state before changing code or docs:

- [docs/brand/README.md](docs/brand/README.md)
- [PROJECT_FOUNDATION.md](PROJECT_FOUNDATION.md)
- [ROADMAP.md](ROADMAP.md)
- [00_HOME/Now.md](00_HOME/Now.md)
- [06_AGENTS/Vault-Map.md](06_AGENTS/Vault-Map.md)

For local CLI setup and package entrypoints, keep using the existing install/setup docs in this repository, including [CLI-INSTALL-README.md](CLI-INSTALL-README.md), [SETUP-INSTRUCTIONS.md](SETUP-INSTRUCTIONS.md), and the command surfaces below.

## Development

### ChaseOS Shell Commands and Runtime Command Surfaces

This section is split deliberately so the README stays honest.
Some command surfaces are directly evidenced in this repository today, while others are documented as part of the broader ChaseOS implementation history and architecture.

### Proven / directly inspectable from this repo

Canonical command spine: `runtime.cli.main:main` (installed as `chaseos` and `chase`). Direct shims `python chaseos.py ...` and `python runtime\\cli.py ...` route to the same parser.

Canonical `--json` output uses the ChaseOS envelope `ok`, `action`, `result`, `errors`, `warnings`, and `audit_id`; detailed command payloads live under `result`.

Machine-readable parser truth now lives at `runtime/cli/command_contract.json`; `runtime/tests/test_cli_command_contract.py` verifies it against the canonical parser so command-path, alias, argument, JSON-shape, side-effect, and maturity drift is deliberate. The generated command reference lives at `06_AGENTS/ChaseOS-CLI-Command-Reference.md`; regenerate with `python -m runtime.cli.generate_docs --write` and check drift with `python -m runtime.cli.generate_docs --check`. Routine local CLI preflight is `python -m runtime.cli.main doctor cli --json`; the full contract/docs/action/smoke ratchet is `python -m runtime.cli.main doctor cli --contract-ratchet-smoke --json` or `python -m runtime.cli.main test cli-contract --json`.

| Command Surface | Status | How to inspect or run |
|----------------|--------|------------------------|
| `chaseos runtime inventory --json` | Live in repo | Lists discovered runtime lifecycle records from canonical CLI |
| `chaseos runtime status --runtime all --json` | Live in repo | Resolves bounded runtime state through canonical CLI |
| `chaseos runtime provider-status --runtime all --json` | Live in repo | Reports runtime provider/fallback governance, provider-state ledger posture, queue/stuck/no-chunk posture, and adapter health without mutating runtime state |
| `chaseos runtime workspace-mode route-preview --workspace-path PATH --workflow-id WORKFLOW_ID --adapter codex --json` | Live in repo | Shows read-only WML/AOR routing posture without workflow dispatch, Agent Bus task write, approval consumption, external action, or canonical writeback |
| `chaseos runtime workspace-mode rollout-plan --json` | Live in repo | Shows a review-only first-profile rollout plan with proposed profile paths and draft payloads; writes no profile file and enables no dispatch |
| `chaseos runtime workspace-mode draft-packet --json` | Live in repo | Shows validated draft YAML for selected WML profiles with no profile file write, overwrite, approval consumption, or dispatch |
| `chaseos runtime workspace-mode write-approval-request --json` | Live in repo | Shows a pending profile-write approval request packet for selected WML profiles with no profile file write, dispatch, approval consumption, or canonical writeback |
| `chaseos runtime workspace-mode write-profiles --gate-approval-id ID --confirm --json` | Live in repo | Create-only guarded writer for approved WML profiles; duplicate writes block and no AOR dispatch, Agent Bus task, approval consumption, provider/model call, browser/external action, or canonical writeback occurs |
| `chaseos runtime workspace-mode dispatch-gate --workspace-path PATH --workflow-id WORKFLOW_ID --adapter codex --confirm --json` | Live in repo | Clears or blocks a WML/AOR dispatch request without calling `run_workflow`, executing a workflow, writing workflow output, writing Agent Bus tasks, consuming approvals, or performing external/canonical action |
| `chaseos runtime workspace-mode dispatch-dry-run --workspace-path PATH --workflow-id WORKFLOW_ID --adapter codex --confirm --json` | Live in repo | Re-runs the WML dispatch gate and calls AOR only with `dry_run=True`; writes AOR dry-run audit evidence but does not execute handlers, write workflow output, write Agent Bus tasks, consume approvals, or perform external/canonical action |
| `chaseos runtime workspace-mode live-execution-approval-gate --workspace-path PATH --workflow-id WORKFLOW_ID --adapter codex --confirm --json` | Live in repo | Shows or writes a pending exact-scope WML live AOR execution approval request; does not call live `run_workflow`, execute handlers, write workflow output, consume approvals, write Agent Bus tasks, or perform external/canonical action |
| `chaseos runtime workspace-mode live-executor --workspace-path PATH --workflow-id WORKFLOW_ID --adapter codex --gate-approval-id ID --decision approved --write-approval-decision --write-approval-consumption --write-consumption-marker --confirm --json` | Live in repo | Consumes an exact-scope approved WML live AOR execution packet once, re-runs the dispatch gate, binds fresh AOR dry-run evidence, reserves an exact-once marker, then calls live AOR for the approved workflow only; duplicate execution blocks before `run_workflow` |
| `chaseos runtime health --runtime <id> --json` | Live in repo | Runs runtime lifecycle health probe through canonical CLI |
| `chaseos setup provider list --json` | Live in repo | Lists setup provider records through canonical CLI |
| `chaseos config set default_provider openai --json` | Live in repo | Bounded config mutation now passes deny-by-default runtime operation policy |
| `chaseos schedule enable sch-operator-today-0700 --json` | Live in repo | Schedule state mutation now passes deny-by-default runtime operation policy |
| `chaseos scaffold project "Alpha Core" --json` | Live in repo | Draft scaffold generation now passes deny-by-default runtime operation policy before writing under `runtime/scaffold/generated/` |
| `chaseos operate browser screenshot https://example.com --json` | Live in repo | Bounded browser artifact writes now pass deny-by-default runtime operation policy |
| `chaseos gate validate --json` | Live in repo | Validates adapter manifests through canonical CLI |
| `chaseos gate check-operation <operation> --json` | Live in repo | Deny-by-default runtime operation policy smoke check |
| `chaseos doctor cli --json` | Live in repo | Fast CLI preflight for installed `chaseos` / `chase`, pyproject scripts, and compatibility shims; use `--contract-ratchet-smoke` for full parser/contract/docs/action/smoke alignment |
| `python runtime\\chaseos_gate.py validate` | Live in repo | Validates adapter manifests |
| `python runtime\\chaseos_gate.py list` | Live in repo | Lists registered adapter manifests |
| `python runtime\\chaseos_gate.py show <adapter-id>` | Live in repo | Shows a manifest |
| `python runtime\\chaseos_gate.py check-write <adapter-id> <file-path>` | Live in repo | Checks write permission |
| `python runtime\\chaseos_gate.py check-task <adapter-id> <task-type>` | Live in repo | Checks task-type permission |
| `python runtime\\state\\resolver.py` | Live in repo | Resolves and writes `runtime/state/current_state.json` |
| `python runtime\\state\\runtime_cli.py resolve` | Live in repo | Resolves runtime state |
| `python runtime\\state\\runtime_cli.py status` | Live in repo | Shows runtime status summary |
| `python runtime\\state\\runtime_cli.py status --refresh --json` | Live in repo | Refreshes and prints full runtime state JSON |
| `python runtime\\cli.py runtime health --runtime <id> --json` | Compatibility shim | Routes to canonical `runtime.cli.main` parser |
| `python runtime\\cli.py runtime health-debug --runtime <id> --json` | Compatibility shim | Routes to canonical `runtime.cli.main` parser |
| `python chaseos.py runtime health --runtime <id> --json` | Compatibility shim | Routes to canonical `runtime.cli.main` parser |

### Documented / broader ChaseOS command surfaces

These are referenced in the framework docs and README history, but should be treated as broader ChaseOS command surfaces whose exact availability depends on the active implementation environment:

- `chaseos capture file`
- `chaseos capture stdin`
- `chaseos capture rss URL [--limit N]`
- `chaseos capture browser file PATH`
- `chaseos capture perplexity --query "..."`
- `chaseos capture grok --query "..."`
- `chaseos watch add PATH --class CLASS`
- `chaseos watch run --once`
- `chaseos intake ls`
- `chaseos intake inspect`
- `chaseos intake dedup-stats`
- `chaseos doctor`
- `chaseos test capture`
- `chaseos run <workflow>`
- runtime command contract: `chaseos runtime resolve`, `chaseos runtime status`, `chaseos runtime health`

For the new runtime-state command family, read:
- `runtime/state/CLI-README.md`
- `runtime/state/COMMAND-CONTRACT-README.md`
- `06_AGENTS/ChaseOS-Runtime-Command-Contract.md`

For the broader command inventory, read:
- `runtime/COMMANDS.md`
- `CLI-SURFACES.md`
- `runtime/COMMANDS-README.md`
- `runtime/CLI-README.md`
- `runtime/LIFECYCLE-README.md`
- `runtime/lifecycle/README.md`
- `CHASEOS-COMMAND-README.md`

## Documentation

### What to Read First

| If you want to understand... | Read |
|------------------------------|------|
| The full framework philosophy | [PROJECT_FOUNDATION.md](PROJECT_FOUNDATION.md) |
| Development phases and direction | [ROADMAP.md](ROADMAP.md) |
| How to fork this for yourself | [FORKING.md](FORKING.md) |
| Agent identity template | [SOUL.template.md](SOUL.template.md) |
| How to navigate the vault | `06_AGENTS/Vault-Map.md` |
| Workspace modes and mode-aware routing | `06_AGENTS/Use-Case-Mode-Architecture.md`, `06_AGENTS/Workspace-Mode-Profile-Standard.md`, `runtime/workspace_modes/` |
| Agent behavior rules | `00_HOME/Assistant-Contract.md` |
| Agent output conventions (all backends) | `06_AGENTS/Agent-Output-Conventions.md` |
| Which AI backends/surfaces are supported | `06_AGENTS/Backends-Supported.md` |
| Knowledge taxonomy and note classification | `06_AGENTS/Knowledge-Taxonomy.md` |
| Current sprint priorities | `00_HOME/Now.md` |
| Full domain operating system | `00_HOME/Operating-System.md` |
| Feature families and their status | `06_AGENTS/Feature-Register.md` |
| Phase 9 adopted feature specification (all 17 features) | `06_AGENTS/Phase9-Adopted-Feature-Specification.md` |
| Operator Surface + Runtime Interaction Layer architecture | `06_AGENTS/Operator-Surface-Runtime-Interaction.md` |
| Phase/layer triage register | `06_AGENTS/Feature-Fit-Register.md` |
| Multi-layer memory architecture | `06_AGENTS/Agent-Memory-Architecture.md` |
| Scheduled Briefing Pipelines architecture | `06_AGENTS/Scheduled-Briefing-Pipelines.md` |
| Autonomous Operator Runtime architecture | `06_AGENTS/Autonomous-Operator-Runtime.md` |
| Operator Briefing v2 architecture | `06_AGENTS/Operator-Briefing-Architecture.md` |
| Native Scheduling Intent architecture | `06_AGENTS/Scheduling-Intent-Architecture.md` |
| Runtime commands and shell surfaces | `runtime/COMMANDS.md`, `CLI-SURFACES.md`, `runtime/COMMANDS-README.md`, `runtime/CLI-README.md`, `runtime/LIFECYCLE-README.md`, `runtime/state/CLI-README.md`, `CHASEOS-COMMAND-README.md` |
| ChaseOS MCP Server architecture + V1 stdio scaffold | `06_AGENTS/ChaseOS-MCP-Server.md`, `runtime/mcp/` |
| Graph Substrate architecture | `06_AGENTS/Graph-Substrate-Architecture.md` |
| Runtime Navigation Map architecture | `06_AGENTS/Runtime-Navigation-Map.md` |
| Runtime profile + nav scaffolds | [[Hermes-Runtime-Profile]], [[OpenClaw-Runtime-Profile]], [[Codex-Runtime-Profile]], `runtime/memory/nav/` |
| Browser autonomy governance | `06_AGENTS/Browser-Autonomy-Policy.md`, `06_AGENTS/Browser-Task-Patterns.md`, `runtime/browser_registry/` |
| Dual-runtime coordination substrate | `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`, `runtime/agent_bus/`, `06_AGENTS/Runtime-Agent-Bus-and-Coordination-Standalone-Application.md` |
| How control-panel input should translate into structured ChaseOS state | `06_AGENTS/Control-Plane-Ingress-and-Bus-Translation.md`, `runtime/agent_bus/README.md` |
| Core/Personal split implementation | `06_AGENTS/Core-Personal-Split-Implementation-Plan.md`, `CORE_MANIFEST.md`, `core_templates/` |
| Core-vs-Personal operator views and export surfaces | `06_AGENTS/Core-Personal-Operator-Views-and-Export-Surfaces-Standalone-Application.md` |
| Project cockpit + workspace browser surfaces | `06_AGENTS/Project-Cockpit-and-Workspace-Browser-Standalone-Application.md` |
| Consolidated operator cockpit surface | `06_AGENTS/Consolidated-Operator-Cockpit-Standalone-Application.md` |
| Knowledge navigator + domain browser surfaces | `06_AGENTS/Knowledge-Navigator-and-Domain-Browser-Standalone-Application.md` |
| Settings / provider-config / scaffold surfaces | `06_AGENTS/Settings-Provider-Config-and-Scaffold-Surfaces-Standalone-Application.md` |
| Governed promotion / review center surfaces | `06_AGENTS/Governed-Promotion-and-Review-Center-Standalone-Application.md` |
| Cross-panel object-model consolidation | `06_AGENTS/Cross-Panel-Object-Model-Consolidation.md` |
| Agent scorecards / runtime quality surfaces | `06_AGENTS/Agent-Scorecards-and-Runtime-Quality-Surfaces-Standalone-Application.md` |
| Execution repair / failure recovery surfaces | `06_AGENTS/Execution-Repair-and-Failure-Recovery-Surfaces-Standalone-Application.md` |
| Memory inspector / runtime-memory surfaces | `06_AGENTS/Memory-Inspector-and-Runtime-Memory-Surfaces-Standalone-Application.md` |
| Agent identity ledger surfaces | `06_AGENTS/Agent-Identity-Ledger-Surfaces-Standalone-Application.md` |
| Graph-native node and edge consolidation surfaces | `06_AGENTS/Graph-Native-Node-and-Edge-Consolidation-Surfaces-Standalone-Application.md` |
| Memory editing / curation surfaces | `06_AGENTS/Memory-Editing-and-Curation-Surfaces-Standalone-Application.md` |
| Core export sync doctrine | `06_AGENTS/Core-Export-Sync-Procedure.md` |
| Markdown -> standalone bridge | `06_AGENTS/Markdown-to-Standalone-Bridge.md` |
| Source Intelligence Core architecture | `06_AGENTS/SIC-Architecture.md` |
| ChaseOS VentureOps business/application layer | `06_AGENTS/VentureOps-Architecture.md`, `06_AGENTS/VentureOps-Instance-Intelligence.md`, `06_AGENTS/Workflow-Recommendation-Engine.md`, `06_AGENTS/Revenue-Workflow-Registry.md`, `06_AGENTS/Workflow-Pack-Standard.md` |

---

## 2026-04-27 Adapter Foundation Truth

- OpenAI adapter foundation added as a shadow/dry-run surface: `openai_operator_research_shadow`, OpenAI policy/config, role card, and Responses API MCP payload builder exist; no live OpenAI API call is enabled.
- ChaseOS Runtime MCP now exposes additional ChaseOS-named safe resources/tools/prompts for adapter use, a unit-tested JSON-RPC stdio wrapper for core MCP methods, and a local subprocess stdio client smoke proof; it remains internal infrastructure, not a public MCP deployment.
- n8n MCP hub policy, workflow exposure registry, connection readiness harness, approval-aware dry-run call governance, and redacted proof artifact runner exist; the current workspace proof blocks live probing because no n8n instance/access token is configured. Governed n8n call drafts are audit-only; no production workflow or live Discord/Telegram send is configured.
- ChatGPT Apps SDK remains a future UI layer; no ChatGPT app is built or deployed.

## Current Limitations

- The framework is still Obsidian-backed in its current implementation, but ChaseOS Studio now has a native shell/read-only panel lane, parser-backed graph input, typed graph/trust overlays, graph-node provenance inspection, approval-gated node create/edit, approval-gated visual link proposals, and approval-gated Runtime Cockpit action-readiness requests, and read-only ChaseOS bootstrap preview. The full standalone governed product experience is still incomplete.
- Agent workflows are defined contractually but not yet automated — agents operate on instruction, not on schedule
- Context routing is partly formalized by the Workspace Mode Layer (`runtime/workspace_modes/`), safe path inference, route preview, profile rollout/draft/write gates, WML/AOR dispatch gate, dry-run executor, live-execution approval request gate, and the exact-once WML live executor (`chaseos runtime workspace-mode live-executor`). The first three approved runtime foundation profiles now exist at `runtime/.workspace-mode.yaml`, `06_AGENTS/.workspace-mode.yaml`, and `01_PROJECTS/ChaseOS/workspace-mode.yaml`; approved packet `wml-aor-live-exec-appr-58147fa104e8514d` was consumed once for `operator_today`, producing live AOR audit `96064d06-81fc-4939-9061-3c6fd958149e` and `07_LOGS/Operator-Briefs/2026-05-14-operator-today.md`. This is exact-scope proof only, not broad live runtime autonomy.
- Input capture is partially automated — the Phase 8 connector stack (`chaseos capture`, `watch_folders.py`, RSS/browser/API connectors) automates content intake into quarantine; full autonomous operator workflows (scheduled SIC ingestion, idea graduation, vault maintenance) are Phase 9
- The Core/Personal split is no longer merely conceptual: structural separation is an active development lane with `core_export/` machinery, scanner-clean preview/report artifacts, Core templates, and 2026-05-01 evidence for a guarded local `chaseos-core` export candidate. Remaining limitations are export-state reconciliation plus governance/publication gates: restore/revalidate the guarded local export target and manual review artifact through the approved export lane, then address license decision, public ignore policy, Git-init approval, public repo setup, and canonical promotion.
- The markdown -> standalone mapping layer is now explicitly documented in `06_AGENTS/Markdown-to-Standalone-Bridge.md`, but the standalone surface itself remains unbuilt

---

## Roadmap Summary

1. **Foundation** — folder structure, conventions, core OS files *(complete)*
2. **Vault Governance** — SOPs, templates, agent contracts, routing rules *(complete)*
3. **Project Canonicalization** — all active projects fully documented in Project-OS format *(complete)*
4. **Agent Control Plane** — formal agent registry, permission layers, execution contracts *(complete)*
5. **Repo / Runtime Binding** — execution adapter standard, Claude/OpenAI/Local/n8n adapters, memory system, hooks *(complete)*
6. **Input / Memory Ingestion** — ingestion architecture, five-layer pipeline, ChaseOS Gate enforcement layer, knowledge taxonomy, operational SOPs *(complete)*
7. **Source Intelligence Core** — local-first source packages, workspace grouping, retrieval-backed reasoning, structured outputs, pluggable provider adapter *(complete — all 7 passes done 2026-03-26)*
8. **Connector / Capture Automation** — operator CLI (`chaseos`), quarantine boundary, sidecar provenance, semantic breadcrumbs, AI-generated output bridge, RSS/Atom connector, SHA-256 dedup registry, browser/HTML connector, Perplexity API connector, watched-folder automation, Grok/xAI API connector *(COMPLETE — all 10 passes done 2026-03-31; 485 tests)*
9. **Operator Runtime** — Autonomous Operator Runtime (8-stage engine live; first-wave workflows live) + Graph Substrate subsystem (87 tests; advisory narrowing seam) + Operator Briefing V2 handlers live + Native Scheduling Intent implementation live + ChaseOS MCP Server architecture + Scheduled Briefing Pipelines (pipeline schema defined; implementation pending) + adopted feature set (17 features) + OSRIL Phase 9 subset *(ACTIVE — MCP implementation and event-triggered workflows next)*
10. **ChaseOS Studio (Interface / Experience Layer)** - native PyWebView shell/read-only panel lane through Pass 10W plus Pass 10X parser-backed graph input, Pass 10Y typed graph/trust overlays, Pass 10Z graph-node provenance inspection, Pass 10AA approval-gated node create/edit, Pass 10AB approval-gated visual link proposals, Pass 10AC approval-gated Runtime Cockpit action-readiness requests, Pass 10F4 read-only ChaseOS bootstrap wizard preview, and Pass 10F5/10F6 proof-temp workspace upgrade approval/execution; remaining work includes real target-folder/file upgrade execution, persisted graph storage, runtime action execution, and OSRIL Phase 10 surfaces (Live Operator Shell, Voice I/O, Companion Surface)

---

*Graph links: [[PROJECT_FOUNDATION]] · [[ROADMAP]] · [[CLAUDE]] · [[FORKING]] · [[06_AGENTS/Agent-Output-Conventions|Agent-Output-Conventions]] · [[06_AGENTS/Knowledge-Taxonomy|Knowledge-Taxonomy]] · [[Feature-Register]] · [[Feature-Fit-Register]] · [[Phase9-Adopted-Feature-Specification]] · [[Agent-Memory-Architecture]] · [[Scheduled-Briefing-Pipelines]] · [[06_AGENTS/Autonomous-Operator-Runtime|Autonomous-Operator-Runtime]] · [[Runtime-Navigation-Map]] · [[06_AGENTS/SIC-Architecture|SIC-Architecture]] · [[ChaseOS-OS]] · [[TradingSystems-OS]] · [[FullStackWeb2Web3-OS]]*

*ChaseOS - Framework version: 0.9 | Phases 1-8 complete | Phase 9 active: AOR first-wave live + Graph Substrate (87 tests) + Operator Briefing V2 live + Native Schedule Layer live + ChaseOS-MCP-Server v1.0 architecture | Phase 10: Studio native shell/read-only panel lane through 10W + parser-backed graph input in 10X + typed graph/trust overlays in 10Y + graph provenance inspection in 10Z + approval-gated node create/edit in 10AA + approval-gated visual link proposals in 10AB + Runtime Cockpit action readiness in 10AC + bootstrap wizard preview in 10F4 + proof-temp workspace upgrade approval/execution in 10F5/10F6 | chaseos CLI v0.10.0 | sidecar schema v8.3 | 485 capture tests + 87 graph substrate tests passing*


*Graph links auto-wired by vault_hygiene (2026-05-04): [[AGENTS]] . [[CLI-INSTALL-README]] . [[KNOWLEDGE-INDEX]] . [[NEXT-STEPS]] . [[OPERATOR-BRIEF-INDEX]] . [[RUNTIME-REGISTRY]] . [[SETUP-INSTRUCTIONS]] . [[STRIKEZONE-DISCORD-SETUP]] . [[SYSTEM-STATUS]]*

## 2026-06-02 Terminal Workbench + ChaserAgent Expansion Addendum

The Hermes-inspired Terminal Workbench / ChaserAgent / Studio expansion has been scoped from the canonical handoff at `06_AGENTS/ChaseOS_Terminal_ChaserAgent_Fullstack_Implementation_Handoff_v2.md`. New canonical planning docs now live at `06_AGENTS/Terminal-ChaserAgent-Feature-Matrix.md`, `06_AGENTS/ChaserAgent-Architecture.md`, `06_AGENTS/Terminal-Workbench-Architecture.md`, and `06_AGENTS/Session-Export-and-Artifacts-Architecture.md`.

Implementation truth: the only code foothold added in this pass is `runtime/operator_surface/adapters/terminal_adapter.py`, now PARTIAL for bounded read-only subprocess execution. It blocks destructive/write/network/elevated/unknown commands, validates cwd scope, captures/redacts/truncates output, and labels terminal output as Tier 4 untrusted. Targeted verification passed with `PYTHONPATH=. uvx --with pyyaml pytest runtime/operator_surface/tests/test_terminal_adapter.py -q` (`6 passed`). ChaserAgent, `runtime/chaser/`, `board.py`, Terminal Workbench UI, `chaseos operate terminal`, session export backend, artifact hub, voice, mobile remote control, billing, and autonomous terminal execution remain PLANNED / DOCS-ONLY / DEFERRED as labeled in the feature matrix.
