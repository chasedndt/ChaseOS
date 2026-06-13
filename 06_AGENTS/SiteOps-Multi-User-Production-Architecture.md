---
title: SiteOps Multi-User Production Architecture
status: PARTIAL
runtime_status: production-scaffolded-local-dev-only
date: 2026-04-30
---

# SiteOps Multi-User Production Architecture

**Approval Center routing:** SiteOps approval-queue references should route to [[ChaseOS-Approval-Center]] when surfaced to operators.

ChaseOS SiteOps is the governed web-workflow runtime for ChaseOS. The user-facing surface is **Site Skills**. The technical registry is the **Website Workflow Index**.

This pass upgrades SiteOps from a local dry-run registry into a production-shaped scaffold. The scaffold supports tenant, workspace, and user scope across templates, installations, workflow runs, browser profile references, credential references, provider bindings, approvals, budgets, policy decisions, and audit events.

## Current Implementation Status

Status: **PARTIAL / production scaffold**

Built now:
- system catalog fixtures under `runtime/siteops/catalog/`
- tenant fixture under `runtime/siteops/tenants/local.yaml`
- scoped models, validators, policy checks, approvals, budgets, credentials, browser profile refs, audit storage, and dry-run runner
- CLI surfaces for catalog, tenants, skills, workflows, runs, approvals, credentials, browser profiles, and budgets
- scoped run/audit/approval artifacts under `07_LOGS/SiteOps-*`
- scoped Browser Skill candidate promotion request, non-mutating apply contract, denied-by-default Gate apply design packets, fail-closed Gate executor specs, review-only Gate allowlist review packets, and design-only trusted executor packets
- focused tests for tenancy, policy, approvals, budgets, credentials, browser profiles, dry-runs, and CLI smokes

Not built:
- live browser execution
- paid provider/API execution
- public/community marketplace UI
- Phase 10 dashboard
- trusted Browser Skill / Site Skill Card apply executor
- automatic canonical writeback
- Hermes/OpenClaw authority expansion

Hermes-specific boundary: Hermes may be used as a bounded reviewer, shadow evaluator, policy consistency checker, documentation sanity checker, or runtime boundary checker. Hermes is not the SiteOps implementation owner or canonical runtime, must not read secrets, must not invoke live connectors, and must not treat Hermes memory as ChaseOS truth.

## Layered Shape

1. Global Catalog Layer: system-owned SiteSkillTemplate, WorkflowTemplate, provider templates, and policy packs.
2. Tenant Configuration Layer: tenant-installed skills, provider bindings, budget rules, and policy overrides.
3. Workspace Layer: workspace workflow availability, artifacts, run history, and approvals.
4. User Layer: per-user browser profile refs, credential refs, approvals, and run artifacts.
5. Execution Layer: dry-run planner now; browser/API/CLI/hybrid runners later.
6. Policy / Referee Layer: fail-closed scope, role, domain, blocked action, budget, credential, and browser ownership checks.
7. Audit / Provenance Layer: durable SiteOpsRun records, append-only SiteOpsAuditEvent JSONL, approval objects, and artifact links.
8. Product Surface Layer: CLI now; admin UI, approval queue, and replay inspector later.

## Local Compatibility Scope

Local single-user ChaseOS is represented as production scope:

```yaml
tenant_id: local
workspace_id: default
user_id: local-user
```

This is compatibility mode, not a separate architecture.

## Core Flow

```text
Site Skill Template
-> Tenant Site Skill Installation
-> Workflow Installation
-> Dry Run
-> Policy Decision
-> ApprovalRequest when needed
-> SiteOpsRun
-> SiteOpsAuditEvent
```

All execution remains dry-run-only in this pass.

## Cross-Runtime Candidate Boundary

Browser Runtime Skill Memory and BOSL can produce untrusted browser skill candidates under `03_INPUTS/Browser-Skill-Candidates/`. SiteOps exposes those candidates through redacted CLI inspection, non-mutating preflight, scoped approval request persistence, non-mutating apply-contract commands, denied-by-default Gate apply design previews, fail-closed Gate executor specs, review-only Gate allowlist review packets, and design-only trusted executor packets.

Current candidate commands are **local-dev integration surfaces** with a production-shaped approval foothold. `request-promotion --tenant ... --user ... --write-approval-request` can create only scoped `SiteOpsRun`, `SiteOpsAuditEvent`, and `ApprovalRequest` artifacts. It does not create `SiteSkillTemplate`, `TenantSiteSkillInstallation`, `WorkflowInstallation`, trusted browser skills, Site Skill Cards, browser sessions, or canonical memory.

Production candidate promotion remains future work. `apply-contract` can report when an approved request is ready for future Gate apply review, `gate-apply-design` can compute the denied-by-default future apply boundary and target write preview, `gate-executor-spec` can describe the future executor preconditions/write plan, `gate-allowlist-review` can review allowlist eligibility without editing Gate policy, and `trusted-executor-design` can define future executor components/audit/rollback behavior without implementing the executor. The actual trusted write operation remains not allowlisted and the executor remains not built, so no trusted Browser Skill or Site Skill Card can be written until a later Gate executor pass explicitly adds and verifies that authority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
