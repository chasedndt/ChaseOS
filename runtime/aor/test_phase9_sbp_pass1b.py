"""
test_phase9_sbp_pass1b.py — SBP Pass 1B Tests (Phase 9)

Tests for the StrikeZone Market Digest Publisher instance pipeline:
  - Instance manifest validation
  - StrikeZoneDigestHandler happy path
  - Real vault-notes input collection
  - Real DiscordDeliveryAdapter behaviour (no-credential path + mock delivery)
  - Bounded output / write target correctness
  - Schedule intent alignment
  - No canonical state mutation
  - MCP scope unchanged

34 tests / expected: all pass.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest.mock
from pathlib import Path

import pytest
import yaml

# ── Path setup ─────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_VAULT_ROOT = _HERE.parent.parent
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.sbp.manifest import validate_sbp_config, load_sbp_config, SBPManifestValidationError
from runtime.sbp.input_adapters import (
    VaultNotesInputAdapter,
    AcquisitionPackInputAdapter,
    SBPInputAdapterConfig,
    InputAdapterError,
)
from runtime.sbp.delivery_adapters import (
    DiscordDeliveryAdapter,
    DiscordDeliveryAdapterStub,
    get_delivery_adapter,
)
from runtime.sbp.base_handler import SBPWorkflowExecutionError
from runtime.workflows.sbp_strikezone_digest import (
    StrikeZoneDigestHandler,
    run_sbp_strikezone_digest,
    WorkflowExecutionError,
    _extract_section,
    _format_trust_line,
)
from runtime.aor.engine import run_workflow


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_manifest_yaml() -> dict:
    path = _VAULT_ROOT / "runtime" / "workflows" / "registry" / "sbp_strikezone_digest.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_schedule_yaml() -> dict:
    path = _VAULT_ROOT / "runtime" / "schedules" / "sch-sbp-strikezone-digest-0600.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _minimal_manifest() -> dict:
    """Minimal AOR manifest for unit tests (does not load from disk)."""
    return {
        "id": "sbp_strikezone_digest",
        "task_type": "scheduled-briefing",
        "role_card": "scheduled-briefing",
        "writeback_targets": ["07_LOGS/SBP-Runs/"],
        "sbp_config": {
            "trigger": {"type": "manual"},
            "input_adapters": [
                {"type": "vault-notes", "trust_tier": 1, "paths": []},
            ],
            "execution_adapter": "claude",
            "delivery_adapters": [
                {"type": "vault-local"},
                {"type": "discord", "channel_hint": "#strikezone-signals"},
            ],
            "guardrail": {
                "permission_ceiling": "no_protected_file_writes",
                "write_scope": ["07_LOGS/SBP-Runs/"],
                "audit_required": True,
            },
        },
    }


# ── 1. Instance manifest validation ───────────────────────────────────────────

class TestInstanceManifest:

    def test_manifest_file_exists(self):
        path = _VAULT_ROOT / "runtime" / "workflows" / "registry" / "sbp_strikezone_digest.yaml"
        assert path.exists(), "sbp_strikezone_digest.yaml must exist in registry"

    def test_manifest_status_active(self):
        m = _load_manifest_yaml()
        assert m["status"] == "active"

    def test_manifest_task_type_scheduled_briefing(self):
        m = _load_manifest_yaml()
        assert m["task_type"] == "scheduled-briefing"

    def test_manifest_sbp_config_validates(self):
        m = _load_manifest_yaml()
        sbp = load_sbp_config(m)
        assert sbp.guardrail.permission_ceiling == "no_protected_file_writes"

    def test_manifest_writeback_targets_within_role_card_scope(self):
        m = _load_manifest_yaml()
        for target in m.get("writeback_targets", []):
            assert target.startswith("07_LOGS/"), (
                f"writeback target '{target}' is outside role card write_scope"
            )

    def test_manifest_id_matches_filename(self):
        m = _load_manifest_yaml()
        assert m["id"] == "sbp_strikezone_digest"

    def test_manifest_write_scope_sbp_runs_only(self):
        m = _load_manifest_yaml()
        sbp = load_sbp_config(m)
        for scope in sbp.guardrail.write_scope:
            assert "07_LOGS/SBP-Runs" in scope, (
                f"write_scope '{scope}' outside expected SBP-Runs target"
            )


# ── 2. Handler tests ───────────────────────────────────────────────────────────

class TestStrikeZoneDigestHandler:

    def test_handler_is_importable(self):
        assert StrikeZoneDigestHandler is not None

    def test_handler_workflow_id(self):
        h = StrikeZoneDigestHandler()
        assert h.workflow_id == "sbp_strikezone_digest"

    def test_generate_content_returns_string(self):
        h = StrikeZoneDigestHandler()
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            result = h.generate_content(collected_inputs={}, vault_root=vault)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_generate_content_includes_date(self):
        from datetime import date
        h = StrikeZoneDigestHandler()
        with tempfile.TemporaryDirectory() as tmp:
            result = h.generate_content({}, Path(tmp))
            assert date.today().isoformat() in result

    def test_generate_content_includes_pipeline_id(self):
        h = StrikeZoneDigestHandler()
        with tempfile.TemporaryDirectory() as tmp:
            result = h.generate_content({}, Path(tmp))
            assert "sbp_strikezone_digest" in result

    def test_generate_content_with_vault_notes_content(self):
        h = StrikeZoneDigestHandler()
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            fake_content = "# 00_HOME/Now.md\n\n## Current Phase\nPhase 9 ACTIVE"
            collected = {"vault-notes": {"content": fake_content, "trust_tier": 1, "sources": []}}
            result = h.generate_content(collected, vault)
            assert "System Context" in result or "Phase 9" in result

    def test_run_returns_handler_status_executed(self):
        manifest = _minimal_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, Path(tmp))
        assert result["handler_status"] == "executed"

    def test_run_returns_writebacks(self):
        manifest = _minimal_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, Path(tmp))
        assert len(result["writebacks"]) >= 1

    def test_run_writeback_path_within_sbp_runs(self):
        manifest = _minimal_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, Path(tmp))
        for wb in result["writebacks"]:
            assert "07_LOGS/SBP-Runs" in wb["path"]

    def test_run_delivery_results_contains_vault_local(self):
        manifest = _minimal_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, Path(tmp))
        types = [d["type"] for d in result["delivery_results"]]
        assert "vault-local" in types

    def test_run_delivery_results_contains_discord(self):
        manifest = _minimal_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, Path(tmp))
        types = [d["type"] for d in result["delivery_results"]]
        assert "discord" in types

    def test_run_no_manifest_raises(self):
        with pytest.raises(WorkflowExecutionError):
            run_sbp_strikezone_digest(inputs={}, vault_root=Path("."), manifest=None)

    def test_run_writeback_content_is_string(self):
        manifest = _minimal_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, Path(tmp))
        for wb in result["writebacks"]:
            assert isinstance(wb["content"], str)


# ── 3. Vault-notes input collection ───────────────────────────────────────────

class TestVaultNotesInputForInstance:

    def test_vault_notes_reads_now_md(self):
        adapter = VaultNotesInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            now_path = vault / "00_HOME" / "Now.md"
            now_path.parent.mkdir(parents=True)
            now_path.write_text("# Test Now\nPhase 9 test content", encoding="utf-8")
            cfg = SBPInputAdapterConfig(type="vault-notes", trust_tier=1, paths=["00_HOME/Now.md"])
            result = adapter.collect(cfg, vault)
        assert result["stub"] is False
        assert result["trust_tier"] == 1
        assert "Phase 9 test content" in (result["content"] or "")

    def test_vault_notes_reads_strikezone_os(self):
        adapter = VaultNotesInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            sz_path = vault / "01_PROJECTS" / "StrikeZone" / "StrikeZone-Crypto-OS.md"
            sz_path.parent.mkdir(parents=True)
            sz_path.write_text("# StrikeZone\nLive signal community", encoding="utf-8")
            cfg = SBPInputAdapterConfig(
                type="vault-notes", trust_tier=1,
                paths=["01_PROJECTS/StrikeZone/StrikeZone-Crypto-OS.md"]
            )
            result = adapter.collect(cfg, vault)
        assert "Live signal community" in (result["content"] or "")

    def test_vault_notes_raises_on_missing_path(self):
        adapter = VaultNotesInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            cfg = SBPInputAdapterConfig(
                type="vault-notes", trust_tier=1,
                paths=["missing/file.md"]
            )
            from runtime.sbp.input_adapters import InputAdapterError
            with pytest.raises(InputAdapterError):
                adapter.collect(cfg, Path(tmp))

    def test_vault_notes_trust_tier_is_1(self):
        adapter = VaultNotesInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            f = vault / "test.md"
            f.write_text("test", encoding="utf-8")
            cfg = SBPInputAdapterConfig(type="vault-notes", trust_tier=1, paths=["test.md"])
            result = adapter.collect(cfg, vault)
        assert result["trust_tier"] == 1

    def test_collected_inputs_structure(self):
        manifest = _minimal_manifest()
        # inject a real vault-notes path
        manifest["sbp_config"]["input_adapters"][0]["paths"] = []
        with tempfile.TemporaryDirectory() as tmp:
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, Path(tmp))
        assert "input_adapters_used" in result
        assert "vault-notes" in result["input_adapters_used"]


# ── 4. Discord delivery adapter tests ─────────────────────────────────────────

class TestDiscordDeliveryAdapter:

    def test_discord_adapter_is_concrete_not_stub(self):
        adapter = get_delivery_adapter("discord")
        assert isinstance(adapter, DiscordDeliveryAdapter)
        assert not isinstance(adapter, DiscordDeliveryAdapterStub)

    def test_discord_adapter_stub_false(self):
        adapter = DiscordDeliveryAdapter()
        env = {k: v for k, v in os.environ.items() if k != "DISCORD_WEBHOOK_URL"}
        with unittest.mock.patch.dict(os.environ, env, clear=True):
            result = adapter.deliver("test", {"pipeline_id": "sbp_test"})
        assert result["stub"] is False

    def test_discord_no_env_var_returns_success_false(self):
        adapter = DiscordDeliveryAdapter()
        env = {k: v for k, v in os.environ.items() if k != "DISCORD_WEBHOOK_URL"}
        with unittest.mock.patch.dict(os.environ, env, clear=True):
            result = adapter.deliver("test content", {"pipeline_id": "sbp_test"})
        assert result["success"] is False
        assert "DISCORD_WEBHOOK_URL" in result["details"]

    def test_discord_no_env_var_details_is_string(self):
        adapter = DiscordDeliveryAdapter()
        env = {k: v for k, v in os.environ.items() if k != "DISCORD_WEBHOOK_URL"}
        with unittest.mock.patch.dict(os.environ, env, clear=True):
            result = adapter.deliver("test", {})
        assert isinstance(result["details"], str)
        assert len(result["details"]) > 0

    def test_discord_with_webhook_sends_json_payload(self):
        adapter = DiscordDeliveryAdapter()

        class _MockResp:
            status = 204

            def __enter__(self): return self
            def __exit__(self, *a): pass

        with unittest.mock.patch.dict(os.environ, {"DISCORD_WEBHOOK_URL": "https://mock.discord.test/webhook"}):
            with unittest.mock.patch("urllib.request.urlopen", return_value=_MockResp()) as mock_open:
                result = adapter.deliver("Hello digest", {"pipeline_id": "sbp_strikezone_digest", "date": "2026-04-22"})

        assert result["success"] is True
        assert result["stub"] is False
        call_args = mock_open.call_args
        req = call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        assert "embeds" in payload
        assert "sbp_strikezone_digest" in payload["embeds"][0]["title"]

    def test_discord_stub_class_still_exists(self):
        stub = DiscordDeliveryAdapterStub()
        result = stub.deliver("test", {})
        assert result["stub"] is True


# ── 5. Bounded output / write target ─────────────────────────────────────────

class TestWriteTargetCorrectness:

    def test_writeback_not_in_projects(self):
        manifest = _minimal_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, Path(tmp))
        for wb in result["writebacks"]:
            assert not wb["path"].startswith("01_PROJECTS/"), (
                f"writeback path '{wb['path']}' must not write to 01_PROJECTS/"
            )

    def test_writeback_not_in_knowledge(self):
        manifest = _minimal_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, Path(tmp))
        for wb in result["writebacks"]:
            assert not wb["path"].startswith("02_KNOWLEDGE/"), (
                f"writeback path '{wb['path']}' must not write to 02_KNOWLEDGE/"
            )

    def test_aor_dry_run_returns_dry_run_ok(self):
        result = run_workflow(
            "sbp_strikezone_digest",
            inputs={},
            vault_root=_VAULT_ROOT,
            dry_run=True,
        )
        assert result.status == "dry_run_ok"

    def test_sbp_config_write_scope_no_protected_files(self):
        m = _load_manifest_yaml()
        sbp = load_sbp_config(m)
        for scope in sbp.guardrail.write_scope:
            for protected in ["SOUL.md", "CLAUDE.md", "ROADMAP.md", "02_KNOWLEDGE", "01_PROJECTS"]:
                assert protected not in scope, (
                    f"write_scope '{scope}' contains protected path '{protected}'"
                )


# ── 6. Schedule alignment ─────────────────────────────────────────────────────

class TestScheduleAlignment:

    def test_schedule_intent_file_exists(self):
        path = _VAULT_ROOT / "runtime" / "schedules" / "sch-sbp-strikezone-digest-0600.yaml"
        assert path.exists()

    def test_schedule_targets_strikezone_digest_workflow(self):
        s = _load_schedule_yaml()
        assert s["workflow_id"] == "sbp_strikezone_digest"

    def test_schedule_cron_0600_et_weekdays(self):
        s = _load_schedule_yaml()
        expr = s["cadence"]["cron_expression"]
        assert expr == "0 6 * * 1-5", f"Expected 0600 ET weekdays cron, got '{expr}'"

    def test_schedule_index_includes_strikezone_digest(self):
        idx_path = _VAULT_ROOT / "runtime" / "schedules" / "index.yaml"
        with idx_path.open(encoding="utf-8") as f:
            idx = yaml.safe_load(f)
        ids = [s["schedule_id"] for s in idx["schedules"]]
        assert "sch-sbp-strikezone-digest-0600" in ids


# ── 7. No canonical mutation ──────────────────────────────────────────────────

class TestNoCanonicalMutation:

    def test_handler_result_has_no_canonical_writes(self):
        manifest = _minimal_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, Path(tmp))
        for wb in result["writebacks"]:
            path = wb["path"]
            for canonical in ["02_KNOWLEDGE/", "00_HOME/Now.md", "ROADMAP.md", "CLAUDE.md"]:
                assert not path.startswith(canonical), (
                    f"writeback '{path}' targets canonical file '{canonical}'"
                )

    def test_manifest_guardrail_no_forbidden_ceilings(self):
        from runtime.sbp.manifest import FORBIDDEN_PERMISSION_CEILINGS
        m = _load_manifest_yaml()
        sbp = load_sbp_config(m)
        assert sbp.guardrail.permission_ceiling not in FORBIDDEN_PERMISSION_CEILINGS


# ── 8. MCP scope unchanged ────────────────────────────────────────────────────

class TestMCPScopeUnchanged:

    def test_mcp_module_count_unchanged(self):
        mcp_dir = _VAULT_ROOT / "runtime" / "mcp"
        expected_modules = {
            "__init__.py",
            "client_smoke.py",
            "config.py",
            "errors.py",
            "safety.py",
            "server.py",
            "stdio_client.py",
            "types.py",
            "yaml_compat.py",
        }
        actual_modules = {f.name for f in mcp_dir.glob("*.py")}
        assert actual_modules == expected_modules, (
            "Runtime MCP module set should match the current bounded Phase 9 MCP surface; "
            f"found {sorted(actual_modules)}"
        )


# ── 9. Extract section helper ─────────────────────────────────────────────────

class TestExtractSection:

    def test_extract_section_finds_now_md(self):
        raw = "# 00_HOME/Now.md\n\nPhase 9 content here"
        result = _extract_section(raw, "Now.md", 1000)
        assert "Phase 9 content here" in result

    def test_extract_section_empty_raw_returns_empty(self):
        result = _extract_section("", "Now.md", 1000)
        assert result == ""

    def test_extract_section_truncates_at_max_chars(self):
        raw = "# test.md\n\n" + "x" * 2000
        result = _extract_section(raw, "test.md", 500)
        assert len(result) <= 530  # 500 + truncation note
        assert "truncated" in result


# ── 10. AcquisitionPackInputAdapter — Pass 1B consumer wiring ─────────────────

def _make_bris(tmp_dir: Path, artifact_id: str = "bris_test") -> Path:
    """Write a minimal briefing_ready_input_set.json to tmp_dir."""
    bris = {
        "artifact_id": artifact_id,
        "artifact_type": "briefing_ready_input_set",
        "schema_version": "anl.v1",
        "sections": {"manual_drop_in": [
            {"display_name": "Test Source", "base_trust_tier": 2,
             "freshness": "same_day", "actionability": "briefing_only",
             "origin_ref": "fake/path.md", "source_packet_ref": "sp_test_001"},
        ]},
        "trust_summary": {"tier1_count": 0, "tier2_count": 1, "tier3_count": 0,
                          "tier4_count": 0, "conflicts": []},
        "freshness_summary": {"stale_items": [], "unknown_freshness_items": [],
                              "missing_required_sources": []},
        "actionability": {"allowed_use": "briefing_only",
                          "blocked_actions": ["canonical_knowledge_promotion",
                                              "trade_execution"]},
    }
    bris_path = tmp_dir / "briefing_ready_input_set.json"
    bris_path.write_text(json.dumps(bris), encoding="utf-8")
    return bris_path


def _make_source_packet(tmp_dir: Path, index: int = 1, text: str = "Test normalized text") -> Path:
    """Write a minimal source_packet JSON to tmp_dir."""
    sp = {
        "artifact_id": f"sp_test_{index:03d}",
        "artifact_type": "source_packet",
        "normalized_text": text,
        "source_origin": {"display_name": f"Source {index}", "ref": "fake/path.md"},
        "trust_evaluation": {"base_trust_tier": 2},
        "freshness": {"freshness_window": "same_day"},
    }
    sp_path = tmp_dir / f"source_packet_{index:03d}.json"
    sp_path.write_text(json.dumps(sp), encoding="utf-8")
    return sp_path


class TestAcquisitionPackInputAdapter:

    def test_adapter_is_importable(self):
        assert AcquisitionPackInputAdapter is not None

    def test_adapter_type_is_acquisition_pack(self):
        assert AcquisitionPackInputAdapter.adapter_type == "acquisition-pack"

    def test_adapter_default_trust_tier_is_2(self):
        assert AcquisitionPackInputAdapter.default_trust_tier == 2

    def test_happy_path_reads_bris_and_packets(self):
        adapter = AcquisitionPackInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp) / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir, index=1, text="Morning thesis content")
            vault = Path(tmp)
            bris_rel = "packs/briefing_ready_input_set.json"
            cfg = SBPInputAdapterConfig(type="acquisition-pack", trust_tier=2, pack_path=bris_rel)
            result = adapter.collect(cfg, vault)
        assert result["stub"] is False
        assert result["trust_tier"] == 2
        assert "Morning thesis content" in (result["content"] or "")

    def test_content_includes_display_name(self):
        adapter = AcquisitionPackInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp) / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir, index=1, text="Some text")
            cfg = SBPInputAdapterConfig(type="acquisition-pack", trust_tier=2, pack_path="packs/briefing_ready_input_set.json")
            result = adapter.collect(cfg, Path(tmp))
        assert "Source 1" in (result["content"] or "")

    def test_content_includes_trust_tier_label(self):
        adapter = AcquisitionPackInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp) / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir, text="content")
            cfg = SBPInputAdapterConfig(type="acquisition-pack", trust_tier=2, pack_path="packs/briefing_ready_input_set.json")
            result = adapter.collect(cfg, Path(tmp))
        assert "trust tier" in (result["content"] or "")

    def test_returns_trust_summary(self):
        adapter = AcquisitionPackInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp) / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir)
            cfg = SBPInputAdapterConfig(type="acquisition-pack", trust_tier=2, pack_path="packs/briefing_ready_input_set.json")
            result = adapter.collect(cfg, Path(tmp))
        assert "trust_summary" in result
        assert "tier2_count" in result["trust_summary"]

    def test_returns_freshness_summary(self):
        adapter = AcquisitionPackInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp) / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir)
            cfg = SBPInputAdapterConfig(type="acquisition-pack", trust_tier=2, pack_path="packs/briefing_ready_input_set.json")
            result = adapter.collect(cfg, Path(tmp))
        assert "freshness_summary" in result

    def test_returns_blocked_actions(self):
        adapter = AcquisitionPackInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp) / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir)
            cfg = SBPInputAdapterConfig(type="acquisition-pack", trust_tier=2, pack_path="packs/briefing_ready_input_set.json")
            result = adapter.collect(cfg, Path(tmp))
        assert "blocked_actions" in result
        assert "canonical_knowledge_promotion" in result["blocked_actions"]

    def test_missing_pack_fails_closed_when_not_optional(self):
        adapter = AcquisitionPackInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            cfg = SBPInputAdapterConfig(
                type="acquisition-pack", trust_tier=2,
                pack_path="nonexistent/briefing_ready_input_set.json",
                optional=False,
            )
            with pytest.raises(InputAdapterError):
                adapter.collect(cfg, Path(tmp))

    def test_missing_pack_returns_stub_when_optional(self):
        adapter = AcquisitionPackInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            cfg = SBPInputAdapterConfig(
                type="acquisition-pack", trust_tier=2,
                pack_path="nonexistent/briefing_ready_input_set.json",
                optional=True,
            )
            result = adapter.collect(cfg, Path(tmp))
        assert result["stub"] is True
        assert result["content"] is None

    def test_malformed_json_fails_closed(self):
        adapter = AcquisitionPackInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp) / "packs"
            pack_dir.mkdir()
            bad = pack_dir / "briefing_ready_input_set.json"
            bad.write_text("not valid json {{{", encoding="utf-8")
            cfg = SBPInputAdapterConfig(type="acquisition-pack", trust_tier=2, pack_path="packs/briefing_ready_input_set.json")
            with pytest.raises(InputAdapterError):
                adapter.collect(cfg, Path(tmp))

    def test_wrong_artifact_type_fails_closed(self):
        adapter = AcquisitionPackInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp) / "packs"
            pack_dir.mkdir()
            wrong = {"artifact_type": "source_packet", "artifact_id": "sp_001"}
            (pack_dir / "briefing_ready_input_set.json").write_text(json.dumps(wrong), encoding="utf-8")
            cfg = SBPInputAdapterConfig(type="acquisition-pack", trust_tier=2, pack_path="packs/briefing_ready_input_set.json")
            with pytest.raises(InputAdapterError):
                adapter.collect(cfg, Path(tmp))

    def test_no_pack_path_fails_closed(self):
        adapter = AcquisitionPackInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            cfg = SBPInputAdapterConfig(type="acquisition-pack", trust_tier=2)
            with pytest.raises(InputAdapterError):
                adapter.collect(cfg, Path(tmp))

    def test_sources_list_includes_bris_and_packets(self):
        adapter = AcquisitionPackInputAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp) / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir, index=1)
            _make_source_packet(pack_dir, index=2)
            cfg = SBPInputAdapterConfig(type="acquisition-pack", trust_tier=2, pack_path="packs/briefing_ready_input_set.json")
            result = adapter.collect(cfg, Path(tmp))
        assert len(result["sources"]) >= 2  # BRIS + at least one packet
        assert any("briefing_ready_input_set.json" in s for s in result["sources"])

    def test_fixture_pack_loads_successfully(self):
        """Smoke test: real fixture pack from Acquisition + Normalization Pass 1A."""
        adapter = AcquisitionPackInputAdapter()
        fixture_rel = (
            "runtime/acquisition/packs/strikezone_pass1a_fixture/2026-04-23/"
            "briefing_ready_input_set.json"
        )
        fixture_abs = _VAULT_ROOT / fixture_rel
        if not fixture_abs.exists():
            pytest.skip("Pass 1A fixture pack not present on this machine")
        cfg = SBPInputAdapterConfig(type="acquisition-pack", trust_tier=2, pack_path=fixture_rel)
        result = adapter.collect(cfg, _VAULT_ROOT)
        assert result["stub"] is False
        assert result["trust_summary"]
        assert len(result["sources"]) >= 1


# ── 11. StrikeZone handler with acquisition-pack integration ───────────────────

class TestStrikeZoneHandlerWithAcquisitionPack:

    def _manifest_with_acq_pack(self, pack_path: str, optional: bool = False) -> dict:
        m = _minimal_manifest()
        m["sbp_config"]["input_adapters"].append({
            "type": "acquisition-pack",
            "trust_tier": 2,
            "pack_path": pack_path,
            "optional": optional,
        })
        return m

    def test_handler_includes_acquisition_sources_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            pack_dir = vault / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir, text="BTC momentum thesis")
            manifest = self._manifest_with_acq_pack("packs/briefing_ready_input_set.json")
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, vault)
        content = result["writebacks"][0]["content"]
        assert "Acquisition Sources" in content

    def test_acquisition_content_in_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            pack_dir = vault / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir, text="ETH momentum: strong accumulation")
            manifest = self._manifest_with_acq_pack("packs/briefing_ready_input_set.json")
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, vault)
        content = result["writebacks"][0]["content"]
        assert "ETH momentum" in content

    def test_trust_summary_in_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            pack_dir = vault / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir)
            manifest = self._manifest_with_acq_pack("packs/briefing_ready_input_set.json")
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, vault)
        content = result["writebacks"][0]["content"]
        assert "Trust summary" in content

    def test_blocked_actions_in_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            pack_dir = vault / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir)
            manifest = self._manifest_with_acq_pack("packs/briefing_ready_input_set.json")
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, vault)
        content = result["writebacks"][0]["content"]
        assert "blocked actions" in content.lower()

    def test_no_pack_available_shows_fallback_message(self):
        """Missing optional pack produces graceful fallback, not an error."""
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            manifest = self._manifest_with_acq_pack(
                "nonexistent/briefing_ready_input_set.json", optional=True
            )
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, vault)
        content = result["writebacks"][0]["content"]
        assert "No acquisition pack available" in content
        assert result["handler_status"] == "executed"

    def test_no_pack_non_optional_raises(self):
        """Missing non-optional pack causes pipeline to fail closed."""
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            manifest = self._manifest_with_acq_pack(
                "nonexistent/briefing_ready_input_set.json", optional=False
            )
            h = StrikeZoneDigestHandler()
            from runtime.sbp.base_handler import SBPWorkflowExecutionError
            with pytest.raises(SBPWorkflowExecutionError):
                h.run(manifest, {}, vault)

    def test_acquisition_pack_no_canonical_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            pack_dir = vault / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir)
            manifest = self._manifest_with_acq_pack("packs/briefing_ready_input_set.json")
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, vault)
        for wb in result["writebacks"]:
            assert not wb["path"].startswith("02_KNOWLEDGE/")
            assert not wb["path"].startswith("00_HOME/Now.md")

    def test_handler_status_executed_with_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            pack_dir = vault / "packs"
            pack_dir.mkdir()
            _make_bris(pack_dir)
            _make_source_packet(pack_dir)
            manifest = self._manifest_with_acq_pack("packs/briefing_ready_input_set.json")
            h = StrikeZoneDigestHandler()
            result = h.run(manifest, {}, vault)
        assert result["handler_status"] == "executed"

    def test_fixture_pack_integration_smoke(self):
        """End-to-end: handler consumes real Pass 1A fixture pack.
        Synthesis is mocked — this test verifies pipeline plumbing, not LLM output.
        """
        from unittest.mock import patch
        from runtime.execution_adapters.execute import SynthesisResult
        fixture_rel = (
            "runtime/acquisition/packs/strikezone_pass1a_fixture/2026-04-23/"
            "briefing_ready_input_set.json"
        )
        if not (_VAULT_ROOT / fixture_rel).exists():
            pytest.skip("Pass 1A fixture pack not present on this machine")
        manifest = self._manifest_with_acq_pack(fixture_rel, optional=True)
        h = StrikeZoneDigestHandler()
        mock_result = SynthesisResult(
            text="## Acquisition Sources\n\nSynthesized content.",
            model_id="claude-sonnet-4-6",
            runtime="openclaw",
            usage={},
            fallback_used=False,
        )
        with patch("runtime.workflows.sbp_strikezone_digest.execute_synthesis", return_value=mock_result):
            result = h.run(manifest, {}, _VAULT_ROOT)
        content = result["writebacks"][0]["content"]
        assert result["handler_status"] == "executed"
        assert "Acquisition Sources" in content


# ── 12. Manifest validation — acquisition-pack adapter type ───────────────────

class TestManifestAcquisitionPackAdapter:

    def test_acquisition_pack_type_accepted_by_validator(self):
        m = _minimal_manifest()
        m["sbp_config"]["input_adapters"].append({
            "type": "acquisition-pack",
            "trust_tier": 2,
            "pack_path": "runtime/acquisition/packs/some/briefing_ready_input_set.json",
            "optional": True,
        })
        sbp = load_sbp_config(m)
        types = [a.type for a in sbp.input_adapters]
        assert "acquisition-pack" in types

    def test_acquisition_pack_pack_path_preserved(self):
        m = _minimal_manifest()
        m["sbp_config"]["input_adapters"].append({
            "type": "acquisition-pack",
            "trust_tier": 2,
            "pack_path": "runtime/acquisition/packs/test/briefing_ready_input_set.json",
        })
        sbp = load_sbp_config(m)
        acq_cfg = next(a for a in sbp.input_adapters if a.type == "acquisition-pack")
        assert acq_cfg.pack_path == "runtime/acquisition/packs/test/briefing_ready_input_set.json"

    def test_acquisition_pack_optional_field_preserved(self):
        m = _minimal_manifest()
        m["sbp_config"]["input_adapters"].append({
            "type": "acquisition-pack",
            "trust_tier": 2,
            "pack_path": "runtime/acquisition/packs/test/briefing_ready_input_set.json",
            "optional": True,
        })
        sbp = load_sbp_config(m)
        acq_cfg = next(a for a in sbp.input_adapters if a.type == "acquisition-pack")
        assert acq_cfg.optional is True

    def test_live_manifest_acquisition_pack_validates(self):
        """The real manifest on disk must validate with acquisition-pack adapter."""
        m = _load_manifest_yaml()
        sbp = load_sbp_config(m)
        types = [a.type for a in sbp.input_adapters]
        assert "acquisition-pack" in types

    def test_live_manifest_acquisition_pack_optional(self):
        m = _load_manifest_yaml()
        sbp = load_sbp_config(m)
        acq_cfg = next((a for a in sbp.input_adapters if a.type == "acquisition-pack"), None)
        assert acq_cfg is not None
        assert acq_cfg.optional is True


# ── 13. Trust line formatter ───────────────────────────────────────────────────

class TestFormatTrustLine:

    def test_format_trust_line_basic(self):
        summary = {"tier1_count": 1, "tier2_count": 2, "tier3_count": 0, "tier4_count": 0, "conflicts": []}
        result = _format_trust_line(summary)
        assert "tier1: 1" in result
        assert "tier2: 2" in result

    def test_format_trust_line_with_conflicts(self):
        summary = {"tier1_count": 0, "tier2_count": 0, "tier3_count": 1, "tier4_count": 0, "conflicts": ["sp_001"]}
        result = _format_trust_line(summary)
        assert "1 conflict" in result

    def test_format_trust_line_empty_summary(self):
        result = _format_trust_line({})
        assert "tier1" in result
        assert "tier2" in result
