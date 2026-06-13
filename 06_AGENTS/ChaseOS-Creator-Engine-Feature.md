---
date: 2026-05-21
runtime: Codex
type: feature-node
status: PARTIAL / PASSES 1-10 VERIFIED / APPROVAL REQUEST WRITER READY / NOT MVP NAV
parent_families:
  - ChaseOS VentureOps
  - Content
  - SiteOps
studio_surface: none primary yet
---

# ChaseOS Creator Engine Feature

The ChaseOS Creator Engine is a partial governed media and creator-output subsystem.

It is not currently a primary Studio MVP page and should not be treated as product-complete. Runtime-local passes 1-10 are implemented and verified; downstream execution, Studio integration, provider/media adapters, publishing, timeline execution, and canonical memory promotion remain blocked.

## Verified Runtime Scope

- Pass 1: runtime skeleton, models, JSON schemas, job store, path policy, adapter protocol.
- Pass 2: provided-transcript intake into runtime-local Creator Engine jobs.
- Pass 3: `creator ingest` CLI surface.
- Pass 4: dry-run manual source metadata and no-secret fixture smoke.
- Pass 5: reference-only manual media adapter.
- Pass 6: media/transcript job linking.
- Pass 7: runtime-local context-pack JSON/Markdown foundation.
- Pass 8: deterministic generation artifact stubs: cleaned transcript, script scaffold, voiceover scaffold, captions, edit plan, social pack, upload metadata, content memory card, generation manifest.
- Pass 9: read-only approval packet preview.
- Pass 10: exact-digest create-only approval request writer.

## Code-Observed / Log Evidence Required

- `creator approval-consumption-dry-run` appears in `runtime/cli/command_contract.json`.
- No dedicated Creator Engine Pass 11 build/history log was confirmed during the 2026-05-21 deep reconciliation.

## Remaining Planned / Blocked Scope

- approval decision/grant writer
- approval consumption and exact-once execution marker
- final content generation via provider/model calls
- TTS voiceover generation
- real transcription backend
- media copy/probe/transcode through FFmpeg or equivalent
- Studio panel integration
- AOR workflow wiring
- Agent Bus dispatch
- Hermes/OpenClaw callable tools under policy
- timeline execution
- upload/publish
- SIC/RAG live query integration
- canonical memory promotion

## Future Scope

- Recordly/OpenScreen bridge
- timeline state reading
- region CRUD
- frame capture
- auto-short generation
- auto-upload after approval
- feedback loop

## Explicit Non-Scope

- OpenHuman active runtime integration
- fully autonomous publishing
- brittle UI automation as the primary integration
- trusting transcripts without review
- treating deterministic draft stubs as final generated content

## Canonical Sources

- `docs/features/chase-os-creator-engine-spec.md`
- `docs/plans/chase-os-creator-engine-implementation-plan.md`
- `runtime/creator_engine/`
- `runtime/cli/command_contract.json`
- `07_LOGS/Build-Logs/2026-05-20-ChaseOS-creator-engine-pass1-skeleton-schemas.md`
- `07_LOGS/Build-Logs/2026-05-20-ChaseOS-creator-engine-pass10-approval-request-writer.md`
- `99_ARCHIVE/Documentation-History/2026-05-20_creator-engine-pass10-approval-request-writer.md`
- `docs/audits/2026-05-21_feature_family_deep_reconciliation.md`

## Graph Links

[[VentureOps-Architecture]] [[ChaseOS-SiteOps]] [[ChaseOS-Feature-Family-and-Subfeature-Inventory]]
