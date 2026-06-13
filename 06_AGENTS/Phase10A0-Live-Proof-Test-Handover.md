---
type: handover
title: Phase 10A0 Live Proof Test Handover
status: PARTIAL / LOCAL FILE-PICKER-DROP COMPLETE TARGETED / FLEXIBLE SOURCE COVERAGE CORRECTED / REAL-FILE PROOF IN PROGRESS
created: 2026-04-29
updated: 2026-05-07
phase: Phase 10A0
runtime: Codex
session_descriptor: phase10a0-live-proof-testing-handover
knowledge_class: system-operational
---

# Phase 10A0 Live Proof Test Handover

## 2026-05-07 Operator Correction - Flexible Source Coverage

The cockpit must not require exactly three source roles and must not require one
file from every named platform before useful work can proceed. The earlier
`perplexity_digest`, `youtube_summary`, and `research_export` grouping should be
treated as coverage/confidence guidance for the StrikeZone pilot, not as a hard
product gate.

Correct rule going forward:

- One real source is sufficient to stage, import, preview, and write a bounded
  runtime-local preview pack.
- Additional source roles may improve confidence, corroboration, or final
  briefing quality.
- Missing source roles should be warnings, not blockers, unless a specific
  downstream workflow explicitly declares that a source role is required.
- The UI must not say `Required inputs 1 / 3` as if every operator workflow needs
  one source from each platform.

Operator screenshots from the 2026-05-07 manual staging test are summarized in
`06_AGENTS/Phase10A0-Acquisition-Cockpit-Cleanup-Plan.md`. The screenshots show
`stage-upload complete`, `Staged inbox 1`, `Required inputs 1 / 3`, and text-only
accepted file suffixes. This is now backlog evidence for cockpit copy/flow
cleanup and document-normalized intake.

Same-test backend observation: after the operator imported the staged file,
`research-status` reported `source_count=1` and `preview-research --json` passed
read-only with one `perplexity_digest` file. That means the current backend can
preview with one real source; the remaining defect is the UI/staging readiness
model and proof copy still implying a hard three-source gate.

## Task Name

Machine/session descriptor:

`phase10a0-studio-acquisition-intake-cockpit`

Human-readable task name:

`Phase 10A0 - Studio Acquisition Intake Cockpit`

## Repo-Truth Baseline

- Phase 9 is still active feature-by-feature. It is not globally closed.
- OSRIL Phase 9 runtime-side scope is closed, but Phase 10+ live surfaces remain future.
- Acquisition + Normalization has a real local/import research lane for StrikeZone.
- The manual workflow now includes `research-status`, `preview-research`, `promote-research-preview`, and `verify-research-sbp`.
- The Studio cockpit service/CLI/action wrapper now exists for `stage-upload`, `import-file`, `import-inbox`, `preview-read-only`, `preview-write`, `promote-reviewed-preview`, and `verify-research-sbp`.
- The next bottleneck for the StrikeZone acquisition/SBP lane is operator UX, not more architecture.
- Phase 10A0 is a narrow UI foothold. It does not make the full Studio product complete.

## Direct Test Answer

Not every remaining proof needs real local source files.

## 2026-05-06 Real Local Research File Proof Attempt

The `phase10a0-real-local-research-file-proof` pass checked the declared StrikeZone source folders and `_inbox` folders. The reusable repository template and local cockpit staging surface are ready, but no operator-selected research files are present yet:

- `research-status`: `source_count=0`, `inbox_candidate_count=0`
- missing pilot coverage classes: `perplexity_digest`, `youtube_summary`, `research_export`
- `import-research-inbox --json`: `candidate_count=0`
- `preview-research --json`: blocked with `no research import files found under declared drop folders`
- `verify-research-sbp --json`: blocked with `latest pointer plan_id is not 'strikezone-research-import-preview'`

This is a blocked proof attempt, not workflow verification. Historical note: this pass used the older three-role proof language. The superseding 2026-05-07 operator correction above requires flexible source coverage: a single real source must be enough for import and preview proof, while multi-role coverage is only confidence metadata unless a specific downstream workflow declares a hard dependency.

## 2026-05-07 Major Local File-Picker / Drop Workflow Pass

The `phase10a0-major-local-file-drop-workflow` pass completed the local file-picker/drop staging lane at a targeted implementation level:

- added `/staging.json`
- added `studio_acquisition_file_drop_workflow`
- added the staging workflow payload to dry-run app plans and `/health.json`
- added explicit `Pick or drop local file` controls per source class
- kept `stage-upload` writes scoped to `_inbox/<source_class>/`
- added upload audit destination and size fields
- verified a current-code localhost app at `http://127.0.0.1:8768/`

This is still not a real-file workflow proof. Current live status remains `source_count=0`, `inbox_candidate_count=0`, and missing pilot coverage classes `perplexity_digest`, `youtube_summary`, and `research_export`. These classes must no longer be treated as a universal hard gate.

## 2026-05-07 Real Local File Rehearsal Attempt

The operator requested the next proof pass after the local file-picker/drop workflow. Current-code localhost proof remained available at `http://127.0.0.1:8768/`, but the rehearsal could not proceed because no real files were present:

- `/staging.json`: `required_ready_count=0`, `staged_inbox_candidate_count=0`, `imported_source_file_count=0`, `next_action=stage-upload`
- `research-status`: `source_count=0`, `inbox_candidate_count=0`
- `import-research-inbox --json`: `candidate_count=0`, `imported_count=0`, `writes=[]`
- `preview-research --json`: blocked with `no research import files found under declared drop folders`
- `verify-research-sbp --json`: blocked with `latest pointer plan_id is not 'strikezone-research-import-preview'`

Result: BLOCKED / NOT VERIFIED. The next import/preview proof can run after at least one actual operator research file is staged and imported. Stronger multi-source SBP confidence can be tested later, but the cockpit must not block basic preview work on all three pilot source classes.

| Feature / proof | Needs real local files? | What it actually needs |
|---|---:|---|
| Coordination-watch activation proof | No | Real host state: elevated Task Scheduler registration, a durable success record, and post-reboot/logon verification result evidence |
| Research-pack SBP verification | Yes for final live proof | At least one real operator research file for minimum proof; extra Perplexity, YouTube, research export, and optional Grok files improve coverage/confidence but are not a default hard gate |
| Phase 10A0 UI plumbing | No for first UI tests | Synthetic/drop-test files can prove import, status, preview, and confirmation behavior |
| Phase 10A0 live workflow proof | Yes | Real operator-supplied local research file(s), then preview, reviewed promotion, and SBP consumption verification |

Fixtures and synthetic files are enough for interface plumbing and fail-closed behavior. They are not enough to claim that the real StrikeZone research workflow is useful or live-verified.

## Phase 10A0 MVP Scope

Build a local-only operator cockpit that wraps the existing Phase 9 acquisition workflow.

The first screen should support:

- Show `research-status` for the StrikeZone profile.
- Show source classes as coverage roles, not mandatory platform quotas.
- Show which declared source-class folders have files and which are empty.
- Let the operator drop/import saved Perplexity, YouTube, research export, and optional Grok files into the correct folders.
- Run read-only preview.
- Write preview pack only on explicit operator action.
- Promote a reviewed preview only with explicit confirmation.
- Verify SBP consumption of the reviewed preview pack.
- Surface warnings, provenance, trust, freshness, and next actions.

## Commands The UI Should Wrap

Canonical operator commands:

```text
chaseos acquisition research-status --profile strikezone --json
chaseos acquisition preview-research --profile strikezone --json
chaseos acquisition preview-research --profile strikezone --write --json
chaseos acquisition promote-research-preview --profile strikezone --briefing-input <path> --reviewed --json
chaseos acquisition verify-research-sbp --profile strikezone --json
```

If a local console-script target is stale, the implementation pass may use the equivalent `python -m runtime.cli.main ...` invocation while keeping the UI command boundary aligned with the canonical `chaseos` surface.

Studio action-wrapper commands now available:

```text
chaseos studio acquisition-cockpit --profile strikezone --action import-file --source-class <source-class> --source-file <operator-selected-file> --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --action clear-active-intake --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --action preview-read-only --json
chaseos studio acquisition-cockpit --profile strikezone --action preview-write --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --action promote-reviewed-preview --briefing-input <preview-briefing-ready-input-set> --reviewed --confirm-action --json
chaseos studio acquisition-cockpit --profile strikezone --action verify-research-sbp --json
```

## 2026-05-07 Clear / Reset Test Update

The cockpit now has an explicit clear/reset action for the issue observed during
manual testing, where staged/imported state remained visible after the import.

Current behavior:

- `clear-active-intake` requires `--confirm-action`.
- It moves active staged inbox files and active imported source files to
  `runtime/acquisition/manual/strikezone/_archive/<clear-id>/`.
- It appends `runtime/acquisition/state/strikezone-active-intake-clears.jsonl`.
- It deletes nothing.
- It does not clear preview packs or `runtime/acquisition/packs/strikezone-latest.json`.
- The app displays `Reset current intake` so the operator can start the next
  intake test without the prior active file continuing to count as current state.

Verification:

- Targeted tests: `42 passed`.
- Real-vault unconfirmed clear command fails closed with
  `clear_active_intake requires --confirm-action`.
- Real-vault dry-run app plan exposes `source_coverage_model=flexible`,
  `minimum_viable_source_count=1`, `clear-active-intake`, and
  `deletes_files=false`.

This does not complete the full live proof. The current real file remains useful
evidence for stage/import/read-only preview, but reviewed preview write,
promotion, and SBP verification remain unverified.

## 2026-05-07 Perplexity Digest Manual Test Result

The manual Perplexity digest test was not intended to create a final briefing,
summary markdown, reviewed pack, or SBP-ready output. It was the first live proof
for the roadmap item: interactive local file intake through the Studio
Acquisition Cockpit.

What the operator tested:

1. A real local Perplexity digest markdown file could be selected through the
   cockpit upload control.
2. The cockpit could stage the selected file into the governed inbox.
3. The cockpit could import the staged inbox file into the declared local source
   repository.
4. The app event log and import ledger could record the action with file path,
   size, fingerprint, source class, and metadata warnings.

Expected outcome:

- `stage-upload` writes the selected file to
  `runtime/acquisition/manual/strikezone/_inbox/perplexity_digest/`.
- `import-inbox` writes/copies the staged file to
  `runtime/acquisition/manual/strikezone/perplexity_digest/`.
- `runtime/studio/state/acquisition-cockpit-app-events.jsonl` records attempted
  and successful app actions.
- `runtime/acquisition/state/strikezone-research-inbox-imports.jsonl` records
  the import ledger.
- The cockpit reports one present source and does not require three different
  source roles.

Actual outcome:

- PASS: the file was staged into
  `runtime/acquisition/manual/strikezone/_inbox/perplexity_digest/LTF Morning Prep &amp; Daily Bias (9_30 AM Daily).md`.
- PASS: the file was imported into
  `runtime/acquisition/manual/strikezone/perplexity_digest/LTF Morning Prep &amp; Daily Bias (9_30 AM Daily).md`.
- PASS: the app event log recorded `stage-upload` and `import-inbox`.
- PASS: the import ledger recorded the imported file with fingerprint
  `ad6e6a3aa0cd4fc901e0022910141806fb8a773dacb2cc45abdfd06c67800add`.
- PASS: the patched cockpit contract reports `source_coverage_model=flexible`,
  `minimum_viable_source_count=1`, and `required_source_classes=[]`.
- PASS: a read-only preview check can read the imported Perplexity digest as one
  Tier-3 source without writing files or updating the latest pointer.
- IMPORTANT AT THE TIME OF THIS TEST: the staged and imported files were byte-for-byte identical. The
  intake step preserved the raw Perplexity digest; it did not rename,
  standardize, rewrite, frontmatter-normalize, date-normalize, or add the source
  to the daily index.
- NOT VERIFIED: true browser drag/drop gesture if the operator used the file
  picker instead of dropping the file onto the control.
- NOT VERIFIED: preview pack write.
- NOT VERIFIED: reviewed preview promotion.
- NOT VERIFIED: SBP consumption.
- NOT BUILT AT THE TIME OF THIS TEST: PDF/DOCX/XLSX/CSV normalization.
- NOT BUILT AT THE TIME OF THIS TEST: standardized digest output that creates a
  dated markdown artifact and links it into the daily operating layer.

## 2026-05-07 Production Intake Development Update

Status: IMPLEMENTED TARGETED / MANUAL REAL-FILE RETEST PENDING.

After the first manual test exposed the missing product behavior, Codex added the production intake path:

- Confirmed imports now preserve the raw file under `runtime/acquisition/manual/strikezone/_raw/<source_class>/`.
- Confirmed imports now create a dated standardized Markdown artifact under `runtime/acquisition/manual/strikezone/<source_class>/`.
- The standardized artifact includes provenance, trust tier, dashboard-ready metadata, source fingerprint, raw source path, and normalized source content.
- Imports now append `runtime/acquisition/state/strikezone-research-dashboard-artifacts.jsonl`.
- Imports now add the artifact to `07_LOGS/Daily/<artifact-date>.md` under `Development / Research Intake` and update `07_LOGS/Daily/Daily-Index.md`.
- Accepted staging/import types now include `.pdf`, `.docx`, `.xlsx`, `.csv`, common image suffixes, and the previous readable text suffixes.
- The hard three-source gate is removed from cockpit model/app contracts; missing source classes are coverage warnings only.
- The localhost app now includes static drag/drop handling and visible `Clear current intake` controls at the top and inside the local file-picker/drop workflow section.
- The localhost app now shows an acquisition proof chain: standardized artifact, preview pack write, reviewed promotion, and SBP verification.

Verification run in code and synthetic local files:

- `python -m py_compile runtime/acquisition/intake_normalization.py runtime/acquisition/research_imports.py runtime/studio/acquisition_cockpit.py runtime/studio/acquisition_cockpit_app.py runtime/acquisition/test_phase10a0_intake_normalization.py runtime/studio/test_phase10a0_acquisition_cockpit.py runtime/studio/test_phase10a0_acquisition_cockpit_app.py`
- `python -m pytest runtime/acquisition/test_phase10a0_intake_normalization.py runtime/studio/test_phase10a0_acquisition_cockpit.py runtime/studio/test_phase10a0_acquisition_cockpit_app.py -q` (`44 passed`)
- `python -m pytest runtime/acquisition/test_phase9_acquisition_research_import_preview.py runtime/acquisition/test_phase9_acquisition_research_source_classes.py -q` (`44 passed`)
- Live localhost smoke on `http://127.0.0.1:8775/`, `/health.json`, and `/staging.json`.

This still does not close the roadmap feature as VERIFIED. The remaining proof must be performed with real operator files from the beginning: clear active intake, drag/drop or choose a real file, stage, import, inspect standardized output and daily index writeback, write preview pack, promote reviewed preview, and run SBP verification.

Roadmap interpretation:

The file-picker half of the interactive local-file intake workflow is partially
proved with one real local markdown file. The roadmap row must not be marked
COMPLETE yet because drag/drop gesture proof, preview-pack write, reviewed
promotion, SBP consumption, document-normalized intake, standardized output
generation, and daily-index writeback remain open.

Next manual proof step:

Run `preview-write` against the imported Perplexity digest after deciding whether
to keep the current file active or clear/reset and re-import it cleanly. Expected
output is a dated preview pack under `runtime/acquisition/packs/`, including
source packets, normalized source pack material, and a briefing-ready input set.

## Live Proof Matrix

| Proof family | Status before Phase 10A0 | First Phase 10A0 test | Final live proof |
|---|---|---|---|
| Local/import file readiness | Command and Studio action-wrapper surfaces exist | COMPLETE TARGETED: UI shows source-class folders, coverage warnings, `/staging.json`, and local picker/drop controls | At least one real operator file present; broader source coverage is confidence metadata |
| Research preview | Read-only/write modes and Studio wrappers exist | UI runs read-only preview with synthetic files | Preview pack generated from real local files |
| Reviewed promotion | Existing command and Studio wrapper require explicit confirmation | UI blocks promotion until explicit confirmation | Latest pointer updates only after reviewed real preview |
| SBP consumption | Read-only verifier and Studio wrapper exist | UI displays verifier result | `verify-research-sbp` passes against reviewed real preview |
| Coordination-watch activation | LIVE-AWAITING-REBOOT-PROOF / VERIFIED TARGETED by current repo truth | UI may display proof state later, read-only | Post-reboot/logon verifier result reconciled back into ChaseOS |
| Discord/Whop/n8n/provider live surfaces | Separate credentials/deployments | UI should not expand these | Operator-approved secret/deployment pass only |

## Boundaries For Phase 10A0

Do not use this foothold to expand authority.

Phase 10A0 must not:

- Create a second datastore.
- Mutate canonical notes or project OS files.
- Bypass Gate or role-card boundaries.
- Add browser authority.
- Add MCP authority.
- Add delivery authority.
- Add cron/scheduler authority.
- Add live provider calls.
- Hide file writes behind implicit UI actions.

All write actions must map to existing governed Phase 9 surfaces and require visible operator intent.

## Test Ladder

1. Empty-state UI: no source files present; status shows missing recommended classes and next actions.
2. Synthetic local-file UI plumbing: drop one or more safe test files; preview reads them; no latest pointer changes.
3. Preview write: explicit write action produces runtime-local preview pack only.
4. Reviewed promotion: explicit confirmation updates only the runtime latest pointer.
5. SBP verifier: read-only verification confirms the latest pointer can be consumed by `sbp_strikezone_digest`.
6. Real-file workflow: repeat steps 1-5 with at least one real operator research file; repeat with additional source roles only to test confidence/coverage handling.


## Final-Pass Interface Notes For Runtime Building Studio

The first UI foothold should remain Phase 10A0, but the implementation team should design the shell so the following adjacent panels can slot in without rewriting the backend contract:

- **Settings/provider/config panel:** read from config validation/summary and provider-status. Show missing provider setup and degraded runtime binding clearly; do not display secrets or mutate provider state implicitly.
- **Approval Center:** model OSRIL approval/wait/resume as a two-step visible chain: decision record first, explicit resume-ready action second. Preserve approval ID, workflow ID, session ID, runtime ID, and audit references in the UI. Route current cross-feature Approval Center semantics through [[ChaseOS-Approval-Center]].
- **Runtime Cockpit:** include Agent Bus status, bounded task list views, heartbeats, runtime lifecycle/registry posture, provider status, and coordination-watch activation proof. Use bounded list payloads and filters so the cockpit remains usable with a large backlog.
- **Provenance Explorer:** expose lineage as read-only evidence navigation; do not let operators edit provenance records from this surface.
- **Memory / Agent Identity Ledger:** display runtime identity, scorecards, repair memory, nav overlays, and task-local memory as advisory runtime state only. Never treat this as canonical doctrine or permission authority.
- **Graph/node view:** maintain stable IDs, typed edges, trust-state badges, runtime/action edges, and derived/rebuildable index discipline from the start.
- **Voice/visual/companion lanes:** useful later for operator experience, but they are ingress surfaces. They should translate to structured ChaseOS state and obey Tier-4 input handling, Agent Bus routing, OSRIL approval, and Gate constraints.
- **Reconnect/history/continuation UX:** should replay OSRIL events, active Agent Bus tasks, approval waits, resume-ready items, and audit trails after reconnect; do not create a second unmanaged session memory store.

If Studio desktop/product shell work is not available yet, the useful work in the meantime is to keep the backend surfaces clean and UI-ready: run read-only smokes, keep bus queues inspectable with bounded output, verify provider/config posture, document degraded states, and avoid widening runtime authority just to make demos easier.

## Next Chat Prompt

Use this prompt to continue in the Phase 10A0 implementation chat:

```text
Continue ChaseOS with repo-grounded task `phase10a0-studio-ui-shell-first-screen`.

Start by reading README.md, PROJECT_FOUNDATION.md, ROADMAP.md, 00_HOME/Now.md, 06_AGENTS/Phase10A0-Live-Proof-Test-Handover.md, 06_AGENTS/Phase10A0-UI-Runtime-Handover.md, runtime/studio/acquisition_cockpit.py, runtime/studio/test_phase10a0_acquisition_cockpit.py, runtime/cli/main.py, runtime/COMMANDS.md, and the latest Phase 10A0 build logs.

Build the first local UI shell/screen over the existing Phase 10A0 service and CLI action layer. The screen should show StrikeZone research readiness, source-class cards, missing folders/files, safe file import/drop handling, read-only preview, explicit preview-write, explicit reviewed promotion, read-only SBP verification, action results, disabled-control reasons, and authority boundaries. Use the existing `run_acquisition_cockpit_action()` backend contract; do not invent a second datastore or bypass ChaseOS. Do not add browser, MCP, delivery, cron, live provider, secret display, or canonical writeback authority. Add focused tests, visual/render verification if a UI runtime is introduced, and required build log, documentation-history note, daily note, indexes, and agent activity log.
```

## Related Files

- `ROADMAP.md`
- `00_HOME/Now.md`
- `06_AGENTS/Phase10A0-UI-Runtime-Handover.md`
- `06_AGENTS/Phase9-Implementation-Closure-Plan.md`
- `06_AGENTS/Feature-Register.md`
- `06_AGENTS/Acquisition-Normalization-Layer.md`
- `06_AGENTS/StrikeZone-Acquisition-Normalization-Pilot.md`
- `06_AGENTS/Scheduled-Briefing-Pipelines.md`
- `runtime/COMMANDS.md`


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
