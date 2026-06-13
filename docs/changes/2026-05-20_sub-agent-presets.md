---
title: Sub-Agent Presets Pass 1
date: 2026-05-20
runtime: Codex
status: PARTIAL / PASS 1 IMPLEMENTED / VERIFIED
branch: codex/2026-05-20-sub-agent-presets
---

# Sub-Agent Presets Pass 1

## Summary

Implemented the first safe ChaseOS sub-agent preset layer as editable instruction
packs plus importable runtime helpers. This pass supports loading, validating,
routing, policy-checking, output-contract checking, activation-context creation,
checkpoint shaping, teardown shaping, and audit-event shaping.

This pass does not execute sub-agents, start daemon processes, enqueue Agent Bus
tasks, call providers, launch browsers, write governed memory, or mutate live
sites.

## Repo Truth

- Existing runtime integration is Agent Bus centered. Hermes and OpenClaw have
  active capability manifests and runtime profiles.
- Hermes, OpenClaw, and Chaser Agent are the ChaseOS 24/7 harness/runtime family.
- Archon is not a portable ChaseOS Core runtime; it is the operator's personal Claude Code instance name.
- OpenHuman is not an active backend in current repo truth. The current profile
  marks it retired/reference-only, so Pass 1 models it but blocks it by default.
- Existing sub-agent logic lives under VentureOps Mission Mode and
  `06_AGENTS/Sub-Agent-Orchestration-Standard.md`; it is mission-specific, not a
  global editable preset registry.
- Workspace Mode Layer and SiteOps already provide mode, approval, policy, and
  budget patterns that this pass reuses conceptually.

## Gap Map

- Missing before this pass: a global preset schema, default preset files,
  registry loader, runtime router, activation lifecycle context, per-preset tool
  and memory policy checks, output-contract validation, and test coverage.
- Still missing after this pass: CLI commands, Studio UI management, Agent Bus
  enqueue/claim integration, approval-center consumption, live runtime execution,
  persistent activation logs, user-authored preset editing UI, and mode-specific
  auto-selection inside Workspace/Mission/VentureOps/SiteOps flows.

## Proposed Module Plan

- `subagents/`: editable preset root.
- `subagents/presets/`: built-in instruction packs.
- `subagents/teams/`: mode-specific team templates.
- `subagents/schemas/`: JSON schema references for preset and team records.
- `runtime/subagents/models.py`: preset, policy, lifecycle, budget, output, and
  activation-context models.
- `runtime/subagents/registry.py`: filesystem-backed registry for built-in and
  user presets.
- `runtime/subagents/router.py`: runtime selection against current Agent Bus
  capability truth, with OpenHuman blocked unless explicitly included later.
- `runtime/subagents/policies.py`: deny/approval/allow checks.
- `runtime/subagents/activation.py`: task-scoped context builder, checkpoint,
  and teardown helpers.
- `runtime/subagents/output.py`: structured Markdown section validation.
- `runtime/subagents/telemetry.py`: audit-event shaping and suggested log path.

## Behavior Added

- Added nine default presets: CEO/Orchestrator, Research, Engineering,
  QA/Testing, Product Analysis, Marketing/Content, Site Ops, Venture Ops, and
  Memory/Documentation.
- Added five team templates for workspace, mission, venture_ops, site_ops, and
  server modes.
- Added validation that rejects unknown modes, unknown runtime preferences,
  secret-shaped allowed tools, secret-shaped memory reads/writes, and
  unrestricted memory writes.
- Added runtime routing that maps `HermesAgent` to `Hermes`, maps `OpenClaw` to
  `OpenClaw`, and treats `OpenHuman` as unavailable under current repo truth.
- Added activation contexts that are explicitly task-scoped and record
  `daemon_started=False`.

## Verification

- `python -m py_compile runtime\subagents\__init__.py runtime\subagents\models.py runtime\subagents\registry.py runtime\subagents\router.py runtime\subagents\policies.py runtime\subagents\activation.py runtime\subagents\output.py runtime\subagents\telemetry.py runtime\subagents\test_subagents.py`
  - Result: PASS.
- `uv run --offline --with pytest --with pyyaml python -m pytest runtime\subagents\test_subagents.py -q`
  - Result: PASS, `7 passed in 0.80s`.
- `uv run --offline --with pyyaml python -c "from pathlib import Path; from runtime.subagents import SubAgentRegistry, SubAgentRuntimeRouter; root=Path.cwd(); preset=SubAgentRegistry(vault_root=root).get_preset('site-ops-worker'); route=SubAgentRuntimeRouter(vault_root=root).select_runtime(preset); print(route.route_status, route.selected_runtime, route.selected_bus_name)"`
  - Result: PASS, `selected OpenClaw OpenClaw`.

## Boundary

- No always-on sub-agent daemon was created.
- No Agent Bus task was written or claimed.
- No provider/model call was made.
- No browser/profile/session was launched.
- No SiteOps live action, publish, payment, trade, or form submit was executed.
- No governed memory, Pulse memory, Personal Map, or R&D truth-state mutation was
  performed.

## Next Steps

1. Add a CLI read/validate/route-preview surface for sub-agent presets.
2. Add approval-preview integration before any activation can enqueue work.
3. Add Studio UI only after CLI and approval-preview behavior are proven.
4. Decide whether OpenHuman should remain reference-only or receive a new active
   backend profile before enabling it in routing.
