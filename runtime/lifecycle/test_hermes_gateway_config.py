"""Tests for safe Hermes gateway .env bootstrap/status helpers."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.lifecycle.hermes_gateway_config import (  # type: ignore
    ALLOWLIST_KEYS,
    MANAGED_BEGIN,
    MANAGED_END,
    apply_hermes_gateway_config,
    backup_hermes_gateway_config,
    build_hermes_gateway_config_plan,
    build_hermes_gateway_config_status,
    run_hermes_gateway_config_action,
)


def test_status_reports_missing_env_without_values(tmp_path):
    env_path = tmp_path / ".hermes" / ".env"

    status = build_hermes_gateway_config_status(env_path)

    assert status["ok"] is True
    assert status["env_present"] is False
    assert status["managed_block_present"] is False
    assert status["gateway_ready"] is False
    assert status["messaging_platform_status"] == "configured_but_disabled"
    assert status["allowlist_status"] == "missing"
    assert status["redaction_guard_passed"] is True


def test_status_prefers_explicit_chaseos_hermes_home(tmp_path, monkeypatch):
    hermes_home = tmp_path / "runtimes" / "hermes-home"
    monkeypatch.setenv("CHASEOS_HERMES_HOME", str(hermes_home))
    monkeypatch.delenv("HERMES_HOME", raising=False)

    status = build_hermes_gateway_config_status()

    assert status["env_path"] == str(hermes_home / ".env")
    assert status["env_present"] is False


def test_apply_creates_safe_managed_block_for_fresh_env(tmp_path):
    env_path = tmp_path / ".hermes" / ".env"

    result = apply_hermes_gateway_config(env_path, confirm=True)

    assert result["ok"] is True
    assert result["env_created"] is True
    text = env_path.read_text(encoding="utf-8")
    assert MANAGED_BEGIN in text
    assert MANAGED_END in text
    assert "GATEWAY_ALLOW_ALL_USERS=false" in text
    assert "GATEWAY_ALLOWED_USERS=" in text
    assert "DISCORD_ALLOWED_USERS=" in text
    assert "DISCORD_ALLOWED_CHANNELS=" in text
    assert "DISCORD_ALLOWED_GUILDS" not in text
    assert result["status"]["redaction_guard_passed"] is True


def test_apply_preserves_user_owned_lines_and_existing_values(tmp_path):
    env_path = tmp_path / ".hermes" / ".env"
    env_path.parent.mkdir(parents=True)
    env_path.write_text(
        "OPENROUTER_API_KEY=test-key-private\n"
        "DISCORD_BOT_TOKEN=bot-private\n"
        "DISCORD_ALLOWED_USERS=123456\n",
        encoding="utf-8",
    )

    result = apply_hermes_gateway_config(env_path, confirm=True)

    text = env_path.read_text(encoding="utf-8")
    assert "OPENROUTER_API_KEY=test-key-private" in text
    assert "DISCORD_BOT_TOKEN=bot-private" in text
    assert "DISCORD_ALLOWED_USERS=123456" in text
    assert result["env_created"] is False
    assert result["backup"]["backup_created"] is True
    assert result["status"]["platform_keys"]["DISCORD_BOT_TOKEN"]["configured"] is True
    assert result["status"]["allowlist_keys"]["DISCORD_ALLOWED_USERS"]["configured"] is True
    assert "123456" not in str(result)
    assert "bot-private" not in str(result)
    assert "test-key-private" not in str(result)


def test_apply_replaces_existing_managed_block_once(tmp_path):
    env_path = tmp_path / ".hermes" / ".env"
    env_path.parent.mkdir(parents=True)
    env_path.write_text(
        "USER_SETTING=keep\n\n"
        f"{MANAGED_BEGIN}\n"
        "GATEWAY_ALLOW_ALL_USERS=true\n"
        f"{MANAGED_END}\n"
        "AFTER=keep\n",
        encoding="utf-8",
    )

    result = apply_hermes_gateway_config(env_path, confirm=True)

    text = env_path.read_text(encoding="utf-8")
    assert result["managed_block_action"] == "updated"
    assert text.count(MANAGED_BEGIN) == 1
    assert text.count(MANAGED_END) == 1
    assert "USER_SETTING=keep" in text
    assert "AFTER=keep" in text
    assert "GATEWAY_ALLOW_ALL_USERS=true" in text


def test_backup_creates_copy_outside_repo_env_tree(tmp_path):
    env_path = tmp_path / ".hermes" / ".env"
    env_path.parent.mkdir(parents=True)
    env_path.write_text("DISCORD_ALLOWED_USERS=123\n", encoding="utf-8")

    result = backup_hermes_gateway_config(env_path)

    assert result["backup_created"] is True
    backup_path = Path(result["backup_path"])
    assert backup_path.exists()
    assert backup_path.read_text(encoding="utf-8") == "DISCORD_ALLOWED_USERS=123\n"
    assert backup_path.parent.parent == env_path.parent / "backups"


def test_status_parses_malformed_env_lines_without_leaking_values(tmp_path):
    env_path = tmp_path / ".hermes" / ".env"
    env_path.parent.mkdir(parents=True)
    env_path.write_text(
        "not-an-assignment\n"
        "DISCORD_BOT_TOKEN=secret-token\n"
        "DISCORD_ALLOWED_USERS=999999\n",
        encoding="utf-8",
    )

    status = build_hermes_gateway_config_status(env_path)

    assert status["platform_keys"]["DISCORD_BOT_TOKEN"]["configured"] is True
    assert status["allowlist_keys"]["DISCORD_ALLOWED_USERS"]["configured"] is True
    assert status["gateway_ready"] is True
    assert "secret-token" not in str(status)
    assert "999999" not in str(status)
    assert status["redaction_guard_passed"] is True


def test_plan_is_redacted_and_dynamic(tmp_path, monkeypatch):
    env_path = tmp_path / ".hermes" / ".env"
    monkeypatch.setenv("USER", "testuser")
    monkeypatch.setenv("WSL_DISTRO_NAME", "TestDistro")

    plan = build_hermes_gateway_config_plan(env_path)

    assert plan["action"] == "plan"
    assert plan["detected"]["posix_user"] == "testuser"
    assert plan["detected"]["wsl_distro"] == "TestDistro"
    assert plan["will_preserve_user_owned_lines"] is True
    assert plan["backup_required_before_apply"] is True
    assert plan["env_path"] == str(env_path)


def test_action_dispatch_and_unsupported_action(tmp_path):
    env_path = tmp_path / ".hermes" / ".env"

    assert run_hermes_gateway_config_action("status", env_path)["ok"] is True
    assert run_hermes_gateway_config_action("plan", env_path)["ok"] is True
    assert run_hermes_gateway_config_action("nope", env_path)["ok"] is False


def test_allowlist_key_set_uses_confirmed_discord_names_only():
    assert "GATEWAY_ALLOWED_USERS" in ALLOWLIST_KEYS
    assert "DISCORD_ALLOWED_USERS" in ALLOWLIST_KEYS
    assert "DISCORD_ALLOWED_CHANNELS" in ALLOWLIST_KEYS
    assert "DISCORD_ALLOWED_ROLES" in ALLOWLIST_KEYS
    assert "DISCORD_ALLOWED_GUILDS" not in ALLOWLIST_KEYS


def test_apply_requires_confirm_for_live_write(tmp_path):
    env_path = tmp_path / ".hermes" / ".env"

    result = apply_hermes_gateway_config(env_path)

    assert result["ok"] is False
    assert result["error"] == "confirm_required"
    assert not env_path.exists()


def test_apply_can_add_global_gateway_allowed_users_without_returning_values(tmp_path):
    env_path = tmp_path / ".hermes" / ".env"

    result = apply_hermes_gateway_config(
        env_path,
        allowed_users=["111", "222", "111"],
        confirm=True,
    )

    text = env_path.read_text(encoding="utf-8")
    assert "GATEWAY_ALLOWED_USERS=111,222" in text
    assert result["allowed_user_addition_count"] == 2
    assert "111" not in str(result)
    assert "222" not in str(result)
    assert result["approval_record"]["approval_recorded"] is True


def test_apply_can_use_chaseos_operator_binding_redacted(tmp_path):
    vault = tmp_path / "vault"
    binding = vault / ".chaseos" / "discord_instance_bindings.yaml"
    binding.parent.mkdir(parents=True)
    binding.write_text(
        "operator:\n"
        "  user_id: \"446420408367972372\"\n"
        "  display_name: Operator\n",
        encoding="utf-8",
    )
    env_path = tmp_path / ".hermes" / ".env"

    result = apply_hermes_gateway_config(
        env_path,
        vault_root=vault,
        use_chaseos_operator=True,
        confirm=True,
    )

    text = env_path.read_text(encoding="utf-8")
    assert "GATEWAY_ALLOWED_USERS=446420408367972372" in text
    assert result["chaseos_operator_binding"]["available"] is True
    assert result["chaseos_operator_binding"]["value_redacted"] is True
    assert "446420408367972372" not in str(result)
