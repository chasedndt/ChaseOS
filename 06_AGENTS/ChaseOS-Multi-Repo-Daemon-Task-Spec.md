---
title: ChaseOS Multi-Repo Daemon Task Spec
created: 2026-05-31
runtime: hermes-optimus
status: SAFE PLAN ONLY / NO UNSAFE EXTERNAL ACTIONS SCHEDULED
type: daemon-scheduled-task-spec
---

# ChaseOS Multi-Repo Daemon Task Spec

## 1. Purpose

This is a safe daemon/scheduled-task plan for the ChaseOS multi-repo launch lane. It defines reminders/checks only. It does not schedule unsafe external actions.

## 2. Repositories/workspaces in scope

- `chaseos_Obsidian` — private operating vault and internal Kanban/logs.
- `chaseos-core` — private product/core repo after initialization.
- `chaseos-web` — public site repo for `https://chaseos.ai`.

## 3. Allowed scheduled checks

### DAEMON-001 — Stale task report
- Scope: Markdown Kanban and assignment files.
- Cadence: daily or on manual request.
- Output: private report in `07_LOGS/Operator-Briefs/` or `07_LOGS/Kanban/`.
- Allowed actions: read task ids/statuses, report stale/open/blocked items.
- Forbidden actions: auto-complete, publish, deploy, email/social send.

### DAEMON-002 — Secret/path scan reminder
- Scope: `chaseos-core` and `chaseos-web` before private baseline/public deploy.
- Cadence: before GitHub baseline, before deployment, and weekly while launch-active.
- Output: reminder/checklist; optional local scan command suggestions.
- Allowed actions: remind and report scan status if run manually/approved.
- Forbidden actions: printing secret values, pushing fixes, changing repo visibility.

### DAEMON-003 — Domain-reference scan
- Scope: public docs/site content.
- Cadence: daily while launch-active.
- Output: report stale primary-domain references.
- Allowed actions: scan for `chaseos.systems` and verify it is only historical/superseded/secondary.
- Forbidden actions: DNS mutation, registrar/Cloudflare changes.

### DAEMON-004 — Website route smoke check
- Scope: local `chaseos-web` dev/build output.
- Cadence: before deployment or daily during active web implementation.
- Output: route availability/build report.
- Allowed actions: run local non-network smoke if repo scripts exist.
- Forbidden actions: production deploy, browser automation, credential reads.

### DAEMON-005 — Forge index JSON validation
- Scope: `chaseos-web` `/forge/index.json` and pack manifests.
- Cadence: on changes and daily during active launch work.
- Output: parse/schema status.
- Allowed actions: validate JSON shape and required fields.
- Forbidden actions: remote fetch/install, marketplace payment/licensing actions.

### DAEMON-006 — Public claims drift check
- Scope: website/public docs/README copy.
- Cadence: on changes and daily during active launch work.
- Output: claims drift report.
- Allowed actions: search for forbidden overclaims and stale domain assumptions.
- Forbidden actions: rewrite public pages automatically unless explicitly approved.

### DAEMON-007 — GitHub readiness reminder
- Scope: `chaseos-core` private baseline and `chaseos-web` launch readiness.
- Cadence: daily until resolved.
- Output: blockers and human approvals needed.
- Allowed actions: reminder/report only.
- Forbidden actions: repo creation, visibility change, push, release publication.

### DAEMON-008 — V1 blocker snapshot
- Scope: V1 release/download gate, core baseline, website launch, claims, DNS, public/private boundary.
- Cadence: daily or before launch decision.
- Output: single blocker snapshot for human approval.
- Allowed actions: aggregate existing reports and task statuses.
- Forbidden actions: declare launch complete without evidence/human approval.

## 4. Blocked scheduled actions

The daemon/scheduled-task lane must not perform:

- sending emails;
- social posting;
- payment actions;
- DNS changes;
- browser automation;
- model calls over waitlist PII;
- publishing repos;
- publishing releases;
- changing GitHub repo visibility;
- pushing to remotes;
- Cloudflare production deploys;
- public download exposure;
- marketplace payment/licensing/payout mutation.

## 5. Suggested report format

Each safe check should report:

```yaml
check_id:
date:
repo_or_workspace:
inputs_read:
commands_run:
status: pass | warn | blocked | not_run
findings:
blockers:
human_approvals_needed:
next_safe_action:
forbidden_actions_not_taken:
```

## 6. Hermes runtime/cron posture

No cron job was created by this document. It is a plan/spec only.

If the operator later approves scheduling, prefer safe reminders/checks that deliver to the existing Hermes alert channel and stay silent when no change is detected. Any job prompt/script must be self-contained and must repeat the forbidden-action list above.

## 7. Review method

Hermes reviews scheduled-check outputs against:

- `07_LOGS/Kanban/ChaseOS-Multi-Repo-Launch-Kanban-2026-05-31.md`;
- `07_LOGS/Kanban/ChaseOS-Multi-Repo-Agent-Assignments-2026-05-31.md`;
- `06_AGENTS/ChaseOS-Promotion-Bridge-Policy.md`;
- current `chaseos.ai` domain override handovers;
- public/private boundary and V1 release/download gate.
