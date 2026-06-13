---
title: Phase 10A0 Acquisition Cockpit Cleanup Plan
type: implementation-plan
status: ACTIVE-BACKLOG
phase: Phase 10A0
runtime: Codex
created: 2026-05-07
updated: 2026-05-07
---

# Phase 10A0 Acquisition Cockpit Cleanup Plan

This plan records the operator correction from the first real local-file cockpit test. The current localhost cockpit can stage a file, but the product flow, copy, source coverage model, and accepted file types are not yet acceptable for a production ChaseOS Studio experience.

## Operator Screenshot Evidence

Operator-attached screenshots in the 2026-05-07 Codex thread show the current cockpit after a successful `stage-upload`:

- Header: `Studio Acquisition Cockpit`, with `Profile: strikezone`.
- Success banner: `stage-upload complete`.
- Metrics: `Source files 0`, `Staged inbox 1`, `Preview packs 0`, `Missing recommended 3`, `Current pointer SBP blocked`, `Reviewed preview pending`.
- Local file-picker/drop workflow: `Required inputs 1 / 3`, `Staged inbox 1`, `Imported sources 0`, `Next action import-inbox`.
- Source cards show `perplexity_digest` as `1 staged / 0 imported`, while `youtube_summary` and `research_export` remain at `0 staged / 0 imported`.
- Accepted suffixes shown in the UI are text formats only: `.html`, `.json`, `.md`, `.toml`, `.txt`, `.yaml`, `.yml`.

The screenshot itself is attached to the Codex conversation, not persisted as a local file artifact by this docs-only pass. The screenshot content above is the repo-recorded evidence summary until a browser/visual QA pass captures a local artifact.

## Required Product Corrections

## Current Backend Observation From Same Test

After the operator pressed `Import staged inbox files`, a read-only status check reported `source_count=1` and `source_classes.perplexity_digest=1`. The importer copies staged files into the source folder and leaves the inbox copy in place, so the UI can still show `Staged inbox 1` after a successful import. That is technically explainable but confusing and should be clarified in the cockpit.

`python -m runtime.cli.main acquisition preview-research --profile strikezone --json` then passed with one real imported source. This proves the backend can already preview with fewer than three source roles. The remaining defect is the cockpit/staging readiness model and product language still presenting three pilot source roles as required.

## Implementation Update - 2026-05-07 Clear Active Intake

Codex implemented the first code-backed cleanup slice:

- Added `clear-active-intake` / `clear_active_intake` to the governed Studio acquisition cockpit action set.
- The clear action requires `--confirm-action`.
- The action archives active staged inbox files and active imported source files under `runtime/acquisition/manual/strikezone/_archive/<clear-id>/`.
- The action appends `runtime/acquisition/state/strikezone-active-intake-clears.jsonl`.
- The action does not delete files, does not clear preview packs, and does not clear `runtime/acquisition/packs/strikezone-latest.json`.
- The localhost app now shows a visible `Reset current intake` panel that says the operation archives rather than deletes.
- The staging contract now reports `source_coverage_model=flexible`, `minimum_viable_source_count=1`, `required_source_classes=[]`, and `missing_recommended_source_classes` as warnings rather than gates.
- The app header now uses `Research Intake Cockpit` and `Profile: StrikeZone Market Digest Pilot`.
- Pulse/runtime controls are no longer first-class in the main acquisition page; they are behind a technical details panel.

Targeted tests passed: `python -m pytest runtime/studio/test_phase10a0_acquisition_cockpit.py runtime/studio/test_phase10a0_acquisition_cockpit_app.py -q` (`42 passed`). Live-safe CLI checks confirmed the unconfirmed clear action fails closed and the dry-run app plan exposes `clear-active-intake` with `deletes_files=false`.

## Implementation Update - 2026-05-07 Production Intake Workflow

Codex implemented the larger production-intake slice requested after the first manual Perplexity test:

- Added `runtime/acquisition/intake_normalization.py` as the local-only normalization layer.
- Confirmed import now preserves the raw source under `runtime/acquisition/manual/strikezone/_raw/<source_class>/`.
- Confirmed import writes a dated standardized Markdown artifact under `runtime/acquisition/manual/strikezone/<source_class>/`.
- Confirmed import appends dashboard-ready artifact records to `runtime/acquisition/state/strikezone-research-dashboard-artifacts.jsonl`.
- Confirmed import links artifacts into `07_LOGS/Daily/<artifact-date>.md` and `07_LOGS/Daily/Daily-Index.md`.
- Supported intake suffixes now include `.pdf`, `.docx`, `.xlsx`, `.csv`, common image formats, and the previous readable text formats.
- The hard three-source requirement is removed from the model and app contracts; `required_source_classes=[]` and missing source roles are warnings.
- The localhost app now includes static drag/drop JavaScript, a clearer `Drop a local file here or choose from this PC` control, proof-chain cards, and `Clear current intake` controls at the top and inside the local file-picker/drop workflow section.

Targeted verification passed:

- `python -m py_compile runtime/acquisition/intake_normalization.py runtime/acquisition/research_imports.py runtime/studio/acquisition_cockpit.py runtime/studio/acquisition_cockpit_app.py runtime/acquisition/test_phase10a0_intake_normalization.py runtime/studio/test_phase10a0_acquisition_cockpit.py runtime/studio/test_phase10a0_acquisition_cockpit_app.py`
- `python -m pytest runtime/acquisition/test_phase10a0_intake_normalization.py runtime/studio/test_phase10a0_acquisition_cockpit.py runtime/studio/test_phase10a0_acquisition_cockpit_app.py -q` (`44 passed`)
- `python -m pytest runtime/acquisition/test_phase9_acquisition_research_import_preview.py runtime/acquisition/test_phase9_acquisition_research_source_classes.py -q` (`44 passed`)
- Live localhost smoke on `http://127.0.0.1:8775/`, `/health.json`, and `/staging.json`.

Status: IMPLEMENTED TARGETED / MANUAL REAL-FILE RETEST PENDING. The code path is ready for the next from-zero operator run, but the roadmap item is not fully verified until an operator repeats the workflow with real local files through drag/drop or picker, import, preview-write, reviewed promotion, and SBP verification.

### Flexible Source Coverage

The cockpit must not require exactly three source roles, and it must not require one file from every named platform before useful work can proceed.

New rule:

- One real source must be enough to stage, import, preview, and produce a bounded runtime-local preview pack.
- Additional sources should improve coverage/confidence, not unlock the workflow.
- The UI may warn about thin coverage, missing corroboration, or missing source diversity.
- The UI must not frame `perplexity_digest`, `youtube_summary`, and `research_export` as mandatory product-wide gates.
- Final proof language should distinguish `minimum viable intake` from `stronger multi-source confidence`.

Replacement copy:

```text
Source coverage: 1 source staged
Coverage note: additional source roles can improve confidence, but they are not required to continue.
Next action: import staged inbox files
```

### File Type Compatibility

The current text-only suffix list is insufficient. Operators will frequently have PDF, DOCX, XLSX, CSV, and exported report files.

Required behavior:

- Accept common local research file formats at staging time.
- Preserve the original file as provenance.
- Normalize non-text formats into a readable `.md` or structured `.json` representation before preview.
- Do not merely add binary extensions to `READABLE_SUFFIXES` without extraction/normalization.
- Surface unsupported formats with a plain reason and a next step.

Initial target formats:

| Format | Expected handling |
|---|---|
| `.pdf` | Extract text/pages into normalized Markdown with source provenance |
| `.docx` | Extract paragraphs/tables into normalized Markdown |
| `.xlsx` | Extract worksheets/tables into structured JSON and/or Markdown |
| `.csv` | Parse as tabular source export |
| `.html` | Keep current readable path |
| `.md`, `.txt`, `.json` | Keep current readable path |

### Cockpit Flow Cleanup

Replace the current mixed page with a clear operator stepper:

1. Stage files
2. Import inbox
3. Preview
4. Write preview
5. Review and promote
6. Verify SBP consumption

Rules:

- Show one current next action.
- Keep raw command details behind an expandable technical panel.
- Remove unrelated Pulse schedule/runtime controls from the acquisition cockpit.
- Do not auto-scroll the operator to the top after staging unless the success banner also provides an anchored `Continue to import` control.
- Replace `Remaining development passes before manual test: none` with honest status text.

Better readiness copy:

```text
Development surface: available
Manual proof: in progress
Current stage: import staged inbox files
Blocked proof items: reviewed preview and SBP verification are not complete
```

### Profile Naming

`strikezone` is the current pilot profile. It must not read as the product identity.

Replacement pattern:

```text
Research Intake Cockpit
Profile: StrikeZone Market Digest Pilot
```

Future work should support user-created profiles rather than hardcoding a single profile into the surface.

### App Navigation And Port Truth

The cockpit must be reachable from a reliable Studio app launcher/shell.

Required launcher behavior:

- Show each registered Studio surface.
- Show expected port, actual health, and actual app identity.
- Warn when a port is listening but serving the wrong or stale surface.
- Provide navigation links between local Studio surfaces.
- Avoid asking the operator to manually guess ports.

## Next Implementation Passes

| Pass | Status | Output |
|---|---|---|
| `phase10a0-studio-app-health-launcher` | PLANNED | Reliable app launcher with port/app identity health checks |
| `phase10a0-acquisition-cockpit-flow-cleanup` | PARTIAL | Header/copy/flexible coverage/reset archive action implemented; proof-chain panel added; full app launcher/navigation still open |
| `phase10a0-document-normalized-intake` | IMPLEMENTED TARGETED / MANUAL PROOF PENDING | PDF/DOCX/XLSX/CSV/images/text normalization with original-file provenance, standardized Markdown output, dashboard ledger, and daily index integration |
| `phase10a0-flexible-preview-coverage` | IMPLEMENTED TARGETED / MANUAL PROOF PENDING | UI/staging/model contracts treat missing source roles as warnings; one real source can continue |
| `phase10a0-real-file-preview-proof` | NEXT | Re-run from zero with a real operator file, then preview-write, reviewed promotion, and SBP verification |

## Boundaries

This plan does not authorize:

- Provider calls.
- Browser automation expansion.
- MCP scope expansion.
- Delivery or scheduler authority.
- Canonical note mutation.
- Automatic reviewed promotion.
- Source deletion from inbox.
- Treating external file contents as instructions.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
