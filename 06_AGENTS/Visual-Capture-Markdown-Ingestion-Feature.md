---
date: 2026-05-29
runtime: Codex
type: feature-node
status: CORE MARKDOWN CAPTURE VERIFIED / DISPLAY REGION CAPTURE IMPLEMENTED IN SOURCE / CAPTURE AND SETTINGS OPEN-SAFETY VERIFIED / PACKAGED CAPTURE AND SETTINGS PASSIVE OPEN-SAFETY AND NATIVE SCREENSHOT CONFIRMATION VERIFIED / EXPLICIT SCREEN, DISPLAY REGION, CLIPBOARD, BROWSER ARTIFACT, ACTIVE CHASEOS BROWSER, CHASEOS BROWSER PAGE, AND DISCORD ARTIFACT COLLECTORS SETTINGS-GATED / CHASEOS BROWSER PAGE CONTROLLED LIVE PROOF VERIFIED / CONTROLLED IMAGE TO MARKDOWN LIVE PROOF VERIFIED / BUILT-IN LOCAL IMAGE TEXT ENGINE QUALITY VERIFIED FOR PIXEL AND COMMON STUDIO-FONT SCREENSHOTS / FULL STUDIO-WINDOW COLLECTOR SHORTCUT COVERAGE VERIFIED / PACKAGED FULL DOWNSTREAM CHAIN VERIFIED / PACKAGED DOWNSTREAM FAILURE MATRIX VERIFIED / CONTROLLED SOURCE-SHAPE MATRIX VERIFIED / PRODUCT LANGUAGE HARDENING VERIFIED / COMMAND HELP PRODUCT LANGUAGE VERIFIED / EXPLICIT CAPTURE PATHS RELEASE READY
parent_families:
  - Connector / Capture Automation
  - Acquisition + Normalization Layer
  - Source Intelligence Core
studio_surface: Capture
---

# Visual Capture Markdown Ingestion Feature

Visual Capture Markdown Ingestion, product-facing as **Capture to Markdown**, is the ChaseOS feature for turning explicit user-triggered visual/browser/window/clipboard/text capture into governed raw Markdown intake with provenance, review state, and downstream promotion gates.

## Current Scope

- Raw capture remains quarantine/untrusted until reviewed.
- Reviewed capture can be transformed into Acquisition preview artifacts.
- Pass 51 corrected the scope boundary: core Markdown capture is explicit source text or vault-file input to Markdown preview, raw-quarantine save, recent-capture listing, sidecar/packet review update, duplicate handling, and redaction blocking. Focused backend and Studio panel tests plus rendered Studio proof are green. Optical character recognition, active browser capture, screen capture, Studio-window shortcuts, Discord capture, Source Intelligence Core ingestion, canonical promotion, agent dispatch, and broad downstream approval workflows are optional extension lanes, not blockers for core Markdown capture.
- Passes 1-44 have verified the local core, quarantine writer, Studio panel, operator review, downstream gate readiness, source-pack approval preview, exact-digest approved source-pack write execution, source-pack Agent Orchestration Runtime dispatch readiness, Agent Orchestration Runtime dispatch approval design, pending approval request writing, pending decision/consumption readiness, approval decision writing, approval consumption execution, a guarded local Agent Bus task writer, read-only Agent Bus task claim readiness, exact-digest/statement-gated local Agent Bus task claiming, read-only claimed-task Agent Orchestration Runtime dry-run readiness, a governed claimed-task Agent Orchestration Runtime dry-run executor, a governed claimed-task review-status lifecycle update, a read-only full-dispatch readiness validator, an exact-digest/statement-gated source-pack Agent Orchestration Runtime full-dispatch executor, read-only Source Intelligence Core ingestion readiness after Pass 28 source-pack writeback, read-only Source Intelligence Core ingestion approval design, a create-only pending Source Intelligence Core ingestion approval request writer, read-only Source Intelligence Core ingestion approval decision/consumption readiness, a create-only Source Intelligence Core ingestion approval decision writer, an exact-digest/statement-gated Source Intelligence Core approval consumption executor, an exact-digest/statement-gated Source Intelligence Core ingestion executor for reviewed Capture to Markdown source packages, a read-only graph-indexing readiness preview over the completed Source Intelligence Core ingestion artifact, an exact-digest/statement-gated graph-indexing executor that can write a create-only marker, graph snapshot, graph-store manifest/current pointer, and create-only execution artifact in verified fixtures, a read-only canonical-promotion readiness preview over the completed graph-indexing artifact/current graph-store pointer, a read-only canonical-promotion approval design, a create-only pending canonical-promotion approval request writer that writes no approval decision and no canonical knowledge, a read-only canonical-promotion approval decision/consumption readiness validator that previews the future decision and consumption contract without writing either one, a create-only canonical-promotion approval decision writer that writes one approved or rejected decision artifact after exact digest, decision value, and operator-statement validation, an exact-once canonical-promotion approval consumption executor that writes a marker before the consumption artifact, and an exact-digest/statement-gated canonical-promotion executor that writes one reviewed capture knowledge note, one managed Knowledge Index route block, one exact-once marker, and one execution artifact in verified fixtures.
- Pass 13 verified source-pack write approval preview.
- Pass 14 verified an exact digest and exact operator-statement gated source-pack write executor.
- Passes 15-44 verified the governed path from written source pack to approved consumption, one local Agent Bus task, read-only task claimability checks, guarded task claim marker/claim artifact writes, claimed-task dry-run packet readiness, exact-digest/statement-gated Agent Orchestration Runtime dry-run execution, exact-digest/statement-gated transition of the claimed task into `review`, read-only future full-dispatch packet readiness, a guarded Agent Orchestration Runtime full-dispatch execution lane limited to `source_pack_builder` source-pack writeback evidence, read-only future Source Intelligence Core ingestion packet readiness, read-only future Source Intelligence Core approval packet design, create-only pending Source Intelligence Core approval request writing, read-only Source Intelligence Core approval decision/consumption readiness, create-only Source Intelligence Core approval decision writing, exact-once Source Intelligence Core approval consumption, exact-once Source Intelligence Core workspace/source-package/membership writing, read-only graph candidate preview readiness over the completed ingestion artifact, guarded graph snapshot/store writing in disposable fixtures, read-only canonical-promotion candidate preview readiness over graph-indexing evidence, read-only canonical-promotion approval packet design, create-only pending canonical-promotion approval request writing, read-only canonical-promotion approval decision/consumption readiness, create-only canonical-promotion approval decision writing, exact-once canonical-promotion approval consumption, and guarded canonical knowledge note/index promotion in disposable fixtures.
- The 2026-05-27 real-repository proof ran the governed Source Intelligence Core ingestion, graph indexing, canonical-promotion approval chain, and final canonical promotion against the real Markdown Guide web capture. It wrote a real reviewed-captures Source Intelligence Core workspace/source package, real graph snapshot/store pointer, real reviewed-capture canonical note, and real Knowledge Index route block.
- Pass 47 added a source text quality guard for common UTF-8 / Windows-1252 mojibake before Source Intelligence Core normalization and before canonical note display. New Source Intelligence Core packages and canonical promotion artifacts now carry repair policy, repair-applied status, replacement count, and source/display digest metadata while preserving original capture provenance.
- Pass 48 ran a fresh real public web replay from `https://example.com/` through Capture to Markdown, operator review, source package writing, Agent Orchestration Runtime dispatch, Source Intelligence Core ingestion, graph indexing, and canonical promotion. The new real source package, ingestion artifact, canonical note, and canonical promotion artifact all carry source text quality metadata. Output Markdown, canonical note, proof report, and Studio panel screenshots were captured as visual proof.
- Pass 49 restored `runtime/studio/capture_to_markdown_panel.py` to maintainable normal source by replacing the recovered-bytecode loader with explicit source for the base panel, preview, save, review, and guarded source-package/Agent Orchestration Runtime dispatch helpers while preserving Pass 26 through Pass 44 wrappers. Focused shell tests, Source Intelligence Core ingestion/canonical-promotion regressions, rendered Studio visual quality assurance, and output Markdown screenshot proof passed after the restoration. The packaged `ChaseOS-Studio.exe` Capture route launched, but native screenshot content was blank or near-uniform.
- Pass 50 repaired packaged Capture route screenshot timing by capping the internal Qt screenshot delay to 1000-1500 milliseconds, rebuilt `dist/studio/ChaseOS-Studio.exe`, and produced a nonblank packaged Capture route proof at `#/capture-markdown`. The pass also normalized visible Capture status and helper copy away from shortcut-heavy labels toward full product language, while preserving exact internal approval statements and code identifiers for compatibility.
- Pass 51 proved the narrowed core Markdown capture contract after correcting scope: source text or vault file to Markdown preview, raw-quarantine save, recent listing, review sidecar/packet update, duplicate handling, and redaction blocking. The pass also changed visible Capture navigation and panel copy from broad capture-source promises to the implemented source-text-to-Markdown surface.
- Pass 52 wired the optional Capture extras into the correct product surfaces without expanding live-capture authority. The Capture page now shows product-facing capture source cards for available explicit inputs, governed manual/covered source paths, and downstream approval-gated consumers. Settings now exposes configurable Studio-window Capture shortcuts, rejects duplicate shortcut assignments, rejects unsupported operating-system-wide capture shortcut assignments, and records that operating-system global keyboard shortcuts, selected-text reads, ambient clipboard reads, active browser profile/session/cookie/history reads, and live Discord listeners are outside the current release path.
- Pass 56 extended packaged Capture proof from raw-quarantine save into visible review-state update. The rebuilt packaged `dist/studio/ChaseOS-Studio.exe` proves source cards, Settings Capture shortcuts, preview, save, recent readback, visible Reviewed decision application, sidecar review status update, visual-capture packet review status update, stable Markdown body hash, no approval-artifact writes, native screenshot capture, nonblank content, and owned-process termination. It also tightened Capture product copy so the visible Capture profile and Agent Orchestration Runtime / Source Intelligence Core status text use full product language.
- Pass 57 implemented the local-only image text extraction adapter for Capture to Markdown. Explicit vault-local screenshot images can now be converted into Markdown source text through Tesseract or a configured local command, with attachment validation, no cloud provider calls, extracted-text digest metadata, secret-like text scanning, redaction blocking, sidecar/review policy persistence, command-line flags, Studio source-mode wiring, and frontend command input. This host currently has no real local image text engine installed, so real Tesseract quality and packaged executable clickthrough remain unverified; focused tests use a fake local command.
- Pass 58 added the product-facing Settings surface for local screenshot image text extraction. Settings can now view and save the local optical character recognition command and timeout, rejects secret-like commands and shell launchers, exposes engine readiness, and feeds the saved command into the Capture page when the per-capture field is blank. This pass also confirmed the normal Capture page load does not run the image text command; extraction still occurs only after an explicit Capture preview/save action for a vault-local image path.
- Pass 59 added packaged executable image-to-Markdown clickthrough proof for the local image text extraction lane. The rebuilt `dist/studio/ChaseOS-Studio.exe` drove Settings command readback, Capture source-card selection, explicit vault-local image path preview, raw-quarantine Markdown save, visible review-state update, sidecar and visual-capture packet persistence, no approval-artifact writes, nonblank native screenshot capture, owned-process termination, temporary Settings restoration, and cleanup of duplicate build output. The proof uses a temporary local command because this host still has no real Tesseract or equivalent engine installed, so real image text quality remains unverified.
- Pass 60 added packaged executable failure-state proof for the image-to-Markdown lane. The rebuilt `dist/studio/ChaseOS-Studio.exe` now proves that missing local engine, no extracted text, command failure, command timeout, and sensitive extracted text paths are visible in the Capture page, keep Save disabled, write no raw quarantine Markdown, write no approval artifacts, restore temporary Settings, terminate only the owned packaged process, and preserve no-window Windows subprocess hardening for Studio diagnostic probes. Real local engine quality remains unverified because this host still has no Tesseract or equivalent engine installed.
- Pass 61 added a product-facing Capture release-readiness surface directly to the Capture page. It shows what is ready now, what remains approval-gated downstream, which collector paths are manual or covered by explicit source flows, and which release proof items are still open. The rebuilt packaged executable proof passed with `ok=true`: visible release readiness, full Source Intelligence Core and Agent Orchestration Runtime wording, Settings shortcuts, source cards, governed collector posture, approval-gated downstream consumers, raw-quarantine Markdown save, Reviewed sidecar/packet state, nonblank native screenshot evidence, no approval artifacts, and owned-process termination. This pass also rejected shell launchers such as PowerShell at the lower local image text adapter even when supplied through the environment command path, and added a regression test proving Capture page model load does not start subprocesses.
- Pass 62 added the real local image text quality fixture harness for Capture to Markdown. The harness generates bounded no-text, dense-text, low-contrast, table, and mixed-language fixture images, runs only a configured local engine, writes JSON/Markdown proof reports, and feeds the latest result into Settings and Capture release readiness. On this host the live report is `blocked_missing_local_engine`, so real engine quality is still not verified. The rebuilt packaged executable passed the Capture clickthrough after stale proof runners were cleared, including Settings shortcut visibility and the new real-engine fixture row; generated build/test folders and duplicate packaged proof processes were removed while preserving `dist/studio/ChaseOS-Studio.exe`, `dist/studio/ChaseOS-Installer.exe`, and proof evidence.
- Pass 63 added packaged downstream source-package release hardening for Capture to Markdown. The rebuilt `dist/studio/ChaseOS-Studio.exe` drives manual text capture through preview, raw-quarantine save, review, source-package approval preview, approved source-package write, visible downstream boundary copy, and Agent Orchestration Runtime readiness preview. The proof verifies create-only source-package artifact writes, no approval-artifact writes, full Source Intelligence Core / canonical promotion / Agent Orchestration Runtime boundary wording, Settings shortcut visibility, nonblank native screenshot evidence, owned-process termination, and cleanup of failed proof/build duplicates. Deeper packaged Source Intelligence Core ingestion, graph indexing, canonical promotion, and downstream failure-state proofs remain open.
- Pass 64 added packaged full downstream-chain proof for Capture to Markdown. The rebuilt `dist/studio/ChaseOS-Studio.exe` now drives manual text capture through preview, raw-quarantine save, review, source-package approval preview/write, Agent Orchestration Runtime approval, local Agent Bus task writing and claiming, Agent Orchestration Runtime dry run, task review status lifecycle, Agent Orchestration Runtime full dispatch, Source Intelligence Core ingestion approval and execution, graph indexing, canonical-promotion approval, and canonical knowledge promotion. The packaged proof passed with `ok=true`, verified create-only downstream approval artifacts, source-package artifacts, graph/canonical outputs, nonblank native screenshot evidence, Settings shortcut visibility, and owned-process termination. Pass 65 then verified the packaged source-package guard-failure path. Remaining open work is real local optical character recognition engine quality, live collectors, deeper downstream failure-state proof, and broader real-source coverage.
- Pass 65 added packaged source-package guard-failure release hardening for Capture to Markdown. The rebuilt `dist/studio/ChaseOS-Studio.exe` now renders a durable blocked guard card when an incorrect source-package operator statement is submitted, keeps the raw Markdown save and Reviewed state intact, and verifies no source-package artifacts or approval artifacts are written. The packaged proof passed with `ok=true`, verified nonblank native screenshot evidence and owned-process termination, and cleaned generated build/test leftovers while preserving the rebuilt executable and passing evidence. Deeper downstream failure-state proofs after source-package write remain open.
- Pass 66 added the explicit Studio screen capture collector for Capture to Markdown. The collector is disabled by default, visible/configurable in Settings, and appears on the Capture page as either `disabled_in_settings` or `available_click_to_capture`. It captures screen pixels only after Settings is enabled and the operator clicks the Capture source card, writes screenshot evidence and an audit JSON file, and does not write raw quarantine Markdown until the existing Preview or Save flow is used. Active browser capture, Discord capture, ambient screen recording, operating-system global keyboard shortcuts, clipboard reads, provider calls, external sends, and canonical mutation remain blocked. The rebuilt `dist/studio/ChaseOS-Studio.exe` SHA-256 is `9E6F874E5E49AD35328C7D1C1364968365017E40B3441CDFE5AF4917F3103F09`; packaged evidence is retained under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-explicit-screen-collector-packaged-action.*`, while generated fake capture/source-package/approval artifacts from that proof were removed from the personal instance.
- Pass 67 added the explicit Studio clipboard text collector for Capture to Markdown. The collector is disabled by default, visible/configurable in Settings, and appears on the Capture page as either `disabled_in_settings` or `available_click_to_capture`. It reads current clipboard text only after Settings is enabled and the operator clicks the Capture source card, fills the raw text field, and does not write raw quarantine Markdown until the existing Preview or Save flow is used. Ambient clipboard monitoring, active browser capture, Discord capture, operating-system global keyboard shortcuts, provider calls, external sends, and canonical mutation remain blocked. The rebuilt `dist/studio/ChaseOS-Studio.exe` SHA-256 is `558B3AE019E290A06DF3FF633C2AA156FCDA816B6DBFD0A695E3CDB360BFCDD3`; packaged evidence is retained under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-explicit-clipboard-collector-packaged-action.*`, while generated fake capture/source-package/approval artifacts from that proof were removed from the personal instance.
- Pass 68 added configurable Studio-window shortcuts for the explicit screen collector and explicit clipboard text collector. These shortcut rows are visible in Settings, unassigned by default, configurable like the existing Capture shortcuts, and still work only inside the Studio window when the Capture page is open. They do not register operating-system global shortcuts, do not read selected text from other applications, and do not bypass the collector Settings toggles. The rebuilt `dist/studio/ChaseOS-Studio.exe` SHA-256 is `43BA620A07946110D6C6848B8AFB5E33732A641323AD78904B7BCE22EB20B558`; packaged guard-failure evidence is retained under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-collector-hotkey-settings-packaged-guard.*`, while the fake raw-quarantine capture generated by that proof was removed from the personal instance.
- Pass 69 added the explicit browser artifact collector for Capture to Markdown. The collector is disabled by default, visible/configurable in Settings, and appears on the Capture page as either `disabled_in_settings` or `available_select_artifact`. It imports only an operator-selected ChaseOS-owned browser records artifact with a declared source address, then feeds extracted text into the existing Preview or Save flow without writing raw quarantine Markdown on click. Live active browser tab capture, browser profiles, browser sessions, cookies, browser history, Discord capture, provider calls, external sends, and canonical mutation remain blocked. The rebuilt `dist/studio/ChaseOS-Studio.exe` SHA-256 is `6675AF98734854979929E74945641D317D237180DE9A4CBD35EAE4046CF0B778`; packaged guard-failure evidence is retained under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-browser-artifact-collector-packaged-guard-rerun.*`, while generated fake raw-quarantine captures and obsolete failed proof output from this pass were removed from the personal instance.
- Pass 70 added the explicit Discord artifact collector for Capture to Markdown. The collector is disabled by default, visible/configurable in Settings, and appears on the Capture page as either `disabled_in_settings` or `available_select_artifact`. It imports only an operator-selected ChaseOS-owned Discord records artifact with a declared Discord source, then fills the raw text field and uses the existing Preview or Save flow before Markdown is written. Direct Discord events, tokens, webhooks, bindings reads, direct Discord application programming interface calls, provider calls, external sends, and canonical mutation remain blocked. The rebuilt `dist/studio/ChaseOS-Studio.exe` SHA-256 is `80683EDDECB08975DB7FB8D9CFA80F154A09DE42E811BFF04CBD774DCEEF2C1B`; packaged guard-failure evidence is retained under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-discord-artifact-collector-packaged-guard-final.*`, while generated fake raw-quarantine captures and obsolete failed proof output from this pass were removed from the personal instance.
- Pass 71 added packaged Capture to Markdown window-size matrix proof. The Studio shell now accepts proof-only window width and height environment variables during packaged visual proof mode, the packaged Capture proof runner can run repeated compact/wide cases, and the Capture release-readiness surface reads the latest retained matrix evidence. The rebuilt `dist/studio/ChaseOS-Studio.exe` SHA-256 is `8E746A0C89AC2C5835A9BBC6BBB2677657A90AA4B3B4EC8BAB5D10EBB38522D1`; retained evidence under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-window-size-matrix-final.*` proves compact `1000 x 700` and wide `1600 x 1000` packaged Capture runs both passed, with captured dimensions increasing from `2000 x 1400` to `2740 x 1784`. The generated fake raw-quarantine proof captures were removed after proof.
- Pass 72 added packaged downstream failure-state matrix proof support and product-facing blocked cards after source-package write. That historical pass verified incorrect Agent Orchestration Runtime approval request statements and incorrect Source Intelligence Core approval request statements, but the canonical promotion approval request case was blocked at Source Intelligence Core ingestion result-card output. Pass 73 supersedes this partial result.
- Pass 73 completed the packaged downstream failure-state matrix. Source Intelligence Core ingestion failures now render product-facing blocked cards with diagnostics, packaged proof diagnostics now report missing Source Intelligence Core ingestion data instead of a generic selector timeout, the Source Intelligence Core workspace reader accepts existing UTF-8 byte-order-mark workspace files, and the command-line proof runner can execute a single downstream failure case. The rebuilt `dist/studio/ChaseOS-Studio.exe` SHA-256 is `013872F4B6297192D067F229E92F042E1724D06BAEE56420CBE72871F44283C6`; retained evidence under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-downstream-failure-state-matrix-remediated-final.*` verifies all three packaged downstream guard states: Agent Orchestration Runtime approval request, Source Intelligence Core approval request, and canonical promotion approval request. Generated build output, bytecode caches, and intermediate single-case proof output were removed while preserving the packaged executable, installer, and final matrix evidence.
- Pass 74 added the explicit ChaseOS-owned browser page collector for Capture to Markdown. The collector is disabled by default, visible/configurable in Settings, and appears on the Capture page as either `disabled_in_settings` or `available_click_to_capture`. It launches only an isolated ChaseOS-owned browser runtime for a declared `http` or `https` address after Settings enablement plus a direct Capture action, writes controlled HTML/screenshot/audit artifacts, and still uses the existing Preview or Save flow before raw quarantine Markdown is written. Personal active browser tabs, browser profiles, browser sessions, cookies, history, storage, provider calls, external sends, and canonical mutation remain blocked. A Studio-window shortcut row for `run_chaseos_browser_page_collector` is now visible/configurable in Settings and unassigned by default. The rebuilt `dist/studio/ChaseOS-Studio.exe` SHA-256 is `43BDBADB542756F9D954F98B386ACDDD462482A22EEACC4FD8EDBA8DC8B6A138`; retained evidence under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-chaseos-browser-page-collector.*` verifies the packaged source card is present and Settings-gated, the collector shortcut row is visible/configurable, active personal browser capture remains blocked, the screenshot is nonblank, the owned packaged process terminated, and generated duplicate executable/build/test output was removed while preserving the final executable and evidence.
- Pass 75 added the controlled live proof for the explicit ChaseOS-owned browser page collector. The proof starts a loopback-only local page, temporarily enables only the ChaseOS-owned browser page collector, launches the isolated ChaseOS-owned browser runtime, captures controlled HTML/screenshot/audit artifacts, renders a Markdown preview without saving raw quarantine Markdown, restores the previous Settings file, and writes durable JSON/Markdown proof evidence. It verifies no personal active browser tab, profile, session, cookie, history, or storage read occurs.
- Pass 76 added the Capture and Settings open-safety proof. The proof blocks global `subprocess.run` and `subprocess.Popen` during Capture page model load, local image text Settings load, and Settings runtime controls load; rejects PowerShell shell launchers before persistence; proves a saved marker local image text command is not executed on page load; and verifies the Studio executable set is unchanged.
- Pass 77 added packaged passive open-safety proof for the shipped `dist/studio/ChaseOS-Studio.exe`. The proof opens `#/capture-markdown` and `#/settings`, keeps each route open through three owned child-process scans, verifies zero Studio-owned PowerShell, pwsh, command prompt, Bash, Windows Script Host, or Windows Terminal child processes, terminates only the proof-owned packaged process, and preserves the Studio executable. Pass 78 supersedes the native screenshot/window-handle blocker from this pass.
- Pass 78 remediated the packaged Settings passive process-probe leak and the packaged proof native screenshot confirmation gap. `StudioAPI.get_runtime_gateway_controls` now requests the passive runtime gateway controls model, `build_runtime_live_status` can skip Windows Subsystem for Linux process probing during passive Settings loads, and the packaged proof harness now rejects blank internal Qt self-captures before using the external native capture fallback. The rebuilt `dist/studio/ChaseOS-Studio.exe` SHA-256 is `32B8F070A376DE42D0E282B8B4EB1C1F971270026E06C5D2B725006057AF46AF`; final evidence under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-packaged-settings-passive-probe-remediation-final.*` verifies both `#/capture-markdown` and `#/settings` open with nonblank native screenshots, Studio content sentinels, zero Studio-owned shell child processes, no Markdown writes, no approval-artifact writes, and owned-process termination. Generated build/test/cache output and duplicate temporary executables were removed while preserving `dist/studio/ChaseOS-Studio.exe` and `dist/studio/ChaseOS-Installer.exe`.
- Pass 79 added the controlled source-shape matrix proof and wired the retained evidence into the Capture release-readiness model. The proof uses a disposable scratch vault through the Studio application programming interface, covers clean article text, long text, sparse text, table/code text, vault Markdown file input, saved page input, controlled browser artifact input, secret-like save blocking, needs-redaction downstream blocking, and duplicate save blocking, then removes scratch output. Retained evidence under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-source-shape-matrix.*` verifies all 10 cases with no forbidden downstream writes, no personal browser reads, no clipboard reads, no screen capture, no Discord calls, no provider calls, and no selected-vault writes beyond evidence.
- Pass 80 hardened product-facing Capture language across source cards, release-readiness details, recent capture statuses, preview/save/review failure messages, downstream guard cards, and collector/downstream error paths. The frontend now maps raw internal status codes into operator-readable labels while preserving literal code identifiers and approval statements for compatibility. The rebuilt `dist/studio/ChaseOS-Studio.exe` SHA-256 is `C12159EA232A80C555FA6CF2D8FA9833B74E7C9FB252AD44C45CEF4E7755CEE8`; retained evidence under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-product-language-hardening-open-safety.*` verifies `#/capture-markdown` and `#/settings` open with nonblank native screenshots, zero Studio-owned shell child processes, no Markdown writes, no approval-artifact writes, and owned-process termination. Generated build folders, cache folders, and duplicate executable output were removed while preserving `dist/studio/ChaseOS-Studio.exe` and `dist/studio/ChaseOS-Installer.exe`.
- Pass 81 hardened current command-line help for Capture to Markdown and downstream acquisition commands. The pass replaces old internal shorthand in `capture --help`, `capture markdown --help`, and `acquisition --help` with product-facing full terms for Capture to Markdown, Agent Orchestration Runtime, and Source Intelligence Core while preserving literal command names, option names, file paths, schema keys, and approval statements for compatibility. Focused command-line help regression tests passed.
- Pass 82 completes Studio-window shortcut coverage for all explicit Capture to Markdown collectors. Settings now exposes configurable, unassigned-by-default rows for screen capture, clipboard text, browser artifact, ChaseOS-owned browser page, and Discord artifact collectors. The Capture page shortcut runner now routes browser artifact and Discord artifact shortcuts to the same Settings-gated source-card actions, while still requiring the Capture page, collector enablement, operator-selected artifacts, and declared source fields where those collectors require them.
- Studio exposes the Capture Markdown panel plus `Write Pack`, `Agent Orchestration Runtime Readiness`, `Approval Design`, `Write Request`, `Decision Readiness`, `Approve` / `Reject`, `Consumption Preview`, `Consume Decision`, `Agent Bus Task Preview`, `Write Agent Bus Task`, `Task Claim Readiness`, `Claim Task`, `Agent Orchestration Runtime Dry-Run Readiness`, `Run Agent Orchestration Runtime Dry-Run`, `Request Task Review`, `Full Dispatch Readiness`, `Run Full Dispatch`, `Source Intelligence Core Readiness`, `Source Intelligence Core Approval Design`, `Write Source Intelligence Core Approval Request`, `Source Intelligence Core Decision Readiness`, `Approve Source Intelligence Core`, `Reject Source Intelligence Core`, `Consume Source Intelligence Core Decision`, `Source Intelligence Core Ingestion Preview`, `Ingest into Source Intelligence Core`, `Graph Indexing Readiness Preview`, `Write Graph Snapshot`, `Canonical Promotion Readiness`, `Canonical Approval Design`, `Write Canonical Request`, `Canonical Decision Readiness`, `Approve Canonical Promotion`, `Reject Canonical Promotion`, `Consume Canonical Decision`, and `Promote Canonical Knowledge`.
- Studio registry now observes the Pass 44 Source Intelligence Core canonical-promotion executor as exact graph-indexing artifact digest gated, exact approval-request digest gated, exact approval-decision digest gated, exact approval-consumption digest gated, exact canonical-promotion digest gated, exact operator-statement gated, create-only, and available after Pass 43 approval consumption. It can write only the canonical promotion marker, reviewed capture knowledge note, managed Knowledge Index route block, and canonical-promotion execution artifact while keeping graph-store mutation, Source Intelligence Core source-package rewrite, provider calls, external sends, attachment deletion, and Agent Bus task body execution blocked.

## Current Status

PARTIAL / VERIFIED for local reviewed source-pack Agent Bus task writing, read-only task claim readiness, guarded local task claiming, read-only claimed-task Agent Orchestration Runtime dry-run readiness, guarded claimed-task Agent Orchestration Runtime dry-run execution, guarded claimed-task status lifecycle update to `review`, read-only full-dispatch readiness, guarded source-pack Agent Orchestration Runtime full-dispatch execution with source-pack writeback evidence, Source Intelligence Core ingestion readiness, Source Intelligence Core ingestion approval design, create-only Source Intelligence Core ingestion approval request writing, Source Intelligence Core ingestion approval decision/consumption readiness, create-only Source Intelligence Core ingestion approval decision writing, exact-once Source Intelligence Core approval consumption, exact-once Source Intelligence Core ingestion into a reviewed-captures workspace, graph-indexing readiness over completed Source Intelligence Core ingestion evidence, guarded graph snapshot/store writing, canonical-promotion readiness over completed graph-indexing evidence/current graph-store state, canonical-promotion approval design, create-only pending canonical-promotion approval request writing, canonical-promotion approval decision/consumption readiness, create-only canonical-promotion approval decision writing, exact-once canonical-promotion approval consumption, and exact-digest canonical knowledge note/index promotion.

Current core Markdown capture status is COMPLETE / VERIFIED for explicit source text and vault-file input through preview, raw-quarantine save, recent listing, review sidecar/packet update, duplicate handling, and redaction blocking. The product-facing Capture to Markdown path is now release-ready for explicit source text, vault files, screen/image capture, clipboard text, browser artifacts, ChaseOS-owned browser pages, Discord artifacts, local image text extraction, Studio-window collector shortcuts, and governed downstream approval paths. The built-in local image text engine is verified on this host for controlled pixel-text screenshots and common Studio-font screenshot text through the six-case fixture report. Full arbitrary photograph extraction remains an engine-expansion lane only if product scope expands beyond screenshot/text surfaces.

Pass 83 added live Discord command capture through ChaseOS Agent Bus ingress. The collector is disabled by default, visible/configurable in Settings, appears on the Capture page and Capture palette, reads only Discord-origin Agent Bus structured state after Settings enablement plus an explicit Capture action, fills the raw text field, and uses the existing Preview or Save flow before Markdown is written. It does not read Discord tokens, webhooks, raw bindings, or direct Discord events, and it does not call the Discord application programming interface.

Pass 84 added local photo/document text extraction. Capture now has a product-facing `photo_document_text_extraction` source mode for explicit vault-local images/photos, embedded-text PDFs, Word documents, rich text files, text files, and Markdown files. Word documents and PDFs are parsed locally without cloud extraction or provider calls. Image/photo inputs route through the existing local image text engine path, so real-world photograph quality still depends on the configured local engine.

Verified:

- Pass 21 backend and CLI write one local open/unclaimed Agent Bus task only after exact request, decision, consumption, task digest, and operator statement matching.
- The writer creates the exact-once task marker before the local task row and task artifact.
- Pass 22 backend and CLI read the Pass 21 task artifact and local Agent Bus row, verify task digest, open/unclaimed state, route configuration, and runtime liveness posture, then report claimability without claiming the task.
- Pass 23 backend and CLI claim one local Agent Bus task only after the exact task digest, exact task-claim digest, and exact required operator statement match.
- The claim executor writes a create-only claim marker, updates only the local Agent Bus task row to claimed by `OpenClaw`, and writes a create-only claim artifact; it does not execute the task.
- Pass 24 backend and CLI read the Pass 23 claim artifact, claim marker, claimed local Agent Bus row, source evidence, source-pack-builder contracts, and AOR workflow/handler contracts, then produce a future AOR dry-run packet preview without calling AOR.
- Pass 25 backend and CLI run a governed AOR `dry_run=True` only after the exact task digest, exact claim digest, exact dry-run packet digest, exact operator statement, and explicit dry-run marker/run/artifact flags match.
- Pass 25 writes a create-only dry-run marker before the AOR dry run, verifies `dry_run_ok` / `dry_run_exit`, OSRIL session/event output, AOR audit output, no source-pack writeback, and unchanged local Agent Bus task execution state, then writes a create-only dry-run artifact.
- Pass 26 backend and CLI consume the Pass 25 dry-run artifact only after exact task digest, exact claim digest, exact dry-run artifact digest, exact operator statement, and explicit marker/status/artifact flags match.
- Pass 26 writes a create-only status lifecycle marker, updates only the local Agent Bus task row to `review` with a `review_requested` event, and writes a create-only status lifecycle artifact.
- Pass 27 backend and CLI consume the Pass 26 status lifecycle artifact only after exact task digest, exact claim digest, exact AOR dry-run artifact digest, exact status lifecycle artifact digest, local task status `review`, owner `OpenClaw`, and `review_requested` event evidence match.
- Pass 27 returns a future full-dispatch packet preview and digest with `future_full_dispatch_packet_ready=true`, `ready_for_full_dispatch_executor=true`, `aor_full_dispatch_allowed_now=false`, and `aor_full_dispatch_performed=false`; it writes no files and executes no task body.
- Pass 28 backend and CLI consume the Pass 27 readiness result only after exact task digest, exact claim digest, exact AOR dry-run artifact digest, exact status lifecycle artifact digest, exact full-dispatch packet digest, exact required operator statement, local task status `review`, owner `OpenClaw`, `review_requested` event evidence, and explicit marker/run/artifact flags match.
- Pass 28 writes a create-only full-dispatch marker, runs AOR `source_pack_builder` with `dry_run=False`, verifies OSRIL session/event output, AOR audit output, runtime acquisition source-pack writeback, and unchanged Agent Bus task row, then writes a create-only full-dispatch artifact.
- Pass 28 does not execute the Agent Bus task body, update Agent Bus status, start a runtime process/watch loop, ingest Source Intelligence Core, mutate graph/canonical state, call providers, send externally, rewrite/overwrite source packs, or delete attachments.
- Pass 29 backend and command-line interface consume the Pass 28 full-dispatch artifact only after exact full-dispatch artifact digest and optional full-dispatch packet digest checks, verify source-pack writeback evidence, verify Source Intelligence Core contract surfaces, and return a future Source Intelligence Core ingestion packet preview.
- Pass 29 writes no Source Intelligence Core source package, no Source Intelligence Core workspace membership, no graph/canonical state, no provider call, no external send, and no attachment deletion.
- Pass 30 backend and command-line interface consume the Pass 29 readiness result only after exact readiness digest checks, then return a future Source Intelligence Core ingestion approval packet preview.
- Pass 30 writes no approval request, no Source Intelligence Core source package, no Source Intelligence Core workspace membership, no graph/canonical state, no provider call, no external send, and no attachment deletion.
- Pass 31 backend and command-line interface consume the Pass 30 approval design only after exact full-dispatch artifact, optional full-dispatch packet, optional Source Intelligence Core readiness packet, exact Source Intelligence Core approval request digest, and exact operator statement checks.
- Pass 31 writes one pending Source Intelligence Core ingestion approval request artifact under `07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/` only when explicitly requested, and blocks duplicate overwrite.
- Pass 31 writes no approval decision, consumes no approval, writes no exact-once ingestion marker, writes no Source Intelligence Core source package, writes no Source Intelligence Core workspace membership, mutates no graph/canonical state, calls no provider, sends nothing externally, and deletes no attachment.
- Pass 32 backend and command-line interface consume the Pass 31 pending approval request only after exact full-dispatch artifact, optional full-dispatch packet, optional Source Intelligence Core readiness packet, exact Source Intelligence Core approval request digest, and pending approval artifact validation.
- Pass 32 returns future approval decision options and a future approval-consumption contract preview, verifies the request is pending and unconsumed, and writes no decision, no consumption marker, no Source Intelligence Core source package, no Source Intelligence Core workspace membership, no graph/canonical state, no provider call, no external send, and no attachment deletion.
- Pass 33 backend and command-line interface consume the Pass 32 pending approval-decision readiness result only after exact full-dispatch artifact, optional full-dispatch packet, optional Source Intelligence Core readiness packet, exact Source Intelligence Core approval request digest, exact Source Intelligence Core approval decision digest, pending approval artifact validation, exact approve/reject decision value, and exact operator-statement validation.
- Pass 33 writes one create-only Source Intelligence Core ingestion approval decision artifact under `07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/_decisions/` only when explicitly requested, blocks duplicate/conflicting decision artifacts, and writes no consumption marker, no Source Intelligence Core source package, no Source Intelligence Core workspace membership, no graph/canonical state, no provider call, no external send, and no attachment deletion.
- Pass 34 backend and command-line interface consume the Pass 33 approval decision artifact only after exact full-dispatch artifact, optional full-dispatch packet, optional Source Intelligence Core readiness packet, exact Source Intelligence Core approval request digest, exact Source Intelligence Core approval decision digest, exact Source Intelligence Core approval consumption digest, exact approve/reject decision value, and exact operator-statement validation.
- Pass 34 writes one create-only exact-once Source Intelligence Core approval-consumption marker under `07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/_consumption_markers/` before one create-only consumption artifact under `07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/_consumptions/` only when explicitly requested. Approved consumption marks the path ready for the Pass 35 Source Intelligence Core ingestion executor, but writes no Source Intelligence Core source package, no Source Intelligence Core workspace membership, no graph/canonical state, no provider call, no external send, and no attachment deletion.
- Pass 35 backend and command-line interface consume the Pass 34 approved consumption artifact only after exact full-dispatch artifact, optional full-dispatch packet, optional Source Intelligence Core readiness packet, exact Source Intelligence Core approval request digest, exact Source Intelligence Core approval decision digest, exact Source Intelligence Core approval consumption digest, exact Source Intelligence Core ingestion digest, exact approved decision value, and exact operator-statement validation.
- Pass 35 writes one create-only exact-once Source Intelligence Core ingestion marker under `07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/_ingestion_markers/`, creates or updates the reviewed-captures Source Intelligence Core workspace, writes one reviewed Markdown source package, updates workspace membership, and writes one create-only ingestion artifact under `07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/_ingestions/`. It still writes no graph index, no canonical knowledge, calls no provider, sends nothing externally, and deletes no attachment.
- Pass 36 backend and command-line interface consume the Pass 35 Source Intelligence Core ingestion artifact only after exact ingestion artifact digest and exact Source Intelligence Core ingestion digest validation.
- Pass 36 reads the written reviewed-captures workspace and reviewed Markdown source package, builds a candidate graph preview containing source package, workspace, ingestion artifact, capture Markdown, and chunk nodes, and returns a graph preview digest. It writes no graph snapshot, mutates no graph index, promotes no canonical knowledge, calls no provider, sends nothing externally, and deletes no attachment.
- Pass 37 backend and command-line interface consume the Pass 36 graph-readiness result only after exact Source Intelligence Core ingestion artifact digest, exact Source Intelligence Core ingestion digest, exact graph preview digest, exact operator statement, and explicit marker/snapshot/artifact write flags match.
- Pass 37 writes a create-only graph-indexing marker under `07_LOGS/Agent-Activity/_vcmi_sic_graph_indexing/_markers/`, writes a graph snapshot plus graph-store manifest/current pointer under `runtime/graph/store/`, and writes a create-only execution artifact under `07_LOGS/Agent-Activity/_vcmi_sic_graph_indexing/_executions/` when authorized. It does not promote canonical knowledge, call providers, send externally, delete attachments, execute Agent Bus task bodies, or start runtime watch loops.
- Pass 38 backend and command-line interface consume the Pass 37 graph-indexing execution artifact only after exact graph-indexing artifact digest validation and current graph-store pointer/snapshot validation.
- Pass 38 builds a future canonical-promotion candidate preview and target plan for a reviewed-capture knowledge note plus knowledge index entry while keeping `canonical_mutation_performed=false`, `canonical_knowledge_promotion_performed=false`, provider calls, external sends, and attachment deletion blocked.
- Pass 39 backend and command-line interface consume the Pass 38 canonical-promotion readiness result only after exact graph-indexing artifact digest validation and optional exact canonical-promotion candidate digest validation.
- Pass 39 builds a deterministic future canonical-promotion approval packet preview and approval request digest while keeping `approval_request_written=false`, `canonical_promotion_allowed_now=false`, `canonical_knowledge_note_written=false`, `canonical_knowledge_index_written=false`, provider calls, external sends, and attachment deletion blocked.
- Pass 40 backend and command-line interface consume the Pass 39 canonical-promotion approval design only after exact graph-indexing artifact digest validation, optional graph snapshot digest validation, optional canonical-promotion candidate digest validation, exact canonical-promotion approval request digest validation, and exact operator-statement validation.
- Pass 40 writes one create-only pending canonical-promotion approval request artifact under `07_LOGS/Agent-Activity/_vcmi_canonical_promotion_approvals/` only when explicitly requested, blocks duplicate overwrite, and writes no approval decision, consumes no approval, writes no exact-once canonical-promotion marker, writes no canonical knowledge note/index, calls no provider, sends nothing externally, and deletes no attachment.
- Pass 41 backend and command-line interface consume the Pass 40 pending canonical-promotion approval request only after exact graph-indexing artifact digest validation, exact canonical-promotion approval request digest validation, pending request validation, and no prior decision/consumption/canonical write evidence.
- Pass 41 returns future approval decision options and a future approval-consumption contract preview, verifies the request is pending and unconsumed, and writes no decision, consumes no approval, writes no exact-once canonical-promotion marker, writes no canonical knowledge note/index, calls no provider, sends nothing externally, and deletes no attachment.
- Pass 42 backend and command-line interface consume the Pass 41 canonical-promotion approval decision readiness result only after exact graph-indexing artifact digest validation, optional graph snapshot digest validation, optional canonical-promotion candidate digest validation, exact canonical-promotion approval request digest validation, exact canonical-promotion approval decision digest validation, exact approve/reject decision value validation, pending request validation, and exact operator-statement validation.
- Pass 42 writes one create-only canonical-promotion approval decision artifact under `07_LOGS/Agent-Activity/_vcmi_canonical_promotion_approvals/_decisions/` only when explicitly requested, blocks duplicate/conflicting decision artifacts, and writes no approval-consumption marker, consumes no approval, writes no exact-once canonical-promotion marker, writes no canonical knowledge note/index, calls no provider, sends nothing externally, and deletes no attachment.
- Pass 43 backend and command-line interface consume the Pass 42 canonical-promotion approval decision artifact only after exact graph-indexing artifact digest validation, optional graph snapshot digest validation, optional canonical-promotion candidate digest validation, exact approval-request digest validation, exact approval-decision digest validation, exact approval-consumption digest validation, exact approve/reject decision value validation, pending request validation, and exact operator-statement validation.
- Pass 43 writes one create-only canonical-promotion approval-consumption marker under `07_LOGS/Agent-Activity/_vcmi_canonical_promotion_approvals/_consumption_markers/` before one create-only consumption artifact under `07_LOGS/Agent-Activity/_vcmi_canonical_promotion_approvals/_consumptions/` only when explicitly requested, blocks duplicate marker/artifact writes, marks approved decisions ready for a future canonical-promotion executor, and still writes no canonical knowledge note/index, calls no provider, sends nothing externally, and deletes no attachment.
- Pass 44 backend and command-line interface consume the Pass 43 approved canonical-promotion approval-consumption artifact only after exact graph-indexing artifact digest validation, optional graph snapshot digest validation, canonical-promotion candidate digest validation, exact approval-request digest validation, exact approval-decision digest validation, exact approval-consumption digest validation, exact canonical-promotion digest validation, and exact operator-statement validation.
- Pass 44 writes one create-only canonical-promotion marker under `07_LOGS/Agent-Activity/_vcmi_canonical_promotion/_markers/`, one reviewed capture note under `02_KNOWLEDGE/Source-Intelligence/Reviewed-Captures/`, one managed route block in `02_KNOWLEDGE/Knowledge-Index.md`, and one create-only execution artifact under `07_LOGS/Agent-Activity/_vcmi_canonical_promotion/_executions/` only when all four write flags are explicitly supplied. It blocks duplicate marker/artifact/note/index writes and still does not mutate the graph store, rewrite Source Intelligence Core source packages, call providers, send externally, or delete attachments.
- Studio Capture Markdown user interface exposes `Agent Bus Task Preview`, `Write Agent Bus Task`, `Task Claim Readiness`, `Claim Task`, `Agent Orchestration Runtime Dry-Run Readiness`, `Run Agent Orchestration Runtime Dry-Run`, `Request Task Review`, `Full Dispatch Readiness`, `Run Full Dispatch`, `Source Intelligence Core Readiness`, `Source Intelligence Core Approval Design`, `Write Source Intelligence Core Approval Request`, `Source Intelligence Core Decision Readiness`, `Approve Source Intelligence Core`, `Reject Source Intelligence Core`, `Consume Source Intelligence Core Decision`, `Source Intelligence Core Ingestion Preview`, `Ingest into Source Intelligence Core`, `Graph Indexing Readiness Preview`, `Write Graph Snapshot`, `Canonical Promotion Readiness`, `Canonical Approval Design`, `Write Canonical Request`, `Canonical Decision Readiness`, `Approve Canonical Promotion`, `Reject Canonical Promotion`, `Consume Canonical Decision`, and `Promote Canonical Knowledge` after the governed prerequisites.
- Fresh Pass 44 rendered visual quality assurance confirms the Source Intelligence Core readiness result, approval design result, pending approval request writer result, decision-readiness result, approval decision writer result, approval consumption preview, approval consumption executor result, Source Intelligence Core ingestion preview, final Source Intelligence Core ingestion executor result, graph-indexing readiness result, graph-indexing executor preview, graph snapshot execution result, canonical-promotion readiness result, canonical-promotion approval-design result, canonical-promotion approval-request writer result, canonical-promotion approval decision readiness result, canonical-promotion approval decision writer result, canonical-promotion approval consumption executor result, and final canonical-promotion executor result are available and contract-verified in disposable desktop/mobile Studio fixtures.
- Real-repository Source Intelligence Core ingestion is now verified for the Markdown Guide capture. Evidence: `07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/_ingestions/vcmi-sic-ingestion-appr-310dd4bc2b1e09e3.json`, workspace `runtime/source_intelligence/workspaces/vcmi-reviewed-captures/workspace.json`, and source package `runtime/source_intelligence/workspaces/vcmi-reviewed-captures/source_packages/20260526-155104-source-visual-captur_35e125d65080.json`.
- Real-repository graph indexing is now verified for the same capture. Evidence: `07_LOGS/Agent-Activity/_vcmi_sic_graph_indexing/_executions/graph-indexing-ba2db78ce1f20d98.json`, graph snapshot `runtime/graph/store/snapshots/vcmi-ba2db78ce1f20d98.json`, graph manifest, and graph current pointer.
- Real-repository canonical promotion is now verified for the same capture. Evidence: `07_LOGS/Agent-Activity/_vcmi_canonical_promotion/_executions/vcmi-canonical-promotion-appr-6132539a312962ec.json`, reviewed capture note `02_KNOWLEDGE/Source-Intelligence/Reviewed-Captures/6385475b-681a-4c51-99e7-3ec6db413359.md`, and route block in `02_KNOWLEDGE/Knowledge-Index.md`.
- A real public web HTML capture from `https://www.markdownguide.org/basic-syntax/` was saved into raw quarantine as `03_INPUTS/00_QUARANTINE/Sources/20260526-155104__source__visual-capture__markdown-guide-basic-syntax-web-capture-pass.md`; it preserved the source URL, extracted 28,286 source characters, included `# Basic Syntax`, and was promoted after review through the guarded downstream chain. Pass 47 corrected the earlier blocker framing: Python UTF-8 reads show the Markdown Guide source package and canonical note contain valid Unicode on disk, while PowerShell console output made some characters look corrupted. The new source text quality guard still matters because future captures can contain real mojibake, and those repairs now get digest-backed metadata.
- Pass 48 real-chain source text quality replay is now verified for a fresh `https://example.com/` capture. Evidence: capture Markdown `03_INPUTS/00_QUARANTINE/Sources/20260527-074357__source__visual-capture__capture-to-markdown-real-web-replay-example-d.md`, Source Intelligence Core ingestion artifact `07_LOGS/Agent-Activity/_vcmi_sic_ingestion_approvals/_ingestions/vcmi-sic-ingestion-appr-e7da1654ba52f093.json`, source package `runtime/source_intelligence/workspaces/vcmi-reviewed-captures/source_packages/20260527-074357-source-visual-captur_f1b45d444746.json`, graph snapshot `runtime/graph/store/snapshots/vcmi-e050f84b92e66aa1.json`, canonical note `02_KNOWLEDGE/Source-Intelligence/Reviewed-Captures/27528067-bdfd-4a3f-8139-c41d29dcc81c.md`, canonical promotion artifact `07_LOGS/Agent-Activity/_vcmi_canonical_promotion/_executions/vcmi-canonical-promotion-appr-e44f5d78f6f632bf.json`, and proof report `07_LOGS/Agent-Activity/2026-05-27-codex-markdown-capture-real-chain-20260527T074357Z.md`.

Current release boundaries:

1. Local image text extraction is VERIFIED for no-text, dense-text, low-contrast, table, mixed-language, controlled pixel-text, and common Studio-font screenshot fixture images through the built-in engine on this host. Local document extraction is VERIFIED for Word document XML and embedded-text PDF sources. Real-world photograph extraction uses the local image text engine path and can be strengthened further by installing or configuring a stronger local engine.
2. The product-facing release path uses explicit source text, vault files, screen/image capture, photo/document text extraction, clipboard text, browser artifact import, active ChaseOS browser state/artifact capture, ChaseOS-owned browser page capture, Discord artifact import, live Discord command capture through Agent Bus ingress, local image text extraction, Studio-window collector shortcuts, and governed downstream approval paths. Personal browser profile/session/cookie/history reads and live Discord token/webhook/listener/direct-call capture are not required for this release path because visible content flows through ChaseOS-owned browser state/artifacts, screen/image capture plus local image extraction, operator-selected artifacts, local document parsing, or ChaseOS-owned Agent Bus state.
3. Studio-window Capture shortcuts are configurable in Settings and run only inside the Studio window when Capture is open. They do not register operating-system-wide hooks, inspect other applications, or bypass collector Settings toggles.
4. Product language is current on the Capture page and current command-line help. Historical archived docs can still receive wording-only sweeps without changing literal commands, file paths, schema keys, or approval statements.
5. Packaged route rendering, manual-text save, Settings shortcut visibility, visible review-state update, image-to-Markdown save, image-to-Markdown failure states, release-readiness posture, source-package result cards, downstream success result cards, source-package guard-failure result cards, downstream failure-state guard cards, compact/wide desktop window sizes, and cleaned open-safety are verified.
6. Pass 79 verifies the controlled source-shape matrix for text, long text, sparse text, table/code text, vault Markdown files, saved pages, controlled browser artifacts, redaction handling, downstream gating, and duplicate save handling. Broader optional live-source proof can still add more websites, malformed pages, image attachment variants, private-source denial cases, and packaged-shell operator review.

## Pass Reconciliation

- Passes 1-4: core contract, quarantine writer, Studio panel, CLI/operator docs.
- Pass 5: Acquisition/AOR review bridge preview only.
- Pass 6: controlled browser/webview extraction.
- Passes 7/7b/7c: screenshot/optical-character-recognition fallback design, attachment quarantine-copy policy, retention/review policy.
- Pass 8: hotkey overlay and external surfaces deferred.
- Pass 9: operator review state machine.
- Pass 10: packaged Studio clickthrough and review user interface.
- Pass 11: packaged Studio visual quality assurance and attachment disposition policy.
- Pass 12: reviewed-capture downstream gate readiness.
- Pass 13: reviewed source-pack write approval preview user interface.
- Pass 14: approved source-pack write executor.
- Pass 15: read-only source-pack AOR dispatch readiness.
- Pass 16: read-only source-pack AOR dispatch approval design.
- Pass 17: exact digest/statement-gated pending approval request writer.
- Pass 18: read-only pending approval decision/consumption readiness.
- Pass 19: exact digest/statement-gated create-only approval decision writer.
- Pass 20: exact digest/statement-gated approval consumption executor with marker-before-artifact ordering.
- Pass 21: exact digest/statement-gated Agent Bus task writer with marker-before-open-task/artifact ordering and no task claim.
- Pass 22: read-only Agent Bus task claim-readiness validator with task artifact/local row binding, route/liveness checks, and no task claim.
- Pass 23: exact digest/statement-gated Agent Bus task claim executor with marker-before-claim/artifact ordering and no task execution.
- Pass 24: read-only claimed-task AOR dry-run readiness validator with claim artifact/claimed row binding, source-pack-builder/AOR contract checks, future dry-run packet preview, and no AOR dry-run call.
- Pass 25: exact digest/statement-gated claimed-task AOR dry-run executor with marker-before-AOR-dry-run ordering, OSRIL/AOR audit/dry-run artifact verification, no source-pack writeback, and no Agent Bus task execution or full dispatch.
- Pass 26: exact digest/statement-gated claimed-task status lifecycle with marker-before-status-update ordering, local Agent Bus task status update to `review`, `review_requested` event evidence, status lifecycle artifact evidence, no task body execution, and no full dispatch.
- Pass 27: read-only full-dispatch readiness validator with task/claim/AOR-dry-run/status-lifecycle artifact digest checks, reviewed local task row/event checks, future full-dispatch packet preview/digest, no task body execution, no runtime process start, and no full dispatch.
- Pass 28: exact digest/statement-gated full-dispatch executor with marker-before-Agent-Orchestration-Runtime-full-dispatch ordering, OSRIL/Agent-Orchestration-Runtime audit/source-pack-writeback evidence, unchanged Agent Bus task row verification, no task body execution, no status update, no runtime process start/watch loop, no Source Intelligence Core ingestion, and no graph/canonical/provider/external/attachment deletion.
- Pass 29: read-only Source Intelligence Core ingestion readiness with Pass 28 full-dispatch artifact/digest binding, source-pack writeback verification, Source Intelligence Core contract checks, future Source Intelligence Core ingestion packet preview, and no Source Intelligence Core write, graph/canonical mutation, provider call, external send, or attachment deletion.
- Pass 30: read-only Source Intelligence Core ingestion approval design with Pass 29 readiness digest binding, future approval packet preview, and no approval request write, Source Intelligence Core write, graph/canonical mutation, provider call, external send, or attachment deletion.
- Pass 31: exact digest/statement-gated Source Intelligence Core ingestion approval request writer with create-only pending approval request artifact writing, duplicate-overwrite blocking, no approval decision/consumption, no Source Intelligence Core write, no graph/canonical mutation, no provider call, no external send, and no attachment deletion.
- Pass 32: read-only Source Intelligence Core ingestion approval decision/consumption readiness with Pass 31 pending approval request validation, decision option preview, consumption contract preview, no approval decision write, no approval consumption, no Source Intelligence Core write, no graph/canonical mutation, no provider call, no external send, and no attachment deletion.
- Pass 33: exact digest/statement-gated Source Intelligence Core ingestion approval decision writer with Pass 32 readiness validation, create-only approval decision artifact writing, duplicate/conflicting decision blocking, no approval consumption, no Source Intelligence Core write, no graph/canonical mutation, no provider call, no external send, and no attachment deletion.
- Pass 34: exact digest/statement-gated Source Intelligence Core approval consumption executor with Pass 33 decision validation, marker-before-artifact ordering, create-only consumption artifact writing, duplicate marker/artifact blocking, no Source Intelligence Core write, no graph/canonical mutation, no provider call, no external send, and no attachment deletion.
- Pass 35: exact digest/statement-gated Source Intelligence Core ingestion executor with Pass 34 approved consumption validation, marker-before-ingestion ordering, reviewed-captures workspace creation/update, reviewed Markdown source-package writing, workspace membership update, create-only ingestion artifact writing, duplicate marker/artifact/output blocking, no graph/canonical mutation, no provider call, no external send, and no attachment deletion.
- Pass 36: read-only Source Intelligence Core graph-indexing readiness with Pass 35 ingestion artifact validation, exact artifact digest matching, exact Source Intelligence Core ingestion digest matching, workspace/source-package state checks, graph candidate node and edge preview, graph preview digest, no graph snapshot write, no graph index mutation, no canonical mutation, no provider call, no external send, and no attachment deletion.
- Pass 37: exact digest/statement-gated Source Intelligence Core graph-indexing executor with Pass 36 graph-readiness validation, exact artifact digest matching, exact Source Intelligence Core ingestion digest matching, exact graph preview digest matching, exact operator statement, create-only graph-indexing marker, graph snapshot plus graph-store manifest/current pointer writes, create-only execution artifact, no canonical mutation, no provider call, no external send, and no attachment deletion.
- Pass 38: read-only Source Intelligence Core canonical-promotion readiness with Pass 37 graph-indexing execution artifact validation, exact graph-indexing artifact digest matching, current graph-store pointer/snapshot/manifest validation, future canonical-promotion candidate preview and target plan, no canonical mutation, no canonical knowledge promotion, no provider call, no external send, and no attachment deletion.
- Pass 39: read-only Source Intelligence Core canonical-promotion approval design with Pass 38 readiness validation, exact graph-indexing artifact digest matching, optional exact canonical-promotion candidate digest matching, future canonical-promotion approval packet preview, no approval request write, no approval decision/consumption, no canonical mutation, no canonical knowledge promotion, no provider call, no external send, and no attachment deletion.
- Pass 40: exact digest/statement-gated Source Intelligence Core canonical-promotion approval request writer with Pass 39 approval-design validation, create-only pending approval request artifact writing, duplicate-overwrite blocking, no approval decision/consumption, no canonical mutation, no canonical knowledge promotion, no provider call, no external send, and no attachment deletion.
- Pass 41: read-only Source Intelligence Core canonical-promotion approval decision/consumption readiness with Pass 40 pending request validation, decision option preview, consumption contract preview, no approval decision write, no approval consumption, no canonical mutation, no canonical knowledge promotion, no provider call, no external send, and no attachment deletion.
- Pass 42: exact digest/statement-gated Source Intelligence Core canonical-promotion approval decision writer with Pass 41 readiness validation, create-only approval decision artifact writing, duplicate/conflicting decision blocking, no approval consumption, no canonical mutation, no canonical knowledge promotion, no provider call, no external send, and no attachment deletion.
- Pass 43: exact digest/statement-gated Source Intelligence Core canonical-promotion approval consumption executor with Pass 42 decision validation, marker-before-artifact ordering, create-only consumption artifact writing, duplicate marker/artifact blocking, no canonical mutation, no canonical knowledge promotion, no provider call, no external send, and no attachment deletion.
- Pass 44: exact digest/statement-gated Source Intelligence Core canonical-promotion executor with Pass 43 approved consumption validation, create-only marker writing, reviewed capture knowledge note writing, managed Knowledge Index route-block writing, create-only execution artifact writing, duplicate write blocking, no graph-store mutation, no Source Intelligence Core source-package rewrite, no provider call, no external send, and no attachment deletion.
- Pass 47: source text quality guard with common mojibake repair, Source Intelligence Core source-package metadata propagation, ingestion artifact metadata propagation, canonical note repaired display text, original source digest preservation, display digest recording, and focused tests.
- Pass 48: fresh real public web replay from controlled saved web artifact through Capture to Markdown, review, source package write, Agent Orchestration Runtime dispatch, Source Intelligence Core ingestion, graph indexing, canonical promotion, generated Markdown screenshot proof, and fresh Studio panel visual quality assurance proof.
- Pass 49: normal source restoration for `runtime/studio/capture_to_markdown_panel.py`, preserving Pass 26 through Pass 44 wrappers; focused shell tests, Source Intelligence Core ingestion/canonical-promotion tests, rendered Studio visual quality assurance, output Markdown screenshot proof, and packaged Capture route launch evidence completed. Packaged route screenshot content still needed repair after this pass.
- Pass 50: packaged Capture route screenshot timing repair, rebuilt packaged executable proof, visible Capture copy cleanup for shortcut-heavy status chips, and final packaged route evidence completed. Remaining packaged work is full action clickthrough inside the packaged executable, not route rendering.
- Pass 51: core Markdown capture scope correction and proof; source text or vault file to Markdown preview, raw-quarantine save, recent listing, review sidecar/packet update, duplicate handling, redaction blocking, and product-facing Capture copy verified as the core feature.
- Pass 52: product-facing extras wiring without authority expansion; Capture page source-option cards added, Settings-page Studio-window Capture shortcuts added, duplicate shortcut and unsupported operating-system-wide capture shortcut assignments rejected, and personal-browser/live-Discord sources kept behind explicit artifact, screen/image, or ChaseOS-owned browser flows.
- Pass 55: packaged Capture action clickthrough proof completed against rebuilt `dist/studio/ChaseOS-Studio.exe`. The proof drives the packaged Capture page through source-card selection, Settings Capture shortcut rows, shortcut chord capture, preview, raw-quarantine save, recent capture readback, native screenshot capture, nonblank/content-area verification, owned-process termination, and no approval-artifact writes.
- Pass 56: packaged Capture save-and-review clickthrough proof completed against rebuilt `dist/studio/ChaseOS-Studio.exe` SHA-256 `466CAB5F6A05D8F2C05CACBA2F7DFDB38B19FB7B81CBED6B0DAB`. The proof drives the visible Review controls, applies Reviewed, verifies the sidecar and visual-capture packet status, verifies the Markdown body hash still matches sidecar content hash, verifies no approval-artifact writes, and captures screenshot evidence after the full-language Capture copy pass. Remaining packaged work is broader action matrix coverage for source-pack/downstream result cards and failure states; compact/wide desktop window-size proof was closed later by Pass 71.
- Pass 57: local optical character recognition adapter completed for explicit vault-local screenshot images. The pass adds `runtime/capture/visual_capture/ocr.py`, screenshot text extraction packet building, command-line `--from-screenshot-text`, Studio `screenshot_text_extraction` source mode, frontend local-command field, metadata/review-policy persistence, and focused tests. Verified with a fake local command because this host has no Tesseract or equivalent local engine installed; real engine quality remains open.
- Pass 58: Settings-page local image text extraction command configuration completed. The pass adds `runtime/studio/capture_ocr_settings.py`, exposes the settings model through the Settings runtime controls panel and Studio application programming interface, renders the Settings section in the frontend, pre-fills the Capture local command field from saved Settings, and verifies command persistence, timeout normalization, secret-like command rejection, shell-launcher rejection, and saved-command Capture preview execution. Real engine quality remained open, and Pass 59 later closed packaged image-to-Markdown clickthrough.
- Pass 59: packaged executable image-to-Markdown clickthrough completed. The pass adds `runtime/studio/capture_markdown_packaged_image_text_clickthrough.py`, extends `runtime/studio/packaged_app_visual_qa.py` with the image-text route, verifies Settings saved-command readback, Capture image-text source-card selection, preview, save, visible Reviewed decision, sidecar and visual-capture packet update, no approval-artifact writes, nonblank screenshot proof, temporary Settings restoration, and owned-process termination. Real local engine quality remains open; Pass 60 later closed packaged image-to-Markdown failure-state proof.
- Pass 60: packaged executable image-to-Markdown failure-state proof completed. The pass adds `runtime/studio/capture_markdown_packaged_image_text_failure_clickthrough.py`, extends `runtime/studio/packaged_app_visual_qa.py` with the failure route, makes preview failures visible in the Capture action message, verifies missing engine, no extracted text, command failure, timeout, and sensitive extracted text paths, verifies Save stays disabled, verifies no raw quarantine Markdown or approval artifacts are written, hardens Studio diagnostic PowerShell probes to run without visible windows, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `B11267C9DCBA4A1BD2A493AB50B6928C5CDD13DFB0CC7FF6459A2EE8595F1135`, and preserves real local engine quality as open.
- Pass 62: real local image text quality fixture harness completed as a product-facing blocked proof lane. The pass adds `runtime/studio/capture_ocr_quality_fixtures.py`, exposes latest fixture status through Settings and Capture release readiness, adds frontend readback for the explicit fixture command, verifies fake-engine fixture success in tests, writes a live blocked report on this host because no local engine is configured, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `00B422F31DBF01423C34EE043E26A3BA6DE5A05C98A019DAF4033D82B4026AF6`, and reruns packaged Capture clickthrough with `ok=true` after stale proof runners were cleared.
- Pass 63: packaged downstream source-package release hardening completed. The pass extends `runtime/studio/packaged_app_visual_qa.py` and `runtime/studio/capture_markdown_packaged_action_clickthrough.py` to prove source-package approval preview, approved source-package write, downstream boundary wording, and Agent Orchestration Runtime readiness inside the packaged executable. It adds the visible downstream boundary strip to the Capture result card, verifies source-package artifacts are create-only additions, verifies no approval artifacts are written, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `DF19FB382E4FD0A52B5F5D740748D0F77121B47BCEF343A444BF74639BD51E05`, and cleans failed proof/build duplicates while preserving the installer and final executable.
- Pass 64: packaged full downstream-chain proof completed. The pass fixes packaged Agent Orchestration Runtime task-type lookup to use the operator vault task table, expands packaged proof assessment to preserve partial evidence and count Capture downstream approval artifacts, verifies Agent Orchestration Runtime dry run/full dispatch, Source Intelligence Core ingestion, graph indexing, and canonical promotion from the packaged Capture page, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `A2C14DFBBDA84E2F6D2440F3B5571415D87BB20B43A4C8CF56BBEB43C485778F`, and cleans failed proof/build duplicates while preserving the installer, passing executable, and passing proof evidence.
- Pass 66: explicit Studio screen capture collector completed as Settings-gated and click-only. The pass adds `runtime/studio/capture_collector_settings.py`, exposes collector state through Settings and the Capture page, adds the Studio application programming interface methods, renders the Settings toggle and Capture source-card action, verifies disabled-by-default behavior, verifies no writes when disabled or missing operator confirmation, verifies screenshot evidence and audit writes with a fake image provider, verifies normal Preview/Save still creates Markdown through the existing quarantine flow, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `9E6F874E5E49AD35328C7D1C1364968365017E40B3441CDFE5AF4917F3103F09`, and cleans generated fake proof artifacts while retaining packaged proof evidence.
- Pass 67: explicit Studio clipboard text collector completed as Settings-gated and click-only. The pass extends `runtime/studio/capture_collector_settings.py`, exposes collector state through Settings and the Capture page, adds `capture_clipboard_text_for_markdown`, renders the Settings toggle and Capture source-card action, verifies disabled-by-default behavior, verifies no writes when disabled or missing operator confirmation, verifies empty clipboard text is blocked, verifies current clipboard text fills the Capture raw text field without writing Markdown, verifies normal Preview/Save still creates Markdown through the existing quarantine flow, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `558B3AE019E290A06DF3FF633C2AA156FCDA816B6DBFD0A695E3CDB360BFCDD3`, and cleans generated fake proof artifacts while retaining packaged proof evidence.
- Pass 68: Studio-window collector shortcuts completed. The pass adds configurable Settings rows for `run_screen_capture_collector` and `run_clipboard_text_collector`, wires the frontend shortcut runner to the explicit collector actions when Capture is open, keeps operating-system global shortcut rows disabled, verifies focused and broader Capture tests, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `43BA620A07946110D6C6848B8AFB5E33732A641323AD78904B7BCE22EB20B558`, and proves the packaged Settings shortcut rows through a source-package guard-failure clickthrough while removing the fake raw capture generated by that proof.
- Pass 69: explicit browser artifact collector completed as Settings-gated and click-only. The pass extends `runtime/studio/capture_collector_settings.py`, exposes collector state through Settings and the Capture page, adds `capture_browser_artifact_for_markdown`, renders the Settings toggle and Capture source-card action, verifies disabled-by-default behavior, verifies required operator confirmation, explicit artifact path, and declared source address, verifies no raw quarantine Markdown write on click, verifies normal Preview/Save still creates Markdown through the existing quarantine flow, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `6675AF98734854979929E74945641D317D237180DE9A4CBD35EAE4046CF0B778`, proves the packaged source card is visible and Settings-gated, and cleans generated fake proof artifacts while retaining packaged proof evidence.
- Pass 70: explicit Discord artifact collector completed as Settings-gated and click-only. The pass extends `runtime/studio/capture_collector_settings.py`, exposes collector state through Settings and the Capture page, adds `capture_discord_artifact_for_markdown`, renders the Settings toggle and Capture source-card action, verifies disabled-by-default behavior, verifies required operator confirmation, explicit artifact path, and declared Discord source, verifies no raw quarantine Markdown write on click, verifies normal Preview/Save still creates Markdown through the existing quarantine flow, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `80683EDDECB08975DB7FB8D9CFA80F154A09DE42E811BFF04CBD774DCEEF2C1B`, proves the packaged source card is visible and Settings-gated, and cleans generated fake proof artifacts while retaining packaged proof evidence.
- Pass 71: packaged desktop window-size matrix proof completed. The pass adds proof-only packaged Studio window-size environment controls, extends the Capture packaged clickthrough runner with repeated `--window-size` cases, exposes latest window-size proof status in the Capture release-readiness surface, verifies compact and wide packaged Capture runs, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `8E746A0C89AC2C5835A9BBC6BBB2677657A90AA4B3B4EC8BAB5D10EBB38522D1`, and removes generated fake proof captures while retaining matrix evidence.
- Pass 72: packaged downstream failure-state matrix proof was PARTIAL. The pass added product-facing blocked cards for Source Intelligence Core approval request failure and canonical promotion approval request failure states, exposed proof-only Capture handlers for deep packaged proof invocation, extended packaged proof tooling with a downstream failure-state matrix, and wired the latest retained matrix result into Capture release readiness. The canonical promotion approval request failure case remained blocked at Source Intelligence Core ingestion result-card output.
- Pass 73: packaged downstream failure-state matrix proof is VERIFIED. The pass adds durable Source Intelligence Core ingestion blocked cards and diagnostics, accepts existing UTF-8 byte-order-mark Source Intelligence Core workspace files, adds single-case downstream failure command-line proof execution, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `013872F4B6297192D067F229E92F042E1724D06BAEE56420CBE72871F44283C6`, and verifies all three packaged failure cases with `ok=true`: Agent Orchestration Runtime approval request bad statement, Source Intelligence Core approval request bad statement, and canonical promotion approval request bad statement.
- Pass 74: explicit ChaseOS-owned browser page collector completed as Settings-gated and click-only. The pass extends `runtime/studio/capture_collector_settings.py`, exposes collector state through Settings and the Capture page, adds `capture_chaseos_browser_page_for_markdown`, renders the Settings toggle and Capture source-card action, adds the configurable Studio-window shortcut row, verifies disabled-by-default behavior, required operator confirmation, declared `http`/`https` address validation, controlled artifact writes, no raw quarantine Markdown write on click, no personal browser tab/profile/session/cookie/history reads, and normal Preview/Save through the existing quarantine flow, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `43BDBADB542756F9D954F98B386ACDDD462482A22EEACC4FD8EDBA8DC8B6A138`, proves the packaged source card and shortcut row are visible and Settings-gated/configurable, and cleans generated duplicate executable/build/test output while retaining packaged proof evidence.
- Pass 75: controlled live ChaseOS-owned browser page proof completed. The pass adds `runtime/studio/capture_markdown_chaseos_browser_page_live_proof.py`, verifies it with focused tests, launches a real isolated ChaseOS-owned browser against a loopback-only controlled page, captures HTML/screenshot/audit artifacts under `07_LOGS/Browser-Runs/Capture-to-Markdown/`, renders a Markdown preview containing the sentinel text, writes durable proof evidence under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-chaseos-browser-page-live-proof.*`, restores the previous Settings file, and leaves raw-quarantine Markdown unsaved by default.
- Pass 76: Capture and Settings open-safety proof completed. The pass adds `runtime/studio/capture_markdown_open_safety_proof.py`, verifies it with focused tests, disables startup-surface process probing for passive Settings page models, proves Capture page load and Settings page load do not start subprocesses, proves the saved local image text command is not executed on load, rejects PowerShell shell launchers before persistence, removes proof scratch output, and confirms only `dist/studio/ChaseOS-Studio.exe` is present.
- Pass 77: packaged passive open-safety proof completed. The pass adds `runtime/studio/capture_markdown_packaged_open_safety.py`, extends `runtime/studio/packaged_app_visual_qa.py` with owned child-process scanning for passive packaged route opens, verifies both `#/capture-markdown` and `#/settings` against `dist/studio/ChaseOS-Studio.exe`, records zero forbidden Studio-owned shell child processes across three scans per route, separates native screenshot/window-handle confirmation from the PowerShell-spam safety result, and preserves `dist/studio/ChaseOS-Studio.exe` SHA-256 `8227F5DD8FC6C9EA2D456B8B613FDDB802C04A0CD2394E818666E0172DB12591`.
- Pass 78: packaged Settings passive-probe remediation completed. The pass changes the Settings runtime gateway application programming interface to use `probe_processes=False`, adds passive Windows Subsystem for Linux process-probe suppression to runtime live status, adds regression tests for the passive Settings path, makes the packaged proof harness reject blank internal self-captures before falling back to external native capture, rebuilds `dist/studio/ChaseOS-Studio.exe`, verifies both `#/capture-markdown` and `#/settings` with nonblank native screenshots and zero Studio-owned shell child processes, and preserves `dist/studio/ChaseOS-Studio.exe` SHA-256 `32B8F070A376DE42D0E282B8B4EB1C1F971270026E06C5D2B725006057AF46AF`.
- Pass 79: controlled source-shape matrix completed. The pass adds `runtime/studio/capture_markdown_source_shape_matrix_proof.py`, verifies the proof through the Studio application programming interface, exposes latest retained source-shape evidence in the Capture release-readiness surface, passes 10 controlled cases, writes evidence under `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-source-shape-matrix.*`, removes scratch output, and keeps real local image text engine quality as the remaining open release-proof item on this host.
- Pass 80: product-language hardening completed. The pass extends `runtime/studio/shell/frontend/app.js` so Capture source cards, release-readiness rows, recent capture review states, preview blockers, review messages, source-package blockers, guard cards, and downstream error paths render product-facing labels instead of raw internal status codes. It adds a static frontend regression test, rebuilds `dist/studio/ChaseOS-Studio.exe` SHA-256 `C12159EA232A80C555FA6CF2D8FA9833B74E7C9FB252AD44C45CEF4E7755CEE8`, reruns focused Capture regressions with `67 passed`, and verifies packaged Capture plus Settings passive open-safety with zero Studio-owned shell child processes.
- Pass 81: command-line help product-language hardening completed. The pass updates `runtime/cli/main.py` help text and print labels for current Capture to Markdown command surfaces, adds a focused regression test in `runtime/capture/test_visual_capture_cli.py`, and verifies `capture --help`, `capture markdown --help`, and `acquisition --help` expose product-facing full terms instead of old internal shorthand.
- Pass 82: full Studio-window collector shortcut coverage completed. The pass adds configurable Settings rows for `run_browser_artifact_collector` and `run_discord_artifact_collector`, keeps all collector rows unassigned by default, routes those shortcuts through the existing guarded Capture page collector actions, updates the packaged proof script to require all five explicit collector shortcut rows, and verifies the shortcut model, Settings panel, Capture page JavaScript routing, and packaged static proof.
- Pass 83: controlled image to Markdown live proof completed. The pass adds `runtime/studio/capture_markdown_image_to_markdown_live_proof.py`, uses the real screen collector with a controlled high-contrast image provider, extracts the image text through the existing local command path, previews and saves Markdown through the normal Capture to Markdown quarantine writer, writes captured image/audit/proof evidence, and exposes the latest proof in Capture release readiness as `live_image_to_markdown_save`. The live vault proof saved `03_INPUTS/00_QUARANTINE/Sources/20260528-134041__source__visual-capture__image-to-markdown-live-proof.md`, containing `CHASEOS CAPTURE PROOF`, `IMAGE TO MARKDOWN`, and `TEXT 2026 05 28`.
- Pass 84: built-in local image text engine completed for controlled ChaseOS pixel-text images. The pass adds `runtime/capture/visual_capture/local_image_text_engine.py`, wires it as the fallback local image text engine in `runtime/capture/visual_capture/ocr.py`, reuses it from the live image-to-Markdown proof, and verifies the no-text, dense-text, low-contrast, table, and mixed-language fixture set with `ok=true`. The retained quality report is `07_LOGS/Studio-Graph-Views/2026-05-28-capture-local-image-text-quality-fixtures-builtin-local-image-text-engine-r2.json`; the retained live proof is `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-builtin-engine-image-to-markdown-live-proof.json`; the saved Markdown is `03_INPUTS/00_QUARANTINE/Sources/20260528-203913__source__visual-capture__image-to-markdown-live-proof.md`. This proves repo-owned local image-to-Markdown for the controlled Capture to Markdown evidence images without Tesseract, cloud calls, or provider calls. Arbitrary photographs and natural screenshots remain a separate engine-expansion lane if product scope requires them.
- Pass 85: common Studio-font screenshot support and explicit-path release readiness completed. The built-in local image text engine now has an in-process Windows system-font template path for common Studio-font screenshots, keeps the pixel-text path, and no longer starts a Python child process when the selected engine is the built-in engine. The quality fixture suite now includes no-text, dense-text, low-contrast, table, mixed-language, and common Studio-font screenshot cases; the retained report `07_LOGS/Studio-Graph-Views/2026-05-29-capture-local-image-text-quality-fixtures-builtin-local-image-text-engine-common-font.json` passed all six required fixtures with `ok=true`. The Capture release-readiness surface now marks explicit capture paths release-ready and presents personal browser reads plus live Discord listeners as covered by ChaseOS-owned browser capture, screen capture, local image text extraction, and Discord artifact import. The cleaned open-safety proof `07_LOGS/Studio-Graph-Views/2026-05-29-capture-markdown-common-font-engine-open-safety-cleaned.json` shows zero subprocess calls during Capture/Settings load and only `dist/studio/ChaseOS-Studio.exe` in the executable scan.
- Pass 86: active ChaseOS browser collector implemented in source. The Capture page now has a Settings-gated `Active ChaseOS browser` source card backed by `capture_active_chaseos_browser_for_markdown`, Settings can enable `active_chaseos_browser_capture_enabled`, and Studio-window shortcuts can run `run_active_browser_collector` when Capture is open. The ChaseOS-owned browser page collector registers its latest controlled artifact as active ChaseOS browser state. The active collector reads only ChaseOS-owned active browser state or a controlled artifact, requires an operator click, writes no raw quarantine Markdown on click, and feeds the normal Preview or Save flow. Personal browser profiles, cookies, sessions, history, and live personal active tabs remain outside this release path. Focused tests passed with `73 passed`.
- Pass 87: display region capture implemented in source. The Capture page now has a Settings-gated `Display region capture` source card backed by `capture_display_region_for_markdown`, Settings can enable `display_region_capture_enabled`, and Studio-window shortcuts can run `run_display_region_collector` when Capture is open. The collector opens a native Windows drag-select overlay only after a Capture page click or configured Studio shortcut, writes selected-region image evidence plus audit JSON, sets the Capture source mode to screenshot text extraction, and leaves Markdown creation to Preview or Save. Focused tests passed, and retained controlled proof shows selected-region image evidence saved into raw quarantine Markdown at `07_LOGS/Visual-QA/2026-05-29-capture-markdown-display-region-proof/display-region-proof-summary.json`. Packaged Studio was not rebuilt in this pass.
- Pass 88: Windows local optical character recognition and final packaged promotion completed. Capture to Markdown now resolves Windows Media Optical Character Recognition as a local image text engine when available, before falling back to the repo-owned controlled-image engine. Explicit image/photo files under `03_INPUTS/00_QUARANTINE/Photo-Documents/` are accepted for local image text extraction. The retained live proof `07_LOGS/Visual-QA/2026-05-29-capture-markdown-windows-photo-text-proof/windows-photo-text-proof-summary.json` extracted `CHASEOS PHOTO TEXT PROOF WINDOWS LOCAL OCR 2026` from an explicit image/photo file, saved raw quarantine Markdown, and made no cloud or provider call. The rebuilt packaged `dist/studio/ChaseOS-Studio.exe` SHA-256 is `A11EC85B45B0C6FC622DF5D7D0E973089D78F6E3E88F872B8C32671F93962DAF`; final packaged proof `07_LOGS/Visual-QA/2026-05-29-capture-markdown-final-packaged-promotion/capture-markdown-final-packaged-clickthrough-r3.json` passed with `ok=true`, verified the Capture page source cards, Settings shortcut rows, raw-quarantine Markdown save, review sidecar/packet update, nonblank native screenshot evidence, no downstream approval/canonical writes, and owned-process termination. Duplicate failed/over-broad proof artifacts and build output were cleaned while preserving the final executable and installer.

## Canonical Sources

- `docs/features/chaseos_visual_capture_markdown_ingestion_rule.md`
- `docs/plans/visual-capture-markdown-ingestion-implementation-plan.md`
- `04_SOPS/Capture-to-Markdown-CLI-SOP.md`
- `runtime/acquisition/visual_capture_source_pack_write_executor.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_readiness.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_approval_design.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_approval_request_writer.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_approval_consumption_readiness.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_approval_decision_writer.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_approval_consumption_executor.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_agent_bus_task_writer.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_readiness.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_agent_bus_task_claim_executor.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_readiness.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_aor_dry_run_executor.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_agent_bus_claimed_task_execution_status_lifecycle.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_readiness.py`
- `runtime/acquisition/visual_capture_source_pack_aor_dispatch_agent_bus_full_dispatch_executor.py`
- `runtime/acquisition/visual_capture_source_pack_sic_ingestion_readiness.py`
- `runtime/acquisition/visual_capture_source_pack_sic_ingestion_approval_design.py`
- `runtime/acquisition/visual_capture_source_pack_sic_ingestion_approval_request_writer.py`
- `runtime/acquisition/visual_capture_source_pack_sic_ingestion_approval_consumption_readiness.py`
- `runtime/acquisition/visual_capture_source_pack_sic_ingestion_approval_decision_writer.py`
- `runtime/acquisition/visual_capture_source_pack_sic_ingestion_approval_consumption_executor.py`
- `runtime/acquisition/visual_capture_source_pack_sic_ingestion_executor.py`
- `runtime/acquisition/visual_capture_source_pack_sic_graph_indexing_readiness.py`
- `runtime/acquisition/visual_capture_source_pack_sic_graph_indexing_executor.py`
- `runtime/acquisition/visual_capture_source_pack_canonical_promotion_readiness.py`
- `runtime/acquisition/visual_capture_source_pack_canonical_promotion_approval_design.py`
- `runtime/acquisition/visual_capture_source_pack_canonical_promotion_approval_request_writer.py`
- `runtime/acquisition/visual_capture_source_pack_canonical_promotion_approval_consumption_readiness.py`
- `runtime/acquisition/visual_capture_source_pack_canonical_promotion_approval_decision_writer.py`
- `runtime/acquisition/visual_capture_source_pack_canonical_promotion_approval_consumption_executor.py`
- `runtime/acquisition/visual_capture_source_pack_canonical_promotion_executor.py`
- `runtime/studio/capture_collector_settings.py`
- `runtime/studio/test_capture_collector_settings.py`
- `runtime/acquisition/test_visual_capture_source_pack_sic_graph_indexing_executor.py`
- `runtime/acquisition/test_visual_capture_source_pack_canonical_promotion_readiness.py`
- `runtime/acquisition/test_visual_capture_source_pack_canonical_promotion_approval_design.py`
- `runtime/acquisition/test_visual_capture_source_pack_canonical_promotion_approval_request_writer.py`
- `runtime/acquisition/test_visual_capture_source_pack_canonical_promotion_approval_consumption_readiness.py`
- `runtime/acquisition/test_visual_capture_source_pack_canonical_promotion_approval_decision_writer.py`
- `runtime/acquisition/test_visual_capture_source_pack_canonical_promotion_approval_consumption_executor.py`
- `runtime/acquisition/test_visual_capture_source_pack_canonical_promotion_executor.py`
- `runtime/studio/capture_to_markdown_panel.py`
- `runtime/studio/capture_hotkey_settings.py`
- `runtime/studio/capture_ocr_settings.py`
- `runtime/studio/capture_ocr_quality_fixtures.py`
- `runtime/studio/capture_markdown_image_to_markdown_live_proof.py`
- `runtime/studio/test_capture_markdown_image_to_markdown_live_proof.py`
- `runtime/capture/visual_capture/local_image_text_engine.py`
- `runtime/capture/test_local_image_text_engine.py`
- `runtime/capture/visual_capture/ocr.py`
- `runtime/capture/test_visual_capture_local_ocr.py`
- `runtime/studio/test_capture_ocr_settings.py`
- `runtime/studio/test_capture_ocr_quality_fixtures.py`
- `runtime/studio/capture_markdown_visual_qa.py`
- `runtime/studio/capture_markdown_packaged_action_clickthrough.py`
- `runtime/studio/capture_markdown_packaged_image_text_clickthrough.py`
- `runtime/studio/capture_markdown_packaged_image_text_failure_clickthrough.py`
- `runtime/studio/packaged_app_visual_qa.py`
- `runtime/studio/capture_markdown_real_chain_source_text_quality_proof.py`
- `runtime/studio/capture_markdown_output_visual_proof.py`
- `runtime/studio/capture_markdown_chaseos_browser_page_live_proof.py`
- `runtime/studio/test_capture_markdown_chaseos_browser_page_live_proof.py`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-pass61-release-readiness-product-surface.json`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-pass61-release-readiness-product-surface.md`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-pass61-release-readiness-product-surface-screenshots/capture-markdown-action-clickthrough.png`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-local-image-text-quality-fixtures-pass62-real-engine-quality.json`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-local-image-text-quality-fixtures-pass62-real-engine-quality.md`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-chaseos-browser-page-live-proof.json`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-chaseos-browser-page-live-proof.md`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-quality-fixtures-packaged-clickthrough-rerun.json`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-quality-fixtures-packaged-clickthrough-rerun.md`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-quality-fixtures-packaged-clickthrough-rerun-screenshots/capture-markdown-action-clickthrough.png`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-packaged-downstream-release-hardening.json`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-packaged-downstream-release-hardening.md`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-packaged-downstream-release-hardening-screenshots/capture-markdown-action-clickthrough.png`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-packaged-full-downstream-chain-r2.json`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-packaged-full-downstream-chain-r2.md`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-packaged-full-downstream-chain-r2-screenshots/capture-markdown-action-clickthrough.png`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-downstream-failure-state-matrix-remediated-final.json`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-downstream-failure-state-matrix-remediated-final.md`
- `07_LOGS/Studio-Graph-Views/cmdfm-remediated-final-shots/`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-chaseos-browser-page-collector.json`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-chaseos-browser-page-collector.md`
- `07_LOGS/Studio-Graph-Views/2026-05-28-capture-markdown-chaseos-browser-page-collector-screenshots/capture-markdown-action-clickthrough.png`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-pass55-packaged-action-clickthrough-final-rerun.json`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-pass59-packaged-image-text-clickthrough.json`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-pass60-image-text-failure-states.json`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-pass55-packaged-action-clickthrough-final-rerun.md`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-pass60-image-text-failure-states.md`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-pass55-packaged-action-clickthrough-final-rerun-screenshots/capture-markdown-action-clickthrough.png`
- `07_LOGS/Studio-Graph-Views/2026-05-27-capture-markdown-pass60-image-text-failure-states-screenshots/capture-markdown-image-text-failure-states.png`
- `07_LOGS/Agent-Activity/2026-05-27-codex-markdown-capture-real-chain-20260527T074357Z.md`
- `07_LOGS/Studio-Visual-QA/2026-05-27-markdown-capture-real-chain-output-proof/capture-markdown-output.png`
- `07_LOGS/Studio-Visual-QA/2026-05-27-markdown-capture-real-chain-output-proof/canonical-note-output.png`
- `07_LOGS/Studio-Visual-QA/2026-05-27-markdown-capture-real-chain-output-proof/proof-report-output.png`
- `runtime/cli/command_contract.json`
- `runtime/cli/operator_handbook_metadata.json`
- `06_AGENTS/ChaseOS-CLI-Command-Reference.md`
- `06_AGENTS/ChaseOS-CLI-Operator-Handbook.md`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-visual-capture-markdown-ingestion-pass33-source-pack-sic-ingestion-approval-decision-writer.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_visual-capture-markdown-ingestion-pass33-source-pack-sic-ingestion-approval-decision-writer.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass33-source-intelligence-core-approval-decision-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-visual-capture-markdown-ingestion-pass34-source-pack-sic-ingestion-approval-consumption-executor.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_visual-capture-markdown-ingestion-pass34-source-pack-sic-ingestion-approval-consumption-executor.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass34-source-intelligence-core-approval-consumption-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-visual-capture-markdown-ingestion-pass35-source-pack-sic-ingestion-executor.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_visual-capture-markdown-ingestion-pass35-source-pack-sic-ingestion-executor.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass35-source-intelligence-core-ingestion-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-visual-capture-markdown-ingestion-pass36-source-pack-sic-graph-indexing-readiness.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_visual-capture-markdown-ingestion-pass36-source-pack-sic-graph-indexing-readiness.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass36-source-intelligence-core-graph-indexing-readiness-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-visual-capture-markdown-ingestion-pass37-source-pack-graph-indexing-executor.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_visual-capture-markdown-ingestion-pass37-source-pack-graph-indexing-executor.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass37-source-intelligence-core-graph-indexing-executor-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-visual-capture-markdown-ingestion-pass38-source-pack-canonical-promotion-readiness.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_visual-capture-markdown-ingestion-pass38-source-pack-canonical-promotion-readiness.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass38-source-pack-canonical-promotion-readiness-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-visual-capture-markdown-ingestion-pass39-source-pack-canonical-promotion-approval-design.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_visual-capture-markdown-ingestion-pass39-source-pack-canonical-promotion-approval-design.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass39-source-pack-canonical-promotion-approval-design-user-interface/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-visual-capture-markdown-ingestion-pass40-source-pack-canonical-promotion-approval-request-writer.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_visual-capture-markdown-ingestion-pass40-source-pack-canonical-promotion-approval-request-writer.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass40-source-pack-canonical-promotion-approval-request-user-interface/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-visual-capture-markdown-ingestion-pass41-source-pack-canonical-promotion-approval-decision-consumption-readiness.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_visual-capture-markdown-ingestion-pass41-source-pack-canonical-promotion-approval-decision-consumption-readiness.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass41-source-pack-canonical-promotion-approval-decision-readiness-user-interface/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-visual-capture-markdown-ingestion-pass42-source-pack-canonical-promotion-approval-decision-writer.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_visual-capture-markdown-ingestion-pass42-source-pack-canonical-promotion-approval-decision-writer.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass42-source-pack-canonical-promotion-approval-decision-writer-user-interface/capture-markdown-visual-qa-report.json`
- `03_INPUTS/00_QUARANTINE/Sources/20260526-155104__source__visual-capture__markdown-guide-basic-syntax-web-capture-pass.md`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-visual-capture-markdown-ingestion-pass32-source-pack-sic-ingestion-approval-decision-consumption-readiness.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_visual-capture-markdown-ingestion-pass32-source-pack-sic-ingestion-approval-decision-consumption-readiness.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass32-source-intelligence-core-decision-readiness-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-visual-capture-markdown-ingestion-pass31-source-pack-sic-ingestion-approval-request-writer.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_visual-capture-markdown-ingestion-pass31-source-pack-sic-ingestion-approval-request-writer.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass31-source-intelligence-core-approval-request-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-markdown-capture-product-implementation.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_markdown-capture-product-implementation.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-pass30-source-intelligence-core-approval-design-ui/capture-markdown-visual-qa-report.json`
- `03_INPUTS/00_QUARANTINE/Sources/20260526-104937__source__visual-capture__markdown-guide-basic-syntax-web-capture-test.md`
- `07_LOGS/Build-Logs/2026-05-26-ChaseOS-mark-capture-product-readiness.md`
- `99_ARCHIVE/Documentation-History/2026-05-26_mark-capture-product-readiness.md`
- `docs/audits/2026-05-26_mark-capture-product-readiness-audit.md`
- `07_LOGS/Studio-Visual-QA/2026-05-26-vcmi-mark-capture-product-readiness-audit/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-25-ChaseOS-visual-capture-markdown-ingestion-pass28-source-pack-aor-dispatch-agent-bus-full-dispatch-executor.md`
- `99_ARCHIVE/Documentation-History/2026-05-25_visual-capture-markdown-ingestion-pass28-source-pack-aor-dispatch-agent-bus-full-dispatch-executor.md`
- `07_LOGS/Studio-Visual-QA/2026-05-25-vcmi-pass28-aor-agent-bus-full-dispatch-executor-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-25-ChaseOS-visual-capture-markdown-ingestion-pass27-source-pack-aor-dispatch-agent-bus-full-dispatch-readiness.md`
- `99_ARCHIVE/Documentation-History/2026-05-25_visual-capture-markdown-ingestion-pass27-source-pack-aor-dispatch-agent-bus-full-dispatch-readiness.md`
- `07_LOGS/Studio-Visual-QA/2026-05-25-vcmi-pass27-aor-agent-bus-full-dispatch-readiness-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-25-ChaseOS-visual-capture-markdown-ingestion-pass26-source-pack-aor-dispatch-agent-bus-claimed-task-execution-status-lifecycle.md`
- `99_ARCHIVE/Documentation-History/2026-05-25_visual-capture-markdown-ingestion-pass26-source-pack-aor-dispatch-agent-bus-claimed-task-execution-status-lifecycle.md`
- `07_LOGS/Studio-Visual-QA/2026-05-25-vcmi-pass26-aor-agent-bus-claimed-task-status-lifecycle-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-25-ChaseOS-visual-capture-markdown-ingestion-pass25-source-pack-aor-dispatch-agent-bus-claimed-task-aor-dry-run-executor.md`
- `99_ARCHIVE/Documentation-History/2026-05-25_visual-capture-markdown-ingestion-pass25-source-pack-aor-dispatch-agent-bus-claimed-task-aor-dry-run-executor.md`
- `07_LOGS/Studio-Visual-QA/2026-05-25-vcmi-pass25-aor-agent-bus-claimed-task-dry-run-executor-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-25-ChaseOS-visual-capture-markdown-ingestion-pass24-source-pack-aor-dispatch-agent-bus-claimed-task-aor-dry-run-readiness.md`
- `99_ARCHIVE/Documentation-History/2026-05-25_visual-capture-markdown-ingestion-pass24-source-pack-aor-dispatch-agent-bus-claimed-task-aor-dry-run-readiness.md`
- `07_LOGS/Studio-Visual-QA/2026-05-25-vcmi-pass24-aor-agent-bus-claimed-task-dry-run-readiness-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-24-ChaseOS-visual-capture-markdown-ingestion-pass23-source-pack-aor-dispatch-agent-bus-task-claim-executor.md`
- `99_ARCHIVE/Documentation-History/2026-05-24_visual-capture-markdown-ingestion-pass23-source-pack-aor-dispatch-agent-bus-task-claim-executor.md`
- `07_LOGS/Studio-Visual-QA/2026-05-24-vcmi-pass23-aor-agent-bus-task-claim-executor-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-24-ChaseOS-visual-capture-markdown-ingestion-pass22-source-pack-aor-dispatch-agent-bus-task-claim-readiness.md`
- `99_ARCHIVE/Documentation-History/2026-05-24_visual-capture-markdown-ingestion-pass22-source-pack-aor-dispatch-agent-bus-task-claim-readiness.md`
- `07_LOGS/Studio-Visual-QA/2026-05-24-vcmi-pass22-aor-agent-bus-task-claim-readiness-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-24-ChaseOS-visual-capture-markdown-ingestion-pass21-source-pack-aor-dispatch-agent-bus-task-writer.md`
- `99_ARCHIVE/Documentation-History/2026-05-24_visual-capture-markdown-ingestion-pass21-source-pack-aor-dispatch-agent-bus-task-writer.md`
- `07_LOGS/Studio-Visual-QA/2026-05-24-vcmi-pass21-aor-agent-bus-task-writer-ui/capture-markdown-visual-qa-report.json`
- `07_LOGS/Build-Logs/2026-05-23-ChaseOS-visual-capture-markdown-ingestion-pass20-source-pack-aor-dispatch-approval-consumption-executor.md`
- `99_ARCHIVE/Documentation-History/2026-05-23_visual-capture-markdown-ingestion-pass20-source-pack-aor-dispatch-approval-consumption-executor.md`
- `07_LOGS/Studio-Visual-QA/2026-05-23-vcmi-pass20-aor-approval-consumption-ui/capture-markdown-visual-qa-report.json`
- `docs/audits/2026-05-21_feature_family_deep_reconciliation.md`

## 2026-05-29 Capture Markdown Hotkey Active Window Proof

Status: PARTIAL broader add-on completion; active-window capture and operating-system-wide Capture collector hotkeys are implemented in source and focused tests.

Implemented in this pass:

- Active-window capture collector.
- Active-window Capture page source card.
- Active-window Settings collector toggle.
- Active-window Studio application programming interface bridge.
- Active-window Studio-window shortcut action.
- Windows foreground-window rectangle capture with window title and process identifier metadata.
- Operating-system-wide Capture collector hotkey registration runtime.
- Settings toggle for global Capture collector hotkeys.
- Global hotkey dispatch back into the Capture page for display-region and active-window collector handlers.

Proof retained:

- Active-window Markdown proof: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-active-window-proof/active-window-proof-summary.json`
- Global hotkey dispatch proof: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-global-hotkey-proof/global-hotkey-proof-summary.json`

Still not complete in this feature family:

- Packaged executable proof for this exact patch.
- Selected text from other applications.
- Accessibility tree capture.
- ChaseOS browser extension capture.
- Live Discord listener or command capture.
- Ambient clipboard monitoring, if the operator accepts the privacy risk.
- Attachment deletion and retention controls beyond the current metadata policy.
- Broad capture palette beyond the display-region drag overlay.
- Strong arbitrary photograph/document text extraction beyond controlled and common-font image text.

Build log: `07_LOGS/Build-Logs/2026-05-29-ChaseOS-capture-markdown-hotkey-active-window-proof.md`
Documentation history: `99_ARCHIVE/Documentation-History/2026-05-29_capture-markdown-hotkey-active-window-proof.md`
Agent activity: `07_LOGS/Agent-Activity/2026-05-29-codex-capture-markdown-hotkey-active-window-proof.md`

## 2026-05-29 Capture Markdown Selected Text Capture

Status: PARTIAL broader add-on completion; selected text from other applications is implemented in source and focused tests, with retained controlled Markdown proof. The active goal remains open for the remaining add-on lanes.

Implemented in this pass:

- Selected-text capture collector.
- Selected-text Capture page source card.
- Selected-text Settings collector toggle.
- Selected-text Studio application programming interface bridge.
- Selected-text Studio-window shortcut action.
- Selected-text operating-system-wide hotkey dispatch mapping through the existing global hotkey runtime.
- Explicit policy requiring Settings enablement plus a Capture page click or configured shortcut.
- Windows selected-text read path using a temporary clipboard copy, with text clipboard restoration attempted after capture.
- Raw text handoff into the existing Capture to Markdown Preview and Save flow, with no raw quarantine Markdown write on collector click.

Proof retained:

- Selected-text Markdown proof: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-selected-text-proof/selected-text-proof-summary.json`

Still not complete in this feature family:

- Packaged executable proof for this exact patch.
- ChaseOS browser extension capture.
- Accessibility tree capture.
- Live Discord listener or command capture.
- Ambient clipboard monitoring, if the operator accepts the privacy risk.
- Attachment deletion and retention controls beyond the current metadata policy.
- Broad capture palette beyond the display-region drag overlay and source cards.
- Strong arbitrary photograph/document text extraction beyond controlled and common-font image text.

Build log: `07_LOGS/Build-Logs/2026-05-29-ChaseOS-capture-markdown-selected-text-capture.md`
Documentation history: `99_ARCHIVE/Documentation-History/2026-05-29_capture-markdown-selected-text-capture.md`
Agent activity: `07_LOGS/Agent-Activity/2026-05-29-codex-capture-markdown-selected-text-capture.md`

## 2026-05-29 Capture Markdown Attachment Retention Controls

Status: PARTIAL broader add-on completion; attachment deletion/retention controls are implemented in source, wired to Studio, and verified with retained proof. The active goal remains open for the remaining external capture and broader image-text lanes.

Implemented in this pass:

- Attachment retention/disposition controls on recent Capture to Markdown rows.
- Studio application programming interface methods for attachment disposition updates and copied-attachment cleanup.
- Disposition states for retain, retain until downstream review, needs redaction, and request deletion.
- Guarded cleanup executor for copied quarantine-local attachments only.
- Exact operator confirmation phrase requirement before deletion: `DELETE CAPTURE ATTACHMENTS`.
- Sidecar and visual-capture packet metadata updates for disposition and cleanup history.
- Recent capture readback fields for attachment count, disposition, deletion request status, and cleanup availability.

Proof retained:

- Attachment retention and cleanup proof: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-attachment-retention-proof/attachment-retention-proof-summary.json`

Still not complete in this feature family:

- Packaged executable proof for this exact patch.
- ChaseOS browser extension capture.
- Accessibility tree capture.
- Live Discord listener or command capture.
- Ambient clipboard monitoring, if the operator accepts the privacy risk.
- Broad capture palette beyond the display-region drag overlay and source cards.
- Strong arbitrary photograph/document text extraction beyond controlled and common-font image text.

Build log: `07_LOGS/Build-Logs/2026-05-29-ChaseOS-capture-markdown-attachment-retention-controls.md`
Documentation history: `99_ARCHIVE/Documentation-History/2026-05-29_capture-markdown-attachment-retention-controls.md`
Agent activity: `07_LOGS/Agent-Activity/2026-05-29-codex-capture-markdown-attachment-retention-controls.md`

## 2026-05-29 Capture Markdown Accessibility Tree Capture

Status: PARTIAL broader add-on completion; accessibility tree capture is implemented in source, wired to Studio, and verified with retained controlled Markdown proof. The active goal remains open for the remaining browser-extension, live Discord, ambient clipboard decision, broader palette, packaged proof, and arbitrary photograph/document text-extraction lanes.

Implemented in this pass:

- Accessibility tree capture collector.
- Accessibility tree Capture page source card.
- Accessibility tree Settings collector toggle.
- Accessibility tree Studio application programming interface bridge.
- Accessibility tree Studio-window shortcut action.
- Accessibility tree operating-system-wide hotkey dispatch mapping through the existing global hotkey runtime.
- Explicit policy requiring Settings enablement plus a Capture page click or configured shortcut.
- Windows foreground accessibility tree provider using local Windows Automation through PowerShell and .NET.
- Raw text handoff into the existing Capture to Markdown Preview and Save flow, with no raw quarantine Markdown write on collector click.
- External capture surface policy update marking accessibility tree capture implemented under explicit operator action.

Proof retained:

- Accessibility tree Markdown proof: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-accessibility-tree-proof/accessibility-tree-proof-summary.json`

Still not complete in this feature family:

- Packaged executable proof for this exact patch.
- ChaseOS browser extension capture.
- Live Discord listener or command capture.
- Ambient clipboard monitoring, if the operator accepts the privacy risk.
- Broad capture palette beyond the display-region drag overlay and source cards.
- Strong arbitrary photograph/document text extraction beyond controlled and common-font image text.
- Real third-party foreground application matrix proof across multiple accessibility providers.

Build log: `07_LOGS/Build-Logs/2026-05-29-ChaseOS-capture-markdown-accessibility-tree-capture.md`
Documentation history: `99_ARCHIVE/Documentation-History/2026-05-29_capture-markdown-accessibility-tree-capture.md`
Agent activity: `07_LOGS/Agent-Activity/2026-05-29-codex-capture-markdown-accessibility-tree-capture.md`

## 2026-05-29 Capture Markdown Browser Extension Capture

Status: PARTIAL broader add-on completion; ChaseOS browser extension capture is implemented in source, wired to Studio, and verified with retained controlled Markdown proof. The active goal remains open for packaged executable promotion, live Discord, ambient clipboard decision, broader capture palette, and stronger arbitrary photograph/document text extraction.

Implemented in this pass:

- ChaseOS browser extension package under `runtime/browser_extension/capture_to_markdown`.
- Manifest V3 popup, service worker, content script, and package README.
- Browser extension artifact schema `chaseos.capture.browser_extension.v1`.
- Browser extension Capture page source card.
- Browser extension Settings collector toggle.
- Browser extension Studio application programming interface bridge.
- Browser extension Studio-window shortcut action.
- Explicit policy requiring Settings enablement, Capture page click, and operator-selected artifact file.
- Artifact path, schema, size, source address, and browser-private-data guards.
- Raw text handoff into the existing Capture to Markdown Preview and Save flow, with no raw quarantine Markdown write on collector click.
- External capture surface policy update marking browser extension capture implemented under explicit operator action.

Proof retained:

- Browser extension Markdown proof: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-browser-extension-proof/browser-extension-proof-summary.json`
- Controlled extension artifact: `07_LOGS/Browser-Extension-Captures/chaseos-browser-extension-proof-20260529165530.json`
- Saved Markdown: `03_INPUTS/00_QUARANTINE/Sources/20260529-165530__source__visual-capture__chaseos-browser-extension-proof-page-20260529.md`

Still not complete in this feature family:

- Packaged executable proof for this exact patch.
- Manual clickthrough with the extension installed in a real browser.
- Live Discord listener or command capture.
- Ambient clipboard monitoring, if the operator accepts the privacy risk.
- Broad floating capture palette beyond the display-region drag overlay and source cards.
- Strong arbitrary photograph/document text extraction beyond controlled and common-font image text.

Build log: `07_LOGS/Build-Logs/2026-05-29-ChaseOS-capture-markdown-browser-extension-capture.md`
Documentation history: `99_ARCHIVE/Documentation-History/2026-05-29_capture-markdown-browser-extension-capture.md`
Agent activity: `07_LOGS/Agent-Activity/2026-05-29-codex-capture-markdown-browser-extension-capture.md`

## 2026-05-29 Capture Markdown Ambient Clipboard Monitor

Status: PARTIAL broader add-on completion; ambient clipboard monitoring is implemented in source, wired to Studio, and verified with retained controlled Markdown proof. The active goal remains open for packaged executable promotion, broader floating capture palette, live Discord, and stronger arbitrary photograph/document text extraction.

Implemented in this pass:

- Privacy-gated ambient clipboard monitor collector.
- Ambient clipboard Capture page source card.
- Ambient clipboard Settings collector toggle.
- Ambient clipboard Studio application programming interface bridge.
- Ambient clipboard Studio-window shortcut action.
- Explicit policy requiring Settings enablement plus an active monitoring session.
- Retention-limited local ring buffer under Studio state.
- Exact confirmation cleanup phrase: `CLEAR AMBIENT CLIPBOARD`.
- Raw text handoff into the existing Capture to Markdown Preview and Save flow, with no raw quarantine Markdown write on monitor poll.
- External capture surface policy update marking ambient clipboard capture implemented only under privacy opt-in and active session authority.

Proof retained:

- Ambient clipboard Markdown proof: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-ambient-clipboard-proof/ambient-clipboard-proof-summary.json`
- Saved Markdown: `03_INPUTS/00_QUARANTINE/Sources/20260529-173400__source__visual-capture__ambient-clipboard-proof-20260529173400.md`

Still not complete in this feature family:

- Packaged executable proof for this exact patch.
- Long-running packaged monitor clickthrough.
- Live Discord listener or command capture.
- Broad floating capture palette beyond the display-region drag overlay and source cards.
- Strong arbitrary photograph/document text extraction beyond controlled and common-font image text.

Build log: `07_LOGS/Build-Logs/2026-05-29-ChaseOS-capture-markdown-ambient-clipboard-monitor.md`
Documentation history: `99_ARCHIVE/Documentation-History/2026-05-29_capture-markdown-ambient-clipboard-monitor.md`
Agent activity: `07_LOGS/Agent-Activity/2026-05-29-codex-capture-markdown-ambient-clipboard-monitor.md`

## 2026-05-29 Capture Markdown Capture Palette

Status: PARTIAL broader add-on completion; the Capture palette overlay is implemented in source, wired to the Capture page, and verified with retained model/frontend proof. The active goal remains open for packaged executable promotion, live Discord, and stronger arbitrary photograph/document text extraction.

Implemented in this pass:

- `Capture palette` source option.
- Capture page palette button.
- Modal-style Capture palette overlay.
- Palette action buttons for existing source actions.
- Frontend dispatch through existing collectors/source modes.
- CSS for the palette overlay and actions.
- Readiness/authority fields proving the palette adds no new capture authority and writes no Markdown on open.

Proof retained:

- Capture palette proof: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-palette-proof/capture-palette-proof-summary.json`

Still not complete in this feature family:

- Packaged executable proof for this exact patch.
- Live Discord listener or command capture.
- Strong arbitrary photograph/document text extraction beyond controlled and common-font image text.

Build log: `07_LOGS/Build-Logs/2026-05-29-ChaseOS-capture-markdown-capture-palette.md`
Documentation history: `99_ARCHIVE/Documentation-History/2026-05-29_capture-markdown-capture-palette.md`
Agent activity: `07_LOGS/Agent-Activity/2026-05-29-codex-capture-markdown-capture-palette.md`

## 2026-05-31 Current Proof Accounting

Status: COMPLETE for the requested Capture to Markdown proof lanes listed below. Earlier `PARTIAL` rows in this feature node are historical pass statuses from before the later lanes were implemented and verified.

Current retained proof:

- Capture overlay/palette: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-palette-proof/capture-palette-proof-summary.json`
- Display-region capture: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-display-region-proof/display-region-proof-summary.json`
- Operating-system-wide global hotkey registration: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-global-hotkey-proof/global-hotkey-proof-summary.json`
- Browser extension capture: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-browser-extension-proof/browser-extension-proof-summary.json`
- Live Discord command capture through ChaseOS Agent Bus ingress: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-live-discord-command-proof/live-discord-command-proof-summary.json`
- Attachment deletion/retention controls: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-attachment-retention-proof/attachment-retention-proof-summary.json`
- Stronger local image text extraction through Windows Media Optical Character Recognition: `07_LOGS/Visual-QA/2026-05-29-capture-markdown-windows-photo-text-proof/windows-photo-text-proof-summary.json`

Capture overlay/palette proof details:

- `ok=true`
- `proof_type`: `capture_palette_model_and_frontend_wiring`
- `capture_palette_overlay_ready=true`
- `capture_palette_overlay_blocked=false`
- `palette_option_available=true`
- Frontend open, close, source-action dispatch, palette button, palette action buttons, and palette styling are present.
- Required actions present include display-region collector, active-window collector, clipboard text collector, ambient clipboard monitor, selected-text collector, accessibility tree collector, and browser-extension collector.
- The palette adds no new capture authority and does not write Markdown when opened.

Current accounting log: `07_LOGS/Build-Logs/2026-05-31-ChaseOS-capture-markdown-final-audit-cleanup.md`

Focused proof bundle: `07_LOGS/Visual-QA/2026-05-31-capture-markdown-proof-accounting/proof-accounting-summary.json`

Focused proof bundle status: `complete`; `palette_accounted_alongside_other_lanes=true`; seven named lanes present and `ok=true`.

## Graph Links

[[Connector-Capture-Architecture]] [[Acquisition-Normalization-Layer]] [[Source-Intelligence-Core]] [[ChaseOS-Feature-Family-and-Subfeature-Inventory]]
