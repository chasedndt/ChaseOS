# runtime/providers - Provider Registry and State Ledger

This folder contains ChaseOS runtime provider/model inspection surfaces.

## Current Surfaces

- `registry.py` reads setup/provider registry truth.
- `governance_status.py` aggregates provider, model, queue, fallback, adapter-health, read-only readiness posture, and operator summary cards for `chaseos runtime provider-status`.
- `governance_layer.py` owns the Runtime Provider Governance Layer (RPGL): provider strength classification, task-class capability gating, queue-on-denial behavior, fallback timeout decisions, simulated local fallback timeout proof, local Ollama streaming timeout wrapper contract with injected stream runner, primary cooldown/recovery/unhealthy state, active provider target profile reporting, target-profile plan/proposal/queue requests under `07_LOGS/Agent-Activity/_rpgl_provider_target_profile_proposals/`, read-only provider config reconciliation, provider config correction proposal/queue requests, provider config apply preflight, non-executing provider config apply design, provider config apply approval request artifacts under `07_LOGS/Agent-Activity/_rpgl_provider_config_apply_approvals/`, immutable provider config apply approval decision records under `07_LOGS/Agent-Activity/_rpgl_provider_config_apply_decisions/`, provider config apply immutable decision-record validation/idempotency preflight, provider config apply decision consumption plan, provider config apply decision consumer design, provider config apply decision consumer invocation preflight, provider config apply decision consumer implementation plan, provider config apply decision consumer writer dry-run, provider config apply decision consumer write-guard contract, guarded provider config apply decision consumer record writer under `07_LOGS/Agent-Activity/_rpgl_provider_config_apply_consumers/`, guarded provider config apply atomic marker writer under `runtime/providers/state/provider_config_apply_markers/`, provider config apply atomic marker writer design, guarded provider config apply live executor with result records under `runtime/providers/state/provider_config_apply_results/` and rollback-on-verification-failure, provider config apply executor dry-run plan, metadata-only provider probe dry-runs, denied-by-default live-probe preflight contracts, Gate approval schema exposure for `runtime.provider.live_probe` and `runtime.provider.config_apply`, pending approval request artifacts under `07_LOGS/Agent-Activity/_rpgl_provider_approvals/`, target-profile-aware live-probe approval plan/request writer, immutable live-probe approval decision records under `07_LOGS/Agent-Activity/_rpgl_provider_live_probe_decisions/`, live-probe approval decision CLI preview/write, non-executing live-probe decision preflight, non-executing live-probe marker contract under `runtime/providers/state/provider_live_probe_markers/`, guarded live-probe decision consumer records under `07_LOGS/Agent-Activity/_rpgl_provider_live_probe_consumers/`, guarded live-probe atomic marker writes under `runtime/providers/state/provider_live_probe_markers/`, non-network live-probe executor dry-run/readiness reports, read-only live-smoke readiness reports, read-only live-smoke closeout plans, read-only RPGL completion-status reports, guarded live-probe executor result records under `runtime/providers/state/provider_live_probe_results/`, non-executing live-probe executor spec/precondition reports, and provider audit events for the `chaseos runtime ...` governance commands.
- `adapter_health.py` rolls connector-health and delivery-health ledgers into adjacent read-only adapter status for `chaseos runtime provider-status` without feeding provider fallback governance.
- `state_ledger.py` owns the append-only provider-state event ledger.
- `runtime/adapters/runtime_governance.py` emits the read-only OpenClaw/Hermes adapter-governance report and `rpgl_consumption` checks exposed through `chaseos runtime adapter-governance`.
- `RECOVERY-TO-PRIMARY.md` defines the governed recovery-to-primary design contract for future Phase 10 plan/apply controls.
- `provider_call_surfaces.json` classifies model, connector, delivery, lifecycle, and dry-run adapter call surfaces by telemetry owner.
- `call_surface_audit.py` validates the provider call-surface classification artifact.
- `runtime/execution_adapters/execute.py` emits provider-state events from the shared model-chain execution path and asks RPGL before attempting configured fallbacks after primary provider failure.
- `runtime/workflows/hermes_review_execute.py` routes optional Hermes review synthesis through the shared execution adapter.

## Provider State Ledger

Ledger path:

```text
runtime/providers/state/provider_state_events.jsonl
```

Recorded event types:

- `provider.request`
- `provider.rate_limited`
- `provider.cooldown_started`
- `provider.cooldown_ended`
- `provider.fallback_activated`
- `provider.recovery_primary_eligible`
- `provider.recovery_primary_completed`

The provider-state ledger remains evidence only. It does not switch providers, enforce cooldowns, retry jobs, clean queues, or recover to primary. Runtime adapters may append events; `runtime provider-status` reads and summarizes them. RPGL control state is separate and lives under `runtime/providers/state/provider_state.json`, `runtime/providers/state/provider_queue.json`, and `runtime/providers/state/provider_audit.jsonl`.

Current implemented emission coverage:

- shared execution adapter model attempts emit `provider.request`
- rate-limit failures emit `provider.rate_limited`
- movement to the next configured model emits `provider.fallback_activated` only after RPGL capability checks allow the fallback for the task class
- a successful primary attempt after a prior active fallback emits `provider.recovery_primary_completed`

Cooldown start/end and recovery eligibility remain valid provider-state event types. The 2026-04-30 RPGL pass added a separate governed control layer that persists cooldown state, denies weak fallback for high-authority tasks, queues serious work, and records provider audit events. The 2026-05-02 shared adapter fallback gate extended that behavior so primary non-rate failures can mark the primary provider unhealthy, high-authority tasks queue instead of falling through to any configured fallback, and weak fallback is denied for non-weak-safe task classes. Hermes review synthesis now uses the shared execution adapter path instead of its older direct Anthropic request helper.

## Recovery-to-Primary Governance

`RECOVERY-TO-PRIMARY.md` is the Phase 9 design contract for governed recovery from fallback back to a primary provider/model route. `06_AGENTS/Runtime-Provider-Governance-Layer.md` is the current canonical RPGL feature spec.

Current truth:

- `runtime provider-status` may report recovery-to-primary evidence from the provider-state ledger.
- provider-state events remain the evidence lane for model-chain attempts.
- RPGL adds provider strength classification, task-class gating, shared execution-adapter fallback capability checks, runtime adapter-governance RPGL consumption checks, queue-on-denial behavior, fallback timeout decisions, simulated local fallback timeout proof, local Ollama streaming timeout wrapper contract with injected stream runner, queue retry package dry-run proof, provider audit events, active provider target profile reporting, read-only provider config reconciliation, provider config correction proposal/queue requests, provider config apply preflight, non-executing provider config apply design, provider config apply approval request persistence/structural validation, immutable provider config apply approval decision records, immutable decision-record validation/idempotency preflight, provider config apply decision consumption plan, provider config apply decision consumer design, provider config apply decision consumer invocation preflight, provider config apply decision consumer implementation plan, provider config apply decision consumer writer dry-run, provider config apply decision consumer write-guard contract, guarded provider config apply decision consumer record writer, guarded provider config apply atomic marker writer, provider config apply atomic marker writer design, guarded provider config apply live executor, rollback-on-verification-failure, provider config apply executor dry-run plan, metadata-only provider probe dry-runs, denied-by-default live-probe preflight contracts, pending approval request persistence/structural validation, target-profile-aware live-probe approval planning/request writing, immutable live-probe approval decision records, live-probe approval decision CLI preview/write, non-executing live-probe decision preflight, non-executing live-probe marker contract, guarded live-probe decision consumer record writer, guarded live-probe atomic marker writer, read-only live-smoke readiness reporting, read-only live-smoke closeout planning, guarded live-probe executor result records/provider-state update, non-executing live-probe executor spec/precondition reports, and dry-run recovery inspection with retry package previews.
- adjacent connector-health and delivery-health evidence must not trigger provider recovery.
- no live `provider-recovery apply` command exists yet.
- any live provider-network probe or queue-drain/apply mutation must remain separate from read-only `provider-status`, Gate-governed, auditable, and operator-approved; the current live-probe executor is implemented only behind the full RPGL approval chain plus `--execute-live-probe`, and live real-provider smoke remains unverified.

Implemented RPGL CLI commands:

- `chaseos runtime providers`
- `chaseos runtime adapter-governance`
- `chaseos runtime fallback-status`
- `chaseos runtime queue list`
- `chaseos runtime queue show <id>`
- `chaseos runtime queue retry <id> --dry-run`
- `chaseos runtime provider probe primary`
- `chaseos runtime provider probe fallback`
- `chaseos runtime provider probe primary --probe-mode network-dry-run`
- `chaseos runtime provider probe primary --probe-mode live-preflight`
- `chaseos runtime provider probe primary --probe-mode live-preflight --write-approval-request`
- `chaseos runtime provider probe primary --probe-mode live-preflight --gate-approval-id <id>`
- `chaseos runtime provider executor-spec primary`
- `chaseos runtime provider executor-spec primary --gate-approval-id <id>`
- `chaseos runtime provider config-report`
- `chaseos runtime provider target-profile`
- `chaseos runtime provider target-profile-plan [MODEL]`
- `chaseos runtime provider target-profile-plan gpt-5.5 --write-approval-request --requested-by operator`
- `chaseos runtime provider config-plan`
- `chaseos runtime provider config-plan --write-approval-request --requested-by operator`
- `chaseos runtime provider config-apply-preflight <proposal_id>`
- `chaseos runtime provider config-apply-design <proposal_id>`
- `chaseos runtime provider config-apply-approval-request <proposal_id> --write-approval-request --requested-by operator`
- `chaseos runtime provider config-apply-approval-request <proposal_id> --gate-approval-id <id>`
- `chaseos runtime provider config-apply-approval-decision <proposal_id> --gate-approval-id <id> --decision approved|denied`
- `chaseos runtime provider config-apply-decision-preflight <proposal_id> --gate-approval-id <id>`
- `chaseos runtime provider config-apply-decision-consumption-plan <proposal_id> --gate-approval-id <id>`
- `chaseos runtime provider config-apply-decision-consumer-design <proposal_id> --gate-approval-id <id>`
- `chaseos runtime provider config-apply-decision-consumer-preflight <proposal_id> --gate-approval-id <id>`
- `chaseos runtime provider config-apply-decision-consumer-implementation-plan <proposal_id> --gate-approval-id <id>`
- `chaseos runtime provider config-apply-decision-consumer-writer-dry-run <proposal_id> --gate-approval-id <id>`
- `chaseos runtime provider config-apply-decision-consumer-write-guard-contract <proposal_id> --gate-approval-id <id>`
- `chaseos runtime provider config-apply-decision-consumer <proposal_id> --gate-approval-id <id> --write-consumer-record`
- `chaseos runtime provider config-apply-atomic-marker-writer <proposal_id> --gate-approval-id <id> --write-consumption-marker`
- `chaseos runtime provider config-apply-atomic-marker-writer-design <proposal_id> --gate-approval-id <id>`
- `chaseos runtime provider config-apply-executor <proposal_id> --gate-approval-id <id> --apply-provider-config`
- `chaseos runtime provider config-apply-executor-dry-run <proposal_id> --gate-approval-id <id>`
- `chaseos runtime provider live-probe-approval-decision primary|fallback --gate-approval-id <id> --decision approved|denied`
- `chaseos runtime provider live-probe-decision-preflight primary|fallback --gate-approval-id <id>`
- `chaseos runtime provider live-probe-marker-contract primary|fallback --gate-approval-id <id>`
- `chaseos runtime provider live-probe-decision-consumer primary|fallback --gate-approval-id <id> --write-consumer-record`
- `chaseos runtime provider live-probe-atomic-marker-writer primary|fallback --gate-approval-id <id> --write-consumption-marker`
- `chaseos runtime provider live-probe-executor-dry-run primary|fallback --gate-approval-id <id>`
- `chaseos runtime provider live-probe-target-approval-plan [primary|fallback|all]`
- `chaseos runtime provider live-probe-target-approval-plan primary --write-approval-request --requested-by operator`
- `chaseos runtime provider live-smoke-readiness`
- `chaseos runtime provider live-smoke-closeout-plan`
- `chaseos runtime provider completion-status`
- `chaseos runtime provider live-probe-executor primary|fallback --gate-approval-id <id> --execute-live-probe`
- `chaseos runtime provider fallback-timeout-proof no-chunks`
- `chaseos runtime provider ollama-timeout-contract success`
- `chaseos gate check-operation runtime.provider.config_apply`
- `chaseos gate check-operation runtime.provider.live_probe --external-api provider.openai`
- `chaseos runtime recover --dry-run`
- `chaseos runtime audit-tail`

## Provider Call-Surface Audit

Machine-readable audit path:

```text
runtime/providers/provider_call_surfaces.json
```

The audit separates provider-state ledger surfaces from adjacent external-call surfaces:

- Runtime model execution emits provider-state ledger evidence directly or through the shared execution adapter.
- Source Intelligence generation and embedding adapters are Source Intelligence telemetry, not runtime fallback governance.
- Perplexity, Grok, RSS, web scrape, IMAP email, Google Docs, and Google Drive acquisition outcomes now emit acquisition connector-health telemetry under `runtime/acquisition/state/connector_health_events.jsonl`.
- Discord webhook and Whop forum-post calls are delivery health telemetry under
  `runtime/sbp/state/delivery_health_events.jsonl`, inspectable through
  `chaseos sbp delivery-health`.
- `runtime provider-status` includes an adjacent `adapter_health_rollup` that reads those connector-health and delivery-health ledgers. This rollup is read-only and explicitly does not feed provider-state ledger, provider switching, cooldown, or recovery-to-primary control.
- setup and lifecycle probes are runtime/setup health telemetry.
- OpenAI Responses/MCP and n8n surfaces currently build dry-run payloads only; they do not perform live provider calls.

Current provider-state ledger scope is intentionally narrow: shared runtime synthesis, SBP synthesis through that adapter, and Hermes review synthesis through that adapter. Other provider-like calls remain classified but do not currently drive rate-limit, cooldown, fallback, or recovery-to-primary state.

## Readiness Summary

`chaseos runtime provider-status` now includes a top-level `readiness_summary` for operator/Studio wrapping. It is read-only and derives posture from existing evidence, including adjacent `adapter_health_status` visibility:

- `ready` when provider setup, runtime heartbeat/model binding, queue health, and provider-state ledger posture have no reported degradation reasons.
- `degraded` when non-blocking evidence exists such as stale runtime heartbeats, stuck/no-chunk queue items, active rate-limit/cooldown state, or warnings.
- `blocked` when there is no valid provider or a runtime model binding cannot be read.

The summary does not switch providers, retry jobs, mutate queues, or control cooldowns; adjacent adapter-health failures remain visible without becoming fallback-governance triggers. It gives the Settings/Studio layer a compact status object without creating a new authority surface.

## Operator Summary

`chaseos runtime provider-status` also includes a top-level `operator_summary` for Studio/operator presentation. It packages the readiness posture into stable status cards:

- active runtime
- operator default provider
- active primary/fallback model route
- provider-governance state for rate-limit, cooldown, and recovery-to-primary evidence
- queue counts for queued, active, stuck, and no-chunk work
- adjacent adapter-health counts
- attention items and recommended next actions

This is presentation-only. `operator_summary.boundary` explicitly reports that it does not control provider switching, cooldowns, recovery-to-primary, or adapter retries.
