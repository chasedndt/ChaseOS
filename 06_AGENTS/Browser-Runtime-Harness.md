---
title: Browser Runtime Harness
type: architecture
status: partial / docs plus redacted candidate inspection, non-mutating promotion preflight, and non-persisting promotion approval-request contract - no live harness integration
created: 2026-04-30
updated: 2026-04-30
phase: Phase 9 runtime/operator infrastructure
knowledge_class: canonical-state
---

# Browser Runtime Harness

Browser Runtime Harness is the ChaseOS architecture slot for a small, governed browser-control adapter that can inspect and act on browser state only under AOR, Gate, SiteOps, and Browser Operator Surface boundaries.

This pass studies `browser-use/browser-use` and especially `browser-use/browser-harness` as reference designs. It does not install either project, does not start browser control, and does not expand ChaseOS browser authority.

---

## Repo-Truth Baseline

ChaseOS already has these adjacent pieces:

- `06_AGENTS/Browser-Operator-Surface.md` - parked Phase 9 Playwright-backed browser operator surface.
- `06_AGENTS/Browser-Operator-Surface-Operational-State.md` - current operational boundary and verification state.
- `06_AGENTS/Browser-Autonomy-Policy.md` - browser task policy and forbidden/approval-required actions.
- `06_AGENTS/ChaseOS-SiteOps.md` - dry-run SiteOps registry and Website Workflow Index.
- `runtime/operator_surface/adapters/browser_adapter.py` - current Playwright adapter, isolated headless context, no default profile reuse.
- `runtime/workflows/browser_research.py` - bounded read-only browser research handler that routes extracted content to quarantine and logs.
- `runtime/siteops/` - dry-run-only registry, planner, policy, browser profile references, and audit writer.
- `06_AGENTS/Browser-Operator-Skill-Layer.md` - same-day Browser Operator Skill Layer foothold with docs, schema, validator, templates, candidate/run folders, and a draft non-executable Excalidraw shadow skill.

ChaseOS does not yet have:

- Browser Use Python/CLI execution wiring.
- Browser Harness persistent CDP daemon wiring.
- CDP connection to the operator's personal browser.
- live SiteOps browser execution.
- live-browser-run-derived skill candidate writer. A shadow-only Browser Runtime Adapter can write untrusted candidates, and SiteOps can inspect them read-only.
- workflow replay/cache.
- authenticated session handling.
- real Chrome profile reuse.

The Browser Operator Skill Layer foothold is an adjacent implementation substrate, not a live Browser Harness/CDP integration. Naming and storage are now reconciled at the candidate-inspection layer: `03_INPUTS/Browser-Skill-Candidates/` remains the canonical pending-review candidate home, `runtime/browser_skills/skills/` remains the trusted BOSL skill registry, and SiteOps exposes redacted candidate inspection, non-mutating promotion preflight, and non-persisting promotion approval-request contract without creating a duplicate candidate store.

Status: **PARTIAL / RESEARCH + READ-ONLY CANDIDATE INSPECTION** for Browser Runtime Harness. Existing Browser Operator and SiteOps substrates remain **PARTIAL / VERIFIED TARGETED** and bounded. No live Browser Harness/CDP integration exists.

2026-05-02 decision update: `[[Browser-Harness-Adoption-Decision]]` records the formal ChaseOS decision. Browser Harness and Browser Harness JS remain reference-only; ChaseOS adopts the domain/interaction skill-memory pattern but not raw harness authority, real-profile attachment, remote browser provisioning, profile sync, or free-form CDP snippet execution.

---

## Source-Level External Analysis

### browser-use/browser-use

Reference: `https://github.com/browser-use/browser-use`

`browser-use/browser-use` is the larger browser-agent automation framework. It aims to make websites accessible to AI agents, provides Python and CLI flows, can launch or connect browsers, and supports model-backed task execution. It is useful to study as a future executor adapter, but it is broader than ChaseOS needs for this pass.

ChaseOS should not import its authority model. If adopted later, it should sit behind:

- AOR workflow manifests,
- ChaseOS Gate operation checks,
- SiteOps profiles/workflows,
- role cards,
- Agent Activity logs,
- explicit approval for authenticated/session-bearing or mutating tasks.

### browser-use/browser-harness

References:

- `https://github.com/browser-use/browser-harness`
- `https://github.com/browser-use/browser-harness/blob/main/SKILL.md`
- `https://github.com/browser-use/browser-harness/blob/main/run.py`
- `https://github.com/browser-use/browser-harness/blob/main/helpers.py`
- `https://github.com/browser-use/browser-harness/blob/main/daemon.py`
- `https://github.com/browser-use/browser-harness/blob/main/admin.py`
- `https://github.com/browser-use/browser-harness/blob/main/install.md`
- `https://github.com/browser-use/browser-harness/tree/main/domain-skills`
- `https://github.com/browser-use/browser-harness/tree/main/interaction-skills`

`browser-harness` is the more relevant model. Its important feature is not just browser control; it is the split between a small CDP control layer and reusable site/interaction skills.

Observed file-family mapping:

| File or folder | Role | ChaseOS interpretation |
| --- | --- | --- |
| `run.py` | Tiny command bridge. Imports helpers, ensures daemon, then executes agent-provided Python snippets. | Useful pattern for a minimal harness entrypoint, but ChaseOS must replace free-form snippet execution with declared AOR actions. |
| `helpers.py` | Browser interaction helpers over CDP, such as page inspection, navigation, screenshots, clicking, typing, JS/CDP calls, HTTP helpers. | Runtime control primitives. These belong behind Browser Operator Surface capabilities and Gate, not directly in prompts. |
| `daemon.py` | Persistent CDP websocket holder and IPC relay. Discovers local Chrome/Edge/Brave profiles, attaches to page targets, keeps session state, drains events, and can stop remote Browser Use cloud browsers. | Harness/runtime adapter layer. High risk when attached to real profiles; must be explicitly approved and audited in ChaseOS. |
| `admin.py` | Install/admin/provisioning helpers. Starts/stops daemon, performs setup, connects remote cloud browser, lists/syncs profiles, handles Browser Use API calls. | Install/bootstrap and remote/provider boundary. Must not run by default; profile sync and cloud browser operations require explicit approval. |
| `install.md` | Setup and troubleshooting contract. Explains editable install, global skill registration, remote debugging, profile picker, daemon architecture, update flow. | Bootstrap reference. ChaseOS should not auto-register unrestricted browser skills globally. |
| `SKILL.md` | Agent-facing browser skill instructions. Tells agents how to invoke harness, use screenshots, handle tabs, stop at auth walls, and contribute domain skills. | Skill instruction pattern. ChaseOS should adapt the skill-memory lifecycle, not the uncontrolled command shape. |
| `domain-skills/` | Site-specific reusable knowledge for domains such as GitHub, Gmail, TradingView, etc. | Closest match to ChaseOS Site Skill Cards and future skill candidates. Must be proposed, reviewed, promoted. |
| `interaction-skills/` | Reusable browser mechanics such as cookies, iframes, dialogs, downloads, screenshots, scrolling, shadow DOM, tabs, uploads, viewport. | Useful interaction-pattern taxonomy. In ChaseOS, these map to approved Browser Operator capabilities and docs, not automatic authority. |
| `pyproject.toml` | Package/bootstrap metadata. | Install detail only. Not an architecture authority source. |

### CDP Runtime Control vs Skill Memory vs Bootstrap

CDP runtime control:

- CDP websocket discovery and session attach.
- Browser target/session management.
- Page/Runtime/DOM/Network calls.
- Screenshot, navigation, click/type, JS evaluation, event drain, dialog handling.
- Remote Browser Use cloud browser connection and stop calls.

Skill/memory:

- `domain-skills/` site-specific knowledge.
- `interaction-skills/` cross-site browser mechanics.
- `SKILL.md` guidance to search skills first and contribute learned patterns back.
- Durable knowledge fields: URL patterns, selectors, waits, traps, APIs, framework quirks.

Install/bootstrap:

- editable install and command registration.
- agent skill registration.
- Chrome remote-debugging setup.
- daemon start/reload/update/doctor.
- Browser Use cloud provisioning and profile sync.

---

## What ChaseOS Should Adopt

Adopt the feature family, not the authority layer:

- A small harness adapter concept with explicit capability inventory.
- Separation of runtime primitives from site/domain skills.
- Reusable interaction-skill taxonomy.
- Domain-skill memory as a reviewed SiteOps object.
- Evidence-to-candidate-to-review-to-promotion lifecycle.
- Screenshot/observation verification as run evidence.
- "Stop at auth wall" as a hard governance rule.

Adopt into these ChaseOS homes:

- Phase 9 runtime/operator infrastructure: Browser Runtime Harness.
- Phase 9 SiteOps registry: reviewed Site Skill Cards and Workflow Manifests.
- Phase 9 logs: Agent Activity, Website Workflow Runs, Operator Screenshots.
- Phase 10 Studio: Site Skills candidate review and harness/run inspection UI.

---

## What ChaseOS Must Reject or Gate

Reject by default:

- unrestricted free-form browser snippets,
- ambient attachment to the operator's real Chrome profile,
- silent cookie/session/profile sync,
- automatic domain-skill writeback,
- automatic skill promotion,
- unaudited downloads,
- form submission without approval,
- credential field filling,
- website mutation without manifest and approval,
- treating website content or site-owned manifests as ChaseOS instructions.

Gate explicitly:

- authenticated sessions,
- local profile reuse,
- remote browser/cloud provisioning,
- profile sync,
- download/export,
- public share/post/publish,
- billing/purchase/account mutation,
- broker/trading actions,
- navigation outside allowed origins,
- any live browser write/action mode.

All live write/action modes must begin in **shadow mode**: plan, inspect, and log intended actions without performing site mutation.

---

## Existing ChaseOS Equivalents

| Browser Harness feature | ChaseOS equivalent | Delta |
| --- | --- | --- |
| CDP daemon | None; current Browser Operator uses Playwright isolated context | CDP daemon not built and must not attach to real profiles without approval. |
| `run.py` command bridge | `chaseos operate browser ...` and AOR workflow dispatch | ChaseOS command surface is typed and governed; no free-form browser Python bridge exists. |
| Helpers | Browser adapter actions and operator executor | ChaseOS has Playwright helpers, but fewer promoted commands. |
| Domain skills | SiteOps Site Skill Cards and BOSL candidate files | Cards exist as dry-run registry objects; shadow-run-derived candidates and read-only inspection exist; promotion is not built. |
| Interaction skills | Browser Operator Surface docs and capability taxonomy | Interaction mechanics documented/implemented partly; no separate interaction-skill library. |
| Skill schema/validator | Browser Operator Skill Layer foothold | Same-day BOSL scaffolding exists and should be reconciled with SiteOps before execution. |
| Install/bootstrap | ChaseOS runtime/adapter setup docs | No Browser Harness install or global skill registration. |
| Profile sync/cloud browser | SiteOps browser profile references are opaque | No visible session values; live profile sync not built. |

---

## Phase Placement

Recommended feature family name: **Browser Runtime Harness + Skill Memory**.

Placement:

- **Phase 9:** runtime/operator infrastructure, candidate schema, audit shape, bounded adapter design, redacted candidate inspection, non-mutating promotion preflight, and non-persisting promotion approval-request contract.
- **Phase 10:** Site Skills inspection UI, skill candidate review, workflow replay inspector, browser run evidence viewer, promotion controls.

This keeps browser capability inside the control plane and keeps UI inspection separate from runtime authority.

---

## First Safe Implementation Pass

The first implementation pass should not run Browser Harness or Browser Use.

The 2026-04-30 candidate reconciliation slice now implements storage reconciliation and read-only SiteOps inspection:

- `runtime/browser_skills/candidates.py` scans `03_INPUTS/Browser-Skill-Candidates/` and reports storage reconciliation.
- `chaseos siteops candidates list|show|preflight|request-promotion` exposes redacted candidate summaries.
- `runtime/cli/command_contract.json` and `06_AGENTS/ChaseOS-CLI-Command-Reference.md` include the candidate inspection commands.

Remaining slice:

1. Add or align a non-executing Browser Skill Candidate schema under the chosen SiteOps/BOSL boundary.
2. Extend SiteOps run records with an optional `skill_candidate_summary`.
3. Add a writer that can derive a pending candidate only from existing audited run records.
4. Write all candidate creation activity to Agent Activity.
5. Keep candidates `PROPOSED` until review.
6. Block promotion to Site Skill Cards until a separate approval-gated pass.

Do not include:

- live browser launch,
- CDP daemon,
- Browser Use API,
- Browser Harness install,
- profile sync,
- authenticated sessions,
- webagents.md execution,
- workflow replay execution,
- canonical writeback.

---

## Current Verdict

Browser Harness is a useful reference because it is small and separates CDP control from reusable site skills. ChaseOS should adopt that split, but route it through AOR, Gate, SiteOps, Browser Operator Surface, and Agent Activity.

Current status: **PARTIAL / RESEARCH + READ-ONLY CANDIDATE INSPECTION**. Live Browser Harness/CDP control remains **NOT BUILT**.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
