---
title: ChaseOS Runtime Shell
type: architecture
status: docs-only — Phase 9 runtime shell subset planned; Phase 10 workspace shell is future
version: 1.0
created: 2026-04-08
updated: 2026-04-08
phase: Phase 9 (runtime shell / command surface) / Phase 10 (workspace product shell) — cross-phase family
knowledge_class: canonical-state
---

# ChaseOS Runtime Shell
## ChaseOS — Cross-Phase Product Shell Architecture

> The ChaseOS Runtime Shell is the governed command surface, provider registry, workflow launcher, and workspace scaffolding layer that makes ChaseOS usable as an operator system — from issuing commands to configuring providers to scaffolding a new brain — while preserving all ChaseOS governance constraints.

**Version:** 1.0
**Created:** 2026-04-08
**Status:** Docs-only — Phase 9 runtime shell subset is planned infrastructure; Phase 10 workspace product shell is future design

---

## What the Runtime Shell Is

The Runtime Shell is the product-layer abstraction that turns ChaseOS from a governed internal architecture into something an operator can actually use as a shell.

It answers: *how does an operator invoke, configure, and extend ChaseOS as a system?*

Without the Runtime Shell:
- AOR can execute workflows, but there is no single defined operator entrypoint for launching one
- ChaseOS supports multiple provider backends, but there is no registry of which ones are configured or how to switch them
- The CLI exists for capture; it is not yet a shell in the OS sense
- ChaseOS can scaffold workspaces and source packages, but there is no user-facing brain/workspace scaffold generator
- Config, environment preferences, and model bindings are implicitly set in env vars and code — not managed as a system-level concern

The Runtime Shell closes these gaps. It is the operator command surface and configuration layer that sits above AOR, OSRIL, capture, SIC, and the vault — and below the Phase 10 UI experience.

**What the Runtime Shell is not:**
- Not AOR — AOR is the autonomous execution engine; the shell is the command surface above it
- Not OSRIL — OSRIL routes AOR events back to the operator; the shell routes operator commands down to execution
- Not the GUI — Phase 10 wraps the shell in a human-facing product experience; the shell is the infrastructure layer
- Not a model launcher — the shell resolves which adapter handles a command; the model runs inside the adapter
- Not a replacement for governance — the shell sits above governance, not outside it

---

## Why the Runtime Shell Exists

ChaseOS has been formalized layer by layer:
- Phase 4: security/control plane (trust model, permission matrix)
- Phase 5: execution adapter bindings (CLAUDE.md, N8N.md, etc.)
- Phase 7: Source Intelligence Core
- Phase 8: capture/connector automation
- Phase 9: autonomous operator runtime

Each layer is well-defined. What is missing is the **product shell above them** — the layer that gives an operator a unified command surface, a model/provider registry, and a scaffold generator for their workspace.

Without this layer, ChaseOS remains an excellent internal architecture that requires knowing how each subsystem works to invoke it. With this layer, ChaseOS becomes a real operator OS: you run a command, the shell resolves it, the right adapter handles it, the right model executes it, the results are written back through the standard Gate chain.

This is the distinction between:
- "a collection of well-governed adapters and an AOR engine" (current state)
- "a real operator OS shell above runtimes" (target state)

---

## Phase Split

OSRIL (the Operator Surface + Runtime Interaction Layer) handles the **output-flow side**: how AOR events become visible to the operator. The Runtime Shell handles the **input-flow side**: how the operator's commands route to execution.

| Half | Phase | What It Is |
|------|-------|------------|
| Runtime Shell / Command Surface | Phase 9 | CLI shell commands, provider/model registry, adapter resolution, workflow launcher, config store, brain scaffold CLI entrypoint |
| Workspace / Product Shell | Phase 10 | Human-facing workspace UI, approval center, provenance explorer, settings, onboarding, brain scaffold generator UI |

Phase 9 builds the command infrastructure. Phase 10 wraps it in a navigable product experience. Neither phase collapses into the other.

**Relationship to OSRIL:**

| | Runtime Shell | OSRIL |
|--|---|---|
| Direction | Operator → Runtime (commands in) | Runtime → Operator (events out) |
| Phase 9 concern | Command routing, provider registry, workflow launch | Event bus, dispatch visibility, session model |
| Phase 10 concern | Workspace UI, settings, scaffold generator | Live shell, voice I/O, companion surface |
| Governance posture | Commands validated before execution | Events are read-only outputs; approval responses follow AOR chain |

Both are needed. They are not alternatives.

---

## Phase 9 — Runtime Shell / Command Surface

These features make the AOR and the rest of ChaseOS invocable through a coherent shell interface. They are the operator-input layer.

All Phase 9 Runtime Shell features started as NOT BUILT in the original architecture pass, but live repo truth has now moved further: runtime onboarding (`chaseos agent ...`), the first provider/model inventory surfaces (`chaseos providers list/status`, `chaseos models list`), and the first bounded config surfaces (`chaseos config list/set`) are now partially implemented. The remaining Runtime Shell work is still planned after those footholds, not before them.

### Feature 1: Provider / Model Registry

**What it is:** A machine-readable registry of configured model providers and their bindings — which providers are active, which models are available per provider, which is set as the primary for a given task type.

**Why it exists:** ChaseOS already supports Anthropic, OpenAI, Perplexity, Grok, and local OSS models as adapters. Currently there is no system-level registry that tracks which are configured, what their capability profiles are, or how to switch between them. The provider/model registry makes this explicit and queryable.

**Example operator commands:**
```
chaseos models list
chaseos models set-primary ollama/gemma3:12b
chaseos models set-primary anthropic/claude-sonnet-4-6
chaseos providers list
chaseos providers status
```

**Where it lives:** first implementation now exists at `runtime/providers/registry.py`, reusing `runtime/setup_registry.json`, `runtime/setup_provider_profiles.json`, and setup-state truth; broader persistent registry/config wiring can still evolve toward dedicated runtime-shell storage later.

**Status:** PARTIAL — `chaseos providers list`, `chaseos providers status`, and `chaseos models list` now exist as the first read-only inventory surface (2026-04-26); `set-primary` and richer persistent binding management remain future work.

**Governance:** Provider bindings declare credential sources (env vars only — same discipline as Phase 8 connectors). Switching providers does not change permission ceilings. The registry is a configuration tool — it does not bypass Gate or AOR.

**Summary-context note:** Provider/model state should now also be read through `Settings-Provider-Config-and-Scaffold-Summary-Context-Application.md`, which keeps provider binding summaries, provider readiness summaries, and settings-vs-governance explainers distinct in future ChaseOS setup surfaces.

---

### Feature 2: Shell Command Router

**What it is:** The central dispatch mechanism that routes `chaseos <command>` invocations to the correct subsystem handler. The current Phase 8 CLI uses argparse with explicit subcommands; the Runtime Shell extends this into a coherent shell model with explicit routing rules.

**Why it exists:** The Phase 8 CLI is capture-focused. `chaseos capture`, `chaseos intake`, `chaseos watch`, `chaseos doctor` exist. What is missing is the shell-level routing tier: `chaseos workflow`, `chaseos run`, `chaseos models`, `chaseos scaffold`, `chaseos config`. These require a routing layer that knows which subsystem handles each command family.

**Shell command surface (target):**
```
chaseos workflow today           → triggers operator_today via AOR
chaseos workflow close-day       → triggers operator_close_day via AOR
chaseos run <workflow_id>        → triggers any registered AOR workflow by ID
chaseos models list              → queries provider/model registry
chaseos models set-primary ...   → updates provider binding
chaseos providers status         → health check on all registered providers
chaseos scaffold brain           → launches brain/workspace scaffold generator
chaseos scaffold project <name>  → scaffolds a new project workspace
chaseos config set <key> <val>   → sets operator config values
chaseos config list              → lists current config
chaseos agent list               → lists registered runtimes with lifecycle state
chaseos agent register <p> <s>  → declare and register a new runtime (explicit only)
chaseos agent status <id>        → show lifecycle state, trust ceiling, policy binding
chaseos agent lifecycle <id> <s> → explicit lifecycle transition (Decision Ledger required)
chaseos doctor                   → full system health check (expands Phase 8 partial)
chaseos ingest                   → triggers intake review session
chaseos review                   → triggers quarantine review workflow
```

**Where it lives:** Expands `runtime/cli/main.py` (Phase 8 existing); shell router in `runtime/shell/router.py` (future).

**Status:** PARTIAL — shell-level routing now exists in meaningful first form through `runtime/cli.py` and `chaseos.py` for `runtime`, `gate`, `setup`, `agent`, `agent-bus`, `providers`, `models`, and `config`; dedicated `scaffold` family support and a fuller standalone router module remain future work.

---

### Feature 3: Workflow Launcher

**What it is:** A shell-level entrypoint that invokes registered AOR workflows by name or ID, with optional arguments, and routes them through the full AOR pipeline (Stage 1–8).

**Why it exists:** Phase 9 Pass 1 scaffolded the AOR engine and workflow registry, but the `_handlers` dictionary is empty — no workflow can run yet. Even after Pass 2 adds `operator_today` and `operator_close_day` handlers, there is no `chaseos run <id>` or `chaseos workflow today` entrypoint. The Workflow Launcher is what binds the shell command surface to the AOR execution engine.

**Status:** NOT BUILT — `runtime/aor/engine.py` scaffold exists; CLI entrypoint and handler dispatch are Phase 9 Pass 2+.

**Dependency:** AOR workflow handlers must be implemented (Pass 2) before the Workflow Launcher is meaningful.

---

### Feature 4: Environment / Config Store

**What it is:** A structured per-user configuration store for ChaseOS operator preferences — vault root, default provider, log verbosity, scaffold defaults, capture preferences, model defaults per task type. Separate from the vault structure itself; stored at `.chaseos/config.yaml` or equivalent.

**Why it exists:** ChaseOS currently relies on env vars and hardcoded defaults for many operator preferences. As the command surface expands, these need to be addressable and settable without modifying code or env files.

**Status:** PARTIAL — first implementation now exists at `runtime/config/store.py`, writing bounded non-secret operator preferences to `.chaseos/config.yaml`; `chaseos config list` and `chaseos config set <key> <val>` are live (2026-04-26), while richer validation/mutation surfaces and broader settings UX remain future work.

**Governance:** Config values do not override Gate rules or permission ceilings. They control operator-level preferences (which model to use, log verbosity, scaffold defaults). Protected-file policy is not a config value.

**Summary-context note:** Config-store and preference surfaces should now also be read through `Settings-Provider-Config-and-Scaffold-Summary-Context-Application.md`, which keeps operator config summaries, config validation summaries, runtime-local config posture, and settings-vs-governance boundaries visibly distinct.

---

### Feature 5: Brain / Workspace Scaffold Generator (CLI)

**What it is:** A guided CLI flow that bootstraps a new ChaseOS workspace or brain configuration from scratch. The operator selects an archetype (research workspace, trading operation, engineering project, personal OS), defines their domains and projects, selects preferred providers and models, sets automation comfort level, and ChaseOS scaffolds:
- `01_PROJECTS/[Domain]/[Domain]-OS.md`
- `02_KNOWLEDGE/[Domain]/[Domain].md`
- `07_LOGS/[Domain]/` subfolder
- Role cards appropriate to the selected workflows
- Workflow manifests for selected automation level
- Initial capture watch-folder entries
- Templates pre-configured to the domain

**Why it is a key product differentiator:** Most governed AI systems require deep architectural knowledge to configure. ChaseOS should scaffold itself from a 5-minute guided session. The scaffold generator is what makes ChaseOS usable for a new operator without reading the full documentation.

**CLI entrypoint:**
```
chaseos scaffold brain            → full brain setup wizard
chaseos scaffold project <name>   → scaffold a single project
chaseos scaffold workspace <name> → scaffold a SIC workspace
```

**Status:** PARTIAL — the first bounded scaffold foothold now exists through `runtime/scaffold/generator.py` plus promoted `chaseos scaffold project` and `chaseos scaffold workspace`, which generate draft-only artifacts under `runtime/scaffold/generated/` (2026-04-26); richer `brain` archetype flows, provider/automation selection, and broader generated surface coverage remain future work.

**Summary-context note:** Scaffold flows should now also be read through `Settings-Provider-Config-and-Scaffold-Summary-Context-Application.md`, which keeps scaffold readiness summaries and scaffold plan previews distinct from live applied configuration and from governance authority.

---

### Feature 6: Doctor / Health / Config Commands (Expanded)

**What it is:** Expansion of the existing `chaseos doctor` command (Phase 8) into a full system health interface that covers:
- Provider connectivity (can the configured model be reached?)
- Vault structure integrity (expected folders exist, required files present)
- Gate hook status (are all 4 hooks live and responding?)
- Quarantine queue depth (how many items are awaiting review?)
- AOR status (is the engine running? last workflow run? any failures?)
- Dedup registry health (registry readable? size?)
- Config validity (is the config store parseable? are required values set?)

**Status:** PARTIAL — `chaseos doctor` exists from Phase 8 Pass 2; expanded health surface is planned.

**Summary-context note:** Shell/command/health outputs should now also be read through `Runtime-Shell-and-Command-Surface-Summary-Context-Application.md`, which keeps doctor summaries, runtime-status summaries, command-contract summaries, and command-availability summaries distinct inside future ChaseOS operator surfaces.

---

## Phase 10 — Workspace / Product Shell

These features are the human-facing product experience built on top of the Phase 9 runtime infrastructure. They require the Runtime Shell command surface to be stable before design begins.

All Phase 10 Runtime Shell features are NOT BUILT. They are future design and implementation.

### Feature 7: Workspace Browser

**What it is:** A visual browser for the operator's ChaseOS workspaces — projects, SIC workspaces, active workflows, recent outputs — as first-class navigable entities rather than raw Obsidian file paths.

**Key concept:** Workspaces (SIC workspaces), projects (`01_PROJECTS/`), and capture contexts are presented as coherent first-class objects. The operator can browse, search, and select without opening Obsidian.

**Status:** NOT BUILT — Phase 10.

---

### Feature 8: Approval Center

Canonical cross-feature Approval Center reference: [[ChaseOS-Approval-Center]].

**What it is:** A unified surface for all pending operator approvals — quarantine promotion decisions, AOR approval gates, generated idea graduation proposals, and graph hygiene proposals — presented in one queue rather than scattered across log folders.

**Relationship to OSRIL:** OSRIL's "Approval-Linked Execution Flow" (Phase 9) defines how approvals are emitted by AOR. The Approval Center (Phase 10) is the unified *display surface* for those approval events. They are complementary — the Phase 9 plumbing enables the Phase 10 surface.

**Status:** PARTIAL / NATIVE READ-ONLY PANEL MOUNTED in Studio. Mutation, decision, consumption, and execution flows remain separately governed.

---

### Feature 9: Provenance Explorer

**What it is:** An interactive trace surface — given any vault note or generated output, show the full provenance chain: original capture, quarantine sidecar, SIC workspace processing, Gate promotion decisions, and any AOR workflow involvement.

**Status:** NOT BUILT — Phase 10. Depends on Provenance Schema (Phase 9 second-wave). Standalone bridge/application mapping: `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`

---

### Feature 10: Settings / Brain Config UI

**What it is:** The visual equivalent of the Phase 9 Config Store and Provider/Model Registry. The operator can configure their brain, switch models, set capture defaults, manage watched folders, and review their automation comfort settings — without touching `yaml` files.

**Status:** NOT BUILT — Phase 10.

---

### Feature 11: Onboarding + Scaffold Generator UI

**What it is:** The Phase 10 visual wrapper for the Phase 9 `chaseos scaffold brain` CLI flow. A guided onboarding wizard that walks a new ChaseOS operator through brain setup, domain selection, provider configuration, and automation level — and produces the full scaffold. The CLI version (Feature 5) must exist first; this is the UI layer on top of it.

**Status:** NOT BUILT — Phase 10.

---

### Feature 12: Agent / Runtime Browser

**What it is:** A view of registered agents, their role cards, their current permission ceilings, their Agent Scorecard performance, and their last-run status. The operator can see which runtimes are active, which are performing well, and which have flagged issues.

**Status:** NOT BUILT — Phase 10. Depends on Agent Scorecards (Phase 9 second-wave) and Agent Identity Ledger.

---

## Brain / Workspace Scaffolding — Product Differentiator

The scaffold generator is a top-level product differentiator for ChaseOS. It deserves explicit treatment because it bridges the gap between "a framework you must configure manually" and "a system that gets you running in minutes."

**The scaffold generator flow:**

1. Operator selects archetype (research OS / trading OS / engineering OS / full personal OS)
2. Operator names their active domains (up to the 18 ChaseOS domains)
3. Operator selects their preferred providers and comfort level (local-only / Anthropic / mixed)
4. Operator selects their automation comfort level (manual-only / light automation / full AOR)
5. ChaseOS generates:
   - `01_PROJECTS/` entries with correct OS file structure
   - `02_KNOWLEDGE/` domain index files
   - `07_LOGS/` subfolders matching the operator's selected workflows
   - Role cards appropriate to the automation level
   - Workflow manifests (if automation selected)
   - Capture watched-folder configuration
   - Templates pre-configured to the domain profile

**What the scaffold generator does NOT do:**
- It does not pre-populate knowledge notes — that is the operator's work
- It does not bypass the Gate for any of its writes — all scaffold writes go through normal protected-file rules
- It does not add providers without credential configuration — it only registers provider slots; the operator must supply credentials
- It does not set automation in motion — scaffolded workflows are `status=draft` until the operator enables them

---

## Provider / Adapter Model for the Shell

Provider adapters are how the Runtime Shell resolves which execution backend handles a given command. Each registered provider answers:

| Dimension | Description |
|-----------|-------------|
| **Auth model** | How credentials are supplied (env var, keychain, OAuth — env-var-first per Phase 8 discipline) |
| **Capability profile** | Which task types this provider supports (generation, embeddings, structured output, tool use, streaming) |
| **Write ceiling** | Whether this provider can be used for vault-capable execution or is advisory-only |
| **Permission ceiling** | The maximum trust tier for workflows using this provider |
| **MCP/tool support** | Whether this provider supports the MCP protocol or tool calling |
| **Streaming support** | Whether the provider supports streaming responses |
| **Long-running support** | Whether the provider can handle sessions beyond typical context limits |
| **Cost profile** | Whether the operator has set cost controls for this provider |

**Current registered providers (Execution Adapter Standard — Phase 5):**
- Claude / Anthropic — Tier 2 ceiling; tool use; current primary
- OpenAI — Tier 2 ceiling; planned
- Local / OSS (Ollama) — Tier 2 ceiling; future
- n8n — workflow runtime; Tier 2 ceiling; planned

**Future shell-registered providers:**
- Perplexity — advisory/digest only; Tier 3 ceiling (research bridge, not vault-capable)
- Grok/xAI — advisory/digest only; Tier 3 ceiling (research bridge, not vault-capable)
- Local models via Ollama — Tier 2 ceiling; local-first; no external network required for execution

---

## Safety Model

The Runtime Shell must preserve the ChaseOS safety model in full. Explicitly:

| Rule | How the Shell Enforces It |
|------|--------------------------|
| Vault remains canonical truth | Shell commands that write to the vault go through the Gate; no shell bypass |
| No hidden writeback | All writes are logged in the AOR audit trail or direct session log |
| No promotion bypass | Scaffold generator creates OS file structure; does not promote raw content to `02_KNOWLEDGE/` without Gate |
| Provider / surface / adapter distinctions preserved | Provider registry is separate from trust ceilings; switching providers does not change permission scope |
| No broad unsafe agent privileges | Shell commands route to AOR with declared permissions; shell cannot grant ambient vault access |
| No mutation of canonical state without policy | Shell config writes to `.chaseos/` (operator config); not to `00_HOME/` or `06_AGENTS/` |
| Local-first identity intact | Provider adapters are pluggable; shell does not push workspace data to external providers |
| Shell sits above governance, not outside it | Every command that touches the vault or an external system passes through AOR → Gate → permission ceiling |

---

## Relationship to Other ChaseOS Components

| Component | Relationship |
|-----------|-------------|
| **Autonomous Operator Runtime (AOR)** | AOR is the execution engine; the Runtime Shell is the command surface above it. Shell commands that run workflows invoke AOR; AOR enforces permission ceilings and Gate rules. The shell does not bypass AOR. |
| **OSRIL (Operator Surface + Runtime Interaction Layer)** | OSRIL routes AOR events to the operator (output-flow). The Runtime Shell routes operator commands to execution (input-flow). They are orthogonal and complementary; both are needed. |
| **Execution Adapter Standard** | Provider/Adapter Model for the shell builds on the Execution Adapter Standard (`06_AGENTS/Execution-Adapter-Standard.md`). Shell provider registration extends the adapter concept to include capability profiles and shell-level metadata. |
| **ChaseOS Gate** | All write commands issued through the shell go through Gate. The shell cannot initiate protected-file writes, cross-repo edits, or canonical promotions without the Gate approval chain. |
| **Phase 8 CLI** | The Phase 8 `chaseos` CLI is the first layer of the Runtime Shell. Phase 9 expands it from a capture-focused CLI into a shell-level command surface. The Phase 8 CLI does not need to be replaced — it needs to be routed into the shell architecture. |
| **SIC Architecture** | The scaffold generator creates SIC workspace scaffolding. SIC workspaces created by the scaffold generator are empty shells — the operator populates them through the standard capture → promote → SIC ingest flow. |
| **Phase 10 Interface / Experience Layer** | The Phase 10 Workspace Product Shell is the visual experience layer above the Phase 9 Runtime Shell. The shell provides the command infrastructure; Phase 10 provides the navigable workspace UI. |

---

## What Is Not In Scope for the Runtime Shell

- **Full GUI application** — that is Phase 10 Workspace Product Shell, not the Runtime Shell
- **Event visibility and session state** — that is OSRIL; not the Runtime Shell's concern
- **AOR execution engine** — AOR executes; the shell invokes
- **Replacing vault markdown with a database** — vault remains the source of truth; `.chaseos/` config files are operator configuration only
- **Autonomous knowledge promotion** — the shell can trigger workflows; it cannot autonomously promote content to `02_KNOWLEDGE/`
- **Bypassing Gate for scaffold writes** — scaffold generator follows Gate rules like any other write surface

---

## Current Status and Next Steps

**Phase 9 Runtime Shell (runtime/command side):**

All features are currently NOT BUILT. Recommended sequencing:

1. Build `operator_today` + `operator_close_day` handlers (Phase 9 Pass 2 — current next target)
2. Add `chaseos run <workflow_id>` and `chaseos workflow today` shell commands (Workflow Launcher — Pass 2 parallel or Pass 3)
3. Formalize Provider/Model Registry schema (`.chaseos/providers.json`) — can be done in parallel with Pass 2
4. Extend `chaseos doctor` into full system health surface — Pass 3
5. Implement Environment/Config Store (`.chaseos/config.yaml`) — Pass 3 or Pass 4
6. Implement Brain/Workspace Scaffold Generator CLI — Phase 9 later pass (depends on AOR handlers being operational)

**Phase 10 Workspace Product Shell:**

All Phase 10 features wait behind Phase 9 Runtime Shell being operational. No Phase 10 surface work begins until:
- `chaseos run`, `chaseos workflow`, `chaseos models`, `chaseos config` shell commands are stable
- AOR is running at least two live workflows
- Audit trail is operational

---

*Graph links: [[Vault-Map]] · [[Autonomous-Operator-Runtime]] · [[Operator-Surface-Runtime-Interaction]] · [[Execution-Adapter-Standard]] · [[Feature-Fit-Register]] · [[ROADMAP]] · [[ChaseOS-Gate]] · [[Permission-Matrix]] · [[SIC-Architecture]] · [[Phase9-Adopted-Feature-Specification]] · [[Provenance-Explorer-and-Chronology-Browser-Standalone-Application]] · [[Runtime-Shell-and-Command-Surface-Summary-Context-Application]] · [[Settings-Provider-Config-and-Scaffold-Summary-Context-Application]]*

*ChaseOS-Runtime-Shell.md — v1.0 | Created: 2026-04-08 | New canonical doc for the Runtime Shell / Product Shell cross-phase family; Phase 9 command surface + Phase 10 workspace product shell; orthogonal to OSRIL (event visibility layer); extends Phase 8 CLI into shell-level architecture*
