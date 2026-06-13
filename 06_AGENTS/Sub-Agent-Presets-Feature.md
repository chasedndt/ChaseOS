---
date: 2026-05-21
runtime: Codex
type: feature-node
status: PARTIAL / CONTRACT LANES VERIFIED / LIVE EXECUTION NOT BUILT
parent_families:
  - Autonomous Operator Runtime
  - Agent Control Plane
  - Chaser Forge
  - VentureOps
studio_surface: none primary yet
---

# Sub-Agent Presets Feature

Sub-Agent Presets define task-scoped worker presets and default teams that can be selected, validated, routed, approval-previewed, and eventually handed to the Agent Bus under ChaseOS governance.

They are not always-running runtimes and do not bypass the Agent Control Plane.

## Current Scope

- Preset and team schemas exist.
- Nine default preset files exist.
- Five default team files exist.
- Registry, router, activation helpers, CLI list/show/validate/route-preview, approval preview, guarded pending request writing, approval consumption dry-run, immutable decision artifact, decision-binding preflight, exact-once marker contract, and inert Agent Bus task packet preview are implemented/verified.
- CLI contract exposes 11 `subagents` commands: `list`, `show`, `validate`, `route-preview`, `approval-preview`, `write-approval-request`, `approval-consumption-dry-run`, `approval-review-decision`, `approval-consumption-decision-binding`, `agent-bus-task-packet-preview`, and `approval-consumption-exact-once-marker-contract`.

## Current Status

PARTIAL / VERIFIED through inert Agent Bus task packet preview.

Still blocked:

- Agent Bus task enqueue writer
- full approval/decision consumer
- request/decision mutation
- daemon start
- live runtime dispatch
- Studio Approval Center integration
- live sub-agent execution

## Observed Presets

- `ceo-orchestrator`
- `memory-documentation-worker`
- `research-worker`
- `engineering-worker`
- `qa-testing-worker`
- `site-ops-worker`
- `marketing-content-worker`
- `product-analysis-worker`
- `venture-ops-worker`

## Observed Teams

- `default-mission-team`
- `default-server-team`
- `default-site-ops-team`
- `default-venture-ops-team`
- `default-workspace-team`

## Canonical Sources

- `docs/features/CHASE_OS_SUB_AGENT_PRESETS.md`
- `subagents/README.md`
- `runtime/subagents/`
- `07_LOGS/Build-Logs/2026-05-20-ChaseOS-sub-agent-presets-approval-consumption-exact-once-marker-contract.md`
- `07_LOGS/Build-Logs/2026-05-20-ChaseOS-sub-agent-presets-agent-bus-task-packet-preview.md`
- `runtime/cli/command_contract.json`
- `docs/audits/2026-05-21_feature_family_deep_reconciliation.md`

## Graph Links

[[Autonomous-Operator-Runtime]] [[Agent-Control-Plane]] [[Chaser-Forge-Feature-Family]] [[ChaseOS-Feature-Family-and-Subfeature-Inventory]]
