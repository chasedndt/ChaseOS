from __future__ import annotations

import argparse
import json

import runtime.setup_cli as setup_cli


PROFILE = {
    "secret_reference_kind": "env-var-or-local-secret-ref",
    "validation_checks": ["api_key_present", "model_selected", "secret_reference_present"],
}


def _configured_state(target: str) -> dict:
    return {
        "configured": True,
        "api_key_present": True,
        "model_selected": True,
        "secret_reference_present": True,
        "secret_reference_kind": "env-var-or-local-secret-ref",
        "secret_reference_target": target,
    }


def test_provider_validation_fails_when_secret_reference_does_not_resolve(monkeypatch) -> None:
    monkeypatch.delenv("SET_OPENAI_SECRET_REF", raising=False)

    payload = setup_cli._validate_provider("openai", PROFILE, _configured_state("SET_OPENAI_SECRET_REF"))

    assert payload["valid"] is False
    assert "secret_reference_resolvable" in payload["missing"]
    assert {"check": "secret_reference_resolvable", "passed": False} in payload["checks"]
    assert payload["secret_reference_target_is_placeholder"] is True
    assert payload["secret_reference_resolvable"] is False
    assert payload["secret_reference_probe_source"] == "env-var-or-local-secret-ref"
    assert payload["secret_reference_probe_error"] == "reference_not_found"
    assert payload["secret_reference_probe"]["exists"] is False
    assert payload["secret_reference_probe"]["error"] == "reference_not_found"
    assert payload["safe_to_call_update_goal_complete"] is False
    assert payload["no_safe_autonomous_completion_pass_available"] is True
    assert payload["update_goal_allowed"] is False
    assert payload["next_operator_action_id"] == "openai_secret_reference"
    assert payload["next_recommended_pass"] == "operator-provide-openai-secret-reference"


def test_provider_validation_passes_when_env_reference_resolves_without_leaking_value(monkeypatch) -> None:
    secret_value = "test-key-test-value-that-must-not-appear"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)

    payload = setup_cli._validate_provider("openai", PROFILE, _configured_state("OPENAI_API_KEY"))
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["valid"] is True
    assert payload["missing"] == []
    assert {"check": "secret_reference_resolvable", "passed": True} in payload["checks"]
    assert payload["secret_reference_target_is_placeholder"] is False
    assert payload["secret_reference_resolvable"] is True
    assert payload["secret_reference_probe_source"] == "env-var"
    assert payload["secret_reference_probe_error"] is None
    assert payload["secret_reference_probe"]["exists"] is True
    assert payload["secret_reference_probe"]["source"] == "env-var"
    assert payload["safe_to_call_update_goal_complete"] is False
    assert payload["no_safe_autonomous_completion_pass_available"] is False
    assert payload["update_goal_allowed"] is False
    assert payload["next_operator_action_id"] == "provider-live-probe-after-secret-reference"
    assert payload["next_recommended_pass"] == "provider-live-probe-after-secret-reference"
    assert secret_value not in serialized


def test_provider_validate_cli_exits_nonzero_for_missing_secret_reference(monkeypatch, capsys) -> None:
    monkeypatch.delenv("SET_OPENAI_SECRET_REF", raising=False)
    monkeypatch.setattr(
        setup_cli,
        "load_setup_registry",
        lambda: {"providers": [{"id": "openai"}]},
    )
    monkeypatch.setattr(setup_cli, "load_provider_profiles", lambda: {"openai": PROFILE})
    monkeypatch.setattr(
        setup_cli,
        "load_setup_state",
        lambda: {"providers": {"openai": _configured_state("SET_OPENAI_SECRET_REF")}},
    )
    args = argparse.Namespace(setup_command="validate", target_id="openai", json=True)

    exit_code = setup_cli.cmd_provider(args)
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["valid"] is False
    assert "secret_reference_resolvable" in payload["missing"]
    assert payload["secret_reference_target"] == "SET_OPENAI_SECRET_REF"
    assert payload["secret_reference_target_is_placeholder"] is True
    assert payload["secret_reference_resolvable"] is False
    assert payload["secret_reference_probe_source"] == "env-var-or-local-secret-ref"
    assert payload["secret_reference_probe_error"] == "reference_not_found"
    assert payload["safe_to_call_update_goal_complete"] is False
    assert payload["no_safe_autonomous_completion_pass_available"] is True
    assert payload["update_goal_allowed"] is False
    assert payload["next_operator_action_id"] == "openai_secret_reference"
    assert payload["next_recommended_pass"] == "operator-provide-openai-secret-reference"
