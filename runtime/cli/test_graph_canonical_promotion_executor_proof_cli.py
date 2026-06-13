"""CLI tests for graph canonical promotion executor proof."""

from __future__ import annotations

import json
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parents[2]
if str(VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402


def _seed_vault(root: Path) -> None:
    (root / "runtime" / "acquisition" / "packs").mkdir(parents=True)
    (root / "runtime" / "acquisition" / "packs" / "strikezone-latest.json").write_text(
        json.dumps({"profile": "strikezone", "reviewed": True, "normalized_source_pack": "pack.json"}),
        encoding="utf-8",
    )
    (root / "06_AGENTS").mkdir(parents=True)
    (root / "06_AGENTS" / "Permission-Matrix.md").write_text("# Protected\n", encoding="utf-8")


def test_graph_canonical_promotion_executor_proof_cli_json(tmp_path, capsys) -> None:
    _seed_vault(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "graph-canonical-promotion-executor-proof",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.graph-canonical-promotion-executor-proof"
    assert result["surface"] == "graph_source_pack_canonical_promotion_executor_proof"
    assert result["candidate_packet"]["approved_candidate_packet"] is True
    assert result["derived_vs_canonical_graph"]["canonical_graph_mutation_performed"] is False
    assert result["source_pack_promotion_state"]["promotion_state_written"] is False
    assert result["protected_file_denial_proof"]["denial_proven"] is True
    assert result["rollback_rejection_behavior"]["rollback_path_modeled"] is True
    assert result["authority"]["knowledge_promotion_write_allowed"] is False


def test_graph_canonical_promotion_executor_proof_cli_text_output(tmp_path, capsys) -> None:
    _seed_vault(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "graph-canonical-promotion-executor-proof",
            "--vault-root",
            str(tmp_path),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Graph / Source-Pack / Canonical Promotion Backend Executor Proof" in output
    assert "approved_candidate_packet: True" in output
    assert "canonical_graph_mutation_performed: False" in output
    assert "protected_file_denial_proven: True" in output
    assert "Boundary: lower-phase executor proof only" in output
