"""Tests for Hermes review synthesis through the shared execution adapter."""

from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path
from unittest.mock import patch


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.agent_bus.bus import create_task, init_db  # noqa: E402
from runtime.providers.state_ledger import load_provider_state_events  # noqa: E402
from runtime.workflows.hermes_review_execute import (  # noqa: E402
    _execute_synthesis,
    run_hermes_review_execute,
)


def _make_vault() -> Path:
    vault = _VAULT_ROOT / ".codex_tmp_test" / "hermes-review-shared-adapter" / uuid.uuid4().hex / "vault"
    vault.mkdir(parents=True)
    (vault / "07_LOGS" / "Build-Logs").mkdir(parents=True)
    (vault / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    (vault / "runtime" / "hermes").mkdir(parents=True)
    (vault / "runtime" / "hermes" / "model_config.yaml").write_text(
        "\n".join(
            [
                "runtime: hermes",
                "primary:",
                "  model_id: claude-opus-4-7",
                "  max_tokens: 512",
                "  temperature: 0.2",
                "fallbacks:",
                "  - model_id: claude-haiku-4-5-20251001",
                "    max_tokens: 512",
                "    temperature: 0.2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    init_db(vault)
    return vault


def _cleanup_vault(vault: Path) -> None:
    root = (_VAULT_ROOT / ".codex_tmp_test" / "hermes-review-shared-adapter").resolve()
    target = vault.parent.resolve()
    if target.parent == root:
        shutil.rmtree(target, ignore_errors=True)


def test_hermes_execute_synthesis_records_shared_adapter_event() -> None:
    vault = _make_vault()
    try:
        with patch("runtime.execution_adapters.execute._get_api_key", return_value="key"):
            with patch(
                "runtime.execution_adapters.execute._call_anthropic",
                return_value={"text": "Strong artifact.", "usage": {}},
            ):
                result = _execute_synthesis(
                    request="Review artifact",
                    artifact_path="07_LOGS/Build-Logs/test.md",
                    endorsed=["Artifact present."],
                    flags=[],
                    artifact_content="# Test\n\n2026-04-27 content here.",
                    vault_root=vault,
                )

        events = load_provider_state_events(vault)
        assert result == "Strong artifact."
        assert [event["event_type"] for event in events] == ["provider.request"]
        assert events[0]["runtime"] == "hermes"
        assert events[0]["provider_id"] == "claude"
        assert events[0]["model_id"] == "claude-opus-4-7"
    finally:
        _cleanup_vault(vault)


def test_hermes_review_execute_synthesis_uses_shared_adapter() -> None:
    vault = _make_vault()
    try:
        artifact_path = "07_LOGS/Build-Logs/test.md"
        (vault / artifact_path).write_text(
            "# Build Log\n\n2026-04-27 content here with enough words for review.",
            encoding="utf-8",
        )
        task = create_task(
            vault,
            sender="OpenClaw",
            recipient="Hermes",
            intent="REVIEW",
            priority="normal",
            request="Review the artifact.",
            expected_output="Structured review.",
            notes=f"artifact_path: {artifact_path}",
        )

        with patch("runtime.execution_adapters.execute._get_api_key", return_value="key"):
            with patch(
                "runtime.execution_adapters.execute._call_anthropic",
                return_value={"text": "Hermes synthesis.", "usage": {}},
            ):
                result = run_hermes_review_execute(
                    inputs={"task_id": task["task_id"], "synthesize": True},
                    vault_root=vault,
                )

        events = load_provider_state_events(vault)
        assert result["status"] == "done"
        assert result["synthesis"] == "Hermes synthesis."
        assert "Hermes synthesis." in result["review_summary"]
        assert [event["event_type"] for event in events] == ["provider.request"]
        assert events[0]["runtime"] == "hermes"
    finally:
        _cleanup_vault(vault)
