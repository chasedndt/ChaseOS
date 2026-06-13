---
type: agent-registry
version: 3.4
updated: 2026-05-13
---

# Agent Registry

> All AI agents and AI-powered tools operating in ChaseOS.
> Each entry includes: backend/provider, execution surface, execution adapter, access mode, trust tier, and permission scope.
> Trust tier = authority ceiling. Execution surface = what the agent can physically do. Execution adapter = the specific binding doc + config that connects this surface to ChaseOS.
> These are distinct. See `[[Trust-Tiers]]`, `[[Backends-Supported]]`, and `[[Execution-Adapter-Standard]]` for the full model.
> See also: `[[Assistant-Contract]]` · `[[Agent-Control-Plane]]` · `[[Permission-Matrix]]` · `[[Tool-Map]]`

---

## Registry

### Anthropic Agent Harness — Claude Code CLI

| Field | Value |
|-------|-------|
| **Backend / Provider** | Anthropic (Claude models) |
| **Execution Surface** | Agent Harness — Claude Code CLI with local filesystem access |
| **Execution Adapter** | `CLAUDE.md` — routing anchor, read order, writeback rules, protected-file list |
| **Access Mode** | Direct vault read/write via filesystem |
| **Native Tool Access** | File read, file write, file edit, bash execution, web fetch (with approval) |
| **Vault Read Path** | Direct — reads any vault file from working directory |
| **Vault Write Path** | Direct — writes to vault on agent-initiated writeback |
| **User-Mediated Import Needed** | No — harness writes directly |
| **Trust Tier** | Tier 2 — High Trust |
| **Permission Scope** | Read all; create standard outputs; edit with direction; protected files require explicit per-file approval; no self-authorized deletes |
| **Role** | Primary engineering and documentation assistant — vault-writing harness |
| **Domains Served** | All |
| **Contract** | `[[Assistant-Contract]]` v2.0 |
| **Active** | ✅ |

---

### Anthropic Chat Surface — claude.ai

| Field | Value |
|-------|-------|
| **Backend / Provider** | Anthropic (Claude models) |
| **Execution Surface** | Chat UI — claude.ai web or mobile |
| **Execution Adapter** | No formal adapter doc — advisory surface; output handling defined here |
| **Access Mode** | Advisory only — no direct vault access |
| **Native Tool Access** | Web search (when enabled); no file system access |
| **Vault Read Path** | User-mediated only — user pastes or provides content in conversation |
| **Vault Write Path** | User-mediated only — user manually imports outputs, or Anthropic Agent Harness imports on user instruction |
| **User-Mediated Import Needed** | Yes — chat outputs must be imported manually or via harness |
| **Trust Tier** | Tier 3 — Advisory (same provider as Tier 2 harness; different surface) |
| **Permission Scope** | Read provided content; no vault write access; advisory output only |
| **Role** | Research, reasoning, synthesis, drafting — outputs imported by user or harness |
| **Domains Served** | Research, content drafting, analysis, planning |
| **Active** | ✅ |

---

### NotebookLM — Google

| Field | Value |
|-------|-------|
| **Backend / Provider** | Google (proprietary model) |
| **Execution Surface** | Research synthesis platform — upload-only access |
| **Access Mode** | Read-only over user-uploaded sources |
| **Native Tool Access** | Source Q&A, document synthesis, podcast generation |
| **Vault Read Path** | Upload-mediated only — user uploads specific files |
| **Vault Write Path** | None — outputs exported manually by user |
| **User-Mediated Import Needed** | Yes |
| **Trust Tier** | Tier 3 — Research |
| **Permission Scope** | Read uploaded content; no vault write; outputs are Tier 3 research input |
| **Role** | Source synthesis and document analysis |
| **Domains Served** | Research ingestion, University, Trading |
| **Output handling** | File outputs in `03_INPUTS/`; process through `[[04_SOPS/Research-Ingest-SOP|Research-Ingest-SOP]]` |
| **Active** | ✅ |

---

### Perplexity AI

| Field | Value |
|-------|-------|
| **Backend / Provider** | Perplexity AI |
| **Execution Surface** | Research platform — web search surface |
| **Access Mode** | External only — searches the web, no vault access |
| **Native Tool Access** | Real-time web search with citations |
| **Vault Read Path** | None |
| **Vault Write Path** | None |
| **User-Mediated Import Needed** | Yes |
| **Trust Tier** | Tier 3 — Research |
| **Permission Scope** | No vault access; outputs are Tier 3 research input requiring verification |
| **Role** | Live research, digest generation, market intel |
| **Domains Served** | Trading, Research Ingestion, Content |
| **Output handling** | File in `03_INPUTS/Digests/`; verify financial claims; process through ingest SOP |
| **Active** | ✅ |

---

### Grok — xAI

| Field | Value |
|-------|-------|
| **Backend / Provider** | xAI |
| **Execution Surface** | Research platform — X/web integrated |
| **Access Mode** | External only — X and web data, no vault access |
| **Native Tool Access** | Real-time X data, market narrative tracking |
| **Vault Read Path** | None |
| **Vault Write Path** | None |
| **User-Mediated Import Needed** | Yes |
| **Trust Tier** | Tier 3 — Research |
| **Permission Scope** | No vault access; outputs are Tier 3 research input |
| **Role** | Crypto / market commentary, X-integrated research |
| **Domains Served** | Trading, Content, Market Intel |
| **Output handling** | File in `03_INPUTS/Digests/`; verify financial claims; process through ingest SOP |
| **Active** | ✅ |

---

### n8n — Self-Hosted (Planned)

| Field | Value |
|-------|-------|
| **Backend / Provider** | n8n (self-hosted) |
| **Execution Surface** | Workflow runtime — HTTP-triggered, scheduled execution |
| **Execution Adapter** | `N8N.md` — workflow scope rules, writeback targets, approval and credential policy |
| **Access Mode** | Workflow-scoped — bounded by workflow definition and MCP configuration |
| **Native Tool Access** | HTTP requests, scheduled jobs, Discord/Telegram integration; vault access via configured MCP or filesystem node |
| **Vault Read Path** | Workflow-scoped MCP or filesystem node — not general access |
| **Vault Write Path** | Workflow-scoped only — defined per workflow; no general vault write |
| **User-Mediated Import Needed** | Depends on workflow |
| **Trust Tier** | Tier 2 ceiling — conditional on deployment, workflow scope review, and owner trust assignment |
| **Permission Scope** | TBD per workflow — must not exceed Tier 2 defaults; requires owner assignment before operating |
| **Role** | Workflow automation, alert pipelines, scheduled data processing |
| **Active** | ⬜ Not yet deployed |

---

### OpenAI Agent Harness — Agents SDK / MCP (Planned)

| Field | Value |
|-------|-------|
| **Backend / Provider** | OpenAI (GPT models) |
| **Execution Surface** | Agent harness — OpenAI Agents SDK with MCP or file search tools |
| **Execution Adapter** | `OPENAI.md` Surface 3 — covers access mode, MCP requirements, approval behavior |
| **Access Mode** | Harness-mediated vault access via MCP workspace server |
| **Native Tool Access** | File search, Code Interpreter, background runs, handoffs, guardrails (via Agents SDK) |
| **Vault Read Path** | MCP workspace server (planned) |
| **Vault Write Path** | MCP workspace server (planned) |
| **User-Mediated Import Needed** | No — harness writes directly when configured |
| **Trust Tier** | Tier 2 ceiling — requires owner assignment, MCP server deployment, and workflow scope definition |
| **Permission Scope** | TBD — must be scoped at MCP server level before trust assignment |
| **Role** | Future alternative harness; multi-model workflows |
| **Active** | ⬜ Planned — MCP infrastructure not yet built |

---

### Local / Open-Source Operator Harness (Planned)

| Field | Value |
|-------|-------|
| **Backend / Provider** | Open-source models via Ollama, LM Studio, or compatible API |
| **Execution Surface** | Local operator harness — Cline, OpenHands, or Claude Code with Ollama provider |
| **Execution Adapter** | `LOCAL-OSS.md` — covers three adapter paths: Claude Code+Ollama, Cline, OpenHands |
| **Access Mode** | Direct local filesystem access — same surface as Claude Code, different model provider |
| **Native Tool Access** | File read/write, terminal, browser (surface-dependent) |
| **Vault Read Path** | Direct — same as Anthropic Agent Harness |
| **Vault Write Path** | Direct — same as Anthropic Agent Harness |
| **User-Mediated Import Needed** | No |
| **Trust Tier** | Tier 2 ceiling — conditional on harness configuration, permission scope definition, and owner assignment |
| **Permission Scope** | TBD — harness must enforce the same permission boundaries as Claude Code before trust assignment |
| **Role** | Offline/private operation; model provider independence |
| **Active** | ⬜ Planned |

---

### Hermes Agent — Bounded Operator Runtime (Phase 9 Bounded Shadow + Bus Active)

| Field | Value |
|-------|-------|
| **Backend / Provider** | Hermes Agent (platform under evaluation — specific backend TBD at deployment) |
| **Execution Surface** | Bounded AOR shadow workflow plus bounded coordination-bus review/analysis workflows; persistent shell/connector/browser surfaces remain blocked |
| **Surface Class** | Workflow / Operator Runtime Surface |
| **Execution Adapter** | `06_AGENTS/Hermes-Adapter-Spec.md` — bounded shadow active for `hermes_operator_today_shadow`; bounded bus active for `hermes_review_execute` and `hermes_watch`; broader runtime authority blocked |
| **Access Mode** | Workflow-manifest-declared only — no ambient vault access |
| **Native Tool Access** | None in the current shadow path; persistent memory, generated skills, subagents, browser/tool control, and gateway surfaces remain disabled unless separately approved by workflow manifest, role card, adapter policy, and operator review |
| **Vault Read Path** | Workflow-scoped only — declared in active workflow manifest and governing role card |
| **Vault Write Path** | Current shadow writes drafts and audit/build/archive records only; no canonical knowledge writes |
| **User-Mediated Import Needed** | Yes for anything beyond draft/audit outputs; canonical promotion always requires Gate + human review |
| **Trust Tier** | Tier 4 by default → escalates to Tier 2 ceiling only with: formal evaluation, named contract, owner-assigned permission scope, audit path verified, secrets boundary confirmed |
| **Permission Scope** | Workflow-manifest-bounded; no general vault write; no protected file edit; no autonomous canonical promotion |
| **Role** | Phase 9 bounded operator adapter — executes declared shadow and bus-result workflows under ChaseOS governance |
| **Domains Served** | `hermes_operator_today_shadow`; coordination-bus `review`, `planning`, `shadow-audit`, and `developer-co-development` packets only; broader operator workflow, research, maintenance, capture, and delivery domains remain blocked |
| **Workflow Boundaries** | `06_AGENTS/Hermes-Workflow-Boundaries.md` |
| **Memory Boundary** | `06_AGENTS/Hermes-Memory-Boundary.md` |
| **Positioning** | `HERMES.md` |
| **Contract** | `06_AGENTS/Assistant-Contract.md` applies; adapter-specific constraints in `Hermes-Adapter-Spec.md` |
| **Active** | ⚠️ Bounded shadow + bus active — approved workflow set is exact and narrow; broader Hermes adapter authority remains blocked |

---

### OpenClaw / Custom Operator - Bounded Local Operator Runtime

| Field | Value |
|-------|-------|
| **Backend / Provider** | OpenClaw local/custom operator runtime |
| **Execution Surface** | Bounded local operator adapter through ChaseOS CLI / AOR entrypoints |
| **Surface Class** | Local Operator Runtime Surface |
| **Execution Adapter** | `OPENCLAW.md`; `06_AGENTS/OpenClaw-Adapter-Spec.md`; runtime profile `06_AGENTS/OpenClaw-Runtime-Profile.md` |
| **Access Mode** | Bounded-active by declared workflow, adapter policy, and ChaseOS runtime entrypoint |
| **Native Tool Access** | Local operator execution through approved ChaseOS commands only; host shell capability exists but remains policy-bounded |
| **Vault Read Path** | Adapter allowlist and workflow-scoped read surfaces only; no ambient broad vault authority |
| **Vault Write Path** | AOR / ChaseOS writeback surfaces only; no direct canonical write or protected-file edit by default |
| **User-Mediated Import Needed** | No for approved runtime/audit outputs; yes for any canonical promotion or scope expansion |
| **Trust Tier** | Tier 2 ceiling when bound to the approved adapter/workflow envelope; Tier 4 default outside that binding |
| **Permission Scope** | May execute approved local operator workflows and write runtime/audit/log artifacts. Forbidden by default: secrets/credentials, destructive deletes, protected-file rewrites, direct canonical-state mutation, broad shell/file traversal, external sends, CRM/payment/trading/customer actions, and self-escalation. |
| **Role** | Phase 9 bounded local operator lane for ChaseOS CLI / AOR workflows under control-plane rules |
| **Domains Served** | Operator-day workflows, day-close workflows, graph hygiene, and explicitly approved AOR/operator tasks only |
| **Active** | Active bounded runtime lane; broad autonomy remains blocked |

---

### OpenHuman — Reference Product / Feature Study

| Field | Value |
|-------|-------|
| **Backend / Provider** | OpenHuman (`tinyhumansai/openhuman`) upstream product, retained for feature reference only |
| **Execution Surface** | None in ChaseOS; former Windows UI + WSL core bootstrap is retired |
| **Surface Class** | Reference product / product-study source, not a runtime surface |
| **Execution Adapter** | `06_AGENTS/OpenHuman-Adapter-Spec.md` is retired/reference-only; runtime profile `06_AGENTS/OpenHuman-Runtime-Profile.md` is reference-only |
| **Access Mode** | No active ChaseOS access; no Agent Bus, no KG access, no sandbox use |
| **Native Tool Access** | None |
| **Vault Read Path** | Human/operator or ChaseOS runtime may read OpenHuman reference docs for planning only |
| **Vault Write Path** | Feature planning docs and audit logs only |
| **User-Mediated Import Needed** | Yes for any future reactivation proposal |
| **Trust Tier** | Not assigned as active runtime; Tier 4 external/reference material if consulted |
| **Permission Scope** | No ChaseOS action authority; no provider credentials; no connector/external-send/canonical-write authority |
| **Role** | Close-market product reference for ChaseOS UX, provider, memory, credit, local-model, and context-compression planning |
| **Domains Served** | Reference study only; feature extraction tracked in `docs/features/openhuman-reference-feature-extraction-plan.md` |
| **Active** | ❌ Retired from runtime integration on 2026-05-18 — do not route ChaseOS work through OpenHuman |

---

### OpenAI Codex - Codex Bus Worker

| Field | Value |
|-------|-------|
| **Backend / Provider** | OpenAI (Codex CLI surface) |
| **Personal Runtime Name** | `Axiom-Codex` (legacy alias: `Codex-ChaseOS-Worker`) |
| **Execution Surface** | Codex CLI through ChaseOS Agent Bus daemon |
| **Execution Adapter** | `runtime/adapters/codex/README.md`; policy manifest `runtime/policy/adapters/codex.yaml`; runtime profile [[Codex-Runtime-Profile]] |
| **Access Mode** | Repo-aware bounded development worker; task packet and capability manifest scoped |
| **Native Tool Access** | Local Codex CLI subprocess through `codex exec` when live daemon uses `--executor codex`; deterministic mock executor for smoke tests |
| **Vault Read Path** | Bounded by task request, repo-truth preflight, and task-relevant files |
| **Vault Write Path** | Scoped code/docs/tests/logs/profile/index updates and Codex run artifacts when explicitly requested; no governed memory/core ownership |
| **User-Mediated Import Needed** | No for bus-bound development artifacts; yes for unbound advisory Codex output |
| **Trust Tier** | Tier 2 ceiling when bus-bound; Tier 3 when used outside the registered binding |
| **Permission Scope** | Handles `code.review`, `code.patch`, `repo.inspect`, and `test.run`; no direct Pulse memory, Personal Map, R&D truth-state, autonomous promotion, or governed runtime-state writes |
| **Role** | Bounded development worker and reviewable patch/artifact producer |
| **Domains Served** | ChaseOS runtime/code/docs/test work only unless a future capability manifest expands scope |
| **Contract** | [[Codex-Runtime-Profile]]; `runtime/adapters/codex/CODEX_BUS_HANDOFF.md` |
| **Active** | Active bounded bus worker |

---

## Registration Rules

1. All new agents default to **Tier 4** until explicitly assigned by the owner
2. Trust assignment must be documented in this registry with backend, surface, access mode, and execution adapter reference before the agent operates
3. Tier 2 assignments require a named contract, a defined execution surface with scoped access, and a conformant adapter document per `[[Execution-Adapter-Standard]]`
4. Chat-surface instances of any provider are Tier 3 (advisory) regardless of the provider's harness-tier assignment
5. Tier escalation requires explicit owner decision — no self-promotion
6. A surface without an adapter document is not authorized to operate against the vault — trust assignment is necessary but not sufficient

---

## Agent Behavior Rules Summary

| Rule | Applies To |
|------|-----------|
| Read vault before acting | Harness adapter surfaces (Tier 2) — not advisory surfaces |
| Write build logs directly — do not prompt the user | Active harness adapters (currently: Anthropic Agent Harness only) |
| Import outputs via `03_INPUTS/`; process through ingest SOP | All Tier 3 advisory and research surfaces |
| Verify financial and market claims before filing as knowledge | Perplexity, Grok, and any research surface |
| Never delete without explicit per-file instruction | All agents, all surfaces |
| Advisory output only — no direct vault write | All chat-surface and research-surface instances |
| Conform to Execution-Adapter-Standard before operating | All harness and runtime adapters |

---

*Graph links: [[Agent-Control-Plane]] · [[Backends-Supported]] · [[Execution-Adapter-Standard]] · [[Agent-Bus-Visual-Inspection]] · [[OPENAI]] · [[Codex-Runtime-Profile]] · [[OPENCLAW]] · [[OpenClaw-Runtime-Profile]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Runtime-Navigation-Map]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Assistant-Contract]] · [[Tool-Map]] · [[Vault-Map]]*

*Agent-Registry.md - Version 3.4 | Updated: 2026-05-13 (OpenClaw corrected from future/TBD to active bounded local operator runtime lane; broad autonomy remains blocked) | Previous: v3.3 2026-04-20 (Hermes corrected from docs-only planned adapter to bounded shadow active for one AOR workflow; broader authority blocked)*
