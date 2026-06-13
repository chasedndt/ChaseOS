---
type: companion-roster
title: Companion Roster
status: COMPLETE / INITIAL ROSTER ADOPTED / CONFIG SURFACE WIRED / CHASER AGENT PLANNED
created: 2026-05-13
updated: 2026-06-06
runtime: Codex
---

# Companion Roster

## V0.1 Roster

The current ChaseOS companion roster contains three available companion profiles
and one planned coming-soon profile:

| Companion | Runtime Link | Role Summary | Tone / Identity |
|---|---|---|---|
| Hermes | `hermes` | Bounded runtime coordination companion | Careful shadow operator; calm, precise, audit-friendly |
| OpenClaw | `openclaw` | Local operator/runtime control companion | High-control local operator identity; visibly stronger governance warnings |
| Chaser Agent / Claude Code | `claude-code` / Studio alias `chaser_agent` | Engineering and architecture companion | Planning, architecture, strategy, system design, and governance reasoning |
| Chaser Agent | `chaser` | Planned internal ChaserAgent companion and gateway diagnostic surface | Coming soon; read-only profile/card only; not selectable or hatchable |

The roster is implemented in `runtime/companion/roster.py` and validated by
`runtime/companion/test_companion_policy.py`.

`runtime/studio/companion_apps_configuration.py` now builds the read-only
Companion Apps configuration inventory used by Studio Settings. It reports all
four companion cards, storage keys/paths, local UI settings, approval-gated
selection posture, proposal-only profile/memory metadata, and blocked runtime
authority surfaces. Chaser Agent remains visible as a planned card only; it is
not hatchable, selectable, live, or runtime-dispatchable.

## Profile Card Fields

Each profile card supports:

- `companion_id`
- `display_name`
- `runtime_identity`
- `short_description`
- `role_summary`
- `personality_preset`
- `tone_profile`
- `visual_mark`
- `border_style`
- `animation_preset`
- `status_states`
- `rarity`
- `stats`
- `capability_summary`
- `governance_boundary`
- `memory_scope`
- `routing_effect`
- `permission_effect`
- `current_status`
- `allowed_effects`
- `forbidden_effects`
- `commentary_policy`

Stats and rarity are cosmetic/descriptive only. They do not change runtime
capability, authority, model selection, routing, tool use, memory, or
permissions.

## Visual Tokens

V0.1 uses abstract runtime marks only:

- Hermes: `H`
- OpenClaw: `O`
- Chaser Agent / Claude Code: `C`
- Chaser Agent: `Ch`

Final avatars, brand assets, and icon files are deferred until a separate brand
pack pass.

Supported v0.1 visual states:

- `idle`
- `selected`
- `running`
- `waiting_for_approval`
- `blocked`
- `warning`
- `complete`
- `unavailable`

## Selection Boundary

The active companion model is one active companion per Chat session.

Companion selection writes are approval-gated and target only:

`runtime/studio/chat/companion-selection.json`

Selection also appends a switch ledger entry under:

`07_LOGS/Agent-Activity/companion-switch-ledger.jsonl`

For v0.1, every switch record must keep:

- `routing_changed=false`
- `memory_changed=false`
- `permissions_changed=false`

## Future Expansion

Future roster expansion may add project-specific companions, teaching
companions, security reviewer companions, trading research companions,
documentation companions, and Studio/UI companions. Chaser Agent is now present
as a planned coming-soon profile only; it is not a precedent for bypassing
runtime implementation, verification, or approval gates.

Future expansion must not bypass approval gates, runtime adapter boundaries,
role cards, Permission Matrix, Trust Tiers, or protected-file policy.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-15): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
