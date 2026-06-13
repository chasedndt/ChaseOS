# Studio Agent Bus Client Handover — Chat, Runtime Surfaces, and Passive Launch Boundary

**Date:** 2026-05-28  
**Runtime author:** Hermes / Optimus  
**Audience:** Hermes, OpenClaw, Archon/Claude Code, Codex/Axiom-Codex, Studio/UI developers  
**Status:** Implementation foothold added; further expansion should reuse the new Studio Agent Bus client seam.

## Executive Summary

Studio Chat must behave as an **Agent Bus client**, not as a provider client and not as a process launcher. The correct route is:

```text
Studio Chat UI
  -> Studio shell API
  -> runtime.studio.phase11_chat_send_message
  -> runtime.studio.agent_bus_client.StudioAgentBusClient
  -> runtime/agent_bus task packet
  -> selected runtime watch daemon claims task
  -> runtime-owned execution adapter / backend
  -> Agent Bus result_attached event
  -> Studio poll/readback renders reply
```

This preserves the Agent Control Plane boundary: Studio is an operator surface and request client; runtime daemons own execution. Studio must not call Anthropic/OpenAI/xAI/etc. directly for runtime replies, must not read runtime credentials, and must not spawn WSL/terminal windows just because the Chat page opened.

## What Changed In This Pass

### New reusable client seam

Added:

- `runtime/studio/agent_bus_client.py`

This module provides:

- `StudioAgentBusClient.create_task(...)` — writes a governed task packet to Agent Bus only.
- `StudioAgentBusClient.runtime_status(...)` — reads heartbeat/task state only; it does **not** launch WSL, spawn terminals, start daemons, or call providers.
- `resolve_recipient(...)` / `load_recipient_map(...)` — shared runtime selector -> Agent Bus recipient resolution.
- `derive_portable_vault_paths(...)` — derives WSL/Windows path hints from the selected vault root, avoiding Chase-local hard-coded paths in GitHub downloads.

### Chat send path now uses the shared client

Updated:

- `runtime/studio/phase11_chat_send_message.py`

The Chat send path still returns the same task metadata shape, but the Agent Bus write now goes through `StudioAgentBusClient`. This makes Chat the first consumer of a reusable Studio Agent Bus client seam rather than a one-off bus writer.

### Hermes live reply dispatch restored at runtime daemon layer

Updated:

- `runtime/workflows/hermes_watch.py`

`_hermes_runtime_chat(...)` now invokes:

```python
runtime.execution_adapters.execute.execute_synthesis(
    vault_root=vault_root,
    prompt_user=message,
    execution_adapter="hermes",
)
```

This is intentionally inside the Hermes watch/runtime-daemon layer, not inside Studio frontend/backend direct-provider code. Adapter failure still fails open to `None`, allowing the bus result path to attach a bounded backend blocker instead of crashing the watch loop.

### Passive launch / terminal-spam boundary

The new `runtime_status(...)` contract returns:

```json
"launch_policy": {
  "passive_status_only": true,
  "starts_wsl": false,
  "spawns_terminal": false,
  "starts_runtime_daemon": false,
  "provider_call_performed": false
}
```

This is the boundary other Studio surfaces should adopt when they merely need readiness/status. Opening Chat or other UI pages should read status, not invoke `wsl -d Ubuntu`, PowerShell `Start-Process`, gateway launchers, or daemon start commands.

## Repository Evidence Used

- `runtime/tests/test_chat_runtime_dispatch.py` defines the architecture rule: Studio Chat routes through Agent Bus; runtimes dispatch chat through `execute_synthesis()` and must not call provider URLs directly.
- `runtime/studio/phase11_chat_send_message.py` was the existing Chat -> Agent Bus task writer.
- `runtime/studio/phase11_chat_agent_bus_dispatch_bridge.py` is a separate approval-gated Chat -> Agent Bus/AOR bridge for workflow/runtime dispatch.
- `runtime/agent_bus/bus.py` is the public bus API and already supports task creation, heartbeat listing, and task polling.
- `runtime/workflows/hermes_watch.py`, `runtime/workflows/openclaw_watch.py`, and `runtime/workflows/archon_watch.py` are runtime-daemon-side task handlers.
- `runtime/studio/shell/frontend/app.js` calls Studio shell APIs for Chat send/poll and runtime controls; frontend should remain a client of backend contracts, not a launcher/provider surface.

## Should Agent Bus Client Capability Expand Beyond Chat?

Yes, but only as a bounded reusable backend seam. The repository already contains multiple Studio surfaces that need to ask runtimes to do work or read runtime state. Those surfaces should not each implement their own bus routing, WSL path handling, or launch-status behavior.

Recommended expansion path:

1. **Keep Chat as the first live consumer** of `StudioAgentBusClient`.
2. **Adopt the client for passive runtime readiness/status** wherever Studio currently reads Agent Bus heartbeats/tasks.
3. **Adopt the client for future runtime-bound Studio actions** that only need to create Agent Bus task packets.
4. **Do not use this client to bypass approval gates.** Approval-gated dispatch remains in `phase11_chat_agent_bus_dispatch_bridge.py` or future approval-specific bridge modules.
5. **Do not use this client to start daemons.** Runtime startup remains in Runtime Controls / lifecycle surfaces with operator approval and cooldowns.

Candidate future consumers:

- Chat runtime readiness strip / runtime selector.
- Runtime Control status cards that only need passive Agent Bus liveness.
- Future Studio task handoff panels that enqueue runtime work.
- Browser/Canvas/Graph/Pulse panels when they need runtime assistance, as long as they create bus tasks rather than local provider calls.

## Runtime Responsibilities

### Hermes

- Owns Hermes Chat synthesis after Agent Bus task claim.
- Must use Hermes execution adapter/backend configuration; Studio must not read Hermes credentials.
- Should attach `result_attached` events with user-visible reply text or a bounded blocker.

### OpenClaw

- Remains bus-dispatch-only for Chat unless/until a separate OpenClaw chat synthesis contract is approved.
- Should not be forced to provide direct Studio replies if its role is coordination/Windows runtime operations.

### Archon / Claude Code

- Uses Agent Bus recipient mapping through companion config where needed.
- Should not require Studio frontend changes to rename or retarget the recipient; use `.chaseos/companion_config.json` `recipient_names`.

### Codex / Axiom-Codex

- Studio currently uses Codex as sender identity for Chat task packets.
- Codex development lanes should treat `runtime/studio/agent_bus_client.py` as the shared client seam for future runtime-bound Studio requests.

## Do / Do Not Rules

Do:

- Use `StudioAgentBusClient.create_task(...)` for runtime-bound task packet writes.
- Use `StudioAgentBusClient.runtime_status(...)` for passive status/readiness.
- Keep path hints derived from the selected vault root.
- Keep provider calls inside runtime-owned adapters/daemons.
- Preserve `result_attached` polling for Chat readback.

Do not:

- Add provider URLs or provider SDK calls to Studio Chat frontend/backend for runtime replies.
- Start WSL, spawn terminals, or launch gateway processes on page open/status refresh.
- Hard-code `%USERPROFILE%` or `<WSL_WINDOWS_USER_HOME>` into portable GitHub-facing code.
- Treat Agent Bus task write as approval to mutate canonical knowledge.
- Let OpenClaw become an implicit provider chat runtime without a new contract.

## Verification Added / Run

New tests:

- `runtime/studio/test_agent_bus_client.py`
  - portable path derivation is not hard-coded to Chase's username,
  - recipient mapping is configurable,
  - runtime status is passive and does not launch WSL/terminals,
  - task creation routes through Agent Bus only.

Focused verification run results from this pass:

```text
PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uvx --with pyyaml pytest -q \
  runtime/studio/test_agent_bus_client.py -p no:cacheprovider

4 passed, 1 warning in 56.03s
```

```text
PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uvx --with pyyaml pytest -q \
  runtime/tests/test_chat_runtime_dispatch.py -p no:cacheprovider

16 passed, 1 warning in 126.80s
```

Additional bridge verification was partially run. The full bridge file is very slow on the Windows-mounted filesystem and hit a 300s timeout after printing four passing dots; the last bridge test was run individually and passed:

```text
runtime/studio/test_phase11_chat_agent_bus_dispatch_bridge.py::test_approved_dispatch_blocks_when_approval_lacks_request_binding
PASSED in 100.41s
```

## Known Follow-Ups

1. Wire Chat runtime readiness display to consume `StudioAgentBusClient.runtime_status(...)` directly where appropriate.
2. Audit other Studio pages for passive status reads that accidentally trigger launch/start behavior.
3. Move future runtime-bound Studio task creation onto `StudioAgentBusClient` instead of one-off `create_task(...)` calls.
4. Keep Runtime Controls as the only operator-approved daemon/gateway start surface.
5. Investigate pytest slowness on `/mnt/c` and cache behavior separately; verification succeeded with `-p no:cacheprovider`, but full combined runs are slow.

## Bottom Line

Studio Chat is now backed by an explicit reusable Studio Agent Bus client seam. This should be expanded beyond Chat for passive runtime state and runtime-bound task writes, but not for provider execution, WSL launch, gateway launch, approval consumption, or canonical mutation.
