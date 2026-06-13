"""Tests for bounded safe-local workflow replay execution proof."""

from __future__ import annotations

import inspect
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import runtime.browser_runtime.workflow_replay_execution_proof as proof_module
from runtime.browser_runtime.workflow_replay_execution_proof import (
    WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED,
    WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED_MARKER_EXISTS,
    WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED_NO_EXECUTION_REQUESTED,
    WORKFLOW_REPLAY_EXECUTION_PROOF_COMPLETE,
    WORKFLOW_REPLAY_EXECUTION_PROOF_FAILED,
    WorkflowReplayExecutionProofRequest,
    main as proof_main,
    run_workflow_replay_execution_proof,
)


def _write_cache_metadata(root: Path, workflow_id: str, entry_path: Path) -> None:
    metadata_path = root / "runtime" / "browser_workflows" / "metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            {
                "record_type": "browser_workflow_cache_metadata",
                "schema_version": "browser.workflow_cache.v1",
                "status": "inactive_review_cache",
                "activation_allowed": False,
                "replay_allowed": False,
                "trusted_write_allowed": False,
                "external_code_copied": False,
                "workflows": [
                    {
                        "workflow_id": workflow_id,
                        "domain": "127.0.0.1",
                        "status": "reviewed_for_trial",
                        "path": entry_path.as_posix(),
                        "activation_allowed": False,
                        "replay_allowed": True,
                        "trusted_write_allowed": False,
                        "external_code_copied": False,
                        "trial_candidate": True,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_reviewed_workflow(root: Path, *, workflow_id: str = "wf_local_trial") -> Path:
    entry_path = root / "runtime" / "browser_workflows" / "workflows" / f"{workflow_id}.workflow.json"
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "record_type": "browser_workflow_cache_entry",
        "schema_version": "browser.workflow_cache.v1",
        "workflow_id": workflow_id,
        "domain": "127.0.0.1",
        "intent": "local safe workflow trial",
        "source_run_id": "safe-run",
        "source_run_log_path": "07_LOGS/Browser-Runs/safe-run.json",
        "status": "reviewed_for_trial",
        "allowed_domains": ["127.0.0.1"],
        "source_url": "http://127.0.0.1:8770/",
        "steps": [
            {
                "step_id": "step_01_open",
                "action_type": "open",
                "target": "http://127.0.0.1:8770/",
                "status": "succeeded",
                "source_action_index": 0,
            },
            {
                "step_id": "step_02_read_state",
                "action_type": "read_state",
                "target": "initial DOM snapshot",
                "status": "succeeded",
                "source_action_index": 1,
            },
            {
                "step_id": "step_03_click",
                "action_type": "harmless_click",
                "target": "Approvals tab",
                "status": "succeeded",
                "source_action_index": 2,
            },
            {
                "step_id": "step_04_click",
                "action_type": "harmless_click",
                "target": "Workflow tab",
                "status": "succeeded",
                "source_action_index": 3,
            },
            {
                "step_id": "step_05_click",
                "action_type": "harmless_click",
                "target": "Mark panel inspected button",
                "status": "succeeded",
                "source_action_index": 4,
            },
            {
                "step_id": "step_06_screenshot",
                "action_type": "capture_screenshot",
                "target": "visible viewport",
                "status": "succeeded",
                "source_action_index": 5,
            },
        ],
        "review_required": True,
        "activation_allowed": False,
        "replay_allowed": True,
        "trusted_write_allowed": False,
        "external_code_copied": False,
    }
    entry_path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    _write_cache_metadata(root, workflow_id, entry_path)
    return entry_path


class FakeController:
    def __init__(self, marker_path: Path | None = None, *, fail_on_open: bool = False) -> None:
        self.marker_path = marker_path
        self.fail_on_open = fail_on_open
        self.calls: list[str] = []

    def ensure_available(self) -> dict[str, object]:
        self.calls.append("ensure_available")
        return {"available": True}

    def open(self, url: str) -> dict[str, object]:
        self.calls.append("open")
        if self.marker_path is not None:
            assert self.marker_path.exists()
            self.calls.append("marker_existed_before_open")
        if self.fail_on_open:
            raise RuntimeError("simulated open failure")
        return {"opened_url": url}

    def read_state(self) -> dict[str, object]:
        self.calls.append("read_state")
        return {
            "title": "ChaseOS Studio Product UI Test Target",
            "url": "http://127.0.0.1:8770/",
            "visible_text": "Panel inspected in safe mode.",
            "dom_snapshot": {"outer_html_preview": "<body data-safe-mode='true'></body>"},
        }

    def harmless_click(self, target: str) -> dict[str, object]:
        self.calls.append(f"click:{target}")
        return {"ok": True, "target": target}

    def capture_screenshot(self) -> bytes:
        self.calls.append("capture_screenshot")
        return b"fake-png"

    def close(self) -> None:
        self.calls.append("close")


class UnavailableController(FakeController):
    def ensure_available(self) -> dict[str, object]:
        self.calls.append("ensure_available")
        raise RuntimeError("browser unavailable")


def _request(**overrides: object) -> WorkflowReplayExecutionProofRequest:
    payload = {
        "workflow_id": "wf_local_trial",
        "target_url": "http://127.0.0.1:8770/",
        "allowed_domains": ["127.0.0.1"],
        "requested_by": "Codex",
        "operator_id": "operator-test",
        "execute_local_replay": True,
        "run_slug": "safe-local-proof-test",
    }
    payload.update(overrides)
    return WorkflowReplayExecutionProofRequest(**payload)


def test_module_does_not_copy_or_import_external_workflow_runtime_code() -> None:
    source = inspect.getsource(proof_module)
    forbidden = (
        "import workflow_use",
        "from workflow_use",
        "import browser_use",
        "from browser_use",
        "import browser_harness",
        "from browser_harness",
        "playwright",
        "requests.",
    )
    for token in forbidden:
        assert token not in source


def test_no_execute_flag_blocks_without_writes(tmp_path: Path) -> None:
    _write_reviewed_workflow(tmp_path)
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    result = run_workflow_replay_execution_proof(
        tmp_path,
        _request(execute_local_replay=False),
        generated_at="2026-05-03T08:00:00Z",
        controller=FakeController(),
    )
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert result.status == WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED_NO_EXECUTION_REQUESTED
    assert result.approval_request_written is False
    assert result.idempotency_marker_written is False
    assert result.workflow_replay_attempted is False


def test_successful_injected_replay_writes_bounded_artifacts_and_marker_first(tmp_path: Path) -> None:
    _write_reviewed_workflow(tmp_path)
    probe = run_workflow_replay_execution_proof(
        tmp_path,
        _request(execute_local_replay=False),
        generated_at="2026-05-03T08:05:00Z",
        controller=FakeController(),
    )
    marker_path = Path(probe.idempotency_marker_path)
    controller = FakeController(marker_path)

    result = run_workflow_replay_execution_proof(
        tmp_path,
        _request(),
        generated_at="2026-05-03T08:05:00Z",
        controller=controller,
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTION_PROOF_COMPLETE
    assert result.approval_request_written is True
    assert result.idempotency_marker_written is True
    assert result.workflow_replay_attempted is True
    assert result.browser_launch_attempted is True
    assert result.cdp_connection_attempted is True
    assert result.browser_run_log_written is True
    assert result.agent_activity_log_written is True
    assert result.screenshot_artifact_written is True
    assert result.draft_skill_written is True
    assert result.untrusted_candidate_written is True
    assert result.trusted_skill_write_attempted is False
    assert result.skill_activation_attempted is False
    assert result.canonical_writeback_attempted is False
    assert Path(result.approval_request_record_path).exists()
    assert Path(result.idempotency_marker_path).exists()
    assert Path(result.browser_run_log_path).exists()
    assert Path(result.agent_activity_log_path).exists()
    assert Path(result.screenshot_path).read_bytes() == b"fake-png"
    assert Path(result.draft_skill_path).exists()
    assert Path(result.skill_candidate_path).exists()
    assert controller.calls.index("marker_existed_before_open") > controller.calls.index("open")

    marker = json.loads(Path(result.idempotency_marker_path).read_text(encoding="utf-8"))
    assert marker["status"] == "completed"
    assert marker["browser_launch_attempted"] is True
    assert marker["workflow_replay_attempted"] is True


def test_duplicate_marker_blocks_before_browser_action(tmp_path: Path) -> None:
    _write_reviewed_workflow(tmp_path)
    first = run_workflow_replay_execution_proof(
        tmp_path,
        _request(),
        generated_at="2026-05-03T08:10:00Z",
        controller=FakeController(),
    )
    controller = FakeController()

    second = run_workflow_replay_execution_proof(
        tmp_path,
        _request(),
        generated_at="2026-05-03T08:10:00Z",
        controller=controller,
    )

    assert first.status == WORKFLOW_REPLAY_EXECUTION_PROOF_COMPLETE
    assert second.status == WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED_MARKER_EXISTS
    assert second.workflow_replay_attempted is False
    assert "open" not in controller.calls


def test_unavailable_controller_blocks_before_marker_or_approval_write(tmp_path: Path) -> None:
    _write_reviewed_workflow(tmp_path)
    result = run_workflow_replay_execution_proof(
        tmp_path,
        _request(),
        generated_at="2026-05-03T08:15:00Z",
        controller=UnavailableController(),
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED
    assert "browser_controller_unavailable" in result.blockers
    assert Path(result.approval_request_path).exists() is False
    assert Path(result.idempotency_marker_path).exists() is False
    assert result.browser_launch_attempted is False


def test_failure_after_marker_writes_failed_run_log_and_keeps_marker(tmp_path: Path) -> None:
    _write_reviewed_workflow(tmp_path)
    result = run_workflow_replay_execution_proof(
        tmp_path,
        _request(run_slug="safe-local-proof-failure"),
        generated_at="2026-05-03T08:20:00Z",
        controller=FakeController(fail_on_open=True),
    )

    assert result.status == WORKFLOW_REPLAY_EXECUTION_PROOF_FAILED
    assert result.approval_request_written is True
    assert result.idempotency_marker_written is True
    assert result.browser_run_log_written is True
    assert result.agent_activity_log_written is False
    assert result.draft_skill_written is False
    assert Path(result.browser_run_log_path).exists()
    marker = json.loads(Path(result.idempotency_marker_path).read_text(encoding="utf-8"))
    assert marker["status"] == "failed"


def test_retry_after_failed_marker_writes_retry_marker_and_preserves_failed_marker(tmp_path: Path) -> None:
    _write_reviewed_workflow(tmp_path)
    failed = run_workflow_replay_execution_proof(
        tmp_path,
        _request(run_slug="safe-local-proof-retry"),
        generated_at="2026-05-03T08:45:00Z",
        controller=FakeController(fail_on_open=True),
    )
    base_marker = Path(failed.idempotency_marker_path)

    assert failed.status == WORKFLOW_REPLAY_EXECUTION_PROOF_FAILED
    assert json.loads(base_marker.read_text(encoding="utf-8"))["status"] == "failed"

    retry = run_workflow_replay_execution_proof(
        tmp_path,
        _request(run_slug="safe-local-proof-retry", retry_after_failed_marker=True),
        generated_at="2026-05-03T08:45:00Z",
        controller=FakeController(),
    )

    assert retry.status == WORKFLOW_REPLAY_EXECUTION_PROOF_COMPLETE
    assert "-retry-" in retry.approval_request_id
    assert "browser-workflow-replay-retry-" in retry.idempotency_marker_path
    assert Path(retry.idempotency_marker_path).exists()
    assert json.loads(base_marker.read_text(encoding="utf-8"))["status"] == "failed"
    assert Path(retry.browser_run_log_path).exists()


def test_nonlocal_target_blocks_without_writes(tmp_path: Path) -> None:
    _write_reviewed_workflow(tmp_path)
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    result = run_workflow_replay_execution_proof(
        tmp_path,
        _request(target_url="https://example.com/", allowed_domains=["example.com"]),
        generated_at="2026-05-03T08:25:00Z",
        controller=FakeController(),
    )
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))

    assert before == after
    assert result.status == WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED
    assert "target_domain_not_local_only" in result.blockers
    assert result.approval_request_written is False
    assert result.idempotency_marker_written is False


def test_cli_without_execute_is_blocked_no_write(tmp_path: Path) -> None:
    _write_reviewed_workflow(tmp_path)
    before = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    output = io.StringIO()

    with redirect_stdout(output):
        exit_code = proof_main(
            [
                "--vault-root",
                str(tmp_path),
                "--workflow-id",
                "wf_local_trial",
                "--target-url",
                "http://127.0.0.1:8770/",
                "--allowed-domain",
                "127.0.0.1",
                "--json",
            ]
        )
    after = sorted(path.as_posix() for path in tmp_path.rglob("*"))
    payload = json.loads(output.getvalue())

    assert exit_code == 2
    assert before == after
    assert payload["status"] == WORKFLOW_REPLAY_EXECUTION_PROOF_BLOCKED_NO_EXECUTION_REQUESTED
    assert payload["approval_request_written"] is False
    assert payload["idempotency_marker_written"] is False
