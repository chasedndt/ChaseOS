"""Tests for bounded external Browser Use CLI validation."""

from __future__ import annotations

import io
import json
import shutil
import subprocess
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.browser_use_cli_external_validation as external_validation
from runtime.browser_runtime.browser_use_cli_external_validation import (
    STATUS_BLOCKED_PREFLIGHT,
    STATUS_COMPLETE_HELP_PROBE,
    STATUS_FAILED_HELP_PROBE,
    STATUS_READY_NO_EXECUTION,
    build_browser_use_cli_external_validation,
    main as external_validation_main,
    write_browser_use_cli_external_validation_evidence,
)

_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_browser_use_cli_external_validation"


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


def _seed_wrapper_and_config(root: Path) -> None:
    wrapper = root / "runtime" / "browser_runtime" / "adapters" / "browser_use_cli.py"
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    wrapper.write_text("# fail-closed wrapper placeholder\n", encoding="utf-8")
    config = root / "runtime" / "browser_runtime" / "config.yaml"
    config.write_text(
        "\n".join(
            [
                "enabled: false",
                "browser_profile_policy: throwaway_only",
                "allow_real_profile: false",
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


def _completed(stdout: str = "Browser automation CLI\nopen click extract cookies tunnel profile") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(["browser-use", "--help"], 0, stdout=stdout, stderr="")


def test_missing_cli_blocks_before_help_probe(monkeypatch) -> None:
    root = _workspace_test_root("missing_cli")
    try:
        _seed_wrapper_and_config(root)
        monkeypatch.setattr(
            external_validation,
            "_run_help_probe",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not probe")),
        )

        report = build_browser_use_cli_external_validation(
            root,
            executable="missing-browser-use",
            generated_at="2026-05-05T15:00:00Z",
            execute_help_probe=True,
        )
        payload = report.to_dict()

        assert payload["status"] == STATUS_BLOCKED_PREFLIGHT
        assert payload["help_probe_attempted"] is False
        assert "preflight:browser_use_cli_executable_not_found" in payload["blockers"]
        assert payload["browser_launch_attempted"] is False
        assert payload["browser_command_execution_attempted"] is False
        assert payload["canonical_writeback_attempted"] is False
    finally:
        _remove_test_root(root)


def test_ready_without_execution_keeps_help_probe_blocker(monkeypatch) -> None:
    root = _workspace_test_root("ready_no_execution")
    try:
        _seed_wrapper_and_config(root)
        monkeypatch.setattr(
            external_validation,
            "_run_help_probe",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not probe")),
        )

        report = build_browser_use_cli_external_validation(
            root,
            executable="python",
            generated_at="2026-05-05T15:05:00Z",
            execute_help_probe=False,
        )

        assert report.status == STATUS_READY_NO_EXECUTION
        assert report.help_probe_attempted is False
        assert "browser_use_cli_external_help_probe_not_run" in report.blockers
        assert report.subprocess_probe_attempted is False
    finally:
        _remove_test_root(root)


def test_help_probe_success_does_not_grant_browser_authority(monkeypatch) -> None:
    root = _workspace_test_root("help_probe_success")
    try:
        _seed_wrapper_and_config(root)
        monkeypatch.setattr(
            external_validation.subprocess,
            "run",
            lambda *_args, **_kwargs: _completed(),
        )

        report = build_browser_use_cli_external_validation(
            root,
            executable="python",
            generated_at="2026-05-05T15:10:00Z",
            execute_help_probe=True,
        )
        payload = report.to_dict()

        assert payload["status"] == STATUS_COMPLETE_HELP_PROBE
        assert payload["help_probe_attempted"] is True
        assert payload["subprocess_probe_attempted"] is True
        assert payload["expected_help_surface_present"] is True
        assert "open" in payload["observed_command_tokens"]
        assert "cookies" in payload["observed_command_tokens"]
        assert payload["blockers"] == []
        assert payload["browser_command_execution_attempted"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["real_profile_access_attempted"] is False
        assert payload["credential_or_cookie_read_attempted"] is False
        assert payload["public_tunnel_attempted"] is False
        assert payload["cloud_api_call_attempted"] is False
        assert payload["llm_or_provider_call_attempted"] is False
        assert payload["canonical_writeback_attempted"] is False
    finally:
        _remove_test_root(root)


def test_help_probe_failure_blocks(monkeypatch) -> None:
    root = _workspace_test_root("help_probe_failure")
    try:
        _seed_wrapper_and_config(root)
        monkeypatch.setattr(
            external_validation.subprocess,
            "run",
            lambda *_args, **_kwargs: subprocess.CompletedProcess(
                ["browser-use", "--help"],
                2,
                stdout="",
                stderr="bad install",
            ),
        )

        report = build_browser_use_cli_external_validation(
            root,
            executable="python",
            generated_at="2026-05-05T15:15:00Z",
            execute_help_probe=True,
        )

        assert report.status == STATUS_FAILED_HELP_PROBE
        assert "browser_use_cli_help_probe_failed" in report.blockers
        assert "browser_use_cli_help_probe_exit_code:2" in report.blockers
        assert report.browser_launch_attempted is False
    finally:
        _remove_test_root(root)


def test_evidence_write_is_explicit(monkeypatch) -> None:
    root = _workspace_test_root("evidence")
    try:
        _seed_wrapper_and_config(root)
        monkeypatch.setattr(
            external_validation.subprocess,
            "run",
            lambda *_args, **_kwargs: _completed(),
        )
        report = build_browser_use_cli_external_validation(
            root,
            executable="python",
            execute_help_probe=True,
        )
        evidence = write_browser_use_cli_external_validation_evidence(
            root,
            report,
            run_slug="browser-use-cli-external-validation-test",
        )

        assert evidence["written"] is True
        assert Path(evidence["json_path"]).exists()
        assert Path(evidence["markdown_path"]).exists()
    finally:
        _remove_test_root(root)


def test_cli_json_without_help_probe_is_bounded() -> None:
    root = _workspace_test_root("cli_json")
    try:
        _seed_wrapper_and_config(root)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = external_validation_main(
                [
                    "--vault-root",
                    str(root),
                    "--executable",
                    "python",
                    "--json",
                ]
            )
        payload = json.loads(stdout.getvalue())

        assert exit_code == 0
        assert payload["status"] == STATUS_READY_NO_EXECUTION
        assert payload["help_probe_attempted"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["canonical_writeback_attempted"] is False
    finally:
        _remove_test_root(root)
