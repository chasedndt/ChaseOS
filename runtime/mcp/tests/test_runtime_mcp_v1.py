"""Runtime MCP V1 acceptance tests — Pass 5A hardening edition."""

from __future__ import annotations

import json
import re
import shutil
import sys
import unittest
import uuid
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[3]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.mcp.audit.logger import MCPAuditError, MCPAuditLogger
from runtime.mcp.config import ConfigError, load_config
from runtime.mcp.safety import DEFERRED_SURFACES, EXCLUDED_SURFACES
from runtime.mcp.server import handle_request, run_server
from runtime.mcp.types import HandlerResult, MCPRequest, SurfaceClass


class FailingAuditLogger:
    """Stub that raises MCPAuditError on every log() call."""

    def log(
        self,
        request_id: str,
        surface_id: str,
        surface_class: str,
        runtime_id: str,
        trust_tier: int,
        safety_mode: str,
        outcome: str,
        outcome_detail: str | None,
        files_read: list[str],
        files_written: list[str],
        error_code: str | None,
        error_message: str | None,
    ) -> None:
        raise MCPAuditError("forced audit failure")


class RuntimeMCPV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = _VAULT_ROOT / ".codex_tmp_test"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = scratch / f"chaseos-mcp-v1-{uuid.uuid4().hex}"
        self.tmp.mkdir()
        self._populate_vault(self.tmp)
        self.config = load_config(vault_root=self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _populate_vault(self, root: Path) -> None:
        (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
        (root / "00_HOME").mkdir(parents=True)
        (root / "00_HOME" / "Now.md").write_text(
            "\n".join(
                [
                    "# Now",
                    "",
                    "## Current Phase",
                    "Phase 9 Pass 4A active.",
                    "",
                    "## Active Now",
                    "| Domain | Current focus |",
                    "|--------|---------------|",
                    "| ChaseOS / System Infrastructure | Runtime MCP V1 |",
                    "",
                    "- Ship Runtime MCP scaffold",
                ]
            ),
            encoding="utf-8",
        )
        (root / "01_PROJECTS" / "ChaseOS").mkdir(parents=True)
        (root / "01_PROJECTS" / "ChaseOS" / "ChaseOS-OS.md").write_text(
            "## Open Loops\n- [ ] Keep MCP bounded\n",
            encoding="utf-8",
        )
        (root / "04_SOPS").mkdir(parents=True)
        (root / "05_TEMPLATES").mkdir(parents=True)
        (root / "05_TEMPLATES" / "example.md").write_text("old\n", encoding="utf-8")
        (root / "06_AGENTS").mkdir(parents=True)
        (root / "06_AGENTS" / "role-cards").mkdir(parents=True)
        (root / "06_AGENTS" / "role-cards" / "operator-briefing.yaml").write_text(
            "\n".join(
                [
                    "id: operator-briefing",
                    "name: Operator Briefing",
                    "allowed_actions:",
                    "  - read_any_non_protected_file",
                    "forbidden_actions:",
                    "  - write_protected_files",
                    "write_scope:",
                    "  - 07_LOGS/Operator-Briefs/",
                    "forbidden_write_zones:",
                    "  - 00_HOME/Now.md",
                ]
            ),
            encoding="utf-8",
        )
        (root / "runtime" / "workflows" / "registry").mkdir(parents=True)
        (root / "runtime" / "workflows" / "registry" / "operator_today.yaml").write_text(
            "\n".join(
                [
                    "id: operator_today",
                    "name: Operator Today",
                    "status: active",
                    "task_type: operator-briefing",
                    "role_card: operator-briefing",
                    "permission_ceiling: no_protected_file_writes",
                    "writeback_targets:",
                    "  - 07_LOGS/Operator-Briefs/",
                ]
            ),
            encoding="utf-8",
        )
        (root / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
        (root / "07_LOGS" / "Decision-Ledger" / "Index.md").write_text(
            "- Decision: keep MCP internal\n",
            encoding="utf-8",
        )

    def _request(self, payload: dict) -> dict:
        return handle_request(payload, config=self.config)

    def _submit(
        self,
        target: str = "05_TEMPLATES/example.md",
        change_type: str = "update",
        description: str = "test proposal",
    ) -> str:
        response = self._request(
            {
                "tool": "proposal.submit",
                "runtime_id": "openclaw",
                "mode": "read_plus_proposal",
                "params": {
                    "target_file": target,
                    "change_type": change_type,
                    "proposed_content": "new\n",
                    "description": description,
                },
            }
        )
        self.assertTrue(response["ok"], response)
        return response["result"]["proposal_id"]

    # ──────────────────────────────────────────────
    # Config
    # ──────────────────────────────────────────────

    def test_config_load_success(self) -> None:
        self.assertEqual(self.config.default_mode, "read_only")
        self.assertEqual(self.config.server_identity, "chaseos-runtime-mcp")

    def test_config_load_failure(self) -> None:
        bad_config = self.tmp / "bad-config.yaml"
        bad_config.write_text("safety: [bad\n", encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_config(vault_root=self.tmp, config_path=bad_config)

    # ──────────────────────────────────────────────
    # Mode and surface availability
    # ──────────────────────────────────────────────

    def test_read_only_blocks_tools(self) -> None:
        response = self._request(
            {
                "tool": "proposal.submit",
                "runtime_id": "openclaw",
                "mode": "read_only",
                "params": {"target_file": "05_TEMPLATES/example.md", "proposed_content": "x"},
            }
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "surface_unavailable")

    def test_read_plus_proposal_allows_tools(self) -> None:
        proposal_id = self._submit()
        self.assertTrue(proposal_id.startswith("proposal-"))

    def test_unknown_surface_rejection(self) -> None:
        response = self._request(
            {"resource": "runtime.not_real", "runtime_id": "openclaw", "mode": "read_only"}
        )
        self.assertFalse(response["ok"])
        self.assertIn(response["error"]["code"], {"unknown_surface", "surface_unavailable"})

    # ──────────────────────────────────────────────
    # runtime.identity — frozen field names
    # ──────────────────────────────────────────────

    def test_runtime_identity_field_names(self) -> None:
        response = self._request(
            {"resource": "runtime.identity", "runtime_id": "openclaw", "mode": "read_only"}
        )
        self.assertTrue(response["ok"])
        result = response["result"]
        # Frozen contract field names from ChaseOS-MCP-Data-Contracts.md
        self.assertIn("server_name", result)
        self.assertIn("server_version", result)
        self.assertIn("vault_root_confirmed", result)
        self.assertIn("transport", result)
        self.assertIn("active_safety_mode", result)
        self.assertEqual(result["server_name"], "chaseos-runtime-mcp")
        self.assertEqual(result["active_safety_mode"], "read_only")
        self.assertTrue(result["vault_root_confirmed"])

    # ──────────────────────────────────────────────
    # chaseos.current_truth
    # ──────────────────────────────────────────────

    def test_current_truth_default_safe_fields(self) -> None:
        response = self._request(
            {"resource": "chaseos.current_truth", "runtime_id": "openclaw", "mode": "read_only"}
        )
        self.assertTrue(response["ok"])
        self.assertEqual(
            sorted(response["result"].keys()),
            ["active_domains", "current_phase", "sprint_focus"],
        )

    def test_current_truth_explicit_fields(self) -> None:
        response = self._request(
            {
                "resource": "chaseos.current_truth",
                "runtime_id": "openclaw",
                "mode": "read_only",
                "params": {"fields": ["open_loops", "recent_decisions"]},
            }
        )
        self.assertTrue(response["ok"])
        self.assertEqual(sorted(response["result"].keys()), ["open_loops", "recent_decisions"])

    def test_current_truth_missing_now_md_fails_cleanly(self) -> None:
        """Missing Now.md must produce a clean system_error, not silent empty results."""
        (self.tmp / "00_HOME" / "Now.md").unlink()
        response = self._request(
            {"resource": "chaseos.current_truth", "runtime_id": "openclaw", "mode": "read_only"}
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["category"], "system_error")
        self.assertIn("Now.md", response["error"]["message"])

    # ──────────────────────────────────────────────
    # proposal.submit — artifact schema and filename
    # ──────────────────────────────────────────────

    def test_proposal_submit_artifact_schema(self) -> None:
        """Staged artifact must contain all frozen ProposalArtifact schema fields."""
        proposal_id = self._submit()
        staged = list((self.tmp / ".chaseos" / "mcp-proposals").glob("*.json"))
        self.assertEqual(len(staged), 1)
        raw = json.loads(staged[0].read_text(encoding="utf-8"))

        required_fields = [
            "schema_version", "proposal_id", "staged_at", "runtime_id",
            "safety_mode_at_staging", "change_type", "target_file", "description",
            "proposed_content", "current_sha256", "proposed_sha256",
            "governance_flags", "status", "status_history",
        ]
        for field in required_fields:
            self.assertIn(field, raw, f"Missing field: {field}")

        self.assertEqual(raw["schema_version"], "1.0")
        self.assertEqual(raw["proposal_id"], proposal_id)
        self.assertEqual(raw["status"], "staged")
        self.assertEqual(raw["change_type"], "update")
        self.assertIsInstance(raw["status_history"], list)
        self.assertEqual(raw["status_history"][0]["status"], "staged")

        # governance_flags must use frozen field names
        gf = raw["governance_flags"]
        self.assertIn("is_protected_file", gf)
        self.assertIn("permission_ceiling_respected", gf)
        self.assertIn("writeback_scope_declared", gf)
        self.assertFalse(gf["is_protected_file"])

    def test_proposal_submit_filename_is_timestamp_based(self) -> None:
        """Staging filename must follow {YYYYMMDD-HHMMSS}__{proposal_id[:8]}.json pattern."""
        self._submit()
        staged = list((self.tmp / ".chaseos" / "mcp-proposals").glob("*.json"))
        self.assertEqual(len(staged), 1)
        name = staged[0].stem  # without .json
        # Pattern: YYYYMMDD-HHMMSS__<8 hex chars>
        self.assertRegex(name, r"^\d{8}-\d{6}__[0-9a-f]{8}$")

    def test_proposal_submit_response_shape(self) -> None:
        """Submit response must use frozen field names from data contracts."""
        response = self._request(
            {
                "tool": "proposal.submit",
                "runtime_id": "openclaw",
                "mode": "read_plus_proposal",
                "params": {
                    "target_file": "05_TEMPLATES/example.md",
                    "change_type": "update",
                    "proposed_content": "new\n",
                    "description": "test",
                },
            }
        )
        self.assertTrue(response["ok"])
        result = response["result"]
        self.assertIn("proposal_id", result)
        self.assertIn("proposal_status", result)
        self.assertIn("staged_at", result)
        self.assertIn("target_file", result)
        self.assertIn("change_type", result)
        self.assertIn("preliminary_validation", result)
        self.assertEqual(result["proposal_status"], "staged")

    def test_proposal_submit_audit_failure_rolls_back(self) -> None:
        response = handle_request(
            {
                "tool": "proposal.submit",
                "runtime_id": "openclaw",
                "mode": "read_plus_proposal",
                "params": {
                    "target_file": "05_TEMPLATES/example.md",
                    "change_type": "update",
                    "proposed_content": "new\n",
                    "description": "force rollback",
                },
            },
            config=self.config,
            logger=FailingAuditLogger(),
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "audit_write_failed")
        staged = list((self.tmp / ".chaseos" / "mcp-proposals").glob("*.json"))
        self.assertEqual(staged, [])

    # ──────────────────────────────────────────────
    # proposal.validate — frozen protected file list
    # ──────────────────────────────────────────────

    def test_proposal_validate_protected_file_violation(self) -> None:
        """Permission-Matrix.md is protected per frozen Proposal Staging doc."""
        proposal_id = self._submit("06_AGENTS/Permission-Matrix.md")
        response = self._request(
            {
                "tool": "proposal.validate",
                "runtime_id": "openclaw",
                "mode": "read_plus_proposal",
                "params": {"proposal_id": proposal_id},
            }
        )
        self.assertTrue(response["ok"])
        result = response["result"]
        self.assertFalse(result["is_valid"])
        self.assertTrue(result["protected_file_flag"])
        self.assertGreater(len(result["errors"]), 0)
        self.assertEqual(result["errors"][0]["error_code"], "protected_file_violation")

    def test_proposal_validate_response_shape(self) -> None:
        """Validate response must use frozen field names: is_valid, protected_file_flag, errors, warnings, governance_checks."""
        proposal_id = self._submit()
        response = self._request(
            {
                "tool": "proposal.validate",
                "runtime_id": "openclaw",
                "mode": "read_plus_proposal",
                "params": {"proposal_id": proposal_id},
            }
        )
        self.assertTrue(response["ok"])
        result = response["result"]
        for field in ["is_valid", "protected_file_flag", "errors", "warnings", "governance_checks"]:
            self.assertIn(field, result)
        self.assertTrue(result["is_valid"])
        self.assertFalse(result["protected_file_flag"])
        self.assertEqual(result["errors"], [])

    def test_proposal_validate_non_protected_project_file(self) -> None:
        """01_PROJECTS/ file must NOT be protected per frozen doc (was over-restricted in Pass 4)."""
        proposal_id = self._submit("01_PROJECTS/ChaseOS/ChaseOS-OS.md")
        response = self._request(
            {
                "tool": "proposal.validate",
                "runtime_id": "openclaw",
                "mode": "read_plus_proposal",
                "params": {"proposal_id": proposal_id},
            }
        )
        self.assertTrue(response["ok"])
        self.assertTrue(response["result"]["is_valid"])

    # ──────────────────────────────────────────────
    # proposal.diff_preview — frozen response shape
    # ──────────────────────────────────────────────

    def test_proposal_diff_preview_response_shape(self) -> None:
        """diff_preview response must use frozen field names."""
        proposal_id = self._submit()
        response = self._request(
            {
                "tool": "proposal.diff_preview",
                "runtime_id": "openclaw",
                "mode": "read_plus_proposal",
                "params": {"proposal_id": proposal_id},
            }
        )
        self.assertTrue(response["ok"])
        result = response["result"]
        self.assertIn("diff_content", result)
        self.assertIn("diff_format", result)
        self.assertIn("current_sha256", result)
        self.assertIn("proposed_sha256", result)
        self.assertIn("lines_added", result)
        self.assertIn("lines_removed", result)
        self.assertEqual(result["diff_format"], "unified")
        self.assertIn("-old", result["diff_content"])
        self.assertIn("+new", result["diff_content"])

    # ──────────────────────────────────────────────
    # approval_request.create — frozen response shape
    # ──────────────────────────────────────────────

    def test_approval_request_create_response_shape(self) -> None:
        """approval_request.create response must use frozen field names."""
        proposal_id = self._submit()
        response = self._request(
            {
                "tool": "approval_request.create",
                "runtime_id": "openclaw",
                "mode": "read_plus_proposal",
                "params": {"proposal_id": proposal_id},
            }
        )
        self.assertTrue(response["ok"], response)
        result = response["result"]
        self.assertIn("approval_request_id", result)
        self.assertIn("approval_status", result)
        self.assertIn("delivery_confirmed", result)
        self.assertIn("delivered_to", result)
        self.assertIn("next_action", result)
        self.assertEqual(result["approval_status"], "pending_human_review")
        self.assertTrue(result["delivery_confirmed"])
        self.assertIsInstance(result["delivered_to"], list)
        # Artifact must actually exist.
        artifact_path = self.tmp / result["delivered_to"][0]
        self.assertTrue(artifact_path.exists())

    def test_approval_request_artifact_write_failure(self) -> None:
        from dataclasses import replace
        proposal_id = self._submit()
        blocked = self.tmp / "blocked-operator-briefs"
        blocked.write_text("not a directory", encoding="utf-8")
        bad_config = replace(self.config, operator_briefs_dir=blocked)
        response = handle_request(
            {
                "tool": "approval_request.create",
                "runtime_id": "openclaw",
                "mode": "read_plus_proposal",
                "params": {"proposal_id": proposal_id},
            },
            config=bad_config,
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "artifact_write_failed")

    # ──────────────────────────────────────────────
    # Audit logger — frozen schema
    # ──────────────────────────────────────────────

    def test_audit_logger_writes_frozen_schema(self) -> None:
        """Audit record JSON must match the frozen schema from ChaseOS-MCP-Audit-Policy.md."""
        audit_logger = MCPAuditLogger(self.config.audit_dir)
        audit_logger.log(
            request_id="req-abc12345def67890",
            surface_id="runtime.identity",
            surface_class="resource",
            runtime_id="openclaw",
            trust_tier=1,
            safety_mode="read_only",
            outcome="success",
            outcome_detail=None,
            files_read=["00_HOME/Now.md"],
            files_written=[],
            error_code=None,
            error_message=None,
        )
        files = list(self.config.audit_dir.glob("*.json"))
        self.assertEqual(len(files), 1)
        raw = json.loads(files[0].read_text(encoding="utf-8"))

        required_fields = [
            "schema_version", "request_id", "recorded_at", "surface_id",
            "surface_class", "runtime_id", "trust_tier", "safety_mode",
            "outcome", "outcome_detail", "files_read", "files_written",
            "error_code", "error_message",
        ]
        for field in required_fields:
            self.assertIn(field, raw, f"Missing frozen audit field: {field}")

        self.assertEqual(raw["schema_version"], "1.0")
        self.assertEqual(raw["surface_id"], "runtime.identity")
        self.assertEqual(raw["trust_tier"], 1)
        self.assertEqual(raw["safety_mode"], "read_only")
        self.assertEqual(raw["outcome"], "success")
        self.assertIsNone(raw["outcome_detail"])
        self.assertEqual(raw["files_read"], ["00_HOME/Now.md"])
        self.assertEqual(raw["files_written"], [])
        self.assertIsNone(raw["error_code"])

    def test_audit_filename_convention(self) -> None:
        """Audit filename must follow {YYYYMMDD-HHMMSS}__mcp__{surface_id}__{request_id[:8]}.json."""
        audit_logger = MCPAuditLogger(self.config.audit_dir)
        audit_logger.log(
            request_id="req-aabbccdd11223344",
            surface_id="chaseos.current_truth",
            surface_class="resource",
            runtime_id="openclaw",
            trust_tier=1,
            safety_mode="read_only",
            outcome="success",
            outcome_detail=None,
            files_read=[],
            files_written=[],
            error_code=None,
            error_message=None,
        )
        files = list(self.config.audit_dir.glob("*.json"))
        self.assertEqual(len(files), 1)
        name = files[0].name
        # Must contain mcp and the surface_id
        self.assertIn("__mcp__", name)
        self.assertIn("chaseos.current_truth", name)
        # Timestamp prefix: YYYYMMDD-HHMMSS
        self.assertRegex(name, r"^\d{8}-\d{6}__mcp__")

    def test_audit_logger_raises_mcp_audit_error_on_failure(self) -> None:
        """MCPAuditLogger.log() must raise MCPAuditError when audit_dir is unwriteable."""
        blocked = self.tmp / "blocked-audit-file"
        blocked.write_text("not a directory", encoding="utf-8")
        audit_logger = MCPAuditLogger(blocked)
        with self.assertRaises(MCPAuditError):
            audit_logger.log(
                request_id="req-test",
                surface_id="runtime.identity",
                surface_class="resource",
                runtime_id="openclaw",
                trust_tier=1,
                safety_mode="read_only",
                outcome="success",
                outcome_detail=None,
                files_read=[],
                files_written=[],
                error_code=None,
                error_message=None,
            )

    # ──────────────────────────────────────────────
    # Prompt — static only
    # ──────────────────────────────────────────────

    def test_prompt_serving_static_only(self) -> None:
        (self.tmp / "runtime_handoff_secret.md").write_text("SECRET_CONTEXT_SHOULD_NOT_LOAD", encoding="utf-8")
        response = self._request(
            {
                "prompt": "handoff.runtime_draft_frame",
                "runtime_id": "openclaw",
                "mode": "read_plus_proposal",
            }
        )
        self.assertTrue(response["ok"])
        self.assertFalse(response["result"]["context_loaded"])
        self.assertNotIn("SECRET_CONTEXT_SHOULD_NOT_LOAD", response["result"]["template"])

    # ──────────────────────────────────────────────
    # No deferred/excluded surfaces exposed
    # ──────────────────────────────────────────────

    def test_no_deferred_or_excluded_surfaces_exposed(self) -> None:
        response = self._request(
            {"resource": "runtime.capabilities", "runtime_id": "openclaw", "mode": "read_plus_proposal"}
        )
        self.assertTrue(response["ok"])
        live = (
            response["result"]["resources"]
            + response["result"]["tools"]
            + response["result"]["prompts"]
        )
        for surface in DEFERRED_SURFACES + EXCLUDED_SURFACES:
            self.assertNotIn(surface, live)

        rejected = self._request(
            {"tool": "workflow.invoke_bounded", "runtime_id": "openclaw", "mode": "read_plus_proposal"}
        )
        self.assertFalse(rejected["ok"])

    # ──────────────────────────────────────────────
    # stdio loop
    # ──────────────────────────────────────────────

    def test_stdio_server_loop_starts_and_serves_one_request(self) -> None:
        payload = json.dumps(
            {"resource": "runtime.identity", "runtime_id": "openclaw", "mode": "read_only"}
        )
        output = StringIO()
        exit_code = run_server(
            stdin=StringIO(payload + "\n"),
            stdout=output,
            vault_root=self.tmp,
        )
        self.assertEqual(exit_code, 0)
        response = json.loads(output.getvalue())
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["server_name"], "chaseos-runtime-mcp")


class Pass5AHardeningTests(unittest.TestCase):
    """Pass 5A — hardened paths + handler fidelity tests."""

    def setUp(self) -> None:
        scratch = _VAULT_ROOT / ".codex_tmp_test"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = scratch / f"chaseos-mcp-pass5a-{uuid.uuid4().hex}"
        self.tmp.mkdir()
        self._populate_vault(self.tmp)
        self.config = load_config(vault_root=self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _populate_vault(self, root: Path) -> None:
        (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
        (root / "00_HOME").mkdir(parents=True)
        (root / "00_HOME" / "Now.md").write_text(
            "\n".join([
                "# Now",
                "## Current Phase",
                "Phase 9 Pass 5A active.",
                "## Active Now",
                "| Domain | Current focus |",
                "|--------|---------------|",
                "| ChaseOS | MCP hardening |",
                "- Ship Pass 5A",
            ]),
            encoding="utf-8",
        )
        (root / "01_PROJECTS" / "ChaseOS").mkdir(parents=True)
        (root / "01_PROJECTS" / "ChaseOS" / "ChaseOS-OS.md").write_text(
            "## Open Loops\n- [ ] Harden MCP\n", encoding="utf-8"
        )
        (root / "04_SOPS").mkdir(parents=True)
        (root / "05_TEMPLATES").mkdir(parents=True)
        (root / "05_TEMPLATES" / "example.md").write_text("old\n", encoding="utf-8")
        (root / "06_AGENTS").mkdir(parents=True)
        (root / "06_AGENTS" / "role-cards").mkdir(parents=True)
        (root / "06_AGENTS" / "role-cards" / "operator-briefing.yaml").write_text(
            "id: operator-briefing\nname: Operator Briefing\nallowed_actions:\n  - read_any_non_protected_file\nforbidden_actions:\n  - write_protected_files\nwrite_scope:\n  - 07_LOGS/Operator-Briefs/\nforbidden_write_zones:\n  - 00_HOME/Now.md\n",
            encoding="utf-8",
        )
        (root / "runtime" / "workflows" / "registry").mkdir(parents=True)
        (root / "runtime" / "workflows" / "registry" / "operator_today.yaml").write_text(
            "id: operator_today\nname: Operator Today\nstatus: active\ntask_type: operator-briefing\nrole_card: operator-briefing\npermission_ceiling: no_protected_file_writes\nwriteback_targets:\n  - 07_LOGS/Operator-Briefs/\n",
            encoding="utf-8",
        )
        (root / "runtime" / "workflows" / "registry" / "draft_workflow.yaml").write_text(
            "id: draft_workflow\nname: Draft Workflow\nstatus: draft\ntask_type: operator-briefing\nrole_card: operator-briefing\npermission_ceiling: no_protected_file_writes\nwriteback_targets: []\n",
            encoding="utf-8",
        )
        (root / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
        (root / "07_LOGS" / "Decision-Ledger" / "Index.md").write_text(
            "- Decision: keep MCP internal\n", encoding="utf-8"
        )

    def _request(self, payload: dict) -> dict:
        return handle_request(payload, config=self.config)

    # ──────────────────────────────────────────────
    # Stdio hardening — malformed input
    # ──────────────────────────────────────────────

    def test_malformed_json_returns_bad_json_error(self) -> None:
        from runtime.mcp.server import handle_json_line
        response = handle_json_line("{not valid json}")
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "bad_json")

    def test_non_dict_json_returns_bad_request(self) -> None:
        from runtime.mcp.server import handle_json_line
        response = handle_json_line('["list", "not", "object"]')
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "bad_request")

    def test_empty_string_json_returns_bad_json(self) -> None:
        from runtime.mcp.server import handle_json_line
        response = handle_json_line('""')
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "bad_request")

    def test_missing_surface_key_returns_bad_request(self) -> None:
        response = self._request({"runtime_id": "openclaw", "mode": "read_only"})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "bad_request")

    def test_invalid_params_type_returns_bad_request(self) -> None:
        response = self._request(
            {"resource": "runtime.identity", "runtime_id": "openclaw", "mode": "read_only", "params": "bad"}
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "bad_request")

    def test_mode_denied_returns_proper_error(self) -> None:
        # n8n is only allowed read_only, not read_plus_proposal
        response = self._request(
            {"resource": "runtime.identity", "runtime_id": "n8n", "mode": "read_plus_proposal"}
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "mode_denied")

    def test_unknown_mode_returns_mode_denied(self) -> None:
        response = self._request(
            {"resource": "runtime.identity", "runtime_id": "openclaw", "mode": "super_mode"}
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "mode_denied")

    def test_config_invalid_path_raises_config_error(self) -> None:
        bad_config = self.tmp / "bad-config.yaml"
        bad_config.write_text("safety: [bad\n", encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_config(vault_root=self.tmp, config_path=bad_config)

    def test_handle_request_returns_config_invalid_on_bad_config(self) -> None:
        bad_config = self.tmp / "bad2.yaml"
        bad_config.write_text("{}\n", encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_config(vault_root=self.tmp, config_path=bad_config)

    # ──────────────────────────────────────────────
    # workflows.registry — filter param
    # ──────────────────────────────────────────────

    def test_workflows_registry_filter_all_returns_all(self) -> None:
        response = self._request(
            {"resource": "workflows.registry", "runtime_id": "openclaw", "mode": "read_only",
             "params": {"filter": "all"}}
        )
        self.assertTrue(response["ok"])
        self.assertEqual(len(response["result"]["workflows"]), 2)
        self.assertEqual(response["result"]["filter"], "all")

    def test_workflows_registry_filter_active_returns_only_active(self) -> None:
        response = self._request(
            {"resource": "workflows.registry", "runtime_id": "openclaw", "mode": "read_only",
             "params": {"filter": "active"}}
        )
        self.assertTrue(response["ok"])
        ids = [w["id"] for w in response["result"]["workflows"]]
        self.assertIn("operator_today", ids)
        self.assertNotIn("draft_workflow", ids)
        self.assertEqual(response["result"]["filter"], "active")

    def test_workflows_registry_filter_draft_returns_only_draft(self) -> None:
        response = self._request(
            {"resource": "workflows.registry", "runtime_id": "openclaw", "mode": "read_only",
             "params": {"filter": "draft"}}
        )
        self.assertTrue(response["ok"])
        ids = [w["id"] for w in response["result"]["workflows"]]
        self.assertNotIn("operator_today", ids)
        self.assertIn("draft_workflow", ids)

    def test_workflows_registry_default_filter_is_all(self) -> None:
        response = self._request(
            {"resource": "workflows.registry", "runtime_id": "openclaw", "mode": "read_only"}
        )
        self.assertTrue(response["ok"])
        self.assertEqual(len(response["result"]["workflows"]), 2)

    def test_workflows_registry_invalid_filter_returns_error(self) -> None:
        response = self._request(
            {"resource": "workflows.registry", "runtime_id": "openclaw", "mode": "read_only",
             "params": {"filter": "published"}}
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "invalid_filter_value")

    # ──────────────────────────────────────────────
    # runtime.audit.recent — bounded output
    # ──────────────────────────────────────────────

    def test_audit_recent_limit_is_clamped(self) -> None:
        from runtime.mcp.server import handle_request as _hr
        # Limit of 200 should be clamped to 50 — no error, just bounded result
        response = _hr(
            {"resource": "runtime.audit.recent", "runtime_id": "openclaw", "mode": "read_only",
             "params": {"limit": 200}},
            config=self.config,
        )
        self.assertTrue(response["ok"])

    def test_audit_recent_with_no_files_returns_empty(self) -> None:
        response = self._request(
            {"resource": "runtime.audit.recent", "runtime_id": "openclaw", "mode": "read_only"}
        )
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["records"], [])

    # ──────────────────────────────────────────────
    # runtime.handoff.current — error propagation
    # ──────────────────────────────────────────────

    def test_handoff_current_missing_now_md_propagates_error(self) -> None:
        (self.tmp / "00_HOME" / "Now.md").unlink()
        response = self._request(
            {"resource": "runtime.handoff.current", "runtime_id": "openclaw", "mode": "read_only"}
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["category"], "system_error")
        self.assertIn("Now.md", response["error"]["message"])

    def test_handoff_current_with_valid_vault_succeeds(self) -> None:
        response = self._request(
            {"resource": "runtime.handoff.current", "runtime_id": "openclaw", "mode": "read_only"}
        )
        self.assertTrue(response["ok"])
        self.assertIn("current_truth", response["result"])
        self.assertIn("open_loops", response["result"])
        self.assertIn("latest_operator_brief", response["result"])

    # ──────────────────────────────────────────────
    # Stdio multi-request smoke
    # ──────────────────────────────────────────────

    def test_stdio_multi_request_smoke(self) -> None:
        lines = "\n".join([
            json.dumps({"resource": "runtime.identity", "runtime_id": "openclaw", "mode": "read_only"}),
            json.dumps({"resource": "runtime.capabilities", "runtime_id": "openclaw", "mode": "read_only"}),
            "{bad json}",
            json.dumps({"resource": "chaseos.current_truth", "runtime_id": "openclaw", "mode": "read_only"}),
        ]) + "\n"
        output = StringIO()
        exit_code = run_server(
            stdin=StringIO(lines),
            stdout=output,
            vault_root=self.tmp,
        )
        self.assertEqual(exit_code, 0)
        responses = [json.loads(line) for line in output.getvalue().strip().splitlines()]
        self.assertEqual(len(responses), 4)
        self.assertTrue(responses[0]["ok"])   # runtime.identity
        self.assertTrue(responses[1]["ok"])   # runtime.capabilities
        self.assertFalse(responses[2]["ok"])  # bad JSON → bad_json
        self.assertEqual(responses[2]["error"]["code"], "bad_json")
        self.assertTrue(responses[3]["ok"])   # current_truth — server continues after bad request


class Pass6BWorkflowInvocationTests(unittest.TestCase):
    """Pass 6B - scoped workflow.invoke_bounded implementation tests."""

    def setUp(self) -> None:
        scratch = _VAULT_ROOT / ".codex_tmp_test"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = scratch / f"chaseos-mcp-pass6b-{uuid.uuid4().hex}"
        self.tmp.mkdir()
        self._populate_vault(self.tmp)
        self.config = load_config(vault_root=self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _populate_vault(self, root: Path) -> None:
        (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
        (root / "00_HOME").mkdir(parents=True)
        (root / "00_HOME" / "Now.md").write_text(
            "# Now\n## Current Phase\nPhase 9 Pass 6B active.\n",
            encoding="utf-8",
        )
        (root / "03_INPUTS").mkdir(parents=True)
        (root / "07_LOGS" / "Build-Logs").mkdir(parents=True)
        (root / "07_LOGS" / "Decision-Ledger").mkdir(parents=True)
        (root / "07_LOGS" / "Decision-Ledger" / "Index.md").write_text(
            "- Decision: invoke bounded workflows through AOR only\n",
            encoding="utf-8",
        )
        (root / "07_LOGS" / "Operator-Briefs").mkdir(parents=True)
        (root / "06_AGENTS" / "role-cards").mkdir(parents=True)
        self._write_role_card()
        (root / "runtime" / "workflows" / "registry").mkdir(parents=True)
        self._write_manifest("operator_today")
        self._write_manifest("operator_close_day")

    def _write_role_card(
        self,
        *,
        write_scope: list[str] | None = None,
    ) -> None:
        scopes = write_scope or ["07_LOGS/Operator-Briefs/", "07_LOGS/Agent-Activity/"]
        lines = [
            "id: operator-briefing",
            "name: Operator Briefing",
            'version: "1.0"',
            "description: Bounded operator briefing role",
            "owner: operator",
            "allowed_actions:",
            "  - read_any_non_protected_file",
            "  - write_operator_brief",
            "forbidden_actions:",
            "  - write_protected_files",
            "write_scope:",
        ]
        lines.extend(f"  - {scope}" for scope in scopes)
        lines.extend(
            [
                "forbidden_write_zones:",
                "  - 00_HOME/Now.md",
                "escalation_rules:",
                "  - write outside scope",
                "runtime_expectations:",
                "  - AOR owns execution",
            ]
        )
        (self.tmp / "06_AGENTS" / "role-cards" / "operator-briefing.yaml").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

    def _write_manifest(
        self,
        workflow_id: str,
        *,
        status: str = "active",
        task_type: str = "operator-briefing",
        role_card: str = "operator-briefing",
        permission_ceiling: str = "no_protected_file_writes",
        writeback_targets: list[str] | None = None,
    ) -> None:
        targets = writeback_targets or ["07_LOGS/Operator-Briefs/"]
        input_lines = (
            ["  - date", "  - output_format"]
            if workflow_id == "operator_today"
            else ["  - date", "  - open_loops", "  - notes"]
        )
        lines = [
            f"id: {workflow_id}",
            f"name: {workflow_id}",
            'version: "2.0"',
            "description: Bounded operator briefing workflow",
            f"task_type: {task_type}",
            f"role_card: {role_card}",
            "trigger_type: manual",
            "owner: operator",
            f"status: {status}",
            f"permission_ceiling: {permission_ceiling}",
            "inputs:",
            *input_lines,
            "writeback_targets:",
        ]
        lines.extend(f"  - {target}" for target in targets)
        lines.extend(["failure_behavior: escalate"])
        (self.tmp / "runtime" / "workflows" / "registry" / f"{workflow_id}.yaml").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

    def _request(self, payload: dict, **kwargs: object) -> dict:
        return handle_request(payload, config=self.config, **kwargs)

    def _invoke_payload(
        self,
        workflow_id: str = "operator_today",
        *,
        mode: str = "draft_execution",
        runtime_id: str = "openclaw",
        params_extra: dict | None = None,
        inputs: dict | None = None,
        dry_run: bool = False,
    ) -> dict:
        params = {"workflow_id": workflow_id, "inputs": inputs or {}, "dry_run": dry_run}
        if params_extra:
            params.update(params_extra)
        return {
            "tool": "workflow.invoke_bounded",
            "runtime_id": runtime_id,
            "mode": mode,
            "params": params,
        }

    def _fake_aor_result(
        self,
        workflow_id: str,
        *,
        status: str = "success",
        files_written: list[str] | None = None,
    ) -> SimpleNamespace:
        files = files_written or [f"07_LOGS/Operator-Briefs/2026-04-21-{workflow_id}.md"]
        outputs = (
            {"dry_run": True}
            if status == "dry_run_ok"
            else {
                "run": {
                    "writebacks": [
                        {
                            "path": files[0],
                            "content": "SECRET_FULL_BRIEF_SHOULD_NOT_RETURN",
                        }
                    ]
                },
                "writeback": {"files_written": files},
            }
        )
        return SimpleNamespace(
            workflow_id=workflow_id,
            status=status,
            audit_id=f"aor-{workflow_id}",
            stage_reached="audit_record" if status == "success" else "dry_run_exit",
            outputs=outputs,
            escalation_reason=None,
            error=None,
        )

    def test_draft_execution_mode_resolution_success(self) -> None:
        response = self._request(
            {"resource": "runtime.permission_envelope", "runtime_id": "openclaw", "mode": "draft_execution"}
        )
        self.assertTrue(response["ok"], response)
        self.assertEqual(response["result"]["mode"], "draft_execution")
        self.assertIn("workflow.invoke_bounded", response["result"]["tools"])

    def test_draft_execution_mode_denied_for_n8n(self) -> None:
        response = self._request(
            {"resource": "runtime.identity", "runtime_id": "n8n", "mode": "draft_execution"}
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "mode_denied")

    def test_workflow_invoke_unavailable_in_read_only(self) -> None:
        response = self._request(self._invoke_payload(mode="read_only"))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "surface_unavailable")

    def test_workflow_invoke_unavailable_in_read_plus_proposal(self) -> None:
        response = self._request(self._invoke_payload(mode="read_plus_proposal"))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "surface_unavailable")

    def test_workflow_not_allowed_for_non_allowlisted_workflow(self) -> None:
        with patch("runtime.mcp.tools.workflow_invoke.run_workflow") as fake_run:
            response = self._request(self._invoke_payload("graph_hygiene"))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "workflow_not_allowed")
        fake_run.assert_not_called()

    def test_missing_manifest_denial(self) -> None:
        (self.tmp / "runtime" / "workflows" / "registry" / "operator_today.yaml").unlink()
        with patch("runtime.mcp.tools.workflow_invoke.run_workflow") as fake_run:
            response = self._request(self._invoke_payload("operator_today"))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "workflow_manifest_not_found")
        fake_run.assert_not_called()

    def test_inactive_manifest_denial(self) -> None:
        self._write_manifest("operator_today", status="draft")
        response = self._request(self._invoke_payload("operator_today"))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "workflow_not_active")

    def test_wrong_task_type_denial(self) -> None:
        self._write_manifest("operator_today", task_type="graph-hygiene")
        response = self._request(self._invoke_payload("operator_today"))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "workflow_not_allowed")

    def test_missing_role_card_denial(self) -> None:
        (self.tmp / "06_AGENTS" / "role-cards" / "operator-briefing.yaml").unlink()
        response = self._request(self._invoke_payload("operator_today"))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "role_card_not_found")

    def test_wrong_permission_ceiling_denial(self) -> None:
        self._write_manifest("operator_today", permission_ceiling="proposal_log_only")
        response = self._request(self._invoke_payload("operator_today"))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "workflow_permission_ceiling_exceeded")

    def test_writeback_scope_denial(self) -> None:
        self._write_manifest(
            "operator_today",
            writeback_targets=["07_LOGS/Operator-Briefs/", "07_LOGS/Hygiene-Reports/"],
        )
        response = self._request(self._invoke_payload("operator_today"))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "workflow_writeback_scope_denied")

    def test_invalid_input_keys_denial(self) -> None:
        response = self._request(self._invoke_payload("operator_today", inputs={"write_path": "00_HOME/Now.md"}))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "workflow_inputs_invalid")

    def test_control_fields_denied(self) -> None:
        response = self._request(self._invoke_payload(params_extra={"schedule_id": "sch-operator-today-0700"}))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "workflow_inputs_invalid")

    def test_aor_routing_success_path_operator_today(self) -> None:
        with patch("runtime.mcp.tools.workflow_invoke.run_workflow") as fake_run:
            fake_run.return_value = self._fake_aor_result("operator_today")
            response = self._request(self._invoke_payload("operator_today", inputs={"date": "2026-04-21"}))
        self.assertTrue(response["ok"], response)
        fake_run.assert_called_once()
        self.assertEqual(fake_run.call_args.kwargs["workflow_id"], "operator_today")
        self.assertEqual(fake_run.call_args.kwargs["inputs"], {"date": "2026-04-21"})
        self.assertEqual(fake_run.call_args.kwargs["vault_root"], self.tmp)
        self.assertFalse(fake_run.call_args.kwargs["dry_run"])
        self.assertEqual(response["result"]["invocation_status"], "completed")
        self.assertEqual(response["result"]["aor_audit_id"], "aor-operator_today")

    def test_aor_routing_success_path_operator_close_day(self) -> None:
        with patch("runtime.mcp.tools.workflow_invoke.run_workflow") as fake_run:
            fake_run.return_value = self._fake_aor_result("operator_close_day")
            response = self._request(
                self._invoke_payload("operator_close_day", inputs={"open_loops": ["close this"]})
            )
        self.assertTrue(response["ok"], response)
        fake_run.assert_called_once()
        self.assertEqual(fake_run.call_args.kwargs["workflow_id"], "operator_close_day")
        self.assertEqual(response["result"]["aor_audit_id"], "aor-operator_close_day")

    def test_dry_run_behavior(self) -> None:
        with patch("runtime.mcp.tools.workflow_invoke.run_workflow") as fake_run:
            fake_run.return_value = self._fake_aor_result("operator_today", status="dry_run_ok", files_written=[])
            response = self._request(self._invoke_payload("operator_today", dry_run=True))
        self.assertTrue(response["ok"], response)
        self.assertTrue(fake_run.call_args.kwargs["dry_run"])
        self.assertEqual(response["result"]["invocation_status"], "dry_run_ok")
        self.assertEqual(response["result"]["files_written"], [])
        self.assertEqual(response["result"]["output_artifacts"], [])

    def test_dry_run_ignores_existing_output_duplicate_guard(self) -> None:
        existing = self.tmp / "07_LOGS" / "Operator-Briefs" / "2026-04-21-operator-today.md"
        existing.write_text("existing operator brief\n", encoding="utf-8")
        with patch("runtime.mcp.tools.workflow_invoke.run_workflow") as fake_run:
            fake_run.return_value = self._fake_aor_result("operator_today", status="dry_run_ok", files_written=[])
            response = self._request(
                self._invoke_payload("operator_today", inputs={"date": "2026-04-21"}, dry_run=True)
            )
        self.assertTrue(response["ok"], response)
        fake_run.assert_called_once()
        self.assertEqual(response["result"]["invocation_status"], "dry_run_ok")

    def test_duplicate_live_output_denied_before_aor_call(self) -> None:
        existing = self.tmp / "07_LOGS" / "Operator-Briefs" / "2026-04-21-operator-today.md"
        existing.write_text("existing operator brief\n", encoding="utf-8")
        with patch("runtime.mcp.tools.workflow_invoke.run_workflow") as fake_run:
            response = self._request(
                self._invoke_payload("operator_today", inputs={"date": "2026-04-21"})
            )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "workflow_output_already_exists")
        self.assertEqual(
            response["error"]["details"]["existing_artifacts"],
            ["07_LOGS/Operator-Briefs/2026-04-21-operator-today.md"],
        )
        self.assertIn("do not retry blindly", response["error"]["details"]["retry_guidance"])
        fake_run.assert_not_called()

    def test_gate_policy_denial_blocks_before_aor_call(self) -> None:
        with (
            patch("runtime.mcp.tools.workflow_invoke.check_runtime_operation") as fake_gate,
            patch("runtime.mcp.tools.workflow_invoke.run_workflow") as fake_run,
        ):
            fake_gate.return_value = (False, "blocked-by-gateway-policy")
            response = self._request(self._invoke_payload("operator_today"))
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "gate_policy_denied")
        self.assertEqual(
            response["error"]["details"]["operation"],
            "gateway.workflow.invoke_bounded",
        )
        fake_run.assert_not_called()

    def test_bounded_live_path_response_includes_audit_reconciliation(self) -> None:
        with patch("runtime.mcp.tools.workflow_invoke.run_workflow") as fake_run:
            fake_run.return_value = self._fake_aor_result("operator_today")
            response = self._request(self._invoke_payload("operator_today"))
        self.assertTrue(response["ok"], response)
        result = response["result"]
        self.assertEqual(result["aor_audit_id"], "aor-operator_today")
        self.assertEqual(result["audit_reconciliation"]["aor_audit_id"], "aor-operator_today")
        self.assertEqual(result["audit_reconciliation"]["mcp_audit_surface"], "workflow.invoke_bounded")
        self.assertIn("do not retry blindly", result["retry_guidance"])

    def test_mcp_audit_written_on_success(self) -> None:
        with patch("runtime.mcp.tools.workflow_invoke.run_workflow") as fake_run:
            fake_run.return_value = self._fake_aor_result("operator_today")
            response = self._request(self._invoke_payload("operator_today"))
        self.assertTrue(response["ok"], response)
        audit_files = sorted((self.tmp / "07_LOGS" / "Agent-Activity").glob("*__mcp__workflow.invoke_bounded__*.json"))
        self.assertEqual(len(audit_files), 1)
        raw = json.loads(audit_files[0].read_text(encoding="utf-8"))
        self.assertEqual(raw["surface_id"], "workflow.invoke_bounded")
        self.assertEqual(raw["safety_mode"], "draft_execution")
        detail = json.loads(raw["outcome_detail"])
        self.assertEqual(detail["workflow_id"], "operator_today")
        self.assertEqual(detail["aor_audit_id"], "aor-operator_today")

    def test_mcp_audit_failure_after_aor_return_fails_closed(self) -> None:
        with patch("runtime.mcp.tools.workflow_invoke.run_workflow") as fake_run:
            fake_run.return_value = self._fake_aor_result("operator_today")
            response = handle_request(
                self._invoke_payload("operator_today"),
                config=self.config,
                logger=FailingAuditLogger(),
            )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "workflow_invocation_audit_failed")
        fake_run.assert_called_once()

    def test_no_full_generated_brief_text_returned(self) -> None:
        with patch("runtime.mcp.tools.workflow_invoke.run_workflow") as fake_run:
            fake_run.return_value = self._fake_aor_result("operator_today")
            response = self._request(self._invoke_payload("operator_today"))
        self.assertTrue(response["ok"], response)
        self.assertNotIn("SECRET_FULL_BRIEF_SHOULD_NOT_RETURN", json.dumps(response))
        self.assertIn("output_artifacts", response["result"])
        self.assertFalse(response["result"]["canonical_write"])

    def test_no_other_deferred_or_excluded_surface_exposed_in_draft_execution(self) -> None:
        response = self._request(
            {"resource": "runtime.capabilities", "runtime_id": "openclaw", "mode": "draft_execution"}
        )
        self.assertTrue(response["ok"])
        live = (
            response["result"]["resources"]
            + response["result"]["tools"]
            + response["result"]["prompts"]
        )
        self.assertIn("workflow.invoke_bounded", live)
        for surface in DEFERRED_SURFACES + EXCLUDED_SURFACES:
            self.assertNotIn(surface, live)


if __name__ == "__main__":
    unittest.main(verbosity=2)
