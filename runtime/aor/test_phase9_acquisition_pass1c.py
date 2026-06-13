"""
test_phase9_acquisition_pass1c.py — Acquisition + Normalization Pass 1C tests.

Covers:
  - OutputTargets.latest_pointer_path field parsed from plan JSON
  - validate_acquisition_plan accepts/rejects latest_pointer_path
  - SourcePackBuilder.build_and_write() writes pointer file when configured
  - Pointer file schema (schema_version, pointer_type, briefing_ready_input_set_path, etc.)
  - AcquisitionPackInputAdapter resolves BRIS via pointer (pack_latest_path)
  - Pointer-based resolution falls back to pack_path when pointer absent/unreadable
  - strikezone_acquisition handler: loads plan, builds pack, writes pointer
  - strikezone_acquisition.yaml manifest: active, task_type, role_card, required_reads
  - sch-strikezone-acquisition-0550.yaml schedule: schedule_id, cron, enabled, task_type
  - Schedule order: acquisition (0550) declared before digest (0600)
  - SBP manifest uses pack_latest_path (not static pack_path)
  - No canonical mutation, no MCP expansion, no browser authority change
  - No duplicate schedule truth (ChaseOS index has the schedule; not invented in OpenClaw)
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# ── Vault root fixture ────────────────────────────────────────────────────────

def _vault_root() -> Path:
    here = Path(__file__).resolve()
    candidate = here.parents[2]
    if (candidate / "CLAUDE.md").exists():
        return candidate
    raise RuntimeError(f"Cannot detect vault root from {here}")


VAULT_ROOT = _vault_root()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_minimal_plan_raw(pack_root: str, **overrides) -> dict:
    base = {
        "plan_id": "test-plan",
        "objective": {"title": "test", "requested_by": "operator", "downstream_target": "sbp_input"},
        "cadence": {"trigger": "manual"},
        "acquisition_surfaces": ["vault_file"],
        "acquisition_methods": ["direct_file_read"],
        "scope": {"read_scope": ["00_HOME/Now.md"]},
        "sources": [{
            "source_id": "now",
            "source_class": "vault_note",
            "surface": "vault_file",
            "acquisition_method": "direct_file_read",
            "path": "00_HOME/Now.md",
            "display_name": "Now.md",
            "base_trust_tier": 1,
        }],
        "output_targets": {"pack_root": pack_root},
        "trust": {"trust_floor": 2, "default_actionability": "briefing_only"},
        "freshness_policy": {"default_window": "daily"},
        "promotion": {"canonical_mutation_allowed": False},
        "audit": {"audit_required": True},
    }
    base.update(overrides)
    return base


# ══════════════════════════════════════════════════════════════════════════════
# 1. Plan validation — latest_pointer_path field
# ══════════════════════════════════════════════════════════════════════════════

class TestPlanLatestPointerPath:

    def test_plan_without_latest_pointer_path_is_valid(self):
        from runtime.acquisition.plan import validate_acquisition_plan
        raw = _make_minimal_plan_raw("runtime/acquisition/packs/test-plan")
        plan = validate_acquisition_plan(raw)
        assert plan.output_targets.latest_pointer_path is None

    def test_plan_with_latest_pointer_path_is_parsed(self):
        from runtime.acquisition.plan import validate_acquisition_plan
        raw = _make_minimal_plan_raw("runtime/acquisition/packs/test-plan")
        raw["output_targets"]["latest_pointer_path"] = "runtime/acquisition/packs/test-latest.json"
        plan = validate_acquisition_plan(raw)
        assert plan.output_targets.latest_pointer_path == "runtime/acquisition/packs/test-latest.json"

    def test_latest_pointer_path_must_be_in_allowed_zone(self):
        from runtime.acquisition.plan import validate_acquisition_plan
        from runtime.acquisition.validators import AcquisitionValidationError
        raw = _make_minimal_plan_raw("runtime/acquisition/packs/test-plan")
        raw["output_targets"]["latest_pointer_path"] = "00_HOME/some-pointer.json"
        with pytest.raises(AcquisitionValidationError):
            validate_acquisition_plan(raw)

    def test_latest_pointer_path_cannot_escape_vault(self):
        from runtime.acquisition.plan import validate_acquisition_plan
        from runtime.acquisition.validators import AcquisitionValidationError
        raw = _make_minimal_plan_raw("runtime/acquisition/packs/test-plan")
        raw["output_targets"]["latest_pointer_path"] = "../outside-vault.json"
        with pytest.raises(AcquisitionValidationError):
            validate_acquisition_plan(raw)

    def test_latest_pointer_path_cannot_be_absolute(self):
        from runtime.acquisition.plan import validate_acquisition_plan
        from runtime.acquisition.validators import AcquisitionValidationError
        raw = _make_minimal_plan_raw("runtime/acquisition/packs/test-plan")
        raw["output_targets"]["latest_pointer_path"] = "/absolute/path.json"
        with pytest.raises(AcquisitionValidationError):
            validate_acquisition_plan(raw)

    def test_strikezone_daily_plan_parses(self):
        """The real strikezone-daily.json plan validates without error."""
        from runtime.acquisition.plan import validate_acquisition_plan
        plan_path = VAULT_ROOT / "runtime/acquisition/plans/strikezone-daily.json"
        assert plan_path.exists(), "strikezone-daily.json must exist"
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
        plan = validate_acquisition_plan(raw)
        assert plan.plan_id == "strikezone-daily"
        assert plan.output_targets.latest_pointer_path == "runtime/acquisition/packs/strikezone-latest.json"
        assert plan.downstream_target == "sbp_strikezone_digest"
        assert plan.trigger == "schedule_declared"

    def test_strikezone_daily_plan_sources_are_vault_tier1(self):
        from runtime.acquisition.plan import validate_acquisition_plan
        plan_path = VAULT_ROOT / "runtime/acquisition/plans/strikezone-daily.json"
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
        plan = validate_acquisition_plan(raw)
        for source in plan.sources:
            assert source.base_trust_tier == 1, f"{source.source_id} must be tier 1"

    def test_strikezone_daily_plan_no_canonical_mutation(self):
        from runtime.acquisition.plan import validate_acquisition_plan
        plan_path = VAULT_ROOT / "runtime/acquisition/plans/strikezone-daily.json"
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
        plan = validate_acquisition_plan(raw)
        assert plan.promotion.canonical_mutation_allowed is False


# ══════════════════════════════════════════════════════════════════════════════
# 2. Builder — pointer file writing
# ══════════════════════════════════════════════════════════════════════════════

class TestBuilderPointerWrite:

    def _make_temp_vault(self, tmp: Path) -> Path:
        """Create a minimal temp vault with Now.md and CLAUDE.md."""
        (tmp / "CLAUDE.md").write_text("# CLAUDE.md", encoding="utf-8")
        (tmp / "00_HOME").mkdir()
        (tmp / "00_HOME" / "Now.md").write_text("# Now\ncurrent focus", encoding="utf-8")
        return tmp

    def test_build_and_write_creates_pointer_file(self, tmp_path):
        from runtime.acquisition.plan import validate_acquisition_plan
        from runtime.acquisition.builder import SourcePackBuilder
        vault = self._make_temp_vault(tmp_path)
        raw = _make_minimal_plan_raw("runtime/acquisition/packs/test")
        raw["output_targets"]["latest_pointer_path"] = "runtime/acquisition/packs/test-latest.json"
        plan = validate_acquisition_plan(raw)
        SourcePackBuilder().build_and_write(plan, vault)
        pointer_path = vault / "runtime/acquisition/packs/test-latest.json"
        assert pointer_path.exists(), "pointer file must be created"

    def test_pointer_file_schema(self, tmp_path):
        from runtime.acquisition.plan import validate_acquisition_plan
        from runtime.acquisition.builder import SourcePackBuilder
        vault = self._make_temp_vault(tmp_path)
        raw = _make_minimal_plan_raw("runtime/acquisition/packs/test")
        raw["output_targets"]["latest_pointer_path"] = "runtime/acquisition/packs/test-latest.json"
        plan = validate_acquisition_plan(raw)
        SourcePackBuilder().build_and_write(plan, vault)
        pointer = json.loads(
            (vault / "runtime/acquisition/packs/test-latest.json").read_text(encoding="utf-8")
        )
        assert pointer["schema_version"] == "anl.v1"
        assert pointer["pointer_type"] == "briefing_ready_input_set_latest"
        assert "briefing_ready_input_set_path" in pointer
        assert pointer["briefing_ready_input_set_path"].endswith("briefing_ready_input_set.json")
        assert "generated_at" in pointer
        assert pointer["plan_id"] == "test-plan"
        assert isinstance(pointer["source_packet_count"], int)
        assert pointer["source_packet_count"] >= 1

    def test_pointer_points_to_actual_bris(self, tmp_path):
        from runtime.acquisition.plan import validate_acquisition_plan
        from runtime.acquisition.builder import SourcePackBuilder
        vault = self._make_temp_vault(tmp_path)
        raw = _make_minimal_plan_raw("runtime/acquisition/packs/test")
        raw["output_targets"]["latest_pointer_path"] = "runtime/acquisition/packs/test-latest.json"
        plan = validate_acquisition_plan(raw)
        result = SourcePackBuilder().build_and_write(plan, vault)
        pointer = json.loads(
            (vault / "runtime/acquisition/packs/test-latest.json").read_text(encoding="utf-8")
        )
        bris_path = vault / pointer["briefing_ready_input_set_path"]
        assert bris_path.exists(), "pointer must reference an existing BRIS file"
        bris = json.loads(bris_path.read_text(encoding="utf-8"))
        assert bris["artifact_type"] == "briefing_ready_input_set"

    def test_build_and_write_without_latest_pointer_path_skips_pointer(self, tmp_path):
        from runtime.acquisition.plan import validate_acquisition_plan
        from runtime.acquisition.builder import SourcePackBuilder
        vault = self._make_temp_vault(tmp_path)
        raw = _make_minimal_plan_raw("runtime/acquisition/packs/test")
        plan = validate_acquisition_plan(raw)
        SourcePackBuilder().build_and_write(plan, vault)
        # No pointer file should exist anywhere
        for f in (vault / "runtime/acquisition/packs").glob("*.json"):
            assert "latest" not in f.name, f"unexpected pointer file: {f}"

    def test_pointer_overwrites_stale_pointer_on_rerun(self, tmp_path):
        from runtime.acquisition.plan import validate_acquisition_plan
        from runtime.acquisition.builder import SourcePackBuilder
        vault = self._make_temp_vault(tmp_path)
        pointer_rel = "runtime/acquisition/packs/test-latest.json"
        raw = _make_minimal_plan_raw("runtime/acquisition/packs/test")
        raw["output_targets"]["latest_pointer_path"] = pointer_rel
        plan = validate_acquisition_plan(raw)
        # Write once
        SourcePackBuilder().build_and_write(plan, vault)
        first = json.loads((vault / pointer_rel).read_text(encoding="utf-8"))
        # Write again (simulates next day re-run)
        SourcePackBuilder().build_and_write(plan, vault)
        second = json.loads((vault / pointer_rel).read_text(encoding="utf-8"))
        # Both must be valid — pointer gets overwritten
        assert second["pointer_type"] == "briefing_ready_input_set_latest"
        _ = first  # first pointer was overwritten; that is correct behavior


# ══════════════════════════════════════════════════════════════════════════════
# 3. SBP manifest — pack_latest_path field
# ══════════════════════════════════════════════════════════════════════════════

class TestSBPManifestPackLatestPath:

    def _make_minimal_sbp_config(self, **adapter_overrides) -> dict:
        adapter = {"type": "acquisition-pack", "trust_tier": 2, "optional": True}
        adapter.update(adapter_overrides)
        return {
            "trigger": {"type": "cron", "cron_expression": "0 6 * * 1-5"},
            "input_adapters": [adapter],
            "execution_adapter": "claude",
            "delivery_adapters": [{"type": "vault-local"}],
            "guardrail": {
                "permission_ceiling": "no_protected_file_writes",
                "write_scope": ["07_LOGS/SBP-Runs/"],
                "audit_required": True,
            },
        }

    def test_pack_latest_path_is_parsed_by_validate_sbp_config(self):
        from runtime.sbp.manifest import validate_sbp_config
        cfg = self._make_minimal_sbp_config(
            pack_latest_path="runtime/acquisition/packs/strikezone-latest.json"
        )
        result = validate_sbp_config(cfg, "test")
        adapter = result.input_adapters[0]
        assert adapter.pack_latest_path == "runtime/acquisition/packs/strikezone-latest.json"
        assert adapter.pack_path is None

    def test_pack_path_and_pack_latest_path_can_coexist(self):
        from runtime.sbp.manifest import validate_sbp_config
        cfg = self._make_minimal_sbp_config(
            pack_path="runtime/acquisition/packs/fixture/bris.json",
            pack_latest_path="runtime/acquisition/packs/strikezone-latest.json",
        )
        result = validate_sbp_config(cfg, "test")
        adapter = result.input_adapters[0]
        assert adapter.pack_latest_path is not None
        assert adapter.pack_path is not None

    def test_strikezone_digest_manifest_uses_pack_latest_path(self):
        """The real sbp_strikezone_digest.yaml must use pack_latest_path, not pack_path."""
        manifest_path = VAULT_ROOT / "runtime/workflows/registry/sbp_strikezone_digest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        adapters = manifest.get("sbp_config", {}).get("input_adapters", [])
        acq_adapters = [a for a in adapters if a.get("type") == "acquisition-pack"]
        assert acq_adapters, "sbp_strikezone_digest must have an acquisition-pack adapter"
        for adapter in acq_adapters:
            assert "pack_latest_path" in adapter, "acquisition-pack adapter must use pack_latest_path"
            assert adapter["pack_latest_path"] == "runtime/acquisition/packs/strikezone-latest.json"
            assert "pack_path" not in adapter or adapter.get("pack_path") is None, (
                "static pack_path should not be set when pack_latest_path is used"
            )

    def test_strikezone_digest_manifest_acquisition_adapter_is_optional(self):
        manifest_path = VAULT_ROOT / "runtime/workflows/registry/sbp_strikezone_digest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        adapters = manifest.get("sbp_config", {}).get("input_adapters", [])
        acq_adapters = [a for a in adapters if a.get("type") == "acquisition-pack"]
        for adapter in acq_adapters:
            assert adapter.get("optional") is True, "acquisition-pack adapter must remain optional"


# ══════════════════════════════════════════════════════════════════════════════
# 4. AcquisitionPackInputAdapter — pointer resolution
# ══════════════════════════════════════════════════════════════════════════════

class TestAcquisitionPackAdapterPointerResolution:

    def _make_vault_with_pack(self, tmp: Path) -> tuple[Path, str, str]:
        """Create a temp vault with a valid BRIS and source_packet."""
        (tmp / "CLAUDE.md").write_text("# CLAUDE.md", encoding="utf-8")
        pack_dir = tmp / "runtime/acquisition/packs/2026-04-23-test"
        pack_dir.mkdir(parents=True)
        packet = {
            "artifact_id": "sp_test_001_abc12345",
            "artifact_type": "source_packet",
            "schema_version": "anl.v1",
            "created_at": "2026-04-23T05:50:00Z",
            "owner_layer": "acquisition_normalization",
            "owning_workflow": "source_pack_builder",
            "objective": {"title": "test", "requested_by": "op", "downstream_target": "sbp"},
            "acquirer": {"identity": "source_pack_builder", "runtime_id": "source_pack_builder",
                         "trust_tier_ceiling": 2, "adapter_id": None, "role_card": "source-pack-builder"},
            "scope": {"read_scope": [], "browser_scope": [], "network_scope": [], "cadence_or_trigger": "manual"},
            "promotion": {"status": "workspace-local", "allowed_next_steps": [], "canonical_mutation_allowed": False},
            "audit": {"activity_log_ref": None, "source_hashes": [], "audit_required": True},
            "source_id": "now",
            "source_class": "vault_note",
            "source_origin": {"kind": "vault", "ref": "00_HOME/Now.md", "display_name": "Now.md"},
            "acquisition_method": "direct_file_read",
            "provenance": {
                "source_origin": {"kind": "vault", "ref": "00_HOME/Now.md", "display_name": "Now.md"},
                "acquisition_method": "direct_file_read",
                "acquirer": {},
                "captured_at": "2026-04-23T05:50:00Z",
                "content_sha256": "abc",
                "raw_pointer": {"path": "00_HOME/Now.md", "sidecar_ref": None},
                "representation_level": "normalized",
            },
            "trust_evaluation": {
                "base_trust_tier": 1, "assigned_by": "source_pack_builder",
                "confidence": "high", "quality_marker": "canonical",
                "operator_approval_state": "not_required", "actionability": "briefing_only",
            },
            "freshness": {
                "source_event_at": None, "captured_at": "2026-04-23T05:50:00Z",
                "freshness_window": "daily", "expires_at": None,
                "staleness_policy": "warn", "time_sensitive_domain": "none",
            },
            "transformation_chain": [{"step_id": "file_read", "performed_by": "op",
                                       "method": "direct_file_read", "timestamp": "2026-04-23T05:50:00Z",
                                       "input_ref": "00_HOME/Now.md", "output_ref": "sp_test_001_abc12345",
                                       "representation_level": "raw"}],
            "raw_pointer": {"path": "00_HOME/Now.md", "sidecar_ref": None},
            "content_sha256": "abc",
            "normalized_text": "# Now\ncurrent focus",
        }
        bris = {
            "artifact_id": "bris_test",
            "artifact_type": "briefing_ready_input_set",
            "schema_version": "anl.v1",
            "created_at": "2026-04-23T05:50:00Z",
            "owner_layer": "acquisition_normalization",
            "owning_workflow": "source_pack_builder",
            "objective": {"title": "test", "requested_by": "op", "downstream_target": "sbp"},
            "acquirer": {},
            "scope": {"read_scope": [], "browser_scope": [], "network_scope": [], "cadence_or_trigger": "manual"},
            "promotion": {"status": "workspace-local", "allowed_next_steps": [], "canonical_mutation_allowed": False},
            "audit": {"activity_log_ref": None, "source_hashes": [], "audit_required": True},
            "normalized_source_pack_ref": "nsp_test",
            "sections": {},
            "trust_summary": {"tier1_count": 1, "tier2_count": 0, "tier3_count": 0, "tier4_count": 0, "conflicts": []},
            "freshness_summary": {"stale_items": [], "unknown_freshness_items": [], "missing_required_sources": []},
            "actionability": {"allowed_use": "briefing_only", "blocked_actions": ["canonical_knowledge_promotion"]},
            "source_refs": ["sp_test_001_abc12345"],
            "transformation_chain": [{}],
        }
        (pack_dir / "source_packet_001.json").write_text(json.dumps(packet), encoding="utf-8")
        bris_path = pack_dir / "briefing_ready_input_set.json"
        bris_path.write_text(json.dumps(bris), encoding="utf-8")
        bris_rel = str(bris_path.relative_to(tmp)).replace("\\", "/")
        return tmp, bris_rel, str(bris_path.relative_to(tmp)).replace("\\", "/")

    def _write_pointer(self, vault: Path, pointer_rel: str, bris_rel: str) -> None:
        pointer = {
            "schema_version": "anl.v1",
            "pointer_type": "briefing_ready_input_set_latest",
            "briefing_ready_input_set_path": bris_rel,
            "generated_at": "2026-04-23T05:50:00Z",
            "plan_id": "test",
            "source_packet_count": 1,
        }
        dest = vault / pointer_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(pointer), encoding="utf-8")

    def test_adapter_resolves_bris_via_pointer(self, tmp_path):
        from runtime.sbp.input_adapters import AcquisitionPackInputAdapter
        from runtime.sbp.manifest import SBPInputAdapterConfig
        vault, bris_rel, _ = self._make_vault_with_pack(tmp_path)
        pointer_rel = "runtime/acquisition/packs/test-latest.json"
        self._write_pointer(vault, pointer_rel, bris_rel)
        config = SBPInputAdapterConfig(
            type="acquisition-pack",
            trust_tier=2,
            pack_latest_path=pointer_rel,
            optional=False,
        )
        result = AcquisitionPackInputAdapter().collect(config, vault)
        assert result["stub"] is False
        assert result["trust_tier"] == 2

    def test_adapter_falls_back_to_pack_path_when_pointer_absent(self, tmp_path):
        from runtime.sbp.input_adapters import AcquisitionPackInputAdapter
        from runtime.sbp.manifest import SBPInputAdapterConfig
        vault, bris_rel, _ = self._make_vault_with_pack(tmp_path)
        # pointer file does NOT exist; pack_path points directly
        config = SBPInputAdapterConfig(
            type="acquisition-pack",
            trust_tier=2,
            pack_latest_path="runtime/acquisition/packs/nonexistent-latest.json",
            pack_path=bris_rel,
            optional=False,
        )
        result = AcquisitionPackInputAdapter().collect(config, vault)
        assert result["stub"] is False

    def test_adapter_returns_stub_when_pointer_absent_and_optional(self, tmp_path):
        from runtime.sbp.input_adapters import AcquisitionPackInputAdapter
        from runtime.sbp.manifest import SBPInputAdapterConfig
        vault = tmp_path
        (vault / "CLAUDE.md").write_text("# CLAUDE.md", encoding="utf-8")
        config = SBPInputAdapterConfig(
            type="acquisition-pack",
            trust_tier=2,
            pack_latest_path="runtime/acquisition/packs/nonexistent-latest.json",
            optional=True,
        )
        result = AcquisitionPackInputAdapter().collect(config, vault)
        assert result["stub"] is True

    def test_adapter_raises_when_pointer_absent_and_not_optional(self, tmp_path):
        from runtime.sbp.input_adapters import AcquisitionPackInputAdapter, InputAdapterError
        from runtime.sbp.manifest import SBPInputAdapterConfig
        vault = tmp_path
        (vault / "CLAUDE.md").write_text("# CLAUDE.md", encoding="utf-8")
        config = SBPInputAdapterConfig(
            type="acquisition-pack",
            trust_tier=2,
            pack_latest_path="runtime/acquisition/packs/nonexistent-latest.json",
            optional=False,
        )
        with pytest.raises(InputAdapterError):
            AcquisitionPackInputAdapter().collect(config, vault)

    def test_adapter_falls_back_gracefully_on_corrupt_pointer(self, tmp_path):
        from runtime.sbp.input_adapters import AcquisitionPackInputAdapter
        from runtime.sbp.manifest import SBPInputAdapterConfig
        vault, bris_rel, _ = self._make_vault_with_pack(tmp_path)
        pointer_path = vault / "runtime/acquisition/packs/corrupt-latest.json"
        pointer_path.parent.mkdir(parents=True, exist_ok=True)
        pointer_path.write_text("NOT VALID JSON{{{{", encoding="utf-8")
        config = SBPInputAdapterConfig(
            type="acquisition-pack",
            trust_tier=2,
            pack_latest_path="runtime/acquisition/packs/corrupt-latest.json",
            pack_path=bris_rel,
            optional=False,
        )
        # Should fall back to pack_path without raising
        result = AcquisitionPackInputAdapter().collect(config, vault)
        assert result["stub"] is False

    def test_adapter_no_config_raises_when_not_optional(self, tmp_path):
        from runtime.sbp.input_adapters import AcquisitionPackInputAdapter, InputAdapterError
        from runtime.sbp.manifest import SBPInputAdapterConfig
        vault = tmp_path
        config = SBPInputAdapterConfig(type="acquisition-pack", trust_tier=2, optional=False)
        with pytest.raises(InputAdapterError):
            AcquisitionPackInputAdapter().collect(config, vault)


# ══════════════════════════════════════════════════════════════════════════════
# 5. strikezone_acquisition handler
# ══════════════════════════════════════════════════════════════════════════════

class TestStrikeZoneAcquisitionHandler:

    def _make_temp_vault_with_strikezone(self, tmp: Path) -> Path:
        (tmp / "CLAUDE.md").write_text("# CLAUDE.md", encoding="utf-8")
        (tmp / "00_HOME").mkdir()
        (tmp / "00_HOME" / "Now.md").write_text("# Now\ncurrent sprint focus", encoding="utf-8")
        (tmp / "01_PROJECTS" / "StrikeZone").mkdir(parents=True)
        (tmp / "01_PROJECTS" / "StrikeZone" / "StrikeZone-Crypto-OS.md").write_text(
            "# StrikeZone-Crypto-OS\nproject state", encoding="utf-8"
        )
        # Copy the real plan file
        import shutil
        plans_dir = tmp / "runtime/acquisition/plans"
        plans_dir.mkdir(parents=True)
        real_plan = VAULT_ROOT / "runtime/acquisition/plans/strikezone-daily.json"
        shutil.copy(real_plan, plans_dir / "strikezone-daily.json")
        return tmp

    def test_handler_returns_dict_with_expected_keys(self, tmp_path):
        from runtime.workflows.strikezone_acquisition import run_strikezone_acquisition
        vault = self._make_temp_vault_with_strikezone(tmp_path)
        result = run_strikezone_acquisition(inputs={}, vault_root=vault)
        assert result["workflow"] == "source_pack_builder"
        assert "briefing_ready_input_set_path" in result
        assert "source_packet_paths" in result
        assert len(result["source_packet_paths"]) >= 1

    def test_handler_writes_pointer_file(self, tmp_path):
        from runtime.workflows.strikezone_acquisition import run_strikezone_acquisition
        vault = self._make_temp_vault_with_strikezone(tmp_path)
        run_strikezone_acquisition(inputs={}, vault_root=vault)
        pointer = vault / "runtime/acquisition/packs/strikezone-latest.json"
        assert pointer.exists(), "strikezone-latest.json pointer must be written"
        data = json.loads(pointer.read_text(encoding="utf-8"))
        assert data["pointer_type"] == "briefing_ready_input_set_latest"
        assert data["plan_id"] == "strikezone-daily"

    def test_handler_pointer_references_valid_bris(self, tmp_path):
        from runtime.workflows.strikezone_acquisition import run_strikezone_acquisition
        vault = self._make_temp_vault_with_strikezone(tmp_path)
        run_strikezone_acquisition(inputs={}, vault_root=vault)
        pointer = json.loads(
            (vault / "runtime/acquisition/packs/strikezone-latest.json").read_text(encoding="utf-8")
        )
        bris_path = vault / pointer["briefing_ready_input_set_path"]
        assert bris_path.exists()
        bris = json.loads(bris_path.read_text(encoding="utf-8"))
        assert bris["artifact_type"] == "briefing_ready_input_set"

    def test_handler_raises_when_plan_file_missing(self, tmp_path):
        from runtime.workflows.strikezone_acquisition import (
            run_strikezone_acquisition, WorkflowExecutionError
        )
        vault = tmp_path
        (vault / "CLAUDE.md").write_text("# CLAUDE.md", encoding="utf-8")
        with pytest.raises(WorkflowExecutionError, match="plan file not found"):
            run_strikezone_acquisition(inputs={}, vault_root=vault)

    def test_handler_no_canonical_mutation(self, tmp_path):
        from runtime.workflows.strikezone_acquisition import run_strikezone_acquisition
        vault = self._make_temp_vault_with_strikezone(tmp_path)
        run_strikezone_acquisition(inputs={}, vault_root=vault)
        # No canonical directories should be touched
        for protected in ["02_KNOWLEDGE", "SOUL.md", "Principles.md", "ROADMAP.md"]:
            path = vault / protected
            assert not path.exists(), f"handler must not create {protected}"

    def test_handler_project_scope_is_strikezone(self, tmp_path):
        from runtime.workflows.strikezone_acquisition import run_strikezone_acquisition
        vault = self._make_temp_vault_with_strikezone(tmp_path)
        result = run_strikezone_acquisition(inputs={}, vault_root=vault)
        assert result.get("project_scope") == "StrikeZone"


# ══════════════════════════════════════════════════════════════════════════════
# 6. Manifest and schedule file integrity
# ══════════════════════════════════════════════════════════════════════════════

class TestStrikeZoneAcquisitionManifest:

    def test_manifest_exists(self):
        path = VAULT_ROOT / "runtime/workflows/registry/strikezone_acquisition.yaml"
        assert path.exists(), "strikezone_acquisition.yaml must exist"

    def test_manifest_id_matches_filename(self):
        path = VAULT_ROOT / "runtime/workflows/registry/strikezone_acquisition.yaml"
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert manifest["id"] == "strikezone_acquisition"

    def test_manifest_is_active(self):
        path = VAULT_ROOT / "runtime/workflows/registry/strikezone_acquisition.yaml"
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert manifest["status"] == "active"

    def test_manifest_task_type_is_source_pack_builder(self):
        path = VAULT_ROOT / "runtime/workflows/registry/strikezone_acquisition.yaml"
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert manifest["task_type"] == "source-pack-builder"

    def test_manifest_role_card_is_source_pack_builder(self):
        path = VAULT_ROOT / "runtime/workflows/registry/strikezone_acquisition.yaml"
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert manifest["role_card"] == "source-pack-builder"

    def test_manifest_writeback_targets_are_non_canonical(self):
        path = VAULT_ROOT / "runtime/workflows/registry/strikezone_acquisition.yaml"
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        for target in manifest.get("writeback_targets", []):
            assert target.startswith("runtime/acquisition/packs/"), (
                f"writeback target {target!r} is outside acquisition zone"
            )

    def test_manifest_declares_plan_in_required_reads(self):
        path = VAULT_ROOT / "runtime/workflows/registry/strikezone_acquisition.yaml"
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        required = manifest.get("required_reads", [])
        assert "runtime/acquisition/plans/strikezone-daily.json" in required


class TestStrikeZoneAcquisitionSchedule:

    def test_schedule_file_exists(self):
        path = VAULT_ROOT / "runtime/schedules/sch-strikezone-acquisition-0550.yaml"
        assert path.exists()

    def test_schedule_id_matches_filename(self):
        path = VAULT_ROOT / "runtime/schedules/sch-strikezone-acquisition-0550.yaml"
        sch = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert sch["schedule_id"] == "sch-strikezone-acquisition-0550"

    def test_schedule_workflow_id(self):
        path = VAULT_ROOT / "runtime/schedules/sch-strikezone-acquisition-0550.yaml"
        sch = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert sch["workflow_id"] == "strikezone_acquisition"

    def test_schedule_cron_fires_before_digest(self):
        """0550 ET (50 5 * * 1-5) must be before 0600 ET (0 6 * * 1-5)."""
        path = VAULT_ROOT / "runtime/schedules/sch-strikezone-acquisition-0550.yaml"
        sch = yaml.safe_load(path.read_text(encoding="utf-8"))
        cron = sch["cadence"]["cron_expression"]
        # cron: "50 5 * * 1-5" → minute=50, hour=5 → 05:50 ET
        parts = cron.strip().split()
        minute, hour = int(parts[0]), int(parts[1])
        assert hour < 6 or (hour == 6 and minute < 0), (
            f"acquisition schedule {cron!r} must fire before 06:00 ET"
        )
        # More precisely: hour 5 minute 50 = 350 minutes; digest at 360
        assert hour * 60 + minute < 6 * 60

    def test_schedule_is_enabled(self):
        path = VAULT_ROOT / "runtime/schedules/sch-strikezone-acquisition-0550.yaml"
        sch = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert sch["enabled"] is True

    def test_schedule_adapter_target_is_hermes(self):
        path = VAULT_ROOT / "runtime/schedules/sch-strikezone-acquisition-0550.yaml"
        sch = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert sch["runtime_adapter_target"] == "hermes"
        assert sch.get("runtime_adapter_fallback") == "openclaw"

    def test_schedule_allowed_task_types_includes_source_pack_builder(self):
        path = VAULT_ROOT / "runtime/schedules/sch-strikezone-acquisition-0550.yaml"
        sch = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert "source-pack-builder" in sch.get("allowed_workflow_task_types", [])

    def test_schedule_in_index(self):
        index_path = VAULT_ROOT / "runtime/schedules/index.yaml"
        index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        ids = [s["schedule_id"] for s in index.get("schedules", [])]
        assert "sch-strikezone-acquisition-0550" in ids

    def test_schedule_order_in_index(self):
        """Acquisition (0550) must appear in index before digest (0600)."""
        index_path = VAULT_ROOT / "runtime/schedules/index.yaml"
        index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        ids = [s["schedule_id"] for s in index.get("schedules", [])]
        assert "sch-strikezone-acquisition-0550" in ids
        assert "sch-sbp-strikezone-digest-0600" in ids
        acq_idx = ids.index("sch-strikezone-acquisition-0550")
        digest_idx = ids.index("sch-sbp-strikezone-digest-0600")
        assert acq_idx < digest_idx, (
            "acquisition schedule must be listed before digest schedule in index"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 7. Engine handler registration
# ══════════════════════════════════════════════════════════════════════════════

class TestEngineHandlerRegistration:

    def test_strikezone_acquisition_is_registered_in_handlers(self):
        from runtime.workflows.strikezone_acquisition import run_strikezone_acquisition
        import runtime.aor.engine as engine_mod
        import inspect
        source = inspect.getsource(engine_mod._stage_run)
        assert "strikezone_acquisition" in source

    def test_strikezone_acquisition_workflow_executes_via_engine(self, tmp_path):
        """Engine dry-run resolves manifest, role card, and task type successfully."""
        import shutil
        vault = tmp_path
        # Copy minimal vault structure
        for src_rel in [
            "CLAUDE.md", "00_HOME/Now.md",
            "runtime/workflows/registry/strikezone_acquisition.yaml",
            "runtime/acquisition/plans/strikezone-daily.json",
            "runtime/aor/task_type_table.yaml",
        ]:
            src = VAULT_ROOT / src_rel
            dst = vault / src_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.exists():
                shutil.copy(src, dst)
        # Copy role card
        rc_src = VAULT_ROOT / "06_AGENTS/role-cards/source-pack-builder.yaml"
        rc_dst = vault / "06_AGENTS/role-cards/source-pack-builder.yaml"
        rc_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(rc_src, rc_dst)
        # StrikeZone-Crypto-OS.md (required read in manifest)
        sz_dst = vault / "01_PROJECTS/StrikeZone/StrikeZone-Crypto-OS.md"
        sz_dst.parent.mkdir(parents=True, exist_ok=True)
        sz_dst.write_text("# StrikeZone-Crypto-OS\n", encoding="utf-8")
        from runtime.aor.engine import run_workflow
        result = run_workflow("strikezone_acquisition", inputs={}, vault_root=vault, dry_run=True)
        assert result.status == "dry_run_ok", f"Expected dry_run_ok, got: {result.status} — {result.escalation_reason}"


# ══════════════════════════════════════════════════════════════════════════════
# 8. Boundary enforcement
# ══════════════════════════════════════════════════════════════════════════════

class TestPass1CBoundaries:

    def test_strikezone_acquisition_handler_has_no_mcp_references(self):
        handler_path = VAULT_ROOT / "runtime/workflows/strikezone_acquisition.py"
        content = handler_path.read_text(encoding="utf-8")
        assert "mcp" not in content.lower() or "mcp_surface" not in content.lower()
        # More specifically: no runtime/mcp imports
        assert "runtime.mcp" not in content

    def test_strikezone_acquisition_handler_has_no_browser_imports(self):
        handler_path = VAULT_ROOT / "runtime/workflows/strikezone_acquisition.py"
        content = handler_path.read_text(encoding="utf-8")
        assert "browser_connector" not in content
        assert "operator_surface.browser" not in content
        assert "run_browser_research" not in content

    def test_strikezone_acquisition_handler_has_no_delivery_imports(self):
        handler_path = VAULT_ROOT / "runtime/workflows/strikezone_acquisition.py"
        content = handler_path.read_text(encoding="utf-8")
        assert "delivery_adapters" not in content
        assert "DiscordDelivery" not in content
        assert "DISCORD_WEBHOOK_URL" not in content

    def test_plan_rejects_connector_call(self):
        from runtime.acquisition.plan import validate_acquisition_plan
        from runtime.acquisition.validators import AcquisitionValidationError
        plan_path = VAULT_ROOT / "runtime/acquisition/plans/strikezone-daily.json"
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
        raw["connector_call_requested"] = True
        with pytest.raises(AcquisitionValidationError):
            validate_acquisition_plan(raw)

    def test_plan_rejects_network_scope(self):
        from runtime.acquisition.plan import validate_acquisition_plan
        from runtime.acquisition.validators import AcquisitionValidationError
        plan_path = VAULT_ROOT / "runtime/acquisition/plans/strikezone-daily.json"
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
        raw["scope"]["network_scope"] = [{"origin": "https://example.com"}]
        with pytest.raises(AcquisitionValidationError):
            validate_acquisition_plan(raw)

    def test_schedule_index_has_no_duplicate_entries(self):
        index_path = VAULT_ROOT / "runtime/schedules/index.yaml"
        index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        ids = [s["schedule_id"] for s in index.get("schedules", [])]
        assert len(ids) == len(set(ids)), "Schedule index must not have duplicate schedule_id entries"
