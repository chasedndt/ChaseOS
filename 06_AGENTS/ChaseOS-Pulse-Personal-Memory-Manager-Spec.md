# ChaseOS Pulse Personal Memory Manager Spec

**Status:** SPEC / IMPLEMENTATION-READY BOUNDARY CONTRACT  
**Date:** 2026-05-12  
**Runtime lane:** Hermes/Optimus PM  
**Phase:** Phase 10 Pulse / Studio surface over governed Personal Map memory  
**Scope:** Product spec, source-of-truth boundary, task split, and dependency routing only. This pass does not mutate protected identity/control documents and does not implement runtime code.

## Purpose

The Personal Memory Manager is the local ChaseOS UI that lets the operator import, edit, review, approve, reject, and apply personal memory while keeping ChaseOS governance intact.

It is not a hidden LLM memory store. It is an inspectable Personal Map management surface over explicit evidence, candidate logs, review decisions, and approved runtime-memory graph state.

The product goal is:

1. give the operator full visibility and control over personal context;
2. keep public/Core ChaseOS templates clean for GitHub/framework users;
3. keep private instance facts local to the operator;
4. preserve the authority boundary between identity docs, canonical OS docs, dashboards, runtime memory, and governed apply lanes.

## Live repo truth this spec depends on

Current inspected surfaces:

- `06_AGENTS/Personal-Map-Architecture.md` defines Personal Map purpose, node/edge schema, governance rules, candidate store path, and current implementation gaps.
- `SOUL.template.md` is a public framework template for new users to copy and populate.
- `SOUL.md` is Chase's populated private identity/voice/doctrine file and is not editable without explicit approval.
- `00_HOME/Operating-System.md` is the high-level personal OS/domain map and source of truth when priorities conflict.
- `00_HOME/Dashboard.md` is the control-tower/index surface.
- `00_HOME/Principles.md` is personal doctrine and decision rules.
- `runtime/memory/personal_map.py` contains partial Personal Map graph schema.
- `runtime/memory/candidate_store.py` persists pending-review Personal Map candidates under `07_LOGS/Pulse-Decks/memory-candidates/personal-map/` and explicitly blocks apply/canonical mutation.
- `runtime/pulse/personal_map_visualization.py` renders read-only declared/candidate Personal Map visualization and explicitly blocks apply/mutation authority.
- Existing Phase 10 Personal Map docs already define read-only visualization, review/apply visibility, live-apply proof, and transaction-proof layers.

## Source-of-truth boundary

| Surface | Role | Public/Core or Personal/private | UI behavior | Mutation rule |
|---|---|---|---|---|
| `SOUL.template.md` | Framework template for identity, voice, values, operating character, risk/decision posture, session protocol | Public/Core | Show as onboarding template and section guide | May be updated only as framework template work, not with private facts |
| `SOUL.md` | Private populated identity/voice/doctrine profile for this ChaseOS instance | Personal/private | Read as evidence only; propose candidate memories from it; show protected-file warning | Do not edit from Memory Manager; changes require explicit protected-doc approval outside this flow |
| `00_HOME/Operating-System.md` | Canonical personal OS/domain map: who the operator is, active domains, operating layers, priority conflict anchor | Personal/private instance truth | Read as high-authority evidence; map domains to Personal Map nodes; flag drift | Do not edit from Memory Manager; propose review candidates or separate protected-doc update requests |
| `00_HOME/Principles.md` | Personal doctrine and decision rules | Personal/private instance truth | Read as high-authority evidence for doctrine/value nodes | Do not edit from Memory Manager; doctrine changes require explicit approval |
| `00_HOME/Dashboard.md` | Control tower / index / launch surface | Instance navigation surface | Link to Memory Manager and show status summaries only | Dashboard link/status updates are a separate Studio/navigation task, not memory apply |
| `06_AGENTS/Personal-Map-Architecture.md` | Architecture/governance contract for Personal Map | Core architecture + instance-specific evolution notes | Display boundary rules and schema in UI help | Spec changes are docs work, not UI memory apply |
| `runtime/memory/personal-map/graph.json` | Applied runtime Personal Map graph after governed approval | Personal/private runtime memory | Primary applied-memory store shown by UI | Only written by explicit governed apply path after approved review decisions |
| `07_LOGS/Pulse-Decks/memory-candidates/personal-map/*.jsonl` | Pending Personal Map node/edge candidates | Personal/private audit log | Import/edit/review queue source | Append-only candidate log; not an approval or applied graph |
| `07_LOGS/Pulse-Decks/review-decisions/` and apply registry | Review/apply audit evidence | Personal/private audit log | Show reviewer decisions, transaction proofs, applied/already-applied status | Written only by review/apply flows with explicit operator decision |

### Boundary summary

- SOUL is identity/voice/character.
- Principles is doctrine and decision law.
- Operating-System is the canonical personal OS/domain map and conflict anchor.
- Dashboard is navigation/control tower.
- Personal Map is structured runtime memory derived from evidence and operator review.
- Candidate Store is pending proposals, not accepted truth.
- Applied graph is accepted runtime memory, not canonical knowledge and not a replacement for protected docs.

## Core/template behavior vs personal/private instance data

### Public GitHub/Core ChaseOS should include

- `SOUL.template.md` with generic placeholders and instructions.
- Generic onboarding questions and schema definitions.
- Personal Map schema, candidate store code, no-secret policy, and tests using synthetic sample data.
- Empty directory placeholders or documented generated paths for local candidate/review/apply logs.
- UI code that works without Chase's personal facts.
- Redaction/ignore lists and policy defaults.

### Public GitHub/Core ChaseOS must not include

- Chase's populated `SOUL.md` private facts in exported framework releases.
- Private Operating-System domain details unless intentionally sanitized into examples.
- Real candidate logs, review decisions, applied graph, trading/business/private project facts, credentials, tokens, session cookies, addresses, private IDs, or connector exports.
- Any default behavior that uploads, syncs, or promotes personal memory externally.

### Personal/private ChaseOS instance may contain

- Populated `SOUL.md`, `Operating-System.md`, `Principles.md`, active projects, private domains, and local logs.
- Local Personal Map candidates and applied runtime graph.
- Operator-confirmed imports from approved local sources.
- Evidence references to local vault paths or explicitly enabled connectors, not raw secrets.

## New-user onboarding: manual fill vs UI import/proposal

### New users manually fill first

A new ChaseOS user should manually fill or approve the first version of:

- name / preferred identity label;
- broad archetype or operating persona;
- top-level domains/projects;
- core principles/doctrine;
- communication style;
- hard constraints and risk posture;
- privacy preferences and redaction rules;
- which sources the Memory Manager is allowed to scan.

Manual fill is required because these fields define identity and governance. The UI may assist with prompts and examples, but it must not invent identity.

### UI may import/propose

After the user approves source access, the UI may propose candidates from:

- populated `SOUL.md` sections;
- `00_HOME/Operating-System.md` domain map;
- `00_HOME/Principles.md` doctrine sections;
- project OS files selected by the operator;
- daily/weekly/build logs selected by the operator;
- approved connector exports, when connector ingestion is separately enabled.

The UI may produce:

- candidate nodes;
- candidate edges;
- suggested tags;
- conflict/drift warnings;
- duplicate/merge suggestions;
- evidence-backed summary rewrites.

The UI must not auto-apply any of these proposals.

## Candidate/review/apply workflow

### 1. Source selection

The operator chooses import sources from an allowlisted set. The UI shows the exact files or connector exports to be scanned before import.

Required UI fields:

- source path/export ID;
- source trust tier;
- data class: identity, doctrine, domain, project, preference, habit, event, constraint, skill, cadence;
- whether source may create candidates, update pending candidates, or only be viewed;
- no-secret scan result.

### 2. Import to candidates

Importer creates Personal Map candidates, not accepted memory.

Each candidate must include:

- stable candidate ID;
- node or edge payload;
- source evidence reference;
- reason for proposal;
- confidence;
- data class;
- sensitivity classification;
- no-secret scan status;
- created timestamp;
- status `pending_review`;
- blocked effects matching current candidate store policy.

### 3. Review queue

The Memory Manager shows candidates grouped by:

- new node;
- new edge;
- update existing node;
- merge duplicate;
- conflict/drift warning;
- sensitive claim requiring extra review;
- blocked due to secret-like content.

Review controls:

- approve as-is;
- edit then approve;
- reject;
- defer;
- merge into existing node;
- mark as stale;
- escalate to protected-doc update request;
- open evidence source read-only.

### 4. Edit candidate

Editing happens on the candidate payload only. It does not edit `SOUL.md`, `Operating-System.md`, `Principles.md`, Dashboard, Project-OS files, or canonical knowledge.

Required edit behavior:

- diff before/after candidate payload;
- preserve original evidence;
- record editor/operator and timestamp where available;
- keep status history;
- rerun validation and no-secret scan;
- refuse save if candidate would contain blocked data.

### 5. Apply preview

Before live apply, UI shows transaction proof:

- target path: `runtime/memory/personal-map/graph.json`;
- graph before-state node/edge counts and hash;
- candidate IDs and review decision IDs;
- idempotency keys;
- planned node/edge additions/updates;
- blocked writes list;
- explicit statement that protected docs and canonical knowledge will not change.

### 6. Explicit apply

Apply requires an explicit operator action and must route through the governed apply lane. It writes accepted memory only to runtime Personal Map state plus audit/apply registry artifacts.

It must not:

- mutate protected identity/control docs;
- auto-promote to `02_KNOWLEDGE/`;
- update Now/project truth;
- dispatch runtimes;
- create tasks without separate operator approval;
- call external providers/connectors during apply;
- store secrets.

### 7. Post-apply inspection

After apply, UI shows:

- applied graph counts;
- accepted nodes/edges changed;
- review decisions consumed;
- already-applied/skipped entries;
- audit artifact paths;
- remaining pending/rejected/blocked candidates;
- drift warnings still unresolved.

## No-secret policy

The Memory Manager treats secrets as forbidden content, not as memories.

Blocked classes include:

- API keys, auth tokens, session cookies, private keys, seed phrases;
- passwords, recovery codes, MFA backup codes;
- bank/card/account numbers unless explicitly represented as redacted metadata;
- full addresses, phone numbers, government IDs, or private identifiers unless the user explicitly creates a redacted profile field;
- raw connector credential exports;
- anything matching configured secret scanners or operator redaction patterns.

Behavior:

- import scans must block or redact secret-like values before candidate persistence;
- blocked candidates must show reason and source path without exposing the secret value;
- apply must refuse candidates whose latest payload has not passed no-secret validation;
- UI must provide a local-only redaction editor for turning private raw text into safe summary context;
- audit logs record `blocked_secret_like_content: true` and scanner class, not secret payloads.

## Product UI requirements

### Main panels

1. Overview
   - applied graph status;
   - candidate counts by status/type/sensitivity;
   - source coverage;
   - no-secret gate status;
   - live apply readiness.

2. Source Import
   - select files/sources;
   - preview scan scope;
   - run dry-run extraction;
   - show proposed candidates before persistence where feasible;
   - write candidates only after operator confirmation.

3. Candidate Queue
   - filter/sort/search;
   - grouped review lanes;
   - bulk actions only for low-risk candidates and only after preview.

4. Candidate Editor
   - form and raw JSON view;
   - evidence drilldown;
   - diff preview;
   - validation/no-secret status;
   - save candidate revision.

5. Source-of-Truth Boundary
   - compare SOUL, Principles, Operating-System, Dashboard, Personal Map, Candidate Store, Applied Graph;
   - explain which surfaces are read-only/protected;
   - show drift/conflict warnings.

6. Apply Preview / Transaction Proof
   - ready approved candidates;
   - exact planned writes;
   - graph before-state hash;
   - idempotency;
   - explicit confirm control.

7. Applied Graph Inspector
   - node/edge browser;
   - evidence links;
   - history/status;
   - source file references;
   - export sanitized summary.

8. Policy / Redaction Settings
   - source allowlists;
   - ignored paths;
   - secret patterns;
   - data classes requiring extra review;
   - local-only/export-safe posture.

### Launcher/Studio integration

The Memory Manager should appear as a local Studio/Pulse app, not a general ambient write tool.

Integration requirements:

- registered in the Studio/Pulse app launcher with local-only authority text;
- linked from Pulse product shell memory/personal-map areas;
- dashboard status may link to the app but must not execute import/apply;
- CLI/API surface should support dry-run and JSON output for tests;
- browser/Studio surface must display blocked authority in the UI itself.

## Acceptance criteria

### Functional acceptance

- User can select approved local sources and dry-run import candidate memories.
- User can persist pending Personal Map node/edge candidates with evidence and no-secret scan metadata.
- User can inspect, edit, approve, reject, defer, merge, and escalate candidates.
- User can preview exact apply transaction before any live write.
- User can explicitly apply approved Personal Map candidates to `runtime/memory/personal-map/graph.json` through governed apply.
- User can inspect applied nodes/edges with evidence and history.
- User can see clear distinctions among SOUL, Principles, Operating-System, Dashboard, Candidate Store, and applied Personal Map.

### Governance acceptance

- No protected identity/control doc is mutated by Memory Manager import/edit/review/apply flows.
- `SOUL.md`, `00_HOME/Operating-System.md`, and `00_HOME/Principles.md` remain read-only evidence unless a separate explicit protected-doc workflow is approved.
- Public/Core templates do not receive private instance data.
- Candidate persistence remains pending-review by default.
- Apply is explicit, auditable, idempotent, and limited to runtime Personal Map state plus audit/apply artifacts.
- No canonical knowledge promotion occurs.
- No external provider/connector call occurs during apply.
- Secret-like values are blocked or redacted before candidate persistence and before apply.

### Test acceptance

- Unit tests cover schema validation, candidate edit revisioning, no-secret blocking, and idempotent apply.
- Integration tests prove protected docs are unchanged after import/edit/apply.
- UI/API tests prove default no-write/dry-run behavior.
- Launcher tests prove the app is registered with local-only/bounded authority text.
- Regression tests prove public template export excludes private Personal Map artifacts.
- Proof artifact records current graph counts/hash before and after test apply.

## Dependency routing and task split

Existing child tasks from this spec lane:

- `t_97c02c98` — ops: implement Personal Map applied persistence and import/edit/apply substrate.
- `t_0924515b` — pm: design GitHub-ready personal-instance templating and onboarding flow.

New child tasks created by this PM pass:

- `t_6a6b9865` — ops: build Studio/Pulse Personal Memory Manager UI over governed Personal Map lanes.
- `t_032e1f2b` — ops: QA Personal Memory Manager no-secret and source-of-truth boundaries.

Recommended execution order:

1. `t_0924515b` finalizes onboarding/template contract for public Core vs private instance.
2. `t_97c02c98` implements backend applied persistence and candidate import/edit/apply substrate.
3. `t_6a6b9865` builds the Studio/Pulse UI over the backend substrate and existing proof surfaces.
4. `t_032e1f2b` verifies no-secret, no-protected-doc-mutation, template/export, and UI authority boundaries.

Backend dependencies:

- applied graph persistence path and schema;
- candidate edit/revision model;
- candidate merge/update semantics;
- secret scanner/redaction helper;
- dry-run import API;
- apply transaction preview API;
- idempotent governed apply path.

Studio/Pulse dependencies:

- app launcher registration;
- local panel routing;
- evidence drilldown components;
- diff/JSON editor component;
- explicit confirmation control;
- visual display of source-of-truth boundary and blocked authority.

Approval gates:

- Any direct edit to `SOUL.md`, `00_HOME/Operating-System.md`, `00_HOME/Principles.md`, protected governance docs, or canonical knowledge requires a separate explicit approval workflow.
- Any connector import beyond local approved files requires connector-specific source authorization and no-secret proof.
- Any public/Core export must run private artifact exclusion tests before release.

## Definition of done for full Personal Memory Manager

The lane is complete when a local ChaseOS user can:

1. open the Memory Manager from Studio/Pulse;
2. import candidate memories from approved local sources;
3. review and edit candidates with evidence and redaction gates;
4. approve/reject/merge/escalate candidate changes;
5. preview exact apply transactions;
6. apply approved candidates to runtime Personal Map state only;
7. inspect the applied graph and audit trail;
8. prove via tests that no protected identity/control docs, public templates, canonical knowledge, or secrets were mutated/leaked.

Graph links: [[Personal-Map-Architecture]] · [[ChaseOS-Pulse-Personal-Map-Visualization-Contract]] · [[ChaseOS-Pulse-Personal-Map-Review-Apply-Surface]] · [[ChaseOS-Pulse-Personal-Map-Live-Apply-Proof]] · [[ChaseOS-Pulse-Personal-Map-Apply-Transaction-Proof]] · [[ChaseOS-Pulse-Governed-Feedback-Review-Apply-UI]] · [[ChaseOS-Studio-Architecture]] · [[ChaseOS-Approval-Center]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
