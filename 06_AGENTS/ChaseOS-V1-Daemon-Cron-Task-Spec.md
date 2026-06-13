---
title: ChaseOS V1 Daemon Cron Task Spec
created: 2026-05-31
runtime: hermes-optimus
status: DRAFT / SAFE CHECKS ONLY / NOT ACTIVATED
type: daemon-cron-spec
links:
  - [[ChaseOS-AI-Domain-Override-Handover-2026-05-31]]
  - [[Hermes-Runtime-Profile]]
  - [[HERMES]]
  - [[Agent-Activity-Index]]
---

# ChaseOS V1 Daemon / Cron Task Spec

## Discovery summary

The repo contains ChaseOS schedule/daemon/Agent Bus surfaces and Hermes has a durable Kanban/cron runtime available. This pass does not activate new live jobs because the safe check commands should be implemented and verified by Codex first.

## Safe scheduled tasks to create after Codex implements scripts

| Task | Cadence | Owner | Command shape | Must not do |
|---|---|---|---|---|
| Daily V1 readiness snapshot | daily | Hermes/Ops | read-only readiness script | no writes except report |
| Daily stale Kanban blocker report | daily | Hermes/Ops | board/status read | no auto-complete/unblock |
| Daily website route smoke check | daily | Ops | local/public route GETs | no deployment/DNS |
| Daily Forge index JSON validation | daily | Ops | fetch/parse/digest compare | no upload/install/payment |
| Daily public-claims drift check | daily | Hermes/Ops | rg/static scan | no broad rewrites |
| Weekly GitHub public-readiness check | weekly | Hermes/Ops | no-secret/path/claims scan | no GitHub publish |
| Weekly docs/domain reference scan | weekly | Hermes/Ops | rg domain markers | no blind replace |
| Weekly waitlist export/check | weekly | Ops | only if waitlist implemented | no emails/PII provider calls |
| Weekly security/public leak scan | weekly | Ops | local static scan | no exfiltration |

## Forbidden scheduled tasks without explicit approval

Outbound emails, social posting, DNS changes, payments, marketplace payouts, provider/model calls using waitlist PII, browser automation, CRM mutation, or external deployment.
