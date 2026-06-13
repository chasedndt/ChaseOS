---
title: Graph Substrate Architecture
type: architecture-doc
status: active — pass 2 complete 2026-04-14; stdlib-only; 87 tests passing
created: 2026-04-10
version: 2.0
phase: Phase 9 (subsystem); Phase 10 (Studio integration surface)
---

# ChaseOS Graph Substrate Architecture

> The graph substrate provides deterministic structure extraction, persistent graph artifacts,
> topology-aware clustering, and graph-first routing for corpus, repo, and runtime navigation.
>
> It is NOT a GraphRAG product. It is NOT a Studio UI layer. It is NOT an autonomous promotion engine.
> It is a bounded architectural subsystem that makes the ChaseOS runtime structure legible.
> Deferred durable graph storage and durable node-ID authority are specified separately in `06_AGENTS/Persisted-Graph-Engine-and-Durable-Node-ID-Layer.md`; that contract does not activate canonical graph mutation or hidden Studio persistence.

---

## 1. What This Is

The ChaseOS Graph Substrate is a native graph infrastructure layer for:

- **Deterministic structure extraction** before LLM or semantic reasoning
- **Persistent graph artifacts** — serializable snapshots of extracted structure
- **Deferred durable graph-store path** — future explicit graph-store roots and durable node identity are governed by `06_AGENTS/Persisted-Graph-Engine-and-Durable-Node-ID-Layer.md`, not by implicit UI/state writes
- **Topology-aware clustering** — community detection over extracted graphs
- **Graph-first routing** — narrow read targets before wide file search
- **Operator-readable graph reports** — structured analysis for human review
- **Future Phase 9 / 10 integration** — foundation for runtime and Studio graph surfaces

### What It Is Not

- Not a replacement for SIC (Source Intelligence Core) — the graph substrate maps structure; SIC handles content
- Not a canonical knowledge promotion path — graph inference does not become vault truth
- Not a UI layer — Phase 10 Studio will build on top of this; this pass is infrastructure only
- Not dependent on NetworkX, rustworkx, or any external graph library

---

## 2. Location

```
runtime/graph/
  __init__.py           — public API exports (pass 1 + pass 2)
  artifact.py           — canonical GraphSnapshot model; Confidence / NodeType / Relation vocabularies
  index.py              — in-memory index layer
  extractor.py          — deterministic extraction (Python AST, YAML, Markdown)
  topology.py           — algorithm layer (pure Python)
  reporter.py           — operator report generation
  query.py              — graph-first query/routing service
  builder.py            — pipeline orchestrator (pass 1); resolve_imports_pass flag (pass 2)
  resolver.py           — cross-file import resolution; SymbolIndex; IMPORT_RESOLVES_TO edges  [pass 2]
  diff.py               — snapshot diffing; SnapshotDiff; render_diff_report                   [pass 2]
  advisory.py           — AOR advisory narrowing seam; AdvisoryNarrowingResult                 [pass 2]
  test_graph_substrate.py — 87 tests, all passing (58 pass 1 + 29 pass 2)
```

---

## 3. Architecture Layers

### Layer A — Graph Artifact (Source of Truth)

`runtime/graph/artifact.py`

The **GraphSnapshot** is the canonical artifact. Everything else is derived from it.

```
GraphSnapshot
  snapshot_id: str         — UUID, unique per build
  created_at: str          — ISO 8601 UTC
  vault_root: str          — absolute path at extraction time
  extraction_scope: list   — vault-relative paths extracted
  nodes: list[GraphNode]   — all extracted nodes
  edges: list[GraphEdge]   — all extracted edges
  community_assignments: dict[str, int]  — node_id → community_id
  build_info: dict         — extraction stats, timing, errors
  metadata: dict           — free-form user/system metadata
```

**Node model:**
```
GraphNode
  node_id: str    — 16-char SHA-256 hex, deterministic from (type + source_file + label)
  label: str      — human-readable name
  node_type: str  — NodeType constant (see below)
  source_file: str — vault-relative path
  source_line: Optional[int]
  domain: Optional[str]   — inferred from path (aor, capture, sic, etc.)
  properties: dict        — type-specific extras
  confidence: str         — EXTRACTED | INFERRED | AMBIGUOUS
  provenance: str         — extraction method description
```

**Edge model:**
```
GraphEdge
  edge_id: str     — 16-char SHA-256 hex, deterministic from (source_id + relation + target_id)
  source_id: str
  target_id: str
  relation: str    — Relation constant (see below)
  confidence: str  — EXTRACTED | INFERRED | AMBIGUOUS
  properties: dict
  provenance: str
```

**Node types (pass 1):**
- `file` — a source file in the corpus
- `python_class` — class definition
- `python_function` — function or method
- `python_import` — imported module/symbol
- `workflow` — AOR workflow manifest
- `manifest_field` — a field within a workflow manifest
- `doc_section` — a heading-delimited section in markdown
- `wikilink_ref` — a wikilink target referenced from a doc
- `frontmatter_key` — a key-value pair from markdown frontmatter

**Relation types (pass 1):**
- `imports` — file imports module/symbol
- `defines` — file or class defines function/class
- `inherits` — class inherits from another
- `references` — doc references another via wikilink
- `workflow_declares` — manifest declares a field
- `workflow_links_file` — manifest references a handler file (INFERRED)
- `file_contains` — file contains a class/function/section

**Confidence semantics:**
- `EXTRACTED` — directly observed from source structure (AST, YAML parse, regex)
- `INFERRED` — derived by pattern or heuristic (e.g., base class reference, handler path inference)
- `AMBIGUOUS` — conflicting signals; requires human review

**ID stability guarantee:** re-extracting the same source always produces the same node_id and edge_id. IDs are content-derived, not position or order derived.

**Serialization:** GraphSnapshot serializes to/from JSON (stdlib). `snapshot.save(path)` and `GraphSnapshot.load(path)` are the persistence interface.

---

### Layer B — In-Memory Index

`runtime/graph/index.py`

GraphIndex builds derived lookup tables over a snapshot. The snapshot is always canonical; indexes are rebuilt from it.

**Indexes built:**
- `node_by_id: dict[str, GraphNode]`
- `outgoing_edges: dict[str, list[GraphEdge]]`
- `incoming_edges: dict[str, list[GraphEdge]]`
- `edges_by_relation: dict[str, list[GraphEdge]]`
- `nodes_by_source_file: dict[str, list[GraphNode]]`
- `nodes_by_type: dict[str, list[GraphNode]]`
- `nodes_by_domain: dict[str, list[GraphNode]]`
- `community_by_node: dict[str, int]`
- `nodes_by_community: dict[int, list[str]]`

**Traversal operations:**
- `neighbors_out(node_id)` → outgoing neighbors
- `neighbors_in(node_id)` → incoming neighbors
- `neighbors_all(node_id)` → all neighbors (deduplicated)
- `degree(node_id)`, `in_degree(node_id)`, `out_degree(node_id)`
- `adjacency_list(directed)` → plain dict for algorithm use

**Design:** No mutable graph library objects. Dict and list operations only. O(1) or O(k) for all indexed operations.

---

### Layer C — Algorithm / Topology Layer

`runtime/graph/topology.py`

Pure-Python topology algorithms. No external library required for pass 1.

**Algorithms implemented:**

| Algorithm | Implementation | Notes |
|-----------|---------------|-------|
| Connected components | BFS (undirected) | Returns sorted list, largest first |
| Community detection | Label propagation (iterative, seed-controlled) | Renumbered 0..N by size |
| Degree centrality | (in + out) / (n - 1) | Normalized |
| Shortest path | BFS (directed or undirected) | Returns node_id path or None |
| Top by degree | Sort over all nodes | Configurable N |
| Isolated nodes | Zero-edge filter | |
| Cross-domain edges | Domain field comparison | |
| Ambiguous/inferred edges | Confidence filter | |
| Community summary | Per-community stats | Dominant type, domain, top members |

**Backend rule:** This layer is replaceable. A future pass could introduce NetworkX or rustworkx behind the same interface without changing callers. The graph library is never the architecture.

---

### Layer D — Extraction Layer

`runtime/graph/extractor.py`

Three deterministic extractors. No LLM calls. No external services. No inference beyond what is directly present in source structure.

**PythonExtractor** (stdlib `ast`):
- Extracts: file nodes, imports, class defs, function defs, methods
- Edges: imports, defines, inherits (INFERRED), file_contains
- Scope: all `.py` files in declared directories
- Excludes: `_tmp_tests`, `__pycache__` by default

**YAMLManifestExtractor** (stdlib `yaml`):
- Extracts: workflow nodes, manifest field nodes
- Edges: workflow_declares, workflow_links_file (INFERRED)
- Scope: `*.yaml` files in declared directories

**MarkdownExtractor** (stdlib `re` + `yaml`):
- Extracts: file nodes, doc_section nodes (headings), wikilink_ref nodes, frontmatter_key nodes
- Edges: file_contains, references
- Scope: `.md` files at declared paths or directories

**Pass 1 default scope:**
- Code: `runtime/aor`, `runtime/workflows`, `runtime/capture`, `runtime/cli`, `runtime/graph`
- Manifests: `runtime/workflows/registry`
- Docs: `CLAUDE.md`, `README.md`, `ROADMAP.md`, selected `06_AGENTS/` docs

**Pass 1 results (real vault):**
- 1667 nodes, 2303 edges extracted from 60 source files
- 0.45s extraction, 0.036s topology
- 70 communities detected
- 1 benign error (_schema.yaml not a mapping — correct fail-open)

---

### Layer E — Report Layer

`runtime/graph/reporter.py`

Generates operator-readable Markdown graph analysis reports.

**Report sections:**
1. Header + snapshot identity
2. Summary statistics (node count, edge count, type breakdown, relation breakdown)
3. Most connected nodes — degree-sorted table (architectural core identification)
4. Community summaries — dominant type, domain breakdown, top members
5. Cross-domain edges — potential coupling concerns
6. Inferred/ambiguous edges — edges requiring human review
7. Isolated nodes — potential orphans or out-of-scope references
8. Suggested next inspections — actionable recommendations
9. Connected components — if >1 component detected
10. Build provenance — snapshot identity, scope, timing

**Design:** Report is proposal-only. It never mutates canonical vault state. It surfaces what to look at, not what is true.

---

### Layer F — Query / Routing Layer

`runtime/graph/query.py`

GraphQueryService: graph-first query and routing over a snapshot.

**Operations:**
- `search(terms, node_types, domains, confidence)` — term-based node search
- `inspect_node(node_id)` → node + neighbors + community + edge details
- `inspect_community(community_id)` → member nodes + internal/external edges + source files
- `shortest_path(source_id, target_id, directed)` → BFS path dict
- `narrow_to_relevant(terms)` → **graph-first narrowing** — returns ranked source files
- `graph_stats()` → summary statistics
- `nodes_by_type(node_type)` → filtered, degree-sorted node list
- `files_for_community(community_id)` → source files for a community

**Graph-first narrowing (key operation):**
The `narrow_to_relevant(terms)` operation is the primary value for operator and runtime use:
1. Search for nodes matching query terms
2. Expand to nodes in the same communities (optional)
3. Score source files by match density × degree
4. Return ranked source file list

This means: **before scanning files, consult the graph to decide what files to read first.**

---

### Layer G — Build Orchestrator

`runtime/graph/builder.py`

Orchestrates the full extraction → dedup → snapshot → index → topology pipeline.

**Public API:**
- `build_snapshot(vault_root, ...)` → GraphSnapshot with community assignments
- `build_index(snapshot)` → GraphIndex
- `build_query_service(snapshot, index)` → GraphQueryService
- `full_pipeline(vault_root, ...)` → (snapshot, index, query_service)
- `save_snapshot(snapshot, output_dir)` → Path

**Deduplication strategy:**
- Nodes: deduplicate by node_id; keep highest-confidence version (EXTRACTED > INFERRED > AMBIGUOUS)
- Edges: deduplicate by edge_id; keep highest-confidence version
- Dangling edges (referencing missing nodes) are dropped before snapshot assembly

---

## 4. Persistent Artifact Storage

Graph snapshots are stored at:
```
07_LOGS/Graph-Snapshots/graph_snapshot_YYYYMMDD-HHMMSS__<id[:8]>.json
```

Graph reports are stored at:
```
07_LOGS/Graph-Reports/YYYY-MM-DD-graph-substrate-<descriptor>.md
```

These are **operator-read artifacts** — not canonical vault state. They are inputs to human review and runtime decisions, not authoritative claims.

---

## 5. Relationship to Other ChaseOS Subsystems

| Subsystem | Relationship |
|-----------|-------------|
| SIC (Source Intelligence Core) | Complementary: SIC handles content/semantic; graph substrate handles structure |
| AOR (Autonomous Operator Runtime) | Potential Phase 9 consumer: graph narrowing to inform `required_reads` |
| graph_hygiene (AOR workflow) | Separate: graph_hygiene scans vault links/frontmatter; substrate extracts code/runtime structure |
| ChaseOS Studio (Phase 10) | Future surface: Studio will expose graph-based navigation built on this substrate |
| Governed knowledge promotion | Not bypassed: graph inference is never autonomously promoted to canonical state |

---

## 6. Pass 2 Additions (2026-04-14)

Three capabilities added on top of the Pass 1 foundation:

### Cross-File Import Resolution (`resolver.py`)

`SymbolIndex` maps Python module dotted paths to FILE node IDs found in the snapshot.
- Exact match: `"runtime.aor.engine"` → `"runtime/aor/engine.py"` file node
- Suffix match: `"aor.engine"` and `"engine"` also resolve
- Class-suffix strip: `"runtime.aor.engine.AOREngine"` → strips uppercase last component → `"runtime.aor.engine"`

`resolve_imports(snapshot)` → list of new INFERRED `IMPORT_RESOLVES_TO` edges (no file I/O; fail-open on misses).

`apply_resolved_edges(snapshot, edges)` → new GraphSnapshot with resolved edges added; build_info gains `resolver_new_edges` and `substrate_version = "2.0"`.

`cross_domain_resolved_edges(snapshot)` → surfaces all IMPORT_RESOLVES_TO edges that cross domain boundaries (e.g., aor → workflows, graph → aor).

Pass 1 had 0 genuine cross-domain edges (import nodes carried the importing file's domain).
Pass 2 with `resolve_imports_pass=True` produces verified cross-domain edges on the real vault.

All resolved edges carry `INFERRED` confidence — module path matching is heuristic, not directly observed.

`full_pipeline(..., resolve_imports_pass=True)` activates the resolver pass. Default is `False` for Pass 1 compatibility.

### Snapshot Diffing (`diff.py`)

`diff_snapshots(before, after)` → `SnapshotDiff` using stable SHA-256 IDs (clean set subtraction; no fuzzy matching).

`SnapshotDiff` reports:
- `added_nodes`, `removed_nodes` — present in one snapshot but not the other
- `changed_nodes` — same node_id, different label/type/source_file/domain/confidence
- `added_edges`, `removed_edges`
- `community_shifts` — nodes whose community_id changed between snapshots
- `is_clean` — True if structurally identical

`render_diff_report(diff)` → Markdown report suitable for `07_LOGS/Graph-Reports/`.

### AOR Advisory Narrowing Seam (`advisory.py`)

`advise_required_reads(query_service, task_context, workflow_id)` → `AdvisoryNarrowingResult`

- Tokenizes task_context + workflow_id into search terms (stopword filtered, deduped, capped at 8)
- Calls `narrow_to_relevant()` on the query service for graph-proximity match
- Returns `candidate_reads` (ranked vault-relative paths) as advisory input

**Advisory boundary:** This output is not authoritative. AOR Stage 5 may use it as a hint. It does not replace manifest-declared required_reads, does not bypass role card permission ceilings, and does not write to the vault. `confidence` is always `"graph-advisory"` (not a Confidence constant).

**Fail-open:** exceptions inside advisory are caught and return an empty result — AOR execution is never blocked by a graph substrate failure.

AOR Stage 5 formal integration (engine calling advisory in the run path) is deferred to Pass 3.

---

## 7. What Is Not Built (Future Passes)

| Capability | Deferred to |
|------------|------------|
| Cross-file call graph inference (function A calls function B in another file) | Pass 3 |
| AOR Stage 5 formal advisory integration (engine wires advisory into run path) | Pass 3 |
| Vault-wide markdown extraction (all 06_AGENTS/ docs) | Pass 3 |
| Incremental diff automation (automated diff on every save_snapshot) | Pass 3 |
| Semantic enrichment / LLM augmentation | Pass 4+ |
| Temporal graph evolution tracking (snapshot series → diff chain) | Later |
| Studio graph visualization surface | Phase 10 |
| External graph library backend (NetworkX, rustworkx) | Optional future adapter |
| Multi-repo graph federation | Later |

---

## 8. Non-Goals

1. Do not promote graph-inferred edges to canonical knowledge without explicit operator action
2. Do not make any graph library the source of truth
3. Do not build autonomous vault mutation from graph analysis
4. Do not treat graph reports as authoritative — they are proposals for human review
5. Do not replace SIC — graph substrate and SIC are complementary, not competing

---

*Graph links: [[Autonomous-Operator-Runtime]] · [[SIC-Architecture]] · [[Feature-Fit-Register]] · [[Vault-Map]] · [[ROADMAP]]*

*Graph-Substrate-Architecture.md — v2.0 | Created: 2026-04-10 | Pass 2 complete: 2026-04-14 | Subsystem: runtime/graph/*
