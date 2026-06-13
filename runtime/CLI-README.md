# runtime/ — CLI README

> Human-facing guide for the canonical ChaseOS CLI entrypoint and the compatibility shims that still exist around it.

---

## What This Is

The canonical ChaseOS operator CLI is now:
- `runtime.cli.main:main`

Installed script truth:
- `chaseos`
- `chase`

Compatibility shims still exist for direct invocation:
- `python chaseos.py ...`
- `python runtime/cli.py ...`

Those shims now import the same parser/dispatcher from `runtime.cli.main`; they are not a second command spine.

---

## Machine-readable Contract

The canonical CLI parser now has a stable machine-readable contract at:

```text
runtime/cli/command_contract.json
```

It records command families, command paths, args, option aliases, JSON result shapes, side effects, and maturity. Parser drift is checked by `runtime/tests/test_cli_command_contract.py`, which compares the contract against `runtime.cli.main:build_parser()`.

This contract is the source to use when automation, gateway code, or future Studio surfaces need to know what the CLI accepts without scraping help text.

Routine local CLI preflight:

```powershell
python -m runtime.cli.main doctor cli --json
python -m runtime.cli.main doctor cli --contract-ratchet-smoke --json
python -m runtime.cli.main test cli-contract --json
```

Use the first command as the fast entrypoint/shim check, the second before trusting parser/contract/docs/action/smoke alignment, and the third when running the ratchet directly.

The full ratchet's SiteOps candidate preflight smoke uses the packaged runtime fixture vault at `runtime/cli/fixtures/browser_skill_candidates_vault`, not historical live-vault candidate state or test-only fixture state.

Cross-family JSON smokes now use four expectation profiles:
- full governance smokes require standard status, blocked reason, writes, evidence, and authority fields where proof/approval/status commands naturally expose them
- read-only list/status/validate smokes require the canonical JSON envelope, exact action name, exit code `0`, and explicit per-command `result.*` paths
- expected-nonzero readiness smokes require the canonical JSON envelope, exact action name, the declared non-zero exit code, the declared `ok:false` posture, and explicit per-command `result.*` blocker/readiness paths
- optional live readiness smokes require the canonical JSON envelope, exact action name, read-only authority posture, explicit `result.*` gateway evidence, and accept either healthy exit `0` when a gateway is running or unavailable exit `1` when it is not

This lets the ratchet cover older read-only command families without falsely requiring proof-only or approval-only fields on simple inventory commands.

Current read-only ratchet expansion covers agent, Agent Bus, capture, config,
context, develop, events, Gate, intake, maintain, memory, schedule, models,
providers, OSRIL, SBP, watch, setup, operate, run, scorecard, and scaffold. The
setup family enters the smoke map through a fixture-backed `setup status --json`
smoke plus registry-only `setup provider list --json` and `setup integration
list --json` smokes. The capture/intake lane uses a packaged intake fixture
vault for `capture status --json`, `intake dedup-stats --json`, `intake ls
--json`, `capture validate --json`, and `intake inspect ... --json`. The
maintain lane uses both `maintain --status --json` as a fast preflight posture
and `maintain --dry-run --fixture-root runtime/cli/fixtures/maintain_vault
--json` as the bounded dry-run smoke so routine preflight never scans the live
vault. The developer lane enters only through `develop explain --dry-run
--json`. The run lane enters through `run operator_today --dry-run --json`,
which validates AOR workflow stages without handler execution, workflow
writeback, Agent Bus writes, or canonical writeback. `setup validate --json`
also uses the canonical envelope, but remains outside the smoke map because
normal incomplete setup state can return a non-zero validation exit. The first
expected-nonzero readiness smoke covers `core-export readiness --json`, which is
read-only in this workspace and should remain blocked until manual
review/verifier issues are clean; the ratchet now treats that blocked posture as
intentional instead of as a smoke failure.

The first optional live readiness smokes cover `health openclaw --json` and
`health hermes --json`. These checks do not start, stop, restart, or mutate any
gateway. They pass when the gateway is detected as healthy and also pass when
the gateway is unavailable, provided the command returns canonical JSON with
read-only evidence and a clean blocked/unavailable posture.

Session-scoped runtime health now has a read-only heartbeat reader. The ratchet
smokes `health codex --json` and `health archon --json` accept either a fresh
Agent Bus heartbeat as `healthy` or a missing/stale heartbeat as canonical
`unavailable` evidence. These checks open the existing heartbeat store in
read-only mode and do not create Agent Bus rows, claim tasks, or start workers.

The n8n readiness and dry-run closeout promotes both `n8n readiness --json` and
`n8n dry-run send_discord_draft_alert --caller chaseos_runtime_mcp --json` into
routine read-only smoke coverage. These commands never execute a workflow,
never make a live HTTP call, and never write draft artifacts during routine
preflight; they validate connection/registry posture and execution-adjacent
policy shape only.

Deferred smoke candidates are now explicit and closed in the ratchet output
under `deferred_smoke_commands`. Current permanent deferrals are live
`n8n execute` and mutating/external capture commands. They remain outside
routine smoke coverage by design because routine preflight must not execute
workflows, call connectors, fetch external data, write quarantine artifacts, or
mutate canonical state. Each deferred entry is mirrored in `deferred_closure_map`
with a `closed_...` status, blocker type, representative smoke, fixture
readiness note, forbidden ratchet actions, and promotion condition.

Generated operator docs now have two layers:
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md` is the machine/generated command-contract table
- `06_AGENTS/ChaseOS-CLI-Operator-Handbook.md` is the generated operator handbook with family sections, examples, safety posture, ratchet disposition, and real-world use cases

---

## Current Families Wired

### Runtime family
Canonical operator surface:
- `runtime.cli.main`

Lower-level compatibility/dev footholds still exist:
- `runtime/state/runtime_cli.py`

Examples:
```powershell
python runtime\cli.py runtime resolve
python runtime\cli.py runtime status
python runtime\cli.py runtime status --refresh --json
python runtime\cli.py runtime provider-status --runtime all --json
python runtime\cli.py runtime provider-status --runtime OpenClaw --probe-health --timeout 1 --json
python runtime\cli.py runtime surfaces summary --json
python runtime\cli.py runtime surfaces capabilities --surface agent.codex.bus --json
python runtime\cli.py runtime surfaces route-review --capability browser.click --json
python runtime\cli.py studio arsl-route-review-panel --capability browser.click --json
```

### Gate family
Canonical operator surface:
- `runtime.cli.main`

Examples:
```powershell
python runtime\cli.py gate validate
python runtime\cli.py gate list-adapters
python runtime\cli.py gate show-adapter openclaw
python runtime\cli.py gate check-write openclaw 07_LOGS/Agent-Activity/test.md
python runtime\cli.py gate check-task openclaw operator-briefing
```

Legacy compatibility aliases still accepted:
- `python runtime\cli.py gate list`
- `python runtime\cli.py gate show openclaw`

Current caveat:
- Gate policy still ultimately depends on the same runtime policy/python environment beneath the canonical CLI surface
- in the current environment, `PyYAML` is missing, so Gate family commands can fail until dependency alignment is fixed
- runtime-state commands currently compensate with a fallback parser; Gate does not yet

### Acquisition family
Canonical operator surface:
- `runtime.cli.main`

Examples:
```powershell
python runtime\cli.py acquisition preview-research --profile strikezone
python runtime\cli.py acquisition preview-research --profile strikezone --json
python runtime\cli.py acquisition preview-research --profile strikezone --write --json
python runtime\cli.py acquisition connector-health --json
python runtime\cli.py acquisition connector-health --connector perplexity --limit 10 --json
```

Current caveat:
- `preview-research` scans only declared local/import StrikeZone research drop folders under `runtime/acquisition/manual/strikezone/`
- default preview is read-only; `--write` writes runtime-local preview pack artifacts without updating `strikezone-latest.json`, delivering externally, or promoting content
- live network/email/Google acquisition remains on the separate `acquisition run` / `strikezone_acquisition` path and depends on configured sources and credentials
- `connector-health` is read-only and reports acquisition connector telemetry for Perplexity, Grok, RSS, web scrape, IMAP email, Google Docs, and Google Drive outcomes; it does not alter provider fallback state

### Events family
Canonical operator surface:
- `runtime.cli.main`

Examples:
```powershell
python runtime\cli.py events validate
python runtime\cli.py events rules
python runtime\cli.py events pending
python runtime\cli.py events emit acquisition.new_item --source-workflow strikezone_acquisition --subject runtime/acquisition/packs/strikezone-latest.json --subject-kind briefing_ready_input_set --dry-run
python runtime\cli.py events dispatch --pending
python runtime\cli.py events watch --once
python runtime\cli.py events watch --interval 30 --execute
python runtime\cli.py schedule show sch-events-watch-every-minute --json
python runtime\cli.py schedule export --adapter openclaw --json
```

Current caveat:
- `events dispatch` and `events watch` are dry-run by default; `--execute` is required before matching workflows are run
- the first live rule is `acquisition.new_item -> sbp_strikezone_digest`
- OpenClaw now exports an enabled command schedule for `events.watch`; the fixed 06:00 StrikeZone digest schedule is disabled so event dispatch does not double-run the digest

### Memory family
Canonical operator surface:
- `runtime.cli.main`

Examples:
```powershell
python runtime\cli.py memory status
python runtime\cli.py memory list
python runtime\cli.py memory show openclaw --json
python runtime\cli.py memory show claude --json
python runtime\cli.py memory tasks
python runtime\cli.py memory validate
```

Current caveat:
- the memory surface is read-only and advisory; it inspects Layer C runtime memory and Layer D task-local memory without mutating either layer
- Layer C now has seeded runtime profiles and repair memory for OpenClaw and Hermes
- Layer C now has a first formal Claude Agent Identity Ledger at `runtime/memory/adapters/claude/identity-ledger.json`
- Layer D has a live `runtime/tasks/` substrate, but there are currently no active task-local contexts

---

## Why This Matters

This file marks the point where ChaseOS command surfaces are now unified in practice, not only in architecture docs.

It supports the broader OS direction by moving from:
- subsystem-local scripts

toward:
- one canonical shell entrypoint
- live `chaseos runtime ...`
- live `chaseos gate ...`
- broader package-native CLI integration

---

## Current Boundary

The canonical CLI now owns the operator-facing parser tree, but the active live command families are still intentionally scoped.
This layer does not yet mean every historically documented ChaseOS command family is complete or equally mature.
It currently focuses on the strongest live footholds:
- runtime inspection
- provider/fallback governance status
- gate policy inspection
- vault-local event dispatch

But they are not equally mature yet:
- `runtime` family is operational through the canonical CLI and compatibility shims
- `runtime provider-status` is a read-only beta aggregation surface; it reports provider/model fallback posture, agent-bus queue/stuck/no-chunk posture, optional lifecycle probes, and provider-state ledger evidence for rate limits, cooldowns, fallback activation, and recovery-to-primary; shared execution-adapter paths, including Hermes review synthesis, now emit request/rate-limit/fallback/recovery-completed ledger evidence, while `runtime/providers/provider_call_surfaces.json` classifies Source Intelligence, connector/acquisition, delivery, setup/lifecycle, and OpenAI/n8n dry-run surfaces outside provider-state emission; acquisition connector outcomes report through connector health instead; the CLI does not enforce rate limits, cooldowns, provider switching, or recovery-to-primary
- `runtime surfaces` is a read-only ARSL inspection surface; it summarizes registered runtime surfaces, capability-policy records, and route-review posture without runtime dispatch, browser control, provider calls, credential access, raw manifest exposure, MCP tool exposure, ledger writes, approval grants, or canonical writeback. `route-review` previews routing posture only; it does not commit a route proposal or append the routing ledger.
- `gate` family is structurally wired into the canonical CLI, but Gate validity still depends on the active runtime policy environment beneath it
- `events` family is a beta substrate: rule validation and dry-run dispatch are active, while live execution remains explicit via `--execute`

That is the right Phase 9 scope.

---

## Recommended Operator Pattern

Use the canonical CLI first when you want the operator-facing command surface.

Recommended primary forms:
- `python -m runtime.cli.main ...`
- installed `chaseos ...` / `chase ...`

Use the compatibility shims only when direct script invocation is specifically needed.

Examples:
```powershell
python runtime\cli.py runtime status --refresh --json
python runtime\cli.py gate validate
```

If you need subsystem-specific docs, also read:
- `runtime/state/CLI-README.md`
- `runtime/COMMANDS.md`
- `CLI-SURFACES.md`
- `06_AGENTS/ChaseOS-CLI-Integration-Seam.md`
