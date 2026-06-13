---
type: handover
title: Phase 10A0 UI Runtime Handover
status: PRODUCTION INTAKE IMPLEMENTED TARGETED / MANUAL REAL-FILE RETEST PENDING / APP LAUNCHER STILL OPEN
created: 2026-04-29
updated: 2026-05-07
phase: Phase 10A0
runtime: Codex
session_descriptor: phase10a0-ui-runtime-handover
handoff_for: Studio UI runtime / next Phase 10A implementation harness
knowledge_class: system-operational
related_handover: Phase10A0-Live-Proof-Test-Handover.md
---

# Phase 10A0 UI Runtime Handover

## 2026-05-07 Operator Correction - Cockpit Cleanup And Coverage Rule

The operator staged a real local file through the current localhost cockpit and reported the following product problems:

- the page is visually and structurally messy
- the `strikezone` profile reads like product branding instead of a pilot
- the app scrolls back to the top after staging
- the UI says `Required inputs 1 / 3`
- the UI implies one source is required from each pilot source/platform
- the file picker accepts only text-readable suffixes, while real operator exports include PDF and spreadsheet/document formats
- the next action after staging is not obvious enough
- there is no launcher/navigation surface for moving between Studio pages

Superseding rule: Phase 10A0 must support flexible source coverage. One real operator source must be enough to stage, import, preview, and write a bounded runtime-local preview pack. Extra source roles improve confidence/coverage; they are not a hard gate unless a downstream workflow explicitly declares a source dependency.

Operator screenshot evidence is summarized in `06_AGENTS/Phase10A0-Acquisition-Cockpit-Cleanup-Plan.md`. The screenshot is attached in the Codex thread; this pass records the screenshot content in repo markdown but does not persist a local PNG artifact.

Next implementation focus:

1. reliable Studio app launcher / port-health identity
2. from-zero manual proof with real files through drag/drop, import, preview-write, reviewed promotion, and SBP verification
3. broader acquisition cockpit stepper/navigation cleanup


## Current Pivot Note — ChaseOS Pulse

As of 2026-04-29, the active user-supplied implementation context may be **ChaseOS Pulse** rather than the StrikeZone Acquisition Intake Cockpit. If the active task is Pulse, use `06_AGENTS/ChaseOS-Pulse-UI-and-Runtime-Handoff.md` and the Pulse scaffold under `runtime/pulse/` as the primary handoff.

The Acquisition Intake Cockpit remains a valid Phase 10A0 foothold, but it should not override the current Pulse implementation lane unless the operator explicitly switches back to acquisition UI work.

## 2026-05-06 Research Repository Template Bootstrap

Fresh user machines no longer need pre-existing `perplexity_digest`, `youtube_summary`, `research_export`, or `grok_digest` folders before Phase 10A0 can start. The bounded bootstrap command now inspects or creates the reusable StrikeZone local research repository template:

```text
chaseos acquisition init-research-repository --profile strikezone --json
chaseos acquisition init-research-repository --profile strikezone --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --action init-repository --confirm-action --json
```

The default command is dry-run. The confirmed command creates only folder layout, `_inbox` folders, README/example files, `.gitkeep` placeholders, and source templates under `runtime/acquisition/manual/strikezone/`. It does not create real research source files, preview packs, latest pointers, provider/browser calls, MCP scope, delivery, schedules, or canonical notes.

This closes the production bootstrap gap for local research repository creation. It does not close the remaining live-proof requirement: real local research files still need to be staged, imported, previewed, reviewed, promoted, and SBP-verified before the workflow can be claimed live verified.

## 2026-05-06 Real Local Research File Proof Attempt

The next live-proof pass was attempted against the declared StrikeZone local intake folders and inboxes. The repository template is ready and the local cockpit reports `development_ready_for_manual_real_file_test=true`, but manual input is not ready:

- `source_count=0`
- `inbox_candidate_count=0`
- missing recommended source classes: `perplexity_digest`, `youtube_summary`, `research_export`
- `preview-research` is blocked because no research import files exist under the declared drop folders
- `verify-research-sbp` is blocked because the current latest pointer is not a reviewed `strikezone-research-import-preview` pointer

Result: BLOCKED / NOT VERIFIED for the real local research-file workflow. No preview pack, reviewed latest pointer, SBP proof, browser/provider/MCP/delivery/scheduler authority, or canonical note write was produced by this proof attempt.

## 2026-05-07 Major Local File-Picker / Drop Workflow Update

Status: COMPLETE TARGETED for the local file-picker/drop staging workflow; real-file workflow proof remains BLOCKED / NOT VERIFIED.

The localhost Studio Acquisition Cockpit now exposes a first-class staging contract:

```text
GET /staging.json
surface: studio_acquisition_file_drop_workflow
input_mode: operator_selected_local_file_picker_or_drag_drop
```

The dry-run app plan and `/health.json` now include the same `file_drop_workflow` payload and route map. The HTML surface now includes a `Local file-picker / drop workflow` panel plus per-source `Pick or drop local file` controls. Confirmed uploads still write only to:

```text
runtime/acquisition/manual/strikezone/_inbox/<source_class>/
```

Upload audit events now include destination path and size. This is local operator-selected file staging only. It is not full OS-wide file explorer/system control, does not browse, does not call providers, does not expand MCP/delivery/scheduler authority, and does not mutate canonical notes.

Current-code localhost proof was run on:

```text
http://127.0.0.1:8768/
http://127.0.0.1:8768/staging.json
```

The proof showed `source_class_count=4`, `required_ready_count=0`, `staged_inbox_candidate_count=0`, and `manual_real_file_test_verified=false`, which is correct because no real operator research files are present yet. A stale pre-patch app was observed on `127.0.0.1:8767`; do not use that process for current-code staging proof.

## 2026-05-07 Production Intake Workflow Update

Status: IMPLEMENTED TARGETED / MANUAL REAL-FILE RETEST PENDING.

The intake cockpit now has the production-shaped intake path that was missing from the first manual proof:

- `runtime/acquisition/intake_normalization.py` normalizes operator-selected sources into ChaseOS Markdown artifacts while preserving raw provenance.
- Confirmed `import-file` and `import-inbox` now write raw provenance, standardized Markdown, dashboard ledger, daily note, and daily index artifacts.
- Supported suffixes now include `.pdf`, `.docx`, `.xlsx`, `.csv`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.bmp`, `.tif`, `.tiff`, plus readable text formats.
- The model/app contracts use `required_source_classes=[]`; missing Perplexity/YouTube/research-export roles are warnings, not gates.
- The localhost app includes static drag/drop handling, accepted-format copy, proof-chain cards, and visible `Clear current intake` controls at the top and inside `Local file-picker / drop workflow`.
- The proof chain is explicit: standardized artifact creation -> preview pack write -> reviewed promotion -> SBP verification.

Current-code localhost proof was run on:

```text
http://127.0.0.1:8775/
http://127.0.0.1:8775/health.json
http://127.0.0.1:8775/staging.json
```

The smoke confirmed the new accepted suffixes, `required_source_classes=[]`, drag/drop HTML/script markers, proof-chain copy, and multiple clear controls. The manual proof remains open because the operator still needs to repeat the whole workflow with real files from zero.

## 2026-05-07 Real Local File Rehearsal Attempt

Status: BLOCKED / NOT VERIFIED.

The requested real-file rehearsal was attempted against the current-code localhost app and declared StrikeZone folders. The app and repository template are ready, but no actual operator research files are staged/imported:

```text
http://127.0.0.1:8768/staging.json
required_ready_count=0
staged_inbox_candidate_count=0
imported_source_file_count=0
next_action=stage-upload
manual_real_file_test_verified=false
```

`research-status` still reports `source_count=0` and `inbox_candidate_count=0`. `preview-research` and `verify-research-sbp` both fail closed for the expected reasons. This pass did not import files, write a preview pack, promote a latest pointer, or complete SBP verification.

## 2026-04-30 Static Local Cockpit Surface Update

The Acquisition Intake Cockpit now has a richer static local HTML surface through `render_acquisition_cockpit_html()` and the existing explicit `--output-html` CLI flag. The generated page shows readiness metrics, source-class cards, import commands, governed controls, current pointer state, next actions, warnings, and authority boundaries. It remains a static local artifact only: no server, browser automation, MCP/provider calls, delivery, cron/scheduler authority, second datastore, or canonical writeback was added.

Live smoke artifact generated in the implementation pass:

```text
runtime/studio/out/acquisition-cockpit.html
```

Full Studio desktop/product shell remains unbuilt.

## Purpose

This is the handover packet for the runtime that starts the Phase 10A UI work.

The companion live-proof handover, `06_AGENTS/Phase10A0-Live-Proof-Test-Handover.md`, explains why Phase 10A0 exists and what live proofs are still needed. This document tells the UI implementation runtime what already exists, what to wrap first, what boundaries must not move, and what the first usable interface should do.

## Current Repo Truth

- Phase 10A0 is the first narrow Studio/product-shell foothold, not the full ChaseOS Studio product.
- Full Studio desktop is not built yet.
- A local-only Phase 10A0 backend/model foothold already exists under `runtime/studio/`.
- The first visible surface should be the Studio Acquisition Intake Cockpit for StrikeZone local/import research proof.
- ChaseOS remains the source of truth and control plane. Studio is an operator surface over ChaseOS state, not a second authority system.
- Phase 9 remains active for selected proof/hardening. Do not claim global Phase 9 closeout from this UI pass.

## Existing Implementation To Reuse

| Surface | Status | Path / command | Notes |
|---|---|---|---|
| Live-proof handover | COMPLETE | `06_AGENTS/Phase10A0-Live-Proof-Test-Handover.md` | Defines proof matrix, source-file requirements, boundaries, and next prompt |
| Acquisition cockpit model/static surface | IMPLEMENTED FOOTHOLD / STATIC SURFACE VERIFIED | `runtime/studio/acquisition_cockpit.py`; `runtime/studio/out/acquisition-cockpit.html` | Builds UI-ready model, copies explicit operator-selected research files, renders a static local cockpit with readiness, source-class, control, pointer, next-action, warning, and authority-boundary sections |
| Acquisition cockpit action wrappers | IMPLEMENTED FOOTHOLD | `run_acquisition_cockpit_action()` / `chaseos studio acquisition-cockpit --action ...` | Wraps import-file, preview-read-only, preview-write, promote-reviewed-preview, and verify-research-sbp; write actions require `--confirm-action` |
| Acquisition cockpit tests | IMPLEMENTED | `runtime/studio/test_phase10a0_acquisition_cockpit.py` | Covers empty state, safe import, unsafe suffix rejection, action wrappers, confirmation failure, HTML render, CLI JSON, explicit HTML write |
| CLI surface | IMPLEMENTED FOOTHOLD | `chaseos studio acquisition-cockpit --profile strikezone --json` | Read-only by default; optional explicit static HTML output; governed action mode available through `--action` |
| Command contract | IMPLEMENTED | `runtime/cli/command_contract.json` | Lists `studio acquisition-cockpit` as alpha Phase 10 command family |
| Studio architecture | DOCS | `06_AGENTS/ChaseOS-Studio-Architecture.md` | Desktop-first product shell; service layer required before broad UI expansion |

## First UI Target

Build a local-only operator cockpit around the existing acquisition cockpit model.

The first usable screen should show:

- Product title: `Research Intake Cockpit`
- Profile label: `StrikeZone Market Digest Pilot`
- Source-class cards for `perplexity_digest`, `youtube_summary`, `research_export`, and optional `grok_digest` as coverage roles, not hard platform quotas
- Folder path and file count per source class
- Present/empty status per source class, with warnings rather than default blockers
- Accepted file suffixes
- Explicit import/drop control that writes only into the declared source-class inbox/folder
- Read-only preview control
- Explicit preview-write control
- Explicit reviewed-promotion control
- Read-only SBP verification control
- Authority boundary banner: no browser, MCP, delivery, provider call, cron, or canonical mutation authority
- Warnings and next actions from the existing model/status payload

This is an operational cockpit, not a landing page. Keep it dense, clear, and action-oriented.

## Backend Contract

The UI should consume the existing model shape before inventing new state.

Primary Python functions:

```text
runtime.studio.acquisition_cockpit.build_acquisition_cockpit_model(vault_root, profile="strikezone")
runtime.studio.acquisition_cockpit.import_research_file(vault_root, source_class=..., source_path=..., profile="strikezone")
runtime.studio.acquisition_cockpit.render_acquisition_cockpit_html(model)
```

Primary CLI:

```text
chaseos acquisition init-research-repository --profile strikezone --json
chaseos acquisition init-research-repository --profile strikezone --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --json
chaseos studio acquisition-cockpit --profile strikezone --output-html runtime/studio/out/acquisition-cockpit.html --json
chaseos studio acquisition-cockpit --profile strikezone --action init-repository --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --action import-file --source-class perplexity_digest --source-file <operator-selected-file> --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --action preview-read-only --json
chaseos studio acquisition-cockpit --profile strikezone --action preview-write --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --action promote-reviewed-preview --briefing-input <preview-briefing-ready-input-set> --reviewed --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --action verify-research-sbp --json
```

Existing governed commands the UI should make visible:

```text
chaseos acquisition init-research-repository --profile strikezone --json
chaseos acquisition init-research-repository --profile strikezone --confirm-action --json
chaseos acquisition research-status --profile strikezone --json
chaseos acquisition preview-research --profile strikezone --json
chaseos acquisition preview-research --profile strikezone --write --json
chaseos acquisition promote-research-preview --profile strikezone --briefing-input <path> --reviewed --json
chaseos acquisition verify-research-sbp --profile strikezone --json
```

If installed `chaseos` is stale on the host, use `python -m runtime.cli.main ...` while preserving the canonical command labels in the UI.

## Non-Negotiable Boundaries

The Phase 10A0 UI must not:

- Create a second datastore.
- Become canonical truth.
- Mutate `00_HOME/`, `01_PROJECTS/`, `02_KNOWLEDGE/`, or protected docs.
- Hide file writes behind background UI behavior.
- Promote a preview without explicit reviewed confirmation.
- Add browser authority.
- Add MCP authority.
- Add external delivery authority.
- Add live provider calls.
- Add cron/scheduler authority.
- Read or display secrets.
- Treat runtime memory, identity ledgers, scorecards, or agent bus state as permission authority.

Every write action must be visible, explicit, auditable, and mapped to an existing ChaseOS governed surface.

## Suggested Phase 10A0 Build Order

1. Keep `runtime/studio/acquisition_cockpit.py` as the first service/model boundary.
2. Add a local UI shell around that model. Choose the desktop stack intentionally; the repo currently has no `package.json`.
3. Build only one route/view first: `Acquisition Intake`.
4. Render the existing model payload into stable sections: readiness summary, source-class cards, governed controls, authority boundaries, and next actions.
5. Add explicit local research repository template initialization for fresh user machines. COMPLETE as dry-run/confirmed CLI and Studio action wrapper.
6. Add explicit import/drop handling that calls the existing safe import path and shows the exact destination. COMPLETE TARGETED as service/CLI action wrapper plus localhost file-picker/drop staging controls and `/staging.json`; full OS-wide file explorer/system control remains unbuilt.
7. Add command execution wrappers for preview, preview-write, reviewed promotion, and SBP verification. COMPLETE as service/CLI action wrapper; desktop button execution remains unbuilt.
8. Remove the hard three-source/one-per-platform gate. COMPLETE TARGETED: pilot source roles are confidence coverage, not the minimum intake requirement.
9. Add document-normalized intake for PDF/DOCX/XLSX/CSV/images. COMPLETE TARGETED: preserve originals as provenance, write standardized Markdown artifacts, dashboard ledger records, and daily operating-layer links.
10. Log all UI write attempts through existing ChaseOS logging discipline before broadening UI scope.
11. Only after this view is stable, add shared runtime-state service seams for Settings, Approval Center, Runtime Cockpit, Provenance Explorer, Memory/Identity, Graph/Node, companion, and reconnect/history panels.

## UI Design Guidance

- Build a work surface, not a marketing page.
- Use compact panels, clear status markers, and predictable controls.
- Show disabled controls with concrete reasons from the model.
- Use explicit confirmation modals for write actions.
- Keep repeated source classes as cards or rows; avoid nested card layouts.
- No hero page, decorative gradient background, or broad explanatory copy.
- Make file paths copyable/inspectable but not visually dominant.
- Keep authority boundaries visible at the point of action.

## Future Panels To Plan For

The first shell should not hard-code itself into only acquisition. Leave room for:

| Panel | Reads from | First boundary |
|---|---|---|
| Settings / Provider / Config | `config validate`, `config summary`, `runtime provider-status` | No secret display, no implicit provider switching |
| Approval Center | OSRIL approvals, `wait-resume`, `resume-ready --dry-run`; canonical cross-feature doc: [[ChaseOS-Approval-Center]] | Approval decision and resume action stay separate |
| Runtime Cockpit | Agent Bus status/tasks/heartbeats, lifecycle, coordination-watch proof | Read-only by default; mutations need scoped confirmation |
| Provenance Explorer | provenance records, trace outputs, sidecars, audit logs | Read-only lineage navigation |
| Memory / Agent Identity Ledger | memory summary/show/ledger, profiles, scorecards | Advisory only; not permission authority |
| Graph / Node UI | graph substrate, vault markdown/frontmatter | Derived/rebuildable index; service layer owns writes |
| Voice / Visual / Companion | future OSRIL/ingress adapters | Tier-4 input handling; no ambient command trust |
| Reconnect / History | OSRIL events, Agent Bus tasks, audit trails | No second unmanaged session memory store |

## Test Ladder For UI Runtime

Run the existing backend tests before adding a UI layer:

```text
python -m pytest runtime/studio/test_phase10a0_acquisition_cockpit.py -q
python -m pytest runtime/studio/test_phase10a0_acquisition_cockpit_app.py -q
python -m runtime.cli.main studio acquisition-cockpit --profile strikezone --json
python -m runtime.cli.generate_docs --check
```

When a real UI shell exists, add:

- Render smoke for the empty state.
- Import/drop test with synthetic `.md`/`.txt` research files.
- Disabled-control test when no files exist.
- Explicit write confirmation test for preview-write.
- Reviewed-promotion confirmation test.
- SBP verification read-only test.
- Screenshot/visual QA at desktop and narrow widths.
- Test proving no browser/MCP/provider/delivery/cron authority was added.

## 2026-04-30 Local Visual Wrapper Update

Status: COMPLETE / VERIFIED TARGETED for the first localhost wrapper.

Implemented:

- `runtime/studio/acquisition_cockpit_app.py`
- `runtime/studio/test_phase10a0_acquisition_cockpit_app.py`
- `chaseos studio acquisition-cockpit-app --profile strikezone --dry-run --json`
- `chaseos studio acquisition-cockpit-app --profile strikezone --host 127.0.0.1 --port 8765`

The wrapper is a stdlib Python `ThreadingHTTPServer` bound to loopback only. It renders the existing Studio Acquisition Intake Cockpit model, exposes `/model.json` and `/health.json`, and posts operator actions back through the existing governed cockpit action wrapper. It does not create a second workflow path.

Live smoke on 2026-04-30 started the local wrapper at `http://127.0.0.1:8765/`; `GET /`, `/model.json`, and `/health.json` returned HTTP 200. `netstat` reported listener PID `31812`.

Preserved boundaries:

- No browser automation authority.
- No MCP/provider calls.
- No delivery authority.
- No scheduler/cron authority.
- No canonical writeback authority.
- No `02_KNOWLEDGE/` mutation.
- No second datastore.

Remaining UI gaps:

- Desktop file picker and drag/drop are still unbuilt.
- Browser screenshot/visual QA is still pending.
- Real operator research-file import, preview-write, reviewed promotion, and SBP proof still require real local research files.

## 2026-04-30 Visual QA Update

Status: COMPLETE / VERIFIED TARGETED for browser visual QA.

Verified in the Codex in-app browser at `http://127.0.0.1:8765/`:

- Page title: `Studio Acquisition Cockpit`.
- Top viewport renders readiness metrics and authority boundary.
- Scrolled viewport renders source-class cards for `perplexity_digest`, `youtube_summary`, `research_export`, and `grok_digest`.
- Scrolled viewport renders governed controls for read-only preview, preview write, reviewed pointer promotion, and SBP verification.
- Bottom viewport renders next actions.
- `/model.json` and `/health.json` returned valid JSON.
- Console error count: `0`.
- Script tag count: `0`.

Screenshot artifacts:

- `runtime/studio/out/acquisition-cockpit-visual-qa-top.png`
- `runtime/studio/out/acquisition-cockpit-visual-qa-sources.png`
- `runtime/studio/out/acquisition-cockpit-visual-qa-bottom.png`

Real-file proof status: BLOCKED by missing operator research files. `acquisition research-status --profile strikezone --json` reported `source_count: 0`, and read-only `acquisition preview-research --profile strikezone --json` failed with no research import files under the declared source-class folders.

## 2026-04-30 Research Inbox Automation Update

Status: COMPLETE / VERIFIED TARGETED for local staged-file automation.

The Acquisition Intake Cockpit now has a local source-class inbox model in front of the declared import folders:

```text
runtime/acquisition/manual/strikezone/_inbox/perplexity_digest/
runtime/acquisition/manual/strikezone/_inbox/youtube_summary/
runtime/acquisition/manual/strikezone/_inbox/research_export/
runtime/acquisition/manual/strikezone/_inbox/grok_digest/
```

The canonical command is:

```text
chaseos acquisition import-research-inbox --profile strikezone --json
chaseos acquisition import-research-inbox --profile strikezone --confirm-action --json
```

The first command is a dry run. The confirmed command copies supported files into the declared source-class folders, records SHA-256 import fingerprints in `runtime/acquisition/state/strikezone-research-inbox-imports.jsonl`, and does not delete staged inbox files.

The localhost cockpit now renders each inbox path and an `Import staged inbox files` control. This remains local-only: no browser automation, MCP/provider calls, delivery authority, scheduler/cron authority, canonical writeback, or `02_KNOWLEDGE/` mutation was added.

## 2026-04-30 Inbox Readiness Inspector Update

Status: COMPLETE / VERIFIED TARGETED for staged-file readiness visibility.

The research inbox scan now reports metadata/readiness details before files are
copied into declared source-class folders. `research-status`,
`import-research-inbox`, `build_acquisition_cockpit_model()`,
`render_acquisition_cockpit_html()`, and the localhost cockpit wrapper surface:

- staged candidate counts by source class
- per-file display name, metadata keys, declared URL, source event time, and capture time
- readiness labels: `metadata_ready`, `metadata_thin`, `metadata_error`, `empty_content`
- warning counts and missing recommended metadata
- source-class card inbox counts in the local cockpit

This is advisory/read-only until the existing explicit import action is
confirmed. Missing metadata does not create a new gate, does not call providers,
does not browse, does not mutate canonical notes, and does not bypass the Phase
9 acquisition/SBP preview and reviewed-promotion path.

## 2026-04-30 Inbox Upload Foothold Update

Status: COMPLETE / VERIFIED TARGETED for local browser staging.

The localhost cockpit now exposes a confirmed `stage-upload` action on each
source-class card. The action receives an operator-selected browser file and
writes it only to:

```text
runtime/acquisition/manual/strikezone/_inbox/<source_class>/
```

This reduces manual folder-copy friction while preserving the existing
acquisition gates. A staged upload does not import into the declared source
folder, build a preview pack, promote a pointer, call providers, browse, deliver,
schedule, or mutate canonical notes. The next step remains the existing
dry-run-first `import-research-inbox` path.

## 2026-04-30 Preview Promotion Prefill Update

Status: COMPLETE / VERIFIED TARGETED for preview-pack visibility and reviewed
promotion handoff.

`research-status`, the static cockpit model, and the localhost cockpit now
discover existing `runtime/acquisition/packs/*-strikezone-research-import-preview/`
preview packs and expose:

- `preview_candidates`
- `preview_candidate_count`
- `latest_preview_candidate`
- the latest valid preview `briefing_ready_input_set.json` path

The reviewed-promotion control now enables only when a valid preview candidate
or already reviewed preview pointer exists, and the localhost form pre-fills the
BRIS path after `preview-write`. This removes another manual path-copy step
without bypassing review: the operator must still inspect the preview pack,
check `Reviewed`, and confirm the latest-pointer write.

Preserved boundaries:

- no browser automation
- no MCP/provider calls
- no delivery authority
- no scheduler/cron authority
- no canonical note mutation
- no automatic reviewed-promotion or SBP run

## 2026-04-30 Workflow Rehearsal Ladder Update

Status: COMPLETE / VERIFIED TARGETED for read-only workflow-stage guidance.

The acquisition cockpit model, static HTML surface, and localhost cockpit now
include a `rehearsal` model with the surface id
`strikezone_research_rehearsal_ladder`. It derives the current operator stage
from existing acquisition status only:

1. Stage research files.
2. Import staged inbox files.
3. Write preview pack.
4. Review and promote preview.
5. Verify SBP consumption.

Each step reports `complete`, `current`, `pending`, or `blocked`, the mapped
governed action, whether the action writes, whether confirmation is required,
and current blockers. This makes the real-file proof path visible without
adding a new workflow engine or authority surface.

Preserved boundaries:

- no new write path
- no automatic action sequencing
- no browser automation
- no MCP/provider calls
- no delivery authority
- no scheduler/cron authority
- no canonical note mutation
- no `02_KNOWLEDGE/` mutation

## 2026-04-30 Manual-Test Readiness Closeout Update

Status: COMPLETE / VERIFIED TARGETED for development-side closeout before the
real local-file rehearsal.

The acquisition cockpit model now includes a `manual_test_readiness` contract
with surface id `studio_acquisition_manual_test_readiness`. It reports:

- `development_ready_for_manual_real_file_test`
- `manual_input_ready`
- `manual_rehearsal_complete`
- current rehearsal step
- remaining development passes before manual tests
- remaining manual test passes
- development blockers
- manual blockers
- required/optional source classes
- exact manual test sequence

The localhost cockpit renders this as `Manual test readiness`, and the app plan
/ health JSON also expose it for machine-readable inspection.

The local app now also surfaces a sanitized `Recent app actions` view from the
existing append-only audit log:

```text
runtime/studio/state/acquisition-cockpit-app-events.jsonl
```

This is read-only display of already-recorded local action attempts. It does not
log source content, does not create a new datastore, and does not add a new
execution path.

Development-side remaining passes for this narrow feature are now closed. The
remaining work is manual/live proof only:

1. `phase10a0-real-local-file-rehearsal`
2. `phase10a0-reviewed-research-pack-sbp-proof`

Preserved boundaries:

- no browser automation
- no MCP/provider calls
- no delivery authority
- no scheduler/cron authority
- no canonical note mutation
- no automatic action sequencing
- no `02_KNOWLEDGE/` mutation

## 2026-05-07 Clear Active Intake + Flexible Coverage Update

Status: PARTIAL IMPLEMENTED / VERIFIED TARGETED.

The acquisition cockpit now exposes a confirmation-gated reset path:

```text
chaseos studio acquisition-cockpit --profile strikezone --action clear-active-intake --confirm-action --json
```

The action archives active staged inbox files and active imported source files
under `runtime/acquisition/manual/strikezone/_archive/<clear-id>/`, appends
`runtime/acquisition/state/strikezone-active-intake-clears.jsonl`, and deletes
nothing. It does not clear preview packs or the latest pointer.

The localhost app now renders:

- `Research Intake Cockpit`
- `Profile: StrikeZone Market Digest Pilot`
- `Source coverage` instead of `Required inputs`
- `Coverage warnings` instead of a hard missing-source gate
- `Reset current intake` with copy that says archive, not delete
- Pulse/runtime controls behind `Runtime/Pulse technical controls`

Machine-readable staging now reports `source_coverage_model=flexible`,
`minimum_viable_source_count=1`, `required_source_classes=[]`, and
`missing_recommended_source_classes` as warning metadata.

Verified with:

```text
python -m pytest runtime/studio/test_phase10a0_acquisition_cockpit.py runtime/studio/test_phase10a0_acquisition_cockpit_app.py -q
python -m runtime.cli.main studio acquisition-cockpit --profile strikezone --action clear-active-intake --json
python -m runtime.cli.main studio acquisition-cockpit-app --profile strikezone --port 8774 --dry-run --json
```

The unconfirmed clear action fails closed with `clear_active_intake requires --confirm-action`.

Remaining UI cleanup:

- full stepper polish and visual QA
- app launcher/port identity health
- PDF/DOCX/XLSX/CSV normalized intake
- real write-preview, reviewed promotion, and SBP verification proof

## Acceptance Criteria For The Next UI Pass

The next runtime should be considered successful if:

1. A local UI surface can display the current StrikeZone acquisition readiness model.
2. The UI shows missing required source classes when no real files exist.
3. Safe import/drop copies only supported files into declared source-class folders.
4. Preview is read-only unless the operator explicitly chooses preview-write.
5. Reviewed promotion cannot run without explicit confirmation.
6. SBP verification remains read-only.
7. Authority boundaries are visible in the UI and backed by tests.
8. No live providers, browser, MCP, delivery, cron, or canonical writeback authority is added.
9. Build log, documentation-history note, daily note, indexes, and agent activity are updated.

## Prompt For The UI Runtime

```text
Continue ChaseOS with repo-grounded task `phase10a0-studio-ui-implementation`.

Read first:
- README.md
- ROADMAP.md
- 00_HOME/Now.md
- 06_AGENTS/Phase10A0-Live-Proof-Test-Handover.md
- 06_AGENTS/Phase10A0-UI-Runtime-Handover.md
- 06_AGENTS/ChaseOS-Studio-Architecture.md
- runtime/studio/acquisition_cockpit.py
- runtime/studio/test_phase10a0_acquisition_cockpit.py
- runtime/COMMANDS.md

Build the first local-only Phase 10A0 UI around the existing Studio Acquisition Intake Cockpit model. Do not invent a second datastore or bypass ChaseOS. The first screen must show StrikeZone research readiness, source-class cards, missing files, safe import/drop handling, read-only preview, explicit preview-write, explicit reviewed promotion, read-only SBP verification, authority boundaries, warnings, and next actions. Preserve ChaseOS governance: no browser, MCP, delivery, cron, live provider, secret display, or canonical writeback authority. Add focused tests and required build/archive/daily/activity logs.
```

## Related Files

- `06_AGENTS/Phase10A0-Live-Proof-Test-Handover.md`
- `06_AGENTS/ChaseOS-Studio-Architecture.md`
- `06_AGENTS/Operator-Surface-Runtime-Interaction.md`
- `06_AGENTS/Phase9-Implementation-Closure-Plan.md`
- `runtime/studio/acquisition_cockpit.py`
- `runtime/studio/test_phase10a0_acquisition_cockpit.py`
- `runtime/COMMANDS.md`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
