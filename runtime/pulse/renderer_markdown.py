"""Markdown renderer for ChaseOS Pulse decks."""

from __future__ import annotations

from runtime.pulse.card_schema import PulseCard, PulseDeck


def render_card_markdown(card: PulseCard) -> str:
    card.validate()
    lines = [
        f"### {card.title}",
        f"- Audience: {card.audience}",
        f"- Class: {card.card_class}",
        f"- Type: {card.type}",
        f"- Promotion status: {card.promotion_status}",
        f"- Writeback status: {card.writeback_status}",
        f"- Governance: {card.governance_state}",
        "",
        card.summary,
    ]
    if card.why_it_matters:
        lines.extend(["", f"Why it matters: {card.why_it_matters}"])
    if card.evidence:
        lines.extend(["", "Evidence:"])
        for item in card.evidence:
            source = item.source_path
            if item.source_url:
                source = f"{source} | {item.source_url}"
            lines.append(f"- {source} ({item.source_type}): {item.summary}")
    if card.source_links:
        lines.extend(["", "Source links:"])
        for link in card.source_links:
            target = link.url or link.path
            lines.append(f"- {link.label}: {target} ({link.source_type})")
    if card.related_nodes:
        lines.extend(["", "Related nodes:"])
        for node in card.related_nodes:
            label = node.label or node.node_id
            lines.append(f"- {label} ({node.node_type}; {node.relation})")
    if card.thumbnails:
        lines.extend(["", "Thumbnails:"])
        for thumbnail in card.thumbnails:
            lines.append(f"- {thumbnail.path} ({thumbnail.source_type}): {thumbnail.alt}")
    if card.recommended_actions:
        lines.extend(["", "Recommended actions:"])
        for action in card.recommended_actions:
            approval = "requires approval" if action.requires_operator_approval else "no approval"
            lines.append(f"- {action.label} [{action.action_type}; {approval}]")
    if card.feedback:
        lines.extend(["", "Feedback:"])
        for feedback in card.feedback:
            lines.append(f"- {feedback.feedback_type}: {feedback.operator_note}".rstrip())
    return "\n".join(lines)


def render_deck_markdown(deck: PulseDeck) -> str:
    deck.validate()
    lines = [
        f"# ChaseOS Pulse Deck - {deck.deck_id}",
        "",
        f"- Audience: {deck.audience}",
        f"- Generated: {deck.generated_at}",
        f"- Canonical writeback enabled: {deck.canonical_writeback_enabled}",
        "",
    ]
    for card in deck.cards:
        lines.append(render_card_markdown(card))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
