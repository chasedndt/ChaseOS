---
type: framework-standard
title: Sub-Agent Orchestration Standard
status: PARTIAL / STANDARD AND HELPER IMPLEMENTED
created: 2026-05-13
updated: 2026-05-13
---

# Sub-Agent Orchestration Standard

Mission Mode splits long-term objectives into role-bound sub-agents. A mission should not be one vague agent doing everything.

## Standard Roles

- mission_supervisor
- planner
- researcher
- tool_operator
- critic_validator
- security_reviewer
- growth_operator
- commerce_operator
- career_operator
- runtime_operator
- presenter

## Authority Rule

Sub-agent assignment never grants new permissions. A sub-agent may only produce the outputs its assignment allows, and execution still routes through AOR, Gate, Agent Bus, workflow manifests, role cards, proof artifacts, and audit logs.

Unknown runtime roles fail closed.

## Runtime Preferences

- Hermes: mission supervision, planning, research, reviews, advisory drafting.
- Codex: repo implementation, schemas, tests, validation, documentation sync.
- OpenClaw/browser runtime: supervised browser/GUI proof collection only through BOSL/Gate/AOR boundaries.
- Strong model: high-reasoning planning, architecture, safety review, workflow evolution review.
- Human: external effects, protected edits, financial decisions, canonical promotion, and final approval.

Schema: `runtime/ventureops/templates/sub_agent_plan_schema.yaml`

Validator: `runtime.ventureops.validation.validate_sub_agent_plan`

Helper: `runtime.ventureops.sub_agents.build_sub_agent_plan`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
