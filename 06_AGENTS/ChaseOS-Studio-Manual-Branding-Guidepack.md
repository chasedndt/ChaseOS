---
type: product-guidepack
title: ChaseOS Studio Manual Branding Guidepack
created: 2026-05-12
updated: 2026-05-12
status: GUIDE READY / CANDIDATE DIRECTIONS AVAILABLE / NO ASSETS GENERATED
runtime: Codex
---

# ChaseOS Studio Manual Branding Guidepack

## Status

**GUIDE READY / CANDIDATE DIRECTIONS AVAILABLE / NO ASSETS GENERATED.**

This guidepack exists so the operator can manually explore brand direction before Codex generates or packages Studio logo/icon assets. It does not choose the final logo, generate images, mutate Studio UI, rebuild the installer, sign artifacts, or promote a release.

Candidate direction docs now exist in `docs/brand/ChaseOS_Logo_Candidate_Directions.md`, with the governed asset path in `docs/brand/Studio_Brand_Asset_Generation_Plan.md`.

## Product Names

- Framework/internal system: `ChaseOS`
- Desktop product shell: `ChaseOS Studio`
- Phase 11 conversational UI: `ChaseOS Chat`
- Internal code/package naming remains `chaseos`; do not rename modules, imports, commands, or runtime folders for branding.
- Canonical brand source: `docs/brand/`

## Design Questions To Decide First

- Should the mark feel like an operating system, a command center, a graph intelligence tool, or a personal AI workspace?
- Should the logo emphasize `ChaseOS` as a sovereign framework, `Studio` as the desktop product, or both?
- Should the visual identity feel sharp/technical, calm/utilitarian, premium/futuristic, or warm/personal?
- Should the mark be abstract, monogram-based, graph/node-based, terminal/control-plane inspired, or companion-friendly?
- Should companion avatars inherit the same mark language or have a softer separate style?
- Should first-run surfaces emphasize `ChaseOS`, `ChaseOS Studio`, or `ChaseOS Chat` based on the surface?
- What should never be implied visually: uncontrolled AI, surveillance, crypto-only, generic chatbot, or corporate SaaS blandness?

## Brand Principles

- Human intent. Agentic execution. Private control.
- Human core. Agent network. Private boundary. Controlled execution.
- Local-first and sovereign: the system belongs to the operator.
- Governed and bounded: the identity should communicate control, not chaos.
- Graph-first: Studio is a visual operating surface, not a chat wrapper.
- Runtime-aware: agents and companions are visible but not authority owners.
- Product-grade: the installer/icon must feel like a real desktop app, not an experiment.
- Calm under load: avoid noisy, gimmicky, or overly decorative branding that fights dense operational UI.

## Core Visual Decisions

Choose these before asset generation:

- Primary mark: full logo, symbol-only icon, or monogram plus wordmark.
- Wordmark text: `ChaseOS Studio`, `ChaseOS`, or split treatment.
- Symbol direction: node graph, OS window, command mark, compass/control-plane, vault/core, or abstract signal.
- Shape language: angular, geometric, circular, layered, or grid-based.
- Color posture: restrained dark UI with a few high-signal accent colors; avoid one-note purple/blue gradients or overly beige/cream/brown palettes.
- Companion compatibility: mark should survive next to companion avatars without turning the UI into mascot-first software.
- Small-size legibility: the app icon must remain readable at 16px and 32px.

## Required Asset Inventory

Create or approve these before branded installer packaging:

| Asset | Target Path | Notes |
|---|---|---|
| Editable source logo | `runtime/studio/brand/source/chaseos-studio-logo.svg` | Clean vector master; must work on dark and light backgrounds. |
| Source bitmap review export | `runtime/studio/brand/source/chaseos-studio-logo.png` | High-resolution preview export for docs/review. |
| Symbol-only source | `runtime/studio/brand/source/chaseos-studio-symbol.svg` | Needed for icon derivation and compact UI. |
| Windows icon bundle | `runtime/studio/brand/icons/chaseos-studio.ico` | Must include 16/24/32/48/64/128/256 px where tooling supports it. |
| PNG icon set | `runtime/studio/brand/icons/png/` | 16, 24, 32, 48, 64, 128, 256, 512, 1024 px. |
| Installer/wizard assets | `runtime/studio/brand/installer/` | Future installer sidebar/banner/header images; exact dimensions depend on installer tech. |
| Shortcut/Start Menu preview | `runtime/studio/brand/installer/shortcut-preview.png` | For manual review before any host mutation. |
| Splash/about mark | `runtime/studio/brand/ui/chaseos-studio-about.png` | For future About/settings surfaces. |
| UI brand tokens | `runtime/studio/brand/tokens/studio-brand-tokens.json` | Color, typography, border, icon, and avatar token contract. |
| Release screenshot framing | `runtime/studio/brand/release/screenshot-frame.json` | Optional metadata for consistent release screenshots. |

## UI Surfaces Affected

- Studio title/sidebar identity
- graph canvas empty/loading states
- Chat welcome and status cards
- `/dashboard`, `/pet`, `/models`, `/runtime status` read-only response cards
- companion roster and companion picker
- Approval Center visual trust/status indicators
- installer metadata, shortcut icon, and future Start Menu/Desktop entry
- docs screenshots and release evidence packets

## Installer And Release Considerations

- The current installer proof is a portable ZIP, not a full branded installer.
- A future real installer may need different dimensions depending on NSIS, WiX/MSI, MSIX, Inno Setup, or another packaging path.
- Do not claim installer branding is complete until the asset pack is present, validated, and referenced by packaging code.
- Signing, startup/autostart, shortcut creation, Start Menu entries, registry writes, and release promotion remain separate governed lanes.

## Companion Design Considerations

- Companion visuals should not imply elevated authority.
- Companion avatars may be runtime marks, generated character/avatar art, initials, or brand-derived icon variants.
- The roster must support more than one companion.
- A selected companion is a UX preference, not a permission grant.
- Companion status cards should remain compact and operational; avoid mascot-heavy UI that makes the control plane feel less serious.

## Manual Review Checklist

Before asking Codex to generate or package assets, decide:

- primary logo concept
- symbol-only icon direction
- rough color palette
- typography direction
- whether companion avatars are abstract marks, character-like companions, or simple runtime badges
- whether `ChaseOS Chat` needs a light sub-surface treatment or should inherit the main ChaseOS mark directly
- whether the first generated pass should produce one polished direction or three candidate directions
- whether final assets should be SVG-first, bitmap-first, or both

## Future Codex Passes

Recommended order:

1. `studio-brand-manual-guidepack-review`
2. `studio-brand-candidate-directions` - current candidate directions now documented
3. `studio-brand-operator-direction-selection`
4. `studio-logo-concept-generation-preview`
5. `studio-brand-asset-generation`
6. `studio-brand-token-ui-preview`
7. `studio-installer-brand-asset-packaging-preview`

Do not run `studio-brand-asset-generation` until the operator has chosen the manual direction or approved candidate exploration.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
