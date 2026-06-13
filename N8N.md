# N8N.md — n8n Workflow Runtime Adapter for ChaseOS

> This is the execution adapter document for the n8n self-hosted workflow runtime operating in ChaseOS.
> n8n is a workflow / operator runtime adapter — not a chat surface, not a general-purpose harness.
> Status: **Planned** — n8n is not yet deployed or active in ChaseOS.
> Conformance standard: `[[06_AGENTS/Execution-Adapter-Standard|Execution-Adapter-Standard]]`
> Registry entry: `[[06_AGENTS/Agent-Registry|Agent-Registry]]` — "n8n — Self-Hosted (Planned)"
> Security model: `[[06_AGENTS/Agent-Security-Model|Agent-Security-Model]]`

---

## 2026-04-27 MCP Hub Foundation Update

**Status:** n8n remains not deployed, but its MCP hub policy foundation is now PARTIAL / DRY-RUN.

Implemented now:
- `06_AGENTS/N8N-MCP-Hub-Spec.md`
- `runtime/policy/adapters/n8n_config.yaml`
- `runtime/policy/adapters/n8n_workflows.yaml`
- `runtime/adapters/n8n/workflow_policy.py`
- `runtime/adapters/n8n/mcp_connection.py`

Truth boundary:
- no n8n instance is configured;
- no n8n access token or secret is configured;
- no production workflow execution is enabled;
- no workflow is live-posting to Discord/Telegram;
- no trading, wallet, or exchange action is enabled;
- no n8n workflow may bypass ChaseOS Gate, AOR, or writeback policy.

n8n has two planned roles: MCP client consuming ChaseOS Runtime MCP surfaces, and MCP server exposing selected workflows to approved agents. Both remain policy/dry-run only.

### 2026-04-27 MCP Connection Readiness Update

**Status:** readiness harness implemented; real n8n connection blocked by missing deployment configuration.

Implemented now:
- connection readiness resolver using `runtime/policy/adapters/n8n_config.yaml`;
- redacted env-state reporting for `N8N_BASE_URL` and `N8N_MCP_ACCESS_TOKEN`;
- local-only MCP HTTP probe helper requiring explicit `--live-probe`;
- tests using a local HTTP stub, not a real n8n instance.

Current workspace readiness result:
- registry validates;
- exposed workflow list is policy-visible;
- `deployment.enabled` is false;
- `deployment.secrets_configured` is false;
- `N8N_BASE_URL` is not set;
- `N8N_MCP_ACCESS_TOKEN` is not set;
- no live HTTP call was made.

Activation remains blocked until a local or explicitly approved n8n instance is configured and the MCP access token is supplied outside the vault.

### 2026-04-27 Dry-Run Call Governance Update

**Status:** approval-aware dry-run call governance implemented; live workflow execution remains blocked.

Implemented now:
- approval request records under `07_LOGS/Agent-Activity/_n8n_approvals/`;
- immutable approval decision records under the same audit folder;
- governed dry-run call drafts under `07_LOGS/Agent-Activity/_n8n_call_drafts/`;
- secret-like payload key rejection before approval or draft audit writes;
- production-request policy validation only when a matching approval record is approved;
- blocked workflows, including `execute_trade_order`, cannot produce dry-run call drafts.

Truth boundary:
- approval records prove operator intent for a draft path only;
- governed call drafts still set `dry_run: true` and `live_http_call: false`;
- no HTTP runner, webhook caller, Discord poster, Telegram sender, wallet signer, or trading action was enabled;
- approval does not grant canonical writeback or bypass ChaseOS Gate.

### 2026-04-28 MCP Proof Artifact Runner Update

**Status:** proof artifact runner implemented; real n8n live proof remains blocked in this workspace.

Implemented now:
- `runtime/adapters/n8n/mcp_live_proof.py`;
- durable redacted proof records under `07_LOGS/Agent-Activity/_n8n_mcp_proofs/`;
- proof CLI with optional `--live-probe` and `--write-proof`;
- local-stub tests proving a live probe can be summarized without logging token values.

Workspace proof result:
- proof artifact created: `07_LOGS/Agent-Activity/_n8n_mcp_proofs/20260427-233637-workspace-blocked-readiness-clean.json`;
- `live_http_call: false`;
- `proof_status: blocked`;
- blockers: deployment disabled, secrets unconfigured, `N8N_BASE_URL` unset, `N8N_MCP_ACCESS_TOKEN` unset.

Truth boundary:
- the proof runner can record readiness and probe evidence;
- it does not configure n8n, create tokens, enable instance-level MCP, expose workflows, or execute workflows;
- real live proof still requires local n8n configuration and token material outside the vault.

---

## Identity

- **Provider / backend:** n8n (open-source workflow automation; self-hosted)
- **Execution surface:** Workflow runtime — HTTP-triggered, scheduled, event-driven execution
- **Adapter class:** Runtime Adapter
- **Trust tier:** Tier 2 ceiling — conditional on deployment review, workflow scope definition, and owner trust assignment
- **Status:** Planned — not yet deployed
- **Registry entry:** `Agent-Registry.md` — n8n — Self-Hosted (Planned)

---

## What n8n Is in ChaseOS

n8n is not a chat interface. It is not a model harness. It is a workflow orchestration layer that can:
- Execute scheduled jobs (daily digest ingestion, weekly review triggers)
- React to external events (webhook, Discord message, price alert, API callback)
- Orchestrate multi-step pipelines involving external APIs, file operations, and model calls
- Integrate with ChaseOS vault content via filesystem node or MCP connector

n8n's role in ChaseOS is the **automation and scheduling layer** — it bridges external events and scheduled operations with the vault and agent layer, but it does not replace the human-initiated agent harness for interactive or exploratory work.

---

## Access Mode

- **Vault access:** Workflow-scoped only — via configured filesystem node or MCP connector
- **Read path:** Filesystem node reading specific vault subfolders as defined in the workflow; or MCP connector with scoped resource access
- **Write path:** Filesystem node or MCP connector — writes only to paths explicitly defined in the workflow definition; no general vault write
- **User-mediated import required:** Depends on workflow — some workflows deposit to `03_INPUTS/` for later human review; others write directly to log folders

---

## What n8n Is Allowed to Do

n8n workflows may, within their defined scope:

- **Read** vault files that the workflow is explicitly authorized to access
- **Write** to output-class targets when the workflow is scoped for direct writeback:
  - `07_LOGS/Build-Logs/` — automated log entries
  - `07_LOGS/Daily/` — session-triggered or scheduled daily notes
  - `07_LOGS/Morning-Thesis/` — pre-filled morning thesis from data feeds
  - `07_LOGS/Agent-Activity/` — n8n activity logs
  - `03_INPUTS/` subfolders — depositing raw ingested content for later triage
- **Call external APIs** that the workflow is explicitly configured to use (with credentials stored as n8n environment variables, not in vault content)
- **Send messages** to configured output channels (Discord, Telegram) when the workflow is explicitly defined to do so and the user has approved the channel integration
- **Trigger model API calls** (Anthropic, OpenAI, or local model) as workflow steps — model outputs are treated as workflow data, not as vault-authoritative content

---

## What n8n Is Never Allowed to Do

Regardless of workflow configuration, n8n must not:

- Access general vault paths not defined in its workflow scope
- Write to protected files (canonical list: `[[06_AGENTS/Permission-Matrix|Permission-Matrix]]` Section 2)
- Delete vault files
- Promote raw input content directly to `02_KNOWLEDGE/` without a human review gate
- Execute actions with external side effects (exchange orders, payment transactions) without explicit per-workflow owner approval and documented approval trail
- Store credentials or secrets in workflow node configurations that are tracked in vault content
- Override or modify ChaseOS governance documents (`Agent-Control-Plane.md`, `Permission-Matrix.md`, `Trust-Tiers.md`, etc.)
- Self-escalate its own permission scope — any change to what n8n can access requires explicit owner action and registry update

---

## Writeback Pattern

n8n workflows that produce vault-relevant output must write to the correct target directly:

| Output type | Target |
|------------|--------|
| Automated build log | `07_LOGS/Build-Logs/YYYY-MM-DD-n8n-[workflow-name].md` |
| Ingested raw content | `03_INPUTS/[Subfolder]/YYYY-MM-DD_[source]-[topic].md` |
| Daily note pre-fill | `07_LOGS/Daily/YYYY-MM-DD.md` |
| Activity log | `07_LOGS/Agent-Activity/YYYY-MM-DD-n8n-[workflow-name].md` |
| Morning thesis pre-fill | `07_LOGS/Morning-Thesis/YYYY-MM-DD-thesis.md` |

Workflows that produce research digests or external content must deposit to `03_INPUTS/` — not directly to `02_KNOWLEDGE/`. Human or harness review is required before knowledge promotion.

---

## Logging Behavior

Every n8n workflow execution that writes to the vault or calls an external API with side effects must produce an activity log:
- File: `07_LOGS/Agent-Activity/YYYY-MM-DD-n8n-[workflow-name].md`
- Minimum content: workflow name, trigger type, execution time, actions taken, targets written, errors (if any)
- Failed executions: must log the failure; must not leave partial writes in vault without flagging

n8n's built-in execution log (in the n8n UI) is supplementary to the vault activity log — the vault log is the authoritative audit trail.

---

## Approval Behavior

### Automatic approvals (no additional approval needed if within workflow scope)
- Scheduled read operations (reading vault files to generate a digest)
- Writing to defined output-class targets (logs, `03_INPUTS/`)
- Sending messages to pre-configured Discord/Telegram channels already approved by owner

### Requires explicit per-workflow owner approval before deployment
- Any workflow that writes to Project-OS files or knowledge notes
- Any workflow that calls financial APIs (exchange data, trading, payment)
- Any workflow that makes irreversible external writes (sends emails, posts public content)
- Any new external service integration (new API endpoint, new webhook, new channel)

### Requires explicit per-action approval (cannot be automated)
- Exchange order submission
- Deletion of any vault file
- Writing to any protected file
- Any action the owner has not explicitly pre-approved in the workflow definition

---

## How Credentials Are Handled

n8n has a built-in credential manager. Use it for all API keys and secrets that n8n workflows require.

**Rules:**
- All API keys and secrets used by n8n workflows must be stored in n8n's credential manager (encrypted at rest in the n8n database)
- Credential values must never appear in workflow node configurations that are exported or tracked
- Credential names may appear in vault content for reference (e.g., "uses `Anthropic-API-Key` credential in n8n") — values must not
- n8n instance credentials (admin password, database password) must be stored separately — not in vault content
- See `[[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]]` for full policy

---

## Failure Behavior

n8n workflows must be designed to fail safely:

- **Partial write guard:** If a workflow writes multiple files and fails mid-way, it must not leave partial state in the vault. Either complete all writes or roll back and log the failure.
- **External call failure:** If an external API call fails, the workflow must log the failure and stop — it must not proceed with downstream vault writes based on incomplete data.
- **Authentication failure:** If vault access fails (filesystem permission, MCP auth), the workflow must stop and alert — not fall back to writing to a different path.
- **Escalation:** Critical workflow failures must surface to the owner — via Discord alert, email, or n8n built-in error workflow.

---

## What Must Be True Before n8n Is Active in ChaseOS

1. n8n deployed on a trusted host (local machine or self-hosted server)
2. n8n credential manager configured with required API keys
3. First workflow written and reviewed against this adapter document
4. Vault access configured (filesystem node or MCP connector) with scoped permissions
5. Activity log workflow confirmed working (first execution produces `07_LOGS/Agent-Activity/` entry)
6. Registry entry in `Agent-Registry.md` updated with `Active` status and defined workflow scope
7. Owner trust assignment confirmed: explicit confirmation that n8n has vault write access for defined targets
8. MCP connection readiness passes with `safe_to_probe: true`
9. First live MCP probe succeeds against `/mcp-server/http` with token values redacted from logs

---

## Relationship to Other ChaseOS Adapters

n8n does not replace the agent harness (CLAUDE.md, OPENAI.md, LOCAL-OSS.md). It handles:
- Scheduled and event-triggered operations
- Pipeline automation (ingest → triage → route)
- Alerting and notification routing

The agent harness handles:
- Interactive, exploratory, and engineering sessions
- Complex reasoning and multi-step planning
- Protected-file operations
- Build sessions

n8n can invoke model APIs as part of workflows (e.g., "call Anthropic API to summarize this digest"), but the resulting output is workflow data — it is deposited to `03_INPUTS/` or a log, not treated as authoritative vault content without review.

---

---

## ChaseOS Gate Conformance

**Current status:** Planned. Manifest defined at `runtime/policy/adapters/n8n.yaml`.

n8n Gate conformance is primarily structural: workflow-scoped filesystem/MCP access means n8n physically cannot reach protected files if configured correctly. The manifest declares the intended scope and the deny list.

When n8n is activated:
- Update `runtime/policy/adapters/n8n.yaml` with deployed workflow scope and `status: active`
- Verify structural access scoping: n8n's filesystem node or MCP connector must only have access to explicitly defined targets
- Verify activity log is generated for every vault-writing or external-API execution
- Pass `05_TEMPLATES/Adapter-Compliance-Checklist.md` Tier 3 (Draft-Capable) at minimum
- Update registry entry status to Active

Gate architecture: `[[06_AGENTS/ChaseOS-Gate|ChaseOS-Gate]]` · Compliance checklist: `[[05_TEMPLATES/Adapter-Compliance-Checklist|Adapter-Compliance-Checklist]]`

---

*Graph links: [[06_AGENTS/Execution-Adapter-Standard|Execution-Adapter-Standard]] · [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] · [[06_AGENTS/Agent-Registry|Agent-Registry]] · [[06_AGENTS/Backends-Supported|Backends-Supported]] · [[06_AGENTS/Permission-Matrix|Permission-Matrix]] · [[06_AGENTS/Trust-Tiers|Trust-Tiers]] · [[06_AGENTS/Agent-Security-Model|Agent-Security-Model]] · [[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]] · [[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]] · [[ROADMAP]] · [[06_AGENTS/ChaseOS-Gate|ChaseOS-Gate]] · [[06_AGENTS/Adapter-Manifest-Standard|Adapter-Manifest-Standard]]*

*N8N.md — Version 1.0 | Created: 2026-03-20 | Phase 5 — Repo / Runtime Binding | Patched: 2026-03-20 (Phase 6 preflight — Gate conformance section added)*
