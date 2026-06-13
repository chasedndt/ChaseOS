---
date: 2026-05-30
runtime: Hermes / Optimus
type: feature-family-node
status: LOCAL DEVELOPMENT COMPLETE / REAL-TEST CLOSEOUT READY
feature_family: artifact_intelligence_submission_operator
short_name: AISO
risk_class: medium_high
authority: bounded local dry-run, approval-consuming rename, and approval-consuming package proof only
---

# Artifact Intelligence & Submission Operator

The **Artifact Intelligence & Submission Operator** (AISO) is a ChaseOS feature family for turning messy local files into governed, understood, packaged, and submission-ready artifacts. Its bounded local prepare/rename/package proof path is now development-complete and ready for a real-media closeout test; external submission authority remains separately gated.

The initial product story is the university video submission workflow: Chase records an assignment video, leaves it with a raw filename in a likely local folder, and asks ChaseOS to find it, understand it, rename a staged copy, package it, prepare an email or portal draft, request explicit approval, and leave a full audit trail.

AISO is a feature-family registration, not a live automation claim. No current row authorizes ambient filesystem scanning, original-file mutation, email sending, portal submission, credential access, unrestricted browser operation, provider calls, or canonical knowledge promotion.

## Primary Mission Example

```text
Find the university video I recorded last night, rename it properly, zip it, and prepare the Outlook email for submission.
```

Expected governed behavior:

1. Interpret the request as a bounded submission-prep mission.
2. Inspect only declared safe roots such as Downloads, Desktop, Videos/Captures, and approved University folders.
3. Produce a ranked candidate list with file, time, duration, size, and ranking reasons.
4. Run media comprehension on serious candidates: metadata, audio transcript, keyframe OCR, visual scene understanding, and evidence fusion.
5. Propose a deterministic, evidence-backed staged filename and package name.
6. Require approval for file selection, staged rename/package plan, attachment, send, upload, or portal submission according to risk.
7. Copy and rename only staged files by default; preserve originals.
8. Generate package, manifest, checksum, evidence summary, delivery draft, and audit logs.

## Architecture Placement

AISO sits across existing ChaseOS layers instead of replacing them:

| Layer | AISO role |
|---|---|
| AOR | Owns mission execution, manifest validation, handler routing, runtime coordination, approval checks, and audit writeback. |
| Capture / Connector | Provides artifact intake, sidecar metadata, quarantine-first routing, content packet identity, and provenance. |
| Media Comprehension Engine | Extracts metadata, transcript, OCR, keyframes, visual scene evidence, and fused confidence. |
| Gate / Permission Matrix | Enforces read roots, staging writes, no deletes, no original rename without approval, no external send/upload without approval. |
| Runtime adapters | Hermes/OpenClaw/browser/email adapters may operate files, email drafts, or portals only under workflow policy. |
| Studio | Future mission card for candidates, evidence, rename editor, staging preview, delivery draft, approval controls, and audit links. |
| SIC / Knowledge | Optional downstream source-note or knowledge promotion only after explicit separate promotion. Default AISO output is operational manifest/evidence, not knowledge ingestion. |

## Core Subfeatures

- Recent Artifact Locator.
- Media Metadata Extraction.
- Keyframe Sampler.
- Audio Transcript Understanding.
- OCR Keyframe Scanner.
- Visual-Only Video Understanding.
- Evidence Fusion Confidence Scorer.
- Rename Recommendation Engine.
- Staging and Packaging Layer.
- Submission Manifest / Evidence Summary Generator.
- Email Draft Adapter.
- Browser Portal Draft Adapter.
- Approval-Gated Delivery Flow.
- Media Workflow Audit Logger.
- Studio Mission Card.

## Proposed Workflow IDs

```yaml
workflow_id: university_submission_operator
workflow_id: media_artifact_package_operator
workflow_id: recent_artifact_locator
workflow_id: media_comprehension_scan
```

Proposed task types:

```yaml
university_submission_prepare
media_comprehension
artifact_rename_proposal
artifact_packaging
email_draft_prepare
browser_submission_prepare
```

## Default Risk Posture

```yaml
risk_class: medium_high
default_mode: prepare_and_stage
send_or_submit: explicit_approval_required
delete_originals: forbidden_by_default
overwrite_files: explicit_approval_required
promote_to_knowledge: false
media_derived_text_is_instruction: false
```

Transcript text, OCR text, subtitles, filenames, visible browser/page text, and media metadata are untrusted data. They may support evidence extraction, but they cannot change workflow policy, select recipients, authorize sends, or override ChaseOS instructions.

## Minimal Production Path

The roadmap from blueprint to production should remain gated:

1. Documentation and feature-family registration.
2. Recent Artifact Locator MVP over declared safe folders.
3. FFmpeg/ffprobe metadata + keyframe sampler.
4. Transcript understanding adapter.
5. OCR + visual scene understanding / visual-only mode.
6. Evidence fusion + rename proposal.
7. Staging + packaging + checksum + manifest.
8. Email draft adapter.
9. Browser portal draft adapter.
10. Studio mission card.

## First Bounded Dry-Run Contract

The first implementation slice must be a testable, local-only dry run. It is accepted only when an operator or reviewer can reproduce every step from fixtures, command output, proof files, and visual evidence without using credentials, provider APIs, live email, live portal submission, or canonical promotion.

Acceptance checklist:

- [x] Intent parse: fixture request resolves to `university_submission_prepare` with `prepare_and_stage` posture.
- [x] Safe-root locator: candidates come only from declared fixture/approved roots; outside-vault, credential-like, browser-profile, and missing roots are reported as blocked evidence.
- [x] Evidence/metadata stub: deterministic local metadata or fixture evidence is emitted; unavailable transcript/OCR/visual evidence is explicitly labelled rather than inferred.
- [x] Rename/package proposal: staged filenames, package names, manifest paths, and checksums are proposed without touching originals.
- [x] Result delivery fallbacks: all three dry-run result paths are represented: local proof packet, email draft preview with no send, and browser/portal draft preview with no submit.
- [x] Approval blocking: any write, attach, upload, send, submit, overwrite, original rename, provider call, credential use, or canonical promotion returns `approval_required` / `blocked` before side effects.
- [x] Audit envelope: JSON proof includes authority booleans, selected fallback path, blocked live paths, test commands/results, source fixture IDs, and visual proof artifact paths.

Per-step implementation test requirements:

| Step | Required tests for OPS implementation card |
|---|---|
| Intent parse | Add focused tests that prove the university submission prompt maps to `workflow_id=university_submission_operator`, `task_type=university_submission_prepare`, `mode=prepare_and_stage`, and `media_derived_text_is_instruction=false`. |
| Safe-root locator | Preserve `runtime/aiso/test_recent_artifact_locator.py` coverage and extend it or add sibling tests proving declared-root-only scans, outside-root rejection, credential/browser-profile root rejection, no file content read, and sorted candidate metadata. |
| Evidence/metadata stub | Test deterministic fixture/local metadata output with `provider_call=false`; unavailable transcript/OCR/keyframe evidence must be explicit statuses, not hallucinated content. |
| Rename/package proposal | Test deterministic staged target names and package names from evidence; assert original path, mtime, bytes, and filename are unchanged. |
| Local proof packet | Test that a dry run can produce or preview a local proof packet under `07_LOGS/Workflow-Proofs/` or an equivalent test temp directory with manifest, checksum plan, evidence summary, and visual preview path. |
| Email draft preview | Test generated subject/body/attachment plan and `email_send=false`; missing email adapter/credentials must return a structured fallback reason while preserving the local proof packet. |
| Browser/portal draft preview | Test generated portal action plan/preview and `browser_submit=false`; missing browser/session/portal authority must return a structured fallback reason while preserving the local proof packet. |
| Approval/audit envelope | Test the authority envelope booleans: `write_performed=false`, `original_mutation=false`, `provider_call=false`, `browser_submit=false`, `email_send=false`, `credential_access=false`, `canonical_promotion=false`; assert live actions block before side effects. |
| Visual QA proof | Test or QA script must generate a local HTML/Markdown preview plus screenshot/image artifact for proof packet, email draft preview, and portal draft preview when live adapters are unavailable; reviewer must cite screenshot paths. |

Expected OPS/reviewer command plan:

```bash
PYTHONPATH=. uvx --with pyyaml pytest runtime/aiso/test_recent_artifact_locator.py -q
PYTHONPATH=. uvx --with pyyaml pytest runtime/aiso/test_aiso_dry_run_contract.py -q
PYTHONPATH=. uvx --with pyyaml pytest runtime/aiso/test_aiso_result_fallbacks.py -q
```

If OPS chooses different filenames, the replacement tests must cover the same step names and authority booleans above, and the reviewer must cite the actual commands and results.

Fallback result design:

1. **Primary local proof packet** — always available in dry run; contains manifest/checksum plan/evidence summary/audit envelope plus rendered preview and screenshot path. This is the canonical QA recovery path when external adapters are blocked.
2. **Email draft preview without send** — generates body, subject, recipient placeholder/source requirement, attachment plan, and screenshot/HTML preview. It must never read credentials or send; if unavailable, it records `email_preview_blocked` and points back to the local packet.
3. **Browser/portal draft preview without submit** — generates a portal action plan and local preview/screenshot. It must never open an unrestricted browser session, read browser profiles, upload, or submit; if unavailable, it records `portal_preview_blocked` and points back to the local packet.

Authority boundary for this slice: no ambient scan, no original mutation, no credential read, no provider call, no live browser submit, no email send, no external upload, no approval consumption, no workflow execution beyond local dry-run/proof generation, and no canonical promotion.

## Current Status

AISO is **local-development complete for the bounded prepare/rename/package proof path and ready for a real-media closeout test**. It is not a live external submission operator. The implemented local path covers declared-root candidate location, deterministic local metadata stubs, proposal-only dry-run planning, email/portal previews with screenshot artifacts and no send/submit, explicit approval-consuming same-directory rename, explicit approval-consuming sibling `.zip` package creation, manifest/audit/exact-once proof records, Studio review/approval controls, and a read-only closeout readiness contract.

Current repo posture:

- Feature family is registered for planning and backlog tracking.
- User-submitted source dossier is retained as governed input at `03_INPUTS/00_QUARANTINE/2026-05-30-artifact-intelligence-submission-operator-user-dossier.md`.
- Current local foothold: `runtime/aiso/recent_artifact_locator.py`, `runtime/aiso/dry_run_contract.py`, `runtime/aiso/closeout_readiness.py`, `runtime/studio/aiso_rename_review_panel.py`, and focused `runtime/aiso/test_*` / `runtime/studio/test_aiso_rename_review_panel.py` coverage provide declared-root candidate location, deterministic local metadata stubs, rename/package proof planning, visual proof artifacts, approval-consuming rename, approval-consuming package creation, and real-test readiness reporting.
- Current proof: `07_LOGS/Workflow-Proofs/aiso-closeout-visual-proof-20260613/` proves the visual dry-run with email/portal screenshot artifacts, and `07_LOGS/Workflow-Proofs/aiso-full-rename-zip-smoke-20260613T0000Z/` proves the safe-root full rename plus zip package path.
- Remaining closeout-only action: run one operator-declared safe-root real media test, then record final approval/proof review. No further bounded local development pass is currently required for the prepare/rename/package proof path.
- Still not implemented / still separately gated: provider-backed transcript/OCR/visual understanding, live email send, live browser/portal upload/submit, credential access, unrestricted browser operation, and canonical knowledge promotion.

## Non-Scope Until Separately Approved

- Full filesystem scan.
- Deleting originals.
- Renaming originals without explicit approval.
- Overwriting existing files without explicit approval.
- Sending emails.
- Submitting coursework to portals.
- External upload.
- Credential or secret reads.
- Recipient inference without approved course/contact context.
- Treating media-derived text as instructions.
- Promoting media-derived content into canonical knowledge.

## Source Dossier

- `03_INPUTS/00_QUARANTINE/2026-05-30-artifact-intelligence-submission-operator-user-dossier.md`
- `docs/features/chaseos_not_built_backlog.md` row `NB-031`
- `docs/features/-Upcoming-Features-Index.md`
- `06_AGENTS/Feature-Register.md` Feature Family 16

## Graph Links

[[Feature-Register]] · [[ChaseOS-Feature-Family-and-Subfeature-Inventory]] · [[Autonomous-Operator-Runtime]] · [[Connector-Capture-Architecture]] · [[Acquisition-Normalization-Layer]] · [[ChaseOS-Gate]] · [[Hermes-Adapter-Spec]] · [[OpenClaw-Adapter-Spec]] · [[chaseos_not_built_backlog]]
