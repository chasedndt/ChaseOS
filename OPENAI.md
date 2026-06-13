# OPENAI.md — OpenAI Execution Adapter for ChaseOS

> This is the execution adapter document for OpenAI surfaces operating in or adjacent to ChaseOS.
> It covers three distinct surfaces: the Chat UI, the Codex engineering surface, and the Agent Harness.
> These are not the same surface. Do not conflate them.
> Conformance standard: `[[06_AGENTS/Execution-Adapter-Standard|Execution-Adapter-Standard]]`
> Registry entries: `[[06_AGENTS/Agent-Registry|Agent-Registry]]`
> Permission rules: `[[06_AGENTS/Permission-Matrix|Permission-Matrix]]`
> Security model: `[[06_AGENTS/Agent-Security-Model|Agent-Security-Model]]`

---

## 2026-04-27 Adapter Foundation Update

**Status:** OpenAI adapter foundation is now PARTIAL / SHADOW PROOF.

Implemented now:
- `06_AGENTS/OpenAI-Adapter-Spec.md`
- `runtime/policy/adapters/openai_config.yaml`
- `06_AGENTS/role-cards/openai-operator-shadow.yaml`
- `runtime/workflows/registry/openai_operator_research_shadow.yaml`
- `runtime/workflows/openai_shadow.py`
- `runtime/adapters/openai/responses_mcp_payload.py`

Truth boundary:
- OpenAI Agents SDK is not live.
- Responses API calls are not live.
- Remote MCP calls are not live.
- ChatGPT Apps SDK remains a future UI surface.
- OpenAI remains an adapter/harness lane; ChaseOS remains the control plane and canonical truth holder.

The first use case is `openai_operator_research_shadow`: a bounded local shadow workflow that reads declared ChaseOS context and writes only draft/audit outputs.

---

## Surface Overview

OpenAI provides three execution surfaces that are in scope for ChaseOS. Each has a different access mode, trust ceiling, and role:

| Surface | Interface | Vault Access | Status |
|---------|-----------|-------------|--------|
| OpenAI Chat Surface | ChatGPT web / mobile | Advisory only — no vault access | Active (advisory) |
| Codex Engineering Surface | Codex CLI / subscription tool | Agent Bus worker for bounded code/repo/test tasks | Active bounded bus worker |
| OpenAI Agent Harness | Responses API + Agents SDK + MCP | Vault-capable via MCP — not yet deployed | Planned |

---

## Surface 1 — OpenAI Chat Surface (ChatGPT)

**2026-04-27 table correction:** the OpenAI Agent Harness row above is now shadow/dry-run only, not live; ChatGPT Apps SDK is a future UI surface documented in the adapter spec rather than a current backend.

### Identity
- **Provider:** OpenAI
- **Execution surface:** Chat UI — ChatGPT web or mobile
- **Adapter class:** Advisory Adapter
- **Trust tier:** Tier 3 — Advisory
- **Status:** Active (advisory use)
- **Registry entry:** See `Agent-Registry.md` — "OpenAI Chat Surface" entry (currently noted in Permission-Matrix surface rows)

### Access Mode
- **Advisory-only.** No direct vault access.
- **Read path:** User-pasted or uploaded content only — no filesystem access
- **Write path:** None — outputs must be imported manually by the user or by the Anthropic Agent Harness acting on user instruction
- **User-mediated import required:** Yes

### Required Read Order (Session Start)
ChatGPT has no vault access. The user provides context by pasting relevant files or excerpts.

For research sessions, the user should provide:
- The relevant domain excerpt or question context
- Any specific constraints or prior decisions from vault files

ChatGPT outputs are treated as Tier 3 research — verify before promoting to `02_KNOWLEDGE/`.

### Writeback Requirements
ChatGPT cannot write to the vault directly. Outputs that should be preserved:
1. Paste into `03_INPUTS/` via the Anthropic Agent Harness or manually
2. Process through `[[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]]` before promoting to knowledge

### Logging Behavior
No direct logging. If a ChatGPT session produces meaningful output:
- Import the output to `03_INPUTS/` with date and source label
- Treat as Tier 3 research input

### Approval Behavior
ChatGPT has no vault write capability; approval is not mechanically required. However:
- Do not paste credentials, protected-file contents, or sensitive vault state into ChatGPT — model provider may log prompt content
- Advisory outputs must be reviewed before being treated as canonical

### Failure and Escalation
Not applicable — ChatGPT operates in advisory mode. The user is responsible for evaluating and importing its outputs.

### Memory Rules
ChatGPT maintains conversation context within a session. It does not have persistent memory of vault state. Do not rely on ChatGPT's context as a substitute for vault content.

### Credential Handling
Do not paste API keys, exchange credentials, webhook secrets, or any other secrets into ChatGPT. Provider may log prompt content. See `[[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]]`.

### Security Inheritance
ChatGPT outputs are Tier 3. Process through `[[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]]` before vault promotion. Do not paste vault credentials or sensitive agent config into ChatGPT prompts.

### Cost / Billing
ChatGPT subscription (ChatGPT Plus / Pro) — flat monthly rate. No per-token billing for standard chat use.

---

## Surface 2 — Codex Engineering Surface

### Identity
- **Provider:** OpenAI
- **Execution surface:** Codex CLI / subscription-included engineering interface
- **Retained personal runtime name:** Axiom-Codex (legacy alias: Codex-ChaseOS-Worker)
- **Adapter class:** Harness / Agent Bus worker for bounded development packets
- **Trust tier:** Tier 2 ceiling when operating through the repo-local Codex bus adapter; Tier 3 when used as an unbound chat/advisory surface
- **Status:** Active bounded bus worker for `code.review`, `code.patch`, `repo.inspect`, and `test.run`
- **Registry entry:** `Agent-Registry.md` — "OpenAI Codex — Codex Bus Worker"
- **Runtime profile:** [[Codex-Runtime-Profile]]

### What Codex Is
Codex is OpenAI's subscription-included code-focused execution surface — separate from the chat UI and separate from the Agents SDK / API harness path. It is designed for code generation, editing, and engineering tasks. Codex CLI operates locally on the user's filesystem with tool-use capabilities.

**Codex is not the same as the OpenAI Agent Harness.** The Agent Harness (Surface 3) is the programmable API path — Responses API, Agents SDK, MCP. Codex is the subscription-included surface with its own interface and execution model.

### Access Mode in ChaseOS
- **Bus-bound in ChaseOS.** Codex is registered through `runtime/codex/capabilities.yaml` and `runtime/policy/adapters/codex.yaml`.
- **Local filesystem access:** Codex CLI can read and write local files when invoked by the operator or daemon, but ChaseOS treats the registered path as bounded by task packet, capability manifest, and adapter policy.
- **Read path in ChaseOS:** bounded task packet plus task-relevant repo files.
- **Write path in ChaseOS:** scoped development patches, tests, docs, logs, and Codex run artifacts when explicitly requested; no Pulse memory, Personal Map, R&D truth-state, autonomous promotion, or governed runtime-state ownership.
- **Daemon path:** `python -m chaseos agent-bus codex-daemon --interval 30 --executor codex --codex-binary codex`.

### ChaseOS Position
Codex is now formally registered as a bounded development worker, not as a broad runtime owner.

Codex outputs are still reviewable engineering artifacts. The vault remains the source of truth, and ChaseOS/OpenClaw/Gate remain the arbiters for governed memory, canonical promotion, and runtime-state writes.

If Codex is used outside the registered bus/profile path, treat the output as advisory/unbound and import or apply it through the normal ChaseOS review path.

### Formal Binding
The initial Codex binding is active through:
1. `runtime/codex/capabilities.yaml`
2. `runtime/policy/adapters/codex.yaml`
3. `runtime/adapters/codex/`
4. [[Codex-Runtime-Profile]]
5. `Agent-Registry.md`

This is a Phase 9 bounded worker path. It does not activate the OpenAI Agents SDK / MCP harness path in Surface 3.

### Cost / Billing
Included in OpenAI subscription tiers (ChatGPT Plus / Pro). Rate limits apply.

---

## Surface 3 — OpenAI Agent Harness (Responses API + Agents SDK + MCP)

### Identity
- **Provider:** OpenAI
- **Execution surface:** Programmatic agent harness — Responses API, Agents SDK, MCP workspace server
- **Adapter class:** Harness Adapter (when deployed)
- **Trust tier:** Tier 2 ceiling — conditional on deployment, MCP server scope, and owner trust assignment
- **Status:** Planned — MCP infrastructure not yet built; binding not active
- **Registry entry:** `Agent-Registry.md` — "OpenAI Agent Harness — Agents SDK / MCP (Planned)"

### What the OpenAI Agent Harness Is
The OpenAI Agent Harness is the API-based programmatic path: the Responses API (successor to the Chat Completions API with tool use), the Agents SDK (multi-agent orchestration with handoffs, guardrails, and background runs), and MCP server integration for vault access.

This is the path that enables OpenAI models to operate against ChaseOS as a vault-capable execution adapter — but only when the MCP server is deployed and the adapter is formally registered.

### Access Mode (When Deployed)
- **Vault-capable via MCP.** The harness reads and writes the vault through a ChaseOS MCP workspace server.
- **Read path:** MCP server exposes vault files as resources; adapter reads via MCP protocol
- **Write path:** MCP server exposes write tools; adapter writes per its granted permission scope
- **User-mediated import required:** No — harness writes directly when configured

### Required Read Order (When Active)
Same minimum as the Anthropic harness:
```
1. 00_HOME/Now.md
2. 01_PROJECTS/[Relevant]-OS.md
3. [supporting files per task type]
```
See `[[06_AGENTS/Execution-Adapter-Standard|Execution-Adapter-Standard]]` Section 3.3 for task-type routing.

### Writeback Requirements (When Active)
Same as all harness adapters:
- Build log at session close: `07_LOGS/Build-Logs/YYYY-MM-DD-[Project]-[descriptor].md`
- Project-OS update if state changed
- Archive note if the session was a major pass
- Index updates for any new logs or archive notes

### Logging Behavior (When Active)
The OpenAI Agent Harness writes build logs directly — it does not prompt the user to do this manually.

### Approval Behavior (When Active)
Same as all harness adapters per `[[06_AGENTS/Permission-Matrix|Permission-Matrix]]`:
- Protected-file edits: explicit per-file user approval required
- Deletions: explicit per-file instruction required
- External writes: session-scoped approval required
- Elevated actions: stated to user before proceeding

### Native Tool Access (Agents SDK)
When the OpenAI Agents SDK is configured:
- File search (vector store) — read access to indexed vault content
- Code Interpreter — sandboxed code execution
- MCP tool servers — vault read/write via ChaseOS MCP server
- Background runs — async execution with defined completion callbacks
- Handoffs — agent-to-agent context transfer (trust scope must not escalate at handoff)
- Guardrails — input/output validation (configured per deployment)

### MCP Server Requirements
The ChaseOS MCP server for this adapter must:
- Enforce permission boundaries at the server level (not only at the model level)
- Be scoped to the minimum file access required for the workflow
- Authenticate the adapter before granting access
- Log access events for audit trail
- Not expose protected files for write without matching the approval requirements in `[[06_AGENTS/Permission-Matrix|Permission-Matrix]]`

See `[[06_AGENTS/Agent-Security-Model|Agent-Security-Model]]` Section 5 for MCP security requirements.

### Memory Rules
The OpenAI Agents SDK maintains thread state for background runs. This is out-of-vault state:
- Thread state must not be treated as authoritative — vault files win on conflict
- Do not store credential values in thread state or agent instructions
- Background run results must be written to the vault before they are considered persistent

### Credential Handling
- OpenAI API key: stored in environment variable `OPENAI_API_KEY` — not in vault content
- MCP server credentials: in environment variables or secrets manager — not in vault content
- See `[[04_SOPS/Credential-Setup-SOP|Credential-Setup-SOP]]` and `[[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]]`

Current local MVP setup note: the actual key may live in the local ChaseOS root `.env` file, which is gitignored and loaded by the ChaseOS CLI, or in an OS/user environment variable. ChaseOS setup metadata should store only `secret_reference_target=OPENAI_API_KEY`. Do not write the key value into `runtime/setup_state.json`, Markdown docs, build logs, approval artifacts, or Git-tracked files.

### Cost / Billing
API-based pricing. Responses API: per-token input/output pricing per model. Agents SDK: per-token pricing plus tool call overhead. Background runs: asynchronous but still billed at completion. Codex (Surface 2) is separate from this billing path.

### What Must Be True Before This Adapter Is Active
1. MCP workspace server for ChaseOS deployed and tested
2. Registry entry in `Agent-Registry.md` updated with `Active` status and defined permission scope
3. This adapter document updated with actual MCP server URL and scope
4. Owner trust assignment confirmed for this surface
5. At least one test session run with audit trail before production use

---

## Advisory Note — Keeping Surfaces Separate

| Question | Answer |
|----------|--------|
| Is ChatGPT a vault-writing surface? | No — advisory only, Tier 3 |
| Is Codex a formally bound ChaseOS adapter? | Yes, as a bounded Agent Bus worker for code/repo/test packets; not as a broad runtime owner |
| Is the OpenAI Agent Harness active? | Not yet — MCP infrastructure not built |
| Can the same OpenAI model run on all three surfaces? | Yes — provider ≠ surface |
| Does registering one OpenAI surface grant access to others? | No — each surface requires independent registration |

---

---

## ChaseOS Gate Conformance

**Current status:** OpenAI Chat Surface (advisory) has no vault write access — Gate conformance is structural. The OpenAI Agent Harness (planned) must pass the Adapter Compliance Checklist before activation.

When the OpenAI Agent Harness is activated:
- Create `runtime/policy/adapters/openai-harness.yaml` with the full manifest
- Wire equivalent enforcement to the protected-file guard (MCP server-level scope restriction or input/output validators in Agents SDK)
- Pass `05_TEMPLATES/Adapter-Compliance-Checklist.md` Tier 4 (Vault-Writing)
- Update registry entry status to Active

Gate architecture: `[[06_AGENTS/ChaseOS-Gate|ChaseOS-Gate]]` · Compliance checklist: `[[05_TEMPLATES/Adapter-Compliance-Checklist|Adapter-Compliance-Checklist]]`

---

*Graph links: [[06_AGENTS/Execution-Adapter-Standard|Execution-Adapter-Standard]] · [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] · [[06_AGENTS/Agent-Registry|Agent-Registry]] · [[06_AGENTS/Backends-Supported|Backends-Supported]] · [[06_AGENTS/Permission-Matrix|Permission-Matrix]] · [[06_AGENTS/Trust-Tiers|Trust-Tiers]] · [[06_AGENTS/Agent-Security-Model|Agent-Security-Model]] · [[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]] · [[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]] · [[ROADMAP]] · [[06_AGENTS/ChaseOS-Gate|ChaseOS-Gate]] · [[06_AGENTS/Adapter-Manifest-Standard|Adapter-Manifest-Standard]]*

*OPENAI.md — Version 1.0 | Created: 2026-03-20 | Phase 5 — Repo / Runtime Binding | Patched: 2026-03-20 (Phase 6 preflight — Gate conformance section added)*
