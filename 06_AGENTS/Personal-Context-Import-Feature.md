---
type: feature-contract
title: Personal Context Import Feature
status: READY_FOR_MANUAL_TESTING / 100_PERCENT_IMPLEMENTED_FOR_LOCAL_MANUAL_TEST / LIVE WRITES STILL GATED
updated: 2026-05-21
runtime_surface: ChaseOS Studio
workspace_mode: personal_os
---

# Personal Context Import Feature

> Studio feature contract for importing personal context memory into a personal ChaseOS instance without allowing raw memory exports to rewrite canonical state.

## Current Truth

Status: READY_FOR_MANUAL_TESTING / 100_PERCENT_IMPLEMENTED_FOR_LOCAL_MANUAL_TEST / LIVE WRITES STILL GATED

All 9 original passes and the later full-surface wiring are complete for the local manual test lane. The operator can run the full personal context import loop using ChaseOS Studio or CLI commands and see: imported context routing, canonical routes written through approved executors, Personal Map entries applied or staged through approved executors, runtime memory changes through approved executors, Agent Bus dispatch packet preview, provider execution result or exact no-secret blocker, evidence files, rollback records, and exact-once markers.

2026-05-21 reconciliation note: the feature family inventory treats registry-only/provider/runtime-memory/personal-map readiness flags as capability rows, not broad authority grants. No Personal Context Import surface has ambient live writes, raw full-memory injection, unapproved runtime dispatch, unapproved provider calls, credential reads, graph writes, or unrestricted canonical mutation.

Implemented now:

- Read-only backend planner: `runtime/studio/personal_context_import.py`.
- StudioAPI read surface: `get_personal_context_import_panel`.
- Native shell panel registry entry: `context-import`.
- Native shell frontend panel: Context Import.
- Settings panel summary and detailed import posture.
- Dashboard payload field: `personal_context_import_panel`.
- Digest-gated preview writer: `runtime/studio/personal_context_import_preview_writer.py`.
- StudioAPI preview/approval methods: `get_personal_context_import_preview_writer` and `request_personal_context_import_preview`.
- Approval queue artifact path through `runtime/studio/approvals/` plus audit records under `runtime/studio/approvals/personal-context-import/`.
- Ambient `StudioService.execute_approved` block for personal context import preview approvals.
- Approved preview execution proof: `runtime/studio/personal_context_import_approved_preview_execution_proof.py`.
- StudioAPI approved-preview methods: `get_personal_context_import_approved_preview_execution_proof` and `execute_personal_context_import_approved_preview_execution`.
- Exact-once execution markers under `runtime/studio/approvals/personal-context-import/_execution_markers/`.
- Review artifact writes under `03_INPUTS/Personal-Context-Intake/`, `07_LOGS/Pulse-Decks/memory-candidates/personal-map/`, and `runtime/studio/context-import/`.
- Multi-instance fixture harness: `runtime/studio/personal_context_import_multi_instance_fixture_harness.py`.
- StudioAPI fixture method: `get_personal_context_import_multi_instance_fixture_harness`.
- Temp-only anonymized fixture proof that runs multiple context shapes through the preview writer and approved-preview execution proof while checking parent/child rule coverage, secret blocking, source-digest gating, artifact boundaries, and canonical-write blocking.
- Runtime-consumption readiness: `runtime/studio/personal_context_import_runtime_consumption_readiness.py`.
- StudioAPI runtime readiness method: `get_personal_context_import_runtime_consumption_readiness`.
- Bounded runtime reference packet preview that reads Personal Operator Context plus WML `personal_os`, returns scoped path/trust references only, and excludes raw source text/full-memory payloads.
- Canonical-promotion approval preview: `runtime/studio/personal_context_import_canonical_promotion_approval_preview.py`.
- StudioAPI canonical-promotion methods: `get_personal_context_import_canonical_promotion_approval_preview` and `request_personal_context_import_canonical_promotion_approval`.
- Canonical-promotion approved executor: `runtime/studio/personal_context_import_canonical_promotion_approved_executor.py`.
- StudioAPI canonical-promotion executor methods: `get_personal_context_import_canonical_promotion_approved_executor` and `execute_personal_context_import_canonical_promotion_approved_executor`.
- Digest-gated canonical route block writer for Dashboard, Personal Operator Index, Operating System, Projects Hub, Knowledge Index, Personal Domains Index, and Personal Context Intake Index after approval id, exact digest, operator statement, protected-target flag, and `execute=True`.
- Personal Map apply readiness: `runtime/studio/personal_context_import_personal_map_apply_readiness.py`.
- Personal Map approved apply executor: `runtime/studio/personal_context_import_personal_map_approved_apply_executor.py`.
- Exact-once Personal Map apply with markers under `runtime/studio/approvals/personal-context-import/_personal_map_apply_markers/`.
- Evidence and rollback plan under `runtime/studio/context-import/personal-map-apply-executions/`.
- Runtime memory mutation readiness: `runtime/studio/personal_context_import_runtime_memory_mutation_readiness.py`.
- Runtime memory approved mutation executor: `runtime/studio/personal_context_import_runtime_memory_approved_mutation_executor.py`.
- Exact-once nav-map personal context route appends for codex, hermes, chaser_agent.
- Markers under `runtime/studio/approvals/personal-context-import/_runtime_memory_mutation_markers/`.
- Agent Bus dispatch packet preview: `runtime/studio/personal_context_import_agent_bus_dispatch_packet.py`.
- Bounded reference-only packet preview (no Bus task write; preview-only surface with full gate requirements).
- Provider credential readiness: `runtime/studio/personal_context_import_provider_credential_readiness.py`.
- Checks OPENAI_API_KEY presence only — never reads or logs the value.
- Provider execution proof: `runtime/studio/personal_context_import_provider_execution_proof.py`.
- Shows exact call structure preview; executes minimal proof call if key present and execute=True with approved statement; returns exact unblock packet if key absent.
- End-to-end manual test orchestrator: `runtime/studio/personal_context_import_end_to_end_real_world_manual_test.py`.
- Runs all 8 lanes read-only and produces a comprehensive status report with lane-by-lane results, operator-owned blockers, code blockers, and manual-test step instructions.
- Ambient `StudioService.execute_approved` blocks for personal_map_apply_readiness_approval, runtime_memory_mutation_readiness_approval, and provider_credential_readiness_approval.

Governance boundary maintained:

- No automatic markdown node creation outside approved executors.
- No automatic index/dashboard/project hub mutation outside the approved canonical-promotion executor.
- All writes use exact digest, exact-once markers, approval_id, operator statement.
- No raw source text in any approval packet or reference packet.
- No credential value reads or logs.
- No canonical writeback from any surface that does not have a specific executor.

## Approved Preview Writer Contract

The approved preview writer is built, but it is not the live importer.

Implemented surface:

- `runtime.studio.personal_context_import_preview_writer.build_personal_context_import_preview_writer`.

Behavior:

- Reads operator-provided source text in memory.
- Screens for secret-like values and blocks if any are found.
- Produces a deterministic source digest, route proposal, parent/child node proposal set, edge proposal set, index patch plan, and future artifact plan.
- Requires the exact `import_preview_digest` before it queues an approval packet.
- Queues only a Studio approval artifact and a small audit record.
- Does not store the raw source text inside the approval packet.
- Does not write raw intake markdown, source digest markdown, node coverage audits, index patches, Dashboard routes, project routes, knowledge routes, Personal Map candidates, runtime memory, Agent Bus tasks, or canonical state.

Approved executor requirement:

- The approved preview execution proof must receive the matching source text again, verify it against the stored source digest, reserve an exact-once marker before writes, and then write only the reviewed preview artifacts authorized by the approval packet.
- It may write Tier 4 raw intake, source digest, node coverage audit, index patch preview, Personal Map candidate log/review deck, approval preview packet, execution evidence, rollback plan, and artifact manifest.
- It must not write canonical markdown nodes, Dashboard routes, Personal Operator Index routes, Projects Hub routes, Knowledge Index routes, runtime memory, provider calls, Agent Bus tasks, or Personal Map apply records.

## Approved Preview Execution Proof Contract

Implemented surface:

- `runtime.studio.personal_context_import_approved_preview_execution_proof.execute_personal_context_import_approved_preview_execution_proof`.

Behavior:

- Consumes one personal-context preview approval request produced by the preview writer.
- Requires approval id, exact `import_preview_digest`, matching source text, an operator approval statement containing the digest, and `execute=True`.
- Verifies the approval packet metadata, proposal digest, source digest, target paths, and effect flags before any artifact write.
- Blocks secret-like source text before writing raw intake.
- Reserves an exact-once marker before artifacts are written.
- Mutates the approval record through `approved/executing/executed` and stamps executor proof metadata back onto the approval.
- Writes only review artifacts and proof files:
  - `03_INPUTS/Personal-Context-Intake/YYYY-MM-DD_personal-context-source.md`
  - `03_INPUTS/Personal-Context-Intake/YYYY-MM-DD_personal-context-source-digest.md`
  - `03_INPUTS/Personal-Context-Intake/YYYY-MM-DD_personal-context-node-coverage-audit.md`
  - `03_INPUTS/Personal-Context-Intake/YYYY-MM-DD_personal-context-index-patch-preview.md`
  - `07_LOGS/Pulse-Decks/memory-candidates/personal-map/YYYY-MM-DD-personal-context-candidates.jsonl`
  - `07_LOGS/Pulse-Decks/memory-candidates/personal-map/YYYY-MM-DD-personal-context-candidates-review.md`
  - `runtime/studio/context-import/previews/<proposal>.json`
  - `runtime/studio/context-import/execution-proofs/<approval>/`

Still blocked:

- Canonical node creation, Dashboard edits, Personal Operator Index edits, Operating System edits, Projects Hub edits, Knowledge Index edits, root Knowledge Index rewrites, Personal Map apply, runtime memory mutation, Agent Bus task writes, runtime dispatch, and provider calls.

## Multi-Instance Fixture Harness Contract

Implemented surface:

- `runtime.studio.personal_context_import_multi_instance_fixture_harness.build_personal_context_import_multi_instance_fixture_harness`.

Behavior:

- Runs anonymized positive fixture packets across technical-founder/student, creator/fitness/commerce, and markets/security/hardware context shapes.
- Runs a negative secret-like fixture and verifies the preview writer blocks it before any approval request is created.
- Uses isolated fixture vaults only. By default, generated fixture artifacts are placed under the system temp root and cleaned up after the run.
- Exercises both the digest-gated preview writer and the approved-preview execution proof for each positive fixture.
- Verifies required rule coverage for parent/child nodes including Mandarin/HSK 1, prompt engineering, agent engineering, runtime engineering, RAG/MCP/source intelligence, University modules, content creation/YouTube monetization, fitness, interests, piano, geopolitics/history, networking, hardware/robotics, trading, cybersecurity, full-stack/software engineering, ChaseOS architecture, and Personal Map candidates.
- Verifies fixture execution writes only raw/review/proof artifacts and does not create `00_HOME/`, `01_PROJECTS/`, `02_KNOWLEDGE/`, or `06_AGENTS/` canonical targets.
- Returns digests, counts, rule ids, blockers, and boundary proof only; it does not return the raw fixture source text.

Still blocked:

- Live-vault context import writes, canonical markdown node creation, index/dashboard/project hub mutation, Personal Map apply, runtime memory mutation, Agent Bus task writes, runtime dispatch, provider calls, and credential reads.

## Runtime Consumption Readiness Contract

Implemented surface:

- `runtime.studio.personal_context_import_runtime_consumption_readiness.build_personal_context_import_runtime_consumption_readiness`.

Behavior:

- Reads the Personal Operator Context read model and `00_HOME/.workspace-mode.yaml`.
- Builds a `personal_context_runtime_reference_packet.v1` preview for `personal_os`.
- Includes reference ids, paths, group labels, statuses, trust/review posture, and source boundaries only.
- Does not include raw source text, raw context bodies, full-memory dumps, credential values, or secret values.
- Shows which consumer classes may later receive references: Codex, Hermes, OpenClaw, and Phase 11 Chat/Studio.
- Keeps future Agent Bus task creation, runtime dispatch, provider delivery, runtime memory mutation, Personal Map apply, and canonical writes blocked.

Still blocked:

- Raw full-memory injection, live Agent Bus task write, runtime dispatch, provider/model call, runtime memory mutation, Personal Map apply, canonical markdown node creation, Dashboard/Personal Operator/Projects Hub/Knowledge Index edits, credential reads, and secret reads.

## Canonical Promotion Approval Preview Contract

Implemented surface:

- `runtime.studio.personal_context_import_canonical_promotion_approval_preview.build_personal_context_import_canonical_promotion_approval_preview`.

Behavior:

- Reads the runtime-consumption reference packet and builds a target plan for Dashboard, Personal Operator Index, Operating System, Projects Hub, Knowledge Index, Personal Domains Index, and Personal Context Intake Index.
- Computes a `canonical_promotion_digest`.
- Can queue a pending approval only when the operator supplies the exact digest.
- Stores a review packet and audit record only; it does not write canonical target files.
- Ambient `StudioService.execute_approved()` is blocked for these approvals; only the governed canonical-promotion executor may consume them.

Still blocked:

- Canonical markdown node/index writes, Personal Map apply, runtime memory mutation, Agent Bus dispatch, provider/model call, credential read, secret read, and raw full-memory injection.

## Canonical Promotion Approved Executor Contract

Implemented surface:

- `runtime.studio.personal_context_import_canonical_promotion_approved_executor.execute_personal_context_import_canonical_promotion_approved_executor`.

Behavior:

- Consumes one canonical-promotion approval request produced by the approval preview.
- Requires approval id, exact `canonical_promotion_digest`, an operator approval statement containing the digest, `execute=True`, and an explicit protected-target flag for `00_HOME/Operating-System.md`.
- Verifies approval metadata, packet schema, target paths, digest match, source-text exclusion, raw full-memory exclusion, and effect flags before writing any canonical target.
- Reserves an exact-once marker under `runtime/studio/approvals/personal-context-import/_canonical_promotion_markers/` before canonical writes.
- Appends managed route blocks to Dashboard, Personal Operator Index, Operating System, Projects Hub, Knowledge Index, Personal Domains Index, and Personal Context Intake Index.
- Writes execution evidence, target manifest, rollback snapshots, and an Agent Activity audit record.
- Mutates the approval record through `approved/executing/executed` and stamps executor metadata back onto the approval.

Still blocked:

- Personal Map apply, runtime memory mutation, Agent Bus dispatch, provider/model call, credential read, secret read, raw full-memory injection, arbitrary canonical rewrites, and generated node body creation.

## Purpose

This feature is the governed intake lane for personal context memory exports such as ChatGPT profile/context handovers, operator-written life context, project history, learning context, goals, preferences, skills, doctrines, interests, language goals, fitness/combat context, and future personal domains.

The feature must make imports usable for real-world agent work by proposing the right parent nodes, child nodes, graph links, and runtime-facing read models while preserving ChaseOS trust discipline.

## Studio Entry Points

Primary entry point:

- Settings - operator-facing import posture, storage policy, and blocked writer status.

Additional required surfaces:

- Context Import panel - dedicated parent/child routing, Knowledge Index resolution, storage/security posture, and next-pass readiness.
- Dashboard - top-level personal-instance readiness.
- Personal Operator Context - current grouped read model for the user's personal instance.
- Runtime Memory Inspector - review how runtime memory can consume approved personal context without direct apply.
- Workspace Mode Layer - route imports through `personal_os` context before runtime use.
- Graph / Node Inspector - inspect proposed nodes and edges before any approved write.
- Approval Center - future lane for raw intake writes, canonical edits, Personal Map candidates, and apply decisions.

## Import Pipeline

1. Capture raw context export.
   - Store as Tier 4 raw input under `03_INPUTS/Personal-Context-Intake/`.
   - Preserve source provenance and date.
   - Do not treat raw export as canonical memory.

2. Normalize, redact, and screen.
   - Remove or block secrets, credentials, wallet keys, exchange keys, API keys, passwords, webhook URLs, token values, and sensitive account identifiers.
   - Produce a source-derived digest with explicit trust posture.

3. Extract parent nodes, child nodes, and graph edges.
   - Parent nodes include SOUL, Principles, Operating System, Personal Domains, Projects Hub, Knowledge Index - Master, and Personal Map candidate lanes.
   - Child nodes include domain-specific project, knowledge, language, fitness, interest, module, runtime, and creator/business nodes.
   - Every proposed edge needs an explainable source or operator statement.

4. Route approved context to the personal instance.
   - Dashboard and Personal Operator Index should expose the import results.
   - `01_PROJECTS/Projects-Hub.md` should route project operating files.
   - `02_KNOWLEDGE/Knowledge-Index.md` remains the canonical knowledge taxonomy.
   - `KNOWLEDGE-INDEX.md` remains a root compatibility shim only.

5. Stage Personal Map candidates.
   - Candidate records belong under `07_LOGS/Pulse-Decks/memory-candidates/personal-map/`.
   - Candidates remain review/apply-gated and are not live Personal Map memory.

6. Refresh runtime-facing read models.
   - Runtime agents consume bounded context references through Personal Operator Context and Workspace Mode.
   - Agent Bus tasks should receive scoped references, not raw full-memory dumps.

## Parent / Child Routing Requirements

Identity and doctrine:

- Parent: `SOUL.md`, `00_HOME/Principles.md`, `02_KNOWLEDGE/Doctrine/Doctrine-Philosophy.md`.
- Children: values, identity statements, discipline, decision rules, agent behavior preferences.

Personal domains:

- Parent: `00_HOME/Operating-System.md` and `00_HOME/Personal-Domains/Personal-Domains-Index.md`.
- Children: fitness/combat/physical discipline, interests/knowledge domains, language learning/global mobility, networking/social capital, hardware/systems/future robotics, and future accepted personal domains.

Projects:

- Parent: `01_PROJECTS/Projects-Hub.md`.
- Children: active projects, paused projects, creator/business lanes, University modules, and module-to-project bridges.

Knowledge:

- Parent: `02_KNOWLEDGE/Knowledge-Index.md`.
- Children: AI/agent engineering, runtime ops, full-stack, computer science, mathematics, cybersecurity, trading systems, content distribution, platform strategy, doctrine, fitness, networking, language, hardware.

Personal Map:

- Parent: `06_AGENTS/Personal-Map-Architecture.md`.
- Children: profile node candidates, profile edge candidates, review decks, apply proofs.

## Storage and Security Policy

- Raw context exports stay in `03_INPUTS/Personal-Context-Intake/`.
- Review maps and coverage audits stay in `03_INPUTS/Personal-Context-Intake/`.
- Personal Map candidates stay in `07_LOGS/Pulse-Decks/memory-candidates/personal-map/`.
- Canonical targets under `00_HOME/`, `01_PROJECTS/`, `02_KNOWLEDGE/`, and `06_AGENTS/` require explicit review or an approved writer.
- Populated personal context stays private. Public/core export must use templates, examples, or redacted summaries.
- The importer must not store credential values, wallet keys, exchange keys, API keys, passwords, seed phrases, tokens, webhook URLs, or secret account identifiers.

## Runtime Context Contract

Workspace Mode target: `personal_os`.

Runtime read model:

- `runtime.studio.personal_operator_context_index.build_personal_operator_context_index`.
- `runtime.studio.personal_context_import_runtime_consumption_readiness.build_personal_context_import_runtime_consumption_readiness`.

Runtime rules:

- Runtimes may read approved context routes.
- Runtimes must not infer permission from context availability.
- WML supplies mode-aware routing context; it does not grant execution authority.
- Personal Map candidates must be reviewed/applied before being treated as runtime memory.
- Raw context exports should not be injected wholesale into tasks.
- Agent Bus/runtime packets must carry scoped references only until a separate approved dispatch/executor exists.

## Future Test Strategy

- Extend the fixture harness with additional anonymized personal-context instances as new domains appear.
- Assert parent nodes, child nodes, graph links, Dashboard, Projects Hub, Personal Operator Index, and Knowledge Index routes remain proposed.
- Assert root `KNOWLEDGE-INDEX.md` remains a routing shim and `02_KNOWLEDGE/Knowledge-Index.md` remains canonical.
- Assert secrets are blocked and raw inputs remain Tier 4.
- Assert generated candidates remain candidate/review/apply-gated.
- Assert agent runtimes can consume the read model as bounded references without raw source text, provider calls, Agent Bus writes, canonical mutation, or memory apply.

## Next Verification / Product Pass

The implementation lane is local-manual-test ready. The next pass should be verification/productization, not broad new authority:

- run the full local manual test loop against an operator-approved test input;
- verify exact-once markers, rollback records, and no-secret/provider boundary behavior;
- keep Personal Map apply, runtime memory mutation, Agent Bus dispatch, provider execution, and canonical promotion limited to their specific approved executors;
- clean Studio copy so the page reads as Context Import, not implementation passes.

*Graph links: [[00_HOME/Personal-Operator-Index|Personal Operator Index]] [[00_HOME/Dashboard|Dashboard]] [[SOUL]] [[00_HOME/Operating-System|Operating System]] [[00_HOME/Principles|Principles]] [[03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index|Personal Context Intake Index]] [[02_KNOWLEDGE/Knowledge-Index|Knowledge Index - Master]] [[KNOWLEDGE-INDEX|Root Knowledge Index Routing Shim]] [[01_PROJECTS/Projects-Hub|Projects Hub]] [[06_AGENTS/Personal-Map-Architecture|Personal Map Architecture]] [[06_AGENTS/Use-Case-Mode-Architecture|Workspace Mode Layer Architecture]] [[06_AGENTS/ChaseOS-Studio-Architecture|ChaseOS Studio Architecture]] [[06_AGENTS/Settings-Provider-Config-and-Scaffold-Surfaces-Standalone-Application|Settings Surface Architecture]] [[ChaseOS-Feature-Family-and-Subfeature-Inventory]] [[docs/audits/2026-05-21_feature_family_deep_reconciliation]]*
