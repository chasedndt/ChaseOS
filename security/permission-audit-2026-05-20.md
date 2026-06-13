---
type: security-audit
title: ChaseOS Permission Audit — 2026-05-20
version: 1.0
created: 2026-05-20
auditor: Archon (Claude Code Engineering Runtime)
scope: Post-2026-05-11 delta — Studio Shell, Phase 10/11, daemon lifecycle, folder-import flow, chat routing, new workflows
canonical_source: 06_AGENTS/Permission-Matrix.md
prior_audit: security/permission-audit-2026-05-11.md
connected_indexes:
  - [[Security-Audits-Index]]
  - [[Agent-Activity-Index]]
---

# ChaseOS Permission Audit — 2026-05-20

> **Auditor:** Archon (Claude Code Engineering Runtime)
> **Scope:** Incremental delta audit covering all new surfaces built since 2026-05-11:
> Phase 10 Studio Shell (PyWebView), Phase 11 Chat Companion, daemon lifecycle API,
> folder-import flow, 3D graph overhaul, new workflow manifests, .exe packaging,
> provider-agnostic routing, and security-audit-fix regression tests.
> **Method:** Static analysis of runtime/studio/shell/api.py, runtime/workflows/,
> runtime/schedules/, runtime/policy/, runtime/tests/, and all new manifests.
> **Prior audit remediation status included below.**

---

## Prior Audit (2026-05-11) Remediation Status

### FIXED ✅

| Finding | Fix Applied | Enforcement |
|---------|-------------|-------------|
| **C-1**: strikezone_acquisition live API calls, no gate | `shadow_mode: true` + `approval_gate: true` added to `sch-strikezone-acquisition-0550.yaml` | Enforced in `hermes_watch.py:203` — shadow runs record intent without subprocess |
| **C-2**: Hermes LLM synthesis fail-open | `synthesize=False` default in all handlers; `llm_synthesis_enabled: false` in hermes_watch.yaml | Regression tests in `test_security_audit_fixes.py` covering 6 code paths |
| **C-3**: SBP Discord delivery without draft review | `draft_review_required: true` + `human_in_loop: required` in `sbp_strikezone_digest.yaml` | `DiscordDeliveryAdapter` checks flag before delivery |
| **H-1**: setup_init vault-wide write target | Split into `setup_init_scaffold` (folder names only) + `setup_init_seed_files` (explicit file list) | `test_h1_setup_init_split.py` verifies split and rejects old broad key |
| **H-2**: host.startup_folder no approval gate | `approval_gate: operator` + `audit_requirement: startup_write_tag` added to `gateway_allowlists.json:248` | Policy documented; runtime enforcement requires callsite check |
| **H-3**: Watch loops at * * * * * with no rate guard | `runtime/aor/rate_guard.py` built; `max_cycles_per_day` added to `ScheduleIntent`; AOR engine pre-stage rate check | `test_h3_rate_guard.py` covers rate_guard, schedule loader, and engine integration |
| **L-2**: ventureops approval actor unvalidated | `test_l2_actor_validation.py` added; actor validated against identity ledger | Tests enforce actor format and registry membership |

### STILL OPEN FROM PRIOR AUDIT

| Finding | Status | Notes |
|---------|--------|-------|
| **M-1**: protected_files.yaml not synced | ⚠️ PARTIALLY OPEN | File shows `Last synced: 2026-05-11`. Synced at audit time, but 9+ days of new paths added since. No automatic sync mechanism. |
| **M-3**: Shadow workflows in active registry | ⚠️ OPEN | `hermes_operator_today_shadow.yaml`, `openai_operator_research_shadow.yaml`, `developer_repo_explain_shadow.yaml` still in `runtime/workflows/registry/`. No `status: deprecated` set. |
| **M-4**: approval_rule: none on external workflows | ⚠️ PARTIALLY OPEN | `strikezone_acquisition.yaml` still has `approval_rule: none`. `shadow_mode: true` mitigates for now, but there is no enforcement of per-run approval if shadow_mode is disabled. |
| **M-5**: No git operations row in Permission-Matrix | ⚠️ OPEN | No explicit git operations permission row added to Permission-Matrix.md. |
| **L-3**: Credential reference enforcement self-attesting | ⚠️ PARTIALLY OPEN | `test_gateway_allowlists_and_credentials.py` exists; unclear if it scans all YAML for literal secrets. |

---

## New Findings (2026-05-11 → 2026-05-20)

### HIGH

#### N-1: `start_runtime_daemon` hardcodes `--synthesize` — bypasses C-2 fix

**File:** `runtime/studio/shell/api.py:1294–1299`

**What:**
```python
cmd = [
    sys.executable, "-m", "runtime.cli.main",
    "runtime", "daemon",
    "--runtime", runtime_name,
    "--synthesize",          # ← hardcoded, no opt-in
    "--daemon-interval", "5",
]
```

**Risk:** When the Studio UI operator clicks "Start Daemon" for Hermes or OpenClaw,
the background watch loop is launched with `--synthesize` unconditionally. This means
any review task claimed by that daemon will call the Anthropic API (LLM synthesis),
even though the C-2 fix explicitly established `synthesize=False` as the safe default
requiring explicit opt-in. The daemon launch path bypasses the opt-in requirement.

**Scope:** Hermes and OpenClaw daemons launched from the Studio shell sidebar.

**Remediation:**
- Remove `"--synthesize"` from the hardcoded command in `start_runtime_daemon`.
- Add a `synthesize: bool = False` parameter to `start_runtime_daemon(runtime_adapter, synthesize=False)` and let the operator explicitly pass it.
- Add a UI toggle in the daemon start flow: "Enable AI synthesis (calls LLM API)" — off by default.
- Add a regression test asserting that `start_runtime_daemon` does NOT include `--synthesize` by default.

---

#### N-2: `start_runtime_daemon` / `stop_runtime_daemon` spawn OS processes without approval gate

**File:** `runtime/studio/shell/api.py:1255–1376`

**What:** `start_runtime_daemon` spawns a detached subprocess. `stop_runtime_daemon`
sends SIGTERM to a process. Neither routes through `StudioService.queue_for_approval()`.
By contrast, `toggle_runtime_surface` (a much less impactful write action) correctly
routes through the approval queue.

**Risk:** Any operator-visible JS call can start a background daemon process that:
- Persists after Studio closes
- Polls the Agent Bus every 5 seconds
- Makes LLM API calls (see N-1)
- Writes to `07_LOGS/Agent-Activity/` continuously

Process spawn is a more significant OS action than a vault file write, yet it has no
approval checkpoint.

**Remediation:**
- Route `start_runtime_daemon` through the approval queue: queue an `ActionSpec` with
  `action_type="spawn_process"` and metadata about the runtime and flags. Execute only
  after operator approval.
- Alternatively, add a confirmation dialog in the frontend before spawning.
- Add a test asserting that `start_runtime_daemon` returns `requires_approval` status.

---

### MEDIUM

#### N-3: `scan_folder` accepts arbitrary filesystem paths — no boundary check

**Files:** `runtime/studio/shell/api.py:4496`, `runtime/studio/open_folder_compatibility_readiness.py:100`

**What:** `scan_folder(folder_path: str)` in the StudioAPI calls multiple analysis modules
(compatibility readiness, Obsidian detection, markdown inference, bootstrap wizard preview,
upgrade plan approval packet). The underlying `_resolve_target()`:
```python
def _resolve_target(vault_root, folder_path=None):
    vault = Path(vault_root).resolve()
    if folder_path is None or str(folder_path).strip() == "":
        return vault, vault
    candidate = Path(folder_path)
    if not candidate.is_absolute():
        candidate = vault / candidate
    return vault, candidate.resolve()   # ← no is_relative_to(vault) check
```
There is no validation that `candidate` is within the vault root or any other approved boundary.

**Risk:** The JS frontend can enumerate any directory on the host filesystem
(directory listing, file existence checks, file counts). While these are read-only
operations and `folder_path` currently comes from a system file dialog, any XSS in
markdown content rendered by the 3D graph or other panels could trigger `scan_folder`
on sensitive paths (e.g., `<WINDOWS_USER_HOME>\.ssh`, `C:\Windows\System32`, etc.).

**Remediation:**
- Add a path-boundary guard in `scan_folder`:
  ```python
  resolved = Path(folder_path).resolve()
  # Accept if within vault, or if it's a clean absolute path outside vault
  # but NEVER traverse to known sensitive system paths
  ```
- Alternatively, only accept paths returned by `open_folder_dialog()` (system dialog result)
  and reject direct API calls with arbitrary strings.
- At minimum, block paths containing `.ssh`, `AppData/Local/Microsoft/Credentials`,
  `Windows/System32`, and other known sensitive locations.

---

#### N-4: Phase 11 chat `send_chat_message` has no message size cap

**File:** `runtime/studio/phase11_chat_send_message.py:82`

**What:** `send_chat_message` posts raw user `message` directly to the Agent Bus
(SQLite) with no length limit. The only check is `if not message: return error`.

**Risk:** A user could send a very large message (e.g., pasting a 10 MB document),
bloating the SQLite Agent Bus database and causing `07_LOGS/Agent-Activity/` writeback
files to grow unbounded. Repeated large messages could degrade Bus performance.

**Remediation:**
- Cap `message` at a reasonable limit (e.g., 8000 chars — matching Whop delivery adapter's `POST_CHAR_LIMIT`):
  ```python
  MAX_CHAT_MESSAGE_LEN = 8000
  if len(message) > MAX_CHAT_MESSAGE_LEN:
      message = message[:MAX_CHAT_MESSAGE_LEN]  # or return error
  ```
- Log a warning when truncation occurs.

---

#### N-5: `companion_config.json` routing not in approval-required paths

**File:** `runtime/studio/phase11_chat_send_message.py:48`, `runtime/studio/service.py:74`

**What:** `_load_recipient_map()` reads `.chaseos/companion_config.json` to build the
chat routing table. This file controls which Agent Bus recipient receives chat messages.
The path `.chaseos/` is NOT in `_ALWAYS_APPROVAL_REQUIRED_PREFIXES` in `service.py`:
```python
_ALWAYS_APPROVAL_REQUIRED_PREFIXES = (
    "02_KNOWLEDGE/", "01_PROJECTS/", "00_HOME/",
    "04_SOPS/", "06_AGENTS/", "runtime/aor/",
)
```
So a write action targeting `.chaseos/companion_config.json` would NOT require approval.

**Risk:** An automated workflow or a carelessly approved write action could update the
companion config, redirecting all chat messages to a different runtime without the
operator explicitly acknowledging the routing change.

**Remediation:**
- Add `.chaseos/` to `_ALWAYS_APPROVAL_REQUIRED_PREFIXES` in `service.py`.
- OR treat `companion_config.json` as a protected file (requires explicit instruction).
- Add schema validation on load: reject configs with unknown keys or non-string recipient names.

---

#### N-6: `runtime/studio/approvals/` not in approval-required paths

**File:** `runtime/studio/service.py:74`

**What:** The approval queue persists as JSON files in `runtime/studio/approvals/`.
This path is NOT in `_ALWAYS_APPROVAL_REQUIRED_PREFIXES`. The `.json` extension is NOT
in `_FORBIDDEN_WRITE_EXTENSIONS`. This means a write action targeting
`runtime/studio/approvals/<id>.json` would be treated as an unapproved immediate write.

**Current mitigations:** No direct JS API method exposes arbitrary file write to
arbitrary paths — all writes go through specific API methods. Risk is latent, not
immediately exploitable.

**Risk:** If a future API method adds a general `write_file(path, content)` endpoint,
or if a workflow gains vault write access to `runtime/studio/`, it could forge an
approval record and execute it via `submit_approval(id, "approve")`.

**Remediation:**
- Add `runtime/studio/approvals/` to `_ALWAYS_APPROVAL_REQUIRED_PREFIXES` OR to
  `_PROTECTED_FILES` (blocking all Studio writes to that path).
- Consider adding `runtime/studio/` broadly to the approval-required list.

---

#### N-7: Three shadow/experimental workflows without decommission path (M-3 still open)

**Files:**
- `runtime/workflows/registry/hermes_operator_today_shadow.yaml`
- `runtime/workflows/registry/openai_operator_research_shadow.yaml`
- `runtime/workflows/registry/developer_repo_explain_shadow.yaml`

Plus three new workflows in `packs/` subdirectory:
- `runtime/workflows/registry/packs/agent_runtime_governance_audit.yaml`
- `runtime/workflows/registry/packs/growth_studio_proof_pack.yaml`

**Risk:** Shadow workflows in the active registry can be invoked via `chaseos run`.
No `status: deprecated` or archive path defined. Packs subdirectory has no `_*` naming
convention guard — if the loader scans recursively, these would load as live workflows.

**Remediation:**
- Set `status: deprecated` on all three shadow workflows.
- Move them to `runtime/workflows/archive/` or add a `deprecated_at` field.
- Add a loader check: warn (or skip) workflows with `status: deprecated`.
- Confirm whether the loader scans `packs/` recursively and if so, add schema type enforcement.

---

### LOW

#### N-8: `protected_files.yaml` not synced since 2026-05-11 — new sensitive paths uncovered

**File:** `runtime/policy/protected_files.yaml:8`

**What:** Header reads `Last synced: 2026-05-11`. Since that date, significant new system
paths have been added: `runtime/studio/shell/api.py`, `runtime/studio/shell/main.py`,
`.chaseos/companion_config.json`, `runtime/companion/`, `runtime/memory/adapters/`,
`ChaseOS-Studio.spec`, `build_exe.ps1`. None of these are in the 13-file protected list.

The protected_write_guard.py hook reads from this file — not from Permission-Matrix.md.

**Remediation:**
- Add a `chaseos doctor` check: compare protected_files.yaml against Permission-Matrix.md
  Section 2 and warn if they differ.
- Review whether any Phase 10/11 paths deserve protected status (ChaseOS-Studio.spec,
  companion config, shell main.py at minimum).
- Update `Last synced:` date after each sync.

---

#### N-9: `strikezone_acquisition.yaml` still has `approval_rule: none` (M-4 still open)

**File:** `runtime/workflows/registry/strikezone_acquisition.yaml:27`

**What:** The manifest continues to declare `approval_rule: none`. The schedule
`sch-strikezone-acquisition-0550.yaml` has `shadow_mode: true` and `approval_gate: true`
(documentation flag only), but the manifest-level approval rule is unchanged.

**Risk:** If shadow_mode is disabled by the operator without also adding a manifest-level
approval gate, live paid API calls resume immediately with no per-run approval checkpoint.
The safety relies on operator remembering to also add a manifest-level gate before going live.

**Remediation:**
- Change `approval_rule: none` to `approval_rule: operator-first-run` in the manifest.
- Document what "operator-first-run" enforces in the AOR engine.

---

#### N-10: WebView vault_root injection via Python repr — not formally audited

**File:** `runtime/studio/shell/main.py:108`

**What:**
```python
window.evaluate_js(
    f"window.__CHASEOS_VAULT_ROOT__ = {repr(str(vault_root))};"
)
```
Python `repr()` of a string uses `'` quotes and escapes backslashes, but the resulting
JS is `window.__CHASEOS_VAULT_ROOT__ = '%USERPROFILE%\\...';`. This works for
standard Windows paths but has not been formally audited against edge-case path characters
(paths with embedded single quotes, Unicode normalization differences, etc.).

**Remediation:**
- Use `json.dumps(str(vault_root))` instead of `repr()` for JS-safe string serialization:
  ```python
  import json
  window.evaluate_js(
      f"window.__CHASEOS_VAULT_ROOT__ = {json.dumps(str(vault_root))};"
  )
  ```
- `json.dumps` always produces double-quoted, properly escaped JS string literals.

---

## Summary Table

| ID | Risk | Category | Active Now? | Priority |
|----|------|----------|-------------|----------|
| N-1 | `start_runtime_daemon` hardcodes `--synthesize` | Financial / C-2 bypass | ~~YES~~ **FIXED 2026-05-21** | ~~Immediate~~ Closed |
| N-2 | Daemon spawn/stop bypasses approval gate | Process lifecycle / Governance | ~~YES~~ **FIXED 2026-05-21** | ~~High~~ Closed |
| N-3 | `scan_folder` accepts arbitrary filesystem paths | Info disclosure | ~~YES~~ **FIXED 2026-05-21** | ~~High~~ Closed |
| N-4 | Chat message no size cap | Resource abuse | ~~YES~~ **FIXED 2026-05-21** | ~~Medium~~ Closed |
| N-5 | `companion_config.json` not approval-required | Routing hijack | ~~Latent~~ **FIXED 2026-05-21** | ~~Medium~~ Closed |
| N-6 | `runtime/studio/approvals/` not protected | Approval forgery (latent) | ~~Latent~~ **FIXED 2026-05-21** | ~~Medium~~ Closed |
| N-7 | Shadow/experimental workflows, no decommission | Attack surface | ~~Latent~~ **FIXED 2026-05-21** | ~~Medium~~ Closed |
| M-1 | `protected_files.yaml` sync stale | Enforcement drift | ~~Latent~~ **FIXED 2026-05-21** | ~~Low-Medium~~ Closed |
| M-3 | Shadow workflows in active registry | Attack surface | ~~Latent~~ **FIXED 2026-05-21** | ~~Low-Medium~~ Closed |
| M-4 | `strikezone_acquisition` approval_rule: none | Governance gap | ~~Latent~~ **FIXED 2026-05-21** | ~~Low~~ Closed |
| M-5 | No git operations row in Permission-Matrix | Documentation gap | **ALREADY CLOSED (2026-05-11)** | Closed |
| N-8 | New paths not in protected_files.yaml | Enforcement drift | ~~Latent~~ **FIXED 2026-05-21** | ~~Low~~ Closed |
| N-9 | strikezone_acquisition approval_rule: none (M-4 renamed) | Governance gap | ~~Latent~~ **FIXED 2026-05-21** | ~~Low~~ Closed |
| N-10 | vault_root repr injection not formally audited | XSS risk | **ALREADY CLOSED (2026-05-20)** — `main.py:134` uses `json.dumps` | Closed |

---

## Recommended Remediation Order

1. **Fix N-1 immediately** — remove `--synthesize` from `start_runtime_daemon` hardcoded command. Add `synthesize=False` default parameter. Add UI toggle. This is a direct C-2 regression.

2. **Fix N-10 immediately (1 line)** — replace `repr()` with `json.dumps()` in `main.py:108`.

3. **Fix N-3 before exposing folder-import to broader users** — add a boundary check in `scan_folder` and all `folder_path` API methods. A path that resolves outside the vault should either be rejected or only accepted from the system file dialog.

4. **Gate N-2 (daemon spawn approval)** — add a minimal approval checkpoint for daemon start. Can be a simple confirmation pattern in the frontend if a full approval queue record is too heavy.

5. **Add N-4 size cap** — 1 line change in `phase11_chat_send_message.py`.

6. **Add N-5 protection** — add `.chaseos/` to approval-required prefixes.

7. **Close M-3** — mark shadow workflows deprecated and move to archive.

8. **Close M-1/N-8** — sync `protected_files.yaml`; add `chaseos doctor` consistency check.

9. **Close M-4/N-9** — change `strikezone_acquisition.yaml` approval_rule to `operator-first-run`.

---

## Not Found (No New Findings)

- **Approval forgery via StudioService** — the approval JSON format and execution path are robust. No direct JS API method exposes arbitrary file write to `runtime/studio/approvals/`. Risk is latent only.
- **C-2 regression in workflow handlers** — regression tests cover all known synthesis call sites. The only gap is the daemon launch path (N-1).
- **C-3 regression in SBP delivery** — `draft_review_required` is correctly enforced in `DiscordDeliveryAdapter`. No regression found.
- **Path traversal in `service.py`** — `_resolve_path()` correctly rejects paths outside the vault (raises `StudioServiceError`).
- **Credential leakage in manifests** — no literal API keys found in scanned YAML files.

---

*security/permission-audit-2026-05-20.md — Archon (Claude Code Engineering Runtime)*
*Created: 2026-05-20 | Scope: Post-2026-05-11 delta audit | Prior: security/permission-audit-2026-05-11.md*
