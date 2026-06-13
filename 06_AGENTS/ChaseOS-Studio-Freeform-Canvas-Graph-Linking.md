---
title: ChaseOS Studio Freeform Canvas and Graph Node Linking
status: seeded-spec / not-built
phase: Phase 10E — Studio Canvas / Whiteboard / Spatial Mode
created: 2026-05-12
owner_runtime_lane: Hermes/Optimus PM
authority: workspace-local draft surface; canonical mutation blocked until Gate
---

# ChaseOS Studio Freeform Canvas and Graph Node Linking

> This is the Phase 10E product/technical specification for a future Studio Canvas / Whiteboard lane.
> It seeds the deferred spatial investigation mode without activating canvas writes, browser/Excalidraw control, graph mutation, provenance writes, or canonical promotion.

## 1. Purpose

Studio Canvas gives the operator a freeform spatial board for investigation, architecture mapping, clustering, and working-memory arrangement while staying attached to the ChaseOS graph model.

The core product idea is not “a second graph editor.” It is a workspace-local canvas layer that can place visual cards, annotations, groups, and graph-node references around the existing graph. Canvas state helps the operator think spatially, but it does not become canonical truth by existing.

## 2. Product Position

Canvas / Whiteboard is Phase 10E, after the graph-first Studio lane.

Current live repo truth already contains these relevant foundations:

- Read-only graph scanner/parser and derived graph contracts.
- Read-only graph view, typed graph/trust overlays, and graph provenance inspector.
- Approval-gated controlled node create/edit and visual link approval flows.
- Browser/Excalidraw proof surfaces that demonstrate bounded public canvas reachability/drawing proof separately from Studio authority.
- Studio service-layer and approval patterns for governed writes.

Canvas should compose those surfaces instead of bypassing them.

## 3. Non-Negotiable Authority Boundary

Canvas outputs are workspace-local drafts.

They are not:

- canonical graph truth;
- promoted knowledge;
- direct vault mutations;
- graph-index persistence;
- provenance writes;
- source-package writes;
- browser/Excalidraw automation authority;
- permission to create links or nodes without the existing service layer and Gate checks.

A canvas object can reference a graph node, a source file, a provenance report, or an approval packet. That reference is a pointer in the canvas draft. It does not alter the target.

Promotion from canvas to canonical knowledge, graph edges, markdown links, source records, or provenance records requires a separate Gate-governed lower-lane contract and explicit operator approval.

## 4. Canvas Data Model

The first data model should be JSON-serializable and workspace-local. It must not require a new database.

Candidate storage surface:

```text
runtime/studio/canvas_drafts/<canvas_id>.json
```

Future operator-approved export targets may write under `07_LOGS/Studio-Canvas/` for proof/report artifacts, but the first product substrate should keep editable drafts in a runtime-local Studio lane.

### 4.1 CanvasDocument

```json
{
  "schema_version": "studio_canvas.v1",
  "canvas_id": "canvas_<digest>",
  "title": "Investigation board",
  "created_at": "2026-05-12T00:00:00Z",
  "updated_at": "2026-05-12T00:00:00Z",
  "workspace_root_ref": ".",
  "authority": {
    "canonical_mutation_allowed": false,
    "graph_mutation_allowed": false,
    "promotion_requires_gate": true,
    "browser_control_allowed": false
  },
  "objects": [],
  "links": [],
  "view_state": {},
  "provenance": {}
}
```

### 4.2 CanvasObject

Each object is a visual element. Required object families:

| Kind | Purpose | Canonical effect |
|---|---|---|
| `graph_node_ref` | Place an existing graph node on the board | None; pointer only |
| `note_card` | Draft operator annotation | None; draft only |
| `group` | Spatial cluster/area label | None; draft only |
| `image_ref` | Workspace-local image/proof reference | None; pointer only |
| `artifact_ref` | Build log, trace report, approval packet, or audit reference | None; pointer only |
| `proposal_card` | Future action proposal preview | None until approval path consumes it |

Minimum shape:

```json
{
  "object_id": "obj_<digest>",
  "kind": "graph_node_ref",
  "label": "Hermes Runtime Profile",
  "position": {"x": 120, "y": 80},
  "size": {"width": 220, "height": 96},
  "style": {"color": "runtime", "locked": false},
  "target_ref": {
    "type": "graph_node",
    "node_id": "derived-node-id",
    "source_path": "06_AGENTS/Hermes-Runtime-Profile.md",
    "trust_state": "derived"
  },
  "draft_text": null,
  "created_by": "operator-or-runtime-label",
  "updated_at": "2026-05-12T00:00:00Z"
}
```

### 4.3 CanvasLink

Canvas links are visual relationships between canvas objects.

They are not graph edges unless a later approval-gated action converts them through the existing visual-link approval path.

```json
{
  "link_id": "link_<digest>",
  "source_object_id": "obj_a",
  "target_object_id": "obj_b",
  "label": "related hypothesis",
  "kind": "canvas_visual_link",
  "canonical_edge_ref": null,
  "conversion": {
    "can_propose_graph_link": true,
    "requires_approval": true,
    "proposal_surface": "visual-link-approval-flow"
  }
}
```

## 5. Graph Node Linking UX

The UX should keep graph truth and canvas draft state visibly separate.

### Required interactions

1. From Graph View: “Send to Canvas” on a selected graph node.
2. From Node Inspector: “Pin to Canvas” for the inspected node.
3. From Canvas: search/select an existing graph node and place it.
4. From Canvas object: open read-only Node Inspector for the target.
5. From Canvas visual link: “Propose graph link” only as a pending approval preview, reusing the visual-link approval flow.
6. From Canvas note card: “Draft promotion proposal” only as a preview packet; no direct canonical write.

### Visual requirements

Canvas cards must show source posture:

- `graph_node_ref`: derived/existing graph node badge.
- `note_card`: workspace-local draft badge.
- `artifact_ref`: audit/log/proof badge.
- `proposal_card`: approval-required badge.

The canvas itself should show a persistent boundary banner:

> Workspace-local canvas draft. This board does not mutate graph truth or canonical knowledge. Promotion and graph writes require Gate approval.

## 6. Provenance and Read-Only Behavior

Canvas can display provenance; it cannot create provenance truth.

Allowed read-only behavior:

- show graph provenance inspector summaries for referenced nodes;
- show source path, node ID, trust state, and provenance chain if already available;
- show build-log / trace-report / approval-packet references as linked artifacts;
- show whether a canvas card is backed by a canonical note, generated artifact, runtime audit, or draft-only text.

Forbidden first-pass behavior:

- writing provenance sidecars;
- changing trust state;
- creating source-package records;
- rewriting graph snapshot artifacts;
- promoting canvas annotations to `02_KNOWLEDGE/`;
- running browser/Excalidraw control from a canvas action.

## 7. Implementation Task Split

This spec should be implemented as separate bounded passes, not one large canvas build.

### Task A — Canvas Draft Schema and Read-Only Loader

Owner: Studio/runtime implementation lane.

Acceptance criteria:

- Add a JSON-serializable `CanvasDocument` model and validator.
- Load seeded canvas fixture(s) from a workspace-local draft path.
- Reject path traversal and non-JSON inputs.
- Report `canonical_mutation_allowed=false`, `graph_mutation_allowed=false`, and `promotion_requires_gate=true` in every response.
- Focused tests prove no markdown/canonical writes occur.

### Task B — Graph Node Reference Resolver

Owner: Studio graph lane.

Acceptance criteria:

- Resolve `graph_node_ref` objects through existing graph/node-inspector contracts.
- Return missing-node, stale-node, and source-path-moved states explicitly.
- Do not persist graph IDs, mutate graph snapshots, or write node IDs.
- Focused tests cover existing node, missing node, and stale source reference.

### Task C — Canvas Shell Panel Contract

Owner: Studio UI lane.

Acceptance criteria:

- Expose a read-only `chaseos studio canvas-panel --json` contract.
- Mount a Canvas tab/panel inside the existing shell as a read-only visualization over fixture data.
- Render boundary banner and source/draft badges.
- No drag/save/edit yet unless a later pass adds explicit draft-save authority.

### Task D — Workspace-Local Draft Save Approval Boundary

Owner: Studio service/Gate lane.

Acceptance criteria:

- Define which canvas draft writes are allowed locally and which require approval.
- Draft saves may only affect `runtime/studio/canvas_drafts/` or a declared workspace-local equivalent.
- Any conversion into graph links, markdown notes, provenance records, source packages, or canonical knowledge remains blocked and preview-only.
- Tests prove protected/canonical targets are denied.

### Task E — Visual Link Proposal Bridge

Owner: existing visual-link approval lane.

Acceptance criteria:

- Convert selected canvas visual links into preview-only `visual-link-approval-flow` proposals.
- Keep canvas link IDs separate from graph edge IDs.
- Show exact source/target graph node references and approval posture.
- No approved execution unless the existing visual-link path already authorizes the target mutation.

### Task F — Optional Excalidraw / Browser Runtime Proof Mapping

Owner: browser-runtime proof lane, only if separately approved.

Acceptance criteria:

- Treat Excalidraw as proof/export/interop only, not the first Studio canvas authority substrate.
- No live browser control from Canvas without a dedicated approval packet.
- Any Excalidraw import/export remains workspace-local proof material until Gate promotion.

## 8. Phase 9-and-Below Dependencies

The following dependencies must stay owned by lower lanes:

| Dependency | Owner surface | Canvas behavior before dependency is built |
|---|---|---|
| Canonical promotion | Gate / AOR / promotion workflows | Preview only |
| Graph mutation backend | Studio service layer + graph substrate | Use existing approval-gated link/node flows only |
| Browser/Excalidraw control | Browser Runtime / SiteOps / approval packets | No direct canvas control |
| Provenance writes | Provenance schema / Gate-adjacent helpers | Read-only display only |
| Source-package writes | SIC/acquisition/source intelligence lanes | Link to existing artifacts only |
| Runtime dispatch | AOR / Agent Bus / Runtime Cockpit | No canvas-origin runtime dispatch |

## 9. Acceptance Criteria for This Spec Lane

The Canvas/Whiteboard lane is seeded when:

- a product/technical spec defines the workspace-local canvas object model;
- graph-node linking UX is explicitly pointer-only until a governed conversion path is invoked;
- provenance behavior is read-only;
- browser/Excalidraw control is separated from Studio canvas authority;
- implementation tasks are split into schema, resolver, panel, save-boundary, proposal bridge, and optional proof/export lanes;
- Roadmap, Feature Fit, Studio architecture/engineering docs, Vault Map, and Build Logs index can route future workers here.

## 10. Open Loops

- Decide the exact editable draft storage path after the first implementation pass evaluates Studio runtime packaging constraints.
- Decide whether canvas draft saves require approval by default or can be local-only writes under a constrained draft path.
- Design visual diff/review for converting canvas links/cards into graph/markdown proposals.
- Decide whether Excalidraw import/export is a separate interoperability feature or a long-term optional proof-only lane.

## 11. ChaseOS OS Alignment

This keeps Canvas aligned with the ChaseOS operating-system model: Studio presents a spatial interface over lower-layer truth, but the OS still owns authority. The graph substrate remains derived/rebuildable, Gate owns canonical promotion, Browser Runtime owns browser proofs, and AOR/Agent Bus own runtime dispatch. Canvas is useful because it gives the operator a workspace-local thinking surface linked to real nodes; it is safe because those links are pointers until governed service-layer actions convert them.

*Graph links: [[ChaseOS-Studio-Architecture]] · [[Phase10-Desktop-Shell-Engineering-Plan]] · [[Graph-Substrate-Architecture]] · [[ChaseOS-Gate]] · [[Feature-Fit-Register]] · [[Vault-Map]] · [[Build-Logs-Index]]*
