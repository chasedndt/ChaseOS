---
type: architecture
project: ChaseOS
phase: Phase 8 — Connector / Capture Automation
version: 1.8
date: 2026-03-31
status: complete
---

# Connector / Capture Architecture — Phase 8

## Purpose

Phase 8 adds automated content capture to ChaseOS. It removes the manual
"copy-paste into 03_INPUTS/" step and replaces it with a governed, deterministic
pipeline that any connector (CLI, API, browser extension, scheduled agent) can
drive through a single public API.

---

## Core Principles

1. **Quarantine-first.** All captures land in `03_INPUTS/` as raw quarantine files.
   Nothing is promoted until the user (or an agent with explicit `CHASEOS_PROMOTION_APPROVED=1`)
   moves it through the Gate.

2. **Type-first routing.** The primary organizational dimension is content type
   (`input_class`), not date, source, or workspace. Each class routes to a dedicated
   subfolder: type grouping keeps content separated and navigation flat.

3. **Sidecar as canonical provenance.** Every content file is paired with a
   `[filename].meta.json` sidecar. The sidecar is the authoritative metadata record.
   The content file carries only raw text. This separation is binary-file-ready
   and keeps provenance durable across renames.

4. **Deterministic naming.** Filenames encode exactly four semantic fields,
   separated by double underscores (`__`):
   ```
   YYYYMMDD-HHMMSS__[class]__[source]__[slug].md
   ```
   Same title + source + timestamp → same filename. Collisions are resolved
   by appending `_2`, `_3`, etc. to the stem.

5. **Source Package timing.** Source Packages (SIC ingestion units) are built
   **after** quarantine review and Gate promotion, not at capture time.
   Capture → Quarantine → (user review) → Gate promotion → SIC ingestion.

6. **Connector-agnostic.** The `ContentPacket` data container is the sole
   interface between connectors and the intake writer. Any connector that produces
   a valid `ContentPacket` works with the same pipeline.

---

## Physical Quarantine Boundary

All new automated captures write to `03_INPUTS/00_QUARANTINE/[class]/`.
The `00_` prefix sorts the quarantine boundary first in any directory listing,
making it physically distinct from legacy content.

```
03_INPUTS/
    00_QUARANTINE/           ← CANONICAL WRITE TARGET for all new captures
        Transcript-Raw/      ← input_class: transcript
        Digests/             ← input_class: digest
        NotebookLM/          ← input_class: notebooklm
        Sources/             ← input_class: source
        Clipboard/           ← input_class: clipboard
        Journal-Raw/         ← input_class: journal
        YouTube-Notes/       ← input_class: youtube_note
    Transcript-Raw/          ← legacy (pre-Pass-2 files, coexist safely)
    Digests/                 ← legacy
    NotebookLM/              ← legacy
    Sources/                 ← legacy
    Clipboard/               ← legacy
    Journal-Raw/             ← legacy
    YouTube-Notes/           ← legacy
```

**Migration strategy:** Legacy files in flat `03_INPUTS/[class]/` remain untouched.
New captures always go to `00_QUARANTINE/[class]/`. Legacy migration is manual, not automatic.
`chaseos intake ls` shows both quarantine and legacy file counts.

---

## Filename Convention

```
YYYYMMDD-HHMMSS__[class]__[source]__[slug].md
```

**Fields:**
- `YYYYMMDD-HHMMSS` — compact UTC timestamp, collision-safe, recency-sortable
- `[class]` — intake class (e.g. `transcript`, `digest`, `source`)
- `[source]` — source platform slug (e.g. `youtube`, `perplexity`, `web`)
- `[slug]` — title slug, max 45 chars, lowercase, hyphens only

**Examples:**
```
20260327-143022__transcript__youtube__order-flow-market-microstructure-lecture.md
20260327-143022__digest__perplexity__crypto-perps-funding-rates-q1-2026.md
20260327-143022__source__web__defi-lending-mechanics.md
20260327-143022__clipboard__manual__quick-note-on-vol-surface.md
```

Programmatic parsing: `filename.split("__")` → `[timestamp, class, source, slug_noext]`

---

## Sidecar Schema (v8.3)

Added in Pass 2: `original_name`, `original_path_or_uri`, `detected_mime`,
`route_reason`, `quarantine_status`, `workspace_hint`, `source_package_status`.

Added in Pass 3 (semantic breadcrumbs): `domain_hint`, `project_hint`, `topic_hint`,
`event_date_hint`, `origin_kind`, `desired_output_kind`.

```json
{
  "schema_version":       "8.3",
  "capture_id":           "<UUID4>",
  "content_filename":     "<filename>.md",
  "content_sha256":       "<hex>",

  "input_class":          "<class>",
  "source_platform":      "<slug>",
  "title":                "<human title>",
  "captured_at":          "<ISO 8601 UTC>",
  "capture_method":       "cli | rss | manual | agent | watched_folder | api",

  "source_url":           "<url or null>",
  "author":               "<string or null>",
  "original_name":        "<filename at source or null>",
  "original_path_or_uri": "<absolute path or URI or null>",
  "detected_mime":        "text/plain; charset=utf-8",

  "route_reason":         "input_class='transcript' -> 03_INPUTS/00_QUARANTINE/Transcript-Raw/",

  "knowledge_class":      "source-derived | user-origin",
  "injection_scan":       "not-scanned | clean | flagged",

  "quarantine_status":    "pending-review",
  "promotion_status":     "quarantine",
  "source_package_status": "not-ingested",
  "workspace_hint":       "<SIC workspace name or null>",

  "domain_hint":          "<ChaseOS domain or null>",
  "project_hint":         "<active project or null>",
  "topic_hint":           "<subject label or null>",
  "event_date_hint":      "<YYYY-MM-DD or null>",
  "origin_kind":          "human-authored | ai-generated | human-ai-collaborative | null",
  "desired_output_kind":  "synthesis | briefing | generated-idea | source-note | reference | null",

  "extra_metadata":       {}
}
```

**Gate-facing field:** `promotion_status: "quarantine"` — never changed by capture layer.
**Operator-facing field:** `quarantine_status: "pending-review"` — the human-readable state.
**SIC seam:** `source_package_status: "not-ingested"` — SIC may update this after promotion.
**Semantic breadcrumbs:** `domain_hint`, `project_hint`, `topic_hint`, `event_date_hint`, `origin_kind`, `desired_output_kind` — hints only; do not trigger SIC or change routing. See `[[AI-Generated-Output-Bridge]]`.
Backward compat: v8.1/v8.2 sidecars remain valid; consumers should use `.get()` for new fields.

---

## Module Map

```
runtime/
    cli/
        __init__.py                — CLI package marker
        main.py                    — canonical `chaseos`/`chase` CLI entrypoint
    capture/
        __init__.py                — package marker
        content_packet.py          — ContentPacket dataclass + VALID_INPUT_CLASSES
        router.py                  — routing table (with QUARANTINE_SUBDIR), slug generators,
                                     filename builder, route_reason, collision resolver
        intake_writer.py           — writes content file + sidecar v8.3; sole I/O module
        capture.py                 — public API (capture_content, dedup check, registry update) + backward-compat CLI
        dedup_registry.py          — SHA-256 dedup registry: load/save/is_duplicate/register_capture/build_registry_entry (Pass 6)
        connectors/
            __init__.py
            cli_connector.py       — CLI connector (stdin or file path, Pass 3: semantic hints)
            rss_connector.py       — RSS 2.0 + Atom 1.0 feed connector, stdlib-only (Pass 5)
            browser_connector.py   — HTML→markdown connector, stdlib html.parser, title auto-extraction (Pass 7)
            perplexity_connector.py — Perplexity API connector, stdlib urllib.request, env-var-only creds, default input_class=digest (Pass 8)
            grok_connector.py      — Grok/xAI API connector, stdlib urllib.request, XAI_API_KEY env var, default model grok-3, default input_class=digest (Pass 10)
        watch_folders.py           — watched-folder automation; config + processed-file registry; .txt/.md/.html routing (Pass 9)
        test_pass8.py              — 25 tests, 108 assertions (updated for Pass 3)
        test_pass8p2.py            — 25 Pass 2 tests, 66 assertions (updated for v8.3)
        test_pass8p3.py            — 25 Pass 3 tests, 81 assertions
        test_pass8p5.py            — 35 Pass 5 tests, 59 assertions (RSS/Atom connector)
        test_pass8p6.py            — 25 Pass 6 tests, 65 assertions (dedup registry)
        test_pass8p7.py            — 26 Pass 7 tests, ~60 assertions (browser/HTML connector)
        test_pass8p8.py            — 25 Pass 8 tests (Perplexity API connector)
        test_pass8p9.py            — 30 Pass 9 tests (watched-folder automation)
        test_pass8p10.py           — 25 Pass 10 tests (Grok/xAI API connector)
                                     Combined: 485 tests (all passing)
pyproject.toml                     — console_scripts: chaseos + chase
06_AGENTS/AI-Generated-Output-Bridge.md — canonical 4-layer output bridge architecture
```

---

## Data Flow

```
Connector (CLI / API / RSS / ...)
    └─► ContentPacket (pure data — no I/O)
            └─► capture_content(packet, vault_root)
                    └─► intake_writer.write_intake()
                            ├─► route_input_class()   → target subfolder
                            ├─► make_filename()        → deterministic name
                            ├─► resolve_unique_path()  → collision-safe path
                            ├─► write content file     → 03_INPUTS/[class]/[filename].md
                            └─► write sidecar          → 03_INPUTS/[class]/[filename].meta.json
```

---

## CLI Usage

### Canonical command (Phase 8 Pass 3+)

```bash
# Capture RSS feed (Pass 5 — default class: source)
chaseos capture rss https://feeds.feedburner.com/oreilly/radar/atom \
    --limit 10 \
    --domain trading-systems \
    --topic "market-microstructure"

# Capture RSS feed with explicit source platform override
chaseos capture rss https://www.ft.com/rss/home/uk \
    --source ft-com \
    --limit 5 \
    --workspace macro-research \
    --json

# Capture with full semantic breadcrumbs (Pass 3)
chaseos capture file transcript.txt \
    --class transcript \
    --source youtube \
    --title "Order Flow and Market Microstructure" \
    --domain trading-systems \
    --topic "market-microstructure" \
    --event-date 2026-03-15 \
    --origin-kind human-authored \
    --output-kind source-note

# Capture AI-generated content with bridge hints
chaseos capture file notebooklm-output.txt \
    --class notebooklm \
    --source notebooklm \
    --title "DeFi Lending Mechanics Synthesis" \
    --origin-kind ai-generated \
    --output-kind synthesis \
    --workspace defi-research

# Capture with workspace hint (stored for later SIC ingestion)
chaseos capture file digest.txt \
    --class digest \
    --source perplexity \
    --title "Crypto Perps Funding Rate Deep Dive" \
    --workspace "crypto-trading" \
    --domain trading-systems

# Capture from stdin
cat digest.txt | chaseos capture stdin \
    --class digest \
    --source perplexity \
    --title "Crypto Perps Funding Rate Deep Dive"

# JSON output
chaseos capture file source.txt \
    --class source \
    --source web \
    --title "DeFi Lending Mechanics" \
    --json

# List quarantine contents
chaseos intake ls
chaseos intake ls --class transcript

# Inspect a quarantined item's sidecar (Pass 3)
chaseos intake inspect 03_INPUTS/00_QUARANTINE/Digests/20260327-143022__digest__perplexity__crypto.md
chaseos intake inspect 03_INPUTS/00_QUARANTINE/Digests/20260327-143022__digest__perplexity__crypto.meta.json --json

# Health check
chaseos doctor

# Capture browser-saved HTML file (Pass 7 — title auto-extracted from HTML)
chaseos capture browser file article.html \
    --domain trading-systems \
    --topic "market-microstructure"

# Capture with explicit title override
chaseos capture browser file article.html \
    --title "Order Flow Primer" \
    --url "https://example.com/order-flow" \
    --class source \
    --source web

# Capture from Perplexity API (Pass 8 — requires PERPLEXITY_API_KEY env var)
chaseos capture perplexity --query "What is funding rate arbitrage in crypto perps?" \
    --domain trading-systems \
    --topic "market-microstructure"

# Capture Perplexity with explicit title and model override
chaseos capture perplexity \
    --query "Explain DeFi lending mechanics and risks" \
    --model sonar-pro \
    --title "DeFi Lending Mechanics Overview" \
    --workspace defi-research \
    --json

# Run full test suite (Pass 1 + Pass 2 + Pass 3 + Pass 5 + Pass 6 + Pass 7 + Pass 8)
chaseos test capture
```

### Backward-compat path (preserved, still functional)

```bash
python -m runtime.capture.capture \
    --input-class transcript \
    --source-platform youtube \
    --title "Order Flow and Market Microstructure" \
    --file transcript.txt
```

### Setup (first time)

```bash
cd <vault_root>
.venv/Scripts/pip install -e .
chaseos doctor
```

---

## Phase 8 Scope

**Pass 1 — Capture foothold:**
- ContentPacket data container
- Router (type-first organization + deterministic naming)
- intake_writer (content file + sidecar v8.1)
- CLI connector + capture.py entry point
- 03_INPUTS/ subfolder structure with index files
- Connector-Capture-Architecture.md v1.0

**Pass 2 — Structural hardening + canonical CLI:**
- pyproject.toml + `chaseos` / `chase` console_scripts
- `runtime/cli/main.py` (capture file/stdin, intake ls, doctor, test capture)
- Physical quarantine boundary (`03_INPUTS/00_QUARANTINE/[class]/` — `00_` prefix)
- Sidecar schema v8.2 (7 new fields)
- Legacy coexistence strategy

**Pass 3 — Truth sync + semantic breadcrumbs + AI-generated output bridge:**
- Sidecar schema v8.3 (6 semantic breadcrumb hint fields)
- ContentPacket 6 new optional hint fields with module-level vocabulary constants
- CLI flags: `--domain`, `--project`, `--topic`, `--event-date`, `--origin-kind`, `--output-kind`
- `chaseos intake inspect PATH` — sidecar inspection command
- `06_AGENTS/AI-Generated-Output-Bridge.md` — 4-layer output bridge architecture
- Truth-sync across ROADMAP, PROJECT_FOUNDATION, Now.md, CLAUDE.md, Ingestion-Architecture

**Pass 5 — RSS/Atom connector:**
- `rss_connector.py` — `fetch_feed()`, `detect_and_parse()`, `parse_rss()`, `parse_atom()`, `items_to_packets()`, `fetch_and_parse_feed()`
- Stdlib-only: `urllib.request` + `xml.etree.ElementTree` (no external deps)
- RSS 2.0 + Atom 1.0 both supported; auto-detect via XML probe
- Default input class: `source` (items → `Sources/` quarantine subfolder)
- Per-item provenance: `feed_url`, `feed_title`, `feed_type`, `item_guid`, `item_author`, `published_raw` in `extra_metadata`; `event_date_hint` parsed from pubDate/published
- `chaseos capture rss URL [--limit N] [--class CLASS] [--source SOURCE] [--domain ...] [--json]`
- `FeedFetchError` and `FeedParseError` exception types
- 35 tests / 59 assertions

**Pass 6 — SHA-256 dedup registry:**
- `dedup_registry.py` — `load_registry()`, `save_registry()`, `is_duplicate()`, `get_entry()`, `register_capture()`, `build_registry_entry()`, `registry_path()`
- Registry location: `<vault_root>/.chaseos/dedup_registry.json` — follows tool-state directory conventions (.git/, .venv/)
- Dedup identity: SHA-256 of normalized content body (UTF-8) — content is what's being deduplicated, not URL or title
- Fail-open: corrupt or missing registry returns empty registry; never blocks capture
- First-capture-wins: `register_capture()` is a no-op if SHA already exists; preserves original provenance
- `capture_content()` modified: checks registry before writing; returns `is_duplicate=True` result if duplicate (no file written)
- `_print_capture_result()` updated: prints `[DUPLICATE]` message showing original capture_id
- RSS repeated-run dedup: second run on same feed items returns all duplicates; verified by tests
- `chaseos intake dedup-stats [--json]` — shows registry path, total entry count, by-class breakdown
- 25 tests / 65 assertions; combined 135 tests / 379 assertions

**Pass 7 — Browser / saved-HTML connector:**
- `browser_connector.py` — `_HTMLConverter` (HTMLParser subclass): discard depth tracking for nested discard tags (script/style/noscript/nav/aside/footer); heading tags → markdown `#`–`######`; block element blank-line insertion; link buffering (`_a_buffer`, emits `[text](href)` on `</a>`, internal anchors as plain text); ordered list counter stack (`_ol_stack`); pre block pass-through; HTML comment discard; `handle_data()` routes to `_a_buffer` when inside link
- Public API: `load_html_file()` (UTF-8 first, latin-1 fallback), `html_to_markdown()` (returns markdown, html_title, first_h1), `resolve_title()` (returns resolved_title, title_source), `capture_from_browser()`
- Title precedence: cli `--title` > HTML `<title>` > first `<h1>` > filename stem (hyphens/underscores normalized to spaces)
- `capture_from_browser()` returns ContentPacket with: `detected_mime="text/html; charset=utf-8"`, `capture_method="browser"`, `extra_metadata={source_file, html_title, html_h1, title_source}`
- `chaseos capture browser file PATH [--title --url --class --source --workspace --domain --project --topic --event-date --origin-kind --output-kind --vault-root --json]`
- 3-level CLI nesting: `capture browser file` — forward-compatible for future `capture browser live URL`
- Dedup registry applies transparently (SHA-256 of extracted markdown body)
- Default: `input_class=source`, `source_platform=web`
- 26 tests / ~60 assertions; combined 161 tests / ~439 assertions

**Pass 8 — Perplexity API connector:**
- `perplexity_connector.py` — `query_perplexity()` + `capture_from_perplexity()` + `PerplexityCredentialError` + `PerplexityAPIError`
- Stdlib-only: `urllib.request` + `json` (no external HTTP dependencies)
- Credential: `PERPLEXITY_API_KEY` env var only; never stored in any file/sidecar/log/ContentPacket field
- Default input_class=digest (multi-source synthesis), source_platform=perplexity, capture_method=api, origin_kind=ai-generated
- Citations extracted from Perplexity-specific `citations` field (list of URL strings alongside OpenAI-compatible response)
- extra_metadata: query, model, citations, citation_count, response_id, usage, capture_method_detail
- Title derivation: truncates at 80 chars at word boundary with "..." when `--title` not provided
- `chaseos capture perplexity --query "..." [--model --title --class --source --workspace --domain --project --topic --event-date --origin-kind --output-kind --vault-root --json]`
- Dedup registry applies transparently (SHA-256 of answer content body)
- 25 tests; combined 186 tests / ~511 assertions, all pass

**Pass 9 — Watched-Folder Automation:**
- `watch_folders.py` — `add_folder()`, `remove_folder()`, `set_folder_enabled()`, `list_folders()`, `scan_folder()`, `scan_all_folders()` public API
- Config: `.chaseos/watch_folders.json` — co-located with dedup_registry.json; human-readable JSON; one file for all folder definitions
- Processed-file registry: `.chaseos/watch_processed.json` — path+mtime+size fingerprint; answers "did I handle this exact file version?"; fast (no re-read needed)
- Two distinct dedup layers: watch_processed ("did I handle THIS file?") + dedup_registry ("is THIS CONTENT in quarantine?")
- Routing: `.txt`/`.md` → `capture_from_cli()` with `capture_method="watched-folder"`; `.html` → `capture_from_browser()` for title auto-extraction + markdown conversion
- Per-file fail-safe: bad files marked processed to prevent infinite error retry; error logged; scan continues
- No recursive subdirectory scanning (top-level files only in Pass 9)
- No daemon/service installation; polling only (`--once` or `--interval N`)
- All semantic hint fields (domain, project, topic, workspace, origin_kind, desired_output_kind) propagated from folder config to sidecar
- `FolderScanResult` dataclass aggregates `FileCaptured` / `FileDuplicate` / `FileSkipped` / `FileError` per folder
- `chaseos watch add PATH --class CLASS [--source --ext --workspace --domain --project --topic --origin-kind --output-kind --vault-root --json]`
- `chaseos watch remove PATH [--json]`
- `chaseos watch list [--json]`
- `chaseos watch enable PATH [--json]`
- `chaseos watch disable PATH [--json]`
- `chaseos watch run --once [--json]`
- `chaseos watch run --interval N [--json]`
- 30 tests; combined 216 tests / ~541 assertions, all pass
- **Phase 8 Definition of Done met**: external content flows automatically into quarantine without manual placement

**Pass 10 — Grok/xAI API Connector + Phase 8 Closeout:**
- `grok_connector.py` — `query_grok()` + `capture_from_grok()` + `GrokCredentialError` + `GrokAPIError`
- Stdlib-only: `urllib.request` + `json` (no external HTTP dependencies)
- Credential: `XAI_API_KEY` env var only; never stored in any file/sidecar/log/ContentPacket field
- Endpoint: `POST https://api.x.ai/v1/chat/completions` (OpenAI-compatible chat completions format)
- Default model: `grok-3`; operator may override with `--model`
- Default: `input_class=digest`, `source_platform=grok`, `capture_method=api`, `origin_kind=ai-generated`
- No citations field (xAI standard completions do not include a top-level citations list)
- `finish_reason` from first choice stored in `extra_metadata` (vs. citations in Perplexity connector)
- `extra_metadata`: `query`, `model`, `response_id`, `usage`, `finish_reason`, `capture_method_detail`
- `chaseos capture grok --query "..." [--model --title --class --source --workspace --domain --project --topic --event-date --origin-kind --output-kind --vault-root --json]`
- SHA-256 dedup registry applies transparently; same answer on repeat capture → duplicate on second
- 25 tests; combined 485 tests, all pass; **Phase 8 COMPLETE**
- `06_AGENTS/Feature-Fit-Register.md` created: canonical feature/layer triage table for Phase 8 through Phase 10

**Future (Phase 9 — AOR):**
- Scheduled ingestion runs (n8n or AOR wiring)
- Connector plugin system (AOR-managed dynamic registration)

---

## Relationship to Other ChaseOS Systems

- **Gate** — governs promotion from 03_INPUTS/ to knowledge vault. Phase 8 does not touch the Gate.
- **SIC** — Source Packages are built after promotion, not at capture time. Phase 8 feeds SIC indirectly. Semantic breadcrumb hints are stored in the sidecar for future SIC use — they do not trigger SIC at capture time.
- **AOR** — Phase 9 will wire scheduled connector runs into the Autonomous Operator Runtime.
- **Knowledge Taxonomy** — all captured content is `source-derived` or `user-origin` (journal only). Never `synthesized` or `canonical-state` at capture time.
- **AI-Generated Output Bridge** — `[[AI-Generated-Output-Bridge]]` defines the 4-layer promotion path from raw quarantine → SIC workspace-local → durable generated artifacts → canonical knowledge.

---

*Connector-Capture-Architecture.md — Phase 8 Pass 10 — Phase 8 COMPLETE — 2026-03-31*


*Graph links: [[Vault-Map]]*
