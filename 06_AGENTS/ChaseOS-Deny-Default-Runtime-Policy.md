---
title: ChaseOS Deny-by-Default Runtime Policy
type: architecture-control
status: active-foothold
created: 2026-04-27
model: Codex GPT-5
phase: phase-9-hardening
---

# ChaseOS Deny-by-Default Runtime Policy

> This note documents the 2026-04-27/2026-04-28 policy foothold so agentic runtimes can extend it safely while continuing Phase 9 gateway and CLI work.

---

## Summary

ChaseOS now has a package-native deny-by-default runtime operation check:

```text
runtime/chaseos_gate.py::check_runtime_operation()
```

Unknown runtime operations are denied. Known operations must be explicitly listed in `RUNTIME_OPERATION_POLICIES` and must satisfy the adapter manifests, task/write checks, coordination path rules, and external side-effect policy relevant to that operation.

The first live caller surface was the canonical CLI agent-bus command family. That coverage has now expanded to the first setup/config/schedule mutation paths, draft scaffold generation, bounded browser operator read/screenshot surfaces, runtime registry mutations, coordination-watch lifecycle/bootstrap side-effect surfaces, and SBP Discord/Whop delivery adapters. Side-effecting operations now check policy before creating, claiming, updating, reclaiming, watching, heartbeating, expiring, or translating Discord ingress into bus state; before applying setup state, bounded config writes, or schedule enable/disable mutations; before scaffold draft generation under `runtime/scaffold/generated/`; before browser operator audit/screenshot writes under `07_LOGS/Agent-Activity/` and `07_LOGS/Operator-Screenshots/`; before coordination-watch process/scheduler/bootstrap state effects under the runtime lifecycle surface; and before SBP delivery adapters call Discord webhook or Whop API endpoints.

---

## Files Changed

- `runtime/chaseos_gate.py` - adds `RUNTIME_OPERATION_POLICIES` and `check_runtime_operation()`
- `runtime/cli/agent_bus_commands.py` - checks runtime operation policy before agent-bus mutations
- `runtime/cli/gate_commands.py` - implements `chaseos gate check-operation`
- `runtime/cli/main.py` - registers the `check-operation` parser under the canonical CLI and gates runtime lifecycle side-effect commands before execution
- `runtime/policy/gateway_allowlists.json` - adds runtime lifecycle state, host process/scheduler IDs, scheduled briefing run outputs, SBP delivery external API IDs, and missing n8n manifest task types
- `runtime/events/dispatcher.py` - checks `gateway.workflow.dispatch` before event-triggered AOR execution
- `runtime/mcp/tools/workflow_invoke.py` - checks `gateway.workflow.invoke_bounded` before Runtime MCP invokes AOR
- `runtime/sbp/delivery_adapters.py` - checks `sbp.delivery.discord.webhook_send` and `sbp.delivery.whop.post` before HTTP delivery writes
- `runtime/sbp/runner.py` - propagates delivery adapter context fields in the generic SBP runner
- `runtime/tests/test_gate_deny_default_runtime_policy.py` - verifies allow/block behavior and CLI JSON output
- `runtime/tests/test_gateway_allowlists_and_credentials.py` - verifies SBP delivery external API IDs remain allowlisted
- `runtime/tests/test_events_dispatch_gate.py` - verifies event-triggered dispatch blocks before AOR when Gate denies
- `runtime/mcp/tests/test_runtime_mcp_v1.py` - verifies MCP invocation blocks before AOR when Gate denies
- `runtime/aor/test_phase9_sbp_pass1d.py` and `runtime/aor/test_phase9_sbp_whop.py` - verify SBP delivery blocks before `urlopen` when Gate denies
- `runtime/agent_bus/test_canonical_agent_bus_cli.py` - verifies side-effecting bus smoke flows through `python chaseos.py agent-bus ...` with disposable vaults and cleanup markers
- `06_AGENTS/ChaseOS-Gate.md` - updates Gate doctrine to include the Phase 9 policy layer

Related prior refactor:
- `06_AGENTS/ChaseOS-CLI-Consolidation-Refactor.md`
- `07_LOGS/Build-Logs/2026-04-26-ChaseOS-CLI-Consolidation-Codex-GPT5.md`

This pass:
- `07_LOGS/Build-Logs/2026-04-27-ChaseOS-Deny-Default-Runtime-Policy-Codex-GPT5.md`
- `99_ARCHIVE/Documentation-History/2026-04-27-ChaseOS-Deny-Default-Runtime-Policy-Codex-GPT5.md`
- `07_LOGS/Build-Logs/2026-04-28-ChaseOS-phase9-sbp-delivery-gate-policy.md`
- `99_ARCHIVE/Documentation-History/2026-04-28_phase9-sbp-delivery-gate-policy.md`
- `07_LOGS/Build-Logs/2026-04-28-ChaseOS-sbp-delivery-side-effect-policy.md`
- `99_ARCHIVE/Documentation-History/2026-04-28_sbp-delivery-side-effect-policy.md`

---

## Active Operation Allowlist

Current allowlisted operations:

```text
agent_bus.ingress.discord
agent_bus.task.create
agent_bus.task.claim
agent_bus.task.update
agent_bus.task.cleanup
agent_bus.task.reclaim
agent_bus.heartbeat
agent_bus.watch
agent_bus.expire_stale
config.set
schedule.enable
schedule.disable
events.emit
events.dispatch
gateway.workflow.dispatch
gateway.workflow.invoke_bounded
setup.init.write
setup.provider.apply
setup.integration.apply
setup.state.set
scaffold.project.generate
scaffold.workspace.generate
sbp.delivery.discord.webhook_send
sbp.delivery.whop.post
browser.open
browser.inspect
browser.screenshot
agent.register
agent.lifecycle.transition
lifecycle.coordination_watch.run
lifecycle.coordination_watch_supervisor.start
lifecycle.coordination_watch_supervisor.stop
lifecycle.coordination_watch_bootstrap.install
lifecycle.coordination_watch_bootstrap.apply
lifecycle.coordination_watch_bootstrap.verify
lifecycle.coordination_watch_bootstrap.activation_report
lifecycle.coordination_watch_bootstrap.unregister
lifecycle.coordination_watch_bootstrap.handoff
lifecycle.coordination_watch_bootstrap.reboot_verify
lifecycle.coordination_watch_bootstrap.capture_success
lifecycle.coordination_watch_bootstrap.reconcile_reboot_result
lifecycle.coordination_watch_bootstrap.remove
osril.approval_response
osril.approval_resume
```

The policy is still intentionally narrow, but it no longer stops at bus-only coverage, setup/config/schedule/scaffold draft writes, event-state writes, existing event/MCP AOR dispatch seams, bounded OSRIL approval response/resume writes, the bounded browser operator read/screenshot command family, runtime registry mutation, coordination-watch lifecycle/bootstrap side-effect paths, or SBP Discord/Whop delivery writes. Future concrete Gateway/Studio UI dispatches, browser actions beyond read/screenshot, and any new lifecycle process/scheduler families still need to be added as named operations before Phase 10.

---

## Canonical Bus Smoke Rule

Agent-bus command hardening is validated through the canonical ChaseOS shell, not subsystem scripts.

Smoke tests that create task state must:

1. invoke `python chaseos.py agent-bus ...`
2. pass `--vault-root` to a disposable test vault, or cancel created tasks with a known cleanup marker
3. verify the live bus database does not contain that marker in task or heartbeat records

Current canonical smoke coverage includes task creation, Discord ingress translation, heartbeat publication, watch/claim, reclaim, and cancellation.

---

## Runtime Contract

When adding a command that writes state, mutates state, coordinates runtimes, starts external work, or touches external systems:

1. Add a stable operation name to `RUNTIME_OPERATION_POLICIES`.
2. Require an actor manifest when the command is executed by a runtime.
3. Require a target manifest when the command targets another runtime.
4. Mark `coordination_sensitive` when work can affect another runtime, shared bus state, or operator-visible execution.
5. Require the bus path for coordination-sensitive machine-to-machine work.
6. Pass declared task type and write targets into `check_runtime_operation()` when applicable.
7. Set `external_side_effect=True` for API calls, external writes, gateway dispatches, browser automation with outside effects, or webhook/service actions.
8. Block before performing the side effect.

Do not build a separate permission check inside a command handler. Command handlers should call the Gate seam and then execute.

---

## CLI Surface

Human and runtime smoke check:

```powershell
python -m runtime.cli.main gate check-operation gateway.magic.write --json
```

Expected result: denied, because the operation is not allowlisted.

Allowed bus creation check:

```powershell
python -m runtime.cli.main gate check-operation agent_bus.task.create --actor-adapter Hermes --target-runtime OpenClaw --json
```

Expected result: allowed, assuming both manifests remain active and coordination policy still permits bus-first coordination.

Allowed setup/config/schedule/scaffold/browser checks:

```powershell
python -m runtime.cli.main gate check-operation setup.provider.apply --json
python -m runtime.cli.main gate check-operation config.set --write-target .chaseos/config.yaml --json
python -m runtime.cli.main gate check-operation schedule.enable --write-target runtime/schedules/sch-example.yaml --write-target runtime/schedules/index.yaml --write-target 07_LOGS/Schedule-State/schedule_state_log.jsonl --json
python -m runtime.cli.main gate check-operation scaffold.project.generate --write-target runtime/scaffold/generated/project-alpha-core/scaffold_request.json --json
python -m runtime.cli.main gate check-operation browser.screenshot --write-target 07_LOGS/Agent-Activity/browser-smoke.json --write-target 07_LOGS/Operator-Screenshots/smoke.png --json
```

Expected result: allowed, because these bounded CLI-operator mutation paths are now named operations with explicit write-target category checks where applicable.

---

## Next Expansion Targets

Priority order for the next runtimes:

1. Gateway/Studio command prep: every future concrete UI dispatch/write must call the named runtime operation seam; the existing event-rule AOR dispatch and Runtime MCP `workflow.invoke_bounded` AOR dispatch paths now have `gateway.workflow.dispatch` and `gateway.workflow.invoke_bounded` policy checks.
2. Core/Personal export and template-copy writes beyond draft scaffold generation.
3. Browser operator actions beyond bounded read/screenshot, especially form submits, clicks against external controls, downloads, or authenticated flows.
4. New lifecycle process/scheduler families beyond the coordination-watch supervisor/bootstrap foothold.
5. Studio Phase 10 surfaces: Studio must call this same Gate seam and must not own a parallel policy model.

Lifecycle note: `chaseos runtime status` and `chaseos runtime health` are inspection surfaces today. Coordination-watch supervisor/bootstrap actions now have explicit operation names and bounded allowlists. General runtime `start`, `stop`, `restart`, and `logs` should not become live command surfaces until they have their own explicit operation names, approval posture, and process/log authority rules.

Lifecycle side-effect pass on 2026-04-27:

```powershell
python -m pytest runtime/tests/test_gate_deny_default_runtime_policy.py -q --basetemp .pytest-tmp/gate-lifecycle
python -m pytest runtime/tests/test_gateway_allowlists_and_credentials.py runtime/tests/test_gate_coordination_policy.py runtime/tests/test_cli_gate_and_coordination_surface.py runtime/tests/test_agent_bus_runtime_cli_surface.py runtime/tests/test_runtime_provider_status.py -q --basetemp .pytest-tmp/gate-lifecycle-related
```

Result:

```text
32 deny-default policy tests passed
27 related Gate/coordination/runtime tests passed
```

Gateway/Studio dispatch policy preflight on 2026-04-28:

```powershell
python -m pytest runtime/tests/test_gate_deny_default_runtime_policy.py runtime/tests/test_events_dispatch_gate.py -q -p no:cacheprovider
python -m pytest runtime/mcp/tests/test_runtime_mcp_v1.py -q -p no:cacheprovider
python -m pytest runtime/tests/test_gateway_allowlists_and_credentials.py runtime/tests/test_gate_coordination_policy.py runtime/tests/test_cli_gate_and_coordination_surface.py -q -p no:cacheprovider
python -m py_compile runtime/chaseos_gate.py runtime/events/dispatcher.py runtime/mcp/tools/workflow_invoke.py runtime/mcp/errors.py runtime/tests/test_events_dispatch_gate.py
```

Result:

```text
36 Gate/event-dispatch policy tests passed
68 Runtime MCP tests passed
19 related Gate/allowlist/coordination tests passed
py_compile passed for changed Python modules
```

SBP delivery policy pass on 2026-04-28:

```powershell
python -m pytest runtime/tests/test_gate_deny_default_runtime_policy.py runtime/aor/test_phase9_sbp_pass1d.py runtime/aor/test_phase9_sbp_whop.py -q -p no:cacheprovider
python -m py_compile runtime/chaseos_gate.py runtime/sbp/delivery_adapters.py runtime/tests/test_gate_deny_default_runtime_policy.py runtime/aor/test_phase9_sbp_pass1d.py runtime/aor/test_phase9_sbp_whop.py
```

Result:

```text
Gate allows only declared SBP delivery operation/API pairs.
Discord and Whop adapters block before urllib.request.urlopen when Gate denies.
```

---

## Verification

Focused tests run on 2026-04-27:

```powershell
python -m pytest -q runtime\tests\test_gate_deny_default_runtime_policy.py runtime\operator_surface\tests\test_browser_pass4.py runtime\operator_surface\tests\test_browser_pass5.py -p no:cacheprovider
python -m pytest -q runtime\tests\test_cli_entrypoint_consolidation.py runtime\tests\test_cli_json_contract.py runtime\tests\test_cli_command_contract.py runtime\tests\test_config_store.py -p no:cacheprovider
python -m pytest -q runtime\agent_bus\test_canonical_agent_bus_cli.py -p no:cacheprovider
```

Result:

```text
26 policy tests passed
120 browser/operator-policy regression tests passed, 5 skipped
20 CLI JSON/command/entrypoint tests passed
```

Smoke checks:

```text
gateway.magic.write -> denied, not allowlisted
agent_bus.task.create Hermes -> OpenClaw -> allowed
setup.provider.apply -> allowed
config.set (.chaseos/config.yaml) -> allowed
schedule.enable (manifest + index + state log targets) -> allowed
scaffold.project.generate (runtime/scaffold/generated draft target) -> allowed
browser.screenshot (Agent-Activity + Operator-Screenshots targets) -> allowed
browser.screenshot (/tmp/outside.png) -> denied outside browser_operator_outputs
gateway.workflow.dispatch (OpenClaw scheduled briefing targets) -> allowed
gateway.workflow.dispatch (02_KNOWLEDGE target) -> denied by OpenClaw manifest
gateway.workflow.invoke_bounded (OpenClaw operator brief targets) -> allowed
sbp.delivery.discord.webhook_send (delivery.discord_webhook) -> allowed
sbp.delivery.discord.webhook_send (delivery.whop_api) -> denied
sbp.delivery.whop.post (delivery.whop_api) -> allowed
```


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
