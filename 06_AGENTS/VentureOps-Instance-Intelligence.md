---
type: architecture
title: VentureOps Instance Intelligence
status: PARTIAL / READ-ONLY RUNTIME HELPER VERIFIED
updated: 2026-05-10
runtime: Codex
---

# VentureOps Instance Intelligence

VentureOps Instance Intelligence is the portable profiling contract that lets ChaseOS suggest workflow packs from the user's own workspace evidence. It does not assume Chase's dashboard, ventures, crypto/trading context, or project list.

## Workspace Modes

| Mode | Meaning | Recommendation posture |
|---|---|---|
| `chaseos_native` | Strong ChaseOS markers are present. | Evidence-backed draft workflow recommendations. |
| `partial_chaseos` | Some ChaseOS markers are present. | Draft recommendations with missing-info prompts. |
| `general_markdown` | Markdown/Obsidian evidence exists without full ChaseOS structure. | Low/medium confidence draft recommendations only. |
| `unknown_sparse` | Too little structure or evidence. | Discovery questions, not workflow claims. |

## Runtime Contract

Implemented helper: `runtime/ventureops/instance_profile.py`

The helper reads bounded Markdown samples and ChaseOS marker files, then produces:

- detected workspace mode
- detected domains
- active/dormant project evidence
- monetization signals
- workflow opportunities
- evidence file references
- missing information
- discovery questions
- readiness level
- authority boundary

## Authority Boundary

The profiler is read-only. It does not write the workspace, call providers, call connectors, read secrets, perform browser automation, execute workflows, mutate Gate/AOR/MCP/Studio state, or promote canonical truth.

## RAG / Retrieval Posture

This pass uses deterministic local Markdown/folder/frontmatter/tag scanning. No new vector database was added. Future RAG/vector retrieval may be proposed only after deterministic evidence-backed recommendation quality is insufficient and a bounded local interface exists.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
