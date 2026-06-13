---
title: Codex V1 Build Test Report 2026-05-31
created: 2026-05-31
runtime: Codex
status: COMPLETE FOR STATIC LAUNCH SMOKE / VISUAL BROWSER QA BLOCKED
type: build-test-report
---

# Codex V1 Build Test Report - 2026-05-31

## Commands Run

| Command | Result |
|---|---|
| `python website\build_site.py` | PASS / regenerated static website, Forge index, standards examples, and demo fixture |
| `python -m py_compile website\build_site.py website\smoke_test.py` | PASS |
| `python website\smoke_test.py` | PASS / `OK: ChaseOS static launch smoke passed for 50 files.` |
| `rg -n -F "chaseos.systems" website docs\standards\examples docs\website docs\forge 06_AGENTS\ChaseOS-V1-Release-Cutline.md` | REVIEWED / matches are superseded-domain context in docs plus the smoke-test forbidden-string literal; no generated public page or public JSON uses `chaseos.systems` |
| `git diff --check -- website docs\standards docs\website 06_AGENTS 07_LOGS fixtures 99_ARCHIVE` | PASS |
| Node REPL Playwright render of `website/index.html` | BLOCKED / `Module not found: playwright` |

## Smoke Coverage

`website/smoke_test.py` verifies:
- Required route files exist.
- Homepage headline, supporting copy, primary CTA, Forge CTA, docs CTA, and `https://chaseos.ai` are present.
- Waitlist form includes email, role, main use case, biggest pain, and consent fields.
- Admin page is noindex and declares disabled/protected/no PII status.
- Forge index parses, has six preview packs, and each pack has required manifest fields.
- Standards examples parse in both site and docs locations.
- Demo fixture files exist and parse.
- Public generated surfaces avoid stale domains, private paths, secret markers, and forbidden overclaim phrases.

## Remaining Test Gaps

- No live browser screenshot or responsive visual QA was captured in this pass.
- No deployment smoke, DNS check, production waitlist storage check, email check, analytics check, or payment check was run.
- No Studio app route/browser proof was run because this pass did not change Studio source.
