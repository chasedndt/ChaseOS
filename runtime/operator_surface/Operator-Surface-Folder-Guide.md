# runtime/operator_surface — Operator Surface Runtime

ChaseOS Full-System Operator Surface (FSOS) runtime module.

Provides governed, auditable, scope-bounded computer operation across physical surfaces. Currently operational: Browser. Declared future: Terminal, Desktop, Filesystem.

---

## What Surfaces Exist

| Surface | Status | Notes |
|---------|--------|-------|
| **Browser** | OPERATIONAL — parked | Playwright lifecycle, 18 actions, CLI surface, read-only policy report, `browser_research` AOR workflow |
| Terminal | NOT BUILT | Declared; stub adapter only |
| Desktop | NOT BUILT | Declared; stub adapter only |
| Filesystem | NOT BUILT | Declared; stub adapter only |

---

## Browser Surface — Usage

### Prerequisites

```bash
# Playwright installed
playwright install chromium
# Verify
python -c "from playwright.sync_api import sync_playwright; print('ok')"
```

### CLI Commands

**Inspect current browser authority policy:**
```bash
chaseos operate browser policy --json
```

**Open a URL and extract visible text:**
```bash
chaseos operate browser open https://example.com
chaseos operate browser open https://example.com --json
chaseos operate browser open https://example.com --max-text 5000
```

**Inspect a URL (structure summary):**
```bash
chaseos operate browser inspect https://example.com --json
```

**Screenshot a URL:**
```bash
chaseos operate browser screenshot https://example.com
chaseos operate browser screenshot https://example.com --output path/to/screenshot.png
```

**Replay a previous run:**
```bash
chaseos operate browser list-runs --json
chaseos operate browser replay <run_id>
```

**List recent browser runs:**
```bash
chaseos operate browser list-runs
chaseos operate browser list-runs --json
```

### AOR Workflow — `browser_research`

Bounded research workflow: navigates declared URLs, extracts page text to quarantine, produces a research summary brief.

```bash
# Basic
chaseos run browser_research \
  --input goal="research topic or question" \
  --input urls="https://example.com https://another.com"

# With options
chaseos run browser_research \
  --input goal="python packaging standards" \
  --input urls="https://packaging.python.org" \
  --input max_pages=5 \
  --input max_text_chars=5000 \
  --input output_format=json

# Dry-run — validates all AOR pipeline stages without executing
chaseos run browser_research \
  --input goal="test" \
  --input urls="https://example.com" \
  --dry-run
```

**Output routing:**
- Research summary → `07_LOGS/Operator-Briefs/YYYY-MM-DD-browser-research-{slug}.md`
- Page captures → `03_INPUTS/00_QUARANTINE/source/` (via Phase 8 dedup pipeline)
- Audit record → `07_LOGS/Agent-Activity/`

---

## Security Model

- **Scope enforcement:** `allowed_origins` declared per-run. Navigation outside scope fails closed.
- **Page content = data:** Extracted text is never executed or treated as operator instruction.
- **No credentials:** Credential field interaction blocked in all current role cards.
- **No form submission:** `submit_forms` is a forbidden action in the `browser-research` role card.
- **No file download:** `download_files` is forbidden.
- **Effective approval set:** executor approval checks combine shared surface defaults with adapter-specific `APPROVAL_REQUIRED_ACTIONS`; `chaseos operate browser policy --json` shows the current union.
- **Promotion boundary:** `click`, `type`, keyboard, tab-management, and generic extraction primitives remain adapter-supported but are not promoted through the CLI or `browser_research`.
- **Audit trail:** Every run produces an immutable JSON audit record in `07_LOGS/Agent-Activity/`.

---

## Running Tests

```bash
# Contract tests only (no browser required)
python -m pytest runtime/operator_surface/tests/test_browser_pass2.py -q
python -m pytest runtime/operator_surface/tests/test_browser_policy.py -q
python -m pytest runtime/operator_surface/tests/test_browser_pass5.py -q

# Full suite (integration tests need Playwright)
python -m pytest runtime/operator_surface/tests/ -q

# Specific acceptance criteria
python -m pytest runtime/operator_surface/tests/test_browser_pass5.py::TestAORManifestAndDryRun -v
python -m pytest runtime/operator_surface/tests/test_browser_pass5.py::TestAORWritebackIntegration -v
```

**Expected results:**
- 207 tests collected; 196 pass; 11 skipped (integration tests gated on `browser_available`)
- 4 pre-existing failures in older briefing_v2/pass2/pass3 tests — unrelated to browser surface

---

## Module Map

```
runtime/operator_surface/
├── __init__.py
├── audit.py                 # AuditPayload; load_audit; reconstruct_event_sequence
├── capabilities.py          # SurfaceType enum; capability constants (BROWSER_*, TERMINAL_*, etc.)
├── contracts.py             # OperatorScope; OperatorRunAudit dataclass
├── events.py                # OperatorEvent; OperatorEventType enum; event factory helpers
├── executor.py              # OperatorExecutor — runs plan against adapter; writes audit
├── recovery.py              # RecoveryPolicy; recovery action dispatch
├── session.py               # SessionState; session lifecycle management
│
├── adapters/
│   ├── base_adapter.py      # BaseOperatorAdapter — abstract contract all adapters implement
│   ├── browser_adapter.py   # BrowserAdapter — real Playwright execution (OPERATIONAL)
│   ├── terminal_adapter.py  # TerminalAdapter — stub only
│   ├── desktop_adapter.py   # DesktopAdapter — stub only
│   └── filesystem_adapter.py # FilesystemAdapter — stub only
│
├── browser/
│   ├── __init__.py
│   ├── actions.py           # 18 action functions with real Playwright execution
│   ├── grounding.py         # Tier A→B→C target resolution
│   ├── operator.py          # 5 CLI-facing functions (run_open/inspect/screenshot/replay/list_runs)
│   ├── perception.py        # DOM reads; TabState; page state extraction
│   └── replay.py            # Run reconstruction from audit for post-mortem
│
└── tests/
    ├── conftest.py           # PLAYWRIGHT_AVAILABLE; browser_available fixture
    ├── test_browser_pass2.py # 71 contract tests
    ├── test_browser_pass3.py # 30 tests (24 contract + 6 integration)
    ├── test_browser_pass4.py # 53 tests (48 contract + 5 integration)
    └── test_browser_pass5.py # 52 tests — browser_research workflow
```

---

## Known Limitations

- **Tier B (accessibility) not yet wired** — `grounding.py` declares the fallthrough but `page.accessibility.snapshot()` is not called in current implementation.
- **Tier C (vision) not yet wired** — screenshot capture works but coordinate resolution via vision model is not implemented.
- **No recursive crawling** — `browser_research` visits declared URLs only; no link-following.
- **No authenticated sessions** — credential fields are blocked in all current role cards.
- **Windows console encoding** — some Unicode characters may display as replacement chars in narrow Windows terminals; content is always written/stored correctly.

---

## Architecture References

- `06_AGENTS/Browser-Operator-Surface.md` — full architecture doc
- `06_AGENTS/Browser-Operator-Surface-Operational-State.md` — closure/park state, deferred items, reopen conditions
- `06_AGENTS/Full-System-Operator-Surface.md` — parent FSOS family doc
- `06_AGENTS/Full-System-Operator-Safety-SOP.md` — safety constraints
- `04_SOPS/Untrusted-Input-Handling-SOP.md` — page content handling
- `06_AGENTS/ChaseOS-MCP-Server.md` — next active lane architecture

---

*runtime/operator_surface/Operator-Surface-Folder-Guide.md — FSOS Browser Sub-Track PARKED 2026-04-19 | MCP next*


*Graph links: [[OpenClaw-Runtime-Profile]]*
