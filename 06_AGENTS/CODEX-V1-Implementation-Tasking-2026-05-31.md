---
title: CODEX V1 Implementation Tasking 2026-05-31
created: 2026-05-31
runtime: hermes-optimus
status: ACTIVE / CODEX IMPLEMENTATION QUEUE / HERMES REVIEW REQUIRED
type: codex-tasking
links:
  - [[ChaseOS-AI-Domain-Override-Handover-2026-05-31]]
  - [[Hermes-Runtime-Profile]]
  - [[HERMES]]
  - [[Agent-Activity-Index]]
---

# CODEX V1 Implementation Tasking — 2026-05-31

## Codex responsibilities

Implementation, website scaffold/code, waitlist/admin implementation, Forge static index implementation, Studio code polish, tests, CI/smoke checks, build fixes, safe static assets, demo fixture, and implementation handover.

## No-go boundaries

No DNS mutation, deployment, live email campaigns, Stripe/payment products, managed agents, runtime credits, arbitrary browser automation, CRM/payment mutation, provider calls with waitlist PII, external posting, or enterprise-readiness claims without separate proof/approval.

## First tasks

| Task ID | Title | Priority | Acceptance criteria |
|---|---|---|---|
| DOM-001 | Implement chaseos.ai domain constants/routes | P0 | README/site config/public routes use chaseos.ai; forge index target is /forge/index.json. |
| WEB-001 | Implement chaseos.ai website skeleton | P0 | All required routes render truthful copy. |
| WAIT-001 | Implement waitlist form | P0 | Captures required fields and consent; no email campaign. |
| ADMIN-001 | Implement protected admin stub | P0 | Auth/allowlist protected; no vault/private graph data. |
| FORGE-001 | Implement static /forge/index.json preview | P0 | Valid JSON, example packs, digest metadata, no paid claims. |
| STD-001 | Implement standards examples pages | P1 | Examples for pack/index/approval/graph/outcome. |
| DOC-001 | Public docs and GitHub readiness files | P0 | LICENSE/SECURITY/CONTRIBUTING/public README decisions surfaced. |
| STUDIO-001 | Studio V1 demo polish only within existing architecture | P0 | Route smoke and demo fixture; no new authority. |
| GRAPH-001 | Knowledge graph demo visibility | P0 | Non-private graph/source/project fixture renders with honest partial-state labels. |
| SRC-001 | Source/project organization demo fixture | P0 | Public-safe source/project examples with no private paths/secrets. |
| RUNTIME-001 | Runtime/agent awareness public-safe surface | P0 | Bounded runtime awareness only; no managed-agent/runtime-credit claims. |
| APPROVAL-001 | Approval visibility demo card | P0 | Approval Center pending/blocked visibility without approval consumption/execution. |
| MISSION-001 | Workflow/mission pack V1 example | P0 | One public-safe pack/mission example wired to Forge/standards with no payment/install overclaim. |
| TEST-001 | Build/test/smoke suite | P0 | Recorded commands/output and release-smoke packet. |
| VIDEO-001 | Demo fixture and screenshots | P1 | No private data/secrets/personal paths. |

## How Codex should report back

Return changed files, commands run, test output, screenshots/route smoke output, blockers, and claim-boundary notes. Every task should cite acceptance criteria and no-go boundary compliance.

## Hermes review

Hermes will review public claims, domain correctness, no-secret/no-personal-path leakage, V1 cutline consistency, Forge no-payment truth, legal/privacy draft labels, and route smoke evidence.
