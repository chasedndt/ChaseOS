---
title: ChaseOS Studio Full Desktop/Card UI Closure Criteria
date: 2026-05-12
runtime: Hermes-Optimus
status: ACTIVE / ACCEPTANCE CRITERIA / NOT CLOSED
phase: Phase 10 - ChaseOS Studio
---

# ChaseOS Studio Full Desktop/Card UI Closure Criteria

This artifact closes the ambiguous ROADMAP item wording around "Full Studio desktop/card UI" by defining what must be true before that box can be checked. It does **not** mark the item complete. Current installer-lane Pass 10B packaged native visual-QA truth uses the verified complete audit selected by installer governance; later WebView2 remediation diagnostics remain historical unless that lane is explicitly resumed.

Canonical tracker: [[ChaseOS-Studio-Phase10-Implementation-Tracker]]
Related current-state evidence: [[Now]]

---

## Current repo truth snapshot

As of 2026-05-12:

- Native product lane is `chaseos studio shell`, not the legacy localhost harness.
- Legacy compatibility/QA lane remains `chaseos studio desktop-shell-app`.
- `runtime/studio/shell/panel_registry.py` declares 32 mounted panels in the current live registry.
- 4 panels are approval-gated rather than direct-write surfaces: Graph, Node Inspector, Chat, and Runtime Cockpit.
- `runtime/studio/product_hardening_status.py` and `runtime/studio/installer_plan.py` report green product/installer readiness against the current complete Pass 10B audit chain.
- `07_LOGS/Studio-Graph-Views/pass10b-completion-audits/2026-05-11-studio-pass10b-final-current-completion-audit.json` is the current installer-lane Pass 10B audit and reports `COMPLETE / VERIFIED`.
- `07_LOGS/Studio-Graph-Views/webview2-operator-remediation-packets/2026-05-12-pass10b-webview2-operator-remediation-packet.json` remains useful historical diagnostic infrastructure, but no WebView2 remediation rerun is part of the current installer-build proof lane.
- Current installer-build approval artifact `studio-installer-build-appr-ac14811da651baec` is written, dry-run validated, and readiness-verified, but it has not been consumed by `--execute`.

2026-05-21 addendum:

- `runtime/studio/shell/panel_registry.py` currently reports 39 declared panels, of which 38 are mounted and 1 is readiness-only. Treat the 32-panel count above as historical May 12 truth only.
- Studio product UI finalization is now tracked in `06_AGENTS/Finalize-ChaseOS-Studio-Product-UI-Handover.md`; feature-family normalization must happen before navbar or Dashboard/Home implementation is claimed complete.
- Studio feature-family normalization is now documented in `06_AGENTS/Studio-Product-UI-Feature-Family-Normalization.md`; the navbar and Dashboard/Home remain unimplemented until the operator confirms the 39-panel mapping.

---

## Definition of "full desktop/card UI"

The ROADMAP item may be treated as closed only when **all** of the following are true.

### 1. Native desktop shell proof

Acceptance criteria:

- `chaseos studio shell` is the primary visible app lane.
- Packaged native Studio opens visibly on the target host.
- A fresh packaged visual-QA run captures a nonblank native screenshot after any required WebView2 remediation.
- The installer-lane selected Pass 10B completion audit is green, and any newer diagnostic reports are clearly marked as historical or lane-specific rather than installer-blocking.
- Evidence distinguishes source-shell, packaged-shell, localhost-harness, and historical screenshots.

Current status: **current installer-lane Pass 10B visual proof is verified; desktop/card closure remains open for target-effect execution, installer execution, and governed follow-through.**

### 2. Card UI inventory and navigation completeness

Acceptance criteria:

- The native shell registry exposes the complete Studio card/panel inventory expected for MVP closure.
- Every mounted panel has a visible card/route/sidebar entry or a documented reason for being background-only.
- Every card reports source contract, status, authority boundary, and available actions.
- Card states distinguish read-only, approval-gated, blocked, degraded, and future-only posture.
- The acceptance evidence includes a machine-readable inventory generated from the live registry, not a prose-only claim.

Current status: **implemented enough for proof packet generation, but product-family/nav cleanup remains open**. Live registry now reports 39 declared panels, 38 mounted panels, and 1 readiness-only panel; the proof packet must stay machine-readable and no-execution.

### 3. Approval-gated card actions

Acceptance criteria:

- Graph create/edit and visual-link cards queue approval artifacts only and never direct-write graph/canonical state.
- Node Inspector metadata edits are approval-gated with exact scope and restricted-field blocking.
- Chat proposal/companion queue-write cards prove digest/scope validation, exact-once behavior, and duplicate blocking before any target-effect execution is claimed.
- Runtime Cockpit action cards queue request artifacts only until governed execution lanes are explicitly approved and verified.
- Approval Center itself remains read-only until a separate approval decision/execution lane is active.

Current status: **partial**. Many approval-gated card surfaces exist, but companion selection/Chat target-effect execution, approval consumption, and runtime actions are not closed as full target-effect execution paths.

### 4. Real execution cards versus preview cards

Acceptance criteria:

- Provider/model call cards distinguish readiness/approval preview from real provider execution.
- Runtime dispatch cards distinguish readiness/proof packet from real runtime dispatch.
- Browser dispatch cards distinguish readiness/proof packet from real browser launch/navigation/screenshot control.
- Schedule/Pulse cards distinguish local queue/audit/proof writes from daemon start, workflow execution, provider calls, and runtime dispatch.
- No card uses a green visual status for execution that is still preview-only or proof-only.

Current status: **partial / intentionally blocked**. Current runtime/provider/browser execution surfaces are read-only, approval-preview, or proof-only.

### 5. Target workspace/import/setup card completion

Acceptance criteria:

- Open Folder, Obsidian detection, general Markdown inference, bootstrap wizard, upgrade approval packet, and approved upgrade proof are surfaced as cards.
- The UI clearly distinguishes proof-temp upgrade execution from real operator-selected target workspace upgrade/migration.
- Real target folder/file migration is either executed with rollback/audit/exact-once evidence or explicitly deferred outside MVP closure.

Current status: **partial**. Pass 10F5/10F6 proof-temp chain exists; real target workspace migration remains deferred.

### 6. Release/install/host card boundaries

Acceptance criteria:

- Installer/signing/startup/release cards distinguish historical proof artifacts from current release authority.
- Real installer install, production signing, startup/autostart, registry/shortcut, and release-promotion host mutations are not implied by proof-temp or historical workspace evidence.
- If closure claims release-ready desktop UX, installer/release/host mutation proof must be current and governed.

Current status: **blocked/deferred**. Current installer-build approval artifact is written, dry-run validated, and readiness-verified, but not consumed by approved execution; signing/startup/release/host follow-through remains deferred.

---

## Minimum closure evidence packet

Before the ROADMAP checkbox can be marked `[x]`, create one evidence packet that includes:

1. latest Pass 10B audit path and status,
2. packaged visual-QA JSON and screenshot path,
3. shell panel/card inventory JSON generated from the live registry,
4. list of approval-gated cards with possible writes and exact blocked authority,
5. list of preview-only/proof-only cards that remain intentionally non-executing,
6. explicit claim decision: `full_desktop_card_ui_closed=true|false`,
7. no-new-authority checklist: no provider/connector call, no Agent Bus task write, no Gate/workflow/Git/host/release/canonical mutation unless separately approved and evidenced.

Recommended implementation card: `studio-full-desktop-card-ui-inventory-proof`.

---

## Current split of remaining work

This ambiguous ROADMAP item should be split into concrete shippable cards:

1. **Pass 10B installer-lane audit reconciliation**
   - Owner surface: Studio implementation/QA.
   - Required output: inventory/closure evidence consumes the same current complete Pass 10B audit selected by installer governance, while WebView2 remediation reports remain historical diagnostic context unless that lane is resumed.

2. **Full desktop/card UI inventory proof**
   - Owner surface: Studio implementation/QA.
   - Required output: machine-readable inventory packet over live registry + acceptance criteria above.

3. **Approval target-effect execution closure**
   - Owner surface: Studio/Phase 11 governed action lanes.
   - Required output: exact-once target-effect proofs for selected Chat/Studio/runtime actions, or explicit MVP deferral.

4. **Runtime/provider/browser execution proof or explicit MVP deferral**
   - Owner surface: Phase 9-and-below governed execution lanes.
   - Required output: bounded live execution proof, or an explicit product decision that preview/proof-only cards are acceptable for MVP.

5. **Real target workspace migration proof or explicit MVP deferral**
   - Owner surface: import/setup lane.
   - Required output: operator-selected target folder proof with rollback/audit/exact-once evidence, or explicit product deferral.

6. **Release/install/host mutation proof or explicit MVP deferral**
   - Owner surface: release governance / host-operation lane.
   - Required output: governed installer/signing/startup/release proof, or explicit product deferral.

---

## Authority boundary

This criteria artifact is a product/spec surface only. It grants no host mutation, WebView2 repair/install, packaged app launch, screenshot capture, approval consumption, provider/model call, runtime dispatch, browser control, Agent Bus task write, Gate mutation, workflow mutation, Git mutation, release mutation, or canonical writeback authority.

The operating-system alignment is: ChaseOS Studio can expose rich desktop/card UI surfaces, but closure belongs to the ChaseOS control plane only when the underlying AOR/Gate/runtime evidence is current, bounded, and auditable.

---

*Graph links: [[ChaseOS-Studio-Phase10-Implementation-Tracker]] · [[ChaseOS-Phase11-Architecture]] · [[ChaseOS-Approval-Center]] · [[HERMES]] · [[Agent-Activity-Index]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
