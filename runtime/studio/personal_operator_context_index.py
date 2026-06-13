"""Read-only Studio personal operator context index.

This module groups the personal-instance surfaces ChaseOS should review before
real-world use. It only reads vault files and reports link health; it does not
write Personal Map, Pulse, companion memory, project truth, provider state, or
canonical runtime state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.personal_operator_context_index.v1"
SURFACE_ID = "studio_personal_operator_context_index"
ROOT_HUB_PATH = "00_HOME/Personal-Operator-Index.md"

_CONTEXT_INTAKE_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "id": "personal_context_intake_index",
        "label": "Personal Context Intake Index",
        "path": "03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index.md",
        "status": "ACTIVE INDEX",
        "boundary": "routes raw imports and promotion queues",
    },
    {
        "id": "personal_context_import_feature",
        "label": "Personal Context Import Feature",
        "path": "06_AGENTS/Personal-Context-Import-Feature.md",
        "status": "PARTIAL / CANONICAL PROMOTION APPROVED EXECUTOR READY / PERSONAL MAP AND RUNTIME MUTATIONS BLOCKED",
        "boundary": "Studio import planner, digest-gated approval preview writer, approved-preview artifact executor, temp-only fixture harness, runtime reference readiness, and feature contract; no canonical import writes",
    },
    {
        "id": "personal_context_intake_raw_packet",
        "label": "Raw Personal Context Intake Packet",
        "path": "03_INPUTS/Personal-Context-Intake/2026-05-15_personal-context-intake-packet.md",
        "status": "TIER 4 RAW INPUT",
        "boundary": "not canonical until reviewed/promoted",
    },
    {
        "id": "personal_context_intake_implementation_map",
        "label": "Personal Context Intake Implementation Map",
        "path": "03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-intake-implementation-map.md",
        "status": "PROMOTION MAP",
        "boundary": "review and routing surface only",
    },
    {
        "id": "personal_context_source_digest",
        "label": "Personal Context Source Digest",
        "path": "03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-source-digest.md",
        "status": "SOURCE-DERIVED DIGEST",
        "boundary": "usable agent context with candidate/unknown labels preserved",
    },
    {
        "id": "personal_context_promotion_queue",
        "label": "Personal Context Promotion Queue",
        "path": "03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-promotion-queue.md",
        "status": "CANDIDATE REVIEW QUEUE",
        "boundary": "candidate/generated/uncertain items only",
    },
    {
        "id": "personal_context_node_reaudit_source",
        "label": "Personal Context Node Reaudit Source",
        "path": "03_INPUTS/Personal-Context-Intake/2026-05-16_n-personal-context-node-reaudit-source.md",
        "status": "TIER 4 RAW INPUT",
        "boundary": "raw source for standalone-node reaudit",
    },
    {
        "id": "personal_context_node_reaudit",
        "label": "Personal Context Node Reaudit",
        "path": "03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-node-reaudit.md",
        "status": "SOURCE-DERIVED / REVIEW REQUIRED",
        "boundary": "routes missing standalone nodes from n.md",
    },
    {
        "id": "personal_context_final_node_coverage_audit",
        "label": "Personal Context Final Node Coverage Audit",
        "path": "03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-final-node-coverage-audit.md",
        "status": "SOURCE-DERIVED / REVIEW REQUIRED",
        "boundary": "maps source-explicit nodes to implemented nodes or routed equivalents",
    },
)

_UNIVERSITY_MODULE_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "id": "university_modules_index",
        "label": "University Modules",
        "path": "01_PROJECTS/University/Modules/Modules.md",
        "status": "ACTIVE INDEX",
    },
    {
        "id": "university_concept_to_project_map",
        "label": "University Concept to Project Map",
        "path": "01_PROJECTS/University/Modules/Concept-to-Project-Map.md",
        "status": "ACTIVE ROUTING MAP",
    },
    {
        "id": "university_coursework_tracker",
        "label": "Coursework Tracker",
        "path": "01_PROJECTS/University/Modules/Coursework-Tracker.md",
        "status": "ACTIVE TRACKER",
    },
    {
        "id": "university_lab_log",
        "label": "Lab Log",
        "path": "01_PROJECTS/University/Modules/Lab-Log.md",
        "status": "ACTIVE LOG",
    },
    {
        "id": "university_revision_queue",
        "label": "Revision Queue",
        "path": "01_PROJECTS/University/Modules/Revision-Queue.md",
        "status": "ACTIVE QUEUE",
    },
    {
        "id": "comp1765_computer_and_communication_systems",
        "label": "COMP1765 Computer and Communication Systems",
        "path": "01_PROJECTS/University/Modules/COMP1765-Computer-and-Communication-Systems.md",
        "status": "MODULE NODE",
    },
    {
        "id": "comp1811_paradigms_of_programming",
        "label": "COMP1811 Paradigms of Programming",
        "path": "01_PROJECTS/University/Modules/COMP1811-Paradigms-of-Programming.md",
        "status": "MODULE NODE",
    },
    {
        "id": "comp1819_algorithms_and_data_structures",
        "label": "COMP1819 Algorithms and Data Structures",
        "path": "01_PROJECTS/University/Modules/COMP1819-Algorithms-and-Data-Structures.md",
        "status": "MODULE NODE",
    },
    {
        "id": "comp1820_introduction_to_compilers",
        "label": "COMP1820 Introduction to Compilers",
        "path": "01_PROJECTS/University/Modules/COMP1820-Introduction-to-Compilers.md",
        "status": "MODULE NODE",
    },
    {
        "id": "comp1821_principles_of_software_engineering",
        "label": "COMP1821 Principles of Software Engineering",
        "path": "01_PROJECTS/University/Modules/COMP1821-Principles-of-Software-Engineering.md",
        "status": "MODULE NODE",
    },
    {
        "id": "math1179_mathematics_for_computer_science",
        "label": "MATH1179 Mathematics for Computer Science",
        "path": "01_PROJECTS/University/Modules/MATH1179-Mathematics-for-Computer-Science.md",
        "status": "MODULE NODE",
    },
    {
        "id": "math1197_advanced_mathematics_for_computer_science",
        "label": "MATH1197 Advanced Mathematics for Computer Science",
        "path": "01_PROJECTS/University/Modules/MATH1197-Advanced-Mathematics-for-Computer-Science.md",
        "status": "MODULE NODE",
    },
    {
        "id": "comp1549_advanced_programming",
        "label": "COMP1549 Advanced Programming",
        "path": "01_PROJECTS/University/Modules/COMP1549-Advanced-Programming.md",
        "status": "CANDIDATE / FUTURE MODULE NODE",
    },
    {
        "id": "comp1562_operating_systems",
        "label": "COMP1562 Operating Systems",
        "path": "01_PROJECTS/University/Modules/COMP1562-Operating-Systems.md",
        "status": "CANDIDATE / FUTURE MODULE NODE",
    },
    {
        "id": "comp1806_information_security",
        "label": "COMP1806 Information Security",
        "path": "01_PROJECTS/University/Modules/COMP1806-Information-Security.md",
        "status": "CANDIDATE / FUTURE MODULE NODE",
    },
    {
        "id": "comp1814_statistical_techniques_with_r",
        "label": "COMP1814 Statistical Techniques with R",
        "path": "01_PROJECTS/University/Modules/COMP1814-Statistical-Techniques-with-R.md",
        "status": "CANDIDATE / FUTURE MODULE NODE",
    },
    {
        "id": "comp1827_introduction_to_ai",
        "label": "COMP1827 Introduction to Artificial Intelligence",
        "path": "01_PROJECTS/University/Modules/COMP1827-Introduction-to-Artificial-Intelligence.md",
        "status": "CANDIDATE / FUTURE MODULE NODE",
    },
    {
        "id": "comp1828_advanced_algorithms_and_data_structures",
        "label": "COMP1828 Advanced Algorithms and Data Structures",
        "path": "01_PROJECTS/University/Modules/COMP1828-Advanced-Algorithms-and-Data-Structures.md",
        "status": "CANDIDATE / FUTURE MODULE NODE",
    },
    {
        "id": "math1180_computational_methods_and_numerical_techniques",
        "label": "MATH1180 Computational Methods and Numerical Techniques",
        "path": "01_PROJECTS/University/Modules/MATH1180-Computational-Methods-and-Numerical-Techniques.md",
        "status": "CANDIDATE / FUTURE MODULE NODE",
    },
    {
        "id": "comp1649_hci_and_design",
        "label": "COMP1649 Human Computer Interaction and Design",
        "path": "01_PROJECTS/University/Modules/COMP1649-Human-Computer-Interaction-and-Design.md",
        "status": "CANDIDATE / FUTURE MODULE NODE",
    },
    {
        "id": "comp1682_final_year_projects",
        "label": "COMP1682 Final Year Projects",
        "path": "01_PROJECTS/University/Modules/COMP1682-Final-Year-Projects.md",
        "status": "CANDIDATE / FUTURE MODULE NODE",
    },
    {
        "id": "comp1805_natural_computing",
        "label": "COMP1805 Natural Computing",
        "path": "01_PROJECTS/University/Modules/COMP1805-Natural-Computing.md",
        "status": "CANDIDATE / FUTURE MODULE NODE",
    },
    {
        "id": "year3_machine_learning",
        "label": "Year 3 Machine Learning",
        "path": "01_PROJECTS/University/Modules/YEAR3-Machine-Learning.md",
        "status": "CANDIDATE / MODULE CODE UNKNOWN",
    },
    {
        "id": "comp1818_ai_applications",
        "label": "COMP1818 Artificial Intelligence Applications",
        "path": "01_PROJECTS/University/Modules/COMP1818-Artificial-Intelligence-Applications.md",
        "status": "CANDIDATE / FUTURE MODULE NODE",
    },
)

_PERSONAL_DOMAIN_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "id": "personal_domains_index",
        "label": "Personal Domains Index",
        "path": "00_HOME/Personal-Domains/Personal-Domains-Index.md",
        "status": "ACTIVE INDEX",
        "boundary": "personal OS life-domain routing",
    },
    {
        "id": "fitness_combat_physical_discipline",
        "label": "Fitness / Combat / Physical Discipline",
        "path": "00_HOME/Personal-Domains/Fitness-Combat-Physical-Discipline.md",
        "status": "SOURCE-DERIVED / REVIEW REQUIRED",
    },
    {
        "id": "interests_knowledge_domains",
        "label": "Interests / Knowledge Domains",
        "path": "00_HOME/Personal-Domains/Interests-Knowledge-Domains.md",
        "status": "SOURCE-DERIVED / REVIEW REQUIRED",
    },
    {
        "id": "language_learning_global_mobility",
        "label": "Language Learning / Global Mobility",
        "path": "00_HOME/Personal-Domains/Language-Learning-Global-Mobility.md",
        "status": "SOURCE-DERIVED / REVIEW REQUIRED",
    },
    {
        "id": "networking_social_capital_personal",
        "label": "Networking / Social Capital",
        "path": "00_HOME/Personal-Domains/Networking-Social-Capital.md",
        "status": "SOURCE-DERIVED / REVIEW REQUIRED",
    },
    {
        "id": "hardware_systems_future_robotics",
        "label": "Hardware / Systems / Future Robotics",
        "path": "00_HOME/Personal-Domains/Hardware-Systems-Future-Robotics.md",
        "status": "SOURCE-DERIVED / REVIEW REQUIRED",
    },
)

_PERSONAL_MAP_CANDIDATE_REVIEW_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "id": "personal_map_life_domain_candidate_log",
        "label": "2026-05-16 Personal Map Candidate Log",
        "path": "07_LOGS/Pulse-Decks/memory-candidates/personal-map/2026-05-16-personal-map-candidates.jsonl",
        "status": "PENDING REVIEW / CANDIDATE LOG",
        "boundary": "append-only candidate records; no canonical apply",
    },
    {
        "id": "personal_map_life_domain_candidate_review",
        "label": "Personal Life-Domain Candidate Review",
        "path": "07_LOGS/Pulse-Decks/memory-candidates/personal-map/2026-05-16-personal-life-domain-candidates-review.md",
        "status": "PENDING REVIEW / OPERATOR DECK",
        "boundary": "review surface only",
    },
    {
        "id": "personal_map_life_domain_candidate_generator",
        "label": "Personal Life-Domain Candidate Generator",
        "path": "runtime/studio/personal_life_domain_personal_map_candidates.py",
        "status": "REVIEW-GATED GENERATOR",
        "boundary": "writes candidate log and review deck only",
    },
)

_SOURCE_DERIVED_STANDALONE_ITEMS: tuple[dict[str, Any], ...] = (
    {"id": "prompt_engineering", "label": "Prompt Engineering", "path": "02_KNOWLEDGE/AI-Agents/Prompt-Engineering.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "agent_engineering", "label": "Agent Engineering", "path": "02_KNOWLEDGE/AI-Agents/Agent-Engineering.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "runtime_engineering", "label": "Runtime Engineering", "path": "02_KNOWLEDGE/AI-Agents/Runtime-Engineering.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "rag", "label": "RAG", "path": "02_KNOWLEDGE/AI-Agents/RAG.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "mcp", "label": "MCP", "path": "02_KNOWLEDGE/AI-Agents/MCP.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "source_intelligence", "label": "Source Intelligence", "path": "02_KNOWLEDGE/AI-Agents/Source-Intelligence.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "multi_runtime_systems", "label": "Multi-Runtime Systems", "path": "02_KNOWLEDGE/AI-Agents/Multi-Runtime-Systems.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "execution_adapters", "label": "Execution Adapters", "path": "02_KNOWLEDGE/AI-Agents/Execution-Adapters.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "tool_use", "label": "Tool Use", "path": "02_KNOWLEDGE/AI-Agents/Tool-Use.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "agent_control_plane", "label": "Agent Control Plane", "path": "06_AGENTS/Agent-Control-Plane.md", "status": "EXISTING GOVERNANCE DOC / SOURCE-ROUTED"},
    {"id": "chaseos_core", "label": "ChaseOS Core", "path": "06_AGENTS/ChaseOS-Core.md", "status": "SOURCE-DERIVED ROUTING BRIDGE / REVIEW REQUIRED"},
    {"id": "chaseos_personal", "label": "ChaseOS Personal", "path": "06_AGENTS/ChaseOS-Personal.md", "status": "SOURCE-DERIVED ROUTING BRIDGE / REVIEW REQUIRED"},
    {"id": "source_intelligence_core", "label": "Source Intelligence Core", "path": "06_AGENTS/Source-Intelligence-Core.md", "status": "SOURCE-DERIVED ROUTING BRIDGE / REVIEW REQUIRED"},
    {"id": "autonomous_operator_runtime", "label": "Autonomous Operator Runtime", "path": "06_AGENTS/Autonomous-Operator-Runtime.md", "status": "EXISTING GOVERNANCE DOC / SOURCE-ROUTED"},
    {"id": "chaseos_studio_architecture", "label": "ChaseOS Studio Architecture", "path": "06_AGENTS/ChaseOS-Studio-Architecture.md", "status": "EXISTING GOVERNANCE DOC / SOURCE-ROUTED"},
    {"id": "runtime_ops", "label": "Runtime Ops / Linux / Infrastructure", "path": "02_KNOWLEDGE/Runtime-Ops/Runtime-Ops.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "linux_wsl_cli", "label": "Linux / WSL / CLI", "path": "02_KNOWLEDGE/Runtime-Ops/Linux-WSL-CLI.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "wsl2_ubuntu_setup_guide", "label": "WSL2 Ubuntu Setup Guide", "path": "02_KNOWLEDGE/Runtime-Ops/WSL2-Ubuntu-Setup-Guide.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "linux_commands", "label": "Linux Commands", "path": "02_KNOWLEDGE/Runtime-Ops/Linux-Commands.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "hermes_runbook", "label": "Hermes Runbook", "path": "02_KNOWLEDGE/Runtime-Ops/Hermes-Runbook.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "openclaw_runbook", "label": "OpenClaw Runbook", "path": "02_KNOWLEDGE/Runtime-Ops/OpenClaw-Runbook.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "platform_strategy", "label": "Platform Strategy", "path": "02_KNOWLEDGE/Platform-Strategy/Platform-Strategy.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "sovereign_platform_playbook", "label": "Sovereign Platform Playbook", "path": "02_KNOWLEDGE/Platform-Strategy/Sovereign-Platform-Playbook.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "portfolio_diagnostic", "label": "Portfolio Diagnostic", "path": "02_KNOWLEDGE/Platform-Strategy/Portfolio-Diagnostic.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "action_matrix", "label": "Action Matrix", "path": "02_KNOWLEDGE/Platform-Strategy/Action-Matrix.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "venture_scorecards", "label": "Venture Scorecards", "path": "02_KNOWLEDGE/Platform-Strategy/Venture-Scorecards.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "funding_rates", "label": "Funding Rates", "path": "02_KNOWLEDGE/Trading-Systems/Funding-Rates.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "order_flow", "label": "Order Flow", "path": "02_KNOWLEDGE/Trading-Systems/Order-Flow.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "morning_thesis", "label": "Morning Thesis", "path": "02_KNOWLEDGE/Trading-Systems/Morning-Thesis.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "trade_journal", "label": "Trade Journal", "path": "02_KNOWLEDGE/Trading-Systems/Trade-Journal.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "risk_management", "label": "Risk Management", "path": "02_KNOWLEDGE/Trading-Systems/Risk-Management.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "vulnerability_patterns", "label": "Vulnerability Patterns", "path": "02_KNOWLEDGE/Cybersecurity/Vulnerability-Patterns.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "lab_writeups", "label": "Lab Writeups", "path": "02_KNOWLEDGE/Cybersecurity/Lab-Writeups.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "agent_security", "label": "Agent Security", "path": "02_KNOWLEDGE/Cybersecurity/Agent-Security.md", "status": "SOURCE-DERIVED ROUTING BRIDGE / REVIEW REQUIRED"},
    {"id": "credential_boundaries", "label": "Credential Boundaries", "path": "02_KNOWLEDGE/Cybersecurity/Credential-Boundaries.md", "status": "SOURCE-DERIVED ROUTING BRIDGE / REVIEW REQUIRED"},
    {"id": "react", "label": "React", "path": "02_KNOWLEDGE/Full-Stack/React.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "backend_architecture", "label": "Backend Architecture", "path": "02_KNOWLEDGE/Full-Stack/Backend-Architecture.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "solana_future", "label": "Solana Future", "path": "02_KNOWLEDGE/Full-Stack/Solana-Future.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "content_distribution", "label": "Content Distribution", "path": "02_KNOWLEDGE/Content-Distribution/Content-Distribution.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "digest_to_content", "label": "Digest to Content", "path": "02_KNOWLEDGE/Content-Distribution/Digest-to-Content.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "content_cta_systems", "label": "Content CTA Systems", "path": "02_KNOWLEDGE/Content-Distribution/Content-CTA-Systems.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "no_zero_days", "label": "No Zero Days", "path": "02_KNOWLEDGE/Doctrine/No-Zero-Days.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "decision_doctrine", "label": "Decision Doctrine", "path": "02_KNOWLEDGE/Doctrine/Decision-Doctrine.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "mandarin_hsk1_operating_lane", "label": "Mandarin / HSK 1 Operating Lane", "path": "01_PROJECTS/Language-Mobility/Mandarin.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "mandarin_hsk1_knowledge_node", "label": "Mandarin / HSK 1", "path": "02_KNOWLEDGE/Language/Mandarin-HSK1.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "indicator_registry", "label": "Indicator Registry", "path": "01_PROJECTS/StrikeZone/Indicator-Registry.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "freelancer_launchpad", "label": "Freelancer Launchpad", "path": "01_PROJECTS/CareerOps/Freelancer-Launchpad.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "career_networking", "label": "Career Networking", "path": "01_PROJECTS/CareerOps/Networking.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "bug_bounty_os", "label": "Bug Bounty OS", "path": "01_PROJECTS/Cybersecurity/Bug-Bounty-OS.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
    {"id": "content_cta_map", "label": "Content CTA Map", "path": "01_PROJECTS/ContentEngine/Content-CTA-Map.md", "status": "SOURCE-DERIVED / REVIEW REQUIRED"},
)


_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "id": "identity_doctrine",
        "label": "Identity and Doctrine",
        "purpose": "Protected personal identity, doctrine, and current operating context.",
        "items": (
            {
                "id": "soul",
                "label": "SOUL",
                "path": "SOUL.md",
                "status": "PROTECTED",
                "boundary": "explicit identity pass only",
            },
            {
                "id": "principles",
                "label": "Principles",
                "path": "00_HOME/Principles.md",
                "status": "PROTECTED",
                "boundary": "explicit doctrine pass only",
            },
            {
                "id": "operating_system",
                "label": "Operating System",
                "path": "00_HOME/Operating-System.md",
                "status": "PROTECTED",
                "boundary": "explicit OS/domain pass only",
            },
            {
                "id": "now",
                "label": "Now",
                "path": "00_HOME/Now.md",
                "status": "CURRENT TRUTH",
                "boundary": "evidence-backed updates only",
            },
            {
                "id": "dashboard",
                "label": "Dashboard",
                "path": "00_HOME/Dashboard.md",
                "status": "NAVIGATION",
                "boundary": "index and routing surface",
            },
            {
                "id": "personal_operator_index",
                "label": "Personal Operator Index",
                "path": ROOT_HUB_PATH,
                "status": "ACTIVE / INDEX ONLY",
                "boundary": "review map only",
            },
            {
                "id": "doctrine_philosophy",
                "label": "Doctrine / Philosophy",
                "path": "02_KNOWLEDGE/Doctrine/Doctrine-Philosophy.md",
                "status": "DOMAIN INDEX",
                "boundary": "knowledge-domain context",
            },
        ),
    },
    {
        "id": "context_intake_sources",
        "label": "Context Intake Sources",
        "purpose": "Raw and reviewed personal context imports used to update the personal operator instance.",
        "items": _CONTEXT_INTAKE_ITEMS,
    },
    {
        "id": "personal_life_domain_nodes",
        "label": "Personal Life-Domain Nodes",
        "purpose": "Operator-facing personal context nodes for fitness, interests, language, networking, and hardware lanes.",
        "items": _PERSONAL_DOMAIN_ITEMS,
    },
    {
        "id": "source_derived_standalone_nodes",
        "label": "Source-Derived Standalone Nodes",
        "purpose": "Standalone nodes extracted from n.md that were too important to remain only in SOUL, interests, or broad digests.",
        "items": _SOURCE_DERIVED_STANDALONE_ITEMS,
    },
    {
        "id": "project_operating_files",
        "label": "Project Operating Files",
        "purpose": "Personal project and domain operating files that carry real-world context.",
        "items": (
            {"id": "projects_hub", "label": "Projects Hub", "path": "01_PROJECTS/Projects-Hub.md"},
            {"id": "chaseos_os", "label": "ChaseOS OS", "path": "01_PROJECTS/ChaseOS/ChaseOS-OS.md"},
            {
                "id": "trading_systems_os",
                "label": "Trading Systems OS",
                "path": "01_PROJECTS/TradingSystems/TradingSystems-OS.md",
            },
            {"id": "crypto_perps_os", "label": "Crypto Perps OS", "path": "01_PROJECTS/TradingSystems/CryptoPerps-OS.md"},
            {"id": "dex_perps_os", "label": "DEX Perps OS", "path": "01_PROJECTS/TradingSystems/DEXPerps-OS.md"},
            {"id": "tradfi_perps_os", "label": "TradFi Perps OS", "path": "01_PROJECTS/TradingSystems/TradFiPerps-OS.md"},
            {"id": "strikezone_crypto_os", "label": "StrikeZone Crypto OS", "path": "01_PROJECTS/StrikeZone/StrikeZone-Crypto-OS.md"},
            {"id": "indicator_rnd_os", "label": "Indicator R&D OS", "path": "01_PROJECTS/IndicatorRnD/IndicatorRnD-OS.md"},
            {"id": "tradesync_os", "label": "TradeSync OS", "path": "01_PROJECTS/TradeSync/TradeSync-OS.md"},
            {"id": "geomacro_os", "label": "GeoMacro OS", "path": "01_PROJECTS/GeoMacro/GeoMacro-OS.md"},
            {
                "id": "full_stack_web2_web3_os",
                "label": "FullStackWeb2Web3 OS",
                "path": "01_PROJECTS/FullStackWeb2Web3/FullStackWeb2Web3-OS.md",
            },
            {"id": "hypelist_os", "label": "HypeList OS", "path": "01_PROJECTS/HypeList/HypeList-OS.md"},
            {"id": "cybersecurity_os", "label": "Cybersecurity OS", "path": "01_PROJECTS/Cybersecurity/Cybersecurity-OS.md"},
            {"id": "grey_theory_os", "label": "Grey Theory OS", "path": "01_PROJECTS/GreyTheory/GreyTheory-OS.md"},
            {"id": "degree_os", "label": "Degree OS", "path": "01_PROJECTS/University/Degree-OS.md"},
            {"id": "career_ops_os", "label": "Career Ops OS", "path": "01_PROJECTS/CareerOps/CareerOps-OS.md"},
            {
                "id": "content_creation_os",
                "label": "Content Creation OS",
                "path": "01_PROJECTS/ContentEngine/ContentCreation-OS.md",
            },
            {"id": "chase_in_tech_os", "label": "ChaseInTech OS", "path": "01_PROJECTS/ContentEngine/ChaseInTech-OS.md"},
            {"id": "chaser_sol_os", "label": "ChaserSol OS", "path": "01_PROJECTS/ContentEngine/ChaserSol-OS.md"},
            {"id": "businesses_os", "label": "Businesses OS", "path": "01_PROJECTS/Businesses/Businesses-OS.md"},
            {
                "id": "ecommerce_reselling_os",
                "label": "Ecommerce Reselling OS",
                "path": "01_PROJECTS/Businesses/EcommerceReselling-OS.md",
            },
            {"id": "marketplaces", "label": "Marketplaces", "path": "01_PROJECTS/Businesses/Marketplaces.md"},
            {"id": "dripndrown_os", "label": "DripNDrown OS", "path": "01_PROJECTS/DripNDrown/DripNDrown-OS.md"},
            {"id": "flipworks_os", "label": "FlipWorks OS", "path": "01_PROJECTS/FlipWorks/FlipWorks-OS.md"},
            {
                "id": "gpu_hardware_resale_os",
                "label": "GPU Hardware Resale OS",
                "path": "01_PROJECTS/GPUHardwareResale/GPUHardwareResale-OS.md",
            },
            {"id": "shopify_os", "label": "Shopify OS", "path": "01_PROJECTS/Shopify/Shopify-OS.md"},
            {"id": "vibecoding_os", "label": "VibeCoding OS", "path": "01_PROJECTS/VibeCoding/VibeCoding-OS.md"},
        ),
    },
    {
        "id": "university_module_tree",
        "label": "University Module Tree",
        "purpose": "Degree OS child nodes, coursework/revision surfaces, and module-to-project routing.",
        "items": _UNIVERSITY_MODULE_ITEMS,
    },
    {
        "id": "knowledge_roots",
        "label": "Knowledge Roots",
        "purpose": "Canonical knowledge entrypoints used to update doctrine and domain context.",
        "items": (
            {"id": "root_knowledge_index", "label": "Root Knowledge Index", "path": "KNOWLEDGE-INDEX.md"},
            {"id": "master_knowledge_index", "label": "Knowledge Index - Master", "path": "02_KNOWLEDGE/Knowledge-Index.md"},
            {"id": "ai_agent_engineering", "label": "AI Agent Engineering", "path": "02_KNOWLEDGE/AI-Agents/AI-Agent-Engineering.md"},
            {"id": "full_stack_engineering", "label": "Full-Stack Engineering", "path": "02_KNOWLEDGE/Full-Stack/Full-Stack-Engineering.md"},
            {"id": "computer_science", "label": "Computer Science", "path": "02_KNOWLEDGE/Computer-Science/Computer-Science.md"},
            {"id": "mathematics", "label": "Mathematics", "path": "02_KNOWLEDGE/Mathematics/Mathematics.md"},
            {"id": "cybersecurity", "label": "Cybersecurity", "path": "02_KNOWLEDGE/Cybersecurity/Cybersecurity.md"},
            {
                "id": "trading_systems_engineering",
                "label": "Trading Systems Engineering",
                "path": "02_KNOWLEDGE/Trading-Systems/Trading-Systems-Engineering.md",
            },
            {"id": "runtime_ops_knowledge", "label": "Runtime Ops / Linux / Infrastructure", "path": "02_KNOWLEDGE/Runtime-Ops/Runtime-Ops.md"},
            {"id": "platform_strategy_knowledge", "label": "Platform Strategy", "path": "02_KNOWLEDGE/Platform-Strategy/Platform-Strategy.md"},
            {"id": "content_distribution_knowledge", "label": "Content Distribution", "path": "02_KNOWLEDGE/Content-Distribution/Content-Distribution.md"},
            {"id": "fitness_physical", "label": "Fitness / Physical", "path": "02_KNOWLEDGE/Fitness/Fitness-Physical.md"},
            {
                "id": "networking_social_capital",
                "label": "Networking / Social Capital",
                "path": "02_KNOWLEDGE/Networking-Social/Networking-Social-Capital.md",
            },
            {"id": "language_learning", "label": "Language Learning", "path": "02_KNOWLEDGE/Language/Language-Learning.md"},
            {"id": "hardware_robotics", "label": "Hardware / Robotics", "path": "02_KNOWLEDGE/Hardware/Hardware-Robotics.md"},
        ),
    },
    {
        "id": "personal_map_memory",
        "label": "Personal Map, Memory, and Operator Surfaces",
        "purpose": "Governed personal-memory review, visualization, and apply surfaces.",
        "items": (
            {
                "id": "personal_map_architecture",
                "label": "Personal Map Architecture",
                "path": "06_AGENTS/Personal-Map-Architecture.md",
                "status": "PARTIAL",
                "boundary": "candidate/review architecture",
            },
            {
                "id": "personal_map_node_template",
                "label": "Personal Map Node Template",
                "path": "05_TEMPLATES/Personal-Map-Node-Template.md",
                "status": "TEMPLATE",
            },
            {
                "id": "pulse_personal_map_visualization_contract",
                "label": "Pulse Personal Map Visualization Contract",
                "path": "06_AGENTS/ChaseOS-Pulse-Personal-Map-Visualization-Contract.md",
                "status": "VERIFIED TARGETED",
            },
            {
                "id": "pulse_personal_map_review_apply_surface",
                "label": "Pulse Personal Map Review Apply Surface",
                "path": "06_AGENTS/ChaseOS-Pulse-Personal-Map-Review-Apply-Surface.md",
                "status": "VERIFIED TARGETED",
            },
            {
                "id": "pulse_personal_memory_manager_spec",
                "label": "Personal Memory Manager Spec",
                "path": "06_AGENTS/ChaseOS-Pulse-Personal-Memory-Manager-Spec.md",
                "status": "PARTIAL / SPEC",
            },
            {
                "id": "runtime_personal_map",
                "label": "Runtime personal_map.py",
                "path": "runtime/memory/personal_map.py",
                "status": "PARTIAL CODE SCAFFOLD",
            },
        ),
    },
    {
        "id": "personal_map_candidate_reviews",
        "label": "Personal Map Candidate Reviews",
        "purpose": "Pending-review Personal Map candidate logs and decks generated from accepted personal-domain context.",
        "items": _PERSONAL_MAP_CANDIDATE_REVIEW_ITEMS,
    },
    {
        "id": "workspace_mode_profiles",
        "label": "Workspace Mode and Runtime Context",
        "purpose": "Profiles that route personal OS, project, SOP, and runtime surfaces.",
        "items": (
            {"id": "use_case_mode_architecture", "label": "Workspace Mode Layer Architecture", "path": "06_AGENTS/Use-Case-Mode-Architecture.md"},
            {"id": "workspace_mode_profile_standard", "label": "Workspace Mode Profile Standard", "path": "06_AGENTS/Workspace-Mode-Profile-Standard.md"},
            {"id": "home_workspace_mode", "label": "00_HOME personal_os profile", "path": "00_HOME/.workspace-mode.yaml"},
            {"id": "chaseos_workspace_mode", "label": "ChaseOS project profile", "path": "01_PROJECTS/ChaseOS/workspace-mode.yaml"},
            {"id": "university_workspace_mode", "label": "University study/research profile", "path": "01_PROJECTS/University/workspace-mode.yaml"},
            {"id": "sops_workspace_mode", "label": "SOP business profile", "path": "04_SOPS/.workspace-mode.yaml"},
            {"id": "runtime_workspace_mode", "label": "Runtime agent-ops profile", "path": "runtime/.workspace-mode.yaml"},
            {"id": "agents_workspace_mode", "label": "Agent-control profile", "path": "06_AGENTS/.workspace-mode.yaml"},
        ),
    },
    {
        "id": "update_templates",
        "label": "Update Templates",
        "purpose": "Templates for proposed personal-map nodes, domain goals, playbooks, and audits.",
        "items": (
            {"id": "domain_goal_profile_template", "label": "Domain Goal Profile Template", "path": "05_TEMPLATES/Domain-Goal-Profile-Template.md"},
            {"id": "domain_playbook_template", "label": "Domain Playbook Template", "path": "05_TEMPLATES/Domain-Playbook-Template.md"},
            {"id": "personal_domain_node_template", "label": "Personal Domain Node Template", "path": "05_TEMPLATES/Personal-Domain-Node-Template.md"},
            {"id": "operator_run_audit_template", "label": "Operator Run Audit Template", "path": "05_TEMPLATES/Operator-Run-Audit-Template.md"},
            {"id": "agent_activity_log_template", "label": "Agent Activity Log Template", "path": "05_TEMPLATES/Agent-Activity-Log-Template.md"},
            {"id": "daily_note_template", "label": "Daily Note Template", "path": "05_TEMPLATES/Daily-Note-Template.md"},
        ),
    },
)

_PERSONAL_INDEX_TOKENS = (
    "[[00_HOME/Personal-Operator-Index",
    "[[Personal-Operator-Index",
    "00_HOME/Personal-Operator-Index.md",
)

_LINK_CHECKS: tuple[dict[str, Any], ...] = (
    {
        "id": "dashboard_links_soul",
        "label": "Dashboard links SOUL",
        "source_path": "00_HOME/Dashboard.md",
        "expected_tokens": ("[[SOUL", "SOUL.md"),
        "severity": "blocker",
    },
    {
        "id": "dashboard_links_personal_operator_index",
        "label": "Dashboard links Personal Operator Index",
        "source_path": "00_HOME/Dashboard.md",
        "expected_tokens": _PERSONAL_INDEX_TOKENS,
        "severity": "blocker",
    },
    {
        "id": "dashboard_links_context_intake",
        "label": "Dashboard links Context Intake",
        "source_path": "00_HOME/Dashboard.md",
        "expected_tokens": (
            "03_INPUTS/Personal-Context-Intake",
            "2026-05-16_personal-context-intake-implementation-map",
        ),
        "severity": "blocker",
    },
    {
        "id": "personal_operator_index_links_context_intake",
        "label": "Personal Operator Index links Context Intake",
        "source_path": ROOT_HUB_PATH,
        "expected_tokens": (
            "03_INPUTS/Personal-Context-Intake",
            "2026-05-15_personal-context-intake-packet",
            "2026-05-16_personal-context-intake-implementation-map",
        ),
        "severity": "blocker",
    },
    {
        "id": "personal_operator_index_links_university_modules",
        "label": "Personal Operator Index links University Modules",
        "source_path": ROOT_HUB_PATH,
        "expected_tokens": (
            "01_PROJECTS/University/Modules/Modules",
            "University Modules",
        ),
        "severity": "blocker",
    },
    {
        "id": "personal_operator_index_links_personal_domains",
        "label": "Personal Operator Index links Personal Domains",
        "source_path": ROOT_HUB_PATH,
        "expected_tokens": (
            "00_HOME/Personal-Domains/Personal-Domains-Index",
            "Personal Domains Index",
        ),
        "severity": "blocker",
    },
    {
        "id": "dashboard_links_personal_domains",
        "label": "Dashboard links Personal Domains",
        "source_path": "00_HOME/Dashboard.md",
        "expected_tokens": (
            "00_HOME/Personal-Domains/Personal-Domains-Index",
            "Personal Domains Index",
        ),
        "severity": "blocker",
    },
    {
        "id": "degree_os_links_university_modules",
        "label": "Degree OS links University Modules",
        "source_path": "01_PROJECTS/University/Degree-OS.md",
        "expected_tokens": (
            "Modules/Modules",
            "University Modules",
        ),
        "severity": "blocker",
    },
    {
        "id": "computer_science_links_university_modules",
        "label": "Computer Science links University Modules",
        "source_path": "02_KNOWLEDGE/Computer-Science/Computer-Science.md",
        "expected_tokens": (
            "University Module Tree",
            "01_PROJECTS/University/Modules/Modules",
        ),
        "severity": "blocker",
    },
    {
        "id": "root_knowledge_index_links_personal_operator_index",
        "label": "Root Knowledge Index links Personal Operator Index",
        "source_path": "KNOWLEDGE-INDEX.md",
        "expected_tokens": _PERSONAL_INDEX_TOKENS,
        "severity": "warning",
    },
    {
        "id": "root_knowledge_index_is_routing_shim",
        "label": "Root Knowledge Index is explicit routing shim",
        "source_path": "KNOWLEDGE-INDEX.md",
        "expected_tokens": (
            "knowledge-index-routing-shim",
            "ROUTING SHIM / NOT CANONICAL",
            "02_KNOWLEDGE/Knowledge-Index",
        ),
        "match": "all",
        "severity": "warning",
    },
    {
        "id": "dashboard_links_personal_context_import_feature",
        "label": "Dashboard links Personal Context Import Feature",
        "source_path": "00_HOME/Dashboard.md",
        "expected_tokens": (
            "06_AGENTS/Personal-Context-Import-Feature",
            "Personal Context Import Feature",
        ),
        "match": "all",
        "severity": "warning",
    },
    {
        "id": "personal_operator_index_links_personal_context_import_feature",
        "label": "Personal Operator Index links Personal Context Import Feature",
        "source_path": ROOT_HUB_PATH,
        "expected_tokens": (
            "06_AGENTS/Personal-Context-Import-Feature",
            "Personal Context Import Feature",
        ),
        "match": "all",
        "severity": "warning",
    },
    {
        "id": "intake_index_links_personal_context_import_feature",
        "label": "Personal Context Intake Index links Personal Context Import Feature",
        "source_path": "03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index.md",
        "expected_tokens": (
            "06_AGENTS/Personal-Context-Import-Feature",
            "Personal Context Import Feature",
        ),
        "match": "all",
        "severity": "warning",
    },
    {
        "id": "root_knowledge_index_links_university_modules",
        "label": "Root Knowledge Index links University Modules",
        "source_path": "KNOWLEDGE-INDEX.md",
        "expected_tokens": (
            "01_PROJECTS/University/Modules/Modules",
            "University Modules",
        ),
        "severity": "warning",
    },
    {
        "id": "master_knowledge_index_links_personal_operator_index",
        "label": "Master Knowledge Index links Personal Operator Index",
        "source_path": "02_KNOWLEDGE/Knowledge-Index.md",
        "expected_tokens": _PERSONAL_INDEX_TOKENS,
        "severity": "warning",
    },
    {
        "id": "master_knowledge_index_links_university_modules",
        "label": "Master Knowledge Index links University Modules",
        "source_path": "02_KNOWLEDGE/Knowledge-Index.md",
        "expected_tokens": (
            "01_PROJECTS/University/Modules/Modules",
            "University Modules",
        ),
        "severity": "warning",
    },
    {
        "id": "doctrine_links_personal_operator_index",
        "label": "Doctrine index links Personal Operator Index",
        "source_path": "02_KNOWLEDGE/Doctrine/Doctrine-Philosophy.md",
        "expected_tokens": _PERSONAL_INDEX_TOKENS,
        "severity": "warning",
    },
    {
        "id": "personal_map_links_personal_operator_index",
        "label": "Personal Map Architecture links Personal Operator Index",
        "source_path": "06_AGENTS/Personal-Map-Architecture.md",
        "expected_tokens": _PERSONAL_INDEX_TOKENS,
        "severity": "warning",
    },
    {
        "id": "personal_operator_index_links_personal_map_candidates",
        "label": "Personal Operator Index links Personal Map candidates",
        "source_path": ROOT_HUB_PATH,
        "expected_tokens": (
            "2026-05-16-personal-life-domain-candidates-review",
            "2026-05-16-personal-map-candidates.jsonl",
        ),
        "severity": "warning",
    },
    {
        "id": "personal_operator_index_links_standalone_nodes",
        "label": "Personal Operator Index links standalone source-derived nodes",
        "source_path": ROOT_HUB_PATH,
        "expected_tokens": (
            "Prompt-Engineering",
            "Runtime-Ops",
            "Platform-Strategy",
            "Content-Distribution",
            "Language-Mobility/Mandarin",
            "Mandarin-HSK1",
        ),
        "severity": "warning",
    },
    {
        "id": "personal_operator_index_links_final_source_children",
        "label": "Personal Operator Index links final source child nodes",
        "source_path": ROOT_HUB_PATH,
        "expected_tokens": (
            "2026-05-16_personal-context-final-node-coverage-audit",
            "Tool-Use",
            "Funding-Rates",
            "Vulnerability-Patterns",
            "Backend-Architecture",
            "WSL2-Ubuntu-Setup-Guide",
        ),
        "match": "all",
        "severity": "warning",
    },
    {
        "id": "dashboard_links_final_coverage_audit",
        "label": "Dashboard links final node coverage audit",
        "source_path": "00_HOME/Dashboard.md",
        "expected_tokens": (
            "2026-05-16_personal-context-final-node-coverage-audit",
            "Personal Context Final Node Coverage Audit",
        ),
        "severity": "warning",
    },
    {
        "id": "intake_index_links_final_coverage_audit",
        "label": "Personal Context Intake Index links final node coverage audit",
        "source_path": "03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index.md",
        "expected_tokens": (
            "2026-05-16_personal-context-final-node-coverage-audit",
            "final node coverage audit",
        ),
        "severity": "warning",
    },
    {
        "id": "ai_agent_index_links_tool_use",
        "label": "AI Agent index links Tool Use",
        "source_path": "02_KNOWLEDGE/AI-Agents/AI-Agent-Engineering.md",
        "expected_tokens": ("Tool-Use",),
        "severity": "warning",
    },
    {
        "id": "architecture_coverage_audit_routes_chaseos_nodes",
        "label": "Final coverage audit routes ChaseOS architecture nodes",
        "source_path": "03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-final-node-coverage-audit.md",
        "expected_tokens": (
            "ChaseOS-Core",
            "ChaseOS-Personal",
            "Source-Intelligence-Core",
        ),
        "match": "all",
        "severity": "warning",
    },
    {
        "id": "runtime_ops_links_explicit_children",
        "label": "Runtime Ops links explicit WSL/Linux child nodes",
        "source_path": "02_KNOWLEDGE/Runtime-Ops/Runtime-Ops.md",
        "expected_tokens": (
            "WSL2-Ubuntu-Setup-Guide",
            "Linux-Commands",
        ),
        "match": "all",
        "severity": "warning",
    },
    {
        "id": "platform_strategy_links_action_matrix",
        "label": "Platform Strategy links Action Matrix",
        "source_path": "02_KNOWLEDGE/Platform-Strategy/Platform-Strategy.md",
        "expected_tokens": ("Action-Matrix",),
        "severity": "warning",
    },
    {
        "id": "trading_knowledge_links_explicit_children",
        "label": "Trading knowledge index links explicit source child nodes",
        "source_path": "02_KNOWLEDGE/Trading-Systems/Trading-Systems-Engineering.md",
        "expected_tokens": (
            "Funding-Rates",
            "Order-Flow",
            "Morning-Thesis",
            "Trade-Journal",
            "Risk-Management",
        ),
        "match": "all",
        "severity": "warning",
    },
    {
        "id": "cybersecurity_knowledge_links_explicit_children",
        "label": "Cybersecurity index links explicit source child nodes",
        "source_path": "02_KNOWLEDGE/Cybersecurity/Cybersecurity.md",
        "expected_tokens": (
            "Vulnerability-Patterns",
            "Lab-Writeups",
            "Agent-Security",
            "Credential-Boundaries",
        ),
        "match": "all",
        "severity": "warning",
    },
    {
        "id": "full_stack_knowledge_links_explicit_children",
        "label": "Full-Stack index links explicit source child nodes",
        "source_path": "02_KNOWLEDGE/Full-Stack/Full-Stack-Engineering.md",
        "expected_tokens": (
            "React",
            "Backend-Architecture",
            "Solana-Future",
        ),
        "match": "all",
        "severity": "warning",
    },
    {
        "id": "personal_language_domain_links_mandarin_child",
        "label": "Language personal domain links Mandarin child nodes",
        "source_path": "00_HOME/Personal-Domains/Language-Learning-Global-Mobility.md",
        "expected_tokens": (
            "01_PROJECTS/Language-Mobility/Mandarin",
            "02_KNOWLEDGE/Language/Mandarin-HSK1",
        ),
        "match": "all",
        "severity": "warning",
    },
    {
        "id": "language_knowledge_links_mandarin_child",
        "label": "Language knowledge index links Mandarin child nodes",
        "source_path": "02_KNOWLEDGE/Language/Language-Learning.md",
        "expected_tokens": (
            "01_PROJECTS/Language-Mobility/Mandarin",
            "Mandarin-HSK1",
        ),
        "match": "all",
        "severity": "warning",
    },
    {
        "id": "vault_map_links_context_intake",
        "label": "Vault Map links Context Intake",
        "source_path": "06_AGENTS/Vault-Map.md",
        "expected_tokens": (
            "Personal-Context-Intake",
            "context intake",
        ),
        "severity": "warning",
    },
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _authority() -> dict[str, bool]:
    return {
        "read_only": True,
        "writes_vault": False,
        "writes_personal_map": False,
        "writes_pulse_memory": False,
        "writes_companion_memory": False,
        "writes_project_truth": False,
        "provider_calls_allowed": False,
        "secret_values_read": False,
        "personal_map_mutation_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _text_for(vault: Path, relative_path: str) -> str:
    path = vault / relative_path
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _item_with_presence(vault: Path, group_id: str, item: dict[str, Any]) -> dict[str, Any]:
    relative_path = str(item["path"]).replace("\\", "/")
    path = vault / relative_path
    return {
        "id": item["id"],
        "group_id": group_id,
        "label": item["label"],
        "path": relative_path,
        "exists": path.exists(),
        "status": item.get("status", "TRACKED"),
        "boundary": item.get("boundary", "review before real-world use"),
    }


def _link_check(vault: Path, check: dict[str, Any]) -> dict[str, Any]:
    source_path = check["source_path"]
    text = _text_for(vault, source_path)
    expected_tokens = tuple(check["expected_tokens"])
    match_mode = check.get("match", "any")
    if match_mode == "all":
        passed = bool(text) and all(token in text for token in expected_tokens)
    else:
        passed = bool(text) and any(token in text for token in expected_tokens)
    return {
        "id": check["id"],
        "label": check["label"],
        "source_path": source_path,
        "source_exists": bool(text),
        "expected_tokens": list(expected_tokens),
        "match": match_mode,
        "severity": check.get("severity", "warning"),
        "passed": passed,
    }


def _grouped_items(vault: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    for group in _GROUPS:
        group_items = [_item_with_presence(vault, group["id"], item) for item in group["items"]]
        groups.append(
            {
                "id": group["id"],
                "label": group["label"],
                "purpose": group["purpose"],
                "count": len(group_items),
                "existing_count": sum(1 for item in group_items if item["exists"]),
                "missing_count": sum(1 for item in group_items if not item["exists"]),
                "items": group_items,
            }
        )
        items.extend(group_items)
    return groups, items


def _graph(grouped: list[dict[str, Any]]) -> dict[str, Any]:
    hub_id = "personal_operator_index"
    nodes = [
        {
            "id": hub_id,
            "label": "Personal Operator Index",
            "path": ROOT_HUB_PATH,
            "group_id": "hub",
            "kind": "hub",
        }
    ]
    edges: list[dict[str, str]] = []
    for group in grouped:
        group_node_id = f"group:{group['id']}"
        nodes.append(
            {
                "id": group_node_id,
                "label": group["label"],
                "path": ROOT_HUB_PATH,
                "group_id": group["id"],
                "kind": "group",
            }
        )
        edges.append({"source": hub_id, "target": group_node_id, "kind": "groups"})
        for item in group["items"]:
            nodes.append(
                {
                    "id": item["id"],
                    "label": item["label"],
                    "path": item["path"],
                    "group_id": group["id"],
                    "kind": "file",
                    "exists": str(item["exists"]).lower(),
                }
            )
            edges.append({"source": group_node_id, "target": item["id"], "kind": "contains"})
    return {
        "root_hub_path": ROOT_HUB_PATH,
        "nodes": nodes,
        "edges": edges,
    }


def build_personal_operator_context_index(vault_root: str | Path) -> dict[str, Any]:
    """Return grouped personal-operator context and link checks."""

    vault = Path(vault_root).resolve()
    grouped, items = _grouped_items(vault)
    link_checks = [_link_check(vault, check) for check in _LINK_CHECKS]
    blockers = [check for check in link_checks if check["severity"] == "blocker" and not check["passed"]]
    warnings = [check for check in link_checks if check["severity"] != "blocker" and not check["passed"]]
    existing_count = sum(1 for item in items if item["exists"])
    missing_count = len(items) - existing_count
    passed_link_count = sum(1 for check in link_checks if check["passed"])
    status = "ready_for_review"
    if blockers:
        status = "blocked_link_repair_required"
    elif warnings:
        status = "ready_with_warnings"

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "status": status,
        "headline": "Personal operator context",
        "root_hub_path": ROOT_HUB_PATH,
        "summary": {
            "group_count": len(grouped),
            "tracked_file_count": len(items),
            "existing_file_count": existing_count,
            "missing_file_count": missing_count,
            "project_operating_file_count": len(next(group for group in grouped if group["id"] == "project_operating_files")["items"]),
            "context_intake_file_count": len(next(group for group in grouped if group["id"] == "context_intake_sources")["items"]),
            "personal_life_domain_file_count": len(next(group for group in grouped if group["id"] == "personal_life_domain_nodes")["items"]),
            "source_derived_standalone_node_count": len(next(group for group in grouped if group["id"] == "source_derived_standalone_nodes")["items"]),
            "personal_map_candidate_review_file_count": len(next(group for group in grouped if group["id"] == "personal_map_candidate_reviews")["items"]),
            "university_module_file_count": len(next(group for group in grouped if group["id"] == "university_module_tree")["items"]),
            "knowledge_root_count": len(next(group for group in grouped if group["id"] == "knowledge_roots")["items"]),
            "link_check_count": len(link_checks),
            "link_check_passed_count": passed_link_count,
            "link_blocker_count": len(blockers),
            "link_warning_count": len(warnings),
        },
        "groups": grouped,
        "missing_files": [item for item in items if not item["exists"]],
        "link_checks": link_checks,
        "link_blockers": blockers,
        "link_warnings": warnings,
        "graph": _graph(grouped),
        "update_guidance": [
            "Start with SOUL, Principles, and Operating System before updating project goals.",
            "Use the handover/source packet to the maximum safe extent; fill fields with source-derived context before leaving evidence gaps.",
            "Do not leave TODO/TBD/work-later placeholders when the source packet contains usable doctrine, discipline, interest, language, domain, project, module, or operating-context detail.",
            "Update one domain or project operating file at a time.",
            "Keep generated ideas labeled as generated until accepted.",
            "Do not store secrets, credentials, wallet keys, exchange keys, or API key values in the vault.",
            "Use the approved canonical-promotion executor only for managed route blocks; keep Personal Map updates candidate/review/apply-gated until a separate approved live-apply pass exists.",
        ],
        "authority": _authority(),
    }
