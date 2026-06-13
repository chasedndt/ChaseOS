# board.py Orchestration Board — Integration Deep Dive

Date: 2026-06-03 (N5 read-only state, pre-N6 proposal packets, N6A approval requests, N6R executor readiness, initial N6 CLI executor, N7 internal gateway ingress, N9 approved file-create, N10 approved file-copy, N11 read-only Studio dashboard, and N12 source visual QA built 2026-06-06)
N5/N6A/N6R/N6/N7/N9/N10/N11/N12 current status: PARTIAL - `runtime/chaser/board.py` read-only state aggregator, terminal command proposal packets, terminal write approval-request queue front half, terminal write executor-readiness validation, the dedicated N6 CLI executor with approved `mkdir`/`touch`/`copy`/`cp` verbs, the internal N7 gateway facade, the read-only Studio Chaser Board dashboard, and source-rendered visual QA proof are built; broader write/content verbs, network gateway ingress, Agent Bus mutation, packaged/native Chaser Board proof, and ChaserAgent live runtime wiring remain planned
Runtime: Archon (claude-code); N5 implementation: Codex
Status: PARTIAL - read-only state aggregation, terminal command proposal packet construction, gated approval-request queue writing, no-execution terminal executor-readiness validation, the approved `mkdir`/`touch`/`copy`/`cp` CLI executor, N7 internal gateway ingress routing, and the N11 read-only Studio dashboard are built; broader live gateway/runtime work remains planned
Source books: `247 Agent Harness engineering V0.md` §9, `deep-research-report.md`
Related: [[Chaser-Gateway-Architecture]] · [[ChaserAgent-Architecture]] · [[Terminal-ChaserAgent-Agent-Bus-Handover]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Autonomous-Operator-Runtime]] · [[Scheduled-Briefing-Pipelines]]

## 0. What board.py is (and is not)

You asked: *"board.py could wire in with our other features and deep dive what it could work with."* Per the handoff, `board.py` is the **operator-visible orchestration board** that aggregates the live state of runtimes, terminal runs, approvals, and agent tasks into a single read surface, and proposes (never executes) bounded actions.

It **is**: a read-and-propose aggregator + card builder.
It **is not**: an autonomous brain, a scheduler, a second source of truth, or anything that applies changes without the AOR/Gate/approval path.

The books are explicit: "`board.py` should not be a magical autonomous brain." It builds board state; execution still flows through governed adapters.

## 1. The board's data sources (what it READS)

Each board card type is built by reading an existing ChaseOS subsystem. board.py imports these read surfaces; it does not duplicate their logic.

| Card type | Reads from (existing) | Produces |
|---|---|---|
| `runtime_health` | `runtime/studio/runtime_cockpit.py` (`_runtime_health`, `_bus_heartbeat_state`), `list_heartbeats()` | per-runtime live/degraded/stale cards |
| `terminal_run` | `runtime/operator_surface/terminal_runs.py` (`list_terminal_runs`) | recent command preview/run/blocked cards |
| `approval` | `runtime/studio/service.py` approval queue + AOR OSRIL approvals | pending-approval cards |
| `agent_task` | Agent Bus (`list_tasks`, `list_events`) | created→claimed→done task cards |
| `build_pass` | `07_LOGS/Build-Logs/`, `07_LOGS/Agent-Activity/` | current pass / modified files / next handoff |
| `evidence` | `07_LOGS/` (Terminal-Runs, Agent-Activity, Decision-Ledger) | audit/diagnostic/readiness artifacts |
| `schedule` | `runtime/schedules/loader.py` (`list_schedules`) | scheduled intent cards (read-only) |
| `gateway_diag` | Chaser Gateway Diagnostic (built, [[Chaser-Gateway-Architecture]] §6) | readiness + repair-plan cards |

All reads are fail-open: a missing/unreadable source yields an empty card section, never a board crash.

## 2026-06-06 N5 implementation truth

`runtime/chaser/board.py` now exposes `build_board_state(vault_root, limit=8, include_gateway=True)`.

Built read-only cards:

- `terminal_run` from `runtime/operator_surface/terminal_runs.py`;
- `approval` from `runtime/studio/service.py` pending approvals;
- `agent_task` and `runtime_health` from an already-initialized Agent Bus only;
- `schedule` from `runtime/schedules/loader.py`, including validation warnings;
- `gateway_diag` from `runtime/chaser/gateway_diagnostic.py`.

Surfaces:

- CLI: `chaseos chaser board state [--limit N] [--skip-gateway] [--json]`;
- Studio API: `StudioAPI.get_chaser_board_state(limit=8)`.

N5 originally did **not** build proposal packets, did not execute card actions, and did not add a Studio dashboard panel. If no Agent Bus SQLite DB exists, the board reports `agent_bus:not_initialized` and does not materialize storage.

2026-06-06 pre-N6 correction: proposal packets are now built for terminal command classification/readiness only. `build_action_proposal()` returns `preview_allowed`, `approval_required_future_n6`, or `blocked` packets through CLI/API without executing commands, writing approvals, consuming approvals, creating Agent Bus tasks, calling providers, or mutating canonical state. Execution routing remained planned at that point; the read-only Studio visual dashboard was completed later in N11.

2026-06-06 N6A correction: approval-request queue writing is now built for eligible N6 write-command proposals only. `build_terminal_write_approval_request()` previews by default and writes a pending Studio approval only when the CLI/API caller explicitly requests it. Ambient `StudioService.execute_approved()` is blocked for those approval records; only the dedicated N6 CLI executor may consume them. No terminal execution, approval consumption, Agent Bus write, provider call, or canonical mutation is added by the request path itself.

2026-06-06 N6R correction: terminal write executor-readiness validation is built as a separate no-execution surface. `runtime/chaser/terminal_write_executor_readiness.py` validates approved terminal write approval requests against exact approval/proposal/cwd/classification/metadata/marker requirements, but it does not reserve markers, consume approvals, write terminal audit records, execute commands, write Agent Bus tasks, call providers, or mutate canonical state. Structurally valid approved requests now report `ready_for_executor` for the dedicated CLI lane.

2026-06-06 N10 correction: the dedicated N6 CLI executor is built in `runtime/chaser/terminal_write_executor.py`. It consumes one approved terminal write approval with explicit CLI confirmation, reserves an exact-once marker before mutation, supports only `mkdir <target>`, `touch <target>`, `copy <source> <target>`, and `cp <source> <target>` inside the vault, writes a terminal run audit, updates the approval status, and duplicate-blocks. The board remains a proposal/read surface; Agent Bus dispatch, provider calls, canonical writeback, unrestricted shell, shell operators, elevation, arbitrary content-writing terminal lanes, and ChaserAgent runtime activation are still not added.

2026-06-06 N11 correction: Studio now mounts a read-only Chaser Board dashboard at `#/chaser-board` over `StudioAPI.get_chaser_board_state()`. The dashboard renders existing board cards and selected-card detail only; it adds no execution, approval consumption, approval request write, Agent Bus write, provider call, canonical mutation, or live ChaserAgent wiring.

2026-06-06 N12 correction: the source-rendered Chaser Board dashboard now has dedicated Playwright visual QA in `runtime/studio/chaser_board_product_visual_qa.py`. The harness allows only `get_chaser_board_state`, captures desktop/mobile screenshots, verifies selected-card detail and read-only/Tier 4/authority copy, and verifies forbidden execution API copy is absent. This is not packaged/native proof and does not add execution, approval writes/consumption, Agent Bus writes, provider/connector calls, canonical writeback, host mutation, or live ChaserAgent wiring.

2026-06-06 N13 correction: packaged/native Chaser Board proof is not complete. `runtime/studio/chaser_board_packaged_visual_qa.py` now exists and live proof launched the current packaged executable, but the package did not mount `#/chaser-board` and stayed on `panel-dashboard`. Treat N13 as a packaged proof harness plus stale-package finding until package rebuild recovery succeeds and the proof is rerun.

2026-06-06 N7 correction: `runtime/chaser/gateway.py` now provides an internal structured ingress facade over the board/proposal/approval/readiness/N6 executor contracts. The facade requires local-operator confirmation for every request, separate confirmation for approval queue writes, and separate approved-terminal-write confirmation for execution. It is not a network server and does not add Studio execution, Agent Bus task writes, provider calls, canonical writeback, external upload, ChaserAgent runtime/profile/toolset activation, unrestricted shell, shell operators, or elevation.

## 2. What the board can PROPOSE (and how it is gated)

A board action is a **proposal packet**, not an execution. The flow (from the handoff sequence diagram, adapted to ChaseOS):

```
Studio/CLI → board.build_action_proposal(card, action)
           → Gate / Permission-Matrix policy check  →  allowed | approval_required | blocked
           → proposal packet returned (NOT executed)
operator confirms (if required)
           → execution ONLY through the governed adapter (TerminalAdapter / AOR workflow / approval service)
           → adapter writes audit evidence
           → board re-reads sources and updates the card
```

Proposal actions map to existing governed executors — the board never gets its own execution path:

| Board action | Routes to (governed) |
|---|---|
| "Run diagnosis" | Chaser Gateway Diagnostic (read-only) |
| "Preview command" | `TerminalAdapter.classify_command` (no execution) |
| "Run command" | `chaseos operate terminal run` / TerminalAdapter (read-only, audited) |
| "Approve/deny" | `runtime/studio/service.py` approval queue |
| "Dispatch task" | Agent Bus `create_task` (under bus router caps) |
| "Run workflow" | AOR `engine.run_workflow` (manifest + role card + ceiling) |

## 3. Board state schema (planned)

```json
{
  "board_id": "chaseos_main_board",
  "updated_at": "<iso>",
  "mode": "operator",
  "authority_summary": {
    "terminal": "adapter_gated_read_only",
    "runtime": "diagnostic_only",
    "canonical_writes": "approval_required",
    "provider_calls": false
  },
  "cards": [ { "card_id": "...", "type": "runtime_health|terminal_run|approval|agent_task|schedule|gateway_diag|evidence|build_pass",
               "title": "...", "status": "...", "summary": "...",
               "actions": [ { "label": "...", "action_type": "...", "requires_approval": false } ],
               "evidence_paths": [] } ]
}
```

## 4. Where board.py sits in the package

```text
runtime/chaser/
  board.py     # PLANNED — read aggregator + proposal builder (this doc)
  sessions.py  # BUILT — board reads session list for session cards
  exports.py   # BUILT — board "export" action routes here
  models.py    # BUILT — board may reuse ArtifactRef/TerminalRun models
  gateway.py   # BUILT PARTIAL — internal N7 ingress facade exposes governed board/terminal routes
```

2026-06-06 correction: `board.py` is no longer only planned. It is PARTIAL: read-only state aggregation, terminal command proposal packets, N6A approval-request queue writing, N6R readiness, N6 CLI executor contract visibility, N7 gateway routing, and the N11 read-only Studio dashboard are built, while broader execution verbs and live runtime wiring remain planned.

Studio can read the board via `StudioAPI.get_chaser_board_state()`, mirroring `get_terminal_workbench`. The board is also reachable from the CLI as `chaseos chaser board state`. The N11 visual Studio dashboard is now mounted read-only at `#/chaser-board`.

## 5. Build sequence for board.py (when claimed — unit N5 in the handover)

1. **DONE 2026-06-06:** Read-only board first: aggregate runtime_health + terminal_run + approval + agent_task + schedule + gateway diagnostic cards from existing sources. No proposals yet. Test each card builder against fixtures.
2. **DONE 2026-06-06:** Proposal packets second: `build_action_proposal` returns `preview_allowed` / `approval_required_future_n6` / `blocked` from TerminalAdapter policy/classification — still no execution and no approval writes.
3. **DONE 2026-06-06 FOR REQUEST QUEUE ONLY:** Approval-request queue front half: eligible write-command proposals can create pending Studio approvals, but ambient execution is blocked.
4. **DONE 2026-06-06 FOR READINESS ONLY:** Executor-readiness validation: approved terminal write approvals can be checked for exact metadata/scope/marker blockers, but no marker, approval consumption, terminal audit, or command execution is performed.
5. **DONE 2026-06-06 FOR INITIAL CLI LANE:** route approved proposals to the dedicated governed terminal executor through `terminal_write_executor.py` and the N7 gateway wrapper. Never add an unrestricted execution path inside board.py.
6. **PARTIAL 2026-06-06:** CLI/API read surfaces exist (`get_chaser_board_state()` + `chaseos chaser board state`) and Studio mounts `#/chaser-board` read-only. Write-capable dashboard actions remain planned/gated.

## 6. Governance invariants for board.py

1. The board reads many subsystems but **owns none** of them — no duplicated policy, no cached authority.
2. A card action is a proposal until an operator (or an approval record) authorizes it.
3. Execution always flows through an existing governed adapter that writes its own audit.
4. The board never calls a model provider and never writes canonical truth.
5. The board's `authority_summary` must always reflect the real ceilings, never an optimistic claim.
