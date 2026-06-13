# Studio Full Terminal Product Contract

Date: 2026-06-08
Runtime: Codex
Status: COMPLETE FOR HUMAN STUDIO TERMINAL FOUNDATION
Session descriptor: `terminal-full-studio-terminal-implementation`
Next pass: `terminal-n31-terminal-session-ui-hardening`

## N33 Correction Note (2026-06-08)

This contract has advanced. As of pass `terminal-n33-real-host-terminal-pty-implementation`:

- The human Studio terminal is now a **real interactive PTY/ConPTY terminal**, not a
  line-oriented subprocess command runner. Backend: `runtime/studio/terminal_pty.py`
  (ConPTY via `pywinpty` on Windows; stdlib `pty` on POSIX; legacy subprocess runner
  remains only as a documented non-interactive fallback when no PTY backend exists).
- Normal human commands (`cd`, `git`, `python`, `npm`, `wsl -d Ubuntu`, runtime gateway
  commands, etc.) are **not artificially blocked**. The old narrow approval-gated
  mkdir/touch/copy/cp lane and the governed CLI preview/run/history/show lane remain
  separate and unchanged.
- `wsl -d Ubuntu` launches WSL Ubuntu from inside the Studio terminal (verified on host).
- **Runtime naming corrected:** the established 24/7 runtime lanes are **ChaserAgent,
  Hermes, OpenClaw**. There is no OpenCore runtime lane; OpenCore was removed from all
  live terminal registries/contracts. ChaserAgent's real surface is the repo CLI
  (`chaseos chaser ...`, e.g. `chaseos chaser gateway diagnose`); it remains
  non-executable/non-autonomous.
- Authority boundaries unchanged: no ChaserAgent terminal binding, no Agent Bus mutation,
  no provider/model dispatch, no approval consumption, no canonical writeback, no host
  elevation. Terminal output remains Tier 4 untrusted. Workbench remains read-only.

## Purpose

The terminal track has been redirected from premature ChaserAgent terminal binding to the human-operated Studio full terminal foundation. The repo now has a mounted `#/terminal` route, a real interactive PTY session backend, Studio API lifecycle, slash-command registry, preview-only agent launcher registry, and JSONL session audit.

This is a human operator terminal lane, not a ChaserAgent runtime binding. On Windows the backend uses ConPTY (`pywinpty`); on POSIX it uses the stdlib `pty`. The legacy audited PowerShell subprocess model is retained only as a fallback when no interactive PTY backend is present.

## Implemented Contract

- Python contract builder: `runtime/studio/terminal_product_contract.py`.
- CLI readback: `chaseos studio terminal-product-contract --json`.
- Studio API readback: `StudioAPI.get_studio_terminal_product_contract()`.
- Studio panel registry entry: mounted operator-control `terminal` route at `#/terminal`.
- Session backend: `runtime/studio/terminal_sessions.py`.
- Slash registry: `runtime/studio/terminal_slash_commands.py`.
- Agent launcher registry: `runtime/studio/terminal_agent_launchers.py`.
- Chaser readiness/gate metadata now defers terminal toolset binding until the human Studio terminal foundation exists.

## Product Lanes

The contract separates these lanes:

- `human_studio_terminal`: mounted bounded human-facing Studio terminal.
- `governed_cli_command_runner`: existing bounded operator command runner.
- `future_agent_tool_terminal`: deferred ChaserAgent terminal tool lane.
- `agent_bus_mutation`: deferred and blocked.
- `provider_model_dispatch`: deferred and blocked.

## Policy Modes

The future terminal must distinguish:

- `view_only`
- `governed_command`
- `full_operator_terminal`
- `agent_tool_terminal`

The `full_operator_terminal` mode is active for the human Studio page only. Agent/tool terminal mode remains inactive.

## Backend API

Studio mounts these session backend methods:

- `create_terminal_session`
- `list_terminal_sessions`
- `get_terminal_session`
- `read_terminal_output`
- `write_terminal_input`
- `resize_terminal_session`
- `interrupt_terminal_session`
- `terminate_terminal_session`
- `close_terminal_session`

These methods are for human operator sessions only and are not exposed as ChaserAgent tools.

## Slash And Launcher Direction

The slash-command registry is implemented for help, clear/history/session commands, policy/audit/readback commands, Chaser read-only status commands, and agent launcher preview commands. Launcher entries for Hermes, OpenCore/OpenClaw, and Chaser preview remain preview-only and grant no provider, Agent Bus, terminal-tool, or ChaserAgent autonomy authority.

## Authority Boundaries

The current boundary preserves:

- no Workbench execution;
- no ChaserAgent terminal binding;
- no terminal-to-Chaser adapter;
- no Agent Bus write/claim/update;
- no provider/model/connector call;
- no approval request write;
- no approval consumption;
- no canonical truth mutation;
- no external gateway or upload.

## Verification

Focused tests passed for terminal sessions, Studio API/contract, frontend mount, Chaser authority/readiness, Terminal Workbench regressions, terminal operator surfaces, and compileall. The session backend test verified create/write/read/terminate lifecycle and JSONL audit creation under a temp vault.

Live diagnostics still surface pre-existing invalid Strikezone schedule warnings unrelated to this terminal pass.
