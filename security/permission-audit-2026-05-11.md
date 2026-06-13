---
type: security-audit
title: ChaseOS Permission Audit — 2026-05-11
version: 1.0
created: 2026-05-11
auditor: security-auditor (ChaseOS agent persona)
scope: routines, agents, connectors, env vars, repo permissions
canonical_source: 06_AGENTS/Permission-Matrix.md
connected_indexes:
  - [[Security-Audits-Index]]
  - [[Agent-Activity-Index]]
---

# ChaseOS Permission Audit — 2026-05-11

> Auditor: security-auditor agent role
> Scope: all active workflows, schedules, connectors, environment references, gate configurations
> Method: static analysis of runtime/workflows/registry/, runtime/schedules/, runtime/policy/, 06_AGENTS/Permission-Matrix.md, Trust-Tiers.md, .claude/settings.json, gateway_allowlists.json, protected_files.yaml
> Default posture applied: least privilege

---

## Audit Inventory

### Schedules inspected (9 total)

| Schedule ID | Enabled | External Side Effects |
|---|---|---|
| sch-operator-today-0700 | true | None (vault read/write only) |
| sch-operator-close-day-1900 | true | None |
| sch-os-hygiene-graph-0300 | **true** | Vault mutations (wikilink repair, daily hubs) |
| sch-strikezone-acquisition-0550 | **true** | **Live API calls: RSS, web scrape, IMAP email, Google, Perplexity, Grok** |
| sch-sbp-strikezone-digest-0600 | false | Discord webhook when enabled |
| sch-archon-watch-every-minute | false | None (bus poll only) |
| sch-hermes-watch-every-minute | false | Anthropic API (LLM synthesis) when enabled |
| sch-openclaw-watch-every-minute | false | None |
| sch-events-watch-every-minute | false | None confirmed |

### Connectors present in runtime/capture/connectors/

| Connector | Active workflow usage | External credential |
|---|---|---|
| cli_connector.py | Yes — chaseos capture | None |
| rss_connector.py | Yes — strikezone_acquisition | None (public feeds) |
| browser_connector.py | Yes — browser_research | None |
| perplexity_connector.py | strikezone_acquisition live acquisitions | PERPLEXITY_API_KEY |
| grok_connector.py | strikezone_acquisition live acquisitions | XAI_API_KEY |
| email_adapter.py (runtime/capture/) | **No active workflow manifest** | email IMAP credentials |
| google_adapter.py (runtime/capture/) | **No active workflow manifest** | GOOGLE_OAUTH_TOKEN |

### Active runtimes

OpenClaw (schedule executor), Hermes (review + research synthesis), Archon (implementation + code/architecture review), Claude Code (direct session).

---

## Risk Findings

### CRITICAL

#### C-1: strikezone_acquisition runs live paid API calls with no approval gate

**What:** `sch-strikezone-acquisition-0550.yaml` — `enabled: true` — fires at 05:50 ET every weekday.

**Risk:** `run_all_live_acquisitions()` calls six adapter categories: AI digest (Perplexity/Grok), RSS, web scrape, email IMAP, Google Docs, Google Drive. If `PERPLEXITY_API_KEY` or `XAI_API_KEY` are set in env, this spends money autonomously on each run with no human approval, cost ceiling, or per-run budget guard.

**Applicable permission:** `gateway_allowlists.json → capture.perplexity` and `capture.grok` both declare `credential_reference_required: true` — this governs how credentials are *referenced in manifests*, not whether a live API call requires operator approval.

**Approval_rule in manifest:** `none`.

**Remediation:**
- Add `approval_rule: operator` to `strikezone_acquisition.yaml` OR enable `shadow_mode: true` until cost profile is validated.
- Add `max_api_calls_per_run` guardrail to `strikezone_acquisition.yaml` sbp_config.
- Confirm which adapters have live credentials set in environment before next run.

---

#### C-2: hermes_watch makes autonomous Anthropic API calls (fail-open on key presence)

**What:** `hermes_review_execute.py` → `_execute_synthesis()` calls `claude-haiku-4-5-20251001` via Anthropic Messages API whenever `ANTHROPIC_API_KEY` is present. Triggered on every claimed review task.

**Risk:** Anthropic API calls are automatically gated on env var presence, not on explicit operator approval per run. If `sch-hermes-watch-every-minute` is enabled (currently `enabled: false`), this is 1440 potential LLM synthesis calls/day, each using the operator's API quota and billing account. The fail-open behavior (skip silently if key absent) inverts the safe default: the unsafe path (live API) is the opt-out, not opt-in.

**Remediation:**
- Change `_execute_synthesis()` to require an explicit `synthesize=true` flag in the workflow manifest input OR an explicit operator enable flag in the schedule.
- Current schedule `enabled: false` mitigates this. Do not enable until remediated.
- Add `max_token_budget` enforcement in the watch loop (currently only in sbp_strikezone_digest).

---

#### C-3: sbp_strikezone_digest can post to external community channel with no draft review

**What:** `sbp_strikezone_digest.yaml` — delivery adapter includes `discord` with `channel_hint: "#strikezone-signals"` and `approval_rule: none`.

**Risk:** When enabled, this sends automated content to an external Discord community server. Content is generated from vault state + acquisition pack. No human reads the draft before it posts. Errors in content generation, stale acquisition data, or workflow bugs publish directly to community members.

**Current state:** `enabled: false` in `sch-sbp-strikezone-digest-0600.yaml`. Risk is latent, not active.

**Remediation:**
- Add `human_in_loop: required` (not `optional`) to guardrail block before enabling the delivery adapter.
- Add a draft approval step: write to `07_LOGS/SBP-Runs/_drafts/` first, require operator approval to promote to delivery.
- Keep `enabled: false` until draft-review gate is implemented.

---

### HIGH

#### H-1: setup_init write target in gateway_allowlists.json is vault-wide

**What:** `gateway_allowlists.json → write_targets.setup_init` includes: `00_HOME/**`, `01_PROJECTS/**`, `02_KNOWLEDGE/**`, `03_INPUTS/**`, `04_SOPS/**`, `05_TEMPLATES/**`, `06_AGENTS/**`, `07_LOGS/**`, `99_ARCHIVE/**`, plus root-level protected files (`README.md`, `PROJECT_FOUNDATION.md`, `ROADMAP.md`, `FORKING.md`, `SOUL.md`).

**Risk:** Any routine granted the `setup_init` write bucket effectively has vault-wide write access, including protected files. The name "setup_init" implies a one-time initialization scope, but there is no time-bound or precondition enforcement. If a workflow incorrectly claims or is granted this target, it bypasses nearly all write restrictions.

**Remediation:**
- Split `setup_init` into: `setup_init_scaffold` (empty folder creation only) and `setup_init_files` (specific known seed files, enumerated explicitly, not glob).
- Remove `SOUL.md` and `00_HOME/Principles.md` from all non-protected write targets in allowlists.
- Consider whether `setup_init` should be disabled after initial vault setup.

---

#### H-2: host.startup_folder permission allows writing OS startup entries

**What:** `gateway_allowlists.json → external_apis.host.startup_folder` allows writes to `%USERPROFILE%/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/` and creation of `gateway.cmd` files for Hermes and OpenClaw.

**Risk:** Writing to the Windows Startup folder creates persistent processes that survive reboots. This is OS-level persistence, not vault-level persistence. If a workflow incorrectly invokes this permission, it can create startup entries that survive session close. No `approval_rule` is stated for this permission in the allowlist.

**Remediation:**
- Add an explicit per-action approval gate for any `host.startup_folder` write.
- Document which specific workflow(s) are permitted to invoke this permission.
- Log all startup folder writes to `07_LOGS/Agent-Activity/` with a `startup_write` tag.

---

#### H-3: Three watch loops scheduled at * * * * * (1440 cycles/day each)

**What:** `sch-archon-watch-every-minute`, `sch-hermes-watch-every-minute`, `sch-openclaw-watch-every-minute` — all cron `* * * * *`. All currently `enabled: false`.

**Risk:** When enabled, each loop runs 1440 times/day. Hermes loops can trigger LLM synthesis (see C-2). Even without synthesis, 1440 bus polls/day per runtime generates significant `07_LOGS/Agent-Activity/` write volume and potential race conditions if multiple runtimes claim the same task. No `max_cycles_per_day` or `rate_limit` guard exists at the schedule level.

**Remediation:**
- Before enabling any `* * * * *` schedule: add `max_cycles_per_day` to the schedule spec.
- Stagger intervals: e.g., archon at `*/2 * * * *`, hermes at `*/3 * * * *`.
- Add `max_token_budget` to hermes_watch manifest before enabling.

---

#### H-4: os_hygiene_graph mutates vault files autonomously (enabled: true)

**What:** `sch-os-hygiene-graph-0300.yaml` — `enabled: true` — fires at 03:00 ET daily. Task type `os-graph-maintenance` with `permission_set: write_vault_graph`. Performs: wikilink repair, daily hub creation, provenance link injection.

**Risk:** This is the only currently-enabled schedule that mutates canonical vault files (not just logs). Automated wikilink repair can silently change file content based on pattern matching. If the graph builder has a bug or reads stale snapshot data, it can corrupt links in knowledge notes.

**Current mitigation:** `strict_review_gate=true` and `allow_review_debt=false` block mutation if review-gated loose nodes exist. This is good. Gap: no explicit rollback mechanism if wikilink repair produces incorrect output.

**Remediation:**
- Add pre-mutation snapshot or backup step.
- Add a diff preview mode that writes proposed changes to a staging file before applying them.
- Log every modified file path and the change made (current: logs run record, not per-file diffs).

---

### MEDIUM

#### M-1: protected_files.yaml not synced since 2026-03-20 — may drift from Permission-Matrix

**What:** `runtime/policy/protected_files.yaml` — header says `# Last synced: 2026-03-20`. `Permission-Matrix.md` was updated 2026-04-25 with Hermes rows, additional constraint tables, and Runtime MCP surface. The hook `protected_write_guard.py` reads from `protected_files.yaml`, not the markdown.

**Risk:** If new protected files were added to Permission-Matrix.md after 2026-03-20 but not to `protected_files.yaml`, the enforcement hook does not guard them. The markdown is policy; the YAML is enforcement. They must match.

**Cross-check:** Current `protected_files.yaml` lists 13 files. Permission-Matrix.md Section 2 also lists 13 files. Superficially matched — but requires explicit line-by-line verification against the 2026-04-25 update.

**Remediation:**
- Verify line-by-line match between `protected_files.yaml` and Permission-Matrix.md Section 2.
- Update `# Last synced:` date.
- Add a CI-style consistency check (e.g., `chaseos doctor` verifies sync).

---

#### M-2: Email IMAP and Google adapters are built but have no workflow scope

**What:** `email_adapter.py` (runtime/capture/) and `google_adapter.py` (runtime/capture/) are built and documented as Phase 9 Pass 2 deliverables. No active workflow manifest declares them in `required_reads` or `input_adapters`.

**Risk:** These adapters have broad credential access (IMAP mailbox, Google OAuth). They exist in the codebase and can be called via `run_all_live_acquisitions()` which is invoked by `strikezone_acquisition`. If email or Google credentials are present in env, live acquisitions will silently call them.

**Remediation:**
- Confirm whether `GOOGLE_OAUTH_TOKEN` and email IMAP credentials are currently set in environment.
- If not needed for active workflows: remove from `run_all_live_acquisitions()` call or add per-adapter enabled flags.
- Add per-adapter `enabled: true/false` guard in `strikezone_acquisition.yaml` input_adapters.

---

#### M-3: Shadow-mode test workflows in active registry

**What:** Registry contains: `hermes_operator_today_shadow.yaml`, `openai_operator_research_shadow.yaml`, `developer_repo_explain_shadow.yaml`. These are shadow/pilot workflows with `trigger_type: manual` but no clear decommission path.

**Risk:** Shadow workflows are not executable by schedule, but they are registered in the active workflow registry and can be invoked via `chaseos run`. Their presence increases the attack surface and creates ambiguity about which workflows are production vs. experimental.

**Remediation:**
- Archive inactive shadow workflows to `runtime/workflows/archive/` or mark `status: deprecated`.
- Confirm which, if any, are still being actively used.

---

#### M-4: approval_rule: none on all active external-touching workflows

**What:** `strikezone_acquisition`, `sbp_strikezone_digest`, `hermes_watch`, and `archon_watch` all declare `approval_rule: none`.

**Risk:** `approval_rule: none` is appropriate for log-only or vault-local workflows. For workflows with external side effects (API calls, Discord delivery), it means zero human checkpoints between schedule trigger and external action.

**Remediation:**
- Differentiate `approval_rule: none` (truly local, no external effects) from `approval_rule: operator-first-run` (requires operator approval on first execution of a new schedule or new API target).
- Apply `operator-first-run` to any workflow that calls an external API or delivers to an external channel.

---

#### M-5: No explicit git/branch-push permission documented

**What:** The Permission-Matrix.md covers read, create, edit, delete, execute, network. There is no row for git operations (commit, push, branch creation, force-push).

**Risk:** Absence of an explicit prohibition is not equivalent to prohibition. If a workflow gains shell execution capability, git operations are not documented as out-of-scope.

**Remediation:**
- Add a `Git operations` row to Permission-Matrix.md Section 1 with all surfaces marked `❌` except Claude Code (⚠️ — explicit instruction required per operation, no force-push to main).

---

### LOW

#### L-1: _schema.yaml and _sbp_base_template.yaml protected only by naming convention

**What:** Files prefixed `_` in `runtime/workflows/registry/` are excluded from execution by the convention "loader rejects `_*` filenames with schema_file error." This is convention-based, not enforced by a separate file type or access control.

**Risk:** Low — convention is documented and the loader enforces it. But if a new loader or CLI path bypasses this check, a `_schema.yaml` could be loaded as a workflow.

**Remediation:** Add an explicit `is_template: true` or `is_schema: true` flag to these files' frontmatter and enforce the check in the loader rather than relying only on filename prefix.

---

#### L-2: ventureops-runtime-audit approval chain uses unvalidated actor string

**What:** `agent_runtime_governance_audit.yaml` accepts `approval_decision_actor` as a string input. The actor identity is not verified against a registered identity in the system.

**Risk:** A spoofed actor name could be passed to consume an approval token without a legitimate human decision.

**Remediation:** Validate `approval_decision_actor` against registered operators in the identity ledger before consuming an approval.

---

#### L-3: Credential reference enforcement is self-attesting

**What:** `gateway_allowlists.json → credential_references` defines what credential formats are allowed in manifest state. Enforcement relies on manifests following the convention voluntarily — there is no scanner that rejects manifests with hardcoded secret values.

**Risk:** A manifest author (or AI agent editing a manifest) could accidentally commit an actual webhook URL or API key value rather than an env var reference.

**Remediation:**
- Add a pre-commit or `chaseos doctor` scan that checks all `*.yaml` files in `runtime/` for patterns matching `secret_value_key_fragments` (api_key, token, webhook, etc.) and warns on apparent literal secret values.

---

## Summary Table

| ID | Risk | Category | Enabled Now? | Remediation Priority |
|----|------|----------|-------------|---------------------|
| C-1 | strikezone_acquisition live API calls, no approval gate | Financial / External | **YES** | Immediate |
| C-2 | hermes_watch autonomous Anthropic API calls (fail-open) | Financial / Autonomy | No (disabled) | Before enabling |
| C-3 | sbp_strikezone_digest community Discord publish, no draft review | Community / External | No (disabled) | Before enabling |
| H-1 | setup_init write target is vault-wide | Permission scope | Latent | High |
| H-2 | host.startup_folder allows OS startup persistence | OS integrity | Latent | High |
| H-3 | Watch loops at * * * * * (1440/day), no rate guard | Resource / Cost | No (disabled) | Before enabling |
| H-4 | os_hygiene_graph autonomous vault mutations (enabled) | Data integrity | **YES** | Improve safeguards |
| M-1 | protected_files.yaml not synced since 2026-03-20 | Enforcement drift | Latent | Next session |
| M-2 | Email IMAP + Google adapters unscoped, no active manifest | Credential exposure | Latent | Medium |
| M-3 | Shadow workflows in active registry without decommission path | Attack surface | Latent | Medium |
| M-4 | approval_rule: none on all external-touching workflows | Governance gap | YES (acq.) | Medium |
| M-5 | No git/branch-push permission row in Permission-Matrix | Documentation gap | Latent | Medium |
| L-1 | _schema protection by naming convention only | Loader safety | Latent | Low |
| L-2 | ventureops approval actor unvalidated | Auth bypass | Latent | Low |
| L-3 | Credential reference enforcement is self-attesting | Secret leakage | Latent | Low |

---

## Unnecessary Connectors

| Connector | Status | Recommendation |
|---|---|---|
| email_adapter.py | Built, no active workflow manifest | Disable in run_all_live_acquisitions() until explicitly scoped |
| google_adapter.py | Built, no active workflow manifest | Disable in run_all_live_acquisitions() until explicitly scoped |
| grok_connector.py | Active via strikezone_acquisition | Confirm XAI_API_KEY not set unless operator has reviewed cost profile |
| perplexity_connector.py | Active via strikezone_acquisition | Confirm PERPLEXITY_API_KEY not set unless operator has reviewed cost profile |

---

## Permissions to Reduce

1. `setup_init` write target — narrow from vault-wide glob to specific initialization file set.
2. `host.startup_folder` — add per-action approval gate.
3. `strikezone_acquisition` — add `approval_rule: operator-first-run` or `shadow_mode: true`.
4. Hermes LLM synthesis — change from env-var-presence gating to explicit operator flag.

---

## Workflows Requiring Human Approval Gate

| Workflow | Current approval_rule | External action | Recommended gate |
|---|---|---|---|
| strikezone_acquisition | none | Live paid API calls | operator-first-run |
| sbp_strikezone_digest | none | Community Discord post | draft-review required |
| Any workflow using delivery.whop_api | (not yet active) | Whop community post | operator-per-run |
| hermes_watch (when LLM synthesis enabled) | none | Anthropic API | explicit-enable flag |

---

## Outputs That Should Be Draft-Only

1. **sbp_strikezone_digest Discord delivery** — write to `07_LOGS/SBP-Runs/_drafts/` first; require operator approval to promote to live delivery.
2. **hermes_review_execute LLM synthesis block** — currently appended to audit record automatically. Should be labeled `[SYNTHESIS — UNREVIEWED]` until operator marks it reviewed.
3. **strikezone_acquisition briefing_ready_input_set** — output of live API calls. Should be flagged as draft until operator confirms acquisition quality.

---

## Next Actions (Recommended Order)

1. Check `PERPLEXITY_API_KEY`, `XAI_API_KEY`, `GOOGLE_OAUTH_TOKEN`, and IMAP credentials — are any set in the current env? (C-1, M-2)
2. Set `strikezone_acquisition` to `shadow_mode: true` in schedule until approval gate is added. (C-1)
3. Add `max_token_budget` and `synthesize: requires_explicit_flag` to `hermes_watch` before enabling. (C-2)
4. Add `human_in_loop: required` to `sbp_strikezone_digest` before enabling digest delivery. (C-3)
5. Narrow `setup_init` write target in `gateway_allowlists.json`. (H-1)
6. Verify `protected_files.yaml` sync against current Permission-Matrix.md. (M-1)
7. Add git operations row to Permission-Matrix.md. (M-5)
8. Archive or deprecate shadow-mode test workflows in registry. (M-3)

---

*security/permission-audit-2026-05-11.md — ChaseOS security-auditor agent | Created: 2026-05-11 | Scope: static analysis of runtime, schedules, connectors, policy, gate config*
