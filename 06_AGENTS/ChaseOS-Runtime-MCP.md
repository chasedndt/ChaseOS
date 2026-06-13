# ChaseOS Runtime MCP

**Status:** PARTIAL MCP JSON-RPC STDIO COMPATIBILITY + LOCAL CLIENT SMOKE VERIFIED  
**Created:** 2026-04-27  
**Existing implementation:** `runtime/mcp/`

---

## Repo Truth

Runtime MCP already exists as an internal ChaseOS stdio JSON server. It implements:
- safety modes;
- permission envelopes;
- resource/tool/prompt registries;
- proposal staging;
- audit records;
- bounded AOR workflow invocation for approved workflows.

The adapter-foundation pass did not replace that implementation. It added ChaseOS-named safe aliases that match the OpenAI/n8n adapter foundation.

The follow-on stdio compatibility pass added a JSON-RPC 2.0 wrapper for core MCP methods while keeping the older ChaseOS internal JSON request envelope working.

The client-smoke pass added a local process-boundary smoke client that launches `python -m runtime.mcp.server` as a child process and verifies JSON-RPC over stdin/stdout against the actual workspace root. This proves the local stdio path, not a public or third-party-hosted MCP deployment.

---

## Transport Position

Current:
- newline-delimited stdio JSON server in `runtime/mcp/server.py`;
- JSON-RPC 2.0 request/response handling for a bounded MCP method set;
- local process-boundary stdio smoke client in `runtime/mcp/client_smoke.py`;
- legacy ChaseOS request envelope preserved for existing internal callers;
- no public HTTP endpoint;
- no shell execution;
- no broad filesystem traversal;
- no secret access;
- no canonical writeback.

Future:
- real third-party MCP client smoke test and/or official MCP SDK integration;
- Streamable HTTP wrapper only after auth, origin validation, localhost binding, and audit behavior are specified.

---

## JSON-RPC MCP Method Set

Implemented:
- `initialize`
- `ping`
- `resources/list`
- `resources/templates/list`
- `resources/read`
- `tools/list`
- `tools/call`
- `prompts/list`
- `prompts/get`
- `notifications/initialized` as a no-response notification

The JSON-RPC surface lists only the ChaseOS-named safe aliases below. Legacy internal Runtime MCP surfaces remain accessible through the existing ChaseOS request envelope, not through the JSON-RPC public-facing list.

Limitations:
- no Streamable HTTP transport;
- no OAuth/auth layer;
- no live OpenAI/n8n/Claude external client connection tested;
- no official SDK or third-party client smoke yet;
- no broad MCP server exposure;
- no MCP resource subscriptions;
- no full prompt/tool schema enrichment beyond stable object shapes.

---

## Resources

Read-only ChaseOS-named resources added:
- `chaseos.current_state`
- `chaseos.project_summary`
- `chaseos.operator_brief_latest`
- `chaseos.sic_workspace_summary`
- `chaseos.adapter_status`
- `chaseos.rnd_register_summary`
- `chaseos.runtime_surfaces_summary`

Existing resources remain:
- `runtime.identity`
- `runtime.capabilities`
- `runtime.surfaces`
- `chaseos.current_truth`
- `workflows.registry`
- `workflows.role_boundaries`
- `runtime.permission_envelope`
- `runtime.handoff.current`
- `runtime.audit.recent`
- `operator.briefing.latest`

---

## Tools

Bounded ChaseOS-named tools added:
- `chaseos.generate_operator_brief_draft`
- `chaseos.create_research_digest_draft`
- `chaseos.prepare_discord_alert_draft`
- `chaseos.query_sic_evidence`
- `chaseos.validate_writeback_target`

These tools only write draft/audit artifacts or return read-only summaries. They reject canonical/protected write targets.

Existing tools remain:
- `proposal.submit`
- `proposal.validate`
- `proposal.diff_preview`
- `approval_request.create`
- `workflow.invoke_bounded`

---

## Prompts

Static prompt templates added:
- `chaseos.operator_today_prompt`
- `chaseos.research_ingest_prompt`
- `chaseos.adapter_handoff_prompt`
- `chaseos.risk_review_prompt`

Prompts are template-only and load no hidden context.

---

## Hard Restrictions

- no shell;
- no delete/rename/move;
- no secret reading;
- no `.env`;
- no canonical writeback;
- no production external sends;
- no trading;
- no wallet/exchange signing;
- no public deployment in this pass.

---

## External Docs Checked

- [MCP resources](https://modelcontextprotocol.io/docs/concepts/resources)
- [MCP tools](https://modelcontextprotocol.io/docs/concepts/tools)
- [MCP prompts](https://modelcontextprotocol.io/docs/concepts/prompts)
- [MCP transports](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)
- [MCP schema](https://modelcontextprotocol.io/specification/2025-11-25/schema)


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
