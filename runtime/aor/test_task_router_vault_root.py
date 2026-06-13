from __future__ import annotations

from pathlib import Path

from runtime.aor.task_router import classify, list_task_types


def test_task_router_prefers_vault_root_task_type_table(tmp_path: Path) -> None:
    table = tmp_path / "runtime" / "aor" / "task_type_table.yaml"
    table.parent.mkdir(parents=True)
    table.write_text(
        "\n".join(
            [
                "task_types:",
                "  - id: packaged-only-type",
                "    description: Packaged runtime fixture",
                "    required_reads: []",
                "    optional_reads: []",
                "    runtime_class: read-heavy",
                "    permission_set:",
                "      - read_vault",
                "    permission_ceiling: proposal_log_only",
                "    writeback_expectations: fixture only",
                "    escalation_trigger:",
                "      - fixture escalation",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = classify("packaged-only-type", vault_root=tmp_path)

    assert result["id"] == "packaged-only-type"
    assert result["permission_ceiling"] == "proposal_log_only"
    assert classify("operator-briefing", vault_root=tmp_path)["id"] == "unclassified"
    assert [item["id"] for item in list_task_types(vault_root=tmp_path)] == ["packaged-only-type"]
