# OpenAI Adapter Spec

**Status:** PARTIAL / SHADOW PROOF  
**Created:** 2026-04-27  
**Runtime owner:** ChaseOS  
**Adapter role:** OpenAI is an adapter/harness candidate, not ChaseOS truth.

---

## Position

OpenAI fits ChaseOS as a set of external execution and UI surfaces behind ChaseOS governance:

| Surface | Role | Current status |
|---|---|---|
| ChatGPT | Advisory chat surface | ACTIVE advisory; user-mediated import only |
| Codex | Repo-aware implementation/review harness | ACTIVE as this development surface; ChaseOS policy still governs writeback |
| OpenAI Agents SDK | Programmable harness candidate | SHADOW PROOF via `openai_operator_research_shadow`; no live API call |
| Responses API | Model/tool/MCP call path | DRY-RUN payload builder only |
| Remote MCP / connectors | External tool binding path | DOCS + DRY-RUN policy only |
| ChatGPT Apps SDK | Future UI surface through MCP app model | PLANNED; no app deployed |

OpenAI supplies model execution and tool orchestration. ChaseOS owns context selection, permissions, writeback, logs, promotion, and canonical truth.

---

## First Use Case

`openai_operator_research_shadow` is the first concrete use case.

It:
- reads a narrow declared context packet;
- prepares a local operator/research draft;
- prepares a Responses API MCP payload template;
- optionally prepares an n8n workflow call draft;
- writes only draft/audit artifacts through AOR;
- does not mutate `00_HOME/Now.md`, Project-OS files, `02_KNOWLEDGE/`, Discord, Telegram, trading systems, wallets, exchanges, or live external services.

Implementation:
- `runtime/workflows/registry/openai_operator_research_shadow.yaml`
- `06_AGENTS/role-cards/openai-operator-shadow.yaml`
- `runtime/workflows/openai_shadow.py`
- `runtime/policy/adapters/openai_config.yaml`

---

## Approval Model

Allowed without further approval:
- read declared context packet;
- build dry-run Responses MCP payload;
- build dry-run n8n call draft;
- write draft/audit artifacts under declared targets.

Approval required before future activation:
- live OpenAI API call;
- live remote MCP call;
- connector use that sends ChaseOS context to a third party;
- live n8n workflow execution;
- live Discord/Telegram notification.

Forbidden first pass:
- secrets or `.env` access;
- wallet/exchange signing;
- direct trading;
- canonical writeback;
- autonomous knowledge promotion;
- broad filesystem access;
- shell execution.

---

## Audit And State

OpenAI adapter state is not canonical ChaseOS state. The current implementation stores evidence in:
- draft outputs: `07_LOGS/Operator-Briefs/_drafts/`
- activity/audit: `07_LOGS/Agent-Activity/`
- adapter policy: `runtime/policy/adapters/openai.yaml`
- shadow config: `runtime/policy/adapters/openai_config.yaml`

Future live Agents SDK state must be replayable through ChaseOS audit records, not hidden in provider session state.

---

## Differences From Other Surfaces

| Surface | Difference |
|---|---|
| Codex | Codex is a repo-aware engineering/review harness in this session; OpenAI Agents SDK would be an application-programmed runtime adapter. |
| Claude Code | Claude Code has verified Anthropic/Gate enforcement history; OpenAI harness enforcement is not verified. |
| OpenClaw | OpenClaw is high-privilege local runtime and remains bounded; OpenAI must not inherit local privilege. |
| Hermes | Hermes is an active bounded Discord/runtime-bus lane; OpenAI must not inherit Hermes gateway or bus authority. |
| n8n | n8n is a workflow hub/router, not a model provider. |
| Local/OSS | Local/OSS models remain future provider lanes behind the same adapter contract. |

---

## Implemented Now

- Shadow workflow manifest, role card, config, and handler.
- Responses API MCP dry-run payload builder.
- Policy-backed no-live-call posture.
- Draft/audit-only AOR writeback path.

## Planned

- Real Agents SDK proof with API key configured outside repo.
- Real remote MCP approval loop.
- Hosted/local ChaseOS Runtime MCP compatibility pass.
- ChatGPT Apps SDK UI planning only after backend boundaries are proven.

---

*Graph links: [[OPENAI]] · [[OpenAI-Adapter-Spec]] · [[Codex-Runtime-Profile]] · [[Runtime-Navigation-Map]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Runtime-Instance-Authority-Parity]] · [[Execution-Adapter-Standard]] · [[Vault-Map]] · [[Permission-Matrix]] · [[Trust-Tiers]]*

---

## External Docs Checked

- [OpenAI Agents SDK quickstart](https://openai.github.io/openai-agents-python/quickstart/)
- [OpenAI Agents SDK guardrails](https://openai.github.io/openai-agents-python/guardrails/)
- [OpenAI Agents SDK results/state](https://openai.github.io/openai-agents-python/results/)
- [OpenAI Responses MCP/connectors](https://platform.openai.com/docs/guides/tools-remote-mcp?lang=python)
- [ChatGPT Apps SDK](https://developers.openai.com/apps-sdk)

