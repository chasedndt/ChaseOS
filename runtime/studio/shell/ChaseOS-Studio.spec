# ChaseOS-Studio.spec
# PyInstaller spec for ChaseOS Studio standalone desktop shell (.exe)
#
# Backend: PyQt6 + PyQt6-WebEngine (WinForms/pythonnet unavailable on Python 3.14.x)
# PYWEBVIEW_GUI=qt is set in main.py before webview import.
#
# Build:  pyinstaller runtime/studio/shell/ChaseOS-Studio.spec
#         (or use build_exe.ps1 which handles venv activation)
#
# Usage:  ChaseOS-Studio.exe [--vault-root "C:\path\to\vault"] [--dev]
#   If --vault-root is omitted the last used vault is recalled from
#   %USERPROFILE%\.chaseos\studio\window-state.json.

import sys
import os
from pathlib import Path

block_cipher = None

# SPECPATH = directory containing this .spec file = <vault>/runtime/studio/shell/
# VAULT_ROOT = three levels up from the spec file
_SPEC_DIR = Path(SPECPATH)          # noqa: F821  (SPECPATH is PyInstaller built-in)
_VAULT_ROOT = _SPEC_DIR.parents[2]  # <vault>/runtime/studio/shell/ → <vault>/

# ── Collect all runtime.* submodules so nothing is missed ────────────────────
from PyInstaller.utils.hooks import collect_submodules, collect_data_files


def _without_test_modules(module_names):
    test_parts = {'test', 'tests', 'testing'}
    filtered = []
    for name in module_names:
        parts = name.split('.')
        if any(part in test_parts or part.startswith('test_') for part in parts):
            continue
        filtered.append(name)
    return filtered


runtime_hidden = _without_test_modules(collect_submodules('runtime'))
pywebview_hidden = _without_test_modules(collect_submodules('webview'))

# Keep the Qt bundle scoped to the backend Studio actually uses. Collecting
# every PyQt6 submodule pulls in optional Bluetooth/DBus/QAx stacks and makes
# packaging fragile on this host.
pyqt6_hidden = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtWebEngineCore',
    'PyQt6.QtWebChannel',
    'PyQt6.QtNetwork',
    'PyQt6.QtPrintSupport',
    'PyQt6.QtOpenGL',
    'PyQt6.QtOpenGLWidgets',
]
qtpy_hidden = [
    'qtpy',
    'qtpy.QtCore',
    'qtpy.QtGui',
    'qtpy.QtWidgets',
    'qtpy.QtWebEngineWidgets',
    'qtpy.QtWebEngineCore',
    'qtpy.QtWebChannel',
    'qtpy.QtNetwork',
    'qtpy.QtPrintSupport',
]

a = Analysis(
    [str(_SPEC_DIR / 'main.py')],
    pathex=[str(_VAULT_ROOT)],
    binaries=[],
    datas=[
        # Bundle the frontend under 'studio_frontend' — matches frontend_dir() MEIPASS lookup
        (str(_SPEC_DIR / 'frontend'), 'studio_frontend'),
        # Recovered Studio API bytecode is loaded by runtime.studio.shell.api at startup.
        (str(_VAULT_ROOT / 'runtime' / 'studio' / 'recovery'), 'runtime/studio/recovery'),
        # PyWebView needs its own data files (JS bridge, platform shims)
        *collect_data_files('webview'),
        # PyQt6 / WebEngine binaries and data are collected by PyInstaller's
        # Qt hooks for the explicit Qt modules above. Avoid bundling every
        # optional PyQt6 plugin/QML asset here; that made the one-file PKG
        # stage unstable on this host.
    ],
    hiddenimports=[
        *runtime_hidden,
        *pywebview_hidden,
        *pyqt6_hidden,
        *qtpy_hidden,
        # PyWebView Qt platform backend
        'webview.platforms.qt',
        # Qt WebEngine — required for HTML rendering in pywebview Qt mode
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebChannel',
        'PyQt6.QtNetwork',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        # Optional local Windows optical character recognition engine.
        'winrt.windows.foundation',
        'winrt.windows.foundation.collections',
        'winrt.windows.globalization',
        'winrt.windows.graphics.imaging',
        'winrt.windows.media.ocr',
        'winrt.windows.storage',
        'winrt.windows.storage.streams',
        # stdlib modules sometimes missed by the static scanner
        'sqlite3',
        'json',
        'pathlib',
        'importlib.resources',
        'importlib.metadata',
        'email.mime.text',
        'email.mime.multipart',
        'xml.etree.ElementTree',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        '_tkinter', 'tkinter',
        'matplotlib', 'numpy', 'scipy',
        'PyQt5', 'PySide2', 'PySide6',
        'IPython', 'notebook', 'jupyter',
        'test', 'tests', 'testing',
        # Exclude WinForms backend — not available without pythonnet
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ChaseOS-Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['webview2loader.dll'],
    runtime_tmpdir=None,
    console=False,          # no console window in production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # TODO: add assets/icon.ico when artwork is ready
    version_file=None,
)
