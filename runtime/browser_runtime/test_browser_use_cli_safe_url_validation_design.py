"""Tests for Browser Use CLI safe-URL validation design."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from runtime.browser_runtime.browser_use_cli_safe_url_validation_design import (
    STATUS_BLOCKED,
    STATUS_READY,
    build_browser_use_cli_safe_url_validation_design,
    main as design_main,
    write_browser_use_cli_safe_url_validation_design_evidence,
)


def _write_help_probe(path: Path, *, executable: Path, unsafe: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.write_text("exe", encoding="utf-8")
    payload = {
        "status": "browser_use_cli_external_validation_complete_help_probe_no_browser",
        "executable": str(executable),
        "executable_path": str(executable),
        "help_probe_attempted": True,
        "help_probe_exit_code": 0,
        "expected_help_surface_present": True,
        "browser_command_execution_attempted": False,
        "browser_launch_attempted": False,
        "real_profile_access_attempted": False,
        "credential_or_cookie_read_attempted": False,
        "public_tunnel_attempted": False,
        "canonical_writeback_attempted": False,
    }
    if unsafe:
        payload["browser_launch_attempted"] = True
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_design_ready_for_loopback_target_without_execution(tmp_path: Path) -> None:
    evidence = tmp_path / "help.json"
    executable = tmp_path / "browser-use.exe"
    _write_help_probe(evidence, executable=executable)

    report = build_browser_use_cli_safe_url_validation_design(
        tmp_path,
        help_probe_evidence=evidence,
        generated_at="2026-05-05T16:00:00Z",
    )
    payload = report.to_dict()

    assert payload["status"] == STATUS_READY
    assert payload["target_url"] == "http://127.0.0.1:8770/"
    assert payload["browser_use_package_download_complete"] is True
    assert payload["browser_dependency_download_verified"] is False
    assert payload["browser_dependency_install_command_run"] is False
    assert payload["allowed_subcommand"] == "open"
    assert "--profile" not in payload["future_command_argv"]
    assert "tunnel" in payload["forbidden_subcommands"]
    assert payload["browser_command_execution_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False


def test_design_blocks_non_loopback_target(tmp_path: Path) -> None:
    evidence = tmp_path / "help.json"
    executable = tmp_path / "browser-use.exe"
    _write_help_probe(evidence, executable=executable)

    report = build_browser_use_cli_safe_url_validation_design(
        tmp_path,
        target_url="https://example.com/",
        help_probe_evidence=evidence,
    )

    assert report.status == STATUS_BLOCKED
    assert "safe_url_target_not_loopback_http" in report.blockers


def test_design_blocks_unsafe_or_missing_help_probe(tmp_path: Path) -> None:
    evidence = tmp_path / "help.json"
    executable = tmp_path / "browser-use.exe"
    _write_help_probe(evidence, executable=executable, unsafe=True)

    report = build_browser_use_cli_safe_url_validation_design(
        tmp_path,
        help_probe_evidence=evidence,
    )

    assert report.status == STATUS_BLOCKED
    assert "browser_use_cli_external_help_probe_evidence_not_ready" in report.blockers


def test_evidence_write_is_explicit(tmp_path: Path) -> None:
    evidence = tmp_path / "help.json"
    executable = tmp_path / "browser-use.exe"
    _write_help_probe(evidence, executable=executable)
    report = build_browser_use_cli_safe_url_validation_design(tmp_path, help_probe_evidence=evidence)

    written = write_browser_use_cli_safe_url_validation_design_evidence(
        tmp_path,
        report,
        run_slug="safe-url-design-test",
    )

    assert written["written"] is True
    assert Path(written["json_path"]).exists()
    assert Path(written["markdown_path"]).exists()


def test_cli_json_is_no_execution(tmp_path: Path) -> None:
    evidence = tmp_path / "help.json"
    executable = tmp_path / "browser-use.exe"
    _write_help_probe(evidence, executable=executable)
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = design_main(
            [
                "--vault-root",
                str(tmp_path),
                "--help-probe-evidence",
                str(evidence),
                "--json",
            ]
        )
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert payload["status"] == STATUS_READY
    assert payload["read_only"] is True
    assert payload["browser_dependency_download_attempted"] is False
    assert payload["browser_command_execution_attempted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
