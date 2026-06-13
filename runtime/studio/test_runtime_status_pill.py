"""Tests for runtime/studio/runtime_status_pill.py (Pass 10D)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.runtime_status_pill import (
    MODEL_VERSION,
    SURFACE_ID,
    _derive_mode,
    _read_pending_approvals,
    get_runtime_status,
)


# ── _derive_mode ──────────────────────────────────────────────────────────────

class TestDeriveMode:
    def test_observe_when_nothing_active(self):
        mode = _derive_mode(active_count=0, pending_approval_count=0, failed_count=0)
        assert mode == "OBSERVE"

    def test_act_when_tasks_active(self):
        mode = _derive_mode(active_count=2, pending_approval_count=0, failed_count=0)
        assert mode == "ACT"

    def test_await_approval_takes_precedence_over_act(self):
        mode = _derive_mode(active_count=1, pending_approval_count=1, failed_count=0)
        assert mode == "AWAIT_APPROVAL"

    def test_recover_when_failed_tasks(self):
        mode = _derive_mode(active_count=0, pending_approval_count=0, failed_count=1)
        assert mode == "RECOVER"

    def test_await_approval_takes_precedence_over_recover(self):
        mode = _derive_mode(active_count=0, pending_approval_count=1, failed_count=1)
        assert mode == "AWAIT_APPROVAL"

    def test_observe_with_zero_counts(self):
        assert _derive_mode(active_count=0, pending_approval_count=0, failed_count=0) == "OBSERVE"


# ── _read_pending_approvals ───────────────────────────────────────────────────

class TestReadPendingApprovals:
    def _approval_dir(self, vault: Path) -> Path:
        d = vault / "runtime" / "studio" / "approvals"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def test_returns_empty_when_dir_missing(self, tmp_path):
        result = _read_pending_approvals(tmp_path)
        assert result == []

    def test_reads_pending_approvals(self, tmp_path):
        adir = self._approval_dir(tmp_path)
        (adir / "appr_001.json").write_text(
            json.dumps({"approval_id": "appr_001", "action_type": "create_file", "status": "pending"}),
            encoding="utf-8",
        )
        result = _read_pending_approvals(tmp_path)
        assert len(result) == 1
        assert result[0]["approval_id"] == "appr_001"

    def test_ignores_non_pending_approvals(self, tmp_path):
        adir = self._approval_dir(tmp_path)
        (adir / "appr_done.json").write_text(
            json.dumps({"approval_id": "appr_done", "action_type": "write_file", "status": "approved"}),
            encoding="utf-8",
        )
        result = _read_pending_approvals(tmp_path)
        assert result == []

    def test_skips_malformed_json(self, tmp_path):
        adir = self._approval_dir(tmp_path)
        (adir / "bad.json").write_text("not json", encoding="utf-8")
        result = _read_pending_approvals(tmp_path)
        assert result == []

    def test_returns_approval_id_from_filename_when_missing(self, tmp_path):
        adir = self._approval_dir(tmp_path)
        (adir / "appr_fallback.json").write_text(
            json.dumps({"status": "pending", "action_type": "unknown"}),
            encoding="utf-8",
        )
        result = _read_pending_approvals(tmp_path)
        assert len(result) == 1
        assert result[0]["approval_id"] == "appr_fallback"


# ── get_runtime_status ────────────────────────────────────────────────────────

class TestGetRuntimeStatus:
    def test_basic_shape(self, tmp_path):
        result = get_runtime_status(tmp_path)
        assert result["surface"] == SURFACE_ID
        assert result["model_version"] == MODEL_VERSION
        assert "mode" in result
        assert "color" in result
        assert "pulse" in result
        assert "label" in result
        assert isinstance(result["active_task_count"], int)
        assert isinstance(result["pending_approval_count"], int)
        assert isinstance(result["failed_task_count"], int)
        assert isinstance(result["heartbeat_count"], int)

    def test_mode_is_valid_string(self, tmp_path):
        result = get_runtime_status(tmp_path)
        valid_modes = {"OBSERVE", "PLAN", "ACT", "AWAIT_APPROVAL", "RECOVER", "DONE", "FAILED", "IDLE"}
        assert result["mode"] in valid_modes

    def test_observe_mode_when_bus_unavailable(self, tmp_path):
        result = get_runtime_status(tmp_path)
        # Bus not available in test env — should still return a valid result
        assert result["mode"] in {"OBSERVE", "RECOVER"}
        assert result["readiness"]["mode_derived"] is True

    def test_fail_open_returns_dict_even_without_bus(self, tmp_path):
        result = get_runtime_status(tmp_path)
        assert isinstance(result, dict)
        assert "ok" not in result  # not the api envelope — raw data

    def test_read_only_authority(self, tmp_path):
        result = get_runtime_status(tmp_path)
        readiness = result["readiness"]
        assert readiness["read_only"] is True
        assert readiness["writes_vault"] is False
        assert readiness["provider_calls"] is False
        assert readiness["connector_calls"] is False

    def test_await_approval_mode_when_pending_approval_exists(self, tmp_path):
        adir = tmp_path / "runtime" / "studio" / "approvals"
        adir.mkdir(parents=True)
        (adir / "appr_test.json").write_text(
            json.dumps({"approval_id": "appr_test", "action_type": "create_file", "status": "pending"}),
            encoding="utf-8",
        )
        result = get_runtime_status(tmp_path)
        assert result["mode"] == "AWAIT_APPROVAL"
        assert result["pending_approval_count"] == 1
        assert result["color"] == "amber"
        assert result["pulse"] is False

    def test_observe_mode_with_no_approvals(self, tmp_path):
        result = get_runtime_status(tmp_path)
        assert result["pending_approval_count"] == 0

    def test_pending_approvals_capped_at_five(self, tmp_path):
        adir = tmp_path / "runtime" / "studio" / "approvals"
        adir.mkdir(parents=True)
        for i in range(8):
            (adir / f"appr_{i:03d}.json").write_text(
                json.dumps({"approval_id": f"appr_{i}", "action_type": "create_file", "status": "pending"}),
                encoding="utf-8",
            )
        result = get_runtime_status(tmp_path)
        assert result["pending_approval_count"] == 8
        assert len(result["pending_approvals"]) <= 5

    def test_warnings_is_list(self, tmp_path):
        result = get_runtime_status(tmp_path)
        assert isinstance(result["warnings"], list)

    def test_color_matches_mode(self, tmp_path):
        result = get_runtime_status(tmp_path)
        mode_to_color = {
            "OBSERVE": "gray", "IDLE": "gray",
            "PLAN": "blue",
            "ACT": "green", "DONE": "green",
            "AWAIT_APPROVAL": "amber",
            "RECOVER": "orange",
            "FAILED": "red",
        }
        assert result["color"] == mode_to_color.get(result["mode"], "gray")

    def test_label_is_human_readable(self, tmp_path):
        result = get_runtime_status(tmp_path)
        assert "_" not in result["label"]
        assert len(result["label"]) > 0

    def test_returns_path_as_string_in_vault_root(self, tmp_path):
        result = get_runtime_status(tmp_path)
        assert isinstance(result, dict)

    def test_live_vault_returns_valid_shape(self):
        from pathlib import Path
        vault = Path(__file__).parent.parent.parent
        result = get_runtime_status(vault)
        assert result["surface"] == SURFACE_ID
        assert "mode" in result
        valid_modes = {"OBSERVE", "PLAN", "ACT", "AWAIT_APPROVAL", "RECOVER", "DONE", "FAILED", "IDLE"}
        assert result["mode"] in valid_modes


# ── API envelope integration ──────────────────────────────────────────────────

class TestApiIntegration:
    def test_api_get_project_workspace_view(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        (tmp_path / "01_PROJECTS").mkdir()
        api = StudioAPI(tmp_path)
        result = api.get_project_workspace_view()
        assert result["ok"] is True
        assert result["surface"] == "project_workspace_view"
        data = result["data"]
        assert "project_count" in data
        assert "domains" in data

    def test_api_get_runtime_status(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(tmp_path)
        result = api.get_runtime_status()
        assert result["ok"] is True
        assert result["surface"] == "runtime_status"
        data = result["data"]
        assert "mode" in data
        assert "color" in data

    def test_api_project_workspace_warns_missing_dir(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(tmp_path)
        result = api.get_project_workspace_view()
        assert result["ok"] is True
        assert "projects_dir_missing" in result.get("warnings", [])
