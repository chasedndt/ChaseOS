"""Tests for two-phase progressive graph loading.

Phase 1: get_graph_nodes_fast() — fast vault walk, nodes in ~4–8 s
Phase 2: get_graph_contract() — full parse, edges + rich metadata

Key invariant: Phase 1 node IDs must match Phase 2 node IDs (by SHA-256
of node_type + chr(31) + stable_key) so that position transfer works.
"""
from __future__ import annotations

import hashlib
import os
import types
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VAULT = Path(__file__).parent.parent.parent.parent  # repo root

def _make_fake_api(vault_root: str) -> object:
    """Return a minimal stub that exposes _vault_root like StudioAPI does."""
    api = MagicMock()
    api._vault_root = vault_root
    return api


def _canonical_id(node_type: str, stable_key: str) -> str:
    """Replicate graph_scanner_parser._node_id() exactly."""
    joined = f"{node_type}\x1f{stable_key}"
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()[:18]
    return f"studio:{node_type}:{digest}"


# ---------------------------------------------------------------------------
# Import the method under test
# ---------------------------------------------------------------------------

def _get_fast_fn():
    from runtime.studio.shell.api import StudioAPI
    return StudioAPI.get_graph_nodes_fast


# ---------------------------------------------------------------------------
# Unit tests: path-to-node_type mapping
# ---------------------------------------------------------------------------

class TestNodeTypeMapping:
    """get_graph_nodes_fast infers node_type from path the same way
    graph_scanner_parser does."""

    @pytest.fixture(autouse=True)
    def _fn(self):
        self.fn = _get_fast_fn()

    def _call(self, vault_dir: str) -> dict:
        stub = _make_fake_api(vault_dir)
        return self.fn(stub)

    def test_build_log_type(self, tmp_path):
        f = tmp_path / "07_LOGS" / "Build-Logs" / "2026-05-28-test.md"
        f.parent.mkdir(parents=True)
        f.write_text("# test")
        result = self._call(str(tmp_path))
        assert result["ok"], result
        nodes = result["data"]["nodes"]
        bl = [n for n in nodes if n["source_path"].startswith("07_LOGS/Build-Logs/")]
        assert bl, "expected build_log node"
        assert bl[0]["node_type"] == "build_log"
        assert bl[0]["node_family"] == "log_audit"

    def test_project_doc_type(self, tmp_path):
        f = tmp_path / "01_PROJECTS" / "Studio" / "Studio-OS.md"
        f.parent.mkdir(parents=True)
        f.write_text("# Studio OS")
        result = self._call(str(tmp_path))
        nodes = result["data"]["nodes"]
        proj = [n for n in nodes if n["node_type"] == "project_doc"]
        assert proj, "expected project_doc"
        assert proj[0]["node_family"] == "project"

    def test_knowledge_doc_type(self, tmp_path):
        f = tmp_path / "02_KNOWLEDGE" / "engineering" / "topic.md"
        f.parent.mkdir(parents=True)
        f.write_text("# topic")
        result = self._call(str(tmp_path))
        nodes = result["data"]["nodes"]
        kn = [n for n in nodes if n["node_type"] == "knowledge_doc"]
        assert kn

    def test_runtime_doc_type(self, tmp_path):
        f = tmp_path / "runtime" / "aor" / "engine.md"
        f.parent.mkdir(parents=True)
        f.write_text("# engine")
        result = self._call(str(tmp_path))
        nodes = result["data"]["nodes"]
        rt = [n for n in nodes if n["node_type"] == "runtime_doc"]
        assert rt

    def test_agent_control_doc_type(self, tmp_path):
        f = tmp_path / "06_AGENTS" / "AOR.md"
        f.parent.mkdir(parents=True)
        f.write_text("# AOR")
        result = self._call(str(tmp_path))
        nodes = result["data"]["nodes"]
        ac = [n for n in nodes if n["node_type"] == "agent_control_doc"]
        assert ac
        assert ac[0]["node_family"] == "agent"

    def test_system_root_doc(self, tmp_path):
        (tmp_path / "README.md").write_text("# readme")
        result = self._call(str(tmp_path))
        nodes = result["data"]["nodes"]
        sr = [n for n in nodes if n["node_type"] == "system_root_doc"]
        assert sr

    def test_decision_doc_type(self, tmp_path):
        # "decision" in path triggers decision_doc ONLY for paths not caught
        # by earlier prefix rules (07_LOGS/ captures log_audit first).
        # A decision file at the top level or under a non-special directory works.
        f = tmp_path / "decision-architecture-notes.md"
        f.write_text("# Decision")
        result = self._call(str(tmp_path))
        nodes = result["data"]["nodes"]
        dd = [n for n in nodes if n["node_type"] == "decision_doc"]
        assert dd, "expected decision_doc for root-level decision file"

    def test_intake_doc_type(self, tmp_path):
        f = tmp_path / "03_INPUTS" / "some-clip.md"
        f.parent.mkdir(parents=True)
        f.write_text("# clip")
        result = self._call(str(tmp_path))
        nodes = result["data"]["nodes"]
        intake = [n for n in nodes if n["node_type"] == "intake_doc"]
        assert intake

    def test_sop_template_type(self, tmp_path):
        for prefix in ("04_SOPS", "05_TEMPLATES"):
            f = tmp_path / prefix / "something.md"
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("# sop")
        result = self._call(str(tmp_path))
        nodes = result["data"]["nodes"]
        sops = [n for n in nodes if n["node_type"] == "sop_template_doc"]
        assert sops


# ---------------------------------------------------------------------------
# Unit tests: trust_state
# ---------------------------------------------------------------------------

class TestTrustState:
    @pytest.fixture(autouse=True)
    def _fn(self):
        self.fn = _get_fast_fn()

    def _call(self, vault_dir: str) -> list[dict]:
        stub = _make_fake_api(vault_dir)
        result = self.fn(stub)
        return result["data"]["nodes"]

    def test_canonical_trust(self, tmp_path):
        f = tmp_path / "01_PROJECTS" / "foo.md"
        f.parent.mkdir()
        f.write_text("x")
        nodes = self._call(str(tmp_path))
        assert nodes[0]["trust_state"] == "canonical"

    def test_archived_trust(self, tmp_path):
        f = tmp_path / "99_ARCHIVE" / "old.md"
        f.parent.mkdir()
        f.write_text("x")
        nodes = self._call(str(tmp_path))
        assert nodes[0]["trust_state"] == "archived"

    def test_quarantined_trust(self, tmp_path):
        f = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "clip.md"
        f.parent.mkdir(parents=True)
        f.write_text("x")
        nodes = self._call(str(tmp_path))
        assert any(n["trust_state"] == "quarantined" for n in nodes)


# ---------------------------------------------------------------------------
# Unit tests: ID matches graph_scanner_parser formula
# ---------------------------------------------------------------------------

class TestIdFormula:
    """Critical invariant: Phase 1 IDs must equal Phase 2 IDs so positions
    computed by the force simulation in Phase 1 can be ported to Phase 2."""

    @pytest.fixture(autouse=True)
    def _fn(self):
        self.fn = _get_fast_fn()

    def test_project_doc_id_matches_canonical(self, tmp_path):
        f = tmp_path / "01_PROJECTS" / "Studio" / "Studio-OS.md"
        f.parent.mkdir(parents=True)
        f.write_text("# Studio OS")
        stub = _make_fake_api(str(tmp_path))
        result = self.fn(stub)
        nodes = result["data"]["nodes"]
        n = nodes[0]
        expected = _canonical_id("project_doc", "01_PROJECTS/Studio/Studio-OS.md")
        assert n["id"] == expected, f"ID mismatch: {n['id']} != {expected}"

    def test_build_log_id_matches_canonical(self, tmp_path):
        f = tmp_path / "07_LOGS" / "Build-Logs" / "2026-05-28-test.md"
        f.parent.mkdir(parents=True)
        f.write_text("x")
        stub = _make_fake_api(str(tmp_path))
        result = self.fn(stub)
        nodes = result["data"]["nodes"]
        n = nodes[0]
        expected = _canonical_id("build_log", "07_LOGS/Build-Logs/2026-05-28-test.md")
        assert n["id"] == expected

    def test_runtime_doc_id_matches_canonical(self, tmp_path):
        f = tmp_path / "runtime" / "aor" / "engine.md"
        f.parent.mkdir(parents=True)
        f.write_text("x")
        stub = _make_fake_api(str(tmp_path))
        result = self.fn(stub)
        nodes = result["data"]["nodes"]
        n = nodes[0]
        expected = _canonical_id("runtime_doc", "runtime/aor/engine.md")
        assert n["id"] == expected

    def test_root_file_id_matches_canonical(self, tmp_path):
        f = tmp_path / "README.md"
        f.write_text("# readme")
        stub = _make_fake_api(str(tmp_path))
        result = self.fn(stub)
        nodes = result["data"]["nodes"]
        n = nodes[0]
        expected = _canonical_id("system_root_doc", "README.md")
        assert n["id"] == expected

    def test_deeply_nested_id_matches_canonical(self, tmp_path):
        f = tmp_path / "02_KNOWLEDGE" / "engineering" / "subdir" / "deep.md"
        f.parent.mkdir(parents=True)
        f.write_text("x")
        stub = _make_fake_api(str(tmp_path))
        result = self.fn(stub)
        nodes = result["data"]["nodes"]
        n = nodes[0]
        expected = _canonical_id("knowledge_doc", "02_KNOWLEDGE/engineering/subdir/deep.md")
        assert n["id"] == expected


# ---------------------------------------------------------------------------
# Unit tests: skip dirs and file filters
# ---------------------------------------------------------------------------

class TestSkipDirs:
    @pytest.fixture(autouse=True)
    def _fn(self):
        self.fn = _get_fast_fn()

    def _call(self, vault_dir: str):
        stub = _make_fake_api(vault_dir)
        result = self.fn(stub)
        return result["data"]["nodes"]

    def test_skips_venv(self, tmp_path):
        venv = tmp_path / ".venv" / "lib" / "site.md"
        venv.parent.mkdir(parents=True)
        venv.write_text("x")
        real = tmp_path / "README.md"
        real.write_text("x")
        nodes = self._call(str(tmp_path))
        assert len(nodes) == 1
        assert nodes[0]["source_path"] == "README.md"

    def test_skips_git(self, tmp_path):
        git_file = tmp_path / ".git" / "HEAD.md"
        git_file.parent.mkdir(parents=True)
        git_file.write_text("x")
        real = tmp_path / "README.md"
        real.write_text("x")
        nodes = self._call(str(tmp_path))
        paths = [n["source_path"] for n in nodes]
        assert not any(".git" in p for p in paths)

    def test_skips_non_md_files(self, tmp_path):
        (tmp_path / "note.md").write_text("x")
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        (tmp_path / "script.py").write_text("pass")
        nodes = self._call(str(tmp_path))
        assert len(nodes) == 1
        assert nodes[0]["label"] == "note"

    def test_skips_pycache(self, tmp_path):
        pc = tmp_path / "__pycache__" / "cached.md"
        pc.parent.mkdir()
        pc.write_text("x")
        (tmp_path / "real.md").write_text("x")
        nodes = self._call(str(tmp_path))
        assert len(nodes) == 1


# ---------------------------------------------------------------------------
# Unit tests: response shape
# ---------------------------------------------------------------------------

class TestResponseShape:
    @pytest.fixture(autouse=True)
    def _fn(self):
        self.fn = _get_fast_fn()

    def test_ok_response_structure(self, tmp_path):
        (tmp_path / "note.md").write_text("x")
        stub = _make_fake_api(str(tmp_path))
        result = self.fn(stub)
        assert result["ok"] is True
        assert "data" in result
        assert "nodes" in result["data"]
        assert "node_count" in result["data"]
        assert result["data"]["fast_loaded"] is True

    def test_node_has_required_fields(self, tmp_path):
        (tmp_path / "note.md").write_text("x")
        stub = _make_fake_api(str(tmp_path))
        result = self.fn(stub)
        n = result["data"]["nodes"][0]
        for field in ("id", "label", "display_label", "node_type", "node_family",
                      "trust_state", "source_path", "domain", "_fast_loaded"):
            assert field in n, f"missing field: {field}"

    def test_fast_loaded_flag(self, tmp_path):
        (tmp_path / "note.md").write_text("x")
        stub = _make_fake_api(str(tmp_path))
        result = self.fn(stub)
        n = result["data"]["nodes"][0]
        assert n["_fast_loaded"] is True

    def test_label_strips_md_extension(self, tmp_path):
        (tmp_path / "My-Note.md").write_text("x")
        stub = _make_fake_api(str(tmp_path))
        result = self.fn(stub)
        n = result["data"]["nodes"][0]
        assert n["label"] == "My-Note"
        assert n["display_label"] == "My-Note"

    def test_node_count_matches_nodes_length(self, tmp_path):
        for i in range(5):
            (tmp_path / f"note{i}.md").write_text("x")
        stub = _make_fake_api(str(tmp_path))
        result = self.fn(stub)
        assert result["data"]["node_count"] == len(result["data"]["nodes"])

    def test_error_on_bad_vault(self):
        stub = _make_fake_api("/nonexistent/vault/path/xyz")
        result = self.fn(stub)
        # Should return error (vault path doesn't exist)
        # os.walk on nonexistent path just yields nothing — so ok with 0 nodes
        # or it raises; either way the method should not crash the caller.
        assert "ok" in result


# ---------------------------------------------------------------------------
# Integration smoke test against real vault (skipped if vault not present)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not VAULT.exists(), reason="real vault not found")
class TestRealVaultSmoke:
    def test_real_vault_returns_nodes(self):
        fn = _get_fast_fn()
        vault_str = str(VAULT)
        stub = _make_fake_api(vault_str)
        result = fn(stub)
        assert result["ok"], result.get("error")
        nodes = result["data"]["nodes"]
        # Vault has several thousand nodes — sanity-check lower bound
        assert len(nodes) > 100, f"expected >100 nodes, got {len(nodes)}"

    def test_real_vault_has_all_families(self):
        fn = _get_fast_fn()
        stub = _make_fake_api(str(VAULT))
        result = fn(stub)
        families = {n["node_family"] for n in result["data"]["nodes"]}
        expected = {"project", "knowledge", "agent", "runtime", "log_audit"}
        missing = expected - families
        assert not missing, f"missing families: {missing}"

    def test_real_vault_ids_match_canonical_formula(self):
        """Spot-check 10 nodes from the real vault for ID correctness."""
        fn = _get_fast_fn()
        stub = _make_fake_api(str(VAULT))
        result = fn(stub)
        nodes = result["data"]["nodes"]
        # Check first 10 nodes
        for n in nodes[:10]:
            nt = n["node_type"]
            sk = n["source_path"]
            expected = _canonical_id(nt, sk)
            assert n["id"] == expected, (
                f"ID mismatch for {sk}: got {n['id']}, expected {expected}"
            )

    def test_real_vault_source_path_is_posix(self):
        fn = _get_fast_fn()
        stub = _make_fake_api(str(VAULT))
        result = fn(stub)
        for n in result["data"]["nodes"]:
            assert "\\" not in n["source_path"], (
                f"Windows separator in source_path: {n['source_path']}"
            )

    def test_real_vault_no_venv_paths(self):
        fn = _get_fast_fn()
        stub = _make_fake_api(str(VAULT))
        result = fn(stub)
        bad = [n for n in result["data"]["nodes"] if ".venv/" in n["source_path"]]
        assert not bad, f"found .venv paths: {[n['source_path'] for n in bad[:5]]}"
