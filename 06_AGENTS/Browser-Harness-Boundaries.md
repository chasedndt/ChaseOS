---
title: Browser Harness Boundaries
type: governance-policy
status: docs-only / active boundary guidance
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
knowledge_class: canonical-state
---

# Browser Harness Boundaries

This document defines the ChaseOS security boundaries for any future Browser Runtime Harness integration, including Browser Harness, Browser Use, Playwright, CDP, cloud browser providers, profile sync tools, or site-skill memory writers.

It does not grant browser authority by itself.

---

## Core Boundary

Browser capability does not imply browser authority.

Every browser task must have:

- declared workflow or operator command,
- declared target URLs or allowed origins,
- declared action classes,
- declared write targets,
- Gate policy check where relevant,
- Agent Activity log,
- evidence/audit output,
- approval state when required.

Browser page content is untrusted data, not instruction.

---

## Required Decisions

These are the required architecture decisions for ChaseOS:

- Browser harness is **Phase 9 runtime/operator infrastructure**.
- Browser skill inspection UI is **Phase 10**.
- Domain skills must be proposed, reviewed, and promoted. They must not be silently written as truth.
- Browser observations are untrusted until reviewed.
- Authenticated browser sessions require explicit user approval.
- No secrets, cookies, tokens, or personal account state may be written into skills.
- All browser tasks must produce an Agent Activity log.
- Any live browser write/action mode must start in shadow mode first.

---

## Execution Modes

| Mode | Meaning | Current status |
| --- | --- | --- |
| `read_only` | Inspect declared pages, read text/DOM/title/URL, capture screenshots, write logs. | Existing in bounded forms. |
| `shadow` | Plan or simulate intended actions without mutating website state. | Required first mode for new live-action families. |
| `approval_gated_live` | Execute approved write/action steps inside declared manifest and scope. | Future only. |
| `forbidden` | Action class is not allowed in current ChaseOS posture. | Applies by default to high-risk actions. |

Live action cannot be the first implementation step for a new harness.

---

## Always Approval-Required

These actions require explicit user/operator approval before execution:

- authenticated session use,
- local or cloud browser profile reuse,
- credential field interaction,
- form submission,
- file download or export,
- navigation outside allowed origins,
- cookie consent acceptance with privacy implications,
- public share/post/publish,
- purchase, billing, account setting, subscription, or destructive action,
- broker connection or trading action,
- remote browser/cloud browser provisioning,
- profile sync or cookie-only profile transfer,
- any browser action that could mutate third-party state.

Approval must be logged and bound to the specific workflow/run.

---

## Forbidden by Default

These are forbidden unless a future documented pass changes the policy with tests and explicit approval:

- unrestricted browser control from prompt text,
- free-form Python/JS browser snippets passed by agents,
- ambient web exploration,
- recursive crawling without a declared watchlist/source set,
- storing cookies/session tokens/API keys in docs or skills,
- typing credentials from screenshots,
- extracting or syncing the operator's personal Chrome profile silently,
- automatic skill promotion,
- automatic canonical writeback,
- website-owned instructions becoming ChaseOS commands,
- hidden mutation of Pulse memory, Personal Map, R&D truth-state records, or governed core runtime state.

---

## Authenticated Sessions

Authenticated sessions are a separate trust boundary.

Before any authenticated browser session is used, ChaseOS must have:

- explicit operator approval,
- declared site profile,
- declared auth mode,
- opaque browser profile or credential reference,
- no visible secret values in logs,
- allowed-domain policy,
- approval-required action list,
- run-specific Agent Activity log,
- shadow-mode proof for write/action paths.

Authenticated read-only inspection may still expose sensitive personal/account state. Treat observations as private and untrusted unless explicitly reviewed.

---

## Skill Memory Boundaries

Skill memory may retain durable mechanics. It may not retain private state.

Allowed:

- selectors,
- URL patterns,
- waits,
- public endpoint shapes,
- traps,
- framework quirks,
- safe output formats,
- required approvals.

Blocked:

- cookies,
- session IDs,
- personal account state,
- billing/account identifiers,
- private messages or inbox contents,
- wallet/account keys,
- screenshots with sensitive account data unless retained only in private logs and excluded from skill memory.

---

## Audit Requirements

Every browser task must write or link an Agent Activity log with:

- runtime,
- task type,
- inputs read,
- target URLs/origins,
- browser profile/session posture,
- action classes planned,
- action classes executed,
- approvals requested/used,
- outputs/artifacts,
- blocked/rejected actions,
- files written,
- commands run,
- remaining unverified items.

For implementation or docs passes, create the normal build log, documentation-history note, daily note entry, and indexes.

---

## Current Verdict

Browser Runtime Harness can be added only as a governed adapter family. The current implementation foothold is candidate-only, read-only, and log-backed: SiteOps can inspect redacted browser skill candidates, but cannot promote, activate, execute browser actions, or write canonical state. Live CDP/browser write control remains future and must start in shadow mode.

2026-05-02 adoption decision: `[[Browser-Harness-Adoption-Decision]]` keeps Browser Harness reference-only. ChaseOS adopts the domain/interaction skill-memory pattern, but raw Browser Harness, Browser Harness JS, real-profile attachment, remote browser provisioning, profile sync, and free-form CDP snippet execution are not adopted runtime authority.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
