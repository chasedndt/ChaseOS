---
title: Companion Surface Mobile/Tablet Architecture
type: architecture
status: SEEDED / PHASE 10 SURFACE CONTRACT / NOT LIVE
phase: Phase 10 surface-side OSRIL / Phase 11 Chat companion UX
created: 2026-05-12
updated: 2026-05-12
knowledge_class: architecture
---

# Companion Surface Mobile/Tablet Architecture

## Purpose

The Companion Surface is the mobile/tablet/browser operator surface for ChaseOS. It lets the operator view active briefs, inspect pending approvals, send bounded approval responses, trigger declared capture/workflow requests, and check runtime status from a phone, tablet, or lightweight browser view.

This surface is a ChaseOS operator surface. It is not a new control plane, not a runtime identity, not a canonical memory store, and not an authority grant. Companion personality/status is presentation state only; every action routes through the same ChaseOS authority chain used by Studio and the CLI.

## Current Repo Truth

Current implementation footholds already exist in the Phase 11 Chat companion lane:

- `runtime/studio/phase11_chat_companion_status.py` builds authority-neutral companion status cards for Hermes, OpenClaw, and Archon.
- `runtime/studio/phase11_chat_companion_selection_preview.py` builds digest-bound approval previews for companion selection.
- `runtime/studio/phase11_chat_companion_selection_queue_write_readiness.py` previews future approval-queue writes without writing artifacts.
- `runtime/studio/phase11_chat_companion_selection_queue_write_execution.py` can create a pending approval artifact for companion selection while preserving no target selection write, no approval consumption, no runtime control, and no canonical mutation.
- `runtime/studio/phase11_chat_companion_selection_approval_consumption_readiness.py` inspects companion-selection approvals and previews exact-once consumption posture while still blocking target writes.

Those modules prove that companion identity/status can be surfaced without granting authority. They do not yet provide a mobile/tablet operator surface for briefs, approvals, capture triggers, or live status.

## Target Surfaces

| Surface | Operator use | Required backend | Authority posture |
|---|---|---|---|
| Mobile brief viewer | Read latest operator briefs, workflow outputs, and selected status packets | read-only brief/output feed over approved paths | read-only; no promotion or mutation |
| Approval inbox | Review pending Studio/AOR/Gate approvals and submit approve/deny responses | approval queue read plus governed response writer | approval response only; exact target action still handled by AOR/Gate/StudioService |
| Capture trigger panel | Submit capture requests such as URL/text/file-intent packets | capture request preview/approval path | no direct connector or file ingestion; writes only queued request artifacts until approved |
| Runtime status cards | Show runtime health, companion status, OSRIL sessions, waiting approvals, and dispatch state | OSRIL/runtime-state read APIs | read-only status; no lifecycle mutation |
| Companion selector | Pick preferred companion/runtime presentation lane | existing companion selection approval chain | selection is approval-gated presentation state; no runtime authority change |
| Push/notification layer | Notify operator of approval-needed, workflow-failed, or brief-ready events | gateway/mobile delivery adapter | delivery is output-only by default; responses still enter governed endpoints |

## System Boundary

```text
mobile/tablet/browser companion
  -> authenticated local/LAN/approved gateway surface
  -> StudioAPI / StudioService preview + approval queue
  -> AOR workflow registry / OSRIL session + event APIs
  -> Gate checks for any write or approval consumption
  -> approved workflow/capture/runtime handler
  -> audit/writeback lanes declared by workflow and role card
```

The companion never writes directly to `02_KNOWLEDGE/`, runtime manifests, role cards, provider config, credential stores, Agent Bus tasks, or canonical docs. It can display those surfaces only through explicit read contracts, and any mutation must become a governed request that another ChaseOS layer evaluates.

## Authority Ceiling

The companion surface may:

- Read bounded operator-facing summaries, briefs, status packets, and pending approval metadata.
- Render companion/runtimes as personality/status cards with visible authority ceilings.
- Create approval-response intents only through the approved StudioService/AOR/Gate chain.
- Create capture or workflow request previews only when the target workflow/capture path is declared.
- Show proof that an approval/capture/workflow request has been queued, denied, consumed, or completed.

The companion surface must not:

- Execute workflows directly.
- Consume approvals directly.
- Mutate companion selection state without the approval chain.
- Promote to canonical knowledge.
- Write protected files.
- Dispatch browsers, connectors, shells, providers, or runtime lifecycle actions directly.
- Treat mobile push messages, chat text, browser URLs, or gateway payloads as trusted instructions.
- Use companion personality, avatar, selected runtime, or trust-tier display fields as authorization.

## Privacy and Security Model

### Device/session boundary

- Default local development mode should be localhost-only or operator-approved LAN exposure.
- Any remote/mobile exposure needs an explicit auth boundary before launch: operator identity, session expiry, CSRF-style response binding, and revocation.
- Mobile session state is runtime-local and ephemeral by default. Durable records belong in the relevant approval, audit, brief, capture, or build-log lanes.

### Transport trust

- All mobile/tablet/gateway inputs are Tier 4 untrusted data until translated into a declared ChaseOS request schema.
- Push notifications are summaries/links/status signals, not instructions to execute.
- Approval responses must bind to exact approval IDs, action digests, target paths, and expected statuses to prevent replay or confused-deputy behavior.

### Data minimization

- Mobile cards should show minimal operator-needed context: title, runtime, authority, status, digest, target family, and safe excerpts.
- Raw secrets, credential paths, provider tokens, full logs, and large captured sources must not be sent to mobile surfaces.
- Gateway logs should store summaries/artifact paths, not full sensitive payloads.

## Backend Dependency Map

| Dependency | Owner layer | Minimum proof before live mobile/tablet use |
|---|---|---|
| Gateway/mobile delivery | Phase 9-and-below adapter/gateway layer | delivery adapter can send output-only cards without accepting ambient commands |
| Authentication/session boundary | Phase 10/Phase 9 security boundary | localhost/LAN/remote mode has explicit auth, expiry, replay prevention, and revocation story |
| Approval responses | AOR/OSRIL/StudioService/Gate | mobile response path writes immutable approval-response/apply markers and preserves exact-once handling |
| Capture triggers | Capture/acquisition + Gate | mobile capture request becomes a preview/approval packet before connector/file ingestion |
| Credentials | Credential boundary | no raw credential read/write from companion; provider/gateway secrets stay outside UI payloads |
| Runtime dispatch | AOR workflow registry | companion-triggered workflow requests resolve only to active declared workflows and role-card ceilings |
| Canonical writes | Gate/writeback layer | mobile never writes canonical truth directly; approved workflows produce declared outputs only |
| Push notifications | Gateway/output lanes | notification output is redactable, rate-limited, and trace-linked to source approval/session/brief IDs |
| Offline/reconnect | OSRIL/session layer | stale mobile actions are rejected unless approval/session digest still matches current state |

## Minimum Product Slices

### Slice A — Read-only companion dashboard

- Render latest companion status cards from `phase11_chat_companion_status.py`.
- Show selected runtime presentation state and authority ceiling.
- Show read-only OSRIL/session/approval counts where existing APIs can provide them.
- No writes, no approvals, no capture triggers, no remote network exposure.

Acceptance criteria:
- Status cards render on desktop browser and narrow mobile viewport.
- Authority ceiling text is visible for every runtime/companion card.
- Static QA proves no approval artifact, target write, runtime dispatch, provider call, or canonical mutation occurs.

### Slice B — Brief viewer

- Read bounded operator briefs and selected workflow outputs.
- Show safe excerpts and artifact paths, not full raw logs/secrets.
- Preserve source family distinctions: Operator Briefs, Agent Activity, Build Logs, Trace Reports, Promotion Records.

Acceptance criteria:
- Mobile viewport shows brief title, generated time, runtime/source, authority posture, and safe excerpt.
- No canonical or source-pack mutation occurs.
- Missing brief/output directories degrade to empty-state cards.

### Slice C — Approval inbox preview

- Display pending approval metadata with action digest, target family, authority ceiling, and response options.
- Preview the exact response envelope without consuming approval.
- Require explicit operator confirmation before writing any response artifact.

Acceptance criteria:
- Approval cards bind to approval ID + action digest + target path.
- Preview mode writes nothing.
- Confirmed mode routes through existing AOR/OSRIL/StudioService/Gate response path, not direct file writes.

### Slice D — Capture trigger preview

- Let the operator draft a URL/text/file-intent capture request from mobile.
- Normalize it into a declared capture request preview or approval packet.
- Do not run connectors or ingest files until the governed capture path approves it.

Acceptance criteria:
- Input is treated as untrusted and prompt-injection scanned.
- Capture request preview shows target workflow/capture family and blocked/live status.
- No connector/network/file ingestion occurs from the companion surface itself.

### Slice E — Gateway/mobile delivery proof

- Deliver output-only cards through an approved gateway/mobile path.
- Responses, if allowed, return only as structured approval/capture request envelopes.

Acceptance criteria:
- Delivery proof redacts sensitive payloads.
- Response proof rejects stale/mismatched digest submissions.
- Audit links source notification to approval/session/brief IDs.

## Implementation Handoff

Recommended next implementation order:

1. Add a read-only `runtime/studio/phase10_companion_surface_status.py` aggregator over existing companion status, OSRIL counts, approval counts, and brief/output folder presence.
2. Add a focused test proving the aggregator is read-only and lists blockers for missing mobile auth/gateway/write-response paths.
3. Mount the aggregator in Studio as a responsive/narrow panel or static HTML proof before any network/mobile delivery.
4. Add a mobile brief-view contract over approved output families.
5. Only after auth/session policy exists, add approval-response preview and exact response handoff through the existing governed chain.
6. Treat gateway/mobile delivery and capture triggers as later Phase 9-and-below dependency tasks, not as Phase 10 authority shortcuts.

## Open Blockers

- No dedicated mobile/tablet auth/session boundary exists yet.
- No approved remote/mobile gateway delivery path exists yet.
- Approval response submission from mobile must be bound to existing OSRIL/AOR/StudioService response semantics before live use.
- Capture triggers require a governed request/approval packet path before connector/file ingestion.
- Runtime dispatch from mobile remains blocked until it resolves only to active declared workflows and role-card ceilings.
- Canonical writeback remains entirely downstream of Gate and declared workflow outputs.

## Related Documents

- [[Operator-Surface-Runtime-Interaction]]
- [[ChaseOS-Phase11-Architecture]]
- [[ChaseOS-Studio-Architecture]]
- [[ChaseOS-Runtime-Shell]]
- [[ChaseOS-Approval-Center]]
- [[HERMES]]
- [[Agent-Activity-Index]]

## Agent Note — Optimus

Optimus seeded this as a Phase 10 companion-surface architecture lane over live Phase 11 companion-status/selection truth. The work is testable now at the read-only contract/proof layer, but mobile/tablet live authority is intentionally blocked until auth, gateway delivery, approval-response, capture-trigger, runtime-dispatch, and Gate writeback dependencies are implemented by the proper lower layers.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
