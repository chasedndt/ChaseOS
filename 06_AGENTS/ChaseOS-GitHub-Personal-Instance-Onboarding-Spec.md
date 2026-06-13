# ChaseOS GitHub Personal-Instance Onboarding Spec

**Status:** SPEC / IMPLEMENTATION PLAN  
**Date:** 2026-05-12  
**Runtime lane:** Hermes/Optimus PM  
**Phase:** Core/public template onboarding plus Personal/private instance bootstrap  
**Scope:** Documentation/spec and proposal only. This pass does not rewrite `SOUL.md`, `00_HOME/Operating-System.md`, `00_HOME/Dashboard.md`, `00_HOME/Principles.md`, or any private identity/control document.

## Purpose

This spec defines how a future GitHub/public ChaseOS release should let a new user create a clean private ChaseOS instance from public Core templates without inheriting Chase's personal context.

The onboarding goal is:

1. keep `chaseos-core` public, reusable, scanner-clean, and generic;
2. create a local private instance that the user owns and populates;
3. make `SOUL.template.md` the public identity template and `SOUL.md` the private populated identity file;
4. make `00_HOME/Operating-System.md` the canonical personal OS/domain map;
5. make `00_HOME/Dashboard.md` the control-tower/index surface, not memory truth;
6. make Personal Map the structured inspectable runtime profile graph generated through review/apply, not hidden model memory;
7. support both manual first-run setup and Memory Manager assisted import/proposal.

## Live repo truth this spec depends on

Inspected surfaces for this pass:

- `SOUL.template.md` already exists as the public identity-layer framework template.
- `SOUL.md` exists as the populated private identity/voice/doctrine instance file and is Core-excluded by `CORE_MANIFEST.md`.
- `00_HOME/Operating-System.md` is private personal instance truth and Core-excluded by `CORE_MANIFEST.md`.
- `00_HOME/Dashboard.md` is private dashboard/control-tower state and Core-excluded by `CORE_MANIFEST.md`.
- `core_templates/00_HOME/Operating-System.example.md` is a sanitized public example for the personal OS/domain-map shape.
- `core_export/templates/docs/framework-home/Dashboard.example.md` is a sanitized public example for the dashboard/control-tower shape.
- `06_AGENTS/Core-Personal-Split-Implementation-Plan.md` defines Core vs Personal as the active structural/export lane.
- `CORE_MANIFEST.md` defines Core-included and Core-excluded categories and blocks private identity/log/runtime state from public Core.
- `06_AGENTS/ChaseOS-Pulse-Personal-Memory-Manager-Spec.md` defines the Memory Manager source-of-truth boundary, candidate/review/apply flow, no-secret policy, and Personal Map apply behavior.
- `06_AGENTS/Personal-Map-Architecture.md` defines Personal Map as an inspectable evidence-linked user profile graph.

## Product model

ChaseOS should ship in two layers:

| Layer | What it is | Where it lives | Contains | Must not contain |
|---|---|---|---|---|
| Core/public template | Reusable GitHub/framework repository | `chaseos-core` or exported Core packet | Folder structure, docs, policies, templates, sanitized examples, generic runtime scaffolds, onboarding CLI/UI code | Private identity, projects, personal logs, candidate memory, applied Personal Map graph, credentials, connector exports |
| Personal/private instance | User's populated local ChaseOS vault/runtime | local clone / generated instance folder | User's `SOUL.md`, `Operating-System.md`, `Dashboard.md`, `Principles.md`, projects, logs, candidates, applied Personal Map graph | Public default assumptions copied from another user's life, unreviewed imported secrets, hidden memory writes |

The public repository is the seed. The personal instance is generated from that seed, then populated locally by the user.

## Source-of-truth decisions

### `SOUL.template.md` — public Core template

Role:
- reusable identity/voice/values/operating-character template;
- section guide for first-run onboarding;
- safe to ship in GitHub Core.

Rules:
- remains generic and placeholder-driven;
- may include examples only if they are synthetic and clearly marked;
- should explain that users copy or generate `SOUL.md` from it;
- must not contain Chase's populated identity, active projects, preferences, private risk posture, or personal constraints.

### `SOUL.md` — private populated identity instance

Role:
- user's populated identity, voice, values, operating character, communication style, and behavior constraints;
- high-sensitivity evidence source for Memory Manager candidate extraction;
- not the runtime memory graph itself.

Rules:
- generated locally from `SOUL.template.md` during first-run setup;
- ignored/excluded from public Core by default;
- never silently rewritten by onboarding or Memory Manager;
- may be read by an explicitly approved local import flow to propose Personal Map candidates;
- direct edits require user-controlled editing or a separate protected-doc approval flow.

### `00_HOME/Operating-System.md` — canonical personal OS/domain map

Role:
- authoritative map of the user's operating domains, active top-level systems, conflict anchors, and current strategic shape;
- canonical personal OS context used to interpret priorities and domain relationships.

Rules:
- generated locally from a sanitized example/template during onboarding;
- populated by the user before project/knowledge imports are treated as reliable;
- read as high-authority evidence for Personal Map domain/project nodes;
- not edited by Memory Manager apply;
- drift against Personal Map should create a review warning, not an automatic rewrite.

### `00_HOME/Dashboard.md` — control tower / index

Role:
- human-facing launch surface and status/control-tower index;
- links to Now, projects, logs, approvals, Memory Manager, runtime panels, and review queues;
- shows onboarding completion and Personal Map health/status summaries.

Rules:
- generated locally with generic sections and empty/default statuses;
- may link to onboarding and Memory Manager panels;
- should not be treated as canonical memory truth;
- status widgets are derived views, not accepted facts;
- write-capable dashboard edits belong to a separate Studio/navigation task, not memory apply.

### Personal Map — structured inspectable user profile graph

Role:
- evidence-linked runtime profile graph for user identity-adjacent operational context: domains, goals, projects, values, doctrine, habits, cadences, skills, constraints, preferences, commitments, and relevant events;
- Memory Manager managed graph state;
- input to ChaseOS Pulse and other local runtime personalization surfaces.

Rules:
- starts empty or with only user-approved seed nodes;
- candidates are generated from onboarding answers, selected docs, or imports;
- every accepted node/edge needs evidence, review decision, sensitivity class, no-secret status, and apply transaction proof;
- applied graph lives under private local runtime memory, e.g. `runtime/memory/personal-map/graph.json`;
- candidate logs and review/apply decisions remain private local audit artifacts;
- it is not canonical knowledge, not a replacement for protected docs, and not hidden LLM memory.

## What belongs in the repo template vs generated private instance

### Public GitHub/Core should include

Core files:
- `README.md` with public setup path and privacy warning;
- `FORKING.md` with Core-vs-Personal onboarding guidance;
- `CORE_MANIFEST.md` and `core_export/export_manifest.yaml` for export/allowlist truth;
- `SOUL.template.md`;
- `core_templates/00_HOME/Operating-System.example.md`;
- `core_export/templates/docs/framework-home/Dashboard.example.md` or a future `core_templates/00_HOME/Dashboard.example.md` mirror;
- `core_templates/00_HOME/HOME-Templates-Guide.md`;
- `06_AGENTS/Core-Personal-Split-Implementation-Plan.md`;
- `06_AGENTS/Personal-Map-Architecture.md` if sanitized/generic;
- `06_AGENTS/ChaseOS-Pulse-Personal-Memory-Manager-Spec.md` or a sanitized Core version if it remains framework-relevant;
- generic onboarding docs and checklists;
- Memory Manager UI/runtime code that can run against empty or synthetic local data;
- schema files for onboarding answers, Personal Map candidates, Personal Map graph, review decisions, and no-secret validation;
- tests using synthetic sample profiles only.

Core template/generated-stub files proposed:
- `core_templates/SOUL.template.md` or root `SOUL.template.md` as the authoritative source;
- `core_templates/00_HOME/Operating-System.template.md` for blank fill-in prompts;
- `core_templates/00_HOME/Operating-System.example.md` for synthetic example;
- `core_templates/00_HOME/Dashboard.template.md` for blank generated dashboard;
- `core_templates/00_HOME/Dashboard.example.md` for synthetic example;
- `core_templates/00_HOME/Principles.template.md` for doctrine prompts;
- `core_templates/runtime/memory/personal-map/graph.empty.json` for empty graph shape;
- `core_templates/runtime/memory/personal-map/schema.json` for graph validation;
- `core_templates/07_LOGS/Pulse-Decks/memory-candidates/personal-map/.gitkeep` or README-only placeholder;
- `core_templates/07_LOGS/Pulse-Decks/review-decisions/.gitkeep` or README-only placeholder;
- `core_templates/onboarding/first-run-questionnaire.yaml` for prompt definitions;
- `core_templates/onboarding/source-allowlist.example.yaml` for import-source configuration;
- `core_templates/onboarding/redaction-policy.example.yaml` for no-secret defaults.

### Public GitHub/Core must exclude

- populated `SOUL.md`;
- populated `00_HOME/Operating-System.md`;
- populated `00_HOME/Dashboard.md`;
- populated `00_HOME/Principles.md`;
- real `00_HOME/Now.md`;
- real project OS files;
- real knowledge notes;
- real logs, build logs, operator briefs, Agent-Activity records, approvals, and review decisions;
- real Personal Map candidate logs;
- real Personal Map applied graph;
- connector exports, account maps, provider configs, cookies, tokens, private IDs, local paths containing private context;
- any generated memory or runtime state derived from the operator.

### Generated private local instance should contain

At first run, the local bootstrap may create:

- `SOUL.md` from `SOUL.template.md` plus user answers;
- `00_HOME/Operating-System.md` from template/example plus user domain map;
- `00_HOME/Dashboard.md` from dashboard template plus local links/status placeholders;
- `00_HOME/Principles.md` from doctrine prompts if the user opts in;
- `runtime/memory/personal-map/graph.json` as an empty or seed-approved graph;
- `07_LOGS/Pulse-Decks/memory-candidates/personal-map/` for candidate logs;
- `07_LOGS/Pulse-Decks/review-decisions/` for review/apply decisions;
- `.gitignore` or local ignore entries for all private populated files and runtime state if the user is working in a template-derived repo;
- onboarding receipt/audit file recording what was generated without storing secrets.

Private generated files should be local-first and should not be committed to the public Core repository unless intentionally sanitized into templates/examples.

## First-run/bootstrap architecture

### Stage 0 — Preflight

The bootstrapper checks:

- repository is Core/template mode or local instance mode;
- no populated private files will be overwritten without explicit confirmation;
- `.gitignore` or equivalent private-state guard exists;
- Core templates are present;
- no source import is enabled by default;
- no external connector or cloud sync is required for onboarding.

If private files already exist, bootstrap switches to repair/continue mode and shows a diff/skip plan instead of overwriting.

### Stage 1 — Choose onboarding mode

The user chooses one of three paths:

1. **Manual-first minimal:** create blank/private docs from templates and let the user fill them in an editor.
2. **Guided questionnaire:** ask structured questions and render initial private docs from answers.
3. **Import-assisted:** after manual consent, scan selected local files or exports and create Personal Map candidates for review.

Default should be Manual-first minimal plus optional guided questionnaire. Import-assisted is opt-in only.

### Stage 2 — Identity and doctrine prompts

Required/strongly recommended prompts:

- preferred name / identity label;
- operating archetype or self-description;
- communication style;
- values/principles the system should respect;
- hard constraints and never-do rules;
- risk posture: privacy, finance, technical automation, scope, reputation;
- agent decision posture: when to ask, when to act, when to refuse;
- privacy boundaries and redaction preferences.

Output:
- `SOUL.md` draft;
- optional `00_HOME/Principles.md` draft;
- Personal Map candidates for `person`, `value`, `doctrine`, `preference`, and `constraint` nodes, only if the user opts into candidate generation.

### Stage 3 — Personal OS/domain map prompts

Required prompts:

- top-level life/work domains;
- active projects per domain;
- current phase of the system;
- which domains are active now vs parked;
- priority/conflict rules between domains;
- review cadence;
- which docs are canonical for current focus.

Output:
- `00_HOME/Operating-System.md` draft;
- Personal Map candidates for `domain`, `project`, `goal`, `commitment`, and `cadence` nodes;
- Dashboard section seeds.

### Stage 4 — Dashboard/control-tower generation

The bootstrapper generates a dashboard shell with:

- links to `Now.md`, Operating System, Principles, SOUL, projects, logs, approvals, Memory Manager, and runtime panels where present;
- onboarding completion checklist;
- Personal Map status widget placeholder;
- review queue links;
- empty attention queue;
- clear labels that dashboard summaries are status views, not source-of-truth memory.

Output:
- `00_HOME/Dashboard.md` draft or update proposal;
- no Personal Map apply by default.

### Stage 5 — Personal Map seed proposal

If enabled, bootstrap creates Personal Map candidates from the user's own answers, not accepted graph entries.

Each candidate includes:

- candidate ID;
- node/edge payload;
- source evidence reference such as `onboarding://questionnaire/<section>` or local file path;
- data class;
- sensitivity class;
- confidence;
- no-secret scan result;
- blocked effects list;
- status `pending_review`.

The user reviews candidates in Memory Manager before apply. Applying writes only to `runtime/memory/personal-map/graph.json` plus review/apply audit artifacts.

### Stage 6 — Optional import-assisted enrichment

After the baseline docs exist, Memory Manager may offer imports from:

- the newly created `SOUL.md`;
- `00_HOME/Operating-System.md`;
- `00_HOME/Principles.md`;
- selected project OS files;
- selected local logs;
- approved connector exports if a separate connector setup exists.

Import rules:
- exact sources are shown before scan;
- source access is opt-in and revocable;
- import writes candidates only;
- no-secret scanner runs before persistence;
- blocked secret-like findings show class/reason but not raw secret values;
- apply requires explicit review and transaction preview.

## Proposed implementation stages

### Stage A — Template inventory and file contract

Deliverables:
- finalize public/private file matrix in `CORE_MANIFEST.md` or a linked onboarding contract;
- add blank `Operating-System.template.md`, `Dashboard.template.md`, and `Principles.template.md` if not already present;
- decide whether Dashboard examples live under `core_templates/00_HOME/` in addition to `core_export/templates/docs/framework-home/`;
- add ignore rules for generated private local instance state.

Acceptance:
- every onboarding-created file has a source template and a public/private classification;
- no populated personal file is required to run Core onboarding tests;
- Core export scanner has explicit allowlist/denylist coverage for onboarding files.

### Stage B — First-run questionnaire schema

Deliverables:
- `onboarding/first-run-questionnaire.yaml` or equivalent schema;
- renderer mapping questionnaire answers to `SOUL.md`, `Operating-System.md`, `Dashboard.md`, and optional `Principles.md`;
- validation for required answers and redaction preferences.

Acceptance:
- questionnaire can run without external providers/connectors;
- blank/manual mode is supported;
- generated docs include placeholders when the user skips optional answers;
- rerun does not overwrite populated files without confirmation.

### Stage C — Private instance generator

Deliverables:
- CLI or Studio flow such as `chaseos init-personal` / Studio Onboarding panel;
- preflight/diff/skip behavior;
- generated local folder/file set;
- onboarding receipt/audit artifact.

Acceptance:
- fresh Core checkout can create a private instance scaffold;
- existing local instance can be detected and continued safely;
- generated files are local/private by policy;
- no secrets or connector data are requested in first-run default path.

### Stage D — Personal Map candidate seeding

Deliverables:
- candidate generation from questionnaire answers;
- candidate store integration;
- Memory Manager review queue display;
- no-secret validation before candidate persistence.

Acceptance:
- no Personal Map graph mutation happens during initial candidate generation;
- candidates are inspectable and evidence-linked;
- apply preview names `runtime/memory/personal-map/graph.json` as the only memory graph target;
- protected docs are listed as blocked writes in apply preview.

### Stage E — Import-assisted Memory Manager flow

Deliverables:
- source-selection UI;
- local file scan/import candidate creator;
- review/edit/reject/approve controls;
- apply transaction proof;
- post-apply inspection.

Acceptance:
- import from `SOUL.md` or `Operating-System.md` creates candidates only;
- no silent protected-doc rewrite exists;
- no hidden memory store exists;
- review/apply decisions are auditable;
- secret-like content is blocked/redacted before persistence.

### Stage F — Core export/publication gate

Deliverables:
- scanner tests for onboarding templates and examples;
- Core export dry-run includes only public-safe onboarding files;
- manual review artifact for any mixed-layer doc;
- GitHub readiness checklist.

Acceptance:
- public packet includes templates, examples, schema, tests, and docs only;
- public packet excludes populated local instance files and runtime memory;
- scanner report has zero blockers;
- manual review explicitly approves the onboarding packet before Git/publication.

## New-user onboarding acceptance criteria

A GitHub/public user onboarding flow is acceptable when all of the following are true:

1. A fresh user can clone/export Core and understand that Core is not a populated personal OS.
2. `SOUL.template.md` is present and clearly marked as the source for private `SOUL.md`.
3. First-run setup can generate or guide creation of private `SOUL.md` without pulling in Chase's populated `SOUL.md`.
4. First-run setup can generate or guide creation of private `00_HOME/Operating-System.md` as the canonical personal OS/domain map.
5. First-run setup can generate or guide creation of private `00_HOME/Dashboard.md` as a control-tower/index surface.
6. The Dashboard links to Memory Manager/review state but does not become the source of memory truth.
7. Personal Map starts empty or candidate-only until the user explicitly reviews and applies nodes/edges.
8. Memory Manager imports from SOUL/Operating-System/Principles create candidates only, not direct protected-doc edits or accepted graph entries.
9. Every Personal Map candidate has evidence, sensitivity classification, no-secret status, and review status.
10. Apply requires explicit user confirmation and writes only to applied graph/audit artifacts, not protected identity/control docs.
11. Core templates/examples use synthetic or placeholder data only.
12. Public export excludes populated private files, runtime memory, logs, connector exports, credentials, and account-specific state.
13. Existing local instances are not overwritten during bootstrap without explicit diff/confirmation.
14. No external connector, cloud account, LLM provider, or credential is required for manual-first onboarding.
15. Import-assisted onboarding is opt-in and source-scoped.
16. No-secret scanning blocks or redacts secret-like content before candidate persistence.
17. Review/apply audit artifacts are local/private and inspectable.
18. The implementation has tests for template rendering, public/private path classification, no-overwrite behavior, candidate-only import, no-secret blocking, and Core export exclusion.
19. The user can rerun onboarding in repair/continue mode without losing private context.
20. The flow preserves ChaseOS OS alignment: Core provides reusable operating-system structure; the private instance becomes the user's actual operating system only after the user populates identity, domain map, dashboard, and reviewed memory.

## Open implementation decisions

These should be resolved before coding the generator:

1. Should `00_HOME/Operating-System.template.md` and `00_HOME/Dashboard.template.md` live directly under `core_templates/00_HOME/`, `05_TEMPLATES/`, or both?
2. Should `SOUL.template.md` remain root-only, be mirrored under `core_templates/`, or be copied into Core root during export?
3. Should first-run onboarding be a CLI-first flow, Studio-first flow, or CLI with Studio wrapper?
4. Should generated private files be created inside the same clone, a sibling `chaseos-personal` folder, or a user-selected vault path?
5. What exact `.gitignore`/export-deny rules should protect private generated instance files in a GitHub-template workflow?
6. Which no-secret scanner should be the required baseline for local candidate persistence and Core export verification?

## Recommended next tasks

1. Create the missing blank templates under `core_templates/00_HOME/`:
   - `Operating-System.template.md`
   - `Dashboard.template.md`
   - `Principles.template.md`
2. Add an onboarding schema under `core_templates/onboarding/`.
3. Add public/private onboarding path rules to the Core export allowlist/denylist.
4. Build a dry-run generator that prints the proposed file plan before writing.
5. Route the resulting implementation through governance/privacy review before public GitHub publication.

## Non-goals

- No direct rewrite of the current user's `SOUL.md`.
- No direct rewrite of the current user's `00_HOME/Operating-System.md`.
- No direct rewrite of the current user's `00_HOME/Dashboard.md`.
- No canonical knowledge promotion.
- No connector ingestion in default onboarding.
- No hidden agent/model memory.
- No GitHub publication decision in this spec.
- No framework export expansion beyond the long-term Core/public lane already defined by `CORE_MANIFEST.md`.

---

*Graph links: [[SOUL.template]] · [[CORE_MANIFEST]] · [[FORKING]] · [[Core-Personal-Split-Implementation-Plan]] · [[ChaseOS-Pulse-Personal-Memory-Manager-Spec]] · [[Personal-Map-Architecture]] · [[Operating-System]] · [[Dashboard]] · [[Hermes-Runtime-Profile]] · [[HERMES]] · [[Agent-Activity-Index]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
