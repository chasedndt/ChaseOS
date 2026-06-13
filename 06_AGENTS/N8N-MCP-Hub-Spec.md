# n8n MCP Hub Spec

**Status:** DOCS + DRY-RUN POLICY + CONNECTION READINESS + CALL GOVERNANCE + PROOF ARTIFACT RUNNER IMPLEMENTED + LIVE EXECUTOR IMPLEMENTED (blocked pending operator setup)  
**Created:** 2026-04-27  
**Policy:** `runtime/policy/adapters/n8n.yaml`  
**Registry:** `runtime/policy/adapters/n8n_workflows.yaml`  
**Policy Helper:** `runtime/adapters/n8n/workflow_policy.py`  
**Connection Helper:** `runtime/adapters/n8n/mcp_connection.py`  
**Call Governance Helper:** `runtime/adapters/n8n/call_governance.py`  
**Proof Artifact Helper:** `runtime/adapters/n8n/mcp_live_proof.py`
**Live Executor:** `runtime/adapters/n8n/executor.py`

---

## Position

n8n is a workflow automation hub and external-service router. It is not ChaseOS truth, not a model provider, and not a broad vault runtime.

ChaseOS owns permissions, approval, audit, and canonical writeback. n8n receives scoped workflows only.

---

## A. n8n As MCP Client

n8n may later consume ChaseOS Runtime MCP resources/tools.

Initial client use cases:
- ask ChaseOS for current project state;
- ask ChaseOS for draft brief context;
- validate whether a workflow output can be promoted;
- request a research digest draft.

Allowed first surfaces:
- `chaseos.current_state`
- `chaseos.operator_brief_latest`
- `chaseos.create_research_digest_draft`
- `chaseos.validate_writeback_target`

No n8n MCP client connection is live in this pass.

---

## B. n8n As MCP Server

n8n may later expose selected workflows through MCP to OpenAI, Claude/Codex, or other approved agents.

First safe workflow candidates:
- `send_discord_draft_alert`
- `create_calendar_review_block`
- `capture_research_digest`
- `route_webhook_to_quarantine`
- `prepare_trade_journal_draft`
- `notify_operator_for_approval`

The registry requires:
- workflow id;
- purpose;
- `exposed_to_mcp`;
- trigger type;
- approval requirement;
- allowed callers;
- reads/writes;
- secrets required;
- current status.

Instance-level MCP connection readiness now exists locally. It validates:
- n8n deployment config;
- declared env var names for base URL and MCP access token;
- local-only endpoint policy by default;
- workflow registry validity;
- redacted token presence without logging credential values.

The helper can run a live HTTP initialize probe only when explicitly invoked with `--live-probe` and the config/env state is safe. In the current workspace, this is blocked because n8n deployment is disabled and no base URL/token is configured.

Dry-run call governance now exists locally. It can:
- create pending approval request records;
- record one immutable operator decision per request;
- resolve approval state for a workflow/caller pair;
- build governed n8n call drafts with approval metadata;
- write those drafts only to `07_LOGS/Agent-Activity/_n8n_call_drafts/`;
- reject credential-shaped payload keys before anything is logged.

Even with an approved record, the helper emits dry-run JSON only. It does not call n8n, enable a workflow, post to Discord/Telegram, mutate canonical ChaseOS state, or execute production side effects.

MCP proof artifacts now exist locally. The proof helper can:
- build a redacted readiness proof without HTTP;
- write proof JSON to `07_LOGS/Agent-Activity/_n8n_mcp_proofs/`;
- optionally attempt a live local-only MCP initialize probe when explicitly requested;
- summarize probe response metadata without logging token values or raw response excerpts.

The current workspace proof is blocked and no live HTTP call was made because deployment is disabled, secrets are unconfigured, and the required n8n env vars are unset.

---

## Restrictions

Forbidden:
- live trading execution;
- wallet/exchange signing;
- credential exposure;
- autonomous canonical writeback;
- exposing all workflows by default;
- production Discord/Telegram posting without approval.

Approval required:
- production n8n execution;
- external-service write;
- MCP-exposed workflow execution;
- workflow deployment or changed secret scope.

Allowed now:
- registry validation;
- dry-run call draft generation;
- approval request/decision audit records for n8n draft calls;
- governed dry-run call draft audit writes;
- connection readiness checks;
- redacted MCP readiness/proof artifact writes;
- local-stub live probe tests;
- docs/policy registration.

Blocked now (pending operator setup — see Section C):
- real n8n MCP live probe;
- instance-level n8n workflow execution (executor built, blocked by config — see Section C.1);
- third-party MCP client connection to n8n;
- external service writes from n8n.

---

## C. Self-Hosted Setup + Use Case Planning

This section is a pre-deployment planning document. n8n is not yet running. The live executor is built and gated — once the operator completes Section C.1, live workflow execution is immediately available via `chaseos n8n execute`.

---

### C.1 — Self-Hosted Setup Checklist

n8n is designed for self-hosting via Docker. The ChaseOS local-only policy (`local_only: true` in `n8n_config.yaml`) enforces that n8n is never routed to an external cloud instance.

**Recommended stack:** Docker Desktop on same machine as this vault.

```bash
docker run -d \
  --name chaseos-n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=<your-password> \
  n8nio/n8n
```

n8n UI will be at `http://localhost:5678`. MCP server will be at `http://localhost:5678/mcp-server/http` (requires instance-level MCP enabled in n8n settings).

**Once n8n is running, enable ChaseOS live execution:**

1. Set env var: `N8N_BASE_URL=http://localhost:5678`
2. Set env var: `N8N_MCP_ACCESS_TOKEN=<token from n8n settings>`
3. Edit `runtime/policy/adapters/n8n_config.yaml`: set `enabled: true` and `secrets_configured: true`
4. Run `chaseos n8n readiness` — confirms all four gate conditions are met
5. First live test: `chaseos n8n execute send_discord_draft_alert --caller chaseos`

The readiness command shows all blocking reasons without making any HTTP calls. It is safe to run at any time.

---

### C.2 — Personal Dashboard Integration

Chase's personal dashboard runs through the OpenClaw/Discord control surface. n8n can extend the dashboard in two directions:

**Inbound (n8n → ChaseOS):** n8n workflows trigger actions that land in the ChaseOS operator pipeline — briefings, digest delivery, acquisition runs.

**Outbound (ChaseOS → n8n):** The AOR engine or SBP pipeline trigger n8n workflows for external-service operations (posting to Discord, Whop, calendars) that ChaseOS itself does not own natively.

Personal dashboard touch points and how n8n connects to each:

| Dashboard Element | How n8n Extends It |
|---|---|
| Morning operator briefing (0700 ET) | n8n webhook receives AOR trigger → enriches briefing with external data (calendar, price feeds, email summary) before `operator_today` runs |
| StrikeZone digest (0600 ET) | n8n runs acquisition feeds (RSS, scrape) at 0550 ET → posts result to n8n webhook → ChaseOS `strikezone_acquisition` picks up; OR SBP triggers `send_discord_draft_alert` workflow after digest is produced |
| Discord alert delivery | SBP `DiscordDeliveryAdapter` can be replaced or supplemented by n8n webhook delivery for richer message formatting (embeds, buttons) |
| Approval notifications | When an AOR action requires approval, n8n can route the notification to Discord DM or a separate approval channel rather than the ops channel |
| Close-of-day summary (1900 ET) | n8n workflow collects external signals (trade summary, calendar events, unread priority messages) and POSTs them to a ChaseOS webhook for inclusion in `operator_close_day` |

---

### C.3 — ChaseOS Feature Hooks (Concrete Workflow Candidates)

These are starter workflows to build once n8n is running. Ordered by value/effort ratio.

#### W1 — `send_discord_draft_alert`
**Trigger:** webhook (already in registry as draft)
**Purpose:** Receives a StrikeZone digest or operator brief excerpt and posts a formatted Discord embed to the ops channel.
**Why n8n instead of native:** n8n's Discord node handles embeds, button components, and retry natively. The SBP `DiscordDeliveryAdapter` uses raw webhook POSTs without embeds.
**ChaseOS trigger:** SBP pipeline at end of `sbp_strikezone_digest.py` — replace or supplement current Discord delivery.
**Status:** Registry entry exists. Blocked pending n8n instance.

#### W2 — `notify_operator_for_approval`
**Trigger:** webhook
**Purpose:** When the AOR engine escalates an action requiring approval, ChaseOS POSTs to this workflow. n8n routes to Discord DM (not ops channel) + optionally sends an iOS push notification.
**Why n8n:** ChaseOS can POST a simple JSON payload. n8n handles the routing to multiple channels, retry on failure, and any custom formatting.
**ChaseOS trigger:** AOR `escalate_required_approval` event → POST to n8n webhook.
**Status:** Not yet in registry. Add to `n8n_workflows.yaml` before first use.

#### W3 — `create_calendar_review_block`
**Trigger:** webhook
**Purpose:** After `operator_today` runs, ChaseOS can trigger this workflow to create a calendar block for the day's review time (Google Calendar, Notion Calendar, or Fantastical via URL scheme).
**Why n8n:** Calendar API auth is complex; n8n has pre-built Google Calendar nodes that handle OAuth.
**ChaseOS trigger:** `operator_today` handler last stage — optional POST if `N8N_BASE_URL` is set.
**Status:** Not yet in registry.

#### W4 — `capture_research_digest`
**Trigger:** MCP tool (exposed via n8n instance MCP)
**Purpose:** Claude/Codex or the ChaseOS MCP client calls this tool with a research query. n8n runs Perplexity/search nodes, assembles result, and returns it. ChaseOS writes to quarantine.
**Why n8n:** n8n can fan out to multiple search APIs simultaneously (Perplexity, Brave, Exa) with a single MCP tool call. Currently ChaseOS calls each connector individually.
**Status:** Registry entry exists. Requires MCP server mode on n8n. Add after W1/W2 are proven.

#### W5 — `prepare_trade_journal_draft`
**Trigger:** webhook
**Purpose:** After a trading session, ChaseOS posts a trade summary payload. n8n formats it into a journal template and writes back to a ChaseOS webhook or directly to a Notion page.
**Why n8n:** Trade data formatting and Notion API auth are better handled in n8n. ChaseOS captures the intent and the final artifact — not the transformation.
**ChaseOS trigger:** Manual `chaseos n8n execute prepare_trade_journal_draft --caller chaseos --payload '{...}'`.
**Status:** Registry entry exists.

#### W6 — `route_webhook_to_quarantine`
**Trigger:** webhook (inbound from any external service)
**Purpose:** n8n acts as a universal inbound webhook receiver. Any external service (Stripe, GitHub webhooks, price alerts) POSTs to n8n. n8n normalizes the payload and forwards to ChaseOS capture endpoint. ChaseOS handles it as a quarantined input.
**Why n8n:** Allows ChaseOS quarantine to receive events from any service without exposing ChaseOS directly to the internet.
**Status:** Registry entry exists.

---

### C.4 — Acquisition Pipeline Trigger Pattern

The current StrikeZone acquisition flow runs on a ChaseOS cron schedule (`sch-strikezone-acquisition-0550.yaml`). n8n can participate in two ways:

**Option A (n8n as trigger):** n8n cron at 0550 ET calls `chaseos n8n execute strikezone_acquisition --caller n8n` via the MCP tool interface. ChaseOS runs the acquisition, writes the artifact, and the 0600 digest picks it up via latest-pointer. Advantage: n8n controls schedule pacing and can retry on failure.

**Option B (n8n as enrichment layer):** ChaseOS acquisition runs on its own schedule. At the end of acquisition, ChaseOS triggers n8n `capture_research_digest` to supplement RSS/scrape data with a fresh Perplexity query. n8n returns structured results; ChaseOS merges them into the artifact store before the digest runs.

Current recommendation: **Option A first** — simpler, gives n8n a working trigger pattern, and validates the live executor before adding enrichment complexity.

---

### C.5 — Agent Bus Event Hooks

The agent bus (`runtime/agent_bus/`) generates events (task created, claimed, completed, blocked, escalated) that are currently only written to the SQLite backend and read by Hermes/OpenClaw watch loops.

n8n can subscribe to agent bus events via a polling webhook pattern:

1. ChaseOS writes bus events normally.
2. A lightweight `chaseos agent-bus export --since TIMESTAMP --json` command (not yet built) streams recent events.
3. An n8n scheduled workflow polls this endpoint every N minutes.
4. n8n routes events to Discord, dashboards, or external logging.

This pattern avoids exposing the SQLite backend directly. The n8n workflow only sees sanitized event payloads.

**What to notify on:**
- `task_blocked` with high-priority → Discord DM to Chase
- `task_result_attached` with review outcome → post to ops Discord thread
- Hermes synthesis complete → post excerpt to StrikeZone community Discord channel
- Recurring failures on same workflow → trigger `notify_operator_for_approval`

---

### C.6 — Deployment Decisions and Constraints

**Local-only enforced:** `local_only: true` in `n8n_config.yaml`. ChaseOS will refuse to connect to a remote n8n URL. This is intentional — workflows that access vault content must not leave the local machine.

**Credential boundary:** n8n holds its own credentials for external services (Google, Discord, Whop). These are stored in n8n's encrypted credential store, not in ChaseOS env vars. ChaseOS holds only `N8N_BASE_URL` and `N8N_MCP_ACCESS_TOKEN`. No external service credential ever passes through the ChaseOS layer.

**Approval gate:** Any n8n workflow with `approval_required: true` in the registry cannot run in production mode without an approval record. The `notify_operator_for_approval` workflow (W2) is the canonical path for requesting that approval.

**Audit:** Every live execution via `execute_n8n_workflow()` returns a result dict with `executed_at_utc`, `workflow_id`, `caller`, `trigger_type`, `http_status`, and `response_excerpt`. These are available for SBP/AOR pipeline logging. Persistent audit writeback to `07_LOGS/` is deferred (listed in Phase 9 deferred items).

---

## External Docs Checked

- [n8n MCP Client node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-langchain.mcpClient/)
- [n8n MCP Client Tool node](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp/)
- [n8n MCP Server Trigger node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-langchain.mcptrigger/)
- [n8n instance-level MCP server](https://docs.n8n.io/advanced-ai/mcp/accessing-n8n-mcp-server/)

Doc refresh note 2026-04-27: official n8n docs state instance-level MCP access requires explicit enablement, authentication by OAuth2 or access token, and opt-in workflow exposure. MCP Server Trigger remains a workflow-specific server pattern.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
