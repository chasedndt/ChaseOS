# Pulse Truth-State Audit Checklist

**Status:** CREATED - next-pass checklist  
**Created:** 2026-04-29  
**Scope:** ChaseOS Pulse architecture and scaffold audit

Run this checklist before enabling any live Pulse schedule runner, connector, UI,
or writeback workflow.

## Repo Truth

- [ ] Confirm `README.md`, `PROJECT_FOUNDATION.md`, `ROADMAP.md`, and `00_HOME/Now.md` still agree on Phase 9 / Phase 10 posture.
- [ ] Confirm ChaseOS Pulse remains marked PARTIAL, not COMPLETE.
- [ ] Confirm Feature Register and Feature-Fit Register status labels match runtime evidence.
- [ ] Confirm no R&D workbook update is required or explicitly schedule that as a separate pass.

## Runtime Truth

- [ ] Run Pulse schema tests.
- [ ] Run Context Memory Core schema tests.
- [ ] Run AgentHub schema tests.
- [ ] Confirm no Pulse runtime code writes to `02_KNOWLEDGE/`.
- [ ] Confirm no Pulse runtime code mutates `Now.md`, Dashboard, or Project-OS files.
- [ ] Confirm external connector signals require explicit enablement.

## Schedule Truth

- [ ] Confirm Pulse schedule manifests remain ChaseOS-owned intent declarations.
- [ ] Confirm no OpenClaw cron or Windows Task Scheduler state is treated as the owner.
- [ ] Confirm inactive manifests are not confused with live scheduled runs.
- [ ] Confirm OpenFlow manifest remains absent unless OpenFlow repo truth appears.

## Memory Truth

- [ ] Confirm context events and memory atoms are candidates by default.
- [ ] Confirm Personal Map updates are candidates by default.
- [ ] Confirm feedback creates review items, not automatic canonical memory.
- [ ] Confirm runtime brains remain advisory Layer C surfaces.

## UI Truth

- [ ] Confirm no visual UI is claimed as built.
- [ ] Confirm any future UI is a governed surface over ChaseOS state, not a second truth store.

## Governance Truth

- [ ] Confirm agent self-upgrade is not active.
- [ ] Confirm runtime profiles cannot grant canonical promotion authority.
- [ ] Confirm recommended actions requiring mutation require operator approval.
- [ ] Confirm card evidence contains source paths and trust labels.

## Next Recommended Outcome

Only after this checklist passes should a future pass wire Pulse into a real
schedule runner or a read-only operator surface.


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
