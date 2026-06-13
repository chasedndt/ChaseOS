---
title: Discord Command Envelope Schema
type: control-plane-governance
status: ACTIVE — dual-runtime envelope schema; OpenClaw and Hermes both eligible adapter targets under shared approval and audit governance
version: 1.1
created: 2026-04-20
phase: 9
scope: Dual-runtime Discord control-plane — OpenClaw live, Hermes bounded active Discord lane
---

# Discord Command Envelope Schema

> This file defines the required fields and validation rules for any Discord-origin request before it may be considered for execution routing.
> An envelope with missing or invalid fields defaults to denied.
> This schema does not grant execution authority. It is a minimum structural requirement that any classification and routing layer must enforce.

---

## Canonical Rule

A Discord message is not a command. A Discord message becomes a candidate command only after it is wrapped in a valid envelope with all required fields present and validated against the identity map, channel registry, adapter allowlist, and workflow manifest.

An envelope that fails any required field check is denied before reaching the classification layer.

---

## Required Fields

Every authenticated command envelope must contain all of the following fields.

```yaml
envelope_schema:
  version: "1.0"

  required_fields:

    - field: request_id
      type: string
      format: "UUID v4 or equivalent monotonic unique ID"
      description: >
        Unique identifier for this request. Used to correlate approval records,
        audit log entries, and execution results. Must be generated at intake,
        not supplied by the Discord message author.
      validation: required, must be unique within the active approval ledger window
      example: "a3f2c1d0-7e84-4b12-9f01-c6e5d4b3a2f1"

    - field: actor
      type: object
      description: >
        The identity of the account that originated this request.
        Must resolve to a registered entry in Discord-Identity-Map.md.
      validation: required, account_id must match a registered entry, trust_tier must be >= 1 and eligible for the requested action
      sub_fields:
        - account_id: Discord snowflake ID of the originating account
        - display_name: Human-readable label from the identity map
        - trust_tier: Integer 1–4 from the identity map (1 = operator, 4 = untrusted)
        - execution_eligible: Boolean from the identity map
      example:
        account_id: "123456789012345678"
        display_name: "Chase (primary operator)"
        trust_tier: 1
        execution_eligible: true

    - field: source_channel_id
      type: string
      format: Discord snowflake ID
      description: >
        The Discord channel ID where the request originated.
        Must match a registered entry in Discord-Channel-Registry.md.
      validation: required, must match a registered channel_id in the channel registry

    - field: channel_class
      type: string
      enum:
        - control-plane-routing
        - runtime-chat
        - approvals
        - audit-writeback
        - alerts
        - debug
        - docs-archive
      description: >
        The canonical channel class resolved from Discord-Channel-Registry.md.
        Must match the class assigned to source_channel_id.
        Must be a class that permits command parsing (see channel registry).
      validation: required, must be resolved from registry, not supplied by message author

    - field: adapter_target
      type: string
      enum:
        - openclaw
        - hermes
        - none
      description: >
        The adapter lane this request is targeting.
        "openclaw" targets the OpenClaw bounded execution lane.
        "hermes" targets the Hermes bounded Discord runtime lane (advisory and shadow workflows only).
        "none" is valid for advisory-only and approval-record requests.
      validation: required, must be "openclaw", "hermes", or "none"; unlisted adapters are denied

    - field: workflow_id
      type: string
      nullable: true
      description: >
        The exact workflow identifier from the AOR workflow registry this request intends to trigger.
        Must match a manifest in runtime/workflows/registry/ with status=active.
        Null is valid for non-execution requests (advisory, status, approval-record only).
      validation: when non-null, must resolve to a real active manifest; unknown workflow IDs are denied
      eligible_values_current_state:
        - operator_today
        - operator_close_day
        - graph_hygiene
        - hermes_operator_today_shadow
        - null (advisory or status only)

    - field: action_name
      type: string
      nullable: true
      description: >
        Human-readable name for the action being requested when a full workflow_id is not applicable.
        Used for approval records, status requests, and routing decisions.
        Must be present when workflow_id is null.
      validation: at least one of workflow_id or action_name must be non-null

    - field: command_text
      type: string
      description: >
        The exact command or instruction text as it would be passed to the adapter.
        Must be explicit — no template variables, no references to prior context.
        Used verbatim in approval records and audit entries.
      validation: required, must be non-empty, must not contain prompt-injection patterns (see guardrail check)
      example: "chaseos run operator_today"

    - field: inputs
      type: object
      description: >
        Explicit key-value inputs for the workflow or action.
        Must list all non-default parameters that will be passed to the adapter.
      validation: required (may be empty object if no inputs), must not contain credential values or external URLs unless the workflow manifest explicitly permits them

    - field: date_window
      type: string
      nullable: true
      description: >
        The date or time window this request applies to (e.g. "2026-04-20", "today", "last 48h").
        Used in audit records and approval scope.
      validation: optional but must be present for time-bounded workflows

    - field: read_targets
      type: array
      items: string
      description: >
        Explicit list of vault paths or external sources the adapter will read.
        Must match what the role card and workflow manifest permit.
      validation: required, must be non-empty for execution requests

    - field: write_targets
      type: array
      items: string
      description: >
        Explicit list of vault paths the adapter will write.
        Must match what the role card and workflow manifest permit.
        Protected files must not appear here.
      validation: required, must not include protected files, must match permitted writeback surfaces

    - field: external_systems
      type: array
      items: string
      description: >
        Any external systems or APIs the adapter will contact.
        Empty array if no external systems are touched.
      validation: required (may be empty), must be declared in the workflow manifest

    - field: risk_class
      type: string
      enum:
        - advisory
        - low
        - medium
        - high
        - forbidden
      description: >
        Operator-assigned risk classification for this request.
        Used to determine whether approval is required and what audit tier applies.
      validation: required, must be consistent with the requested action and adapter

    - field: scope
      type: object
      description: >
        Explicit scope declaration for this request.
        Approval is always single-run and single-action scoped.
      sub_fields:
        - single_run: Boolean — true if this approval covers exactly one execution
        - expiration: ISO8601 timestamp after which this envelope is invalid (approvals must be consumed before expiration)
        - vault_root: Absolute or relative path to the vault root this request operates against
      validation: required, single_run must be true for all approval-required requests

    - field: approval_state
      type: string
      enum:
        - pending
        - approved_once
        - denied
        - needs_clarification
        - expired
      description: >
        Current approval state of this envelope.
        Default for new envelopes is "pending".
        Only an operator-tier account via the approvals channel may transition to "approved_once".
      validation: required, must be "pending" on creation; must be "approved_once" before execution proceeds for approval-required requests

    - field: audit_destination
      type: string
      description: >
        Vault path where the audit record for this request will be written.
        Must be within 07_LOGS/Agent-Activity/ or an approved audit surface.
      validation: required, must be under 07_LOGS/Agent-Activity/ in current state
      example: "07_LOGS/Agent-Activity/2026-04-20-discord-run-operator_today.md"

    - field: timestamp
      type: string
      format: ISO8601 datetime with timezone
      description: >
        The time this envelope was created (intake time, not Discord message time).
        Generated by the intake/classification layer, not by the Discord message author.
      validation: required, must be within a reasonable intake window (e.g. 60 seconds of Discord message timestamp)
      example: "2026-04-20T14:32:00Z"
```

---

## Validation Rules

```yaml
validation_rules:

  - id: deny-unknown-actor
    rule: >
      If actor.account_id does not match a registered entry in Discord-Identity-Map.md,
      deny immediately. Do not proceed to classification.

  - id: deny-unmapped-channel
    rule: >
      If source_channel_id does not match a registered channel in Discord-Channel-Registry.md,
      deny immediately. Do not proceed to classification.

  - id: deny-channel-class-mismatch
    rule: >
      If channel_class does not match the class assigned to source_channel_id in the registry,
      deny. Channel class must be resolved from the registry, not from message content.

  - id: deny-ineligible-adapter
    rule: >
      If adapter_target is not in the approved adapter list for the current repo state
      ("openclaw", "hermes", or "none"), deny. Unlisted adapters are always denied.
      "hermes" is valid only for hermes_operator_today_shadow workflow and advisory requests.

  - id: deny-unknown-workflow
    rule: >
      If workflow_id is non-null and does not resolve to an active manifest in
      runtime/workflows/registry/, deny. Unknown workflow IDs are never assumed valid.

  - id: deny-missing-required-field
    rule: >
      If any required field is absent, null when not nullable, or empty when non-empty
      is required, deny. Do not attempt partial execution.

  - id: deny-protected-write-target
    rule: >
      If any path in write_targets matches a protected file (see Permission-Matrix.md Section 2),
      deny immediately. Do not route to any adapter.

  - id: deny-pending-approval-for-execution
    rule: >
      If approval_state is "pending" and the requested action requires approval
      (risk_class != "advisory"), deny execution. Route to approvals channel for operator review.

  - id: deny-expired-envelope
    rule: >
      If scope.expiration is in the past, treat approval_state as "expired" and deny.
      Require a new envelope.

  - id: deny-prompt-injection-pattern
    rule: >
      If command_text, inputs, action_name, or any string field contains patterns
      that appear to be embedded instructions directed at an AI model, flag for operator
      review before proceeding. Do not execute. Log the pattern and the source channel.
```

---

## Approval State Transitions

```yaml
approval_state_transitions:

  - from: pending
    to: approved_once
    condition: >
      Operator-tier account (trust_tier=1) posts an explicit approval record
      in the registered "approvals" channel referencing this request_id,
      the exact command_text, and the exact write_targets.

  - from: pending
    to: denied
    condition: >
      Operator-tier account posts an explicit denial in the "approvals" channel
      referencing this request_id. OR: the envelope fails any validation rule.

  - from: pending
    to: needs_clarification
    condition: >
      Operator posts a clarification request in the approvals channel.
      Execution is blocked until state transitions to approved_once or denied.

  - from: approved_once
    to: expired
    condition: >
      scope.expiration is reached before execution completes.
      OR: the envelope has already been consumed by one execution run.

  - from: any
    to: expired
    condition: >
      scope.expiration is in the past. Treat as denied.
```

---

## Eligible OpenClaw Routes

In the current repo state, these are the only workflow_ids that may appear in an approved envelope targeting adapter_target=openclaw:

| workflow_id | Approval Required | Risk Class |
|---|---|---|
| `operator_today` | Yes (ad hoc Discord-triggered run) | medium |
| `operator_close_day` | Yes (ad hoc Discord-triggered run) | medium |
| `graph_hygiene` | Yes | low |
| null (status / advisory only) | No | advisory |

Scheduled runs that are already covered by a configured OpenClaw schedule and schedule intent entry are governed by that schedule approval, not an ad hoc envelope.

---

## Eligible Hermes Routes

In the current repo state, these are the only workflow_ids that may appear in an approved envelope targeting adapter_target=hermes:

| workflow_id | Approval Required | Risk Class |
|---|---|---|
| `hermes_operator_today_shadow` | Yes | low |
| null (advisory or status only) | No | advisory |

Hermes routes are bounded to advisory output and shadow read-only workflows. No write authority to canonical vault paths. Shell, connectors, canonical promotion, and protected-file write authority remain forbidden regardless of envelope state.

---

## Forbidden Envelope Targets

These must never appear in a valid envelope. Any envelope containing them is denied before classification.

```yaml
forbidden_targets:

  adapter_target_forbidden:
    - mcp_runtime
    - home_assistant
    - any_unknown_adapter

  workflow_id_forbidden:
    - any_workflow_with_status_draft
    - any_workflow_not_in_runtime_workflows_registry
    - any_hermes_workflow_not_listed_in_eligible_hermes_routes

  write_targets_forbidden:
    - SOUL.md
    - 00_HOME/Principles.md
    - 00_HOME/Operating-System.md
    - 00_HOME/Assistant-Contract.md
    - README.md
    - PROJECT_FOUNDATION.md
    - ROADMAP.md
    - FORKING.md
    - CLAUDE.md
    - 06_AGENTS/Agent-Control-Plane.md
    - 06_AGENTS/Permission-Matrix.md
    - 06_AGENTS/Trust-Tiers.md
    - 06_AGENTS/Handoff-Protocol.md
    - 02_KNOWLEDGE/ (any path — canonical promotion is not permitted from Discord)
    - runtime/policy/ (any path — policy files require governed update pass)
    - .chaseos/hermes_config.yaml
    - runtime/workflows/registry/ (manifests may not be created or modified from Discord)
    - 06_AGENTS/role-cards/ (role cards may not be created or modified from Discord)
```

---

## Example Valid Envelope (Advisory Only)

```yaml
envelope_example_advisory:
  request_id: "a3f2c1d0-7e84-4b12-9f01-c6e5d4b3a2f1"
  actor:
    account_id: "OPERATOR_DISCORD_USER_ID"
    display_name: "Chase (primary operator)"
    trust_tier: 1
    execution_eligible: true
  source_channel_id: "RUNTIME_CHAT_CHANNEL_ID"
  channel_class: runtime-chat
  adapter_target: none
  workflow_id: null
  action_name: "show schedule status"
  command_text: "chaseos schedule list"
  inputs: {}
  date_window: null
  read_targets:
    - runtime/schedules/index.yaml
  write_targets: []
  external_systems: []
  risk_class: advisory
  scope:
    single_run: true
    expiration: "2026-04-20T15:00:00Z"
    vault_root: "%CHASEOS_VAULT_ROOT%"
  approval_state: approved_once
  audit_destination: "07_LOGS/Agent-Activity/2026-04-20-discord-schedule-status.md"
  timestamp: "2026-04-20T14:32:00Z"
```

---

## Example Valid Envelope (Approval-Required Execution)

```yaml
envelope_example_execution:
  request_id: "b7e3f2a1-8c94-4d23-0e12-d7f6e5c4b3a2"
  actor:
    account_id: "OPERATOR_DISCORD_USER_ID"
    display_name: "Chase (primary operator)"
    trust_tier: 1
    execution_eligible: true
  source_channel_id: "CONTROL_PLANE_ROUTING_CHANNEL_ID"
  channel_class: control-plane-routing
  adapter_target: openclaw
  workflow_id: operator_today
  action_name: "run operator today briefing"
  command_text: "chaseos run operator_today"
  inputs:
    date: "2026-04-20"
  date_window: "2026-04-20"
  read_targets:
    - 00_HOME/Now.md
    - ROADMAP.md
    - 07_LOGS/Operator-Briefs/
    - 07_LOGS/Decision-Ledger/Index.md
  write_targets:
    - 07_LOGS/Operator-Briefs/2026-04-20-operator-today.md
    - 07_LOGS/Agent-Activity/
  external_systems: []
  risk_class: medium
  scope:
    single_run: true
    expiration: "2026-04-20T15:00:00Z"
    vault_root: "%CHASEOS_VAULT_ROOT%"
  approval_state: approved_once
  audit_destination: "07_LOGS/Agent-Activity/2026-04-20-discord-run-operator_today.md"
  timestamp: "2026-04-20T14:35:00Z"
```

---

## Activation Status

| Item | Status |
|---|---|
| Required field list defined | COMPLETE |
| Validation rules defined | COMPLETE |
| Approval state machine defined | COMPLETE |
| Eligible OpenClaw routes defined | COMPLETE |
| Forbidden targets defined | COMPLETE |
| Example envelopes defined | COMPLETE |
| Envelope validation wiring to classification layer | NOT BUILT — deferred to future pass |
| Approval ledger writeback to vault | NOT BUILT — deferred to future pass |

This file is part of Discord control-plane hardening Pass 1 (blockers 1–3 of 10).

Blockers 4–10 (request classifier, approval ledger, adapter allowlists, deny-by-default enforcement, red-team tests, dry-run mode, rollback documentation) remain open.

---

## Related Docs

- `06_AGENTS/ChaseOS-Discord-Control-Plane.md` — canonical Discord control-plane spec (approval model section)
- `06_AGENTS/Discord-Identity-Map.md` — operator and bot account identity map
- `06_AGENTS/Discord-Channel-Registry.md` — channel class registry
- `06_AGENTS/Permission-Matrix.md` — canonical permission source (protected file list)
- `OPENCLAW.md` — OpenClaw bounded adapter lane
- `06_AGENTS/Autonomous-Operator-Runtime.md` — AOR governance

---

*Graph links: [[Vault-Map]] · [[ChaseOS-Discord-Control-Plane]] | [[Discord-Identity-Map]] | [[Discord-Channel-Registry]] | [[Permission-Matrix]] | [[Autonomous-Operator-Runtime]] | [[OPENCLAW]]*

*Discord-Command-Envelope-Schema.md — Version 1.1 | Created: 2026-04-20 (Discord control-plane hardening Pass 1 — command envelope schema complete; validation wiring and approval ledger writeback deferred to future pass) | Updated: 2026-04-20 (Hermes Discord Activation Alignment Pass — hermes added to adapter_target enum; hermes_operator_today_shadow added to eligible workflow IDs; Eligible Hermes Routes table added; hermes removed from forbidden_targets; deny-ineligible-adapter rule updated)*
