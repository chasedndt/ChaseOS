---
title: Phase 9 Adopted Feature Specification
version: 1.3
date: 2026-03-31
updated: 2026-04-20 (Pass 2 verification and reconciliation)
status: ACTIVE — Phase 9 Pass 4 COMPLETE 2026-04-09; Features 7–10 (operator_today, operator_close_day, graph_hygiene, graduate_ideas) BUILT in bounded form; graph_hygiene + graduate_ideas are proposal-only; native ChaseOS schedule intent (`runtime/schedules/`) BUILT and validated; Operator Briefing V2 live for `operator_today` and `operator_close_day`; OpenClaw remains the active scheduled execution lane; Hermes shadow activation proven and limited to draft/audit outputs only
type: specification
---

# Phase 9 Adopted Feature Specification

> Canonical specification for all features adopted into Phase 9 (Operator Runtime / AOR).
> Each feature is fully specified across 17 sub-sections covering purpose, placement, governance, implementation direction, and success criteria.
> This document is authoritative. ROADMAP.md summarizes it. PROJECT_FOUNDATION.md references it.

---

## Overview

Phase 9 delivers two infrastructure families plus an adopted feature set that was identified during Phase 8 as architecturally necessary for AOR to function correctly.

**Infrastructure families already documented:**
- Autonomous Operator Runtime (AOR) â€” `06_AGENTS/Autonomous-Operator-Runtime.md`
- Scheduled Briefing Pipelines (SBP) â€” `06_AGENTS/Scheduled-Briefing-Pipelines.md`

**Adopted features â€” this document:**
- 10 first-wave foundation features (required to make AOR operational)
- 6 second-wave features (dependent on first-wave; added once foundation is stable)
- 1 later orchestration-surface candidate (Paperclip â€” reserved; not Phase 9 scope)

**Feature waves:**
| Wave | Count | Description |
|------|-------|-------------|
| First-wave (foundation) | 10 | Required before AOR can run governed workflows |
| Second-wave (dependent) | 6 | Extend AOR capability once foundation is stable |
| Later candidate | 1 | Paperclip â€” orchestration surface above ChaseOS |

---

## First-Wave Features (Foundation)

Features 1â€“10 must be built before AOR workflows are treated as production-ready.

---

### Feature 1: Workflow Registry

**Feature Name:** Workflow Registry

**Feature Class:** AOR Infrastructure / Governance

**Primary Phase Placement:** Phase 9 â€” first-wave

**What It Is:**
The Workflow Registry is the canonical manifest store for all AOR workflows. It is a structured register â€” a collection of workflow definition files â€” that declares every workflow ChaseOS is permitted to execute autonomously. No workflow runs unless it is declared in the registry. A registry entry is a machine-readable specification: workflow identity, purpose, trigger type, owner, required inputs, expected outputs, runtime class, approval rule, writeback target, and rollback path. The registry is the source of truth for what AOR is authorized to do.

**Problem It Solves:**
Without a registry, AOR workflows accumulate ad hoc â€” run by convention, undocumented, with no canonical list of what is authorized. This creates an operational blind spot: neither the operator nor the governance layer can enumerate what the system is doing autonomously. It also prevents policy enforcement, because there is nothing to enforce policy against.

**Why It Is Being Added Now:**
AOR is the Phase 9 infrastructure goal. The registry is the prerequisite that makes AOR legible to governance. Before any workflow is scheduled, triggered, or run autonomously, there must be a canonical, auditable list of what is authorized. The registry makes that list formal and checkable.

**Where It Sits in ChaseOS:**
`runtime/workflows/registry/` â€” one `.yaml` or `.md` file per registered workflow. The registry directory is treated as a policy resource: readable by AOR at runtime, auditable by the operator, governed by the Gate like any other canonical write.

**What It Coordinates With:**
- AOR scheduler (reads registry to determine what to run)
- Task-Type Router (uses workflow type field to route execution)
- Agent Role Cards (references which role card governs a workflow run)
- Operator audit log (records registry lookups and workflow outcomes)
- ChaseOS Gate (governs writes to registry files)
- Permission Matrix (registry entries must stay within declared permission ceilings)

**What It Improves:**
- Replaces ad hoc workflow invocations with declared, governed execution
- Makes autonomous behavior enumerable and auditable
- Provides the schema foundation for SBP pipeline definitions
- Enables rollback path specification before a workflow ever runs

**Operational Inputs:**
- Workflow manifest file (YAML or structured Markdown): identity fields, trigger spec, permission ceiling, writeback targets, failure behavior
- AOR runtime request (trigger event or schedule tick) referencing a workflow ID

**Operational Outputs:**
- Resolved workflow execution plan (inputs, permissions, adapter selection, writeback targets, rollback path)
- Registry lookup log entry (workflow ID, trigger timestamp, resolution result)

**Governance/Security Constraints:**
- Registry files are governed canonical writes â€” Gate rules apply to all additions and changes
- No workflow runs unless it appears in the registry
- Permission ceilings in registry entries are hard limits â€” AOR cannot escalate beyond them at runtime
- Registry is not user-editable during a running workflow (write lock during execution)
- All registry entries must declare a failure behavior (abort/notify/retry/rollback)
- Rollback paths must be non-destructive â€” rollback cannot delete canonical vault content

**Implementation Direction:**
1. Define workflow manifest schema (YAML): `workflow_id`, `name`, `purpose`, `trigger_type`, `owner`, `inputs`, `outputs`, `runtime_class`, `approval_rule`, `writeback_targets`, `permission_ceiling`, `failure_behavior`, `rollback_path`
2. Create `runtime/workflows/registry/` directory as registry home
3. Implement registry loader in `runtime/aor/registry.py`: list, load, validate, resolve
4. Wire AOR scheduler to consult registry before execution
5. Add registry audit logging to `runtime/audit/`

**Dependencies:**
- AOR scheduler (Phase 9 core)
- Permission Matrix (Phase 4 â€” already live)
- ChaseOS Gate (Phase 5 â€” already live)
- Audit log infrastructure (Phase 9 â€” co-developed with AOR)

**Not In Scope:**
- Dynamic workflow generation at runtime (workflows are declared before execution, not generated on the fly)
- Workflow versioning or migration system (Phase 10 concern)
- UI for browsing the registry (Phase 10)
- Cross-vault registry synchronization (out of scope entirely)

**Success Criteria:**
- At least one workflow is declared in the registry in canonical manifest format
- AOR refuses to execute any workflow not in the registry
- Registry lookups are logged with outcome
- Permission ceiling in the registry entry is enforced at runtime â€” AOR cannot exceed it

**Status:** BUILT for first-wave workflows — registry loader and manifest validation are live; first-wave manifests are active where implemented; AOR refuses to run any workflow not in the registry (sentinel enforced); broader manifest management remains iterative.

---

### Feature 2: Agent Role Cards

**Feature Name:** Agent Role Cards

**Feature Class:** AOR Governance / Agent Identity

**Primary Phase Placement:** Phase 9 â€” first-wave

**What It Is:**
Agent Role Cards are bounded runtime-role definitions. Each card specifies a named operational role â€” not a persona, not an identity â€” and declares exactly what that role is permitted to do within ChaseOS. A Role Card contains: allowed actions, forbidden actions, required reads (what context the agent must load before operating), write scope (where outputs are permitted to land), and escalation rules (when to pause and surface a decision to the operator). Role Cards are consumed by AOR at workflow execution time to configure a runtime's operating boundary for that run.

**Problem It Solves:**
Without Role Cards, agent behavior within a workflow is governed only by the general Permission Matrix and session-level discretion. This creates ambiguity at execution time: what is this runtime allowed to do in this specific role? Are there reads it must perform? Where can it write? What triggers escalation? Role Cards make these answers runtime-legible and auditable, not just documented in markdown.

**Why It Is Being Added Now:**
AOR needs to configure bounded agent execution programmatically. The moment AOR runs a workflow autonomously, the system must be able to declare the operating boundary for that run without relying on session context or operator discretion. Role Cards provide that declaration in a machine-readable, reusable form. They are the per-workflow behavioral envelope.

**Where It Sits in ChaseOS:**
`06_AGENTS/role-cards/` â€” one file per defined role. Role Cards are referenced by workflow registry entries (a workflow declares which role card governs its execution). The Gate governs writes to role card files.

**What It Coordinates With:**
- Workflow Registry (workflow entries reference a role card ID)
- AOR execution engine (reads role card at workflow start to configure the runtime)
- Permission Matrix (role cards must stay within permission ceilings defined there)
- Agent Identity Ledger (role card compliance is tracked in ledger entries)
- Agent Scorecards (second-wave â€” scorecard tracks how well a runtime respects its role card)

**What It Improves:**
- Makes agent operating boundaries explicit, reusable, and auditable
- Prevents privilege creep between workflow executions (each run starts from a declared boundary)
- Provides the input structure Agent Scorecards need to evaluate compliance
- Reduces ambiguity at operator review time (reviewers can see declared vs actual behavior)

**Operational Inputs:**
- Role Card file (YAML or Markdown): `role_id`, `name`, `allowed_actions`, `forbidden_actions`, `required_reads`, `write_scope`, `escalation_rules`
- Workflow execution request referencing a `role_id`

**Operational Outputs:**
- Resolved execution boundary object (passed to AOR runtime at workflow start)
- Role card compliance record (written to audit log after execution)

**Governance/Security Constraints:**
- Role Cards are canonical governance files â€” Gate rules apply to all creation and edits
- Role Cards cannot grant permissions that exceed the Permission Matrix ceiling
- `forbidden_actions` entries are enforced, not advisory â€” violations trigger escalation
- Role Cards do not define identity or persona â€” they define a bounded operational scope
- Role Card file changes require explicit user instruction (same class as Permission Matrix edits)
- Escalation rules must include at minimum: "unknown state" and "write to canonical without prior explicit instruction"

**Implementation Direction:**
1. Define role card schema: `role_id`, `name`, `description`, `allowed_actions[]`, `forbidden_actions[]`, `required_reads[]`, `write_scope`, `escalation_rules[]`, `version`, `owner`
2. Create `06_AGENTS/role-cards/` directory
3. Write at least two role cards: `operator-briefing` (for operator_today/operator_close_day) and `vault-maintenance` (for graph_hygiene)
4. Implement role card loader in `runtime/aor/role_cards.py`
5. Wire role card loader into AOR workflow initialization sequence

**Dependencies:**
- Workflow Registry (Feature 1 â€” role cards referenced from registry entries)
- Permission Matrix (Phase 4 â€” already live)
- ChaseOS Gate (Phase 5 â€” already live)
- AOR execution engine (Phase 9 core)

**Not In Scope:**
- Persona definitions or identity profiles (those belong to Agent Identity Ledger and `SOUL.md`)
- Dynamic role generation at runtime
- Role escalation without explicit operator grant
- Cross-system role portability

**Success Criteria:**
- At least two role cards defined in canonical format
- AOR workflow execution loads the declared role card before running
- Forbidden actions trigger escalation rather than silent bypass
- Role card compliance is logged per execution

**Status:** PARTIAL â€” Pass 1 (2026-03-31): `06_AGENTS/role-cards/operator-briefing.yaml` + `vault-maintenance.yaml` live with full schema; `runtime/aor/role_cards.py` loader functional; forbidden_write_zones enforced in pipeline Stage 4; additional role cards are Pass 2+

---

### Feature 3: Task-Type Router

**Feature Name:** Task-Type Router

**Feature Class:** AOR Infrastructure / Governance

**Primary Phase Placement:** Phase 9 â€” first-wave

**What It Is:**
The Task-Type Router is a canonical task classification system that maps task types to execution parameters. For each recognized task type, the router defines: required context reads before execution, runtime class to use, permission set that applies, and writeback expectations after completion. The router ensures that any task arriving at AOR â€” whether triggered by schedule, event, or operator instruction â€” is classified into a known type before execution begins. Classification is required; unclassified tasks are escalated, not run.

**Problem It Solves:**
Different tasks require different operating contexts. A briefing workflow needs different reads, different permissions, and different writeback targets than a vault maintenance workflow. Without a router, AOR must either run all tasks with maximum permissions (unsafe) or defer classification to per-workflow logic (redundant, inconsistent). The router provides a single, canonical classification layer that all workflows consult.

**Why It Is Being Added Now:**
The Task-Type Router is infrastructure that AOR workflows depend on. It is co-developed with the Workflow Registry and Role Cards as part of the first-wave foundation. Without it, individual workflows must encode classification logic internally â€” that leads to drift and inconsistency across the workflow library as it grows.

**Where It Sits in ChaseOS:**
`runtime/aor/task_router.py` â€” the router module. A companion routing table (`runtime/aor/task_type_table.yaml` or equivalent) defines the classification map. AOR consults the router as part of workflow initialization, after registry lookup and before role card resolution.

**What It Coordinates With:**
- Workflow Registry (router classification informs which registry entry to use)
- Agent Role Cards (task type â†’ role card selection)
- AOR execution engine (router output configures the execution context)
- Operator audit log (task type logged as part of every execution record)

**What It Improves:**
- Makes task classification explicit and auditable rather than implicit and embedded
- Ensures consistent permission assignment across all tasks of the same type
- Provides a stable extension point for new task types as the workflow library grows
- Enables operator-level review by task type category

**Operational Inputs:**
- Incoming task or workflow trigger (structured: task description, source, triggering event)
- Task type table (router reads this to classify)

**Operational Outputs:**
- Classified task object: `task_type`, `required_reads[]`, `runtime_class`, `permission_set`, `writeback_expectations`
- Classification audit entry

**Governance/Security Constraints:**
- Unclassified tasks must escalate â€” they cannot run with a fallback default classification
- Task type table is a governed document â€” changes require explicit user instruction
- Permission sets referenced by task types must stay within Permission Matrix ceilings
- Router classification is logged â€” classification decisions are auditable

**Implementation Direction:**
1. Define task type taxonomy (minimum 8 types): `operator-briefing`, `vault-maintenance`, `content-ingestion`, `research-synthesis`, `idea-graduation`, `project-review`, `scheduled-digest`, `ad-hoc-capture`
2. For each type, define: `required_reads[]`, `runtime_class`, `permission_set`, `writeback_expectations`, `escalation_trigger`
3. Implement `runtime/aor/task_router.py`: `classify_task(task_input)` â†’ `ClassifiedTask`
4. Wire into AOR execution pipeline at step 2 (after registry lookup, before role card loading)
5. Add task type to all audit log entries

**Dependencies:**
- Workflow Registry (Feature 1)
- Agent Role Cards (Feature 2 â€” role card selection is downstream of task classification)
- AOR execution engine (Phase 9 core)
- Permission Matrix (Phase 4 â€” already live)

**Not In Scope:**
- Natural language task parsing or intent inference (tasks are structured, not freeform)
- Dynamic task type creation at runtime
- Cross-system task routing (external task queues or ticketing systems)

**Success Criteria:**
- At least 8 task types defined in the routing table
- All AOR workflow executions pass through the router before running
- Unclassified task arrives â†’ escalation fires, execution blocked
- Task type field present in all audit log entries

**Status:** IMPLEMENTED â€” Pass 1 (2026-03-31): `runtime/aor/task_router.py` + `runtime/aor/task_type_table.yaml` (9 task types + `UNCLASSIFIED_SENTINEL`) fully functional; unclassified tasks are blocked at Stage 2 â€” execution never starts; task type logged in every AOR audit record

---

### Feature 4: Decision Ledger

**Feature Name:** Decision Ledger

**Feature Class:** Governance / Institutional Memory

**Primary Phase Placement:** Phase 9 â€” first-wave

**What It Is:**
The Decision Ledger is a canonical record-keeping system for operational and architectural decisions. Each ledger entry captures: the decision made, the date, the context that prompted it, the rationale, the alternatives considered, the consequences expected, and the decision owner. Ledger entries are immutable once written â€” corrections are addenda, not overwrites. The Ledger accumulates the "why" of ChaseOS operational history in a way that build logs and code comments cannot.

**Problem It Solves:**
Build logs record what was built. Code captures what was decided technically. Neither captures why a direction was chosen over alternatives, why a design trade-off was made, or what was rejected and why. Without a Decision Ledger, that institutional knowledge lives only in chat history â€” which is ephemeral, unsearchable, and unavailable to future runtimes or operators. Repeated decisions happen. Regressions into rejected patterns happen. Rationale is reconstructed from memory rather than record.

**Why It Is Being Added Now:**
Phase 9 introduces autonomous execution. When AOR runs a workflow, makes a judgment, or encounters a decision point, there must be a governed record of what was decided and why. This is not a nice-to-have in autonomous systems â€” it is a governance requirement. The Decision Ledger is the canonical home for that record.

**Where It Sits in ChaseOS:**
`07_LOGS/Decision-Ledger/` â€” one file per decision or decision session. A companion index at `07_LOGS/Decision-Ledger/Index.md` provides a searchable summary. The Gate governs all writes. Entries are not promoted to `02_KNOWLEDGE/` â€” they stay in `07_LOGS/` as historical record.

**What It Coordinates With:**
- AOR audit log (autonomous decisions are cross-referenced to ledger entries)
- Project OS files (significant project decisions reference ledger entry IDs)
- Project Pivot Log (Feature 6 â€” pivots reference the Decision Ledger entries that preceded them)
- Agent Role Cards (role card design decisions are ledger entries)

**What It Improves:**
- Replaces ephemeral chat-based rationale with durable, searchable institutional memory
- Makes autonomous decision points auditable by a future operator or runtime
- Provides SIC with structured decision history for reasoning-backed synthesis
- Prevents repeated relitigating of settled decisions

**Operational Inputs:**
- Decision context: what was being decided, what options were available
- Decision outcome: what was chosen, what was rejected
- Rationale: why this choice
- Consequences: what changes, what is now ruled out

**Operational Outputs:**
- Ledger entry file: structured Markdown at `07_LOGS/Decision-Ledger/YYYY-MM-DD_[decision-slug].md`
- Index entry added to `07_LOGS/Decision-Ledger/Index.md`

**Governance/Security Constraints:**
- Ledger entries are immutable â€” overwrites are not permitted; corrections are appended with `[CORRECTION YYYY-MM-DD]` prefix
- Gate governs writes to `07_LOGS/Decision-Ledger/`
- Decision entries written by autonomous runtimes must be flagged with `source: autonomous` in frontmatter
- Entries referencing personal information or sensitive operational details follow the same trust tier as canonical state files

**Implementation Direction:**
1. Define ledger entry schema (Markdown frontmatter): `decision_id`, `date`, `decision`, `context`, `rationale`, `alternatives_rejected[]`, `consequences`, `owner`, `source` (`operator`/`autonomous`/`agent-assisted`)
2. Create `07_LOGS/Decision-Ledger/` directory with `Index.md`
3. Create at least two seed ledger entries documenting key ChaseOS architectural decisions (e.g., quarantine-first doctrine, local-first SIC, advisory-only hint vocabulary)
4. Define ledger entry template in `05_TEMPLATES/`
5. AOR writes a ledger entry for any workflow execution that makes a branching decision

**Dependencies:**
- ChaseOS Gate (Phase 5 â€” already live)
- AOR execution engine (Phase 9 â€” for autonomous entry writes)
- `07_LOGS/` structure (already established)

**Not In Scope:**
- Decision versioning or branching history (decisions are linear record, not a tree)
- Decision impact scoring or weighting
- External integration (ticketing system sync, Jira, etc.)
- AI-generated decision rationale without operator review

**Success Criteria:**
- At least 3 ledger entries written with canonical structure
- AOR writes a ledger entry for branching decision points during autonomous execution
- Index.md reflects all entries
- Immutability rule enforced â€” overwrites are rejected by Gate policy

**Status:** IMPLEMENTED â€” Pass 1 (2026-03-31): `07_LOGS/Decision-Ledger/` live with `Index.md` + 3 seed entries (SIC scope expansion, stdlib-first constraint, AOR bounded autonomy model) + `05_TEMPLATES/Decision-Log-Template.md`; AOR engine writes an audit record (Stage 8) that cross-references ledger entries; full autonomous branching-decision writes deferred to Pass 2 when handlers run real work

---

### Feature 5: Feature Filter

**Feature Name:** Feature Filter

**Feature Class:** Governance / Scope Control

**Primary Phase Placement:** Phase 9 â€” first-wave

**What It Is:**
The Feature Filter is a formal 6-question filter applied to all feature proposals before they are adopted into any ChaseOS roadmap phase. The six questions are: (1) Does this fit an existing layer/phase, or does it require a new layer? (2) What problem does it solve that cannot be solved with current capabilities? (3) What does ChaseOS look like without it, and is that state acceptable? (4) Does this introduce new security or governance surface area? (5) What does this depend on, and are those dependencies already built? (6) What would have to be NOT built (or delayed) to build this? A feature that cannot clearly answer all six questions is deferred, not adopted. The filter is a governance artifact, not a judgment call.

**Problem It Solves:**
Roadmap drift. Phase 8 accumulated 10 passes partly because each pass surfaced adjacent needs. Without a formal filter, feature adoption is driven by proximity and enthusiasm rather than architectural necessity and dependency ordering. The Feature Filter makes the adoption decision explicit, documented, and reversible.

**Why It Is Being Added Now:**
Phase 9 is architecturally complex â€” AOR, SBP, and the adopted feature set must be built in dependency order. The Feature Filter ensures that any new feature proposal during Phase 9 is evaluated against the filter before being adopted, preventing scope explosion during the most infrastructure-intensive phase. The `06_AGENTS/Feature-Fit-Register.md` (Phase 8 Pass 10) is the register; the Feature Filter is the protocol for writing to it.

**Where It Sits in ChaseOS:**
The filter lives as a formal SOP at `04_SOPS/Feature-Filter-SOP.md`. It is referenced by `06_AGENTS/Feature-Fit-Register.md` as the protocol for new feature additions. The filter is applied whenever a feature proposal is raised in any session.

**What It Coordinates With:**
- Feature-Fit-Register.md (filter determines register placement)
- ROADMAP.md (filter outcome determines roadmap adoption)
- Project Pivot Log (Feature 6 â€” if a filter rejection causes a direction change, that change is a pivot entry)
- Decision Ledger (Feature 4 â€” filter outcomes for significant proposals become ledger entries)

**What It Improves:**
- Prevents scope creep during complex phases
- Makes adoption decisions auditable (the filter record shows the reasoning)
- Provides a lightweight governance layer for feature backlog management
- Creates a shared vocabulary between operator and agent for evaluating proposals

**Operational Inputs:**
- Feature proposal (description, motivation, rough implementation idea)
- Current phase state (which dependencies are built, which phases are active)
- Feature-Fit-Register.md (existing feature inventory)

**Operational Outputs:**
- Filter assessment: 6-question answers + recommendation (adopt / defer / reject)
- Filter record entry added to Decision Ledger if adopted
- Feature-Fit-Register.md updated with new entry if adopted

**Governance/Security Constraints:**
- Feature Filter SOP is a protected document â€” changes require explicit user instruction
- Filter bypass is not permitted; agent cannot adopt a feature without completing the filter
- Filter assessments written by autonomous runtimes must be reviewed by operator before register update
- Rejected features retain their filter record (no silent deletion)

**Implementation Direction:**
1. Write `04_SOPS/Feature-Filter-SOP.md` â€” full 6-question template, pass/defer/reject decision tree, integration notes for Feature-Fit-Register.md and Decision Ledger
2. Create filter record template in `05_TEMPLATES/feature-filter-record.md`
3. Reference filter SOP from Feature-Fit-Register.md preamble
4. Apply filter retrospectively to all 17 adopted Phase 9 features as seed entries

**Dependencies:**
- Feature-Fit-Register.md (Phase 8 Pass 10 â€” already live)
- Decision Ledger (Feature 4 â€” filter records belong in ledger)
- ROADMAP.md and PROJECT_FOUNDATION.md (output destinations)

**Not In Scope:**
- Automated feature scoring or ML-based priority ranking
- Integration with external backlog tools
- Quantitative ROI evaluation
- Retroactive filter application to Phase 1â€“8 features (seed entries only)

**Success Criteria:**
- Feature-Filter-SOP.md written and referencing all 6 questions
- At least one new feature proposal processed through the filter with documented outcome
- Feature-Fit-Register.md preamble references the SOP
- Filter record template exists in `05_TEMPLATES/`

**Status:** IMPLEMENTED â€” Pass 1 (2026-03-31): `04_SOPS/Feature-Filter-SOP.md` (6-question gate) + `05_TEMPLATES/Feature-Filter-Template.md` live; `06_AGENTS/Feature-Fit-Register.md` (Phase 8 Pass 10) is the register this SOP governs; retroactive seed entries not yet applied â€” deferred to a dedicated governance pass

---

### Feature 6: Project Pivot Log

**Feature Name:** Project Pivot Log

**Feature Class:** Governance / Institutional Memory

**Primary Phase Placement:** Phase 9 â€” first-wave

**What It Is:**
The Project Pivot Log is a structured record of major direction changes in ChaseOS development or operational strategy. Each entry captures: what the prior direction was, what changed, what triggered the change, what remains constant through the change, what the change kills (features or approaches now ruled out), and what the change unlocks (new capabilities or paths opened). Pivot entries are not routine decision records â€” they are reserved for inflection points where the system's operating model, architecture, or goal structure changes materially.

**Problem It Solves:**
Direction changes are inevitable in long-running systems. Without a formal record, pivots exist only as narrative in build logs or chat history. Future operators, runtimes, or contributors cannot understand why the current state diverged from earlier documented plans. Deprecated patterns get re-proposed. Architectural regressions happen because the rationale for a prior decision is lost. The Pivot Log preserves the "we tried that, here's why it changed" history permanently.

**Why It Is Being Added Now:**
ChaseOS has already had at least one significant pivot (scope expansion from governed memory system to local-first source intelligence OS, documented 2026-03-21). That pivot is in chat history and CLAUDE.md audit notes, but not in a formal structured log. Phase 9 is another potential inflection point â€” AOR introduces autonomous execution, which is a fundamentally different operating model. The Pivot Log should be seeded now, before Phase 9 runs, so that Phase 9 architectural decisions have a formal record.

**Where It Sits in ChaseOS:**
`07_LOGS/Pivot-Log/` â€” one file per recorded pivot, plus `Index.md`. Pivot entries are formal records, not project OS updates â€” they live in logs, not in the project directory. Pivots that affect Project-OS files cross-reference both locations.

**What It Coordinates With:**
- Decision Ledger (Feature 4 â€” pivots are high-significance decision records; cross-referenced)
- Project OS files (pivots that affect a project's operating model update the relevant Project-OS.md with a reference)
- ROADMAP.md (pivots that affect phase structure are documented in ROADMAP and cross-referenced to the Pivot Log)
- Feature-Fit-Register.md (features killed by a pivot are marked deprecated with pivot reference)

**What It Improves:**
- Preserves inflection point rationale permanently
- Prevents architectural regression into deprecated patterns
- Makes ChaseOS evolution legible to future contributors and runtimes
- Provides SIC with structured context for strategic synthesis tasks

**Operational Inputs:**
- Description of the prior direction
- Description of what changed and the trigger
- What remains constant
- What is now killed/deprecated
- What is now unlocked

**Operational Outputs:**
- Pivot entry file: `07_LOGS/Pivot-Log/YYYY-MM-DD_[pivot-slug].md`
- Index entry: `07_LOGS/Pivot-Log/Index.md`
- Cross-reference updates in affected Project-OS files and ROADMAP.md

**Governance/Security Constraints:**
- Pivot entries are immutable after writing (same rule as Decision Ledger)
- Gate governs writes to `07_LOGS/Pivot-Log/`
- Pivots are operator-written â€” autonomous runtimes flag potential pivots for operator review; they do not write pivot entries unilaterally
- A pivot entry that marks features as deprecated must update the Feature-Fit-Register.md in the same session

**Implementation Direction:**
1. Define pivot entry schema: `pivot_id`, `date`, `prior_direction`, `what_changed`, `trigger`, `what_remains`, `what_is_killed[]`, `what_is_unlocked[]`, `owner`, `references[]`
2. Create `07_LOGS/Pivot-Log/` directory with `Index.md`
3. Write the first seed entry: ChaseOS scope expansion (2026-03-21) â€” governed memory system â†’ local-first Source Intelligence OS
4. Write the second seed entry: Phase 9 model change â€” session-based execution â†’ AOR autonomous execution
5. Create pivot entry template in `05_TEMPLATES/`

**Dependencies:**
- Decision Ledger (Feature 4 â€” pivots are referenced from the Decision Ledger)
- `07_LOGS/` structure (already established)
- ChaseOS Gate (Phase 5 â€” already live)

**Not In Scope:**
- Quantitative impact scoring for pivots
- Automated pivot detection from git history
- Pivot prediction or risk scoring
- Cross-project pivot synchronization

**Success Criteria:**
- At least 2 seed pivot entries written in canonical format
- Index.md reflects all entries
- `05_TEMPLATES/` has pivot entry template
- Feature-Fit-Register.md updated when a pivot kills a feature (tested in seed entries)

**Status:** IMPLEMENTED â€” Pass 1 (2026-03-31): `07_LOGS/Pivot-Log/` live with `Index.md` + 2 seed entries (scope expansion 2026-03-21; session-based â†’ AOR execution model) + `05_TEMPLATES/Pivot-Log-Template.md`; immutability rule enforced by Gate policy; Feature-Fit-Register.md deprecation cross-referencing deferred to when a pivot kills an active feature

---

### Feature 7: operator_today

**Feature Name:** operator_today

**Feature Class:** AOR Workflow â€” Operator Briefing

**Primary Phase Placement:** Phase 9 â€” first-wave

**What It Is:**
`operator_today` is the first live AOR workflow and currently runs on demand to produce a daily operator briefing. It reads current vault state â€” open tasks, project OS priority fields, recent captures in the intake surface, recent log entries, active sprint focus from `Now.md` â€” and outputs a structured daily brief: top priorities, open loops, pending captures awaiting promotion, and recommended first actions. The brief is written to a governed log destination, not surfaced only in chat. The workflow does not modify vault content â€” it reads and summarizes.

**Problem It Solves:**
Each operator session currently starts from scratch â€” re-reading `Now.md`, checking logs, scanning quarantine, reconstructing context. This manual re-orientation costs time and introduces inconsistency. `operator_today` automates the re-orientation into a reliable, repeatable, governed briefing that the operator receives at session start or on demand.

**Why It Is Being Added Now:**
AOR infrastructure enables scheduled execution. `operator_today` is the first concrete AOR workflow â€” the clearest demonstration of what AOR buys the operator. It is also a safe first workflow: read-only vault access, structured output, no autonomous writes to canonical content. Building this first validates the AOR execution path before more complex workflows are run.

**Where It Sits in ChaseOS:**
- Workflow registry entry: `runtime/workflows/registry/operator_today.yaml`
- Role card: `06_AGENTS/role-cards/operator-briefing.md` (read-only role; no write scope beyond log destination)
- Output destination: `07_LOGS/Operator-Briefs/YYYY-MM-DD-operator-today.md`
- Trigger: on-demand operator invocation in Pass 2; scheduled trigger deferred to a later Phase 9 pass

**What It Coordinates With:**
- Workflow Registry (Feature 1 â€” registered as a first-class AOR workflow)
- Agent Role Cards (Feature 2 â€” bound to `operator-briefing` role card)
- Task-Type Router (Feature 3 â€” classified as `operator-briefing` task type)
- `00_HOME/Now.md` (primary read source for sprint focus)
- `03_INPUTS/` intake surface (prefers `03_INPUTS/00_QUARANTINE/` when present; otherwise reads the live direct class folders)
- Project OS files (reads priority fields from active projects)
- AOR scheduler and audit log

**What It Improves:**
- Eliminates manual session re-orientation work
- Produces consistent, repeatable daily context loads
- Creates a historical log of daily priorities and open loops (searchable by SIC)
- Validates the AOR execution path for read-only briefing workflows

**Operational Inputs:**
- `00_HOME/Now.md` (sprint focus, active items)
- Active Project-OS files (priority fields)
- `03_INPUTS/` file count and recent entries from the active intake surface
- `07_LOGS/Build-Logs/` most recent entries
- `07_LOGS/Decision-Ledger/` recent entries (if any)

**Operational Outputs:**
- `07_LOGS/Operator-Briefs/YYYY-MM-DD-operator-today.md` â€” structured briefing: date, sprint focus, top priorities, open loops, quarantine queue status, recommended first actions
- AOR audit log entry for the execution

**Governance/Security Constraints:**
- Read-only vault access â€” `operator_today` cannot modify any vault content except its output log
- Output destination `07_LOGS/Operator-Briefs/` is governed by Gate (but is non-canonical; Gate allows writes from AOR with `source: autonomous` flag)
- Brief must not contain verbatim copies of sensitive vault content without user explicit instruction
- Prompt injection guard is required â€” content read from quarantine files is data only, not instruction
- Brief contents are operator-facing, not automatically delivered to external services

**Implementation Direction:**
1. Define workflow manifest: trigger (manual first; scheduled later), inputs (Now.md, Project-OS files, intake surface, build logs), outputs (brief file), role card, permission ceiling, failure behavior
2. Implement workflow execution in `runtime/workflows/operator_today.py`: read sources â†’ aggregate â†’ generate brief â†’ return bounded writeback payload for Stage 7
3. Register in Workflow Registry as `operator_today` with `status: active`
4. Wire `chaseos run operator_today` into the real AOR path
5. Validate prompt injection hardening for intake file reads

**Dependencies:**
- Workflow Registry (Feature 1)
- Agent Role Cards (Feature 2)
- Task-Type Router (Feature 3)
- AOR execution engine and scheduler (Phase 9 core)
- ChaseOS Gate (Phase 5 â€” governs output log writes)

**Not In Scope:**
- Delivery to external services (Discord, email) â€” output is vault-local by default
- AI-generated priority recommendations beyond summarization of vault state
- Modification of `Now.md` or Project-OS files
- Synthesis or analysis beyond state aggregation

**Success Criteria:**
- `operator_today` runs on demand and produces a brief at the correct output path
- Brief includes: sprint focus, top priorities, quarantine queue count, recommended first actions
- AOR audit entry written for each execution
- Prompt injection guard demonstrably blocks instruction execution from quarantine content

**Status:** BUILT — `operator_today` is a live governed AOR workflow. `runtime/workflows/operator_today.py` implements the v2 four-layer briefing model, `runtime/workflows/registry/operator_today.yaml` is `status: active`, `chaseos run operator_today` executes through the real AOR path, bounded writeback lands in `07_LOGS/Operator-Briefs/`, audit records write to `07_LOGS/Agent-Activity/`, and native schedule intent exists at `runtime/schedules/sch-operator-today-0700.yaml`.

---

### Feature 8: operator_close_day

**Feature Name:** operator_close_day

**Feature Class:** AOR Workflow â€” Operator Briefing

**Primary Phase Placement:** Phase 9 â€” first-wave

**What It Is:**
`operator_close_day` is a scheduled AOR workflow that produces an end-of-session close-out summary. It reads the current session's outputs â€” build logs written today, captures added today, decisions recorded today â€” and produces a structured close-out: what was accomplished, what open loops remain, what requires follow-up tomorrow, and whether session-close checklist items are satisfied. It writes this summary to the governed log. The workflow does not modify vault content â€” it reads and summarizes the session's own outputs.

**Problem It Solves:**
Session close-out is currently manual and inconsistent. The CLAUDE.md session-close checklist exists but is enforced by convention, not by system. `operator_close_day` makes close-out automatic and consistent. It also produces a daily close log that accumulates into a searchable session history â€” enabling later analysis of what was accomplished over time, which patterns repeat, and which open loops chronically remain unresolved.

**Why It Is Being Added Now:**
`operator_close_day` pairs with `operator_today` as the bookend briefing workflow set. Together, they represent the first full AOR workflow pair: open and close. Building them in the same phase validates the full AOR execution loop and demonstrates the infrastructure value. The close workflow is slightly more complex than `operator_today` because it must determine what happened today â€” but the same read-only role card and infrastructure apply.

**Where It Sits in ChaseOS:**
- Workflow registry entry: `runtime/workflows/registry/operator_close_day.yaml`
- Role card: `06_AGENTS/role-cards/operator-briefing.md` (same as `operator_today` â€” both are briefing-class read-only workflows)
- Output destination: `07_LOGS/Operator-Briefs/YYYY-MM-DD-close.md`
- Trigger: cron (end-of-day) or on-demand operator invocation

**What It Coordinates With:**
- Same infrastructure as `operator_today` (Workflow Registry, Role Cards, Task-Type Router, AOR scheduler)
- `07_LOGS/Build-Logs/` (scans for today's entries)
- `03_INPUTS/00_QUARANTINE/` (counts captures added today)
- `07_LOGS/Decision-Ledger/` (flags any decisions made today)
- Session-close checklist from `CLAUDE.md` (used as the completeness check template)

**What It Improves:**
- Automates the session-close checklist
- Produces consistent close-out records searchable by SIC
- Accumulates a daily accomplishment log over time
- Identifies chronically unresolved open loops (patterns visible in log history)

**Operational Inputs:**
- Today's build logs (scanned from `07_LOGS/Build-Logs/` by date)
- Today's quarantine additions (scanned from `03_INPUTS/00_QUARANTINE/` by mtime)
- Today's Decision Ledger entries
- Session-close checklist template (from `CLAUDE.md` or a derived SOP)

**Operational Outputs:**
- `07_LOGS/Operator-Briefs/YYYY-MM-DD-close.md` â€” structured close-out: accomplished today, open loops, follow-up items, checklist status
- AOR audit log entry

**Governance/Security Constraints:**
- Same as `operator_today` â€” read-only vault access; output destination governed by Gate; prompt injection guard on any external content read
- Close-out summary must not mark checklist items as complete unless the corresponding vault evidence exists (build log written, archive note created, etc.)

**Implementation Direction:**
1. Reuse `operator-briefing` role card from `operator_today` (same role class)
2. Implement `runtime/workflows/operator_close_day.py` â€” reads today's logs, aggregates, generates close-out, writes to output log
3. Register in Workflow Registry as `operator_close_day`
4. Wire to AOR scheduler for end-of-day trigger
5. Implement checklist completeness check against CLAUDE.md session-close criteria

**Dependencies:**
- Same as `operator_today` (Workflow Registry, Role Cards, Task-Type Router, AOR)
- `operator_today` should be built first (establishes the briefing workflow pattern)

**Not In Scope:**
- Delivery to external services
- Automated vault remediation (close-out does not fix open loops â€” it surfaces them)
- Evaluation of work quality â€” only completeness check

**Success Criteria:**
- `operator_close_day` runs on demand and produces a close-out at the correct output path
- Close-out includes: today's accomplishments, open loops, follow-up items, checklist status
- Checklist items marked incomplete only when vault evidence is absent
- AOR audit entry written for each execution

**Status:** BUILT — `operator_close_day` is live. `runtime/workflows/operator_close_day.py` implements the v2 four-layer close model; manifest `status: active`; wired into Stage 6 dispatch; reads today's build logs, recent decisions, quarantine status, Now.md phase line, and same-day AOR activity; accepts operator-provided `open_loops` and `notes`; writes structured close note to `07_LOGS/Operator-Briefs/`; audit record writes to `07_LOGS/Agent-Activity/`; native schedule intent exists at `runtime/schedules/sch-operator-close-day-1900.yaml`.

---

### Feature 9: graph_hygiene

**Feature Name:** graph_hygiene

**Feature Class:** AOR Workflow â€” Vault Maintenance

**Primary Phase Placement:** Phase 9 â€” first-wave

**What It Is:**
`graph_hygiene` is a scheduled AOR workflow that scans the vault graph and produces a structured maintenance proposal â€” not a rewrite, not autonomous edits. It identifies: broken internal links, orphaned notes (no inbound links and no outbound links), notes with stale frontmatter (missing required fields, wrong `knowledge_class` for their location), index files out of sync with their actual directory contents, and notes in `03_INPUTS/` that have not moved through the ingest pipeline in more than N days. The output is a hygiene report. The operator reviews and applies â€” `graph_hygiene` does not modify vault content.

**Problem It Solves:**
Vault entropy. As ChaseOS grows, broken links, orphaned notes, and stale metadata accumulate. Manual auditing is time-consuming and inconsistent. Without periodic hygiene, the vault's graph integrity degrades: SIC retrieval quality drops (broken sources), promotion pipelines stall (quarantine backlog grows), and index files diverge from reality. `graph_hygiene` makes entropy visible and actionable on a schedule.

**Why It Is Being Added Now:**
Phase 9 introduces scheduled autonomous execution. `graph_hygiene` is a safe, bounded, read-only workflow that demonstrates scheduled maintenance value. It runs on a weekly or on-demand cadence, produces a structured report, and leaves all decisions to the operator. This is exactly the profile for which AOR was designed: autonomous sensing, operator acting.

**Where It Sits in ChaseOS:**
- Workflow registry entry: `runtime/workflows/registry/graph_hygiene.yaml`
- Role card: `06_AGENTS/role-cards/vault-maintenance.yaml` (read-only proposal role; write scope = hygiene report only)
- Output destination: `07_LOGS/Hygiene-Reports/YYYY-MM-DD-graph-hygiene.md`
- Trigger: cron (weekly) or on-demand operator invocation

**What It Coordinates With:**
- Workflow Registry (Feature 1)
- Agent Role Cards (Feature 2 â€” `vault-maintenance` role card)
- Task-Type Router (Feature 3 â€” classified as `vault-maintenance` task type)
- graduate_ideas (Feature 10 â€” hygiene report may identify idea graduation candidates)
- AOR scheduler and audit log

**What It Improves:**
- Makes vault entropy visible before it degrades SIC retrieval quality
- Keeps quarantine backlog visible (aging captures flagged)
- Keeps index files in sync with reality
- Provides input to the graduate_ideas workflow (orphaned ideas may be graduation candidates)

**Operational Inputs:**
- Full vault file tree (read-only scan)
- Internal link graph (extracted from Markdown files)
- Required frontmatter schema (from `06_AGENTS/Knowledge-Taxonomy.md`)
- Index file list and their expected contents
- Quarantine directory with capture timestamps

**Operational Outputs:**
- `07_LOGS/Hygiene-Reports/YYYY-MM-DD-graph-hygiene.md` â€” structured report: broken links list, orphaned notes list, stale frontmatter list, index drift entries, aging quarantine items (with days since capture)
- AOR audit log entry

**Governance/Security Constraints:**
- Read-only vault access â€” `graph_hygiene` cannot modify any vault content
- Hygiene report is a proposal, not an execution â€” operator must apply changes manually or via an explicit follow-up pass
- No automated link repair, no automated file moves, no automated frontmatter patching
- Report must not surface the content of quarantine captures â€” only metadata (filename, capture date, days aging)

**Implementation Direction:**
1. Define `vault-maintenance` role card: read-only; allowed actions = scan, read, report; forbidden actions = write, modify, promote, delete
2. Implement `runtime/workflows/graph_hygiene.py`: scan vault tree â†’ extract links â†’ identify broken/orphaned/stale â†’ generate report â†’ write to output log
3. Register in Workflow Registry as `graph_hygiene`
4. Wire to AOR scheduler for weekly trigger
5. Test scan against real vault; validate that report surface is metadata-only

**Dependencies:**
- Workflow Registry (Feature 1)
- Agent Role Cards (Feature 2)
- Task-Type Router (Feature 3)
- AOR execution engine (Phase 9 core)
- Knowledge-Taxonomy.md (Phase 6 â€” already live; required frontmatter schema source)

**Not In Scope:**
- Automated application of hygiene proposals
- Graph visualization
- Cross-vault hygiene (ChaseOS vault only)
- Semantic content analysis (structure and metadata only, not content quality)

**Success Criteria:**
- `graph_hygiene` runs on demand and produces a report at the correct output path
- Report includes: broken links, orphaned notes, stale frontmatter, index drift, aging quarantine items
- No vault content modified during or after execution
- Report format is readable and actionable by the operator

**Status:** BUILT — Pass 4 (2026-04-09): `runtime/workflows/registry/graph_hygiene.yaml` is `status: active`; `runtime/workflows/graph_hygiene.py` is implemented; the workflow runs through the real AOR path and writes a proposal-only hygiene report to `07_LOGS/Hygiene-Reports/`; no canonical vault content is modified.

---

### Feature 10: graduate_ideas

**Feature Name:** graduate_ideas

**Feature Class:** AOR Workflow â€” Idea Lifecycle

**Primary Phase Placement:** Phase 9 â€” first-wave

**What It Is:**
`graduate_ideas` is a workflow that surfaces raw notes, fragments, and quarantine captures that are eligible for promotion to durable vault destinations â€” and proposes explicit promotion decisions. It does not promote automatically. It reads the `generated-ideas` layer (Layer C in the AI-Generated-Output-Bridge model), the quarantine directory, and any notes tagged with `knowledge_class: generated-ideas` or `promotion_status: candidate`, and produces a structured graduation proposal: for each candidate, suggested destination, suggested `knowledge_class` after promotion, and a brief rationale. The operator makes the actual promotion call.

**Problem It Solves:**
Ideas accumulate. Raw notes, fragments, quarantine captures, and generated outputs pile up in workspace-local and quarantine locations. Without an explicit graduation workflow, the path from raw idea to durable canonical note is informal and inconsistent. Good ideas get lost. Low-quality ideas persist indefinitely. The `AI-Generated-Output-Bridge.md` (Phase 8) defined the Layer Aâ†’Bâ†’Câ†’D promotion path conceptually; `graduate_ideas` makes that path executable.

**Why It Is Being Added Now:**
The quarantine and generated-ideas layers are live. The promotion path is designed but not operationalized. Phase 9 is the right time to build the graduation workflow â€” AOR provides the execution infrastructure, and the first-wave features provide the governance layer (Role Cards, Router, Registry) that makes a promotion-adjacent workflow safe to run autonomously. The workflow is still operator-gated at promotion time, so it carries low risk.

**Where It Sits in ChaseOS:**
- Workflow registry entry: `runtime/workflows/registry/graduate_ideas.yaml`
- Role card: `06_AGENTS/role-cards/idea-graduation.yaml` (read quarantine/generated-ideas; write scope = graduation proposal log only; promotion decisions require operator approval)
- Output destination: `07_LOGS/Graduation-Proposals/YYYY-MM-DD-graduate-ideas.md`
- Trigger: on-demand operator invocation (not scheduled by default â€” operator decides when to review graduation queue)

**What It Coordinates With:**
- AI-Generated-Output-Bridge.md (Phase 8 â€” defines the Layer Aâ†’Bâ†’Câ†’D graduation model)
- Workflow Registry (Feature 1)
- Agent Role Cards (Feature 2 â€” `idea-graduation` role card)
- Task-Type Router (Feature 3 â€” classified as `idea-graduation` task type)
- graph_hygiene (Feature 9 â€” hygiene report may surface graduation candidates)
- SIC (Phase 7 â€” graduated notes become SIC-retrievable source packages after promotion)

**What It Improves:**
- Operationalizes the graduation path defined in AI-Generated-Output-Bridge.md
- Prevents good ideas from being lost in the quarantine or generated-ideas layer
- Makes the promotion decision explicit and operator-gated (not automatic)
- Feeds durable content back into SIC for future retrieval-backed reasoning

**Operational Inputs:**
- `03_INPUTS/00_QUARANTINE/` directory (all classes; filtered by `promotion_status` sidecar field)
- `generated-ideas` layer notes (if any exist in `02_KNOWLEDGE/` or workspace-local)
- Notes tagged `knowledge_class: generated-ideas` or `promotion_status: candidate`
- Destination taxonomy from `06_AGENTS/Knowledge-Taxonomy.md`

**Operational Outputs:**
- `07_LOGS/Graduation-Proposals/YYYY-MM-DD-graduate-ideas.md` â€” structured proposal: for each candidate, current location, suggested destination, suggested knowledge_class, rationale, operator decision field (to be filled by operator)
- AOR audit log entry

**Governance/Security Constraints:**
- Graduation proposals are proposals only â€” `graduate_ideas` cannot write to canonical destinations without explicit operator approval
- Promotion decisions must be operator-initiated; no autonomous promotion to `02_KNOWLEDGE/` or `01_PROJECTS/`
- Generated-ideas content must not be treated as canonical truth without endorsement (per Knowledge-Taxonomy.md Phase 6 doctrine)
- Gate governs all actual promotion writes (same as any canonical write)

**Implementation Direction:**
1. Define `idea-graduation` role card: read quarantine + generated-ideas; forbidden = write to canonical without operator approval; escalation = any promotion attempt
2. Implement `runtime/workflows/graduate_ideas.py`: scan candidates â†’ apply graduation criteria â†’ generate proposal â†’ write to output log
3. Define graduation criteria: minimum age in quarantine/generated-ideas layer, `promotion_status` field value, knowledge_class suitability for destination
4. Register in Workflow Registry as `graduate_ideas`
5. Wire operator review step: proposal file is the handoff; operator marks decisions and runs a separate apply step

**Dependencies:**
- Workflow Registry (Feature 1)
- Agent Role Cards (Feature 2)
- Task-Type Router (Feature 3)
- AI-Generated-Output-Bridge.md (Phase 8 â€” graduation model already defined)
- Knowledge-Taxonomy.md (Phase 6 â€” destination taxonomy)
- Phase 8 capture layer (quarantine directory structure already live)

**Not In Scope:**
- Automated promotion without operator approval
- Content quality scoring or semantic evaluation
- Deletion of rejected candidates (candidates remain until operator decides)
- Cross-vault graduation

**Success Criteria:**
- `graduate_ideas` runs on demand and produces a graduation proposal at the correct output path
- Each proposal entry includes: current location, suggested destination, suggested knowledge_class, rationale
- No canonical vault writes during execution
- Operator decision field is present and clearly labeled in the proposal output

**Status:** BUILT — Pass 4 (2026-04-09): `runtime/workflows/registry/graduate_ideas.yaml` is `status: active`; `runtime/workflows/graduate_ideas.py` is implemented; the workflow runs through the real AOR path and writes a proposal-only graduation report to `07_LOGS/Graduation-Proposals/`; no canonical promotion occurs during execution.

---

## Second-Wave Features (Dependent)

Features 11â€“16 require the first-wave foundation to be stable before implementation begins.

---

### Feature 11: Provenance Schema

**Feature Name:** Provenance Schema

**Feature Class:** Data Governance / Lineage

**Primary Phase Placement:** Phase 9 â€” second-wave

**What It Is:**
The Provenance Schema is a machine-readable lineage model attached to ChaseOS notes, outputs, and source packages. It formally captures: source package IDs that contributed to this output, the processing stage at which this content was created (raw capture â†’ quarantine â†’ promoted â†’ synthesized â†’ generated â†’ endorsed), the verification status (unverified / operator-reviewed / cross-referenced), and a lineage chain showing the transformation path from source to current form. The schema is embedded in note frontmatter and/or sidecar files.

**Problem It Solves:**
ChaseOS produces many kinds of outputs â€” raw captures, SIC-generated synthesis, endorsed ideas, canonical notes. Without provenance, it is impossible to know where a given piece of content came from, what it went through, or how much it can be trusted. This matters for SIC retrieval (you should weight highly-verified content more heavily), for operator review (you should know if a recommendation comes from a single unverified source), and for long-term governance (you should be able to audit any canonical claim back to its origin).

**Why It Is Being Added Now (second-wave):**
Provenance is meaningful only once the data it tracks is flowing â€” the capture layer (Phase 8) and SIC pipeline (Phase 7) must be live before provenance schemas are worth populating. Building provenance in second-wave ensures the schema is designed against real data flows, not hypothetical ones. The Context Governance Layer (Feature 12) consumes provenance data, so Provenance Schema is a prerequisite for that feature.

**Where It Sits in ChaseOS:**
- Schema definition: `runtime/schemas/provenance_schema.md` and `runtime/schemas/provenance_schema.yaml`
- Applied to: SIC source package sidecars, promoted notes (frontmatter), generated output files
- Cross-references sidecar schema v8.3 (`capture_id`, `SHA-256`) as Phase 8 foundation

**What It Coordinates With:**
- Phase 8 sidecar schema v8.3 (capture_id, SHA-256 are provenance anchors)
- SIC source package schema (Phase 7 â€” source package IDs are lineage nodes)
- Context Governance Layer (Feature 12 â€” consumes provenance fields)
- Agent Scorecards (Feature 13 â€” scorecard tracks provenance chain quality over time)
- Gate (all writes that update provenance fields are governed)

**What It Improves:**
- Makes every output's origin auditable
- Enables SIC to weight evidence by verification status
- Provides the data layer that Context Governance Layer needs to assess trustworthiness
- Creates a formal basis for the `trace_idea` workflow (Feature 15)

**Operational Inputs:**
- Source package metadata (IDs, ingest timestamps, processing stage)
- Phase 8 sidecar fields (capture_id, SHA-256, promotion_status)
- Processing event log (what happened to this content at each stage)

**Operational Outputs:**
- Provenance-annotated frontmatter blocks for promoted notes
- Provenance sidecar extension for source packages
- Schema definition and validation tooling

**Governance/Security Constraints:**
- Provenance fields are append-only â€” they accumulate lineage; they do not overwrite history
- Provenance data does not contain raw content from external sources â€” only IDs, timestamps, and stage markers
- Verification status changes must be explicitly operator-authored or AOR-authored with audit trail
- Schema changes require explicit user instruction (breaking changes require a migration pass)

**Implementation Direction:**
1. Define provenance schema: `source_ids[]`, `processing_stage`, `verification_status`, `lineage_chain[]`, `created_at`, `last_modified_at`, `operator_reviewed_at`
2. Extend SIC source package schema with provenance block
3. Add provenance validation to promotion path (Gate check: promoted notes must have minimum provenance fields)
4. Implement `runtime/schemas/provenance_validator.py` â€” validates provenance blocks against schema
5. Write migration note for existing Phase 7 workspaces (add provenance retroactively via a scan pass)

**Dependencies:**
- Phase 7 SIC (source package schema â€” already live)
- Phase 8 sidecar schema v8.3 (already live â€” provenance extends it)
- First-wave features (Decision Ledger for tracking schema decisions; Feature Filter for schema adoption)

**Not In Scope:**
- External provenance registries or blockchain-based lineage
- Cross-vault provenance linking
- Automated verification (verification status is always human or runtime-assigned, never inferred automatically)

**Success Criteria:**
- Provenance schema defined and documented
- At least one promoted note has provenance frontmatter populated
- Provenance validator runs without errors on schema-compliant content
- Context Governance Layer (Feature 12) can consume provenance fields at build time

**Status:** NOT BUILT â€” Phase 9 second-wave target

---

### Feature 12: Context Governance Layer

**Feature Name:** Context Governance Layer

**Feature Class:** Data Governance / Trust Model

**Primary Phase Placement:** Phase 9 â€” second-wave

**What It Is:**
The Context Governance Layer (CGL) is a mechanism that makes vault notes action-governing â€” i.e., a note's metadata determines what actions can be taken with it and by whom. Each note in the CGL carries: trust level (untrusted / reviewed / verified / canonical), sensitivity classification (internal / operator-only / shareable), promotion stage (quarantine / promoted / synthesized / canonical), and allowed surfaces (which outputs or runtimes may use this note as input). The CGL does not change note content â€” it annotates notes with governance metadata that AOR, SIC, and the Gate can consult before using a note as input to an action.

**Problem It Solves:**
Right now, notes in the vault have structural classification (`knowledge_class`) but not action-governing metadata. SIC retrieves notes without knowing their trust level. AOR would use notes as context without knowing their sensitivity. A quarantine capture and a canonical doctrine note look the same to an automated runtime unless it reads sidecar data manually. The CGL provides a formal, consistent governance layer that automated systems can consult.

**Why It Is Being Added Now (second-wave):**
CGL requires Provenance Schema (Feature 11) for its trust level and verification status fields, and requires first-wave features (Role Cards, Task-Type Router) to define how governance constraints map to execution decisions. Building CGL after those dependencies are live ensures the design is grounded in real data and real execution constraints rather than hypothetical requirements.

**Where It Sits in ChaseOS:**
- Governance metadata: embedded in note frontmatter (`trust_level`, `sensitivity`, `promotion_stage`, `allowed_surfaces[]`)
- Enforcement: `runtime/aor/context_governance.py` â€” reads CGL metadata and resolves whether a note is eligible for use in a given action
- Validation: Gate extended with CGL check (notes used in write actions must have compatible CGL classification)

**What It Coordinates With:**
- Provenance Schema (Feature 11 â€” CGL trust level derives from provenance verification status)
- Agent Role Cards (Feature 2 â€” role cards declare which CGL tiers they can access)
- SIC retrieval layer (Phase 7 â€” evidence packets include CGL tier of source material)
- Gate (enforces CGL constraints at write time)
- Agent Scorecards (Feature 13 â€” CGL violation events are scorecard signals)

**What It Improves:**
- Prevents low-trust content from being used in high-stakes autonomous actions without explicit authorization
- Makes the trust model machine-readable (not just documented in markdown)
- Enables SIC to weight evidence by trust tier in retrieval output
- Provides a formal basis for sensitivity classification (operator-only content stays operator-only)

**Operational Inputs:**
- Note frontmatter (existing knowledge_class, promotion_status)
- Provenance Schema fields (verification_status)
- AOR runtime request (which notes does this workflow want to use as context?)

**Operational Outputs:**
- CGL-annotated frontmatter blocks for governed notes
- Context resolution result per note per action: `eligible` / `restricted` / `blocked`
- CGL violation log entries

**Governance/Security Constraints:**
- CGL metadata is set by operator or AOR with audit trail â€” not inferred automatically without explicit authorization
- Downgrading trust level (from verified to reviewed, or from canonical to untrusted) requires explicit operator instruction
- Blocked notes cannot be used as AOR context under any automatic escalation
- CGL annotations for sensitive notes must be consistent with `Trust-Tiers.md` (Phase 4)

**Implementation Direction:**
1. Define CGL frontmatter schema: `trust_level`, `sensitivity`, `promotion_stage`, `allowed_surfaces[]`
2. Implement `runtime/aor/context_governance.py`: `resolve_context_eligibility(note, action)` â†’ `CglResult`
3. Extend Gate's pre-write check to include CGL compatibility check
4. Add CGL fields to the standard note template in `05_TEMPLATES/`
5. Write CGL violation events to AOR audit log

**Dependencies:**
- Provenance Schema (Feature 11 â€” prerequisite)
- Agent Role Cards (Feature 2 â€” role cards reference CGL tiers)
- SIC retrieval layer (Phase 7 â€” needs CGL tier in evidence packets)
- Gate (Phase 5 â€” extended with CGL check)
- Trust-Tiers.md (Phase 4 â€” already live; CGL trust levels must align)

**Not In Scope:**
- Automated trust level inference from content
- Per-sentence or per-paragraph CGL annotation (note-level granularity only)
- Cross-vault CGL synchronization
- Public-facing content classification (CGL is internal governance only)

**Success Criteria:**
- CGL frontmatter schema defined and documented
- At least 10 notes annotated with CGL metadata
- `context_governance.py` resolves eligibility for at least 3 action types
- SIC evidence packets include CGL tier of source material
- CGL violation events appear in AOR audit log

**Status:** NOT BUILT â€” Phase 9 second-wave target

---

### Feature 13: Agent Scorecards

**Feature Name:** Agent Scorecards

**Feature Class:** Agent Identity / Runtime Performance Memory

**Primary Phase Placement:** Phase 9 â€” second-wave

**What It Is:**
Agent Scorecards are runtime-performance memory records for each AOR-registered agent runtime. A scorecard tracks, over time: reliability (did the runtime complete its assigned workflows?), overreach (did the runtime attempt actions outside its declared role card?), compliance (did the runtime respect CGL constraints and permission ceilings?), and output quality signals (operator acceptance rate of generated content). Scorecards accumulate from AOR audit log entries and provide the data layer for the Agent Identity Ledger's behavioral evolution tracking.

**Problem It Solves:**
AOR will run multiple runtimes autonomously. Without performance memory, the system cannot distinguish a reliable runtime from an unreliable one. Overreach events are logged but not aggregated. Permission compliance is checked but not tracked longitudinally. The operator has no summary view of runtime performance history. Scorecards provide that aggregate view.

**Why It Is Being Added Now (second-wave):**
Scorecards require a body of AOR execution history to be meaningful. Building them before AOR runs any workflows would produce empty scorecards. Building them after first-wave features are live and at least one production workflow has run ensures scorecards are populated with real data. They also depend on Agent Role Cards (Feature 2 â€” overreach is defined relative to the role card) and Context Governance Layer (Feature 12 â€” CGL violations are a scorecard signal).

**Where It Sits in ChaseOS:**
- Scorecard store: `runtime/memory/scorecards/[runtime_id].json` (Layer C in Agent-Memory-Architecture)
- Scorecard updater: wired into AOR audit log post-processing
- Canonical doc extension: `06_AGENTS/Agent-Memory-Architecture.md` (scorecards as Layer C formal structure)

**What It Coordinates With:**
- AOR audit log (primary data source for scorecard updates)
- Agent Role Cards (Feature 2 â€” compliance measured against declared role card)
- Context Governance Layer (Feature 12 â€” CGL violation events feed scorecard)
- Agent Identity Ledger (Phase 9 â€” scorecard is the data source for ledger behavioral evolution section)
- Execution Repair Memory (AOR doc â€” repair events also feed scorecard)

**What It Improves:**
- Makes runtime performance history operator-visible
- Provides aggregate compliance signal for each runtime
- Enables operator to adjust role cards or permission ceilings based on demonstrated behavior
- Grounds Agent Identity Ledger behavioral evolution section in real performance data

**Operational Inputs:**
- AOR audit log entries (one per workflow execution: outcome, overreach events, CGL violations, operator acceptance)
- Role card declarations (used as the compliance baseline)

**Operational Outputs:**
- Updated scorecard JSON at `runtime/memory/scorecards/[runtime_id].json`
- Scorecard summary report (on-demand or as part of `operator_today` briefing)

**Governance/Security Constraints:**
- Scorecards are runtime-performance records â€” they are factual, not evaluative judgments
- Scorecard data must not be used to autonomously reduce a runtime's permissions (permission changes require operator instruction)
- Scorecard files are governed writes (Gate applies)
- Overreach classifications in scorecards are factual (action attempted outside role card scope) â€” not inferred

**Implementation Direction:**
1. Define scorecard schema: `runtime_id`, `executions[]` (each with: workflow_id, outcome, overreach_events, cgl_violations, operator_acceptance, timestamp), `aggregate_stats` (reliability_rate, overreach_rate, compliance_rate)
2. Implement `runtime/memory/scorecards/scorecard_updater.py` â€” consumes audit log entries, updates scorecard JSON
3. Wire updater into AOR post-execution hook
4. Add scorecard summary to `operator_today` output
5. Update `06_AGENTS/Agent-Memory-Architecture.md` Layer C section with scorecard structure

**Dependencies:**
- AOR execution engine and audit log (Phase 9 core â€” requires execution history)
- Agent Role Cards (Feature 2)
- Context Governance Layer (Feature 12)
- Agent-Memory-Architecture.md (Phase 7/architecture pass â€” already live; scorecard is its Layer C realization)

**Not In Scope:**
- Automated permission reduction based on scorecard data
- Cross-runtime comparison scoring
- Public scorecard reporting
- ML-based performance prediction

**Success Criteria:**
- Scorecard schema defined
- At least one scorecard populated after a production workflow run
- Overreach and CGL violation events appear in scorecard correctly
- Scorecard summary visible in `operator_today` output
- `runtime/memory/scorecards/` directory and updater implemented

**Status:** NOT BUILT â€” Phase 9 second-wave target

---

### Feature 14: Meeting Ingest Linker

**Feature Name:** Meeting Ingest Linker

**Feature Class:** Connector / Capture Enrichment

**Primary Phase Placement:** Phase 9 â€” second-wave

**What It Is:**
The Meeting Ingest Linker is a capture-time and post-capture enrichment workflow for meeting transcripts. When a transcript is captured (via CLI connector or watched folder), the linker proposes contextual links to existing vault content: projects mentioned in the transcript get linked to their Project-OS files, people mentioned get linked to contact or relationship notes, topics align with domain knowledge index entries. Links are proposed, not inserted â€” the operator reviews and accepts before any vault content is modified. The linker does not analyze meeting content for decisions or actions; it maps nouns to vault structure.

**Problem It Solves:**
Meeting transcripts are the most information-dense captures in ChaseOS â€” and the most disconnected from vault structure. A raw transcript in quarantine has no relationship to the projects it discussed, the people it involves, or the domain knowledge it references. Without the linker, the operator must do this mapping manually, which is time-consuming and rarely done. The linker makes transcripts first-class participants in the vault graph, not isolated text blobs.

**Why It Is Being Added Now (second-wave):**
The linker depends on the full capture pipeline (Phase 8 â€” already live), the graph model (graph_hygiene â€” Feature 9, first-wave), and CGL (Feature 12 â€” second-wave, so the linker knows which vault notes can be surfaced to the linking proposal). It also requires the Task-Type Router to be live so transcript ingestion can be classified as a distinct task type.

**Where It Sits in ChaseOS:**
- Workflow: `runtime/workflows/meeting_ingest_linker.py`
- Triggered post-capture for `.txt`/`.md` files with `origin_kind: meeting-transcript` or `domain_hint: meeting`
- Output: link proposal file at `07_LOGS/Link-Proposals/YYYY-MM-DD-[capture_id]-links.md`
- Integration with CLI connector: `chaseos capture file --origin-kind meeting-transcript` triggers linker

**What It Coordinates With:**
- Phase 8 capture pipeline (sidecar `origin_kind` field activates linker)
- graph_hygiene (Feature 9 â€” link proposal uses current graph to identify existing nodes)
- Context Governance Layer (Feature 12 â€” linker only proposes links to CGL-eligible content)
- SIC (Phase 7 â€” linker may query workspace for related source packages)
- graduate_ideas (Feature 10 â€” linked transcript may become a graduation candidate)

**What It Improves:**
- Connects transcripts to vault structure at ingest time rather than never
- Reduces manual context-mapping work per meeting
- Improves SIC retrieval relevance for meeting-adjacent topics
- Builds the meeting record layer that `trace_idea` (Feature 15) can traverse

**Operational Inputs:**
- Captured transcript (text content + sidecar metadata)
- Current vault graph (project OS files, contact notes, domain index files)
- CGL metadata for potential link targets (eligibility check)

**Operational Outputs:**
- `07_LOGS/Link-Proposals/YYYY-MM-DD-[capture_id]-links.md` â€” proposal: for each identified entity, suggested vault link target, confidence, rationale
- AOR audit log entry

**Governance/Security Constraints:**
- Link proposals are proposals only â€” no vault content is modified without operator approval
- Transcript content is not surfaced in the link proposal beyond entity names (no verbatim excerpts without explicit instruction)
- Gate governs any link application pass (subsequent write)
- CGL must approve link targets before they appear in proposals (no proposals to `trust_level: operator-only` content for external surfaces)

**Implementation Direction:**
1. Define entity extraction logic: project names, person names, domain topic references, explicit `[[wiki-link]]` mentions
2. Implement `runtime/workflows/meeting_ingest_linker.py`: extract entities â†’ match to vault â†’ check CGL eligibility â†’ generate proposal â†’ write to output log
3. Wire into capture pipeline via `origin_kind: meeting-transcript` post-capture hook
4. Implement operator apply step: operator reviews proposal file and runs `chaseos intake link-apply [proposal_path]` to apply accepted links

**Dependencies:**
- Phase 8 capture pipeline (sidecar `origin_kind` field â€” already live)
- graph_hygiene (Feature 9 â€” graph structure source)
- Context Governance Layer (Feature 12 â€” CGL eligibility check)
- AOR execution engine (Phase 9 core)

**Not In Scope:**
- Action item extraction from transcripts
- Sentiment analysis or meeting quality scoring
- Automated CRM or external system updates
- Cross-vault transcript linking

**Success Criteria:**
- Transcript captured with `--origin-kind meeting-transcript` triggers link proposal
- Proposal file identifies at least project and domain topic links from a test transcript
- No vault content modified without operator apply step
- CGL check prevents proposals to restricted content

**Status:** NOT BUILT â€” Phase 9 second-wave target

---

### Feature 15: trace_idea

**Feature Name:** trace_idea

**Feature Class:** AOR Workflow â€” Idea Lifecycle

**Primary Phase Placement:** Phase 9 â€” second-wave

**What It Is:**
`trace_idea` is an on-demand AOR workflow that traces the history of a given idea or concept through the vault â€” from first capture to current canonical state. Given a query (an idea name, a concept phrase, or a source package ID), it produces a lineage report: when the idea first appeared (which capture, which date), where it lived at each stage (quarantine â†’ generated-ideas â†’ promoted note), what processing it went through (SIC synthesis, operator endorsement, cross-references added), and what its current status is. The report is a read-only vault traversal â€” no content is modified.

**Problem It Solves:**
ChaseOS produces a large volume of notes, captures, and generated outputs over time. Without a tracing tool, the operator cannot easily answer: "Where did this idea come from?" or "When did I first capture this concept?" or "Has this idea been through SIC synthesis?" The answer is buried in build logs, sidecar metadata, and note histories. `trace_idea` makes lineage traversal a first-class operation.

**Why It Is Being Added Now (second-wave):**
`trace_idea` requires Provenance Schema (Feature 11) to have populated lineage chain fields, and graduate_ideas (Feature 10) to have established the graduation path that trace_idea traverses. It is a read operation on top of infrastructure that second-wave builds.

**Where It Sits in ChaseOS:**
- Workflow: `runtime/workflows/trace_idea.py`
- CLI: `chaseos trace --idea "idea name"` or `chaseos trace --source-id [capture_id]`
- Output: `07_LOGS/Trace-Reports/YYYY-MM-DD-trace-[slug].md`

**What It Coordinates With:**
- Provenance Schema (Feature 11 â€” primary lineage data source)
- graduate_ideas (Feature 10 â€” graduation history traversed)
- Phase 8 sidecar schema (capture_id, SHA-256 â€” lineage anchors)
- SIC source package schema (Phase 7 â€” SIC processing stages in lineage)
- Decision Ledger (Feature 4 â€” decisions about this idea appear in trace)

**What It Improves:**
- Makes idea lineage traversable in a single operation
- Provides accountability for canonical claims (can trace to originating capture)
- Supports the operator's retrospective analysis without manual log archaeology

**Operational Inputs:**
- Query: idea name / concept phrase / source package ID / capture ID
- Vault graph (sidecar files, provenance schema data, graduate_ideas logs, Decision Ledger)

**Operational Outputs:**
- `07_LOGS/Trace-Reports/YYYY-MM-DD-trace-[slug].md` â€” lineage report: first capture, promotion history, SIC processing stages, endorsement events, current canonical status

**Governance/Security Constraints:**
- Read-only vault access
- Trace report does not surface verbatim content from untrusted captures without explicit operator instruction
- CGL eligibility check on all nodes in lineage (restricted nodes appear as `[restricted â€” CGL tier: X]`)

**Implementation Direction:**
1. Implement `runtime/workflows/trace_idea.py`: query resolution â†’ lineage graph traversal â†’ report generation
2. Add `chaseos trace` CLI subcommand
3. Leverage provenance `lineage_chain[]` as primary traversal structure
4. Fall back to sidecar capture_id matching for pre-provenance captures

**Dependencies:**
- Provenance Schema (Feature 11)
- graduate_ideas (Feature 10)
- Phase 8 sidecar schema (already live)
- SIC (Phase 7 â€” already live)
- Context Governance Layer (Feature 12 â€” CGL check on trace nodes)

**Not In Scope:**
- Automated lineage repair
- Cross-vault tracing
- Graph visualization UI (Phase 10)

**Success Criteria:**
- `chaseos trace --idea "X"` produces a lineage report
- Report correctly identifies first capture and promotion history from provenance data
- CGL-restricted nodes appear as restricted (not surfaced as content)
- No vault content modified during execution

**Status:** NOT BUILT â€” Phase 9 second-wave target

---

### Feature 16: drift_scan

**Feature Name:** drift_scan

**Feature Class:** AOR Workflow â€” Doctrine / Behavior Alignment

**Primary Phase Placement:** Phase 9 â€” second-wave

**What It Is:**
`drift_scan` is a scheduled AOR workflow that compares ChaseOS operational behavior against stated doctrine. It reads canonical doctrine files (`SOUL.md` neighbors, `Principles.md`, `Operating-System.md` domain priorities), then reads operational history (build logs, Decision Ledger entries, Project-OS files active work fields), and identifies divergences: domains declared high-priority in doctrine that show no recent activity; behaviors in the build log that are not consistent with stated principles; project OS files with stale sprint focus; open loops that have persisted across multiple close-day reports. The output is a drift report â€” no vault content is modified.

**Problem It Solves:**
Long-running systems drift. Priorities get stated and then deprioritized in practice. Stated doctrine describes an ideal operating model; actual build history describes what was done. Without a comparison mechanism, drift is invisible until the operator notices (usually during a retrospective). `drift_scan` makes drift visible on a scheduled basis, while it is still correctable rather than entrenched.

**Why It Is Being Added Now (second-wave):**
`drift_scan` requires a body of operational history to scan â€” build logs, close-day reports, Decision Ledger entries. It requires first-wave features (Decision Ledger, close-day workflow) to be live and producing data before drift analysis is meaningful. Building it in second-wave ensures it has real data to work with.

**Where It Sits in ChaseOS:**
- Workflow: `runtime/workflows/drift_scan.py`
- Triggered: weekly cron or on-demand
- Output: `07_LOGS/Drift-Reports/YYYY-MM-DD-drift-scan.md`

**What It Coordinates With:**
- `SOUL.md` / `Principles.md` / `Operating-System.md` (doctrine source)
- `07_LOGS/Build-Logs/` (operational history)
- `07_LOGS/Decision-Ledger/` (decision history)
- Project-OS files (declared vs actual priorities)
- operator_close_day (Feature 8 â€” close-day reports are a drift data source)
- graph_hygiene (Feature 9 â€” neglected domains appear in both hygiene and drift reports)

**What It Improves:**
- Makes operational drift visible before it becomes entrenched
- Identifies neglected domains and false priorities
- Provides retrospective data for the Pivot Log (Feature 6 â€” drift patterns may indicate a needed pivot)
- Grounds operator retrospectives in systematic data rather than memory

**Operational Inputs:**
- Canonical doctrine files (read-only)
- `07_LOGS/Build-Logs/` (date range: last N days)
- `07_LOGS/Decision-Ledger/` entries
- Project-OS files (active priority fields)
- `operator_close_day` logs (open loops that repeat)

**Operational Outputs:**
- `07_LOGS/Drift-Reports/YYYY-MM-DD-drift-scan.md` â€” structured drift report: neglected domains, behavior inconsistencies, stale priorities, persistent open loops, recommended review items

**Governance/Security Constraints:**
- Read-only vault access (doctrine files are read, never written)
- Drift report flags behavior against doctrine â€” it does not modify doctrine or propose doctrine changes
- `SOUL.md` and `Principles.md` are read only â€” drift_scan cannot flag them as "incorrect" or propose edits to them
- Report is operator-facing; not delivered to external surfaces automatically

**Implementation Direction:**
1. Implement doctrine reader: extract domain priorities and behavioral norms from doctrine files (structured parsing, not semantic inference)
2. Implement history scanner: extract domain activity signal from build logs and close-day reports
3. Implement comparison engine: domain-by-domain activity check against doctrine priorities
4. Generate drift report with structured sections: neglected domains, priority drift, persistent open loops
5. Wire to weekly cron via AOR scheduler

**Dependencies:**
- operator_close_day (Feature 8 â€” close-day reports are drift data source)
- Decision Ledger (Feature 4)
- AOR execution engine (Phase 9 core)
- Doctrine files (already live)

**Not In Scope:**
- Automated doctrine modification based on drift findings
- Sentiment or tone analysis of build logs
- Cross-vault drift comparison
- Drift scoring or ranking

**Success Criteria:**
- `drift_scan` runs on demand and produces a drift report
- Report correctly identifies at least one neglected domain from build log history
- Doctrine files are not modified during execution
- Report includes: neglected domains, persistent open loops, recommended review items

**Status:** NOT BUILT â€” Phase 9 second-wave target

---

## Later Orchestration-Surface Candidate

### Feature 17: Paperclip

**Feature Name:** Paperclip

**Feature Class:** Orchestration Surface / External Interface Layer

**Primary Phase Placement:** Phase 10 candidate â€” NOT Phase 9 scope

**What It Is:**
Paperclip is a proposed orchestration surface that sits above ChaseOS. Where ChaseOS is the constitutional system â€” governing memory, governance, execution boundaries, and writeback â€” Paperclip is a higher-level coordination interface for operating across multiple systems simultaneously. Paperclip would provide: an executive dashboard for ChaseOS status and priorities, integration with external ticketing and project management systems, budget and resource approval surfaces, and cross-system trigger coordination (e.g., "when this GitHub issue closes, run this ChaseOS workflow"). Paperclip is the user-facing layer that makes ChaseOS's internal governance visible and actionable from outside the vault.

**Problem It Solves:**
ChaseOS is powerful but operates within the vault. Many operator decisions involve external systems â€” GitHub projects, financial tools, team communication, client ticketing. Coordinating between ChaseOS's internal state and these external systems currently requires manual translation. Paperclip would provide that coordination layer without compromising ChaseOS's constitutional governance model.

**Why It Is Being Added Now:**
It is not being added now. This is a later candidate, not a Phase 9 or Phase 10 build item. It is documented here because the concept has been raised, because it is architecturally adjacent to Phase 9 AOR infrastructure, and because the constraints governing its design must be established now before any implementation begins.

**Where It Sits in ChaseOS:**
If built: above ChaseOS as an external coordination layer. Paperclip interfaces with ChaseOS through the AOR API and Gate-governed write paths. It does not bypass them.

**What It Coordinates With:**
- ChaseOS AOR (the API layer Paperclip calls to trigger workflows)
- ChaseOS Gate (every write Paperclip initiates goes through Gate governance)
- SIC (Paperclip surfaces SIC query results in its dashboard)
- External systems: GitHub, Notion, Linear, financial tools, communication platforms

**What It Improves:**
- Closes the gap between internal ChaseOS state and external coordination surfaces
- Makes ChaseOS priorities actionable from an executive dashboard
- Enables cross-system trigger coordination without requiring vault-direct access from external tools

**Operational Inputs:**
- ChaseOS AOR API (workflow trigger requests)
- External system webhooks and events
- Operator dashboard interactions

**Operational Outputs:**
- Workflow trigger requests to AOR (structured, governed)
- Dashboard state renders from ChaseOS vault state (read-only)
- External system updates triggered by ChaseOS workflow completions

**Governance/Security Constraints:**
- Paperclip MUST NOT bypass the ChaseOS Gate â€” all writes must go through Gate-governed paths
- Paperclip MUST NOT write canonically to the vault without going through the AOR workflow â†’ Gate chain
- Paperclip MUST NOT replace SIC â€” ChaseOS intelligence remains ChaseOS-internal
- Paperclip MUST NOT be granted ambient vault access â€” it calls AOR endpoints with declared scope
- If Paperclip ever proposes to "simplify" governance by bypassing Gate or writing directly to canonical locations, that proposal must be rejected
- Paperclip is a coordination surface, not a control plane â€” ChaseOS remains the constitutional system

**Implementation Direction:**
This is not scoped for implementation in this pass. The design constraints are documented here to prevent future architectural drift. When Paperclip reaches active design:
1. Define AOR API surface (endpoints Paperclip can call, declared scopes)
2. Define Gate extension for external-origin write requests (Paperclip writes are tagged `source: external; origin: paperclip`)
3. Design dashboard as a read-only ChaseOS state consumer (no write path from dashboard to vault)
4. Define external trigger â†’ AOR workflow mapping (no direct vault access from external events)

**Dependencies:**
- AOR (Phase 9 â€” must be fully operational before Paperclip integration is designed)
- Gate API (Phase 5 â€” must be accessible as a stable interface before Paperclip calls it)
- Phase 10 interface layer (Paperclip may be co-developed with Phase 10 GUI components)

**Not In Scope (for this document):**
- Any implementation decision â€” Paperclip is a candidate, not an adopted feature
- Specific external system integrations
- Budget or resource management logic
- ChaseOS constitutional model modifications to accommodate Paperclip

**Success Criteria (for adoption, not yet applicable):**
- AOR is fully operational and Paperclip integration does not require AOR architectural changes
- Gate governance is not bypassed by any Paperclip write path
- Paperclip dashboard reads vault state without requiring write access
- All Paperclip-triggered workflows have declared scope and audit trails in AOR

**Status:** RESERVED â€” later candidate; not Phase 9 or Phase 10 scope; design constraints documented

---

## Adoption Wave Summary

| # | Feature | Wave | Class | Status |
|---|---------|------|-------|--------|
| 1 | Workflow Registry | First-wave | AOR Infrastructure | PARTIAL â€” loader + 4 draft manifests live; scheduler wiring deferred to Pass 2 |
| 2 | Agent Role Cards | First-wave | AOR Governance | PARTIAL â€” 2 role cards + loader live; more cards deferred to Pass 2+ |
| 3 | Task-Type Router | First-wave | AOR Infrastructure | IMPLEMENTED â€” `task_router.py` + `task_type_table.yaml` (9 types + sentinel) functional |
| 4 | Decision Ledger | First-wave | Governance | IMPLEMENTED â€” `07_LOGS/Decision-Ledger/` live; 3 seed entries + template |
| 5 | Feature Filter | First-wave | Governance | IMPLEMENTED â€” `04_SOPS/Feature-Filter-SOP.md` + template live |
| 6 | Project Pivot Log | First-wave | Governance | IMPLEMENTED â€” `07_LOGS/Pivot-Log/` live; 2 seed entries + template |
| 7 | operator_today | First-wave | AOR Workflow | BUILT — Pass 2 (2026-04-09); governed day-open workflow live |
| 8 | operator_close_day | First-wave | AOR Workflow | BUILT — Pass 3 (2026-04-09); governed day-close workflow live |
| 9 | graph_hygiene | First-wave | AOR Workflow | BUILT — Pass 4 (2026-04-09); proposal-only hygiene report workflow live |
| 10 | graduate_ideas | First-wave | AOR Workflow | BUILT — Pass 4 (2026-04-09); proposal-only graduation proposal workflow live |
| 11 | Provenance Schema | Second-wave | Data Governance | BUILT — 2026-04-25; `runtime/schemas/provenance_block.py` + `promotion_check.py`; 35 tests; SIC enriched |
| 12 | Context Governance Layer | Second-wave | Data Governance | BUILT — 2026-04-25; `runtime/aor/context_governance.py`; 77 tests; 10 notes annotated; AOR Stage 5 wired |
| 13 | Agent Scorecards | Second-wave | Agent Identity | BUILT — 2026-04-25; `runtime/memory/scorecards/scorecard_updater.py`; 38 tests; AOR engine wired Stage 9 |
| 14 | Meeting Ingest Linker | Second-wave | Connector Enrichment | BUILT — 2026-04-26; `runtime/workflows/meeting_ingest_linker.py`; wikilink + project + domain entity extraction; CGL check; 57 tests; live AOR run: 4 proposals from 5 entities |
| 15 | trace_idea | Second-wave | AOR Workflow | BUILT — prior session; `runtime/workflows/trace_idea.py`; manifest + role card + tests live |
| 16 | drift_scan | Second-wave | AOR Workflow | BUILT — 2026-04-25; `runtime/workflows/drift_scan.py`; 18-domain scan; manifest + role card; 59 tests |
| 17 | Paperclip | Later candidate | Orchestration Surface | RESERVED |

---

## Cross-Feature Dependency Map

```
First-Wave Foundation:
  Workflow Registry (1) â†â”€â”€ all workflows depend on this
  Agent Role Cards (2) â†â”€â”€ all workflows depend on this
  Task-Type Router (3) â†â”€â”€ all workflows depend on this
  Decision Ledger (4) â†â”€â”€ Feature Filter (5), Pivot Log (6) reference this
  Feature Filter (5) â”€â”€â†’ Feature-Fit-Register.md (Phase 8, already live)
  Project Pivot Log (6) â”€â”€â†’ references Decision Ledger (4)

  First-wave workflows:
  operator_today (7) â”€â”€â†’ depends on 1, 2, 3
  operator_close_day (8) â”€â”€â†’ depends on 1, 2, 3; pairs with operator_today (7)
  graph_hygiene (9) â”€â”€â†’ depends on 1, 2, 3; feeds graduate_ideas (10) candidates
  graduate_ideas (10) â”€â”€â†’ depends on 1, 2, 3; depends on AI-Generated-Output-Bridge (Phase 8)

Second-Wave:
  Provenance Schema (11) â”€â”€â†’ extends Phase 7 SIC schema + Phase 8 sidecar
  Context Governance Layer (12) â”€â”€â†’ depends on Provenance Schema (11), Role Cards (2)
  Agent Scorecards (13) â”€â”€â†’ depends on Role Cards (2), CGL (12), AOR execution history
  Meeting Ingest Linker (14) â”€â”€â†’ depends on Phase 8 capture, graph_hygiene (9), CGL (12)
  trace_idea (15) â”€â”€â†’ depends on Provenance Schema (11), graduate_ideas (10)
  drift_scan (16) â”€â”€â†’ depends on operator_close_day (8), Decision Ledger (4)

Later:
  Paperclip (17) â”€â”€â†’ depends on AOR fully operational; Gate API stable; Phase 10 GUI layer
```

---

*Phase9-Adopted-Feature-Specification.md â€” v1.1 â€” Updated: 2026-04-07 (truth-sync pass: all 10 first-wave feature status lines updated; Adoption Wave Summary corrected to match per-feature sections; created 2026-03-31)*
*Canonical specification for Phase 9 adopted features. Authoritative over ROADMAP.md summaries.*



*Graph links: [[Vault-Map]]*
