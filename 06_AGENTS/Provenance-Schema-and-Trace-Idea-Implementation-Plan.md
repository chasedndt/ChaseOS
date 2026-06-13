---
title: Provenance Schema and trace_idea Implementation Plan
type: implementation-plan
status: seeded — Phase 9 second-wave implementation planning
version: 0.1
created: 2026-04-24
updated: 2026-04-24
owner: Optimus
phase: Phase 9 second-wave
---

# Provenance Schema and trace_idea Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build the first real Phase 9 implementation foothold for provenance lineage and on-demand idea tracing so ChaseOS can validate provenance blocks, attach them to promoted/runtime artifacts, and later power `trace_idea` plus Provenance Explorer honestly.

**Architecture:** Start with the smallest truthful substrate: a canonical schema definition under `runtime/schemas/`, a validator module, and one read-only `trace_idea` workflow path that traverses existing artifacts instead of inventing missing data. Reuse current Phase 8 sidecars, Phase 7 source packages, Phase 9 acquisition artifacts, build logs, and AOR/runtime outputs rather than creating a parallel truth store.

**Tech Stack:** Python stdlib, existing `runtime/` package structure, markdown docs in `06_AGENTS/`, YAML/JSON schemas already present in the repo, pytest for focused verification.

**Implementation status (2026-04-24):**
- Task 1 completed — canonical provenance schema docs + YAML seeded under `runtime/schemas/`
- Task 2 completed — `runtime/schemas/provenance_validator.py` + focused tests live
- Task 3 completed — fixture-backed provenance examples live under `runtime/schemas/fixtures/provenance/`
- Task 4 partially completed — read-only `trace_idea` handler, manifest, role card, AOR dispatch, and focused tests are now seeded
- Task 5 partially completed — `07_LOGS/Trace-Reports/` folder guide + index + report routing seeded
- Task 6 partially completed — narrow Gate-adjacent helper in `runtime/chaseos_gate.py` now checks promoted-note provenance minimums without attempting full CGL enforcement, and `.claude/hooks/ingestion_promotion_guard.py` is the first live caller path for that seam
- Task 7 completed — `runtime/schemas/provenance_migration_notes.md` now defines historical partial-lineage doctrine and related bridge/contract docs are synced to it

---

## Preconditions and Source Docs

Read before implementation:
- `06_AGENTS/Phase9-Adopted-Feature-Specification.md` — Feature 11 `Provenance Schema`, Feature 12 `Context Governance Layer`, Feature 15 `trace_idea`
- `06_AGENTS/Normalization-Provenance-Contract.md`
- `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`
- `06_AGENTS/Summary-Context-Taxonomy-and-Object-Model.md`
- `runtime/source_intelligence/schemas/source_package_schema.md`
- `runtime/acquisition/models.py`
- `runtime/source_intelligence/pipelines/source_package_builder.py`
- `runtime/chaseos_gate.py`

Key existing paths to reuse:
- `runtime/source_intelligence/workspaces/*/source_packages/*.json`
- `runtime/acquisition/`
- `03_INPUTS/00_QUARANTINE/` + sidecars
- `07_LOGS/Build-Logs/`
- `07_LOGS/Agent-Activity/`

Non-goals for this pass:
- full Context Governance Layer implementation
- cross-vault lineage
- automatic truth verification
- Studio UI implementation
- retrofitting every historical artifact in one pass

---

## Task 1: Create the provenance schema directory and canonical schema docs

**Objective:** Establish the runtime-side canonical provenance schema location promised by the Phase 9 spec.

**Files:**
- Create: `runtime/schemas/provenance_schema.md`
- Create: `runtime/schemas/provenance_schema.yaml`
- Modify: `06_AGENTS/Phase9-Adopted-Feature-Specification.md` only if a path clarification note is needed later

**Step 1: Write the schema markdown doc**

Document at minimum:
- required fields
- optional fields
- append-only rule
- stage vocabulary (`raw_capture`, `quarantine`, `normalized`, `source_package`, `briefing_input`, `generated`, `reviewed`, `promoted`, `canonical`)
- verification vocabulary
- lineage-chain entry shape
- relationship to Phase 8 sidecars and SIC source packages

**Step 2: Write the machine-readable YAML schema draft**

Include exact field names such as:
- `source_ids`
- `processing_stage`
- `verification_status`
- `lineage_chain`
- `created_at`
- `last_modified_at`
- `operator_reviewed_at`
- `source_refs`
- `audit_refs`

**Step 3: Verify the new paths exist**

Run:
```bash
python - <<'PY'
from pathlib import Path
for p in [
    Path('runtime/schemas/provenance_schema.md'),
    Path('runtime/schemas/provenance_schema.yaml'),
]:
    print(p, p.exists())
PY
```
Expected: both paths print `True`.

---

## Task 2: Add a validator module for provenance blocks

**Objective:** Create the first runtime-side enforcement foothold for provenance shape validation.

**Files:**
- Create: `runtime/schemas/provenance_validator.py`
- Create: `runtime/schemas/__init__.py`
- Test: `runtime/tests/test_provenance_validator.py`

**Step 1: Write failing tests for minimum valid provenance blocks**

Cover:
- valid minimal provenance dict
- missing required field fails
- invalid `processing_stage` fails
- invalid `verification_status` fails
- malformed lineage-chain entry fails

**Step 2: Implement a minimal stdlib validator**

Provide functions like:
```python
def validate_provenance_block(data: dict) -> list[str]: ...
def is_valid_provenance_block(data: dict) -> bool: ...
```

Keep it dependency-light and truthful.
No fake migration logic yet.

**Step 3: Run focused tests**

Run:
```bash
pytest runtime/tests/test_provenance_validator.py -q
```
Expected: all tests pass.

---

## Task 3: Define a fixture set that represents current lineage sources honestly

**Objective:** Make provenance design concrete using real current ChaseOS artifact families.

**Files:**
- Create: `runtime/tests/fixtures/provenance/minimal_valid.json`
- Create: `runtime/tests/fixtures/provenance/source_package_linked.json`
- Create: `runtime/tests/fixtures/provenance/acquisition_packet_linked.json`
- Create: `runtime/tests/fixtures/provenance/generated_output_linked.json`

**Step 1: Create a minimal valid fixture**

Use only required fields.

**Step 2: Create lineage fixtures grounded in existing repo structures**

Examples should reference realistic paths such as:
- `runtime/source_intelligence/workspaces/.../source_packages/...json`
- `03_INPUTS/00_QUARANTINE/...`
- `07_LOGS/Build-Logs/...`
- `07_LOGS/Agent-Activity/...`

**Step 3: Extend tests to load and validate fixture files**

Run:
```bash
pytest runtime/tests/test_provenance_validator.py -q
```
Expected: fixture-backed tests pass too.

---

## Task 4: Write a read-only trace model for `trace_idea`

**Objective:** Define the minimum trace traversal contract before writing the workflow.

**Files:**
- Create: `runtime/workflows/trace_idea.py`
- Create: `runtime/workflows/registry/trace_idea.yaml`
- Create: `06_AGENTS/role-cards/trace-idea-readonly.yaml`
- Test: `runtime/tests/test_trace_idea.py`

**Step 1: Write failing tests for read-only lineage traversal**

Cover at minimum:
- trace from a known artifact ID returns ordered lineage items
- unknown ID returns not-found result cleanly
- workflow never writes outside declared log/report destinations
- workflow result clearly distinguishes source artifacts vs derived summaries

**Step 2: Implement minimal traversal behavior**

For this first pass, allow `trace_idea` to search and chain across:
- provenance blocks when present
- source package IDs
- acquisition artifact IDs
- file/path refs in logs and artifacts
- build-log / agent-activity references

Prefer honest partial traces over invented completeness.
If lineage is missing, report the gap explicitly.

**Step 3: Register the workflow and role card**

Manifest should be read-only / report-only.
Role card should forbid:
- protected writes
- canonical mutation
- external commands
- network access unless already justified elsewhere

**Step 4: Run focused tests**

Run:
```bash
pytest runtime/tests/test_trace_idea.py -q
```
Expected: the read-only trace workflow passes its focused tests.

---

## Task 5: Add report routing for trace output

**Objective:** Give `trace_idea` a clean, bounded output destination that fits existing log doctrine.

**Files:**
- Create: `07_LOGS/Trace-Reports/Trace-Reports-Index.md`
- Create: `07_LOGS/Trace-Reports/TRACE-REPORTS-Folder-Guide.md`
- Modify: `06_AGENTS/Vault-Map.md`
- Modify: `06_AGENTS/Feature-Register.md`
- Modify: `07_LOGS/Build-Logs/Build-Logs-Index.md` if the implementation session produces a build log

**Step 1: Define the report folder guide**

Clarify:
- what belongs in Trace Reports
- how this differs from Build Logs and Agent Activity
- naming convention
- read-only lineage/report role

**Step 2: Add the index file**

Create the discovery surface for trace reports.

**Step 3: Route `trace_idea` output there**

Expected naming:
```text
07_LOGS/Trace-Reports/YYYY-MM-DD-trace-[slug].md
```

---

## Task 6: Add Gate-adjacent validation hook for promoted-note provenance minimums

**Objective:** Prepare the minimum enforcement seam without overbuilding full CGL.

**Files:**
- Modify: `runtime/chaseos_gate.py`
- Create or modify tests under: `runtime/tests/test_gate_provenance_minimums.py`

**Step 1: Write failing tests**

Cover:
- promoted note missing provenance minimums -> blocked
- note with valid minimum provenance -> allowed by provenance check layer
- provenance check only applies where relevant

**Step 2: Implement a narrow, opt-in helper**

Example function:
```python
def check_provenance_minimums(path: str, frontmatter: dict) -> tuple[bool, str]: ...
```

Do not turn this into a full migration or CGL system yet.
Only add the minimum seam.

**Step 3: Run focused tests**

Run:
```bash
pytest runtime/tests/test_gate_provenance_minimums.py -q
```
Expected: tests pass.

---

## Task 7: Document migration posture for existing artifacts

**Objective:** Make sure historical incompleteness is handled honestly instead of hidden.

**Files:**
- Create: `runtime/schemas/provenance_migration_notes.md`
- Modify: `06_AGENTS/Provenance-Explorer-and-Chronology-Browser-Standalone-Application.md`
- Modify: `06_AGENTS/Normalization-Provenance-Contract.md`

**Step 1: Record what can be retrofitted now**

Examples:
- source package IDs
- acquisition artifact IDs
- build-log refs
- agent-activity refs
- capture IDs / hashes where already available

**Step 2: Record what cannot be reconstructed perfectly**

Examples:
- missing historical transformation steps
- outputs created before provenance schema existed
- incomplete verification status history

**Step 3: Explicitly define partial-trace honesty rule**

A partial lineage is allowed.
A fabricated complete lineage is not.

---

## Task 8: Write the implementation build log and truth-sync docs

**Objective:** Keep the repo navigable and OS-aligned once implementation starts.

**Files:**
- Create: `07_LOGS/Build-Logs/YYYY-MM-DD-ChaseOS-[agent]-provenance-schema-trace-idea-implementation-pass.md`
- Modify: `07_LOGS/Build-Logs/Build-Logs-Index.md`
- Modify: `06_AGENTS/Feature-Fit-Register.md`
- Modify: `06_AGENTS/Feature-Register.md`
- Modify: `06_AGENTS/Markdown-to-Standalone-Bridge.md`
- Modify: `06_AGENTS/Vault-Map.md`

**Step 1: Record what was actually implemented**

**Step 2: Sync status lines**

Update seeded/planned wording only where true.
Do not overstate completion.

**Step 3: Verify all new artifacts are indexed**

Run:
```bash
python - <<'PY'
from pathlib import Path
checks = [
    'runtime/schemas/provenance_schema.md',
    'runtime/schemas/provenance_schema.yaml',
    'runtime/schemas/provenance_validator.py',
    'runtime/workflows/trace_idea.py',
    'runtime/workflows/registry/trace_idea.yaml',
    '06_AGENTS/role-cards/trace-idea-readonly.yaml',
    '07_LOGS/Trace-Reports/Trace-Reports-Index.md',
]
for item in checks:
    p = Path(item)
    print(f'{item}:', 'OK' if p.exists() else 'MISSING')
PY
```
Expected: all `OK` once implementation is complete.

---

## Verification Checklist

- [ ] provenance schema docs exist under `runtime/schemas/`
- [ ] validator module exists and tests pass
- [ ] fixture lineage examples exist and validate
- [ ] `trace_idea` workflow exists, is read-only, and is registered
- [ ] report routing exists under `07_LOGS/Trace-Reports/`
- [ ] Gate has a minimal provenance-minimum seam
- [ ] migration notes document partial-history honesty
- [ ] build-log index and routing docs are updated

---

## Why This Aligns with the Overall ChaseOS Operating System

This plan advances ChaseOS at the operating-system level, not just as schema work.

- **Constitutional traceability:** it turns provenance from an architectural promise into a real governed substrate.
- **Runtime honesty:** `trace_idea` is explicitly read-only and allowed to return partial traces instead of fake certainty.
- **Phase continuity:** it connects Phase 8 sidecars, Phase 7 source packages, Phase 9 acquisition artifacts, and future Phase 10 provenance explorer surfaces.
- **Gate alignment:** it creates a minimum enforcement seam without pretending Context Governance Layer is already built.

---

## Current Verdict

The next correct implementation-facing move is not another abstract bridge pass.
It is to create the first real provenance substrate and a truthful read-only lineage workflow.

That is how ChaseOS moves from “we want provenance-aware surfaces” to “the OS can actually validate lineage and trace an idea back through its governed history.”

---

*Graph links: [[Normalization-Provenance-Contract]] · [[Provenance-Explorer-and-Chronology-Browser-Standalone-Application]] · [[Summary-Context-Taxonomy-and-Object-Model]] · [[Phase9-Adopted-Feature-Specification]] · [[Acquisition-Normalization-Layer]] · [[Autonomous-Operator-Runtime]] · [[ChaseOS-Gate]]*

*Provenance-Schema-and-Trace-Idea-Implementation-Plan.md — v0.1 | Created: 2026-04-24 | Owner label: Optimus*


## Graph Hygiene Governance Links

*Auto-wired by vault_hygiene (2026-05-06): [[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]] . [[06_AGENTS/Vault-Map|Vault-Map]]*
