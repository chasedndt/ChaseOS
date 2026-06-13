"""Process-boundary Runtime MCP stdio client smoke tests."""

from __future__ import annotations

import shutil
import sys
import unittest
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[3]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.mcp.client_smoke import run_local_smoke
from runtime.mcp.stdio_client import MCPStdioSmokeClient


class RuntimeMCPStdioClientSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = _VAULT_ROOT / ".codex_tmp_test"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = scratch / f"chaseos-mcp-client-smoke-{uuid.uuid4().hex}"
        self.tmp.mkdir()
        self._populate_vault(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _populate_vault(self, root: Path) -> None:
        (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
        (root / "README.md").write_text("# ChaseOS\n\nRuntime MCP client smoke vault.\n", encoding="utf-8")
        (root / "PROJECT_FOUNDATION.md").write_text("# Foundation\n", encoding="utf-8")
        (root / "00_HOME").mkdir(parents=True)
        (root / "00_HOME" / "Now.md").write_text(
            "# Now\n\n## Current Phase\nPhase 9 Runtime MCP client smoke.\n",
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

    def test_local_smoke_runs_against_subprocess_stdio_server(self) -> None:
        now_path = self.tmp / "00_HOME" / "Now.md"
        before = now_path.read_text(encoding="utf-8")

        result = run_local_smoke(vault_root=self.tmp, cwd=_VAULT_ROOT, timeout_s=10)

        self.assertTrue(result["ok"])
        self.assertEqual(result["server"]["name"], "chaseos-runtime-mcp")
        self.assertEqual(result["protocol_version"], "2025-11-25")
        self.assertTrue(result["has_current_state"])
        self.assertTrue(result["has_validate_writeback_target"])
        self.assertTrue(result["has_risk_review_prompt"])
        self.assertEqual(result["current_state_source"], "00_HOME/Now.md")
        self.assertFalse(result["canonical_target_allowed"])
        self.assertFalse(result["canonical_writeback"])
        self.assertEqual(result["read_only_tool_error_code"], "surface_unavailable")
        self.assertTrue(result["ping_ok"])
        self.assertFalse(result["live_external_connection"])
        self.assertFalse(result["public_transport"])
        self.assertEqual(now_path.read_text(encoding="utf-8"), before)

        audit_dir = self.tmp / "07_LOGS" / "Agent-Activity"
        audit_files = list(audit_dir.glob("*.json")) if audit_dir.exists() else []
        self.assertGreaterEqual(len(audit_files), 3)

    def test_notification_does_not_emit_response_before_ping(self) -> None:
        with MCPStdioSmokeClient(cwd=_VAULT_ROOT, vault_root=self.tmp, timeout_s=10) as client:
            initialize = client.request("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}})
            client.notify("notifications/initialized")
            ping = client.request("ping", {}, request_id="after-notification")

        self.assertEqual(initialize["result"]["serverInfo"]["name"], "chaseos-runtime-mcp")
        self.assertEqual(ping["id"], "after-notification")
        self.assertEqual(ping["result"], {})


if __name__ == "__main__":
    unittest.main()
