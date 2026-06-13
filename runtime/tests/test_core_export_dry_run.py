"""Dry-run tests for the ChaseOS Core export boundary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402


def _write_manifest(path: Path, target: Path) -> Path:
    manifest = path / "export_manifest.yaml"
    manifest.write_text(
        "\n".join(
            [
                "version: 0.1",
                "source_root_mode: live-personal-instance",
                f"default_target: {target.as_posix()}",
                "mode: allowlist-only",
                "include:",
                "  - source: README.md",
                "    target: README.md",
                "    mode: copy",
                "exclude_always:",
                "  - 00_HOME/",
                "  - 07_LOGS/",
                "  - .chaseos/",
            ]
        ),
        encoding="utf-8",
    )
    return manifest


def test_core_export_build_dry_run_reports_would_write_without_creating_target(tmp_path: Path) -> None:
    from runtime.core_export.exporter import build_dry_run_report

    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n\nFramework docs only.\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)

    report = build_dry_run_report(source_root=source, target_root=target, manifest_path=manifest)

    assert report["ok"] is True
    assert report["dry_run"] is True
    assert report["writes_performed"] is False
    assert report["target_exists"] is False
    assert report["would_create_target"] is True
    assert report["candidate_count"] == 1
    assert report["candidates"][0]["source"] == "README.md"
    assert not target.exists()


def test_core_export_dry_run_fails_closed_when_target_is_inside_source(tmp_path: Path) -> None:
    from runtime.core_export.exporter import build_dry_run_report

    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# Core\n", encoding="utf-8")
    target = source / "chaseos-core"
    manifest = _write_manifest(source, target)

    report = build_dry_run_report(source_root=source, target_root=target, manifest_path=manifest)

    assert report["ok"] is False
    assert report["dry_run"] is True
    assert report["writes_performed"] is False
    assert any("inside source root" in issue for issue in report["blocking_issues"])
    assert not target.exists()


def test_core_export_dry_run_blocks_private_content_patterns(tmp_path: Path) -> None:
    from runtime.core_export.exporter import build_dry_run_report

    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text(
        "# ChaseOS\n\nPrivate runtime path: <VAULT_ROOT>\n",
        encoding="utf-8",
    )
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)

    report = build_dry_run_report(source_root=source, target_root=target, manifest_path=manifest)

    assert report["ok"] is False
    assert report["writes_performed"] is False
    assert report["scanner"]["blocking_findings"]
    assert report["scanner"]["blocking_findings"][0]["pattern_family"] == "local_paths"
    assert not target.exists()


def test_core_export_manifest_loads_without_pyyaml(tmp_path: Path, monkeypatch) -> None:
    import runtime.core_export.manifest as manifest_module

    source = tmp_path / "live-vault"
    source.mkdir()
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    monkeypatch.setattr(manifest_module, "yaml", None)

    loaded = manifest_module.load_manifest(manifest)

    assert loaded["mode"] == "allowlist-only"
    assert loaded["include"][0]["source"] == "README.md"
    assert loaded["include"][0]["target"] == "README.md"
    assert loaded["exclude_always"] == ["00_HOME/", "07_LOGS/", ".chaseos/"]


def test_core_export_cli_build_dry_run_uses_manifest_relative_default_target(tmp_path: Path, capsys) -> None:
    source = tmp_path / "portable-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    manifest = _write_manifest(source, Path("../portable-core"))
    expected_target = tmp_path / "portable-core"

    exit_code = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--manifest",
            str(manifest),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 0
    assert result["ok"] is True
    assert result["target_root"] == str(expected_target.resolve())
    assert result["would_create_target"] is True
    assert not expected_target.exists()


def test_core_export_cli_default_manifest_in_core_export_resolves_sibling_target(tmp_path: Path, capsys) -> None:
    source = tmp_path / "portable-vault"
    manifest_dir = source / "core_export"
    manifest_dir.mkdir(parents=True)
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    manifest = _write_manifest(manifest_dir, Path("../../portable-core"))
    expected_target = tmp_path / "portable-core"

    exit_code = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--manifest",
            str(manifest),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 0
    assert result["ok"] is True
    assert result["target_root"] == str(expected_target.resolve())
    assert "inside source root" not in "\n".join(result["blocking_issues"])
    assert result["would_create_target"] is True
    assert not expected_target.exists()


def test_live_core_export_manifest_default_target_is_sibling_safe() -> None:
    manifest = _VAULT_ROOT / "core_export" / "export_manifest.yaml"
    text = manifest.read_text(encoding="utf-8")

    assert "default_target: ../../chaseos-core" in text


def test_core_export_cli_build_dry_run_uses_json_contract_and_creates_no_target(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)

    exit_code = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "core-export.build"
    assert payload["result"]["dry_run"] is True
    assert payload["result"]["writes_performed"] is False
    assert not target.exists()


def test_core_export_write_report_creates_review_artifacts_not_export_target(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"

    exit_code = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    artifacts = result["report_artifacts"]
    assert exit_code == 0
    assert result["writes_performed"] is False
    assert not target.exists()
    assert artifacts["report_dir"] == str(report_dir.resolve())
    assert Path(artifacts["report_json"]).is_file()
    assert Path(artifacts["preview_files"][0]).is_file()
    assert Path(artifacts["preview_files"][0]).read_text(encoding="utf-8") == "# ChaseOS Core\n"


def test_core_export_verify_report_rescans_previews_and_confirms_target_absent(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0

    verify_exit = cli.main(
        [
            "core-export",
            "verify-report",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert verify_exit == 0
    assert result["ok"] is True
    assert result["report_exists"] is True
    assert result["target_exists"] is False
    assert result["preview_count"] == 1
    assert result["preview_scan"]["blocking_count"] == 0
    assert result["hash_mismatches"] == []
    assert result["blocking_issues"] == []
    assert not target.exists()


def test_core_export_verify_report_fails_closed_if_preview_changed_to_private_content(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0
    (report_dir / "previews" / "README.md").write_text(
        "# Leaked\n\n<VAULT_ROOT>\n",
        encoding="utf-8",
    )

    verify_exit = cli.main(
        [
            "core-export",
            "verify-report",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert verify_exit == 1
    assert result["ok"] is False
    assert result["preview_scan"]["blocking_count"] == 1
    assert result["hash_mismatches"]
    assert any("privacy scanner" in issue for issue in result["blocking_issues"])
    assert not target.exists()


def test_core_export_readiness_requires_clean_verifier_and_passed_manual_review(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"
    review = report_dir / "manual-preview-review-pass2.md"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0
    review.write_text("# Manual Review Pass 2\n\nOverall verdict: PASS\n", encoding="utf-8")

    status_exit = cli.main(
        [
            "core-export",
            "readiness",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--manual-review",
            str(review),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert status_exit == 0
    assert result["ok"] is True
    assert result["readiness_status"] == "ready_for_gate_governed_export"
    assert result["manual_review"]["verdict"] == "pass"
    assert result["verifier"]["ok"] is True
    assert result["writes_performed"] is False
    assert result["target_exists"] is False
    assert result["git_init_allowed"] is False
    assert result["real_export_allowed_without_gate"] is False
    assert not target.exists()


def test_core_export_apply_blocks_without_confirmation_and_approval_ref(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"
    review = report_dir / "manual-preview-review-pass2.md"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0
    review.write_text("# Manual Review Pass 2\n\nOverall verdict: PASS\n", encoding="utf-8")

    export_exit = cli.main(
        [
            "core-export",
            "export",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--manual-review",
            str(review),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert export_exit == 1
    assert result["ok"] is False
    assert result["writes_performed"] is False
    assert result["target_created"] is False
    assert result["git_initialized"] is False
    assert any("--confirm" in issue for issue in result["blocking_issues"])
    assert any("operator approval" in issue.lower() for issue in result["blocking_issues"])
    assert not target.exists()


def test_core_export_apply_writes_verified_previews_without_git_init(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"
    review = report_dir / "manual-preview-review-pass2.md"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0
    review.write_text("# Manual Review Pass 2\n\nOverall verdict: PASS\n", encoding="utf-8")

    export_exit = cli.main(
        [
            "core-export",
            "export",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--manual-review",
            str(review),
            "--operator-approval-ref",
            "test-approval-core-export",
            "--confirm",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert export_exit == 0
    assert result["ok"] is True
    assert result["writes_performed"] is True
    assert result["target_created"] is True
    assert result["git_initialized"] is False
    assert result["written_count"] == 2
    assert (target / "README.md").read_text(encoding="utf-8") == "# ChaseOS Core\n"
    export_status = target / "CORE_EXPORT_STATUS.json"
    assert export_status.exists()
    status_payload = json.loads(export_status.read_text(encoding="utf-8"))
    assert status_payload["operator_approval_ref"] == "test-approval-core-export"
    assert status_payload["git_initialized"] is False
    assert not (target / ".git").exists()


def test_core_export_update_existing_prior_export_without_git_init(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core Updated\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    target.mkdir()
    (target / "README.md").write_text("# Old Seed\n", encoding="utf-8")
    (target / "_GIT_READINESS_REVIEW_CHECKLIST.md").write_text("old review helper\n", encoding="utf-8")
    (target / "CORE_EXPORT_STATUS.json").write_text(
        json.dumps(
            {
                "generated_by": "chaseos core-export export",
                "operator_approval_ref": "old-approval",
                "git_initialized": False,
                "publication_performed": False,
            }
        ),
        encoding="utf-8",
    )
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"
    review = report_dir / "manual-preview-review-pass2.md"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0
    review.write_text("# Manual Review Pass 2\n\nOverall verdict: PASS\n", encoding="utf-8")

    export_exit = cli.main(
        [
            "core-export",
            "export",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--manual-review",
            str(review),
            "--operator-approval-ref",
            "test-approval-core-export-update",
            "--confirm",
            "--update-existing",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert export_exit == 0
    assert result["ok"] is True
    assert result["writes_performed"] is True
    assert result["target_created"] is False
    assert result["target_updated"] is True
    assert result["git_initialized"] is False
    assert (target / "README.md").read_text(encoding="utf-8") == "# ChaseOS Core Updated\n"
    assert (target / "_GIT_READINESS_REVIEW_CHECKLIST.md").exists()
    status_payload = json.loads((target / "CORE_EXPORT_STATUS.json").read_text(encoding="utf-8"))
    assert status_payload["operator_approval_ref"] == "test-approval-core-export-update"
    assert status_payload["update_existing"] is True
    assert status_payload["previous_export_status"]["operator_approval_ref"] == "old-approval"
    assert not (target / ".git").exists()


def test_core_export_verify_export_blocks_absent_target_without_writes(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"
    review = report_dir / "manual-preview-review-pass2.md"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0
    review.write_text("# Manual Review Pass 2\n\nOverall verdict: PASS\n", encoding="utf-8")

    verify_exit = cli.main(
        [
            "core-export",
            "verify-export",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--manual-review",
            str(review),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert verify_exit == 1
    assert result["ok"] is False
    assert result["action"] == "core-export.verify-export"
    assert result["writes_performed"] is False
    assert result["target_exists"] is False
    assert result["git_initialized"] is False
    assert any("target" in issue for issue in result["blocking_issues"])
    assert not target.exists()


def test_core_export_verify_export_validates_exported_tree_without_git_init(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"
    review = report_dir / "manual-preview-review-pass2.md"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0
    review.write_text("# Manual Review Pass 2\n\nOverall verdict: PASS\n", encoding="utf-8")

    export_exit = cli.main(
        [
            "core-export",
            "export",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--manual-review",
            str(review),
            "--operator-approval-ref",
            "test-approval-core-export",
            "--confirm",
            "--json",
        ]
    )
    capsys.readouterr()
    assert export_exit == 0

    verify_exit = cli.main(
        [
            "core-export",
            "verify-export",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--manual-review",
            str(review),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert verify_exit == 0
    assert result["ok"] is True
    assert result["verification_status"] == "export_verified"
    assert result["writes_performed"] is False
    assert result["target_exists"] is True
    assert result["git_initialized"] is False
    assert result["publication_performed"] is False
    assert result["candidate_count"] == 1
    assert result["verified_file_count"] == 1
    assert result["status_file_exists"] is True
    assert result["missing_files"] == []
    assert result["hash_mismatches"] == []
    assert not (target / ".git").exists()


def test_core_export_next_step_identifies_manual_export_approval_when_target_absent(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"
    review = report_dir / "manual-preview-review-pass2.md"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0
    review.write_text("# Manual Review Pass 2\n\nOverall verdict: PASS\n", encoding="utf-8")

    step_exit = cli.main(
        [
            "core-export",
            "next-step",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--manual-review",
            str(review),
            "--requested-by",
            "optimus",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert step_exit == 0
    assert result["ok"] is True
    assert result["action"] == "core-export.next-step"
    assert result["stage"] == "ready_for_manual_export_approval"
    assert result["manual_step_required"] is True
    assert result["manual_step_kind"] == "approve_local_export"
    assert result["approval_operation"] == "core_export.real_export"
    assert result["writes_performed"] is False
    assert result["target_created"] is False
    assert result["git_initialized"] is False
    assert result["publication_performed"] is False
    assert "--operator-approval-ref" in result["operator_command_preview"]
    assert "<APPROVAL_REF>" in result["operator_command_preview"]
    assert not target.exists()


def test_core_export_next_step_identifies_manual_git_init_approval_after_verified_export(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"
    review = report_dir / "manual-preview-review-pass2.md"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0
    review.write_text("# Manual Review Pass 2\n\nOverall verdict: PASS\n", encoding="utf-8")
    export_exit = cli.main(
        [
            "core-export",
            "export",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--manual-review",
            str(review),
            "--operator-approval-ref",
            "test-approved-export",
            "--confirm",
            "--json",
        ]
    )
    capsys.readouterr()
    assert export_exit == 0

    step_exit = cli.main(
        [
            "core-export",
            "next-step",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--manual-review",
            str(review),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert step_exit == 0
    assert result["ok"] is True
    assert result["stage"] == "ready_for_manual_git_init_approval"
    assert result["manual_step_required"] is True
    assert result["manual_step_kind"] == "approve_git_init"
    assert result["approval_operation"] == "core_export.git_init"
    assert result["export_verification_status"] == "export_verified"
    assert result["writes_performed"] is False
    assert result["target_created"] is False
    assert result["git_initialized"] is False
    assert result["publication_performed"] is False
    assert result["operator_command_preview"] is None
    assert not (target / ".git").exists()


def test_core_export_request_export_returns_non_mutating_approval_packet(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"
    review = report_dir / "manual-preview-review-pass2.md"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0
    review.write_text("# Manual Review Pass 2\n\nOverall verdict: PASS\n", encoding="utf-8")

    request_exit = cli.main(
        [
            "core-export",
            "request-export",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--manual-review",
            str(review),
            "--requested-by",
            "optimus",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert request_exit == 0
    assert result["ok"] is True
    assert result["action"] == "core-export.request-export"
    assert result["approval_request_ready"] is True
    assert result["writes_performed"] is False
    assert result["approval_request_written"] is False
    assert result["target_created"] is False
    assert result["git_initialized"] is False
    assert result["publication_performed"] is False
    assert result["requested_by"] == "optimus"
    assert result["approval_operation"] == "core_export.real_export"
    assert result["readiness_status"] == "ready_for_gate_governed_export"
    assert "--operator-approval-ref" in result["operator_command_preview"]
    assert str(target) in result["operator_command_preview"]
    assert not target.exists()


def test_core_export_request_export_blocks_when_readiness_not_clean(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0

    request_exit = cli.main(
        [
            "core-export",
            "request-export",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--requested-by",
            "optimus",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert request_exit == 1
    assert result["ok"] is False
    assert result["approval_request_ready"] is False
    assert result["writes_performed"] is False
    assert result["approval_request_written"] is False
    assert result["readiness_status"] == "blocked"
    assert any("readiness" in issue for issue in result["blocking_issues"])
    assert not target.exists()


def test_core_export_readiness_blocks_when_manual_review_missing(tmp_path: Path, capsys) -> None:
    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# ChaseOS Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = _write_manifest(source, target)
    report_dir = source / "core_export" / "reports" / "latest"

    build_exit = cli.main(
        [
            "core-export",
            "build",
            "--dry-run",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--write-report",
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )
    capsys.readouterr()
    assert build_exit == 0

    status_exit = cli.main(
        [
            "core-export",
            "readiness",
            "--source-root",
            str(source),
            "--target",
            str(target),
            "--manifest",
            str(manifest),
            "--report-dir",
            str(report_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert status_exit == 1
    assert result["ok"] is False
    assert result["readiness_status"] == "blocked"
    assert result["manual_review"]["verdict"] == "missing"
    assert any("manual review" in issue for issue in result["blocking_issues"])
    assert result["writes_performed"] is False
    assert not target.exists()
