"""
graph_hygiene_decision_draft.py — ChaseOS Studio

Phase 2: decision draft writer for Graph Hygiene review.

Creates structured decision draft JSON artifacts under:
    07_LOGS/Graph-Reports/Decision-Drafts/

Authority:
  - Writes ONLY to 07_LOGS/Graph-Reports/Decision-Drafts/
  - Does NOT modify source files, graph indexes, or canonical state
  - Draft status = "draft_pending_operator_review" until applied via executor
  - Approval required to create (write-gated through StudioService)
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

DRAFT_DIR_REL = Path("07_LOGS") / "Graph-Reports" / "Decision-Drafts"
DRAFT_VERSION = "studio.graph_hygiene_decision_draft.v1"

ALLOWED_DECISIONS = {
    "keep_and_wire",
    "keep_excluded",
    "archive_after_review",
    "archive_noncanonical_artifact",
    "delete_after_review",
    "replace_with_canonical",
    "manual_investigation",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_decision_draft(
    vault_root: Path,
    source_queue_path: str,
    decisions: list[dict],
    operator_note: str = "",
) -> dict:
    """
    Validate and write a decision draft artifact.

    Parameters
    ----------
    vault_root        : Path
    source_queue_path : str   relative path to the source review queue JSON
    decisions         : list  each entry must have keys: path, decision
                              optional: issue, operator_note
    operator_note     : str   overall operator annotation for the draft

    Returns
    -------
    dict  with keys: ok, draft_path, draft_id, decision_count, validation_errors
    """
    vault_root = Path(vault_root)
    now = datetime.now(tz=timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H%M%S")

    validation_errors: list[str] = []
    validated: list[dict] = []

    for i, item in enumerate(decisions):
        d_path = (item.get("path") or "").strip()
        d_type = (item.get("decision") or "").strip()
        if not d_path:
            validation_errors.append(f"Item {i}: missing 'path'")
            continue
        if d_type not in ALLOWED_DECISIONS:
            validation_errors.append(
                f"Item {i} ({d_path!r}): invalid decision {d_type!r} — "
                f"allowed: {sorted(ALLOWED_DECISIONS)}"
            )
            continue
        validated.append({
            "path":          d_path,
            "issue":         (item.get("issue") or "loose_node").strip(),
            "decision":      d_type,
            "operator_note": (item.get("operator_note") or "").strip(),
        })

    if validation_errors:
        return {
            "ok":               False,
            "validation_errors": validation_errors,
            "draft_path":       None,
            "draft_id":         None,
            "decision_count":   0,
        }

    if not validated:
        return {
            "ok":               False,
            "validation_errors": ["No valid decisions provided"],
            "draft_path":       None,
            "draft_id":         None,
            "decision_count":   0,
        }

    # Derive stable draft ID from content hash
    content_for_hash = json.dumps(
        {"ts": ts, "queue": source_queue_path, "decisions": validated},
        sort_keys=True,
    )
    draft_id = "ghd-" + hashlib.sha256(content_for_hash.encode()).hexdigest()[:12]
    filename = f"{ts}-graph-hygiene-decision-draft.json"

    draft = {
        "surface":           "studio_graph_hygiene_decision_draft",
        "model_version":     DRAFT_VERSION,
        "draft_id":          draft_id,
        "created_at":        now.isoformat(),
        "created_by":        "studio_graph_hygiene_review_panel",
        "source_queue_path": source_queue_path,
        "operator_note":     operator_note,
        "status":            "draft_pending_operator_review",
        "decision_count":    len(validated),
        "decisions":         validated,
        "authority": {
            "draft_only":                 True,
            "applied":                    False,
            "canonical_mutation_allowed": False,
            "delete_archive_allowed":     False,
            "note": (
                "Draft only — no graph changes applied. "
                "Apply only through the approved execution path."
            ),
        },
    }

    draft_dir = vault_root / DRAFT_DIR_REL
    draft_dir.mkdir(parents=True, exist_ok=True)
    # Handle same-second collision by appending a counter
    draft_path = draft_dir / filename
    if draft_path.exists():
        stem = filename[:-5]  # strip .json
        for i in range(1, 1000):
            candidate = draft_dir / f"{stem}_{i}.json"
            if not candidate.exists():
                draft_path = candidate
                filename = candidate.name
                break
    draft_path.write_text(
        json.dumps(draft, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "ok":                True,
        "draft_path":        str(DRAFT_DIR_REL / filename),
        "draft_id":          draft_id,
        "decision_count":    len(validated),
        "validation_errors": [],
    }


def list_decision_drafts(vault_root: Path) -> dict:
    """Return summary list of all decision drafts, newest first."""
    vault_root = Path(vault_root)
    draft_dir = vault_root / DRAFT_DIR_REL

    if not draft_dir.exists():
        return {"drafts": [], "total": 0}

    drafts = []
    for p in sorted(draft_dir.glob("*graph-hygiene-decision-draft*.json"), reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            auth = data.get("authority") or {}
            drafts.append({
                "filename":       p.name,
                "rel_path":       str(DRAFT_DIR_REL / p.name),
                "draft_id":       data.get("draft_id", ""),
                "created_at":     data.get("created_at", ""),
                "status":         data.get("status", "unknown"),
                "decision_count": data.get("decision_count", 0),
                "operator_note":  data.get("operator_note", ""),
                "applied":        bool(auth.get("applied")),
            })
        except (OSError, json.JSONDecodeError):
            drafts.append({
                "filename": p.name,
                "rel_path": str(DRAFT_DIR_REL / p.name),
                "status":   "malformed",
                "applied":  False,
            })

    return {"drafts": drafts, "total": len(drafts)}


def load_decision_draft(vault_root: Path, rel_path: str) -> dict | None:
    """Load a specific draft by relative vault path. Returns None if not found."""
    vault_root = Path(vault_root)
    abs_path = (vault_root / rel_path).resolve()
    expected_root = (vault_root / DRAFT_DIR_REL).resolve()

    # Path-traversal guard: must be inside Decision-Drafts/
    try:
        abs_path.relative_to(expected_root)
    except ValueError:
        return None

    if not abs_path.exists():
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
