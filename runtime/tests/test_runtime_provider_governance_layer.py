"""Tests for the Runtime Provider Governance Layer (RPGL)."""

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

import runtime.cli.main as cli  # noqa: E402
import runtime.providers.governance_layer as rpgl  # noqa: E402
import runtime.execution_adapters.execute as execution_adapter  # noqa: E402
from runtime.chaseos_gate import (  # noqa: E402
    RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
    RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
    RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID,
    RUNTIME_PROVIDER_LIVE_PROBE_OPERATION,
    check_runtime_operation,
    get_runtime_operation_approval_schema,
)
from runtime.providers.governance_layer import (  # noqa: E402
    APPROVAL_RELATIVE_DIR,
    CONFIG_APPLY_APPROVAL_RELATIVE_DIR,
    CONFIG_APPLY_CONSUMER_RELATIVE_DIR,
    CONFIG_APPLY_DECISION_RELATIVE_DIR,
    CONFIG_APPLY_MARKER_RELATIVE_DIR,
    CONFIG_APPLY_RESULT_RELATIVE_DIR,
    CONFIG_PROPOSAL_RELATIVE_DIR,
    PROVIDER_TARGET_PROFILE_RELATIVE_PATH,
    TARGET_PROFILE_PROPOSAL_RELATIVE_DIR,
    RuntimeProviderGovernanceError,
    audit_path,
    build_fallback_status,
    build_credential_config_mutation_governance_lane_proof,
    build_provider_config_apply_approval_decision_record,
    build_provider_config_apply_approval_request_preview,
    build_provider_config_apply_atomic_marker_writer_design,
    build_provider_config_apply_decision_consumer_design,
    build_provider_config_apply_decision_consumer_implementation_plan,
    build_provider_config_apply_decision_consumer_preflight,
    build_provider_config_apply_decision_consumer_write_guard_contract,
    build_provider_config_apply_decision_consumer_writer_dry_run,
    build_provider_config_apply_decision_consumption_plan,
    build_provider_config_apply_decision_preflight,
    build_provider_config_apply_design,
    build_provider_config_apply_executor_dry_run_plan,
    build_provider_config_apply_preflight,
    build_provider_config_change_plan,
    build_provider_config_reconciliation,
    build_provider_inventory,
    build_provider_target_profile,
    build_provider_target_profile_plan,
    build_governance_status,
    execute_local_ollama_fallback_stream,
    build_live_probe_executor_spec,
    build_live_probe_approval_decision_record,
    build_live_probe_decision_preflight,
    build_live_probe_executor_dry_run_plan,
    build_live_probe_marker_contract,
    build_live_probe_smoke_readiness,
    build_live_probe_target_approval_plan,
    build_live_smoke_closeout_plan,
    build_rpgl_completion_status,
    evaluate_fallback_timeout,
    load_live_probe_atomic_marker,
    load_live_probe_approval_request,
    load_live_probe_decision_consumer_record,
    load_live_probe_decision_records,
    load_live_probe_result_record,
    load_provider_audit_events,
    load_provider_records,
    load_queue_items,
    mark_primary_rate_limited,
    probe_provider,
    queue_summary,
    record_fallback_timeout,
    retry_queue_item_dry_run,
    route_task,
    run_fallback_timeout_proof,
    run_ollama_timeout_contract,
    run_recovery_dry_run,
    validate_provider_config_apply_approval_request,
    validate_live_probe_approval_request,
    validate_live_probe_decision_records,
    write_live_probe_approval_decision_record,
    write_live_probe_atomic_marker,
    write_live_probe_decision_consumer_record,
    write_live_probe_live_executor,
    write_live_probe_target_approval_requests,
    write_provider_config_apply_approval_decision_record,
    write_provider_config_apply_approval_request,
    write_provider_config_apply_atomic_marker,
    write_provider_config_apply_decision_consumer_record,
    write_provider_config_apply_live_executor,
    write_provider_config_change_approval_request,
    write_provider_target_profile_approval_request,
)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_vault() -> Path:
    vault = _VAULT_ROOT / ".codex_tmp_test" / "rpgl" / uuid.uuid4().hex / "vault"
    vault.mkdir(parents=True)
    _write_text(vault / "CLAUDE.md", "# ChaseOS\n")
    _write_text(
        vault / "runtime" / "openclaw" / "model_config.yaml",
        "\n".join(
            [
                "runtime: openclaw",
                "primary:",
                "  model_id: gpt-5.5",
                "  max_tokens: 8192",
                "  temperature: 0.2",
                "fallbacks:",
                "  - model_id: phi4-mini:latest",
                "    max_tokens: 2048",
                "    temperature: 0.2",
            ]
        )
        + "\n",
    )
    _write_text(
        vault / "runtime" / "openclaw" / "capabilities.yaml",
        "\n".join(
            [
                "runtime: openclaw",
                "bus_name: OpenClaw",
                'display_name: "OpenClaw"',
                'description: "Primary operator runtime"',
                "handles:",
                "  - task_type: operator-briefing",
                "    priority: primary",
                "max_concurrent_tasks: 3",
                "heartbeat_stale_seconds: 900",
                "priority_ceiling: normal",
            ]
        )
        + "\n",
    )
    return vault


def _cleanup_vault(vault: Path) -> None:
    root = (_VAULT_ROOT / ".codex_tmp_test" / "rpgl").resolve()
    target = vault.parent.resolve()
    if target.parent == root:
        shutil.rmtree(target, ignore_errors=True)


def _json_result(stdout: str) -> dict:
    return json.loads(stdout)["result"]


def _cool_down_primary(vault: Path) -> None:
    mark_primary_rate_limited(
        vault,
        provider_id="openai",
        model="gpt-5.5",
        runtime="openclaw",
        retry_after_seconds=300,
        reason="rate_limit",
        source_command="test",
    )


def _write_openai_placeholder_setup_state(vault: Path) -> None:
    _write_text(
        vault / "runtime" / "setup_state.json",
        json.dumps(
            {
                "providers": {
                    "openai": {
                        "configured": True,
                        "auth_present": True,
                        "secret_reference_present": True,
                        "secret_reference_kind": "env-var-or-local-secret-ref",
                        "secret_reference_target": "SET_OPENAI_SECRET_REF",
                        "default_model": "gpt-5.5",
                        "model_selected": True,
                    },
                    "local_oss": {
                        "configured": False,
                        "endpoint_present": False,
                        "model_target_present": False,
                    },
                }
            },
            indent=2,
        )
        + "\n",
    )


def _write_provider_config_mismatch_fixture(vault: Path) -> None:
    _write_text(
        vault / "runtime" / "openclaw" / "model_config.yaml",
        "\n".join(
            [
                "runtime: openclaw",
                "primary:",
                "  model_id: claude-sonnet-4-6",
                "  max_tokens: 4096",
                "  temperature: 0.3",
                "fallbacks:",
                "  - model_id: claude-haiku-4-5-20251001",
                "    max_tokens: 4096",
                "    temperature: 0.3",
            ]
        )
        + "\n",
    )
    _write_text(
        vault / "runtime" / "setup_state.json",
        json.dumps(
            {
                "providers": {
                    "openai": {
                        "configured": True,
                        "auth_present": True,
                        "secret_reference_present": True,
                        "default_model": "set-by-wizard:openai",
                        "model_selected": True,
                    },
                    "local_oss": {
                        "configured": False,
                        "endpoint_present": False,
                        "model_target_present": False,
                    },
                }
            },
            indent=2,
        )
        + "\n",
    )


def test_runtime_provider_governance_status_and_cli_surfaces(capsys) -> None:
    vault = _make_vault()
    try:
        status = build_governance_status(vault)
        assert status["primary_provider"]["provider_id"] == "openai"
        assert status["primary_provider"]["model"] == "gpt-5.5"
        assert status["primary_provider"]["strength"] == "strong"
        assert status["fallback_providers"][0]["provider_id"] == "local_oss"
        assert status["fallback_providers"][0]["model"] == "phi4-mini:latest"
        assert status["fallback_providers"][0]["strength"] == "weak"

        assert cli.main(["runtime", "providers", "--vault-root", str(vault), "--json"]) == 0
        providers_payload = _json_result(capsys.readouterr().out)
        assert providers_payload["feature"] == "Runtime Provider Governance Layer"
        assert any(item["strength"] == "strong" for item in providers_payload["providers"])

        assert cli.main(["runtime", "fallback-status", "--vault-root", str(vault), "--json"]) == 0
        fallback_payload = _json_result(capsys.readouterr().out)
        assert fallback_payload["sticky_for_development"] is False
        assert fallback_payload["timeout_defaults"]["first_token_timeout_sec"] == 30
    finally:
        _cleanup_vault(vault)


def test_execution_adapter_denies_weak_fallback_for_high_authority_primary_failure(monkeypatch) -> None:
    vault = _make_vault()
    calls: list[str] = []

    def fail_primary(**kwargs):
        calls.append(kwargs["model_spec"].model_id)
        raise execution_adapter.ExecutionAdapterError("network error calling primary")

    try:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(execution_adapter, "_call_anthropic", fail_primary)

        with pytest.raises(execution_adapter.ExecutionAdapterError) as exc_info:
            execution_adapter.execute_synthesis(
                prompt_system="system",
                prompt_user="implement a multi-file runtime patch",
                execution_adapter="openclaw",
                vault_root=vault,
                task_class="repo_development",
            )

        assert "RPGL queued high-authority task" in str(exc_info.value)
        assert calls == ["gpt-5.5"]
        queue = queue_summary(vault)
        assert queue["high_complexity_waiting_for_primary"] == 1
        item = queue["items"][0]
        assert item["task_class"] == "repo_development"
        assert item["fallback_denied_reason"] == "weak_fallback_denied_for_high_authority_task"
        records = load_provider_records(vault)
        primary = next(record for record in records.values() if record.is_primary and record.runtime == "openclaw")
        assert primary.state == "unhealthy"
        assert primary.last_error_type == "network_error"
    finally:
        _cleanup_vault(vault)


def test_execution_adapter_denies_weak_fallback_for_medium_task_without_context_allowance(monkeypatch) -> None:
    vault = _make_vault()
    calls: list[str] = []

    def fail_primary(**kwargs):
        calls.append(kwargs["model_spec"].model_id)
        raise execution_adapter.ExecutionAdapterError("network error calling primary")

    try:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(execution_adapter, "_call_anthropic", fail_primary)

        with pytest.raises(execution_adapter.ExecutionAdapterError) as exc_info:
            execution_adapter.execute_synthesis(
                prompt_system="system",
                prompt_user="draft canonical-facing documentation",
                execution_adapter="openclaw",
                vault_root=vault,
                task_class="documentation_draft",
            )

        assert "RPGL denied fallback provider by capability" in str(exc_info.value)
        assert calls == ["gpt-5.5"]
        queue = queue_summary(vault)
        assert queue["queued_task_count"] == 1
        item = queue["items"][0]
        assert item["task_class"] == "documentation_draft"
        assert item["required_provider_strength"] == "medium"
        assert item["fallback_denied_reason"] == "provider_strength_or_state_not_authorized"
    finally:
        _cleanup_vault(vault)


def test_execution_adapter_allows_weak_safe_fallback_after_primary_rate_limit(monkeypatch) -> None:
    vault = _make_vault()
    calls: list[str] = []

    def primary_rate_limit_then_fallback(**kwargs):
        model_id = kwargs["model_spec"].model_id
        calls.append(model_id)
        if model_id == "gpt-5.5":
            raise execution_adapter.ExecutionAdapterError("rate limit")
        return {"text": "failure summary", "usage": {"output_tokens": 2}}

    try:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setattr(execution_adapter, "_call_anthropic", primary_rate_limit_then_fallback)

        result = execution_adapter.execute_synthesis(
            prompt_system="system",
            prompt_user="summarize failed provider run",
            execution_adapter="openclaw",
            vault_root=vault,
            task_class="summarize_failure",
        )

        assert result.text == "failure summary"
        assert result.model_id == "phi4-mini:latest"
        assert result.fallback_used is True
        assert calls == ["gpt-5.5", "phi4-mini:latest"]
        events = load_provider_audit_events(vault)
        assert any(event["event_type"] == "primary_rate_limited" for event in events)
        assert any(event["event_type"] == "primary_entered_cooldown" for event in events)
    finally:
        _cleanup_vault(vault)


def test_runtime_status_human_output_includes_provider_sections_and_does_not_mutate_state(capsys) -> None:
    vault = _make_vault()
    try:
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        queue_path = vault / "runtime" / "providers" / "state" / "provider_queue.json"
        assert cli.main(["runtime", "status", "--vault-root", str(vault)]) == 0
        output = capsys.readouterr().out
        assert "Primary provider:" in output
        assert "Fallback providers:" in output
        assert not state_path.exists()
        assert not queue_path.exists()
        assert audit_path(vault).exists()
    finally:
        _cleanup_vault(vault)


def test_weak_provider_is_denied_for_high_authority_tasks() -> None:
    vault = _make_vault()
    try:
        _cool_down_primary(vault)
        for task_class in [
            "repo_development",
            "architecture_change",
            "yaml_registry_update",
            "multi_file_patch",
            "security_policy_change",
            "runtime_config_change",
        ]:
            decision = route_task(
                vault,
                task_class=task_class,
                original_request=f"do {task_class}",
                runtime="openclaw",
                related_adapter="openclaw",
                source_command="test",
            )
            assert decision.allowed is False
            assert decision.route == "queue"
            assert decision.queue_item_id
            assert decision.fallback_denied_reason == "weak_fallback_denied_for_high_authority_task"

        assert len(load_queue_items(vault)) == 6
        assert all(item.files_modified is False for item in load_queue_items(vault))
    finally:
        _cleanup_vault(vault)


def test_weak_provider_is_allowed_for_weak_safe_tasks() -> None:
    vault = _make_vault()
    try:
        _cool_down_primary(vault)
        for task_class in ["summarize_failure", "prompt_compression", "queue_item_creation"]:
            decision = route_task(
                vault,
                task_class=task_class,
                original_request=f"do {task_class}",
                runtime="openclaw",
                related_adapter="openclaw",
                source_command="test",
            )
            assert decision.allowed is True
            assert decision.route == "fallback"
            assert decision.provider_strength == "weak"
            assert decision.sticky_for_development is False
    finally:
        _cleanup_vault(vault)


def test_primary_rate_limit_queues_high_complexity_work_and_cli_can_inspect_queue(capsys) -> None:
    vault = _make_vault()
    try:
        _cool_down_primary(vault)
        decision = route_task(
            vault,
            task_class="repo_development",
            original_request="Implement a runtime provider patch",
            runtime="openclaw",
            related_adapter="openclaw",
            required_context_files=["runtime/providers/governance_layer.py"],
            source_command="test",
        )

        assert decision.allowed is False
        assert decision.queue_item_id
        assert cli.main(["runtime", "queue", "list", "--vault-root", str(vault), "--json"]) == 0
        queue_payload = _json_result(capsys.readouterr().out)
        assert queue_payload["queued_task_count"] == 1
        assert queue_payload["high_complexity_waiting_for_primary"] == 1

        assert cli.main(["runtime", "queue", "show", decision.queue_item_id, "--vault-root", str(vault), "--json"]) == 0
        queue_item = _json_result(capsys.readouterr().out)
        assert queue_item["task_id"] == decision.queue_item_id
        assert queue_item["task_class"] == "repo_development"
        assert queue_item["files_modified"] is False
    finally:
        _cleanup_vault(vault)


def test_fallback_timeout_policy_and_no_chunk_unhealthy_state() -> None:
    vault = _make_vault()
    try:
        assert evaluate_fallback_timeout(chunks_received=0, total_elapsed_sec=31) == "fallback_timeout_first_token"
        assert evaluate_fallback_timeout(chunks_received=0, total_elapsed_sec=61) == "fallback_timeout_no_chunks"
        assert evaluate_fallback_timeout(chunks_received=1, total_elapsed_sec=181) == "fallback_timeout_wall_time"

        result = record_fallback_timeout(
            vault,
            provider_id="local_oss",
            model="phi4-mini:latest",
            task_class="summarize_failure",
            timeout_event_type="fallback_timeout_no_chunks",
            runtime="openclaw",
            source_command="test",
        )
        assert result["provider"]["state"] == "unhealthy"
        assert result["fallback_marked_unhealthy_event"]["event_type"] == "fallback_marked_unhealthy"

        records = load_provider_records(vault)
        fallback = next(record for record in records.values() if record.is_fallback)
        assert fallback.state == "unhealthy"
        assert fallback.last_no_chunk_timeout_at is not None
    finally:
        _cleanup_vault(vault)


def test_fallback_timeout_proof_no_chunks_marks_fallback_unhealthy_without_provider_call() -> None:
    vault = _make_vault()
    try:
        payload = run_fallback_timeout_proof(
            vault,
            scenario="no-chunks",
            runtime="openclaw",
            source_command="test",
        )
        assert payload["proof_type"] == "simulated_local_fallback_timeout"
        assert payload["timeout_event_type"] == "fallback_timeout_no_chunks"
        assert payload["fallback_marked_unhealthy"] is True
        assert payload["simulated_stream"] is True
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert payload["wall_clock_wait_performed"] is False
        assert payload["provider_state_mutated"] is True
        assert payload["queue_drained"] is False
        assert payload["gateway_mutated"] is False
        assert payload["provider_state_after"]["state"] == "unhealthy"
        assert payload["provider_state_after"]["last_error_type"] == "no_chunk_timeout"
        assert payload["provider_state_after"]["last_no_chunk_timeout_at"] is not None
        assert payload["provider_state_after"]["sticky_for_development"] is False

        fallback = [
            record
            for record in load_provider_records(vault).values()
            if record.is_fallback and record.runtime == "openclaw"
        ][0]
        assert fallback.state == "unhealthy"
        assert fallback.last_error_type == "no_chunk_timeout"
        assert fallback.last_no_chunk_timeout_at is not None
        assert fallback.sticky_for_development is False

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "fallback_timeout_proof_requested" in event_types
        assert "fallback_timeout_no_chunks" in event_types
        assert "fallback_marked_unhealthy" in event_types
    finally:
        _cleanup_vault(vault)


def test_fallback_timeout_proof_does_not_mark_unmatched_configured_fallback_unhealthy() -> None:
    vault = _make_vault()
    try:
        _write_text(
            vault / "runtime" / "openclaw" / "model_config.yaml",
            "\n".join(
                [
                    "runtime: openclaw",
                    "primary:",
                    "  model_id: gpt-5.5",
                    "  max_tokens: 8192",
                    "  temperature: 0.2",
                    "fallbacks:",
                    "  - model_id: claude-haiku-4-5-20251001",
                    "    max_tokens: 2048",
                    "    temperature: 0.2",
                ]
            )
            + "\n",
        )
        payload = run_fallback_timeout_proof(
            vault,
            scenario="no-chunks",
            runtime="openclaw",
            provider_id="local_oss",
            model="phi4-mini:latest",
            source_command="test",
        )
        assert payload["provider_id"] == "local_oss"
        assert payload["model"] == "phi4-mini:latest"
        assert payload["provider_state_after"]["state"] == "unhealthy"

        records = load_provider_records(vault)
        configured_fallback = [
            record
            for record in records.values()
            if record.is_fallback and record.runtime == "openclaw" and record.provider_id == "claude"
        ][0]
        assert configured_fallback.state == "unknown"
        assert configured_fallback.last_error_type is None
    finally:
        _cleanup_vault(vault)


def test_fallback_timeout_proof_first_token_aborts_without_marking_unhealthy() -> None:
    vault = _make_vault()
    try:
        payload = run_fallback_timeout_proof(
            vault,
            scenario="first-token",
            runtime="openclaw",
            source_command="test",
        )
        assert payload["timeout_event_type"] == "fallback_timeout_first_token"
        assert payload["fallback_marked_unhealthy"] is False
        assert payload["simulated_stream"] is True
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert payload["wall_clock_wait_performed"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["queue_drained"] is False
        assert payload["gateway_mutated"] is False

        fallback = [
            record
            for record in load_provider_records(vault).values()
            if record.is_fallback and record.runtime == "openclaw"
        ][0]
        assert fallback.state == "unknown"
        assert fallback.last_error_type is None
        assert fallback.sticky_for_development is False
    finally:
        _cleanup_vault(vault)


def test_fallback_timeout_proof_cli_runs_no_chunk_proof_and_rejects_live_flags(capsys) -> None:
    vault = _make_vault()
    try:
        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "fallback-timeout-proof",
                    "no-chunks",
                    "--runtime",
                    "openclaw",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["timeout_event_type"] == "fallback_timeout_no_chunks"
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert payload["fallback_marked_unhealthy"] is True

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "fallback-timeout-proof",
                    "no-chunks",
                    "--runtime",
                    "openclaw",
                    "--vault-root",
                    str(vault),
                    "--execute-live-probe",
                    "--json",
                ]
            )
            == 1
        )
        capsys.readouterr()
    finally:
        _cleanup_vault(vault)


def test_ollama_timeout_contract_success_uses_injected_stream_without_provider_call() -> None:
    vault = _make_vault()
    try:
        payload = run_ollama_timeout_contract(
            vault,
            scenario="success",
            runtime="openclaw",
            source_command="test",
        )
        result = payload["result"]
        assert payload["proof_type"] == "local_ollama_stream_timeout_contract"
        assert payload["simulated_stream"] is True
        assert payload["wall_clock_wait_performed"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert payload["request_payload"]["stream"] is True
        assert payload["request_payload"]["options"]["num_ctx"] == 16384
        assert result["ok"] is True
        assert result["content"] == "Recovered summary."
        assert result["chunks_received"] == 2
        assert result["provider_state_mutated"] is False
        assert result["queue_drained"] is False
        assert result["gateway_mutated"] is False
        assert result["files_modified"] is False

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "fallback_attempt_started" in event_types
        assert "provider_state_updated" in event_types
    finally:
        _cleanup_vault(vault)


def test_ollama_timeout_contract_first_token_aborts_without_unhealthy_state() -> None:
    vault = _make_vault()
    try:
        payload = run_ollama_timeout_contract(
            vault,
            scenario="first-token",
            runtime="openclaw",
            source_command="test",
        )
        result = payload["result"]
        assert result["ok"] is False
        assert result["timeout_event_type"] == "fallback_timeout_first_token"
        assert result["provider_state_mutated"] is False
        assert result["files_modified"] is False

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "fallback_timeout_first_token" in event_types
        assert "fallback_marked_unhealthy" not in event_types
    finally:
        _cleanup_vault(vault)


def test_ollama_timeout_contract_no_chunks_marks_fallback_unhealthy() -> None:
    vault = _make_vault()
    try:
        payload = run_ollama_timeout_contract(
            vault,
            scenario="no-chunks",
            runtime="openclaw",
            source_command="test",
        )
        result = payload["result"]
        assert result["ok"] is False
        assert result["timeout_event_type"] == "fallback_timeout_no_chunks"
        assert result["provider_state_mutated"] is True
        assert result["files_modified"] is True

        fallback = [
            record
            for record in load_provider_records(vault).values()
            if record.is_fallback and record.runtime == "openclaw"
        ][0]
        assert fallback.state == "unhealthy"
        assert fallback.last_error_type == "no_chunk_timeout"
        assert fallback.sticky_for_development is False

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "fallback_timeout_no_chunks" in event_types
        assert "fallback_marked_unhealthy" in event_types
    finally:
        _cleanup_vault(vault)


def test_ollama_timeout_contract_wall_time_aborts_without_provider_call() -> None:
    vault = _make_vault()
    try:
        payload = run_ollama_timeout_contract(
            vault,
            scenario="wall-time",
            runtime="openclaw",
            source_command="test",
        )
        result = payload["result"]
        assert result["ok"] is False
        assert result["timeout_event_type"] == "fallback_timeout_wall_time"
        assert result["content"] == "Partial"
        assert result["live_network_call_attempted"] is False
        assert result["provider_state_mutated"] is False
        assert result["fallback_sticky_for_development"] is False
    finally:
        _cleanup_vault(vault)


def test_ollama_timeout_contract_denies_high_authority_task_before_stream() -> None:
    vault = _make_vault()
    try:
        stream_called = False

        def runner(_: dict[str, object]):
            nonlocal stream_called
            stream_called = True
            return iter([{"elapsed_sec": 1, "content": "unsafe", "done": True}])

        result = execute_local_ollama_fallback_stream(
            vault,
            prompt="Patch the runtime.",
            task_class="repo_development",
            runtime="openclaw",
            stream_runner=runner,
            source_command="test",
        )
        assert result["ok"] is False
        assert result["reason"] == "task_not_allowed_for_local_ollama_fallback"
        assert result["live_network_call_attempted"] is False
        assert result["provider_state_mutated"] is False
        assert stream_called is False

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "fallback_denied_by_capability" in event_types
    finally:
        _cleanup_vault(vault)


def test_ollama_timeout_contract_cli_runs_injected_scenario_and_rejects_live_flags(capsys) -> None:
    vault = _make_vault()
    try:
        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "ollama-timeout-contract",
                    "success",
                    "--runtime",
                    "openclaw",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["proof_type"] == "local_ollama_stream_timeout_contract"
        assert payload["result"]["ok"] is True
        assert payload["result"]["content"] == "Recovered summary."
        assert payload["result"]["live_network_call_attempted"] is False
        assert payload["result"]["secret_value_read"] is False
        assert payload["request_payload"]["options"]["num_ctx"] == 16384

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "ollama-timeout-contract",
                    "success",
                    "--runtime",
                    "openclaw",
                    "--vault-root",
                    str(vault),
                    "--execute-live-probe",
                    "--json",
                ]
            )
            == 1
        )
        capsys.readouterr()
    finally:
        _cleanup_vault(vault)


def test_primary_cooldown_expiry_recovers_and_routes_high_authority_to_primary() -> None:
    vault = _make_vault()
    try:
        mark_primary_rate_limited(
            vault,
            provider_id="openai",
            model="gpt-5.5",
            runtime="openclaw",
            cooldown_until="2000-01-01T00:00:00Z",
            reason="rate_limit",
            source_command="test",
        )

        decision = route_task(
            vault,
            task_class="repo_development",
            original_request="retry serious work",
            runtime="openclaw",
            related_adapter="openclaw",
            source_command="test",
        )
        assert decision.allowed is True
        assert decision.route == "primary"
        assert decision.provider_id == "openai"

        primary = next(record for record in load_provider_records(vault).values() if record.is_primary)
        assert primary.state == "healthy"
        assert primary.cooldown_until is None
        assert primary.last_recovered_at is not None
        assert primary.sticky_for_development is False
        assert "primary_recovered" in {event["event_type"] for event in load_provider_audit_events(vault)}
    finally:
        _cleanup_vault(vault)


def test_recovery_dry_run_is_bounded_and_audit_events_are_emitted() -> None:
    vault = _make_vault()
    try:
        _cool_down_primary(vault)
        route_task(
            vault,
            task_class="repo_development",
            original_request="blocked serious work",
            runtime="openclaw",
            related_adapter="openclaw",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        state_before = state_path.read_text(encoding="utf-8")

        payload = run_recovery_dry_run(vault)
        state_after = state_path.read_text(encoding="utf-8")

        assert payload["dry_run"] is True
        assert payload["provider_state_mutated"] is False
        assert payload["canonical_files_mutated"] is False
        assert state_before == state_after

        event_types = {event["event_type"] for event in load_provider_audit_events(vault)}
        assert {
            "primary_rate_limited",
            "fallback_denied_by_capability",
            "queue_item_created",
            "task_queued_for_primary_retry",
            "scheduled_recovery_dry_run_started",
            "scheduled_recovery_dry_run_completed",
        }.issubset(event_types)
    finally:
        _cleanup_vault(vault)


def test_queue_retry_dry_run_builds_retry_package_without_mutating_queue_or_state() -> None:
    vault = _make_vault()
    try:
        _cool_down_primary(vault)
        route_task(
            vault,
            task_class="repo_development",
            original_request="blocked serious work",
            runtime="openclaw",
            related_adapter="openclaw",
            source_command="test",
        )
        item = load_queue_items(vault)[0]
        queue_path = vault / "runtime" / "providers" / "state" / "provider_queue.json"
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        queue_before = queue_path.read_text(encoding="utf-8")
        state_before = state_path.read_text(encoding="utf-8")

        payload = retry_queue_item_dry_run(vault, item.task_id, source_command="test")

        assert payload["ok"] is True
        assert payload["dry_run"] is True
        assert payload["ready_for_retry"] is False
        assert payload["files_modified"] is False
        assert payload["queue_state_mutated"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["canonical_files_mutated"] is False
        assert payload["queue_drained"] is False
        assert payload["live_provider_call_attempted"] is False
        assert payload["secret_value_read"] is False
        package = payload["retry_package"]
        assert package["proof_type"] == "queue_retry_package_dry_run"
        assert package["original_request"] == "blocked serious work"
        assert package["task_class"] == "repo_development"
        assert package["fallback_used"] is False
        assert package["fallback_sticky_for_development"] is False
        assert "primary_provider_not_eligible" in package["blocked_reasons"]
        assert "drain_high_complexity_queue" in package["denied_actions"]
        assert queue_path.read_text(encoding="utf-8") == queue_before
        assert state_path.read_text(encoding="utf-8") == state_before
    finally:
        _cleanup_vault(vault)


def test_queue_retry_dry_run_ready_after_primary_probe_without_draining_queue() -> None:
    vault = _make_vault()
    try:
        _cool_down_primary(vault)
        route_task(
            vault,
            task_class="repo_development",
            original_request="retry after primary recovery",
            runtime="openclaw",
            related_adapter="openclaw",
            source_command="test",
        )
        item = load_queue_items(vault)[0]
        probe_provider(vault, target="primary", runtime="openclaw", source_command="test")
        queue_path = vault / "runtime" / "providers" / "state" / "provider_queue.json"
        queue_before = queue_path.read_text(encoding="utf-8")

        payload = retry_queue_item_dry_run(vault, item.task_id, source_command="test")

        assert payload["ready_for_retry"] is True
        package = payload["retry_package"]
        assert package["retry_ready"] is True
        assert package["retry_package_status"] == "ready_for_retry"
        assert package["would_route_to"] == "primary"
        assert package["would_update_queue_status"] == "ready_for_retry"
        assert package["would_increment_retry_attempts"] is False
        assert package["queue_state_mutated"] is False
        assert package["queue_drained"] is False
        assert package["live_provider_call_attempted"] is False
        assert queue_path.read_text(encoding="utf-8") == queue_before
    finally:
        _cleanup_vault(vault)


def test_recovery_dry_run_includes_retry_packages_without_queue_drain() -> None:
    vault = _make_vault()
    try:
        _cool_down_primary(vault)
        route_task(
            vault,
            task_class="repo_development",
            original_request="recover package serious work",
            runtime="openclaw",
            related_adapter="openclaw",
            source_command="test",
        )
        item = load_queue_items(vault)[0]
        probe_provider(vault, target="primary", runtime="openclaw", source_command="test")
        queue_path = vault / "runtime" / "providers" / "state" / "provider_queue.json"
        queue_before = queue_path.read_text(encoding="utf-8")

        payload = run_recovery_dry_run(vault)

        assert payload["dry_run"] is True
        assert payload["queue_state_mutated"] is False
        assert payload["queue_drained"] is False
        assert payload["live_provider_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert len(payload["retry_packages"]) == 1
        package = payload["retry_packages"][0]
        assert package["task_id"] == item.task_id
        assert package["retry_ready"] is True
        assert package["original_request"] == "recover package serious work"
        assert package["files_modified"] is False
        assert queue_path.read_text(encoding="utf-8") == queue_before
    finally:
        _cleanup_vault(vault)


def test_queue_retry_cli_dry_run_reports_retry_package_and_rejects_live_retry(capsys) -> None:
    vault = _make_vault()
    try:
        _cool_down_primary(vault)
        route_task(
            vault,
            task_class="repo_development",
            original_request="cli retry package",
            runtime="openclaw",
            related_adapter="openclaw",
            source_command="test",
        )
        item = load_queue_items(vault)[0]

        assert (
            cli.main(
                [
                    "runtime",
                    "queue",
                    "retry",
                    item.task_id,
                    "--dry-run",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        output = json.loads(capsys.readouterr().out)
        result = output["result"]
        assert result["retry_package"]["proof_type"] == "queue_retry_package_dry_run"
        assert result["retry_package"]["queue_drained"] is False

        assert (
            cli.main(
                [
                    "runtime",
                    "queue",
                    "retry",
                    item.task_id,
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 1
        )
        capsys.readouterr()
    finally:
        _cleanup_vault(vault)


def test_network_dry_run_probe_reads_no_secret_and_does_not_mutate_provider_state() -> None:
    vault = _make_vault()
    try:
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        assert not state_path.exists()

        payload = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="network-dry-run",
            source_command="test",
        )

        assert payload["ok"] is True
        assert payload["probe_mode"] == "network-dry-run"
        assert payload["provider_state_mutated"] is False
        assert payload["canonical_files_mutated"] is False
        assert payload["probe_plan"]["live_network_call_attempted"] is False
        assert payload["probe_plan"]["secret_value_read"] is False
        assert not state_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "primary_probe_started" in event_types
        assert "provider_state_updated" in event_types
    finally:
        _cleanup_vault(vault)


def test_recovery_dry_run_includes_network_probe_plans_without_state_mutation() -> None:
    vault = _make_vault()
    try:
        mark_primary_rate_limited(
            vault,
            provider_id="openai",
            model="gpt-5.5",
            runtime="openclaw",
            cooldown_until="2000-01-01T00:00:00Z",
            reason="rate_limit",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        state_before = state_path.read_text(encoding="utf-8")

        payload = run_recovery_dry_run(vault)
        state_after = state_path.read_text(encoding="utf-8")

        assert payload["provider_state_mutated"] is False
        assert state_before == state_after
        assert len(payload["provider_probe_plans"]) == 1
        plan = payload["provider_probe_plans"][0]
        assert plan["probe_mode"] == "network-dry-run"
        assert plan["live_network_call_attempted"] is False
        assert plan["secret_value_read"] is False
    finally:
        _cleanup_vault(vault)


def test_provider_probe_cli_supports_network_dry_run_mode(capsys) -> None:
    vault = _make_vault()
    try:
        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "probe",
                    "primary",
                    "--probe-mode",
                    "network-dry-run",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["probe_mode"] == "network-dry-run"
        assert payload["provider_state_mutated"] is False
        assert payload["probe_plan"]["live_network_call_attempted"] is False
        assert payload["probe_plan"]["secret_value_read"] is False
    finally:
        _cleanup_vault(vault)


def test_gate_live_provider_probe_operation_has_denied_approval_schema() -> None:
    schema = get_runtime_operation_approval_schema(
        RUNTIME_PROVIDER_LIVE_PROBE_OPERATION,
        provider_id="openai",
        model="gpt-5.5",
        runtime="openclaw",
        external_api="provider.openai",
        source_command="test",
    )

    assert schema is not None
    assert schema["approval_schema_id"] == RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID
    assert schema["operation"] == RUNTIME_PROVIDER_LIVE_PROBE_OPERATION
    assert schema["approval_request_written"] is False
    assert schema["live_network_call_attempted"] is False
    assert schema["secret_value_read"] is False
    assert schema["provider_state_mutated"] is False
    assert schema["approval_request_template"]["credential_values_allowed"] is False

    allowed, reason = check_runtime_operation(
        RUNTIME_PROVIDER_LIVE_PROBE_OPERATION,
        external_api="provider.openai",
        write_targets=[
            "runtime/providers/state/provider_state.json",
            "runtime/providers/state/provider_audit.jsonl",
        ],
    )
    assert allowed is False
    assert RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID in reason


def test_live_probe_preflight_is_denied_by_default_without_network_or_state_mutation() -> None:
    vault = _make_vault()
    try:
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        assert not state_path.exists()

        payload = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            source_command="test",
        )

        assert payload["ok"] is True
        assert payload["probe_mode"] == "live-preflight"
        assert payload["provider_state_mutated"] is False
        assert payload["canonical_files_mutated"] is False
        assert payload["live_probe_allowed"] is False
        assert payload["probe_plan"]["live_network_call_attempted"] is False

        preflight = payload["live_probe_preflight"]
        assert preflight["gate_operation"] == RUNTIME_PROVIDER_LIVE_PROBE_OPERATION
        assert preflight["gate_approval_schema_id"] == RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID
        assert preflight["gate_policy_allowed"] is False
        assert RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID in preflight["gate_policy_reason"]
        assert preflight["external_api_id"] == "provider.openai"
        assert preflight["live_probe_allowed"] is False
        assert preflight["approval_required"] is True
        assert preflight["approval_status"] == "missing"
        assert preflight["approval_request_written"] is False
        assert preflight["approval_request_template"]["provider_id"] == "openai"
        assert preflight["approval_request_template"]["credential_values_allowed"] is False
        assert preflight["live_network_call_attempted"] is False
        assert preflight["secret_value_read"] is False
        assert preflight["provider_state_mutated"] is False
        assert preflight["queue_mutated"] is False
        assert "gate_approval_id" in preflight["required_approval_fields"]
        assert "external_api_id" in preflight["required_approval_fields"]
        assert not state_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_probe_preflight_started" in event_types
        assert "provider_live_probe_gate_approval_schema_built" in event_types
        assert "provider_live_probe_preflight_denied" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_probe_cli_supports_live_preflight_without_external_effects(capsys) -> None:
    vault = _make_vault()
    try:
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "probe",
                    "primary",
                    "--probe-mode",
                    "live-preflight",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["probe_mode"] == "live-preflight"
        assert payload["provider_state_mutated"] is False
        assert payload["live_probe_preflight"]["live_probe_allowed"] is False
        assert payload["live_probe_preflight"]["gate_operation"] == RUNTIME_PROVIDER_LIVE_PROBE_OPERATION
        assert payload["live_probe_preflight"]["gate_policy_allowed"] is False
        assert payload["live_probe_preflight"]["approval_request_written"] is False
        assert payload["live_probe_preflight"]["live_network_call_attempted"] is False
        assert payload["live_probe_preflight"]["secret_value_read"] is False
        assert not state_path.exists()
    finally:
        _cleanup_vault(vault)


def test_live_probe_preflight_can_write_pending_approval_artifact_without_execution() -> None:
    vault = _make_vault()
    try:
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        payload = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )

        assert payload["ok"] is True
        assert payload["files_modified"] is True
        assert payload["provider_state_mutated"] is False
        assert payload["live_probe_allowed"] is False
        assert payload["live_probe_preflight"]["approval_request_written"] is True
        assert payload["live_probe_preflight"]["approval_status"] == "pending"
        assert payload["live_probe_preflight"]["live_network_call_attempted"] is False
        assert payload["approval_artifact"]["requested_by"] == "Codex"
        assert payload["approval_artifact"]["operator_request_id"].startswith("rpgl-live-probe-req-")
        assert payload["approval_artifact"]["credential_values_allowed"] is False
        assert payload["approval_artifact"]["live_network_call_attempted"] is False
        assert payload["approval_artifact"]["provider_state_mutated"] is False
        assert payload["approval_artifact"]["approval_ref"].startswith(str(vault / APPROVAL_RELATIVE_DIR))
        assert Path(payload["approval_artifact"]["approval_ref"]).exists()
        assert not state_path.exists()

        loaded = load_live_probe_approval_request(vault, payload["approval_artifact"]["gate_approval_id"])
        assert loaded["status"] == "pending"
        assert loaded["provider_id"] == "openai"
        assert loaded["model"] == "gpt-5.5"
        assert "gpt-5.5" in Path(loaded["approval_ref"]).read_text(encoding="utf-8")

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_probe_approval_request_created" in event_types
    finally:
        _cleanup_vault(vault)


def test_live_probe_target_approval_plan_uses_active_target_profile_without_writes() -> None:
    vault = _make_vault()
    try:
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        approval_dir = vault / APPROVAL_RELATIVE_DIR

        payload = build_live_probe_target_approval_plan(
            vault,
            target="all",
            runtime="unknown",
            source_command="test",
        )

        assert payload["plan_status"] == "ready_to_write_approval_requests"
        assert payload["active_target_primary_model"] == "gpt-5.5"
        assert payload["target_profile_exists"] is False
        assert payload["approval_requests_needed"] == 1
        assert payload["approval_request_written"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert payload["provider_state_mutated"] is False
        assert not approval_dir.exists()
        assert not state_path.exists()

        primary = next(item for item in payload["candidates"] if item["target"] == "primary")
        assert primary["candidate_status"] == "ready_for_approval_request"
        assert primary["provider"]["provider_id"] == "openai"
        assert primary["provider"]["model"] == "gpt-5.5"
        assert primary["external_api_id"] == "provider.openai"
        assert primary["approval_request_template"]["provider_id"] == "openai"

        fallback = next(item for item in payload["candidates"] if item["target"] == "fallback")
        assert fallback["candidate_status"] == "blocked"
        assert fallback["provider"]["provider_id"] == "local_oss"
        assert fallback["provider"]["model"] == "phi4-mini:latest"
        assert "local_fallback_target_disabled_or_unconfigured" in fallback["blocked_reasons"]
    finally:
        _cleanup_vault(vault)


def test_live_probe_target_approval_plan_supports_non_openai_target_profile() -> None:
    vault = _make_vault()
    try:
        _write_text(
            vault / PROVIDER_TARGET_PROFILE_RELATIVE_PATH,
            json.dumps(
                {
                    "schema_version": "1.0",
                    "profile_schema_id": "rpgl.provider_target_profile.v1",
                    "default_primary_model": "claude-sonnet-4-6",
                    "runtime_targets": {
                        "openclaw": {
                            "primary_model": "claude-sonnet-4-6",
                            "fallback_models": ["claude-haiku-4-5-20251001"],
                            "fallback_enforcement": "observe_only",
                        }
                    },
                    "provider_setup_targets": {
                        "claude": {"default_model": "claude-sonnet-4-6"}
                    },
                    "local_fallback": {
                        "provider_id": "local_oss",
                        "model": "phi4-mini:latest",
                        "strength": "weak",
                        "enabled": False,
                        "num_ctx": 16384,
                        "authority": "recovery_assistant_only",
                    },
                },
                indent=2,
            )
            + "\n",
        )

        payload = build_live_probe_target_approval_plan(
            vault,
            target="primary",
            runtime="unknown",
            source_command="test",
        )

        assert payload["active_target_primary_model"] == "claude-sonnet-4-6"
        assert payload["target_profile_exists"] is True
        primary = payload["candidates"][0]
        assert primary["target"] == "primary"
        assert primary["candidate_status"] == "ready_for_approval_request"
        assert primary["provider"]["provider_id"] == "claude"
        assert primary["provider"]["model"] == "claude-sonnet-4-6"
        assert primary["external_api_id"] == "provider.anthropic"
        assert primary["approval_request_template"]["provider_id"] == "claude"
    finally:
        _cleanup_vault(vault)


def test_live_probe_target_approval_request_writer_creates_only_pending_matching_request() -> None:
    vault = _make_vault()
    try:
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        profile_path = vault / PROVIDER_TARGET_PROFILE_RELATIVE_PATH

        payload = write_live_probe_target_approval_requests(
            vault,
            target="primary",
            runtime="unknown",
            requested_by="test-operator",
            source_command="test",
        )

        assert payload["approval_request_written"] is True
        assert payload["approval_requests_written_count"] == 1
        assert payload["provider_state_mutated"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert not state_path.exists()
        assert not profile_path.exists()

        written = payload["approval_requests_written"][0]
        assert written["provider_id"] == "openai"
        assert written["model"] == "gpt-5.5"
        assert written["runtime"] == "unknown"
        assert written["status"] == "pending"
        assert written["requested_by"] == "test-operator"
        assert Path(written["approval_ref"]).exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_probe_target_approval_plan_requested" in event_types
        assert "provider_live_probe_approval_request_created" in event_types
        assert "provider_live_probe_target_approval_request_created" in event_types
    finally:
        _cleanup_vault(vault)


def test_live_probe_decision_preflight_uses_target_profile_approval_over_stale_state() -> None:
    vault = _make_vault()
    try:
        rpgl._save_provider_records(
            vault,
            {
                "hermes:primary:claude:claude-opus-4-7": rpgl.ProviderStatusRecord(
                    provider_key="hermes:primary:claude:claude-opus-4-7",
                    provider_id="claude",
                    provider_name="Anthropic Claude",
                    model="claude-opus-4-7",
                    strength="strong",
                    runtime="hermes",
                    role="primary",
                    is_primary=True,
                    active_for_task_classes=rpgl.allowed_task_classes_for_strength("strong"),
                    denied_task_classes=[],
                )
            },
        )
        request = write_live_probe_target_approval_requests(
            vault,
            target="primary",
            runtime="unknown",
            requested_by="test-operator",
            source_command="test",
        )
        gate_approval_id = request["approval_requests_written"][0]["gate_approval_id"]
        write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="test-operator",
            source_command="test",
        )

        payload = build_live_probe_decision_preflight(
            vault,
            target="primary",
            runtime="unknown",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )

        assert payload["provider"]["provider_id"] == "openai"
        assert payload["provider"]["model"] == "gpt-5.5"
        assert payload["approval_validation"]["structurally_valid"] is True
        assert payload["decision_validation"]["decision_record_consumable"] is True
        assert "approval_artifact_invalid" not in payload["blocked_reasons"]
        assert payload["live_network_call_attempted"] is False
    finally:
        _cleanup_vault(vault)


def test_live_probe_target_approval_plan_cli_and_guard_flags(capsys) -> None:
    vault = _make_vault()
    try:
        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-target-approval-plan",
                    "primary",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["active_target_primary_model"] == "gpt-5.5"
        assert payload["candidates"][0]["provider"]["provider_id"] == "openai"
        assert payload["approval_request_written"] is False
        assert payload["live_network_call_attempted"] is False

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-target-approval-plan",
                    "primary",
                    "--vault-root",
                    str(vault),
                    "--execute-live-probe",
                ]
            )
            == 1
        )
    finally:
        _cleanup_vault(vault)


def test_live_probe_preflight_validates_existing_approval_artifact_without_execution() -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        payload = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )

        validation = payload["approval_validation"]
        assert validation["structurally_valid"] is True
        assert validation["matches_preflight"] is True
        assert validation["approval_status"] == "pending"
        assert validation["live_probe_execution_allowed"] is False
        assert payload["live_probe_allowed"] is False
        assert payload["live_probe_preflight"]["approval_validation"]["live_network_call_attempted"] is False
        assert payload["live_probe_preflight"]["secret_value_read"] is False
        assert not state_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_probe_approval_request_validated" in event_types
    finally:
        _cleanup_vault(vault)


def test_live_probe_approval_decision_record_preview_and_write_are_non_executing() -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]

        preview = build_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            reason="unit-test approval",
            source_command="test",
        )
        assert preview["decision_record_writable"] is True
        assert preview["decision_record_written"] is False
        assert preview["live_probe_execution_allowed"] is False
        assert preview["live_network_call_attempted"] is False
        assert preview["secret_value_read"] is False
        assert load_live_probe_decision_records(vault, gate_approval_id=gate_approval_id) == []

        written = write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            reason="unit-test approval",
            source_command="test",
        )
        assert written["decision_record_written"] is True
        assert written["files_modified"] is True
        assert Path(written["decision_ref"]).exists()
        assert written["live_probe_execution_allowed"] is False
        assert written["provider_state_mutated"] is False
        assert written["live_network_call_attempted"] is False

        validation = validate_live_probe_decision_records(vault, gate_approval_id=gate_approval_id)
        assert validation["structurally_valid"] is True
        assert validation["decision_record_consumable"] is True
        assert validation["decision"] == "approved"

        events = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_probe_approval_decision_previewed" in events
        assert "provider_live_probe_approval_decision_created" in events
        assert "provider_live_probe_decision_record_validated" in events
    finally:
        _cleanup_vault(vault)


def test_live_probe_approval_decision_record_is_immutable_per_gate_approval_id() -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            source_command="test",
        )
        with pytest.raises(RuntimeProviderGovernanceError) as exc_info:
            write_live_probe_approval_decision_record(
                vault,
                gate_approval_id,
                decision="denied",
                decided_by="operator",
                source_command="test",
            )
        assert "immutable_decision_already_exists" in str(exc_info.value)
    finally:
        _cleanup_vault(vault)


def test_live_probe_executor_spec_reports_immutable_decision_precondition() -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        missing = build_live_probe_executor_spec(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        decision_precondition = next(
            item for item in missing["preconditions"] if item["id"] == "approved_immutable_decision_record_present"
        )
        assert decision_precondition["passed"] is False
        assert missing["decision_validation"]["status"] == "missing"

        write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            source_command="test",
        )
        present = build_live_probe_executor_spec(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        decision_precondition = next(
            item for item in present["preconditions"] if item["id"] == "approved_immutable_decision_record_present"
        )
        assert decision_precondition["passed"] is True
        assert present["decision_validation"]["decision_record_consumable"] is True
        assert present["live_probe_execution_allowed"] is False
        assert present["live_network_call_attempted"] is False
    finally:
        _cleanup_vault(vault)


def test_live_probe_approval_decision_cli_preview_and_write_are_guarded(capsys) -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-approval-decision",
                    "primary",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--decision",
                    "approved",
                    "--requested-by",
                    "operator",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        preview = _json_result(capsys.readouterr().out)
        assert preview["decision_record_written"] is False
        assert preview["live_probe_execution_allowed"] is False
        assert preview["live_network_call_attempted"] is False
        assert preview["secret_value_read"] is False
        assert load_live_probe_decision_records(vault, gate_approval_id=gate_approval_id) == []

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-approval-decision",
                    "primary",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--decision",
                    "approved",
                    "--write-approval-decision",
                    "--requested-by",
                    "operator",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        written = _json_result(capsys.readouterr().out)
        assert written["decision_record_written"] is True
        assert written["files_modified"] is True
        assert Path(written["decision_ref"]).exists()
        assert written["provider_state_mutated"] is False
        assert written["live_network_call_attempted"] is False
        assert written["secret_value_read"] is False
        assert len(load_live_probe_decision_records(vault, gate_approval_id=gate_approval_id)) == 1
    finally:
        _cleanup_vault(vault)


def test_live_probe_decision_preflight_reports_marker_absent_and_executor_not_built(capsys) -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            source_command="test",
        )

        payload = build_live_probe_decision_preflight(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        assert payload["preflight_status"] == "approved_decision_record_valid_but_executor_not_built"
        assert payload["marker_exists"] is False
        assert payload["idempotency_marker_written"] is False
        assert payload["live_probe_execution_allowed"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["decision_validation"]["decision_record_consumable"] is True
        assert not Path(payload["marker_path"]).exists()

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-decision-preflight",
                    "primary",
                    "--runtime",
                    "openclaw",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        cli_payload = _json_result(capsys.readouterr().out)
        assert cli_payload["preflight_status"] == "approved_decision_record_valid_but_executor_not_built"
        assert cli_payload["marker_exists"] is False
        assert cli_payload["idempotency_marker_written"] is False
        assert cli_payload["live_network_call_attempted"] is False
    finally:
        _cleanup_vault(vault)


def test_live_probe_marker_contract_is_non_writing(capsys) -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            source_command="test",
        )

        payload = build_live_probe_marker_contract(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        assert payload["writer_status"] == "not_built"
        assert payload["marker_exists"] is False
        assert payload["idempotency_marker_written"] is False
        assert payload["files_modified"] is False
        assert payload["marker_payload_preview"]["marker_written"] is False
        assert payload["marker_payload_preview"]["selected_decision_id"]
        assert not Path(payload["marker_path"]).exists()

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-marker-contract",
                    "primary",
                    "--runtime",
                    "openclaw",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        cli_payload = _json_result(capsys.readouterr().out)
        assert cli_payload["writer_status"] == "not_built"
        assert cli_payload["marker_exists"] is False
        assert cli_payload["idempotency_marker_written"] is False
        assert not Path(cli_payload["marker_path"]).exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_probe_decision_preflight_requested" in event_types
        assert "provider_live_probe_marker_contract_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_live_probe_decision_consumer_record_and_marker_writer_are_guarded(capsys) -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        decision = write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            source_command="test",
        )

        consumer = write_live_probe_decision_consumer_record(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        assert consumer["decision_consumer_record_written"] is True
        assert consumer["decision_consumed"] is True
        assert consumer["approval_consumed"] is False
        assert consumer["idempotency_marker_written"] is False
        assert consumer["live_probe_execution_allowed"] is False
        assert consumer["live_network_call_attempted"] is False
        assert consumer["provider_state_mutated"] is False
        assert Path(consumer["consumer_record_ref"]).exists()
        loaded_consumer = load_live_probe_decision_consumer_record(vault, gate_approval_id=gate_approval_id)
        assert loaded_consumer is not None
        assert loaded_consumer["selected_decision_id"] == decision["decision_id"]

        marker = write_live_probe_atomic_marker(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        assert marker["idempotency_marker_written"] is True
        assert marker["decision_consumer_record_written"] is True
        assert marker["decision_consumed"] is True
        assert marker["approval_consumed"] is False
        assert marker["live_probe_execution_allowed"] is False
        assert marker["live_network_call_attempted"] is False
        assert marker["provider_state_mutated"] is False
        assert Path(marker["marker_ref"]).exists()
        loaded_marker = load_live_probe_atomic_marker(vault, gate_approval_id=gate_approval_id)
        assert loaded_marker is not None
        assert loaded_marker["selected_decision_id"] == decision["decision_id"]

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-decision-preflight",
                    "primary",
                    "--runtime",
                    "openclaw",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        preflight_after_marker = _json_result(capsys.readouterr().out)
        assert preflight_after_marker["preflight_status"] == "blocked_marker_already_exists"
        assert preflight_after_marker["marker_exists"] is True

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_probe_decision_consumer_record_written" in event_types
        assert "provider_live_probe_atomic_marker_written" in event_types
    finally:
        _cleanup_vault(vault)


def test_live_probe_decision_consumer_cli_requires_explicit_write_flag(capsys) -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            source_command="test",
        )

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-decision-consumer",
                    "primary",
                    "--runtime",
                    "openclaw",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 1
        )
        capsys.readouterr()
        assert load_live_probe_decision_consumer_record(vault, gate_approval_id=gate_approval_id) is None

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-decision-consumer",
                    "primary",
                    "--runtime",
                    "openclaw",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--write-consumer-record",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["decision_consumer_record_written"] is True
        assert payload["live_network_call_attempted"] is False
        assert payload["provider_state_mutated"] is False
    finally:
        _cleanup_vault(vault)


def test_live_probe_atomic_marker_cli_requires_consumer_record_and_write_flag(capsys) -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            source_command="test",
        )

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-atomic-marker-writer",
                    "primary",
                    "--runtime",
                    "openclaw",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--write-consumption-marker",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 1
        )
        capsys.readouterr()
        assert load_live_probe_atomic_marker(vault, gate_approval_id=gate_approval_id) is None

        write_live_probe_decision_consumer_record(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-atomic-marker-writer",
                    "primary",
                    "--runtime",
                    "openclaw",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 1
        )
        capsys.readouterr()
        assert load_live_probe_atomic_marker(vault, gate_approval_id=gate_approval_id) is None

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-atomic-marker-writer",
                    "primary",
                    "--runtime",
                    "openclaw",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--write-consumption-marker",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["idempotency_marker_written"] is True
        assert payload["live_probe_execution_allowed"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["provider_state_mutated"] is False
    finally:
        _cleanup_vault(vault)


def test_live_probe_executor_dry_run_reports_ready_after_marker_without_execution(capsys) -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            source_command="test",
        )
        write_live_probe_decision_consumer_record(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        write_live_probe_atomic_marker(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )

        payload = build_live_probe_executor_dry_run_plan(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        assert payload["readiness_status"] == "ready_for_live_executor_implementation"
        assert payload["executor_status"] == "dry_run_readiness_only"
        assert payload["execution_enabled"] is False
        assert payload["live_probe_execution_allowed"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["queue_mutated"] is False
        assert payload["gateway_mutated"] is False
        assert payload["idempotency_marker_written"] is True
        assert payload["files_modified"] is False
        assert payload["blocked_reasons"] == []

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-executor-dry-run",
                    "primary",
                    "--runtime",
                    "openclaw",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        cli_payload = _json_result(capsys.readouterr().out)
        assert cli_payload["readiness_status"] == "ready_for_live_executor_implementation"
        assert cli_payload["live_network_call_attempted"] is False
        assert cli_payload["provider_state_mutated"] is False
        assert cli_payload["files_modified"] is False

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_probe_smoke_readiness_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_live_probe_executor_dry_run_blocks_without_marker_and_rejects_write_flags(capsys) -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            source_command="test",
        )
        write_live_probe_decision_consumer_record(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )

        payload = build_live_probe_executor_dry_run_plan(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        assert payload["readiness_status"] == "blocked_executor_readiness_preconditions"
        assert "live_probe_idempotency_marker_missing" in "\n".join(payload["blocked_reasons"])
        assert payload["execution_enabled"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["provider_state_mutated"] is False

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-executor-dry-run",
                    "primary",
                    "--runtime",
                    "openclaw",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--write-consumption-marker",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 1
        )
        capsys.readouterr()
        assert load_live_probe_atomic_marker(vault, gate_approval_id=gate_approval_id) is None
    finally:
        _cleanup_vault(vault)


def test_live_probe_smoke_readiness_reports_blockers_without_provider_calls() -> None:
    vault = _make_vault()
    try:
        _write_openai_placeholder_setup_state(vault)
        payload = build_live_probe_smoke_readiness(vault)

        assert payload["readiness_status"] == "blocked"
        assert payload["ready_for_live_smoke"] is False
        assert payload["safe_to_call_update_goal_complete"] is False
        assert payload["no_safe_autonomous_completion_pass_available"] is True
        assert payload["update_goal_allowed"] is False
        assert payload["next_operator_action_id"] == "openai_secret_reference"
        assert payload["next_recommended_pass"] == "operator-provide-openai-secret-reference"
        assert payload["current_secret_reference_target"] == "SET_OPENAI_SECRET_REF"
        assert payload["current_secret_reference_target_is_placeholder"] is True
        assert payload["current_secret_reference_resolvable"] is False
        assert payload["secret_reference_probe_source"] == "env-var-or-local-secret-ref"
        assert payload["secret_reference_probe_error"] == "reference_not_found"
        assert payload["provider_secret_reference"]["secret_reference_probe"]["exists"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["queue_drained"] is False
        assert payload["files_modified"] is False
        assert "no_live_probe_approval_requests_present" in payload["blocked_reasons"]
        assert "live_probe_decision_records_directory_missing" in payload["blocked_reasons"]
        assert any(reason.startswith("primary:") for reason in payload["target_blockers"])

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_probe_smoke_readiness_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_live_probe_smoke_readiness_cli_is_read_only(capsys) -> None:
    vault = _make_vault()
    try:
        _write_openai_placeholder_setup_state(vault)
        assert cli.main([
            "runtime",
            "provider",
            "live-smoke-readiness",
            "--vault-root",
            str(vault),
            "--json",
        ]) == 0
        payload = _json_result(capsys.readouterr().out)

        assert payload["readiness_status"] == "blocked"
        assert payload["ready_for_live_smoke"] is False
        assert payload["safe_to_call_update_goal_complete"] is False
        assert payload["no_safe_autonomous_completion_pass_available"] is True
        assert payload["update_goal_allowed"] is False
        assert payload["next_operator_action_id"] == "openai_secret_reference"
        assert payload["next_recommended_pass"] == "operator-provide-openai-secret-reference"
        assert payload["current_secret_reference_target"] == "SET_OPENAI_SECRET_REF"
        assert payload["current_secret_reference_target_is_placeholder"] is True
        assert payload["current_secret_reference_resolvable"] is False
        assert payload["secret_reference_probe_error"] == "reference_not_found"
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert payload["canonical_files_mutated"] is False

        assert cli.main([
            "runtime",
            "provider",
            "live-smoke-readiness",
            "--vault-root",
            str(vault),
            "--execute-live-probe",
            "--json",
        ]) == 1
    finally:
        _cleanup_vault(vault)


def test_live_smoke_closeout_plan_reports_next_steps_without_mutation() -> None:
    vault = _make_vault()
    try:
        payload = build_live_smoke_closeout_plan(vault)

        assert payload["plan_status"] == "blocked_pending_config_and_approval_chain"
        assert payload["ready_for_live_smoke"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["approval_artifact_written"] is False
        assert payload["decision_record_written"] is False
        assert payload["consumer_record_written"] is False
        assert payload["idempotency_marker_written"] is False
        assert payload["files_modified"] is False
        assert "no_live_probe_approval_requests_present" in payload["blocked_reasons"]
        step_ids = [step["step_id"] for step in payload["closeout_steps"]]
        assert "prepare_provider_config_change_request" in step_ids
        assert "run_approved_live_smoke" in step_ids

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_smoke_closeout_plan_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_live_smoke_closeout_plan_cli_is_read_only(capsys) -> None:
    vault = _make_vault()
    try:
        assert cli.main([
            "runtime",
            "provider",
            "live-smoke-closeout-plan",
            "--vault-root",
            str(vault),
            "--json",
        ]) == 0
        payload = _json_result(capsys.readouterr().out)

        assert payload["plan_status"] == "blocked_pending_config_and_approval_chain"
        assert payload["live_network_call_attempted"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["approval_artifact_written"] is False

        assert cli.main([
            "runtime",
            "provider",
            "live-smoke-closeout-plan",
            "--vault-root",
            str(vault),
            "--apply-provider-config",
            "--json",
        ]) == 1
    finally:
        _cleanup_vault(vault)


def test_live_probe_live_executor_writes_result_and_updates_primary_state_with_injected_success() -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            source_command="test",
        )
        write_live_probe_decision_consumer_record(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        write_live_probe_atomic_marker(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )

        def fake_runner(record, preflight):
            return {
                "ok": True,
                "error_type": None,
                "reason": "injected_probe_success",
                "status_code": 200,
                "live_network_call_attempted": False,
                "secret_value_read": False,
                "first_token_received": True,
                "chunks_received": 1,
            }

        payload = write_live_probe_live_executor(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
            probe_runner=fake_runner,
        )

        assert payload["executor_status"] == "executed"
        assert payload["execution_enabled"] is True
        assert payload["live_probe_execution_allowed"] is True
        assert payload["result_status"] == "probe_succeeded"
        assert payload["provider_state_mutated"] is True
        assert payload["queue_drained"] is False
        assert payload["gateway_mutated"] is False
        assert payload["canonical_files_mutated"] is False
        assert payload["files_modified"] is True

        result = load_live_probe_result_record(vault, gate_approval_id=gate_approval_id)
        assert result is not None
        assert result["result_status"] == "probe_succeeded"
        assert result["provider_state_after"]["state"] == "healthy"
        assert result["provider_state_after"]["sticky_for_development"] is False
        assert result["provider_state_after"]["last_success_at"]
        assert result["provider_state_after"]["cooldown_until"] is None

        primary = [
            record
            for record in load_provider_records(vault).values()
            if record.is_primary and record.runtime == "openclaw"
        ][0]
        assert primary.state == "healthy"
        assert primary.last_success_at is not None
        assert primary.cooldown_until is None
        assert primary.sticky_for_development is False

        with pytest.raises(RuntimeProviderGovernanceError):
            write_live_probe_live_executor(
                vault,
                target="primary",
                runtime="openclaw",
                gate_approval_id=gate_approval_id,
                source_command="test",
                probe_runner=fake_runner,
            )

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_probe_executor_started" in event_types
        assert "provider_live_probe_executor_completed" in event_types
        assert "provider_live_probe_result_record_written" in event_types
        assert "primary_probe_succeeded" in event_types
        assert "primary_recovered" in event_types
    finally:
        _cleanup_vault(vault)


def test_live_probe_live_executor_rate_limit_sets_primary_cooling_down_with_injected_result() -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            source_command="test",
        )
        write_live_probe_decision_consumer_record(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        write_live_probe_atomic_marker(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )

        def fake_runner(record, preflight):
            return {
                "ok": False,
                "error_type": "rate_limited",
                "reason": "injected_rate_limit",
                "status_code": 429,
                "retry_after_seconds": "120",
                "live_network_call_attempted": False,
                "secret_value_read": False,
            }

        payload = write_live_probe_live_executor(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
            probe_runner=fake_runner,
        )
        assert payload["result_status"] == "primary_rate_limited"
        assert payload["provider_state_after"]["state"] == "cooling_down"
        assert payload["provider_state_after"]["last_error_type"] == "rate_limited"
        assert payload["provider_state_after"]["cooldown_until"] is not None
        assert payload["queue_drained"] is False

        primary = [
            record
            for record in load_provider_records(vault).values()
            if record.is_primary and record.runtime == "openclaw"
        ][0]
        assert primary.state == "cooling_down"
        assert primary.last_error_type == "rate_limited"
        assert primary.cooldown_until is not None
        assert primary.sticky_for_development is False

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "primary_probe_failed" in event_types
        assert "provider_live_probe_result_record_written" in event_types
    finally:
        _cleanup_vault(vault)


def test_live_probe_live_executor_cli_requires_execute_flag_without_writing_result(capsys) -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        write_live_probe_approval_decision_record(
            vault,
            gate_approval_id,
            decision="approved",
            decided_by="operator",
            source_command="test",
        )
        write_live_probe_decision_consumer_record(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )
        write_live_probe_atomic_marker(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "live-probe-executor",
                    "primary",
                    "--runtime",
                    "openclaw",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 1
        )
        capsys.readouterr()
        assert load_live_probe_result_record(vault, gate_approval_id=gate_approval_id) is None
    finally:
        _cleanup_vault(vault)


def test_live_probe_approval_validation_rejects_mismatched_preflight() -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        mismatched_preflight = dict(created["live_probe_preflight"])
        mismatched_preflight["provider_id"] = "ollama"

        validation = validate_live_probe_approval_request(
            vault,
            gate_approval_id,
            expected_preflight=mismatched_preflight,
            source_command="test",
        )

        assert validation["structurally_valid"] is False
        assert validation["matches_preflight"] is False
        assert validation["live_probe_execution_allowed"] is False
        assert any("provider_id" in error for error in validation["errors"])

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_probe_approval_request_invalid" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_probe_cli_can_write_live_preflight_approval_artifact(capsys) -> None:
    vault = _make_vault()
    try:
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "probe",
                    "primary",
                    "--probe-mode",
                    "live-preflight",
                    "--write-approval-request",
                    "--requested-by",
                    "local-operator",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["probe_mode"] == "live-preflight"
        assert payload["files_modified"] is True
        assert payload["provider_state_mutated"] is False
        assert payload["approval_artifact"]["status"] == "pending"
        assert payload["approval_artifact"]["requested_by"] == "local-operator"
        assert Path(payload["approval_artifact"]["approval_ref"]).exists()
        assert not state_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_probe_cli_validates_gate_approval_id_without_execution(capsys) -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "probe",
                    "primary",
                    "--probe-mode",
                    "live-preflight",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["approval_validation"]["gate_approval_id"] == gate_approval_id
        assert payload["approval_validation"]["structurally_valid"] is True
        assert payload["approval_validation"]["live_probe_execution_allowed"] is False
        assert payload["live_probe_allowed"] is False
    finally:
        _cleanup_vault(vault)


def test_live_probe_executor_spec_is_not_built_and_non_executing() -> None:
    vault = _make_vault()
    try:
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        assert not state_path.exists()

        payload = build_live_probe_executor_spec(
            vault,
            target="primary",
            runtime="openclaw",
            source_command="test",
        )

        assert payload["ok"] is True
        assert payload["executor_status"] == "not_built"
        assert payload["execution_enabled"] is False
        assert payload["live_probe_execution_allowed"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["queue_mutated"] is False
        assert payload["gateway_mutated"] is False
        assert payload["canonical_files_mutated"] is False
        assert payload["approval_request_written"] is False
        assert not state_path.exists()

        preconditions = {item["id"]: item for item in payload["preconditions"]}
        assert preconditions["executor_implemented"]["status"] == "not_built"
        assert preconditions["gate_operation_declared"]["passed"] is True
        assert preconditions["gate_operation_allows_execution"]["passed"] is False
        assert preconditions["approval_artifact_supplied"]["status"] == "missing"
        assert preconditions["approval_decision_consumption_implemented"]["status"] == "not_built"
        assert preconditions["timeout_policy_present"]["passed"] is True
        assert preconditions["blocked_actions_unchanged"]["passed"] is True
        assert "live_provider_probe_executor_not_implemented" in payload["blocked_reasons"]

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_live_probe_executor_spec_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_live_probe_executor_spec_validates_pending_artifact_without_execution() -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        payload = build_live_probe_executor_spec(
            vault,
            target="primary",
            runtime="openclaw",
            gate_approval_id=gate_approval_id,
            source_command="test",
        )

        assert payload["ok"] is True
        assert payload["executor_status"] == "not_built"
        assert payload["approval_validation"]["gate_approval_id"] == gate_approval_id
        assert payload["approval_validation"]["structurally_valid"] is True
        assert payload["approval_validation"]["approval_status"] == "pending"
        assert payload["approval_validation"]["live_probe_execution_allowed"] is False
        assert payload["live_probe_execution_allowed"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert not state_path.exists()

        preconditions = {item["id"]: item for item in payload["preconditions"]}
        assert preconditions["approval_artifact_supplied"]["passed"] is True
        assert preconditions["approval_artifact_structurally_valid"]["passed"] is True
        assert preconditions["approval_status_approved"]["status"] == "pending"
        assert preconditions["approval_status_approved"]["passed"] is False
    finally:
        _cleanup_vault(vault)


def test_provider_executor_spec_cli_supports_gate_approval_id_without_execution(capsys) -> None:
    vault = _make_vault()
    try:
        created = probe_provider(
            vault,
            target="primary",
            runtime="openclaw",
            probe_mode="live-preflight",
            write_approval_request=True,
            requested_by="Codex",
            source_command="test",
        )
        gate_approval_id = created["approval_artifact"]["gate_approval_id"]
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "executor-spec",
                    "primary",
                    "--gate-approval-id",
                    gate_approval_id,
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["executor_status"] == "not_built"
        assert payload["execution_enabled"] is False
        assert payload["approval_validation"]["structurally_valid"] is True
        assert payload["approval_validation"]["live_probe_execution_allowed"] is False
        assert payload["provider_state_mutated"] is False
        assert not state_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_reconciliation_reports_expected_model_and_local_fallback_without_mutation() -> None:
    vault = _make_vault()
    try:
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        assert not state_path.exists()

        payload = build_provider_config_reconciliation(vault, source_command="test")

        assert payload["read_only"] is True
        assert payload["active_target_primary_model"] == "gpt-5.5"
        assert payload["expected_primary_model"] == "gpt-5.5"
        assert payload["expected_primary_model_compatibility_field"] is True
        assert payload["runtime_model_configs"][0]["primary_model"] == "gpt-5.5"
        assert payload["runtime_model_configs"][0]["primary_matches_expected"] is True
        assert payload["local_fallback"]["model_config_records"][0]["model"] == "phi4-mini:latest"
        assert payload["local_fallback"]["model_config_records"][0]["strength"] == "weak"
        assert payload["local_fallback"]["safe_num_ctx_default"] == 16384
        assert payload["provider_state_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["model_config_mutated"] is False
        assert payload["secret_value_read"] is False
        assert not state_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_reconciliation_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_rpgl_completion_status_reports_final_development_done_with_live_proof_deferred() -> None:
    vault = _make_vault()
    try:
        profile_path = vault / PROVIDER_TARGET_PROFILE_RELATIVE_PATH

        payload = build_rpgl_completion_status(vault, source_command="test")

        assert payload["completion_schema_id"] == "rpgl.completion_status.v1"
        assert payload["completion_status"] == "implemented_foundation_live_provider_proof_deferred"
        assert payload["feature_development_status"] == "complete_except_operator_approved_live_provider_proof"
        assert payload["remaining_major_development_passes_after_this"] == 0
        assert payload["remaining_optional_operator_approval_passes"] == 1
        assert payload["live_provider_proof_status"] == "deferred_pending_operator_approval"
        assert payload["primary_live_probe_verified"] is False
        assert payload["fallback_live_probe_verified"] is False
        assert payload["live_probe_result_record_count"] == 0
        assert payload["target_profile_exists"] is False
        assert payload["primary_target_model"] == "gpt-5.5"
        assert payload["current_model_target_is_configurable"] is True
        assert payload["gpt_5_5_is_compatibility_default_not_hardcoded_truth"] is True
        assert payload["local_fallback"]["num_ctx"] == 16384
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["queue_drained"] is False
        assert payload["files_modified"] is False
        assert not profile_path.exists()

        criteria = {item["id"]: item["status"] for item in payload["acceptance_criteria"]}
        assert criteria["weak_provider_high_authority_denial"] == "passed"
        assert criteria["queue_high_authority_when_primary_unavailable"] == "passed"
        assert criteria["fallback_timeout_contract"] == "passed_simulated_and_injected"
        assert criteria["live_openai_ollama_provider_smoke"] == "deferred_pending_operator_approval"
        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_completion_status_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_rpgl_completion_status_supports_non_gpt_target_profile() -> None:
    vault = _make_vault()
    try:
        _write_text(
            vault / PROVIDER_TARGET_PROFILE_RELATIVE_PATH,
            json.dumps(
                {
                    "schema_version": 1,
                    "profile_schema_id": "rpgl.provider_target_profile.v1",
                    "default_primary_model": "claude-sonnet-4-6",
                    "runtime_targets": {
                        "openclaw": {
                            "primary_model": "claude-sonnet-4-6",
                            "fallback_models": ["local-llama-coder:latest"],
                            "fallback_policy": "approval_required",
                        }
                    },
                    "local_fallback_target": {
                        "provider_id": "local_oss",
                        "model": "local-llama-coder:latest",
                        "enabled": False,
                        "num_ctx": 16384,
                    },
                }
            ),
        )

        payload = build_rpgl_completion_status(vault, source_command="test")

        assert payload["target_profile_exists"] is True
        assert payload["primary_target_model"] == "claude-sonnet-4-6"
        assert payload["current_model_target_is_configurable"] is True
        assert payload["gpt_5_5_is_compatibility_default_not_hardcoded_truth"] is False
    finally:
        _cleanup_vault(vault)


def test_rpgl_completion_status_cli_is_read_only_and_guarded(capsys) -> None:
    vault = _make_vault()
    try:
        assert cli.main([
            "runtime",
            "provider",
            "completion-status",
            "--vault-root",
            str(vault),
            "--json",
        ]) == 0
        envelope = json.loads(capsys.readouterr().out)
        output = envelope.get("result") or envelope
        assert output["completion_schema_id"] == "rpgl.completion_status.v1"
        assert output["remaining_major_development_passes_after_this"] == 0
        assert output["live_network_call_attempted"] is False
        assert output["secret_value_read"] is False

        assert cli.main([
            "runtime",
            "provider",
            "completion-status",
            "--vault-root",
            str(vault),
            "--execute-live-probe",
        ]) == 1
        assert "read-only" in capsys.readouterr().err
        assert not (vault / PROVIDER_TARGET_PROFILE_RELATIVE_PATH).exists()
    finally:
        _cleanup_vault(vault)


def test_provider_target_profile_defaults_to_legacy_model_without_becoming_fixed_truth() -> None:
    vault = _make_vault()
    try:
        payload = build_provider_target_profile(vault, source_command="test")

        assert payload["profile_exists"] is False
        assert payload["profile_source"] == "legacy_default_expected_primary_model"
        assert payload["default_primary_model"] == "gpt-5.5"
        assert payload["runtime_targets"]["openclaw"]["desired_primary_model"] == "gpt-5.5"
        assert payload["runtime_targets"]["openclaw"]["desired_fallback_models"] == []
        assert payload["local_fallback_target"]["num_ctx"] == 16384
        assert payload["local_fallback_target"]["safety_status"] == "safe_context_limit"
        assert payload["read_only"] is True
        assert payload["files_modified"] is False

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_target_profile_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_reconciliation_uses_dynamic_target_profile_for_primary_and_fallbacks() -> None:
    vault = _make_vault()
    try:
        _write_text(
            vault / "runtime" / "providers" / "provider_target_profile.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "default_primary_model": "gpt-6.0",
                    "runtime_targets": {
                        "openclaw": {
                            "primary_model": "gpt-6.0",
                            "fallback_models": ["phi4-mini:latest"],
                            "fallback_enforcement": "minimum",
                        }
                    },
                    "provider_setup_targets": {
                        "openai": {"default_model": "gpt-6.0"}
                    },
                    "local_fallback": {
                        "provider_id": "local_oss",
                        "model": "phi4-mini:latest",
                        "num_ctx": 16384,
                        "enabled": False,
                    },
                },
                indent=2,
            ),
        )

        payload = build_provider_config_reconciliation(vault, source_command="test")

        assert payload["target_profile_exists"] is True
        assert payload["active_target_primary_model"] == "gpt-6.0"
        assert payload["expected_primary_model"] == "gpt-6.0"
        assert payload["expected_primary_model_compatibility_field"] is True
        runtime_config = payload["runtime_model_configs"][0]
        assert runtime_config["target_primary_model"] == "gpt-6.0"
        assert runtime_config["target_fallback_models"] == ["phi4-mini:latest"]
        assert runtime_config["fallbacks_match_target"] is True
        assert runtime_config["primary_matches_target"] is False
        mismatch = next(item for item in payload["mismatches"] if item["type"] == "runtime_primary_model_mismatch")
        assert mismatch["expected_model"] == "gpt-6.0"

        plan = build_provider_config_change_plan(vault, source_command="test")
        assert plan["active_target_primary_model"] == "gpt-6.0"
        assert plan["expected_primary_model_compatibility_field"] is True
        primary_change = next(change for change in plan["proposed_changes"] if change["change_id"] == "openclaw-primary-model")
        assert primary_change["proposed_value"] == "gpt-6.0"
    finally:
        _cleanup_vault(vault)


def test_provider_target_profile_cli_is_read_only(capsys) -> None:
    vault = _make_vault()
    try:
        assert cli.main([
            "runtime",
            "provider",
            "target-profile",
            "--vault-root",
            str(vault),
            "--json",
        ]) == 0
        payload = _json_result(capsys.readouterr().out)

        assert payload["profile_source"] == "legacy_default_expected_primary_model"
        assert payload["read_only"] is True
        assert payload["files_modified"] is False

        assert cli.main([
            "runtime",
            "provider",
            "target-profile",
            "--vault-root",
            str(vault),
            "--apply-provider-config",
            "--json",
        ]) == 1
    finally:
        _cleanup_vault(vault)


def test_provider_target_profile_plan_is_generic_and_non_mutating() -> None:
    vault = _make_vault()
    try:
        profile_path = vault / PROVIDER_TARGET_PROFILE_RELATIVE_PATH
        proposal_dir = vault / TARGET_PROFILE_PROPOSAL_RELATIVE_DIR
        queue_path = vault / "runtime" / "providers" / "state" / "provider_queue.json"

        payload = build_provider_target_profile_plan(vault, source_command="test")

        assert payload["plan_status"] == "profile_missing_candidate_ready"
        assert payload["desired_default_primary_model"] == "gpt-5.5"
        assert payload["profile_change_needed"] is True
        assert payload["candidate_profile"]["default_primary_model"] == "gpt-5.5"
        assert payload["candidate_profile"]["runtime_targets"]["openclaw"]["primary_model"] == "gpt-5.5"
        assert payload["candidate_profile"]["runtime_targets"]["openclaw"]["fallback_models"] == ["phi4-mini:latest"]
        assert payload["candidate_profile"]["runtime_targets"]["openclaw"]["fallback_enforcement"] == "observe_only"
        assert payload["candidate_profile"]["local_fallback"]["num_ctx"] == 16384
        assert payload["candidate_profile"]["local_fallback"]["authority"] == "recovery_assistant_only"
        assert payload["read_only"] is True
        assert payload["profile_file_written"] is False
        assert payload["approval_request_written"] is False
        assert payload["files_modified"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["model_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert not profile_path.exists()
        assert not proposal_dir.exists()
        assert not queue_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_target_profile_plan_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_target_profile_plan_accepts_non_gpt_target_model() -> None:
    vault = _make_vault()
    try:
        payload = build_provider_target_profile_plan(vault, target_model="claude-sonnet-4-6", source_command="test")

        assert payload["desired_default_primary_model"] == "claude-sonnet-4-6"
        assert payload["target_model_source"] == "cli_target"
        assert payload["candidate_profile"]["default_primary_model"] == "claude-sonnet-4-6"
        assert payload["candidate_profile"]["runtime_targets"]["openclaw"]["primary_model"] == "claude-sonnet-4-6"
        assert payload["candidate_profile"]["provider_setup_targets"]["claude"]["default_model"] == "claude-sonnet-4-6"
        assert payload["candidate_profile"]["runtime_targets"]["openclaw"]["fallback_models"] == ["phi4-mini:latest"]
    finally:
        _cleanup_vault(vault)


def test_provider_target_profile_approval_request_creates_proposal_and_queue_only() -> None:
    vault = _make_vault()
    try:
        profile_path = vault / PROVIDER_TARGET_PROFILE_RELATIVE_PATH
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        payload = write_provider_target_profile_approval_request(
            vault,
            target_model="claude-sonnet-4-6",
            requested_by="test-operator",
            source_command="test",
        )

        assert payload["approval_request_written"] is True
        assert payload["queue_item_created"] is True
        assert payload["queue_item_id"]
        assert payload["profile_file_written"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["model_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert not profile_path.exists()
        assert not state_path.exists()
        assert "model_id: gpt-5.5" in model_config_path.read_text(encoding="utf-8")

        proposal_path = Path(payload["approval_request_ref"])
        assert proposal_path.exists()
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        assert proposal["record_type"] == "runtime_provider_target_profile_approval_request"
        assert proposal["status"] == "pending_operator_review"
        assert proposal["profile_file_written"] is False
        assert proposal["candidate_profile_digest_sha256"] == payload["candidate_profile_digest_sha256"]

        queue_item = load_queue_items(vault)[0]
        assert queue_item.task_class == "runtime_config_change"
        assert queue_item.approval_status == "needs_operator_approval"
        assert queue_item.retry_status == "needs_operator_approval"
        assert queue_item.files_modified is False
        assert str(PROVIDER_TARGET_PROFILE_RELATIVE_PATH) in queue_item.required_context_files

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_target_profile_approval_request_created" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_target_profile_plan_cli_supports_generic_model_and_write_guard(capsys) -> None:
    vault = _make_vault()
    try:
        assert cli.main([
            "runtime",
            "provider",
            "target-profile-plan",
            "claude-sonnet-4-6",
            "--vault-root",
            str(vault),
            "--json",
        ]) == 0
        payload = _json_result(capsys.readouterr().out)
        assert payload["desired_default_primary_model"] == "claude-sonnet-4-6"
        assert payload["read_only"] is True
        assert payload["profile_file_written"] is False

        assert cli.main([
            "runtime",
            "provider",
            "target-profile-plan",
            "--vault-root",
            str(vault),
            "--apply-provider-config",
            "--json",
        ]) == 1
        capsys.readouterr()

        assert cli.main([
            "runtime",
            "provider",
            "target-profile-plan",
            "gpt-5.5",
            "--vault-root",
            str(vault),
            "--write-approval-request",
            "--requested-by",
            "test-operator",
            "--json",
        ]) == 0
        written = _json_result(capsys.readouterr().out)
        assert written["approval_request_written"] is True
        assert written["profile_file_written"] is False
        assert Path(written["approval_request_ref"]).exists()
        assert not (vault / PROVIDER_TARGET_PROFILE_RELATIVE_PATH).exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_reconciliation_reports_repo_model_mismatch_and_missing_context() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)

        payload = build_provider_config_reconciliation(vault, source_command="test")

        assert payload["operator_truth_matches_repo"] is False
        assert payload["runtime_model_configs"][0]["primary_model"] == "claude-sonnet-4-6"
        assert payload["runtime_model_configs"][0]["primary_matches_expected"] is False
        assert payload["provider_setup_state"]["providers"]["openai"]["default_model"] == "set-by-wizard:openai"
        assert payload["local_fallback"]["num_ctx_status"] == "not_declared"
        mismatch_types = {item["type"] for item in payload["mismatches"]}
        assert "runtime_primary_model_mismatch" in mismatch_types
        assert "setup_openai_default_model_mismatch" in mismatch_types
        assert "local_fallback_context_not_declared" in mismatch_types
        assert payload["config_file_scan"]["expected_model_files"] == []
    finally:
        _cleanup_vault(vault)


def test_provider_config_change_plan_is_non_mutating() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        queue_path = vault / "runtime" / "providers" / "state" / "provider_queue.json"
        proposal_dir = vault / CONFIG_PROPOSAL_RELATIVE_DIR

        payload = build_provider_config_change_plan(vault, source_command="test")

        assert payload["status"] == "changes_proposed"
        assert payload["requires_operator_approval"] is True
        assert payload["approval_request_written"] is False
        assert payload["queue_item_created"] is False
        assert payload["files_modified"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["model_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert not state_path.exists()
        assert not queue_path.exists()
        assert not proposal_dir.exists()

        change_types = {change["change_type"] for change in payload["proposed_changes"]}
        assert "runtime_primary_model_update" in change_types
        assert "setup_openai_default_model_update" in change_types
        assert "local_fallback_context_policy_decision" in change_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_change_approval_request_creates_proposal_and_queue_only() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        payload = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )

        assert payload["approval_request_written"] is True
        assert payload["queue_item_created"] is True
        assert payload["queue_item_id"]
        assert payload["provider_state_mutated"] is False
        assert payload["model_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()

        proposal_path = Path(payload["approval_request_ref"])
        assert proposal_path.exists()
        assert proposal_path.parent == vault / CONFIG_PROPOSAL_RELATIVE_DIR
        record = json.loads(proposal_path.read_text(encoding="utf-8"))
        assert record["record_type"] == "runtime_provider_config_change_approval_request"
        assert record["provider_config_mutated"] is False
        assert record["queue_item_id"] == payload["queue_item_id"]

        queue_items = load_queue_items(vault)
        assert len(queue_items) == 1
        assert queue_items[0].task_class == "runtime_config_change"
        assert queue_items[0].approval_status == "needs_operator_approval"
        assert queue_items[0].retry_status == "needs_operator_approval"
        assert queue_items[0].files_modified is False
        summary = queue_summary(vault)
        assert summary["queued_task_count"] == 1
        assert summary["needs_operator_approval_count"] == 1
        assert summary["high_complexity_waiting_for_primary"] == 1
    finally:
        _cleanup_vault(vault)


def test_provider_config_plan_cli_can_write_review_artifact_without_config_mutation(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"
        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-plan",
                    "--vault-root",
                    str(vault),
                    "--write-approval-request",
                    "--requested-by",
                    "test-operator",
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["approval_request_written"] is True
        assert payload["queue_item_id"]
        assert payload["provider_state_mutated"] is False
        assert payload["model_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()
    finally:
        _cleanup_vault(vault)


def test_credential_config_mutation_governance_lane_proof_is_secret_safe_and_non_mutating() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        profile_path = vault / PROVIDER_TARGET_PROFILE_RELATIVE_PATH
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        payload = build_credential_config_mutation_governance_lane_proof(
            vault,
            target_model="claude-sonnet-4-6",
            source_command="test",
        )

        assert payload["schema_id"] == "rpgl.credential_config_mutation_governance_lane_proof.v1"
        assert payload["status"] == "proof_ready_no_mutation"
        assert payload["read_only"] is True
        assert payload["files_modified"] is False
        assert payload["raw_secret_values_included"] is False
        assert payload["secret_value_read"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["approval_consumed"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["target_profile_mutated"] is False
        assert payload["runtime_config_mutated"] is False
        assert payload["protected_config_mutated"] is False
        assert not profile_path.exists()
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()

        proof = payload["minimum_proof"]
        assert proof["approval_packet"]["available"] is True
        assert proof["approval_packet"]["approval_required"] is True
        assert proof["approval_packet"]["gate_allows_without_approval"] is False
        assert RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID in proof["approval_packet"]["gate_reason"]
        assert proof["redacted_before_after_diff"]
        assert {item["change_id"] for item in proof["redacted_before_after_diff"]} >= {
            "openclaw-primary-model",
            "setup-openai-default-model",
        }
        secret_proof = proof["secret_reference_only"]
        assert secret_proof["secret_reference_metadata_only"] is True
        assert secret_proof["raw_credentials_included"] is False
        assert secret_proof["raw_credential_values_displayed"] is False
        assert secret_proof["settings_secrets_allowed_in_config"] is False
        denial = proof["protected_config_denial"]
        assert denial["denied_payload_ok"] is False
        assert "secret_like_key" in denial["denied_issue_codes"]
        assert "parent_traversal_not_allowed" in denial["denied_issue_codes"]
        readiness = proof["provider_readiness_refresh"]
        assert readiness["read_only"] is True
        assert readiness["secret_values_visible"] is False
        assert readiness["writes_provider_config"] is False
        assert readiness["writes_target_profile"] is False
        assert proof["audit_path"]["audit_event_type"] == "credential_config_mutation_governance_lane_proof_requested"

        serialized = json.dumps(payload)
        assert "test-key-redacted-proof-placeholder-not-a-real-secret" not in serialized
        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "credential_config_mutation_governance_lane_proof_requested" in event_types
    finally:
        _cleanup_vault(vault)



def test_provider_config_apply_preflight_validates_proposal_and_queue_without_apply() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )

        payload = build_provider_config_apply_preflight(
            vault,
            proposal["proposal_id"],
            source_command="test",
        )

        assert payload["preflight_status"] == "ready_for_operator_approval"
        assert payload["structurally_valid"] is True
        assert payload["drift_detected"] is False
        assert payload["apply_enabled"] is False
        assert payload["approval_consumed"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["queue_item_id"] == proposal["queue_item_id"]
        assert {check["status"] for check in payload["checks"]} == {"ok"}
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_preflight_blocks_on_config_drift() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        _write_text(
            vault / "runtime" / "openclaw" / "model_config.yaml",
            "\n".join(
                [
                    "runtime: openclaw",
                    "primary:",
                    "  model_id: gpt-5.5",
                    "  max_tokens: 8192",
                    "  temperature: 0.2",
                    "fallbacks: []",
                ]
            )
            + "\n",
        )

        payload = build_provider_config_apply_preflight(
            vault,
            proposal["proposal_id"],
            source_command="test",
        )

        assert payload["preflight_status"] == "blocked"
        assert payload["structurally_valid"] is False
        assert payload["drift_detected"] is True
        assert "current config drift detected" in payload["errors"]
        assert any(check["status"] == "drift_detected" for check in payload["checks"])
        assert payload["provider_config_mutated"] is False
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_preflight_cli_is_no_apply(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"
        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-preflight",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["structurally_valid"] is True
        assert payload["apply_enabled"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_design_is_non_executing_executor_spec() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        payload = build_provider_config_apply_design(
            vault,
            proposal["proposal_id"],
            source_command="test",
        )

        assert payload["design_status"] == "ready_for_executor_implementation_review"
        assert payload["executor_status"] == "not_built"
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["operation"] == RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION
        assert payload["approval_schema_id"] == RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID
        assert payload["approval_schema"]["approval_schema_id"] == RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID
        assert payload["approval_request_template"]["proposal_id"] == proposal["proposal_id"]
        assert payload["approval_request_template"]["queue_item_id"] == proposal["queue_item_id"]
        assert payload["preflight_structurally_valid"] is True
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["secret_value_read"] is False
        assert payload["live_network_call_attempted"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()

        preconditions = {item["id"]: item for item in payload["preconditions"]}
        assert preconditions["apply_preflight_structurally_valid"]["passed"] is True
        assert preconditions["gate_operation_declared"]["passed"] is True
        assert preconditions["gate_operation_allows_execution"]["passed"] is False
        assert preconditions["approval_decision_consumption_implemented"]["status"] == "not_built"
        assert preconditions["apply_executor_implemented"]["status"] == "not_built"
        assert "provider_config_apply_executor_not_implemented" in payload["blocked_reasons"]

        target_writes = {item["change_id"]: item for item in payload["target_writes"]}
        assert target_writes["openclaw-primary-model"]["write_enabled_after_approval"] is True
        assert target_writes["setup-openai-default-model"]["write_enabled_after_approval"] is True
        assert target_writes["local-fallback-context-policy"]["write_enabled_after_approval"] is False
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_design_cli_is_non_mutating(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-design",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["executor_status"] == "not_built"
        assert payload["execution_enabled"] is False
        assert payload["approval_consumed"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["provider_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_approval_request_preview_is_non_mutating() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        payload = build_provider_config_apply_approval_request_preview(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )

        assert payload["record_type"] == "runtime_provider_config_apply_approval_request"
        assert payload["approval_schema_id"] == RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID
        assert payload["operation"] == RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION
        assert payload["proposal_id"] == proposal["proposal_id"]
        assert payload["queue_item_id"] == proposal["queue_item_id"]
        assert payload["operator_request_id"].startswith("rpgl-config-apply-req-")
        assert payload["approval_request_written"] is False
        assert payload["files_modified"] is False
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "runtime/openclaw/model_config.yaml" in payload["target_paths"]
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not (vault / CONFIG_APPLY_APPROVAL_RELATIVE_DIR / f"{payload['gate_approval_id']}.json").exists()
        assert not state_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_approval_request_writes_pending_artifact_without_apply() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        payload = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )

        assert payload["approval_request_written"] is True
        assert payload["approval_ref"].startswith(str(vault / CONFIG_APPLY_APPROVAL_RELATIVE_DIR))
        assert Path(payload["approval_ref"]).exists()
        assert payload["operator_request_id"].startswith("rpgl-config-apply-req-")
        assert payload["status"] == "pending"
        assert payload["files_modified"] is True
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["secret_value_read"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["approval_consumed"] is False
        assert payload["request_digest_sha256"]
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()

        validation = validate_provider_config_apply_approval_request(
            vault,
            payload["gate_approval_id"],
            expected_design=payload["approval_design"],
            source_command="test",
        )
        assert validation["structurally_valid"] is True
        assert validation["matches_design"] is True
        assert validation["approval_status"] == "pending"
        assert validation["apply_execution_allowed"] is False
        assert validation["approval_consumed"] is False
        assert validation["provider_config_mutated"] is False

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_approval_request_created" in event_types
        assert "provider_config_apply_approval_request_validated" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_approval_request_cli_write_and_validate_are_non_mutating(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-approval-request",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--write-approval-request",
                    "--requested-by",
                    "test-operator",
                    "--json",
                ]
            )
            == 0
        )
        written = _json_result(capsys.readouterr().out)
        assert written["approval_request_written"] is True
        assert written["provider_config_mutated"] is False
        assert Path(written["approval_ref"]).exists()

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-approval-request",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    written["gate_approval_id"],
                    "--json",
                ]
            )
            == 0
        )
        validated = _json_result(capsys.readouterr().out)
        assert validated["approval_request_written"] is False
        assert validated["approval_validation"]["structurally_valid"] is True
        assert validated["approval_validation"]["apply_execution_allowed"] is False
        assert validated["provider_config_mutated"] is False
        assert validated["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_preflight_blocks_pending_approval_without_consuming() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        payload = build_provider_config_apply_decision_preflight(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["decision_consumption_status"] == "blocked_missing_immutable_decision_record"
        assert payload["approval_status"] == "pending"
        assert payload["approval_decision_accepted"] is False
        assert payload["immutable_decision_status"] == "missing"
        assert payload["immutable_decision_accepted"] is False
        assert payload["decision_record_validation"]["records_found"] == 0
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["approval_artifact_mutated"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["queue_drained"] is False
        assert payload["idempotency"]["marker_exists"] is False
        assert payload["idempotency"]["marker_path"] == str(marker_path)
        assert "approval_decision_consumption_not_implemented" in payload["blocked_reasons"]
        assert "provider_config_apply_immutable_decision_missing" in payload["blocked_reasons"]
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()
        assert not marker_path.exists()

        loaded_approval = json.loads(Path(approval["approval_ref"]).read_text(encoding="utf-8"))
        assert loaded_approval["status"] == "pending"
        assert loaded_approval["approval_consumed"] is False

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_decision_record_invalid" in event_types
        assert "provider_config_apply_decision_preflight_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_preflight_approved_still_does_not_apply() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        payload = build_provider_config_apply_decision_preflight(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["decision_consumption_status"] == "blocked_missing_immutable_decision_record"
        assert payload["approval_status"] == "pending"
        assert payload["approval_decision_accepted"] is False
        assert payload["immutable_decision_status"] == "missing"
        assert payload["immutable_decision_accepted"] is False
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["provider_config_mutated"] is False
        assert "approval_decision_consumption_not_implemented" in payload["blocked_reasons"]
        assert "provider_config_apply_immutable_decision_missing" in payload["blocked_reasons"]
        assert "provider_config_apply_executor_not_implemented" in payload["blocked_reasons"]
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_preflight_validates_immutable_approved_decision_without_consuming() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        decision = write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"

        payload = build_provider_config_apply_decision_preflight(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["decision_consumption_status"] == "approved_decision_record_valid_but_executor_not_built"
        assert payload["approval_status"] == "pending"
        assert payload["approval_decision_accepted"] is False
        assert payload["immutable_decision_status"] == "approved_decision_record_valid"
        assert payload["immutable_decision_accepted"] is True
        assert payload["decision_record_validation"]["records_found"] == 1
        assert payload["decision_record_validation"]["selected_decision_id"] == decision["decision_id"]
        assert payload["decision_record_validation"]["decision_digest_valid"] is True
        assert payload["decision_record_validation"]["decision_record_consumable"] is True
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["idempotency"]["marker_exists"] is False
        assert "approval_decision_consumption_not_implemented" in payload["blocked_reasons"]
        assert "provider_config_apply_executor_not_implemented" in payload["blocked_reasons"]
        assert not state_path.exists()
        assert not marker_path.exists()

        loaded_decision = json.loads(Path(decision["decision_ref"]).read_text(encoding="utf-8"))
        assert loaded_decision["decision_status"] == "recorded"
        assert loaded_decision["decision_consumed"] is False

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_decision_record_validated" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_preflight_blocks_denied_decision_record_without_consuming() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="denied",
            decided_by="test-operator",
            reason="unit test denial",
            source_command="test",
        )

        payload = build_provider_config_apply_decision_preflight(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["decision_consumption_status"] == "blocked_approval_decision_denied"
        assert payload["immutable_decision_status"] == "denied_decision_record_valid"
        assert payload["immutable_decision_accepted"] is False
        assert payload["decision_record_validation"]["decision_record_consumable"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["decision_consumed"] is False
        assert "provider_config_apply_approval_decision_denied" in payload["blocked_reasons"]
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumption_plan_blocks_missing_decision_without_mutation() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        payload = build_provider_config_apply_decision_consumption_plan(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["decision_consumption_plan_status"] == "blocked_blocked_missing_immutable_decision_record"
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["future_consumption_marker_plan"]["marker_path"] == str(marker_path)
        assert payload["future_consumption_marker_plan"]["write_enabled"] is False
        assert payload["future_consumption_marker_plan"]["payload_preview"]["record_type"] == (
            "runtime_provider_config_apply_decision_consumption_marker"
        )
        assert "provider_config_apply_decision_consumer_not_implemented" in payload["blocked_reasons"]
        assert not marker_path.exists()
        assert not state_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_decision_consumption_plan_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumption_plan_for_approved_decision_is_non_mutating() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        decision = write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"

        payload = build_provider_config_apply_decision_consumption_plan(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["decision_consumption_plan_status"] == "ready_for_consumption_design_review_executor_not_built"
        assert payload["selected_decision_id"] == decision["decision_id"]
        assert payload["decision_record_validation"]["decision_record_consumable"] is True
        marker_plan = payload["future_consumption_marker_plan"]
        assert marker_plan["marker_exists"] is False
        assert marker_plan["write_supported"] is False
        assert marker_plan["atomic_create_new_required"] is True
        assert marker_plan["payload_preview"]["selected_decision_id"] == decision["decision_id"]
        assert marker_plan["payload_preview"]["decision_digest_sha256"] == decision["decision_digest_sha256"]
        assert "write_marker_with_create_new_exclusive_semantics" in payload["atomic_consumption_rules"]
        assert "provider_config_apply_decision_consumption_plan" in payload["feature_completion_tracker"]["completed"]
        assert "atomic_consumption_marker_writer" in payload["feature_completion_tracker"]["remaining_before_complete"]
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumption_plan_cli_is_non_mutating(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-decision-consumption-plan",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["decision_consumption_plan_status"] == "blocked_blocked_missing_immutable_decision_record"
        assert payload["execution_enabled"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_design_blocks_missing_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        payload = build_provider_config_apply_decision_consumer_design(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_design_status"] == "blocked_decision_consumption_plan_not_ready"
        assert payload["consumer_status"] == "not_built"
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["marker_directory_created"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["consumer_record_template"]["consumer_record_schema_id"] == (
            "rpgl.provider_config_apply_decision_consumer.v1"
        )
        assert payload["consumer_record_template"]["target_marker_path"] == str(marker_path)
        assert payload["path_constraints"]["decision_record_mutation_allowed"] is False
        assert payload["path_constraints"]["approval_artifact_mutation_allowed"] is False
        assert "secret" in payload["forbidden_consumer_fields"]
        assert "preserve immutable decision records; represent consumption through a separate consumer record and future marker" in payload["consumer_algorithm"]
        assert not marker_path.exists()
        assert not state_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_decision_consumer_design_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_design_ready_for_approved_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        decision = write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"

        payload = build_provider_config_apply_decision_consumer_design(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_design_status"] == "ready_for_future_decision_consumer_but_consumer_not_built"
        assert payload["selected_decision_id"] == decision["decision_id"]
        assert payload["decision_record_validation"]["decision_record_consumable"] is True
        assert payload["idempotency"]["marker_exists"] is False
        assert payload["consumer_record_template"]["selected_decision_id"] == decision["decision_id"]
        assert payload["consumer_record_template"]["decision_digest_sha256"] == decision["decision_digest_sha256"]
        preconditions = {item["id"]: item for item in payload["future_consumer_preconditions"]}
        assert preconditions["decision_consumption_plan_ready"]["passed"] is True
        assert preconditions["single_approved_immutable_decision_selected"]["passed"] is True
        assert preconditions["decision_consumer_implemented"]["status"] == "not_built"
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_record_mutated"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_design_flags_existing_marker() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text('{"status":"reserved_for_future_test"}\n', encoding="utf-8")

        payload = build_provider_config_apply_decision_consumer_design(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_design_status"] == "blocked_prior_apply_marker_exists"
        assert payload["idempotency"]["marker_exists"] is True
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["provider_config_mutated"] is False
        assert "provider_config_apply_idempotency_marker_exists" in payload["blocked_reasons"]
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_design_cli_is_non_mutating(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-decision-consumer-design",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["consumer_design_status"] == "blocked_decision_consumption_plan_not_ready"
        assert payload["execution_enabled"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_preflight_blocks_missing_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        payload = build_provider_config_apply_decision_consumer_preflight(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_preflight_status"] == "blocked_decision_consumer_design_not_ready"
        assert payload["consumer_preflight_schema_id"] == "rpgl.provider_config_apply_decision_consumer_preflight.v1"
        assert payload["consumer_status"] == "not_built"
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumer_preflight_record_written"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["marker_directory_created"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["idempotency"]["marker_exists"] is False
        assert payload["idempotency"]["marker_path"] == str(marker_path)
        assert "decision_consumer_not_built" in payload["stop_conditions"]
        assert "preserve_immutable_decision_record" in payload["handoff_requirements"]
        assert not marker_path.exists()
        assert not state_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_decision_consumer_preflight_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_preflight_ready_for_approved_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        decision = write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"

        payload = build_provider_config_apply_decision_consumer_preflight(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_preflight_status"] == (
            "ready_for_future_decision_consumer_invocation_but_consumer_not_built"
        )
        assert payload["selected_decision_id"] == decision["decision_id"]
        assert payload["selected_decision_digest_sha256"] == decision["decision_digest_sha256"]
        assert payload["decision_record_validation"]["decision_record_consumable"] is True
        assert payload["consumer_invocation_contract"]["required_gate_approval_id"] == approval["gate_approval_id"]
        assert payload["consumer_invocation_contract"]["required_decision_digest_sha256"] == decision["decision_digest_sha256"]
        preconditions = {item["id"]: item for item in payload["future_consumer_preconditions"]}
        assert preconditions["decision_consumer_design_ready"]["passed"] is True
        assert preconditions["single_approved_immutable_decision_selected"]["passed"] is True
        assert preconditions["decision_record_consumable"]["passed"] is True
        assert preconditions["single_use_marker_absent"]["passed"] is True
        assert preconditions["decision_consumer_implemented"]["status"] == "not_built"
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_record_mutated"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumer_preflight_record_written"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_preflight_flags_existing_marker() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text('{"status":"reserved_for_future_test"}\n', encoding="utf-8")

        payload = build_provider_config_apply_decision_consumer_preflight(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_preflight_status"] == "blocked_prior_apply_marker_exists"
        assert payload["idempotency"]["marker_exists"] is True
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumer_preflight_record_written"] is False
        assert payload["provider_config_mutated"] is False
        assert "provider_config_apply_idempotency_marker_exists" in payload["blocked_reasons"]
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_preflight_cli_is_non_mutating(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-decision-consumer-preflight",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["consumer_preflight_status"] == "blocked_decision_consumer_design_not_ready"
        assert payload["execution_enabled"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumer_preflight_record_written"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_implementation_plan_blocks_missing_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        payload = build_provider_config_apply_decision_consumer_implementation_plan(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_implementation_plan_status"] == "blocked_decision_consumer_preflight_not_ready"
        assert payload["consumer_implementation_plan_schema_id"] == (
            "rpgl.provider_config_apply_decision_consumer_implementation_plan.v1"
        )
        assert payload["consumer_writer_status"] == "not_built"
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumer_preflight_record_written"] is False
        assert payload["consumer_directory_created"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["consumer_write_contract"]["write_enabled"] is False
        assert payload["consumer_write_contract"]["future_write_flag_required"] == "--write-consumer-record"
        assert "rerun decision consumer preflight immediately before writing any consumer record" in payload["implementation_sequence"]
        assert "secret" in payload["forbidden_consumer_record_fields"]
        assert not consumer_dir.exists()
        assert not marker_path.exists()
        assert not state_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_decision_consumer_implementation_plan_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_implementation_plan_ready_for_approved_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        decision = write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"

        payload = build_provider_config_apply_decision_consumer_implementation_plan(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_implementation_plan_status"] == (
            "ready_for_future_decision_consumer_implementation_but_writer_not_built"
        )
        assert payload["selected_decision_id"] == decision["decision_id"]
        assert payload["decision_record_validation"]["decision_record_consumable"] is True
        assert payload["consumer_record_template"]["selected_decision_id"] == decision["decision_id"]
        assert payload["consumer_record_template"]["decision_digest_sha256"] == decision["decision_digest_sha256"]
        assert payload["consumer_write_contract"]["write_supported_now"] is False
        preconditions = {item["id"]: item for item in payload["future_consumer_writer_preconditions"]}
        assert preconditions["decision_consumer_preflight_ready"]["passed"] is True
        assert preconditions["single_approved_immutable_decision_selected"]["passed"] is True
        assert preconditions["decision_consumer_writer_implemented"]["status"] == "not_built"
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_record_mutated"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert not consumer_dir.exists()
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_implementation_plan_flags_existing_marker() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text('{"status":"reserved_for_future_test"}\n', encoding="utf-8")
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR

        payload = build_provider_config_apply_decision_consumer_implementation_plan(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_implementation_plan_status"] == "blocked_prior_apply_marker_exists"
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumer_directory_created"] is False
        assert payload["provider_config_mutated"] is False
        assert "provider_config_apply_idempotency_marker_exists" in payload["blocked_reasons"]
        assert not consumer_dir.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_implementation_plan_cli_is_non_mutating(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-decision-consumer-implementation-plan",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["consumer_implementation_plan_status"] == "blocked_decision_consumer_preflight_not_ready"
        assert payload["execution_enabled"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not consumer_dir.exists()
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_writer_dry_run_blocks_missing_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        payload = build_provider_config_apply_decision_consumer_writer_dry_run(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_writer_dry_run_status"] == "blocked_decision_consumer_implementation_plan_not_ready"
        assert payload["consumer_writer_dry_run_schema_id"] == (
            "rpgl.provider_config_apply_decision_consumer_writer_dry_run.v1"
        )
        assert payload["consumer_writer_status"] == "dry_run_only"
        assert payload["write_enabled"] is False
        assert payload["execution_enabled"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumer_directory_created"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["consumer_record_digest_sha256"]
        assert payload["candidate_consumer_record"]["consumer_record_written"] is False
        assert "compute consumer record digest" in payload["dry_run_steps"]
        assert not consumer_dir.exists()
        assert not marker_path.exists()
        assert not state_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_decision_consumer_writer_dry_run_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_writer_dry_run_ready_for_approved_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        decision = write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"

        payload = build_provider_config_apply_decision_consumer_writer_dry_run(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_writer_dry_run_status"] == "ready_for_future_consumer_writer_dry_run_but_write_disabled"
        assert payload["selected_decision_id"] == decision["decision_id"]
        assert payload["decision_record_validation"]["decision_record_consumable"] is True
        assert payload["candidate_consumer_record"]["selected_decision_id"] == decision["decision_id"]
        assert payload["candidate_consumer_record"]["decision_digest_sha256"] == decision["decision_digest_sha256"]
        assert payload["candidate_consumer_record"]["consumer_record_digest_sha256"] == payload["consumer_record_digest_sha256"]
        preconditions = {item["id"]: item for item in payload["future_consumer_writer_preconditions"]}
        assert preconditions["implementation_plan_ready"]["passed"] is True
        assert preconditions["single_approved_immutable_decision_selected"]["passed"] is True
        assert preconditions["consumer_writer_real_write_enabled"]["status"] == "disabled_dry_run_only"
        assert payload["write_supported_now"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_record_mutated"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert not consumer_dir.exists()
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_writer_dry_run_flags_existing_marker() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text('{"status":"reserved_for_future_test"}\n', encoding="utf-8")
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR

        payload = build_provider_config_apply_decision_consumer_writer_dry_run(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_writer_dry_run_status"] == "blocked_prior_apply_marker_exists"
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumer_directory_created"] is False
        assert payload["provider_config_mutated"] is False
        assert "provider_config_apply_idempotency_marker_exists" in payload["blocked_reasons"]
        assert not consumer_dir.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_writer_dry_run_cli_is_non_mutating(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-decision-consumer-writer-dry-run",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["consumer_writer_dry_run_status"] == "blocked_decision_consumer_implementation_plan_not_ready"
        assert payload["execution_enabled"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not consumer_dir.exists()
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_write_guard_contract_blocks_missing_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        payload = build_provider_config_apply_decision_consumer_write_guard_contract(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_write_guard_status"] == "blocked_consumer_writer_dry_run_not_ready"
        assert payload["consumer_write_guard_contract_schema_id"] == (
            "rpgl.provider_config_apply_decision_consumer_write_guard_contract.v1"
        )
        assert payload["consumer_writer_status"] == "contract_only"
        assert payload["write_enabled"] is False
        assert payload["explicit_write_flag_contract"]["required_future_flag"] == "--write-consumer-record"
        assert payload["explicit_write_flag_contract"]["current_cli_accepts_write_flag"] is False
        assert payload["create_new_record_policy"]["directory_created_now"] is False
        assert payload["create_new_record_policy"]["overwrite_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert not consumer_dir.exists()
        assert not marker_path.exists()
        assert not state_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_decision_consumer_write_guard_contract_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_write_guard_contract_ready_for_approved_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        decision = write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"

        payload = build_provider_config_apply_decision_consumer_write_guard_contract(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_write_guard_status"] == "ready_for_future_write_guard_but_real_write_disabled"
        assert payload["selected_decision_id"] == decision["decision_id"]
        assert payload["decision_record_validation"]["decision_record_consumable"] is True
        assert payload["consumer_record_digest_sha256"]
        preconditions = {item["id"]: item for item in payload["future_write_guard_preconditions"]}
        assert preconditions["consumer_writer_dry_run_ready"]["passed"] is True
        assert preconditions["single_approved_immutable_decision_selected"]["passed"] is True
        assert preconditions["real_write_enabled"]["status"] == "disabled_contract_only"
        assert payload["write_supported_now"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_record_mutated"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert not consumer_dir.exists()
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_write_guard_contract_flags_existing_marker() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text('{"status":"reserved_for_future_test"}\n', encoding="utf-8")
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR

        payload = build_provider_config_apply_decision_consumer_write_guard_contract(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_write_guard_status"] == "blocked_prior_apply_marker_exists"
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumer_directory_created"] is False
        assert payload["provider_config_mutated"] is False
        assert "provider_config_apply_idempotency_marker_exists" in payload["blocked_reasons"]
        assert not consumer_dir.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_write_guard_contract_cli_is_non_mutating(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-decision-consumer-write-guard-contract",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["consumer_write_guard_status"] == "blocked_consumer_writer_dry_run_not_ready"
        assert payload["execution_enabled"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["decision_consumer_record_written"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not consumer_dir.exists()
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_record_write_blocks_missing_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"

        try:
            write_provider_config_apply_decision_consumer_record(
                vault,
                proposal["proposal_id"],
                gate_approval_id=approval["gate_approval_id"],
                source_command="test",
            )
        except RuntimeProviderGovernanceError as exc:
            assert "provider config apply decision consumer record write blocked" in str(exc)
        else:
            raise AssertionError("consumer record write should block without immutable approved decision")

        assert not consumer_dir.exists()
        assert not marker_path.exists()
        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_decision_consumer_record_write_blocked" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_record_write_creates_only_consumer_record() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        decision = write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        payload = write_provider_config_apply_decision_consumer_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["consumer_write_status"] == "consumer_record_written_marker_handoff_required"
        assert payload["consumer_writer_status"] == "record_written"
        assert payload["selected_decision_id"] == decision["decision_id"]
        assert payload["decision_consumed"] is True
        assert payload["approval_consumed"] is False
        assert payload["decision_consumer_record_written"] is True
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["queue_drained"] is False
        assert payload["files_modified"] is True
        record_path = Path(payload["consumer_record_ref"])
        assert record_path.exists()
        record = json.loads(record_path.read_text(encoding="utf-8"))
        assert record["consumer_record_digest_sha256"]
        assert record["decision_consumed"] is True
        assert record["decision_record_mutated"] is False
        assert record["provider_config_mutated"] is False
        assert not marker_path.exists()
        assert not state_path.exists()
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")

        loaded_approval = json.loads(Path(approval["approval_ref"]).read_text(encoding="utf-8"))
        assert loaded_approval["status"] == "pending"
        assert loaded_approval["approval_consumed"] is False
        loaded_decision = json.loads(Path(decision["decision_ref"]).read_text(encoding="utf-8"))
        assert loaded_decision["decision_consumed"] is False

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_decision_consumer_record_written" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_record_write_is_create_new_only() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        first = write_provider_config_apply_decision_consumer_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )
        record_path = Path(first["consumer_record_ref"])
        before = record_path.read_text(encoding="utf-8")

        try:
            write_provider_config_apply_decision_consumer_record(
                vault,
                proposal["proposal_id"],
                gate_approval_id=approval["gate_approval_id"],
                source_command="test",
            )
        except RuntimeProviderGovernanceError as exc:
            assert "consumer record already exists" in str(exc)
        else:
            raise AssertionError("duplicate consumer record write should be blocked")

        assert record_path.read_text(encoding="utf-8") == before
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_record_cli_requires_write_flag(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        consumer_dir = vault / CONFIG_APPLY_CONSUMER_RELATIVE_DIR

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-decision-consumer",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--json",
                ]
            )
            == 1
        )
        assert "requires --write-consumer-record" in capsys.readouterr().err
        assert not consumer_dir.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_consumer_record_cli_writes_record_without_apply(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-decision-consumer",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--write-consumer-record",
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["consumer_write_status"] == "consumer_record_written_marker_handoff_required"
        assert payload["decision_consumer_record_written"] is True
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert Path(payload["consumer_record_ref"]).exists()
        assert not marker_path.exists()
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_atomic_marker_write_blocks_without_consumer_record() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"

        try:
            write_provider_config_apply_atomic_marker(
                vault,
                proposal["proposal_id"],
                gate_approval_id=approval["gate_approval_id"],
                source_command="test",
            )
        except RuntimeProviderGovernanceError as exc:
            assert "atomic marker write blocked" in str(exc)
            assert "provider_config_apply_consumer_record_missing" in str(exc)
        else:
            raise AssertionError("atomic marker write should require a consumer record")

        assert not marker_path.exists()
        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_atomic_marker_write_blocked" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_atomic_marker_write_creates_marker_without_apply() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        consumer = write_provider_config_apply_decision_consumer_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )
        consumer_path = Path(consumer["consumer_record_ref"])
        consumer_before = consumer_path.read_text(encoding="utf-8")
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        payload = write_provider_config_apply_atomic_marker(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["marker_write_status"] == "atomic_marker_written_apply_executor_handoff_required"
        assert payload["idempotency_marker_written"] is True
        assert payload["decision_consumer_record_written"] is True
        assert payload["consumer_record_mutated"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["queue_drained"] is False
        marker_path = Path(payload["marker_ref"])
        assert marker_path.exists()
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        assert marker["marker_digest_sha256"]
        assert marker["consumer_record_ref"] == str(consumer_path)
        assert marker["provider_config_mutated"] is False
        assert consumer_path.read_text(encoding="utf-8") == consumer_before
        assert not state_path.exists()
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_atomic_marker_written" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_atomic_marker_write_is_create_new_only() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        write_provider_config_apply_decision_consumer_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )
        first = write_provider_config_apply_atomic_marker(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )
        marker_path = Path(first["marker_ref"])
        before = marker_path.read_text(encoding="utf-8")

        try:
            write_provider_config_apply_atomic_marker(
                vault,
                proposal["proposal_id"],
                gate_approval_id=approval["gate_approval_id"],
                source_command="test",
            )
        except RuntimeProviderGovernanceError as exc:
            assert "idempotency_marker_exists" in str(exc)
        else:
            raise AssertionError("duplicate marker write should be blocked")

        assert marker_path.read_text(encoding="utf-8") == before
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_atomic_marker_cli_requires_marker_flag(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-atomic-marker-writer",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--json",
                ]
            )
            == 1
        )
        assert "requires --write-consumption-marker" in capsys.readouterr().err
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_atomic_marker_cli_writes_marker_without_apply(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        write_provider_config_apply_decision_consumer_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-atomic-marker-writer",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--write-consumption-marker",
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["marker_write_status"] == "atomic_marker_written_apply_executor_handoff_required"
        assert payload["idempotency_marker_written"] is True
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert Path(payload["marker_ref"]).exists()
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_atomic_marker_writer_design_blocks_missing_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        payload = build_provider_config_apply_atomic_marker_writer_design(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["writer_design_status"] == "blocked_decision_consumer_design_not_ready"
        assert payload["writer_status"] == "not_built"
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["marker_directory_created"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["idempotency"]["marker_path"] == str(marker_path)
        assert payload["idempotency"]["future_marker_write_mode"] == "atomic_create_new_only"
        assert payload["marker_record_template"]["writer_record_schema"] == (
            "rpgl.provider_config_apply_atomic_marker_writer.v1"
        )
        assert payload["path_constraints"]["overwrite_allowed"] is False
        assert payload["path_constraints"]["delete_on_failure_allowed"] is False
        assert "write only the sanitized marker JSON payload and flush it before any provider config or setup mutation" in payload["atomic_write_algorithm"]
        assert "secret" in payload["forbidden_marker_fields"]
        assert not marker_path.exists()
        assert not state_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_atomic_marker_writer_design_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_atomic_marker_writer_design_ready_for_approved_decision_without_write() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        decision = write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"

        payload = build_provider_config_apply_atomic_marker_writer_design(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["writer_design_status"] == "ready_for_future_atomic_marker_writer_but_writer_not_built"
        assert payload["selected_decision_id"] == decision["decision_id"]
        assert payload["idempotency"]["marker_exists"] is False
        assert payload["marker_record_template"]["selected_decision_id"] == decision["decision_id"]
        assert payload["marker_record_template"]["decision_digest_sha256"] == decision["decision_digest_sha256"]
        preconditions = {item["id"]: item for item in payload["future_writer_preconditions"]}
        assert preconditions["decision_consumption_plan_ready"]["passed"] is True
        assert preconditions["decision_consumer_design_ready"]["passed"] is True
        assert preconditions["atomic_marker_writer_implemented"]["status"] == "not_built"
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_atomic_marker_writer_design_flags_existing_marker() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text('{"status":"reserved_for_future_test"}\n', encoding="utf-8")

        payload = build_provider_config_apply_atomic_marker_writer_design(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["writer_design_status"] == "blocked_prior_apply_marker_exists"
        assert payload["idempotency"]["marker_exists"] is True
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert "provider_config_apply_idempotency_marker_exists" in payload["blocked_reasons"]
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_atomic_marker_writer_design_cli_is_non_mutating(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-atomic-marker-writer-design",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["writer_design_status"] == "blocked_decision_consumer_design_not_ready"
        assert payload["execution_enabled"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["consumption_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_decision_preflight_cli_is_non_mutating(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-decision-preflight",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["decision_consumption_status"] == "blocked_missing_immutable_decision_record"
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["approval_artifact_mutated"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_executor_dry_run_plan_blocks_pending_approval_without_apply() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        payload = build_provider_config_apply_executor_dry_run_plan(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["dry_run"] is True
        assert payload["dry_run_status"] == "blocked_blocked_missing_immutable_decision_record"
        assert payload["executor_status"] == "dry_run_plan_only"
        assert payload["live_apply_supported"] is False
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["approval_artifact_mutated"] is False
        assert payload["idempotency_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["queue_drained"] is False
        assert len(payload["dry_run_write_plan"]) == 2
        assert len(payload["rollback_snapshot"]) == 2
        planned_ids = {item["change_id"] for item in payload["dry_run_write_plan"]}
        assert planned_ids == {"openclaw-primary-model", "setup-openai-default-model"}
        assert payload["idempotency_marker_plan"]["marker_path"] == str(marker_path)
        assert payload["idempotency_marker_plan"]["write_enabled"] is False
        assert payload["feature_completion_tracker"]["can_call_feature_complete"] is False
        assert "live_provider_config_apply_executor" in payload["feature_completion_tracker"]["completed"]
        assert "live_provider_probe_executor" in payload["feature_completion_tracker"]["remaining_before_complete"]
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()
        assert not marker_path.exists()

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_executor_dry_run_requested" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_executor_dry_run_plan_for_approved_decision_record_still_no_live_apply() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )

        payload = build_provider_config_apply_executor_dry_run_plan(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["dry_run_status"] == "ready_for_dry_run_review_live_apply_not_enabled"
        assert payload["decision_preflight"]["approval_status"] == "pending"
        assert payload["decision_preflight"]["approval_decision_accepted"] is False
        assert payload["decision_preflight"]["immutable_decision_accepted"] is True
        assert payload["decision_preflight"]["decision_record_validation"]["decision_record_consumable"] is True
        assert payload["live_apply_supported"] is False
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["provider_config_mutated"] is False
        assert "provider_config_apply_live_executor_not_implemented" in payload["blocked_reasons"]
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_executor_dry_run_cli_is_non_mutating(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-executor-dry-run",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["dry_run"] is True
        assert payload["live_apply_supported"] is False
        assert payload["execution_enabled"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["idempotency_marker_written"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def _prepare_provider_config_apply_chain(vault: Path) -> tuple[dict, dict]:
    _write_provider_config_mismatch_fixture(vault)
    proposal = write_provider_config_change_approval_request(
        vault,
        requested_by="test-operator",
        source_command="test",
    )
    approval = write_provider_config_apply_approval_request(
        vault,
        proposal["proposal_id"],
        requested_by="test-operator",
        source_command="test",
    )
    write_provider_config_apply_approval_decision_record(
        vault,
        proposal["proposal_id"],
        gate_approval_id=approval["gate_approval_id"],
        decision="approved",
        decided_by="test-operator",
        reason="unit test approval",
        source_command="test",
    )
    write_provider_config_apply_decision_consumer_record(
        vault,
        proposal["proposal_id"],
        gate_approval_id=approval["gate_approval_id"],
        source_command="test",
    )
    write_provider_config_apply_atomic_marker(
        vault,
        proposal["proposal_id"],
        gate_approval_id=approval["gate_approval_id"],
        source_command="test",
    )
    return proposal, approval


def test_provider_config_apply_live_executor_blocks_without_marker() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )
        write_provider_config_apply_decision_consumer_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        try:
            write_provider_config_apply_live_executor(
                vault,
                proposal["proposal_id"],
                gate_approval_id=approval["gate_approval_id"],
                source_command="test",
            )
        except RuntimeProviderGovernanceError as exc:
            assert "live executor blocked" in str(exc)
            assert "provider_config_apply_idempotency_marker_missing" in str(exc)
        else:
            raise AssertionError("live executor should require an idempotency marker")

        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        result_path = vault / CONFIG_APPLY_RESULT_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        assert not result_path.exists()
        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_live_executor_blocked" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_live_executor_applies_targets_and_writes_result() -> None:
    vault = _make_vault()
    try:
        proposal, approval = _prepare_provider_config_apply_chain(vault)
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"
        setup_state_path = vault / "runtime" / "setup_state.json"
        provider_state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"

        payload = write_provider_config_apply_live_executor(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )

        assert payload["executor_status"] == "live_apply_completed"
        assert payload["apply_execution_allowed"] is True
        assert payload["result_record_written"] is True
        assert payload["provider_config_mutated"] is True
        assert payload["setup_state_mutated"] is True
        assert payload["provider_state_mutated"] is False
        assert payload["queue_drained"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["post_apply_verification_status"] == "passed"
        assert {item["change_id"] for item in payload["applied_writes"]} == {
            "openclaw-primary-model",
            "setup-openai-default-model",
        }
        assert "model_id: gpt-5.5" in model_config_path.read_text(encoding="utf-8")
        setup_state = json.loads(setup_state_path.read_text(encoding="utf-8"))
        assert setup_state["providers"]["openai"]["default_model"] == "gpt-5.5"
        assert not provider_state_path.exists()
        result_path = Path(payload["result_ref"])
        assert result_path.exists()
        result = json.loads(result_path.read_text(encoding="utf-8"))
        assert result["apply_result_status"] == "completed"
        assert result["result_digest_sha256"]

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_live_executor_started" in event_types
        assert "provider_config_apply_live_executor_completed" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_live_executor_is_result_create_new_only() -> None:
    vault = _make_vault()
    try:
        proposal, approval = _prepare_provider_config_apply_chain(vault)
        first = write_provider_config_apply_live_executor(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            source_command="test",
        )
        result_path = Path(first["result_ref"])
        before = result_path.read_text(encoding="utf-8")

        try:
            write_provider_config_apply_live_executor(
                vault,
                proposal["proposal_id"],
                gate_approval_id=approval["gate_approval_id"],
                source_command="test",
            )
        except RuntimeProviderGovernanceError as exc:
            assert "provider_config_apply_result_already_exists" in str(exc)
        else:
            raise AssertionError("duplicate live executor should be blocked by result record")

        assert result_path.read_text(encoding="utf-8") == before
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_live_executor_rolls_back_on_verification_failure() -> None:
    vault = _make_vault()
    original_verified = rpgl._provider_config_apply_target_verified
    try:
        proposal, approval = _prepare_provider_config_apply_chain(vault)
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"
        setup_state_path = vault / "runtime" / "setup_state.json"

        def fail_gpt55_verification(vault_root: str | Path, target: dict, expected_value: object) -> bool:
            if expected_value == "gpt-5.5":
                return False
            return original_verified(vault_root, target, expected_value)

        rpgl._provider_config_apply_target_verified = fail_gpt55_verification
        try:
            write_provider_config_apply_live_executor(
                vault,
                proposal["proposal_id"],
                gate_approval_id=approval["gate_approval_id"],
                source_command="test",
            )
        except RuntimeProviderGovernanceError as exc:
            assert "verification failed; rollback completed" in str(exc)
        else:
            raise AssertionError("verification failure should abort live apply")

        assert "model_id: claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        setup_state = json.loads(setup_state_path.read_text(encoding="utf-8"))
        assert setup_state["providers"]["openai"]["default_model"] == "set-by-wizard:openai"
        result_path = vault / CONFIG_APPLY_RESULT_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        assert not result_path.exists()
        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_rollback_completed" in event_types
        assert "provider_config_apply_live_executor_failed" in event_types
    finally:
        rpgl._provider_config_apply_target_verified = original_verified
        _cleanup_vault(vault)


def test_provider_config_apply_live_executor_cli_requires_apply_flag(capsys) -> None:
    vault = _make_vault()
    try:
        proposal, approval = _prepare_provider_config_apply_chain(vault)

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-executor",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--json",
                ]
            )
            == 1
        )
        assert "requires --apply-provider-config" in capsys.readouterr().err
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_live_executor_cli_applies_targets(capsys) -> None:
    vault = _make_vault()
    try:
        proposal, approval = _prepare_provider_config_apply_chain(vault)
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-executor",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--apply-provider-config",
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["executor_status"] == "live_apply_completed"
        assert payload["provider_config_mutated"] is True
        assert payload["setup_state_mutated"] is True
        assert Path(payload["result_ref"]).exists()
        assert "model_id: gpt-5.5" in model_config_path.read_text(encoding="utf-8")
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_approval_decision_preview_is_non_mutating() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        decision_path = vault / CONFIG_APPLY_DECISION_RELATIVE_DIR
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        payload = build_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )

        assert payload["record_type"] == "runtime_provider_config_apply_approval_decision"
        assert payload["decision"] == "approved"
        assert payload["decision_record_writable"] is True
        assert payload["decision_record_written"] is False
        assert payload["files_modified"] is False
        assert payload["approval_artifact_status_at_decision"] == "pending"
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["apply_execution_allowed"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["idempotency_marker_written"] is False
        assert payload["decision_digest_sha256"]
        assert not decision_path.exists()
        assert not marker_path.exists()
        assert not state_path.exists()
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_approval_decision_write_is_append_only_without_apply() -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"
        model_config_path = vault / "runtime" / "openclaw" / "model_config.yaml"

        payload = write_provider_config_apply_approval_decision_record(
            vault,
            proposal["proposal_id"],
            gate_approval_id=approval["gate_approval_id"],
            decision="approved",
            decided_by="test-operator",
            reason="unit test approval",
            source_command="test",
        )

        assert payload["decision_status"] == "recorded"
        assert payload["decision_record_written"] is True
        assert payload["files_modified"] is True
        assert Path(payload["decision_ref"]).exists()
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["provider_state_mutated"] is False
        assert payload["idempotency_marker_written"] is False
        assert "claude-sonnet-4-6" in model_config_path.read_text(encoding="utf-8")
        assert not state_path.exists()
        assert not marker_path.exists()

        loaded_approval = json.loads(Path(approval["approval_ref"]).read_text(encoding="utf-8"))
        assert loaded_approval["status"] == "pending"
        assert loaded_approval["approval_consumed"] is False

        try:
            write_provider_config_apply_approval_decision_record(
                vault,
                proposal["proposal_id"],
                gate_approval_id=approval["gate_approval_id"],
                decision="denied",
                decided_by="test-operator",
                reason="duplicate decision",
                source_command="test",
            )
        except RuntimeProviderGovernanceError as exc:
            assert "immutable_decision_already_exists" in str(exc)
        else:
            raise AssertionError("duplicate immutable approval decision should be blocked")

        event_types = [event["event_type"] for event in load_provider_audit_events(vault)]
        assert "provider_config_apply_approval_decision_previewed" in event_types
        assert "provider_config_apply_approval_decision_created" in event_types
    finally:
        _cleanup_vault(vault)


def test_provider_config_apply_approval_decision_cli_write_is_non_apply(capsys) -> None:
    vault = _make_vault()
    try:
        _write_provider_config_mismatch_fixture(vault)
        proposal = write_provider_config_change_approval_request(
            vault,
            requested_by="test-operator",
            source_command="test",
        )
        approval = write_provider_config_apply_approval_request(
            vault,
            proposal["proposal_id"],
            requested_by="test-operator",
            source_command="test",
        )
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        marker_path = vault / CONFIG_APPLY_MARKER_RELATIVE_DIR / f"{approval['gate_approval_id']}.json"

        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-apply-approval-decision",
                    proposal["proposal_id"],
                    "--vault-root",
                    str(vault),
                    "--gate-approval-id",
                    approval["gate_approval_id"],
                    "--decision",
                    "denied",
                    "--requested-by",
                    "test-operator",
                    "--reason",
                    "unit test denial",
                    "--write-decision",
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["decision"] == "denied"
        assert payload["decision_record_written"] is True
        assert payload["apply_execution_allowed"] is False
        assert payload["approval_consumed"] is False
        assert payload["decision_consumed"] is False
        assert payload["provider_config_mutated"] is False
        assert payload["setup_state_mutated"] is False
        assert payload["idempotency_marker_written"] is False
        assert Path(payload["decision_ref"]).exists()
        assert not state_path.exists()
        assert not marker_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_config_report_cli_is_read_only(capsys) -> None:
    vault = _make_vault()
    try:
        state_path = vault / "runtime" / "providers" / "state" / "provider_state.json"
        assert (
            cli.main(
                [
                    "runtime",
                    "provider",
                    "config-report",
                    "--vault-root",
                    str(vault),
                    "--json",
                ]
            )
            == 0
        )
        payload = _json_result(capsys.readouterr().out)
        assert payload["read_only"] is True
        assert payload["provider_state_mutated"] is False
        assert payload["model_config_mutated"] is False
        assert payload["live_network_call_attempted"] is False
        assert payload["secret_value_read"] is False
        assert not state_path.exists()
    finally:
        _cleanup_vault(vault)


def test_provider_inventory_reports_authority_matrix() -> None:
    vault = _make_vault()
    try:
        payload = build_provider_inventory(vault)
        assert payload["authority_matrix"]["repo_development"]["weak"] == "denied"
        assert payload["authority_matrix"]["summarize_failure"]["weak"] == "allowed"

        fallback = build_fallback_status(vault)["fallback_providers"][0]
        assert "repo_development" in fallback["denied_task_classes"]
        assert "summarize_failure" in fallback["active_for_task_classes"]
    finally:
        _cleanup_vault(vault)
