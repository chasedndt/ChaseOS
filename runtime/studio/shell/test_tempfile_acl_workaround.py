"""Tests for the packaged shell Windows tempfile ACL workaround."""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile

from runtime.studio.shell import main as shell_main


def test_windows_safe_mkdtemp_workaround_creates_writable_cleanup_child(monkeypatch, tmp_path: Path) -> None:
    original_mkdtemp = tempfile.mkdtemp
    if hasattr(tempfile, "_chaseos_safe_mkdtemp_installed"):
        delattr(tempfile, "_chaseos_safe_mkdtemp_installed")
    monkeypatch.setattr(shell_main.sys, "platform", "win32")
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))

    try:
        shell_main._install_windows_safe_mkdtemp_workaround()
        created = Path(tempfile.mkdtemp(prefix="chaseos-test-", dir=str(tmp_path)))
        marker = created / "probe.txt"
        marker.write_text("ok", encoding="utf-8")
        marker.unlink()
        shutil.rmtree(created)

        assert created.exists() is False
    finally:
        tempfile.mkdtemp = original_mkdtemp
        if hasattr(tempfile, "_chaseos_safe_mkdtemp_installed"):
            delattr(tempfile, "_chaseos_safe_mkdtemp_installed")


def test_webview_storage_path_uses_bounded_env_override(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(shell_main.WEBVIEW2_USER_DATA_ENV, ".pytest_tmp_env/studio-webview2-test/user-data")

    selected = shell_main._resolve_webview_storage_path(tmp_path)

    assert selected == str((tmp_path / ".pytest_tmp_env/studio-webview2-test/user-data").resolve())
    assert Path(selected).is_dir()


def test_webview_storage_path_defaults_to_pywebview_private_mode(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv(shell_main.WEBVIEW2_USER_DATA_ENV, raising=False)

    assert shell_main._resolve_webview_storage_path(tmp_path) is None
