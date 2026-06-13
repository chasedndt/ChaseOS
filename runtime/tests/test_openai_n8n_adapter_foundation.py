from __future__ import annotations

import shutil
import sys
import unittest
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from runtime.adapters.n8n.workflow_policy import (
    N8NWorkflowPolicyError,
    build_n8n_call_draft,
    load_workflow_registry,
    validate_registry,
)
from runtime.adapters.openai.responses_mcp_payload import (
    ResponsesMCPPolicyError,
    build_responses_mcp_payload,
    validate_payload_policy,
)
from runtime.aor.engine import run_workflow
from runtime.aor.registry import load_manifest
from runtime.aor.role_cards import load_card
from runtime.mcp.config import load_config
from runtime.mcp.server import handle_request


class AdapterFoundationTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = _VAULT_ROOT / ".codex_tmp_test"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = scratch / f"openai-n8n-foundation-{uuid.uuid4().hex}"
        self.tmp.mkdir()
        self._populate_vault(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _copy(self, rel: str) -> None:
        source = _VAULT_ROOT / rel
        dest = self.tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    def _populate_vault(self, root: Path) -> None:
        for directory in [
            "00_HOME",
            "06_AGENTS/role-cards",
            "07_LOGS/Agent-Activity",
            "07_LOGS/Build-Logs",
            "07_LOGS/Operator-Briefs/_drafts",
            "runtime/aor",
            "runtime/policy/adapters",
            "runtime/workflows/registry",
        ]:
            (root / directory).mkdir(parents=True, exist_ok=True)

        (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
        (root / "README.md").write_text("# ChaseOS\nPhase 9 active.\n", encoding="utf-8")
        (root / "ROADMAP.md").write_text("# ROADMAP\nPhase 9 current.\n", encoding="utf-8")
        (root / "00_HOME" / "Now.md").write_text(
            "# Now\n\n## Current Phase\nPhase 9 active.\n",
            encoding="utf-8",
        )
        (root / "06_AGENTS" / "OpenAI-Adapter-Spec.md").write_text("# OpenAI Adapter Spec\n", encoding="utf-8")
        (root / "06_AGENTS" / "Responses-MCP-Binding.md").write_text("# Responses MCP Binding\n", encoding="utf-8")
        (root / "06_AGENTS" / "N8N-MCP-Hub-Spec.md").write_text("# n8n MCP Hub\n", encoding="utf-8")
        (root / "runtime" / "source_intelligence").mkdir(parents=True, exist_ok=True)
        (root / "runtime" / "source_intelligence" / "README.md").write_text("# SIC\n", encoding="utf-8")

        self._copy("runtime/aor/task_type_table.yaml")
        # Write an active fixture — real file is deprecated (M-3); tests need status=active
        # so the engine can reach permission_ceiling checks.
        (root / "runtime/workflows/registry/openai_operator_research_shadow.yaml").write_text(
            "id: openai_operator_research_shadow\n"
            "name: OpenAI Operator Research Shadow\n"
            "version: '1.0'\n"
            "description: 'Bounded local OpenAI shadow workflow.'\n"
            "task_type: openai-operator-research-shadow\n"
            "role_card: openai-operator-shadow\n"
            "trigger_type: manual\n"
            "owner: ChaseOS\n"
            "status: active\n"
            "permission_ceiling: shadow_log_only\n"
            "writeback_targets:\n"
            "  - '07_LOGS/Operator-Briefs/_drafts/'\n"
            "  - '07_LOGS/Agent-Activity/'\n"
            "failure_behavior: escalate\n"
            "runtime_adapter: openai\n"
            "required_reads:\n"
            "  - '00_HOME/Now.md'\n"
            "  - 'README.md'\n"
            "  - 'ROADMAP.md'\n"
            "  - '06_AGENTS/OpenAI-Adapter-Spec.md'\n"
            "  - '06_AGENTS/Responses-MCP-Binding.md'\n"
            "  - '06_AGENTS/N8N-MCP-Hub-Spec.md'\n"
            "notes: 'No live OpenAI call, no live n8n call, no Discord send, no canonical mutation.'\n",
            encoding="utf-8",
        )
        self._copy("06_AGENTS/role-cards/openai-operator-shadow.yaml")
        self._copy("runtime/policy/adapters/openai_config.yaml")
        self._copy("runtime/policy/adapters/n8n_workflows.yaml")
        self._copy("runtime/policy/adapters/openai.yaml")
        self._copy("runtime/policy/adapters/n8n.yaml")
        self._copy("runtime/policy/adapters/responses_api.yaml")

    def test_openai_adapter_config_manifest_and_role_card_load(self) -> None:
        if yaml is None:
            self.skipTest("PyYAML is required for adapter config validation in this repo")
        config = yaml.safe_load((_VAULT_ROOT / "runtime/policy/adapters/openai_config.yaml").read_text(encoding="utf-8"))
        self.assertEqual(config["status"], "shadow_proof")
        self.assertFalse(config["live_api_calls"]["enabled"])
        self.assertFalse(config["canonical_writeback"]["enabled"])

        manifest = load_manifest("openai_operator_research_shadow", self.tmp)
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["task_type"], "openai-operator-research-shadow")

        role_card = load_card("openai-operator-shadow", self.tmp)
        self.assertIsNotNone(role_card)
        self.assertIn("07_LOGS/Operator-Briefs/_drafts/", role_card["write_scope"])

    def test_openai_shadow_workflow_writes_only_draft_and_audit_targets(self) -> None:
        result = run_workflow(
            "openai_operator_research_shadow",
            inputs={"run_label": "unit-test"},
            vault_root=self.tmp,
            runtime_id="openai",
        )
        self.assertEqual(result.status, "success", result.error or result.escalation_reason)
        written = result.outputs["writeback"]["files_written"]
        self.assertEqual(len(written), 2)
        for rel in written:
            self.assertTrue(
                rel.startswith("07_LOGS/Operator-Briefs/_drafts/")
                or rel.startswith("07_LOGS/Agent-Activity/")
            )

    def test_openai_shadow_refuses_canonical_write_target(self) -> None:
        result = run_workflow(
            "openai_operator_research_shadow",
            inputs={"write_path": "00_HOME/Now.md"},
            vault_root=self.tmp,
            runtime_id="openai",
        )
        self.assertEqual(result.status, "escalated")
        self.assertEqual(result.stage_reached, "permission_ceiling")

    def test_responses_mcp_payload_builder_dry_run_shape_and_blocks_forbidden(self) -> None:
        payload = build_responses_mcp_payload(
            prompt="Prepare a source lookup draft.",
            server_label="chaseos_runtime_mcp",
            server_url="https://example.invalid/mcp",
            allowed_tools=["chaseos.current_state"],
        )
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["metadata"]["live_api_call"])
        self.assertEqual(payload["tools"][0]["require_approval"], "always")
        self.assertTrue(validate_payload_policy(payload)["ok"])

        with self.assertRaises(ResponsesMCPPolicyError):
            build_responses_mcp_payload(
                prompt="trade",
                server_label="bad",
                server_url="https://example.invalid/mcp",
                allowed_tools=["execute_trade"],
            )

    def test_n8n_workflow_registry_validates_and_blocks_unapproved_production(self) -> None:
        registry_path = self.tmp / "runtime/policy/adapters/n8n_workflows.yaml"
        registry = load_workflow_registry(registry_path)
        verdict = validate_registry(registry)
        self.assertTrue(verdict["ok"], verdict["errors"])

        draft = build_n8n_call_draft(
            workflow_id="capture_research_digest",
            registry_path=registry_path,
            caller="openai_operator_research_shadow",
            payload={"brief": "draft"},
        )
        self.assertTrue(draft["dry_run"])
        self.assertFalse(draft["live_http_call"])

        with self.assertRaises(N8NWorkflowPolicyError):
            build_n8n_call_draft(
                workflow_id="capture_research_digest",
                registry_path=registry_path,
                caller="openai_operator_research_shadow",
                production=True,
                approved=False,
            )

    def test_chaseos_mcp_lists_allowed_surfaces_and_rejects_forbidden_target(self) -> None:
        config = load_config(vault_root=self.tmp)
        envelope = handle_request(
            {"resource": "runtime.permission_envelope", "runtime_id": "openclaw", "mode": "read_plus_proposal"},
            config=config,
        )
        self.assertTrue(envelope["ok"])
        resources = envelope["result"]["resources"]
        tools = envelope["result"]["tools"]
        prompts = envelope["result"]["prompts"]
        self.assertIn("chaseos.current_state", resources)
        self.assertIn("chaseos.validate_writeback_target", tools)
        self.assertIn("chaseos.risk_review_prompt", prompts)

        response = handle_request(
            {
                "tool": "chaseos.validate_writeback_target",
                "runtime_id": "openclaw",
                "mode": "read_plus_proposal",
                "params": {"target": "00_HOME/Now.md"},
            },
            config=config,
        )
        self.assertTrue(response["ok"])
        self.assertFalse(response["result"]["allowed"])


if __name__ == "__main__":
    unittest.main()
