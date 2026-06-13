---
type: framework-matrix
title: Runtime Adapter Use Case Matrix
status: DOCS-ONLY
created: 2026-05-10
updated: 2026-05-10
---

# Runtime Adapter Use Case Matrix

> VentureOps uses runtime adapters according to declared workflow need and authority boundary. Provider choice does not expand permissions.

| Runtime / surface | Best VentureOps role | Default authority |
|---|---|---|
| ChaseOS AOR | Routing, manifests, task state, permission gates, runtime coordination, audit logs | Manifest-bound execution only |
| SIC / Capture | Raw intake and source packaging | Intake and source artifact generation only |
| Hermes | Research, reasoning, planning, scoring, briefs, advisory drafts | Declared workflow reads/writes only |
| OpenClaw | Browser/GUI execution, screenshots, supervised SaaS/file operations | Shadow/read-only first; approved action later |
| Codex | Repo-aware implementation, tests, docs, code patches, refactors | Bounded development runtime; no core state ownership |
| Claude Code | Repo-aware implementation and docs work | Harness-scoped edits with protected-file approval |
| Discord | Approvals, alerts, summaries, blockers, runtime status | Visibility/approval transport, not machine truth |
| MCP | Controlled resources, tools, prompts | Scoped contract only |
| Studio | Human-facing product shell and approval surface | Read-only or approval-gated based on panel |
| n8n | Future workflow runtime / integration runner | Dry-run/readiness until deployed and scoped |
| Human | Sensitive actions, financial decisions, external sends, credential setup | Final authority |

## Routing Rule

Choose the least-authority runtime that can produce the required proof artifact. If a weaker runtime cannot satisfy evidence, governance, or output requirements, escalate through AOR/Gate, not through ambient chat.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
