---
title: Codex Core Private Baseline Task
created: 2026-05-31
owner: Codex Core
status: READY FOR CODEX CORE / HUMAN APPROVAL REQUIRED FOR REMOTE/PUBLICATION
type: codex-task
---

# Codex Core Private Baseline Task — 2026-05-31

## Read first

Read these if present in the workspace/vault handoff set:

- `06_AGENTS/ChaseOS-Multi-Repo-Operating-Model-Promotion-Bridge-Handover-2026-05-31.md`
- `06_AGENTS/ChaseOS-Core-GitHub-Private-Baseline-Handover-2026-05-31.md`
- `06_AGENTS/ChaseOS-Promotion-Bridge-Policy.md`
- `07_LOGS/Kanban/ChaseOS-Multi-Repo-Launch-Kanban-2026-05-31.md`
- `07_LOGS/Kanban/ChaseOS-Multi-Repo-Agent-Assignments-2026-05-31.md`
- `PROJECT_FOUNDATION.md`
- `ROADMAP.md`
- `SYSTEM-STATUS.md`
- `06_AGENTS/Feature-Register.md`
- `06_AGENTS/Feature-Fit-Register.md`
- `06_AGENTS/ChaseOS-V1-Release-Cutline.md`
- `06_AGENTS/ChaseOS-Gate.md`
- `06_AGENTS/Permission-Matrix.md`
- `06_AGENTS/Agent-Control-Plane.md`

## Your scope

You are Codex Core. You own private core-repo baseline safety, not public launch.

Tasks:

1. CORE-001 — Backup ChaseOS Core local folder.
2. CORE-002 — Detect/init Git in `chaseos-core`.
3. CORE-003 — Add/update `.gitignore`.
4. CORE-004 — Run secret scan / path scan.
5. CORE-005 — Create private baseline commit.
6. CORE-006 — Connect private GitHub remote only after human approval and private visibility confirmation.
7. CORE-007 — Create public-readiness checklist.
8. CORE-008 — Create release/download gate.
9. PROMOTE-003 — Create core import manifest template.
10. GH-001 — Core repo private GitHub setup after approval.

## Hard boundaries

Do not:

- create a public GitHub repo;
- push to a public remote;
- publish releases/downloads;
- expose `ChaseOS.exe` or installer assets;
- bulk-copy `chaseos_Obsidian` into `chaseos-core`;
- commit `.env`, credentials, tokens, local DBs, private build logs, raw transcripts, personal notes, or private strategy;
- print secret values into logs;
- treat checklist completion as public-release approval.

## Acceptance evidence

Produce a private baseline report that includes:

- repo path used;
- backup proof/path;
- Git status/init result;
- `.gitignore` summary;
- secret/path scan command patterns and redacted findings;
- baseline commit hash if created;
- remote status/visibility only if approved;
- public-readiness checklist path;
- release/download gate path;
- import manifest template path;
- blockers and human approvals needed.

## Hermes review

Return outputs for Hermes review before human approval. Hermes will check against the promotion bridge policy and public/private boundary.
