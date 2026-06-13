---
title: Codex Web Launch Build Task
created: 2026-05-31
owner: Codex Web
status: READY FOR CODEX WEB / HUMAN APPROVAL REQUIRED FOR DEPLOYMENT-DNS
type: codex-task
primary_domain: https://chaseos.ai
---

# Codex Web Launch Build Task — 2026-05-31

## Read first

Read these if present:

- `06_AGENTS/ChaseOS-Web-Repository-Launch-Build-Handover-2026-05-31.md`
- `06_AGENTS/ChaseOS-AI-Domain-Override-Handover-2026-05-31.md`
- `06_AGENTS/ChaseOS-Platform-Monetization-Forge-Standards-Data-Moat-Handover-2026-05-31.md`
- `06_AGENTS/ChaseOS-Post-Domain-Website-LaunchOps-Handover-2026-05-31.md`
- `06_AGENTS/ChaseOS-Launch-Video-GitHub-Public-Readiness-Handover-2026-05-31.md`
- `06_AGENTS/ChaseOS-Promotion-Bridge-Policy.md`
- `07_LOGS/Kanban/ChaseOS-Multi-Repo-Launch-Kanban-2026-05-31.md`
- `07_LOGS/Kanban/ChaseOS-Multi-Repo-Agent-Assignments-2026-05-31.md`

## Repo

Local path:

```text
%USERPROFILE%\Documents\Projects\chaseos-web
```

WSL path:

```text
<WSL_PROJECTS_ROOT>/chaseos-web
```

Primary domain:

```text
https://chaseos.ai
```

Do not use `chaseos.systems` as primary.

## Your scope

You are Codex Web. You own website implementation and local verification.

Tasks:

1. WEB-001 — Confirm `chaseos-web` repo structure.
2. WEB-002 — Build/align Astro/Tailwind website scaffold.
3. WEB-003 — Implement homepage.
4. WEB-004 — Implement waitlist.
5. WEB-005 — Implement admin stub/protection.
6. WEB-006 — Implement Forge page and `/forge/index.json`.
7. WEB-007 — Implement standards page/examples.
8. WEB-008 — Implement open-core/pricing/download/privacy/security/roadmap/terms.
9. WEB-009 — Add Cloudflare Pages config.
10. WEB-010 — Add smoke tests.
11. DOMAIN-001 — `chaseos.ai` DNS/Cloudflare setup checklist.
12. DOMAIN-002 — Cloudflare Pages deployment checklist.
13. DOMAIN-003 — Keep download gated until V1 gate passes.
14. FORGE-001 — Forge public preview hardening.
15. STD-001 — Standards examples hardening.
16. GH-002 — Web repo GitHub setup checklist/approval handoff.

## Public copy requirements

Use:

```text
ChaseOS is the local-first AI operating system for builders running real projects with agents.
```

Expanded:

```text
ChaseOS turns scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.
```

CTA:

```text
Join Early Access
```

Secondary CTA:

```text
Explore Chaser Forge
```

## Required routes

- `/`
- `/waitlist`
- `/studio`
- `/forge`
- `/forge/index.json`
- `/standards`
- `/open-core`
- `/pricing`
- `/docs`
- `/download`
- `/privacy`
- `/security`
- `/roadmap`
- `/support`
- `/terms`
- `/creators`
- `/submit-pack`
- `/admin`

## Hard boundaries

Do not:

- deploy to production;
- mutate DNS/Cloudflare;
- publish repos/releases;
- expose a public download;
- send emails;
- do social posting;
- implement checkout/payment/runtime credits;
- expose waitlist PII publicly;
- run model calls over waitlist PII;
- claim live paid Forge marketplace, creator payouts, managed agents, untrusted install, or fully public core release;
- copy private vault/build logs/raw transcripts into the website repo.

## Acceptance evidence

Return a report with:

- repo structure inventory;
- routes implemented;
- build command/output;
- smoke test command/output;
- Forge JSON validation result;
- stale-domain scan result;
- no-overclaim scan result;
- admin protection/stub status;
- waitlist PII boundary;
- Cloudflare checklist path;
- deployment blockers and human approvals needed.

## Hermes review

Hermes reviews public claims, no-stale-domain status, Forge/payment claims, admin/PII posture, and download gating before human deploy approval.
