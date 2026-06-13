from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.agents.agent_harness_readiness import build_agent_harness_readiness


def _write_capabilities(root: Path, runtime_name: str, *, bus_name: str | None = None) -> None:
    runtime_dir = root / "runtime" / runtime_name
    runtime_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir.joinpath("capabilities.yaml").write_text(
        "\n".join(
            [
                f"bus_name: {bus_name or runtime_name}",
                f"display_name: {runtime_name.title()} Harness",
                "description: Test runtime harness",
                "handles:",
                "  - task_type: code.patch",
                "    priority: primary",
                "max_concurrent_tasks: 1",
                "heartbeat_stale_seconds: 60",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_agent_harness_readiness_is_read_only_and_blocks_execution_without_liveness(tmp_path: Path) -> None:
    _write_capabilities(tmp_path, "hermes", bus_name="Hermes")

    payload = build_agent_harness_readiness(tmp_path, runtime="hermes")

    assert payload["ok"] is True
    assert payload["surface"] == "agent_harness_readiness"
    assert payload["read_only"] is True
    assert payload["runtime_id"] == "hermes"
    assert payload["runtime_bus_name"] == "Hermes"
    assert payload["harness_status"] == "blocked"
    assert "runtime_heartbeat_missing_or_stale" in payload["blocked_reasons"]
    assert payload["authority"] == {
        "read_only": True,
        "tools_callable_now": False,
        "agent_bus_mutation_allowed": False,
        "provider_calls_allowed": False,
        "terminal_execution_allowed": False,
        "route_execution_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }
    assert "agent_bus_capability_manifest" in payload["required_evidence"]
    assert "fresh_runtime_heartbeat" in payload["required_evidence"]


def test_agent_harness_readiness_fails_closed_for_unknown_runtime(tmp_path: Path) -> None:
    _write_capabilities(tmp_path, "hermes", bus_name="Hermes")

    payload = build_agent_harness_readiness(tmp_path, runtime="missing-runtime")

    assert payload["ok"] is True
    assert payload["runtime_id"] == "missing-runtime"
    assert payload["harness_status"] == "blocked"
    assert "runtime_capability_manifest_missing" in payload["blocked_reasons"]
    assert payload["authority"]["tools_callable_now"] is False


def test_agent_harness_readiness_aggregates_codex_daemon_readiness(tmp_path: Path, monkeypatch) -> None:
    _write_capabilities(tmp_path, "codex", bus_name="Codex")

    def fake_codex_readiness(vault_root, *, codex_binary="codex"):
        return {
            "ok": False,
            "runtime": "Codex",
            "runtime_instance_id": "codex-cli",
            "blocking_reasons": ["codex_binary"],
            "capability_task_types": ["code.patch"],
            "smoke_command": "python -m chaseos agent-bus codex-daemon --once --executor mock --json",
            "live_command": "python -m chaseos agent-bus codex-daemon --interval 30 --executor codex",
        }

    monkeypatch.setattr(
        "runtime.agents.agent_harness_readiness.get_codex_daemon_readiness",
        fake_codex_readiness,
    )

    payload = build_agent_harness_readiness(tmp_path, runtime="codex")

    assert payload["adapter_readiness"]["adapter"] == "codex"
    assert payload["adapter_readiness"]["ok"] is False
    assert payload["adapter_readiness"]["blocking_reasons"] == ["codex_binary"]
    assert "adapter_not_ready" in payload["blocked_reasons"]
    assert payload["tool_calling"]["tool_calling_posture"] == "inspect_only_until_gated_execution"
    assert payload["tool_calling"]["tools_callable_now"] is False
