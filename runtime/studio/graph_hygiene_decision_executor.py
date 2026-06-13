"""
graph_hygiene_decision_executor.py — ChaseOS Studio

Phase 3: approved decision executor for Graph Hygiene.

Reads an approved decision draft and applies the decisions to vault files.

Decision handling per type:
  - keep_and_wire / keep_excluded / replace_with_canonical / manual_investigation
      → annotation record only; no file move
  - archive_after_review / archive_noncanonical_artifact
      → move file to 99_ARCHIVE/Loose-Nodes-Archive/YYYYMMDD/
  - delete_after_review
      → SOFT DELETE: move to 99_ARCHIVE/Loose-Nodes-Archive/YYYYMMDD/Deleted/
        (permanent rm never performed by Studio)

Writes execution log to: 07_LOGS/Graph-Reports/Decision-Logs/

Authority:
  - Requires approval ID gated through StudioService
  - Only touches vault files after explicit approval
  - Never rewrites graph indexes
  - Never calls model providers or connectors
  - delete_after_review = soft-delete (archive), never permanent rm
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR_REL  = Path("07_LOGS") / "Graph-Reports" / "Decision-Logs"
ARCHIVE_BASE = Path("99_ARCHIVE") / "Loose-Nodes-Archive"
EXECUTOR_VER = "studio.graph_hygiene_decision_executor.v1"

# Decisions that produce an annotation record only (no file movement)
_ANNOTATION_ONLY = frozenset({
    "keep_and_wire",
    "keep_excluded",
    "replace_with_canonical",
    "manual_investigation",
})
# Decisions that move files to archive
_ARCHIVE_ACTIONS = frozenset({"archive_after_review", "archive_noncanonical_artifact"})
# Soft-delete: move to Deleted sub-folder inside archive, never permanent rm
_SOFT_DELETE = frozenset({"delete_after_review"})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def execute_approved_decisions(
    vault_root: Path,
    draft_rel_path: str,
    approval_id: str,
) -> dict:
    """
    Apply all decisions recorded in an approved decision draft.

    Parameters
    ----------
    vault_root      : Path
    draft_rel_path  : str  relative vault path to the decision draft JSON
    approval_id     : str  approval ID that authorised this execution

    Returns
    -------
    dict with: ok, log_path, applied_count, skipped_count, error_count,
               before_count, after_count, results
    """
    vault_root = Path(vault_root)
    now = datetime.now(tz=timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H%M%S")

    # -- Load and validate draft ------------------------------------------
    from runtime.studio.graph_hygiene_decision_draft import load_decision_draft
    draft = load_decision_draft(vault_root, draft_rel_path)
    if draft is None:
        return _fail("Draft not found or invalid path", draft_rel_path)
    if (draft.get("authority") or {}).get("applied"):
        return _fail("Draft has already been applied", draft_rel_path)

    decisions = draft.get("decisions") or []
    before_count = len(decisions)

    # -- Destination directories ------------------------------------------
    date_str    = now.strftime("%Y%m%d")
    archive_dir = vault_root / ARCHIVE_BASE / date_str
    deleted_dir = archive_dir / "Deleted"

    results: list[dict] = []
    applied_count = 0
    skipped_count = 0
    error_count   = 0

    # -- Apply each decision -----------------------------------------------
    for item in decisions:
        rel = item.get("path", "")
        decision = item.get("decision", "")
        op_note  = item.get("operator_note", "")

        if decision in _ANNOTATION_ONLY:
            # Nothing to move — record the decision as an annotation
            results.append({
                "path":     rel,
                "decision": decision,
                "action":   "annotation_written",
                "note":     op_note or f"Annotated: {decision}",
            })
            applied_count += 1

        elif decision in _ARCHIVE_ACTIONS:
            r = _move_file(vault_root, rel, archive_dir, decision, op_note)
            results.append(r)
            if r["action"] == "archived":
                applied_count += 1
            elif r["action"].startswith("skipped"):
                skipped_count += 1
            else:
                error_count += 1

        elif decision in _SOFT_DELETE:
            r = _move_file(vault_root, rel, deleted_dir, decision, op_note,
                           soft_delete=True)
            results.append(r)
            if r["action"] == "soft_deleted":
                applied_count += 1
            elif r["action"].startswith("skipped"):
                skipped_count += 1
            else:
                error_count += 1

        else:
            results.append({
                "path":     rel,
                "decision": decision,
                "action":   "skipped_unknown_type",
                "note":     f"Unrecognised decision type: {decision!r}",
            })
            skipped_count += 1

    after_count = max(0, before_count - applied_count)

    # -- Mark draft as applied --------------------------------------------
    draft_abs = vault_root / draft_rel_path
    try:
        draft["authority"]["applied"]    = True
        draft["authority"]["applied_at"] = now.isoformat()
        draft["authority"]["approval_id"] = approval_id
        draft["status"] = "applied"
        draft_abs.write_text(
            json.dumps(draft, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        pass  # Non-fatal; the log still records the result

    # -- Write decision log -----------------------------------------------
    log_filename = f"{ts}-graph-hygiene-decision-log.json"
    log_dir = vault_root / LOG_DIR_REL
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_filename

    log_data = {
        "surface":       "studio_graph_hygiene_decision_log",
        "model_version": EXECUTOR_VER,
        "executed_at":   now.isoformat(),
        "approval_id":   approval_id,
        "draft_path":    draft_rel_path,
        "before_count":  before_count,
        "after_count":   after_count,
        "applied_count": applied_count,
        "skipped_count": skipped_count,
        "error_count":   error_count,
        "results":       results,
    }
    log_path.write_text(
        json.dumps(log_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "ok":            True,
        "log_path":      str(LOG_DIR_REL / log_filename),
        "draft_path":    draft_rel_path,
        "approval_id":   approval_id,
        "before_count":  before_count,
        "after_count":   after_count,
        "applied_count": applied_count,
        "skipped_count": skipped_count,
        "error_count":   error_count,
        "results":       results,
    }


def list_decision_logs(vault_root: Path) -> dict:
    """Return summary list of all decision logs, newest first."""
    vault_root = Path(vault_root)
    log_dir = vault_root / LOG_DIR_REL

    if not log_dir.exists():
        return {"logs": [], "total": 0}

    logs = []
    for p in sorted(log_dir.glob("*-graph-hygiene-decision-log.json"), reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            logs.append({
                "filename":      p.name,
                "rel_path":      str(LOG_DIR_REL / p.name),
                "executed_at":   data.get("executed_at", ""),
                "draft_path":    data.get("draft_path", ""),
                "before_count":  data.get("before_count", 0),
                "applied_count": data.get("applied_count", 0),
                "skipped_count": data.get("skipped_count", 0),
                "error_count":   data.get("error_count", 0),
            })
        except (OSError, json.JSONDecodeError):
            logs.append({
                "filename": p.name,
                "rel_path": str(LOG_DIR_REL / p.name),
                "status":   "malformed",
            })

    return {"logs": logs, "total": len(logs)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _move_file(
    vault_root: Path,
    rel: str,
    dest_dir: Path,
    decision: str,
    op_note: str,
    soft_delete: bool = False,
) -> dict:
    """Attempt to move a vault file to dest_dir. Returns a result dict."""
    source = (vault_root / rel).resolve()

    # Path-traversal guard
    if not _is_inside_vault(source, vault_root):
        return {
            "path":     rel,
            "decision": decision,
            "action":   "skipped_outside_vault",
            "note":     "Rejected: path escapes vault root",
        }

    if not source.exists():
        return {
            "path":     rel,
            "decision": decision,
            "action":   "skipped_not_found",
            "note":     "Source file not found — may already have been moved",
        }

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = _unique_dest(dest_dir / source.name)
        shutil.move(str(source), str(dest))
        action = "soft_deleted" if soft_delete else "archived"
        return {
            "path":     rel,
            "decision": decision,
            "action":   action,
            "dest":     str(dest.relative_to(vault_root)),
            "note":     op_note or action,
        }
    except OSError as exc:
        return {
            "path":     rel,
            "decision": decision,
            "action":   "error",
            "note":     str(exc),
        }


def _fail(msg: str, path: str) -> dict:
    return {
        "ok":            False,
        "error":         msg,
        "draft_path":    path,
        "applied_count": 0,
        "skipped_count": 0,
        "error_count":   0,
        "before_count":  0,
        "after_count":   0,
        "results":       [],
    }


def _is_inside_vault(path: Path, vault_root: Path) -> bool:
    try:
        path.relative_to(vault_root.resolve())
        return True
    except ValueError:
        return False


def _unique_dest(dest: Path) -> Path:
    """If dest already exists, append a numeric suffix."""
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    for i in range(1, 10000):
        candidate = dest.parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
    return dest  # fallback (should never reach)
