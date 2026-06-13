"""Tests for chaseos operate browser excalidraw-* CLI commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from runtime.cli.main import (
    cmd_operate_browser_excalidraw_chain_readiness,
    cmd_operate_browser_excalidraw_live_readiness,
    cmd_operate_browser_excalidraw_readiness_from_response,
    cmd_operate_browser_excalidraw_setup_instructions,
    cmd_operate_browser_excalidraw_target_contract,
    cmd_operate_browser_excalidraw_target_response,
    cmd_operate_browser_excalidraw_mcp_execution_approval,
    cmd_operate_browser_excalidraw_mcp_proof_execution,
    cmd_operate_browser_excalidraw_public_drawing_approval,
    cmd_operate_browser_excalidraw_public_drawing_proof,
)
from runtime.browser_runtime.excalidraw_mcp_live_readiness import (
    EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_MISSING_TARGET,
    EXCALIDRAW_MCP_LIVE_READINESS_READY,
)
from runtime.browser_runtime.excalidraw_target_setup_instructions import (
    EXCALIDRAW_TARGET_SETUP_READY,
    EXCALIDRAW_TARGET_SETUP_BLOCKED_READINESS,
)
from runtime.browser_runtime.excalidraw_target_contract import (
    EXCALIDRAW_TARGET_CONTRACT_READY,
    EXCALIDRAW_TARGET_CONTRACT_REQUEST_READY,
)
from runtime.browser_runtime.excalidraw_target_response import (
    EXCALIDRAW_TARGET_RESPONSE_ACCEPTED,
    EXCALIDRAW_TARGET_RESPONSE_PENDING,
)
from runtime.browser_runtime.excalidraw_mcp_execution_approval import (
    EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED,
)
from runtime.browser_runtime.excalidraw_mcp_proof_execution import (
    EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_APPROVAL,
)
from runtime.browser_runtime.excalidraw_public_drawing_approval import (
    EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_BLOCKED,
    EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_WRITTEN,
)
from runtime.browser_runtime.excalidraw_public_drawing_proof import (
    EXCALIDRAW_PUBLIC_DRAWING_PROOF_COMPLETE,
)
from runtime.browser_runtime.excalidraw_readiness_from_response import (
    EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_PENDING,
    EXCALIDRAW_READINESS_FROM_RESPONSE_READY,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _args(**kwargs) -> argparse.Namespace:
    defaults = {"vault_root": None, "output_json": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _prep_payload() -> dict:
    false_keys = [
        "live_proof_allowed_in_this_pass", "browser_launch_attempted",
        "cdp_connection_attempted", "mcp_server_invoked", "mcp_tool_call_attempted",
        "network_navigation_attempted", "real_profile_access_attempted",
        "credential_or_cookie_read_attempted", "cookie_export_attempted",
        "browser_profile_sync_attempted", "public_tunnel_attempted",
        "browser_harness_used", "browser_use_cli_live_used", "workflow_use_code_copied",
        "trusted_skill_write_attempted", "skill_activation_attempted",
        "agent_bus_enqueue_attempted", "provider_call_attempted",
        "gate_mutation_attempted", "canonical_writeback_attempted",
    ]
    payload = {
        "record_type": "excalidraw_local_browser_mcp_proof_prep",
        "schema_version": "browser.excalidraw_mcp_proof_prep.v1",
        "status": "excalidraw_local_browser_mcp_proof_prep_ready_no_execution",
        "prep_artifact_written": True,
    }
    payload.update({k: False for k in false_keys})
    return payload


def _blocked_readiness_payload() -> dict:
    false_keys = [
        "browser_launch_attempted", "cdp_connection_attempted", "mcp_server_invoked",
        "mcp_tool_call_attempted", "network_navigation_attempted", "dependency_install_attempted",
        "real_profile_access_attempted", "credential_or_cookie_read_attempted",
        "cookie_export_attempted", "browser_profile_sync_attempted", "public_tunnel_attempted",
        "browser_harness_used", "browser_use_cli_live_used", "workflow_use_code_copied",
        "trusted_skill_write_attempted", "skill_activation_attempted",
        "agent_bus_enqueue_attempted", "provider_call_attempted",
        "gate_mutation_attempted", "canonical_writeback_attempted",
    ]
    payload = {
        "record_type": "excalidraw_local_browser_mcp_live_readiness",
        "schema_version": "browser.excalidraw_mcp_live_readiness.v1",
        "status": "blocked_excalidraw_live_readiness_missing_local_target",
        "readiness_artifact_written": True,
        "prep_evidence_ready": True,
        "browser_controller_ready": True,
        "blockers": ["local_excalidraw_target_url_not_provided"],
    }
    payload.update({k: False for k in false_keys})
    return payload


def _seed_prep(tmp_path: Path) -> None:
    path = tmp_path / "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_proof_prep_20260503_ready.json"
    _write_json(path, _prep_payload())


def _seed_blocked_artifact(tmp_path: Path) -> None:
    path = tmp_path / "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_blocked_missing_local_target.json"
    _write_json(path, _blocked_readiness_payload())


def _seed_public_reachability(tmp_path: Path) -> None:
    screenshot = tmp_path / "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.png"
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    screenshot.write_bytes(b"png")
    _write_json(
        tmp_path / "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.json",
        {
            "ok": True,
            "status": "excalidraw_live_browser_proof_complete",
            "target_url": "https://excalidraw.com",
            "canvas_found": True,
            "screenshot_path": "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.png",
            "authority": {
                "target_registered_in_chaseos": True,
                "target_registry_id": "excalidraw",
                "env_var_required": False,
                "no_login_profile_cookies": True,
                "no_browser_use_cli": True,
                "no_agent_bus_writes": True,
                "no_gate_mutation": True,
                "no_canonical_mutation": True,
                "no_provider_calls": True,
            },
        },
    )


# ── chain readiness ───────────────────────────────────────────────────────────

class TestExcalidrawChainReadiness:
    def test_returns_nonzero_when_blocked(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_chain_readiness(_args())
        assert rc != 0

    def test_json_output_has_required_keys(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_chain_readiness(_args(output_json=True))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "status" in data
        assert "chain_steps" in data
        assert "next_recommended_pass" in data
        assert "blockers" in data

    def test_text_output_shows_status_and_next_pass(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_chain_readiness(_args())
        out = capsys.readouterr().out
        assert "status:" in out
        assert "next_recommended_pass:" in out

    def test_chain_steps_all_present(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_chain_readiness(_args(output_json=True))
        data = json.loads(capsys.readouterr().out)
        step_names = {s["step"] for s in data["chain_steps"]}
        assert "target_response_resolution" in step_names
        assert "execution_approval_contract" in step_names

    def test_vault_resolution_error_returns_1(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("no vault")))
        rc = cmd_operate_browser_excalidraw_chain_readiness(_args())
        assert rc == 1


# ── live readiness ────────────────────────────────────────────────────────────

class TestExcalidrawLiveReadiness:
    def test_blocked_missing_target_returns_nonzero(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        _seed_prep(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_live_readiness(_args(local_target_url=""))
        assert rc != 0

    def test_json_output_has_required_keys(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        _seed_prep(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_live_readiness(_args(output_json=True))
        data = json.loads(capsys.readouterr().out)
        assert "status" in data
        assert "blockers" in data
        assert "readiness_artifact_written" in data
        assert "next_recommended_pass" in data

    def test_text_output_shows_status(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        _seed_prep(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_live_readiness(_args())
        out = capsys.readouterr().out
        assert "status:" in out
        assert "next_recommended_pass:" in out

    def test_blocked_status_is_missing_target(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        _seed_prep(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_live_readiness(_args(output_json=True))
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_MISSING_TARGET

    def test_write_readiness_creates_artifact(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        _seed_prep(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_live_readiness(_args(write_readiness=True, output_json=True))
        data = json.loads(capsys.readouterr().out)
        assert data["readiness_artifact_written"] is True
        artifact = tmp_path / "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_blocked_missing_local_target.json"
        assert artifact.is_file()

    def test_vault_error_returns_1(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("no vault")))
        rc = cmd_operate_browser_excalidraw_live_readiness(_args())
        assert rc == 1


# ── readiness from response ───────────────────────────────────────────────────

class TestExcalidrawReadinessFromResponse:
    def test_blocked_pending_response_returns_nonzero(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        _seed_prep(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_target_response(
            _args(output_json=True, write_response=True)
        )
        capsys.readouterr()

        rc = cmd_operate_browser_excalidraw_readiness_from_response(_args(output_json=True))
        data = json.loads(capsys.readouterr().out)

        assert rc == 1
        assert data["status"] == EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_PENDING
        assert "excalidraw_target_response_pending_external_runtime" in data["blockers"]
        assert data["browser_launch_attempted"] is False
        assert data["canonical_writeback_attempted"] is False

    def test_ready_with_accepted_response_when_controller_available(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        _seed_prep(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_target_response(
            _args(
                output_json=True,
                target_url="http://127.0.0.1:3030/",
                write_response=True,
            )
        )
        capsys.readouterr()

        rc = cmd_operate_browser_excalidraw_readiness_from_response(_args(output_json=True))
        data = json.loads(capsys.readouterr().out)

        assert rc in {0, 1}
        if rc == 0:
            assert data["status"] == EXCALIDRAW_READINESS_FROM_RESPONSE_READY
            assert data["target_url"] == "http://127.0.0.1:3030/"
        assert data["network_probe_attempted"] is False
        assert data["browser_launch_attempted"] is False
        assert data["mcp_invocation_attempted"] is False

    def test_write_bridge_creates_artifact_when_blocked(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        _seed_prep(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_target_response(
            _args(output_json=True, write_response=True)
        )
        capsys.readouterr()

        cmd_operate_browser_excalidraw_readiness_from_response(
            _args(output_json=True, write_bridge=True)
        )
        data = json.loads(capsys.readouterr().out)

        assert data["bridge_artifact_written"] is True
        assert Path(data["bridge_artifact_path"]).is_file()

    def test_vault_error_returns_1(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("no vault")))
        rc = cmd_operate_browser_excalidraw_readiness_from_response(_args())
        assert rc == 1


# ── setup instructions ────────────────────────────────────────────────────────

class TestExcalidrawSetupInstructions:
    def test_ready_when_blocked_artifact_present(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        _seed_blocked_artifact(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_setup_instructions(_args())
        assert rc == 0
        out = capsys.readouterr().out
        assert "status:" in out
        assert "next_recommended_pass:" in out

    def test_blocked_when_no_artifact(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_setup_instructions(_args())
        assert rc != 0

    def test_json_output_has_required_keys(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        _seed_blocked_artifact(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_setup_instructions(_args(output_json=True))
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == EXCALIDRAW_TARGET_SETUP_READY
        assert "runtime_handoff" in data
        assert "setup_modes" in data
        assert "readiness_rerun_command" in data

    def test_json_blocked_status_when_no_artifact(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_setup_instructions(_args(output_json=True))
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == EXCALIDRAW_TARGET_SETUP_BLOCKED_READINESS

    def test_write_instructions_creates_artifact(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        _seed_blocked_artifact(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_setup_instructions(_args(write_instructions=True, output_json=True))
        data = json.loads(capsys.readouterr().out)
        assert data["setup_artifact_written"] is True
        artifact = tmp_path / "07_LOGS/Browser-Runs/excalidraw_local_target_setup_instructions_20260503_ready.json"
        assert artifact.is_file()

    def test_vault_error_returns_1(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("no vault")))
        rc = cmd_operate_browser_excalidraw_setup_instructions(_args())
        assert rc == 1


# ── target contract ───────────────────────────────────────────────────────────

class TestExcalidrawTargetContract:
    def test_request_ready_when_no_url(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_target_contract(_args(target_url=""))
        assert rc != 0
        out = capsys.readouterr().out
        assert "status:" in out

    def test_ready_when_local_url_provided(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_target_contract(_args(target_url="http://127.0.0.1:3002/"))
        assert rc == 0
        out = capsys.readouterr().out
        assert "status:" in out

    def test_blocked_when_nonlocal_url(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_target_contract(_args(target_url="https://excalidraw.com/"))
        assert rc != 0

    def test_json_no_url_request_ready_status(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_target_contract(_args(output_json=True))
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == EXCALIDRAW_TARGET_CONTRACT_REQUEST_READY
        assert "target_requirements" in data
        assert "next_recommended_pass" in data

    def test_json_local_url_ready_status(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_target_contract(
            _args(output_json=True, target_url="http://localhost:3001/")
        )
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == EXCALIDRAW_TARGET_CONTRACT_READY
        assert data["target_url"] == "http://localhost:3001/"
        assert data["next_recommended_pass"] == "excalidraw-local-browser-mcp-live-readiness-with-target"

    def test_write_contract_flag_propagates(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_target_contract(
            _args(output_json=True, target_url="http://127.0.0.1:3002/", write_contract=True)
        )
        data = json.loads(capsys.readouterr().out)
        assert data["contract_artifact_written"] is True
        artifact = tmp_path / "07_LOGS/Browser-Runs/excalidraw_local_target_contract_20260503_ready.json"
        assert artifact.is_file()

    def test_vault_error_returns_1(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("no vault")))
        rc = cmd_operate_browser_excalidraw_target_contract(_args())
        assert rc == 1


# ── target response ─────────────────────────────────────────────────────────

class TestExcalidrawTargetResponse:
    def test_pending_when_no_target_or_env_without_write(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_target_response(_args(output_json=True))
        data = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert data["status"] == EXCALIDRAW_TARGET_RESPONSE_PENDING
        assert data["target_url_source"] == "none"
        assert data["response_artifact_written"] is False
        assert data["network_probe_attempted"] is False

    def test_accepts_loopback_target_from_argument_without_probe(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_target_response(
            _args(output_json=True, target_url="http://127.0.0.1:3010/")
        )
        data = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert data["status"] == EXCALIDRAW_TARGET_RESPONSE_ACCEPTED
        assert data["target_url_source"] == "argument"
        assert data["target_url"] == "http://127.0.0.1:3010/"
        assert data["network_probe_attempted"] is False

    def test_accepts_loopback_target_from_env_without_probe(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        monkeypatch.setenv("CHASEOS_EXCALIDRAW_TARGET_URL", "http://localhost:3020/")
        rc = cmd_operate_browser_excalidraw_target_response(
            _args(output_json=True, from_env=True)
        )
        data = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert data["status"] == EXCALIDRAW_TARGET_RESPONSE_ACCEPTED
        assert data["target_url_source"] == "CHASEOS_EXCALIDRAW_TARGET_URL"
        assert data["target_url"] == "http://localhost:3020/"
        assert data["browser_launch_attempted"] is False

    def test_blocks_nonlocal_target_from_env(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        monkeypatch.setenv("CHASEOS_EXCALIDRAW_TARGET_URL", "https://excalidraw.com/")
        rc = cmd_operate_browser_excalidraw_target_response(
            _args(output_json=True, from_env=True)
        )
        data = json.loads(capsys.readouterr().out)
        assert rc == 1
        assert data["target_url_source"] == "CHASEOS_EXCALIDRAW_TARGET_URL"
        assert "target_url_must_use_loopback_host" in data["blocked_reasons"]
        assert data["public_tunnel_attempted"] is False

    def test_write_response_writes_only_pending_input_response_artifact(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_target_response(
            _args(
                output_json=True,
                target_url="http://127.0.0.1:3030/",
                write_response=True,
            )
        )
        data = json.loads(capsys.readouterr().out)
        artifact = Path(data["response_artifact_path"])
        assert data["status"] == EXCALIDRAW_TARGET_RESPONSE_ACCEPTED
        assert data["response_artifact_written"] is True
        assert artifact.is_file()
        assert "03_INPUTS/Browser-Target-Responses/_pending" in artifact.as_posix()

    def test_vault_error_returns_1(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("no vault")))
        rc = cmd_operate_browser_excalidraw_target_response(_args())
        assert rc == 1


# ── execution approval/proof shell ──────────────────────────────────────────

class TestExcalidrawMCPExecutionApprovalCLI:
    def test_blocked_without_accepted_target_response(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_mcp_execution_approval(_args(output_json=True))
        data = json.loads(capsys.readouterr().out)
        assert rc == 1
        assert data["status"] == EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED
        assert data["approval_request_written"] is False
        assert data["idempotency_marker_written"] is False
        assert data["execution_allowed"] is False
        assert data["browser_launch_attempted"] is False
        assert data["mcp_invocation_attempted"] is False
        assert data["canonical_writeback_attempted"] is False

    def test_text_output_includes_status_and_next_step(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        cmd_operate_browser_excalidraw_mcp_execution_approval(_args())
        out = capsys.readouterr().out
        assert "status:" in out
        assert "next_step:" in out

    def test_vault_error_returns_1(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("no vault")))
        rc = cmd_operate_browser_excalidraw_mcp_execution_approval(_args())
        assert rc == 1


class TestExcalidrawMCPProofExecutionCLI:
    def test_blocked_without_approval_readiness(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_mcp_proof_execution(_args(output_json=True))
        data = json.loads(capsys.readouterr().out)
        assert rc == 1
        assert data["status"] == EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_APPROVAL
        assert data["approval_request_written"] is False
        assert data["idempotency_marker_written"] is False
        assert data["execution_attempted"] is False
        assert data["browser_launch_attempted"] is False
        assert data["mcp_invocation_attempted"] is False
        assert data["canonical_writeback_attempted"] is False

    def test_execute_flag_still_no_execution_when_blocked(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_mcp_proof_execution(
            _args(output_json=True, execute_local_canvas_proof=True, live_executor_enabled=True)
        )
        data = json.loads(capsys.readouterr().out)
        assert rc == 1
        assert data["execution_attempted"] is False
        assert data["browser_launch_attempted"] is False
        assert data["mcp_tool_call_attempted"] is False

    def test_vault_error_returns_1(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("no vault")))
        rc = cmd_operate_browser_excalidraw_mcp_proof_execution(_args())
        assert rc == 1


class TestExcalidrawPublicDrawingApprovalCLI:
    def test_blocked_without_public_reachability(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_public_drawing_approval(_args(output_json=True))
        data = json.loads(capsys.readouterr().out)

        assert rc == 1
        assert data["status"] == EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_BLOCKED
        assert "public_reachability_evidence_ready" in data["blockers"]
        assert data["browser_launch_attempted"] is False
        assert data["drawing_action_attempted"] is False

    def test_write_approval_with_public_reachability(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        _seed_public_reachability(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_public_drawing_approval(
            _args(output_json=True, write_approval=True)
        )
        data = json.loads(capsys.readouterr().out)

        assert rc == 0
        assert data["status"] == EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_WRITTEN
        assert data["approval_artifact_written"] is True
        assert data["future_single_run_approved"] is True
        assert data["execution_allowed_in_this_pass"] is False
        assert data["canonical_writeback_attempted"] is False
        assert (tmp_path / data["approval_artifact_path"]).is_file()

    def test_text_output_includes_status_and_next_step(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        _seed_public_reachability(tmp_path)
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)
        rc = cmd_operate_browser_excalidraw_public_drawing_approval(_args())
        out = capsys.readouterr().out

        assert rc == 0
        assert "status:" in out
        assert "next_step:" in out

    def test_vault_error_returns_1(self, tmp_path, monkeypatch):
        import runtime.cli.main as main_mod
        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("no vault")))
        rc = cmd_operate_browser_excalidraw_public_drawing_approval(_args())
        assert rc == 1


class TestExcalidrawPublicDrawingProofCLI:
    def test_json_output_runs_approved_proof(self, tmp_path, monkeypatch, capsys):
        import runtime.cli.main as main_mod
        import runtime.browser_runtime.excalidraw_public_drawing_proof as proof_mod

        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: tmp_path)

        def fake_runner(vault_root, **kwargs):
            assert vault_root == tmp_path
            assert kwargs["approval_id"] == "approval-123"
            assert kwargs["headless"] is True
            assert kwargs["settle_ms"] == 7000
            return {
                "ok": True,
                "status": EXCALIDRAW_PUBLIC_DRAWING_PROOF_COMPLETE,
                "approval_id": "approval-123",
                "target_url": "https://excalidraw.com",
                "page_title": "Excalidraw Whiteboard",
                "canvas_found": True,
                "screenshot_path": "07_LOGS/Browser-Runs/proof.png",
                "evidence_json_path": "07_LOGS/Browser-Runs/proof.json",
                "agent_activity_evidence_path": "07_LOGS/Agent-Activity/_excalidraw_public_drawing_runs/proof.json",
                "checks": [],
                "blockers": [],
            }

        monkeypatch.setattr(proof_mod, "run_excalidraw_public_drawing_proof", fake_runner)
        rc = cmd_operate_browser_excalidraw_public_drawing_proof(
            _args(output_json=True, approval_id="approval-123", headed=False, settle_ms=7000)
        )
        data = json.loads(capsys.readouterr().out)

        assert rc == 0
        assert data["status"] == EXCALIDRAW_PUBLIC_DRAWING_PROOF_COMPLETE
        assert data["approval_id"] == "approval-123"

    def test_vault_error_returns_1(self, monkeypatch):
        import runtime.cli.main as main_mod

        monkeypatch.setattr(main_mod, "_resolve_vault", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("no vault")))
        rc = cmd_operate_browser_excalidraw_public_drawing_proof(_args())
        assert rc == 1
