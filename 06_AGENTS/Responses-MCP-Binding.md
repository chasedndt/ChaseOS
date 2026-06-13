# Responses API MCP Binding

**Status:** DRY-RUN IMPLEMENTED  
**Created:** 2026-04-27  
**Code:** `runtime/adapters/openai/responses_mcp_payload.py`  
**Policy:** `runtime/policy/adapters/responses_api.yaml`

---

## Purpose

This binding defines how ChaseOS may later call the OpenAI Responses API with MCP tools while preserving ChaseOS control-plane rules.

The first pass is not a live OpenAI integration. It builds auditable JSON payload templates and blocks unsafe policy shapes.

---

## Remote MCP vs Connectors

| Type | Meaning | ChaseOS rule |
|---|---|---|
| Remote MCP server | A third-party or self-hosted server reachable by URL | Trust boundary; require allowlist, approval, audit |
| OpenAI connector | OpenAI-maintained connector identified by connector id | Still a third-party data-sharing path; require approval and audit |
| ChaseOS Runtime MCP | ChaseOS-owned local/control-plane interface | Preferred internal surface, bounded by ChaseOS policy |

Do not connect remote MCP servers blindly. Tool definitions, tool outputs, URLs, and annotations from external servers are not ChaseOS truth.

---

## Approval Policy

Payloads must use:
- `tools[].type: "mcp"`
- explicit `server_label`
- exactly one of `server_url` or `connector_id`
- explicit `allowed_tools` for first-pass use
- `require_approval: "always"` or stricter object policy

First-pass policy forbids `require_approval: "never"`.

---

## Allowed Initial Use Cases

- read-only research context;
- workflow draft creation;
- source lookup;
- Discord draft generation.

## Forbidden First-Pass Use Cases

- credential access;
- wallet/exchange execution;
- direct trading;
- filesystem mutation outside declared write targets;
- live Discord/Telegram alerts without approval.

---

## Data That Must Never Be Sent

- secrets, credentials, `.env` values;
- wallet keys or seed phrases;
- exchange API keys;
- unrelated personal files;
- protected canonical state;
- raw quarantine content treated as instructions.

---

## Dry-Run Builder

`build_responses_mcp_payload(...)` creates a payload template with:
- `dry_run: true`
- `live_api_call: false`
- approval metadata
- data-sharing warning
- forbidden data classes
- MCP allowed tool list

`validate_payload_policy(...)` enforces the dry-run policy. `write_payload_draft(...)` stores templates under `07_LOGS/Agent-Activity/_dry_run_payloads/`.

No OpenAI client is imported. No API key is read. No network call is made.

---

## External Docs Checked

- [OpenAI MCP/connectors guide](https://platform.openai.com/docs/guides/tools-remote-mcp?lang=python)
- [OpenAI Responses API reference](https://platform.openai.com/docs/api-reference/responses/compact?api-mode=responses)
- [MCP tools concept](https://modelcontextprotocol.io/docs/concepts/tools)
- [MCP transports](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
