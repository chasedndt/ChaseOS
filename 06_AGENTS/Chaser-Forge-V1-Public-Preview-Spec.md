---
title: Chaser Forge V1 Public Preview Spec
created: 2026-05-31
runtime: hermes-optimus
status: DRAFT / PREVIEW ONLY / NO PAID MARKETPLACE CLAIM
type: forge-spec
links:
  - [[ChaseOS-AI-Domain-Override-Handover-2026-05-31]]
  - [[Hermes-Runtime-Profile]]
  - [[HERMES]]
  - [[Agent-Activity-Index]]
---

# Chaser Forge V1 Public Preview Spec

## V1 scope

Chaser Forge V1 is a preview/catalog, not a paid marketplace.

## Required public surfaces

- `/forge` public overview page.
- `/forge/index.json` static preview at `https://chaseos.ai/forge/index.json`.
- Example packs with manifest/digest metadata.
- Pack submission waitlist via `/submit-pack`.
- Creator interest page via `/creators`.
- Pack standards docs.
- Install/preview instructions that preserve validation and approval gates.

## Must not claim

- no live paid checkout;
- no live licensing entitlement enforcement;
- no untrusted third-party install without validation;
- no automatic remote install bypassing approval;
- no creator payouts;
- no external hosted registry mutation.

## Future monetization strategy

- free packs: 0%;
- paid creator packs: 9%;
- certified packs: 12–15%;
- managed/runtime packs: 15–20% plus runtime credits;
- enterprise/private packs: custom.

## Codex tasks

Implement static Forge index, implement `/submit-pack`, validate example pack metadata, display `coming soon` for payments/licensing/managed install, and add tests for no-overclaim copy.
