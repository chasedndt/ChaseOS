from __future__ import annotations

import json
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]


def _copy_adapter_policy(vault: Path, adapter_id: str) -> None:
    source = _REPO_ROOT / "runtime" / "policy" / "adapters" / f"{adapter_id}.yaml"
    target = vault / "runtime" / "policy" / "adapters" / f"{adapter_id}.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _records(vault: Path) -> list[dict]:
    spool = vault / "07_LOGS" / "Runtime-Events" / "runtime-events.jsonl"
    return [json.loads(line) for line in spool.read_text(encoding="utf-8").splitlines()]


def test_aor_stage_writeback_emits_graph_readable_runtime_activity(tmp_path: Path) -> None:
    from runtime.aor.engine import _stage_writeback
    from runtime.studio.graph_runtime_overlay_surface import build_graph_runtime_overlay_surface

    _copy_adapter_policy(tmp_path, "openclaw")
    manifest = {
        "id": "openclaw_watch",
        "runtime_adapter": "openclaw",
        "writeback_targets": ["07_LOGS/Agent-Activity/"],
    }
    role_card = {"write_scope": ["07_LOGS/Agent-Activity/"]}
    run_data = {
        "task_id": "task-openclaw-writeback-proof",
        "writebacks": [
            {
                "path": "07_LOGS/Agent-Activity/openclaw-writeback-proof.md",
                "content": "# OpenClaw Writeback Proof\n\nVisibility-only Graph event proof.",
            }
        ],
    }

    result = _stage_writeback(manifest, role_card, run_data, tmp_path, dry_run=False)

    assert result.ok is True
    assert (tmp_path / "07_LOGS" / "Agent-Activity" / "openclaw-writeback-proof.md").exists()
    activity = result.data["runtime_activity_events"]
    assert activity["ok"] is True
    assert activity["emitted_count"] == 2
    assert activity["event_types"] == ["file.written", "artifact.created"]

    records = _records(tmp_path)
    assert [record["adapter_id"] for record in records] == ["openclaw", "openclaw"]
    assert [record["event_type"] for record in records] == ["file.written", "artifact.created"]
    assert all(record["authority"]["visibility_event_only"] is True for record in records)
    assert all(record["authority"]["canonical_mutation_allowed"] is False for record in records)
    assert all(record["payload"]["source"] == "aor_stage_writeback" for record in records)
    assert records[0]["payload"]["write_scope"] == "aor_stage7_writeback"
    assert records[1]["payload"]["artifact_path"] == "07_LOGS/Agent-Activity/openclaw-writeback-proof.md"

    surface = build_graph_runtime_overlay_surface(tmp_path, limit=20)
    assert surface["ok"] is True
    assert surface["runtime_activity"]["spool_row_count"] == 2
    assert surface["runtime_activity"]["imported_overlay_event_count"] == 2
    assert surface["authority"]["runtime_dispatch_allowed"] is False
    assert surface["authority"]["canonical_mutation_allowed"] is False
    event_types = {event["event_type"] for event in surface["events"]}
    assert "node_edit_finished" in event_types
    assert "artifact_generated" in event_types


def test_aor_stage_writeback_runtime_activity_is_fail_open(tmp_path: Path) -> None:
    from runtime.aor.engine import _stage_writeback

    manifest = {
        "id": "hermes_watch",
        "runtime_adapter": "hermes",
        "writeback_targets": ["07_LOGS/Agent-Activity/"],
    }
    role_card = {"write_scope": ["07_LOGS/Agent-Activity/"]}
    run_data = {
        "task_id": "task-hermes-missing-policy",
        "writebacks": [
            {
                "path": "07_LOGS/Agent-Activity/hermes-writeback-proof.md",
                "content": "# Hermes Writeback Proof\n\nPolicy intentionally absent.",
            }
        ],
    }

    result = _stage_writeback(manifest, role_card, run_data, tmp_path, dry_run=False)

    assert result.ok is True
    assert result.data["files_written"] == ["07_LOGS/Agent-Activity/hermes-writeback-proof.md"]
    assert result.data["runtime_activity_events"]["ok"] is False
    assert result.data["runtime_activity_events"]["emitted_count"] == 0
    assert result.data["runtime_activity_events"]["errors"]
    assert not (tmp_path / "07_LOGS" / "Runtime-Events" / "runtime-events.jsonl").exists()
