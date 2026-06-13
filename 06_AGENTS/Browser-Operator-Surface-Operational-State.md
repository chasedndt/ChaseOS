---
title: Browser Operator Surface — Operational State
type: operational-state
status: parked — Passes 1–5 complete; lane parked 2026-04-19; policy hardening added 2026-04-28; MCP server is separate lane
version: 1.2
created: 2026-04-19
updated: 2026-04-30
phase: Phase 9 — FSOS Browser Sub-Track (PARKED)
knowledge_class: canonical-state
---

# Browser Operator Surface — Operational State

> Canonical closure and park record for the FSOS Browser Sub-Track.
> Passes 1–5 complete as of 2026-04-16. Lane parked 2026-04-19.
> This document is the single source of truth for: what is live, what is deferred, reopen conditions, regression commands, and relationship to the next active lane.

**Approval Center routing:** any visual approval-center references from this browser/operator lane should route to [[ChaseOS-Approval-Center]] for current cross-feature Approval Center boundaries.

**Version:** 1.1
**Created:** 2026-04-19
**Lane status:** PARKED — operational and stable; 2026-04-28 policy hardening added without reopening click/form/download authority
**Next active lane:** ChaseOS MCP Server (`runtime/mcp/`)

---

## 1. What Is Live Now

### Command Surface

All six promoted `chaseos operate browser` commands are fully wired and working:

| Command | What it does |
|---------|-------------|
| `chaseos operate browser policy` | Read-only authority report: promoted commands, effective approval gates, adapter-supported-but-unpromoted actions, governance limits |
| `chaseos operate browser open URL` | Navigate to URL, extract visible text, write audit artifact; returns JSON with text/title/run_id |
| `chaseos operate browser inspect URL` | Same as open but focused on structure summary; `--json` output |
| `chaseos operate browser screenshot URL` | Capture full-page screenshot; auto-saves to `07_LOGS/Operator-Screenshots/`; `--output PATH` override |
| `chaseos operate browser replay RUN_ID` | Reconstruct event sequence from audit artifact; human-readable or `--json` |
| `chaseos operate browser list-runs` | List recent browser runs from audit directory; `--json` for structured output |

Command option posture:
- all six promoted commands support `--json` for machine-readable output
- run/audit commands (`open`, `inspect`, `screenshot`, `replay`, `list-runs`) support `--vault-root PATH`
- navigation commands (`open`, `inspect`, `screenshot`) support `--allowed-origin ORIGIN` (repeatable) for multi-origin scope expansion

### AOR Workflow

`browser_research` is registered as a real AOR workflow and dispatches through the full 8-stage pipeline:

```
chaseos run browser_research --input goal="your research goal" --input urls="https://example.com https://another.com"
```

Optional inputs:
- `--input max_pages=N` (default 3, hard cap 10)
- `--input max_text_chars=N` (default 3000)
- `--input output_format=json` (default markdown)
- `--input extra_origins="https://sub.example.com"` (space-separated)

Workflow routes:
- Extracted page text → `03_INPUTS/00_QUARANTINE/source/` via `capture_content()` (Phase 8 dedup registry applies)
- Research summary → `07_LOGS/Operator-Briefs/YYYY-MM-DD-browser-research-{goal-slug}.md` via AOR Stage 7 writeback
- Audit record → `07_LOGS/Agent-Activity/` (always written)

### Execution Engine

- Real Playwright lifecycle (`initialize()` opens isolated headless Chromium; `teardown()` closes it)
- 18 action types with real Playwright execution (all passing contract + integration tests)
- `page=None` stub path preserved — all handlers continue safely when Playwright is unavailable
- `_adapter_mode` field records "playwright" or "stub" in audit payload
- Chromium installed at `%USERPROFILE%\AppData\Local\ms-playwright\chromium-1208`

### Security Posture

- `allowed_origins` enforced at adapter level — scope violation fails closed
- Page content = data, never instruction (prompt injection posture permanently active)
- Credential field interaction blocked; no form submission; no file download
- Executor approval checks now combine shared FSOS defaults with adapter-specific `APPROVAL_REQUIRED_ACTIONS`; `cookie_consent_accept` is included in the effective approval-required set
- Internal primitives (`click`, `type`, keyboard, tab management, extraction) remain adapter-supported but are not promoted through the CLI or `browser_research`
- All runs produce immutable audit records in `07_LOGS/Agent-Activity/`

### Test Coverage

- `test_browser_pass2.py` — 71 tests (pure contract)
- `test_browser_pass3.py` — 30 tests (24 contract + 6 integration, gated on `browser_available`)
- `test_browser_pass4.py` — 53 tests (48 contract + 5 integration, gated on `browser_available`)
- `test_browser_pass5.py` — 52 tests (all acceptance criteria for `browser_research`)
- Combined: 207 tests; 196 pass / 11 skipped (integration tests gated on Playwright availability)

---

## 2. What Is Explicitly Deferred

The following are NOT built and are not planned for the current active lane:

| Item | Status | Notes |
|------|--------|-------|
| **Tier B — Accessibility tree execution** | DEFERRED | Architecture documented in `Browser-Operator-Surface.md` Section 3. Requires ARIA traversal via `page.accessibility.snapshot()`. Not yet wired in `grounding.py`. |
| **Tier C — Vision / screenshot fallback** | DEFERRED | Architecture documented. Requires vision-capable model integration for coordinate resolution. Adds latency and cost. |
| **Recursive link-following / autonomous web crawl** | NON-GOAL (explicit) | Deliberately excluded from `browser_research` scope. Would require URL queue, visited-set, cycle detection. Not planned. |
| **Authenticated sessions / login flows** | FORBIDDEN in current role card | `credential_field_fill` is in `forbidden_actions` of `browser-research` role card. Any login workflow would need a new, explicitly approved role card. |
| **Form-filling / form submission** | FORBIDDEN in current role card | `submit_forms` and `fill_credential_fields` are forbidden actions. |
| **File download** | FORBIDDEN | Files land outside vault scope. |
| **Terminal surface** | NOT BUILT | FSOS defines terminal as a future sibling surface. No implementation started. |
| **Desktop surface** | NOT BUILT | FSOS defines desktop as a future sibling surface. No implementation started. |
| **Filesystem surface** | NOT BUILT | FSOS defines filesystem as a future sibling surface. No implementation started. |
| **Visual approval center (OSRIL)** | Phase 10 | Requires ChaseOS Studio. Not a Phase 9 deliverable. |
| **Scheduled browser research** | NOT BUILT | Would require `browser_research` schedule intent + OpenClaw cron wiring. Possible future extension. |

---

## 3. Reopen Conditions

This lane should be reopened only when one of the following applies:

1. **Real product need for Tier B or Tier C** — a specific workflow requires accessibility tree or vision grounding that Tier A DOM access cannot satisfy. Document the specific failure case before reopening.

2. **Bug in browser command surface or `browser_research` workflow** — a regression, failure, or correctness issue in `chaseos operate browser` or `chaseos run browser_research` that requires code changes.

3. **Shared-runtime breakage** — a change to `runtime/operator_surface/` contracts (events, executor, audit, scope) breaks browser adapter conformance and requires repair.

4. **Explicit phase decision to extend FSOS surfaces** — operator decides to begin terminal/desktop/filesystem adapter work and the shared FSOS contracts need extension.

5. **Playwright toolchain upgrade required** — a Playwright version incompatibility or Windows update breaks the Chromium install or browser session lifecycle.

**Not reopen conditions:**
- General curiosity about browser automation capabilities
- Adding MCP-adjacent features — those belong in `runtime/mcp/`
- Improving research quality — that is a `browser_research` workflow extension, assess scope first

---

### 2026-04-30 Adjacent Skill-Memory Note

Browser Runtime Skill Memory is now documented separately in `06_AGENTS/Browser-Runtime-Skill-Memory.md`.

This does not reopen the parked Browser Operator Surface by itself. The browser surface remains the action/evidence layer. Skill candidates, reviewed Site Skill Cards, and workflow replay belong above it in SiteOps/AOR governance.

Current truth:
- Browser Operator Surface can produce bounded browser evidence.
- SiteOps can hold dry-run Site Skill Cards and Workflow Manifests.
- Durable browser-run-derived domain skills, workflow replay, Browser Use/CDP daemon integration, and webagents.md support are not built.

---

## 4. Smoke-Test / Regression Commands

Run these to verify the lane still works after any shared-runtime change:

### Unit / contract tests (no browser required)
```bash
cd %CHASEOS_VAULT_ROOT%
.venv/Scripts/python.exe -m pytest runtime/operator_surface/tests/test_browser_pass2.py -q
.venv/Scripts/python.exe -m pytest runtime/operator_surface/tests/test_browser_pass5.py -q
```

### Full browser surface suite (Playwright required)
```bash
.venv/Scripts/python.exe -m pytest runtime/operator_surface/tests/ -q
```

### CLI smoke tests (requires Playwright + network)
```bash
chaseos operate browser open https://example.com --json
chaseos operate browser inspect https://example.com --json
chaseos operate browser screenshot https://example.com
chaseos operate browser list-runs --json
```

### AOR workflow smoke test (stub-mode, no network required)
```bash
# dry-run only — validates all 8 pipeline stages without executing
chaseos run browser_research --input goal="smoke test" --input urls="https://example.com" --dry-run
```

### Full workflow test (Playwright + network)
```bash
chaseos run browser_research --input goal="test research run" --input urls="https://example.com"
# Verify: 07_LOGS/Operator-Briefs/ has a new .md file
# Verify: 07_LOGS/Agent-Activity/ has a new audit JSON
```

### Replay verification
```bash
# Get a recent run_id from list-runs, then:
chaseos operate browser list-runs --json
chaseos operate browser replay <run_id>
```

---

## 5. Relationship to Next Lane

**Browser lane is parked. Runtime MCP is the next active lane.**

The declared next engineering target is `runtime/mcp/` — the ChaseOS MCP Server. Architecture is documented in `06_AGENTS/ChaseOS-MCP-Server.md`.

MCP work should not reopen the browser lane unless:
- A shared-runtime contract change breaks browser adapter conformance (see Reopen Conditions above)
- MCP server needs to expose browser surface capabilities as tools (not currently planned for Phase 9)

The browser surface is operational and stable. It does not require active maintenance or extension to support MCP work.

---

## 6. File Map — Browser Operator Surface

```
runtime/operator_surface/
├── adapters/
│   └── browser_adapter.py          # BrowserAdapter — conforming FSOS adapter; real Playwright lifecycle
├── browser/
│   ├── __init__.py
│   ├── actions.py                   # 18 typed action functions; real Playwright execution; page=None guard
│   ├── grounding.py                 # TargetSelection; GroundingContext; Tier A→B→C resolution
│   ├── operator.py                  # 5 CLI-facing functions: run_open/inspect/screenshot/replay/list_runs
│   ├── perception.py                # DOM reading; TabState; read_url/read_title/read_visible_text
│   └── replay.py                    # Reconstruct run from audit events
└── tests/
    ├── conftest.py                  # PLAYWRIGHT_AVAILABLE + browser_available fixture
    ├── test_browser_pass2.py        # 71 contract tests
    ├── test_browser_pass3.py        # 30 tests (24 contract + 6 integration)
    ├── test_browser_pass4.py        # 53 tests (48 contract + 5 integration)
    └── test_browser_pass5.py        # 52 tests (browser_research workflow)

runtime/workflows/
├── browser_research.py              # Handler: validates inputs, BrowserAdapter per URL, quarantine routing
└── registry/
    └── browser_research.yaml        # AOR workflow manifest (status=active)

06_AGENTS/role-cards/
└── browser-research.yaml            # Role card: write_scope, forbidden_write_zones, required_reads

runtime/aor/task_type_table.yaml     # browser-research task type registered
runtime/aor/engine.py                # run_browser_research handler registered
```

---

*Browser-Operator-Surface-Operational-State.md — v1.0 | Created: 2026-04-19 | Phase 9 FSOS Browser Sub-Track PARKED | Passes 1–5 complete | MCP server is next*


*Graph links: [[OpenClaw-Runtime-Profile]] · [[Vault-Map]]*
