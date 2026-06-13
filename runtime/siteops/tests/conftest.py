from __future__ import annotations

import shutil
import time
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]


def _remove_tmp_vault(path: Path) -> None:
    for _attempt in range(3):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            time.sleep(0.1)
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture()
def siteops_vault(request: pytest.FixtureRequest) -> Path:
    base = ROOT / "runtime" / "siteops" / "_tmp_tests"
    vault = base / uuid.uuid4().hex[:8]
    if vault.exists():
        shutil.rmtree(vault)
    for name in ("catalog", "tenants"):
        shutil.copytree(
            ROOT / "runtime" / "siteops" / name,
            vault / "runtime" / "siteops" / name,
        )
    try:
        yield vault
    finally:
        if vault.exists():
            _remove_tmp_vault(vault)
