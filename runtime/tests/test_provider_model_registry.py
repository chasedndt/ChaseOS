"""Tests for Phase 9 runtime-shell provider/model registry."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402
from runtime.providers.registry import (  # noqa: E402
    load_provider_catalog,
    list_model_bindings,
    list_provider_status,
)


class TestProviderRegistryModule:
    def test_provider_catalog_loads(self) -> None:
        catalog = load_provider_catalog()
        provider_ids = [entry["id"] for entry in catalog]
        assert "claude" in provider_ids
        assert "openai" in provider_ids
        assert "local_oss" in provider_ids

    def test_provider_status_contains_validation_shape(self) -> None:
        statuses = list_provider_status()
        openai = next(item for item in statuses if item["provider_id"] == "openai")
        assert "configured" in openai
        assert "valid" in openai
        assert "checks" in openai
        assert isinstance(openai["checks"], list)

    def test_model_bindings_include_default_model_when_present(self) -> None:
        bindings = list_model_bindings()
        assert any(item["provider_id"] == "openai" for item in bindings)
        for item in bindings:
            assert "provider_id" in item
            assert "model_id" in item
            assert "configured" in item
            assert "primary" in item


class TestProviderRegistryCli:
    def test_providers_status_json(self, capsys) -> None:
        exit_code = cli.main(["providers", "status", "--json"])
        captured = capsys.readouterr()
        payload = json.loads(captured.out)

        assert exit_code == 0
        assert payload["ok"] is True
        assert payload["action"] == "providers.status"
        assert isinstance(payload["result"], list)
        assert any(item["provider_id"] == "claude" for item in payload["result"])

    def test_providers_list_json(self, capsys) -> None:
        exit_code = cli.main(["providers", "list", "--json"])
        captured = capsys.readouterr()
        payload = json.loads(captured.out)

        assert exit_code == 0
        assert payload["ok"] is True
        assert payload["action"] == "providers.list"
        assert isinstance(payload["result"], list)
        assert any(item["id"] == "openai" for item in payload["result"])

    def test_models_list_json(self, capsys) -> None:
        exit_code = cli.main(["models", "list", "--json"])
        captured = capsys.readouterr()
        payload = json.loads(captured.out)

        assert exit_code == 0
        assert payload["ok"] is True
        assert payload["action"] == "models.list"
        assert isinstance(payload["result"], list)
        assert any(item["provider_id"] == "openai" for item in payload["result"])

    def test_malformed_provider_registry_fails_clearly(self, tmp_path: Path, monkeypatch, capsys) -> None:
        bad_runtime_dir = tmp_path / "runtime"
        bad_runtime_dir.mkdir(parents=True)
        (bad_runtime_dir / "setup_registry.json").write_text(
            json.dumps({"providers": [{"id": "broken"}], "integrations": []}),
            encoding="utf-8",
        )
        (bad_runtime_dir / "setup_provider_profiles.json").write_text("{}", encoding="utf-8")
        (bad_runtime_dir / "setup_state.example.json").write_text(json.dumps({"providers": {}, "integrations": {}}), encoding="utf-8")
        monkeypatch.setattr("runtime.providers.registry.RUNTIME_DIR", bad_runtime_dir)
        monkeypatch.setattr("runtime.providers.registry.SETUP_REGISTRY", bad_runtime_dir / "setup_registry.json")
        monkeypatch.setattr("runtime.providers.registry.SETUP_PROVIDER_PROFILES", bad_runtime_dir / "setup_provider_profiles.json")
        monkeypatch.setattr("runtime.providers.registry.SETUP_STATE_EXAMPLE", bad_runtime_dir / "setup_state.example.json")
        monkeypatch.setattr("runtime.providers.registry.SETUP_STATE_PATH", bad_runtime_dir / "setup_state.json")

        with pytest.raises(ValueError, match="missing required fields"):
            load_provider_catalog()

        exit_code = cli.main(["providers", "list", "--json"])
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "missing required fields" in captured.err
