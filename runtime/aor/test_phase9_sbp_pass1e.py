"""
test_phase9_sbp_pass1e.py — Phase 9 SBP Pass 1E Tests

Covers:
  - runtime/execution_adapters/model_config.py (ModelSpec, RuntimeModelConfig, loader)
  - runtime/execution_adapters/execute.py (execute_synthesis, fallback chain, credential guard)
  - runtime/sbp/manifest.py (VALID_EXECUTION_ADAPTERS, validation gate)
  - runtime/sbp/base_handler.py (sbp_config kwarg threaded through to generate_content)
  - runtime/workflows/sbp_strikezone_digest.py (generate_content synthesis path)

All network calls are mocked. No live API calls in tests.
"""
from __future__ import annotations

import json
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

# ── Model config tests ─────────────────────────────────────────────────────────

from runtime.execution_adapters.model_config import (
    ModelSpec,
    RuntimeModelConfig,
    load_runtime_model_config,
    ModelConfigError,
)


class TestModelSpec:
    def test_basic_string_shorthand_via_parse(self):
        """ModelSpec from string shorthand (used when loading config)."""
        from runtime.execution_adapters.model_config import _parse_model_spec
        spec = _parse_model_spec("claude-sonnet-4-6", context="test")
        assert spec.model_id == "claude-sonnet-4-6"
        assert spec.max_tokens == 4096
        assert spec.temperature == 0.3

    def test_from_dict(self):
        from runtime.execution_adapters.model_config import _parse_model_spec
        spec = _parse_model_spec(
            {"model_id": "claude-opus-4-7", "max_tokens": 8192, "temperature": 0.1},
            context="test",
        )
        assert spec.model_id == "claude-opus-4-7"
        assert spec.max_tokens == 8192
        assert spec.temperature == 0.1

    def test_invalid_model_id_raises(self):
        with pytest.raises(ModelConfigError):
            ModelSpec(model_id="")

    def test_invalid_max_tokens_raises(self):
        with pytest.raises(ModelConfigError):
            ModelSpec(model_id="x", max_tokens=0)

    def test_invalid_temperature_raises(self):
        with pytest.raises(ModelConfigError):
            ModelSpec(model_id="x", temperature=3.0)

    def test_model_alias_field(self):
        from runtime.execution_adapters.model_config import _parse_model_spec
        spec = _parse_model_spec({"model": "claude-haiku-4-5"}, context="test")
        assert spec.model_id == "claude-haiku-4-5"


class TestRuntimeModelConfig:
    def test_all_models_yields_primary_then_fallbacks(self):
        primary = ModelSpec(model_id="primary-model")
        fb1 = ModelSpec(model_id="fallback-1")
        fb2 = ModelSpec(model_id="fallback-2")
        config = RuntimeModelConfig(runtime_name="test", primary=primary, fallbacks=[fb1, fb2])
        models = list(config.all_models())
        assert models[0].model_id == "primary-model"
        assert models[1].model_id == "fallback-1"
        assert models[2].model_id == "fallback-2"

    def test_no_fallbacks(self):
        primary = ModelSpec(model_id="only-model")
        config = RuntimeModelConfig(runtime_name="r", primary=primary)
        assert list(config.all_models()) == [primary]


class TestLoadRuntimeModelConfig:
    def _write_config(self, tmp: Path, name: str, content: str) -> Path:
        d = tmp / "runtime" / name
        d.mkdir(parents=True)
        cfg = d / "model_config.yaml"
        cfg.write_text(content, encoding="utf-8")
        return tmp

    def test_loads_openclaw_style_config(self, tmp_path):
        self._write_config(tmp_path, "openclaw", textwrap.dedent("""\
            runtime: openclaw
            primary:
              model_id: claude-sonnet-4-6
              max_tokens: 4096
              temperature: 0.3
            fallbacks:
              - model_id: claude-haiku-4-5-20251001
                max_tokens: 4096
                temperature: 0.3
        """))
        config = load_runtime_model_config("openclaw", tmp_path)
        assert config.runtime_name == "openclaw"
        assert config.primary.model_id == "claude-sonnet-4-6"
        assert len(config.fallbacks) == 1
        assert config.fallbacks[0].model_id == "claude-haiku-4-5-20251001"

    def test_loads_hermes_style_config(self, tmp_path):
        self._write_config(tmp_path, "hermes", textwrap.dedent("""\
            runtime: hermes
            primary:
              model_id: claude-opus-4-7
              max_tokens: 8192
              temperature: 0.2
            fallbacks:
              - model_id: claude-sonnet-4-6
                max_tokens: 8192
                temperature: 0.2
              - model_id: claude-haiku-4-5-20251001
                max_tokens: 4096
                temperature: 0.2
        """))
        config = load_runtime_model_config("hermes", tmp_path)
        assert config.primary.model_id == "claude-opus-4-7"
        assert len(config.fallbacks) == 2
        assert config.fallbacks[1].model_id == "claude-haiku-4-5-20251001"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(ModelConfigError, match="No model_config.yaml"):
            load_runtime_model_config("nonexistent", tmp_path)

    def test_missing_primary_raises(self, tmp_path):
        self._write_config(tmp_path, "test", "runtime: test\n")
        with pytest.raises(ModelConfigError, match="missing required 'primary'"):
            load_runtime_model_config("test", tmp_path)

    def test_string_shorthand_primary(self, tmp_path):
        self._write_config(tmp_path, "test", "primary: claude-sonnet-4-6\n")
        config = load_runtime_model_config("test", tmp_path)
        assert config.primary.model_id == "claude-sonnet-4-6"

    def test_empty_fallbacks_list(self, tmp_path):
        self._write_config(tmp_path, "test", "primary: claude-sonnet-4-6\nfallbacks: []\n")
        config = load_runtime_model_config("test", tmp_path)
        assert config.fallbacks == []


# ── Execution adapter tests ────────────────────────────────────────────────────

from runtime.execution_adapters.execute import (
    execute_synthesis,
    ExecutionAdapterError,
    ExecutionAdapterCredentialError,
    ADAPTER_TO_RUNTIME,
    SynthesisResult,
)


class TestAdapterToRuntime:
    def test_openclaw_resolves_to_openclaw(self):
        assert ADAPTER_TO_RUNTIME["openclaw"] == "openclaw"

    def test_hermes_resolves_to_hermes(self):
        assert ADAPTER_TO_RUNTIME["hermes"] == "hermes"

    def test_claude_resolves_to_openclaw(self):
        assert ADAPTER_TO_RUNTIME["claude"] == "openclaw"

    def test_unknown_adapter_raises(self, tmp_path):
        with pytest.raises(ExecutionAdapterError, match="Unknown execution_adapter"):
            execute_synthesis(
                prompt_system="sys",
                prompt_user="user",
                execution_adapter="unknown-runtime",
                vault_root=tmp_path,
            )


class TestCredentialGuard:
    def test_missing_api_key_raises_credential_error(self, tmp_path):
        """Missing ANTHROPIC_API_KEY raises non-retryable credential error."""
        self._write_openclaw_config(tmp_path)
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(ExecutionAdapterCredentialError, match="ANTHROPIC_API_KEY"):
                execute_synthesis(
                    prompt_system="sys",
                    prompt_user="user",
                    execution_adapter="openclaw",
                    vault_root=tmp_path,
                )

    def _write_openclaw_config(self, tmp: Path):
        d = tmp / "runtime" / "openclaw"
        d.mkdir(parents=True)
        (d / "model_config.yaml").write_text(
            "primary: claude-sonnet-4-6\nfallbacks:\n  - claude-haiku-4-5-20251001\n",
            encoding="utf-8",
        )


class TestExecuteSynthesisSuccess:
    def _write_openclaw_config(self, tmp: Path):
        d = tmp / "runtime" / "openclaw"
        d.mkdir(parents=True)
        (d / "model_config.yaml").write_text(
            "primary: claude-sonnet-4-6\nfallbacks:\n  - claude-haiku-4-5-20251001\n",
            encoding="utf-8",
        )

    def _mock_response(self, text: str, model: str = "claude-sonnet-4-6") -> dict:
        # _call_anthropic extracts text and returns {"text": ..., "usage": ...}
        return {"text": text, "usage": {"input_tokens": 100, "output_tokens": 200}}

    def test_successful_synthesis_returns_result(self, tmp_path):
        self._write_openclaw_config(tmp_path)
        mock_resp = self._mock_response("# Morning Brief\n\nGreat market today.")
        with patch("runtime.execution_adapters.execute._get_api_key", return_value="test-key"):
            with patch("runtime.execution_adapters.execute._call_anthropic", return_value=mock_resp):
                result = execute_synthesis(
                    prompt_system="sys",
                    prompt_user="user",
                    execution_adapter="openclaw",
                    vault_root=tmp_path,
                )
        assert isinstance(result, SynthesisResult)
        assert result.text == "# Morning Brief\n\nGreat market today."
        assert result.model_id == "claude-sonnet-4-6"
        assert result.runtime == "openclaw"
        assert result.fallback_used is False

    def test_claude_adapter_label_routes_to_openclaw(self, tmp_path):
        self._write_openclaw_config(tmp_path)
        mock_resp = self._mock_response("digest text")
        with patch("runtime.execution_adapters.execute._get_api_key", return_value="key"):
            with patch("runtime.execution_adapters.execute._call_anthropic", return_value=mock_resp):
                result = execute_synthesis(
                    prompt_system="s",
                    prompt_user="u",
                    execution_adapter="claude",
                    vault_root=tmp_path,
                )
        assert result.runtime == "openclaw"


class TestFallbackChain:
    def _write_openclaw_config(self, tmp: Path):
        d = tmp / "runtime" / "openclaw"
        d.mkdir(parents=True)
        (d / "model_config.yaml").write_text(
            "primary: claude-sonnet-4-6\nfallbacks:\n  - claude-haiku-4-5-20251001\n",
            encoding="utf-8",
        )

    def test_falls_back_to_second_model_on_primary_failure(self, tmp_path):
        self._write_openclaw_config(tmp_path)
        call_count = {"n": 0}

        def fake_call(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise ExecutionAdapterError("model failure")
            return {"text": "fallback text", "usage": {}}

        with patch("runtime.execution_adapters.execute._get_api_key", return_value="key"):
            with patch("runtime.execution_adapters.execute._call_anthropic", side_effect=fake_call):
                result = execute_synthesis(
                    prompt_system="s",
                    prompt_user="u",
                    execution_adapter="openclaw",
                    vault_root=tmp_path,
                )
        assert result.text == "fallback text"
        assert result.fallback_used is True
        assert result.model_id == "claude-haiku-4-5-20251001"
        assert call_count["n"] == 2

    def test_all_models_fail_raises(self, tmp_path):
        self._write_openclaw_config(tmp_path)
        with patch("runtime.execution_adapters.execute._get_api_key", return_value="key"):
            with patch(
                "runtime.execution_adapters.execute._call_anthropic",
                side_effect=ExecutionAdapterError("always fails"),
            ):
                with pytest.raises(ExecutionAdapterError, match="All 2 model"):
                    execute_synthesis(
                        prompt_system="s",
                        prompt_user="u",
                        execution_adapter="openclaw",
                        vault_root=tmp_path,
                    )

    def test_credential_error_does_not_try_fallback(self, tmp_path):
        self._write_openclaw_config(tmp_path)
        call_count = {"n": 0}

        def fake_call(**kwargs):
            call_count["n"] += 1
            raise ExecutionAdapterCredentialError("no key")

        with patch("runtime.execution_adapters.execute._get_api_key", return_value="key"):
            with patch("runtime.execution_adapters.execute._call_anthropic", side_effect=fake_call):
                with pytest.raises(ExecutionAdapterCredentialError):
                    execute_synthesis(
                        prompt_system="s",
                        prompt_user="u",
                        execution_adapter="openclaw",
                        vault_root=tmp_path,
                    )
        # Should have tried only once — credential errors don't retry
        assert call_count["n"] == 1


# ── SBP manifest execution_adapter validation ──────────────────────────────────

from runtime.sbp.manifest import validate_sbp_config, VALID_EXECUTION_ADAPTERS, SBPManifestValidationError


def _minimal_sbp_config(execution_adapter: str = "openclaw") -> dict:
    return {
        "trigger": {"type": "cron", "cron_expression": "0 6 * * 1-5"},
        "input_adapters": [{"type": "vault-notes", "trust_tier": 1}],
        "execution_adapter": execution_adapter,
        "delivery_adapters": [{"type": "vault-local"}],
        "guardrail": {
            "permission_ceiling": "no_protected_file_writes",
            "human_in_loop": "optional",
            "fail_behavior": "halt_and_log",
        },
    }


class TestManifestExecutionAdapterValidation:
    def test_openclaw_is_valid(self):
        cfg = validate_sbp_config(_minimal_sbp_config("openclaw"), "test")
        assert cfg.execution_adapter == "openclaw"

    def test_hermes_is_valid(self):
        cfg = validate_sbp_config(_minimal_sbp_config("hermes"), "test")
        assert cfg.execution_adapter == "hermes"

    def test_claude_legacy_is_valid(self):
        cfg = validate_sbp_config(_minimal_sbp_config("claude"), "test")
        assert cfg.execution_adapter == "claude"

    def test_unknown_adapter_raises(self):
        with pytest.raises(SBPManifestValidationError, match="not a known runtime"):
            validate_sbp_config(_minimal_sbp_config("openai"), "test")

    def test_empty_adapter_raises(self):
        with pytest.raises(SBPManifestValidationError):
            validate_sbp_config(_minimal_sbp_config(""), "test")

    def test_valid_adapters_set_contains_expected(self):
        assert "openclaw" in VALID_EXECUTION_ADAPTERS
        assert "hermes" in VALID_EXECUTION_ADAPTERS
        assert "claude" in VALID_EXECUTION_ADAPTERS


# ── base_handler sbp_config kwarg threading ────────────────────────────────────

from runtime.sbp.base_handler import SBPBaseHandler, SBPWorkflowExecutionError


class CapturingSBPHandler(SBPBaseHandler):
    """Test handler that captures what sbp_config it receives."""
    workflow_id = "test-capture-handler"
    received_sbp_config = None

    def generate_content(self, collected_inputs, vault_root, *, sbp_config=None):
        CapturingSBPHandler.received_sbp_config = sbp_config
        return "test-content"


class TestBaseHandlerSBPConfigThreading:
    def _write_minimal_vault(self, tmp: Path) -> dict:
        (tmp / "07_LOGS" / "SBP-Runs").mkdir(parents=True)
        return {
            "id": "test-capture-handler",
            "task_type": "scheduled-briefing",
            "sbp_config": {
                "trigger": {"type": "cron", "cron_expression": "0 6 * * 1-5"},
                "input_adapters": [],
                "execution_adapter": "openclaw",
                "delivery_adapters": [{"type": "vault-local"}],
                "guardrail": {
                    "permission_ceiling": "no_protected_file_writes",
                    "write_scope": ["07_LOGS/SBP-Runs/"],
                    "human_in_loop": "optional",
                    "fail_behavior": "halt_and_log",
                },
            },
        }

    def test_sbp_config_is_passed_to_generate_content(self, tmp_path):
        manifest = self._write_minimal_vault(tmp_path)
        CapturingSBPHandler.received_sbp_config = None
        handler = CapturingSBPHandler()
        with patch("runtime.sbp.base_handler.get_delivery_adapter") as mock_da:
            mock_da.return_value.deliver.return_value = {"success": True}
            handler.run(manifest, {}, tmp_path)
        assert CapturingSBPHandler.received_sbp_config is not None
        assert CapturingSBPHandler.received_sbp_config.execution_adapter == "openclaw"

    def test_generate_content_receives_valid_sbp_config(self, tmp_path):
        manifest = self._write_minimal_vault(tmp_path)
        CapturingSBPHandler.received_sbp_config = None
        handler = CapturingSBPHandler()
        with patch("runtime.sbp.base_handler.get_delivery_adapter") as mock_da:
            mock_da.return_value.deliver.return_value = {"success": True}
            handler.run(manifest, {}, tmp_path)
        from runtime.sbp.manifest import SBPConfig
        assert isinstance(CapturingSBPHandler.received_sbp_config, SBPConfig)


# ── StrikeZone digest handler synthesis path ───────────────────────────────────

from runtime.workflows.sbp_strikezone_digest import (
    StrikeZoneDigestHandler,
    _build_synthesis_prompt,
    _format_fallback_digest,
)


class TestBuildSynthesisPrompt:
    def test_returns_tuple_of_two_strings(self):
        sys_p, user_p = _build_synthesis_prompt(
            run_date="2026-04-24",
            system_section="Now section content",
            strikezone_section="StrikeZone content",
            acq_content="Live market data",
            acq_trust={"tier1_count": 2, "tier3_count": 1},
            acq_freshness={},
            acq_blocked=[],
        )
        assert isinstance(sys_p, str)
        assert isinstance(user_p, str)

    def test_system_prompt_contains_strikezone_identity(self):
        sys_p, _ = _build_synthesis_prompt(
            run_date="2026-04-24",
            system_section="",
            strikezone_section="",
            acq_content="",
            acq_trust={},
            acq_freshness={},
            acq_blocked=[],
        )
        assert "StrikeZone" in sys_p

    def test_user_prompt_contains_run_date(self):
        _, user_p = _build_synthesis_prompt(
            run_date="2026-04-24",
            system_section="",
            strikezone_section="",
            acq_content="",
            acq_trust={},
            acq_freshness={},
            acq_blocked=[],
        )
        assert "2026-04-24" in user_p

    def test_user_prompt_includes_acq_content_when_present(self):
        _, user_p = _build_synthesis_prompt(
            run_date="2026-04-24",
            system_section="",
            strikezone_section="",
            acq_content="Live BTC data here",
            acq_trust={"tier3_count": 1},
            acq_freshness={},
            acq_blocked=[],
        )
        assert "Live BTC data here" in user_p

    def test_user_prompt_handles_no_acq_content(self):
        _, user_p = _build_synthesis_prompt(
            run_date="2026-04-24",
            system_section="",
            strikezone_section="",
            acq_content="",
            acq_trust={},
            acq_freshness={},
            acq_blocked=[],
        )
        assert "vault context only" in user_p

    def test_stale_items_noted_in_prompt(self):
        _, user_p = _build_synthesis_prompt(
            run_date="2026-04-24",
            system_section="",
            strikezone_section="",
            acq_content="some data",
            acq_trust={},
            acq_freshness={"stale_items": ["s1", "s2"]},
            acq_blocked=[],
        )
        assert "stale" in user_p.lower()


class TestGenerateContentSynthesisPath:
    def _make_collected(self, now_content="now content", sz_content="strikezone content"):
        raw = f"# 00_HOME/Now.md\n\n{now_content}\n\n---\n\n# 01_PROJECTS/StrikeZone/StrikeZone-Crypto-OS.md\n\n{sz_content}"
        return {"vault-notes": {"content": raw}}

    def _mock_sbp_config(self, execution_adapter="openclaw"):
        cfg = MagicMock()
        cfg.execution_adapter = execution_adapter
        return cfg

    def test_synthesis_result_appears_in_output(self, tmp_path):
        collected = self._make_collected()
        handler = StrikeZoneDigestHandler()
        with patch("runtime.workflows.sbp_strikezone_digest.execute_synthesis") as mock_synth:
            mock_synth.return_value = SynthesisResult(
                text="# Synthesized Brief\n\nBTC: bullish",
                model_id="claude-sonnet-4-6",
                runtime="openclaw",
                usage={"input_tokens": 50, "output_tokens": 200},
                fallback_used=False,
            )
            result = handler.generate_content(
                collected, tmp_path, sbp_config=self._mock_sbp_config()
            )
        assert "# Synthesized Brief" in result
        assert "BTC: bullish" in result

    def test_synthesis_note_shows_runtime_and_model(self, tmp_path):
        collected = self._make_collected()
        handler = StrikeZoneDigestHandler()
        with patch("runtime.workflows.sbp_strikezone_digest.execute_synthesis") as mock_synth:
            mock_synth.return_value = SynthesisResult(
                text="brief content",
                model_id="claude-sonnet-4-6",
                runtime="openclaw",
                usage={},
                fallback_used=False,
            )
            result = handler.generate_content(
                collected, tmp_path, sbp_config=self._mock_sbp_config()
            )
        assert "openclaw" in result
        assert "claude-sonnet-4-6" in result

    def test_fallback_indicator_shown_when_fallback_used(self, tmp_path):
        collected = self._make_collected()
        handler = StrikeZoneDigestHandler()
        with patch("runtime.workflows.sbp_strikezone_digest.execute_synthesis") as mock_synth:
            mock_synth.return_value = SynthesisResult(
                text="fallback brief",
                model_id="claude-haiku-4-5-20251001",
                runtime="openclaw",
                usage={},
                fallback_used=True,
            )
            result = handler.generate_content(
                collected, tmp_path, sbp_config=self._mock_sbp_config()
            )
        assert "(fallback)" in result

    def test_synthesis_error_falls_back_to_formatted_dump(self, tmp_path):
        collected = self._make_collected()
        handler = StrikeZoneDigestHandler()
        with patch(
            "runtime.workflows.sbp_strikezone_digest.execute_synthesis",
            side_effect=ExecutionAdapterError("model unavailable"),
        ):
            result = handler.generate_content(
                collected, tmp_path, sbp_config=self._mock_sbp_config()
            )
        assert "Synthesis unavailable" in result
        assert "model unavailable" in result

    def test_credential_error_propagates(self, tmp_path):
        collected = self._make_collected()
        handler = StrikeZoneDigestHandler()
        with patch(
            "runtime.workflows.sbp_strikezone_digest.execute_synthesis",
            side_effect=ExecutionAdapterCredentialError("no ANTHROPIC_API_KEY"),
        ):
            with pytest.raises(ExecutionAdapterCredentialError):
                handler.generate_content(
                    collected, tmp_path, sbp_config=self._mock_sbp_config()
                )

    def test_uses_openclaw_default_when_no_sbp_config(self, tmp_path):
        collected = self._make_collected()
        handler = StrikeZoneDigestHandler()
        captured_adapter = {}
        def fake_synth(**kwargs):
            captured_adapter["execution_adapter"] = kwargs.get("execution_adapter")
            return SynthesisResult(
                text="text", model_id="m", runtime="openclaw", usage={}, fallback_used=False
            )
        with patch("runtime.workflows.sbp_strikezone_digest.execute_synthesis", side_effect=fake_synth):
            handler.generate_content(collected, tmp_path, sbp_config=None)
        assert captured_adapter["execution_adapter"] == "openclaw"

    def test_output_has_frontmatter_header(self, tmp_path):
        collected = self._make_collected()
        handler = StrikeZoneDigestHandler()
        with patch("runtime.workflows.sbp_strikezone_digest.execute_synthesis") as mock_synth:
            mock_synth.return_value = SynthesisResult(
                text="brief", model_id="m", runtime="openclaw", usage={}, fallback_used=False
            )
            result = handler.generate_content(
                collected, tmp_path, sbp_config=self._mock_sbp_config()
            )
        assert "pipeline_id: sbp_strikezone_digest" in result

    def test_output_has_footer(self, tmp_path):
        collected = self._make_collected()
        handler = StrikeZoneDigestHandler()
        with patch("runtime.workflows.sbp_strikezone_digest.execute_synthesis") as mock_synth:
            mock_synth.return_value = SynthesisResult(
                text="brief", model_id="m", runtime="openclaw", usage={}, fallback_used=False
            )
            result = handler.generate_content(
                collected, tmp_path, sbp_config=self._mock_sbp_config()
            )
        assert "Generated by ChaseOS SBP" in result


# ── Real model_config.yaml file validation ─────────────────────────────────────

class TestRealModelConfigFiles:
    """Validate the actual openclaw/hermes model_config.yaml files are well-formed."""

    def _vault_root(self) -> Path:
        """Resolve vault root relative to this test file."""
        return Path(__file__).parent.parent.parent

    def test_openclaw_config_loads(self):
        config = load_runtime_model_config("openclaw", self._vault_root())
        assert bool(config.primary.model_id)
        assert config.primary.max_tokens > 0
        assert 0.0 <= config.primary.temperature <= 2.0

    def test_openclaw_has_at_least_one_fallback(self):
        config = load_runtime_model_config("openclaw", self._vault_root())
        assert len(config.fallbacks) >= 1

    def test_hermes_config_loads(self):
        config = load_runtime_model_config("hermes", self._vault_root())
        assert bool(config.primary.model_id)

    def test_hermes_has_at_least_one_fallback(self):
        config = load_runtime_model_config("hermes", self._vault_root())
        assert len(config.fallbacks) >= 1

    def test_openclaw_fallback_different_from_primary(self):
        config = load_runtime_model_config("openclaw", self._vault_root())
        for fb in config.fallbacks:
            assert fb.model_id != config.primary.model_id

    def test_hermes_fallback_chain_ordered(self):
        config = load_runtime_model_config("hermes", self._vault_root())
        models = list(config.all_models())
        model_ids = [m.model_id for m in models]
        assert len(model_ids) == len(set(model_ids)), "fallback chain contains duplicate model IDs"


# ── Real sbp_strikezone_digest.yaml execution_adapter field ───────────────────

class TestRealManifestExecutionAdapter:
    def _vault_root(self) -> Path:
        return Path(__file__).parent.parent.parent

    def test_manifest_has_openclaw_execution_adapter(self):
        manifest_path = (
            self._vault_root()
            / "runtime" / "workflows" / "registry" / "sbp_strikezone_digest.yaml"
        )
        assert manifest_path.exists(), f"Manifest not found: {manifest_path}"
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        sbp = raw.get("sbp_config", {})
        assert sbp.get("execution_adapter") == "openclaw"

    def test_manifest_validates_cleanly(self):
        manifest_path = (
            self._vault_root()
            / "runtime" / "workflows" / "registry" / "sbp_strikezone_digest.yaml"
        )
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        sbp_config_dict = raw.get("sbp_config", {})
        cfg = validate_sbp_config(sbp_config_dict, raw.get("id", "test"))
        assert cfg.execution_adapter == "openclaw"
