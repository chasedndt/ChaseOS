---
type: framework-standard
title: Workflow Evolution Proposal Standard
status: PARTIAL / STANDARD AND VALIDATOR IMPLEMENTED
created: 2026-05-13
updated: 2026-05-13
---

# Workflow Evolution Proposal Standard

A workflow evolution proposal is the only Mission Mode artifact allowed to suggest changing workflow behavior.

## Required Fields

- proposal_id
- mission_id
- workflow_id
- current_workflow_version
- proposed_workflow_version
- proposal_type
- reason
- evidence
- risk_review
- expected_benefit
- failure_mode
- dry_run_plan
- approval_required
- auto_apply_allowed
- status

## Allowed Proposal Types

- threshold_change
- new_required_input
- new_blocked_condition
- new_approval_gate
- new_browser_skill_candidate
- new_site_profile
- new_scorecard_metric
- new_runtime_routing_rule
- new_domain_playbook_rule
- workflow_deprecation

## Boundary

Proposal status does not imply implementation. `approved` means the operator accepted the idea; applying the change still requires a versioned implementation path. `applied` requires a linked approval id and implementation evidence.

Schema: `runtime/ventureops/templates/workflow_evolution_proposal_schema.yaml`

Validator: `runtime.ventureops.validation.validate_workflow_evolution_proposal`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
