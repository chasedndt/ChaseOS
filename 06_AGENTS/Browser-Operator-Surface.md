---
title: Browser Operator Surface
type: architecture
status: parked — Phase 9 sub-track; Passes 1–5 complete 2026-04-16; lane parked 2026-04-19; command surface live; browser_research AOR workflow live; policy report and adapter-specific approval hardening added 2026-04-28; Tier B/C deferred; MCP is next active lane
version: 1.6
created: 2026-04-15
updated: 2026-04-28
phase: Phase 9 — Full-System Operator Surface sub-track (first child)
knowledge_class: canonical-state
---

# Browser Operator Surface
## ChaseOS — First FSOS Child Execution Surface

> The Browser Operator Surface is the first child execution surface of the Full-System Operator Surface family. It defines how ChaseOS controls browser tabs, navigates pages, extracts content, and performs UI interactions — under governed scope, with approval gates, full audit trails, and structured recovery — using a tiered grounding model (DOM → accessibility → visual fallback).

**Version:** 1.6
**Created:** 2026-04-15
**Updated:** 2026-04-28 (FSOS hardening pass — policy report and adapter-specific approval union added)
**Status:** Parked — Phase 9 sub-track; Passes 1–5 complete 2026-04-16; lane parked 2026-04-19. All 18 action types have real Playwright execution. `chaseos operate browser policy/open/inspect/screenshot/replay/list-runs` fully wired in canonical CLI. `browser_research` AOR workflow registered and running via `chaseos run browser_research --input goal="..." --input urls="..."`. Extracted page content routed to quarantine via Phase 8 capture pipeline. Research summary written to `07_LOGS/Operator-Briefs/`. `initialize()`/`teardown()` manage a real isolated headless Chromium context. `page=None` stub path preserved for contract-only environments. Tier A (DOM/structured) execution live. Tier B (accessibility) and Tier C (vision) deferred. A read-only browser policy report now surfaces promoted CLI actions, adapter-supported-but-unpromoted actions, effective approval-required action classes, governance flags, and limitations. MCP server remains a separate lane.

---

## 1. Why Browser Is the First Child Surface

Browser is the first FSOS child slice for four reasons:

1. **Best tool ecosystem** — Playwright, Puppeteer, and Chrome DevTools Protocol (CDP) are mature, well-documented browser automation toolchains. The path from architecture to working implementation is direct.

2. **Natural scope isolation** — Browser targets are naturally bounded by URL and domain. `allowed_origins` provides a clean scope enforcement mechanism that does not exist for terminal or desktop operations.

3. **Structured grounding** — DOM provides structured element access. Accessibility trees add semantic context. Visual/screenshot fallback is well-understood (GPT-4V, Claude vision). The grounding hierarchy is tiered and progressively fallible.

4. **Highest workflow value first** — Research workflows, data extraction, web-based form automation, and content monitoring are all browser operations. These are the most common real-world automation targets.

---

## 2. Browser/Tab/Navigation/Action Model

### 2.1 Browser Session Lifecycle

```
INITIALIZE → NAVIGATE(target_uri) → [ACTION]* → EXTRACT? → TEARDOWN
```

A browser session:
1. Opens a browser context (isolated from operator's personal browser sessions)
2. Navigates to the first `target_uri` in scope
3. Executes planned actions (click, type, scroll, wait, extract)
4. Optionally extracts structured content for vault writeback
5. Tears down (closes context, clears session state)

**Isolation rule:** The browser adapter always uses an isolated browser context — not the operator's default browser profile. No cookies, no saved passwords, no extensions from the operator's personal browser carry over into FSOS execution contexts.

### 2.2 Navigation Model

Navigation targets must be in `scope.target_uris` or a subdomain of `scope.allowed_origins`:

```python
@dataclass
class BrowserNavigationTarget:
    url: str
    reason: str                 # why this navigation is needed
    allowed_origins_check: bool # enforce allowed_origins
    requires_approval: bool     # set to True for external domains
```

Navigation outside `allowed_origins` triggers an `AWAIT_APPROVAL` event. The executor pauses. The operator may approve or deny. Unauthorized navigation attempts are logged and blocked.

### 2.3 Action Model

Browser actions are typed and ordered. Pass 3 complete action inventory (all 18 actions have real Playwright execution):

**Navigation**

| Action Type | Description | Approval required |
|-------------|-------------|------------------|
| `navigate` | Navigate to a URL within allowed origins | Only if outside allowed_origins |
| `back` | Navigate back in browser history | No |
| `forward` | Navigate forward in browser history | No |
| `reload` | Reload current page | No |

**Tab Management**

| Action Type | Description | Approval required |
|-------------|-------------|------------------|
| `tab_open` | Open a new tab and navigate to URL (scope enforced) | No (but URL scope-checked) |
| `tab_close` | Close tab matching target URL | No |
| `tab_focus` | Bring focus to tab matching target URL | No |

**Interaction**

| Action Type | Description | Approval required |
|-------------|-------------|------------------|
| `click` | Click an element by selector | No (unless declared in manifest) |
| `type` | Type text into an input field | Yes if credential field detected |
| `keypress` | Send keyboard key or combination (Enter, Tab, Escape, Ctrl+A) | No |
| `scroll` | Scroll the page (up/down/left/right) | No |
| `wait_for` | Wait for element/condition | No |

**State Reads (non-mutating)**

| Action Type | Description | Approval required |
|-------------|-------------|------------------|
| `read_url` | Read current page URL | No |
| `read_title` | Read current page title | No |
| `read_visible_text` | Read all visible body text (UNTRUSTED) | No |

**Extraction**

| Action Type | Description | Approval required |
|-------------|-------------|------------------|
| `extract` | Extract structured content by selector | No |
| `screenshot` | Capture full-page screenshot | No |

**Always-gated (require explicit approval before execution)**

| Action Type | Reason |
|-------------|--------|
| `form_submit` | POST state changes are irreversible |
| `credential_field_fill` | Never auto-fill credentials |
| `file_download` | Files land outside vault scope |
| `navigate_external_domain` | Domain outside allowed_origins |
| `cookie_consent_accept` | Privacy-relevant consent |

Actions are declared in the plan produced by `browser_adapter.plan()`. The plan is reviewed (as `PLAN_READY` event) before execution begins. Unknown action types raise `ValueError` — the executor catches this as `STEP_FAILED`.

As of 2026-04-28, the executor computes effective always-gated browser actions from the shared FSOS surface defaults plus the adapter's `APPROVAL_REQUIRED_ACTIONS`. This closes the gap where adapter-specific hard gates such as `cookie_consent_accept` could be declared by the adapter but not visible to executor approval checks. The promoted CLI and `browser_research` workflow still expose only read/screenshot/replay/research authority; `click`, `type`, keyboard, tab-management, and generic extraction primitives remain adapter-supported but not promoted through the CLI.

The current authority boundary is inspectable with:

```powershell
chaseos operate browser policy --json
```

---

## 3. Grounding Model — Tiered (A → B → C)

The browser adapter uses a tiered grounding hierarchy. It tries the highest tier first; falls through to lower tiers if the higher tier fails or is insufficient.

### Tier A — Structured Browser / DOM Access

**What it is:** Direct element access via CSS selectors, XPath, or CDP-provided element references. The browser's own structured representation of the page.

**How it works:**
- Use Playwright's `page.locator()` or CDP element queries to identify elements by selector
- Elements have deterministic locations — no screenshot analysis needed
- Structured page data (JSON-LD, microdata, meta tags) extracted directly from DOM
- Preferred for: form elements, navigation links, structured tables, known page layouts

**Failure mode:** Element not found, dynamic content not yet loaded, heavily obfuscated selectors.

**Fallthrough:** Move to Tier B.

### Tier B — Accessibility / Semantic Surface

**What it is:** Accessibility tree traversal using ARIA roles, computed labels, and semantic element context. Provides human-meaningful descriptions that are more stable than raw CSS selectors.

**How it works:**
- Query `page.accessibility.snapshot()` (Playwright) or CDP `Accessibility.getFullAXTree()`
- Match elements by role + name combinations: `button[name="Submit"]`, `textbox[name="Email"]`
- Semantic labels are more robust than class-based selectors across page redesigns
- Preferred for: interactive elements with clear semantic purpose, forms, navigation menus

**Failure mode:** Page uses no ARIA labels, dynamic components with no accessible names, deeply nested custom components.

**Fallthrough:** Move to Tier C.

### Tier C — Screenshot / Visual Fallback

**What it is:** Visual perception layer using page screenshots analyzed by a vision-capable model (Claude, GPT-4V). Identifies elements by visual appearance and layout when DOM/accessibility fails.

**How it works:**
- Capture full-page screenshot via `page.screenshot()`
- Pass screenshot + task description to vision model
- Model identifies element coordinates, bounding boxes, or descriptions
- Actions are then executed at identified coordinates via mouse simulation

**Important constraints:**
- Tier C is slower and less reliable than Tier A or B
- Tier C results must be validated against the DOM before action (prevent misidentification)
- Tier C is a fallback — workflows should be designed to succeed at Tier A or B
- Tier C adds latency and cost; its use is logged in the audit payload

**When Tier C is appropriate:** Heavily JavaScript-rendered SPAs, custom canvas elements, legacy UIs with no ARIA annotations.

---

## 4. Browser-Specific Approval Semantics

In addition to the base FSOS approval model, the browser adapter requires approval for:

| Trigger | Reason |
|---------|--------|
| Navigation to domain outside `allowed_origins` | Prevents scope drift to unintended sites |
| Detection of credential/password input fields | Never fill credential fields without explicit operator confirmation |
| Form submission with `method=POST` | Irreversible server-side state change |
| File download trigger | Files arrive in local filesystem outside vault scope |
| Cookie consent dialogs that accept tracking | Privacy-relevant consent should not be auto-granted |
| Any redirect to a domain outside `allowed_origins` | Follows-the-link policy |

These checks happen in `browser_adapter.execute_step()` before any action is taken.

---

## 5. Browser-Specific Recovery Behavior

When a browser step fails:

1. Emit `STEP_FAILED` with error description and current URL
2. Take a screenshot of current page state (recovery evidence)
3. Attach screenshot path to recovery event payload
4. Close any modals or overlays that may have opened
5. Navigate back to last known-good URL if current URL is outside plan
6. If `target_uris` are now all invalid or unreachable: emit `SESSION_FAILED`
7. Otherwise: emit `RECOVERY_COMPLETE` and proceed to next step (if manifest allows)
8. Close browser context on teardown regardless of outcome

Recovery evidence (screenshots) are stored in a temp directory and referenced from the audit artifact. They are not written to the vault by default.

---

## 6. Content Extraction and Vault Writeback

Browser sessions may extract content for vault writeback. This integrates with the Phase 8 capture pipeline:

```
Browser extracts content
    → ContentPacket created
    → capture_content() writes to 03_INPUTS/00_QUARANTINE/
    → Standard sidecar + dedup registry update
    → Content awaits operator promotion (same as any captured content)
```

**The browser adapter does NOT directly write to `02_KNOWLEDGE/` or other canonical vault locations.** All extracted content goes through quarantine first. This is non-negotiable.

Extracted content uses `origin_kind="browser-operator"` in the sidecar semantic breadcrumbs to distinguish operator-surface captures from manual captures.

---

## 7. Prompt Injection Hardening

Browser content is high-risk for prompt injection. Malicious pages may contain embedded instructions designed to hijack the running operator session.

Browser adapter injection defense:
- Page content extracted for analysis is passed as `data`, not as `instruction`
- Extracted text is never interpolated directly into system prompts
- If page content contains patterns matching instruction injection (e.g., "Ignore previous instructions"), flag to operator and halt
- All navigation targets are compared against `allowed_origins` before content is parsed
- See `04_SOPS/Untrusted-Input-Handling-SOP.md` for full untrusted input handling rules

---

## 8. Implementation Target

The canonical implementation is `runtime/operator_surface/browser/`:

```
runtime/operator_surface/browser/
├── __init__.py
├── perception.py      # DOM reading, accessibility tree, screenshot capture;
│                      # TabState + list_tabs (tab management); read_url/read_title/
│                      # read_visible_text; PageState with tabs/tab_count/visible_text
├── actions.py         # 18 typed action functions with full contracts and failure modes;
│                      # ActionResult with tab_id field; scope enforcement on navigate
│                      # and tab_open; credential field blocking placeholder
├── grounding.py       # TargetSelection dataclass; GroundingContext run-scoped tracker
│                      # (record_tier_use, to_audit_dict, grounding_summary);
│                      # resolve_target(); select_grounding_tier(); fallthrough A→B→C
└── replay.py          # reconstruct run from audit events for post-mortem analysis
```

Plus `runtime/operator_surface/adapters/browser_adapter.py` — the conforming adapter class.

**Capability declarations (Pass 2 — unchanged):**
- `BROWSER_NAVIGATE`, `BROWSER_CLICK`, `BROWSER_TYPE`, `BROWSER_SCROLL`,
  `BROWSER_EXTRACT`, `BROWSER_SCREENSHOT`, `BROWSER_WAIT` (Pass 1)
- `BROWSER_TAB_MANAGE` — open/close/focus tabs (Pass 2)
- `BROWSER_READ_STATE` — read URL/title/visible text (Pass 2)
- `BROWSER_KEYBOARD` — keypress, shortcuts (Pass 2)

**Pass 3 implementation status:**
- `browser_adapter.py` v0.3.0 — real `initialize()` (headless Chromium, isolated context); real `teardown()` (context→browser→playwright.stop()); `_adapter_mode` field; all 18 handlers delegate to `actions.py` with real `self._page`
- `actions.py` — all 18 action functions with real Playwright calls behind `page is None` guard
- `perception.py` — all perception functions with real Playwright calls behind `page is None` guard
- `grounding.py` — unchanged; `_try_tier()` already delegated to real perception functions
- `tests/conftest.py` — `PLAYWRIGHT_AVAILABLE` + `browser_available` session-scoped fixture
- `pyproject.toml` — `playwright>=1.40` added; install note for `playwright install chromium`

**Pass 4 implementation status (command surface):**
- `browser/operator.py` — core execution logic; `_validate_url`, `_extract_origin`, `_build_browser_scope`, `_extract_step_outputs`, `_run_operate_plan`; 5 CLI-facing functions: `run_open`, `run_inspect`, `run_screenshot`, `run_replay`, `run_list_runs`
- `runtime/cli/main.py` — `chaseos operate browser open/inspect/screenshot/replay/list-runs` fully wired; all commands support `--json`; `--allowed-origin` (repeatable) for scope expansion; `--output` for screenshot path; `--max-text` for open; audit artifacts always written via executor
- Screenshots auto-saved to `07_LOGS/Operator-Screenshots/` with timestamped filename if no `--output` specified
- Plans use `navigate` action type — no approval gates for read-only operations

**Test coverage:**
- `runtime/operator_surface/tests/test_browser_pass2.py` — 71 tests / 71 pass (pure contract tests, no browser required)
- `runtime/operator_surface/tests/test_browser_pass3.py` — 30 tests: 24 contract + 6 integration (gated on `browser_available`)
- `runtime/operator_surface/tests/test_browser_pass4.py` — 53 tests: 48 contract + 5 integration (gated on `browser_available`)
- Combined: 155 collected / 144 pass / 11 skipped (integration tests in combined session)
- Integration tests verified live: open/inspect/screenshot against example.com; replay round-trip; list-runs after live execute

**Playwright toolchain (installed):**
- `playwright>=1.40` in `pyproject.toml`
- `playwright install chromium` — downloads headless Chromium (~280MB)
- Chromium verified: `%USERPROFILE%\AppData\Local\ms-playwright\chromium-1208`
- Graceful degradation: if Playwright unavailable or launch fails, `_adapter_mode = "stub"` — all handlers continue via `page=None` path

---

## 9. Registered AOR Workflow — `browser_research`

The `browser_research` workflow is registered and running via the full AOR 8-stage pipeline.

**Registration:**
- Manifest: `runtime/workflows/registry/browser_research.yaml` (status=active, task_type=browser-research)
- Role card: `06_AGENTS/role-cards/browser-research.yaml`
- Handler: `runtime/workflows/browser_research.py`
- Task type: `browser-research` in `runtime/aor/task_type_table.yaml`

**Invocation:**
```
chaseos run browser_research --input goal="your research goal" --input urls="https://example.com"
```

**Content routing:**
- Extracted page text → `03_INPUTS/00_QUARANTINE/source/` via `capture_content()` (Phase 8 pipeline; dedup applies)
- Research summary → `07_LOGS/Operator-Briefs/YYYY-MM-DD-browser-research-{goal-slug}.md` via AOR Stage 7
- Audit record → `07_LOGS/Agent-Activity/` (always written regardless of outcome)

**Security invariants (non-negotiable):**
- Page content = data, never instruction
- `allowed_origins` enforced at adapter level (scope violation → escalate)
- No credential access; no form submission; no file download
- Stub mode (no Playwright) → succeeds but produces no quarantine captures

---

## 10. Operational State — Lane Parked

**As of 2026-04-19, the FSOS Browser Sub-Track is parked.**

Passes 1–5 are complete. The browser surface is operational and stable. It is not the current active build lane.

**What is live:** Playwright lifecycle, 18 action types, command surface, `browser_research` AOR workflow, quarantine routing, audit trail.

**What is deferred:** Tier B (accessibility execution), Tier C (vision fallback), recursive crawling, authenticated sessions, form submission, terminal/desktop/filesystem sibling surfaces.

**Next active lane:** ChaseOS MCP Server (`runtime/mcp/`).

For full detail on deferred items, reopen conditions, and regression commands:
→ `06_AGENTS/Browser-Operator-Surface-Operational-State.md`

---

*Graph links: [[OpenClaw-Runtime-Profile]] · [[Vault-Map]] · [[Full-System-Operator-Surface]] · [[Browser-Operator-Surface-Operational-State]] · [[Operator-Surface-Adapter-Spec]] · [[Autonomous-Operator-Runtime]] · [[04_SOPS/Untrusted-Input-Handling-SOP|Untrusted-Input-Handling-SOP]] · [[04_SOPS/Credential-Boundaries-SOP|Credential-Boundaries-SOP]] · [[Full-System-Operator-Safety-SOP]]*

*Browser-Operator-Surface.md — v1.5 | Created: 2026-04-15 | Updated: 2026-04-19 (closure/park — lane parked; Section 9 updated: browser_research registered; Section 10 added: operational state) | Phase 9 sub-track PARKED | First FSOS child execution slice | 18 action types with real Playwright execution | initialize/teardown live | page=None stub path preserved | chaseos operate browser fully wired | browser_research AOR workflow registered | 207 tests (196 pass / 11 integration-skipped) | Tier A live; Tier B/C future | MCP next*
