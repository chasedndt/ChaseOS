---
title: Project Cockpit and Workspace Browser Standalone Application
type: implementation-bridge-plan
status: seeded — next concrete application of the markdown-to-standalone bridge for project/workspace surfaces
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 -> Phase 10 bridge
---

# Project Cockpit and Workspace Browser Standalone Application

> This document applies the markdown-to-standalone bridge to the operator-facing project/workspace slice.
> It defines how future ChaseOS standalone/operator surfaces should expose Project-OS files, SIC workspaces, recent outputs, and workspace-mode context as first-class operating surfaces rather than raw file navigation.

---

## 1. Purpose

ChaseOS already has the structural pieces for project and workspace visibility:
- Project-OS files under `01_PROJECTS/`
- SIC workspace structures under `runtime/source_intelligence/`
- runtime/workflow/output layers that produce project-relevant artifacts
- summary-context and bridge docs that explain how outputs should be interpreted

What is still missing is an explicit worked application for how those pieces should become future **project cockpit** and **workspace browser** surfaces.

This document answers:
- how a future standalone should surface active project state,
- how SIC workspace objects should be browsed without losing provenance/governance meaning,
- how project and workspace surfaces should relate to runtime, approval, and summary layers,
- and how ChaseOS can replace raw markdown-path navigation with operator-legible cockpit views without creating a second unmanaged truth store.

This remains a planning/application artifact.
It does **not** replace Project-OS files, SIC workspace objects, or current markdown routing as source of truth.

---

## 2. Scope of This Application Pass

Included in this pass:
- `01_PROJECTS/**/[Project]-OS.md`
- `06_AGENTS/SIC-Architecture.md`
- `runtime/source_intelligence/`
- `06_AGENTS/Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application.md`
- `06_AGENTS/Workflow-Registry-and-Role-Cards-Standalone-Application.md`
- `06_AGENTS/Standalone-Summary-Context-Layer.md`
- `06_AGENTS/Summary-Context-Taxonomy-and-Object-Model.md`

Not included yet:
- final Studio implementation
- mutation-capable project editing UI
- full SIC workspace UI backend
- multi-workspace cross-workspace orchestration views
- deep graph-substrate visualization beyond project/workspace operator views

---

## 3. Current Markdown-Era Roles

### A. Project operating layer
Project-OS files are the canonical operating-state surface for live projects.
They hold:
- mission
- status
- goals
- open loops
- links to relevant knowledge, logs, and artifacts

### B. Workspace/source-intelligence layer
SIC workspaces and source packages provide the research/evidence environment for operator reasoning and structured output generation.
They hold:
- grouped source sets
- retrieval/index state
- workspace-local outputs
- evidence-grounded context for downstream workflows and decisions

### C. Current operating pattern
Today ChaseOS preserves these distinctions:
- Project-OS = canonical project operating truth
- SIC workspace = evidence/research workspace, not canonical project truth by default
- generated outputs = typed operating artifacts that may inform projects but do not silently become project truth
- runtime/workflow summaries = derivative surfaces, not replacements for Project-OS state

The future standalone must preserve those distinctions instead of flattening project files, workspaces, and outputs into one generic “project page.”

---

## 4. Standalone Surface Families for This Slice

| Current artifact family | Standalone family | Primary standalone surface |
|---|---|---|
| Project-OS files | Project Operating Record | project cockpit |
| SIC workspace objects | Workspace Record | workspace browser |
| source packages / workspace-local outputs | Evidence Workspace Record | workspace detail / evidence panel |
| project/workspace-linked summaries | Summary Context View | project activity feed / workspace result panel |
| project/workspace routing docs | Navigation Context View | cockpit/workspace sidebars and link panels |

---

## 5. Concrete Mapping Table

| Current path | Current role | Future standalone role | Key fields / behaviors that must survive |
|---|---|---|---|
| `01_PROJECTS/**/[Project]-OS.md` | canonical project operating file | project operating record | mission, status, goals, open loops, project-linked truth posture |
| `runtime/source_intelligence/workspaces/` | SIC workspace state | workspace record | grouped source sets, retrieval state, workspace-local output posture |
| `runtime/source_intelligence/schemas/workspace_schema.md` | workspace contract | workspace schema inspector | workspace identity, source grouping, output semantics |
| `runtime/source_intelligence/schemas/source_package_schema.md` | source package contract | source package schema inspector | source identity, provenance, chunk/evidence semantics |
| `06_AGENTS/SIC-Architecture.md` | SIC subsystem doctrine | workspace-browser governance node | workspace purpose, local-first/provider-pluggable rule, Phase 10 SIC browser intent |
| project-linked build logs / operator briefs / outputs | project-facing summary artifacts | project activity feed | advisory vs operating vs proposal posture |
| workspace-linked evidence/summary outputs | workspace-facing summary artifacts | workspace result / evidence panel | evidence-grounded output posture, workspace-local vs promoted distinction |
| `06_AGENTS/Standalone-Summary-Context-Layer.md` + taxonomy docs | summary interpretation layer | project/workspace summary context panel | routing surface, authority posture, promotion posture, source posture |

---

## 6. Recommended Standalone Views

### A. Project Cockpit
This should answer:
1. what this project is,
2. what state it is in,
3. what the important current goals/open loops are,
4. what recent outputs/workflows/summaries matter,
5. and what needs review or action.

Recommended panels:
1. **Project operating summary**
   - mission
   - status
   - goals
   - open loops
2. **Recent project-linked outputs**
   - operator briefs
   - build logs
   - workflow outputs
   - review/proposal items
3. **Project runtime context**
   - recent runtime involvement
   - approval/review status where relevant
4. **Knowledge / evidence links**
   - related SIC workspaces
   - related knowledge notes
   - related logs/artifacts

### B. Workspace Browser
This should answer:
1. what workspaces exist,
2. what sources each contains,
3. what outputs each has produced,
4. and how each workspace relates to broader project/runtime work.

Recommended panels:
1. **Workspace list**
   - workspace ID
   - topic/project alignment
   - source count
   - recent output count
2. **Workspace detail panel**
   - source packages
   - evidence/retrieval posture
   - latest outputs
   - workspace-local status
3. **Project alignment panel**
   - linked project(s)
   - whether outputs are advisory, promoted, or review-facing
4. **Output/result panel**
   - summaries
   - synthesis drafts
   - FAQs
   - project-relevant derivations

### C. Project / Workspace Cross-Link Panel
This is the place where the system shows how project truth and workspace evidence relate without collapsing them.

Recommended panels:
1. **Project truth side**
   - canonical operating state
2. **Workspace evidence side**
   - source/evidence context
3. **Derived-output bridge**
   - typed summaries/results linking the two
4. **Promotion/review posture**
   - whether anything should remain workspace-local, become a proposal, or inform project truth

---

## 7. Relationship to the Summary Context Layer

This slice depends heavily on the Summary Context Layer.

Without typed summary context:
- workspace outputs can look like canonical project truth,
- project cockpit cards can hide whether a result is advisory or review-needed,
- evidence-grounded outputs can be mistaken for promoted state,
- project-facing summaries can lose provenance back to the workspace/source layer.

The Summary Context Layer already established that outputs should carry:
- runtime identity
- output class
- authority posture
- source posture
- routing surface
- promotion/review posture

For project/workspace surfaces, that means:
- a workspace summary should look like a workspace artifact,
- a project cockpit summary should show whether it is canonical project state, advisory output, or proposal,
- and the bridge between workspace and project should remain typed and traceable.

That is what keeps project/workspace views aligned with ChaseOS as an operating system rather than becoming generic productivity dashboards.

---

## 8. Service-Layer Boundary Rules

The standalone service layer for this slice should preserve the distinctions ChaseOS already relies on.

### Project-OS remains canonical project truth
A project cockpit is a surface over Project-OS truth, not a replacement truth store.

### SIC workspaces remain evidence/reasoning surfaces
Workspace browsers should not silently promote workspace-local results into project or knowledge truth.

### Workspace outputs must retain their posture
Evidence-grounded or generated outputs must keep their authority/promotion posture visible.

### Project and workspace must stay linked but distinct
A project may depend on a workspace.
A workspace may inform a project.
Neither should erase the role of the other.

### Operator convenience must not erase provenance
Cockpit cards and workspace tiles may be friendly, but they must remain traceable back to project files, workspace records, and source/evidence objects.

---

## 9. Suggested Data Model Direction

This slice suggests ChaseOS likely needs at least these additional standalone object families:
- `project_operating_record`
- `workspace_record`
- `source_package_record`
- `project_workspace_link_record`
- `project_workspace_summary_record`

And likely these specialized presentation layers:
- `project_cockpit_view`
- `workspace_browser_view`
- `workspace_detail_view`
- `project_workspace_bridge_panel`

That matters because project and workspace surfaces are not just folders in the UI.
They are distinct operating concepts with different authority and provenance rules.

---

## 10. What This Application Pass Proves

This pass proves the bridge can extend into project/workspace operator surfaces.
It clarifies:
- how Project-OS files become cockpits,
- how SIC workspaces become browseable evidence environments,
- how project and workspace layers should remain linked but distinct,
- and how typed summaries should mediate between evidence, workflow output, and project operating state.

This makes the future standalone operator experience more concrete because project/workspace browsing is where many of the previously defined runtime/workflow/summary layers start to converge.

---

## 11. Alignment with the Overall ChaseOS Operating System

This pass aligns with ChaseOS as an operating system in four important ways.

### A. It preserves canonical-vs-derived distinctions
Project-OS files remain operating truth.
Workspaces remain evidence/reasoning environments.
Outputs remain typed intermediates unless promoted or written back through governed paths.

### B. It makes operator-facing project navigation OS-native
A future operator should be able to navigate active projects and evidence workspaces as first-class OS surfaces instead of raw file trees.

### C. It connects runtime/workflow output back to project work
This is where the earlier runtime/workflow/summary bridge passes begin to pay off: outputs can surface in project cockpits and workspace browsers with proper posture and provenance.

### D. It improves long-term system legibility
ChaseOS becomes much more usable when projects, workspaces, runtime outputs, and review/proposal states can be inspected together without losing the structural boundaries between them.

That is operating-system behavior, not just note browsing.

---

## 12. Recommended Next Application Passes

After this slice, the strongest next passes would be:
1. **consolidated operator cockpit surface** where project, runtime, approval, and coordination views begin to merge
2. **knowledge navigator / domain browser** to complement the project/workspace side
3. **settings / provider-config / scaffold surfaces** to round out the operator-facing product shell

---

## 13. Current Verdict

A future ChaseOS standalone should not treat Project-OS files and SIC workspaces as just two kinds of folders.
It should treat them as **different operating surfaces**:
- project cockpit = canonical operating state
- workspace browser = evidence/reasoning environment
- summary bridge = typed link between the two

That is how project/workspace surfaces align with the overall ChaseOS operating system.

---

*Graph links: [[Markdown-to-Standalone-Bridge]] · [[SIC-Architecture]] · [[Runtime-Shell-Approval-Center-and-Runtime-Browser-Standalone-Application]] · [[Standalone-Summary-Context-Layer]] · [[ChaseOS-Studio-Architecture]]*

*Project-Cockpit-and-Workspace-Browser-Standalone-Application.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
