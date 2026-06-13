"""Tests for chaseos setup path — CLI accessibility via user PATH."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.setup_cli import cmd_path


def _args(
    vault_root: str | None = None,
    dry_run: bool = False,
    json_out: bool = False,
) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.vault_root = vault_root
    ns.dry_run = dry_run
    ns.json = json_out
    return ns


class TestCmdPathDryRun:
    def test_dry_run_reports_would_add(self, tmp_path, capsys):
        venv_scripts = tmp_path / ".venv" / "Scripts"
        venv_scripts.mkdir(parents=True)
        args = _args(vault_root=str(tmp_path), dry_run=True)
        rc = cmd_path(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "dry-run" in out.lower()
        assert str(venv_scripts.resolve()) in out

    def test_dry_run_json(self, tmp_path):
        venv_scripts = tmp_path / ".venv" / "Scripts"
        venv_scripts.mkdir(parents=True)
        args = _args(vault_root=str(tmp_path), dry_run=True, json_out=True)
        rc = cmd_path(args)
        assert rc == 0

    def test_dry_run_json_shape(self, tmp_path, capsys):
        venv_scripts = tmp_path / ".venv" / "Scripts"
        venv_scripts.mkdir(parents=True)
        args = _args(vault_root=str(tmp_path), dry_run=True, json_out=True)
        cmd_path(args)
        raw = capsys.readouterr().out
        data = json.loads(raw)
        inner = data.get("result", data)
        assert inner["ok"] is True
        assert inner["status"] == "dry_run"
        assert "would_add" in inner

    def test_dry_run_includes_already_on_process_path_flag(self, tmp_path, capsys):
        venv_scripts = tmp_path / ".venv" / "Scripts"
        venv_scripts.mkdir(parents=True)
        args = _args(vault_root=str(tmp_path), dry_run=True, json_out=True)
        cmd_path(args)
        raw = capsys.readouterr().out
        inner = json.loads(raw).get("result", json.loads(raw))
        assert "already_on_process_path" in inner


class TestCmdPathMissingVenv:
    def test_missing_venv_returns_nonzero(self, tmp_path, capsys):
        # tmp_path has no .venv
        args = _args(vault_root=str(tmp_path))
        rc = cmd_path(args)
        assert rc != 0

    def test_missing_venv_json_ok_false(self, tmp_path, capsys):
        args = _args(vault_root=str(tmp_path), json_out=True)
        cmd_path(args)
        raw = capsys.readouterr().out
        inner = json.loads(raw).get("result", json.loads(raw))
        assert inner["ok"] is False

    def test_missing_venv_error_message(self, tmp_path, capsys):
        args = _args(vault_root=str(tmp_path))
        cmd_path(args)
        out = capsys.readouterr().out
        assert "venv" in out.lower() or "error" in out.lower()


class TestCmdPathNonWindows:
    @pytest.mark.skipif(sys.platform == "win32", reason="non-Windows path only")
    def test_non_windows_prints_export_instruction(self, tmp_path, capsys):
        venv_scripts = tmp_path / ".venv" / "Scripts"
        venv_scripts.mkdir(parents=True)
        args = _args(vault_root=str(tmp_path))
        rc = cmd_path(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "export PATH" in out or "shell profile" in out

    @pytest.mark.skipif(sys.platform == "win32", reason="non-Windows path only")
    def test_non_windows_json_manual_status(self, tmp_path, capsys):
        venv_scripts = tmp_path / ".venv" / "Scripts"
        venv_scripts.mkdir(parents=True)
        args = _args(vault_root=str(tmp_path), json_out=True)
        cmd_path(args)
        raw = capsys.readouterr().out
        inner = json.loads(raw).get("result", json.loads(raw))
        assert inner["ok"] is True
        assert "manual" in inner.get("status", "")


class TestCmdPathWindows:
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
    def test_windows_dry_run_does_not_call_powershell(self, tmp_path):
        venv_scripts = tmp_path / ".venv" / "Scripts"
        venv_scripts.mkdir(parents=True)
        args = _args(vault_root=str(tmp_path), dry_run=True)
        with patch("subprocess.run") as mock_run:
            rc = cmd_path(args)
            assert rc == 0
            mock_run.assert_not_called()

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
    def test_windows_calls_powershell_to_set_path(self, tmp_path, capsys):
        venv_scripts = tmp_path / ".venv" / "Scripts"
        venv_scripts.mkdir(parents=True)
        args = _args(vault_root=str(tmp_path))
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "added"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            rc = cmd_path(args)
            assert rc == 0
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "powershell" in call_args[0].lower()

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
    def test_windows_already_present_status(self, tmp_path, capsys):
        venv_scripts = tmp_path / ".venv" / "Scripts"
        venv_scripts.mkdir(parents=True)
        args = _args(vault_root=str(tmp_path), json_out=True)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "already_present"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            cmd_path(args)
            raw = capsys.readouterr().out
            inner = json.loads(raw).get("result", json.loads(raw))
            assert inner["status"] == "already_present"

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
    def test_windows_powershell_failure_returns_nonzero(self, tmp_path, capsys):
        venv_scripts = tmp_path / ".venv" / "Scripts"
        venv_scripts.mkdir(parents=True)
        args = _args(vault_root=str(tmp_path))
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Access denied"
        with patch("subprocess.run", return_value=mock_result):
            rc = cmd_path(args)
            assert rc != 0

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
    def test_windows_added_output_includes_note(self, tmp_path, capsys):
        venv_scripts = tmp_path / ".venv" / "Scripts"
        venv_scripts.mkdir(parents=True)
        args = _args(vault_root=str(tmp_path))
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "added"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            cmd_path(args)
            out = capsys.readouterr().out
            assert "terminal" in out.lower() or "chaseos" in out.lower()


class TestCmdPathCLIRegistration:
    def test_setup_path_registered_in_main_cli(self):
        import runtime.cli.main as m
        import argparse
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        m._add_setup_subcommands(sub)
        args = parser.parse_args(["setup", "path", "--dry-run"])
        assert hasattr(args, "func")
        assert args.dry_run is True

    def test_setup_path_func_is_cmd_path(self):
        import runtime.cli.main as m
        import argparse
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        m._add_setup_subcommands(sub)
        args = parser.parse_args(["setup", "path", "--dry-run"])
        from runtime.setup_cli import cmd_path
        assert args.func is cmd_path

    def test_setup_help_lists_path(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "runtime.cli.main", "setup", "--help"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parents[2])
        )
        assert "path" in result.stdout
