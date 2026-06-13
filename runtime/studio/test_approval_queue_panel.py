"""Tests for the read-only Studio Pulse Approval Queue panel contract."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.approval_queue_panel import (
    MODEL_VERSION,
    SURFACE_ID,
    build_studio_approval_queue_panel_contract,
    latest_approval_queue_artifact,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _seed_approval_queue_artifact(vault: Path) -> Path:
    root = vault / "07_LOGS" / "Pulse-Decks" / "approval-queue"
    root.mkdir(parents=True, exist_ok=True)
    artifact = root / "2026-05-03-approval-queue.html"
    artifact.write_text(
        "<!doctype html><title>ChaseOS Pulse Approval Queue</title>",
        encoding="utf-8",
    )
    return artifact


def test_approval_queue_panel_contract_mounts_existing_artifact_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    artifact = _seed_approval_queue_artifact(vault)
    before = _snapshot(vault)

    model = build_studio_approval_queue_panel_contract(vault)

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["panel"]["panel_id"] == "studio.pulse.approval_queue.panel"
    assert model["panel"]["mount_target"] == "desktop-shell-app:workspace-main-panel"
    assert model["panel"]["source_artifact_path"] == artifact.relative_to(vault).as_posix()
    assert model["panel"]["source_artifact_uri"].startswith("file:///")
    assert model["summary"]["lane_count"] == 8
    assert model["readiness"]["approval_queue_panel_contract_ready"] is True
    assert model["readiness"]["static_approval_queue_artifact_ready"] is True
    assert model["readiness"]["desktop_shell_mount_ready"] is True
    assert model["readiness"]["approval_execution_ui_ready"] is False
    assert model["readiness"]["candidate_apply_ui_ready"] is False
    assert model["approval_queue_truth"]["approval_queue_panel_contract_built"] is True
    assert model["approval_queue_truth"]["approval_queue_mounted_in_studio"] is True
    assert model["authority"]["read_only"] is True
    assert model["authority"]["grants_approvals"] is False
    assert model["authority"]["executes_approvals"] is False
    assert model["authority"]["applies_candidates"] is False
    assert model["authority"]["writes_agent_bus_tasks"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []


def test_approval_queue_panel_blocks_without_static_artifact(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    model = build_studio_approval_queue_panel_contract(vault)

    assert model["ok"] is False
    assert model["panel"]["source_artifact_path"] is None
    assert model["readiness"]["approval_queue_panel_contract_ready"] is False
    assert model["readiness"]["static_approval_queue_artifact_ready"] is False
    assert "approval-queue-static-artifact-not-found" in model["readiness"]["blockers"]
    assert model["authority"]["starts_servers"] is False
    assert model["authority"]["writes_review_decisions"] is False


def test_latest_approval_queue_artifact_returns_newest(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    root = vault / "07_LOGS" / "Pulse-Decks" / "approval-queue"
    root.mkdir(parents=True)
    older = root / "2026-05-02-approval-queue.html"
    newer = root / "2026-05-03-approval-queue.html"
    older.write_text("old", encoding="utf-8")
    newer.write_text("new", encoding="utf-8")

    assert latest_approval_queue_artifact(vault) == newer
