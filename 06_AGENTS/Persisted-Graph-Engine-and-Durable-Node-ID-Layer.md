---
title: Persisted Graph Engine and Durable Node-ID Layer
status: architecture-ready / implementation-deferred
phase: Phase 9 backend dependency; Phase 10 Studio consumer
type: architecture-contract
created: 2026-05-12
updated: 2026-05-12
owner: Optimus
---

# Persisted Graph Engine and Durable Node-ID Layer

> This contract handles the deferred gap beyond the Phase 10 read-only graph model: durable graph storage and durable node identity. It does not activate graph mutation, node-ID writeback, canonical promotion, protected-file writes, or hidden Studio persistence.

## 1. Purpose

Phase 10 Studio already has a strong read-only graph foundation:

- `runtime/studio/graph_scanner_parser.py` parses Markdown/Obsidian/ChaseOS folders into deterministic graph input.
- `runtime/studio/graph_index_contract.py` derives bounded in-memory nodes and edges with deterministic IDs.
- `runtime/studio/graph_visual_model.py` and `runtime/studio/graph_visual_overlays.py` render typed node families, edge layers, and trust/generated/canonical visual posture.
- `runtime/studio/graph_provenance_inspector.py` exposes selected-node provenance in read-only form.
- `runtime/studio/controlled_node_write.py` and `runtime/studio/visual_link_approval.py` queue approval-gated file/link changes without persisting a graph database or writing node IDs.
- `runtime/graph/artifact.py` defines the Phase 9 graph snapshot model with serializable `GraphSnapshot`, deterministic `GraphNode.node_id`, deterministic `GraphEdge.edge_id`, and save/load helpers.

The remaining gap is not another visual overlay. It is the durable backend layer that decides when a derived graph identity becomes a stable operating identifier, where graph snapshots live, how migrations are reviewed, and which write path may update canonical/source-of-truth artifacts.

## 2. Governing Split

ChaseOS must keep three graph layers separate:

| Layer | Source of truth | May persist? | May write canonical/source files? | Studio role |
|---|---|---:|---:|---|
| Derived read-only graph | Scanner/parser output, `runtime/graph` snapshots, current Markdown/runtime files | Yes, as rebuildable snapshots/caches | No | Render, inspect, filter, prove readiness |
| Durable graph identity layer | Approved graph identity registry and snapshot manifest | Yes, under explicit Phase 9 graph storage contract | No direct Markdown/canonical mutation by itself | Resolve stable IDs, compare snapshots, warn about migrations |
| Canonical/source write layer | Markdown files, source packs, promoted knowledge, Gate-approved write packets | Yes, through existing governed write paths | Only after Gate/approval/executor contract | Queue and display approval state; never bypass backend |

Short rule: durable graph IDs are operating identifiers, not proof that the graph owns canonical truth. Canonical/source writes still happen through declared governed write paths.

## 3. Architecture

### 3.1 Storage roots

The first durable graph layer should use repo-local, explicit roots rather than hidden application state:

```text
runtime/graph/store/
  Graph-Store-Folder-Guide.md
  manifests/
    current.json                 # pointer to active snapshot manifest
    snapshots/<snapshot_id>.json # immutable snapshot manifests
  snapshots/
    <snapshot_id>.json           # serialized GraphSnapshot or StudioGraphSnapshot
  identity/
    node_identity_registry.json  # durable node-key -> durable node-id map
    aliases.json                 # reviewed rename/split/merge aliases
  migrations/
    <migration_id>.json          # dry-run migration plans and outcomes
```

These files are graph-operating artifacts. They are not canonical knowledge and must not be silently copied into `02_KNOWLEDGE/`.

### 3.2 Snapshot manifest

Each persisted snapshot should carry a small manifest that can be audited without loading the full graph:

```json
{
  "snapshot_id": "graph-snap-2026-05-12T010203Z-abc123",
  "created_at": "2026-05-12T01:02:03Z",
  "builder": "runtime.graph.builder.full_pipeline",
  "source_model": "runtime.graph.GraphSnapshot.v2 or studio.graph_index_contract.v1",
  "vault_root_hash": "sha256 redacted/path-normalized root identity",
  "scope": ["06_AGENTS/", "runtime/"],
  "source_file_count": 1234,
  "node_count": 20000,
  "edge_count": 39800,
  "source_hashes_path": "runtime/graph/store/manifests/source-hashes/<snapshot_id>.json",
  "identity_registry_version": "node_identity_registry.v1",
  "canonical_mutation_allowed": false,
  "generated_from_read_only_scan": true
}
```

### 3.3 Durable node identity registry

The durable registry should map deterministic source keys to durable IDs while preserving rebuildability:

```json
{
  "schema_version": "node_identity_registry.v1",
  "updated_at": "2026-05-12T01:02:03Z",
  "authority": {
    "canonical_write_allowed": false,
    "requires_gate_for_source_write": true,
    "generated_by": "phase9_graph_storage_contract"
  },
  "nodes": {
    "studio:file:06_AGENTS/HERMES.md": {
      "durable_node_id": "node_01J...",
      "source_key": "studio:file:06_AGENTS/HERMES.md",
      "current_derived_ids": ["studio:agent_control_doc:..."],
      "source_path": "06_AGENTS/HERMES.md",
      "node_type": "agent_control_doc",
      "first_seen_snapshot": "graph-snap-...",
      "last_seen_snapshot": "graph-snap-...",
      "status": "active",
      "provenance": "derived_from_markdown_scan_contract",
      "canonical_ref": null
    }
  },
  "aliases": {
    "old-derived-id-or-path-key": {
      "durable_node_id": "node_01J...",
      "reason": "path rename reviewed",
      "review_ref": "runtime/graph/store/migrations/...json"
    }
  }
}
```

Durable IDs should be generated once per reviewed source key and then reused. The current deterministic derived IDs remain useful as cache keys, but the durable ID is the stable UI/operator reference across snapshot rebuilds, path moves, and parser-version changes.

### 3.4 Read path

Read path for Studio:

1. Scanner/parser builds current derived graph input.
2. Persisted graph reader loads the latest snapshot manifest and identity registry if present.
3. Resolver annotates each derived node with:
   - `durable_node_id` when a reviewed registry mapping exists,
   - `identity_state` such as `registered`, `unregistered`, `stale`, `aliased`, or `conflict`,
   - `snapshot_id` and `registry_version` for audit.
4. Studio renders identity state as read-only graph metadata.

### 3.5 Write path

Write path must stay approval/Gate mediated:

1. Studio may propose a node identity registration, alias, split, merge, or source-file edit.
2. The proposal becomes an approval packet, not an immediate write.
3. Phase 9 graph governance validates target roots, source hashes, provenance, and Gate policy.
4. Approved executor writes only the declared graph-store artifact or approved source-file change.
5. Every mutation writes Agent Activity / graph-store migration evidence.
6. Studio refreshes from the new snapshot/registry, not from local UI state.

## 4. Storage and Migration Risks

| Risk | Why it matters | Required mitigation |
|---|---|---|
| Derived ID churn | Parser/model changes can change `studio:*` IDs and break user pins/history | Durable registry maps reviewed source keys to durable IDs; migration plans must preserve aliases |
| Path rename ambiguity | Markdown file moves can look like delete+create | Compare content hash, title/frontmatter, aliases, and prior registry entries before declaring a new node |
| Canonical/source truth confusion | A graph database could appear to be a second vault truth layer | Store graph artifacts under `runtime/graph/store/`; require docs/UI to label them rebuildable/non-canonical |
| Hidden UI persistence | Frontend could silently persist graph state outside governance | No browser/localStorage authority for durable IDs; persistence must be backend file/artifact based and audited |
| Concurrent approvals | Node edits and link proposals can race with snapshot persistence | Store source hashes in approval packets and reject stale approved execution if source hash changed |
| Trust/canonical escalation | Durable IDs could be misread as trust promotion | Identity status must not change trust/canonical state; trust/canonical writes remain blocked unless separate Gate path exists |
| Large-vault size | Persisting full graphs every refresh can bloat repo | Snapshot cap policy, manifest-only current pointer, retention/compaction plan, and optional diff snapshots |

## 5. Acceptance Criteria

The durable graph/node-ID layer is implementation-ready only when all criteria below can be tested:

1. A graph-store folder guide declares allowed roots, forbidden roots, retention, and audit expectations.
2. A persisted snapshot writer can write an immutable snapshot plus manifest under `runtime/graph/store/` only when explicitly requested.
3. A snapshot reader can load the current manifest and snapshot without scanning the vault.
4. A node identity registry can map stable source keys to durable node IDs without modifying Markdown/frontmatter.
5. A resolver can annotate existing Studio graph nodes with durable IDs while preserving the derived graph model.
6. Migration dry-run can classify `unchanged`, `new`, `missing`, `path_renamed`, `content_changed`, `split_candidate`, and `merge_candidate` states.
7. Approval packets include source hashes and reject stale execution when the source file changed after preview.
8. Gate/runtime policy blocks graph-store writes outside the declared roots and all direct canonical/source writes not routed through existing governed write paths.
9. Studio can display durable identity state read-only and cannot write registry/snapshot data directly from frontend state.
10. Tests prove no node IDs are inserted into Markdown/frontmatter by the snapshot or registry layers.

## 6. Proof Plan

Use strict TDD and keep the first implementation pass storage-only:

1. Add failing tests for a `runtime.graph.store` snapshot manifest writer that writes only under `runtime/graph/store/` and rejects `02_KNOWLEDGE/`, `06_AGENTS/Permission-Matrix.md`, and arbitrary paths.
2. Implement the minimal store writer/reader over existing `GraphSnapshot.save()` and `GraphSnapshot.load()`.
3. Add failing tests for `node_identity_registry.v1` create/load/resolve behavior using source keys and deterministic fixtures.
4. Implement registry creation and read-only annotation; do not touch Markdown files.
5. Add migration dry-run tests for path rename, missing node, new node, and changed content hash.
6. Add Gate-policy tests for `graph_store.snapshot.write`, `graph_store.identity.write`, and `graph_store.migration.write` operation names before any CLI/API mutator exists.
7. Add Studio resolver tests proving current graph nodes can carry `durable_node_id` metadata when a registry exists and `identity_state=unregistered` when it does not.
8. Add static/no-write QA proving the real vault source tree, approval artifacts, and canonical docs remain unchanged unless an explicit graph-store write command is invoked.

Recommended focused validation commands after implementation starts:

```bash
PYTHONPATH=. uvx --with pyyaml pytest runtime/graph -q
PYTHONPATH=. uvx --with pyyaml pytest runtime/studio/test_graph_index_contract.py runtime/studio/test_graph_provenance_inspector.py -q
PYTHONPATH=. uvx --with pyyaml pytest runtime/studio/test_controlled_node_write.py runtime/studio/test_visual_link_approval.py -q
```

## 7. Safe Migration Path

Stage 0 — current truth:
- Derived graph and Studio graph surfaces remain read-only or approval-gated.
- No persisted graph engine or durable node-ID writer is active.

Stage 1 — storage contract and tests:
- Add graph-store schemas, folder guide, snapshot manifest tests, identity registry tests, and Gate operation-policy tests.
- No Studio UI write controls.

Stage 2 — explicit snapshot write command:
- Add an operator-confirmed CLI/API path to write a snapshot under `runtime/graph/store/`.
- Require dry-run output and explicit `--write`/confirmation.
- Still no source Markdown writes.

Stage 3 — identity registry and migration dry-run:
- Create/read registry and aliases.
- Produce migration plans but do not apply source changes.
- Surface conflicts in Studio as read-only warnings.

Stage 4 — approval-gated graph-store mutations:
- Queue approval packets for registry aliases/split/merge decisions.
- Execute only graph-store artifact writes with exact-once markers and source-hash checks.

Stage 5 — source/canonical integration, separately governed:
- If a future workflow must write node IDs into source files or canonical graph artifacts, require a separate Phase 9/Gate contract, protected-file policy review, rollback plan, and approval execution tests.
- Studio remains a proposal/inspection surface.

## 8. Explicit Non-Goals

This contract does not authorize:

- direct canonical graph mutation;
- direct `02_KNOWLEDGE/` writes;
- protected-file writes;
- node-ID insertion into Markdown/frontmatter;
- trust/canonical promotion;
- source-pack promotion;
- provider/connector calls;
- workflow/runtime execution;
- Agent Bus task creation from graph UI;
- hidden browser/localStorage persistence as an operating source of truth.

## 9. Implementation Backlog

The first lower-phase implementation subtasks should be created in this order:

1. Graph store schemas/folder guide plus store writer/reader tests.
2. Durable node identity registry plus resolver tests.
3. Migration dry-run classifier plus source-hash/stale-execution tests.
4. Gate operation-policy coverage for graph-store writes.
5. Studio read-only durable identity annotation after the backend is ready.

Do not implement Stage 5 source/canonical writes until Phase 9 graph governance and Gate consumption explicitly approve that authority.

## 10. Graph Links

[[Graph-Substrate-Architecture]] · [[Graph-Native-Node-and-Edge-Consolidation-Surfaces-Standalone-Application]] · [[Phase10-Graph-Write-Structural-Gap-Plan]] · [[ChaseOS-Studio-Phase10-Implementation-Tracker]] · [[ChaseOS-Approval-Center]] · [[Autonomous-Operator-Runtime]]


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-12): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
