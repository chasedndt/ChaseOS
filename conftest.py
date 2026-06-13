"""Repo-root pytest bootstrap for local ChaseOS test execution.

Ensures the repository root is importable when focused pytest slices are run
without an editable install or explicit PYTHONPATH=.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load .env into os.environ early so all test code sees the same credentials
# that the CLI sees via main() → load_chaseos_env(). Values are never printed.
from runtime.local_env import load_chaseos_env as _load_chaseos_env  # noqa: E402
_load_chaseos_env(ROOT)

_ORIGINAL_OS_MKDIR = os.mkdir


def _mkdir_with_windows_readable_acl(path, mode=0o777, *args, **kwargs):
    """Avoid unreadable pytest temp dirs on Windows Store Python builds."""

    if os.name == "nt" and mode == 0o700:
        mode = 0o777
    return _ORIGINAL_OS_MKDIR(path, mode, *args, **kwargs)


if os.name == "nt":
    os.mkdir = _mkdir_with_windows_readable_acl


def pytest_configure(config):
    """Keep pytest temp writes inside a repo-local writable directory."""

    if not getattr(config.option, "basetemp", None):
        base_root = ROOT / ".pytest_tmp_env"
        base_root.mkdir(parents=True, exist_ok=True)
        base = base_root / f"pytest-of-chaseos-{os.getpid()}"
        config.option.basetemp = str(base)
