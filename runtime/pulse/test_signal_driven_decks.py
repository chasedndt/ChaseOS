from __future__ import annotations

from dataclasses import replace
import shutil
from pathlib import Path

import pytest

from runtime.pulse.signal_driven_decks import (
    SIGNAL_DRIVEN_AUDIENCES,
    build_pulse_local_signal_snapshot,
    build_signal_driven_pulse_decks,
    collect_signal_driven_pulse_signals,
)


def _temp_vault(name: str) -> Path:
    base = (Path(__file__).resolve().parent / "_tmp_signal_driven_decks").resolve()
    expected_parent = Path(__file__).resolve().parent.resolve()
    if base.parent != expected_parent:
        raise RuntimeError(f"Refusing unsafe test temp root: {base}")
    root = base / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def _cleanup_temp_vault(vault: Path) -> None:
    base = (Path(__file__).resolve().parent / "_tmp_signal_driven_decks").resolve()
    if vault.resolve().parent != base:
        raise RuntimeError(f"Refusing unsafe test cleanup: {vault}")
    if vault.exists():
        shutil.rmtree(vault)


def _write(vault: Path, rel_path: str, text: str = "# test\n") -> None:
    path = vault / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _manifest(name: str, runtime_target: str | None = None) -> str:
    runtime_line = f"runtime_target: {runtime_target}\n" if runtime_target else ""
    return (
        "schedule_id: test\n"
        "owner: chaseos\n"
        "enabled: false\n"
        "activation_state: planned\n"
        "external_runtime_owner: false\n"
        "canonical_writeback_enabled: false\n"
        "external_connectors_enabled: false\n"
        "unrestricted_browsing_enabled: false\n"
        f"{runtime_line}"
        f"name: {name}\n"
    )


def _seed_vault(vault: Path) -> None:
    required_docs = [
        "06_AGENTS/ChaseOS-Pulse-Architecture.md",
        "06_AGENTS/ChaseOS-Pulse-Completion-Tracker.md",
        "06_AGENTS/ChaseOS-Pulse-Post-Apply-Truth-State-Audit.md",
        "06_AGENTS/ChaseOS-Pulse-RnD-Workbook-Update-Approval.md",
        "06_AGENTS/ChaseOS-Pulse-Native-Schedule-Activation-Catchup-Proof.md",
        "06_AGENTS/ChaseOS-Pulse-Phase10-UI-Proof.md",
        "06_AGENTS/Context-Memory-Core.md",
        "06_AGENTS/Pulse-Truth-State-Audit-Checklist.md",
        "runtime/studio/shell/api.py",
        "runtime/studio/app_launcher.py",
        "runtime/pulse/card_schema.py",
        "runtime/pulse/writeback.py",
        "runtime/pulse/post_completion_hardening.py",
        "runtime/pulse/signal_driven_decks.py",
        "runtime/memory/README.md",
        "00_HOME/Now.md",
        "00_HOME/Dashboard.md",
        "07_LOGS/Agent-Activity/Agent-Activity-Index.md",
    ]
    for rel_path in required_docs:
        _write(vault, rel_path)

    _write(
        vault,
        "runtime/schedules/manifests/chaseos_pulse_daily.yaml",
        _manifest("daily"),
    )
    _write(
        vault,
        "runtime/schedules/manifests/hermes_runtime_pulse.yaml",
        _manifest("hermes", runtime_target="hermes")
        + "hermes_owner: false\nopenclaw_cron_owner: false\n",
    )
    _write(
        vault,
        "runtime/schedules/manifests/openflow_runtime_pulse.yaml",
        _manifest("openflow", runtime_target="openflow"),
    )
    _write(
        vault,
        "07_LOGS/Build-Logs/2026-05-02-ChaseOS-chaseos-pulse-multi-audience-deck-operationalization.md",
    )
    _write(
        vault,
        "07_LOGS/Build-Logs/2026-05-02-ChaseOS-browser-use-cli-live-validation.md",
    )
    _write(
        vault,
        "07_LOGS/Agent-Activity/2026-05-02-codex-chaseos-pulse-multi-audience-deck-operationalization.md",
    )
    _write(
        vault,
        "07_LOGS/Agent-Activity/2026-05-02-hermes-optimus-pulse-post-completion-permission-boundary.md",
    )


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def test_signal_snapshot_reads_local_evidence_without_writes() -> None:
    vault = _temp_vault("snapshot")
    try:
        _seed_vault(vault)
        before = _snapshot(vault)

        snapshot = build_pulse_local_signal_snapshot(
            vault,
            generated_at="2026-05-02T18:00:00+00:00",
        )

        assert snapshot.completion_status in {
            "partial",
            "backend_proof_pending",
            "phase10_ui_pending",
            "complete",
        }
        assert isinstance(snapshot.pulse_feature_done, bool)
        assert snapshot.hardening_status in {"pass", "partial", "fail"}
        assert snapshot.latest_pulse_build_log is not None
        assert snapshot.latest_hermes_activity_log is not None
        assert len(snapshot.schedule_manifests) == 3
        assert len(snapshot.inactive_schedule_manifests) == 3
        assert snapshot.canonical_writeback_allowed is False
        assert _snapshot(vault) == before
    finally:
        _cleanup_temp_vault(vault)


def test_signal_collection_uses_only_non_external_sources() -> None:
    vault = _temp_vault("signals")
    try:
        _seed_vault(vault)

        signals = collect_signal_driven_pulse_signals(
            vault,
            generated_at="2026-05-02T18:05:00+00:00",
        )

        assert len(signals) == 6
        assert {signal.audience_hint for signal in signals} == {
            "user",
            "agent",
            "shared_coordination",
        }
        assert "external_connector" not in {signal.source_type for signal in signals}
        for signal in signals:
            signal.validate(external_sources_enabled=False)
    finally:
        _cleanup_temp_vault(vault)


def test_signal_driven_deck_dry_run_builds_three_audiences_without_writes() -> None:
    vault = _temp_vault("dry_run")
    try:
        _seed_vault(vault)
        before = _snapshot(vault)

        result = build_signal_driven_pulse_decks(
            vault,
            generated_at="2026-05-02T18:10:00+00:00",
        )

        assert result.read_only is True
        assert result.write_requested is False
        assert result.write_executed is False
        assert result.writes == ()
        assert tuple(deck.audience for deck in result.decks) == SIGNAL_DRIVEN_AUDIENCES
        assert [len(deck.cards) for deck in result.decks] == [3, 3, 3]
        assert result.signal_count == 6
        assert result.canonical_writeback_allowed is False
        assert result.provider_or_connector_call_allowed is False
        assert result.schedule_activation_allowed is False
        assert result.agent_bus_task_write_allowed is False
        assert result.rd_workbook_update_allowed is False
        assert _snapshot(vault) == before
    finally:
        _cleanup_temp_vault(vault)


def test_signal_driven_deck_write_stays_under_pulse_deck_logs() -> None:
    vault = _temp_vault("write")
    try:
        _seed_vault(vault)

        result = build_signal_driven_pulse_decks(
            vault,
            generated_at="2026-05-02T18:15:00+00:00",
            slug_prefix="2026-05-02-signal-test",
            write=True,
        )

        assert result.read_only is False
        assert result.write_requested is True
        assert result.write_executed is True
        assert len(result.artifacts) == 3
        assert len(result.writes) == 6
        assert all(path.replace("\\", "/").startswith("07_LOGS/Pulse-Decks/") for path in result.writes)
        assert all((vault / path).exists() for path in result.writes)
    finally:
        _cleanup_temp_vault(vault)


def test_signal_driven_result_rejects_authority_flags() -> None:
    vault = _temp_vault("authority")
    try:
        _seed_vault(vault)
        result = build_signal_driven_pulse_decks(vault)

        for flag in (
            "canonical_writeback_allowed",
            "memory_approval_allowed",
            "provider_or_connector_call_allowed",
            "runtime_dispatch_allowed",
            "schedule_activation_allowed",
            "agent_bus_task_write_allowed",
            "rd_workbook_update_allowed",
            "second_datastore_created",
        ):
            with pytest.raises(ValueError):
                replace(result, **{flag: True}).validate()
    finally:
        _cleanup_temp_vault(vault)
