---
title: Adaptive Runtime Surface Layer Audit
type: feature-audit
status: PARTIAL
created: 2026-05-03
runtime: Codex
session: 2026-05-03_adaptive-runtime-surface-layer-audit
---

# Adaptive Runtime Surface Layer Audit

## Post-Audit Update

2026-05-03 Phase 1 now exists under `runtime/runtime_surfaces/` as a read-only manifest schema and registry loader. The audit verdict remains true for full ARSL: ChaseOS still does not have live ARSL routing, routing ledger writes, browser domain skill promotion integration, or MCP exposure.

## Verdict

ChaseOS does not yet have a complete Adaptive Runtime Surface Layer.

ChaseOS does have substantial partial pieces:

- Runtime provider governance exists through RPGL.
- Runtime/task routing exists through AOR and the Agent Bus capability router.
- Browser operator control exists as a bounded Playwright-backed operator surface.
- Browser runtime and browser skill memory exist as partial, proposal-first substrates.
- SiteOps exists as a dry-run registry and promotion/control scaffold for website workflows and skill cards.
- Runtime MCP exists as a bounded read/proposal interface.

The missing feature is the unified cross-cutting layer that detects, registers, classifies, routes, and audits all execution surfaces under one canonical manifest and registry model, including browser surfaces, agent runtimes, embedded/client runtimes, and future domain-specific browser skills.

## Repo-Truth Delta

Current:

- Phase 9 Operator Runtime is active.
- AOR is partial but live for bounded workflows.
- RPGL is implemented as a targeted provider-governance foundation, with real provider proof deferred or approval-bound where noted by repo docs.
- Browser Operator Surface is parked but has live bounded command surfaces and real Playwright primitives.
- Browser Runtime Skill Memory is partial and proposal-first.
- SiteOps is a registry, dry-run, policy, approval, candidate, and inactive-artifact scaffold, not broad live website automation.
- Agent Bus can route task packets to registered runtimes by capability and liveness.
- Runtime MCP is partial, stdio/local, read/proposal-first, and not a broad execution layer.

Stale or incomplete relative to the feature concept:

- No single runtime surface manifest schema spans providers, browser operators, client runtimes, MCP, AOR, and SiteOps.
- No unified risk-classification registry for every surface capability exists.
- No implemented WebAssembly, WebGPU, WebContainer, or browser-hosted local-model runtime registry exists.
- Browser domain skill memory is present but not a trusted active automation layer.
- Browser Use / Browser Harness / CDP integration remains reference-only or gated/no-execution except for explicitly documented proof paths.

Unknown or unverified:

- Whether all current runtime capability manifests are complete enough for a unified surface layer without normalization.
- Whether client-side runtime categories should be first-class runtime instances, provider surfaces, or operator surfaces.
- Whether future MCP exposure should serve the unified registry directly or via curated resources only.

## Existing Overlaps

### Runtime provider routing and fallback governance

Implemented or partially implemented:

- `runtime/providers/governance_layer.py` - RPGL task-class authority matrix, provider strength classification, queue-on-denial, fallback denial for weak models, audit events, approval chains, provider config proposals, and guarded live-probe/config apply paths.
- `runtime/providers/README.md` - current provider registry/state-ledger truth.
- `runtime/providers/registry.py` - setup/provider registry inspection.
- `runtime/providers/provider_call_surfaces.json` - machine-readable classification of provider/model/connector/delivery/lifecycle call surfaces.
- `runtime/providers/call_surface_audit.py` - validates provider call-surface classification.
- `runtime/providers/state_ledger.py` - append-only provider-state evidence.
- `runtime/execution_adapters/execute.py` - shared model execution path that emits provider-state events and consults RPGL before fallback.
- `06_AGENTS/Runtime-Provider-Governance-Layer.md` - canonical RPGL doc.

Assessment: Strong partial. It governs model/provider fallback and prevents weak fallback from becoming sticky for serious work, but it is provider/model centered, not a universal runtime surface layer.

### Runtime registry and task routing

Implemented or partially implemented:

- `runtime/aor/runtime_registry.py` - machine-readable runtime instance registry substrate.
- `runtime/aor/task_router.py` - task-type classification, unclassified fail-closed sentinel, permission ceilings.
- `runtime/aor/task_type_table.yaml` - task type table.
- `runtime/agent_bus/capabilities.py` - runtime capability manifests under `runtime/<runtime>/capabilities.yaml`.
- `runtime/agent_bus/router.py` - routes by capability, liveness, stale thresholds, concurrency, priority ceiling.
- `runtime/codex/capabilities.yaml`
- `runtime/openclaw/capabilities.yaml`
- `runtime/hermes/capabilities.yaml`
- `runtime/chaser_agent/capabilities.yaml`
- `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
- `06_AGENTS/Agent-Bus-Backend-Architecture.md`
- `06_AGENTS/Autonomous-Operator-Runtime.md`

Assessment: Strong partial for agent-runtime task routing. It does not yet cover browser surfaces, provider surfaces, embedded runtimes, browser skill memory, and MCP exposure as one surface model.

### Browser operator surface

Implemented or partially implemented:

- `runtime/operator_surface/capabilities.py` - surface types and operator capabilities for browser, terminal, desktop, filesystem.
- `runtime/operator_surface/adapter_registry.py` - operator surface adapter registry by surface type.
- `runtime/operator_surface/contracts.py` - operator scope, session, approval, run audit contracts.
- `runtime/operator_surface/executor.py` - scope enforcement, approval gates, audit writing, adapter execution orchestration.
- `runtime/operator_surface/scopes.py`
- `runtime/operator_surface/audit.py`
- `runtime/operator_surface/adapters/base.py`
- `runtime/operator_surface/adapters/browser_adapter.py` - Playwright-backed browser adapter with isolated headless context and all 18 action handlers; partial status for accessibility/vision tiers.
- `runtime/operator_surface/browser/actions.py`
- `runtime/operator_surface/browser/policy.py`
- `runtime/operator_surface/browser/replay.py`
- `runtime/operator_surface/tests/test_browser_pass2.py`
- `runtime/operator_surface/tests/test_browser_pass3.py`
- `runtime/operator_surface/tests/test_browser_pass4.py`
- `runtime/operator_surface/tests/test_browser_pass5.py`
- `runtime/operator_surface/tests/test_browser_policy.py`
- `06_AGENTS/Browser-Operator-Surface.md`
- `06_AGENTS/Operator-Surface-Adapter-Spec.md`
- `06_AGENTS/Browser-Operator-Policy.md`
- `06_AGENTS/Browser-Autonomy-Policy.md`

Assessment: Strong partial for browser operator surfaces. It has the clearest existing insertion point for browser capabilities, action classes, approvals, and audit. It is not a general runtime surface registry.

### Browser runtime, domain skills, and workflow memory

Implemented or partially implemented:

- `runtime/browser_runtime/adapter.py` - bounded browser runtime adapter contract and shadow adapter.
- `runtime/browser_runtime/models.py`
- `runtime/browser_runtime/skills.py` - draft-only site skill generation from browser run evidence.
- `runtime/browser_runtime/candidates.py`
- `runtime/browser_runtime/site_memory.py`
- `runtime/browser_runtime/workflows.py`
- `runtime/browser_runtime/browser_harness_adoption.py`
- `runtime/browser_runtime/browser_use_cli_validation.py`
- `runtime/browser_runtime/cdp_executor_spec.py`
- `runtime/browser_runtime/config.yaml`
- `runtime/browser_skills/candidates.py`
- `runtime/browser_skills/registry.py`
- `runtime/browser_skills/shadow_runner.py`
- `runtime/browser_skills/validator.py`
- `runtime/browser_skills/schemas/browser_skill.schema.yaml`
- `runtime/browser_skills/skills/README.md`
- `runtime/browser_skills/skills/excalidraw/draw_basic_shape.yaml`
- `runtime/browser_workflows/metadata.json`
- `runtime/browser_workflows/workflows/`
- `06_AGENTS/Browser-Runtime-Harness.md`
- `06_AGENTS/Browser-Runtime-Skill-Memory.md`
- `06_AGENTS/Browser-Skill-Memory.md`
- `06_AGENTS/Browser-Operator-Skill-Layer.md`
- `06_AGENTS/Browser-Workflow-Cache.md`
- `06_AGENTS/Browser-Harness-Adoption-Decision.md`

Assessment: Strong partial for proposal-first skill memory. Trusted activation and live reuse remain gated, partial, or deferred. This aligns well with the proposed domain-specific browser skill memory requirement.

### SiteOps website workflow and skill-card layer

Implemented or partially implemented:

- `runtime/siteops/README.md`
- `runtime/siteops/registry.py`
- `runtime/siteops/policy.py`
- `runtime/siteops/approvals.py`
- `runtime/siteops/audit.py`
- `runtime/siteops/runner.py`
- `runtime/siteops/browser_profiles.py`
- `runtime/siteops/credentials.py`
- `runtime/siteops/candidate_promotions.py`
- `runtime/siteops/schemas/skill_card.schema.json`
- `runtime/siteops/schemas/workflow_manifest.schema.json`
- `runtime/siteops/schemas/browser_profile_ref.schema.yaml`
- `runtime/siteops/catalog/site_skill_templates.yaml`
- `runtime/siteops/catalog/provider_templates.yaml`
- `runtime/siteops/tests/test_candidate_promotions.py`
- `runtime/siteops/tests/test_siteops_dry_run.py`
- `runtime/siteops/tests/test_policy.py`
- `06_AGENTS/SiteOps-Browser-Session-Boundaries.md`
- `06_AGENTS/SiteOps-Candidate-Trusted-Executor-Design.md`
- `06_AGENTS/SiteOps-Product-Surface-Roadmap.md`

Assessment: Strong partial for governed website workflows and skill cards. It should consume browser skills and workflow manifests, not become the cross-runtime registry by itself.

### Runtime MCP

Implemented or partially implemented:

- `runtime/mcp/server.py`
- `runtime/mcp/config.py`
- `runtime/mcp/safety.py`
- `runtime/mcp/resources/runtime_capabilities.py`
- `runtime/mcp/resources/runtime_identity.py`
- `runtime/mcp/tests/test_runtime_mcp_v1.py`
- `runtime/mcp/tests/test_runtime_mcp_jsonrpc_stdio.py`
- `runtime/mcp/tests/test_runtime_mcp_stdio_client_smoke.py`
- `06_AGENTS/ChaseOS-Runtime-MCP.md`
- `06_AGENTS/ChaseOS-MCP-Server.md`
- `06_AGENTS/ChaseOS-MCP-Surface-Map.md`
- `06_AGENTS/ChaseOS-MCP-Guardrails.md`

Assessment: Partial exposure layer. MCP should expose a curated read-only view of runtime surfaces in a later phase, not own the source registry.

## Missing Components

Missing code modules:

- `runtime/runtime_surfaces/` or equivalent canonical package.
- `runtime/runtime_surfaces/surface.schema.json`
- `runtime/runtime_surfaces/registry.py`
- `runtime/runtime_surfaces/risk.py`
- `runtime/runtime_surfaces/router.py`
- `runtime/runtime_surfaces/audit.py`
- `runtime/runtime_surfaces/policy.py`
- `runtime/runtime_surfaces/manifests/*.yaml`
- `runtime/runtime_surfaces/tests/`

Missing docs:

- Canonical feature spec for cross-cutting runtime surfaces.
- Phase plan linking RPGL, AOR, Browser Operator, SiteOps, Agent Bus, and MCP without granting extra authority.
- Acceptance criteria for client-side/embedded runtime registration.
- Risk classification vocabulary shared across provider, browser, filesystem, terminal, MCP, and SiteOps actions.

Missing behavior:

- Unified capability normalization across agent runtimes, provider/model runtimes, browser operator surfaces, SiteOps skills, MCP tools, and client-side runtimes.
- Unified routing decision records that include why a surface was selected or denied.
- Surface detection/discovery protocol.
- Embedded runtime family registration for WebAssembly, WebGPU, WebContainer, local browser-hosted agents, and sandboxed browser runtimes.
- Cross-surface audit ledger for routing and execution outcomes.
- First-class review/promote flow for browser domain skills into trusted active automation.

## Feature Placement

Cleanest placement: a new cross-cutting layer under existing runtime governance.

Recommended home:

- `runtime/runtime_surfaces/` for code.
- `runtime/runtime_surfaces/manifests/` for first-party surface manifests.
- `06_AGENTS/Adaptive-Runtime-Surface-Layer.md` or the requested `docs/features/adaptive-runtime-surface-layer-spec.md` for docs.

Integration points:

- RPGL remains provider/model fallback authority.
- AOR remains workflow execution authority.
- Agent Bus remains runtime task coordination and liveness routing.
- Browser Operator Surface remains browser action execution authority.
- SiteOps remains website skill/workflow registry and review surface.
- Runtime MCP exposes curated registry/resource views only after Phase 6.

Do not place this solely under:

- Browser Operator Surface: too narrow.
- RPGL: too provider/model-specific.
- AOR: too execution-engine-specific.
- MCP: exposure layer, not authority source.
- SiteOps: website workflow layer, not all runtime surfaces.

## Canonical Name Recommendation

Recommended canonical feature name: Adaptive Runtime Surface Layer.

Comparison:

- Adaptive Runtime Surface Layer: best fit. Covers dynamic discovery, capability normalization, routing, risk, browser and non-browser surfaces, and future embedded runtimes.
- Runtime Surface Registry: good subsystem name, but too static for routing/adaptation.
- Runtime Capability Mesh: evocative, but less clear and risks sounding like distributed autonomy.
- Browser Skill Runtime Layer: too browser-specific.
- Execution Surface Adapter Layer: accurate for adapters, but misses provider governance, skill memory, and routing decisions.

Suggested internal subsystem names:

- Feature: Adaptive Runtime Surface Layer (ARSL)
- Registry module: Runtime Surface Registry
- Manifest type: Runtime Surface Manifest
- Routing ledger: Runtime Surface Routing Ledger

## Recommended Architecture

ARSL should be a registry and policy-normalization layer, not a new executor.

Core responsibilities:

- Load surface manifests from declared locations.
- Normalize capabilities into a shared vocabulary.
- Classify capabilities and actions by risk.
- Link every surface to existing authority: RPGL, AOR, Agent Bus, Browser Operator, SiteOps, or MCP.
- Produce routing recommendations and denials.
- Write auditable routing decisions.
- Fail closed on unknown surface type, unknown capability, missing trust ceiling, missing permission envelope, or unclassified risk.

Authority boundaries:

- No ambient browser control.
- No unrestricted vault access.
- No credential handling.
- No silent provider/model fallback.
- No direct canonical writeback.
- No trusted browser skill activation without review.
- No automatic expansion of Trust Tier, Permission Matrix, Gate, or Agent Control Plane authority.

## Proposed File Map

New docs:

- `docs/features/adaptive-runtime-surface-layer-audit.md`
- `docs/features/adaptive-runtime-surface-layer-spec.md`
- `docs/changes/2026-05-03_adaptive_runtime_surface_layer_audit.md`

Future code:

- `runtime/runtime_surfaces/__init__.py`
- `runtime/runtime_surfaces/models.py`
- `runtime/runtime_surfaces/schema.py`
- `runtime/runtime_surfaces/registry.py`
- `runtime/runtime_surfaces/risk.py`
- `runtime/runtime_surfaces/router.py`
- `runtime/runtime_surfaces/audit.py`
- `runtime/runtime_surfaces/policy.py`
- `runtime/runtime_surfaces/manifests/browser_operator.yaml`
- `runtime/runtime_surfaces/manifests/rpgl_provider_runtime.yaml`
- `runtime/runtime_surfaces/manifests/agent_bus_codex.yaml`
- `runtime/runtime_surfaces/manifests/siteops_skill_runtime.yaml`
- `runtime/runtime_surfaces/manifests/runtime_mcp.yaml`
- `runtime/runtime_surfaces/schemas/runtime_surface_manifest.schema.json`
- `runtime/runtime_surfaces/tests/test_runtime_surface_manifest_schema.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_registry.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_risk.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_router.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_audit.py`

Future docs:

- `06_AGENTS/Adaptive-Runtime-Surface-Layer.md`
- `06_AGENTS/Runtime-Surface-Manifest-Standard.md`
- `06_AGENTS/Runtime-Surface-Risk-Taxonomy.md`
- `06_AGENTS/Runtime-Surface-Routing-Audit.md`

## Implementation Phases

### Phase 0: Repo Audit and Gap Map

Status: this pass.

Outputs:

- Audit report.
- Spec scaffold.
- Change note.
- Session trace logs.

### Phase 1: Runtime Surface Manifest Schema

Define a manifest with:

- `surface_id`
- `surface_family`
- `surface_type`
- `owner_layer`
- `status`
- `trust_ceiling`
- `permission_model_ref`
- `gate_operations`
- `capabilities`
- `risk_classes`
- `routing_inputs`
- `execution_boundary`
- `writeback_surfaces`
- `audit_targets`
- `credential_policy`
- `fallback_policy`
- `skill_memory_policy`
- `mcp_exposure_policy`

### Phase 2: Capability Registry and Risk Classification

Build a registry that loads manifests and validates declared capabilities, risk classes, trust ceilings, permission references, blocked actions, approval-required actions, and audit targets.

### Phase 3: Provider/Runtime Routing Integration

Integrate without replacing:

- RPGL provider decisions,
- Agent Bus capability router,
- AOR task router,
- operator-surface adapter registry.

ARSL should produce a routing decision record that references the underlying authoritative decision rather than reimplementing it.

### Phase 4: Browser Domain Skill Memory

Normalize browser skill candidates and SiteOps skill cards as runtime surface capabilities.

Rules:

- candidates are untrusted data,
- trusted skills require review,
- activation requires explicit approval/Gate path,
- no credentials, cookies, sessions, browser profile paths, or private browser history,
- learned workflows remain proposal-first until promoted.

### Phase 5: Audit Logs, Tests, and Docs

Add route-decision JSONL ledger, CLI read-only inspection, manifest validation tests, risk policy tests, no-ambient-authority tests, and docs linking ARSL to Agent Control Plane, Permission Matrix, Trust Tiers, AOR, RPGL, Browser Operator, SiteOps, and MCP.

### Phase 6: Optional MCP Exposure

Expose only curated read-only resources:

- `runtime.surfaces`
- `runtime.surface_capabilities`
- `runtime.surface_routing_policy`
- `runtime.surface_audit_recent`

Do not expose raw policy files, secrets, arbitrary manifest file paths, write/apply tools, or broad browser operation.

## Test Strategy

Phase 1 tests:

- manifest schema accepts valid first-party surfaces,
- rejects missing trust ceiling,
- rejects unknown surface type,
- rejects credential access without explicit forbidden/default-deny policy,
- rejects activation-capable browser skills without review state.

Phase 2 tests:

- risk taxonomy classifies read, draft, action, mutation, credential, external, destructive, and canonical-write classes,
- unknown capability fails closed,
- weak provider cannot route high-authority development.

Phase 3 tests:

- Agent Bus route decisions remain unchanged for existing task types,
- RPGL still denies weak fallback for high-authority tasks,
- AOR task router still escalates unclassified tasks,
- browser operator actions still require current approval gates.

Phase 4 tests:

- browser skill candidates remain untrusted,
- trusted skill activation is blocked without approval,
- candidates cannot contain credentials, cookies, tokens, browser profiles, or absolute-only coordinate recipes.

Phase 5 tests:

- every route decision writes an audit event,
- denied routes record reason and source policy,
- successful route records selected authority layer,
- audit ledger can be summarized read-only.

Phase 6 tests:

- MCP resources are read-only,
- no arbitrary path exposure,
- no write/apply tool exposure,
- permission envelope narrows returned surfaces by runtime.

## Risks

- Duplicating RPGL, AOR, SiteOps, or Browser Operator logic instead of referencing it.
- Accidentally making a registry look like an authority grant.
- Treating browser-learned skill candidates as trusted instructions.
- Letting weak/local fallback become sticky for serious work.
- Registering client-side runtimes without sandbox boundaries.
- Exposing too much policy detail through MCP to governed runtimes.
- Adding browser/session capability without explicit approval, audit, and credential isolation.

## Acceptance Criteria

ARSL is acceptable only when every runtime surface is represented by a validated manifest, every capability has a risk class, every routing decision is auditable, unknown surfaces fail closed, browser skills remain proposal-first until reviewed, RPGL remains provider fallback authority, AOR remains execution authority, Agent Bus remains coordination authority, SiteOps remains website workflow/skill authority, Runtime MCP remains read/proposal-only unless separately approved, and no secrets, credentials, cookies, browser profiles, or protected write guards are weakened.
