# ChaseOS Pulse Multi-Audience Decks

Status: COMPLETE TARGETED / LOG-ONLY
Date: 2026-05-02
Runtime: Codex, building on Hermes/Optimus feature hardening

## Purpose

ChaseOS Pulse must support user, agent, and shared-coordination audiences. The
first user deck path already existed, and Hermes/Optimus added deterministic
agent/shared deck builders. This pass made those builders operational through a
single governed CLI surface and inventory reader.

## Runtime Surface

Implemented:

- `runtime/pulse/multi_audience_decks.py`
- `chaseos pulse generate-decks`
- `chaseos pulse deck-inventory`
- `runtime/pulse/test_multi_audience_decks.py`

`generate-decks` is dry-run by default. With `--write`, it writes markdown and
JSON deck artifacts only under:

```text
07_LOGS/Pulse-Decks/users/
07_LOGS/Pulse-Decks/agents/
07_LOGS/Pulse-Decks/shared/
```

## Current Live Artifact Set

Generated on 2026-05-02:

```text
07_LOGS/Pulse-Decks/users/2026-05-02-multi-audience-user-pulse-expanded.md
07_LOGS/Pulse-Decks/users/2026-05-02-multi-audience-user-pulse-expanded.json
07_LOGS/Pulse-Decks/agents/2026-05-02-multi-audience-agent-pulse-expanded.md
07_LOGS/Pulse-Decks/agents/2026-05-02-multi-audience-agent-pulse-expanded.json
07_LOGS/Pulse-Decks/shared/2026-05-02-multi-audience-shared-pulse-expanded.md
07_LOGS/Pulse-Decks/shared/2026-05-02-multi-audience-shared-pulse-expanded.json
```

Inventory command:

```text
chaseos pulse deck-inventory --json
```

The current inventory reports:

- user deck: 8 cards
- agent deck: 3 cards
- shared-coordination deck: 3 cards

## Governance Boundary

Allowed:

- Build deterministic local decks from repo-local Pulse scaffold evidence.
- Dry-run all deck audiences without writing.
- Write log-only deck artifacts under `07_LOGS/Pulse-Decks/` when `--write` is
  explicit.
- Read latest deck inventory by audience.

Blocked:

- Schedule activation.
- Runtime dispatch.
- Agent Bus task writes.
- Provider, browser, MCP, or connector calls.
- Memory approval.
- Personal Map mutation.
- Project file mutation.
- `02_KNOWLEDGE/` promotion.
- R&D workbook mutation.
- Second datastore creation.

## Remaining Work

This pass does not make decks intelligent from live runtime state yet. Future
passes can replace deterministic cards with richer signal selection while
preserving this audience/output contract.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
