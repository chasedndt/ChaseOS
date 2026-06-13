from __future__ import annotations

from dataclasses import replace
import shutil
from pathlib import Path

import pytest

from runtime.pulse.multi_audience_decks import (
    build_pulse_deck_inventory,
    build_pulse_multi_audience_decks,
)


def _temp_vault(name: str) -> Path:
    base = (Path(__file__).resolve().parent / "_tmp_multi_audience_decks").resolve()
    expected_parent = Path(__file__).resolve().parent.resolve()
    if base.parent != expected_parent:
        raise RuntimeError(f"Refusing unsafe test temp root: {base}")
    root = base / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def _cleanup_temp_vault(vault: Path) -> None:
    base = (Path(__file__).resolve().parent / "_tmp_multi_audience_decks").resolve()
    if vault.resolve().parent != base:
        raise RuntimeError(f"Refusing unsafe test cleanup: {vault}")
    if vault.exists():
        shutil.rmtree(vault)


def _seed_minimal_vault(vault: Path) -> None:
    for rel_path in [
        "00_HOME/Now.md",
        "00_HOME/Dashboard.md",
        "06_AGENTS/ChaseOS-Pulse-Architecture.md",
        "06_AGENTS/ChaseOS-Pulse-Completion-Tracker.md",
        "06_AGENTS/Context-Memory-Core.md",
        "06_AGENTS/Pulse-Truth-State-Audit-Checklist.md",
        "runtime/pulse/card_schema.py",
        "runtime/pulse/post_completion_hardening.py",
        "runtime/pulse/signal_collector.py",
        "runtime/memory/README.md",
        "runtime/schedules/manifests/chaseos_pulse_daily.yaml",
        "runtime/schedules/manifests/hermes_runtime_pulse.yaml",
        "07_LOGS/Build-Logs/2026-04-29-ChaseOS-chaseos-pulse-architecture-scaffolding.md",
        "07_LOGS/Build-Logs/2026-04-29-ChaseOS-chaseos-pulse-scaffold-audit.md",
        "07_LOGS/Agent-Activity/Agent-Activity-Index.md",
    ]:
        path = vault / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# test\n", encoding="utf-8")


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def test_multi_audience_deck_dry_run_builds_all_audiences_without_writes() -> None:
    vault = _temp_vault("dry_run")
    try:
        _seed_minimal_vault(vault)
        before = _snapshot(vault)

        result = build_pulse_multi_audience_decks(
            vault,
            generated_at="2026-05-02T17:00:00+00:00",
        )

        assert result.read_only is True
        assert result.write_requested is False
        assert result.write_executed is False
        assert result.writes == ()
        assert result.audiences == ("user", "agent", "shared_coordination")
        assert [deck.audience for deck in result.decks] == [
            "user",
            "agent",
            "shared_coordination",
        ]
        assert [deck.card_count for deck in result.decks] == [8, 3, 3]
        assert all(deck.canonical_writeback_enabled is False for deck in result.decks)
        assert result.schedule_activation_allowed is False
        assert result.agent_bus_task_write_allowed is False
        assert result.provider_or_connector_call_allowed is False
        assert _snapshot(vault) == before
    finally:
        _cleanup_temp_vault(vault)


def test_multi_audience_deck_write_stays_under_pulse_logs() -> None:
    vault = _temp_vault("write")
    try:
        _seed_minimal_vault(vault)

        result = build_pulse_multi_audience_decks(
            vault,
            generated_at="2026-05-02T17:05:00+00:00",
            slug_prefix="2026-05-02-test",
            write=True,
        )

        assert result.read_only is False
        assert result.write_requested is True
        assert result.write_executed is True
        assert len(result.writes) == 6
        assert all(path.replace("\\", "/").startswith("07_LOGS/Pulse-Decks/") for path in result.writes)
        assert all((vault / path).exists() for path in result.writes)
        assert {item.audience for item in result.inventory} == {
            "user",
            "agent",
            "shared_coordination",
        }
        assert all(item.latest_json_path for item in result.inventory)
        assert all(item.card_count > 0 for item in result.inventory)
    finally:
        _cleanup_temp_vault(vault)


def test_deck_inventory_reads_existing_artifacts_without_writes() -> None:
    vault = _temp_vault("inventory")
    try:
        _seed_minimal_vault(vault)
        build_pulse_multi_audience_decks(
            vault,
            generated_at="2026-05-02T17:10:00+00:00",
            slug_prefix="2026-05-02-inventory",
            write=True,
        )
        before = _snapshot(vault)

        inventory = build_pulse_deck_inventory(vault)

        assert [item.audience for item in inventory] == [
            "user",
            "agent",
            "shared_coordination",
        ]
        assert [item.card_count for item in inventory] == [8, 3, 3]
        assert _snapshot(vault) == before
    finally:
        _cleanup_temp_vault(vault)


def test_multi_audience_deck_rejects_invalid_audience() -> None:
    vault = _temp_vault("invalid_audience")
    try:
        _seed_minimal_vault(vault)

        with pytest.raises(ValueError, match="unsupported"):
            build_pulse_multi_audience_decks(vault, audiences=["user", "openflow"])
    finally:
        _cleanup_temp_vault(vault)


def test_multi_audience_deck_result_rejects_authority_flags() -> None:
    vault = _temp_vault("authority_flags")
    try:
        _seed_minimal_vault(vault)
        result = build_pulse_multi_audience_decks(vault)

        for flag in (
            "canonical_writeback_allowed",
            "memory_approval_allowed",
            "provider_or_connector_call_allowed",
            "runtime_dispatch_allowed",
            "schedule_activation_allowed",
            "agent_bus_task_write_allowed",
            "second_datastore_created",
        ):
            with pytest.raises(ValueError):
                replace(result, **{flag: True}).validate()
    finally:
        _cleanup_temp_vault(vault)
