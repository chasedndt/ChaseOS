"""Runtime MCP ARSL summary exposure tests."""

from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[3]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.mcp.config import load_config
from runtime.mcp.server import handle_jsonrpc_message, handle_request


class RuntimeMCPRuntimeSurfacesTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = _VAULT_ROOT / ".codex_tmp_test"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = scratch / f"chaseos-mcp-runtime-surfaces-{uuid.uuid4().hex}"
        self.tmp.mkdir()
        self._populate_vault(self.tmp)
        self.config = load_config(vault_root=self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _populate_vault(self, root: Path) -> None:
        (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
        (root / "06_AGENTS").mkdir(parents=True)
        (root / "06_AGENTS" / "Permission-Matrix.md").write_text("# Permission Matrix\n", encoding="utf-8")
        (root / "06_AGENTS" / "Trust-Tiers.md").write_text("# Trust Tiers\n", encoding="utf-8")
        (root / "06_AGENTS" / "Test-ARSL.md").write_text("# Test ARSL\n", encoding="utf-8")
        (root / "runtime" / "test_surface.py").parent.mkdir(parents=True)
        (root / "runtime" / "test_surface.py").write_text("# test surface\n", encoding="utf-8")
        (root / "runtime" / "runtime_surfaces" / "manifests").mkdir(parents=True)
        manifest = {
            "schema_version": 1,
            "surface_id": "test.surface",
            "display_name": "Test Surface",
            "surface_family": "agent_runtime",
            "surface_type": "agent",
            "owner_layer": "runtime/test_surface.py",
            "status": "PARTIAL",
            "implementation_refs": ["runtime/test_surface.py"],
            "docs_refs": ["06_AGENTS/Test-ARSL.md"],
            "trust_ceiling": "tier-2",
            "permission_model_refs": ["06_AGENTS/Permission-Matrix.md", "06_AGENTS/Trust-Tiers.md"],
            "gate_operations": [],
            "capabilities": [
                {
                    "capability_id": "test.read",
                    "maps_to": "test_read",
                    "risk_class": "read_local_scoped",
                    "approval_required": False,
                }
            ],
            "credential_policy": {
                "credentials_allowed": False,
                "cookies_allowed": False,
                "real_profile_allowed": False,
            },
            "fallback_policy": {"sticky_fallback_allowed": False},
            "writeback_surfaces": ["07_LOGS/Agent-Activity/"],
            "audit_targets": ["07_LOGS/Agent-Activity/"],
            "routing_policy": {
                "default": "deny_unknown",
                "authority_layer": "runtime/test_surface.py",
            },
            "mcp_exposure_policy": {
                "expose_summary": True,
                "expose_raw_manifest": False,
            },
        }
        (root / "runtime" / "runtime_surfaces" / "manifests" / "test_surface.yaml").write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )

    def test_legacy_resource_returns_curated_summary_only(self) -> None:
        response = handle_request(
            {"resource": "runtime.surfaces", "runtime_id": "openclaw", "mode": "read_only"},
            config=self.config,
        )

        self.assertTrue(response["ok"], response)
        result = response["result"]
        self.assertEqual(result["feature_name"], "Adaptive Runtime Surface Layer")
        self.assertEqual(result["registry_status"], "available")
        self.assertFalse(result["exposure_policy"]["raw_manifest_exposed"])
        self.assertFalse(result["exposure_policy"]["execution_performed"])
        self.assertFalse(result["exposure_policy"]["ledger_written"])
        self.assertFalse(result["exposure_policy"]["provider_calls_performed"])
        self.assertFalse(result["exposure_policy"]["browser_control_performed"])
        self.assertEqual(result["registry"]["surface_count"], 1)
        self.assertEqual(result["registry"]["surfaces"][0]["surface_id"], "test.surface")
        self.assertEqual(result["capability_policy"]["records"][0]["capability_id"], "test.read")

        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("credential_policy", serialized)
        self.assertNotIn("fallback_policy", serialized)
        self.assertNotIn("implementation_refs", serialized)
        self.assertNotIn("writeback_surfaces", serialized)
        self.assertFalse((self.tmp / "runtime" / "runtime_surfaces" / "state" / "routing_decisions.jsonl").exists())

    def test_jsonrpc_alias_lists_and_reads_summary(self) -> None:
        context = {"_chaseos": {"runtime_id": "openclaw", "mode": "read_only"}}
        listing = handle_jsonrpc_message(
            {"jsonrpc": "2.0", "id": "list", "method": "resources/list", "params": context},
            config=self.config,
        )
        uris = [resource["uri"] for resource in listing["result"]["resources"]]
        self.assertIn("chaseos://resource/chaseos.runtime_surfaces_summary", uris)

        response = handle_jsonrpc_message(
            {
                "jsonrpc": "2.0",
                "id": "read",
                "method": "resources/read",
                "params": {
                    "uri": "chaseos://resource/chaseos.runtime_surfaces_summary",
                    **context,
                },
            },
            config=self.config,
        )
        content = response["result"]["contents"][0]
        decoded = json.loads(content["text"])
        self.assertEqual(decoded["resource"], "runtime.surfaces")
        self.assertFalse(decoded["exposure_policy"]["raw_manifest_exposed"])


if __name__ == "__main__":
    unittest.main()
