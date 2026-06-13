"""Tests for read-only Browser Use CLI validation preflight."""

from __future__ import annotations

import inspect
import io
import json
import shutil
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.browser_use_cli_validation as validation_module
import runtime.browser_runtime.env_config as env_config
import runtime.cli.main as main_mod
from runtime.browser_runtime.browser_use_cli_validation import (
    build_browser_use_cli_validation_status,
    main as validation_main,
)
from runtime.cli.main import cmd_operate_browser_browser_use_cli_preflight

_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_browser_use_cli_validation"


def _workspace_test_root(name: str) -> Path:
    root = _TMP_ROOT / name
    if root.exists():
        _remove_test_root(root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _remove_test_root(root: Path) -> None:
    resolved = root.resolve()
    if resolved.parent != _TMP_ROOT.resolve():
        raise AssertionError(f"refusing to remove unexpected path: {resolved}")
    shutil.rmtree(resolved, ignore_errors=True)
    try:
        _TMP_ROOT.rmdir()
    except OSError:
        pass


def _seed_wrapper_and_config(root: Path, *, unsafe_policy: bool = False) -> None:
    wrapper = root / "runtime" / "browser_runtime" / "adapters" / "browser_use_cli.py"
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    wrapper.write_text("# fail-closed wrapper placeholder\n", encoding="utf-8")
    config = root / "runtime" / "browser_runtime" / "config.yaml"
    config.write_text(
        "\n".join(
            [
                "enabled: false",
                "browser_profile_policy: throwaway_only",
                f"allow_real_profile: {'true' if unsafe_policy else 'false'}",
                "allow_credentials: false",
                "allow_shell_execution: false",
                "allow_cookie_export: false",
                "allow_browser_profile_sync: false",
                "allow_public_tunnel: false",
                "canonical_writeback: false",
                "automatic_skill_activation: false",
                "skill_generation: draft_only",
            ]
        ),
        encoding="utf-8",
    )


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _args(**kwargs) -> object:
    class Args:
        vault_root = None
        executable = ""
        from_env = False
        output_json = False

    args = Args()
    for key, value in kwargs.items():
        setattr(args, key, value)
    return args


def test_validation_module_does_not_import_or_call_live_surfaces() -> None:
    source = inspect.getsource(validation_module)
    forbidden_tokens = (
        "import subprocess",
        "subprocess.",
        "socket.",
        "requests.",
        "urllib.",
        "Popen",
        "write_text(",
        "mkdir(",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_missing_browser_use_cli_fails_closed_without_writes(monkeypatch) -> None:
    root = _workspace_test_root("missing_cli")
    try:
        _seed_wrapper_and_config(root)
        monkeypatch.setattr(validation_module.shutil, "which", lambda _: None)
        before = _snapshot(root)

        status = build_browser_use_cli_validation_status(
            root,
            generated_at="2026-05-02T03:00:00Z",
        )
        after = _snapshot(root)

        assert before == after
        assert status.status == "blocked_browser_use_cli_unavailable"
        assert status.executable_found is False
        assert status.ready_for_future_live_validation is False
        assert "browser_use_cli_executable_not_found" in status.blockers
        assert status.dependency_install_attempted is False
        assert status.browser_launch_attempted is False
        assert status.browser_use_cli_live_run_attempted is False
        assert status.real_profile_access_attempted is False
        assert status.credential_or_cookie_read_attempted is False
        assert status.canonical_writeback_attempted is False
    finally:
        _remove_test_root(root)


def test_found_browser_use_cli_reports_ready_but_no_live_run(monkeypatch) -> None:
    root = _workspace_test_root("found_cli")
    try:
        _seed_wrapper_and_config(root)
        monkeypatch.setattr(validation_module.shutil, "which", lambda _: r"C:\Tools\browser-use.exe")

        status = build_browser_use_cli_validation_status(
            root,
            generated_at="2026-05-02T03:01:00Z",
        )

        assert status.status == "ready_for_operator_authorized_live_validation_no_execution"
        assert status.executable_found is True
        assert status.executable_path == r"C:\Tools\browser-use.exe"
        assert status.ready_for_future_live_validation is True
        assert "browser_use_cli_live_validation_not_run" in status.blockers
        assert status.subprocess_probe_attempted is False
        assert status.browser_launch_attempted is False
        assert status.browser_use_cli_live_run_attempted is False
        assert status.real_profile_access_attempted is False
    finally:
        _remove_test_root(root)


def test_throwaway_policy_violation_blocks_future_validation(monkeypatch) -> None:
    root = _workspace_test_root("unsafe_policy")
    try:
        _seed_wrapper_and_config(root, unsafe_policy=True)
        monkeypatch.setattr(validation_module.shutil, "which", lambda _: r"C:\Tools\browser-use.exe")

        status = build_browser_use_cli_validation_status(root)
        finding = next(item for item in status.config_findings if item.key == "allow_real_profile")

        assert status.status == "blocked_policy_not_throwaway_only"
        assert status.ready_for_future_live_validation is False
        assert "browser_runtime_policy_not_throwaway_only" in status.blockers
        assert finding.observed == "true"
        assert finding.ok is False
        assert status.real_profile_access_attempted is False
    finally:
        _remove_test_root(root)


def test_cli_json_output_is_read_only(monkeypatch) -> None:
    root = _workspace_test_root("cli_json")
    try:
        _seed_wrapper_and_config(root)
        monkeypatch.setattr(validation_module.shutil, "which", lambda _: None)

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = validation_main(
                [
                    "--vault-root",
                    str(root),
                    "--json",
                ]
            )
        payload = json.loads(stdout.getvalue())

        assert exit_code == 0
        assert payload["status"] == "blocked_browser_use_cli_unavailable"
        assert payload["read_only"] is True
        assert payload["dependency_install_attempted"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["browser_use_cli_live_run_attempted"] is False
        assert payload["canonical_writeback_attempted"] is False
    finally:
        _remove_test_root(root)


def test_chaseos_preflight_command_blocks_missing_cli_without_invocation(monkeypatch, capsys) -> None:
    root = _workspace_test_root("chaseos_missing_cli")
    try:
        _seed_wrapper_and_config(root)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: root)
        monkeypatch.setattr(validation_module.shutil, "which", lambda _: None)

        exit_code = cmd_operate_browser_browser_use_cli_preflight(_args(output_json=True))
        payload = json.loads(capsys.readouterr().out)

        assert exit_code == 1
        assert payload["status"] == "blocked_browser_use_cli_unavailable"
        assert payload["executable_source"] == "default"
        assert payload["dependency_install_attempted"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["browser_use_cli_live_run_attempted"] is False
        assert payload["canonical_writeback_attempted"] is False
    finally:
        _remove_test_root(root)


def test_chaseos_preflight_command_reads_env_executable_without_invocation(monkeypatch, capsys) -> None:
    root = _workspace_test_root("chaseos_env_cli")
    try:
        _seed_wrapper_and_config(root)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: root)
        monkeypatch.setenv("CHASEOS_BROWSER_USE_CLI", "browser-use-test")
        monkeypatch.setattr(
            validation_module.shutil,
            "which",
            lambda executable: r"C:\Tools\browser-use-test.exe"
            if executable == "browser-use-test"
            else None,
        )

        exit_code = cmd_operate_browser_browser_use_cli_preflight(
            _args(from_env=True, output_json=True)
        )
        payload = json.loads(capsys.readouterr().out)

        assert exit_code == 0
        assert payload["status"] == "ready_for_operator_authorized_live_validation_no_execution"
        assert payload["executable"] == "browser-use-test"
        assert payload["executable_source"] == "CHASEOS_BROWSER_USE_CLI"
        assert payload["browser_use_cli_live_run_attempted"] is False
        assert payload["real_profile_access_attempted"] is False
    finally:
        _remove_test_root(root)


def test_chaseos_preflight_command_reads_user_env_when_process_env_empty(monkeypatch, capsys) -> None:
    root = _workspace_test_root("chaseos_user_env_cli")
    try:
        _seed_wrapper_and_config(root)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: root)
        monkeypatch.delenv("CHASEOS_BROWSER_USE_CLI", raising=False)
        monkeypatch.setattr(
            env_config,
            "_read_windows_user_env",
            lambda name: "browser-use-user-env" if name == "CHASEOS_BROWSER_USE_CLI" else "",
        )
        monkeypatch.setattr(
            validation_module.shutil,
            "which",
            lambda executable: r"C:\Tools\browser-use-user-env.exe"
            if executable == "browser-use-user-env"
            else None,
        )

        exit_code = cmd_operate_browser_browser_use_cli_preflight(
            _args(from_env=True, output_json=True)
        )
        payload = json.loads(capsys.readouterr().out)

        assert exit_code == 0
        assert payload["status"] == "ready_for_operator_authorized_live_validation_no_execution"
        assert payload["executable"] == "browser-use-user-env"
        assert payload["executable_source"] == "CHASEOS_BROWSER_USE_CLI"
        assert payload["executable_source_detail"] == "windows_user"
        assert payload["browser_use_cli_live_run_attempted"] is False
    finally:
        _remove_test_root(root)
