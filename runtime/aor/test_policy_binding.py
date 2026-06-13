"""Policy-binding tests for Phase 9 runtime onboarding."""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.aor.policy_binding import bind_runtime_policy, load_policy_binding
from runtime.aor.runtime_registry import load_runtime_entry, register_runtime_entry, transition_runtime_lifecycle


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]


def _make_min_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "CLAUDE.md").write_text("# ChaseOS", encoding="utf-8")
    return vault


def test_bind_runtime_policy_writes_record_and_updates_registry() -> None:
    result = bind_runtime_policy("openclaw", vault_root=_VAULT_ROOT)

    assert result["runtime_id"] == "openclaw"
    assert Path(result["binding_path"]).as_posix().endswith("runtime/aor/runtime_registry/openclaw/policy_binding.yaml")
    assert "operator-briefing" in result["allowed_task_types"]
    assert result["policy_binding_complete"] is True

    entry = load_runtime_entry("openclaw", vault_root=_VAULT_ROOT)
    assert entry is not None
    assert entry["policy_binding_record"] == result["binding_path"]

    binding = load_policy_binding("openclaw", vault_root=_VAULT_ROOT)
    assert binding is not None
    assert binding["runtime_id"] == "openclaw"
    assert binding["adapter_id"] == "openclaw"


def test_load_policy_binding_returns_none_when_missing(tmp_path: Path) -> None:
    vault = _make_min_vault(tmp_path)
    assert load_policy_binding("missing", vault_root=vault) is None



def test_execution_capable_transition_requires_policy_binding(tmp_path: Path) -> None:
    vault = _make_min_vault(tmp_path)
    register_runtime_entry(
        "custom-local",
        provider="custom-provider",
        surface_type="local-runner",
        vault_root=vault,
        lifecycle_state="registered",
    )

    with pytest.raises(ValueError, match="policy binding"):
        transition_runtime_lifecycle(
            "custom-local",
            "execution-capable",
            decision_ref="2026-04-26_custom-local-exec",
            vault_root=vault,
        )
