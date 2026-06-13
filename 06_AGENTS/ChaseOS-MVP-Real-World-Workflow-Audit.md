---
title: ChaseOS MVP Real-World Workflow Audit
type: audit
status: PARTIAL / MVP PATH IDENTIFIED / REAL-WORLD USE BLOCKED BY CREDENTIALS AND APPROVAL CONSUMPTION
created: 2026-05-11
updated: 2026-05-11
runtime: Codex
session_descriptor: mvp-real-world-workflow-audit
---

# ChaseOS MVP Real-World Workflow Audit

## 2026-05-13 Supersession Note

This audit remains useful as the first MVP framing pass, but the current operational map is now [[ChaseOS-MVP-Consolidation-Map]].

Important deltas since this audit:

- Studio internal portable MVP is now closed with deferrals.
- Phase 11 companion-selection approval consumption is complete for one approved selection.
- Phase 11 runtime-dispatch approval consumption has written one bounded Agent Bus task for `Codex`.
- Agent Bus task lifecycle completion is now the sharpest next MVP proof.
- Provider readiness remains blocked by unresolved secret reference state.
- VentureOps remains blocked by missing real client-approved scope/evidence.

## Summary

ChaseOS has enough subsystem scaffolding to become useful as a real local-first operating loop, but the current MVP should not try to activate every feature family at once.

The usable MVP is:

> A governed operator cockpit that can ingest a real work scope, route it through Chat or Studio into an approval-gated workflow, run one bounded runtime task through the Agent Bus or AOR, produce durable proof artifacts, and close the loop in the daily/log/history layer without exposing secrets or mutating canonical state without approval.

Current repo truth supports this as a narrow MVP. It does not yet support broad "full system control", unrestricted browser/computer automation, marketplace operations, live revenue claims, autonomous canonical promotion, or live external delivery without explicit operator evidence and approvals.

## Canonical Rules Consulted

- [[README]]
- [[PROJECT_FOUNDATION]]
- [[ROADMAP]]
- [[00_HOME/Now]]
- [[CLAUDE]]
- [[HERMES]]
- [[OPENAI]]
- [[Agent-Control-Plane]]
- [[Permission-Matrix]]
- [[Trust-Tiers]]
- [[Vault-Map]]
- [[Agent-Registry]]
- [[Backends-Supported]]
- [[Runtime-InterAgent-Coordination-Bus]]
- [[Autonomous-Operator-Runtime]]
- [[ChaseOS-Studio-Phase10-Implementation-Tracker]]
- [[ChaseOS-Phase11-Architecture]]
- [[ChaseOS-Approval-Center]]
- [[VentureOps-Architecture]]
- [[Credential-Boundaries-SOP]]
- `.env.example`
- `.gitignore`
- `runtime/setup_state.json`
- `runtime/setup_state.example.json`
- latest relevant 2026-05-11 build logs for Studio, Chat, VentureOps, Agent Bus, provider readiness, and graph hygiene

## Repo-Truth Delta

### What Appears Current

- ChaseOS is framework-first and local-first; the vault/repo is the source of truth.
- Phase 7 Source Intelligence Core is complete enough as a subsystem.
- Phase 8 Connector/Capture Automation is complete enough as a subsystem.
- Phase 9 Operator Runtime / AOR remains the active hardening area.
- VentureOps has many local proof artifacts, guarded workflows, evidence templates, delivery-packet previews, approval gates, and revenue-evidence scaffolds.
- Studio has broad read-only and readiness surfaces for graph, node, dashboard, browser/runtime readiness, approval center, runtime cockpit, provenance, memory, identity, import/setup, and Phase 10/11 readiness.
- Phase 11 Chat has readiness contracts for provider preview, approval consumption, runtime dispatch, browser dispatch, companion selection, and no-write regression proof surfaces.
- Agent Bus local storage is readable and populated.

### What Appears Stale Or Misleading

- "Feature complete" language is unsafe unless it is narrowed to local proof or readiness surfaces.
- Pulse completion status reports local v1/backend control-plane completion, but provider calls, schedule activation, canonical mutation, and runtime dispatch effects remain blocked.
- Chat and Studio can show many readiness states, but the useful MVP is still blocked until at least one live path consumes an approval and writes the intended target or queues the intended bounded task.
- Product hardening still reports blocked release readiness because native packaged visual QA lacks required evidence.

### What Is Implemented

- Local proof and readiness surfaces for Agent Bus, AOR, Studio, Chat, graph hygiene, provider readiness checks, VentureOps evidence flows, and bounded browser-readiness contracts.
- Credential boundary documentation and environment-template conventions.
- No-write and approval-first patterns across risky surfaces.
- VentureOps workflow-family contract scaffolding for client scope, approval, delivery packet, exact-once gate, external-send dry run, CRM draft, invoice/payment draft, publication preview, and revenue evidence packet.

### What Is Only Documented Or Planned

- Live provider execution from Chat.
- Live Chat conversation persistence as the primary daily operator surface.
- Chat-to-Agent-Bus task dispatch execution.
- Browser dispatch from Chat into real browser effects.
- Native packaged Studio release/installer/startup/autostart readiness.
- General computer or full-system control beyond targeted browser/control-plane readiness lanes.
- Marketplace/workflow exchange publication, live revenue, CRM/payment mutations, and external delivery.

### What Is Unknown Or Unverified

- Whether the operator has a valid OpenAI secret reference available outside the repo.
- Whether Anthropic, local OSS/Ollama, Perplexity, n8n, Whop, and Discord delivery credentials are available in the operator environment.
- Whether WebView2 remediation has been performed on the host after the latest Pass 10B blocker.
- Whether a real client-approved VentureOps scope packet exists.
- Whether existing open/expired Agent Bus tasks should be cleaned, replayed, or archived.

## MVP Decision

The next MVP should be called:

`ChaseOS Operator MVP v0.1`

It should prove five things only:

1. A real operator can configure credentials without storing secrets in the repo.
2. A real request can enter through Chat or Studio and create a reviewable approval.
3. One approval can be consumed exactly once into a bounded output or task.
4. One bounded runtime workflow can run and write durable evidence.
5. The daily/log/history/index layer can explain what happened without chat memory.

Everything else remains a P1/P2 lane until this loop is boringly reliable.

## P0 MVP Workflow

### Loop 1 - Credential-Backed Chat Or Provider Smoke

Goal: prove one model-backed lane can run without exposing secrets.

Required now:
- Replace placeholder `SET_OPENAI_SECRET_REF` with a real local secret reference or environment binding.
- Run setup validation until OpenAI is structurally and probe-valid.
- Run provider live-smoke readiness until primary provider readiness is no longer blocked.
- Keep `.env` and actual secret values out of repo.

MVP success:
- `setup validate --json` reports OpenAI valid.
- provider live-smoke readiness reports an unblocked primary provider path.
- no raw API key appears in Markdown, JSON artifacts, logs, screenshots, or git diff.

### Loop 2 - Chat To Approval To File Or Task

Goal: make Chat useful as an operator surface, not only a readiness dashboard.

Recommended narrow path:
- Accept a short operator request in Chat.
- Generate an approval artifact.
- Consume one approved artifact exactly once.
- Write one bounded target under the approved path or queue one bounded Agent Bus task.

Do not start with broad natural-language automation. Start with one target class:
- proposal file write under `01_PROJECTS/_chat_proposals/`, or
- `repo.inspect` task for `Codex` through the Agent Bus.

MVP success:
- approval request exists,
- operator decision exists,
- consumption evidence exists,
- target write or task event exists,
- repeated consumption is blocked.

### Loop 3 - Agent Bus Runtime Lifecycle

Goal: prove that Codex, Hermes, OpenClaw, or Chaser Agent can be operated as workers instead of chat-only personas.

Current bus truth:
- Agent Bus local storage is readable.
- Latest observed task count: 286.
- Latest observed open tasks: 41.
- Latest observed done tasks: 14.
- Latest observed expired tasks: 113.

Required now:
- Run readiness.
- Decide whether to clean, archive, or leave expired/open tasks.
- Run one mock daemon pass.
- Run one bounded live daemon pass only after readiness and approval.
- Produce one task lifecycle proof: created, claimed, executed, artifact written, result event emitted.

MVP success:
- one current task is completed by a runtime worker,
- artifacts are under the adapter boundary,
- result shape is `proposal`, `patch`, `risk`, `blocked`, or `complete`,
- no governed memory or canonical state is mutated directly by Codex.

### Loop 4 - VentureOps Real Client Scope Proof

Goal: make VentureOps useful against one real client-approved scope.

Current repo truth:
- VentureOps is heavily scaffolded and guarded.
- It is not complete as a live business workflow.
- The next real-use pass is `ventureops-live-client-workflow-proof`.
- Real client-approved source evidence is required first.

Required now:
- Operator supplies typed real-client scope approval.
- Operator supplies real client-approved source evidence.
- Run scope evidence validation before workflow proof.
- Run one live-client workflow proof.
- Keep external send/payment/revenue claims blocked unless the specific proof lane is approved.

MVP success:
- a real scope packet validates,
- the workflow proof writes artifacts,
- the client output packet is reviewable,
- any external send remains approval-gated,
- revenue/payment remains proof-only until payment evidence exists.

### Loop 5 - Daily Operating Closeout

Goal: make ChaseOS useful every day, not just impressive in architecture.

Required now:
- A daily "operator today" or closeout runbook selects the next one or two tasks.
- Daily note records session status, tests, artifacts, blockers, and next action.
- Graph hygiene queue is reviewed, not merely regenerated.
- Build logs and documentation history are indexed on the same day.

MVP success:
- the operator can open one daily note and know what to do next.

## Feature Family Audit

| Feature Family | Current Truth | MVP Role | Needed Now |
|---|---|---|---|
| Agent Bus | PARTIAL / local readable / task store populated | P0 runtime coordination proof | readiness, task hygiene, one lifecycle proof |
| Studio | PARTIAL / strong read-only cockpit / native packaging blocked | P0 visibility surface, P1 native release | use local/static/readiness cockpit now; remediate WebView2 before packaged MVP |
| Chat Interface | PARTIAL / readiness contracts exist / live execution blocked | P0 operator intake and approval surface | one approval consumption path and one target write/task queue |
| Graph / Vault Intelligence | COMPLETE ENOUGH for read/context; hygiene still review-gated | P0 navigation and source-of-truth sanity | review graph hygiene queue; keep mutation approval-gated |
| VentureOps | PARTIAL / local proofs strong / no live client run | P0 real-world workflow proof | real client scope approval and source evidence |
| Source Intelligence Core | COMPLETE ENOUGH | P0 context/evidence substrate | use one source pack in real workflow |
| Connector/Capture | COMPLETE ENOUGH / credentials pending for some external lanes | P1 live research/capture | add only credentials needed for chosen MVP path |
| Pulse | LOCAL V1 COMPLETE / broader effects blocked | P1 daily orchestration/readiness | use read-only or proof paths; do not claim autonomous schedule effects yet |
| Browser Runtime | PARTIAL / targeted readiness and shadow proof | P1 targeted browser workflows | keep safe URL/browser readiness only until live browser proof approved |
| Full System Control | PLANNED / HIGH RISK | Not in MVP | define threat model, allowlist, approvals, dry-run proofs first |
| Workflow Exchange / Marketplace | PLANNED/PREVIEW | P2 | no publication before real proof and operator approval |
| Payments / CRM / Revenue | PROOF/PREVIEW ONLY | P2 | do not activate until real client proof and explicit finance approvals exist |

## Credentials And API Key Readiness

No secret values should be committed to the repo. Use environment variables, OS secret storage, or a secret-reference indirection that probes valid without revealing the value.

| Credential / Config | Priority | Current Repo Signal | Needed For MVP |
|---|---:|---|---|
| `OPENAI_API_KEY` or OpenAI secret reference | P0 | OpenAI marked configured, but latest probe found placeholder/missing secret reference | Required if OpenAI is the primary live model lane |
| `ANTHROPIC_API_KEY` | P0/P1 | Claude/Anthropic not configured in setup validation | Required if Hermes/Claude synthesis is part of MVP |
| Local OSS / Ollama host and model | P0/P1 | fallback not configured | Required if offline/fallback live-smoke readiness is in scope |
| Discord webhook/bot token secret reference | P1 | Discord binding configured, delivery secrets remain boundary-sensitive | Required only for live Discord delivery/control-plane output |
| `PERPLEXITY_API_KEY` | P1 | template only | Required only for live research connector path |
| Browser Use CLI path | P1 | environment intake exists; no account/profile credential required for safe local proofs | Required for live browser lane, not for first Chat/File MVP |
| Excalidraw target URL | P1 | setup/readiness path exists | Required only for Excalidraw browser proof |
| n8n base URL/API/access token | P2 | n8n not configured/deployed | Not needed for first MVP |
| Whop/payment/CRM credentials | P2 | proof-only lanes exist | Not needed until live commerce lane is approved |
| Trading/exchange/wallet credentials | Out of scope | high-risk by policy | Do not add to MVP |

## High-Risk Publication Findings

This section follows the Core/Personal audit posture.

- `00_HOME/`, `01_PROJECTS/`, `02_KNOWLEDGE/`, `03_INPUTS/`, `07_LOGS/`, `99_ARCHIVE/`, `SOUL.md`, runtime state, and generated proof artifacts are personal/operator-specific and unsafe for public mirroring without review.
- `06_AGENTS/` is mixed. Architecture docs can become core templates, but current files contain live status, runtime names, activity records, and personal operating truth.
- `.env.example` is template-like, but must stay placeholder-only.
- `runtime/setup_state.json` is local setup state and should remain private/manual-review.
- `.gitignore` already protects many secret and local-state paths; keep it strict before any public mirror.

## Classification Table

| Path Or Surface | Classification | Notes |
|---|---|---|
| `README.md` | Core with review | Public identity anchor; avoid personal state |
| `PROJECT_FOUNDATION.md` | Core with review | Architecture anchor |
| `ROADMAP.md` | Core with review | Must distinguish complete, partial, planned |
| `FORKING.md` | Core template candidate | useful for public mirror rules |
| `04_SOPS/` | Mixed core/template | review for personal workflow details |
| `05_TEMPLATES/` | Core/template candidate | safe after placeholder review |
| `06_AGENTS/` | Mixed | architecture plus live runtime truth |
| `runtime/` source code | Core/private mixed | source can be core; state/artifacts private |
| `00_HOME/` | Personal/private | daily operating truth |
| `01_PROJECTS/` | Personal/private | client/project details possible |
| `02_KNOWLEDGE/` | Personal/private | source notes may contain private info |
| `03_INPUTS/` | Personal/private | capture ingress |
| `07_LOGS/` | Personal/private | build/runtime/daily evidence |
| `99_ARCHIVE/` | Personal/private | historical records |
| `.env.example` | Template with review | placeholders only |
| `runtime/setup_state.json` | Private/local | can reveal configured services/status |
| `.gitignore` | Core safety surface | keep strict |

## Recommended Moves

1. Make OpenAI or one chosen provider probe-valid through a secret reference.
2. Keep provider setup separate from repo writeback; record only reference names and validation status.
3. Choose one Chat consumption target and finish it end to end.
4. Cleanly prove one Agent Bus task lifecycle.
5. Run VentureOps against one real client-approved scope packet.
6. Use Studio as a cockpit now, but do not make packaged/native release a blocker for internal MVP if localhost/static shell is enough.
7. Treat graph hygiene review as an operator queue, not a background mutation.
8. Keep full system control out of MVP.

## Suggested Private-Only Ignore Rules

Existing ignore rules already cover many of these. Confirm before any public mirror:

```gitignore
.env
.env.*
secrets/
credentials/
runtime/setup_state.json
runtime/**/runs/
runtime/**/state/
07_LOGS/
00_HOME/
01_PROJECTS/
02_KNOWLEDGE/
03_INPUTS/
99_ARCHIVE/
.obsidian/
.chaseos/
```

## Open Questions / Manual Review

- Which provider is the MVP default: OpenAI, Anthropic, local OSS, or a hybrid?
- Should Chat MVP target a proposal file first or an Agent Bus task first?
- Which Agent Bus open/expired tasks should be retained, archived, or replayed?
- What exact real client scope is allowed for the first VentureOps workflow proof?
- Is packaged Studio required for MVP, or is local browser/static Studio acceptable until WebView2 is repaired?
- Which external delivery lane, if any, is approved for first live use?

## What Not To Do Now

- Do not add raw API keys to Markdown, JSON, `.env.example`, screenshots, logs, or chat artifacts.
- Do not activate broad computer/full-system control.
- Do not claim VentureOps is live-business complete before a real client workflow proof.
- Do not enable payment, CRM, external send, marketplace publication, or browser profile access as part of the first MVP.
- Do not mutate Pulse memory, Personal Map, R&D truth-state records, or canonical state from Codex.
- Do not turn every readiness surface into a live action at once.

## Next Recommended Pass

`mvp-provider-and-chat-approval-consumption-proof`

Suggested first command path:

1. Fix provider secret reference outside the repo.
2. Run setup validation.
3. Run provider live-smoke readiness.
4. Pick Chat target: file proposal or Agent Bus `repo.inspect`.
5. Prove one approval request and exact-once consumption.

Result expected: one usable operator loop, not a universal automation system.
