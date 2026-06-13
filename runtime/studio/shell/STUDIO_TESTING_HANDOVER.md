# ChaseOS Studio — Testing Handover Document

**Purpose:** Standalone reference for a separate Claude session to systematically test, debug, and verify every panel in ChaseOS Studio. Work panel by panel; mark each as PASS / FAIL / SKIP with notes.

**Created:** 2026-05-27  
**Last updated:** 2026-05-28 (R18 Tier B Remaining Panels v2 — Intake card glass + teal hover + trust-badge teal; Acquisition source/run cards glass + teal hover + success badges teal; Bus task/heartbeat cards glass + done badge teal + hb-ok health teal + state-ready teal border + section panels glass)  
**State at handover:** All redesigns from both sessions require an app restart before testing.

---

## How to Launch the Shell

```powershell
# Activate venv
& "<VAULT_ROOT>\.venv\Scripts\Activate.ps1"

# Launch desktop shell
chaseos studio shell

# OR: launch the compiled EXE (if available)
& "<VAULT_ROOT>\runtime\studio\shell\dist\studio\ChaseOS-Studio.exe" --vault-root "<VAULT_ROOT>"
```

**Vault root:** `<VAULT_ROOT>`  
**Frontend files:** `runtime/studio/shell/frontend/`  
**Backend API:** `runtime/studio/shell/api.py`  
**Tray/icon:** `runtime/studio/shell/tray.py`

---

## Known Issues Requiring App Restart

These changes were made in the last session and are not yet verified:

| # | Change | File(s) | Expected Outcome |
|---|--------|---------|-----------------|
| R1 | Home page complete redesign (5-row layout) | `app.js`, `styles.css`, `index.html` | Home shows runtime strip, Now.md strip, 4 metric chips, attention+launch grid, activity strip. No tabs, no intent input, no VentureOps. |
| R2 | No-scroll enforcement for most panels | `styles.css` | Panels fit within viewport — no vertical scrollbar except Chat, Docs/Inspector, Settings |
| R3 | C-kernel tray icon (teal C-arc + violet nodes) | `tray.py` | Tray icon and Windows taskbar icon both show C-kernel design |
| R4 | Studio Status panel added to Dev Tools sidebar | `app.js`, `index.html`, `styles.css`, `api.py` | "Studio Status" button appears under Advanced governance section; clicking loads build status |
| R5 | Home v2 — ambient background system | `styles.css`, `app.js` | Ambient toggle (Off / Fog / Glow) in runtime strip row; aurora fog (Option 1) or breathing radial (Option 2); CSS-only, no canvas/WebGL; `prefers-reduced-motion` respected; pauses when tab is hidden |
| R6 | Home v2 — companion mascot (C-kernel) | `styles.css`, `app.js` | C-arc SVG mascot bottom-right of home layout; idle float animation (5px bob, 5.5s); hover lifts tooltip; `companion--alert` (amber) when approvals pending; `companion--happy` (teal) otherwise |
| R7 | Home v2 — profile-driven runtime strip | `api.py`, `app.js` | Runtime chips read `profile.json` for display name and personal name; Hermes + OpenClaw show teal `24/7` badge (`lane_class: persistent`); Archon shows session dot; no hardcoded name dict |
| R8 | Home v2 — launch button icons + tooltips | `app.js`, `styles.css` | Each of 8 launch buttons has an inline SVG icon; icon shifts color on hover; tooltip text on hover; button lifts (`translateY(-2px)`) with panel-colour glow |
| R9 | Home v2 — activity cards (v2) | `app.js`, `styles.css` | Recent activity shown as full-width cards (icon badge + title + timestamp) instead of plain text chips |
| R10 | Home v2 — card glass treatment | `styles.css` | Home cards get `color-mix` semi-transparent background + `backdrop-filter: blur(10px)` for glass depth; runtime chip persistent glow dot + teal border |
| R11 | Chat panel v2 — palette + visual redesign | `styles.css` | ~280 lines appended, all scoped to `body.chat-page-active`: segmented adapter pill control (teal selected state), teal status pip, compact daemon strip, runtime pulse dot in thread header, glass message bubbles (user = teal/violet gradient, runtime = dark glass violet border), empty thread as clean text, glass composer box, teal send button with glow |
| R12 | Graph panel v2 — palette + glass redesign | `styles.css` | ~140 lines appended, all scoped to `#panel-graph`: header increased transparency (78%) + backdrop-filter blur(14px) + teal top-border stripe; h2 reduced to 15px; description muted/smaller; authority chips more compact; search glass bg + enhanced focus ring; toolbar buttons glass base; filter panel backdrop-filter; `#graph-node-count` chip teal (border + text + bg); legend dark glass; quality chip teal accent alignment |
| R13 | Standard Panels v2 — global panel header + Approvals queue | `styles.css` | ~90 lines appended, global scope: `.panel-title-row` glass card (elevated bg + teal 2px top stripe + border + rounded + shadow); `.panel-title-row h2` 15px (down from 18px); `.panel-subtitle` 11px muted; `.runtime-authority-row span` transparent bg + 9px + tighter padding; `.approval-queue-item` glass bg + teal 3px left border + hover; `.approval-stat-pill:first-child` teal pending accent; `.btn-approve`/`.btn-reject` 8px radius; `.approval-center-tech` glass |
| R14 | Content Panels v2 — Runtime Cockpit, Schedules, AOR card glass + teal | `styles.css` | ~90 lines appended: `.rc-runtime-card` glass + teal hover; `.rc-status-live` teal (from green); `.rc-bus-fresh` teal; `.rc-tech-details` glass; `.schedules-card` glass + teal hover; `.schedules-badge-enabled` teal (from green); `.schedules-stats-row` glass; `.aor-exec-card` glass + teal hover; `.aor-badge-success` teal (from green); `.aor-stat-success` teal |
| R15 | Inspector & List Panels v2 — Node Inspector toolbar + tab strip + list items | `styles.css` | ~65 lines appended: `.node-inspector-toolbar` glass bg + teal 2px top stripe + `border-bottom-color` subtle; h2 15px; description 11px muted; `.node-tab-strip` slightly elevated bg; `.node-inspector-tab.active` teal `2px` top border + teal text; inactive tab teal hover; `.build-log-item` rounded 8px + teal hover border + teal active state; `.decision-item--active` teal tint bg |
| R16 | Misc Panel Cards v2 — Memory Manager, Site Skills, Daemon | `styles.css` | ~50 lines appended: `.ml-runtime-card`/`.rnm-runtime-card` glass; `.ml-status-complete` teal (from green); `.siteops-run-card` glass + teal hover + 8px radius; `.daemon-runtime-card` glass + `.daemon-running` teal border (from green); `.settings-tab-btn.active` teal text |
| R17 | Tier C Panels v2 — Decision/Pivot, Role Cards, Agent Identity, RNM, Support Loops, Provenance | `styles.css` | ~65 lines appended: `.decision-item`/`.pivot-item` teal left-border on hover; `.role-card-item--active` teal bg+text+border (from blue); `.ai-ledger-card` glass; `.ai-posture-seeded` teal (from green); `.rnm-status-seeded` teal (from blue); `.runtime-support-card` glass + teal hover; `.provenance-record-card` glass; `.provenance-trust-pill.ts-promoted` teal (from green); `.daemon-runtime-status.status--running` teal (from green) |
| R18 | Tier B Remaining Panels v2 — Intake, Acquisition, Agent Bus | `styles.css` | ~84 lines appended: `.intake-item` glass + teal hover border; `.intake-trust-badge.ts-promoted` teal (from green); `.acquisition-source-card`/`.acquisition-run-card` glass + teal hover; `.acquisition-badge-success`/`-succeeded` teal (from green); `.acquisition-msg-ok` teal; first stat pill teal; `.bus-task-card`/`.bus-heartbeat-card` glass; `.bus-badge-done` teal (from green); `.bus-hb-ok .bus-hb-health` teal; `.bus-state-ready` teal border; bus section panels glass backdrop; bus inner cards glass |

---

## Testing Checklist by Panel

Priority tiers:
- **Tier A — Critical path** (must work; blocks core operator loop)
- **Tier B — Important** (used regularly)
- **Tier C — Reference/Dev** (important but not daily)

---

### TIER A — Critical Path Panels

---

#### 1. Home (`dashboard`)

**Nav label:** Home | **Shortcut:** `1` | **State:** Live  
**Version:** v2 (ambient background, companion, profile-driven runtimes, icon buttons, activity cards)

**What should happen:**
- Loads a 5-row layout filling the viewport without vertical scroll
- **Row 1 — Runtime strip:** Shows runtime chips driven by `profile.json` (not hardcoded); Hermes + OpenClaw show `24/7` teal badge; Archon shows session dot; ambient toggle widget (Off / Fog / Glow) sits at far right of this row
- **Row 2 — Now.md strip:** Shows first 5 lines from `00_HOME/Now.md` in a violet-tinted glass strip labeled `NOW`
- **Row 3 — Metric chips:** 4 chips: Pending Approvals / Bus Tasks / Graph Nodes / Enabled Schedules — each clickable to navigate to the relevant panel
- **Row 4 — Main row:** Left column (Attention items) + Right column (2×4 launch grid with icon + label + tooltip per button)
- **Row 5 — Recent activity:** Full-width activity cards (icon badge + title + timestamp); empty-state card if no logs
- **Companion:** C-kernel SVG mascot at bottom-right of `.home-layout`; floats continuously; amber glow when approvals pending; teal glow otherwise; shows "ChaseOS" label on hover
- **Ambient:** `#home-ambient` div beneath dashboard-body; applies aurora fog or breathing radial class from localStorage; CSS-only animations; pauses when tab hidden

**Tests:**
- [ ] Panel loads without vertical scrollbar
- [ ] **Runtime strip v2:** Chips show Hermes and OpenClaw with `24/7` badge (teal border, glow dot). Archon shows session dot (muted). Names come from profile data (not hardcoded strings)
- [ ] Hovering a runtime chip shows a tooltip with the runtime's primary role
- [ ] Now.md strip shows actual content (not "No sprint focus loaded")
- [ ] Each metric chip is clickable and navigates to the correct panel
- [ ] Launch grid — all 8 buttons show an SVG icon + label; hovering shows tooltip text; clicking navigates correctly:
  - Graph → `graph`
  - Approvals → `approval-center`
  - Intake → `intake`
  - Schedules → `schedules`
  - Bus → `bus`
  - Memory → `runtime-memory-inspector`
  - Pulse → `pulse-enqueue`
  - Chat → `chat`
- [ ] Launch button hover: button lifts (`translateY(-2px)`), icon colour shifts, subtle glow appears
- [ ] Recent activity renders as cards (icon badge + title + timestamp), not plain text chips
- [ ] Companion mascot is visible at bottom-right (C-arc SVG, floating animation)
- [ ] Companion is amber-glowing when approvals are pending, teal when none
- [ ] Hovering companion shows "ChaseOS" label
- [ ] **Ambient toggle:** Off / Fog / Glow buttons appear in runtime strip row
  - Fog: aurora radial blobs drift slowly behind dashboard content
  - Glow: single breathing radial centre glow
  - Off: no animation, plain background
  - Selection persists after panel switch (localStorage)
- [ ] With `prefers-reduced-motion` set in OS: ambient animations are frozen (test in browser DevTools → Rendering → Emulate CSS media)
- [ ] Tab-switch away and back: ambient animation pauses while tab is hidden
- [ ] No console errors on load

**API calls used:** `get_dashboard()`, `get_now_md_summary()`, `get_runtime_profiles()`  
**New API method (R7):** `get_runtime_profiles()` — reads `runtime/memory/adapters/*/profile.json`, returns `runtime_id`, `display_name`, `personal_name`, `primary_role`, `lane_class`

---

#### 2. Graph (`graph`)

**Nav label:** Graph | **Shortcut:** `3` | **State:** Approval-gated  
**Version:** v2 (header glass, teal node-count chip, filter panel backdrop-filter, compact authority row)

**What should happen:**
- 3D force graph (Three.js/WebGL) loads with all vault nodes (~160 nodes, ~554 links per Phase 4 verification)
- Scan limit warnings in console are normal/informational
- Node click → inspector panel opens with node detail
- Graph search filters nodes by label
- Filter panel (Ctrl+F) shows node type / trust state / edge type filters
- Quick Switch (Ctrl+O) shows fuzzy label/path search overlay
- Preset bar at top shows available presets

**v2 visual targets (R12):**
- **Header:** More transparent (78% opacity) with `backdrop-filter: blur(14px)` — glass effect. Teal `2px` top-border stripe (`rgba(57,230,210,0.18)`). Smaller `h2` (15px) and muted description text (11px). Authority row chips are compact/smaller footprint.
- **Search input:** Glass background, teal border + outer glow ring on focus (matching Chat v2 composer focus style)
- **Toolbar + focus depth buttons:** Glass base background; teal hover already in place (unchanged)
- **Filter panel:** `backdrop-filter: blur(12px)` + teal top-border stripe when open — matches header treatment
- **Preset bar:** Slightly more opaque + `backdrop-filter: blur(10px)` for consistent depth layering
- **Status dock `#graph-node-count` chip:** Teal text + teal border tint + teal bg tint — visually distinguished from the other 3 muted chips
- **Legend:** Darker glass (`rgba(11,18,34,0.86)`) + blur(8px) + subtle white border
- **Quality chip:** Teal-accented when Balanced; violet when Ultra (matching existing colour convention)

**Tests:**
- [ ] Graph renders with visible nodes (not blank)
- [ ] Click any node → Docs/Inspector panel opens with that node's data
- [ ] Graph search filters work (type a node name, graph updates)
- [ ] Filter toggle opens filter panel
- [ ] Quick Switch overlay opens on Ctrl+O
- [ ] Preset bar renders with selectable presets
- [ ] No crash on graph load
- [ ] **v2 — Header:** header is visually more transparent/glass than v1; `h2` is visibly smaller (15px); description is smaller/muted; authority chips are compact
- [ ] **v2 — Header top border:** Thin teal stripe visible at top of the header card
- [ ] **v2 — Search focus:** Teal border + outer glow ring when input is focused
- [ ] **v2 — Node count chip:** `#graph-node-count` shows teal text + teal border (distinct from other 3 grey chips)
- [ ] **v2 — Filter panel:** When open, has glass backdrop-filter treatment (semi-transparent, blurred) with teal top stripe
- [ ] **v2 — Legend:** Dark glass pill in bottom-right (no regression from v1)
- [ ] **v2 — Quality chip:** Shows teal accent when set to Balanced/Ultra (not just muted grey)
- [ ] No other panels affected (these styles are scoped to `#panel-graph`)

**API calls used:** `get_graph_contract()`  
**CSS changes:** ~140 lines appended to `styles.css` — scoped under `#panel-graph`; zero impact on other panels

---

#### 3. Approvals (`approval-center`)

**Nav label:** Approvals | **Shortcut:** `5` | **State:** Read-only  
**Version:** v2 (standard panels glass header, approval items teal left border, pending stat pill teal)

**What should happen:**
- Shows pending approval queue (or empty-state if no pending approvals)
- Each approval item shows description, target file, action type, and approve/reject buttons
- Approval badge count in sidebar stays in sync with pending count

**v2 visual targets (R13 — applies to this panel + all standard panels):**
- **Panel header:** `.panel-title-row` now renders as a glass card — slightly elevated background, teal `2px` top-border stripe, rounded corners, subtle shadow. `h2` is 15px (down from 18px). Subtitle is 11px muted.
- **Authority chips:** Transparent background (was solid dark), 9px text — less visual weight
- **Queue items:** Glass background + `3px` teal left border accent; brightens on hover
- **Stat pills:** First pill (pending count) shows in teal (border + bg + text)
- **Approve / Reject buttons:** Existing green/red palette preserved, rounded 8px

**Tests:**
- [ ] Panel loads with approval list or structured empty-state card
- [ ] **v2 — Panel header** is visually a glass card with teal top stripe (distinct from body content)
- [ ] **v2 — H2** is noticeably smaller (15px) — consistent with Graph panel header size
- [ ] **v2 — Authority chips** (Queue, Decisions, Digest review, No execution) are transparent with compact text
- [ ] **v2 — Queue items** show teal left border; hover brightens the left border
- [ ] **v2 — Stat pills** — first pill (e.g. "2 pending") shows teal colour; other pills remain muted
- [ ] Approval badge count in nav reflects actual count
- [ ] Topbar "Approvals" count chip matches
- [ ] Approve button (green) and Reject button (red) are functional and visually correct
- [ ] "Evidence & Boundaries" `<details>` section has glass background

**API calls used:** `get_approval_queue()`  
**CSS changes:** ~90 lines appended to `styles.css` — global scope (affects all panels using `.panel-title-row`)

---

#### 4. Agents / Runtimes (`runtime-cockpit`)

**Nav label:** Agents / Runtimes | **Shortcut:** `6` | **State:** Approval-gated  
**Version:** v2 (standard panel header glass + teal top stripe; runtime cards glass + teal live/fresh status)

**What should happen (from Phase 4+5 verification):**
- Archon: `current_state: live`, `bus_heartbeat.freshness: fresh`
- Hermes (WSL): `current_state: live` when WSL is running
- OpenClaw: `current_state: live`, `bus_heartbeat.freshness: fresh`
- Runtimes NOT running show `idle` (not `blocked`) with `platform: local-session`

**v2 visual targets (R13 + R14):**
- Panel header is a glass card with teal top stripe (R13 — same as all standard panels)
- Runtime cards have glass background; hover shows teal border
- `live` status badge is **teal** (not green) — matches palette
- `idle` stays blue/cyan; `offline` stays grey; `blocked` stays red
- Bus freshness `fresh` badge is teal

**Tests:**
- [ ] Panel loads with runtime list
- [ ] **v2 — Panel header** is glass card with teal top stripe
- [ ] **v2 — Runtime cards** have glass background + teal hover border
- [ ] **v2 — Live badge** shows teal (not green) when runtime is live
- [ ] **v2 — Bus fresh badge** shows teal when fresh
- [ ] Archon shows `live` (hooks fire on each prompt)
- [ ] Bus heartbeat freshness shown for each runtime
- [ ] Summary counts shown (total/live/idle/blocked)

**API calls used:** `get_runtime_cockpit_status()` or `build_runtime_cockpit_contract()`  
**CSS changes:** R13 global header + R14 card content (see build logs)

---

#### 5. Schedules (`schedules`)

**Nav label:** Schedules | **Shortcut:** `7` | **State:** Approval-gated  
**Version:** v2 (standard panel header glass; schedule cards glass + teal enabled badge)

**What should happen (from Phase 4 verification):**
- 9 schedule intents listed
- Each shows cron expression, enabled/disabled state, last-run info

**v2 visual targets (R13 + R14):**
- Panel header is a glass card with teal top stripe
- Schedule cards have glass background + teal hover border
- **Enabled badge** is teal (not green) — `schedules-badge-enabled` now uses `var(--accent)`
- Stats row has glass base background

**Tests:**
- [ ] Panel loads with schedule list (not empty-state)
- [ ] **v2 — Panel header** is glass card with teal top stripe
- [ ] **v2 — Schedule cards** have glass background + teal hover border
- [ ] **v2 — Enabled badge** shows teal (not green) for enabled schedules
- [ ] Disabled schedules: badge is muted/grey (unchanged)
- [ ] Schedule detail expandable

**API calls used:** `get_schedule_summary()`

---

#### 6. Tasks & Runs (`aor`)

**Nav label:** Tasks & Runs | **Shortcut:** `8` | **State:** Read-only  
**Version:** v2 (standard panel header glass; AOR exec cards glass + teal success badge)

**What should happen (from Phase 4 verification):**
- 50 recent runs listed
- Each shows workflow name, status, timestamp
- Click to inspect individual run

**v2 visual targets (R13 + R14):**
- Panel header is a glass card with teal top stripe
- AOR execution cards have glass background + teal hover border
- **Success badge** is teal (not green) — `aor-badge-success` now uses `var(--accent)`
- Success stat text in summary is teal

**Tests:**
- [ ] Panel loads with run list (not empty)
- [ ] **v2 — Panel header** is glass card with teal top stripe
- [ ] **v2 — AOR cards** have glass background + teal hover border
- [ ] **v2 — Success badge** shows teal (not green) for successful runs
- [ ] Escalated badge stays yellow; failed badge stays red (unchanged)
- [ ] Run detail expandable

**API calls used:** `get_aor_summary()`

---

#### 7. Chat (`chat`)

**Nav label:** Chat | **Shortcut:** `2` | **State:** Approval-gated  
**Version:** v2 (teal palette, segmented adapter control, glass bubbles, teal send, runtime pulse dot)

**What should happen:**
- Full-height chat shell (left rail + main area) — no page scroll; only the conversation stream scrolls
- **Left rail:** Adapter selector redesigned as a segmented pill control (Hermes / OpenClaw as compact teal-selectable chips). Thread search input with teal focus ring. Thread list with teal selection highlight. Daemon control as a compact strip.
- **Main area:** Thread header with folder path + runtime name + pulsing status dot (teal when live, amber when warning, muted when offline). Conversation stream with glass bubbles — user messages right-aligned teal/violet gradient; runtime messages left-aligned dark glass with violet border. Empty thread state is clean centered text (not a dashed box). Composer is a glass-bordered pill with teal send button.
- **Teal send button:** Gradient teal (`#39e6d2 → #0d9488`) with glow on hover. Dark text on teal. Disabled state: washed-out teal, no glow.
- **Runtime status dot:** Lives in thread header next to runtime name. Pulses continuously when `is-live`. Static amber dot when `is-warning`. Static muted when `is-offline`.

**Tests:**
- [ ] Panel loads with full-height chat shell — no vertical scrollbar on the outer panel
- [ ] Adapter selector: Hermes/OpenClaw appear as segmented pill buttons. Selected one shows teal border + teal text
- [ ] Status pip on adaptor card shows teal dot with glow when runtime is live
- [ ] Thread search input: teal focus ring when focused
- [ ] Selecting a thread: thread nav row shows teal border + teal-tinted background
- [ ] Thread header: runtime name + status `em` element visible. When runtime is live, the `em` shows teal pulsing dot before text
- [ ] User message bubble: right-aligned, teal/violet gradient border
- [ ] Runtime message bubble: left-aligned, dark glass background, violet-tinted border
- [ ] Sender labels in message head: teal for user, violet for runtime
- [ ] Empty thread state: plain centered text (no dashed box border)
- [ ] Composer box: teal-tinted border (`rgba(57,230,210,0.22)`); focus-within applies stronger teal border + subtle glow
- [ ] Send button: teal gradient background, dark text, glow on hover
- [ ] Send button disabled: washed-out appearance, cursor: not-allowed
- [ ] File / Image tool buttons: muted style, teal tint on hover
- [ ] Daemon control: compact strip, start button shows teal styling
- [ ] Offline banner (if visible): amber tint (not default browser style)
- [ ] Manage menu `<details>`: subtle border chip appearance, teal on hover
- [ ] Vertical scroll of conversation stream works; outer panel does not scroll

**API calls used:** `get_phase11_chat_workspaces_foundation()`, `get_chat_runtime_availability()`  
**CSS changes:** ~280 lines appended to `styles.css` — all scoped under `body.chat-page-active`; zero impact on other panels

---

### TIER B — Important Panels

---

#### 8. Docs / Inspector (`node-inspector`)

**Nav label:** Docs / Inspector | **State:** Approval-gated  
**Version:** v2 (toolbar glass + teal top stripe, compact h2, active tab teal border)

**What should happen:**
- Full-width route panel (`#panel-node-inspector`) with tab strip
- Activated when clicking a graph node
- 7 tabs: Overview / Relations / Provenance / Trust / Runtime / Source / Debug
- Overview tab shows formatted Markdown with WikiLink rendering
- WikiLinks are clickable purple links that open in a new inspector tab
- Tab strip supports pinning, bookmarking, and multi-tab workspace
- Quick Switch (Ctrl+O) overlays on this panel too

**v2 visual targets (R15):**
- **Toolbar:** Glass elevated background + teal `2px` top-border stripe; `h2` is 15px; description is 11px muted
- **Active tab:** Teal `2px` top-border + teal text (clearly indicates which node tab is active)
- **Inactive tab hover:** Teal text tint
- **Tab strip:** Slightly elevated background separating it from toolbar and content

**Tests:**
- [ ] Click a graph node → inspector opens
- [ ] **v2 — Toolbar** has glass background + teal top stripe (consistent with all other panel headers)
- [ ] **v2 — Active tab** shows teal top border + teal text (clearly distinguishable from inactive tabs)
- [ ] **v2 — Inactive tab hover** shows teal text tint
- [ ] Markdown renders (not raw text)
- [ ] WikiLinks appear as clickable purple links
- [ ] Clicking a WikiLink opens a new tab for that node
- [ ] Pin tab stays when switching tabs
- [ ] Bookmark tab persists across panel switches (localStorage)
- [ ] Tab context menu opens on right-click
- [ ] Vertical scroll works on this panel

**API calls used:** `get_node()`, `get_node_full_content()`, `get_provenance()`  
**CSS changes:** R15 inspector/list pass

---

#### 9. Intake (`intake`)

**Nav label:** Intake | **Shortcut:** `4` | **State:** Approval-gated  
**Version:** v2 (Intake item cards glass + teal hover + promoted badge teal)

**What should happen (from Phase 4 verification):**
- Currently empty quarantine (correct current state)
- Shows empty-state card with CLI hint chip (not a blank string)
- Promote button triggers approval flow

**v2 visual targets (R18):**
- Intake item cards have glass background + teal border on hover
- Promoted trust badge (`ts-promoted`) shows teal (not green)

**Tests:**
- [ ] Loads with structured empty-state card (not blank)
- [ ] Empty-state includes a CLI hint chip (e.g., `chaseos capture file ...`)
- [ ] **v2 — When items present:** item cards have glass background + teal hover border
- [ ] **v2 — Promoted badge** shows teal text + teal bg tint (not green)

**API calls used:** `get_dashboard()` (quarantine panel within dashboard)

---

#### 10. Agent Bus (`bus`)

**Nav label:** Agent Bus | **State:** Read-only  
**Version:** v2 (task/heartbeat cards glass; done badge teal; hb-ok health teal; state-ready teal border; section panels glass)

**What should happen:**
- Shows open tasks, heartbeats, and recent events from the Agent Bus SQLite store
- Hermes and OpenClaw heartbeats visible when running

**v2 visual targets (R18):**
- Task cards and heartbeat cards have glass background
- **"Done" badge** is teal (not green)
- **Heartbeat OK health label** is teal (not green)
- **"Ready" state** card border is teal tint (not green tint)
- Bus section panels (context/readiness/feature/queue/heartbeat/event) have glass backdrop-filter

**Tests:**
- [ ] Panel loads with bus data (not blank)
- [ ] Heartbeat freshness shown per runtime
- [ ] Task list shows recent tasks (or empty-state if none)
- [ ] **v2 — Task cards** have glass background (semi-transparent over page bg)
- [ ] **v2 — Heartbeat cards** have glass background
- [ ] **v2 — "Done" task badge** shows teal (not green)
- [ ] **v2 — Heartbeat OK health label** shows teal text (not green)
- [ ] **v2 — Bus section panels** have glass depth (backdrop-filter blur)

**API calls used:** `get_dashboard()` (bus panel), potentially direct bus inspection

---

#### 11. Memory Manager (`runtime-memory-inspector`)

**Nav label:** Memory Manager | **State:** Read-only

**What should happen:**
- Lists registered runtimes (archon, hermes, openclaw)
- Click runtime → 5-section summary: profile / identity_ledger / nav_map / scorecard / repair
- Read-only — no edit controls

**Tests:**
- [ ] Runtime list loads
- [ ] Clicking archon shows profile data
- [ ] All 5 sections render with data
- [ ] No write controls visible

**API calls used:** `get_memory_summary()`

---

#### 12. Sources / Acquisition (`acquisition`)

**Nav label:** Sources | **State:** Approval-gated  
**Version:** v2 (source/run cards glass + teal hover; success badges teal; msg-ok teal)

**What should happen (from Phase 4 verification):**
- Currently empty (correct current state — no acquisitions run yet)
- Shows structured empty-state with acquisition readiness status

**v2 visual targets (R18):**
- Source cards and run cards have glass background
- Run cards show teal border on hover
- Success/succeeded badges are teal (not green)
- Success message text is teal (not green)

**Tests:**
- [ ] Loads with structured empty-state (not blank string)
- [ ] Acquisition readiness chips visible
- [ ] **v2 — When runs present:** run cards have glass background + teal hover border
- [ ] **v2 — Success badge** shows teal (not green) for succeeded acquisitions
- [ ] **v2 — Success message text** is teal (not green)

**API calls used:** `get_acquisition_staging_model()`

---

#### 13. History / Audit (`build-logs`)

**Nav label:** History / Audit | **State:** Read-only  
**Version:** v2 (build-log-item teal active state, rounded 8px)

**What should happen:**
- Lists build logs from `07_LOGS/Build-Logs/` and agent activity from `07_LOGS/Agent-Activity/`
- Each entry shows filename and date
- Click to read content in node inspector

**v2 visual targets (R15):**
- Build log items: `border-radius: 8px`; teal border on hover; active item has teal border + subtle teal bg tint (replacing the flat blue accent)

**Tests:**
- [ ] Panel loads with log list
- [ ] Entries appear (there are many build logs)
- [ ] **v2 — Active item** shows teal border + subtle teal bg tint
- [ ] **v2 — Hover** shows teal border tint
- [ ] Click entry → inspector opens with content

---

#### 14. Settings (`settings`)

**Nav label:** Settings | **State:** Read-only

**What should happen:**
- 6-tab settings form: Appearance / Graph / Provider / Config / Presets / Debug
- No destructive controls — settings are observability-first
- Panel scrolls (one of 3 allowed-to-scroll panels)

**Tests:**
- [ ] Panel loads with settings tabs
- [ ] All 6 tabs clickable and render content
- [ ] Vertical scroll works on this panel

**API calls used:** `get_config_summary()`, `get_graph_settings()`

---

#### 15. Graph Hygiene (`graph-hygiene`)

**Nav label:** Graph Hygiene | **State:** Approval-gated

**What should happen:**
- Reads `07_LOGS/Maintain-Runs/` and `07_LOGS/Graph-Reports/`
- Shows hygiene debt, loose nodes, duplicates
- "Review required" state → dashboard alert appears
- Draft workflow: create decision draft → approve → execute (all gated)
- Dashboard alert card shows `operator_next_action` when review required

**Tests:**
- [ ] Panel loads hygiene data or structured empty-state
- [ ] Draft creation modal opens
- [ ] Dashboard shows hygiene alert when review is pending (if any)

**API calls used:** `get_graph_hygiene_review_panel()`, `get_drafts()`, `create_draft()`

---

#### 16. Provenance (`provenance-explorer`)

**Nav label:** Provenance | **State:** Read-only

**What should happen:**
- Shows origin trails for quarantine items
- Reads sidecar files and dedup registry
- Trust state derivation: promoted / scanned-clean / flagged / unscanned-quarantine

**Tests:**
- [ ] Panel loads with provenance list or empty-state
- [ ] Trust states displayed with correct visual treatment
- [ ] Dedup registry cross-reference shown

**API calls used:** `get_provenance()`

---

### TIER C — Reference / Dev Panels

---

#### 17. Workspaces (`project-workspace`)

**Nav label:** Workspaces | **State:** Read-only

**Tests:**
- [ ] Panel loads with workspace/project list
- [ ] Project details accessible

---

#### 18. Missions / Workflow Packs (`workflow-packs`)

**Nav label:** Missions | **State:** Approval-gated

**Tests:**
- [ ] Panel loads (workflow pack list or structured empty-state)

---

#### 19. Extensions / Chaser Forge (`chaser-forge`)

**Nav label:** Extensions | **State:** Approval-gated

**Tests:**
- [ ] Panel loads (empty-state expected — not implemented yet)

---

#### 20. Capture (`capture-markdown`)

**Nav label:** Capture | **State:** Approval-gated

**What should happen:**
- Text area for pasting source content
- Preview renders Markdown before save
- Save writes to raw quarantine only (no vault mutation)

**Tests:**
- [ ] Input area accepts text
- [ ] Preview renders
- [ ] Save writes to quarantine (verify `03_INPUTS/00_QUARANTINE/`)

---

#### 21. Research Collections (`sic`)

**Nav label:** Research Collections | **State:** Read-only

**Tests:**
- [ ] Panel loads SIC workspace list
- [ ] Click workspace → detail renders

**API calls used:** `get_sic_workspaces()`

---

#### 22. Review Queue (`pulse-enqueue`)

**Nav label:** Review Queue | **State:** Read-only

**Tests:**
- [ ] Loads Pulse candidates list or structured empty-state
- [ ] Enqueue pipeline status visible

**API calls used:** `get_pulse_summary()`

---

#### 23. Proactive Briefings (`pulse-schedule-proof`)

**Nav label:** Proactive Briefings | **State:** Read-only

**Tests:**
- [ ] Loads SBP schedule summary and deck list or empty-state

**API calls used:** `get_pulse_summary()`

---

#### 24. Decisions (`decision-ledger`)

**Nav label:** Decisions | **State:** Read-only

**Tests:**
- [ ] Decision ledger entries load (seed entries exist in `07_LOGS/Decision-Ledger/`)
- [ ] Pivot log entries accessible

---

#### 25. Memory Ledger (`memory-ledger`)

**Nav label:** Memory Ledger | **State:** Read-only

**Tests:**
- [ ] Loads ledger entries or empty-state
- [ ] Trust states visible

---

#### 26. Context Import (`context-import`)

**Nav label:** Context Import | **State:** Approval-gated

**Tests:**
- [ ] Import form loads
- [ ] Preview works
- [ ] Approve path fires approval gate

---

#### 27. Browser Runtime (`browser-runtime`)

**Nav label:** Browser Runtime | **State:** Read-only (Advanced)

**Note:** PARKED — readiness state only. No browser control.

**Tests:**
- [ ] Panel loads with readiness status (not error)

---

#### 28. Site Skills (`siteops`)

**Nav label:** Site Skills | **State:** Read-only (Advanced)

**Tests:**
- [ ] Panel loads siteops run records or structured empty-state

**API calls used:** `get_siteops_summary()`

---

#### 29. Runtime Navigation (`runtime-navigation`)

**Nav label:** Runtime Navigation | **State:** Read-only (Advanced)

**Tests:**
- [ ] Panel loads RNM data for registered runtimes

---

#### 30. Agent Identity (`agent-identity`)

**Nav label:** Agent Identity | **State:** Read-only (Advanced)

**Tests:**
- [ ] Panel loads identity ledger summary

---

#### 31. Support Loops (`runtime-support-loops`)

**Nav label:** Support Loops | **State:** Read-only (Advanced)

**Tests:**
- [ ] Panel loads repair patterns and incident candidates or empty-state

---

#### 32. Quality Review (`qa-proof`)

**Nav label:** Quality Review | **State:** Read-only (Advanced)

**Tests:**
- [ ] Panel loads QA surface reference
- [ ] No test execution triggered from UI

---

#### 33. Feature Audit (`feature-filter`)

**Nav label:** Feature Audit | **State:** Read-only (Advanced)

**What should happen:**
- Two tabs: Task Types (searchable) + Filter SOP text
- Reads `04_SOPS/Feature-Filter-SOP.md` + `runtime/aor/task_type_table.yaml`

**Tests:**
- [ ] Both tabs render content
- [ ] Task type search works

**API calls used:** `get_feature_filter()`

---

#### 34. Workflow Registry (`workflow-registry`)

**Nav label:** Workflow Registry | **State:** Read-only (Advanced)

**What should happen:**
- Lists all workflow manifests from `runtime/workflows/registry/*.yaml`
- Search/filter by status
- Click → manifest detail viewer

**Tests:**
- [ ] Workflow list loads (several manifests exist)
- [ ] Search filters work
- [ ] Manifest detail renders on click

**API calls used:** `get_workflow_registry()`

---

#### 35. Role Cards (`role-cards`)

**Nav label:** Role Cards | **State:** Read-only (Advanced)

**Tests:**
- [ ] Role card list loads from `06_AGENTS/role-cards/`
- [ ] Card detail renders on click

---

#### 36. Pivot Log (`pivot-log`)

**Nav label:** Pivot Log | **State:** Read-only (Advanced)

**Tests:**
- [ ] Pivot log entries load (seed entries exist in `07_LOGS/Pivot-Log/`)

---

#### 37. App Launcher (`app-launcher`)

**Nav label:** App Launcher | **State:** Read-only (Advanced)

**Tests:**
- [ ] Surface discovery index loads
- [ ] All panels listed with status

---

#### 38. Workspace Entry (`workspace-entry`)

**Nav label:** Workspace Entry | **State:** Read-only (Advanced)

**Tests:**
- [ ] Bootstrap and vault detection status shown
- [ ] Current vault root displayed correctly

---

#### 39. Studio Status (`studio-status`) ⚠️ NEW

**Nav label:** Studio Status | **State:** Read-only (Advanced)  
**Added:** 2026-05-27 — requires restart to verify

**What should happen:**
- Under Advanced (Governance) sidebar section
- Loads via `get_studio_status()` which wraps `get_dashboard()` product + VentureOps panels
- Shows: product build grade, evidence paths, VentureOps readiness, release lanes (collapsible)
- Panel is allowed to scroll (Studio Status is an exception to the no-scroll rule)

**Tests:**
- [ ] Button appears in Advanced section
- [ ] Clicking loads Studio Status panel (not an error state)
- [ ] Product metrics section renders
- [ ] VentureOps section renders
- [ ] Panel scrolls when content is long

**API calls used:** `get_studio_status()` → `get_dashboard()`

---

## Global UI / Chrome Tests

These apply to the shell as a whole, not a specific panel:

#### Topbar
- [ ] Logo and vault name shown in topbar-left
- [ ] Approvals count chip updates when approvals exist
- [ ] Review count chip updates
- [ ] Runs count chip updates
- [ ] Command search input focuses on click
- [ ] `?` feature guide button opens feature guide panel/overlay
- [ ] Settings gear button navigates to settings panel

#### Sidebar
- [ ] Collapse/expand toggle works (sidebar hides, main panel expands)
- [ ] Collapsed state persists on panel switch
- [ ] Keyboard shortcuts 1–8 navigate to correct panels
- [ ] Keyboard shortcut `/` focuses graph search
- [ ] Advanced sections expand/collapse
- [ ] Coming-soon buttons are visually disabled (grayed out, not clickable)

#### Tray Icon ⚠️ Requires restart
- [ ] System tray shows C-kernel icon (teal arc, violet dots — NOT blue hexagon)
- [ ] Windows taskbar shows same C-kernel icon
- [ ] Tray tooltip shows `ChaseOS Studio — chaseos_obsidian`
- [ ] Right-click tray → menu shows "Show ChaseOS Studio", "Quit ChaseOS Studio", status line
- [ ] Closing window (X button) hides to tray (does NOT quit)
- [ ] Double-click tray icon restores window
- [ ] "Quit" in tray menu exits cleanly

#### Right Object Inspector
- [ ] Inspector collapses when clicking the collapse button
- [ ] Node click in graph triggers inspector content update
- [ ] Inspector posture note changes per panel (where configured)

#### Loading Overlay
- [ ] Startup overlay shows `ChaseOS Studio` with spinner
- [ ] Overlay disappears when bridge is ready (usually < 2 seconds)

---

## API Methods Reference

Key `StudioAPI` methods. If a panel fails, check whether the underlying API call returns `ok: true`.

```python
# Test from Python (with vault root set):
from runtime.studio.shell.api import StudioAPI
from pathlib import Path
api = StudioAPI(vault_root=Path("C:/Users/chaseos/Documents/chaseos_obsidian"))

api.get_dashboard()           # Home, Approvals, Bus, Intake
api.get_now_md_summary()      # Home Now.md strip
api.get_studio_status()       # Studio Status panel
api.get_graph_contract()      # Graph nodes + links
api.get_node("NodeName")      # Node detail for inspector
api.get_node_full_content("path/to/file.md")  # Raw content for inspector
api.get_approval_queue()      # Approval center
api.get_runtime_cockpit_status()  # Runtime cockpit
api.get_aor_summary()         # Tasks & Runs
api.get_schedule_summary()    # Schedules
api.get_sic_workspaces()      # Research Collections
api.get_pulse_summary()       # Pulse/Review Queue
api.get_memory_summary()      # Memory Manager
api.get_siteops_summary()     # Site Skills
api.get_graph_hygiene_review_panel()  # Graph Hygiene
api.get_workflow_registry()   # Workflow Registry
api.get_feature_filter()      # Feature Audit
api.get_graph_settings()      # Settings / graph config
api.get_config_summary()      # Settings / provider config
api.get_runtime_profiles()    # Home v2 runtime strip — reads runtime/memory/adapters/*/profile.json
```

---

## Running the Test Suite

The shell has a large dedicated test suite. Run before and after any fixes:

```powershell
# From vault root with venv active:
python -m pytest runtime/studio/shell/ -q

# Expected: 1426 passed, 1 skipped (as of last verified run 2026-05-18)
# If count differs significantly, investigate regressions before proceeding
```

---

## Priority Order for Testing Session

1. **Restart the app** — required for R1–R10 changes to take effect
2. **Home panel — layout (R1)** — confirm 5-row layout, no scroll
3. **Home panel — runtime strip v2 (R7)** — confirm profile-driven names; Hermes + OpenClaw show `24/7` badge; Archon shows session dot
4. **Home panel — ambient toggle (R5)** — confirm Off / Fog / Glow cycle; localStorage persistence; animations visible
5. **Home panel — companion mascot (R6)** — confirm C-kernel SVG visible; float animation; alert/happy state
6. **Home panel — launch icons + hover (R8)** — hover each button; check icon colour shift + lift effect + tooltip
7. **Home panel — activity cards v2 (R9)** — cards show icon badge + title + timestamp (not plain chips)
8. **No-scroll verification (R2)** — open each Tier A panel and verify no scrollbar
9. **Tray/taskbar icon (R3)** — confirm C-kernel design in system tray AND taskbar
10. **Studio Status panel (R4)** — confirm button visible and panel loads
11. **Graph panel v2 (R12)** — header glass, teal node-count chip, filter panel backdrop-filter, authority chip compactness
12. **Chat panel v2 (R11)** — segmented adapter control, runtime pulse dot, glass bubbles, teal send
13. **Standard Panels v2 (R13)** — panel header glass card; verify on Approvals first, then check Runtimes, Schedules, Tasks & Runs — all use `.panel-title-row`
14. **Content Panels v2 (R14)** — Runtime Cockpit cards teal live badge; Schedule cards teal enabled badge; AOR cards teal success badge
15. **Inspector & List v2 (R15)** — Docs/Inspector toolbar glass + active tab teal; History/Audit item teal active
16. **Misc Panel Cards v2 (R16)** — Memory Manager/RNM/Site Skills/Daemon glass + teal running; Settings tab active teal
17. **Tier C Panels v2 (R17)** — Decisions/Pivot Log teal hover; Role Cards teal active; Agent Identity glass cards + teal seeded badge; RNM teal seeded; Support Loops glass + teal hover; Provenance Explorer record cards glass + promoted teal; daemon running text teal
18. **All Tier A panels** — core operator loop must pass
19. **All Tier B panels** — important but not blocking
20. **Tier C panels** — best-effort verification

---

## File Locations for This Session's Changes

| File | Change | Verified? |
|------|--------|-----------|
| `runtime/studio/shell/frontend/styles.css` | No-scroll enforcement; Home CSS; Studio Status CSS; +340 lines Home v2 (ambient, companion, glass cards, runtime chip v2, launch hover, activity cards) | ❌ Needs restart |
| `runtime/studio/shell/frontend/app.js` | Home redesign functions; Studio Status panel load; Home v2 (Promise.all 3-fetch, profile data merge, `initAmbientToggle()`, `homeRuntimeChip()` v2, `homeLaunchBtn()` with icons+tooltips, `homeActivityCard()`, `homeCompanion()` C-kernel SVG) | ❌ Needs restart |
| `runtime/studio/shell/frontend/index.html` | Studio Status nav button + panel section; `#home-ambient` div (first child of `#panel-dashboard`) | ❌ Needs restart |
| `runtime/studio/shell/api.py` | `get_now_md_summary()` + `get_studio_status()` + `get_runtime_profiles()` (monkey-patched; reads `runtime/memory/adapters/*/profile.json`) | ❌ Needs restart |
| `runtime/studio/shell/frontend/styles.css` (Chat v2) | ~280 lines appended — `body.chat-page-active` scoped: segmented adapter control, teal pip, compact daemon, thread header pulse dot, glass message bubbles, glass composer, teal send button | ❌ Needs restart |
| `runtime/studio/shell/frontend/styles.css` (Graph v2) | ~140 lines appended — `#panel-graph` scoped: header glass (78% opacity, blur, teal top-border stripe), h2/description/authority chips compact, search glass+focus ring, filter panel backdrop-filter, `#graph-node-count` teal chip, legend dark glass, quality chip teal accent | ❌ Needs restart |
| `runtime/studio/shell/frontend/styles.css` (Standard Panels v2) | ~90 lines appended — global scope: `.panel-title-row` glass card (elevated bg + teal 2px top stripe + border + rounded); h2 15px; subtitle 11px muted; authority chips transparent 9px; `.approval-queue-item` glass + teal 3px left border + hover; `.approval-stat-pill:first-child` teal; approve/reject 8px radius; tech section glass | ❌ Needs restart |
| `runtime/studio/shell/frontend/styles.css` (Content Panels v2) | ~90 lines appended — global scope: `.rc-runtime-card` glass + teal hover + `rc-status-live` teal + `rc-bus-fresh` teal + `rc-tech-details` glass; `.schedules-card` glass + teal hover + `schedules-badge-enabled` teal + `schedules-stats-row` glass; `.aor-exec-card` glass + teal hover + `aor-badge-success` teal + `aor-stat-success` teal | ❌ Needs restart |
| `runtime/studio/shell/frontend/styles.css` (Inspector & List v2) | ~65 lines appended — global scope: `.node-inspector-toolbar` glass bg + teal 2px top stripe; h2 15px; description 11px muted; `.node-tab-strip` elevated bg; `.node-inspector-tab.active` teal 2px top border + teal text; inactive tab teal hover; `.build-log-item` rounded 8px + teal hover/active; `.decision-item--active` teal tint bg | ❌ Needs restart |
| `runtime/studio/shell/frontend/styles.css` (Misc Cards v2) | ~50 lines appended — global scope: `.ml-runtime-card`/`.rnm-runtime-card` glass; `.ml-status-complete` teal; `.siteops-run-card` glass + teal hover; `.daemon-runtime-card` glass + `.daemon-running` teal border; `.settings-tab-btn.active` teal text | ❌ Needs restart |
| `runtime/studio/shell/frontend/styles.css` (Tier C v2) | ~65 lines appended — global scope: `.decision-item`/`.pivot-item` teal hover left border; `.role-card-item--active` teal (from blue); `.ai-ledger-card` glass + `.ai-posture-seeded` teal (from green); `.rnm-status-seeded` teal (from blue); `.runtime-support-card` glass + teal hover; `.provenance-record-card` glass + `.provenance-trust-pill.ts-promoted` teal; `.daemon-runtime-status.status--running` teal (from green) | ❌ Needs restart |
| `runtime/studio/shell/tray.py` | C-kernel icon; `setWindowIcon()` for taskbar | ❌ Needs restart |

---

*Testing Handover Document — ChaseOS Studio*  
*Created: 2026-05-27 | Use this document to drive a dedicated testing/fix session.*
