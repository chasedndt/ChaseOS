# ChaserAgent Architecture

Date: 2026-06-02
Runtime: Hermes/Optimus
Status: PARTIAL / CORE FOUNDATION / NOT LIVE
Source handoff: [[ChaseOS_Terminal_ChaserAgent_Fullstack_Implementation_Handoff_v2]]
Related: [[Terminal-ChaserAgent-Feature-Matrix]] Â· [[Terminal-Workbench-Architecture]] Â· [[Session-Export-and-Artifacts-Architecture]] Â· [[HERMES]] Â· [[Hermes-Runtime-Profile]] Â· [[Agent-Activity-Index]]

## Position

ChaserAgent starts inside ChaseOS Core first. It is not a new autonomous repo, not a Hermes clone, not a provider wrapper, and not a second source of truth.

Correct ownership model:

```text
ChaseOS Core
  owns ChaserAgent, Gate, AOR/runtime governance, policies, terminal policy,
  session/export/artifact truth, memory/bootstrap boundaries, and board contracts.

ChaseOS Backend
  exposes safe API contracts over ChaseOS Core.

ChaseOS Studio / frontend
  displays product surfaces over those contracts.

Future external ChaserAgent repo
  allowed only after stable internal contracts are implemented and tested.
```

Hermes Desktop is a reference pattern for â€œone agent core, many surfaces, shared state.â€ It is not the authority model for ChaseOS.

## Authority model

ChaserAgent is a bounded planner / proposer / coordinator inside ChaseOS. It may produce proposals, task packets, patch artifacts, risk notes, runtime cards, session exports, terminal previews, and completion evidence.

ChaserAgent must not by itself:

- Own canonical truth.
- Bypass ChaseOS Gate.
- Mutate protected docs.
- Execute unrestricted shell commands.
- Grant itself profile/toolset authority.
- Access credentials directly.
- Promote memory/bootstrap files into permissions.
- Treat terminal output or external content as trusted instructions.

Profiles, toolsets, persona files, and bootstrap/memory files are configuration and context surfaces. They do not create permissions by themselves. Authority remains with ChaseOS Gate, Permission Matrix, Trust Tiers, AOR manifests, operator approvals, and audited writeback.

## Target internal module

Planned location:

```text
runtime/chaser/
  __init__.py
  agent.py              # bounded ChaserAgent core interface
  board.py              # orchestration board contracts
  models.py             # task/session/artifact/proposal models
  policies.py           # policy adapters over ChaseOS policy/Gate surfaces
  profiles.py           # profile views/config, not authority grants
  memory.py             # bootstrap/context references, not permission grants
  toolsets.py           # toolset configuration views and proposal routing
  sessions.py           # session metadata and management contracts
  exports.py            # session export contracts
  artifacts.py          # artifact manifests and provenance references
```

The 2026-06-02 pass documented the contract and started the TerminalAdapter foothold. The 2026-06-03 pass created `runtime/chaser/` with the first three core modules (`models.py`, `sessions.py`, `exports.py`) plus tests - the session-export backend slice. The 2026-06-06 Phase A pass added preview/contract modules (`agent.py`, `board.py`, `policies.py`, `profiles.py`, `memory.py`, `toolsets.py`, and `artifacts.py`). Later 2026-06-06 passes added the Studio chat -> `SessionRecord` export adapter, the N5 read-only board state aggregator, pre-N6 terminal command proposal packets, the N6A terminal write approval-request front half, the N6R terminal write executor-readiness contract, the N6 gated CLI executor, N9/N10 approved file operations, the N7 internal gateway ingress facade, the N11 read-only Studio Chaser Board dashboard, and N12 source-rendered Chaser Board visual QA. These modules produce previews, policy snapshots, board cards, proposal packets, approval requests, readiness validations, profile/toolset views, memory-boundary previews, artifact manifests, session exports, read-only board state, one narrow approved terminal write lane for `mkdir`/`touch`/`copy`/`cp`, an internal structured ingress wrapper over governed routes, a Studio readback dashboard, and source visual evidence. They do not activate ChaserAgent, claim or write Agent Bus tasks, call providers, execute unrestricted tools/shell, write memory, or mutate canonical state.

## `board.py` / orchestration-board target

The board is a runtime coordination surface, not memory ownership. It should model:

- task ID, origin, operator intent, target workspace/session;
- proposed runtime/profile/toolset;
- required authority and approval state;
- result type: proposal, patch, proof, risk, blocked, complete;
- evidence/artifact/session links;
- audit/log references;
- blocked lower-phase dependency reports.

The board may expose cards in Studio and backend APIs. It must not apply changes without the appropriate AOR/Gate/writeback path.

## Surface split

| Surface | Role | Not allowed |
|---|---|---|
| Core | Owns ChaserAgent contracts, policies, Gate/AOR integration, sessions, exports, artifacts | Become an uncontrolled provider/runtime bypass |
| Backend | Serves safe APIs over Core | Own truth or raw shell execution |
| Studio | Displays Terminal Workbench, Runtime Console, Artifacts, Sessions, Profiles, Toolsets, Settings | Mutate protected truth directly |
| Messaging/future surfaces | Submit operator intents and display results | Become separate `DiscordAgent`/`StudioAgent` brains |

## Implementation sequence

1. Keep ChaserAgent architecture internal-core-first.
2. Finish TerminalAdapter policy/executor/CLI wiring before building terminal UI.
3. Add session export/artifact backend contracts before UI context menus claim export readiness.
4. Extend `runtime/chaser/board.py` beyond Phase A previews only after task/proposal/evidence schemas are stable and approval/write paths are defined. N5 read-only board state, pre-N6 terminal command proposal packets, N6A terminal write approval-request queueing, N6R executor-readiness validation, the N6 CLI approval consumer with approved `mkdir`/`touch`/`copy`/`cp` verbs, N7 internal gateway ingress, N8 authority audit, and N11 Studio read-only dashboard are now built; Agent Bus routing, broader write/content verbs, network gateway ingress, and live ChaserAgent runtime wiring remain future work.
5. Add Studio/Backend surfaces over those contracts. The N5 backend/API/CLI board read surface exists, N11 mounts the read-only Studio visual dashboard, and N12 verifies the source-rendered dashboard visually. N13 added a packaged proof harness, but current packaged/native dashboard proof is PARTIAL because the executable does not mount `#/chaser-board`; package rebuild recovery and write-capable dashboard actions remain planned/gated.
6. Consider external repo split only after stable internal APIs and tests exist.

## Current truth (updated 2026-06-06)

- ChaserAgent core exists as a partial foothold: `runtime/chaser/` has session/export models, audited session metadata lifecycle, a Studio chat export adapter, no-authority preview helpers, and read-only board state.
- `agent.py` remains a Phase A preview/contract module only. `board.py` now has read-only state aggregation, card contracts, terminal command proposal packets, and terminal write approval-request queueing, with terminal write executor-readiness validation in `terminal_write_executor_readiness.py`, the CLI-only N6 consumer in `terminal_write_executor.py` for approved `mkdir`/`touch`/`copy`/`cp`, and N7 routing in `gateway.py`. The board itself does not execute, dispatch, write Agent Bus tasks, consume approvals, or mutate canonical state.
- TerminalAdapter is a partial bounded MVP scaffold under `runtime/operator_surface/`.
- Session export backend is implemented (markdown/json, redaction, manifests, audit, no external upload); session metadata lifecycle is implemented for pin/unpin, rename, and archive-first active-store removal; Studio chat export CLI is implemented; generic session export CLI and Studio export UI remain planned.
- ChaserAgent holds no Gate-bypass, no canonical-write, and no shell-execution authority. The export backend performs no network I/O and no command execution.
- Hermes remains a reference pattern under ChaseOS Gate.
