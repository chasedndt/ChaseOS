---
type: hardening-passover
title: ChaseOS Phase 9 (and Previous) — Hardening Passover Document
version: 1.0-superseded
created: 2026-05-11
superseded_by: 06_AGENTS/ChaseOS-Hardening-Passover.md
---

# ChaseOS Phase 9 Hardening Passover — SUPERSEDED

> **This document has been superseded.**
> The complete all-phase hardening register (Phase 1–9) is at:
> `06_AGENTS/ChaseOS-Hardening-Passover.md`
>
> That document covers all items from this file plus Phase 4/5 Gate hook hardening,
> Phase 8 connector/capture hardening, and an explicit AUTONOMOUS vs REQUIRES-OPERATOR-INPUT
> classification on every item. Use that document for all hardening work.

---

*Original content preserved below for reference. Do not act on this file — use the superseding document.*

---

> This document is a handover reference for all ChaseOS agents and runtimes.
> It is a static snapshot of open hardening items as of 2026-05-11.
> Canonical permission policy lives in `06_AGENTS/Permission-Matrix.md`.
> Runtime enforcement state lives in `kernel/PERMISSION_MATRIX.md`.
> Security audit findings live in `security/permission-audit-2026-05-11.md`.
>
> **When reading this document:** Items marked `ACTIONABLE NOW` can be implemented
> in a focused hardening pass without blocking deferred architecture work.
> Items marked `DEFERRED` require new architecture or are blocked by Phase 9+ scope.
> Items marked `VERIFIED-MATCH` or `PARTIAL-ADDRESSED` have been checked against
> the live repository state as of 2026-05-11.

---

## How to Use This Document

- **Archon (Claude Code):** Use this as the routing anchor for any hardening or security pass. Do not re-derive findings — read this first.
- **Hermes:** Do not act on findings autonomously. Escalate implementation decisions to operator. Use as context for review tasks.
- **OpenClaw:** Before enabling any disabled schedule, check this document for associated CRITICAL or HIGH findings.
- **Any new runtime or agent:** Read `kernel/PERMISSION_MATRIX.md` alongside this for the current permission state.

---

## Phase 10/11 Overlap Verification

The following "deferred" items were checked against the live Phase 10/11 repository state on 2026-05-11:

| Item | Deferred Status | Phase 10/11 Overlap Confirmed? |
|------|----------------|-------------------------------|
| D-1 Automated context routing engine | `runtime/context/boot.py` exists (Context Boot Protocol) but routing engine is not built | No overlap — boot protocol ≠ routing engine |
| D-2 Multi-repo policy enforcement | Schema defined; runtime enforcement absent | No overlap — Phase 10/11 does not address multi-repo |
| D-3 `runtime/audit/` migration | Directory does not exist in repository | No overlap — confirmed absent |
| D-4 ChaseOS-native cron runner | OpenClaw remains sole executor; `runtime/schedules/` intent files exist | No overlap — Phase 10/11 does not add native runner |
| D-5 `chaseos doctor` protected_files sync check | `doctor` command exists but does NOT check `protected_files.yaml` sync | No overlap — gap confirmed; simple to add |
| D-6 Per-adapter enabled flags in strikezone_acquisition | Not present in manifest or handler | No overlap — straightforward manifest change |
| D-7 Coordination-watch activation proof | Watch loop handlers exist and are registered; no formal round-trip proof | No overlap — proof not produced in Phase 10/11 |
| D-8 Research-pack SBP verification with real files | No evidence of verified test with real local files | No overlap |
| H-2 host.startup_folder approval gate | Phase 10 Pass 10AC surfaces 12 requestable startup-surface approval requests; Studio blocks lifecycle actions | **PARTIAL ADDRESSED** — Studio surface requires approval requests, but `gateway_allowlists.json` has no `approval_gate` documentation for the `host.startup_folder` entry |

**Net result:** D-5, D-6 are straightforward and can be promoted to ACTIONABLE. D-1, D-2, D-3, D-4, D-7, D-8 remain genuinely deferred. H-2 is partially addressed by Phase 10 Studio but still has a gap in `gateway_allowlists.json`.

---

## Protected Files Sync Verification

Verified 2026-05-11 by reading both files directly:

`runtime/policy/protected_files.yaml` (13 entries) **exactly matches** `06_AGENTS/Permission-Matrix.md` Section 2 (13 entries). All file paths are identical. The sync date comment (`# Last synced: 2026-03-20`) is stale but the content is accurate.

**Action required:** Update `# Last synced:` date to `2026-05-11` to close M-1.

---

## Synthesis Fix: C-2 Already Has a Path

`runtime/workflows/hermes_review_execute.py` line 28 documents `synthesize` as an optional bool (default: `True`). Line 40 of `runtime/workflows/registry/hermes_watch.yaml` lists it as an optional input. The handler already supports `synthesize=False`.

**The fix for C-2 is a manifest change only:** Set `synthesize: false` as the default input in `hermes_watch.yaml`, requiring the operator to explicitly pass `synthesize: true` to enable LLM synthesis. No code change needed.

---

## SBP Discord Status: Partial Guard Exists

`runtime/workflows/registry/sbp_strikezone_digest.yaml` currently declares `human_in_loop: optional`.

**The fix for C-3 is a manifest change only:** Change `human_in_loop: optional` → `human_in_loop: required`. The guardrail infrastructure for this flag already exists in `runtime/sbp/guardrail.py`.

---

## All Hardening Items — Master Register

### CRITICAL — Active Risk

---

#### C-1 | `strikezone_acquisition` — Live paid API calls with no approval gate
**Status:** `ACTIONABLE NOW`
**Files to change:**
- `runtime/schedules/sch-strikezone-acquisition-0550.yaml` — change `shadow_mode: false` → `shadow_mode: true`
- `runtime/workflows/registry/strikezone_acquisition.yaml` — change `approval_rule: none` → `approval_rule: operator-first-run`
- Optional (longer fix): add per-adapter `enabled` flags in the acquisition plan JSON at `runtime/acquisition/plans/strikezone-daily.json`

**What it does:** `sch-strikezone-acquisition-0550` is `enabled: true` and fires every weekday at 05:50 ET. `run_all_live_acquisitions()` calls six adapter categories including Perplexity API, Grok/xAI API, IMAP email, and Google. If `PERPLEXITY_API_KEY` or `XAI_API_KEY` are set in env, this spends money autonomously with no human approval, cost ceiling, or per-run budget guard.

**Linked feature:** Phase 9 Acquisition Pass 2B (2026-04-27), Phase 8 Perplexity connector (Pass 8), Phase 8 Grok connector (Pass 10).

**Immediate action:** Confirm `PERPLEXITY_API_KEY` and `XAI_API_KEY` are NOT set in env. If either is set, disable the schedule immediately with `chaseos schedule disable sch-strikezone-acquisition-0550`.

---

#### C-2 | `hermes_watch` — Autonomous Anthropic API calls (fail-open on key presence)
**Status:** `ACTIONABLE NOW` — manifest change only, no code required
**Files to change:**
- `runtime/workflows/registry/hermes_watch.yaml` — add `synthesize: false` to `default_inputs` block (or equivalent input default section)

**What it does:** `hermes_review_execute._execute_synthesis()` calls `claude-haiku-4-5-20251001` automatically whenever `ANTHROPIC_API_KEY` is present in env. `hermes_watch` schedule is currently `enabled: false`, but if enabled at `* * * * *` this could trigger up to 1440 LLM synthesis calls/day.

**The code already supports this:** `synthesize` is an optional bool input (default `True`). Changing the manifest default to `false` makes LLM synthesis opt-in per run.

**Linked feature:** Phase 9 Hermes Watch Loop + LLM Synthesis (2026-04-26), Agent Bus coordination.

**Do not enable `sch-hermes-watch-every-minute` until this is resolved.**

---

#### C-3 | `sbp_strikezone_digest` — Discord delivery with no draft review gate
**Status:** `ACTIONABLE NOW` — manifest change only, no code required
**Files to change:**
- `runtime/workflows/registry/sbp_strikezone_digest.yaml` — change `human_in_loop: optional` → `human_in_loop: required`

**What it does:** When enabled, the SBP pipeline posts to the StrikeZone Discord community channel `#strikezone-signals` with no human review of the draft content. Content is generated from vault state + acquisition pack. If the acquisition has a bug or produces stale/incorrect data, it publishes directly to community members.

**Current state:** `sch-sbp-strikezone-digest-0600.yaml` is `enabled: false`. Risk is latent but one config flip away from active.

**Linked feature:** Phase 9 SBP Pass 1D Discord Delivery (2026-04-27), Phase 9 SBP substrate.

**Do not enable `sch-sbp-strikezone-digest-0600` until this is resolved.**

---

### HIGH — Latent Risk (becomes critical on enable or misconfiguration)

---

#### H-1 | `setup_init` write target in `gateway_allowlists.json` is vault-wide
**Status:** `ACTIONABLE NOW`
**Files to change:**
- `runtime/policy/gateway_allowlists.json` — split `setup_init` into two narrower buckets

**What it does:** `gateway_allowlists.json → write_targets.setup_init` currently covers `00_HOME/**`, `01_PROJECTS/**`, `02_KNOWLEDGE/**`, `03_INPUTS/**`, `04_SOPS/**`, `05_TEMPLATES/**`, `06_AGENTS/**`, `07_LOGS/**`, `99_ARCHIVE/**`, `runtime/bindings/**`, `runtime/lifecycle/**`, `runtime/policy/**`, `runtime/schedules/**`, plus root-level protected files including `SOUL.md`, `README.md`, `PROJECT_FOUNDATION.md`, `ROADMAP.md`, and `FORKING.md`.

Any workflow granted the `setup_init` write bucket effectively has vault-wide write access. The name implies one-time initialization scope, but there is no time-bound or precondition enforcement.

**Recommended fix:** Split into:
- `setup_init_scaffold` — empty folder creation only, no file writes
- `setup_init_seed_files` — explicit enumerated list of specific known seed files (no globs, no protected files)

Remove `SOUL.md`, `00_HOME/Principles.md`, and all other protected files from `setup_init` entirely.

**Linked feature:** Phase 4/5 ChaseOS Gate, `runtime/policy/gateway_allowlists.json`.

---

#### H-2 | `host.startup_folder` — No per-action approval gate documented
**Status:** `PARTIAL-ADDRESSED — ACTIONABLE NOW (documentation gap only)`
**Files to change:**
- `runtime/policy/gateway_allowlists.json` — add `approval_gate: operator` field to `host.startup_folder` entry

**Current state:** Phase 10 Pass 10AC (`runtime/studio/runtime_cockpit_action_readiness.py`) surfaces startup-surface actions as approval-gated in the Studio UI. The Studio correctly requires approval requests for any startup-surface action. However, the underlying `gateway_allowlists.json` entry for `host.startup_folder` has no `approval_gate` field — it relies entirely on the Studio surface being the only code path.

**Remaining gap:** If a workflow or runtime bypasses Studio and calls the host.startup_folder permission directly, there is no policy-layer gate. All startup folder writes should require a logged approval artifact before execution.

**Linked feature:** Phase 9 Runtime Lifecycle, Phase 10 Pass 10AC (`runtime/studio/runtime_cockpit_action_readiness.py`).

---

#### H-3 | Watch loops scheduled at `* * * * *` — No rate guard
**Status:** `ACTIONABLE NOW` — schedule YAML changes only
**Files to change:**
- `runtime/schedules/sch-archon-watch-every-minute.yaml` — add `max_cycles_per_day: 480` (every 3 minutes equivalent)
- `runtime/schedules/sch-hermes-watch-every-minute.yaml` — add `max_cycles_per_day: 480`; stagger to `*/3 * * * *`
- `runtime/schedules/sch-openclaw-watch-every-minute.yaml` — add `max_cycles_per_day: 720` (every 2 minutes equivalent)
- `runtime/aor/engine.py` — add enforcement logic for `max_cycles_per_day` from schedule config

**What it does:** All three watch loop schedules are `* * * * *` (1440/day). All are currently `enabled: false`, but the rate guard must exist before any are enabled. Hermes loops trigger LLM synthesis per cycle if `ANTHROPIC_API_KEY` is set and `synthesize` default is not changed (see C-2). 1440 cycles × Anthropic API = significant cost exposure.

**Linked feature:** Phase 9 Agent Bus (2026-04-25–27), Phase 9 Hermes Watch Loop, Phase 9 OpenClaw Watch Loop, Phase 9 Archon identity (2026-04-30).

**Do not enable any `* * * * *` schedule until `max_cycles_per_day` enforcement is added.**

---

#### H-4 | `os_hygiene_graph` — Autonomous vault mutations with no pre-mutation snapshot
**Status:** `ACTIONABLE NOW`
**Files to change:**
- `runtime/workflows/os_hygiene_graph.py` — add pre-mutation snapshot step before wikilink repair writes
- `runtime/workflows/os_hygiene_graph.py` — add per-file diff log (file path + before/after hash) to audit record

**What it does:** `sch-os-hygiene-graph-0300.yaml` is `enabled: true` and fires at 03:00 ET daily. It is currently the only enabled schedule that mutates canonical vault files beyond logs. It performs wikilink repair, daily hub creation, and provenance link injection. If the graph builder reads stale snapshot data or has a bug, link corruption is silent and rollback requires manual inspection.

**Existing mitigation:** `strict_review_gate=true` and `allow_review_debt=false` block mutation if loose nodes exist. This is good but insufficient — a pre-mutation snapshot and per-file change log are also needed.

**Linked feature:** Phase 9 AOR (graph_hygiene workflow), Phase 7 SIC graph builder.

---

### MEDIUM — Structural Gaps

---

#### M-1 | `protected_files.yaml` sync date stale
**Status:** `ACTIONABLE NOW — trivial`
**Repository verification:** File contents match `06_AGENTS/Permission-Matrix.md` Section 2 exactly (13 files, all paths identical). Only the header comment is outdated.
**Files to change:**
- `runtime/policy/protected_files.yaml` — update `# Last synced: 2026-03-20` → `# Last synced: 2026-05-11`

**Linked feature:** Phase 4/5 Gate hooks (`protected_write_guard.py`).

---

#### M-2 | Email IMAP + Google adapters built but unscoped — silently activated by `run_all_live_acquisitions()`
**Status:** `ACTIONABLE NOW`
**Files to change:**
- `runtime/acquisition/strikezone_acquisition.py` — confirm whether `run_all_live_acquisitions()` is called here and add per-category `enabled` guard flags
- `runtime/acquisition/plans/strikezone-daily.json` (or equivalent plan) — add `email_enabled: false` and `google_enabled: false` fields
- `runtime/acquisition/adapters/email_adapter.py` — add `enabled` check at top of `run_email_acquisitions()`
- `runtime/acquisition/adapters/google_adapter.py` — same

**What it does:** `email_adapter.py` and `google_adapter.py` exist under `runtime/acquisition/adapters/`. They are called through `run_all_live_acquisitions()`. If `GOOGLE_OAUTH_TOKEN` or IMAP credentials are set in env, they run silently on every acquisition cycle with no manifest declaring them in scope.

**Linked feature:** Phase 9 Acquisition Pass 2B (2026-04-27).

**Immediate action:** Confirm `GOOGLE_OAUTH_TOKEN` and IMAP credentials are NOT set in env.

---

#### M-3 | Shadow workflows in active registry without deprecation path
**Status:** `ACTIONABLE NOW — trivial`
**Files to change (or move):**
- `runtime/workflows/registry/hermes_operator_today_shadow.yaml` — mark `status: deprecated` or move to `runtime/workflows/registry/archive/`
- `runtime/workflows/registry/openai_operator_research_shadow.yaml` — same
- `runtime/workflows/registry/developer_repo_explain_shadow.yaml` — same

**What it does:** These three shadow/pilot workflows are registered in the active workflow registry and are invokable via `chaseos run`. Their presence increases the effective attack surface. No decommission policy exists for them.

**Linked feature:** Phase 9 AOR workflow registry (`runtime/workflows/registry/`).

---

#### M-4 | `approval_rule: none` on all external-touching workflows
**Status:** `ACTIONABLE NOW (policy documentation + 2 manifest changes)`
**Files to change:**
- `runtime/workflows/registry/strikezone_acquisition.yaml` — change to `approval_rule: operator-first-run` (covered by C-1)
- `runtime/workflows/registry/sbp_strikezone_digest.yaml` — add draft-review posture (covered by C-3)
- `06_AGENTS/Permission-Matrix.md` — add `approval_rule` taxonomy section defining: `none` (local-only, no external effects), `operator-first-run` (external API or delivery target), `operator-per-run` (community/public-facing posts)
- `runtime/workflows/registry/hermes_watch.yaml` — document that `approval_rule: none` applies because external effects (Anthropic API) are gated by `synthesize` flag, not by schedule-level approval

**What it does:** `approval_rule: none` is appropriate for log-only or vault-local workflows. For workflows with external side effects (paid API calls, Discord delivery), it means zero human checkpoints. No formal taxonomy distinguishes between the two cases.

**Linked feature:** Phase 9 AOR manifest schema, all four external-touching workflow manifests.

---

#### M-5 | No git operations row in `Permission-Matrix.md`
**Status:** `ACTIONABLE NOW — documentation only`
**Files to change:**
- `06_AGENTS/Permission-Matrix.md` — add `Git operations` row to Section 1 permission table

**Recommended entry:**
```
| Git (commit, push, branch, force-push) | ⚠️ Explicit per-operation instruction | ❌ | ❌ | ❌ | ❌ | ❌ |
```
Note: Force-push to main is `❌ Prohibited` for all runtimes. Claude Code (Archon) may commit/push only with explicit per-operation user instruction.

**Linked feature:** Phase 4 Agent Control + Security Plane, `06_AGENTS/Permission-Matrix.md`.

---

#### M-6 | MCP V1 — No live integration hardening for real client deployment
**Status:** `DEFERRED — Phase 9 active feature, hardening requires external client test setup`
**Current state:** `runtime/mcp/` V1 stdio scaffold is built and hardened (Pass 5A, 44 tests). No live deployment with Claude Desktop or external MCP client has been tested. Trust boundary extension is untested under real conditions.
**When to address:** Before any production MCP endpoint is exposed to external clients.
**Linked feature:** Phase 9 Runtime MCP Pass 5A (2026-04-20), `06_AGENTS/ChaseOS-MCP-Server.md`.

---

#### M-7 | Pulse Pipeline Runner — Single `operator_approved` flag with no per-step fidelity
**Status:** `DEFERRED — low operational risk while Pulse is in dry-run default`
**Current state:** `runtime/pulse/pipeline_runner.py` uses `dry_run=True` as default. `operator_approved` sets all 4 evidence flags simultaneously. No independent per-step validation.
**When to address:** Before Pulse pipeline is activated for live enqueue runs.
**Linked feature:** Phase 9 Pulse Pipeline Runner (2026-04-30), `runtime/pulse/pipeline_runner.py`.

---

### LOW — Convention-Only Enforcement / Minor Structural

---

#### L-1 | `_schema.yaml` and `_sbp_base_template.yaml` — Convention-only exclusion
**Status:** `DEFERRED — low risk while loader convention is maintained`
**Recommended fix:** Add `is_template: true` frontmatter field to both files and add a type-check assertion in `runtime/aor/registry.py` loader alongside the filename-prefix check.
**Linked feature:** Phase 9 AOR loader (`runtime/aor/registry.py`), Phase 9 SBP substrate.

---

#### L-2 | VentureOps approval actor — Unvalidated string
**Status:** `DEFERRED — only affects VentureOps synthetic client proofs currently`
**Recommended fix:** Validate `approval_decision_actor` against registered operators in `runtime/memory/adapters/*/identity-ledger.json` before consuming an approval token.
**Linked feature:** Phase 9 VentureOps AOR workflow (`runtime/workflows/agent_runtime_governance_audit.py`).

---

#### L-3 | Credential reference enforcement — Self-attesting only
**Status:** `ACTIONABLE NOW (add to `chaseos doctor`)`
**Files to change:**
- `runtime/cli/main.py` — add a `doctor` check that scans all `*.yaml` files under `runtime/` for patterns matching literal secret value fragments (e.g., `api_key:`, `token:`, `webhook:` followed by a non-`$env`/non-`env_var` value)

**What it does:** `gateway_allowlists.json` requires credentials to be env-var references only, but there is no scanner that rejects manifests containing hardcoded secret values. An AI agent editing a manifest could accidentally commit an actual webhook URL or API key.

**Linked feature:** Phase 9 Gate policy, all connector manifests.

---

### Deferred Architecture Items (Phase 9)

Items confirmed deferred in Phase 10/11 repository — no overlapping work found.

| ID | Item | Why Deferred | When to Address |
|----|------|-------------|-----------------|
| D-1 | Automated context routing engine | New architectural layer; no current use case forcing it | Phase 10 or Phase 12 context management work |
| D-2 | Multi-repo policy enforcement | No multi-repo use case; schema defined only | When second vault instance is created |
| D-3 | `runtime/audit/` migration | Directory does not exist; migration target undefined | Before any cross-session audit query tooling is built |
| D-4 | ChaseOS-native cron runner | OpenClaw is the executor; native runner requires OS-level daemon work | Phase 10/11 lifecycle work |
| D-5 | `chaseos doctor` protected_files sync check | `doctor` exists but does not check YAML/markdown sync | Promote to ACTIONABLE; simple to add alongside L-3 |
| D-7 | Coordination-watch activation proof | Watch loops registered; formal round-trip proof not produced | Before enabling any watch loop schedule |
| D-8 | Research-pack SBP verification with real local files | No evidence in repository | Before enabling `sbp_strikezone_digest` schedule |

**Note on D-5:** Confirmed as a straightforward `doctor` extension — add a check that reads `runtime/policy/protected_files.yaml` and `06_AGENTS/Permission-Matrix.md` Section 2 and asserts they match. Can be done in the same pass as L-3.

---

## Priority Sequence — Recommended Implementation Order

For a focused hardening sprint, implement in this order:

### Sprint 1 — Immediate (can be done in one session)

1. **Check env vars first** — Confirm `PERPLEXITY_API_KEY`, `XAI_API_KEY`, `GOOGLE_OAUTH_TOKEN`, IMAP credentials are not set. If any are set, disable `sch-strikezone-acquisition-0550` before proceeding.
2. **C-2 manifest fix** — Add `synthesize: false` default to `hermes_watch.yaml`. (1 file, 2 lines)
3. **C-3 manifest fix** — Change `human_in_loop: optional` → `required` in `sbp_strikezone_digest.yaml`. (1 file, 1 line)
4. **M-1 sync date** — Update `protected_files.yaml` header. (1 file, 1 line)
5. **M-3 shadow archives** — Add `status: deprecated` to three shadow workflow YAMLs. (3 files)
6. **M-5 git row** — Add git operations row to `Permission-Matrix.md`. (1 file)

### Sprint 2 — Structural (moderate session)

7. **C-1 approval gate** — Add `shadow_mode: true` to `sch-strikezone-acquisition-0550.yaml` + change `approval_rule` on manifest.
8. **H-3 rate guards** — Add `max_cycles_per_day` to three watch loop schedule YAMLs + enforcement logic in AOR engine.
9. **M-2 adapter gating** — Add `email_enabled: false`, `google_enabled: false` flags to acquisition plan and adapter calls.
10. **M-4 approval_rule taxonomy** — Document taxonomy in `Permission-Matrix.md`.
11. **L-3 + D-5** — Add `chaseos doctor` credential scan + protected_files sync check in one `doctor` extension pass.

### Sprint 3 — Architecture (larger scope)

12. **H-1 setup_init split** — Narrow `gateway_allowlists.json` write target.
13. **H-2 startup_folder gate** — Add `approval_gate: operator` documentation to `gateway_allowlists.json` entry.
14. **H-4 os_hygiene_graph snapshot** — Add pre-mutation snapshot and per-file diff log to graph hygiene workflow.

### Sprint 4 — Deferred (requires architecture or external test setup)

15. D-7 coordination-watch activation proof
16. D-8 research-pack SBP verification
17. M-6 MCP live integration hardening
18. M-7 Pulse per-step approval fidelity
19. L-1 template type-check assertion
20. L-2 VentureOps actor validation

---

## Open Actions Requiring Operator Decision

These items require a human decision before implementation can proceed:

1. **C-1:** Should `strikezone_acquisition` use `shadow_mode: true` (dry-run, no real API calls) OR `approval_rule: operator-first-run` (requires operator sign-off before each new acquisition target)? Both are valid; shadow mode is faster to implement.
2. **H-3:** What are the acceptable `max_cycles_per_day` values for each watch loop? Suggested: Archon=480 (every 3 min), Hermes=288 (every 5 min), OpenClaw=720 (every 2 min).
3. **M-2:** Are `GOOGLE_OAUTH_TOKEN` and IMAP credentials currently configured in env? If yes, the email/Google adapters are already running silently.

---

## File Manifest — All Files Requiring Changes

| File | Changes Required | Priority |
|------|-----------------|---------|
| `runtime/schedules/sch-strikezone-acquisition-0550.yaml` | `shadow_mode: true` | C-1 |
| `runtime/workflows/registry/strikezone_acquisition.yaml` | `approval_rule: operator-first-run` | C-1/M-4 |
| `runtime/workflows/registry/hermes_watch.yaml` | `synthesize: false` default input | C-2 |
| `runtime/workflows/registry/sbp_strikezone_digest.yaml` | `human_in_loop: required` | C-3 |
| `runtime/policy/gateway_allowlists.json` | Split `setup_init`; add `approval_gate` to `host.startup_folder` | H-1/H-2 |
| `runtime/policy/protected_files.yaml` | Update sync date | M-1 |
| `runtime/schedules/sch-archon-watch-every-minute.yaml` | Add `max_cycles_per_day` | H-3 |
| `runtime/schedules/sch-hermes-watch-every-minute.yaml` | Add `max_cycles_per_day`; stagger cron | H-3 |
| `runtime/schedules/sch-openclaw-watch-every-minute.yaml` | Add `max_cycles_per_day` | H-3 |
| `runtime/aor/engine.py` | Enforce `max_cycles_per_day` from schedule config | H-3 |
| `runtime/workflows/os_hygiene_graph.py` | Pre-mutation snapshot + per-file diff log | H-4 |
| `runtime/acquisition/strikezone_acquisition.py` | Per-adapter `enabled` guard | M-2 |
| `runtime/acquisition/adapters/email_adapter.py` | `enabled` check at entry | M-2 |
| `runtime/acquisition/adapters/google_adapter.py` | `enabled` check at entry | M-2 |
| `runtime/workflows/registry/hermes_operator_today_shadow.yaml` | `status: deprecated` | M-3 |
| `runtime/workflows/registry/openai_operator_research_shadow.yaml` | `status: deprecated` | M-3 |
| `runtime/workflows/registry/developer_repo_explain_shadow.yaml` | `status: deprecated` | M-3 |
| `06_AGENTS/Permission-Matrix.md` | Add git ops row; add `approval_rule` taxonomy | M-4/M-5 |
| `runtime/cli/main.py` | Add `doctor` credential scan + protected_files sync check | L-3/D-5 |

---

*Phase9-Hardening-Passover.md — ChaseOS hardening handover | Version 1.0 | Created 2026-05-11*
*Source: security/permission-audit-2026-05-11.md + live repository verification 2026-05-11*
*Next update: after Sprint 1 and Sprint 2 completion*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
