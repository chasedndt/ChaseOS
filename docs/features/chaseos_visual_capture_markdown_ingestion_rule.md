---
title: "ChaseOS Visual Capture & Markdown Ingestion Rule"
feature_family: "Visual Capture & Markdown Ingestion"
product_surface: "Capture to Markdown"
architecture_layer: "Acquisition + Raw Ingestion"
status: "draft_for_repo_review"
version: "0.1.0"
created_for: "ChaseOS repository architecture review"
created_at: "2026-05-19"
standalone_app_first: true
discord_control_plane: "deferred"
canonical_ingestion: "not_allowed_in_mvp_without_review"
---

# ChaseOS Visual Capture & Markdown Ingestion Rule

## 0. Purpose

This document defines a proposed ChaseOS feature family for expanding the acquisition and ingestion layer so that useful visible context can be captured, converted into Markdown, and stored inside the local ChaseOS system as raw ingestion material.

The feature is not primarily a screenshot tool. The feature is an acquisition surface.

The product-facing concept is:

> **Capture to Markdown** — a standalone ChaseOS application feature that lets a user capture what they are currently working with, convert it into a structured Markdown artifact, and place it into raw ingestion so ChaseOS can process it safely.

The architecture-facing concept is:

> **Visual Capture & Markdown Ingestion** — a new acquisition surface that captures visual, textual, browser, window, clipboard, selected-text, accessibility, and screenshot context, then normalizes it into raw Markdown artifacts with provenance, review status, and routing metadata.

This document should be placed into the ChaseOS repository as a rule/specification document before implementation. It should be reviewed by Codex, Claude Code, or another repo-aware coding agent against the actual repository architecture before any code is written.

Current implementation note as of 2026-05-29: core Capture to Markdown is implemented for explicit source text and vault-local source files. Studio also has disabled-by-default, Settings-gated, click-only collectors for explicit screen capture, explicit clipboard text capture, explicit browser artifact capture, active ChaseOS browser capture, explicit ChaseOS-owned browser page capture, and explicit Discord artifact capture. The screen collector writes evidence first and requires the existing Preview or Save flow before Markdown is created. The clipboard text collector fills the raw text field first and requires the existing Preview or Save flow before Markdown is created. The browser artifact collector imports only an operator-selected ChaseOS-owned browser records artifact with a declared source address, then requires the existing Preview or Save flow before Markdown is created. The active ChaseOS browser collector reads only ChaseOS-owned active browser state or a controlled artifact, then requires the existing Preview or Save flow before Markdown is created. The ChaseOS-owned browser page collector launches only an isolated ChaseOS-owned browser runtime for a declared address, writes controlled artifacts first, registers that artifact as active ChaseOS browser state, and then requires the existing Preview or Save flow before Markdown is created. The Discord artifact collector imports only an operator-selected ChaseOS-owned Discord records artifact with a declared Discord source, then requires the existing Preview or Save flow before Markdown is created. Settings now includes configurable Studio-window shortcuts for all six explicit collectors, unassigned by default, active only when Capture is open, and still gated by the collector toggles. A repo-owned built-in local image text engine is verified for controlled ChaseOS pixel-text images and common Studio-font screenshots, runs in-process when selected, and drives the controlled image-to-Markdown proof without Tesseract or provider calls. Personal browser tab/profile/session/cookie/history reads, live Discord command/event capture, Discord token/webhook/bindings reads, operating-system global keyboard shortcut capture, ambient clipboard monitoring, provider calls, external sends, canonical mutation, and arbitrary photograph extraction are optional expansion lanes outside the current explicit-source release path.

---

## 1. Core Decision

ChaseOS should support a **Capture to Markdown** feature, but it should be implemented as part of the acquisition and raw ingestion system, not as a loose screenshot/OCR utility.

The MVP should be standalone-app-first.

Discord commands, external control planes, advanced runtime evidence capture, browser extensions, and deep graph integration should be deferred until the local standalone application implementation is stable.

The correct MVP direction is:

```txt
Standalone ChaseOS App
    ↓
User-triggered capture
    ↓
Extract visible/available context
    ↓
Normalize to structured Markdown
    ↓
Save into raw ingestion
    ↓
AOR / ingestion router processes it
    ↓
Review / promotion pipeline decides whether it becomes canonical knowledge
```

The incorrect implementation direction is:

```txt
Screenshot everything
    ↓
OCR everything
    ↓
Dump text directly into knowledge nodes
```

That path is weak, noisy, privacy-risky, and likely to pollute the repository.

---

## 2. Naming

### 2.1 Feature family name

```txt
Visual Capture & Markdown Ingestion
```

### 2.2 Product-facing name

```txt
Capture to Markdown
```

### 2.3 Internal shorthand

```txt
VCMI
```

### 2.4 Architecture layer

```txt
Acquisition + Raw Ingestion
```

### 2.5 Repository naming note

This document uses the canonical repository and product name `ChaseOS`.

Older source notes for this feature used non-canonical names. Current product copy should use `ChaseOS`; implementation agents should preserve existing code identifiers unless a separate rename pass is approved and tested.

---

## 3. Non-Negotiable Principles

These rules should be treated as hard constraints.

### 3.1 This is an acquisition feature

The feature exists to help ChaseOS acquire useful context and place it into raw ingestion.

It is not a screenshot toy, not a note-taking gimmick, and not a direct knowledge-node writer.

### 3.2 Raw ingestion first

All captured Markdown artifacts must be saved into raw ingestion first.

They should not automatically become canonical knowledge nodes.

They should not automatically mutate the long-term graph.

They should not automatically update project memory without review or a trusted ingestion pass.

### 3.3 No always-on capture by default

The MVP must not run as an invisible always-on screen recorder.

Capture should be explicit and user-triggered.

A later enterprise/user-configured mode could support automatic runtime evidence capture, but that is out of scope for the MVP.

### 3.4 DOM/text extraction beats screenshot OCR

The extraction hierarchy must prefer structured sources before OCR.

OCR should be a fallback, not the main path.

### 3.5 Preserve source and provenance

Every artifact must record:

- Capture method
- Capture timestamp
- User-selected intent/profile
- Source application/window/browser context when available
- Screenshot evidence if used
- Confidence level
- Raw ingestion path
- Review status
- Whether redaction was applied

### 3.6 User intent matters

The same visible content may be captured for different reasons.

For example:

- Archiving exact source text
- Creating a research note
- Capturing a bug/error
- Turning a chatbot answer into a feature spec
- Performing a UI/UX teardown
- Saving a prompt or workflow
- Creating an implementation plan

The feature must allow the user to specify or adjust capture intent before or immediately after saving.

### 3.7 Transformations must be separated from raw capture

The system should distinguish between:

1. **Raw capture** — what was actually extracted from the screen/page/window/clipboard.
2. **Normalized Markdown** — structured Markdown representation of the raw capture.
3. **Generated interpretation** — summaries, analysis, suggested routing, action items, or rewritten output.

Raw capture should not be silently rewritten.

### 3.8 Local-first

The MVP should save artifacts locally into the ChaseOS repository/local system.

Cloud processing, remote OCR, or external LLM processing should not be assumed.

### 3.9 Standalone app first

The first implementation target is the actual ChaseOS standalone application.

Discord, Slack, webhooks, remote command surfaces, and external control planes are explicitly deferred.

### 3.10 Review before promotion

Captured artifacts can be saved quickly, but promotion into canonical knowledge must go through the ingestion/AOR/review pipeline.

---

## 4. Problem Statement

Modern users work across many surfaces:

- Chatbot web applications
- Documentation pages
- SaaS dashboards
- Browser research sessions
- Local development tools
- Error screens
- Product UIs
- Agent runtime panels
- Code editors
- Design tools
- Terminals

A user may see something useful and want ChaseOS to remember it, process it, route it, or turn it into Markdown.

The current manual pattern often looks like this:

```txt
See useful information
    ↓
Copy content manually
    ↓
Ask a chatbot to convert it to Markdown
    ↓
Save a .md file manually somewhere
    ↓
Tell an agent/runtime where the file is
    ↓
Hope the file is routed correctly
```

ChaseOS should reduce this friction.

The desired pattern is:

```txt
See useful information
    ↓
Trigger Capture to Markdown
    ↓
Choose/confirm intent
    ↓
ChaseOS saves a structured raw-ingestion Markdown artifact
    ↓
AOR/ingestion pipeline routes it
    ↓
The repository can process it safely
```

---

## 5. Why A Screenshot-Only Feature Is Too Weak

A screenshot-only implementation loses too much information.

Screenshots are useful evidence, but screenshots are a poor primary data source when better sources exist.

### 5.1 Screenshot-only weaknesses

Screenshot-only capture has these problems:

- Text extraction depends on OCR accuracy.
- Links are lost unless separately extracted.
- Headings and hierarchy are lost.
- Code blocks are often mangled.
- Tables become unreliable.
- Hidden metadata such as URL and page title may be missing.
- Browser state and provenance may be incomplete.
- Long pages require scrolling/stitching.
- OCR can confuse characters in code, commands, prices, file paths, and API names.
- Sensitive content may be captured accidentally.
- The resulting Markdown may be noisy and low-trust.

### 5.2 Correct screenshot role

Screenshots should be used for:

- Evidence attachment
- Visual UI reference
- Error screen reference
- Canvas/image-only content
- Non-selectable content
- Cases where DOM/text/clipboard/accessibility extraction fails
- Human review support

Screenshots should not be the default extraction method when direct text, DOM, clipboard, or accessibility data is available.

---

## 6. Extraction Hierarchy

The feature should use a layered acquisition strategy.

Preferred order:

```txt
1. Selected text / explicit clipboard capture
2. Controlled browser or webview DOM extraction
3. Browser harness extraction where ChaseOS owns the session
4. Accessibility tree extraction
5. Active window metadata + visible text where OS APIs allow it
6. Region/window/fullscreen screenshot
7. Local OCR fallback
8. Human correction / review
```

The exact order may differ depending on the active capture mode, but the principle remains:

> Use the highest-fidelity available source first, and degrade gracefully to lower-fidelity sources only when necessary.

---

## 7. Standalone App Capture Reality

A key UX question is:

> If the user is looking at another browser tab or another app, do they need to switch back into the ChaseOS executable to click a button?

The answer should be: **not necessarily**.

The standalone app should support more than one trigger model.

### 7.1 In-app capture button

Inside ChaseOS, there can be a visible **Capture to Markdown** button.

This is useful when the user is already in the ChaseOS app.

However, this alone is not enough, because the user may be viewing another app or browser tab.

### 7.2 Global hotkey

The standalone app should support a global hotkey, for example:

```txt
Ctrl/Cmd + Shift + M
```

The exact shortcut should be configurable.

The hotkey should open a small capture palette over the current screen.

Example palette:

```txt
Capture to Markdown

[1] Selected text / clipboard
[2] Active window
[3] Region
[4] Full screen
[5] Error/debug capture
[6] UI teardown capture

Intent: [Auto-detect / choose profile]
Destination: Raw ingestion
```

The hotkey model allows capture without needing to switch tabs.

### 7.3 System tray / menu bar trigger

The standalone app may expose a tray/menu bar action:

```txt
ChaseOS → Capture to Markdown
```

This is useful for users who prefer mouse-driven workflows.

### 7.4 Floating mini-capture overlay

A later version can include a small floating capture control.

This should be optional, not always-on.

### 7.5 Window/region picker

For active window or region capture, the app can invoke an OS-level picker:

```txt
Select window or region to capture
```

This is safer than blind full-screen capture.

### 7.6 Controlled browser session

If ChaseOS includes its own embedded browser, browser-use harness, or managed webview, then ChaseOS can extract DOM/text/links directly from that controlled surface.

This is the strongest path for browser content.

### 7.7 External browser limitation

If the user is using an external browser such as Chrome, Edge, Safari, Firefox, Brave, or Arc, the standalone app cannot reliably extract page DOM from arbitrary tabs unless one of the following is true:

- A browser extension is installed.
- The browser exposes a supported automation/debugging interface and the user grants permission.
- The page is opened inside a ChaseOS-controlled browser/webview.
- The user copies/selects content manually.
- OS accessibility APIs expose usable text.

Therefore, the MVP should not assume direct DOM access for all external browser tabs.

For external browser pages, MVP options are:

```txt
Best: selected text / clipboard capture
Good: accessibility tree capture where available
Acceptable: screenshot + OCR fallback
Better later: official browser extension or controlled browser integration
```

---

## 8. Capture Intent and Tone Control

The user raised a critical point:

> If ChaseOS saves what the user sees into Markdown, how does it know the tone or context in which to save it?

The correct answer is:

> ChaseOS should not guess too aggressively. It should capture raw material faithfully, then let the user select or confirm an intent/profile that controls how the Markdown is organized and what additional interpretation is added.

### 8.1 Raw capture should be tone-neutral

The raw extracted content should remain faithful to the source.

The system should not rewrite source content into a different tone by default.

For example, if the source is a chatbot answer, the raw capture should preserve the answer as closely as possible.

If the source is an error screen, the raw capture should preserve the error message.

If the source is a pricing page, the raw capture should preserve the visible pricing content and source details.

### 8.2 Interpretation can have a profile

A generated analysis section can have a tone/profile.

Examples:

- Research note
- Feature specification
- Implementation task
- UI teardown
- Debug report
- Prompt capture
- Meeting note
- Source archive
- Competitive analysis
- Product decision note

The profile controls the sections added around the raw capture, not the raw capture itself.

### 8.3 Capture profiles

The MVP should support a small number of profiles.

Recommended MVP profiles:

```txt
1. Raw Archive
2. Research Note
3. Feature / Product Spec
4. Debug / Error Capture
5. UI / UX Teardown
6. Prompt / Chatbot Output Capture
```

Later profiles:

```txt
7. Competitive Analysis
8. Implementation Plan
9. Meeting / Call Notes
10. Workflow / SOP Capture
11. Legal / Policy Review Capture
12. Agent Runtime Evidence
```

### 8.4 Profile selection UX

When the user triggers capture, ChaseOS should show a compact selector:

```txt
Save as:
[ Raw Archive ] [ Research Note ] [ Feature Spec ] [ Debug ] [ UI Teardown ] [ Prompt Capture ]

Destination:
Raw ingestion

Optional note:
[ user note field ]

[Capture]
```

The user should not need to manually format every Markdown file.

The system should generate the structure automatically based on the selected profile.

### 8.5 Auto-detect is allowed but should be overridable

The system may suggest an intent based on cues.

Examples:

- If the screen contains stack traces or `Error`, suggest `Debug / Error Capture`.
- If the active page is ChatGPT/Claude/Gemini/etc., suggest `Prompt / Chatbot Output Capture`.
- If the user selects a region of a web app UI, suggest `UI / UX Teardown`.
- If the content contains headings, citations, documentation, or search results, suggest `Research Note`.

But the user must be able to override the suggestion.

### 8.6 Profile metadata

Every Markdown artifact should record the profile.

Example:

```yaml
capture_profile: "feature_spec"
transform_policy: "preserve_raw_plus_structured_interpretation"
user_intent: "Turn visible chatbot output into a ChaseOS feature spec for repo review."
```

### 8.7 Tone policy

The system should use this rule:

```txt
Raw Capture: preserve source tone and content.
Generated Summary: concise, neutral, implementation-oriented.
Generated Recommendations: clearly labeled as system interpretation.
User Notes: preserved exactly unless user asks for rewriting.
```

No generated interpretation should be confused with source content.

---

## 9. Markdown Formatting Rule

The user should not have to manually format every file.

ChaseOS should produce consistent Markdown automatically.

The user may optionally correct, enrich, or re-route the artifact after capture.

### 9.1 Every artifact must include frontmatter

All generated Markdown artifacts should include YAML frontmatter.

Required frontmatter fields:

```yaml
---
artifact_type: "visual_capture"
capture_id: ""
capture_profile: ""
capture_method: ""
source_app: ""
source_window_title: ""
source_url: ""
source_title: ""
captured_at: ""
captured_by: "user"
local_timezone: ""
raw_ingestion_path: ""
status: "raw_ingested"
canonical_status: "not_promoted"
requires_review: true
confidence: "high|medium|low"
redaction_status: "not_scanned|scanned_clean|redacted|needs_review"
screenshots: []
attachments: []
tags: []
---
```

Optional frontmatter fields:

```yaml
project_hint: ""
feature_family_hint: ""
repository_hint: ""
aor_route_hint: ""
ingestion_batch_id: ""
parent_capture_id: ""
related_capture_ids: []
source_hash: ""
content_hash: ""
ocr_engine: ""
accessibility_provider: ""
browser_session_id: ""
agent_runtime_id: ""
user_note: ""
```

### 9.2 Standard Markdown sections

Every artifact should use this base structure:

```md
# Capture Title

## Capture Summary

## Source & Provenance

## User Intent

## Raw Extracted Content

## Structured Notes

## Generated Interpretation

## Suggested Routing

## Review Checklist

## Attachments

## Ingestion Metadata
```

Not every section needs to be long. But the structure should be consistent enough that the ingestion pipeline can parse it.

### 9.3 Raw content must be clearly separated

Example:

```md
## Raw Extracted Content

> The following section is extracted source material. It should not be treated as ChaseOS interpretation.

```text
[raw extracted content here]
```
```

### 9.4 Generated content must be labeled

Example:

```md
## Generated Interpretation

> The following section was generated by ChaseOS based on the capture profile. It should be reviewed before promotion.
```

### 9.5 Human correction section

Every file should include a place for manual correction.

Example:

```md
## Human Corrections / Review Notes

- [ ] Source content looks accurate
- [ ] Capture profile is correct
- [ ] Sensitive data removed or approved
- [ ] Routing is correct
- [ ] Safe for canonical ingestion

Reviewer notes:

```txt

```
```

---

## 10. Raw Ingestion Placement

The feature should write into raw ingestion, not directly into knowledge nodes.

The actual folder path should be confirmed against the current repository.

Recommended conceptual path:

```txt
/ChaseOS/raw_ingestion/visual_capture/YYYY/MM/DD/<capture_id>.md
```

Alternative repository-style paths:

```txt
/ChaseOS/00_RAW_INGESTION/visual_capture/YYYY/MM/DD/<capture_id>.md
/ChaseOS/data/raw_ingestion/visual_capture/YYYY/MM/DD/<capture_id>.md
/ChaseOS/vault/_raw_ingestion/visual_capture/YYYY/MM/DD/<capture_id>.md
/ChaseOS/ingestion/raw/visual_capture/YYYY/MM/DD/<capture_id>.md
```

The repo-aware implementation agent must inspect the repository and choose the existing raw ingestion convention if one exists.

### 10.1 File naming

Recommended filename pattern:

```txt
vcap_<YYYYMMDD>_<HHMMSS>_<short-source-slug>_<short-id>.md
```

Example:

```txt
vcap_20260519_143022_chatgpt_feature_plan_a1b2c3.md
```

### 10.2 Attachment folder

Screenshots and raw assets should be stored next to the Markdown file or in a sibling attachments directory.

Example:

```txt
raw_ingestion/visual_capture/2026/05/19/
  vcap_20260519_143022_chatgpt_feature_plan_a1b2c3.md
  attachments/
    vcap_20260519_143022_chatgpt_feature_plan_a1b2c3.png
    vcap_20260519_143022_chatgpt_feature_plan_a1b2c3.raw.txt
    vcap_20260519_143022_chatgpt_feature_plan_a1b2c3.metadata.json
```

### 10.3 Raw assets

Depending on capture method, raw assets may include:

- Screenshot image
- Raw OCR text
- Raw clipboard text
- Raw selected text
- Raw DOM snapshot
- Raw accessibility tree excerpt
- Source metadata JSON
- Capture log JSON

These raw assets should not be required for every capture, but the artifact should reference them when present.

---

## 11. AOR / Ingestion Router Role

The user specifically noted that ChaseOS has an AOR and that captured files should go into raw ingestion rather than knowledge nodes immediately.

This document assumes the AOR or repository ingestion router is responsible for downstream routing and processing.

The implementation should not bypass that system.

### 11.1 AOR responsibilities

The AOR / ingestion router should decide:

- Whether the capture belongs to a project, feature family, bug, research bucket, or archive.
- Whether the capture needs redaction.
- Whether the capture should be normalized further.
- Whether the capture should be embedded/indexed.
- Whether graph nodes should be proposed.
- Whether the artifact should be promoted, rejected, merged, or archived.
- Whether the user must review before promotion.

### 11.2 Capture feature responsibilities

The Capture to Markdown feature should only do the acquisition-side job:

- Capture available content.
- Create a structured Markdown artifact.
- Attach provenance.
- Save into raw ingestion.
- Notify/queue the AOR.
- Expose review actions in the standalone app.

### 11.3 Explicit boundary

The capture feature must not directly perform these actions in MVP:

- Create canonical knowledge nodes.
- Mutate graph memory.
- Rewrite project plans.
- Commit to repository automatically.
- Send to Discord.
- Trigger external agents without user review.
- Auto-promote low-confidence OCR output.

---

## 12. Lifecycle States

A captured artifact should move through explicit states.

Recommended states:

```txt
captured
raw_ingested
queued_for_aor
triaged
normalized
needs_review
approved_for_promotion
promoted
rejected
archived
```

### 12.1 State definitions

#### captured

The capture action completed and raw material exists in memory or temp storage.

#### raw_ingested

A Markdown artifact has been written into raw ingestion.

#### queued_for_aor

The artifact has been queued for routing/classification.

#### triaged

The AOR has assigned route hints, project hints, or review requirements.

#### normalized

The artifact has been converted into a cleaner internal representation.

#### needs_review

The capture requires user/human review before promotion.

#### approved_for_promotion

A user or trusted rule has approved promotion.

#### promoted

The artifact has been accepted into canonical knowledge, project files, index, or graph.

#### rejected

The artifact is not useful or should not be ingested.

#### archived

The artifact is retained for audit/history but not active.

### 12.2 MVP state requirement

MVP only needs:

```txt
captured → raw_ingested → queued_for_aor / needs_review
```

Promotion can be deferred to existing repository ingestion logic.

---

## 13. Capture Modes

The feature should support multiple capture modes over time.

### 13.1 MVP capture modes

Recommended MVP modes:

```txt
1. Clipboard to Markdown
2. Selected Text to Markdown
3. Active Window Screenshot + Metadata
4. Region Screenshot + Optional OCR
5. ChaseOS-controlled Browser/Webview Page to Markdown, if such a surface already exists
```

### 13.2 Deferred capture modes

Deferred modes:

```txt
1. External browser extension DOM capture
2. Full-page scroll capture
3. Multi-monitor capture
4. Video/frame sequence capture
5. Agent runtime before/after evidence packets
6. Automatic recurring capture
7. Discord capture commands
8. Remote control-plane capture commands
9. Deep graph promotion from capture
```

### 13.3 Clipboard capture

Clipboard capture is a very strong MVP path because it is simple and reliable.

Workflow:

```txt
User selects text in any app
User copies it
User triggers ChaseOS Capture to Markdown
ChaseOS reads clipboard
User chooses profile
ChaseOS writes Markdown into raw ingestion
```

Pros:

- Works across many apps.
- Avoids OCR.
- Preserves text better than screenshot.
- Easy to implement.
- Low privacy risk compared to full-screen capture if user intentionally copied content.

Cons:

- Requires the user to copy/select content.
- Does not capture layout or screenshot evidence unless added.

### 13.4 Selected text capture

If OS APIs allow ChaseOS to read currently selected text, this can remove the copy step.

This may be platform-dependent.

The implementation should treat selected-text capture as optional unless the current app framework supports it reliably.

### 13.5 Active window screenshot

Active window screenshot is useful for:

- Error screens
- UI teardown
- Visual evidence
- Non-selectable content
- App state capture

It should include metadata:

- App name
- Window title
- Timestamp
- Display ID if available
- OCR status
- Screenshot path

### 13.6 Region capture

Region capture is useful because it limits accidental sensitive data capture.

For MVP, region capture can produce:

- Screenshot attachment
- OCR text if available
- Markdown wrapper
- User-selected intent/profile

### 13.7 ChaseOS-controlled browser/webview capture

If the standalone ChaseOS app contains a controlled browser, webview, or browser-use harness, this should become the strongest MVP browser capture path.

It can extract:

- URL
- Title
- Headings
- Visible text
- Links
- Code blocks
- Tables where possible
- Page metadata
- Screenshot evidence

This is superior to external browser screenshot capture.

### 13.8 External browser capture

For external browsers, MVP should not promise full DOM extraction.

Possible options:

- Clipboard/selected text capture
- Accessibility extraction
- Screenshot + OCR
- Browser extension later
- Browser automation/debugging later with explicit permission

---

## 14. Capture Profiles

Profiles determine Markdown organization and generated interpretation sections.

They do not overwrite raw extracted content.

### 14.1 Profile: Raw Archive

Use when the user wants to preserve visible/source content with minimal interpretation.

Sections:

```md
# Raw Capture

## Source & Provenance
## User Note
## Raw Extracted Content
## Attachments
## Review Checklist
```

Tone:

```txt
Neutral. Minimal. Preserve source.
```

### 14.2 Profile: Research Note

Use for docs, articles, search results, webpages, product research, and public information.

Sections:

```md
# Research Capture

## Capture Summary
## Source & Provenance
## User Intent
## Raw Extracted Content
## Key Points
## Open Questions
## Suggested Routing
## Review Checklist
```

Tone:

```txt
Concise, neutral, source-aware.
```

### 14.3 Profile: Feature / Product Spec

Use for chatbot outputs, product plans, feature families, architecture decisions, implementation plans, and repo specs.

Sections:

```md
# Feature Capture

## Capture Summary
## Source & Provenance
## User Intent
## Raw Extracted Content
## Feature Interpretation
## Architecture Implications
## MVP Scope
## Deferred Scope
## Risks
## Suggested Repository Routing
## Review Checklist
```

Tone:

```txt
Implementation-oriented. Clear. Repo-ready. No hype.
```

### 14.4 Profile: Debug / Error Capture

Use for errors, stack traces, broken screens, failing commands, runtime bugs, and production issues.

Sections:

```md
# Debug Capture

## Error Summary
## Source & Provenance
## Environment Clues
## Raw Error Text
## Screenshot Evidence
## Reproduction Clues
## Suspected Cause
## Suggested Next Checks
## Review Checklist
```

Tone:

```txt
Technical, precise, evidence-first.
```

### 14.5 Profile: UI / UX Teardown

Use when capturing application screens, dashboards, product UI, onboarding flows, settings panels, or competitor interfaces.

Sections:

```md
# UI / UX Capture

## Screen Summary
## Source & Provenance
## Visual Structure
## Visible Copy
## Interaction Elements
## UX Observations
## Opportunities / Issues
## Screenshot Evidence
## Review Checklist
```

Tone:

```txt
Product/design focused. Observational. Distinguish facts from opinions.
```

### 14.6 Profile: Prompt / Chatbot Output Capture

Use when capturing content from AI assistants, chatbot outputs, prompt chains, plans, or generated Markdown.

Sections:

```md
# Chatbot / Prompt Capture

## Capture Summary
## Source & Provenance
## User Intent
## Prompt Context
## Raw Assistant Output
## Extracted Action Items
## Suggested Repository Routing
## Review Checklist
```

Tone:

```txt
Preserve original answer. Convert into clean, routeable Markdown only where needed.
```

---

## 15. Markdown Template: Base Artifact

This is the base artifact format.

```md
---
artifact_type: "visual_capture"
capture_id: "vcap_YYYYMMDD_HHMMSS_shortid"
capture_profile: "research_note"
capture_method: "clipboard|selected_text|controlled_browser_dom|accessibility|active_window_screenshot|region_screenshot|ocr_fallback"
source_app: ""
source_window_title: ""
source_url: ""
source_title: ""
captured_at: "YYYY-MM-DDTHH:MM:SS+TZ"
captured_by: "user"
local_timezone: ""
raw_ingestion_path: ""
status: "raw_ingested"
canonical_status: "not_promoted"
requires_review: true
confidence: "high"
redaction_status: "not_scanned"
project_hint: ""
feature_family_hint: ""
aor_route_hint: ""
screenshots: []
attachments: []
tags:
  - acquisition
  - raw-ingestion
  - capture-to-markdown
---

# Capture Title

## Capture Summary

Brief generated summary of what was captured. This is not source text.

## Source & Provenance

- Capture ID: `vcap_...`
- Captured at: `...`
- Capture method: `...`
- Source app: `...`
- Source window: `...`
- Source URL: `...`
- Confidence: `...`
- Redaction status: `...`

## User Intent

```txt
User-provided note or selected capture profile.
```

## Raw Extracted Content

> This section contains extracted source material. Review before canonical ingestion.

```text
...
```

## Structured Notes

- ...

## Generated Interpretation

> This section is generated by ChaseOS based on the selected capture profile. It should be reviewed before promotion.

### Key Points

- ...

### Suggested Actions

- ...

## Suggested Routing

- Raw ingestion route: `...`
- Project hint: `...`
- Feature family hint: `...`
- AOR route hint: `...`

## Review Checklist

- [ ] Raw content appears accurate
- [ ] Capture profile is correct
- [ ] Sensitive data has been scanned/redacted
- [ ] Routing is correct
- [ ] Safe to promote beyond raw ingestion

## Attachments

- Screenshot: `...`
- Metadata: `...`

## Ingestion Metadata

```json
{
  "capture_id": "",
  "status": "raw_ingested",
  "canonical_status": "not_promoted",
  "requires_review": true
}
```
```

---

## 16. Data Contract

The feature should create a machine-readable capture packet alongside the Markdown file.

Recommended JSON contract:

```json
{
  "schema_version": "0.1.0",
  "artifact_type": "visual_capture",
  "capture_id": "vcap_20260519_143022_a1b2c3",
  "capture_profile": "feature_spec",
  "capture_method": "clipboard",
  "captured_at": "2026-05-19T14:30:22+01:00",
  "captured_by": "user",
  "source": {
    "app": "Chrome",
    "window_title": "ChatGPT - Feature planning",
    "url": "",
    "title": ""
  },
  "local_context": {
    "timezone": "Europe/London",
    "device_id": "",
    "os": "",
    "ChaseOS_app_version": ""
  },
  "content": {
    "raw_text_path": "attachments/vcap_20260519_143022_a1b2c3.raw.txt",
    "markdown_path": "vcap_20260519_143022_chatgpt_feature_plan_a1b2c3.md",
    "content_hash": "",
    "source_hash": ""
  },
  "assets": {
    "screenshots": [],
    "dom_snapshot": null,
    "accessibility_snapshot": null,
    "ocr_output": null
  },
  "ingestion": {
    "raw_ingestion_path": "raw_ingestion/visual_capture/2026/05/19/",
    "status": "raw_ingested",
    "canonical_status": "not_promoted",
    "requires_review": true,
    "aor_route_hint": "",
    "project_hint": "",
    "feature_family_hint": ""
  },
  "quality": {
    "confidence": "high",
    "redaction_status": "not_scanned",
    "ocr_confidence": null,
    "warnings": []
  }
}
```

---

## 17. Standalone App UI Requirements

The MVP UI should be simple.

### 17.1 Main capture entry

In the ChaseOS standalone application:

```txt
Button: Capture to Markdown
```

Clicking it opens:

```txt
Capture Source
- Clipboard
- Selected Text
- Active Window Screenshot
- Region Screenshot
- Current ChaseOS Browser Page, if available

Capture Profile
- Raw Archive
- Research Note
- Feature / Product Spec
- Debug / Error Capture
- UI / UX Teardown
- Prompt / Chatbot Output Capture

Destination
- Raw ingestion

Optional note
[ text field ]

[Capture]
```

### 17.2 Global hotkey palette

The standalone app should eventually support a global hotkey.

Palette:

```txt
Capture to Markdown

Source:
[Clipboard] [Selected Text] [Active Window] [Region]

Profile:
[Auto] [Raw] [Research] [Feature Spec] [Debug] [UI Teardown] [Prompt]

Destination:
Raw ingestion

[Capture]
```

### 17.3 Raw ingestion queue UI

The app should expose recent captures.

```txt
Raw Captures

- vcap_20260519_143022_chatgpt_feature_plan_a1b2c3.md
  Profile: Feature Spec
  Status: raw_ingested
  Review: required

Actions:
[Open Markdown] [Reveal in Folder] [Send to AOR] [Mark Reviewed] [Reject]
```

### 17.4 No Discord UI in MVP

There should be no MVP requirement for Discord commands.

Any Discord/control-plane integration should be documented as deferred.

---

## 18. API / Internal Service Surface

The repo-aware implementation agent should adapt this to the current codebase.

Conceptual service names:

```txt
CaptureOrchestrator
CaptureProfileService
CaptureSourceAdapter
MarkdownArtifactBuilder
RawIngestionWriter
CaptureReviewQueue
AORIngestionBridge
RedactionScanner
```

### 18.1 CaptureOrchestrator

Responsible for coordinating a capture request.

Input:

```json
{
  "source_type": "clipboard",
  "profile": "feature_spec",
  "user_note": "",
  "include_screenshot": false
}
```

Output:

```json
{
  "capture_id": "vcap_...",
  "markdown_path": "...",
  "status": "raw_ingested",
  "requires_review": true
}
```

### 18.2 CaptureProfileService

Responsible for profile definitions and Markdown section selection.

### 18.3 CaptureSourceAdapter

Adapter interface for each source type.

Conceptual interface:

```ts
interface CaptureSourceAdapter {
  canCapture(context: CaptureContext): Promise<boolean>;
  capture(request: CaptureRequest): Promise<CapturePayload>;
}
```

### 18.4 MarkdownArtifactBuilder

Responsible for frontmatter, sections, formatting, and safe separation between raw content and generated interpretation.

### 18.5 RawIngestionWriter

Responsible for writing Markdown and attachments to raw ingestion paths.

### 18.6 AORIngestionBridge

Responsible for notifying/queuing the AOR or ingestion router after raw write.

This bridge should not promote content directly.

### 18.7 RedactionScanner

Responsible for detecting sensitive values before or after writing.

Potential detections:

- API keys
- Tokens
- Password-like strings
- Private keys
- Emails
- Phone numbers
- Addresses
- Payment data
- Secret environment variables
- Access credentials

For MVP, the redaction scanner can start as warning-only if automatic redaction is not safe yet.

---

## 19. Security and Privacy Guardrails

This feature touches the user's screen and local files, so guardrails matter.

### 19.1 Explicit user trigger

No capture should happen without user action in MVP.

Allowed triggers:

- User clicks button.
- User presses configured hotkey.
- User selects capture from tray/menu.

Not allowed in MVP:

- Invisible continuous capture.
- Background screen recording.
- Unbounded agent-initiated screen capture.
- Automatic capture of every tab/window.

### 19.2 Visible confirmation

After capture, the app should show:

- What was captured
- Where it was saved
- Profile used
- Whether review is required
- Whether sensitive data warning exists

### 19.3 Region/window over full-screen

The app should prefer scoped capture modes.

Recommended order:

```txt
Selected text / clipboard → active window → region → full screen
```

Full-screen capture should be available only with clear user selection.

### 19.4 Sensitive data scanning

Before promotion, and ideally before raw ingestion indexing, scan for secrets.

Detected secrets should mark the artifact:

```yaml
redaction_status: "needs_review"
requires_review: true
```

### 19.5 Redaction policy

The app should support:

- Warning-only mode
- User-approved redaction
- Automatic redaction for obvious secrets
- Preservation of raw asset only if user allows it

For MVP, safest path:

```txt
Write raw artifact locally → mark sensitive warning → block canonical promotion until review
```

### 19.6 Screenshot evidence sensitivity

Screenshots may contain more sensitive data than extracted text.

If a screenshot is attached, the Markdown must reference it clearly.

Example:

```yaml
screenshots:
  - path: "attachments/vcap_...png"
    sensitivity: "unreviewed"
```

### 19.7 Local-only default

No capture artifact should be uploaded externally by default.

### 19.8 Agent permissions

Agents may be allowed to propose a capture, but not silently perform or promote one in MVP.

Allowed:

```txt
Agent: "This error screen should be captured. Capture now?"
User: approves
```

Not allowed:

```txt
Agent silently captures screen and writes canonical knowledge.
```

### 19.9 Audit log

Every capture should produce an audit entry.

Minimum audit fields:

```json
{
  "event_type": "visual_capture_created",
  "capture_id": "",
  "captured_at": "",
  "capture_method": "",
  "profile": "",
  "raw_ingestion_path": "",
  "requires_review": true
}
```

---

## 20. MVP Scope

The MVP should be deliberately narrow.

### 20.1 MVP goal

Enable a ChaseOS standalone app user to capture useful content into structured Markdown files stored in raw ingestion.

### 20.2 MVP must include

```txt
1. Standalone app capture entry point
2. Clipboard capture
3. Manual/selected text capture if supported
4. Region or active-window screenshot capture
5. Optional local OCR fallback if available
6. Capture profile selector
7. Markdown artifact generation with frontmatter
8. Raw ingestion writer
9. Attachment handling
10. Review-required status
11. Recent captures list or raw ingestion queue
12. AOR queue/notification hook if the repository already supports it
```

### 20.3 MVP should include if easy

```txt
1. Global hotkey capture palette
2. Active app/window metadata
3. Simple secret scan warning
4. ChaseOS-controlled browser/webview capture if already present
5. Open/reveal captured Markdown from app UI
```

### 20.4 MVP must not include

```txt
1. Discord commands
2. Always-on screen capture
3. Unreviewed graph mutation
4. Automatic canonical knowledge node creation
5. External browser DOM extraction without explicit integration
6. Remote/cloud OCR requirement
7. Multi-monitor advanced capture
8. Video capture
9. Agent-initiated silent capture
10. Automatic repository commits
```

---

## 21. Implementation Passes

### Pass 0 — Docs-only architecture

Create repository documentation defining:

- Feature family
- Data contract
- Markdown format
- Capture profiles
- Raw ingestion flow
- Guardrails
- Deferred scope

No code yet.

### Pass 1 — Clipboard/Manual Text to Markdown

Build the simplest reliable capture path:

```txt
Read clipboard or user-pasted text
Choose profile
Generate Markdown
Save to raw ingestion
List recent captures
```

This validates the artifact format and ingestion path without OS-level screen complexity.

### Pass 2 — Active Window / Region Screenshot

Add screenshot capture:

```txt
Capture active window or selected region
Save screenshot attachment
Generate Markdown wrapper
Optionally run OCR if local OCR is available
```

### Pass 3 — Capture Profile Intelligence

Add profile templates and optional auto-suggestions.

Examples:

- Error text → Debug
- Chatbot page/window title → Prompt Capture
- Docs URL/title → Research Note
- Web app UI screenshot → UI Teardown

### Pass 4 — AOR Raw Ingestion Hook

Wire the raw capture artifact into existing AOR/ingestion queue.

Do not promote automatically.

### Pass 5 — Controlled Browser/Webview DOM Capture

If ChaseOS has a managed browser surface, add DOM extraction.

Extract:

- URL
- Title
- Headings
- Visible text
- Links
- Code blocks
- Tables if possible
- Screenshot evidence if requested

### Pass 6 — Review Queue UI

Add a review panel:

- Recent captures
- Status
- Sensitive warnings
- Open Markdown
- Reveal in folder
- Mark reviewed
- Send to AOR
- Reject/archive

### Pass 7 — Deferred Integrations

Only after the standalone app flow is solid:

- Discord commands
- Browser extension
- Agent runtime evidence capture
- Automated graph proposals
- External control planes

---

## 22. Repository Placement Suggestions

The repo-aware agent must inspect the actual repository before final placement.

Potential docs paths:

```txt
docs/feature-families/visual-capture-markdown-ingestion.md
docs/rules/acquisition/visual-capture-markdown-ingestion-rule.md
docs/architecture/acquisition/visual-capture-markdown-ingestion.md
docs/contracts/visual-capture-packet.md
docs/security/visual-capture-guardrails.md
```

Potential source paths:

```txt
src/acquisition/visual_capture/
src/ingestion/visual_capture/
src/features/capture_to_markdown/
apps/desktop/src/features/capture-to-markdown/
packages/acquisition/visual-capture/
packages/ingestion/raw-capture/
```

Potential UI paths:

```txt
apps/desktop/src/components/CaptureToMarkdown/
apps/desktop/src/features/capture-to-markdown/
apps/desktop/src/pages/RawCaptures/
```

Potential data paths:

```txt
raw_ingestion/visual_capture/
data/raw_ingestion/visual_capture/
vault/_raw_ingestion/visual_capture/
```

The implementation must follow existing repo conventions rather than creating duplicate architecture.

---

## 23. Acceptance Criteria

### 23.1 Artifact creation

A user can trigger Capture to Markdown from the standalone app and create a `.md` file in raw ingestion.

### 23.2 Frontmatter

The file includes required frontmatter fields.

### 23.3 Profile selection

The user can choose a capture profile.

### 23.4 Raw/source separation

The Markdown clearly separates raw extracted content from generated interpretation.

### 23.5 Raw ingestion destination

The artifact is saved into raw ingestion, not canonical knowledge nodes.

### 23.6 Review required

The artifact is marked as requiring review before promotion.

### 23.7 Attachment support

If a screenshot is captured, it is saved as an attachment and referenced from the Markdown.

### 23.8 Recent captures

The standalone app can show/reveal recent capture artifacts.

### 23.9 No Discord dependency

The feature works without Discord/control-plane integration.

### 23.10 No silent capture

The feature requires explicit user trigger.

---

## 24. Test Plan

### 24.1 Unit tests

Test Markdown builder:

- Generates valid YAML frontmatter.
- Escapes raw content safely.
- Preserves raw content.
- Inserts required sections.
- Applies profile-specific sections.
- Marks review required.

Test capture profile service:

- Returns correct templates.
- Suggests profile from content cues.
- Allows override.

Test raw ingestion writer:

- Creates expected directories.
- Writes Markdown file.
- Writes metadata JSON.
- Writes attachments.
- Does not overwrite existing files.
- Produces stable capture IDs.

Test redaction scanner:

- Detects obvious API keys/tokens.
- Marks redaction status correctly.
- Does not destroy raw content unless configured.

### 24.2 Integration tests

Test clipboard capture:

```txt
Given clipboard text
When user captures with Feature Spec profile
Then Markdown file exists in raw ingestion
And frontmatter has capture_method=clipboard
And raw content matches clipboard text
```

Test screenshot capture:

```txt
Given active window or selected region
When user captures with Debug profile
Then screenshot attachment exists
And Markdown references screenshot
And artifact requires review
```

Test AOR queue hook:

```txt
Given raw capture saved
When AOR hook is enabled
Then capture packet is queued but not promoted
```

### 24.3 UI tests

Test standalone app capture dialog:

- User can open capture dialog.
- User can select source.
- User can select profile.
- User can add note.
- User can capture.
- User sees saved path.
- User can open/reveal artifact.

### 24.4 Security tests

Test that:

- Capture does not run without explicit trigger.
- Full-screen capture requires explicit choice.
- Sensitive data warning marks review required.
- External upload does not happen by default.
- Agents cannot silently capture in MVP.

### 24.5 Regression tests

Test that:

- Captures do not write into canonical knowledge paths.
- Captures do not mutate graph/index unless existing ingestion pipeline later approves.
- Low-confidence OCR is not promoted automatically.

---

## 25. Risks and Mitigations

### 25.1 Risk: garbage ingestion

If every screen becomes a Markdown file, raw ingestion may become noisy.

Mitigation:

- User-triggered capture only.
- Profile selector.
- Raw ingestion queue.
- Review requirement.
- AOR triage.
- Reject/archive support.

### 25.2 Risk: OCR errors

OCR can misread code, file paths, tokens, error messages, and UI labels.

Mitigation:

- Prefer clipboard/DOM/text/accessibility first.
- Mark OCR confidence.
- Attach screenshot evidence.
- Require review for OCR-heavy captures.

### 25.3 Risk: privacy leakage

Screenshots can capture unrelated private data.

Mitigation:

- Prefer selected text/region capture.
- Avoid always-on capture.
- Add visible confirmation.
- Secret/PII scanning.
- Review before promotion.

### 25.4 Risk: wrong tone/context

The system may save the content in the wrong format or interpret it incorrectly.

Mitigation:

- Capture profiles.
- User override.
- Raw/source separation.
- Generated interpretation clearly labeled.
- Human correction section.

### 25.5 Risk: bypassing existing architecture

A standalone capture feature could accidentally create duplicate ingestion logic.

Mitigation:

- Save only to raw ingestion.
- Use existing AOR/router if present.
- Repo-aware agent must inspect current architecture before implementation.
- No direct graph mutation in MVP.

### 25.6 Risk: external browser limitations

Standalone app may not access external browser DOM.

Mitigation:

- Be honest in implementation scope.
- Support clipboard/selected text first.
- Use screenshot/OCR fallback.
- Add browser extension later if needed.
- Use controlled browser/webview where available.

### 25.7 Risk: feature bloat

The feature could expand into an overly complex capture suite.

Mitigation:

- MVP is limited to local standalone app raw ingestion.
- Defer Discord, extensions, video, automation, and graph mutation.
- Build passes incrementally.

---

## 26. Open Questions for Repo Review

The repo-aware coding agent must answer these before implementation:

1. What is the canonical raw ingestion path in the current ChaseOS repository?
2. Does the repository already have an AOR, ingestion router, source packet, or evidence packet system?
3. Does the repository already define Markdown artifact schemas?
4. Does the standalone app already have a capture/screenshot/clipboard utility?
5. Does the standalone app already support global hotkeys?
6. Does the standalone app already include a managed browser/webview/browser-use harness?
7. Does the repository have an existing review queue UI?
8. Does the repository have a secrets/PII scanner?
9. What app framework is used for the standalone executable?
10. What OS platforms are targeted first?
11. What permission model is needed for screenshots and accessibility capture?
12. Where should capture artifacts be stored in dev versus production?
13. How should the AOR be notified of new raw ingestion artifacts?
14. Should OCR be included in MVP or deferred?
15. What is the exact file naming convention used elsewhere in the repo?

---

## 27. Recommended MVP Build Decision

Recommendation:

```txt
Build the feature family, but start with a narrow standalone-app MVP.
```

The first build should not attempt full universal screen understanding.

The first build should prove:

```txt
User can capture content → ChaseOS creates structured Markdown → file lands in raw ingestion → AOR/review pipeline can process it
```

That is the real value.

---

## 28. Final Feature Definition

### 28.1 One-sentence definition

**Capture to Markdown** is a standalone ChaseOS acquisition feature that converts user-triggered clipboard, selected text, browser/webview, window, region, or screenshot context into structured Markdown artifacts saved into raw ingestion for AOR-driven processing.

### 28.2 MVP definition

The MVP is:

```txt
A local, standalone-app capture flow that lets a user capture clipboard/selected text or a scoped screenshot, choose a capture profile, generate a structured Markdown artifact with provenance, and save it into raw ingestion without directly creating knowledge nodes.
```

### 28.3 What this feature is not

It is not:

- A generic screenshot app.
- A screen recorder.
- A Discord-first command system.
- A direct graph mutation tool.
- A universal browser DOM extractor in MVP.
- An always-on surveillance feature.
- A replacement for the AOR or ingestion pipeline.

### 28.4 Why it belongs in ChaseOS

It belongs because it strengthens the operating system's ability to acquire and process real working context.

It reduces manual friction.

It makes local Markdown creation easier.

It improves raw ingestion.

It gives ChaseOS a better path from what the user sees to what the system can process.

It keeps provenance and review intact.

It respects the existing AOR/ingestion architecture.

---

## 29. Suggested Repository Rule Text

This section can be copied into a shorter repo rule if needed.

```txt
Rule: Visual Capture & Markdown Ingestion

ChaseOS may provide user-triggered capture features that convert visible, selected, clipboard, browser, window, region, or screenshot context into Markdown artifacts.

All such artifacts must be written to raw ingestion first, with provenance metadata, capture method, selected profile, timestamp, review status, and sensitivity/redaction status.

Capture artifacts must not directly create canonical knowledge nodes or mutate graph/index state without passing through the existing AOR/ingestion/review pipeline.

Structured extraction sources such as clipboard, selected text, controlled browser DOM, and accessibility data must be preferred over screenshot OCR. Screenshot/OCR capture is allowed as a fallback or evidence attachment.

The standalone ChaseOS application is the first implementation target. Discord and other control-plane commands are deferred.

The MVP must require explicit user action, must not run always-on screen capture, and must mark captured artifacts as requiring review before promotion.
```

---

## 30. Appendix: Example Feature Spec Capture Artifact

```md
---
artifact_type: "visual_capture"
capture_id: "vcap_20260519_143022_a1b2c3"
capture_profile: "feature_spec"
capture_method: "clipboard"
source_app: "External Browser"
source_window_title: "Chatbot Feature Planning"
source_url: ""
source_title: ""
captured_at: "2026-05-19T14:30:22+01:00"
captured_by: "user"
local_timezone: "Europe/London"
raw_ingestion_path: "raw_ingestion/visual_capture/2026/05/19/vcap_20260519_143022_chatbot_feature_plan_a1b2c3.md"
status: "raw_ingested"
canonical_status: "not_promoted"
requires_review: true
confidence: "high"
redaction_status: "not_scanned"
project_hint: "ChaseOS"
feature_family_hint: "Visual Capture & Markdown Ingestion"
aor_route_hint: "feature_family_review"
screenshots: []
attachments:
  - "attachments/vcap_20260519_143022_a1b2c3.raw.txt"
tags:
  - acquisition
  - raw-ingestion
  - capture-to-markdown
  - feature-spec
---

# Feature Capture: Visual Capture & Markdown Ingestion

## Capture Summary

This capture contains a proposed ChaseOS feature family for converting visible or selected working context into structured Markdown artifacts that are saved into raw ingestion.

## Source & Provenance

- Capture ID: `vcap_20260519_143022_a1b2c3`
- Captured at: `2026-05-19T14:30:22+01:00`
- Capture method: `clipboard`
- Source app: `External Browser`
- Source window: `Chatbot Feature Planning`
- Confidence: `high`
- Status: `raw_ingested`
- Canonical status: `not_promoted`

## User Intent

```txt
Save this feature planning output into ChaseOS raw ingestion so the repository-aware agent can review how to wire it into the current architecture.
```

## Raw Extracted Content

> This section contains source material captured from the user's selected/copied content.

```text
[raw captured content here]
```

## Feature Interpretation

> This section is generated from the selected `feature_spec` capture profile and must be reviewed before promotion.

### Proposed Feature Family

Visual Capture & Markdown Ingestion.

### Product Surface

Capture to Markdown.

### Architecture Layer

Acquisition + Raw Ingestion.

### MVP

Standalone app capture to Markdown, saved into raw ingestion.

## Suggested Repository Routing

- Raw ingestion route: `raw_ingestion/visual_capture/`
- Review route: AOR / feature-family review
- Do not promote automatically

## Review Checklist

- [ ] Raw content is accurate
- [ ] Feature profile is correct
- [ ] Sensitive data has been scanned
- [ ] Raw ingestion route is correct
- [ ] Repo-aware agent has reviewed architecture fit
- [ ] Safe to promote or implement
```

---

## 31. Appendix: Example Debug Capture Artifact

```md
---
artifact_type: "visual_capture"
capture_id: "vcap_20260519_151100_d4e5f6"
capture_profile: "debug_error"
capture_method: "region_screenshot_ocr"
source_app: "ChaseOS Standalone App"
source_window_title: "Runtime Error"
captured_at: "2026-05-19T15:11:00+01:00"
captured_by: "user"
status: "raw_ingested"
canonical_status: "not_promoted"
requires_review: true
confidence: "medium"
redaction_status: "needs_review"
screenshots:
  - "attachments/vcap_20260519_151100_d4e5f6.png"
tags:
  - debug
  - error-capture
  - raw-ingestion
---

# Debug Capture: Runtime Error

## Error Summary

A runtime error was captured from a selected screen region. OCR was used, so the extracted error text requires review.

## Source & Provenance

- Capture method: `region_screenshot_ocr`
- Confidence: `medium`
- Screenshot: `attachments/vcap_20260519_151100_d4e5f6.png`

## Raw Error Text

```text
[OCR output here]
```

## Screenshot Evidence

See attached screenshot.

## Suspected Cause

> Generated interpretation. Review before acting.

- ...

## Suggested Next Checks

- ...

## Review Checklist

- [ ] OCR text matches screenshot
- [ ] No secrets are exposed
- [ ] Error is routed to the correct project/repo
- [ ] Safe to create bug/task from this capture
```

---

## 32. Appendix: Example UI Teardown Capture Artifact

```md
---
artifact_type: "visual_capture"
capture_id: "vcap_20260519_160500_g7h8i9"
capture_profile: "ui_ux_teardown"
capture_method: "active_window_screenshot"
source_app: "External Browser"
source_window_title: "SaaS Dashboard"
captured_at: "2026-05-19T16:05:00+01:00"
captured_by: "user"
status: "raw_ingested"
canonical_status: "not_promoted"
requires_review: true
confidence: "medium"
redaction_status: "not_scanned"
screenshots:
  - "attachments/vcap_20260519_160500_g7h8i9.png"
tags:
  - ui-teardown
  - product-research
  - raw-ingestion
---

# UI / UX Capture: SaaS Dashboard

## Screen Summary

A dashboard screen was captured for UI/UX analysis.

## Source & Provenance

- Capture method: `active_window_screenshot`
- Source window: `SaaS Dashboard`
- Screenshot: `attachments/vcap_20260519_160500_g7h8i9.png`

## Visual Structure

> Generated observation based on screenshot. Review before promotion.

- Header/navigation area
- Main dashboard content
- Action buttons
- Sidebar or secondary navigation if visible

## Visible Copy

```text
[OCR/accessibility extracted copy if available]
```

## UX Observations

- ...

## Opportunities / Issues

- ...

## Review Checklist

- [ ] Screenshot is safe to keep
- [ ] Sensitive information removed or approved
- [ ] UI observations are accurate
- [ ] Route to product/design research if useful
```

---

## 33. Deferred Future Work

The following ideas are valuable but should not block MVP.

### 33.1 Browser extension

A browser extension could provide stronger external browser capture:

- DOM extraction
- Selection extraction
- Full-page capture
- URL/title metadata
- Code block capture
- Link extraction

This should be added only after the standalone app raw ingestion flow is proven.

### 33.2 Runtime evidence packets

Agents/runtimes could generate before/after capture packets for auditability.

This is useful for:

- Browser automation
- App testing
- UI changes
- Debugging
- Operator workflows

This should require clear permissions and should not become always-on surveillance.

### 33.3 Visual diff

Compare before and after screenshots/DOM captures.

Useful for:

- UI testing
- Agent execution audits
- Design changes
- Regression checks

### 33.4 Video-to-Markdown

Capture short screen recordings and convert them into step-by-step Markdown.

This is powerful but far beyond MVP.

### 33.5 Discord/control-plane commands

Potential later commands:

```txt
/capture clipboard
/capture active-window
/capture latest
/ingest latest
```

Deferred until the standalone app and raw ingestion flow are stable.

### 33.6 Direct task generation

Capture artifact could propose tasks/issues after review.

Do not auto-create tasks in MVP.

---

## 34. Summary

The feature should be built as an expansion of ChaseOS acquisition and raw ingestion.

The best version is not screenshot-only.

The best version is:

```txt
User-triggered local capture
    + profile-aware Markdown generation
    + provenance
    + raw ingestion placement
    + AOR/review routing
    + no automatic canonical promotion
```

This gives ChaseOS a practical bridge between what a user sees and what the system can process.

It supports research, chatbot output capture, product planning, UI teardown, debugging, and local system work without making the repository messy or unsafe.

The MVP should stay focused:

```txt
Standalone app first.
Raw ingestion only.
Clipboard/selected text/screenshot capture.
Markdown artifact generation.
Review required.
AOR integration when available.
Discord deferred.
```
