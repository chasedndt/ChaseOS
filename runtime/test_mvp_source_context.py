from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.mvp_source_context import build_mvp_source_context_bridge  # noqa: E402


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _seed_source_context_fixture(root: Path) -> None:
    _write_text(root / "06_AGENTS" / "Agent-Control-Plane.md", "# Agent Control Plane\n\n[[Permission-Matrix]]\n")
    _write_text(root / "06_AGENTS" / "Permission-Matrix.md", "# Permission Matrix\n\n[[Trust-Tiers]]\n")
    _write_text(root / "06_AGENTS" / "Trust-Tiers.md", "# Trust Tiers\n")
    _write_text(root / "06_AGENTS" / "Backends-Supported.md", "# Backends Supported\n")

    _write_text(
        root / "runtime" / "workflows" / "registry" / "ventureops_ai_runtime_security_audit.yaml",
        "\n".join(
            [
                "id: ventureops_ai_runtime_security_audit",
                "status: active",
                "required_reads:",
                '  - "06_AGENTS/Agent-Control-Plane.md"',
                '  - "06_AGENTS/Permission-Matrix.md"',
                '  - "06_AGENTS/Trust-Tiers.md"',
                '  - "06_AGENTS/Backends-Supported.md"',
                "audit_expectations:",
                '  - "no canonical promotion attempted"',
            ]
        )
        + "\n",
    )

    source_package = root / "runtime" / "source_intelligence" / "workspaces" / "phase7-test" / "sources" / "demo.json"
    _write_json(source_package, {"id": "source-1", "title": "Demo Source"})
    _write_json(
        root / "runtime" / "source_intelligence" / "workspaces" / "phase7-test" / "workspace.json",
        {
            "slug": "phase7-test",
            "status": "active",
            "source_count": 1,
            "index_status": "indexed",
            "query_scope": "workspace-only",
            "source_refs": {
                "source-1": {
                    "source_package_id": "source-1",
                    "source_package_path": str(source_package),
                    "source_type": "research-digest",
                    "title": "Demo Source",
                    "origin_path": str(root / "03_INPUTS" / "demo.md"),
                    "extraction_status": "complete",
                    "embedding_status": "embedded",
                    "user_trust_level": "untrusted",
                }
            },
        },
    )


def test_mvp_source_context_bridge_references_workflow_sources_and_graph_without_mutation(tmp_path: Path) -> None:
    _seed_source_context_fixture(tmp_path)

    payload = build_mvp_source_context_bridge(tmp_path)

    assert payload["ok"] is True
    assert payload["status"] == "ready_for_read_only_workflow_context_reference"
    assert payload["workflow_context"]["workflow_can_reference_source_context"] is True
    assert payload["workflow_context"]["workflow_can_reference_graph_context"] is True
    assert payload["workflow_context"]["workflow_can_reference_context_without_mutation"] is True
    assert payload["source_context"]["reference_count"] == 1
    assert payload["graph_context"]["resolved_reference_count"] >= 4
    assert payload["authority"]["read_only"] is True
    assert payload["authority"]["source_package_promotion_allowed"] is False
    assert payload["authority"]["graph_mutation_allowed"] is False
    assert payload["authority"]["canonical_mutation_allowed"] is False
    assert payload["authority"]["provider_calls_allowed"] is False
    assert payload["blockers"] == []

