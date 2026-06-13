---
date: 2026-05-21
runtime: Codex
type: feature-node
status: PARTIAL / LOCAL PACK LANES VERIFIED / EXTERNAL EXECUTION BLOCKED
parent_families:
  - ChaseOS VentureOps
  - Workspace Mode Layer
  - Autonomous Operator Runtime
studio_surface: Missions / Workflow Packs
---

# Product Workflow Packs Feature

Product Workflow Packs are packaged ChaseOS workflows that turn governed runtime, source, approval, proof, and Studio surfaces into repeatable product-facing missions.

## Current Packs

- Visual Product & Creative Studio
- Founder / Personal Automation Audit
- Research-to-Product Intelligence Engine
- Safe Agent Runtime Governance Kit

## Current Verified Local Capabilities

- Workflow manifests and pack registry.
- Local run records.
- Source/provenance artifacts.
- Proof cards and scorecards.
- Approval gates.
- Studio Workflow Packs panel.
- Automation Audit MVP.
- Creative Studio MVP.
- Research-to-Product Intelligence MVP with manual source intake, evidence/claim packet, scorecard, decision matrix, implementation/content briefs, R&D-style JSON export, proof card, and Studio API/UI.
- Agent Governance Kit MVP.
- Approval resume contract.
- Approval review artifact writer.
- Approval consumption dry-run.
- Exact-once marker reservation.
- Approved local resume executor.
- Local resume / approval resume UI chain.
- Packaged Studio clickthrough evidence.
- Missions product UI operating context, readiness, feature-family coverage, mission pack cards, and right-inspector selection source-render verified on 2026-05-24.

## Current Blockers

- External source fetching, scraping, GitHub API, repo cloning.
- Provider calls.
- Browser automation.
- Runtime execution and Agent Bus dispatch from packs.
- Graph/canonical/R&D workbook mutation.
- External delivery, CRM, payment, invoice, marketplace publication, or live client/revenue mutation.

## Reconciled Capability Rows

| Capability | Evidence status | Evidence |
|---|---:|---|
| Product Workflow Packs foundation | PARTIAL / VERIFIED LOCAL | `runtime/workflow_packs/registry.py`, run store, artifact store, panel, Phase 1 log. |
| Automation Audit | PARTIAL / VERIFIED LOCAL | `runtime/workflow_packs/automation_audit.py`, 2026-05-20 MVP log. |
| Creative Studio | PARTIAL / VERIFIED LOCAL | `runtime/workflow_packs/creative_studio.py`, 2026-05-20 MVP log. |
| Research Intelligence | PARTIAL / VERIFIED LOCAL | `runtime/workflow_packs/research_intelligence.py`, 2026-05-20 MVP log. |
| Agent Governance Kit | PARTIAL / VERIFIED LOCAL | `runtime/workflow_packs/agent_governance.py`, Studio registry readiness, 2026-05-20 MVP log. |
| Approval review/resume/dry-run/marker chain | PARTIAL / VERIFIED LOCAL | Approval review, consumption dry-run, marker reservation, and resume-contract logs. |
| Approved local resume executor | PARTIAL / VERIFIED LOCAL | 2026-05-21 100-percent local approval resume and UI wiring logs. |
| Missions / Workflow Packs Studio product UI | PARTIAL PRODUCT UI / SOURCE UI VERIFIED | `runtime/workflow_packs/panel.py`, Studio shell frontend, `runtime/studio/final_productization_visual_qa.py`, 2026-05-24 Missions visual QA. |

## Canonical Sources

- `docs/features/chaseos_product_facing_workflow_packs_spec.md.md`
- `runtime/workflow_packs/`
- `07_LOGS/Build-Logs/2026-05-20-ChaseOS-product-workflow-packs-research-intelligence-mvp.md`
- `07_LOGS/Build-Logs/2026-05-20-ChaseOS-product-workflow-packs-agent-governance-kit-mvp.md`
- `07_LOGS/Build-Logs/2026-05-21-ChaseOS-product-workflow-packs-100-percent-local-approval-resume.md`
- `07_LOGS/Build-Logs/2026-05-21-ChaseOS-product-workflow-packs-local-resume-ui-wiring.md`
- `07_LOGS/Build-Logs/2026-05-24-ChaseOS-studio-ui-missions-workflow-packs-product-polish.md`
- `docs/audits/2026-05-21_feature_family_deep_reconciliation.md`

## Graph Links

[[VentureOps-Architecture]] [[Workflow-Pack-Standard]] [[Workspace-Mode-Layer-Feature-Family]] [[ChaseOS-Feature-Family-and-Subfeature-Inventory]]
