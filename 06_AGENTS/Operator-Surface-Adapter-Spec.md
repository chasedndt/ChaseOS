---
title: Operator Surface Adapter Spec
type: specification
status: docs-only — Phase 9 sub-track; adapter base contract defined; browser adapter is first implementation target
version: 1.0
created: 2026-04-15
updated: 2026-04-15
phase: Phase 9 — Full-System Operator Surface sub-track
knowledge_class: canonical-state
---

# Operator Surface Adapter Spec
## ChaseOS — Shared Adapter Contract for All FSOS Execution Surfaces

> Every FSOS execution surface adapter must conform to this specification. The adapter contract defines identity, capabilities, scope, permissions, event emission, failure semantics, approval hooks, audit payload, and grounding mode expectations. Adapters that do not conform cannot be registered with FSOS.

**Version:** 1.0
**Created:** 2026-04-15
**Status:** Docs-only — base contract implemented in `runtime/operator_surface/adapters/base.py`; browser adapter is first conforming implementation target

---

## 1. What This Spec Is

The Operator Surface Adapter Spec defines the conformance contract that every FSOS surface adapter must satisfy. It is analogous to `06_AGENTS/Execution-Adapter-Standard.md` for execution adapters, and `runtime/source_intelligence/SIC-Provider-Adapter-Standard.md` for SIC provider adapters — but applied to real-world computer action surfaces.

An FSOS adapter is a Python class that:
1. Inherits from `OperatorSurfaceAdapterBase`
2. Declares its identity, surface type, capabilities, and scope constraints
3. Implements the `plan()` and `execute()` lifecycle methods
4. Emits events conforming to `OperatorEvent` schema at required lifecycle points
5. Handles failures by entering recovery mode, not silent abort
6. Produces an `OperatorRunAudit` artifact at run close

---

## 2. Adapter Identity

Every adapter declares:

```python
class MyAdapter(OperatorSurfaceAdapterBase):
    # Required class-level identity fields
    ADAPTER_ID: str         # e.g. "browser-playwright-v1"
    SURFACE_TYPE: SurfaceType  # SurfaceType.BROWSER | TERMINAL | DESKTOP | FILESYSTEM
    ADAPTER_VERSION: str    # semver
    ADAPTER_STATUS: str     # "active" | "stub" | "partial"
    DESCRIPTION: str        # one-line description of this adapter
```

Identity fields are read by the `AdapterRegistry` to populate the adapter inventory. An adapter with `ADAPTER_STATUS = "stub"` can be registered but will not be dispatched to for real executions.

---

## 3. Surface Type

Each adapter declares exactly one `SurfaceType`:

| SurfaceType | Description | Primary toolchain |
|-------------|-------------|------------------|
| `BROWSER` | Browser tab/page navigation and interaction | Playwright / CDP / Puppeteer |
| `TERMINAL` | Terminal/shell command execution | PTY / subprocess |
| `DESKTOP` | Desktop window and UI interaction | Accessibility API / screenshot |
| `FILESYSTEM` | Governed filesystem operations | Python pathlib with scope enforcement |

An adapter may not declare multiple surface types. If a workflow requires multiple surfaces, it must use multiple adapters declared in sequence in the workflow manifest.

---

## 4. Capability Declarations

Every adapter declares its capability set:

```python
CAPABILITIES: frozenset[OperatorCapability]
```

Capabilities are declared statically. AOR checks declared capabilities against the workflow manifest before dispatching. A workflow that requires `OperatorCapability.BROWSER_NAVIGATE` will not dispatch to an adapter that does not declare it.

Core capabilities (defined in `runtime/operator_surface/capabilities.py`):

**Browser:**
- `BROWSER_NAVIGATE` — navigate to URLs
- `BROWSER_CLICK` — click elements
- `BROWSER_TYPE` — type text into inputs
- `BROWSER_SCROLL` — scroll pages
- `BROWSER_EXTRACT` — extract structured data from pages
- `BROWSER_SCREENSHOT` — capture page screenshots
- `BROWSER_WAIT` — wait for conditions

**Terminal:**
- `TERMINAL_READ` — read shell output / inspect current state
- `TERMINAL_EXECUTE` — execute shell commands
- `TERMINAL_SPAWN` — spawn subprocesses
- `TERMINAL_MONITOR` — monitor long-running process output

**Desktop:**
- `DESKTOP_READ` — read screen state via accessibility / screenshot
- `DESKTOP_CLICK` — click UI elements
- `DESKTOP_TYPE` — type into focused fields
- `DESKTOP_WINDOW_MANAGE` — focus, move, or close windows

**Filesystem:**
- `FILESYSTEM_READ` — read files within allowed paths
- `FILESYSTEM_WRITE` — write files within allowed paths
- `FILESYSTEM_LIST` — list directory contents within allowed paths
- `FILESYSTEM_MOVE` — move files within allowed paths
- `FILESYSTEM_DELETE` — delete files (always requires approval gate)

---

## 5. Scope Declarations

Every adapter declares its minimum required scope fields and its forbidden scope properties:

```python
REQUIRED_SCOPE_FIELDS: frozenset[str]   # fields that must be set for this adapter
FORBIDDEN_SCOPE_PROPERTIES: frozenset[str]  # properties this adapter will never accept
```

Example for browser adapter:
```python
REQUIRED_SCOPE_FIELDS = frozenset({"target_uris", "allowed_origins"})
FORBIDDEN_SCOPE_PROPERTIES = frozenset({"credential_access"})  # browser never accesses credentials
```

The FSOS executor validates scope against adapter declarations before dispatch.

---

## 6. Permission Requirements

Every adapter declares its minimum required permission ceiling:

```python
MIN_TRUST_TIER: int   # minimum AOR trust tier required to run this adapter
```

Values:
- Browser adapter: Tier 2 (bounded operator actions; user approval for sensitive targets)
- Terminal adapter: Tier 2 minimum; destructive commands require Tier 1 explicit grant
- Desktop adapter: Tier 2 minimum; always requires approval gate for any write action
- Filesystem adapter: Tier 2 minimum; delete operations require Tier 1 explicit grant

AOR will not dispatch to an adapter if the workflow's declared trust tier is below `MIN_TRUST_TIER`.

---

## 7. Event Emission Expectations

Every adapter must emit `OperatorEvent` at these lifecycle points:

| Lifecycle Point | Required Event Type | Notes |
|-----------------|--------------------:|-------|
| Plan produced | `PLAN_READY` | Before any execution begins |
| Step begins | `STEP_STARTED` | For each step in the plan |
| Step completes | `STEP_COMPLETE` | With structured result payload |
| Step fails | `STEP_FAILED` | With error info; triggers recovery |
| Approval needed | `AWAIT_APPROVAL` | Execution pauses until response |
| Approval received | `APPROVAL_RECEIVED` | Records operator decision |
| Recovery begins | `RECOVERY_STARTED` | After STEP_FAILED |
| Recovery complete | `RECOVERY_COMPLETE` | Or SESSION_FAILED if unrecoverable |
| Session completes | `SESSION_COMPLETE` | Final event on success |
| Session fails | `SESSION_FAILED` | Final event on failure |

Events are passed to the `emit_event()` hook provided by the FSOS executor. The adapter does not own event storage — it produces events; the executor stores them.

---

## 8. Failure Semantics

Adapter failure handling must follow this protocol:

1. On any exception or unexpected state: emit `STEP_FAILED`, do NOT silently continue
2. Enter recovery mode: invoke `recover()` method
3. `recover()` must: undo any partial state changes, emit `RECOVERY_STARTED`, attempt cleanup
4. If recovery succeeds: emit `RECOVERY_COMPLETE`, resume from next step OR halt (per manifest)
5. If recovery fails: emit `SESSION_FAILED`, write partial audit, return to AOR
6. Never leave the surface in an ambiguous state — always reach a defined outcome

Adapters must not swallow exceptions. Every exception surfaces as a `STEP_FAILED` event.

---

## 9. Approval Hooks

Adapters declare which action classes require approval gates:

```python
APPROVAL_REQUIRED_ACTIONS: frozenset[str]
```

At runtime, when the executor reaches an action in `APPROVAL_REQUIRED_ACTIONS`:
1. Adapter emits `AWAIT_APPROVAL` event
2. Executor pauses execution
3. Returns control to AOR pending approval response
4. On APPROVE: executor continues, records approval in audit
5. On DENY: executor halts, writes `outcome=DENIED` in audit

Default approval requirements by surface type:

| Surface | Required approval actions |
|---------|--------------------------|
| Browser | form submit, credential fields, external domain navigation |
| Terminal | write commands, destructive commands, network commands |
| Desktop | write actions, window close, application launch |
| Filesystem | write operations, move/rename, delete (always) |

Adapters may declare additional approval requirements specific to their implementation.

---

## 10. Audit Payload Contract

Every adapter contributes surface-specific data to the `OperatorRunAudit` payload:

```python
def build_audit_payload(self) -> dict:
    """Return surface-specific audit fields to be merged into OperatorRunAudit."""
    ...
```

Required fields in every adapter's audit payload:

| Field | Type | Description |
|-------|------|-------------|
| `adapter_id` | str | Which adapter executed |
| `surface_type` | str | Surface type enum value |
| `capabilities_used` | list[str] | Which capabilities were actually exercised |
| `steps_planned` | int | Number of steps in the plan |
| `steps_completed` | int | Number of steps completed before halt/complete |
| `steps_failed` | int | Number of failed steps |
| `approvals_required` | int | Number of approval gates triggered |
| `approvals_granted` | int | Number approved |
| `approvals_denied` | int | Number denied |
| `recovery_attempts` | int | Number of recovery attempts |

Surface-specific additional fields are added by each adapter implementation.

---

## 11. Grounding Mode Expectations

Adapters that interact with visual/semantic surfaces declare their grounding mode hierarchy:

```python
GROUNDING_MODES: list[GroundingMode]  # in priority order, highest to lowest
```

`GroundingMode` values:
- `STRUCTURED_API` — direct API access (e.g., browser CDP structured data)
- `ACCESSIBILITY` — accessibility tree / semantic labeling / ARIA roles
- `VISUAL_SCREENSHOT` — pixel-level screenshot analysis

Every adapter must declare its grounding priority. The executor uses the highest available grounding mode. If the highest mode fails or is unavailable, it falls through to the next.

**Browser adapter grounding order (canonical):**
```python
GROUNDING_MODES = [GroundingMode.STRUCTURED_API, GroundingMode.ACCESSIBILITY, GroundingMode.VISUAL_SCREENSHOT]
```

**Terminal adapter:** No visual grounding — text output is the ground truth.

**Desktop adapter grounding order (future):**
```python
GROUNDING_MODES = [GroundingMode.ACCESSIBILITY, GroundingMode.VISUAL_SCREENSHOT]
```

---

## 12. Required Method Signatures

Every FSOS adapter must implement:

```python
class OperatorSurfaceAdapterBase(ABC):

    @abstractmethod
    def initialize(self, scope: OperatorScope, session: OperatorSession) -> None:
        """Set up the surface context (open browser, connect to terminal, etc.)."""

    @abstractmethod
    def plan(self, goal: str, context: dict) -> list[dict]:
        """Produce an ordered list of steps to accomplish goal within scope."""

    @abstractmethod
    def execute_step(self, step: dict, emit_event: Callable) -> StepResult:
        """Execute a single step; emit events; return StepResult."""

    @abstractmethod
    def recover(self, failed_step: dict, emit_event: Callable) -> RecoveryResult:
        """Attempt recovery after step failure; emit RECOVERY_STARTED/COMPLETE."""

    @abstractmethod
    def teardown(self, outcome: str, emit_event: Callable) -> None:
        """Clean up surface state; always called on run completion or failure."""

    @abstractmethod
    def build_audit_payload(self) -> dict:
        """Return surface-specific audit fields."""
```

---

## 13. Adapter Registration

Adapters are registered in the `AdapterRegistry` (`runtime/operator_surface/adapter_registry.py`):

```python
from runtime.operator_surface.adapter_registry import AdapterRegistry
from runtime.operator_surface.adapters.browser_adapter import BrowserAdapter

registry = AdapterRegistry()
registry.register(BrowserAdapter)

# Lookup by surface type
adapter_class = registry.get_by_surface(SurfaceType.BROWSER)
```

The registry does not instantiate adapters — it stores adapter classes. Instantiation happens per-run inside the executor.

---

## 14. Conformance Checklist

To add a new FSOS adapter, verify:

- [ ] Inherits from `OperatorSurfaceAdapterBase`
- [ ] Declares `ADAPTER_ID`, `SURFACE_TYPE`, `ADAPTER_VERSION`, `ADAPTER_STATUS`, `DESCRIPTION`
- [ ] Declares `CAPABILITIES` as `frozenset[OperatorCapability]`
- [ ] Declares `REQUIRED_SCOPE_FIELDS` and `FORBIDDEN_SCOPE_PROPERTIES`
- [ ] Declares `MIN_TRUST_TIER`
- [ ] Declares `APPROVAL_REQUIRED_ACTIONS`
- [ ] Declares `GROUNDING_MODES` (visual surfaces only)
- [ ] Implements all 6 abstract methods: `initialize`, `plan`, `execute_step`, `recover`, `teardown`, `build_audit_payload`
- [ ] Emits `OperatorEvent` at all required lifecycle points
- [ ] Never swallows exceptions — all failures surface as `STEP_FAILED`
- [ ] Registered in `AdapterRegistry`
- [ ] Has at least a stub test file in `runtime/operator_surface/adapters/tests/`

---

*Graph links: [[OpenClaw-Runtime-Profile]] · [[Vault-Map]] · [[Full-System-Operator-Surface]] · [[Browser-Operator-Surface]] · [[Operator-Overlay-UX-Spec]] · [[Autonomous-Operator-Runtime]] · [[Execution-Adapter-Standard]] · [[Permission-Matrix]] · [[Agent-Security-Model]]*

*Operator-Surface-Adapter-Spec.md — v1.0 | Created: 2026-04-15 | Phase 9 sub-track | Shared adapter contract for all FSOS execution surfaces | Extends Execution-Adapter-Standard pattern to computer-action surfaces*
