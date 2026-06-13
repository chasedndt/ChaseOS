---
title: Graph Hygiene CLI and Hermes/OpenClaw Cron Runbook
type: operator-runbook
status: CURRENT
created: 2026-05-06
updated: 2026-05-14
scope: graph hygiene, vault maintenance, Hermes cron, OpenClaw fallback
runtime_surfaces:
  - vault_hygiene.py
  - runtime.cli.main maintain
  - os_hygiene_graph
  - Hermes cron
  - OpenClaw fallback cron
---

# Graph Hygiene CLI and Hermes/OpenClaw Cron Runbook

This is the practical setup and output guide for ChaseOS Graph Hygiene.

Graph Hygiene is the feature that keeps markdown nodes from drifting loose in
the vault. It scans graph links, classifies loose files, wires safe nodes into
the right index, and blocks duplicate/placeholder/runtime artifacts for operator
review before archive or delete decisions.

The scanner intentionally ignores repo-local scratch directories such as
`.codex`, `.codex_tmp`, `.codex-tmp`, `.pytest_cache`, and pytest fixture
folders. Temporary runtime/test markdown must not become graph debt or block
the strict review gate.

## What Runs What

There are three related paths:

| Path | Command / owner | Purpose | Mutates by default |
|------|-----------------|---------|--------------------|
| Standalone scanner | `python -m runtime.cli.vault_hygiene` | Inspect, fix auto-wirable nodes, generate proposals, apply approved decisions | No unless `--fix` or `--execute-review-decisions` |
| Integrated maintenance CLI | `python -m runtime.cli.main maintain` | Runs Stage 1 Graph Hygiene, Stage 2 Daily Hub linking, Stage 3 Provenance linking | Yes unless `--dry-run` |
| Hermes cron workflow | `sch-os-hygiene-graph-0300` -> `os_hygiene_graph` | Scheduled twice-daily maintenance through Hermes/AOR, with OpenClaw retained as fallback | Yes when clean; blocks when review debt exists |

Important distinction:

- `graph_hygiene` is the proposal/report AOR task. It is not the scheduled mutating cleanup lane.
- `os_hygiene_graph` is the scheduled maintenance workflow used by Hermes cron, with OpenClaw retained as fallback.

## Setup Checks

Run these from the vault root:

```powershell
cd <VAULT_ROOT>
```

Use the repo Python surface:

```powershell
python -m runtime.cli.main schedule validate --json
```

Expected valid output:

```json
{
  "ok": true,
  "action": "schedule.validate",
  "result": {
    "valid": true,
    "error_count": 0,
    "errors": []
  }
}
```

Confirm the ChaseOS schedule:

```powershell
python -m runtime.cli.main schedule show sch-os-hygiene-graph-0300 --json
```

Expected schedule facts:

```json
{
  "schedule_id": "sch-os-hygiene-graph-0300",
  "workflow_id": "os_hygiene_graph",
  "enabled": true,
  "shadow_mode": false,
  "cadence": {
    "type": "cron",
    "cron_expression": "0 3,15 * * *",
    "timezone": "America/New_York"
  },
  "trigger_source": "hermes",
  "runtime_adapter_target": "hermes",
  "delivery": {
    "primary_target": "vault-local",
    "vault_writeback_targets": [
      "07_LOGS/Maintain-Runs/",
      "07_LOGS/Hygiene-Reports/",
      "07_LOGS/Daily/"
    ]
  }
}
```

Meaning: Hermes is expected to run `os_hygiene_graph` every day at 03:00 ET
and 15:00 ET, with OpenClaw retained as the fallback runtime adapter. The run
is local-vault only and writes maintenance evidence back into the vault.

### 2026-05-14 Hermes Cron Failure Triage

The failed alert for job `0c42e5b6b468` showed two environment symptoms:

- Windows `cmd.exe` was launched while the caller current directory was a WSL
  UNC path under `\\wsl.localhost\Ubuntu\home\chaseos\runtimes\hermes-home\scripts`.
- The Windows ChaseOS virtual environment was missing `PyYAML`, causing
  `ModuleNotFoundError: No module named 'yaml'` before the workflow could run.

Hermes/Optimus repaired that runtime path later on 2026-05-14 by installing
`PyYAML` into the Windows ChaseOS venv and patching the WSL wrapper to `pushd`
into `<VAULT_ROOT>` before invoking
`cmd.exe`. Repo-side verification after the repair:

```powershell
python -m runtime.cli.main schedule validate --json
python -m runtime.cli.main schedule show sch-os-hygiene-graph-0300 --json
python -m runtime.cli.main run os_hygiene_graph --dry-run --json
python -m runtime.cli.main run os_hygiene_graph --json
```

Current expected result: the command layer exits successfully and writes the
Maintain-Runs evidence file. The workflow may still report
`blocked_review_required` inside the run record while review-gated loose nodes
exist. That is a governance gate, not a cron boot failure.

### 2026-05-14 Runtime Governance YAML Import Hardening

The full traceback showed the command could still fail at import time:

```text
from runtime.adapters.runtime_governance import ...
File "runtime/adapters/runtime_governance.py", line 15, in <module>
  import yaml
ModuleNotFoundError: No module named 'yaml'
```

Codex patched `runtime/adapters/runtime_governance.py` so PyYAML is optional
for the adapter-governance verifier. When PyYAML is present, it remains the
preferred parser. When it is absent, the verifier falls back to a local stdlib
YAML-subset parser that supports the governance manifest shapes used by:

- `runtime/policy/adapters/openclaw.yaml`
- `runtime/policy/adapters/hermes.yaml`
- `.chaseos/hermes_config.yaml`
- `runtime/openclaw/capabilities.yaml`

Verification included a fresh Python process with `sys.modules['yaml']=None`
before importing `runtime.cli.main`; `chaseos runtime adapter-governance --json`
returned `ok=true`. This closes the import-time `ModuleNotFoundError` path for
the graph hygiene cron command surface.

## Standalone CLI

### Operator Preview

Use this when you want a plain view of current graph hygiene state:

```powershell
python -m runtime.cli.vault_hygiene --review-summary --review-summary-limit 20
```

Machine-readable version:

```powershell
python -m runtime.cli.vault_hygiene --json --review-summary --review-summary-limit 20
```

Clean output shape:

```json
{
  "files_scanned": 3256,
  "total_issues": 0,
  "review_count": 0,
  "raw_issue_counts": {},
  "issue_counts": {},
  "active_review_issue_counts": {},
  "recommended_decision_counts": {},
  "visible_graph_audit": {
    "raw_zero_degree_count": 0,
    "unresolved_link_target_count": 0,
    "ambiguous_link_target_count": 0,
    "connected_duplicate_stem_count": 0,
    "semantic_hub_gap_count": 0
  },
  "items": []
}
```

If the vault has safe auto-wirable nodes only, expect this kind of output:

```json
{
  "total_issues": 3,
  "review_count": 0,
  "raw_issue_counts": {
    "loose_node": 3
  },
  "items": []
}
```

That is not duplicate/delete debt. It means there are safe index links to add.
Run the fix command below.

### Canonical Duplicate Routing

Ambiguous duplicate-looking links are only auto-rewritten when Graph Hygiene can
prove a canonical target. For high-volume ChaseOS control-plane and SOP nodes,
the CLI keeps an explicit canonical map. Current examples include:

```text
Runtime-InterAgent-Coordination-Bus -> 06_AGENTS/Runtime-InterAgent-Coordination-Bus
ChaseOS-Gate -> 06_AGENTS/ChaseOS-Gate
Autonomous-Operator-Runtime -> 06_AGENTS/Autonomous-Operator-Runtime
Agent-Security-Model -> 06_AGENTS/Agent-Security-Model
SIC-Architecture -> 06_AGENTS/SIC-Architecture
Research-Ingest-SOP -> 04_SOPS/Research-Ingest-SOP
Credential-Boundaries-SOP -> 04_SOPS/Credential-Boundaries-SOP
Untrusted-Input-Handling-SOP -> 04_SOPS/Untrusted-Input-Handling-SOP
Adapter-Compliance-Checklist -> 05_TEMPLATES/Adapter-Compliance-Checklist
Build-Log-SOP -> 04_SOPS/Build-Log-SOP
Agent-Audit-Log-Template -> 05_TEMPLATES/Agent-Audit-Log-Template
Agent-Failure-Ambiguity-SOP -> 04_SOPS/Agent-Failure-Ambiguity-SOP
Source-Note-Template -> 05_TEMPLATES/Source-Note-Template
Synthesis-Note-Template -> 05_TEMPLATES/Synthesis-Note-Template
```

If more than one real primary candidate exists, Graph Hygiene leaves the link
unmodified and requires review. It does not guess between active runtimes,
projects, or profiles.

### Unsafe Ambiguous-Link Review

Use this when the graph looks cleaner than Obsidian because ambiguous duplicate
stems still exist but Graph Hygiene cannot safely pick a canonical target:

```powershell
python -m runtime.cli.vault_hygiene --json --review-ambiguous-links --ambiguous-review-limit 50 --review-unresolved-links --unresolved-link-limit 50 --strict-review-gate --no-report
```

Expected output shape:

```json
{
  "total_issues": 78,
  "category_counts": {
    "ambiguous_link_target_review": 28,
    "unresolved_link_target": 50
  },
  "loose_node_review_count": 0,
  "strict_gate_failed": false
}
```

Meaning:

- `ambiguous_link_target_review` is a review-only issue for duplicate stems that
  have no safe canonical route.
- It does not enter the loose-node archive/delete queue.
- It does not mutate links.
- It tells the operator which source file and target need a path-qualified link,
  rename, alias node, or deferred decision.

The integrated maintenance CLI supports the same review surface:

```powershell
python -m runtime.cli.main maintain --dry-run --json --strict-graph-review --fix-semantic-hub-gaps --semantic-hub-gap-limit 50 --fix-ambiguous-links --ambiguous-link-limit 50 --review-ambiguous-links --ambiguous-review-limit 50 --review-unresolved-links --unresolved-link-limit 50
```

Hermes/OpenClaw AOR compatibility: the governed `os_hygiene_graph` workflow
accepts the same `review_ambiguous_links` and `ambiguous_review_limit` inputs.
Scheduled runs still default these inputs to `false` unless the workflow caller
enables them.

### Unresolved-Link Decision Proposals

Use this when Graph Hygiene finds wikilinks whose target does not exist yet.
These are not loose-node archive/delete decisions. They are link-target
decisions: create the missing target, rename the link to an existing node,
remove the source link, or defer.

Generate the operator packet:

```powershell
python -m runtime.cli.vault_hygiene --json --propose-unresolved-link-decisions --unresolved-proposal-max-items 50 --unresolved-proposal-path 07_LOGS\Graph-Reports\YYYY-MM-DD-unresolved-link-decision-proposal.json
```

Expected proposal output:

```json
{
  "proposal_kind": "unresolved_link_target_review",
  "operator_approved": false,
  "proposal_count": 50,
  "proposal_path": "07_LOGS/Graph-Reports/YYYY-MM-DD-unresolved-link-decision-proposal.json",
  "proposal_markdown_path": "07_LOGS/Graph-Reports/YYYY-MM-DD-unresolved-link-decision-proposal.md"
}
```

Each row includes the source file, current file hash, missing link target,
inferred category, source-line evidence, and these allowed decisions:

```text
create_target_node
rename_link_to_existing_node
remove_link
defer
```

Generated proposals are intentionally blocked. Before validation can pass, the
operator must set top-level `operator_approved: true`, choose a real row
`decision`, set row `approved: true`, and fill the decision-specific field:
`create_path` for `create_target_node`, `replacement_target` for
`rename_link_to_existing_node`, or a non-empty `reason` for `remove_link`.

Validate the edited file:

```powershell
python -m runtime.cli.vault_hygiene --json --validate-unresolved-link-decisions PATH_TO_EDITED_UNRESOLVED_PROPOSAL.json
```

Expected valid status is `valid_non_executing` with
`production_execution_allowed: false`. The validator checks the source path,
source hash, missing target evidence, destination existence rules, approval
fields, and planned writes. It does not create nodes, rewrite links, or remove
links.

For a demonstration copy that still cannot execute:

```powershell
python -m runtime.cli.vault_hygiene --json --write-unresolved-approval-preview-copy PATH_TO_EDITED_UNRESOLVED_PROPOSAL.json --unresolved-approval-preview-output PATH_TO_PREVIEW.json
```

The preview copy is indexed from `[[Graph-Reports-Index]]`, sets
`approval_preview_only: true`, keeps `production_execution_allowed: false`, and
exists only so the operator can inspect the planned write surface before any
future production applier exists.

### Ambiguous-Link Decision Proposals

Use this when unsafe ambiguous links need a governed operator packet instead of
manual inspection:

```powershell
python -m runtime.cli.vault_hygiene --json --propose-ambiguous-link-decisions --ambiguous-proposal-max-items 50 --ambiguous-proposal-path 07_LOGS\Graph-Reports\YYYY-MM-DD-ambiguous-link-decision-proposal.json
```

Expected proposal output:

```json
{
  "proposal_kind": "ambiguous_link_target_review",
  "operator_approved": false,
  "proposal_count": 28,
  "proposal_path": "07_LOGS/Graph-Reports/YYYY-MM-DD-ambiguous-link-decision-proposal.json",
  "proposal_markdown_path": "07_LOGS/Graph-Reports/YYYY-MM-DD-ambiguous-link-decision-proposal.md"
}
```

Each decision row includes the source file, current file hash, ambiguous
`link_target`, candidate paths, candidate hashes, inferred node categories,
review hints, and these allowed decisions:

```text
path_qualify_to_existing_node
create_alias_node
rename_or_merge_duplicate_node
remove_link
defer
```

The operator must edit the JSON deliberately. For a path-qualified fix, set:

```json
{
  "operator_approved": true,
  "approved_by": "Chase",
  "decisions": [
    {
      "file": "06_AGENTS/OpenClaw-Runtime-Profile.md",
      "link_target": "coordination_bridge",
      "decision": "path_qualify_to_existing_node",
      "approved": true,
      "selected_target": "runtime/openclaw/coordination_bridge.md"
    }
  ]
}
```

Validate the edited file before any future applier is considered:

```powershell
python -m runtime.cli.vault_hygiene --json --validate-ambiguous-link-decisions PATH_TO_EDITED_AMBIGUOUS_PROPOSAL.json
```

Valid non-executing output shape:

```json
{
  "status": "valid_non_executing",
  "valid": true,
  "operator_approved": true,
  "production_execution_allowed": false,
  "decision_count": 1,
  "blocked_count": 0,
  "planned_actions": [
    {
      "execution_ready": true,
      "effect": "path-qualify coordination_bridge in 06_AGENTS/OpenClaw-Runtime-Profile.md to runtime/openclaw/coordination_bridge.md",
      "writes": ["06_AGENTS/OpenClaw-Runtime-Profile.md"]
    }
  ]
}
```

Generated or unedited proposals are expected to block:

```text
status=blocked
operator_approved=false
blocked_count=<decision_count>
execution_blockers include: decision must be set explicitly, operator_approved must be true, per-row approved must be true
```

To demonstrate the post-approval shape without creating an executable file:

```powershell
python -m runtime.cli.vault_hygiene --json --write-ambiguous-approval-preview-copy PATH_TO_EDITED_AMBIGUOUS_PROPOSAL.json --ambiguous-approval-preview-output PATH_TO_PREVIEW.json
```

Approval-preview copies set `operator_approved: true`,
`approval_preview_only: true`, and `production_execution_allowed: false`. They
are indexed from `[[Graph-Reports-Index]]` and are demonstration artifacts only.
They do not rewrite links, create aliases, rename/merge duplicates, archive, or
delete anything.

### Visible Graph Audit

Use this when Obsidian still shows loose nodes, draft links, or duplicate-looking
targets even though the review queue looks clean:

```powershell
python -m runtime.cli.vault_hygiene --json --review-summary --review-summary-limit 20
```

The `visible_graph_audit` block reports graph-visible debt separately from the
review queue:

```json
{
  "raw_zero_degree_count": 2,
  "weak_degree_1_count": 325,
  "unresolved_link_target_count": 126,
  "ambiguous_link_target_count": 77,
  "connected_duplicate_stem_count": 21,
  "semantic_hub_gap_count": 292
}
```

Meaning:

- `raw_zero_degree_count` is the literal Obsidian-style loose-node count for files with no inbound or outbound graph links.
- `unresolved_link_target_count` catches draft/broken links whose target does not resolve to an existing markdown node.
- `ambiguous_link_target_count` catches wikilinks such as `[[Vault-Map]]` when multiple files can resolve to the same stem.
- `connected_duplicate_stem_count` catches duplicate-looking file stems even when they have some graph connection.
- `semantic_hub_gap_count` catches major agent/runtime/Studio/Pulse/SiteOps docs that are not linked back to one of the control-plane hubs.

Strict visible-graph mode:

```powershell
python -m runtime.cli.vault_hygiene --json --strict-visible-graph
```

Exit code `2` means graph-visible debt remains. This is stricter than the
normal review gate and is intended for operator audits, not for destructive
cleanup. It does not archive or delete files.

Hash-approved `keep_excluded` files are not silently ignored if they still look
loose in Obsidian. `--fix` wires them to:

```text
99_ARCHIVE/Vault-Hygiene-Review/Keep-Excluded/Keep-Excluded-Index.md
```

That holding index is reversible evidence, not canonical navigation.

Hash-approved `keep_excluded` runtime/readme docs are also excluded from
semantic hub-gap counts when the file hash still matches the approved decision.
This prevents a deliberate non-canonical technical README from remaining as a
false semantic hub-link gap after the operator already chose keep-excluded.

StrikeZone Crypto RSS staged captures are a special project/acquisition lane,
not generic runtime markdown. Files under
`runtime/acquisition/staging/strikezone/` with staged-capture metadata such as
`source_id: strikezone-rss-*`, `source_class: staged_capture`, and
`source_platform: rss` are wired by `--fix` to:

```text
runtime/acquisition/staging/strikezone/StrikeZone-RSS-Staging-Index.md
```

That index links back to `[[StrikeZone-Crypto-OS]]`, Trading Systems / Market Ops,
Crypto Perps, Trading Systems Engineering, and the StrikeZone acquisition guide.
The files remain raw context inputs and do not become canonical trading notes.

StrikeZone Crypto manual research templates are also a special local acquisition
lane. Markdown templates under:

```text
runtime/acquisition/manual/strikezone/templates/
```

are wired by `--fix` to:

```text
runtime/acquisition/manual/strikezone/README.md
```

They are reusable operator import templates, not duplicate runtime junk, and
should not be archived or deleted by the loose-node cleanup lane.

### 50-Item Visible Graph Cleanup Pass

Use this when the operator wants the maintenance feature to target more than raw
loose files. This is the current recommended preview for a real cleanup batch:

```powershell
python -m runtime.cli.main maintain --dry-run --json --strict-graph-review --fix-semantic-hub-gaps --semantic-hub-gap-limit 50 --fix-ambiguous-links --ambiguous-link-limit 50 --review-ambiguous-links --ambiguous-review-limit 50 --review-unresolved-links --unresolved-link-limit 50
```

Expected preview shape:

```json
{
  "ok": true,
  "result": {
    "status": "dry_run",
    "review_required": false,
    "stage_1_vault_hygiene": {
      "total_issues": 200,
      "category_counts": {
        "ambiguous_link_target": 50,
        "ambiguous_link_target_review": 50,
        "semantic_hub_gap": 50,
        "unresolved_link_target": 50
      },
      "loose_node_review_count": 0,
      "strict_gate_failed": false
    }
  }
}
```

Then apply the same batch through the standalone mutating path:

```powershell
python -m runtime.cli.vault_hygiene --fix --fix-semantic-hub-gaps --semantic-hub-gap-limit 50 --fix-ambiguous-links --ambiguous-link-limit 50 --review-ambiguous-links --ambiguous-review-limit 50 --review-unresolved-links --unresolved-link-limit 50 --json --strict-review-gate
```

As of the batch11 verification pass on 2026-05-06, this path was confirmed to:

- keep raw loose nodes at `0`;
- keep semantic hub gaps at `0`;
- pass strict review gate with `loose_node_review_count=0`;
- reduce ambiguous link source files from `119` to `66`;
- leave unresolved links in review-only mode, with no automatic target creation
  or guessed rewrites.

As of the batch12 verification pass on 2026-05-06, the same path also expanded
canonical duplicate routing to proven template/SOP export duplicates and reduced
ambiguous source files from `66` to `37`, while keeping raw loose nodes,
semantic hub gaps, and active review issues at `0`.

As of the batch13 verification pass on 2026-05-06, raw loose nodes and semantic
hub gaps remained `0`. Safe ambiguous auto-repair reduced the visible ambiguous
source files to `8`; the remaining unsafe ambiguous cases are now surfaced as
`ambiguous_link_target_review` rows instead of being hidden behind
`visible_graph_audit`. The bounded live preview surfaced `28` unsafe ambiguous
review rows and `50` unresolved-link review rows with `loose_node_review_count=0`.
The pass also safely wired three StrikeZone Crypto manual import templates back
to their local README after they appeared as raw zero-degree runtime templates.

What this does:

- Adds hub links to 50 semantically important agent/runtime/Studio/Pulse/SiteOps nodes that are connected but under-wired.
- Path-qualifies up to 50 safe ambiguous wikilink targets when a known canonical file exists.
- Surfaces up to 50 unsafe ambiguous wikilink targets as review-only issues.
- Surfaces up to 50 unresolved wikilink targets as review issues.
- Does not create guessed files for unresolved links.
- Does not archive or delete duplicate candidates without an operator-approved decision file.

Ambiguous-link repair is conservative. For example, `[[Vault-Map]]` can be
rewritten to `[[06_AGENTS/Vault-Map|Vault-Map]]` only when Graph Hygiene can map
the stem to a known canonical doc. Ambiguous links that do not have a safe
canonical mapping stay visible for later review.

Graph Hygiene can also infer a safe canonical target when an ambiguous stem has
exactly one real non-export, non-archive candidate after excluding generated
export previews, review archives, and runtime run artifacts. It still refuses to
guess when multiple primary candidates remain, such as runtime-specific
`agents.md` files.

To generate a review artifact for unsafe ambiguous duplicate-stem links:

```powershell
python -m runtime.cli.vault_hygiene --propose-ambiguous-link-decisions --ambiguous-proposal-max-items 50 --ambiguous-proposal-path 07_LOGS\Graph-Reports\YYYY-MM-DD-ambiguous-link-decision-proposal.json --json
```

Expected output shape:

```json
{
  "proposal_kind": "ambiguous_link_target_review",
  "proposal_count": 28,
  "operator_approved": false,
  "proposal_path": "07_LOGS/Graph-Reports/YYYY-MM-DD-ambiguous-link-decision-proposal.json",
  "proposal_markdown_path": "07_LOGS/Graph-Reports/YYYY-MM-DD-ambiguous-link-decision-proposal.md"
}
```

Each row is proposal-only and has allowed decisions:

```text
path_qualify_to_existing_node
create_alias_node
rename_or_merge_duplicate_node
remove_link
defer
```

The row includes candidate paths, candidate hashes, node categories, and review
hints such as `same_folder_candidate`, `same_top_level_candidate`,
`archive_candidate`, or `cross_graph_candidate`. Graph Hygiene does not execute
those decisions yet. The proposal is the operator review surface for deciding
which duplicate-stem node the original link meant.

The integrated maintenance CLI can create the same proposal during Stage 1:

```powershell
python -m runtime.cli.main maintain --dry-run --json --propose-ambiguous-link-decisions --ambiguous-proposal-max-items 50 --ambiguous-proposal-path 07_LOGS\Graph-Reports\YYYY-MM-DD-ambiguous-link-decision-proposal.json
```

Ambiguous-link proposals skip rows that already exist in older unapproved
ambiguous-link proposal JSON files. To intentionally regenerate rows already
staged elsewhere, add:

```powershell
--ambiguous-proposal-include-pending
```

Unresolved-link review is separate from the loose-node review queue. It tells the
operator that a target is missing or misspelled, but it does not block the strict
loose-node review gate unless there is also a real loose-node artifact that needs
archive/delete/replace approval.

To generate a review artifact for unresolved links:

```powershell
python -m runtime.cli.vault_hygiene --propose-unresolved-link-decisions --unresolved-proposal-max-items 50 --unresolved-proposal-path 07_LOGS\Graph-Reports\YYYY-MM-DD-unresolved-link-decision-proposal.json --json
```

Expected output shape:

```json
{
  "proposal_kind": "unresolved_link_target_review",
  "proposal_count": 50,
  "operator_approved": false,
  "proposal_path": "07_LOGS/Graph-Reports/YYYY-MM-DD-unresolved-link-decision-proposal.json",
  "proposal_markdown_path": "07_LOGS/Graph-Reports/YYYY-MM-DD-unresolved-link-decision-proposal.md"
}
```

Each row is proposal-only and has allowed decisions:

```text
create_target_node
rename_link_to_existing_node
remove_link
defer
```

Graph Hygiene does not currently execute those decisions. The proposal is the
operator review surface for deciding what each unresolved target actually means.

Unresolved-link proposals skip rows that already exist in older unapproved
unresolved-link proposal JSON files. This lets the operator generate batch 07,
batch 08, and later review packets without repeatedly seeing the same first 50
rows. To intentionally regenerate rows already staged elsewhere, add:

```powershell
--unresolved-proposal-include-pending
```

### Strict Review Gate

Use this after any runtime or agent writes markdown:

```powershell
python -m runtime.cli.vault_hygiene --json --review-loose-nodes --strict-review-gate
```

Clean output shape:

```json
{
  "total_issues": 0,
  "loose_node_review_count": 0,
  "loose_node_review_queue": [],
  "strict_gate_failed": false,
  "strict_gate_review_count": 0,
  "issues": []
}
```

Blocked output shape:

```json
{
  "loose_node_review_count": 4,
  "strict_gate_failed": true,
  "strict_gate_review_count": 4,
  "loose_node_review_queue": [
    {
      "file": "runtime/adapters/codex/runs/.../codex-stdout.md",
      "issue_category": "empty_placeholder",
      "recommended_action": "delete_candidate",
      "decision_hint": "delete_after_review",
      "file_sha256": "<expected hash>"
    }
  ]
}
```

Exit code behavior:

- `0`: no review-gated loose-node debt remains.
- `2`: review-gated loose nodes remain and require explicit decisions.

### Auto-Fix Safe Wiring

Use this for safe wiring only:

```powershell
python -m runtime.cli.vault_hygiene --fix --json --strict-review-gate
```

Expected clean result after safe wiring:

```json
{
  "total_issues": 0,
  "loose_node_review_count": 0,
  "strict_gate_failed": false,
  "nodes_wired": 0,
  "indexes_created": 0,
  "issues": []
}
```

If `nodes_wired` is greater than `0`, the command added graph links to indexes
or anchors. Re-run the review summary afterward and expect `total_issues=0`.

This command does not approve duplicate replacement or deletion decisions.

### Semantic Hub-Gap Repair

Use this when the visible graph audit shows that major agent/runtime/Studio/Pulse
docs are connected somewhere, but are not connected back to the control-plane
hubs. This is the lane for the problem where Obsidian shows important agentic
nodes floating away from `[[Agent-Control-Plane]]` and `[[Vault-Map]]`.

Preview the next bounded batch without mutation:

```powershell
python -m runtime.cli.main maintain --dry-run --json --strict-graph-review --fix-semantic-hub-gaps --semantic-hub-gap-limit 25
```

Expected preview shape:

```json
{
  "ok": true,
  "result": {
    "stage_1_vault_hygiene": {
      "total_issues": 25,
      "category_counts": {
        "semantic_hub_gap": 25
      },
      "visible_graph_audit": {
        "raw_zero_degree_count": 0,
        "semantic_hub_gap_count": 267
      }
    }
  }
}
```

Apply a standalone bounded batch:

```powershell
python -m runtime.cli.vault_hygiene --fix --fix-semantic-hub-gaps --semantic-hub-gap-limit 25 --json --strict-review-gate
```

Apply through the integrated maintenance CLI:

```powershell
python -m runtime.cli.main maintain --json --strict-graph-review --fix-semantic-hub-gaps --semantic-hub-gap-limit 25
```

Each repaired node receives a small footer:

```markdown
## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (YYYY-MM-DD): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
```

This is safe wiring. It does not delete files, archive files, replace
duplicates, or change canonical feature status. The default batch limit is `25`
so operators can inspect changes between passes.

OpenClaw compatibility:

- `os_hygiene_graph` keeps `fix_semantic_hub_gaps=false` by default.
- Daily cron remains compatible and will not start this lane unless the workflow
  input explicitly enables it.
- Standalone runtimes inside ChaseOS Studio can use the same flags when they
  need to repair visible graph hub gaps after writing agent/runtime docs.

## Applying Review Decisions

Detection and execution are intentionally separate.

Generate a proposal:

```powershell
python -m runtime.cli.vault_hygiene --json --propose-review-decisions --proposal-max-items 10 --proposal-categories duplicate_candidate,empty_placeholder,review_only_artifact,runtime_markdown_loose,technical_readme_loose --proposal-path 07_LOGS\Graph-Reports\YYYY-MM-DD-loose-node-decision-proposal.json
```

Validate a decision file without execution:

```powershell
python -m runtime.cli.vault_hygiene --json --apply-review-decisions 07_LOGS\Graph-Reports\DECISIONS.json
```

Human-readable plan:

```powershell
python -m runtime.cli.vault_hygiene --apply-review-decisions 07_LOGS\Graph-Reports\DECISIONS.json
```

Expected approved-plan shape:

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

Execute only an approved file:

```powershell
python -m runtime.cli.vault_hygiene --json --apply-review-decisions 07_LOGS\Graph-Reports\DECISIONS-approved.json --execute-review-decisions
```

Decision execution writes:

- `runtime/graph/vault_hygiene_decisions.json`
- `07_LOGS/Graph-Reports/Decision-Logs/YYYY-MM-DDTHHMMSS-loose-node-decision-apply.json`
- `07_LOGS/Graph-Reports/Graph-Reports-Index.md`
- archive indexes when files are archived:
  - `99_ARCHIVE/Vault-Hygiene-Review/Noncanonical-Artifacts/Noncanonical-Artifacts-Index.md`
  - `99_ARCHIVE/Vault-Hygiene-Review/Replaced-Duplicates/Replaced-Duplicates-Index.md`

Delete rules:

- delete requires `operator_approved: true`
- destructive rows require per-file `approved: true`
- destructive rows require `expected_sha256`
- stale hash blocks execution
- protected canonical files cannot be deleted by this lane

## Integrated Maintenance CLI

Use this as the local smoke for the same path OpenClaw cron depends on:

```powershell
python -m runtime.cli.main maintain --dry-run --json --strict-graph-review
```

Clean output shape:

```json
{
  "ok": true,
  "action": "maintain",
  "result": {
    "status": "dry_run",
    "review_required": false,
    "errors": [],
    "stage_1_vault_hygiene": {
      "total_issues": 0,
      "loose_node_review_count": 0,
      "strict_gate_failed": false,
      "strict_gate_review_count": 0
    },
    "stage_2_daily_hub": {
      "skipped": false
    },
    "stage_3_provenance": {
      "skipped": false
    }
  }
}
```

Blocked output shape:

```json
{
  "ok": false,
  "action": "maintain",
  "result": {
    "status": "blocked_review_required",
    "review_required": true,
    "errors": ["blocked_review_required"],
    "stage_1_vault_hygiene": {
      "loose_node_review_count": 4,
      "strict_gate_failed": true
    },
    "stage_2_daily_hub": {
      "skipped": true
    },
    "stage_3_provenance": {
      "skipped": true
    }
  }
}
```

Use the standalone `vault_hygiene` review summary and decision proposal commands
to clear review debt before allowing mutation.

## OpenClaw Cron Behavior

Schedule source:

```text
runtime/schedules/sch-os-hygiene-graph-0300.yaml
```

Expected schedule:

```text
schedule_id: sch-os-hygiene-graph-0300
workflow_id: os_hygiene_graph
trigger_source: openclaw
runtime_adapter_target: openclaw
cron_expression: 0 3 * * *
timezone: America/New_York
enabled: true
shadow_mode: false
```

OpenClaw should invoke the governed workflow path:

```text
chaseos run os_hygiene_graph
```

The workflow defaults are:

```text
strict_review_gate=true
allow_review_debt=false
dry_run=false
fix_semantic_hub_gaps=false
fix_ambiguous_links=false
review_unresolved_links=false
review_ambiguous_links=false
```

Expected clean scheduled run:

- Stage 1 runs Graph Hygiene.
- If there are only safe auto-fixable graph links, they are wired.
- If the OpenClaw workflow inputs enable semantic/ambiguous/unresolved passes,
  Stage 1 uses the same bounded 50-item lanes described above unless the caller
  supplies a different limit.
- Stage 2 updates daily hub links.
- Stage 3 updates runtime provenance links.
- A run record is written.

Expected clean run record:

```text
07_LOGS/Maintain-Runs/YYYY-MM-DD-os-hygiene-graph-run.md
```

Expected clean run record status:

```yaml
workflow_id: os_hygiene_graph
status: complete
```

Expected blocked scheduled run:

- Stage 1 detects review-gated loose nodes.
- The workflow returns `blocked_review_required`.
- Stage 2 and Stage 3 are skipped.
- No archive/delete/replacement decision is executed.
- A run record is still written so the operator can see the failure.

Expected blocked run record status:

```yaml
workflow_id: os_hygiene_graph
status: blocked_review_required
```

The blocked run record should include:

```text
review_gated_loose_nodes=<count>
duplicate_candidates=<count>
Stage 2: Daily Hub Linker | skipped
Stage 3: Provenance Linker | skipped
```

## What To Check After Cron Runs

Check the maintain run record:

```powershell
Get-Content 07_LOGS\Maintain-Runs\YYYY-MM-DD-os-hygiene-graph-run.md
```

Check the current graph state:

```powershell
python -m runtime.cli.vault_hygiene --json --review-summary --review-summary-limit 20
```

Clean target:

```text
total_issues=0
review_count=0
raw_issue_counts={}
```

Check integrated maintenance:

```powershell
python -m runtime.cli.main maintain --dry-run --json --strict-graph-review
```

Clean target:

```text
ok=true
review_required=false
stage_1_vault_hygiene.total_issues=0
stage_1_vault_hygiene.loose_node_review_count=0
```

## What Not To Expect

- The cron job should not silently delete files.
- Duplicate candidates should not be deleted outright; replacement archives the duplicate under `99_ARCHIVE/Vault-Hygiene-Review/Replaced-Duplicates/`.
- Runtime/readme artifacts should not be forced into canonical graph navigation without review.
- Review archives are not active graph debt when connected through their archive indexes.
- A clean CLI dry run does not prove the cron executed; it proves the command path cron depends on is healthy.

## Troubleshooting

If `raw_issue_counts` has only `loose_node` and `review_count=0`:

```powershell
python -m runtime.cli.vault_hygiene --fix --json --strict-review-gate
```

If `loose_node_review_count > 0`:

```powershell
python -m runtime.cli.vault_hygiene --review-summary --review-summary-limit 25
python -m runtime.cli.vault_hygiene --json --propose-review-decisions --proposal-max-items 25 --proposal-categories duplicate_candidate,empty_placeholder,review_only_artifact,runtime_markdown_loose,technical_readme_loose --proposal-path 07_LOGS\Graph-Reports\YYYY-MM-DD-loose-node-decision-proposal.json
```

If schedule validation fails:

```powershell
python -m runtime.cli.main schedule validate --json
python -m runtime.cli.main schedule show sch-os-hygiene-graph-0300 --json
```

If OpenClaw did not run at 03:00 ET, check the OpenClaw runtime side, but do
not edit the schedule YAML manually just to toggle it. Use the schedule CLI.

## Related Nodes

- [[ChaseOS-Vault-Maintenance]]
- [[Vault-Map]]
- [[OpenClaw-Runtime-Profile]]
- [[Hermes-Runtime-Profile]]
- [[Maintain-Runs-Index]]
- [[Graph-Reports-Index]]
