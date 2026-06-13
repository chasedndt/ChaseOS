# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the native ChaseOS Studio shell.

Updated: 2026-05-05 — added 10D/10E hidden imports
  (file_watcher, workspace_import_flow, project_workspace_view, runtime_status_pill)
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


ROOT = Path.cwd()
FRONTEND = ROOT / "runtime" / "studio" / "shell" / "frontend"
RECOVERY = ROOT / "runtime" / "studio" / "recovery"

HIDDEN = collect_submodules("webview") + [
    # ── Studio shell ─────────────────────────────────────────────────────
    "runtime.studio.shell.config",
    "runtime.studio.shell.api",
    "runtime.studio.shell.panel_registry",
    "runtime.studio.shell.file_watcher",
    "runtime.studio.shell.workspace_import_flow",
    "runtime.studio.shell.write_surface",
    "runtime.studio.shell.graph_style_registry",
    "runtime.studio.shell.graph_settings",
    "runtime.studio.shell.graph_presets",
    # ── Studio backend ───────────────────────────────────────────────────
    "runtime.studio.service",
    "runtime.studio.graph_view",
    "runtime.studio.graph_view_contract",
    "runtime.studio.graph_index_contract",
    "runtime.studio.node_inspector_contract",
    "runtime.studio.dashboard",
    "runtime.studio.provenance",
    "runtime.studio.memory_inspector",
    "runtime.studio.sic_workspace_browser",
    "runtime.studio.aor_pipeline_monitor",
    "runtime.studio.schedule_inspector",
    "runtime.studio.pulse_inspector",
    "runtime.studio.siteops_inspector",
    "runtime.studio.runtime_cockpit",
    "runtime.studio.approval_queue_panel",
    "runtime.studio.open_folder_readiness",
    "runtime.studio.project_workspace_view",
    "runtime.studio.runtime_status_pill",
    "runtime.studio.packaging_readiness",
    "runtime.studio.installer_plan",
    # ── Runtime deps ─────────────────────────────────────────────────────
    "runtime.agent_bus.bus",
    "runtime.agent_bus.backends.sqlite_backend",
    "runtime.aor.engine",
    "runtime.aor.registry",
    "runtime.aor.role_cards",
    "runtime.schedules.loader",
    "runtime.context.boot",
    "runtime.memory.growth",
    "runtime.pulse.candidate_inspector",
    "runtime.pulse.bus_review_response_ingest",
    "watchdog.observers",
    "watchdog.events",
]

a = Analysis(
    [str(ROOT / "runtime" / "studio" / "shell" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(FRONTEND), "studio_frontend"),
        (str(RECOVERY), "runtime/studio/recovery"),
    ],
    hiddenimports=HIDDEN,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ChaseOS-Studio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ChaseOS-Studio",
)
