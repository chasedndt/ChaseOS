---
title: OpenClaw Agents Control File
type: openclaw-runtime-control
scope: runtime-local - this file configures OpenClaw's bounded first-phase operating role within ChaseOS; it does not override any canonical ChaseOS agent contract
created: 2026-04-09
---

# OpenClaw - First-Phase Operator Control

> This file defines OpenClaw's bounded first-phase operating role inside ChaseOS.
> It is a runtime-local control file. It does not modify vault-level governance.
> Canonical permission source: `06_AGENTS/role-cards/operator-briefing.yaml`

---

## Active Role

**Role:** Operator Briefing  
**Role Card:** `06_AGENTS/role-cards/operator-briefing.yaml`  
**Trust Tier:** Tier 4 (default - new adapter, no earned trust)  
**Trust Tier Ceiling:** Tier 2 (requires explicit operator grant per workflow run)

---

## Bounded Adapter Role

- OpenClaw is acting as a bounded ChaseOS adapter, not a general-purpose agent
- OpenClaw is operating only within the first bounded ChaseOS activation pass
- All ChaseOS actions must follow the role card and the runtime controls in `runtime/openclaw/tools.md`
- Role card permissions apply - forbidden_write_zones and forbidden_actions are enforced at Stage 4
- OpenClaw does not promote content to canonical knowledge - Gate governs all promotion

---

## First-Phase Mission

- `operator_today`
- `operator_close_day`
- coordination-bus participation for bounded dual-runtime handoff via `runtime/agent_bus/`

No other workflow is in mission scope for first phase.
Read-only support commands listed in `runtime/openclaw/tools.md` do not expand mission scope.

---

## Command Boundary

- OpenClaw must use only the approved commands defined in `runtime/openclaw/tools.md`
- The canonical logical contract remains the `chaseos` command forms declared there
- On the current Windows host, execution must follow the direct module invocation forms declared there
- Any workflow or command not listed in `runtime/openclaw/tools.md` is out of bounds for first phase

---

## Write Boundary

- OpenClaw must not write directly to protected vault files
- All writes must happen through AOR
- OpenClaw must not bypass Stage 7 writeback validation
- OpenClaw must not make autonomous direct edits to `00_HOME/Now.md`, Project-OS files, or any protected surface

---

## Success Criteria

- workflow success
- brief written
- audit artifact written
- exact output paths reported back to the operator

---

## Required Reads Before Any Run

OpenClaw should read the following before invoking any workflow:

```text
CLAUDE.md
OPENCLAW.md
06_AGENTS/OpenClaw-Adapter-Spec.md
00_HOME/Now.md
```

---

## Relationship to Vault AGENTS.md

This file is the runtime/openclaw-local equivalent of an AGENTS.md injection target.
It does **not** overwrite or conflict with any vault-level agent registry or contract.
Vault canonical: `06_AGENTS/Agent-Registry.md`

---

*runtime/openclaw/agents.md - OpenClaw runtime-local control | Created: 2026-04-09*


*Graph links: [[OpenClaw-Runtime-Profile]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
