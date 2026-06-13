---
title: OpenClaw Tools Control File
type: openclaw-runtime-control
scope: runtime-local - declares permitted chaseos CLI toolset for OpenClaw's first-phase activation
created: 2026-04-09
---

# OpenClaw - Permitted ChaseOS Toolset

> This file declares the permitted `chaseos` CLI toolset for OpenClaw's first bounded activation phase.
> It is a runtime-local control file. Additional tools require AOR manifest declaration before invocation.
> Canonical permission source: `06_AGENTS/OpenClaw-Adapter-Spec.md` Section 4

---

## First-Phase Permitted Tools

| Command | Description | Scope |
|---------|-------------|-------|
| `chaseos run operator_today` | Run operator_today through AOR pipeline | Produces brief in `07_LOGS/Operator-Briefs/` |
| `chaseos run operator_close_day` | Run operator_close_day through AOR pipeline | Produces close note in `07_LOGS/Operator-Briefs/` |
| `chaseos run graph_hygiene` | Run graph_hygiene through AOR pipeline | Proposal-only report; no canonical mutation |
| `chaseos run sbp_strikezone_digest` | Run declared SBP digest workflow through AOR/SBP pipeline | Output limited by SBP manifest and Gate policy |
| `chaseos intake ls` | List quarantine intake contents | Read-only audit |
| `chaseos intake dedup-stats` | Show dedup registry stats | Read-only audit |
| `runtime/agent_bus/*` | Read/write structured coordination bus state | Bounded runtime-to-runtime task routing only; does not expand AOR authority |

---

## Host Execution Note (Current Windows Host)

The canonical logical ChaseOS tool contract remains:

- `chaseos run operator_today`
- `chaseos run operator_close_day`
- `chaseos run graph_hygiene`
- `chaseos run sbp_strikezone_digest`
- `chaseos intake ls`
- `chaseos intake dedup-stats`

However, on the current Windows host, the `chaseos` PATH alias is not yet reliable.

Therefore, OpenClaw must currently execute approved commands from:

`<VAULT_ROOT>`

using:

`.\.venv\Scripts\python.exe -m runtime.cli.main ...`

### Working directory

`<VAULT_ROOT>`

### Approved current host execution forms

#### operator_today

```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main run operator_today
```

#### operator_close_day

```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main run operator_close_day
```

#### doctor

```powershell
cd <VAULT_ROOT>
.\.venv\Scripts\python.exe -m runtime.cli.main doctor
```

---

## Deferred Tools (Require Explicit Grant)

| Command | Status | Unlock Condition |
|---------|--------|-----------------|
| `chaseos run graduate_ideas` | Deferred | Explicit operator grant + AOR manifest declaration |
| `chaseos capture ...` | Deferred | Requires workflow declaration in AOR manifest |
| `chaseos watch ...` | Deferred | Requires workflow declaration in AOR manifest |
| Any shell command outside `chaseos` | Forbidden for ChaseOS-governed tasks unless explicitly granted | Host-level access is not ChaseOS authority; any exception needs operator/session approval plus a declared manifest/tool grant |

---

## Constraint: AOR Pipeline Required

All `chaseos run` invocations must go through the AOR pipeline.
OpenClaw must not:
- Write directly to vault files (even though it has host-level filesystem access)
- Bypass Stage 7 writeback validation
- Invoke handlers outside the registered workflow manifest

---

## Constraint: Credential Boundary

OpenClaw must not read:
- `.env` files anywhere in the vault
- `secrets/` directories
- Any file with API keys, tokens, or credentials

The chaseos CLI reads credentials from environment variables (e.g., `PERPLEXITY_API_KEY`, `XAI_API_KEY`).
OpenClaw should not set or override these variables.

---

*runtime/openclaw/tools.md - OpenClaw runtime-local control | Created: 2026-04-09 | Patched: 2026-04-28 (graph_hygiene and SBP digest aligned with proven bounded AOR/SBP scope; host shell clarified as non-authority)*


*Graph links: [[OpenClaw-Runtime-Profile]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
