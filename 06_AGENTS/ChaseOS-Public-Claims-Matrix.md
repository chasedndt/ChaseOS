---
title: ChaseOS Public Claims Matrix
created: 2026-05-31
runtime: hermes-optimus
status: DRAFT / PUBLIC CLAIMS CONTROL
type: claims-matrix
links:
  - [[ChaseOS-AI-Domain-Override-Handover-2026-05-31]]
  - [[Hermes-Runtime-Profile]]
  - [[HERMES]]
  - [[Agent-Activity-Index]]
---

# ChaseOS Public Claims Matrix

| Claim | Status | Public-safe wording / constraint |
|---|---|---|
| local-first memory | **CURRENT / PARTIAL** | Local-first substrate exists; public-safe claims must avoid hosted sync/managed memory unless proven. |
| source/project organization | **CURRENT / SAFE** | Core ChaseOS identity and repo/vault surfaces support project/source organization. |
| knowledge graph visibility | **CURRENT / PARTIAL** | Graph/Studio read surfaces exist; persisted graph DB and full UX remain not fully public-ready. |
| Studio command surface | **CURRENT / PARTIAL** | Studio exists and has many read-only/approval-gated panels; release-grade polish still open. |
| runtime/agent awareness | **CURRENT / PARTIAL** | Runtime/Agent Bus awareness exists; unrestricted dispatch/claims are not public capability. |
| Approval Center visibility | **CURRENT / PARTIAL** | Approval visibility exists; generic approval execution is still governed/narrow. |
| workflow/mission packs | **PREVIEW** | Mission/workflow pack foundation and examples exist; public pack UX still needs Codex implementation. |
| Chaser Forge preview | **PREVIEW** | Local Forge proof exists; public preview/static index pending. |
| Forge live marketplace | **BLOCKED** | No live paid marketplace/payment/license path. |
| Forge payments/licensing | **DO NOT CLAIM** | Future only until payment/license infrastructure exists. |
| managed agents | **FUTURE** | Future managed runtime infrastructure, not current public capability. |
| runtime credits | **FUTURE** | Strategy only. |
| arbitrary browser automation | **DO NOT CLAIM** | Only bounded SiteOps/browser proofs where explicitly implemented. |
| live external posting | **DO NOT CLAIM** | Requires explicit approval/executor; not V1 public claim. |
| live email sending | **DO NOT CLAIM** | Waitlist/contact only after implementation and approval; no campaigns now. |
| CRM/payment mutation | **DO NOT CLAIM** | Blocked/future. |
| enterprise readiness | **DO NOT CLAIM** | Can say enterprise/private deployment planned, not ready. |
| GitHub public readiness | **BLOCKED** | Needs repo/package hygiene, LICENSE/SECURITY/CONTRIBUTING, no-leak scan. |
| open-core / source-available posture | **PREVIEW** | Strategy needs LICENSE/NOTICE/terms decisions. |
| privacy/security posture | **CURRENT / PARTIAL** | Local-first boundary safe; legal/security docs draft only. |

## Global rule

If a claim requires live payments, live managed runtime, arbitrary browser control, live external sends, CRM/payment mutation, or enterprise compliance, classify it as FUTURE / BLOCKED / DO NOT CLAIM unless current repo evidence and green tests prove otherwise.
