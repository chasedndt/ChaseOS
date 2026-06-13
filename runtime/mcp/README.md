# ChaseOS Runtime MCP

**Status:** partial MCP-compatible JSON-RPC stdio surface with bounded ChaseOS resources/tools/prompts and local process-boundary client smoke proof.

This directory contains ChaseOS-owned Runtime MCP infrastructure. It is not a public MCP deployment and does not expose shell, broad filesystem access, secret access, or canonical writeback.

The stdio server now accepts newline-delimited JSON-RPC 2.0 MCP-style requests for the supported methods below while preserving the older internal ChaseOS JSON request shape.

The local smoke harness in `runtime/mcp/client_smoke.py` starts `python -m runtime.mcp.server` as a child process and verifies bounded JSON-RPC calls over stdin/stdout. It is a local compatibility proof, not a public deployment or live OpenAI/n8n connection.

## Current Surface

Resources are read-only. Tools are bounded to proposal/draft/audit paths. Prompts are static templates.

New ChaseOS-named aliases added 2026-04-27:
- resources: `chaseos.current_state`, `chaseos.project_summary`, `chaseos.operator_brief_latest`, `chaseos.sic_workspace_summary`, `chaseos.adapter_status`, `chaseos.rnd_register_summary`, `chaseos.runtime_surfaces_summary`
- tools: `chaseos.generate_operator_brief_draft`, `chaseos.create_research_digest_draft`, `chaseos.prepare_discord_alert_draft`, `chaseos.query_sic_evidence`, `chaseos.validate_writeback_target`
- prompts: `chaseos.operator_today_prompt`, `chaseos.research_ingest_prompt`, `chaseos.adapter_handoff_prompt`, `chaseos.risk_review_prompt`

ARSL summary exposure added 2026-05-03:
- legacy resource: `runtime.surfaces`
- JSON-RPC alias: `chaseos.runtime_surfaces_summary`
- scope: curated read-only Adaptive Runtime Surface Layer summary only
- explicitly not exposed: raw manifests, route execution, ARSL ledger writes, provider calls, browser control, credentials, cookies, browser profiles, and MCP write/apply tools

JSON-RPC methods implemented 2026-04-27:
- `initialize`
- `ping`
- `resources/list`
- `resources/templates/list`
- `resources/read`
- `tools/list`
- `tools/call`
- `prompts/list`
- `prompts/get`
- `notifications/initialized` as a notification with no response

The JSON-RPC surface intentionally lists only the ChaseOS-named safe aliases. Older internal resources/tools remain available through the legacy ChaseOS request envelope for existing local callers.

## Non-Goals

- No public HTTP server in this pass.
- No live remote MCP bridge in this pass.
- No credential handling in this directory.
- No canonical vault mutation through MCP.
- No full third-party client certification yet; local process-boundary stdio smoke is verified for the methods above.

See `06_AGENTS/ChaseOS-Runtime-MCP.md` for the governance spec.
