---
type: standard
title: Workspace Mode Profile Standard
status: active contract
created: 2026-05-13
runtime_package: runtime/workspace_modes/
---

# Workspace Mode Profile Standard

Workspace Mode Profiles are the machine-readable WML contract for a workspace, project, or runtime area. A profile declares the workspace mode, read order, allowed knowledge classes, output classes, workflow scope, adapter ceilings, approvals, graph rules, protected paths, write targets, and escalation behavior.

Canonical feature-family node: [[Workspace-Mode-Layer-Feature-Family]].

## Profile Locations

Preferred locations:

- `01_PROJECTS/[Project]/workspace-mode.yaml`
- `01_PROJECTS/[Project]/[Project]-OS.md` frontmatter
- `.workspace-mode.yaml` for a bounded workspace root

Runtime helpers can also load an explicit YAML path.

The read-only AOR route preview can be run with:

```powershell
python -m runtime.cli.main runtime workspace-mode route-preview --workspace-path PATH --workflow-id WORKFLOW_ID --adapter codex --json
```

The review-only first-profile rollout plan can be run with:

```powershell
python -m runtime.cli.main runtime workspace-mode rollout-plan --json
```

The validated draft packet can be run with:

```powershell
python -m runtime.cli.main runtime workspace-mode draft-packet --json
```

The profile-write approval request packet can be run with:

```powershell
python -m runtime.cli.main runtime workspace-mode write-approval-request --json
```

The guarded profile writer can be run with a matching approval packet id and confirmation:

```powershell
python -m runtime.cli.main runtime workspace-mode write-profiles --gate-approval-id wml-profile-write-appr-98b513c58e0412ac --confirm --json
```

The full-product missing-profile writer can be run after its matching approval request:

```powershell
python -m runtime.cli.main runtime workspace-mode write-approval-request-full --requested-by Codex --write-approval-request --json
python -m runtime.cli.main runtime workspace-mode write-profiles-full --gate-approval-id wml-profile-write-appr-980b50fd2868cd1f --requested-by Codex --confirm --json
```

The read-only WML product status and approval ledger can be run with:

```powershell
python -m runtime.cli.main runtime workspace-mode product-status --json
python -m runtime.cli.main runtime workspace-mode approval-ledger --json
```

The no-execution dispatch gate can be run with:

```powershell
python -m runtime.cli.main runtime workspace-mode dispatch-gate --workspace-path runtime/aor/engine.py --workflow-id operator_today --adapter codex --confirm --json
```

The WML-gated AOR dry-run executor can be run with:

```powershell
python -m runtime.cli.main runtime workspace-mode dispatch-dry-run --workspace-path runtime/aor/engine.py --workflow-id operator_today --adapter codex --confirm --json
```

The live-execution approval request gate can be run with:

```powershell
python -m runtime.cli.main runtime workspace-mode live-execution-approval-gate --workspace-path runtime/aor/engine.py --workflow-id operator_today --adapter codex --confirm --json
```

The exact-scope live executor can be run only after an approval packet is approved:

```powershell
python -m runtime.cli.main runtime workspace-mode live-executor --workspace-path runtime/aor/engine.py --workflow-id operator_today --adapter codex --gate-approval-id wml-aor-live-exec-appr-58147fa104e8514d --decision approved --write-approval-decision --write-approval-consumption --write-consumption-marker --confirm --json
```

The canonical operator contracts are `chaseos runtime workspace-mode route-preview`, `chaseos runtime workspace-mode rollout-plan`, `chaseos runtime workspace-mode draft-packet`, `chaseos runtime workspace-mode write-approval-request`, `chaseos runtime workspace-mode write-profiles`, `chaseos runtime workspace-mode write-approval-request-full`, `chaseos runtime workspace-mode write-profiles-full`, `chaseos runtime workspace-mode dispatch-gate`, `chaseos runtime workspace-mode dispatch-dry-run`, `chaseos runtime workspace-mode live-execution-approval-gate`, `chaseos runtime workspace-mode live-executor`, `chaseos runtime workspace-mode product-status`, and `chaseos runtime workspace-mode approval-ledger`; the direct helper modules remain available for focused smoke tests. The route preview never dispatches AOR. The rollout plan proposes candidate profile paths and draft payloads. The draft packet renders and validates YAML drafts for operator review. The write-approval-request packet renders the exact pending approval scope and confirmation text without profile file writes by default. The guarded writer creates only approved profile files when the approval packet id and confirmation match, refuses overwrite, and leaves AOR dispatch blocked. The full-product writer created the three remaining missing profiles at `04_SOPS/.workspace-mode.yaml`, `01_PROJECTS/University/workspace-mode.yaml`, and `00_HOME/.workspace-mode.yaml` after approval packet `wml-profile-write-appr-980b50fd2868cd1f`, bringing profile coverage to 6/6 valid. The dispatch gate clears or blocks a future executor request without calling `run_workflow`. The dry-run executor re-runs the dispatch gate and calls `run_workflow(..., dry_run=True)` only after the gate clears. The live-execution approval gate re-runs the dispatch gate and can write a pending exact-scope approval request without live execution. The live executor consumes an exact approved packet once, writes decision/marker/consumption artifacts, re-runs the gate, requires fresh dry-run evidence, and calls live AOR only for that scope. Approved live-execution packet `wml-aor-live-exec-appr-58147fa104e8514d` was consumed once for `operator_today`, producing live audit `96064d06-81fc-4939-9061-3c6fd958149e` and `07_LOGS/Operator-Briefs/2026-05-14-operator-today.md`. `product-status` now reports the WML runtime/operator product feature `COMPLETE` when core modules, six profile files, architecture docs, generated CLI/operator docs, Studio panel evidence, and Chat deeplink evidence are present; `approval-ledger` reads profile-write and AOR live-execution artifacts without mutation. Inferred modes can propose routing context, but live AOR execution/writeback requires exact-scope approval consumption.

## Studio And Chat Product Surfaces

WML is visible in Studio through `runtime/studio/workspace_mode_panel.py` and in Chat through `runtime/studio/phase11_chat_panel_contract.py`.

The Studio panel exposes read-only product status, profile coverage, approval-ledger posture, project/domain cards, route previews, and URL-persistent `wml_mode` selection. The Chat panel exposes a read-only `Workspace Mode Studio` selector with mode cards and project/domain/route previews that deep-link into the Studio panel. These surfaces are navigation and inspection surfaces only: no profile write, WML workflow execution, Agent Bus task write, approval consumption, provider call, or canonical mutation is authorized by selecting a mode.

## Required Fields

Every profile must include:

```yaml
workspace_id: chaseos
workspace_name: ChaseOS
workspace_mode: runtime_agent_ops
description: Local-first human-AI operating framework and runtime control plane.

primary_domains:
  - AI Engineering

canonical_state_files:
  - 00_HOME/Now.md

required_read_order:
  - README.md

allowed_knowledge_classes:
  - user-origin
  - source-derived
  - synthesized
  - generated-ideas
  - system-operational
  - canonical-state

default_output_classes:
  - build-log
  - proposal

allowed_workflows:
  - operator_today

runtime_adapter_ceiling:
  claude: tier-2
  codex: tier-2
  openclaw: tier-2-bounded
  hermes: tier-2-bounded

approval_rules:
  canonical_state_write: explicit_user_approval_required
  generated_idea_creation: allowed_with_label
  generated_idea_endorsement: human_only
  source_promotion: gate_required
  protected_file_write: explicit_per_file_approval_required
  shell_execution: blocked_by_default
  external_connector_action: blocked_by_default

graph_rules:
  update_domain_index_on_promotion: true
  backlinks_required_for_durable_notes: true
  orphan_notes_flagged: true

protected_paths:
  - .env
  - secrets/
  - credentials/

default_write_targets:
  - 07_LOGS/Build-Logs/

escalation_rules:
  unknown_mode: stop_and_request_mode
  protected_write: require_explicit_approval
  external_action: require_explicit_approval
  runtime_authority_unclear: fail_closed
```

## Allowed Modes

- `personal_os`
- `study_research`
- `founder_venture`
- `business_ops`
- `runtime_agent_ops`
- `unknown`

## Allowed Knowledge Classes

Profiles must preserve the canonical six classes:

- `user-origin`
- `source-derived`
- `synthesized`
- `generated-ideas`
- `system-operational`
- `canonical-state`

Invalid classes fail validation.

## Adapter Ceiling Values

Allowed ceiling values:

- `tier-2`
- `tier-2-bounded`
- `tier-3`
- `tier-4`
- `tier-4-default-tier-2-bounded`
- `blocked`

Adapter ceilings are ceilings only. They do not grant execution authority by themselves.

## Validation Rules

The runtime package validates that:

- all required fields exist
- `workspace_mode` is one of the allowed modes
- list fields are lists
- mapping fields are mappings
- knowledge classes match the canonical taxonomy
- runtime adapter ceiling values are recognized

Validation errors are fail-closed.

## Inference Behavior

When no explicit profile is present, WML may infer from safe path prefixes:

| Path prefix | Mode |
|---|---|
| `00_HOME/` | `personal_os` |
| `01_PROJECTS/University/` | `study_research` |
| `01_PROJECTS/ChaseOS/` | `runtime_agent_ops` |
| `06_AGENTS/` | `runtime_agent_ops` |
| `runtime/` | `runtime_agent_ops` |
| `04_SOPS/` | `business_ops` |
| unknown path | `unknown` |

Inference must not guess when uncertain.

## Unknown Mode Behavior

`unknown` is a fail-closed mode.

Allowed behavior:

- inspect declared files
- summarize observed context
- propose a likely mode
- ask the operator for confirmation
- write no durable/canonical outputs unless separately approved

Blocked behavior:

- runtime execution
- shell execution
- external sends
- protected file writes
- canonical state writes
- generated idea endorsement
- source promotion

## Agent Usage Rule

Before acting, an agent should:

1. Identify current workspace/task path.
2. Load an explicit workspace profile if present.
3. If no profile exists, infer mode from the path.
4. If mode is `unknown`, stop and ask or produce a proposal only.
5. Apply read order, output class, workflow allowance, adapter ceiling, write targets, and approval rules.
6. Escalate when requested work exceeds the profile.

## Runtime Adapter Usage Rule

Runtime adapters should treat WML as an additional context gate, not as a permission grant. OpenClaw, Hermes, Codex, Claude, and future adapters must still obey Agent Registry, Permission Matrix, Trust Tiers, role cards, workflow manifests, Gate, and task profiles.

---

*Graph links: [[Workspace-Mode-Layer-Feature-Family]] [[Use-Case-Mode-Architecture]] [[Vault-Map]] [[Agent-Registry]] [[Agent-Control-Plane]] [[Permission-Matrix]] [[Trust-Tiers]] [[ChaseOS-Studio-Architecture]] [[ChaseOS-Phase11-Architecture]]*
