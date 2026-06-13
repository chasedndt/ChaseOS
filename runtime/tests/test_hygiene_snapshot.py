"""
test_hygiene_snapshot.py — Tests for runtime/workflows/hygiene_snapshot.py

Covers:
  Unit tests for sha256_file, collect_pre_snapshot, write_snapshot_dir,
  compute_diff_records, write_diff_json.

  Integration tests for the os_hygiene_graph snapshot wiring: verifies that
  snapshot_taken, snapshot_dir, snapshot_modified_count appear in the result
  dict and that the on-disk snapshot/diff files are created correctly.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.cli.vault_hygiene import HygieneReport, Issue
from runtime.workflows.hygiene_snapshot import (
    MAX_SNAPSHOT_FILE_BYTES,
    MAX_SNAPSHOT_FILES,
    SNAPSHOT_ROOT,
    collect_pre_snapshot,
    compute_diff_records,
    sha256_file,
    write_diff_json,
    write_snapshot_dir,
)
from runtime.workflows.os_hygiene_graph import run_os_hygiene_graph


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _auto_fix_issue(file_path: str) -> Issue:
    return Issue(
        category="backtick_wikilink",
        severity="auto_fix",
        file_path=file_path,
        index_path="",
        description="test issue",
    )


def _review_issue(file_path: str) -> Issue:
    return Issue(
        category="loose_node",
        severity="review_required",
        file_path=file_path,
        index_path="",
        description="test review issue",
    )


def _report_with_issues(issues: list[Issue]) -> HygieneReport:
    r = HygieneReport()
    r.issues = issues
    r.files_scanned = len(issues)
    return r


# ===========================================================================
# sha256_file
# ===========================================================================

class TestSha256File:
    def test_hashes_file_content(self, tmp_path):
        f = tmp_path / "a.md"
        f.write_bytes(b"hello vault")
        assert sha256_file(f) == _sha256_bytes(b"hello vault")

    def test_hashes_empty_file(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_bytes(b"")
        assert sha256_file(f) == _sha256_bytes(b"")

    def test_missing_file_returns_empty_string(self, tmp_path):
        assert sha256_file(tmp_path / "nonexistent.md") == ""

    def test_different_content_different_hash(self, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_bytes(b"content A")
        b.write_bytes(b"content B")
        assert sha256_file(a) != sha256_file(b)


# ===========================================================================
# collect_pre_snapshot
# ===========================================================================

class TestCollectPreSnapshot:
    def test_captures_auto_fix_files(self, tmp_path):
        f = tmp_path / "SOUL.md"
        f.write_text("# soul", encoding="utf-8")
        report = _report_with_issues([_auto_fix_issue("SOUL.md")])
        result = collect_pre_snapshot(tmp_path, report)
        assert "SOUL.md" in result
        assert result["SOUL.md"] == sha256_file(f)

    def test_ignores_review_required_issues(self, tmp_path):
        f = tmp_path / "loose.md"
        f.write_text("# loose", encoding="utf-8")
        report = _report_with_issues([_review_issue("loose.md")])
        result = collect_pre_snapshot(tmp_path, report)
        assert result == {}

    def test_deduplicates_same_file_in_multiple_issues(self, tmp_path):
        f = tmp_path / "dup.md"
        f.write_text("# dup", encoding="utf-8")
        report = _report_with_issues([
            _auto_fix_issue("dup.md"),
            _auto_fix_issue("dup.md"),
        ])
        result = collect_pre_snapshot(tmp_path, report)
        assert len(result) == 1
        assert "dup.md" in result

    def test_skips_missing_files(self, tmp_path):
        report = _report_with_issues([_auto_fix_issue("does_not_exist.md")])
        result = collect_pre_snapshot(tmp_path, report)
        assert result == {}

    def test_skips_oversized_files(self, tmp_path):
        f = tmp_path / "big.md"
        f.write_bytes(b"x" * (MAX_SNAPSHOT_FILE_BYTES + 1))
        report = _report_with_issues([_auto_fix_issue("big.md")])
        result = collect_pre_snapshot(tmp_path, report)
        assert result == {}

    def test_accepts_files_at_size_limit(self, tmp_path):
        f = tmp_path / "edge.md"
        f.write_bytes(b"x" * MAX_SNAPSHOT_FILE_BYTES)
        report = _report_with_issues([_auto_fix_issue("edge.md")])
        result = collect_pre_snapshot(tmp_path, report)
        assert "edge.md" in result

    def test_bounded_by_max_snapshot_files(self, tmp_path):
        issues = []
        for i in range(MAX_SNAPSHOT_FILES + 10):
            f = tmp_path / f"file_{i}.md"
            f.write_text(f"# {i}", encoding="utf-8")
            issues.append(_auto_fix_issue(f"file_{i}.md"))
        report = _report_with_issues(issues)
        result = collect_pre_snapshot(tmp_path, report)
        assert len(result) == MAX_SNAPSHOT_FILES

    def test_empty_report_returns_empty(self, tmp_path):
        report = HygieneReport()
        result = collect_pre_snapshot(tmp_path, report)
        assert result == {}

    def test_nested_path_captured(self, tmp_path):
        sub = tmp_path / "06_AGENTS"
        sub.mkdir()
        f = sub / "Permission-Matrix.md"
        f.write_text("# pm", encoding="utf-8")
        report = _report_with_issues([_auto_fix_issue("06_AGENTS/Permission-Matrix.md")])
        result = collect_pre_snapshot(tmp_path, report)
        assert "06_AGENTS/Permission-Matrix.md" in result


# ===========================================================================
# write_snapshot_dir
# ===========================================================================

class TestWriteSnapshotDir:
    def test_creates_snapshot_directory(self, tmp_path):
        f = tmp_path / "a.md"
        f.write_text("# a", encoding="utf-8")
        snapshots = {"a.md": sha256_file(f)}
        sd = write_snapshot_dir(tmp_path, snapshots, "2026-05-11")
        assert sd.is_dir()

    def test_dir_name_includes_date_str(self, tmp_path):
        sd = write_snapshot_dir(tmp_path, {}, "2026-05-11")
        assert "2026-05-11" in sd.name
        assert "pre-hygiene" in sd.name

    def test_creates_manifest_json(self, tmp_path):
        f = tmp_path / "a.md"
        f.write_text("# a", encoding="utf-8")
        snapshots = {"a.md": sha256_file(f)}
        sd = write_snapshot_dir(tmp_path, snapshots, "2026-05-11")
        manifest_path = sd / "snapshot_manifest.json"
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text())
        assert data["date"] == "2026-05-11"
        assert len(data["files"]) == 1

    def test_manifest_records_sha256_before(self, tmp_path):
        f = tmp_path / "a.md"
        f.write_text("original", encoding="utf-8")
        h = sha256_file(f)
        snapshots = {"a.md": h}
        sd = write_snapshot_dir(tmp_path, snapshots, "2026-05-11")
        manifest = json.loads((sd / "snapshot_manifest.json").read_text())
        assert manifest["files"][0]["sha256_before"] == h

    def test_copies_file_content(self, tmp_path):
        f = tmp_path / "a.md"
        content = b"original content"
        f.write_bytes(content)
        snapshots = {"a.md": sha256_file(f)}
        sd = write_snapshot_dir(tmp_path, snapshots, "2026-05-11")
        copy = sd / "a.md"
        assert copy.exists()
        assert copy.read_bytes() == content

    def test_flattens_nested_path(self, tmp_path):
        sub = tmp_path / "06_AGENTS"
        sub.mkdir()
        f = sub / "perm.md"
        f.write_text("# perm", encoding="utf-8")
        snapshots = {"06_AGENTS/perm.md": sha256_file(f)}
        sd = write_snapshot_dir(tmp_path, snapshots, "2026-05-11")
        flat = sd / "06_AGENTS__perm.md"
        assert flat.exists()

    def test_snapshot_dir_placed_under_snapshot_root(self, tmp_path):
        sd = write_snapshot_dir(tmp_path, {}, "2026-05-11")
        expected_parent = tmp_path / SNAPSHOT_ROOT
        assert sd.parent == expected_parent

    def test_empty_snapshots_creates_empty_manifest(self, tmp_path):
        sd = write_snapshot_dir(tmp_path, {}, "2026-05-11")
        manifest = json.loads((sd / "snapshot_manifest.json").read_text())
        assert manifest["files"] == []

    def test_skips_missing_source_file(self, tmp_path):
        snapshots = {"ghost.md": "deadbeef"}
        sd = write_snapshot_dir(tmp_path, snapshots, "2026-05-11")
        manifest = json.loads((sd / "snapshot_manifest.json").read_text())
        assert manifest["files"] == []


# ===========================================================================
# compute_diff_records
# ===========================================================================

class TestComputeDiffRecords:
    def test_unchanged_file_marked_unchanged(self, tmp_path):
        f = tmp_path / "a.md"
        f.write_text("same content", encoding="utf-8")
        h = sha256_file(f)
        records = compute_diff_records(tmp_path, {"a.md": h})
        assert records[0]["change_type"] == "unchanged"
        assert records[0]["new_sha256"] == h

    def test_modified_file_marked_modified(self, tmp_path):
        f = tmp_path / "a.md"
        f.write_text("before", encoding="utf-8")
        old_h = sha256_file(f)
        f.write_text("after mutation", encoding="utf-8")
        records = compute_diff_records(tmp_path, {"a.md": old_h})
        assert records[0]["change_type"] == "modified"
        assert records[0]["old_sha256"] == old_h
        assert records[0]["new_sha256"] != old_h

    def test_deleted_file_marked_deleted(self, tmp_path):
        records = compute_diff_records(tmp_path, {"gone.md": "abc123"})
        assert records[0]["change_type"] == "deleted"
        assert records[0]["new_sha256"] == ""
        assert records[0]["old_sha256"] == "abc123"

    def test_empty_before_returns_empty(self, tmp_path):
        assert compute_diff_records(tmp_path, {}) == []

    def test_multiple_files_all_classified(self, tmp_path):
        unchanged = tmp_path / "a.md"
        unchanged.write_text("same", encoding="utf-8")
        modified = tmp_path / "b.md"
        modified.write_text("before", encoding="utf-8")
        old_b = sha256_file(modified)
        modified.write_text("after", encoding="utf-8")

        before = {
            "a.md": sha256_file(unchanged),
            "b.md": old_b,
            "c.md": "fakehash",
        }
        records = compute_diff_records(tmp_path, before)
        by_path = {r["path"]: r["change_type"] for r in records}
        assert by_path["a.md"] == "unchanged"
        assert by_path["b.md"] == "modified"
        assert by_path["c.md"] == "deleted"

    def test_records_include_both_hashes(self, tmp_path):
        f = tmp_path / "a.md"
        f.write_text("v1", encoding="utf-8")
        old_h = sha256_file(f)
        f.write_text("v2", encoding="utf-8")
        new_h = sha256_file(f)
        records = compute_diff_records(tmp_path, {"a.md": old_h})
        assert records[0]["old_sha256"] == old_h
        assert records[0]["new_sha256"] == new_h


# ===========================================================================
# write_diff_json
# ===========================================================================

class TestWriteDiffJson:
    def test_creates_diff_log_json(self, tmp_path):
        diff_records = [
            {"path": "a.md", "old_sha256": "old", "new_sha256": "new", "change_type": "modified"},
        ]
        path = write_diff_json(tmp_path, diff_records)
        assert path.name == "diff_log.json"
        assert path.exists()

    def test_structure_has_required_keys(self, tmp_path):
        diff_records = [
            {"path": "a.md", "old_sha256": "x", "new_sha256": "y", "change_type": "modified"},
            {"path": "b.md", "old_sha256": "z", "new_sha256": "z", "change_type": "unchanged"},
            {"path": "c.md", "old_sha256": "q", "new_sha256": "", "change_type": "deleted"},
        ]
        write_diff_json(tmp_path, diff_records)
        data = json.loads((tmp_path / "diff_log.json").read_text())
        assert data["total_files_snapshotted"] == 3
        assert data["modified_count"] == 1
        assert data["deleted_count"] == 1
        assert len(data["records"]) == 3

    def test_empty_records_structure(self, tmp_path):
        write_diff_json(tmp_path, [])
        data = json.loads((tmp_path / "diff_log.json").read_text())
        assert data["total_files_snapshotted"] == 0
        assert data["modified_count"] == 0
        assert data["deleted_count"] == 0
        assert data["records"] == []

    def test_returns_diff_log_path(self, tmp_path):
        p = write_diff_json(tmp_path, [])
        assert p == tmp_path / "diff_log.json"


# ===========================================================================
# os_hygiene_graph integration — snapshot wiring
# ===========================================================================

class TestOsHygieneGraphSnapshotWiring:
    """Verify that run_os_hygiene_graph wires the snapshot correctly."""

    def _setup_mocks(self, monkeypatch, tmp_path, files_scanned=5, files_fixed=2):
        import runtime.cli.daily_hub_linker as daily_hub_mod
        import runtime.cli.provenance_linker as provenance_mod
        import runtime.cli.vault_hygiene as hygiene_mod

        report = HygieneReport()
        report.files_scanned = files_scanned
        report.files_fixed = files_fixed
        report.wikilinks_fixed = 1
        report.nodes_wired = 1
        report.junk_flagged = 0

        monkeypatch.setattr(hygiene_mod, "scan_vault", lambda vault_root, **kw: report)
        monkeypatch.setattr(hygiene_mod, "build_loose_node_review_queue", lambda r, vr: [])
        monkeypatch.setattr(hygiene_mod, "summarize_issues", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "summarize_node_categories", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "render_report", lambda r, vr: "# report\n")
        monkeypatch.setattr(hygiene_mod, "apply_fixes", lambda vr, r, **kw: None)
        monkeypatch.setattr(
            daily_hub_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, dates_found=0, notes_created=0,
                notes_updated=0, backlinks_added=0, index_updated=False,
            )
        )
        monkeypatch.setattr(
            provenance_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, files_modified=0, links_added={},
            )
        )
        return report

    def test_stage1_has_snapshot_fields(self, monkeypatch, tmp_path):
        self._setup_mocks(monkeypatch, tmp_path)
        result = run_os_hygiene_graph({}, tmp_path)
        s1 = result["stage_1_vault_hygiene"]
        assert "snapshot_taken" in s1
        assert "snapshot_dir" in s1
        assert "snapshot_files_count" in s1
        assert "snapshot_modified_count" in s1
        assert "snapshot_deleted_count" in s1
        assert "snapshot_diff_records" in s1

    def test_no_snapshot_when_dry_run(self, monkeypatch, tmp_path):
        self._setup_mocks(monkeypatch, tmp_path)
        result = run_os_hygiene_graph({"dry_run": True}, tmp_path)
        s1 = result["stage_1_vault_hygiene"]
        assert s1["snapshot_taken"] is False
        assert s1["snapshot_dir"] is None
        assert s1["snapshot_files_count"] == 0

    def test_no_snapshot_when_strict_blocked(self, monkeypatch, tmp_path):
        import runtime.cli.vault_hygiene as hygiene_mod
        report = HygieneReport()
        report.files_scanned = 3
        monkeypatch.setattr(hygiene_mod, "scan_vault", lambda vr, **kw: report)
        monkeypatch.setattr(hygiene_mod, "build_loose_node_review_queue", lambda r, vr: [{"file": "a.md"}])
        monkeypatch.setattr(hygiene_mod, "summarize_issues", lambda r: {"duplicate_candidate": 1})
        monkeypatch.setattr(hygiene_mod, "summarize_node_categories", lambda r: {})
        result = run_os_hygiene_graph({}, tmp_path)
        assert result["status"] == "blocked_review_required"
        s1 = result["stage_1_vault_hygiene"]
        assert s1["snapshot_taken"] is False

    def test_snapshot_taken_true_when_fixable_issues_exist(self, monkeypatch, tmp_path):
        import runtime.cli.vault_hygiene as hygiene_mod
        import runtime.cli.daily_hub_linker as daily_hub_mod
        import runtime.cli.provenance_linker as provenance_mod

        # Create a real file that will be in the report
        target = tmp_path / "fixable.md"
        target.write_text("# fix me", encoding="utf-8")

        report = HygieneReport()
        report.files_scanned = 1
        report.files_fixed = 1
        report.issues = [_auto_fix_issue("fixable.md")]

        monkeypatch.setattr(hygiene_mod, "scan_vault", lambda vr, **kw: report)
        monkeypatch.setattr(hygiene_mod, "build_loose_node_review_queue", lambda r, vr: [])
        monkeypatch.setattr(hygiene_mod, "summarize_issues", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "summarize_node_categories", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "render_report", lambda r, vr: "# report\n")
        monkeypatch.setattr(hygiene_mod, "apply_fixes", lambda vr, r, **kw: None)
        monkeypatch.setattr(
            daily_hub_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, dates_found=0, notes_created=0,
                notes_updated=0, backlinks_added=0, index_updated=False,
            )
        )
        monkeypatch.setattr(
            provenance_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, files_modified=0, links_added={},
            )
        )

        result = run_os_hygiene_graph({}, tmp_path)
        s1 = result["stage_1_vault_hygiene"]
        assert s1["snapshot_taken"] is True
        assert s1["snapshot_files_count"] == 1

    def test_snapshot_dir_created_on_disk(self, monkeypatch, tmp_path):
        import runtime.cli.vault_hygiene as hygiene_mod
        import runtime.cli.daily_hub_linker as daily_hub_mod
        import runtime.cli.provenance_linker as provenance_mod

        target = tmp_path / "fixable.md"
        target.write_text("# fix me", encoding="utf-8")

        report = HygieneReport()
        report.files_scanned = 1
        report.files_fixed = 1
        report.issues = [_auto_fix_issue("fixable.md")]

        monkeypatch.setattr(hygiene_mod, "scan_vault", lambda vr, **kw: report)
        monkeypatch.setattr(hygiene_mod, "build_loose_node_review_queue", lambda r, vr: [])
        monkeypatch.setattr(hygiene_mod, "summarize_issues", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "summarize_node_categories", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "render_report", lambda r, vr: "# report\n")
        monkeypatch.setattr(hygiene_mod, "apply_fixes", lambda vr, r, **kw: None)
        monkeypatch.setattr(
            daily_hub_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, dates_found=0, notes_created=0,
                notes_updated=0, backlinks_added=0, index_updated=False,
            )
        )
        monkeypatch.setattr(
            provenance_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, files_modified=0, links_added={},
            )
        )

        result = run_os_hygiene_graph({}, tmp_path)
        s1 = result["stage_1_vault_hygiene"]

        assert s1["snapshot_dir"] is not None
        snapshot_dir = tmp_path / s1["snapshot_dir"]
        assert snapshot_dir.is_dir()
        assert (snapshot_dir / "snapshot_manifest.json").exists()
        assert (snapshot_dir / "diff_log.json").exists()

    def test_modified_file_detected_in_diff(self, monkeypatch, tmp_path):
        import runtime.cli.vault_hygiene as hygiene_mod
        import runtime.cli.daily_hub_linker as daily_hub_mod
        import runtime.cli.provenance_linker as provenance_mod

        target = tmp_path / "mutated.md"
        target.write_text("before mutation", encoding="utf-8")
        original_hash = sha256_file(target)

        report = HygieneReport()
        report.files_scanned = 1
        report.issues = [_auto_fix_issue("mutated.md")]

        def _mutating_apply_fixes(vault_root, r, **kw):
            (vault_root / "mutated.md").write_text("after mutation", encoding="utf-8")

        monkeypatch.setattr(hygiene_mod, "scan_vault", lambda vr, **kw: report)
        monkeypatch.setattr(hygiene_mod, "build_loose_node_review_queue", lambda r, vr: [])
        monkeypatch.setattr(hygiene_mod, "summarize_issues", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "summarize_node_categories", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "render_report", lambda r, vr: "# report\n")
        monkeypatch.setattr(hygiene_mod, "apply_fixes", _mutating_apply_fixes)
        monkeypatch.setattr(
            daily_hub_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, dates_found=0, notes_created=0,
                notes_updated=0, backlinks_added=0, index_updated=False,
            )
        )
        monkeypatch.setattr(
            provenance_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, files_modified=0, links_added={},
            )
        )

        result = run_os_hygiene_graph({}, tmp_path)
        s1 = result["stage_1_vault_hygiene"]

        assert s1["snapshot_modified_count"] == 1
        assert s1["snapshot_deleted_count"] == 0

        diff_records = s1["snapshot_diff_records"]
        assert len(diff_records) == 1
        assert diff_records[0]["change_type"] == "modified"
        assert diff_records[0]["old_sha256"] == original_hash
        assert diff_records[0]["path"] == "mutated.md"

    def test_unchanged_file_not_counted_as_modified(self, monkeypatch, tmp_path):
        import runtime.cli.vault_hygiene as hygiene_mod
        import runtime.cli.daily_hub_linker as daily_hub_mod
        import runtime.cli.provenance_linker as provenance_mod

        target = tmp_path / "steady.md"
        target.write_text("no change", encoding="utf-8")

        report = HygieneReport()
        report.files_scanned = 1
        report.issues = [_auto_fix_issue("steady.md")]

        monkeypatch.setattr(hygiene_mod, "scan_vault", lambda vr, **kw: report)
        monkeypatch.setattr(hygiene_mod, "build_loose_node_review_queue", lambda r, vr: [])
        monkeypatch.setattr(hygiene_mod, "summarize_issues", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "summarize_node_categories", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "render_report", lambda r, vr: "# report\n")
        monkeypatch.setattr(hygiene_mod, "apply_fixes", lambda vr, r, **kw: None)
        monkeypatch.setattr(
            daily_hub_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, dates_found=0, notes_created=0,
                notes_updated=0, backlinks_added=0, index_updated=False,
            )
        )
        monkeypatch.setattr(
            provenance_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, files_modified=0, links_added={},
            )
        )

        result = run_os_hygiene_graph({}, tmp_path)
        s1 = result["stage_1_vault_hygiene"]
        assert s1["snapshot_modified_count"] == 0

    def test_run_record_includes_snapshot_section_when_taken(self, monkeypatch, tmp_path):
        import runtime.cli.vault_hygiene as hygiene_mod
        import runtime.cli.daily_hub_linker as daily_hub_mod
        import runtime.cli.provenance_linker as provenance_mod

        target = tmp_path / "fix.md"
        target.write_text("fix me", encoding="utf-8")

        report = HygieneReport()
        report.files_scanned = 1
        report.issues = [_auto_fix_issue("fix.md")]

        monkeypatch.setattr(hygiene_mod, "scan_vault", lambda vr, **kw: report)
        monkeypatch.setattr(hygiene_mod, "build_loose_node_review_queue", lambda r, vr: [])
        monkeypatch.setattr(hygiene_mod, "summarize_issues", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "summarize_node_categories", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "render_report", lambda r, vr: "# report\n")
        monkeypatch.setattr(hygiene_mod, "apply_fixes", lambda vr, r, **kw: None)
        monkeypatch.setattr(
            daily_hub_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, dates_found=0, notes_created=0,
                notes_updated=0, backlinks_added=0, index_updated=False,
            )
        )
        monkeypatch.setattr(
            provenance_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, files_modified=0, links_added={},
            )
        )

        result = run_os_hygiene_graph({}, tmp_path)
        run_record_content = result["writebacks"][0]["content"]
        assert "Pre-Mutation Snapshot" in run_record_content
        assert "diff_log.json" in run_record_content

    def test_run_record_no_snapshot_section_when_dry_run(self, monkeypatch, tmp_path):
        self._setup_mocks(monkeypatch, tmp_path)
        result = run_os_hygiene_graph({"dry_run": True}, tmp_path)
        run_record_content = result["writebacks"][0]["content"]
        assert "Pre-Mutation Snapshot" not in run_record_content

    def test_snapshot_dir_field_in_run_record_frontmatter(self, monkeypatch, tmp_path):
        import runtime.cli.vault_hygiene as hygiene_mod
        import runtime.cli.daily_hub_linker as daily_hub_mod
        import runtime.cli.provenance_linker as provenance_mod

        target = tmp_path / "fix.md"
        target.write_text("fix me", encoding="utf-8")

        report = HygieneReport()
        report.files_scanned = 1
        report.issues = [_auto_fix_issue("fix.md")]

        monkeypatch.setattr(hygiene_mod, "scan_vault", lambda vr, **kw: report)
        monkeypatch.setattr(hygiene_mod, "build_loose_node_review_queue", lambda r, vr: [])
        monkeypatch.setattr(hygiene_mod, "summarize_issues", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "summarize_node_categories", lambda r: {})
        monkeypatch.setattr(hygiene_mod, "render_report", lambda r, vr: "# report\n")
        monkeypatch.setattr(hygiene_mod, "apply_fixes", lambda vr, r, **kw: None)
        monkeypatch.setattr(
            daily_hub_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, dates_found=0, notes_created=0,
                notes_updated=0, backlinks_added=0, index_updated=False,
            )
        )
        monkeypatch.setattr(
            provenance_mod, "run", lambda **kw: SimpleNamespace(
                files_scanned=0, files_modified=0, links_added={},
            )
        )

        result = run_os_hygiene_graph({}, tmp_path)
        run_record_content = result["writebacks"][0]["content"]
        assert "snapshot_dir:" in run_record_content
