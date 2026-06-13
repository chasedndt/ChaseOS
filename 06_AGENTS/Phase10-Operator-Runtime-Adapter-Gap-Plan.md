---
title: Phase 10 Operator Runtime Adapter Gap Plan
type: readiness-matrix
status: DECISION-COMPLETE-BACKLOG
phase: 10
runtime: Codex
updated: 2026-05-07
---

# Phase 10 Operator Runtime Adapter Gap Plan

This note captures the remaining operator/runtime/adapter activation work. These are runtime activation problems, not Studio panel-only problems. This pass performs no provider calls, connector calls, host mutation, Agent Bus writes, or workflow execution.

## Readiness Matrix

| Feature | Current Status | Blocker | Required Approval | Command / Entrypoint | Evidence Needed | Parallel With Studio Work |
|---|---|---|---|---|---|---|
| n8n live deployment readiness | PLANNED / NOT LIVE | token/config/test workflow missing | provider/connector approval before live call | TBD n8n readiness command | config redaction proof, dry-run workflow, live smoke evidence | Yes, if read-only planning |
| OpenAI Agent Harness MCP workspace | PLANNED / NOT BUILT | MCP workspace and adapter contract missing | provider/API use approval before live calls | future `runtime/adapters/openai/` harness | adapter manifest, no-secret test, mock run, live gated smoke | Yes, after contract split |
| Local/OSS model harness | PLANNED / NOT ACTIVE | target runtime, timeout, and fallback contract missing | local process/model launch approval | future local harness command | startup/readiness proof, timeout proof, no-provider fallback | Yes, read-only design can run now |
| Excalidraw local loopback/MCP | BLOCKED | target URL/readiness unknown | external loopback approval | existing external runtime readiness/branch gate paths | loopback target proof, local-only screenshot/evidence | Yes, blocked until target known |
| Pulse live schedule runner | PARTIAL / BLOCKED | backend proof chains exist; live apply effects not active | schedule apply approval and exact-once executor | Pulse schedule/apply commands | approval packet, marker, schedule state diff, run evidence | Partly; executor must serialize with truth sync |
| OSRIL continuation/reconnect UX | PLANNED | browser shell route and reconnect state not mounted | operator shell approval before live surface | future OSRIL shell route | reconnect simulation, session continuity evidence | Yes for design, no for live activation |
| Live Operator Shell browser surface | FUTURE | route, auth boundary, and approval surfaces not built | operator shell launch approval | future browser-accessible shell | localhost-only proof, auth/permission boundary QA | No if touching shared shell truth |
| Voice I/O Architecture | FUTURE | STT/TTS abstraction/adapters missing | microphone/speaker/provider approval | future voice adapter contract | mock STT/TTS, privacy boundary, live gated smoke | Yes for architecture only |
| Live Visual Shell | CONTRACT SEEDED / NOT IMPLEMENTED | render target and fixture-backed adapter still missing; `06_AGENTS/Live-Visual-Shell-Contract.md` now defines source classes, visual state precedence, packet shape, QA proof, and authority boundary | visual shell runtime approval before live surface/panel activation | future `runtime/studio/live_visual_shell.py` + desktop shell panel | state-to-visual fixture, contract shape tests, no-write static QA, browser visual evidence | Yes; start with fixture-backed mapper only |
| Companion mobile/tablet surface | SEEDED / NOT LIVE | target architecture exists; live auth, gateway/mobile delivery, approval-response execution, capture-trigger request path, runtime-dispatch bridge, and canonical writeback chain remain blocked | network/mobile + approval/capture approvals before live action | future companion app or responsive Studio panel | responsive read-only proof, auth/session proof, approval/capture smoke through AOR/Gate/StudioService | Architecture yes; live mobile actions no until security/backend dependencies are proven |
| Runtime Support Loops | FUTURE | telemetry schema and suggestion boundaries missing | telemetry/support-loop approval | future support-loop runner | opt-in tracking proof, no-autonomous-write proof | Yes for schema only |

## Activation Rules

- Provider/connector live calls require explicit approval and must keep secrets hidden.
- Local process launches require a bounded launcher, timeout, and proof evidence.
- Agent Bus writes are not implied by readiness checks.
- Host startup/autostart mutation remains deferred behind its own approval consumption/execution chain.
- Pulse memory, Personal Map, and governed core runtime state must not be mutated directly from Codex work.

## Recommended Future Passes

| Pass | Scope | Dependencies |
|---|---|---|
| `runtime-n8n-readiness-contract` | Read-only n8n config/test workflow readiness | operator supplies target/config boundary |
| `runtime-openai-agent-harness-mock` | MCP workspace and mock executor | adapter manifest and no-secret config path |
| `runtime-local-oss-harness-timeout-proof` | Local model target, launch timeout, fallback proof | selected local runtime target |
| `runtime-excalidraw-loopback-readiness` | Loopback target/readiness check | target URL/readiness from operator |
| `pulse-live-schedule-approval-chain` | Approval packet plus exact-once schedule apply proof | Pulse schedule backend proof chain |
| `osril-reconnect-shell-contract` | Browser-accessible continuation/reconnect design | operator shell boundary |



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*

*Graph links: [[OpenClaw-Runtime-Profile]]*
