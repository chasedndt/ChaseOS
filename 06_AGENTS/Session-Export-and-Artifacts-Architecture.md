# Session Export and Artifacts Architecture

Date: 2026-06-02 (backend foothold 2026-06-03; session lifecycle + N4 adapter 2026-06-06)
Runtime: Hermes/Optimus (backend foothold: Chaser Agent; lifecycle + N4 adapter passes: Codex)
Status: BACKEND PARTIAL - markdown/json export, session metadata lifecycle, and Studio chat export adapter/CLI implemented; UI/zip/generic session CLI planned
Source handoff: [[ChaseOS_Terminal_ChaserAgent_Fullstack_Implementation_Handoff_v2]]
Related: [[Terminal-ChaserAgent-Feature-Matrix]] Â· [[ChaserAgent-Architecture]] Â· [[Terminal-Workbench-Architecture]] Â· [[HERMES]] Â· [[Hermes-Runtime-Profile]] Â· [[Agent-Activity-Index]]

## Position

Session Export is a first-class ChaseOS feature, not an afterthought. Hermes Desktop's `Pin & export any chat` pattern maps to ChaseOS as a governed session/export/artifacts layer with provenance, redaction, and audit.

The export **backend** is implemented (2026-06-03) in `runtime/chaser/exports.py` for markdown and json formats, with mandatory secret redaction, artifact/tool-run/terminal-run manifests, an on-disk export audit record, and `external_upload_performed=False`. Session metadata lifecycle is implemented (2026-06-06) in `runtime/chaser/sessions.py`: audited pin/unpin, rename, archive-first active-store removal, and malformed payload/path id rejection. The N4 Studio chat export adapter is implemented (2026-06-06) in `runtime/chaser/chat_session_adapter.py` with CLI `chaseos chaser session export-chat`; it converts existing Studio chat transcripts into `SessionRecord` objects and optionally attaches recorded terminal audit runs. The generic `chaseos session export` CLI, the Studio export action/toast, and the zip bundle remain planned.

## 2026-06-06 update - session metadata lifecycle

- `set_session_pinned(vault_root, session_id, pinned, actor=...)` updates pinned metadata and writes a lifecycle audit.
- `rename_session(vault_root, session_id, title, actor=...)` updates title metadata, validates title shape, and writes a lifecycle audit.
- `archive_session(vault_root, session_id, actor=..., reason=...)` moves the active session JSON into `07_LOGS/Chaser-Sessions/_archive/<YYYY-MM-DD>/` and writes lifecycle audit evidence under `_audit/`.
- Session reads reject records whose internal `session_id` does not match the safe path id.
- Archive-first lifecycle performs no hard delete. Result and audit records carry `hard_delete_performed=False`, `canonical_writeback_performed=False`, and `external_upload_performed=False`.
- Focused session/export tests cover lifecycle writes, archive exclusion from active list, unsafe session ID rejection, and export compatibility after metadata updates.

## 2026-06-06 update - N4 Studio chat export adapter

- `build_session_record_from_studio_chat(vault_root, thread_id, terminal_run_ids=...)` loads an existing Studio native-state conversation from `runtime/studio/chat/native-state/conversations/` and converts it to a Chaser `SessionRecord`.
- `export_studio_chat_session(vault_root, thread_id, fmt=..., actor=..., terminal_run_ids=...)` calls `exports.export_session()` with the converted record and returns explicit no-authority flags.
- Optional terminal run attachments use `terminal_runs.load_terminal_run_detail()` and remain Tier 4 untrusted evidence in the terminal-run manifest.
- Unsafe thread IDs, unsafe terminal run IDs, and missing terminal run records fail with compact `ok:false` results and do not create exports.
- CLI `chaseos chaser session export-chat THREAD_ID --format markdown|json [--terminal-run RUN_ID] --json` is wired through `runtime/cli/main.py`.
- The adapter does not execute Studio actions, terminal commands, providers, Agent Bus writes, approvals, canonical memory writes, or external uploads.

## Export feature

Supported formats, in planned order:

1. Markdown transcript.
2. JSON transcript.
3. ZIP bundle later.

Exports are local artifacts unless a separate approved delivery/upload path exists. There is no hidden external upload.

## Included data

Every export should include:

- transcript messages;
- session ID and metadata;
- created/updated/exported timestamps;
- participant/runtime/profile metadata where safe;
- model/provider display metadata where safe;
- artifacts manifest;
- tool-run manifest;
- terminal-run manifest;
- audit/provenance metadata;
- redaction report;
- trust labels for external/terminal/tool outputs;
- source handoff/log references when applicable.

Secret-like values must be redacted. Export should not include raw tokens, API keys, cookies, passwords, private `.env` values, browser session material, or credential store contents.

## Studio context-menu actions

The session context menu should support:

| Action | Contract | Governance note |
|---|---|---|
| Pin / unpin | update local session metadata | does not promote truth |
| Copy ID | read-only session ID copy | may expose correlation ID only |
| Export | create local markdown/json export | must redact and audit |
| Rename | update session title metadata | title is metadata, not canonical truth |
| Delete/archive | archive-first session lifecycle | hard delete requires explicit policy and review |

The UI should show a success/failure toast such as `Session exported` only after the backend returns a verified export path and audit metadata.

## CLI contract

Implemented N4 CLI:

```text
chaseos chaser session export-chat <thread_id> --format markdown
chaseos chaser session export-chat <thread_id> --format json --terminal-run <run_id>
```

Still-planned generic session CLI:

```text
chaseos session export <session_id> --format markdown
chaseos session export <session_id> --format json
chaseos session export <session_id> --bundle zip
```

Expected result shape:

```json
{
  "ok": true,
  "session_id": "...",
  "format": "markdown",
  "export_path": "...",
  "artifact_manifest_path": "...",
  "audit_path": "...",
  "redaction_applied": true,
  "external_upload_performed": false
}
```

## Artifact hub

Artifacts should be typed, queryable, and provenance-linked. Planned tabs:

- Files;
- Links;
- Images;
- All.

Each artifact manifest should include:

- artifact ID;
- artifact type;
- source session/task/tool/terminal run;
- path or URL reference;
- trust tier;
- redaction status;
- visual verification status for screenshots/images where applicable;
- creation/export timestamps;
- audit link.

Artifacts are evidence/output objects. They are not canonical ChaseOS truth unless later promoted through the normal Gate/writeback path.

## Terminal-run manifest

Terminal Workbench exports must include terminal run records with:

- command;
- cwd;
- classification;
- blocked/executed state;
- return code;
- stdout/stderr redaction and truncation flags;
- Tier 4 untrusted label;
- audit event IDs/links.

## Tool-run manifest

Tool-call exports should include tool name, arguments when safe, result summary, trust tier, redaction metadata, and audit/provenance links. Product display mode may summarize tool runs, but technical export mode should preserve safe details.

## Governance

- Protected data redaction is mandatory.
- Export creation is audited.
- No hidden external upload.
- Terminal/tool/external output remains untrusted unless separately verified.
- Delete/archive/export actions must be visible to the operator.
- Session export does not create permission to promote memory or canonical docs.

## First implementation target â€” DONE (backend, 2026-06-03)

Implemented in `runtime/chaser/exports.py` + `runtime/chaser/sessions.py` + `runtime/chaser/models.py`, covered by `runtime/chaser/tests/test_session_export.py` (14 tests):

- [x] missing session fails cleanly (`SessionNotFoundError`);
- [x] unsafe session id rejected (path-traversal guard);
- [x] markdown export shape;
- [x] JSON export shape;
- [x] artifact manifest inclusion;
- [x] terminal/tool manifest inclusion;
- [x] secret-like value redaction (markdown + json);
- [x] export audit record (on disk + optional sink);
- [x] `external_upload_performed=False` flag;
- [x] no-redaction case reports zero redactions.

## Chat export tie-in (how export connects to "export any chat") - N4 DONE 2026-06-06

The Hermes Desktop pattern is `Pin & export any chat`. In ChaseOS, a "chat" is a
Studio native-state conversation that can be exported as a Chaser `SessionRecord`
without activating ChaserAgent. The tie-in is a thin adapter (handover unit
**N4**, now implemented) that converts an existing chat transcript into a
`SessionRecord` (`runtime/chaser/models.py`) and calls `exports.export_session()`.
Nothing about the export backend changes - the chat surface simply produces the
`SessionRecord` the backend already consumes:

```
live chat transcript  â†’  SessionRecord(messages, tool_runs, terminal_runs, artifacts)
                      â†’  exports.export_session(vault_root, session_id, fmt=...)
                      â†’  redacted md/json + manifests + audit  (external_upload_performed=False)
```

Terminal runs surfaced in a chat already have a canonical record shape
(`07_LOGS/Terminal-Runs/<id>.json` via `terminal_runs.py`); the chat-export
adapter references those run records in the session's `terminal_runs` so an
exported chat carries its governed terminal evidence. This is the integration
point between the Terminal Workbench and Session Export tracks.

## Remaining (still planned)

- generic `chaseos session export <session_id> --format markdown|json` CLI wiring;
- zip bundle format;
- Studio export action + `Session exported` toast;
- unified Artifacts Hub UI and typed artifact registry beyond the per-export manifest.
