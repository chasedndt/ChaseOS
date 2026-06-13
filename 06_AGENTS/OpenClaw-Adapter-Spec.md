---
title: OpenClaw Adapter Specification
type: adapter-spec
status: LIVE — OpenClaw installed and operational on this machine; active bounded runtime adapter lane; operator_today, operator_close_day, and graph_hygiene executed through OpenClaw → chaseos run → AOR path; Discord transport operational; scheduled execution proven through OpenClaw cron/control plane; AOR writeback and audit verified
created: 2026-04-09
version: 1.2
conforms_to: Execution-Adapter-Standard.md
---

# OpenClaw Adapter Specification

> Runtime contract for OpenClaw Agent operating as a ChaseOS Phase 9 bounded operator runtime adapter.
> This document is the machine-readable governance contract. The positioning document is `OPENCLAW.md`.
> OpenClaw is the **active live bounded runtime adapter lane** for this machine as of 2026-04-15.

---

## 1. Adapter Identity

| Field | Value |
|-------|-------|
| **Adapter ID** | `openclaw` |
| **Adapter class** | Persistent operator runtime |
| **Provider** | OpenClaw (open-source operator agent runtime) |
| **Platform** | Windows native (Node 24); WSL2 optional |
| **Trust Tier ceiling** | Tier 2 (with explicit operator grant per workflow) |
| **Trust Tier default** | Tier 4 (new adapter, no earned trust) |
| **Activation status** | LIVE — OpenClaw installed and operational; bounded execution proven; Discord transport operational; scheduled execution proven via OpenClaw cron; 2026-04-15 |
| **Peer lane** | Hermes (active bounded Discord runtime lane with narrower workflow breadth; see HERMES.md) |

---

## 2. Execution Surface

OpenClaw's execution surface within ChaseOS:

| Surface | Status | Notes |
|---------|--------|-------|
| `chaseos run operator_today` | Permitted first | Must route through AOR pipeline |
| `chaseos run operator_close_day` | Permitted first | Must route through AOR pipeline |
| `chaseos run sbp_strikezone_digest` | Permitted for declared SBP workflow | AOR manifest-bounded; vault writeback limited to `07_LOGS/SBP-Runs/`; external delivery is not a general OpenClaw grant |
| `chaseos runtime daemon --runtime openclaw --daemon-interval N` | Permitted operator-controlled runtime loop | Starts OpenClaw's coordination-watch loop for live Agent Bus heartbeat/claim/dispatch/result handling; does not expand OpenClaw beyond declared workflow handlers or Gate/AOR boundaries |
| `chaseos intake ls` / `dedup-stats` | Permitted read-only | Audit only |
| `chaseos capture ...` | Deferred | Requires explicit workflow declaration |
| Direct vault file write | Forbidden first phase | Only via AOR Stage 7 writeback |
| Shell command execution | Not authorized as ambient ChaseOS authority | Host-level shell capability is a risk boundary, not a ChaseOS permission. ChaseOS-governed work must route through declared AOR/Gate surfaces or an explicit operator/session grant. |
| External connector invocation | Forbidden first phase | Must be declared in AOR manifest |

---

## 3. Injected File Governance

OpenClaw injects workspace control files. ChaseOS maps them as follows:

| OpenClaw file | Scope in ChaseOS | Rule |
|--------------|------------------|------|
| `SOUL.md` | OpenClaw runtime-local only | Must NOT overwrite ChaseOS `SOUL.md`. OpenClaw soul file goes in `runtime/openclaw/soul.md` or equivalent runtime-local path. |
| `AGENTS.md` | Maps to active role card | Should reference `06_AGENTS/role-cards/operator-briefing.yaml` for first activation. Does not grant new permissions. |
| `TOOLS.md` | Maps to permitted chaseos CLI toolset | First phase: `chaseos run`, `chaseos intake ls/dedup-stats`. Additional tools require AOR manifest declaration. |

**Governing rule:** OpenClaw injected files configure OpenClaw's runtime. They do not override ChaseOS canonical files.

---

## 4. Permission Envelope — First Phase

### 4.1 Read Allowlist

Paths OpenClaw may read in the first bounded activation:

```
CLAUDE.md
OPENCLAW.md
06_AGENTS/OpenClaw-Adapter-Spec.md
00_HOME/Now.md
01_PROJECTS/ChaseOS/ChaseOS-OS.md
01_PROJECTS/TradingSystems/TradingSystems-OS.md
01_PROJECTS/StrikeZone/StrikeZone-Crypto-OS.md
01_PROJECTS/University/Degree-OS.md
07_LOGS/Build-Logs/
07_LOGS/Operator-Briefs/
07_LOGS/Agent-Activity/
runtime/aor/
runtime/workflows/registry/
06_AGENTS/role-cards/
```

All other vault paths are **not included** in first-phase read scope unless added by explicit operator grant.

### 4.2 Write Allowlist (Via AOR Only)

Paths OpenClaw may write to — only via AOR Stage 7 bounded writeback:

```
07_LOGS/Operator-Briefs/
07_LOGS/Agent-Activity/
07_LOGS/SBP-Runs/
```

Direct writes (not via AOR) to any vault path are **not permitted** in the first phase, even though OpenClaw has host-level filesystem access.

### 4.3 Forbidden Surfaces

Regardless of host access, OpenClaw must not write to these surfaces:

```
SOUL.md
CLAUDE.md
00_HOME/Principles.md
00_HOME/Operating-System.md
00_HOME/Assistant-Contract.md
00_HOME/Now.md
README.md
PROJECT_FOUNDATION.md
ROADMAP.md
FORKING.md
06_AGENTS/Agent-Control-Plane.md
06_AGENTS/Permission-Matrix.md
06_AGENTS/Trust-Tiers.md
06_AGENTS/Handoff-Protocol.md
01_PROJECTS/
02_KNOWLEDGE/
03_INPUTS/
06_AGENTS/ (except runtime-local output paths)
runtime/ (except via AOR writeback)
.claude/
.venv/
```

### 4.4 Forbidden Actions

| Action | Status |
|--------|--------|
| Canonical knowledge promotion | Forbidden — Gate governs all promotion |
| Protected file modification | Forbidden — even with host access |
| Multi-repo access | Forbidden first phase |
| External connector invocation (network) | Forbidden first phase without AOR manifest |
| Credential access | Forbidden — OpenClaw must not read `.env` or `secrets/` |
| Autonomous Now.md updates | Forbidden — operator-updated only |
| Autonomous project OS file edits | Forbidden first phase |

---

### 4.5 Host Privilege Boundary

OpenClaw's host-level capability does not become ChaseOS authority. Any ChaseOS-governed shell, filesystem, connector, schedule, delivery, or writeback action must still be declared in the active manifest/tool contract, pass the relevant AOR/Gate checks, and produce audit evidence.

The current hardening verifier is `runtime/adapters/runtime_governance.py`. It validates OpenClaw/Hermes adapter manifests, Hermes shadow config, OpenClaw bus capabilities, shared Tier 2 ceilings, promotion blocks, external-side-effect blocks, denied write targets, and bus-required coordination.

---

## 5. Audit Requirements

Every OpenClaw execution that touches ChaseOS must produce:

| Artifact | Location | Rule |
|----------|----------|------|
| AOR audit JSON | `07_LOGS/Agent-Activity/YYYYMMDD-HHMMSS__<workflow>__<audit_id[:8]>.json` | Written by AOR Stage 8; immutable after creation |
| Operator brief (if operator workflow) | `07_LOGS/Operator-Briefs/YYYY-MM-DD-<workflow>.md` | Written by AOR Stage 7 |
| No silent execution | Applies always | Every ChaseOS-governed action is logged |

---

## 6. Activation Checklist

First bounded OpenClaw activation — COMPLETE as of 2026-04-15:

- [x] Install OpenClaw on this machine (Node 24, Windows native) — **DONE 2026-04-15**
- [x] Configure ChaseOS vault root path in OpenClaw workspace settings — **DONE 2026-04-15**
- [x] Create `runtime/openclaw/agents.md` — references `operator-briefing` role card — **DONE 2026-04-09**
- [x] Create `runtime/openclaw/tools.md` — declares permitted chaseos CLI toolset — **DONE 2026-04-09**
- [x] Create `runtime/openclaw/soul.md` — runtime-local redirect; isolation rule documented — **DONE 2026-04-09**
- [x] Confirm `SOUL.md` injection isolation — documented in `soul.md` + Gate write guard enforces — **DONE 2026-04-09**
- [x] AOR path verified independently: `operator_today` + `operator_close_day` ran clean via AOR; audit + briefs written — **DONE 2026-04-09**
- [x] `chaseos run operator_today` invoked via OpenClaw → audit JSON written → brief written — **DONE 2026-04-15**
- [x] `chaseos run operator_close_day` invoked via OpenClaw → clean close note produced — **DONE 2026-04-15**
- [x] `chaseos run graph_hygiene` invoked via OpenClaw → proposal-only report produced — **DONE 2026-04-15**
- [x] Discord transport/control surface operational — **DONE 2026-04-15** (after channel config fix)
- [x] Scheduled jobs created in OpenClaw cron/control plane → scheduled execution proven — **DONE 2026-04-15**
- [x] Record: first bounded governance pass in `07_LOGS/Agent-Activity/` + build log — **DONE 2026-04-09**
- [x] Coordination daemon surface exists for OpenClaw — `chaseos runtime daemon --runtime openclaw --daemon-interval N` — **DONE 2026-05-17**

**Schedule-source sync COMPLETE (2026-04-21):** ChaseOS-native schedule intent is built (`runtime/schedules/`). OpenClaw must derive its cron config from `runtime/schedules/` using `chaseos schedule export --adapter openclaw`. The bridge contract is in `runtime/openclaw/schedule_bridge.md`.

---

## 7. Trust Tier Progression

OpenClaw starts at Tier 4 (new adapter, unproven) and may progress to Tier 2 ceiling:

| Stage | Tier | Condition |
|-------|------|-----------|
| Default | Tier 4 | No earned trust; new adapter |
| Read + AOR invoke | Tier 3 | Operator grants explicit `chaseos run` permission scope |
| Full operator-briefing scope | Tier 2 ceiling | AOR manifest + role card enforced; multiple confirmed runs |
| Scheduled-briefing scope | Tier 2 ceiling | Declared SBP workflow manifests only; vault output limited to `07_LOGS/SBP-Runs/` |
| Beyond operator/scheduled briefing | Not yet | Requires additional explicit grant per workflow class |

Tier ceiling = Tier 2. OpenClaw may not exceed Tier 2 regardless of operator grants.

---

## 8. Relationship to Other Adapters

| Adapter | Status | Notes |
|---------|--------|-------|
| Claude / Anthropic lane (CLAUDE.md) | Active — primary | Session-based; Tier 2; reference implementation |
| Hermes / Optimus | Active bounded Discord runtime lane + bounded coordination-bus lane; primary Phase 10 Studio surface implementer | Approved bounded workflows: `hermes_operator_today_shadow`, `hermes_review_execute`, `hermes_watch`; peer Tier 2 ceiling under AOR/Gate; owns bounded Studio surface/readiness/handoff continuation, while OpenClaw records backend dependencies and lower-phase handoffs instead of becoming the Studio implementer |
| OpenAI Agent Harness | Docs only | Tier 2 ceiling; not yet configured |
| Local/OSS (Cline, OpenHands) | Docs only | Tier 2 ceiling; not yet configured |
| n8n | Docs only | Conditional Tier 2; not yet deployed |

---

## 9. Non-Goals — First Phase

These are explicitly deferred:
- OpenClaw writing to `01_PROJECTS/`, `02_KNOWLEDGE/`, or `06_AGENTS/`
- OpenClaw invoking arbitrary external delivery connectors outside declared AOR/SBP manifests
- OpenClaw doing autonomous vault promotion
- Treating OpenClaw as a general production runtime before activation verification
- OpenClaw having broader write authority than Claude Code session agent
- OpenClaw becoming the default Phase 10 Studio implementer; Hermes/Optimus owns bounded Studio surface continuation unless a future explicit workflow says otherwise
- Solving Phase 9-and-below backend blockers from a Phase 10 Studio handoff; OpenClaw should record missing contract, affected Phase 10/11 surface, lower-phase owner/surface, minimum proof needed, and blocked action reason, then route through the appropriate AOR/Gate/Agent Bus lane

---

*Graph links: [[OPENCLAW]] · [[OpenClaw-Runtime-Profile]] · [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Runtime-Navigation-Map]] · [[Runtime-InterAgent-Coordination-Bus]] · [[Runtime-Instance-Authority-Parity]] · [[Vault-Map]] · [[Autonomous-Operator-Runtime]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Execution-Adapter-Standard]] · [[Phase9-Adopted-Feature-Specification]]*

*OpenClaw-Adapter-Spec.md — v1.3 | Created: 2026-04-09 | Patched: 2026-04-09 (governance files created; AOR path verified; activation checklist updated) | Patched: 2026-04-14 (status corrected to governance-configured — stale) | Patched: 2026-04-15 (status corrected to LIVE; activation checklist completed; scheduled execution proven; Discord transport operational) | Patched: 2026-04-21 (schedule-source sync complete; stale Next item corrected; schedule_bridge.md bridge contract live) | Patched: 2026-04-28 (OpenClaw/Hermes governance hardening verifier linked; Hermes stale deferred row corrected; host shell clarified as risk boundary, not authority) | Conforms to: Execution-Adapter-Standard.md*
