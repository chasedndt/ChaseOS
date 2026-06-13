from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.adapters.n8n.call_governance import (
    CALL_DRAFT_DIR,
    APPROVAL_DIR,
    N8NCallGovernanceError,
    build_governed_call_draft,
    create_approval_request,
    load_approval_request,
    record_approval_decision,
    resolve_approval_state,
    write_governed_call_draft,
)
from runtime.adapters.n8n.workflow_policy import N8NWorkflowPolicyError, build_n8n_call_draft


class N8NCallGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = _VAULT_ROOT / ".codex_tmp_test"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = scratch / f"n8n-call-governance-{uuid.uuid4().hex}"
        self.tmp.mkdir()
        self.registry_path = self.tmp / "n8n_workflows.yaml"
        self._write_registry(current_status="active")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_registry(self, *, current_status: str = "dry_run_candidate") -> None:
        self.registry_path.write_text(
            "\n".join(
                [
                    'registry_id: "test-n8n-workflows"',
                    'status: "test"',
                    'owner: "ChaseOS"',
                    "workflows:",
                    '  - workflow_id: "capture_research_digest"',
                    '    purpose: "Capture a research digest draft into quarantine or draft logs after approval."',
                    "    exposed_to_mcp: true",
                    '    trigger_type: "mcp_tool"',
                    "    approval_required: true",
                    "    allowed_callers:",
                    '      - "openai_operator_research_shadow"',
                    '      - "chaseos_runtime_mcp"',
                    "    reads:",
                    '      - "07_LOGS/Operator-Briefs/_drafts/"',
                    "    writes:",
                    '      - "03_INPUTS/00_QUARANTINE/"',
                    '      - "07_LOGS/Agent-Activity/"',
                    "    secrets_required: []",
                    f'    current_status: "{current_status}"',
                    "",
                    '  - workflow_id: "execute_trade_order"',
                    '    purpose: "Blocked live trading workflow placeholder; must not be exposed or executed."',
                    "    exposed_to_mcp: false",
                    '    trigger_type: "manual"',
                    "    approval_required: true",
                    "    allowed_callers:",
                    '      - "chaseos_runtime_mcp"',
                    "    reads: []",
                    "    writes: []",
                    "    secrets_required:",
                    '      - "exchange_api_key_reference"',
                    '    current_status: "blocked"',
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def test_approval_request_and_decision_are_audited_without_payload_or_secrets(self) -> None:
        request = create_approval_request(
            vault_root=self.tmp,
            registry_path=self.registry_path,
            workflow_id="capture_research_digest",
            caller="openai_operator_research_shadow",
            requested_by="Codex",
            reason="unit test approval request",
            payload={"brief": "draft"},
            production_requested=True,
        )
        request_path = Path(request["path"])
        self.assertTrue(request_path.exists())
        self.assertEqual(request_path.parent, self.tmp / APPROVAL_DIR)
        self.assertFalse(request["payload_values_logged"])
        self.assertFalse(request["credential_values_logged"])
        self.assertFalse(request["live_http_call"])
        self.assertNotIn("draft", request_path.read_text(encoding="utf-8"))

        loaded = load_approval_request(vault_root=self.tmp, approval_id=request["approval_id"])
        self.assertEqual(loaded["payload_digest_sha256"], request["payload_digest_sha256"])

        decision = record_approval_decision(
            vault_root=self.tmp,
            approval_id=request["approval_id"],
            workflow_id="capture_research_digest",
            caller="openai_operator_research_shadow",
            decision="approved",
            decided_by="operator",
            reason="approved for dry-run production policy validation",
        )
        self.assertTrue(Path(decision["path"]).exists())
        self.assertFalse(decision["live_http_call"])

    def test_production_governed_call_requires_approved_decision(self) -> None:
        request = create_approval_request(
            vault_root=self.tmp,
            registry_path=self.registry_path,
            workflow_id="capture_research_digest",
            caller="openai_operator_research_shadow",
            requested_by="Codex",
            reason="pending request",
            payload={"brief": "draft"},
        )
        with self.assertRaises(N8NCallGovernanceError):
            build_governed_call_draft(
                vault_root=self.tmp,
                registry_path=self.registry_path,
                workflow_id="capture_research_digest",
                caller="openai_operator_research_shadow",
                payload={"brief": "draft"},
                production=True,
                approval_id=request["approval_id"],
            )

    def test_approved_production_governed_call_still_writes_dry_run_audit_only(self) -> None:
        request = create_approval_request(
            vault_root=self.tmp,
            registry_path=self.registry_path,
            workflow_id="capture_research_digest",
            caller="openai_operator_research_shadow",
            requested_by="Codex",
            reason="approval for active dry-run call draft",
            payload={"brief": "draft"},
        )
        record_approval_decision(
            vault_root=self.tmp,
            approval_id=request["approval_id"],
            workflow_id="capture_research_digest",
            caller="openai_operator_research_shadow",
            decision="approved",
            decided_by="operator",
            reason="approved",
        )
        draft = build_governed_call_draft(
            vault_root=self.tmp,
            registry_path=self.registry_path,
            workflow_id="capture_research_digest",
            caller="openai_operator_research_shadow",
            payload={"brief": "draft"},
            production=True,
            approval_id=request["approval_id"],
        )
        self.assertTrue(draft["dry_run"])
        self.assertFalse(draft["live_http_call"])
        self.assertTrue(draft["production_requested"])
        self.assertEqual(draft["governance"]["approval_state"], "approved")
        self.assertFalse(draft["governance"]["can_execute_live"])
        self.assertFalse(draft["governance"]["credential_values_logged"])

        out_path = write_governed_call_draft(draft, vault_root=self.tmp, descriptor="unit-governed-call")
        self.assertTrue(out_path.exists())
        self.assertEqual(out_path.parent, self.tmp / CALL_DRAFT_DIR)
        written = json.loads(out_path.read_text(encoding="utf-8"))
        self.assertFalse(written["governance"]["canonical_writeback"])
        self.assertFalse(written["governance"]["http_execution_enabled"])

    def test_denied_or_mismatched_approval_blocks_production_call(self) -> None:
        request = create_approval_request(
            vault_root=self.tmp,
            registry_path=self.registry_path,
            workflow_id="capture_research_digest",
            caller="openai_operator_research_shadow",
            requested_by="Codex",
            reason="denied request",
        )
        record_approval_decision(
            vault_root=self.tmp,
            approval_id=request["approval_id"],
            workflow_id="capture_research_digest",
            caller="openai_operator_research_shadow",
            decision="denied",
            decided_by="operator",
            reason="denied",
        )
        state = resolve_approval_state(
            vault_root=self.tmp,
            approval_id=request["approval_id"],
            workflow_id="capture_research_digest",
            caller="openai_operator_research_shadow",
        )
        self.assertEqual(state["state"], "denied")
        self.assertFalse(state["approved"])

        with self.assertRaises(N8NCallGovernanceError):
            build_governed_call_draft(
                vault_root=self.tmp,
                registry_path=self.registry_path,
                workflow_id="capture_research_digest",
                caller="openai_operator_research_shadow",
                production=True,
                approval_id=request["approval_id"],
            )

        with self.assertRaises(N8NCallGovernanceError):
            resolve_approval_state(
                vault_root=self.tmp,
                approval_id=request["approval_id"],
                workflow_id="capture_research_digest",
                caller="chaseos_runtime_mcp",
            )

    def test_secret_like_payload_keys_are_rejected_before_audit_write(self) -> None:
        with self.assertRaises(N8NCallGovernanceError):
            create_approval_request(
                vault_root=self.tmp,
                registry_path=self.registry_path,
                workflow_id="capture_research_digest",
                caller="openai_operator_research_shadow",
                requested_by="Codex",
                reason="bad payload",
                payload={"api_token": "do-not-log"},
            )

        with self.assertRaises(N8NCallGovernanceError):
            build_governed_call_draft(
                vault_root=self.tmp,
                registry_path=self.registry_path,
                workflow_id="capture_research_digest",
                caller="openai_operator_research_shadow",
                payload={"nested": {"credential_name": "unsafe"}},
            )

    def test_blocked_trading_workflow_cannot_be_drafted(self) -> None:
        with self.assertRaises(N8NWorkflowPolicyError):
            build_n8n_call_draft(
                workflow_id="execute_trade_order",
                registry_path=self.registry_path,
                caller="chaseos_runtime_mcp",
            )
        with self.assertRaises(N8NCallGovernanceError):
            build_governed_call_draft(
                vault_root=self.tmp,
                registry_path=self.registry_path,
                workflow_id="execute_trade_order",
                caller="chaseos_runtime_mcp",
            )


if __name__ == "__main__":
    unittest.main()
