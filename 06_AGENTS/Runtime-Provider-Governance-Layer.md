# Runtime Provider Governance Layer

Status: COMPLETE TARGETED / IMPLEMENTED FOUNDATION / LIVE PROVIDER PROOF DEFERRED  
Runtime label: RPGL  
Implemented surfaces: `runtime/providers/governance_layer.py`, `chaseos runtime ...` CLI commands, active provider target profile report, target-profile plan/proposal/queue request, read-only provider config reconciliation report, provider config change proposal/queue request, provider config apply preflight, non-executing provider config apply design, provider config apply approval request artifacts, immutable provider config apply approval decision records, provider config apply immutable decision-record validation/idempotency preflight, provider config apply decision consumption plan, provider config apply decision consumer design, provider config apply decision consumer invocation preflight, provider config apply decision consumer implementation plan, provider config apply decision consumer writer dry-run, guarded provider config apply decision consumer record writer, guarded provider config apply atomic marker writer, provider config apply atomic marker writer design, guarded provider config apply live executor with rollback-on-verification-failure, provider config apply executor dry-run plan, shared execution-adapter fallback capability gate, runtime adapter governance RPGL consumption report, simulated local fallback timeout proof harness, local Ollama streaming timeout wrapper contract with injected stream runner, queue retry package dry-run proof, RPGL live-probe approval artifacts, target-profile-aware live-probe approval plan/request writer, immutable live-probe approval decision records, live-probe approval decision CLI preview/write, non-executing live-probe decision preflight, non-executing live-probe marker contract, guarded live-probe decision consumer record writer, guarded live-probe atomic marker writer, non-network live-probe executor dry-run/readiness plan, read-only live-smoke readiness report, read-only live-smoke closeout plan, read-only RPGL completion-status report, guarded live-probe executor with result records and provider-state update, non-executing live-probe executor spec, targeted tests  
Primary boundary: ChaseOS owns provider governance; Hermes and OpenClaw consume shared decisions instead of inventing independent fallback rules.

## Why This Exists

RPGL exists because provider fallback is a governance decision, not a convenience retry. A primary provider can rate-limit, a fallback can be too weak for the task, and a long no-chunk local model call can waste operator time while producing irrelevant output. ChaseOS must decide when fallback is allowed, when work must be queued, and when the system should return to the primary provider.

The motivating failure was:

- primary model rate-limited
- local Ollama fallback selected
- weak model attempted high-complexity development
- no useful chunks streamed for an extended period
- no early abort or queue handoff occurred
- provider state was not clearly exposed through the ChaseOS CLI
- automatic return-to-primary was not proved

## Provider Strength Model

### Strong

Strong providers are approved primary/cloud development providers that may handle high-authority ChaseOS development tasks when existing permission, Gate, and approval rules allow the action.

Examples:

- Codex with the current approved strong development model when configured as the active development runtime
- approved OpenAI cloud models through current runtime config, including GPT-5.5 for this ChaseOS instance while it remains the operator-selected target
- approved Anthropic/Claude lanes already covered by existing ChaseOS runtime policy

Allowed by RPGL capability:

- repo development
- architecture changes
- multi-file patches
- YAML registry changes
- runtime config changes
- provider routing changes with approval
- security/trust/permission changes with approval
- canonical docs writes where existing ChaseOS writeback rules allow

### Medium

Medium providers may support read-heavy, draft-heavy, or isolated work. They are not automatically trusted for high-authority mutation.

Allowed by default:

- read-only analysis
- documentation drafts
- test generation proposals
- config review
- queue review
- audit review

Denied or conditional by default:

- provider routing changes
- security policy changes
- trust-tier changes
- permission-matrix changes
- broad multi-file patches
- canonical mutation without approval

### Weak

Weak providers are recovery assistants, not development authorities.

Examples:

- local Ollama phi4-mini
- small local models on the current 16 GB RAM laptop
- any fallback previously observed producing no chunks or irrelevant output for high-complexity work

Allowed:

- `summarize_failure`
- `prompt_compression`
- `task_classification`
- `queue_item_creation`
- `retry_package_creation`
- `log_summary`
- `provider_status_summary`
- `fallback_diagnostic_summary`

Denied:

- `repo_development`
- `architecture_change`
- `yaml_registry_update`
- `multi_file_patch`
- `security_policy_change`
- `runtime_config_change`
- `provider_routing_change`
- `canonical_doc_write`
- `shell_mutation`
- `git_mutation`
- `gateway_restart`
- `deployment_action`
- `trust_tier_change`
- `permission_matrix_change`

Rule: weak fallback can help ChaseOS survive, but it must not silently replace the main development brain.

## Task Class Taxonomy

High-authority / strong-only:

- `repo_development`
- `architecture_change`
- `yaml_registry_update`
- `multi_file_patch`
- `security_policy_change`
- `runtime_config_change`
- `provider_routing_change`
- `canonical_doc_write`
- `shell_mutation`
- `git_mutation`
- `gateway_restart`
- `deployment_action`
- `trust_tier_change`
- `permission_matrix_change`

Medium / conditional:

- `read_only_analysis`
- `documentation_draft`
- `test_generation`
- `config_review`
- `queue_review`
- `audit_review`

Weak-safe:

- `summarize_failure`
- `prompt_compression`
- `task_classification`
- `queue_item_creation`
- `retry_package_creation`
- `log_summary`
- `provider_status_summary`
- `fallback_diagnostic_summary`

Unknown task classes fail closed and are queued or marked as needing operator approval.

## Authority Matrix

| Task type | Weak local fallback | Medium provider | Strong primary |
|---|---|---|---|
| `summarize_failure` | allowed | allowed | allowed |
| `prompt_compression` | allowed | allowed | allowed |
| `task_classification` | allowed | allowed | allowed |
| `queue_item_creation` | allowed | allowed | allowed |
| `retry_package_creation` | allowed | allowed | allowed |
| `log_summary` | allowed | allowed | allowed |
| `provider_status_summary` | allowed | allowed | allowed |
| `fallback_diagnostic_summary` | allowed | allowed | allowed |
| `read_only_analysis` | small-context only | allowed | allowed |
| `documentation_draft` | scratch only | allowed | allowed |
| `canonical_doc_write` | denied | conditional | allowed |
| `repo_development` | denied | conditional/denied | allowed |
| `architecture_change` | denied | denied by default | allowed |
| `yaml_registry_update` | denied | denied by default | allowed |
| `multi_file_patch` | denied | denied by default | allowed |
| `security_policy_change` | denied | denied | allowed with approval |
| `runtime_config_change` | denied | denied by default | allowed |
| `provider_routing_change` | denied | denied | allowed with approval |
| `trust_tier_change` | denied | denied | allowed with approval |
| `permission_matrix_change` | denied | denied | allowed with approval |
| `shell_mutation` | denied | denied by default | allowed with approval |
| `git_mutation` | denied | denied by default | allowed with approval |
| `gateway_restart` | denied | denied by default | allowed with approval |
| `deployment_action` | denied | denied | allowed with approval |

## Provider States

RPGL persists provider state under:

- `runtime/providers/state/provider_state.json`
- `runtime/providers/state/provider_queue.json`
- `runtime/providers/state/provider_audit.jsonl`

RPGL live-provider-probe approval request artifacts are operator-visible runtime activity records under:

- `07_LOGS/Agent-Activity/_rpgl_provider_approvals/`

These approval artifacts are not provider state. They do not execute probes, read secrets, mutate provider health state, drain queues, restart gateways, or authorize canonical writes. The executor-spec surface reports future executor preconditions only; it also does not execute probes or consume approvals.

Immutable RPGL live-provider-probe approval decision records are separate append-only records under:

- `07_LOGS/Agent-Activity/_rpgl_provider_live_probe_decisions/`

These decision records do not mutate the original approval artifact, consume approval or decision, write idempotency markers, call providers, read secrets, mutate provider state, drain queues, restart gateways, or authorize execution. The current module and CLI can preview/write/validate them, and `executor-spec` plus `live-probe-decision-preflight` report whether a matching approved immutable decision exists for a supplied `gate_approval_id`.

Future live-probe idempotency marker records are reserved under:

- `runtime/providers/state/provider_live_probe_markers/`

Current `live-probe-marker-contract` output is a no-write contract only. It computes the marker path and payload preview, declares create-new-only/write-before-network-call rules, and keeps provider calls, secret reads, provider-state mutation, queue drain, gateway restart, marker writes, approval consumption, and decision consumption disabled. The guarded `live-probe-decision-consumer` and `live-probe-atomic-marker-writer` commands can write the separate consumer record and create-new marker, but still do not call providers, read secrets, mutate provider state, drain queues, restart gateways, or authorize execution.

Guarded live-probe result records are create-new-only records under:

- `runtime/providers/state/provider_live_probe_results/`

`chaseos runtime provider live-probe-executor primary|fallback --gate-approval-id <id> --execute-live-probe` is the only implemented live-probe execution surface. It requires the existing approval request, valid approved immutable decision, matching decision-consumer record, matching idempotency marker, no existing result record, and the explicit `--execute-live-probe` flag. It may perform one bounded provider health probe, write a result record, and update provider state from the bounded outcome. It does not drain queues, restart gateways, edit canonical docs, mutate provider config, or make weak fallback sticky for development. Tests verify the executor through an injected probe runner; a real OpenAI/Ollama live smoke remains unverified.

`chaseos runtime provider live-smoke-readiness` is a read-only closeout readiness report for the final real-provider smoke step. It reports current model config reconciliation, local fallback posture, live-probe approval requests, matching primary/fallback approval-chain status, missing decision/consumer/marker/result directories, and global/target blockers. It rejects write/execution flags and records `live_network_call_attempted: false`, `secret_value_read: false`, `provider_state_mutated: false`, `queue_drained: false`, `gateway_mutated: false`, and `files_modified: false`. Current repo truth reports the live smoke as blocked because Hermes/OpenClaw model configs still do not match the active provider target profile, local Ollama fallback is not configured, existing live-probe approval requests are pending Anthropic/Claude requests, and the immutable decision/consumer/marker/result chain is incomplete.

`chaseos runtime provider live-smoke-closeout-plan` is a read-only closeout sequence planner. It composes `live-smoke-readiness` with the provider config change plan and returns the ordered operator/governance path from current blockers to approved live smoke: verify config truth, create a provider-config approval request and queue item if still needed, write immutable config-apply decision/consumer/marker records, apply config only through the guarded config executor, decide local Ollama fallback metadata while preserving `num_ctx: 16384`, create target-matching live-probe approval requests after config truth is resolved, write immutable live-probe decisions, consume decisions/markers, and only then run the guarded live-probe executor. It rejects write/apply/execute flags and performs no provider calls, secret reads, provider-state mutation, queue drain, gateway restart, approval writes, config apply, marker writes, or canonical mutation.

`chaseos runtime provider completion-status` is the final read-only RPGL completion/deferred-live-proof report. It composes target profile truth, provider config reconciliation, target-matching live-probe approval posture, live-smoke readiness, queue summary, provider inventory, implemented CLI surfaces, and acceptance-criteria status. It reports `remaining_major_development_passes_after_this: 0` while keeping real OpenAI/Ollama live-provider proof deferred until an operator-approved approval/decision/consumer/marker chain exists. It rejects approval-write, approval-consumption, provider-config apply, and live-probe execution flags and records no provider call, secret read, provider-state mutation, queue drain, gateway restart, target-profile write, approval decision, marker write, or canonical mutation.

`chaseos runtime provider target-profile` reports the active model target profile used by RPGL config reconciliation. If `runtime/providers/provider_target_profile.json` exists, that file is treated as the operator-declared target profile. If no file exists, RPGL uses the legacy `gpt-5.5` operator-reported default as a compatibility target and explicitly reports `profile_source: legacy_default_expected_primary_model`. Target profiles can declare per-runtime primary models, per-runtime fallback model targets, fallback enforcement mode (`observe_only`, `minimum`, or `exact`), provider setup default targets, and local fallback metadata. This keeps ChaseOS from treating any one primary model as permanent source truth; model targets are data and can change by governed profile/config update.

`chaseos runtime provider target-profile-plan [MODEL]` builds a non-mutating candidate target profile. If `MODEL` is omitted, it uses the active profile/default target; if supplied, the same schema works for another strong provider/model such as a Claude, OpenAI, local validated, or future provider target. The candidate preserves per-runtime fallback chains from current runtime model configs, keeps fallback enforcement at `observe_only` by default, and caps local fallback metadata at `num_ctx: 16384` for the current 16 GB local machine. With `--write-approval-request`, RPGL writes only an operator-visible proposal artifact plus a `needs_operator_approval` queue item under:

- `07_LOGS/Agent-Activity/_rpgl_provider_target_profile_proposals/`

This command does not write `runtime/providers/provider_target_profile.json`, edit Hermes/OpenClaw model configs, edit setup state, mutate provider state, call providers, read secrets, drain queues, restart gateways, or authorize live smoke.

`chaseos runtime provider live-probe-target-approval-plan [primary|fallback|all]` builds target-profile-aware pending live-probe approval templates. It derives the primary provider/model from the active RPGL target profile rather than hardcoding GPT-5.5, so another approved model family uses the same governance path. With `--write-approval-request`, it writes only pending live-probe approval request artifacts under `07_LOGS/Agent-Activity/_rpgl_provider_approvals/` for candidates that are ready. Disabled/unconfigured local fallback remains blocked and is reported as health-check-only, not development authority. The command does not call providers, read secrets, mutate provider state, apply config, write the active target-profile file, consume approvals, write decisions/markers, drain queues, restart gateways, or authorize live smoke.

RPGL provider-config apply approval request artifacts are operator-visible runtime activity records under:

- `07_LOGS/Agent-Activity/_rpgl_provider_config_apply_approvals/`

These approval artifacts are not provider config and are not provider state. They record operator intent for one future `runtime.provider.config_apply` executor attempt only. They do not edit Hermes/OpenClaw model config, edit setup state, consume approval, call providers, read secrets, drain queues, restart gateways, or authorize broad canonical writes.

Supported provider states:

- `healthy`
- `rate_limited`
- `cooling_down`
- `unhealthy`
- `disabled`
- `unknown`

State fields include:

- `provider_key`
- `provider_id`
- `provider_name`
- `model`
- `strength`
- `state`
- `last_success_at`
- `last_failure_at`
- `last_error_type`
- `cooldown_until`
- `last_probe_at`
- `last_recovered_at`
- `last_no_chunk_timeout_at`
- `active_for_task_classes`
- `denied_task_classes`
- `is_primary`
- `is_fallback`
- `sticky_for_development: false`

Fallback must never become sticky for high-complexity development tasks.

## Routing Rules

Implemented RPGL rules:

1. High-authority tasks require a strong primary provider.
2. A strong primary provider is selected first unless it is disabled, unhealthy, or still cooling down.
3. A primary rate-limit marks provider state as `cooling_down` and persists `cooldown_until`.
4. If a high-authority task is blocked by any primary provider failure at the shared execution-adapter boundary, fallback is denied and the task is queued for primary retry.
5. Non-high-authority tasks are still checked against the authority matrix before any fallback is attempted; weak fallback is denied unless the task class is explicitly weak-safe.
6. Weak-safe tasks may route to weak fallback with hard timeout policy.
7. Unknown task classes fail closed and are queued as needing operator approval.
8. When cooldown is expired, RPGL can probe primary and clear cooling-down state.
9. After primary recovery, high-authority tasks route back to primary.
10. Weak fallback never gains canonical write, shell, git, trust-tier, permission-matrix, provider-routing, or deployment authority.

## Timeout Policy

Default weak fallback timeout policy:

- `first_token_timeout_sec: 30`
- `no_chunk_timeout_sec: 60`
- `total_wall_time_sec: 180`
- `max_fallback_attempts: 1`

If no first token appears after 30 seconds, fallback aborts. If no chunks appear after 60 seconds, fallback aborts and the fallback provider is marked unhealthy. If wall time exceeds 180 seconds, fallback aborts. Weak fallback is not retried more than once for the same task.

`chaseos runtime provider fallback-timeout-proof first-token|no-chunks|wall-time|post-chunk-no-chunks` is a deterministic, simulated proof harness for these timeout outcomes. It does not call Ollama, OpenAI, Hermes, OpenClaw, or any provider; it does not read secret values; and it does not sleep for the timeout duration. It feeds simulated stream observations into the same RPGL timeout evaluator and timeout recorder used by the governance layer. The `no-chunks` scenario records `fallback_timeout_no_chunks` and `fallback_marked_unhealthy`; the first-token and wall-time scenarios record abort decisions without secretly promoting fallback authority.

`chaseos runtime provider ollama-timeout-contract success|first-token|no-chunks|wall-time|post-chunk-no-chunks` exercises the concrete local Ollama fallback wrapper contract through an injected stream runner. The wrapper builds the bounded Ollama request payload (`stream: true`, local fallback model default `phi4-mini:latest`, `num_ctx` capped at `16384`), checks the weak-provider authority matrix before starting any stream, rejects high-authority work before the stream runner can execute, enforces first-token/no-chunk/wall-time outcomes through RPGL timeout evaluation, marks fallback unhealthy on no-chunk timeout, and records provider audit events. The command still performs no live network call, reads no secret value, drains no queue, restarts no gateway, and mutates no canonical project files. It proves the wrapper contract with injected streams; live Ollama endpoint smoke remains unverified.

## Queue / Retry Packages

Queue items preserve:

- original request
- task class
- required provider strength
- primary provider id
- primary failure reason
- fallback denial reason
- cooldown state
- required context files
- related runtime/adapter
- approval status
- retry status
- retry attempts
- safe next step
- operator note
- `files_modified: false`

Queue statuses:

- `queued`
- `waiting_for_primary`
- `ready_for_retry`
- `retrying`
- `completed`
- `failed`
- `cancelled`
- `needs_operator_approval`

Initial retry is dry-run only unless later governance explicitly expands authority.

`chaseos runtime queue retry <id> --dry-run` now builds a retry package without draining the queue. The package preserves the original request, task class, required strength, required context files, related runtime/adapter, primary failure reason, fallback denial reason, approval state, retry status, and primary provider eligibility. It reports whether the item is ready for primary retry, what would route to primary, and which actions remain denied. It always reports `files_modified: false`, `queue_state_mutated: false`, `provider_state_mutated: false`, `canonical_files_mutated: false`, `queue_drained: false`, `live_provider_call_attempted: false`, and `secret_value_read: false`.

`chaseos runtime recover --dry-run` includes the same retry package previews for open queue items. It may identify a ready package after primary recovery/probe, but it still does not execute the queued task, increment retry attempts, call a provider, write code, or mark the queue item completed.

## Automatic Return To Primary

Implemented behavior:

1. `mark_primary_rate_limited` records cooldown state.
2. Serious work routes to queue while primary is cooling down.
3. A later route/probe checks whether cooldown has expired.
4. If the provider record is valid, `probe_provider(target="primary")` marks it healthy.
5. RPGL records `primary_probe_started`, `primary_probe_succeeded`, and `primary_recovered`.
6. High-authority tasks route back to primary after recovery.

Default probe mode is a local configuration/state probe. `probe_mode="network-dry-run"` builds a metadata-only provider probe plan from setup/provider registry status, writes audit evidence, and explicitly records that no network call was attempted, no secret value was read, and no provider state was mutated. `probe_mode="live-preflight"` adds the denied-by-default contract for a future live provider probe: it embeds the Gate operation `runtime.provider.live_probe`, approval schema `rpgl.live_provider_probe.v1`, required approval fields, a non-executing approval request template, and denial audit evidence. With `--write-approval-request`, live-preflight can persist a pending approval request artifact under `07_LOGS/Agent-Activity/_rpgl_provider_approvals/`. With `--gate-approval-id`, live-preflight can structurally validate a matching artifact.

`chaseos runtime provider executor-spec primary|fallback` is a separate non-executing executor-precondition report for future live probes. It reports `executor_status: not_built`, `execution_enabled: false`, `live_probe_execution_allowed: false`, and preconditions for Gate approval, approval artifact status, immutable approval decision records, approval-decision consumption, provider setup validity, secret-reference metadata, timeout policy, idempotency markers, and write-boundary limits. It can validate an existing `--gate-approval-id` and report whether a matching approved immutable decision exists, but it cannot write approval artifacts, consume an approval, call a provider, read secrets, mutate provider state, drain queues, restart gateways, or edit canonical files.

`chaseos runtime provider live-probe-approval-decision primary|fallback --gate-approval-id <id> --decision approved|denied` previews an append-only live-probe decision record. With `--write-decision`, it writes a single immutable record under `07_LOGS/Agent-Activity/_rpgl_provider_live_probe_decisions/`. It does not consume approval or decision, call a provider, read secrets, mutate provider state, drain queues, restart gateways, or write idempotency markers.

`chaseos runtime provider live-probe-decision-preflight primary|fallback --gate-approval-id <id>` validates the approval artifact, immutable decision record, and future marker absence without execution. A valid approved decision can report `approved_decision_record_valid_but_executor_not_built`; live probe execution still remains disabled.

`chaseos runtime provider live-probe-marker-contract primary|fallback --gate-approval-id <id>` computes the future idempotency marker path under `runtime/providers/state/provider_live_probe_markers/`, previews schema `rpgl.live_provider_probe_consumption_marker.v1`, and lists atomic create-new/write-before-network-call rules. It is no-write and does not create the marker directory or marker.

`chaseos runtime provider live-probe-decision-consumer primary|fallback --gate-approval-id <id> --write-consumer-record` writes a create-new-only consumer record under `07_LOGS/Agent-Activity/_rpgl_provider_live_probe_consumers/` after a valid approved immutable decision exists and before marker writing. It records `decision_consumed: true` in the separate consumer record while preserving the original approval request and decision artifact as immutable.

`chaseos runtime provider live-probe-atomic-marker-writer primary|fallback --gate-approval-id <id> --write-consumption-marker` writes a create-new-only idempotency marker under `runtime/providers/state/provider_live_probe_markers/` only after the valid approved decision and matching consumer record exist. It does not execute the provider call itself.

`chaseos runtime provider live-probe-executor-dry-run primary|fallback --gate-approval-id <id>` composes the provider record, Gate operation metadata, approval artifact, immutable approved decision, decision-consumer record, idempotency marker, setup metadata, secret-reference metadata, timeout policy, and denied action list into a single non-network executor readiness report. It can report `ready_for_live_executor_implementation` when the governance chain is complete, but it still returns `execution_enabled: false`, `live_probe_execution_allowed: false`, `live_network_call_attempted: false`, `secret_value_read: false`, and `provider_state_mutated: false`.

`chaseos runtime provider live-probe-executor primary|fallback --gate-approval-id <id> --execute-live-probe` consumes the completed governance chain without mutating the approval, decision, consumer, or marker records. It writes one result record under `runtime/providers/state/provider_live_probe_results/`, updates provider health state from the bounded probe outcome, records primary recovery or primary probe failure audit events where applicable, and blocks a second execution for the same `gate_approval_id`. The executor remains intentionally narrow: no queue drain, no gateway restart, no provider config edit, no canonical docs mutation, and no fallback stickiness for development.

Live-preflight, executor-spec, and executor-dry-run paths still perform no network call, read no secret value, mutate no provider state, and do not authorize live probe execution. Only the explicit live-probe executor command can attempt the bounded health probe, and real external provider smoke proof remains unverified in repo evidence.

## Provider Config Reconciliation

Implemented read-only surface:

```powershell
chaseos runtime provider config-report
chaseos runtime provider config-report --json
```

This report reconciles the active RPGL provider target profile against current repo config truth without changing provider setup. It reads only targeted provider/config metadata:

- `runtime/*/model_config.yaml`
- `runtime/setup_state.json`
- `.chaseos/config.yaml`
- selected `.codex`, `.claude`, and `runtime/policy/adapters/*` provider metadata files when present

It reports:

- active target primary model from `runtime/providers/provider_target_profile.json` when present
- legacy compatibility target `gpt-5.5` only when no provider target profile file exists
- runtime primary/fallback model declarations
- whether runtime primaries match the active target profile
- per-runtime fallback targets and fallback enforcement posture when declared
- OpenAI setup-state default model metadata
- local fallback setup posture
- local fallback `phi4`/Ollama references in targeted config files
- declared `num_ctx` / context-length values, with `16384` as the safe default ceiling for the current 16 GB local fallback machine

It does not:

- edit `runtime/*/model_config.yaml`
- edit `runtime/setup_state.json`
- edit `.chaseos/config.yaml`
- read secret values
- call OpenAI, Codex, Ollama, Hermes, or OpenClaw
- mutate provider health state
- create approval artifacts
- authorize provider config changes

The command appends an operator-visible RPGL audit event, but it does not create or mutate `provider_state.json`.

## Provider Config Change Plan

Implemented proposal surface:

```powershell
chaseos runtime provider config-plan
chaseos runtime provider config-plan --json
chaseos runtime provider config-plan --write-approval-request --requested-by operator
```

`config-plan` converts the read-only reconciliation report into a non-applying correction plan. It proposes, where mismatches exist:

- runtime primary model updates to the active provider target profile
- provider setup default-model corrections declared by the active target profile
- local fallback context policy review with `16384` as the safe local `num_ctx` ceiling

The default command is non-mutating and does not create queue items or proposal artifacts. With `--write-approval-request`, RPGL writes an operator-visible proposal artifact under:

```text
07_LOGS/Agent-Activity/_rpgl_provider_config_proposals/
```

and creates a provider queue item with:

- `task_class: runtime_config_change`
- `approval_status: needs_operator_approval`
- `retry_status: needs_operator_approval`
- `files_modified: false`

This proposal path still does not edit provider config, edit setup state, mutate provider health state, read secrets, call providers, drain queues, restart gateways, or authorize config changes. A later governed mutation pass must consume operator approval explicitly before any model config write occurs.

Implemented no-apply preflight:

```powershell
chaseos runtime provider config-apply-preflight <proposal_id>
chaseos runtime provider config-apply-preflight <proposal_id> --json
```

The apply-preflight command validates a provider config proposal before any future apply command exists. It checks:

- proposal record type and schema id
- proposal digest
- queue item existence
- queue status `needs_operator_approval`
- queue `files_modified: false`
- current runtime/setup/local fallback values still match the proposal's expected current values
- no config drift since proposal creation

It returns `preflight_status: ready_for_operator_approval` only when the proposal and queue still match current repo truth. It still reports `apply_enabled: false`, consumes no approval, edits no config, edits no setup state, mutates no provider state, drains no queue, reads no secrets, and calls no providers.

Implemented non-executing apply design:

```powershell
chaseos runtime provider config-apply-design <proposal_id>
chaseos runtime provider config-apply-design <proposal_id> --json
chaseos runtime provider config-apply-approval-request <proposal_id> --write-approval-request --json
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
```

`config-apply-design` composes the no-apply preflight with a Gate approval schema for future operation `runtime.provider.config_apply` / schema `rpgl.provider_config_apply.v1`. It reports:

- proposal id and queue item id
- apply-preflight status
- target writes that would be eligible only after approval
- local fallback context policy as blocked until an active local OSS config target exists
- proposed-changes digest
- rollback plan
- post-apply verification commands
- executor preconditions
- blocked reasons

It returns `executor_status: not_built`, `execution_enabled: false`, and `apply_execution_allowed: false`. It does not consume approval, write approval artifacts, edit provider config, edit setup state, mutate provider state, drain queues, read secrets, call providers, restart gateways, or write canonical docs.

`config-apply-approval-request` is the request-only artifact surface for the same schema. With `--write-approval-request`, it writes a pending record under `07_LOGS/Agent-Activity/_rpgl_provider_config_apply_approvals/` containing the proposal id, queue item id, active target primary model, proposed changes digest, reviewed target paths, rollback plan, and post-apply verification requirements. Existing artifacts keep the `expected_primary_model` compatibility field, but new reconciliation truth is target-profile driven. With `--gate-approval-id`, it structurally validates an existing artifact against the current apply design. Both modes keep `execution_enabled: false`, `apply_execution_allowed: false`, `approval_consumed: false`, `provider_config_mutated: false`, and `setup_state_mutated: false`.

`config-apply-approval-decision` records the operator decision separately from the request artifact. Without `--write-decision`, it previews an immutable decision record. With `--write-decision`, it writes an append-only record under `07_LOGS/Agent-Activity/_rpgl_provider_config_apply_decisions/` for one `gate_approval_id`, with `--decision approved|denied`, `--requested-by`, and optional `--reason`. It does not mutate the original approval request artifact, does not consume the decision, and does not allow apply. A second decision for the same `gate_approval_id` is blocked as `immutable_decision_already_exists`.

`config-apply-decision-preflight` is the no-mutation decision-record validation, future consumption, and idempotency check for a future executor. It requires an existing `--gate-approval-id`, rebuilds the apply design, validates the approval request artifact against the design, validates any immutable decision record under `07_LOGS/Agent-Activity/_rpgl_provider_config_apply_decisions/`, checks the future idempotency marker path under `runtime/providers/state/provider_config_apply_markers/`, and reports whether the run is blocked by missing/duplicate/invalid/denied decision records, an existing marker, or the still-unbuilt live executor. A valid approved immutable decision record can make the preflight report `approved_decision_record_valid_but_executor_not_built`, while still keeping execution disabled. It never changes the approval artifact, changes the decision record, writes the marker, consumes approval or decision, edits provider config, edits setup state, mutates provider state, drains queue, restarts gateways, reads secrets, or calls providers. It appends only RPGL audit events.

`config-apply-decision-consumption-plan` is the no-mutation contract for a future single-use decision consumer. It composes decision preflight, selects the approved immutable decision record when one exists, computes the future consumption/idempotency marker under `runtime/providers/state/provider_config_apply_markers/`, previews the marker payload schema `rpgl.provider_config_apply_consumption_marker.v1`, lists atomic create-new/write-before-mutation rules, and reports required preconditions for the future consumer, atomic marker writer, and live apply executor. It does not write the marker, consume approval or decision, mutate the decision record, mutate the approval artifact, edit provider config, edit setup state, mutate provider state, drain queue, restart gateways, read secrets, call providers, or apply config.

`config-apply-decision-consumer-design` is the no-write contract for the future approval-decision consumer. It composes the decision consumption plan, reports consumer readiness, previews consumer record schema `rpgl.provider_config_apply_decision_consumer.v1`, defines digest/path/immutable-record checks, forbidden consumer fields, failure handling, and the handoff requirement to the atomic marker writer. It preserves immutable decision records and original approval artifacts; consumption must be represented through a separate consumer record plus future marker, not by editing the decision or approval artifact. It does not write consumer records, create directories, write markers, consume approval or decision, mutate decision records or approval artifacts, edit provider config, edit setup state, mutate provider state, drain queue, restart gateways, read secrets, call providers, or apply config.

`config-apply-decision-consumer-preflight` is the no-write invocation preflight for the future approval-decision consumer. It composes the consumer design, reports whether a future consumer invocation is allowed or blocked, binds the selected immutable decision id/ref and approval/decision digests when available, checks the idempotency marker path, and lists stop conditions plus handoff requirements before any consumer implementation exists. It writes no consumer preflight record, consumer record, marker directory, or marker; it consumes no approval or decision; and it mutates no approval artifact, decision record, provider config, setup state, provider state, queue, gateway, secrets, or provider/network surface.

`config-apply-decision-consumer-implementation-plan` is the no-write implementation contract for the future explicit-write consumer writer. It composes the consumer preflight, declares future command shape and required `--write-consumer-record` flag, previews the sanitized consumer record schema/path under `07_LOGS/Agent-Activity/_rpgl_provider_config_apply_consumers/`, lists create-new/write-before-marker handoff ordering, and keeps all write support disabled. It does not create the consumer directory, write consumer records, write markers, consume approval or decision, mutate approval artifacts or decision records, edit provider config, edit setup state, mutate provider state, drain queue, restart gateways, read secrets, call providers, or apply config.

`config-apply-decision-consumer-writer-dry-run` is the no-write simulation of the future explicit-write consumer writer. It composes the implementation plan, previews the exact candidate consumer record payload, computes a deterministic consumer record digest, checks selected decision/digest/marker/path preconditions, and reports dry-run steps. It does not create the consumer directory, write consumer records, write markers, consume approval or decision, mutate approval artifacts or decision records, edit provider config, edit setup state, mutate provider state, drain queue, restart gateways, read secrets, call providers, or apply config.

`config-apply-decision-consumer-write-guard-contract` is the no-write contract for the real consumer writer's write boundary. It composes the writer dry-run, declares the required explicit `--write-consumer-record` flag, fail-closed flag validation, create-new-only consumer record policy, consumer path/digest/idempotency preconditions, and marker-writer handoff requirements. The guard-contract command itself keeps real writes disabled; it does not create the consumer directory, write consumer records, write markers, consume approval or decision, mutate approval artifacts or decision records, edit provider config, edit setup state, mutate provider state, drain queue, restart gateways, read secrets, call providers, or apply config.

`config-apply-decision-consumer` is the guarded consumer-record writer for approved immutable decision records. It requires `--write-consumer-record`, reruns the write-guard contract immediately before writing, requires exactly one valid approved immutable decision record, requires the idempotency marker to be absent, writes a single consumer record under `07_LOGS/Agent-Activity/_rpgl_provider_config_apply_consumers/` with create-new-only semantics, and stops before marker writing or provider config apply. It does not mutate the original approval artifact or immutable decision record, does not write the idempotency marker, does not edit provider config, edit setup state, mutate provider state, drain queue, restart gateways, read secrets, call providers, or apply config. If the immutable decision is missing, denied, invalid, duplicated, or already consumed by an existing consumer record, it fails closed.

`config-apply-atomic-marker-writer` is the guarded idempotency marker writer. It requires `--write-consumption-marker`, requires a valid approved immutable decision record, requires a matching consumer record under `07_LOGS/Agent-Activity/_rpgl_provider_config_apply_consumers/`, verifies the consumer record digest and mutation claims, and writes the marker under `runtime/providers/state/provider_config_apply_markers/` with exclusive create-new semantics. It does not mutate the consumer record, approval artifact, or immutable decision record, and it does not edit provider config, edit setup state, mutate provider state, drain queue, restart gateways, read secrets, call providers, or apply config.

`config-apply-atomic-marker-writer-design` is the no-write contract for the marker writer. It composes the decision consumer design, reports writer readiness, previews marker payload schema `rpgl.provider_config_apply_atomic_marker_writer.v1`, defines path constraints, exclusive create-new semantics, forbidden marker fields, failure handling, and preconditions. It does not create directories, write markers, consume approval or decision, mutate decision records or approval artifacts, edit provider config, edit setup state, mutate provider state, drain queue, restart gateways, read secrets, call providers, or apply config.

`config-apply-executor` is the guarded live provider config apply executor. It requires `--apply-provider-config`, requires a structurally valid apply approval request, exactly one valid approved immutable decision record, a matching decision-consumer record, a matching idempotency marker, no existing result record, no current-value drift, and target paths limited to reviewed runtime model/setup files. It applies only enabled target writes, verifies post-apply values, writes a create-new-only result record under `runtime/providers/state/provider_config_apply_results/`, and rolls back applied writes if verification fails. It does not read secrets, call providers, mutate provider health state, drain queues, restart gateways, or mutate approval/decision/consumer/marker records. A second executor invocation for the same `gate_approval_id` is blocked by the result record.

`config-apply-executor-dry-run` is the next non-mutating step toward a live apply executor. It composes decision preflight with a dry-run target write plan, rollback snapshot, idempotency marker payload preview, post-apply verification plan, stop conditions, and an RPGL feature completion tracker. It reports `executor_status: dry_run_plan_only`, `live_apply_supported: false`, `execution_enabled: false`, and `apply_execution_allowed: false`. It does not consume approval, mutate the approval artifact, write idempotency markers, edit provider config, edit setup state, mutate provider state, drain queue, restart gateways, read secrets, call providers, or perform live apply.

## RPGL Completion Tracker

Current feature status: COMPLETE TARGETED / IMPLEMENTED FOUNDATION / LIVE PROVIDER PROOF DEFERRED.

Done:

- provider strength classification
- task-class capability gate
- weak fallback denial for high-authority work
- queue-on-denial records
- fallback timeout decision records
- primary cooldown/recovery state
- provider status CLI
- active provider target profile report
- target-profile plan/proposal/queue request without writing the active profile file
- provider config reconciliation
- provider config proposal/queue request
- provider config apply preflight
- provider config apply design
- provider config apply approval request artifacts
- immutable provider config apply approval decision records
- immutable approval decision record validation
- provider config apply decision/idempotency preflight
- provider config apply decision consumption plan
- provider config apply decision consumer design
- provider config apply decision consumer invocation preflight
- provider config apply decision consumer implementation plan
- provider config apply decision consumer writer dry-run
- provider config apply decision consumer write-guard contract
- provider config apply guarded decision consumer record writer
- provider config apply guarded atomic marker writer
- provider config apply atomic marker writer design
- provider config apply guarded live executor
- rollback execution after failed apply verification
- provider config apply executor dry-run plan
- shared execution-adapter capability gate for Hermes/OpenClaw synthesis fallback attempts
- primary non-rate provider failures can mark primary `unhealthy` before queue/denial decisions
- live-probe immutable approval decision record preview/write/validation helpers
- live-probe approval decision CLI preview/write
- live-probe decision preflight and marker-contract CLI surfaces
- live-probe guarded decision consumer record writer
- live-probe guarded atomic marker writer
- live-probe non-network executor dry-run/readiness plan
- live-probe read-only live-smoke readiness report
- live-probe read-only live-smoke closeout plan
- read-only RPGL completion-status report with acceptance-criteria and deferred-live-proof status
- live-probe guarded executor with create-new result records and provider-state update from bounded probe outcome
- live-probe executor-spec approved immutable decision-record precondition reporting
- simulated fallback timeout proof for first-token, no-chunk, post-chunk-no-chunk, and wall-time outcomes
- local Ollama streaming timeout wrapper contract through injected streams, including success, first-token, no-chunk, post-chunk no-chunk, wall-time, and high-authority denial behavior
- queue retry package dry-run proof through `chaseos runtime queue retry <id> --dry-run`
- recovery dry-run retry package previews through `chaseos runtime recover --dry-run`
- runtime adapter governance RPGL consumption report through `chaseos runtime adapter-governance`
- audit events for the above

Remaining operator-approved proof deferred outside the current development closeout:

- live real-provider smoke proof against OpenAI/Codex and local Ollama where operator approval and credentials/endpoints allow
- live Ollama endpoint first-token/no-chunk timeout smoke through the implemented wrapper contract
- resolution of current live-smoke blockers: runtime model config mismatch with the active provider target profile, missing local Ollama fallback setup, pending target-profile-matching live-probe approvals, and missing live-probe decision/consumer/marker/result chain evidence
- optional operator-approved write of `runtime/providers/provider_target_profile.json`; if absent, RPGL uses the legacy GPT-5.5 compatibility target only as a default and not as permanent source truth
- live Hermes/OpenClaw operational proof if a future adapter-local provider path is added; current static governance report shows no direct provider calls in Hermes/OpenClaw watch paths and shared synthesis remains behind RPGL
- Discord read-only/dry-run surface if kept in scope

Development done means the governance layer, CLI status/recovery surfaces, capability gate, queue/retry path, fallback timeout contracts, approval chains, executor guard, adapter seams, audit events, and completion-status reporting are implemented and tested. Live provider proof remains a separate operator-approved evidence step because it may call external/local providers, read secret metadata, and mutate provider state.

## Scheduled / Night Boundaries

Implemented dry-run surface:

```powershell
chaseos runtime recover --dry-run
```

Allowed in dry-run:

- inspect provider state
- inspect queue
- identify cooldown-expired primaries
- prepare metadata-only provider probe plans for cooldown-expired primaries
- identify queue items ready for primary
- prepare retry package previews without draining queue
- write provider audit events
- summarize next actions

Denied by default:

- apply code patches
- edit provider config
- edit security policy
- edit trust tiers
- edit permission matrix
- restart gateways
- change Hermes/OpenClaw service config
- push commits
- deploy
- delete or move files
- drain high-complexity queue automatically

No cron job, Windows scheduled task, or background service is installed by RPGL.

## Hermes / OpenClaw Integration

Live integration:

- Hermes/OpenClaw model configs are discovered through `runtime/{runtime}/model_config.yaml`.
- Hermes/OpenClaw provider records are classified by provider strength.
- Execution adapter rate-limit handling writes RPGL cooldown state.
- Execution adapter primary non-rate failures can mark the primary provider `unhealthy`.
- Execution adapter high-authority requests are queued instead of being sent to fallback after primary provider failure.
- Execution adapter fallback attempts are capability-gated against the RPGL authority matrix before any configured fallback model is called.
- `runtime/adapters/runtime_governance.py` now emits a read-only `rpgl_consumption` report proving the shared execution adapter imports/uses RPGL routing markers, Hermes review synthesis imports the shared adapter with `execution_adapter="hermes"`, and OpenClaw watch remains bus-dispatch-only with no direct provider call markers.
- `chaseos runtime adapter-governance` exposes that OpenClaw/Hermes adapter-governance and RPGL-consumption report in text or JSON form.

Bounded seam:

- Hermes/OpenClaw can consume `route_task`, provider state, queue records, and audit events.
- Current adapter boundary remains unchanged: RPGL does not grant Hermes/OpenClaw new write authority.

Future work:

- live real-provider smoke evidence for the guarded provider-network probe executor
- richer adapter health report ingestion
- live OpenClaw/Hermes provider-path proof only if a future adapter-local provider path is introduced

## CLI Surface

Implemented:

```powershell
chaseos runtime status
chaseos runtime adapter-governance
chaseos runtime providers
chaseos runtime fallback-status
chaseos runtime queue list
chaseos runtime queue show <id>
chaseos runtime queue retry <id> --dry-run
chaseos runtime provider probe primary
chaseos runtime provider probe fallback
chaseos runtime provider probe primary --probe-mode network-dry-run
chaseos runtime provider probe primary --probe-mode live-preflight
chaseos runtime provider probe primary --probe-mode live-preflight --write-approval-request
chaseos runtime provider probe primary --probe-mode live-preflight --gate-approval-id <id>
chaseos runtime provider executor-spec primary
chaseos runtime provider executor-spec primary --gate-approval-id <id>
chaseos runtime provider live-probe-approval-decision primary --gate-approval-id <id> --decision approved|denied
chaseos runtime provider live-probe-approval-decision primary --gate-approval-id <id> --decision approved|denied --write-decision
chaseos runtime provider live-probe-decision-preflight primary --gate-approval-id <id>
chaseos runtime provider live-probe-marker-contract primary --gate-approval-id <id>
chaseos runtime provider live-probe-decision-consumer primary --gate-approval-id <id> --write-consumer-record
chaseos runtime provider live-probe-atomic-marker-writer primary --gate-approval-id <id> --write-consumption-marker
chaseos runtime provider live-probe-executor-dry-run primary --gate-approval-id <id>
chaseos runtime provider live-probe-target-approval-plan all
chaseos runtime provider live-probe-target-approval-plan primary --write-approval-request --requested-by operator
chaseos runtime provider live-smoke-readiness
chaseos runtime provider live-smoke-closeout-plan
chaseos runtime provider completion-status
chaseos runtime provider live-probe-executor primary --gate-approval-id <id> --execute-live-probe
chaseos runtime provider fallback-timeout-proof no-chunks
chaseos runtime provider ollama-timeout-contract success
chaseos runtime provider target-profile
chaseos runtime provider target-profile-plan
chaseos runtime provider target-profile-plan gpt-5.5 --write-approval-request --requested-by operator
chaseos runtime provider config-report
chaseos runtime provider config-plan
chaseos runtime provider config-plan --write-approval-request --requested-by operator
chaseos runtime provider config-apply-preflight <proposal_id>
chaseos runtime provider config-apply-design <proposal_id>
chaseos runtime provider config-apply-approval-request <proposal_id> --write-approval-request --requested-by operator
chaseos runtime provider config-apply-approval-request <proposal_id> --gate-approval-id <id>
chaseos runtime provider config-apply-approval-decision <proposal_id> --gate-approval-id <id> --decision approved|denied
chaseos runtime provider config-apply-decision-preflight <proposal_id> --gate-approval-id <id>
chaseos runtime provider config-apply-decision-consumption-plan <proposal_id> --gate-approval-id <id>
chaseos runtime provider config-apply-decision-consumer-design <proposal_id> --gate-approval-id <id>
chaseos runtime provider config-apply-decision-consumer-preflight <proposal_id> --gate-approval-id <id>
chaseos runtime provider config-apply-decision-consumer-implementation-plan <proposal_id> --gate-approval-id <id>
chaseos runtime provider config-apply-decision-consumer-writer-dry-run <proposal_id> --gate-approval-id <id>
chaseos runtime provider config-apply-atomic-marker-writer-design <proposal_id> --gate-approval-id <id>
chaseos runtime provider config-apply-executor <proposal_id> --gate-approval-id <id> --apply-provider-config
chaseos runtime provider config-apply-executor-dry-run <proposal_id> --gate-approval-id <id>
chaseos gate check-operation runtime.provider.config_apply
chaseos gate check-operation runtime.provider.live_probe --external-api provider.openai
chaseos runtime recover --dry-run
chaseos runtime audit-tail
```

JSON is available through the existing `--json` flag.

`chaseos runtime provider-status` remains the older read-only aggregator and is not removed.

## Discord Control-Plane Mapping

Current status: DOCS-ONLY / NOT WIRED as live slash commands.

Repo truth on 2026-04-30 shows Discord currently enters ChaseOS through `agent-bus ingress discord`, where bound channel posture is translated into bus task state. That is not the same as a synchronous read-only slash command responder, so RPGL does not claim live Discord commands yet.

Planned read-only/dry-run mappings:

| Discord surface | ChaseOS CLI equivalent | Boundary |
| --- | --- | --- |
| `/runtime status` | `chaseos runtime status` | read-only status |
| `/provider status` | `chaseos runtime providers` or `chaseos runtime provider-status` | read-only status |
| `/fallback status` | `chaseos runtime fallback-status` | read-only status |
| `/queue list` | `chaseos runtime queue list` | read-only queue inspection |
| `/queue show <id>` | `chaseos runtime queue show <id>` | read-only queue inspection |
| `/runtime recover dry-run` | `chaseos runtime recover --dry-run` | dry-run only; no queue drain |

## Audit Events

RPGL writes audit records to:

```text
runtime/providers/state/provider_audit.jsonl
```

Supported audit events:

- `primary_rate_limited`
- `primary_entered_cooldown`
- `primary_probe_started`
- `primary_probe_succeeded`
- `primary_probe_failed`
- `primary_recovered`
- `primary_recovery_failed`
- `fallback_attempt_started`
- `fallback_allowed_by_capability`
- `fallback_denied_by_capability`
- `fallback_timeout_first_token`
- `fallback_timeout_no_chunks`
- `fallback_timeout_wall_time`
- `fallback_timeout_proof_requested`
- `fallback_marked_unhealthy`
- `task_queued_for_primary_retry`
- `queue_item_created`
- `queue_item_retried`
- `queue_item_completed`
- `queue_item_failed`
- `provider_status_requested`
- `provider_state_updated`
- `provider_target_profile_requested`
- `provider_live_probe_preflight_started`
- `provider_live_probe_gate_approval_schema_built`
- `provider_live_probe_approval_request_created`
- `provider_live_probe_approval_request_validated`
- `provider_live_probe_approval_request_invalid`
- `provider_live_probe_approval_decision_previewed`
- `provider_live_probe_approval_decision_created`
- `provider_live_probe_decision_record_validated`
- `provider_live_probe_decision_record_invalid`
- `provider_live_probe_decision_preflight_requested`
- `provider_live_probe_marker_contract_requested`
- `provider_live_probe_decision_consumer_record_write_blocked`
- `provider_live_probe_decision_consumer_record_written`
- `provider_live_probe_atomic_marker_write_blocked`
- `provider_live_probe_atomic_marker_written`
- `provider_live_probe_executor_blocked`
- `provider_live_probe_executor_started`
- `provider_live_probe_executor_completed`
- `provider_live_probe_executor_dry_run_requested`
- `provider_live_probe_smoke_readiness_requested`
- `provider_live_smoke_closeout_plan_requested`
- `provider_live_probe_executor_spec_requested`
- `provider_live_probe_result_record_written`
- `provider_config_reconciliation_requested`
- `provider_config_change_plan_requested`
- `provider_config_change_approval_request_created`
- `provider_config_apply_preflight_requested`
- `provider_config_apply_design_requested`
- `provider_config_apply_approval_request_created`
- `provider_config_apply_approval_request_validated`
- `provider_config_apply_approval_request_invalid`
- `provider_config_apply_approval_decision_previewed`
- `provider_config_apply_approval_decision_created`
- `provider_config_apply_decision_record_validated`
- `provider_config_apply_decision_record_invalid`
- `provider_config_apply_decision_consumption_plan_requested`
- `provider_config_apply_decision_consumer_design_requested`
- `provider_config_apply_decision_consumer_preflight_requested`
- `provider_config_apply_decision_consumer_implementation_plan_requested`
- `provider_config_apply_decision_consumer_writer_dry_run_requested`
- `provider_config_apply_decision_consumer_write_guard_contract_requested`
- `provider_config_apply_decision_consumer_record_write_blocked`
- `provider_config_apply_decision_consumer_record_written`
- `provider_config_apply_atomic_marker_write_blocked`
- `provider_config_apply_atomic_marker_written`
- `provider_config_apply_atomic_marker_writer_design_requested`
- `provider_live_probe_preflight_denied`
- `runtime_status_requested`
- `scheduled_recovery_dry_run_started`
- `scheduled_recovery_dry_run_completed`

## Non-Goals

RPGL does not:

- expose gateways publicly
- change gateway bind addresses
- install schedules or services
- grant weak fallback shell/git/write authority
- let weak fallback edit canonical ChaseOS docs or protected runtime policy
- drain high-authority queue automatically
- replace ChaseOS Gate, permission matrix, or trust tiers
- claim live OpenAI/Ollama enforcement unless tests or live commands prove it

## Current Verification

Tested through targeted RPGL tests on 2026-05-03:

- capability denial for weak fallback on high-authority tasks
- weak-safe fallback allowance
- high-authority queue creation on primary cooldown
- first-token/no-chunk/wall-time fallback timeout decisions
- no-chunk fallback unhealthy marking
- simulated `chaseos runtime provider fallback-timeout-proof` scenarios for first-token, no-chunks, post-chunk-no-chunks, and wall-time timeout decisions without provider calls, secret reads, wall-clock waits, gateway mutation, queue drains, or canonical file mutation
- injected `chaseos runtime provider ollama-timeout-contract` scenarios for local Ollama wrapper success, first-token timeout, no-chunk timeout, wall-time timeout, and high-authority weak-fallback denial without provider calls, secret reads, queue drains, gateway mutation, fallback stickiness, or canonical file mutation
- fail-closed fallback provider selection when a requested fallback provider id is absent from configured fallback records
- primary cooldown expiry and return-to-primary routing
- recovery dry-run boundary
- queue retry dry-run package creation for waiting and ready queue items without queue/state/canonical mutation
- recovery dry-run retry package previews without queue drain, provider calls, secret reads, retry-attempt increments, or fallback use
- metadata-only provider `network-dry-run` probe plans that do not read secrets, call external endpoints, or mutate provider state
- denied-by-default provider `live-preflight` contracts that require Gate/operator approval before any future external provider call
- Gate operation schema exposure for `runtime.provider.live_probe` through `chaseos gate check-operation`, still blocked without approval and still non-executing
- pending RPGL live-probe approval request artifact persistence through `--write-approval-request`
- structural RPGL live-probe approval artifact validation through `--gate-approval-id`
- immutable RPGL live-probe approval decision record preview/write/validation helpers under `07_LOGS/Agent-Activity/_rpgl_provider_live_probe_decisions/`, tested without provider calls, secret reads, provider-state mutation, queue drain, gateway restart, approval artifact mutation, or execution
- non-executing `chaseos runtime provider executor-spec primary|fallback` reports future live-probe executor preconditions, validates existing approval artifacts, and reports approved immutable decision-record presence without executing or consuming them
- `chaseos runtime provider live-probe-approval-decision primary|fallback --gate-approval-id <id> --decision approved|denied` previews or writes immutable live-probe approval decision records without consuming approval/decision, writing markers, calling providers, reading secrets, mutating provider state, draining queues, or restarting gateways
- `chaseos runtime provider live-probe-decision-preflight primary|fallback --gate-approval-id <id>` validates approval/decision/marker preconditions and can report `approved_decision_record_valid_but_executor_not_built` while keeping execution disabled
- `chaseos runtime provider live-probe-marker-contract primary|fallback --gate-approval-id <id>` previews the future single-use marker contract under `runtime/providers/state/provider_live_probe_markers/` without creating directories, writing markers, consuming approval/decision, calling providers, reading secrets, mutating provider state, draining queues, or restarting gateways
- `chaseos runtime provider live-probe-decision-consumer primary|fallback --gate-approval-id <id> --write-consumer-record` writes a guarded create-new-only consumer record after a valid approved immutable decision exists, while keeping approval/decision artifacts immutable and provider calls, secret reads, provider-state mutation, queue drains, gateway restarts, and marker writes disabled
- `chaseos runtime provider live-probe-atomic-marker-writer primary|fallback --gate-approval-id <id> --write-consumption-marker` writes a guarded create-new-only marker after a valid approved decision and matching consumer record exist, while keeping live provider execution, provider calls, secret reads, provider-state mutation, queue drains, and gateway restarts disabled
- `chaseos runtime provider live-probe-executor primary|fallback --gate-approval-id <id> --execute-live-probe` executes a guarded one-shot health probe only after the full governance chain exists, writes a create-new result record, updates provider state from the bounded outcome, blocks duplicate execution, and keeps queue drains, gateway restarts, provider config edits, canonical docs mutation, and fallback stickiness disabled; tests use an injected runner, not a real provider call
- read-only `chaseos runtime provider live-smoke-readiness` reports final live-smoke blockers across model config truth, local fallback setup, live-probe approval requests, decision/consumer/marker/result chain readiness, and no-execution flags without writing approval artifacts, calling providers, reading secrets, mutating provider state, draining queues, restarting gateways, or editing canonical files
- read-only `chaseos runtime provider live-smoke-closeout-plan` reports the ordered no-mutation command sequence from current blockers to approved live smoke, including provider config approval/apply chain, local fallback metadata decision, target-matching live-probe approval requests, immutable live-probe decisions, consumer/marker writes, and final guarded executor command
- read-only `chaseos runtime provider completion-status` reports final RPGL feature status, remaining major pass count, live-provider proof deferral, acceptance-criteria status, target profile/config truth, queue summary, and blocked live-smoke reasons without writing approval artifacts, calling providers, reading secrets, mutating provider state, draining queues, restarting gateways, or editing canonical files
- read-only `chaseos runtime provider config-report` reconciles current provider/model config truth against the active provider target profile, reports local fallback and context posture, and does not mutate provider state or provider config
- read-only `chaseos runtime provider target-profile` reports the active primary/fallback target profile; when no profile file exists, the current GPT-5.5 expectation is only a legacy compatibility target, not a permanent hardcoded truth
- `chaseos runtime provider target-profile-plan [MODEL]` builds a portable candidate target profile for the supplied/current model, preserves runtime fallback chains, and can write only a proposal artifact plus `needs_operator_approval` queue item without writing the active target-profile file or mutating runtime/provider config
- `chaseos runtime provider config-plan` builds a provider-config correction proposal and can write a review artifact plus `needs_operator_approval` queue item without editing provider config or setup state
- `chaseos runtime provider config-apply-preflight <proposal_id>` validates proposal, queue, digest, and current-value drift while keeping apply disabled
- `chaseos runtime provider config-apply-design <proposal_id>` reports the future approved apply executor design, Gate schema `rpgl.provider_config_apply.v1`, target writes, rollback plan, post-apply verification, and blocked preconditions while keeping execution disabled
- `chaseos runtime provider config-apply-approval-request <proposal_id>` writes or validates pending request-only apply approval artifacts for `rpgl.provider_config_apply.v1` without applying provider config, consuming approval, calling providers, mutating provider state, draining queues, or restarting gateways
- `chaseos runtime provider config-apply-approval-decision <proposal_id> --gate-approval-id <id> --decision approved|denied` previews or writes immutable approval decision records without mutating the request artifact or enabling apply
- `chaseos runtime provider config-apply-decision-preflight <proposal_id> --gate-approval-id <id>` validates immutable approval decision records and idempotency readiness for a future executor without consuming approval/decision, writing idempotency markers, applying provider config, mutating setup/provider state, draining queues, or restarting gateways
- `chaseos runtime provider config-apply-decision-consumption-plan <proposal_id> --gate-approval-id <id>` reports the future single-use consumption marker schema, selected immutable decision record, atomic create-new rules, and preconditions without writing markers, consuming approval/decision, or applying provider config
- `chaseos runtime provider config-apply-decision-consumer-design <proposal_id> --gate-approval-id <id>` reports the future approval-decision consumer design, consumer record schema, immutable-record/digest/path checks, forbidden consumer fields, and marker-writer handoff requirement without writing consumer records, creating directories, writing markers, consuming approval/decision, or applying provider config
- `chaseos runtime provider config-apply-decision-consumer-preflight <proposal_id> --gate-approval-id <id>` reports whether a future decision consumer invocation is allowed or blocked, binds selected immutable decision/digest metadata when available, and lists stop conditions plus handoff requirements without writing preflight/consumer records, creating marker directories, writing markers, consuming approval/decision, or applying provider config
- `chaseos runtime provider config-apply-decision-consumer-implementation-plan <proposal_id> --gate-approval-id <id>` reports the future explicit-write consumer writer contract, sanitized consumer record path/schema, required write flag, and marker-writer handoff sequence without creating the consumer directory, writing consumer records, writing markers, consuming approval/decision, or applying provider config
- `chaseos runtime provider config-apply-decision-consumer-writer-dry-run <proposal_id> --gate-approval-id <id>` previews the candidate consumer record payload and digest while keeping directory creation, consumer record writes, marker writes, approval/decision consumption, and provider config apply disabled
- `chaseos runtime provider config-apply-atomic-marker-writer-design <proposal_id> --gate-approval-id <id>` reports the future exclusive-create marker writer design, path constraints, forbidden marker fields, and failure policy without creating directories, writing markers, consuming approval/decision, or applying provider config
- `chaseos runtime provider config-apply-executor <proposal_id> --gate-approval-id <id> --apply-provider-config` applies approved provider config targets only after the valid approval/decision/consumer/marker chain exists, verifies results, writes a create-new result record, and rolls back applied writes if verification fails
- `chaseos runtime provider config-apply-executor-dry-run <proposal_id> --gate-approval-id <id>` reports future apply target writes, rollback snapshot, idempotency marker preview, post-apply verification, stop conditions, and feature completion tracker while keeping live apply disabled
- CLI command contract and JSON contract compatibility

Deferred live evidence:

- live external provider probe against OpenAI/Codex using the implemented executor
- live local Ollama provider probe using the implemented executor
- live Ollama streaming timeout enforcement against the actual local Ollama endpoint
- current live-smoke blocker resolution: governed target-profile decision, active model config truth alignment, local Ollama fallback setup, approved immutable live-probe decisions, decision-consumer records, idempotency markers, and result-directory readiness
- operator-approved active target-profile file write and provider config mutation from the reconciliation report
- live execution against the current pending provider config apply artifact, which is still blocked on missing immutable decision/consumer/marker evidence
- immutable operator approval decisions/signatures for RPGL artifacts
- live Discord slash command responder wiring
- automatic schedule execution


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
