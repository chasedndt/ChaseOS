"""
reporter.py — ChaseOS Graph Substrate: Operator Report Generation

Generates operator-readable graph analysis reports.

The report is NOT a generic dump of graph data.
It is a decision-support artifact: it surfaces what a human or runtime agent
should look at next, what is surprising, what requires review, and where
the structural weight of the corpus lives.

Report sections:
  1. Header + snapshot identity
  2. Summary statistics
  3. Most connected nodes (architectural cores)
  4. Community summaries
  5. Cross-domain edges (potential coupling concerns)
  6. Ambiguous / inferred edges requiring review
  7. Isolated nodes (potential orphans)
  8. Suggested next inspections
  9. Build provenance

Output: Markdown text. Caller writes to disk (e.g. via AOR Stage 7 writeback).

Design: reporter only reads from snapshot + topology results.
It never mutates anything.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .artifact import GraphSnapshot, Confidence
from .index import GraphIndex
from .topology import (
    top_by_degree,
    isolated_nodes,
    cross_domain_edges,
    ambiguous_edges,
    community_summary,
    connected_components,
)


def generate_report(
    snapshot: GraphSnapshot,
    index: GraphIndex,
    *,
    title: Optional[str] = None,
    max_top_nodes: int = 15,
    max_cross_domain: int = 20,
    max_ambiguous: int = 20,
    max_isolated: int = 20,
    max_communities: int = 10,
) -> str:
    """
    Generate a full operator graph analysis report as Markdown text.

    Parameters mirror the depth of analysis. Callers can tune these
    for narrower/broader reports without changing the report logic.
    """
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    report_title = title or f"ChaseOS Graph Substrate Report — {snapshot.snapshot_id[:8]}"

    # Run analytics
    top_nodes = top_by_degree(index, n=max_top_nodes)
    isolated = isolated_nodes(index)
    cross_domain = cross_domain_edges(index)
    ambig = ambiguous_edges(index)
    communities = community_summary(index)
    components = connected_components(index)
    stats = index.stats()

    lines = []

    # ── Header ────────────────────────────────────────────────────────────────
    lines += [
        "---",
        "type: graph-substrate-report",
        f"snapshot_id: {snapshot.snapshot_id}",
        f"generated_at: {generated_at}",
        "source: chaseos-graph-substrate",
        "mode: operator-read",
        "---",
        "",
        f"# {report_title}",
        "",
        f"> Snapshot `{snapshot.snapshot_id[:8]}` built from {len(snapshot.extraction_scope)} source scopes.",
        f"> This report surfaces structure, coupling, and review targets — it does NOT mutate canonical vault state.",
        "",
    ]

    # ── Summary stats ─────────────────────────────────────────────────────────
    lines += [
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total nodes | {stats['node_count']} |",
        f"| Total edges | {stats['edge_count']} |",
        f"| Source files extracted | {stats['source_files']} |",
        f"| Communities detected | {stats['community_count']} |",
        f"| Connected components | {len(components)} |",
        f"| Isolated nodes | {len(isolated)} |",
        f"| Cross-domain edges | {len(cross_domain)} |",
        f"| Inferred/ambiguous edges | {len(ambig)} |",
        "",
        "### Node Type Breakdown",
        "",
    ]
    for ntype, count in sorted(stats["node_types"].items(), key=lambda x: -x[1]):
        lines.append(f"- **{ntype}**: {count}")

    lines += [
        "",
        "### Relation Type Breakdown",
        "",
    ]
    for rel, count in sorted(stats["relation_types"].items(), key=lambda x: -x[1]):
        lines.append(f"- **{rel}**: {count}")

    # ── Most connected nodes ───────────────────────────────────────────────────
    lines += [
        "",
        "## Most Connected Nodes (Architectural Cores)",
        "",
        "> These are the highest-degree nodes — likely core abstractions, central modules,",
        "> or heavily-referenced docs. High in-degree = many things reference this. High out-degree = this references many things.",
        "",
        "| Rank | Label | Type | Domain | In | Out | Total |",
        "|------|-------|------|--------|----|----|-------|",
    ]
    for rank, node in enumerate(top_nodes, 1):
        domain = node.get("domain") or "—"
        lines.append(
            f"| {rank} | `{_truncate(node['label'], 50)}` | {node['node_type']} | {domain} "
            f"| {node['in_degree']} | {node['out_degree']} | {node['degree']} |"
        )

    # ── Community summaries ────────────────────────────────────────────────────
    lines += [
        "",
        "## Community Summaries",
        "",
        "> Label propagation found structural clusters. Community 0 = largest cluster.",
        "> Communities suggest natural subsystem groupings — review for architectural alignment.",
        "",
    ]
    for comm in communities[:max_communities]:
        dom_breakdown = ", ".join(f"{d}:{c}" for d, c in sorted(comm["domain_breakdown"].items()))
        lines += [
            f"### Community {comm['community_id']} — {comm['size']} nodes",
            f"- **Dominant type**: {comm['dominant_type']}",
            f"- **Dominant domain**: {comm['dominant_domain']}",
            f"- **Domain breakdown**: {dom_breakdown or '—'}",
            f"- **Top members by degree**:",
        ]
        for m in comm["top_members"]:
            lines.append(f"  - `{_truncate(m['label'], 60)}` ({m['type']}, degree={m['degree']})")

    if len(communities) > max_communities:
        lines.append(f"\n*{len(communities) - max_communities} smaller communities omitted.*")

    # ── Cross-domain edges ─────────────────────────────────────────────────────
    lines += [
        "",
        "## Cross-Domain Edges",
        "",
        "> Edges spanning different domains. These may be intended couplings or",
        "> surprising dependencies worth reviewing for architecture drift.",
        "",
    ]
    if cross_domain:
        shown = cross_domain[:max_cross_domain]
        lines += [
            "| Relation | Source | Source Domain | Target | Target Domain | Confidence |",
            "|----------|--------|--------------|--------|---------------|------------|",
        ]
        for e in shown:
            lines.append(
                f"| {e['relation']} | `{_truncate(e['source_label'], 40)}` | {e['source_domain']} "
                f"| `{_truncate(e['target_label'], 40)}` | {e['target_domain']} | {e['confidence']} |"
            )
        if len(cross_domain) > max_cross_domain:
            lines.append(f"\n*{len(cross_domain) - max_cross_domain} additional cross-domain edges not shown.*")
    else:
        lines.append("*No cross-domain edges detected in this extraction scope.*")

    # ── Ambiguous / inferred edges ────────────────────────────────────────────
    lines += [
        "",
        "## Inferred and Ambiguous Edges",
        "",
        "> These edges were not directly extracted — they were inferred by heuristic.",
        "> Review before treating them as architectural truth.",
        "",
    ]
    if ambig:
        shown_ambig = ambig[:max_ambiguous]
        lines += [
            "| Relation | Source | Target | Confidence | Provenance |",
            "|----------|--------|--------|------------|-----------|",
        ]
        for e in shown_ambig:
            lines.append(
                f"| {e['relation']} | `{_truncate(e['source_label'], 40)}` "
                f"| `{_truncate(e['target_label'], 40)}` | {e['confidence']} | {e['provenance']} |"
            )
        if len(ambig) > max_ambiguous:
            lines.append(f"\n*{len(ambig) - max_ambiguous} additional inferred/ambiguous edges not shown.*")
    else:
        lines.append("*No inferred or ambiguous edges in this snapshot.*")

    # ── Isolated nodes ────────────────────────────────────────────────────────
    lines += [
        "",
        "## Isolated Nodes",
        "",
        "> Nodes with zero edges. May be orphaned definitions, unused imports,",
        "> or nodes whose connections fall outside the current extraction scope.",
        "",
    ]
    if isolated:
        shown_isolated = isolated[:max_isolated]
        for node_id in shown_isolated:
            node = index.node_by_id.get(node_id)
            label = node.label if node else node_id
            ntype = node.node_type if node else "unknown"
            lines.append(f"- `{_truncate(label, 60)}` ({ntype})")
        if len(isolated) > max_isolated:
            lines.append(f"*{len(isolated) - max_isolated} additional isolated nodes not shown.*")
    else:
        lines.append("*No isolated nodes — all extracted nodes have at least one connection.*")

    # ── Suggested next inspections ────────────────────────────────────────────
    lines += [
        "",
        "## Suggested Next Inspections",
        "",
    ]
    suggestions = _generate_suggestions(
        top_nodes, cross_domain, ambig, isolated, communities, components, stats
    )
    for suggestion in suggestions:
        lines.append(f"- {suggestion}")

    # ── Connected component summary ────────────────────────────────────────────
    if len(components) > 1:
        lines += [
            "",
            "## Connected Components",
            "",
            f"> {len(components)} separate connected components detected.",
            "> Components other than the main one may indicate disconnected subsystems or extraction scope gaps.",
            "",
        ]
        for idx, component in enumerate(components[:5]):
            if idx == 0:
                lines.append(f"- **Component 0 (main)**: {len(component)} nodes")
            else:
                sample_nodes = []
                for nid in component[:3]:
                    node = index.node_by_id.get(nid)
                    if node:
                        sample_nodes.append(node.label)
                lines.append(f"- **Component {idx}**: {len(component)} nodes — e.g. {', '.join(sample_nodes)}")
        if len(components) > 5:
            lines.append(f"*{len(components) - 5} additional small components not shown.*")

    # ── Build provenance ──────────────────────────────────────────────────────
    lines += [
        "",
        "## Build Provenance",
        "",
        f"- **Snapshot ID**: `{snapshot.snapshot_id}`",
        f"- **Created at**: {snapshot.created_at}",
        f"- **Vault root**: `{snapshot.vault_root}`",
        f"- **Extraction scope**: {len(snapshot.extraction_scope)} paths",
        "",
        "**Scope paths:**",
    ]
    for scope_path in snapshot.extraction_scope:
        lines.append(f"- `{scope_path}`")

    if snapshot.build_info:
        lines += ["", "**Extraction stats:**"]
        for key, val in snapshot.build_info.items():
            lines.append(f"- {key}: {val}")

    lines += [
        "",
        "---",
        "",
        "> ChaseOS Graph Substrate report — proposal only.",
        "> No vault state is modified by generating this report.",
        "> Operator review required before acting on graph findings.",
        "",
    ]

    return "\n".join(lines)


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def _generate_suggestions(
    top_nodes: list[dict],
    cross_domain: list[dict],
    ambig: list[dict],
    isolated: list[str],
    communities: list[dict],
    components: list[list[str]],
    stats: dict,
) -> list[str]:
    suggestions = []

    if top_nodes:
        top = top_nodes[0]
        suggestions.append(
            f"Inspect `{top['label']}` ({top['node_type']}) — highest degree node ({top['degree']} connections). "
            "This is likely a central abstraction."
        )

    if len(components) > 1:
        suggestions.append(
            f"{len(components)} disconnected components found. "
            "Investigate whether small components are intentional islands or extraction scope gaps."
        )

    if cross_domain:
        unique_domain_pairs: set[tuple] = {(e["source_domain"], e["target_domain"]) for e in cross_domain}
        if len(unique_domain_pairs) > 3:
            suggestions.append(
                f"{len(cross_domain)} cross-domain edges span {len(unique_domain_pairs)} domain pairs. "
                "Review for unintended coupling or missing abstraction layers."
            )

    if ambig:
        suggestions.append(
            f"{len(ambig)} inferred/ambiguous edges need verification. "
            "These were produced by heuristics, not direct extraction. Review before treating as structural truth."
        )

    if len(isolated) > 5:
        suggestions.append(
            f"{len(isolated)} isolated nodes have no edges. "
            "They may be out-of-scope references or genuinely orphaned definitions."
        )

    if communities and communities[0]["size"] > stats["node_count"] * 0.8:
        suggestions.append(
            "Most nodes fall into a single community. "
            "The graph may be highly interconnected or the extraction scope may be too narrow to reveal clusters."
        )
    elif len(communities) > 5:
        suggestions.append(
            f"{len(communities)} communities detected. "
            "Review community boundaries for alignment with intended subsystem decomposition."
        )

    if stats.get("node_count", 0) < 20:
        suggestions.append(
            "Extraction scope produced fewer than 20 nodes. "
            "Consider expanding scope to adjacent runtime directories or architecture docs."
        )

    if not suggestions:
        suggestions.append("No specific anomalies detected. Review community summaries for subsystem structure.")

    return suggestions
