"""
os_hygiene_graph.py -- ChaseOS AOR Phase 9

Governed AOR workflow handler for the 3-stage OS graph maintenance suite.

Executes vault_hygiene -> daily_hub_linker -> provenance_linker in sequence,
captures structured metrics from each stage, writes a run record to
07_LOGS/Maintain-Runs/, and returns AOR-compatible writebacks.

This is the governed execution path. The direct CLI path is `chaseos maintain`.
Both invoke the same underlying modules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.workflows.hygiene_snapshot import (
    collect_pre_snapshot,
    compute_diff_records,
    write_diff_json,
    write_snapshot_dir,
)


class WorkflowExecutionError(RuntimeError):
    """Fail-closed workflow error for bounded AOR handlers."""


def run_os_hygiene_graph(inputs: dict[str, Any], vault_root: Path) -> dict[str, Any]:
    """
    AOR handler for os_hygiene_graph.

    Inputs:
        dry_run: If True, report only; no mutations. Default: False.
        strict_review_gate: If True, block scheduled mutation when Stage 1 finds
            review-gated loose nodes. Default: True.
        allow_review_debt: Explicit override for controlled/manual runs.
            Default: False.
        fix_semantic_hub_gaps: If True, repair a bounded batch of major
            agent/runtime docs missing governance hub links. Default: False.
        semantic_hub_gap_limit: Maximum semantic hub gaps to repair in one run.
            Default: 50.
        fix_ambiguous_links: If True, path-qualify a bounded batch of safe
            ambiguous wikilinks to known canonical docs. Default: False.
        ambiguous_link_limit: Maximum ambiguous links to repair in one run.
            Default: 50.
        review_ambiguous_links: If True, surface ambiguous wikilinks with no
            safe canonical target as review issues. Default: False.
        ambiguous_review_limit: Maximum unsafe ambiguous links to surface in
            one run. Default: 50.
        propose_ambiguous_link_decisions: If True, write an unapproved
            ambiguous-link decision proposal artifact. Default: False.
        ambiguous_proposal_path: Optional proposal output path.
        ambiguous_proposal_max_items: Maximum ambiguous-link rows in proposal.
            Default: 50.
        ambiguous_proposal_include_pending: If True, include rows already
            staged in older unapproved ambiguous-link proposals. Default: False.
        review_unresolved_links: If True, surface a bounded batch of unresolved
            wikilinks as review issues. Default: False.
        unresolved_link_limit: Maximum unresolved links to surface in one run.
            Default: 50.

    Returns AOR writeback dict with stage metrics and a Maintain-Runs record.
    """
    import runtime.cli.daily_hub_linker as daily_hub_mod
    import runtime.cli.provenance_linker as provenance_mod
    import runtime.cli.vault_hygiene as hygiene_mod
    from runtime.cli.vault_hygiene import apply_fixes, scan_vault

    dry_run: bool = bool(inputs.get("dry_run", False))
    strict_review_gate: bool = bool(inputs.get("strict_review_gate", True))
    allow_review_debt: bool = bool(inputs.get("allow_review_debt", False))
    fix_semantic_hub_gaps: bool = bool(inputs.get("fix_semantic_hub_gaps", False))
    semantic_hub_gap_limit = max(0, int(inputs.get("semantic_hub_gap_limit", 50)))
    fix_ambiguous_links: bool = bool(inputs.get("fix_ambiguous_links", False))
    ambiguous_link_limit = max(0, int(inputs.get("ambiguous_link_limit", 50)))
    review_ambiguous_links: bool = bool(inputs.get("review_ambiguous_links", False))
    ambiguous_review_limit = max(0, int(inputs.get("ambiguous_review_limit", 50)))
    propose_ambiguous_link_decisions: bool = bool(inputs.get("propose_ambiguous_link_decisions", False))
    ambiguous_proposal_path = inputs.get("ambiguous_proposal_path")
    ambiguous_proposal_max_items = max(0, int(inputs.get("ambiguous_proposal_max_items", 50)))
    ambiguous_proposal_include_pending: bool = bool(inputs.get("ambiguous_proposal_include_pending", False))
    review_unresolved_links: bool = bool(inputs.get("review_unresolved_links", False))
    unresolved_link_limit = max(0, int(inputs.get("unresolved_link_limit", 50)))
    if propose_ambiguous_link_decisions:
        review_ambiguous_links = True
        if not ambiguous_proposal_include_pending:
            pending_count = len(hygiene_mod._pending_ambiguous_link_proposal_keys(
                vault_root,
                exclude_rel=str(ambiguous_proposal_path) if ambiguous_proposal_path else None,
            ))
            ambiguous_review_limit = max(
                ambiguous_review_limit,
                ambiguous_proposal_max_items + pending_count,
            )
        else:
            ambiguous_review_limit = max(ambiguous_review_limit, ambiguous_proposal_max_items)
    fix = not dry_run

    run_start = datetime.now(timezone.utc)
    date_str = run_start.astimezone().strftime("%Y-%m-%d")
    timestamp_str = run_start.astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

    try:
        if fix_semantic_hub_gaps or fix_ambiguous_links or review_ambiguous_links or review_unresolved_links:
            hygiene_report = scan_vault(
                vault_root,
                semantic_hub_fix_limit=semantic_hub_gap_limit,
                ambiguous_link_fix_limit=ambiguous_link_limit if fix_ambiguous_links else 0,
                ambiguous_link_review_limit=ambiguous_review_limit if review_ambiguous_links else 0,
                unresolved_link_review_limit=unresolved_link_limit if review_unresolved_links else 0,
            )
        else:
            hygiene_report = scan_vault(vault_root)
        review_queue = hygiene_mod.build_loose_node_review_queue(hygiene_report, vault_root)
        strict_blocked = bool(strict_review_gate and review_queue and not allow_review_debt)
        ambiguous_link_proposal = None
        if propose_ambiguous_link_decisions:
            ambiguous_link_proposal = hygiene_mod.propose_ambiguous_link_decisions(
                hygiene_report,
                vault_root,
                output_path=str(ambiguous_proposal_path) if ambiguous_proposal_path else None,
                max_items=ambiguous_proposal_max_items,
                include_pending=ambiguous_proposal_include_pending,
            )
        _pre_snapshot: dict[str, str] = {}
        _snapshot_dir: Path | None = None
        _diff_records: list[dict] = []

        if fix and not strict_blocked:
            # Pre-mutation snapshot: hash files that apply_fixes() will touch
            _pre_snapshot = collect_pre_snapshot(vault_root, hygiene_report)
            if _pre_snapshot:
                _snapshot_dir = write_snapshot_dir(vault_root, _pre_snapshot, date_str)

            apply_fixes(vault_root, hygiene_report, delete_junk=False)

            # Post-mutation diff
            if _pre_snapshot:
                _diff_records = compute_diff_records(vault_root, _pre_snapshot)
                if _snapshot_dir is not None:
                    write_diff_json(_snapshot_dir, _diff_records)

            hygiene_dir = vault_root / "07_LOGS" / "Hygiene-Reports"
            hygiene_dir.mkdir(parents=True, exist_ok=True)
            report_text = hygiene_mod.render_report(hygiene_report, vault_root)
            (hygiene_dir / f"{date_str}-vault-hygiene-report.md").write_text(
                report_text, encoding="utf-8"
            )

        _modified_count = sum(1 for r in _diff_records if r["change_type"] == "modified")
        _deleted_count = sum(1 for r in _diff_records if r["change_type"] == "deleted")
        _snapshot_dir_rel = (
            str(_snapshot_dir.relative_to(vault_root)).replace("\\", "/")
            if _snapshot_dir is not None
            else None
        )

        stage_1 = {
            "files_scanned": hygiene_report.files_scanned,
            "files_fixed": hygiene_report.files_fixed,
            "wikilinks_fixed": hygiene_report.wikilinks_fixed,
            "nodes_wired": hygiene_report.nodes_wired,
            "junk_flagged": hygiene_report.junk_flagged,
            "category_counts": hygiene_mod.summarize_issues(hygiene_report),
            "node_category_counts": hygiene_mod.summarize_node_categories(hygiene_report),
            "loose_node_review_count": len(review_queue),
            "strict_gate_failed": strict_blocked,
            "strict_gate_review_count": len(review_queue),
            "semantic_hub_fix_requested": fix_semantic_hub_gaps,
            "semantic_hub_gap_limit": semantic_hub_gap_limit,
            "ambiguous_link_fix_requested": fix_ambiguous_links,
            "ambiguous_link_limit": ambiguous_link_limit,
            "ambiguous_link_review_requested": review_ambiguous_links,
            "ambiguous_review_limit": ambiguous_review_limit,
            "ambiguous_link_proposal_requested": propose_ambiguous_link_decisions,
            "ambiguous_link_proposal": ambiguous_link_proposal,
            "unresolved_link_review_requested": review_unresolved_links,
            "unresolved_link_limit": unresolved_link_limit,
            "visible_graph_audit": hygiene_report.visible_graph_audit,
            "snapshot_taken": bool(_pre_snapshot),
            "snapshot_dir": _snapshot_dir_rel,
            "snapshot_files_count": len(_pre_snapshot),
            "snapshot_modified_count": _modified_count,
            "snapshot_deleted_count": _deleted_count,
            "snapshot_diff_records": _diff_records,
        }
    except Exception as exc:  # noqa: BLE001
        raise WorkflowExecutionError(f"Stage 1 vault hygiene failed: {exc}") from exc

    if stage_1["strict_gate_failed"]:
        run_end = datetime.now(timezone.utc)
        duration_s = round((run_end - run_start).total_seconds(), 1)
        run_record_path = f"07_LOGS/Maintain-Runs/{date_str}-os-hygiene-graph-run.md"
        duplicate_count = stage_1["category_counts"].get("duplicate_candidate", 0)
        run_record = f"""---
workflow_id: os_hygiene_graph
run_date: {date_str}
status: blocked_review_required
duration_seconds: {duration_s}
---

# OS Graph Maintenance Run - {date_str}

**Status:** BLOCKED - review-gated loose nodes remain
**Run started:** {timestamp_str}
**Duration:** {duration_s}s

---

## Stage Results

| Stage | Status | Files Scanned | Detail |
|-------|--------|--------------|--------|
| Stage 1: Vault Hygiene | blocked_review_required | {stage_1["files_scanned"]} | review_gated_loose_nodes={stage_1["loose_node_review_count"]}, duplicate_candidates={duplicate_count} |
| Stage 2: Daily Hub Linker | skipped | 0 | skipped because Stage 1 strict review gate failed |
| Stage 3: Provenance Linker | skipped | 0 | skipped because Stage 1 strict review gate failed |

---

## Operator Follow-Up

- Run `python -m runtime.cli.vault_hygiene --review-summary` for a plain preview.
- Review and apply explicit decision JSON batches before allowing scheduled mutation.
- Use `allow_review_debt=true` only for controlled manual runs where the operator accepts remaining review debt.

---

*Graph links: [[OpenClaw-Runtime-Profile]] - [[Hermes-Runtime-Profile]] - [[Maintain-Runs-Index]]*
"""
        return {
            "handler_status": "blocked_review_required",
            "status": "blocked_review_required",
            "writebacks": [{"path": run_record_path, "content": run_record}],
            "stage_1_vault_hygiene": stage_1,
            "stage_2_daily_hub": {
                "files_scanned": 0,
                "dates_found": 0,
                "notes_created": 0,
                "notes_updated": 0,
                "backlinks_added": 0,
                "index_updated": False,
                "skipped": True,
            },
            "stage_3_provenance": {
                "files_scanned": 0,
                "files_modified": 0,
                "links_added": {},
                "skipped": True,
            },
            "run_record_path": run_record_path,
            "dry_run": dry_run,
            "duration_seconds": duration_s,
            "strict_review_gate": strict_review_gate,
            "allow_review_debt": allow_review_debt,
        }

    try:
        hub_report = daily_hub_mod.run(fix=fix, update_index=fix)
        stage_2 = {
            "files_scanned": hub_report.files_scanned,
            "dates_found": hub_report.dates_found,
            "notes_created": hub_report.notes_created,
            "notes_updated": hub_report.notes_updated,
            "backlinks_added": hub_report.backlinks_added,
            "index_updated": hub_report.index_updated,
        }
    except Exception as exc:  # noqa: BLE001
        raise WorkflowExecutionError(f"Stage 2 daily hub linker failed: {exc}") from exc

    try:
        prov_report = provenance_mod.run(fix=fix)
        stage_3 = {
            "files_scanned": getattr(prov_report, "files_scanned", 0),
            "files_modified": getattr(prov_report, "files_modified", 0),
            "links_added": dict(getattr(prov_report, "links_added", {})),
        }
    except Exception as exc:  # noqa: BLE001
        raise WorkflowExecutionError(f"Stage 3 provenance linker failed: {exc}") from exc

    run_end = datetime.now(timezone.utc)
    duration_s = round((run_end - run_start).total_seconds(), 1)
    links_added_total = sum(stage_3["links_added"].values())
    link_detail = "No links added."
    if stage_3["links_added"]:
        link_detail = "\n".join(f"- Added [[{key}]] x {value}" for key, value in stage_3["links_added"].items())

    _snapshot_section = ""
    if stage_1["snapshot_taken"]:
        _snapshot_section = f"""
---

## Pre-Mutation Snapshot

**Snapshot directory:** `{stage_1["snapshot_dir"]}`
**Files snapshotted:** {stage_1["snapshot_files_count"]}
**Files modified by Stage 1:** {stage_1["snapshot_modified_count"]}
**Files deleted by Stage 1:** {stage_1["snapshot_deleted_count"]}

Diff log: `{stage_1["snapshot_dir"]}/diff_log.json`
"""

    status = "dry_run" if dry_run else "complete"
    run_record = f"""---
workflow_id: os_hygiene_graph
run_date: {date_str}
status: {status}
duration_seconds: {duration_s}
snapshot_dir: {stage_1["snapshot_dir"] or "none"}
---

# OS Graph Maintenance Run - {date_str}

**Status:** {"DRY RUN (no mutations)" if dry_run else "Complete"}
**Run started:** {timestamp_str}
**Duration:** {duration_s}s

---

## Stage Results

| Stage | Files Scanned | Fixed / Created | Detail |
|-------|--------------|-----------------|--------|
| Stage 1: Vault Hygiene | {stage_1["files_scanned"]} | {stage_1["files_fixed"]} | wikilinks_fixed={stage_1["wikilinks_fixed"]}, nodes_wired={stage_1["nodes_wired"]}, review_gated_loose_nodes={stage_1["loose_node_review_count"]} |
| Stage 2: Daily Hub Linker | {stage_2["files_scanned"]} | {stage_2["notes_created"] + stage_2["notes_updated"]} | notes_created={stage_2["notes_created"]}, backlinks_added={stage_2["backlinks_added"]} |
| Stage 3: Provenance Linker | {stage_3["files_scanned"]} | {stage_3["files_modified"]} | links_added={links_added_total} |

---

## Stage 3 Link Detail

{link_detail}
{_snapshot_section}
---

*Graph links: [[OpenClaw-Runtime-Profile]] - [[Hermes-Runtime-Profile]] - [[Maintain-Runs-Index]]*
"""

    run_record_path = f"07_LOGS/Maintain-Runs/{date_str}-os-hygiene-graph-run.md"

    return {
        "handler_status": status,
        "status": status,
        "writebacks": [{"path": run_record_path, "content": run_record}],
        "stage_1_vault_hygiene": stage_1,
        "stage_2_daily_hub": stage_2,
        "stage_3_provenance": stage_3,
        "run_record_path": run_record_path,
        "dry_run": dry_run,
        "duration_seconds": duration_s,
        "strict_review_gate": strict_review_gate,
        "allow_review_debt": allow_review_debt,
    }
