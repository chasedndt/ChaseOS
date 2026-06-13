---
title: ChaseOS Phase 11 Architecture — Conversational Command Center
type: architecture
status: FOUNDATION PLUS GOVERNED MANUAL-TEST EXECUTION CONTROLS COMPLETE - provider/chat router contracts, native Chat panel, native chat workspace/thread foundation, approval handoff queue contract, post-closeout planning, conversation persistence approval preview, Chat proposal approval-queue write proof, live-provider approval preview, live-provider execution executor, runtime/browser dispatch readiness, approval-consumption readiness, companion status UI, companion-selection approval preview, companion-selection queue-write readiness, companion-selection queue-write execution proof, companion-selection approval-consumption readiness, companion-selection approval-consumption executor, runtime-dispatch executor, authority execution controls, companion memory boundary contract, companion memory approval preview, companion memory approved execution proof, companion memory readback/search preview, companion memory ledger-write approval preview, companion memory approved ledger-write execution, companion memory ledger read model, companion memory real-ledger activation closeout, read-only slash command responses, native read-only slash response UI, read-only card visual QA, no-HITL feature-family selection audit, read-only slash command catalog audit, read-only operator dashboard aggregate audit, no-HITL lane completion audit, operator-governed executor/deferred closeout handoff, and operator-action-required no-autonomous-pass gate verified; live runtime completion remains manual-test pending
version: 1.0
created: 2026-05-06
updated: 2026-05-16
phase: Phase 11 — ChaseOS Conversational Command Center
knowledge_class: system-operational
owner: Chaser Agent (primary Phase 10/11 engineering runtime)
related_docs:
  - 06_AGENTS/Phase10-Desktop-Shell-Engineering-Plan.md
  - 06_AGENTS/ChaseOS-Studio-Architecture.md
  - 06_AGENTS/ChaseOS-Studio-Phase10-Implementation-Tracker.md
  - 06_AGENTS/Agent-Control-Plane.md
  - 06_AGENTS/Permission-Matrix.md
  - 06_AGENTS/Trust-Tiers.md
  - 06_AGENTS/Agent-Registry.md
  - 06_AGENTS/Autonomous-Operator-Runtime.md
  - 06_AGENTS/Scheduled-Briefing-Pipelines.md
  - 06_AGENTS/Agent-Memory-Architecture.md
  - 06_AGENTS/Feature-Fit-Register.md
  - 06_AGENTS/ChaseOS-Approval-Center.md
  - runtime/studio/shell/ (Phase 10 shell — the UI host for Phase 11)
---

# ChaseOS Phase 11 — Conversational Command Center

> **Handover notice for all runtimes (Chaser Agent, Hermes, OpenClaw, and future):**
> This is the canonical planning document for Phase 11 and the handover guide for completing Phase 10.
> Read this file before starting any new Phase 10 or Phase 11 pass.
> If you have suggestions or find a contradiction with current repo truth, update this document
> rather than working around it in code. The document is the source of coordination across runtimes.

---

## 0. How to Use This Document

This document has three layers:

1. **Phase 10 Completion Handover** (Section 1) — the remaining Phase 10 passes, ordered by
   priority, with exact scope boundaries. Read this before starting any Phase 10 work.

2. **Phase 11 Architecture** (Sections 2–10) — the full architecture for Phase 11, the
   Conversational Command Center. Read this before proposing any Phase 11 implementation.

3. **Cross-runtime rules** (Section 11) — governance rules that apply to all runtimes during
   both Phase 10 completion and Phase 11 implementation.

Do not implement Phase 11 features during Phase 10 passes. Keep pass boundaries clean.

**2026-05-11 closure note:** Phase 11 readiness surfaces do not close Studio MVP by themselves. Phase 10 native packaged visual QA, product hardening, installer planning, release-readiness governance, and installer-build approval preview/review readiness are now verified, but the remaining MVP blockers are explicit installer approval artifact write/consumption/execution, broader approval execution/target mutation, real provider/model calls, actual runtime/browser dispatch, companion-selection target writes, real target workspace upgrade/migration, and governed installer/signing/startup/release/host mutation tracked in `06_AGENTS/ChaseOS-Studio-Phase10-Implementation-Tracker.md`.

**2026-05-12 companion-selection note:** Companion-selection queue-write execution proof, approval-consumption readiness, and the governed approval-consumption executor are now verified. The executor consumed a selected companion approval, wrote the exact-once marker, wrote `runtime/studio/chat/companion-selection.json`, and blocked duplicate execution before target rewrite. It did not grant ambient Chat execution, provider/model calls, runtime/browser dispatch, Agent Bus writes, identity/profile/role-card mutation, broad approval execution, or canonical writeback.

**2026-05-12 read-only slash response UI note:** Read-only slash command responses and their native Chat rendering are now implemented/static-QA verified. They expose bounded response cards and explicit blocked-authority posture only; command execution, provider/model calls, runtime/browser dispatch, approval actions, vault writes, Agent Bus task writes, and canonical mutation remain blocked. The follow-on `phase11-chat-readonly-card-visual-qa` pass is now complete.

**2026-05-12 read-only card visual QA note:** Read-only slash response card visual QA is now complete with static HTML evidence, CLI/QA runner coverage, and a governed loopback screenshot proof. It remains visual evidence only: no slash command execution, approval action/consumption, provider/model call, runtime/browser dispatch from Chat, vault write, Agent Bus task write, or canonical mutation was added. The follow-on no-HITL feature-family selection audit is now complete.

**2026-05-12 no-HITL feature-family selection audit note:** The no-HITL selection audit is now complete/read-only/verified. It selected `phase11-chat-readonly-slash-command-catalog-audit` as the next safe no-human-in-loop pass and explicitly deferred companion-selection approval consumption executors, live provider/model calls, runtime/browser dispatch executors, target mutation, Agent Bus task writes, and canonical mutation.

**2026-05-12 read-only slash command catalog audit note:** The read-only slash command catalog audit is now complete/read-only/verified. It covers supported response cards for `/dashboard`, `/map`, `/vault`, `/runtime status`, `/models`, `/provider`, `/log`, `/memory show`, and `/pet`, blocks `/approve`, `/reject`, `/run`, `/browser`, `/memory save`, `/rnd`, `/new-project`, and unknown slash commands, and was followed by the now-complete `phase11-chat-readonly-operator-dashboard-aggregate-audit`. The pass corrected the router map for `/vault` and `/log` to match the documented read-only help surface. It added no command execution, approval write/consumption/execution, provider/model call, runtime/browser dispatch, target mutation, Agent Bus task write, or canonical mutation.

**2026-05-12 read-only operator dashboard aggregate audit note:** The read-only operator dashboard aggregate audit is now complete/read-only/verified. It proves `/dashboard` source coverage across approval center, provider readiness, runtime status, companion status, recent build logs, and slash catalog surfaces, and was followed by the now-complete no-HITL lane completion audit. It added no command execution, approval write/consumption/execution, provider/model call, runtime/browser dispatch, target mutation, Agent Bus task write, or canonical mutation.

**2026-05-12 no-HITL lane completion audit note:** The no-HITL lane completion audit is now complete/read-only/verified. It verified six completed no-HITL/read-only artifacts, build/history/daily/activity linkage, and zero remaining eligible no-human-in-loop Phase 11 candidates. The current marker is `operator-selected-governed-executor-or-deferred-closeout`; companion-selection approval consumption and the first approved runtime-dispatch Agent Bus enqueue are now closed by governed executors, while live provider/model calls, browser dispatch, Agent Bus task claim/result handling, broader target mutation, and canonical writeback remain operator-governed or deferred.

**2026-05-12 operator-governed executor/deferred closeout handoff note:** The operator-governed closeout handoff is now complete/read-only/verified. It verifies zero substantial autonomous Phase 11 development passes remain; after the companion-selection consumption executor and runtime-dispatch enqueue executor, four remaining lanes stay operator-governed/deferred. It records `implementation_authority_granted=false` and advances the marker to `operator-action-required-no-autonomous-phase11-pass`. It added no command execution, approval artifact write/consumption/execution, exact-once marker write, provider/model call, runtime/browser dispatch, Agent Bus task write, target mutation, or canonical mutation.

**2026-05-12 operator-action-required no-autonomous-pass gate note:** The operator action gate is now complete/read-only/verified. It records that zero autonomous Phase 11 passes remain, exposes two unselected decisions (`select_governed_executor_lane` and `defer_phase11_closeout`), and after the companion-selection consumption executor plus runtime-dispatch enqueue executor keeps four remaining lanes operator-governed. It advances the next action to `operator-select-governed-executor-lane-or-defer-closeout`. It added no lane selection, deferral selection, command execution, approval artifact write/consumption/execution, exact-once marker write, provider/model call, runtime/browser dispatch, Agent Bus task write, target mutation, or canonical mutation.
**2026-05-13 companion memory boundary note:** The operator confirmed separate companion memory. `runtime/companion/memory.py` and `runtime/studio/phase11_companion_memory_boundary_contract.py` now define governed separate namespaces for Hermes/OpenClaw/Chaser Agent, candidate validation, Chat panel display, StudioAPI/CLI/QA wiring, and no-write proof. This does not create memory files or grant memory write authority; future writes require `phase11-companion-memory-approval-preview` and then a separate exact-once executor proof.
**2026-05-13 companion memory approval preview note:** `runtime/studio/phase11_companion_memory_approval_preview.py` now turns valid companion-memory candidates into deterministic approval-packet previews and supports explicit digest-gated pending approval queue writes. Live proof wrote approval `448282cc-4d3c-4853-a114-8246657dbe5a` and audit evidence for Hermes preference memory, blocked duplicate approval creation before writing, and blocked credential-class memory candidates. It still writes no companion memory ledger and consumes no approval; this was followed by the now-complete `phase11-companion-memory-approved-execution-proof`.
**2026-05-13 companion memory approved execution proof note:** `runtime/studio/phase11_companion_memory_approved_execution_proof.py` now consumes a digest-bound companion-memory approval exactly once and writes proof-only evidence. Live proof consumed approval `448282cc-4d3c-4853-a114-8246657dbe5a`, matched digest `3c49a24ad2f9275d327fc6923c0873ae3e42dfb9b97d3a194c163f07e0364250`, reserved the exact-once marker before proof outputs, wrote proof artifacts and execution evidence, and blocked duplicate execution before writes. It still does not create `07_LOGS/Companion-Memory/`, append a memory ledger, call providers/models, dispatch runtimes/browsers, write Agent Bus tasks, mutate Gate/Git/workflow/host state, or mutate canonical state. It was followed by the now-complete `phase11-companion-memory-readback-search-preview`.
**2026-05-13 companion memory readback/search preview note:** `runtime/studio/phase11_companion_memory_readback_search_preview.py` now indexes companion-memory approval/proof evidence without touching the real companion-memory ledger. Live proof search found approval `448282cc-4d3c-4853-a114-8246657dbe5a`, its exact-once marker, proof-temp outputs, and execution evidence as `proof_written`; filters cover companion id, memory class, query, status, and limit. The pass still does not create or read `07_LOGS/Companion-Memory/`, append a memory ledger, write/consume approvals, call providers/models, dispatch runtimes/browsers, write Agent Bus tasks, mutate Gate/Git/workflow/host state, or mutate canonical state. It was followed by the now-complete `phase11-companion-memory-ledger-write-approval-preview`.
**2026-05-14 companion memory ledger-write approval preview note:** `runtime/studio/phase11_companion_memory_ledger_write_approval_preview.py` now turns a proof-written companion-memory approval into a deterministic future ledger-entry preview and digest-bound ledger-write approval packet. Live preview selected source approval `448282cc-4d3c-4853-a114-8246657dbe5a`, computed ledger-write approval digest `f415f33f24d87227388e399ad5d056943120a2f614903e33c446c52e4b7650e2`, and confirmed the real `07_LOGS/Companion-Memory/` root remains absent. The surface may queue one pending ledger-write approval only when the exact digest is supplied; temp-vault QA proves duplicate, mismatch, missing-proof, and ambient `StudioService.execute_approved` blocks. It still does not append a real memory ledger, create/read the memory root, consume/execute ledger-write approvals, call providers/models, dispatch runtimes/browsers, write Agent Bus tasks, mutate Gate/Git/workflow/host state, or mutate canonical state. It was followed by the now-static-QA-verified `phase11-companion-memory-approved-ledger-write-execution-proof`.
**2026-05-14 companion memory approved ledger-write execution proof note:** `runtime/studio/phase11_companion_memory_approved_ledger_write_execution_proof.py` now consumes a digest-bound ledger-write approval exactly once and appends one companion-memory JSONL entry only through the explicit executor. Temp-vault static QA proved marker reservation before append, one ledger entry written, execution/rollback/evidence outputs written, duplicate execution blocked before a second append, generic Studio execution blocked, and real-vault Markdown/approval/companion-memory snapshots unchanged. This was followed by the real-vault activation closeout: approval `3243d5f9-7f34-47b4-a4cd-7c67f7b78541` was explicitly written and consumed once to append one raw/non-canonical Hermes ledger entry. This pass adds no provider/model call, runtime/browser dispatch, Agent Bus task write, Gate/Git/workflow/host mutation, or canonical mutation.
**2026-05-14 companion memory ledger read model preview note:** `runtime/studio/phase11_companion_memory_ledger_read_model_preview.py` now exposes a read-only Studio/Chat/CLI model over companion-memory JSONL ledgers and proof-only evidence. It reads `07_LOGS/Companion-Memory/*/memory-ledger.jsonl` only when present, tolerates malformed optional JSONL lines, filters by companion, memory class, query, and limit, and uses proof backfill when the real ledger is absent. Initial live real-vault verification returned proof-only evidence while `07_LOGS/Companion-Memory/` was absent; the later real-ledger activation closeout superseded that state, and the read model now returns the real Hermes ledger entry. It adds no provider/model call, runtime/browser dispatch, Agent Bus task write, Gate/Git/workflow/host mutation, or canonical mutation.
**2026-05-14 companion memory real-ledger activation closeout note:** `runtime/studio/phase11_companion_memory_real_ledger_activation_closeout.py` verifies the executed real ledger-write chain end to end. Live closeout confirmed approval `3243d5f9-7f34-47b4-a4cd-7c67f7b78541` is executed, marker `runtime/studio/approvals/_companion_memory_ledger_write_markers/3243d5f9-7f34-47b4-a4cd-7c67f7b78541.json` was reserved before append, evidence exists under `07_LOGS/Studio-Graph-Views/cml-ledger-write-proof/`, `07_LOGS/Companion-Memory/hermes/memory-ledger.jsonl` contains one raw/non-canonical entry, duplicate execution blocks before append, and the read model returns the real ledger entry. It adds no provider/model call, runtime/browser dispatch, Agent Bus task write, Gate/Git/workflow/host mutation, broad memory authority, or canonical mutation. The next companion-memory lane is `phase11-companion-memory-context-readiness-preview`.
**2026-05-12 runtime-dispatch executor note:** The governed runtime-dispatch executor is now complete/approval-consumed/verified for the first bounded Agent Bus enqueue path. It consumed approval `60a3153a-00e4-4258-af43-9df89d515705`, wrote task `chat-runtime-dispatch-ec40d576ce3940c3b3d2` for `Codex`, wrote the exact-once marker and audit evidence, and blocks duplicate execution before a second task write. It does not claim tasks, start runtimes, dispatch workflows, call providers/models, control browsers, mutate target vault files, mutate Gate/Git/host state, or write canonical state. Four substantial lanes remain: live provider/model execution, browser dispatch executor, approval target mutation executor, and Agent Bus task claim/result/canonical writeback.

**2026-05-16 Studio Chat authority execution controls note:** `runtime/studio/phase11_chat_live_provider_execution_executor.py` and `runtime/studio/phase11_chat_authority_execution_controls.py` now provide the governed manual-test execution lane for provider response plus runtime handoffs. The Chat page can prepare exact digests and run an operator-statement-gated stack for OpenAI provider execution through `OPENAI_API_KEY` env reference, Hermes/main-runtime Agent Bus dispatch, Discord-control handoff to OpenClaw, cron/schedule-control handoff to OpenClaw, and Agent Bus readback. The provider executor is built, but secrets are never displayed or returned. Studio still does not call Discord directly, mutate external cron, claim runtime tasks, execute workflows, persist a conversation transcript, or mutate canonical state. Manual UI testing with live Hermes/OpenClaw/provider env remains pending.

**2026-05-15 native chat workspaces foundation note:** `runtime/studio/phase11_chat_workspaces_foundation.py` now models ChaseOS-native Chat projects, folders, tabs, threads, runtime lanes, and proposal actions for Hermes, OpenClaw, Codex, and future runtimes. The native Chat panel renders this foundation as `ChaseOS Chat` and embeds runtime/project/thread cards plus next-action cards for thread creation, board handoff, cron/schedule management, and chat-driven runtime setup. This is a read-only/product-shape foundation only: it does not persist conversations, create threads, send messages, call Discord APIs/webhooks, write Agent Bus tasks, mutate runtime boards, mutate schedules, consume approvals, call providers, expose credential values, or write canonical state.

**2026-05-15 native chat workspace proposal-writer note:** `runtime/studio/phase11_chat_workspace_proposal_writer.py` now prepares digest-bound approval queue artifacts for Studio Chat workspace, folder, and runtime-thread requests. The Chat panel, StudioAPI, and panel registry expose the preview/write contract and require an exact proposal digest before any pending approval artifact is queued. Generic `StudioService.execute_approved()` blocks these artifacts; only the governed workspace proposal consumption executor can consume them. No Chat workspace/folder/thread, Discord thread, message send, Agent Bus task, runtime board item, schedule change, provider/model call, credential exposure, or canonical mutation was added by the writer.

**2026-05-15 native chat workspace proposal-consumption note:** `runtime/studio/phase11_chat_workspace_proposal_consumption_executor.py` now consumes one digest-bound Studio Chat workspace proposal approval exactly once and writes one native proposal JSON record under `runtime/studio/chat/workspace-proposals/`. The executor requires approval id plus exact proposal digest, can record a current-session operator approval statement, reserves an exact-once marker before the target write, mutates only the matching approval status/execution fields, and writes audit evidence. It still does not create Chat workspaces, folders, threads, messages, Discord threads, Agent Bus tasks, runtime board items, schedules, provider/model calls, credential exposure, or canonical mutation. The next pass is a separate target-state executor if the operator wants approved proposals to become real native Chat state or transport actions.

**2026-05-15 native chat workspace target-state note:** `runtime/studio/phase11_chat_workspace_target_state_executor.py` and `runtime/studio/phase11_chat_native_state.py` now apply an approved proposal JSON record into native Studio Chat state under `runtime/studio/chat/native-state/`. The executor requires proposal path/id, exact proposal digest, and an operator target-state statement; it reserves an exact-once marker, writes workspace/folder/thread state records according to proposal kind, mutates the proposal status to `target_state_applied`, and writes audit evidence. The Chat foundation reads these native-state records back into the Studio Chat project/folder/thread model. This is native Studio state only: no Discord API/webhook call, Discord thread creation, message send, Agent Bus task write, runtime board mutation, schedule mutation, provider/model call, credential exposure, or canonical mutation was added.

**2026-05-15 native chat route-state and draft note:** `runtime/studio/phase11_chat_route_state_and_message_drafts.py` now persists local Studio Chat route selection and message draft/intent state under `runtime/studio/chat/native-state/route-state/` and `runtime/studio/chat/native-state/drafts/`. StudioAPI exposes read/save methods, the Chat panel renders route/draft posture, and the native Chat foundation reads selected-thread and draft counts back into thread cards. This is local UI state only: it does not send messages, persist transcripts/conversation logs, call Discord APIs/webhooks, create Discord threads, write Agent Bus tasks, mutate runtime boards, dispatch runtimes, mutate schedules, call providers/models, read credential values, or mutate canonical state.

**2026-05-15 native chat runtime-board handoff proposal note:** `runtime/studio/phase11_chat_runtime_board_handoff_proposal.py` now packages the selected Studio Chat thread or saved draft into a digest-bound approval request for a future Hermes/OpenClaw/Codex runtime board item. StudioAPI exposes read/request methods, the Chat panel renders board target/lane/digest posture, and `StudioService.execute_approved()` blocks ambient execution of these artifacts. This is approval-queue request state only: it does not write a runtime board item, create an Agent Bus task, dispatch a runtime/workflow, send a chat message, persist a conversation log, call Discord APIs/webhooks, mutate schedules, call providers/models, read credential values, or mutate canonical state.

**2026-05-15 native chat schedule proposal packet note:** `runtime/studio/phase11_chat_schedule_proposal_packet.py` now packages the selected Studio Chat schedule request or saved draft into a digest-bound approval request for a future `runtime/schedules/*.yaml` intent. StudioAPI exposes read/request methods, the Chat panel renders schedule id/workflow/command/cron/runtime-adapter/digest posture, and `StudioService.execute_approved()` blocks ambient execution of these artifacts. This is approval-queue request state only: it does not write schedule intent YAML, regenerate `runtime/schedules/index.yaml`, enable schedules, change OpenClaw/Hermes cron, create Agent Bus tasks, dispatch runtimes/workflows, send chat/Discord messages, call providers/models, read credential values, or mutate canonical state.

**2026-05-16 native chat schedule proposal-consumption note:** `runtime/studio/phase11_chat_schedule_proposal_consumption_executor.py` now consumes one digest-bound Studio Chat schedule proposal approval exactly once and writes one staged approved proposal JSON record under `runtime/studio/chat/schedule-proposals/`. The executor requires approval id plus exact schedule digest, can record a current-session operator approval statement for a pending request, validates the approved schedule YAML with the schedule loader, reserves an exact-once marker, mutates only the matching approval status/execution fields, and writes audit evidence. It still does not write `runtime/schedules/*.yaml`, regenerate `runtime/schedules/index.yaml`, enable schedules, change OpenClaw/Hermes cron, create Agent Bus tasks, dispatch runtimes/workflows, call Discord/providers, read credential values, or mutate canonical state. The next required pass is a separate approved schedule-intent writer if the operator wants staged proposals to become canonical schedule intent state.

**2026-05-16 native chat approved schedule-intent writer note:** `runtime/studio/phase11_chat_approved_schedule_intent_writer.py` now consumes one staged approved Studio Chat schedule proposal exactly once and writes the declared `runtime/schedules/*.yaml` schedule intent plus regenerated `runtime/schedules/index.yaml`. The executor requires staged proposal path or schedule id, exact schedule digest, and an operator schedule-write statement; validates the schedule against the workflow registry before writing; reserves an exact-once marker; updates the staged proposal record to `schedule_intent_written`; and writes audit evidence. It still does not enable schedules, change OpenClaw/Hermes cron, mutate an external scheduler, create Agent Bus tasks, dispatch runtimes/workflows, call Discord/providers, read credential values, send messages, or write broader canonical state. The next pass is schedule activation/readiness: deciding how approved disabled schedule intents become enabled and exported to runtime adapters.

**2026-05-16 native chat schedule activation-readiness note:** `runtime/studio/phase11_chat_schedule_intent_activation_readiness.py` now inspects an existing disabled ChaseOS schedule intent and prepares a digest-bound activation approval packet for a future enable/export executor. The surface validates the current schedule, previews the future `enabled: true` YAML, checks current enabled duplicate risks for the target runtime adapter, previews current adapter export state, and can queue a pending activation approval only when the exact activation digest is supplied. `StudioService.execute_approved()` explicitly blocks ambient execution of these activation packets. This pass still does not enable schedules, regenerate the schedule index, change OpenClaw/Hermes cron, mutate an external scheduler, create Agent Bus tasks, dispatch runtimes/workflows, call Discord/providers, read credential values, send messages, or perform canonical activation.

**2026-05-16 native chat approved schedule-activation executor note:** `runtime/studio/phase11_chat_approved_schedule_activation_executor.py` now consumes one approved digest-bound schedule activation packet exactly once. The executor requires approval id, exact activation digest, and an operator activation statement; verifies the current disabled schedule YAML hash; validates the future enabled YAML with the schedule loader; reserves an exact-once marker; enables the matching ChaseOS schedule through the native schedule loader; regenerates `runtime/schedules/index.yaml`; refreshes the adapter export read model; updates the matching approval record; and writes audit evidence. It still does not mutate OpenClaw/Hermes cron state, write external scheduler files, create Agent Bus tasks, dispatch runtimes/workflows, call Discord/providers, read credential values, send messages, or perform broader canonical writeback. The next required pass is adapter export/readiness, not live external cron mutation.

**2026-05-16 native chat schedule adapter export-readiness note:** `runtime/studio/phase11_chat_schedule_adapter_export_readiness.py` now inspects enabled ChaseOS schedules for one registered runtime adapter and prepares a digest-bound local adapter export packet approval. The surface validates the adapter/schedule filter, reads `export_schedules_for_adapter(..., enabled_only=True)`, hashes schedule files plus `runtime/schedules/index.yaml`, previews the future local packet content, and can queue a pending approval only when the exact export digest is supplied. `StudioService.execute_approved()` explicitly blocks ambient execution of these adapter export approvals. This still does not write the local export packet, mutate external scheduler files, change OpenClaw/Hermes cron, create Agent Bus tasks, dispatch runtimes/workflows, call Discord/providers, read credential values, send messages, or perform broader canonical writeback.

**2026-05-16 native chat approved adapter export packet writer note:** `runtime/studio/phase11_chat_approved_schedule_adapter_export_packet_writer.py` now consumes one approved digest-bound adapter export approval exactly once and writes the local adapter export JSON packet under `runtime/studio/chat/schedule-adapter-exports/`. The writer requires approval id, exact export digest, and an operator export-write statement; rechecks current adapter export digest material against schedule/index hashes; reserves an exact-once marker before the target write; updates only the matching approval record; and writes audit evidence. It still does not mutate external scheduler files, change OpenClaw/Hermes cron, create Agent Bus tasks, dispatch runtimes/workflows, call Discord/providers, read credential values, send messages, or perform broader canonical writeback.

**2026-05-16 native chat schedule UI action controls/readback note:** `runtime/studio/phase11_chat_schedule_ui_action_controls_and_readback.py` now exposes the native Chat manual-test contract for the full local schedule chain. The Chat page renders fields and buttons for proposal preview/queue, approved proposal consumption, approved schedule-intent write, activation preview/queue/execution, adapter export preview/queue, and local export packet write, plus readback over schedules, approvals, staged proposals, and local export packets. This is UI/action-control/readback only over already-governed Studio API methods: it adds no external scheduler mutation, OpenClaw/Hermes cron mutation, Agent Bus task write, runtime/workflow dispatch, Discord/provider call, credential read, message send, or broader canonical writeback.

**2026-05-16 Studio Chat P0 runtime completion note:** Six runtime-side surfaces are now implemented and test-verified (53 pass): `phase11_chat_conversation_log_writer.py` (governed Markdown writer to `07_LOGS/Conversations/`, exact-once marker, secret redaction, all lane fields, dry-run default); `phase11_chat_runtime_result_display.py` (read-only Agent Bus poller for Hermes/OpenClaw tasks, severity-sorted result cards, no task claim); `phase11_chat_manual_ui_verification_harness.py` (loopback HTTP harness at `127.0.0.1:8772` — Prepare All → Run Approved Test → Save Log); `phase11_chat_discord_control_handler.py` (Discord control via `.chaseos/discord_instance_bindings.yaml` channel IDs + env credential refs, dry-run default, post_message/post_audit/dry_run_ping); `phase11_chat_schedule_apply_handler.py` (schedule apply via native schedule loader, dry-run default, enable_schedule/validate_only actions, `external_cron_mutated: false` always); `phase11_credential_setup_ux.py` (6 credentials — OpenAI/Anthropic/OpenClaw Discord/Hermes Discord/Perplexity/xAI Grok — presence check only, never value, `.env.example` template). Live provider/Discord/Hermes lanes are CONFIGURED BUT UNVERIFIED — credentials and daemons not in test env. Manual verification via harness at `http://127.0.0.1:8772/` is the next step once `OPENAI_API_KEY` is set and Hermes/OpenClaw daemons are running.

**2026-05-16 Studio Chat schedule manual test closeout note:** `runtime/studio/phase11_chat_schedule_manual_test_app.py` now provides a loopback-only browser harness for manually testing the same schedule-control chain outside the pywebview shell. The harness serves `/`, `/health.json`, `/api/readback`, and `/api/action` on `127.0.0.1`, calls the existing `StudioAPI` methods, blocks secret-like input strings, and exposes no credential fields. Bounded smoke and browser-open readiness are verified for manual testing; external scheduler mutation, OpenClaw/Hermes cron mutation, Agent Bus task writes, runtime/workflow dispatch, Discord/provider calls, credential reads, message sending, and broad canonical mutation remain blocked.

**2026-05-17 Studio Chat runtime routing refactor note:** Chat primary path refactored from direct-OpenAI to Agent Bus → Hermes (WSL). `OPENAI_API_KEY` is no longer required for the primary Chat path — Hermes owns `ANTHROPIC_API_KEY` in its WSL env. New: `phase11_chat_send_message.py` (Studio→Bus dispatch, `_SENDER="Codex"`), `phase11_chat_hermes_wsl_config.py` (WSL connection status + startup guide), `chat` task type in `task_type_table.yaml`, `_dispatch_chat` + `_call_anthropic_chat` in `hermes_watch.py` (fail-open LLM synthesis). Credential registry now exposes `routing_path` per credential and a `routing_model` section distinguishing `runtime_dispatch` primary from `direct_provider` fallback. 38 new routing tests; 118 P0+E2E+routing pass. Operator action to activate live path: set `ANTHROPIC_API_KEY` in WSL `~/.bashrc` + start `hermes_watch`.

**2026-05-17 Studio Chat P1 E2E fake runtime harness note:** `runtime/studio/phase11_chat_e2e_fake_runtime_harness.py` now proves the full Chat flow (task injection → result display → conversation log) in CI without live credentials, network, Discord, or external cron. The harness guards against real-vault execution (`is_test_vault=True` required), injects three synthetic completed Agent Bus tasks (Hermes planning, OpenClaw discord-control, OpenClaw schedule-control), polls `build_chat_runtime_result_display`, and calls `write_conversation_log` — all from a temp vault. `test_phase11_e2e_full_flow.py` covers 27 tests: guard/dry-run, live 3-task injection, result cards visible/done, log file written, task IDs in log, secret redaction, idempotent second write blocked, authority flags all false, no real OpenAI key pattern in output. Bug fixed in `phase11_chat_runtime_result_display.py`: `intent` field is stored as a string by Agent Bus, not a dict; added `isinstance(intent_raw, dict)` guard. 27 new + 53 P0 regression tests pass. P0 live provider/Discord verification remains pending (operator must set `OPENAI_API_KEY`).

**2026-05-16 Studio Chat authority-tier controls note:** `runtime/studio/phase11_chat_authority_tier_controls.py` now groups the high-authority Chat lanes into one native Chat control/readiness surface: provider calls, credential readiness, runtime dispatch, Agent Bus tasks, Discord actions, and external cron apply. The Chat page renders lane cards with `Open Lane` navigation into the existing governed surfaces and disabled execution buttons. This is a navigation/readiness layer only; it reads no secret values, calls no providers or Discord APIs, writes no Agent Bus tasks, dispatches no runtimes/workflows, mutates no OpenClaw/Hermes cron or external scheduler state, consumes no approvals, and performs no canonical mutation.

---

## 1. Phase 10 Completion Handover

**Current state (2026-05-06):** The ChaseOS Studio native PyWebView shell is live with 15 panels
(graph, dashboard, browser-runtime, workspace-entry, settings, approval-center, runtime-cockpit,
provenance-explorer, memory-ledger, agent-identity, runtime-navigation, project-workspace, intake,
sic, plus panel registry). 417/417 shell tests pass. The exe is built and smoke-tested.

The following passes remain to complete Phase 10. They are ordered by priority and independence.
Each pass follows the same pattern as 10G/10H: new or updated API method + HTML section +
JS render functions + CSS block + test file (30–55 tests target) + build log + archive note +
both indexes updated.

**Read before any pass:**
1. `06_AGENTS/ChaseOS-Studio-Phase10-Implementation-Tracker.md` — canonical pass state
2. `runtime/studio/shell/` — existing shell code
3. The relevant backend module (listed per pass below)

---

### Pass 10J — AOR Execution Monitor Panel

**Priority:** 1 (highest — closes the biggest visibility gap)

**Backend:** `runtime/studio/aor_pipeline_monitor.py`
- `list_recent_executions(vault_root, limit, workflow_filter, status_filter)` — audit records
- `inspect_execution(vault_root, filename)` — single execution detail
- `get_execution_summary(vault_root)` — per-workflow stats (total/success/escalated/failed)

**API methods to add to `api.py`:**
- `get_aor_executions(workflow="", status="", limit=20)` → wraps `list_recent_executions`
- `get_aor_execution_detail(filename)` → wraps `inspect_execution`
- `get_aor_summary()` → already exists; may need enrichment

**Sidebar button:** `[E]` — title "AOR Executions"

**Panel layout:**
- Filter row: workflow dropdown + status dropdown (all/success/escalated/failed) + refresh
- Stats bar: total / success / escalated / failed counts
- Execution list: cards with workflow name, status badge, timestamp, run duration
- Drill-down: click card → detail view showing all stage results (breadcrumb back button pattern same as 10H SIC)

**Governance:** Read-only. No workflow dispatch, no re-run, no audit log mutation.

**Tests target:** 40–50 tests across `TestAPIAORExecutions`, `TestAPIAORExecutionDetail`, `TestAORHTMLStructure`, `TestAORCSS`, `TestAORJS`.

---

### Pass 10K — Schedule Manager Panel

**Priority:** 2

**Backend:** `runtime/studio/schedule_inspector.py`
- `list_schedules(vault_root)` — all schedule intents
- `inspect_schedule(vault_root, schedule_id)` — single schedule detail
- `get_schedule_summary(vault_root)` — enabled/disabled/total counts + state log

**API methods to add:**
- `get_schedules()` → wraps `list_schedules`
- `get_schedule_detail(schedule_id)` → wraps `inspect_schedule`
- `toggle_schedule(schedule_id, enable: bool)` → routes through approval gate (write surface)
- `get_schedule_summary()` → already exists

**Sidebar button:** `[K]` — title "Schedules"

**Panel layout:**
- Stats row: enabled/disabled/total
- Schedule list: cards showing schedule ID, workflow, cron expr, enabled state, last-run timestamp
- Enable/Disable toggle: routes through `StudioService` → approval queue for destructive state changes
- State log: recent enable/disable events from `07_LOGS/Schedule-State/schedule_state_log.jsonl`

**Governance:** Enable/disable is a write action and must route through approval gate. Read surfaces are read-only.

**Tests target:** 45 tests.

---

### Pass 10L — SiteOps Inspector Panel

**Priority:** 3

**Backend:** `runtime/studio/siteops_inspector.py`
- `get_siteops_summary(vault_root)` — counts and last-run status
- `list_siteops_runs(vault_root, limit)` — recent runs
- `list_siteops_approvals(vault_root)` — pending/completed approvals
- `inspect_siteops_run(vault_root, run_id)` — single run detail

**API methods to add:**
- `get_siteops_summary()` → already exists
- `get_siteops_runs(limit=20)` → wraps `list_siteops_runs`
- `get_siteops_approvals()` → wraps `list_siteops_approvals`
- `get_siteops_run_detail(run_id)` → wraps `inspect_siteops_run`

**Sidebar button:** `[T]` — title "SiteOps"

**Panel layout:**
- Summary row: run count, approval count
- Run list: cards with run ID, workflow, status, timestamp
- Approval list: pending items with approve/reject buttons (routes through approval gate)
- Detail drill-down: click run card → inspection view (same breadcrumb back pattern)

**Governance:** Approval actions route through `StudioService`. Run inspection is read-only.

**Tests target:** 40 tests.

---

### Pass 10M — Acquisition Cockpit Panel

**Priority:** 4

**Backend:** `runtime/studio/sic_workspace_browser.py` (source stat side) +
`runtime/studio/aor_pipeline_monitor.py` (acquisition run side) +
`runtime/acquisition/artifact_store.py` (artifact stats direct read)

**API methods to add:**
- `get_acquisition_summary()` — artifact store stats (total/by-source/recent), last-run metadata
- `get_acquisition_runs(limit=20)` — recent acquisition executions from AOR audit
- `run_acquisition_dry_run()` — triggers `run_all_live_acquisitions(dry_run=True)` through approval gate

**Sidebar button:** `[X]` — title "Acquisition"

**Panel layout:**
- Stats row: total artifacts, by-source breakdown (RSS/web/email/Google/AI)
- Source cards: per-source last-run timestamp, last artifact count, status
- Run history: recent acquisition runs with duration and artifact counts
- Dry-run button: operator-triggered, routes through approval gate, results shown inline

**Governance:** Live acquisition execution (non-dry-run) requires explicit approval. Dry-run is
proposable but still shows approval confirmation before execution.

**Tests target:** 40 tests.

---

### Pass 10N — Agent Bus Diagnostics Panel

**Priority:** 5

**Backend:** `runtime/agent_bus/bus.py` public API
- `list_heartbeats(vault_root, runtime=None)` — heartbeat recency per runtime
- `get_bus_mode(vault_root)` — local/server mode + config path + storage path
- `list_tasks(vault_root, ...)` — task queue state
- `list_events(vault_root, ...)` — recent bus events

**API methods to add:**
- `get_bus_diagnostics()` — mode + heartbeats + task queue counts + recent event count
- `get_bus_tasks(status="", runtime="", limit=20)` — filtered task list
- `get_bus_events(limit=30)` — recent events timeline

**Sidebar button:** `[U]` — title "Agent Bus"

**Panel layout:**
- Mode banner: local/server + storage path
- Heartbeat grid: per-runtime last heartbeat + staleness indicator
- Task queue: counts by status (open/claimed/in_progress/done/blocked)
- Task list: filterable by runtime/status — shows task type, sender, recipient, priority
- Event timeline: recent events with type, runtime, timestamp

**Governance:** Read-only. No task creation, no task claiming, no bus writes.

**Tests target:** 40 tests.

---

### Pass 10O — Graph Filter Bar

**Priority:** 6

**Backend:** No new API calls needed — graph data is already loaded from `get_graph_contract()`.
Filtering is Cytoscape-side only using `cy.elements().filter(...)` and `show()`/`hide()`.

**What to add:**
- Filter sidebar section above the graph (collapsible): chips/toggles for:
  - Node family (14 families from `NODE_TYPE_FAMILIES` — multi-select)
  - Trust state (8 states — multi-select)
  - Domain (derived from loaded graph data)
  - Project (derived from loaded graph data)
- "Reset filters" button
- Filter state persists as a JS object (not saved to disk — session-only)
- Preset bar already exists — presets can set filter state as well as style state

**CSS to add:** `.graph-filter-bar`, `.filter-section`, `.filter-chip`, `.filter-chip--active`, `.filter-group-label`, `.filter-reset-btn`

**Tests target:** 25 JS-level tests (`TestGraphFilterBarHTML`, `TestGraphFilterBarCSS`, `TestGraphFilterBarJS`).

---

### Pass 10P — Sprint Focus Quick Panel

**Priority:** 7

**Backend:** Read `00_HOME/Now.md` via existing file-read path. Write through `StudioService`.

**API methods to add:**
- `get_sprint_focus()` — reads `00_HOME/Now.md`, returns raw content + parsed sprint focus section
- `update_sprint_focus(new_content)` — routes through approval gate (Now.md is not protected but is a high-value file — approval required)

**Where it lives:** Inside the existing Project Workspace panel (`#panel-project-workspace`) as a new tab or top card, not a new panel. Keeps the sidebar from growing further.

**Layout:** Now.md content rendered as markdown preview + "Edit" button → textarea → "Propose change" → approval modal.

**Tests target:** 25 tests.

---

### Pass 10Q — Build Log Viewer Panel

**Priority:** 8

**Backend:** Direct file listing of `07_LOGS/Build-Logs/` — no backend module exists, needs a new one or inline reading.

**API methods to add:**
- `get_build_logs(limit=30, search="")` — lists `.md` files in `07_LOGS/Build-Logs/`, sorted by date descending, filtered by search term in filename
- `get_build_log_content(filename)` — reads single build log file content (read-only, no write)

**Sidebar button:** `[L]` — title "Build Logs"

**Panel layout:**
- Search bar + date range filter
- Log list: cards with date, descriptor, file size
- Detail view: rendered markdown content of selected log (breadcrumb back pattern)

**Governance:** Read-only. No log creation from this panel.

**Tests target:** 30 tests.

---

### Pass 10R — Decision Ledger Panel

**Priority:** 9

**Backend:** Direct file listing of `07_LOGS/Decision-Ledger/` + `07_LOGS/Pivot-Log/`.

**API methods to add:**
- `get_decision_ledger(limit=30)` — lists decision entries sorted by date
- `get_pivot_log(limit=20)` — lists pivot entries sorted by date
- `get_decision_detail(filename)` — reads single entry content

**Sidebar button:** Integrated into Build Log viewer panel as a tab (not a new sidebar button) — "Decisions" tab and "Pivots" tab alongside "Build Logs" tab.

**Governance:** Read-only.

**Tests target:** 25 tests.

---

### Deferred — Pass 10I (Pulse Panel)

Deferred at operator request. The `pulse_inspector.py` and `pulse_product_shell_panel.py` backends exist. When this pass is activated: sidebar `[Z]` button, `get_pulse_summary`/`get_pulse_candidates`/`get_enqueue_pipeline_status` API calls, candidate cards, enqueue-pipeline dry-run button through approval gate.

---

### Deferred — Governed Installer Build

The `.exe` is built at SHA-256 `830735D2`, 7.42 MB. Installer signing, Start Menu shortcut, startup entry, and Windows registry writes require a separate operator-approved approval packet before execution. This is the `studio-governed-installer-build-approval` pass. Do not execute without a formal approval artifact.

---

## 2. Phase 11 — What It Is

**Phase 11 is the Conversational Command Center for ChaseOS.**

It transforms ChaseOS from a graph/panel desktop tool (Phase 10 Studio) into a conversational
operating interface where the operator talks normally, pastes ideas, issues commands, and the
system responds by taking governed actions: creating nodes, dispatching runtimes, opening
browser tasks, routing to agents, proposing projects, or requesting approval.

**Product naming:** The Phase 11 conversational interface uses the canonical ChaseOS brand. The old **ChaserOS** UI alias is retired for current product copy. The distinction:

| Name | What It Is |
|------|-----------|
| **ChaseOS** | The product and framework: vault governance, capture pipeline, SIC, AOR, Gate, Agent Bus, Studio, and runtime infrastructure |
| **ChaseOS Chat** | The conversational interface layer inside ChaseOS Studio |
| **ChaseOS Studio** | The graph-first desktop shell (Phase 10) and host window for the ChaseOS Chat surface |

Historical note: earlier planning docs used `ChaserOS` as a UI alias. That alias should not appear in current product-facing copy. Internal code, filenames, and module names still use `chaseos`; do not rename runtime modules or imports as part of branding cleanup.

**Where it lives:** ChaseOS Chat runs inside ChaseOS Studio (the PyWebView shell)
as one or more new panels wired into the existing sidebar + panel system. It is not a separate
app. It shares the same Python backend, the same `StudioAPI` bridge, and the same governance
control plane.

---

## 3. What Phase 11 Is NOT

- Not a second control plane. Chat routes through the existing Gate/AOR/StudioService chain.
- Not a second truth store. Conversation memory and companion memory must map to governed vault structures and remain approval-gated, inspectable, and non-authoritative until separately promoted.
- Not a bypass for protected files, trust tiers, or approval requirements.
- Not a general-purpose chatbot wrapper. Every chat output is a governed system action.
- Not a UI that operates independently of the vault. All outputs persist to vault or are discarded.
- Not a replacement for the graph panel. ChaseOS Chat augments Studio; it does not replace it.
- Not a credential manager. API keys and OAuth tokens follow existing Credential-Boundaries-SOP.
- Not a browser-use engine. Browser-use tasks are dispatched through the existing Browser Operator surface.
- A chat message is user intent. It is not automatically permission to mutate canonical state.

---

## 4. Phase 11 Feature Families

Phase 11 has eleven feature families. Each is defined below with scope, governance, and MVP vs deferred split.

---

### Feature Family 1 — Conversational Command Router

**Purpose:** Classify free-form chat input into a governed intent, load the correct context,
route to the right backend, and return a structured response or proposal.

**Intent classes:**

| Intent Class | What It Means | Output |
|---|---|---|
| `chat-answer` | Pure Q&A, no system action | Text response |
| `project-create` | New project proposal | Creation packet for approval |
| `project-update` | Existing project update | Update proposal |
| `vault-node-create` | New knowledge/source note | Node creation proposal |
| `vault-node-update` | Update existing node metadata | Update proposal |
| `source-note` | New source note from pasted content | Quarantine capture + proposal |
| `synthesis-note` | AI-generated synthesis | Draft output, not canonical |
| `rnd-entry` | R&D feature register row | Proposal entry |
| `roadmap-item` | Add to roadmap | Roadmap update proposal |
| `runtime-task` | Dispatch to AOR workflow | AOR dispatch with approval |
| `browser-task` | Browser-use / computer-use | Browser operator dispatch |
| `scheduled-workflow` | Schedule a workflow | Schedule intent proposal |
| `model-chat` | Route to a specific model/provider | Model call through provider router |
| `approval-action` | Approve/reject a pending action | StudioService approval |
| `memory-save` | Save conversation content | Memory write proposal |
| `handoff` | Hand off to another runtime | Bus task creation |
| `archive` | Archive conversation | Archive write |
| `dashboard-query` | Read dashboard/system state | Read-only dashboard surface |

**Router implementation sketch:**
```
user_input → intent_classifier (LLM call with system prompt + context) → IntentResult
→ ContextLoader (load project/domain/runtime context as needed)
→ ActionProposer (generate proposal or execute read-only)
→ GovernanceCheck (gate/permission/trust tier check)
→ Response (proposal card | approval request | executed read | error)
```

**Implementation status (2026-05-08):** `runtime/studio/phase11_chat_router_contract.py`
now provides a read-only router intent contract and
`chaseos studio phase11-chat-router-contract --json` exposes it for CLI/Studio
consumers. It uses deterministic rule classification only and does not call an
LLM classifier, generate chat responses, dispatch runtimes, control browsers,
execute approvals, write conversation history, write vault files, create Agent
Bus tasks, mutate schedules, display credentials, or perform canonical
writeback. Model-bound intents must consume
`runtime/providers/routing_consumer_contract.py` before any future provider
call path can be considered.

**Governance:**
- Current seeded intent contract uses deterministic rules only; a future LLM intent classifier must be read-only with no vault writes at classification time
- Proposal generation is a draft — no vault writes until user approves
- All write actions route through `StudioService.execute_action(ActionSpec(...))`
- Prompt injection guard: treat all user input as untrusted per `Untrusted-Input-Handling-SOP.md`
- Embedded instructions in pasted content must be flagged, not executed

**MVP scope:** Intent classification + chat-answer + project-create + vault-node-create + approval-action
**Deferred:** browser-task, scheduled-workflow, handoff, memory-save automation

---

### Feature Family 2 — Project + Node Autogenesis

**Purpose:** When the user describes a new idea, tool, venture, or feature, ChaseOS proposes a
structured creation packet — not a silent write.

**Creation packet shape:**
```
{
  proposed_name: string,
  proposed_type: "project" | "knowledge_note" | "source_note" | "rnd_entry" | "roadmap_item",
  reason_new: string,          // why this is new vs. an existing item
  existing_candidate: string | null,  // closest existing match if any
  vault_path: string,          // suggested location
  linked_nodes: [string],      // suggested wikilinks
  project_os_stub: string | null,  // stub Project-OS content if type=project
  dashboard_card: boolean,     // should this appear on dashboard?
  domain: string,              // ChaseOS domain
  suggested_tags: [string],
  suggested_agents: [string],  // which runtimes would support this
  first_actions: [string],     // suggested next steps
  user_actions: ["approve", "edit", "merge", "reject"]
}
```

**Duplicate detection:** Before generating a proposal, scan the vault for similar node titles
using the existing graph index. If a close match exists, show merge option instead of create.

**Merge option:** Propose adding content to the existing node (frontmatter update or body append)
rather than creating a duplicate.

**After approval:** Route the creation through `StudioService.execute_action(ActionSpec(...))` —
not directly to the filesystem.

**Naming rules:**
- Use vault-standard naming conventions (sentence case for notes, kebab-case for filenames)
- Respect domain folder placement from Knowledge-Taxonomy and Vault-Map
- Never create files outside the approved vault structure

**Governance:** All creation is proposal-first. No silent vault mutations. User must explicitly
approve the packet before any file is written.

**MVP scope:** project creation + knowledge note creation + source note routing to quarantine
**Deferred:** rnd-entry auto-creation, roadmap-item creation, agent/runtime suggestion enrichment

---

### Feature Family 3 — Chat Workspace Experience

**Purpose:** Make the ChaseOS Chat interface feel like a modern AI workspace (persistent chats,
project context, attached files) while mapping everything to the ChaseOS vault structure.

**Current implementation status (2026-05-15):**
- `runtime/studio/phase11_chat_workspaces_foundation.py` is BUILT / PARTIAL / READ-ONLY.
- `runtime/studio/phase11_chat_route_state_and_message_drafts.py` is BUILT / PARTIAL / LOCAL UI STATE ONLY.
- The native Chat panel now renders ChaseOS Chat workspace cards for runtime ops, VentureOps, personal operator work, and source intelligence.
- The model includes project/folder/tab/thread shapes, runtime lanes for Hermes/OpenClaw/Codex, Discord transport binding posture, and proposal actions for thread creation, runtime board handoff, cron/schedule management, and chat-driven setup.
- Route-state selection and message draft/intent persistence are BUILT as local Studio UI state. Actual message sending, transcript/conversation persistence, Discord API/thread creation, runtime board writes, Agent Bus task writes, schedule mutation, provider/model calls, and canonical mutation remain NOT BUILT from ambient Chat.

**Chat persistence model:**
- Conversations are stored in `07_LOGS/Conversations/YYYY-MM-DD_[descriptor].md`
- Each conversation has a title, project context (optional), participants (user + which models)
- Conversations are read-only history — they are never canonical knowledge
- Conversations can be promoted to source notes (quarantine capture) with explicit operator action

**Project-level context:**
- Chat can be linked to a project (from the Project Workspace panel)
- When linked, the router auto-loads project context (Project-OS file + related nodes)
- Project context does not change permissions — it narrows context loading only

**File attachment:**
- User can attach local files; these are treated as quarantine captures (same as `chaseos capture file`)
- Attached content is not automatically canonical — it enters quarantine for review

**Conversation-to-X flows:**
- "Turn this into a project brief" → project-create proposal
- "Save this as a source note" → quarantine capture proposal
- "Add this to R&D" → rnd-entry proposal
- "Turn this into a roadmap item" → roadmap-item proposal
- All flows require user approval before any write

**MVP scope:** Chat history rendering + project context loading + file attach to quarantine
**Deferred:** Conversation-to-dashboard, conversation-to-vault-map, cross-session history search

---

### Feature Family 4 — Multi-Model Provider Router

**Purpose:** Route chat/task requests to the correct model provider while maintaining ChaseOS's
provider/surface/adapter/runtime distinctions.

**Layer definitions:**

| Layer | What It Is | Examples |
|---|---|---|
| Provider | The model service | Anthropic, OpenAI, Google, Perplexity, Ollama |
| Model | Specific model at a provider | claude-sonnet-4-6, gpt-4o, gemini-2.5-pro |
| Adapter | ChaseOS rules for a surface | ChaseOS-MCP-Server, n8n executor, RPGL |
| Surface | Where the model is invoked | chat, AOR workflow, SBP pipeline, browser-use |
| Runtime harness | An execution-capable agent environment | OpenClaw, Hermes, Chaser Agent |

**Provider status (2026-05-08 truth):**

| Provider | Status | Capability | Credential |
|---|---|---|---|
| Anthropic / Claude | ACTIVE | Advisory + AOR workflows + Hermes synthesis | `ANTHROPIC_API_KEY` env var |
| OpenAI / GPT | SHADOW PROOF | Adapter exists; no live proof | `OPENAI_API_KEY` env var |
| Perplexity | ACTIVE | Research capture via connector | `PERPLEXITY_API_KEY` env var |
| Grok / xAI | ACTIVE | Capture via connector | `XAI_API_KEY` env var |
| Ollama / local | PLANNED | Local fallback; not configured | local endpoint |
| Google Gemini | PLANNED | Provider lane defined; not live | OAuth / API key |
| OpenRouter | FUTURE | Aggregator lane; not planned | API key |
| n8n | SHADOW PROOF | Workflow hub; dry-run only | local deployment |

**Routing logic:**
```
chat_request → provider_router
  → check task_class (advisory / code / research / runtime / browser)
  → check model preference (user setting or default)
  → check provider health (RPGL provider governance)
  → check credential availability (env var present? fallback configured?)
  → select provider + model
  → call through adapter (ChaseOS API client, not raw HTTP)
  → return response with provider attribution
```

**Implementation status (2026-05-08):** `runtime/providers/routing_consumer_contract.py`
now provides the read-only Phase 11 provider routing consumer contract and
`chaseos runtime provider routing-consumer-contract --json` exposes it for
Studio/CLI consumers. This is not a live provider router: provider calls, config
writes, provider switching, approval consumption, markers, queue mutation, and
credential value display are denied by this surface. It depends on
`runtime/studio/provider_readiness.py` for active profile, fallback profile,
degraded reason, last probe marker/result, and queued retry count.

**Chat panel closeout status (2026-05-08):** `runtime/studio/phase11_chat_panel_contract.py`
and native Studio `#panel-chat` now provide a complete read-only Phase 11 Chat
foundation. The panel consumes the chat router contract and provider readiness
contract, renders slash-command preview, proposal-card preview,
approval-handoff preflight, provider readiness, live-routing gate state, denied
authority, and closeout evidence, and keeps live model execution blocked. It
does not persist conversations, call providers, execute live probes, switch
providers, display credential values, queue approvals, dispatch runtimes,
control browsers, write Agent Bus tasks, write vault files, or mutate canonical
state. Post-closeout future work remains approval queue writes, conversation
persistence, live provider execution, approval consumption, and browser/runtime
dispatch.

**Approval handoff queue contract status (2026-05-08):**
`runtime/studio/phase11_chat_approval_handoff_queue_contract.py` now closes the
final foundation gap as a read-only queue-handoff contract. It previews the
future `StudioService.queue_for_approval` packet for supported Chat proposal
intents, including future target path, action type, approval class, metadata,
blocked reasons, and denied authority. It does not call the queue writer, write
`runtime/studio/approvals`, grant/reject/execute approvals, persist chat,
dispatch runtimes, control browsers, call providers, or mutate canonical state.

**Post-closeout planning status (2026-05-09):**
`runtime/studio/phase11_post_closeout_planning.py` is now the read-only
dependency map for the remaining Conversational Command Center work. It is
exposed through `chaseos studio phase11-post-closeout-planning --json`,
StudioAPI `get_phase11_post_closeout_planning`, the native Chat panel contract,
and the native panel registry. It selects
`phase11-chat-conversation-persistence-approval-contract` as the next
recommended pass because conversation/audit targets should exist before live
provider execution or Chat-originated queue writes. Verification covered focused
Phase 11 planning tests (`35 passed`), QA runner static dry run and suite
(`29 passed`), CLI command/JSON contracts (`22 passed`), the full native shell
suite (`1330 passed`), runtime CLI (`54 passed`), generated CLI docs, and broad
Studio/CLI/runtime regression (`2769 passed`). It does not write
conversation logs, queue approvals, execute approvals, call providers, dispatch
runtimes, control browsers, write Agent Bus tasks, write vault files, or mutate
canonical state.

**Approval queue write execution proof status (2026-05-09):**
`runtime/studio/phase11_chat_approval_queue_write.py` now closes the first
approval-gated Chat proposal queue-write proof. It is exposed through
`chaseos studio phase11-chat-approval-queue-write-execution-proof --json`,
StudioAPI preview/write methods, native Chat panel queue-write controls, the
Approval Center source display, panel-registry readiness, and QA runner surface
`phase11-chat-approval-queue-write-execution-proof`. The live proof wrote one
pending Studio approval artifact under `runtime/studio/approvals/` for a Chat
proposal, returned the existing request on duplicate queue attempts, and keeps
`StudioService.execute_approved` blocked for this proof class before target
writes. It does not write the proposed target Markdown, persist conversations,
execute approvals, call providers/models, dispatch runtimes, control browsers,
write Agent Bus tasks, mutate Gate/Git/workflow/host/release surfaces, or
mutate canonical state. This was followed by the now-complete
`phase11-chat-live-provider-execution-approval-preview`; the current next
recommended pass is `phase11-chat-runtime-dispatch-readiness-contract`.

**Live provider execution approval preview status (2026-05-10):**
`runtime/studio/phase11_chat_live_provider_approval_preview.py` now closes the
no-call approval preview required before any future Chat-originated provider
execution. It is exposed through
`chaseos studio phase11-chat-live-provider-execution-approval-preview --json`,
StudioAPI `get_phase11_chat_live_provider_execution_approval_preview`, native
Chat panel rendering, panel-registry readiness, and QA runner surface
`phase11-chat-live-provider-execution-approval-preview`. The pass builds a
request digest, provider-readiness preflight, conversation-audit target preview,
and future approval packet shape for model-bound intents only. It does not write
approval artifacts, execute approvals, call providers/models, persist
conversations, dispatch runtimes/browsers, write Agent Bus tasks, mutate
Gate/Git/workflow/host/release surfaces, or mutate canonical state. Current
provider execution remains blocked by provider readiness evidence. The current
next recommended pass was `phase11-chat-runtime-dispatch-readiness-contract`,
which is now complete.

**Runtime dispatch readiness status (2026-05-11):**
`runtime/studio/phase11_chat_runtime_dispatch_readiness.py` now provides the
read-only runtime dispatch readiness contract for Chat-originated runtime-task
intents. It is exposed through
`chaseos studio phase11-chat-runtime-dispatch-readiness-contract --json`,
StudioAPI `get_phase11_chat_runtime_dispatch_readiness`, native Chat panel
rendering, panel-registry readiness, and QA runner surface
`phase11-chat-runtime-dispatch-readiness-contract`. The pass consumes runtime
capability manifests, Agent Bus storage in read-only mode, AOR workflow registry
posture, and Runtime Cockpit action readiness, then previews digest-bound future
dispatch packets. It does not write approval artifacts, execute approvals,
create Agent Bus tasks, dispatch workflows, mutate runtime lifecycle, call
providers/models, control browsers, write vault files, or mutate canonical
state. The next dispatch lane was
`phase11-chat-browser-dispatch-readiness-contract`, now complete.

**Browser dispatch readiness status (2026-05-11):**
`runtime/studio/phase11_chat_browser_dispatch_readiness.py` now provides the
read-only browser dispatch readiness contract for Chat-originated browser-task
intents. It is exposed through StudioAPI
`get_phase11_chat_browser_dispatch_readiness`, native Chat panel rendering,
panel-registry readiness, and QA runner surface
`phase11-chat-browser-dispatch-readiness-contract`. The pass consumes external
Browser Use CLI and Excalidraw readiness, builds digest-bound future browser
dispatch packet previews, and keeps all effects blocked. It does not launch a
browser, invoke Browser Use CLI/CDP/MCP, navigate targets, capture screenshots,
write approval artifacts, execute approvals, create Agent Bus tasks, call
providers/models, mutate Gate/Git/workflow/host surfaces, or mutate canonical
state. The current next recommended pass is
`phase11-chat-approval-consumption-readiness-contract`.

**Approval consumption readiness + companion selection status (2026-05-11):**
`runtime/studio/phase11_chat_approval_consumption_readiness.py` provides the
read-only approval-consumption readiness contract for Chat-originated approval
packets, and `runtime/studio/phase11_chat_companion_selection_preview.py`
provides the companion-selection approval-preview contract. The companion
selection preview is exposed through CLI, StudioAPI, native Chat panel rendering,
panel registry readiness, and QA runner surface
`phase11-chat-companion-selection-approval-preview`. It builds a deterministic
selection digest and future approval packet preview only. It does not write an
approval artifact, consume or execute approvals, mutate companion selection
state, mutate runtime identity/profile/role-card files, dispatch runtimes, call
providers/models, control browsers, write Agent Bus tasks, or mutate canonical
state.

**Companion selection queue-write and consumption-executor status (2026-05-12):**
The current repo contains `runtime/studio/phase11_chat_companion_selection_queue_write_readiness.py`,
`runtime/studio/phase11_chat_companion_selection_queue_write_execution.py`,
`runtime/studio/phase11_chat_companion_selection_approval_consumption_readiness.py`, and
`runtime/studio/phase11_chat_companion_selection_approval_consumption_executor.py`.
Live CLI/static QA now verify digest-gated pending approval artifact writes,
duplicate digest blocking, read-only approval-consumption preflight, digest
replay mismatch blocks, missing approval blocks, exact-once consumption marker
writes, approval status mutation to executed, target write to
`runtime/studio/chat/companion-selection.json`, duplicate execution blocking
before target rewrite, and service fail-closed behavior for generic execution.
Runtime control, provider/model calls, Agent Bus task writes, identity/profile
or role-card mutation, broad approval execution, and canonical mutation remain
blocked.

**Read-only slash command responses + UI status (2026-05-12):**
`runtime/studio/phase11_chat_readonly_slash_command_responses.py` provides
bounded response cards for safe read-only slash commands, and the native Chat
frontend now renders those cards through `runtime/studio/shell/frontend/app.js`
and `runtime/studio/shell/frontend/styles.css`. The response builder, StudioAPI,
Chat panel contract embedding, panel-registry readiness, QA runner, CLI surface,
CLI contract/docs, frontend renderer, and static UI QA are verified. Unknown,
write, or execution slash commands return help or boundary cards. This surface
does not execute slash commands, write approvals, consume approvals, call
providers/models, dispatch runtimes/browsers, persist conversations, write vault
files, write graph indexes or node IDs, create Agent Bus tasks, display
credentials, or mutate canonical state. Browser viewport visual proof was
completed by `phase11-chat-readonly-card-visual-qa`; the follow-on no-HITL
selection, slash catalog, and dashboard aggregate audits are complete through
`phase11-chat-readonly-operator-dashboard-aggregate-audit`.

**Credential discipline:** API keys are read from environment variables only. They are never
displayed in the UI, stored in the vault, logged in build logs, or passed in audit events.
Follow `04_SOPS/Credential-Boundaries-SOP.md` exactly.

**Fallback behavior:** If the primary provider fails or rate-limits, route to the configured
fallback per RPGL policy. Never silently fail without surfacing the failure reason.

**Model selection UI:** User selects provider/model from a dropdown or slash command. The system
shows: model name, advisory-only vs execution-capable marker, credential status (set / missing),
usage mode (chat / AOR / research).

**MVP scope:** Anthropic lane (already live) + Perplexity research capture + provider health indicator
**Deferred:** OpenAI live, Google Gemini, OpenRouter, Ollama local fallback, multi-model parallel calls

---

### Feature Family 5 — Runtime Chat Control

**Purpose:** Let the operator command existing runtimes (AOR, Hermes, OpenClaw, Browser Operator)
from the chat interface without needing to run CLI commands.

**Commands the chat surface must support:**

```
"Run operator_today"               → AOR workflow dispatch (approval required)
"Ask Hermes to review this"        → Agent Bus task creation (review type)
"Show me what's in the AOR queue"  → read-only bus query
"Show failed runs today"           → AOR execution filter query
"Show what needs approval"         → approval queue read
"Stop the current SBP run"         → governed stop request (approval required)
"Show me all heartbeats"           → bus diagnostics read
"Schedule a weekly digest"         → schedule intent proposal (approval required)
```

**Runtime status display:** Chat responses that reference a runtime should include a runtime
status card: name, last heartbeat, mode (advisory/active/blocked/scheduled), current task if any.

**Approval-gated commands:** Any command that dispatches a workflow, creates a task, modifies
a schedule, or stops a running process must go through the approval gate before execution.
The chat surface shows the approval modal inline (same `ApprovalModal` component from Phase 10C).

**Permissions:** The chat surface does not grant new runtime permissions. A runtime that cannot
perform an action via CLI cannot perform it via chat. The chat is a front-end only.

**Audit:** Every runtime command dispatched via chat creates an audit event in
`07_LOGS/Agent-Activity/` with `surface: chaseros_chat` in the event metadata.

**MVP scope:** AOR run dispatch (approval required) + bus queue read + approval queue read
**Deferred:** Stop/pause/resume runtime, force-kill task, cross-runtime handoff from chat

**Approval Center routing note:** Chat-originated approval or approval-queue surfaces must point operators to [[ChaseOS-Approval-Center]] for the current cross-feature source map, read-only/read-write boundary, and execution-denial truth.

---

### Feature Family 6 — Browser-Use / Computer-Use Task Interface

**Purpose:** Let the operator request browser or computer-use tasks from chat. The existing
Browser Operator surface (`runtime/operator_surface/browser/`) handles execution.

**Chat surface responsibilities:**
- Accept natural-language browser task descriptions
- Classify as: open URL / research page / screenshot / replay / custom
- Generate a `BrowserTask` proposal (URL, action type, settle time, write evidence flag)
- Show the proposal for operator review before dispatch
- Show evidence (screenshot, JSON result) inline after completion

**Governance (from Browser Operator surface rules):**
- No credential exposure — browser sessions use throwaway profiles
- No unrestricted browsing — known-target registry applies
- No uncontrolled write actions
- No direct secrets handling
- All browser runs produce a `07_LOGS/Browser-Runs/` evidence file
- Approval required for any browser action beyond `open` (inspect, screenshot, replay, custom)

**Computer-use scope (2026-05-06 truth):** Computer-use beyond browser control is NOT planned
for Phase 11. The Agent Control UX Contract (`06_AGENTS/Agent-Control-UX-Contract.md`) defines
browser as the only locally proven lane. Files/system/OS control remains deferred and must be
treated as the highest-risk lane requiring its own dedicated architecture pass.

**MVP scope:** Browser open + screenshot from chat (approval required) + evidence display
**Deferred:** Computer-use beyond browser, file-explorer control, OS-level automation

---

### Feature Family 7 — Agent Companion System (Slash Pets)

**Purpose:** Give each ChaseOS runtime a visual identity, personality, and status indicator
inside the Studio shell. This is a UX/status layer — not an authority layer.

**Canonical rule (non-negotiable):**
> Companion personality does not grant authority.
> A companion's name, avatar, tone, or status cannot expand permissions, grant file access,
> enable browser control, provide credential access, or change trust tiers.
> Authority comes only from `Permission-Matrix.md`, `Trust-Tiers.md`, and the Gate.

**What a companion is:**
- A named, visually represented identity for a runtime (Hermes companion, OpenClaw companion, Chaser Agent companion)
- Shows runtime status, last activity, health state, current mode
- Has a personality/tone that shapes how it communicates in the chat interface
- Has a visual avatar (icon, ASCII sprite, or small image)
- Can be customized by the operator (name, avatar, speaking style)

**What a companion is NOT:**
- Not a separate agent or runtime
- Not a permission boundary
- Not a credential holder
- Not a trust escalation path
- Not a separate process
- Not a toy only — companions surface real runtime state and real health data

**Companion profile schema:**
```yaml
# 06_AGENTS/companions/[runtime-id]-companion.yaml
companion_id: hermes-companion
runtime_id: hermes
display_name: Hermes
avatar_icon: "H"  # single letter fallback for non-visual contexts
avatar_style: scholarly  # personality style
status_messages:
  drafting: "Reviewing..."
  waiting: "Waiting for approval."
  blocked: "Blocked — needs operator input."
  complete: "Done. Output written."
  idle: "Ready."
speaking_tone: careful-strategic
specialty: research-synthesis
default_model: claude-haiku-4-5-20251001
runtime_lane: hermes
trust_tier: 2  # read from Agent Registry — not overridable here
permission_ceiling: advisory-plus-aor  # from Trust-Tiers.md — not overridable here
current_mode: advisory  # derived from bus heartbeat — not set here
last_activity_source: "07_LOGS/Agent-Activity/"
```

**Built-in companions (Phase 11 MVP):**

| Companion | Runtime | Style | Specialty |
|---|---|---|---|
| Hermes | hermes | Careful, strategic, scholarly | Research synthesis, repo-aware review |
| OpenClaw | openclaw | Execution-oriented, direct | Browser/computer-use, workflow dispatch |
| Chaser Agent | chaser_agent | Engineering-focused, precise | Code passes, implementation, testing |
| Scout | future-local | Minimal, offline marker | Local model fallback, privacy-first tasks |

**Slash commands for companions:**
```
/pet                   → show all companion status
/pet hermes            → show Hermes companion status + last activity
/pet assign hermes     → set Hermes as the active companion for this chat session
/pet mute openclaw     → suppress OpenClaw status in current session
/pet reset             → clear session companion assignment
/companion status      → same as /pet
/companion hermes chat → open direct chat routing to Hermes runtime lane
```

**Storage:**
- Companion profiles: `06_AGENTS/companions/[id]-companion.yaml`
- Companion registry: `06_AGENTS/Agent-Companion-Registry.md`
- Template: `05_TEMPLATES/Agent-Companion-Profile-Template.md`
- Runtime state (current_mode, last_heartbeat) — derived at runtime from Agent Bus, not stored in companion file

**Visual states (for UI rendering):**
```
idle     → gray border, dim avatar
active   → blue border, bright avatar
drafting → pulsing yellow border
blocked  → orange border, warning icon
error    → red border, error icon
complete → green flash, then idle
```

**MVP scope:** Hermes + OpenClaw + Chaser Agent companions defined; `/pet` slash command direction; companion status card in chat responses. Current implementation truth includes authority-neutral companion status cards, digest-bound companion-selection approval previews, approval queue-write readiness/execution proof, approval-consumption readiness, one governed companion-selection approval-consumption executor proof, and separate governed companion memory namespace boundary/readiness with memory writes still blocked.

**Mobile/tablet bridge:** `06_AGENTS/Companion-Surface-Mobile-Tablet-Architecture.md` extends this companion UX into a Phase 10 companion-surface lane for brief viewing, approval inboxes, capture-trigger previews, runtime status, and gateway/mobile delivery posture. It does not activate live mobile authority; all actions still route through Gate/AOR/StudioService and lower-layer gateway/capture/runtime-dispatch dependencies.

**Deferred:** Custom avatar upload, animated sprites, companion persona editor UI, live mobile/tablet delivery, live capture triggers, and any direct companion selection target write.

---

### Feature Family 8 — Slash Command Surface

**Purpose:** Slash commands as first-class UX. They are governed shortcuts into the same
command router — not bypasses.

**Slash command catalog (Phase 11 MVP and future):**

| Command | Intent Class | Permission | MVP/Future |
|---|---|---|---|
| `/new-project [name]` | project-create | Proposal → approval | MVP |
| `/map [domain]` | dashboard-query | Read-only | MVP |
| `/dashboard` | dashboard-query | Read-only | MVP |
| `/vault [query]` | dashboard-query | Read-only | MVP |
| `/memory save` | memory-save | Proposal → approval | MVP |
| `/memory show` | dashboard-query | Read-only | MVP |
| `/run [workflow]` | runtime-task | Approval required | MVP |
| `/agent [runtime] [command]` | runtime-task | Approval required | MVP |
| `/runtime status` | dashboard-query | Read-only | MVP |
| `/models` | dashboard-query | Read-only | MVP |
| `/provider [name]` | dashboard-query | Read-only | MVP |
| `/browser open [url]` | browser-task | Approval required | MVP |
| `/approve [id]` | approval-action | Write (approval) | MVP |
| `/reject [id]` | approval-action | Write (rejection) | MVP |
| `/handoff [runtime]` | handoff | Proposal → approval | MVP |
| `/log [filter]` | dashboard-query | Read-only | MVP |
| `/archive` | archive | Proposal → approval | MVP |
| `/rnd [idea]` | rnd-entry | Proposal | MVP |
| `/pet [runtime]` | companion status | Read-only | MVP |
| `/companion [runtime]` | companion chat | Routing | MVP |
| `/new-node [type] [title]` | vault-node-create | Proposal → approval | Future |
| `/search [query]` | dashboard-query | Read-only | Future |
| `/schedule [workflow] [cron]` | scheduled-workflow | Proposal → approval | Future |
| `/browser screenshot [url]` | browser-task | Approval required | Future |
| `/export [format]` | archive | Proposal | Future |

**Slash command governance:**
- Slash commands are parsed client-side (JS) before entering the router
- They receive no elevated permissions; the same approval rules apply
- Unknown commands show a help card listing available commands
- Commands with write side-effects always show a proposal first

**Current implementation truth (2026-05-12):** `runtime/studio/phase11_chat_readonly_slash_command_responses.py` now provides verified read-only response cards for `/dashboard`, `/map`, `/vault`, `/runtime status`, `/models`, `/provider`, `/log`, `/memory show`, and `/pet`. `runtime/studio/phase11_readonly_slash_command_catalog_audit.py` verifies the supported/blocked catalog, and `runtime/studio/phase11_readonly_operator_dashboard_aggregate_audit.py` verifies `/dashboard` aggregate coverage across approval center, provider readiness, runtime status, companion status, recent build logs, and slash catalog sources. Unknown commands return help cards, and write/execution commands such as `/run`, `/approve`, `/reject`, `/browser`, `/new-project`, `/new-node`, `/archive`, and `/rnd` return boundary cards without executing, writing approval artifacts, dispatching runtimes/browsers, calling providers/models, writing Agent Bus tasks, or mutating canonical state.

**Workspace Mode selector truth (2026-05-14):** Chat now exposes the Workspace Mode Layer through a read-only `Workspace Mode Studio` card selector in `runtime/studio/phase11_chat_panel_contract.py` and `runtime/studio/shell/frontend/app.js`. The selector renders WML mode cards, project/domain/route previews, and `wml_mode` Studio deep links. It is a navigation-only surface: selecting a WML mode does not execute workflows, write profiles, consume approvals, dispatch Agent Bus tasks, call providers, or mutate canonical state. Canonical WML feature-family node: [[Workspace-Mode-Layer-Feature-Family]].

---

### Feature Family 9 — Dashboard + Vault Map Expansion

**Purpose:** Surface system-wide state in the chat interface through natural-language queries
and dashboard cards.

**Queryable surfaces from chat:**
- Active projects (from project workspace data)
- Pending approvals count and list
- Hermes/OpenClaw/Chaser Agent last activity
- AOR pipeline status
- Quarantine queue depth
- Schedule next-run times
- Recent build logs (last 5)
- Current sprint focus (Now.md)
- SIC workspace count and index status

**Dashboard card format (inline in chat responses):**
```
┌─ Active Projects ──────────────────────────────────────┐
│  TradeSync         [active]   7 open tasks              │
│  ChaseOS Studio    [active]   Phase 10 completion       │
│  StrikeZone SBP    [active]   weekly digest scheduled   │
└────────────────────────────────────────────────────────┘
```

**Vault map integration:** When the user asks "what relates to X?", the system queries the graph
index (using `build_graph_view_contract` with a focus node) and surfaces related nodes as
a list with trust states and provenance indicators.

**Governance:** All dashboard queries are read-only. No dashboard read writes any vault state.

---

### Feature Family 10 — Conversation Memory Controls

**Purpose:** Let the operator decide what to save from conversations, using typed memory classes.

**Memory classes (matching `Agent-Memory-Architecture.md` Layer structure):**

| Class | What It Is | Storage Target |
|---|---|---|
| `user-preference` | Operator preferences for system behavior | `runtime/memory/adapters/claude/profile.json` |
| `project-state` | Current project truth | Relevant `Project-OS.md` (via approval) |
| `decision` | Decision rationale | `07_LOGS/Decision-Ledger/` (via approval) |
| `source-note` | External content | `03_INPUTS/00_QUARANTINE/` (capture then promote) |
| `synthesis-note` | AI-generated synthesis | Layer B → Layer C per AI-Generated-Output-Bridge |
| `task` | Action item | `00_HOME/Now.md` or project OS (via approval) |
| `runtime-activity` | What a runtime did | `07_LOGS/Agent-Activity/` (read-only display) |
| `rnd-feature` | Feature idea | `06_AGENTS/Feature-Fit-Register.md` (via approval) |
| `roadmap-item` | Phase/milestone entry | `ROADMAP.md` (via approval, protected border) |

**Operator commands:**
```
"Save this as project memory"       → project-state memory proposal
"Don't save this"                   → no write, discard current conversation content
"Turn this into a source note"      → quarantine capture proposal
"Archive this conversation"         → conversation archive write
"Show me what you'd save"           → show proposed memory packet, no write yet
"Save this to R&D"                  → rnd-feature entry proposal
```

**Governance:**
- No automatic memory saves. Operator must explicitly request a save or approve a proposal.
- Conversation content does not become canonical knowledge without explicit promotion.
- Raw conversation text that goes to quarantine is treated as untrusted content (same as any capture).
- Memory writes to protected files (`SOUL.md`, `Principles.md`, `Assistant-Contract.md`, etc.) are blocked entirely — not approval-gated.

---

### Feature Family 11 — R&D + Feature Register Integration

**Purpose:** When chat describes a feature idea, surface a structured R&D entry proposal.

**R&D entry proposal:**
```
{
  feature_name: string,
  description: string,
  proposed_phase: "Phase 10" | "Phase 11" | "Future",
  layer: "Phase 8/Capture" | "Phase 9/AOR" | "Phase 10/Studio" | "Phase 11/Chat" | "Cross-cutting",
  dependencies: [string],
  governance_notes: string,
  status: "Idea Only",  // always starts here; never auto-promoted
  source: "conversation YYYY-MM-DD"
}
```

**Trigger:** User says something like "we should add X" or "wouldn't it be good if Y" in chat.
Router classifies as `rnd-entry` intent and generates a proposal card.

**Approval path:** User approves → entry added to `06_AGENTS/Feature-Fit-Register.md` as an
"Idea Only" row (via `StudioService` → Gate). Entry is not marked as planned or implemented
without a separate, deliberate architecture pass.

---

## 5. Architecture — How It All Fits Together

```
┌─────────────────────────────────────────────────────────┐
│            ChaseOS Chat Surface (Phase 11)               │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Chat Panel (#panel-chat)               │  │
│  │   Input bar → Slash command parser → Router call   │  │
│  │   Response renderer → Proposal cards → Approval    │  │
│  │   Companion status bar (Hermes / OpenClaw / etc.)  │  │
│  └────────────────┬───────────────────────────────────┘  │
│                   │ window.pywebview.api.chat_input()     │
│  ┌────────────────▼───────────────────────────────────┐  │
│  │         StudioAPI Bridge (extended for Phase 11)    │  │
│  │  chat_input(message, session_id, project_ctx)       │  │
│  │  get_chat_history(session_id)                       │  │
│  │  get_companion_status()                             │  │
│  │  submit_slash_command(command, args)                │  │
│  │  [all Phase 10 read/write methods still present]    │  │
│  └────────────────┬───────────────────────────────────┘  │
│                   │                                       │
│  ┌────────────────▼───────────────────────────────────┐  │
│  │            Conversational Command Router            │  │
│  │  runtime/studio/shell/chat_router.py                │  │
│  │  IntentClassifier → ContextLoader → ActionProposer  │  │
│  │  → GovernanceCheck → Response builder               │  │
│  └────────────────┬───────────────────────────────────┘  │
│                   │                                       │
│  ┌────────────────▼───────────────────────────────────┐  │
│  │        Existing ChaseOS Control Plane               │  │
│  │  StudioService  │  AOR/engine  │  Agent Bus         │  │
│  │  Gate           │  SIC         │  Browser Operator  │  │
│  │  Approval queue │  Schedules   │  Capture pipeline  │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Key principle:** The chat surface is one more client of the existing control plane.
It has no special authority that a CLI command does not also have.

---

## 6. New Files Phase 11 Will Create

**`runtime/studio/shell/` additions:**
- `runtime/studio/phase11_chat_router_contract.py` - BUILT as the read-only deterministic intent/router contract; no LLM classifier or execution; dependency reports use the exact handover fields `affected_phase10_or_phase11_surface` and `lower_phase_owner_or_surface`
- `runtime/studio/phase11_chat_safety_policy.py` - BUILT as the deny-default action-class policy surface; no provider, browser, shell, Agent Bus, approval-consumption, credential/config, protected-file, graph, or canonical authority
- `runtime/studio/phase11_chat_panel_contract.py` - BUILT/CLOSED as the native Studio Chat panel closeout contract; no persistence or live execution
- `runtime/studio/phase11_chat_workspaces_foundation.py` - BUILT/PARTIAL as the read-only native Studio Chat project/folder/tab/thread/runtime-lane foundation; no conversation persistence, thread creation, message send, Discord API call, Agent Bus task write, runtime board write, schedule mutation, provider call, or canonical mutation
- `runtime/studio/phase11_chat_workspace_proposal_writer.py` - BUILT/PARTIAL as the digest-bound Studio Chat workspace/folder/thread proposal approval-queue writer; writes pending approval artifacts only after exact digest match and keeps target workspace state, Discord, Agent Bus, board, schedule, provider, and canonical writes blocked
- `runtime/studio/phase11_chat_workspace_proposal_consumption_executor.py` - BUILT/PARTIAL as the governed exact-once consumer for approved Studio Chat workspace/folder/thread proposal artifacts; writes one proposal JSON record only and keeps actual Chat state creation, Discord, Agent Bus, board, schedule, provider, credential, and canonical writes blocked
- `runtime/studio/phase11_chat_native_state.py` - BUILT/PARTIAL as the local file-backed native Studio Chat state reader/path helper; no Discord, Agent Bus, board, schedule, provider, credential, or canonical authority
- `runtime/studio/phase11_chat_workspace_target_state_executor.py` - BUILT/PARTIAL as the governed exact-once target-state executor for approved Studio Chat proposal records; writes native workspace/folder/thread JSON state only and keeps Discord, Agent Bus, runtime board, schedule, provider, credential, and canonical writes blocked
- `runtime/studio/phase11_chat_route_state_and_message_drafts.py` - BUILT/PARTIAL as the local Studio Chat route-state and message draft/intent persistence surface; writes only local UI state and keeps message send, transcript/conversation logging, Discord, Agent Bus, runtime board, schedule, provider, credential, and canonical writes blocked
- `runtime/studio/phase11_chat_runtime_board_handoff_proposal.py` - BUILT/PARTIAL as the digest-bound approval request surface for future runtime board handoffs; actual runtime board, Agent Bus, runtime dispatch, Discord, schedule, provider, credential, and canonical effects remain blocked
- `runtime/studio/phase11_chat_schedule_proposal_packet.py` - BUILT/PARTIAL as the digest-bound approval request surface for future schedule-intent YAML writes; actual schedule YAML writes, schedule-index regeneration, external scheduler mutation, runtime dispatch, Discord, provider, credential, and canonical effects remain blocked
- `runtime/studio/phase11_chat_schedule_proposal_consumption_executor.py` - BUILT/PARTIAL as the governed exact-once consumer for approved Studio Chat schedule proposal artifacts; writes one staged approved proposal JSON record only and keeps actual schedule YAML, index, external scheduler, runtime dispatch, Discord, provider, credential, and canonical effects blocked
- `runtime/studio/phase11_chat_approved_schedule_intent_writer.py` - BUILT/PARTIAL as the governed exact-once writer for approved disabled schedule intent YAML plus `runtime/schedules/index.yaml` regeneration; schedule enablement and external scheduler effects remain separate
- `runtime/studio/phase11_chat_schedule_intent_activation_readiness.py` - BUILT/PARTIAL as the digest-bound activation approval packet surface for disabled schedule intents; ambient approval execution remains blocked
- `runtime/studio/phase11_chat_approved_schedule_activation_executor.py` - BUILT/PARTIAL as the governed exact-once activation consumer that enables one approved schedule and regenerates the schedule index; external scheduler, OpenClaw/Hermes cron, Agent Bus/runtime dispatch, Discord, provider, credential, and broader canonical effects remain blocked
- `runtime/studio/phase11_chat_schedule_adapter_export_readiness.py` - BUILT/PARTIAL as the digest-bound adapter export approval packet surface over enabled schedules; packet write remains explicit-writer-only, while external scheduler, OpenClaw/Hermes cron, Agent Bus/runtime dispatch, Discord, provider, credential, and broader canonical effects remain blocked
- `runtime/studio/phase11_chat_approved_schedule_adapter_export_packet_writer.py` - BUILT/PARTIAL as the governed exact-once consumer for approved adapter export packet artifacts; writes one local JSON packet under `runtime/studio/chat/schedule-adapter-exports/` only and keeps external scheduler, OpenClaw/Hermes cron, Agent Bus/runtime dispatch, Discord, provider, credential, and broader canonical effects blocked
- `runtime/studio/phase11_chat_approval_handoff_queue_contract.py` - BUILT/CLOSED as the read-only approval queue handoff contract; previews future queue packet only
- `runtime/studio/phase11_chat_conversation_persistence_contract.py` - BUILT/CLOSED as the read-only conversation persistence approval contract; previews `07_LOGS/Conversations/` target paths and approval packet shape only
- `runtime/studio/phase11_chat_approval_queue_write.py` - BUILT/CLOSED as the approval-gated Chat proposal approval-queue write proof; writes pending approval artifacts only with explicit operator confirmation and keeps execution blocked
- `runtime/studio/phase11_chat_approval_consumption_readiness.py` - BUILT/CLOSED as the read-only approval-consumption readiness contract; no approval mutation, marker write, execution, or target write
- `runtime/studio/phase11_chat_approval_consumption_executor.py` - BUILT as a bounded executor contract surface for separately approved approval consumption; not Chat ambient authority
- `runtime/studio/phase11_chat_runtime_dispatch_readiness.py` - BUILT/CLOSED as read-only runtime dispatch readiness; no Agent Bus task write, claim, or workflow/runtime execution
- `runtime/studio/phase11_chat_runtime_dispatch_executor.py` - BUILT/CLOSED as governed approval-consumption executor for one bounded Agent Bus task enqueue; no task claim, workflow/runtime execution, provider/model call, browser control, target mutation, or canonical writeback
- `runtime/studio/phase11_chat_agent_bus_dispatch_bridge.py` - BUILT as an Agent Bus dispatch bridge preview/readiness surface; no Agent Bus task write or runtime dispatch
- `runtime/studio/phase11_chat_browser_dispatch_readiness.py` - BUILT/CLOSED as browser dispatch readiness; no browser launch, CDP/MCP/Browser Use invocation, navigation, screenshots, or browser-run writes
- `runtime/studio/phase11_chat_live_provider_approval_preview.py` - BUILT/CLOSED as provider-execution approval preview; no provider/model call, approval write, approval execution, conversation write, runtime/browser dispatch, Agent Bus task write, or canonical mutation
- `runtime/studio/phase11_chat_live_provider_execution_contract.py` - BUILT as the live-provider execution contract proof surface; provider execution remains approval-gated and outside ambient Chat authority
- `runtime/studio/phase11_chat_companion_status.py` - BUILT/CLOSED as companion status readiness; no runtime control, identity mutation, profile write, or Agent Bus write
- `runtime/studio/phase11_chat_companion_selection_preview.py` - BUILT/CLOSED as companion selection approval preview; no approval artifact write or selection mutation
- `runtime/studio/phase11_chat_companion_selection_queue_write_readiness.py` - BUILT/CLOSED as companion selection queue-write readiness; queue writes remain blocked
- `runtime/studio/phase11_chat_companion_selection_queue_write_execution.py` - BUILT/CLOSED as companion selection approval queue-write execution proof; writes pending approval artifacts only with digest match and keeps approval execution/selection target writes blocked
- `runtime/studio/phase11_chat_companion_selection_approval_consumption_readiness.py` - BUILT/CLOSED as read-only companion selection approval-consumption readiness; no approval status mutation, exact-once marker write, approval execution, target write, runtime control, provider call, or Agent Bus task write
- `runtime/studio/phase11_goal_checkpoint_contract.py` - BUILT as long-running `/goal` checkpoint contract support; no authority expansion
- `runtime/studio/phase11_post_closeout_planning.py` - BUILT/CLOSED as post-closeout planning/status support; no authority expansion
- `chat_router.py` — FUTURE live Conversational Command Router (intent classification, context loading, proposal building)
- `chat_session.py` — chat session state management (in-memory, with optional vault persistence)
- `companion_registry.py` — loads and resolves companion profiles from `06_AGENTS/companions/`
- `slash_command_parser.py` — slash command tokenizer and validator
- `frontend/chatPanel.js` — chat panel JS (message rendering, proposal cards, companion bar)
- `frontend/slashCommands.js` — slash command autocomplete and parser
- `frontend/companionBar.js` — companion status bar rendering
- `test_phase11_chat_router.py` — router unit tests
- `test_phase11_companion.py` — companion system tests
- `test_phase11_slash_commands.py` — slash command surface tests

**`06_AGENTS/` additions:**
- `Agent-Companion-Registry.md` — canonical list of all companions
- `companions/` — directory of per-runtime companion YAML profiles
  - `companions/hermes-companion.yaml`
  - `companions/openclaw-companion.yaml`
  - `companions/chaser_agent-companion.yaml`

**`05_TEMPLATES/` additions:**
- `Agent-Companion-Profile-Template.md`

**`07_LOGS/` additions:**
- `Conversations/` — persistent conversation history directory

---

## 7. Phase 11 Dependencies on Phase 10

Phase 11 cannot begin until the following Phase 10 items are stable:

| Dependency | Why Required | Status |
|---|---|---|
| PyWebView shell with sidebar + panel system | Phase 11 chat panel mounts as `#panel-chat` | DONE |
| `StudioAPI` bridge pattern | Phase 11 extends this class with chat methods | DONE |
| `StudioService` write governance | All Phase 11 write proposals must route here | DONE |
| Approval modal (`ApprovalModal`) | Phase 11 reuses approval modal for proposal approval | DONE |
| Agent Bus (`bus.py`) public API | Companion status reads heartbeats; runtime control dispatches tasks | DONE |
| `aor_pipeline_monitor.py` | Dashboard queries and AOR run status in chat | DONE |
| File watcher (`file_watcher.py`) | Chat can be notified when relevant files change | DONE |
| Companion registry (new — Phase 10 final pass) | Must exist before Phase 11 chat references companions | NOT DONE |
| RPGL provider governance (`runtime/policy/`) | Model/provider router depends on RPGL for health/fallback | PARTIAL |
| `07_LOGS/Conversations/` directory | Created by first Phase 11 chat session, not pre-created | AUTO |

**Minimum Phase 10 completion before Phase 11 starts:**
- Passes 10J (AOR Monitor) and 10K (Schedule Manager) provide essential backend coverage for
  chat dashboard queries. Do not start Phase 11 chat router until at least 10J is live.
- The companion YAML schema (Section 7 above) must be defined and 3 starter profiles created
  as part of a pre-Phase-11 pass (can be Phase 10 Final or Phase 10S "companion seed pass").

---

## 8. Phase 11 Implementation Priority

**Phase 11 MVP (first implementation pass):**

1. **Chat panel HTML/JS/CSS** - BUILT READ-ONLY / CLOSED as native `#panel-chat`; renders route preview, provider readiness, native workspace/thread foundation, proposal preview, approval-handoff preflight, closeout evidence, and live-routing gate; no persistence or execution
2. **Intent/router contract (basic)** - BUILT READ-ONLY as deterministic contract; no LLM classifier
3. **Slash command preview** - BUILT READ-ONLY for known/unknown slash command posture; no command execution
4. **Proposal-card preview** - BUILT READ-ONLY for proposal intents; no approval queue writes
5. **Provider readiness in Chat** - BUILT READ-ONLY; no provider switching, live probe, or credential mutation
6. **Approval handoff queue contract** - BUILT READ-ONLY / CLOSED; previews future `StudioService.queue_for_approval` packet shape for proposal intents, denies queue writer, approval artifact write, approval execution, provider/runtime/browser dispatch, vault writes, and canonical mutation
7. **Post-closeout planning contract** - BUILT READ-ONLY / VERIFIED; maps remaining passes and selected conversation persistence approval contract as next, no new authority
8. **Conversation persistence approval contract** - BUILT READ-ONLY / VERIFIED; previews deterministic conversation-log target paths, source-message hashes, content digests, and future approval packet shape; no directory creation, Markdown write, approval artifact write, or queue write
9. **Approval queue write execution proof** - BUILT APPROVAL-GATED / VERIFIED; queues supported Chat proposal approval requests only with explicit confirmation; no target write, approval execution, provider/model call, runtime/browser dispatch, or canonical mutation
10. **Read-only slash command responses + native UI** - BUILT READ-ONLY / STATIC UI QA VERIFIED; `/dashboard`, `/map`, `/vault`, `/runtime status`, `/models`, `/provider`, `/log`, `/memory show`, and `/pet` produce bounded response cards rendered in native Chat while unknown/write/execution commands fail closed to help/boundary cards
11. **Native Chat workspace/thread foundation** - BUILT PARTIAL / READ-ONLY / VERIFIED; models Chat projects, folders, tabs, threads, runtime lanes, Discord transport posture, and proposal actions for thread creation, runtime board handoff, schedule management, and runtime setup without writing chat state or dispatching runtimes
12. **Native Chat workspace/folder/thread proposal writer** - BUILT PARTIAL / APPROVAL-GATED / VERIFIED; queues digest-bound Studio approval artifacts for workspace, folder, and runtime-thread proposals only, while target Chat state, Discord, Agent Bus, board, schedule, provider, and canonical writes remain blocked
6. **Companion status bar** — shows Hermes/OpenClaw/Chaser Agent status derived from bus heartbeats (read-only)
7. **`/map`, `/dashboard`, `/runtime status`** — read-only slash commands (lowest risk, highest value)
8. **`/pet` companion commands** — show companion status cards
9. **Companion profile seed** — Hermes, OpenClaw, Chaser Agent YAML profiles + registry

**Phase 11 post-closeout passes completed (2026-05-11):**
1. `phase11-chat-conversation-persistence-approval-contract` - COMPLETE / READ-ONLY / VERIFIED / CONVERSATION WRITES BLOCKED; defines and previews governed conversation-log target paths under `07_LOGS/Conversations/` before any live provider execution or Chat-originated approval queue writes.
2. `phase11-chat-approval-queue-write-execution-proof` - COMPLETE / APPROVAL-GATED / VERIFIED / LIVE EXECUTION BLOCKED; explicit operator-confirmed Chat proposal queue writes create pending approval artifacts only, duplicate queueing is idempotent, and execution remains blocked before target writes.
3. `phase11-chat-live-provider-execution-approval-preview` - COMPLETE / READ-ONLY / VERIFIED / PROVIDER CALLS BLOCKED; builds deterministic request digests, provider-readiness preflight, conversation-audit target preview, and future approval packet shape for model-bound Chat intents only; no provider/model call, approval artifact write, approval execution, conversation write, runtime/browser dispatch, Agent Bus task write, or canonical mutation.
4. `phase11-chat-runtime-dispatch-readiness-contract` - COMPLETE / READ-ONLY / VERIFIED / RUNTIME DISPATCH BLOCKED; previews runtime dispatch packets from runtime capabilities, Agent Bus read-only posture, AOR workflow registry, and Runtime Cockpit readiness without Agent Bus task writes or workflow/runtime execution.
5. `phase11-chat-browser-dispatch-readiness-contract` - COMPLETE / READ-ONLY / VERIFIED / BROWSER DISPATCH BLOCKED; previews browser dispatch packets from external Browser Use/Excalidraw readiness without browser launch, Browser Use CLI/CDP/MCP invocation, navigation, screenshot capture, or browser-run writes.
6. `phase11-chat-approval-consumption-readiness-contract` - COMPLETE / READ-ONLY / VERIFIED / APPROVAL CONSUMPTION BLOCKED; previews Chat approval consumption readiness without approval status mutation, exact-once marker write, approval execution, or target writes.
7. `phase11-chat-companion-status-ui-shell` - COMPLETE / READ-ONLY / VERIFIED / AUTHORITY NEUTRAL; renders Hermes/OpenClaw/Chaser Agent companion status without runtime control, identity mutation, profile writes, role-card mutation, provider calls, Agent Bus writes, or canonical mutation.
8. `phase11-chat-companion-selection-approval-preview` - COMPLETE / APPROVAL-PREVIEW ONLY / VERIFIED / SELECTION WRITES BLOCKED; previews digest-bound companion selection approval packets without approval artifact writes or companion selection target mutation.
9. `phase11-chat-companion-selection-queue-write-readiness` - COMPLETE / QUEUE-WRITE-READINESS / VERIFIED / QUEUE WRITES BLOCKED; previews exact queue-write packet metadata and required digest match without writing approval artifacts or companion selection state.
10. `phase11-chat-companion-selection-queue-write-execution-proof` - COMPLETE / APPROVAL-GATED / VERIFIED / TARGET WRITE BLOCKED; writes pending companion-selection approval artifacts only with exact digest match and blocks duplicate digest writes, approval execution, and companion selection target mutation.
11. `phase11-chat-companion-selection-approval-consumption-readiness` - COMPLETE / READ-ONLY / VERIFIED / SELECTION WRITE BLOCKED; validates companion-selection approval artifacts, previews exact-once marker and consumption digest material, blocks mismatch/missing approval paths, and keeps approval status mutation, marker writes, approval execution, and target writes disabled.
12. `phase11-chat-readonly-slash-command-responses` - COMPLETE / READ-ONLY / VERIFIED / NO COMMAND EXECUTION; renders bounded cards for safe slash commands and blocks unknown/write/execution slash commands without provider/model calls, runtime/browser dispatch, approval action, Agent Bus task writes, vault writes, graph/node writes, or canonical mutation.
13. `phase11-chat-readonly-slash-command-response-ui` - COMPLETE / STATIC UI QA VERIFIED / NO COMMAND EXECUTION; renders the verified read-only slash response cards in native Chat and exposes blocked authority posture without adding command execution, provider/model calls, runtime/browser dispatch, approval actions, vault writes, Agent Bus task writes, or canonical mutation.
14. `phase11-chat-readonly-card-visual-qa` - COMPLETE / VISUAL QA VERIFIED / NO COMMAND EXECUTION; renders static HTML evidence and a governed loopback screenshot proof for the read-only slash response cards without adding command execution.
15. `phase11-chat-no-hitl-feature-family-selection-audit` - COMPLETE / READ-ONLY / VERIFIED / NO-HITL SELECTION AUDIT; selected `phase11-chat-readonly-slash-command-catalog-audit` as the next safe no-human-in-loop pass and deferred executor/live/target-mutation lanes.
16. `phase11-chat-readonly-slash-command-catalog-audit` - COMPLETE / READ-ONLY / VERIFIED / SLASH COMMAND CATALOG AUDIT; covers supported read-only slash commands, blocks write/execution/unknown commands, corrects `/vault` and `/log` router catalog coverage, and advances the no-HITL lane without command execution.
17. `phase11-chat-readonly-operator-dashboard-aggregate-audit` - COMPLETE / READ-ONLY / VERIFIED / OPERATOR DASHBOARD AGGREGATE AUDIT; covers dashboard summary, approval center, provider readiness, runtime status, companion status, recent build logs, and slash catalog sources while preserving no command execution.
18. `phase11-chat-no-hitl-lane-completion-audit` - COMPLETE / READ-ONLY / VERIFIED / NO-HITL LANE COMPLETION AUDIT; verified the completed no-HITL/read-only artifact trail, confirmed build/history/daily/activity index coverage, found zero remaining eligible no-HITL candidates, and moved the next marker to `operator-selected-governed-executor-or-deferred-closeout`.
19. `operator-selected-governed-executor-or-deferred-closeout` - COMPLETE / READ-ONLY / VERIFIED / OPERATOR HANDOFF READY; verified zero substantial autonomous Phase 11 development passes remain, listed the then-open operator-governed/deferred lanes after companion-selection consumption, kept implementation authority false, and moved the marker to `operator-action-required-no-autonomous-phase11-pass`.
20. `operator-action-required-no-autonomous-phase11-pass` - COMPLETE / READ-ONLY / VERIFIED / OPERATOR DECISION REQUIRED; verified zero autonomous Phase 11 passes remain, exposed unselected governed-lane/defer decisions, kept implementation authority false, and moved the next action to `operator-select-governed-executor-lane-or-defer-closeout`.
21. `studio-runtime-chat-workspaces-foundation` - PARTIAL / READ-ONLY / VERIFIED / PRODUCT-SHAPE FOUNDATION; added native Studio Chat workspace/thread/runtime-lane modeling and UI rendering while preserving no conversation persistence, thread creation, message send, Discord API call, Agent Bus task write, runtime board mutation, schedule mutation, provider/model call, approval consumption, credential exposure, or canonical mutation.
22. `studio-runtime-chat-workspace-proposal-writer` - PARTIAL / APPROVAL-GATED / VERIFIED / TARGET WRITES BLOCKED; added digest-bound Studio Chat workspace/folder/thread proposal approval artifacts and fail-closed ambient execution blocking while preserving no Chat state write, Discord API call/thread creation, message send, Agent Bus task write, runtime board mutation, schedule mutation, provider/model call, approval consumption, credential exposure, or canonical mutation.
23. `phase11-chat-companion-selection-approval-consumption-executor` - COMPLETE / APPROVAL-CONSUMED / VERIFIED / COMPANION SELECTION WRITTEN; consumed one approved companion-selection approval, wrote the exact-once marker and `runtime/studio/chat/companion-selection.json`, blocked duplicate execution before target rewrite, and preserved no provider/model call, runtime/browser dispatch, Agent Bus task write, identity/profile/role-card mutation, broad approval execution, or canonical writeback.
24. `phase11-chat-runtime-dispatch-executor` - COMPLETE / APPROVAL-CONSUMED / VERIFIED / AGENT BUS TASK ENQUEUED; consumed one approved runtime-dispatch approval, wrote open Agent Bus task `chat-runtime-dispatch-ec40d576ce3940c3b3d2` for `Codex` with `write_policy=none`, blocked duplicate execution before a second task write, and preserved no task claim, runtime process start, workflow dispatch, provider/model call, browser control, target mutation, Gate/Git/host mutation, or canonical writeback.
25. `studio-chat-schedule-proposal-consumption` - PARTIAL / APPROVAL-CONSUMED / VERIFIED / STAGED SCHEDULE PROPOSAL RECORDED; consumed digest-bound Studio Chat schedule proposal approvals into `runtime/studio/chat/schedule-proposals/` with exact-once marker/audit evidence and preserved no `runtime/schedules/*.yaml` write, schedule-index regeneration, schedule enablement, OpenClaw/Hermes cron mutation, Agent Bus task write, runtime/workflow dispatch, Discord/API provider call, credential read, or canonical writeback.
26. `studio-chat-approved-schedule-adapter-export-packet-writer` - PARTIAL / APPROVAL-CONSUMED / VERIFIED / LOCAL ADAPTER EXPORT PACKET WRITTEN; consumed digest-bound Studio Chat adapter export approvals into `runtime/studio/chat/schedule-adapter-exports/` with exact-once marker/audit evidence and preserved no external scheduler mutation, OpenClaw/Hermes cron mutation, Agent Bus task write, runtime/workflow dispatch, Discord/API provider call, credential read, or broader canonical writeback.
27. `studio-chat-full-authority-manual-test-orchestrator` - COMPLETE / TARGETED VERIFIED / MANUAL UI TEST READY; added digest-plus-operator-statement gated provider execution, Hermes/main-runtime Agent Bus dispatch, Discord-control runtime handoff, cron-control runtime handoff, and Agent Bus readback while preserving no raw credential display, direct Discord API call from Studio, direct external cron mutation, runtime task claim from Studio, conversation transcript persistence, or canonical mutation.

**Phase 11 later post-closeout passes:**
1. `operator-select-governed-executor-lane-or-defer-closeout` - OPERATOR DECISION REQUIRED; no autonomous no-HITL pass remains, so the operator must explicitly select the next governed executor/live/target-mutation lane or defer closeout.
2. Broader Chat/runtime/browser completion - future; browser dispatch, approval target mutation beyond the companion-selection proof, runtime task claim/result/canonical writeback, conversation persistence, and unrelated target writes remain deferred. Provider execution exists only through the new digest/statement-gated executor.

**Historical Phase 11 Pass 2 sketch (superseded by post-closeout plan):**
1. `project-create` intent → creation packet → approval modal
2. `vault-node-create` intent → node proposal → approval
3. `/new-project` slash command wired end-to-end
4. `/run [workflow]` slash command → AOR dispatch approval
5. `/approve` and `/reject` slash commands → inline approval action
6. Conversation persistence to `07_LOGS/Conversations/`

**Phase 11 Pass 3 (model routing + memory):**
1. Provider router UI — model selector dropdown + credential status
2. Multi-model chat with Anthropic lane (already live behind API)
3. `/memory save` → memory class selection → approval
4. R&D entry proposals from chat (`rnd-entry` intent)

**Phase 11 Pass 4 (browser-use + advanced runtime control):**
1. `/browser open [url]` → Browser Operator dispatch + result display
2. `/agent hermes [command]` → Agent Bus task creation (approval required)
3. Hermes chat lane — route messages directly to Hermes via bus task

**Phase 11 Pass 5 (AI companion personas + full slash surface):**
1. Companion persona in chat responses (Hermes speaks in its style)
2. `/companion hermes chat` → session routed through Hermes runtime lane
3. Remaining slash commands
4. Cross-session conversation history search

---

## 9. What Is NOT Phase 11

Do not introduce these in any Phase 11 pass:

- Browser profiles, cookies, saved credentials, or persistent OAuth sessions
- Computer-use / OS-level automation (files/system/OS control requires separate architecture)
- Model fine-tuning, RLHF, or weight-level memory updates
- ChaseOS forking or re-architecture based on chat output
- Auto-modification of protected files (SOUL.md, Principles.md, Assistant-Contract.md, etc.)
- Autonomous project creation without operator approval
- Silent canonical promotion from chat content
- Chat interface with higher permissions than CLI
- "Smart contracts" or automated financial execution from chat
- Credential display in the chat UI
- Public-facing chat endpoints (ChaseOS Chat is local-first for V1)
- Direct model API calls from JS (all model calls go through the Python bridge)

---

## 10. ChaseOS Chat v1 Definition of Done

Phase 11 is complete when:

- [ ] Chat panel mounts in the Studio shell with persistent message history
- [ ] Companion status bar shows Hermes, OpenClaw, Chaser Agent with live heartbeat data
- [ ] Slash commands: `/map`, `/dashboard`, `/run`, `/approve`, `/reject`, `/pet` all working
- [ ] Intent classification routes at minimum: `chat-answer`, `project-create`, `vault-node-create`, `approval-action`
- [ ] Project creation proposal generated and approved creates actual vault file via `StudioService`
- [ ] One model provider lane (Anthropic) used for `chat-answer` responses
- [ ] `/new-project` creates a proposal that can be approved end-to-end
- [ ] Conversation saved to `07_LOGS/Conversations/` per session
- [ ] All write actions routed through `StudioService` with audit records
- [ ] No write bypasses Gate or approval gate
- [ ] Companion profiles for Hermes, OpenClaw, Chaser Agent exist in YAML
- [ ] Prompt injection guard active for all user input
- [ ] `07_LOGS/Agent-Activity/` event written for every runtime dispatch from chat

---

## 11. Cross-Runtime Rules

These rules apply to all runtimes (Chaser Agent, Hermes, OpenClaw) during Phase 10 completion and Phase 11 implementation.

1. **Read this document before starting any pass.** If something in this document is wrong or
   outdated, update it before building on incorrect assumptions.

2. **Do not add Phase 11 features during Phase 10 passes.** The line is the Panel architecture.
   If you are adding a panel, you are in Phase 10. If you are adding a chat router, companion system,
   or slash command infrastructure, you are in Phase 11.

3. **Update the Phase 10 tracker after every pass.** `06_AGENTS/ChaseOS-Studio-Phase10-Implementation-Tracker.md`
   is the canonical Phase 10 state. Append a row after each completed pass.

4. **Follow the test target guidelines.** Each panel pass targets 30–55 tests covering API,
   HTML, CSS, and JS layers. Do not ship a panel pass without hitting the test target.

5. **Writeback discipline is mandatory.** Every pass must produce: build log in
   `07_LOGS/Build-Logs/`, archive note in `99_ARCHIVE/Documentation-History/`, both indexes
   updated. No exceptions — this is in the Assistant-Contract.

6. **The companion system does not grant authority.** Any runtime implementing companion
   features must verify this invariant: the companion profile can be changed without changing
   the trust tier, permission ceiling, or any behavior-governing policy. If these are coupled,
   the implementation is wrong.

7. **Chat input is untrusted.** All user chat input must be treated as untrusted per
   `04_SOPS/Untrusted-Input-Handling-SOP.md`. Embedded instructions in pasted content must be
   flagged and surfaced to the operator before execution.

8. **Proposals are not executions.** A proposal generated by the router is a draft. It does not
   write anything until the operator approves. Never auto-approve.

9. **Model calls require attribution.** Every AI-generated response surfaced in the chat UI must
   be attributed: which model/provider produced it. No anonymous AI output in the chat.

10. **Skill activation is still quarantine-first.** Any AI-generated output that could become
    a ChaseOS skill, workflow, or SOP must enter quarantine first. The chat surface does not
    create trusted skills directly.

---

*Graph links: [[ChaseOS-Studio-Architecture]] · [[Workspace-Mode-Layer-Feature-Family]] · [[Phase10-Desktop-Shell-Engineering-Plan]] · [[ChaseOS-Studio-Phase10-Implementation-Tracker]] · [[Agent-Control-Plane]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Agent-Registry]] · [[Autonomous-Operator-Runtime]] · [[Agent-Memory-Architecture]] · [[Feature-Fit-Register]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Chaser-Agent-Runtime-Profile]]*

*ChaseOS Phase 11 Architecture — v1.0 | Created: 2026-05-06 | Author: Chaser Agent*
*This is the canonical planning document for Phase 11. Update it when architecture decisions change.*
*Do not split this document without creating a clear primary anchor that all runtimes can find.*


**2026-05-13 companion layer v0.1 note:** The core companion layer is now implemented under `runtime/companion/` with [[Companion-Behavior-Policy]], [[Companion-Roster]], and [[Companion-Profile-Template]]. It supports Hermes/OpenClaw/Chaser Agent profile validation, read-only switch preview, approval-flag-gated active selection, and switch-ledger entries while preserving no runtime routing, provider/model, memory, permission, tool, connector, protected-file, workflow, Agent Bus, or canonical authority changes. This does not build Studio UI or avatar assets.

**2026-05-13 companion runtime core adapter sync note:** Studio companion status, registry readiness, roster preview, and companion-selection approval preview now consume `runtime/companion` as the source of truth for Hermes/OpenClaw/Chaser Agent metadata, profile validation, visual marks, descriptive stats, and the shared selection target path. This closes the drift where Studio companion panels carried their own metadata and where the core package depended back on Studio status code. The pass is read-only and authority-neutral: no companion memory, provider/model routing, runtime/browser dispatch, Agent Bus task write, permission change, profile/role-card mutation, protected-file access, approval execution broadening, or canonical mutation was added. Next recommended pass is `phase11-companion-memory-boundary-contract`.
