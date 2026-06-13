"""Tests for the read-only Studio Pulse product-shell panel contract."""

from __future__ import annotations

from pathlib import Path

from runtime.pulse.card_schema import EvidenceRef, PulseCard, PulseDeck, RecommendedAction
from runtime.pulse.product_shell_browser_qa import PRODUCT_SHELL_ROOT
from runtime.pulse.renderer_json import render_deck_json
from runtime.studio.pulse_product_shell_panel import (
    MODEL_VERSION,
    SURFACE_ID,
    build_pulse_product_shell_panel_contract,
)


def _write_user_deck(vault: Path) -> Path:
    deck_dir = vault / "07_LOGS" / "Pulse-Decks" / "users"
    deck_dir.mkdir(parents=True, exist_ok=True)
    deck = PulseDeck(
        deck_id="pulse-panel-test",
        audience="user",
        generated_at="2026-05-03T11:50:00+01:00",
        cards=[
            PulseCard(
                card_id="pulse-panel-card-001",
                audience="user",
                card_class="Project Momentum",
                title="Verify Pulse panel",
                summary="A valid Pulse panel test card.",
                generated_at="2026-05-03T11:50:00+01:00",
                evidence=[
                    EvidenceRef(
                        source_path="06_AGENTS/ChaseOS-Pulse-Product-Shell-Integration.md",
                        source_type="repo_doc",
                        summary="Product shell doc exists.",
                        trust_label="repo-observed",
                    )
                ],
                recommended_actions=[
                    RecommendedAction(
                        action_id="inspect",
                        label="Inspect panel",
                        action_type="review",
                        requires_operator_approval=False,
                    )
                ],
                urgency=3,
                confidence=0.8,
            )
        ],
    )
    path = deck_dir / "2026-05-03-user-pulse.json"
    path.write_text(render_deck_json(deck), encoding="utf-8")
    return path


def _seed_static_evidence(vault: Path) -> None:
    root = vault / PRODUCT_SHELL_ROOT
    root.mkdir(parents=True, exist_ok=True)
    (root / "2026-05-03-pulse-product-shell.html").write_text(
        "<!doctype html><title>ChaseOS Pulse Product Shell</title>",
        encoding="utf-8",
    )
    (root / "2026-05-03-pulse-product-shell-browser-qa.md").write_text(
        "browser qa evidence\n",
        encoding="utf-8",
    )
    (root / "2026-05-03-pulse-product-shell-browser-qa.png").write_bytes(b"png")


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_pulse_product_shell_panel_contract_reports_mount_contract_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    deck_path = _write_user_deck(vault)
    _seed_static_evidence(vault)
    before = _snapshot(vault)

    model = build_pulse_product_shell_panel_contract(vault, deck_path=deck_path)

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["panel"]["panel_id"] == "studio.pulse.product_shell.panel"
    assert model["panel"]["mount_target"] == "desktop-shell-app:workspace-main-panel"
    assert model["panel"]["source_artifact_path"].endswith("pulse-product-shell.html")
    assert model["panel"]["browser_qa_evidence_path"].endswith("product-shell-browser-qa.md")
    assert model["readiness"]["pulse_product_shell_panel_contract_ready"] is True
    assert model["readiness"]["static_product_shell_artifact_ready"] is True
    assert model["readiness"]["static_product_shell_browser_qa_ready"] is True
    assert model["readiness"]["desktop_shell_mount_ready"] is False
    assert model["readiness"]["interactive_pulse_controls_ready"] is False
    assert model["readiness"]["next_recommended_pass"] == "chaseos-pulse-studio-product-shell-mount"
    assert model["pulse_product_shell_truth"]["pulse_product_shell_panel_contract_built"] is True
    assert model["pulse_product_shell_truth"]["pulse_product_shell_mounted_in_studio"] is False
    assert model["authority"]["read_only"] is True
    assert model["authority"]["writes_vault"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []


def test_pulse_product_shell_panel_blocks_without_browser_qa_evidence(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    deck_path = _write_user_deck(vault)
    root = vault / PRODUCT_SHELL_ROOT
    root.mkdir(parents=True, exist_ok=True)
    (root / "2026-05-03-pulse-product-shell.html").write_text(
        "<!doctype html><title>ChaseOS Pulse Product Shell</title>",
        encoding="utf-8",
    )

    model = build_pulse_product_shell_panel_contract(vault, deck_path=deck_path)

    assert model["ok"] is False
    assert model["readiness"]["pulse_product_shell_panel_contract_ready"] is False
    assert "pulse-product-shell-browser-qa-evidence-not-found" in model["readiness"]["blockers"]
    assert model["readiness"]["next_recommended_pass"] == "chaseos-pulse-product-shell-studio-panel-contract"


def test_pulse_product_shell_panel_blocks_without_static_artifact(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    deck_path = _write_user_deck(vault)
    root = vault / PRODUCT_SHELL_ROOT
    root.mkdir(parents=True, exist_ok=True)
    (root / "2026-05-03-pulse-product-shell-browser-qa.md").write_text(
        "browser qa evidence\n",
        encoding="utf-8",
    )

    model = build_pulse_product_shell_panel_contract(vault, deck_path=deck_path)

    assert model["ok"] is False
    assert model["panel"]["source_artifact_path"] is None
    assert "pulse-product-shell-artifact-not-found" in model["readiness"]["blockers"]
    assert model["authority"]["starts_servers"] is False
