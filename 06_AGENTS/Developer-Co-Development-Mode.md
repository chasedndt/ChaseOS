---
title: Developer Co-Development Mode
type: architecture
status: COMPLETE / PARKED
version: 1.2
created: 2026-04-22
updated: 2026-04-27
phase: Phase 9 closeout - bounded shadow workflow complete; parked off critical automation path
owner: operator
---

# Developer Co-Development Mode

> ChaseOS-owned feature. Adapter-capable. Not Claude-owned. Not harness-owned.
> The feature runs through adapters. The feature does not belong to any adapter.

---

## 1. What It Is

Developer Co-Development Mode is a ChaseOS-governed feature that provides bounded, draft-only repo intelligence to a developer or operator working on or with ChaseOS.

It operates as a **read-heavy, draft-only, shadow-mode** workflow layer. It reads narrow declared context, produces structured intelligence artifacts, and never writes canonical vault state.

**Core capability:** "What is this part of the system, how does it fit, what matters right now?"

**Five first-subfeature slice (20/80 value):**

| # | Subfeature | What it does |
|---|-----------|--------------|
| 1 | **Repo Truth Explainer** | Reads declared context, explains what the system is in a focus area |
| 2 | **Contradiction / Drift Scan** | Detects mismatch between runtime truth, doc truth, phase truth, and feature truth |
| 3 | **Doc Refresh Proposal Generator** | Drafts update proposals for README, build logs, architecture notes, handovers |
| 4 | **Implementation Brief Generator** | Turns current repo truth into a pass prompt ready for the next engineering session |
| 5 | **Diagram Draft Generator** | Outputs Mermaid / ASCII text proposals — not live GUI rendering |

---

## 2. What It Is Not

- **Not a Claude Code feature** — it runs on ChaseOS governance, not on provider capabilities
- **Not a Hermes feature** — it is a ChaseOS feature that Hermes may run through a declared adapter lane
- **Not a Codex feature** — same; Codex runs through a declared adapter lane
- **Not an OpenClaw feature** — same
- **Not a harness-owned feature** — no harness owns the feature definition
- **Not a canonical writer** — draft-only; no canonical vault state is ever modified by this feature
- **Not an ambient crawler** — reads only declared narrow context; no broad vault traversal
- **Not an LLM orchestration layer** — Phase 9 implementation is structural analysis and template-based generation; LLM generation is a Phase 10 upgrade path

---

## 3. Why It Exists

ChaseOS has accumulated significant repo complexity. Navigating it correctly requires holding several truths simultaneously:

- Phase state and what has been built vs. what is planned
- Current runtime truth vs. doc truth vs. feature register truth
- Where a pass ended and what was left open
- What a file is for, how it connects, what depends on it

Without a governed intelligence layer, every session starts cold. The developer must manually reconstruct context from CLAUDE.md, Now.md, and Project-OS files — and trust that those files are current.

Developer Co-Development Mode provides a governed, draft-only mechanism for:
- Onboarding new runtimes or developers to a subsystem quickly
- Catching documentation drift before it causes build errors
- Generating ready-to-use implementation briefs from live repo state
- Producing architecture diagrams as proposals — not as embedded governance artifacts

The first bounded implementation (`developer_repo_explain_shadow`) proves the pattern without requiring LLM integration.

---

## 4. Current Bounded Scope

**Phase 9 closeout scope - `developer_repo_explain_shadow`:**

| Dimension | Current scope |
|-----------|--------------|
| Input | `focus_area`, `question`, `target_paths`, `project_scope` |
| Read scope | CLAUDE.md + declared `target_paths` + `focus_area` path (if valid) |
| Output | Draft developer brief, contradiction scan, doc refresh proposal, implementation brief, diagram proposal, build log, archive note |
| Write targets | `07_LOGS/Developer-Briefs/`, `07_LOGS/Build-Logs/`, `99_ARCHIVE/Documentation-History/` |
| Audit | `07_LOGS/Agent-Activity/` |
| Mode | Shadow / draft-only — no canonical writes |
| Analysis type | Structural pattern matching, heuristic phase/version scan |
| LLM generation | Not used — structural analysis only in Phase 9 |
| CLI alias | `chaseos develop explain --focus <area> --question "<question>" --target <path>` delegates to `developer_repo_explain_shadow` |

**What is deferred:**

- LLM-backed contextual explanation (Phase 10 upgrade path via SIC generation adapter)
- Full vault-wide contradiction scan (deferred — ambient traversal risk)
- Automated doc refresh writes (deferred — only draft proposals exist in this slice)
- Multiple adapter lanes (Phase 9+ — design is adapter-capable now, lane activation is later)
- Diagram rendering (deferred — Studio Phase 10)

---

## 5. Relationship to AOR, Runtime Shell, OSRIL, Studio, and Adapters

### AOR (Phase 9)
Developer Co-Development Mode is an AOR workflow. It runs through the standard 8-stage AOR pipeline: manifest → task classification → role card → permission ceiling → required reads → run → writeback → audit. It is gated by all AOR governance rules.

### Runtime Shell
`developer_repo_explain_shadow` is invocable via `chaseos run developer_repo_explain_shadow`. It also has a bounded convenience surface: `chaseos develop explain --focus <area> --question "<question>" --target <path>`, which delegates to the same AOR workflow rather than creating a second execution path.

### OSRIL (Phase 9/10)
OSRIL provides the event bus and runtime interaction contract. When Developer Co-Development Mode produces a draft brief, OSRIL is the future path to surface that brief to the operator in real time. In Phase 9, outputs land as draft/log/archive artifacts only; no real-time OSRIL surface is active yet.

### Studio (Phase 10)
Studio is the future surface for Developer Co-Development Mode outputs:
- Developer briefs as browsable artifacts
- Contradiction scan findings as surfaced alerts
- Diagram proposals as renderable Studio canvases
- Implementation briefs as copy-ready context panels

Studio cannot consume these before OSRIL event bus and Studio service layer are stable.

### Adapters / Harnesses
The **feature identity belongs to ChaseOS**. Adapters are execution lanes:

| Concept | Definition |
|---------|-----------|
| Provider | Who makes the underlying model |
| Execution surface | Where / how the model connects to tools |
| Execution adapter | The ChaseOS binding layer for that surface |
| Permission scope | What the operator explicitly grants to that adapter |

Current active implementation lane: the declared bounded development adapter/harness available to AOR for this pass. The feature identity is not tied to that lane.

Future lanes (not yet activated):
- Hermes adapter lane
- OpenClaw adapter lane
- Codex / OpenAI adapter lane
- Local-OSS adapter lane

Each lane is configured in its adapter manifest, not in this feature definition. The feature itself is adapter-agnostic.

---

## 6. Safety Posture

This feature operates at the most conservative permission ceiling available for a non-trivial workflow.

**Absolute constraints — never violated at any phase:**

- No canonical vault writes at any phase
- No edits to protected files (SOUL.md, Principles.md, CLAUDE.md, etc.)
- No 01_PROJECTS/ writes
- No 02_KNOWLEDGE/ writes
- No 03_INPUTS/ writes
- No shell execution
- No git operations
- No browser automation
- No network / connector calls
- No credential reads
- No ambient vault traversal — reads only declared context

**Write scope — current phase:**
- `07_LOGS/Developer-Briefs/` (draft brief artifacts)
- `07_LOGS/Agent-Activity/` (audit records)
- `07_LOGS/Build-Logs/` (bounded run/build records)
- `99_ARCHIVE/Documentation-History/` (bounded archive notes)

**Fail-closed behavior:** Any attempt to write outside declared scope → immediate escalation, no partial output, audit record written.

---

## 7. First Subfeatures — Implementation State

| Subfeature | File | Status |
|-----------|------|--------|
| Repo Truth Explainer | `runtime/aor/developer_shadow.py` → `run_developer_repo_explain()` | **BUILT** — Phase 9 |
| Contradiction / Drift Scan | `_scan_contradictions()` in `developer_shadow.py` | **BUILT** — Phase 9 (heuristic) |
| Doc Refresh Proposal Generator | `_build_doc_refresh_proposal()` in `developer_shadow.py` | **BUILT** — Phase 9 structured diff proposal artifact only; no writeback to target docs |
| Implementation Brief Generator | `_build_implementation_brief()` in `developer_shadow.py` | **BUILT** — Phase 9 |
| Diagram Draft Generator | `_build_diagram_proposal()` in `developer_shadow.py` | **BUILT** — Phase 9 (text/Mermaid draft only) |

---

## 8. Non-Goals

**Permanent non-goals (never in scope for this feature):**
- Ambient vault crawling or full-vault analysis without declared scope
- Canonical knowledge promotion
- Automated doc repair without operator review
- Replacing human judgement for architectural decisions
- Bypassing AOR → Gate governance chain

**Phase 9 non-goals (may change in later phases):**
- LLM-backed contextual generation
- Real-time streaming output to OSRIL
- Multi-adapter simultaneous execution
- Live diagram rendering
- Broad contradiction scan across the full vault

---

## 9. Adapter-Capable Design Rule

> The feature runs through adapters. The feature does not belong to any adapter.

**Applied to this feature:**

The workflow manifest (`developer_repo_explain_shadow.yaml`) declares the feature. A declared execution adapter or harness is what runs it. Adapter-specific configuration (adapter trust ceilings, adapter-specific writeback paths, adapter-specific approval models) lives in adapter manifests and adapter config — **not** in this feature definition.

This means:
1. The role card is adapter-agnostic
2. The task type is adapter-agnostic
3. The handler logic is adapter-agnostic
4. The manifest may declare `runtime_adapter` — but that is an execution hint, not a feature ownership claim
5. A future Hermes or Codex lane for this feature adds a new manifest + adapter config — it does not change this canonical doc or the handler

---

## 10. Canonical Placement

| Register | Entry |
|---------|-------|
| `Feature-Fit-Register.md` | Cross-Cutting → Developer Co-Development Mode subsection |
| `runtime/workflows/registry/` | `developer_repo_explain_shadow.yaml` |
| `06_AGENTS/role-cards/` | `developer-copilot-shadow.yaml` |
| `runtime/aor/task_type_table.yaml` | `developer-copilot-shadow` task type |
| `runtime/aor/developer_shadow.py` | Handler |
| `runtime/aor/test_phase9_dev_copilot_shadow.py` | Tests (31 focused tests passing after closeout) |
| `07_LOGS/Developer-Briefs/` | Draft output home |
| `07_LOGS/Build-Logs/` | Build/run log output home |
| `99_ARCHIVE/Documentation-History/` | Archive note output home |

---

## 11. Closeout / Reopen Conditions

**Current status:** COMPLETE / PARKED.

Developer Co-Development Mode is now useful and bounded, but it is not the current critical path for making ChaseOS more automatic. The closeout state is:

1. Shadow workflow remains active and runnable through AOR.
2. Convenience CLI alias exists through `chaseos develop explain`.
3. Doc refresh output is structured as draft diff proposals without applying canonical edits.
4. Adapter-capable identity is preserved; additional adapter lanes remain manifest/config work only.
5. Broad graph-assisted narrowing remains DEFERRED because the feature is explicitly not an ambient traversal tool.

Reopen this feature only when one of these is true:

1. A real adapter lane needs to run developer-mode briefs under its own manifest/config.
2. Studio or OSRIL needs a presentation surface for existing draft artifacts.
3. A declared, non-ambient Graph Substrate narrowing API is available and can be used without broad vault reads.
4. The operator wants Project-OS-specific formatting for explicitly declared target paths.

---

*Developer-Co-Development-Mode.md — ChaseOS canonical feature definition*
*Version: 1.2 | Created: 2026-04-22 | Updated: 2026-04-27 | Phase: 9 closeout / parked*
*ChaseOS-owned feature. Runs through adapters. Does not belong to adapters.*


*Graph links: [[Vault-Map]]*
