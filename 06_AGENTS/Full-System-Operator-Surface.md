---
title: Full-System Operator Surface
type: architecture
status: partial — Phase 9 formalization; runtime foothold created; browser child slice operational and policy-hardened; terminal/desktop/filesystem are future sibling surfaces
version: 1.1
created: 2026-04-15
updated: 2026-04-28
phase: Phase 9 — Operator Runtime (bounded sub-track)
knowledge_class: canonical-state
---

# Full-System Operator Surface

**Approval Center routing:** FSOS approval surface references should point to [[ChaseOS-Approval-Center]] for current operator-facing Approval Center truth; FSOS remains an execution/runtime contract family, not the approval aggregator.
## ChaseOS — Phase 9 Parent Runtime Execution Family

> The Full-System Operator Surface (FSOS) is the parent Phase 9 runtime execution family for controlled, governed computer operation across multiple physical surfaces — browser, terminal, desktop, and filesystem. It provides the shared planning, approval, event, audit, scope, session, and recovery contracts that all surface-specific execution adapters must conform to. Only the execution adapters vary by surface.

**Version:** 1.1
**Created:** 2026-04-15
**Status:** Partial — Phase 9 sub-track. Runtime foothold exists in `runtime/operator_surface/`. Browser is the first operational child execution slice with bounded CLI, `browser_research`, replay/audit, and a read-only policy report. Terminal/Desktop/Filesystem remain future sibling surfaces.

---

## 1. What the Full-System Operator Surface Is

The Full-System Operator Surface is a Phase 9 runtime execution family that extends ChaseOS's bounded operator model from vault and workflow operations to real-world computer actions — navigating browsers, executing terminal commands, interacting with desktop windows, and operating the local filesystem.

FSOS answers: *how does ChaseOS act on the real computer in a governed, auditable, recoverable way?*

FSOS is not a single tool. It is a parent family:
- One shared contract layer for all surfaces (planning, approval, events, audit, session, recovery)
- Multiple execution adapters, one per physical surface (browser, terminal, desktop, filesystem)
- Browser is the first child slice — the most structured, most isolation-friendly surface
- Terminal, desktop, and filesystem are future sibling child surfaces with their own adapters

FSOS is a Phase 9 engineering target. It does not yet have a visual approval center — that is Phase 10 Studio / OSRIL surface work. The runtime contracts, adapter base, and browser-first foothold are Phase 9 deliverables.

---

## 2. What FSOS Is Not

- **Not AOR** — AOR is the runtime brain that plans, routes, and audits. FSOS is the execution-surface family that AOR dispatches to. FSOS does not replace AOR; it runs under it.
- **Not OSRIL** — OSRIL routes AOR events to the operator surface (event/session visibility layer). FSOS is the execution layer that produces those events. They are orthogonal.
- **Not the Runtime Shell** — the Runtime Shell is command ingress. FSOS is execution output.
- **Not Studio** — Studio is the Phase 10 visual cockpit and approval center. FSOS provides the runtime contracts that Studio will consume.
- **Not ambient computer control** — every FSOS execution is declared in a workflow manifest, scoped, approved, and audited. There is no ambient, unsupervised computer action.
- **Not a browser automation library** — Playwright, Puppeteer, and similar tools are potential adapter implementations, not the architecture. The architecture lives above any specific tool.

---

## 3. Why FSOS Exists

Phase 9 AOR delivers governed autonomous execution for vault and SIC operations — briefings, close notes, graph hygiene, idea graduation. These are all internal ChaseOS operations.

Many operator workflows require real-world computer action beyond the vault:
- Research tasks that require navigating web pages
- Data extraction from sites without a public API
- Terminal commands for build/test/deploy operations
- File system operations for cross-project data movement
- Desktop UI interactions with applications that have no CLI

Without FSOS, these workflows cannot be executed under ChaseOS governance. The operator either does them manually or uses ungoverned automation scripts with no audit trail, no approval gates, and no recovery paths.

FSOS brings the same governance model that AOR applies to vault operations — bounded scope, declared permissions, approval gates, audit trails, session continuity, and graceful recovery — to real-world computer action.

---

## 4. Placement in ChaseOS Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 10 — ChaseOS Studio                    │
│           (Approval Center / Visual Cockpit / UX surface)       │
└───────────────────────────────┬─────────────────────────────────┘
                                │ consumes OSRIL events + FSOS state
┌───────────────────────────────▼─────────────────────────────────┐
│              OSRIL — Operator Surface + Runtime Interaction      │
│     (Event bus / session visibility / approval-linked flow)     │
└──────────────────┬──────────────────────────────────────────────┘
                   │ events from
┌──────────────────▼──────────────────────────────────────────────┐
│                 AOR — Autonomous Operator Runtime               │
│       (planning / bounded autonomy / policy / audit brain)      │
│                    dispatches to ↓                              │
└──────────────────┬──────────────────────────────────────────────┘
                   │ dispatches to
┌──────────────────▼──────────────────────────────────────────────┐
│          Full-System Operator Surface (FSOS) — THIS FILE        │
│   Parent execution family: shared contracts, adapter registry   │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Browser  │  │ Terminal │  │ Desktop  │  │  Filesystem  │   │
│  │ Adapter  │  │ Adapter  │  │ Adapter  │  │   Adapter    │   │
│  │(Phase 9) │  │ (STUB)   │  │ (STUB)   │  │  (STUB)      │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                   ↑ receives commands from
┌──────────────────┴──────────────────────────────────────────────┐
│         Runtime Shell — command ingress / workflow launcher     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Parent/Child Surface Hierarchy

FSOS uses a parent/child architecture:

```
Full-System Operator Surface (FSOS)
├── Browser Operator Surface          [Phase 9 — first child slice]
├── Terminal / PowerShell Operator Surface  [future sibling]
├── Desktop / Window Operator Surface       [future sibling]
└── Filesystem Operator Surface             [future sibling]
```

**The parent defines all shared contracts.** Every child surface implementation must conform to:
- Scope model
- Approval model
- Event schema
- Audit payload contract
- Session/continuity model
- Recovery model
- Security boundary rules

**Only the execution adapters vary.** The browser adapter uses DOM/accessibility/visual grounding. The terminal adapter uses PTY/subprocess execution. The desktop adapter uses accessibility APIs and screenshot analysis. The filesystem adapter uses governed path operations. The contracts are shared; the wiring is surface-specific.

This architecture prevents:
- Separate competing architectures for each surface
- Governance drift between surfaces
- Approval schemas that are surface-specific and incompatible
- Audit formats that cannot be compared across surfaces

---

## 6. Shared Runtime Contracts

All FSOS child surface adapters share these contracts. Defined in `runtime/operator_surface/`:

### 6.1 Scope Model

Every FSOS run operates within a declared scope:

```python
@dataclass
class OperatorScope:
    run_id: str
    surface: SurfaceType
    target_uris: list[str]          # URLs, paths, process names — explicit targets
    allowed_origins: list[str]      # for browser: allowed domains
    allowed_paths: list[str]        # for filesystem: allowed path prefixes
    forbidden_zones: list[str]      # explicit exclusion list
    max_actions: int                # hard action count ceiling
    max_duration_seconds: int       # hard time ceiling
    requires_approval: list[str]    # action classes requiring approval gate
    external_network: bool          # whether external network access is allowed
    credential_access: bool         # whether credential/secret access is allowed (always requires approval)
```

Scope is declared before execution. AOR validates it against the workflow manifest. The FSOS executor enforces it at every action.

### 6.2 Approval Model

Every action class that the manifest declares as approval-required triggers a pause:

```
1. Executor reaches approval-required action class
2. Emits OperatorEvent(type=AWAIT_APPROVAL, action_class=..., description=...)
3. Pauses — no action taken
4. OSRIL routes the approval_required event to the operator surface (Phase 9 event bus)
5. Operator responds: APPROVE or DENY with optional note
6. AOR records approval response in audit trail before execution resumes
7. If DENY: executor halts; writes OperatorRunResult(outcome=DENIED)
```

Approval responses are immutable once recorded. The executor cannot proceed without a recorded approval when one is required.

### 6.3 Event Schema

All FSOS surfaces emit events conforming to `OperatorEvent`:

```python
@dataclass
class OperatorEvent:
    event_id: str               # UUID
    run_id: str                 # links to OperatorSession
    surface: str                # "browser" | "terminal" | "desktop" | "filesystem"
    event_type: OperatorEventType
    timestamp: str              # ISO 8601
    step_index: int             # which step in the plan
    action_class: Optional[str] # what class of action triggered this
    description: str            # human-readable description
    payload: dict               # surface-specific structured data
    approval_required: bool
    approval_id: Optional[str]  # set if approval_required=True
```

`OperatorEventType` values: PLAN_READY, STEP_STARTED, STEP_COMPLETE, STEP_FAILED, AWAIT_APPROVAL, APPROVAL_RECEIVED, RECOVERY_STARTED, RECOVERY_COMPLETE, SESSION_COMPLETE, SESSION_FAILED

### 6.4 Audit/Replay Model

Every FSOS run produces an `OperatorRunAudit` artifact:

```python
@dataclass
class OperatorRunAudit:
    run_id: str
    workflow_id: str
    surface: str
    scope: OperatorScope
    plan: list[dict]            # declared steps before execution
    events: list[OperatorEvent] # full event sequence
    approvals: list[dict]       # approval records
    outcome: str                # COMPLETE | FAILED | DENIED | HALTED
    vault_writes: list[str]     # paths written to vault (if any)
    error: Optional[str]
    started_at: str
    completed_at: str
```

Audit artifacts are written to `07_LOGS/Agent-Activity/` on run close. Future: `runtime/audit/` directory when that subsystem is formalized.

Replay: given a `run_id`, FSOS can reconstruct the full event sequence from the audit artifact. This supports post-mortem analysis without re-execution.

### 6.5 Session/Continuity Model

Each FSOS execution creates an `OperatorSession`:

```python
@dataclass
class OperatorSession:
    session_id: str
    run_id: str
    workflow_id: str
    surface: str
    scope: OperatorScope
    status: SessionStatus       # ACTIVE | SUSPENDED | COMPLETE | FAILED
    current_step: int
    total_steps: int
    started_at: str
    last_active: str
    events: list[OperatorEvent]
    pending_approvals: list[str]
```

Sessions are runtime-local state. They are NOT canonical memory. Session state is stored ephemerally during execution. If the runtime restarts, the session is reconstructed from the audit artifact (which is persisted).

### 6.6 Recovery Model

When an FSOS execution fails mid-run:

```
1. Executor catches exception or receives STEP_FAILED event
2. Recovery protocol activates:
   a. Emit OperatorEvent(type=RECOVERY_STARTED)
   b. Execute recovery steps declared in surface adapter
   c. Write partial audit with failure state
   d. Emit OperatorEvent(type=RECOVERY_COMPLETE or SESSION_FAILED)
3. Vault is never left in a partial-write state
4. Recovery notes written to audit artifact
```

Each surface adapter declares its own recovery semantics:
- Browser: close tabs opened during the run; clear cookies if declared; emit recovery event
- Terminal: terminate spawned processes; reset working directory; emit recovery event
- Desktop: close windows opened during the run; emit recovery event
- Filesystem: reverse any partial writes if rollback_path is declared

---

## 7. Security Boundaries

These are hard limits that no FSOS surface adapter may violate:

| Boundary | Rule |
|----------|------|
| **Credential isolation** | No FSOS run may read, log, transmit, or expose credential/secret values. Credential access requires explicit approval gate. |
| **Scope ceiling** | No action outside the declared `target_uris`, `allowed_origins`, or `allowed_paths` may be taken. |
| **Forbidden zones** | `forbidden_zones` in scope are absolute — the executor must refuse to act on them even if explicitly instructed mid-run. |
| **Action count ceiling** | `max_actions` is a hard cap. The executor halts when reached, regardless of plan state. |
| **Time ceiling** | `max_duration_seconds` is a hard cap. The executor halts when reached. |
| **No ambient access** | FSOS adapters are invoked by AOR under a declared manifest. They do not run as ambient daemons with persistent computer access. |
| **No silent writes** | Every file write, network call, and system state change is logged in the audit artifact. |
| **Gate rules apply** | Any vault write from an FSOS run goes through Gate. FSOS cannot write to protected files. |
| **Injection hardening** | Content read from external surfaces (web pages, terminal output, files) is treated as untrusted data — not as instructions. Prompt injection via page content is a first-class risk. See `04_SOPS/Untrusted-Input-Handling-SOP.md`. |

---

## 8. Child Surfaces

### 8.1 Browser Operator Surface — Phase 9 First Child

**Status:** Phase 9 — operational child slice; bounded CLI and `browser_research` are live; 2026-04-28 policy hardening added; detailed spec in `06_AGENTS/Browser-Operator-Surface.md`

Browser is the first child execution surface because:
- Browser automation is the most mature, standardized toolchain (Playwright, Puppeteer, CDP)
- Browser targets are bounded by URL/domain — natural scope isolation
- DOM/accessibility provides structured grounding before visual fallback
- Most research and data extraction workflows involve browser targets
- Browser security boundaries (same-origin, sandboxing) provide a natural safety layer

Browser grounding order (Tier A → B → C):
- Tier A: structured browser / DOM access — direct element selection, semantic labeling
- Tier B: accessibility / semantic surface — ARIA roles, accessibility tree, computed labels
- Tier C: screenshot / visual fallback — pixel-level perception when Tiers A+B insufficient

Current promoted browser authority is inspectable with `chaseos operate browser policy --json`. The policy report is read-only and lists promoted CLI commands, effective always-approval action classes, adapter-supported-but-unpromoted primitives, governance flags, and known limitations. It does not grant new click/form/download/authenticated-session authority.

### 8.2 Terminal / PowerShell Operator Surface — Future Sibling

**Status:** STUB — adapter placeholder created; not yet implemented

Terminal operations require:
- PTY/subprocess isolation model
- Command whitelist/blacklist enforcement
- Working directory scope enforcement
- Output capture and structured parsing
- Process lifecycle management (spawn, monitor, terminate)
- Risk classification by command class (read-only vs. write vs. destructive)

Terminal is the second priority surface after browser because many operator workflows involve build/test/deploy commands.

### 8.3 Desktop / Window Operator Surface — Future Sibling

**Status:** STUB — adapter placeholder created; not yet implemented

Desktop operations require:
- Accessibility API integration (Windows UI Automation, macOS Accessibility API)
- Window/process targeting
- Visual grounding (screenshot + element detection)
- Mouse/keyboard action model
- Application lifecycle management

Desktop is a higher-risk surface because actions are harder to scope and reverse. More conservative approval model required.

### 8.4 Filesystem Operator Surface — Future Sibling

**Status:** STUB — adapter placeholder created; not yet implemented

Filesystem operations require:
- Explicit allowed path prefix enforcement
- Operation classification (read / write / delete / move)
- Delete operations require explicit approval gate — no silent deletion
- Cross-path operations require both paths to be in allowed_paths
- Integration with vault Gate for any writes to the ChaseOS vault

Note: The existing `runtime/capture/` subsystem handles vault-to-quarantine writes. The Filesystem Operator Surface handles general cross-directory file operations that fall outside the capture path.

---

## 9. Command Surface (Planned)

Future `chaseos operate` command family:

```
chaseos operate browser open URL
chaseos operate browser inspect
chaseos operate browser act --goal "..."
chaseos operate terminal inspect
chaseos operate terminal act --goal "..."
chaseos operate desktop inspect
chaseos operate approve RUN_ID STEP_ID
chaseos operate deny RUN_ID STEP_ID
chaseos operate replay RUN_ID
chaseos operate status RUN_ID
chaseos operate abort RUN_ID
```

These commands are defined here as canonical intent. They are NOT yet wired in `runtime/cli/main.py`. Command implementation requires:
1. FSOS executor and adapter contracts to be stable
2. At least one adapter (browser) to be non-stub
3. AOR dispatch to FSOS surface type to be wired in engine.py

---

## 10. Relationship to Other ChaseOS Components

| Component | Relationship |
|-----------|-------------|
| **AOR** | AOR is the planning and governance brain. FSOS is the execution-surface family AOR dispatches to. AOR validates scope against manifest; FSOS enforces it at action time. |
| **OSRIL** | OSRIL routes FSOS events to the operator surface. FSOS produces events; OSRIL routes them. Both needed; neither replaces the other. |
| **Runtime Shell** | Runtime Shell routes `chaseos operate` commands to FSOS. Shell is ingress; FSOS is execution. |
| **Studio (Phase 10)** | Studio provides the visual approval center, step feed, and operator overlay for FSOS runs. Studio consumes FSOS events via OSRIL. Studio is not an FSOS dependency. |
| **ChaseOS Gate** | Gate rules apply to all vault writes from FSOS runs. FSOS cannot bypass Gate. |
| **Untrusted Input SOP** | Content encountered during FSOS execution (web pages, terminal output, files) is treated as Tier 4 untrusted input. |
| **Credential Boundaries SOP** | FSOS never exposes credential values. Credential access requires explicit approval gate. |
| **Graph Substrate** | Graph advisory seam can inform FSOS planning — which vault files are related to the task, which files should be read before acting. |

---

## 11. Phase Placement Summary

| Work item | Phase | Status |
|-----------|-------|--------|
| FSOS parent architecture (this doc) | Phase 9 sub-track | COMPLETE — docs |
| Browser Operator Surface spec | Phase 9 sub-track | COMPLETE — docs |
| Operator Surface Adapter Spec | Phase 9 sub-track | COMPLETE — docs |
| Operator Overlay UX Spec | Phase 9 sub-track | COMPLETE — docs |
| Full-System Operator Safety SOP | Phase 9 sub-track | COMPLETE — docs |
| Operator Run Audit Template | Phase 9 sub-track | COMPLETE — docs |
| `runtime/operator_surface/` foothold | Phase 9 sub-track | COMPLETE — runtime |
| Browser adapter (non-stub) | Phase 9 sub-track | PLANNED |
| Terminal adapter (non-stub) | Phase 9 or later | FUTURE |
| Desktop adapter (non-stub) | Phase 9 or later | FUTURE |
| Filesystem adapter (non-stub) | Phase 9 or later | FUTURE |
| `chaseos operate` CLI wiring | Phase 9 sub-track | PLANNED |
| Studio visual approval surface | Phase 10 | FUTURE |

---

## 12. What Is Not in Scope

- Full computer autonomy — no ambient, unsupervised machine control
- Terminal/Desktop/Filesystem as complete implementations — they are stubs
- Studio visual overlay — Phase 10
- Voice-initiated computer actions — Phase 10 OSRIL
- Cross-machine / remote execution — outside current scope
- Screen recording / screen awareness — future perception adapter

---

*Graph links: [[OpenClaw-Runtime-Profile]] · [[Vault-Map]] · [[Autonomous-Operator-Runtime]] · [[Operator-Surface-Runtime-Interaction]] · [[ChaseOS-Runtime-Shell]] · [[Browser-Operator-Surface]] · [[Operator-Surface-Adapter-Spec]] · [[Operator-Overlay-UX-Spec]] · [[ChaseOS-Studio-Architecture]] · [[Permission-Matrix]] · [[Trust-Tiers]] · [[Agent-Security-Model]] · [[Feature-Fit-Register]]*

*Full-System-Operator-Surface.md — v1.0 | Created: 2026-04-15 | Phase 9 bounded sub-track | Parent execution family for all FSOS child surfaces | Browser is first child | Terminal/Desktop/Filesystem are future siblings*
