---
type: framework-control
title: ChaseOS Gate — Execution Control Layer
version: 1.0
created: 2026-03-20
scope: framework-level
---

# ChaseOS Gate

> The ChaseOS Gate is the custom execution control layer that sits above all provider-specific adapters.
> It enforces ChaseOS policy through machine-readable manifests, scoped controls, and auditable execution paths.
> Markdown docs are the policy source of truth. The Gate is how that policy is enforced by force.
> This document defines what the Gate is, why it exists, what it enforces now, and what remains documentation-only.

---

## Current Enforcement Status (as of 2026-04-28)

Quick-glance status for the active Claude lane plus the Phase 9 runtime/gateway prep surfaces. Full detail: Section 3.

| Enforcement Layer | Status | Mechanism |
|-------------------|--------|-----------|
| Protected-file write guard | **ACTIVE — VERIFIED** | PreToolUse hook exits 1 on protected file write |
| Ingestion promotion guard | **ACTIVE — VERIFIED** | PreToolUse hook exits 1 on unauthorized `02_KNOWLEDGE/` write |
| Session-start context check | **ACTIVE — VERIFIED** | UserPromptSubmit hook — notification, not blocking |
| Session-end audit reminder | **ACTIVE — VERIFIED** | Stop hook — checklist notification |
| Adapter manifest validation | **ACTIVE CLI CHECK / PARTIAL RUNTIME USE** | `chaseos gate validate`, `chaseos gate check-*`, and `chaseos run` coordination preflight |
| Bus-first coordination guard | **ACTIVE FOR COORDINATION-SENSITIVE WORKFLOWS** | `chaseos run` requires adapter identity and `--coordination-via runtime/agent_bus/` where manifests require it |
| Deny-by-default runtime operation policy | **ACTIVE EXPANDED FOOTHOLD** | `runtime/chaseos_gate.py::check_runtime_operation`; canonical CLI surface `chaseos gate check-operation`; live mutation callers now include `chaseos agent-bus ...`, setup apply/set/init-write, bounded config writes, schedule enable/disable, event-state writes, existing event/MCP workflow-dispatch seams, draft scaffold generation, SBP Discord/Whop delivery adapters, bounded OSRIL approval response/resume writes, bounded browser operator open/inspect/screenshot audit/artifact writes, runtime registry lifecycle mutations, coordination-watch lifecycle/scheduler side-effect commands, a declared-but-blocked RPGL live provider probe operation schema, and a declared-but-blocked Browser CDP read-only proof operation schema |
| Gateway allowlists + credential boundary | **ACTIVE FOOTHOLD** | `runtime/policy/gateway_allowlists.json`; Gate allowlist checks; setup-state writer rejects raw secret values |
| Runtime state and lifecycle inspection | **ACTIVE INSPECTION SURFACE** | `chaseos runtime inventory/status/health/...` from canonical `runtime.cli.main` |
| OpenAI / local-oss / n8n enforcement | Partial / documentation only | Manifests declared; no hook-equivalent hard enforcement for those harnesses yet |

**Active hard-enforced adapter:** Claude Code / Anthropic harness.
**Canonical CLI entrypoint:** `runtime.cli.main:main` via installed `chaseos` / `chase`; `chaseos.py` and `runtime/cli.py` are compatibility shims only.
**Current Phase 9 refactor records:** `07_LOGS/Build-Logs/2026-04-26-ChaseOS-CLI-Consolidation-Codex-GPT5.md`; `07_LOGS/Build-Logs/2026-04-27-ChaseOS-Deny-Default-Runtime-Policy-Codex-GPT5.md`.
**Verification date:** 2026-03-21 — 11 live tests all passed. Full record: `07_LOGS/Agent-Activity/2026-03-21-claude-gate-verification-micropass.md`
**Runtime policy verification date:** 2026-05-02 — focused gate/RPGL/BOSL regression tests passed for the declared-but-blocked `runtime.provider.live_probe` operation and Browser CDP read-only proof surfaces through the injected executor, no-launch isolated browser launcher design, no-launch launcher implementation preflight, and approval-gated default CDP code path. Hermes later completed the Browser CDP local throwaway-profile activation smoke; closeout-readiness now reports that activation when repo-local evidence is present. Earlier focused gate/event-dispatch/MCP/SBP-delivery/gateway-allowlist regression tests passed 2026-04-28. Browser external API binding, runtime registry lifecycle mutation checks, and coordination-watch lifecycle host side-effect checks were extended in `07_LOGS/Build-Logs/2026-04-27-ChaseOS-phase9-gate-browser-lifecycle-policy-Codex-GPT5.md` and `07_LOGS/Build-Logs/2026-04-27-ChaseOS-gate-lifecycle-side-effect-policy.md`; event-triggered AOR dispatch and Runtime MCP `workflow.invoke_bounded` dispatch were extended in `07_LOGS/Build-Logs/2026-04-28-ChaseOS-gateway-studio-dispatch-policy-preflight.md`; SBP Discord/Whop delivery writes were extended in `07_LOGS/Build-Logs/2026-04-28-ChaseOS-phase9-sbp-delivery-gate-policy.md` and finalized in `07_LOGS/Build-Logs/2026-04-28-ChaseOS-sbp-delivery-side-effect-policy.md`; OSRIL approved-resume writes were extended in `07_LOGS/Build-Logs/2026-04-28-ChaseOS-osril-resume-ready-runner.md`.

---

## 1. Why the Gate Exists

The ChaseOS agent layer is documented: trust tiers, permission matrices, protected-file lists, adapter standards. These are useful and necessary. They are not sufficient.

Markdown documents do not enforce themselves. A documented rule that says "do not edit protected files without approval" can be violated by any adapter that does not implement that rule mechanically. If the only enforcement is the agent's instruction-following quality, then the permission model is advisory — not enforced.

The ChaseOS Gate exists to close this gap:

| Layer | What it does | Enforced by |
|-------|-------------|-------------|
| Markdown policy docs | Define what is allowed | Human + agent discipline |
| Adapter manifests (YAML) | Machine-readable intent declarations per adapter | Registry + Gate validator |
| Hook scripts | Shell-level pre/post-action guards | Claude Code settings.json |
| Gate entrypoint | Policy-aware session wrapper | Python stub (runtime/) |
| Runtime policy files | Structured task + adapter rules | Gate reads at session start |

**The Gate adds a machine-readable enforcement layer.** It does not replace the markdown docs — those remain canonical. It makes the policies harder to violate accidentally or through instruction drift.

---

## 2. What the Gate Is

The ChaseOS Gate is composed of:

### 2.1 Adapter Manifests
Structured YAML files that declare each adapter's intent, allowed scope, and enforcement posture. Located in `runtime/policy/adapters/`. Each adapter's manifest is the machine-readable statement of what it is allowed to do.

Standard: `[[Adapter-Manifest-Standard]]`

### 2.2 Task Profiles
YAML files that define what reads and permissions are required for each task type. Located in `runtime/policy/tasks/`. A task profile defines: required reads, allowed write targets, approval mode, and promotion behavior for that session type.

### 2.3 Protected File Registry
A machine-readable list of all protected files. Located at `runtime/policy/protected_files.yaml`. This is the source of truth for the hook scripts — hooks read from this file, not from markdown.

### 2.4 Hook Scripts
Shell-callable Python scripts in `.claude/hooks/` that enforce policy at the tool-call level. These run as Claude Code lifecycle hooks (PreToolUse, PostToolUse, Stop) and provide enforcement that is independent of the model's instruction-following.

Current hooks:
- `protected_write_guard.py` — blocks writes to protected files without session approval
- `ingestion_promotion_guard.py` — blocks direct promotion to `02_KNOWLEDGE/` without gate check; now also enforces minimum provenance posture once the promotion gate is approved
- `session_start_context.py` — validates required reads for ingestion sessions
- `session_end_audit.py` — surfaces the session-close checklist on Stop

### 2.5 Gate Entrypoint
`runtime/chaseos_gate.py` — the package policy module for adapter manifests, write/task/coordination checks, provenance minimums, gateway allowlists, credential-reference checks, and the Phase 9 deny-by-default runtime operation policy foothold. Unknown runtime operations are denied until explicitly allowlisted.

### 2.6 Hook Configuration
`.claude/settings.json` — the Claude Code project-level settings file that wires the hook scripts to lifecycle events.

---

## 3. Enforcement Layers in Scope Now

### Layer 1 — Protected-File Write Guard (active via hook)

The `protected_write_guard.py` hook fires on `PreToolUse` for `Write` and `Edit` tool calls. It checks the write target against `runtime/policy/protected_files.yaml`. If the target is a protected file and the session has not explicitly approved it (via a session approval flag), the hook exits non-zero and blocks the write.

This is the highest-priority enforcement. Protected files must not be editable by accident.

**Status:** ACTIVE — VERIFIED 2026-03-21. Tested against all 13 protected files (relative and absolute paths). Blocked correctly with exit 1. Non-protected paths allowed with exit 0. `CHASEOS_APPROVED_FILE` session-approval env var confirmed working. Runs via `.venv/Scripts/python.exe` (repo-local Python 3.13.12 + PyYAML 6.0.3).

### Layer 2 — Ingestion Promotion Guard (active via hook)

The `ingestion_promotion_guard.py` hook fires on `PreToolUse` for `Write` tool calls targeting `02_KNOWLEDGE/`. It verifies that the current session is running as an authorized ingestion pass with the promotion gate met (all 4 conditions confirmed). If not, it blocks the write.

Once the promotion gate is approved, this hook is also now the **first live caller path** for the Phase 9 provenance minimum seam in `runtime/chaseos_gate.py`. That means a promoted knowledge-note write is no longer only checking the session gate flag — it also checks for minimum provenance posture in frontmatter (`verification_status` plus at least one provenance anchor such as `promoted_from`, `source_package_id`, `source_ids`, `source_refs`, `provenance_ref`, or `capture_id`).

This prevents accidental direct promotion that bypasses the triage/sanitize/verify gate and starts making provenance minimums real in a live write path instead of leaving them as a dormant helper only.

**Status:** ACTIVE — VERIFIED 2026-04-24 for provenance-minimum integration. Tested direct write to `02_KNOWLEDGE/` without `CHASEOS_PROMOTION_APPROVED` — blocked. With `CHASEOS_PROMOTION_APPROVED=1` but missing provenance minimums — blocked. With `CHASEOS_PROMOTION_APPROVED=1` plus minimum provenance frontmatter — allowed. Runs via `.venv/Scripts/python.exe`.

### Layer 3 — Session-Start Context Check (notification via hook)

The `session_start_context.py` hook fires on `UserPromptSubmit`. For ingestion sessions, it verifies that the required reads are in scope and reminds the user if not.

**Status:** ACTIVE — VERIFIED 2026-03-21. Tested with a general prompt (no output, exit 0) and an ingestion-session prompt (required-read reminder printed to stderr, exit 0). Does not block — notification only.

### Layer 4 — Session-End Audit Reminder (notification via hook)

The `session_end_audit.py` hook fires on `Stop`. It outputs the session-close checklist to remind the agent to write the build log and check for open loops.

**Status:** ACTIVE — VERIFIED 2026-03-21. Checklist confirmed printed to stderr on invocation, exit 0. Does not block — notification only.

### Layer 5 — Adapter Manifests (validated by CLI; partially enforced at runtime)

Adapter manifests in `runtime/policy/adapters/` declare what each adapter is allowed to do. The Gate entrypoint (`runtime/chaseos_gate.py`) is now exposed through `chaseos gate ...` and the package-native CLI. `chaseos run` also uses manifest-backed preflight for coordination-sensitive workflows so adapter identity and bus path cannot be silently skipped.

**Status:** Manifests defined, CLI validation active, coordination preflight active for manifest-marked workflows. The deny-by-default runtime operation seam now covers agent-bus mutations plus bounded setup/config/schedule writes, event-state writes, event-triggered AOR dispatch, Runtime MCP `workflow.invoke_bounded` dispatch, scaffold draft generation, SBP Discord/Whop delivery writes, OSRIL approval response/resume state writes, browser open/inspect/screenshot audit/artifact paths bound to `browser.navigation`, runtime registry lifecycle mutations, coordination-watch lifecycle/bootstrap host side-effect surfaces bound to `runtime_lifecycle_state`, `host.process`, and `host.scheduler`, RPGL live provider probe preflight approval schema exposure through `runtime.provider.live_probe`, and Browser CDP read-only proof schema exposure through `browser.cdp.read_only_proof`; it is exposed through `chaseos gate check-operation`. RPGL can now write and structurally validate pending approval request artifacts and report a non-executing executor spec/precondition checklist. Browser CDP can now write and structurally validate pending approval request artifacts, report executor spec/precondition checklists, inspect approval decision/idempotency/write-plan preflights, compute approval consumer/marker writer/launcher designs, and execute the bounded approved read-only proof path with a default isolated launcher/client. Both operations still return denied by default until the required approval path is satisfied. Remaining gap: expand this seam across future concrete Gateway/Studio UI dispatches, future approval-consuming live provider execution, and browser actions beyond bounded read/screenshot before Phase 10.

### Layer 6 — Runtime Operation Policy (deny-by-default foothold)

`runtime/chaseos_gate.py::check_runtime_operation()` is now the canonical check for runtime operations that create state, mutate runtime state, trigger coordination, or prepare external side effects.

Current behavior:
- unknown operation names return denied
- actor and target runtime names resolve through `runtime/policy/adapters/`
- required manifests must exist and be active
- coordination-sensitive operations must pass `check_coordination_path()`
- write targets delegate to `check_write_permission()`
- task types delegate to `check_task_type()`
- external API side effects require explicit allowlist IDs; CLI-operator external side effects are only allowed when a runtime operation policy explicitly names the API and opts into CLI operator execution
- operations marked `approval_required` return denied until an executor validates and consumes the named Gate approval schema; `runtime.provider.live_probe` and `browser.cdp.read_only_proof` use this path. Browser CDP now also has no-execution decision, idempotency-reservation, executor dry-run, approval-decision policy, approval decision consumer design, atomic marker writer design, isolated browser launcher design, and isolated launcher implementation preflight surfaces that check approval status, future idempotency marker posture, future write-plan confinement, marker contract shape, future execution order, decision-record requirements, single-use consumer requirements, exclusive-create marker writer requirements, throwaway-profile launcher requirements, and live code-path readiness without consuming approval, writing decisions/markers, launching a browser, or opening CDP.

Current allowlisted operations:
- `agent_bus.ingress.discord`
- `agent_bus.task.create`
- `agent_bus.task.claim`
- `agent_bus.task.update`
- `agent_bus.task.cleanup`
- `agent_bus.task.reclaim`
- `agent_bus.heartbeat`
- `agent_bus.watch`
- `agent_bus.expire_stale`
- `config.set`
- `schedule.enable`
- `schedule.disable`
- `events.emit`
- `events.dispatch`
- `gateway.workflow.dispatch`
- `gateway.workflow.invoke_bounded`
- `sbp.delivery.discord.webhook_send`
- `sbp.delivery.whop.post`
- `osril.approval_response`
- `osril.approval_resume`
- `runtime.provider.live_probe` (declared approval schema; RPGL can persist/structurally validate `rpgl.live_provider_probe.v1` approval artifacts and report executor preconditions, but live execution is still denied/not built)
- `browser.cdp.read_only_proof` (declared approval schema `bosl.cdp_read_only_proof.v1`; denied by default, injected executor tests only, no default CDP connection, no browser launch, and no real profile/session/cookie access)
- `setup.init.write`
- `setup.provider.apply`
- `setup.integration.apply`
- `setup.state.set`
- `scaffold.project.generate`
- `scaffold.workspace.generate`
- `browser.open`
- `browser.inspect`
- `browser.screenshot`
- `agent.register`
- `agent.lifecycle.transition`
- `lifecycle.coordination_watch.run`
- `lifecycle.coordination_watch_supervisor.start`
- `lifecycle.coordination_watch_supervisor.stop`
- `lifecycle.coordination_watch_bootstrap.install`
- `lifecycle.coordination_watch_bootstrap.apply`
- `lifecycle.coordination_watch_bootstrap.verify`
- `lifecycle.coordination_watch_bootstrap.activation_report`
- `lifecycle.coordination_watch_bootstrap.unregister`
- `lifecycle.coordination_watch_bootstrap.handoff`
- `lifecycle.coordination_watch_bootstrap.reboot_verify`
- `lifecycle.coordination_watch_bootstrap.capture_success`
- `lifecycle.coordination_watch_bootstrap.reconcile_reboot_result`
- `lifecycle.coordination_watch_bootstrap.remove`

Current caller path:
- `chaseos gate check-operation ...`
- `chaseos agent-bus ingress discord ...`
- `chaseos agent-bus task create/claim/update/cleanup/reclaim ...`
- `chaseos agent-bus heartbeat ...`
- `chaseos agent-bus watch ...`
- `chaseos agent-bus expire-stale ...`
- `chaseos setup init --write ...`
- `chaseos setup provider wizard <id> --apply ...`
- `chaseos setup integration wizard <id> --apply ...`
- `chaseos setup set ...`
- `chaseos config set ...`
- `chaseos schedule enable/disable ...`
- `chaseos events emit ...`
- `chaseos events dispatch/watch ...`
- Runtime MCP `workflow.invoke_bounded`
- SBP Discord webhook and Whop API delivery adapters
- `chaseos osril respond ...`
- `chaseos osril resume-ready ...`
- `chaseos gate check-operation runtime.provider.live_probe --external-api provider.openai --json` (non-executing schema inspection; returns denied without approval)
- `chaseos gate check-operation browser.cdp.read_only_proof --external-api browser.navigation --json` (non-executing schema inspection; returns denied without approval)
- `chaseos runtime browser-cdp approval-request [target_url] --write-approval-request --json` (writes a pending Browser CDP approval request artifact only; no browser/CDP action)
- `chaseos runtime browser-cdp approval-request --gate-approval-id <id> --json` (structurally validates a pending Browser CDP approval request artifact only; does not consume approval)
- `chaseos runtime browser-cdp executor-spec [target_url] --json` (reports future CDP read-only proof executor preconditions only; may structurally validate a supplied pending approval artifact, but performs no approval consumption, browser launch, CDP connection, screenshot, DOM read, or artifact write)
- `chaseos runtime browser-cdp decision-preflight [target_url] --gate-approval-id <id> --json` (reports approval status, future idempotency marker posture, and future write-plan confinement only; performs no approval consumption, marker write, browser launch, CDP connection, screenshot, DOM read, or artifact write)
- `chaseos runtime browser-cdp idempotency-reservation-spec [target_url] --gate-approval-id <id> --json` (reports the future marker path, marker record template, atomic reservation rules, and blocked status only; performs no approval consumption, marker write, browser launch, CDP connection, screenshot, DOM read, or artifact write)
- `chaseos runtime browser-cdp executor-dry-run [target_url] --gate-approval-id <id> --json` (reports future executor sequence, stop conditions, artifact plan, and feature tracker only; performs no approval consumption, marker write, browser launch, CDP connection, screenshot, DOM read, or artifact write)
- `chaseos runtime browser-cdp approval-decision-policy [target_url] --gate-approval-id <id> --json` (reports future approval decision record and consumption rules only; performs no decision write, approval consumption, marker write, browser launch, CDP connection, screenshot, DOM read, or artifact write)
- `chaseos runtime browser-cdp approval-decision-consumer-design [target_url] --gate-approval-id <id> --json` (reports future single-use approval consumer algorithm, request/decision binding checks, marker-absence guard, consumption record template, and forbidden field policy only; performs no decision write, approval consumption, marker write, browser launch, CDP connection, screenshot, DOM read, or artifact write)
- `chaseos runtime browser-cdp atomic-marker-writer-design [target_url] --gate-approval-id <id> --json` (reports future exclusive-create marker write algorithm, path constraints, marker template, and failure policy only; performs no approval consumption, marker directory creation, marker write, browser launch, CDP connection, screenshot, DOM read, or artifact write)
- `chaseos runtime browser-cdp isolated-browser-launcher-design [target_url] --gate-approval-id <id> --json` (reports future local-only throwaway-profile launcher contract only; performs no profile creation, browser process spawn, CDP port open, CDP connection, screenshot, DOM read, marker write, or artifact write)
- `chaseos runtime browser-cdp isolated-launcher-implementation-preflight [target_url] --gate-approval-id <id> --json` (reports live launcher/client code-path and opaque implementation metadata checks only; performs no profile creation, browser process spawn, CDP port open, CDP connection, screenshot, DOM read, marker write, or artifact write)
- `chaseos runtime provider probe primary --probe-mode live-preflight --write-approval-request --json` (writes a pending RPGL approval artifact only; no provider call)
- `chaseos runtime provider probe primary --probe-mode live-preflight --gate-approval-id <id> --json` (structurally validates an RPGL approval artifact only; no provider call)
- `chaseos runtime provider executor-spec primary --gate-approval-id <id> --json` (reports future live-probe executor preconditions only; validates artifact structure without executing or consuming approval)
- `chaseos scaffold project/workspace ...`
- `chaseos operate browser open/inspect/screenshot ...`
- `chaseos agent register ...`
- `chaseos agent lifecycle RUNTIME STATE --decision-ref ...`
- `chaseos runtime coordination-watch ...`
- `chaseos runtime coordination-watch-supervisor --action start|stop ...`
- `chaseos runtime coordination-watch-bootstrap --action install|apply|verify|unregister|handoff|reboot-verify|capture-success|reconcile-reboot-result|activation-report|remove ...`

Implementation note for runtimes: new gateway, Studio, lifecycle, setup, scaffold, provider, and browser-operation commands must add a named operation to `RUNTIME_OPERATION_POLICIES` and call `check_runtime_operation()` before side effects. Do not introduce a second permission path in a command handler.

### Layer 7 — Gateway Allowlists and Credential Boundary (active foothold)

`runtime/policy/gateway_allowlists.json` is the machine-readable allowlist source for:
- write-target categories
- task types
- external API identifiers
- control-plane transports
- credential reference forms

Gate helpers now fail closed when a write target, task type, external API, or control-plane transport is not explicitly listed. The canonical CLI exposes the policy through:
- `chaseos gate allowlists`
- `chaseos gate check-external-api <api-id>`
- `chaseos gate check-transport <transport>`
- `chaseos gate check-credential-reference <kind> <target>`

Setup/gateway credential boundary rule: setup state may record only env var names, keychain-style references, or template placeholders. It must never record raw API keys, tokens, passwords, webhook secrets, private keys, or pasted credential values. `runtime/setup_state.py` enforces this before writing `runtime/setup_state.json`; `setup provider/integration wizard --apply` and `setup set ...` surface an error instead of persisting the value.

---

## 4. What Is Documentation-Only (Not Yet Enforced by Force)

| Rule | Where documented | Enforcement gap |
|------|-----------------|-----------------|
| Required read order per session type | `CLAUDE.md`, `Session-Prompt-Patterns.md` | Agent instruction-following only |
| No self-authorized permission escalation | `Permission-Matrix.md`, `Agent-Control-Plane.md` | Agent instruction-following only |
| Trust tier ceilings | `Trust-Tiers.md` | Registry + agent discipline |
| Advisory surface write block | `Permission-Matrix.md` | Physical: no filesystem access |
| External API approval requirement | `Agent-Security-Model.md` | Agent instruction-following only |
| Credential exclusion from vault content | `Credential-Boundaries-SOP.md` | Agent discipline + credential scan hook (planned) |
| Writeback discipline | `CLAUDE.md`, `Build-Log-SOP.md` | Agent discipline + session-end reminder hook |

These rules are correctly documented. Mechanical enforcement requires extending the Gate with additional hook scripts or a full runtime policy engine (Phase 7).

---

## 5. The Multi-Provider Conformance Model

Every execution adapter must conform to the Gate. Conformance does not mean the same implementation — it means the same policy outcomes regardless of adapter.

### Conformance tiers

**Advisory surfaces (Claude Chat, ChatGPT, Grok, Perplexity, NotebookLM):**
- No vault write access — conformance is structural (no filesystem access)
- Gate conformance: none required (physically cannot violate vault policies)

**Planned harness adapters (OPENAI.md, LOCAL-OSS.md):**
- Must define an adapter manifest in `runtime/policy/adapters/`
- Must document their hook-equivalent enforcement mechanism (input/output validators, approval UI, sandbox)
- Manifests already created with planned status; enforcement is documentation-only until adapters are active

**Active harness adapter (Claude Code / CLAUDE.md):**
- Adapter manifest at `runtime/policy/adapters/claude.yaml`
- Hook scripts wired in `.claude/settings.json`
- Protected-file guard is the primary hard enforcement
- Build log reminder is active at session close

**Workflow runtime (N8N.md):**
- Must define a manifest in `runtime/policy/adapters/n8n.yaml`
- Enforces via workflow-scoped access (structural) + workflow error handling
- Cannot write to protected files — scoped out at the workflow level

---

## 6. Evolution Plan

| Phase | Gate Maturity |
|-------|-------------|
| Phase 6 | Claude hook backstops active; protected-file and ingestion-promotion guards hard-enforced |
| Phase 7/8 | Source Intelligence Core and capture automation completed; provenance minimums entered live promotion guard path |
| Phase 9 (current) | Canonical CLI exposes `gate`, `runtime`, `agent-bus`, `osril`, and `run`; adapter manifests validate through CLI; coordination-sensitive workflow preflight is active; deny-by-default runtime operation policy foothold active for agent-bus plus bounded setup/config/schedule/event dispatch/scaffold draft/SBP delivery/OSRIL approval/browser read-screenshot paths, runtime registry lifecycle mutations, and coordination-watch lifecycle/bootstrap host side-effect paths; gateway allowlists and setup credential-boundary checks are active footholds |
| Phase 9 hardening before Phase 10 | Expand deny-by-default policy across future concrete Gateway/Studio UI dispatches, browser actions beyond bounded read/screenshot, credential scan hook, adapter conformance checks for OpenAI/local/n8n/gateway lanes, and Core/Personal export manifest enforcement |
| Phase 10 | Studio/gateway UI must call the same policy checks and must not introduce a separate permission path |

---

## 7. Gate Activation — Completed Steps

All activation steps for the Anthropic lane are complete as of 2026-03-21.

1. ✅ **Hook scripts deployed** — `.claude/hooks/` (Phase 6 preflight)
2. ✅ **Hooks wired in settings.json** — project-level, using `.venv/Scripts/python.exe` (updated 2026-03-21)
3. ✅ **Code hardened** — stdin payload nesting fix; PyYAML graceful fallback (2026-03-21)
4. ✅ **Python runtime available** — repo-local venv at `.venv/Scripts/python.exe` (Python 3.13.12 + PyYAML 6.0.3)
5. ✅ **Hooks verified** — all 4 hooks tested with simulated payloads; blocking hooks exit 1 on violation, exit 0 on allow; notification hooks exit 0 always (2026-03-21)
6. ✅ **`runtime/policy/protected_files.yaml` in sync** — confirmed matches `Permission-Matrix.md` Section 2 (13 files)

**Ongoing maintenance requirement:** Keep `runtime/policy/protected_files.yaml` in sync with `Permission-Matrix.md` Section 2 whenever the protected-file list changes. The hook enforces the YAML — if they diverge, the hook enforces the wrong list.

---

*Graph links: [[Vault-Map]] · [[CLAUDE]] · [[Execution-Adapter-Standard]] · [[Permission-Matrix]] · [[Agent-Control-Plane]] · [[Agent-Security-Model]] · [[Trust-Tiers]] · [[Hook-Patterns]] · [[Adapter-Manifest-Standard]] · [[Backends-Supported]] · [[ROADMAP]] · [[OPENAI]] · [[LOCAL-OSS]] · [[N8N]]*

*ChaseOS-Gate.md — Version 1.1 | Created: 2026-03-20 | Phase 6 Preflight — Execution Control Layer | Updated: 2026-03-21 — Layer 1–4 status: ACTIVE VERIFIED; Section 7 updated with all activation steps complete*
