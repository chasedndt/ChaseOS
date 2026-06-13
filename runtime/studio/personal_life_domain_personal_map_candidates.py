"""Personal life-domain Personal Map candidate generator.

This module turns the reviewed personal life-domain notes into governed
Personal Map candidates. It only writes the append-only candidate log plus a
human review deck; it does not approve, apply, or mutate the canonical Personal
Map graph.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.memory.candidate_store import (
    PERSONAL_MAP_BLOCKED_EFFECTS,
    build_personal_map_edge_candidate,
    build_personal_map_node_candidate,
    load_personal_map_candidates,
    personal_map_candidate_log_path,
    persist_personal_map_candidate,
)
from runtime.memory.personal_map import PersonalMapEdge, PersonalMapNode
from runtime.pulse.card_schema import EvidenceRef


CREATED_AT = "2026-05-16T00:00:00Z"
SESSION_DESCRIPTOR = "personal-map-life-domain-candidates"
REVIEW_DECK_PATH = (
    Path("07_LOGS")
    / "Pulse-Decks"
    / "memory-candidates"
    / "personal-map"
    / "2026-05-16-personal-life-domain-candidates-review.md"
)
SOURCE_DECK_PATH = REVIEW_DECK_PATH.as_posix()
DATA_CLASS = "personal_life_domain_context"


def _evidence(source_path: str, summary: str, *, trust_label: str) -> EvidenceRef:
    return EvidenceRef(
        source_path=source_path,
        source_type="vault_markdown_review_surface",
        summary=summary,
        trust_label=trust_label,
        observed_at=CREATED_AT,
    )


SOURCE_DIGEST = _evidence(
    "03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-source-digest.md",
    "Source-derived digest covering identity, doctrine, discipline, interests, languages, life domains, and project context.",
    trust_label="source_derived_review_required",
)
PROMOTION_QUEUE = _evidence(
    "03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-promotion-queue.md",
    "Candidate-only queue that explicitly blocks live Personal Map, Pulse memory, companion memory, project truth, and runtime-state mutation.",
    trust_label="candidate_queue_review_required",
)
INTERESTS_NODE = _evidence(
    "00_HOME/Personal-Domains/Interests-Knowledge-Domains.md",
    "Operator-facing personal domain node containing source-derived interests and direct 2026-05-16 operator updates.",
    trust_label="direct_operator_update_review_required",
)
FITNESS_NODE = _evidence(
    "00_HOME/Personal-Domains/Fitness-Combat-Physical-Discipline.md",
    "Operator-facing personal domain node for gym, boxing, running, recovery, health, and physical discipline.",
    trust_label="source_derived_review_required",
)
LANGUAGE_NODE = _evidence(
    "00_HOME/Personal-Domains/Language-Learning-Global-Mobility.md",
    "Operator-facing personal domain node for Mandarin, HSK 1, global mobility, and Asian market alignment.",
    trust_label="source_derived_review_required",
)
NETWORKING_NODE = _evidence(
    "00_HOME/Personal-Domains/Networking-Social-Capital.md",
    "Operator-facing personal domain node for professional networking, higher-value networks, visibility, and relationship building.",
    trust_label="source_derived_review_required",
)
HARDWARE_NODE = _evidence(
    "00_HOME/Personal-Domains/Hardware-Systems-Future-Robotics.md",
    "Operator-facing personal domain node for GPU/hardware, Raspberry Pi, edge compute, robotics, and physical AI optionality.",
    trust_label="source_derived_review_required",
)


def _node(
    node_id: str,
    node_type: str,
    label: str,
    summary: str,
    *,
    evidence: list[EvidenceRef],
    tags: list[str],
) -> PersonalMapNode:
    return PersonalMapNode(
        node_id=node_id,
        node_type=node_type,
        label=label,
        summary=summary,
        evidence=evidence,
        tags=tags,
        updated_at=CREATED_AT,
        status="candidate",
        history=[
            {
                "status": "candidate",
                "timestamp": CREATED_AT,
                "actor": "Codex",
                "reason": "Generated from reviewed personal life-domain context; pending operator review.",
            }
        ],
    )


def _edge(
    source_node_id: str,
    target_node_id: str,
    relation: str,
    *,
    evidence: list[EvidenceRef],
    confidence: float = 0.72,
) -> PersonalMapEdge:
    edge_id = f"{source_node_id}__{relation}__{target_node_id}"
    return PersonalMapEdge(
        edge_id=edge_id,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        relation=relation,
        evidence=evidence,
        confidence=confidence,
        updated_at=CREATED_AT,
        status="candidate",
        history=[
            {
                "status": "candidate",
                "timestamp": CREATED_AT,
                "actor": "Codex",
                "reason": "Relationship generated from personal-domain routing; pending operator review.",
            }
        ],
    )


def build_personal_life_domain_personal_map_candidates():
    """Build candidate-only Personal Map nodes and edges for operator review."""

    reason = (
        "Promote source-derived personal life-domain context into pending-review Personal Map candidates "
        "without canonical apply."
    )
    nodes = [
        _node(
            "domain.fitness_combat_physical_discipline",
            "domain",
            "Fitness / Combat / Physical Discipline",
            (
                "Physical discipline base layer for gym, boxing, running, recovery, health, and identity reinforcement. "
                "The source digest frames fitness as supporting trading performance and platform-building velocity."
            ),
            evidence=[FITNESS_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["personal_os", "fitness", "combat", "running", "recovery", "discipline"],
        ),
        _node(
            "domain.interests_knowledge_domains",
            "domain",
            "Interests / Knowledge Domains",
            (
                "Cross-domain interest map spanning AI/runtime engineering, trading systems, software engineering, "
                "cybersecurity, content/distribution, platform theory, university learning, piano, geopolitics, "
                "history, and YouTube monetization."
            ),
            evidence=[INTERESTS_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["personal_os", "interests", "knowledge_domains", "learning_routes"],
        ),
        _node(
            "domain.language_learning_global_mobility",
            "domain",
            "Language Learning / Global Mobility",
            (
                "Lightweight language lane for Mandarin and HSK 1 with future relocation/travel optionality and "
                "Asian market alignment."
            ),
            evidence=[LANGUAGE_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["personal_os", "language_learning", "mandarin", "hsk1", "global_mobility"],
        ),
        _node(
            "domain.networking_social_capital",
            "domain",
            "Networking / Social Capital",
            (
                "Relationship and access layer for professional networking, higher-value networks, LinkedIn visibility, "
                "Twitch/social growth, relationship building, career, content, advisory, and opportunity flow."
            ),
            evidence=[NETWORKING_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["personal_os", "networking", "social_capital", "career", "content"],
        ),
        _node(
            "domain.hardware_systems_future_robotics",
            "domain",
            "Hardware / Systems / Future Robotics",
            (
                "Future strategic lane for GPU/hardware, Raspberry Pi, edge compute, robotics, physical AI, embedded "
                "systems, ROS, computer vision, SLAM, mechatronics, and power systems."
            ),
            evidence=[HARDWARE_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["personal_os", "hardware", "edge_compute", "robotics", "physical_ai"],
        ),
        _node(
            "skill.gym_training",
            "habit",
            "Gym Training",
            "Source-derived physical lane under the fitness base layer; current programme and metrics still need operator evidence.",
            evidence=[FITNESS_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["fitness", "gym", "routine", "evidence_gap_programme"],
        ),
        _node(
            "skill.boxing",
            "skill",
            "Boxing",
            "Source-derived combat-sport lane under physical discipline; current cadence and level still need operator confirmation.",
            evidence=[FITNESS_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["fitness", "boxing", "combat_sport", "evidence_gap_cadence"],
        ),
        _node(
            "habit.running",
            "habit",
            "Running",
            "Source-derived endurance lane under physical discipline; current cadence and distance metrics still need operator confirmation.",
            evidence=[FITNESS_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["fitness", "running", "endurance", "evidence_gap_metrics"],
        ),
        _node(
            "skill.mandarin_hsk1",
            "skill",
            "Mandarin / HSK 1",
            "Source-derived language-learning target: Mandarin with HSK 1 as the current lightweight milestone.",
            evidence=[LANGUAGE_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["language_learning", "mandarin", "hsk1", "asia_market_alignment"],
        ),
        _node(
            "preference.interest.piano",
            "preference",
            "Piano",
            "Direct 2026-05-16 operator interest update; candidate creative skill and discipline lane pending priority/cadence review.",
            evidence=[INTERESTS_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["interest", "piano", "creative_skill", "direct_operator_update"],
        ),
        _node(
            "preference.interest.geopolitics",
            "preference",
            "Geopolitics",
            "Direct 2026-05-16 operator interest update linked to GeoMacro, trading narrative context, strategy, and content ideas.",
            evidence=[INTERESTS_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["interest", "geopolitics", "geomacro", "strategy", "direct_operator_update"],
        ),
        _node(
            "preference.interest.history",
            "preference",
            "History",
            "Direct 2026-05-16 operator interest update linked to doctrine, geopolitics, strategic context, storytelling, and content.",
            evidence=[INTERESTS_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["interest", "history", "strategy", "storytelling", "direct_operator_update"],
        ),
        _node(
            "content_map.youtube_monetization",
            "content_map",
            "YouTube Monetization",
            "Direct 2026-05-16 operator interest update routed to Content Creation OS, ChaseInTech, and Chaser.sol for creator strategy and monetization funnels.",
            evidence=[INTERESTS_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["content", "youtube", "monetization", "creator_business", "direct_operator_update"],
        ),
        _node(
            "content_map.content_distribution_creator_monetization",
            "content_map",
            "Content Distribution / Creator Monetization",
            (
                "Source-derived content lane covering ChaseInTech, Chaser.sol, build-in-public, YouTube, Twitch, X, "
                "LinkedIn, creator monetization, AI content systems, and distribution into projects."
            ),
            evidence=[INTERESTS_NODE, SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["content", "distribution", "creator_monetization", "personal_brand"],
        ),
        _node(
            "learning_map.university_computer_science_ai",
            "learning_map",
            "University / Computer Science AI Learning Map",
            (
                "Source-derived academic lane: University of Greenwich Computer Science (Artificial Intelligence), "
                "Year 1 pass goal, module child tree, coursework tracking, revision workflows, and concept-to-project linking."
            ),
            evidence=[SOURCE_DIGEST, PROMOTION_QUEUE],
            tags=["university", "computer_science", "artificial_intelligence", "module_tree"],
        ),
    ]

    edges = [
        _edge("skill.gym_training", "domain.fitness_combat_physical_discipline", "belongs_to_domain", evidence=[FITNESS_NODE, SOURCE_DIGEST]),
        _edge("skill.boxing", "domain.fitness_combat_physical_discipline", "belongs_to_domain", evidence=[FITNESS_NODE, SOURCE_DIGEST]),
        _edge("habit.running", "domain.fitness_combat_physical_discipline", "belongs_to_domain", evidence=[FITNESS_NODE, SOURCE_DIGEST]),
        _edge("skill.mandarin_hsk1", "domain.language_learning_global_mobility", "belongs_to_domain", evidence=[LANGUAGE_NODE, SOURCE_DIGEST]),
        _edge("preference.interest.piano", "domain.interests_knowledge_domains", "belongs_to_domain", evidence=[INTERESTS_NODE, SOURCE_DIGEST]),
        _edge("preference.interest.geopolitics", "domain.interests_knowledge_domains", "belongs_to_domain", evidence=[INTERESTS_NODE, SOURCE_DIGEST]),
        _edge("preference.interest.history", "domain.interests_knowledge_domains", "belongs_to_domain", evidence=[INTERESTS_NODE, SOURCE_DIGEST]),
        _edge("content_map.youtube_monetization", "content_map.content_distribution_creator_monetization", "belongs_to_content_map", evidence=[INTERESTS_NODE, SOURCE_DIGEST]),
        _edge("content_map.youtube_monetization", "domain.interests_knowledge_domains", "belongs_to_domain", evidence=[INTERESTS_NODE, SOURCE_DIGEST]),
        _edge("preference.interest.geopolitics", "preference.interest.history", "reinforces", evidence=[INTERESTS_NODE, SOURCE_DIGEST], confidence=0.68),
        _edge("domain.networking_social_capital", "content_map.content_distribution_creator_monetization", "supports_distribution", evidence=[NETWORKING_NODE, SOURCE_DIGEST], confidence=0.7),
        _edge("learning_map.university_computer_science_ai", "domain.interests_knowledge_domains", "feeds_project_learning", evidence=[SOURCE_DIGEST, PROMOTION_QUEUE], confidence=0.74),
        _edge("domain.hardware_systems_future_robotics", "learning_map.university_computer_science_ai", "extends_systems_learning", evidence=[HARDWARE_NODE, SOURCE_DIGEST], confidence=0.66),
    ]

    candidates = [
        build_personal_map_node_candidate(
            node,
            reason=reason,
            source_deck_path=SOURCE_DECK_PATH,
            created_at=CREATED_AT,
            data_class=DATA_CLASS,
            confidence=0.78,
        )
        for node in nodes
    ]
    candidates.extend(
        build_personal_map_edge_candidate(
            edge,
            reason=reason,
            source_deck_path=SOURCE_DECK_PATH,
            created_at=CREATED_AT,
            data_class=DATA_CLASS,
            confidence=edge.confidence,
        )
        for edge in edges
    )
    return candidates


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _candidate_payload(candidate) -> dict[str, str]:
    payload = candidate.node if candidate.node is not None else candidate.edge
    if payload is None:
        return {"id": candidate.candidate_id, "label": "Invalid candidate", "type": candidate.candidate_type}
    if candidate.node is not None:
        return {
            "id": candidate.candidate_id,
            "payload_id": candidate.node.node_id,
            "type": candidate.node.node_type,
            "label": candidate.node.label,
            "summary": candidate.node.summary,
        }
    return {
        "id": candidate.candidate_id,
        "payload_id": candidate.edge.edge_id,
        "type": "edge",
        "label": f"{candidate.edge.source_node_id} -> {candidate.edge.target_node_id}",
        "summary": candidate.edge.relation,
    }


def _review_deck(candidates, *, candidate_log_path: str) -> str:
    node_rows = [_candidate_payload(item) for item in candidates if item.candidate_type == "node"]
    edge_rows = [_candidate_payload(item) for item in candidates if item.candidate_type == "edge"]
    source_paths = sorted(
        {
            evidence.source_path
            for candidate in candidates
            for evidence in (
                (candidate.node.evidence if candidate.node is not None else candidate.edge.evidence)
            )
        }
    )
    lines: list[str] = [
        "---",
        "type: personal-map-candidate-review",
        "date: 2026-05-16",
        f"session_descriptor: {SESSION_DESCRIPTOR}",
        "status: PENDING REVIEW / CANDIDATE ONLY",
        f"candidate_log: {candidate_log_path}",
        "canonical_writeback_allowed: false",
        "personal_map_apply_performed: false",
        "provider_call_performed: false",
        "---",
        "",
        "# Personal Map Life-Domain Candidate Review",
        "",
        "> Candidate-only review deck for promoting personal life-domain context into the governed Personal Map. This deck does not approve or apply memory.",
        "",
        "## Boundary",
        "",
        "- Status: PENDING REVIEW / CANDIDATE ONLY.",
        "- Canonical Personal Map graph is unchanged.",
        "- No Pulse memory, companion memory, project truth, R&D truth-state, provider state, schedule, credential, or external-system mutation occurred.",
        "- Candidate log: [[2026-05-16-personal-map-candidates.jsonl]].",
        "",
        "## Source Inputs",
        "",
    ]
    lines.extend(f"- [[{path}]]" for path in source_paths)
    lines.extend(
        [
            "",
            "## Candidate Nodes",
            "",
            "| Candidate | Node | Type | Summary |",
            "|---|---|---|---|",
        ]
    )
    for row in node_rows:
        lines.append(f"| `{row['id']}` | `{row['payload_id']}` | {row['type']} | {row['summary']} |")
    lines.extend(
        [
            "",
            "## Candidate Edges",
            "",
            "| Candidate | Edge | Relation |",
            "|---|---|---|",
        ]
    )
    for row in edge_rows:
        lines.append(f"| `{row['id']}` | `{row['payload_id']}` | {row['summary']} |")
    lines.extend(
        [
            "",
            "## Review Checklist",
            "",
            "- Confirm whether fitness/combat/running/gym should become accepted Personal Map nodes.",
            "- Confirm current cadence, priority weight, and evidence for piano, Mandarin/HSK 1, networking, and hardware/robotics.",
            "- Confirm geopolitics/history as active interests and whether they should route into GeoMacro, trading narratives, and content planning.",
            "- Confirm YouTube monetization as an active Content Creation OS lane before any project or memory apply.",
            "- Edit or reject any candidate that is too broad before live apply.",
            "",
            "## Blocked Effects",
            "",
        ]
    )
    lines.extend(f"- `{effect}`" for effect in PERSONAL_MAP_BLOCKED_EFFECTS)
    lines.extend(
        [
            "",
            "## Next Pass",
            "",
            "If the operator approves specific candidates, run the governed Personal Map review/apply surface against the selected candidate ids only. Do not bulk-apply this deck automatically.",
            "",
            "## Graph Links",
            "",
            "[[00_HOME/Personal-Operator-Index]] [[03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index]] [[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-source-digest]] [[00_HOME/Personal-Domains/Personal-Domains-Index]] [[06_AGENTS/Personal-Map-Architecture]] [[06_AGENTS/ChaseOS-Pulse-Personal-Map-Review-Apply-Surface]]",
            "",
        ]
    )
    return "\n".join(lines)


def write_personal_life_domain_personal_map_candidates(vault_root: str | Path = ".") -> dict[str, Any]:
    """Persist missing candidates and write the operator review deck."""

    vault = Path(vault_root).resolve()
    candidates = build_personal_life_domain_personal_map_candidates()
    existing_ids = {candidate.candidate_id for candidate in load_personal_map_candidates(vault)}
    artifacts = []
    skipped_existing = []
    for candidate in candidates:
        if candidate.candidate_id in existing_ids:
            skipped_existing.append(candidate.candidate_id)
            continue
        artifacts.append(persist_personal_map_candidate(vault, candidate).to_dict())
    candidate_log = personal_map_candidate_log_path(vault, created_at=CREATED_AT)
    review_path = (vault / REVIEW_DECK_PATH).resolve()
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(
        _review_deck(candidates, candidate_log_path=_relative_to_vault(vault, candidate_log)),
        encoding="utf-8",
    )
    return {
        "ok": True,
        "session_descriptor": SESSION_DESCRIPTOR,
        "candidate_log_path": _relative_to_vault(vault, candidate_log),
        "review_deck_path": _relative_to_vault(vault, review_path),
        "candidate_count": len(candidates),
        "node_candidate_count": sum(1 for candidate in candidates if candidate.candidate_type == "node"),
        "edge_candidate_count": sum(1 for candidate in candidates if candidate.candidate_type == "edge"),
        "written_candidate_count": len(artifacts),
        "skipped_existing_candidate_count": len(skipped_existing),
        "canonical_writeback_allowed": False,
        "personal_map_apply_performed": False,
        "blocked_effects": list(PERSONAL_MAP_BLOCKED_EFFECTS),
        "artifacts": artifacts,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(write_personal_life_domain_personal_map_candidates("."), indent=2, sort_keys=True))
