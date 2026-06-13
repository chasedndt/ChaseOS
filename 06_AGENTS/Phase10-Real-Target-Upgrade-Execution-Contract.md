---
title: Phase 10 Real Target Upgrade Execution Contract
type: implementation-contract
status: DESIGN READY / BLOCKED ON SEPARATE APPROVAL AND LOWER-PHASE EXECUTION AUTHORITY
phase: 10F-real-target-execution
runtime: Hermes-Optimus
updated: 2026-05-12
---

# Phase 10 Real Target Upgrade Execution Contract

This contract defines the next safe step after the Phase 10F5/10F6 workspace upgrade approval/proof-temp chain. It does **not** activate real target-folder/file mutation. It specifies the approval-first executor shape, preflight gates, rollback/audit model, verification evidence, and guard tests required before ChaseOS may execute an upgrade against an operator-selected folder.

Graph links: [[ChaseOS-Studio-Phase10-Implementation-Tracker]] · [[Phase10-Import-Compatibility-Setup-Plan]] · [[ChaseOS-Approval-Center]] · [[HERMES]] · [[Agent-Activity-Index]]

## Current Repo Truth Audited

Implemented and verified today:

- `runtime/studio/upgrade_plan_approval_packet.py` creates a governed approval packet and may write one approval artifact only when explicitly requested.
- `runtime/studio/approved_upgrade_execution_proof.py` consumes one matching approval exactly once, reserves an execution marker before proof outputs, blocks duplicate execution, and writes proof-temp evidence only.
- The current proof chain explicitly reports `target_workspace_writes_performed: false` and keeps `writes_target_workspace`, `writes_target_folders`, `writes_target_files`, `updates_existing_files`, `invokes_scaffold_generator`, `executes_migration`, `executes_upgrade`, `uses_git`, and `canonical_mutation_allowed` false.
- `runtime/scaffold/generator.py` is still draft-only. It writes generated artifacts under `runtime/scaffold/generated/` and does not mutate real target roots.
- The Studio MVP closure gate still names real target workspace upgrade/migration as partial/proof-temp-only.

Therefore the next executor cannot be a minor flag flip on `approved_upgrade_execution_proof.py`. It must be a new lower-phase write-capable execution lane with its own path policy, approval consumption, rollback, and evidence.

## Proposed Executor Surface

Suggested new surface name:

- backend module: `runtime/studio/approved_target_upgrade_executor.py`
- focused tests: `runtime/studio/test_approved_target_upgrade_executor.py`
- shell/static tests: `runtime/studio/shell/test_pass10f_real_target_upgrade_executor.py`
- CLI command: `chaseos studio approved-target-upgrade-executor --approval-packet-id <id> --target-path <path> --execute --json`
- QA runner surface: `approved-target-upgrade-executor`
- evidence root: `07_LOGS/Studio-Graph-Views/target-upgrade-executions/`
- exact-once marker root: `07_LOGS/Agent-Activity/_workspace_upgrade_approvals/_target_execution_markers/`

This should remain CLI/governed first. Studio may display readiness and evidence, but should not mount a one-click write button until the CLI executor has passed focused and broad regression.

## Required Approval Packet Changes Before Execution

The existing 10F5 approval packet is proof-temp scoped. A real executor must reject proof-temp approvals and require a new packet scope such as:

```text
approval_scope: one_operator_selected_target_upgrade
operation: workspace_upgrade_target_execution
proof_temp_only: false
target_workspace_writes_allowed: true
```

The approval material must include:

- exact operator-selected `target_path`, normalized to an absolute path;
- target fingerprint captured at approval time: existence, directory status, device/inode or platform equivalent where available, selected marker files, and bounded directory listing digest;
- full planned operation list with operation ids, normalized relative paths, operation type, expected pre-state, content digest for created/updated files, and explicit protected-path posture;
- generated rollback plan before execution, not after;
- exact-once marker path;
- audit/evidence output paths;
- `approval_packet_id` and request digest that binds target, plan, and operator decision together.

## Mandatory Path Policy

Every planned write must pass policy before any marker or target write occurs.

### Allowed first implementation

The first real target executor should be create-only for missing ChaseOS bootstrap anchors:

- create missing required directories from `REQUIRED_DIRS`;
- create missing required anchor files from `REQUIRED_FILES` using approved placeholder content;
- never overwrite existing files;
- never delete target files;
- never rewrite arbitrary Markdown content;
- never edit `.obsidian` configuration;
- never run provider, connector, Git, workflow, host, installer, release, or canonical promotion actions.

### Blocked write classes

The executor must fail closed if any planned operation:

- resolves outside the operator-selected target root after symlink and `..` normalization;
- uses an absolute planned target path instead of a target-relative path;
- targets the ChaseOS source repo/vault root unless the operator explicitly selected it and the plan is still create-only/no-overwrite;
- targets protected doctrine/control surfaces such as `06_AGENTS/Permission-Matrix.md`, `06_AGENTS/Trust-Tiers.md`, `06_AGENTS/Agent-Security-Model.md`, `runtime/policy/`, `runtime/workflows/registry/`, `02_KNOWLEDGE/`, or existing canonical notes;
- crosses into a foreign folder outside the selected root;
- follows a symlink escape;
- would overwrite, truncate, rename, delete, chmod, move, or recursively copy content;
- attempts scaffold generation against a live target rather than using approved operation payloads.

The current target-write proof must include tests showing protected/canonical/foreign-folder writes are guarded. Passing those tests is part of readiness; it is not optional hardening.

## Execution State Machine

The executor must use an explicit state model:

```text
preview_only
  -> preflight_ready
  -> marker_reserved
  -> executing_target_writes
  -> verifying_target_writes
  -> executed
```

Failure states:

```text
blocked_preflight
blocked_duplicate_execution
execution_failed_before_target_write
execution_failed_after_partial_write
rollback_attempted
rollback_succeeded
rollback_failed_operator_review_required
```

Rules:

1. Preview mode never writes marker, approval consumption, evidence, or target files.
2. Execute mode validates approval, target fingerprint, path policy, marker absence, and output-path absence first.
3. The exact-once marker is created with create-new-only semantics before target writes.
4. Target writes are performed from the approved operation list only.
5. Each created path is verified immediately after write.
6. Approval is marked consumed only after marker reservation and before or with first target write, with audit evidence recording the ordering. If the implementation cannot make that atomic, it must record the split explicitly and block duplicate replay through the marker.
7. Duplicate execution must block before any target write attempt.

## Rollback Model

For the first create-only executor, rollback is simple but still mandatory:

- record every created file and directory in execution order;
- rollback removes created files first;
- rollback removes created directories only if empty and created by this execution;
- rollback never deletes pre-existing files or directories;
- rollback writes an audit result with removed paths, retained paths, failures, and operator follow-up requirements.

If future versions allow updates, they must add pre-write backups and digest-verified restoration before allowing update operations.

## Evidence Model

Each execution should write these bounded evidence artifacts:

- `preflight-report.json` — target fingerprint, approval validation, path-policy result, marker/output readiness, and blockers;
- `planned-writes.json` — exact approved create-only operations;
- `execution-audit.json` — marker reservation, approval consumption, per-operation write attempts, verification, and final status;
- `rollback-plan.json` — operation-specific undo plan generated before writes;
- `rollback-result.json` — only when rollback is invoked;
- `target-upgrade-execution.json` — operator-facing summary surfaced by Studio/Approval Center.

Evidence belongs under logs/audit roots only. Evidence writes do not imply permission to write canonical knowledge.

## Required Test Plan

Minimum focused tests for `runtime/studio/test_approved_target_upgrade_executor.py`:

1. preview mode reports planned writes and writes nothing;
2. execute mode rejects proof-temp 10F5 approval scope;
3. execute mode accepts only real-target approval scope;
4. missing approval blocks;
5. request digest mismatch blocks;
6. target fingerprint drift blocks;
7. exact-once marker is reserved before target writes;
8. duplicate marker blocks before writes;
9. create-only happy path creates missing required directories/files in a temp target;
10. existing files are not overwritten;
11. protected canonical path operation blocks;
12. foreign-folder operation blocks;
13. symlink escape operation blocks;
14. rollback plan is generated before writes;
15. rollback removes only created paths;
16. audit survives blocked and partial-failure states.

Minimum shell/static tests:

- Studio registry/readiness labels the surface as approval-gated, not read-only and not direct-write;
- QA static surface proves no writes in preview/static mode;
- CLI command contract includes the command and JSON envelope;
- Approval Center can show readiness/evidence without granting execution authority.

## Activation Gate

Do not activate real target mutation until all are true:

- operator supplies/selects the exact target folder;
- a real-target approval packet, not a proof-temp packet, exists and is approved;
- path-policy tests prove protected/canonical/foreign/symlink writes fail closed;
- exact-once marker and duplicate blocking pass;
- rollback plan and rollback test pass;
- target-effect evidence is written for a temp target first;
- broad Studio/CLI/runtime regressions pass;
- human review explicitly approves moving from temp target to operator-selected real target.

## Current Blocker Report

Status: blocked for live mutation, design-ready for implementation.

Blockers to clear before real target execution:

- no real-target approval packet scope exists yet;
- reusable Studio target-write path-policy helper now exists at `runtime/studio/target_write_path_policy.py` with focused protected/canonical/foreign/absolute/symlink/no-overwrite guard tests; executor integration remains separate;
- `approved_upgrade_execution_proof.py` is intentionally proof-temp and must not be repurposed directly;
- scaffold generator remains draft-only and is not a live target mutator;
- no operator-selected real target and approval packet for this task were supplied;
- no human approval was provided to mutate a real folder.

This is the correct Phase 10/ChaseOS alignment: Studio can surface the readiness and executor contract, but actual file mutation is a governed Phase 9-and-below write path with Gate/approval/exact-once/rollback evidence.

## Recommended Kanban Split

1. Ops implementation card: add target-write path-policy helper and focused tests for protected/canonical/foreign/symlink blocking.
2. Ops implementation card: add preview-only real-target approval packet scope and readiness evidence; no target writes.
3. Ops implementation card: add temp-target executor happy path, rollback, exact-once marker, and audit; still no live operator target.
4. Reviewer card: review target-mutation authority, tests, and evidence before any operator-selected target execution.
5. PM/operator card: only after review, decide whether to run one approved execution against a named real target folder.

## Operator-Facing Payoff

Once implemented and reviewed, this gives Studio the missing ChaseOS-native upgrade path for real folders: an operator can select a partial folder, inspect the exact planned ChaseOS bootstrap writes, approve the bounded operation, execute once, verify target effects, and retain rollback/audit evidence. Until then, ChaseOS remains honest: the runtime exists and is testable now, but real target mutation is intentionally blocked rather than hidden behind preview/proof surfaces.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
