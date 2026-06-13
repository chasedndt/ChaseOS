# runtime/memory/nav/ — Runtime Navigation Memory

> Machine-readable navigation overlays for bounded ChaseOS runtimes.
> This folder is the implementation foothold for the Runtime Navigation Map architecture.
> It exists so runtime-specific navigation knowledge can connect both to the current Obsidian markdown vault and to the future standalone ChaseOS surface.

---

## Purpose

The shared vault map (`06_AGENTS/Vault-Map.md`) explains the static structure of the system.

This folder stores the **runtime-specific overlays** that answer a different question:

- Which routes does a runtime actually prefer?
- Which zones are trusted vs risky?
- Which write paths are validated?
- Which successful route patterns have accumulated from repeated runtime evidence?
- Which index files and markdown anchors help the runtime orient correctly?
- Which routes should be preserved when ChaseOS is later represented in a standalone graph/desktop surface?

This is the machine-readable counterpart to:
- `06_AGENTS/Runtime-Navigation-Map.md`
- `06_AGENTS/Hermes-Runtime-Profile.md`
- `06_AGENTS/OpenClaw-Runtime-Profile.md`

---

## Layout

```text
runtime/memory/nav/
├── README.md
├── _schema.json
├── hermes/
│   └── nav-map.json
└── openclaw/
    └── nav-map.json
```

---

## Design Rules

1. **Overlay, not authority** — nav maps never override Vault Map, Permission Matrix, role cards, or Gate rules.
2. **Evidence-oriented** — entries should reflect observed or explicitly approved routes, not speculation.
3. **Obsidian-aware** — routes should preserve markdown structure, index files, wikilinks, and graph navigation conventions.
4. **Standalone-ready** — fields should be usable later by ChaseOS Studio / standalone surfaces without depending on Obsidian internals alone.
5. **Runtime-local** — Hermes and OpenClaw may have different preferred routes, risk zones, and escalation boundaries.

---

## Runtime Self-Orientation Contract

A runtime may also expose a self-orientation layer beside its nav map.

Recommended machine-readable artifacts:
- `state.json` — runtime identity, posture, governance position, orientation sources
- `capabilities.json` — active, blocked, and deferred capability classes
- `next-actions.json` — recommended bounded next steps and explicit not-next items
- `self-report.json` — operator-facing summary synthesized from the other runtime self-state files
- `nav-map.json` — route preferences, trusted zones, risk zones, escalation boundaries

`nav-map.json` may also expose `successful_route_patterns` as read-only accumulated evidence. Each pattern should identify the workflow, the ordered read route, and when that route was observed. Studio may inspect these patterns, but it must not write or curate them from the UI.

These files remain overlays, not authority. They help a runtime describe itself and surface valid next actions without overriding ChaseOS governance.

A good `self-report.json` should answer, in one place:
- who the runtime is
- what it is allowed to do now
- what is blocked now
- what it should do next
- which source files ground that self-description

## Relationship to Markdown Index Structure

These nav overlays should explicitly reference:
- folder index notes like `Build-Logs-Index.md`, `Knowledge-Index.md`, and `Documentation-History-Index.md`
- key routing docs like `06_AGENTS/Vault-Map.md`
- runtime-local machine-readable paths under `runtime/`

This ensures the runtime can bridge between:
1. the current markdown-first Obsidian vault, and
2. the future standalone graph/native representation of the same system.

---

*Graph links: [[Runtime-Navigation-Map]] · [[06_AGENTS/Vault-Map|Vault-Map]] · [[Hermes-Runtime-Profile]] · [[OpenClaw-Runtime-Profile]] · [[ChaseOS-Studio-Architecture]]*
