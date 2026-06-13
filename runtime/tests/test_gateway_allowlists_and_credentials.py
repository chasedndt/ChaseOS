"""Gate/Gateway allowlist and credential-boundary regression tests."""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime import setup_state  # noqa: E402
from runtime.chaseos_gate import (  # noqa: E402
    check_control_plane_transport,
    check_credential_reference,
    check_external_api,
    check_runtime_operation,
    check_task_type,
    check_write_permission,
    load_gateway_allowlists,
    load_all_manifests,
)


def _workspace_tmp_dir() -> Path:
    path = _VAULT_ROOT / ".codex_tmp_test" / f"gateway-allowlists-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_gateway_allowlists_define_required_categories() -> None:
    allowlists = load_gateway_allowlists()

    assert allowlists["write_targets"]["setup_state"] == ["runtime/setup_state.json"]
    assert allowlists["write_targets"]["osril_run_state"] == ["runtime/osril/run/**"]
    assert "runtime/providers/state/provider_audit.jsonl" in allowlists["write_targets"]["runtime_provider_state"]
    assert "operator-briefing" in allowlists["task_types"]
    assert "provider.openai" in allowlists["external_apis"]
    assert "delivery.discord_webhook" in allowlists["external_apis"]
    assert "delivery.whop_api" in allowlists["external_apis"]
    assert "runtime/agent_bus/" in allowlists["control_plane_transports"]
    assert "secret_reference_target" in allowlists["credential_references"]["reference_only_state_keys"]


def test_gate_manifest_loader_skips_support_policy_files() -> None:
    manifests = load_all_manifests()

    assert "n8n_config" not in manifests
    assert "n8n_workflows" not in manifests
    assert "openai_config" not in manifests
    assert "responses_api" in manifests


def test_write_targets_are_explicitly_allowlisted_by_manifest_category() -> None:
    allowed, reason = check_write_permission("hermes", "07_LOGS/Agent-Activity/example.md")

    assert allowed is True
    assert "allowed" in reason

    allowed, reason = check_write_permission("hermes", "07_LOGS/Unexpected/example.md")

    assert allowed is False
    assert "outside explicit allowlists" in reason


def test_task_types_must_be_globally_and_adapter_allowlisted() -> None:
    allowed, reason = check_task_type("openclaw", "operator-briefing")

    assert allowed is True
    assert "allowed" in reason

    allowed, reason = check_task_type("openclaw", "unclassified")

    assert allowed is False
    assert "global gateway task allowlist" in reason


def test_external_apis_and_transports_are_allowlisted() -> None:
    allowed, reason = check_external_api("provider.openai")
    assert allowed is True
    assert "allowlisted" in reason

    allowed, reason = check_external_api("provider.magic")
    assert allowed is False
    assert "not allowlisted" in reason

    allowed, reason = check_control_plane_transport("discord")
    assert allowed is True
    assert "allowlisted" in reason

    allowed, reason = check_control_plane_transport("chat")
    assert allowed is False
    assert "not allowlisted" in reason


def test_runtime_operation_blocks_unallowlisted_control_plane_transport() -> None:
    allowed, reason = check_runtime_operation(
        "agent_bus.task.create",
        actor_adapter_id="Hermes",
        target_runtime="OpenClaw",
        control_plane_transport="chat",
    )

    assert allowed is False
    assert "Control-plane transport 'chat' is not allowlisted" in reason


def test_credential_reference_accepts_refs_and_blocks_secret_values() -> None:
    allowed, reason = check_credential_reference("env-var", "OPENAI_API_KEY")
    assert allowed is True
    assert "allowed" in reason

    allowed, reason = check_credential_reference("env-var", "test-key-test_1234567890abcdefghijklmnop")
    assert allowed is False
    assert "env var name" in reason


def test_setup_state_writer_blocks_raw_secret_values(monkeypatch: pytest.MonkeyPatch) -> None:
    workdir = _workspace_tmp_dir()
    try:
        example_path = workdir / "setup_state.example.json"
        state_path = workdir / "setup_state.json"
        example_path.write_text('{"providers": {}, "integrations": {}}\n', encoding="utf-8")
        monkeypatch.setattr(setup_state, "SETUP_STATE_EXAMPLE", example_path)
        monkeypatch.setattr(setup_state, "SETUP_STATE_PATH", state_path)

        with pytest.raises(ValueError, match="credential boundary"):
            setup_state.update_provider_state(
                "openai",
                {"api_key": "test-key-test_1234567890abcdefghijklmnop"},
            )

        assert not state_path.exists()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def test_setup_state_writer_allows_reference_only_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workdir = _workspace_tmp_dir()
    try:
        example_path = workdir / "setup_state.example.json"
        state_path = workdir / "setup_state.json"
        example_path.write_text('{"providers": {}, "integrations": {}}\n', encoding="utf-8")
        monkeypatch.setattr(setup_state, "SETUP_STATE_EXAMPLE", example_path)
        monkeypatch.setattr(setup_state, "SETUP_STATE_PATH", state_path)

        path = setup_state.update_provider_state(
            "openai",
            {
                "api_key_present": True,
                "secret_reference_present": True,
                "secret_reference_kind": "env-var",
                "secret_reference_target": "OPENAI_API_KEY",
            },
        )

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["providers"]["openai"]["secret_reference_target"] == "OPENAI_API_KEY"
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
