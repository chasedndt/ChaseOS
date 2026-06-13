"""Local process-boundary smoke proof for ChaseOS Runtime MCP stdio."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from runtime.mcp.stdio_client import MCPStdioSmokeClient


def _context(mode: str) -> dict[str, Any]:
    return {"_chaseos": {"runtime_id": "openclaw", "mode": mode}}


def _names(items: list[dict[str, Any]], field: str) -> list[str]:
    return [str(item.get(field)) for item in items if isinstance(item, dict)]


def run_local_smoke(
    *,
    vault_root: Path,
    cwd: Path | None = None,
    timeout_s: float = 5.0,
) -> dict[str, Any]:
    """Start Runtime MCP as a child process and exercise bounded JSON-RPC calls."""
    with MCPStdioSmokeClient(cwd=cwd, vault_root=vault_root, timeout_s=timeout_s) as client:
        initialize = client.request("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}})
        client.notify("notifications/initialized")

        resources = client.request("resources/list", _context("read_only"))
        current_state = client.request(
            "resources/read",
            {"uri": "chaseos://resource/chaseos.current_state", **_context("read_only")},
        )
        tools = client.request("tools/list", _context("read_plus_proposal"))
        canonical_check = client.request(
            "tools/call",
            {
                "name": "chaseos.validate_writeback_target",
                "arguments": {"target": "00_HOME/Now.md"},
                **_context("read_plus_proposal"),
            },
        )
        read_only_tool = client.request(
            "tools/call",
            {
                "name": "chaseos.validate_writeback_target",
                "arguments": {"target": "07_LOGS/Agent-Activity/client-smoke.md"},
                **_context("read_only"),
            },
        )
        prompts = client.request("prompts/list", _context("read_plus_proposal"))
        prompt = client.request(
            "prompts/get",
            {"name": "chaseos.risk_review_prompt", "arguments": {}, **_context("read_plus_proposal")},
        )
        ping = client.request("ping", {})

    resource_names = _names(resources.get("result", {}).get("resources", []), "name")
    tool_names = _names(tools.get("result", {}).get("tools", []), "name")
    prompt_names = _names(prompts.get("result", {}).get("prompts", []), "name")
    current_payload = json.loads(current_state["result"]["contents"][0]["text"])
    canonical_result = canonical_check["result"]["structuredContent"]

    return {
        "ok": True,
        "server": initialize["result"]["serverInfo"],
        "protocol_version": initialize["result"]["protocolVersion"],
        "resource_count": len(resource_names),
        "tool_count": len(tool_names),
        "prompt_count": len(prompt_names),
        "has_current_state": "chaseos.current_state" in resource_names,
        "has_validate_writeback_target": "chaseos.validate_writeback_target" in tool_names,
        "has_risk_review_prompt": "chaseos.risk_review_prompt" in prompt_names,
        "current_state_source": current_payload.get("source"),
        "canonical_target_allowed": canonical_result.get("allowed"),
        "canonical_writeback": canonical_result.get("canonical_writeback"),
        "read_only_tool_error_code": read_only_tool.get("error", {}).get("data", {}).get("chaseos_error", {}).get("code"),
        "prompt_message_count": len(prompt["result"]["messages"]),
        "ping_ok": ping.get("result") == {},
        "live_external_connection": False,
        "public_transport": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local ChaseOS Runtime MCP stdio smoke proof.")
    parser.add_argument("--vault-root", required=True, help="Vault root to expose to the local MCP child process.")
    parser.add_argument("--cwd", default=None, help="Working directory for the MCP child process.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Response timeout in seconds.")
    args = parser.parse_args(argv)
    result = run_local_smoke(
        vault_root=Path(args.vault_root),
        cwd=Path(args.cwd) if args.cwd else None,
        timeout_s=args.timeout,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
