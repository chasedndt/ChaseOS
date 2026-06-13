# Terminal Workbench + ChaserAgent + Hermes-Inspired Studio Feature Matrix

Date: 2026-06-02
Runtime: Hermes/Optimus
Source handoff: [[ChaseOS_Terminal_ChaserAgent_Fullstack_Implementation_Handoff_v2]]
Status: TRACKING MATRIX / SCOPE INTEGRATION

This matrix preserves the handoff's Hermes-video-derived feature families so they are not lost. It is not a completion claim. Status values: `existing`, `partial`, `planned`, `deferred`, `rejected`.

## Pass truth

- Exact handoff read: `06_AGENTS/ChaseOS_Terminal_ChaserAgent_Fullstack_Implementation_Handoff_v2.md`.
- `runtime/operator_surface/adapters/terminal_adapter.py` was a documented STUB before the 2026-06-02 pass and is a PARTIAL bounded MVP scaffold (9 tests).
- `chaseos operate terminal policy|preview|run|history|show` is wired; `chaseos session export` is not wired in CLI yet.
- Studio Terminal Workbench frontend preview/history/detail mount, read-only terminal run-detail hardening, session metadata lifecycle, Studio chat -> SessionRecord export adapter/CLI, Chaser read-only board state, pre-N6 terminal command proposal packets, the N6A terminal write approval-request queue front half, the N6R terminal write executor-readiness contract, the initial N6 gated CLI executor, the N7 internal gateway ingress facade, the N8 terminal authority audit, the N9 approved `touch` file-create lane, the N10 approved `copy`/`cp` file-copy lane, the N11 Studio Chaser Board read-only dashboard, the N12 source-rendered Chaser Board visual QA proof, the N13 packaged visual QA harness, the N14 packaged route rebuild/reproof, the N15 Chaser runtime readiness review, the N16 Chaser runtime activation gate design, the N17 Chaser runtime activation approval preview, the N18 Chaser runtime activation approval request write gate, the N19 Chaser runtime activation approval decision preflight, the N20 Chaser runtime activation approval consumption design, the N21 Chaser runtime activation approval consumption write guard, the N22 Chaser runtime activation post-consumption readiness readback, the N23 Chaser runtime activation executor design, the N24 Chaser runtime activation executor write guard, the N25 Chaser runtime activation state readiness readback, the N26 Chaser runtime profile/toolset activation design, the N27 Chaser runtime profile/toolset activation write guard, the N28 Chaser runtime profile/toolset activation readiness validator, the N29 Studio full terminal product contract, and the human Studio terminal foundation are built/verified for their scoped lanes. ChaserAgent live execution, Chaser terminal binding, network-served/external gateway ingress, Agent Bus mutation from the gateway/Studio, full Artifacts Hub, Toolsets Manager, and complete Profiles Manager remain planned.

### 2026-06-08 Full Studio terminal foundation update

- **Human terminal mounted:** `#/terminal` is a real Studio panel with session list, output viewport, input, stop/terminate/clear controls, slash suggestions, and Workbench navigation.
- **Session backend built:** `runtime/studio/terminal_sessions.py` implements safe IDs, workspace-scoped cwd, async command output polling, interrupt/terminate/close lifecycle, Tier 4 output handling, and JSONL audit under `07_LOGS/Terminal-Sessions/`.
- **Registries built:** slash commands and preview-only agent launchers live in `runtime/studio/terminal_slash_commands.py` and `runtime/studio/terminal_agent_launchers.py`.
- **Boundary:** human Studio terminal execution is allowed only in the operator-controlled lane. Terminal Workbench remains read-only; ChaserAgent terminal binding, terminal-to-Chaser adapter, Agent Bus mutation, provider dispatch, approval consumption, and canonical mutation remain blocked.

### 2026-06-08 N29 Studio full terminal product contract update

- **Studio full terminal contract built:** `runtime/studio/terminal_product_contract.py` defines the human Studio full terminal lanes, policy modes, future session backend APIs, UI contract, slash-command registry, agent launcher registry, and audit/history/replay contract.
- **CLI/API wired:** `chaseos studio terminal-product-contract --json` and `StudioAPI.get_studio_terminal_product_contract()` expose read-only contract readback.
- **Superseded by full terminal foundation:** `#/terminal` is now mounted as operator-control with session APIs; Chaser binding remains deferred.
- **Chaser boundary corrected:** Chaser terminal binding is now explicitly deferred until the human Studio terminal foundation exists.
- **Authority boundary:** no Studio execution, no PTY/session process, no write-capable Studio terminal lane, no ChaserAgent terminal binding, no Agent Bus mutation, no provider call, no approval consumption, and no canonical mutation.
- **Next:** `terminal-n30-terminal-session-backend-pty`.

### 2026-06-03 foothold update

- `runtime/chaser/` core package created (ChaserAgent-inside-core): `__init__.py`, `models.py`, `sessions.py`, `exports.py`, `tests/test_session_export.py` (14 tests).
- Session export backend is now implemented (markdown + json) with mandatory secret redaction, artifact/tool-run/terminal-run manifests, an on-disk export audit record, and an explicit `external_upload_performed=False` flag. No network I/O, no command execution.
- At that point, `agent.py`, `board.py`, `policies.py`, `profiles.py`, `toolsets.py`, `artifacts.py`, and the `chaseos session export` CLI remained planned. The Phase A core modules were later added on 2026-06-06 as no-authority preview contracts.

### 2026-06-03 update B (terminal CLI + Studio workbench backend + Chaser Gateway docs)

- **CLI terminal wired:** `chaseos operate terminal policy|preview|run|history` (`runtime/cli/main.py` + `runtime/operator_surface/terminal/operator.py`). Read-only; `run` blocks non-allowlisted commands at exit code 3.
- **Run-audit persistence:** `runtime/operator_surface/terminal_runs.py` â†’ `07_LOGS/Terminal-Runs/`. `TerminalAdapter` registered in `adapter_registry`.
- **Studio Terminal Workbench backend:** `runtime/studio/terminal_workbench.py` + `StudioAPI.get_terminal_workbench()` - read-only (policy + no-execution preview + run history).
- **New architecture docs:** `Chaser-Gateway-Architecture.md` (maps the Hermes/OpenClaw reverse-engineering books + diagrams onto ChaseOS; defines the Chaser Gateway Diagnostic), `ChaserAgent-Moat.md`, `board-py-Integration-Deep-Dive.md`, `Terminal-ChaserAgent-Agent-Bus-Handover.md` (living handover for bus runtimes).
- Tests: terminal_runs (8), terminal_operator (8), terminal_workbench (6).

### 2026-06-05 frontend mount update

- **Studio Terminal Workbench frontend mounted:** `#/terminal-workbench` nav/panel is live in `runtime/studio/shell/frontend/index.html`.
- **Preview/history only:** `app.js` calls `get_terminal_workbench(command, 20)` and renders policy, no-execution preview, warnings, and run history.
- **No execute button:** frontend tests verify the panel exposes only `terminal-workbench-preview-btn` and does not call run/execute APIs.
- Tests: terminal workbench backend + frontend (10), terminal operator surface regression (24), CLI policy smoke, and shell collect-only (2505 collected under isolated Python 3.14).

### 2026-06-06 ChaserAgent Phase A core foundation update

- `runtime/chaser/agent.py`, `board.py`, `policies.py`, `profiles.py`, `memory.py`, `toolsets.py`, and `artifacts.py` are now implemented as no-authority preview/contract modules.
- The new modules produce in-memory task previews, board cards, policy snapshots, profile/toolset views, memory-boundary previews, and artifact manifests only.
- They do not activate ChaserAgent, claim/write Agent Bus tasks, call providers, execute tools/shell, write memory, or mutate canonical state.
- Tests: `runtime/chaser/tests` now has 37 focused tests passing; companion persistence parity passes under isolated Python 3.14.

### 2026-06-06 session lifecycle update

- **N3 session metadata lifecycle built:** `runtime/chaser/sessions.py` now exposes audited `set_session_pinned`, `rename_session`, and `archive_session`.
- **Payload/path guard:** session reads reject records whose internal `session_id` does not match the safe path id.
- **Archive-first delete:** `archive_session` moves the active JSON into `_archive/<YYYY-MM-DD>/` and writes `_audit/` evidence. It performs no hard delete.
- **Authority boundary:** lifecycle writes are metadata/operator-state writes only. No terminal execution, provider call, Agent Bus write, memory write, or canonical truth mutation is added.
- Tests: session/export lifecycle focused suite (24), full chaser tests (38), Terminal/N2 regression (34), and `compileall runtime/chaser`.

### 2026-06-06 terminal read-only hardening update

- **Terminal run detail readback built:** `runtime/operator_surface/terminal_runs.py` now exposes safe detail loading for recorded run audit JSON, rejecting unsafe run ids and returning compact missing/unsafe error shapes.
- **CLI show built:** `chaseos operate terminal show <run_id> --json` reads an existing audit record only. It does not execute commands or consume approvals.
- **Studio readback built:** `get_terminal_workbench` now includes policy defaults, audit root/status, richer recent-run metadata, and an explicit run-detail contract. `StudioAPI.get_terminal_run_detail(run_id)` exposes read-only detail data.
- **Frontend detail ergonomics built:** selected history runs display command, cwd, classification, policy, exit, duration, stdout/stderr excerpts, redaction/truncation flags, audit paths, and a Tier 4 warning. Non-executing actions are select run, copy run id/command, and preview the selected history command through the existing Preview flow.
- **Authority boundary:** no Studio execution, no write-capable terminal lane, no ChaserAgent terminal adapter, no provider calls, no Agent Bus writes, no approval consumption, and no canonical mutation.
- Tests: Terminal/Studio focused suite (42), `compileall runtime/operator_surface runtime/studio`, CLI show smoke, and frontend JS syntax check.

### 2026-06-06 N4 chat-to-SessionRecord export adapter update

- **Studio chat export adapter built:** `runtime/chaser/chat_session_adapter.py` safely loads existing Studio chat native-state conversations and converts them into Chaser `SessionRecord` objects.
- **Terminal audit references supported:** optional `--terminal-run RUN_ID` attachments are loaded through safe terminal run-detail readback and preserved as Tier 4 terminal evidence in the exported session manifest.
- **CLI export-chat wired:** `chaseos chaser session export-chat <thread_id> --format markdown|json [--terminal-run RUN_ID] --json` writes a redacted local Chaser session export/audit without executing anything.
- **Authority boundary:** no Studio execution, no terminal execution, no ChaserAgent runtime wiring, no provider calls, no Agent Bus writes, no approval consumption, no canonical memory write, and no external upload.
- Tests: N4 adapter/CLI focused suite (31), `compileall runtime/chaser runtime/cli`.

### 2026-06-06 N5 Chaser board read-only orchestration update

- **Board state built:** `runtime/chaser/board.py` now exposes `build_board_state()` as a fail-open read-only aggregator for terminal runs, Studio pending approvals, already-initialized Agent Bus tasks/heartbeats, schedules, and Chaser Gateway Diagnostic state.
- **CLI/API wired:** `chaseos chaser board state --json` and `StudioAPI.get_chaser_board_state(limit=8)` expose the board state contract.
- **No bus materialization:** if the Agent Bus DB does not exist, the board reports `agent_bus:not_initialized` and does not create storage.
- **Authority boundary:** no terminal execution, Studio execution, provider calls, Agent Bus writes, approval queue writes, approval consumption, canonical writeback, external upload, host mutation, profile activation, or toolset activation.
- Tests: N5 board/CLI/API focused suite (14), `compileall runtime/chaser runtime/cli runtime/studio/shell/api.py runtime/studio/test_chaser_board_state.py`.

### 2026-06-06 pre-N6 board proposal packet update

- **Proposal packets built:** `runtime/chaser/board.py` now exposes `build_action_proposal()` for terminal command proposal/readiness packets.
- **CLI/API wired:** `chaseos chaser board propose terminal-command <command> --json` and `StudioAPI.get_chaser_board_action_proposal(...)` return non-executing proposal packets.
- **Policy posture:** read-only commands return `preview_allowed`; write commands return `approval_required_future_n6`; shell-control/destructive/elevated/network/unknown and out-of-vault cwd proposals block.
- **Authority boundary:** no terminal execution, no Studio execution, no approval queue write, no approval consumption, no Agent Bus write, no provider call, no canonical writeback, no external upload, and no ChaserAgent runtime wiring.
- Tests: focused pre-N6 board/CLI/API suite (19), `compileall runtime/chaser runtime/cli runtime/studio/shell/api.py runtime/studio/test_chaser_board_state.py`.

### 2026-06-06 N6A terminal write approval-request update

- **Approval request front half built:** `runtime/chaser/board.py` now exposes `build_terminal_write_approval_request()` for N6 terminal write approvals.
- **CLI/API wired:** `chaseos chaser board request-terminal-approval <command> --json` previews by default and queues a pending Studio approval only with explicit `--write-approval-request`; `StudioAPI.request_chaser_terminal_write_approval(...)` mirrors the same preview/write split.
- **Eligibility:** only `write_command` / `approval_required_future_n6` proposals can be queued. Read-only, shell-control, destructive, elevated, network, unknown, and out-of-vault cwd proposals block.
- **Ambient execution blocked:** `StudioService.execute_approved()` now rejects approvals with `terminal_write_lane_approval_request=True`, so these requests cannot be consumed by generic Studio approval execution.
- **Authority boundary:** no terminal execution, no Studio execution button, no approval consumption, no Agent Bus write, no provider call, no canonical writeback, no external upload, no ChaserAgent runtime wiring.
- Tests: focused N6A board/CLI/API suite (20), Chaser core + board/CLI/API regression (28), compileall over touched runtime surfaces.

### 2026-06-06 N6R terminal write executor-readiness update

- **Readiness contract built:** `runtime/chaser/terminal_write_executor_readiness.py` validates terminal write approval requests for the dedicated N6 executor without consuming approvals or executing commands.
- **CLI/API wired:** `chaseos chaser board terminal-executor-readiness <approval_id> --json` and `StudioAPI.get_chaser_terminal_write_executor_readiness(...)` inspect approval status, terminal-write metadata, fresh proposal classification, proposal id, target path, cwd, authority flags, and exact-once marker absence.
- **Policy posture:** pending/non-approved approvals block; structurally valid approved approvals report `ready_for_executor`, `ready_for_future_executor_after_review=true`, `terminal_write_executor_implemented=true`, and `ready_for_execution_now=true`.
- **Authority boundary:** no terminal execution, no terminal audit write, no exact-once marker write, no approval consumption, no Studio execution, no Agent Bus write, no provider call, no canonical writeback, no external upload, and no ChaserAgent runtime wiring.
- Tests: focused N6R board/CLI/API suite (27), Chaser core + board/CLI/API regression (35), compileall over touched runtime surfaces, and temp-vault CLI smoke.

### 2026-06-06 N6 terminal write gated executor update

- **Dedicated CLI executor built:** `runtime/chaser/terminal_write_executor.py` consumes approved terminal write approvals through `chaseos chaser board execute-terminal-approval <approval_id> --confirm-approved-terminal-write --json`.
- **Policy posture:** exact approval/proposal match, approved status, terminal-write metadata, fresh classification, explicit confirmation, existing in-vault cwd, in-vault target, and absent exact-once marker are required before mutation. The initial supported write verb is only `mkdir <target>`.
- **Authority boundary:** this pass adds bounded approval consumption, exact-once marker write, terminal run audit write, and approved in-vault host mutation for the narrow CLI lane only. It does not add Studio execution, unrestricted shell, shell operators, elevation, Agent Bus writes, provider calls, canonical writeback, external upload, or ChaserAgent runtime wiring.
- Tests: focused N6 board/CLI/API suite (34), adjacent terminal/operator regression (70), compileall over touched runtime surfaces, and temp-vault CLI smoke with duplicate blocking.

### 2026-06-06 N7 gateway ingress update

- **Internal ingress facade built:** `runtime/chaser/gateway.py` exposes `build_gateway_ingress_contract()` and `handle_gateway_ingress()` as a structured, fail-closed internal facade. It is not a network server.
- **CLI/API wired:** `chaseos chaser gateway ingress <intent> --payload-json ... --confirm-local-operator --json` routes board state, terminal proposals, terminal approval preview/write, executor readiness, and the existing N6 executor. `StudioAPI.get_chaser_gateway_ingress_contract()` exposes read-only contract metadata only.
- **Policy posture:** every ingress route requires local-operator confirmation; approval queue writes additionally require approval-queue confirmation; terminal execution additionally requires approved-terminal-write confirmation and still delegates to N6 exact approval/proposal/scope/marker checks.
- **Authority boundary:** no Studio execution, frontend execute button, network gateway server, Agent Bus task write, provider call, canonical writeback, external upload, ChaserAgent runtime/profile/toolset activation, unrestricted shell, shell operators, or elevation. Gateway payloads and terminal output remain Tier 4 untrusted.
- Tests: focused N7 gateway/CLI/API suite (14), adjacent Chaser + terminal/operator regression (79), Terminal Workbench read-only backend/frontend regression (14), and compileall over touched runtime surfaces.

### 2026-06-06 N8 terminal authority audit update

- **Authority audit built:** `runtime/chaser/terminal_authority_audit.py` returns a deterministic read-only proof packet across Terminal Workbench, Chaser board, N7 gateway ingress, N6 readiness/executor denial paths, TerminalAdapter unsafe-command classification, and Studio API method exposure.
- **CLI/API wired:** `chaseos chaser terminal authority-audit --json` and `StudioAPI.get_chaser_terminal_authority_audit()` expose the audit packet.
- **Policy posture:** the audit exercises preview/blocked paths only and snapshots approval files, exact-once markers, terminal run audit files, Agent Bus files, and the probe target before/after.
- **Authority boundary:** no Studio execution, terminal execution, approval queue write, approval consumption, exact-once marker write, terminal audit write, Agent Bus write, provider call, canonical writeback, external upload, or host mutation.
- Tests: focused N8 audit/CLI/API suite (10), adjacent terminal/Chaser/Studio regression (89), and compileall over touched runtime surfaces.

### 2026-06-06 N9 approved file-create update

- **Approved file-create lane built:** the N6 executor now supports `touch <target>` as a second narrow approved write verb alongside `mkdir <target>`.
- **Policy posture:** exact approval/proposal match, approved status, terminal-write metadata, fresh classification, explicit confirmation, existing in-vault cwd, in-vault target, absent exact-once marker, and non-existing target are required before file creation. Missing parent directories fail after marker reservation and audit instead of silently creating parents.
- **Authority boundary:** no Studio execution, unrestricted shell, shell operators, elevation, network/destructive command lane, Agent Bus writes, provider calls, canonical writeback, external upload, ChaserAgent runtime/profile/toolset activation, or content-writing terminal lane.
- Tests: focused N9 board/CLI/gateway/API/audit suite (51), adjacent terminal/Chaser/Studio regression (93), and compileall over touched runtime surfaces.

### 2026-06-06 N10 approved file-copy update

- **Approved file-copy lane built:** the N6 executor now supports `copy <source> <target>` and `cp <source> <target>` alongside `mkdir <target>` and `touch <target>`.
- **Policy posture:** exact approval/proposal match, approved status, terminal-write metadata, fresh classification, explicit confirmation, existing in-vault cwd, existing in-vault source file, existing target parent, in-vault non-existing target, and absent exact-once marker are required before file copy. Copy does not create parents, overwrite files, read file content into output, or invoke a shell.
- **Authority boundary:** no Studio execution, unrestricted shell, shell operators, elevation, network/destructive command lane, Agent Bus writes, provider calls, canonical writeback, external upload, ChaserAgent runtime/profile/toolset activation, or arbitrary content-writing lane.
- Tests: focused N10 board/CLI/gateway/API/audit suite (55), adjacent terminal/Chaser/Studio regression (97), and compileall over touched runtime surfaces.

### 2026-06-06 N11 Studio Chaser Board read-only dashboard update

- **Studio dashboard built:** `#/chaser-board` is mounted as a read-only Studio shell panel over `StudioAPI.get_chaser_board_state()`.
- **Frontend readback:** The panel renders authority posture, card type/status counts, source readiness, status cards, selected-card detail, evidence paths, copy card/command actions, and a non-executing command preview handoff into Terminal Workbench.
- **Authority preserved:** No execute/run button, no terminal execution API, no approval request write/consume API, no Agent Bus write, no provider call, no canonical mutation, and no ChaserAgent runtime/profile/toolset activation.
- **Tests:** focused Chaser board frontend/backend/terminal workbench suite (52), adjacent terminal/Chaser/Studio regression (102), frontend JS syntax check, and compileall passed.

### 2026-06-06 N12 Chaser Board source visual QA update

- **Visual proof built:** `runtime/studio/chaser_board_product_visual_qa.py` verifies `#/chaser-board` through Playwright using a restricted pywebview bridge that allows only `get_chaser_board_state`.
- **Screenshot evidence:** desktop initial, desktop selected-card, and mobile responsive screenshots plus JSON/Markdown reports are written under `07_LOGS/Studio-Visual-QA/2026-06-06-terminal-n12-chaser-board-visual-qa/`.
- **Authority preserved:** The proof checks required read-only/Tier 4/authority copy, forbidden execution API copy absence, selected-card detail, restricted API calls, and false authority flags. It does not run packaged/native Studio and adds no Studio execution, terminal execution, approval writes/consumption, Agent Bus write, provider call, connector call, canonical mutation, or ChaserAgent live runtime wiring.
- **Tests:** focused visual/frontend/backend suite (21), adjacent terminal/Chaser/Studio regression (106), live visual QA `ok=true`, and compileall passed.

### 2026-06-06 N13 Chaser Board packaged visual QA update

- **Packaged proof harness built:** `runtime/studio/chaser_board_packaged_visual_qa.py` targets `#/chaser-board` through the existing packaged route visual QA runner.
- **Shared helper hardening:** packaged visual QA now supports route-specific allowed visible-copy terms so `dashboard` / `read-only` can remain valid governance copy on this page without weakening other routes.
- **Live result:** current `dist/studio/ChaseOS-Studio.exe` launched and captured a nonblank screenshot, but proof returned `PARTIAL` because route activation left `panel-dashboard` active and Chaser Board cards/detail/authority copy were not visible.
- **Rebuild result:** current-source PyInstaller rebuild attempt timed out; duplicate Python/PyInstaller build processes were stopped. The executable timestamp remained 2026-06-06 20:16.
- **Authority preserved:** no Studio execution, terminal execution, approval writes/consumption, Agent Bus write, provider/connector call, canonical mutation, installer/signing/startup work, or ChaserAgent live wiring was added.

### 2026-06-07 N14 packaged route rebuild recovery update

- **Stale package gap closed:** `dist/studio/ChaseOS-Studio.exe` was rebuilt from current source through `studio local-packaging-proof`; rebuilt SHA-256 `7786795cb0c6531ae6b959a982b1780c1c4c9bd9c8e6e43876679a6cfa34c5d6`.
- **Route diagnostics hardened:** packaged QA route activation now prefers the QA activator in QA mode and records panel/nav diagnostics.
- **Freshness proof added:** Chaser Board packaged QA reports whether source sentinels are newer than the executable.
- **Read-only authority interpreted correctly:** `Read only: available` is allowed, while terminal execution, Studio execution, approval consumption, Agent Bus writes, provider calls, and canonical writeback must remain blocked.
- **Live result:** final packaged/native proof returned `VERIFIED` with route `#/chaser-board`, 44 cards, selected detail, Tier 4/authority copy, no execution buttons, no forbidden execution API copy, no provider/secret copy, no terminal execution claim, and blockers `[]`.
- **Authority preserved:** no Studio execution, terminal execution from Studio, approval consumption, Agent Bus write, provider/connector call, canonical mutation, installer/signing/startup work, release promotion, store/mobile packaging, or ChaserAgent live runtime wiring was added.

### 2026-06-07 N15 Chaser runtime readiness review update

- **Readiness review built:** `runtime/chaser/runtime_readiness.py` validates the current no-authority Chaser runtime wiring posture before any live runtime activation.
- **CLI/API wired:** `chaseos chaser runtime readiness --json` and `StudioAPI.get_chaser_runtime_readiness()` expose the report.
- **Policy posture:** the report validates Phase A policy, board authority, gateway contract, N8 terminal authority audit, descriptive-only profiles, and non-executing toolsets. It returns `live_runtime_ready=false` and names required blockers/gates for runtime adapter installation, profile/toolset activation, terminal-toolset binding, Agent Bus mutation, provider dispatch, external gateway ingress, and live runtime activation approval.
- **N8 hardening:** the terminal authority audit now falls back to source-text Studio API inspection when recovered CPython 3.14 bytecode cannot import under default Python.
- **Authority preserved:** no ChaserAgent runtime activation, no terminal-to-Chaser adapter, no Studio execution, no terminal execution, no approval write/consumption, no Agent Bus write/claim/update, no provider call, no external network call, no canonical mutation, and no host mutation was added.

### 2026-06-07 N16 Chaser runtime activation gate design update

- **Gate design built:** `runtime/chaser/runtime_activation_gate.py` now defines the future activation gate contract before any ChaserAgent runtime/profile/toolset activation can exist.
- **CLI/API wired:** `chaseos chaser runtime activation-gate-design --json` and `StudioAPI.get_chaser_runtime_activation_gate_design(...)` expose the read-only design.
- **Policy posture:** the design validates requested profile/toolset ids, depends on N15 readiness, defines future activation approval request fields, evidence references, exact-once marker expectations, operator-confirmation expectations, gate phases, and terminal-binding constraints.
- **Default live result:** `ops` + `terminal-preview` returns `design_ready_no_activation`, `ready_for_activation_now=false`, `activation_request_write_available=false`, and `activation_approval_consumption_available=false`.
- **Authority preserved:** no ChaserAgent runtime activation, no profile/toolset activation, no terminal-to-Chaser binding, no Studio execution, no terminal execution, no approval queue write/consumption, no Agent Bus write/claim/update, no provider call, no external network call, no canonical mutation, and no host mutation was added.

### 2026-06-07 N17 Chaser runtime activation approval preview update

- **Approval preview built:** `runtime/chaser/runtime_activation_approval.py` now returns the preview-only activation approval request packet shape for a requested profile/toolset.
- **CLI/API wired:** `chaseos chaser runtime activation-approval-preview --json` and `StudioAPI.get_chaser_runtime_activation_approval_preview(...)` expose the read-only preview.
- **Policy posture:** the preview includes a deterministic preview id, evidence refs, authority ceiling, future approval metadata, N16 gate summary, terminal-binding contract, warnings, and blockers. Agent Bus mutation or provider dispatch requests are fail-closed and require separate future gates.
- **N8 hardening:** terminal authority audit snapshots now ignore Python bytecode cache churn while retaining real Agent Bus file drift detection, preventing import-cache creation from being misread as Agent Bus mutation.
- **Live result:** the live-vault CLI report returned `ok=true`, `preview_status=preview_ready_no_write`, `approval_request_written=false`, `ready_to_write_activation_request_now=false`, `activation_approval_consumption_available=false`, no blockers, and all authority flags false.
- **Authority preserved:** no ChaserAgent runtime activation, no profile/toolset activation, no terminal-to-Chaser binding, no Studio execution, no terminal execution, no approval queue write/consumption, no Agent Bus write/claim/update, no provider call, no external network call, no canonical mutation, and no host mutation was added.

### 2026-06-07 N18 Chaser runtime activation approval request write-gate update

- **Approval request writer built:** `runtime/chaser/runtime_activation_approval_request.py` now previews or queues the Chaser runtime activation approval request.
- **CLI/API wired:** `chaseos chaser runtime activation-approval-request --json` previews by default and queues only with explicit `--write-approval-request`; `StudioAPI.request_chaser_runtime_activation_approval(...)` mirrors the preview/write split.
- **Policy posture:** the writer composes the N17 preview, rejects Agent Bus mutation/provider dispatch requests, writes only pending Studio approvals, reuses duplicate pending requests by preview id, and blocks ambient `StudioService.execute_approved()` consumption through `chaser_runtime_activation_approval_request=True` metadata.
- **Live result:** live CLI wrote pending approval `7623ee52-ffff-411c-b11d-87d6b6f30e02` at `runtime/studio/approvals/7623ee52-ffff-411c-b11d-87d6b6f30e02.json`; the duplicate live write returned `existing_pending_activation_approval_request` and `duplicate_of_existing_pending=true`.
- **N8 hardening:** terminal authority audit snapshots now ignore Python bytecode cache and volatile SQLite `-wal`/`-shm` sidecars while retaining real Agent Bus file drift detection.
- **Authority preserved:** no ChaserAgent runtime activation, no profile/toolset activation, no terminal-to-Chaser binding, no Studio execution, no terminal execution, no approval consumption, no Agent Bus write/claim/update, no provider call, no external network call, no canonical mutation, and no host mutation was added.

### 2026-06-07 N19 Chaser runtime activation approval decision preflight update

- **Decision preflight built:** `runtime/chaser/runtime_activation_approval_decision_preflight.py` validates pending/approved/rejected N18 activation approval requests without deciding or consuming them.
- **CLI/API wired:** `chaseos chaser runtime activation-approval-decision-preflight <approval_id> --json` and `StudioAPI.get_chaser_runtime_activation_approval_decision_preflight(...)` expose read-only decision posture.
- **Policy posture:** unsafe/missing ids fail closed; valid requests must carry N18 activation-approval metadata, blocked ambient Studio execution metadata, matching target path, matching preview id against a fresh N17 preview, false Agent Bus/provider request flags, false authority metadata, and Tier 4 terminal trust posture.
- **Live result:** live CLI over pending approval `7623ee52-ffff-411c-b11d-87d6b6f30e02` returned `blocked_pending_activation_approval`, all checks passed, `ready_for_activation_consumer_next_pass=false`, and all authority flags false.
- **Authority preserved:** no approval decision write, approval status mutation, approval consumption, exact-once marker write, ChaserAgent runtime activation, profile/toolset activation, terminal-to-Chaser binding, Studio execution, terminal execution, Agent Bus write/claim/update, provider call, external network call, canonical mutation, or host mutation was added.

### 2026-06-07 N20 Chaser runtime activation approval consumption design update

- **Consumption design built:** `runtime/chaser/runtime_activation_approval_consumption_design.py` now defines the future exact-once consumption marker, append-only audit event shape, write-guard handoff, and stop conditions after an approved N19 preflight.
- **CLI/API wired:** `chaseos chaser runtime activation-approval-consumption-design <approval_id> --json` and `StudioAPI.get_chaser_runtime_activation_approval_consumption_design(...)` expose read-only design/readback.
- **Policy posture:** unsafe/missing ids fail closed; pending approvals block as not approved; approved structurally valid approvals in tests report ready for a future write-guard pass only. The live pending approval `7623ee52-ffff-411c-b11d-87d6b6f30e02` returned `blocked_activation_approval_consumption_design_preflight_not_approved`.
- **Authority preserved:** no approval consumption, approval status mutation, exact-once marker write, activation audit write, ChaserAgent runtime activation, profile/toolset activation, terminal-to-Chaser binding, Studio execution, terminal execution, Agent Bus write/claim/update, provider call, external network call, canonical mutation, or host mutation was added.

### 2026-06-07 N21 Chaser runtime activation approval consumption write guard update

- **Consumption write guard built:** `runtime/chaser/runtime_activation_approval_consumption_write_guard.py` now composes N20 and performs only the exact-once consumption marker write plus append-only activation audit event after approved preflight and explicit confirmation.
- **CLI/API wired:** `chaseos chaser runtime activation-approval-consumption-write-guard <approval_id> --json` previews by default and writes only with both `--write-consumption-marker` and `--confirm-activation-approval-consumption`; `StudioAPI.get_chaser_runtime_activation_approval_consumption_write_guard(...)` is preview-only.
- **Policy posture:** unsafe/missing ids fail closed; pending approvals block; duplicate marker presence blocks before a second audit append; approval request status is not mutated. The live pending approval `7623ee52-ffff-411c-b11d-87d6b6f30e02` returned `blocked_activation_approval_consumption_write_guard_preview`.
- **Authority preserved:** no ChaserAgent runtime activation, profile/toolset activation, terminal-to-Chaser binding, Studio execution, terminal execution, approval status mutation, Agent Bus write/claim/update, provider call, external network call, canonical mutation, or host mutation was added.

### 2026-06-07 N22 Chaser runtime activation post-consumption readiness update

- **Post-consumption readiness built:** `runtime/chaser/runtime_activation_post_consumption_readiness.py` reads and validates the N21 exact-once marker plus matching append-only audit event for a Chaser runtime activation approval.
- **CLI/API wired:** `chaseos chaser runtime activation-post-consumption-readiness <approval_id> --json` and `StudioAPI.get_chaser_runtime_activation_post_consumption_readiness(...)` expose read-only marker/audit readiness.
- **Policy posture:** unsafe/missing ids fail closed; pending approvals block; valid readiness requires approved N19/N20 posture, a marker with the expected schema/status/effect flags, and a matching audit event. The live pending approval `7623ee52-ffff-411c-b11d-87d6b6f30e02` returned blocked with missing marker/audit and all authority false.
- **Authority preserved:** no marker/audit write, approval status mutation, approval consumption, ChaserAgent runtime activation, profile/toolset activation, terminal-to-Chaser binding, Studio execution, terminal execution, Agent Bus write/claim/update, provider call, external network call, canonical mutation, or host mutation was added.

### 2026-06-07 N23 Chaser runtime activation executor design update

- **Executor design built:** `runtime/chaser/runtime_activation_executor_design.py` defines the fail-closed future activation executor contract after N22 readiness.
- **CLI/API wired:** `chaseos chaser runtime activation-executor-design <approval_id> --json` and `StudioAPI.get_chaser_runtime_activation_executor_design(...)` expose read-only design/readback.
- **Policy posture:** unsafe/missing ids fail closed; N22 not-ready evidence blocks; Agent Bus mutation or provider dispatch requests block; valid consumed pairs in tests report readiness only for a future N24 write guard. The live pending approval `7623ee52-ffff-411c-b11d-87d6b6f30e02` returned blocked with missing marker/audit and all authority false.
- **Authority preserved:** no activation marker write, activation state write, activation executor audit write, approval status mutation, approval consumption, ChaserAgent runtime activation, profile/toolset activation, terminal-to-Chaser binding, Studio execution, terminal execution, Agent Bus write/claim/update, provider call, external network call, canonical mutation, or host mutation was added.

### 2026-06-07 N24 Chaser runtime activation executor write guard update

- **Executor write guard built:** `runtime/chaser/runtime_activation_executor_write_guard.py` now composes N23/N22 readiness and performs only the exact-once runtime activation marker write, activation state record write, and append-only activation executor audit event after explicit confirmation.
- **CLI/API wired:** `chaseos chaser runtime activation-executor-write-guard <approval_id> --json` previews by default and writes only with both `--write-activation-state` and `--confirm-runtime-activation-record`; `StudioAPI.get_chaser_runtime_activation_executor_write_guard(...)` is preview-only.
- **Policy posture:** unsafe/missing ids fail closed; pending approvals and missing N21/N22 consumption evidence block; Agent Bus mutation or provider dispatch requests block; duplicate marker/state presence blocks before a second audit append. The live pending approval `7623ee52-ffff-411c-b11d-87d6b6f30e02` returned blocked and no live marker/state/audit files were created.
- **Authority preserved:** no approval status mutation, approval consumption, live ChaserAgent runtime activation, profile/toolset executable activation, terminal-to-Chaser binding, Studio execution, terminal execution, Agent Bus write/claim/update, provider call, external network call, canonical mutation, or host mutation was added.

### 2026-06-07 N25 Chaser runtime activation state readiness update

- **State readiness built:** `runtime/chaser/runtime_activation_state_readiness.py` reads and validates the N24 runtime activation marker, activation state record, and append-only activation executor audit event.
- **CLI/API wired:** `chaseos chaser runtime activation-state-readiness <approval_id> --json` and `StudioAPI.get_chaser_runtime_activation_state_readiness(...)` expose read-only readiness.
- **Policy posture:** unsafe/missing approval chains fail closed; pending approvals and missing N24 evidence block; valid evidence requires matching marker/state/audit paths, expected schema/status values, and false effect flags. The live pending approval `7623ee52-ffff-411c-b11d-87d6b6f30e02` returned blocked and no live marker/state/audit files were created.
- **Authority preserved:** no marker/state/audit write in N25, approval status mutation, approval consumption, live ChaserAgent runtime activation, profile/toolset executable activation, terminal-to-Chaser binding, Studio execution, terminal execution, Agent Bus write/claim/update, provider call, external network call, canonical mutation, or host mutation was added.

### 2026-06-07 N26 Chaser runtime profile/toolset activation design update

- **Profile/toolset activation design built:** `runtime/chaser/runtime_profile_toolset_activation_design.py` defines the future guarded profile/toolset activation write-guard contract after N25 readiness.
- **CLI/API wired:** `chaseos chaser runtime profile-toolset-activation-design <approval_id> --json` and `StudioAPI.get_chaser_runtime_profile_toolset_activation_design(...)` expose read-only design/readback.
- **Policy posture:** unsafe/missing approval chains fail closed; pending approvals and missing N24 evidence block; valid evidence requires N25 readiness, descriptive-only profile views, non-executing toolset views, and false authority flags before reporting readiness for the future N27 write guard. The live pending approval `7623ee52-ffff-411c-b11d-87d6b6f30e02` returned blocked and no profile/toolset marker/state/audit files were created.
- **Authority preserved:** no profile/toolset marker/state/audit write in N26, approval status mutation, approval consumption, live ChaserAgent runtime activation, profile/toolset executable activation, terminal-to-Chaser binding, Studio execution, terminal execution, Agent Bus write/claim/update, provider call, external network call, canonical mutation, or host mutation was added.

### 2026-06-07 N27 Chaser runtime profile/toolset activation write guard update

- **Profile/toolset activation write guard built:** `runtime/chaser/runtime_profile_toolset_activation_write_guard.py` implements the explicit confirmation guarded writer for profile/toolset activation marker/state/audit records after N26/N25 readiness.
- **CLI/API wired:** `chaseos chaser runtime profile-toolset-activation-write-guard <approval_id> --json` previews by default and writes only with both `--write-profile-toolset-activation` and `--confirm-profile-toolset-activation-record`; `StudioAPI.get_chaser_runtime_profile_toolset_activation_write_guard(...)` is preview-only.
- **Policy posture:** unsafe or mismatched approval/profile/toolset inputs fail closed; pending approvals and missing N24/N25 evidence block; valid evidence writes only an exact-once profile/toolset marker, profile state record, toolset state record, and append-only audit event. The live pending approval `7623ee52-ffff-411c-b11d-87d6b6f30e02` returned blocked and no profile/toolset marker/state/audit files were created.
- **Authority preserved:** no approval status mutation, approval consumption, live ChaserAgent runtime activation, profile/toolset executable activation, terminal-to-Chaser binding, Studio execution, terminal execution, Agent Bus write/claim/update, provider call, external network call, canonical mutation, or host mutation was added.

### 2026-06-07 N28 Chaser runtime profile/toolset activation readiness update

- **Profile/toolset activation readiness built:** `runtime/chaser/runtime_profile_toolset_activation_readiness.py` validates the N27 profile/toolset marker, profile state, toolset state, and append-only audit event without writing.
- **CLI/API wired:** `chaseos chaser runtime profile-toolset-activation-readiness <approval_id> --json` and `StudioAPI.get_chaser_runtime_profile_toolset_activation_readiness(...)` expose read-only readiness.
- **Policy posture:** unsafe/missing approval chains fail closed; pending approvals and missing N27 evidence block; valid evidence requires matching marker/state/audit paths, expected schema/status values, matching append-only audit evidence, and false effect flags. The live pending approval `7623ee52-ffff-411c-b11d-87d6b6f30e02` returned blocked and no profile/toolset marker/state/audit files were created.
- **Authority preserved:** no marker/state/audit write in N28, approval status mutation, approval consumption, live ChaserAgent runtime activation, profile/toolset executable activation, terminal-to-Chaser binding, Studio execution, terminal execution, Agent Bus write/claim/update, provider call, external network call, canonical mutation, or host mutation was added.

## Matrix

| # | Feature | Source / reason | ChaseOS target layer | Status | Priority | Governance risk | Required backend contract | Required frontend surface | Notes |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | Governed Terminal Workbench + Human Studio Terminal | Handoff first safe slice | ChaseOS Core + backend + Studio | partial | P0 | Raw shell / sudo / ambient FS | TerminalAdapter policy, scope, audit, run-detail readback, authority audit, Studio full terminal contract, human session audit | Chaser terminal binding | Adapter + CLI + run-audit/readback + Studio read-only backend + frontend preview/history/detail mount + proposal packets + N6A approval-request queue + N6R readiness + N6 approved CLI executor (`mkdir`, `touch`, `copy`, `cp`) + N7 internal gateway ingress + N8 authority audit + N15 readiness + N16 activation gate design + N17 activation approval preview + N18 activation approval request queue write gate + N19 decision preflight + N20 consumption design + N21 consumption write guard + N22 post-consumption readiness readback + N23 activation executor design + N24 activation executor write guard + N25 activation state readiness + N26 profile/toolset activation design + N27 profile/toolset activation write guard + N28 profile/toolset activation readiness + N29 Studio full terminal product contract + human `#/terminal` session backend/frontend built; broader write/content verbs, Chaser terminal binding, live ChaserAgent wiring, and network/external gateway ingress planned |
| 2 | TerminalAdapter non-stub implementation | Handoff required foothold | `runtime/operator_surface` | partial | P0 | Host mutation | command classification, cwd validation, capture | Backend route before UI | Read-only allowlist; `chaseos operate terminal` CLI including `show`, `terminal_runs` audit/readback, and registry registration BUILT |
| 3 | Runtime Console / Gateway Health | Hermes Desktop/status pattern | Studio Runtime Cockpit | partial | P1 | Status mistaken for authority | runtime health/readiness contract | Runtime console cards | Existing cockpit surfaces, expansion planned |
| 4 | WSL Ubuntu â†’ Hermes Gateway diagnostic and start-plan | Handoff diagnostic lane | Hermes lifecycle + Studio settings | partial | P1 | Autostart/start mutation | read-only diagnostics + approval packet | Gateway health card | Start/restart automation out of scope |
| 5 | ChaserAgent internal core architecture | Critical architecture decision | ChaseOS Core `runtime/chaser` | partial | P0 | Second uncontrolled brain | AOR/Gate/policy/session/artifact contracts | ChaserAgent dashboard | Core package foothold exists (models/sessions/exports plus Phase A agent/board/policy/profile/memory/toolset/artifact preview contracts) plus N15 readiness, N16 activation gate design, N17 activation approval preview, N18 approval request queue writer, N19 decision preflight, N20 consumption design, N21 consumption marker/audit write guard, N22 post-consumption readiness readback, N23 activation executor design, N24 activation executor write guard, N25 activation state readiness, N26 profile/toolset activation design, N27 profile/toolset activation write guard, and N28 profile/toolset activation readiness; live runtime planned and explicitly blocked until terminal binding design/execution, Agent Bus/provider gates, and operator approval exist |
| 6 | `board.py` / orchestration board | Handoff board control surface | `runtime/chaser/board.py` + Studio `#/chaser-board` | partial | P0 | Board becoming memory owner | task/proposal/evidence/approval schema | Board dashboard | Phase A board card contracts, N5 read-only board state aggregator, proposal packets, N6A approval-request queue, N6R readiness, N6 CLI executor contract visibility, N7 gateway ingress routing, N11 read-only Studio dashboard, N12 source-rendered visual QA proof, N13 packaged harness, and N14 packaged/native route proof are built/verified. Board itself still does not execute, dispatch, consume approvals, write Agent Bus tasks, or own mutation authority |
| 7 | Studio frontend/backend split | Handoff app split | Backend APIs over Core + Studio | planned | P1 | Frontend as truth source | safe API contracts | Product shell surfaces | Core remains source of truth |
| 8 | Session list and session management | Hermes Desktop session pattern | Session metadata store | partial | P1 | Private metadata/delete risk | session index + lifecycle contract | Sidebar/session list | `list_sessions()`/`load_session()` plus audited pin/unpin, rename, and archive-first removal are built; UI context menu planned |
| 9 | Pin/unpin chat | Session context menu | Session metadata | partial | P1 | Metadata mutation | pin-state contract | Context menu | Backend `set_session_pinned()` implemented; UI planned |
| 10 | Copy session ID | Session context menu | Session metadata | planned | P2 | ID exposure/confusion | read-only ID API | Context menu | Not implemented |
| 11 | Export chat/session | Required handoff feature | Session export backend | partial | P0 | Secret/provenance leakage | Markdown/JSON export + redaction + audit | Export action/toast | Backend implemented in `runtime/chaser/exports.py` (md/json, redaction, manifests, audit, no upload); N4 Studio chat -> SessionRecord adapter and CLI `chaseos chaser session export-chat` built; Studio UI action/toast and generic `chaseos session export` remain planned |
| 12 | Rename chat | Session context menu | Session metadata | partial | P2 | Rename not canonical truth | rename metadata contract | Context menu | Backend `rename_session()` implemented; UI planned |
| 13 | Delete/archive chat | Session context menu | Session archive | partial | P1 | Irreversible deletion | archive-first/delete contract | Context menu | Backend `archive_session()` implemented as archive-first active-store removal; no hard delete; UI planned |
| 14 | Session exported toast / feedback | Hermes UX | Studio UX | planned | P3 | False success | export result contract | Toast | Not implemented |
| 15 | Artifacts hub | Hermes Desktop feature | Artifact/provenance registry | partial | P1 | Artifact mistaken for truth | typed artifact manifest | Artifacts page | Phase A artifact manifest contracts built; no unified hub or writes |
| 16 | Files artifact tab | Artifacts hub | Artifact registry | planned | P2 | File exposure | file artifact manifest | Files tab | Not implemented |
| 17 | Links artifact tab | Artifacts hub | Artifact registry | planned | P2 | External trust risk | link artifact manifest | Links tab | Not implemented |
| 18 | Images artifact tab | Artifacts hub | Artifact registry | planned | P2 | Visual evidence ambiguity | image manifest + verification | Images tab | Not implemented |
| 19 | All artifacts tab | Artifacts hub | Artifact registry | planned | P2 | Mixed trust states | combined artifact query | All tab | Not implemented |
| 20 | Toolsets manager | Hermes tools UI | Policy/capability registry | partial | P1 | UI toggles granting authority | toolset config/proposal contract | Toolsets page | Phase A read-only toolset views built; no manager UI or executable toggles |
| 21 | Browser toolset | Toolsets family | Browser operator policy | partial | P2 | Auth/browser action risk | browser capability policy | Toolset card | Browser runtime exists; manager planned |
| 22 | Files toolset | Toolsets family | Filesystem policy | planned | P2 | Ambient file access | allowed path contract | Toolset card | Planned |
| 23 | Image toolset | Toolsets family | Image/artifact tools | planned | P3 | Media provenance | media artifact contract | Toolset card | Planned |
| 24 | Memory toolset | Toolsets family | Memory/Gate policy | planned | P1 | Memory bypass | candidate/review contract | Toolset card | Planned |
| 25 | Shell toolset | Toolsets family | TerminalAdapter policy | partial | P0 | Unrestricted shell | TerminalAdapter + approvals + authority audit | Toolset card | MVP policy scaffold, read-only audit/detail readback, proposal packets, approval-request queue, readiness validation, approved `mkdir`/`touch`/`copy`/`cp` CLI executor, N7 internal gateway wrapper, N8 authority audit, and N28 profile/toolset activation readiness exist; no ChaserAgent shell wiring, unrestricted shell, Studio execution, network gateway server, or broader write/content verbs |
| 26 | Web toolset | Toolsets family | Web/search policy | planned | P2 | Prompt injection | web intake trust labels | Toolset card | Planned |
| 27 | Profiles page | Hermes profile pattern | Runtime profiles/role cards | partial | P1 | Profile grants authority | profile schema with ceilings | Profiles page | Phase A Chaser profile views built; full manager planned |
| 28 | default/research/ops/local/builder profile pattern | Handoff profile pattern | Runtime profile config | planned | P2 | Role drift | template/profile schema | Profile templates | Planned |
| 29 | SOUL.md-style editable persona surface, safely adapted | Hermes profile/persona | Persona/profile proposal layer | planned | P2 | Persona overriding policy | draft/review contract | Persona editor | Must not directly mutate protected SOUL |
| 30 | Settings surface | Hermes Desktop feature | Studio settings | partial | P2 | Settings mutate policy/credentials | settings schema + approvals | Settings page | Existing surfaces; expansion planned |
| 31 | Model settings | Settings | Provider governance | partial | P2 | Provider/credential risk | provider config proposal/readiness | Model settings | Existing governance, UI expansion planned |
| 32 | Chat settings | Settings | Chat/session config | planned | P3 | Runtime authority confusion | chat config schema | Chat settings | Planned |
| 33 | Appearance settings | Settings | Local Studio prefs | planned | P3 | Low | local prefs | Appearance page | Planned |
| 34 | Workspace settings | Settings | Workspace/vault scope | partial | P1 | Ambient workspace exposure | workspace scope validation | Workspace page | Planned expansion |
| 35 | Safety settings | Settings | Permission/Gate view | planned | P1 | UI weakening policy | read-only safety display + proposals | Safety page | Planned |
| 36 | Memory & Context settings | Settings | Memory boundary/Gate | planned | P1 | Canonical memory mutation | candidate/review contract | Memory settings | Planned |
| 37 | Voice settings | Settings | Voice I/O | deferred | P3 | Transcript/privacy | voice transcript/audit policy | Voice page | Out of scope |
| 38 | Advanced settings | Settings | Runtime config | planned | P3 | Hidden authority expansion | read-only + approval packets | Advanced page | Planned |
| 39 | Gateway settings | Settings | Hermes/lifecycle config | partial | P1 | Startup/gateway mutation | diagnostic + explicit approvals | Gateway settings | Existing status surfaces |
| 40 | API Keys settings | Settings | Credential refs | planned | P1 | Secret leakage | opaque secret refs only | API Keys page | Planned, no raw keys |
| 41 | Skills & Tools settings | Settings/toolsets | Skill/capability registry | planned | P2 | Skill mutation bypass | quarantine/review path | Skills & Tools page | Planned |
| 42 | MCP settings | Settings/connectors | MCP governance | planned | P2 | Connector authority | MCP registry + approvals | MCP page | Planned |
| 43 | About page | Product shell | Studio info | planned | P3 | Low | version/status contract | About page | Planned |
| 44 | Light/Dark/System color mode | Theme pattern | Studio prefs | planned | P3 | Low | local prefs | Theme toggle | Planned |
| 45 | Product vs Technical tool-call display mode | Hermes UX | Tool event renderer | planned | P2 | Hidden audit detail | display-mode + audit contract | Mode toggle | Planned |
| 46 | Theme pattern | Visual design | Studio shell | planned | P3 | Low | theme tokens | Theme UI | Planned |
| 47 | Command palette | Hermes/Desktop pattern | Studio action registry | planned | P2 | Unsafe palette actions | preview/action-envelope catalog | Command palette | Planned |
| 48 | Update status / one-click update pattern | Product shell | Release governance | deferred | P3 | Autoupdate mutation | read-only update status first | Update card | One-click update out of scope |
| 49 | Gateway-ready status | Status bar | Runtime health | partial | P1 | False readiness | readiness contract | Indicator | Existing Hermes status surfaces |
| 50 | Agents-running status | Status bar | Runtime inventory/Agent Bus | partial | P1 | Presence â‰  authority | runtime status contract | Indicator | Planned expansion |
| 51 | Cron status | Status bar | Schedules/cron | partial | P2 | Schedule authority | read-only schedule status | Indicator | Planned expansion |
| 52 | Token count | Status bar | Session telemetry | planned | P3 | Low | telemetry contract | Indicator | Planned |
| 53 | Session timer | Status bar | Session telemetry | planned | P3 | Low | telemetry contract | Indicator | Planned |
| 54 | Active model display | Status bar | Provider governance | partial | P2 | Provider identity confusion | model status contract | Indicator | Planned expansion |
| 55 | Drag/drop attachment direction | Chat UX | Attachment intake | planned | P2 | External file injection | quarantine/intake contract | Dropzone | Planned |
| 56 | Right preview rail direction | Studio UX | Preview/artifact rail | planned | P3 | Preview â‰  truth | preview contract | Right rail | Planned |
| 57 | File browser rail | Studio UX | Scoped file browser | planned | P2 | Ambient file exposure | allowed workspace file API | File rail | Planned |
| 58 | Branch/workspace indicator | Status bar | Workspace/git status | planned | P2 | Git-state trust | read-only git/workspace contract | Indicator | Planned |
| 59 | Inline tool cards | Chat/tool UX | Tool event renderer | planned | P2 | Tool output trust | tool-event schema + trust labels | Inline cards | Planned |
| 60 | Tool-call disclosure | Chat/tool UX | Audit renderer | planned | P2 | Hidden action risk | technical disclosure mode | Expandable details | Planned |
| 61 | Streaming chat | Chat UX | Runtime bridge | partial | P2 | Runtime routing risk | Agent Bus/runtime handler | Chat panel | Phase 11 chat bridge exists; not ChaserAgent complete |
| 62 | Inline generated-image artifacts | Chat/artifacts | Artifact registry | planned | P2 | Media provenance | image artifact manifest | Inline artifact card | Planned |
| 63 | ChaserAgent dashboard direction | Product direction | Studio + `runtime/chaser` | partial | P1 | Dashboard as authority plane | read-only task/health/proposal contracts | Dashboard | N11 read-only Studio Chaser Board dashboard is mounted for board readback and N12 source-rendered visual QA is passing; N13 packaged harness is built but current packaged proof is partial because the executable does not mount `#/chaser-board`. Write-capable dashboard actions, Agent Bus mutation, approval consumption, and live ChaserAgent wiring remain planned/gated |
| 64 | Hermes as reference pattern only | Governance rule | All layers | existing | P0 | Hermes bypassing Gate | ChaseOS Gate/AOR authority | N/A | Explicitly preserved |

## Rejected for this pass

| Rejected expansion | Reason |
|---|---|
| Unrestricted terminal | Violates Terminal Workbench governance and host safety. |
| Sudo/elevation | Blocked by policy and tests. |
| Ambient filesystem or credential access | Violates ChaseOS scope and credential boundaries. |
| Separate uncontrolled ChaserAgent repo | ChaserAgent starts inside ChaseOS Core first. |
| Hermes/OpenClaw/Gateway authority bypass | Hermes is a reference pattern; ChaseOS Gate remains authority. |
