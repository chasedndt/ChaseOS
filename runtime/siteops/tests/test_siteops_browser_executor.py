"""Tests for runtime.siteops.browser_executor — SiteOps-owned Playwright executor.

Covers:
  - SiteOpsBrowserExecutor.capture_page() in stub mode (Playwright unavailable)
  - SiteOpsBrowserExecutor.capture_page() with mocked Playwright (live path)
  - capture_and_route() quarantine routing
  - run_siteops_live() end-to-end via executor.py
  - Approval validation (not found, not approved, consumed)
  - Executor kind guard (provider_api raises SiteOpsExecutorNotBuiltError)
  - mark_approval_consumed idempotency
  - AOR handler run_siteops_execute()
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.siteops.browser_executor import (
    SiteOpsBrowserExecutor,
    _reset_playwright_cache,
    capture_and_route,
)
from runtime.siteops.executor import (
    SiteOpsApprovalError,
    SiteOpsExecutorNotBuiltError,
    run_siteops_live,
)
from runtime.siteops.approvals import mark_approval_consumed


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_playwright_cache():
    """Reset Playwright availability cache between tests."""
    _reset_playwright_cache()
    yield
    _reset_playwright_cache()


def _minimal_vault(tmp_path: Path) -> Path:
    """Create a minimal vault structure for SiteOps tests."""
    (tmp_path / "CLAUDE.md").write_text("# test vault\n")
    (tmp_path / "runtime" / "siteops" / "registry" / "sites").mkdir(parents=True)
    (tmp_path / "runtime" / "siteops" / "registry" / "providers").mkdir(parents=True)
    (tmp_path / "runtime" / "siteops" / "registry" / "workflows").mkdir(parents=True)
    (tmp_path / "runtime" / "siteops" / "registry" / "skill_cards").mkdir(parents=True)
    (tmp_path / "07_LOGS" / "SiteOps-Runs").mkdir(parents=True)
    (tmp_path / "07_LOGS" / "SiteOps-Audits").mkdir(parents=True)
    (tmp_path / "07_LOGS" / "SiteOps-Approvals" / "local" / "default").mkdir(parents=True)
    (tmp_path / "03_INPUTS" / "00_QUARANTINE" / "source").mkdir(parents=True)
    (tmp_path / ".chaseos").mkdir(parents=True)

    # Minimal tenant
    (tmp_path / "runtime" / "siteops" / "tenants").mkdir(parents=True)
    tenant = {
        "tenant_id": "local",
        "name": "Local",
        "workspace_ids": ["default"],
        "roles": [{"user_id": "local-user", "roles": ["approver", "operator"]}],
        "site_skill_installations": [
            {
                "installation_id": "inst-tradingview",
                "skill_template_id": "tradingview.capture",
                "default_policy_pack": "siteops_default_v1",
                "risk_level": "low",
                "workflow_template_ids": ["tradingview.idea.capture"],
            }
        ],
        "workflow_installations": [
            {
                "workflow_installation_id": "wf-tradingview-idea",
                "workflow_template_id": "tradingview.idea.capture",
                "provider_account_binding": None,
                "browser_profile_binding": None,
            }
        ],
        "credential_refs": [],
        "browser_profile_refs": [],
        "provider_account_bindings": [],
        "budget_policies": [],
    }
    (tmp_path / "runtime" / "siteops" / "tenants" / "local.yaml").write_text(
        "tenant_id: local\nname: Local\nworkspace_ids: [default]\nroles:\n  - user_id: local-user\n    roles: [approver, operator]\n"
        "site_skill_installations:\n  - installation_id: inst-tradingview\n    skill_template_id: tradingview.capture\n    default_policy_pack: siteops_default_v1\n    risk_level: low\n    workflow_template_ids: [tradingview.idea.capture]\n"
        "workflow_installations:\n  - workflow_installation_id: wf-tradingview-idea\n    workflow_template_id: tradingview.idea.capture\n    provider_account_binding: null\n    browser_profile_binding: null\n"
        "credential_refs: []\nbrowser_profile_refs: []\nprovider_account_bindings: []\nbudget_policies: []\n"
    )

    # Minimal catalog
    catalog = {
        "site_skill_templates": [
            {
                "skill_template_id": "tradingview.capture",
                "name": "TradingView Capture",
                "workflow_template_ids": ["tradingview.idea.capture"],
            }
        ],
        "workflow_templates": [
            {
                "workflow_template_id": "tradingview.idea.capture",
                "name": "TradingView Idea Capture",
                "executor_kind": "browser",
                "default_target_url": "https://www.tradingview.com/ideas/",
                "site_profile_id": "tradingview",
                "provider_adapter_id": None,
                "inputs_schema": {"required": []},
            }
        ],
        "provider_templates": [],
        "policy_packs": [{"version": "siteops_default_v1", "rules": []}],
    }
    import yaml
    (tmp_path / "runtime" / "siteops" / "catalog").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runtime" / "siteops" / "catalog" / "site_skill_templates.yaml").write_text(
        yaml.dump({"site_skill_templates": catalog["site_skill_templates"]})
    )
    (tmp_path / "runtime" / "siteops" / "catalog" / "workflow_templates.yaml").write_text(
        yaml.dump({"workflow_templates": catalog["workflow_templates"]})
    )
    (tmp_path / "runtime" / "siteops" / "catalog" / "provider_templates.yaml").write_text(
        yaml.dump({"provider_templates": []})
    )
    (tmp_path / "runtime" / "siteops" / "catalog" / "policy_packs.yaml").write_text(
        yaml.dump({"policy_packs": catalog["policy_packs"]})
    )
    return tmp_path


def _write_approval(vault: Path, approval_id: str, status: str = "approved", consumed: bool = False) -> dict:
    record = {
        "approval_id": approval_id,
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "run_id": f"run_{approval_id}",
        "workflow_id": "tradingview.idea.capture",
        "action": "execute",
        "risk_level": "low",
        "approval_reason": "test",
        "requested_by": "local-user",
        "required_approver_role": "approver",
        "status": status,
        "consumed": consumed,
        "metadata": {},
    }
    path = vault / "07_LOGS" / "SiteOps-Approvals" / "local" / "default" / f"{approval_id}.json"
    path.write_text(json.dumps(record, indent=2))
    return record


# ── SiteOpsBrowserExecutor stub mode ─────────────────────────────────────────

class TestBrowserExecutorStubMode:

    def test_stub_when_playwright_not_installed(self, tmp_path):
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=False):
            ex = SiteOpsBrowserExecutor()
            result = ex.capture_page("https://example.com")
        assert result["ok"] is True
        assert result["adapter_mode"] == "stub"
        assert result["is_stub"] is True
        assert result["text"] == ""
        assert result["error"] is None

    def test_playwright_available_property_reflects_state(self):
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=True):
            ex = SiteOpsBrowserExecutor()
            assert ex.playwright_available is True
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=False):
            ex2 = SiteOpsBrowserExecutor()
            assert ex2.playwright_available is False

    def test_invalid_url_returns_error_result(self):
        ex = SiteOpsBrowserExecutor()
        result = ex.capture_page("not-a-url")
        assert result["ok"] is False
        assert "invalid URL" in (result["error"] or "")

    def test_empty_url_returns_error_result(self):
        ex = SiteOpsBrowserExecutor()
        result = ex.capture_page("")
        assert result["ok"] is False

    def test_result_shape_is_complete(self):
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=False):
            ex = SiteOpsBrowserExecutor()
            result = ex.capture_page("https://example.com")
        required_keys = {"ok", "url", "requested_url", "title", "text", "char_count",
                         "adapter_mode", "is_stub", "error"}
        assert required_keys.issubset(result.keys())

    def test_stub_preserves_requested_url(self):
        url = "https://www.tradingview.com/ideas/"
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=False):
            ex = SiteOpsBrowserExecutor()
            result = ex.capture_page(url)
        assert result["requested_url"] == url


# ── SiteOpsBrowserExecutor live mode (mocked Playwright) ─────────────────────

class TestBrowserExecutorLiveMode:

    def _mock_playwright(self, title: str = "Test Page", text: str = "Hello world", url: str = "https://example.com/final"):
        mock_page = MagicMock()
        mock_page.title.return_value = title
        mock_page.url = url
        mock_page.inner_text.return_value = text

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_pw.__enter__ = MagicMock(return_value=mock_pw)
        mock_pw.__exit__ = MagicMock(return_value=False)
        return mock_pw, mock_page, mock_browser

    def test_live_capture_returns_title_and_text(self):
        mock_pw, _, _ = self._mock_playwright(title="TV Ideas", text="market analysis content")
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=True), \
             patch("runtime.siteops.browser_executor.sync_playwright", return_value=mock_pw):
            ex = SiteOpsBrowserExecutor()
            result = ex.capture_page("https://www.tradingview.com/ideas/")
        assert result["ok"] is True
        assert result["title"] == "TV Ideas"
        assert result["text"] == "market analysis content"
        assert result["adapter_mode"] == "live"
        assert result["is_stub"] is False

    def test_live_capture_records_final_url(self):
        mock_pw, mock_page, _ = self._mock_playwright(url="https://www.tradingview.com/ideas/?redirected=1")
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=True), \
             patch("runtime.siteops.browser_executor.sync_playwright", return_value=mock_pw):
            ex = SiteOpsBrowserExecutor()
            result = ex.capture_page("https://www.tradingview.com/ideas/")
        assert result["url"] == "https://www.tradingview.com/ideas/?redirected=1"

    def test_live_capture_truncates_text_at_max(self):
        long_text = "x" * 200_000
        mock_pw, _, _ = self._mock_playwright(text=long_text)
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=True), \
             patch("runtime.siteops.browser_executor.sync_playwright", return_value=mock_pw):
            ex = SiteOpsBrowserExecutor(max_text_chars=50_000)
            result = ex.capture_page("https://example.com")
        assert len(result["text"]) == 50_000
        assert result["char_count"] == 50_000

    def test_live_capture_falls_back_to_content_on_inner_text_error(self):
        mock_page = MagicMock()
        mock_page.title.return_value = "Fallback Page"
        mock_page.url = "https://example.com"
        mock_page.inner_text.side_effect = Exception("inner_text failed")
        mock_page.content.return_value = "<html>fallback content</html>"

        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_pw.__enter__ = MagicMock(return_value=mock_pw)
        mock_pw.__exit__ = MagicMock(return_value=False)

        with patch("runtime.siteops.browser_executor._check_playwright", return_value=True), \
             patch("runtime.siteops.browser_executor.sync_playwright", return_value=mock_pw):
            ex = SiteOpsBrowserExecutor()
            result = ex.capture_page("https://example.com")
        assert result["ok"] is True
        assert "fallback content" in result["text"]

    def test_playwright_exception_returns_error_not_raises(self):
        mock_pw = MagicMock()
        mock_pw.chromium.launch.side_effect = RuntimeError("chromium not found")
        mock_pw.__enter__ = MagicMock(return_value=mock_pw)
        mock_pw.__exit__ = MagicMock(return_value=False)

        with patch("runtime.siteops.browser_executor._check_playwright", return_value=True), \
             patch("runtime.siteops.browser_executor.sync_playwright", return_value=mock_pw):
            ex = SiteOpsBrowserExecutor()
            result = ex.capture_page("https://example.com")
        assert result["ok"] is False
        assert "chromium not found" in (result["error"] or "")
        assert result["adapter_mode"] == "live"

    def test_browser_closed_even_on_page_error(self):
        mock_page = MagicMock()
        mock_page.goto.side_effect = Exception("navigation timeout")
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_pw.__enter__ = MagicMock(return_value=mock_pw)
        mock_pw.__exit__ = MagicMock(return_value=False)

        with patch("runtime.siteops.browser_executor._check_playwright", return_value=True), \
             patch("runtime.siteops.browser_executor.sync_playwright", return_value=mock_pw):
            ex = SiteOpsBrowserExecutor()
            ex.capture_page("https://example.com")
        mock_browser.close.assert_called_once()


# ── capture_and_route ─────────────────────────────────────────────────────────

class TestCaptureAndRoute:

    def test_stub_mode_returns_none_quarantine_path(self, tmp_path):
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=False):
            result = capture_and_route("https://example.com", vault_root=tmp_path)
        assert result["quarantine_path"] is None
        assert result["capture_id"] is None
        assert result["adapter_mode"] == "stub"

    def test_live_mode_routes_to_quarantine(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("# test\n")
        (tmp_path / "03_INPUTS" / "00_QUARANTINE" / "source").mkdir(parents=True)
        (tmp_path / ".chaseos").mkdir(parents=True)

        mock_pw, _, _ = TestBrowserExecutorLiveMode._mock_playwright(
            TestBrowserExecutorLiveMode(),
            title="TV Ideas",
            text="some page content for routing test",
        )
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=True), \
             patch("runtime.siteops.browser_executor.sync_playwright", return_value=mock_pw):
            result = capture_and_route(
                "https://www.tradingview.com/ideas/",
                workflow_id="tradingview.idea.capture",
                vault_root=tmp_path,
            )
        assert result["ok"] is True
        assert result["quarantine_path"] is not None or result["capture_id"] is not None

    def test_quarantine_routing_fail_open(self, tmp_path):
        mock_pw, _, _ = TestBrowserExecutorLiveMode._mock_playwright(
            TestBrowserExecutorLiveMode(), text="content"
        )
        # capture_content is lazy-imported inside _route_to_quarantine; patch via its source module
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=True), \
             patch("runtime.siteops.browser_executor.sync_playwright", return_value=mock_pw), \
             patch("runtime.capture.capture.capture_content", side_effect=Exception("capture error")):
            result = capture_and_route("https://example.com", vault_root=tmp_path)
        assert result["ok"] is True
        assert result["quarantine_path"] is None


# ── Approval validation ───────────────────────────────────────────────────────

class TestApprovalValidation:

    def test_run_live_raises_if_approval_not_found(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        with pytest.raises(SiteOpsApprovalError, match="not found"):
            run_siteops_live(
                "tradingview.idea.capture",
                approval_id="nonexistent-approval",
                tenant_id="local",
                workspace_id="default",
                user_id="local-user",
                vault_root=vault,
            )

    def test_run_live_raises_if_approval_pending(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        _write_approval(vault, "appr-pending", status="pending")
        with pytest.raises(SiteOpsApprovalError, match="not in 'approved' state"):
            run_siteops_live(
                "tradingview.idea.capture",
                approval_id="appr-pending",
                tenant_id="local",
                workspace_id="default",
                user_id="local-user",
                vault_root=vault,
            )

    def test_run_live_raises_if_approval_rejected(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        _write_approval(vault, "appr-rejected", status="rejected")
        with pytest.raises(SiteOpsApprovalError, match="not in 'approved' state"):
            run_siteops_live(
                "tradingview.idea.capture",
                approval_id="appr-rejected",
                tenant_id="local",
                workspace_id="default",
                user_id="local-user",
                vault_root=vault,
            )

    def test_run_live_raises_if_approval_consumed(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        _write_approval(vault, "appr-consumed", status="approved", consumed=True)
        with pytest.raises(SiteOpsApprovalError, match="already consumed"):
            run_siteops_live(
                "tradingview.idea.capture",
                approval_id="appr-consumed",
                tenant_id="local",
                workspace_id="default",
                user_id="local-user",
                vault_root=vault,
            )


# ── Executor kind guard ───────────────────────────────────────────────────────

class TestExecutorKindGuard:

    def test_provider_api_raises_not_built(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        # Patch workflow template to have executor_kind=provider_api
        wf_path = vault / "runtime" / "siteops" / "catalog" / "workflow_templates.yaml"
        import yaml
        data = yaml.safe_load(wf_path.read_text())
        data["workflow_templates"][0]["executor_kind"] = "provider_api"
        wf_path.write_text(yaml.dump(data))

        _write_approval(vault, "appr-api", status="approved")
        with pytest.raises(SiteOpsExecutorNotBuiltError, match="provider_api"):
            run_siteops_live(
                "tradingview.idea.capture",
                approval_id="appr-api",
                tenant_id="local",
                workspace_id="default",
                user_id="local-user",
                vault_root=vault,
            )

    def test_unknown_executor_kind_raises_not_built(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        import yaml
        wf_path = vault / "runtime" / "siteops" / "catalog" / "workflow_templates.yaml"
        data = yaml.safe_load(wf_path.read_text())
        data["workflow_templates"][0]["executor_kind"] = "robot_arms"
        wf_path.write_text(yaml.dump(data))

        _write_approval(vault, "appr-robot", status="approved")
        with pytest.raises(SiteOpsExecutorNotBuiltError, match="robot_arms"):
            run_siteops_live(
                "tradingview.idea.capture",
                approval_id="appr-robot",
                tenant_id="local",
                workspace_id="default",
                user_id="local-user",
                vault_root=vault,
            )


# ── mark_approval_consumed idempotency ────────────────────────────────────────

class TestApprovalConsumedIdempotency:

    def test_mark_consumed_writes_consumed_flag(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        _write_approval(vault, "appr-consume-test", status="approved")
        result = mark_approval_consumed(vault, "local", "default", "appr-consume-test")
        assert result is not None
        assert result["consumed"] is True
        assert "consumed_at" in result

    def test_mark_consumed_is_idempotent(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        _write_approval(vault, "appr-idem", status="approved")
        r1 = mark_approval_consumed(vault, "local", "default", "appr-idem")
        r2 = mark_approval_consumed(vault, "local", "default", "appr-idem")
        assert r1["consumed"] is True
        assert r2["consumed"] is True

    def test_mark_consumed_fail_open_on_missing(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        result = mark_approval_consumed(vault, "local", "default", "nonexistent")
        assert result is None


# ── run_siteops_live success path (stub mode) ─────────────────────────────────

class TestRunSiteopsLiveSuccess:

    def test_stub_mode_returns_would_execute_true(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        _write_approval(vault, "appr-stub-ok", status="approved")
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=False):
            result = run_siteops_live(
                "tradingview.idea.capture",
                approval_id="appr-stub-ok",
                tenant_id="local",
                workspace_id="default",
                user_id="local-user",
                vault_root=vault,
            )
        assert result["would_execute"] is True
        assert result["live_execution_status"] == "ok"

    def test_stub_mode_writes_run_record(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        _write_approval(vault, "appr-runrecord", status="approved")
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=False):
            result = run_siteops_live(
                "tradingview.idea.capture",
                approval_id="appr-runrecord",
                tenant_id="local",
                workspace_id="default",
                user_id="local-user",
                vault_root=vault,
            )
        assert result["run_ref"] is not None
        assert Path(result["run_ref"]).exists()

    def test_stub_mode_marks_approval_consumed(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        _write_approval(vault, "appr-consumed-after", status="approved")
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=False):
            run_siteops_live(
                "tradingview.idea.capture",
                approval_id="appr-consumed-after",
                tenant_id="local",
                workspace_id="default",
                user_id="local-user",
                vault_root=vault,
            )
        approval_path = vault / "07_LOGS" / "SiteOps-Approvals" / "local" / "default" / "appr-consumed-after.json"
        updated = json.loads(approval_path.read_text())
        assert updated["consumed"] is True

    def test_stub_mode_writes_audit_event(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        _write_approval(vault, "appr-audit", status="approved")
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=False):
            result = run_siteops_live(
                "tradingview.idea.capture",
                approval_id="appr-audit",
                tenant_id="local",
                workspace_id="default",
                user_id="local-user",
                vault_root=vault,
            )
        assert result["audit_ref"] is not None

    def test_no_url_in_inputs_returns_failed_status(self, tmp_path):
        import yaml
        vault = _minimal_vault(tmp_path)
        # Remove default_target_url from template
        wf_path = vault / "runtime" / "siteops" / "catalog" / "workflow_templates.yaml"
        data = yaml.safe_load(wf_path.read_text())
        data["workflow_templates"][0].pop("default_target_url", None)
        wf_path.write_text(yaml.dump(data))

        _write_approval(vault, "appr-nourl", status="approved")
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=False):
            result = run_siteops_live(
                "tradingview.idea.capture",
                approval_id="appr-nourl",
                tenant_id="local",
                workspace_id="default",
                user_id="local-user",
                vault_root=vault,
            )
        assert result["live_execution_status"] == "failed"
        assert result["would_execute"] is True

    def test_dry_run_still_returns_would_execute_false(self, tmp_path):
        from runtime.siteops.runner import run_siteops_dry_run
        from runtime.siteops.validator import validate_production_siteops
        vault = _minimal_vault(tmp_path)
        # Patch validation to pass so we can verify the dry-run result shape,
        # not the catalog validation rules (those are tested in test_siteops_runner.py).
        # Patch internal SiteOps validator + policy path — those are tested elsewhere.
        # We care only that the dry-run route returns would_execute=False.
        with patch("runtime.siteops.runner.validate_production_siteops",
                   return_value={"ok": True, "errors": [], "warnings": []}), \
             patch("runtime.siteops.runner.select_policy_pack",
                   return_value={"version": "siteops_default_v1", "policy_pack_id": "siteops_default_v1",
                                 "rules": [], "blocked_actions": [], "approval_required_actions": []}), \
             patch("runtime.siteops.runner.evaluate_siteops_policy",
                   return_value={"status": "pending_approval", "violations": [], "ok": True, "decisions": []}):
            result = run_siteops_dry_run(
                root=vault,
                workflow_id="tradingview.idea.capture",
                tenant_id="local",
                workspace_id="default",
                user_id="local-user",
                write_artifacts=False,
            )
        assert result["would_execute"] is False
        assert result["live_execution_status"] == "NOT BUILT"


# ── AOR handler ───────────────────────────────────────────────────────────────

class TestAORHandler:

    def test_handler_raises_if_workflow_id_missing(self, tmp_path):
        from runtime.workflows.siteops_execute import run_siteops_execute, WorkflowExecutionError
        with pytest.raises(WorkflowExecutionError, match="workflow_id"):
            run_siteops_execute({}, tmp_path)

    def test_handler_raises_if_approval_id_missing(self, tmp_path):
        from runtime.workflows.siteops_execute import run_siteops_execute, WorkflowExecutionError
        with pytest.raises(WorkflowExecutionError, match="approval_id"):
            run_siteops_execute({"workflow_id": "tradingview.idea.capture"}, tmp_path)

    def test_handler_propagates_approval_error_as_workflow_error(self, tmp_path):
        from runtime.workflows.siteops_execute import run_siteops_execute, WorkflowExecutionError
        vault = _minimal_vault(tmp_path)
        with pytest.raises(WorkflowExecutionError):
            run_siteops_execute(
                {"workflow_id": "tradingview.idea.capture", "approval_id": "missing"},
                vault,
            )

    def test_handler_returns_writebacks_on_success(self, tmp_path):
        from runtime.workflows.siteops_execute import run_siteops_execute
        vault = _minimal_vault(tmp_path)
        _write_approval(vault, "appr-handler-ok", status="approved")
        with patch("runtime.siteops.browser_executor._check_playwright", return_value=False):
            result = run_siteops_execute(
                {
                    "workflow_id": "tradingview.idea.capture",
                    "approval_id": "appr-handler-ok",
                    "tenant_id": "local",
                    "workspace_id": "default",
                    "user_id": "local-user",
                },
                vault,
            )
        assert "writebacks" in result
        assert result["live_execution_status"] == "ok"
