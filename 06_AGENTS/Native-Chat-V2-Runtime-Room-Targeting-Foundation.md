# Native Chat V2 - Runtime Room Targeting Foundation

Status: VERIFIED SOURCE UI PASS
Date: 2026-06-06
Runtime: Codex

## Scope

This pass is Chat-first. It does not implement a full unified Runtime Control Plane, Runtime Cockpit redesign, Agent Bus redesign, Tasks & Runs redesign, Approval Center redesign, runtime start/stop, approval execution, provider calls, shell expansion, canonical memory mutation, secrets access, cross-user messaging, or enterprise sharing.

## Implemented

- Primary runtime target chips now live inside the Chat composer.
- Runtime selection resolves in this order:
  - existing chat-specific saved runtime targets
  - existing chat runtime id when no multi-target override exists
  - workspace last-used runtime targets
  - Hermes if available
  - no runtime selected
- Canonical Chat roster:
  - `hermes` / Hermes
  - `openclaw` / OpenClaw
  - `chaser-agent` / Chaser Agent, locked
- Chaser Agent is visible but not selectable. Disabled reason: Runtime adapter not installed yet.
- No-runtime selection disables the composer and send button.
- Chat send passes the Native Chat V2 payload shape:

```json
{
  "targetRuntimeIds": ["hermes", "openclaw"],
  "dispatchMode": "fanout"
}
```

- The backend keeps the existing governed Studio Chat Agent Bus path and creates fanout tasks only for selectable targets.
- The Chat timeline remains limited to messages and compact event/action cards. Full runtime/companion cards are not rendered into the default Chat timeline.
- Runtime/companion detail lives in a Chat-scoped right overlay drawer.
- The drawer opens from composer runtime controls and companion presence chips, closes on Escape, backdrop click, and X, and does not use the default inspector rail.
- Companion presence is chip-level only in the default Chat page.
- Folder/chat right-click actions remain separated from runtime drawer actions.
- Delete feedback uses a floating toast outside the timeline.

## Verified

Source visual QA verified 10 screenshot states:

- default Chat view
- Hermes only selected
- OpenClaw only selected
- Hermes + OpenClaw selected
- no runtime selected with composer disabled
- Chaser Agent locked
- runtime drawer open
- folder deleted toast
- narrow width
- inspector open class state
- inspector closed class state

Evidence:

- `07_LOGS/Visual-QA/2026-06-06-native-chat-v2-runtime-room-targeting-foundation/studio-chat-management-controls-visual-qa.json`
- `07_LOGS/Visual-QA/2026-06-06-native-chat-v2-runtime-room-targeting-foundation/studio-chat-management-controls-visual-qa.md`
- `07_LOGS/Visual-QA/2026-06-07-native-chat-v2-openclaw-only-correction/studio-chat-management-controls-visual-qa.json`
- `07_LOGS/Visual-QA/2026-06-07-native-chat-v2-openclaw-only-correction/studio-chat-management-controls-visual-qa.md`

## Authority Boundary

Allowed in this pass:

- local UI runtime target selection
- local UI preferences and state
- local chat organization actions through existing APIs
- existing governed Chat Agent Bus send path
- source visual QA fixtures

Not allowed or not implemented:

- provider calls
- runtime start/stop
- approval execution or consumption
- shell expansion
- Agent Bus writes beyond the existing governed send path
- canonical memory/writeback mutation
- secrets access
- full live runtime event streaming
