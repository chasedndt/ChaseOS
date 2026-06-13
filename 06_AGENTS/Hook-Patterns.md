---
type: framework-control
title: Hook Patterns — ChaseOS Session Lifecycle
version: 1.0
created: 2026-03-20
scope: Anthropic Agent Harness (execution adapter)
---

# Hook Patterns

> Defines session-open and session-close hook patterns for the Claude Code execution adapter.
> Hooks are shell commands that Claude Code executes automatically in response to lifecycle events.
> They are configured in `settings.json` — they run in the shell, not in Claude's context.
> This document defines what hooks are appropriate for ChaseOS, what they may and may not do, and failure behavior.
> Execution adapter: `[[CLAUDE]]` · Standard: `[[Execution-Adapter-Standard]]` Section 3.9 · Security: `[[Agent-Security-Model]]`

---

## 1. What Hooks Are in Claude Code

Claude Code hooks are shell commands that execute automatically in response to defined lifecycle events. They are configured in `~/.claude/settings.json` (user-level) or `.claude/settings.json` (project-level).

**Key distinction:** Hooks run in the shell as separate processes. They are not instructions to Claude — they cannot direct Claude's reasoning or inject context into the conversation. They are side-effect runners attached to events.

### Hook event types

| Event | When it fires |
|-------|--------------|
| `PreToolUse` | Before Claude executes a tool call (e.g., before a file write) |
| `PostToolUse` | After Claude executes a tool call |
| `Notification` | When Claude sends a notification to the user |
| `Stop` | When Claude finishes responding (end of a turn) |
| `UserPromptSubmit` | When the user submits a prompt |

Hooks can be configured to match specific tool names (e.g., only fire `PreToolUse` for `Write` calls) or to fire for all events of that type.

---

## 2. Session-Open Pattern

Claude Code does not have a dedicated session-start event hook. The closest pattern is `UserPromptSubmit`, which fires when the user submits the first (or any) message.

### Recommended session-open posture

Rather than a shell hook, the session-open protocol for ChaseOS is implemented through Claude's read order — defined in `CLAUDE.md` and the `[[Handoff-Protocol]]`:

```
1. Read 00_HOME/Now.md         ← current phase and sprint focus
2. Read relevant Project-OS    ← state of the project in scope
3. Read supporting files       ← only what the task requires
```

This read order is the effective "session-open hook" — it is enforced by the adapter routing rules, not by a shell script.

### When a shell-level UserPromptSubmit hook is appropriate

A `UserPromptSubmit` hook is appropriate for:
- Logging session start timestamps to an activity file
- Checking that required tools (e.g., Obsidian, a local server) are running
- Outputting a reminder to the user about current phase status (as a notification, not as instruction injection)

### What a UserPromptSubmit hook must NOT do
- Inject instructions into Claude's context — hooks run in the shell and cannot modify Claude's active prompt
- Write to vault files autonomously — all vault writes must be initiated by Claude based on session content
- Modify protected files — the hook has filesystem access; this boundary must be enforced at configuration time
- Make external API calls that could carry vault content — exfiltration risk

---

## 3. Session-Close Pattern

The `Stop` event fires when Claude finishes a response turn. This is the primary hook point for session-close automation.

### What session-close must cover (per adapter standard)

Before a substantive session ends, the following must be confirmed:

- [ ] Meaningful output produced → written to vault
- [ ] Relevant `Project-OS.md` updated if state changed
- [ ] Build log written to `07_LOGS/Build-Logs/YYYY-MM-DD-[Project]-[descriptor].md`
- [ ] `Build-Logs-Index.md` updated
- [ ] Archive note written if this was a major pass
- [ ] `Documentation-History-Index.md` updated if archive note written
- [ ] Open loops surfaced in build log

### Implementing session-close with a Stop hook

A `Stop` hook can automate the *reminder* side of session-close without automating the *writes* themselves. Example use:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Session close checklist: build log? project-OS update? index update?'"
          }
        ]
      }
    ]
  }
}
```

This surfaces the checklist without automating vault writes — vault writes remain Claude's responsibility under the writeback discipline in `CLAUDE.md`.

### Future: automated session-close logging (Phase 7)

Fully autonomous session-close logging — where a `Stop` hook triggers a script that generates and writes the build log without Claude involvement — is a Phase 7 capability. It requires:
- A defined build log format the script can populate from session metadata
- A defined method for passing session context to the hook script
- Explicit owner approval for autonomous vault writes from hook scripts

Until Phase 7, session-close writeback is Claude-assisted, not hook-automated. Claude writes the log; the user triggers the session-close checklist.

---

## 4. PreToolUse and PostToolUse Patterns

These hooks fire around individual tool calls, making them suitable for approval gates, logging, and validation.

### Approved PreToolUse patterns

| Use case | What the hook does | Notes |
|----------|-------------------|-------|
| Protected-file write guard | Check if the write target is in the protected file list; exit non-zero to block if not explicitly approved in session | Implemented at shell level; provides a backstop against silent protected-file edits |
| Credential scan | Check that a file being written does not contain patterns matching API key formats | Runs before write; exits non-zero to block if pattern detected |
| Dry-run logging | Log the tool call target and action to an activity file | Read-only side effect; safe to automate |

### Approved PostToolUse patterns

| Use case | What the hook does | Notes |
|----------|-------------------|-------|
| Write confirmation logging | After a file write, log the target path and timestamp to `07_LOGS/Agent-Activity/` | Audit trail for autonomous writes |
| Index reminder | After writing to `07_LOGS/Build-Logs/`, remind that `Build-Logs-Index.md` needs updating | Notification only, not automated write |

### What PreToolUse/PostToolUse hooks must NOT do

- Write to vault files autonomously in response to another write — this creates circular write chains
- Make decisions about vault state without Claude's awareness — if the hook blocks a write, Claude must be informed
- Call external services with vault content as payload — exfiltration risk
- Override Claude's tool call decisions silently — if a hook blocks a tool, it must surface a clear error message

---

## 5. Protected-File Hook Boundary

The protected-file list (`[[Permission-Matrix]]` Section 2) defines which files require explicit per-file user approval before edits.

A `PreToolUse` hook targeting `Write` and `Edit` tool calls can implement a backstop check:

```
if target file is in protected list:
    check if current session explicitly approved this file
    if not approved: exit 1 with message "Protected file [filename] — explicit user approval required"
```

This adds a shell-level guard that complements Claude's own permission enforcement. It does not replace the approval requirement — it reinforces it.

**Configuration note:** This hook requires access to the list of protected files. The list is maintained in `Permission-Matrix.md`. The hook script should read from a stable reference (e.g., a flat `.claude/protected-files.txt` that mirrors the canonical list) rather than parsing the markdown file directly.

---

## 6. What Hooks May Auto-Run (No Additional Approval)

These actions can be automated in hooks without per-session approval:
- Logging tool call metadata (file path, action type, timestamp) to an activity file
- Outputting reminder text to the user as a notification
- Checking that local services or tools are running (read-only check)
- Dry-run validation (reading files to verify structure, without writes)

---

## 7. What Hooks Require Explicit Owner Configuration

These require explicit, deliberate configuration by the vault owner before they are active:
- Any hook that writes to vault files autonomously
- Any hook that makes external HTTP requests
- Any hook that executes code beyond simple shell commands
- Any hook that reads or transmits vault content to an external service
- Any protected-file guard hook (must match the canonical protected list)

These are not "on by default." Each requires a conscious decision, documented in the settings file and, for anything with external side effects, in the agent registry.

---

## 8. Failure Handling

If a hook fails (exits non-zero or errors):

- **PreToolUse failure:** Claude Code blocks the tool call and surfaces the error to the user. Claude must acknowledge the block and ask the user how to proceed — it must not silently retry or bypass the hook.
- **PostToolUse failure:** The tool call already completed. Claude should log the hook failure in the session and surface it to the user. It must not suppress the failure.
- **Stop failure:** Claude should note that the session-close hook failed and the user should manually verify the close-out checklist.

**Hooks must not silently fail.** If a hook's exit code is checked and it fails, the failure must surface. A silent failure in a protected-file guard is a security gap.

---

## 9. Hook Configuration for Other Execution Adapters

Hook support varies by execution surface:

| Adapter | Hook support |
|---------|-------------|
| Anthropic Agent Harness (Claude Code) | Full hook support via settings.json |
| OPENAI Agent Harness (Agents SDK) | Tool-call guardrails and input/output validators serve a similar role — defined in `OPENAI.md` |
| LOCAL-OSS adapters (Cline, OpenHands) | Surface-specific approval mechanisms — defined in `LOCAL-OSS.md` |
| n8n Workflow Runtime | Workflow-level error handling and step-failure behavior — defined in `N8N.md` |

The patterns defined in this document are Claude Code-specific. The underlying principles (session-open context loading, session-close writeback verification, protected-file guards) apply to all execution adapters but are implemented differently per surface.

---

## 10. Current Configuration State

As of Phase 6 preflight, hook scripts are defined and wired in `.claude/settings.json`.

**Configured (Phase 6 preflight — 2026-03-20):**

- [x] Protected-file guard hook (`PreToolUse` on `Write`/`Edit`) — `.claude/hooks/protected_write_guard.py`
- [x] Ingestion promotion guard (`PreToolUse` on `Write` to `02_KNOWLEDGE/`) — `.claude/hooks/ingestion_promotion_guard.py`
- [x] Session-start context reminder (`UserPromptSubmit` — ingestion sessions) — `.claude/hooks/session_start_context.py`
- [x] Session-close checklist reminder (`Stop`) — `.claude/hooks/session_end_audit.py`

**Status: CONFIGURED — NOT YET VERIFIED**

Open loop: run a test session to confirm `protected_write_guard.py` fires and blocks a write to a protected file. Until verified, hooks are configured but untested.

**Policy source for hook enforcement:**
- Protected-file list: `runtime/policy/protected_files.yaml` (mirrors `Permission-Matrix.md` Section 2)
- Gate architecture: `[[ChaseOS-Gate]]`
- Settings: `.claude/settings.json` (project-level)

**Future (Phase 7):**
- Write audit log hook (`PostToolUse` on `Write`) — automated activity log entry
- Credential scan hook (`PreToolUse` on `Write`) — block writes containing API key patterns
- Fully autonomous session-close log generation

---

*Graph links: [[CLAUDE]] · [[Execution-Adapter-Standard]] · [[Permission-Matrix]] · [[Agent-Security-Model]] · [[Handoff-Protocol]] · [[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]] · [[Agent-Control-Plane]] · [[Claude-Memory-System]] · [[Subagent-Patterns]] · [[Vault-Map]] · [[ChaseOS-Gate]] · [[Adapter-Manifest-Standard]]*

*Hook-Patterns.md — Version 1.0 | Created: 2026-03-20 | Phase 5B — Repo / Runtime Binding*
