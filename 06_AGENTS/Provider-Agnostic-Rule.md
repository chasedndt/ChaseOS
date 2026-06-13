---
type: governance
domain: agent-execution
status: active
version: "1.0"
created: 2026-05-18
---

# Provider-Agnostic Rule

**Rule:** ChaseOS workflows and Studio modules must never call model providers directly.
All LLM dispatch must route through `execute_synthesis()` (execution adapter layer) or
the Agent Bus. No workflow, handler, or Studio module may embed provider endpoints,
hardcode model IDs, or read API key environment variables for synthesis purposes.

---

## Why This Rule Exists

Direct provider calls in workflow code create three governance failures:

1. **Unconstrained spending** — a workflow calling an API by default runs on every
   trigger without operator awareness. The C-2 security finding (2026-05-11) found
   `synthesize` defaulting to `True` in Hermes workflows, meaning every hermes_watch
   cycle would call the Anthropic API without any operator opt-in.

2. **Model lock-in** — hardcoding `claude-haiku-4-5-20251001` or `gpt-4o-mini` inside
   a workflow prevents model upgrades without code changes. The execution adapter layer
   reads model config from `runtime/{runtime}/model_config.yaml`, decoupling model
   choice from workflow logic.

3. **Auditability gap** — the provider state ledger (`runtime/providers/`) records every
   API call, fallback event, and rate-limit. Direct calls in workflow code bypass this
   ledger entirely, making cost and reliability tracking impossible.

---

## The Rule in Practice

### Allowed (correct pattern)

```python
# Workflows route through the execution adapter
from runtime.execution_adapters.execute import execute_synthesis

result = execute_synthesis(
    prompt_system="...",
    prompt_user="...",
    execution_adapter="hermes",  # or "openclaw"
    vault_root=vault_root,
)
```

The adapter resolves model config, handles fallbacks, and writes to the provider state
ledger. The workflow never touches a URL, model ID, or API key.

### Forbidden (violation pattern)

```python
# Never do this in a workflow or Studio module
import urllib.request
payload = {"model": "claude-haiku-4-5-20251001", ...}
req = urllib.request.Request("https://api.anthropic.com/v1/messages", ...)
```

---

## Enforcement Points

| Surface | Rule |
|---------|------|
| `runtime/workflows/*.py` | Must route synthesis through `execute_synthesis()` |
| `runtime/studio/*.py` | Must not embed provider endpoints or API key reads for synthesis |
| `runtime/sbp/*.py` | SBP pipelines must not call providers directly |
| Manifests (`*.yaml`) | `synthesize` inputs must document `default: False, opt-in only` |
| AOR engine (`engine.py`) | Stage 6 writeback never calls providers |

---

## Approved Exceptions

There is one approved exception to this rule:

### `runtime/studio/personal_context_import_provider_execution_proof.py`

**Why approved:** This module is a diagnostic credential-proof tool, not a synthesis
workflow. Its sole purpose is to confirm that a provider credential works. It never
produces canonical vault writes, never runs automatically, and is gated behind both
`execute=True` and a required `operator_approval_statement`. It is not a precedent for
direct provider calls elsewhere.

**Conditions for this exception to remain valid:**
- The module must never be called from an autonomous workflow path
- `execute=False` must remain the default
- `operator_approval_statement` gating must remain in place
- The `authority.canonical_writeback_allowed` flag must remain `False`

If any of these conditions changes, the exception must be re-reviewed.

---

## How to Add a New Provider-Calling Capability

If a new workflow genuinely needs LLM synthesis:

1. Set `synthesize: bool = False` (or `inputs.get("synthesize", False)`) as the default
2. Route the call through `execute_synthesis(execution_adapter="hermes")` (or `"openclaw"`)
3. Declare `llm_synthesis_enabled: false` in the workflow manifest
4. Add the workflow to the `synthesize` opt-in list in the relevant test suite
5. Do NOT embed model IDs, provider URLs, or API key env var reads in the workflow

If the capability genuinely requires direct provider access (e.g., a new credential
verification proof module), create a dedicated proof module matching the pattern in
`personal_context_import_provider_execution_proof.py` and document the exception here.

---

## Audit History

| Date | Event |
|------|-------|
| 2026-05-11 | Security audit found C-2: `synthesize` defaulting `True` in Hermes workflows |
| 2026-05-18 | C-2 fixed: all `synthesize` defaults changed to `False` across 5 files |
| 2026-05-18 | `hermes_research_synthesis.py` direct urllib/Anthropic call replaced with `execute_synthesis()` |
| 2026-05-18 | This governance doc created; proof module annotated as approved exception |
