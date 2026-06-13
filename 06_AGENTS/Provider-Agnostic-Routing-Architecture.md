---
type: architecture
domain: agent-routing
status: active
created: 2026-05-18
---

# Provider-Agnostic Routing Architecture

> **Canonical rule for this repository.**
> Nothing in ChaseOS is locked to a single model provider.
> All LLM dispatch routes through the Agent Bus → runtime layer.
> Studio and UI surfaces never call model providers directly.

---

## The Rule

**Studio surfaces never call model providers directly.**
All LLM execution routes through the Agent Bus → the configured runtime (Hermes, OpenClaw, Chaser Agent, or any future runtime). Each runtime owns its own credentials, model configuration, and provider selection. No ChaseOS feature is wired to a single provider.

This rule applies to:
- Studio Chat companion (Phase 11)
- SBP pipelines (execution_adapter field)
- Operator briefing workflows
- Any future surface that generates model output

---

## Architecture

```
User → Studio/Chat → Agent Bus (create_task) → Runtime
                                                   ↓
                                           model_config.yaml
                                                   ↓
                                     OpenAI / Anthropic / Ollama /
                                     OpenClaw / Hermes / OAuth provider
                                           (runtime's choice)
```

Studio creates an Agent Bus task with the intent and message. The runtime that claims the task calls whatever model it's configured for. The result comes back through the bus. Studio reads the result. Studio never touches a provider credential.

---

## What "Runtime-Owned Model Choice" Means

Each runtime has its own `model_config.yaml` file:

| Runtime | Config location | Default provider |
|---------|----------------|-----------------|
| Hermes (WSL) | `runtime/hermes/model_config.yaml` | `ANTHROPIC_API_KEY` → claude model |
| OpenClaw (Windows) | `runtime/openclaw/model_config.yaml` | operator-configured |
| Chaser Agent (Claude Code) | `runtime/memory/adapters/chaser_agent/` | Anthropic (session) |

To switch models or providers: edit the runtime's `model_config.yaml`. No code change required. No Studio code is affected.

---

## Provider Registry (non-exhaustive)

For surfaces that need a direct-provider fallback (e.g., `phase11_chat_live_provider_execution_executor.py`), the provider registry allows any of these:

| provider_id | Env var | Endpoint |
|------------|---------|---------|
| `openai` | `OPENAI_API_KEY` | `https://api.openai.com/v1/chat/completions` |
| `anthropic` | `ANTHROPIC_API_KEY` | `https://api.anthropic.com/v1/messages` |
| `ollama` | *(none — local)* | `$OLLAMA_BASE_URL/v1/chat/completions` |
| `openai-compatible` | `OPENAI_COMPATIBLE_API_KEY` | `$OPENAI_COMPATIBLE_BASE_URL/v1/chat/completions` |

For bus-routed runtimes (`hermes`, `openclaw`, `chaser_agent`): dispatch via `agent_bus.create_task()` instead of a direct HTTP call.

---

## What Is NOT Permitted

- Hardcoding `provider_id = "openai"` anywhere in Studio code
- Checking `if provider_id != "openai": block(...)` — this is an architecture violation
- Reading `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in Studio surfaces for actual API calls
- Embedding model names (`gpt-4`, `claude-haiku`, etc.) as required constants in Studio
- Calling `https://api.openai.com` or `https://api.anthropic.com` from Studio panels

---

## What Is Permitted

- Runtimes (Hermes, OpenClaw, Chaser Agent) calling providers directly — they own those credentials
- `phase11_chat_live_provider_execution_executor.py` as an approval-gated fallback path — but with multi-provider support, not OpenAI-only
- SBP `execution_adapter` field pointing to a specific runtime — the runtime handles provider selection
- Personal context import proof referencing a configurable provider via env var

---

## Phase 11 Chat Dispatch (canonical path)

The primary Chat path is already provider-agnostic:

```python
# runtime/studio/phase11_chat_send_message.py — CORRECT
agent_bus.create_task(
    vault_root=vault,
    task_type="chat",
    sender="Codex",
    recipient=configured_runtime,  # Hermes | OpenClaw | Chaser Agent
    message=user_message,
)
```

The fallback direct-provider path (`phase11_chat_live_provider_execution_executor.py`) is approval-gated and multi-provider aware. It must not block on `provider_id != "openai"`.

---

## Enforcement

- Any new Studio feature that calls a model provider must route through Agent Bus
- PR reviews must flag direct provider calls in `runtime/studio/` as architecture violations
- `runtime/workflows/` and `runtime/sbp/` code is runtime-layer code and may call providers directly via the shared `execute_synthesis()` adapter
- Model config lives in `runtime/[runtime]/model_config.yaml` — never hardcoded

---

## Related Documents

- `06_AGENTS/ChaseOS-MCP-Server.md` — MCP server and scoped vault surfaces
- `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md` — Agent Bus architecture
- `06_AGENTS/Chaser-Agent-Runtime-Profile.md`, `Hermes-Runtime-Profile.md`, `OpenClaw-Runtime-Profile.md`
- `runtime/execution_adapters/execute.py` — shared `execute_synthesis()` adapter used by runtimes
