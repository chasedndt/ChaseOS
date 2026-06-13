"""Tests for the canonical CLI JSON envelope."""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402
import runtime.lifecycle.health_cli as health_cli  # noqa: E402
import runtime.setup_cli as setup_cli  # noqa: E402
from runtime.cli.json_contract import JSON_CONTRACT_KEYS, envelope_json_payload  # noqa: E402

INTAKE_FIXTURE_VAULT = _VAULT_ROOT / "runtime" / "cli" / "fixtures" / "intake_vault"
INTAKE_FIXTURE_ITEM = (
    INTAKE_FIXTURE_VAULT
    / "03_INPUTS"
    / "00_QUARANTINE"
    / "Sources"
    / "20260510__fixture__cli-ratchet-source.md"
)
MAINTAIN_FIXTURE_VAULT = _VAULT_ROOT / "runtime" / "cli" / "fixtures" / "maintain_vault"


def _write_heartbeat_fixture(
    vault: Path,
    *,
    runtime_name: str = "codex",
    bus_name: str = "Codex",
    last_seen: str | None = None,
    status: str = "idle",
    health: str = "ok",
) -> None:
    lifecycle_dir = vault / "runtime" / "lifecycle"
    runtime_dir = vault / "runtime" / runtime_name
    agent_bus_dir = vault / "runtime" / "agent_bus"
    lifecycle_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    agent_bus_dir.mkdir(parents=True)
    (lifecycle_dir / f"{runtime_name}.lifecycle.yaml").write_text(
        f'runtime_id: "{runtime_name}"\nhealth:\n  kind: "heartbeat"\n',
        encoding="utf-8",
    )
    (runtime_dir / "capabilities.yaml").write_text(
        f'runtime: "{runtime_name}"\nbus_name: "{bus_name}"\nheartbeat_stale_seconds: 900\n',
        encoding="utf-8",
    )
    conn = sqlite3.connect(agent_bus_dir / "agent_bus.sqlite")
    conn.execute(
        """
        CREATE TABLE heartbeats (
          heartbeat_key TEXT PRIMARY KEY,
          runtime TEXT NOT NULL,
          runtime_instance_id TEXT,
          heartbeat_scope TEXT NOT NULL DEFAULT 'runtime',
          control_surface TEXT,
          control_surface_key TEXT,
          status TEXT NOT NULL,
          current_task_id TEXT,
          health TEXT NOT NULL,
          summary TEXT,
          last_seen TEXT NOT NULL
        )
        """
    )
    if last_seen is not None:
        conn.execute(
            """
            INSERT INTO heartbeats (
              heartbeat_key, runtime, runtime_instance_id, heartbeat_scope,
              control_surface, control_surface_key, status, current_task_id,
              health, summary, last_seen
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bus_name,
                bus_name,
                None,
                "runtime",
                "codex",
                runtime_name,
                status,
                None,
                health,
                "fixture heartbeat",
                last_seen,
            ),
        )
    conn.commit()
    conn.close()


def test_envelope_preserves_native_payload_under_result() -> None:
    payload = envelope_json_payload(
        {"runtime_id": "openclaw", "audit_id": "audit-123"},
        action="agent.status",
        exit_code=0,
    )

    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "agent.status"
    assert payload["result"]["runtime_id"] == "openclaw"
    assert payload["errors"] == []
    assert payload["warnings"] == []
    assert payload["audit_id"] == "audit-123"


def test_canonical_cli_json_output_uses_contract_keys(capsys) -> None:
    exit_code = cli.main(["gate", "check-operation", "gateway.magic.write", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is False
    assert payload["action"] == "gate.check-operation"
    assert payload["result"]["operation"] == "gateway.magic.write"
    assert payload["errors"]


def test_cli_contract_verification_command_uses_json_envelope(capsys) -> None:
    exit_code = cli.main(["test", "cli-contract", "--no-smoke", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "test.cli-contract"
    assert payload["result"]["status"] == "passed"


def test_doctor_cli_default_reports_skipped_contract_ratchet(capsys) -> None:
    exit_code = cli.main(["doctor", "cli", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "doctor.cli"
    assert payload["result"]["cli_contract_ratchet"]["status"] == "skipped"
    assert payload["result"]["cli_contract_ratchet"]["requested"] is False
    assert "cli contract ratchet" not in {
        check["name"] for check in payload["result"]["checks"]
    }


def test_doctor_cli_contract_ratchet_reports_result_and_check(capsys) -> None:
    exit_code = cli.main(["doctor", "cli", "--contract-ratchet", "--json"])

    payload = json.loads(capsys.readouterr().out)
    checks = {check["name"]: check for check in payload["result"]["checks"]}
    ratchet = payload["result"]["cli_contract_ratchet"]

    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "doctor.cli"
    assert checks["cli contract ratchet"]["ok"] is True
    assert ratchet["requested"] is True
    assert ratchet["run_smokes"] is False
    assert ratchet["status"] == "passed"
    assert any(
        check["name"] == "cross_family_json_smokes" and check["status"] == "skipped"
        for check in ratchet["checks"]
    )


def test_setup_status_json_uses_canonical_envelope(capsys) -> None:
    exit_code = cli.main(["setup", "status", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "setup.status"
    assert "providers" in payload["result"]
    assert "integrations" in payload["result"]


def test_setup_validate_json_uses_canonical_envelope(capsys) -> None:
    exit_code = cli.main(["setup", "validate", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code in {0, 1}
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is (exit_code == 0)
    assert payload["action"] == "setup.validate"
    assert "providers" in payload["result"]
    assert "integrations" in payload["result"]
    if exit_code != 0:
        assert payload["errors"]


def test_setup_validate_json_envelope_preserves_provider_secret_reference_aliases(
    monkeypatch, capsys
) -> None:
    profile = {
        "secret_reference_kind": "env-var-or-local-secret-ref",
        "validation_checks": ["api_key_present", "model_selected", "secret_reference_present"],
    }
    state = {
        "configured": True,
        "api_key_present": True,
        "model_selected": True,
        "secret_reference_present": True,
        "secret_reference_kind": "env-var-or-local-secret-ref",
        "secret_reference_target": "SET_OPENAI_SECRET_REF",
    }
    monkeypatch.delenv("SET_OPENAI_SECRET_REF", raising=False)
    monkeypatch.setattr(setup_cli, "ensure_setup_state", lambda: None)
    monkeypatch.setattr(
        setup_cli,
        "load_setup_registry",
        lambda: {"providers": [{"id": "openai"}], "integrations": []},
    )
    monkeypatch.setattr(setup_cli, "load_provider_profiles", lambda: {"openai": profile})
    monkeypatch.setattr(setup_cli, "load_setup_state", lambda: {"providers": {"openai": state}})

    exit_code = cli.main(["setup", "validate", "--json"])

    envelope = json.loads(capsys.readouterr().out)
    provider = envelope["result"]["providers"][0]
    assert exit_code == 1
    assert tuple(envelope.keys()) == JSON_CONTRACT_KEYS
    assert envelope["ok"] is False
    assert envelope["action"] == "setup.validate"
    assert envelope["result"]["safe_to_call_update_goal_complete"] is False
    assert envelope["result"]["no_safe_autonomous_completion_pass_available"] is True
    assert envelope["result"]["update_goal_allowed"] is False
    assert envelope["result"]["next_operator_action_id"] == "openai_secret_reference"
    assert envelope["result"]["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert provider["secret_reference_target"] == "SET_OPENAI_SECRET_REF"
    assert provider["secret_reference_target_is_placeholder"] is True
    assert provider["secret_reference_resolvable"] is False
    assert provider["secret_reference_probe_source"] == "env-var-or-local-secret-ref"
    assert provider["secret_reference_probe_error"] == "reference_not_found"
    assert provider["safe_to_call_update_goal_complete"] is False
    assert provider["no_safe_autonomous_completion_pass_available"] is True
    assert provider["update_goal_allowed"] is False
    assert provider["next_operator_action_id"] == "openai_secret_reference"
    assert provider["next_recommended_pass"] == "operator-provide-openai-secret-reference"


def test_setup_provider_validate_json_envelope_preserves_secret_reference_aliases(
    monkeypatch, capsys
) -> None:
    profile = {
        "secret_reference_kind": "env-var-or-local-secret-ref",
        "validation_checks": ["api_key_present", "model_selected", "secret_reference_present"],
    }
    state = {
        "configured": True,
        "api_key_present": True,
        "model_selected": True,
        "secret_reference_present": True,
        "secret_reference_kind": "env-var-or-local-secret-ref",
        "secret_reference_target": "SET_OPENAI_SECRET_REF",
    }
    monkeypatch.delenv("SET_OPENAI_SECRET_REF", raising=False)
    monkeypatch.setattr(setup_cli, "load_setup_registry", lambda: {"providers": [{"id": "openai"}]})
    monkeypatch.setattr(setup_cli, "load_provider_profiles", lambda: {"openai": profile})
    monkeypatch.setattr(setup_cli, "load_setup_state", lambda: {"providers": {"openai": state}})

    exit_code = cli.main(["setup", "provider", "validate", "openai", "--json"])

    envelope = json.loads(capsys.readouterr().out)
    payload = envelope["result"]
    assert exit_code == 1
    assert tuple(envelope.keys()) == JSON_CONTRACT_KEYS
    assert envelope["ok"] is False
    assert envelope["action"] == "setup.provider.validate"
    assert payload["safe_to_call_update_goal_complete"] is False
    assert payload["no_safe_autonomous_completion_pass_available"] is True
    assert payload["update_goal_allowed"] is False
    assert payload["next_operator_action_id"] == "openai_secret_reference"
    assert payload["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert payload["secret_reference_target"] == "SET_OPENAI_SECRET_REF"
    assert payload["secret_reference_target_is_placeholder"] is True
    assert payload["secret_reference_resolvable"] is False
    assert payload["secret_reference_probe_source"] == "env-var-or-local-secret-ref"
    assert payload["secret_reference_probe_error"] == "reference_not_found"


def test_capture_status_json_uses_packaged_fixture_without_writes(capsys) -> None:
    exit_code = cli.main([
        "capture",
        "status",
        "--vault-root",
        str(INTAKE_FIXTURE_VAULT),
        "--json",
    ])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "capture.status"
    assert payload["result"]["read_only"] is True
    assert payload["result"]["mutates_capture"] is False
    assert payload["result"]["total_quarantine"] == 1
    assert payload["result"]["dedup_registry"]["entry_count"] == 1
    assert payload["result"]["writes_performed"] is False


def test_intake_ls_json_uses_packaged_fixture_without_writes(capsys) -> None:
    exit_code = cli.main([
        "intake",
        "ls",
        "--vault-root",
        str(INTAKE_FIXTURE_VAULT),
        "--json",
    ])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "intake.ls"
    assert payload["result"]["read_only"] is True
    assert payload["result"]["total_quarantine"] == 1
    assert payload["result"]["writes_performed"] is False


def test_intake_inspect_json_uses_packaged_fixture(capsys) -> None:
    exit_code = cli.main(["intake", "inspect", str(INTAKE_FIXTURE_ITEM), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "intake.inspect"
    assert payload["result"]["capture_id"] == "capture_fixture_cli_ratchet_source_20260510"
    assert payload["result"]["input_class"] == "source"
    assert payload["result"]["extra_metadata"]["writes_performed"] is False


def test_maintain_status_json_is_fast_read_only_profile(capsys) -> None:
    exit_code = cli.main(["maintain", "--status", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "maintain"
    assert payload["result"]["read_only"] is True
    assert payload["result"]["mutates_vault"] is False
    assert payload["result"]["full_scan_deferred_from_ratchet"] is True
    assert payload["result"]["writes_performed"] is False


def test_capture_validate_json_is_fixture_no_write_profile(capsys) -> None:
    exit_code = cli.main(["capture", "validate", "--vault-root", str(INTAKE_FIXTURE_VAULT), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "capture.validate"
    assert payload["result"]["valid"] is True
    assert payload["result"]["read_only"] is True
    assert payload["result"]["safe_validate_only"] is True
    assert payload["result"]["writes_performed"] is False
    assert payload["result"]["authority_flags"]["connector_calls_allowed"] is False
    assert payload["result"]["authority_flags"]["quarantine_write_allowed"] is False


def test_maintain_fixture_dry_run_json_is_bounded_no_write_profile(capsys) -> None:
    exit_code = cli.main(
        [
            "maintain",
            "--dry-run",
            "--fixture-root",
            str(MAINTAIN_FIXTURE_VAULT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "maintain"
    result = payload["result"]
    assert result["dry_run"] is True
    assert result["read_only"] is True
    assert result["bounded_fixture_mode"] is True
    assert result["bounded_fixture_root"] == str(MAINTAIN_FIXTURE_VAULT.resolve())
    assert result["writes_performed"] is False
    assert result["authority_flags"]["read_only"] is True
    assert result["authority_flags"]["maintenance_fix_allowed"] is False
    assert result["stage_1_vault_hygiene"]["files_scanned"] >= 1
    assert "stage_2_daily_hub" in result
    assert "stage_3_provenance" in result


def test_n8n_dry_run_json_has_no_live_execution_or_writes(capsys) -> None:
    exit_code = cli.main(
        [
            "n8n",
            "dry-run",
            "send_discord_draft_alert",
            "--caller",
            "chaseos_runtime_mcp",
            "--payload",
            "{}",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "n8n.dry-run"
    result = payload["result"]
    assert result["status"] == "dry_run_ready"
    assert result["dry_run"] is True
    assert result["live_http_call"] is False
    assert result["writes_performed"] is False
    assert result["draft"]["workflow_id"] == "send_discord_draft_alert"
    assert result["authority_flags"]["workflow_execution_allowed"] is False
    assert result["authority_flags"]["live_http_call_allowed"] is False


def test_run_operator_today_dry_run_json_has_no_write_authority(capsys) -> None:
    exit_code = cli.main(["run", "operator_today", "--dry-run", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "run"
    result = payload["result"]
    assert result["workflow_id"] == "operator_today"
    assert result["status"] == "dry_run_ok"
    assert result["dry_run"] is True
    assert result["stage_reached"] == "dry_run_exit"
    assert result["outputs"]["dry_run"] is True
    assert result["writes_performed"] is False
    assert result["authority_flags"]["read_only"] is True
    assert result["authority_flags"]["workflow_execution_allowed"] is False
    assert result["authority_flags"]["writeback_allowed"] is False
    assert result["authority_flags"]["agent_bus_write_allowed"] is False


def test_health_openclaw_json_reports_detected_gateway(monkeypatch, capsys) -> None:
    def fake_probe(url: str, success_status: int, timeout_seconds: int) -> dict:
        return {
            "url": url,
            "timed_out": False,
            "status_code": success_status,
            "healthy": True,
            "stdout": "ok",
            "stderr": "",
            "failure_reason": None,
        }

    monkeypatch.setattr(health_cli, "_probe_http_url", fake_probe)

    exit_code = cli.main(["health", "openclaw", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "health"
    assert payload["result"]["runtime_id"] == "openclaw"
    assert payload["result"]["status"] == "healthy"
    assert payload["result"]["gateway_detected"] is True
    assert payload["result"]["writes_performed"] is False


def test_health_openclaw_json_reports_gateway_unavailable(monkeypatch, capsys) -> None:
    def fake_probe(url: str, success_status: int, timeout_seconds: int) -> dict:
        return {
            "url": url,
            "timed_out": False,
            "status_code": None,
            "healthy": False,
            "stdout": "",
            "stderr": "connection refused",
            "failure_reason": "connection_error",
        }

    monkeypatch.setattr(health_cli, "_probe_http_url", fake_probe)

    exit_code = cli.main(["health", "openclaw", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is False
    assert payload["action"] == "health"
    assert payload["result"]["runtime_id"] == "openclaw"
    assert payload["result"]["status"] == "unavailable"
    assert payload["result"]["gateway_detected"] is False
    assert payload["result"]["blocked_reason"] == "connection_error"
    assert payload["errors"]


def test_health_hermes_json_reports_detected_gateway(monkeypatch, capsys) -> None:
    def fake_probe(url: str, success_status: int, timeout_seconds: int) -> dict:
        return {
            "url": url,
            "timed_out": False,
            "status_code": success_status,
            "healthy": True,
            "stdout": "ok",
            "stderr": "",
            "failure_reason": None,
        }

    monkeypatch.setattr(health_cli, "_probe_http_url", fake_probe)

    exit_code = cli.main(["health", "hermes", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "health"
    assert payload["result"]["runtime_id"] == "hermes"
    assert payload["result"]["status"] == "healthy"
    assert payload["result"]["gateway_detected"] is True


def test_health_hermes_json_reports_gateway_unavailable(monkeypatch, capsys) -> None:
    def fake_probe(url: str, success_status: int, timeout_seconds: int) -> dict:
        return {
            "url": url,
            "timed_out": False,
            "status_code": None,
            "healthy": False,
            "stdout": "",
            "stderr": "connection refused",
            "failure_reason": "connection_error",
        }

    monkeypatch.setattr(health_cli, "_probe_http_url", fake_probe)

    exit_code = cli.main(["health", "hermes", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is False
    assert payload["action"] == "health"
    assert payload["result"]["runtime_id"] == "hermes"
    assert payload["result"]["status"] == "unavailable"
    assert payload["result"]["gateway_detected"] is False


def test_health_invalid_runtime_json_is_canonical(capsys) -> None:
    exit_code = cli.main(["health", "not-a-runtime", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is False
    assert payload["action"] == "health"
    assert payload["result"]["status"] == "invalid_runtime"
    assert payload["result"]["blocked_reason"] == "lifecycle_record_missing"


def test_health_missing_config_json_is_canonical(monkeypatch, tmp_path, capsys) -> None:
    lifecycle_dir = tmp_path / "lifecycle"
    lifecycle_dir.mkdir()
    (lifecycle_dir / "empty.lifecycle.yaml").write_text(
        'runtime_id: "empty"\nplatform: "local"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(health_cli, "LIFECYCLE_DIR", lifecycle_dir)

    exit_code = cli.main(["health", "empty", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is False
    assert payload["action"] == "health"
    assert payload["result"]["status"] == "not_configured"
    assert payload["result"]["blocked_reason"] == "health_not_configured"


def test_health_codex_heartbeat_json_reports_fresh_session_runtime(tmp_path, capsys) -> None:
    last_seen = datetime.now(timezone.utc).isoformat()
    _write_heartbeat_fixture(tmp_path, last_seen=last_seen)

    exit_code = cli.main(["health", "codex", "--vault-root", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is True
    assert payload["action"] == "health"
    result = payload["result"]
    assert result["runtime_id"] == "codex"
    assert result["kind"] == "heartbeat"
    assert result["status"] == "healthy"
    assert result["gateway_detected"] is False
    assert result["heartbeat_runtime"] == "Codex"
    assert result["heartbeat_present"] is True
    assert result["heartbeat_fresh"] is True
    assert result["writes_performed"] is False
    assert result["authority_flags"]["read_only"] is True


def test_health_codex_heartbeat_json_reports_unavailable_without_heartbeat(tmp_path, capsys) -> None:
    _write_heartbeat_fixture(tmp_path, last_seen=None)

    exit_code = cli.main(["health", "codex", "--vault-root", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is False
    assert payload["action"] == "health"
    result = payload["result"]
    assert result["runtime_id"] == "codex"
    assert result["kind"] == "heartbeat"
    assert result["status"] == "unavailable"
    assert result["heartbeat_present"] is False
    assert result["heartbeat_fresh"] is False
    assert result["blocked_reason"] == "heartbeat_missing"
    assert result["writes_performed"] is False


def test_health_codex_heartbeat_json_reports_unavailable_for_stale_heartbeat(tmp_path, capsys) -> None:
    last_seen = (datetime.now(timezone.utc) - timedelta(seconds=3600)).isoformat()
    _write_heartbeat_fixture(tmp_path, last_seen=last_seen)

    exit_code = cli.main(["health", "codex", "--vault-root", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is False
    assert payload["action"] == "health"
    assert payload["result"]["status"] == "unavailable"
    assert payload["result"]["heartbeat_present"] is True
    assert payload["result"]["heartbeat_fresh"] is False
    assert payload["result"]["blocked_reason"] == "heartbeat_stale"


def test_n8n_readiness_json_reports_canonical_blocked_posture(capsys) -> None:
    exit_code = cli.main(["n8n", "readiness", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert tuple(payload.keys()) == JSON_CONTRACT_KEYS
    assert payload["ok"] is False
    assert payload["action"] == "n8n.readiness"
    assert payload["result"]["status"] == "blocked"
    assert payload["result"]["readiness_status"] == "blocked"
    assert payload["result"]["live_http_call"] is False
    assert payload["result"]["writes_performed"] is False
    assert payload["result"]["authority_flags"]["read_only"] is True
    assert payload["result"]["authority_flags"]["credential_values_logged"] is False
    assert "N8N_BASE_URL is not set" in payload["result"]["blocked_reasons"]
