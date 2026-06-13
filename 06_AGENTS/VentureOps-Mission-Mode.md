---
type: framework-architecture
title: VentureOps Mission Mode
status: PARTIAL / LOCAL MISSION ACTIVE + FINAL HARDENING VERIFIED + STUDIO USECASE GUIDE / NO EXTERNAL AUTONOMY
created: 2026-05-13
updated: 2026-05-15
runtime: Codex
---

# VentureOps Mission Mode

> VentureOps Mission Mode lets a user define a long-term objective, bind it to workflow packs, assign sub-agent responsibilities, track progress across repeated passes, learn from proof artifacts and scorecards, and safely evolve workflow logic through evidence-backed proposals and approval-gated versioning.

## Layer Placement

Mission Mode sits above and composes existing ChaseOS layers:

- AOR for governed workflow execution and task state.
- Gate for protected actions, approvals, and policy enforcement.
- Agent Bus for structured coordination and sub-agent task packets.
- SIC/Capture/graph/markdown scanning for local-first evidence.
- MCP for controlled resources/tools/prompts.
- BOSL for browser/site learning as candidate skills only.
- RPGL/provider governance for model strength and fallback boundaries.
- Studio for future human-facing mission review and approvals.
- Workflow registry, role cards, proof artifacts, scorecards, and audit logs for traceability.

Mission Mode does not replace any of those systems and does not create a parallel automation engine.

## Runtime Model

The safe loop is:

1. Observe evidence.
2. Score the run.
3. Propose a change.
4. Request approval.
5. Apply only through a versioned workflow update after approval.
6. Continue the mission.

Forbidden model: an agent silently mutates its own workflow logic or starts acting differently without approval.

## Current Implementation

Implemented in this pass:

- Architecture and standards for mission manifests, sub-agent orchestration, mission state ledgers, mission reviews, workflow evolution proposals, domain goal profiles, mission recommendations, and site-profile/browser learning.
- Templates under `05_TEMPLATES/`.
- Machine-readable schema contracts under `runtime/ventureops/templates/`.
- Deterministic runtime helpers under `runtime/ventureops/`.
- Example mission manifests under `runtime/ventureops/examples/mission_manifests/`.
- First local dry-run workspace under `07_LOGS/VentureOps-Missions/2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run/`, with mission manifest, domain profile, sub-agent plan, mission state ledger, review, proposal-only workflow evolution artifact, site-profile candidate, proof card, scorecard, and boundary flags.
- Dry-run workspace validator `runtime.ventureops.mission_dry_runs.validate_mission_dry_run_workspace`.
- Activation/AOR readiness helper `runtime.ventureops.mission_activation_readiness.build_mission_activation_readiness`.
- CLI command `chaseos ventureops mission-activation-readiness --mission-workspace PATH --json`, with optional create-only report writeback.
- Activation approval packet helper `runtime.ventureops.mission_activation_approval_packet.build_mission_activation_approval_packet`.
- CLI command `chaseos ventureops mission-activation-approval-packet --mission-workspace PATH --json`, with optional create-only draft packet writeback.
- Draft activation packet artifact `07_LOGS/VentureOps-Missions/2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run/activation-approval-packet-draft.json`.
- Exact-once activation approval helper `runtime.ventureops.mission_activation_approval_consumption.consume_mission_activation_approval`.
- CLI command `chaseos ventureops mission-activation-approval-consume --mission-workspace PATH --write-approval --consume --json`.
- Consumed activation approval artifacts `activation-approval-approved.json` and `activation-approval-consumption.json`.
- Exact-once manifest-promotion/workflow-evolution review helper `runtime.ventureops.mission_manifest_promotion_review_gate.consume_mission_manifest_promotion_review_gate`.
- CLI command `chaseos ventureops mission-manifest-promotion-review-gate --mission-workspace PATH --write-review --consume --json`.
- Consumed manifest-promotion/workflow-evolution review artifacts `mission-manifest-promotion-workflow-evolution-review-approved.json` and `mission-manifest-promotion-workflow-evolution-review-consumption.json`.
- Exact-once Agent Bus enqueue helper `runtime.ventureops.mission_agent_bus_enqueue_gate.consume_mission_agent_bus_enqueue_gate`.
- CLI command `chaseos ventureops mission-agent-bus-enqueue-gate --mission-workspace PATH --write-approval --consume --enqueue-task --json`.
- Consumed Agent Bus enqueue artifacts `mission-agent-bus-enqueue-approval-approved.json` and `mission-agent-bus-enqueue-consumption.json`.
- One local Agent Bus mission dry-review task addressed to Codex: `mission-dry-review-mission-chase-ai-runtime-governance-kit-2026-05-14-ventureops-mission-agent-bus-enqueue`.
- Exact-once runtime claim/result gate `runtime.ventureops.mission_runtime_claim_result_gate.consume_mission_runtime_claim_result_gate`.
- CLI command `chaseos ventureops mission-runtime-claim-result-gate --mission-workspace PATH --write-approval --consume --claim-task --dispatch-aor --ingest-result --close-task --json`.
- Consumed runtime claim/result artifacts `mission-runtime-claim-result-approval-approved.json`, `mission-runtime-claim-result-consumption.json`, and `mission-runtime-result.json`.
- Local AOR dry-review dispatch from the claimed Agent Bus task through `mission_chase_ai_runtime_governance_kit`, with no external effects.
- Result ingestion into the mission workspace, including state ledger, review, proof/audit index, artifact index, boundary, and workspace README updates.
- Agent Bus mission task closeout to `done`.
- Exact-once local mission activation gate `runtime.ventureops.mission_activation_gate.consume_mission_activation_gate`.
- CLI command `chaseos ventureops mission-activation-gate --mission-workspace PATH --write-approval --consume --activate --json`.
- Consumed activation artifacts `mission-activation-execution-approved.json` and `mission-activation-execution-consumption.json`.
- Local mission active state in `mission-manifest.json`, `mission-state-ledger.json`, `mission-review.json`, `run-boundary.json`, `artifact-index.json`, and workspace README evidence.
- Final hardening for local Mission Mode gates: claim/result state now fails closed if the consumed marker's Agent Bus task is missing, reopened, or no longer owned by the runtime; activation approvals are bound to the requested workspace path; runtime outputs and workspace indexes include explicit credential/secret-read false flags; and schema templates cover the runtime claim/result and local activation gates.
- Fail-closed external/client evidence gate `runtime.ventureops.mission_external_client_evidence_gate.build_mission_external_client_evidence_gate`.
- CLI command `chaseos ventureops mission-external-client-evidence-gate --mission-workspace PATH --json`, with optional create-only report writeback.
- Schema template `runtime/ventureops/templates/mission_external_client_evidence_gate_schema.yaml`.
- Focused validators and tests.

Not implemented:

- External/live mission execution beyond local active state and local dry-review.
- Autonomous repeated mission loop execution.
- Studio Mission Mode UI.
- Browser skill activation.
- External sends, payments, purchases, listings, provider calls, protected-file edits, or live trading.

The dry-run workspace has now advanced to local active mission state through exact-once gates and final local hardening. It claims and closes the local Codex Agent Bus dry-review task, dispatches only the existing local AOR dry-review handler, ingests local result evidence, rejects closed-task drift, binds activation approvals to the requested workspace, and does not call providers, launch browsers, send externally, mutate CRM/payment systems, read credentials, or authorize external effects.

The activation readiness command currently reports `mission_active_local`: the dry-run artifacts validate, activation approval, manifest-promotion/workflow-evolution review, Agent Bus enqueue, runtime claim/result, and local activation gates have all been consumed exactly once; the Agent Bus task is closed; the AOR dry-review result has been ingested; and the mission manifest/state ledger now record local active state. The next command routes to `mission-external-client-evidence-gate`, not another local activation or hardening pass. `workflow-evolution-proposal.json` remains `pending_review`/unapplied, and readiness is read-only unless `--write-report` is explicitly supplied.

The external/client evidence gate currently fails closed when no new evidence is supplied. It requires local mission active state, an explicit `external_action_type`, an operator approval statement, and typed evidence artifacts whose paths stay inside the vault root. It can only recommend the next guarded proof/review command for `live-client-workflow-proof`, `operator-attested-delivery-proof`, or `live-revenue-proof`; it does not execute live workflows, send externally, call providers or browsers, mutate CRM/payment systems, read credentials, apply workflow evolution, trade, edit protected files, or promote canonical state.

The 2026-05-14 mega pass consumed the prepared local scope/live-client evidence and wrote durable readiness/blocker reports under `07_LOGS/Workflow-Proofs/2026-05-14_ventureops-mega-pass-*`. It confirms valid local scope evidence, a valid local live-client workflow proof, and a valid client-safe delivery artifact, but still blocks operator-attested delivery proof, redacted receipt/payment evidence, proof-only live revenue, and final evidence bundle completion until real operator evidence exists.

The 2026-05-15 governed completion pass attempted the delivery proof, revenue evidence/proof, and final evidence bundle chain in one pass using the available repo-local evidence. It wrote blocked readiness/audit reports under `07_LOGS/Workflow-Proofs/2026-05-15_ventureops-governed-completion-*`, but it did not write delivery proof, revenue packet, proof-only live revenue, or final bundle artifacts because factual operator delivery attestation and redacted receipt/payment evidence were not supplied.

The 2026-05-15 real-operator evidence ingestion pass prepared a template/readiness-only handoff under `07_LOGS/Workflow-Proofs/2026-05-15_ventureops-real-operator-evidence-ingestion-*`. It wrote a revenue evidence template plus discovery/intake/readiness reports, but still did not create delivery, revenue, live-revenue, or final-bundle proof artifacts. The required next input remains redacted, factual operator delivery and payment/receipt evidence.

The 2026-05-15 autonomous implementation completion pass added `runtime.ventureops.autonomous_implementation_completion` and CLI `chaseos ventureops autonomous-implementation-completion`. Live report `07_LOGS/Workflow-Proofs/2026-05-15_ventureops-autonomous-implementation-completion-report.json` now reports `feature_implementation_complete=true` and `operator_evidence_required_for_tests=false` while preserving `real_world_delivery_revenue_complete=false`. This completes the local implementation lane and does not create delivery proof, revenue packet, proof-only live revenue, final bundle, external send, provider/browser action, CRM/payment mutation, invoice, credential read, accounting claim, or revenue claim.

The 2026-05-15 final hardening Studio guide pass exposes that local implementation truth in Studio Dashboard through `runtime.studio.ventureops_real_world_usecase_panel`, the localhost dashboard app, and the native Studio shell dashboard. It links operator guide `07_LOGS/Operator-Briefs/2026-05-15-ventureops-studio-real-world-usecase-test-guide.md`, lists safe rehearsal commands, and keeps real-world delivery/revenue completion blocked until factual external delivery and payment evidence exists. This is Studio visibility and real-usecase rehearsal hardening only; it does not execute external/client delivery, send externally, call providers or browsers, mutate CRM/payment systems, read credentials, claim revenue, or promote canonical state.

The activation approval packet command now reports `mission_active_local` for the live workspace. The historical draft packet remains as review material, while consumed gates are represented by `activation-approval-approved.json`, `activation-approval-consumption.json`, `mission-manifest-promotion-workflow-evolution-review-approved.json`, `mission-manifest-promotion-workflow-evolution-review-consumption.json`, `mission-agent-bus-enqueue-approval-approved.json`, `mission-agent-bus-enqueue-consumption.json`, `mission-runtime-claim-result-approval-approved.json`, `mission-runtime-claim-result-consumption.json`, `mission-runtime-result.json`, `mission-activation-execution-approved.json`, and `mission-activation-execution-consumption.json`. This activates only the local mission state after result ingestion; it does not apply workflow evolution, call providers, control browsers, or authorize external side effects.

## Authority Boundary

Mission Mode defaults to proposal/draft mode. Human approval is required for external sends, purchases, listings, payments, live trading, credential setup, protected-file edits, browser actions with external effect, provider config mutation, workflow evolution activation, and canonical promotion.

## Related Standards

- [[Sub-Agent-Orchestration-Standard]]
- [[Mission-State-Ledger]]
- [[Mission-Review-Standard]]
- [[Workflow-Evolution-Proposal-Standard]]
- [[Domain-Goal-Profile-Standard]]
- [[Mission-Recommendation-Standard]]
- [[Site-Profile-to-Workflow-Learning]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
