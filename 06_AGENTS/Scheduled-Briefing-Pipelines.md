# Scheduled-Briefing-Pipelines.md
## ChaseOS — Scheduled Briefing Pipelines Feature Architecture

> Scheduled Briefing Pipelines are a reusable ChaseOS framework feature for producing structured, scheduled, guardrailed briefings from governed data sources. They are not a one-off StrikeZone feature. They are a composable pipeline pattern that runs on top of ChaseOS execution infrastructure and routes all outputs through the standard vault governance model.

**Version:** 1.4
**Created:** 2026-03-23
**Current repo-truth override (2026-04-29):** Phase 9 SBP substrate is beyond the original Pass 1B status line below. Later Acquisition/SBP passes added latest-pointer consumption, local/import research preview, reviewed preview promotion, read-only SBP verification, and research readiness status. Final reviewed research-pack proof still requires real local source files.
**Status:** Pass 1B COMPLETE (2026-04-23) — StrikeZone digest wired to consume `briefing_ready_input_set` from `runtime/acquisition/`; `AcquisitionPackInputAdapter` generic substrate live; optional graceful degradation when pack absent; 78 Pass 1B tests pass

---

## Implementation Reality (as of Pass 1B)

**Pass 1B wired the StrikeZone SBP instance to consume `briefing_ready_input_set` artifacts from `runtime/acquisition/`. The first SBP → Acquisition bridge is live.**

The SBP substrate (`runtime/sbp/`) is now live with Pass 1B additions:
- `SBPConfig` manifest contract (`manifest.py`) — validates the `sbp_config` block; now includes `acquisition-pack` adapter type, `pack_path`, and `optional` fields
- `SBPGuardrailProfile` enforcement (`guardrail.py`) — write scope enforcement, forbidden ceiling check, audit requirement
- `InputAdapter` ABC + `VaultNotesInputAdapter` + `AcquisitionPackInputAdapter` (`input_adapters.py`) — vault notes (tier 1); acquisition packs (tier 2, reads BRIS + source packets, exposes trust/freshness/blocked_actions metadata); stubs for SIC workspace, external API, agent activity, raw digest
- `DeliveryAdapter` ABC + `VaultLocalDeliveryAdapter` + `DiscordDeliveryAdapter` (`delivery_adapters.py`) — vault-local and Discord concrete; email/Whop/Slack are stubs; embed title is generic (pipeline_id-based, not StrikeZone-specific)
- `SBPBaseHandler` ABC (`base_handler.py`) — instance handlers extend this, implement `generate_content()`, get orchestration for free
- `run_sbp_pipeline()` generic stub runner (`runner.py`) — AOR Stage 6 fallback for any `task_type: scheduled-briefing` workflow without a specific instance handler
- `_sbp_base_template.yaml` (`runtime/workflows/registry/`) — template for instance pipeline manifests
- `scheduled-briefing` role card (`06_AGENTS/role-cards/`) — permission envelope for all SBP pipelines

**What is still not built:**
- Acquisition scheduling before SBP (acquisition at ~0550 ET to produce pack before 0600 ET SBP fire)
- Static `pack_path` in manifest needs to compute from run date or reference a "latest" pointer
- Provenance/trust/freshness scoring over live digest/browser/research inputs (live source acquisition)
- SIC workspace input adapter implementation
- Whop/email concrete delivery adapter implementations
- `07_LOGS/SBP-Runs/` directory (created on first actual pipeline run)

**Current consumer wiring state (2026-04-23):** StrikeZone manifest declares both `vault-notes` (tier 1) and `acquisition-pack` (tier 2, optional) adapters. Pack path points to the Pass 1A fixture. When the acquisition scheduling is wired, the pack path will be updated to a run-date-computed path.

**Next SBP-adjacent pass:** Phase 10A0 should wrap existing acquisition readiness, preview, reviewed promotion, and read-only SBP verification commands in a local operator cockpit so the reviewed research-pack workflow can be tested with real local files.

**2026-04-29 live-test note:** the old "wire acquisition scheduling before SBP" gap is stale by current repo truth. The current bottleneck for the StrikeZone acquisition/SBP lane is operator UX around real local research files. `research-status`, `preview-research`, `promote-research-preview`, and `verify-research-sbp` exist; Phase 10A0 should wrap these in a local-only cockpit. Fixture tests prove plumbing, but final reviewed research-pack verification requires real operator-supplied Perplexity, YouTube, research export, and optional Grok files.

---

## What Problem Scheduled Briefing Pipelines Solve

ChaseOS currently produces knowledge and outputs only when a human explicitly runs a session. Every briefing, digest, or structured output requires a person to open a session, load context, run a prompt, and write back the result.

This works during development. It does not work as an operating system.

Three specific problems this does not solve:

**Problem 1 — Morning briefings require a person to be at the keyboard before the briefing is useful.**
A trader needs the morning digest before market open. If generating it requires a session, the value arrives after the context is needed, or requires rushing the start of the day to produce it. The briefing is only useful if it is already there when the person sits down.

**Problem 2 — Recurring outputs are rediscovered, not remembered.**
Every morning thesis, weekly review, and knowledge digest starts from scratch. The structure, sources, and format are re-specified. ChaseOS has the framework and the source material, but without scheduled pipelines, there is no way to encode "this is how we produce this output, on this schedule, from these sources, and deliver it here."

**Problem 3 — SIC produces workspace outputs that have no path to structured, recurring delivery.**
Once the Source Intelligence Core can produce a workspace summary or briefing, there is no system to trigger that query on a schedule, format the result, write it to the vault, and deliver it to a consumer. Without Scheduled Briefing Pipelines, SIC outputs are still pull-only — you have to ask for them. SBP makes SIC outputs push-capable.

**What Scheduled Briefing Pipelines provide:**
- A structured, reusable way to encode recurring output workflows into the system
- A governed path from source material to structured output to vault writeback to external delivery
- The ability to run a known workflow reliably without reinventing it each time
- Auditability — every pipeline run is logged, every output is attributed, every delivery is declared
- Composability — the same pipeline pattern works for trading briefings, research digests, project updates, or content performance reviews; the schema is the same

This is not automation for automation's sake. It is the operating system remembering how to do something it has already been taught to do.

---

## What Scheduled Briefing Pipelines Are

A Scheduled Briefing Pipeline is a defined, repeatable workflow that:

1. **Runs on a trigger schedule** (cron, event-based, or user-initiated)
2. **Pulls from governed input sources** via defined input adapters
3. **Executes through an approved ChaseOS execution adapter** (Claude, OpenAI, local model)
4. **Generates a structured briefing output**
5. **Writes the output back to the vault** through standard Gate and taxonomy rules
6. **Delivers the briefing to one or more endpoints** via delivery adapters (Discord, email, dashboard, etc.)
7. **Operates within a defined guardrail profile** — no pipeline runs outside its declared scope

This is a framework-level concept. A single ChaseOS instance can run multiple briefing pipelines across different domains (trading, research, operations, content). Each pipeline is independently configured, independently governed, and independently audited.

---

## Why This Is a Framework Feature, Not a One-Off

The Scheduled Briefing Pipeline pattern emerged from StrikeZone's need to deliver a daily market digest. But the underlying architecture is reusable:

- A trading operation needs a morning briefing from market data
- A research workflow needs a weekly synthesis of recent sources
- A content engine needs a weekly performance digest
- A project operations workflow needs a daily open-loop review

All of these share the same structural requirements: trigger, inputs, execution, output, writeback, delivery, and guardrails. ChaseOS defines the pattern once and instantiates it per use case.

**Relationship to SIC:**
Scheduled Briefing Pipelines can use SIC workspace queries as an input source. A briefing pipeline might query a SIC workspace for recent source summaries, then format them into a structured briefing. SIC is an optional input layer — not a requirement. Pipelines that do not need retrieval-backed reasoning can run with simpler input adapters.

**Relationship to Autonomous Operator Runtime:**
Scheduled Briefing Pipelines run on top of the Autonomous Operator Runtime infrastructure. The AOR provides: scheduling, execution adapter selection, bounded autonomy, multi-repo policy, audit trails, and failure handling. A briefing pipeline is one type of workflow that the AOR executes.

---

## Pipeline Architecture: Six Components

Every Scheduled Briefing Pipeline is defined by six components. These components form the pipeline's schema — its formal declaration.

### 1. Trigger Schedule

**What it is:** When and how the pipeline runs.

**Options:**
- Cron schedule (daily at 0600, weekly on Sunday at 1800, etc.)
- Event-based trigger (price alert fires, new source added to workspace, calendar hook)
- User-initiated (manual run with standard guardrails still applied)

**Schema fields:**
- `trigger_type`: `cron | event | manual`
- `cron_expression`: if trigger_type is cron
- `event_source`: if trigger_type is event (e.g., `price_alert`, `workspace_update`)
- `max_runs_per_day`: rate limit to prevent runaway execution

---

### 2. Input Adapters

**What it is:** What sources feed the pipeline.

**Adapter types:**
- **SIC workspace query** — retrieve summaries or evidence from a named SIC workspace
- **Vault notes** — read specific `02_KNOWLEDGE/` notes or project OS files as structured input
- **External API** — market data feed, news API, structured data source (requires explicit permission and credential handling per `Credential-Boundaries-SOP.md`)
- **Raw digest input** — content from `03_INPUTS/Digests/` that is already past the triage stage
- **Agent-Activity log** — summarize recent agent actions for an operations briefing

**Governance rule:** Every input adapter declares its trust tier. External API inputs are Tier 3–4 by default. SIC workspace outputs are Tier 3 until promoted. Vault canonical state is Tier 1–2.

---

### 3. Execution Adapter

**What it is:** Which ChaseOS-registered runtime executes the pipeline logic.

**Approved adapters:**
- Claude / Anthropic lane — primary, current
- OpenAI Agent Harness — planned
- Local model harness — future
- n8n Workflow Runtime — future; preferred for pure orchestration without model generation

**Rules:**
- Execution adapter must be registered in `06_AGENTS/Agent-Registry.md`
- Adapter trust ceiling applies during execution — no privilege escalation inside a pipeline
- Pipeline execution must conform to the adapter's manifested permission scope

---

### 4. Writeback Targets

**What it is:** Where the pipeline's outputs are written inside ChaseOS.

**Options:**
- `07_LOGS/Morning-Thesis/YYYY-MM-DD.md` — daily briefing archive
- `07_LOGS/Build-Logs/YYYY-MM-DD-[Pipeline]-run.md` — pipeline run log
- `01_PROJECTS/[Project]/[briefing-output].md` — project-specific briefing
- `02_KNOWLEDGE/[Domain]/[briefing-output].md` — promoted knowledge (requires Gate approval)

**Governance rule:** All writeback goes through the standard ChaseOS Gate. Automated pipelines may write to log folders without additional approval. Writing to `02_KNOWLEDGE/` requires promotion gate — a pipeline cannot auto-promote knowledge.

---

### 5. Delivery Adapters

**What it is:** How the briefing reaches its end consumers (if it has external delivery).

**Adapter types:**
- Discord webhook — formatted message to a server channel (e.g., StrikeZone signals)
- Email — structured digest to a mailing list
- Whop dashboard — formatted update to a community platform
- Slack webhook — team notification
- Internal only (no external delivery — vault writeback is the output)

**Governance rule:** Delivery adapters are external-facing. They must be explicitly declared in the pipeline schema and registered in the system. No pipeline may send to an external endpoint not declared in its manifest. Credential handling for delivery adapters follows `Credential-Boundaries-SOP.md`.

---

### 6. Guardrail Profile

**What it is:** The behavioral boundaries and failure policy for this pipeline run.

**Elements:**
- `permission_ceiling`: which trust tier this pipeline operates at (Tier 2 or Tier 3 max)
- `write_scope`: explicit list of writable directories/files
- `read_scope`: explicit list of readable sources
- `max_token_budget`: execution size limit
- `human_in_loop`: `required | optional | none` — whether a human must review before delivery
- `fail_behavior`: `halt_and_log | retry_once | notify_user`
- `audit_required`: `true | false`

All pipelines default to fail-closed. If the guardrail profile is not declared, the pipeline does not run.

---

## First Named Instance: StrikeZone Market Digest Publisher

**Status:** Pass 1B COMPLETE (2026-04-23) — StrikeZone digest consumes `briefing_ready_input_set` from `runtime/acquisition/` via `AcquisitionPackInputAdapter`; trust/freshness/blocked-actions metadata surfaced in digest output; optional graceful degradation when pack absent; acquisition scheduling before SBP remains the next gap.

> **Note:** Pass 1A built the generic SBP substrate that all instance pipelines run on.
> The StrikeZone Market Digest Publisher is the first named instance pipeline on top of that substrate.
> Repo inspection on 2026-04-23 found its manifest, handler, test, and schedule intent files present and active.
> The missing layer is now live consumption of acquisition-normalized source packs, not generic SBP substrate creation.

**Purpose:** Daily morning market briefing for StrikeZone Crypto community members. Structured overnight digest → formatted signal output → StrikeZone Discord and Whop delivery.

**Pipeline schema (declared):**

| Component | Configuration |
|-----------|---------------|
| Trigger | Cron: daily at 0600 ET (during NY pre-market) |
| Input adapters | SIC workspace query (TradingMarkets workspace), vault morning thesis template, optional external market data feed |
| Execution adapter | Claude / Anthropic lane |
| Writeback targets | `07_LOGS/Morning-Thesis/YYYY-MM-DD.md`, `01_PROJECTS/StrikeZone/digest-log.md` |
| Delivery adapters | Discord webhook (StrikeZone server), Whop dashboard update |
| Guardrail profile | Tier 2 ceiling; write scope: `07_LOGS/Morning-Thesis/`, `01_PROJECTS/StrikeZone/`; human-in-loop: optional for delivery; fail behavior: halt and notify |

**What it is not:** This pipeline is not a direct market signal automation system. It is a briefing digest system — it summarizes and formats structured context into a readable briefing. All market decisions remain with the user.

---

## Governance Rules for All Pipelines

1. **Every pipeline has a declared manifest.** No pipeline runs without a schema file.
2. **All writeback goes through Gate.** No automated promotion to `02_KNOWLEDGE/` without explicit promotion gate.
3. **All external delivery is explicitly declared.** No surprise outbound calls to webhooks or APIs.
4. **Execution history is logged.** Every pipeline run produces a log entry in `07_LOGS/`.
5. **Failures halt and log.** Failed pipelines do not retry silently or continue partially.
6. **Credentials are never in pipeline schemas.** External API keys and webhook URLs use `Credential-Boundaries-SOP.md` handling.
7. **Inputs are trust-typed.** Input adapter outputs are assigned a trust tier before they enter pipeline reasoning.
8. **Human review is supported.** Pipelines can declare `human_in_loop: required` for delivery approval.

---

## Relationship to Other ChaseOS Components

| Component | Relationship |
|-----------|-------------|
| **Autonomous Operator Runtime** | AOR is the infrastructure. Pipelines are workflows that AOR executes. |
| **Source Intelligence Core** | SIC can be an input adapter. Pipelines may query SIC workspaces. |
| **ChaseOS Gate** | All writeback from pipelines goes through Gate. Gate rules are not bypassed by automation. |
| **Knowledge Taxonomy** | All pipeline outputs that enter `02_KNOWLEDGE/` must declare a knowledge class. |
| **Multi-Repo Policy** | Pipelines declare repo scope and cross-repo access in their manifest. |
| **Agent Memory Architecture** | Pipeline execution history populates Layer E (Audit Memory) and feeds the Agent Identity Ledger. |

---

## Future Pipeline Instantiations

These are planned but not yet designed:

| Domain | Potential Pipeline |
|--------|-------------------|
| Research | Weekly synthesis digest from active SIC workspaces → `02_KNOWLEDGE/` draft |
| University | Weekly lecture digest → study note draft → review queue |
| GeoMacro | Bi-weekly macro intelligence briefing → `01_PROJECTS/GeoMacro/` |
| ChaseOS | Weekly system health sweep → `00_HOME/Dashboard.md` update |
| Content Engine | Weekly content performance digest → `01_PROJECTS/ContentEngine/` |

---

*Graph links: [[Vault-Map]] · [[Autonomous-Operator-Runtime]] · [[SIC-Architecture]] · [[Agent-Memory-Architecture]] · [[ChaseOS-Gate]] · [[Feature-Register]] · [[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]]*

*Scheduled-Briefing-Pipelines.md — v1.3 | Created: 2026-03-23 | Updated: 2026-03-23 (Truth-sync pass — "What Problem SBP Solves" section added with three concrete problems; SIC → SBP relationship clarified as push-enabling layer) | Updated: 2026-04-22 (Pass 1A complete — Implementation Reality section added; generic substrate built in runtime/sbp/; First Named Instance section corrected — StrikeZone remains the first planned instance but this pass built the substrate first; status updated to Pass 1A COMPLETE) | Updated: 2026-04-23 (repo-observed StrikeZone instance files active; Acquisition + Normalization Pass 1A source-pack substrate active; live SBP consumer wiring remains the gap)*
