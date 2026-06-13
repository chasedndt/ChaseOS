---
type: framework-control
title: Adaptive Runtime Surface Layer - ChaseOS
status: PARTIAL
created: 2026-05-04
updated: 2026-05-04
scope: runtime-governance
---

# Adaptive Runtime Surface Layer

> The Adaptive Runtime Surface Layer (ARSL) is the ChaseOS registry and governance layer for execution surfaces. It classifies what a runtime can do, which authority layer owns execution, which risk class applies, and what audit trail is required. ARSL does not execute work directly.

---

## 1. Current Repo Truth

Status: PARTIAL.

Implemented targeted as of 2026-05-04:

- runtime surface manifest schema;
- validated manifest model and registry loader;
- first-party runtime surface manifests;
- Chaser Agent Bus runtime manifest;
- Hermes and OpenClaw Agent Bus runtime manifests;
- OpenAI dry-run provider adapter manifest;
- local Ollama timeout-contract manifest;
- Studio sandboxed static artifact client/embedded manifest;
- normalized risk taxonomy and capability policy records;
- read-only route proposal helper;
- read-only browser skill memory normalization;
- append-only route decision ledger helpers;
- curated read-only Runtime MCP summary exposure;
- read-only CLI inspection for registry and capability-policy summaries.
- read-only CLI route-review contract for operator review of route posture.
- read-only Studio ARSL Route Review panel contract and desktop shell mount.
- targeted browser QA evidence for the Studio ARSL Route Review panel.

Not built:

- live route execution;
- automatic Agent Bus enqueueing;
- AOR dispatch from ARSL;
- provider calls from ARSL;
- browser/CDP/Playwright control from ARSL;
- trusted browser skill activation from ARSL;
- MCP write/apply tools for ARSL;
- WebGPU/WebAssembly/local model execution;
- WebContainer-style browser-hosted code execution.

## 2. Canonical Role

ARSL is the canonical registry for runtime surface metadata and capability classification.

It answers:

- which runtime surfaces are known;
- what each surface claims it can do;
- which risk class each capability carries;
- which authority layer owns actual execution;
- whether approval, Gate checks, audit, or denial applies;
- whether a route proposal is safe to present.

ARSL does not replace existing execution authorities.

## 3. Authority Boundaries

| Authority | Owner | ARSL relationship |
| --- | --- | --- |
| Provider/model fallback | `runtime/providers/` | ARSL classifies and references provider fallback; RPGL remains authority. |
| Runtime task routing | `runtime/agent_bus/` | ARSL can describe/route-propose; Agent Bus remains task substrate. |
| Workflow execution | `runtime/aor/` | ARSL can classify; AOR remains executor. |
| Browser actions | `runtime/operator_surface/`, `runtime/browser_runtime/`, `runtime/siteops/` | ARSL can inventory and classify; browser runtimes and SiteOps remain executors/review authorities. |
| Runtime MCP | `runtime/mcp/` | ARSL exposes curated summaries only; MCP does not receive ARSL write/apply tools. |
| Gate and permission policy | `runtime/chaseos_gate.py`, `06_AGENTS/Permission-Matrix.md`, `06_AGENTS/Trust-Tiers.md`, `06_AGENTS/Agent-Control-Plane.md` | ARSL must never weaken or bypass these. |

## 4. Implemented Runtime Files

- `runtime/runtime_surfaces/schemas/runtime_surface_manifest.schema.json`
- `runtime/runtime_surfaces/models.py`
- `runtime/runtime_surfaces/registry.py`
- `runtime/runtime_surfaces/risk.py`
- `runtime/runtime_surfaces/policy.py`
- `runtime/runtime_surfaces/router.py`
- `runtime/runtime_surfaces/review_contract.py`
- `runtime/runtime_surfaces/browser_skill_memory.py`
- `runtime/runtime_surfaces/audit.py`
- `runtime/runtime_surfaces/inspection.py`
- `runtime/runtime_surfaces/state/routing_decisions.jsonl`
- `runtime/runtime_surfaces/manifests/*.yaml`
- `runtime/mcp/resources/runtime_surfaces.py`
- `runtime/studio/arsl_route_review_panel.py`
- `07_LOGS/Studio-ARSL-Route-Review/2026-05-04-arsl-route-review-browser-qa.md`

Current named Agent Bus runtime manifests:

- `agent.chaser_agent.bus`
- `agent.codex.bus`
- `agent.hermes.bus`
- `agent.openclaw.bus`

Current named provider-specific manifests:

- `provider.openai.responses_mcp_dry_run`
- `provider.local_ollama.timeout_contract`

Current named client/embedded manifests:

- `client.studio.sandboxed_static_mount`

## 5. Current CLI Exposure

The canonical CLI exposes ARSL only as curated read-only summaries:

- `chaseos runtime surfaces summary`
- `chaseos runtime surfaces capabilities`
- `chaseos runtime surfaces route-review`

The CLI exposure must report:

- `execution_performed: false`;
- `route_proposal_performed: false` for summary/capability inspection;
- `route_proposal_committed: false` for route-review previews;
- `ledger_written: false`;
- `provider_calls_performed: false`;
- `browser_control_performed: false`;
- `raw_manifest_exposed: false`;
- no credential, cookie, session, or browser profile visibility.

No ARSL CLI command may execute, approve, promote browser skills, or write the routing ledger without a separate approval-gated design pass. `route-review` may preview route posture for operator review only; it must not commit a route proposal, write the ledger, or invoke the selected authority layer.

## 6. Current MCP Exposure

Runtime MCP exposes ARSL only as curated read-only summaries:

- legacy resource: `runtime.surfaces`;
- JSON-RPC alias: `chaseos.runtime_surfaces_summary`.

The MCP exposure must report:

- `raw_manifest_exposed: false`;
- `execution_performed: false`;
- `ledger_written: false`;
- `provider_calls_performed: false`;
- `browser_control_performed: false`;
- no credential, cookie, session, or browser profile visibility.

No ARSL MCP tool may be added without a separate approval-gated design pass.

## 6A. Current Studio Exposure

Studio exposes ARSL only as a read-only route-review panel:

- `chaseos studio arsl-route-review-panel`
- `chaseos studio desktop-shell-app --dry-run --json`
- desktop route: `#arsl-route-review`
- JSON route: `/arsl-route-review.json`

The Studio panel wraps `runtime.runtime_surfaces.review_contract.build_route_review_contract` and reports route posture, selected authority layer, risk class, approval requirement, Gate requirement, audit requirement, and review rows. It must report:

- `executes_routes: false`;
- `commits_route_proposals: false`;
- `writes_routing_ledger: false`;
- `grants_approvals: false`;
- `mutates_gate_policy: false`;
- `dispatches_runtimes: false`;
- `provider_calls_allowed: false`;
- `browser_control_allowed: false`;
- `mcp_tools_exposed: false`;
- `raw_manifest_exposed: false`;
- no credential, cookie, session, or browser profile visibility.

No Studio ARSL panel may execute a route, grant an approval, write the routing ledger, call a provider, control a browser, expose raw manifests, or mutate canonical ChaseOS state without a separate approval-gated design and test pass.

Targeted browser QA evidence:

- `07_LOGS/Studio-ARSL-Route-Review/2026-05-04-arsl-route-review-browser-qa.md`
- `07_LOGS/Studio-ARSL-Route-Review/2026-05-04-arsl-route-review-browser-qa.json`
- `07_LOGS/Studio-ARSL-Route-Review/2026-05-04-arsl-route-review-browser-qa-desktop.png`
- `07_LOGS/Studio-ARSL-Route-Review/2026-05-04-arsl-route-review-browser-qa-mobile.png`

The QA verified desktop and mobile visibility, compact status badge rendering, route-review content, zero ARSL-relevant console errors, zero script tags in the shell, and no route execution, ledger write, approval grant, Gate mutation, provider call, browser-control authority, or canonical mutation.

## 7. Routing Rules

ARSL route proposals are advisory metadata until another authority acts.

Required behavior:

- unknown capability: deny closed;
- unknown surface: deny closed;
- preferred surface mismatch: deny closed;
- blocked risk class: blocked;
- approval-gated risk class: approval required;
- low-risk read metadata: proposed only;
- route-review output: preview only;
- route proposal must set `execution_performed: false`;
- route proposal must set `ledger_written: false` before audit append.

## 8. Browser Skill Memory Rules

Browser-learned domain skills are proposal-first.

ARSL may inventory:

- Browser Skill candidates;
- Browser Skill YAML records;
- SiteOps skill cards;
- SiteOps workflow manifests;
- browser workflow cache records.

ARSL must not:

- activate a browser skill;
- promote a candidate into trusted automation;
- run Playwright/CDP/browser actions;
- read credentials, cookies, sessions, or real browser profiles;
- expose raw browser skill content through MCP;
- bypass SiteOps approvals or protected write guards.

## 9. Risk and Permission Constraints

ARSL must preserve:

- Trust Tiers as authority ceilings;
- Permission Matrix rules as action boundaries;
- Agent Control Plane separation of provider, execution surface, and permission scope;
- Gate policy for protected operations;
- no silent fallback to weaker models for serious work;
- no ambient browser control;
- no unrestricted vault access;
- no unrestricted MCP exposure.

## 10. Manifest Standard

Runtime surface manifests are governed by `06_AGENTS/Runtime-Surface-Manifest-Standard.md`.

Manifests live under:

- `runtime/runtime_surfaces/manifests/`

All manifests must validate before ARSL can treat a surface as registered.

## 11. Future Work

Future ARSL work may add:

- richer MCP resource summaries;
- additional client/embedded runtime manifests;
- explicit integration tests for new execution authorities.

Future ARSL work must not add execution authority without a separate design, permission, Gate, audit, and test pass.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
