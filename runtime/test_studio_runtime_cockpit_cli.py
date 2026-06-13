"""CLI tests for the Studio Runtime Cockpit contract surface."""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
from time import monotonic

import runtime.cli.main as cli
from runtime.studio import runtime_cockpit


def _test_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


def test_studio_runtime_cockpit_parser_accepts_contract_command() -> None:
    args = cli.build_parser().parse_args([
        "studio",
        "runtime-cockpit",
        "--runtime",
        "hermes",
        "--json",
    ])

    assert args.func is cli.cmd_studio_runtime_cockpit
    assert args.runtime_id == "hermes"
    assert args.output_json is True


def test_studio_runtime_cockpit_dispatches_contract_model(monkeypatch, tmp_path: Path, capsys) -> None:
    captured: dict[str, object] = {}

    def fake_contract(vault_root, *, runtime_id=None, **kwargs):
        captured["vault_root"] = str(vault_root)
        captured["runtime_id"] = runtime_id
        captured["probe_child_apps"] = kwargs.get("probe_child_apps")
        captured["service_timeout_seconds"] = kwargs.get("service_timeout_seconds")
        return {
            "ok": True,
            "surface": "studio_runtime_cockpit_contract",
            "title": "Studio Runtime Cockpit Contract",
            "status": "contract_ready_desktop_shell_unbuilt",
            "runtime_filter": runtime_id or "all",
            "desktop": {"desktop_runtime_cockpit_built": False},
            "runtime_startup": {
                "surface_count": 1,
                "manageable_surface_count": 1,
                "visual_surface_count": 1,
                "readiness_summary": {"readiness_packet_count": 2, "approval_missing_count": 2, "host_mutation_allowed_now": False},
            },
            "available_surfaces": [],
            "errors": [],
        }

    monkeypatch.setattr(runtime_cockpit, "build_runtime_cockpit_contract", fake_contract)
    vault = _test_vault(tmp_path)
    args = cli.build_parser().parse_args([
        "studio",
        "runtime-cockpit",
        "--runtime",
        "hermes",
        "--vault-root",
        str(vault),
        "--json",
    ])

    assert cli.cmd_studio_runtime_cockpit(args) == 0
    out = capsys.readouterr().out

    assert "studio_runtime_cockpit_contract" in out
    assert captured["runtime_id"] == "hermes"
    assert captured["probe_child_apps"] is False
    assert captured["service_timeout_seconds"] == 0.0
    assert Path(str(captured["vault_root"])).resolve() == vault.resolve()


def test_chaseos_py_studio_panel_json_smokes_are_bounded(tmp_path: Path) -> None:
    vault = _test_vault(tmp_path)
    repo_root = Path(__file__).resolve().parents[1]

    for panel_args, expected_action in [
        (["studio", "approval-center-panel", "--vault-root", str(vault), "--json"], "studio.approval-center-panel"),
        (["studio", "runtime-cockpit", "--vault-root", str(vault), "--json"], "studio.runtime-cockpit"),
    ]:
        started = monotonic()
        completed = subprocess.run(
            [sys.executable, "chaseos.py", *panel_args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
        elapsed = monotonic() - started
        payload = json.loads(completed.stdout)

        assert completed.returncode == 0, completed.stderr
        assert elapsed < 12
        assert payload["ok"] is True
        assert payload["action"] == expected_action
        boundary = payload["result"]["authority" if "approval" in expected_action else "boundary"]
        assert boundary["canonical_mutation_allowed"] is False
