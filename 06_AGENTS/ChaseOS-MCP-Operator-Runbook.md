---
title: "ChaseOS Runtime MCP - Operator Runbook"
version: "1.0"
date: 2026-04-21
status: live
knowledge_class: system-operational
---

# ChaseOS Runtime MCP - Operator Runbook

This runbook is for normal local operator use of the internal Runtime MCP server, with special focus on the active V2 `workflow.invoke_bounded` lane.

Runtime MCP remains local-first, stdio-first, bounded, and policy-heavy. It is not a shell, git, browser, network, schedule, or canonical writeback bridge.

---

## Which Mode To Use

| Mode | Use when | Main boundary |
|---|---|---|
| `read_only` | Inspect identity, capabilities, current truth, workflow registry, role boundaries, handoff, audit, or latest operator brief | No tools, no proposal staging, no workflow invocation |
| `read_plus_proposal` | Stage or review human-governed proposal artifacts | No apply path; proposals and approval requests are artifacts only |
| `draft_execution` | Intentionally run the bounded workflow invocation lane as `openclaw` | Only `workflow.invoke_bounded`; only `operator_today` / `operator_close_day`; AOR only |

Only `openclaw` is granted `draft_execution` in `runtime/mcp/config.yaml`. `claude_code`, `n8n`, and `_unregistered` must not use this mode.

---

## When To Use `workflow.invoke_bounded`

Use `workflow.invoke_bounded` when you need MCP to request one bounded AOR operator-briefing workflow run:

- `operator_today`
- `operator_close_day`

It is appropriate for dry-run checks, operator smoke verification, and deliberate operator brief generation through the AOR pipeline.

It is not appropriate for:
- arbitrary workflow execution
- schedule-triggered execution
- source workspace lookup
- shell, git, browser, or network operations
- canonical vault writeback
- protected-file mutation
- apply, commit, or approval automation

---

## Dry-Run Smoke

Dry-run is the first check before any live invocation:

```bash
echo '{"request_id":"smoke-pass6c-dryrun","tool":"workflow.invoke_bounded","runtime_id":"openclaw","mode":"draft_execution","params":{"workflow_id":"operator_today","dry_run":true}}' | .venv/Scripts/python.exe -m runtime.mcp.server
```

Expected:
- `ok: true`
- `aor_status: dry_run_ok`
- `invocation_status: dry_run_ok`
- `files_written: []`
- `output_artifacts: []`
- `canonical_write: false`
- `aor_audit_id` present
- `audit_reconciliation` present

Dry-run still writes AOR and MCP audit records. It does not write an Operator-Briefs artifact.

---

## Intentional Live Invocation

Run live only when the target output artifact is known not to exist.

Pass 6C verified this live path on 2026-04-21:

```bash
echo '{"request_id":"smoke-pass6c-live-json","tool":"workflow.invoke_bounded","runtime_id":"openclaw","mode":"draft_execution","params":{"workflow_id":"operator_today","inputs":{"date":"2026-04-21","output_format":"json"},"dry_run":false}}' | .venv/Scripts/python.exe -m runtime.mcp.server
```

Expected:
- `ok: true`
- `aor_status: success`
- `invocation_status: completed`
- `stage_reached: audit_record`
- `output_artifacts[0].path: 07_LOGS/Operator-Briefs/2026-04-21-operator-today.json`
- `canonical_write: false`
- no full generated brief text in the MCP response

The AOR-owned output artifact from the Pass 6C live smoke is:

```text
07_LOGS/Operator-Briefs/2026-04-21-operator-today.json
```

---

## Audit Reconciliation

For every successful `workflow.invoke_bounded` response, inspect three things:

| Evidence | Where |
|---|---|
| Output artifact | Path listed in `output_artifacts` |
| AOR audit | `07_LOGS/Agent-Activity/{timestamp}__operator_today__{aor_audit_id[:8]}.json` or matching workflow id |
| MCP audit | `07_LOGS/Agent-Activity/{timestamp}__mcp__workflow.invoke_bounded__{request_id[:8]}.json` |

For Pass 6C live smoke:
- AOR audit id: `677bc4d3-2ae9-41d2-9f5c-8091393bcf03`
- AOR audit file: `07_LOGS/Agent-Activity/20260421-171132__operator_today__677bc4d3.json`
- MCP audit file: `07_LOGS/Agent-Activity/20260421-171132__mcp__workflow.invoke_bounded__smokepas.json`
- Output artifact: `07_LOGS/Operator-Briefs/2026-04-21-operator-today.json`

The MCP response and MCP audit stay bounded to status, ids, and relative paths. The generated brief content lives in the AOR artifact path and may also be represented inside AOR-owned audit output data.

---

## Do Not Retry Blindly

These errors mean stop and inspect state before rerunning:

| Error | Meaning | Operator action |
|---|---|---|
| `workflow_output_already_exists` | MCP predicted the live output path already exists and did not start AOR | Inspect `existing_artifacts`, MCP audit, and any prior AOR audit before choosing a different date/output format |
| `workflow_invocation_audit_failed` | AOR returned, but MCP could not write the MCP envelope audit | Do not rerun automatically; inspect the AOR audit id in the error details and any output artifact |
| `aor_invocation_failed` | AOR denied, escalated, or failed the run | Inspect the AOR audit/error details; do not bypass AOR through MCP |

The duplicate-output guard is narrow by design. It is not a generic idempotency framework; it only blocks known first-release Operator-Briefs outputs before AOR is called.

---

## Hard Limits

- V1 resources, proposal tools, and static prompt remain unchanged.
- `workflow.invoke_bounded` is the only active V2 surface.
- Only `operator_today` and `operator_close_day` are allowed.
- Only `openclaw` has `draft_execution`.
- MCP never calls workflow handlers directly.
- MCP never spawns `chaseos run` or any subprocess.
- MCP never calls Gate, schedule loader, shell, git, browser, or network code.
- MCP never returns full generated brief text.
- MCP never applies, commits, or writes canonical vault state.
- Other deferred/excluded surfaces remain inactive.

---

*ChaseOS-MCP-Operator-Runbook.md - Phase 9 Pass 6C - 2026-04-21*


*Graph links: [[OpenClaw-Runtime-Profile]] · [[Vault-Map]] · [[ChaseOS-Runtime-State-and-Gateway-Design]]*
