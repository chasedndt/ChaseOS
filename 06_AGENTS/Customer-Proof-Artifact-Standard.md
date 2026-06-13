---
type: framework-standard
title: Customer Proof Artifact Standard
status: DOCS-ONLY
created: 2026-05-10
updated: 2026-05-10
---

# Customer Proof Artifact Standard

> A proof artifact is the customer/internal evidence packet that shows what a VentureOps workflow did, what it used, what it produced, and what remains unresolved.

## Proof Artifact Types

| Type | Use |
|---|---|
| Proof-of-run card | Compact evidence summary for one run |
| Permission matrix | Shows read/write/tool/contact authority |
| Risk report | Shows risks, blockers, and severity |
| Remediation plan | Shows recommended fixes and owner actions |
| Client report draft | External-facing draft, human-reviewed before send |
| Screenshot set | Browser/GUI proof where relevant |
| Output bundle | Workflow output files and generated artifacts |

## Required Fields

- workflow_id
- run_id
- date
- operator/runtime
- trigger
- inputs used
- tools used
- permissions exercised
- permissions blocked
- outputs written
- external side effects
- approvals required
- approvals granted
- risks found
- unresolved risks
- next recommended action
- links to audit logs

## Customer Boundary

Customer-facing proof artifacts must never include secrets, raw credentials, private browser state, wallet keys, session tokens, or unredacted private file paths unless the operator deliberately prepares a redacted client copy.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
