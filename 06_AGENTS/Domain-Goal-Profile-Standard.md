---
type: framework-standard
title: Domain Goal Profile Standard
status: PARTIAL / STANDARD AND VALIDATOR IMPLEMENTED
created: 2026-05-13
updated: 2026-05-13
---

# Domain Goal Profile Standard

A domain goal profile describes what a user is trying to improve in one domain without hard-coding Chase's personal dashboard.

## Required Fields

- domain
- user_goal
- current_assets
- current_constraints
- preferred_tools
- forbidden_tools
- risk_tolerance
- approval_preferences
- success_metrics
- available_capital
- available_time
- current_workflows
- known_strategies
- known_failure_patterns
- recommended_workflow_packs
- missing_context
- readiness_level

## Portability Rule

Mission Mode must work across Chase's personal ChaseOS instance, another ChaseOS instance, partial ChaseOS instances, general markdown/Obsidian workspaces, and sparse workspaces. Sparse workspaces should produce discovery questions rather than confident mission recommendations.

## Financial Boundary

Trading and financial profiles default to analysis, journal, paper, and risk-review modes. Live execution, funds movement, leverage changes, and financial actions require explicit human approval and a separate governed path.

Schema: `runtime/ventureops/templates/domain_goal_profile_schema.yaml`

Validator: `runtime.ventureops.validation.validate_domain_goal_profile`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
