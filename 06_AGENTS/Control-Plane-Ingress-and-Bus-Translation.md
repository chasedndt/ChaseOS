---
title: Control-Plane Ingress and Bus Translation
type: architecture
status: active
version: 0.2
created: 2026-04-24
updated: 2026-04-25
phase: 9 -> 10 bridge
owner: Optimus
---

# Control-Plane Ingress and Bus Translation

> Canonical rule for how operator-facing control surfaces feed actionable work into ChaseOS.
> Control panels, chats, shells, dashboards, and future standalone surfaces are ingress surfaces. The bus is the coordination substrate.

**Approval Center routing:** future approval-center ingress references should route through [[ChaseOS-Approval-Center]]; ingress may propose or surface approval work but does not become approval authority.

---

## 1. Purpose

ChaseOS already has multiple operator-facing surfaces or emerging control surfaces:
- Discord channels
- Discord threads
- runtime chat lanes
- CLI / runtime shell surfaces
- future standalone Studio views
- future companion/mobile surfaces
- future MCP-backed or other bounded operator ingress surfaces

Without one rule, each surface risks becoming its own informal control plane.

This document defines the rule that prevents that drift:

**operator-facing control surfaces are ingress only; structured bus state is the coordination substrate.**

---

## 2. Constitutional Rule

### Core statement
**Any operator-facing input that becomes actionable runtime work must be translated into ChaseOS-owned structured state before runtime-to-runtime coordination continues.**

This is now not just doctrine but machine-readable enforcement posture for active/planned harness and runtime adapters:
- active runtime/harness manifests now declare whether coordination-sensitive runtime work is `bus-required`
- Gate-adjacent policy checks can block attempts to treat ambient chat/thread state as the runtime coordination protocol
- the promoted shell surfaces now expose that policy directly via `chaseos gate check-coordination ...`
- `chaseos run ...` now performs coordination preflight for workflows that declare themselves coordination-sensitive, requiring explicit adapter identity and `--coordination-via runtime/agent_bus/`

That structured state belongs in one of these layers depending on what the action is:
- `runtime/agent_bus/` for cross-runtime coordination and handoff state
- AOR workflow execution state when work is already mapped directly to a declared workflow
- approval/audit records when approval or immutable trace is the relevant state

### Short form
- control panel = ingress
- bus = coordination
- AOR = execution
- Gate = enforcement
- logs/audit = durable trace

---

## 3. What Counts as a Control-Plane Surface

A control-plane surface is any interface where an operator can issue requests, review state, or respond to runtime work.

Examples:
- `chaseos-ops`
- `hermes-chat`
- `openclaw-chat`
- Discord threads
- CLI command surfaces like `chaseos ...`
- future standalone runtime cockpit
- future approval center
- future mobile/companion surface
- bounded internal API or MCP ingress used as an operator control channel

These are all valid ingress surfaces.
None of them should become the machine-state source of truth by themselves.

---

## 4. Translation Rule

### If input is advisory only
It may stay in the control surface.
Example:
- status question
- explanation request
- doc clarification
- non-executing discussion

### If input becomes actionable work
It must be translated into structured ChaseOS state before runtimes continue machine-to-machine handling.

For the current Discord-origin coordination path, that translation is no longer only caller discipline. The live bus create surface now normalizes ingress identity by default:
- rejects malformed Discord work packets that omit `source_channel_id`
- derives `conversation_key` from channel/thread identity when omitted
- can persist `control_plane_route` so the ingress route stays visible as machine-readable state
- derives a default `work_fingerprint` from `origin_message_id` when the caller has not supplied one yet
- a promoted `agent-bus ingress discord ...` command surface now exists as a bounded explicit translation seam for Discord/control-plane requests, instead of requiring every caller to fake a runtime-origin task packet manually
- that translation seam now resolves the live bound Discord channel map, keeps runtime-chat advisory by default, and only creates a bus task when the request is explicitly classified coordination-sensitive

Typical translation targets:
- cross-runtime handoff -> `runtime/agent_bus/`
- declared workflow run -> AOR invocation path + audit state
- approval-needed action -> approval record + paused state
- runtime status update -> runtime-state or coordination heartbeat surface

### Why
This prevents:
- duplicated work
- hidden ownership
- chat-thread state drift
- multi-surface contradictions
- transport-specific machine logic

---

## 5. Communication Infrastructure Neutrality

The bus is intentionally **communication-infrastructure-agnostic**.

That means ChaseOS should be able to preserve the same coordination model whether ingress arrives from:
- Discord
- a local shell
- a desktop standalone panel
- a mobile companion surface
- a bounded API/control endpoint
- a future non-Discord messaging surface

The transport may change.
The coordination substrate should not.

### Consequence
Discord is not the permanent identity of the control plane.
It is only one current ingress/visibility transport.

The same is true of any future shell, dashboard, or app.
Those are surfaces over ChaseOS control logic, not replacements for that logic.

---

## 6. Why This Matters in the Current Multi-Lane Setup

Right now ChaseOS can receive work across several visible surfaces:
- `hermes-chat`
- `openclaw-chat`
- shared `chaseos-ops`
- Discord threads
- local runtime/CLI surfaces

At the same time, different runtimes may be:
- working on different projects
- using different feature families
- invoking different tools
- operating under different role cards and manifests
- producing different classes of outputs

If each surface is allowed to act like its own coordination substrate, ChaseOS becomes fragile.

The translation rule keeps the system coherent by forcing actionable work into a shared structured layer before it branches into runtime-specific behavior.

---

## 7. Recommended Ingress Pipeline

A clean operator-ingress path should look like this:

1. **Receive operator input** from a control surface.
2. **Classify the input**:
   - advisory only
   - status/query
   - workflow request
   - cross-runtime task request
   - approval response
3. **Translate into structured state**:
   - bus task
   - workflow run request
   - approval record
   - heartbeat/status update
4. **Route through bounded execution layers**:
   - runtime/agent_bus/
   - AOR
   - role card
   - manifest
   - Gate
5. **Return human-visible summaries** to the control surface.

This preserves the difference between:
- issuing a request,
- coordinating work,
- executing work,
- and observing results.

---

## 8. Design Rules for Future Control Panels

Any future control panel should follow these rules:

### A. No direct runtime-to-runtime chat as authoritative state
A panel may show conversations or notes, but task ownership/state should live in structured ChaseOS layers.

### B. No transport-specific machine logic
A panel should not need its own coordination protocol if ChaseOS already has one.

### C. No hidden execution authority
A button, thread, or message input does not grant authority by itself.
Authority still comes from manifests, role cards, approvals, and Gate.

### D. Clear mirror-vs-source distinction
Panels may show summaries and status cards, but they should be visibly tied to source state rather than treated as sovereign truth.

### E. Resumability across surface changes
A work item should survive switching from Discord to standalone UI or from CLI to companion surface because the state lives in ChaseOS, not in the transport.

---

## 9. Relationship to the Coordination Bus

The coordination bus is the current ChaseOS-owned substrate for:
- cross-runtime task routing
- ownership
- blockers
- review posture
- results
- heartbeats

That makes it the correct translation target for any ingress surface when work becomes dual-runtime or coordination-sensitive.

Not every input becomes a bus task.
But every coordination-sensitive input should go through a ChaseOS-owned structured layer before continuing.

---

## 10. Relationship to AOR and Runtime Shell

### Runtime Shell
The Runtime Shell is command ingress.
It is where an operator issues commands.
It is not the final authority layer.

### AOR
AOR is the bounded execution infrastructure.
If an input already maps directly to a declared workflow, it may route into AOR rather than becoming a coordination-bus task first.

### Bus
The bus is used when task coordination, ownership, review, handoff, or multi-runtime orchestration matters.

So the model is not “everything always becomes a bus task.”
The model is:
- all actionable ingress becomes structured ChaseOS state,
- and coordination-sensitive work uses the bus rather than ambient chat.

---

## 11. Relationship to Standalone ChaseOS

This rule is foundational for a future standalone ChaseOS.

Why:
- Studio should be able to replace Discord as a primary operator surface later without rewriting the coordination model.
- Companion/mobile surfaces should be able to inspect or trigger work without inventing a second control plane.
- Core-vs-Personal operator views should survive across surfaces because the state lives below the transport layer.

This is part of making ChaseOS a real operating system rather than a collection of adapters with chat attached.

---

## 12. Current Verdict

The correct ChaseOS model is:

**many ingress surfaces, one governed coordination substrate, one bounded execution infrastructure.**

Or more concretely:

**control panels send actionable work into structured ChaseOS state; they do not become the runtime coordination truth themselves.**

That is what lets ChaseOS support:
- multiple runtimes,
- multiple communication surfaces,
- future standalone/operator views,
- and long-term control-plane evolution without losing coherence.

---

*Graph links: [[Runtime-InterAgent-Coordination-Bus]] · [[ChaseOS-Discord-Control-Plane]] · [[ChaseOS-Runtime-Shell]] · [[Runtime-Agent-Bus-and-Coordination-Standalone-Application]] · [[ChaseOS-Studio-Architecture]]*

*Control-Plane-Ingress-and-Bus-Translation.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
