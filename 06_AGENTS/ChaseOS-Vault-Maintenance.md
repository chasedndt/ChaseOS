---
title: ChaseOS Vault Maintenance Guide
type: runtime-capability-readme
scope: Operator and Autonomous Agent Graph Repair
created: 2026-04-24
status: CURRENT
---

# ChaseOS Vault Maintenance

This node defines the official **ChaseOS Maintenance Sweep** capability. This tool serves as the operating system's self-healing graph enforcement mechanism. It prevents node drift, ensures correct chronology routing, and enforces rigid agent provenance.

For the practical setup guide, CLI examples, expected JSON output shapes, and
OpenClaw cron behavior, use `[[Graph-Hygiene-CLI-and-OpenClaw-Cron-Runbook]]`.

> [!IMPORTANT]
> **To All Autonomous Agents (Hermes, OpenClaw):** When you run complex workflows that spawn multiple new nodes, index documents, or move system files, you **must** invoke this capability as your final step to ensure your structural footprint converges with the vault's governance schema.

## What it does

Executing the maintenance suite runs three stages sequentially:
1. **Vault Hygiene (`vault_hygiene.py`)** — Scans loose nodes with path-resolved wikilink graph state, tolerates transient runtime markdown files that disappear during scans, enforces directory boundaries, rewrites broken backtick syntax to graph links, constructs index maps, writes path-qualified index/anchor links when stems are ambiguous, and classifies suspicious loose markdown before any fix/delete decision.
2. **Daily Hub Linker (`daily_hub_linker.py`)** — Extracts all `YYYY-MM-DD` timestamps from build logs and operator briefs, securely wiring them to the Chronological Daily Hubs.
3. **Provenance Linker (`provenance_linker.py`)** — Scans all agent outputs and enforces graph routing backwards to the core Runtime Profiles (`[[OpenClaw-Runtime-Profile]]` / `[[Hermes-Runtime-Profile]]`).

### Loose-node classification

`vault_hygiene.py` does not treat every loose Obsidian node as the same class of problem.

Current loose-node buckets:
- `graph_orphan` / `loose_node` — safe index/anchor wiring candidates.
- `keep_excluded_visible_orphan` — a hash-approved `keep_excluded` file that is safe to leave out of canonical navigation but still appears as a raw zero-degree node in Obsidian; `--fix` wires it to the reversible holding index at `99_ARCHIVE/Vault-Hygiene-Review/Keep-Excluded/Keep-Excluded-Index.md`.
- `strikezone_staged_capture_orphan` — raw RSS staged captures for the StrikeZone Crypto trading/crypto project lane. These are kept in place and wired to `runtime/acquisition/staging/strikezone/StrikeZone-RSS-Staging-Index.md`; they are context inputs, not canonical trading notes or trade authority.
- `duplicate_candidate` — likely duplicate of a canonical document such as `[[Agent-Control-Plane]]`, `[[Permission-Matrix]]`, `[[Trust-Tiers]]`, `[[Vault-Map]]`, `[[Agent-Registry]]`, `[[Backends-Supported]]`, `[[ROADMAP]]`, or `[[PROJECT_FOUNDATION]]`; requires review before archive/delete.
- `review_only_artifact` — export/template/runtime-run artifacts such as `core_export/`, `core_templates/`, or Codex run output; not auto-wired into canonical navigation. The default proposal decision is `archive_noncanonical_artifact`.
- `technical_readme_loose` / `runtime_markdown_loose` — code/runtime README or markdown artifacts; review before wiring, excluding, or archiving as non-canonical evidence.
- `empty_placeholder` — empty or near-empty markdown slot; delete candidate only after explicit operator approval.

The JSON output now includes:
- `category_counts` - hygiene issue counts such as duplicate candidates, technical READMEs, runtime markdown, and graph orphans.
- `node_category_counts` - inferred ChaseOS node buckets such as `agent_control_doc`, `agent_draft_doc`, `runtime_readme`, `core_export_artifact`, `studio_graph_evidence`, and log/archive classes.
- `loose_node_review_queue` - the operator queue for review-gated duplicate, misplaced, runtime, export/template, and placeholder nodes. Each row includes the suspected canonical/keep path when available.
- `visible_graph_audit` - graph-visible counters that can still make Obsidian look wrong even when the active review queue is clean: `raw_zero_degree_count`, `weak_degree_1_count`, `unresolved_link_target_count`, `ambiguous_link_target_count`, `connected_duplicate_stem_count`, and `semantic_hub_gap_count`.
- `strict_visible_graph_count` / `strict_visible_graph_failed` - optional stricter debt accounting enabled by `--strict-visible-graph`.

Deletion remains review-gated. The hygiene pass may flag delete candidates, but it must not delete markdown content merely because it is loose.

## How to use it

### For Human Operators (CLI)
You can directly run the maintenance pass through the standard ChaseOS binary via PowerShell from the vault root:

```powershell
cd %CHASEOS_VAULT_ROOT%
.\.venv\Scripts\python.exe -m runtime.cli.main maintain
```

*(Use `--dry-run` to preview the modifications without altering the graph).*

To inspect loose-node review candidates without writing a Graph-Reports markdown report:

```powershell
python -m runtime.cli.vault_hygiene --json --review-loose-nodes
```

To show an operator-facing preview of the current loose-node queue, including
issue category, inferred node category, recommended decision, canonical/keep
target, and the expected effect, run:

```powershell
python -m runtime.cli.vault_hygiene --review-summary --review-summary-limit 20
```

This preview is non-mutating. It does not wire, archive, delete, replace, or
write keep-exclusion decisions. It labels raw scan issue counts separately from
active review-queue counts. It also includes `visible_graph_audit`, because a
review-clean vault can still contain visible graph debt such as unresolved
draft links or duplicate-stem ambiguity. A finalized clean active queue should
report `total_issues: 0`, `raw_issue_counts: {}`, and `review_count: 0`;
archived cleanup evidence under `99_ARCHIVE/Vault-Hygiene-Review/` should
remain connected through path-qualified review-archive index links rather than
reappearing as raw orphan debt. A stricter visible-graph closeout should also
drive the `visible_graph_audit` debt counters to zero or document why each
remaining class is intentionally tolerated. Use `--json` with
`--review-summary` when a runtime needs the same preview as structured data.

To run the integrated maintenance suite in machine-readable dry-run mode:

```powershell
python -m runtime.cli.main maintain --dry-run --json
```

`maintain --dry-run --json` suppresses the human markdown report write and returns the Stage 1 category and node-category counts inside `result.stage_1_vault_hygiene`.

### Runtime handoff guardrail

For future agent/runtime work, use the strict review gate after any pass that creates, renames, moves, or edits markdown files:

```powershell
python -m runtime.cli.vault_hygiene --json --review-loose-nodes --strict-review-gate --write-review-queue
```

Expected behavior:
- exit code `0` means no review-gated loose-node debt remains;
- exit code `2` means duplicate, partial, runtime, export/template, README, placeholder, or manual-review loose nodes remain;
- `--write-review-queue` writes the operator review artifacts under `07_LOGS/Graph-Reports/` and indexes the markdown queue from `Graph-Reports-Index.md`;
- duplicate candidates include canonical keep-path evidence such as canonical existence, canonical size, canonical wikilink count, heading count, and whether the canonical file is larger than the candidate stub.

Integrated maintenance can use the same guard:

```powershell
python -m runtime.cli.main maintain --dry-run --json --strict-graph-review
```

This is the recommended runtime handoff check. Runtimes should treat the non-zero review-required exit as blocked/review-required, not as a successful clean closeout. In JSON mode the result includes `status: "blocked_review_required"`, `review_required: true`, `errors: ["blocked_review_required"]`, and skipped downstream stages when Stage 1 blocks. The correct next step is to review the queue and decide per file: `keep_and_wire`, `keep_excluded`, `archive_after_review`, `archive_noncanonical_artifact`, `delete_after_review`, `replace_with_canonical`, or `manual_investigation`.

### Applying reviewed decisions

Decision application is intentionally separate from detection. A review queue is not a decision file. To apply cleanup, create a JSON file with explicit operator decisions:

```json
{
  "operator_approved": true,
  "approved_by": "Chase",
  "decisions": [
    {
      "file": "core_export/reports/latest/previews/06_AGENTS/Agent-Control-Plane.md",
      "decision": "replace_with_canonical",
      "approved": true,
      "expected_sha256": "<hash from review queue>",
      "canonical_path": "06_AGENTS/Agent-Control-Plane.md",
      "reason": "Canonical control-plane file is the kept version."
    }
  ]
}
```

Validate first:

```powershell
python -m runtime.cli.vault_hygiene --json --apply-review-decisions PATH_TO_DECISIONS.json
```

For an operator-readable execution plan before production cleanup, omit
`--json`:

```powershell
python -m runtime.cli.vault_hygiene --apply-review-decisions PATH_TO_DECISIONS.json
```

The decision plan is non-mutating unless `--execute-review-decisions` is also
present. It shows each file, decision, approval blockers, canonical file kept,
planned move/archive/delete/write target, and hash status. Unapproved proposal
files can validate structurally while still showing `execution_ready: false`
until `operator_approved: true` and per-decision approval fields are set.

To demonstrate the post-approval plan shape without creating an executable
decision file, write an approval-preview copy:

```powershell
python -m runtime.cli.vault_hygiene --write-approval-preview-copy PATH_TO_DECISIONS.json --approval-preview-output PATH_TO_PREVIEW.json
```

Approval-preview copies set approval fields so the plan can show the final
shape, but they also set `approval_preview_only: true` and
`production_execution_allowed: false`. They are blocked from
`--execute-review-decisions` and are for operator demonstration only.
Approval-preview JSON files are linked from `[[Graph-Reports-Index]]` so the
operator-visible pre-production plan remains discoverable.

### Validating unresolved-link decisions

Unresolved wikilinks are handled as missing-target decisions, not loose-node
archive/delete decisions. Generate an operator packet with:

```powershell
python -m runtime.cli.vault_hygiene --json --propose-unresolved-link-decisions --unresolved-proposal-max-items 50 --unresolved-proposal-path 07_LOGS\Graph-Reports\YYYY-MM-DD-unresolved-link-decision-proposal.json
```

Then edit the JSON deliberately. Valid row decisions are
`create_target_node`, `rename_link_to_existing_node`, `remove_link`, and
`defer`. Rows must be approved, top-level `operator_approved` must be true, and
the row must include the needed field such as `create_path` or
`replacement_target`.

Validate without mutating the vault:

```powershell
python -m runtime.cli.vault_hygiene --json --validate-unresolved-link-decisions PATH_TO_EDITED_UNRESOLVED_PROPOSAL.json
```

Expected valid status is `valid_non_executing` with
`production_execution_allowed: false`. Generated unedited proposals block. The
validator checks source hashes, current missing-link evidence, destination
rules, approvals, and planned writes; it does not create, rewrite, remove,
archive, or delete anything.

For an operator preview copy:

```powershell
python -m runtime.cli.vault_hygiene --json --write-unresolved-approval-preview-copy PATH_TO_EDITED_UNRESOLVED_PROPOSAL.json --unresolved-approval-preview-output PATH_TO_PREVIEW.json
```

The preview copy is indexed from `[[Graph-Reports-Index]]`, marks itself
`approval_preview_only: true`, and remains blocked from production execution.

### Validating ambiguous-link decisions

Unsafe duplicate-stem wikilinks are handled separately from loose-node
archive/delete decisions. Generate the review packet first:

```powershell
python -m runtime.cli.vault_hygiene --json --propose-ambiguous-link-decisions --ambiguous-proposal-max-items 50 --ambiguous-proposal-path 07_LOGS\Graph-Reports\YYYY-MM-DD-ambiguous-link-decision-proposal.json
```

Then edit the JSON deliberately. Each row must set a real `decision`, per-row
`approved: true`, and the decision-specific field such as `selected_target` or
`alias_path`. Validate the edited file with:

```powershell
python -m runtime.cli.vault_hygiene --json --validate-ambiguous-link-decisions PATH_TO_EDITED_AMBIGUOUS_PROPOSAL.json
```

Expected valid status is `valid_non_executing` with
`production_execution_allowed: false`. Generated proposals block until the
operator sets `operator_approved: true`, chooses each row decision, and approves
each row. This validator shows planned writes and blockers only; no
ambiguous-link production applier exists in this pass.

For a demonstration copy that still cannot execute:

```powershell
python -m runtime.cli.vault_hygiene --json --write-ambiguous-approval-preview-copy PATH_TO_EDITED_AMBIGUOUS_PROPOSAL.json --ambiguous-approval-preview-output PATH_TO_PREVIEW.json
```

The preview copy is indexed from `[[Graph-Reports-Index]]`, sets
`approval_preview_only: true`, and does not rewrite links, create aliases,
rename/merge duplicates, archive, or delete anything.

Execute only after validation:

```powershell
python -m runtime.cli.vault_hygiene --json --apply-review-decisions PATH_TO_DECISIONS.json --execute-review-decisions
```

Safety rules:
- destructive decisions require `operator_approved: true`, per-file `approved: true`, and `expected_sha256`;
- stale hashes block execution;
- protected canonical files cannot be handled destructively;
- `replace_with_canonical` archives the duplicate candidate under `99_ARCHIVE/Vault-Hygiene-Review/Replaced-Duplicates/`; it does not delete the candidate outright;
- `archive_noncanonical_artifact` moves review-only/runtime artifacts under `99_ARCHIVE/Vault-Hygiene-Review/Noncanonical-Artifacts/YYYY-MM-DD/` and appends `99_ARCHIVE/Vault-Hygiene-Review/Noncanonical-Artifacts/Noncanonical-Artifacts-Index.md`;
- `keep_excluded` writes a durable hash-bound decision to `runtime/graph/vault_hygiene_decisions.json`; if the file changes, it re-enters review. Hash-approved keep-excluded files are also wired to `99_ARCHIVE/Vault-Hygiene-Review/Keep-Excluded/Keep-Excluded-Index.md` when they would otherwise remain raw zero-degree visible nodes.
- production decision logs are timestamped per execution under `07_LOGS/Graph-Reports/Decision-Logs/` and linked from `[[Graph-Reports-Index]]`, so multiple approved applies on the same day do not overwrite earlier evidence.

To generate a small unapproved proposal batch from the current queue:

```powershell
python -m runtime.cli.vault_hygiene --json --propose-review-decisions --proposal-max-items 10 --proposal-categories duplicate_candidate,empty_placeholder,junk,review_only_artifact,runtime_markdown_loose,technical_readme_loose --proposal-path 07_LOGS\Graph-Reports\YYYY-MM-DD-loose-node-decision-proposal-small-batch.json
```

Proposal JSON files set `operator_approved: false` and leave destructive `approved` fields false. They are safe to review and validate, but should not be executed until the operator edits the JSON file deliberately. Proposal generation also writes a same-stem Markdown companion for operator review and indexes that Markdown note from `[[Graph-Reports-Index]]`.

Proposal generation suppresses files already archived under `99_ARCHIVE/Vault-Hygiene-Review/`. Those files are prior cleanup evidence, not new loose-node debt, and should not re-enter future approval batches unless they are moved back out of the review archive deliberately.

Proposal generation also suppresses files already staged in other unapproved `*proposal*.json` artifacts under `07_LOGS/Graph-Reports/`. This prevents the same loose node from appearing in multiple active batches. Regenerating the same proposal path does not self-suppress, and stale unapproved proposal files with an approved sibling such as `*-approved.json` are ignored as pending sources.

If a stale unapproved proposal is blocking a file whose current recommended
decision has changed, generate a conflict-resolving proposal with:

```powershell
python -m runtime.cli.vault_hygiene --json --propose-review-decisions --proposal-include-pending-conflicts --proposal-categories runtime_markdown_loose --proposal-path 07_LOGS\Graph-Reports\YYYY-MM-DD-loose-node-decision-proposal-conflict-resolution.json
```

This keeps normal duplicate suppression intact. It only includes pending files
when the current recommended decision differs from the older unapproved
decision, and each row records `supersedes_pending_proposal_sources` plus
`supersedes_pending_decisions` so the operator can see exactly which old
proposal is being overridden before execution.

If older unapproved proposals still reserve files whose current recommended
decision has not changed, consolidate them into a new clean batch with:

```powershell
python -m runtime.cli.vault_hygiene --json --propose-review-decisions --proposal-include-pending-same-decision --proposal-categories technical_readme_loose --proposal-path 07_LOGS\Graph-Reports\YYYY-MM-DD-loose-node-decision-proposal-same-decision-consolidation.json
```

This also keeps normal duplicate suppression intact unless the explicit flag is
used. It only includes pending files when the current recommended decision
matches the older unapproved decision, and each row records
`consolidates_pending_proposal_sources` plus
`consolidates_pending_decisions`. This is the cleanup lane for stale mixed
proposal batches after some rows have already been handled by newer approved
decision files.

### Current approved decision preview output

When an approved decision JSON is validated without `--execute-review-decisions`, the CLI prints a plain execution plan before any production cleanup. The expected shape is:

```text
ChaseOS Loose-Node Decision Plan

Mode: VALIDATE ONLY
Status: dry_run_valid
Approval preview only: false
Decisions: 10
Validated/applied count: 10
Blocked: 0
Skipped: 0
```

Each planned action shows the loose file, issue category, inferred node category, decision, `execution_ready`, canonical file kept, move/archive/delete/write targets, hash status, and plain effect. For `replace_with_canonical`, the canonical document is kept and the duplicate candidate is archived under `99_ARCHIVE/Vault-Hygiene-Review/Replaced-Duplicates/YYYY-MM-DD/` only when the operator later runs with `--execute-review-decisions`. For `archive_noncanonical_artifact`, the artifact is moved under `99_ARCHIVE/Vault-Hygiene-Review/Noncanonical-Artifacts/YYYY-MM-DD/` and linked from `Noncanonical-Artifacts-Index.md`.

### Indexes and runtime compatibility

Graph hygiene writes or updates these operator-facing index surfaces depending on mode:

- `07_LOGS/Graph-Reports/Graph-Reports-Index.md` for full reports, loose-node review queues, proposal Markdown companions, approval-preview notes, and approved decision review nodes.
- `runtime/graph/vault_hygiene_decisions.json` for durable hash-bound keep/archive/delete/replace decisions after execution.
- `99_ARCHIVE/Vault-Hygiene-Review/Noncanonical-Artifacts/Noncanonical-Artifacts-Index.md` for connected evidence of artifacts removed from canonical navigation by `archive_noncanonical_artifact`.
- `99_ARCHIVE/Vault-Hygiene-Review/Replaced-Duplicates/Replaced-Duplicates-Index.md` for connected evidence of duplicate candidates replaced by canonical documents.
- `07_LOGS/Graph-Reports/Decision-Logs/` for timestamped decision execution logs after production execution; these are indexed from `07_LOGS/Graph-Reports/Graph-Reports-Index.md`.
- `07_LOGS/Maintain-Runs/Maintain-Runs-Index.md` for integrated `os_hygiene_graph` maintenance run records.
- `07_LOGS/Daily/Daily-Index.md`, `07_LOGS/Build-Logs/Build-Logs-Index.md`, `99_ARCHIVE/Documentation-History/Documentation-History-Index.md`, and `07_LOGS/Agent-Activity/Agent-Activity-Index.md` are session writeback obligations for Codex/operator development passes, not automatic outputs of every hygiene scan.

Standalone use is current through:

```powershell
python -m runtime.cli.vault_hygiene --review-summary
python -m runtime.cli.vault_hygiene --json --review-loose-nodes --strict-review-gate --write-review-queue
python -m runtime.cli.vault_hygiene --fix --json --strict-review-gate
python -m runtime.cli.vault_hygiene --json --strict-visible-graph
python -m runtime.cli.main maintain --dry-run --json --strict-graph-review
```

OpenClaw compatibility has two active paths:

- `graph_hygiene` is the proposal-only AOR/bus task type for OpenClaw dispatch. It writes a bounded report and does not mutate vault content.
- `os_hygiene_graph` is the scheduled OpenClaw cron maintenance workflow from `runtime/schedules/sch-os-hygiene-graph-0300.yaml`. The scheduled wrapper exposes strict loose-node review counts and defaults to `strict_review_gate=true` with `allow_review_debt=false`, so OpenClaw cron runs return `blocked_review_required` and skip mutating stages while duplicate, placeholder, runtime, export/template, README, or manual-review loose nodes remain. When the vault is clean, the integrated maintenance dry run returns `ok: true`, `review_required: false`, and Stage 1 `total_issues: 0`. Operators can still run standalone previews and approved decision batches through `vault_hygiene.py` before allowing production cleanup.

### For Autonomous Agents (MCP Server)
If you are operating beneath the internal ChaseOS Server (via `mcp_server`), you possess explicit permission to trigger a maintenance sweep using your toolkit:

```json
{
  "tool": "vault.maintain",
  "params": {
    "dry_run": false
  }
}
```

This ensures zero-friction cleanup after major operational briefs, project scaffolding, or long-running context passes.

---
*Graph links: [[Vault-Map]] · [[OpenClaw-Runtime-Profile]] · [[Hermes-Runtime-Profile]]*
