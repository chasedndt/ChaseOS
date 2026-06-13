# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller scaffold for the future ChaseOS installer/update lane.

This spec is source-only in the current pass. It is not executed by Settings or
by the updater readiness proofs.
"""

from pathlib import Path


project_root = Path.cwd()
entrypoint = project_root / "runtime" / "studio" / "launcher_update_installer_cli.py"

a = Analysis(
    [str(entrypoint)],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "runtime.studio.launcher_update_helper",
        "runtime.studio.launcher_update_check",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ChaseOS-Installer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
