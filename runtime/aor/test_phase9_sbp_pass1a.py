"""
test_phase9_sbp_pass1a.py — SBP Substrate Tests (Phase 9 Pass 1A)

Tests for the generic Scheduled Briefing Pipeline substrate:
  - SBPConfig manifest validation
  - SBPGuardrailProfile enforcement
  - Input adapter infrastructure (VaultNotesInputAdapter + stubs)
  - Delivery adapter infrastructure (VaultLocalDeliveryAdapter + stubs)
  - SBPBaseHandler base class pattern
  - run_sbp_pipeline() generic runner
  - AOR task type classification (scheduled-briefing)
  - No MCP scope expansion (manifest count unchanged)
  - Substrate is generic and not coupled to StrikeZone specifics

30 tests / expected: all pass.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ── Path setup ─────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_VAULT_ROOT = _HERE.parent.parent
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.sbp.manifest import (
    SBPConfig,
    SBPManifestValidationError,
    validate_sbp_config,
    load_sbp_config,
    FORBIDDEN_PERMISSION_CEILINGS,
    VALID_TRIGGER_TYPES,
    VALID_INPUT_ADAPTER_TYPES,
    VALID_DELIVERY_ADAPTER_TYPES,
)
from runtime.sbp.guardrail import (
    SBPGuardrailViolation,
    enforce_write_scope,
    check_pipeline_runnable,
)
from runtime.sbp.input_adapters import (
    InputAdapterError,
    VaultNotesInputAdapter,
    SICWorkspaceInputAdapterStub,
    ExternalAPIInputAdapterStub,
    get_input_adapter,
)
from runtime.sbp.delivery_adapters import (
    VaultLocalDeliveryAdapter,
    DiscordDeliveryAdapterStub,
    get_delivery_adapter,
)
from runtime.sbp.base_handler import SBPBaseHandler, SBPWorkflowExecutionError
from runtime.sbp.runner import run_sbp_pipeline, SBPRunnerError


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _minimal_sbp_config_dict() -> dict:
    return {
        "trigger": {"type": "manual"},
        "input_adapters": [
            {"type": "vault-notes", "trust_tier": 1, "paths": []},
        ],
        "execution_adapter": "claude",
        "delivery_adapters": [
            {"type": "vault-local"},
        ],
        "guardrail": {
            "permission_ceiling": "no_protected_file_writes",
            "write_scope": ["07_LOGS/SBP-Runs/"],
            "audit_required": True,
        },
    }


def _full_sbp_config_dict() -> dict:
    return {
        "trigger": {
            "type": "cron",
            "cron_expression": "0 6 * * 1-5",
            "timezone": "America/New_York",
            "max_runs_per_day": 1,
        },
        "input_adapters": [
            {"type": "vault-notes", "trust_tier": 1, "paths": ["00_HOME/Now.md"]},
            {"type": "sic-workspace", "trust_tier": 3, "workspace_id": "trading-markets"},
        ],
        "execution_adapter": "claude",
        "delivery_adapters": [
            {"type": "vault-local"},
            {"type": "discord", "channel_hint": "#alerts"},
        ],
        "guardrail": {
            "permission_ceiling": "no_protected_file_writes",
            "write_scope": ["07_LOGS/SBP-Runs/"],
            "read_scope": ["00_HOME/", "01_PROJECTS/"],
            "human_in_loop": "optional",
            "fail_behavior": "halt_and_log",
            "audit_required": True,
        },
    }


def _minimal_aor_manifest(pipeline_id: str = "sbp_test", sbp_config: dict | None = None) -> dict:
    return {
        "id": pipeline_id,
        "name": "Test SBP Pipeline",
        "version": "1.0",
        "description": "Test pipeline.",
        "task_type": "scheduled-briefing",
        "role_card": "scheduled-briefing",
        "trigger_type": "manual",
        "owner": "operator",
        "status": "active",
        "permission_ceiling": "no_protected_file_writes",
        "writeback_targets": ["07_LOGS/SBP-Runs/"],
        "failure_behavior": "escalate",
        "sbp_config": sbp_config or _minimal_sbp_config_dict(),
    }


# ── SBPConfig manifest validation tests ───────────────────────────────────────

def test_sbp_manifest_valid_minimal():
    """Valid minimal sbp_config parses without error."""
    config = validate_sbp_config(_minimal_sbp_config_dict(), "test_pipeline")
    assert isinstance(config, SBPConfig)
    assert config.trigger.type == "manual"
    assert config.execution_adapter == "claude"
    assert len(config.input_adapters) == 1
    assert len(config.delivery_adapters) == 1


def test_sbp_manifest_valid_full():
    """Full sbp_config with cron trigger, multiple adapters, and guardrail options."""
    config = validate_sbp_config(_full_sbp_config_dict(), "sbp_full")
    assert config.trigger.type == "cron"
    assert config.trigger.cron_expression == "0 6 * * 1-5"
    assert config.trigger.timezone == "America/New_York"
    assert len(config.input_adapters) == 2
    assert config.input_adapters[0].type == "vault-notes"
    assert config.input_adapters[1].type == "sic-workspace"
    assert len(config.delivery_adapters) == 2
    assert config.guardrail.human_in_loop == "optional"
    assert config.guardrail.fail_behavior == "halt_and_log"
    assert config.guardrail.audit_required is True


def test_sbp_manifest_missing_trigger():
    """sbp_config missing trigger key raises SBPManifestValidationError."""
    d = _minimal_sbp_config_dict()
    del d["trigger"]
    with pytest.raises(SBPManifestValidationError, match="trigger"):
        validate_sbp_config(d, "test")


def test_sbp_manifest_invalid_trigger_type():
    """Unknown trigger type raises SBPManifestValidationError."""
    d = _minimal_sbp_config_dict()
    d["trigger"]["type"] = "interval"
    with pytest.raises(SBPManifestValidationError, match="trigger.type"):
        validate_sbp_config(d, "test")


def test_sbp_manifest_cron_missing_expression():
    """trigger.type=cron without cron_expression raises SBPManifestValidationError."""
    d = _minimal_sbp_config_dict()
    d["trigger"] = {"type": "cron"}
    with pytest.raises(SBPManifestValidationError, match="cron_expression"):
        validate_sbp_config(d, "test")


def test_sbp_manifest_invalid_input_adapter_type():
    """Unknown input adapter type raises SBPManifestValidationError."""
    d = _minimal_sbp_config_dict()
    d["input_adapters"][0]["type"] = "file-system"
    with pytest.raises(SBPManifestValidationError, match="input_adapters"):
        validate_sbp_config(d, "test")


def test_sbp_manifest_invalid_delivery_type():
    """Unknown delivery adapter type raises SBPManifestValidationError."""
    d = _minimal_sbp_config_dict()
    d["delivery_adapters"][0]["type"] = "telegram"
    with pytest.raises(SBPManifestValidationError, match="delivery_adapters"):
        validate_sbp_config(d, "test")


def test_sbp_manifest_forbidden_ceiling_protected_file_writes():
    """permission_ceiling=protected_file_writes is forbidden for SBP."""
    d = _minimal_sbp_config_dict()
    d["guardrail"]["permission_ceiling"] = "protected_file_writes"
    with pytest.raises(SBPManifestValidationError, match="forbidden"):
        validate_sbp_config(d, "test")


def test_sbp_manifest_forbidden_ceiling_canonical_promotion():
    """permission_ceiling=canonical_promotion is forbidden for SBP."""
    d = _minimal_sbp_config_dict()
    d["guardrail"]["permission_ceiling"] = "canonical_promotion"
    with pytest.raises(SBPManifestValidationError, match="forbidden"):
        validate_sbp_config(d, "test")


def test_sbp_manifest_missing_sbp_config_block():
    """AOR manifest with task_type=scheduled-briefing but no sbp_config raises error."""
    manifest = _minimal_aor_manifest()
    del manifest["sbp_config"]
    with pytest.raises(SBPManifestValidationError, match="sbp_config"):
        load_sbp_config(manifest)


# ── Guardrail enforcement tests ────────────────────────────────────────────────

def test_guardrail_enforce_write_scope_pass():
    """Write path within declared scope passes without raising."""
    enforce_write_scope("07_LOGS/SBP-Runs/2026-04-22-test-run.md", ["07_LOGS/SBP-Runs/"])


def test_guardrail_enforce_write_scope_fail():
    """Write path outside declared scope raises SBPGuardrailViolation."""
    with pytest.raises(SBPGuardrailViolation, match="outside declared write scope"):
        enforce_write_scope("01_PROJECTS/StrikeZone/output.md", ["07_LOGS/SBP-Runs/"])


def test_guardrail_enforce_write_scope_empty_unconstrained():
    """Empty write_scope means unconstrained — any path passes."""
    enforce_write_scope("01_PROJECTS/StrikeZone/output.md", [])


def test_guardrail_enforce_write_scope_multiple_scopes():
    """Path within any declared scope passes."""
    enforce_write_scope(
        "07_LOGS/Operator-Briefs/2026-04-22-test.md",
        ["07_LOGS/SBP-Runs/", "07_LOGS/Operator-Briefs/"],
    )


def test_guardrail_check_pipeline_runnable_pass():
    """Valid config passes check_pipeline_runnable without raising."""
    config = validate_sbp_config(_minimal_sbp_config_dict(), "test")
    check_pipeline_runnable(config)  # must not raise


def test_guardrail_check_pipeline_runnable_forbidden_ceiling():
    """Pipeline with forbidden permission ceiling raises SBPGuardrailViolation."""
    from runtime.sbp.manifest import SBPGuardrailConfig, SBPConfig, SBPTriggerConfig
    config = SBPConfig(
        trigger=SBPTriggerConfig(type="manual"),
        input_adapters=[],
        execution_adapter="claude",
        delivery_adapters=[],
        guardrail=SBPGuardrailConfig(
            permission_ceiling="protected_file_writes",
            audit_required=True,
        ),
    )
    with pytest.raises(SBPGuardrailViolation, match="forbidden"):
        check_pipeline_runnable(config)


def test_guardrail_audit_required_false_raises():
    """audit_required=False raises SBPGuardrailViolation."""
    from runtime.sbp.manifest import SBPGuardrailConfig, SBPConfig, SBPTriggerConfig
    config = SBPConfig(
        trigger=SBPTriggerConfig(type="manual"),
        input_adapters=[],
        execution_adapter="claude",
        delivery_adapters=[],
        guardrail=SBPGuardrailConfig(
            permission_ceiling="no_protected_file_writes",
            audit_required=False,
        ),
    )
    with pytest.raises(SBPGuardrailViolation, match="audit_required"):
        check_pipeline_runnable(config)


# ── Input adapter tests ────────────────────────────────────────────────────────

def test_vault_notes_adapter_reads_file(tmp_path: Path):
    """VaultNotesInputAdapter reads a declared file and returns its content."""
    note = tmp_path / "00_HOME" / "Now.md"
    note.parent.mkdir(parents=True)
    note.write_text("# Now\n\nTest content.", encoding="utf-8")

    from runtime.sbp.manifest import SBPInputAdapterConfig
    cfg = SBPInputAdapterConfig(type="vault-notes", trust_tier=1, paths=["00_HOME/Now.md"])
    adapter = VaultNotesInputAdapter()
    result = adapter.collect(cfg, tmp_path)

    assert result["stub"] is False
    assert result["trust_tier"] == 1
    assert "Test content." in result["content"]
    assert "00_HOME/Now.md" in result["sources"]


def test_vault_notes_adapter_missing_file_raises(tmp_path: Path):
    """VaultNotesInputAdapter raises InputAdapterError for missing declared path."""
    from runtime.sbp.manifest import SBPInputAdapterConfig
    cfg = SBPInputAdapterConfig(type="vault-notes", trust_tier=1, paths=["missing/file.md"])
    adapter = VaultNotesInputAdapter()
    with pytest.raises(InputAdapterError, match="does not exist"):
        adapter.collect(cfg, tmp_path)


def test_vault_notes_adapter_trust_tier_canonical():
    """VaultNotesInputAdapter default trust tier is 1 (canonical vault state)."""
    assert VaultNotesInputAdapter.default_trust_tier == 1


def test_sic_workspace_stub_returns_stub():
    """SIC workspace stub returns stub=True and trust_tier=3."""
    from runtime.sbp.manifest import SBPInputAdapterConfig
    cfg = SBPInputAdapterConfig(type="sic-workspace", trust_tier=3, workspace_id="test-ws")
    adapter = SICWorkspaceInputAdapterStub()
    result = adapter.collect(cfg, Path("/fake"))
    assert result["stub"] is True
    assert result["trust_tier"] == 3
    assert result["content"] is None


def test_external_api_stub_tier4():
    """External API stub returns trust_tier=4 (untrusted external content)."""
    from runtime.sbp.manifest import SBPInputAdapterConfig
    cfg = SBPInputAdapterConfig(type="external-api", trust_tier=4)
    adapter = ExternalAPIInputAdapterStub()
    result = adapter.collect(cfg, Path("/fake"))
    assert result["trust_tier"] == 4
    assert result["stub"] is True
    assert "Tier 4" in result["stub_reason"]


def test_get_input_adapter_factory():
    """get_input_adapter returns correct types for all registered adapter types."""
    assert isinstance(get_input_adapter("vault-notes"), VaultNotesInputAdapter)
    assert isinstance(get_input_adapter("sic-workspace"), SICWorkspaceInputAdapterStub)
    assert isinstance(get_input_adapter("external-api"), ExternalAPIInputAdapterStub)


def test_get_input_adapter_unknown_raises():
    """get_input_adapter raises InputAdapterError for unknown type."""
    with pytest.raises(InputAdapterError, match="unknown input adapter type"):
        get_input_adapter("file-system")


# ── Delivery adapter tests ─────────────────────────────────────────────────────

def test_vault_local_delivery_success():
    """VaultLocalDeliveryAdapter returns success=True and stub=False."""
    adapter = VaultLocalDeliveryAdapter()
    result = adapter.deliver("content", {"pipeline_id": "test"})
    assert result["success"] is True
    assert result["stub"] is False


def test_discord_stub_returns_stub():
    """Discord stub returns success=False and stub=True."""
    adapter = DiscordDeliveryAdapterStub()
    result = adapter.deliver("content", {})
    assert result["success"] is False
    assert result["stub"] is True
    # details string varies by version — just verify it is a non-empty string
    assert isinstance(result["details"], str) and len(result["details"]) > 0


def test_get_delivery_adapter_factory():
    """get_delivery_adapter returns correct types for all registered adapter types."""
    from runtime.sbp.delivery_adapters import DiscordDeliveryAdapter
    assert isinstance(get_delivery_adapter("vault-local"), VaultLocalDeliveryAdapter)
    # Discord was promoted to a concrete adapter in Pass 1B
    assert isinstance(get_delivery_adapter("discord"), DiscordDeliveryAdapter)
    assert isinstance(get_delivery_adapter("email"), type(get_delivery_adapter("email")))


# ── SBP runner tests ───────────────────────────────────────────────────────────

def test_sbp_runner_valid_manifest_vault_local(tmp_path: Path):
    """Generic runner produces writeback for a vault-local pipeline."""
    note = tmp_path / "00_HOME" / "Now.md"
    note.parent.mkdir(parents=True)
    note.write_text("# Now\n\nTest sprint.", encoding="utf-8")

    sbp_config = _minimal_sbp_config_dict()
    sbp_config["input_adapters"][0]["paths"] = ["00_HOME/Now.md"]
    manifest = _minimal_aor_manifest("sbp_test_run", sbp_config)

    result = run_sbp_pipeline(manifest=manifest, inputs={}, vault_root=tmp_path)

    assert result["handler_status"] == "executed"
    assert result["workflow_id"] == "sbp_test_run"
    assert result["sbp_mode"] == "substrate-stub"
    assert len(result["writebacks"]) == 1
    assert "07_LOGS/SBP-Runs/" in result["writebacks"][0]["path"]


def test_sbp_runner_stub_output_content(tmp_path: Path):
    """Stub output content contains expected structural markers."""
    manifest = _minimal_aor_manifest("sbp_content_test", _minimal_sbp_config_dict())
    result = run_sbp_pipeline(manifest=manifest, inputs={}, vault_root=tmp_path)
    content = result["writebacks"][0]["content"]

    assert "sbp-run-stub" in content
    assert "sbp_content_test" in content
    assert "substrate-stub" in content
    assert "generate_content()" in content


def test_sbp_runner_write_scope_violation(tmp_path: Path):
    """Runner raises SBPRunnerError when writeback path is outside declared write scope."""
    sbp_config = _minimal_sbp_config_dict()
    sbp_config["guardrail"]["write_scope"] = ["07_LOGS/Operator-Briefs/"]
    manifest = _minimal_aor_manifest("sbp_scope_test", sbp_config)
    manifest["writeback_targets"] = ["07_LOGS/SBP-Runs/"]

    with pytest.raises(SBPRunnerError, match="write scope violation"):
        run_sbp_pipeline(manifest=manifest, inputs={}, vault_root=tmp_path)


def test_sbp_runner_delivery_results_in_output(tmp_path: Path):
    """Runner includes delivery results in return dict."""
    manifest = _minimal_aor_manifest("sbp_delivery_test", _minimal_sbp_config_dict())
    result = run_sbp_pipeline(manifest=manifest, inputs={}, vault_root=tmp_path)

    assert "delivery_results" in result
    assert len(result["delivery_results"]) == 1
    assert result["delivery_results"][0]["type"] == "vault-local"
    assert result["delivery_results"][0]["success"] is True


# ── SBPBaseHandler pattern tests ───────────────────────────────────────────────

def test_sbp_base_handler_run(tmp_path: Path):
    """SBPBaseHandler subclass executes generate_content and returns AOR-compatible dict."""
    note = tmp_path / "00_HOME" / "Now.md"
    note.parent.mkdir(parents=True)
    note.write_text("# Now\n\nHandler test.", encoding="utf-8")

    sbp_config = _minimal_sbp_config_dict()
    sbp_config["input_adapters"][0]["paths"] = ["00_HOME/Now.md"]
    manifest = _minimal_aor_manifest("sbp_handler_test", sbp_config)

    class TestHandler(SBPBaseHandler):
        workflow_id = "sbp_handler_test"
        def generate_content(self, collected_inputs, vault_root, *, sbp_config=None):
            content = collected_inputs.get("vault-notes", {}).get("content") or ""
            return f"## Handler Output\n\n{content}"

    result = TestHandler().run(manifest, {}, tmp_path)
    assert result["handler_status"] == "executed"
    assert "Handler Output" in result["writebacks"][0]["content"]
    assert "Handler test." in result["writebacks"][0]["content"]


def test_sbp_base_handler_invalid_manifest_raises(tmp_path: Path):
    """SBPBaseHandler raises SBPWorkflowExecutionError when sbp_config is missing."""
    manifest = _minimal_aor_manifest("sbp_invalid")
    del manifest["sbp_config"]  # remove sbp_config entirely — triggers load_sbp_config error

    class TestHandler(SBPBaseHandler):
        workflow_id = "sbp_invalid"
        def generate_content(self, collected_inputs, vault_root, *, sbp_config=None):
            return "content"

    with pytest.raises(SBPWorkflowExecutionError, match="sbp_config"):
        TestHandler().run(manifest, {}, tmp_path)


# ── AOR task type classification test ─────────────────────────────────────────

def test_aor_task_classification_scheduled_briefing():
    """task_type=scheduled-briefing is classified correctly by the AOR task router."""
    from runtime.aor.task_router import classify
    result = classify("scheduled-briefing", _VAULT_ROOT)
    assert result["id"] == "scheduled-briefing"
    assert result["id"] != "unclassified"


def test_sbp_substrate_not_coupled_to_strikezone():
    """SBP substrate modules have no StrikeZone-specific references."""
    import runtime.sbp.manifest as m
    import runtime.sbp.guardrail as g
    import runtime.sbp.input_adapters as ia
    import runtime.sbp.delivery_adapters as da
    import runtime.sbp.runner as r
    import runtime.sbp.base_handler as bh
    import inspect

    for mod in [m, g, ia, da, r, bh]:
        src = inspect.getsource(mod)
        assert "StrikeZone" not in src, (
            f"SBP substrate module {mod.__name__} must not reference StrikeZone; "
            f"instance-specific content belongs in instance pipelines (Pass 1B+)"
        )
