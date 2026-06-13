from __future__ import annotations

import json
import shutil
import sys
import threading
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.adapters.n8n.mcp_connection import (
    build_connection_readiness,
    probe_instance_mcp,
    resolve_connection,
)


class N8NMCPConnectionTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = _VAULT_ROOT / ".codex_tmp_test"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = scratch / f"n8n-mcp-connection-{uuid.uuid4().hex}"
        self.tmp.mkdir()
        self.config_path = self.tmp / "n8n_config.yaml"
        self.registry_path = self.tmp / "n8n_workflows.yaml"
        self._write_config(enabled=False, secrets_configured=False)
        shutil.copyfile(_VAULT_ROOT / "runtime/policy/adapters/n8n_workflows.yaml", self.registry_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_config(
        self,
        *,
        enabled: bool,
        secrets_configured: bool,
        local_only: bool = True,
    ) -> None:
        self.config_path.write_text(
            "\n".join(
                [
                    'config_id: "test-n8n-mcp"',
                    'adapter_id: "n8n-workflow"',
                    'status: "test"',
                    "deployment:",
                    f"  enabled: {str(enabled).lower()}",
                    '  base_url_env_var: "N8N_BASE_URL"',
                    '  mcp_access_token_env_var: "N8N_MCP_ACCESS_TOKEN"',
                    '  mcp_http_path: "/mcp-server/http"',
                    f"  local_only: {str(local_only).lower()}",
                    f"  secrets_configured: {str(secrets_configured).lower()}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def test_default_config_blocks_live_probe_without_env_or_enablement(self) -> None:
        readiness = build_connection_readiness(
            config_path=self.config_path,
            registry_path=self.registry_path,
            environ={},
        )
        self.assertFalse(readiness["ok"])
        self.assertFalse(readiness["live_http_call"])
        self.assertTrue(readiness["registry"]["ok"], readiness["registry"]["errors"])
        self.assertIn("capture_research_digest", readiness["registry"]["exposed_to_mcp"])
        self.assertIn("deployment.enabled is false", readiness["connection"]["blocked_reasons"])
        self.assertIn("N8N_MCP_ACCESS_TOKEN is not set", readiness["connection"]["blocked_reasons"])
        self.assertFalse(readiness["forbidden"]["credential_values_logged"])
        self.assertFalse(readiness["forbidden"]["trading_execution"])

        probe = probe_instance_mcp(config_path=self.config_path, environ={})
        self.assertFalse(probe["ok"])
        self.assertTrue(probe["blocked"])
        self.assertFalse(probe["live_http_call"])

    def test_non_local_base_url_is_blocked_by_default(self) -> None:
        self._write_config(enabled=True, secrets_configured=True)
        connection = resolve_connection(
            config_path=self.config_path,
            environ={"N8N_BASE_URL": "https://example.com", "N8N_MCP_ACCESS_TOKEN": "secret-token"},
        )
        self.assertFalse(connection.safe_to_probe)
        self.assertIn("non-local n8n base URL requires explicit approval", connection.blocked_reasons)

    def test_local_live_probe_uses_bearer_token_and_redacts_value(self) -> None:
        self._write_config(enabled=True, secrets_configured=True)
        server = _ProbeServer()
        server.start()
        try:
            base_url = f"http://127.0.0.1:{server.port}"
            result = probe_instance_mcp(
                config_path=self.config_path,
                environ={"N8N_BASE_URL": base_url, "N8N_MCP_ACCESS_TOKEN": "unit-secret"},
                timeout_s=5,
            )
        finally:
            server.stop()

        self.assertTrue(result["ok"], result)
        self.assertTrue(result["live_http_call"])
        self.assertFalse(result["blocked"])
        self.assertEqual(result["http_status"], 200)
        self.assertEqual(result["connection"]["mcp_server_url"], f"{base_url}/mcp-server/http")
        self.assertTrue(result["connection"]["token_present"])
        self.assertNotIn("unit-secret", json.dumps(result))
        self.assertEqual(server.last_authorization, "Bearer unit-secret")
        self.assertEqual(server.last_path, "/mcp-server/http")


class _ProbeHandler(BaseHTTPRequestHandler):
    server: "_HTTPProbeServer"

    def do_POST(self) -> None:  # noqa: N802
        self.server.last_path = self.path
        self.server.last_authorization = self.headers.get("Authorization")
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length)
        payload = json.loads(raw.decode("utf-8"))
        response = {
            "jsonrpc": "2.0",
            "id": payload.get("id"),
            "result": {
                "protocolVersion": "2025-11-25",
                "serverInfo": {"name": "n8n-mcp-test", "version": "0"},
                "capabilities": {"tools": {}},
            },
        }
        body = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class _HTTPProbeServer(ThreadingHTTPServer):
    last_authorization: str | None = None
    last_path: str | None = None


class _ProbeServer:
    def __init__(self) -> None:
        self.httpd = _HTTPProbeServer(("127.0.0.1", 0), _ProbeHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    @property
    def port(self) -> int:
        return int(self.httpd.server_address[1])

    @property
    def last_authorization(self) -> str | None:
        return self.httpd.last_authorization

    @property
    def last_path(self) -> str | None:
        return self.httpd.last_path

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
