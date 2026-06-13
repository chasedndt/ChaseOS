"""Tests for bounded Phase 9 scaffold generator foothold."""

from __future__ import annotations

import json
import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402
from runtime.scaffold.generator import generate_scaffold  # noqa: E402


def _make_min_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "CLAUDE.md").write_text("# ChaseOS", encoding="utf-8")
    return vault


class TestScaffoldGeneratorModule:
    def test_generate_project_scaffold_writes_draft_artifacts_only(self, tmp_path: Path) -> None:
        vault = _make_min_vault(tmp_path)

        result = generate_scaffold("project", "Alpha Core", vault_root=vault)

        root = Path(result["scaffold_root"])
        artifact_paths = [Path(path) for path in result["artifact_paths"]]
        manifest = root / "scaffold_request.json"
        project_note = root / "artifacts" / "01_PROJECTS" / "alpha-core" / "Alpha-Core-OS.draft.md"
        workflow_manifest = root / "artifacts" / "runtime" / "workflows" / "registry" / "alpha-core_scaffold_draft.yaml"

        assert root == vault / "runtime" / "scaffold" / "generated" / "project-alpha-core"
        assert manifest.exists()
        assert project_note.exists()
        assert workflow_manifest.exists()
        assert all(str(path).startswith(str(root / "artifacts")) for path in artifact_paths)
        assert "status: draft" in project_note.read_text(encoding="utf-8")
        assert "status: draft" in workflow_manifest.read_text(encoding="utf-8")

    def test_generate_workspace_scaffold_stays_under_runtime_scaffold_generated(self, tmp_path: Path) -> None:
        vault = _make_min_vault(tmp_path)

        result = generate_scaffold("workspace", "Signal Lab", vault_root=vault)

        root = Path(result["scaffold_root"])
        workspace_payload = root / "artifacts" / "runtime" / "source_intelligence" / "workspaces" / "signal-lab" / "workspace.draft.json"

        assert root == vault / "runtime" / "scaffold" / "generated" / "workspace-signal-lab"
        assert workspace_payload.exists()
        payload = json.loads(workspace_payload.read_text(encoding="utf-8"))
        assert payload["status"] == "draft"
        assert payload["workspace_id"] == "signal-lab"

    def test_generate_brain_scaffold_writes_draft_only_bootstrap_artifact(self, tmp_path: Path) -> None:
        vault = _make_min_vault(tmp_path)

        result = generate_scaffold("brain", "Demo Brain", vault_root=vault)

        root = Path(result["scaffold_root"])
        brain_payload = root / "artifacts" / "runtime" / "scaffold" / "brain_targets" / "demo-brain" / "brain.draft.json"

        assert result["scaffold_type"] == "brain"
        assert root == vault / "runtime" / "scaffold" / "generated" / "brain-demo-brain"
        assert brain_payload.exists()
        payload = json.loads(brain_payload.read_text(encoding="utf-8"))
        assert payload["status"] == "draft"
        assert payload["requires_future_approval_packet"] is True


class TestScaffoldGeneratorCli:
    def test_scaffold_project_json(self, tmp_path: Path, capsys) -> None:
        vault = _make_min_vault(tmp_path)

        exit_code = cli.main(
            [
                "scaffold",
                "project",
                "Alpha Core",
                "--vault-root",
                str(vault),
                "--json",
            ]
        )
        captured = capsys.readouterr()
        payload = json.loads(captured.out)

        assert exit_code == 0
        assert payload["ok"] is True
        assert payload["action"] == "scaffold.project"
        assert payload["result"]["scaffold_type"] == "project"
        assert payload["result"]["name"] == "Alpha Core"
        assert payload["result"]["slug"] == "alpha-core"
        assert payload["result"]["draft_only"] is True

    def test_scaffold_workspace_json(self, tmp_path: Path, capsys) -> None:
        vault = _make_min_vault(tmp_path)

        exit_code = cli.main(
            [
                "scaffold",
                "workspace",
                "Signal Lab",
                "--vault-root",
                str(vault),
                "--json",
            ]
        )
        captured = capsys.readouterr()
        payload = json.loads(captured.out)

        assert exit_code == 0
        assert payload["ok"] is True
        assert payload["action"] == "scaffold.workspace"
        assert payload["result"]["scaffold_type"] == "workspace"
        assert payload["result"]["slug"] == "signal-lab"
        assert payload["result"]["draft_only"] is True

    def test_scaffold_brain_json(self, tmp_path: Path, capsys) -> None:
        vault = _make_min_vault(tmp_path)

        exit_code = cli.main(
            [
                "scaffold",
                "brain",
                "Demo Brain",
                "--vault-root",
                str(vault),
                "--json",
            ]
        )
        captured = capsys.readouterr()
        payload = json.loads(captured.out)

        assert exit_code == 0
        assert payload["ok"] is True
        assert payload["action"] == "scaffold.brain"
        assert payload["result"]["scaffold_type"] == "brain"
        assert payload["result"]["slug"] == "demo-brain"
        assert payload["result"]["draft_only"] is True
