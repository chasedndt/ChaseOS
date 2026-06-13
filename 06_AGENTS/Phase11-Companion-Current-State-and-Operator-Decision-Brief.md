---
type: implementation-brief
title: Phase 11 Companion Current State and Operator Decision Brief
created: 2026-05-12
updated: 2026-05-14
status: CURRENT STATE DOCUMENTED / REGISTRY READINESS VERIFIED / OPERATOR DIRECTION CAPTURED / ROSTER UI PREVIEW READY / MEMORY BOUNDARY DEFINED / MEMORY APPROVAL PREVIEW WRITTEN / MEMORY APPROVAL EXECUTION PROOF WRITTEN / MEMORY READBACK SEARCH PREVIEW VERIFIED / LEDGER-WRITE EXECUTOR STATIC-QA VERIFIED / LEDGER READ MODEL VERIFIED / REAL LEDGER ACTIVE
runtime: Codex
---

# Phase 11 Companion Current State and Operator Decision Brief

## Status

**CURRENT STATE DOCUMENTED / REGISTRY READINESS VERIFIED / OPERATOR DIRECTION CAPTURED / ROSTER UI PREVIEW READY / CORE ADAPTER SYNC VERIFIED / MEMORY BOUNDARY DEFINED / MEMORY APPROVAL PREVIEW WRITTEN / MEMORY APPROVAL EXECUTION PROOF WRITTEN / MEMORY READBACK SEARCH PREVIEW VERIFIED / LEDGER-WRITE EXECUTOR STATIC-QA VERIFIED / LEDGER READ MODEL VERIFIED / REAL LEDGER ACTIVE.**

Phase 11 companion work has read-only status cards, approval previews, digest-bound approval queue writes, approval-consumption readiness, a read-only multi-companion registry readiness validator, a read-only operator direction packet, captured operator-approved v0.1 companion direction, a governed companion-selection approval-consumption executor, a read-only companion roster UI preview, Studio surfaces synced to `runtime/companion` as the core companion source of truth, a read-only separate companion memory boundary, a digest-gated companion memory approval preview/queue-write surface, a proof-only exact-once companion-memory approval consumption executor, a read-only proof readback/search preview, a digest-bound ledger-write approval preview, an explicit approved ledger-write executor, a companion-memory ledger read model, and a real current-vault raw/non-canonical ledger entry written through explicit approval `3243d5f9-7f34-47b4-a4cd-7c67f7b78541`. It does not yet have a durable custom registry loader, provider/model calls, runtime dispatch, Agent Bus writes from companion memory, context-pack readiness over companion memory, broad or ambient companion-memory writes, or canonical mutation.

## What Exists Now

Current builtin companion cards:

| Companion | Runtime ID | Current Role | Style Hint | Current Authority |
|---|---|---|---|---|
| Hermes | `hermes` | bounded runtime coordination companion | precise, governance-aware, coordination-heavy | read-only status only |
| OpenClaw | `openclaw` | local operator/runtime control companion | operational, tool-aware, safety-bounded | read-only status only |
| Archon | `archon` | engineering and architecture companion | systems-focused, implementation-oriented | read-only status only |

Current companion runtime surfaces:

- `runtime/studio/phase11_chat_companion_status.py`
- `runtime/studio/phase11_chat_companion_selection_preview.py`
- `runtime/studio/phase11_chat_companion_selection_queue_write_readiness.py`
- `runtime/studio/phase11_chat_companion_selection_queue_write_execution.py`
- `runtime/studio/phase11_chat_companion_selection_approval_consumption_readiness.py`
- `runtime/studio/phase11_chat_companion_selection_approval_consumption_executor.py`
- `runtime/studio/chat/companions/companion-profile.schema.json`
- `runtime/studio/chat/companions/registry.example.json`
- `runtime/studio/phase11_multi_companion_registry_readiness.py`
- `runtime/studio/phase11_operator_companion_direction.py`
- `runtime/studio/phase11_operator_companion_direction_answers.py`
- `runtime/studio/chat/companions/operator-direction.v0.1.json`
- `runtime/studio/phase11_companion_roster_ui_preview.py`
- `runtime/studio/phase11_companion_runtime_core_adapter_sync.py`
- `runtime/companion/memory.py`
- `runtime/studio/phase11_companion_memory_boundary_contract.py`
- `runtime/studio/phase11_companion_memory_approval_preview.py`
- `runtime/studio/phase11_companion_memory_approved_execution_proof.py`
- `runtime/studio/phase11_companion_memory_readback_search_preview.py`
- `runtime/studio/phase11_companion_memory_ledger_read_model_preview.py`
- `runtime/studio/phase11_companion_memory_real_ledger_activation_closeout.py`
- `runtime/companion/`

Current UI/status truth:

- The Chat panel can embed companion status.
- `/pet` and dashboard surfaces can expose companion status/read-only cards.
- Unknown companion/runtime requests block.
- Companion selection preview can build a future approval packet.
- Queue-write execution can write a pending approval artifact only with the expected digest.
- Approval-consumption readiness can validate a companion-selection approval but does not execute it.
- The governed approval-consumption executor has consumed one approved companion-selection artifact, written `runtime/studio/chat/companion-selection.json`, and blocked duplicate execution before target rewrite.
- Multi-companion registry readiness validates the registry/schema and compares Hermes/OpenClaw/Archon registry entries against builtin status cards without loading the registry for selection.
- Operator companion direction exposes the current roster options and the captured v0.1 operator answers that enabled the read-only roster UI preview.
- The roster UI preview renders active-first companion cards from `runtime/companion` metadata and keeps selection writes approval-gated.
- The runtime core adapter sync verifies Studio companion status, registry readiness, roster preview, and selection preview all consume the core companion roster while preserving no authority expansion.
- The companion memory boundary contract declares separate future memory namespaces under `07_LOGS/Companion-Memory/{companion}/`, validates allowed/denied memory candidates, and proves no memory files are written by the boundary pass.
- The companion memory approval preview computes deterministic future memory approval digests, previews a gated `companion_memory_write` packet, writes a pending approval only with explicit digest confirmation, and keeps memory ledger writes blocked until a future exact-once executor.
- The companion memory approved execution proof consumes one digest-bound approval exactly once, reserves an execution marker before proof outputs, marks the approval executed, writes proof-only evidence, and still keeps the real companion memory ledger/root absent.
- The companion memory readback/search preview indexes approval artifacts, exact-once markers, proof-temp outputs, and execution evidence, filters them by companion, memory class, status, and query, and still does not create or read a real companion-memory ledger.
- The companion memory ledger-write approval preview computes a deterministic future ledger entry and digest-bound approval packet from proof-only evidence.
- The companion memory approved ledger-write executor can consume a matching ledger-write approval exactly once and append one JSONL entry only through the explicit executor.
- Real-vault approval `3243d5f9-7f34-47b4-a4cd-7c67f7b78541` has been consumed once to append one raw/non-canonical Hermes ledger entry at `07_LOGS/Companion-Memory/hermes/memory-ledger.jsonl`; duplicate execution is exact-once-marker blocked before a second append.
- The companion memory ledger read model reads real JSONL ledgers when present, falls back to proof-only evidence when no current-vault ledger exists, tolerates malformed optional JSONL lines, and renders inside the Studio Chat panel without granting write authority.
- The companion memory real-ledger activation closeout verifies the executed approval, marker-before-append ordering, proof evidence, real ledger entry, duplicate guard, and non-authoritative/canonical-blocked posture.

## Current Live Proof Snapshot

Observed live command behavior during this pass:

- `phase11-chat-companion-selection-approval-preview --requested-runtime hermes --current-runtime openclaw --message "select Hermes companion"` returned `ok=true`, selection requested, zero blockers, and no writes.
- The embedded companion status reported 3 registered companion cards: Hermes, OpenClaw, and Archon.
- `phase11-chat-companion-selection-approval-consumption-readiness --json` without an approval artifact returned blocked with `no_companion_selection_approval_artifacts_found`.
- `qa-runner --surface phase11-chat-companion-selection-approval-consumption-readiness --mode static --json` passed and confirmed no real Markdown writes and no real approval artifact writes.
- `phase11-multi-companion-registry-readiness --json` returned `ok=true`, 3 registry companions, 3 builtin status cards, no blockers, and a warning that preferred `registry.json` is absent so the example registry was used.
- `qa-runner --surface phase11-multi-companion-registry-readiness --mode static --json` passed and confirmed no real Markdown writes and no real approval artifact writes.
- `operator-companion-direction-before-roster-ui --json` returned `ok=true`, 3 companion options, 10 unanswered operator decisions, `ready_for_roster_ui_preview=false`, and no writes/execution authority.
- `qa-runner --surface operator-companion-direction-before-roster-ui --mode static --json` passed and confirmed no real Markdown writes and no real approval artifact writes.
- `operator-answer-companion-direction-questions --json` returned `ok=true`, captured 10/10 operator answers, preserved v0.1 UI-only effects, blocked routing/provider/permission/writeback/memory/tool/protected-file authority, and advanced next action to `phase11-companion-roster-ui-preview`.
- `qa-runner --surface operator-answer-companion-direction-questions --mode static --json` passed and confirmed no real Markdown writes and no real approval artifact writes.
- `qa-runner --surface phase11-chat-companion-status-ui-shell --mode static --json` now passes after stale next-pass metadata was corrected.
- `phase11-companion-memory-approval-preview --companion-id hermes --memory-class preference --content "Operator prefers direct progress updates during long implementation passes." --json` returned `ok=true` with digest `3c49a24ad2f9275d327fc6923c0873ae3e42dfb9b97d3a194c163f07e0364250` and no writes.
- The same command with `--expected-memory-approval-digest 3c49a24ad2f9275d327fc6923c0873ae3e42dfb9b97d3a194c163f07e0364250 --write-approval` wrote pending approval `runtime/studio/approvals/448282cc-4d3c-4853-a114-8246657dbe5a.json` and audit `07_LOGS/Agent-Activity/phase11-companion-memory-approval-preview-3c49a24ad2f9275d.json`.
- Repeating the same approval write blocked with `approval_queue_request_already_exists_for_digest` before new artifact writes.
- A credential-class candidate blocked with `memory_class_not_allowed`, `memory_class_denied`, and `content_contains_denied_secret_or_credential_marker`.
- `qa-runner --surface phase11-companion-memory-approval-preview --mode static --json` passed and confirmed no Markdown, approval-artifact, or companion-memory writes during static QA.
- `phase11-companion-memory-approved-execution-proof` without `--execute` blocked before marker/proof writes with `execute_flag_required` plus missing approval decision.
- `phase11-companion-memory-approved-execution-proof --approval-id 448282cc-4d3c-4853-a114-8246657dbe5a --expected-memory-approval-digest 3c49a24ad2f9275d327fc6923c0873ae3e42dfb9b97d3a194c163f07e0364250 --execute` consumed the approval, wrote marker `runtime/studio/approvals/_companion_memory_execution_markers/448282cc-4d3c-4853-a114-8246657dbe5a.json`, wrote proof outputs under `.pytest_tmp_env/phase11-companion-memory-proof/448282cc-4d3c-4853-a114-8246657dbe5a/`, and wrote execution evidence under `07_LOGS/Studio-Graph-Views/phase11-companion-memory-approved-execution-proof/`.
- A duplicate execution attempt against the same approval blocked before writes with `exact_once_marker_already_present` and `future_proof_output_collision`.
- `07_LOGS/Companion-Memory/` remains absent after the live proof.
- `qa-runner --surface phase11-companion-memory-approved-execution-proof --mode static --json` passed and confirmed exact-once proof behavior in temp vaults without real Markdown, real approval-artifact, or real companion-memory writes.
- `phase11-companion-memory-readback-search-preview --query "direct progress" --status proof_written --json` returned `ok=true`, indexed executed approval `448282cc-4d3c-4853-a114-8246657dbe5a`, found one proof-written result, and reported `memory_root_read=false`.
- `qa-runner --surface phase11-companion-memory-readback-search-preview --mode static --json` passed and confirmed read-only proof indexing/search in a temp vault without real Markdown, approval-artifact, or companion-memory writes.
- `Test-Path 07_LOGS/Companion-Memory` returned `False` after the readback/search pass.
- `qa-runner --surface phase11-companion-memory-approved-ledger-write-execution-proof --mode static --json` returned `ok=true`: in temp vaults it consumed one ledger-write approval exactly once, reserved the marker before append, wrote one JSONL entry, wrote execution/rollback/evidence outputs, blocked duplicate execution, and confirmed real-vault Markdown, approval-artifact, and companion-memory snapshots were unchanged.
- `phase11-companion-memory-ledger-write-approval-preview --json` in the real vault returned `ok=true`, computed ledger-write approval digest `f415f33f24d87227388e399ad5d056943120a2f614903e33c446c52e4b7650e2`, and did not write an approval artifact or append the real ledger during the preview pass.
- The digest-gated real ledger-write approval was later written as `runtime/studio/approvals/3243d5f9-7f34-47b4-a4cd-7c67f7b78541.json`.
- `phase11-companion-memory-approved-ledger-write-execution-proof --approval-id 3243d5f9-7f34-47b4-a4cd-7c67f7b78541 --execute` consumed that approval once, reserved marker `runtime/studio/approvals/_companion_memory_ledger_write_markers/3243d5f9-7f34-47b4-a4cd-7c67f7b78541.json`, wrote one raw/non-canonical ledger entry at `07_LOGS/Companion-Memory/hermes/memory-ledger.jsonl`, and wrote evidence under `07_LOGS/Studio-Graph-Views/cml-ledger-write-proof/`.
- Repeating the same ledger-write execution blocked before append with the exact-once marker already present, future evidence collisions, and `ledger_entry_already_present`; ledger line count remained one.
- `phase11-companion-memory-real-ledger-activation-closeout --approval-id 3243d5f9-7f34-47b4-a4cd-7c67f7b78541 --json` returned `ok=true`, `real_ledger_active=true`, `duplicate_guard_verified=true`, and no provider/runtime/browser/Agent Bus/canonical authority flags.
- `phase11-companion-memory-ledger-read-model-preview --query "direct progress" --json` in the real vault now returns the real Hermes `ledger_entry` record from `07_LOGS/Companion-Memory/hermes/memory-ledger.jsonl`.
- `qa-runner --surface phase11-companion-memory-ledger-read-model-preview --mode static --json` returned `ok=true`: in temp vaults it read a JSONL ledger entry, verified filters and proof backfill, tolerated malformed JSONL lines, embedded the read model in the Chat panel contract, and confirmed real-vault Markdown, approval-artifact, and companion-memory snapshots were unchanged.
- `qa-runner --surface phase11-companion-memory-real-ledger-activation-closeout --mode static --json` returned `ok=true`: in temp vaults it verified closeout state, missing-ledger/missing-evidence blockers, API/registry/panel/frontend exposure, and no real-vault snapshot changes.

## What Does Not Exist Yet

- durable custom profile loader from `runtime/studio/chat/companions/registry.json`
- write-capable companion roster/picker UI beyond read-only preview
- roster-driven companion-selection target writes beyond the existing governed executor proof
- support for user-defined custom companion identities
- companion avatar assets
- companion voice style or speech output
- multi-companion conversation mode
- provider/model routing based on selected companion
- runtime/browser dispatch from companion selection
- Agent Bus task writes from companion UI
- companion-memory context readiness/context-pack surface over ledger and proof records
- additional companion-memory ledger appends beyond the first approved raw entry

## Approved v0.1 Operator Direction

The operator approved the following companion model on 2026-05-13:

- Companions are runtime-linked identity profiles with visual, tone, and status surfaces.
- Initial roster remains Hermes, OpenClaw, and Archon.
- Names stay Hermes/OpenClaw/Archon; aliases are deferred.
- v0.1 selection is per Chat session.
- v0.1 affects only UI identity, tone preset, status narration, read-only runtime card display, and non-authoritative companion comments.
- v0.1 does not affect execution routing, provider/model selection, permission scope, writeback authority, memory write authority, tool access, or protected file access.
- Rarity, stats, and personality metadata are descriptive UX metadata only.
- Visuals use abstract runtime marks, status badges, borders, and lightweight animation presets until a brand pack exists.
- Switching companions must use read-only preview plus approval-gated write to the selected companion target.
- Separate companion memory is allowed as governed, approval-gated, non-authoritative memory. The memory boundary is defined, and one raw Hermes ledger entry has been written through an explicit approval/executor chain; future writes require their own governed approval/executor pass.
- Runtime capability changes require a future governed routing pass.
- Roster expansion should support one active companion first, inactive roster browsing second, and multiple visible companions later.

## Operator Decisions Captured

The previous direction packet asked ten questions. They are now answered by `runtime/studio/chat/companions/operator-direction.v0.1.json` and validated by `runtime/studio/phase11_operator_companion_direction_answers.py`:

1. Companion concept  
Should companions be runtime identities, named AI personas, small product mascots, or mode/profile presets?

2. Number of first companions  
Should MVP start with Hermes/OpenClaw/Archon only, or add new custom companions?

3. Companion names  
Keep Hermes/OpenClaw/Archon, rename any of them, or add aliases?

4. Visual style  
Should companions use abstract runtime marks, generated avatars, initials/badges, or character-like portraits?

5. Selection behavior  
Should there be one active companion globally, one per Chat session, or one per surface?

6. What companion changes  
Does selecting a companion change only tone/status cards, or also default runtime/model routing after separate approval?

7. Tone boundaries  
How expressive should companions be: subtle status layer, conversational personality, or strong character presence?

8. Memory behavior  
Should companions have their own remembered preferences later, or should all memory stay under existing runtime/profile structures?

9. Manual override  
Should the operator be able to switch companions instantly after approval, or should switching always queue a visible approval?

10. Multi-companion future  
Do you eventually want multiple companions visible/responding together, or only a selectable roster with one active companion?

## Completed Safe Companion Pass

Completed build passes:

`phase11-multi-companion-registry-readiness`

`operator-companion-direction-before-roster-ui`

`operator-answer-companion-direction-questions`

`phase11-companion-roster-ui-preview`

`phase11-companion-runtime-core-adapter-sync`

`phase11-companion-memory-boundary-contract`

`phase11-companion-memory-approval-preview`

`phase11-companion-memory-approved-execution-proof`

`phase11-companion-memory-readback-search-preview`

`phase11-companion-memory-ledger-write-approval-preview`

`phase11-companion-memory-approved-ledger-write-execution-proof`

`phase11-companion-memory-ledger-read-model-preview`

`phase11-companion-memory-real-ledger-activation-closeout`

Those passes now:

- validates `runtime/studio/chat/companions/registry.example.json` or a future real `registry.json`
- compares registry entries against existing builtin cards
- produces read-only readiness output
- exposes Hermes/OpenClaw/Archon as current companion options
- captures ten operator decisions with approved v0.1 UI-only boundaries
- unblocks a read-only companion roster UI preview
- renders active-first roster preview cards from the core companion package
- proves Studio companion surfaces are synced to `runtime/companion`
- defines separate governed companion memory namespaces and candidate validation
- computes deterministic companion-memory approval digests and can write one pending approval only with explicit digest confirmation
- blocks duplicate companion-memory approval queue writes before new artifacts
- blocks denied credential/secret-like companion-memory candidates
- consumes one digest-bound companion-memory approval exactly once into proof-only evidence
- marks the consumed companion-memory approval executed and blocks duplicate execution before writes
- indexes companion-memory approval/proof evidence for read-only search without reading a real ledger
- computes a deterministic future companion-memory ledger entry from proof-only evidence
- computes a digest-bound ledger-write approval packet preview
- can queue one pending ledger-write approval only with exact digest confirmation
- blocks duplicate, mismatched-digest, and missing-proof ledger-write approval requests before writes
- verifies the approved ledger-write executor in temp/static QA: exact-once marker before append, one JSONL entry, duplicate block, evidence outputs, and no real-vault snapshot changes
- reads companion-memory JSONL ledgers when present and falls back to proof-only evidence when absent
- exposes the read model in the native Chat panel, StudioAPI, CLI, and QA runner without write authority
- verifies the real current-vault companion-memory ledger activation after approval `3243d5f9-7f34-47b4-a4cd-7c67f7b78541` was consumed once
- confirms `07_LOGS/Companion-Memory/hermes/memory-ledger.jsonl` contains one raw/non-canonical entry and duplicate execution blocks before append
- keeps selection target writes blocked for the read-only registry/direction surfaces
- keeps ambient real memory ledger writes blocked; additional ledger appends still require explicit approval artifacts and execution decisions
- keeps provider/model calls blocked
- keeps runtime dispatch and Agent Bus writes blocked

Next recommended pass is `phase11-companion-memory-context-readiness-preview`. Do not expand companion behavior into routing, provider/model selection, permissions, broad real memory authority, tool access, protected file access, Agent Bus writes, or canonical mutation without a future governed pass. The next pass may only build a bounded context-readiness model over the real raw ledger entry plus proof evidence and must keep provider/runtime/write authority blocked unless a separate approval chain is implemented.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*

## 2026-05-13 Core Companion Layer v0.1 Update

Status: COMPLETE / V0.1 CORE LAYER VERIFIED / NO RUNTIME AUTHORITY.

`runtime/companion/` now provides the core companion policy, profile validation, Hermes/OpenClaw/Archon roster, read-only switch preview, approval-flag-gated selection writer, and switch-ledger behavior. The pass also created [[Companion-Behavior-Policy]], [[Companion-Roster]], and [[Companion-Profile-Template]]. It does not add Studio UI, avatar assets, companion memory, provider/model routing, runtime dispatch, Agent Bus writes, permission changes, tool/connector access, protected-file access, or canonical mutation.

Verification: focused companion tests passed (`10 passed`), adjacent Phase 11 companion regression passed (`18 passed`), read-only preview wrote nothing, and approved selection against a log-root proof fixture wrote only a scoped selection proof plus switch ledger with routing/memory/permission changes false.

## 2026-05-13 Runtime Core Adapter Sync Update

Status: COMPLETE / READ-ONLY / CORE ADAPTER SYNC VERIFIED / NO AUTHORITY EXPANSION.

Studio companion status, multi-companion registry readiness, companion roster UI preview, and companion-selection approval preview now consume `runtime/companion` as the source of truth for Hermes/OpenClaw/Archon identity metadata, visual marks, descriptive stats, profile validation, and the shared companion selection target path. `runtime/companion` no longer reverse-imports Studio status metadata.

Verification: focused implementation tests passed (`27 passed`), the companion selection chain passed (`25 passed`), the adapter-sync audit passed (`4 passed`), the broader companion regression passed (`58 passed`), the companion QA subset passed (`10 passed, 67 deselected`), and static QA surfaces for companion status, registry readiness, roster UI preview, selection approval preview, and selection approval consumption executor all passed. The adapter-sync dry run returned `ok=true` with status/registry/roster/selection synced and `canonical_mutation_allowed=false`.

*Graph links: [[OpenClaw-Runtime-Profile]]*
