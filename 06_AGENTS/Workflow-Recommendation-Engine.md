---
type: architecture
title: Workflow Recommendation Engine
status: PARTIAL / READ-ONLY RUNTIME HELPER VERIFIED
updated: 2026-05-10
runtime: Codex
---

# Workflow Recommendation Engine

The VentureOps recommendation engine maps an instance profile to draft workflow-pack suggestions. A recommendation is an operator aid, not execution approval and not proof that a workflow is implemented.

Implemented helper: `runtime/ventureops/recommendations.py`

## Required Recommendation Fields

- `workflow_id`
- `workflow_name`
- `target_user_or_customer`
- `domain`
- `problem_solved`
- `why_suggested`
- `evidence_files`
- `confidence_score`
- `required_inputs`
- `required_context`
- `required_runtime_surfaces`
- `approval_requirements`
- `expected_outputs`
- `proof_artifact`
- `monetization_path`
- `risks`
- `first_safe_next_step`

## Recommendation Rules

- Cite local evidence files.
- Mark uncertainty honestly.
- Never infer active projects without evidence.
- Never claim implementation, revenue, customer value, or live execution without proof.
- Unknown/sparse workspaces receive discovery questions instead of confident workflow suggestions.
- External sends, payments, publication, account mutation, live browser actions, and trading are approval-gated.
- Crypto/trading workflow packs are optional domain packs and require direct instance evidence.

## Status

PARTIAL. The deterministic helper and validators exist and are covered by focused tests. No live execution, marketplace ranking, provider-based synthesis, or Studio recommendation UI exists yet.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
