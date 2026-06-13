---
title: ChaseOS Studio Phase 10A+ Branch-Out Coordination
date: 2026-05-04
runtime: Codex
status: ACTIVE / CO-DEVELOPMENT LOCK / NATIVE SHELL PRIMARY
---

# ChaseOS Studio Phase 10A+ Branch-Out Coordination

**Approval Center routing:** the native Approval Center panel described here is tracked canonically in [[ChaseOS-Approval-Center]] for source-family mapping and authority boundaries.

## Current Studio Truth

- Canonical Phase 10 implementation tracker: `06_AGENTS/ChaseOS-Studio-Phase10-Implementation-Tracker.md`.
- Primary product lane: `chaseos studio shell`.
- Primary implementation surface: `runtime/studio/shell/` native PyWebView shell.
- Legacy compatibility/QA harness: `chaseos studio desktop-shell-app`.
- The localhost `desktop-shell-app` route is not the canonical product shell. It remains useful for bounded route/HTML/JSON evidence and compatibility checks.
- Browser Runtime operator UI has a read-only readiness contract and is mounted as a native read-only Studio panel.
- Workspace Entry / Open Folder readiness is mounted as a native read-only Studio panel.
- Settings + Runtime Controls is mounted as a native read-only Studio panel.
- Approval Center is mounted as a native read-only Studio panel aggregating Pulse, Studio service approval queue, OSRIL, Gate request artifacts, runtime resume evidence, SiteOps approvals, and startup-control approval posture.
- Runtime Cockpit is mounted as a native read-only Studio panel surfacing runtime health profiles, coordination-watch artifacts, startup drift posture, logs/audit inventory, and post-reboot indicators.
- Runtime Intelligence panels are mounted as native read-only Studio panels: Provenance Explorer, Memory Ledger, Agent Identity, and Runtime Navigation Map.
- Native shell panel registry is built through `runtime/studio/shell/panel_registry.py` and exposed through `StudioAPI.get_panel_registry()`.
- Current native mounted panels are tracked canonically in `06_AGENTS/ChaseOS-Studio-Phase10-Implementation-Tracker.md`; latest registry evidence reports 22 mounted panels through Pass 10R Decision Ledger.
- Browser Runtime is mounted in the native shell through `StudioAPI.get_browser_runtime_panel()`.
- Workspace Entry is mounted in the native shell through `StudioAPI.get_workspace_entry_panel()`.
- Settings is mounted in the native shell through `StudioAPI.get_settings_runtime_controls_panel()`.
- Approval Center is mounted in the native shell through `StudioAPI.get_approval_center_panel()`.
- Runtime Cockpit is mounted in the native shell through `StudioAPI.get_runtime_cockpit_panel()`.
- Provenance Explorer is mounted in the native shell through `StudioAPI.get_provenance_explorer_panel()`.
- Memory Ledger is mounted in the native shell through `StudioAPI.get_memory_ledger_panel()`.
- Agent Identity is mounted in the native shell through `StudioAPI.get_agent_identity_panel()`.
- Runtime Navigation Map is mounted in the native shell through `StudioAPI.get_runtime_navigation_map_panel()`.
- Intake / Quarantine is mounted in the native shell through `StudioAPI.get_intake_panel()`.
- SIC Workspace Browser is mounted in the native shell through `StudioAPI.get_sic_workspace_detail(slug)`.
- Node Inspector Provenance tab is productized in the native shell and hydrates read-only sidecar provenance through `StudioAPI.get_provenance()`.
- Real Desktop Packaging now has a read-only readiness contract at `chaseos studio packaging-readiness --json` and bounded static QA at `chaseos studio qa-runner --surface packaging --mode static --json`.
- The packaging readiness pass declares Studio packaging extras, package-data coverage for native frontend assets, a PyInstaller spec template, and PyInstaller `_MEIPASS` frontend resolution. It does not build an executable or installer.
- Local packaging proof now has a bounded command at `chaseos studio local-packaging-proof --execute-build --json`; the latest proof built `ChaseOS-Studio.exe` under `.pytest_tmp_env/studio-packaging-proof/dist/` and did not launch the app or create an installer.
- Packaged app launch smoke now has a bounded command at `chaseos studio packaged-app-launch-smoke --json`; the latest smoke launched the packaged executable, confirmed it stayed alive for the settle window, terminated the owned process, and wrote evidence without installer/startup/canonical mutation.
- Packaged app visual QA now has a bounded command at `chaseos studio packaged-app-visual-qa --write-evidence --json`; the latest visual QA launched the packaged executable, captured a native PNG screenshot, terminated the owned process, and wrote evidence without installer/startup/canonical mutation.
- Installer plan and governance now has a read-only command at `chaseos studio installer-plan --json`; the latest plan requires packaging readiness, local packaging proof, launch smoke, and visual QA evidence, then declares installer-build, signing, startup/autostart, and release-promotion gates without writing installer/startup/canonical state.
- Browser Runtime production closeout now has a bounded command at `chaseos studio browser-runtime-production-closeout --json`; the internal Studio Browser Runtime panel lane is complete, Browser Use safe-URL validation is complete targeted, and the public Excalidraw drawing proof is complete targeted. The local loopback Excalidraw/MCP lane remains optional and governed.
- Product hardening now has a bounded static QA surface at `chaseos studio qa-runner --surface product-hardening --mode static --json`; it composes the native shell panel registry, Browser Runtime production closeout, packaging readiness, and installer governance without launching PyWebView, starting servers, building executables, creating installers, signing artifacts, mutating startup, running Browser Use/Excalidraw, calling providers/connectors, writing Agent Bus tasks, mutating Gate, or writing canonical state.
- Release-readiness governance now has a read-only command at `chaseos studio release-readiness-governance --json` and bounded static QA at `chaseos studio qa-runner --surface release-governance --mode static --json`; it composes product hardening and installer plan evidence, declares the installer-build, signing, startup/autostart, and release-promotion gates, and confirms no approval artifact creation/consumption, installer build, signing, startup mutation, release promotion, PyWebView/server/executable launch, Browser Use/Excalidraw run, provider/connector call, Agent Bus write, Gate mutation, workflow execution, or canonical writeback.
- Governed installer-build approval preview now has a read-only command at `chaseos studio governed-installer-build-approval --json` and bounded static QA at `chaseos studio qa-runner --surface installer-build-approval --mode static --json`; it composes release-readiness governance, previews packet `studio-installer-build-appr-4efe404083dae669`, exact approval artifact path, exact-once marker path, future installer output paths, dry-run plan, rollback/audit requirements, and confirms no approval artifact write, approval decision consumption, marker reservation, executable/installer build, signing, startup/autostart/registry/shortcut write, release promotion, PyWebView/server/executable launch, Browser Use/Excalidraw run, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback.
- Installer-build approval operator review now has `chaseos studio installer-build-approval-review --json` and bounded static QA at `chaseos studio qa-runner --surface installer-build-approval-review --mode static --json`; it wrote the scoped matching approval artifact `07_LOGS/Agent-Activity/_studio_installer_build_approvals/studio-installer-build-appr-4efe404083dae669.json` and confirms no approval consumption, exact-once marker reservation, installer output, dry-run/execution evidence, signing, startup/autostart/registry/shortcut write, release promotion, PyWebView/server/executable launch, Browser Use/Excalidraw run, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback.
- Installer-build approval consumption dry-run now has `chaseos studio installer-build-approval-consumption-dry-run --json` and bounded static QA at `chaseos studio qa-runner --surface installer-build-approval-consumption-dry-run --mode static --json`; it validates the written approval artifact digest and one-build scope, proves exact-once marker reservation and duplicate-consumption blocking in memory, verifies future output paths are clear, and confirms no approval consumption, real marker reservation, installer output, manifest, dry-run/execution evidence, signing, startup/autostart/registry/shortcut write, release promotion, PyWebView/server/executable launch, Browser Use/Excalidraw run, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback.
- Installer-build approved execution proof now has `chaseos studio installer-build-approved-execution-proof --json` and bounded static QA at `chaseos studio qa-runner --surface installer-build-approved-execution-proof --mode static --json`; it consumed approval packet `studio-installer-build-appr-4efe404083dae669`, reserved/completed the exact-once marker before output writes, wrote the portable ZIP, manifest, audit, dry-run, and execution evidence under the approved proof paths, blocks duplicate execution, and confirms no signing, signing certificate read, startup/autostart/registry/shortcut write, release promotion, PyWebView/server/executable launch, Browser Use/Excalidraw run, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback.
- Signing approved execution proof now has `chaseos studio signing-approved-execution-proof --json` and bounded static QA at `chaseos studio qa-runner --surface signing-approved-execution-proof --mode static --json`; it consumed approval packet `studio-signing-appr-c6d0561f9a8f921e`, reserved/completed the exact-once marker before proof-signed output writes, resolved only the opaque certificate profile label, wrote proof-signed portable ZIP `.pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip`, manifest, audit, dry-run, and execution evidence under approved proof paths, blocks duplicate execution, and confirms no raw signing certificate/secret read, production code-signing claim, startup/autostart/registry/shortcut write, release promotion, PyWebView/server/executable launch, Browser Use/Excalidraw run, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback.
- Startup/autostart approval preview now has `chaseos studio startup-autostart-approval-preview --json` and bounded static QA at `chaseos studio qa-runner --surface startup-autostart-approval-preview --mode static --json`; it inspects the completed signing proof and proof-signed ZIP/manifest hashes, previews packet `studio-startup-autostart-appr-a90e121d6b079a51`, future approval artifact, exact-once marker, dry-run/execution evidence, rollback, and audit paths, enumerates host target categories without resolving host paths, and confirms no approval artifact write, approval consumption, marker reservation, host startup/autostart/registry/Start Menu/desktop shortcut mutation, release promotion, PyWebView/server/executable launch, Browser Use/Excalidraw run, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback.
- Startup/autostart approval operator review now has `chaseos studio startup-autostart-approval-review --json` and bounded static QA at `chaseos studio qa-runner --surface startup-autostart-approval-review --mode static --json`; it wrote the scoped matching approval artifact `07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/studio-startup-autostart-appr-a90e121d6b079a51.json` for packet `studio-startup-autostart-appr-a90e121d6b079a51`, confirms the digest and signed ZIP/manifest hashes, and confirms no approval consumption, exact-once marker reservation, host path resolution, host startup/autostart/registry/Start Menu/desktop shortcut mutation, release promotion, PyWebView/server/executable launch, Browser Use/Excalidraw run, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback.
- Startup/autostart approval consumption dry-run now has `chaseos studio startup-autostart-approval-consumption-dry-run --json` and bounded static QA at `chaseos studio qa-runner --surface startup-autostart-approval-consumption-dry-run --mode static --json`; it validates the scoped approval artifact digest/scope/source hashes for packet `studio-startup-autostart-appr-a90e121d6b079a51`, proves exact-once marker reservation and duplicate-consumption blocking in memory, verifies future startup/autostart output paths are clear, and confirms no approval consumption, real marker write, host path resolution, host startup/autostart/registry/Start Menu/desktop shortcut mutation, release promotion, PyWebView/server/executable launch, Browser Use/Excalidraw run, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback.
- Release-promotion approval preview now has `chaseos studio release-promotion-approval-preview --json` and bounded static QA at `chaseos studio qa-runner --surface release-promotion-approval-preview --mode static --json`; it inspects the completed startup/autostart execution proof, exact-once marker, proof-signed ZIP, signing manifest, startup evidence, host mutation audit, and rollback plan, previews packet `studio-release-promotion-appr-d698d13b011ccf06`, future approval artifact, exact-once marker, release evidence, manifest, release-status preview, audit, rollback paths, and confirms no approval artifact write, approval consumption, marker reservation, release-status write, release promotion, host startup/autostart/registry/shortcut mutation, Studio launch, Browser Use/Excalidraw run, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback.
- Release-promotion approval operator review now has `chaseos studio release-promotion-approval-review --json` and bounded static QA at `chaseos studio qa-runner --surface release-promotion-approval-review --mode static --json`; it wrote the scoped matching approval artifact `07_LOGS/Agent-Activity/_studio_release_promotion_approvals/studio-release-promotion-appr-d698d13b011ccf06.json` for packet `studio-release-promotion-appr-d698d13b011ccf06`, confirms the digest plus signed ZIP/signing manifest/startup evidence hashes, and confirms no approval consumption, exact-once marker reservation, release-status write, release promotion, host startup/autostart/registry/shortcut mutation, Studio launch, Browser Use/Excalidraw run, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback.
- External runtime readiness now has a bounded command at `chaseos studio external-runtime-readiness --json`; it reports whether Browser Use CLI or local-loopback Excalidraw branches may start, honors `CHASEOS_BROWSER_USE_CLI`, and currently reports Browser Use ready when set to `C:\tmp\chaseos-browser-use-cli-venv\Scripts\browser-use.exe` while the local Excalidraw lane remains blocked pending a loopback URL.
- External runtime setup request now has a bounded handoff command at `chaseos studio external-runtime-setup-request --json`; it produces exact Browser Use CLI and Excalidraw setup requests for an external runtime/operator without installing dependencies, probing targets, launching browsers, invoking CDP/MCP, executing approvals, writing/activating skills, calling providers/connectors, enqueueing Agent Bus work, mutating Gate, or writing canonical state.
- Browser Use CLI preflight now has a bounded command at `chaseos operate browser browser-use-cli-preflight`; with `--from-env`, it reads `CHASEOS_BROWSER_USE_CLI` and checks executable discoverability plus throwaway-only config without invoking Browser Use CLI, launching a browser, reading profiles/credentials/cookies, or writing artifacts.
- Browser Use CLI external validation now has a bounded command at `chaseos operate browser browser-use-cli-external-validation`; the latest run executed only `browser-use --help`, wrote evidence, and did not run browser commands, launch a browser, read profiles/credentials/cookies, start tunnels, call providers/cloud APIs, activate skills, enqueue Agent Bus work, mutate Gate, or write canonical state.
- Browser Use CLI safe-URL validation design now has a bounded command at `chaseos operate browser browser-use-cli-safe-url-validation-design`; it selects the ChaseOS-owned localhost target `http://127.0.0.1:8770/`, allows only a future `open` command, and records Browser Use browser dependency download as not verified.
- Browser Use CLI safe-URL validation run now has a bounded command at `chaseos operate browser browser-use-cli-safe-url-validation-run`; the latest run opened `http://127.0.0.1:8770/`, closed the named Browser Use session, wrote evidence, and preserved no install, real profile, credentials/cookies, tunnel, cloud/provider call, Agent Bus write, Gate mutation, skill activation, or canonical writeback.
- Excalidraw target response intake now has a bounded command at `chaseos operate browser excalidraw-target-response`; with `--from-env`, it reads `CHASEOS_EXCALIDRAW_TARGET_URL` and can optionally write only the untrusted target response under `03_INPUTS/Browser-Target-Responses/_pending/` without probing the target or running browser/CDP/MCP actions.
- Excalidraw readiness from response now has a bounded command at `chaseos operate browser excalidraw-readiness-from-response`; it consumes only the untrusted target-response slot and can write bridge/live-readiness evidence, but currently blocks because no accepted loopback target response exists.
- Excalidraw MCP approval/proof shell contracts now have bounded commands at `chaseos operate browser excalidraw-mcp-execution-approval` and `chaseos operate browser excalidraw-mcp-proof-execution`; in the current repo state they return blocked JSON and perform no approval write, decision consumption, marker reservation, browser launch, CDP/MCP action, screenshot, skill write, provider/connector call, Agent Bus write, Gate mutation, or canonical writeback.
- Excalidraw public live browser proof now has complete-targeted evidence from `chaseos operate browser excalidraw-live-proof --settle-ms 6000 --json`; after explicit operator URL approval, it loaded `https://excalidraw.com`, detected `Excalidraw Whiteboard`, found the canvas, wrote screenshot evidence, and left the drawing/MCP proof not run.
- External runtime branch gating now has a bounded command at `chaseos studio external-runtime-branch-gate --branch <branch>`; Browser Use CLI validation now returns `can_start_branch=true` with `CHASEOS_BROWSER_USE_CLI` set to the external install, while Excalidraw target/readiness and Excalidraw live proof branches must not start until their exact branch gate returns `can_start_branch=true`.
- Excalidraw public reachability is proven, but drawing/MCP proof work remains separately approval-gated and must not be mixed into native shell implementation passes. Browser Use CLI no-account safe-URL validation is complete targeted.
- Phase 10C changed write methods from static blockers into governed `StudioService` write-surface methods. Real-vault static QA must not call `create_node`, `create_link`, approval submission, quarantine promotion, or metadata update methods; those belong in isolated temp-vault write-surface tests.

## Collision Map

Do not run parallel implementation chats against these shared surfaces without an explicit handoff:

- `runtime/studio/shell/*`
- `runtime/studio/desktop_shell_app.py`
- `runtime/cli/main.py`
- `runtime/cli/command_contract.json`
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md`
- `06_AGENTS/ChaseOS-Studio-Architecture.md`
- `06_AGENTS/Phase10-Desktop-Shell-Engineering-Plan.md`
- shared build-log, documentation-history, daily, and agent-activity indexes

Low-collision branches may run only when scoped to read-only inspection, isolated evidence, or external dependency readiness:

- Browser Use CLI external runtime validation with no real profile and no credentials.
- Excalidraw target discovery/readiness after a safe loopback target exists.
- Isolated completion-status inspection.
- Isolated documentation review that does not edit shared indexes.

## Confirm Before Spinning Off Another Chat

Before another chat starts co-development, confirm:

- exact pass name,
- files it may edit,
- files it must not edit,
- expected artifacts,
- whether the pass is implementation, QA, docs, or external readiness,
- whether it depends on native shell panel mounting.

## Current QA Entry Point

Use the bounded QA runner for Studio QA:

```powershell
chaseos studio qa-runner --surface native-shell --mode static --json
chaseos studio qa-runner --surface browser-runtime --mode static --json
chaseos studio qa-runner --surface workspace-entry --mode static --json
chaseos studio qa-runner --surface settings --mode static --json
chaseos studio qa-runner --surface approval-center --mode static --json
chaseos studio qa-runner --surface runtime-cockpit --mode static --json
chaseos studio qa-runner --surface runtime-intelligence --mode static --json
chaseos studio qa-runner --surface packaging --mode static --json
chaseos studio qa-runner --surface release-governance --mode static --json
chaseos studio qa-runner --surface installer-build-approval --mode static --json
chaseos studio qa-runner --surface installer-build-approval-review --mode static --json
chaseos studio qa-runner --surface installer-build-approval-consumption-dry-run --mode static --json
chaseos studio qa-runner --surface installer-build-approved-execution-proof --mode static --json
chaseos studio qa-runner --surface signing-approved-execution-proof --mode static --json
chaseos studio qa-runner --surface startup-autostart-approval-preview --mode static --json
chaseos studio qa-runner --surface startup-autostart-approval-review --mode static --json
chaseos studio qa-runner --surface startup-autostart-approved-execution-proof --mode static --json
chaseos studio qa-runner --surface release-promotion-approval-preview --mode static --json
chaseos studio qa-runner --surface release-promotion-approval-review --mode static --json
chaseos studio qa-runner --surface graph-view --mode legacy-browser --json
```

Static mode does not launch PyWebView. Legacy-browser mode starts an internally-owned ephemeral localhost server and shuts it down before returning. Future browser-visual QA can build on this evidence but must still record visual/browser limitations honestly.

Static mode must also prove no Studio approval artifact writes. The safety check is `no_approval_artifact_writes`; if it fails, stop Studio development and repair QA before adding more panels.

## Current Native Panel Registry

The native registry is read-only and records blocked authority for every declared panel. It does not introduce settings writes, approval decisions, provider/connector calls, workflow execution, graph persistence, node ID writes, node editing, Browser Use CLI execution, Excalidraw proof execution, or canonical mutation.

Latest registry QA evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-phase10a-native-shell-panel-registry-static-qa.md`

Latest provenance inspector QA evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-phase10b-studio-shell-provenance-inspector-tab-static-qa.md`

Latest Browser Runtime native panel QA evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-native-shell-panel-static-qa.md`
- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-panel-qa-runner-static-qa.md`
- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-panel-browser-qa.md`

Latest Workspace Entry native panel QA evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-open-folder-workspace-entry-static-qa.md`

Latest Settings native panel QA evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-settings-runtime-controls-static-qa.md`

Latest Approval Center native panel QA evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-approval-center-static-qa.md`

Latest Runtime Cockpit native panel QA evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-runtime-cockpit-expansion-static-qa.md`

Latest Runtime Intelligence native panel QA evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-runtime-intelligence-readonly-panels-static-qa.md`

Latest Real Desktop Packaging readiness QA evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-real-desktop-packaging-readiness-static-qa.md`

Latest Local Packaging Proof evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-local-packaging-proof.md`

Latest Packaged App Launch Smoke evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-packaged-app-launch-smoke.md`

Latest Packaged App Visual QA evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-packaged-app-visual-qa.md`
- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-packaged-app-visual-qa.png`

Latest Installer Plan and Governance evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-installer-plan-and-governance.md`
- `07_LOGS/Studio-Graph-Views/2026-05-04-studio-installer-plan-and-governance-static-qa.md`

Latest Release Readiness Governance evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-release-readiness-governance.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-release-governance-static-qa.md`

Latest Governed Installer Build Approval evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-governed-installer-build-approval.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-installer-build-approval-static-qa.md`

Latest Installer Build Approval Operator Review evidence:

- `07_LOGS/Agent-Activity/_studio_installer_build_approvals/studio-installer-build-appr-4efe404083dae669.json`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-installer-build-approval-operator-review.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-installer-build-approval-review-static-qa.md`

Latest Installer Build Approval Consumption Dry-Run evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-installer-build-approval-consumption-dry-run.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-installer-build-approval-consumption-dry-run-static-qa.md`

Latest Installer Build Approved Execution Proof evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-installer-build-approved-execution-proof.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-installer-build-approved-execution-proof-static-qa.md`
- `07_LOGS/Studio-Graph-Views/studio-installer-build-appr-4efe404083dae669-installer-build-dry-run.json`
- `07_LOGS/Studio-Graph-Views/studio-installer-build-appr-4efe404083dae669-installer-build-execution.json`
- `07_LOGS/Agent-Activity/_studio_installer_build_approvals/_execution_markers/studio-installer-build-appr-4efe404083dae669.json`
- `.pytest_tmp_env/studio-installer-proof/dist/ChaseOS-Studio-portable.zip`

Latest Signing Approval Preview evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-signing-approval-preview.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-signing-approval-preview-static-qa.md`
- `06_AGENTS/ChaseOS-Studio-Launch-Instructions.md`

Latest Signing Approval Operator Review evidence:

- `07_LOGS/Agent-Activity/_studio_signing_approvals/studio-signing-appr-c6d0561f9a8f921e.json`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-signing-approval-operator-review.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-signing-approval-review-static-qa.md`

Latest Signing Approval Consumption Dry Run evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-signing-approval-consumption-dry-run.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-signing-approval-consumption-dry-run-static-qa.md`

Latest Signing Approved Execution Proof evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-signing-approved-execution-proof.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-signing-approved-execution-proof-static-qa.md`
- `07_LOGS/Studio-Graph-Views/studio-signing-appr-c6d0561f9a8f921e-signing-dry-run.json`
- `07_LOGS/Studio-Graph-Views/studio-signing-appr-c6d0561f9a8f921e-signing-execution.json`
- `07_LOGS/Agent-Activity/_studio_signing_approvals/_execution_markers/studio-signing-appr-c6d0561f9a8f921e.json`
- `.pytest_tmp_env/studio-signing-proof/dist/ChaseOS-Studio-portable-signed.zip`

Latest Startup/Autostart Approval Preview evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-startup-autostart-approval-preview.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-startup-autostart-approval-preview-static-qa.md`

Latest Startup/Autostart Approval Operator Review evidence:

- `07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/studio-startup-autostart-appr-a90e121d6b079a51.json`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-startup-autostart-approval-operator-review.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-startup-autostart-approval-review-static-qa.md`

Latest Startup/Autostart Approval Consumption Dry Run evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-startup-autostart-approval-consumption-dry-run.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-startup-autostart-approval-consumption-dry-run-static-qa.md`

Latest Startup/Autostart Approved Execution Proof evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-startup-autostart-approved-execution-proof.md`
- `07_LOGS/Studio-Graph-Views/2026-05-06-studio-startup-autostart-approved-execution-proof-static-qa.md`
- `07_LOGS/Studio-Graph-Views/studio-startup-autostart-appr-a90e121d6b079a51-startup-autostart-dry-run.json`
- `07_LOGS/Studio-Graph-Views/studio-startup-autostart-appr-a90e121d6b079a51-startup-autostart-execution.json`
- `07_LOGS/Agent-Activity/_studio_startup_autostart_approvals/_execution_markers/studio-startup-autostart-appr-a90e121d6b079a51.json`
- `.pytest_tmp_env/studio-startup-autostart-proof/rollback/studio-startup-autostart-appr-a90e121d6b079a51-startup-autostart-rollback-plan.json`
- `.pytest_tmp_env/studio-startup-autostart-proof/audit/studio-startup-autostart-appr-a90e121d6b079a51-startup-autostart-host-mutation-audit.json`
- `.pytest_tmp_env/studio-startup-autostart-proof/shortcuts/ChaseOS-Studio-startup-shortcut-preview.json`

Latest Release Promotion Approval Preview evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-07-studio-release-promotion-approval-preview.md`
- `07_LOGS/Studio-Graph-Views/2026-05-07-studio-release-promotion-approval-preview-static-qa.md`

Latest Release Promotion Approval Review evidence:

- `07_LOGS/Agent-Activity/_studio_release_promotion_approvals/studio-release-promotion-appr-d698d13b011ccf06.json`
- `07_LOGS/Studio-Graph-Views/2026-05-07-studio-release-promotion-approval-operator-review.md`
- `07_LOGS/Studio-Graph-Views/2026-05-07-studio-release-promotion-approval-review-static-qa.md`

Current operator launch reference:

- Native product lane: `python -m chaseos studio shell`
- Localhost compatibility harness on an operator-selected port: `python -m chaseos studio desktop-shell-app --host 127.0.0.1 --port 8788`

Latest Browser Runtime Production Closeout evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-04-browser-runtime-production-closeout.md`

Latest External Runtime Readiness evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-readiness.md`

Latest External Runtime Setup Request evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-setup-request.md`

Latest Excalidraw MCP Approval / Proof CLI evidence:

- `07_LOGS/Build-Logs/2026-05-05-ChaseOS-excalidraw-mcp-approval-proof-cli-wiring.md`

Latest External Runtime Branch Gate evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-branch-gate-browser-use.md`
- `07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-branch-gate-excalidraw-target.md`
- `07_LOGS/Studio-Graph-Views/2026-05-05-studio-external-runtime-branch-gate-excalidraw-proof.md`
- `07_LOGS/Studio-Graph-Views/2026-05-05-browser-use-cli-external-install-branch-gate.md`

Latest Browser Use CLI external install evidence:

- `07_LOGS/Studio-Graph-Views/2026-05-05-browser-use-cli-external-install-readiness.md`
- `07_LOGS/Studio-Graph-Views/2026-05-05-browser-use-cli-external-install-branch-gate.md`

Latest Browser Use CLI external validation evidence:

- `07_LOGS/Browser-Runs/browser-use-cli-external-validation-20260505-help-probe.md`

Latest Browser Use CLI safe-URL validation design evidence:

- `07_LOGS/Browser-Runs/browser-use-cli-safe-url-validation-design-20260505.md`

Latest Browser Use CLI safe-URL validation run evidence:

- `07_LOGS/Browser-Runs/browser-use-cli-safe-url-validation-run-20260505.md`

Latest Excalidraw readiness from response CLI evidence:

- `06_AGENTS/Excalidraw-Readiness-From-Response-CLI.md`
- `07_LOGS/Browser-Runs/excalidraw_readiness_from_target_response_20260503_blocked_pending.json`

Latest Excalidraw public live browser proof evidence:

- `06_AGENTS/Excalidraw-Public-Live-Browser-Proof.md`
- `07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.json`
- `07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.png`
- `07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.md`

Next native-shell productization pass:

- None for Browser Runtime internal Studio panel work. The public Browser Runtime path now reports `browser-runtime-production-complete`; next Browser Runtime work exists only if the optional local loopback Excalidraw/MCP lane is resumed through `external-runtime-provide-excalidraw-target-url`.
- Phase 10 product hardening, release-readiness governance, governed installer-build approval preview, operator-review approval artifact writing, approval-consumption dry-run proof, approved installer-build execution proof, no-execution signing approval preview, signing approval operator review, signing approval consumption dry-run, signing approved execution proof, startup/autostart approval preview, startup/autostart approval operator review, startup/autostart approval consumption dry-run, startup/autostart approved execution proof, release-promotion approval preview, and release-promotion approval operator review are complete for the current native shell/package/evidence lane. The next release-governance pass is `studio-release-promotion-approval-consumption-dry-run`; product-surface pass sequencing may continue separately only with file-boundary coordination.
- Before any local-loopback external branch starts, run `chaseos studio external-runtime-branch-gate --branch <branch> --json` and require `can_start_branch=true`.

## Deferred Branches

- `studio-browser-runtime-shell-panel`: complete targeted as native read-only panel mount.
- `studio-browser-runtime-shell-panel-qa-runner`: complete targeted as `browser-runtime/static` bounded QA evidence.
- `studio-browser-runtime-panel-browser-qa`: complete targeted as legacy-harness browser support evidence; direct native PyWebView screenshot QA remains unavailable in normal browser.
- `browser-use-cli-external-runtime-validation`: complete targeted as a help-surface validation; no browser command ran.
- `browser-use-cli-no-account-safe-url-validation-design`: complete targeted; no browser command ran.
- `browser-use-cli-no-account-safe-url-validation-run`: complete targeted; Browser Use opened the loopback Studio Product UI target and closed the named session with no forbidden authority expansion.
- `excalidraw-target-response-live-readiness`: local target readiness only; still blocked until a loopback target response exists if that lane is resumed.
- `excalidraw-public-live-browser-proof`: complete targeted; public reachability, title, canvas, and screenshot evidence are present.
- `excalidraw-public-browser-drawing-proof-run`: complete targeted; approval consumed, marker completed, one rectangle plus `ChaseOS proof` drawn, screenshot/JSON/Agent Activity evidence written.
- `excalidraw-live-browser-mcp-proof`: local loopback MCP lane only if a safe loopback target/readiness chain is later supplied and approved.
- `browser-runtime-production-closeout`: complete; internal Studio lane closed and public Browser Runtime blockers cleared.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
