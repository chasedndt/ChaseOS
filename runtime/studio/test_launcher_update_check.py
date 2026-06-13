"""Recovered launcher update tests with current-pass verifier coverage.

The original source file was truncated during the 2026-05-25 candidate-verifier
pass. This wrapper keeps the last compiled test module available without
decompiling or mutating the recovered bytecode, then defines the new pass tests
as normal source below.
"""

from __future__ import annotations

import hashlib as _hashlib
import json as _json
import marshal as _marshal
from pathlib import Path as _Path


_RECOVERED_TEST_BYTECODE_PATH = (
    _Path(__file__).with_name("recovery")
    / "test_launcher_update_check_recovered_20260525_025258.cpython-314.bytecode"
)
_RECOVERED_TEST_BYTECODE_SHA256 = (
    "2ee2dc1c4bd243051edef9a9323346f20d353293f19ae377805d994e327db30c"
)

if not _RECOVERED_TEST_BYTECODE_PATH.exists():
    raise ImportError(
        f"Recovered launcher update test bytecode is missing: "
        f"{_RECOVERED_TEST_BYTECODE_PATH}"
    )

_RECOVERED_TEST_BYTECODE_BYTES = _RECOVERED_TEST_BYTECODE_PATH.read_bytes()
if (
    _hashlib.sha256(_RECOVERED_TEST_BYTECODE_BYTES).hexdigest()
    != _RECOVERED_TEST_BYTECODE_SHA256
):
    raise ImportError(
        f"Recovered launcher update test bytecode hash mismatch: "
        f"{_RECOVERED_TEST_BYTECODE_PATH}"
    )

_RECOVERED_TEST_CODE = _marshal.loads(_RECOVERED_TEST_BYTECODE_BYTES[16:])
exec(_RECOVERED_TEST_CODE, globals())


def test_launcher_update_normal_source_candidate_verification_requires_digest_bound_statement(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_normal_source_candidate_verification_proof,
        required_update_normal_source_candidate_verification_operator_statement,
    )

    launcher_candidate = tmp_path / "launcher_update_check.py"
    launcher_candidate.write_text(
        "\n".join(
            [
                "def build_launcher_update_status():",
                "    return None",
                "",
                "def build_launcher_update_check():",
                "    return None",
                "",
            ]
        ),
        encoding="utf-8",
    )
    api_candidate = tmp_path / "api.py"
    api_candidate.write_text(
        "\n".join(
            [
                "class StudioAPI:",
                "    def get_launcher_update_status(self):",
                "        return None",
                "",
            ]
        ),
        encoding="utf-8",
    )
    shell_test_candidate = tmp_path / "test_pass10a_shell.py"
    shell_test_candidate.write_text(
        "\n".join(
            [
                "class TestLauncherUpdatePrimaryRelaunchReceiptBoundaryShell:",
                "    def test_candidate(self):",
                "        assert True",
                "",
            ]
        ),
        encoding="utf-8",
    )

    candidate_paths = {
        "launcher_update_check": [str(launcher_candidate)],
        "studio_shell_api": [str(api_candidate)],
        "studio_shell_test_pass10a": [str(shell_test_candidate)],
    }
    required_symbols_by_role = {
        "launcher_update_check": [
            "build_launcher_update_status",
            "build_launcher_update_check",
        ],
        "studio_shell_api": ["StudioAPI", "get_launcher_update_status"],
        "studio_shell_test_pass10a": [
            "TestLauncherUpdatePrimaryRelaunchReceiptBoundaryShell",
            "test_candidate",
        ],
    }

    preview = build_launcher_update_normal_source_candidate_verification_proof(
        tmp_path,
        candidate_paths=candidate_paths,
        required_symbols_by_role=required_symbols_by_role,
    )

    assert preview["status"] == (
        "launcher_update_normal_source_candidate_verification_pending_approval"
    )
    assert preview["ok"] is False
    assert preview["candidate_set_complete"] is True
    assert preview["source_replacement_performed"] is False
    assert preview["source_rewrite_from_bytecode_performed"] is False
    assert preview["decompiler_execution_performed"] is False
    assert preview["final_auto_update_closeout_blocked"] is True

    approval_statement = (
        required_update_normal_source_candidate_verification_operator_statement(
            preview["candidate_set"]
        )
    )
    approved = build_launcher_update_normal_source_candidate_verification_proof(
        tmp_path,
        candidate_paths=candidate_paths,
        operator_approved_candidate_verification=True,
        operator_statement=approval_statement,
        required_symbols_by_role=required_symbols_by_role,
    )

    assert approved["ok"] is True
    assert approved["status"] == "launcher_update_normal_source_candidate_verification_ready"
    assert approved["source_restoration_candidate_verification_ready"] is True
    assert approved["normal_source_restoration_ready"] is False
    assert approved["source_replacement_performed"] is False
    assert approved["source_rewrite_from_bytecode_performed"] is False
    assert approved["decompiler_execution_performed"] is False
    assert approved["final_auto_update_closeout_blocked"] is True
    assert (
        approved["authority"]["updater_normal_source_candidate_verification_ready"]
        is True
    )
    assert (
        approved["authority"][
            "updater_normal_source_candidate_verification_source_replacement_performed"
        ]
        is False
    )
    assert (
        approved["authority"][
            "updater_normal_source_candidate_verification_final_closeout_blocked"
        ]
        is True
    )


def test_launcher_update_normal_source_candidate_verification_rejects_recovery_wrappers(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_normal_source_candidate_verification_proof,
    )

    wrapper_candidate = tmp_path / "launcher_update_check.py"
    wrapper_candidate.write_text(
        "\n".join(
            [
                "import marshal as _marshal",
                "from pathlib import Path as _Path",
                "_RECOVERED_BYTECODE_PATH = _Path('launcher.bytecode')",
                "def build_launcher_update_status():",
                "    return None",
                "def build_launcher_update_check():",
                "    return None",
                "exec(_RECOVERED_BYTECODE_CODE, globals())",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = build_launcher_update_normal_source_candidate_verification_proof(
        tmp_path,
        candidate_paths={"launcher_update_check": [str(wrapper_candidate)]},
        required_symbols_by_role={
            "launcher_update_check": [
                "build_launcher_update_status",
                "build_launcher_update_check",
            ]
        },
    )

    assert result["ok"] is False
    assert "launcher_update_check_candidate_verification_required" in result["errors"]
    assert result["source_replacement_performed"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    candidate = result["candidates"]["launcher_update_check"][0]
    assert candidate["candidate_status"] == "failed_verification"
    assert "candidate_contains_recovery_wrapper_tokens" in candidate["errors"]


def test_launcher_update_normal_source_candidate_restore_executor_writes_fixture_targets_after_digest_approval(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_normal_source_candidate_restore_executor_proof,
        build_launcher_update_normal_source_candidate_verification_proof,
        required_update_normal_source_candidate_restore_operator_statement,
        required_update_normal_source_candidate_verification_operator_statement,
    )

    launcher_candidate = tmp_path / "candidates" / "launcher_update_check.py"
    api_candidate = tmp_path / "candidates" / "api.py"
    shell_test_candidate = tmp_path / "candidates" / "test_pass10a_shell.py"
    launcher_candidate.parent.mkdir(parents=True)
    launcher_candidate.write_text(
        "def build_launcher_update_status():\n"
        "    return {'ok': True}\n\n"
        "def build_launcher_update_check():\n"
        "    return {'status': 'ok'}\n",
        encoding="utf-8",
    )
    api_candidate.write_text(
        "class StudioAPI:\n"
        "    def get_launcher_update_status(self):\n"
        "        return {'ok': True}\n",
        encoding="utf-8",
    )
    shell_test_candidate.write_text(
        "class TestLauncherUpdatePrimaryRelaunchReceiptBoundaryShell:\n"
        "    def test_candidate(self):\n"
        "        assert True\n",
        encoding="utf-8",
    )
    candidate_paths = {
        "launcher_update_check": [str(launcher_candidate)],
        "studio_shell_api": [str(api_candidate)],
        "studio_shell_test_pass10a": [str(shell_test_candidate)],
    }
    required_symbols_by_role = {
        "launcher_update_check": [
            "build_launcher_update_status",
            "build_launcher_update_check",
        ],
        "studio_shell_api": ["StudioAPI", "get_launcher_update_status"],
        "studio_shell_test_pass10a": [
            "TestLauncherUpdatePrimaryRelaunchReceiptBoundaryShell",
            "test_candidate",
        ],
    }
    preview = build_launcher_update_normal_source_candidate_verification_proof(
        tmp_path,
        candidate_paths=candidate_paths,
        required_symbols_by_role=required_symbols_by_role,
    )
    verification_statement = (
        required_update_normal_source_candidate_verification_operator_statement(
            preview["candidate_set"]
        )
    )
    verification = build_launcher_update_normal_source_candidate_verification_proof(
        tmp_path,
        candidate_paths=candidate_paths,
        operator_approved_candidate_verification=True,
        operator_statement=verification_statement,
        required_symbols_by_role=required_symbols_by_role,
    )
    assert verification["ok"] is True

    restore_root = tmp_path / "restore-root"
    blocked = build_launcher_update_normal_source_candidate_restore_executor_proof(
        tmp_path,
        candidate_verification_proof=verification,
        restore_root=restore_root,
        required_symbols_by_role=required_symbols_by_role,
    )
    assert (
        blocked["status"]
        == "launcher_update_normal_source_candidate_restore_executor_pending_approval"
    )
    assert blocked["source_restore_performed"] is False
    assert blocked["source_write_performed"] is False
    assert blocked["final_auto_update_closeout_blocked"] is True

    restore_statement = required_update_normal_source_candidate_restore_operator_statement(
        blocked["restore_plan"]
    )
    restored = build_launcher_update_normal_source_candidate_restore_executor_proof(
        tmp_path,
        candidate_verification_proof=verification,
        restore_root=restore_root,
        operator_approved_restore=True,
        operator_statement=restore_statement,
        required_symbols_by_role=required_symbols_by_role,
    )

    assert restored["ok"] is True
    assert (
        restored["status"]
        == "launcher_update_normal_source_candidate_restore_executor_restored"
    )
    assert restored["source_restore_performed"] is True
    assert restored["source_write_performed"] is True
    assert restored["source_file_replacement_performed"] is True
    assert restored["source_rewrite_from_bytecode_performed"] is False
    assert restored["decompiler_execution_performed"] is False
    assert restored["candidate_source_execution_performed"] is False
    assert restored["installer_launch_performed"] is False
    assert restored["primary_exe_replacement_performed"] is False
    assert restored["production_auto_update_complete"] is False
    assert restored["final_auto_update_closeout_blocked"] is True
    assert (
        restore_root / "runtime" / "studio" / "launcher_update_check.py"
    ).read_text(encoding="utf-8") == launcher_candidate.read_text(encoding="utf-8")
    assert (
        restore_root / "runtime" / "studio" / "shell" / "api.py"
    ).read_text(encoding="utf-8") == api_candidate.read_text(encoding="utf-8")
    assert (
        restore_root / "runtime" / "studio" / "shell" / "test_pass10a_shell.py"
    ).read_text(encoding="utf-8") == shell_test_candidate.read_text(encoding="utf-8")


def test_launcher_update_normal_source_candidate_restore_executor_blocks_tampered_candidate(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_normal_source_candidate_restore_executor_proof,
        build_launcher_update_normal_source_candidate_verification_proof,
        required_update_normal_source_candidate_restore_operator_statement,
        required_update_normal_source_candidate_verification_operator_statement,
    )

    launcher_candidate = tmp_path / "launcher_update_check.py"
    api_candidate = tmp_path / "api.py"
    shell_test_candidate = tmp_path / "test_pass10a_shell.py"
    launcher_candidate.write_text(
        "def build_launcher_update_status():\n"
        "    return None\n\n"
        "def build_launcher_update_check():\n"
        "    return None\n",
        encoding="utf-8",
    )
    api_candidate.write_text(
        "class StudioAPI:\n"
        "    def get_launcher_update_status(self):\n"
        "        return None\n",
        encoding="utf-8",
    )
    shell_test_candidate.write_text(
        "class TestLauncherUpdatePrimaryRelaunchReceiptBoundaryShell:\n"
        "    def test_candidate(self):\n"
        "        assert True\n",
        encoding="utf-8",
    )
    candidate_paths = {
        "launcher_update_check": [str(launcher_candidate)],
        "studio_shell_api": [str(api_candidate)],
        "studio_shell_test_pass10a": [str(shell_test_candidate)],
    }
    required_symbols_by_role = {
        "launcher_update_check": [
            "build_launcher_update_status",
            "build_launcher_update_check",
        ],
        "studio_shell_api": ["StudioAPI", "get_launcher_update_status"],
        "studio_shell_test_pass10a": [
            "TestLauncherUpdatePrimaryRelaunchReceiptBoundaryShell",
            "test_candidate",
        ],
    }
    preview = build_launcher_update_normal_source_candidate_verification_proof(
        tmp_path,
        candidate_paths=candidate_paths,
        required_symbols_by_role=required_symbols_by_role,
    )
    verification_statement = (
        required_update_normal_source_candidate_verification_operator_statement(
            preview["candidate_set"]
        )
    )
    verification = build_launcher_update_normal_source_candidate_verification_proof(
        tmp_path,
        candidate_paths=candidate_paths,
        operator_approved_candidate_verification=True,
        operator_statement=verification_statement,
        required_symbols_by_role=required_symbols_by_role,
    )
    assert verification["ok"] is True

    launcher_candidate.write_text(
        "def build_launcher_update_status():\n"
        "    return None\n\n"
        "def build_launcher_update_check():\n"
        "    return 'tampered'\n",
        encoding="utf-8",
    )
    blocked = build_launcher_update_normal_source_candidate_restore_executor_proof(
        tmp_path,
        candidate_verification_proof=verification,
        restore_root=tmp_path / "restore-root",
        required_symbols_by_role=required_symbols_by_role,
    )
    restore_statement = required_update_normal_source_candidate_restore_operator_statement(
        blocked["restore_plan"]
    )
    result = build_launcher_update_normal_source_candidate_restore_executor_proof(
        tmp_path,
        candidate_verification_proof=verification,
        restore_root=tmp_path / "restore-root",
        operator_approved_restore=True,
        operator_statement=restore_statement,
        required_symbols_by_role=required_symbols_by_role,
    )

    assert result["ok"] is False
    assert result["source_restore_performed"] is False
    assert result["source_write_performed"] is False
    assert "launcher_update_check_restore_plan_invalid" in result["errors"]
    assert (
        "candidate_hash_mismatch"
        in result["restore_plan"]["role_plan"]["launcher_update_check"]["errors"]
    )


def test_launcher_update_source_regeneration_readiness_blocks_without_tooling_or_candidates():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_source_regeneration_readiness,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = build_launcher_update_source_regeneration_readiness(
        vault_root,
        decompiler_command_candidates=["definitely-missing-chaseos-decompiler"],
        decompiler_module_candidates=["definitely_missing_chaseos_decompiler_module"],
    )

    assert result["ok"] is False
    assert result["surface"] == "studio_launcher_update_source_regeneration_readiness"
    assert (
        result["status"]
        == "launcher_update_source_regeneration_readiness_blocked"
    )
    assert result["bytecode_artifacts_ready"] is True
    assert result["decompiler_tool_available"] is False
    assert result["source_regeneration_execution_enabled"] is False
    assert result["source_regeneration_execution_performed"] is False
    assert result["source_regeneration_output_written"] is False
    assert result["source_write_performed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["installer_launch_performed"] is False
    assert result["helper_launch_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert "source_regeneration_tool_unavailable" in result["errors"]
    assert "authoritative_normal_source_candidates_missing" in result["errors"]
    for role in [
        "launcher_update_check",
        "studio_shell_api",
        "launcher_update_tests",
    ]:
        descriptor = result["bytecode_inputs"][role]
        assert descriptor["exists"] is True
        assert descriptor["inside_vault_root"] is True
        assert descriptor["marshal_load_ok"] is True
        assert descriptor["sha256"]
        assert descriptor["code_object_count"] > 0


def test_launcher_update_source_regeneration_readiness_simulates_tool_availability_without_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_source_regeneration_readiness,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = build_launcher_update_source_regeneration_readiness(
        vault_root,
        decompiler_command_candidates=["python"],
        decompiler_module_candidates=["pathlib"],
    )

    assert result["ok"] is True, result["errors"]
    assert (
        result["status"]
        == "launcher_update_source_regeneration_readiness_ready_for_operator_plan"
    )
    assert result["bytecode_artifacts_ready"] is True
    assert result["decompiler_tool_available"] is True
    assert "source_regeneration_tool_unavailable" not in result["errors"]
    assert "authoritative_normal_source_candidates_missing" not in result["errors"]
    assert result["source_regeneration_ready"] is True
    assert result["source_regeneration_execution_enabled"] is False
    assert result["source_regeneration_execution_performed"] is False
    assert result["source_write_performed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["final_auto_update_closeout_blocked"] is True


def _write_fixture_source_regeneration_bytecode(path):
    code = compile("def regenerated_fixture():\n    return True\n", str(path), "exec")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\0" * 16 + _marshal.dumps(code))


def _fixture_source_regeneration_bytecode_inputs(root):
    recovery_root = root / "runtime" / "studio" / "recovery"
    paths = {
        "launcher_update_check": recovery_root / "launcher.bytecode",
        "studio_shell_api": recovery_root / "api.bytecode",
        "launcher_update_tests": recovery_root / "tests.bytecode",
    }
    for path in paths.values():
        _write_fixture_source_regeneration_bytecode(path)
    return paths


def _fixture_source_regeneration_runner(context):
    return {
        "ok": True,
        "runner_label": context["runner_label"],
        "generated_sources": {
            "launcher_update_check": "\n".join(
                [
                    "def build_launcher_update_status():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_check():",
                    "    return {'status': 'ok'}",
                    "",
                    "def build_launcher_update_source_recovery_cleanup_proof():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_normal_source_restoration_readiness():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_normal_source_candidate_verification_proof():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_source_regeneration_candidate_verification_restore_proof():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_source_regeneration_live_source_restoration_closeout_proof():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_real_source_restoration_execution_regression_boundary_proof():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_current_vault_source_restoration_closeout_readiness():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_source_candidate_inventory_wrapper_removal_preflight():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_authoritative_normal_source_candidate_supply_packet():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_authoritative_normal_source_candidate_supply_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_authoritative_source_candidate_import_boundary_proof():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_authoritative_source_candidate_import_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_real_authoritative_source_candidate_supply_readiness():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_real_authoritative_source_candidate_materialization_proof():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_real_authoritative_source_candidate_materialization_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_real_authoritative_source_candidate_import_from_materialization_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_current_vault_wrapper_removal_from_materialization_import_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_production_primary_closeout_after_source_recovery_proof():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_final_production_auto_update_closeout_audit():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_governed_live_completion_evidence_packet():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_governed_live_completion_evidence_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_controlled_live_installer_evidence_runner():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_controlled_live_installer_evidence_runner_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_approved_live_evidence_runner_adapter():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_approved_live_evidence_runner_adapter_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_approved_live_evidence_runner_real_dry_run():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_approved_live_evidence_runner_real_dry_run_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_live_receipt_digest_consistency_closeout():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_real_live_receipt_capture_boundary():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_real_live_receipt_capture_boundary_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_real_live_receipt_bundle_production_runner():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_real_live_receipt_bundle_production_runner_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_production_runner_final_closeout_bridge():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_approved_production_runner_real_evidence_capture():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_approved_production_runner_real_evidence_capture_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_installer_real_artifact_build_output_capture():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_dist_artifact_isolation_cohabitation_proof():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_signed_artifact_verification_closeout():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_local_installer_disposable_dry_run_proof():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_local_manifest_background_prompt_settings_action():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_local_release_channel_blocker_closeout():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_authoritative_candidate_supply_verification_after_import_proof():",
                    "    return {'ok': True}",
                    "",
                    "def build_launcher_update_current_vault_wrapper_removal_after_import_execution_proof():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_current_vault_wrapper_removal_after_import_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_current_vault_wrapper_removal_executor_boundary_proof():",
                    "    return {'ok': True}",
                    "",
                    "def required_update_current_vault_wrapper_removal_operator_statement():",
                    "    return 'ok'",
                    "",
                    "def build_launcher_update_production_primary_relaunch_receipt_boundary_proof():",
                    "    return {'ok': True}",
                    "",
                ]
            ),
            "studio_shell_api": "\n".join(
                [
                    "class StudioAPI:",
                    "    def get_launcher_update_source_recovery_cleanup_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_normal_source_restoration_readiness(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_normal_source_candidate_verification_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_source_regeneration_candidate_verification_restore_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_source_regeneration_live_source_restoration_closeout_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_real_source_restoration_execution_regression_boundary_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_current_vault_source_restoration_closeout_readiness(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_source_candidate_inventory_wrapper_removal_preflight(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_authoritative_normal_source_candidate_supply_packet(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_authoritative_source_candidate_import_boundary_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_real_authoritative_source_candidate_supply_readiness(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_real_authoritative_source_candidate_materialization_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_production_primary_closeout_after_source_recovery_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_final_production_auto_update_closeout_audit(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_governed_live_completion_evidence_packet(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_controlled_live_installer_evidence_runner(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_approved_live_evidence_runner_adapter(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_approved_live_evidence_runner_real_dry_run(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_live_receipt_digest_consistency_closeout(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_real_live_receipt_capture_boundary(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_real_live_receipt_bundle_production_runner(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_production_runner_final_closeout_bridge(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_approved_production_runner_real_evidence_capture(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_installer_real_artifact_build_output_capture(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_dist_artifact_isolation_cohabitation_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_signed_artifact_verification_closeout(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_local_installer_disposable_dry_run_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_local_manifest_background_prompt_settings_action(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_local_release_channel_blocker_closeout(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_authoritative_candidate_supply_verification_after_import_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_current_vault_wrapper_removal_after_import_execution_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_current_vault_wrapper_removal_executor_boundary_proof(self):",
                    "        return {'ok': True}",
                    "",
                    "    def get_launcher_update_production_primary_relaunch_receipt_boundary_proof(self):",
                    "        return {'ok': True}",
                    "",
                ]
            ),
            "studio_shell_test_pass10a": "\n".join(
                [
                    "class TestLauncherUpdatePrimaryRelaunchReceiptBoundaryShell:",
                    "    def test_api_returns_source_recovery_cleanup_proof_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_normal_source_restoration_readiness_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_normal_source_candidate_verification_proof_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_source_regeneration_candidate_verification_restore_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_source_regeneration_live_source_restoration_closeout_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_real_source_restoration_execution_regression_boundary_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_current_vault_source_restoration_closeout_readiness_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_source_candidate_inventory_wrapper_removal_preflight_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_authoritative_normal_source_candidate_supply_packet_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_authoritative_source_candidate_import_boundary_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_real_authoritative_source_candidate_supply_readiness_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_real_authoritative_source_candidate_materialization_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_real_authoritative_source_candidate_import_from_materialization_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_real_authoritative_source_candidate_supply_verification_from_materialization_import_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_current_vault_wrapper_removal_from_materialization_import_execution_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_post_wrapper_removal_regression_from_materialization_import_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_current_vault_source_closeout_from_materialization_import_regression_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_production_primary_closeout_after_source_recovery_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_final_production_auto_update_closeout_audit_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_governed_live_completion_evidence_packet_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_controlled_live_installer_evidence_runner_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_approved_live_evidence_runner_adapter_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_approved_live_evidence_runner_real_dry_run_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_live_receipt_digest_consistency_closeout_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_real_live_receipt_capture_boundary_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_real_live_receipt_bundle_production_runner_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_production_runner_final_closeout_bridge_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_approved_production_runner_real_evidence_capture_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_installer_real_artifact_build_output_capture_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_dist_artifact_isolation_cohabitation_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_signed_artifact_verification_closeout_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_local_installer_disposable_dry_run_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_local_manifest_background_prompt_settings_action_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_local_release_channel_blocker_closeout_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_authoritative_candidate_supply_verification_after_import_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_current_vault_wrapper_removal_after_import_execution_envelope(self):",
                    "        assert True",
                    "",
                    "    def test_api_returns_current_vault_wrapper_removal_executor_boundary_envelope(self):",
                    "        assert True",
                    "",
                ]
            ),
        },
    }


def _fixture_regression_evidence(command_plan):
    return {
        "commands": {
            item["id"]: {
                "id": item["id"],
                "command": item["command"],
                "exit_code": item.get("required_exit_code", 0),
                "passed": True,
            }
            for item in command_plan
        }
    }


def _fixture_live_source_restoration_proof(tmp_path, timestamp="2026-05-25T00:00:00Z"):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof,
        build_launcher_update_source_regeneration_readiness,
        build_launcher_update_source_regeneration_runner_boundary_proof,
    )

    bytecode_inputs = _fixture_source_regeneration_bytecode_inputs(tmp_path)
    readiness = build_launcher_update_source_regeneration_readiness(
        tmp_path,
        decompiler_command_candidates=["python"],
        decompiler_module_candidates=["pathlib"],
        recovered_bytecode_inputs=bytecode_inputs,
        generated_at=timestamp,
    )
    candidate_root = tmp_path / "generated-candidates"
    runner_preview = build_launcher_update_source_regeneration_runner_boundary_proof(
        tmp_path,
        source_regeneration_readiness_proof=readiness,
        candidate_output_root=candidate_root,
        source_regeneration_runner=_fixture_source_regeneration_runner,
        runner_label="fixture-source-regenerator",
        generated_at=timestamp,
    )
    runner_result = build_launcher_update_source_regeneration_runner_boundary_proof(
        tmp_path,
        source_regeneration_readiness_proof=readiness,
        candidate_output_root=candidate_root,
        source_regeneration_runner=_fixture_source_regeneration_runner,
        runner_label="fixture-source-regenerator",
        operator_approved_source_regeneration=True,
        operator_statement=runner_preview["required_operator_statement"],
        generated_at=timestamp,
    )
    verification_preview = (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof(
            tmp_path,
            source_regeneration_runner_boundary_proof=runner_result,
            restore_root=tmp_path,
            generated_at=timestamp,
        )
    )
    restore_preview = (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof(
            tmp_path,
            source_regeneration_runner_boundary_proof=runner_result,
            restore_root=tmp_path,
            operator_approved_candidate_verification=True,
            candidate_verification_statement=verification_preview[
                "required_candidate_verification_statement"
            ],
            generated_at=timestamp,
        )
    )
    restored = (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof(
            tmp_path,
            source_regeneration_runner_boundary_proof=runner_result,
            restore_root=tmp_path,
            operator_approved_candidate_verification=True,
            candidate_verification_statement=verification_preview[
                "required_candidate_verification_statement"
            ],
            operator_approved_restore=True,
            restore_statement=restore_preview["required_restore_statement"],
            generated_at=timestamp,
        )
    )
    return {
        "timestamp": timestamp,
        "runner_result": runner_result,
        "verification_preview": verification_preview,
        "restore_preview": restore_preview,
        "restored": restored,
    }


def _fixture_materialization_import_wrapper_removal_proof(
    tmp_path,
    timestamp="2026-05-25T00:00:00Z",
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof,
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof,
        build_launcher_update_real_authoritative_source_candidate_materialization_proof,
        build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof,
    )

    required_symbols = {
        "launcher_update_check": [
            "build_materialized_post_wrapper_regression_ready"
        ],
        "studio_shell_api": [
            "class StudioAPI",
            "get_materialized_post_wrapper_regression_ready",
        ],
        "studio_shell_test_pass10a": [
            "TestMaterializedPostWrapperRegressionReady",
            "test_materialized_post_wrapper_regression_ready",
        ],
    }

    def fixture_materializer(context):
        return {
            "ok": True,
            "runner_label": context["source_materializer_label"],
            "generated_sources": {
                "launcher_update_check": (
                    "def build_materialized_post_wrapper_regression_ready():\n"
                    "    return True\n"
                ),
                "studio_shell_api": (
                    "class StudioAPI:\n"
                    "    def get_materialized_post_wrapper_regression_ready(self):\n"
                    "        return True\n"
                ),
                "studio_shell_test_pass10a": (
                    "class TestMaterializedPostWrapperRegressionReady:\n"
                    "    def test_materialized_post_wrapper_regression_ready(self):\n"
                    "        assert True\n"
                ),
            },
        }

    target_launcher = tmp_path / "runtime" / "studio" / "launcher_update_check.py"
    target_api = tmp_path / "runtime" / "studio" / "shell" / "api.py"
    target_shell_test = (
        tmp_path / "runtime" / "studio" / "shell" / "test_pass10a_shell.py"
    )
    target_launcher.parent.mkdir(parents=True, exist_ok=True)
    target_api.parent.mkdir(parents=True, exist_ok=True)
    target_launcher.write_text(
        "_RECOVERED_BYTECODE_PATH = 'fixture'\n"
        "exec(_RECOVERED_BYTECODE_CODE, globals())\n",
        encoding="utf-8",
    )
    target_api.write_text(
        "_RECOVERED_BYTECODE_PATH = 'fixture'\n"
        "exec(_RECOVERED_BYTECODE_CODE, globals())\n",
        encoding="utf-8",
    )
    target_shell_test.write_text(
        "_RECOVERED_TEST_BYTECODE_PATH = 'fixture'\n"
        "exec(_RECOVERED_TEST_CODE, globals())\n",
        encoding="utf-8",
    )

    materialization_root = (
        tmp_path
        / ".chaseos"
        / "updates"
        / "source-candidates"
        / "operator-supplied-normal-source"
    )
    materialization_preview = (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof(
            tmp_path,
            materialization_root=materialization_root,
            source_materializer=fixture_materializer,
            source_materializer_label="fixture-source-candidate-materializer",
            required_symbols_by_role=required_symbols,
            generated_at=timestamp,
        )
    )
    materialization = (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof(
            tmp_path,
            materialization_root=materialization_root,
            source_materializer=fixture_materializer,
            source_materializer_label="fixture-source-candidate-materializer",
            required_symbols_by_role=required_symbols,
            operator_approved_candidate_materialization=True,
            operator_statement=materialization_preview["required_operator_statement"],
            allow_candidate_materialization_write=True,
            generated_at=timestamp,
        )
    )
    import_preview = (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof(
            tmp_path,
            materialization_proof=materialization,
            required_symbols_by_role=required_symbols,
            generated_at=timestamp,
        )
    )
    imported = (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof(
            tmp_path,
            materialization_proof=materialization,
            required_symbols_by_role=required_symbols,
            operator_approved_import_from_materialization=True,
            operator_statement=import_preview["required_operator_statement"],
            allow_candidate_import_write=True,
            generated_at=timestamp,
        )
    )
    supply_preview = (
        build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof(
            tmp_path,
            import_from_materialization_proof=imported,
            required_symbols_by_role=required_symbols,
            generated_at=timestamp,
        )
    )
    supply_ready = (
        build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof(
            tmp_path,
            import_from_materialization_proof=imported,
            required_symbols_by_role=required_symbols,
            operator_approved_supply_verification_from_materialization_import=True,
            operator_statement=supply_preview["required_operator_statement"],
            generated_at=timestamp,
        )
    )
    removal_preview = (
        build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof(
            tmp_path,
            supply_verification_from_materialization_import_proof=supply_ready,
            required_symbols_by_role=required_symbols,
            generated_at=timestamp,
        )
    )
    restored = (
        build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof(
            tmp_path,
            supply_verification_from_materialization_import_proof=supply_ready,
            required_symbols_by_role=required_symbols,
            allow_current_vault_source_write=True,
            operator_approved_current_vault_wrapper_removal_from_materialization_import=True,
            operator_statement=removal_preview["required_operator_statement"],
            generated_at=timestamp,
        )
    )
    return {
        "timestamp": timestamp,
        "required_symbols": required_symbols,
        "supply_ready": supply_ready,
        "removal_preview": removal_preview,
        "restored": restored,
    }


def _fixture_source_recovery_cleanup_ready_proof(vault_root, timestamp):
    from runtime.studio.launcher_update_check import _extension_digest_without

    proof = {
        "ok": True,
        "surface": "studio_launcher_update_source_recovery_cleanup_proof",
        "schema_version": "chaser.update_source_recovery_cleanup.v1",
        "status": "launcher_update_source_recovery_cleanup_ready",
        "generated_at_utc": timestamp,
        "vault_root": str(tmp_path_resolved := _Path(vault_root).resolve()),
        "errors": [],
        "warnings": [],
        "source_recovery_cleanup_ready": True,
        "recovery_artifacts_pinned": True,
        "normal_source_restored": True,
        "final_auto_update_closeout_blocked": False,
        "production_auto_update_complete": False,
        "launcher_update_check_source": {
            "path": str(tmp_path_resolved / "runtime/studio/launcher_update_check.py"),
            "wrapper_active": False,
            "hash_pinned": True,
            "recovered_artifact": {"exists": True, "sha256_matches": True},
        },
        "studio_shell_api_source": {
            "path": str(tmp_path_resolved / "runtime/studio/shell/api.py"),
            "wrapper_active": False,
            "hash_pinned": True,
            "recovered_artifact": {"exists": True, "sha256_matches": True},
        },
        "authority": {},
        "readiness": {},
    }
    proof["source_recovery_cleanup_digest_sha256"] = _extension_digest_without(
        proof,
        "source_recovery_cleanup_digest_sha256",
    )
    return proof


def _fixture_primary_relaunch_receipt_boundary_ready_proof(vault_root, timestamp):
    from runtime.studio.launcher_update_check import _extension_digest_without

    vault = _Path(vault_root).resolve()
    boundary = {
        "schema_version": "chaser.update_production_primary_relaunch_receipt_boundary.v1",
        "surface": "studio_launcher_update_production_primary_relaunch_receipt_boundary_proof",
        "generated_at_utc": timestamp,
        "helper_binary_name": "ChaseOS-Installer.exe",
        "artifact_name": "ChaseOS-Studio.exe",
        "latest_version": "9.9.9",
        "vault_root": str(vault),
        "primary_relaunch_receipt_valid": True,
        "external_helper_primary_relaunch_reported": True,
        "external_helper_primary_replacement_reported": True,
        "relaunch_performed_by_chaseos": False,
        "os_process_spawn_performed_by_chaseos": False,
        "primary_install_mutation_performed": False,
        "startup_mutation_performed": False,
        "real_executable_replacement_performed": False,
        "primary_real_executable_replacement_performed": False,
        "primary_real_executable_replacement_verified_live": False,
        "settings_install_control_exposed": False,
        "production_auto_update_complete": False,
        "requires_final_update_closeout_audit": True,
    }
    boundary["primary_relaunch_receipt_boundary_digest_sha256"] = (
        _extension_digest_without(
            boundary,
            "primary_relaunch_receipt_boundary_digest_sha256",
        )
    )
    return {
        "ok": True,
        "surface": "studio_launcher_update_production_primary_relaunch_receipt_boundary_proof",
        "schema_version": "chaser.update_production_primary_relaunch_receipt_boundary.v1",
        "status": "launcher_update_production_primary_relaunch_receipt_boundary_ready",
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "errors": [],
        "warnings": [],
        "primary_relaunch_receipt_boundary": boundary,
        "primary_relaunch_receipt_boundary_digest_sha256": boundary[
            "primary_relaunch_receipt_boundary_digest_sha256"
        ],
        "primary_relaunch_receipt_boundary_ready": True,
        "primary_relaunch_receipt_valid": True,
        "external_helper_primary_relaunch_reported": True,
        "external_helper_primary_replacement_reported": True,
        "relaunch_performed_by_chaseos": False,
        "os_process_spawn_performed_by_chaseos": False,
        "primary_install_mutation_performed": False,
        "startup_mutation_performed": False,
        "real_executable_replacement_performed": False,
        "primary_real_executable_replacement_performed": False,
        "primary_real_executable_replacement_verified_live": False,
        "settings_install_control_exposed": False,
        "production_auto_update_complete": False,
        "requires_final_update_closeout_audit": True,
        "authority": {},
        "readiness": {},
    }


def _fixture_final_production_auto_update_live_completion_evidence(
    vault_root,
    timestamp,
):
    from runtime.studio.launcher_update_check import _extension_digest_without

    vault = _Path(vault_root).resolve()
    evidence = {
        "surface": "external_chaseos_production_auto_update_live_completion_evidence",
        "schema_version": "chaser.external_production_auto_update_live_completion_evidence.v1",
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "github_release_publication_verified": True,
        "live_release_manifest_readback_verified": True,
        "release_manifest_signature_verified": True,
        "live_binary_download_verified": True,
        "downloaded_artifact_signature_verified": True,
        "chaseos_installer_signed_output_verified": True,
        "operator_digest_approval_verified": True,
        "prompted_install_flow_verified": True,
        "chaseos_installer_launch_receipt_verified": True,
        "primary_exe_replacement_verified_live": True,
        "primary_relaunch_verified_live": True,
        "rollback_audit_receipt_verified": True,
        "startup_background_prompt_verified": True,
        "installed_version_matches_manifest": True,
        "silent_install_performed": False,
        "secrets_or_private_keys_read_by_chaseos": False,
        "source_write_performed_by_final_audit": False,
        "primary_replacement_performed_by_final_audit": False,
        "github_mutation_performed_by_final_audit": False,
        "download_performed_by_final_audit": False,
        "installer_launch_performed_by_final_audit": False,
    }
    evidence["final_production_auto_update_live_evidence_digest_sha256"] = (
        _extension_digest_without(
            evidence,
            "final_production_auto_update_live_evidence_digest_sha256",
        )
    )
    return evidence


def _fixture_final_production_auto_update_live_completion_claims(
    vault_root,
    timestamp,
):
    claims = _fixture_final_production_auto_update_live_completion_evidence(
        vault_root,
        timestamp,
    )
    for key in [
        "surface",
        "schema_version",
        "generated_at_utc",
        "vault_root",
        "final_production_auto_update_live_evidence_digest_sha256",
    ]:
        claims.pop(key, None)
    return claims


def _fixture_controlled_live_installer_evidence_runner(claims):
    def runner(context):
        assert context["target_artifact"] == "ChaseOS-Studio.exe"
        assert context["helper_binary_name"] == "ChaseOS-Installer.exe"
        assert context["operator_allowed_live_actions"]["live_release_readback"] is True
        assert context["operator_allowed_live_actions"]["live_download"] is True
        assert context["operator_allowed_live_actions"]["installer_launch"] is True
        assert context["operator_allowed_live_actions"]["primary_replacement"] is True
        assert (
            context["operator_allowed_live_actions"]["startup_prompt_verification"]
            is True
        )
        return {
            "ok": True,
            "status": "fixture_controlled_live_evidence_collected",
            "runner_label": context["runner_label"],
            "helper_binary_name": "ChaseOS-Installer.exe",
            "artifact_name": "ChaseOS-Studio.exe",
            "latest_version": "99.99.99",
            "download_performed_by_runner": True,
            "installer_launch_performed_by_runner": True,
            "primary_replacement_performed_by_runner": True,
            "primary_relaunch_performed_by_runner": True,
            "startup_prompt_verified_by_runner": True,
            "evidence_claims": dict(claims),
            "receipt_artifacts": {
                "manifest_readback_sha256": "manifest-readback-fixture-sha256",
                "downloaded_artifact_sha256": "downloaded-artifact-fixture-sha256",
                "installer_receipt_sha256": "installer-receipt-fixture-sha256",
                "rollback_receipt_sha256": "rollback-receipt-fixture-sha256",
            },
        }

    return runner


def _fixture_approved_live_evidence_adapter_source_proofs(vault_root, timestamp):
    from runtime.studio.launcher_update_check import _extension_digest_without

    vault = _Path(vault_root).resolve()

    def proof_with_digest(surface, digest_key, **values):
        proof = {
            "ok": True,
            "surface": surface,
            "schema_version": f"{surface}.fixture.v1",
            "status": f"{surface}_ready",
            "generated_at_utc": timestamp,
            "vault_root": str(vault),
            "errors": [],
            "warnings": [],
            "artifact_name": "ChaseOS-Studio.exe",
            "latest_version": "9.9.9",
        }
        proof.update(values)
        proof[digest_key] = _extension_digest_without(proof, digest_key)
        return proof

    return {
        "signed_release_manifest_live_readback": proof_with_digest(
            "studio_launcher_update_signed_release_manifest_live_readback_proof",
            "signed_release_manifest_live_readback_digest_sha256",
            published_manifest_url="https://example.invalid/chaseos/update-manifest.json",
            github_release_publication_verified=True,
            live_release_manifest_readback_verified=True,
            release_manifest_signature_verified=True,
        ),
        "signed_manifest_approved_live_download_staging": proof_with_digest(
            "studio_launcher_update_signed_manifest_approved_live_download_staging_proof",
            "signed_manifest_approved_live_download_staging_digest_sha256",
            live_binary_download_verified=True,
            downloaded_artifact_path=str(vault / "tmp" / "ChaseOS-Studio.exe"),
        ),
        "signed_manifest_downloaded_staged_signature_verification": proof_with_digest(
            "studio_launcher_update_signed_manifest_downloaded_staged_signature_verification_proof",
            "signed_manifest_downloaded_staged_signature_verification_digest_sha256",
            downloaded_artifact_signature_verified=True,
        ),
        "installer_real_build_signed_output_verification": proof_with_digest(
            "studio_launcher_update_installer_real_build_signed_output_verification_proof",
            "real_build_signed_output_verification_digest_sha256",
            helper_binary_name="ChaseOS-Installer.exe",
            chaseos_installer_signed_output_verified=True,
        ),
        "production_primary_relaunch_receipt_boundary": _fixture_primary_relaunch_receipt_boundary_ready_proof(
            vault,
            timestamp,
        ),
        "startup_background_prompt_from_signed_manifest_execution_dry_run": proof_with_digest(
            "studio_launcher_update_startup_background_prompt_from_signed_manifest_execution_dry_run_proof",
            "prompt_readiness_digest_sha256",
            startup_background_prompt_verified=True,
            prompted_install_flow_verified=True,
        ),
    }


def _fixture_real_live_receipt_bundle(vault_root, timestamp, source_proofs=None):
    from runtime.studio.launcher_update_check import _extension_digest_without

    vault = _Path(vault_root).resolve()
    bundle = {
        "surface": "external_chaseos_real_live_updater_receipt_bundle",
        "schema_version": "chaser.external_real_live_updater_receipt_bundle.v1",
        "generated_at_utc": timestamp,
        "vault_root": str(vault),
        "target_artifact": "ChaseOS-Studio.exe",
        "helper_binary_name": "ChaseOS-Installer.exe",
        "receipt_source": "operator_supplied_real_live_receipts",
        "source_proofs": source_proofs
        or _fixture_approved_live_evidence_adapter_source_proofs(vault, timestamp),
        "download_performed_by_this_boundary": False,
        "installer_launch_performed_by_this_boundary": False,
        "primary_replacement_performed_by_this_boundary": False,
        "startup_mutation_performed_by_this_boundary": False,
        "settings_install_control_exposed": False,
        "secrets_or_private_keys_included": False,
    }
    bundle["real_live_receipt_bundle_digest_sha256"] = _extension_digest_without(
        bundle,
        "real_live_receipt_bundle_digest_sha256",
    )
    return bundle


def _fixture_real_live_receipt_bundle_production_runner():
    def runner(context):
        bundle = _fixture_real_live_receipt_bundle(
            context["vault_root"],
            context["generated_at_utc"],
        )
        return {
            "ok": True,
            "status": "real_live_receipt_bundle_production_runner_ready",
            "runner_label": context["runner_label"],
            "live_receipt_bundle": bundle,
            "download_performed_by_runner": True,
            "installer_launch_performed_by_runner": True,
            "primary_replacement_performed_by_runner": True,
            "primary_relaunch_performed_by_runner": True,
            "startup_prompt_verified_by_runner": True,
        }

    return runner


def _fixture_production_primary_closeout_after_source_recovery_ready(tmp_path):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof,
        build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof,
        build_launcher_update_production_primary_closeout_after_source_recovery_proof,
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement,
    )

    fixture = _fixture_materialization_import_wrapper_removal_proof(tmp_path)
    preview = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        generated_at=fixture["timestamp"],
    )
    regression_evidence = _fixture_regression_evidence(
        preview["regression_command_plan"]
    )
    pending = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        regression_evidence=regression_evidence,
        generated_at=fixture["timestamp"],
    )
    required_statement = (
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement(
            pending[
                "post_wrapper_removal_regression_from_materialization_import_plan"
            ]
        )
    )
    regression = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        regression_evidence=regression_evidence,
        operator_approved_post_wrapper_removal_regression=True,
        operator_statement=required_statement,
        generated_at=fixture["timestamp"],
    )
    source_closeout = build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof(
        tmp_path,
        post_wrapper_removal_regression_from_materialization_import_proof=regression,
        source_recovery_cleanup_proof=_fixture_source_recovery_cleanup_ready_proof(
            tmp_path,
            fixture["timestamp"],
        ),
        generated_at=fixture["timestamp"],
    )
    primary_closeout = build_launcher_update_production_primary_closeout_after_source_recovery_proof(
        tmp_path,
        current_vault_source_closeout_from_materialization_import_regression_proof=source_closeout,
        production_primary_relaunch_receipt_boundary_proof=_fixture_primary_relaunch_receipt_boundary_ready_proof(
            tmp_path,
            fixture["timestamp"],
        ),
        generated_at=fixture["timestamp"],
    )
    return primary_closeout, fixture["timestamp"]


def test_launcher_update_source_regeneration_runner_boundary_blocks_default_execution(tmp_path):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_source_regeneration_runner_boundary_proof,
    )

    result = build_launcher_update_source_regeneration_runner_boundary_proof(tmp_path)

    assert result["ok"] is False, result["errors"]
    assert (
        result["status"]
        == "launcher_update_source_regeneration_runner_boundary_blocked"
    )
    assert result["runner_execution_performed"] is False
    assert result["source_regeneration_execution_performed"] is False
    assert result["source_regeneration_output_written"] is False
    assert result["source_write_performed"] is False
    assert result["live_source_write_performed"] is False
    assert result["source_restore_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert "source_regeneration_readiness_not_ready" in result["errors"]
    assert "candidate_output_root_required" in result["errors"]
    assert "source_regeneration_runner_required" in result["errors"]
    assert "operator_source_regeneration_approval_required" in result["errors"]


def test_launcher_update_source_regeneration_runner_boundary_writes_fixture_candidates_after_digest_approval(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_source_regeneration_readiness,
        build_launcher_update_source_regeneration_runner_boundary_proof,
        required_update_source_regeneration_runner_operator_statement,
    )

    bytecode_inputs = _fixture_source_regeneration_bytecode_inputs(tmp_path)
    readiness = build_launcher_update_source_regeneration_readiness(
        tmp_path,
        decompiler_command_candidates=["python"],
        decompiler_module_candidates=["pathlib"],
        recovered_bytecode_inputs=bytecode_inputs,
    )
    assert readiness["ok"] is True

    candidate_root = tmp_path / "generated-candidates"
    pending = build_launcher_update_source_regeneration_runner_boundary_proof(
        tmp_path,
        source_regeneration_readiness_proof=readiness,
        candidate_output_root=candidate_root,
        source_regeneration_runner=_fixture_source_regeneration_runner,
        runner_label="fixture-source-regenerator",
    )

    assert (
        pending["status"]
        == "launcher_update_source_regeneration_runner_boundary_pending_approval"
    )
    assert pending["runner_execution_performed"] is False
    assert pending["source_regeneration_output_written"] is False
    assert pending["required_operator_statement"] == (
        required_update_source_regeneration_runner_operator_statement(
            pending["execution_plan"]
        )
    )

    result = build_launcher_update_source_regeneration_runner_boundary_proof(
        tmp_path,
        source_regeneration_readiness_proof=readiness,
        candidate_output_root=candidate_root,
        source_regeneration_runner=_fixture_source_regeneration_runner,
        runner_label="fixture-source-regenerator",
        operator_approved_source_regeneration=True,
        operator_statement=pending["required_operator_statement"],
    )

    assert result["ok"] is True, result["errors"]
    assert result["status"] == "launcher_update_source_regeneration_runner_candidates_written"
    assert result["runner_execution_performed"] is True
    assert result["source_regeneration_execution_performed"] is True
    assert result["source_regeneration_output_written"] is True
    assert result["candidate_source_write_performed"] is True
    assert result["source_write_performed"] is True
    assert result["live_source_write_performed"] is False
    assert result["source_restore_performed"] is False
    assert result["source_file_replacement_performed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["installer_launch_performed"] is False
    assert result["helper_launch_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert result["candidate_set_complete"] is True
    assert (
        result["candidate_verification_preview"]["status"]
        == "launcher_update_normal_source_candidate_verification_pending_approval"
    )
    for role, paths in result["generated_candidate_paths"].items():
        assert paths
        assert _Path(paths[0]).exists()
        assert result["generated_candidates"][role]["sha256"]


def test_launcher_update_source_regeneration_candidate_restore_chain_blocks_default_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof,
    )

    result = build_launcher_update_source_regeneration_candidate_verification_restore_proof(
        tmp_path
    )

    assert result["ok"] is False
    assert (
        result["status"]
        == "launcher_update_source_regeneration_candidate_restore_blocked"
    )
    assert result["runner_candidates_written"] is False
    assert result["candidate_verification_ready"] is False
    assert result["restore_plan_ready"] is False
    assert result["source_regeneration_execution_performed"] is False
    assert result["source_regeneration_output_written"] is False
    assert result["source_restore_performed"] is False
    assert result["source_write_performed"] is False
    assert result["live_source_write_performed"] is False
    assert result["source_file_replacement_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert "source_regeneration_runner_candidates_required" in result["errors"]


def test_launcher_update_source_regeneration_candidate_restore_chain_restores_fixture_candidates_after_dual_approval(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof,
        build_launcher_update_source_regeneration_readiness,
        build_launcher_update_source_regeneration_runner_boundary_proof,
    )

    timestamp = "2026-05-25T00:00:00Z"
    bytecode_inputs = _fixture_source_regeneration_bytecode_inputs(tmp_path)
    readiness = build_launcher_update_source_regeneration_readiness(
        tmp_path,
        decompiler_command_candidates=["python"],
        decompiler_module_candidates=["pathlib"],
        recovered_bytecode_inputs=bytecode_inputs,
        generated_at=timestamp,
    )
    candidate_root = tmp_path / "generated-candidates"
    runner_preview = build_launcher_update_source_regeneration_runner_boundary_proof(
        tmp_path,
        source_regeneration_readiness_proof=readiness,
        candidate_output_root=candidate_root,
        source_regeneration_runner=_fixture_source_regeneration_runner,
        runner_label="fixture-source-regenerator",
        generated_at=timestamp,
    )
    runner_result = build_launcher_update_source_regeneration_runner_boundary_proof(
        tmp_path,
        source_regeneration_readiness_proof=readiness,
        candidate_output_root=candidate_root,
        source_regeneration_runner=_fixture_source_regeneration_runner,
        runner_label="fixture-source-regenerator",
        operator_approved_source_regeneration=True,
        operator_statement=runner_preview["required_operator_statement"],
        generated_at=timestamp,
    )
    assert runner_result["ok"] is True

    restore_root = tmp_path / "restore-root"
    verification_preview = (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof(
            tmp_path,
            source_regeneration_runner_boundary_proof=runner_result,
            restore_root=restore_root,
            generated_at=timestamp,
        )
    )

    assert (
        verification_preview["status"]
        == "launcher_update_source_regeneration_candidate_restore_pending_candidate_verification_approval"
    )
    assert verification_preview["candidate_set_complete"] is True
    assert verification_preview["candidate_verification_ready"] is False
    assert verification_preview["required_candidate_verification_statement"]
    assert (
        "source_regeneration_candidate_verification_approval_required"
        in verification_preview["errors"]
    )

    restore_preview = (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof(
            tmp_path,
            source_regeneration_runner_boundary_proof=runner_result,
            restore_root=restore_root,
            operator_approved_candidate_verification=True,
            candidate_verification_statement=verification_preview[
                "required_candidate_verification_statement"
            ],
            generated_at=timestamp,
        )
    )

    assert (
        restore_preview["status"]
        == "launcher_update_source_regeneration_candidate_restore_pending_restore_approval"
    )
    assert restore_preview["candidate_verification_ready"] is True
    assert restore_preview["restore_plan_ready"] is True
    assert restore_preview["required_restore_statement"]
    assert (
        "source_regeneration_candidate_restore_approval_required"
        in restore_preview["errors"]
    )

    restored = (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof(
            tmp_path,
            source_regeneration_runner_boundary_proof=runner_result,
            restore_root=restore_root,
            operator_approved_candidate_verification=True,
            candidate_verification_statement=verification_preview[
                "required_candidate_verification_statement"
            ],
            operator_approved_restore=True,
            restore_statement=restore_preview["required_restore_statement"],
            generated_at=timestamp,
        )
    )

    assert restored["ok"] is True
    assert (
        restored["status"]
        == "launcher_update_source_regeneration_candidate_restore_fixture_restored"
    )
    assert restored["runner_boundary_digest_matched"] is True
    assert restored["candidate_verification_ready"] is True
    assert restored["restore_plan_ready"] is True
    assert restored["source_restore_performed"] is True
    assert restored["source_write_performed"] is True
    assert restored["live_source_write_performed"] is False
    assert restored["source_file_replacement_performed"] is True
    assert restored["source_regeneration_execution_performed"] is False
    assert restored["decompiler_execution_performed"] is False
    assert restored["candidate_source_execution_performed"] is False
    assert restored["installer_launch_performed"] is False
    assert restored["helper_launch_performed"] is False
    assert restored["primary_exe_replacement_performed"] is False
    assert restored["production_auto_update_complete"] is False
    assert restored["final_auto_update_closeout_blocked"] is True
    for role, paths in runner_result["generated_candidate_paths"].items():
        candidate_path = _Path(paths[0])
        target = restored["restore_executor_proof"]["restore_plan"]["role_plan"][role][
            "target"
        ]
        assert _Path(target["resolved_target_path"]).read_text(
            encoding="utf-8"
        ) == candidate_path.read_text(encoding="utf-8")


def test_launcher_update_source_regeneration_live_source_restoration_closeout_blocks_default_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_source_regeneration_live_source_restoration_closeout_proof,
    )

    result = (
        build_launcher_update_source_regeneration_live_source_restoration_closeout_proof(
            tmp_path
        )
    )

    assert result["ok"] is False
    assert (
        result["status"]
        == "launcher_update_source_regeneration_live_source_restoration_closeout_blocked"
    )
    assert result["live_restore_proof_ready"] is False
    assert result["wrapper_removal_verified"] is False
    assert result["live_source_restoration_verified"] is False
    assert result["source_restore_performed"] is False
    assert result["source_write_performed"] is False
    assert result["live_source_write_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert "source_regeneration_candidate_restore_proof_not_live" in result["errors"]


def test_launcher_update_source_regeneration_live_source_restoration_closeout_verifies_live_fixture_root(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof,
        build_launcher_update_source_regeneration_live_source_restoration_closeout_proof,
        build_launcher_update_source_regeneration_readiness,
        build_launcher_update_source_regeneration_runner_boundary_proof,
    )

    timestamp = "2026-05-25T00:00:00Z"
    bytecode_inputs = _fixture_source_regeneration_bytecode_inputs(tmp_path)
    readiness = build_launcher_update_source_regeneration_readiness(
        tmp_path,
        decompiler_command_candidates=["python"],
        decompiler_module_candidates=["pathlib"],
        recovered_bytecode_inputs=bytecode_inputs,
        generated_at=timestamp,
    )
    candidate_root = tmp_path / "generated-candidates"
    runner_preview = build_launcher_update_source_regeneration_runner_boundary_proof(
        tmp_path,
        source_regeneration_readiness_proof=readiness,
        candidate_output_root=candidate_root,
        source_regeneration_runner=_fixture_source_regeneration_runner,
        runner_label="fixture-source-regenerator",
        generated_at=timestamp,
    )
    runner_result = build_launcher_update_source_regeneration_runner_boundary_proof(
        tmp_path,
        source_regeneration_readiness_proof=readiness,
        candidate_output_root=candidate_root,
        source_regeneration_runner=_fixture_source_regeneration_runner,
        runner_label="fixture-source-regenerator",
        operator_approved_source_regeneration=True,
        operator_statement=runner_preview["required_operator_statement"],
        generated_at=timestamp,
    )
    verification_preview = (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof(
            tmp_path,
            source_regeneration_runner_boundary_proof=runner_result,
            restore_root=tmp_path,
            generated_at=timestamp,
        )
    )
    restore_preview = (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof(
            tmp_path,
            source_regeneration_runner_boundary_proof=runner_result,
            restore_root=tmp_path,
            operator_approved_candidate_verification=True,
            candidate_verification_statement=verification_preview[
                "required_candidate_verification_statement"
            ],
            generated_at=timestamp,
        )
    )
    restored = (
        build_launcher_update_source_regeneration_candidate_verification_restore_proof(
            tmp_path,
            source_regeneration_runner_boundary_proof=runner_result,
            restore_root=tmp_path,
            operator_approved_candidate_verification=True,
            candidate_verification_statement=verification_preview[
                "required_candidate_verification_statement"
            ],
            operator_approved_restore=True,
            restore_statement=restore_preview["required_restore_statement"],
            generated_at=timestamp,
        )
    )

    assert restored["ok"] is True
    assert (
        restored["status"]
        == "launcher_update_source_regeneration_candidate_restore_live_source_restored"
    )
    assert restored["live_source_write_performed"] is True

    result = (
        build_launcher_update_source_regeneration_live_source_restoration_closeout_proof(
            tmp_path,
            source_regeneration_candidate_restore_proof=restored,
            generated_at=timestamp,
        )
    )

    assert result["ok"] is True, result["errors"]
    assert (
        result["status"]
        == "launcher_update_source_regeneration_live_source_restoration_closeout_verified"
    )
    assert result["source_regeneration_candidate_restore_digest_matched"] is True
    assert result["live_restore_proof_ready"] is True
    assert result["wrapper_removal_verified"] is True
    assert result["live_source_restoration_verified"] is True
    assert result["source_restore_performed"] is False
    assert result["source_write_performed"] is False
    assert result["live_source_write_performed"] is False
    assert result["source_restore_previously_performed"] is True
    assert result["source_write_previously_performed"] is True
    assert result["live_source_write_previously_performed"] is True
    assert result["primary_exe_replacement_performed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    for descriptor in result["target_readiness"].values():
        assert descriptor["live_source_file_ready"] is True
        assert descriptor["recovery_wrapper_present"] is False


def test_launcher_update_real_source_restoration_execution_regression_boundary_blocks_default_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_source_restoration_execution_regression_boundary_proof,
    )

    result = build_launcher_update_real_source_restoration_execution_regression_boundary_proof(
        tmp_path
    )

    assert result["ok"] is False
    assert (
        result["status"]
        == "launcher_update_real_source_restoration_execution_regression_boundary_blocked"
    )
    assert result["real_source_restore_attempted"] is False
    assert result["real_source_restore_performed"] is False
    assert result["live_source_restoration_closeout_verified"] is False
    assert result["regression_evidence_required"] is False
    assert result["regression_evidence_verified"] is False
    assert result["regression_commands_executed_by_chaseos"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert "real_source_restore_evidence_required" in result["errors"]
    assert "live_source_restoration_closeout_verification_required" in result["errors"]


def test_launcher_update_real_source_restoration_execution_regression_boundary_waits_for_regression_evidence(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_source_restoration_execution_regression_boundary_proof,
    )

    fixture = _fixture_live_source_restoration_proof(tmp_path)
    result = build_launcher_update_real_source_restoration_execution_regression_boundary_proof(
        tmp_path,
        source_regeneration_candidate_restore_proof=fixture["restored"],
        generated_at=fixture["timestamp"],
    )

    assert result["ok"] is False
    assert (
        result["status"]
        == "launcher_update_real_source_restoration_execution_restored_pending_regression_evidence"
    )
    assert result["source_regeneration_candidate_restore_digest_matched"] is True
    assert (
        result[
            "source_regeneration_live_source_restoration_closeout_digest_matched"
        ]
        is True
    )
    assert result["real_source_restore_attempted"] is True
    assert result["real_source_restore_performed"] is True
    assert result["live_source_restoration_closeout_verified"] is True
    assert result["regression_evidence_required"] is True
    assert result["regression_evidence_verified"] is False
    assert result["regression_commands_executed_by_chaseos"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["production_auto_update_complete"] is False
    assert (
        "real_source_restoration_regression_evidence_required"
        in result["errors"]
    )


def test_launcher_update_real_source_restoration_execution_regression_boundary_verifies_supplied_regression_evidence(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_source_restoration_execution_regression_boundary_proof,
    )

    fixture = _fixture_live_source_restoration_proof(tmp_path)
    preview = build_launcher_update_real_source_restoration_execution_regression_boundary_proof(
        tmp_path,
        source_regeneration_candidate_restore_proof=fixture["restored"],
        generated_at=fixture["timestamp"],
    )
    evidence = _fixture_regression_evidence(preview["regression_command_plan"])
    result = build_launcher_update_real_source_restoration_execution_regression_boundary_proof(
        tmp_path,
        source_regeneration_candidate_restore_proof=fixture["restored"],
        regression_evidence=evidence,
        generated_at=fixture["timestamp"],
    )

    assert result["ok"] is True
    assert (
        result["status"]
        == "launcher_update_real_source_restoration_execution_regression_verified"
    )
    assert result["real_source_restore_performed"] is True
    assert result["live_source_restoration_closeout_verified"] is True
    assert result["regression_evidence_required"] is True
    assert result["regression_evidence_verified"] is True
    assert result["regression_commands_executed_by_chaseos"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_primary_real_exe_enabled"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True


def test_launcher_update_current_vault_source_restoration_closeout_readiness_blocks_default_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_source_restoration_closeout_readiness,
    )

    result = build_launcher_update_current_vault_source_restoration_closeout_readiness(
        tmp_path
    )

    assert result["ok"] is False
    assert (
        result["status"]
        == "launcher_update_current_vault_source_restoration_closeout_blocked"
    )
    assert result["real_source_restoration_regression_boundary_verified"] is False
    assert result["source_recovery_cleanup_ready"] is False
    assert result["current_vault_wrappers_removed"] is False
    assert result["current_vault_source_restoration_closeout_ready"] is False
    assert result["source_restoration_closeout_ready_for_primary_exe_resume"] is False
    assert result["regression_commands_executed_by_chaseos"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert "real_source_restoration_regression_boundary_not_verified" in result["errors"]
    assert "source_recovery_cleanup_not_ready" in result["errors"]


def test_launcher_update_current_vault_source_restoration_closeout_readiness_verifies_supplied_ready_evidence(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_source_restoration_closeout_readiness,
        build_launcher_update_real_source_restoration_execution_regression_boundary_proof,
    )

    fixture = _fixture_live_source_restoration_proof(tmp_path)
    preview = build_launcher_update_real_source_restoration_execution_regression_boundary_proof(
        tmp_path,
        source_regeneration_candidate_restore_proof=fixture["restored"],
        generated_at=fixture["timestamp"],
    )
    boundary = build_launcher_update_real_source_restoration_execution_regression_boundary_proof(
        tmp_path,
        source_regeneration_candidate_restore_proof=fixture["restored"],
        regression_evidence=_fixture_regression_evidence(
            preview["regression_command_plan"]
        ),
        generated_at=fixture["timestamp"],
    )
    cleanup = _fixture_source_recovery_cleanup_ready_proof(
        tmp_path,
        fixture["timestamp"],
    )

    result = build_launcher_update_current_vault_source_restoration_closeout_readiness(
        tmp_path,
        real_source_restoration_execution_regression_boundary_proof=boundary,
        source_recovery_cleanup_proof=cleanup,
        generated_at=fixture["timestamp"],
    )

    assert result["ok"] is True
    assert (
        result["status"]
        == "launcher_update_current_vault_source_restoration_closeout_ready"
    )
    assert result["real_source_restoration_regression_boundary_digest_matched"] is True
    assert result["source_recovery_cleanup_digest_matched"] is True
    assert result["real_source_restoration_regression_boundary_verified"] is True
    assert result["source_recovery_cleanup_ready"] is True
    assert result["current_vault_wrappers_removed"] is True
    assert result["current_vault_source_restoration_closeout_ready"] is True
    assert result["source_restoration_closeout_ready_for_primary_exe_resume"] is True
    assert result["regression_commands_executed_by_chaseos"] is False
    assert result["source_write_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_primary_real_exe_enabled"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True


def test_launcher_update_source_candidate_inventory_wrapper_removal_preflight_reports_current_blockers():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_source_candidate_inventory_wrapper_removal_preflight,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = build_launcher_update_source_candidate_inventory_wrapper_removal_preflight(
        vault_root
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_source_candidate_inventory_wrapper_removal_preflight"
    )
    assert (
        result["status"]
        == "launcher_update_source_candidate_inventory_authoritative_candidates_missing"
    )
    assert result["source_recovery_artifacts_pinned"] is True
    assert result["current_vault_wrappers_active"] is True
    assert result["launcher_update_check_wrapper_active"] is True
    assert result["studio_shell_api_wrapper_active"] is True
    assert result["authoritative_source_candidates_available"] is False
    assert result["wrapper_removal_plan_ready"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert "launcher_update_check_wrapper_active" in result["errors"]
    assert "studio_shell_api_wrapper_active" in result["errors"]
    assert (
        "launcher_update_check_authoritative_source_candidate_missing"
        in result["errors"]
    )
    assert (
        "studio_shell_api_authoritative_source_candidate_missing"
        in result["errors"]
    )
    assert (
        "current_vault_recovery_wrapper_source"
        in result["role_candidate_classes"]["launcher_update_check"]
    )
    assert (
        "current_vault_recovery_wrapper_source"
        in result["role_candidate_classes"]["studio_shell_api"]
    )


def test_launcher_update_source_candidate_inventory_wrapper_removal_preflight_accepts_verified_candidates(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_source_candidate_inventory_wrapper_removal_preflight,
    )

    candidate_root = tmp_path / "candidates"
    launcher_candidate = candidate_root / "launcher_update_check.py"
    api_candidate = candidate_root / "api.py"
    shell_test_candidate = candidate_root / "test_pass10a_shell.py"
    launcher_candidate.parent.mkdir(parents=True, exist_ok=True)
    launcher_candidate.write_text(
        "def build_inventory_ready():\n    return True\n",
        encoding="utf-8",
    )
    api_candidate.write_text(
        "class StudioAPI:\n"
        "    def get_inventory_ready(self):\n"
        "        return True\n",
        encoding="utf-8",
    )
    shell_test_candidate.write_text(
        "class TestInventoryReady:\n"
        "    def test_inventory_ready(self):\n"
        "        assert True\n",
        encoding="utf-8",
    )
    required_symbols = {
        "launcher_update_check": ["build_inventory_ready"],
        "studio_shell_api": ["class StudioAPI", "get_inventory_ready"],
        "studio_shell_test_pass10a": [
            "TestInventoryReady",
            "test_inventory_ready",
        ],
    }

    result = build_launcher_update_source_candidate_inventory_wrapper_removal_preflight(
        tmp_path,
        candidate_paths={
            "launcher_update_check": [launcher_candidate],
            "studio_shell_api": [api_candidate],
            "studio_shell_test_pass10a": [shell_test_candidate],
        },
        required_symbols_by_role=required_symbols,
    )

    assert result["ok"] is True
    assert (
        result["status"]
        == "launcher_update_source_candidate_inventory_wrapper_removal_preflight_ready"
    )
    assert result["authoritative_source_candidates_available"] is True
    assert result["wrapper_removal_plan_ready"] is True
    assert result["role_readiness"] == {
        "launcher_update_check": True,
        "studio_shell_api": True,
        "studio_shell_test_pass10a": True,
    }
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False


def test_launcher_update_authoritative_normal_source_candidate_supply_packet_reports_missing_candidates(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_authoritative_normal_source_candidate_supply_packet,
    )

    result = build_launcher_update_authoritative_normal_source_candidate_supply_packet(
        tmp_path,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_authoritative_normal_source_candidate_supply_packet"
    )
    assert (
        result["status"]
        == "launcher_update_authoritative_normal_source_candidate_supply_blocked"
    )
    assert result["candidate_supply_packet_ready"] is False
    assert result["ready_for_candidate_verifier"] is False
    assert result["authoritative_source_candidates_available"] is False
    assert result["current_vault_wrappers_active"] is True
    assert "authoritative_normal_source_candidates_missing" in result["errors"]
    assert "operator_candidate_supply_approval_required" in result["errors"]
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    expected_launcher = (
        tmp_path
        / ".chaseos"
        / "updates"
        / "source-candidates"
        / "authoritative-normal-source"
        / "runtime"
        / "studio"
        / "launcher_update_check.py"
    )
    assert result["candidate_paths"]["launcher_update_check"] == [
        str(expected_launcher.resolve())
    ]
    assert (
        result["candidate_supply_contract"]["source_write_allowed"] is False
    )


def test_launcher_update_authoritative_normal_source_candidate_supply_packet_accepts_verified_candidates_after_statement(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_authoritative_normal_source_candidate_supply_packet,
        required_update_authoritative_normal_source_candidate_supply_operator_statement,
    )

    candidate_root = tmp_path / "authoritative"
    launcher_candidate = candidate_root / "launcher_update_check.py"
    api_candidate = candidate_root / "api.py"
    shell_test_candidate = candidate_root / "test_pass10a_shell.py"
    launcher_candidate.parent.mkdir(parents=True, exist_ok=True)
    launcher_candidate.write_text(
        "def build_supply_ready():\n    return True\n",
        encoding="utf-8",
    )
    api_candidate.write_text(
        "class StudioAPI:\n"
        "    def get_supply_ready(self):\n"
        "        return True\n",
        encoding="utf-8",
    )
    shell_test_candidate.write_text(
        "class TestSupplyReady:\n"
        "    def test_supply_ready(self):\n"
        "        assert True\n",
        encoding="utf-8",
    )
    candidate_paths = {
        "launcher_update_check": [launcher_candidate],
        "studio_shell_api": [api_candidate],
        "studio_shell_test_pass10a": [shell_test_candidate],
    }
    required_symbols = {
        "launcher_update_check": ["build_supply_ready"],
        "studio_shell_api": ["class StudioAPI", "get_supply_ready"],
        "studio_shell_test_pass10a": ["TestSupplyReady", "test_supply_ready"],
    }
    generated_at = "2026-05-25T00:00:00Z"

    preview = build_launcher_update_authoritative_normal_source_candidate_supply_packet(
        tmp_path,
        candidate_paths=candidate_paths,
        required_symbols_by_role=required_symbols,
        generated_at=generated_at,
    )

    assert preview["status"] == (
        "launcher_update_authoritative_normal_source_candidate_supply_"
        "pending_approval"
    )
    assert preview["authoritative_source_candidates_available"] is True
    assert preview["operator_statement_matched"] is False

    statement = (
        required_update_authoritative_normal_source_candidate_supply_operator_statement(
            preview["candidate_supply_contract"]
        )
    )
    approved = build_launcher_update_authoritative_normal_source_candidate_supply_packet(
        tmp_path,
        candidate_paths=candidate_paths,
        required_symbols_by_role=required_symbols,
        operator_approved_candidate_supply=True,
        operator_statement=statement,
        generated_at=generated_at,
    )

    assert approved["ok"] is True
    assert approved["status"] == (
        "launcher_update_authoritative_normal_source_candidate_supply_"
        "ready_for_verifier"
    )
    assert approved["operator_statement_matched"] is True
    assert approved["candidate_supply_packet_ready"] is True
    assert approved["ready_for_candidate_verifier"] is True
    assert approved["source_candidate_inventory"]["wrapper_removal_plan_ready"] is True
    assert approved["source_write_performed"] is False
    assert approved["wrapper_removal_performed"] is False
    assert approved["primary_exe_replacement_performed"] is False
    assert approved["settings_write_control_exposed"] is False
    assert approved["production_auto_update_complete"] is False


def test_launcher_update_authoritative_source_candidate_import_boundary_blocks_default_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_authoritative_source_candidate_import_boundary_proof,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = build_launcher_update_authoritative_source_candidate_import_boundary_proof(
        vault_root
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_authoritative_source_candidate_import_boundary_proof"
    )
    assert (
        result["status"]
        == "launcher_update_authoritative_source_candidate_import_blocked"
    )
    assert result["candidate_import_plan_ready"] is False
    assert result["candidate_import_write_enabled"] is False
    assert result["candidate_import_write_performed"] is False
    assert result["candidate_import_performed"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert (
        "operator_authoritative_source_candidate_import_approval_required"
        in result["errors"]
    )
    assert any(
        error.endswith("_import_plan_invalid") for error in result["errors"]
    )


def test_launcher_update_authoritative_source_candidate_import_boundary_imports_candidates_after_exact_approval(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_authoritative_source_candidate_import_boundary_proof,
        required_update_authoritative_source_candidate_import_operator_statement,
    )

    incoming_root = tmp_path / "incoming-authoritative-source"
    launcher_candidate = incoming_root / "launcher_update_check.py"
    api_candidate = incoming_root / "api.py"
    shell_test_candidate = incoming_root / "test_pass10a_shell.py"
    launcher_candidate.parent.mkdir(parents=True, exist_ok=True)
    launcher_candidate.write_text(
        "def build_authoritative_import_ready():\n    return True\n",
        encoding="utf-8",
    )
    api_candidate.write_text(
        "class StudioAPI:\n"
        "    def get_authoritative_import_ready(self):\n"
        "        return True\n",
        encoding="utf-8",
    )
    shell_test_candidate.write_text(
        "class TestAuthoritativeImportReady:\n"
        "    def test_authoritative_import_ready(self):\n"
        "        assert True\n",
        encoding="utf-8",
    )
    import_candidate_paths = {
        "launcher_update_check": [launcher_candidate],
        "studio_shell_api": [api_candidate],
        "studio_shell_test_pass10a": [shell_test_candidate],
    }
    required_symbols = {
        "launcher_update_check": ["build_authoritative_import_ready"],
        "studio_shell_api": [
            "class StudioAPI",
            "get_authoritative_import_ready",
        ],
        "studio_shell_test_pass10a": [
            "TestAuthoritativeImportReady",
            "test_authoritative_import_ready",
        ],
    }
    generated_at = "2026-05-25T00:00:00Z"
    preview = build_launcher_update_authoritative_source_candidate_import_boundary_proof(
        tmp_path,
        import_candidate_paths=import_candidate_paths,
        required_symbols_by_role=required_symbols,
        generated_at=generated_at,
    )

    assert preview["candidate_import_plan_ready"] is True
    assert preview["operator_statement_matched"] is False
    assert (
        preview["status"]
        == "launcher_update_authoritative_source_candidate_import_pending_approval"
    )

    statement = required_update_authoritative_source_candidate_import_operator_statement(
        preview["candidate_import_plan"]
    )
    blocked_write_flag = build_launcher_update_authoritative_source_candidate_import_boundary_proof(
        tmp_path,
        import_candidate_paths=import_candidate_paths,
        required_symbols_by_role=required_symbols,
        operator_approved_candidate_import=True,
        operator_statement=statement,
        generated_at=generated_at,
    )

    assert blocked_write_flag["status"] == (
        "launcher_update_authoritative_source_candidate_import_write_flag_required"
    )
    assert blocked_write_flag["candidate_import_write_performed"] is False

    imported = build_launcher_update_authoritative_source_candidate_import_boundary_proof(
        tmp_path,
        import_candidate_paths=import_candidate_paths,
        required_symbols_by_role=required_symbols,
        operator_approved_candidate_import=True,
        operator_statement=statement,
        allow_candidate_import_write=True,
        generated_at=generated_at,
    )

    assert imported["ok"] is True
    assert (
        imported["status"]
        == "launcher_update_authoritative_source_candidate_import_imported"
    )
    assert imported["candidate_import_write_performed"] is True
    assert imported["candidate_import_performed"] is True
    assert imported["source_write_performed"] is False
    assert imported["wrapper_removal_performed"] is False
    assert imported["primary_exe_replacement_performed"] is False
    assert imported["settings_write_control_exposed"] is False

    target_launcher = (
        tmp_path
        / ".chaseos"
        / "updates"
        / "source-candidates"
        / "authoritative-normal-source"
        / "runtime"
        / "studio"
        / "launcher_update_check.py"
    )
    target_api = (
        tmp_path
        / ".chaseos"
        / "updates"
        / "source-candidates"
        / "authoritative-normal-source"
        / "runtime"
        / "studio"
        / "shell"
        / "api.py"
    )
    target_shell_test = (
        tmp_path
        / ".chaseos"
        / "updates"
        / "source-candidates"
        / "authoritative-normal-source"
        / "runtime"
        / "studio"
        / "shell"
        / "test_pass10a_shell.py"
    )
    assert target_launcher.read_text(encoding="utf-8") == launcher_candidate.read_text(
        encoding="utf-8"
    )
    assert target_api.read_text(encoding="utf-8") == api_candidate.read_text(
        encoding="utf-8"
    )
    assert target_shell_test.read_text(
        encoding="utf-8"
    ) == shell_test_candidate.read_text(encoding="utf-8")
    assert all(
        item["write_performed"] and item["write_verified"]
        for item in imported["candidate_import_results"].values()
    )
    supply_preview = imported["post_import_supply_packet_preview"]
    assert supply_preview["authoritative_source_candidates_available"] is True
    assert supply_preview["ready_for_candidate_verifier"] is False
    assert supply_preview["status"] == (
        "launcher_update_authoritative_normal_source_candidate_supply_"
        "pending_approval"
    )
    assert imported["ready_for_candidate_supply_approval"] is True


def test_launcher_update_real_authoritative_source_candidate_supply_readiness_reports_missing_candidates():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_authoritative_source_candidate_supply_readiness,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = build_launcher_update_real_authoritative_source_candidate_supply_readiness(
        vault_root,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["surface"] == (
        "studio_launcher_update_real_authoritative_source_candidate_supply_readiness"
    )
    assert result["status"] == (
        "launcher_update_real_authoritative_source_candidate_supply_blocked"
    )
    assert result["real_authoritative_source_candidates_available"] is False
    assert result["ready_for_authoritative_import_boundary"] is False
    assert result["candidate_import_plan_ready"] is False
    assert result["source_write_performed"] is False
    assert result["candidate_import_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert "real_authoritative_source_candidates_missing" in result["errors"]
    assert (
        "launcher_update_check_real_authoritative_candidate_missing"
        in result["errors"]
    )


def test_launcher_update_real_authoritative_source_candidate_supply_readiness_feeds_import_boundary(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_authoritative_source_candidate_import_boundary_proof,
        build_launcher_update_real_authoritative_source_candidate_supply_readiness,
        required_update_authoritative_source_candidate_import_operator_statement,
    )

    incoming_root = tmp_path / "incoming-authoritative-source"
    launcher_candidate = incoming_root / "runtime" / "studio" / "launcher_update_check.py"
    api_candidate = incoming_root / "runtime" / "studio" / "shell" / "api.py"
    shell_test_candidate = (
        incoming_root / "runtime" / "studio" / "shell" / "test_pass10a_shell.py"
    )
    launcher_candidate.parent.mkdir(parents=True, exist_ok=True)
    api_candidate.parent.mkdir(parents=True, exist_ok=True)
    launcher_candidate.write_text(
        "def build_real_candidate_supply_ready():\n    return True\n",
        encoding="utf-8",
    )
    api_candidate.write_text(
        "class StudioAPI:\n"
        "    def get_real_candidate_supply_ready(self):\n"
        "        return True\n",
        encoding="utf-8",
    )
    shell_test_candidate.write_text(
        "class TestRealCandidateSupplyReady:\n"
        "    def test_real_candidate_supply_ready(self):\n"
        "        assert True\n",
        encoding="utf-8",
    )
    required_symbols = {
        "launcher_update_check": ["build_real_candidate_supply_ready"],
        "studio_shell_api": [
            "class StudioAPI",
            "get_real_candidate_supply_ready",
        ],
        "studio_shell_test_pass10a": [
            "TestRealCandidateSupplyReady",
            "test_real_candidate_supply_ready",
        ],
    }
    generated_at = "2026-05-25T00:00:00Z"

    readiness = build_launcher_update_real_authoritative_source_candidate_supply_readiness(
        tmp_path,
        candidate_roots=[incoming_root],
        required_symbols_by_role=required_symbols,
        generated_at=generated_at,
    )

    assert readiness["ok"] is True
    assert readiness["status"] == (
        "launcher_update_real_authoritative_source_candidate_supply_"
        "ready_for_import_boundary"
    )
    assert readiness["real_authoritative_source_candidates_available"] is True
    assert readiness["ready_for_authoritative_import_boundary"] is True
    assert readiness["candidate_import_plan_ready"] is True
    assert all(readiness["role_readiness"].values())
    assert readiness["candidate_import_write_performed"] is False
    assert readiness["source_write_performed"] is False
    assert readiness["wrapper_removal_performed"] is False

    statement = required_update_authoritative_source_candidate_import_operator_statement(
        readiness["candidate_import_preview"]["candidate_import_plan"]
    )
    assert readiness["required_candidate_import_operator_statement"] == statement
    imported = build_launcher_update_authoritative_source_candidate_import_boundary_proof(
        tmp_path,
        import_candidate_paths=readiness["candidate_import_paths"],
        required_symbols_by_role=required_symbols,
        operator_approved_candidate_import=True,
        operator_statement=statement,
        allow_candidate_import_write=True,
        generated_at=generated_at,
    )

    assert imported["ok"] is True
    assert imported["candidate_import_write_performed"] is True
    assert imported["post_import_supply_packet_candidates_available"] is True
    assert imported["source_write_performed"] is False
    assert imported["wrapper_removal_performed"] is False
    assert imported["primary_exe_replacement_performed"] is False


def test_launcher_update_real_authoritative_source_candidate_materialization_blocks_default_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof(
            vault_root,
            generated_at="2026-05-25T00:00:00Z",
        )
    )

    assert result["ok"] is False
    assert result["surface"] == (
        "studio_launcher_update_real_authoritative_source_candidate_materialization_proof"
    )
    assert result["status"] == (
        "launcher_update_real_authoritative_source_candidate_materialization_blocked"
    )
    assert result["materialization_plan_ready"] is False
    assert result["source_materializer_execution_performed"] is False
    assert result["candidate_materialization_write_performed"] is False
    assert result["candidate_import_write_performed"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert "real_authoritative_source_candidates_missing" in result["errors"]
    assert "source_materializer_required" in result["errors"]
    assert "operator_candidate_materialization_approval_required" in result["errors"]


def test_launcher_update_real_authoritative_source_candidate_materialization_writes_fixture_candidates_only(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof,
    )

    required_symbols = {
        "launcher_update_check": ["build_materialized_candidate_ready"],
        "studio_shell_api": [
            "class StudioAPI",
            "get_materialized_candidate_ready",
        ],
        "studio_shell_test_pass10a": [
            "TestMaterializedCandidateReady",
            "test_materialized_candidate_ready",
        ],
    }

    def fixture_materializer(context):
        return {
            "ok": True,
            "runner_label": context["source_materializer_label"],
            "generated_sources": {
                "launcher_update_check": (
                    "def build_materialized_candidate_ready():\n"
                    "    return True\n"
                ),
                "studio_shell_api": (
                    "class StudioAPI:\n"
                    "    def get_materialized_candidate_ready(self):\n"
                    "        return True\n"
                ),
                "studio_shell_test_pass10a": (
                    "class TestMaterializedCandidateReady:\n"
                    "    def test_materialized_candidate_ready(self):\n"
                    "        assert True\n"
                ),
            },
        }

    generated_at = "2026-05-25T00:00:00Z"
    materialization_root = (
        tmp_path
        / ".chaseos"
        / "updates"
        / "source-candidates"
        / "operator-supplied-normal-source"
    )
    preview = (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof(
            tmp_path,
            materialization_root=materialization_root,
            source_materializer=fixture_materializer,
            source_materializer_label="fixture-source-candidate-materializer",
            required_symbols_by_role=required_symbols,
            generated_at=generated_at,
        )
    )

    assert preview["ok"] is False
    assert preview["status"] == (
        "launcher_update_real_authoritative_source_candidate_materialization_"
        "pending_approval"
    )
    assert preview["materialization_plan_ready"] is True
    assert preview["candidate_materialization_write_performed"] is False

    result = (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof(
            tmp_path,
            materialization_root=materialization_root,
            source_materializer=fixture_materializer,
            source_materializer_label="fixture-source-candidate-materializer",
            required_symbols_by_role=required_symbols,
            operator_approved_candidate_materialization=True,
            operator_statement=preview["required_operator_statement"],
            allow_candidate_materialization_write=True,
            generated_at=generated_at,
        )
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_real_authoritative_source_candidate_materialization_"
        "candidates_materialized"
    )
    assert result["operator_statement_matched"] is True
    assert result["source_materializer_execution_performed"] is True
    assert result["candidate_materialization_write_performed"] is True
    assert result["post_materialization_ready_for_import_boundary"] is True
    assert result["ready_for_authoritative_import_boundary"] is True
    assert result["candidate_import_write_performed"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert (
        materialization_root / "runtime" / "studio" / "launcher_update_check.py"
    ).exists()
    assert (materialization_root / "runtime" / "studio" / "shell" / "api.py").exists()
    assert (
        materialization_root
        / "runtime"
        / "studio"
        / "shell"
        / "test_pass10a_shell.py"
    ).exists()
    assert (
        result["post_materialization_supply_readiness"][
            "ready_for_authoritative_import_boundary"
        ]
        is True
    )


def test_launcher_update_real_authoritative_source_candidate_import_from_materialization_blocks_default_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof(
            vault_root,
            generated_at="2026-05-25T00:00:00Z",
        )
    )

    assert result["ok"] is False
    assert result["surface"] == (
        "studio_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof"
    )
    assert result["status"] == (
        "launcher_update_real_authoritative_source_candidate_import_from_materialization_blocked"
    )
    assert result["import_from_materialization_plan_ready"] is False
    assert result["materialization_ready_for_import_boundary"] is False
    assert result["candidate_import_write_performed"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert (
        "real_authoritative_source_candidate_materialization_proof_required"
        in result["errors"]
    )


def test_launcher_update_real_authoritative_source_candidate_import_from_materialization_imports_fixture_candidates(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof,
        build_launcher_update_real_authoritative_source_candidate_materialization_proof,
    )

    required_symbols = {
        "launcher_update_check": ["build_materialized_import_candidate_ready"],
        "studio_shell_api": [
            "class StudioAPI",
            "get_materialized_import_candidate_ready",
        ],
        "studio_shell_test_pass10a": [
            "TestMaterializedImportCandidateReady",
            "test_materialized_import_candidate_ready",
        ],
    }

    def fixture_materializer(context):
        return {
            "ok": True,
            "runner_label": context["source_materializer_label"],
            "generated_sources": {
                "launcher_update_check": (
                    "def build_materialized_import_candidate_ready():\n"
                    "    return True\n"
                ),
                "studio_shell_api": (
                    "class StudioAPI:\n"
                    "    def get_materialized_import_candidate_ready(self):\n"
                    "        return True\n"
                ),
                "studio_shell_test_pass10a": (
                    "class TestMaterializedImportCandidateReady:\n"
                    "    def test_materialized_import_candidate_ready(self):\n"
                    "        assert True\n"
                ),
            },
        }

    generated_at = "2026-05-25T00:00:00Z"
    materialization_root = (
        tmp_path
        / ".chaseos"
        / "updates"
        / "source-candidates"
        / "operator-supplied-normal-source"
    )
    materialization_preview = (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof(
            tmp_path,
            materialization_root=materialization_root,
            source_materializer=fixture_materializer,
            source_materializer_label="fixture-source-candidate-materializer",
            required_symbols_by_role=required_symbols,
            generated_at=generated_at,
        )
    )
    materialization = (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof(
            tmp_path,
            materialization_root=materialization_root,
            source_materializer=fixture_materializer,
            source_materializer_label="fixture-source-candidate-materializer",
            required_symbols_by_role=required_symbols,
            operator_approved_candidate_materialization=True,
            operator_statement=materialization_preview["required_operator_statement"],
            allow_candidate_materialization_write=True,
            generated_at=generated_at,
        )
    )
    assert materialization["ok"] is True

    import_preview = (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof(
            tmp_path,
            materialization_proof=materialization,
            required_symbols_by_role=required_symbols,
            generated_at=generated_at,
        )
    )

    assert import_preview["ok"] is False
    assert import_preview["status"] == (
        "launcher_update_real_authoritative_source_candidate_import_from_"
        "materialization_pending_approval"
    )
    assert import_preview["import_from_materialization_plan_ready"] is True
    assert import_preview["candidate_import_write_performed"] is False

    blocked_write_flag = (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof(
            tmp_path,
            materialization_proof=materialization,
            required_symbols_by_role=required_symbols,
            operator_approved_import_from_materialization=True,
            operator_statement=import_preview["required_operator_statement"],
            generated_at=generated_at,
        )
    )
    assert blocked_write_flag["status"] == (
        "launcher_update_real_authoritative_source_candidate_import_from_"
        "materialization_write_flag_required"
    )
    assert blocked_write_flag["candidate_import_write_performed"] is False

    imported = (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof(
            tmp_path,
            materialization_proof=materialization,
            required_symbols_by_role=required_symbols,
            operator_approved_import_from_materialization=True,
            operator_statement=import_preview["required_operator_statement"],
            allow_candidate_import_write=True,
            generated_at=generated_at,
        )
    )

    assert imported["ok"] is True
    assert imported["status"] == (
        "launcher_update_real_authoritative_source_candidate_import_from_"
        "materialization_imported"
    )
    assert imported["operator_statement_matched"] is True
    assert imported["materialization_digest_matched"] is True
    assert imported["materialization_ready_for_import_boundary"] is True
    assert imported["candidate_import_write_performed"] is True
    assert imported["ready_for_candidate_supply_approval"] is True
    assert imported["source_write_performed"] is False
    assert imported["wrapper_removal_performed"] is False
    assert imported["decompiler_execution_performed"] is False
    assert imported["candidate_source_execution_performed"] is False
    assert imported["settings_write_control_exposed"] is False
    assert imported["primary_exe_replacement_performed"] is False
    authoritative_import = imported[
        "authoritative_source_candidate_import_boundary_proof"
    ]
    assert authoritative_import["ok"] is True
    assert authoritative_import["candidate_import_write_performed"] is True
    target_root = tmp_path / ".chaseos" / "updates" / "source-candidates" / "authoritative-normal-source"
    assert (target_root / "runtime" / "studio" / "launcher_update_check.py").exists()
    assert (target_root / "runtime" / "studio" / "shell" / "api.py").exists()
    assert (
        target_root / "runtime" / "studio" / "shell" / "test_pass10a_shell.py"
    ).exists()


def test_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_blocks_default_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = (
        build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof(
            vault_root,
            generated_at="2026-05-25T00:00:00Z",
        )
    )

    assert result["ok"] is False
    assert result["surface"] == (
        "studio_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof"
    )
    assert result["status"] == (
        "launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_blocked"
    )
    assert (
        result["supply_verification_from_materialization_import_plan_ready"] is False
    )
    assert (
        result["import_from_materialization_ready_for_supply_verification"] is False
    )
    assert result["embedded_import_boundary_ready"] is False
    assert result["ready_for_wrapper_removal_executor"] is False
    assert result["candidate_import_write_performed"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert (
        "real_authoritative_source_candidate_import_from_materialization_proof_required"
        in result["errors"]
    )


def test_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_readies_wrapper_removal_chain(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof,
        build_launcher_update_real_authoritative_source_candidate_materialization_proof,
        build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof,
    )

    required_symbols = {
        "launcher_update_check": [
            "build_materialized_supply_verification_ready"
        ],
        "studio_shell_api": [
            "class StudioAPI",
            "get_materialized_supply_verification_ready",
        ],
        "studio_shell_test_pass10a": [
            "TestMaterializedSupplyVerificationReady",
            "test_materialized_supply_verification_ready",
        ],
    }

    def fixture_materializer(context):
        return {
            "ok": True,
            "runner_label": context["source_materializer_label"],
            "generated_sources": {
                "launcher_update_check": (
                    "def build_materialized_supply_verification_ready():\n"
                    "    return True\n"
                ),
                "studio_shell_api": (
                    "class StudioAPI:\n"
                    "    def get_materialized_supply_verification_ready(self):\n"
                    "        return True\n"
                ),
                "studio_shell_test_pass10a": (
                    "class TestMaterializedSupplyVerificationReady:\n"
                    "    def test_materialized_supply_verification_ready(self):\n"
                    "        assert True\n"
                ),
            },
        }

    generated_at = "2026-05-25T00:00:00Z"
    materialization_root = (
        tmp_path
        / ".chaseos"
        / "updates"
        / "source-candidates"
        / "operator-supplied-normal-source"
    )
    materialization_preview = (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof(
            tmp_path,
            materialization_root=materialization_root,
            source_materializer=fixture_materializer,
            source_materializer_label="fixture-source-candidate-materializer",
            required_symbols_by_role=required_symbols,
            generated_at=generated_at,
        )
    )
    materialization = (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof(
            tmp_path,
            materialization_root=materialization_root,
            source_materializer=fixture_materializer,
            source_materializer_label="fixture-source-candidate-materializer",
            required_symbols_by_role=required_symbols,
            operator_approved_candidate_materialization=True,
            operator_statement=materialization_preview["required_operator_statement"],
            allow_candidate_materialization_write=True,
            generated_at=generated_at,
        )
    )
    import_preview = (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof(
            tmp_path,
            materialization_proof=materialization,
            required_symbols_by_role=required_symbols,
            generated_at=generated_at,
        )
    )
    imported = (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof(
            tmp_path,
            materialization_proof=materialization,
            required_symbols_by_role=required_symbols,
            operator_approved_import_from_materialization=True,
            operator_statement=import_preview["required_operator_statement"],
            allow_candidate_import_write=True,
            generated_at=generated_at,
        )
    )
    assert imported["ok"] is True

    preview = (
        build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof(
            tmp_path,
            import_from_materialization_proof=imported,
            required_symbols_by_role=required_symbols,
            generated_at=generated_at,
        )
    )

    assert preview["ok"] is False
    assert preview["status"] == (
        "launcher_update_real_authoritative_source_candidate_supply_verification_"
        "from_materialization_import_pending_approval"
    )
    assert (
        preview["supply_verification_from_materialization_import_plan_ready"]
        is True
    )
    assert (
        preview["import_from_materialization_ready_for_supply_verification"]
        is True
    )
    assert preview["embedded_import_boundary_ready"] is True
    assert preview["operator_statement_matched"] is False
    assert preview["source_import_candidate_write_already_performed"] is True
    assert preview["candidate_import_write_performed"] is False
    assert preview["source_write_performed"] is False
    assert preview["after_import_verification_preview"]["import_boundary_verified"] is True

    ready = (
        build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof(
            tmp_path,
            import_from_materialization_proof=imported,
            required_symbols_by_role=required_symbols,
            operator_approved_supply_verification_from_materialization_import=True,
            operator_statement=preview["required_operator_statement"],
            generated_at=generated_at,
        )
    )

    assert ready["ok"] is True
    assert ready["status"] == (
        "launcher_update_real_authoritative_source_candidate_supply_verification_"
        "from_materialization_import_ready_for_wrapper_removal_executor"
    )
    assert ready["operator_statement_matched"] is True
    assert ready["candidate_supply_packet_ready"] is True
    assert ready["candidate_verification_ready"] is True
    assert ready["ready_for_wrapper_removal_executor"] is True
    assert ready["after_import_verification_proof"]["ok"] is True
    assert (
        ready["after_import_verification_proof"][
            "ready_for_wrapper_removal_executor"
        ]
        is True
    )
    assert ready["candidate_import_write_performed"] is False
    assert ready["source_write_performed"] is False
    assert ready["wrapper_removal_performed"] is False
    assert ready["decompiler_execution_performed"] is False
    assert ready["candidate_source_execution_performed"] is False
    assert ready["settings_write_control_exposed"] is False
    assert ready["primary_exe_replacement_performed"] is False


def test_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_blocks_default_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof(
        vault_root,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["surface"] == (
        "studio_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof"
    )
    assert result["status"] == (
        "launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_blocked"
    )
    assert (
        result["supply_verification_from_materialization_import_ready"] is False
    )
    assert (
        result["wrapper_removal_from_materialization_import_execution_plan_ready"]
        is False
    )
    assert result["restore_plan_ready"] is False
    assert result["current_vault_source_write_enabled"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["current_vault_wrappers_removed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert (
        "real_authoritative_source_candidate_supply_verification_from_materialization_import_proof_required"
        in result["errors"]
    )


def test_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_restores_fixture_current_vault_after_exact_approval(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof,
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof,
        build_launcher_update_real_authoritative_source_candidate_materialization_proof,
        build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof,
        required_update_current_vault_wrapper_removal_from_materialization_import_operator_statement,
    )

    required_symbols = {
        "launcher_update_check": [
            "build_materialized_wrapper_removal_ready"
        ],
        "studio_shell_api": [
            "class StudioAPI",
            "get_materialized_wrapper_removal_ready",
        ],
        "studio_shell_test_pass10a": [
            "TestMaterializedWrapperRemovalReady",
            "test_materialized_wrapper_removal_ready",
        ],
    }

    def fixture_materializer(context):
        return {
            "ok": True,
            "runner_label": context["source_materializer_label"],
            "generated_sources": {
                "launcher_update_check": (
                    "def build_materialized_wrapper_removal_ready():\n"
                    "    return True\n"
                ),
                "studio_shell_api": (
                    "class StudioAPI:\n"
                    "    def get_materialized_wrapper_removal_ready(self):\n"
                    "        return True\n"
                ),
                "studio_shell_test_pass10a": (
                    "class TestMaterializedWrapperRemovalReady:\n"
                    "    def test_materialized_wrapper_removal_ready(self):\n"
                    "        assert True\n"
                ),
            },
        }

    generated_at = "2026-05-25T00:00:00Z"
    target_launcher = tmp_path / "runtime" / "studio" / "launcher_update_check.py"
    target_api = tmp_path / "runtime" / "studio" / "shell" / "api.py"
    target_shell_test = (
        tmp_path / "runtime" / "studio" / "shell" / "test_pass10a_shell.py"
    )
    target_launcher.parent.mkdir(parents=True, exist_ok=True)
    target_api.parent.mkdir(parents=True, exist_ok=True)
    target_launcher.write_text(
        "_RECOVERED_BYTECODE_PATH = 'fixture'\n"
        "exec(_RECOVERED_BYTECODE_CODE, globals())\n",
        encoding="utf-8",
    )
    target_api.write_text(
        "_RECOVERED_BYTECODE_PATH = 'fixture'\n"
        "exec(_RECOVERED_BYTECODE_CODE, globals())\n",
        encoding="utf-8",
    )
    target_shell_test.write_text(
        "_RECOVERED_TEST_BYTECODE_PATH = 'fixture'\n"
        "exec(_RECOVERED_TEST_CODE, globals())\n",
        encoding="utf-8",
    )

    materialization_root = (
        tmp_path
        / ".chaseos"
        / "updates"
        / "source-candidates"
        / "operator-supplied-normal-source"
    )
    materialization_preview = (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof(
            tmp_path,
            materialization_root=materialization_root,
            source_materializer=fixture_materializer,
            source_materializer_label="fixture-source-candidate-materializer",
            required_symbols_by_role=required_symbols,
            generated_at=generated_at,
        )
    )
    materialization = (
        build_launcher_update_real_authoritative_source_candidate_materialization_proof(
            tmp_path,
            materialization_root=materialization_root,
            source_materializer=fixture_materializer,
            source_materializer_label="fixture-source-candidate-materializer",
            required_symbols_by_role=required_symbols,
            operator_approved_candidate_materialization=True,
            operator_statement=materialization_preview["required_operator_statement"],
            allow_candidate_materialization_write=True,
            generated_at=generated_at,
        )
    )
    import_preview = (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof(
            tmp_path,
            materialization_proof=materialization,
            required_symbols_by_role=required_symbols,
            generated_at=generated_at,
        )
    )
    imported = (
        build_launcher_update_real_authoritative_source_candidate_import_from_materialization_proof(
            tmp_path,
            materialization_proof=materialization,
            required_symbols_by_role=required_symbols,
            operator_approved_import_from_materialization=True,
            operator_statement=import_preview["required_operator_statement"],
            allow_candidate_import_write=True,
            generated_at=generated_at,
        )
    )
    supply_preview = (
        build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof(
            tmp_path,
            import_from_materialization_proof=imported,
            required_symbols_by_role=required_symbols,
            generated_at=generated_at,
        )
    )
    supply_ready = (
        build_launcher_update_real_authoritative_source_candidate_supply_verification_from_materialization_import_proof(
            tmp_path,
            import_from_materialization_proof=imported,
            required_symbols_by_role=required_symbols,
            operator_approved_supply_verification_from_materialization_import=True,
            operator_statement=supply_preview["required_operator_statement"],
            generated_at=generated_at,
        )
    )

    preview = (
        build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof(
            tmp_path,
            supply_verification_from_materialization_import_proof=supply_ready,
            required_symbols_by_role=required_symbols,
            generated_at=generated_at,
        )
    )

    assert preview["supply_verification_from_materialization_import_ready"] is True
    assert preview["restore_plan_ready"] is True
    assert (
        preview[
            "wrapper_removal_from_materialization_import_execution_plan_ready"
        ]
        is True
    )
    assert preview["operator_statement_matched"] is False
    assert preview["status"] == (
        "launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_"
        "pending_approval"
    )

    removal_statement = required_update_current_vault_wrapper_removal_from_materialization_import_operator_statement(
        preview["wrapper_removal_from_materialization_import_execution_plan"]
    )
    blocked_write_flag = (
        build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof(
            tmp_path,
            supply_verification_from_materialization_import_proof=supply_ready,
            required_symbols_by_role=required_symbols,
            operator_approved_current_vault_wrapper_removal_from_materialization_import=True,
            operator_statement=removal_statement,
            generated_at=generated_at,
        )
    )

    assert blocked_write_flag["status"] == (
        "launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_"
        "write_flag_required"
    )
    assert blocked_write_flag["source_write_performed"] is False

    restored = (
        build_launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_proof(
            tmp_path,
            supply_verification_from_materialization_import_proof=supply_ready,
            required_symbols_by_role=required_symbols,
            allow_current_vault_source_write=True,
            operator_approved_current_vault_wrapper_removal_from_materialization_import=True,
            operator_statement=removal_statement,
            generated_at=generated_at,
        )
    )

    assert restored["ok"] is True
    assert restored["status"] == (
        "launcher_update_current_vault_wrapper_removal_from_materialization_import_execution_restored"
    )
    assert restored["source_write_performed"] is True
    assert restored["wrapper_removal_performed"] is True
    assert restored["current_vault_wrappers_removed"] is True
    assert restored["primary_exe_replacement_performed"] is False
    assert restored["settings_write_control_exposed"] is False

    authoritative_root = (
        tmp_path
        / ".chaseos"
        / "updates"
        / "source-candidates"
        / "authoritative-normal-source"
    )
    authoritative_launcher = (
        authoritative_root / "runtime" / "studio" / "launcher_update_check.py"
    )
    authoritative_api = authoritative_root / "runtime" / "studio" / "shell" / "api.py"
    authoritative_shell_test = (
        authoritative_root
        / "runtime"
        / "studio"
        / "shell"
        / "test_pass10a_shell.py"
    )
    assert target_launcher.read_text(encoding="utf-8") == authoritative_launcher.read_text(
        encoding="utf-8"
    )
    assert target_api.read_text(encoding="utf-8") == authoritative_api.read_text(
        encoding="utf-8"
    )
    assert target_shell_test.read_text(
        encoding="utf-8"
    ) == authoritative_shell_test.read_text(encoding="utf-8")
    assert all(
        item["target_verification_passed"] and item["wrapper_free"]
        for item in restored["post_write_source_checks"].values()
    )


def _installer_disposable_plan_digest(payload):
    plan = dict(payload)
    plan.pop("plan_digest_sha256", None)
    return _hashlib.sha256(
        _json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _write_installer_disposable_plan(root, *, vault_root=None):
    from runtime.studio.launcher_update_helper import (
        HELPER_BINARY_NAME,
        INSTALLER_DISPOSABLE_UPDATE_MODE,
        INSTALLER_DISPOSABLE_UPDATE_PLAN_SCHEMA_VERSION,
    )

    target_root = root / "disposable-target"
    current = target_root / "installed" / "ChaseOS-Studio.exe"
    staged = target_root / "staged" / "ChaseOS-Studio.exe"
    backup = target_root / "backup" / "ChaseOS-Studio.exe.bak"
    receipt = target_root / "receipts" / "receipt.json"
    plan_file = target_root / "plans" / "plan.json"
    current.parent.mkdir(parents=True)
    staged.parent.mkdir(parents=True)
    plan_file.parent.mkdir(parents=True)
    current.write_bytes(b"current-build")
    staged.write_bytes(b"new-build")
    plan = {
        "schema_version": INSTALLER_DISPOSABLE_UPDATE_PLAN_SCHEMA_VERSION,
        "mode": INSTALLER_DISPOSABLE_UPDATE_MODE,
        "generated_at_utc": "2026-05-27T00:00:00Z",
        "helper_binary_name": HELPER_BINARY_NAME,
        "target_artifact_name": "ChaseOS-Studio.exe",
        "target_root_kind": "disposable",
        "target_root": str(target_root),
        "current_executable_path": str(current),
        "staged_artifact_path": str(staged),
        "backup_executable_path": str(backup),
        "receipt_path": str(receipt),
        "expected_current_sha256": _hashlib.sha256(b"current-build").hexdigest(),
        "expected_staged_sha256": _hashlib.sha256(b"new-build").hexdigest(),
        "allow_live_install": False,
        "allow_primary_install_mutation": False,
        "relaunch_after_update": False,
        "github_release_publication_enabled": False,
        "startup_mutation_enabled": False,
        "production_auto_update_complete": False,
    }
    plan["plan_digest_sha256"] = _installer_disposable_plan_digest(plan)
    plan_file.write_text(_json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "vault_root": vault_root or root,
        "target_root": target_root,
        "current": current,
        "staged": staged,
        "backup": backup,
        "receipt": receipt,
        "plan_file": plan_file,
        "plan": plan,
    }


def test_chaseos_installer_disposable_plan_executes_fixture_replacement(tmp_path):
    from runtime.studio.launcher_update_helper import (
        execute_launcher_update_installer_disposable_update_plan,
    )

    fixture = _write_installer_disposable_plan(tmp_path)
    result = execute_launcher_update_installer_disposable_update_plan(
        fixture["plan_file"],
        vault_root=fixture["vault_root"],
        execute_disposable=True,
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is True
    assert result["status"] == "installer_disposable_update_executed"
    assert result["disposable_target_update_performed"] is True
    assert result["primary_install_mutation_performed"] is False
    assert result["live_install_performed"] is False
    assert fixture["current"].read_bytes() == b"new-build"
    assert fixture["backup"].read_bytes() == b"current-build"
    receipt = _json.loads(fixture["receipt"].read_text(encoding="utf-8"))
    assert receipt["target_replaced"] is True
    assert receipt["replacement_verified"] is True
    assert receipt["production_auto_update_complete"] is False


def test_chaseos_installer_disposable_plan_blocks_primary_dist_target(tmp_path):
    from runtime.studio.launcher_update_helper import (
        HELPER_BINARY_NAME,
        INSTALLER_DISPOSABLE_UPDATE_MODE,
        INSTALLER_DISPOSABLE_UPDATE_PLAN_SCHEMA_VERSION,
        execute_launcher_update_installer_disposable_update_plan,
    )

    target_root = tmp_path / "dist"
    current = target_root / "studio" / "ChaseOS-Studio.exe"
    staged = target_root / "staged" / "ChaseOS-Studio.exe"
    backup = target_root / "backup" / "ChaseOS-Studio.exe.bak"
    receipt = target_root / "receipts" / "receipt.json"
    plan_file = target_root / "plans" / "plan.json"
    current.parent.mkdir(parents=True)
    staged.parent.mkdir(parents=True)
    plan_file.parent.mkdir(parents=True)
    current.write_bytes(b"current-primary")
    staged.write_bytes(b"new-build")
    plan = {
        "schema_version": INSTALLER_DISPOSABLE_UPDATE_PLAN_SCHEMA_VERSION,
        "mode": INSTALLER_DISPOSABLE_UPDATE_MODE,
        "generated_at_utc": "2026-05-27T00:00:00Z",
        "helper_binary_name": HELPER_BINARY_NAME,
        "target_artifact_name": "ChaseOS-Studio.exe",
        "target_root_kind": "disposable",
        "target_root": str(target_root),
        "current_executable_path": str(current),
        "staged_artifact_path": str(staged),
        "backup_executable_path": str(backup),
        "receipt_path": str(receipt),
        "expected_current_sha256": _hashlib.sha256(b"current-primary").hexdigest(),
        "expected_staged_sha256": _hashlib.sha256(b"new-build").hexdigest(),
        "allow_live_install": False,
        "allow_primary_install_mutation": False,
        "relaunch_after_update": False,
        "github_release_publication_enabled": False,
        "startup_mutation_enabled": False,
        "production_auto_update_complete": False,
    }
    plan["plan_digest_sha256"] = _installer_disposable_plan_digest(plan)
    plan_file.write_text(_json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")

    result = execute_launcher_update_installer_disposable_update_plan(
        plan_file,
        vault_root=tmp_path,
        execute_disposable=True,
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["disposable_target_update_performed"] is False
    assert (
        "current_executable_path_must_not_target_primary_dist_artifact"
        in result["errors"]
    )
    assert current.read_bytes() == b"current-primary"


def test_launcher_update_local_installer_disposable_dry_run_executes_receipt(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_local_installer_disposable_dry_run_proof,
    )

    fixture = _write_installer_disposable_plan(tmp_path)
    fixture["plan_file"].unlink()

    result = build_launcher_update_local_installer_disposable_dry_run_proof(
        tmp_path,
        disposable_root=fixture["target_root"],
        current_executable_path=fixture["current"],
        staged_artifact_path=fixture["staged"],
        backup_executable_path=fixture["backup"],
        receipt_path=fixture["receipt"],
        plan_file_path=fixture["plan_file"],
        allow_disposable_execution=True,
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is True
    assert (
        result["status"]
        == "launcher_update_local_installer_disposable_dry_run_receipt_verified"
    )
    assert result["helper_binary_name"] == "ChaseOS-Installer.exe"
    assert result["local_installer_disposable_dry_run_executed"] is True
    assert result["receipt_verified"] is True
    assert result["primary_install_mutation_performed"] is False
    assert result["production_auto_update_complete"] is False
    assert fixture["current"].read_bytes() == b"new-build"


def test_launcher_update_local_installer_disposable_dry_run_default_writes_nothing(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_local_installer_disposable_dry_run_proof,
    )

    disposable_root = tmp_path / "disposable-target"
    result = build_launcher_update_local_installer_disposable_dry_run_proof(
        tmp_path,
        disposable_root=disposable_root,
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is False
    assert (
        result["status"]
        == "launcher_update_local_installer_disposable_dry_run_plan_ready_execution_disabled"
    )
    assert result["plan_file_write_performed"] is False
    assert result["installer_execution_performed"] is False
    assert result["settings_install_control_exposed"] is False
    assert not disposable_root.exists()


def _write_local_manifest_for_prompt(
    root,
    *,
    latest_version="0.8.3",
    artifact_name="ChaseOS-Studio.exe",
    artifact_path=None,
    sha256=None,
):
    manifest_dir = root / ".chaseos" / "updates"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "chaser.local_update_manifest.v1",
        "latest_version": latest_version,
        "release_date": "2026-05-27",
        "release_notes_summary": "Local manifest prompt fixture.",
        "artifact_name": artifact_name,
        "download_url": "https://example.invalid/ChaseOS-Studio.exe",
        "mandatory": False,
        "recommended": True,
    }
    if artifact_path is not None:
        manifest["artifact_path"] = str(artifact_path)
    if sha256 is not None:
        manifest["sha256"] = sha256
    path = manifest_dir / "local-update-manifest.json"
    path.write_text(_json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def test_launcher_update_local_manifest_background_prompt_previews_disposable_plan(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_local_manifest_background_prompt_settings_action,
    )

    disposable = tmp_path / "disposable-target"
    current = disposable / "installed" / "ChaseOS-Studio.exe"
    staged = disposable / "staged" / "ChaseOS-Studio.exe"
    current.parent.mkdir(parents=True, exist_ok=True)
    staged.parent.mkdir(parents=True, exist_ok=True)
    current.write_bytes(b"current-build")
    staged.write_bytes(b"new-build")
    manifest = _write_local_manifest_for_prompt(
        tmp_path,
        artifact_path=staged,
        sha256=_hashlib.sha256(staged.read_bytes()).hexdigest(),
    )

    result = build_launcher_update_local_manifest_background_prompt_settings_action(
        tmp_path,
        manifest_path=manifest,
        current_version="0.8.2",
        disposable_root=disposable,
        current_executable_path=current,
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_local_manifest_background_prompt_"
        "prompt_ready_installer_plan_preview"
    )
    assert result["current_version"] == "0.8.2"
    assert result["latest_available_version"] == "0.8.3"
    assert result["update_available"] is True
    assert result["settings_prompt_visible"] is True
    assert result["settings_action_state"]["install_action_exposed"] is False
    assert result["staged_artifact_ready"] is True
    assert result["installer_plan_preview_ready"] is True
    assert result["installer_plan_preview"]["plan_file_write_performed"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["production_auto_update_complete"] is False
    assert current.read_bytes() == b"current-build"


def test_launcher_update_local_manifest_background_prompt_same_version_is_up_to_date(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_local_manifest_background_prompt_settings_action,
    )

    manifest = _write_local_manifest_for_prompt(tmp_path, latest_version="0.8.2")

    result = build_launcher_update_local_manifest_background_prompt_settings_action(
        tmp_path,
        manifest_path=manifest,
        current_version="0.8.2",
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is True
    assert (
        result["status"]
        == "launcher_update_local_manifest_background_prompt_up_to_date"
    )
    assert result["version_comparison"]["installed_up_to_date"] is True
    assert result["settings_prompt_visible"] is False
    assert result["settings_install_control_exposed"] is False


def test_launcher_update_local_manifest_background_prompt_rejects_malformed_version(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_local_manifest_background_prompt_settings_action,
    )

    manifest = _write_local_manifest_for_prompt(tmp_path, latest_version="latest")

    result = build_launcher_update_local_manifest_background_prompt_settings_action(
        tmp_path,
        manifest_path=manifest,
        current_version="0.8.2",
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["status"] == (
        "launcher_update_local_manifest_background_prompt_malformed_manifest"
    )
    assert "latest_version_malformed" in result["errors"]
    assert result["settings_prompt_visible"] is False
    assert result["download_performed_by_this_proof"] is False


def test_launcher_update_local_manifest_background_prompt_blocks_invalid_checksum(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_local_manifest_background_prompt_settings_action,
    )

    staged = tmp_path / ".chaseos" / "updates" / "staged" / "ChaseOS-Studio.exe"
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_bytes(b"new-build")
    manifest = _write_local_manifest_for_prompt(
        tmp_path,
        artifact_path=staged,
        sha256="not-a-sha",
    )

    result = build_launcher_update_local_manifest_background_prompt_settings_action(
        tmp_path,
        manifest_path=manifest,
        current_version="0.8.2",
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["manifest_valid"] is False
    assert "artifact_sha256_invalid" in result["errors"]
    assert result["settings_prompt_visible"] is False
    assert result["staged_artifact_ready"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False


def test_launcher_update_local_manifest_background_prompt_default_no_manifest(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_local_manifest_background_prompt_settings_action,
    )

    result = build_launcher_update_local_manifest_background_prompt_settings_action(
        tmp_path,
        current_version="0.8.2",
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["status"] == (
        "launcher_update_local_manifest_background_prompt_no_manifest_configured"
    )
    assert result["manifest_read_performed"] is False
    assert result["settings_prompt_visible"] is False
    assert result["settings_download_control_exposed"] is False
    assert result["settings_install_control_exposed"] is False


def test_launcher_update_local_release_channel_blocker_closeout_reports_only_external_blockers(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_local_release_channel_blocker_closeout,
    )

    _write_dist_artifact_isolation_cohabitation_fixture(tmp_path)

    result = build_launcher_update_local_release_channel_blocker_closeout(
        tmp_path,
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is True, result["errors"]
    assert result["surface"] == (
        "studio_launcher_update_local_release_channel_blocker_closeout"
    )
    assert result["status"] == (
        "launcher_update_local_release_channel_blocker_closeout_"
        "only_external_blockers_remain"
    )
    assert result["local_closeout_ready"] is True
    assert result["only_external_blockers_remain"] is True
    assert result["non_external_blockers"] == []
    assert result["dist_artifacts_cohabitation_ready"] is True
    assert result["local_manifest_configured"] is False
    assert "release_channel_hosting_not_connected" in result["external_blocker_ids"]
    assert "production_signing_not_verified" in result["external_blocker_ids"]
    assert result["closeout_summary"][
        "local_passes_remaining_before_external_blocker"
    ] == 0
    assert result["settings_install_control_exposed"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["production_auto_update_complete"] is False


def test_launcher_update_local_release_channel_blocker_closeout_blocks_missing_artifacts(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_local_release_channel_blocker_closeout,
    )

    result = build_launcher_update_local_release_channel_blocker_closeout(
        tmp_path,
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["status"] == (
        "launcher_update_local_release_channel_blocker_closeout_"
        "local_blockers_remaining"
    )
    assert "dist_artifacts_cohabitation_ready" in result["non_external_blockers"]
    assert "chaseos_studio_artifact_present" in result["non_external_blockers"]
    assert "chaseos_installer_artifact_present" in result["non_external_blockers"]
    assert result["only_external_blockers_remain"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False


def test_launcher_update_post_wrapper_removal_regression_from_materialization_import_blocks_default_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        vault_root,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["surface"] == (
        "studio_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof"
    )
    assert result["status"] == (
        "launcher_update_post_wrapper_removal_regression_from_materialization_import_blocked"
    )
    assert (
        result["wrapper_removal_from_materialization_import_verified"] is False
    )
    assert result["regression_command_plan_ready"] is True
    assert result["regression_evidence_required"] is False
    assert result["regression_evidence_verified"] is False
    assert result["regression_commands_executed_by_chaseos"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert (
        "current_vault_wrapper_removal_from_materialization_import_execution_proof_required"
        in result["errors"]
    )


def test_launcher_update_post_wrapper_removal_regression_from_materialization_import_verifies_supplied_evidence(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof,
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement,
    )

    fixture = _fixture_materialization_import_wrapper_removal_proof(tmp_path)
    assert fixture["restored"]["ok"] is True

    preview = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        generated_at=fixture["timestamp"],
    )

    assert preview["ok"] is False
    assert preview["status"] == (
        "launcher_update_post_wrapper_removal_regression_from_materialization_import_"
        "regression_evidence_required"
    )
    assert (
        preview["wrapper_removal_from_materialization_import_execution_digest_valid"]
        is True
    )
    assert (
        preview["wrapper_removal_from_materialization_import_verified"] is True
    )
    assert preview["regression_evidence_required"] is True
    assert preview["regression_evidence_verified"] is False
    assert preview["source_write_previously_performed"] is True
    assert preview["wrapper_removal_previously_performed"] is True
    assert preview["source_write_performed"] is False
    assert preview["wrapper_removal_performed"] is False
    assert preview["regression_commands_executed_by_chaseos"] is False

    evidence = _fixture_regression_evidence(preview["regression_command_plan"])
    pending = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        regression_evidence=evidence,
        generated_at=fixture["timestamp"],
    )

    assert pending["ok"] is False
    assert pending["status"] == (
        "launcher_update_post_wrapper_removal_regression_from_materialization_import_"
        "pending_approval"
    )
    assert pending["regression_evidence_supplied"] is True
    assert pending["regression_evidence_verified"] is True
    assert pending["operator_statement_matched"] is False
    assert (
        "operator_post_wrapper_removal_regression_from_materialization_import_approval_required"
        in pending["errors"]
    )

    required_statement = (
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement(
            pending[
                "post_wrapper_removal_regression_from_materialization_import_plan"
            ]
        )
    )
    result = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        regression_evidence=evidence,
        operator_approved_post_wrapper_removal_regression=True,
        operator_statement=required_statement,
        generated_at=fixture["timestamp"],
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_post_wrapper_removal_regression_from_materialization_import_"
        "verified"
    )
    assert result["operator_statement_matched"] is True
    assert result["regression_evidence_verified"] is True
    assert result["current_vault_wrappers_removed"] is True
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["regression_commands_executed_by_chaseos"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True


def test_launcher_update_current_vault_source_closeout_from_materialization_import_regression_blocks_default_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof(
        vault_root,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["surface"] == (
        "studio_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof"
    )
    assert result["status"] == (
        "launcher_update_current_vault_source_closeout_from_materialization_import_"
        "regression_blocked"
    )
    assert (
        result[
            "post_wrapper_removal_regression_from_materialization_import_verified"
        ]
        is False
    )
    assert result["source_recovery_cleanup_ready"] is False
    assert result["current_vault_wrappers_removed"] is False
    assert (
        result[
            "current_vault_source_closeout_from_materialization_import_regression_ready"
        ]
        is False
    )
    assert result["source_restoration_closeout_ready_for_primary_exe_resume"] is False
    assert result["regression_commands_executed_by_chaseos"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert (
        "post_wrapper_removal_regression_from_materialization_import_proof_required"
        in result["errors"]
    )
    assert (
        "post_wrapper_removal_regression_from_materialization_import_not_verified"
        in result["errors"]
    )
    assert "source_recovery_cleanup_not_ready" in result["errors"]


def test_launcher_update_current_vault_source_closeout_from_materialization_import_regression_verifies_supplied_evidence(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof,
        build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof,
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement,
    )

    fixture = _fixture_materialization_import_wrapper_removal_proof(tmp_path)
    preview = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        generated_at=fixture["timestamp"],
    )
    evidence = _fixture_regression_evidence(preview["regression_command_plan"])
    pending = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        regression_evidence=evidence,
        generated_at=fixture["timestamp"],
    )
    required_statement = (
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement(
            pending[
                "post_wrapper_removal_regression_from_materialization_import_plan"
            ]
        )
    )
    regression = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        regression_evidence=evidence,
        operator_approved_post_wrapper_removal_regression=True,
        operator_statement=required_statement,
        generated_at=fixture["timestamp"],
    )
    cleanup = _fixture_source_recovery_cleanup_ready_proof(
        tmp_path,
        fixture["timestamp"],
    )

    result = build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof(
        tmp_path,
        post_wrapper_removal_regression_from_materialization_import_proof=regression,
        source_recovery_cleanup_proof=cleanup,
        generated_at=fixture["timestamp"],
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_current_vault_source_closeout_from_materialization_import_"
        "regression_ready"
    )
    assert (
        result[
            "post_wrapper_removal_regression_from_materialization_import_digest_matched"
        ]
        is True
    )
    assert result["source_recovery_cleanup_digest_matched"] is True
    assert (
        result[
            "post_wrapper_removal_regression_from_materialization_import_verified"
        ]
        is True
    )
    assert result["source_recovery_cleanup_ready"] is True
    assert result["current_vault_wrappers_removed"] is True
    assert (
        result[
            "current_vault_source_closeout_from_materialization_import_regression_ready"
        ]
        is True
    )
    assert result["source_restoration_closeout_ready_for_primary_exe_resume"] is True
    assert result["source_write_previously_performed"] is True
    assert result["wrapper_removal_previously_performed"] is True
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["regression_commands_executed_by_chaseos"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True


def test_launcher_update_production_primary_closeout_after_source_recovery_blocks_default_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_production_primary_closeout_after_source_recovery_proof,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = build_launcher_update_production_primary_closeout_after_source_recovery_proof(
        vault_root,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_production_primary_closeout_after_source_recovery_proof"
    )
    assert (
        result["status"]
        == "launcher_update_production_primary_closeout_after_source_recovery_blocked"
    )
    assert result["source_closeout_ready"] is False
    assert result["primary_relaunch_receipt_boundary_ready"] is False
    assert (
        result[
            "production_primary_closeout_after_source_recovery_ready_for_final_audit"
        ]
        is False
    )
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["helper_launch_performed"] is False
    assert result["installer_launch_performed"] is False
    assert result["relaunch_performed_by_chaseos"] is False
    assert result["os_process_spawn_performed_by_chaseos"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["primary_exe_replacement_performed_by_chaseos"] is False
    assert result["settings_write_control_exposed"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert (
        "current_vault_source_closeout_from_materialization_import_regression_proof_required"
        in result["errors"]
    )
    assert (
        "production_primary_relaunch_receipt_boundary_proof_required"
        in result["errors"]
    )


def test_launcher_update_production_primary_closeout_after_source_recovery_readies_final_audit_only(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof,
        build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof,
        build_launcher_update_production_primary_closeout_after_source_recovery_proof,
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement,
    )

    fixture = _fixture_materialization_import_wrapper_removal_proof(tmp_path)
    preview = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        generated_at=fixture["timestamp"],
    )
    evidence = _fixture_regression_evidence(preview["regression_command_plan"])
    pending = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        regression_evidence=evidence,
        generated_at=fixture["timestamp"],
    )
    required_statement = (
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement(
            pending[
                "post_wrapper_removal_regression_from_materialization_import_plan"
            ]
        )
    )
    regression = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        regression_evidence=evidence,
        operator_approved_post_wrapper_removal_regression=True,
        operator_statement=required_statement,
        generated_at=fixture["timestamp"],
    )
    source_closeout = build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof(
        tmp_path,
        post_wrapper_removal_regression_from_materialization_import_proof=regression,
        source_recovery_cleanup_proof=_fixture_source_recovery_cleanup_ready_proof(
            tmp_path,
            fixture["timestamp"],
        ),
        generated_at=fixture["timestamp"],
    )
    primary_relaunch = _fixture_primary_relaunch_receipt_boundary_ready_proof(
        tmp_path,
        fixture["timestamp"],
    )

    result = build_launcher_update_production_primary_closeout_after_source_recovery_proof(
        tmp_path,
        current_vault_source_closeout_from_materialization_import_regression_proof=source_closeout,
        production_primary_relaunch_receipt_boundary_proof=primary_relaunch,
        generated_at=fixture["timestamp"],
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_production_primary_closeout_after_source_recovery_"
        "ready_for_final_update_closeout_audit"
    )
    assert result["source_closeout_digest_matched"] is True
    assert result["primary_relaunch_receipt_boundary_digest_matched"] is True
    assert result["source_closeout_ready"] is True
    assert result["primary_relaunch_receipt_boundary_ready"] is True
    assert result["primary_relaunch_receipt_valid"] is True
    assert result["external_helper_primary_relaunch_reported"] is True
    assert result["external_helper_primary_replacement_reported"] is True
    assert (
        result[
            "production_primary_closeout_after_source_recovery_ready_for_final_audit"
        ]
        is True
    )
    assert result["requires_final_update_closeout_audit"] is True
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["helper_launch_performed"] is False
    assert result["installer_launch_performed"] is False
    assert result["relaunch_performed_by_chaseos"] is False
    assert result["os_process_spawn_performed_by_chaseos"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["primary_exe_replacement_performed_by_chaseos"] is False
    assert result["primary_real_executable_replacement_verified_live"] is False
    assert result["settings_write_control_exposed"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True


def test_launcher_update_final_production_auto_update_closeout_audit_blocks_default_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_final_production_auto_update_closeout_audit,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = build_launcher_update_final_production_auto_update_closeout_audit(
        vault_root,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_final_production_auto_update_closeout_audit"
    )
    assert (
        result["status"]
        == "launcher_update_final_production_auto_update_closeout_audit_blocked"
    )
    assert (
        result[
            "production_primary_closeout_after_source_recovery_ready_for_final_audit"
        ]
        is False
    )
    assert result["live_completion_evidence_verified"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert result["helper_launch_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["github_mutation_performed_by_this_proof"] is False
    assert result["primary_exe_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert (
        "production_primary_closeout_after_source_recovery_proof_required"
        in result["errors"]
    )
    assert "live_completion_evidence_required" in result["errors"]


def test_launcher_update_final_production_auto_update_closeout_audit_requires_live_evidence_after_primary_closeout(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof,
        build_launcher_update_final_production_auto_update_closeout_audit,
        build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof,
        build_launcher_update_production_primary_closeout_after_source_recovery_proof,
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement,
    )

    fixture = _fixture_materialization_import_wrapper_removal_proof(tmp_path)
    preview = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        generated_at=fixture["timestamp"],
    )
    evidence = _fixture_regression_evidence(preview["regression_command_plan"])
    pending = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        regression_evidence=evidence,
        generated_at=fixture["timestamp"],
    )
    required_statement = (
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement(
            pending[
                "post_wrapper_removal_regression_from_materialization_import_plan"
            ]
        )
    )
    regression = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        regression_evidence=evidence,
        operator_approved_post_wrapper_removal_regression=True,
        operator_statement=required_statement,
        generated_at=fixture["timestamp"],
    )
    source_closeout = build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof(
        tmp_path,
        post_wrapper_removal_regression_from_materialization_import_proof=regression,
        source_recovery_cleanup_proof=_fixture_source_recovery_cleanup_ready_proof(
            tmp_path,
            fixture["timestamp"],
        ),
        generated_at=fixture["timestamp"],
    )
    primary_closeout = build_launcher_update_production_primary_closeout_after_source_recovery_proof(
        tmp_path,
        current_vault_source_closeout_from_materialization_import_regression_proof=source_closeout,
        production_primary_relaunch_receipt_boundary_proof=_fixture_primary_relaunch_receipt_boundary_ready_proof(
            tmp_path,
            fixture["timestamp"],
        ),
        generated_at=fixture["timestamp"],
    )

    result = build_launcher_update_final_production_auto_update_closeout_audit(
        tmp_path,
        production_primary_closeout_after_source_recovery_proof=primary_closeout,
        generated_at=fixture["timestamp"],
    )

    assert result["ok"] is False
    assert result["status"] == (
        "launcher_update_final_production_auto_update_closeout_audit_"
        "live_completion_evidence_required"
    )
    assert (
        result[
            "production_primary_closeout_after_source_recovery_ready_for_final_audit"
        ]
        is True
    )
    assert result["production_primary_closeout_after_source_recovery_digest_matched"] is True
    assert result["live_completion_evidence_verified"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert result["helper_launch_performed_by_this_proof"] is False
    assert result["primary_exe_replacement_performed_by_this_proof"] is False
    assert "live_completion_evidence_required" in result["errors"]


def test_launcher_update_final_production_auto_update_closeout_audit_verifies_supplied_live_evidence_only(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof,
        build_launcher_update_final_production_auto_update_closeout_audit,
        build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof,
        build_launcher_update_production_primary_closeout_after_source_recovery_proof,
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement,
    )

    fixture = _fixture_materialization_import_wrapper_removal_proof(tmp_path)
    preview = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        generated_at=fixture["timestamp"],
    )
    regression_evidence = _fixture_regression_evidence(preview["regression_command_plan"])
    pending = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        regression_evidence=regression_evidence,
        generated_at=fixture["timestamp"],
    )
    required_statement = (
        required_update_post_wrapper_removal_regression_from_materialization_import_operator_statement(
            pending[
                "post_wrapper_removal_regression_from_materialization_import_plan"
            ]
        )
    )
    regression = build_launcher_update_post_wrapper_removal_regression_from_materialization_import_proof(
        tmp_path,
        wrapper_removal_from_materialization_import_execution_proof=fixture["restored"],
        regression_evidence=regression_evidence,
        operator_approved_post_wrapper_removal_regression=True,
        operator_statement=required_statement,
        generated_at=fixture["timestamp"],
    )
    source_closeout = build_launcher_update_current_vault_source_closeout_from_materialization_import_regression_proof(
        tmp_path,
        post_wrapper_removal_regression_from_materialization_import_proof=regression,
        source_recovery_cleanup_proof=_fixture_source_recovery_cleanup_ready_proof(
            tmp_path,
            fixture["timestamp"],
        ),
        generated_at=fixture["timestamp"],
    )
    primary_closeout = build_launcher_update_production_primary_closeout_after_source_recovery_proof(
        tmp_path,
        current_vault_source_closeout_from_materialization_import_regression_proof=source_closeout,
        production_primary_relaunch_receipt_boundary_proof=_fixture_primary_relaunch_receipt_boundary_ready_proof(
            tmp_path,
            fixture["timestamp"],
        ),
        generated_at=fixture["timestamp"],
    )
    live_evidence = _fixture_final_production_auto_update_live_completion_evidence(
        tmp_path,
        fixture["timestamp"],
    )

    result = build_launcher_update_final_production_auto_update_closeout_audit(
        tmp_path,
        production_primary_closeout_after_source_recovery_proof=primary_closeout,
        live_completion_evidence=live_evidence,
        generated_at=fixture["timestamp"],
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_final_production_auto_update_closeout_audit_"
        "verified_complete"
    )
    assert (
        result[
            "production_primary_closeout_after_source_recovery_ready_for_final_audit"
        ]
        is True
    )
    assert result["live_completion_evidence_digest_matched"] is True
    assert result["live_completion_evidence_verified"] is True
    assert result["github_release_publication_verified"] is True
    assert result["live_binary_download_verified"] is True
    assert result["downloaded_artifact_signature_verified"] is True
    assert result["chaseos_installer_launch_receipt_verified"] is True
    assert result["primary_exe_replacement_verified_live"] is True
    assert result["primary_relaunch_verified_live"] is True
    assert result["startup_background_prompt_verified"] is True
    assert result["production_auto_update_complete"] is True
    assert result["final_auto_update_closeout_blocked"] is False
    assert result["helper_launch_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["github_mutation_performed_by_this_proof"] is False
    assert result["source_write_performed_by_this_proof"] is False
    assert result["primary_exe_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False


def test_launcher_update_governed_live_completion_evidence_packet_blocks_default_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_governed_live_completion_evidence_packet,
    )

    result = build_launcher_update_governed_live_completion_evidence_packet(
        tmp_path,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_governed_live_completion_evidence_packet"
    )
    assert result["status"] == (
        "launcher_update_governed_live_completion_evidence_packet_claims_required"
    )
    assert result["live_completion_evidence_verified"] is False
    assert result["feeds_final_production_auto_update_closeout_audit"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert result["github_mutation_performed_by_this_proof"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["helper_launch_performed_by_this_proof"] is False
    assert result["source_write_performed_by_this_proof"] is False
    assert result["primary_exe_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert "live_completion_evidence_claims_required" in result["errors"]
    assert "operator_live_completion_evidence_approval_required" in result["errors"]
    assert "operator_statement_mismatch" in result["errors"]


def test_launcher_update_governed_live_completion_evidence_packet_readies_audit_input_only(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_governed_live_completion_evidence_packet,
        required_update_governed_live_completion_evidence_operator_statement,
    )

    timestamp = "2026-05-25T00:00:00Z"
    claims = _fixture_final_production_auto_update_live_completion_claims(
        tmp_path,
        timestamp,
    )
    preview = build_launcher_update_governed_live_completion_evidence_packet(
        tmp_path,
        evidence_claims=claims,
        generated_at=timestamp,
    )
    operator_statement = required_update_governed_live_completion_evidence_operator_statement(
        preview["evidence_plan"]
    )

    result = build_launcher_update_governed_live_completion_evidence_packet(
        tmp_path,
        evidence_claims=claims,
        operator_approved_live_completion_evidence=True,
        operator_statement=operator_statement,
        generated_at=timestamp,
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_governed_live_completion_evidence_packet_ready"
    )
    assert result["operator_statement_matched"] is True
    assert result["live_completion_evidence_digest_matched"] is True
    assert result["live_completion_evidence_verified"] is True
    assert result["feeds_final_production_auto_update_closeout_audit"] is True
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert result["github_mutation_performed_by_this_proof"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["helper_launch_performed_by_this_proof"] is False
    assert result["source_write_performed_by_this_proof"] is False
    assert result["primary_exe_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["live_completion_evidence"]["primary_exe_replacement_verified_live"] is True
    assert result["live_completion_evidence"]["silent_install_performed"] is False


def test_launcher_update_final_production_auto_update_closeout_audit_accepts_governed_evidence_packet(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_final_production_auto_update_closeout_audit,
        build_launcher_update_governed_live_completion_evidence_packet,
        required_update_governed_live_completion_evidence_operator_statement,
    )

    primary_closeout, timestamp = (
        _fixture_production_primary_closeout_after_source_recovery_ready(tmp_path)
    )
    claims = _fixture_final_production_auto_update_live_completion_claims(
        tmp_path,
        timestamp,
    )
    preview = build_launcher_update_governed_live_completion_evidence_packet(
        tmp_path,
        evidence_claims=claims,
        generated_at=timestamp,
    )
    operator_statement = required_update_governed_live_completion_evidence_operator_statement(
        preview["evidence_plan"]
    )
    packet = build_launcher_update_governed_live_completion_evidence_packet(
        tmp_path,
        evidence_claims=claims,
        operator_approved_live_completion_evidence=True,
        operator_statement=operator_statement,
        generated_at=timestamp,
    )

    result = build_launcher_update_final_production_auto_update_closeout_audit(
        tmp_path,
        production_primary_closeout_after_source_recovery_proof=primary_closeout,
        live_completion_evidence=packet,
        generated_at=timestamp,
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_final_production_auto_update_closeout_audit_"
        "verified_complete"
    )
    assert result["governed_live_completion_evidence_packet_supplied"] is True
    assert result["governed_live_completion_evidence_packet_digest_matched"] is True
    assert result["live_completion_evidence_digest_matched"] is True
    assert result["live_completion_evidence_verified"] is True
    assert result["production_auto_update_complete"] is True
    assert result["final_auto_update_closeout_blocked"] is False
    assert result["helper_launch_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["github_mutation_performed_by_this_proof"] is False
    assert result["source_write_performed_by_this_proof"] is False
    assert result["primary_exe_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False


def test_launcher_update_controlled_live_installer_evidence_runner_blocks_default_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_controlled_live_installer_evidence_runner,
    )

    result = build_launcher_update_controlled_live_installer_evidence_runner(
        tmp_path,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_controlled_live_installer_evidence_runner"
    )
    assert (
        result["status"]
        == "launcher_update_controlled_live_installer_evidence_runner_blocked"
    )
    assert result["runner_execution_allowed"] is False
    assert result["runner_execution_performed"] is False
    assert result["governed_live_completion_evidence_packet_ready"] is False
    assert result["feeds_final_production_auto_update_closeout_audit"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert result["settings_install_control_exposed"] is False
    assert result["source_write_performed_by_this_proof"] is False
    assert "controlled_live_installer_evidence_runner_required" in result["errors"]
    assert (
        "operator_live_installer_evidence_runner_approval_required"
        in result["errors"]
    )
    assert "live_download_approval_required" in result["errors"]
    assert "primary_replacement_approval_required" in result["errors"]


def test_launcher_update_controlled_live_installer_evidence_runner_builds_governed_packet_from_approved_runner(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_controlled_live_installer_evidence_runner,
        required_update_controlled_live_installer_evidence_runner_operator_statement,
    )

    timestamp = "2026-05-25T00:00:00Z"
    claims = _fixture_final_production_auto_update_live_completion_claims(
        tmp_path,
        timestamp,
    )
    evidence_runner = _fixture_controlled_live_installer_evidence_runner(claims)
    preview = build_launcher_update_controlled_live_installer_evidence_runner(
        tmp_path,
        evidence_runner=evidence_runner,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )
    operator_statement = required_update_controlled_live_installer_evidence_runner_operator_statement(
        preview["runner_plan"]
    )

    result = build_launcher_update_controlled_live_installer_evidence_runner(
        tmp_path,
        evidence_runner=evidence_runner,
        operator_approved_live_installer_evidence_runner=True,
        operator_statement=operator_statement,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_controlled_live_installer_evidence_runner_packet_ready"
    )
    assert result["operator_statement_matched"] is True
    assert result["runner_execution_allowed"] is True
    assert result["runner_execution_performed"] is True
    assert result["runner_receipt_digest_matched"] is True
    assert result["governed_live_completion_evidence_packet_ready"] is True
    assert result["governed_live_completion_evidence_packet_digest_matched"] is True
    assert result["live_completion_evidence_verified"] is True
    assert result["feeds_final_production_auto_update_closeout_audit"] is True
    assert result["download_performed_by_runner"] is True
    assert result["installer_launch_performed_by_runner"] is True
    assert result["primary_replacement_performed_by_runner"] is True
    assert result["primary_relaunch_performed_by_runner"] is True
    assert result["startup_prompt_verified_by_runner"] is True
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert result["settings_install_control_exposed"] is False
    assert result["source_write_performed_by_this_proof"] is False


def test_launcher_update_final_audit_accepts_controlled_runner_governed_packet(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_controlled_live_installer_evidence_runner,
        build_launcher_update_final_production_auto_update_closeout_audit,
        required_update_controlled_live_installer_evidence_runner_operator_statement,
    )

    primary_closeout, timestamp = (
        _fixture_production_primary_closeout_after_source_recovery_ready(tmp_path)
    )
    claims = _fixture_final_production_auto_update_live_completion_claims(
        tmp_path,
        timestamp,
    )
    evidence_runner = _fixture_controlled_live_installer_evidence_runner(claims)
    preview = build_launcher_update_controlled_live_installer_evidence_runner(
        tmp_path,
        evidence_runner=evidence_runner,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )
    operator_statement = required_update_controlled_live_installer_evidence_runner_operator_statement(
        preview["runner_plan"]
    )
    runner_result = build_launcher_update_controlled_live_installer_evidence_runner(
        tmp_path,
        evidence_runner=evidence_runner,
        operator_approved_live_installer_evidence_runner=True,
        operator_statement=operator_statement,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )

    result = build_launcher_update_final_production_auto_update_closeout_audit(
        tmp_path,
        production_primary_closeout_after_source_recovery_proof=primary_closeout,
        live_completion_evidence=runner_result[
            "governed_live_completion_evidence_packet"
        ],
        generated_at=timestamp,
    )

    assert runner_result["ok"] is True
    assert result["ok"] is True
    assert result["production_auto_update_complete"] is True
    assert result["governed_live_completion_evidence_packet_supplied"] is True
    assert result["governed_live_completion_evidence_packet_digest_matched"] is True
    assert result["live_completion_evidence_verified"] is True
    assert result["helper_launch_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["github_mutation_performed_by_this_proof"] is False
    assert result["primary_exe_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False


def test_launcher_update_approved_live_evidence_runner_adapter_blocks_default_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_approved_live_evidence_runner_adapter,
    )

    result = build_launcher_update_approved_live_evidence_runner_adapter(
        tmp_path,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_approved_live_evidence_runner_adapter"
    )
    assert result["status"] == (
        "launcher_update_approved_live_evidence_runner_adapter_blocked"
    )
    assert result["approved_live_evidence_runner_adapter_ready"] is False
    assert result["sources_ready"] is False
    assert result["adapter_runner_executed"] is False
    assert result["controlled_live_installer_evidence_runner_ready"] is False
    assert result["governed_live_completion_evidence_packet_ready"] is False
    assert result["feeds_final_production_auto_update_closeout_audit"] is False
    assert result["download_performed_by_adapter"] is False
    assert result["installer_launch_performed_by_adapter"] is False
    assert result["primary_replacement_performed_by_adapter"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert (
        "signed_release_manifest_live_readback_proof_required"
        in result["errors"]
    )
    assert (
        "operator_live_evidence_runner_adapter_approval_required"
        in result["errors"]
    )


def test_launcher_update_approved_live_evidence_runner_adapter_builds_governed_packet_from_source_proofs(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS,
        FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS,
        build_launcher_update_approved_live_evidence_runner_adapter,
        required_update_approved_live_evidence_runner_adapter_operator_statement,
    )

    timestamp = "2026-05-25T00:00:00Z"
    source_proofs = _fixture_approved_live_evidence_adapter_source_proofs(
        tmp_path,
        timestamp,
    )
    preview = build_launcher_update_approved_live_evidence_runner_adapter(
        tmp_path,
        **source_proofs,
        generated_at=timestamp,
    )
    operator_statement = required_update_approved_live_evidence_runner_adapter_operator_statement(
        preview["adapter_plan"]
    )

    result = build_launcher_update_approved_live_evidence_runner_adapter(
        tmp_path,
        **source_proofs,
        operator_approved_live_evidence_runner_adapter=True,
        operator_statement=operator_statement,
        generated_at=timestamp,
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_approved_live_evidence_runner_adapter_ready"
    )
    assert result["approved_live_evidence_runner_adapter_ready"] is True
    assert result["operator_statement_matched"] is True
    assert result["sources_ready"] is True
    assert all(item["ready"] for item in result["source_proof_checks"])
    assert result["adapter_runner_executed"] is True
    assert result["controlled_live_installer_evidence_runner_ready"] is True
    assert result["governed_live_completion_evidence_packet_ready"] is True
    assert result["live_completion_evidence_verified"] is True
    assert result["feeds_final_production_auto_update_closeout_audit"] is True
    for field in FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_TRUE_EVIDENCE_FIELDS:
        assert result["evidence_claims"][field] is True
    for field in FINAL_PRODUCTION_AUTO_UPDATE_REQUIRED_FALSE_EVIDENCE_FIELDS:
        assert result["evidence_claims"][field] is False
    assert result["download_performed_by_adapter"] is False
    assert result["installer_launch_performed_by_adapter"] is False
    assert result["primary_replacement_performed_by_adapter"] is False
    assert result["source_write_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True


def test_launcher_update_final_audit_accepts_approved_live_evidence_adapter_packet(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_approved_live_evidence_runner_adapter,
        build_launcher_update_final_production_auto_update_closeout_audit,
        required_update_approved_live_evidence_runner_adapter_operator_statement,
    )

    primary_closeout, timestamp = (
        _fixture_production_primary_closeout_after_source_recovery_ready(tmp_path)
    )
    source_proofs = _fixture_approved_live_evidence_adapter_source_proofs(
        tmp_path,
        timestamp,
    )
    preview = build_launcher_update_approved_live_evidence_runner_adapter(
        tmp_path,
        **source_proofs,
        generated_at=timestamp,
    )
    operator_statement = required_update_approved_live_evidence_runner_adapter_operator_statement(
        preview["adapter_plan"]
    )
    adapter_result = build_launcher_update_approved_live_evidence_runner_adapter(
        tmp_path,
        **source_proofs,
        operator_approved_live_evidence_runner_adapter=True,
        operator_statement=operator_statement,
        generated_at=timestamp,
    )

    result = build_launcher_update_final_production_auto_update_closeout_audit(
        tmp_path,
        production_primary_closeout_after_source_recovery_proof=primary_closeout,
        live_completion_evidence=adapter_result[
            "governed_live_completion_evidence_packet"
        ],
        generated_at=timestamp,
    )

    assert adapter_result["ok"] is True
    assert result["ok"] is True
    assert result["production_auto_update_complete"] is True
    assert result["governed_live_completion_evidence_packet_supplied"] is True
    assert result["governed_live_completion_evidence_packet_digest_matched"] is True
    assert result["live_completion_evidence_verified"] is True
    assert result["helper_launch_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["github_mutation_performed_by_this_proof"] is False
    assert result["primary_exe_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False


def test_launcher_update_approved_live_evidence_runner_real_dry_run_blocks_default_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_approved_live_evidence_runner_real_dry_run,
    )

    result = build_launcher_update_approved_live_evidence_runner_real_dry_run(
        tmp_path,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_approved_live_evidence_runner_real_dry_run"
    )
    assert result["status"] == (
        "launcher_update_approved_live_evidence_runner_real_dry_run_blocked"
    )
    assert result["current_vault_source_proofs_collected"] is True
    assert result["sources_ready"] is False
    assert result["approved_live_evidence_runner_adapter_ready"] is False
    assert result["governed_live_completion_evidence_packet_ready"] is False
    assert result["final_production_auto_update_closeout_audit_ready"] is False
    assert result["download_performed_by_dry_run"] is False
    assert result["installer_launch_performed_by_dry_run"] is False
    assert result["primary_replacement_performed_by_dry_run"] is False
    assert result["startup_mutation_performed_by_dry_run"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["final_auto_update_closeout_blocked"] is True
    assert (
        "operator_live_evidence_runner_real_dry_run_approval_required"
        in result["errors"]
    )
    assert any(
        item.startswith("signed_release_manifest_live_readback_")
        for item in result["errors"]
    )


def test_launcher_update_approved_live_evidence_runner_real_dry_run_builds_adapter_packet_from_supplied_proofs(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_approved_live_evidence_runner_real_dry_run,
        required_update_approved_live_evidence_runner_real_dry_run_operator_statement,
    )

    timestamp = "2026-05-25T00:00:00Z"
    source_proofs = _fixture_approved_live_evidence_adapter_source_proofs(
        tmp_path,
        timestamp,
    )
    preview = build_launcher_update_approved_live_evidence_runner_real_dry_run(
        tmp_path,
        **source_proofs,
        generated_at=timestamp,
    )
    operator_statement = (
        required_update_approved_live_evidence_runner_real_dry_run_operator_statement(
            preview["dry_run_plan"]
        )
    )

    result = build_launcher_update_approved_live_evidence_runner_real_dry_run(
        tmp_path,
        **source_proofs,
        operator_approved_live_evidence_runner_real_dry_run=True,
        operator_statement=operator_statement,
        generated_at=timestamp,
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_approved_live_evidence_runner_real_dry_run_packet_ready"
    )
    assert result["current_vault_source_proofs_collected"] is False
    assert result["operator_statement_matched"] is True
    assert result["sources_ready"] is True
    assert all(item["ready"] for item in result["source_proof_checks"])
    assert result["approved_live_evidence_runner_adapter_ready"] is True
    assert result["governed_live_completion_evidence_packet_ready"] is True
    assert result["feeds_final_production_auto_update_closeout_audit"] is True
    assert result["final_production_auto_update_closeout_audit_ready"] is False
    assert result["download_performed_by_dry_run"] is False
    assert result["installer_launch_performed_by_dry_run"] is False
    assert result["primary_replacement_performed_by_dry_run"] is False
    assert result["source_write_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False


def test_launcher_update_approved_live_evidence_runner_real_dry_run_previews_final_audit_with_primary_closeout(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_approved_live_evidence_runner_real_dry_run,
        required_update_approved_live_evidence_runner_real_dry_run_operator_statement,
    )

    primary_closeout, timestamp = (
        _fixture_production_primary_closeout_after_source_recovery_ready(tmp_path)
    )
    source_proofs = _fixture_approved_live_evidence_adapter_source_proofs(
        tmp_path,
        timestamp,
    )
    preview = build_launcher_update_approved_live_evidence_runner_real_dry_run(
        tmp_path,
        **source_proofs,
        production_primary_closeout_after_source_recovery_proof=primary_closeout,
        generated_at=timestamp,
    )
    operator_statement = (
        required_update_approved_live_evidence_runner_real_dry_run_operator_statement(
            preview["dry_run_plan"]
        )
    )

    result = build_launcher_update_approved_live_evidence_runner_real_dry_run(
        tmp_path,
        **source_proofs,
        production_primary_closeout_after_source_recovery_proof=primary_closeout,
        operator_approved_live_evidence_runner_real_dry_run=True,
        operator_statement=operator_statement,
        generated_at=timestamp,
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_approved_live_evidence_runner_real_dry_run_final_audit_ready"
    )
    assert result["approved_live_evidence_runner_adapter_ready"] is True
    assert result["governed_live_completion_evidence_packet_ready"] is True
    assert result["final_production_auto_update_closeout_audit_ready"] is True
    assert result["final_audit_production_auto_update_complete"] is True
    assert result["production_auto_update_complete"] is False
    assert result["download_performed_by_dry_run"] is False
    assert result["installer_launch_performed_by_dry_run"] is False
    assert result["primary_replacement_performed_by_dry_run"] is False
    assert result["settings_install_control_exposed"] is False


def test_launcher_update_live_receipt_digest_consistency_closeout_normalizes_blocked_default_receipts(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_live_receipt_digest_consistency_closeout,
    )

    result = build_launcher_update_live_receipt_digest_consistency_closeout(
        tmp_path,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_live_receipt_digest_consistency_closeout_"
        "ready_but_receipts_not_ready"
    )
    assert result["current_vault_source_proofs_collected"] is True
    assert result["digest_consistency_closeout_ready"] is True
    assert result["source_receipts_ready"] is False
    assert result["normalized_blocked_receipt_digest_count"] >= 1
    assert result["ready_digest_mismatch_rejected"] is False
    assert result["receipt_readiness_blockers"]
    assert all(item["effective_digest_matched"] for item in result["digest_checks"])
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False


def test_launcher_update_live_receipt_digest_consistency_closeout_rejects_ready_digest_mismatch(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_live_receipt_digest_consistency_closeout,
    )

    timestamp = "2026-05-25T00:00:00Z"
    source_proofs = _fixture_approved_live_evidence_adapter_source_proofs(
        tmp_path,
        timestamp,
    )
    source_proofs["signed_release_manifest_live_readback"][
        "signed_release_manifest_live_readback_digest_sha256"
    ] = "0" * 64

    result = build_launcher_update_live_receipt_digest_consistency_closeout(
        tmp_path,
        **source_proofs,
        generated_at=timestamp,
    )

    assert result["ok"] is False
    assert (
        result["status"]
        == "launcher_update_live_receipt_digest_consistency_closeout_blocked"
    )
    assert result["ready_digest_mismatch_rejected"] is True
    assert (
        "signed_release_manifest_live_readback_ready_digest_mismatch"
        in result["errors"]
    )
    assert result["source_receipts_ready"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False


def test_launcher_update_live_receipt_digest_consistency_closeout_accepts_ready_supplied_receipts(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_live_receipt_digest_consistency_closeout,
    )

    timestamp = "2026-05-25T00:00:00Z"
    source_proofs = _fixture_approved_live_evidence_adapter_source_proofs(
        tmp_path,
        timestamp,
    )

    result = build_launcher_update_live_receipt_digest_consistency_closeout(
        tmp_path,
        **source_proofs,
        generated_at=timestamp,
    )

    assert result["ok"] is True
    assert (
        result["status"]
        == "launcher_update_live_receipt_digest_consistency_closeout_ready"
    )
    assert result["current_vault_source_proofs_collected"] is False
    assert result["digest_consistency_closeout_ready"] is True
    assert result["source_receipts_ready"] is True
    assert result["normalized_blocked_receipt_digest_count"] == 0
    assert result["receipt_readiness_blockers"] == []
    assert all(item["effective_ready"] for item in result["digest_checks"])
    assert result["production_auto_update_complete"] is False


def test_launcher_update_real_live_receipt_capture_boundary_blocks_default_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_live_receipt_capture_boundary,
    )

    result = build_launcher_update_real_live_receipt_capture_boundary(
        tmp_path,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["surface"] == "studio_launcher_update_real_live_receipt_capture_boundary"
    assert result["status"] == (
        "launcher_update_real_live_receipt_capture_boundary_blocked"
    )
    assert result["receipt_bundle_valid"] is False
    assert result["source_receipts_ready"] is False
    assert result["approved_live_evidence_runner_real_dry_run_ready"] is False
    assert result["governed_live_completion_evidence_packet_ready"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert "real_live_receipt_bundle_required" in result["errors"]
    assert (
        "operator_real_live_receipt_capture_approval_required"
        in result["errors"]
    )


def test_launcher_update_real_live_receipt_capture_boundary_validates_bundle_before_approval(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_live_receipt_capture_boundary,
    )

    timestamp = "2026-05-25T00:00:00Z"
    bundle = _fixture_real_live_receipt_bundle(tmp_path, timestamp)

    result = build_launcher_update_real_live_receipt_capture_boundary(
        tmp_path,
        live_receipt_bundle=bundle,
        generated_at=timestamp,
    )

    assert result["ok"] is False
    assert result["status"] == (
        "launcher_update_real_live_receipt_capture_boundary_operator_approval_required"
    )
    assert result["receipt_bundle_valid"] is True
    assert result["receipt_bundle_digest_matched"] is True
    assert result["digest_consistency_closeout_ready"] is True
    assert result["source_receipts_ready"] is True
    assert result["governed_live_completion_evidence_packet_ready"] is False
    assert (
        "operator_real_live_receipt_capture_approval_required"
        in result["errors"]
    )
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False


def test_launcher_update_real_live_receipt_capture_boundary_feeds_real_dry_run_packet(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_live_receipt_capture_boundary,
        required_update_real_live_receipt_capture_boundary_operator_statement,
    )

    timestamp = "2026-05-25T00:00:00Z"
    bundle = _fixture_real_live_receipt_bundle(tmp_path, timestamp)
    preview = build_launcher_update_real_live_receipt_capture_boundary(
        tmp_path,
        live_receipt_bundle=bundle,
        generated_at=timestamp,
    )
    operator_statement = (
        required_update_real_live_receipt_capture_boundary_operator_statement(
            preview["capture_plan"]
        )
    )

    result = build_launcher_update_real_live_receipt_capture_boundary(
        tmp_path,
        live_receipt_bundle=bundle,
        operator_approved_real_live_receipt_capture=True,
        operator_statement=operator_statement,
        generated_at=timestamp,
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_real_live_receipt_capture_boundary_packet_ready"
    )
    assert result["operator_statement_matched"] is True
    assert result["receipt_bundle_valid"] is True
    assert result["source_receipts_ready"] is True
    assert result["approved_live_evidence_runner_real_dry_run_ready"] is True
    assert result["governed_live_completion_evidence_packet_ready"] is True
    assert result["feeds_final_production_auto_update_closeout_audit"] is True
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["source_write_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False


def test_launcher_update_real_live_receipt_capture_boundary_rejects_ready_source_digest_mismatch(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        _extension_digest_without,
        build_launcher_update_real_live_receipt_capture_boundary,
    )

    timestamp = "2026-05-25T00:00:00Z"
    source_proofs = _fixture_approved_live_evidence_adapter_source_proofs(
        tmp_path,
        timestamp,
    )
    source_proofs["signed_release_manifest_live_readback"][
        "signed_release_manifest_live_readback_digest_sha256"
    ] = "0" * 64
    bundle = _fixture_real_live_receipt_bundle(
        tmp_path,
        timestamp,
        source_proofs=source_proofs,
    )
    bundle["real_live_receipt_bundle_digest_sha256"] = _extension_digest_without(
        bundle,
        "real_live_receipt_bundle_digest_sha256",
    )

    result = build_launcher_update_real_live_receipt_capture_boundary(
        tmp_path,
        live_receipt_bundle=bundle,
        generated_at=timestamp,
    )

    assert result["ok"] is False
    assert result["receipt_bundle_valid"] is True
    assert result["digest_consistency_closeout_ready"] is False
    assert result["source_receipts_ready"] is False
    assert result["governed_live_completion_evidence_packet_ready"] is False
    assert (
        "receipt_digest_closeout:signed_release_manifest_live_readback_ready_digest_mismatch"
        in result["errors"]
    )
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False


def test_launcher_update_real_live_receipt_bundle_production_runner_blocks_default_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_live_receipt_bundle_production_runner,
    )

    result = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_real_live_receipt_bundle_production_runner"
    )
    assert result["status"] == (
        "launcher_update_real_live_receipt_bundle_production_runner_blocked"
    )
    assert result["runner_execution_performed"] is False
    assert result["receipt_bundle_valid"] is False
    assert result["capture_boundary_ready"] is False
    assert result["governed_live_completion_evidence_packet_ready"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert "real_live_receipt_bundle_runner_required" in result["errors"]
    assert (
        "operator_real_live_receipt_bundle_runner_approval_required"
        in result["errors"]
    )


def test_launcher_update_real_live_receipt_bundle_production_runner_requires_operator_statement_before_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_live_receipt_bundle_production_runner,
    )

    result = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=_fixture_real_live_receipt_bundle_production_runner(),
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["status"] == (
        "launcher_update_real_live_receipt_bundle_production_runner_pending_approval"
    )
    assert result["runner_execution_allowed"] is False
    assert result["runner_execution_performed"] is False
    assert result["capture_boundary_ready"] is False
    assert result["governed_live_completion_evidence_packet_ready"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert (
        "operator_real_live_receipt_bundle_runner_approval_required"
        in result["errors"]
    )


def test_launcher_update_real_live_receipt_bundle_production_runner_feeds_capture_boundary_packet(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_live_receipt_bundle_production_runner,
        required_update_real_live_receipt_bundle_production_runner_operator_statement,
    )

    timestamp = "2026-05-25T00:00:00Z"
    runner = _fixture_real_live_receipt_bundle_production_runner()
    preview = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=runner,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )
    operator_statement = (
        required_update_real_live_receipt_bundle_production_runner_operator_statement(
            preview["runner_plan"]
        )
    )

    result = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=runner,
        operator_approved_real_live_receipt_bundle_runner=True,
        operator_statement=operator_statement,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )

    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_real_live_receipt_bundle_production_runner_packet_ready"
    )
    assert result["runner_execution_allowed"] is True
    assert result["runner_execution_performed"] is True
    assert result["runner_result_valid"] is True
    assert result["capture_boundary_ready"] is True
    assert result["receipt_bundle_valid"] is True
    assert result["source_receipts_ready"] is True
    assert result["governed_live_completion_evidence_packet_ready"] is True
    assert result["download_performed_by_runner"] is True
    assert result["installer_launch_performed_by_runner"] is True
    assert result["primary_replacement_performed_by_runner"] is True
    assert result["primary_relaunch_performed_by_runner"] is True
    assert result["startup_prompt_verified_by_runner"] is True
    assert result["download_performed_by_this_proof"] is True
    assert result["installer_launch_performed_by_this_proof"] is True
    assert result["primary_replacement_performed_by_this_proof"] is True
    assert result["source_write_performed_by_this_proof"] is False
    assert result["github_mutation_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert (
        result["real_live_receipt_capture_boundary"][
            "governed_live_completion_evidence_packet_ready"
        ]
        is True
    )


def test_launcher_update_real_live_receipt_bundle_production_runner_rejects_secret_like_runner_output(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_real_live_receipt_bundle_production_runner,
        required_update_real_live_receipt_bundle_production_runner_operator_statement,
    )

    timestamp = "2026-05-25T00:00:00Z"

    def runner(context):
        return {
            "ok": True,
            "live_receipt_bundle": _fixture_real_live_receipt_bundle(
                context["vault_root"],
                context["generated_at_utc"],
            ),
            "private_key": "not-allowed",
        }

    preview = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=runner,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )
    operator_statement = (
        required_update_real_live_receipt_bundle_production_runner_operator_statement(
            preview["runner_plan"]
        )
    )

    result = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=runner,
        operator_approved_real_live_receipt_bundle_runner=True,
        operator_statement=operator_statement,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )

    assert result["ok"] is False
    assert result["status"] == (
        "launcher_update_real_live_receipt_bundle_production_runner_capture_blocked"
    )
    assert result["runner_execution_performed"] is True
    assert result["runner_result_valid"] is False
    assert result["capture_boundary_ready"] is False
    assert result["governed_live_completion_evidence_packet_ready"] is False
    assert "private_key" in result["runner_result_forbidden_key_paths"]
    assert (
        "real_live_receipt_bundle_runner_secret_like_keys_rejected"
        in result["errors"]
    )
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False


def test_launcher_update_production_runner_final_closeout_bridge_blocks_default_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_production_runner_final_closeout_bridge,
    )

    result = build_launcher_update_production_runner_final_closeout_bridge(
        tmp_path,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_production_runner_final_closeout_bridge"
    )
    assert result["status"] == (
        "launcher_update_production_runner_final_closeout_bridge_blocked"
    )
    assert result["runner_proof_ready"] is False
    assert result["primary_closeout_ready"] is False
    assert result["final_production_auto_update_closeout_audit_ready"] is False
    assert result["runner_execution_previously_performed"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert (
        "real_live_receipt_bundle_production_runner_proof_required"
        in result["errors"]
    )
    assert (
        "production_primary_closeout_after_source_recovery_proof_required"
        in result["errors"]
    )


def test_launcher_update_production_runner_final_closeout_bridge_feeds_final_audit(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_production_runner_final_closeout_bridge,
        build_launcher_update_real_live_receipt_bundle_production_runner,
        required_update_real_live_receipt_bundle_production_runner_operator_statement,
    )

    primary_closeout, timestamp = (
        _fixture_production_primary_closeout_after_source_recovery_ready(tmp_path)
    )
    runner = _fixture_real_live_receipt_bundle_production_runner()
    preview = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=runner,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )
    operator_statement = (
        required_update_real_live_receipt_bundle_production_runner_operator_statement(
            preview["runner_plan"]
        )
    )
    runner_result = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=runner,
        operator_approved_real_live_receipt_bundle_runner=True,
        operator_statement=operator_statement,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )

    result = build_launcher_update_production_runner_final_closeout_bridge(
        tmp_path,
        real_live_receipt_bundle_production_runner_proof=runner_result,
        production_primary_closeout_after_source_recovery_proof=primary_closeout,
        generated_at=timestamp,
    )

    assert runner_result["ok"] is True
    assert result["ok"] is True
    assert result["status"] == (
        "launcher_update_production_runner_final_closeout_bridge_verified_complete"
    )
    assert result["runner_proof_ready"] is True
    assert result["primary_closeout_ready"] is True
    assert result["final_production_auto_update_closeout_audit_ready"] is True
    assert result["production_auto_update_complete"] is True
    assert result["runner_execution_previously_performed"] is True
    assert result["download_previously_verified_by_runner"] is True
    assert result["installer_launch_previously_verified_by_runner"] is True
    assert result["primary_replacement_previously_verified_by_runner"] is True
    assert result["primary_relaunch_previously_verified_by_runner"] is True
    assert result["startup_prompt_previously_verified_by_runner"] is True
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["source_write_performed_by_this_proof"] is False
    assert result["github_mutation_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert (
        result["final_production_auto_update_closeout_audit"][
            "production_auto_update_complete"
        ]
        is True
    )


def test_launcher_update_production_runner_final_closeout_bridge_rejects_runner_digest_mismatch(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_production_runner_final_closeout_bridge,
        build_launcher_update_real_live_receipt_bundle_production_runner,
        required_update_real_live_receipt_bundle_production_runner_operator_statement,
    )

    primary_closeout, timestamp = (
        _fixture_production_primary_closeout_after_source_recovery_ready(tmp_path)
    )
    runner = _fixture_real_live_receipt_bundle_production_runner()
    preview = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=runner,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )
    operator_statement = (
        required_update_real_live_receipt_bundle_production_runner_operator_statement(
            preview["runner_plan"]
        )
    )
    runner_result = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=runner,
        operator_approved_real_live_receipt_bundle_runner=True,
        operator_statement=operator_statement,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )
    tampered_runner = dict(runner_result)
    tampered_runner["real_live_receipt_bundle_production_runner_digest_sha256"] = (
        "0" * 64
    )

    result = build_launcher_update_production_runner_final_closeout_bridge(
        tmp_path,
        real_live_receipt_bundle_production_runner_proof=tampered_runner,
        production_primary_closeout_after_source_recovery_proof=primary_closeout,
        generated_at=timestamp,
    )

    assert result["ok"] is False
    assert result["runner_proof_digest_matched"] is False
    assert result["runner_proof_ready"] is False
    assert result["primary_closeout_ready"] is True
    assert result["final_production_auto_update_closeout_audit_ready"] is False
    assert result["production_auto_update_complete"] is False
    assert (
        "real_live_receipt_bundle_production_runner_digest_mismatch"
        in result["errors"]
    )
    assert result["settings_install_control_exposed"] is False


def test_launcher_update_approved_production_runner_real_evidence_capture_blocks_default_execution(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_approved_production_runner_real_evidence_capture,
    )

    result = build_launcher_update_approved_production_runner_real_evidence_capture(
        tmp_path,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["surface"] == (
        "studio_launcher_update_approved_production_runner_real_evidence_capture"
    )
    assert result["status"] == (
        "launcher_update_approved_production_runner_real_evidence_capture_blocked"
    )
    assert result["evidence_file_read_performed"] is False
    assert result["runner_evidence_file_read"] is False
    assert result["primary_closeout_evidence_file_read"] is False
    assert result["production_runner_final_closeout_bridge_ready"] is False
    assert result["runner_execution_performed_by_this_proof"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert (
        "approved_production_runner_real_evidence_root_required"
        in result["errors"]
    )
    assert (
        "approved_production_runner_evidence_file_read_flag_required"
        in result["errors"]
    )
    assert "operator_real_evidence_capture_approval_required" in result["errors"]


def test_launcher_update_approved_production_runner_real_evidence_capture_reads_approved_fixture_files(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_approved_production_runner_real_evidence_capture,
        build_launcher_update_real_live_receipt_bundle_production_runner,
        required_update_approved_production_runner_real_evidence_capture_operator_statement,
        required_update_real_live_receipt_bundle_production_runner_operator_statement,
    )

    primary_closeout, timestamp = (
        _fixture_production_primary_closeout_after_source_recovery_ready(tmp_path)
    )
    runner = _fixture_real_live_receipt_bundle_production_runner()
    runner_preview = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=runner,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )
    runner_statement = (
        required_update_real_live_receipt_bundle_production_runner_operator_statement(
            runner_preview["runner_plan"]
        )
    )
    runner_result = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=runner,
        operator_approved_real_live_receipt_bundle_runner=True,
        operator_statement=runner_statement,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )
    evidence_root = tmp_path / ".chaseos" / "updates" / "real-evidence"
    evidence_root.mkdir(parents=True)
    (evidence_root / "real-live-receipt-bundle-production-runner.json").write_text(
        _json.dumps(runner_result, sort_keys=True),
        encoding="utf-8",
    )
    (
        evidence_root / "production-primary-closeout-after-source-recovery.json"
    ).write_text(
        _json.dumps(primary_closeout, sort_keys=True),
        encoding="utf-8",
    )
    preview = build_launcher_update_approved_production_runner_real_evidence_capture(
        tmp_path,
        evidence_root=evidence_root,
        allow_evidence_file_read=True,
        generated_at=timestamp,
    )
    operator_statement = (
        required_update_approved_production_runner_real_evidence_capture_operator_statement(
            preview["capture_plan"]
        )
    )

    result = build_launcher_update_approved_production_runner_real_evidence_capture(
        tmp_path,
        evidence_root=evidence_root,
        operator_approved_real_evidence_capture=True,
        operator_statement=operator_statement,
        allow_evidence_file_read=True,
        generated_at=timestamp,
    )

    assert result["ok"] is True, result["errors"]
    assert result["status"] == (
        "launcher_update_approved_production_runner_real_evidence_capture_verified_complete"
    )
    assert result["evidence_file_read_performed"] is True
    assert result["runner_evidence_file_read"] is True
    assert result["primary_closeout_evidence_file_read"] is True
    assert result["production_runner_final_closeout_bridge_ready"] is True
    assert result["final_production_auto_update_closeout_audit_ready"] is True
    assert result["runner_execution_performed_by_this_proof"] is False
    assert result["runner_execution_previously_performed"] is True
    assert result["download_previously_verified_by_runner"] is True
    assert result["installer_launch_previously_verified_by_runner"] is True
    assert result["primary_replacement_previously_verified_by_runner"] is True
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is True


def test_launcher_update_approved_production_runner_real_evidence_capture_blocks_outside_root(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_approved_production_runner_real_evidence_capture,
        required_update_approved_production_runner_real_evidence_capture_operator_statement,
    )

    outside_root = tmp_path.parent / f"{tmp_path.name}-outside"
    outside_root.mkdir()
    preview = build_launcher_update_approved_production_runner_real_evidence_capture(
        tmp_path,
        evidence_root=outside_root,
        allow_evidence_file_read=True,
        generated_at="2026-05-25T00:00:00Z",
    )
    operator_statement = (
        required_update_approved_production_runner_real_evidence_capture_operator_statement(
            preview["capture_plan"]
        )
    )

    result = build_launcher_update_approved_production_runner_real_evidence_capture(
        tmp_path,
        evidence_root=outside_root,
        operator_approved_real_evidence_capture=True,
        operator_statement=operator_statement,
        allow_evidence_file_read=True,
        generated_at="2026-05-25T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["evidence_root_inside_vault"] is False
    assert result["evidence_file_read_performed"] is False
    assert result["production_runner_final_closeout_bridge_ready"] is False
    assert (
        "approved_production_runner_real_evidence_root_outside_vault"
        in result["errors"]
    )
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False


def test_launcher_update_approved_production_runner_real_evidence_capture_rejects_tampered_runner_digest(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_approved_production_runner_real_evidence_capture,
        build_launcher_update_real_live_receipt_bundle_production_runner,
        required_update_approved_production_runner_real_evidence_capture_operator_statement,
        required_update_real_live_receipt_bundle_production_runner_operator_statement,
    )

    primary_closeout, timestamp = (
        _fixture_production_primary_closeout_after_source_recovery_ready(tmp_path)
    )
    runner = _fixture_real_live_receipt_bundle_production_runner()
    runner_preview = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=runner,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )
    runner_statement = (
        required_update_real_live_receipt_bundle_production_runner_operator_statement(
            runner_preview["runner_plan"]
        )
    )
    runner_result = build_launcher_update_real_live_receipt_bundle_production_runner(
        tmp_path,
        receipt_bundle_runner=runner,
        operator_approved_real_live_receipt_bundle_runner=True,
        operator_statement=runner_statement,
        allow_live_release_readback=True,
        allow_live_download=True,
        allow_staged_signature_verification=True,
        allow_installer_signed_output_verification=True,
        allow_installer_launch=True,
        allow_primary_replacement=True,
        allow_startup_prompt_verification=True,
        generated_at=timestamp,
    )
    tampered_runner = dict(runner_result)
    tampered_runner["real_live_receipt_bundle_production_runner_digest_sha256"] = (
        "0" * 64
    )
    evidence_root = tmp_path / "approved-real-evidence"
    evidence_root.mkdir()
    (evidence_root / "real-live-receipt-bundle-production-runner.json").write_text(
        _json.dumps(tampered_runner, sort_keys=True),
        encoding="utf-8",
    )
    (
        evidence_root / "production-primary-closeout-after-source-recovery.json"
    ).write_text(
        _json.dumps(primary_closeout, sort_keys=True),
        encoding="utf-8",
    )
    preview = build_launcher_update_approved_production_runner_real_evidence_capture(
        tmp_path,
        evidence_root=evidence_root,
        allow_evidence_file_read=True,
        generated_at=timestamp,
    )
    operator_statement = (
        required_update_approved_production_runner_real_evidence_capture_operator_statement(
            preview["capture_plan"]
        )
    )

    result = build_launcher_update_approved_production_runner_real_evidence_capture(
        tmp_path,
        evidence_root=evidence_root,
        operator_approved_real_evidence_capture=True,
        operator_statement=operator_statement,
        allow_evidence_file_read=True,
        generated_at=timestamp,
    )

    assert result["ok"] is False
    assert result["status"] == (
        "launcher_update_approved_production_runner_real_evidence_capture_bridge_blocked"
    )
    assert result["evidence_file_read_performed"] is True
    assert result["production_runner_final_closeout_bridge_ready"] is False
    assert result["production_auto_update_complete"] is False
    assert (
        "final_closeout_bridge:real_live_receipt_bundle_production_runner_digest_mismatch"
        in result["errors"]
    )
    assert result["settings_install_control_exposed"] is False


def _write_installer_real_artifact_build_output_capture_fixture(root):
    installer = root / "dist" / "studio" / "ChaseOS-Installer.exe"
    studio = root / "dist" / "studio" / "ChaseOS-Studio.exe"
    build_script = root / "runtime" / "studio" / "shell" / "build_installer.ps1"
    installer.parent.mkdir(parents=True)
    build_script.parent.mkdir(parents=True)
    installer_bytes = b"chaseos installer artifact"
    studio_bytes = b"chaseos studio artifact"
    installer.write_bytes(installer_bytes)
    studio.write_bytes(studio_bytes)
    build_script.write_text(
        "\n".join(
            [
                '$InstallerDistPath = Join-Path $ResolvedVaultRoot "build\\studio-installer-dist"',
                '$InstallerBuildOutput = Join-Path $InstallerDistPath "ChaseOS-Installer.exe"',
                '$ExpectedOutput = Join-Path $DistPath "ChaseOS-Installer.exe"',
                '$StudioPath = Join-Path $DistPath "ChaseOS-Studio.exe"',
                "$StudioHashBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $StudioPath).Hash",
                "pyinstaller $SpecFile --distpath $InstallerDistPath --workpath $WorkPath --noconfirm",
                "Copy-Item -LiteralPath $InstallerBuildOutput -Destination $ExpectedOutput -Force",
                "$StudioHashAfter = (Get-FileHash -Algorithm SHA256 -LiteralPath $StudioPath).Hash",
            ]
        ),
        encoding="utf-8",
    )
    return installer, studio, build_script, installer_bytes, studio_bytes


def test_launcher_update_installer_real_artifact_build_output_capture_reads_real_artifact_metadata(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_installer_real_artifact_build_output_capture,
    )

    installer, studio, build_script, installer_bytes, studio_bytes = (
        _write_installer_real_artifact_build_output_capture_fixture(tmp_path)
    )

    result = build_launcher_update_installer_real_artifact_build_output_capture(
        tmp_path,
        generated_at="2026-05-26T00:00:00Z",
    )

    assert result["ok"] is True, result["errors"]
    assert result["surface"] == (
        "studio_launcher_update_installer_real_artifact_build_output_capture"
    )
    assert result["status"] == (
        "launcher_update_installer_real_artifact_build_output_capture_"
        "captured_unsigned"
    )
    assert result["installer_path"] == str(installer.resolve())
    assert result["studio_path"] == str(studio.resolve())
    assert result["build_script_path"] == str(build_script.resolve())
    assert result["installer_artifact_present"] is True
    assert result["studio_artifact_present"] is True
    assert result["build_script_present"] is True
    assert result["installer_artifact_exact_name"] is True
    assert result["installer_artifact_size_bytes"] == len(installer_bytes)
    assert result["installer_artifact_sha256"] == _hashlib.sha256(
        installer_bytes
    ).hexdigest()
    assert result["studio_artifact_sha256"] == _hashlib.sha256(
        studio_bytes
    ).hexdigest()
    assert result["build_script_hardening_ready"] is True
    assert result["build_script_studio_hash_guard_ready"] is True
    assert result["build_script_isolated_installer_dist_ready"] is True
    assert result["build_script_copies_only_installer_output"] is True
    assert result["signature_probe_performed"] is False
    assert result["signing_required"] is True
    assert result["installer_signed_output_verified"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False


def test_launcher_update_installer_real_artifact_build_output_capture_blocks_missing_artifact(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_installer_real_artifact_build_output_capture,
    )

    result = build_launcher_update_installer_real_artifact_build_output_capture(
        tmp_path,
        generated_at="2026-05-26T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["status"] == (
        "launcher_update_installer_real_artifact_build_output_capture_blocked"
    )
    assert result["installer_artifact_present"] is False
    assert result["build_script_hardening_ready"] is False
    assert "installer_artifact_missing" in result["errors"]
    assert "build_script_missing" in result["errors"]
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False


def test_launcher_update_installer_real_artifact_build_output_capture_accepts_valid_signature_probe(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_installer_real_artifact_build_output_capture,
    )

    _write_installer_real_artifact_build_output_capture_fixture(tmp_path)

    result = build_launcher_update_installer_real_artifact_build_output_capture(
        tmp_path,
        signature_probe=lambda path: {"status": "Valid", "verified": True},
        generated_at="2026-05-26T00:00:00Z",
    )

    assert result["ok"] is True, result["errors"]
    assert result["status"] == (
        "launcher_update_installer_real_artifact_build_output_capture_"
        "signed_output_verified"
    )
    assert result["signature_probe_performed"] is True
    assert result["installer_signed_output_verified"] is True
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["production_auto_update_complete"] is False


def test_launcher_update_installer_real_artifact_build_output_capture_rejects_secret_like_signature_probe(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_installer_real_artifact_build_output_capture,
    )

    _write_installer_real_artifact_build_output_capture_fixture(tmp_path)

    result = build_launcher_update_installer_real_artifact_build_output_capture(
        tmp_path,
        signature_probe=lambda path: {
            "status": "Valid",
            "verified": True,
            "private_key": "not-allowed",
        },
        generated_at="2026-05-26T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["status"] == (
        "launcher_update_installer_real_artifact_build_output_capture_blocked"
    )
    assert result["signature_probe_performed"] is True
    assert result["installer_signed_output_verified"] is False
    assert "private_key" in result["signature_probe_forbidden_key_paths"]
    assert "signature_probe_secret_like_keys_rejected" in result["errors"]
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False


def _write_dist_artifact_isolation_cohabitation_fixture(root):
    studio = root / "dist" / "studio" / "ChaseOS-Studio.exe"
    installer = root / "dist" / "studio" / "ChaseOS-Installer.exe"
    studio_script = root / "runtime" / "studio" / "shell" / "build_exe.ps1"
    installer_script = root / "runtime" / "studio" / "shell" / "build_installer.ps1"
    studio.parent.mkdir(parents=True)
    studio_script.parent.mkdir(parents=True)
    studio_bytes = b"studio final artifact"
    installer_bytes = b"installer final artifact"
    studio.write_bytes(studio_bytes)
    installer.write_bytes(installer_bytes)
    studio_script.write_text(
        "\n".join(
            [
                '$StudioDistPath = "build\\studio-dist"',
                '$StudioBuildOutput = Join-Path $VaultRoot (Join-Path $StudioDistPath "ChaseOS-Studio.exe")',
                '$ExpectedOutput = Join-Path $FinalDistPath "ChaseOS-Studio.exe"',
                '$InstallerPath = Join-Path $FinalDistPath "ChaseOS-Installer.exe"',
                "$InstallerHashBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $InstallerPath).Hash",
                '$piArgs = @($SpecFile, "--distpath", $StudioDistPath)',
                "Copy-Item -LiteralPath $StudioBuildOutput -Destination $ExpectedOutput -Force",
                "$InstallerHashAfter = (Get-FileHash -Algorithm SHA256 -LiteralPath $InstallerPath).Hash",
            ]
        ),
        encoding="utf-8",
    )
    installer_script.write_text(
        "\n".join(
            [
                '$InstallerDistPath = Join-Path $ResolvedVaultRoot "build\\studio-installer-dist"',
                '$InstallerBuildOutput = Join-Path $InstallerDistPath "ChaseOS-Installer.exe"',
                '$ExpectedOutput = Join-Path $DistPath "ChaseOS-Installer.exe"',
                '$StudioPath = Join-Path $DistPath "ChaseOS-Studio.exe"',
                "$StudioHashBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $StudioPath).Hash",
                "pyinstaller $SpecFile --distpath $InstallerDistPath --workpath $WorkPath --noconfirm",
                "Copy-Item -LiteralPath $InstallerBuildOutput -Destination $ExpectedOutput -Force",
                "$StudioHashAfter = (Get-FileHash -Algorithm SHA256 -LiteralPath $StudioPath).Hash",
            ]
        ),
        encoding="utf-8",
    )
    return studio, installer, studio_bytes, installer_bytes


def test_launcher_update_dist_artifact_isolation_cohabitation_proof_verifies_both_artifacts(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_dist_artifact_isolation_cohabitation_proof,
    )

    studio, installer, studio_bytes, installer_bytes = (
        _write_dist_artifact_isolation_cohabitation_fixture(tmp_path)
    )

    result = build_launcher_update_dist_artifact_isolation_cohabitation_proof(
        tmp_path,
        generated_at="2026-05-26T00:00:00Z",
    )

    assert result["ok"] is True, result["errors"]
    assert result["surface"] == (
        "studio_launcher_update_dist_artifact_isolation_cohabitation_proof"
    )
    assert result["status"] == (
        "launcher_update_dist_artifact_isolation_cohabitation_verified_unsigned"
    )
    assert result["both_artifacts_present"] is True
    assert result["studio_artifact_present"] is True
    assert result["installer_artifact_present"] is True
    assert result["studio_artifact_sha256"] == _hashlib.sha256(
        studio_bytes
    ).hexdigest()
    assert result["installer_artifact_sha256"] == _hashlib.sha256(
        installer_bytes
    ).hexdigest()
    assert result["studio_build_script_isolated_dist_ready"] is True
    assert result["installer_build_script_isolated_dist_ready"] is True
    assert result["cross_artifact_hash_guards_ready"] is True
    assert result["cohabitation_ready"] is True
    assert result["signing_required"] is True
    assert result["signed_output_verified"] is False
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False
    assert result["studio_artifact_descriptor"]["path"] == str(studio.resolve())
    assert result["installer_artifact_descriptor"]["path"] == str(installer.resolve())


def test_launcher_update_dist_artifact_isolation_cohabitation_proof_blocks_missing_studio(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_dist_artifact_isolation_cohabitation_proof,
    )

    _write_dist_artifact_isolation_cohabitation_fixture(tmp_path)
    (tmp_path / "dist" / "studio" / "ChaseOS-Studio.exe").unlink()

    result = build_launcher_update_dist_artifact_isolation_cohabitation_proof(
        tmp_path,
        generated_at="2026-05-26T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["status"] == (
        "launcher_update_dist_artifact_isolation_cohabitation_blocked"
    )
    assert result["studio_artifact_present"] is False
    assert result["installer_artifact_present"] is True
    assert "studio_artifact_missing" in result["errors"]
    assert result["cohabitation_ready"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False


def test_launcher_update_dist_artifact_isolation_cohabitation_proof_blocks_unhardened_studio_script(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_dist_artifact_isolation_cohabitation_proof,
    )

    _write_dist_artifact_isolation_cohabitation_fixture(tmp_path)
    (tmp_path / "runtime" / "studio" / "shell" / "build_exe.ps1").write_text(
        "pyinstaller runtime\\studio\\shell\\ChaseOS-Studio.spec --distpath dist\\studio",
        encoding="utf-8",
    )

    result = build_launcher_update_dist_artifact_isolation_cohabitation_proof(
        tmp_path,
        generated_at="2026-05-26T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["studio_build_script_isolated_dist_ready"] is False
    assert "build_exe.ps1:missing_required_tokens" in result["errors"]
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False


def test_launcher_update_signed_artifact_verification_closeout_blocks_without_signature_probe(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_signed_artifact_verification_closeout,
    )

    _write_dist_artifact_isolation_cohabitation_fixture(tmp_path)

    result = build_launcher_update_signed_artifact_verification_closeout(
        tmp_path,
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["surface"] == (
        "studio_launcher_update_signed_artifact_verification_closeout"
    )
    assert result["status"] == (
        "launcher_update_signed_artifact_verification_closeout_"
        "signature_probe_required"
    )
    assert result["cohabitation_ready"] is True
    assert result["signature_probe_performed"] is False
    assert result["studio_signed_output_verified"] is False
    assert result["installer_signed_output_verified"] is False
    assert result["signed_artifacts_verified"] is False
    assert "studio_signature_probe_required" in result["errors"]
    assert "installer_signature_probe_required" in result["errors"]
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["settings_install_control_exposed"] is False
    assert result["production_auto_update_complete"] is False


def test_launcher_update_signed_artifact_verification_closeout_verifies_signed_artifacts(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_signed_artifact_verification_closeout,
    )

    _write_dist_artifact_isolation_cohabitation_fixture(tmp_path)

    result = build_launcher_update_signed_artifact_verification_closeout(
        tmp_path,
        signature_probe=lambda path: {
            "status": "Valid",
            "verified": True,
            "signer_subject": "CN=ChaseOS Release",
            "certificate_thumbprint": "AA BB CC",
        },
        expected_signer_subject="ChaseOS Release",
        expected_certificate_thumbprint="AABBCC",
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is True, result["errors"]
    assert result["status"] == (
        "launcher_update_signed_artifact_verification_closeout_verified"
    )
    assert result["cohabitation_ready"] is True
    assert result["signature_probe_performed"] is True
    assert result["studio_signed_output_verified"] is True
    assert result["installer_signed_output_verified"] is True
    assert result["signed_artifacts_verified"] is True
    assert result["studio_signature"]["expected_signer_subject_matched"] is True
    assert (
        result["installer_signature"]["expected_certificate_thumbprint_matched"]
        is True
    )
    assert result["download_performed_by_this_proof"] is False
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False
    assert result["production_auto_update_complete"] is False


def test_launcher_update_signed_artifact_verification_closeout_blocks_unsigned_artifacts(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_signed_artifact_verification_closeout,
    )

    _write_dist_artifact_isolation_cohabitation_fixture(tmp_path)

    result = build_launcher_update_signed_artifact_verification_closeout(
        tmp_path,
        signature_probe=lambda path: {"status": "NotSigned", "verified": False},
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["status"] == (
        "launcher_update_signed_artifact_verification_closeout_signatures_blocked"
    )
    assert result["signature_probe_performed"] is True
    assert result["studio_signed_output_verified"] is False
    assert result["installer_signed_output_verified"] is False
    assert "studio_signature_not_valid" in result["errors"]
    assert "installer_signature_not_valid" in result["errors"]
    assert result["installer_launch_performed_by_this_proof"] is False
    assert result["primary_replacement_performed_by_this_proof"] is False


def test_launcher_update_signed_artifact_verification_closeout_rejects_secret_like_probe(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_signed_artifact_verification_closeout,
    )

    _write_dist_artifact_isolation_cohabitation_fixture(tmp_path)

    result = build_launcher_update_signed_artifact_verification_closeout(
        tmp_path,
        signature_probe=lambda path: {
            "status": "Valid",
            "verified": True,
            "private_key": "not-allowed",
        },
        generated_at="2026-05-27T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["studio_signed_output_verified"] is False
    assert result["installer_signed_output_verified"] is False
    assert "studio_signature_probe_secret_like_keys_rejected" in result["errors"]
    assert "installer_signature_probe_secret_like_keys_rejected" in result["errors"]
    assert "private_key" in result["studio_signature"][
        "signature_probe_forbidden_key_paths"
    ]
    assert result["studio_signature"]["signature_probe_result"] == {}


def test_launcher_update_authoritative_candidate_supply_verification_after_import_blocks_default_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_authoritative_candidate_supply_verification_after_import_proof,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = (
        build_launcher_update_authoritative_candidate_supply_verification_after_import_proof(
            vault_root
        )
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_authoritative_candidate_supply_verification_after_import_proof"
    )
    assert result["status"] == (
        "launcher_update_authoritative_candidate_supply_verification_after_import_blocked"
    )
    assert result["import_boundary_verified"] is False
    assert result["candidate_supply_packet_ready"] is False
    assert result["candidate_verification_ready"] is False
    assert result["ready_for_wrapper_removal_executor"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert (
        "authoritative_source_candidate_import_boundary_proof_required"
        in result["errors"]
    )


def test_launcher_update_authoritative_candidate_supply_verification_after_import_readies_wrapper_removal_chain(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_authoritative_candidate_supply_verification_after_import_proof,
        build_launcher_update_authoritative_source_candidate_import_boundary_proof,
        required_update_authoritative_source_candidate_import_operator_statement,
        required_update_authoritative_normal_source_candidate_supply_operator_statement,
        required_update_normal_source_candidate_verification_operator_statement,
    )

    incoming_root = tmp_path / "incoming-authoritative-source"
    launcher_candidate = incoming_root / "launcher_update_check.py"
    api_candidate = incoming_root / "api.py"
    shell_test_candidate = incoming_root / "test_pass10a_shell.py"
    launcher_candidate.parent.mkdir(parents=True, exist_ok=True)
    launcher_candidate.write_text(
        "def build_supply_verification_ready():\n    return True\n",
        encoding="utf-8",
    )
    api_candidate.write_text(
        "class StudioAPI:\n"
        "    def get_supply_verification_ready(self):\n"
        "        return True\n",
        encoding="utf-8",
    )
    shell_test_candidate.write_text(
        "class TestSupplyVerificationReady:\n"
        "    def test_supply_verification_ready(self):\n"
        "        assert True\n",
        encoding="utf-8",
    )
    import_candidate_paths = {
        "launcher_update_check": [launcher_candidate],
        "studio_shell_api": [api_candidate],
        "studio_shell_test_pass10a": [shell_test_candidate],
    }
    required_symbols = {
        "launcher_update_check": ["build_supply_verification_ready"],
        "studio_shell_api": [
            "class StudioAPI",
            "get_supply_verification_ready",
        ],
        "studio_shell_test_pass10a": [
            "TestSupplyVerificationReady",
            "test_supply_verification_ready",
        ],
    }
    generated_at = "2026-05-25T00:00:00Z"

    import_preview = build_launcher_update_authoritative_source_candidate_import_boundary_proof(
        tmp_path,
        import_candidate_paths=import_candidate_paths,
        required_symbols_by_role=required_symbols,
        generated_at=generated_at,
    )
    import_statement = required_update_authoritative_source_candidate_import_operator_statement(
        import_preview["candidate_import_plan"]
    )
    import_proof = build_launcher_update_authoritative_source_candidate_import_boundary_proof(
        tmp_path,
        import_candidate_paths=import_candidate_paths,
        required_symbols_by_role=required_symbols,
        operator_approved_candidate_import=True,
        operator_statement=import_statement,
        allow_candidate_import_write=True,
        generated_at=generated_at,
    )

    supply_pending = build_launcher_update_authoritative_candidate_supply_verification_after_import_proof(
        tmp_path,
        source_candidate_import_boundary_proof=import_proof,
        required_symbols_by_role=required_symbols,
        generated_at=generated_at,
    )

    assert supply_pending["import_boundary_verified"] is True
    assert supply_pending["candidate_supply_packet_ready"] is False
    assert supply_pending["status"] == (
        "launcher_update_authoritative_candidate_supply_verification_after_import_"
        "pending_supply_approval"
    )

    supply_statement = (
        required_update_authoritative_normal_source_candidate_supply_operator_statement(
            supply_pending["candidate_supply_preview"]["candidate_supply_contract"]
        )
    )
    verification_pending = build_launcher_update_authoritative_candidate_supply_verification_after_import_proof(
        tmp_path,
        source_candidate_import_boundary_proof=import_proof,
        required_symbols_by_role=required_symbols,
        operator_approved_candidate_supply=True,
        candidate_supply_statement=supply_statement,
        generated_at=generated_at,
    )

    assert verification_pending["candidate_supply_packet_ready"] is True
    assert verification_pending["candidate_verification_ready"] is False
    assert verification_pending["status"] == (
        "launcher_update_authoritative_candidate_supply_verification_after_import_"
        "pending_candidate_verification_approval"
    )

    verification_statement = (
        required_update_normal_source_candidate_verification_operator_statement(
            verification_pending["candidate_verification_preview"]["candidate_set"]
        )
    )
    ready = build_launcher_update_authoritative_candidate_supply_verification_after_import_proof(
        tmp_path,
        source_candidate_import_boundary_proof=import_proof,
        required_symbols_by_role=required_symbols,
        operator_approved_candidate_supply=True,
        candidate_supply_statement=supply_statement,
        operator_approved_candidate_verification=True,
        candidate_verification_statement=verification_statement,
        generated_at=generated_at,
    )

    assert ready["ok"] is True
    assert ready["status"] == (
        "launcher_update_authoritative_candidate_supply_verification_after_import_"
        "ready_for_wrapper_removal_executor"
    )
    assert ready["candidate_supply_statement_matched"] is True
    assert ready["candidate_verification_statement_matched"] is True
    assert ready["candidate_supply_packet_ready"] is True
    assert ready["candidate_verification_ready"] is True
    assert ready["ready_for_wrapper_removal_executor"] is True
    assert ready["source_write_performed"] is False
    assert ready["wrapper_removal_performed"] is False
    assert ready["primary_exe_replacement_performed"] is False
    assert ready["settings_write_control_exposed"] is False
    assert all(ready["role_candidate_path_matches"].values())
    assert ready["readiness_bundle"]["source_write_allowed"] is False
    assert ready["readiness_bundle"]["wrapper_removal_allowed"] is False


def test_launcher_update_current_vault_wrapper_removal_after_import_execution_blocks_default_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_wrapper_removal_after_import_execution_proof,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = build_launcher_update_current_vault_wrapper_removal_after_import_execution_proof(
        vault_root
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_current_vault_wrapper_removal_after_import_execution_proof"
    )
    assert result["status"] == (
        "launcher_update_current_vault_wrapper_removal_after_import_execution_blocked"
    )
    assert result["after_import_ready_for_wrapper_removal_executor"] is False
    assert result["restore_plan_ready"] is False
    assert result["current_vault_source_write_enabled"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["current_vault_wrappers_removed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert (
        "authoritative_candidate_supply_verification_after_import_proof_required"
        in result["errors"]
    )


def test_launcher_update_current_vault_wrapper_removal_after_import_execution_restores_fixture_current_vault_after_exact_approval(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_authoritative_candidate_supply_verification_after_import_proof,
        build_launcher_update_authoritative_source_candidate_import_boundary_proof,
        build_launcher_update_current_vault_wrapper_removal_after_import_execution_proof,
        required_update_authoritative_normal_source_candidate_supply_operator_statement,
        required_update_authoritative_source_candidate_import_operator_statement,
        required_update_current_vault_wrapper_removal_after_import_operator_statement,
        required_update_normal_source_candidate_verification_operator_statement,
    )

    incoming_root = tmp_path / "incoming-authoritative-source"
    launcher_candidate = incoming_root / "launcher_update_check.py"
    api_candidate = incoming_root / "api.py"
    shell_test_candidate = incoming_root / "test_pass10a_shell.py"
    launcher_candidate.parent.mkdir(parents=True, exist_ok=True)
    launcher_candidate.write_text(
        "def build_after_import_wrapper_removal_ready():\n    return True\n",
        encoding="utf-8",
    )
    api_candidate.write_text(
        "class StudioAPI:\n"
        "    def get_after_import_wrapper_removal_ready(self):\n"
        "        return True\n",
        encoding="utf-8",
    )
    shell_test_candidate.write_text(
        "class TestAfterImportWrapperRemovalReady:\n"
        "    def test_after_import_wrapper_removal_ready(self):\n"
        "        assert True\n",
        encoding="utf-8",
    )
    target_launcher = tmp_path / "runtime" / "studio" / "launcher_update_check.py"
    target_api = tmp_path / "runtime" / "studio" / "shell" / "api.py"
    target_shell_test = (
        tmp_path / "runtime" / "studio" / "shell" / "test_pass10a_shell.py"
    )
    target_launcher.parent.mkdir(parents=True, exist_ok=True)
    target_api.parent.mkdir(parents=True, exist_ok=True)
    target_launcher.write_text(
        "_RECOVERED_BYTECODE_PATH = 'fixture'\n"
        "exec(_RECOVERED_BYTECODE_CODE, globals())\n",
        encoding="utf-8",
    )
    target_api.write_text(
        "_RECOVERED_BYTECODE_PATH = 'fixture'\n"
        "exec(_RECOVERED_BYTECODE_CODE, globals())\n",
        encoding="utf-8",
    )
    target_shell_test.write_text(
        "_RECOVERED_TEST_BYTECODE_PATH = 'fixture'\n"
        "exec(_RECOVERED_TEST_CODE, globals())\n",
        encoding="utf-8",
    )
    import_candidate_paths = {
        "launcher_update_check": [launcher_candidate],
        "studio_shell_api": [api_candidate],
        "studio_shell_test_pass10a": [shell_test_candidate],
    }
    required_symbols = {
        "launcher_update_check": ["build_after_import_wrapper_removal_ready"],
        "studio_shell_api": [
            "class StudioAPI",
            "get_after_import_wrapper_removal_ready",
        ],
        "studio_shell_test_pass10a": [
            "TestAfterImportWrapperRemovalReady",
            "test_after_import_wrapper_removal_ready",
        ],
    }
    generated_at = "2026-05-25T00:00:00Z"

    import_preview = build_launcher_update_authoritative_source_candidate_import_boundary_proof(
        tmp_path,
        import_candidate_paths=import_candidate_paths,
        required_symbols_by_role=required_symbols,
        generated_at=generated_at,
    )
    import_statement = required_update_authoritative_source_candidate_import_operator_statement(
        import_preview["candidate_import_plan"]
    )
    import_proof = build_launcher_update_authoritative_source_candidate_import_boundary_proof(
        tmp_path,
        import_candidate_paths=import_candidate_paths,
        required_symbols_by_role=required_symbols,
        operator_approved_candidate_import=True,
        operator_statement=import_statement,
        allow_candidate_import_write=True,
        generated_at=generated_at,
    )
    supply_pending = build_launcher_update_authoritative_candidate_supply_verification_after_import_proof(
        tmp_path,
        source_candidate_import_boundary_proof=import_proof,
        required_symbols_by_role=required_symbols,
        generated_at=generated_at,
    )
    supply_statement = (
        required_update_authoritative_normal_source_candidate_supply_operator_statement(
            supply_pending["candidate_supply_preview"]["candidate_supply_contract"]
        )
    )
    verification_pending = build_launcher_update_authoritative_candidate_supply_verification_after_import_proof(
        tmp_path,
        source_candidate_import_boundary_proof=import_proof,
        required_symbols_by_role=required_symbols,
        operator_approved_candidate_supply=True,
        candidate_supply_statement=supply_statement,
        generated_at=generated_at,
    )
    verification_statement = (
        required_update_normal_source_candidate_verification_operator_statement(
            verification_pending["candidate_verification_preview"]["candidate_set"]
        )
    )
    after_import_ready = build_launcher_update_authoritative_candidate_supply_verification_after_import_proof(
        tmp_path,
        source_candidate_import_boundary_proof=import_proof,
        required_symbols_by_role=required_symbols,
        operator_approved_candidate_supply=True,
        candidate_supply_statement=supply_statement,
        operator_approved_candidate_verification=True,
        candidate_verification_statement=verification_statement,
        generated_at=generated_at,
    )

    preview = build_launcher_update_current_vault_wrapper_removal_after_import_execution_proof(
        tmp_path,
        authoritative_candidate_supply_verification_after_import_proof=after_import_ready,
        required_symbols_by_role=required_symbols,
        generated_at=generated_at,
    )

    assert preview["after_import_ready_for_wrapper_removal_executor"] is True
    assert preview["restore_plan_ready"] is True
    assert preview["operator_statement_matched"] is False
    assert preview["status"] == (
        "launcher_update_current_vault_wrapper_removal_after_import_execution_"
        "pending_approval"
    )

    removal_statement = (
        required_update_current_vault_wrapper_removal_after_import_operator_statement(
            preview["wrapper_removal_after_import_execution_plan"]
        )
    )
    blocked_write_flag = build_launcher_update_current_vault_wrapper_removal_after_import_execution_proof(
        tmp_path,
        authoritative_candidate_supply_verification_after_import_proof=after_import_ready,
        required_symbols_by_role=required_symbols,
        operator_approved_current_vault_wrapper_removal_after_import=True,
        operator_statement=removal_statement,
        generated_at=generated_at,
    )

    assert blocked_write_flag["status"] == (
        "launcher_update_current_vault_wrapper_removal_after_import_execution_"
        "write_flag_required"
    )
    assert blocked_write_flag["source_write_performed"] is False

    restored = build_launcher_update_current_vault_wrapper_removal_after_import_execution_proof(
        tmp_path,
        authoritative_candidate_supply_verification_after_import_proof=after_import_ready,
        required_symbols_by_role=required_symbols,
        allow_current_vault_source_write=True,
        operator_approved_current_vault_wrapper_removal_after_import=True,
        operator_statement=removal_statement,
        generated_at=generated_at,
    )

    assert restored["ok"] is True
    assert restored["status"] == (
        "launcher_update_current_vault_wrapper_removal_after_import_execution_restored"
    )
    assert restored["source_write_performed"] is True
    assert restored["wrapper_removal_performed"] is True
    assert restored["current_vault_wrappers_removed"] is True
    assert restored["primary_exe_replacement_performed"] is False
    assert restored["settings_write_control_exposed"] is False
    assert target_launcher.read_text(encoding="utf-8") == launcher_candidate.read_text(
        encoding="utf-8"
    )
    assert target_api.read_text(encoding="utf-8") == api_candidate.read_text(
        encoding="utf-8"
    )
    assert target_shell_test.read_text(
        encoding="utf-8"
    ) == shell_test_candidate.read_text(encoding="utf-8")
    assert all(
        item["target_verification_passed"] and item["wrapper_free"]
        for item in restored["post_write_source_checks"].values()
    )


def test_launcher_update_current_vault_wrapper_removal_executor_boundary_blocks_default_execution():
    from runtime.studio.launcher_update_check import (
        build_launcher_update_current_vault_wrapper_removal_executor_boundary_proof,
    )

    vault_root = _Path(__file__).resolve().parents[2]
    result = build_launcher_update_current_vault_wrapper_removal_executor_boundary_proof(
        vault_root
    )

    assert result["ok"] is False
    assert (
        result["surface"]
        == "studio_launcher_update_current_vault_wrapper_removal_executor_boundary_proof"
    )
    assert (
        result["status"]
        == "launcher_update_current_vault_wrapper_removal_executor_blocked"
    )
    assert result["restore_plan_ready"] is False
    assert result["current_vault_source_write_enabled"] is False
    assert result["source_write_performed"] is False
    assert result["wrapper_removal_performed"] is False
    assert result["current_vault_wrappers_removed"] is False
    assert result["decompiler_execution_performed"] is False
    assert result["candidate_source_execution_performed"] is False
    assert result["primary_exe_replacement_performed"] is False
    assert result["settings_write_control_exposed"] is False
    assert "authoritative_candidate_supply_packet_not_ready" in result["errors"]
    assert "candidate_verification_proof_required" in result["errors"]
    assert (
        "operator_current_vault_wrapper_removal_approval_required"
        in result["errors"]
    )


def test_launcher_update_current_vault_wrapper_removal_executor_boundary_restores_fixture_current_vault_after_exact_approval(
    tmp_path,
):
    from runtime.studio.launcher_update_check import (
        build_launcher_update_authoritative_normal_source_candidate_supply_packet,
        build_launcher_update_current_vault_wrapper_removal_executor_boundary_proof,
        build_launcher_update_normal_source_candidate_verification_proof,
        required_update_authoritative_normal_source_candidate_supply_operator_statement,
        required_update_current_vault_wrapper_removal_operator_statement,
        required_update_normal_source_candidate_verification_operator_statement,
    )

    candidate_root = tmp_path / "candidates"
    launcher_candidate = candidate_root / "launcher_update_check.py"
    api_candidate = candidate_root / "api.py"
    shell_test_candidate = candidate_root / "test_pass10a_shell.py"
    launcher_candidate.parent.mkdir(parents=True, exist_ok=True)
    launcher_candidate.write_text(
        "def build_fixture_wrapper_removal_ready():\n    return True\n",
        encoding="utf-8",
    )
    api_candidate.write_text(
        "class StudioAPI:\n"
        "    def get_fixture_wrapper_removal_ready(self):\n"
        "        return True\n",
        encoding="utf-8",
    )
    shell_test_candidate.write_text(
        "class TestFixtureWrapperRemovalReady:\n"
        "    def test_fixture_wrapper_removal_ready(self):\n"
        "        assert True\n",
        encoding="utf-8",
    )
    target_launcher = tmp_path / "runtime" / "studio" / "launcher_update_check.py"
    target_api = tmp_path / "runtime" / "studio" / "shell" / "api.py"
    target_shell_test = (
        tmp_path / "runtime" / "studio" / "shell" / "test_pass10a_shell.py"
    )
    target_launcher.parent.mkdir(parents=True, exist_ok=True)
    target_api.parent.mkdir(parents=True, exist_ok=True)
    target_launcher.write_text(
        "_RECOVERED_BYTECODE_PATH = 'fixture'\n"
        "exec(_RECOVERED_BYTECODE_CODE, globals())\n",
        encoding="utf-8",
    )
    target_api.write_text(
        "_RECOVERED_BYTECODE_PATH = 'fixture'\n"
        "exec(_RECOVERED_BYTECODE_CODE, globals())\n",
        encoding="utf-8",
    )
    target_shell_test.write_text(
        "_RECOVERED_TEST_BYTECODE_PATH = 'fixture'\n"
        "exec(_RECOVERED_TEST_CODE, globals())\n",
        encoding="utf-8",
    )
    candidate_paths = {
        "launcher_update_check": [launcher_candidate],
        "studio_shell_api": [api_candidate],
        "studio_shell_test_pass10a": [shell_test_candidate],
    }
    required_symbols = {
        "launcher_update_check": ["build_fixture_wrapper_removal_ready"],
        "studio_shell_api": [
            "class StudioAPI",
            "get_fixture_wrapper_removal_ready",
        ],
        "studio_shell_test_pass10a": [
            "TestFixtureWrapperRemovalReady",
            "test_fixture_wrapper_removal_ready",
        ],
    }
    generated_at = "2026-05-25T00:00:00Z"
    supply_preview = build_launcher_update_authoritative_normal_source_candidate_supply_packet(
        tmp_path,
        candidate_paths=candidate_paths,
        required_symbols_by_role=required_symbols,
        generated_at=generated_at,
    )
    supply_statement = (
        required_update_authoritative_normal_source_candidate_supply_operator_statement(
            supply_preview["candidate_supply_contract"]
        )
    )
    supply_packet = build_launcher_update_authoritative_normal_source_candidate_supply_packet(
        tmp_path,
        candidate_paths=candidate_paths,
        required_symbols_by_role=required_symbols,
        operator_approved_candidate_supply=True,
        operator_statement=supply_statement,
        generated_at=generated_at,
    )
    verification_preview = build_launcher_update_normal_source_candidate_verification_proof(
        tmp_path,
        candidate_paths=candidate_paths,
        required_symbols_by_role=required_symbols,
        generated_at=generated_at,
    )
    verification_statement = (
        required_update_normal_source_candidate_verification_operator_statement(
            verification_preview["candidate_set"]
        )
    )
    verification = build_launcher_update_normal_source_candidate_verification_proof(
        tmp_path,
        candidate_paths=candidate_paths,
        required_symbols_by_role=required_symbols,
        operator_approved_candidate_verification=True,
        operator_statement=verification_statement,
        generated_at=generated_at,
    )
    preview = build_launcher_update_current_vault_wrapper_removal_executor_boundary_proof(
        tmp_path,
        authoritative_candidate_supply_packet=supply_packet,
        candidate_verification_proof=verification,
        required_symbols_by_role=required_symbols,
        generated_at=generated_at,
    )

    assert preview["restore_plan_ready"] is True
    assert preview["operator_statement_matched"] is False
    assert (
        preview["status"]
        == "launcher_update_current_vault_wrapper_removal_executor_pending_approval"
    )

    removal_statement = required_update_current_vault_wrapper_removal_operator_statement(
        preview["wrapper_removal_plan"]
    )
    blocked_write_flag = build_launcher_update_current_vault_wrapper_removal_executor_boundary_proof(
        tmp_path,
        authoritative_candidate_supply_packet=supply_packet,
        candidate_verification_proof=verification,
        required_symbols_by_role=required_symbols,
        operator_approved_current_vault_wrapper_removal=True,
        operator_statement=removal_statement,
        generated_at=generated_at,
    )

    assert blocked_write_flag["status"] == (
        "launcher_update_current_vault_wrapper_removal_executor_write_flag_required"
    )
    assert blocked_write_flag["source_write_performed"] is False

    restored = build_launcher_update_current_vault_wrapper_removal_executor_boundary_proof(
        tmp_path,
        authoritative_candidate_supply_packet=supply_packet,
        candidate_verification_proof=verification,
        required_symbols_by_role=required_symbols,
        allow_current_vault_source_write=True,
        operator_approved_current_vault_wrapper_removal=True,
        operator_statement=removal_statement,
        generated_at=generated_at,
    )

    assert restored["ok"] is True
    assert (
        restored["status"]
        == "launcher_update_current_vault_wrapper_removal_executor_restored"
    )
    assert restored["source_write_performed"] is True
    assert restored["wrapper_removal_performed"] is True
    assert restored["current_vault_wrappers_removed"] is True
    assert restored["primary_exe_replacement_performed"] is False
    assert target_launcher.read_text(encoding="utf-8") == launcher_candidate.read_text(
        encoding="utf-8"
    )
    assert target_api.read_text(encoding="utf-8") == api_candidate.read_text(
        encoding="utf-8"
    )
    assert target_shell_test.read_text(
        encoding="utf-8"
    ) == shell_test_candidate.read_text(encoding="utf-8")
    assert all(
        item["target_verification_passed"] and item["wrapper_free"]
        for item in restored["post_write_source_checks"].values()
    )
