---
type: framework-standard
title: Mission Recommendation Standard
status: PARTIAL / EVIDENCE-BACKED HELPER IMPLEMENTED
created: 2026-05-13
updated: 2026-05-13
---

# Mission Recommendation Standard

Mission recommendations are instance-aware suggestions for long-running objectives.

## Required Rule

Every mission recommendation must cite local evidence files. If the workspace is sparse or unknown, Mission Mode must ask discovery questions instead of hallucinating missions.

## Recommendation Fields

- mission_candidate_id
- mission_name
- target_domain
- target_user
- objective
- why_suggested
- evidence_files
- confidence_score
- recommended_workflow_packs
- recommended_sub_agents
- required_inputs
- required_context
- required_integrations
- approval_requirements
- risk_class
- first_safe_next_step
- readiness_level

## Boundary

Recommendations do not create mission state, enqueue tasks, dispatch AOR workflows, call providers, activate browsers, or authorize external effects.

Schema: `runtime/ventureops/templates/mission_recommendation_schema.yaml`

Validator: `runtime.ventureops.validation.validate_mission_recommendation`

Helper: `runtime.ventureops.recommendations.build_mission_recommendations`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
