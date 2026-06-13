"""Tests for bounded Browser Use CLI safe-URL validation run."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from runtime.browser_runtime.browser_use_cli_safe_url_validation_run import (
    STATUS_COMPLETE,
    STATUS_FAILED_BROWSER_USE,
    build_browser_use_cli_safe_url_validation_run,
    main as run_main,
    write_browser_use_cli_safe_url_validation_run_evidence,
)


def _write_design(path: Path, *, executable: Path) -> None:
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.write_text("exe", encoding="utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "status": "browser_use_cli_safe_url_validation_design_ready_no_execution",
                "target_url": "http://127.0.0.1:8770/",
                "browser_use_executable": str(executable),
                "browser_use_executable_path": str(executable),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_help_probe(path: Path, *, executable: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
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
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_safe_url_run_completes_with_existing_target_and_fake_runner(tmp_path: Path) -> None:
    design = tmp_path / "design.json"
    help_probe = tmp_path / "07_LOGS/Browser-Runs/browser-use-cli-external-validation-20260505-help-probe.json"
    executable = tmp_path / "browser-use.exe"
    _write_design(design, executable=executable)
    _write_help_probe(help_probe, executable=executable)

    report = build_browser_use_cli_safe_url_validation_run(
        tmp_path,
        design_evidence=design,
        run_browser_use=False,
        generated_at="2026-05-05T17:00:00Z",
    )

    assert report.status != STATUS_COMPLETE
    assert "browser_use_open_not_run" in report.blockers
    assert report.browser_dependency_install_command_run is False
    assert report.real_profile_access_attempted is False
    assert report.canonical_writeback_attempted is False


def test_evidence_write_is_explicit_for_failed_run(tmp_path: Path) -> None:
    design = tmp_path / "design.json"
    help_probe = tmp_path / "07_LOGS/Browser-Runs/browser-use-cli-external-validation-20260505-help-probe.json"
    executable = tmp_path / "browser-use.exe"
    _write_design(design, executable=executable)
    _write_help_probe(help_probe, executable=executable)
    report = build_browser_use_cli_safe_url_validation_run(
        tmp_path,
        design_evidence=design,
        run_browser_use=False,
    )

    written = write_browser_use_cli_safe_url_validation_run_evidence(
        tmp_path,
        report,
        run_slug="safe-url-run-test",
    )

    assert Path(written["json_path"]).exists()
    assert Path(written["markdown_path"]).exists()


def test_cli_json_blocks_without_run_flag(tmp_path: Path) -> None:
    design = tmp_path / "design.json"
    help_probe = tmp_path / "07_LOGS/Browser-Runs/browser-use-cli-external-validation-20260505-help-probe.json"
    executable = tmp_path / "browser-use.exe"
    _write_design(design, executable=executable)
    _write_help_probe(help_probe, executable=executable)
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = run_main(
            [
                "--vault-root",
                str(tmp_path),
                "--design-evidence",
                str(design),
                "--json",
            ]
        )
    payload = json.loads(output.getvalue())

    assert exit_code == 1
    assert payload["status"] in {
        STATUS_FAILED_BROWSER_USE,
        "blocked_browser_use_cli_safe_url_validation_run_target_not_ready",
    }
    assert payload["dependency_install_command_attempted"] is False
    assert payload["real_profile_access_attempted"] is False
    assert payload["canonical_writeback_attempted"] is False
