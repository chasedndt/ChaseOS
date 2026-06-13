---
type: feature-family
title: Workspace Mode Layer Feature Family
status: COMPLETE
created: 2026-05-14
updated: 2026-05-14
feature_family: workspace-mode-layer
runtime_package: runtime/workspace_modes/
studio_surface: runtime/studio/workspace_mode_panel.py
chat_surface: runtime/studio/phase11_chat_panel_contract.py
---

# Workspace Mode Layer Feature Family

The Workspace Mode Layer (WML) is the ChaseOS feature family that resolves the operating context of a workspace before agents read, reason, route, write, request approval, or invoke workflows.

WML is now a complete runtime/operator product feature with Studio and Chat visibility. It distinguishes `personal_os`, `study_research`, `founder_venture`, `business_ops`, `runtime_agent_ops`, and `unknown` contexts, then applies the existing ChaseOS governance stack rather than creating a second permission system.

## Current Status

**Status:** COMPLETE / VERIFIED / READ-ONLY STUDIO + CHAT SURFACES LIVE.

Implemented product surfaces:

- Runtime profile schema, inference, validation, and safe fallback under `runtime/workspace_modes/`
- Six validated workspace profiles across runtime, agent, ChaseOS project, SOP, university, and home contexts
- AOR route preview, dispatch gate, dry-run executor, exact-scope live-execution approval gate, and exact-once live executor
- Product-status and approval-ledger commands
- Read-only Studio Workspace Mode panel with URL-persistent `wml_mode` selector
- Project/domain/route cards inside the Studio WML panel
- Chat-side `Workspace Mode Studio` selector cards that deep-link into the Studio WML panel
- Desktop/mobile visual QA proof for the Studio panel and the Chat selector

## What WML Does

WML answers one question before action: what kind of workspace is this?

It can narrow:

- read order
- output class
- knowledge class
- allowed workflows
- adapter ceiling
- approval posture
- graph rules
- write targets

WML does not grant authority. Agent Control Plane, Permission Matrix, Trust Tiers, Gate, AOR manifests, adapter profiles, approval packets, and protected-path rules still decide what can happen.

## Feature Surfaces

| Surface | Status | Primary files |
|---|---|---|
| Architecture | COMPLETE | [[Use-Case-Mode-Architecture]], [[Workspace-Mode-Profile-Standard]] |
| Profile template | COMPLETE | [[05_TEMPLATES/Workspace-Mode-Profile-Template]] |
| Runtime package | COMPLETE | `runtime/workspace_modes/` |
| CLI/operator contracts | COMPLETE | [[ChaseOS-CLI-Command-Reference]], `runtime/cli.py`, `chaseos.py` |
| AOR routing/execution gates | COMPLETE | `runtime/workspace_modes/aor_routing_preview.py`, `aor_dispatch_gate.py`, `aor_dispatch_dry_run_executor.py`, `aor_live_execution_approval_gate.py`, `aor_live_executor.py` |
| Product status/ledger | COMPLETE | `runtime/workspace_modes/product_status.py` |
| Studio panel | COMPLETE / READ-ONLY | `runtime/studio/workspace_mode_panel.py`, `runtime/studio/desktop_shell_app.py` |
| Chat selector | COMPLETE / READ-ONLY | `runtime/studio/phase11_chat_panel_contract.py`, `runtime/studio/shell/frontend/app.js` |
| Visual QA | VERIFIED | `runtime/studio/workspace_mode_chat_deeplink_visual_qa.py`, `07_LOGS/Studio-Visual-QA/` |

## User-Facing Studio And Chat Path

Manual user path:

1. Open ChaseOS Studio.
2. Open the Chat page.
3. Preview `/dashboard` or load the default Chat panel.
4. Find `Workspace Mode Studio`.
5. Select a mode card such as `Founder / Venture`.
6. Open the linked Studio Workspace Mode panel.
7. Confirm the URL carries `wml_mode=founder_venture` and the panel filters project/domain/route context.

This is navigation-only. The Chat selector and Studio panel do not execute workflows, write profiles, consume approvals, dispatch Agent Bus tasks, call providers, or mutate canonical state.

## Completion Evidence

Core implementation passes:

- [[2026-05-13-ChaseOS-workspace-mode-layer]]
- [[2026-05-13-ChaseOS-workspace-mode-cli-contract]]
- [[2026-05-13-ChaseOS-workspace-mode-profile-rollout-plan]]
- [[2026-05-13-ChaseOS-workspace-mode-profile-draft-packet]]
- [[2026-05-13-ChaseOS-workspace-mode-profile-write-approval-request]]
- [[2026-05-13-ChaseOS-workspace-mode-guarded-profile-writer]]
- [[2026-05-14-ChaseOS-workspace-mode-aor-dispatch-gate]]
- [[2026-05-14-ChaseOS-workspace-mode-aor-dispatch-dry-run-executor]]
- [[2026-05-14-ChaseOS-workspace-mode-aor-live-executor-approval-gate]]
- [[2026-05-14-ChaseOS-workspace-mode-aor-live-executor]]
- [[2026-05-14-ChaseOS-workspace-mode-full-product-feature]]

Studio and Chat product passes:

- [[2026-05-14-ChaseOS-workspace-mode-studio-panel]]
- [[2026-05-14-ChaseOS-workspace-mode-studio-panel-browser-qa]]
- [[2026-05-14-ChaseOS-workspace-mode-studio-ux-mode-project-selector]]
- [[2026-05-14-ChaseOS-workspace-mode-studio-selector-state-contract]]
- [[2026-05-14-ChaseOS-workspace-mode-chat-deeplink-selector]]

Manual/handoff documents:

- [[07_LOGS/Operator-Briefs/2026-05-14-workspace-mode-manual-testing-guide]]
- [[07_LOGS/Operator-Briefs/2026-05-14-workspace-mode-studio-panel-human-action-guide]]
- [[07_LOGS/Operator-Briefs/2026-05-14-workspace-mode-studio-ux-mode-project-selector-human-action-guide]]
- [[07_LOGS/Operator-Briefs/2026-05-14-workspace-mode-studio-selector-state-contract-human-action-guide]]
- [[07_LOGS/Operator-Briefs/2026-05-14-workspace-mode-chat-deeplink-selector-human-action-guide]]

Visual proof:

- [[07_LOGS/Studio-Visual-QA/2026-05-14-workspace-mode-studio-panel/2026-05-14-workspace-mode-studio-panel-browser-qa]]
- [[07_LOGS/Studio-Visual-QA/2026-05-14-workspace-mode-studio-ux-mode-project-selector/workspace-mode-selector-browser-proof]]
- [[07_LOGS/Studio-Visual-QA/2026-05-14-workspace-mode-studio-selector-state-contract/workspace-mode-selector-state-browser-proof]]
- [[07_LOGS/Studio-Visual-QA/2026-05-14-workspace-mode-chat-deeplink-selector/visual-qa-report]]

## Boundaries

WML explicitly does not provide:

- RBAC, team accounts, enterprise packaging, or multi-user permissions
- broad live runtime autonomy
- unapproved AOR execution
- ambient Agent Bus task creation
- profile overwrites
- provider/model calls
- browser/external actions
- approval consumption outside exact-scope executors
- canonical promotion or protected-file mutation
- Pulse memory, Personal Map, or R&D truth-state mutation

## Remaining Work

No required WML implementation pass remains.

Optional follow-up:

- `workspace-mode-chat-deeplink-live-host-click-qa` if the operator wants live pywebview click-through proof after manual testing.

## Graph Links

[[Use-Case-Mode-Architecture]] [[Workspace-Mode-Profile-Standard]] [[Workspace-Mode-Profile-Template]] [[Agent-Control-Plane]] [[Permission-Matrix]] [[Trust-Tiers]] [[Agent-Registry]] [[Backends-Supported]] [[Autonomous-Operator-Runtime]] [[ChaseOS-Studio-Architecture]] [[ChaseOS-Phase11-Architecture]] [[ChaseOS-CLI-Command-Reference]] [[Feature-Fit-Register]] [[Vault-Map]] [[Build-Logs-Index]] [[Documentation-History-Index]] [[2026-05-14]]
