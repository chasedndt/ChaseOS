---
title: ChaseOS CLI Surface Architecture
type: architecture
status: active
created: 2026-04-24
updated: 2026-04-26
phase: phase-9-active
---

# ChaseOS CLI Surface Architecture

> This document defines the intended top-level shell command tree for ChaseOS as it evolves from scattered command surfaces into a coherent operating-system command interface.

**Current canonical entrypoint (2026-04-26):** `runtime.cli.main:main`. Installed `chaseos` and `chase` scripts point there directly. `chaseos.py` and `runtime/cli.py` remain compatibility shims only.

---

## 1. Why This Exists

ChaseOS now has multiple command surfaces at different maturity levels:
- historical/documented `chaseos capture`, `watch`, `intake`, `doctor`, `test capture`
- runtime policy/Gate command surface via `runtime/chaseos_gate.py`
- runtime-state resolver and CLI foothold via `runtime/state/`
- workflow execution surfaces referenced across AOR and schedule docs

Without a command-tree architecture, the shell surface will drift into a mixture of:
- implementation stubs
- historically valid commands
- future intended commands
- subsystem-local helper scripts

This document defines the intended shape so the CLI can grow coherently.

---

## 2. Design Principle

ChaseOS CLI should be organized around OS-level capability families, not around implementation accidents.

That means commands should group by operator intent, for example:
- capture / intake
- runtime inspection
- runtime policy / gate
- workflows / run
- scheduling
- health / diagnostics

The shell surface should mirror the architecture of the OS.

---

## 3. Proposed Top-Level Command Tree

```text
chaseos capture ...
chaseos intake ...
chaseos watch ...
chaseos run ...
chaseos runtime ...
chaseos gate ...
chaseos setup ...
chaseos schedule ...
chaseos doctor ...
chaseos test ...
```

---

## 4. Command Families

### `chaseos capture ...`
Purpose:
- ingest external material into ChaseOS intake/quarantine surfaces

Examples already documented in framework history:
- `chaseos capture file`
- `chaseos capture stdin`
- `chaseos capture rss URL [--limit N]`
- `chaseos capture browser file PATH`
- `chaseos capture perplexity --query "..."`
- `chaseos capture grok --query "..."`

### `chaseos intake ...`
Purpose:
- inspect and manage intake-side material

Examples:
- `chaseos intake ls`
- `chaseos intake inspect`
- `chaseos intake dedup-stats`

### `chaseos watch ...`
Purpose:
- manage watched-folder or automated input monitoring surfaces

Examples:
- `chaseos watch add PATH --class CLASS`
- `chaseos watch run --once`

### `chaseos run ...`
Purpose:
- invoke bounded workflows through the operator/runtime substrate
- for coordination-sensitive workflows, require explicit adapter identity plus declared bus path so the shell surface cannot silently bypass bus-first governance

Examples:
- `chaseos run operator_today`
- `chaseos run operator_close_day`
- `chaseos run graph_hygiene`
- `chaseos run hermes_review_execute --adapter hermes --coordination-via runtime/agent_bus/`

### `chaseos runtime ...`
Purpose:
- inspect and resolve runtime posture
- later, possibly inspect runtime health and attachments

First intended commands:
- `chaseos runtime resolve`
- `chaseos runtime status`

### `chaseos gate ...`
Purpose:
- validate and inspect runtime policy surfaces
- expose Gate checks in a stable operator-facing way
- give operators and harnesses a promoted coordination-policy check instead of relying on raw helper scripts

Live commands:
- `chaseos gate validate`
- `chaseos gate list-adapters`
- `chaseos gate show-adapter <adapter-id>`
- `chaseos gate check-write <adapter-id> <path>`
- `chaseos gate check-task <adapter-id> <task-type>`
- `chaseos gate check-coordination <adapter-id> --coordination-sensitive --via runtime/agent_bus/ --target-runtime <runtime>`

### `chaseos setup ...`
Purpose:
- configure providers, integrations, runtime-specific onboarding, and guided setup flows

Likely commands:
- `chaseos setup provider list`
- `chaseos setup provider wizard <provider-id>`
- `chaseos setup integration list`
- `chaseos setup integration wizard <integration-id>`
- `chaseos setup runtime wizard`
- `chaseos setup menu`

### `chaseos schedule ...`
Purpose:
- inspect and manage native ChaseOS schedule intent

Likely commands:
- `chaseos schedule list`
- `chaseos schedule show <schedule-id>`
- `chaseos schedule enable <schedule-id>`
- `chaseos schedule disable <schedule-id>`
- `chaseos schedule export --adapter openclaw`

### `chaseos doctor ...`
Purpose:
- environment and subsystem diagnostics

Examples:
- `chaseos doctor`
- future subsystem-specific health checks

### `chaseos test ...`
Purpose:
- explicit test and verification surfaces

Examples:
- `chaseos test capture`
- future runtime/gate/schedule verification commands

---

## 5. Command-Surface Maturity Model

ChaseOS should distinguish command maturity clearly.

### A. Live and directly inspectable
Commands backed by current implementation in the active repo/environment.

### B. Documented and historically valid
Commands that are part of the broader ChaseOS system history or related implementation environments, but not necessarily directly invokable from the current repo surface.

### C. Intended contract
Commands explicitly named as future stable command surfaces, backed by design docs and foothold implementations.

This distinction should appear in operator docs so the CLI remains honest.

---

## 6. Mapping Current Footholds into the Canonical Tree

| Current foothold | Future CLI home |
|------------------|-----------------|
| `python runtime\\state\\runtime_cli.py resolve` | `chaseos runtime resolve` (package-native in `runtime.cli.main`) |
| `python runtime\\state\\runtime_cli.py status` | `chaseos runtime status` (package-native in `runtime.cli.main`) |
| `python runtime\\chaseos_gate.py validate` | `chaseos gate validate` |
| `python runtime\\chaseos_gate.py list` | `chaseos gate list-adapters` |
| `python runtime\\chaseos_gate.py show <adapter-id>` | `chaseos gate show-adapter <adapter-id>` |
| `python runtime\\chaseos_gate.py check-write ...` | `chaseos gate check-write ...` |
| `python runtime\\chaseos_gate.py check-task ...` | `chaseos gate check-task ...` |
| `python runtime\\setup_cli.py provider list` | `chaseos setup provider list` (package-native parser calls setup handlers directly) |

No new shell-facing family should be added to `chaseos.py` or `runtime/cli.py`. Add it to `runtime/cli/main.py`, then keep the shims passive.

---

## 7. Why This Aligns with the Overall ChaseOS OS

This architecture matters because ChaseOS is no longer just a file system plus docs.
It is becoming:
- a governed operating environment
- a runtime-aware system
- a workflow-capable operator substrate
- a future interface-bearing operating system

A coherent CLI tree is one of the first durable external shapes of that operating system.

---

## 8. Recommended Next Step

After this consolidation pass, the next practical moves are:
1. remove or retire stale subsystem-local command docs once the equivalent package-native command is proven
2. add deny-by-default gateway policy commands under the same parser tree instead of creating a gateway-specific shell front
3. keep regression tests that prove `pyproject.toml`, `chaseos.py`, and `runtime/cli.py` all route to `runtime.cli.main`

---

*Graph links: [[ChaseOS-Runtime-Command-Contract]] · [[ChaseOS-Runtime-CLI-Foothold]] · [[Autonomous-Operator-Runtime]] · [[Scheduling-Intent-Architecture]]*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
