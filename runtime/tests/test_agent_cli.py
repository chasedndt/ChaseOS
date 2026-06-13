"""CLI-level tests for Phase 9 runtime agent onboarding surface."""

from __future__ import annotations

import json
import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402
from runtime.aor.runtime_registry import load_runtime_entry  # noqa: E402


def _make_min_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "CLAUDE.md").write_text("# ChaseOS", encoding="utf-8")
    return vault


def test_agent_register_creates_declared_runtime_entry(tmp_path: Path, capsys) -> None:
    vault = _make_min_vault(tmp_path)

    exit_code = cli.main(
        [
            "agent",
            "register",
            "custom-provider",
            "local-runner",
            "--runtime-id",
            "custom-local",
            "--vault-root",
            str(vault),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "agent.register"
    assert payload["result"]["runtime_id"] == "custom-local"
    assert payload["result"]["created"] is True

    entry = load_runtime_entry("custom-local", vault_root=vault)
    assert entry is not None
    assert entry["provider"] == "custom-provider"
    assert entry["surface_type"] == "local-runner"
    assert entry["lifecycle_state"] == "declared"
    assert entry["trust_ceiling"] == "tier-4"


def test_agent_status_reports_seeded_runtime_entry(capsys) -> None:
    exit_code = cli.main(
        [
            "agent",
            "status",
            "openclaw",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "agent.status"
    assert payload["result"]["runtime_id"] == "openclaw"
    assert payload["result"]["lifecycle_state"] == "registered"
    assert payload["result"]["trust_ceiling"] == "tier-2"


def test_agent_lifecycle_show_returns_current_state(capsys) -> None:
    exit_code = cli.main(
        [
            "agent",
            "lifecycle",
            "hermes",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "agent.lifecycle"
    assert payload["result"]["runtime_id"] == "hermes"
    assert payload["result"]["lifecycle_state"] == "registered"
    assert payload["result"]["transition_performed"] is False


def test_agent_lifecycle_transition_requires_decision_ref(tmp_path: Path, capsys) -> None:
    vault = _make_min_vault(tmp_path)
    cli.main(
        [
            "agent",
            "register",
            "custom-provider",
            "local-runner",
            "--runtime-id",
            "custom-local",
            "--vault-root",
            str(vault),
            "--json",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "agent",
            "lifecycle",
            "custom-local",
            "sandboxed",
            "--vault-root",
            str(vault),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "decision-ref" in captured.err


def test_agent_lifecycle_transition_updates_entry_and_writes_audit(tmp_path: Path, capsys) -> None:
    vault = _make_min_vault(tmp_path)
    cli.main(
        [
            "agent",
            "register",
            "custom-provider",
            "local-runner",
            "--runtime-id",
            "custom-local",
            "--vault-root",
            str(vault),
            "--json",
        ]
    )
    capsys.readouterr()

    exit_code = cli.main(
        [
            "agent",
            "lifecycle",
            "custom-local",
            "sandboxed",
            "--decision-ref",
            "2026-04-25_custom-local-sandboxed",
            "--vault-root",
            str(vault),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    entry = load_runtime_entry("custom-local", vault_root=vault)
    audit_path = vault / "runtime" / "aor" / "runtime_registry" / "custom-local" / "audit" / "lifecycle_log.jsonl"

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "agent.lifecycle"
    assert payload["result"]["transition_performed"] is True
    assert payload["result"]["lifecycle_state"] == "sandboxed"
    assert entry is not None
    assert entry["lifecycle_state"] == "sandboxed"
    assert audit_path.exists()


def test_agent_list_returns_sorted_runtime_ids(capsys) -> None:
    exit_code = cli.main(
        [
            "agent",
            "list",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    runtime_ids = [item["runtime_id"] for item in payload["result"]["runtimes"]]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "agent.list"
    assert runtime_ids == sorted(runtime_ids)
    assert "hermes" in runtime_ids
    assert "openclaw" in runtime_ids
