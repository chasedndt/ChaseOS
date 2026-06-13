# ChaseOS Pulse Signal-Driven Decks

**Status:** COMPLETE TARGETED / LOG-ONLY  
**Date:** 2026-05-02  
**Runtime:** Codex  
**Feature lane:** ChaseOS Pulse product-grade pass 1/6

## Purpose

Signal-driven decks move ChaseOS Pulse beyond fixed proof cards while staying
inside ChaseOS governance.

The implementation reads a narrow local evidence snapshot and generates user,
agent, and shared-coordination decks from current repo truth. It is not a live
provider call, not browsing, not schedule activation, not an Agent Bus write,
not memory approval, and not canonical writeback.

## Local Signal Inputs

`runtime/pulse/signal_driven_decks.py` reads:

- recent build logs under `07_LOGS/Build-Logs/`
- latest matching Pulse build log
- recent agent activity logs under `07_LOGS/Agent-Activity/`
- latest matching Pulse and Hermes activity logs
- Pulse schedule manifests under `runtime/schedules/manifests/`
- Pulse completion status from `runtime/pulse/completion_status.py`
- Pulse post-completion hardening status from `runtime/pulse/post_completion_hardening.py`
- Pulse deck inventory from `runtime/pulse/multi_audience_decks.py`

It does not read browser history, invoke external connectors, call providers,
scan the web, or create a second datastore.

## Deck Output

The command:

```powershell
python -m chaseos pulse generate-signal-decks --write --json
```

writes only markdown/JSON deck artifacts under:

```text
07_LOGS/Pulse-Decks/users/
07_LOGS/Pulse-Decks/agents/
07_LOGS/Pulse-Decks/shared/
```

Current written artifacts:

```text
07_LOGS/Pulse-Decks/users/2026-05-02-pass1-signal-user-pulse-signal.md
07_LOGS/Pulse-Decks/users/2026-05-02-pass1-signal-user-pulse-signal.json
07_LOGS/Pulse-Decks/agents/2026-05-02-pass1-signal-agent-pulse-signal.md
07_LOGS/Pulse-Decks/agents/2026-05-02-pass1-signal-agent-pulse-signal.json
07_LOGS/Pulse-Decks/shared/2026-05-02-pass1-signal-shared-pulse-signal.md
07_LOGS/Pulse-Decks/shared/2026-05-02-pass1-signal-shared-pulse-signal.json
```

## Generated Audiences

The signal-driven pass generates all three Pulse audiences:

- `user`
- `agent`
- `shared_coordination`

Each deck currently emits three cards and includes local evidence, source
links, related nodes, thumbnails, recommended actions, confidence,
promotion/writeback status, and governance state through the existing
`PulseCard` schema.

## Governance Boundary

The result schema rejects these authority flags:

- canonical writeback
- memory approval
- provider or connector calls
- runtime dispatch
- schedule activation
- Agent Bus task writes
- R&D workbook update
- second datastore creation

`--write` changes only the Pulse deck archive. It does not mutate Now.md,
Project-OS files, governance docs, runtime memory, Personal Map files, or
`02_KNOWLEDGE/`.

## CLI Surface

Dry-run:

```powershell
python -m chaseos pulse generate-signal-decks --json
```

Write deck artifacts:

```powershell
python -m chaseos pulse generate-signal-decks --write --json
```

Check latest artifacts:

```powershell
python -m chaseos pulse deck-inventory --json
```

## Tests

Focused coverage:

```powershell
python -m pytest runtime/pulse/test_signal_driven_decks.py -q
```

CLI contract coverage:

```powershell
python -m pytest runtime/pulse/test_signal_driven_decks.py runtime/tests/test_cli_command_contract.py -q
```

Latest targeted result: `13 passed`.

## Remaining Work

Signal-driven decks are still local backend artifacts. Remaining product-grade
work includes approval UI, runtime brain dashboard, Personal Map visualization,
native schedule runner activation after explicit approval, and optional
connector/source-scanner expansion under permission envelopes.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
