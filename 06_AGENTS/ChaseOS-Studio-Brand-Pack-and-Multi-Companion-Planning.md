---
type: architecture-planning
title: ChaseOS Studio Brand Pack and Multi-Companion Planning
created: 2026-05-12
updated: 2026-05-13
status: PLANNED / CONTRACT SEEDED / OPERATOR COMPANION DIRECTION CAPTURED / NO ASSET GENERATION
runtime: Codex
---

# ChaseOS Studio Brand Pack and Multi-Companion Planning

## Status

**PLANNED / CONTRACT SEEDED / OPERATOR COMPANION DIRECTION CAPTURED / NO ASSET GENERATION.**

This pass records the missing brand/logo/installer identity lane and the multi-companion planning gap before the next Studio UI or installer pass. It does not generate a logo, rewrite the UI, package branded installer assets, execute companion selection, call providers, dispatch runtimes, or mutate canonical state.

2026-05-12 update: the operator is not ready for logo/brand asset generation yet. The next brand lane is manual guidepack review through [[ChaseOS-Studio-Manual-Branding-Guidepack]], not immediate asset generation.

2026-05-12 companion update: `phase11-multi-companion-registry-readiness` is now COMPLETE / READ-ONLY / VERIFIED. The registry/schema can be validated against builtin Hermes/OpenClaw/Archon status cards, but the registry is not loaded for selection and no roster UI or executor has been built.

2026-05-12 direction update: `operator-companion-direction-before-roster-ui` is now COMPLETE / READ-ONLY / VERIFIED. The direction packet lists Hermes/OpenClaw/Archon, exposes ten unanswered operator decisions with recommended defaults, and keeps roster UI blocked until the operator answers them.

2026-05-13 direction-answer update: `operator-answer-companion-direction-questions` is now COMPLETE / OPERATOR-APPROVED / READ-ONLY POLICY CAPTURE / NO AUTHORITY EXPANSION. The approved v0.1 policy is stored at `runtime/studio/chat/companions/operator-direction.v0.1.json`; it keeps Hermes/OpenClaw/Archon, makes selection per Chat session, allows only UI identity/tone/status/read-only-card/non-authoritative comments, and blocks routing, provider/model selection, permissions, writeback, memory, tool access, protected-file access, runtime dispatch, Agent Bus task writes, and canonical mutation. Next companion pass is `phase11-companion-roster-ui-preview`.

## Repo-Truth Baseline

- Studio installer-build execution proof for packet `studio-installer-build-appr-ac14811da651baec` is complete and verified as a scoped `zip-portable` proof.
- The current portable ZIP proof does not include a branded installer logo, app icon, shortcut icon, install wizard, signed installer, or release-ready visual identity pack.
- Phase 11 companion status and companion-selection preview/queue/readiness surfaces exist, but `runtime/studio/chat/companions/` was not present before this pass.
- Existing companion code already treats companions as more than one possible runtime-facing UX card (`hermes`, `openclaw`, `archon`), but the future durable registry and roster model still needed an explicit contract.
- Companion personality/status remains UX only and never grants runtime authority, trust tier, Gate permission, provider access, Agent Bus write access, or canonical mutation authority.

## Brand Pack Contract

The Studio brand pack should be treated as a product/release dependency before any real installable release lane is claimed complete.

Required future surfaces:

- source logo mark for `ChaseOS Studio`
- app/window/taskbar icon
- Windows `.ico` bundle
- installer or wizard image assets if an installer technology is adopted
- shortcut/Start Menu icon
- splash/about/settings brand mark
- in-app brand token set for colors, typography, spacing, icon usage, and companion avatar compatibility
- docs/screenshot brand metadata for release evidence

Seeded runtime contract:

- `runtime/studio/brand/README.md`
- `runtime/studio/brand/brand-pack.contract.json`

The next brand implementation pass should generate or place candidate assets under the contract paths, verify image dimensions and file presence, and keep signing/startup/release/host mutation separate.

## Multi-Companion Contract

The companion system must support a roster, not a singleton.

Core rules:

- More than one companion can exist.
- One active companion may be selected per surface/session unless a future multi-companion conversation mode is explicitly designed.
- Companion selection is preference/state, not authority.
- Companion profile, avatar, tone, and status display never override runtime profiles, role cards, trust tiers, Gate rules, Approval Center posture, or Agent Bus boundaries.
- Every selection write remains approval/executor governed; the verified companion-selection approval-consumption executor does not grant roster UI, provider/model routing, runtime dispatch, or canonical authority.

Seeded runtime contract:

- `runtime/studio/chat/companions/README.md`
- `runtime/studio/chat/companions/companion-profile.schema.json`
- `runtime/studio/chat/companions/registry.example.json`

Minimum future companion profile fields:

- `companion_id`
- `display_name`
- `runtime_id`
- `status`
- `avatar`
- `tone_tags`
- `supported_surfaces`
- `authority`
- `selection`
- `evidence`

## UI Implications

Brand and companion design should land before another broad Studio visual polish pass because both affect:

- sidebar identity
- Chat welcome and status cards
- companion roster/picker cards
- `/pet` and dashboard response cards
- installer metadata and shortcut presentation
- screenshots used as release/readiness evidence

The UI should consume tokens and assets from the brand pack instead of hardcoding a one-off logo/color decision in frontend CSS.

## Recommended Pass Order

1. `studio-brand-pack-contract-validation`
2. `studio-brand-manual-guidepack-review`
3. `studio-logo-brand-candidate-directions`
4. `studio-brand-token-ui-preview`
5. `phase11-multi-companion-registry-readiness` - complete/read-only/verified
6. `operator-companion-direction-before-roster-ui` - complete/read-only/verified
7. `operator-answer-companion-direction-questions` - complete/operator-approved/read-only/verified
8. `phase11-companion-roster-ui-preview`
9. `phase11-chat-companion-selection-approval-consumption-executor`
10. `studio-installer-brand-asset-packaging-preview`
11. governed signing/startup/release/host follow-through or explicit MVP deferral

## Boundaries

This planning pass did not:

- generate bitmap or vector logo assets
- choose final brand colors or typography
- mutate Studio frontend UI
- write companion selection target state
- approve, consume, or execute approval artifacts
- call providers/models
- dispatch runtimes or browser tasks
- write Agent Bus tasks
- mutate Gate/Git/workflow/host/release state
- mutate Pulse memory, Personal Map, R&D truth-state, or canonical ChaseOS state


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
