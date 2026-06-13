---
type: documentation
created: 2026-05-15
updated: 2026-05-15
---

# 🖥️ ChaseOS Dashboards and Interfaces

> **A canonical inventory of all local, operator-facing interactive surfaces within the ChaseOS ecosystem.**
> This file serves as the directory for all local read-only, mutating, and agent-controlled dashboards to ensure visibility for operators.

---

## 1. Primary Product Surfaces

These are the two active ChaseOS product surfaces. All functionality lives in one of these two; standalone micro-app ports have been consolidated.

* **[[ChaseOS-Studio-Architecture|Native ChaseOS Studio Desktop App]] (The Master Controller)**
    *Use Case:* This is the actual product. Run this for full control and operation of ChaseOS.
    *Context:* Opens a dedicated PyWebView desktop window with all functionality unified in a single tabbed interface. All write-capable actions (approvals, acquisition, memory management, runtime controls) route through governed panels here.
    *Command:* `chaseos studio shell`
    *Authority:* Full Control (governed write surface over all backend modules)

* **ChaseOS Web QA Harness (`8772`) (Read-Only Browser Fallback)**
    *Use Case:* Run this when you want a browser-based status view without the desktop app open.
    *Context:* A read-only browser version of the Studio shell. Shows system status, agent health, pending approval counts, and schedule state. Does not allow writes.
    *Command:* `chaseos studio desktop-shell-app`
    *Authority:* Read-only

> **Note:** The standalone KPI Dashboard (port 8768) and App Directory (port 8769) have been removed. KPI health data is now in the desktop shell Dashboard panel. The app directory is in the desktop shell App Launcher panel.

---

## 2. Agent Control & Execution Dashboards

These dashboards belong to the autonomous runtimes processing events, coordinating, and executing complex workflows. See [[Runtime-InterAgent-Coordination-Bus]] for more details.

* **[[OpenClaw-Runtime-Profile|OpenClaw]] Dashboard / Execution Plane (`5678`)**
    The core n8n execution environment for the OpenClaw runtime. This interface visualizes all autonomous node executions, workflow layouts, and provider bindings.
    *Local URL:* `http://127.0.0.1:5678/`

* **[[Hermes-Runtime-Profile|Hermes]] Kanban Dashboard (`9119`)**
    The Hermes dashboard and Kanban board surface for active queue coordination, task tracking, and agent-bus lifecycle visualization.
    *Local URL:* `http://127.0.0.1:9119/`

---

## 3. Targeted Control Panels (Pending Migration → Desktop Shell)

These standalone apps have write-capable functionality not yet present in the desktop shell. They remain active while their write paths are being migrated into `shell/api.py` and the corresponding desktop shell panels. Once migrated, each port will be deleted.

| Port | App | Migration Target | Status |
|------|-----|-----------------|--------|
| 8765 | Acquisition Cockpit | Desktop shell Acquisition panel | Pending migration |
| 8766 | Runtime Startup Controls | Desktop shell Runtime Cockpit panel | Pending migration |
| 8767 | Pulse Deck | Desktop shell Pulse panels | Pending migration |
| 8774 | Personal Memory Manager | Desktop shell Memory Manager panel | Pending migration |

> **Removed (Phase 1):** Ports 8768 (KPI Dashboard), 8769 (App Launcher), 8770 (Product UI Test Target), 8771 (Runtime Cockpit), 8773 (Approval Center) — functionality covered by desktop shell panels.

---

## 4. Diagnostics & External Tool Ports

Reference ports for external tools and diagnostic contexts. These are not started by ChaseOS — they are opened by external processes when active.

* **Browser/Runtime Local Target (`4173`)**
    Common Vite/browser-runtime preview target port used by local proof runs.

* **Static Artifact Server (`8781`)**
    Local static artifact server used for Studio proof files and screenshots.

* **Chrome CDP (`9222`)**
    Chrome DevTools Protocol endpoint active if Chromium was launched for browser proofing.

* **Excalidraw/Canvas Loopback (`3002`)**
    Optional loopback used for visual and canvas-based experiments.

* **Ollama Local Models (`11434`)**
    Ollama API endpoint active when local model serving is running.

---

*Graph links: [[00_HOME/Dashboard|Dashboard]] · [[Agent-Registry]] · [[Tool-Map]] · [[ChaseOS-Studio-Architecture]]*
