---
title: Adaptive Runtime Surface Layer Spec
type: feature-spec
status: PARTIAL
created: 2026-05-03
runtime: Codex
session: 2026-05-03_adaptive-runtime-surface-layer-audit
---

# Adaptive Runtime Surface Layer Spec

## Status

PARTIAL. The 2026-05-03 Phase 1 pass implemented the read-only runtime surface manifest schema, validated manifest model, registry loader, first-party manifests, and focused tests. The 2026-05-03 Phase 2 pass added normalized risk taxonomy and policy classification helpers. The 2026-05-03 Phase 3 pass added a read-only routing proposal helper. The 2026-05-03 Phase 4 pass added read-only browser skill memory normalization. The 2026-05-03 Phase 5 pass added append-only routing decision ledger support. The 2026-05-03 Phase 6 pass exposed a curated read-only ARSL summary through Runtime MCP. The 2026-05-04 canonical-docs pass added protected framework-control docs for ARSL and the Runtime Surface Manifest Standard. The 2026-05-04 CLI-inspection pass added read-only operator CLI summaries for registry and capability-policy inspection. The 2026-05-04 manifest-expansion passes added Hermes, OpenClaw, and Archon Agent Bus runtime manifests plus bounded OpenAI dry-run and local Ollama timeout-contract provider manifests. The 2026-05-04 client/embedded audit pass added the Studio sandboxed static artifact mount manifest. The 2026-05-04 route-review pass added a read-only operator route review contract and CLI preview. ARSL still does not execute work, activate browser skills, grant new authority, expose raw manifests, or provide MCP tools.

Implemented files:

- `runtime/runtime_surfaces/schemas/runtime_surface_manifest.schema.json`
- `runtime/runtime_surfaces/models.py`
- `runtime/runtime_surfaces/registry.py`
- `runtime/runtime_surfaces/manifests/*.yaml`
- `runtime/runtime_surfaces/manifests/agent_bus_archon.yaml`
- `runtime/runtime_surfaces/manifests/agent_bus_hermes.yaml`
- `runtime/runtime_surfaces/manifests/agent_bus_openclaw.yaml`
- `runtime/runtime_surfaces/manifests/client_studio_sandboxed_static_mount.yaml`
- `runtime/runtime_surfaces/manifests/provider_openai_responses_mcp_dry_run.yaml`
- `runtime/runtime_surfaces/manifests/provider_local_ollama_timeout_contract.yaml`
- `runtime/runtime_surfaces/risk.py`
- `runtime/runtime_surfaces/policy.py`
- `runtime/runtime_surfaces/router.py`
- `runtime/runtime_surfaces/review_contract.py`
- `runtime/runtime_surfaces/browser_skill_memory.py`
- `runtime/runtime_surfaces/audit.py`
- `runtime/runtime_surfaces/inspection.py`
- `runtime/runtime_surfaces/state/routing_decisions.jsonl`
- `runtime/mcp/resources/runtime_surfaces.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- `06_AGENTS/Adaptive-Runtime-Surface-Layer.md`
- `06_AGENTS/Runtime-Surface-Manifest-Standard.md`
- `runtime/runtime_surfaces/tests/test_runtime_surface_registry.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_risk.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_router.py`
- `runtime/runtime_surfaces/tests/test_browser_skill_memory.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_audit.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_cli_inspection.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_route_review.py`
- `runtime/mcp/tests/test_runtime_mcp_runtime_surfaces.py`

## Feature Name

Canonical name: Adaptive Runtime Surface Layer (ARSL).

Subsystem names:

- Runtime Surface Registry
- Runtime Surface Manifest
- Runtime Surface Risk Taxonomy
- Runtime Surface Routing Ledger

## Purpose

ARSL is the governed abstraction layer that lets ChaseOS detect, register, classify, route, and audit work across execution surfaces without granting new ambient authority.

It covers browser operator surfaces, agent runtime providers, provider/model runtimes, client-side and embedded runtimes, browser skill memory, and MCP-facing read-only capability exposure.

ARSL does not execute work directly. It produces validated surface metadata and routing decisions that point to existing authority layers.

## Existing Authorities ARSL Must Preserve

| Authority | Existing home | ARSL relationship |
| --- | --- | --- |
| Provider/model fallback | `runtime/providers/governance_layer.py` | Consult and reference RPGL decisions |
| Workflow execution | `runtime/aor/` | AOR remains executor |
| Cross-runtime coordination | `runtime/agent_bus/` | Agent Bus remains task substrate |
| Browser action execution | `runtime/operator_surface/` | Browser adapter remains executor |
| Website workflows and skill cards | `runtime/siteops/` | SiteOps remains website skill/workflow authority |
| Runtime MCP exposure | `runtime/mcp/` | Exposes curated read-only ARSL views only |
| Gate and permission boundaries | `runtime/chaseos_gate.py`, `06_AGENTS/Permission-Matrix.md`, `06_AGENTS/Trust-Tiers.md`, `06_AGENTS/Agent-Control-Plane.md` | Never weaken or bypass |

## Manifest Shape

Initial manifest fields:

```yaml
schema_version: 1
surface_id: browser.operator.playwright
display_name: Browser Operator Surface
surface_family: browser_operator
surface_type: browser
owner_layer: operator_surface
status: PARTIAL
implementation_refs:
  - runtime/operator_surface/adapters/browser_adapter.py
  - runtime/operator_surface/browser/policy.py
docs_refs:
  - 06_AGENTS/Browser-Operator-Surface.md
trust_ceiling: tier-2
permission_model_refs:
  - 06_AGENTS/Permission-Matrix.md
  - 06_AGENTS/Trust-Tiers.md
gate_operations: []
capabilities:
  - capability_id: browser.read_state
    maps_to: browser_read_state
    risk_class: read_untrusted_external
    approval_required: false
  - capability_id: browser.click
    maps_to: browser_click
    risk_class: external_ui_mutation
    approval_required: conditional
credential_policy:
  credentials_allowed: false
  cookies_allowed: false
  real_profile_allowed: false
fallback_policy:
  sticky_fallback_allowed: false
writeback_surfaces:
  - 07_LOGS/Agent-Activity/
  - 07_LOGS/Operator-Screenshots/
audit_targets:
  - 07_LOGS/Agent-Activity/
routing_policy:
  default: deny_unknown
  authority_layer: runtime/operator_surface/
mcp_exposure_policy:
  expose_summary: true
  expose_raw_manifest: false
```

## Surface Families

Initial surface families:

- `provider_model_runtime`
- `agent_runtime`
- `browser_operator`
- `siteops_skill_runtime`
- `runtime_mcp`
- `client_embedded_runtime`
- `filesystem_surface`
- `terminal_surface`
- `desktop_surface`

## Risk Classes

Initial risk classes:

- `read_local_scoped`
- `read_untrusted_external`
- `draft_only`
- `proposal_write`
- `quarantine_write`
- `canonical_write`
- `external_ui_read`
- `external_ui_mutation`
- `external_network_call`
- `credential_sensitive`
- `browser_profile_sensitive`
- `provider_fallback`
- `runtime_config_change`
- `security_policy_change`
- `destructive_action`
- `blocked`

Unknown risk class fails closed.

## Routing Decision Record

ARSL routing decisions should be append-only JSONL:

```json
{
  "schema_version": 1,
  "decision_id": "arsl-route-example",
  "created_at": "2026-05-03T00:00:00Z",
  "request_id": "operator-or-workflow-request",
  "task_type": "code.patch",
  "requested_capability": "repo.patch",
  "candidate_surfaces": ["agent.codex.bus"],
  "selected_surface": "agent.codex.bus",
  "decision": "allow",
  "authority_layer": "runtime/agent_bus",
  "policy_refs": [
    "06_AGENTS/Agent-Control-Plane.md",
    "runtime/codex/capabilities.yaml"
  ],
  "risk_class": "proposal_write",
  "trust_ceiling": "tier-2",
  "approval_required": false,
  "denial_reasons": [],
  "audit_refs": []
}
```

## Phase Plan

### Phase 0: Repo Audit and Gap Map

This pass. Produce audit, spec, change note, and session trace logs.

### Phase 1: Runtime Surface Manifest Schema

Status: COMPLETE TARGETED / READ-ONLY.

Implemented schema and model validation only. This phase loads first-party surface manifests and fails closed on unknown surface families, surface types, risk classes, credential grants, sticky fallback, raw MCP manifest exposure, duplicate surface IDs, and missing referenced implementation/docs/policy files.

Target files:

- `runtime/runtime_surfaces/schemas/runtime_surface_manifest.schema.json`
- `runtime/runtime_surfaces/models.py`
- `runtime/runtime_surfaces/registry.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_registry.py`

First-party manifests:

- `runtime/runtime_surfaces/manifests/agent_bus_archon.yaml`
- `runtime/runtime_surfaces/manifests/agent_bus_codex.yaml`
- `runtime/runtime_surfaces/manifests/agent_bus_hermes.yaml`
- `runtime/runtime_surfaces/manifests/agent_bus_openclaw.yaml`
- `runtime/runtime_surfaces/manifests/browser_operator.yaml`
- `runtime/runtime_surfaces/manifests/client_studio_sandboxed_static_mount.yaml`
- `runtime/runtime_surfaces/manifests/provider_openai_responses_mcp_dry_run.yaml`
- `runtime/runtime_surfaces/manifests/provider_local_ollama_timeout_contract.yaml`
- `runtime/runtime_surfaces/manifests/runtime_mcp.yaml`
- `runtime/runtime_surfaces/manifests/runtime_provider_governance.yaml`
- `runtime/runtime_surfaces/manifests/siteops_skill_runtime.yaml`

### Phase 2: Capability Registry and Risk Classification

Status: COMPLETE TARGETED / READ-ONLY.

Added normalized capability and risk vocabulary with fail-closed validation. This phase classifies manifest capabilities, applies risk approval floors, blocks credential/profile/destructive capabilities, requires conditional or explicit approval for provider fallback and external UI mutation, and requires explicit approval for external network calls and runtime/security policy changes.

Target files:

- `runtime/runtime_surfaces/risk.py`
- `runtime/runtime_surfaces/policy.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_risk.py`

Implemented policy helpers:

- `get_risk_class`
- `list_risk_classes`
- `highest_risk`
- `build_capability_policy_index`
- `capability_policy_records`
- `assert_registry_policy_safe`

### Phase 3: Provider/Runtime Routing Integration

Status: COMPLETE TARGETED / READ-ONLY PROPOSAL ROUTER.

Reference existing routers without replacing them:

- RPGL for provider fallback,
- Agent Bus for runtime task routing,
- AOR for task/workflow classification,
- operator surface registry for browser/filesystem/terminal/desktop adapters.

Target files:

- `runtime/runtime_surfaces/router.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_router.py`

Implemented behavior:

- `propose_route` returns a structured `RuntimeSurfaceRouteDecision`.
- Unknown capabilities deny closed with no fallback.
- Preferred-surface mismatches deny closed.
- Blocked policy records return `blocked`.
- Approval-gated capabilities return `approval_required`.
- Low-risk metadata routes return `proposed`.
- Every Phase 3 decision sets `execution_performed: false` and `ledger_written: false`.

### Phase 4: Browser Domain Skill Memory

Status: COMPLETE TARGETED / READ-ONLY NORMALIZATION.

Normalize Browser Runtime, Browser Skills, and SiteOps skill cards into ARSL manifests while preserving proposal-first promotion.

Initial manifests:

- `runtime/runtime_surfaces/manifests/browser_operator.yaml`
- `runtime/runtime_surfaces/manifests/browser_runtime_shadow.yaml`
- `runtime/runtime_surfaces/manifests/browser_skill_memory.yaml`
- `runtime/runtime_surfaces/manifests/siteops_skill_runtime.yaml`

Implemented helper:

- `runtime/runtime_surfaces/browser_skill_memory.py`

Implemented behavior:

- Normalizes untrusted browser skill candidates from `03_INPUTS/Browser-Skill-Candidates/`.
- Normalizes draft/trusted-browser-skill YAML records from `runtime/browser_skills/skills/`.
- Normalizes SiteOps skill cards and workflow manifests from `runtime/siteops/registry/`.
- Normalizes reviewed browser workflow cache entries from `runtime/browser_workflows/workflows/`.
- Preserves storage reconciliation from `runtime/browser_skills/candidates.py`.
- Forces ARSL inventory output to report no writes, no browser execution, no promotion, no activation, no credential access, no real browser profile access, and no raw content visibility.

### Phase 5: Audit Logs, Tests, and Docs

Status: COMPLETE TARGETED / APPEND-ONLY LEDGER SUPPORT.

Add routing ledger and docs.

Target files:

- `runtime/runtime_surfaces/audit.py`
- `runtime/runtime_surfaces/state/routing_decisions.jsonl`
- `06_AGENTS/Adaptive-Runtime-Surface-Layer.md`
- `06_AGENTS/Runtime-Surface-Manifest-Standard.md`

Implemented behavior:

- `append_route_decision` appends JSONL records from `propose_route` decisions.
- `read_route_decision_records` reads only route-decision records and ignores the initialization marker.
- Audit records preserve requested capability, candidate surfaces, selected surface, decision, authority layer, policy refs, risk, approval, Gate/audit flags, denial reasons, and the original decision payload.
- Audit append refuses decisions that report `execution_performed: true`.
- Audit append refuses decisions that already report `ledger_written: true`.
- Relative ledger paths containing `..` fail closed.
- Default ledger path is `runtime/runtime_surfaces/state/routing_decisions.jsonl`.

Protected docs `06_AGENTS/Adaptive-Runtime-Surface-Layer.md` and `06_AGENTS/Runtime-Surface-Manifest-Standard.md` were added in the 2026-05-04 canonical-docs pass. They preserve ARSL as PARTIAL and do not grant execution authority.

### Phase 6: Optional MCP Exposure

Status: COMPLETE TARGETED / CURATED READ-ONLY MCP SUMMARY.

Expose curated read-only ARSL summaries through Runtime MCP.

Implemented resources:

- `runtime.surfaces`
- `chaseos.runtime_surfaces_summary` JSON-RPC alias

Implemented behavior:

- Lists summarized runtime surfaces, surface families, owner layers, status, trust ceilings, and capability counts.
- Lists normalized capability policy records without exposing raw manifests.
- Includes browser skill memory counts only through the existing sanitized ARSL inventory summary.
- Includes recent routing-decision metadata only, not full decision payloads.
- Reports explicit no-execution/no-provider/no-browser/no-ledger-write exposure flags.
- Exposes no write/apply MCP tools.
- Does not execute `propose_route`.
- Does not append to the ARSL routing ledger.
- Does not call providers, browsers, Agent Bus, AOR, SiteOps activation, or external network surfaces.

Target files:

- `runtime/mcp/resources/runtime_surfaces.py`
- `runtime/mcp/resources/__init__.py`
- `runtime/mcp/safety.py`
- `runtime/mcp/server.py`
- `runtime/mcp/tests/test_runtime_mcp_runtime_surfaces.py`

### Phase 7: Canonical Framework Docs

Status: COMPLETE TARGETED / DOCS-ONLY CANONICALIZATION.

Promote ARSL from feature docs into protected framework-control documentation without granting new authority.

Implemented docs:

- `06_AGENTS/Adaptive-Runtime-Surface-Layer.md`
- `06_AGENTS/Runtime-Surface-Manifest-Standard.md`

Reference updates:

- `06_AGENTS/Agent-Control-Plane.md`
- `06_AGENTS/Vault-Map.md`
- `06_AGENTS/ChaseOS-Runtime-MCP.md`

Implemented behavior:

- Documents ARSL as canonical registry/classification/proposal/audit governance.
- Documents manifest schema requirements, allowed surface families/types, risk classes, trust ceilings, and safety policies.
- Preserves ARSL status as PARTIAL.
- Preserves Gate, Permission Matrix, Trust Tiers, Agent Control Plane, RPGL, AOR, Agent Bus, SiteOps, and Runtime MCP authority.
- Adds no runtime code, no execution path, no MCP tools, no browser control, no provider calls, and no credential/profile access.

### Phase 8: Read-Only CLI Inspection

Status: COMPLETE TARGETED / READ-ONLY CLI INSPECTION.

Expose curated ARSL summaries through the canonical operator CLI without granting execution authority.

Implemented commands:

- `chaseos runtime surfaces summary`
- `chaseos runtime surfaces capabilities`
- `chaseos runtime surfaces route-review`

Target files:

- `runtime/runtime_surfaces/inspection.py`
- `runtime/runtime_surfaces/review_contract.py`
- `runtime/runtime_surfaces/__init__.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md`
- `runtime/CLI-README.md`
- `runtime/runtime_surfaces/tests/test_runtime_surface_cli_inspection.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_route_review.py`

Implemented behavior:

- Summarizes validated runtime surface registry metadata.
- Summarizes capability policy records and supports `--surface SURFACE_ID` filtering.
- Builds a read-only route-review contract for operator review with optional `--capability` and `--surface` filters.
- Fails closed for unknown surfaces.
- Reports explicit safety flags for no execution, no route proposal, no provider calls, no browser control, no raw manifest exposure, no MCP tool exposure, and no ledger write.
- Summary and capability inspection do not call `propose_route`.
- Route-review previews route posture but does not commit a route proposal or append the routing ledger.
- Does not append to the ARSL routing ledger.
- Does not call providers, browsers, Agent Bus, AOR, SiteOps activation, or external network surfaces.

### Phase 9: Agent Runtime Manifest Expansion

Status: COMPLETE TARGETED / MANIFEST-ONLY REGISTRY EXPANSION.

Register repo-existing Hermes and OpenClaw Agent Bus runtime lanes in ARSL without adding execution authority.

Implemented manifests:

- `runtime/runtime_surfaces/manifests/agent_bus_hermes.yaml`
- `runtime/runtime_surfaces/manifests/agent_bus_openclaw.yaml`

Registered surface IDs:

- `agent.hermes.bus`
- `agent.openclaw.bus`

Repo-truth anchors:

- `runtime/hermes/capabilities.yaml`
- `runtime/openclaw/capabilities.yaml`
- `runtime/hermes/coordination_bridge.md`
- `runtime/openclaw/coordination_bridge.md`
- `runtime/lifecycle/hermes.lifecycle.yaml`
- `runtime/lifecycle/openclaw.lifecycle.yaml`
- `runtime/workflows/hermes_watch.py`
- `runtime/workflows/openclaw_watch.py`
- `06_AGENTS/Hermes-Runtime-Profile.md`
- `06_AGENTS/OpenClaw-Runtime-Profile.md`

Implemented behavior:

- Adds validated manifest metadata only.
- Keeps `routing_policy.default: deny_unknown`.
- Keeps `credential_policy.credentials_allowed: false`.
- Keeps `credential_policy.cookies_allowed: false`.
- Keeps `credential_policy.real_profile_allowed: false`.
- Keeps `fallback_policy.sticky_fallback_allowed: false`.
- Keeps `mcp_exposure_policy.expose_raw_manifest: false`.
- Preserves Agent Bus as the authority layer for these runtime lanes.
- Adds no Agent Bus enqueueing, watch-loop activation, AOR dispatch, provider call, browser action, or canonical writeback.

### Phase 10: Archon Agent Runtime Manifest Expansion

Status: COMPLETE TARGETED / MANIFEST-ONLY REGISTRY EXPANSION.

Register repo-existing Archon Agent Bus runtime lane in ARSL without making Archon always-on or adding execution authority.

Implemented manifest:

- `runtime/runtime_surfaces/manifests/agent_bus_archon.yaml`

Registered surface ID:

- `agent.archon.bus`

Repo-truth anchors:

- `runtime/archon/capabilities.yaml`
- `runtime/lifecycle/archon.lifecycle.yaml`
- `runtime/workflows/archon_watch.py`
- `runtime/workflows/registry/archon_watch.yaml`
- `06_AGENTS/Archon-Runtime-Profile.md`
- `06_AGENTS/role-cards/archon-engineering.yaml`

Implemented behavior:

- Adds validated manifest metadata only.
- Preserves Archon as session-scoped and reachable only when Claude Code / `archon_watch` is running.
- Keeps `routing_policy.default: deny_unknown`.
- Keeps `credential_policy.credentials_allowed: false`.
- Keeps `credential_policy.cookies_allowed: false`.
- Keeps `credential_policy.real_profile_allowed: false`.
- Keeps `fallback_policy.sticky_fallback_allowed: false`.
- Keeps `mcp_exposure_policy.expose_raw_manifest: false`.
- Preserves Agent Bus as the authority layer for this runtime lane.
- Adds no Agent Bus enqueueing, watch-loop activation, shell execution, AOR dispatch, provider call, browser action, or canonical writeback.

### Phase 11: Provider-Specific Manifest Expansion

Status: COMPLETE TARGETED / MANIFEST-ONLY REGISTRY EXPANSION.

Register bounded provider-specific surfaces that already exist in repo truth without enabling live provider execution.

Implemented manifests:

- `runtime/runtime_surfaces/manifests/provider_openai_responses_mcp_dry_run.yaml`
- `runtime/runtime_surfaces/manifests/provider_local_ollama_timeout_contract.yaml`

Registered surface IDs:

- `provider.openai.responses_mcp_dry_run`
- `provider.local_ollama.timeout_contract`

Repo-truth anchors:

- `runtime/adapters/openai/responses_mcp_payload.py`
- `runtime/workflows/openai_shadow.py`
- `runtime/workflows/registry/openai_operator_research_shadow.yaml`
- `runtime/policy/adapters/openai_config.yaml`
- `06_AGENTS/OpenAI-Adapter-Spec.md`
- `06_AGENTS/role-cards/openai-operator-shadow.yaml`
- `runtime/providers/governance_layer.py`
- `runtime/providers/provider_call_surfaces.json`
- `06_AGENTS/Runtime-Provider-Governance-Layer.md`

Implemented behavior:

- Adds validated manifest metadata only.
- Preserves OpenAI as dry-run/shadow-proof only; no live OpenAI API call or remote MCP call is enabled.
- Preserves local Ollama timeout contract as RPGL-governed fallback/diagnostic evidence; no live Ollama endpoint call is enabled by ARSL.
- Keeps `routing_policy.default: deny_unknown`.
- Keeps `credential_policy.credentials_allowed: false`.
- Keeps `credential_policy.cookies_allowed: false`.
- Keeps `credential_policy.real_profile_allowed: false`.
- Keeps `fallback_policy.sticky_fallback_allowed: false`.
- Keeps `mcp_exposure_policy.expose_raw_manifest: false`.
- Adds no provider call, provider switching, sticky fallback, live network probe, credential read, MCP tool, or canonical writeback.

### Phase 12: Client/Embedded Manifest Audit

Status: COMPLETE TARGETED / MANIFEST-ONLY REGISTRY EXPANSION.

Repo truth found one safe client/embedded insertion point:

- `client.studio.sandboxed_static_mount`

This manifest registers the Studio desktop shell's local-only, read-only static artifact mount layer as a client/embedded runtime surface.

Repo-truth anchors:

- `runtime/studio/desktop_shell_app.py`
- `runtime/studio/graph_view_shell_panel.py`
- `runtime/studio/pulse_product_shell_panel.py`
- `runtime/studio/approval_queue_panel.py`
- `runtime/studio/test_desktop_shell_app.py`
- `06_AGENTS/ChaseOS-Studio-Architecture.md`
- `06_AGENTS/ChaseOS-Studio-Graph-View-Shell-Panel-Mount.md`
- `06_AGENTS/ChaseOS-Pulse-Studio-Product-Shell-Mount.md`
- `06_AGENTS/ChaseOS-Studio-Node-Inspector-Shell-Panel-Mount.md`

Implemented behavior:

- Adds validated manifest metadata only.
- Registers local-only read-only iframe/webview-style static artifact mounting.
- Preserves loopback-only serving evidence from Studio shell tests.
- Preserves empty iframe sandbox usage and no script-bearing shell HTML.
- Keeps `routing_policy.default: deny_unknown`.
- Keeps `credential_policy.credentials_allowed: false`.
- Keeps `credential_policy.cookies_allowed: false`.
- Keeps `credential_policy.real_profile_allowed: false`.
- Keeps `fallback_policy.sticky_fallback_allowed: false`.
- Keeps `mcp_exposure_policy.expose_raw_manifest: false`.
- Adds no WebAssembly inference, WebGPU/local model execution, browser-hosted agent environment, WebContainer-style code execution, browser/CDP/Playwright action, provider call, connector call, Agent Bus write, approval execution, candidate apply, schedule activation, or canonical writeback.

### Phase 13: Routing UI Review Contract

Status: COMPLETE TARGETED / READ-ONLY ROUTE REVIEW CONTRACT.

Implemented files:

- `runtime/runtime_surfaces/review_contract.py`
- `runtime/runtime_surfaces/tests/test_runtime_surface_route_review.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md`
- `runtime/CLI-README.md`

Implemented command:

- `chaseos runtime surfaces route-review --capability CAPABILITY_ID --surface SURFACE_ID --json`

Implemented behavior:

- Builds a sanitized route-review contract for operator-facing inspection.
- Supports all-capability review rows when no capability filter is supplied.
- Supports route posture preview for a requested capability.
- Preserves unknown-surface and unknown-capability fail-closed behavior.
- Reports selected authority layer, risk class, approval requirement, Gate requirement, audit requirement, denial reasons, and policy references when a capability is reviewed.
- Sets `execution_performed: false`, `runtime_dispatch_performed: false`, `route_proposal_committed: false`, `ledger_written: false`, `approval_granted: false`, `gate_mutated: false`, `provider_calls_performed: false`, and `browser_control_performed: false`.
- Adds no runtime dispatch, browser/CDP/Playwright action, provider call, Agent Bus write, AOR dispatch, approval grant, Gate mutation, routing-ledger append, raw manifest exposure, MCP tool, or canonical writeback.

### Phase 14: Studio Route Review Panel Contract

Status: COMPLETE TARGETED / READ-ONLY STUDIO PANEL CONTRACT AND SHELL MOUNT.

Implemented files:

- `runtime/studio/arsl_route_review_panel.py`
- `runtime/studio/test_arsl_route_review_panel.py`
- `runtime/studio/desktop_shell_app.py`
- `runtime/studio/test_desktop_shell_app.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md`

Implemented command:

- `chaseos studio arsl-route-review-panel --capability CAPABILITY_ID --surface SURFACE_ID --json`

Implemented Studio exposure:

- desktop shell route: `#arsl-route-review`
- JSON route: `/arsl-route-review.json`
- source contract: `runtime.runtime_surfaces.review_contract.build_route_review_contract`
- default review capability for shell visibility: `browser.click`

Implemented behavior:

- Wraps the existing ARSL route-review backend as a Studio panel contract.
- Mounts the panel inside the local read-only desktop shell mock.
- Reports review rows, selected surface, authority layer, preview decision, approval requirement, Gate requirement, audit requirement, and policy/risk counts.
- Preserves route review as preview-only.
- Reports `executes_routes: false`, `commits_route_proposals: false`, `writes_routing_ledger: false`, `grants_approvals: false`, `mutates_gate_policy: false`, `dispatches_runtimes: false`, `provider_calls_allowed: false`, `browser_control_allowed: false`, `raw_manifest_exposed: false`, and `mcp_tools_exposed: false`.
- Adds no route execution, approval grant, Gate mutation, Agent Bus write, provider call, browser/CDP/Playwright action, MCP tool, raw manifest exposure, routing-ledger append, credential/profile access, or canonical writeback.

Closeout posture:

- ARSL now has schema, registry, manifests, risk classification, route review, curated MCP summary, CLI inspection, and read-only Studio route-review exposure.
- Remaining work is optional hardening or future-authority work, not required for the current ARSL foundation closeout.

### Phase 15: Studio Route Review Browser QA

Status: COMPLETE TARGETED / VISUAL BROWSER QA VERIFIED.

Evidence files:

- `07_LOGS/Studio-ARSL-Route-Review/2026-05-04-arsl-route-review-browser-qa.md`
- `07_LOGS/Studio-ARSL-Route-Review/2026-05-04-arsl-route-review-browser-qa.json`
- `07_LOGS/Studio-ARSL-Route-Review/2026-05-04-arsl-route-review-browser-qa-desktop.png`
- `07_LOGS/Studio-ARSL-Route-Review/2026-05-04-arsl-route-review-browser-qa-mobile.png`

Implemented polish:

- ARSL visible status badge is compact: `READ-ONLY STUDIO MOUNT`.
- Full detailed status remains available in the JSON contract.
- ARSL route-review table uses a horizontal scroll wrapper on narrow/mobile viewports.

Verified behavior:

- Desktop ARSL panel visible.
- Mobile ARSL panel visible.
- Studio nav entry visible.
- Route-review content visible: `browser.click`, `approval_required`, `browser.operator.playwright`.
- Boundary text visible.
- Zero ARSL-relevant console errors.
- Zero shell script tags.
- Known unrelated shared-shell Playwright warnings for existing Pulse/Approval Queue `file://` iframes were recorded separately and do not affect ARSL.
- No route execution, route proposal commit, routing-ledger write, approval grant, Gate mutation, provider call, browser-control authority, credential/profile access, or canonical mutation occurred.

Closeout posture:

- ARSL foundation, CLI, MCP summary, Studio panel, and visual QA are complete targeted.
- Future work should be treated as new scope: additional manifests, MCP expansion, or approval-gated execution authority.

## Non-Goals

- No ambient browser control.
- No unrestricted vault access.
- No direct credential handling.
- No automatic model fallback for serious work.
- No trusted browser skill activation from candidates.
- No Gate, Permission Matrix, Trust Tiers, or Agent Control Plane weakening.
- No broad MCP policy export.
- No WebGPU/WebAssembly execution in the current ARSL manifest set.
- No WebContainer-style code execution in the current ARSL manifest set.

## Acceptance Criteria

- Unknown surface type fails closed.
- Unknown capability fails closed.
- Missing trust ceiling fails closed.
- Missing permission references fail closed.
- Credential/browser profile capabilities are denied by default.
- Browser skills are untrusted until reviewed.
- Provider fallback still goes through RPGL.
- Runtime selection still goes through Agent Bus/AOR where applicable.
- Routing decisions are auditable.
