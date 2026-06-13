from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from runtime.agent_bus.bus import init_db
from runtime.mvp_agent_bus_lifecycle import build_mvp_agent_bus_lifecycle


def _seed_codex_lifecycle(
    root: Path,
    *,
    task_id: str = "task-proof",
    status: str = "done",
    write_result_artifact: bool = True,
) -> None:
    db_path = init_db(root)
    run_id = "run-proof"
    run_dir = root / "runtime" / "adapters" / "codex" / "runs" / f"20260513T120000Z-{task_id}"
    stdout = run_dir / "codex-stdout.md"
    stderr = run_dir / "codex-stderr.log"
    result = run_dir / "codex-adapter-result.json"
    run_dir.mkdir(parents=True, exist_ok=True)
    stdout.write_text("Codex proof output.\n", encoding="utf-8")
    stderr.write_text("", encoding="utf-8")
    if write_result_artifact:
        result.write_text(
            json.dumps(
                {
                    "event_id": "evt-proof",
                    "task_id": task_id,
                    "run_id": run_id,
                    "from": "Codex",
                    "event_type": "proposal",
                    "message": "Codex returned reviewable output artifacts.",
                    "artifacts": [
                        {
                            "artifact_type": "markdown",
                            "path": f"runtime/adapters/codex/runs/20260513T120000Z-{task_id}/codex-stdout.md",
                        },
                        {
                            "artifact_type": "log",
                            "path": f"runtime/adapters/codex/runs/20260513T120000Z-{task_id}/codex-stderr.log",
                        },
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    task_artifacts = [
        f"runtime/adapters/codex/runs/20260513T120000Z-{task_id}/codex-stdout.md",
        f"runtime/adapters/codex/runs/20260513T120000Z-{task_id}/codex-stderr.log",
        f"runtime/adapters/codex/runs/20260513T120000Z-{task_id}/codex-adapter-result.json",
    ]
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO tasks (
              task_id, run_id, sender, recipient, intent, status, priority, owner,
              owner_instance, request, expected_output, depends_on_json, artifacts_json,
              ingress_context_json, execution_constraints_json, work_fingerprint, notes,
              created_at, updated_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                run_id,
                "Codex",
                "Codex",
                "TASK",
                status,
                "normal",
                "Codex",
                "Axiom-Codex",
                "Read-only lifecycle proof.",
                "Reviewable output artifacts.",
                "[]",
                json.dumps(task_artifacts),
                "{}",
                json.dumps({"write_policy": "none", "allowed_write_paths": []}),
                "agent-bus-proof",
                "test proof",
                "2026-05-13T12:00:00+00:00",
                "2026-05-13T12:03:00+00:00",
                None,
            ),
        )
        for event_type, created_at, artifacts in [
            ("created", "2026-05-13T12:00:00+00:00", []),
            ("claimed", "2026-05-13T12:01:00+00:00", []),
            ("started", "2026-05-13T12:02:00+00:00", []),
            ("result_attached", "2026-05-13T12:03:00+00:00", task_artifacts),
        ]:
            conn.execute(
                """
                INSERT INTO events (
                  event_id, task_id, run_id, sender, event_type, message, artifacts_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"evt-{event_type}",
                    task_id,
                    run_id,
                    "Codex",
                    event_type,
                    f"{event_type} event",
                    json.dumps(artifacts),
                    created_at,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def test_mvp_agent_bus_lifecycle_finds_done_task_with_result_artifacts(tmp_path: Path) -> None:
    _seed_codex_lifecycle(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    payload = build_mvp_agent_bus_lifecycle(tmp_path)

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    proof = payload["proof_task"]

    assert before == after
    assert payload["status"] == "complete_for_one_codex_task_lifecycle"
    assert payload["task_created_claimed_executed_artifact_logged"] is True
    assert proof["task_id"] == "task-proof"
    assert proof["status"] == "done"
    assert proof["task_created"] is True
    assert proof["task_claimed_by_codex"] is True
    assert proof["task_started_by_codex"] is True
    assert proof["result_logged"] is True
    assert proof["result_artifact_found"] is True
    assert proof["adapter_result_matches_task"] is True
    assert proof["task_created_claimed_executed_artifact_logged"] is True
    assert payload["authority"]["agent_bus_task_write_allowed"] is False
    assert payload["authority"]["task_claim_allowed"] is False
    assert payload["authority"]["task_status_update_allowed"] is False


def test_mvp_agent_bus_lifecycle_blocks_when_result_artifact_missing(tmp_path: Path) -> None:
    _seed_codex_lifecycle(tmp_path, write_result_artifact=False)

    payload = build_mvp_agent_bus_lifecycle(tmp_path)
    proof = payload["proof_task"]

    assert payload["status"] == "partial_or_unverified"
    assert payload["task_created_claimed_executed_artifact_logged"] is False
    assert proof["task_created"] is True
    assert proof["task_claimed_by_codex"] is True
    assert proof["task_started_by_codex"] is True
    assert proof["result_logged"] is True
    assert proof["result_artifact_found"] is False
    assert "codex_agent_bus_lifecycle_proof_not_found" in payload["blockers"]
