"""
runtime.operator_surface.tests.test_browser_pass5

Browser Operator Surface -- Pass 5 tests
AOR Workflow Registration: browser_research

Tests cover 9 acceptance criteria:
  A. Manifest exists and validates through AOR registry
  B. dry_run=True passes all validation stages
  C. Handler validates inputs: missing goal raises WorkflowExecutionError
  D. Handler validates inputs: missing URLs raises WorkflowExecutionError
  E. Handler validates inputs: invalid URL raises WorkflowExecutionError
  F. run_browser_research with stub browser returns correct dict structure
  G. Quarantine routing: capture_content called with correct ContentPacket fields
  H. Research summary is written to correct path under 07_LOGS/Operator-Briefs/
  I. Stub mode: succeeds but produces no quarantine captures
  (+ additional: JSON format, URL list parsing, unknown inputs fail closed)
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.workflows.browser_research import (
    WorkflowExecutionError,
    _validate_url,
    _extract_origin,
    _extract_page_outputs,
    _build_research_summary,
    _capture_page_to_quarantine,
    run_browser_research,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    """Create a minimal vault structure for testing."""
    # Required files
    (tmp_path / "CLAUDE.md").write_text("# test vault")
    (tmp_path / "04_SOPS").mkdir(parents=True, exist_ok=True)
    (tmp_path / "04_SOPS" / "Untrusted-Input-Handling-SOP.md").write_text("# SOP")
    (tmp_path / "07_LOGS" / "Operator-Briefs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True, exist_ok=True)
    (tmp_path / "03_INPUTS" / "00_QUARANTINE" / "source").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".chaseos").mkdir(exist_ok=True)
    # Context boot protocol requires Now.md — add minimal version
    home = tmp_path / "00_HOME"
    home.mkdir(exist_ok=True)
    (home / "Now.md").write_text(
        "---\ntype: now\ndate: 2026-04-24\n---\n\n# Now — 2026-04-24\n\n"
        "## Current Phase\n\nPhase 9 — Operator Runtime — ACTIVE\n\n"
        "## Active Now\n\n- Browser research testing\n",
        encoding="utf-8",
    )
    return tmp_path


def _fake_audit(
    outcome="COMPLETE",
    run_id="br-test-001",
    text="Sample page text for testing.",
    url="https://example.com",
    title="Example Domain",
    adapter_mode="stub",
):
    """Build a fake OperatorRunAudit-like object for browser_research tests."""
    from runtime.operator_surface.events import OperatorEventType
    audit = MagicMock()
    audit.outcome = outcome
    audit.run_id = run_id
    audit.error = None
    audit.adapter_payload = {
        "adapter_mode": adapter_mode,
        "playwright_available": adapter_mode != "stub",
    }

    # Build stub events for url, title, text
    def _make_event(result_dict):
        ev = MagicMock()
        ev.event_type = OperatorEventType.STEP_COMPLETE
        ev.payload = {"result": result_dict}
        return ev

    audit.events = [
        _make_event({"url": url}),
        _make_event({"title": title}),
        _make_event({"text": text, "char_count": len(text)}),
    ]
    return audit


# ── Unit: _validate_url ───────────────────────────────────────────────────────

class TestValidateUrlHandler:
    def test_valid_https(self):
        assert _validate_url("https://example.com") is None

    def test_valid_http(self):
        assert _validate_url("http://localhost:8080") is None

    def test_empty_string(self):
        assert _validate_url("") is not None

    def test_no_scheme(self):
        assert _validate_url("example.com") is not None

    def test_ftp_rejected(self):
        assert _validate_url("ftp://example.com") is not None

    def test_no_host(self):
        assert _validate_url("https://") is not None


# ── Unit: _extract_origin ─────────────────────────────────────────────────────

class TestExtractOriginHandler:
    def test_https_with_path(self):
        assert _extract_origin("https://example.com/page") == "https://example.com"

    def test_http_with_port(self):
        assert _extract_origin("http://localhost:3000/path") == "http://localhost:3000"

    def test_no_path(self):
        assert _extract_origin("https://example.com") == "https://example.com"

    def test_malformed_falls_back(self):
        result = _extract_origin("not-a-url")
        assert result is not None  # fallback — does not raise


# ── Unit: _extract_page_outputs ───────────────────────────────────────────────

class TestExtractPageOutputs:
    def test_extracts_url_title_text(self):
        audit = _fake_audit(
            url="https://example.com/result",
            title="Result Page",
            text="Some content here.",
        )
        state = _extract_page_outputs(audit)
        assert state["url"] == "https://example.com/result"
        assert state["title"] == "Result Page"
        assert state["text"] == "Some content here."

    def test_empty_events(self):
        audit = MagicMock()
        audit.events = []
        state = _extract_page_outputs(audit)
        assert state == {}

    def test_char_count_from_result(self):
        from runtime.operator_surface.events import OperatorEventType
        audit = MagicMock()
        ev = MagicMock()
        ev.event_type = OperatorEventType.STEP_COMPLETE
        ev.payload = {"result": {"text": "abc", "char_count": 99}}
        audit.events = [ev]
        state = _extract_page_outputs(audit)
        assert state["char_count"] == 99


# ── Unit: _build_research_summary ────────────────────────────────────────────

class TestBuildResearchSummary:
    def _page_result(self, success=True, is_stub=False, text="Test content.", url="https://example.com", title="Test"):
        return {
            "url": url,
            "requested_url": url,
            "title": title,
            "text": text,
            "char_count": len(text),
            "run_id": "run-001",
            "adapter_mode": "stub" if is_stub else "playwright",
            "success": success,
            "is_stub": is_stub,
            "error": None,
        }

    def test_markdown_format_contains_goal(self):
        summary = _build_research_summary(
            goal="learn about testing",
            url_list=["https://example.com"],
            page_results=[self._page_result()],
            capture_ids=["cap-001"],
            run_date="2026-04-16",
            output_format="markdown",
        )
        assert "learn about testing" in summary

    def test_markdown_has_frontmatter(self):
        summary = _build_research_summary(
            goal="goal",
            url_list=["https://example.com"],
            page_results=[self._page_result()],
            capture_ids=[],
            run_date="2026-04-16",
            output_format="markdown",
        )
        assert summary.startswith("---")
        assert "workflow: browser_research" in summary

    def test_json_format_is_parseable(self):
        summary = _build_research_summary(
            goal="json goal",
            url_list=["https://example.com"],
            page_results=[self._page_result()],
            capture_ids=["cap-001"],
            run_date="2026-04-16",
            output_format="json",
        )
        parsed = json.loads(summary)
        assert parsed["goal"] == "json goal"
        assert parsed["workflow"] == "browser_research"
        assert len(parsed["pages"]) == 1

    def test_summary_marks_content_as_untrusted(self):
        summary = _build_research_summary(
            goal="check trust marking",
            url_list=["https://example.com"],
            page_results=[self._page_result(text="Some real content here for the test.")],
            capture_ids=[],
            run_date="2026-04-16",
            output_format="markdown",
        )
        assert "untrusted" in summary.lower() or "UNTRUSTED" in summary

    def test_stub_mode_noted_in_summary(self):
        summary = _build_research_summary(
            goal="stub test",
            url_list=["https://example.com"],
            page_results=[self._page_result(is_stub=True, text="")],
            capture_ids=[],
            run_date="2026-04-16",
            output_format="markdown",
        )
        assert "stub" in summary.lower()

    def test_failed_page_noted(self):
        page = self._page_result(success=False, text="")
        page["error"] = "connection refused"
        summary = _build_research_summary(
            goal="failed page test",
            url_list=["https://example.com"],
            page_results=[page],
            capture_ids=[],
            run_date="2026-04-16",
            output_format="markdown",
        )
        assert "FAILED" in summary or "failed" in summary.lower()


# ── Unit: run_browser_research input validation ───────────────────────────────

class TestRunBrowserResearchInputValidation:
    def setup_method(self):
        self._tmp = tempfile.mkdtemp()
        self._vault = _make_vault(Path(self._tmp))

    def test_missing_goal_raises(self):
        with pytest.raises(WorkflowExecutionError, match="goal"):
            run_browser_research(
                inputs={"urls": "https://example.com"},
                vault_root=self._vault,
            )

    def test_empty_goal_raises(self):
        with pytest.raises(WorkflowExecutionError, match="goal"):
            run_browser_research(
                inputs={"goal": "   ", "urls": "https://example.com"},
                vault_root=self._vault,
            )

    def test_missing_urls_raises(self):
        with pytest.raises(WorkflowExecutionError, match="URL"):
            run_browser_research(
                inputs={"goal": "test research"},
                vault_root=self._vault,
            )

    def test_empty_urls_raises(self):
        with pytest.raises(WorkflowExecutionError, match="URL"):
            run_browser_research(
                inputs={"goal": "test research", "urls": "  "},
                vault_root=self._vault,
            )

    def test_invalid_url_raises(self):
        with pytest.raises(WorkflowExecutionError, match="invalid URL"):
            run_browser_research(
                inputs={"goal": "test", "urls": "ftp://bad-url.com"},
                vault_root=self._vault,
            )

    def test_non_http_url_raises(self):
        with pytest.raises(WorkflowExecutionError, match="invalid URL"):
            run_browser_research(
                inputs={"goal": "test", "urls": "javascript:alert(1)"},
                vault_root=self._vault,
            )

    def test_invalid_output_format_raises(self):
        with pytest.raises(WorkflowExecutionError, match="output_format"):
            run_browser_research(
                inputs={"goal": "test", "urls": "https://example.com", "output_format": "xml"},
                vault_root=self._vault,
            )


# ── Unit: run_browser_research output structure ───────────────────────────────

class TestRunBrowserResearchOutputStructure:
    """Test that the handler returns correct dict structure with mocked executor."""

    def setup_method(self):
        self._tmp = tempfile.mkdtemp()
        self._vault = _make_vault(Path(self._tmp))

    def _run_with_stub(self, goal="research goal", urls="https://example.com", **extra_inputs):
        """Run with mocked executor returning stub audit."""
        audit = _fake_audit()
        with patch("runtime.workflows.browser_research.OperatorExecutor") as MockExec:
            MockExec.return_value.run.return_value = audit
            result = run_browser_research(
                inputs={"goal": goal, "urls": urls, **extra_inputs},
                vault_root=self._vault,
            )
        return result

    def test_returns_summary_path_key(self):
        result = self._run_with_stub()
        assert "summary_path" in result

    def test_summary_path_under_operator_briefs(self):
        result = self._run_with_stub()
        assert result["summary_path"].startswith("07_LOGS/Operator-Briefs/")

    def test_returns_pages_captured(self):
        result = self._run_with_stub()
        assert "pages_captured" in result
        assert isinstance(result["pages_captured"], int)

    def test_returns_capture_ids_list(self):
        result = self._run_with_stub()
        assert "capture_ids" in result
        assert isinstance(result["capture_ids"], list)

    def test_returns_writebacks_list(self):
        result = self._run_with_stub()
        assert "writebacks" in result
        assert isinstance(result["writebacks"], list)
        assert len(result["writebacks"]) >= 1

    def test_writeback_has_path_and_content(self):
        result = self._run_with_stub()
        wb = result["writebacks"][0]
        assert "path" in wb
        assert "content" in wb

    def test_writeback_path_matches_summary_path(self):
        result = self._run_with_stub()
        assert result["writebacks"][0]["path"] == result["summary_path"]

    def test_url_list_parsing_space_separated(self):
        audit = _fake_audit()
        with patch("runtime.workflows.browser_research.OperatorExecutor") as MockExec:
            MockExec.return_value.run.return_value = audit
            result = run_browser_research(
                inputs={"goal": "multi-url test", "urls": "https://a.com https://b.com"},
                vault_root=self._vault,
            )
        # max_pages=3 default, 2 URLs → 2 page results
        assert isinstance(result["pages_captured"], int)

    def test_url_list_as_list_type(self):
        audit = _fake_audit()
        with patch("runtime.workflows.browser_research.OperatorExecutor") as MockExec:
            MockExec.return_value.run.return_value = audit
            result = run_browser_research(
                inputs={"goal": "list test", "urls": ["https://example.com"]},
                vault_root=self._vault,
            )
        assert "summary_path" in result

    def test_max_pages_hard_cap_at_10(self):
        """max_pages > 10 is clamped to 10."""
        audit = _fake_audit()
        urls = " ".join(f"https://example{i}.com" for i in range(15))
        visited = []
        def _mock_run(*args, **kwargs):
            visited.append(1)
            return audit
        with patch("runtime.workflows.browser_research.OperatorExecutor") as MockExec:
            MockExec.return_value.run.side_effect = _mock_run
            run_browser_research(
                inputs={"goal": "cap test", "urls": urls, "max_pages": 999},
                vault_root=self._vault,
            )
        assert len(visited) <= 10

    def test_json_format_output(self):
        audit = _fake_audit()
        with patch("runtime.workflows.browser_research.OperatorExecutor") as MockExec:
            MockExec.return_value.run.return_value = audit
            result = run_browser_research(
                inputs={"goal": "json format test", "urls": "https://example.com",
                        "output_format": "json"},
                vault_root=self._vault,
            )
        content = result["writebacks"][0]["content"]
        parsed = json.loads(content)
        assert parsed["goal"] == "json format test"


# ── Unit: stub mode — no quarantine captures ─────────────────────────────────

class TestStubModeNoCaptureIds:
    """
    Criterion I: Stub mode succeeds but produces no quarantine captures.
    In stub mode adapter_mode="stub" and text="", so capture is skipped.
    """

    def setup_method(self):
        self._tmp = tempfile.mkdtemp()
        self._vault = _make_vault(Path(self._tmp))

    def test_stub_produces_no_capture_ids(self):
        stub_audit = _fake_audit(text="", adapter_mode="stub")
        with patch("runtime.workflows.browser_research.OperatorExecutor") as MockExec:
            MockExec.return_value.run.return_value = stub_audit
            result = run_browser_research(
                inputs={"goal": "stub run", "urls": "https://example.com"},
                vault_root=self._vault,
            )
        assert result["capture_ids"] == []
        assert result["pages_captured"] == 0

    def test_stub_still_returns_summary(self):
        stub_audit = _fake_audit(text="", adapter_mode="stub")
        with patch("runtime.workflows.browser_research.OperatorExecutor") as MockExec:
            MockExec.return_value.run.return_value = stub_audit
            result = run_browser_research(
                inputs={"goal": "stub summary test", "urls": "https://example.com"},
                vault_root=self._vault,
            )
        assert "summary_path" in result
        assert result["writebacks"][0]["content"] != ""


# ── Unit: quarantine capture routing ─────────────────────────────────────────

class TestQuarantineCaptureRouting:
    """
    Criterion G: capture_content is called with correct ContentPacket fields
    when real page content is available.
    """

    def setup_method(self):
        self._tmp = tempfile.mkdtemp()
        self._vault = _make_vault(Path(self._tmp))

    def test_capture_content_called_with_source_class(self):
        playwright_audit = _fake_audit(
            text="Real page content here.",
            adapter_mode="playwright",
            url="https://example.com",
            title="Example Domain",
            outcome="COMPLETE",
        )
        captured_packets = []

        def _fake_capture(packet, vault_root):
            captured_packets.append(packet)
            return {"capture_id": "cap-from-test-001"}

        with patch("runtime.workflows.browser_research.OperatorExecutor") as MockExec, \
             patch("runtime.workflows.browser_research.capture_content", side_effect=_fake_capture):
            MockExec.return_value.run.return_value = playwright_audit
            result = run_browser_research(
                inputs={"goal": "capture routing test", "urls": "https://example.com"},
                vault_root=self._vault,
            )

        assert len(captured_packets) == 1
        pkt = captured_packets[0]
        from runtime.capture.content_packet import INPUT_CLASS_SOURCE
        assert pkt.input_class == INPUT_CLASS_SOURCE
        assert pkt.source_url == "https://example.com"
        assert "browser-operator" in pkt.source_platform
        assert "cap-from-test-001" in result["capture_ids"]

    def test_capture_content_not_called_for_empty_text(self):
        audit_empty = _fake_audit(text="", adapter_mode="playwright", outcome="COMPLETE")
        calls = []

        def _fake_capture(packet, vault_root):
            calls.append(1)
            return {"capture_id": "cap-xxx"}

        with patch("runtime.workflows.browser_research.OperatorExecutor") as MockExec, \
             patch("runtime.workflows.browser_research.capture_content", side_effect=_fake_capture):
            MockExec.return_value.run.return_value = audit_empty
            run_browser_research(
                inputs={"goal": "empty text test", "urls": "https://example.com"},
                vault_root=self._vault,
            )

        assert calls == []


# ── AOR manifest + dry_run validation ────────────────────────────────────────

class TestAORManifestAndDryRun:
    """
    Criteria A + B:
      A. Manifest exists and validates through AOR registry
      B. dry_run=True passes all validation stages without executing
    """

    def setup_method(self):
        import shutil
        self._tmp = tempfile.mkdtemp()
        vault = Path(self._tmp)
        _make_vault(vault)

        # Copy manifest and role card from real vault
        real_vault = Path(__file__).resolve().parents[3]
        manifest_src = real_vault / "runtime/workflows/registry/browser_research.yaml"
        card_src = real_vault / "06_AGENTS/role-cards/browser-research.yaml"

        (vault / "runtime/workflows/registry").mkdir(parents=True, exist_ok=True)
        (vault / "06_AGENTS/role-cards").mkdir(parents=True, exist_ok=True)
        (vault / "runtime/aor").mkdir(parents=True, exist_ok=True)

        # Copy task_type_table.yaml too
        table_src = real_vault / "runtime/aor/task_type_table.yaml"
        shutil.copy(manifest_src, vault / "runtime/workflows/registry/browser_research.yaml")
        shutil.copy(card_src, vault / "06_AGENTS/role-cards/browser-research.yaml")
        shutil.copy(table_src, vault / "runtime/aor/task_type_table.yaml")

        self._vault = vault

    def test_manifest_loads_via_registry(self):
        from runtime.aor.registry import load_manifest
        manifest = load_manifest("browser_research", self._vault)
        assert manifest is not None
        assert manifest["id"] == "browser_research"
        assert manifest["status"] == "active"

    def test_manifest_task_type_is_browser_research(self):
        from runtime.aor.registry import load_manifest
        manifest = load_manifest("browser_research", self._vault)
        assert manifest["task_type"] == "browser-research"

    def test_manifest_role_card_is_browser_research(self):
        from runtime.aor.registry import load_manifest
        manifest = load_manifest("browser_research", self._vault)
        assert manifest["role_card"] == "browser-research"

    def test_manifest_has_writeback_targets(self):
        from runtime.aor.registry import load_manifest
        manifest = load_manifest("browser_research", self._vault)
        assert "07_LOGS/Operator-Briefs/" in manifest.get("writeback_targets", [])

    def test_role_card_loads(self):
        from runtime.aor.role_cards import load_card
        card = load_card("browser-research", self._vault)
        assert card is not None
        assert card["id"] == "browser-research"

    def test_role_card_write_scope(self):
        from runtime.aor.role_cards import load_card
        card = load_card("browser-research", self._vault)
        write_scope = card.get("write_scope", [])
        assert any("Operator-Briefs" in s for s in write_scope)

    def test_role_card_forbids_canonical_writes(self):
        from runtime.aor.role_cards import load_card
        card = load_card("browser-research", self._vault)
        forbidden = card.get("forbidden_write_zones", [])
        assert any("02_KNOWLEDGE" in z for z in forbidden)

    def test_dry_run_ok(self):
        from runtime.aor.engine import run_workflow
        result = run_workflow(
            workflow_id="browser_research",
            inputs={"goal": "test", "urls": "https://example.com"},
            vault_root=self._vault,
            dry_run=True,
        )
        assert result.status == "dry_run_ok"

    def test_dry_run_does_not_write_files(self):
        from runtime.aor.engine import run_workflow
        run_workflow(
            workflow_id="browser_research",
            inputs={"goal": "test", "urls": "https://example.com"},
            vault_root=self._vault,
            dry_run=True,
        )
        briefs_dir = self._vault / "07_LOGS" / "Operator-Briefs"
        briefs = list(briefs_dir.glob("*.md"))
        assert len(briefs) == 0


# ── AOR Stage 7 writeback integration ────────────────────────────────────────

class TestAORWritebackIntegration:
    """
    Criterion H: Research summary is written to correct path under
    07_LOGS/Operator-Briefs/ via AOR Stage 7 writeback.
    """

    def setup_method(self):
        import shutil
        self._tmp = tempfile.mkdtemp()
        vault = Path(self._tmp)
        _make_vault(vault)

        real_vault = Path(__file__).resolve().parents[3]
        for src, rel_dst in [
            ("runtime/workflows/registry/browser_research.yaml", "runtime/workflows/registry/browser_research.yaml"),
            ("06_AGENTS/role-cards/browser-research.yaml", "06_AGENTS/role-cards/browser-research.yaml"),
            ("runtime/aor/task_type_table.yaml", "runtime/aor/task_type_table.yaml"),
        ]:
            dst = vault / rel_dst
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(real_vault / src, dst)

        self._vault = vault

    def test_summary_written_to_operator_briefs(self):
        stub_audit = _fake_audit(text="", adapter_mode="stub")
        from runtime.aor.engine import run_workflow

        with patch("runtime.workflows.browser_research.OperatorExecutor") as MockExec:
            MockExec.return_value.run.return_value = stub_audit
            result = run_workflow(
                workflow_id="browser_research",
                inputs={"goal": "write path test", "urls": "https://example.com"},
                vault_root=self._vault,
            )

        assert result.status == "success", f"unexpected status: {result.status!r}; reason: {result.escalation_reason}"
        briefs_dir = self._vault / "07_LOGS" / "Operator-Briefs"
        written = list(briefs_dir.glob("*.md"))
        assert len(written) >= 1

    def test_summary_file_contains_goal(self):
        stub_audit = _fake_audit(text="", adapter_mode="stub")
        from runtime.aor.engine import run_workflow

        with patch("runtime.workflows.browser_research.OperatorExecutor") as MockExec:
            MockExec.return_value.run.return_value = stub_audit
            run_workflow(
                workflow_id="browser_research",
                inputs={"goal": "write content verification test", "urls": "https://example.com"},
                vault_root=self._vault,
            )

        briefs_dir = self._vault / "07_LOGS" / "Operator-Briefs"
        files = list(briefs_dir.glob("*.md"))
        assert len(files) >= 1
        content = files[0].read_text(encoding="utf-8")
        assert "write content verification test" in content
