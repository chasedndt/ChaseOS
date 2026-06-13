---
title: Agent Bus Backend Architecture
status: active
phase: 9
version: 1.0
created: 2026-04-26
---

# Agent Bus Backend Architecture

> **One-line summary:** The ChaseOS agent coordination bus is backed by a pluggable storage
> layer. Local deployments use SQLite (zero infrastructure). Server deployments will use a
> live HTTP/WebSocket server (Phase 10). All handlers, workflows, and the AOR engine are
> backend-agnostic — they never touch storage directly.

---

## Why This Exists

The original agent bus spoke SQLite directly in `bus.py`. That works perfectly for a single
machine. But ChaseOS is heading toward:

- **Multi-machine deployments**: OpenClaw running on a VPS, Hermes on a local machine, both
  sharing the same task bus
- **Mobile and web dashboards**: Live push updates (WebSocket), not file polling
- **Multi-user / multi-tenant**: Different users running ChaseOS instances that coordinate
  through a shared server

SQLite cannot be shared over a network. Introducing the backend abstraction **now** means
the server backend can be dropped in later (Phase 10) with **zero changes** to handlers,
workflows, or the AOR engine. Only `bus_config.yaml` and `backend_loader.py` change.

This is the distinction between a capability that grows with you and one that forces a
rewrite when you outgrow it.

---

## The Two Modes

### Local Mode (default)

```yaml
# runtime/agent_bus/bus_config.yaml
mode: local
```

- **Storage**: SQLite file at `runtime/agent_bus/agent_bus.sqlite` in the vault
- **Infrastructure**: None. Zero setup. Works offline.
- **Concurrency**: WAL mode — concurrent reads, serialized writes. Sufficient for 2-10
  runtimes on one machine.
- **Who should use this**: Personal deployments, development, testing, any setup where all
  runtimes live on one machine.
- **Limitations**: Cannot be shared across machines. No real-time push. No auth layer.

### Server Mode (Phase 10)

```yaml
# runtime/agent_bus/bus_config.yaml
mode: server
server:
  api_url: http://localhost:8765
  websocket_url: ws://localhost:8765/ws
  api_key_env: CHASEOS_BUS_API_KEY
```

- **Storage**: ChaseOS server process (HTTP REST + WebSocket)
- **Infrastructure**: A running `chaseos server` process; a Postgres or SQLite-over-network
  database on the server
- **Concurrency**: Handled by the server process — N runtimes on N machines
- **Who should use this**: VPS deployments, multi-machine setups, web/mobile dashboards,
  multi-user scenarios
- **Status**: **Not yet implemented.** Phase 10. Selecting `mode: server` raises
  `NotImplementedError` with a clear message. This is intentional — silent fallback to local
  mode would cause tasks to land in a local SQLite file that the server never sees.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Handlers / Workflows / AOR Engine / CLI                    │
│  (never touch storage directly)                             │
├─────────────────────────────────────────────────────────────┤
│  bus.py  —  Public API                                      │
│  Validation (runtime names, intent, priority ceiling)       │
│  ID + timestamp generation                                  │
│  Orchestration (watch_once, run_watch_loop)                 │
├─────────────────────────────────────────────────────────────┤
│  backend_loader.py  —  Config reader + cache                │
│  Reads bus_config.yaml → instantiates + caches BusBackend  │
├─────────────────────────────────────────────────────────────┤
│  BusBackend (ABC)  —  The contract                          │
│  backends/base.py                                           │
├──────────────────────┬──────────────────────────────────────┤
│  SQLiteBackend        │  ServerBackend (Phase 10)           │
│  backends/            │  backends/                          │
│  sqlite_backend.py    │  server_backend.py (not yet built)  │
│                       │                                     │
│  Local SQLite file    │  HTTP REST + WebSocket              │
│  Zero infrastructure  │  Multi-machine, live push, auth     │
└──────────────────────┴──────────────────────────────────────┘
```

---

## How the Backend Is Selected

1. `bus.py` calls `get_backend(vault_root)` on every storage operation
2. `backend_loader.get_backend()` checks its per-vault cache
3. On first call: reads `{vault_root}/runtime/agent_bus/bus_config.yaml`
4. Instantiates the backend declared in `mode`, calls `backend.init()`, caches it
5. Subsequent calls return the cached instance (no re-read, no re-init)

**If `bus_config.yaml` is missing**: defaults to `mode: local` (SQLiteBackend). Existing
vaults without the config file continue to work unchanged.

**If the config is corrupt**: falls back to `mode: local`. A bad config should not prevent
local workflows from running.

**If `mode: server`**: raises `NotImplementedError`. No silent fallback — see rationale above.

---

## The BusBackend Contract

Every backend must implement all methods declared in `backends/base.py`. The full method
list with documented semantics:

| Method | Description |
|--------|-------------|
| `init()` | Initialize storage. Idempotent. Raises `BackendInitError` on failure. |
| `create_task(...)` | Persist a new task + creation event. Returns `{'created': bool, ...}`. |
| `list_tasks(...)` | List tasks with optional filters. Returns list ordered by `created_at ASC`. |
| `get_task(task_id)` | Return single task or `None`. |
| `claim_task(..., lane_guard=None, runtime_instance_id=None)` | Atomically claim an open task while enforcing lane arbitration and persisting instance ownership. Returns `{'claimed': bool, ...}`. |
| `update_task_status(...)` | Update status + append event. Returns `{'updated': bool, ...}`. |
| `upsert_heartbeat(...)` | Insert or update runtime liveness record. |
| `list_heartbeats()` | Return all current heartbeat records. |
| `mark_stale_tasks(...)` | Expire tasks from stale runtimes. `stale_runtimes` is pre-computed by caller. |
| `reclaim_task(...)` | Re-open a task from a stale runtime. Does not check staleness itself. |

**Key design decisions:**

- `vault_root` is injected at **construction time**, not per-call. Methods receive only the
  data they need. Server backends ignore the local filesystem entirely.
- **ID generation** happens in `bus.py` before the backend is called. Backends receive
  fully-formed `task_id` and `run_id`. This keeps ID format consistent across backends.
- **Staleness determination** happens in `bus.py` (via the router), not the backend.
  `mark_stale_tasks()` receives a pre-computed `stale_runtimes` set.
- **Claim atomicity**: `claim_task()` must be atomic. Two runtimes racing to claim the same
  task must result in exactly one winner. SQLite handles this via WAL + exclusive write lock.
  Server backends must implement compare-and-swap or a serialized endpoint.
- **Claim lane arbitration**: the same serialized claim path must reject a task when the
  runtime already owns active work in the same `work_fingerprint`, `origin_message_id`, or
  `conversation_key` lane. SQLite now enforces this under `BEGIN IMMEDIATE`; Phase 10 server
  endpoints must enforce the same rule server-side, not only in the client-side `bus.py`
  preflight.
- **Runtime-instance ownership**: task ownership is `owner` plus nullable `owner_instance`.
  The runtime remains the authority boundary; the instance identifies the control-surface lane
  such as `discord-thread-1496197360382906400` for thread work or
  `discord-channel-1493226873080119397` for shared channel-level work. Server backends must persist
  the same field and keep it aligned with instance-scoped heartbeat identity.

---

## Adding a New Backend

1. Create `runtime/agent_bus/backends/your_backend.py`
2. Subclass `BusBackend` and implement all abstract methods
3. Add a branch in `backend_loader._instantiate_backend()`:
   ```python
   if mode == "your-mode":
       from .backends.your_backend import YourBackend
       backend = YourBackend(vault_root, config.get("your-mode") or {})
       backend.init()
       return backend
   ```
4. Document the config block in `bus_config.yaml`
5. Run `pytest runtime/agent_bus/test_backend_abstraction.py` — all contract tests must pass
   against your backend (parameterize the `sqlite_backend` fixture to yield your backend)
6. Update this document

---

## Contract Test Suite

`runtime/agent_bus/test_backend_abstraction.py` contains the backend contract tests organized as:

- `TestBusBackendContract` — all operations via the BusBackend interface (backend-agnostic)
- `TestBackendLoader` — config reading, caching, mode selection, error handling
- `TestSQLiteBackendSpecific` — SQLite-only internals (db_path, file creation, BackendInitError)

Any new backend must pass `TestBusBackendContract` in full. `TestSQLiteBackendSpecific`
tests are SQLite-specific and do not need to pass for other backends.

---

## Migration (Local → Server)

When a user switches from local to server mode on an existing vault:

1. Change `mode: local` → `mode: server` in `bus_config.yaml`
2. Configure the `server:` block (api_url, api_key_env)
3. **Existing SQLite tasks are NOT automatically migrated** — they remain in the local file
4. Run `chaseos agent-bus migrate` (Phase 10, not yet built) to move historical tasks to
   the server if needed, or accept that historical tasks stay local-only

This is intentional: migration is a destructive operation that should require explicit
operator action, not happen silently on config change.

---

## Relationship to Other Docs

| Document | Relationship |
|----------|-------------|
| `runtime/agent_bus/Agent-Bus-Folder-Guide.md` | Folder structure and CLI commands |
| `06_AGENTS/Runtime-InterAgent-Coordination-Bus.md` | Bus design, routing layer, runtime declarations |
| `runtime/agent_bus/backends/base.py` | Live contract definition (source of truth) |
| `runtime/agent_bus/backend_loader.py` | Config loading and instantiation logic |
| `runtime/agent_bus/bus_config.yaml` | Per-vault mode configuration |

---

*Version 1.0 — Created 2026-04-26 — Phase 9 backend abstraction pass*
*Next: Phase 10 — ServerBackend implementation (HTTP/WebSocket, Postgres, auth)*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
