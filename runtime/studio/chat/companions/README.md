# Phase 11 Companion Profile Registry Contract

Status: CONTRACT SEEDED / READ-ONLY REGISTRY READINESS VERIFIED / OPERATOR DIRECTION CAPTURED / GOVERNED SELECTION TARGET WRITE VERIFIED / CORE COMPANION LAYER SEEDED / STUDIO CORE ADAPTER SYNC VERIFIED / MEMORY BOUNDARY DEFINED.

This folder is the planned durable registry for Phase 11 Studio companions. It exists because the companion feature must support more than one possible companion.

Current truth:

- Existing companion status code exposes multiple builtin runtime companions.
- This folder now defines the future profile schema and example roster shape.
- `runtime/studio/phase11_multi_companion_registry_readiness.py` now validates this folder's registry/schema and compares registry entries to the builtin Hermes/OpenClaw/Archon companion status cards.
- `runtime/studio/phase11_operator_companion_direction.py` now reads the registry readiness output to show current companion options and the unanswered operator decisions before roster UI.
- `operator-direction.v0.1.json` captures the operator-approved v0.1 companion policy: Hermes/OpenClaw/Archon, per-Chat-session selection, UI/tone/status/read-only-card/non-authoritative-comment effects only, separate governed companion memory namespaces, and no routing/provider/permission/writeback/memory-write/tool/protected-file authority.
- `runtime/studio/phase11_operator_companion_direction_answers.py` validates the approved policy and unlocks only the next read-only roster UI preview.
- `runtime/companion/` now holds the core v0.1 companion policy, roster/profile validation, read-only switch preview, approval-flag-gated selection writer, and companion switch ledger behavior. It preserves the existing Studio selection target and does not add Studio UI, avatar assets, provider calls, routing, memory, Agent Bus writes, or canonical mutation.
- Studio companion status, registry readiness, roster UI preview, and selection preview now read Hermes/OpenClaw/Archon identity metadata from `runtime/companion` instead of maintaining separate Studio-local metadata. `runtime/companion` does not import Studio companion status code.
- `runtime/companion/memory.py` and `runtime/studio/phase11_companion_memory_boundary_contract.py` now define the separate governed memory namespace boundary. They preview future `07_LOGS/Companion-Memory/{companion}/` paths and validate future memory candidates, but write no memory files.
- No durable custom profile loader for selection, write-capable UI roster picker, provider call, runtime dispatch, Agent Bus task write, or identity/profile mutation is implemented by this registry-readiness/core-adapter pass. The separate governed approval-consumption executor has written `runtime/studio/chat/companion-selection.json` once under exact approval/digest controls.

Rules:

- Companions are UX/status/personality surfaces only.
- Companion personality never grants authority.
- Runtime authority still comes from runtime profiles, role cards, trust tiers, Gate rules, Approval Center state, and explicit approval/executor paths.
- Future selection writes target `runtime/studio/chat/companion-selection.json` only through the governed companion-selection approval-consumption executor.
- Registry validation is read-only and must not be treated as selection execution.
- Operator direction answer validation is read-only and must not be treated as companion selection execution, provider/model routing, permission expansion, memory access, tool access, or write authority.
- Companion memory boundary validation is read-only and must not be treated as memory write approval, memory execution, provider/model routing, permission expansion, tool access, or canonical promotion.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
