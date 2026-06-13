---
title: Discord Channel Registry
type: control-plane-governance
status: ACTIVE — channel classes defined; per-runtime channel splits bound; Hermes channels active as bounded Discord runtime lane
version: 1.1
created: 2026-04-20
phase: 9
scope: Dual-runtime Discord control-plane — OpenClaw live, Hermes bounded active Discord lane
---

# Discord Channel Registry

> This file is a canonical governance record. It maps real Discord channels to canonical channel classes.
> It does not grant permissions. It assigns class and authority scope to each channel.
> Any channel not registered here is unmapped. All content from unmapped channels is Tier 4 untrusted.

---

## Canonical Rule

A Discord channel has no execution authority by its class alone. Class assignment constrains what actions and outputs are valid in a channel. Execution authority is further governed by identity, envelope validation, adapter scope, and workflow manifests.

---

## How to Use This File

1. Open your Discord server and copy the channel ID for each channel you want to assign to a class.
   - To get a channel ID: right-click the channel name → Copy Channel ID (Developer Mode must be on).
2. Fill in each `channel_id` and `channel_name` field for every class you want active.
3. A class with no `channel_id` filled in is inactive. Messages arriving without a matching registered channel ID are unmapped and denied.
4. A single Discord server is assumed. If multiple servers are ever used, this file must be extended with a `server_id` field per entry.

---

## Server

```yaml
server_id: "FILL_IN_DISCORD_SERVER_ID"
server_name: "FILL_IN_SERVER_NAME"
```

---

## Channel Class Registry

```yaml
channels:

  - channel_class: control-plane-routing
    channel_id: "FILL_IN_CHANNEL_ID"
    channel_name: "FILL_IN_CHANNEL_NAME"
    execution_authority: none_directly
    command_parsing: true
    writeback_allowed: false
    output_allowed: false
    eligible_actors:
      - operator
      - openclaw_bot
      - hermes_bot
    notes: >
      Intake operator intent and route to correct review path or eligible adapter.
      No direct execution from this channel. Routing decisions that lead to execution
      must be logged. Both OpenClaw and Hermes bots may post routing status here.

  - channel_class: runtime-chat
    channel_id: "FILL_IN_CHANNEL_ID"
    channel_name: "FILL_IN_CHANNEL_NAME"
    execution_authority: advisory_only
    command_parsing: false
    writeback_allowed: false
    output_allowed: true
    eligible_actors:
      - operator
      - openclaw_bot
      - hermes_bot
    notes: >
      Human and runtime conversation, low-stakes clarification, bounded status
      summaries. Advisory only. In practice, per-runtime channels are used
      (openclaw-chat / hermes-chat) so each runtime's conversation is isolated.
      Useful outcomes must be captured by a governed harness or AOR workflow
      before becoming ChaseOS state.

  - channel_class: approvals
    channel_id: "FILL_IN_CHANNEL_ID"
    channel_name: "FILL_IN_CHANNEL_NAME"
    execution_authority: approval_unlocks_named_action_only
    command_parsing: true
    writeback_allowed: false
    output_allowed: true
    eligible_actors:
      - operator
    notes: >
      Explicit operator approval or denial records only. Approval is scoped to one
      action, one target set, one adapter, and one run. Emoji reactions are NOT
      approvals. Approval records must be copied to audit before execution resumes.
      Only operator-tier accounts may issue valid approvals from this channel.

  - channel_class: audit-writeback
    channel_id: "FILL_IN_CHANNEL_ID"
    channel_name: "FILL_IN_CHANNEL_NAME"
    execution_authority: none
    command_parsing: false
    writeback_allowed: false
    output_allowed: true
    eligible_actors:
      - openclaw_bot
      - hermes_bot
    notes: >
      Output only. Append-only. Run summaries, audit links, writeback paths, failure
      records from all registered runtimes. No command parsing from this channel.
      The vault is the canonical audit store; Discord receives links and summaries only.

  - channel_class: alerts
    channel_id: "FILL_IN_CHANNEL_ID"
    channel_name: "FILL_IN_CHANNEL_NAME"
    execution_authority: none
    command_parsing: false
    writeback_allowed: false
    output_allowed: true
    eligible_actors:
      - openclaw_bot
      - hermes_bot
    notes: >
      Failures, scope violations, prompt-injection warnings, schedule health alerts
      from all registered runtimes. In practice, per-runtime channels are used
      (alerts-openclaw / alerts-hermes) so each runtime's alerts are isolated.
      Alert source and run ID must be included when available.

  - channel_class: debug
    channel_id: "FILL_IN_CHANNEL_ID"
    channel_name: "FILL_IN_CHANNEL_NAME"
    execution_authority: none_production
    command_parsing: false
    writeback_allowed: false
    output_allowed: true
    eligible_actors:
      - operator
      - openclaw_bot
      - hermes_bot
    notes: >
      Sanitized diagnostics, config status, dry-run output only. Never post secrets,
      tokens, full env dumps, or protected-file contents. No production execution
      from debug channel. In practice, per-runtime channels are used
      (debug-openclaw / debug-hermes). Debug commands that touch runtime state
      require a separate approval record in the approvals channel first.

  - channel_class: docs-archive
    channel_id: "FILL_IN_CHANNEL_ID"
    channel_name: "FILL_IN_CHANNEL_NAME"
    execution_authority: none
    command_parsing: false
    writeback_allowed: false
    output_allowed: true
    eligible_actors:
      - operator
      - openclaw_bot
      - hermes_bot
    notes: >
      Links to canonical vault docs, build logs, archive notes, and runbooks.
      Canonical docs live in the vault, not in Discord. Documentation visibility only.
```

---

## Unmapped Channel Rule

```yaml
unmapped_channel_rule:
  description: >
    Any channel_id not listed in this registry is unmapped.
    All input from an unmapped channel is Tier 4 untrusted.
    No routing, no execution, no approval recognition.
    Do not attempt to classify or route messages from unmapped channels.
    Log the unmapped channel event if a routing system is active.
  default_trust: 4
  default_execution_authority: none
```

---

## Authority Scope Reference

| authority_value | Meaning |
|---|---|
| `none_directly` | Channel may carry requests; no execution happens in this channel directly. Routing to review or eligible adapter only. |
| `advisory_only` | Content is advisory. No execution, no writeback, no approval. Useful output must be captured by a governed harness. |
| `approval_unlocks_named_action_only` | A valid approval record in this channel unlocks exactly the named action, target, adapter, and run. Does not generalize. |
| `none` | Output only. No commands. No execution. |
| `none_production` | Dry-run and diagnostic output only. No production execution without a prior approval record. |

---

## Execution Authority by Channel Class

| Channel Class | Execution Authority | Approval Authority | Commands Parsed | Output Posted |
|---|---|---|---|---|
| `control-plane-routing` | None directly | No | Yes (routing) | No |
| `runtime-chat` | Advisory only | No | No | Yes |
| `approvals` | Unlocks named action | Yes (operator only) | Yes (approvals) | Yes |
| `audit-writeback` | None | No | No | Yes |
| `alerts` | None | No | No | Yes |
| `debug` | None (production) | No | No | Yes |
| `docs-archive` | None | No | No | Yes |
| Unmapped | None | No | No | No |

---

## Instance Binding Layer

Real server and channel IDs are machine-local binding data, not open-source framework truth.

| Layer | Path | GitHub posture |
|---|---|---|
| Live local binding | `.chaseos/discord_instance_bindings.yaml` | Git-ignored / local only |
| GitHub-safe example | `runtime/bindings/discord_instance_bindings.example.yaml` | Tracked template |
| Setup guide | `04_SOPS/Discord-Control-Plane-Setup-SOP.md` | Tracked guide |

New users should copy the example file into `.chaseos/discord_instance_bindings.yaml`, fill their own channel IDs, and keep the copied file out of Git.

---

## Activation Status

| Item | Status |
|---|---|
| Channel class definitions complete | COMPLETE |
| Per-runtime channel split (openclaw/hermes) | COMPLETE — both runtimes have dedicated runtime-chat, alerts, debug channels |
| Server and all primary channel IDs | BOUND in `.chaseos/discord_instance_bindings.yaml` |
| Hermes channels active as bounded Discord runtime lane | COMPLETE |

Machine-local channel IDs live in `.chaseos/discord_instance_bindings.yaml`. The open-source-safe template lives at `runtime/bindings/discord_instance_bindings.example.yaml`.

---

## Related Docs

- `06_AGENTS/ChaseOS-Discord-Control-Plane.md` — canonical Discord control-plane spec (channel model section)
- `06_AGENTS/Discord-Identity-Map.md` — operator and bot account identity map
- `06_AGENTS/Discord-Command-Envelope-Schema.md` — authenticated command envelope schema
- `OPENCLAW.md` — OpenClaw bounded adapter lane

---

*Graph links: [[Vault-Map]] · [[ChaseOS-Discord-Control-Plane]] | [[Discord-Identity-Map]] | [[Discord-Command-Envelope-Schema]] | [[OPENCLAW]]*

*Discord-Channel-Registry.md — Version 1.1 | Created: 2026-04-20 (Discord control-plane hardening Pass 1 — channel registry schema complete; real channel IDs pending operator fill-in) | Updated: 2026-04-20 (Hermes Discord Activation Alignment Pass — hermes_bot added to eligible_actors for control-plane-routing, runtime-chat, audit-writeback, alerts, debug, docs-archive; per-runtime channel split pattern documented)*
