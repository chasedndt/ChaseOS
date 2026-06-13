"""CLI tests for persisted graph current-pointer repair handoff commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parents[2]
if str(VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(VAULT_ROOT))

from runtime.graph.artifact import GraphSnapshot, make_node, make_snapshot_id  # noqa: E402
from runtime.graph.store import write_snapshot_manifest  # noqa: E402
from runtime.studio.persisted_graph_storage_status import (  # noqa: E402
    build_persisted_graph_storage_status,
    request_persisted_graph_current_pointer_repair_approval,
    required_current_pointer_repair_approval_decision_statement,
    required_current_pointer_repair_approval_write_statement,
    required_current_pointer_repair_execution_statement,
)
from runtime.studio.test_graph_long_running_acceptance_audit import (  # noqa: E402
    _approve_current_pointer_repair,
    _seed_runtime_overlay_evidence,
    _seed_vault,
    _use_short_evidence_paths,
)
import runtime.cli.main as cli  # noqa: E402


def _snapshot() -> GraphSnapshot:
    node = make_node(label="CODEX.md", node_type="file", source_file="06_AGENTS/CODEX.md")
    return GraphSnapshot(
        snapshot_id=make_snapshot_id(),
        created_at="2026-06-04T12:00:00Z",
        vault_root="/test/vault",
        extraction_scope=["06_AGENTS/", "runtime/"],
        nodes=[node],
        edges=[],
        community_assignments={},
        build_info={"builder": "test"},
        metadata={},
    )


def _seed_pending_approval(root: Path) -> tuple[dict, str]:
    snapshot = _snapshot()
    write_snapshot_manifest(
        snapshot,
        repo_root=root,
        builder="runtime.graph.builder.full_pipeline",
        source_model="runtime.graph.GraphSnapshot.v1",
        vault_root_hash="sha256:test-root",
        source_file_count=2,
        write_current=False,
    )
    current_pointer = root / "runtime" / "graph" / "store" / "manifests" / "current.json"
    current_pointer.write_text(
        json.dumps(
            {
                "snapshot_id": "missing-snapshot",
                "manifest_path": "runtime/graph/store/manifests/snapshots/missing-snapshot.json",
                "canonical_mutation_allowed": False,
                "generated_from_read_only_scan": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    preview = request_persisted_graph_current_pointer_repair_approval(root)
    digest = preview["approval_digest"]
    approval = request_persisted_graph_current_pointer_repair_approval(
        root,
        expected_approval_digest=digest,
        operator_statement=required_current_pointer_repair_approval_write_statement(
            approval_packet_id=preview["approval_packet_id"],
            approval_digest=digest,
        ),
        operator_id="test-operator",
        write_approval=True,
    )
    return approval, digest


def _file_listing(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def test_current_pointer_repair_approval_consumption_dry_run_cli_validates_without_writes(
    tmp_path: Path,
    capsys,
) -> None:
    approval, digest = _seed_pending_approval(tmp_path)
    before = _file_listing(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-approval-consumption-dry-run",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.persisted-graph-current-pointer-repair-approval-consumption-dry-run"
    assert result["surface"] == "persisted_graph_current_pointer_repair_approval_consumption_dry_run"
    assert result["summary"]["approval_consumption_dry_run_ready"] is True
    assert result["summary"]["approval_consumed"] is False
    assert result["summary"]["execution_marker_written"] is False
    assert result["summary"]["current_pointer_written"] is False
    assert result["writes_performed"] is False
    assert _file_listing(tmp_path) == before


def test_current_pointer_repair_approval_decision_cli_preview_does_not_write(
    tmp_path: Path,
    capsys,
) -> None:
    approval, digest = _seed_pending_approval(tmp_path)
    before = _file_listing(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-approval-decision",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--decision",
            "approved",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    artifact = json.loads((tmp_path / approval["approval_artifact_path"]).read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.persisted-graph-current-pointer-repair-approval-decision"
    assert result["surface"] == "persisted_graph_current_pointer_repair_approval_decision"
    assert result["summary"]["approval_decision_written"] is False
    assert result["summary"]["approval_consumed"] is False
    assert result["summary"]["current_pointer_written"] is False
    assert result["writes_performed"] is False
    assert artifact["status"] == "pending"
    assert _file_listing(tmp_path) == before


def test_current_pointer_repair_approval_decision_cli_write_decision_requires_exact_statement(
    tmp_path: Path,
    capsys,
) -> None:
    approval, digest = _seed_pending_approval(tmp_path)
    before = _file_listing(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-approval-decision",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--decision",
            "approved",
            "--operator-statement",
            "wrong",
            "--write-decision",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 1
    assert payload["ok"] is False
    assert "operator_statement_mismatch" in result["blocked_reasons"]
    assert result["writes_performed"] is False
    assert _file_listing(tmp_path) == before


def test_current_pointer_repair_approval_decision_cli_writes_only_approval_artifact(
    tmp_path: Path,
    capsys,
) -> None:
    approval, digest = _seed_pending_approval(tmp_path)
    statement = required_current_pointer_repair_approval_decision_statement(
        approval_packet_id=approval["approval_packet_id"],
        approval_digest=digest,
        decision="approved",
    )
    before = _file_listing(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-approval-decision",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--decision",
            "approved",
            "--operator-statement",
            statement,
            "--reviewed-by",
            "test-operator",
            "--write-decision",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    after = _file_listing(tmp_path)
    artifact = json.loads((tmp_path / approval["approval_artifact_path"]).read_text(encoding="utf-8"))
    current_pointer = tmp_path / "runtime" / "graph" / "store" / "manifests" / "current.json"
    assert exit_code == 0
    assert payload["ok"] is True
    assert result["summary"]["approval_decision_written"] is True
    assert result["summary"]["approval_consumed"] is False
    assert result["summary"]["execution_marker_written"] is False
    assert result["summary"]["current_pointer_written"] is False
    assert result["writes_performed"] is True
    assert before == after
    assert artifact["status"] == "approved"
    assert artifact["decision_state"] == "approved_for_current_pointer_repair"
    assert artifact["operator_decision"] == "approved"
    assert json.loads(current_pointer.read_text(encoding="utf-8"))["snapshot_id"] == "missing-snapshot"


def test_current_pointer_repair_approved_execution_cli_blocks_pending_artifact_without_writes(
    tmp_path: Path,
    capsys,
) -> None:
    approval, digest = _seed_pending_approval(tmp_path)
    statement = required_current_pointer_repair_execution_statement(
        approval_packet_id=approval["approval_packet_id"],
        approval_digest=digest,
    )
    before = _file_listing(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-approved-execution",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--operator-statement",
            statement,
            "--execute",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    current_pointer = tmp_path / "runtime" / "graph" / "store" / "manifests" / "current.json"
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "studio.persisted-graph-current-pointer-repair-approved-execution"
    assert result["surface"] == "persisted_graph_current_pointer_repair_approved_execution"
    assert "approval_artifact_approved" in result["blocked_reasons"]
    assert result["summary"]["execution_marker_written"] is False
    assert result["summary"]["current_pointer_written"] is False
    assert result["writes_performed"] is False
    assert json.loads(current_pointer.read_text(encoding="utf-8"))["snapshot_id"] == "missing-snapshot"
    assert _file_listing(tmp_path) == before


def test_current_pointer_repair_approved_execution_cli_bad_statement_keeps_approved_execution_next(
    tmp_path: Path,
    capsys,
) -> None:
    approval, digest = _seed_pending_approval(tmp_path)
    decision_statement = required_current_pointer_repair_approval_decision_statement(
        approval_packet_id=approval["approval_packet_id"],
        approval_digest=digest,
        decision="approved",
    )
    decision_exit = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-approval-decision",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--decision",
            "approved",
            "--operator-statement",
            decision_statement,
            "--write-decision",
            "--json",
        ]
    )
    decision_payload = json.loads(capsys.readouterr().out)
    before = _file_listing(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-approved-execution",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--operator-statement",
            "XECUTE PERSISTED GRAPH CURRENT POINTER REPAIR ONLY",
            "--execute",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert decision_exit == 0
    assert decision_payload["ok"] is True
    assert exit_code == 1
    assert payload["ok"] is False
    assert "operator_statement_mismatch" in result["blocked_reasons"]
    assert result["summary"]["execution_marker_written"] is False
    assert result["summary"]["current_pointer_written"] is False
    assert result["summary"]["writes_performed"] is False
    assert result["summary"]["next_recommended_pass"] == "persisted-graph-current-pointer-repair-approved-execution"
    assert result["writes_performed"] is False
    assert _file_listing(tmp_path) == before


def test_current_pointer_repair_readback_cli_blocks_pending_artifact_without_writes(
    tmp_path: Path,
    capsys,
) -> None:
    approval, digest = _seed_pending_approval(tmp_path)
    before = _file_listing(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-readback-proof",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "studio.persisted-graph-current-pointer-repair-readback-proof"
    assert result["surface"] == "persisted_graph_current_pointer_repair_readback_proof"
    assert "approval_artifact_approved" in result["blocked_reasons"]
    assert "execution_marker_present" in result["blocked_reasons"]
    assert result["summary"]["readback_verified"] is False
    assert result["writes_performed"] is False
    assert _file_listing(tmp_path) == before


def test_current_pointer_repair_readback_cli_verifies_after_approved_execution_without_writes(
    tmp_path: Path,
    capsys,
) -> None:
    approval, digest = _seed_pending_approval(tmp_path)
    decision_statement = required_current_pointer_repair_approval_decision_statement(
        approval_packet_id=approval["approval_packet_id"],
        approval_digest=digest,
        decision="approved",
    )
    decision_exit = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-approval-decision",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--decision",
            "approved",
            "--operator-statement",
            decision_statement,
            "--write-decision",
            "--json",
        ]
    )
    decision_payload = json.loads(capsys.readouterr().out)
    execution_statement = required_current_pointer_repair_execution_statement(
        approval_packet_id=approval["approval_packet_id"],
        approval_digest=digest,
    )
    execution_exit = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-approved-execution",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--operator-statement",
            execution_statement,
            "--execute",
            "--json",
        ]
    )
    execution_payload = json.loads(capsys.readouterr().out)
    before = _file_listing(tmp_path)

    readback_exit = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-readback-proof",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert decision_exit == 0
    assert decision_payload["result"]["summary"]["approval_decision_written"] is True
    assert execution_exit == 0
    assert execution_payload["result"]["summary"]["current_pointer_written"] is True
    assert readback_exit == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.persisted-graph-current-pointer-repair-readback-proof"
    assert result["status"] == "COMPLETE / CURRENT_POINTER_REPAIR_READBACK_VERIFIED"
    assert result["summary"]["readback_verified"] is True
    assert result["summary"]["execution_marker_present"] is True
    assert result["summary"]["current_pointer_repaired"] is True
    assert result["summary"]["canonical_mutation_performed"] is False
    assert result["writes_performed"] is False
    assert _file_listing(tmp_path) == before


def test_persisted_graph_current_rendering_proof_cli_blocks_pending_artifact_without_writes(
    tmp_path: Path,
    capsys,
) -> None:
    approval, digest = _seed_pending_approval(tmp_path)
    before = _file_listing(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "persisted-graph-current-rendering-proof",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "studio.persisted-graph-current-rendering-proof"
    assert result["surface"] == "persisted_graph_current_rendering_proof"
    assert "readback_verified_if_required" in result["blocked_reasons"]
    assert "persisted_current_snapshot_used" in result["blocked_reasons"]
    assert result["summary"]["persisted_current_rendering_verified"] is False
    assert result["writes_performed"] is False
    assert _file_listing(tmp_path) == before


def test_persisted_graph_current_rendering_proof_cli_verifies_after_approved_execution_without_writes(
    tmp_path: Path,
    capsys,
) -> None:
    approval, digest = _seed_pending_approval(tmp_path)
    decision_statement = required_current_pointer_repair_approval_decision_statement(
        approval_packet_id=approval["approval_packet_id"],
        approval_digest=digest,
        decision="approved",
    )
    decision_exit = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-approval-decision",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--decision",
            "approved",
            "--operator-statement",
            decision_statement,
            "--write-decision",
            "--json",
        ]
    )
    decision_payload = json.loads(capsys.readouterr().out)
    execution_statement = required_current_pointer_repair_execution_statement(
        approval_packet_id=approval["approval_packet_id"],
        approval_digest=digest,
    )
    execution_exit = cli.main(
        [
            "studio",
            "persisted-graph-current-pointer-repair-approved-execution",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--operator-statement",
            execution_statement,
            "--execute",
            "--json",
        ]
    )
    execution_payload = json.loads(capsys.readouterr().out)
    before = _file_listing(tmp_path)

    proof_exit = cli.main(
        [
            "studio",
            "persisted-graph-current-rendering-proof",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert decision_exit == 0
    assert decision_payload["result"]["summary"]["approval_decision_written"] is True
    assert execution_exit == 0
    assert execution_payload["result"]["summary"]["current_pointer_written"] is True
    assert proof_exit == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.persisted-graph-current-rendering-proof"
    assert result["status"] == "COMPLETE / PERSISTED_CURRENT_RENDERING_VERIFIED"
    assert result["summary"]["persisted_current_rendering_verified"] is True
    assert result["summary"]["repair_readback_verified"] is True
    assert result["summary"]["persisted_snapshot_used"] is True
    assert result["summary"]["default_renderer_mode"] == "2d"
    assert result["summary"]["default_node_count"] > 0
    assert result["writes_performed"] is False
    assert _file_listing(tmp_path) == before


def test_graph_current_pointer_repair_closeout_packet_cli_previews_without_writes(
    tmp_path: Path,
    capsys,
) -> None:
    approval, digest = _seed_pending_approval(tmp_path)
    before = _file_listing(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "graph-current-pointer-repair-closeout-packet",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.graph-current-pointer-repair-closeout-packet"
    assert result["surface"] == "graph_current_pointer_repair_closeout_packet"
    assert result["status"] == "READY / OPERATOR_DECISION_REQUIRED"
    assert result["summary"]["operator_decision_required"] is True
    assert result["summary"]["safe_to_call_update_goal_complete"] is False
    assert result["operator_packet"]["required_operator_statements"]["approve"].startswith(
        "APPROVE PERSISTED GRAPH CURRENT POINTER REPAIR ONLY:"
    )
    assert result["operator_packet"]["required_operator_statements"]["execute_after_approval"].startswith(
        "EXECUTE PERSISTED GRAPH CURRENT POINTER REPAIR ONLY:"
    )
    assert result["writes_performed"] is False
    assert result["authority"]["approval_decision_write_allowed"] is False
    assert result["authority"]["repairs_current_pointer"] is False
    assert result["authority"]["agent_bus_task_write_allowed"] is False
    assert _file_listing(tmp_path) == before


def test_graph_current_pointer_post_repair_closeout_cli_blocks_pending_artifact_without_writes(
    tmp_path: Path,
    capsys,
) -> None:
    approval, digest = _seed_pending_approval(tmp_path)
    before = _file_listing(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "graph-current-pointer-post-repair-closeout",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval["approval_packet_id"],
            "--approval-digest",
            digest,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "studio.graph-current-pointer-post-repair-closeout"
    assert result["surface"] == "graph_current_pointer_post_repair_closeout"
    assert result["status"] == "BLOCKED / POST_REPAIR_GRAPH_CLOSEOUT_NOT_READY"
    assert "repair_readback_verified" in result["blocked_reasons"]
    assert "persisted_current_rendering_verified" in result["blocked_reasons"]
    assert result["summary"]["post_repair_closeout_verified"] is False
    assert result["writes_performed"] is False
    assert result["authority"]["repairs_current_pointer"] is False
    assert result["authority"]["approval_execution_allowed"] is False
    assert result["authority"]["agent_bus_task_write_allowed"] is False
    assert result["authority"]["canonical_mutation_allowed"] is False
    assert _file_listing(tmp_path) == before


def test_graph_current_pointer_repair_rehearsal_cli_verifies_copied_workspace_without_live_repair(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    _use_short_evidence_paths(monkeypatch)
    _seed_vault(tmp_path)
    _seed_runtime_overlay_evidence(tmp_path)
    status = build_persisted_graph_storage_status(tmp_path)
    readiness = status["repair_readiness"]
    preview = status["repair_approval_preview"]
    current_pointer = tmp_path / "runtime" / "graph" / "store" / "manifests" / "current.json"
    approval_artifact = tmp_path / preview["future_approval_artifact_path"]
    execution_marker = tmp_path / preview["future_execution_marker_path"]
    current_before = current_pointer.read_text(encoding="utf-8")
    approval_before = approval_artifact.read_text(encoding="utf-8")

    exit_code = cli.main(
        [
            "studio",
            "graph-current-pointer-repair-rehearsal",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            readiness["approval_packet_id"],
            "--approval-digest",
            readiness["approval_digest"],
            "--rehearsal-slug",
            "cli-rehearsal",
            "--rehearsal-root",
            "r",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.graph-current-pointer-repair-rehearsal"
    assert result["surface"] == "graph_current_pointer_repair_rehearsal"
    assert result["status"] == "COMPLETE / CURRENT_POINTER_REPAIR_REHEARSAL_VERIFIED"
    assert result["summary"]["repair_rehearsal_verified"] is True
    assert result["summary"]["source_protected_files_unchanged"] is True
    assert result["summary"]["live_writes_performed"] is False
    assert result["summary"]["bounded_rehearsal_workspace_written"] is True
    assert (tmp_path / result["summary"]["rehearsal_workspace"]).is_dir()
    assert current_pointer.read_text(encoding="utf-8") == current_before
    assert approval_artifact.read_text(encoding="utf-8") == approval_before
    assert execution_marker.exists() is False


def test_graph_current_pointer_repair_rehearsal_cli_accepts_approved_source_artifact(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    _use_short_evidence_paths(monkeypatch)
    _seed_vault(tmp_path)
    _seed_runtime_overlay_evidence(tmp_path)
    initial_status = build_persisted_graph_storage_status(tmp_path)
    readiness = initial_status["repair_readiness"]
    preview = initial_status["repair_approval_preview"]
    current_pointer = tmp_path / "runtime" / "graph" / "store" / "manifests" / "current.json"
    approval_artifact = tmp_path / preview["future_approval_artifact_path"]
    execution_marker = tmp_path / preview["future_execution_marker_path"]
    _approve_current_pointer_repair(tmp_path)
    current_before = current_pointer.read_text(encoding="utf-8")
    approval_before = approval_artifact.read_text(encoding="utf-8")

    exit_code = cli.main(
        [
            "studio",
            "graph-current-pointer-repair-rehearsal",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            readiness["approval_packet_id"],
            "--approval-digest",
            readiness["approval_digest"],
            "--rehearsal-slug",
            "cli-approved-rehearsal",
            "--rehearsal-root",
            "r",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 0
    assert payload["ok"] is True
    assert result["status"] == "COMPLETE / CURRENT_POINTER_REPAIR_REHEARSAL_VERIFIED"
    assert result["summary"]["source_approval_artifact_status"] == "approved"
    assert result["summary"]["rehearsal_source_approval_mode"] == "execute_from_approved_source_artifact"
    assert result["summary"]["next_recommended_pass"] == "persisted-graph-current-pointer-repair-approved-execution"
    assert result["evidence"]["rehearsal_decision"]["summary"]["approval_decision_written"] is False
    assert result["evidence"]["rehearsal_execution"]["summary"]["current_pointer_written"] is True
    assert current_pointer.read_text(encoding="utf-8") == current_before
    assert approval_artifact.read_text(encoding="utf-8") == approval_before
    assert execution_marker.exists() is False
