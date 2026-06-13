# VentureOps Runtime Helpers

`runtime/ventureops/` is the read-only deterministic helper layer for ChaseOS VentureOps.

It provides:

- instance/workspace profiling from local markdown and ChaseOS markers
- evidence-backed draft workflow recommendations
- evidence-backed draft mission recommendations
- use-case registry loading and validation
- workflow-pack, recommendation, proof-card, and scorecard validators
- Mission Mode manifest, sub-agent, state, review, evolution, domain-profile,
  site-profile, and mission-recommendation validators
- Mission Mode draft helpers for manifests, sub-agent plans, state ledgers,
  workflow evolution proposals, and site-profile candidates
- Mission Mode dry-run workspace validation for local artifact bundles
- Mission Mode activation/AOR readiness checks for approved dry-run workspaces
- Mission Mode draft activation approval packets plus design-only AOR handler
  and Agent Bus mission task contract notes
- autonomous implementation-completion audit that separates local/testable
  feature completion from real-world delivery/revenue evidence completion
- Studio-facing VentureOps real-world usecase panel support for rehearsing the
  AI Runtime Governance Audit workflow while preserving the real evidence gate
- proof-card object construction for future approved runs
- the exact `ventureops_ai_runtime_security_audit` AOR workflow alias for the
  hardened `agent_runtime_governance_audit` implementation

It does not call providers, access external services, read secrets, send messages, mutate canonical state, activate browser skills, enqueue Agent Bus mission tasks outside guarded gates, or perform live trading/payment/browser actions. The executable AOR security-audit workflow writes bounded local proof artifacts only. Mission dry-run validation, activation-readiness checks, and draft activation approval packet generation inspect local artifacts only and do not activate missions.
