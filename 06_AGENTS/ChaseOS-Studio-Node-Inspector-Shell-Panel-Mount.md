# ChaseOS Studio Node Inspector Shell Panel Mount

Status: COMPLETE / VERIFIED TARGETED / BROWSER QA NOT VERIFIED
Date: 2026-05-03
Runtime: Codex

## Summary

The Studio desktop shell mock now mounts a read-only Node Inspector panel at `#node-inspector` and exposes its contract at `/node-inspector-shell-panel.json`.

The panel uses `runtime/studio/node_inspector_shell_panel.py` to derive a selected node from the rebuildable graph contract when no explicit selector is provided. It renders selected-node metadata, edge context, related nodes, and a bounded source excerpt beside or below the existing graph surface.

## Boundary

- No node ID writes.
- No source file edits.
- No graph index writes.
- No snapshot or hidden canonical graph persistence.
- No provider or connector calls.
- No workflow execution.
- No canonical mutation.

## Verification

Targeted unit tests cover the read-only shell-panel contract, desktop shell plan, HTML mount, JSON route, and bounded HTTP smoke. Live browser QA for the mounted node inspector remains the next required pass.



## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
