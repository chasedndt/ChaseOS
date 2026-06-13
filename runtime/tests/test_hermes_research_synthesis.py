"""
test_hermes_research_synthesis.py — Tests for Hermes Research Synthesis workflow

Covers:
  TestWorkspaceOutputLoading      (6 tests) — _load_workspace_outputs
  TestStructuredSummary           (5 tests) — _build_structured_summary
  TestLLMSynthesis                (6 tests) — _execute_llm_synthesis fail-open paths
  TestQuarantineCapture           (4 tests) — _capture_to_quarantine
  TestRunHandler                  (10 tests) — run_hermes_research_synthesis end-to-end
  TestEngineWiring                (3 tests) — _resolve_workflow_handler dispatch
  TestHermesWatchDispatch         (3 tests) — hermes_watch _TASK_DISPATCH research-synthesis
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.workflows.hermes_research_synthesis import (
    WorkflowExecutionError,
    _build_structured_summary,
    _load_workspace_outputs,
    run_hermes_research_synthesis,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "00_HOME").mkdir(parents=True)
    (vault / "00_HOME" / "Now.md").write_text("# Now\n\nDate: 2026-04-29\n")
    (vault / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    (vault / "03_INPUTS" / "00_QUARANTINE" / "digest").mkdir(parents=True)
    return vault


def _make_workspace(vault: Path, workspace_id: str, num_outputs: int = 2) -> Path:
    outputs_dir = (
        vault / "runtime" / "source_intelligence"
        / "workspaces" / workspace_id / "outputs"
    )
    outputs_dir.mkdir(parents=True)
    for i in range(num_outputs):
        data = {
            "output_id": f"out-{i+1}",
            "output_type": "research-digest",
            "content": f"Research finding {i+1}: this is content block {i+1}.",
        }
        (outputs_dir / f"output_{i+1:03d}.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
    return outputs_dir


# ── TestWorkspaceOutputLoading ────────────────────────────────────────────────

class TestWorkspaceOutputLoading:
    def test_returns_empty_for_missing_workspace(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = _load_workspace_outputs(vault, "nonexistent", limit=3)
        assert result == []

    def test_loads_single_output(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-alpha", num_outputs=1)
        result = _load_workspace_outputs(vault, "ws-alpha", limit=3)
        assert len(result) == 1
        assert result[0]["output_id"] == "out-1"

    def test_loads_multiple_outputs(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-beta", num_outputs=3)
        result = _load_workspace_outputs(vault, "ws-beta", limit=5)
        assert len(result) == 3

    def test_limit_respected(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-gamma", num_outputs=5)
        result = _load_workspace_outputs(vault, "ws-gamma", limit=2)
        assert len(result) == 2

    def test_source_file_injected(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-delta", num_outputs=1)
        result = _load_workspace_outputs(vault, "ws-delta", limit=3)
        assert "_source_file" in result[0]
        assert "ws-delta" in result[0]["_source_file"]

    def test_corrupt_json_silently_skipped(self, tmp_path):
        vault = _make_vault(tmp_path)
        outputs_dir = _make_workspace(vault, "ws-corrupt", num_outputs=1)
        (outputs_dir / "bad.json").write_text("NOT JSON", encoding="utf-8")
        result = _load_workspace_outputs(vault, "ws-corrupt", limit=5)
        assert len(result) == 1


# ── TestStructuredSummary ─────────────────────────────────────────────────────

class TestStructuredSummary:
    def test_contains_workspace_id(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-sum", num_outputs=1)
        outputs = _load_workspace_outputs(vault, "ws-sum", limit=3)
        summary = _build_structured_summary("ws-sum", outputs)
        assert "ws-sum" in summary

    def test_contains_output_section(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-sec", num_outputs=2)
        outputs = _load_workspace_outputs(vault, "ws-sec", limit=3)
        summary = _build_structured_summary("ws-sec", outputs)
        assert "## Output 1" in summary
        assert "## Output 2" in summary

    def test_governance_boundary_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-gov", num_outputs=1)
        outputs = _load_workspace_outputs(vault, "ws-gov", limit=3)
        summary = _build_structured_summary("ws-gov", outputs)
        assert "Governance Boundary" in summary
        assert "quarantine capture only" in summary

    def test_long_content_truncated(self, tmp_path):
        vault = _make_vault(tmp_path)
        outputs_dir = (
            vault / "runtime" / "source_intelligence"
            / "workspaces" / "ws-long" / "outputs"
        )
        outputs_dir.mkdir(parents=True)
        long_content = "x" * 3000
        (outputs_dir / "out.json").write_text(
            json.dumps({"output_id": "big", "content": long_content}), encoding="utf-8"
        )
        outputs = _load_workspace_outputs(vault, "ws-long", limit=3)
        summary = _build_structured_summary("ws-long", outputs)
        assert "truncated at 2000 chars" in summary

    def test_missing_content_field(self, tmp_path):
        vault = _make_vault(tmp_path)
        outputs_dir = (
            vault / "runtime" / "source_intelligence"
            / "workspaces" / "ws-nocontent" / "outputs"
        )
        outputs_dir.mkdir(parents=True)
        (outputs_dir / "out.json").write_text(
            json.dumps({"output_id": "empty"}), encoding="utf-8"
        )
        outputs = _load_workspace_outputs(vault, "ws-nocontent", limit=3)
        summary = _build_structured_summary("ws-nocontent", outputs)
        assert "No content field" in summary


# ── TestLLMSynthesis ──────────────────────────────────────────────────────────

class TestLLMSynthesis:
    def test_returns_none_without_api_key(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-llm", num_outputs=1)
        outputs = _load_workspace_outputs(vault, "ws-llm", limit=3)
        from runtime.workflows.hermes_research_synthesis import _execute_llm_synthesis
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=False):
            result = _execute_llm_synthesis("ws-llm", outputs)
        assert result is None

    def test_returns_none_on_network_error(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-net", num_outputs=1)
        outputs = _load_workspace_outputs(vault, "ws-net", limit=3)
        from runtime.workflows.hermes_research_synthesis import _execute_llm_synthesis
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key-test-key"}, clear=False):
            with patch("urllib.request.urlopen", side_effect=OSError("network error")):
                result = _execute_llm_synthesis("ws-net", outputs)
        assert result is None

    def test_returns_string_on_success(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-ok", num_outputs=1)
        outputs = _load_workspace_outputs(vault, "ws-ok", limit=3)
        from runtime.workflows.hermes_research_synthesis import _execute_llm_synthesis
        mock_body = json.dumps({"content": [{"text": "Synthesized result text."}]}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key-test"}, clear=False):
            with patch("urllib.request.urlopen", return_value=mock_resp):
                result = _execute_llm_synthesis("ws-ok", outputs)
        assert result == "Synthesized result text."

    def test_source_text_capped_at_6000(self, tmp_path):
        vault = _make_vault(tmp_path)
        outputs_dir = (
            vault / "runtime" / "source_intelligence"
            / "workspaces" / "ws-cap" / "outputs"
        )
        outputs_dir.mkdir(parents=True)
        big = "z" * 8000
        (outputs_dir / "out.json").write_text(
            json.dumps({"content": big}), encoding="utf-8"
        )
        outputs = _load_workspace_outputs(vault, "ws-cap", limit=3)
        from runtime.workflows.hermes_research_synthesis import _execute_llm_synthesis
        captured_payloads = []
        def fake_urlopen(req, timeout=None):
            captured_payloads.append(json.loads(req.data.decode("utf-8")))
            raise OSError("stop")
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key-test"}, clear=False):
            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                _execute_llm_synthesis("ws-cap", outputs)
        if captured_payloads:
            prompt = captured_payloads[0]["messages"][0]["content"]
            assert "zzzzz" in prompt
            assert len(prompt) < 7000

    def test_returns_none_on_malformed_response(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-bad-resp", num_outputs=1)
        outputs = _load_workspace_outputs(vault, "ws-bad-resp", limit=3)
        from runtime.workflows.hermes_research_synthesis import _execute_llm_synthesis
        mock_body = b'{"content": []}'
        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key-test"}, clear=False):
            with patch("urllib.request.urlopen", return_value=mock_resp):
                result = _execute_llm_synthesis("ws-bad-resp", outputs)
        assert result is None

    def test_routes_through_execute_synthesis_adapter(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-model", num_outputs=1)
        outputs = _load_workspace_outputs(vault, "ws-model", limit=3)
        from runtime.workflows.hermes_research_synthesis import _execute_llm_synthesis
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.text = "synthesis text"
        with patch("runtime.execution_adapters.execute.execute_synthesis", return_value=mock_result) as mock_synth:
            result = _execute_llm_synthesis("ws-model", outputs, vault_root=vault)
        assert result == "synthesis text"
        mock_synth.assert_called_once()
        call_kwargs = mock_synth.call_args[1]
        assert call_kwargs["execution_adapter"] == "hermes"


# ── TestQuarantineCapture ─────────────────────────────────────────────────────

class TestQuarantineCapture:
    def test_returns_path_on_success(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.hermes_research_synthesis import _capture_to_quarantine
        import runtime.capture.capture as cap_mod
        mock_result = {"capture_path": "03_INPUTS/00_QUARANTINE/digest/test.md"}
        with patch.object(cap_mod, "capture_content", return_value=mock_result):
            result = _capture_to_quarantine(vault, "ws-test", "content", False)
        assert result == "03_INPUTS/00_QUARANTINE/digest/test.md"

    def test_returns_none_on_duplicate(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.hermes_research_synthesis import _capture_to_quarantine
        import runtime.capture.capture as cap_mod
        mock_result = {"is_duplicate": True}
        with patch.object(cap_mod, "capture_content", return_value=mock_result):
            result = _capture_to_quarantine(vault, "ws-dup", "content", False)
        assert result is None

    def test_fail_open_on_capture_exception(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.hermes_research_synthesis import _capture_to_quarantine
        import runtime.capture.capture as cap_mod
        with patch.object(cap_mod, "capture_content", side_effect=RuntimeError("boom")):
            result = _capture_to_quarantine(vault, "ws-err", "content", False)
        assert result is None

    def test_content_path_fallback(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.hermes_research_synthesis import _capture_to_quarantine
        import runtime.capture.capture as cap_mod
        mock_result = {"content_path": "03_INPUTS/00_QUARANTINE/digest/fallback.md"}
        with patch.object(cap_mod, "capture_content", return_value=mock_result):
            result = _capture_to_quarantine(vault, "ws-fallback", "content", False)
        assert result == "03_INPUTS/00_QUARANTINE/digest/fallback.md"


# ── TestRunHandler ────────────────────────────────────────────────────────────

class TestRunHandler:
    def test_raises_without_workspace_id(self, tmp_path):
        vault = _make_vault(tmp_path)
        with pytest.raises(WorkflowExecutionError, match="workspace_id is required"):
            run_hermes_research_synthesis({}, vault)

    def test_raises_for_missing_workspace(self, tmp_path):
        vault = _make_vault(tmp_path)
        with pytest.raises(WorkflowExecutionError, match="has no outputs"):
            run_hermes_research_synthesis({"workspace_id": "no-such-ws"}, vault)

    def test_returns_workspace_id_echo(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-run1", num_outputs=1)
        with patch("runtime.workflows.hermes_research_synthesis._capture_to_quarantine", return_value="03_INPUTS/00_QUARANTINE/digest/out.md"):
            result = run_hermes_research_synthesis({"workspace_id": "ws-run1"}, vault)
        assert result["workspace_id"] == "ws-run1"

    def test_outputs_read_count(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-run2", num_outputs=2)
        with patch("runtime.workflows.hermes_research_synthesis._capture_to_quarantine", return_value=None):
            result = run_hermes_research_synthesis({"workspace_id": "ws-run2"}, vault)
        assert result["outputs_read"] == 2

    def test_output_limit_honored(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-lim", num_outputs=5)
        with patch("runtime.workflows.hermes_research_synthesis._capture_to_quarantine", return_value=None):
            result = run_hermes_research_synthesis(
                {"workspace_id": "ws-lim", "output_limit": 2}, vault
            )
        assert result["outputs_read"] == 2

    def test_synthesis_used_false_without_api_key(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-nokey", num_outputs=1)
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=False):
            with patch("runtime.workflows.hermes_research_synthesis._capture_to_quarantine", return_value=None):
                result = run_hermes_research_synthesis({"workspace_id": "ws-nokey"}, vault)
        assert result["synthesis_used"] is False

    def test_synthesis_skipped_when_disabled(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-nosyn", num_outputs=1)
        with patch("runtime.workflows.hermes_research_synthesis._capture_to_quarantine", return_value=None):
            result = run_hermes_research_synthesis(
                {"workspace_id": "ws-nosyn", "synthesize": False}, vault
            )
        assert result["synthesis_used"] is False

    def test_writebacks_contains_audit_log(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-audit", num_outputs=1)
        with patch("runtime.workflows.hermes_research_synthesis._capture_to_quarantine", return_value=None):
            result = run_hermes_research_synthesis({"workspace_id": "ws-audit"}, vault)
        assert "writebacks" in result
        assert len(result["writebacks"]) >= 1
        audit_wb = result["writebacks"][0]
        assert "07_LOGS/Agent-Activity" in audit_wb["path"]
        assert "hermes_research_synthesis" in audit_wb["content"]

    def test_audit_log_has_frontmatter(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-fm", num_outputs=1)
        with patch("runtime.workflows.hermes_research_synthesis._capture_to_quarantine", return_value=None):
            result = run_hermes_research_synthesis({"workspace_id": "ws-fm"}, vault)
        content = result["writebacks"][0]["content"]
        assert "workflow: hermes_research_synthesis" in content
        assert "authority: quarantine-capture-only" in content

    def test_synthesis_used_true_on_llm_success(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-llm-ok", num_outputs=1)
        with patch("runtime.workflows.hermes_research_synthesis._execute_llm_synthesis", return_value="LLM synthesized text."):
            with patch("runtime.workflows.hermes_research_synthesis._capture_to_quarantine", return_value="path/to/out.md"):
                result = run_hermes_research_synthesis(
                    {"workspace_id": "ws-llm-ok", "synthesize": True}, vault
                )
        assert result["synthesis_used"] is True
        assert result["captured_path"] == "path/to/out.md"


# ── TestEngineWiring ──────────────────────────────────────────────────────────

class TestEngineWiring:
    def test_engine_resolves_hermes_research_synthesis(self):
        from runtime.aor.engine import _resolve_workflow_handler
        handler = _resolve_workflow_handler("hermes_research_synthesis")
        assert handler is not None

    def test_engine_handler_is_callable(self):
        from runtime.aor.engine import _resolve_workflow_handler
        handler = _resolve_workflow_handler("hermes_research_synthesis")
        assert callable(handler)

    def test_engine_handler_is_correct_function(self):
        from runtime.aor.engine import _resolve_workflow_handler
        from runtime.workflows.hermes_research_synthesis import run_hermes_research_synthesis
        handler = _resolve_workflow_handler("hermes_research_synthesis")
        assert handler is run_hermes_research_synthesis


# ── TestHermesWatchDispatch ───────────────────────────────────────────────────

class TestHermesWatchDispatch:
    def test_research_synthesis_in_dispatch_table(self):
        from runtime.workflows.hermes_watch import _TASK_DISPATCH
        assert "research-synthesis" in _TASK_DISPATCH

    def test_dispatch_fn_is_callable(self):
        from runtime.workflows.hermes_watch import _TASK_DISPATCH
        fn = _TASK_DISPATCH["research-synthesis"]
        assert callable(fn)

    def test_dispatch_fn_passes_workspace_id_from_notes(self, tmp_path):
        vault = _make_vault(tmp_path)
        _make_workspace(vault, "ws-dispatch", num_outputs=1)
        task = {
            "task_id": "task-001",
            "notes": "workspace_id: ws-dispatch",
            "request": "",
        }
        from runtime.workflows.hermes_watch import _TASK_DISPATCH
        fn = _TASK_DISPATCH["research-synthesis"]
        with patch("runtime.workflows.hermes_research_synthesis._capture_to_quarantine", return_value=None):
            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""}, clear=False):
                result = fn(task, vault, False)
        assert result["workspace_id"] == "ws-dispatch"
