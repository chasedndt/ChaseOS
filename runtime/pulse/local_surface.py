"""Local-only ChaseOS Pulse deck surface.

This module renders existing user Pulse deck artifacts. It does not scan the
web, call providers, activate schedules, submit feedback, approve memory, or
write canonical ChaseOS state.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from runtime.pulse.bus_enqueue_approval_request import load_agent_bus_enqueue_approval_requests
from runtime.pulse.bus_handoff_preflight import build_agent_bus_handoff_preflight
from runtime.pulse.bus_review_queue import build_agent_bus_review_queue_preview
from runtime.pulse.candidate_inspector import build_candidate_inspector_snapshot
from runtime.pulse.card_schema import FEEDBACK_TYPES, PulseCard, PulseDeck
from runtime.pulse.feedback import PulseFeedbackCandidateArtifact, PulseFeedbackRecord, persist_feedback_candidate


SURFACE_ID = "chaseos_pulse_user_deck_surface"
USER_DECK_DIR = Path("07_LOGS") / "Pulse-Decks" / "users"
DEFAULT_FEEDBACK_CANDIDATES = (
    "accepted",
    "dismissed",
    "snoozed",
    "corrected",
    "needs_more_evidence",
    "memory_candidate",
    "thumbs_up",
    "thumbs_down",
    "show_more_like_this",
    "show_less_like_this",
    "never_show_this",
    "save",
    "delegate",
    "turn_into_task",
    "promote_to_memory",
    "link_to_project",
    "link_to_personal_map",
    "link_to_agent_brain",
    "dismiss",
)
if set(DEFAULT_FEEDBACK_CANDIDATES) != set(FEEDBACK_TYPES):
    raise RuntimeError("Pulse governed control feedback candidates must cover FEEDBACK_TYPES")

_SENSITIVE_REF = re.compile(
    r"(?i)(^|[/\\])(\.env|secrets?|credentials?)([/\\]|$)|"
    r"(api[_-]?key|password|token|secret)\s*[:=]|"
    r"(seed\s+phrase|wallet\s+key)"
)


class PulseSurfaceError(RuntimeError):
    """Raised when the local Pulse surface cannot be built safely."""


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path.resolve())


def _assert_inside(child: Path, parent: Path, message: str) -> None:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise PulseSurfaceError(message) from exc


def _safe_display(value: Any) -> str:
    text = "" if value is None else str(value)
    if _SENSITIVE_REF.search(text):
        return "[redacted protected reference]"
    return text


def _authority_boundary() -> dict[str, Any]:
    return {
        "local_only": True,
        "browser_scope": [],
        "mcp_scope_changed": False,
        "delivery_changed": False,
        "cron_or_scheduler_changed": False,
        "live_provider_calls_allowed": False,
        "external_connector_calls_allowed": False,
        "automatic_memory_approval_allowed": False,
        "canonical_writeback_allowed": False,
        "second_datastore_created": False,
    }


def _user_deck_root(vault: Path) -> Path:
    return vault / USER_DECK_DIR


def list_user_deck_json_paths(vault_root: str | Path) -> list[Path]:
    """List user deck JSON artifacts, excluding derived surface artifacts."""
    vault = _vault_path(vault_root)
    deck_root = _user_deck_root(vault)
    if not deck_root.exists():
        return []
    return sorted(
        path
        for path in deck_root.glob("*.json")
        if path.is_file() and ".surface." not in path.name
    )


def find_latest_user_deck_json(vault_root: str | Path) -> Path:
    """Return the latest user Pulse deck JSON under 07_LOGS/Pulse-Decks/users/."""
    candidates = list_user_deck_json_paths(vault_root)
    if not candidates:
        raise PulseSurfaceError("no user Pulse deck JSON artifacts found")
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def _resolve_user_deck_json(vault: Path, deck_path: str | Path | None = None) -> Path:
    if deck_path is None:
        path = find_latest_user_deck_json(vault)
    else:
        raw_path = Path(deck_path)
        path = raw_path if raw_path.is_absolute() else vault / raw_path
    if path.suffix.lower() != ".json":
        raise PulseSurfaceError("Pulse surface requires a user deck JSON artifact")
    if not path.exists() or not path.is_file():
        raise PulseSurfaceError(f"Pulse deck JSON artifact does not exist: {path}")
    _assert_inside(
        path,
        _user_deck_root(vault),
        "Pulse surface deck input must stay inside 07_LOGS/Pulse-Decks/users/",
    )
    return path.resolve()


def load_user_deck_for_surface(
    vault_root: str | Path,
    deck_path: str | Path | None = None,
) -> tuple[PulseDeck, Path]:
    """Load and validate a user Pulse deck for surface rendering."""
    vault = _vault_path(vault_root)
    resolved = _resolve_user_deck_json(vault, deck_path)
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    deck = PulseDeck.from_dict(payload)
    if deck.audience != "user":
        raise PulseSurfaceError("Pulse first surface only renders user decks")
    if deck.canonical_writeback_enabled:
        raise PulseSurfaceError("Pulse surface cannot render canonical-writeback-enabled decks")
    return deck, resolved


def build_feedback_candidate(
    card: PulseCard,
    feedback_type: str,
    *,
    operator_note: str = "",
) -> PulseFeedbackRecord:
    """Create a governed feedback candidate without applying it to a card."""
    card.validate()
    if feedback_type not in DEFAULT_FEEDBACK_CANDIDATES:
        raise PulseSurfaceError("unsupported Pulse surface feedback candidate")
    record = PulseFeedbackRecord(
        feedback_id=f"candidate-{card.card_id}-{feedback_type}",
        card_id=card.card_id,
        feedback_type=feedback_type,
        operator_note=operator_note,
        canonical_writeback_allowed=False,
    )
    record.validate()
    return record


def persist_surface_feedback_candidate(
    vault_root: str | Path,
    *,
    card_id: str,
    feedback_type: str,
    deck_path: str | Path | None = None,
    operator_note: str = "",
    source_surface_path: str | Path | None = None,
) -> PulseFeedbackCandidateArtifact:
    """Persist one governed feedback candidate for a user deck card.

    This appends a review-required candidate row only. It does not apply
    feedback to the source deck or approve memory/writeback.
    """
    vault = _vault_path(vault_root)
    deck, resolved_deck_path = load_user_deck_for_surface(vault, deck_path)
    selected = next((card for card in deck.cards if card.card_id == card_id), None)
    if selected is None:
        raise PulseSurfaceError("Pulse surface feedback card_id was not found in the source deck")
    record = build_feedback_candidate(selected, feedback_type, operator_note=operator_note)
    return persist_feedback_candidate(
        vault,
        record,
        source_deck_path=_relative_to_vault(vault, resolved_deck_path),
        source_surface_path=source_surface_path,
    )


def _feedback_candidate_model(card: PulseCard) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for feedback_type in DEFAULT_FEEDBACK_CANDIDATES:
        record = build_feedback_candidate(card, feedback_type)
        payload = record.to_dict()
        payload.update(
            {
                "label": feedback_type.replace("_", " ").title(),
                "candidate_only": True,
                "review_required": True,
                "applied_to_card": False,
                "mutates_source_state": False,
                "automatic_memory_approval_allowed": False,
            }
        )
        candidates.append(payload)
    return candidates


def _card_model(card: PulseCard) -> dict[str, Any]:
    card.validate()
    return {
        "card_id": card.card_id,
        "deck_id": card.deck_id,
        "audience": card.audience,
        "card_class": card.card_class,
        "type": card.type,
        "title": _safe_display(card.title),
        "summary": _safe_display(card.summary),
        "why_it_matters": _safe_display(card.why_it_matters),
        "created_at": card.created_at,
        "generated_at": card.generated_at,
        "scope": card.scope.to_dict() if hasattr(card.scope, "to_dict") else {
            "user_id": _safe_display(card.scope.user_id),
            "agent_id": _safe_display(card.scope.agent_id),
            "project_ids": [_safe_display(item) for item in card.scope.project_ids],
            "coordination_ids": [_safe_display(item) for item in card.scope.coordination_ids],
        },
        "urgency": card.urgency,
        "confidence": card.confidence,
        "promotion_status": card.promotion_status,
        "writeback_status": card.writeback_status,
        "governance_state": card.governance_state,
        "canonical_writeback_enabled": card.canonical_writeback_enabled,
        "evidence": [
            {
                "source_path": _safe_display(item.source_path),
                "source_type": _safe_display(item.source_type),
                "summary": _safe_display(item.summary),
                "trust_label": _safe_display(item.trust_label),
                "observed_at": _safe_display(item.observed_at),
                "quote": _safe_display(item.quote),
                "source_url": _safe_display(item.source_url),
            }
            for item in card.evidence
        ],
        "source_links": [
            {
                "label": _safe_display(item.label),
                "path": _safe_display(item.path),
                "url": _safe_display(item.url),
                "source_type": _safe_display(item.source_type),
            }
            for item in card.source_links
        ],
        "related_nodes": [
            {
                "node_id": _safe_display(item.node_id),
                "node_type": _safe_display(item.node_type),
                "relation": _safe_display(item.relation),
                "label": _safe_display(item.label),
            }
            for item in card.related_nodes
        ],
        "thumbnails": [
            {
                "path": _safe_display(item.path),
                "alt": _safe_display(item.alt),
                "source_type": _safe_display(item.source_type),
            }
            for item in card.thumbnails
        ],
        "recommended_actions": [
            {
                "action_id": _safe_display(item.action_id),
                "label": _safe_display(item.label),
                "action_type": _safe_display(item.action_type),
                "target_ref": _safe_display(item.target_ref),
                "requires_operator_approval": item.requires_operator_approval,
                "mutates_canonical_state": item.mutates_canonical_state,
            }
            for item in card.recommended_actions
        ],
        "feedback_count": len(card.feedback),
        "feedback_candidates": _feedback_candidate_model(card),
    }


def _handoff_readiness_snapshot(vault: Path, *, limit: int = 8) -> dict[str, Any]:
    """Build a read-only snapshot over persisted Agent Bus handoff requests."""
    try:
        requests = load_agent_bus_enqueue_approval_requests(vault)[:limit]
    except Exception as exc:
        return {
            "snapshot_status": "read_only_unavailable",
            "request_count": 0,
            "item_count": 0,
            "counts_by_handoff_status": {},
            "items": [],
            "errors": [{"request_id": "", "error": str(exc)}],
            "writes": [],
            "approval_granted": False,
            "live_agent_bus_handoff_allowed": False,
            "agent_bus_tasks_written": False,
            "candidate_apply_allowed": False,
            "canonical_writeback_allowed": False,
            "second_datastore_write_allowed": False,
        }
    items: list[dict[str, Any]] = []
    counts_by_status: dict[str, int] = {}
    errors: list[dict[str, str]] = []
    for request in requests:
        try:
            preflight = build_agent_bus_handoff_preflight(vault, request.request_id).to_dict()
            status = str(preflight.get("handoff_status") or "unknown")
            counts_by_status[status] = counts_by_status.get(status, 0) + 1
            items.append(
                {
                    "request_id": preflight["request_id"],
                    "candidate_id": preflight["request"].get("candidate_id"),
                    "recipient": preflight["request"].get("recipient"),
                    "handoff_status": status,
                    "ready_for_supervised_live_command": preflight[
                        "ready_for_supervised_live_command"
                    ],
                    "evidence_record_present": preflight["evidence_record_present"],
                    "blocked_reasons": preflight["blocked_reasons"],
                    "readiness_reasons": preflight["readiness_reasons"],
                    "duplicate_found": preflight["duplicate_posture"].get("duplicate_found"),
                    "bus_snapshot_status": preflight["target_posture"].get("bus_snapshot_status"),
                    "agent_bus_task_written": preflight["agent_bus_task_written"],
                    "live_agent_bus_handoff_allowed": preflight[
                        "live_agent_bus_handoff_allowed"
                    ],
                    "canonical_writeback_allowed": preflight["canonical_writeback_allowed"],
                }
            )
        except Exception as exc:
            errors.append({"request_id": request.request_id, "error": str(exc)})
    return {
        "snapshot_status": "read_only",
        "request_count": len(requests),
        "item_count": len(items),
        "counts_by_handoff_status": counts_by_status,
        "items": items,
        "errors": errors,
        "writes": [],
        "approval_granted": False,
        "live_agent_bus_handoff_allowed": False,
        "agent_bus_tasks_written": False,
        "candidate_apply_allowed": False,
        "canonical_writeback_allowed": False,
        "second_datastore_write_allowed": False,
    }


def build_pulse_surface_model(
    vault_root: str | Path,
    deck_path: str | Path | None = None,
    *,
    include_candidate_inspector: bool = True,
) -> dict[str, Any]:
    """Build a local-only UI model from the latest user Pulse deck artifact."""
    vault = _vault_path(vault_root)
    deck, resolved_deck_path = load_user_deck_for_surface(vault, deck_path)
    cards = [_card_model(card) for card in deck.cards]
    candidate_inspector = (
        build_candidate_inspector_snapshot(vault).to_dict()
        if include_candidate_inspector
        else {
            "inspector_status": "not_loaded",
            "item_count": 0,
            "counts_by_kind": {},
            "decision_counts_by_candidate_id": {},
            "source_log_paths": [],
            "writes": [],
            "canonical_writeback_allowed": False,
            "applies_effects": False,
            "second_datastore_write_allowed": False,
            "items": [],
        }
    )
    bus_review_preview = build_agent_bus_review_queue_preview(
        vault,
        requested_by="openclaw",
        priority="normal",
        limit=8,
    ).to_dict()
    handoff_readiness = _handoff_readiness_snapshot(vault)
    return {
        "surface": SURFACE_ID,
        "title": "ChaseOS Pulse",
        "local_only": True,
        "source_deck_path": _relative_to_vault(vault, resolved_deck_path),
        "deck": {
            "deck_id": deck.deck_id,
            "audience": deck.audience,
            "generated_at": deck.generated_at,
            "card_count": len(deck.cards),
            "source_summary": deck.source_summary,
            "schedule_ref": _safe_display(deck.schedule_ref),
            "feedback_policy_ref": _safe_display(deck.feedback_policy_ref),
            "canonical_writeback_enabled": deck.canonical_writeback_enabled,
        },
        "governed_controls": {
            "control_status": "candidate_only_controls_available",
            "feedback_type_count": len(DEFAULT_FEEDBACK_CANDIDATES),
            "feedback_types": list(DEFAULT_FEEDBACK_CANDIDATES),
            "writes_feedback_candidates": True,
            "candidate_write_only": True,
            "review_required": True,
            "applies_candidates": False,
            "approves_memory": False,
            "creates_tasks": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "schedule_activation_allowed": False,
            "provider_or_connector_call_allowed": False,
            "canonical_writeback_allowed": False,
        },
        "cards": cards,
        "candidate_inspector": candidate_inspector,
        "agent_bus_review_queue_preview": bus_review_preview,
        "agent_bus_handoff_readiness": handoff_readiness,
        "writes": [],
        "authority": _authority_boundary(),
        "boundaries": [
            "Reads existing user Pulse deck artifacts only",
            "No browser launch or browser automation",
            "No MCP, delivery, cron, or schedule activation",
            "No live provider or external connector calls",
            "No secret display; protected references are redacted",
            "No automatic memory approval",
            "No canonical writeback to Now.md, Project-OS files, governance docs, or 02_KNOWLEDGE/",
            "Feedback is exposed as governed candidates only",
            "Persisted feedback candidates append to 07_LOGS/Pulse-Decks/feedback-candidates/ only",
            "Candidate inspector is read-only and applies no review decisions",
            "Agent Bus REVIEW handoff preview is read-only; it creates no bus tasks without separate approval",
            "Agent Bus handoff readiness is read-only and grants no approval or live enqueue authority",
            "No second datastore",
        ],
    }


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _render_list(items: list[str]) -> str:
    if not items:
        return "<p class='empty'>None declared.</p>"
    return "<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in items) + "</ul>"


def render_pulse_surface_html(
    model: dict[str, Any],
    *,
    feedback_action: str | None = None,
) -> str:
    """Render a complete static HTML page for the local Pulse deck surface."""
    title = _escape(model.get("title", "ChaseOS Pulse"))
    deck = model.get("deck", {})
    authority = model.get("authority", {})
    governed_controls = model.get("governed_controls", {}) or {}
    cards_html: list[str] = []

    for card in model.get("cards", []):
        evidence = []
        for item in card.get("evidence", []):
            url = item.get("source_url") or ""
            url_fragment = f"<span class='source-url'>{_escape(url)}</span>" if url else ""
            evidence.append(
                "<li>"
                f"<code>{_escape(item.get('source_path'))}</code> "
                f"<span>{_escape(item.get('source_type'))}</span> "
                f"<span>{_escape(item.get('trust_label'))}</span>"
                f"{url_fragment}"
                f"<p>{_escape(item.get('summary'))}</p>"
                "</li>"
            )

        related = [
            "<li>"
            f"{_escape(node.get('label') or node.get('node_id'))} "
            f"<span>{_escape(node.get('node_type'))}</span> "
            f"<span>{_escape(node.get('relation'))}</span>"
            "</li>"
            for node in card.get("related_nodes", [])
        ]

        actions = [
            "<li>"
            f"{_escape(action.get('label'))} "
            f"<span>{_escape(action.get('action_type'))}</span> "
            f"<span>{'approval required' if action.get('requires_operator_approval') else 'no approval required'}</span>"
            "</li>"
            for action in card.get("recommended_actions", [])
        ]

        feedback = []
        for candidate in card.get("feedback_candidates", []):
            if feedback_action:
                feedback.append(
                    f"<form method='post' action='{_escape(feedback_action)}'>"
                    f"<input type='hidden' name='card_id' value='{_escape(candidate.get('card_id'))}'>"
                    f"<input type='hidden' name='feedback_type' value='{_escape(candidate.get('feedback_type'))}'>"
                    "<input type='text' name='operator_note' maxlength='500' "
                    "placeholder='Optional note' aria-label='Optional feedback note'>"
                    f"<button type='submit'>{_escape(candidate.get('label'))} candidate</button>"
                    "</form>"
                )
            else:
                feedback.append(
                    "<button type='button' disabled "
                    f"data-card-id='{_escape(candidate.get('card_id'))}' "
                    f"data-feedback-type='{_escape(candidate.get('feedback_type'))}'>"
                    f"{_escape(candidate.get('label'))} candidate"
                    "</button>"
                )

        cards_html.append(
            "<article class='pulse-card'>"
            "<div class='card-head'>"
            f"<span class='class'>{_escape(card.get('card_class'))}</span>"
            f"<span class='urgency'>Urgency {int(card.get('urgency', 0))}</span>"
            "</div>"
            f"<h2>{_escape(card.get('title'))}</h2>"
            f"<p class='summary'>{_escape(card.get('summary'))}</p>"
            "<dl class='meta'>"
            f"<div><dt>Governance</dt><dd>{_escape(card.get('governance_state'))}</dd></div>"
            f"<div><dt>Confidence</dt><dd>{float(card.get('confidence', 0.0)):.2f}</dd></div>"
            f"<div><dt>Canonical writeback</dt><dd>{'enabled' if card.get('canonical_writeback_enabled') else 'blocked'}</dd></div>"
            "</dl>"
            "<section><h3>Evidence</h3><ul class='evidence'>"
            + "".join(evidence)
            + "</ul></section>"
            "<section><h3>Related Nodes</h3><ul>"
            + "".join(related)
            + "</ul></section>"
            "<section><h3>Recommended Actions</h3><ul>"
            + "".join(actions)
            + "</ul></section>"
            "<section><h3>Governed Feedback Candidates</h3><div class='feedback-row'>"
            + "".join(feedback)
            + "</div></section>"
            "</article>"
        )

    inspector = model.get("candidate_inspector", {}) or {}
    bus_preview = model.get("agent_bus_review_queue_preview", {}) or {}
    handoff = model.get("agent_bus_handoff_readiness", {}) or {}
    inspector_counts = inspector.get("counts_by_kind", {}) or {}
    bus_counts = bus_preview.get("counts_by_candidate_kind", {}) or {}
    inspector_items = inspector.get("items", []) or []
    inspector_preview = []
    for item in inspector_items[:8]:
        inspector_preview.append(
            "<li>"
            f"<strong>{_escape(item.get('title'))}</strong> "
            f"<span>{_escape(item.get('item_kind'))}</span> "
            f"<span>{_escape(item.get('status'))}</span> "
            f"<code>{_escape(item.get('source_log_path'))}</code>"
            "</li>"
        )
    bus_task_previews = []
    for item in (bus_preview.get("agent_bus_task_previews", []) or [])[:8]:
        bus_task_previews.append(
            "<li>"
            f"<strong>{_escape(item.get('request'))}</strong> "
            f"<span>{_escape(item.get('recipient'))}</span> "
            f"<span>{_escape(item.get('intent'))}</span> "
            f"<code>{_escape(item.get('work_fingerprint'))}</code>"
            "</li>"
        )
    handoff_items = []
    for item in (handoff.get("items", []) or [])[:8]:
        reasons = ", ".join(item.get("blocked_reasons") or item.get("readiness_reasons") or [])
        handoff_items.append(
            "<li>"
            f"<strong>{_escape(item.get('handoff_status'))}</strong> "
            f"<span>{_escape(item.get('recipient'))}</span> "
            f"<code>{_escape(item.get('request_id'))}</code> "
            f"<p>{_escape(reasons)}</p>"
            "</li>"
        )
    inspector_count_items = [
        f"{kind}: {count}" for kind, count in sorted(inspector_counts.items()) if count
    ]
    bus_count_items = [
        f"{kind}: {count}" for kind, count in sorted(bus_counts.items()) if count
    ]
    handoff_count_items = [
        f"{status}: {count}"
        for status, count in sorted((handoff.get('counts_by_handoff_status') or {}).items())
        if count
    ]
    boundary_items = list(model.get("boundaries", []))
    canonical = "blocked" if not authority.get("canonical_writeback_allowed") else "allowed"
    providers = "blocked" if not authority.get("live_provider_calls_allowed") else "allowed"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #111827;
      --muted: #5f6b7a;
      --line: #d7dde5;
      --accent: #0f766e;
      --warn: #9a3412;
      --risk: #991b1b;
      --soft: #eef2f7;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 12px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 16px;
      margin-bottom: 18px;
    }}
    h1 {{ margin: 0; font-size: 1.9rem; letter-spacing: 0; }}
    h2 {{ font-size: 1.08rem; margin: 10px 0 8px; letter-spacing: 0; }}
    h3 {{ font-size: .78rem; margin: 14px 0 6px; text-transform: uppercase; letter-spacing: 0; color: var(--muted); }}
    code {{
      background: var(--soft);
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 1px 5px;
      word-break: break-word;
    }}
    .deck-meta, .boundary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 8px;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      min-width: 0;
    }}
    .metric span {{ display: block; color: var(--muted); font-size: .78rem; }}
    .metric strong {{ display: block; overflow-wrap: anywhere; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 14px; align-items: start; }}
    .pulse-card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; }}
    .card-head {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between; align-items: center; }}
    .class, .urgency, .source-url, li span {{
      display: inline-block;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 7px;
      color: var(--muted);
      font-size: .76rem;
      margin: 2px 3px 2px 0;
      max-width: 100%;
      overflow-wrap: anywhere;
    }}
    .class {{ color: var(--accent); border-color: #99d6cb; }}
    .urgency {{ color: var(--warn); border-color: #fed7aa; }}
    .summary {{ color: #263241; margin: 8px 0 10px; }}
    .meta {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 10px 0; }}
    .meta div {{ background: var(--soft); border-radius: 8px; padding: 8px; min-width: 0; }}
    dt {{ color: var(--muted); font-size: .72rem; }}
    dd {{ margin: 0; font-weight: 600; overflow-wrap: anywhere; }}
    ul {{ margin: 0; padding-left: 18px; }}
    li {{ margin: 5px 0; overflow-wrap: anywhere; }}
    .evidence p {{ margin: 4px 0 0; color: #334155; }}
    .feedback-row {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .feedback-row form {{
      display: grid;
      grid-template-columns: minmax(120px, 1fr) auto;
      gap: 6px;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 6px;
      max-width: 100%;
    }}
    input {{
      width: 100%;
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 6px 8px;
      font: inherit;
    }}
    button {{
      border: 1px solid var(--line);
      background: var(--soft);
      color: var(--muted);
      border-radius: 8px;
      padding: 6px 8px;
      font: inherit;
    }}
    button:disabled {{ opacity: 1; cursor: not-allowed; }}
    .governance {{ border-left: 4px solid var(--risk); }}
    @media (max-width: 720px) {{
      main {{ padding: 16px; }}
      .meta {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>{title}</h1>
    <div class="deck-meta">
      <div class="metric"><span>Deck</span><strong>{_escape(deck.get('deck_id'))}</strong></div>
      <div class="metric"><span>Generated</span><strong>{_escape(deck.get('generated_at'))}</strong></div>
      <div class="metric"><span>Cards</span><strong>{int(deck.get('card_count', 0))}</strong></div>
      <div class="metric"><span>Governed controls</span><strong>{int(governed_controls.get('feedback_type_count', 0))}</strong></div>
      <div class="metric governance"><span>Canonical writeback</span><strong>{canonical}</strong></div>
      <div class="metric"><span>Provider calls</span><strong>{providers}</strong></div>
      <div class="metric"><span>Source deck</span><strong>{_escape(model.get('source_deck_path'))}</strong></div>
    </div>
  </header>
  <section class="boundary-grid">
    <div class="metric"><span>Surface</span><strong>{_escape(model.get('surface'))}</strong></div>
    <div class="metric"><span>Schedule activation</span><strong>{'blocked' if not authority.get('cron_or_scheduler_changed') else 'changed'}</strong></div>
    <div class="metric"><span>External connectors</span><strong>{'blocked' if not authority.get('external_connector_calls_allowed') else 'allowed'}</strong></div>
    <div class="metric governance"><span>Candidate apply</span><strong>{'allowed' if governed_controls.get('applies_candidates') else 'blocked'}</strong></div>
  </section>
  <section>
    <h3>Boundaries</h3>
    {_render_list(boundary_items)}
  </section>
  <section>
    <h3>Operator Review Queue Snapshot</h3>
    <div class="deck-meta">
      <div class="metric"><span>Inspector</span><strong>{_escape(inspector.get('inspector_status'))}</strong></div>
      <div class="metric"><span>Candidate / decision rows</span><strong>{int(inspector.get('item_count', 0))}</strong></div>
      <div class="metric governance"><span>Applies effects</span><strong>{'yes' if inspector.get('applies_effects') else 'no'}</strong></div>
      <div class="metric governance"><span>Second datastore</span><strong>{'yes' if inspector.get('second_datastore_write_allowed') else 'no'}</strong></div>
    </div>
    {_render_list(inspector_count_items)}
    <ul>{''.join(inspector_preview)}</ul>
  </section>
  <section>
    <h3>Agent Bus Review Handoff Preview</h3>
    <div class="deck-meta">
      <div class="metric"><span>Queue</span><strong>{_escape(bus_preview.get('queue_status'))}</strong></div>
      <div class="metric"><span>REVIEW task previews</span><strong>{int(bus_preview.get('contract_count', 0))}</strong></div>
      <div class="metric governance"><span>Bus tasks written</span><strong>{'yes' if bus_preview.get('bus_tasks_written') else 'no'}</strong></div>
      <div class="metric governance"><span>Approval requests written</span><strong>{'yes' if bus_preview.get('approval_requests_written') else 'no'}</strong></div>
    </div>
    {_render_list(bus_count_items)}
    <ul>{''.join(bus_task_previews)}</ul>
  </section>
  <section>
    <h3>Supervised Live Handoff Readiness</h3>
    <div class="deck-meta">
      <div class="metric"><span>Snapshot</span><strong>{_escape(handoff.get('snapshot_status'))}</strong></div>
      <div class="metric"><span>Approval requests</span><strong>{int(handoff.get('request_count', 0))}</strong></div>
      <div class="metric governance"><span>Approval granted</span><strong>{'yes' if handoff.get('approval_granted') else 'no'}</strong></div>
      <div class="metric governance"><span>Live handoff allowed</span><strong>{'yes' if handoff.get('live_agent_bus_handoff_allowed') else 'no'}</strong></div>
    </div>
    {_render_list(handoff_count_items)}
    <ul>{''.join(handoff_items)}</ul>
  </section>
  <section class="cards">
    {''.join(cards_html)}
  </section>
</main>
</body>
</html>
"""


def _default_surface_output_path(deck_path: Path) -> Path:
    return deck_path.with_name(f"{deck_path.stem}.surface.html")


def write_pulse_surface_html(
    vault_root: str | Path,
    *,
    deck_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Write a derived static HTML surface beside user Pulse deck artifacts."""
    vault = _vault_path(vault_root)
    model = build_pulse_surface_model(vault, deck_path=deck_path)
    resolved_deck_path = (vault / model["source_deck_path"]).resolve()
    target = Path(output_path) if output_path is not None else _default_surface_output_path(resolved_deck_path)
    target = target if target.is_absolute() else vault / target
    target = target.resolve()
    _assert_inside(
        target,
        _user_deck_root(vault),
        "Pulse surface HTML output must stay inside 07_LOGS/Pulse-Decks/users/",
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_pulse_surface_html(model), encoding="utf-8")
    model = dict(model)
    model["html_output_path"] = _relative_to_vault(vault, target)
    model["writes"] = [_relative_to_vault(vault, target)]
    return model
