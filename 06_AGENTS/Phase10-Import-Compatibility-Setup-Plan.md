---
title: Phase 10 Import Compatibility Setup Plan
type: implementation-backlog
status: COMPLETE THROUGH 10F6 / REAL-TARGET EXECUTION CONTRACT SEEDED
phase: 10F
runtime: Codex / Hermes-Optimus
updated: 2026-05-12
---

# Phase 10 Import Compatibility Setup Plan

This note defines the remaining 10F onboarding, compatibility, and setup lane. It starts from preview and approval-first flows. It does not authorize automatic rewrites of arbitrary Markdown folders or Obsidian vaults.

## Repo-Truth Baseline

- Workspace entry/readiness surfaces exist as read-only panels.
- Open Folder compatibility readiness is now complete/read-only/verified through 10F1.
- Obsidian vault detection is now complete/read-only/verified through 10F2.
- General Markdown inference preview is now complete/read-only/verified through 10F3.
- ChaseOS bootstrap preview is complete/read-only/verified through 10F4.
- Workspace upgrade approval packet and proof-temp execution chain are complete/verified through 10F5/10F6.
- Real target-folder/file upgrade execution now has an explicit implementation contract in [[Phase10-Real-Target-Upgrade-Execution-Contract]], but no live target mutation is activated.
- Real target-folder/file upgrade execution is not mounted; 10F6 proves exact-once approval consumption and output ordering under controlled proof roots only.
- `chaseos scaffold brain` exists as a backend command path, but Studio upgrade execution does not invoke scaffold generation against the live vault.
- Phase 10A0 real-file cockpit testing exposed an immediate import compatibility gap: the current acquisition file-picker/drop surface accepts only text-readable suffixes, while real operator exports include PDF and spreadsheet/document formats.
- Operator screenshots from the 2026-05-07 staged-inbox test are summarized in `06_AGENTS/Phase10A0-Acquisition-Cockpit-Cleanup-Plan.md`; the screenshot shows `Required inputs 1 / 3`, text-only accepted suffixes, and unclear next-action flow after `stage-upload complete`.
- Source coverage must be flexible. One real source must be sufficient for stage/import/preview; multi-source/platform coverage is confidence metadata, not a default product gate.

## Required Passes

| Pass | Status | Dependencies | Output |
|---|---|---|---|
| `10F1-open-folder-compatibility-readiness` | COMPLETE / READ-ONLY / VERIFIED | workspace entry panel | Read-only readiness report for any selected folder |
| `10F2-obsidian-vault-detection` | COMPLETE / READ-ONLY / VERIFIED | `10F1` | Bounded Obsidian vault detector and compatibility classification |
| `10F3-general-markdown-inference-preview` | COMPLETE / READ-ONLY / VERIFIED | `10F1`, `10F2`, parser contract from `10X` | Preview inferred nodes/links/trust states without writing |
| `10F4-chaseos-bootstrap-wizard-preview` | COMPLETE / READ-ONLY / VERIFIED | scaffold command contract | GUI preview over `chaseos scaffold brain` |
| `10F5-upgrade-plan-approval-packet` | COMPLETE / APPROVAL ARTIFACT WRITTEN / VERIFIED | `10F2`, `10F3`, `10F4` | Approval packet for migration/bootstrap/upgrade |
| `10F6-approved-upgrade-execution-proof` | COMPLETE / APPROVAL CONSUMED / PROOF-TEMP VERIFIED | `10F5` approval artifact | Exact-once proof for approved workspace upgrade writes without live target mutation |
| `10F-RT1-real-target-upgrade-execution-contract` | DESIGN READY / LIVE MUTATION BLOCKED | `10F5`, `10F6`, lower-phase path policy/Gate approval consumption | Approval-first real target executor contract with preflight, rollback, audit, and protected/canonical/foreign-folder guard requirements |
| `10F7-document-normalized-intake` | PLANNED | Acquisition cockpit cleanup | PDF/DOCX/XLSX/CSV original-file provenance plus normalized Markdown/JSON preview artifacts |

## 10F1 - Open Folder Compatibility Readiness

Status: COMPLETE / READ-ONLY / VERIFIED as of 2026-05-08.

Implemented files:
- `runtime/studio/open_folder_compatibility_readiness.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/workspace_import_flow.py`
- `runtime/studio/shell/frontend/app.js`
- `runtime/studio/shell/frontend/styles.css`
- `runtime/studio/shell/panel_registry.py`
- `runtime/studio/qa_runner.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- focused 10F1 tests and CLI docs

Verified behavior:
- `chaseos studio open-folder-compatibility-readiness --json` returns a bounded readiness model.
- `chaseos studio qa-runner --surface open-folder-compatibility-readiness --mode static --json` passes with no markdown writes and no approval artifact writes.
- Workspace Entry embeds compatibility readiness. This pass historically advanced to `phase10f2-obsidian-vault-detection`, which is now complete.
- Real-vault dry run classifies the current repo as `chaseos_native` with 17 ChaseOS markers and bounded/truncated Markdown count by design.

Still not included:
- migration approval packet,
- upgrade/scaffold executor,
- graph persistence,
- `.obsidian` writes,
- arbitrary folder rewrite.

Likely touched files:
- `runtime/studio/open_folder_readiness.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/frontend/app.js`
- `runtime/studio/shell/frontend/index.html`
- `runtime/studio/shell/frontend/styles.css`

Backend contract:
- Accept a folder path from controlled UI context.
- Return folder exists/not exists, directory/file, markdown count, ChaseOS marker count, Obsidian marker count, and warning list.

UI behavior:
- Show compatibility status and blockers.
- No migration buttons with write authority.

Authority boundary:
- Read-only filesystem inspection under selected folder.
- No file creation.

Tests:
- Empty folder, markdown folder, Obsidian vault, ChaseOS vault, missing path, file path.

## 10F2 - Obsidian Vault Detection

Status: COMPLETE / READ-ONLY / VERIFIED as of 2026-05-08.

Implemented files:
- `runtime/studio/obsidian_vault_detection.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/frontend/app.js`
- `runtime/studio/shell/panel_registry.py`
- `runtime/studio/qa_runner.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- focused 10F2 tests and CLI docs

Verified behavior:
- `chaseos studio obsidian-vault-detection --json` returns a bounded Obsidian detection model.
- `chaseos studio qa-runner --surface obsidian-vault-detection --mode static --json` passes with no markdown writes and no approval artifact writes.
- Workspace Entry and Open Folder scan results embed Obsidian vault detection.
- Real-vault dry run classifies the current repo as `obsidian_vault_detected` with `.obsidian` config present, 300 Markdown files analyzed, 2220 wikilinks, 2 aliases, and bounded/truncated scan warnings by design.
- Registry next marker historically advanced to `phase10f3-general-markdown-inference-preview`, which is now complete.

Still not included:
- sidecar hint editor or hint writeback,
- migration approval packet,
- upgrade/scaffold executor,
- graph persistence,
- `.obsidian` writes,
- plugin activation,
- arbitrary folder rewrite.

Likely touched files:
- `runtime/studio/obsidian_vault_detection.py`
- `runtime/studio/open_folder_compatibility_readiness.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/frontend/app.js`
- shell tests

Backend contract:
- Detect `.obsidian`, workspace config, plugin presence, canvas files, attachments, wikilinks, aliases, and embeds.
- Return compatibility classification and risk notes.

UI behavior:
- Show Obsidian compatibility badge, plugin risk notes, and migration-readiness state.

Authority boundary:
- No `.obsidian` writes.
- No plugin activation or config changes.

Tests:
- Fixture vaults with `.obsidian`, canvases, attachments, frontmatter aliases.

## 10F3 - General Markdown Inference Preview

Status: COMPLETE / READ-ONLY / VERIFIED as of 2026-05-08.

Implemented files:
- `runtime/studio/general_markdown_inference_preview.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/frontend/app.js`
- `runtime/studio/shell/frontend/styles.css`
- `runtime/studio/shell/panel_registry.py`
- `runtime/studio/qa_runner.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- focused 10F3 tests and CLI docs

Verified behavior:
- `chaseos studio general-markdown-inference-preview --json` returns a bounded preview-only inference model.
- `chaseos studio qa-runner --surface general-markdown-inference-preview --mode static --json` passes with no markdown writes and no approval artifact writes.
- Workspace Entry and Open Folder scan results embed the inference preview.
- Real-vault dry run reports the current repo as preview-ready with bounded output, candidate node/edge/domain/trust defaults, unresolved-reference posture, and migration warnings by design.
- Registry next marker historically advanced to `phase10f4-chaseos-bootstrap-wizard-preview`, which is now complete.

Still not included:
- sidecar hint editor or hint writeback,
- migration approval packet,
- upgrade/scaffold executor,
- graph persistence,
- `.obsidian` writes,
- arbitrary folder rewrite.

Likely touched files:
- parser-backed graph modules from `10X`
- `runtime/studio/shell/api.py`
- frontend preview panel

Backend contract:
- Infer candidate node types, edge types, source domains, trust state defaults, and migration warnings.
- Mark all inferred data as preview/non-canonical.

UI behavior:
- Show preview graph/table with confidence and warnings.
- No accept/promote button until approval packet pass.

Authority boundary:
- Read-only.
- No sidecar hints written.

Tests:
- Markdown folder fixture.
- Unknown frontmatter fixture.
- Large folder bounded scan behavior.

## 10F4 - ChaseOS Bootstrap Wizard Preview

Status: COMPLETE / READ-ONLY / VERIFIED as of 2026-05-08.

Implemented files:
- `runtime/studio/chaseos_bootstrap_wizard_preview.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/frontend/app.js`
- `runtime/studio/shell/frontend/styles.css`
- `runtime/studio/shell/panel_registry.py`
- `runtime/studio/qa_runner.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- `runtime/scaffold/generator.py`
- `runtime/chaseos_gate.py`
- focused 10F4/scaffold/Gate tests and CLI docs

Verified behavior:
- `chaseos studio chaseos-bootstrap-wizard-preview --json` returns a bounded read-only bootstrap plan.
- `chaseos studio qa-runner --surface chaseos-bootstrap-wizard-preview --mode static --json` passes with no markdown writes and no approval artifact writes.
- Workspace Entry and Open Folder scan results embed the bootstrap preview.
- Real-vault dry run reports `target_state=existing_partial_chaseos`, 5 of 10 target folders present, all 10 anchor files present, 5 future folder creates, and future approval steps for real execution.
- Registry next marker is now `phase10f5-upgrade-plan-approval-packet`.

Still not included:
- migration approval packet,
- approved upgrade/scaffold executor,
- target folder/file creation,
- Studio-invoked scaffold generation,
- scaffold artifact write from preview,
- arbitrary folder rewrite.

Likely touched files:
- CLI scaffold command docs/contracts
- new Studio wizard panel or workspace-entry expansion
- shell API method

Backend contract:
- Wrap `chaseos scaffold brain` as a dry-run preview.
- Return target folders/files that would be created.

UI behavior:
- Stepper-style preview of required structure, docs, and logs.
- No scaffold execution without explicit approval packet.

Authority boundary:
- Preview only.
- No folder creation in this pass.

Tests:
- Existing ChaseOS vault.
- Empty folder.
- Partial ChaseOS folder.

## 10F5 - Upgrade Plan Approval Packet

Status: COMPLETE / APPROVAL ARTIFACT WRITTEN / VERIFIED as of 2026-05-08.

Implemented files:
- `runtime/studio/upgrade_plan_approval_packet.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/frontend/app.js`
- `runtime/studio/shell/panel_registry.py`
- `runtime/studio/approval_center_panel.py`
- `runtime/studio/qa_runner.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- focused 10F5 tests and CLI docs

Backend contract:
- Build approval packet with exact target paths, hashes of existing files, proposed new files, proposed updates, rollback plan, and exact-once marker path.
- Reuse 10F1-10F4 preview data and compute planned target writes before approval.
- Write approval artifact only when explicitly requested.

UI behavior:
- Workspace Entry displays approval packet preview and approval-required posture.
- Approval Center displays written workspace upgrade packets without granting execution authority; cross-feature Approval Center boundaries are tracked in [[ChaseOS-Approval-Center]].

Authority boundary:
- Writes approval artifact only when explicitly requested.
- No upgrade writes.
- No scaffold execution.
- No Git, Gate, Agent Bus, provider, connector, host, release, workflow, or canonical mutation.

Tests:
- Approval packet preview works without writing.
- Explicit approval artifact write works.
- Collision/blocker/output path checks are reported.
- Static QA passes with no markdown writes.
- CLI command contract and JSON contract pass.

Verified live:
- `chaseos studio upgrade-plan-approval-packet --json` returned a no-write preview.
- `chaseos studio upgrade-plan-approval-packet --write-approval --json` wrote `workspace-upgrade-appr-383c66ea3196193a`.

## 10F6 - Approved Upgrade Execution Proof

Status: COMPLETE / APPROVAL CONSUMED / PROOF-TEMP VERIFIED as of 2026-05-08.

Implemented files:
- `runtime/studio/approved_upgrade_execution_proof.py`
- `runtime/studio/shell/api.py`
- `runtime/studio/shell/frontend/app.js`
- `runtime/studio/shell/panel_registry.py`
- `runtime/studio/approval_center_panel.py`
- `runtime/studio/qa_runner.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- focused 10F6 tests and CLI docs

Backend contract:
- Consume approval exactly once.
- Reserve marker before writes.
- Write only proof-temp planned target artifact copies.
- Emit execution evidence and rollback plan.
- Block duplicate execution before any proof output write.

UI behavior:
- Execution remains CLI/governed; Workspace Entry and Approval Center report consumed/proof status, with Approval Center authority governed by [[ChaseOS-Approval-Center]].
- No Studio execution button is mounted in this pass.

Authority boundary:
- No arbitrary folder rewrites.
- No live target workspace folder/file writes.
- Only controlled proof roots are written.
- No Git mutation unless separately approved.
- No scaffold execution, provider/connector call, Gate mutation, Agent Bus task write, host/release mutation, workflow execution, or canonical promotion.

Tests:
- Requires `--execute`.
- Marker before writes.
- Duplicate execution blocks.
- Rollback evidence complete.
- Broad Studio/CLI/runtime regression passes.

Verified live:
- `chaseos studio approved-upgrade-execution-proof --approval-packet-id workspace-upgrade-appr-383c66ea3196193a --execute --json` consumed the approval once and wrote proof-temp outputs.
- A duplicate execution attempt returned `blocked_duplicate_workspace_upgrade_execution` with zero new writes.

## 10F-RT1 - Real Target Upgrade Execution Contract

Status: DESIGN READY / LIVE MUTATION BLOCKED as of 2026-05-12.

Contract artifact:
- `06_AGENTS/Phase10-Real-Target-Upgrade-Execution-Contract.md`

Contract decision:
- The real target executor must be a new approval-first, lower-phase write-capable lane, not a flag flip on the proof-temp `approved_upgrade_execution_proof.py` surface.
- First implementation should be create-only for missing ChaseOS bootstrap anchors, with no overwrite/delete/arbitrary Markdown rewrite authority.
- Required gates are real-target approval scope, operator-selected target path, path-policy guard, exact-once marker, pre-write rollback plan, target-effect audit, duplicate blocking, and temp-target proof before any operator-selected real target run.

Required guard proof before activation:
- protected/canonical write attempts block;
- foreign-folder and symlink-escape writes block;
- existing files are not overwritten;
- rollback removes only created paths;
- audit survives blocked and partial-failure states.

Authority boundary:
- No real target folder/file mutation is authorized by the contract itself.
- No scaffold execution, provider/connector call, Git, workflow, Gate mutation, host/release mutation, or canonical promotion is added.
- Real target execution remains blocked until a separate implementation/review/approval pass clears the gates.

## Dependency Rules

- `10F5` and `10F6` must stay together when implementation begins.
- `10F3` should reuse the parser contract from `10X` when possible.
- No migration execution should run in parallel with final truth sync.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
