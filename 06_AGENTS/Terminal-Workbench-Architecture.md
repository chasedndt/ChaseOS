# Terminal Workbench Architecture

Date: 2026-06-02 (CLI + Studio backend wired 2026-06-03; Studio frontend mounted 2026-06-05; read-only detail hardening, pre-N6 proposal packets, N6A approval requests, N6R executor readiness, initial N6 gated CLI executor, N7 internal gateway ingress, N8 authority audit, N9 approved file-create lane, N10 approved file-copy lane, N11 read-only Chaser Board dashboard, and N12 source visual QA 2026-06-06)
Runtime: Hermes/Optimus (2026-06-03 pass: Archon; 2026-06-06 read-only hardening: Codex)
Status: PARTIAL - adapter + CLI + run-audit/detail readback + Studio backend + Studio frontend preview/history/detail mount + pre-N6 proposal packets + N6A approval-request queue + N6R executor-readiness contract + initial N6 gated CLI executor + N7 internal gateway ingress + N8 authority audit + N9 approved `touch` file-create lane + N10 approved `copy`/`cp` file-copy lane + N11 read-only Chaser Board dashboard + N12 source-rendered Chaser Board visual QA BUILT; N13 packaged proof harness BUILT but current packaged proof PARTIAL because the executable does not mount `#/chaser-board`; broader write/content verbs, kill/stop controls, external/network gateway ingress, package rebuild recovery, and ChaserAgent live runtime wiring PLANNED
Source handoff: [[ChaseOS_Terminal_ChaserAgent_Fullstack_Implementation_Handoff_v2]]
Related: [[Terminal-ChaserAgent-Feature-Matrix]] Â· [[ChaserAgent-Architecture]] Â· [[Session-Export-and-Artifacts-Architecture]] Â· [[Chaser-Gateway-Architecture]] Â· [[Terminal-ChaserAgent-Agent-Bus-Handover]] Â· [[HERMES]] Â· [[Hermes-Runtime-Profile]] Â· [[Agent-Activity-Index]]

## 2026-06-06 update - read-only run detail hardening

- **Run detail helper:** `runtime/operator_surface/terminal_runs.py` now safely loads recorded run audit JSON by run id through `load_terminal_run_detail()`, rejecting unsafe ids and returning compact `ok/error` shapes for unsafe or missing records.
- **CLI readback:** `chaseos operate terminal show <run_id> --json` inspects an existing terminal run audit record without executing anything.
- **Studio contract:** `get_terminal_workbench` now includes policy defaults, audit root/status, richer recent-run metadata, and a run-detail contract. `StudioAPI.get_terminal_run_detail(run_id)` exposes read-only detail data.
- **Studio frontend:** selected history entries open a detail panel with command, cwd, classification, policy decision, exit code, duration, stdout/stderr excerpts, redaction/truncation flags, audit paths, and a Tier 4 warning.
- **Non-executing actions only:** select run, copy run id, copy command, and preview a selected history command through the existing Preview path. There is still no Execute/Run button and no frontend execution API.
- **Boundary preserved:** no write-capable terminal lane, no ChaserAgent terminal adapter, no provider call, no Agent Bus write, no approval consumption, and no canonical mutation.
- **Tests:** terminal/operator/studio focused suite passed (42), `compileall runtime/operator_surface runtime/studio` passed with an existing `export_icon.py` invalid-escape warning, CLI show smoke returned the expected missing-run error envelope, and frontend JS syntax check passed.

## 2026-06-06 update - pre-N6 proposal packets

- **Board proposal helper:** `runtime/chaser/board.py` now exposes `build_action_proposal()` for terminal command classification/readiness packets.
- **CLI/API:** `chaseos chaser board propose terminal-command <command> --json` and `StudioAPI.get_chaser_board_action_proposal(...)` return proposal packets only.
- **Policy posture:** read-only commands return `preview_allowed`; write commands return `approval_required_future_n6`; shell-control/destructive/elevated/network/unknown and out-of-vault cwd proposals block.
- **Boundary preserved:** no terminal execution, no Studio execution, no approval queue write, no approval consumption, no Agent Bus write, no provider call, no canonical mutation, and no ChaserAgent runtime wiring.
- **Tests:** focused pre-N6 board/CLI/API suite passed (19) and compileall over touched runtime surfaces passed.

## 2026-06-06 update - N6A approval-request front half

- **Approval request helper:** `runtime/chaser/board.py` now exposes `build_terminal_write_approval_request()` for eligible future-N6 write-command proposals.
- **CLI/API:** `chaseos chaser board request-terminal-approval <command> --json` previews by default and queues a pending Studio approval only with explicit `--write-approval-request`; `StudioAPI.request_chaser_terminal_write_approval(...)` mirrors the same default-preview behavior.
- **Eligibility:** only `write_command` / `approval_required_future_n6` proposals can be queued. Read-only, shell-control, destructive, elevated, network, unknown, and out-of-vault cwd proposals block.
- **Ambient execution block:** `StudioService.execute_approved()` rejects `terminal_write_lane_approval_request=True`, so generic Studio approval execution cannot run terminal commands.
- **Boundary preserved:** no terminal execution, no Studio execution button, no approval consumption, no Agent Bus write, no provider call, no canonical mutation, and no ChaserAgent runtime wiring.
- **Tests:** focused board/CLI/API suite passed (20), Chaser core regression passed (28), and compileall over touched runtime surfaces passed.

## 2026-06-06 update - N6R executor readiness

- **Readiness helper:** `runtime/chaser/terminal_write_executor_readiness.py` now validates a terminal write approval request for N6 execution without consuming the approval or executing the command.
- **CLI/API:** `chaseos chaser board terminal-executor-readiness <approval_id> --json` and `StudioAPI.get_chaser_terminal_write_executor_readiness(...)` inspect approval status, terminal-write metadata, fresh proposal classification, proposal id, target path, cwd, authority metadata, and exact-once marker absence.
- **Policy posture:** pending/non-approved approvals block. Approved structurally valid approvals report `scope_validation_ok=true`, `ready_for_future_executor_after_review=true`, `terminal_write_executor_implemented=true`, and `ready_for_execution_now=true`.
- **Boundary preserved:** no terminal execution, no terminal audit write, no exact-once marker write, no approval consumption, no Studio execution button, no Agent Bus write, no provider call, no canonical mutation, and no ChaserAgent runtime wiring.
- **Tests:** focused board/CLI/API suite passed (27), Chaser core regression passed (35), compileall over touched runtime surfaces passed, and a temp-vault CLI smoke verified no target directory, marker, or Agent Bus storage was created.

## 2026-06-06 update - N6 gated CLI executor

- **Executor helper:** `runtime/chaser/terminal_write_executor.py` now consumes approved terminal write approvals through a dedicated CLI-only path.
- **CLI:** `chaseos chaser board execute-terminal-approval <approval_id> --confirm-approved-terminal-write --json`.
- **Execution gates:** exact approval/proposal match, approved status, terminal-write metadata, fresh classification, explicit confirmation, existing in-vault cwd, in-vault target, and absent marker are required before mutation.
- **Initial write support:** only `mkdir <target>` is supported. Unsupported write verbs block before marker reservation or approval consumption.
- **Audit/consumption:** marker reservation happens before mutation; the executor writes a terminal run audit, updates the approval to `executed` or `execution_failed`, updates the marker, and duplicate execution blocks.
- **Boundary preserved:** no Studio execution button/API, unrestricted shell, shell operators, elevation, Agent Bus writes, provider calls, canonical writeback, external upload, or ChaserAgent runtime/profile/toolset activation.
- **Tests:** focused N6 board/CLI/API suite passed (34), adjacent terminal/operator regression passed (70), compileall passed, and temp-vault CLI smoke verified confirmed execution plus duplicate blocking.

## 2026-06-06 update - N7 internal gateway ingress

- **Gateway helper:** `runtime/chaser/gateway.py` now exposes an internal structured ingress facade with safe request/session id validation, bounded request size, local-operator authorization, and route-level confirmations.
- **CLI:** `chaseos chaser gateway ingress <intent> --payload-json ... --confirm-local-operator --json` routes board state, terminal proposals, terminal approval preview/write, executor readiness, and the existing N6 approved executor.
- **Studio contract:** `StudioAPI.get_chaser_gateway_ingress_contract()` exposes only read-only contract metadata. Studio still has no ingress execution API and no terminal execute/run button.
- **Execution gates:** approval queue writes require `--confirm-approval-queue-write`; terminal execution requires `--confirm-approved-terminal-write` and still delegates to the N6 exact approval/proposal/scope/marker checks.
- **Boundary preserved:** no network gateway server, Studio execution, unrestricted shell, shell operators, elevation, Agent Bus writes, provider calls, canonical writeback, external upload, or ChaserAgent runtime/profile/toolset activation. Gateway payloads and terminal output remain Tier 4 untrusted.
- **Tests:** focused N7 gateway/CLI/API suite passed (14), adjacent Chaser + terminal/operator regression passed (79), Terminal Workbench read-only backend/frontend regression passed (14), and compileall passed.

## 2026-06-06 update - N8 terminal authority audit

- **Audit helper:** `runtime/chaser/terminal_authority_audit.py` now builds a deterministic read-only proof packet across Terminal Workbench, Chaser board, N7 gateway ingress, N6 readiness/executor denial paths, unsafe TerminalAdapter classifications, and Studio API method exposure.
- **CLI/API:** `chaseos chaser terminal authority-audit --json` and `StudioAPI.get_chaser_terminal_authority_audit()` expose the audit packet.
- **Side-effect proof:** the audit uses preview/blocked paths only and snapshots approvals, exact-once markers, terminal run audit files, Agent Bus files, and the probe target before/after.
- **Boundary preserved:** no Studio execution, terminal execution, approval queue write, approval consumption, exact-once marker write, terminal audit write, Agent Bus write, provider call, canonical writeback, external upload, or host mutation.
- **Tests:** focused N8 audit/CLI/API suite passed (10), adjacent terminal/Chaser/Studio regression passed (89), and compileall passed.

## 2026-06-06 update - N9 approved file-create lane

- **Executor support:** `runtime/chaser/terminal_write_executor.py` now supports `touch <target>` in addition to `mkdir <target>`.
- **Execution gates:** the same N6 gates apply: approved terminal-write request, exact proposal match, fresh classification, explicit `--confirm-approved-terminal-write`, existing in-vault cwd, in-vault target, no existing target, and absent exact-once marker.
- **File behavior:** `touch` creates an empty file only. It does not create parent directories, overwrite existing files, write content, follow shell operators, or run an external shell command.
- **Boundary preserved:** no Studio execution button/API, unrestricted shell, shell operators, elevation, network/destructive command lane, Agent Bus writes, provider calls, canonical writeback, external upload, or ChaserAgent runtime/profile/toolset activation.
- **Tests:** focused N9 board/CLI/gateway/API/audit suite passed (51), adjacent terminal/Chaser/Studio regression passed (93), and compileall passed.

## 2026-06-06 update - N10 approved file-copy lane

- **Executor support:** `runtime/chaser/terminal_write_executor.py` now supports `copy <source> <target>` and `cp <source> <target>` in addition to `mkdir <target>` and `touch <target>`.
- **Execution gates:** the same N6 gates apply: approved terminal-write request, exact proposal match, fresh classification, explicit `--confirm-approved-terminal-write`, existing in-vault cwd, existing in-vault source file, existing target parent, in-vault non-existing target, and absent exact-once marker.
- **File behavior:** copy uses Python file APIs, preserves the source, creates a new target file, and does not create parent directories, overwrite targets, read source content into terminal output, follow shell operators, or run an external shell command.
- **Boundary preserved:** no Studio execution button/API, unrestricted shell, shell operators, elevation, network/destructive command lane, Agent Bus writes, provider calls, canonical writeback, external upload, ChaserAgent runtime/profile/toolset activation, or arbitrary inline content-writing lane.
- **Tests:** focused N10 board/CLI/gateway/API/audit suite passed (55), adjacent terminal/Chaser/Studio regression passed (97), and compileall passed.

## 2026-06-06 update - N11 read-only Chaser Board dashboard

- **Studio dashboard:** `#/chaser-board` now renders existing Chaser board state from `StudioAPI.get_chaser_board_state()` in the Studio shell.
- **Terminal handoff:** The board can send a selected terminal command to Terminal Workbench's existing Preview path only; it does not create a terminal run or call any board execution/approval API.
- **Boundary:** no execute/run button, no terminal execution API, no approval request write/consume API, no Agent Bus write, no provider call, no canonical mutation, and no ChaserAgent live runtime wiring.
- **Tests:** focused dashboard/frontend/backend suite passed (52), adjacent terminal/Chaser/Studio regression passed (102), frontend JS syntax check passed, and compileall passed.

## 2026-06-06 update - N12 Chaser Board source visual QA

- **Visual harness:** `runtime/studio/chaser_board_product_visual_qa.py` verifies the source Studio shell `#/chaser-board` page with Playwright.
- **Restricted API bridge:** the proof permits only `get_chaser_board_state` for the Chaser Board page and records unexpected API calls as failures.
- **Evidence:** desktop initial, desktop selected-card, and mobile responsive screenshots plus JSON/Markdown reports are written under `07_LOGS/Studio-Visual-QA/2026-06-06-terminal-n12-chaser-board-visual-qa/`.
- **Boundary:** this pass does not run the packaged/native EXE. It adds no Studio execution, terminal execution, approval request write, approval consumption, Agent Bus write, provider call, connector call, canonical mutation, host mutation, or ChaserAgent live runtime wiring.
- **Tests:** focused visual/frontend/backend suite passed (21), adjacent terminal/Chaser/Studio regression passed (106), live visual QA returned `ok=true`, and compileall passed.

## 2026-06-06 update - N13 Chaser Board packaged visual QA

- **Packaged harness:** `runtime/studio/chaser_board_packaged_visual_qa.py` targets `#/chaser-board` through the existing packaged route visual QA runner.
- **Helper hardening:** `runtime/studio/packaged_app_visual_qa.py` accepts route-specific visible-copy allowlists for intentional Chaser Board governance copy.
- **Live proof status:** PARTIAL. The packaged executable launched and produced a nonblank screenshot, but route activation left `panel-dashboard` active; Chaser Board cards/detail/Tier 4 authority copy were not visible.
- **Rebuild status:** a current-source PyInstaller rebuild attempt timed out and was cleaned up by stopping the duplicate build processes. No new packaged executable proof was produced.
- **Boundary:** no Studio execution, terminal execution, approval request write, approval consumption, Agent Bus write, provider/connector call, canonical mutation, installer/signing/startup work, or ChaserAgent live runtime wiring was added.

## 2026-06-05 update - Studio frontend preview/history mount

- **Studio frontend:** `runtime/studio/shell/frontend/index.html`, `app.js`, and `styles.css` now mount `#/terminal-workbench` under Runtime / Advanced Runtime.
- **Backend call:** the panel calls `StudioAPI.get_terminal_workbench(command, 20)` for preview/history and, after the 2026-06-06 hardening pass, `StudioAPI.get_terminal_run_detail(run_id)` for read-only audit detail. It renders policy, preview classification, warnings, audited run history, and selected-run detail.
- **No execution path:** the panel has a Preview button only. It has no execute/run button and no frontend call to a terminal execution API. Execution remains in the governed CLI/AOR lane.
- **Registry:** `runtime/studio/shell/panel_registry.py` declares `terminal-workbench` as mounted/read-only with `api_methods=["get_terminal_workbench", "get_terminal_run_detail"]`.
- **Tests:** `runtime/studio/shell/test_terminal_workbench_frontend.py` verifies nav/panel mount, backend call, no execute button, and read-only registry contract.
- **Still planned:** broader write verbs, kill/stop lifecycle, network/external gateway ingress, and any live ChaserAgent/runtime control-plane expansion.

## 2026-06-03 update â€” CLI + run-audit + Studio backend wired

- **CLI:** `chaseos operate terminal policy|preview <CMD>|run <CMD>|history` (`runtime/cli/main.py` + `runtime/operator_surface/terminal/operator.py`). `run` previews-then-executes only read-only commands, exits 3 on block.
- **Run-audit persistence:** `runtime/operator_surface/terminal_runs.py` writes JSON + Markdown records to `07_LOGS/Terminal-Runs/<YYYY-MM-DD>/<run_id>.json|.md` (satisfies the policy file's audit path). Every run â€” executed, blocked, or execution-error â€” is recorded with Tier 4 labels.
- **Adapter registration:** `TerminalAdapter` is registered in the default `adapter_registry` on import of the terminal operator module.
- **Studio backend:** `runtime/studio/terminal_workbench.py` + `StudioAPI.get_terminal_workbench()` expose a **read-only** workbench contract (policy + no-execution classification preview + recent run history). **Studio never executes** â€” execution stays on the CLI/AOR path.
- **Tests:** `test_terminal_runs.py` (8), `test_terminal_operator.py` (8), `test_terminal_workbench.py` (6), plus the existing `test_terminal_adapter.py` (9).
- **Still planned:** broader write verbs, kill/stop of long runs, and N7 gateway ingress. See [[Terminal-ChaserAgent-Agent-Bus-Handover]].

## Governed terminal concept

Terminal Workbench is a ChaseOS operator surface for scoped terminal/runtime actions. It is not an unrestricted shell embedded in Studio. Every terminal action must pass through policy, scope validation, output capture/redaction, and audit.

Terminal output is **Tier 4 untrusted input**. It can be evidence, but it cannot directly mutate canonical ChaseOS truth, memory, policies, Feature Registers, Permission Matrix, Gate rules, or protected docs.

## Current implementation foothold

Before this pass, `runtime/operator_surface/adapters/terminal_adapter.py` was a documented STUB. This pass changes it to a partial bounded MVP scaffold:

- command classification;
- cwd validation against `OperatorScope.allowed_paths` and `file://` target URIs;
- elevated/destructive/write/network command blocking;
- bounded subprocess execution for read-only allowlisted commands;
- stdout/stderr capture;
- max output truncation;
- simple secret-like redaction;
- StepResult and OperatorEvent audit payloads with Tier 4/untrusted labels.

Policy scaffold: `runtime/operator_surface/policies/terminal.yaml`.
Tests: `runtime/operator_surface/tests/test_terminal_adapter.py`.

## TerminalAdapter role

The adapter is the backend executor/policy boundary for terminal actions. Studio or CLI surfaces may request terminal actions, but they must not execute shell commands directly.

Current classes:

| Class | Status in MVP |
|---|---|
| `read_only_command` | allowed if executable is in the allowlist and cwd is in scope |
| `destructive_command` | blocked |
| `elevated_command` | blocked |
| `write_command` | blocked |
| `network_command` | blocked |
| `unknown_command` | blocked |
| `invalid_command` | blocked |

## Command scope and cwd policy

- A run must declare an `OperatorScope` with target paths.
- `cwd` must resolve under a declared allowed root.
- No ambient filesystem roaming.
- No credential access.
- No sudo/elevation.
- No hidden startup/autostart/service/cron mutation.

## Allowlist / denylist posture

The MVP allowlist is intentionally narrow: `pwd`, `ls`, `dir`, `date`, `whoami`, `uname`, `python`, `python3`, `pytest`, `uvx`, `printf`.

Blocked by default:

- elevated: `sudo`, `su`, `doas`, `runas`;
- destructive: `rm`, `rmdir`, `del`, `erase`, `mkfs`, `shutdown`, `reboot`, `poweroff`, destructive flags such as `-rf`;
- write-capable: `touch`, `mkdir`, `cp`, `mv`, `tee`, `chmod`, `chown`, `git`, `npm`, `pip`, `uv`;
- network: `curl`, `wget`, `ssh`, `scp`, `ftp`, `nc`, `ncat`, `telnet`;
- unknown/unclassified commands.

Future expansion may add approval-gated write/network paths, but not in this pass.

## Approval requirements

The MVP blocks high-risk classes rather than pausing for approval. Future versions may emit approval requests through the existing ChaseOS approval store for write/network/destructive classes, but only after explicit implementation and tests.

## Audit logging and run history

Every executed or blocked step should carry:

- command;
- cwd;
- classification;
- return code when executed;
- stdout/stderr truncation flags;
- redaction posture;
- `untrusted_tier: Tier 4`;
- `terminal_output_trusted: false`.

Run history belongs in runtime/session artifacts and Agent-Activity logs, not canonical memory.

Run detail readback is also read-only. Audit JSON is loaded only by safe run id, surfaced with Tier 4/untrusted labels, and never treated as an instruction source.

## Output redaction and truncation

Terminal output is captured, redacted for simple secret-like patterns, and truncated before returning to callers. Redaction is a safety layer, not permission to expose secrets. API keys, tokens, passwords, cookies, and credentials remain forbidden terminal outputs for product UI.

## Kill/stop controls

Long-running PTY/process lifecycle and kill/stop controls are planned, not implemented in this MVP. Future process control must include:

- process ownership tracking;
- timeout and max output limits;
- operator-visible kill/stop button;
- audit event for kill/stop;
- no orphan process persistence.

## Studio panel contract

The Studio Terminal Workbench panel calls backend contracts that enforce the adapter policy. It shows:

- command proposal/classification before execution;
- cwd/workspace scope;
- approval requirements/block reasons;
- output cards labeled Tier 4 untrusted;
- redaction/truncation indicators;
- run history and audit links;
- kill/stop controls after process lifecycle is implemented.

Studio must not run shell commands from the frontend.

## CLI command contract

Current CLI namespace:

```text
chaseos operate terminal policy [--json]
chaseos operate terminal preview <command> [--cwd <path>] [--json]
chaseos operate terminal run <command> [--cwd <path>] [--timeout N] [--max-output N] [--actor NAME] [--json]
chaseos operate terminal history [--limit N] [--json]
chaseos operate terminal show <run_id> [--json]
```

Current truth: the CLI is wired for policy, preview, read-only run, history, read-only audit `show`, board proposal packets, terminal write approval requests, terminal write executor-readiness validation, the approval-gated `execute-terminal-approval` lane for `mkdir <target>`, `touch <target>`, `copy <source> <target>`, and `cp <source> <target>`, and N7 internal gateway ingress over those governed routes.

Current Chaser terminal audit contract:

```text
chaseos chaser terminal authority-audit [--vault-root <path>] [--json]
```

This reads contracts and denial paths only. It does not execute commands, queue approvals, consume approvals, write terminal audits, create exact-once markers, write Agent Bus tasks, call providers, mutate canonical state, upload externally, or create the probe target.

## Relationship to Hermes Gateway / WSL diagnostics

Hermes Gateway / WSL diagnostics are a read-only diagnostic direction for Terminal Workbench. Diagnostic cards may show WSL distro status, gateway config readiness, launcher/autostart readiness, last proof timestamp, and blocked start-plan steps. Starting/restarting gateways, creating startup items, changing Task Scheduler, mutating `.env`, or exposing credentials remains approval-gated and out of this pass.
