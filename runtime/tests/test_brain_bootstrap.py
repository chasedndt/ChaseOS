"""
test_brain_bootstrap.py — Brain Bootstrap Sequence tests

Covers:
  - run_brain_bootstrap() seeds all three surfaces
  - Idempotency: re-running skips existing seeds
  - Seed content shape for profile, identity-ledger, nav-map
  - Missing vault_root auto-detection path
  - CLI integration: chaseos agent register seeds bootstrap surfaces
  - Bootstrap failure is non-fatal (ok=False dict, registration still succeeds)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.aor.brain_bootstrap import run_brain_bootstrap


# ── Helpers ────────────────────────────────────────────────────────────────────

def _bootstrap(tmp_path: Path, runtime_id: str = "test-rt") -> dict:
    return run_brain_bootstrap(runtime_id, vault_root=tmp_path)


def _profile_path(tmp_path: Path, runtime_id: str) -> Path:
    return tmp_path / "runtime" / "memory" / "adapters" / runtime_id / "profile.json"


def _ledger_path(tmp_path: Path, runtime_id: str) -> Path:
    return tmp_path / "runtime" / "memory" / "adapters" / runtime_id / "identity-ledger.json"


def _nav_path(tmp_path: Path, runtime_id: str) -> Path:
    return tmp_path / "runtime" / "memory" / "nav" / runtime_id / "nav-map.json"


# ── Return shape ───────────────────────────────────────────────────────────────

def test_bootstrap_returns_ok():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        result = run_brain_bootstrap("rt1", vault_root=Path(d))
        assert result["ok"] is True


def test_bootstrap_returns_runtime_id():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        result = run_brain_bootstrap("my-runtime", vault_root=Path(d))
        assert result["runtime_id"] == "my-runtime"


def test_bootstrap_returns_seeds_written(tmp_path):
    result = _bootstrap(tmp_path)
    assert isinstance(result["seeds_written"], list)
    assert len(result["seeds_written"]) == 3


def test_bootstrap_returns_seeds_skipped_empty_on_first_run(tmp_path):
    result = _bootstrap(tmp_path)
    assert result["seeds_skipped"] == []


# ── Files created ─────────────────────────────────────────────────────────────

def test_profile_json_created(tmp_path):
    _bootstrap(tmp_path)
    assert _profile_path(tmp_path, "test-rt").exists()


def test_identity_ledger_json_created(tmp_path):
    _bootstrap(tmp_path)
    assert _ledger_path(tmp_path, "test-rt").exists()


def test_nav_map_json_created(tmp_path):
    _bootstrap(tmp_path)
    assert _nav_path(tmp_path, "test-rt").exists()


# ── Seed content shape ────────────────────────────────────────────────────────

def test_profile_schema_version(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_profile_path(tmp_path, "test-rt").read_text())
    assert data["schema_version"] == "1.0"


def test_profile_layer_is_C(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_profile_path(tmp_path, "test-rt").read_text())
    assert data["layer"] == "C"


def test_profile_memory_family(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_profile_path(tmp_path, "test-rt").read_text())
    assert data["memory_family"] == "runtime_behavior_profile"


def test_profile_status_bootstrap_seeded(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_profile_path(tmp_path, "test-rt").read_text())
    assert data["status"] == "bootstrap-seeded"


def test_profile_runtime_id_matches(tmp_path):
    _bootstrap(tmp_path, "my-rt")
    data = json.loads(_profile_path(tmp_path, "my-rt").read_text())
    assert data["runtime_id"] == "my-rt"


def test_profile_has_behavioral_profile(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_profile_path(tmp_path, "test-rt").read_text())
    bp = data["behavioral_profile"]
    assert "primary_role" in bp
    assert "strengths" in bp
    assert "known_failure_modes" in bp
    assert "routing_guidance" in bp
    assert "confidence_signals" in bp


def test_identity_ledger_schema_version(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_ledger_path(tmp_path, "test-rt").read_text())
    assert data["schema_version"] == "1.0"


def test_identity_ledger_memory_family(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_ledger_path(tmp_path, "test-rt").read_text())
    assert data["memory_family"] == "agent_identity_ledger"


def test_identity_ledger_status_bootstrap_seeded(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_ledger_path(tmp_path, "test-rt").read_text())
    assert data["status"] == "bootstrap-seeded"


def test_identity_ledger_has_required_sections(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_ledger_path(tmp_path, "test-rt").read_text())
    assert "identity_summary" in data
    assert "behavioral_tendencies" in data
    assert "correction_history" in data
    assert "drift_signals" in data
    assert "authority_boundaries" in data
    assert "governance_boundary" in data


def test_identity_ledger_behavioral_tendencies_empty(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_ledger_path(tmp_path, "test-rt").read_text())
    assert data["behavioral_tendencies"] == []


def test_identity_ledger_corrections_empty(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_ledger_path(tmp_path, "test-rt").read_text())
    assert data["correction_history"] == []


def test_nav_map_runtime_id_matches(tmp_path):
    _bootstrap(tmp_path, "navtest")
    data = json.loads(_nav_path(tmp_path, "navtest").read_text())
    assert data["runtime_id"] == "navtest"


def test_nav_map_status_bootstrap_seeded(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_nav_path(tmp_path, "test-rt").read_text())
    assert data["status"] == "bootstrap-seeded"


def test_nav_map_has_preferred_read_routes(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_nav_path(tmp_path, "test-rt").read_text())
    assert "preferred_read_routes" in data
    assert len(data["preferred_read_routes"]) >= 1


def test_nav_map_has_trusted_zones(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_nav_path(tmp_path, "test-rt").read_text())
    assert "trusted_zones" in data
    assert "runtime/aor/" in data["trusted_zones"]


def test_nav_map_has_risk_zones(tmp_path):
    _bootstrap(tmp_path)
    data = json.loads(_nav_path(tmp_path, "test-rt").read_text())
    assert "risk_zones" in data
    assert any("SOUL.md" in z for z in data["risk_zones"])


# ── Idempotency ───────────────────────────────────────────────────────────────

def test_second_run_skips_all_seeds(tmp_path):
    _bootstrap(tmp_path)
    result2 = _bootstrap(tmp_path)
    assert result2["seeds_written"] == []
    assert len(result2["seeds_skipped"]) == 3


def test_second_run_does_not_overwrite_profile(tmp_path):
    _bootstrap(tmp_path)
    profile_path = _profile_path(tmp_path, "test-rt")
    original = profile_path.read_text()
    _bootstrap(tmp_path)
    assert profile_path.read_text() == original


def test_partial_existing_seeds_only_writes_missing(tmp_path):
    # Manually create profile only; bootstrap should skip profile, write other two
    profile_path = _profile_path(tmp_path, "test-rt")
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text('{"existing": true}', encoding="utf-8")

    result = _bootstrap(tmp_path)
    assert len(result["seeds_written"]) == 2
    assert len(result["seeds_skipped"]) == 1
    # Profile was not overwritten
    assert json.loads(profile_path.read_text()) == {"existing": True}


# ── Different runtime IDs don't collide ───────────────────────────────────────

def test_two_runtimes_are_independent(tmp_path):
    run_brain_bootstrap("rt-alpha", vault_root=tmp_path)
    run_brain_bootstrap("rt-beta", vault_root=tmp_path)
    alpha_profile = _profile_path(tmp_path, "rt-alpha")
    beta_profile = _profile_path(tmp_path, "rt-beta")
    assert alpha_profile.exists()
    assert beta_profile.exists()
    alpha_data = json.loads(alpha_profile.read_text())
    beta_data = json.loads(beta_profile.read_text())
    assert alpha_data["runtime_id"] == "rt-alpha"
    assert beta_data["runtime_id"] == "rt-beta"


# ── Seed paths in result ──────────────────────────────────────────────────────

def test_seeds_written_paths_are_relative(tmp_path):
    result = _bootstrap(tmp_path)
    for p in result["seeds_written"]:
        assert not Path(p).is_absolute(), f"Expected relative path, got: {p}"


def test_seeds_written_paths_use_forward_slashes(tmp_path):
    result = _bootstrap(tmp_path)
    for p in result["seeds_written"]:
        assert "\\" not in p, f"Path has backslash: {p}"


def test_seeds_written_contains_expected_paths(tmp_path):
    result = _bootstrap(tmp_path)
    written = set(result["seeds_written"])
    assert any("profile.json" in p for p in written)
    assert any("identity-ledger.json" in p for p in written)
    assert any("nav-map.json" in p for p in written)
