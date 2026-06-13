# LOCAL-OSS.md — Local and Open-Source Execution Adapter for ChaseOS

> This is the execution adapter document for local and open-source model paths operating in ChaseOS.
> Covers three adapter paths: Claude Code + Ollama, Cline-style, and OpenHands-style.
> All three are planned / future — none are currently active ChaseOS adapters.
> Conformance standard: `[[06_AGENTS/Execution-Adapter-Standard|Execution-Adapter-Standard]]`
> Registry entry: `[[06_AGENTS/Agent-Registry|Agent-Registry]]` — "Local / Open-Source Operator Harness (Planned)"
> Security model: `[[06_AGENTS/Agent-Security-Model|Agent-Security-Model]]`

---

## Why Local / Open-Source Adapters Matter

Local adapter paths provide:
- **Privacy:** Prompts and vault content never leave the local machine
- **Offline operation:** No dependency on cloud provider availability
- **Model provider independence:** ChaseOS can operate with any model that fits the harness
- **Cost control:** No per-token API costs for local model usage
- **Sovereignty:** The framework does not depend on any single provider's continued service

The architecture is identical to the Anthropic Agent Harness for vault access purposes. The difference is that the model runs locally (via Ollama, LM Studio, or similar) rather than remotely. Provider ≠ surface ≠ adapter.

---

## Adapter Path 1 — Claude Code + Ollama

### Identity
- **Provider:** Open-source models (Llama, Qwen, Mistral, DeepSeek, etc.) via Ollama
- **Execution surface:** Agent Harness — Claude Code CLI with Ollama provider substitution
- **Adapter class:** Harness Adapter (when configured)
- **Trust tier:** Tier 2 ceiling — conditional on model compatibility, permission scope definition, and owner assignment
- **Status:** Planned — configuration not yet implemented
- **Model / cloud / local:** Local — model runs on local machine via Ollama
- **Registry entry:** `Agent-Registry.md` — Local/Open-Source Operator Harness entry

### How It Works
Claude Code CLI supports model provider substitution via an Anthropic-compatible API endpoint. Ollama exposes a compatible API at `http://localhost:11434`. When configured, Claude Code routes prompts to the local model instead of Anthropic's API — the harness surface (filesystem access, tool use, writeback) remains identical.

```
Claude Code CLI → Ollama API (local) → Open-source model (local)
         ↕
    ChaseOS vault (direct filesystem access — same as Anthropic harness)
```

### Access Mode
- **Vault-capable via direct filesystem.** Same access profile as the Anthropic Agent Harness.
- **Read path:** Direct — reads vault files from working directory
- **Write path:** Direct — writes to vault per permission scope (same as Anthropic harness)
- **User-mediated import required:** No

### Sandbox / Isolation Assumptions
- No provider-side sandbox. The model runs locally with the same filesystem access as the Claude Code process.
- No prompt content sent to external servers (by design — this is the privacy benefit).
- Code execution (bash tool) runs locally with the same host permissions as Claude Code.
- Isolation level: process-level only. No OS-level sandbox unless the user configures one.

**Implication:** Local model quality directly affects whether the adapter correctly enforces permission boundaries. Claude Code's tooling enforces the harness contract; the model's instruction-following quality determines how reliably it respects ChaseOS permission rules. Test with simple sessions before trusting local adapters with protected-file operations.

### Required Read Order
Same as Anthropic harness per `[[06_AGENTS/Execution-Adapter-Standard|Execution-Adapter-Standard]]`:
```
1. 00_HOME/Now.md
2. 01_PROJECTS/[Relevant]-OS.md
3. [task-specific supporting files]
```

### Writeback Requirements
Same as all harness adapters — build log at session close, Project-OS update if state changed, archive note for major passes, index updates.

### Approval Behavior
Same as Anthropic harness — protected-file edits, deletions, and external writes require explicit approval. The tooling enforces approval prompts at the Claude Code level; model instruction-following determines whether approval is correctly requested before action.

### Credential Handling
- Ollama does not require an API key by default (localhost only)
- If Ollama is exposed beyond localhost, authentication must be configured
- Model provider credentials: not applicable for local models
- Host machine credentials: same security posture as any local process with filesystem access
- See `[[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]]`

### What Must Be True Before This Adapter Is Active
1. Ollama installed and running locally with a capable model (≥ 7B parameters; instruction-tuned)
2. Claude Code configured with Ollama API endpoint
3. Compatibility test run: confirm the model correctly follows ChaseOS permission rules
4. Registry entry in `Agent-Registry.md` updated with model details and `Active` status
5. Owner trust assignment confirmed for the specific model being used
6. This adapter document updated with the model name and test results

### Cost / Billing
No per-token cost for local model inference. Hardware cost (GPU/CPU compute, power) applies. Ollama is open-source.

---

## Adapter Path 2 — Cline-Style Adapter

### Identity
- **Provider:** Any (multi-provider: Anthropic, OpenAI, Ollama, Azure, etc.)
- **Execution surface:** Agent Harness — Cline VSCode extension with filesystem access via VSCode API
- **Adapter class:** Harness Adapter (when configured and registered)
- **Trust tier:** Tier 2 ceiling — conditional on provider configuration, permission scope, and owner assignment
- **Status:** Planned — not yet formally bound to ChaseOS
- **Model / cloud / local:** Depends on configured provider; can be fully local (Ollama) or cloud-backed (Anthropic, OpenAI)
- **Registry entry:** `Agent-Registry.md` — Local/Open-Source Operator Harness entry (covers this path)

### What Cline Is
Cline is a VSCode extension that provides agent capabilities with multi-provider model support and direct filesystem access via the VSCode extension API. It can read and write files in the open workspace, run terminal commands, and use browser automation tools. It supports Anthropic, OpenAI, Azure, Google, Ollama, and other providers via a configurable backend.

### Access Mode
- **Vault-capable via VSCode filesystem API.**
- **Read path:** Reads vault files via VSCode workspace access (the vault must be open in VSCode)
- **Write path:** Writes to vault files via VSCode API
- **User-mediated import required:** No — Cline writes directly when authorized

### Sandbox / Isolation Assumptions
- Cline runs inside VSCode with the permissions of the VSCode process
- File access is limited to the open workspace by default (the vault folder)
- Terminal access runs commands in the VSCode integrated terminal — same host permissions
- Approval prompts: Cline shows proposed actions to the user before executing — the user approves or rejects each tool call in the VSCode UI
- This approval mechanism is compatible with ChaseOS permission requirements

### ChaseOS Binding Requirements
Cline does not natively read ChaseOS routing anchors. For Cline to operate as a ChaseOS adapter:
1. The ChaseOS vault must be open as the VSCode workspace
2. A Cline system prompt or custom instructions file must replicate the key rules from `CLAUDE.md`
3. Cline must be pointed at the correct read order and writeback targets
4. A registry entry with defined permission scope must exist before Cline operates on vault content

### Required Read Order
Same as Anthropic harness — but Cline must be configured to read these files at session start via its system prompt or custom instructions.

### Approval Behavior
Cline's built-in approval UI is the mechanism for per-action approval. This is compatible with ChaseOS requirements. Users must not set Cline to auto-approve all actions when operating on the vault.

### Credential Handling
- Provider API key (whichever provider Cline is configured with): stored in Cline's VSCode extension settings or environment variable — not in vault content
- See `[[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]]`

### Cost / Billing
Depends on configured provider. If using Ollama: no per-token cost. If using Anthropic or OpenAI API: per-token API pricing.

---

## Adapter Path 3 — OpenHands-Style Adapter

### Identity
- **Provider:** Any (multi-provider: Anthropic, OpenAI, local models, etc.)
- **Execution surface:** Agent Harness — OpenHands autonomous agent framework (or equivalent: SWE-agent, Aider with agent mode)
- **Adapter class:** Harness Adapter (when configured and registered)
- **Trust tier:** Tier 2 ceiling — conditional on provider, sandbox configuration, and owner assignment
- **Status:** Future — not yet scoped for ChaseOS binding
- **Model / cloud / local:** Depends on configured provider; can be fully local or cloud-backed
- **Registry entry:** `Agent-Registry.md` — Local/Open-Source Operator Harness entry (covers this path)

### What OpenHands Is
OpenHands (formerly OpenDevin) is a framework for autonomous software engineering agents that can browse the web, write and execute code, and manage files. It supports multiple model providers and can run in a sandboxed Docker environment. It is designed for longer-horizon tasks than typical chat or coding assistants.

### Access Mode
- **Vault-capable — depends on configuration.**
- **Read path:** Direct filesystem access inside its execution environment (Docker container or host)
- **Write path:** Direct filesystem — writes to any path accessible in its environment
- **User-mediated import required:** No — but requires careful scope control

### Sandbox / Isolation Assumptions
- OpenHands supports Docker-based sandboxing — the agent runs inside a container with a mounted workspace
- This is the recommended configuration for ChaseOS use: mount only the vault folder (not the full host)
- Without Docker: the agent has full host filesystem access — not recommended for ChaseOS use
- Web browsing: OpenHands can browse the web — web content is Tier 4; results must be treated as untrusted input

### ChaseOS Binding Requirements
OpenHands requires more careful configuration than Cline to operate safely inside ChaseOS:
1. Docker sandbox with vault folder mounted (not full host)
2. System prompt must replicate ChaseOS routing and permission rules
3. Web browsing results must be handled per `[[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]]`
4. Registry entry with explicit scope before any vault operations

### Approval Behavior
OpenHands has variable approval granularity depending on configuration. For ChaseOS use:
- Must be configured to pause before protected-file edits
- Must be configured to pause before delete operations
- Auto-approval of all actions is not permitted for ChaseOS vault operations

### Cost / Billing
Depends on configured provider. Docker compute cost applies for containerized execution.

---

## Comparing the Three Paths

| Feature | Claude Code + Ollama | Cline | OpenHands |
|---------|---------------------|-------|-----------|
| Local inference | Yes (Ollama) | Optional | Optional |
| Cloud provider option | Yes (swap provider) | Yes (any provider) | Yes (any provider) |
| VSCode integration | No | Yes (native) | No |
| Docker sandbox | No | No | Yes (recommended) |
| Web browsing | Via web fetch tool | Via browser tool | Yes (native) |
| Approval UI | Claude Code terminal | VSCode UI | Web UI |
| ChaseOS routing native | CLAUDE.md (exists) | Requires config | Requires config |
| Status in ChaseOS | Planned | Planned | Future |

---

## What Must Be True Before Any Local Adapter Is Active

1. The specific path (Claude Code+Ollama / Cline / OpenHands) is chosen and configured
2. A compatibility test is run confirming permission rule enforcement
3. Registry entry in `Agent-Registry.md` updated with path details and `Active` status
4. Owner trust assignment confirmed
5. This adapter document updated with path-specific operational details

---

---

## ChaseOS Gate Conformance

**Current status:** All three paths are planned/future. Manifests defined at `runtime/policy/adapters/local_oss.yaml`.

When any local adapter path is activated:
- Update `runtime/policy/adapters/local_oss.yaml` status to `active` with path-specific details
- Claude Code + Ollama: copy `.claude/settings.json` hook wiring — same enforcement as claude-harness
- Cline: VSCode approval UI serves as per-action approval mechanism; no additional hook required
- OpenHands: configure pause-on-protected-file in OpenHands settings
- Pass `05_TEMPLATES/Adapter-Compliance-Checklist.md` Tier 4 (Vault-Writing)
- Update registry entry status to Active

Gate architecture: `[[06_AGENTS/ChaseOS-Gate|ChaseOS-Gate]]` · Compliance checklist: `[[05_TEMPLATES/Adapter-Compliance-Checklist|Adapter-Compliance-Checklist]]`

---

*Graph links: [[06_AGENTS/Execution-Adapter-Standard|Execution-Adapter-Standard]] · [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] · [[06_AGENTS/Agent-Registry|Agent-Registry]] · [[06_AGENTS/Backends-Supported|Backends-Supported]] · [[06_AGENTS/Permission-Matrix|Permission-Matrix]] · [[06_AGENTS/Trust-Tiers|Trust-Tiers]] · [[06_AGENTS/Agent-Security-Model|Agent-Security-Model]] · [[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]] · [[CLAUDE]] · [[ROADMAP]] · [[06_AGENTS/ChaseOS-Gate|ChaseOS-Gate]] · [[06_AGENTS/Adapter-Manifest-Standard|Adapter-Manifest-Standard]]*

*LOCAL-OSS.md — Version 1.0 | Created: 2026-03-20 | Phase 5 — Repo / Runtime Binding | Patched: 2026-03-20 (Phase 6 preflight — Gate conformance section added)*
