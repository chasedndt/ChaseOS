"""Tests for native Studio packaging readiness."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.packaging_readiness import build_studio_packaging_readiness
from runtime.studio.shell import config


VAULT_ROOT = Path(__file__).resolve().parents[2]


def test_packaging_readiness_reports_static_prerequisites_without_building() -> None:
    model = build_studio_packaging_readiness(VAULT_ROOT)

    assert model["ok"] is True
    assert model["status"] == "ready_for_local_packaging_proof"
    assert model["product_lane"]["primary_command"] == "chaseos studio shell"
    assert model["product_lane"]["localhost_mock_is_product_target"] is False
    assert model["packaging_target"]["spec_path"] == "runtime/studio/packaging/chaseos-studio.spec"
    assert model["packaging_target"]["dist_exe"] == "dist/ChaseOS-Studio/ChaseOS-Studio.exe"
    assert model["dependencies"]["pywebview_declared"] is True
    assert model["dependencies"]["pyinstaller_declared"] is True
    assert model["dependencies"]["declared_as_optional_packaging_extra"] is True
    assert model["frontend"]["package_data_declared"] is True
    assert model["frontend"]["pyinstaller_meipass_resolution"] is True
    assert model["readiness"]["local_packaging_proof_run"] is False
    assert model["readiness"]["installer_built"] is False
    assert model["authority"]["builds_executable"] is False
    assert model["authority"]["writes_installer"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["next_recommended_pass"] == "studio-local-packaging-proof"


def test_frontend_dir_prefers_pyinstaller_meipass_layout(monkeypatch, tmp_path: Path) -> None:
    bundled_frontend = tmp_path / "studio_frontend"
    bundled_frontend.mkdir()
    (bundled_frontend / "index.html").write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(config.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert config.frontend_dir() == bundled_frontend
