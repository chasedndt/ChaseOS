"""Runtime MCP JSON-RPC stdio compatibility tests."""

from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from io import StringIO
from pathlib import Path

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[3]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.mcp.config import load_config
from runtime.mcp.server import handle_jsonrpc_message, run_server


class RuntimeMCPJsonRpcStdioTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = _VAULT_ROOT / ".codex_tmp_test"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = scratch / f"chaseos-mcp-jsonrpc-{uuid.uuid4().hex}"
        self.tmp.mkdir()
        self._populate_vault(self.tmp)
        self.config = load_config(vault_root=self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _populate_vault(self, root: Path) -> None:
        (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
        (root / "README.md").write_text("# ChaseOS\n\nRuntime MCP test vault.\n", encoding="utf-8")
        (root / "PROJECT_FOUNDATION.md").write_text("# Foundation\n", encoding="utf-8")
        (root / "00_HOME").mkdir(parents=True)
        (root / "00_HOME" / "Now.md").write_text(
            "# Now\n\n## Current Phase\nPhase 9 Runtime MCP compatibility.\n",
            encoding="utf-8",
        )
        (root / "01_PROJECTS" / "ChaseOS").mkdir(parents=True)
        (root / "01_PROJECTS" / "ChaseOS" / "ChaseOS-OS.md").write_text(
            "# ChaseOS OS\n\n## Open Loops\n- Keep MCP bounded.\n",
            encoding="utf-8",
        )
        (root / "06_AGENTS").mkdir(parents=True)
        (root / "06_AGENTS" / "Feature-Register.md").write_text(
            "| Feature | Status |\n| --- | --- |\n| ChaseOS Runtime MCP Server | PARTIAL |\n",
            encoding="utf-8",
        )
        (root / "runtime" / "policy" / "adapters").mkdir(parents=True)
        (root / "runtime" / "policy" / "adapters" / "openai.yaml").write_text(
            "status: shadow_proof\n",
            encoding="utf-8",
        )
        (root / "runtime" / "source_intelligence").mkdir(parents=True)
        (root / "runtime" / "source_intelligence" / "README.md").write_text(
            "# Source Intelligence\n\nEvidence workspace.\n",
            encoding="utf-8",
        )
        (root / "07_LOGS" / "Operator-Briefs").mkdir(parents=True)
        (root / "07_LOGS" / "Operator-Briefs" / "2026-04-27-brief.md").write_text(
            "# Operator Brief\n\nLatest brief.\n",
            encoding="utf-8",
        )

    def _request(self, message: dict) -> dict | None:
        return handle_jsonrpc_message(message, config=self.config)

    def _context(self, mode: str = "read_plus_proposal") -> dict:
        return {"_chaseos": {"runtime_id": "openclaw", "mode": mode}}

    def test_initialize_returns_mcp_capabilities(self) -> None:
        response = self._request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "unit-test", "version": "0"},
                },
            }
        )
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        result = response["result"]
        self.assertEqual(result["protocolVersion"], "2025-11-25")
        self.assertIn("resources", result["capabilities"])
        self.assertIn("tools", result["capabilities"])
        self.assertIn("prompts", result["capabilities"])
        self.assertEqual(result["serverInfo"]["name"], "chaseos-runtime-mcp")

    def test_initialized_notification_returns_no_response(self) -> None:
        response = self._request({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.assertIsNone(response)

    def test_resources_list_and_read_safe_resource(self) -> None:
        listing = self._request(
            {"jsonrpc": "2.0", "id": "r1", "method": "resources/list", "params": self._context("read_only")}
        )
        uris = [item["uri"] for item in listing["result"]["resources"]]
        self.assertIn("chaseos://resource/chaseos.current_state", uris)

        read_response = self._request(
            {
                "jsonrpc": "2.0",
                "id": "r2",
                "method": "resources/read",
                "params": {"uri": "chaseos://resource/chaseos.current_state", **self._context("read_only")},
            }
        )
        content = read_response["result"]["contents"][0]
        self.assertEqual(content["mimeType"], "application/json")
        decoded = json.loads(content["text"])
        self.assertFalse(decoded["canonical_writeback_allowed"])
        self.assertEqual(decoded["source"], "00_HOME/Now.md")

    def test_tools_call_validates_canonical_target_without_writing_canonical(self) -> None:
        tools = self._request(
            {"jsonrpc": "2.0", "id": "t1", "method": "tools/list", "params": self._context()}
        )
        names = [item["name"] for item in tools["result"]["tools"]]
        self.assertIn("chaseos.validate_writeback_target", names)

        response = self._request(
            {
                "jsonrpc": "2.0",
                "id": "t2",
                "method": "tools/call",
                "params": {
                    "name": "chaseos.validate_writeback_target",
                    "arguments": {"target": "00_HOME/Now.md"},
                    **self._context(),
                },
            }
        )
        result = response["result"]["structuredContent"]
        self.assertFalse(result["allowed"])
        self.assertFalse(result["canonical_writeback"])

    def test_tools_call_blocks_tools_in_read_only_mode(self) -> None:
        response = self._request(
            {
                "jsonrpc": "2.0",
                "id": "t3",
                "method": "tools/call",
                "params": {
                    "name": "chaseos.validate_writeback_target",
                    "arguments": {"target": "07_LOGS/Agent-Activity/test.md"},
                    **self._context("read_only"),
                },
            }
        )
        self.assertEqual(response["error"]["code"], -32602)
        self.assertEqual(response["error"]["data"]["chaseos_error"]["code"], "surface_unavailable")

    def test_prompts_list_and_get_safe_prompt(self) -> None:
        listing = self._request(
            {"jsonrpc": "2.0", "id": "p1", "method": "prompts/list", "params": self._context()}
        )
        names = [item["name"] for item in listing["result"]["prompts"]]
        self.assertIn("chaseos.risk_review_prompt", names)

        response = self._request(
            {
                "jsonrpc": "2.0",
                "id": "p2",
                "method": "prompts/get",
                "params": {"name": "chaseos.risk_review_prompt", "arguments": {}, **self._context()},
            }
        )
        message = response["result"]["messages"][0]
        self.assertEqual(message["role"], "user")
        self.assertIn("credential", message["content"]["text"].lower())

    def test_unknown_method_returns_jsonrpc_method_not_found(self) -> None:
        response = self._request({"jsonrpc": "2.0", "id": "x1", "method": "unknown/method", "params": {}})
        self.assertEqual(response["error"]["code"], -32601)

    def test_run_server_writes_responses_and_skips_notifications(self) -> None:
        lines = "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}}),
            ]
        )
        output = StringIO()
        exit_code = run_server(stdin=StringIO(lines + "\n"), stdout=output, vault_root=self.tmp)
        self.assertEqual(exit_code, 0)
        responses = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([response["id"] for response in responses], [1, 2])
        self.assertEqual(responses[1]["result"], {})


if __name__ == "__main__":
    unittest.main()
