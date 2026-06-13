---
type: companion-policy
title: Companion Behavior Policy
status: COMPLETE / V0.1 POLICY ADOPTED / NO RUNTIME AUTHORITY
created: 2026-05-13
updated: 2026-06-06
runtime: Codex
---

# Companion Behavior Policy

## Core Rule

Companion identity is not runtime authority.

A ChaseOS companion is a runtime-linked identity profile for presentation, tone,
status narration, and non-authoritative commentary. Selecting Hermes, OpenClaw,
Claude Code / Archon, or Chaser Agent as a companion/profile must not activate
that runtime, widen permissions, invoke tools, change provider/model routing,
change AOR workflow routing, alter memory scope, or mutate canonical truth.

Runtime authority remains governed by AOR manifests, role cards, Permission
Matrix, Trust Tiers, protected-file policy, approval gates, and audit logs.

## V0.1 Allowed Effects

- Visual identity
- Profile card metadata
- Tone preset
- Status narration
- Read-only runtime card display
- Non-authoritative companion commentary
- One active companion per Chat session

## V0.1 Forbidden Effects

- Runtime routing changes
- Model/provider switching
- Memory scope changes
- Permission changes
- Tool access changes
- Connector access changes
- Protected-file access changes
- Workflow execution changes
- Canonical state mutation

## Commentary Policy

Companion comments are allowed as status flavor, runtime narration, progress
notes, warnings, teaching hints, approval reminders, and read-only observations.

Companion comments are forbidden from being executable instructions, policy
overrides, hidden prompts, permission grants, routing commands, canonical truth
updates, memory writes, or tool-call triggers.

Every companion comment is classified as `non_authoritative_commentary`.

## Tone Presets

The v0.1 policy supports these descriptive tone presets:

- `operator_direct`
- `strategist`
- `teacher`
- `security_reviewer`
- `calm_status`
- `debugger`

Tone changes phrasing, explanation style, status commentary, and directness. It
does not change policy, permissions, routing, memory, tool access, approval
boundaries, or execution rights.

## Selection Policy

Companion switching follows this flow:

1. List available companions.
2. Preview the target companion profile read-only.
3. Show current companion and proposed companion.
4. Show allowed v0.1 effects.
5. Show forbidden v0.1 effects.
6. Require approval before writing active selection.
7. Write active selection only to `runtime/studio/chat/companion-selection.json`.
8. Create a switch ledger entry.
9. Return confirmation that routing, memory, and permissions were unchanged.

## Memory Boundary

Separate companion memory is defined in v0.1 only as a governed, approval-gated,
non-authoritative namespace boundary. The current runtime may preview companion
memory namespaces and validate future memory candidates, but it may not write
memory files, consume memory approvals, or use companion memory as canonical
truth.

Companions may reference their static profile card, current session selection,
current runtime status if supplied, allowed status metadata, and any future
approved companion-memory records that pass the governed memory executor. They
may not keep secret state, hidden behavior drift, private execution history
outside logs, provider credentials, permission grants, protected-file facts, or
canonical truth-state records in companion memory.

Any future companion memory write requires a separate approval/executor pass.

## Implementation Evidence

The v0.1 local implementation lives in `runtime/companion/`:

- `policy.py` defines allowed/forbidden effects and authority flags.
- `schema.py` validates profile-card shape.
- `roster.py` exposes Hermes, OpenClaw, Claude Code, and Chaser Agent.
- `selection.py` implements read-only preview, approval-gated selection, and a
  companion switch ledger.
- `runtime/studio/companion_apps_configuration.py` exposes a read-only Studio
  configuration surface for roster, storage, Studio UI settings, memory
  boundaries, and blocked runtime authority. It also previews setting changes
  without writing files, consuming approvals, activating runtimes, calling
  providers, claiming/writing Agent Bus tasks, executing tools/shell commands,
  writing memory, or mutating canonical state.

The implementation preserves all authority-change flags as false.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
