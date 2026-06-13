"""Tests for the read-only personal operator context index."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.personal_operator_context_index import (
    ROOT_HUB_PATH,
    SURFACE_ID,
    build_personal_operator_context_index,
)


def _write(vault: Path, relative_path: str, text: str) -> None:
    path = vault / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_personal_context(vault: Path, *, dashboard_links_soul: bool = True) -> None:
    dashboard_links = [
        "[[Personal-Operator-Index]]",
        "[[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-intake-implementation-map]]",
        "[[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-final-node-coverage-audit|Personal Context Final Node Coverage Audit]]",
        "[[00_HOME/Personal-Domains/Personal-Domains-Index|Personal Domains Index]]",
        "[[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]",
    ]
    if dashboard_links_soul:
        dashboard_links.insert(0, "[[SOUL]]")

    _write(vault, "SOUL.md", "# SOUL\n")
    _write(vault, "00_HOME/Principles.md", "# Principles\n")
    _write(vault, "00_HOME/Operating-System.md", "# Operating System\n")
    _write(vault, "00_HOME/Now.md", "# Now\n")
    _write(vault, "00_HOME/Dashboard.md", "# Dashboard\n" + "\n".join(dashboard_links) + "\n")
    _write(
        vault,
        ROOT_HUB_PATH,
        (
            "# Personal Operator Index\n"
            "[[03_INPUTS/Personal-Context-Intake/2026-05-15_personal-context-intake-packet]]\n"
            "[[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-intake-implementation-map]]\n"
            "[[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-final-node-coverage-audit]]\n"
            "[[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]\n"
            "[[01_PROJECTS/University/Modules/Modules|University Modules]]\n"
            "[[00_HOME/Personal-Domains/Personal-Domains-Index|Personal Domains Index]]\n"
            "[[07_LOGS/Pulse-Decks/memory-candidates/personal-map/2026-05-16-personal-life-domain-candidates-review|Personal Life-Domain Candidate Review]]\n"
            "[[02_KNOWLEDGE/AI-Agents/Prompt-Engineering|Prompt Engineering]]\n"
            "[[02_KNOWLEDGE/AI-Agents/Tool-Use|Tool Use]]\n"
            "[[02_KNOWLEDGE/Runtime-Ops/Runtime-Ops|Runtime Ops]]\n"
            "[[02_KNOWLEDGE/Runtime-Ops/WSL2-Ubuntu-Setup-Guide|WSL2 Ubuntu Setup Guide]]\n"
            "[[02_KNOWLEDGE/Runtime-Ops/Linux-Commands|Linux Commands]]\n"
            "[[02_KNOWLEDGE/Platform-Strategy/Platform-Strategy|Platform Strategy]]\n"
            "[[02_KNOWLEDGE/Platform-Strategy/Action-Matrix|Action Matrix]]\n"
            "[[02_KNOWLEDGE/Trading-Systems/Funding-Rates|Funding Rates]]\n"
            "[[02_KNOWLEDGE/Cybersecurity/Vulnerability-Patterns|Vulnerability Patterns]]\n"
            "[[02_KNOWLEDGE/Full-Stack/Backend-Architecture|Backend Architecture]]\n"
            "[[02_KNOWLEDGE/Content-Distribution/Content-Distribution|Content Distribution]]\n"
            "[[01_PROJECTS/Language-Mobility/Mandarin|Mandarin / HSK 1 Operating Lane]]\n"
            "[[02_KNOWLEDGE/Language/Mandarin-HSK1|Mandarin / HSK 1]]\n"
        ),
    )
    _write(
        vault,
        "KNOWLEDGE-INDEX.md",
        (
            "type: knowledge-index-routing-shim\n"
            "status: ROUTING SHIM / NOT CANONICAL\n"
            "canonical_target: 02_KNOWLEDGE/Knowledge-Index.md\n"
            "[[00_HOME/Personal-Operator-Index|Personal Operator Index]]\n"
            "[[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]\n"
            "[[01_PROJECTS/University/Modules/Modules|University Modules]]\n"
        ),
    )
    _write(
        vault,
        "02_KNOWLEDGE/Knowledge-Index.md",
        (
            "[[00_HOME/Personal-Operator-Index|Personal Operator Index]]\n"
            "[[01_PROJECTS/University/Modules/Modules|University Modules]]\n"
        ),
    )
    _write(vault, "01_PROJECTS/University/Degree-OS.md", "[[Modules/Modules|University Modules]]\n")
    _write(vault, "02_KNOWLEDGE/Computer-Science/Computer-Science.md", "## University Module Tree\n")
    _write(vault, "02_KNOWLEDGE/Doctrine/Doctrine-Philosophy.md", "[[00_HOME/Personal-Operator-Index|Personal Operator Index]]\n")
    _write(vault, "02_KNOWLEDGE/AI-Agents/AI-Agent-Engineering.md", "[[Tool-Use]]\n")
    _write(
        vault,
        "02_KNOWLEDGE/Runtime-Ops/Runtime-Ops.md",
        "[[WSL2-Ubuntu-Setup-Guide]]\n[[Linux-Commands]]\n",
    )
    _write(vault, "02_KNOWLEDGE/Platform-Strategy/Platform-Strategy.md", "[[Action-Matrix]]\n")
    _write(
        vault,
        "02_KNOWLEDGE/Trading-Systems/Trading-Systems-Engineering.md",
        "[[Funding-Rates]]\n[[Order-Flow]]\n[[Morning-Thesis]]\n[[Trade-Journal]]\n[[Risk-Management]]\n",
    )
    _write(
        vault,
        "02_KNOWLEDGE/Cybersecurity/Cybersecurity.md",
        "[[Vulnerability-Patterns]]\n[[Lab-Writeups]]\n[[Agent-Security]]\n[[Credential-Boundaries]]\n",
    )
    _write(vault, "02_KNOWLEDGE/Full-Stack/Full-Stack-Engineering.md", "[[React]]\n[[Backend-Architecture]]\n[[Solana-Future]]\n")
    _write(
        vault,
        "03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index.md",
        (
            "[[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]\n"
            "[[2026-05-16_personal-context-final-node-coverage-audit|final node coverage audit]]\n"
        ),
    )
    _write(
        vault,
        "03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-final-node-coverage-audit.md",
        "[[ChaseOS-Core]]\n[[ChaseOS-Personal]]\n[[Source-Intelligence-Core]]\n",
    )
    _write(vault, "06_AGENTS/Personal-Map-Architecture.md", "[[00_HOME/Personal-Operator-Index|Personal Operator Index]]\n")
    _write(vault, "06_AGENTS/Personal-Context-Import-Feature.md", "# Personal Context Import Feature\n")
    _write(vault, "06_AGENTS/Vault-Map.md", "Personal-Context-Intake context intake\n")
    _write(
        vault,
        "00_HOME/Personal-Domains/Language-Learning-Global-Mobility.md",
        "[[01_PROJECTS/Language-Mobility/Mandarin]]\n[[02_KNOWLEDGE/Language/Mandarin-HSK1]]\n",
    )
    _write(
        vault,
        "02_KNOWLEDGE/Language/Language-Learning.md",
        "[[01_PROJECTS/Language-Mobility/Mandarin]]\n[[Mandarin-HSK1]]\n",
    )
    _write(vault, "01_PROJECTS/ChaseOS/ChaseOS-OS.md", "# ChaseOS OS\n")
    _write(vault, "05_TEMPLATES/Personal-Map-Node-Template.md", "# Personal Map Node Template\n")
    _write(vault, "00_HOME/.workspace-mode.yaml", "mode: personal_os\n")


def test_context_index_groups_personal_surfaces_and_preserves_boundaries(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_personal_context(vault)

    panel = build_personal_operator_context_index(vault)

    assert panel["surface"] == SURFACE_ID
    assert panel["status"] in {"ready_for_review", "ready_with_warnings"}
    assert panel["root_hub_path"] == ROOT_HUB_PATH
    assert panel["summary"]["group_count"] == 11
    assert panel["summary"]["tracked_file_count"] > panel["summary"]["existing_file_count"]
    assert panel["summary"]["link_check_passed_count"] == panel["summary"]["link_check_count"]
    assert panel["summary"]["project_operating_file_count"] >= 20
    assert panel["summary"]["knowledge_root_count"] >= 10
    assert {group["id"] for group in panel["groups"]} >= {
        "identity_doctrine",
        "context_intake_sources",
        "personal_life_domain_nodes",
        "source_derived_standalone_nodes",
        "project_operating_files",
        "university_module_tree",
        "knowledge_roots",
        "personal_map_memory",
        "personal_map_candidate_reviews",
        "workspace_mode_profiles",
        "update_templates",
    }
    assert panel["summary"]["context_intake_file_count"] == 9
    assert panel["summary"]["personal_life_domain_file_count"] == 6
    assert panel["summary"]["source_derived_standalone_node_count"] == 50
    assert panel["summary"]["personal_map_candidate_review_file_count"] == 3
    assert panel["summary"]["university_module_file_count"] >= 20
    assert panel["authority"]["read_only"] is True
    assert panel["authority"]["writes_vault"] is False
    assert panel["authority"]["personal_map_mutation_allowed"] is False
    assert panel["authority"]["canonical_mutation_allowed"] is False
    assert panel["graph"]["root_hub_path"] == ROOT_HUB_PATH


def test_context_index_reports_missing_dashboard_soul_link_as_blocker(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_personal_context(vault, dashboard_links_soul=False)

    panel = build_personal_operator_context_index(vault)

    assert panel["status"] == "blocked_link_repair_required"
    assert panel["summary"]["link_blocker_count"] == 1
    assert [item["id"] for item in panel["link_blockers"]] == ["dashboard_links_soul"]
