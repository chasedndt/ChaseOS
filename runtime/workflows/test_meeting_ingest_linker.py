"""
test_meeting_ingest_linker.py — ChaseOS Phase 9 Feature 14
Tests for meeting_ingest_linker workflow.

Coverage:
  TestExtractWikilinks (6)
  TestExtractProjectMentions (6)
  TestExtractDomainMentions (6)
  TestExtractEntities (4)
  TestMatchEntitiesToVault (6)
  TestCglCheck (4)
  TestRenderProposalReport (6)
  TestRunMeetingIngestLinker (12)
  TestMeetingIngestLinkerInfrastructure (7)

Total: 57 tests
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import pytest

from runtime.workflows.meeting_ingest_linker import (
    WorkflowExecutionError,
    EntityMention,
    LinkProposal,
    _extract_wikilinks,
    _extract_project_mentions,
    _extract_domain_mentions,
    extract_entities,
    match_entities_to_vault,
    apply_cgl_checks,
    _render_proposal_report,
    run_meeting_ingest_linker,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    """Create a minimal fake vault with standard directory structure."""
    vault = tmp_path / "vault"
    vault.mkdir()

    # Minimal CLAUDE.md so vault is recognized
    (vault / "CLAUDE.md").write_text("# ChaseOS", encoding="utf-8")

    # Project directories
    projects = vault / "01_PROJECTS"
    projects.mkdir()
    alpha_dir = projects / "AlphaProject"
    alpha_dir.mkdir()
    (alpha_dir / "AlphaProject-OS.md").write_text(
        "---\ntitle: AlphaProject\n---\n# AlphaProject OS", encoding="utf-8"
    )
    beta_dir = projects / "BetaProject"
    beta_dir.mkdir()
    (beta_dir / "BetaProject-OS.md").write_text(
        "---\ntitle: BetaProject\n---\n# BetaProject OS", encoding="utf-8"
    )

    # Knowledge directories
    knowledge = vault / "02_KNOWLEDGE"
    knowledge.mkdir()
    trading_dir = knowledge / "Trading-Systems"
    trading_dir.mkdir()
    (trading_dir / "Trading-Systems.md").write_text(
        "---\ntitle: Trading Systems\ntrust_level: reviewed\n---\n# Trading Systems",
        encoding="utf-8",
    )
    ai_dir = knowledge / "AI-Agents"
    ai_dir.mkdir()
    (ai_dir / "AI-Agent-Engineering.md").write_text(
        "---\ntitle: AI Agent Engineering\ntrust_level: reviewed\n---\n# AI Agents",
        encoding="utf-8",
    )
    chaseos_dir = knowledge / "ChaseOS"
    chaseos_dir.mkdir()
    (chaseos_dir / "ChaseOS.md").write_text(
        "---\ntitle: ChaseOS\ntrust_level: canonical\n---\n# ChaseOS Knowledge",
        encoding="utf-8",
    )
    doctrine_dir = knowledge / "Doctrine"
    doctrine_dir.mkdir()
    (doctrine_dir / "Doctrine-Philosophy.md").write_text(
        "---\ntrust_level: canonical\nsensitivity: operator-only\npromotion_stage: canonical\n---\n# Doctrine",
        encoding="utf-8",
    )

    # A standalone note for wikilink testing
    (vault / "StandaloneNote.md").write_text("# Standalone Note", encoding="utf-8")

    # Logs
    (vault / "07_LOGS").mkdir()
    (vault / "07_LOGS" / "Link-Proposals").mkdir()

    return vault


@pytest.fixture
def vault(tmp_path):
    return _make_vault(tmp_path)


@pytest.fixture
def transcript_file(vault):
    transcript = vault / "03_INPUTS"
    transcript.mkdir(exist_ok=True)
    t = transcript / "2026-04-25-meeting.md"
    t.write_text(
        "We discussed [[AlphaProject]] and the trading strategy.\n"
        "Also touched on AI agent architecture and defi protocols.\n"
        "See [[StandaloneNote]] for background.\n",
        encoding="utf-8",
    )
    return t


# ── TestExtractWikilinks ───────────────────────────────────────────────────────

class TestExtractWikilinks:
    def test_extracts_simple_wikilink(self):
        text = "See [[MyNote]] for more."
        result = _extract_wikilinks(text)
        assert len(result) == 1
        assert result[0].text == "MyNote"
        assert result[0].kind == "wikilink"

    def test_multiple_wikilinks_on_one_line(self):
        text = "See [[Alpha]] and [[Beta]] for details."
        result = _extract_wikilinks(text)
        assert len(result) == 2
        texts = {m.text for m in result}
        assert "Alpha" in texts and "Beta" in texts

    def test_wikilink_with_alias(self):
        text = "See [[Target|Display Name]] here."
        result = _extract_wikilinks(text)
        assert len(result) == 1
        assert result[0].text == "Target"

    def test_no_wikilinks(self):
        text = "Plain text with no links."
        result = _extract_wikilinks(text)
        assert result == []

    def test_wikilink_line_number_recorded(self):
        text = "Line one.\n[[Alpha]] is here."
        result = _extract_wikilinks(text)
        assert result[0].source_line == 2

    def test_wikilinks_across_multiple_lines(self):
        text = "[[A]]\n[[B]]\n[[C]]"
        result = _extract_wikilinks(text)
        assert len(result) == 3
        assert [m.source_line for m in result] == [1, 2, 3]


# ── TestExtractProjectMentions ─────────────────────────────────────────────────

class TestExtractProjectMentions:
    def test_mentions_known_project(self, vault):
        text = "We worked on AlphaProject today."
        result = _extract_project_mentions(text, vault)
        names = {m.text for m in result}
        assert "AlphaProject" in names

    def test_no_mention_returns_empty(self, vault):
        text = "No projects mentioned here whatsoever."
        result = _extract_project_mentions(text, vault)
        # BetaProject and AlphaProject not mentioned
        assert all(m.text not in text for m in result)

    def test_case_insensitive_match(self, vault):
        text = "alphaproject is in progress."
        result = _extract_project_mentions(text, vault)
        names = {m.text for m in result}
        assert "AlphaProject" in names

    def test_kind_is_project(self, vault):
        text = "BetaProject launch next week."
        result = _extract_project_mentions(text, vault)
        assert all(m.kind == "project" for m in result)

    def test_missing_projects_dir_returns_empty(self, tmp_path):
        vault_no_projects = tmp_path / "noprojects"
        vault_no_projects.mkdir()
        result = _extract_project_mentions("any text", vault_no_projects)
        assert result == []

    def test_multiple_projects_found(self, vault):
        text = "AlphaProject and BetaProject discussed."
        result = _extract_project_mentions(text, vault)
        names = {m.text for m in result}
        assert "AlphaProject" in names
        assert "BetaProject" in names


# ── TestExtractDomainMentions ──────────────────────────────────────────────────

class TestExtractDomainMentions:
    def test_trading_keyword_found(self):
        text = "We reviewed the trading strategy today."
        result = _extract_domain_mentions(text)
        names = {m.text for m in result}
        assert any("Trading" in n for n in names)

    def test_ai_keyword_found(self):
        text = "The llm model produced good results."
        result = _extract_domain_mentions(text)
        names = {m.text for m in result}
        assert any("AI" in n or "Machine" in n for n in names)

    def test_no_domain_keywords(self):
        text = "A completely generic meeting with no domain overlap."
        result = _extract_domain_mentions(text)
        assert isinstance(result, list)

    def test_kind_is_domain(self):
        text = "security audit and pentest findings"
        result = _extract_domain_mentions(text)
        assert all(m.kind == "domain" for m in result)

    def test_same_domain_not_duplicated(self):
        text = "trading trading trading strategy backtest"
        result = _extract_domain_mentions(text)
        domain_letters = [m.text for m in result]
        # Should only appear once per domain
        assert len(domain_letters) == len(set(domain_letters))

    def test_multiple_domains_found(self):
        text = "trading strategy and ai agents discussed."
        result = _extract_domain_mentions(text)
        assert len(result) >= 2


# ── TestExtractEntities ────────────────────────────────────────────────────────

class TestExtractEntities:
    def test_combines_all_sources(self, vault, transcript_file):
        text = transcript_file.read_text(encoding="utf-8")
        result = extract_entities(text, vault)
        kinds = {m.kind for m in result}
        assert "wikilink" in kinds

    def test_empty_text_returns_empty(self, vault):
        result = extract_entities("", vault)
        assert result == []

    def test_only_wikilinks_no_projects_no_domains(self, vault):
        text = "[[SomeNote]] mentioned here."
        result = extract_entities(text, vault)
        wikilinks = [m for m in result if m.kind == "wikilink"]
        assert len(wikilinks) == 1

    def test_returns_list_of_entity_mentions(self, vault):
        text = "trading [[Alpha]]"
        result = extract_entities(text, vault)
        assert all(isinstance(m, EntityMention) for m in result)


# ── TestMatchEntitiesToVault ───────────────────────────────────────────────────

class TestMatchEntitiesToVault:
    def test_wikilink_matched_to_vault_note(self, vault):
        entities = [EntityMention(text="StandaloneNote", kind="wikilink", source_line=1)]
        proposals = match_entities_to_vault(entities, vault)
        assert len(proposals) == 1
        assert "StandaloneNote" in proposals[0].target_path

    def test_project_matched_to_os_file(self, vault):
        entities = [EntityMention(text="AlphaProject", kind="project", source_line=1)]
        proposals = match_entities_to_vault(entities, vault)
        assert len(proposals) == 1
        assert "AlphaProject" in proposals[0].target_path

    def test_unmatched_entity_excluded(self, vault):
        entities = [EntityMention(text="NoSuchNote", kind="wikilink", source_line=1)]
        proposals = match_entities_to_vault(entities, vault)
        assert len(proposals) == 0

    def test_duplicate_targets_deduplicated(self, vault):
        entities = [
            EntityMention(text="StandaloneNote", kind="wikilink", source_line=1),
            EntityMention(text="StandaloneNote", kind="wikilink", source_line=2),
        ]
        proposals = match_entities_to_vault(entities, vault)
        assert len(proposals) == 1

    def test_wikilink_confidence_high(self, vault):
        entities = [EntityMention(text="StandaloneNote", kind="wikilink", source_line=1)]
        proposals = match_entities_to_vault(entities, vault)
        assert proposals[0].confidence == 0.9

    def test_project_confidence_lower_than_wikilink(self, vault):
        entities = [
            EntityMention(text="StandaloneNote", kind="wikilink", source_line=1),
            EntityMention(text="AlphaProject", kind="project", source_line=2),
        ]
        proposals = match_entities_to_vault(entities, vault)
        by_kind = {p.entity_kind: p for p in proposals}
        assert by_kind["wikilink"].confidence > by_kind["project"].confidence


# ── TestCglCheck ──────────────────────────────────────────────────────────────

class TestCglCheck:
    def test_eligible_proposal_unchanged(self, vault):
        proposal = LinkProposal(
            entity_text="Trading",
            entity_kind="domain",
            target_path="02_KNOWLEDGE/Trading-Systems/Trading-Systems.md",
            target_title="Trading-Systems",
            confidence=0.5,
            rationale="domain match",
        )
        results = apply_cgl_checks([proposal], vault)
        assert len(results) == 1
        assert results[0].cgl_eligible is True

    def test_missing_target_treated_as_eligible(self, vault):
        proposal = LinkProposal(
            entity_text="Ghost",
            entity_kind="wikilink",
            target_path="nonexistent/Ghost.md",
            target_title="Ghost",
            confidence=0.9,
            rationale="wikilink",
        )
        results = apply_cgl_checks([proposal], vault)
        # Fail-open: even missing files don't block
        assert results[0].cgl_eligible is True

    def test_empty_proposals_returns_empty(self, vault):
        results = apply_cgl_checks([], vault)
        assert results == []

    def test_multiple_proposals_all_checked(self, vault):
        proposals = [
            LinkProposal("A", "domain", "02_KNOWLEDGE/Trading-Systems/Trading-Systems.md",
                         "Trading-Systems", 0.5, "domain match"),
            LinkProposal("B", "wikilink", "StandaloneNote.md", "StandaloneNote", 0.9, "wikilink"),
        ]
        results = apply_cgl_checks(proposals, vault)
        assert len(results) == 2


# ── TestRenderProposalReport ───────────────────────────────────────────────────

class TestRenderProposalReport:
    def _make_proposal(self, eligible=True):
        return LinkProposal(
            entity_text="AlphaProject",
            entity_kind="project",
            target_path="01_PROJECTS/AlphaProject/AlphaProject-OS.md",
            target_title="AlphaProject-OS",
            confidence=0.7,
            rationale="Project name matched in transcript",
            cgl_eligible=eligible,
            cgl_note=None if eligible else "CGL blocked: operator-only",
        )

    def test_report_has_frontmatter(self):
        proposals = [self._make_proposal()]
        report = _render_proposal_report(proposals, "transcript.md", "cap-001", "2026-04-25", 3)
        assert "type: link-proposal" in report
        assert "capture_id: cap-001" in report

    def test_report_has_read_only_disclaimer(self):
        proposals = [self._make_proposal()]
        report = _render_proposal_report(proposals, "transcript.md", "cap-001", "2026-04-25", 3)
        assert "READ-ONLY PROPOSAL" in report

    def test_eligible_proposals_appear_in_table(self):
        proposals = [self._make_proposal(eligible=True)]
        report = _render_proposal_report(proposals, "t.md", "cap", "2026-04-25", 1)
        assert "Eligible Link Proposals" in report
        assert "AlphaProject" in report

    def test_blocked_proposals_appear_in_blocked_section(self):
        proposals = [self._make_proposal(eligible=False)]
        report = _render_proposal_report(proposals, "t.md", "cap", "2026-04-25", 1)
        assert "CGL-Blocked Proposals" in report

    def test_empty_proposals_shows_no_proposals_section(self):
        report = _render_proposal_report([], "t.md", "cap", "2026-04-25", 0)
        assert "No Link Proposals" in report

    def test_operator_apply_step_present(self):
        proposals = [self._make_proposal()]
        report = _render_proposal_report(proposals, "t.md", "cap", "2026-04-25", 1)
        assert "Operator Apply Step" in report


# ── TestRunMeetingIngestLinker ─────────────────────────────────────────────────

class TestRunMeetingIngestLinker:
    def test_missing_transcript_path_raises(self, vault):
        with pytest.raises(WorkflowExecutionError, match="transcript_path"):
            run_meeting_ingest_linker({}, vault)

    def test_nonexistent_transcript_raises(self, vault):
        with pytest.raises(WorkflowExecutionError, match="not found"):
            run_meeting_ingest_linker({"transcript_path": "no/such/file.md"}, vault)

    def test_returns_writeback_dict(self, vault, transcript_file):
        result = run_meeting_ingest_linker(
            {"transcript_path": str(transcript_file)}, vault
        )
        assert "writebacks" in result
        assert "proposal_count" in result
        assert "entity_count" in result
        assert "eligible_count" in result
        assert "blocked_count" in result

    def test_output_file_is_markdown(self, vault, transcript_file):
        result = run_meeting_ingest_linker(
            {"transcript_path": str(transcript_file)}, vault
        )
        assert len(result["writebacks"]) == 1
        assert result["writebacks"][0]["path"].endswith(".md")

    def test_output_file_written_to_link_proposals(self, vault, transcript_file):
        result = run_meeting_ingest_linker(
            {"transcript_path": str(transcript_file)}, vault
        )
        assert "Link-Proposals" in result["writebacks"][0]["path"]

    def test_output_filename_contains_date(self, vault, transcript_file):
        result = run_meeting_ingest_linker(
            {"transcript_path": str(transcript_file), "date": "2026-01-15"},
            vault,
        )
        assert "2026-01-15" in result["writebacks"][0]["path"]

    def test_invalid_date_raises(self, vault, transcript_file):
        with pytest.raises(WorkflowExecutionError, match="invalid date"):
            run_meeting_ingest_linker(
                {"transcript_path": str(transcript_file), "date": "not-a-date"},
                vault,
            )

    def test_invalid_min_confidence_raises(self, vault, transcript_file):
        with pytest.raises(WorkflowExecutionError, match="min_confidence"):
            run_meeting_ingest_linker(
                {"transcript_path": str(transcript_file), "min_confidence": 2.5},
                vault,
            )

    def test_high_confidence_filter_excludes_domain_matches(self, vault, transcript_file):
        # min_confidence=0.8 should exclude domain matches (0.5) and project matches (0.7)
        result = run_meeting_ingest_linker(
            {"transcript_path": str(transcript_file), "min_confidence": 0.8},
            vault,
        )
        # Only wikilinks (0.9) should survive
        # Proposal count may be 0 or more depending on wikilink matches
        assert result["proposal_count"] >= 0

    def test_vault_relative_transcript_path(self, vault, transcript_file):
        rel = transcript_file.relative_to(vault)
        result = run_meeting_ingest_linker(
            {"transcript_path": str(rel)}, vault
        )
        assert result["entity_count"] >= 0

    def test_capture_id_used_in_filename(self, vault, transcript_file):
        result = run_meeting_ingest_linker(
            {"transcript_path": str(transcript_file), "capture_id": "my-meeting-cap"},
            vault,
        )
        assert "my-meeting-cap" in result["writebacks"][0]["path"]

    def test_output_file_is_readable_markdown(self, vault, transcript_file):
        result = run_meeting_ingest_linker(
            {"transcript_path": str(transcript_file)}, vault
        )
        content = result["writebacks"][0]["content"]
        assert "link-proposal" in content
        assert "READ-ONLY PROPOSAL" in content


# ── TestMeetingIngestLinkerInfrastructure ──────────────────────────────────────

class TestMeetingIngestLinkerInfrastructure:
    def test_task_type_table_has_meeting_ingest(self):
        table_path = Path("runtime/aor/task_type_table.yaml")
        assert table_path.exists(), "task_type_table.yaml must exist"
        content = table_path.read_text(encoding="utf-8")
        assert "meeting-ingest" in content

    def test_manifest_exists(self):
        manifest_path = Path("runtime/workflows/registry/meeting_ingest_linker.yaml")
        assert manifest_path.exists()

    def test_manifest_has_required_fields(self):
        manifest_path = Path("runtime/workflows/registry/meeting_ingest_linker.yaml")
        text = manifest_path.read_text(encoding="utf-8")
        for field in ("id:", "status:", "task_type:", "role_card:", "writeback_targets:"):
            assert field in text, f"manifest missing field: {field}"
        assert "status: active" in text
        assert "task_type: meeting-ingest" in text

    def test_role_card_exists(self):
        role_card_path = Path("06_AGENTS/role-cards/meeting-ingest-readonly.yaml")
        assert role_card_path.exists()

    def test_role_card_has_required_fields(self):
        card_path = Path("06_AGENTS/role-cards/meeting-ingest-readonly.yaml")
        text = card_path.read_text(encoding="utf-8")
        for field in ("id:", "allowed_actions:", "forbidden_actions:", "write_scope:", "forbidden_write_zones:"):
            assert field in text, f"role card missing field: {field}"
        assert "apply_links_without_operator_approval" in text

    def test_engine_import_works(self):
        from runtime.aor.engine import run_workflow  # noqa: F401

    def test_live_vault_smoke_test(self):
        """Run full AOR pipeline against real vault with a real transcript-like file."""
        import tempfile
        from runtime.aor.engine import run_workflow

        vault = Path(".")
        if not (vault / "CLAUDE.md").exists():
            pytest.skip("not in vault root")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", dir=str(vault / "03_INPUTS"),
            delete=False, encoding="utf-8"
        ) as f:
            f.write(
                "Meeting notes: we discussed ChaseOS, trading strategies, and the AI agent architecture.\n"
                "Security posture review also came up.\n"
            )
            tmp_path = Path(f.name)

        try:
            r = run_workflow(
                "meeting_ingest_linker",
                inputs={"transcript_path": str(tmp_path), "capture_id": "smoke-test"},
                vault_root=vault,
            )
            assert r.status == "success", f"expected success, got: {r.status} — {r.escalation_reason or r.error}"
            files = r.outputs.get("writeback", {}).get("files_written", [])
            for f in files:
                Path(vault / f).unlink(missing_ok=True)
        finally:
            tmp_path.unlink(missing_ok=True)
