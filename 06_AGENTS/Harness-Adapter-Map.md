# Harness / Adapter Map

**Status:** UPDATED 2026-04-27  
**Purpose:** place execution surfaces precisely without calling every tool a runtime.

---

| Surface | Type | Authority | Read scope | Write scope | Approval model | Audit model | Current status | Integration path |
|---|---|---|---|---|---|---|---|---|
| Claude Code / Antigravity | Repo-aware implementation harness | Tier 2 when configured | Repo/vault under harness rules | Bounded by Gate/hooks | Human + Gate | Build logs, docs history, Agent Activity | Claude verified; Antigravity historical | Reference harness lane |
| Codex | Repo-aware implementation/review harness | Bounded editor/proposer in this session | Repo/vault under Codex session rules | Explicit task files + required logs | User instruction + sandbox approvals | Build logs, docs history, Agent Activity | Active current harness; formal vault binding still evolving | Implementation/review lane |
| OpenAI Agents SDK | Programmable harness adapter | Not live; Tier 2 ceiling only after approval | Declared context/MCP only | Draft/audit only now | Deny-by-default | Agent Activity + AOR audit | Shadow proof | `openai_operator_research_shadow` |
| Responses API | Model/tool/MCP call path | Not live | Payload-defined; remote MCP trust boundary | None in first pass | `require_approval` required | Dry-run payloads | Dry-run builder | `Responses-MCP-Binding.md` |
| ChatGPT Apps SDK | Future UI surface | None now | Future MCP app server | Future approved UI actions | App review + ChaseOS approval | TBD | Planned | Phase 10+ UI planning |
| ChaseOS Runtime MCP | Internal MCP/control interface | ChaseOS-owned bounded server | Allowlisted resources | Draft/proposal/audit only | Safety mode envelope | MCP audit records | Internal stdio skeleton | Runtime tool boundary |
| n8n | Workflow hub / MCP client+server candidate | Planned Tier 2 ceiling | Workflow-scoped | Inputs/logs/drafts only | Per-workflow + production approval with audit record | Agent Activity + governed call/proof audit | Dry-run policy + connection readiness + call governance + MCP proof artifacts; live blocked | Workflow exposure registry + MCP readiness helper + governed draft builder + proof runner |
| Hermes | Bounded/shadow runtime adapter | Narrow Tier 2 shadow | Declared workflow context | Draft/audit only | Workflow approval | Agent Activity/AOR | Active bounded shadow | Adapter contract only |
| OpenClaw | High-privilege local runtime adapter | High-risk bounded local | Declared local scope | Bounded by AOR/Gate | Explicit approval for high-risk | AOR/Gate/logs | Active bounded local | No privilege expansion here |
| Local/OSS models | Provider lane / future harness backend | Future | Same adapter contract | Same adapter contract | Same approval model | Same audit model | Planned/future | Provider behind ChaseOS contract |
| Browser/computer-use surfaces | Operator surface / tool surface | High-risk bounded | Target-scoped | Screenshot/log/draft only | Approval for actions | Operator Surface logs | Partial/parked where implemented | FSOS/Operator Surface |

---

## Core Rule

Agents do not get raw authority. They get scoped tools. Tools are bounded. Risky actions require approval. Meaningful action is logged. Canonical writeback goes through ChaseOS governance.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
