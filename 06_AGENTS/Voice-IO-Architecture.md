---
title: Voice I/O Architecture
type: architecture
status: phase10-contract-seeded-no-live-provider
version: 0.1
created: 2026-05-12
updated: 2026-05-12
phase: Phase 10 Studio / OSRIL surface contract over Phase 9 runtime governance
knowledge_class: canonical-state
---

# Voice I/O Architecture

> Voice I/O is a provider-neutral Phase 10 operator-experience lane for ChaseOS Studio and OSRIL. It can capture spoken intent and render spoken briefings, but it is not a runtime dispatcher, not an approval authority, not a canonical memory source, and not a credential/provider activation path.

## Current Truth

This pass seeds the architecture only. No STT/TTS provider is wired, no credentials are read, no microphone capture is enabled, no browser AudioContext is mounted, no transcript store is created, no workflow dispatch path is added, and no canonical writeback route is activated.

Voice belongs above the already-live OSRIL/AOR substrate:

1. operator speaks into a Studio/OSRIL surface;
2. the surface produces an untrusted `voice_intent_candidate` object;
3. ChaseOS normalizes it into structured intent for review;
4. any action routes through existing Workflow Registry, OSRIL approval, Agent Bus, and Gate seams;
5. transcripts and audio artifacts stay ephemeral or audit-scoped unless a separate governed persistence workflow exists.

## Design Goals

- Keep speech providers interchangeable: local, browser-native, hosted API, and future model-backed STT/TTS implementations share one contract.
- Preserve trust tier: spoken input is Tier 4 untrusted intent until structured, reviewed, and approved.
- Make transcripts auditable without turning them into canonical truth.
- Support spoken briefings and status readouts without granting TTS any command channel.
- Give Studio a clear future module boundary without forcing provider credentials, live browser audio, or runtime dispatch into this architecture pass.

## Non-Goals

This architecture does not authorize:

- live microphone recording;
- provider/model calls;
- credential setup or provider selection;
- workflow execution from a voice phrase;
- OSRIL approval execution from spoken confirmation alone;
- Agent Bus writes;
- canonical note writes or knowledge promotion;
- ambient always-listening behavior;
- biometric identification or speaker verification;
- long-term raw audio retention.

## Core Boundary

Voice is an ingress/egress experience lane.

| Direction | Allowed first contract | Forbidden interpretation |
|---|---|---|
| Ingress / STT | produce structured, untrusted intent candidates for display/review | direct commands, direct approvals, canonical memory |
| Egress / TTS | read approved text/status/brief payloads aloud | hidden task execution, persuasion layer, approval bypass |
| Transcript | audit/evidence artifact subject to retention rules | canonical truth or source-note promotion by default |
| Provider adapter | STT/TTS implementation behind a common interface | control plane owner or credential authority |

## Minimal Object Model

### `voice_session`

A bounded runtime-local session object that connects Studio UI state to OSRIL session context.

Required fields:

- `voice_session_id`
- `surface_id` such as `studio.native_shell.voice_panel`
- `operator_id` or `operator_label`
- `osril_session_id` when attached to an active OSRIL session
- `runtime_id` when attached to a runtime view
- `started_at`
- `state`: `idle`, `listening`, `transcribing`, `review_pending`, `speaking`, `error`, `closed`
- `retention_mode`: `ephemeral`, `audit_text_only`, or `explicit_artifact`
- `trust_tier`: default `Tier 4`

### `voice_intent_candidate`

The first structured output of STT. It is a proposal, not an action.

Required fields:

- `candidate_id`
- `voice_session_id`
- `transcript_text`
- `transcript_confidence`
- `transcript_provider_ref` as an opaque provider/runtime label, not a secret
- `language`
- `captured_at`
- `trust_tier`: `Tier 4`
- `normalized_intent`: optional structured parse such as `view_status`, `draft_task`, `request_approval_review`, or `unknown`
- `target_surface`: optional display target only
- `requires_operator_confirmation`: always true before action routing
- `blocked_authority`: explicit list of denied direct effects

Default blocked authority:

```yaml
blocked_authority:
  - workflow_dispatch
  - approval_grant
  - approval_consumption
  - agent_bus_write
  - provider_call_outside_stt
  - connector_call
  - canonical_writeback
  - protected_file_write
  - credential_read_or_mutation
```

### `voice_output_request`

The TTS-side object for spoken output.

Required fields:

- `output_request_id`
- `surface_id`
- `source_event_ref` or `source_artifact_ref`
- `text_to_speak`
- `voice_profile_ref` as a non-secret label
- `allowed_output_class`: `status_readout`, `briefing_excerpt`, `approval_prompt_readout`, or `error_readout`
- `must_match_visible_text`: true for approval prompts and decisions
- `retention_mode`

TTS may speak only text already visible to the operator or generated by a governed read-only surface. It must not synthesize hidden instructions or summarize approval consequences differently from the visible approval object.

## Provider-Neutral Adapter Plan

Future code should keep provider coupling behind small adapters, for example:

```text
runtime/studio/voice/
  contract.py              # dataclasses / schemas for session, candidate, output request
  readiness.py             # read-only provider/config readiness, no secret display
  transcript_policy.py     # retention + redaction helpers
  stt_adapters/
    browser_web_speech.py  # browser-native candidate adapter, no server credential
    local_whisper.py       # local/offline candidate adapter if installed
    hosted_api.py          # hosted provider boundary, credential by configured provider only
  tts_adapters/
    browser_speech.py
    local_tts.py
    hosted_api.py
```

All adapters should return common objects and capability metadata. Provider modules should not import AOR dispatch, Gate mutation, Agent Bus mutation, canonical write helpers, or credential mutation helpers.

## Studio / Browser Audio Layer

The future Studio surface may expose:

- push-to-talk or explicit click-to-record first, not ambient always-on listening;
- visible listening indicator;
- transcript preview before routing;
- confidence and source/provider metadata;
- explicit discard / edit / route controls;
- TTS queue with visible text and interrupt/stop controls;
- optional AudioContext analyser for visual feedback only.

The AudioContext/analyser seam is UI chrome. It consumes audio playback state and must not become an evidence source, biometric classifier, or authority signal.

## Trust-Tier Handling

Spoken input is untrusted because transcription can be wrong, spoofed, clipped, or contextless. The default posture is:

| Artifact | Trust posture |
|---|---|
| raw audio buffer | Tier 4, ephemeral unless explicit evidence capture is approved |
| transcript text | Tier 4 operator-input candidate until confirmed |
| normalized intent | proposal only; cannot execute |
| operator-edited transcript | still non-canonical; may be clearer user intent |
| approved OSRIL response | governed approval record only after existing OSRIL approval path accepts it |
| spoken briefing output | derived display output; not source truth |

Voice does not lower the approval bar. A spoken “yes” may populate an approval-response draft, but the operator must still confirm the exact visible approval object through OSRIL’s existing response/record path before any resume or execution effect occurs.

## Transcript, Retention, and Privacy Policy

Default retention should be minimal:

1. raw audio buffers are discarded after transcription unless an explicit evidence workflow is approved;
2. failed/low-confidence transcripts may be discarded or kept only as redacted diagnostic snippets;
3. confirmed intent candidates may be written to audit-scoped logs only when they support a later governed action;
4. transcript artifacts must carry source surface, timestamp, provider label, confidence, retention mode, and redaction status;
5. transcript artifacts must not be promoted into `02_KNOWLEDGE/` without the same Gate/provenance checks as any other source.

Sensitive capture protections:

- visible recording state;
- no background microphone activation;
- easy discard before persistence;
- redaction before any durable log;
- no credential capture persistence;
- no speaker identity inference by default.

## OSRIL / AOR Routing

Voice ingress can produce only reviewable intent candidates. The allowed routing sequence is:

```text
Voice surface -> STT adapter -> voice_intent_candidate -> visible Studio review
  -> structured ChaseOS intent preview -> existing OSRIL / Agent Bus / Workflow Registry / Gate path
```

Required proof before any future live voice action path:

- candidate object shows `trust_tier: Tier 4`;
- `requires_operator_confirmation: true` is preserved;
- blocked authority list includes dispatch, approval grant/consumption, Agent Bus write, and canonical writeback;
- the final routed action is an existing declared workflow/action type;
- OSRIL/Gate records, not the voice adapter, decide execution.

## Provider and Config Readiness

A future read-only readiness surface may report:

- STT providers available vs unavailable;
- TTS providers available vs unavailable;
- local browser API availability;
- whether credentials are configured, as boolean presence only;
- network-required vs local-only provider posture;
- cost/rate/latency warnings;
- privacy posture such as `local_only`, `hosted_api`, or `browser_native`.

It must not display secrets, mutate provider settings, install packages, start daemons, switch providers, or call providers during a passive readiness check.

## No-Dispatch / No-Canonical-Mutation Proof Requirements

Before a future implementation can be treated as safe, focused tests should prove:

- STT adapters can return candidate objects without importing or calling AOR execution;
- TTS adapters can render queued visible text without creating command events;
- transcript policy defaults to ephemeral raw audio;
- voice candidates are always Tier 4 before operator confirmation;
- spoken approval cannot consume OSRIL approval records without the existing explicit approval path;
- static Studio QA over the real vault reports no markdown writes, no approval artifacts, no provider calls in read-only mode, no Agent Bus writes, and no canonical writeback;
- readiness checks expose only booleans and provider labels, not secrets.

Suggested future focused slices:

1. `runtime/studio/voice/contract.py` plus tests for object shapes and blocked authority defaults.
2. `runtime/studio/voice/readiness.py` with no-secret provider/config posture tests.
3. `runtime/studio/voice/transcript_policy.py` with retention/redaction tests.
4. Studio voice panel preview that renders candidate objects read-only.
5. OSRIL handoff preview that turns a confirmed candidate into a non-executing action/approval preview.

## Phase 9-and-Below Dependencies

Voice architecture depends on lower layers for any live effects:

- provider credential/call governance;
- explicit runtime dispatch contracts;
- OSRIL approval response recording;
- Gate runtime-operation policy for any side-effect path;
- transcript persistence and retention policy;
- Agent Activity/audit routing;
- canonical promotion/writeback route if transcripts are ever promoted.

Until those dependencies exist and pass focused validation, Voice I/O remains a surface contract and experience plan only.

## ChaseOS Alignment

Voice I/O strengthens the ChaseOS operating-system model by making the operator interface more natural without weakening the OS boundary. The voice layer captures intent, presents it back to the operator, and routes only structured, confirmed objects into existing governed runtime paths. The control plane remains ChaseOS; providers remain adapters; Studio remains the product shell; OSRIL remains the runtime interaction substrate; Gate remains the authority boundary.

## References

- [[Operator-Surface-Runtime-Interaction]]
- [[ChaseOS-Studio-Architecture]]
- [[ChaseOS-Studio-Phase10-Implementation-Tracker]]
- [[ChaseOS-Gate]]
- [[Trust-Tiers]]
- [[Acquisition-Surface-Map]]
- [[Agent-Activity-Index]]
- [[Vault-Map]]
