---
title: ChaseOS MVP Credential Readiness Checklist
type: credential-readiness-checklist
status: CURRENT / CHECKLIST COMPLETE / VALIDATION FAILS CLOSED / PROVIDER EXECUTION BLOCKED
created: 2026-05-13
updated: 2026-05-15
runtime: Codex
session_descriptor: credential-readiness-repair
---

# ChaseOS MVP Credential Readiness Checklist

## Bottom Line

ChaseOS can now run a simple live read-only Codex Agent Bus task, but provider-backed Chat/Studio workflows are still blocked.

2026-05-15 correction: the P0 OpenAI key may live inside the local ChaseOS install in the root `.env` file. That file is gitignored and loaded by the ChaseOS CLI. The boundary is not "outside ChaseOS"; it is "outside Git-tracked/canonical truth." `runtime/setup_state.json` should still store only the reference name `OPENAI_API_KEY`, never the key value.

2026-05-14 continuation check: `setup provider validate openai --json` and the OpenAI row inside `setup validate --json` still fail closed with `valid=false`, missing check `secret_reference_resolvable`, target `SET_OPENAI_SECRET_REF`, and probe error `reference_not_found`. They now also expose top-level no-secret aliases for shallow consumers: `secret_reference_target_is_placeholder=true`, `secret_reference_resolvable=false`, `secret_reference_probe_source=env-var-or-local-secret-ref`, and `secret_reference_probe_error=reference_not_found`, while preserving the nested `secret_reference_probe`. `mvp credential-handoff --json` still identifies P0 `openai_secret_reference`, recommended reference name `OPENAI_API_KEY`, `safe_to_call_update_goal_complete=false`, and no secret values/provider calls/setup writes/approval actions/Agent Bus writes/browser or host control/canonical mutation. It also now exposes top-level completion aliases, `completion_decision`, and `required_operator_inputs` matching the other MVP handoff surfaces. The machine-readable credential handoff and completion audit now include the reconciled current P0 guide at `07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md`; the filename is retained for links, but the guide is current P0 handoff, not optional future work.

2026-05-15 credential handoff safety-contract sync: `mvp credential-handoff --json` now also exposes `completion_safety_contract` with `status=blocked_do_not_call_update_goal_complete`, `checklist_coverage_is_not_completion=true`, `update_goal_allowed=false`, and P0 `openai_secret_reference` in the current repo. Non-JSON `mvp credential-handoff` prints the same compact safety line before the P0 credential row. This does not resolve the OpenAI reference, perform a provider call, write setup metadata, or authorize `update_goal complete`.

2026-05-15 OpenAI secret-reference dry-run readiness recheck: boolean-only checks returned `User=False` and `Process=False` for `OPENAI_API_KEY` in the active Codex process. The metadata preview for `secret_reference_target=OPENAI_API_KEY` succeeded in dry-run mode and reported `writes_setup_state=false`, `provider_calls_performed=false`, `secret_values_read=false`, and `secret_values_visible=false`; no setup metadata write was performed. `setup provider validate openai --json` and `setup validate --json` still fail closed on the current placeholder target `SET_OPENAI_SECRET_REF` with `secret_reference_resolvable=false` and `reference_not_found`. `runtime provider live-smoke-readiness --json` still reports `ready_for_live_smoke=false` and `update_goal_allowed=false`.

2026-05-14 operator-action pointer check: `mvp operator-action-required --json` now includes `handoff_guide_path=07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md` on the P0 `openai_secret_reference` action while preserving `safe_to_call_update_goal_complete=false` and no-secret/no-provider-call authority. It also carries the shallow provider blocker aliases directly on that action: `current_secret_reference_target=SET_OPENAI_SECRET_REF`, `current_secret_reference_target_is_placeholder=true`, `current_secret_reference_resolvable=false`, `secret_reference_probe_error=reference_not_found`, and `provider_live_smoke_readiness_command=python -m runtime.cli.main runtime provider live-smoke-readiness --json`.

2026-05-14 operator-action text check: non-JSON `mvp operator-action-required` now prints the same current secret-reference target, placeholder flag, resolvability, probe error, and provider live-smoke readiness command for the P0 `openai_secret_reference` action. It still does not print secret values or candidate values.

2026-05-14 operator-input validation blocker alias check: `mvp validate-operator-input --input 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json` now carries those same no-secret provider blocker aliases on the blocked `openai_secret_reference` group. The validator still returns `valid=false`, does not echo candidate values, does not read a secret value, and does not write setup metadata or call a provider.

2026-05-14 operator-input validation text check: the non-JSON `mvp validate-operator-input --input 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json` output now prints the same no-secret blocker summary for the blocked `openai_secret_reference` group: target, placeholder flag, resolvability, probe error, and provider live-smoke readiness command. Candidate values are still not echoed.

2026-05-14 credential handoff text check: non-JSON `mvp credential-handoff` now prints the same target, placeholder flag, resolvability, probe error, and provider live-smoke readiness command under P0 `openai_secret_reference`. It remains a no-secret handoff and does not perform provider calls, setup writes, or live probes.

2026-05-14 presence-check handoff check: `mvp credential-handoff --json` now exposes boolean-only PowerShell presence checks for `OPENAI_API_KEY` at user and process scope under `safe_commands`, `required_operator_inputs`, and the P0 `openai_secret_reference` row. The checks output only `True`/`False` and are marked `reference_presence_check_outputs_secret_value=false`.

2026-05-14 Studio presence-check mirror: `studio dashboard --json` now mirrors the same boolean-only `OPENAI_API_KEY` user/process presence checks in `mvp_readiness_panel.key_checks`, and the rendered dashboard HTML shows them under provider readiness without exposing secret values.

2026-05-14 operator-action presence-check mirror: `mvp operator-action-required --json` now exposes the same boolean-only user/process presence checks on the P0 `openai_secret_reference` action, and non-JSON `mvp operator-action-required` prints a `presence_check:` line without exposing secret values.

2026-05-14 current-state presence-check mirror: `mvp current-state --json` now carries the same boolean-only user/process presence checks in the OpenAI next-action queue, and non-JSON `mvp current-state` prints a `presence_check:` line without exposing secret values.

2026-05-14 shallow credential handoff alias check: `mvp credential-handoff --json` now exposes top-level no-secret provider blocker aliases for shallow consumers: `current_secret_reference_target=SET_OPENAI_SECRET_REF`, `current_secret_reference_target_is_placeholder=true`, `current_secret_reference_resolvable=false`, `secret_reference_probe_error=reference_not_found`, and `recommended_reference_name=OPENAI_API_KEY`. The nested `p0_required_now` row remains the detailed handoff record.

2026-05-14 live-smoke readiness alias check: `runtime provider live-smoke-readiness --json` now exposes the same no-secret setup-reference blocker aliases for the active OpenAI target (`current_secret_reference_target=SET_OPENAI_SECRET_REF`, `current_secret_reference_target_is_placeholder=true`, `current_secret_reference_resolvable=false`, `secret_reference_probe_source=env-var-or-local-secret-ref`, `secret_reference_probe_error=reference_not_found`) while preserving `ready_for_live_smoke=false`, `secret_value_read=false`, `live_network_call_attempted=false`, and `files_modified=false`.

The current P0 blocker is not "we need every key." It is narrower:

1. The OpenAI model target is already `gpt-5.5`.
2. The setup state still points at placeholder secret reference `SET_OPENAI_SECRET_REF`.
3. `OPENAI_API_KEY` is the documented environment variable path, but the current Studio provider preview reports it is not present.
4. No credential value should be written into this repo.

So the next operator step is to place the OpenAI key in the local gitignored ChaseOS `.env` file or another approved secret source, set the setup metadata reference to `OPENAI_API_KEY`, and then re-run the no-secret readiness checks.

## Repo-Truth Delta

| Surface | Current Truth | MVP Impact |
|---|---|---|
| `runtime/hermes/model_config.yaml` | primary model is `gpt-5.5`; Claude models remain fallbacks | OpenAI is the desired primary provider lane |
| `runtime/openclaw/model_config.yaml` | primary model is `gpt-5.5`; Claude Haiku remains fallback | OpenClaw also expects OpenAI primary |
| `runtime/setup_state.json` | OpenAI is structurally configured but secret target is `SET_OPENAI_SECRET_REF` | P0 blocker: reference does not resolve |
| `python -m runtime.cli.main setup validate --json` | top-level validation fails; OpenAI row exposes the same shallow blocker aliases and probe reports `reference_not_found` | cannot claim provider readiness |
| `python -m runtime.cli.main setup provider validate openai --json` | provider validation now fails closed on `secret_reference_resolvable=false` and exposes shallow no-secret aliases for target placeholder, resolvability, probe source, and probe error; no secret value is read or displayed | operator sees a hard validation failure until the reference resolves |
| `python -m runtime.cli.main mvp credential-handoff --json` | P0/P1/P2 credential handoff is now machine-readable, separates needed-now OpenAI reference from later/out-of-scope credentials, and mirrors `completion_safety_contract` | operator can see exactly what to provide without expanding MVP credential scope or mistaking checklist coverage for completion |
| `python -m runtime.cli.main mvp readiness-gate --json` | pass 3 now surfaces `secret_reference_resolvable=false`, `secret_reference_probe_error=reference_not_found`, and the provider validation command | MVP gate and setup provider validation agree on the credential blocker |
| `python -m runtime.cli.main studio dashboard --json` | `mvp_readiness_panel.key_checks` now mirrors provider target, placeholder status, resolvability, probe source/error, and the live-smoke readiness command without exposing values | Studio cockpit shows the same operator-facing blocker as the CLI gates |
| `python -m runtime.cli.main studio phase11-chat-live-provider-execution-approval-preview --json` | provider route is blocked; `OPENAI_API_KEY` is absent; provider call was not performed | Chat live provider lane remains blocked |
| `python -m runtime.cli.main runtime provider live-smoke-readiness --json` | blocked by OpenAI credential failure, missing local Ollama fallback, and missing fallback approval request; now exposes the same OpenAI setup-reference blocker aliases without reading a secret or calling a provider | live smoke is not ready |
| `runtime/providers/provider_call_surfaces.json` | separates model execution, Source Intelligence, acquisition connectors, and delivery connectors | prevents one key from implying broad authority |
| `.env.example` | template only; contains fake placeholders | not evidence of configured credentials |

## Required MVP Credentials And References

| Item | Priority | Current State | Needed Now |
|---|---:|---|---|
| `OPENAI_API_KEY` or equivalent local secret ref | P0 | missing/unresolved; setup target still `SET_OPENAI_SECRET_REF` | required for provider-backed Chat/Studio response lane |
| OpenAI model target | P0 | `gpt-5.5` in Hermes/OpenClaw setup/config paths | keep as target unless operator changes provider strategy |
| RPGL live probe approval chain | P0 | existing OpenAI approval/result exists but failed on missing credential | rerun only after secret reference resolves |
| `ANTHROPIC_API_KEY` | P1 | Claude setup not configured | only needed if Claude becomes selected primary/fallback execution path |
| `OLLAMA_HOST` plus local model target | P1 | local OSS setup not configured; target profile lists disabled `phi4-mini:latest` fallback | useful recovery fallback, not enough for strong development tasks |
| `DISCORD_WEBHOOK_URL` / `STRIKEZONE_DISCORD_WEBHOOK_URL` | P1 | Discord binding is configured in setup; templates exist | output routing only, not model execution |
| `PERPLEXITY_API_KEY` | P1/P2 | template/reference only | needed only for live research capture connector |
| `XAI_API_KEY` | P2 | call-surface reference only | optional Grok/xAI capture connector |
| `N8N_BASE_URL`, `N8N_API_KEY`, `N8N_MCP_ACCESS_TOKEN` | P2 | n8n not configured; shadow/draft paths only | not needed for first MVP loop |
| `WHOP_API_KEY`, CRM/payment keys | P2 | delivery/proof-only surfaces; no real-client completion | defer until VentureOps has real client scope and approval evidence |
| wallet, exchange, seed phrases, host admin credentials | out of scope | no MVP requirement | do not add |

## Operator Setup Boundary

Do:

- Store real API keys in the gitignored ChaseOS root `.env`, Windows user environment variables, local secret-manager entries, or another governed secret store.
- Align `runtime/setup_state.json` metadata to a resolvable reference such as `OPENAI_API_KEY` only through a governed config pass if the operator approves that metadata change.
- Re-run setup and provider readiness commands after the local `.env` entry or other reference exists.

Do not:

- Paste API keys into chat, markdown, logs, tests, examples, `.env.example`, or `runtime/setup_state.json`.
- Treat `.env.example` placeholders as real configuration.
- Activate n8n, payment, CRM, wallet, exchange, or full system-control credentials as part of P0.
- Claim provider execution is verified until a gated live probe succeeds.

## Metadata Preview And Update Commands

For the compact machine-readable credential handoff, run:

```powershell
python -m runtime.cli.main mvp credential-handoff --json
```

Current live output reports P0 `openai_secret_reference`, target `SET_OPENAI_SECRET_REF`, `current_secret_reference_resolvable=false`, P1 optional/later provider/output references, P2/out-of-scope connector/payment/system credentials, top-level completion aliases, `completion_safety_contract`, `required_operator_inputs`, and authority flags showing no secret values, provider call, setup write, approval action, Agent Bus write, browser/host control, or canonical mutation.

After the operator sets `OPENAI_API_KEY` in the local `.env` file or another approved secret source, first preview the setup metadata update, then run the live metadata write only after the preview is acceptable:

```powershell
python -m runtime.cli.main setup set provider openai secret_reference_kind=env-var-or-local-secret-ref secret_reference_present=true secret_reference_target=OPENAI_API_KEY --dry-run --json
python -m runtime.cli.main setup set provider openai secret_reference_kind=env-var-or-local-secret-ref secret_reference_present=true secret_reference_target=OPENAI_API_KEY --json
```

The `--dry-run` command is read-only and must report `writes_setup_state=false`. The second command writes non-secret setup metadata to `runtime/setup_state.json`. Neither command may contain the actual API key.

## Machine-Readable Operator Handoff Steps

The current MVP gate and operator unblock packet expose the OpenAI blocker as four ordered steps:

| Step | Actor | Meaning |
|---:|---|---|
| 1 | operator | `set_outside_repo_secret_reference`: create or confirm the local gitignored secret reference, normally `OPENAI_API_KEY` in the ChaseOS root `.env` file; do not paste the key value into tracked repo files/chat/logs |
| 2 | operator or Codex | `preview_setup_metadata_reference`: run the `setup set --dry-run --json` preview and require `writes_setup_state=false` |
| 3 | operator or Codex after explicit confirmation | `update_setup_metadata_reference`: run the metadata-only setup command that points ChaseOS at the reference name |
| 4 | operator or Codex | `validate_reference_without_secret_read`: run provider validation and require `secret_reference_resolvable=true` |
| 5 | operator | `request_guarded_live_probe_approval`: only after validation passes, review a separate live-probe approval plan |

This split matters because the metadata command is not the first action. The first action is the local gitignored secret reference, whose value Codex must not see.

## Validation Commands

Current no-secret checks:

```powershell
python -m runtime.cli.main mvp credential-handoff --json
python -m runtime.cli.main setup provider validate openai --json
python -m runtime.cli.main runtime provider target-profile --json
python -m runtime.cli.main runtime provider config-report --json
python -m runtime.cli.main runtime provider live-smoke-readiness --json
python -m runtime.cli.main studio phase11-chat-live-provider-execution-approval-preview --json
```

Current expected result while `SET_OPENAI_SECRET_REF` is still active:

- `python -m runtime.cli.main setup provider validate openai --json` exits nonzero.
- JSON envelope reports `ok=false`.
- Result reports `valid=false`.
- Missing check includes `secret_reference_resolvable`.
- Top-level aliases report `secret_reference_target_is_placeholder=true`, `secret_reference_resolvable=false`, `secret_reference_probe_source=env-var-or-local-secret-ref`, and `secret_reference_probe_error=reference_not_found`.
- Probe reports `exists=false`, `error=reference_not_found`.
- `mvp readiness-gate` and Studio `mvp_readiness_panel` also report `secret_reference_resolvable=false`.
- No secret value is read or displayed.

Latest 2026-05-15 recheck preserves this expected blocked result until the operator fills the gitignored `.env` entry. Do not run the live-probe path until the operator has created or confirmed the local secret reference and validation passes.

After the operator sets the local OpenAI reference:

```powershell
python -m runtime.cli.main setup provider validate openai --json
python -m runtime.cli.main runtime provider live-probe-target-approval-plan primary --json
python -m runtime.cli.main studio phase11-chat-live-provider-execution-approval-preview --json
```

Only after explicit approval:

```powershell
python -m runtime.cli.main runtime provider live-probe-executor primary --gate-approval-id <id> --execute-live-probe --json
```

## Known Command Side Effect

`python -m runtime.cli.main runtime provider probe primary --json` is not a live provider call, but in config mode it writes provider-state/audit evidence. This pass ran it once while auditing readiness. Treat that result as provider-state telemetry, not as proof of a real provider response.

## MVP Workflow Effect

The useful near-term MVP does not require every feature family to be wired to credentials. It requires this loop:

`operator request -> approval -> Agent Bus task -> runtime result -> evidence -> daily closeout`

Provider credentials become P0 only when the request needs live model execution through Chat/Studio. VentureOps is now complete for one scoped local MVP workflow proof, but revenue proof, CRM/payment, external delivery, provider/browser execution, and broader client-scope work remain separate gated lanes.

## Current Status

Status: `CHECKLIST COMPLETE / VALIDATION FAILS CLOSED / PROVIDER EXECUTION BLOCKED / OPERATOR SECRET REFERENCE REQUIRED`

Next recommended pass: `operator-provide-openai-secret-reference`, followed by `provider-live-probe-after-secret-reference`.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
