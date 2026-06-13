from __future__ import annotations

import json
import shutil
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import runtime.cli.main as cli
from runtime.browser_runtime.adapter import BrowserRuntimePolicyError, ShadowBrowserRuntimeAdapter
from runtime.browser_runtime.adapters.browser_use_cli import BrowserUseCLIAdapter
from runtime.browser_runtime.artifacts import (
    build_screenshot_artifact,
    browser_run_artifact_path,
    validate_browser_artifact_path,
)
from runtime.browser_runtime.adapters.cdp_design import CDPAdapterDesignRequest, evaluate_cdp_adapter_design
from runtime.browser_runtime.cdp_executor_spec import (
    build_cdp_read_only_atomic_marker_writer_design,
    build_cdp_read_only_approval_decision_consumer_design,
    build_cdp_read_only_closeout_readiness_report,
    build_cdp_read_only_approval_decision_policy,
    build_cdp_read_only_decision_preflight,
    build_cdp_read_only_executor_dry_run_plan,
    build_cdp_read_only_executor_spec,
    execute_cdp_read_only_proof,
    build_cdp_read_only_isolated_browser_launcher_design,
    build_cdp_read_only_isolated_launcher_implementation_preflight,
    write_cdp_read_only_approval_decision,
    build_cdp_read_only_idempotency_reservation_spec,
    cdp_read_only_idempotency_marker_path,
    validate_cdp_read_only_approval_artifact,
    write_cdp_read_only_approval_request,
)
from runtime.browser_runtime.logging import persist_run_evidence
from runtime.browser_runtime.models import BrowserRunRequest, BrowserRuntimeConfig, BrowserRuntimeProvider
from runtime.browser_runtime.skills import create_and_write_site_skill_draft
from runtime.browser_runtime.smoke import run_shadow_smoke
from runtime.browser_runtime.vincisos_preflight import (
    VincisOSBrowserPreflightRequest,
    evaluate_vincisos_browser_preflight,
)
from runtime.browser_runtime.vincisos_full_ui_preflight import (
    VincisOSFullUISafeModePreflightRequest,
    evaluate_vincisos_full_ui_safe_mode_preflight,
)
from runtime.browser_runtime.vincisos_full_ui_target_contract import (
    FORBIDDEN_AUTHORITY_FLAGS,
    evaluate_vincisos_full_ui_target_contract,
    evaluate_vincisos_full_ui_target_contract_file,
)
from runtime.browser_runtime.vincisos_contract_backed_proof import (
    PROOF_PLAN_VERSION,
    build_vincisos_contract_backed_proof_plan,
    build_vincisos_contract_backed_proof_plan_from_file,
)
from runtime.browser_runtime.vincisos_product_ui_target_probe import (
    PROBE_VERSION,
    probe_vincisos_product_ui_target,
    probe_vincisos_product_ui_target_file,
)
from runtime.browser_runtime.vincisos_product_ui_launch_readiness import (
    READINESS_VERSION,
    build_vincisos_product_ui_launch_readiness,
)
from runtime.browser_runtime.vincisos_static_target import (
    TARGET_FILE,
    run_vincisos_static_target_preflight,
)


def test_shadow_smoke_writes_run_activity_and_draft(tmp_path: Path) -> None:
    payload = run_shadow_smoke(root=tmp_path)

    assert payload["ok"] is True
    run_log = Path(payload["browser_run_log_path"])
    activity = Path(payload["agent_activity_log_path"])
    draft = Path(payload["skill_draft_path"])
    candidate = Path(payload["skill_candidate_path"])
    ledger = Path(payload["site_activity_log_path"])
    assert run_log.exists()
    assert activity.exists()
    assert draft.exists()
    assert candidate.exists()
    assert ledger.exists()
    assert run_log.parent == tmp_path / "07_LOGS" / "Browser-Runs"
    assert draft.parent == tmp_path / "06_AGENTS" / "Browser-Skills" / "_drafts"
    assert candidate.parent == tmp_path / "03_INPUTS" / "Browser-Skill-Candidates" / "example-com"
    assert ledger.parent == tmp_path / "07_LOGS" / "Site-Activity"

    record = json.loads(run_log.read_text(encoding="utf-8"))
    assert record["result"]["security_flags"]["real_profile_used"] is False
    assert record["result"]["security_flags"]["canonical_writeback"] is False
    assert "activation_allowed: false" in draft.read_text(encoding="utf-8")
    assert "candidate_untrusted" in candidate.read_text(encoding="utf-8")


def test_policy_blocks_real_profile_and_forbidden_domain(tmp_path: Path) -> None:
    adapter = ShadowBrowserRuntimeAdapter(
        BrowserRuntimeConfig(enabled=True, allowed_providers=["shadow"], allowed_domains=["example.com"])
    )

    real_profile = BrowserRunRequest(
        url="https://example.com",
        task="should block",
        provider=BrowserRuntimeProvider.SHADOW,
        use_real_profile=True,
    )
    try:
        adapter.run_task(real_profile, vault_root=tmp_path)
    except BrowserRuntimePolicyError as exc:
        assert "real browser profiles" in str(exc)
    else:
        raise AssertionError("real profile request should be blocked")

    forbidden = BrowserRunRequest(
        url="https://gmail.com",
        task="should block",
        provider=BrowserRuntimeProvider.SHADOW,
        allowed_domains=["gmail.com"],
    )
    try:
        adapter.run_task(forbidden, vault_root=tmp_path)
    except BrowserRuntimePolicyError as exc:
        assert "forbidden" in str(exc)
    else:
        raise AssertionError("forbidden domain request should be blocked")


def test_browser_use_cli_fails_closed_when_unavailable(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("runtime.browser_runtime.adapters.browser_use_cli.shutil.which", lambda _: None)
    adapter = BrowserUseCLIAdapter(
        BrowserRuntimeConfig(enabled=True, allowed_providers=["browser-use-cli"], allowed_domains=["example.com"])
    )
    request = BrowserRunRequest(
        url="https://example.com",
        task="state check",
        provider=BrowserRuntimeProvider.BROWSER_USE_CLI,
    )

    result = adapter.run_task(request, vault_root=tmp_path)

    assert result.status == "blocked"
    assert "not installed" in (result.error or "")


def test_draft_generation_links_run_evidence(tmp_path: Path) -> None:
    config = BrowserRuntimeConfig(enabled=True, allowed_providers=["shadow"], allowed_domains=["example.com"])
    request = BrowserRunRequest(
        url="https://example.com",
        task="draft evidence",
        provider=BrowserRuntimeProvider.SHADOW,
    )
    result = ShadowBrowserRuntimeAdapter(config).run_task(request, vault_root=tmp_path)
    persisted = persist_run_evidence(result, request, root=tmp_path)

    draft, draft_path = create_and_write_site_skill_draft(
        persisted,
        root=tmp_path,
        source_log_path=persisted.browser_run_log_path,
    )

    assert draft.status == "draft"
    assert draft.activation_allowed is False
    assert persisted.browser_run_log_path in draft.evidence_links
    assert Path(draft_path).exists()


def test_browser_artifact_path_validation_allows_declared_log_dirs() -> None:
    root = _workspace_test_root("browser_artifact_allowed")
    try:
        browser_runs_path = root / "07_LOGS" / "Browser-Runs" / "proof.png"
        browser_runs_path.parent.mkdir(parents=True, exist_ok=True)
        browser_runs_path.write_bytes(b"png-bytes")

        validation = validate_browser_artifact_path(browser_runs_path, root=root, require_exists=True)

        assert validation.ok is True
        assert validation.status == "artifact_present"
        assert validation.relative_path == "07_LOGS/Browser-Runs/proof.png"
        assert validation.bytes == len(b"png-bytes")

        operator_screenshot = root / "07_LOGS" / "Operator-Screenshots" / "proof.png"
        operator_screenshot.parent.mkdir(parents=True, exist_ok=True)
        operator_screenshot.write_bytes(b"operator-png")

        operator_validation = validate_browser_artifact_path(operator_screenshot, root=root, require_exists=True)

        assert operator_validation.ok is True
        assert operator_validation.relative_path == "07_LOGS/Operator-Screenshots/proof.png"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_browser_artifact_path_validation_blocks_untrusted_targets() -> None:
    root = _workspace_test_root("browser_artifact_blocked")
    outside_root = root.parent / f"{root.name}_outside.png"
    try:
        outside_allowed_dir = root / "06_AGENTS" / "proof.png"
        outside_allowed_dir.parent.mkdir(parents=True, exist_ok=True)
        outside_allowed_dir.write_bytes(b"png-bytes")

        validation = validate_browser_artifact_path(outside_allowed_dir, root=root, require_exists=True)

        assert validation.ok is False
        assert validation.status == "blocked_artifact_outside_allowed_dirs"

        outside_root.write_bytes(b"png-bytes")
        outside_validation = validate_browser_artifact_path(outside_root, root=root, require_exists=True)
        assert outside_validation.ok is False
        assert outside_validation.status == "blocked_artifact_outside_vault_root"
    finally:
        outside_root.unlink(missing_ok=True)
        shutil.rmtree(root, ignore_errors=True)


def test_build_screenshot_artifact_requires_nonempty_confined_file() -> None:
    root = _workspace_test_root("browser_artifact_build")
    try:
        screenshot_path = root / "07_LOGS" / "Browser-Runs" / "proof.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        screenshot_path.write_bytes(b"png-bytes")

        artifact = build_screenshot_artifact(
            screenshot_path,
            root=root,
            description="Test screenshot evidence.",
            metadata={"method": "unit-test"},
        )

        assert artifact.artifact_type == "screenshot"
        assert artifact.path == "07_LOGS/Browser-Runs/proof.png"
        assert artifact.metadata["bytes"] == len(b"png-bytes")
        assert artifact.metadata["method"] == "unit-test"

        empty_path = root / "07_LOGS" / "Browser-Runs" / "empty.png"
        empty_path.write_bytes(b"")
        try:
            build_screenshot_artifact(empty_path, root=root)
        except ValueError as exc:
            assert "smaller than required minimum" in str(exc)
        else:
            raise AssertionError("empty screenshot artifact should be blocked")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_browser_run_artifact_path_slugifies_inside_browser_runs() -> None:
    root = _workspace_test_root("browser_artifact_path")
    try:
        artifact_path = browser_run_artifact_path("Run 01 / VincisOS", ".screenshot.png", root=root)

        assert artifact_path == root / "07_LOGS" / "Browser-Runs" / "run-01-vincisos-screenshot-png"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_design_preflight_ready_but_never_executable() -> None:
    request = CDPAdapterDesignRequest(
        cdp_endpoint="http://127.0.0.1:9222",
        target_url="http://127.0.0.1:4173",
        allowed_domains=["127.0.0.1"],
        allowed_actions=["page.navigate", "dom.snapshot", "page.capture_screenshot"],
    )

    result = evaluate_cdp_adapter_design(request)

    assert result["ok"] is True
    assert result["status"] == "cdp_adapter_design_preflight_ready_no_execution"
    assert result["adapter_implemented"] is False
    assert result["execution_allowed"] is False
    assert result["browser_launch_allowed"] is False
    assert result["cdp_connection_attempted"] is False
    assert result["raw_cdp_exposed"] is False
    assert result["trusted_skill_write_allowed"] is False
    assert result["canonical_writeback_allowed"] is False


def test_cdp_design_preflight_blocks_remote_endpoint_profile_and_secrets() -> None:
    request = CDPAdapterDesignRequest(
        cdp_endpoint="ws://10.0.0.5:9222/devtools/browser/example",
        target_url="https://gmail.com",
        allowed_domains=["example.com"],
        allowed_actions=["page.navigate", "runtime.evaluate", "network.getAllCookies"],
        use_existing_profile=True,
        allow_credentials=True,
        allow_cookie_access=True,
        expose_raw_cdp=True,
        allow_runtime_evaluate=True,
        allow_canonical_writeback=True,
        allow_trusted_skill_write=True,
    )

    result = evaluate_cdp_adapter_design(request)
    blockers = {item["blocker_id"] for item in result["blockers"]}

    assert result["ok"] is False
    assert result["status"] == "blocked_cdp_adapter_design_policy"
    assert "cdp_endpoint_not_local" in blockers
    assert "target_domain_not_allowlisted" in blockers
    assert "existing_profile_forbidden" in blockers
    assert "credentials_forbidden" in blockers
    assert "cookie_access_forbidden" in blockers
    assert "raw_cdp_exposure_forbidden" in blockers
    assert "runtime_evaluate_forbidden" in blockers
    assert "canonical_writeback_forbidden" in blockers
    assert "trusted_skill_write_forbidden" in blockers
    assert "forbidden_cdp_actions_requested" in blockers
    assert result["execution_allowed"] is False
    assert result["cdp_connection_attempted"] is False


def test_cdp_read_only_executor_spec_is_non_executing_until_approved() -> None:
    payload = build_cdp_read_only_executor_spec(
        target_url="http://127.0.0.1:4173",
        runtime="Codex",
    )

    assert payload["ok"] is True
    assert payload["operation"] == "browser.cdp.read_only_proof"
    assert payload["approval_schema_id"] == "bosl.cdp_read_only_proof.v1"
    assert payload["executor_status"] == "implemented"
    assert payload["execution_enabled"] is False
    assert payload["cdp_read_only_proof_allowed"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["cdp_connection_attempted"] is False
    assert payload["credential_value_read"] is False
    assert payload["cookie_or_session_read"] is False
    assert payload["real_profile_used"] is False
    assert payload["trusted_skill_written"] is False
    assert payload["canonical_files_mutated"] is False
    assert payload["approval_request_written"] is False
    assert payload["files_modified"] is False
    assert payload["gate_policy"]["allowed"] is False
    assert "bosl.cdp_read_only_proof.v1" in payload["gate_policy"]["reason"]
    assert payload["approval_validation"]["artifact_store_implemented"] is True
    assert payload["cdp_design_preflight"]["ok"] is True
    assert "executor_implemented" not in payload["blocked_reasons"]
    assert "gate_execution_allowed" in payload["blocked_reasons"]
    assert "approval_artifact_supplied" in payload["blocked_reasons"]


def test_cdp_read_only_approval_request_writes_pending_artifact_without_execution() -> None:
    root = _workspace_test_root("cdp_approval_artifact")
    try:
        _assert_cdp_read_only_approval_request_writes(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _assert_cdp_read_only_approval_request_writes(root: Path) -> None:
    result = write_cdp_read_only_approval_request(
        root,
        target_url="http://localhost:4173",
        runtime="Codex",
        requested_by="tester",
    )

    path = Path(result["approval_ref"])
    assert result["approval_request_written"] is True
    assert path.exists()
    assert path.parent == root / "07_LOGS" / "Agent-Activity" / "_bosl_cdp_approvals"
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["record_type"] == "browser_cdp_read_only_proof_approval_request"
    assert record["approval_schema_id"] == "bosl.cdp_read_only_proof.v1"
    assert record["operation"] == "browser.cdp.read_only_proof"
    assert record["status"] == "pending"
    assert record["requested_by"] == "tester"
    assert record["target_url"] == "http://localhost:4173"
    assert record["browser_launch_attempted"] is False
    assert record["cdp_connection_attempted"] is False
    assert record["credential_value_read"] is False
    assert record["cookie_or_session_read"] is False
    assert record["trusted_skill_written"] is False
    assert record["canonical_files_mutated"] is False

    validation = validate_cdp_read_only_approval_artifact(
        root,
        result["gate_approval_id"],
        expected_target_url="http://localhost:4173",
        expected_runtime="Codex",
    )
    assert validation["artifact_supplied"] is True
    assert validation["artifact_lookup_attempted"] is True
    assert validation["structurally_valid"] is True
    assert validation["approval_status"] == "pending"
    assert validation["approval_decision_accepted"] is False

    payload = build_cdp_read_only_executor_spec(
        vault_root=root,
        target_url="http://localhost:4173",
        runtime="Codex",
        gate_approval_id=result["gate_approval_id"],
    )
    assert payload["approval_validation"]["structurally_valid"] is True
    assert payload["approval_validation"]["approval_decision_accepted"] is False
    assert payload["browser_launch_attempted"] is False
    assert payload["cdp_connection_attempted"] is False


def test_cdp_read_only_decision_preflight_is_non_executing_and_write_plan_limited() -> None:
    root = _workspace_test_root("cdp_decision_preflight")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        payload = build_cdp_read_only_decision_preflight(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
        )

        assert payload["ok"] is True
        assert payload["decision_consumption_status"] == "blocked_approval_not_approved"
        assert payload["executor_status"] == "implemented"
        assert payload["execution_enabled"] is False
        assert payload["cdp_read_only_proof_allowed"] is False
        assert payload["approval_status"] == "pending"
        assert payload["approval_status_approved"] is False
        assert payload["approval_decision_accepted"] is False
        assert payload["approval_consumed"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["screenshot_attempted"] is False
        assert payload["dom_snapshot_attempted"] is False
        assert payload["trusted_skill_written"] is False
        assert payload["canonical_files_mutated"] is False
        assert payload["idempotency"]["marker_exists"] is False
        assert payload["future_write_plan"]["write_plan_status"] == "planned_no_write"
        assert payload["future_write_plan"]["writes_attempted"] is False
        target_paths = [item["path"] for item in payload["future_write_plan"]["targets"]]
        assert any(path.startswith("07_LOGS/Browser-Runs/") for path in target_paths)
        assert any(path.startswith("07_LOGS/Agent-Activity/") for path in target_paths)
        assert any(path.startswith("07_LOGS/Operator-Screenshots/") for path in target_paths)
        assert any(path.startswith("03_INPUTS/Browser-Skill-Candidates/") for path in target_paths)
        assert "browser_cdp_approval_not_approved" in payload["blocked_reasons"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_decision_preflight_flags_existing_idempotency_marker() -> None:
    root = _workspace_test_root("cdp_decision_marker")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text('{"status":"reserved_for_future_test"}\n', encoding="utf-8")

        payload = build_cdp_read_only_decision_preflight(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
        )

        assert payload["idempotency"]["marker_exists"] is True
        assert payload["decision_consumption_status"] == "blocked_prior_cdp_proof_marker_exists"
        assert "browser_cdp_idempotency_marker_exists" in payload["blocked_reasons"]
        assert payload["approval_consumed"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["files_modified"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_idempotency_reservation_spec_is_no_write_and_pending_blocked() -> None:
    root = _workspace_test_root("cdp_reservation_spec")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        payload = build_cdp_read_only_idempotency_reservation_spec(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
        )
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])

        assert payload["ok"] is True
        assert payload["reservation_status"] == "blocked_approval_not_approved"
        assert payload["executor_status"] == "implemented"
        assert payload["execution_enabled"] is False
        assert payload["approval_status"] == "pending"
        assert payload["approval_decision_accepted"] is False
        assert payload["approval_consumed"] is False
        assert payload["approval_artifact_mutated"] is False
        assert payload["idempotency_marker_written"] is False
        assert payload["idempotency"]["marker_exists_before"] is False
        assert payload["marker_record_template"]["record_type"] == "browser_cdp_read_only_proof_idempotency_marker"
        assert payload["marker_record_template"]["browser_launch_attempted"] is False
        assert payload["marker_record_template"]["cookie_or_session_read"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["trusted_skill_written"] is False
        assert payload["canonical_files_mutated"] is False
        assert payload["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_idempotency_reservation_spec_flags_existing_marker() -> None:
    root = _workspace_test_root("cdp_reservation_marker")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text('{"status":"reserved_for_future_test"}\n', encoding="utf-8")

        payload = build_cdp_read_only_idempotency_reservation_spec(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
        )

        assert payload["reservation_status"] == "blocked_prior_cdp_proof_marker_exists"
        assert payload["idempotency"]["marker_exists"] is True
        assert payload["idempotency_marker_written"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["files_modified"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_executor_dry_run_plan_is_no_write_and_pending_blocked() -> None:
    root = _workspace_test_root("cdp_executor_dry_run")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        payload = build_cdp_read_only_executor_dry_run_plan(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
        )
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])

        assert payload["ok"] is True
        assert payload["dry_run_status"] == "blocked_approval_not_approved"
        assert payload["dry_run_only"] is True
        assert payload["executor_status"] == "implemented"
        assert payload["execution_enabled"] is False
        assert payload["approval_status"] == "pending"
        assert payload["approval_decision_accepted"] is False
        assert payload["approval_consumed"] is False
        assert payload["idempotency_marker_written"] is False
        assert payload["idempotency"]["marker_exists"] is False
        assert payload["future_artifacts"]["writes_attempted"] is False
        assert payload["feature_completion_tracker"]["pre_execution_governance_status"] == (
            "complete_after_dry_run_plan_targeted_verification"
        )
        assert payload["feature_completion_tracker"]["live_cdp_execution_status"] == "not_built"
        step_ids = [step["step_id"] for step in payload["future_execution_sequence"]]
        assert step_ids[:3] == [
            "reload_and_validate_approval_artifact",
            "consume_approval_decision",
            "reserve_idempotency_marker",
        ]
        assert all(step["attempted_now"] is False for step in payload["future_execution_sequence"])
        assert payload["browser_launch_attempted"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["screenshot_attempted"] is False
        assert payload["dom_snapshot_attempted"] is False
        assert payload["trusted_skill_written"] is False
        assert payload["canonical_files_mutated"] is False
        assert payload["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_approval_decision_policy_is_no_write_and_pending_blocked() -> None:
    root = _workspace_test_root("cdp_approval_decision_policy")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        payload = build_cdp_read_only_approval_decision_policy(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
        )
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])

        assert payload["ok"] is True
        assert payload["policy_status"] == "blocked_approval_not_approved"
        assert payload["approval_status"] == "pending"
        assert payload["approval_artifact_structurally_valid"] is True
        assert payload["approval_decision_metadata_present"] is False
        assert payload["approval_decision_accepted"] is False
        assert payload["approval_consumption_policy"]["consumer_status"] == "not_built"
        assert payload["approval_consumption_policy"]["approved_status_alone_is_sufficient"] is False
        assert payload["decision_record_template"]["record_type"] == "browser_cdp_read_only_proof_approval_decision"
        assert payload["decision_record_template"]["single_use"] is True
        assert payload["approval_consumed"] is False
        assert payload["approval_decision_written"] is False
        assert payload["idempotency_marker_written"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_approval_decision_consumer_design_is_no_write_and_pending_blocked() -> None:
    root = _workspace_test_root("cdp_approval_decision_consumer_design")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        payload = build_cdp_read_only_approval_decision_consumer_design(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
        )
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])

        assert payload["ok"] is True
        assert payload["consumer_design_status"] == "blocked_approval_not_approved"
        assert payload["consumer_status"] == "not_built"
        assert payload["execution_enabled"] is False
        assert payload["approval_status"] == "pending"
        assert payload["approval_decision_accepted"] is False
        assert payload["approval_consumed"] is False
        assert payload["approval_decision_written"] is False
        assert payload["idempotency_marker_written"] is False
        assert payload["idempotency"]["marker_exists"] is False
        assert payload["single_use_constraints"]["source_approval_mutation_allowed"] is False
        assert payload["single_use_constraints"]["consume_twice_allowed"] is False
        assert payload["consume_record_template"]["consumer_record_schema"] == (
            "browser_cdp_read_only_approval_decision_consumer.v1"
        )
        assert "cookie" in payload["forbidden_consumer_fields"]
        assert payload["browser_launch_attempted"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["trusted_skill_written"] is False
        assert payload["canonical_files_mutated"] is False
        assert payload["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_approval_decision_consumer_design_flags_existing_marker() -> None:
    root = _workspace_test_root("cdp_approval_decision_consumer_existing")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text('{"status":"reserved_for_future_test"}\n', encoding="utf-8")

        payload = build_cdp_read_only_approval_decision_consumer_design(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
        )

        assert payload["consumer_design_status"] == "blocked_prior_cdp_proof_marker_exists"
        assert payload["idempotency"]["marker_exists"] is True
        assert payload["idempotency_marker_written"] is False
        assert payload["approval_consumed"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["files_modified"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_atomic_marker_writer_design_is_no_write_and_pending_blocked() -> None:
    root = _workspace_test_root("cdp_atomic_marker_writer_design")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        payload = build_cdp_read_only_atomic_marker_writer_design(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
        )
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])

        assert payload["ok"] is True
        assert payload["writer_design_status"] == "blocked_approval_not_approved"
        assert payload["writer_status"] == "not_built"
        assert payload["execution_enabled"] is False
        assert payload["approval_status"] == "pending"
        assert payload["approval_decision_accepted"] is False
        assert payload["approval_consumed"] is False
        assert payload["approval_decision_written"] is False
        assert payload["idempotency_marker_written"] is False
        assert payload["marker_directory_created"] is False
        assert payload["idempotency"]["marker_exists"] is False
        assert payload["path_constraints"]["overwrite_allowed"] is False
        assert payload["path_constraints"]["delete_on_failure_allowed"] is False
        assert payload["marker_record_template"]["writer_record_schema"] == (
            "browser_cdp_read_only_atomic_marker_writer.v1"
        )
        assert "cookie" in payload["forbidden_marker_fields"]
        assert payload["browser_launch_attempted"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["trusted_skill_written"] is False
        assert payload["canonical_files_mutated"] is False
        assert payload["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_atomic_marker_writer_design_flags_existing_marker() -> None:
    root = _workspace_test_root("cdp_atomic_marker_writer_existing")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text('{"status":"reserved_for_future_test"}\n', encoding="utf-8")

        payload = build_cdp_read_only_atomic_marker_writer_design(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
        )

        assert payload["writer_design_status"] == "blocked_prior_cdp_proof_marker_exists"
        assert payload["idempotency"]["marker_exists"] is True
        assert payload["idempotency_marker_written"] is False
        assert payload["approval_consumed"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["files_modified"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_runtime_browser_cdp_executor_spec_cli_is_read_only(capsys) -> None:
    exit_code = cli.main(
        [
            "runtime",
            "browser-cdp",
            "executor-spec",
            "http://127.0.0.1:4173",
            "--runtime",
            "Codex",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 0
    assert payload["ok"] is True
    assert result["executor_status"] == "implemented"
    assert result["execution_enabled"] is False
    assert result["browser_launch_attempted"] is False
    assert result["cdp_connection_attempted"] is False
    assert result["trusted_skill_written"] is False
    assert result["canonical_files_mutated"] is False
    assert result["approval_request_written"] is False


def test_runtime_browser_cdp_approval_request_cli_writes_pending_artifact(capsys) -> None:
    root = _workspace_test_root("cdp_approval_cli")
    try:
        _assert_runtime_browser_cdp_approval_request_cli(root, capsys)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _assert_runtime_browser_cdp_approval_request_cli(root: Path, capsys) -> None:
    exit_code = cli.main(
        [
            "runtime",
            "browser-cdp",
            "approval-request",
            "http://127.0.0.1:4173",
            "--runtime",
            "Codex",
            "--requested-by",
            "tester",
            "--write-approval-request",
            "--vault-root",
            str(root),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 0
    assert payload["ok"] is True
    assert result["approval_request_written"] is True
    assert Path(result["approval_ref"]).exists()
    assert result["browser_launch_attempted"] is False
    assert result["cdp_connection_attempted"] is False
    assert result["trusted_skill_written"] is False
    assert result["canonical_files_mutated"] is False


def test_runtime_browser_cdp_decision_preflight_cli_is_read_only(capsys) -> None:
    root = _workspace_test_root("cdp_decision_cli")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        exit_code = cli.main(
            [
                "runtime",
                "browser-cdp",
                "decision-preflight",
                "http://127.0.0.1:4173",
                "--runtime",
                "Codex",
                "--gate-approval-id",
                result["gate_approval_id"],
                "--vault-root",
                str(root),
                "--json",
            ]
        )

        payload = json.loads(capsys.readouterr().out)
        body = payload["result"]
        assert exit_code == 0
        assert payload["ok"] is True
        assert body["decision_consumption_status"] == "blocked_approval_not_approved"
        assert body["executor_status"] == "implemented"
        assert body["execution_enabled"] is False
        assert body["approval_consumed"] is False
        assert body["browser_launch_attempted"] is False
        assert body["cdp_connection_attempted"] is False
        assert body["files_modified"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_runtime_browser_cdp_idempotency_reservation_spec_cli_is_read_only(capsys) -> None:
    root = _workspace_test_root("cdp_reservation_cli")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        exit_code = cli.main(
            [
                "runtime",
                "browser-cdp",
                "idempotency-reservation-spec",
                "http://127.0.0.1:4173",
                "--runtime",
                "Codex",
                "--gate-approval-id",
                result["gate_approval_id"],
                "--vault-root",
                str(root),
                "--json",
            ]
        )

        payload = json.loads(capsys.readouterr().out)
        body = payload["result"]
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])
        assert exit_code == 0
        assert payload["ok"] is True
        assert body["reservation_status"] == "blocked_approval_not_approved"
        assert body["executor_status"] == "implemented"
        assert body["execution_enabled"] is False
        assert body["approval_consumed"] is False
        assert body["idempotency_marker_written"] is False
        assert body["browser_launch_attempted"] is False
        assert body["cdp_connection_attempted"] is False
        assert body["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_runtime_browser_cdp_executor_dry_run_cli_is_read_only(capsys) -> None:
    root = _workspace_test_root("cdp_executor_dry_run_cli")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        exit_code = cli.main(
            [
                "runtime",
                "browser-cdp",
                "executor-dry-run",
                "http://127.0.0.1:4173",
                "--runtime",
                "Codex",
                "--gate-approval-id",
                result["gate_approval_id"],
                "--vault-root",
                str(root),
                "--json",
            ]
        )

        payload = json.loads(capsys.readouterr().out)
        body = payload["result"]
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])
        assert exit_code == 0
        assert payload["ok"] is True
        assert body["dry_run_status"] == "blocked_approval_not_approved"
        assert body["dry_run_only"] is True
        assert body["executor_status"] == "implemented"
        assert body["execution_enabled"] is False
        assert body["approval_consumed"] is False
        assert body["idempotency_marker_written"] is False
        assert body["browser_launch_attempted"] is False
        assert body["cdp_connection_attempted"] is False
        assert body["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_runtime_browser_cdp_approval_decision_policy_cli_is_read_only(capsys) -> None:
    root = _workspace_test_root("cdp_approval_decision_policy_cli")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        exit_code = cli.main(
            [
                "runtime",
                "browser-cdp",
                "approval-decision-policy",
                "http://127.0.0.1:4173",
                "--runtime",
                "Codex",
                "--gate-approval-id",
                result["gate_approval_id"],
                "--vault-root",
                str(root),
                "--json",
            ]
        )

        payload = json.loads(capsys.readouterr().out)
        body = payload["result"]
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])
        assert exit_code == 0
        assert payload["ok"] is True
        assert body["policy_status"] == "blocked_approval_not_approved"
        assert body["approval_decision_accepted"] is False
        assert body["approval_consumed"] is False
        assert body["approval_decision_written"] is False
        assert body["idempotency_marker_written"] is False
        assert body["browser_launch_attempted"] is False
        assert body["cdp_connection_attempted"] is False
        assert body["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_runtime_browser_cdp_approval_decision_consumer_design_cli_is_read_only(capsys) -> None:
    root = _workspace_test_root("cdp_approval_decision_consumer_design_cli")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        exit_code = cli.main(
            [
                "runtime",
                "browser-cdp",
                "approval-decision-consumer-design",
                "http://127.0.0.1:4173",
                "--runtime",
                "Codex",
                "--gate-approval-id",
                result["gate_approval_id"],
                "--vault-root",
                str(root),
                "--json",
            ]
        )

        payload = json.loads(capsys.readouterr().out)
        body = payload["result"]
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])
        assert exit_code == 0
        assert payload["ok"] is True
        assert body["consumer_design_status"] == "blocked_approval_not_approved"
        assert body["consumer_status"] == "not_built"
        assert body["approval_consumed"] is False
        assert body["approval_decision_written"] is False
        assert body["idempotency_marker_written"] is False
        assert body["browser_launch_attempted"] is False
        assert body["cdp_connection_attempted"] is False
        assert body["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_runtime_browser_cdp_atomic_marker_writer_design_cli_is_read_only(capsys) -> None:
    root = _workspace_test_root("cdp_atomic_marker_writer_design_cli")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        exit_code = cli.main(
            [
                "runtime",
                "browser-cdp",
                "atomic-marker-writer-design",
                "http://127.0.0.1:4173",
                "--runtime",
                "Codex",
                "--gate-approval-id",
                result["gate_approval_id"],
                "--vault-root",
                str(root),
                "--json",
            ]
        )

        payload = json.loads(capsys.readouterr().out)
        body = payload["result"]
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])
        assert exit_code == 0
        assert payload["ok"] is True
        assert body["writer_design_status"] == "blocked_approval_not_approved"
        assert body["writer_status"] == "not_built"
        assert body["approval_consumed"] is False
        assert body["approval_decision_written"] is False
        assert body["idempotency_marker_written"] is False
        assert body["marker_directory_created"] is False
        assert body["browser_launch_attempted"] is False
        assert body["cdp_connection_attempted"] is False
        assert body["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _workspace_test_root(name: str) -> Path:
    root = Path(__file__).resolve().parent / f"_test_{name}"
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


class _VincisOSProductUITestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler method name
        body = b"<html><body><main data-chaseos-safe-mode='true'>VincisOS product UI</main></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


@contextmanager
def _local_vincisos_product_ui_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _VincisOSProductUITestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_vincisos_preflight_blocks_without_explicit_local_target() -> None:
    result = evaluate_vincisos_browser_preflight()
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert result.status == "blocked_vincisos_browser_preflight"
    assert "vincisos_target_url_missing" in blocker_ids
    assert result.future_shadow_test_ready is False
    assert result.browser_launch_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.credentials_read is False
    assert result.skill_activation_attempted is False
    assert result.canonical_writeback_attempted is False


def test_vincisos_preflight_accepts_local_declared_shadow_target_without_execution() -> None:
    request = VincisOSBrowserPreflightRequest(target_url="http://127.0.0.1:4173")

    result = evaluate_vincisos_browser_preflight(request)

    assert result.ok is True
    assert result.status == "ready_for_future_vincisos_shadow_browser_test_no_execution"
    assert result.future_shadow_test_ready is True
    assert result.checks["url_is_local"] is True
    assert result.checks["target_port_declared"] is True
    assert result.checks["browser_execution_allowed_by_this_preflight"] is False
    assert result.browser_launch_attempted is False
    assert result.screenshot_attempted is False


def test_vincisos_preflight_blocks_remote_target_and_forbidden_authority() -> None:
    request = VincisOSBrowserPreflightRequest(
        target_url="https://example.com:443",
        allow_real_profile=True,
        allow_credentials=True,
        allow_cdp=True,
        allow_canonical_writeback=True,
        allow_skill_activation=True,
    )

    result = evaluate_vincisos_browser_preflight(request)
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert "target_host_not_local_allowlisted" in blocker_ids
    assert "real_profile_forbidden" in blocker_ids
    assert "credentials_forbidden" in blocker_ids
    assert "cdp_execution_forbidden" in blocker_ids
    assert "canonical_writeback_forbidden" in blocker_ids
    assert "skill_activation_forbidden" in blocker_ids
    assert result.future_shadow_test_ready is False


def test_vincisos_static_target_preflight_runs_local_server_without_browser() -> None:
    result = run_vincisos_static_target_preflight()

    assert TARGET_FILE.exists()
    assert result.ok is True
    assert result.status == "static_target_preflight_ready_no_browser"
    assert result.target_url is not None
    assert result.target_url.startswith("http://127.0.0.1:")
    assert result.server_started is True
    assert result.server_stopped is True
    assert result.browser_launch_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.screenshot_attempted is False
    assert result.trusted_write_attempted is False
    assert result.canonical_writeback_attempted is False
    assert result.preflight is not None
    assert result.preflight["ok"] is True
    assert result.preflight["checks"]["local_socket_reachable"] is True


def test_vincisos_full_ui_preflight_blocks_without_explicit_target_and_safe_mode() -> None:
    result = evaluate_vincisos_full_ui_safe_mode_preflight()
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert result.status == "blocked_vincisos_full_ui_safe_mode_preflight"
    assert "full_ui_target_url_missing" in blocker_ids
    assert "safe_mode_not_asserted" in blocker_ids
    assert result.future_full_ui_shadow_proof_ready is False
    assert result.browser_launch_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.screenshot_attempted is False
    assert result.trusted_skill_write_attempted is False
    assert result.canonical_writeback_attempted is False


def test_vincisos_full_ui_preflight_blocks_static_fixture_even_with_safe_mode() -> None:
    request = VincisOSFullUISafeModePreflightRequest(
        target_url="http://127.0.0.1:63479/vincisos_shadow.html",
        safe_mode_asserted=True,
    )

    result = evaluate_vincisos_full_ui_safe_mode_preflight(request)
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert "static_fixture_is_not_product_ui" in blocker_ids
    assert result.checks["static_fixture_detected"] is True
    assert result.future_full_ui_shadow_proof_ready is False
    assert result.browser_launch_attempted is False


def test_vincisos_full_ui_preflight_accepts_local_product_ui_safe_mode_without_execution() -> None:
    request = VincisOSFullUISafeModePreflightRequest(
        target_url="http://127.0.0.1:5173/",
        safe_mode_asserted=True,
    )

    result = evaluate_vincisos_full_ui_safe_mode_preflight(request)

    assert result.ok is True
    assert result.status == "ready_for_future_vincisos_full_ui_shadow_proof_no_execution"
    assert result.future_full_ui_shadow_proof_ready is True
    assert result.checks["url_is_local"] is True
    assert result.checks["target_port_declared"] is True
    assert result.checks["browser_execution_allowed_by_this_preflight"] is False
    assert result.browser_launch_attempted is False
    assert result.screenshot_attempted is False


def test_vincisos_full_ui_preflight_blocks_remote_target_and_forbidden_authority() -> None:
    request = VincisOSFullUISafeModePreflightRequest(
        target_url="https://example.com:443",
        safe_mode_asserted=True,
        allow_real_profile=True,
        allow_credentials=True,
        allow_cdp=True,
        allow_browser_harness=True,
        allow_browser_use_cli_live=True,
        allow_trusted_skill_write=True,
        allow_skill_activation=True,
        allow_agent_bus_enqueue=True,
        allow_provider_call=True,
        allow_gate_mutation=True,
        allow_canonical_writeback=True,
    )

    result = evaluate_vincisos_full_ui_safe_mode_preflight(request)
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert "target_host_not_local_allowlisted" in blocker_ids
    assert "real_profile_forbidden" in blocker_ids
    assert "credentials_forbidden" in blocker_ids
    assert "cdp_execution_forbidden" in blocker_ids
    assert "browser_harness_forbidden" in blocker_ids
    assert "browser_use_cli_live_forbidden" in blocker_ids
    assert "trusted_skill_write_forbidden" in blocker_ids
    assert "skill_activation_forbidden" in blocker_ids
    assert "agent_bus_enqueue_forbidden" in blocker_ids
    assert "provider_call_forbidden" in blocker_ids
    assert "gate_mutation_forbidden" in blocker_ids
    assert "canonical_writeback_forbidden" in blocker_ids
    assert result.browser_launch_attempted is False
    assert result.provider_call_attempted is False


def _valid_vincisos_full_ui_target_contract() -> dict[str, object]:
    return {
        "contract_version": "vincisos.full_ui_target.v1",
        "target_name": "VincisOS local product UI safe-mode target",
        "target_url": "http://127.0.0.1:5173/",
        "target_kind": "product_ui",
        "mode": "shadow",
        "safe_mode_asserted": True,
        "safe_mode_evidence": [
            "Local development server declared by operator for future safe-mode browser proof.",
        ],
        "allowed_hosts": ["127.0.0.1", "localhost"],
        "allowed_actions": ["open", "read_state", "capture_screenshot", "harmless_click", "close"],
        "expected_artifacts": ["browser_run_log", "agent_activity_log", "screenshot", "draft_skill_candidate"],
        "draft_only": True,
        "require_running_target": False,
        "probe_reachability": False,
        "forbidden_authority": {flag: False for flag in FORBIDDEN_AUTHORITY_FLAGS},
    }


def test_vincisos_full_ui_target_contract_blocks_missing_contract_without_execution() -> None:
    result = evaluate_vincisos_full_ui_target_contract(None)
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert result.status == "blocked_vincisos_full_ui_target_contract"
    assert "target_contract_missing" in blocker_ids
    assert "contract_version_invalid" in blocker_ids
    assert result.future_full_ui_shadow_proof_ready is False
    assert result.browser_launch_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.screenshot_attempted is False
    assert result.files_modified is False


def test_vincisos_full_ui_target_contract_accepts_safe_local_product_ui_without_execution() -> None:
    result = evaluate_vincisos_full_ui_target_contract(_valid_vincisos_full_ui_target_contract())

    assert result.ok is True
    assert result.status == "vincisos_full_ui_target_contract_ready_no_execution"
    assert result.future_full_ui_shadow_proof_ready is True
    assert result.preflight["ok"] is True
    assert result.checks["browser_execution_allowed_by_this_contract"] is False
    assert result.checks["allowed_hosts_local_only"] is True
    assert result.browser_launch_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.screenshot_attempted is False
    assert result.trusted_skill_write_attempted is False
    assert result.canonical_writeback_attempted is False
    assert result.files_modified is False


def test_vincisos_full_ui_target_contract_blocks_static_fixture_even_if_declared() -> None:
    contract = _valid_vincisos_full_ui_target_contract()
    contract["target_url"] = "http://127.0.0.1:63479/vincisos_shadow.html"

    result = evaluate_vincisos_full_ui_target_contract(contract)
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert "static_fixture_is_not_product_ui" in blocker_ids
    assert result.preflight["checks"]["static_fixture_detected"] is True
    assert result.future_full_ui_shadow_proof_ready is False
    assert result.browser_launch_attempted is False
    assert result.files_modified is False


def test_vincisos_full_ui_target_contract_blocks_forbidden_authority_and_unknown_actions() -> None:
    contract = _valid_vincisos_full_ui_target_contract()
    contract["allowed_hosts"] = ["127.0.0.1", "example.com"]
    contract["allowed_actions"] = ["open", "read_state", "runtime_eval"]
    contract["expected_artifacts"] = ["browser_run_log"]
    forbidden = dict(contract["forbidden_authority"])  # type: ignore[arg-type]
    forbidden["allow_credentials"] = True
    forbidden["allow_cdp"] = True
    forbidden["allow_canonical_writeback"] = True
    contract["forbidden_authority"] = forbidden

    result = evaluate_vincisos_full_ui_target_contract(contract)
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert "allowed_hosts_not_local_only" in blocker_ids
    assert "allowed_actions_unknown" in blocker_ids
    assert "allowed_actions_minimum_missing" in blocker_ids
    assert "expected_artifacts_missing" in blocker_ids
    assert "allow_credentials_forbidden" in blocker_ids
    assert "allow_cdp_forbidden" in blocker_ids
    assert "allow_canonical_writeback_forbidden" in blocker_ids
    assert result.browser_launch_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.canonical_writeback_attempted is False
    assert result.files_modified is False


def test_vincisos_full_ui_target_contract_file_loader_blocks_invalid_json_without_writes() -> None:
    root = _workspace_test_root("vincisos_contract_invalid_json")
    try:
        contract_path = root / "invalid-contract.json"
        contract_path.write_text("{not-json", encoding="utf-8")

        result = evaluate_vincisos_full_ui_target_contract_file(contract_path)
        blocker_ids = {item["blocker_id"] for item in result.blockers}

        assert result.ok is False
        assert result.status == "blocked_vincisos_full_ui_target_contract"
        assert "target_contract_json_invalid" in blocker_ids
        assert result.browser_launch_attempted is False
        assert result.files_modified is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_vincisos_contract_backed_proof_plan_ready_for_valid_contract_without_execution() -> None:
    result = build_vincisos_contract_backed_proof_plan(
        _valid_vincisos_full_ui_target_contract(),
        run_id="VincisOS Full UI Proof",
    )
    artifacts = {item["artifact_type"]: item for item in result.artifact_plan}
    actions = [item["action"] for item in result.action_plan]

    assert result.ok is True
    assert result.status == "vincisos_contract_backed_proof_plan_ready_no_execution"
    assert result.proof_plan_version == PROOF_PLAN_VERSION
    assert result.run_id == "vincisos-full-ui-proof"
    assert result.contract_validation["ok"] is True
    assert actions == [
        "validate_contract",
        "open",
        "read_state",
        "capture_screenshot",
        "harmless_click",
        "write_draft_evidence",
    ]
    assert artifacts["browser_run_log"]["path"] == "07_LOGS/Browser-Runs/vincisos-full-ui-proof.json"
    assert artifacts["agent_activity_log"]["path"] == "07_LOGS/Agent-Activity/vincisos-full-ui-proof.md"
    assert artifacts["screenshot"]["path"] == "07_LOGS/Browser-Runs/vincisos-full-ui-proof_screenshot.png"
    assert artifacts["draft_site_skill"]["activation_allowed"] is False
    assert artifacts["untrusted_skill_candidate"]["activation_allowed"] is False
    assert result.security_constraints["real_profile_allowed"] is False
    assert result.security_constraints["canonical_writeback_allowed"] is False
    assert result.browser_launch_attempted is False
    assert result.screenshot_attempted is False
    assert result.files_modified is False


def test_vincisos_contract_backed_proof_plan_blocks_static_fixture_contract() -> None:
    contract = _valid_vincisos_full_ui_target_contract()
    contract["target_url"] = "http://127.0.0.1:63479/vincisos_shadow.html"

    result = build_vincisos_contract_backed_proof_plan(contract)
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert result.status == "blocked_vincisos_contract_backed_proof_plan"
    assert "target_contract_not_ready" in blocker_ids
    assert "static_fixture_is_not_product_ui" in blocker_ids
    assert result.contract_validation["ok"] is False
    assert result.browser_launch_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.files_modified is False


def test_vincisos_contract_backed_proof_plan_from_file_blocks_invalid_json() -> None:
    root = _workspace_test_root("vincisos_proof_plan_invalid_json")
    try:
        contract_path = root / "invalid-contract.json"
        contract_path.write_text("{not-json", encoding="utf-8")

        result = build_vincisos_contract_backed_proof_plan_from_file(contract_path)
        blocker_ids = {item["blocker_id"] for item in result.blockers}

        assert result.ok is False
        assert result.status == "blocked_vincisos_contract_backed_proof_plan"
        assert "target_contract_not_ready" in blocker_ids
        assert "target_contract_json_invalid" in blocker_ids
        assert result.browser_launch_attempted is False
        assert result.files_modified is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_vincisos_product_ui_target_probe_reports_local_target_available_without_browser() -> None:
    with _local_vincisos_product_ui_server() as target_url:
        contract = _valid_vincisos_full_ui_target_contract()
        contract["target_url"] = target_url

        result = probe_vincisos_product_ui_target(contract, timeout_seconds=1.0)

    assert result.ok is True
    assert result.status == "vincisos_product_ui_target_available_no_browser"
    assert result.probe_version == PROBE_VERSION
    assert result.checks["contract_ready"] is True
    assert result.checks["local_http_probe_only"] is True
    assert result.checks["http_probe_attempted"] is True
    assert result.checks["http_reachable"] is True
    assert result.checks["browser_execution_allowed_by_this_probe"] is False
    assert result.browser_launch_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.screenshot_attempted is False
    assert result.profile_access_attempted is False
    assert result.credentials_read is False
    assert result.cookie_or_session_read is False
    assert result.canonical_writeback_attempted is False
    assert result.files_modified is False


def test_vincisos_product_ui_target_probe_blocks_unreachable_target_without_browser() -> None:
    contract = _valid_vincisos_full_ui_target_contract()
    contract["target_url"] = "http://127.0.0.1:9/"

    result = probe_vincisos_product_ui_target(contract, timeout_seconds=0.2)
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert result.status == "blocked_vincisos_product_ui_target_availability"
    assert "local_product_ui_target_unreachable" in blocker_ids
    assert result.contract_validation["ok"] is True
    assert result.checks["http_probe_attempted"] is True
    assert result.checks["http_reachable"] is False
    assert result.browser_launch_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.files_modified is False


def test_vincisos_product_ui_target_probe_blocks_static_fixture_contract_without_http_probe() -> None:
    contract = _valid_vincisos_full_ui_target_contract()
    contract["target_url"] = "http://127.0.0.1:63479/vincisos_shadow.html"

    result = probe_vincisos_product_ui_target(contract, timeout_seconds=0.2)
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert "target_contract_not_ready" in blocker_ids
    assert "static_fixture_is_not_product_ui" in blocker_ids
    assert result.checks["http_probe_attempted"] is False
    assert result.browser_launch_attempted is False
    assert result.files_modified is False


def test_vincisos_product_ui_target_probe_from_file_blocks_invalid_json_without_writes() -> None:
    root = _workspace_test_root("vincisos_product_target_probe_invalid_json")
    try:
        contract_path = root / "invalid-contract.json"
        contract_path.write_text("{not-json", encoding="utf-8")

        result = probe_vincisos_product_ui_target_file(contract_path, timeout_seconds=0.2)
        blocker_ids = {item["blocker_id"] for item in result.blockers}

        assert result.ok is False
        assert result.status == "blocked_vincisos_product_ui_target_availability"
        assert "target_contract_not_ready" in blocker_ids
        assert "target_contract_json_invalid" in blocker_ids
        assert result.checks["http_probe_attempted"] is False
        assert result.browser_launch_attempted is False
        assert result.files_modified is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _valid_vincisos_launch_app() -> dict[str, object]:
    return {
        "id": "vincisos-product-ui",
        "title": "VincisOS Product UI",
        "summary": "Local safe-mode browser-runtime-product-target app.",
        "module": "runtime.vincisos.product_ui_app",
        "default_host": "127.0.0.1",
        "default_port": 5173,
        "default_url": "http://127.0.0.1:5173/",
        "health_path": "/health.json",
        "local_only": True,
        "read_only": True,
        "write_capable": False,
        "starts_workflows": False,
        "operator_launch": {
            "execution_mode": "operator_terminal_only",
            "launcher_executes": False,
            "browser_auto_open": False,
            "default_url": "http://127.0.0.1:5173/",
            "health_url": "http://127.0.0.1:5173/health.json",
        },
        "runtime_status": {
            "checked": True,
            "state": "offline",
            "starts_child_app": False,
            "read_only_probe": True,
        },
    }


def test_vincisos_product_ui_launch_readiness_blocks_when_no_product_app_registered(tmp_path: Path) -> None:
    result = build_vincisos_product_ui_launch_readiness(
        tmp_path,
        apps=[
            {
                "id": "studio-dashboard-app",
                "title": "Studio Dashboard",
                "default_host": "127.0.0.1",
                "default_port": 8768,
                "local_only": True,
                "operator_launch": {"launcher_executes": False, "browser_auto_open": False},
                "runtime_status": {"starts_child_app": False, "read_only_probe": True},
            }
        ],
    )
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert result.status == "blocked_vincisos_product_ui_launch_readiness"
    assert "vincisos_product_ui_launch_target_not_registered" in blocker_ids
    assert result.checks["launch_readiness_only"] is True
    assert result.starts_server_attempted is False
    assert result.shell_command_attempted is False
    assert result.browser_launch_attempted is False
    assert result.cdp_connection_attempted is False
    assert result.files_modified is False


def test_vincisos_product_ui_launch_readiness_accepts_registered_local_target_without_starting() -> None:
    result = build_vincisos_product_ui_launch_readiness(
        apps=[_valid_vincisos_launch_app()],
    )

    assert result.ok is True
    assert result.status == "vincisos_product_ui_launch_target_ready_no_start"
    assert result.readiness_version == READINESS_VERSION
    assert result.checks["candidate_app_count"] == 1
    assert result.checks["starts_server_allowed_by_this_check"] is False
    assert result.starts_server_attempted is False
    assert result.shell_command_attempted is False
    assert result.browser_launch_attempted is False
    assert result.profile_access_attempted is False
    assert result.credentials_read is False
    assert result.cookie_or_session_read is False
    assert result.canonical_writeback_attempted is False
    assert result.files_modified is False


def test_vincisos_product_ui_launch_readiness_blocks_unsafe_candidate() -> None:
    app = _valid_vincisos_launch_app()
    app["local_only"] = False
    app["default_host"] = "0.0.0.0"
    app["starts_workflows"] = True
    operator_launch = dict(app["operator_launch"])  # type: ignore[arg-type]
    operator_launch["launcher_executes"] = True
    operator_launch["browser_auto_open"] = True
    app["operator_launch"] = operator_launch

    result = build_vincisos_product_ui_launch_readiness(apps=[app])
    blocker_ids = {item["blocker_id"] for item in result.blockers}

    assert result.ok is False
    assert result.status == "blocked_vincisos_product_ui_launch_readiness"
    assert "vincisos-product-ui_not_local_only" in blocker_ids
    assert "vincisos-product-ui_host_not_loopback" in blocker_ids
    assert "vincisos-product-ui_launcher_executes" in blocker_ids
    assert "vincisos-product-ui_browser_auto_open" in blocker_ids
    assert "vincisos-product-ui_starts_workflows" in blocker_ids
    assert result.starts_server_attempted is False
    assert result.browser_launch_attempted is False
    assert result.files_modified is False


def test_cdp_read_only_closeout_readiness_reports_feature_implemented() -> None:
    root = _workspace_test_root("cdp_closeout_readiness")
    try:
        result = build_cdp_read_only_closeout_readiness_report(
            vault_root=root,
            target_url="http://127.0.0.1:4173",
            runtime="Hermes",
            gate_approval_id="gate-closeout-readiness",
        )
        assert result["ok"] is True
        assert result["pre_execution_governance_thread_closeable"] is True
        assert result["feature_closed_for_live_execution"] is True
        assert result["operational_activation_status"] == "activation_evidence_missing"
        assert result["local_environment_smoke_passed"] is False
        assert result["execution_enabled"] is False
        assert result["browser_launch_attempted"] is False
        assert result["cdp_connection_attempted"] is False
        assert result["approval_consumed"] is False
        assert result["approval_decision_written"] is False
        assert result["idempotency_marker_written"] is False
        assert result["files_modified"] is False
        surfaces = {item["surface"] for item in result["verified_no_execution_surfaces"]}
        assert "approval-decision-consumer-design" in surfaces
        assert "atomic-marker-writer-design" in surfaces
        assert "browser-cdp-execute" in surfaces
        assert "closeout-readiness" in surfaces
        assert "local_chromium_executable_not_configured_for_smoke" in result["implementation_blockers"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_closeout_readiness_reports_operational_activation_from_build_log() -> None:
    root = _workspace_test_root("cdp_closeout_readiness_activated")
    try:
        evidence_path = (
            root
            / "07_LOGS"
            / "Build-Logs"
            / "2026-05-02-ChaseOS-hermes-browser-cdp-operational-environment-activation.md"
        )
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(
            "\n".join(
                [
                    "status: implemented_cdp_read_only_proof_complete",
                    "approval_consumed: True",
                    "idempotency_marker_written: True",
                    "browser_launch_attempted: True",
                    "cdp_connection_attempted: True",
                    "screenshot_attempted: True",
                    "dom_snapshot_attempted: True",
                ]
            ),
            encoding="utf-8",
        )

        result = build_cdp_read_only_closeout_readiness_report(
            vault_root=root,
            target_url="http://127.0.0.1:4173",
            runtime="Hermes",
            gate_approval_id="gate-closeout-readiness-activated",
        )

        assert result["closeout_status"] == "browser_cdp_bounded_read_only_proof_implemented_and_operationally_activated"
        assert result["operational_activation_status"] == "activated_for_bounded_read_only_proof"
        assert result["local_environment_smoke_passed"] is True
        assert result["implementation_blockers"] == []
        assert result["operational_activation_evidence"]["operationally_activated"] is True
        assert result["operational_activation_evidence"]["browser_launch_attempted_by_check"] is False
        assert result["browser_launch_attempted"] is False
        assert result["cdp_connection_attempted"] is False
        assert result["approval_consumed"] is False
        assert result["files_modified"] is False
        surfaces = {item["surface"]: item["status"] for item in result["verified_no_execution_surfaces"]}
        assert surfaces["closeout-readiness"] == "verified_feature_implemented_operationally_activated"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_runtime_browser_cdp_closeout_readiness_cli_is_read_only(capsys) -> None:
    root = _workspace_test_root("cdp_closeout_readiness_cli")
    try:
        result = cli.main([
            "runtime",
            "--vault-root",
            str(root),
            "browser-cdp",
            "closeout-readiness",
            "http://127.0.0.1:4173",
            "--runtime",
            "Hermes",
            "--gate-approval-id",
            "gate-closeout-readiness-cli",
            "--json",
        ])
        assert result == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["result"]["pre_execution_governance_thread_closeable"] is True
        assert payload["result"]["feature_closed_for_live_execution"] is True
        assert payload["result"]["operational_activation_status"] == "activation_evidence_missing"
        assert payload["result"]["local_environment_smoke_passed"] is False
        assert payload["result"]["execution_enabled"] is False
        assert payload["result"]["browser_launch_attempted"] is False
        assert payload["result"]["cdp_connection_attempted"] is False
        assert payload["result"]["approval_consumed"] is False
        assert payload["result"]["idempotency_marker_written"] is False
        assert not (root / "07_LOGS" / "Agent-Activity" / "_bosl_cdp_approvals" / "_execution_markers").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_isolated_browser_launcher_design_is_no_launch_and_pending_blocked() -> None:
    root = _workspace_test_root("cdp_isolated_launcher_design")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        payload = build_cdp_read_only_isolated_browser_launcher_design(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
        )
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])

        assert payload["ok"] is True
        assert payload["launcher_design_status"] == "blocked_approval_not_approved"
        assert payload["launcher_status"] == "not_built"
        assert payload["launch_strategy"] == "chaseos_launch_isolated"
        assert payload["browser_profile_policy"] == "throwaway_only"
        assert payload["launcher_contract"]["attach_to_existing_browser_allowed"] is False
        assert payload["launcher_contract"]["real_profile_allowed"] is False
        assert payload["launcher_contract"]["debugging_address"] == "127.0.0.1"
        assert "--remote-debugging-address=127.0.0.1" in payload["required_launch_arguments"]
        assert "--remote-debugging-address=0.0.0.0" in payload["forbidden_launch_arguments"]
        assert "user_data_dir" in payload["forbidden_launcher_fields"]
        assert payload["browser_launch_attempted"] is False
        assert payload["browser_process_spawned"] is False
        assert payload["throwaway_profile_created"] is False
        assert payload["cdp_port_opened"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_runtime_browser_cdp_isolated_browser_launcher_design_cli_is_read_only(capsys) -> None:
    root = _workspace_test_root("cdp_isolated_launcher_design_cli")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        exit_code = cli.main([
            "runtime",
            "--vault-root",
            str(root),
            "browser-cdp",
            "isolated-browser-launcher-design",
            "http://127.0.0.1:4173",
            "--runtime",
            "Codex",
            "--gate-approval-id",
            result["gate_approval_id"],
            "--json",
        ])
        payload = json.loads(capsys.readouterr().out)
        body = payload["result"]

        assert exit_code == 0
        assert payload["ok"] is True
        assert body["launcher_design_status"] == "blocked_approval_not_approved"
        assert body["launcher_status"] == "not_built"
        assert body["browser_launch_attempted"] is False
        assert body["browser_process_spawned"] is False
        assert body["throwaway_profile_created"] is False
        assert body["cdp_port_opened"] is False
        assert body["cdp_connection_attempted"] is False
        assert body["files_modified"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_isolated_launcher_implementation_preflight_blocks_missing_metadata_without_launch() -> None:
    root = _workspace_test_root("cdp_isolated_launcher_preflight")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        payload = build_cdp_read_only_isolated_launcher_implementation_preflight(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
        )
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])

        assert payload["ok"] is True
        assert payload["preflight_status"] == "blocked_approval_not_approved"
        assert payload["launcher_implementation_status"] == "implemented_code_path_environment_unverified"
        assert payload["implementation_patch_ready"] is False
        assert "browser_cdp_launcher_executable_ref_missing" in payload["blocked_reasons"]
        assert "browser_cdp_default_client_binding_missing" in payload["blocked_reasons"]
        assert payload["live_code_status"]["launcher_code_available"] is True
        assert payload["live_code_status"]["cdp_client_code_available"] is True
        assert payload["proposed_launcher_refs"]["raw_refs_logged"] is False
        assert payload["browser_launch_attempted"] is False
        assert payload["browser_process_spawned"] is False
        assert payload["throwaway_profile_created"] is False
        assert payload["cdp_port_opened"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_isolated_launcher_implementation_preflight_ready_with_opaque_refs_no_execution() -> None:
    root = _workspace_test_root("cdp_isolated_launcher_preflight_ready")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        write_cdp_read_only_approval_decision(
            root,
            result["gate_approval_id"],
            approved_by="tester",
            decision_status="approved",
        )
        payload = build_cdp_read_only_isolated_launcher_implementation_preflight(
            root,
            result["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            browser_executable_ref="chaseos-managed://chromium/stable",
            profile_parent_ref="chaseos-temp://browser-cdp/profiles",
            port_allocation_strategy="allocate_unused_loopback_port",
            process_runner_policy="bounded_spawn_no_shell",
            cleanup_strategy="close_then_delete_throwaway_profile",
            cdp_client_binding_ref="runtime.browser_runtime.cdp_client.LocalReadOnlyCDPClient",
        )
        marker_path = cdp_read_only_idempotency_marker_path(root, result["gate_approval_id"])

        assert payload["preflight_status"] == "ready_for_launcher_implementation_patch_no_execution"
        assert payload["implementation_patch_ready"] is True
        assert payload["execution_enabled"] is False
        assert payload["proposed_launcher_refs"]["browser_executable_ref_allowed"] is True
        assert payload["proposed_launcher_refs"]["profile_parent_ref_allowed"] is True
        assert payload["proposed_launcher_refs"]["cdp_client_binding_ref_allowed"] is True
        assert payload["browser_launch_attempted"] is False
        assert payload["browser_process_spawned"] is False
        assert payload["throwaway_profile_created"] is False
        assert payload["cdp_port_opened"] is False
        assert payload["cdp_connection_attempted"] is False
        assert payload["files_modified"] is False
        assert marker_path.exists() is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_runtime_browser_cdp_isolated_launcher_implementation_preflight_cli_is_read_only(capsys) -> None:
    root = _workspace_test_root("cdp_isolated_launcher_preflight_cli")
    try:
        result = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Codex",
            requested_by="tester",
        )
        exit_code = cli.main([
            "runtime",
            "--vault-root",
            str(root),
            "browser-cdp",
            "isolated-launcher-implementation-preflight",
            "http://127.0.0.1:4173",
            "--runtime",
            "Codex",
            "--gate-approval-id",
            result["gate_approval_id"],
            "--json",
        ])
        payload = json.loads(capsys.readouterr().out)
        body = payload["result"]

        assert exit_code == 0
        assert payload["ok"] is True
        assert body["preflight_status"] == "blocked_approval_not_approved"
        assert body["launcher_implementation_status"] == "implemented_code_path_environment_unverified"
        assert body["implementation_patch_ready"] is False
        assert body["browser_launch_attempted"] is False
        assert body["browser_process_spawned"] is False
        assert body["throwaway_profile_created"] is False
        assert body["cdp_port_opened"] is False
        assert body["cdp_connection_attempted"] is False
        assert body["files_modified"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


class _FakeCDPLauncher:
    def __init__(self):
        self.launched = False
        self.closed = False

    def launch(self):
        self.launched = True
        return {"cdp_endpoint": "http://127.0.0.1:9222", "browser_pid": 12345, "user_data_dir": "[REDACTED]"}

    def close(self):
        self.closed = True


class _FakeCDPClient:
    def __init__(self):
        self.connected = False
        self.navigated_to = None

    def connect(self, endpoint: str):
        self.connected = True
        self.endpoint = endpoint

    def navigate(self, target_url: str):
        self.navigated_to = target_url

    def read_state(self):
        return {
            "title": "Local Test Page",
            "url": "http://127.0.0.1:4173",
            "visible_text": "Hello from local test",
            "dom_snapshot": {"nodes": [{"nodeName": "BODY", "text": "Hello from local test"}]},
        }

    def capture_screenshot(self) -> bytes:
        return b"fake-png-bytes"

    def close(self):
        self.connected = False


def test_cdp_read_only_proof_executor_consumes_approval_writes_marker_and_artifacts() -> None:
    root = _workspace_test_root("cdp_live_executor_fake")
    try:
        request = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Hermes",
            requested_by="tester",
        )
        decision = write_cdp_read_only_approval_decision(
            root,
            request["gate_approval_id"],
            approved_by="operator",
        )
        assert decision["approval_decision_written"] is True

        launcher = _FakeCDPLauncher()
        client = _FakeCDPClient()
        result = execute_cdp_read_only_proof(
            root,
            request["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Hermes",
            launcher=launcher,
            cdp_client=client,
        )

        assert result["ok"] is True
        assert result["executor_status"] == "implemented"
        assert result["approval_consumed"] is True
        assert result["approval_decision_written"] is False
        assert result["idempotency_marker_written"] is True
        assert result["browser_launch_attempted"] is True
        assert result["cdp_connection_attempted"] is True
        assert result["screenshot_attempted"] is True
        assert result["dom_snapshot_attempted"] is True
        assert result["credential_value_read"] is False
        assert result["cookie_or_session_read"] is False
        assert result["real_profile_used"] is False
        assert result["trusted_skill_written"] is False
        assert result["canonical_files_mutated"] is False
        assert result["agent_bus_task_enqueued"] is False
        assert result["provider_call_attempted"] is False
        assert launcher.launched is True
        assert launcher.closed is True
        assert client.navigated_to == "http://127.0.0.1:4173"
        assert Path(result["idempotency_marker_ref"]).exists()
        assert Path(result["consumption_ref"]).exists()
        assert Path(result["browser_run_log_path"]).exists()
        assert Path(result["agent_activity_log_path"]).exists()
        assert Path(result["screenshot_path"]).exists()
        assert Path(result["dom_snapshot_path"]).exists()
        assert Path(result["screenshot_path"]).read_bytes() == b"fake-png-bytes"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cdp_read_only_proof_executor_blocks_duplicate_marker_reuse() -> None:
    root = _workspace_test_root("cdp_live_executor_duplicate")
    try:
        request = write_cdp_read_only_approval_request(
            root,
            target_url="http://127.0.0.1:4173",
            runtime="Hermes",
            requested_by="tester",
        )
        write_cdp_read_only_approval_decision(root, request["gate_approval_id"], approved_by="operator")
        first = execute_cdp_read_only_proof(
            root,
            request["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Hermes",
            launcher=_FakeCDPLauncher(),
            cdp_client=_FakeCDPClient(),
        )
        assert first["ok"] is True
        second = execute_cdp_read_only_proof(
            root,
            request["gate_approval_id"],
            target_url="http://127.0.0.1:4173",
            runtime="Hermes",
            launcher=_FakeCDPLauncher(),
            cdp_client=_FakeCDPClient(),
        )
        assert second["ok"] is False
        assert second["status"] == "blocked_prior_cdp_proof_marker_exists"
        assert second["browser_launch_attempted"] is False
        assert second["cdp_connection_attempted"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_minimal_cdp_client_uses_put_to_create_page_target(monkeypatch):
    from runtime.browser_runtime import cdp_live

    captured = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"webSocketDebuggerUrl":"ws://127.0.0.1:9222/devtools/page/test"}'

    def fake_urlopen(request, timeout=None):
        captured["method"] = request.get_method()
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(cdp_live.urllib.request, "urlopen", fake_urlopen)
    client = cdp_live.MinimalCDPClient(timeout_seconds=3)
    client.endpoint = "http://127.0.0.1:9222"

    target = client._open_or_create_page_target()

    assert captured["method"] == "PUT"
    assert captured["url"].endswith("/json/new?about:blank")
    assert captured["timeout"] == 3
    assert target["webSocketDebuggerUrl"].startswith("ws://127.0.0.1")
