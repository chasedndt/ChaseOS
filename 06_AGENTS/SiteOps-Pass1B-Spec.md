---
title: SiteOps Pass 1B — Live Executor Engineering Spec
type: engineering-spec
status: spec-ready
created: 2026-05-18
phase: Phase 9 / SiteOps
prerequisite: SiteOps Pass 1A dry-run substrate (COMPLETE 2026-04-30)
---

# SiteOps Pass 1B — Live Executor Engineering Spec

## Purpose

Pass 1B transitions SiteOps from a dry-run-only substrate into a system capable of live execution for provider-API workflows. It does not build a browser executor. It opens exactly one execution path — provider API calls for read/capture-only workflows — behind the existing approval and audit infrastructure.

The goal is a proven, end-to-end governed execution loop: dry-run → approval → live execute → quarantine output → audit trail → Studio visibility.

---

## What Pass 1A Delivered (Baseline)

- `runtime/siteops/` — registry, schemas, tenant scaffold, policy, dry-run runner, approval objects, audit writer, credential refs, budget policies
- `run_siteops_dry_run()` — fully operational; returns `would_execute: False`, `live_execution_status: "NOT BUILT"`
- `chaseos siteops list|show|validate|dry-run` — CLI live
- 30+ executor design surfaces — all no-write, all reviewed, all executor-guard-tested
- Gate: `siteops_activation_records` and `siteops_skill_cards_inactive_review` write targets exist in `gateway_allowlists.json`

---

## What Pass 1B Adds

Three sequential sub-passes. Each must be complete and tested before the next begins.

---

## Phase 1B-A — Gate Policy Application

**Scope:** add `siteops.workflow.execute` to `gateway_allowlists.json` and wire the necessary write targets.

### Gate changes required

File: `runtime/policy/gateway_allowlists.json`

**Add to `write_targets`:**

```json
"siteops_execution_outputs": [
  "07_LOGS/Website-Workflow-Runs/**",
  "07_LOGS/SiteOps-Runs/**",
  "07_LOGS/SiteOps-Audits/**",
  "07_LOGS/SiteOps-Approvals/**"
],
"siteops_quarantine_outputs": [
  "03_INPUTS/00_QUARANTINE/digest/**",
  "03_INPUTS/00_QUARANTINE/source/**"
]
```

**Add to `external_apis`:**

```json
"siteops.provider_api": {
  "description": "SiteOps provider-API workflow execution. Credential values must come from env-var references only. Outbound calls go to workflow-registered provider endpoints only.",
  "schemes": ["https"],
  "credential_reference_required": true,
  "approval_gate": "operator",
  "audit_requirement": "siteops_run_audit"
}
```

### Execution protocol

1. Run `chaseos siteops candidates trusted-inactive-artifact-writer-gate-policy-patch-application-preflight` — record pre-patch digests
2. Apply the two file edits above
3. Run `chaseos gate smoke-test` — must pass
4. Record post-patch digests in a `07_LOGS/Build-Logs/` entry
5. Executor guard tests must still pass (no regression)

### Acceptance criteria

- `gateway_allowlists.json` parses cleanly as JSON
- `chaseos gate smoke-test` exits 0
- `test_siteops_executor_guard_tests.py` (or equivalent) still passes
- Pre- and post-patch digests recorded in build log

---

## Phase 1B-B — Provider API Executor

**Scope:** add a live execution path to `runtime/siteops/` for provider-API-only workflows. No browser. No authenticated browser sessions. No site navigation.

### New file: `runtime/siteops/executor.py`

```python
"""Live executor for provider-API SiteOps workflows (no browser)."""

from __future__ import annotations
from pathlib import Path
from typing import Any

EXECUTOR_KIND_PROVIDER_API = "provider_api"
EXECUTOR_KIND_BROWSER = "browser"  # NOT BUILT — raises SiteOpsExecutorNotBuiltError

class SiteOpsExecutorNotBuiltError(Exception):
    pass

class SiteOpsExecutorError(Exception):
    pass


def run_provider_api_step(
    *,
    step: dict[str, Any],
    credential_env_var: str,
    inputs: dict[str, str],
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """Execute one provider API step. Returns raw response dict. Raises SiteOpsExecutorError on failure."""
    ...


def run_siteops_live(
    *,
    root: Path | str | None,
    workflow_id: str,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    approval_id: str,
    inputs: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Execute an approved SiteOps workflow via provider API.

    Preconditions (fail-closed if any are missing):
    - Approval record exists, status == "approved", not consumed
    - Workflow template executor_kind == "provider_api"
    - Credential env var present in environment
    - Budget policy not exceeded

    On success:
    - Writes output to 03_INPUTS/00_QUARANTINE/{class}/{slug}/
    - Updates run record mode to "live", status to "completed" or "failed"
    - Appends audit event "run_executed"
    - Marks approval as consumed

    Never:
    - Launches a browser
    - Reads credential values into vault state
    - Writes to canonical knowledge without a separate promotion pass
    - Calls executor_kind == "browser" (raises SiteOpsExecutorNotBuiltError)
    """
    ...
```

### Modifications to `runtime/siteops/runner.py`

- `run_siteops_dry_run()` is unchanged
- Add `run_siteops_live()` as a thin wrapper that:
  1. Calls `validate_production_siteops()` (same as dry-run)
  2. Loads approval record, checks `status == "approved"` and `consumed == False`
  3. Checks `executor_kind` — if not `"provider_api"`, raises `SiteOpsExecutorNotBuiltError`
  4. Calls `executor.run_siteops_live()`
  5. Returns result with `would_execute: True` and `live_execution_status: "ok"` or `"failed"`

### Output routing

Live execution outputs route through the existing Phase 8 capture pattern:

```python
from runtime.capture.capture import capture_content

result = capture_content(
    content=raw_response_text,
    source=workflow_template_id,
    input_class="digest",
    origin_kind="ai-generated",
    vault_root=root,
)
```

This means:
- SHA-256 dedup applies transparently
- Output lands in `03_INPUTS/00_QUARANTINE/digest/`
- `.meta.json` sidecar written with provenance
- No auto-promotion to canonical knowledge

### Credential access pattern

Consistent with Phase 8 connectors (Perplexity, Grok):

```python
import os

def _get_credential(env_var: str) -> str:
    val = os.environ.get(env_var)
    if not val:
        raise SiteOpsExecutorError(f"Credential env var not set: {env_var}")
    return val
```

The `env_var` name comes from the `credential_ref.secret_store_ref` field in the tenant config. No credential value is ever stored in vault state.

### New tests: `runtime/siteops/tests/test_siteops_live_executor.py`

Minimum required coverage:

| Test | Assertion |
|---|---|
| `test_live_requires_approved_approval` | pending/rejected approval → `SiteOpsExecutorError` |
| `test_live_requires_unconsumed_approval` | consumed approval → `SiteOpsExecutorError` |
| `test_live_blocks_browser_kind` | executor_kind=browser → `SiteOpsExecutorNotBuiltError` |
| `test_live_requires_credential_env_var` | missing env var → `SiteOpsExecutorError` |
| `test_live_output_routes_to_quarantine` | success → quarantine path in result |
| `test_live_marks_approval_consumed` | success → approval status == "consumed" |
| `test_live_writes_run_record_mode_live` | success → run record mode == "live" |
| `test_live_writes_audit_event` | success → audit event type == "run_executed" |
| `test_live_fail_open_on_provider_error` | provider HTTP error → status == "failed", no exception propagation |
| `test_dry_run_unchanged` | `run_siteops_dry_run()` still returns `would_execute: False` |

Target: 15–20 tests. All mock the actual HTTP call — no live provider calls in tests.

---

## Phase 1B-C — First Live Workflow

**Target workflow:** `perplexity.research.capture`

This workflow is provider-API-only (no browser), uses an existing proven connector pattern (`perplexity_connector.py`), produces a digest-class output, and has a read-only risk profile.

### CLI addition

```
chaseos siteops execute \
  --workflow perplexity.research.capture \
  --input query="..." \
  --approval APPROVAL_ID \
  [--tenant local] [--workspace default] [--user local-user] \
  [--vault-root PATH] [--json]
```

This command:
1. Calls `run_siteops_live()` from `runner.py`
2. Prints run record, quarantine path, and audit ref on success
3. Prints error type and message on failure (no traceback unless `--debug`)

Wire in `runtime/cli/siteops_commands.py` under the existing `siteops` subparser.

### AOR wiring

**New task type** in `runtime/aor/task_type_table.yaml`:

```yaml
- id: siteops-execute
  description: Execute an approved SiteOps provider-API workflow and route output to quarantine.
  runtime_class: operator
  permission_ceiling: write-quarantine
  writeback_expectations:
    - 03_INPUTS/00_QUARANTINE/**
    - 07_LOGS/SiteOps-Runs/**
    - 07_LOGS/SiteOps-Audits/**
  escalation_triggers:
    - executor_kind != provider_api
    - approval not found or not approved
    - credential env var missing
    - budget exceeded
```

**New role card:** `06_AGENTS/role-cards/siteops-operator.yaml`

```yaml
role_id: siteops-operator
description: Executes approved SiteOps provider-API workflows. Writes to quarantine and SiteOps audit paths only.
allowed_reads:
  - runtime/siteops/**
  - 07_LOGS/SiteOps-Approvals/**
allowed_writes:
  - 03_INPUTS/00_QUARANTINE/**
  - 07_LOGS/SiteOps-Runs/**
  - 07_LOGS/SiteOps-Audits/**
  - 07_LOGS/Website-Workflow-Runs/**
forbidden_writes:
  - 02_KNOWLEDGE/**
  - 01_PROJECTS/**
  - runtime/policy/**
  - SOUL.md
  - 00_HOME/Principles.md
  - 00_HOME/Assistant-Contract.md
forbidden_actions:
  - canonical_promotion
  - browser_launch
  - credential_read_to_vault
  - gate_mutation
  - agent_bus_write
```

**New workflow manifest:** `runtime/workflows/registry/siteops_execute.yaml`

```yaml
id: siteops_execute
name: SiteOps Execute
description: Execute an approved SiteOps provider-API workflow.
task_type: siteops-execute
role_card: siteops-operator
trigger_type: operator
status: active
runtime_adapter: openclaw
owner: operator
```

**New handler:** `runtime/workflows/siteops_execute.py`

Minimal shape:
```python
def run_siteops_execute(task: dict, vault_root: Path) -> dict:
    """AOR handler for siteops-execute task type."""
    workflow_id = task["inputs"]["workflow_id"]
    approval_id = task["inputs"]["approval_id"]
    inputs = task["inputs"].get("workflow_inputs", {})
    ...
    result = run_siteops_live(
        root=vault_root,
        workflow_id=workflow_id,
        tenant_id=task["inputs"].get("tenant_id", "local"),
        workspace_id=task["inputs"].get("workspace_id", "default"),
        user_id=task["inputs"].get("user_id", "local-user"),
        approval_id=approval_id,
        inputs=inputs,
    )
    return result
```

Wire into `runtime/aor/engine.py` `_resolve_workflow_handler()`.

### End-to-end test

`runtime/siteops/tests/test_siteops_e2e_perplexity.py`

Cover the full loop with a mocked Perplexity API response:
1. `chaseos siteops dry-run --workflow perplexity.research.capture --input query="test"` → `ok: true, would_execute: false`
2. `chaseos siteops candidates request-promotion ...` → approval request written
3. Approval consumed → `chaseos siteops execute --workflow ... --approval ID` → `ok: true, would_execute: true`
4. Quarantine output exists
5. Run record mode == "live"
6. Audit event type == "run_executed"
7. AOR handler `run_siteops_execute()` routes correctly
8. No canonical write occurred

---

## Acceptance Criteria (Pass 1B Complete)

| Criterion | Check |
|---|---|
| Gate smoke-test passes | `chaseos gate smoke-test` exits 0 |
| Executor guard tests still pass | no regression on no-executor boundary |
| `run_siteops_dry_run()` unchanged | `would_execute: False` still returned |
| `run_siteops_live()` executes approved provider-API workflows | live result written to quarantine |
| Browser executor correctly blocked | `SiteOpsExecutorNotBuiltError` on executor_kind=browser |
| Approval consumed exactly once | idempotency marker present after first execution |
| Output in quarantine, not canonical knowledge | quarantine path in result, no `02_KNOWLEDGE/` writes |
| Audit trail written | run record + audit event JSONL present |
| `chaseos siteops execute` CLI live | help text + dry-run contract test pass |
| AOR `siteops-execute` task type registered | `task_type_table.yaml` entry + role card present |
| `run_siteops_execute()` handler wired in engine | engine dispatch test passes |
| Test count: ≥ 35 net new tests | executor + e2e + CLI contract |

---

## Not In Scope for Pass 1B

- Browser/Playwright execution — deferred to Pass 1C
- Authenticated browser sessions
- Site navigation, form fill, screenshot capture
- Site Skill Card promotion from execution outputs
- Studio Site Skills panel
- Multi-tenant production use beyond `tenant_id=local`
- Live trading, posting, purchasing, account-setting, or sharing actions
- Any automatic canonical promotion
- Provider calls during test execution (all mocked)

---

## Sequencing Constraint

Pass 1B must not begin until the current MVP loop (`operator request → Agent Bus → result → Studio`) is proven end-to-end with a live credential. The P0 blocker (`OPENAI_API_KEY` / `ANTHROPIC_API_KEY` in Hermes) must be resolved first. SiteOps Pass 1B is post-MVP scope.

---

## Graph Links

[[ChaseOS-SiteOps]] · [[Autonomous-Operator-Runtime]] · [[Permission-Matrix]] · [[Agent-Control-Plane]] · [[Feature-Fit-Register]]
