---
title: ChaseOS Commands and CLI Surfaces
type: operator-guide
status: active
created: 2026-04-24
updated: 2026-05-09
---

# ChaseOS Commands and CLI Surfaces

> Canonical operator-facing inventory of current ChaseOS command surfaces.

---

## Purpose

This file gives ChaseOS one runtime-adjacent command inventory that operators can actually use.

It distinguishes between:
- directly inspectable command surfaces in this repository
- broader documented ChaseOS command families
- future intended command contracts

It should now also be read as a source for `command_availability_summary` and `command_maturity_summary` artifacts under `06_AGENTS/Runtime-Shell-and-Command-Surface-Summary-Context-Application.md`, so live, partial, documented, and intended command surfaces remain visibly distinct.

---

## 1. Directly Inspectable from This Repository

Canonical command-spine truth:
- installed `chaseos` / `chase` -> `runtime.cli.main:main`
- `python -m runtime.cli.main ...` -> canonical module form
- `python chaseos.py ...` -> compatibility shim into the same parser
- `python runtime\cli.py ...` -> compatibility shim into the same parser

When examples below use shim forms, read them as compatibility invocation paths, not as separate parser trees.

### Machine-readable CLI contract

The canonical parser surface now has a stable machine-readable contract:

```text
runtime/cli/command_contract.json
```

This file lists every canonical command path, command family, argument, option alias, JSON result shape, side-effect class, and maturity level. It is not a replacement for the human inventory in this file; it is the parser-facing contract that tests and future gateway/Studio callers can consume.

Contract conformance is guarded by:

```powershell
python -m pytest runtime\tests\test_cli_command_contract.py
```

The test suite compares the JSON contract against `runtime.cli.main:build_parser()` so parser changes must update the contract intentionally.

Routine local CLI preflight:

```powershell
python -m runtime.cli.main doctor cli --json
python -m runtime.cli.main doctor cli --contract-ratchet-smoke --json
python -m runtime.cli.main test cli-contract --json
```

Use the fast doctor command for entrypoint/shim health, the full doctor ratchet before trusting parser/contract/docs/action/smoke alignment, and the direct ratchet command when only CLI contract drift needs to be checked.

The full ratchet's SiteOps candidate preflight smoke uses the packaged runtime fixture vault at `runtime/cli/fixtures/browser_skill_candidates_vault`, not historical live-vault candidate state or test-only fixture state.

The ratchet uses four smoke expectation profiles:
- full governance JSON smokes for proof, approval, and status surfaces that should expose standard status, blocked reason, writes, evidence, and authority fields
- read-only result-path smokes for list/status/validate surfaces that should expose a valid JSON envelope, exact action name, successful exit, and a small set of command-specific `result.*` fields
- expected-nonzero readiness smokes for blocked-but-canonical read-only surfaces that should expose a valid JSON envelope, exact action name, declared non-zero exit code, declared `ok:false`, and command-specific blocker/readiness fields
- optional live readiness smokes for gateway probes that should expose a valid JSON envelope, exact action name, read-only authority posture, and command-specific gateway evidence while accepting either healthy exit `0` or unavailable exit `1`

The first read-only expansion batch covers `agent list`, `config summary`, `gate validate`, `memory status`, and `schedule validate`, expanding representative smoke coverage to 10 CLI families without adding provider calls, Agent Bus writes, Gate mutation, workflow execution, host mutation, Git mutation, secret reads, Pulse memory mutation, Personal Map mutation, R&D mutation, or canonical writeback.

The second read-only expansion batch adds `models list`, `providers status`,
`osril resume-ready --dry-run`, `sbp delivery-health`, and `watch list`.
The setup normalization pass added `setup status` to the read-only smoke map by
bridging setup's legacy `args.json` flag into the canonical CLI
`ok/action/result` envelope. The follow-on setup fixture pass now runs
`setup status` against packaged fixture state and adds registry-only
`setup provider list` and `setup integration list` smokes. `setup validate
--json` uses the same envelope, but remains outside smoke coverage because
incomplete local setup state can validly return a non-zero validation exit.

The third read-only expansion batch adds `agent-bus status`, `events validate`,
`events rules`, `context boot`, `operate browser policy`, `scorecard list`, and
no-write `scaffold project example`, bringing more mature non-mutating families
under routine smoke coverage.

The first expected-nonzero readiness smoke adds `core-export readiness --json`.
It is intentionally expected to return exit code `1` and `ok:false` while
preserving the canonical envelope, exact action, readiness status, blockers,
write posture, and export authority flags.

The first optional live readiness smokes add `health openclaw --json` and
`health hermes --json`. They never start, stop, restart, or mutate gateways.
They pass when the gateway is detected as healthy and also pass when the gateway
is unavailable, provided the CLI returns canonical read-only JSON with exact
gateway evidence and a clean unavailable posture.

Session-scoped runtime health now has read-only heartbeat smokes for
`health codex --json` and `health archon --json`. They read the existing Agent
Bus heartbeat store without initializing or writing it, then accept either a
fresh heartbeat as `healthy` or a missing/stale heartbeat as canonical
`unavailable` evidence.

The n8n readiness/dry-run closeout promotes both `n8n readiness --json` and
`n8n dry-run send_discord_draft_alert --caller chaseos_runtime_mcp --json` as
read-only n8n smokes. They do not execute workflows, do not make live HTTP
calls, and do not write draft artifacts during routine preflight. Readiness
checks connection/registry posture; dry-run checks execution-adjacent workflow
policy shape.

The fixture-required surface pass promotes `capture status --json`,
`capture validate --json`, `intake dedup-stats --json`, `intake ls --json`, and
`intake inspect ... --json` through a packaged intake fixture vault. It also
adds `maintain --status --json` as a fast read-only maintain posture and
`maintain --dry-run --fixture-root runtime/cli/fixtures/maintain_vault --json`
as the bounded fixture-root dry-run smoke, so routine preflight proves the
maintenance planning path without scanning or mutating the live vault. The
dry-run workflow pass promotes `run operator_today --dry-run --json` with
explicit `dry_run`, `writes_performed: false`, and authority flags. It validates
workflow stages without handler execution, workflow writeback, Agent Bus writes,
or canonical writeback. The ratchet still records explicit permanent deferrals
under `deferred_smoke_commands`: live n8n execute remains execution-adjacent,
and mutating/external capture commands stay excluded. Those same entries appear
in the generated `deferred_closure_map` with `closed_...` status, blocker type,
representative smoke coverage, fixture readiness, forbidden ratchet actions, and
promotion conditions.

The generated operator documentation now has two layers. The generated command
reference at `06_AGENTS/ChaseOS-CLI-Command-Reference.md` remains the raw
parser/contract table. The generated operator handbook at
`06_AGENTS/ChaseOS-CLI-Operator-Handbook.md` is the family-sectioned guide with
examples, safety posture, ratchet disposition, JSON posture, and practical
operator use cases.

### Gate command surface
```powershell
python runtime\chaseos_gate.py validate
python runtime\chaseos_gate.py list
python runtime\chaseos_gate.py allowlists
python runtime\chaseos_gate.py show <adapter-id>
python runtime\chaseos_gate.py check-write <adapter-id> <file-path>
python runtime\chaseos_gate.py check-task <adapter-id> <task-type>
python runtime\chaseos_gate.py check-external-api <api-id>
python runtime\chaseos_gate.py check-transport <transport>
python runtime\chaseos_gate.py check-credential-reference <kind> <target>
```

Current caveat:
- these commands are present and directly inspectable in the repo
- Gate now has a simple YAML fallback path when `PyYAML` is unavailable, so basic manifest-backed operations are more resilient
- richer YAML compatibility still benefits from `PyYAML`
- gateway allowlists now cover write-target categories, task types, external API ids, control-plane transports, and credential-reference forms

### Runtime-state resolution surface
```powershell
python runtime\state\resolver.py
```

### Runtime-state CLI foothold
```powershell
python runtime\state\runtime_cli.py resolve
python runtime\state\runtime_cli.py status
python runtime\state\runtime_cli.py status --refresh
python runtime\state\runtime_cli.py status --refresh --json
```

### Canonical operator CLI examples
```powershell
chaseos runtime resolve
chaseos runtime inventory --json
chaseos runtime status --json
chaseos runtime status --runtime all --json
chaseos runtime provider-status --runtime all --json
chaseos runtime provider-status --runtime OpenClaw --probe-health --timeout 1 --json
chaseos runtime adapter-governance --json
chaseos runtime providers --json
chaseos runtime fallback-status --json
chaseos runtime queue list --json
chaseos runtime queue show <queue_item_id> --json
chaseos runtime queue retry <queue_item_id> --dry-run --json
chaseos runtime provider probe primary --json
chaseos runtime provider probe fallback --json
chaseos runtime provider probe primary --probe-mode network-dry-run --json
chaseos runtime provider probe primary --probe-mode live-preflight --json
chaseos runtime provider probe primary --probe-mode live-preflight --write-approval-request --requested-by operator --json
chaseos runtime provider probe primary --probe-mode live-preflight --gate-approval-id <gate_approval_id> --json
chaseos runtime provider executor-spec primary --json
chaseos runtime provider executor-spec primary --gate-approval-id <gate_approval_id> --json
chaseos runtime provider live-probe-approval-decision primary --gate-approval-id <gate_approval_id> --decision approved|denied --json
chaseos runtime provider live-probe-approval-decision primary --gate-approval-id <gate_approval_id> --decision approved|denied --write-decision --json
chaseos runtime provider live-probe-decision-preflight primary --gate-approval-id <gate_approval_id> --json
chaseos runtime provider live-probe-marker-contract primary --gate-approval-id <gate_approval_id> --json
chaseos runtime provider live-probe-decision-consumer primary --gate-approval-id <gate_approval_id> --write-consumer-record --json
chaseos runtime provider live-probe-atomic-marker-writer primary --gate-approval-id <gate_approval_id> --write-consumption-marker --json
chaseos runtime provider live-probe-executor-dry-run primary --gate-approval-id <gate_approval_id> --json
chaseos runtime provider live-probe-target-approval-plan all --json
chaseos runtime provider live-probe-target-approval-plan primary --write-approval-request --requested-by operator --json
chaseos runtime provider live-smoke-readiness --json
chaseos runtime provider live-smoke-closeout-plan --json
chaseos runtime provider completion-status --json
chaseos runtime provider live-probe-executor primary --gate-approval-id <gate_approval_id> --execute-live-probe --json
chaseos runtime provider fallback-timeout-proof no-chunks --runtime openclaw --json
chaseos runtime provider ollama-timeout-contract success --runtime openclaw --json
chaseos runtime browser-cdp approval-request http://127.0.0.1:4173 --runtime Codex --requested-by operator --write-approval-request --json
chaseos runtime browser-cdp approval-request --gate-approval-id <gate_approval_id> --json
chaseos runtime browser-cdp executor-spec http://127.0.0.1:4173 --runtime Codex --json
chaseos runtime browser-cdp executor-spec --gate-approval-id <gate_approval_id> --json
chaseos runtime browser-cdp decision-preflight http://127.0.0.1:4173 --runtime Codex --gate-approval-id <gate_approval_id> --json
chaseos runtime browser-cdp idempotency-reservation-spec http://127.0.0.1:4173 --runtime Codex --gate-approval-id <gate_approval_id> --json
chaseos runtime browser-cdp executor-dry-run http://127.0.0.1:4173 --runtime Codex --gate-approval-id <gate_approval_id> --json
chaseos runtime browser-cdp approval-decision-policy http://127.0.0.1:4173 --runtime Codex --gate-approval-id <gate_approval_id> --json
chaseos runtime browser-cdp approval-decision-consumer-design http://127.0.0.1:4173 --runtime Codex --gate-approval-id <gate_approval_id> --json
chaseos runtime browser-cdp atomic-marker-writer-design http://127.0.0.1:4173 --runtime Codex --gate-approval-id <gate_approval_id> --json
chaseos runtime browser-cdp isolated-browser-launcher-design http://127.0.0.1:4173 --runtime Codex --gate-approval-id <gate_approval_id> --json
chaseos runtime browser-cdp isolated-launcher-implementation-preflight http://127.0.0.1:4173 --runtime Codex --gate-approval-id <gate_approval_id> --json
chaseos runtime browser-cdp closeout-readiness http://127.0.0.1:4173 --runtime Hermes --gate-approval-id <gate_approval_id> --json
chaseos runtime browser-cdp approval-decision --gate-approval-id <gate_approval_id> --requested-by operator --write-approval-decision --decision approved --json
chaseos runtime browser-cdp execute http://127.0.0.1:4173 --runtime Hermes --gate-approval-id <gate_approval_id> --json
chaseos runtime provider config-report --json
chaseos runtime provider target-profile --json
chaseos runtime provider target-profile-plan [MODEL] --json
chaseos runtime provider target-profile-plan gpt-5.5 --write-approval-request --requested-by operator --json
chaseos runtime provider config-plan --json
chaseos runtime provider config-plan --write-approval-request --requested-by operator --json
chaseos runtime provider config-apply-preflight <proposal_id> --json
chaseos runtime provider config-apply-design <proposal_id> --json
chaseos runtime provider config-apply-approval-request <proposal_id> --write-approval-request --requested-by operator --json
chaseos runtime provider config-apply-approval-request <proposal_id> --gate-approval-id <id> --json
chaseos runtime provider config-apply-approval-decision <proposal_id> --gate-approval-id <id> --decision approved|denied --json
chaseos runtime provider config-apply-approval-decision <proposal_id> --gate-approval-id <id> --decision approved|denied --write-decision --json
chaseos runtime provider config-apply-decision-preflight <proposal_id> --gate-approval-id <id> --json
chaseos runtime provider config-apply-decision-consumption-plan <proposal_id> --gate-approval-id <id> --json
chaseos runtime provider config-apply-decision-consumer-design <proposal_id> --gate-approval-id <id> --json
chaseos runtime provider config-apply-decision-consumer-preflight <proposal_id> --gate-approval-id <id> --json
chaseos runtime provider config-apply-decision-consumer-implementation-plan <proposal_id> --gate-approval-id <id> --json
chaseos runtime provider config-apply-decision-consumer-writer-dry-run <proposal_id> --gate-approval-id <id> --json
chaseos runtime provider config-apply-decision-consumer-write-guard-contract <proposal_id> --gate-approval-id <id> --json
chaseos runtime provider config-apply-decision-consumer <proposal_id> --gate-approval-id <id> --write-consumer-record --json
chaseos runtime provider config-apply-atomic-marker-writer <proposal_id> --gate-approval-id <id> --write-consumption-marker --json
chaseos runtime provider config-apply-atomic-marker-writer-design <proposal_id> --gate-approval-id <id> --json
chaseos runtime provider config-apply-executor <proposal_id> --gate-approval-id <id> --apply-provider-config --json
chaseos runtime provider config-apply-executor-dry-run <proposal_id> --gate-approval-id <id> --json
chaseos gate check-operation runtime.provider.config_apply --json
chaseos gate check-operation runtime.provider.live_probe --external-api provider.openai --json
chaseos runtime recover --dry-run --json
chaseos runtime audit-tail --limit 20 --json
chaseos runtime health --runtime all --json
chaseos runtime health-debug --runtime all --json
chaseos runtime coordination-watch --runtime Hermes --once --json
chaseos runtime coordination-watch --runtime OpenClaw --interval 30
chaseos runtime coordination-watch-supervisor --runtime Hermes --action plan --json
chaseos runtime coordination-watch-supervisor --runtime Hermes --action status --json
chaseos runtime coordination-watch-supervisor --runtime Hermes --action start
chaseos runtime coordination-watch-supervisor --runtime Hermes --action stop
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action plan --json
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action status --json
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action install
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action apply --json
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action verify --json
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action handoff --json
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action reboot-verify --json
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action capture-success --json
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action reconcile-reboot-result --json
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action status --json   # now includes event_log_path + latest_event when present
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action activation-checklist --json
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action unregister
chaseos runtime coordination-watch-bootstrap --runtime Hermes --action remove
chaseos setup status --json
chaseos setup validate --json
chaseos setup set provider openai configured=true api_key_present=true secret_reference_present=true secret_reference_kind=env-var secret_reference_target=OPENAI_API_KEY default_model=gpt-5 reasoning_policy=balanced --dry-run --json
chaseos setup set provider openai configured=true api_key_present=true secret_reference_present=true secret_reference_kind=env-var secret_reference_target=OPENAI_API_KEY default_model=gpt-5 reasoning_policy=balanced --json
chaseos setup provider list --json
chaseos setup provider show openai --json
chaseos setup provider validate openai --json
chaseos mvp credential-handoff --json
chaseos setup provider validate claude --json
chaseos setup provider validate local_oss --json
chaseos setup provider wizard claude --json
chaseos setup provider wizard openai --apply --json
chaseos setup integration list --json
chaseos setup integration validate discord --json
chaseos setup integration validate telegram --json
chaseos setup integration validate slack --json
chaseos setup discord validate --json
chaseos setup menu
chaseos gate validate
chaseos gate allowlists --json
chaseos gate check-external-api provider.openai --json
chaseos gate check-transport runtime/agent_bus/ --json
chaseos gate check-credential-reference env-var OPENAI_API_KEY --json
chaseos providers list --json
chaseos providers status --json
chaseos models list --json
chaseos config list --json
chaseos config validate --json
chaseos config summary --json
chaseos config set default_provider openai --json
chaseos scaffold project "Alpha Core" --json
chaseos scaffold workspace "Signal Lab" --write --json
chaseos agent list --json
chaseos agent status openclaw --json
chaseos agent lifecycle hermes --json
chaseos agent register custom-provider local-runner --runtime-id custom-local --json
chaseos sbp delivery-health --json
chaseos sbp delivery-health --adapter discord --limit 10 --json
chaseos osril resume-ready --dry-run --json
chaseos osril resume-ready APPROVAL_ID --json
chaseos acquisition connector-health --json
chaseos acquisition connector-health --connector perplexity --limit 10 --json
chaseos acquisition init-research-repository --profile strikezone --json
chaseos acquisition init-research-repository --profile strikezone --confirm-action --json
chaseos acquisition import-research-inbox --profile strikezone --json
chaseos acquisition import-research-inbox --profile strikezone --confirm-action --json
chaseos acquisition preview-research --profile strikezone --json
chaseos acquisition preview-research --profile strikezone --write --json
chaseos siteops list --json
chaseos siteops list --type workflow --json
chaseos siteops show canva.poster.magic_layers --json
chaseos siteops validate --json
chaseos siteops dry-run canva.poster.magic_layers --input source_image_path=sample.png --input edit_prompt="make it ChaseOS branded" --json
chaseos siteops dry-run perplexity.research.capture --input query="ETH 4H setup" --json
chaseos siteops dry-run tradingview.idea.capture --input idea_url="https://www.tradingview.com/chart/example" --write-audit --json
chaseos siteops catalog list --json
chaseos siteops catalog show canva.poster.magic_layers --json
chaseos siteops tenants list --json
chaseos siteops skills list --tenant local --json
chaseos siteops workflows list --tenant local --json
chaseos siteops workflows dry-run perplexity.research.capture --tenant local --user local-user --input query="ETH 4H setup" --json
chaseos siteops runs list --tenant local --json
chaseos siteops approvals list --tenant local --json
chaseos siteops credentials check local-gemini-api-credential --tenant local --user local-user --json
chaseos siteops browser-profiles check local-user-canva-browser --tenant local --user local-user --json
chaseos siteops budgets check --provider gemini_image --tenant local --estimated-cost 0.0300 --json
chaseos studio acquisition-cockpit --profile strikezone --json
chaseos studio acquisition-cockpit --profile strikezone --output-html runtime/studio/out/acquisition-cockpit.html --json
chaseos studio acquisition-cockpit-app --profile strikezone --dry-run --json
chaseos studio acquisition-cockpit-app --profile strikezone --host 127.0.0.1 --port 8765
chaseos studio acquisition-cockpit --profile strikezone --action import-inbox --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --action preview-write --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --action promote-reviewed-preview --briefing-input <preview-bris> --reviewed --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --action verify-research-sbp --json
chaseos events validate
chaseos events rules
chaseos events pending
chaseos events emit acquisition.new_item --source-workflow strikezone_acquisition --subject runtime/acquisition/packs/strikezone-latest.json --subject-kind briefing_ready_input_set --dry-run
chaseos events dispatch --pending
chaseos events dispatch --pending --execute
chaseos events watch --once
chaseos events watch --interval 30 --execute
chaseos schedule show sch-events-watch-every-minute --json
chaseos schedule export --adapter openclaw --json
chaseos memory status
chaseos memory summary --json
chaseos operate browser policy --json
chaseos memory list
chaseos memory show openclaw --json
chaseos memory show claude --json
chaseos memory tasks
chaseos memory validate
chaseos agent-bus status
chaseos agent-bus runtimes
chaseos agent-bus route operator-briefing
chaseos agent-bus heartbeat --runtime OpenClaw --status busy --health ok
chaseos agent-bus heartbeat --runtime Axiom-Codex --status idle --health ok
chaseos agent-bus heartbeat --runtime Hermes --status busy --health ok --runtime-instance-id discord-thread-1496197360382906398 --heartbeat-scope instance --control-surface discord --control-surface-key "discord:1493226848409358426:1496197360382906398"
chaseos agent-bus ingress discord --to OpenClaw --request "Coordinate review execution" --expected-output "Structured review result" --source-channel-id 1493226873080119397 --source-thread-id 1496197360382906398 --origin-message-id 1497000000000000001 --coordination-sensitive
chaseos agent-bus task create --sender Hermes --to OpenClaw --intent TASK --priority normal --request "..." --expected-output "..."
chaseos agent-bus task create --sender Hermes --to OpenClaw --request "..." --expected-output "..." --source-platform discord --source-channel-id 1493226848409358426 --source-thread-id 1496197360382906398 --source-channel-class runtime-chat --origin-message-id 1497000000000000001 --control-plane-route "discord:1493226848409358426:1496197360382906398"
chaseos agent-bus task list --to OpenClaw --status open --limit 20
chaseos agent-bus task list --to FutureRuntime --owner FutureRuntime --status open --limit 20 --json
chaseos agent-bus task claim <task-id> --runtime OpenClaw
chaseos agent-bus task update <task-id> --runtime OpenClaw --status in_progress --event-type started --message "..."
python chaseos.py agent-bus task cleanup --runtime Hermes --to OpenClaw --sender Hermes --status open --request-exact test --limit 20 --json
python chaseos.py agent-bus task cleanup --runtime Hermes --to OpenClaw --status open --conversation-key discord:1493226848409358426:1496197360382906398 --limit 10 --json
python chaseos.py agent-bus task cleanup --runtime Hermes --to OpenClaw --status open --work-fingerprint discord:OpenClaw:message-001 --limit 1 --apply --reason "Queue hygiene cleanup"

# Cleanup JSON reports total backlog size separately from the limited selected payload: matched_count/matched_task_ids vs selected_count/selected_tasks/selected_task_ids.
# Cleanup lane filters can target ingress identity with --work-fingerprint, --conversation-key, or --origin-message-id.
# Cleanup mutation is fail-closed: --apply requires an explicit --status open filter.
chaseos agent-bus task reclaim <task-id> --runtime Hermes --reason "..."
chaseos agent-bus watch --runtime Hermes --once --runtime-instance-id discord-thread-1496197360382906398 --control-surface discord --control-surface-key "discord:1493226848409358426:1496197360382906398"
chaseos agent-bus watch --runtime OpenClaw --interval 30 --claim-next --runtime-instance-id openclaw-discord-worker --control-surface discord --control-surface-key "discord:1493226848409358426"

# Canonical smoke tests use a disposable bus backend:
python chaseos.py agent-bus task create ... --vault-root <temp-vault> --json
python chaseos.py agent-bus ingress discord ... --vault-root <temp-vault> --json
```

### Compatibility shim examples
```powershell
python -m runtime.cli.main runtime resolve
python chaseos.py runtime resolve
python runtime\cli.py runtime resolve
```

Legacy transitional alias:
```powershell
python chaseos.py health openclaw
```

Current caveat:
- the promoted `runtime` path is working cleanly
- the promoted `providers` / `models` path now exists for provider inventory, provider readiness, and model-binding inspection against the runtime-shell registry/setup substrate
- the promoted `config` path now exists for bounded non-secret operator preferences through `.chaseos/config.yaml`, with `chaseos config list`, read-only `chaseos config validate`, read-only `chaseos config summary`, and `chaseos config set` failing closed on unknown keys; validation reports ready/blocked posture, allowed schema keys, invalid values, unsafe paths, and secret-like key placement without mutating config, while summary composes config validation, provider readiness, runtime defaults, attention items, next actions, and governance boundaries without provider switching or lifecycle authority
- the promoted `scaffold` path now exists in first bounded form for `project` and `workspace`, writing draft-only artifacts under `runtime/scaffold/generated/` rather than mutating canonical operating surfaces directly
- the first promoted `agent` onboarding path now exists for `list`, `register`, `status`, and `lifecycle` against the runtime registry substrate
- the promoted `sbp delivery-health` path now exists as a read-only delivery telemetry report over `runtime/sbp/state/delivery_health_events.jsonl`; Discord webhook and Whop forum-post delivery outcomes write success/failure events there instead of polluting provider-state fallback governance
- the promoted `osril resume-ready` path now exists as a bounded one-shot approved-resume runner; `--dry-run` plans only, non-dry runs require the `osril.approval_resume` Gate operation, and execution still flows through AOR's existing `operator_approval_ref` approval gate
- the promoted `acquisition connector-health` path now exists as a read-only acquisition telemetry report over `runtime/acquisition/state/connector_health_events.jsonl`; Perplexity, Grok, RSS, web scrape, IMAP email, Google Docs, and Google Drive live-source outcomes write success/failure/skipped events there instead of polluting provider-state fallback governance
- the promoted `acquisition init-research-repository` path now exists for fresh user machines; default mode is dry-run, and `--confirm-action` creates only the reusable StrikeZone local research folder layout, `_inbox` folders, README/example files, `.gitkeep` placeholders, and templates without creating source research files, preview packs, browser/provider calls, delivery, schedules, latest pointers, or canonical notes
- the promoted `acquisition preview-research` path now exists for local/import-only StrikeZone research drop folders under `runtime/acquisition/manual/strikezone/`; default preview is read-only, and `--write` writes runtime-local preview pack artifacts without latest-pointer, delivery, or canonical promotion authority
- the promoted `acquisition import-research-inbox` path now exists for local automation staging under `runtime/acquisition/manual/strikezone/_inbox/<source_class>/`; default mode is dry-run, and `--confirm-action` copies supported files into declared source-class folders and appends `runtime/acquisition/state/strikezone-research-inbox-imports.jsonl` without browser, MCP, provider, delivery, scheduler, deletion, or canonical vault mutation authority
- the promoted `siteops` path now exists as a dry-run-only Website Workflow Index / Site Skills production scaffold; compatibility commands still cover `list|show|validate|dry-run`, while production-shaped commands cover catalog, tenants, skills, workflows, runs, approvals, credentials, browser profiles, and budgets with `tenant_id=local`, `workspace_id=default`, and `user_id=local-user` as the local compatibility scope; scoped dry-run artifacts now write under `07_LOGS/SiteOps-Runs/`, `07_LOGS/SiteOps-Audits/`, and `07_LOGS/SiteOps-Approvals/`, but the surface still does not launch browsers, call provider APIs, authenticate sessions, publish, purchase, delete, change billing/account settings, place trades, or promote outputs into canonical knowledge
- the promoted `studio acquisition-cockpit` path now wraps Phase 10A0 acquisition controls as governed local-only actions: `--action import-file`, `import-inbox`, `preview-read-only`, `preview-write`, `promote-reviewed-preview`, and `verify-research-sbp`; the model also exposes `rehearsal` and `manual_test_readiness` so the remaining work is explicit before manual real-file testing; write actions require `--confirm-action`, remain limited to declared local/import, inbox-ledger, or runtime/acquisition pack paths, and add no browser, MCP, provider, delivery, cron, or canonical vault mutation authority
- the promoted `studio acquisition-cockpit-app` path now serves the Phase 10A0 cockpit as a localhost-only visual wrapper over the existing Studio acquisition cockpit model/action layer; `--dry-run` returns the server plan, non-dry runs bind only to loopback, app POST actions append local audit events, the app renders recent sanitized local action attempts, and the surface adds no browser automation, MCP/provider calls, delivery, scheduler, or canonical writeback authority
- the promoted `events` path now exists for vault-local event envelopes, YAML dispatch rules, pending-event inspection, dry-run dispatch, and explicit `--execute` workflow dispatch; the first pilot rule maps `acquisition.new_item` from `strikezone_acquisition` to `sbp_strikezone_digest`
- `sch-events-watch-every-minute` now wires that event dispatch loop into OpenClaw schedule export as an allowlisted command schedule (`chaseos events watch --once --execute`); the old fixed `sch-sbp-strikezone-digest-0600` schedule is disabled to avoid double-running the digest after acquisition succeeds
- the promoted `memory` path now exists as a read-only Layer C/D inspector over runtime profiles, identity ledgers, navigation overlays, scorecards, execution repair memory, and active task-local memory contexts; `chaseos memory summary` now consolidates validation, runtime-family coverage, task-context counts, governance boundaries, attention items, and next actions; memory remains advisory-only and does not mutate memory or override Gate authority
- `runtime browser-cdp execute` now implements the bounded approved read-only CDP proof path: it requires an approved matching artifact, consumes the decision once, writes an atomic marker, launches a throwaway local Chromium-compatible profile, uses a minimal local-only CDP client, and writes only declared proof artifacts; on this WSL host operational activation is verified with user-local Chromium and a throwaway approved localhost smoke that produced screenshot/DOM proof artifacts.
- the promoted `operate browser policy` path now exists as a read-only FSOS browser authority report; it exposes promoted CLI commands, effective approval-required action classes from shared defaults plus adapter policy, adapter-supported-but-unpromoted primitives, governance flags, write surfaces, known limitations, and next actions without launching a browser or widening click/form/download/authenticated-session authority
- the promoted `agent-bus` path is now live enough for status, runtimes, route, heartbeat, task creation, claim, update, cleanup, and reclaim-surface flows
- the promoted `agent-bus` path is now covered by canonical top-level smoke tests for task creation, Discord ingress translation, heartbeat, watch/claim, reclaim, and cancellation; those tests run with `--vault-root` pointing at a disposable vault and assert the live bus database is not polluted by the smoke marker
- the promoted top-level `agent-bus heartbeat` path now also exposes instance-aware publication fields (`--runtime-instance-id`, `--heartbeat-scope`, `--control-surface`, `--control-surface-key`) instead of flattening all heartbeat publication to runtime-only scope
- the promoted `agent-bus ingress discord ...` path now exists for bounded Discord/control-plane request translation into bus-owned task state when the bound channel posture allows it
- the same ingress translation path now resolves the live bound Discord channel map, keeps runtime-chat advisory by default, and only creates a bus task when the request is explicitly classified coordination-sensitive
- `agent-bus task create` now also accepts Discord/lane ingress metadata (`--source-platform`, `--source-channel-id`, `--source-thread-id`, `--source-channel-class`, `--conversation-key`, `--origin-message-id`, `--control-plane-route`) plus optional `--work-fingerprint` so coordination-sensitive ingress can be translated into structured bus state earlier
- for Discord ingress, ChaseOS now derives `conversation_key` automatically from channel/thread identity and derives a default fingerprint from `origin_message_id` when the caller has not supplied one explicitly
- the same ingress-aware create surface now exists both in the promoted top-level shell (`chaseos.py`) and the canonical runtime shell (`runtime/cli/main.py`) instead of only wrapper-level forwarding
- active duplicate task creation for the same recipient + `work_fingerprint` now fails closed instead of silently creating competing mirrored work items across lanes
- the Agent Bus task/event JSON schemas now use generic runtime identity fields instead of Hermes/OpenClaw-only enums; seeded examples still use Hermes/OpenClaw, but schema-level interoperability no longer blocks future runtime instances
- the promoted `runtime coordination-watch` path now exists as a lifecycle-backed launcher for one-shot or repeating bus refresh loops per runtime
- the promoted `runtime coordination-watch-supervisor` path now exists as a lifecycle-backed bootstrap/supervision foothold for planning, starting, inspecting, and stopping bounded background coordination loops per runtime
- the promoted `runtime coordination-watch-bootstrap` path now exists as a lifecycle-backed registration-artifact foothold for planning, installing, inspecting, and removing host-startup artifacts per runtime
- the same bootstrap path now also exposes host-apply / host-verify / host-unregister actions against the declared Task Scheduler commands, while still failing honestly when the current shell lacks permission
- the same bootstrap path can now emit a ready-to-run elevated handoff bundle so a privilege-bounded shell can hand scheduler mutation off to an explicit PowerShell/UAC step instead of overclaiming startup ownership
- the same bootstrap path now also appends structured runtime bootstrap event records so later status/audit surfaces can see the latest registration/handoff/remove action even after artifacts are cleaned up
- the same bootstrap path can now emit bounded reboot-verification bundles so ChaseOS can define the post-registration checks that should be run after a successful elevated registration and host restart/logon, plus a host-side JSON result artifact path for the observed outcome; the generated verifier now requires a zero scheduler-query exit code and expected task-name evidence before `scheduler_registered` can be true
- the same bootstrap path can now capture a durable success-state record from currently observed scheduler + supervisor evidence, preferring a host-written reboot verification result only when that result matches the expected runtime/task identity; mismatched reboot-result JSON is rejected instead of counted as proof
- `reconcile-reboot-result` now exists as an explicit operator-facing alias for that reboot-result preference path
- `activation-report` now separates live liveness readiness from full activation proof: `proof_complete` and `activation_state: proven` require scheduler registration, running supervisor, fresh heartbeat, validated success-state evidence, and validated reboot-verification evidence together
- `activation-checklist` now maps the same proof evidence into an ordered operator checklist with the current step, ready commands, host/elevation-required steps, missing evidence, and evidence paths; it is read-only and does not install, register, start, stop, or mutate scheduler state
- when `capture-success` observes confirmed scheduler + supervisor success together, it also writes an Agent Activity markdown record into `07_LOGS/Agent-Activity/`
- coordination-watch run, supervisor start/stop, and bootstrap side-effect actions now pass through named deny-by-default Gate runtime operations before process, scheduler, or lifecycle-state effects
- runtime inventory, status, health, and health-debug now model a multi-runtime machine rather than assuming only one runtime exists
- runtime provider-status now gives a read-only control-plane snapshot across runtime model configs, provider setup state, agent-bus queued/stuck/no-chunk posture, fallback-chain declarations, optional lifecycle adapter probes, and the provider-state ledger at `runtime/providers/state/provider_state_events.jsonl`; it reports rate-limit, cooldown, fallback, and recovery-to-primary evidence from ledger events, and shared execution-adapter paths, including Hermes review synthesis, now emit request/rate-limit/fallback/recovery-completed evidence; `runtime/providers/provider_call_surfaces.json` now classifies adjacent provider-like surfaces so Source Intelligence, capture/acquisition connectors, delivery, setup/lifecycle probes, and OpenAI/n8n dry-run adapters are not treated as provider-state emitters, while acquisition connector outcomes report through connector health; it still does not switch providers, enforce cooldowns, or perform recovery
- RPGL (`runtime/providers/governance_layer.py`) now adds governed provider-strength classification, task-class capability gating, weak-fallback denial for high-authority work, queue-on-denial records, fallback timeout decisions, simulated local fallback timeout proof, local Ollama streaming timeout wrapper contract with injected stream runner, queue retry package dry-run proof, provider audit events, primary cooldown/recovery state, metadata-only `--probe-mode network-dry-run` provider probe plans, denied-by-default `--probe-mode live-preflight` contracts, Gate approval schema exposure for `runtime.provider.live_probe` and `runtime.provider.config_apply`, pending live-probe approval artifacts under `07_LOGS/Agent-Activity/_rpgl_provider_approvals/`, target-profile-aware live-probe approval planning/request writing, immutable live-probe approval decision records under `07_LOGS/Agent-Activity/_rpgl_provider_live_probe_decisions/`, live-probe approval decision CLI preview/write, live-probe decision preflight, live-probe marker contract under `runtime/providers/state/provider_live_probe_markers/`, guarded live-probe decision consumer records under `07_LOGS/Agent-Activity/_rpgl_provider_live_probe_consumers/`, guarded live-probe atomic marker writes under `runtime/providers/state/provider_live_probe_markers/`, non-network live-probe executor dry-run/readiness reports, read-only live-smoke readiness reports, read-only live-smoke closeout plans, guarded live-probe executor result records under `runtime/providers/state/provider_live_probe_results/`, provider config apply approval artifacts under `07_LOGS/Agent-Activity/_rpgl_provider_config_apply_approvals/`, immutable provider config apply approval decision records under `07_LOGS/Agent-Activity/_rpgl_provider_config_apply_decisions/`, structural approval artifact validation, provider config apply immutable decision-record validation/idempotency preflight, provider config apply decision consumption plan, provider config apply decision consumer design, provider config apply decision consumer invocation preflight, provider config apply decision consumer implementation plan, provider config apply decision consumer writer dry-run, provider config apply decision consumer write-guard contract, guarded provider config apply decision consumer record writer, guarded provider config apply atomic marker writer, provider config apply atomic marker writer design, provider config apply executor dry-run plan, read-only provider config reconciliation/plan/preflight/design surfaces, runtime adapter-governance RPGL consumption checks, and `chaseos runtime adapter-governance|providers|fallback-status|queue|provider probe|provider fallback-timeout-proof|provider ollama-timeout-contract|provider live-probe-target-approval-plan|provider live-probe-approval-decision|provider live-probe-decision-preflight|provider live-probe-marker-contract|provider live-probe-decision-consumer|provider live-probe-atomic-marker-writer|provider live-probe-executor-dry-run|provider live-smoke-readiness|provider live-smoke-closeout-plan|provider live-probe-executor|provider config-report|provider config-plan|provider config-apply-preflight|provider config-apply-design|provider config-apply-approval-request|provider config-apply-approval-decision|provider config-apply-decision-preflight|provider config-apply-decision-consumption-plan|provider config-apply-decision-consumer-design|provider config-apply-decision-consumer-preflight|provider config-apply-decision-consumer-implementation-plan|provider config-apply-decision-consumer-writer-dry-run|provider config-apply-decision-consumer-write-guard-contract|provider config-apply-decision-consumer|provider config-apply-atomic-marker-writer|provider config-apply-atomic-marker-writer-design|provider config-apply-executor-dry-run|recover --dry-run|audit-tail`
- governed recovery-to-primary now has the design contract at `runtime/providers/RECOVERY-TO-PRIMARY.md` and a partial implemented foundation in `06_AGENTS/Runtime-Provider-Governance-Layer.md`; RPGL approval artifacts can be written/validated only as non-executing preflight records, no live queue-drain/apply command exists yet, Discord command mappings are documented but not wired as live slash commands, and any future provider-network probe or automatic retry execution must be separate from read-only `provider-status`, Gate-governed, auditable, and operator-approved
- runtime provider-status also includes an adjacent `adapter_health_rollup` over acquisition connector-health and SBP delivery-health ledgers; this reports connector/delivery failures and skips without feeding provider-state fallback governance
- runtime provider-status also includes a presentation-only `operator_summary` with status cards, attention items, and recommended next actions for operator/Studio wrapping; this summary has no provider-switching, cooldown, recovery, or adapter-retry authority
- runtime health uses runtime-specific lifecycle probe contracts with visible candidate ports and candidate URLs
- `health-debug` exists as a CLI-visible diagnostic seam so root-cause checks stay inside the command tree instead of drifting into ad hoc scripts
- `chaseos agent-bus heartbeats must still respect the current SQLite enum contract (`idle|busy|blocked|offline`), so ingress helpers should normalize any friendlier status wording before write
- `agent-bus watch` now supports both one-shot refresh and a long-running ChaseOS-owned interval loop (`python chaseos.py agent-bus watch --runtime <runtime-or-capability-alias> --interval N [--claim-next] [--runtime-instance-id INSTANCE] [--control-surface SURFACE] [--control-surface-key KEY]`); aliases such as `Axiom-Codex` are accepted at the canonical parser boundary and normalized for Gate/bus handling, while explicit instance/control-surface fields are preserved into heartbeat publication.
- `task reclaim` correctly refuses non-active tasks, which is good
- stale expiry has been hardened so active work is no longer expired by age alone, and heartbeat staleness is no longer inferred from the task-age threshold
- smoke tests that create bus tasks should keep using a test backend/temp vault or auto-cancel with a known cleanup message; the canonical regression file now enforces both behaviors for the new smoke path
- focused bus regression coverage now passes for this hardening path (`python -m pytest runtime/agent_bus/test_agent_bus.py -q`)
- the fallback capability parser now fails closed on malformed manifests, and router coverage passes (`python -m pytest runtime/agent_bus/test_capabilities_router.py -q`)
- the focused AOR review coordination lane now also passes without `PyYAML` by combining bounded fallback parsing with lazy workflow-handler resolution in `runtime/aor/engine.py`
- validated AOR/agent-bus review-path e2e coverage now passes (`python -m pytest runtime/agent_bus/test_bus_coordination_e2e.py -q`)

---

## 2. Broader Documented ChaseOS Command Families

These command families are part of the broader ChaseOS framework story and implementation history, but their exact local availability depends on the active implementation environment.

```text
chaseos capture ...
chaseos intake ...
chaseos watch ...
chaseos doctor
chaseos test capture
chaseos run <workflow>
chaseos setup ...
```

Recommended next command family after the current runtime/gate promotion work:
- `chaseos setup ...`
  - provider setup (`claude`, `openai`, `local_oss`, `n8n`)
  - integration setup (`discord`, `telegram`, `slack`)
  - menu-driven onboarding and validation flows

---

## 3. Future Intended Runtime Command Contract

### Inspection
```text
chaseos runtime resolve
chaseos runtime status
```

These are currently represented locally by:
```powershell
python runtime\state\runtime_cli.py resolve
python runtime\state\runtime_cli.py status
```

### Lifecycle
```text
chaseos runtime start <runtime>
chaseos runtime stop <runtime>
chaseos runtime restart <runtime>
chaseos runtime health <runtime>
chaseos runtime status <runtime>
chaseos runtime logs <runtime>
```

`status` and `health` are live inspection surfaces today. `start`, `stop`, `restart`, and `logs` are not yet promoted as live ChaseOS lifecycle-control surfaces.
They remain target-shape commands for future OpenClaw/Hermes lifecycle ownership until the runtime-operation policy allowlist and approval rules are explicit.

Runtime-owned coordination-watch loop supervision is now partially live through:
```text
chaseos runtime coordination-watch-supervisor --runtime <id> --action plan|status|start|stop
```

Direct operator-controlled daemon startup is also live for the two current runtime lanes:
```text
chaseos runtime daemon --runtime hermes   --daemon-interval <seconds>
chaseos runtime daemon --runtime openclaw --daemon-interval <seconds>
```

Use `--daemon-once` for a single watch cycle, `--daemon-max-tasks N` to bound claims per cycle, and `--synthesize` only when the selected runtime should use its configured model credentials for synthesis. This command starts the runtime's coordination-watch loop: it publishes bus heartbeat/state, claims eligible Agent Bus tasks for that runtime, dispatches only declared workflow handlers, writes result/audit state, and leaves Discord/operator surfaces as visibility rather than machine-state coordination.

This remains a bounded local daemon/supervisor foothold, not full host-level service registration.

Runtime-owned coordination-watch bootstrap registration is now partially live through:
```text
chaseos runtime coordination-watch-bootstrap --runtime <id> --action plan|status|install|remove|apply|verify|unregister|handoff|reboot-verify|capture-success|reconcile-reboot-result|activation-report|activation-checklist
```

This currently owns launcher + registration artifacts, and can attempt host scheduler mutation/verification through named Gate operations, but still depends on the privilege level of the current shell.

---

## 4. Related Reading

- `CLI-SURFACES.md`
- `runtime/COMMANDS-README.md`
- `runtime/CLI-README.md`
- `runtime/LIFECYCLE-README.md`
- `runtime/state/CLI-README.md`
- `06_AGENTS/ChaseOS-CLI-Surface-Architecture.md`
- `06_AGENTS/ChaseOS-Runtime-Command-Contract.md`
- `06_AGENTS/ChaseOS-Runtime-Lifecycle-Contract.md`
- `06_AGENTS/Runtime-Shell-and-Command-Surface-Summary-Context-Application.md`
- `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md`
- `06_AGENTS/Control-Plane-Ingress-and-Bus-Translation.md`

---

## 5. Promoted Coordination Command Notes

The top-level `chaseos.py` shell now exposes a real coordination ingress seam, not just runtime inspection.

Validated promoted flow on 2026-04-25:
- refresh runtime health through `python chaseos.py runtime health --runtime all --json`
- refresh runtime liveness through `python chaseos.py agent-bus heartbeat ...`
- inspect routing with `python chaseos.py agent-bus route <task-type>`
- inspect capability/liveness declarations with `python chaseos.py agent-bus runtimes`
- create a task with `python chaseos.py agent-bus task create ...`
- claim it with `python chaseos.py agent-bus task claim ...`
- advance it with `python chaseos.py agent-bus task update ...`
- test reclaim path safely with `python chaseos.py agent-bus task reclaim ...` on active tasks, not via zero-threshold mass expiry
- verify stale-expiry regression coverage with `python -m pytest runtime/agent_bus/test_agent_bus.py -q` (passing: 10 tests)
- verify capability routing and malformed-manifest guardrails with `python -m pytest runtime/agent_bus/test_capabilities_router.py -q` (passing: 73 tests)
- verify AOR review-path coordination end to end with `python -m pytest runtime/agent_bus/test_bus_coordination_e2e.py -q` (passing: 50 tests)

This aligns the promoted shell with the constitutional rule that control surfaces are ingress and the bus is coordination state.

*Graph links: [[06_AGENTS/Runtime-InterAgent-Coordination-Bus|Runtime-InterAgent-Coordination-Bus]] Â· [[Control-Plane-Ingress-and-Bus-Translation]] Â· [[Runtime-Shell-and-Command-Surface-Summary-Context-Application]]*

