"""
test_context_governance.py — Feature 12 (Context Governance Layer) tests

Coverage:
  - read_note_cgl: frontmatter parsing, path-based defaults, global defaults, clamp
  - resolve_context_eligibility: all block + restrict + eligible paths
  - check_write_compatibility: canonical vs log writeback routing
  - resolve_notes_eligibility: batch check, directories skipped, all_eligible flag
  - log_cgl_violation: JSONL append, idempotent, never raises
  - cgl_trust_level_from_sic: SIC → CGL trust mapping
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure runtime package is importable from the vault root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.aor.context_governance import (
    ACTION_TYPES,
    PROMOTION_STAGES,
    SENSITIVITY_LEVELS,
    TRUST_LEVELS,
    CglMetadata,
    CglResult,
    CglViolation,
    check_write_compatibility,
    cgl_trust_level_from_sic,
    log_cgl_violation,
    read_note_cgl,
    resolve_context_eligibility,
    resolve_notes_eligibility,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _write_note(tmp_path: Path, filename: str, content: str) -> Path:
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return p


def _note_with_cgl(tmp_path: Path, trust="reviewed", sensitivity="internal",
                   stage="promoted", surfaces=None, extra="") -> Path:
    surfaces_line = ""
    if surfaces:
        items = "\n".join(f"  - {s}" for s in surfaces)
        surfaces_line = f"allowed_surfaces:\n{items}"
    content = f"""---
type: knowledge-note
trust_level: {trust}
sensitivity: {sensitivity}
promotion_stage: {stage}
{surfaces_line}
{extra}
---

# Test note
"""
    return _write_note(tmp_path, "test_note.md", content)


def _note_without_cgl(tmp_path: Path) -> Path:
    content = """---
type: knowledge-note
domain: test
---

# No CGL frontmatter
"""
    return _write_note(tmp_path, "no_cgl_note.md", content)


def _role_card(cgl_min_trust: str = "", card_id: str = "test-card") -> dict:
    card = {"id": card_id}
    if cgl_min_trust:
        card["cgl_min_trust_level"] = cgl_min_trust
    return card


# ── Schema constants tests ────────────────────────────────────────────────────


class TestSchemaConstants:
    def test_trust_levels_ordered(self):
        assert TRUST_LEVELS == ["untrusted", "reviewed", "verified", "canonical"]

    def test_promotion_stages_ordered(self):
        assert PROMOTION_STAGES == ["quarantine", "promoted", "synthesized", "canonical"]

    def test_sensitivity_levels_complete(self):
        assert SENSITIVITY_LEVELS == {"internal", "operator-only", "shareable"}

    def test_action_types_complete(self):
        expected = {
            "read_context", "read_metadata", "write_canonical",
            "write_log", "surface_external", "index_for_retrieval",
        }
        assert ACTION_TYPES == expected


# ── read_note_cgl tests ───────────────────────────────────────────────────────


class TestReadNoteCgl:
    def test_reads_full_frontmatter(self, tmp_path):
        note = _note_with_cgl(tmp_path, trust="verified", sensitivity="operator-only", stage="canonical")
        cgl = read_note_cgl(note)
        assert cgl.trust_level == "verified"
        assert cgl.sensitivity == "operator-only"
        assert cgl.promotion_stage == "canonical"
        assert cgl.source == "frontmatter"

    def test_defaults_when_no_cgl_frontmatter_no_vault_root(self, tmp_path):
        note = _note_without_cgl(tmp_path)
        cgl = read_note_cgl(note)
        assert cgl.source == "global-default"
        assert cgl.trust_level == "reviewed"

    def test_path_default_quarantine(self, tmp_path):
        vault = tmp_path
        qdir = vault / "03_INPUTS" / "00_QUARANTINE" / "source"
        qdir.mkdir(parents=True)
        note = qdir / "raw.md"
        note.write_text("---\ntype: source-note\n---\n# raw\n", encoding="utf-8")
        cgl = read_note_cgl(note, vault_root=vault)
        assert cgl.trust_level == "untrusted"
        assert cgl.promotion_stage == "quarantine"
        assert cgl.source == "path-default"

    def test_path_default_inputs(self, tmp_path):
        vault = tmp_path
        idir = vault / "03_INPUTS" / "Digests"
        idir.mkdir(parents=True)
        note = idir / "digest.md"
        note.write_text("---\ntype: digest\n---\n# d\n", encoding="utf-8")
        cgl = read_note_cgl(note, vault_root=vault)
        assert cgl.trust_level == "untrusted"
        assert cgl.source == "path-default"

    def test_path_default_knowledge(self, tmp_path):
        vault = tmp_path
        kdir = vault / "02_KNOWLEDGE" / "Trading"
        kdir.mkdir(parents=True)
        note = kdir / "note.md"
        note.write_text("---\ntype: knowledge-note\n---\n# n\n", encoding="utf-8")
        cgl = read_note_cgl(note, vault_root=vault)
        assert cgl.trust_level == "reviewed"
        assert cgl.promotion_stage == "promoted"
        assert cgl.source == "path-default"

    def test_path_default_home(self, tmp_path):
        vault = tmp_path
        hdir = vault / "00_HOME"
        hdir.mkdir(parents=True)
        note = hdir / "Now.md"
        note.write_text("---\ntype: now\n---\n# now\n", encoding="utf-8")
        cgl = read_note_cgl(note, vault_root=vault)
        assert cgl.trust_level == "canonical"
        assert cgl.sensitivity == "operator-only"
        assert cgl.source == "path-default"

    def test_path_default_logs(self, tmp_path):
        vault = tmp_path
        ldir = vault / "07_LOGS" / "Build-Logs"
        ldir.mkdir(parents=True)
        note = ldir / "build.md"
        note.write_text("---\ntype: build-log\n---\n# b\n", encoding="utf-8")
        cgl = read_note_cgl(note, vault_root=vault)
        assert cgl.promotion_stage == "canonical"
        assert cgl.source == "path-default"

    def test_frontmatter_takes_precedence_over_path_default(self, tmp_path):
        vault = tmp_path
        kdir = vault / "02_KNOWLEDGE"
        kdir.mkdir(parents=True)
        # Note explicitly says canonical — overrides path default (reviewed)
        note = kdir / "note.md"
        note.write_text(
            "---\ntrust_level: canonical\nsensitivity: operator-only\npromotion_stage: canonical\n---\n# n\n",
            encoding="utf-8"
        )
        cgl = read_note_cgl(note, vault_root=vault)
        assert cgl.trust_level == "canonical"
        assert cgl.source == "frontmatter"

    def test_invalid_trust_level_clamped_to_reviewed(self, tmp_path):
        note = _note_with_cgl(tmp_path, trust="tier-3")  # non-CGL legacy value
        cgl = read_note_cgl(note)
        assert cgl.trust_level == "reviewed"
        assert cgl.source == "frontmatter"

    def test_invalid_sensitivity_clamped(self, tmp_path):
        note = _note_with_cgl(tmp_path, sensitivity="super-secret")
        cgl = read_note_cgl(note)
        assert cgl.sensitivity == "internal"

    def test_invalid_promotion_stage_clamped(self, tmp_path):
        note = _note_with_cgl(tmp_path, stage="draft")
        cgl = read_note_cgl(note)
        assert cgl.promotion_stage == "promoted"

    def test_allowed_surfaces_list(self, tmp_path):
        note = _note_with_cgl(tmp_path, surfaces=["discord", "email"])
        cgl = read_note_cgl(note)
        assert "discord" in cgl.allowed_surfaces
        assert "email" in cgl.allowed_surfaces

    def test_nonexistent_file_returns_global_default(self, tmp_path):
        ghost = tmp_path / "ghost.md"
        cgl = read_note_cgl(ghost)
        assert cgl.source == "global-default"

    def test_file_without_frontmatter_delimiter(self, tmp_path):
        note = tmp_path / "bare.md"
        note.write_text("# Just markdown, no frontmatter\n", encoding="utf-8")
        cgl = read_note_cgl(note)
        assert cgl.source == "global-default"

    def test_empty_frontmatter_returns_default(self, tmp_path):
        note = tmp_path / "empty_fm.md"
        note.write_text("---\n---\n# body\n", encoding="utf-8")
        cgl = read_note_cgl(note)
        assert cgl.source in ("global-default", "path-default")

    def test_trust_index_order(self, tmp_path):
        note = _note_with_cgl(tmp_path, trust="canonical")
        cgl = read_note_cgl(note)
        assert cgl.trust_index() == 3

        note2 = _note_with_cgl(tmp_path, trust="untrusted")
        cgl2 = read_note_cgl(note2)
        assert cgl2.trust_index() == 0


# ── resolve_context_eligibility tests ────────────────────────────────────────


class TestResolveContextEligibility:
    def _cgl(self, trust="reviewed", sensitivity="internal", stage="promoted", surfaces=None):
        return CglMetadata(
            trust_level=trust,
            sensitivity=sensitivity,
            promotion_stage=stage,
            allowed_surfaces=surfaces or [],
        )

    # Block: operator-only → surface_external
    def test_operator_only_blocked_for_surface_external(self):
        cgl = self._cgl(sensitivity="operator-only")
        result = resolve_context_eligibility(cgl, "surface_external", _role_card())
        assert result.eligibility == "blocked"
        assert "operator-only" in result.reason

    # Block: untrusted → write_canonical
    def test_untrusted_blocked_for_write_canonical(self):
        cgl = self._cgl(trust="untrusted")
        result = resolve_context_eligibility(cgl, "write_canonical", _role_card())
        assert result.eligibility == "blocked"
        assert "untrusted" in result.reason

    # Block: untrusted → surface_external
    def test_untrusted_blocked_for_surface_external(self):
        cgl = self._cgl(trust="untrusted")
        result = resolve_context_eligibility(cgl, "surface_external", _role_card())
        assert result.eligibility == "blocked"

    # Block: quarantine → write_canonical
    def test_quarantine_blocked_for_write_canonical(self):
        cgl = self._cgl(stage="quarantine")
        result = resolve_context_eligibility(cgl, "write_canonical", _role_card())
        assert result.eligibility == "blocked"
        assert "quarantine" in result.reason

    # Block: quarantine → surface_external
    def test_quarantine_blocked_for_surface_external(self):
        cgl = self._cgl(stage="quarantine")
        result = resolve_context_eligibility(cgl, "surface_external", _role_card())
        assert result.eligibility == "blocked"

    # Block: role card min trust not met
    def test_role_card_min_trust_blocks_when_note_below(self):
        cgl = self._cgl(trust="untrusted")
        card = _role_card(cgl_min_trust="reviewed")
        result = resolve_context_eligibility(cgl, "read_context", card)
        assert result.eligibility == "blocked"
        assert "cgl_min_trust_level" in result.reason

    def test_role_card_min_trust_passes_when_note_meets(self):
        cgl = self._cgl(trust="verified")
        card = _role_card(cgl_min_trust="reviewed")
        result = resolve_context_eligibility(cgl, "read_context", card)
        assert result.eligibility == "eligible"

    def test_role_card_min_trust_passes_when_note_exceeds(self):
        cgl = self._cgl(trust="canonical")
        card = _role_card(cgl_min_trust="reviewed")
        result = resolve_context_eligibility(cgl, "read_context", card)
        assert result.eligibility == "eligible"

    # Block: allowed_surfaces mismatch
    def test_allowed_surfaces_blocks_non_listed_role_card(self):
        cgl = self._cgl(surfaces=["discord"])
        card = {"id": "some-other-card"}
        result = resolve_context_eligibility(cgl, "read_context", card)
        assert result.eligibility == "blocked"
        assert "allowed_surfaces" in result.reason

    def test_allowed_surfaces_permits_listed_role_card(self):
        cgl = self._cgl(surfaces=["discord"])
        card = {"id": "discord"}
        result = resolve_context_eligibility(cgl, "read_context", card)
        assert result.eligibility == "eligible"

    def test_empty_allowed_surfaces_does_not_block(self):
        cgl = self._cgl(surfaces=[])
        result = resolve_context_eligibility(cgl, "read_context", _role_card())
        assert result.eligibility == "eligible"

    # Restrict: untrusted → read_context
    def test_untrusted_restricted_for_read_context(self):
        cgl = self._cgl(trust="untrusted")
        result = resolve_context_eligibility(cgl, "read_context", _role_card())
        assert result.eligibility == "restricted"
        assert "untrusted" in result.reason

    # Restrict: quarantine → read_context
    def test_quarantine_restricted_for_read_context(self):
        cgl = self._cgl(stage="quarantine")
        result = resolve_context_eligibility(cgl, "read_context", _role_card())
        assert result.eligibility == "restricted"

    # Restrict: quarantine → index_for_retrieval
    def test_quarantine_restricted_for_index_for_retrieval(self):
        cgl = self._cgl(stage="quarantine")
        result = resolve_context_eligibility(cgl, "index_for_retrieval", _role_card())
        assert result.eligibility == "restricted"

    # Eligible paths
    def test_reviewed_note_eligible_for_read_context(self):
        cgl = self._cgl(trust="reviewed")
        result = resolve_context_eligibility(cgl, "read_context", _role_card())
        assert result.eligibility == "eligible"

    def test_reviewed_note_eligible_for_index(self):
        cgl = self._cgl(trust="reviewed")
        result = resolve_context_eligibility(cgl, "index_for_retrieval", _role_card())
        assert result.eligibility == "eligible"

    def test_shareable_note_eligible_for_surface_external(self):
        cgl = self._cgl(sensitivity="shareable", trust="verified")
        result = resolve_context_eligibility(cgl, "surface_external", _role_card())
        assert result.eligibility == "eligible"

    def test_note_ref_propagated(self):
        cgl = self._cgl()
        result = resolve_context_eligibility(cgl, "read_context", _role_card(), note_ref="02_KNOWLEDGE/foo.md")
        assert result.note_ref == "02_KNOWLEDGE/foo.md"

    def test_action_type_propagated(self):
        cgl = self._cgl()
        result = resolve_context_eligibility(cgl, "write_log", _role_card())
        assert result.action_type == "write_log"

    def test_cgl_metadata_attached_to_result(self):
        cgl = self._cgl(trust="verified")
        result = resolve_context_eligibility(cgl, "read_context", _role_card())
        assert result.cgl_metadata is cgl

    # read_metadata is always eligible (no block/restrict rules target it)
    def test_read_metadata_always_eligible(self):
        for trust in TRUST_LEVELS:
            for stage in PROMOTION_STAGES:
                cgl = self._cgl(trust=trust, stage=stage)
                result = resolve_context_eligibility(cgl, "read_metadata", _role_card())
                assert result.eligibility == "eligible", (
                    f"Expected eligible for trust={trust} stage={stage} action=read_metadata"
                )

    def test_write_log_eligible_for_reviewed(self):
        cgl = self._cgl(trust="reviewed")
        result = resolve_context_eligibility(cgl, "write_log", _role_card())
        assert result.eligibility == "eligible"


# ── check_write_compatibility tests ──────────────────────────────────────────


class TestCheckWriteCompatibility:
    def _cgl(self, trust="reviewed", stage="promoted"):
        return CglMetadata(trust_level=trust, sensitivity="internal", promotion_stage=stage)

    def test_canonical_write_blocked_for_untrusted(self):
        cgl = self._cgl(trust="untrusted")
        result = check_write_compatibility(cgl, "02_KNOWLEDGE/foo.md", _role_card())
        assert result.eligibility == "blocked"

    def test_canonical_write_blocked_for_quarantine(self):
        cgl = self._cgl(stage="quarantine")
        result = check_write_compatibility(cgl, "01_PROJECTS/bar.md", _role_card())
        assert result.eligibility == "blocked"

    def test_canonical_write_eligible_for_reviewed(self):
        cgl = self._cgl(trust="reviewed")
        result = check_write_compatibility(cgl, "02_KNOWLEDGE/note.md", _role_card())
        assert result.eligibility == "eligible"

    def test_log_write_eligible_for_reviewed(self):
        cgl = self._cgl(trust="reviewed")
        result = check_write_compatibility(cgl, "07_LOGS/daily.md", _role_card())
        assert result.eligibility == "eligible"

    def test_log_write_eligible_for_untrusted(self):
        # Logs are less restrictive — untrusted source can produce a log entry
        cgl = self._cgl(trust="untrusted")
        result = check_write_compatibility(cgl, "07_LOGS/activity.md", _role_card())
        assert result.eligibility in ("eligible", "restricted")  # never blocked for write_log

    def test_projects_prefix_treated_as_canonical(self):
        cgl = self._cgl(trust="untrusted")
        result = check_write_compatibility(cgl, "01_PROJECTS/foo.md", _role_card())
        assert result.eligibility == "blocked"


# ── resolve_notes_eligibility tests ──────────────────────────────────────────


class TestResolveNotesEligibility:
    def test_all_eligible_returns_true(self, tmp_path):
        vault = tmp_path
        kdir = vault / "02_KNOWLEDGE"
        kdir.mkdir()
        n1 = kdir / "note1.md"
        n2 = kdir / "note2.md"
        n1.write_text("---\ntrust_level: reviewed\nsensitivity: internal\npromotion_stage: promoted\n---\n# n1\n")
        n2.write_text("---\ntrust_level: verified\nsensitivity: internal\npromotion_stage: canonical\n---\n# n2\n")

        all_ok, results = resolve_notes_eligibility(
            ["02_KNOWLEDGE/note1.md", "02_KNOWLEDGE/note2.md"],
            "read_context",
            _role_card(),
            vault_root=vault,
        )
        assert all_ok is True
        assert len(results) == 2
        assert all(r.eligibility == "eligible" for r in results)

    def test_one_blocked_returns_false(self, tmp_path):
        vault = tmp_path
        idir = vault / "03_INPUTS" / "00_QUARANTINE" / "source"
        idir.mkdir(parents=True)
        n1 = idir / "raw.md"
        n1.write_text("---\ntype: raw\n---\n# raw\n")

        kdir = vault / "02_KNOWLEDGE"
        kdir.mkdir()
        n2 = kdir / "note.md"
        n2.write_text("---\ntrust_level: reviewed\nsensitivity: internal\npromotion_stage: promoted\n---\n# n\n")

        all_ok, results = resolve_notes_eligibility(
            ["03_INPUTS/00_QUARANTINE/source/raw.md", "02_KNOWLEDGE/note.md"],
            "write_canonical",
            _role_card(),
            vault_root=vault,
        )
        assert all_ok is False

    def test_directories_are_skipped(self, tmp_path):
        vault = tmp_path
        kdir = vault / "02_KNOWLEDGE"
        kdir.mkdir()

        all_ok, results = resolve_notes_eligibility(
            ["02_KNOWLEDGE"],   # directory, not a file
            "read_context",
            _role_card(),
            vault_root=vault,
        )
        # Directory skipped → zero results, all_eligible vacuously True
        assert all_ok is True
        assert results == []

    def test_missing_paths_are_skipped(self, tmp_path):
        all_ok, results = resolve_notes_eligibility(
            ["02_KNOWLEDGE/ghost.md"],
            "read_context",
            _role_card(),
            vault_root=tmp_path,
        )
        assert all_ok is True
        assert results == []

    def test_empty_list_returns_true(self, tmp_path):
        all_ok, results = resolve_notes_eligibility([], "read_context", _role_card(), tmp_path)
        assert all_ok is True
        assert results == []

    def test_restricted_counts_as_not_all_eligible(self, tmp_path):
        vault = tmp_path
        idir = vault / "03_INPUTS" / "00_QUARANTINE" / "source"
        idir.mkdir(parents=True)
        n = idir / "q.md"
        n.write_text("---\ntype: raw\n---\n# raw\n")

        all_ok, results = resolve_notes_eligibility(
            ["03_INPUTS/00_QUARANTINE/source/q.md"],
            "read_context",    # quarantine→read_context is restricted
            _role_card(),
            vault_root=vault,
        )
        assert all_ok is False
        assert results[0].eligibility == "restricted"


# ── log_cgl_violation tests ───────────────────────────────────────────────────


class TestLogCglViolation:
    def _violation(self, note_ref="02_KNOWLEDGE/test.md", action_type="write_canonical"):
        return CglViolation(
            note_ref=note_ref,
            action_type=action_type,
            eligibility="blocked",
            reason="test violation",
            role_card_id="test-card",
        )

    def test_creates_violation_file(self, tmp_path):
        v = self._violation()
        log_cgl_violation(v, vault_root=tmp_path)
        log_file = tmp_path / "07_LOGS" / "Agent-Activity" / "cgl-violations.jsonl"
        assert log_file.exists()

    def test_violation_is_valid_jsonl(self, tmp_path):
        v = self._violation()
        log_cgl_violation(v, vault_root=tmp_path)
        log_file = tmp_path / "07_LOGS" / "Agent-Activity" / "cgl-violations.jsonl"
        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["note_ref"] == "02_KNOWLEDGE/test.md"
        assert record["action_type"] == "write_canonical"
        assert record["eligibility"] == "blocked"
        assert record["role_card_id"] == "test-card"

    def test_multiple_violations_appended(self, tmp_path):
        for i in range(3):
            v = self._violation(note_ref=f"note_{i}.md")
            log_cgl_violation(v, vault_root=tmp_path)

        log_file = tmp_path / "07_LOGS" / "Agent-Activity" / "cgl-violations.jsonl"
        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3

    def test_violation_record_has_required_fields(self, tmp_path):
        v = self._violation()
        log_cgl_violation(v, vault_root=tmp_path)
        log_file = tmp_path / "07_LOGS" / "Agent-Activity" / "cgl-violations.jsonl"
        record = json.loads(log_file.read_text(encoding="utf-8").strip())
        required_fields = {"violation_id", "timestamp_utc", "note_ref", "action_type",
                           "eligibility", "reason", "role_card_id"}
        assert required_fields <= record.keys()

    def test_never_raises_on_bad_vault_root(self, tmp_path):
        # Pass a file path as vault_root so mkdir will fail
        fake_root = tmp_path / "not_a_dir.txt"
        fake_root.write_text("not a directory")
        v = self._violation()
        log_cgl_violation(v, vault_root=fake_root)  # must not raise

    def test_violation_id_is_unique(self, tmp_path):
        v1 = self._violation()
        v2 = self._violation()
        assert v1.violation_id != v2.violation_id

    def test_timestamp_utc_format(self, tmp_path):
        v = self._violation()
        # Should be an ISO 8601 string
        assert "T" in v.timestamp_utc
        assert "+" in v.timestamp_utc or "Z" in v.timestamp_utc or "UTC" in v.timestamp_utc or v.timestamp_utc.endswith("+00:00")


# ── cgl_trust_level_from_sic tests ────────────────────────────────────────────


class TestCglTrustLevelFromSic:
    def test_trusted_maps_to_verified(self):
        assert cgl_trust_level_from_sic("trusted") == "verified"

    def test_reviewed_maps_to_reviewed(self):
        assert cgl_trust_level_from_sic("reviewed") == "reviewed"

    def test_untrusted_maps_to_untrusted(self):
        assert cgl_trust_level_from_sic("untrusted") == "untrusted"

    def test_none_maps_to_untrusted(self):
        assert cgl_trust_level_from_sic(None) == "untrusted"

    def test_empty_string_maps_to_untrusted(self):
        assert cgl_trust_level_from_sic("") == "untrusted"

    def test_unknown_value_maps_to_untrusted(self):
        assert cgl_trust_level_from_sic("super-trusted") == "untrusted"

    def test_all_sic_values_return_valid_cgl_trust(self):
        for sic_val in ("trusted", "reviewed", "untrusted"):
            result = cgl_trust_level_from_sic(sic_val)
            assert result in TRUST_LEVELS


# ── CglMetadata dataclass tests ───────────────────────────────────────────────


class TestCglMetadata:
    def test_default_values(self):
        cgl = CglMetadata()
        assert cgl.trust_level == "reviewed"
        assert cgl.sensitivity == "internal"
        assert cgl.promotion_stage == "promoted"
        assert cgl.allowed_surfaces == []
        assert cgl.source == "default"

    def test_trust_index_values(self):
        assert CglMetadata(trust_level="untrusted").trust_index() == 0
        assert CglMetadata(trust_level="reviewed").trust_index() == 1
        assert CglMetadata(trust_level="verified").trust_index() == 2
        assert CglMetadata(trust_level="canonical").trust_index() == 3

    def test_trust_index_unknown_returns_zero(self):
        assert CglMetadata(trust_level="tier-3").trust_index() == 0


# ── CglViolation dataclass tests ──────────────────────────────────────────────


class TestCglViolation:
    def test_auto_fields_populated(self):
        v = CglViolation(
            note_ref="foo.md",
            action_type="write_canonical",
            eligibility="blocked",
            reason="test",
            role_card_id="card-a",
        )
        assert len(v.violation_id) > 0
        assert len(v.timestamp_utc) > 0

    def test_two_violations_have_different_ids(self):
        v1 = CglViolation("a.md", "write_canonical", "blocked", "r", "c")
        v2 = CglViolation("b.md", "write_canonical", "blocked", "r", "c")
        assert v1.violation_id != v2.violation_id


# ── Integration: live note files ──────────────────────────────────────────────


class TestLiveNoteAnnotations:
    """
    Smoke tests using annotated knowledge notes from the live vault.
    These confirm that the 10 annotated notes parse correctly.
    """
    VAULT = Path(__file__).resolve().parents[2]  # vault root

    ANNOTATED_NOTES = [
        "02_KNOWLEDGE/Trading-Systems/CryptoMarkets.md",
        "02_KNOWLEDGE/Trading-Systems/Trading-Systems-Engineering.md",
        "02_KNOWLEDGE/Trading-Systems/perps-funding-rates-mechanics.md",
        "02_KNOWLEDGE/Trading-Systems/order-flow-market-microstructure.md",
        "02_KNOWLEDGE/AI-Agents/multi-agent-tool-use-patterns.md",
        "02_KNOWLEDGE/Trading-Systems/DeFi-Protocols.md",
        "02_KNOWLEDGE/AI-Agents/AI-Agent-Engineering.md",
        "02_KNOWLEDGE/Cybersecurity/Cybersecurity.md",
        "02_KNOWLEDGE/Doctrine/Doctrine-Philosophy.md",
        "02_KNOWLEDGE/Trading-Systems/Trade-Scoring-Framework.md",
    ]

    def test_annotated_notes_exist(self):
        for rel in self.ANNOTATED_NOTES:
            p = self.VAULT / rel
            assert p.exists(), f"Annotated note not found: {rel}"

    def test_annotated_notes_parse_valid_cgl(self):
        for rel in self.ANNOTATED_NOTES:
            p = self.VAULT / rel
            if not p.exists():
                continue
            cgl = read_note_cgl(p, vault_root=self.VAULT)
            assert cgl.trust_level in TRUST_LEVELS, (
                f"{rel}: unexpected trust_level={cgl.trust_level!r}"
            )
            assert cgl.sensitivity in SENSITIVITY_LEVELS, (
                f"{rel}: unexpected sensitivity={cgl.sensitivity!r}"
            )
            assert cgl.promotion_stage in PROMOTION_STAGES, (
                f"{rel}: unexpected promotion_stage={cgl.promotion_stage!r}"
            )

    def test_annotated_notes_eligible_for_read_context(self):
        card = _role_card()
        for rel in self.ANNOTATED_NOTES:
            p = self.VAULT / rel
            if not p.exists():
                continue
            cgl = read_note_cgl(p, vault_root=self.VAULT)
            result = resolve_context_eligibility(cgl, "read_context", card, note_ref=rel)
            # All annotated notes should be eligible or restricted (never blocked) for read_context
            assert result.eligibility in ("eligible", "restricted"), (
                f"{rel}: unexpected block for read_context: {result.reason}"
            )

    def test_doctrine_note_blocked_for_surface_external(self):
        p = self.VAULT / "02_KNOWLEDGE/Doctrine/Doctrine-Philosophy.md"
        if not p.exists():
            pytest.skip("Doctrine note not found")
        cgl = read_note_cgl(p, vault_root=self.VAULT)
        # Doctrine is annotated as operator-only → surface_external must be blocked
        if cgl.sensitivity == "operator-only":
            result = resolve_context_eligibility(cgl, "surface_external", _role_card())
            assert result.eligibility == "blocked"
