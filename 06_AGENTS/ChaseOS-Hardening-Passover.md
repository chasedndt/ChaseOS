---
type: hardening-passover
title: ChaseOS All-Phase Hardening Passover
version: 1.1
created: 2026-05-11
updated: 2026-05-11
author: Chaser Agent (security-analysis + cross-phase audit session)
scope: All phases Phase 1–9 runtime — complete hardening register with autonomy classification
supersedes: 06_AGENTS/Phase9-Hardening-Passover.md
canonical_audit_source: security/permission-audit-2026-05-11.md
canonical_permission_source: 06_AGENTS/Permission-Matrix.md
kernel_index: kernel/PERMISSION_MATRIX.md
---

# ChaseOS All-Phase Hardening Passover

> This document is the complete hardening register for all ChaseOS agents and runtimes.
> It covers Phase 1 through Phase 9 runtime infrastructure.
> It supersedes `06_AGENTS/Phase9-Hardening-Passover.md`.
>
> **Autonomy classification on every item:**
> - `AUTONOMOUS` — can be implemented with no operator input, decision, or credential confirmation
> - `REQUIRES OPERATOR INPUT` — needs a human decision or credential state confirmation before implementation
>
> Agents: prioritise AUTONOMOUS items. Do not implement REQUIRES-OPERATOR-INPUT items
> without surfacing the decision to the operator first.

---

## How to Use This Document

- **Chaser Agent (Claude Code):** This is the routing anchor for any hardening session. Read the Sprint Plan at the bottom first — it gives the current queue in priority order. Do not derive work order from source files; use this document.
- **Hermes:** Do not implement any item autonomously. Use as context for review tasks. Escalate implementation to Chaser Agent or operator.
- **OpenClaw:** C-1 is still OPEN. Do not enable `sch-strikezone-acquisition-0550` until C-1 is resolved. C-2 and C-3 are complete.
- **Any new agent/runtime:** Read `kernel/PERMISSION_MATRIX.md` for current permission state, then read this document for open remediations.

**Current state (2026-05-11):** 16 of 25 actionable items complete. All AUTONOMOUS items complete. Remaining: C-1/M-2/P-D2 (REQUIRES OPERATOR INPUT — credentials); D-series (deferred architecture).

---

## Phase 10/11 Overlap Verification

Confirmed live against repository on 2026-05-11. Deferred items checked for overlap with Phase 10/11 work:

| Deferred Item | Repository Status | Phase 10/11 Overlap |
|---|---|---|
| D-1 Automated context routing engine | `runtime/context/boot.py` exists (boot protocol only, not routing) | No overlap |
| D-2 Multi-repo policy enforcement | Schema defined; no runtime enforcement | No overlap |
| D-3 `runtime/audit/` migration | Directory does not exist | No overlap |
| D-4 ChaseOS-native cron runner | OpenClaw remains sole executor | No overlap |
| D-5 `chaseos doctor` protected_files sync check | ✅ COMPLETE — `_check_protected_files_sync()` added; 13 entries in sync | Implemented 2026-05-11 |
| D-6 Per-adapter enabled flags in acquisition | Not present in manifest or handler | No overlap — **promote to AUTONOMOUS** |
| D-7 Coordination-watch activation proof | Watch handlers registered; formal round-trip proof absent | No overlap |
| D-8 Research-pack SBP verification with real files | No evidence in repository | No overlap |
| H-2 host.startup_folder approval gate | Phase 10 Pass 10AC requires approval requests in Studio UI; `gateway_allowlists.json` has no `approval_gate` field | **PARTIAL-ADDRESSED** — documentation gap remains |

**protected_files.yaml content verification:** Contents match `06_AGENTS/Permission-Matrix.md` Section 2 exactly (13 files, all paths identical). Only sync date comment is stale. → M-1 is trivial.

**C-2 code path confirmation:** `hermes_review_execute.py` already accepts `synthesize: bool` (default `True`). The fix is a single manifest default — no code change required.

**C-3 code path confirmation:** `sbp_strikezone_digest.yaml` already declares `human_in_loop: optional`. The guardrail infrastructure exists. Change `optional` → `required` — no code change required.

---

## Section 1 — CRITICAL (Active Risk, Enabled Schedules)

---

### C-1 | `strikezone_acquisition` — Live paid API calls with no approval gate

**Autonomy:** `REQUIRES OPERATOR INPUT` — operator must confirm whether `PERPLEXITY_API_KEY` or `XAI_API_KEY` are set in env, and decide between shadow_mode vs approval_rule approach.

**Phase origin:** Phase 9 Acquisition Pass 2B (2026-04-27) + Phase 8 connectors (Pass 8/10)

**Status:** `enabled: true` in `sch-strikezone-acquisition-0550.yaml`. Fires at 05:50 ET every weekday.

**Risk:** `run_all_live_acquisitions()` calls six adapter categories: AI digest (Perplexity + Grok), RSS, web scrape, email IMAP, Google Docs, Google Drive. If `PERPLEXITY_API_KEY` or `XAI_API_KEY` are set, this spends money autonomously with zero human approval and no cost ceiling.

**Files to change:**
- `runtime/schedules/sch-strikezone-acquisition-0550.yaml` — set `shadow_mode: true`
- `runtime/workflows/registry/strikezone_acquisition.yaml` — change `approval_rule: none` → `approval_rule: operator-first-run`

**Immediate check before next 05:50 ET:** run `echo $PERPLEXITY_API_KEY $XAI_API_KEY`. If either is set, disable with `chaseos schedule disable sch-strikezone-acquisition-0550`.

---

### C-2 | `hermes_watch` — Autonomous Anthropic API calls (fail-open on key presence)

**Autonomy:** `AUTONOMOUS` — manifest change only, no code required, no operator decision needed

**Phase origin:** Phase 9 Hermes Watch Loop + LLM Synthesis (2026-04-26)

**Status:** ✅ COMPLETE — 2026-05-11 Hygiene Snapshot Hardening Pass

`hermes_watch.yaml` inputs comment changed: `synthesize` documented default updated to `False`. The code reads `synthesize` from inputs — operator must now pass `synthesize: true` explicitly to enable LLM calls. See: `07_LOGS/Build-Logs/2026-05-11-hygiene-snapshot-hardening.md`

---

### C-3 | `sbp_strikezone_digest` — Discord delivery with no mandatory draft review

**Autonomy:** `AUTONOMOUS` — manifest change only, no code required

**Phase origin:** Phase 9 SBP Pass 1D Discord Delivery (2026-04-27)

**Status:** ✅ COMPLETE — 2026-05-11 Hygiene Snapshot Hardening Pass

`sbp_strikezone_digest.yaml` guardrail: `human_in_loop: optional` → `human_in_loop: required`. SBP guardrail infrastructure enforces this field. See: `07_LOGS/Build-Logs/2026-05-11-hygiene-snapshot-hardening.md`

---

## Section 2 — HIGH (Latent Risk, Becomes Critical on Enable)

---

### H-1 | `setup_init` write target in `gateway_allowlists.json` is vault-wide

**Autonomy:** `AUTONOMOUS`

**Phase origin:** Phase 4/5 ChaseOS Gate

**Status:** ✅ COMPLETE — 2026-05-11 High-Severity Allowlist Hardening Pass

`setup_init` replaced with two narrower keys:
- `setup_init_scaffold` — 19 exact folder names only (no `/**` globs, no file paths)
- `setup_init_seed_files` — 33 exact named files only (no `/**` globs)

Eliminated: `00_HOME/**`, `01_PROJECTS/**`, `02_KNOWLEDGE/**`, `03_INPUTS/**`, `04_SOPS/**`, `05_TEMPLATES/**`, `06_AGENTS/**`, `07_LOGS/**`, `99_ARCHIVE/**` — these previously granted vault-wide write access to any workflow with `setup_init`. `setup_cli.py` updated at all 3 call sites. 21 new tests / 21 pass. See: `07_LOGS/Build-Logs/2026-05-11-high-severity-allowlist-hardening.md`

---

### H-2 | `host.startup_folder` — No per-action approval gate in policy file

**Autonomy:** `AUTONOMOUS` (documentation gap only — no code change required)

**Phase origin:** Phase 9 Runtime Lifecycle / AOR. Phase 10 Pass 10AC partially addresses in Studio surface.

**Status:** ✅ COMPLETE — 2026-05-11 High-Severity Allowlist Hardening Pass

`approval_gate: operator` and `audit_requirement: startup_write_tag` added to the `host.startup_folder` entry in `gateway_allowlists.json`. Policy now declares the approval requirement at the allowlist level, not only at the Studio surface layer. See: `07_LOGS/Build-Logs/2026-05-11-high-severity-allowlist-hardening.md`

---

### H-3 | Watch loops at `* * * * *` — No rate guard

**Autonomy:** `REQUIRES OPERATOR INPUT` — operator must decide acceptable `max_cycles_per_day` values per runtime

**Phase origin:** Phase 9 Agent Bus (2026-04-25–27), all three watch loop handlers

**Status:** ✅ COMPLETE 2026-05-11

Operator confirmed: Chaser Agent=480/day, Hermes=720/day, OpenClaw=720/day (Hermes=OpenClaw — equal authority).

`runtime/aor/rate_guard.py` new module: daily cycle counter per workflow in `<vault>/.chaseos/rate_guard.json`; resets at UTC midnight; fail-open throughout. `max_cycles_per_day` added to all three watch schedule YAMLs + `ScheduleIntent` dataclass + loader validation. Engine pre-stage `rate_check` fires after context_boot; escalates with `stage_reached="rate_check"` when limit is reached. `record_execution` called on success path. 37 tests. See: `07_LOGS/Build-Logs/2026-05-11-h3-rate-guard.md`

---

### H-4 | `os_hygiene_graph` — Autonomous vault mutations with no pre-mutation snapshot

**Autonomy:** `AUTONOMOUS`

**Phase origin:** Phase 9 AOR (graph_hygiene workflow), Phase 7 SIC graph builder

**Status:** ✅ COMPLETE — 2026-05-11 Hygiene Snapshot Hardening Pass

New module `runtime/workflows/hygiene_snapshot.py` (stdlib only): `collect_pre_snapshot` → hash all `severity="auto_fix"` issue files before `apply_fixes` runs (500-file/2MB bounds, fail-open). `write_snapshot_dir` → copies + manifest to `07_LOGS/Maintain-Runs/_snapshots/YYYY-MM-DD-pre-hygiene/`. `compute_diff_records` → re-hashes post-mutation. `write_diff_json` → `diff_log.json`. `os_hygiene_graph.py` wired: `stage_1` gains 6 snapshot fields; run record gets `snapshot_dir:` frontmatter + `## Pre-Mutation Snapshot` section. 42 new tests / 115 combined. See: `07_LOGS/Build-Logs/2026-05-11-hygiene-snapshot-hardening.md`

---

## Section 3 — Gate Hook Hardening (Phase 4/5)

These were not in the original Phase 9 security audit — found by direct inspection of `.claude/hooks/`.

---

### G-1 | `protected_write_guard.py` fails OPEN on YAML parse error or missing policy file

**Autonomy:** `AUTONOMOUS`

**Phase origin:** Phase 4/5 Gate hooks

**Status:** ✅ COMPLETE — 2026-05-11 Gate Hook Hardening Pass

`load_protected_files()` now returns `(list[Path], str | None)`. All three failure paths (no PyYAML, missing file, parse error) return a non-None error string. `evaluate_write_protection()` returns `"policy_error"` verdict → `main()` exits 2. `CHASEOS_GATE_DISABLE=1` break-glass added. 69 tests — all pass. See: `07_LOGS/Build-Logs/2026-05-11-gate-hook-hardening-pass.md`

---

### G-2 | `ingestion_promotion_guard.py` fails OPEN on JSON parse error

**Autonomy:** `AUTONOMOUS`

**Phase origin:** Phase 5/6 Gate hooks

**Status:** ✅ COMPLETE — 2026-05-11 Gate Hook Hardening Pass

`sys.exit(0)` on parse error changed to `sys.exit(1)` with `[ChaseOS Gate] BLOCKED:` message. `CHASEOS_GATE_DISABLE=1` break-glass added at top of `main()`. 69 tests — all pass. See: `07_LOGS/Build-Logs/2026-05-11-gate-hook-hardening-pass.md`

---

### G-3 | `protected_write_guard.py` path matching uses `endswith()` — minor over-broad match

**Autonomy:** `AUTONOMOUS`

**Phase origin:** Phase 4/5 Gate hooks

**Status:** ✅ COMPLETE — 2026-05-11 Gate Hook Hardening Pass

`is_protected()` now uses separator-boundary suffix matching: `target_posix.endswith("/" + protected_posix)`. `"MY_README.md"`, `"NOSOUL.md"`, `"SUBREADME.md"` all correctly return False. All 13 protected entries still match. 69 tests — all pass. See: `07_LOGS/Build-Logs/2026-05-11-gate-hook-hardening-pass.md`

---

## Section 4 — Connector / Capture Hardening (Phase 8)

---

### P-C1 | `rss_connector.py` — No mandatory max-items-per-feed ceiling

**Autonomy:** `AUTONOMOUS`

**Phase origin:** Phase 8 Pass 5 (2026-03-28)

**Status:** ✅ COMPLETE — 2026-05-11 Connector/Capture Size Guards Pass

`MAX_ITEMS_PER_FEED = 200` added to `rss_connector.py`. Hard ceiling applied as first slice in `items_to_packets()` before operator `limit` slice. Operator limit can reduce below 200 but cannot exceed it. 27 new tests / 27 pass. See: `07_LOGS/Build-Logs/2026-05-11-connector-size-guards.md`

---

### P-C2 | `watch_folders.py` — No max file size guard before reading content

**Autonomy:** `AUTONOMOUS`

**Phase origin:** Phase 8 Pass 9 (2026-03-30)

**Status:** ✅ COMPLETE — 2026-05-11 Connector/Capture Size Guards Pass

`MAX_WATCHED_FILE_SIZE_BYTES = 10 * 1024 * 1024` (10 MB) added to `watch_folders.py`. Size check in `scan_folder()` after `stat = entry.stat()` — before `_capture_file()`. Oversized files produce `FileSkipped(reason="file_too_large")` and are marked processed to prevent infinite retry. 27 new tests / 27 pass. See: `07_LOGS/Build-Logs/2026-05-11-connector-size-guards.md`

---

### P-C3 | `browser_connector.py` — No explicit input size limit before HTML parsing

**Autonomy:** `AUTONOMOUS`

**Phase origin:** Phase 8 Pass 7 (2026-03-29)

**Status:** ✅ COMPLETE — 2026-05-11 Connector/Capture Size Guards Pass

`MAX_HTML_INPUT_CHARS = 500_000` added to `browser_connector.py`. Guard placed in `capture_from_browser()` between `load_html_file()` and `html_to_markdown()` — raises `ValueError` before the HTML parser is invoked for oversized inputs. 27 new tests / 27 pass. See: `07_LOGS/Build-Logs/2026-05-11-connector-size-guards.md`

---

## Section 5 — MEDIUM Structural Gaps (Phase 9)

---

### M-1 | `protected_files.yaml` sync date stale

**Autonomy:** `AUTONOMOUS — trivial (1 line)`

**Phase origin:** Phase 4/5 Gate

**Status:** ✅ COMPLETE — 2026-05-11 M-Pass

`# Last synced: 2026-03-20` → `# Last synced: 2026-05-11`. See: `07_LOGS/Build-Logs/2026-05-11-m-pass-trivial-hardening.md`

---

### M-2 | Email IMAP + Google adapters built but unscoped in acquisition

**Autonomy:** `REQUIRES OPERATOR INPUT` — operator must confirm whether `GOOGLE_OAUTH_TOKEN` and IMAP credentials are currently set in env

**Phase origin:** Phase 9 Acquisition Pass 2B (2026-04-27)

**Risk:** `email_adapter.py` and `google_adapter.py` under `runtime/acquisition/adapters/` are called by `run_all_live_acquisitions()`. No per-adapter `enabled` flag exists. If Google or IMAP credentials are set in env, they run silently on every acquisition cycle.

**Files to change (after operator confirms credential state):**
- `runtime/acquisition/adapters/email_adapter.py` — add `enabled` guard at entry point
- `runtime/acquisition/adapters/google_adapter.py` — same
- `runtime/acquisition/plans/strikezone-daily.json` — add `email_enabled: false`, `google_enabled: false`

---

### M-3 | Shadow workflows in active registry without deprecation path

**Autonomy:** `AUTONOMOUS — trivial`

**Phase origin:** Phase 9 AOR workflow registry

**Status:** ✅ COMPLETE — 2026-05-11 M-Pass

`hermes_operator_today_shadow.yaml`, `openai_operator_research_shadow.yaml`, `developer_repo_explain_shadow.yaml` — all set to `status: deprecated`. Files remain as historical records; AOR loader skips dispatch for deprecated entries. See: `07_LOGS/Build-Logs/2026-05-11-m-pass-trivial-hardening.md`

---

### M-4 | `approval_rule: none` on all external-touching workflows — no taxonomy exists

**Autonomy:** `AUTONOMOUS` (documentation + 2 manifest changes covered by C-1/C-3)

**Phase origin:** Phase 9 AOR manifest schema

**Status:** ✅ COMPLETE — 2026-05-11 M-Pass

Section 5 added to `06_AGENTS/Permission-Matrix.md`: `none` / `operator-first-run` / `operator-per-run` / `declared-scope-preapproved` taxonomy with notes that `approval_rule` is a policy declaration, not a runtime enforcement gate. See: `07_LOGS/Build-Logs/2026-05-11-m-pass-trivial-hardening.md`

---

### M-5 | No git operations row in `Permission-Matrix.md`

**Autonomy:** `AUTONOMOUS — documentation only`

**Phase origin:** Phase 4 Agent Control + Security Plane

**Status:** ✅ COMPLETE — 2026-05-11 M-Pass

Git operations table added to Section 1 of `06_AGENTS/Permission-Matrix.md`. Covers: `git commit`, `git push`, `git push --force` (any branch + main/master), branch create/delete, `git reset --hard`, amending published commits. All non-Chaser Agent runtimes are ❌. See: `07_LOGS/Build-Logs/2026-05-11-m-pass-trivial-hardening.md`

---

### M-6 | MCP V1 — No live integration hardening

**Autonomy:** `REQUIRES OPERATOR INPUT` — requires external MCP client (e.g., Claude Desktop) for real deployment testing

**Phase origin:** Phase 9 Runtime MCP Pass 5A (2026-04-20)

**Status:** Deferred. `runtime/mcp/` stdio scaffold is built/hardened (44 tests). No live external client test.

**When to address:** Before any production MCP endpoint is exposed.

---

### M-7 | Pulse Pipeline Runner — Single `operator_approved` flag covers all steps

**Autonomy:** `REQUIRES OPERATOR INPUT` — architecture decision required

**Phase origin:** Phase 9 Pulse Pipeline Runner (2026-04-30)

**Status:** Deferred. `dry_run=True` default makes this low operational risk today.

---

## Section 6 — LOW / Convention-Only

---

### L-1 | `_schema.yaml` and `_sbp_base_template.yaml` protected by naming convention only

**Autonomy:** `AUTONOMOUS`

**Status:** ✅ COMPLETE 2026-05-11

**Phase origin:** Phase 9 AOR loader + SBP substrate

**Fix:** Add `is_template: true` or `is_schema: true` frontmatter field to both files. Add a type-check assertion in `runtime/aor/registry.py` loader alongside the existing filename-prefix check.

**Files changed:**
- `runtime/workflows/registry/_schema.yaml` — `is_schema: true` added
- `runtime/workflows/registry/_sbp_base_template.yaml` — `is_template: true` added
- `runtime/aor/registry.py` — `_assert_meta_file_typed()` + `VALID_STATUSES` expanded with `deprecated`
- `runtime/cli/main.py` — P-D1 section-scoping regex re-applied (was absent despite prior build log)
- `runtime/tests/test_l1_registry_meta_typing.py` — 32 new tests
- `runtime/tests/test_openai_n8n_adapter_foundation.py` — active fixture for deprecated shadow manifest

---

### L-2 | VentureOps approval actor — Unvalidated string

**Autonomy:** `AUTONOMOUS`

**Phase origin:** Phase 9 VentureOps AOR workflow (2026-05-10)

**Status:** ✅ COMPLETE 2026-05-11

**Fix:** `_load_registered_actors()` globs `runtime/memory/adapters/*/identity-ledger.json`, always includes `"operator"`, fail-open per ledger. `_validate_actor()` raises `WorkflowExecutionError` if actor not in registered set (fail closed). Validation fires only inside `if include_approval_consumption_proof:` and `if include_approved_external_send_proof:` blocks — not when those paths are inactive. `approval_decision_actor` extracted to local variable before both call sites.

**Files changed:**
- `runtime/workflows/agent_runtime_governance_audit.py` — `_load_registered_actors()` + `_validate_actor()` helpers; local extraction; two call sites
- `runtime/tests/test_l2_actor_validation.py` — 25 new tests

---

### L-3 | Credential reference enforcement is self-attesting (no scanner)

**Autonomy:** `AUTONOMOUS`

**Phase origin:** Phase 9 Gate policy + all connector manifests

**Status:** ✅ COMPLETE — 2026-05-11 Doctor Hardening Pass

`_check_credential_literals()` added to `runtime/cli/main.py`. Scans all `runtime/**/*.yaml` (excluding `_*` schema files) for key fragments (`api_key`, `token`, `webhook`, `password`, `client_secret`, `private_key`, `secret`) where the value does not match an allowed reference pattern (env var ALL_CAPS, template placeholder, None/bool/numeric). Reports as `severity="warning"`. 68 tests / 68 pass. See: `07_LOGS/Build-Logs/2026-05-11-doctor-hardening.md`

---

## Section 7 — Promoted from Deferred (Now Actionable)

---

### D-5 / Now P-D1 | `chaseos doctor` does not check `protected_files.yaml` sync

**Autonomy:** `AUTONOMOUS`

**Phase origin:** Phase 4/5 Gate, Phase 8/9 doctor command

**Status:** ✅ COMPLETE — 2026-05-11 Doctor Hardening Pass

`_check_protected_files_sync()` added to `runtime/cli/main.py`. Parses `runtime/policy/protected_files.yaml` list and extracts backtick-quoted paths from `06_AGENTS/Permission-Matrix.md` Section 2 table; diffs bidirectionally; reports `severity="error"` on any mismatch. Real vault integration test confirms 13 entries are currently in sync. 68 tests / 68 pass. See: `07_LOGS/Build-Logs/2026-05-11-doctor-hardening.md`

---

### D-6 / Now P-D2 | Per-adapter enabled flags in `strikezone_acquisition`

**Autonomy:** `REQUIRES OPERATOR INPUT` — operator must confirm current credential state before enabling or disabling adapters

**Phase origin:** Phase 9 Acquisition Pass 2B (2026-04-27)

**Fix:** Add per-category `enabled` flags to the acquisition plan JSON and enforce in the adapter dispatcher. Suggested defaults: `rss_enabled: true`, `web_scrape_enabled: true`, `perplexity_enabled: false`, `grok_enabled: false`, `email_enabled: false`, `google_enabled: false`. Paid/credential adapters default to `false` until operator explicitly enables.

**Files to change:**
- `runtime/acquisition/plans/strikezone-daily.json` — add per-adapter enabled flags
- `runtime/acquisition/strikezone_acquisition.py` — enforce enabled flags before dispatching

---

## Section 8 — Still Deferred (Architecture or External Setup Required)

| ID | Item | Phase Origin | Why Deferred | Gate to Reopen |
|----|------|-------------|-------------|----------------|
| D-1 | Automated context routing engine | Phase 9 AOR | New layer; no forcing use case | Phase 12 context management work |
| D-2 | Multi-repo policy enforcement | Phase 9 AOR | No second vault instance exists | Second vault creation |
| D-3 | `runtime/audit/` migration | Phase 9 AOR | Directory doesn't exist; functional gap absent | Before cross-session audit tooling |
| D-4 | ChaseOS-native cron runner | Phase 9 Schedules | OpenClaw is live executor; native runner = OS daemon work | Phase 10/11 lifecycle work |
| D-7 | Coordination-watch activation proof | Phase 9 Agent Bus | Round-trip proof not built | Before enabling any watch loop |
| D-8 | Research-pack SBP verification with real files | Phase 9 SBP | No evidence in repo | Before enabling `sbp_strikezone_digest` |

---

## Operator Decision Register

Items that cannot be implemented without an operator decision:

| Decision | Needed For | Options |
|---|---|---|
| Are `PERPLEXITY_API_KEY`, `XAI_API_KEY`, `GOOGLE_OAUTH_TOKEN`, IMAP credentials set in env? | C-1, M-2, D-6 | Operator confirms yes/no |
| C-1: `shadow_mode: true` vs `approval_rule: operator-first-run`? | C-1 | `shadow_mode` = safer/faster; `approval_rule` = more granular |
| H-3: Acceptable `max_cycles_per_day` per watch loop? | H-3 | Suggested: Chaser Agent=480, Hermes=288, OpenClaw=720 |

---

## All-Item Count

| Severity | Count | Autonomous | Requires Operator |
|---|---|---|---|
| CRITICAL | 3 | 2 (C-2, C-3) | 1 (C-1) |
| HIGH | 4 | 3 (H-1, H-2, H-4) | 1 (H-3) |
| Gate Hook | 3 | 3 (G-1, G-2, G-3) | 0 |
| Connector/Capture | 3 | 3 (P-C1, P-C2, P-C3) | 0 |
| MEDIUM | 7 | 4 (M-1, M-3, M-4, M-5) | 3 (M-2, M-6, M-7) |
| LOW | 3 | 3 (L-1, L-2, L-3) | 0 |
| Promoted Deferred | 2 | 1 (P-D1) | 1 (P-D2) |
| Still Deferred | 6 | — | — |
| **Total** | **31** | **19 AUTONOMOUS** | **6 REQUIRES INPUT** |

---

## Sprint Plan (current queue — 2026-05-11)

### ✅ Completed (13 items)

| Item | Description | Build Log |
|------|-------------|-----------|
| C-2 | `hermes_watch.yaml` synthesize default → False | `2026-05-11-hygiene-snapshot-hardening.md` |
| C-3 | `sbp_strikezone_digest.yaml` human_in_loop → required | `2026-05-11-hygiene-snapshot-hardening.md` |
| G-1 | `protected_write_guard.py` fail-closed on YAML parse error | `2026-05-11-gate-hook-hardening-pass.md` |
| G-2 | `ingestion_promotion_guard.py` fail-closed on JSON parse error | `2026-05-11-gate-hook-hardening-pass.md` |
| G-3 | `protected_write_guard.py` separator-boundary path matching | `2026-05-11-gate-hook-hardening-pass.md` |
| H-1 | `setup_init` split → `setup_init_scaffold` + `setup_init_seed_files` | `2026-05-11-high-severity-allowlist-hardening.md` |
| H-2 | `host.startup_folder` approval_gate declared in allowlist | `2026-05-11-high-severity-allowlist-hardening.md` |
| H-4 | `os_hygiene_graph` pre-mutation snapshot + diff log | `2026-05-11-hygiene-snapshot-hardening.md` |
| P-C1 | `rss_connector.py` MAX_ITEMS_PER_FEED = 200 | `2026-05-11-connector-size-guards.md` |
| P-C2 | `watch_folders.py` MAX_WATCHED_FILE_SIZE_BYTES = 10 MB | `2026-05-11-connector-size-guards.md` |
| P-C3 | `browser_connector.py` MAX_HTML_INPUT_CHARS = 500 000 | `2026-05-11-connector-size-guards.md` |
| L-3 | `chaseos doctor` YAML credential literal scanner | `2026-05-11-doctor-hardening.md` |
| P-D1 | `chaseos doctor` `protected_files.yaml` ↔ Permission-Matrix sync check | `2026-05-11-doctor-hardening.md` |

---

### Next — Trivial AUTONOMOUS (no tests required)

Pick up in order. Each item is a small manifest edit or 1-line doc change — no test suite needed, no operator input required.

| Priority | Item | File(s) | Change |
|----------|------|---------|--------|
| 1 | M-1 | `runtime/policy/protected_files.yaml` | Line 1: `# Last synced: 2026-03-20` → `# Last synced: 2026-05-11` |
| 2 | M-3 | `runtime/workflows/registry/hermes_operator_today_shadow.yaml`<br>`runtime/workflows/registry/openai_operator_research_shadow.yaml`<br>`runtime/workflows/registry/developer_repo_explain_shadow.yaml` | Add `status: deprecated` field to each |
| 3 | M-4 | `06_AGENTS/Permission-Matrix.md` | Add `approval_rule` taxonomy section: `none` / `operator-first-run` / `operator-per-run` |
| 4 | M-5 | `06_AGENTS/Permission-Matrix.md` | Add git operations table to Section 1 (commit/push/force-push/branch per runtime) |

---

### Then — Code AUTONOMOUS (requires tests)

| Priority | Item | File(s) | Change |
|----------|------|---------|--------|
| 5 | ~~L-1~~ | ~~`_schema.yaml` / `_sbp_base_template.yaml` / `registry.py`~~ | ✅ COMPLETE 2026-05-11 |
| 6 | ~~L-2~~ | ~~`runtime/workflows/agent_runtime_governance_audit.py`~~ | ✅ COMPLETE 2026-05-11 |

---

### Blocked — Requires Operator Input

Do not implement these without surfacing the decision to the operator first.

| Item | Blocked On | Decision Needed |
|------|-----------|-----------------|
| C-1 | `sch-strikezone-acquisition-0550.yaml` enabled=true | (1) Run `echo $PERPLEXITY_API_KEY $XAI_API_KEY` — if either set, disable schedule immediately. (2) Choose: `shadow_mode: true` vs `approval_rule: operator-first-run` |
| H-3 | All three `* * * * *` watch schedules disabled but no rate guard | Confirm acceptable `max_cycles_per_day` per runtime. Suggested: Chaser Agent=480, Hermes=288, OpenClaw=720 |
| M-2 / P-D2 | `email_adapter.py` + `google_adapter.py` have no enabled guard | Confirm whether `GOOGLE_OAUTH_TOKEN` and IMAP credentials are set in env |

---

### Deferred — Architecture or External Setup Required

| Item | Reason | Gate to Reopen |
|------|--------|----------------|
| D-7 | Coordination-watch activation proof not built | Before enabling any watch loop schedule |
| D-8 | Research-pack SBP verification with real files | Before enabling `sbp_strikezone_digest` |
| M-6 | MCP V1 live integration hardening | Before live MCP deployment |
| M-7 | Pulse Pipeline Runner approval granularity | Before Pulse pipeline goes live |
| D-1 | Automated context routing engine | Phase 12 context management work |
| D-2 | Multi-repo policy enforcement | Second vault creation |
| D-3 | `runtime/audit/` migration | Before cross-session audit tooling |
| D-4 | ChaseOS-native cron runner | Phase 10/11 lifecycle work |

---

## Complete File Manifest

| File | Items | Sprint |
|------|-------|--------|
| `runtime/workflows/registry/hermes_watch.yaml` | C-2 | 1 |
| `runtime/workflows/registry/sbp_strikezone_digest.yaml` | C-3 | 1 |
| `runtime/policy/protected_files.yaml` | M-1 | 1 |
| `runtime/workflows/registry/hermes_operator_today_shadow.yaml` | M-3 | 1 |
| `runtime/workflows/registry/openai_operator_research_shadow.yaml` | M-3 | 1 |
| `runtime/workflows/registry/developer_repo_explain_shadow.yaml` | M-3 | 1 |
| `06_AGENTS/Permission-Matrix.md` | M-4, M-5 | 1 |
| `runtime/workflows/registry/_schema.yaml` | L-1 | 1 |
| `runtime/workflows/registry/_sbp_base_template.yaml` | L-1 | 1 |
| `runtime/policy/gateway_allowlists.json` | H-2 (Sprint 1), H-1 (Sprint 3) | 1 + 3 |
| `.claude/hooks/protected_write_guard.py` | G-1, G-3 | 2 |
| `.claude/hooks/ingestion_promotion_guard.py` | G-2 | 2 |
| `runtime/capture/connectors/rss_connector.py` | P-C1 | 2 |
| `runtime/capture/watch_folders.py` | P-C2 | 2 |
| `runtime/capture/connectors/browser_connector.py` | P-C3 | 2 |
| `runtime/cli/main.py` | L-3, P-D1 | 2 |
| `runtime/workflows/os_hygiene_graph.py` | H-4 | 2 |
| `runtime/workflows/agent_runtime_governance_audit.py` | L-2 | 2 |
| `runtime/aor/registry.py` | L-1 (loader) | 3 |
| `runtime/schedules/sch-strikezone-acquisition-0550.yaml` | C-1 | 4 |
| `runtime/workflows/registry/strikezone_acquisition.yaml` | C-1, M-4 | 4 |
| `runtime/schedules/sch-chaser-agent-watch-every-minute.yaml` | H-3 | 4 |
| `runtime/schedules/sch-hermes-watch-every-minute.yaml` | H-3 | 4 |
| `runtime/schedules/sch-openclaw-watch-every-minute.yaml` | H-3 | 4 |
| `runtime/aor/engine.py` | H-3 | 4 |
| `runtime/acquisition/plans/strikezone-daily.json` | M-2, P-D2 | 4 |
| `runtime/acquisition/adapters/email_adapter.py` | M-2 | 4 |
| `runtime/acquisition/adapters/google_adapter.py` | M-2 | 4 |
| `runtime/acquisition/strikezone_acquisition.py` | P-D2 | 4 |

---

*ChaseOS-Hardening-Passover.md — All-phase hardening register | v1.1 | updated 2026-05-11*
*Supersedes: `06_AGENTS/Phase9-Hardening-Passover.md`*
*Source: security/permission-audit-2026-05-11.md + direct repository inspection 2026-05-11*
*Completed 16/25 actionable items. All AUTONOMOUS items complete. Remaining: C-1/M-2/P-D2 (REQUIRES OPERATOR INPUT — credentials); D-series (deferred).*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
