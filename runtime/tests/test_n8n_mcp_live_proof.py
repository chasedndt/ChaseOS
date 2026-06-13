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

from runtime.adapters.n8n.mcp_live_proof import (
    PROOF_DIR,
    build_mcp_connection_proof,
    write_mcp_connection_proof,
)


class N8NMCPLiveProofTests(unittest.TestCase):
    def setUp(self) -> None:
        scratch = _VAULT_ROOT / ".codex_tmp_test"
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = scratch / f"n8n-mcp-live-proof-{uuid.uuid4().hex}"
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

    def test_blocked_readiness_proof_writes_redacted_no_live_artifact(self) -> None:
        proof = build_mcp_connection_proof(
            config_path=self.config_path,
            registry_path=self.registry_path,
            environ={},
        )
        self.assertFalse(proof["ok"])
        self.assertEqual(proof["proof_status"], "blocked")
        self.assertFalse(proof["live_http_call"])
        self.assertFalse(proof["live_probe_attempted"])
        self.assertIn("deployment.enabled is false", proof["blocked_reasons"])

        out_path = write_mcp_connection_proof(proof, vault_root=self.tmp, descriptor="unit-blocked")
        self.assertEqual(out_path.parent, self.tmp / PROOF_DIR)
        written = json.loads(out_path.read_text(encoding="utf-8"))
        self.assertFalse(written["credential_values_logged"])
        self.assertFalse(written["canonical_writeback"])

    def test_ready_without_live_probe_does_not_call_http(self) -> None:
        self._write_config(enabled=True, secrets_configured=True)
        proof = build_mcp_connection_proof(
            config_path=self.config_path,
            registry_path=self.registry_path,
            environ={"N8N_BASE_URL": "http://127.0.0.1:5678", "N8N_MCP_ACCESS_TOKEN": "unit-secret"},
            live_probe=False,
        )
        self.assertTrue(proof["ok"])
        self.assertEqual(proof["proof_status"], "ready_not_probed")
        self.assertFalse(proof["live_http_call"])
        self.assertFalse(proof["live_probe_attempted"])
        self.assertNotIn("unit-secret", json.dumps(proof))

    def test_live_probe_summary_is_redacted_and_auditable(self) -> None:
        self._write_config(enabled=True, secrets_configured=True)
        server = _ProbeServer()
        server.start()
        try:
            base_url = f"http://127.0.0.1:{server.port}"
            proof = build_mcp_connection_proof(
                config_path=self.config_path,
                registry_path=self.registry_path,
                environ={"N8N_BASE_URL": base_url, "N8N_MCP_ACCESS_TOKEN": "unit-secret"},
                live_probe=True,
                timeout_s=5,
            )
        finally:
            server.stop()

        self.assertTrue(proof["ok"], proof)
        self.assertEqual(proof["proof_status"], "live_probe_passed")
        self.assertTrue(proof["live_http_call"])
        self.assertTrue(proof["live_probe_attempted"])
        self.assertEqual(proof["probe"]["server_info"]["name"], "n8n-mcp-test")
        self.assertNotIn("unit-secret", json.dumps(proof))
        self.assertEqual(server.last_authorization, "Bearer unit-secret")

        out_path = write_mcp_connection_proof(proof, vault_root=self.tmp, descriptor="unit-live")
        self.assertNotIn("unit-secret", out_path.read_text(encoding="utf-8"))

    def test_non_local_url_blocks_live_probe_before_http(self) -> None:
        self._write_config(enabled=True, secrets_configured=True)
        proof = build_mcp_connection_proof(
            config_path=self.config_path,
            registry_path=self.registry_path,
            environ={"N8N_BASE_URL": "https://example.com", "N8N_MCP_ACCESS_TOKEN": "unit-secret"},
            live_probe=True,
        )
        self.assertFalse(proof["ok"])
        self.assertEqual(proof["proof_status"], "blocked_before_live_probe")
        self.assertFalse(proof["live_http_call"])
        self.assertFalse(proof["live_probe_attempted"])
        self.assertIn("non-local n8n base URL requires explicit approval", proof["blocked_reasons"])
        self.assertNotIn("unit-secret", json.dumps(proof))


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
                "capabilities": {"tools": {}, "resources": {}},
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

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
