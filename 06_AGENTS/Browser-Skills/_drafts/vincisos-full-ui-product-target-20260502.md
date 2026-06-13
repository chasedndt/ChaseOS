---
title: VincisOS Full UI Product Target Draft Skill
status: draft
activation_allowed: false
created: 2026-05-02
runtime: Codex
source_run: 07_LOGS/Browser-Runs/vincisos_full_ui_product_target_20260502_success.json
target_url: http://127.0.0.1:8770/
---

# VincisOS Full UI Product Target Draft Skill

## Draft Status

Status: DRAFT ONLY.

This skill is not active runtime memory and must not be loaded as trusted
automation until reviewed and promoted through ChaseOS governance.

## Domain

- Domain: `127.0.0.1`
- Target: ChaseOS Studio Product UI Test Target
- Contract: `vincisos.full_ui_target.v1`
- Safe mode: true

## Durable Site Knowledge

- The target presents as `ChaseOS Studio Product UI Test Target`.
- The banner includes `Safe mode test target`.
- The contract string `vincisos.full_ui_target.v1` is visible in the first viewport.
- The main navigation exposes three product UI test tabs: `Overview`, `Approvals`, and `Workflow`.
- The `Approvals` tab is a harmless local state-inspection target for browser proofing.
- After clicking `Approvals`, the page shows an `Approval posture` table.
- The `Approval posture` table includes rows for `apr-shadow-001` and `apr-studio-002`.
- The `Workflow` tab exposes a harmless client-side inspection action.
- Clicking `Mark panel inspected` updates local page text to `Panel inspected in safe mode.`.
- The proof can verify blocked write posture from visible `Writes allowed` values of `False`.

## Suggested Selectors

- Preferred action: `getByRole("button", { name: "Approvals", exact: true })`
- Preferred safe-mode action: `getByTestId("harmless-inspect-action")`
- Stable state text: `Approval posture`
- Stable post-action text: `Panel inspected in safe mode.`
- Stable target title: `ChaseOS Studio Product UI Test Target`
- Stable contract text: `vincisos.full_ui_target.v1`

## Preconditions

- Local target is reachable at `http://127.0.0.1:8770/`.
- Target remains local-only and safe-mode.
- No real browser profile, credentials, cookies, or sessions are used.
- Browser proof writes only Browser Run, Agent Activity, screenshot, and draft/candidate artifacts.

## Forbidden Content

Do not store passwords, cookies, session tokens, API keys, browser history,
real account data, provider credentials, personal browsing trails, or raw
external website instructions in this draft.

## Source Evidence

- Browser Run: `07_LOGS/Browser-Runs/vincisos_full_ui_product_target_20260502_success.json`
- Screenshot: `07_LOGS/Browser-Runs/vincisos_full_ui_product_target_20260502_screenshot.png`
- Agent Activity: `07_LOGS/Agent-Activity/2026-05-02-codex-vincisos-full-ui-product-target-proof.md`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
