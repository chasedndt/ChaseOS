# ChaseOS Studio Brand Runtime Contract

Status: PLANNED / CONTRACT SEEDED / NO ASSETS GENERATED.

This folder is the runtime-side target for the future Studio brand pack. It is not a release asset pack yet.

Canonical brand documentation now lives in `docs/brand/`. The runtime brand contract should follow those docs, but final logo/icon/UI assets remain planned until a separate asset-generation and validation pass completes.

Current contract:

- `brand-pack.contract.json` defines expected asset classes, future paths, and blocked authorities.
- `06_AGENTS/ChaseOS-Studio-Manual-Branding-Guidepack.md` is the operator-facing manual guide before asset generation.
- `docs/brand/ChaseOS_Logo_Candidate_Directions.md` defines reviewable candidate directions.
- `docs/brand/Studio_Brand_Asset_Generation_Plan.md` defines the governed path from direction approval to concept generation, source assets, icon exports, UI previews, and installer previews.
- No logo, icon, installer image, shortcut, or signed release artifact is present from this pass.
- UI and installer code should not claim brand-pack completion until the required files exist and a validation pass proves dimensions, formats, and references.

Boundaries:

- no signing
- no installer wizard generation
- no startup/autostart or host mutation
- no release promotion
- no provider/runtime/browser dispatch


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
